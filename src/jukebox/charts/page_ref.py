"""Where one chart's data lives for one year."""

from dataclasses import dataclass

from jukebox.charts.chart import Chart
from jukebox.charts.page_shape import PageShape


@dataclass(frozen=True)
class PageRef:
    """A resolved page: its title, how to read it, and which columns to take.

    `column` selects one chart from a page that tabulates several side by side,
    matched as a substring of the spanning header.
    """

    chart: Chart
    year: int
    title: str
    shape: PageShape
    column: str | None = None
