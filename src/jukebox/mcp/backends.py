"""What the tools can reach, and what this session has chosen.

Every field is optional and the choice can arrive mid-conversation. A surface
that demanded a client id in the environment before the process started would
force a person to configure the tool before launching the client that exists to
configure it.
"""

import dataclasses

from jukebox.charts.chart_source import ChartSource
from jukebox.mcp.errors import NoProviderChosen
from jukebox.mcp.session import SessionConfig
from jukebox.ports.music_catalog import MusicCatalog
from jukebox.ports.playlist_service import PlaylistService
from jukebox.ports.provider_auth import ProviderAuth
from jukebox.providers import registry


@dataclasses.dataclass(frozen=True)
class Backends:
    """What this server can reach.

    The three account adapters are resolved from `session` when it has been
    told what to use. Passing one explicitly overrides that, which is what a
    test does and what a command line with an environment already set can do.
    """

    charts: ChartSource | None = None
    session: SessionConfig = dataclasses.field(default_factory=SessionConfig)
    auth: ProviderAuth | None = None
    catalog: MusicCatalog | None = None
    playlists: PlaylistService | None = None

    def authorizer(self) -> ProviderAuth:
        """The authorizer for the chosen provider."""
        return self.auth or self._built("auth")

    def searchable(self) -> MusicCatalog:
        """The catalogue for the chosen provider."""
        return self.catalog or self._built("catalog")

    def account(self) -> PlaylistService:
        """The playlist service for the chosen provider."""
        return self.playlists or self._built("playlists")

    def _built(self, adapter: str):
        if not self.session.configured:
            raise NoProviderChosen(sorted(registry.PROVIDERS))
        provider = registry.named(self.session.provider)
        return getattr(provider, adapter)(self.session.client_id)
