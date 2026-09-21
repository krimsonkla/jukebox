"""An assistant can fill the corpus, not only read it."""

import pathlib

import pytest

from jukebox.charts import Chart, FixtureSource
from jukebox.mcp import TooManyYears
from jukebox.mcp.resolve_request import ResolveRequest
from jukebox.mcp.tools import fetch_charts, resolve_charts
from jukebox.net.errors import Throttled, TransientFailure
from jukebox.ports import TrackMatch

FIXTURES = "tests/fixtures/pages"


class OneHitCatalog:
    """Answers every search with the song it was asked for."""

    def __init__(self) -> None:
        self.searched: list[tuple[str, str]] = []

    def search(self, title: str, artist: str) -> list[TrackMatch]:
        """A perfect match."""
        self.searched.append((title, artist))
        return [TrackMatch(uri=f"u:{title}", title=title, artist=artist)]

    def by_isrc(self, _isrc: str) -> list[TrackMatch]:
        """Nothing."""
        return []


@pytest.fixture(name="source")
def _source():
    return FixtureSource(pathlib.Path(FIXTURES))


def test_fetching_writes_chart_files_into_the_corpus(workspace, source):
    found = fetch_charts(workspace, source, (1985, 1985))
    assert found["fetched"][0]["year"] == 1985
    assert found["fetched"][0]["charts"]["hot-100"] == 100
    assert workspace.corpus.path(Chart.HOT_100, 1985).exists()


def test_fetching_names_the_charts_it_cannot_cover_and_why(workspace, source):
    unavailable = fetch_charts(workspace, source, (1985, 1985))["fetched"][0]["unavailable"]
    assert "did not exist" in unavailable["modern-rock"]
    assert "did not exist" in unavailable["latin"]


def test_fetching_too_many_years_at_once_is_refused_with_a_bound(workspace, source):
    with pytest.raises(TooManyYears, match="twenty years"):
        fetch_charts(workspace, source, (1900, 1999))


def test_resolving_matches_the_corpus_and_reports_coverage(unresolved):
    catalog = OneHitCatalog()
    found = resolve_charts(
        unresolved, catalog, ResolveRequest(years=(1985, 1985), charts=["hot-100"])
    )
    assert found["resolved"][0]["matched"] == 3
    assert found["resolved"][0]["of"] == 3
    assert len(catalog.searched) == 3


def test_an_entry_already_matched_is_not_looked_up_again(workspace):
    # The workspace arrives with its three entries already matched.
    catalog = OneHitCatalog()
    resolve_charts(workspace, catalog, ResolveRequest(years=(1985, 1985), charts=["hot-100"]))
    assert not catalog.searched


def test_resolving_stops_at_the_limit_and_says_what_is_left(unresolved):
    catalog = OneHitCatalog()
    found = resolve_charts(
        unresolved, catalog, ResolveRequest(years=(1985, 1985), charts=["hot-100"], limit=2)
    )
    assert len(catalog.searched) == 2
    assert found["lookups_left"] == 0


def test_resolving_again_continues_rather_than_repeating(unresolved):
    first = OneHitCatalog()
    resolve_charts(
        unresolved, first, ResolveRequest(years=(1985, 1985), charts=["hot-100"], limit=2)
    )
    second = OneHitCatalog()
    resolve_charts(unresolved, second, ResolveRequest(years=(1985, 1985), charts=["hot-100"]))
    assert len(second.searched) == 1


def test_resolving_skips_a_chart_the_corpus_does_not_hold(workspace):
    found = resolve_charts(
        workspace, OneHitCatalog(), ResolveRequest(years=(1985, 1985), charts=["latin"])
    )
    assert not found["resolved"]


def test_resolving_every_chart_is_the_default(unresolved):
    found = resolve_charts(unresolved, OneHitCatalog(), ResolveRequest(years=(1985, 1985)))
    assert {row["chart"] for row in found["resolved"]} == {"hot-100", "country"}


def test_resolving_too_many_years_is_refused(workspace):
    with pytest.raises(TooManyYears):
        resolve_charts(workspace, OneHitCatalog(), ResolveRequest(years=(1900, 1999)))


def test_a_year_is_carried_in_each_row_because_json_has_no_integer_keys(workspace, source):
    rows = fetch_charts(workspace, source, (1985, 1985))["fetched"]
    assert isinstance(rows, list) and rows[0]["year"] == 1985


class FakeCatalog:
    """Answers nothing, and records what it was asked."""

    def __init__(self) -> None:
        self.searched: list[tuple[str, str]] = []

    def search(self, title: str, artist: str) -> list[TrackMatch]:
        """Nothing at all."""
        self.searched.append((title, artist))
        return []

    def by_isrc(self, _isrc: str) -> list[TrackMatch]:
        """Nothing."""
        return []


class RefusingCatalog:
    """Answers every search by refusing, the way a limited service does."""

    def __init__(self, refusal: Exception) -> None:
        self._refusal = refusal
        self.searched: list[tuple[str, str]] = []

    def search(self, title: str, artist: str) -> list[TrackMatch]:
        """The refusal this catalog was built with."""
        self.searched.append((title, artist))
        raise self._refusal

    def by_isrc(self, _isrc: str) -> list[TrackMatch]:
        """Nothing."""
        return []


def test_a_chart_that_answers_badly_does_not_skip_the_rest(unresolved):
    # One chart being unwell is not a reason to abandon the others, and what it
    # did resolve was written on the way out.
    catalog = RefusingCatalog(TransientFailure("https://api.example/search", 502, 4))
    found = resolve_charts(unresolved, catalog, ResolveRequest(years=(1985, 1985)))
    assert {row["chart"] for row in found["resolved"]} == {"hot-100", "country"}
    assert all("failed" in row for row in found["resolved"])
    assert "502" in found["resolved"][0]["failed"]


def test_being_told_to_wait_stops_the_pass_rather_than_spending_more_requests(unresolved):
    # Every further chart would be another request against the window the
    # service is already refusing.
    catalog = RefusingCatalog(Throttled("https://api.example/search", 900.0))
    found = resolve_charts(unresolved, catalog, ResolveRequest(years=(1985, 1985)))
    assert found["retry_after_seconds"] == 900
    assert "asked for 900s" in found["stopped"]
    assert len(catalog.searched) == 1
    assert not found["resolved"]


def test_a_spent_quota_is_named_so_the_caller_knows_pacing_will_not_help(unresolved):
    # A quota counts how many requests are made and a rate limit how quickly, so
    # only one of them is answered by slowing down.
    catalog = RefusingCatalog(Throttled("https://api.example/search", 86034.0, "QUOTA_EXCEEDED"))
    found = resolve_charts(unresolved, catalog, ResolveRequest(years=(1985, 1985)))
    assert found["reason"] == "QUOTA_EXCEEDED"
    assert found["retry_after_seconds"] == 86034


def test_a_refusal_that_names_no_reason_says_so_rather_than_inventing_one(unresolved):
    catalog = RefusingCatalog(Throttled("https://api.example/search", 900.0))
    found = resolve_charts(unresolved, catalog, ResolveRequest(years=(1985, 1985)))
    assert found["reason"] is None


def test_a_known_failure_is_not_looked_up_again_and_is_reported(unresolved):
    # A lookup costs the same whether it answers or not, so the second pass over
    # the same misses should spend nothing and say so.
    empty = FakeCatalog()
    resolve_charts(unresolved, empty, ResolveRequest(years=(1985, 1985), charts=["hot-100"]))
    second = FakeCatalog()
    found = resolve_charts(
        unresolved, second, ResolveRequest(years=(1985, 1985), charts=["hot-100"])
    )
    assert not second.searched
    assert found["resolved"][0]["known_missing"] == 3


def test_retrying_missed_asks_for_them_again(unresolved):
    resolve_charts(
        unresolved, FakeCatalog(), ResolveRequest(years=(1985, 1985), charts=["hot-100"])
    )
    again = FakeCatalog()
    resolve_charts(
        unresolved,
        again,
        ResolveRequest(years=(1985, 1985), charts=["hot-100"], retry_missed=True),
    )
    assert len(again.searched) == 3
