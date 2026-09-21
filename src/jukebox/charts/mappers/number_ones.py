"""Shape B: one row per issue date, sometimes for several charts at once.

Three things make these tables awkward, and all three are here rather than in
the caller. A page may tabulate two charts side by side under a spanning header
(the dance charts). A page may cover a whole decade and separate its years with
a banner row rather than a date that carries one (the mainstream rock chart). A
title held for several weeks may be written once across the rows it held, or
once with an explicit weeks column. Spec §Acceptance criteria 3, 10, 11.
"""

import datetime as dt
import re

from jukebox.charts.cell import titles
from jukebox.charts.entry import ChartEntry
from jukebox.charts.entry_kind import EntryKind
from jukebox.charts.errors import UnexpectedColumns
from jukebox.charts.grid import Grid
from jukebox.charts.mappers.columns import Columns

DATE_HEADER = "Issue date"
TITLE_HEADERS = ("Title", "Song")
ARTIST_HEADERS = ("Artist(s)", "Artist")
WEEKS_HEADER = "Weeks at number one"
ABSENT = ("Not issued", "")
SINGLE = "chart"

_YEAR = re.compile(r"^\d{4}$")


class NumberOnesMapper:
    """Reads an issue-date table, for one chart or several."""

    def map(self, grid: Grid, year: int, column: str | None = None) -> list[ChartEntry]:
        """The entries for one chart on the page, named by `column` where it holds several."""
        charts = self.split(grid, year)
        if column is not None:
            return _only_matching(charts, column)
        if len(charts) != 1:
            raise UnexpectedColumns("single-chart number-ones", sorted(charts))
        return next(iter(charts.values()))

    def split(self, grid: Grid, year: int) -> dict[str, list[ChartEntry]]:
        """Every chart the page tabulates, keyed by its spanning header."""
        if grid.rows[0][0] != DATE_HEADER:
            raise UnexpectedColumns("number-ones", grid.rows[0])
        pairs, first = _column_pairs(grid)
        weeks_at = _weeks_column(grid.rows[0])
        return {
            name: _entries(grid.rows[first:], Columns(title_at, artist_at, weeks_at), year)
            for name, title_at, artist_at in pairs
        }


def _weeks_column(header: list[str]) -> int | None:
    return header.index(WEEKS_HEADER) if WEEKS_HEADER in header else None


def _column_pairs(grid: Grid) -> tuple[list[tuple[str, int, int]], int]:
    """Locate each (title, artist) column pair, and the first data row."""
    top = grid.rows[0]
    if len(grid.rows) > 1 and grid.rows[1][1] in TITLE_HEADERS:
        return _paired(top, grid.rows[1]), 2
    return _paired([SINGLE] * len(top), top), 1


def _paired(names: list[str], headers: list[str]) -> list[tuple[str, int, int]]:
    pairs = []
    for index, header in enumerate(headers):
        following = headers[index + 1] if index + 1 < len(headers) else None
        if header in TITLE_HEADERS and following in ARTIST_HEADERS:
            pairs.append((names[index], index, index + 1))
    return pairs


def _entries(rows: list[list[str]], columns: Columns, year: int) -> list[ChartEntry]:
    runs: list[ChartEntry] = []
    banner = None
    for row in rows:
        if _is_banner(row):
            banner = int(row[0])
            continue
        if banner is not None and banner != year:
            continue
        _absorb(runs, row, columns, banner or year)
    return runs


def _is_banner(row: list[str]) -> bool:
    """A row that announces a year rather than a chart position."""
    return bool(_YEAR.match(row[0])) and len(set(row)) == 1


def _absorb(runs: list[ChartEntry], row: list[str], columns: Columns, year: int) -> None:
    named = titles(row[columns.title])
    title = named[0] if named else ""
    artist = row[columns.artist].strip()
    if title in ABSENT or not row[0].strip():
        return
    if columns.weeks is None and runs and runs[-1].title == title and runs[-1].artist == artist:
        runs[-1].weeks += 1
        return
    runs.append(
        ChartEntry(
            kind=EntryKind.NUMBER_ONE,
            title=title,
            also=tuple(named[1:]) or None,
            artist=artist,
            reached=_date(row[0], year),
            weeks=_weeks(row, columns.weeks),
        )
    )


def _weeks(row: list[str], weeks_at: int | None) -> int:
    if weeks_at is None or not row[weeks_at].strip().isdigit():
        return 1
    return int(row[weeks_at])


def _date(text: str, year: int) -> dt.date:
    return dt.datetime.strptime(f"{text.strip()} {year}", "%B %d %Y").date()


def _only_matching(charts: dict[str, list[ChartEntry]], column: str) -> list[ChartEntry]:
    for name, entries in charts.items():
        if column.lower() in name.lower():
            return entries
    raise UnexpectedColumns(f"chart matching {column!r}", sorted(charts))
