"""`jukebox resolve` — match the chart corpus to playable recordings."""

from typing import Annotated

import typer

from jukebox.charts import Chart, Corpus
from jukebox.charts.entry_filter import EntryFilter
from jukebox.charts.fetch import corpus_root
from jukebox.oauth.errors import OAuthError
from jukebox.providers.musicbrainz import MusicBrainzIsrcs
from jukebox.providers.spotify import SpotifyCatalog, build_session
from jukebox.resolve import Attempt, Backfill, ResolutionStore, Resolver, resolutions_root

commands = typer.Typer(help="Match chart entries to playable recordings.")

Year = Annotated[int, typer.Option("--year", help="The chart year to resolve.")]
Charts = Annotated[list[str] | None, typer.Option("--chart", help="Charts; repeatable.")]
Limit = Annotated[int | None, typer.Option("--limit", help="Stop after this many lookups.")]
UseIsrc = Annotated[bool, typer.Option("--isrc/--no-isrc", help="Consult MusicBrainz first.")]
Narrow = Annotated[
    list[str] | None,
    typer.Option("--narrow", help="measure=value, repeatable: max_rank, min_weeks, artist, title."),
]


@commands.command("backfill")
def backfill(
    year: Year,
    chart: Charts = None,
    limit: Limit = None,
    isrc: UseIsrc = False,
    narrow: Narrow = None,
) -> None:
    """Resolve entries not yet answered for, keeping what is already known.

    Songs an earlier pass failed to find are left alone, because a lookup costs
    the same whether it answers or not; `resolve retry` is what asks again.

    The narrowing options apply before a lookup is spent, so resolving what a
    spec selects costs what that selection costs rather than what the whole
    chart would.

    ISRC lookup is off by default: measured against 1985, MusicBrainz carried an
    identifier for roughly one entry in eight, at about two seconds each.
    """
    _resolve(year, chart, isrc, Attempt(limit=limit, rows=EntryFilter.named(narrow)))


@commands.command("retry")
def retry(
    year: Year,
    chart: Charts = None,
    limit: Limit = None,
    narrow: Narrow = None,
) -> None:
    """Look again for the songs an earlier pass did not find.

    Worth doing when the catalogue or the matching has changed, and wasteful
    otherwise: a miss records one attempt rather than a verdict, but asking
    again costs exactly what asking the first time did.
    """
    _resolve(
        year,
        chart,
        False,
        Attempt(limit=limit, rows=EntryFilter.named(narrow), retry_missed=True),
    )


def _resolve(year: int, chart: list[str] | None, isrc: bool, attempt: Attempt) -> None:
    """One pass over a year's charts, reporting each as it lands."""
    corpus = Corpus(corpus_root(None))
    store = ResolutionStore(resolutions_root(None))
    try:
        resolver = Resolver(
            SpotifyCatalog(build_session()),
            MusicBrainzIsrcs() if isrc else None,
        )
    except OAuthError as refusal:
        typer.echo(str(refusal), err=True)
        raise typer.Exit(code=1) from refusal

    typer.echo(f"resolving {year}")
    for name in chart or [c.slug for c in Chart]:
        selected = Chart(name)
        if not corpus.path(selected, year).exists():
            continue
        typer.echo(Backfill(corpus, store, resolver).year(selected, year, attempt).render())
