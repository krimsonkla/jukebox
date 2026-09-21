"""Rowspan and colspan expand into a dense grid — spec §AC 10, 11."""

import pytest

from jukebox.charts import Grid, NoTableFound


def test_ranked_grid_is_dense(hot100_1985):
    grid = Grid.of(hot100_1985)
    assert len(grid.rows) == 101
    assert grid.widths() == {3}
    assert grid.rows[0] == ["No.", "Title", "Artist(s)"]
    assert grid.rows[1] == ["1", '"Careless Whisper"', "George Michael"]
    assert grid.rows[100] == ["100", '"Sugar Walls"', "Sheena Easton"]


def test_references_do_not_reach_the_grid(country_1985):
    grid = Grid.of(country_1985)
    assert grid.rows[1] == [
        "January 5",
        '"Does Fort Worth Ever Cross Your Mind"',
        "George Strait",
        "",
    ]


def test_rowspan_carries_a_title_across_the_weeks_it_held(dance_1985):
    grid = Grid.of(dance_1985)
    assert grid.rows[3][1] == grid.rows[4][1] == '"We Are the Young"'
    assert grid.rows[3][2] == grid.rows[4][2] == "Dan Hartman"


def test_colspan_duplicates_a_two_level_header(dance_1985):
    grid = Grid.of(dance_1985)
    assert grid.rows[0][1:3] == ["Hot Dance/Disco Club Play"] * 2
    assert grid.rows[1][1:3] == ["Title", "Artist(s)"]


def test_br_in_a_header_keeps_its_space(modernrock_1990s):
    assert Grid.of(modernrock_1990s).rows[0][3] == "Weeks at number one"


def test_a_page_with_no_wikitable_is_rejected():
    with pytest.raises(NoTableFound):
        Grid.of("<p>no table here</p>")


def table(body: str) -> str:
    """A minimal wikitable wrapping `body`."""
    return f'<table class="wikitable">{body}</table>'


def test_a_nonsense_span_does_not_raise():
    # `2px` on a publicly editable page gave a traceback rather than a refusal.
    grid = Grid.of(table('<tr><td colspan="2px">a</td><td>b</td></tr>'))
    assert grid.rows[0] == ["a", "b"]


def test_an_enormous_span_is_clamped_rather_than_allocated():
    grid = Grid.of(table('<tr><td colspan="100000">a</td></tr>'))
    assert len(grid.rows[0]) <= 100


def test_a_negative_span_counts_as_one():
    assert Grid.of(table('<tr><td colspan="-5">a</td></tr>')).rows[0] == ["a"]
