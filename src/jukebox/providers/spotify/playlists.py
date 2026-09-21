"""Spotify's implementation of the PlaylistService port.

Playlist items moved to `/playlists/{id}/items` in February 2026, and each entry
now nests its track under `item` rather than `track`. Both a page of reads and a
write are capped at fifty and a hundred respectively, so paging and chunking are
this adapter's business and not the reconciler's.
"""

from jukebox.net.retrying_client import RetryingClient
from jukebox.providers.spotify.client import spotify_client
from jukebox.ports.credentials import Credentials
from jukebox.ports.playlist_ref import PlaylistRef

API = "https://api.spotify.com/v1"
PAGE = 50
CHUNK = 100


class SpotifyPlaylists:
    """Reads and writes playlists on the authorized user's account."""

    def __init__(self, credentials: Credentials, client: RetryingClient | None = None) -> None:
        self._credentials = credentials
        self._client = client or spotify_client()

    def create(self, name: str, description: str = "") -> PlaylistRef:
        """A new private playlist owned by the authorized user."""
        body = self._send(
            "POST",
            f"{API}/me/playlists",
            {"name": name, "description": description, "public": False},
        )
        return _ref(body)

    def find(self, playlist_id: str) -> PlaylistRef | None:
        """The playlist, or None if it is gone."""
        response = self._client.get(f"{API}/playlists/{playlist_id}", headers=self._headers())
        if response.status_code in (403, 404):
            return None
        response.raise_for_status()
        return _ref(response.json())

    def items(self, playlist_id: str) -> list[str]:
        """Every track URI, in order, across as many pages as there are."""
        uris: list[str] = []
        offset = 0
        while True:
            page = self._page(playlist_id, offset)
            uris += [uri for uri in (_uri_of(row) for row in page.get("items", [])) if uri]
            if not page.get("next"):
                return uris
            offset += PAGE

    def replace(self, playlist_id: str, uris: list[str]) -> None:
        """Make the playlist hold exactly these URIs, in this order."""
        head, rest = uris[:CHUNK], uris[CHUNK:]
        self._send("PUT", f"{API}/playlists/{playlist_id}/items", {"uris": head})
        for start in range(0, len(rest), CHUNK):
            self._send(
                "POST",
                f"{API}/playlists/{playlist_id}/items",
                {"uris": rest[start : start + CHUNK]},
            )

    def _page(self, playlist_id: str, offset: int) -> dict:
        response = self._client.get(
            f"{API}/playlists/{playlist_id}/items",
            params={"limit": PAGE, "offset": offset},
            headers=self._headers(),
        )
        response.raise_for_status()
        return response.json()

    def _send(self, method: str, url: str, body: dict) -> dict:
        """A write, retried on the statuses that pass on their own.

        A long playlist is more than one request, so a rate limit part-way
        through would otherwise leave it truncated. The write path needs the
        waiting the read path already had.
        """
        response = self._client.send(method, url, json=body, headers=self._headers())
        response.raise_for_status()
        return response.json() if response.content else {}

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self._credentials.bearer()}"}


def _ref(body: dict) -> PlaylistRef:
    return PlaylistRef(
        id=body["id"],
        name=body.get("name", ""),
        url=body.get("external_urls", {}).get("spotify", ""),
    )


def _uri_of(row: dict) -> str | None:
    """A row's track URI, skipping local files and anything that is not a track."""
    if row.get("is_local"):
        return None
    track = row.get("item") or row.get("track") or {}
    return track.get("uri") if track.get("type", "track") == "track" else None
