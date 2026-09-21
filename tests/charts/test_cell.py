"""Cell text is plain text — spec §Acceptance criteria 7."""

import lxml.html
import pytest

from jukebox.charts import clean_cell, clean_title, titles


def cell(markup: str):
    """The markup as a table cell element."""
    return lxml.html.fragment_fromstring(f"<td>{markup}</td>")


def test_br_becomes_a_space():
    assert clean_cell(cell("Weeks at<br />number one")) == "Weeks at number one"


def test_reference_superscript_is_removed():
    markup = 'George Strait<sup class="reference"><a href="#c">[13]</a></sup>'
    assert clean_cell(cell(markup)) == "George Strait"


def test_whitespace_is_collapsed():
    assert clean_cell(cell("  Dan   \n Hartman ")) == "Dan Hartman"


def test_two_artist_cell_is_preserved_whole():
    assert clean_cell(cell("Philip Bailey and <a href='#'>Phil Collins</a>")) == (
        "Philip Bailey and Phil Collins"
    )


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ('"Careless Whisper"', "Careless Whisper"),
        ('"Cuts You Up" †', "Cuts You Up"),
        ('"Rain Forest" / "Sound Chaser"', "Rain Forest"),
        ('"Part-Time Lover" (Remix)', "Part-Time Lover"),
        ("Sugar Walls", "Sugar Walls"),
    ],
)
def test_title_quotes_and_markers_are_stripped(raw, expected):
    assert clean_title(raw) == expected


def test_a_double_a_side_names_both_songs():
    # One chart position, two songs; taking the cell whole leaves a quote mid-title.
    assert titles('"Rain Forest" / "Sound Chaser"') == ("Rain Forest", "Sound Chaser")
    assert titles('"New Attitude"/ "Axel F"') == ("New Attitude", "Axel F")


def test_a_qualifier_after_the_closing_quote_does_not_defeat_stripping():
    assert titles('"Part-Time Lover" (Remix)') == ("Part-Time Lover",)


def test_an_unquoted_title_survives_whole():
    assert titles("Sugar Walls") == ("Sugar Walls",)


def test_brackets_inside_a_quoted_title_are_kept():
    raw = '"(No Matter How High I Get) I\'ll Still be Looking Up to You"'
    assert titles(raw) == ("(No Matter How High I Get) I'll Still be Looking Up to You",)


def test_an_empty_cell_names_nothing():
    assert not titles("  ")
    assert clean_title("  ") == ""
