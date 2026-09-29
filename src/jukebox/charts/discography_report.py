"""What reading one artist's discography added to the corpus."""

import dataclasses

from jukebox.charts.chart import Chart


@dataclasses.dataclass(frozen=True)
class DiscographyReport:
    """How much of an artist's record a page carried, and how much was new.

    `found` counts placings the page publishes for the years asked about, and
    `added` counts the rows the corpus did not already hold. The gap between
    them is the songs the chart's own article had already recorded, which is
    the overlap that proves the two sources agree about the same act.
    """

    artist: str
    title: str
    found: int
    added: dict[Chart, int]
    missing: bool = False
    """Whether the encyclopaedia holds no such article.

    Not every act has one, and an act whose article is absent is a gap to
    report rather than a reason to abandon the rest of a list.
    """

    @property
    def total(self) -> int:
        """Rows written across every chart."""
        return sum(self.added.values())
