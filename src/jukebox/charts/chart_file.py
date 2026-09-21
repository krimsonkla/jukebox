"""One chart, one year, as the corpus stores it."""

import datetime as dt

from pydantic import BaseModel

from jukebox.charts.chart import Chart
from jukebox.charts.entry import ChartEntry
from jukebox.charts.entry_kind import EntryKind


class ChartFile(BaseModel):
    """Everything a corpus file holds, including where it came from."""

    chart: Chart
    year: int
    kind: EntryKind
    source: str
    retrieved: dt.date
    entries: list[ChartEntry]

    def sorted_entries(self) -> list[ChartEntry]:
        """The entries in the stable order the corpus writes them."""
        return sorted(self.entries, key=lambda entry: entry.order())
