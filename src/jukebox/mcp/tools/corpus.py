"""Building the corpus and matching it to tracks.

An assistant that can query the corpus but not fill it can only tell someone to
go and run a command, which ends the conversation the surface exists to have.
Neither of these touches the user's account: fetching reads Wikipedia and writes
the repository's chart files, and resolving reads a catalogue and writes a
machine-local cache.
"""

from jukebox.charts.chart import Chart, chart_named
from jukebox.charts.chart_source import ChartSource
from jukebox.charts.fetch import Fetch
from jukebox.charts.registry import Registry
from jukebox.mcp.errors import TooManyYears
from jukebox.mcp.resolve_request import ResolveRequest
from jukebox.mcp.workspace import Workspace
from jukebox.net.errors import Throttled, TransientFailure
from jukebox.ports.music_catalog import MusicCatalog
from jukebox.resolve.backfill import Backfill
from jukebox.resolve.resolver import Resolver

MAX_YEARS = 20
DEFAULT_LIMIT = 200


def fetch_charts(workspace: Workspace, source: ChartSource, years: tuple[int, int]) -> dict:
    """Fetch published chart pages into the corpus.

    Reads Wikipedia and writes the repository's chart files. Does not touch the
    user's account.
    """
    _bounded(years)
    # A list with the year in each row rather than a dict keyed by year: JSON has
    # no integer keys, so a year-keyed map reaches the caller as strings and the
    # shape it was promised is not the shape it gets.
    fetched = []
    for year in range(years[0], years[1] + 1):
        report = Fetch(Registry.billboard(), source, workspace.corpus).year(year)
        fetched.append(
            {
                "year": year,
                "charts": {found.chart.slug: found.entries for found in report.resolved},
                "unavailable": {gap.chart.slug: gap.reason.value for gap in report.gaps},
            }
        )
    return {"fetched": fetched}


def resolve_charts(workspace: Workspace, catalog: MusicCatalog, request: ResolveRequest) -> dict:
    """Match chart entries to playable tracks, keeping what is already known.

    Each unmatched entry costs a search, so a call stops after `limit` lookups
    and reports what is left; calling again continues where it stopped.

    `wanted` narrows the rows before they are paid for, so resolving what a
    spec actually selects costs what that selection costs.
    """
    _bounded(request.years)
    resolver = Resolver(catalog)
    remaining = request.limit
    covered: list[dict] = []
    for year in range(request.years[0], request.years[1] + 1):
        for chart in _charts(request.charts):
            if remaining <= 0 or not workspace.corpus.path(chart, year).exists():
                continue
            backfill = Backfill(workspace.corpus, workspace.resolutions, resolver)
            try:
                coverage = backfill.year(chart, year, request.attempt(remaining))
            except Throttled as refused:
                # The service named how long it wants; every further chart would
                # spend a request against the window it is already refusing.
                return _stopped(covered, remaining, refused)
            except TransientFailure as failed:
                # One chart being unwell is not a reason to skip the rest, and
                # what it did resolve was written on the way out.
                covered.append({"chart": chart.slug, "year": year, "failed": str(failed)})
                continue
            remaining -= coverage.attempted
            covered.append(_covered(coverage, year))
    return {"resolved": covered, "lookups_left": max(0, remaining)}


def _stopped(covered: list[dict], remaining: int, refused: Throttled) -> dict:
    return {
        "resolved": covered,
        "lookups_left": max(0, remaining),
        "stopped": str(refused),
        "retry_after_seconds": round(refused.seconds),
        # Whether the budget is spent or the pace is too fast, because only the
        # second is something the caller can do anything about but wait.
        "reason": refused.reason,
    }


def _covered(coverage, year: int) -> dict:
    return {
        "chart": coverage.chart,
        "year": year,
        "matched": coverage.resolved,
        "of": coverage.total,
        "known_missing": coverage.skipped,
        "unmatched": [
            {"title": outcome.title, "artist": outcome.artist} for outcome in coverage.unresolved
        ],
    }


def _charts(charts: list[str] | None) -> list[Chart]:
    return [chart_named(slug) for slug in charts] if charts else list(Chart)


def _bounded(years: tuple[int, int]) -> None:
    if years[1] - years[0] + 1 > MAX_YEARS:
        raise TooManyYears(years)
