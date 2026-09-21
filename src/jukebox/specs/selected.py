"""One chart entry chosen by a spec, with where it came from."""

import dataclasses

from jukebox.charts.chart import Chart
from jukebox.charts.entry import ChartEntry


@dataclasses.dataclass(frozen=True)
class Selected:
    """A chart entry and its provenance.

    The chart and year travel with the entry because the tracklist is ordered by
    them, and because resolution happens later and needs the year.
    """

    chart: Chart
    year: int
    entry: ChartEntry

    @property
    def title(self) -> str:
        """The song."""
        return self.entry.title

    @property
    def artist(self) -> str:
        """Who charted it."""
        return self.entry.artist
