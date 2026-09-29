"""Reading an artist's own article — every table that carries a position."""

from jukebox.charts import Chart, EntryKind, Grid
from jukebox.charts.mappers.discography import DiscographyMapper

ACT = "An Act"


def read(html: str):
    """Every placing a page publishes."""
    return DiscographyMapper().map(Grid.every(html), ACT)


def singles(*rows: str, heads: str = "<th>US Main Rock</th>") -> str:
    """A singles table with a spanning header, as a discography writes one."""
    body = "".join(rows)
    return (
        '<table class="wikitable">'
        '<tr><th rowspan="2">Title</th><th rowspan="2">Year</th>'
        '<th colspan="1">Peak chart positions</th><th rowspan="2">Album</th></tr>'
        f"<tr>{heads}</tr>{body}</table>"
    )


def test_a_placing_becomes_a_peak_row():
    found = read(singles('<tr><td>"A Song"</td><td>1993</td><td>7</td><td>An Album</td></tr>'))
    assert len(found) == 1
    placed = found[0]
    assert placed.chart is Chart.MAINSTREAM_ROCK
    assert placed.year == 1993
    assert placed.entry.kind is EntryKind.PEAK
    assert (placed.entry.rank, placed.entry.title, placed.entry.artist) == (7, "A Song", ACT)


def test_a_record_that_did_not_chart_is_not_a_row():
    for blank in ("\u2014", "\u2013", "-", "\u00d7", "x", "N/A", ""):
        assert read(singles(f'<tr><td>"A"</td><td>1993</td><td>{blank}</td><td>X</td></tr>')) == []


def test_a_cell_that_is_not_a_position_is_not_a_row():
    assert read(singles('<tr><td>"A"</td><td>1993</td><td>later</td><td>X</td></tr>')) == []


def test_a_footnoted_position_is_still_a_position():
    found = read(singles('<tr><td>"A"</td><td>1993</td><td>12 [a]</td><td>X</td></tr>'))
    assert found[0].entry.rank == 12


def test_a_row_without_a_usable_year_is_skipped():
    assert read(singles('<tr><td>"A"</td><td>unreleased</td><td>7</td><td>X</td></tr>')) == []


def test_a_row_naming_no_song_is_skipped():
    assert read(singles("<tr><td></td><td>1993</td><td>7</td><td>X</td></tr>")) == []


def test_a_row_of_the_wrong_width_is_skipped():
    assert read(singles('<tr><td>"A"</td><td>1993</td><td>7</td></tr>')) == []


def test_a_repeated_header_row_is_not_read_as_a_song():
    assert (
        read(singles("<tr><td>Title</td><td>Year</td><td>US Main Rock</td><td>Album</td></tr>"))
        == []
    )


def test_a_double_a_side_keeps_both_songs():
    found = read(singles('<tr><td>"A" / "B"</td><td>1993</td><td>7</td><td>X</td></tr>'))
    assert (found[0].entry.title, found[0].entry.also) == ("A", ("B",))


def test_the_year_may_come_before_the_song():
    page = (
        '<table class="wikitable">'
        '<tr><th rowspan="2">Year</th><th rowspan="2">Title</th>'
        '<th colspan="1">Peak chart positions</th><th rowspan="2">Album</th></tr>'
        "<tr><th>US Alt.</th></tr>"
        '<tr><td>1994</td><td>"B Side"</td><td>3</td><td>X</td></tr></table>'
    )
    found = read(page)
    assert (found[0].chart, found[0].entry.title, found[0].entry.rank) == (
        Chart.MODERN_ROCK,
        "B Side",
        3,
    )


def test_a_table_naming_no_chart_this_project_reads_yields_nothing():
    assert (
        read(
            singles(
                '<tr><td>"A"</td><td>1993</td><td>7</td><td>X</td></tr>',
                heads="<th>US Act. Rock</th>",
            )
        )
        == []
    )


def test_a_table_that_is_not_a_discography_table_is_left_alone():
    other = (
        '<table class="wikitable"><tr><th>Year</th><th>Director</th></tr>'
        "<tr><td>1993</td><td>Someone</td></tr></table>"
    )
    assert read(other) == []


def test_only_the_first_column_naming_a_chart_is_read():
    # An article can print the same chart twice, weekly and year-end; the
    # first is the peak, and counting both would double every song.
    page = (
        '<table class="wikitable">'
        '<tr><th rowspan="2">Title</th><th rowspan="2">Year</th>'
        '<th colspan="2">Peak chart positions</th><th rowspan="2">Album</th></tr>'
        "<tr><th>US Main Rock</th><th>US Main.</th></tr>"
        '<tr><td>"A"</td><td>1993</td><td>7</td><td>9</td><td>X</td></tr></table>'
    )
    found = read(page)
    assert [placed.entry.rank for placed in found] == [7]


def test_every_table_on_the_page_is_read():
    page = singles('<tr><td>"A"</td><td>1993</td><td>7</td><td>X</td></tr>') + singles(
        '<tr><td>"B"</td><td>1994</td><td>2</td><td>Y</td></tr>'
    )
    assert [placed.entry.title for placed in read(page)] == ["A", "B"]
