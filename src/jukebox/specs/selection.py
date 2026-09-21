"""Which chart entries a spec draws from."""

from pydantic import BaseModel, Field

from jukebox.charts.chart import Chart
from jukebox.charts.entry_filter import EntryFilter


class Selection(BaseModel):
    """A predicate over the corpus, in the charts' own vocabulary.

    The row-level measures are named here rather than nested, because a spec is
    a file a person writes and reads. What they mean, and which rows they leave
    alone, is `EntryFilter`'s business and is stated once there.
    """

    charts: list[Chart] = Field(min_length=1)
    years: tuple[int, int]
    max_rank: int | None = None
    min_weeks: int | None = None
    artist: str | None = None
    title: str | None = None

    def covers(self, year: int) -> bool:
        """Whether this selection includes a year."""
        first, last = self.years
        return first <= year <= last

    def span(self) -> range:
        """Every year the selection names."""
        first, last = self.years
        return range(first, last + 1)

    def rows(self) -> EntryFilter:
        """The row-level predicate this selection names."""
        return EntryFilter(
            max_rank=self.max_rank,
            min_weeks=self.min_weeks,
            artist=self.artist,
            title=self.title,
        )
