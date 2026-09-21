"""The port a resolver searches through.

Everything above this names no music service, so resolving a chart entry to a
playable track is the same operation whichever catalogue answers it.
"""

from typing import Protocol

from jukebox.ports.track_match import TrackMatch


class MusicCatalog(Protocol):
    """Somewhere recordings can be looked up."""

    def search(self, title: str, artist: str) -> list[TrackMatch]:
        """Candidates for a title and artist, best first as the service ranks them."""
        raise NotImplementedError

    def by_isrc(self, isrc: str) -> list[TrackMatch]:
        """Candidates carrying an exact recording identifier."""
        raise NotImplementedError
