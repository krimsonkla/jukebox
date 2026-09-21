"""A chart and year the corpus cannot cover, and why."""

from dataclasses import dataclass

from jukebox.charts.chart import Chart
from jukebox.charts.gap_reason import GapReason


@dataclass(frozen=True)
class Gap:
    """One absence, with its reason."""

    chart: Chart
    year: int
    reason: GapReason
