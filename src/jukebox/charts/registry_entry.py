"""One declared range of years for one chart."""

from dataclasses import dataclass

from jukebox.charts.chart import Chart
from jukebox.charts.page_shape import PageShape


@dataclass(frozen=True)
class RegistryEntry:
    """A chart's page title over a span of years.

    `title` is a format string taking `year`; decade pages ignore it and name
    the decade instead.
    """

    chart: Chart
    first: int
    last: int
    title: str
    shape: PageShape
    column: str | None = None

    def covers(self, year: int) -> bool:
        """Whether this entry declares a page for `year`."""
        return self.first <= year <= self.last
