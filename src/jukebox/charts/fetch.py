"""Fetch one year of charts into the corpus.

The composition point for the module: registry to source to grid to mapper to
corpus, with the gaps carried through to the report rather than dropped.
"""

import datetime as dt
import pathlib

from jukebox.charts.chart_file import ChartFile
from jukebox.charts.chart_source import ChartSource
from jukebox.charts.corpus import Corpus
from jukebox.charts.entry import ChartEntry
from jukebox.charts.entry_kind import EntryKind
from jukebox.charts.grid import Grid
from jukebox.charts.mappers import DecadeMapper, NumberOnesMapper, RankedMapper
from jukebox.charts.page_ref import PageRef
from jukebox.charts.page_shape import PageShape
from jukebox.charts.registry import Registry
from jukebox.paths import Paths
from jukebox.charts.report import CoverageReport
from jukebox.charts.resolved import Resolved


class Fetch:
    """Builds one year of the corpus."""

    def __init__(
        self, registry: Registry, source: ChartSource, corpus: Corpus, today: dt.date | None = None
    ) -> None:
        self._registry = registry
        self._source = source
        self._corpus = corpus
        self._today = today or dt.date.today()

    def year(self, year: int) -> CoverageReport:
        """Fetch, parse and write every chart the registry resolves for `year`."""
        resolved = [self._one(ref, year) for ref in self._registry.resolved(year)]
        return CoverageReport(year=year, resolved=resolved, gaps=self._registry.gaps(year))

    def _one(self, ref: PageRef, year: int) -> Resolved:
        grid = Grid.of(self._source.fetch(ref.title))
        entries = map_page(ref, grid, year)
        self._corpus.write(
            ChartFile(
                chart=ref.chart,
                year=year,
                kind=entries[0].kind if entries else EntryKind.NUMBER_ONE,
                source=ref.title,
                retrieved=self._today,
                entries=entries,
            )
        )
        return Resolved(chart=ref.chart, title=ref.title, entries=len(entries))


def map_page(ref: PageRef, grid: Grid, year: int) -> list[ChartEntry]:
    """The entries of one page, read through the mapper its shape names."""
    if ref.shape is PageShape.RANKED:
        return RankedMapper().map(grid)
    if ref.shape is PageShape.DECADE:
        return DecadeMapper().map(grid, year)
    return NumberOnesMapper().map(grid, year, column=ref.column)


def corpus_root(override: pathlib.Path | None = None) -> pathlib.Path:
    """Where the corpus lives: the user's cache unless told otherwise."""
    return override or Paths.resolve().charts
