"""What one attempt at a chart entry produced."""

import dataclasses

from jukebox.ports.track_match import TrackMatch
from jukebox.resolve.method import Method
from jukebox.resolve.score import Score


@dataclasses.dataclass(frozen=True)
class Outcome:
    """A resolved entry, or a reasoned refusal to guess.

    An unresolved entry is data: a playlist that silently drops it is shorter
    than the chart, and nothing says why.
    """

    title: str
    artist: str
    match: TrackMatch | None
    score: Score | None
    method: Method | None
    rejected: tuple[TrackMatch, ...] = ()

    @property
    def resolved(self) -> bool:
        """Whether this attempt produced a track."""
        return self.match is not None
