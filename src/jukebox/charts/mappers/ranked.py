"""Shape A: a year-end chart, ranked one to a hundred.

Spec §Acceptance criteria 2.
"""

from jukebox.charts.cell import titles
from jukebox.charts.entry import ChartEntry
from jukebox.charts.entry_kind import EntryKind
from jukebox.charts.errors import UnexpectedColumns
from jukebox.charts.grid import Grid

# Each publisher heads the same three columns its own way, and a fourth column
# such as a country of origin is ignored rather than refused.
RANK_HEADERS = ("No.", "№", "#")
TITLE_HEADERS = ("Title", "Song")
ARTIST_HEADERS = ("Artist(s)", "Artist")


class RankedMapper:
    """Reads a rank / title / artist table."""

    def map(self, grid: Grid) -> list[ChartEntry]:
        """Every ranked row of the table.

        Takes no year: a year-end table already is one year, and the corpus file
        records which. Spec §Corpus on disk.
        """
        header = grid.rows[0]
        if not _heads(header):
            raise UnexpectedColumns("ranked", header)
        return [entry for row in grid.rows[1:] if (entry := _row(row)) is not None]


def _heads(header: list[str]) -> bool:
    """Whether the first three columns rank, name and credit."""
    if len(header) < 3:
        return False
    return header[0] in RANK_HEADERS and header[1] in TITLE_HEADERS and header[2] in ARTIST_HEADERS


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
