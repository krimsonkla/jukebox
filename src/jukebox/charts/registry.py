"""Which page holds which chart in which year.

Billboard renamed charts mid-era — Hot Black Singles became Hot R&B Singles,
and the rock charts are published a decade at a time. All of that drift lives
here as declared data, so nothing else in the module branches on a year.
Spec §Acceptance criteria 4, 5.
"""

from dataclasses import dataclass

from jukebox.charts.chart import Chart
from jukebox.charts.gap import Gap
from jukebox.charts.gap_reason import GapReason
from jukebox.charts.page_ref import PageRef
from jukebox.charts.page_shape import PageShape
from jukebox.charts.registry_entry import RegistryEntry

_RANKED = PageShape.RANKED
_ONES = PageShape.NUMBER_ONES
_DECADE = PageShape.DECADE

# Only ranges confirmed to parse against the live encyclopaedia are declared —
# resolving to a page is not enough, since several years tabulate the same chart
# under different columns. An unconfirmed guess fails at fetch time; an
# undeclared chart is a gap the report names, which is the honest of the two.
_BILLBOARD = (
    RegistryEntry(
        Chart.HOT_100, 1980, 1999, "Billboard Year-End Hot 100 singles of {year}", _RANKED
    ),
    RegistryEntry(Chart.RNB, 1980, 1981, "Billboard Year-End Hot Soul Singles of {year}", _RANKED),
    RegistryEntry(Chart.RNB, 1982, 1989, "Billboard Year-End Hot Black Singles of {year}", _RANKED),
    RegistryEntry(Chart.RNB, 1990, 1998, "Billboard Year-End Hot R&B Singles of {year}", _RANKED),
    RegistryEntry(
        Chart.RNB,
        1999,
        1999,
        "Billboard Year-End Hot R&B/Hip-Hop Singles & Tracks of {year}",
        _RANKED,
    ),
    RegistryEntry(Chart.RAP, 1989, 1999, "Billboard Year-End Hot Rap Singles of {year}", _RANKED),
    RegistryEntry(
        Chart.COUNTRY, 1980, 1989, "List of Hot Country Singles number ones of {year}", _ONES
    ),
    RegistryEntry(
        Chart.COUNTRY,
        1990,
        1999,
        "List of Hot Country Singles & Tracks number ones of {year}",
        _ONES,
    ),
    # The dance chart is one list until 1985, then a club chart and a sales
    # chart tabulated side by side, and it changes title in 1988.
    RegistryEntry(
        Chart.DANCE_CLUB,
        1982,
        1984,
        "List of Billboard number-one dance/disco singles of {year}",
        _ONES,
    ),
    RegistryEntry(
        Chart.DANCE_CLUB,
        1985,
        1987,
        "List of Billboard number-one dance/disco singles of {year}",
        _ONES,
        column="Club Play",
    ),
    RegistryEntry(
        Chart.DANCE_CLUB,
        1988,
        1999,
        "List of Billboard number-one dance singles of {year}",
        _ONES,
        column="Club Play",
    ),
    RegistryEntry(
        Chart.DANCE_SALES,
        1985,
        1987,
        "List of Billboard number-one dance/disco singles of {year}",
        _ONES,
        column="Sales",
    ),
    RegistryEntry(
        Chart.DANCE_SALES,
        1988,
        1999,
        "List of Billboard number-one dance singles of {year}",
        _ONES,
        column="Sales",
    ),
    RegistryEntry(
        Chart.MODERN_ROCK,
        1988,
        1989,
        "List of Billboard Modern Rock Tracks number ones of the 1980s",
        _DECADE,
    ),
    RegistryEntry(
        Chart.MODERN_ROCK,
        1990,
        1999,
        "List of Billboard Modern Rock Tracks number ones of the 1990s",
        _DECADE,
    ),
    RegistryEntry(
        Chart.MAINSTREAM_ROCK,
        1981,
        1989,
        "List of Billboard Mainstream Rock number-one songs of the 1980s",
        _ONES,
    ),
    RegistryEntry(
        Chart.MAINSTREAM_ROCK,
        1990,
        1999,
        "List of Billboard Mainstream Rock number-one songs of the 1990s",
        _ONES,
    ),
    RegistryEntry(
        Chart.LATIN,
        1986,
        1989,
        "List of number-one Billboard Top Latin Songs from the 1980s",
        _DECADE,
    ),
    RegistryEntry(
        Chart.LATIN, 1990, 1999, "List of number-one Billboard Hot Latin Tracks of {year}", _ONES
    ),
)


@dataclass(frozen=True)
class Registry:
    """The declared (chart, year) to page mapping, and the gaps it leaves."""

    entries: tuple[RegistryEntry, ...]

    @classmethod
    def billboard(cls) -> "Registry":
        """The Billboard charts this project covers."""
        return cls(entries=_BILLBOARD)

    def resolve(self, chart: Chart, year: int) -> PageRef | Gap:
        """The page for this chart and year, or the gap explaining its absence."""
        for entry in self.entries:
            if entry.chart is chart and entry.covers(year):
                return PageRef(
                    chart, year, entry.title.format(year=year), entry.shape, entry.column
                )
        if year < chart.began:
            return Gap(chart, year, GapReason.CHART_DID_NOT_EXIST)
        return Gap(chart, year, GapReason.NO_ARTICLE)

    def resolved(self, year: int) -> list[PageRef]:
        """Every chart with a page this year."""
        found = (self.resolve(chart, year) for chart in Chart)
        return [ref for ref in found if isinstance(ref, PageRef)]

    def gaps(self, year: int) -> list[Gap]:
        """Every chart without one, each carrying its reason."""
        found = (self.resolve(chart, year) for chart in Chart)
        return [gap for gap in found if isinstance(gap, Gap)]
