"""One chart, one year, as the corpus stores it."""

from pydantic import BaseModel

from jukebox.charts.attribution import Attribution
from jukebox.charts.chart import Chart
from jukebox.charts.entry import ChartEntry


class ChartFile(BaseModel):
    """Everything a corpus file holds, including where it came from.

    There is no file-level measure, because one file can hold rows of more than
    one: an article of number ones says who reached the top, and a discography
    says where the records that did not stopped. Each row carries its own kind.
    """

    chart: Chart
    year: int
    sources: list[Attribution]
    entries: list[ChartEntry]

    def sorted_entries(self) -> list[ChartEntry]:
        """The entries in the stable order the corpus writes them."""
        return sorted(self.entries, key=lambda entry: entry.order())

    def sorted_sources(self) -> list[Attribution]:
        """The sources in a stable order, so a re-fetch rewrites the same bytes."""
        return sorted(self.sources, key=lambda source: source.title)
