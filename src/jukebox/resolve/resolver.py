"""Turn a chart entry into a playable track, or say why not.

Search leads and ISRC assists, which is the opposite of the order the design
assumed. Measured against the 1985 Hot 100, MusicBrainz carried an ISRC for
three entries in twenty-five; search answered twenty-two of the remainder. An
exact identifier is worth taking when it is there, but at roughly two seconds a
lookup it does not earn a place in the default path.
"""

from jukebox.ports.isrc_source import IsrcSource
from jukebox.ports.music_catalog import MusicCatalog
from jukebox.ports.track_match import TrackMatch
from jukebox.text.artists import credited
from jukebox.resolve.method import Method
from jukebox.resolve.outcome import Outcome
from jukebox.resolve.score import Score
from jukebox.resolve.sought import Sought

THRESHOLD = 0.72


class Resolver:
    """Matches chart entries against a catalogue."""

    def __init__(
        self, catalog: MusicCatalog, isrcs: IsrcSource | None = None, threshold: float = THRESHOLD
    ) -> None:
        self._catalog = catalog
        self._isrcs = isrcs
        self._threshold = threshold

    def resolve(self, title: str, artist: str, year: int) -> Outcome:
        """The best candidate above the threshold, or an unresolved outcome."""
        sought = Sought(title=title, artist=artist, year=year)
        by_isrc = self._from_isrc(title, artist)
        if by_isrc is not None:
            return by_isrc
        return _best(self._candidates(title, artist), sought, self._threshold, Method.SEARCH)

    def _from_isrc(self, title: str, artist: str) -> Outcome | None:
        if self._isrcs is None:
            return None
        for isrc in self._isrcs.isrcs_for(title, artist):
            for candidate in self._catalog.by_isrc(isrc):
                return Outcome(
                    title=title,
                    artist=artist,
                    match=candidate,
                    score=None,
                    method=Method.ISRC,
                )
        return None

    def _candidates(self, title: str, artist: str) -> list[TrackMatch]:
        """Search once per credited artist, because a conjunction matches nothing."""
        found: dict[str, TrackMatch] = {}
        for name in credited(artist):
            for candidate in self._catalog.search(title, name):
                found.setdefault(candidate.uri, candidate)
            if found:
                break
        return list(found.values())


def _best(
    candidates: list[TrackMatch], sought: Sought, threshold: float, method: Method
) -> Outcome:
    if not candidates:
        return Outcome(
            title=sought.title, artist=sought.artist, match=None, score=None, method=None
        )
    scored = sorted(
        ((Score.of(candidate, sought), candidate) for candidate in candidates),
        key=lambda pair: pair[0].value,
        reverse=True,
    )
    score, candidate = scored[0]
    if score.value < threshold:
        return Outcome(
            title=sought.title,
            artist=sought.artist,
            match=None,
            score=score,
            method=None,
            rejected=tuple(item for _, item in scored),
        )
    return Outcome(
        title=sought.title, artist=sought.artist, match=candidate, score=score, method=method
    )
