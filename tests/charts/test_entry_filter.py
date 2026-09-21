"""One rule for narrowing a chart row, stated once."""

import datetime as dt

import pytest

from jukebox.charts import ChartEntry, EntryKind
from jukebox.charts.entry_filter import EntryFilter
from jukebox.charts.errors import UnknownMeasure


def ranked(rank: int, title: str = "A Song", artist: str = "An Act") -> ChartEntry:
    """A year-end row, which carries a rank and no duration."""
    return ChartEntry(kind=EntryKind.RANKED, title=title, artist=artist, rank=rank)


def number_one(weeks: int, title: str = "A Song", artist: str = "An Act") -> ChartEntry:
    """A number-one row, which carries a duration and no rank."""
    return ChartEntry(
        kind=EntryKind.NUMBER_ONE,
        title=title,
        artist=artist,
        reached=dt.date(1985, 1, 5),
        weeks=weeks,
    )


def test_an_empty_filter_keeps_everything():
    wanted = EntryFilter()
    assert wanted.matches(ranked(100))
    assert wanted.matches(number_one(1))
    assert not wanted.narrows()


def test_a_rank_ceiling_keeps_a_row_at_the_ceiling():
    assert EntryFilter(max_rank=40).matches(ranked(40))


def test_a_rank_ceiling_drops_a_row_below_it():
    assert not EntryFilter(max_rank=40).matches(ranked(41))


def test_a_rank_ceiling_leaves_a_number_one_alone():
    # A number-ones list does not rank at all, because every row was already
    # first; filtering those by rank would drop the strongest rows.
    assert EntryFilter(max_rank=1).matches(number_one(1))


def test_a_weeks_floor_keeps_a_row_at_the_floor():
    assert EntryFilter(min_weeks=2).matches(number_one(2))


def test_a_weeks_floor_drops_a_shorter_run():
    assert not EntryFilter(min_weeks=2).matches(number_one(1))


def test_a_weeks_floor_leaves_a_year_end_row_alone():
    # The reverse of the rank rule: a year-end row carries no duration.
    assert EntryFilter(min_weeks=52).matches(ranked(1))


def test_a_number_one_with_no_recorded_duration_counts_as_one_week():
    entry = ChartEntry(
        kind=EntryKind.NUMBER_ONE, title="A", artist="B", reached=dt.date(1985, 1, 5)
    )
    assert EntryFilter(min_weeks=1).matches(entry)
    assert not EntryFilter(min_weeks=2).matches(entry)


def test_an_artist_matches_loosely_and_ignores_case():
    assert EntryFilter(artist="tlc").matches(ranked(1, artist="TLC featuring Left Eye"))


def test_an_artist_that_does_not_appear_drops_the_row():
    assert not EntryFilter(artist="Prince").matches(ranked(1, artist="TLC"))


def test_a_title_matches_loosely_and_ignores_case():
    assert EntryFilter(title="water").matches(ranked(1, title="Waterfalls"))


def test_a_title_that_does_not_appear_drops_the_row():
    assert not EntryFilter(title="Creep").matches(ranked(1, title="Waterfalls"))


def test_every_named_measure_must_hold_at_once():
    entry = ranked(10, title="Waterfalls", artist="TLC")
    assert EntryFilter(max_rank=20, artist="TLC", title="Water").matches(entry)
    assert not EntryFilter(max_rank=5, artist="TLC").matches(entry)


def test_a_filter_naming_any_measure_narrows():
    assert EntryFilter(max_rank=40).narrows()
    assert EntryFilter(min_weeks=2).narrows()
    assert EntryFilter(artist="TLC").narrows()
    assert EntryFilter(title="Waterfalls").narrows()


def test_measures_are_read_from_the_way_a_command_line_writes_them():
    wanted = EntryFilter.named(["max_rank=40", "min_weeks=2"])
    assert wanted.max_rank == 40
    assert wanted.min_weeks == 2


def test_surrounding_space_is_ignored():
    assert EntryFilter.named([" max_rank = 40 "]).max_rank == 40


def test_naming_nothing_narrows_nothing():
    assert not EntryFilter.named(None).narrows()
    assert not EntryFilter.named([]).narrows()


def test_a_measure_the_charts_do_not_publish_is_refused_with_the_ones_they_do():
    with pytest.raises(UnknownMeasure, match="max_rank, min_weeks, artist, title"):
        EntryFilter.named(["popularity=90"])


def test_a_pair_with_no_value_is_refused():
    with pytest.raises(UnknownMeasure):
        EntryFilter.named(["max_rank"])


def test_a_value_of_the_wrong_kind_is_refused_rather_than_ignored():
    with pytest.raises(UnknownMeasure):
        EntryFilter.named(["max_rank=lots"])
