"""An artist's own article carries what a chart of number ones leaves out."""

import datetime as dt
import pathlib

import pytest

from jukebox.charts import Chart, ChartEntry, ChartFile, Corpus, EntryKind, FixtureSource
from jukebox.charts.attribution import Attribution
from jukebox.charts.chart_columns import charted_by
from jukebox.charts.discography import Discography, page_for

ACT = "A Fictional Act"
PAGES = pathlib.Path(__file__).resolve().parents[2] / "tests" / "fixtures" / "pages"
TODAY = dt.date(2026, 9, 28)


@pytest.fixture(name="reading")
def _reading(tmp_path):
    return Discography(FixtureSource(PAGES), Corpus(tmp_path), today=TODAY)


def test_an_article_is_found_by_the_artist_it_belongs_to():
    assert page_for("Alice in Chains") == "Alice in Chains discography"


def test_every_table_that_carries_positions_is_read(reading):
    report = reading.artist(ACT, (1980, 1999))
    # Three from the singles table's two rock columns, and one more from the
    # promotional table, which is a table of its own.
    assert report.found == 4
    assert report.added == {Chart.MAINSTREAM_ROCK: 3, Chart.MODERN_ROCK: 1}


def test_a_promotional_single_is_read_although_the_year_comes_first(reading, tmp_path):
    reading.artist(ACT, (1980, 1999))
    titles = [e.title for e in Corpus(tmp_path).read(Chart.MAINSTREAM_ROCK, 1985).entries]
    assert "The Promo" in titles


def test_a_placing_is_stored_as_the_peak_it_is(reading, tmp_path):
    reading.artist(ACT, (1980, 1999))
    loud = next(
        e
        for e in Corpus(tmp_path).read(Chart.MAINSTREAM_ROCK, 1985).entries
        if e.title == "The Loud One"
    )
    assert loud.kind is EntryKind.PEAK
    assert loud.rank == 7
    assert loud.artist == ACT


def test_a_record_that_charted_nowhere_is_not_a_row(reading, tmp_path):
    reading.artist(ACT, (1980, 1999))
    held = Corpus(tmp_path).read(Chart.MAINSTREAM_ROCK, 1985)
    assert "Not A Hit" not in [entry.title for entry in held.entries]


def test_a_year_outside_the_span_is_left_alone(reading, tmp_path):
    reading.artist(ACT, (1980, 1999))
    assert not Corpus(tmp_path).path(Chart.MAINSTREAM_ROCK, 2011).exists()


def test_the_article_is_recorded_as_the_files_source(reading, tmp_path):
    reading.artist(ACT, (1980, 1999))
    sources = Corpus(tmp_path).read(Chart.MAINSTREAM_ROCK, 1985).sources
    assert [(s.title, s.retrieved) for s in sources] == [(f"{ACT} discography", TODAY)]


def test_a_song_the_corpus_already_holds_keeps_the_row_it_has(tmp_path):
    corpus = Corpus(tmp_path)
    corpus.write(
        ChartFile(
            chart=Chart.MAINSTREAM_ROCK,
            year=1985,
            sources=[Attribution(title="the chart's own article", retrieved=TODAY)],
            entries=[
                ChartEntry(
                    kind=EntryKind.NUMBER_ONE,
                    title="The Loud One",
                    artist=ACT,
                    reached=dt.date(1985, 3, 2),
                    weeks=4,
                )
            ],
        )
    )
    Discography(FixtureSource(PAGES), corpus, today=TODAY).artist(ACT, (1980, 1999))
    held = corpus.read(Chart.MAINSTREAM_ROCK, 1985)
    loud = [entry for entry in held.entries if entry.title == "The Loud One"]
    assert len(loud) == 1
    assert loud[0].kind is EntryKind.NUMBER_ONE
    assert loud[0].weeks == 4


def test_both_articles_are_credited_when_both_contributed(tmp_path):
    corpus = Corpus(tmp_path)
    corpus.write(
        ChartFile(
            chart=Chart.MAINSTREAM_ROCK,
            year=1985,
            sources=[Attribution(title="the chart's own article", retrieved=TODAY)],
            entries=[],
        )
    )
    Discography(FixtureSource(PAGES), corpus, today=TODAY).artist(ACT, (1980, 1999))
    assert [s.title for s in corpus.read(Chart.MAINSTREAM_ROCK, 1985).sources] == [
        f"{ACT} discography",
        "the chart's own article",
    ]


def test_reading_the_same_article_twice_adds_nothing_the_second_time(reading):
    reading.artist(ACT, (1980, 1999))
    again = reading.artist(ACT, (1980, 1999))
    assert again.found == 4
    assert again.added == {}
    assert again.total == 0


def test_an_act_with_no_article_is_a_gap_rather_than_a_failure(reading):
    report = reading.artist("Nobody At All", (1980, 1999))
    assert report.missing
    assert (report.found, report.total) == (0, 0)


def test_a_peak_is_never_filed_among_year_end_ranks(reading, tmp_path):
    # The fixture's singles table carries a Hot 100 column. A year-end list
    # records how big a song was across a year, not how high it got, so a peak
    # filed there would let a spec asking for the top forty return a record
    # that never came near it.
    reading.artist(ACT, (1980, 1999))
    assert not Corpus(tmp_path).path(Chart.HOT_100, 1985).exists()


def test_a_column_naming_a_chart_this_project_does_not_read_is_passed_over():
    # Active Rock is a separate airplay panel, not the mainstream rock chart.
    assert charted_by("US Act. Rock") is None
    assert charted_by("US") is None
    assert charted_by("US Main Rock") is Chart.MAINSTREAM_ROCK
