"""A song, and everywhere the corpus saw it."""

from pydantic import BaseModel

from jukebox.charts.chart import Chart
from jukebox.songs.appearance import Appearance


class Song(BaseModel):
    """One recording, with every chart showing the corpus holds for it.

    `title` and `artist` are kept as a chart published them, because what the
    corpus says is the fact and the reduced identity is only how two spellings
    are recognised as one.
    """

    key: str
    title: str
    artist: str
    appearances: tuple[Appearance, ...] = ()

    @property
    def charts(self) -> tuple[str, ...]:
        """Every chart this song appeared on, in corpus order."""
        return tuple(dict.fromkeys(appearance.chart.slug for appearance in self.appearances))

    @property
    def years(self) -> tuple[int, ...]:
        """Every year it appeared, earliest first."""
        return tuple(sorted({appearance.year for appearance in self.appearances}))

    @property
    def best_rank(self) -> int | None:
        """The highest year-end placing it reached, if any chart ranked it."""
        ranks = [a.rank for a in self.appearances if a.rank is not None]
        return min(ranks) if ranks else None

    @property
    def weeks_at_number_one(self) -> int:
        """Weeks spent at number one, summed across the charts that had it there."""
        return sum(appearance.weeks or 0 for appearance in self.appearances)

    def crossed(self, charts: tuple[Chart, ...]) -> bool:
        """Whether it appeared on every one of these charts."""
        held = set(self.charts)
        return all(chart.slug in held for chart in charts)
