"""Which chart entries a spec draws from."""

from pydantic import BaseModel, ConfigDict, Field

from jukebox.charts.chart import Chart
from jukebox.charts.entry_filter import EntryFilter, Names


class Selection(BaseModel):
    """A predicate over the corpus, in the charts' own vocabulary.

    The row-level measures are named here rather than nested, because a spec is
    a file a person writes and reads. What they mean, and which rows they leave
    alone, is `EntryFilter`'s business and is stated once there.

    Naming acts under `artists` is what makes a collection expressible: a chart
    is a genre, and a set of acts is a cut across one.
    """

    model_config = ConfigDict(extra="forbid")
    """A measure this selection does not know is refused rather than ignored.

    A spec is a file someone wrote by hand and keeps. A key silently dropped is
    a narrowing silently dropped, and the playlist that follows is the whole
    chart where one artist was asked for.
    """

    charts: list[Chart] = Field(min_length=1)
    years: tuple[int, int]
    max_rank: int | None = None
    max_peak: int | None = None
    min_weeks: int | None = None
    artists: Names = []
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
            max_peak=self.max_peak,
            min_weeks=self.min_weeks,
            artists=self.artists,
            title=self.title,
        )
