"""A stored spec becomes a tracklist without touching a music service."""

import pytest

from jukebox.charts import Chart
from jukebox.specs import EmptySelection, Evaluate, Selection, Shape, Spec


def test_a_spec_evaluates_to_an_ordered_tracklist(corpus, ranked):
    ranked(Chart.HOT_100, 1985, (2, "B", "y"), (1, "A", "x"))
    spec = Spec(name="s", select=Selection(charts=[Chart.HOT_100], years=(1985, 1985)))
    assert [e.title for e in Evaluate(corpus).tracklist(spec).entries] == ["A", "B"]


def test_a_selection_that_matches_nothing_says_how_to_widen_it(corpus):
    spec = Spec(name="Empty", select=Selection(charts=[Chart.LATIN], years=(1985, 1985)))
    with pytest.raises(EmptySelection, match="charts fetch"):
        Evaluate(corpus).tracklist(spec)


def test_shaping_is_applied_to_what_was_selected(corpus, ranked):
    ranked(Chart.HOT_100, 1985, (1, "A", "x"), (2, "B", "x"), (3, "C", "y"))
    spec = Spec(
        name="s",
        select=Selection(charts=[Chart.HOT_100], years=(1985, 1985)),
        shape=Shape(max_per_artist=1, size=1),
    )
    tracklist = Evaluate(corpus).tracklist(spec)
    assert [e.title for e in tracklist.entries] == ["A"]
    assert tracklist.considered == 3


def test_a_selection_sees_a_chart_article_and_a_discography_as_one_chart(
    corpus, number_ones, peaks
):
    # What the chart's own article recorded, and what an artist's article says
    # about the records that never reached the top, are the same chart.
    number_ones(Chart.MAINSTREAM_ROCK, 1993, ("Cryin'", "Aerosmith", 6, 3))
    peaks(Chart.MAINSTREAM_ROCK, 1993, (7, "Rooster", "Alice in Chains"))
    spec = Spec(
        name="Rock 1993",
        select=Selection(charts=[Chart.MAINSTREAM_ROCK], years=(1993, 1993)),
    )
    chosen = Evaluate(corpus).tracklist(spec)
    assert sorted(entry.title for entry in chosen.entries) == ["Cryin'", "Rooster"]


def test_a_peak_ceiling_narrows_a_discography_without_touching_the_number_ones(
    corpus, number_ones, peaks
):
    number_ones(Chart.MAINSTREAM_ROCK, 1993, ("Cryin'", "Aerosmith", 6, 3))
    peaks(Chart.MAINSTREAM_ROCK, 1993, (7, "Rooster", "Alice in Chains"), (40, "Deep", "A Band"))
    spec = Spec(
        name="Rock 1993",
        select=Selection(charts=[Chart.MAINSTREAM_ROCK], years=(1993, 1993), max_peak=10),
    )
    chosen = Evaluate(corpus).tracklist(spec)
    assert sorted(entry.title for entry in chosen.entries) == ["Cryin'", "Rooster"]
