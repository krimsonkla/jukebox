"""One chart the corpus does cover this year."""

from dataclasses import dataclass

from jukebox.charts.chart import Chart


@dataclass(frozen=True)
class Resolved:
    """A chart that was fetched, and how much of it there was."""

    chart: Chart
    title: str
    entries: int
