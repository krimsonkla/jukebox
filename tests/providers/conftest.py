"""A Spotify adapter wired entirely to fakes."""

import datetime as dt

import pytest

from jukebox.oauth import Callback, Flow, TokenClient, TokenStore
from jukebox.providers.spotify import SpotifyAuth, SpotifySettings

NOW = dt.datetime(2026, 9, 7, 12, 0, tzinfo=dt.UTC)


class FakeLoopback:
    """Produces a callback instead of serving a request.

    Takes a factory rather than a value, because the adapter mints the state
    after construction and a realistic callback has to echo it back.
    """

    def __init__(self, produce) -> None:
        self._produce = produce

    def wait(self) -> Callback:
        """The callback the factory produces."""
        return self._produce()


@pytest.fixture(name="settings")
def _settings(tmp_path) -> SpotifySettings:
    return SpotifySettings(client_id="cid", state_dir=tmp_path, redirect_port=8888)


@pytest.fixture(name="opened")
def _opened() -> list[str]:
    return []


@pytest.fixture(name="build")
def _build(settings, opened):
    def make(produce) -> SpotifyAuth:
        if isinstance(produce, Callback):
            produce = _always(produce)
        flow = Flow(
            store=TokenStore(settings.state_dir, "spotify"),
            client=TokenClient("https://accounts.spotify.com/api/token", "cid"),
            clock=lambda: NOW,
        )
        return SpotifyAuth(settings, flow, open_url=opened.append, loopback=FakeLoopback(produce))

    return make


def _always(callback: Callback):
    def produce() -> Callback:
        return callback

    return produce
