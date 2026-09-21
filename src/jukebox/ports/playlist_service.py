"""The port a reconciler writes playlists through.

Deliberately four operations. A reconciler works out the whole final ordering
before it writes anything, so replacing a list is the only mutation it needs;
adding, removing and reordering are the same call with different arguments and
three more chances to get an edit wrong.
"""

from typing import Protocol

from jukebox.ports.playlist_ref import PlaylistRef


class PlaylistService(Protocol):
    """Somewhere playlists can be read and written."""

    def create(self, name: str, description: str = "") -> PlaylistRef:
        """A new, empty playlist owned by the authorized user."""
        raise NotImplementedError

    def find(self, playlist_id: str) -> PlaylistRef | None:
        """The playlist, or None if it no longer exists."""
        raise NotImplementedError

    def items(self, playlist_id: str) -> list[str]:
        """Every track URI on the playlist, in order."""
        raise NotImplementedError

    def replace(self, playlist_id: str, uris: list[str]) -> None:
        """Make the playlist hold exactly these URIs, in this order."""
        raise NotImplementedError
