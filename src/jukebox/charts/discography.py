"""Read an artist's discography into the corpus.

A chart article is fetched per chart and year. A discography is fetched per
artist and lands rows across many charts and many years, so it is a second
route into the same corpus rather than another entry in the registry.

What it adds is what a chart of number ones cannot hold. A single that stopped
at seven is absent from an article listing only the songs that reached first,
and most singles stop somewhere.
"""

import datetime as dt

from jukebox.charts.chart import Chart
from jukebox.charts.chart_source import ChartSource
from jukebox.charts.charted import Charted
from jukebox.charts.corpus import Corpus
from jukebox.charts.discography_report import DiscographyReport
from jukebox.charts.errors import PageNotFound
from jukebox.charts.attribution import Attribution
from jukebox.charts.grid import Grid
from jukebox.charts.mappers.discography import DiscographyMapper

SUFFIX = "discography"


class Discography:
    """Builds corpus rows from an artist's own article."""

    def __init__(self, source: ChartSource, corpus: Corpus, today: dt.date | None = None) -> None:
        self._source = source
        self._corpus = corpus
        self._today = today or dt.date.today()

    def artist(self, name: str, years: tuple[int, int]) -> DiscographyReport:
        """Read one artist's placings for a span of years into the corpus.

        An act the encyclopaedia has no article for is reported as a gap, so a
        list of artists is read to the end rather than abandoned at the first
        one nobody has written up.
        """
        title = page_for(name)
        try:
            page = self._source.fetch(title)
        except PageNotFound:
            return DiscographyReport(artist=name, title=title, found=0, added={}, missing=True)
        found = DiscographyMapper().map(Grid.every(page), name)
        wanted = [row for row in found if years[0] <= row.year <= years[1]]
        return DiscographyReport(
            artist=name,
            title=title,
            found=len(wanted),
            added=self._absorb(wanted, title),
        )

    def _absorb(self, rows: list[Charted], title: str) -> dict[Chart, int]:
        source = Attribution(title=title, retrieved=self._today)
        added: dict[Chart, int] = {}
        for chart, year in sorted({(row.chart, row.year) for row in rows}):
            entries = [row.entry for row in rows if row.chart is chart and row.year == year]
            new = self._corpus.merge(chart, year, entries, source)
            if new:
                added[chart] = added.get(chart, 0) + new
        return added


def page_for(artist: str) -> str:
    """The article holding an artist's discography."""
    return f"{artist} {SUFFIX}"
