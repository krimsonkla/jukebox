"""Builds the Spotify adapter from settings alone."""

import datetime as dt

from jukebox.oauth.flow import Flow
from jukebox.oauth.session import Session
from jukebox.oauth.token_client import TokenClient
from jukebox.oauth.token_store import TokenStore
from jukebox.providers.spotify.auth import NAME, SpotifyAuth
from jukebox.providers.spotify.endpoints import TOKEN_URL
from jukebox.providers.spotify.errors import MissingClientId
from jukebox.providers.spotify.settings import SpotifySettings


def _clock() -> dt.datetime:
    """Now, in UTC — a naive local clock would misjudge a UTC expiry."""
    return dt.datetime.now(dt.UTC)


def build_flow(settings: SpotifySettings | None = None) -> Flow:
    """The store, token client and clock the Spotify adapter shares."""
    resolved = settings or SpotifySettings()
    if not resolved.client_id:
        raise MissingClientId()
    return Flow(
        store=TokenStore(resolved.state_dir, NAME, resolved.client_id),
        client=TokenClient(TOKEN_URL, resolved.client_id),
        clock=_clock,
    )


def build_auth(settings: SpotifySettings | None = None) -> SpotifyAuth:
    """A Spotify authorizer wired from the environment."""
    resolved = settings or SpotifySettings()
    return SpotifyAuth(resolved, build_flow(resolved))


def build_session(settings: SpotifySettings | None = None) -> Session:
    """A Spotify credential supplier wired from the environment."""
    return Session(NAME, build_flow(settings))
