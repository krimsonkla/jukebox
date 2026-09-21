"""`jukebox songs` — ask the corpus about songs and artists rather than lists.

Each command calls the same function the MCP tool of that name calls, so the
two surfaces cannot answer differently. An assistant that can only tell someone
to go and run a command ends the conversation the MCP surface exists to have.
"""

import pathlib
from typing import Annotated

import typer

from jukebox.mcp import tools
from jukebox.mcp.workspace import Workspace
from jukebox.specs.year_range import parse_years

commands = typer.Typer(help="Ask the corpus about songs and artists.")

Years = Annotated[str, typer.Option("--years", help="A span, like 1980-1999.")]
Root = Annotated[pathlib.Path | None, typer.Option("--root", help="Workspace root.")]
Title = Annotated[str, typer.Option("--title", help="The song's title.")]
Artist = Annotated[str, typer.Option("--artist", help="The credited artist.")]
Name = Annotated[str, typer.Option("--name", help="The artist to look up.")]
Charts = Annotated[list[str], typer.Option("--chart", help="Charts; repeatable.")]
Limit = Annotated[int, typer.Option("--limit", help="Most songs to print.")]


@commands.command("build")
def build(years: Years = "1980-1999", root: Root = None) -> None:
    """Read the corpus into songs and artists, replacing any earlier index."""
    answer = tools.build_index(Workspace.here(root), parse_years(years))
    built, covers = answer["built"], answer["covers"]
    typer.echo(
        f"{built['songs']} songs by {built['artists']} artists, "
        f"from {built['appearances']} chart rows, covering {covers[0]}-{covers[1]}"
    )


@commands.command("status")
def status(root: Root = None) -> None:
    """Whether the index has been built, and what it holds."""
    held = tools.index_status(Workspace.here(root))
    if not held["built"]:
        typer.echo("no index yet — run `jukebox songs build`")
        raise typer.Exit(code=1)
    covers = held["covers"]
    span = f"{covers[0]}-{covers[1]}" if covers else "an unrecorded span"
    typer.echo(
        f"{held['songs']} songs, {held['artists']} artists, "
        f"{held['appearances']} rows, covering {span}"
    )


@commands.command("show")
def show(title: Title, artist: Artist, root: Root = None) -> None:
    """One song's whole chart history."""
    found = tools.find_song(Workspace.here(root), title, artist)
    if not found["found"]:
        typer.echo(f"no song matching {title} — {artist}")
        raise typer.Exit(code=1)
    typer.echo(_song(found))


@commands.command("artist")
def by_artist(name: Name, limit: Limit = 100, root: Root = None) -> None:
    """Every song the corpus credits to an artist."""
    found = tools.artist_songs(Workspace.here(root), name, limit)
    if not found["found"]:
        typer.echo(f"no artist matching {name}")
        raise typer.Exit(code=1)
    typer.echo(f"{found['artist']} — {found['total']} songs")
    for song in found["songs"]:
        typer.echo(f"  {_song(song)}")


@commands.command("crossover")
def crossover(chart: Charts, limit: Limit = 100, root: Root = None) -> None:
    """Songs that appeared on every one of these charts."""
    found = tools.crossovers(Workspace.here(root), chart, limit)
    typer.echo(f"{found['total']} songs on all of {', '.join(found['charts'])}")
    for song in found["songs"]:
        typer.echo(f"  {_song(song)}")


def _song(song: dict) -> str:
    years = ", ".join(str(year) for year in song["years"])
    charts = ", ".join(song["charts"])
    measure = f"peak {song['best_rank']}" if song["best_rank"] else ""
    weeks = f"{song['weeks_at_number_one']}w at #1" if song["weeks_at_number_one"] else ""
    trailing = "  ".join(part for part in (measure, weeks) if part)
    return f"{song['title']} — {song['artist']} [{charts}] {years}  {trailing}".rstrip()
