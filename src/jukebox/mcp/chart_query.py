"""A question asked of the chart corpus."""

import dataclasses

from jukebox.charts.entry_filter import EntryFilter


@dataclasses.dataclass(frozen=True)
class ChartQuery:
    """Which charts, which years, and how to narrow the rows within them."""

    charts: list[str]
    years: tuple[int, int]
    rows: EntryFilter = dataclasses.field(default_factory=EntryFilter)
    limit: int = 100
