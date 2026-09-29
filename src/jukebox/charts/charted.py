"""One song's placing on one chart in one year."""

import dataclasses

from jukebox.charts.chart import Chart
from jukebox.charts.entry import ChartEntry


@dataclasses.dataclass(frozen=True)
class Charted:
    """A corpus row and where it belongs.

    A chart page already knows its chart and its year, so its mapper returns
    bare rows. A discography does not: one table holds several charts and
    twenty years, so each row has to carry its own destination.
    """

    chart: Chart
    year: int
    entry: ChartEntry
