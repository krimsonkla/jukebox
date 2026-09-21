"""Build a chart corpus in a temporary directory.

Three suites need one, and a corpus assembled inline in each is the same eight
lines written three times.
"""

import datetime as dt

from jukebox.charts import Chart, ChartEntry, ChartFile, Corpus, EntryKind

TODAY = dt.date(2026, 9, 7)


def write_ranked(corpus: Corpus, chart: Chart, year: int, *rows: tuple[int, str, str]) -> None:
    """A year-end chart of (rank, title, artist) rows."""
    _write(
        corpus,
        chart,
        year,
        EntryKind.RANKED,
        [
            ChartEntry(kind=EntryKind.RANKED, rank=rank, title=title, artist=artist)
            for rank, title, artist in rows
        ],
    )


def write_number_ones(
    corpus: Corpus, chart: Chart, year: int, *rows: tuple[str, str, int, int]
) -> None:
    """A number-ones chart of (title, artist, month, weeks) rows."""
    _write(
        corpus,
        chart,
        year,
        EntryKind.NUMBER_ONE,
        [
            ChartEntry(
                kind=EntryKind.NUMBER_ONE,
                title=title,
                artist=artist,
                reached=dt.date(year, month, 1),
                weeks=weeks,
            )
            for title, artist, month, weeks in rows
        ],
    )


def _write(corpus: Corpus, chart: Chart, year: int, kind: EntryKind, entries: list) -> None:
    corpus.write(
        ChartFile(chart=chart, year=year, kind=kind, source="s", retrieved=TODAY, entries=entries)
    )
