"""Shape D: an artist's singles, with the peak each one reached.

A chart page answers "who was on this list"; a discography answers "where did
this act's records get to". The second reaches far deeper, because a chart
published only as number ones records nothing about a single that stopped at
three, and most singles stop somewhere.

The page is read whole. A discography separates singles from promotional
singles from other charted songs, and every one of those tables carries real
positions, so taking only the first would drop most of what the page publishes.
"""

import dataclasses
import re

from jukebox.charts.cell import titles
from jukebox.charts.chart import Chart
from jukebox.charts.chart_columns import charted_by
from jukebox.charts.charted import Charted
from jukebox.charts.entry import ChartEntry
from jukebox.charts.entry_kind import EntryKind
from jukebox.charts.grid import Grid

TITLE, YEAR = "Title", "Year"

# What a discography prints where there is no position. A dash, in any of the
# three widths editors use, says the record did not chart; a cross says the
# chart did not yet exist. Neither is a position, so neither becomes a row.
BLANK = frozenset(
    {
        "\u2014",  # em dash
        "\u2013",  # en dash
        "-",  # hyphen-minus
        "\u00d7",  # multiplication sign, written for a cross
        "x",
        "N/A",
        "",
    }
)


_LEADING = re.compile(r"\d+")


@dataclasses.dataclass(frozen=True)
class _Layout:
    """Where a table keeps the song, the year, and the charts."""

    at: int
    title: int
    year: int
    charts: dict[int, Chart]
    width: int


class DiscographyMapper:
    """Reads an artist's discography into rows for many charts and years."""

    def map(self, grids: list[Grid], artist: str) -> list[Charted]:
        """Every placing the page publishes, for every table that carries one."""
        return [row for grid in grids for row in _table(grid, artist)]


def _table(grid: Grid, artist: str) -> list[Charted]:
    layout = _layout(grid)
    if layout is None:
        return []
    rows = grid.rows[layout.at + 1 :]
    return [row for cells in rows for row in _row(cells, layout, artist)]


def _layout(grid: Grid) -> _Layout | None:
    """Where the columns are named, and which of them carry a chart.

    A discography groups its chart columns under one `Peak chart positions`
    cell that spans them all, so one row names the group and the next names the
    charts. Expanding the span leaves both opening the same way, so the row to
    read is whichever names charts. Either the song or the year may come first,
    which is an editorial habit rather than a meaning.
    """
    best = None
    for at, row in enumerate(grid.rows[:2]):
        heads = row[:2]
        if len(row) <= 2 or TITLE not in heads or YEAR not in heads:
            continue
        charts = _charts(row)
        if charts and (best is None or len(charts) > len(best.charts)):
            best = _Layout(
                at=at,
                title=heads.index(TITLE),
                year=heads.index(YEAR),
                charts=charts,
                width=len(row),
            )
    return best


def _charts(header: list[str]) -> dict[int, Chart]:
    """Which columns hold a chart this project reads, first naming of each."""
    found: dict[int, Chart] = {}
    for index, name in enumerate(header[2:], start=2):
        chart = charted_by(name)
        if chart is not None and chart not in found.values():
            found[index] = chart
    return found


def _row(cells: list[str], layout: _Layout, artist: str) -> list[Charted]:
    if len(cells) != layout.width or cells[layout.title] == TITLE:
        return []
    named = titles(cells[layout.title])
    year = cells[layout.year].strip()[:4]
    if not named or not year.isdigit():
        return []
    return [
        Charted(
            chart=chart,
            year=int(year),
            entry=ChartEntry(
                kind=EntryKind.PEAK,
                rank=peak,
                title=named[0],
                also=tuple(named[1:]) or None,
                artist=artist,
            ),
        )
        for index, chart in layout.charts.items()
        if (peak := _peak(cells[index])) is not None
    ]


def _peak(cell: str) -> int | None:
    """The position a cell records, where it records one.

    A cell can carry a footnote beside the number, spaced or not, so the
    leading digits are read rather than the whole word. Anything not starting
    with a digit records no position.
    """
    text = cell.strip()
    if text in BLANK:
        return None
    digits = _LEADING.match(text)
    return int(digits.group()) if digits else None
