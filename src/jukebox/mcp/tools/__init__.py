"""One module per group of tools; each is a plain function over a Workspace."""

from jukebox.mcp.tools.auth import auth_login, auth_status
from jukebox.mcp.tools.charts import list_charts, query_charts
from jukebox.mcp.tools.corpus import fetch_charts, resolve_charts
from jukebox.mcp.tools.playlists import apply_playlist, plan_playlist
from jukebox.mcp.tools.providers import list_providers, use_provider
from jukebox.mcp.tools.songs import (
    artist_songs,
    build_index,
    crossovers,
    find_song,
    index_status,
)
from jukebox.mcp.tools.specs import get_spec, list_specs, preview_spec, put_spec

__all__ = [
    "apply_playlist",
    "artist_songs",
    "auth_login",
    "auth_status",
    "build_index",
    "crossovers",
    "fetch_charts",
    "find_song",
    "get_spec",
    "index_status",
    "list_charts",
    "list_providers",
    "list_specs",
    "plan_playlist",
    "preview_spec",
    "put_spec",
    "query_charts",
    "resolve_charts",
    "use_provider",
]
