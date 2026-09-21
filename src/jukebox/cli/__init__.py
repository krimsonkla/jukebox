"""The jukebox command line.

The MCP surface is what an agent drives; this is what a person runs to build the
corpus, authorize a music service, and apply a spec.

Sub-commands are imported as modules rather than as their Typer objects: binding
`jukebox.cli.auth` to a Typer would shadow the module of the same name, and a
test or a caller reaching for the module would silently get the app instead.
"""

import typer

from jukebox.cli import auth, charts, playlist, resolve, serve, songs, spec

app = typer.Typer(help="Build Spotify playlists from published record charts.")
app.add_typer(auth.commands, name="auth")
app.add_typer(charts.commands, name="charts")
app.add_typer(resolve.commands, name="resolve")
app.add_typer(songs.commands, name="songs")
app.add_typer(spec.commands, name="spec")
app.add_typer(playlist.commands, name="playlist")
app.add_typer(serve.commands, name="serve")


def main() -> None:
    """Console-script entry point."""
    app()


__all__ = ["app", "main"]
