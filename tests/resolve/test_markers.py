"""Markers match whole words, because the substring test rejects correct matches."""

import pytest

from jukebox.resolve import penalty


@pytest.mark.parametrize(
    "title",
    [
        "Separate Lives - 2016 Remaster",  # contains "Live"
        "Discover",  # contains "cover"
        "Demolition Man",  # contains "demo"
        "Deliverance",  # contains "live"
    ],
)
def test_an_ordinary_word_containing_a_marker_is_not_penalised(title):
    assert penalty(title, "") == 0


@pytest.mark.parametrize(
    ("title", "expected"),
    [
        ("Careless Whisper - Live", 0.5),
        ("Live at Wembley", 0.5),
        ("Karaoke Version", 1.0),
        ("Take On Me - Remix", 0.3),
        ("Take On Me", 0.0),
    ],
)
def test_a_real_variant_is_penalised(title, expected):
    assert penalty(title, "") == pytest.approx(expected)


def test_the_album_is_searched_as_well_as_the_title():
    assert penalty("Careless Whisper", "Ultimate Karaoke Hits") == pytest.approx(1.0)


def test_penalties_accumulate():
    assert penalty("Careless Whisper - Live", "Tribute Collection") == pytest.approx(1.5)
