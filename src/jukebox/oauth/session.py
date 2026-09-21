"""A stored token, kept usable.

Implements the Credentials port: callers ask for a bearer and get one that works
now, refreshed and re-stored if the one on disk had expired.
"""

from jukebox.oauth.errors import NotAuthorized
from jukebox.oauth.flow import Flow


class Session:
    """Supplies a currently valid bearer for one service."""

    def __init__(self, provider: str, flow: Flow) -> None:
        self._provider = provider
        self._flow = flow

    def bearer(self) -> str:
        """A valid access token, refreshing and re-storing it when it has expired."""
        token = self._flow.store.load()
        if token is None:
            raise NotAuthorized(self._provider)
        now = self._flow.clock()
        if not token.expired(now):
            return token.access_token
        refreshed = self._flow.client.refresh(token, now)
        self._flow.store.save(refreshed)
        return refreshed.access_token
