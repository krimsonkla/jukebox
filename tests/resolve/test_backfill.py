"""A backfill keeps what it has already paid for."""

import pytest

from jukebox.charts import Chart, Corpus
from jukebox.charts.entry_filter import EntryFilter
from jukebox.resolve import Attempt, Backfill, Resolution, ResolutionStore, Resolver

from tests.resolve.conftest import FakeCatalog
from tests.support.corpus import TODAY, write_ranked


def corpus_with(tmp_path, *titles) -> Corpus:
    """A one-chart corpus holding these ranked entries."""
    corpus = Corpus(tmp_path / "charts")
    write_ranked(
        corpus,
        Chart.HOT_100,
        1985,
        *[(index + 1, title, "a-ha") for index, title in enumerate(titles)],
    )
    return corpus


@pytest.fixture(name="parts")
def _parts(tmp_path, track):
    def make(*titles, catalog=None):
        corpus = corpus_with(tmp_path, *titles)
        store = ResolutionStore(tmp_path / "resolutions")
        found = (
            catalog
            if catalog is not None
            else FakeCatalog({(t, "a-ha"): [track(t, "a-ha")] for t in titles})
        )
        return corpus, store, Backfill(corpus, store, Resolver(found), lambda: TODAY)

    return make


def test_every_entry_resolves_and_is_stored(parts):
    _, store, backfill = parts("Take On Me", "The Sun Always Shines on T.V.")
    coverage = backfill.year(Chart.HOT_100, 1985)
    assert coverage.total == 2 and coverage.resolved == 2
    assert len(store.load()) == 2


def test_an_entry_already_held_is_not_looked_up_again(parts, track):
    catalog = FakeCatalog({("Take On Me", "a-ha"): [track("Take On Me", "a-ha")]})
    _, _, backfill = parts("Take On Me", catalog=catalog)
    backfill.year(Chart.HOT_100, 1985)
    backfill.year(Chart.HOT_100, 1985)
    assert catalog.searched == [("Take On Me", "a-ha")]


def test_a_limit_stops_after_that_many_lookups(parts):
    _, store, backfill = parts("One", "Two", "Three")
    backfill.year(Chart.HOT_100, 1985, Attempt(limit=2))
    assert len(store.load()) == 2


def test_unresolved_entries_are_reported_by_name(parts):
    _, _, backfill = parts("Obscure", catalog=FakeCatalog())
    coverage = backfill.year(Chart.HOT_100, 1985)
    assert [outcome.title for outcome in coverage.unresolved] == ["Obscure"]
    assert coverage.resolved == 0


def test_progress_survives_a_failure_partway_through(tmp_path, track):
    # A transient gateway error must not discard the entries already paid for.
    class Failing(FakeCatalog):
        """Fails partway through, the way a gateway error does."""

        def search(self, title, artist):
            if title == "Two":
                raise RuntimeError("502")
            return super().search(title, artist)

    corpus = corpus_with(tmp_path, "One", "Two")
    store = ResolutionStore(tmp_path / "resolutions")
    catalog = Failing({("One", "a-ha"): [track("One", "a-ha")]})
    backfill = Backfill(corpus, store, Resolver(catalog), lambda: TODAY)

    with pytest.raises(RuntimeError):
        backfill.year(Chart.HOT_100, 1985)
    assert len(store.load()) == 1


def test_the_report_states_the_rate_and_the_method_split(parts):
    _, _, backfill = parts("Take On Me")
    rendered = backfill.year(Chart.HOT_100, 1985).render()
    assert "1/1" in rendered and "100%" in rendered and "search 1" in rendered


def test_a_confidence_is_recorded_for_a_searched_match(parts):
    _, store, backfill = parts("Take On Me")
    backfill.year(Chart.HOT_100, 1985)
    row = next(iter(store.load().values()))
    assert 0.0 < row.confidence <= 1.05
    assert row.resolved == TODAY


def test_an_empty_chart_reports_no_rate_rather_than_dividing_by_zero(parts):
    _, _, backfill = parts()
    assert "0/0" in backfill.year(Chart.HOT_100, 1985).render()


def test_a_filter_narrows_before_a_lookup_is_paid_for(parts, track):
    # Resolving a whole chart to serve a spec that takes its top rows pays for
    # rows nobody asked about, and each one is a request against a rate limit.
    titles = ("One", "Two", "Three")
    catalog = FakeCatalog({(t, "a-ha"): [track(t, "a-ha")] for t in titles})
    _, store, backfill = parts(*titles, catalog=catalog)
    backfill.year(Chart.HOT_100, 1985, Attempt(rows=EntryFilter(max_rank=1)))
    assert catalog.searched == [("One", "a-ha")]
    assert len(store.load()) == 1


def test_coverage_is_reported_over_the_rows_asked_for(parts):
    # The rows the filter excluded were never attempted, so counting them as
    # unresolved would report a failure that did not happen.
    _, _, backfill = parts("One", "Two", "Three")
    coverage = backfill.year(Chart.HOT_100, 1985, Attempt(rows=EntryFilter(max_rank=2)))
    assert coverage.total == 2
    assert coverage.resolved == 2
    assert coverage.unresolved == ()


def test_no_filter_still_resolves_the_whole_chart_year(parts):
    _, store, backfill = parts("One", "Two", "Three")
    coverage = backfill.year(Chart.HOT_100, 1985)
    assert coverage.total == 3
    assert len(store.load()) == 3


def test_a_filter_and_a_limit_compose(parts):
    _, store, backfill = parts("One", "Two", "Three")
    backfill.year(Chart.HOT_100, 1985, Attempt(limit=1, rows=EntryFilter(max_rank=2)))
    assert len(store.load()) == 1


def test_a_failure_is_recorded_so_it_is_not_paid_for_twice(parts):
    # A lookup costs the same whether it answers or not, so a store holding only
    # the answers asks for every failure again on every pass.
    _, store, backfill = parts("Obscure", catalog=FakeCatalog())
    backfill.year(Chart.HOT_100, 1985)
    assert list(store.misses.load()) == [Resolution.key_for("Obscure", "a-ha")]


def test_a_known_failure_is_skipped_rather_than_looked_up_again(parts):
    catalog = FakeCatalog()
    _, _, backfill = parts("Obscure", catalog=catalog)
    backfill.year(Chart.HOT_100, 1985)
    coverage = backfill.year(Chart.HOT_100, 1985)
    assert catalog.searched == [("Obscure", "a-ha")]
    assert coverage.attempted == 0
    assert coverage.skipped == 1


def test_a_skipped_failure_is_reported_so_a_cheap_pass_says_why(parts):
    _, _, backfill = parts("Obscure", catalog=FakeCatalog())
    backfill.year(Chart.HOT_100, 1985)
    assert "already known missing" in backfill.year(Chart.HOT_100, 1985).render()


def test_retrying_asks_again_for_what_was_missed(parts):
    catalog = FakeCatalog()
    _, _, backfill = parts("Obscure", catalog=catalog)
    backfill.year(Chart.HOT_100, 1985)
    backfill.year(Chart.HOT_100, 1985, Attempt(retry_missed=True))
    assert len(catalog.searched) == 2


def test_a_retry_that_answers_clears_the_miss(parts, track):
    # The miss records one attempt, never a verdict: a catalogue gains
    # recordings, and what it withheld today it may offer later.
    catalog = FakeCatalog()
    corpus, store, backfill = parts("Take On Me", catalog=catalog)
    backfill.year(Chart.HOT_100, 1985)
    assert store.misses.load()
    found = FakeCatalog({("Take On Me", "a-ha"): [track("Take On Me", "a-ha")]})
    Backfill(corpus, store, Resolver(found), lambda: TODAY).year(
        Chart.HOT_100, 1985, Attempt(retry_missed=True)
    )
    assert not store.misses.load()
    assert len(store.load()) == 1


def test_a_miss_keeps_how_close_the_best_candidate_came(parts, track):
    # A miss just under the threshold says the scorer was cautious; one with
    # nothing to score says the catalogue was silent. Only the first is worth
    # another lookup.
    catalog = FakeCatalog({("Obscure", "a-ha"): [track("Something Else Entirely", "Nobody")]})
    _, store, backfill = parts("Obscure", catalog=catalog)
    backfill.year(Chart.HOT_100, 1985)
    missed = next(iter(store.misses.load().values()))
    assert missed.near is True
    assert 0.0 <= missed.score < 0.72


def test_a_miss_with_nothing_offered_scores_nothing(parts):
    _, store, backfill = parts("Obscure", catalog=FakeCatalog())
    backfill.year(Chart.HOT_100, 1985)
    missed = next(iter(store.misses.load().values()))
    assert missed.score is None
    assert missed.near is False


def test_a_miss_records_the_chart_words_and_the_day_it_was_asked(parts):
    _, store, backfill = parts("Obscure", catalog=FakeCatalog())
    backfill.year(Chart.HOT_100, 1985)
    missed = next(iter(store.misses.load().values()))
    assert (missed.title, missed.artist) == ("Obscure", "a-ha")
    assert missed.attempted == TODAY


def test_nothing_missed_reads_as_nothing(tmp_path):
    assert ResolutionStore(tmp_path / "resolutions").misses.load() == {}
