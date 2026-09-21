"""`jukebox spec` — describe a playlist and see what it selects."""

from typing import Annotated

import typer

from jukebox.charts import Chart, Corpus
from jukebox.charts.fetch import corpus_root
from jukebox.paths import Paths
from jukebox.specs import (
    Evaluate,
    Ordering,
    Selection,
    Spec,
    SpecsError,
    SpecStore,
    parse_years,
)

commands = typer.Typer(help="Describe playlists and preview what they select.")


Name = Annotated[str, typer.Argument(help="The spec's name.")]
ChartsOpt = Annotated[list[str], typer.Option("--chart", help="Chart slug; repeatable.")]
Years = Annotated[str, typer.Option("--years", help="A year, 1985, or a span, 1980-1989.")]
MaxRank = Annotated[int | None, typer.Option("--max-rank", help="Ranked entries only.")]
MinWeeks = Annotated[int | None, typer.Option("--min-weeks", help="Number ones only.")]
Size = Annotated[int | None, typer.Option("--size", help="How many tracks.")]
PerArtist = Annotated[int | None, typer.Option("--max-per-artist", help="Cap per artist.")]
Order = Annotated[Ordering | None, typer.Option("--order", help="How to sequence.")]
Seed = Annotated[int | None, typer.Option("--seed", help="Fixes a shuffle.")]


@commands.command("add")
def add(
    name: Name, chart: ChartsOpt, years: Years, max_rank: MaxRank = None, min_weeks: MinWeeks = None
) -> None:
    """Write a spec that selects from the charts, then preview it."""
    spec = _guard(
        lambda: Spec(
            name=name,
            select=Selection(
                charts=[Chart(slug) for slug in chart],
                years=parse_years(years),
                max_rank=max_rank,
                min_weeks=min_weeks,
            ),
        )
    )
    typer.echo(f"wrote {SpecStore(Paths.resolve().specs).save(spec)}")
    _preview(spec)


@commands.command("shape")
def shape(
    name: Name,
    size: Size = None,
    max_per_artist: PerArtist = None,
    order: Order = None,
    seed: Seed = None,
) -> None:
    """Change how an existing spec is cut down, then preview it."""
    store = SpecStore(Paths.resolve().specs)
    spec = _guard(lambda: store.load(name))
    asked = {"size": size, "max_per_artist": max_per_artist, "order": order, "seed": seed}
    changed = spec.model_copy(update={"shape": spec.shape.model_copy(update=_given(asked))})
    typer.echo(f"wrote {store.save(changed)}")
    _preview(changed)


@commands.command("list")
def show_all() -> None:
    """Every stored spec."""
    names = SpecStore(Paths.resolve().specs).names()
    typer.echo("\n".join(f"  {name}" for name in names) if names else "no specs yet")


@commands.command("preview")
def preview(name: Name) -> None:
    """What a stored spec selects, without touching any music service."""
    _preview(_guard(lambda: SpecStore(Paths.resolve().specs).load(name)))


def _given(asked: dict) -> dict:
    return {field: value for field, value in asked.items() if value is not None}


def _guard(action):
    try:
        return action()
    except SpecsError as refusal:
        typer.echo(str(refusal), err=True)
        raise typer.Exit(code=1) from refusal


def _preview(spec: Spec) -> None:
    typer.echo(_guard(lambda: Evaluate(Corpus(corpus_root(None))).tracklist(spec).render()))
