"""Reading the chart corpus.

Query functions rather than a finished answer: a tool that returned a tracklist
would answer only the question its author imagined, and the whole point of the
corpus is that a model can compose over it.
"""

from jukebox.charts.chart import Chart, chart_named
from jukebox.charts.entry_filter import EntryFilter
from jukebox.mcp.chart_query import ChartQuery

from jukebox.mcp.workspace import Workspace

# Chart text is publicly editable, so what reaches the model is bounded as
# well as marked untrusted in the server instructions.
FIELD = 200


def list_charts(workspace: Workspace, years: tuple[int, int] = (1980, 1999)) -> dict:
    """Which charts the corpus holds, and for which years."""
    coverage: dict[str, list[int]] = {}
    for chart in Chart:
        held = [
            year
            for year in range(years[0], years[1] + 1)
            if workspace.corpus.path(chart, year).exists()
        ]
        if held:
            coverage[chart.slug] = held
    return {"charts": coverage, "empty": not coverage}


def query_charts(workspace: Workspace, query: ChartQuery) -> dict:
    """Chart entries matching a query, in chart order."""
    rows: list[dict] = []
    for slug in query.charts:
        chart = chart_named(slug)
        for year in range(query.years[0], query.years[1] + 1):
            if not workspace.corpus.path(chart, year).exists():
                continue
            rows += _rows(workspace, chart, year, query.rows)
    return {
        "total": len(rows),
        "entries": rows[: query.limit],
        "truncated": len(rows) > query.limit,
    }


def _rows(workspace: Workspace, chart: Chart, year: int, wanted: EntryFilter) -> list[dict]:
    found = []
    for entry in workspace.corpus.read(chart, year).entries:
        if not wanted.matches(entry):
            continue
        found.append(
            {
                "chart": chart.slug,
                "year": year,
                "title": entry.title[:FIELD],
                "artist": entry.artist[:FIELD],
                "rank": entry.rank,
                "weeks_at_number_one": entry.weeks,
            }
        )
    return found
