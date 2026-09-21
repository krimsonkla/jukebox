"""`jukebox serve` — run the MCP server an agent drives."""

import typer

from jukebox.charts import MediaWikiSource
from jukebox.mcp import Backends, Workspace, build_server
from jukebox.oauth.errors import OAuthError
from jukebox.providers.registry import DEFAULT, build_auth
from jukebox.providers.spotify import SpotifyCatalog, SpotifyPlaylists, build_session

commands = typer.Typer(help="Run the MCP server.")


@commands.command("mcp")
def serve() -> None:
    """Serve the corpus, the specs and the account over stdio.

    Starting unauthorized is expected: reading and fetching the corpus need no
    Spotify, and the account can be authorized from the conversation.
    """
    build_server(Workspace.here(), _backends()).run()


def _backends() -> Backends:
    """Whatever this machine can reach.

    The account adapters read the token store on every call, so authorizing
    during a session reaches them without a restart.
    """
    charts = MediaWikiSource()
    try:
        session = build_session()
        return Backends(
            charts=charts,
            auth=build_auth(DEFAULT),
            catalog=SpotifyCatalog(session),
            playlists=SpotifyPlaylists(session),
        )
    except OAuthError:
        return Backends(charts=charts)
