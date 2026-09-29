"""`jukebox charts` — build the vendored chart corpus."""

import pathlib
from typing import Annotated

import typer

from jukebox.charts import Corpus, FixtureSource, MediaWikiSource, Registry
from jukebox.charts.discography import Discography
from jukebox.charts.fetch import Fetch, corpus_root
from jukebox.specs.year_range import parse_years

commands = typer.Typer(help="Fetch and inspect the chart corpus.")

FIXTURES = pathlib.Path(__file__).resolve().parents[3] / "tests" / "fixtures" / "pages"

Year = Annotated[int, typer.Option("--year", help="The chart year to build.")]
Source = Annotated[str, typer.Option("--source", help="wikipedia or fixture.")]
Out = Annotated[pathlib.Path | None, typer.Option("--out", help="Corpus root.")]
Artists = Annotated[list[str], typer.Option("--artist", help="Artist name; repeatable.")]
Years = Annotated[str, typer.Option("--years", help="A year, 1985, or a span, 1980-1989.")]


@commands.command("fetch")
def fetch(year: Year, source: Source = "wikipedia", out: Out = None) -> None:
    """Write every chart the registry resolves for a year, and report the gaps."""
    reader = FixtureSource(FIXTURES) if source == "fixture" else MediaWikiSource()
    report = Fetch(Registry.published(), reader, Corpus(corpus_root(out))).year(year)
    typer.echo(report.render())


@commands.command("discography")
def discography(
    artist: Artists, years: Years, source: Source = "wikipedia", out: Out = None
) -> None:
    """Read an artist's own article for the placings a chart of number ones omits.

    A chart page records who reached the top. A discography records where
    everything else stopped, which is most of what an act released.
    """
    reader = FixtureSource(FIXTURES) if source == "fixture" else MediaWikiSource()
    reading = Discography(reader, Corpus(corpus_root(out)))
    span = parse_years(years)
    for name in artist:
        report = reading.artist(name, span)
        if report.missing:
            typer.echo(f"{report.artist}: no article at {report.title}")
            continue
        added = "  ".join(f"{chart.slug} {count}" for chart, count in sorted(report.added.items()))
        typer.echo(f"{report.artist}: {report.found} placings, {report.total} new  {added}")
