"""Shape A: a year-end chart, ranked one to a hundred.

Spec §Acceptance criteria 2.
"""

from jukebox.charts.cell import titles
from jukebox.charts.entry import ChartEntry
from jukebox.charts.entry_kind import EntryKind
from jukebox.charts.errors import UnexpectedColumns
from jukebox.charts.grid import Grid

RANK_HEADERS = ("No.", "№")
HEADERS = ("Title", "Artist(s)")


class RankedMapper:
    """Reads a rank / title / artist table."""

    def map(self, grid: Grid) -> list[ChartEntry]:
        """Every ranked row of the table.

        Takes no year: a year-end table already is one year, and the corpus file
        records which. Spec §Corpus on disk.
        """
        header = grid.rows[0]
        if header[0] not in RANK_HEADERS or tuple(header[1:3]) != HEADERS:
            raise UnexpectedColumns("ranked", header)
        return [entry for row in grid.rows[1:] if (entry := _row(row)) is not None]


def _row(row: list[str]) -> ChartEntry | None:
    if not row[0].strip().isdigit():
        return None
    named = titles(row[1])
    return ChartEntry(
        kind=EntryKind.RANKED,
        rank=int(row[0]),
        title=named[0],
        also=tuple(named[1:]) or None,
        artist=row[2].strip(),
    )
