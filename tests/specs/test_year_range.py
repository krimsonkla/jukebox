"""A span of chart years, written the way a person writes one."""

import pytest

from jukebox.specs import BadYearRange, parse_years


@pytest.mark.parametrize(
    ("text", "expected"),
    [("1985", (1985, 1985)), ("1980-1989", (1980, 1989)), (" 1980 - 1989 ", (1980, 1989))],
)
def test_a_year_or_a_span_is_read(text, expected):
    assert parse_years(text) == expected


@pytest.mark.parametrize("text", ["the eighties", "", "1980-1989-1999", "1980-", "199x"])
def test_anything_else_says_how_to_write_it(text):
    with pytest.raises(BadYearRange, match="1980-1989"):
        parse_years(text)


def test_a_backwards_span_is_refused():
    with pytest.raises(BadYearRange):
        parse_years("1989-1980")
