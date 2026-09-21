"""Shape C: a decade of number ones on one page, each row carrying its date.

Columns are located by their headers rather than by position. The rock pages
lead with the song and the Latin page leads with the artist, and a mapper that
counted from the left would read one of them backwards while parsing cleanly.

The year cannot come from a section heading — the page carries a single heading
and buries an anchor mid-cell — so it comes from the full date in the date
column. That is also what keeps the 30 December 1989 row off the 1990 chart.
Spec §Acceptance criteria 6.
"""

import datetime as dt

from jukebox.charts.cell import titles
from jukebox.charts.entry import ChartEntry
from jukebox.charts.entry_kind import EntryKind
from jukebox.charts.errors import UnexpectedColumns
from jukebox.charts.grid import Grid
from jukebox.charts.mappers.columns import Columns

TITLE_HEADERS = ("Song", "Single", "Title")
ARTIST_HEADERS = ("Artist", "Artist(s)")
DATE_HEADER = "Reached number one"
WEEKS_HEADERS = ("Weeks at number one", "Weeks")


class DecadeMapper:
    """Reads a dated number-ones table spanning a decade."""

    def map(self, grid: Grid, year: int) -> list[ChartEntry]:
        """Only the rows whose date falls in `year`."""
        header = grid.rows[0]
        columns, date_at = _columns(header)
        rows = (_row(row, columns, date_at, year) for row in grid.rows[1:])
        return [entry for entry in rows if entry is not None]


def _columns(header: list[str]) -> tuple[Columns, int]:
    title_at = _first(header, TITLE_HEADERS)
    artist_at = _first(header, ARTIST_HEADERS)
    date_at = header.index(DATE_HEADER) if DATE_HEADER in header else None
    if title_at is None or artist_at is None or date_at is None:
        raise UnexpectedColumns("decade", header)
    return Columns(title=title_at, artist=artist_at, weeks=_first(header, WEEKS_HEADERS)), date_at


def _first(header: list[str], names: tuple[str, ...]) -> int | None:
    for name in names:
        if name in header:
            return header.index(name)
    return None


def _row(row: list[str], columns: Columns, date_at: int, year: int) -> ChartEntry | None:
    reached = _date(row[date_at])
    if reached is None or reached.year != year:
        return None
    named = titles(row[columns.title])
    if not named:
        return None
    return ChartEntry(
        kind=EntryKind.NUMBER_ONE,
        title=named[0],
        also=tuple(named[1:]) or None,
        artist=row[columns.artist].strip(),
        reached=reached,
        weeks=_weeks(row, columns.weeks),
    )


def _weeks(row: list[str], weeks_at: int | None) -> int:
    if weeks_at is None or not row[weeks_at].strip().isdigit():
        return 1
    return int(row[weeks_at])


def _date(text: str) -> dt.date | None:
    try:
        return dt.datetime.strptime(text.strip(), "%B %d, %Y").date()
    except ValueError:
        return None
