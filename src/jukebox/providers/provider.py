"""One music service, and how to build each of its adapters."""

import dataclasses
from collections.abc import Callable

from jukebox.ports.music_catalog import MusicCatalog
from jukebox.ports.playlist_service import PlaylistService
from jukebox.ports.provider_auth import ProviderAuth


@dataclasses.dataclass(frozen=True)
class Provider:
    """A service jukebox can talk to, built from an application identifier.

    Each builder takes the client id rather than reading configuration, so the
    identifier can arrive at any point in a session instead of having to be in
    the environment before the process starts.
    """

    name: str
    needs: str
    auth: Callable[[str], ProviderAuth]
    catalog: Callable[[str], MusicCatalog]
    playlists: Callable[[str], PlaylistService]
