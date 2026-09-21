"""`jukebox charts` — build the vendored chart corpus."""

import pathlib
from typing import Annotated

import typer

from jukebox.charts import Corpus, FixtureSource, MediaWikiSource, Registry
from jukebox.charts.fetch import Fetch, corpus_root

commands = typer.Typer(help="Fetch and inspect the chart corpus.")

FIXTURES = pathlib.Path(__file__).resolve().parents[3] / "tests" / "fixtures" / "pages"

Year = Annotated[int, typer.Option("--year", help="The chart year to build.")]
Source = Annotated[str, typer.Option("--source", help="wikipedia or fixture.")]
Out = Annotated[pathlib.Path | None, typer.Option("--out", help="Corpus root.")]


@commands.command("fetch")
def fetch(year: Year, source: Source = "wikipedia", out: Out = None) -> None:
    """Write every chart the registry resolves for a year, and report the gaps."""
    reader = FixtureSource(FIXTURES) if source == "fixture" else MediaWikiSource()
    report = Fetch(Registry.billboard(), reader, Corpus(corpus_root(out))).year(year)
    typer.echo(report.render())
