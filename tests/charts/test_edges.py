"""The refusal paths: what each unit does with a table it cannot read.

A mapper that quietly returns nothing on an unrecognised page produces a short
playlist rather than an error, which is the failure this file exists to prevent.
"""

import pathlib

import pytest

from jukebox.charts import (
    ChartSource,
    DecadeMapper,
    Grid,
    NumberOnesMapper,
    RankedMapper,
    UnexpectedColumns,
)
from jukebox.charts.fetch import corpus_root


def table(body: str) -> str:
    """A minimal wikitable wrapping `body`."""
    return f'<table class="wikitable">{body}</table>'


RANKED_WITH_A_BLANK_ROW = table(
    "<tr><th>No.</th><th>Title</th><th>Artist(s)</th></tr>"
    '<tr><td>1</td><td>"A"</td><td>a</td></tr>'
    "<tr><td>&mdash;</td><td>tie</td><td></td></tr>"
)

DECADE_WITH_AN_UNDATED_ROW = table(
    "<tr><th>Song</th><th>Artist</th><th>Reached number one</th>"
    "<th>Weeks at<br />number one</th></tr>"
    '<tr><td>"A"</td><td>a</td><td>January 20, 1990</td><td>3</td></tr>'
    '<tr><td>"B"</td><td>b</td><td>unknown</td><td></td></tr>'
)

TWO_CHART_HEADER = table(
    "<tr><th>Issue date</th><th colspan=2>Club Play</th><th colspan=2>Sales</th></tr>"
    "<tr><th>Title</th><th>Artist(s)</th><th>Title</th><th>Artist(s)</th></tr>"
    '<tr><td>January 5</td><td>"A"</td><td>a</td><td>"B"</td><td>b</td></tr>'
)


def test_a_ranked_row_without_a_rank_is_skipped():
    entries = RankedMapper().map(Grid.of(RANKED_WITH_A_BLANK_ROW))
    assert [e.title for e in entries] == ["A"]


def test_ranked_refuses_a_table_that_is_not_ranked(country_1985):
    with pytest.raises(UnexpectedColumns, match="ranked"):
        RankedMapper().map(Grid.of(country_1985))


def test_decade_refuses_a_table_that_is_not_a_decade(hot100_1985):
    with pytest.raises(UnexpectedColumns, match="decade"):
        DecadeMapper().map(Grid.of(hot100_1985), year=1985)


def test_a_decade_row_with_an_unreadable_date_is_skipped():
    entries = DecadeMapper().map(Grid.of(DECADE_WITH_AN_UNDATED_ROW), year=1990)
    assert [e.title for e in entries] == ["A"]


def test_mapping_a_multi_chart_page_without_naming_a_chart_is_refused():
    with pytest.raises(UnexpectedColumns, match="single-chart"):
        NumberOnesMapper().map(Grid.of(TWO_CHART_HEADER), year=1985)


def test_naming_a_chart_the_page_does_not_carry_is_refused():
    with pytest.raises(UnexpectedColumns, match="chart matching 'Country'"):
        NumberOnesMapper().map(Grid.of(TWO_CHART_HEADER), year=1985, column="Country")


def test_the_port_itself_implements_nothing():
    with pytest.raises(NotImplementedError):
        ChartSource.fetch(object(), "A Page")


def test_the_corpus_defaults_to_the_users_cache_not_the_working_directory(home):
    # Resolving against the cwd meant running the command from elsewhere made a
    # second, empty corpus, and put the user's files inside the checkout.
    assert corpus_root() == home.charts
    assert corpus_root().is_absolute()
    assert corpus_root(pathlib.Path("/tmp/x")) == pathlib.Path("/tmp/x")


def test_an_error_carries_advice():
    error = UnexpectedColumns("ranked", ["a"])
    assert error.advice
    assert error.advice in str(error)
