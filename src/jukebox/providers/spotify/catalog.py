"""Spotify's implementation of the MusicCatalog port.

Search returns at most ten results and the track object no longer carries
`popularity`, so nothing here ranks candidates: it reports what Spotify offered
and leaves the choice to the resolver, which can see the chart entry.
"""

import datetime as dt


from jukebox.net.retrying_client import RetryingClient
from jukebox.providers.spotify.client import spotify_client
from jukebox.ports.credentials import Credentials
from jukebox.ports.track_match import TrackMatch

SEARCH_URL = "https://api.spotify.com/v1/search"
LIMIT = 10


class SpotifyCatalog:
    """Looks recordings up in Spotify's catalogue."""

    def __init__(self, credentials: Credentials, client: RetryingClient | None = None) -> None:
        self._credentials = credentials
        self._client = client or spotify_client()

    def search(self, title: str, artist: str) -> list[TrackMatch]:
        """Candidates for a title and artist."""
        return self._query(f'track:"{_quoted(title)}" artist:"{_quoted(artist)}"')

    def by_isrc(self, isrc: str) -> list[TrackMatch]:
        """Candidates carrying this exact recording identifier."""
        return self._query(f"isrc:{isrc}")

    def _query(self, query: str) -> list[TrackMatch]:
        response = self._client.get(
            SEARCH_URL,
            params={"q": query, "type": "track", "limit": LIMIT},
            headers={"Authorization": f"Bearer {self._credentials.bearer()}"},
        )
        response.raise_for_status()
        items = response.json().get("tracks", {}).get("items", [])
        return [_match(item) for item in items]


def _match(item: dict) -> TrackMatch:
    album = item.get("album", {})
    return TrackMatch(
        uri=item["uri"],
        title=item["name"],
        artist=", ".join(a["name"] for a in item.get("artists", [])),
        album=album.get("name", ""),
        released=_released(album.get("release_date")),
    )


def _released(value: str | None) -> dt.date | None:
    if not value:
        return None
    parts = [int(part) for part in value.split("-")]
    parts += [1] * (3 - len(parts))
    return dt.date(*parts[:3])


def _quoted(text: str) -> str:
    """Chart text as a search-field value.

    A title containing a quotation mark closes the field early and the rest
    parses as further query syntax, so the result is silently wrong rather than
    absent. Titles with quotation marks are ordinary, not adversarial.
    """
    return text.replace('"', " ").strip()
