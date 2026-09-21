"""How well a candidate answers a chart entry.

Title and artist similarity carry the decision; the release year only breaks
ties, because a 1985 recording reissued on a 2010 compilation is the same master
and rejecting it would lose the match rather than improve it.
"""

import dataclasses
import datetime as dt

from rapidfuzz import fuzz

from jukebox.ports.track_match import TrackMatch
from jukebox.resolve.markers import penalty
from jukebox.text.normalize import core_artist, core_title
from jukebox.resolve.sought import Sought

TITLE_WEIGHT = 0.6
ARTIST_WEIGHT = 0.4
ERA_BONUS = 0.05
ERA_YEARS = 2


@dataclasses.dataclass(frozen=True)
class Score:
    """A candidate's fitness, and the parts that produced it."""

    value: float
    title: float
    artist: float
    penalty: float

    @classmethod
    def of(cls, candidate: TrackMatch, sought: Sought) -> "Score":
        """Score one candidate against the chart entry it might answer."""
        title_ratio = _ratio(core_title(candidate.title), core_title(sought.title))
        artist_ratio = _ratio(core_artist(candidate.artist), core_artist(sought.artist))
        deduction = penalty(candidate.title, candidate.album)
        base = TITLE_WEIGHT * title_ratio + ARTIST_WEIGHT * artist_ratio
        return cls(
            value=base + _era(candidate.released, sought.year) - deduction,
            title=title_ratio,
            artist=artist_ratio,
            penalty=deduction,
        )


def _ratio(left: str, right: str) -> float:
    return fuzz.token_sort_ratio(left, right) / 100.0


def _era(released: dt.date | None, year: int) -> float:
    if released is None:
        return 0.0
    return ERA_BONUS if abs(released.year - year) <= ERA_YEARS else 0.0
