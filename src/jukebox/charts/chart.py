"""The charts this project reads, and when each one began.

A chart that did not yet exist is a different kind of absence from one whose
article was never written, and the report says which. Spec §Acceptance criteria 5.

The member value is the slug, so a corpus file round-trips through JSON as the
directory name it was written under rather than as an internal tuple.
"""

import enum

from jukebox.charts.errors import UnknownChart


class Chart(enum.StrEnum):
    """A Billboard chart, valued by its corpus directory name."""

    HOT_100 = ("hot-100", 1958)
    COUNTRY = ("country", 1944)
    RNB = ("rnb", 1942)
    RAP = ("rap", 1989)
    DANCE_CLUB = ("dance-club", 1974)
    DANCE_SALES = ("dance-sales", 1974)
    MAINSTREAM_ROCK = ("mainstream-rock", 1981)
    MODERN_ROCK = ("modern-rock", 1988)
    LATIN = ("latin", 1986)

    def __new__(cls, slug: str, began: int) -> "Chart":
        chart = str.__new__(cls, slug)
        chart._value_ = slug
        chart.began = began
        return chart

    @property
    def slug(self) -> str:
        """The corpus directory name for this chart."""
        return self.value


def chart_named(slug: str) -> Chart:
    """The chart with this slug.

    A bare `Chart(slug)` raises ValueError, which crosses the MCP boundary as a
    traceback rather than as advice a caller can act on.
    """
    try:
        return Chart(slug)
    except ValueError as unknown:
        raise UnknownChart(slug, [chart.slug for chart in Chart]) from unknown
