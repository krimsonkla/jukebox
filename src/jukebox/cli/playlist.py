"""`jukebox playlist` — see what applying a spec would do, then do it."""

from typing import Annotated

import typer

from jukebox.charts import Corpus
from jukebox.charts.fetch import corpus_root
from jukebox.paths import Paths
from jukebox.errors import JukeboxError
from jukebox.providers.spotify import SpotifyPlaylists, build_session
from jukebox.reconcile import Apply, Desired, Ledger, ledger_root
from jukebox.resolve import ResolutionStore, resolutions_root
from jukebox.specs import Evaluate, SpecStore

commands = typer.Typer(help="Apply a spec to a playlist on your account.")


Name = Annotated[str, typer.Argument(help="The spec's name.")]
Replace = Annotated[
    bool,
    typer.Option("--replace-manual", help="Drop tracks you added by hand."),
]
Yes = Annotated[bool, typer.Option("--yes", help="Apply without confirming.")]


@commands.command("plan")
def plan(name: Name, replace_manual: Replace = False) -> None:
    """What applying would change. Writes nothing."""
    _guard(lambda: typer.echo(_planned(name, replace_manual)[0].render()))


@commands.command("apply")
def apply(name: Name, replace_manual: Replace = False, yes: Yes = False) -> None:
    """Bring the playlist into line with the spec."""

    def run() -> None:
        made, spec, applier = _planned(name, replace_manual)
        typer.echo(made.render())
        if not made.changes:
            return
        if not yes and not typer.confirm("apply this to your account?"):
            typer.echo("nothing written")
            return
        playlist_id = applier.write(spec, made)
        typer.echo(f"applied — https://open.spotify.com/playlist/{playlist_id}")

    _guard(run)


def _planned(name: str, replace_manual: bool):
    spec = SpecStore(Paths.resolve().specs).load(name)
    tracklist = Evaluate(Corpus(corpus_root(None))).tracklist(spec)
    applier = Apply(
        SpotifyPlaylists(build_session()),
        Ledger(ledger_root()),
        Desired(ResolutionStore(resolutions_root())),
    )
    return applier.plan(spec, tracklist, keep_manual=not replace_manual), spec, applier


def _guard(action) -> None:
    try:
        action()
    except JukeboxError as refusal:
        typer.echo(str(refusal), err=True)
        raise typer.Exit(code=1) from refusal
