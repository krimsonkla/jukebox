"""MusicBrainz's implementation of the IsrcSource port.

MusicBrainz asks for roughly one request a second and a descriptive user agent,
and answering one recording costs two calls, so this is a background pass rather
than something a resolve does inline.
"""

import time

from jukebox.net.retrying_client import RetryingClient

SEARCH_URL = "https://musicbrainz.org/ws/2/recording"
USER_AGENT = "jukebox/0.0.1 (https://github.com/krimsonkla/jukebox)"
PAUSE = 1.1


class MusicBrainzIsrcs:
    """Finds a recording's ISRCs."""

    def __init__(
        self, client: RetryingClient | None = None, sleep=time.sleep, pause: float = PAUSE
    ) -> None:
        self._client = client or RetryingClient()
        self._sleep = sleep
        self._pause = pause

    def isrcs_for(self, title: str, artist: str) -> tuple[str, ...]:
        """Every ISRC MusicBrainz knows for the best-matching recording."""
        found = self._get(
            SEARCH_URL,
            {
                "query": f'recording:"{title}" AND artist:"{artist}"',
                "fmt": "json",
                "limit": 3,
            },
        )
        for recording in found.get("recordings", [])[:2]:
            detail = self._get(f"{SEARCH_URL}/{recording['id']}", {"inc": "isrcs", "fmt": "json"})
            isrcs = tuple(detail.get("isrcs", ()))
            if isrcs:
                return isrcs
        return ()

    def _get(self, url: str, params: dict) -> dict:
        response = self._client.get(url, params=params, headers={"User-Agent": USER_AGENT})
        self._sleep(self._pause)
        response.raise_for_status()
        return response.json()
