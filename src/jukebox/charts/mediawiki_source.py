"""Rendered chart pages from Wikipedia.

`action=parse` is used rather than raw wikitext because it expands the
sortname, sort and dts templates the chart tables are built from, and emits
rowspan as an attribute a table parser can honour. Spec §Parse rendered HTML.
"""

import time

from jukebox.charts.errors import PageNotFound
from jukebox.net.retrying_client import RetryingClient

API = "https://en.wikipedia.org/w/api.php"
USER_AGENT = "jukebox/0.0.1 (https://github.com/krimsonkla/jukebox)"

# Publishing multiplies the caller: every clone runs the same burst under one
# user agent, so a twenty-year fetch paces itself rather than relying on the
# encyclopaedia's patience.
PAUSE = 0.2


class MediaWikiSource:
    """Fetches a page's rendered HTML through the MediaWiki parse API."""

    def __init__(
        self, client: RetryingClient | None = None, sleep=time.sleep, pause: float = PAUSE
    ) -> None:
        self._client = client or RetryingClient()
        self._sleep = sleep
        self._pause = pause

    def fetch(self, title: str) -> str:
        """The rendered HTML for `title`."""
        response = self._client.get(
            API,
            params={
                "action": "parse",
                "page": title,
                "prop": "text",
                "format": "json",
                "formatversion": "2",
            },
            headers={"User-Agent": USER_AGENT},
        )
        self._sleep(self._pause)
        response.raise_for_status()
        payload = response.json()
        if "error" in payload:
            raise PageNotFound(title)
        return payload["parse"]["text"]
