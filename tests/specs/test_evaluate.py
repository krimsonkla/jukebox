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
