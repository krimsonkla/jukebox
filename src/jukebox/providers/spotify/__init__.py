"""The Spotify adapter: one implementation of the provider ports."""

from jukebox.providers.spotify.auth import NAME, SpotifyAuth
from jukebox.providers.spotify.catalog import SpotifyCatalog
from jukebox.providers.spotify.playlists import SpotifyPlaylists
from jukebox.providers.spotify.errors import MissingClientId
from jukebox.providers.spotify.factory import build_auth, build_flow, build_session
from jukebox.providers.spotify.settings import SpotifySettings

__all__ = [
    "NAME",
    "MissingClientId",
    "SpotifyAuth",
    "SpotifyCatalog",
    "SpotifyPlaylists",
    "SpotifySettings",
    "build_auth",
    "build_flow",
    "build_session",
]
