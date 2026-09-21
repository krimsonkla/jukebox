"""One song's showing on one chart in one year."""

import datetime as dt

from pydantic import BaseModel

from jukebox.charts.chart import Chart
from jukebox.charts.entry_kind import EntryKind


class Appearance(BaseModel):
    """What a chart published about a song that year.

    The measures a row carries follow from its kind, so a year-end showing has
    a rank and a number one has a date and a duration. Neither is converted
    into the other: they are different published measures, and a number that
    ranked one against the other would be invented here.
    """

    chart: Chart
    year: int
    kind: EntryKind
    rank: int | None = None
    reached: dt.date | None = None
    weeks: int | None = None

    def order(self) -> tuple:
        """Sort key: by year, then by the chart's own measure."""
        return (self.year, self.chart.slug, self.rank or 0, self.reached or dt.date.min)
