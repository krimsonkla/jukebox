"""A grid becomes corpus rows — spec §AC 2, 3, 6, 11."""

import datetime as dt

import pytest

from jukebox.charts import (
    DecadeMapper,
    EntryKind,
    Grid,
    NumberOnesMapper,
    RankedMapper,
    UnexpectedColumns,
)


def test_ranked_maps_first_and_last(hot100_1985):
    entries = RankedMapper().map(Grid.of(hot100_1985))
    assert len(entries) == 100
    assert all(e.kind is EntryKind.RANKED for e in entries)
    first, last = entries[0], entries[-1]
    assert (first.rank, first.title, first.artist) == (1, "Careless Whisper", "George Michael")
    assert (last.rank, last.title, last.artist) == (100, "Sugar Walls", "Sheena Easton")


def test_ranked_keeps_an_unlinked_plain_text_title(rnb_1985):
    entries = RankedMapper().map(Grid.of(rnb_1985))
    assert entries[0].title == "Rock Me Tonight (For Old Times Sake)"
    assert entries[10].title == "(No Matter How High I Get) I'll Still be Looking Up to You"


def test_country_number_ones_carry_a_date(country_1985):
    entries = NumberOnesMapper().map(Grid.of(country_1985), year=1985)
    first = entries[0]
    assert first.kind is EntryKind.NUMBER_ONE
    assert first.title == "Does Fort Worth Ever Cross Your Mind"
    assert first.artist == "George Strait"
    assert first.reached == dt.date(1985, 1, 5)


def test_a_run_of_weeks_collapses_to_one_entry_carrying_its_length(country_1985):
    entries = NumberOnesMapper().map(Grid.of(country_1985), year=1985)
    titles = [e.title for e in entries]
    assert len(titles) == len(set(titles)) or all(e.weeks >= 1 for e in entries)
    assert sum(e.weeks for e in entries) == 52


def test_the_dance_page_yields_two_distinct_charts(dance_1985):
    columns = NumberOnesMapper().split(Grid.of(dance_1985), year=1985)
    assert set(columns) == {
        "Hot Dance/Disco Club Play",
        "Hot Dance/Disco 12-inch Singles Sales",
    }


def test_not_issued_is_absence_not_a_song(dance_1985):
    columns = NumberOnesMapper().split(Grid.of(dance_1985), year=1985)
    sales = columns["Hot Dance/Disco 12-inch Singles Sales"]
    assert "Not issued" not in [e.title for e in sales]


def test_the_1989_straddler_is_not_a_1990_entry(modernrock_1990s):
    entries = DecadeMapper().map(Grid.of(modernrock_1990s), year=1990)
    assert "Blues from a Gun" not in [e.title for e in entries]
    assert entries[0].title == "House"
    assert entries[0].artist == "The Psychedelic Furs"
    assert entries[0].reached == dt.date(1990, 1, 20)
    assert entries[0].weeks == 3


def test_a_dagger_marked_title_is_still_matched(modernrock_1990s):
    entries = DecadeMapper().map(Grid.of(modernrock_1990s), year=1990)
    assert "Cuts You Up" in [e.title for e in entries]


def test_a_mapper_rejects_a_grid_whose_columns_it_does_not_recognise(hot100_1985):
    with pytest.raises(UnexpectedColumns):
        NumberOnesMapper().map(Grid.of(hot100_1985), year=1985)


def test_a_year_banner_row_attributes_the_rows_that_follow_it(mainstreamrock_1990s):
    entries = NumberOnesMapper().map(Grid.of(mainstreamrock_1990s), year=1991)
    assert entries, "the 1991 banner should select a year's worth of rows"
    assert all(e.reached.year == 1991 for e in entries)


def test_a_banner_row_is_not_mistaken_for_a_song(mainstreamrock_1990s):
    entries = NumberOnesMapper().map(Grid.of(mainstreamrock_1990s), year=1990)
    assert "1990" not in [e.title for e in entries]
    assert entries[0].title == "Show Don't Tell"
    assert entries[0].artist == "Rush"


def test_an_explicit_weeks_column_is_preferred_to_counting_repeats(mainstreamrock_1990s):
    entries = NumberOnesMapper().map(Grid.of(mainstreamrock_1990s), year=1990)
    assert entries[1].title == "Downtown Train"
    assert entries[1].weeks == 2


def test_the_numero_sign_is_read_as_a_rank_header():
    numero = (
        '<table class="wikitable"><tr><th>№</th><th>Title</th><th>Artist(s)</th></tr>'
        '<tr><td>1</td><td>"A"</td><td>a</td></tr></table>'
    )
    assert RankedMapper().map(Grid.of(numero))[0].rank == 1


def table(body: str) -> str:
    """A minimal wikitable wrapping `body`."""
    return f'<table class="wikitable">{body}</table>'


def test_a_decade_table_may_lead_with_the_artist():
    # The rock pages lead with the song and the Latin page leads with the
    # artist; a mapper counting from the left reads one of them backwards.
    latin = table(
        "<tr><th>Artist</th><th>Single</th><th>Reached number one</th><th>Weeks</th></tr>"
        '<tr><td>Rocío Dúrcal</td><td>"La Guirnalda"</td>'
        "<td>September 6, 1986</td><td>3</td></tr>"
    )
    entry = DecadeMapper().map(Grid.of(latin), year=1986)[0]
    assert (entry.title, entry.artist, entry.weeks) == ("La Guirnalda", "Rocío Dúrcal", 3)


def test_a_decade_table_missing_a_column_it_needs_is_refused():
    for header in (
        "<tr><th>Artist</th><th>Reached number one</th></tr>",
        "<tr><th>Single</th><th>Reached number one</th></tr>",
        "<tr><th>Single</th><th>Artist</th></tr>",
    ):
        with pytest.raises(UnexpectedColumns, match="decade"):
            DecadeMapper().map(Grid.of(table(header)), year=1986)


def test_a_decade_row_with_an_empty_title_is_skipped():
    blank = table(
        "<tr><th>Song</th><th>Artist</th><th>Reached number one</th><th>Weeks</th></tr>"
        "<tr><td></td><td>a</td><td>September 6, 1986</td><td>1</td></tr>"
    )
    assert DecadeMapper().map(Grid.of(blank), year=1986) == []


def test_a_decade_table_without_a_weeks_column_counts_one_week():
    no_weeks = table(
        "<tr><th>Song</th><th>Artist</th><th>Reached number one</th></tr>"
        '<tr><td>"A"</td><td>a</td><td>September 6, 1986</td></tr>'
    )
    assert DecadeMapper().map(Grid.of(no_weeks), year=1986)[0].weeks == 1
