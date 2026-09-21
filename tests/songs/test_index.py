"""The corpus grouped by what its rows are about."""

import datetime as dt

import pytest

from jukebox.charts import Chart, ChartEntry, ChartFile, Corpus, EntryKind
from jukebox.songs import Identity, Index, IndexStore


def ranked(title: str, artist: str, rank: int) -> ChartEntry:
    """A year-end row."""
    return ChartEntry(kind=EntryKind.RANKED, title=title, artist=artist, rank=rank)


def number_one(title: str, artist: str, reached: str, weeks: int = 1) -> ChartEntry:
    """A week-at-the-top row."""
    return ChartEntry(
        kind=EntryKind.NUMBER_ONE,
        title=title,
        artist=artist,
        reached=dt.date.fromisoformat(reached),
        weeks=weeks,
    )


def write(corpus: Corpus, chart: Chart, year: int, entries: list[ChartEntry]) -> None:
    """Put one chart year in the corpus."""
    corpus.write(
        ChartFile(
            chart=chart,
            year=year,
            kind=entries[0].kind,
            source="a page",
            retrieved=dt.date(2026, 1, 1),
            entries=entries,
        )
    )


@pytest.fixture(name="corpus")
def _corpus(tmp_path) -> Corpus:
    """Two charts carrying one song in common."""
    corpus = Corpus(tmp_path / "charts")
    write(corpus, Chart.RNB, 1995, [ranked("Waterfalls", "TLC", 4), ranked("Creep", "TLC", 1)])
    write(corpus, Chart.HOT_100, 1995, [ranked("Waterfalls", "TLC", 2)])
    write(
        corpus,
        Chart.DANCE_CLUB,
        1995,
        [number_one("Waterfalls", "TLC featuring Left Eye", "1995-07-01", weeks=3)],
    )
    return corpus


@pytest.fixture(name="index")
def _index(corpus) -> Index:
    return Index.of(corpus, list(Chart), (1995, 1995))


def test_one_song_on_three_charts_is_one_song(index):
    assert index.counts() == {
        "songs": 2,
        "artists": 1,
        "appearances": 4,
        "years": [1995, 1995],
    }


def test_the_span_it_was_built_over_survives_the_store(tmp_path, index):
    # Building replaces rather than merges, so a narrower span is a narrower
    # index; without the span recorded that reads as a healthy smaller one.
    store = IndexStore(tmp_path / "index")
    store.save(index)
    assert store.load().years == (1995, 1995)


def test_an_index_that_was_never_built_records_no_span(tmp_path):
    assert IndexStore(tmp_path / "index").load().years is None


def test_a_song_carries_every_chart_it_appeared_on(index):
    song = index.song("Waterfalls", "TLC")
    assert set(song.charts) == {"rnb", "hot-100", "dance-club"}


def test_a_song_is_found_however_its_billing_is_written(index):
    # The dance chart credited the guest; the identity is the lead.
    assert index.song("waterfalls", "TLC featuring Left Eye") is index.song("Waterfalls", "TLC")


def test_a_song_the_corpus_never_saw_is_absent(index):
    assert index.song("Nothing Compares 2 U", "Sinead O'Connor") is None


def test_the_best_rank_is_the_highest_placing_any_chart_gave_it(index):
    assert index.song("Waterfalls", "TLC").best_rank == 2


def test_a_song_no_chart_ranked_has_no_best_rank(corpus):
    only_ones = Corpus(corpus.path(Chart.RNB, 1995).parents[1])
    index = Index.of(only_ones, [Chart.DANCE_CLUB], (1995, 1995))
    assert index.song("Waterfalls", "TLC").best_rank is None


def test_weeks_at_number_one_sum_across_the_charts_that_had_it_there(index):
    assert index.song("Waterfalls", "TLC").weeks_at_number_one == 3


def test_years_are_listed_once_each_earliest_first(corpus):
    write(corpus, Chart.RNB, 1996, [ranked("Waterfalls", "TLC", 30)])
    index = Index.of(corpus, list(Chart), (1995, 1996))
    assert index.song("Waterfalls", "TLC").years == (1995, 1996)


def test_an_artist_carries_every_song_credited_to_them(index):
    artist = index.artist("TLC")
    assert artist.total == 2


def test_an_artist_keeps_the_other_billings_the_charts_used(index):
    assert set(index.artist("TLC").billings) == {"TLC", "TLC featuring Left Eye"}


def test_an_artist_the_corpus_never_saw_is_absent(index):
    assert index.artist("Nobody At All") is None


def test_a_crossover_is_a_song_on_every_named_chart(index):
    found = index.crossovers([Chart.RNB, Chart.HOT_100])
    assert [song.title for song in found] == ["Waterfalls"]


def test_a_song_on_only_one_of_the_charts_is_not_a_crossover(index):
    assert index.crossovers([Chart.HOT_100, Chart.COUNTRY]) == []


def test_a_year_the_corpus_lacks_is_skipped_rather_than_read(corpus):
    assert Index.of(corpus, list(Chart), (1970, 1970)).counts()["songs"] == 0


def test_an_appearance_orders_by_year_then_chart(index):
    song = index.song("Waterfalls", "TLC")
    assert sorted(a.order() for a in song.appearances)[0][0] == 1995


def test_an_index_round_trips_through_the_store(tmp_path, index):
    store = IndexStore(tmp_path / "index")
    store.save(index)
    assert store.load().counts() == index.counts()


def test_an_unbuilt_index_reads_as_empty(tmp_path):
    assert not IndexStore(tmp_path / "index").exists()
    assert IndexStore(tmp_path / "index").load().counts()["songs"] == 0


def test_rebuilding_produces_identical_bytes(tmp_path, index):
    store = IndexStore(tmp_path / "index")
    store.save(index)
    first = store.path.read_bytes()
    store.save(index)
    assert store.path.read_bytes() == first


def test_an_identity_round_trips_through_its_key():
    identity = Identity.of("Take On Me", "a-ha")
    assert Identity.parse(identity.key) == identity
