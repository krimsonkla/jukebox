"""A playlist service that lives entirely in memory.

Shared, because both the reconciler suite and the command suite need one and a
second copy would drift from the first.
"""

from jukebox.ports import PlaylistRef


class FakePlaylists:
    """Records every write, so a test can assert what reached the account."""

    def __init__(self, existing: dict[str, list[str]] | None = None) -> None:
        self.playlists = existing or {}
        self.created: list[str] = []
        self.descriptions: list[str] = []
        self.writes: list[tuple[str, list[str]]] = []

    def create(self, name: str, description: str = "") -> PlaylistRef:
        """A new empty playlist."""
        playlist_id = f"pl{len(self.playlists) + 1}"
        self.playlists[playlist_id] = []
        self.created.append(name)
        self.descriptions.append(description)
        return PlaylistRef(id=playlist_id, name=name)

    def find(self, playlist_id: str) -> PlaylistRef | None:
        """The playlist, or None."""
        if playlist_id not in self.playlists:
            return None
        return PlaylistRef(id=playlist_id, name="x")

    def items(self, playlist_id: str) -> list[str]:
        """What is on it."""
        return list(self.playlists[playlist_id])

    def replace(self, playlist_id: str, uris: list[str]) -> None:
        """Overwrite it."""
        self.playlists[playlist_id] = list(uris)
        self.writes.append((playlist_id, list(uris)))
