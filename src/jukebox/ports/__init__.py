"""The vocabulary jukebox depends on, so no core module names a music service."""

from jukebox.ports.auth_status import AuthStatus
from jukebox.ports.credentials import Credentials
from jukebox.ports.isrc_source import IsrcSource
from jukebox.ports.music_catalog import MusicCatalog
from jukebox.ports.playlist_ref import PlaylistRef
from jukebox.ports.playlist_service import PlaylistService
from jukebox.ports.provider_auth import ProviderAuth
from jukebox.ports.track_match import TrackMatch

__all__ = [
    "AuthStatus",
    "Credentials",
    "IsrcSource",
    "MusicCatalog",
    "PlaylistRef",
    "PlaylistService",
    "ProviderAuth",
    "TrackMatch",
]
