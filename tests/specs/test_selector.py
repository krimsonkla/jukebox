"""Selection reads the corpus and keeps what the spec names."""

from jukebox.charts import Chart
from jukebox.specs import Exclusion, Selection, Selector, Spec


def spec_for(**over) -> Spec:
    """A spec over the Hot 100 for 1985."""
    selection = {"charts": [Chart.HOT_100], "years": (1985, 1985)} | over.pop("select", {})
    return Spec(name="s", select=Selection(**selection), **over)


def test_every_entry_of_a_named_chart_year_is_selected(corpus, ranked):
    ranked(Chart.HOT_100, 1985, (1, "A", "x"), (2, "B", "y"))
    assert len(Selector(corpus).select(spec_for())) == 2


def test_a_year_with_no_corpus_file_contributes_nothing(corpus, ranked):
    ranked(Chart.HOT_100, 1985, (1, "A", "x"))
    chosen = Selector(corpus).select(spec_for(select={"years": (1984, 1986)}))
    assert len(chosen) == 1 and chosen[0].year == 1985


def test_a_rank_ceiling_narrows_a_ranked_chart(corpus, ranked):
    ranked(Chart.HOT_100, 1985, (1, "A", "x"), (2, "B", "y"), (3, "C", "z"))
    chosen = Selector(corpus).select(spec_for(select={"max_rank": 2}))
    assert [c.title for c in chosen] == ["A", "B"]


def test_a_rank_ceiling_does_not_drop_number_ones(corpus, number_ones):
    # Every row on a number-ones chart was already first; filtering them by a
    # year-end rank would discard the strongest entries in the selection.
    number_ones(Chart.COUNTRY, 1985, ("A", "x", 1, 1), ("B", "y", 2, 3))
    spec = Spec(name="s", select=Selection(charts=[Chart.COUNTRY], years=(1985, 1985), max_rank=1))
    assert len(Selector(corpus).select(spec)) == 2


def test_a_weeks_floor_narrows_a_number_ones_chart(corpus, number_ones):
    number_ones(Chart.COUNTRY, 1985, ("A", "x", 1, 1), ("B", "y", 2, 3))
    spec = Spec(name="s", select=Selection(charts=[Chart.COUNTRY], years=(1985, 1985), min_weeks=2))
    assert [c.title for c in Selector(corpus).select(spec)] == ["B"]


def test_a_weeks_floor_does_not_drop_ranked_entries(corpus, ranked):
    ranked(Chart.HOT_100, 1985, (1, "A", "x"))
    assert len(Selector(corpus).select(spec_for(select={"min_weeks": 5}))) == 1


def test_several_charts_are_gathered_together(corpus, ranked):
    ranked(Chart.HOT_100, 1985, (1, "A", "x"))
    ranked(Chart.RNB, 1985, (1, "B", "y"))
    spec = Spec(name="s", select=Selection(charts=[Chart.HOT_100, Chart.RNB], years=(1985, 1985)))
    assert {c.chart for c in Selector(corpus).select(spec)} == {Chart.HOT_100, Chart.RNB}


def test_an_excluded_song_is_never_selected(corpus, ranked):
    ranked(Chart.HOT_100, 1985, (1, "Shout", "Tears for Fears"), (2, "B", "y"))
    spec = spec_for(exclude=[Exclusion(title="Shout")])
    assert [c.title for c in Selector(corpus).select(spec)] == ["B"]


def test_a_selected_entry_carries_where_it_came_from(corpus, ranked):
    ranked(Chart.HOT_100, 1985, (1, "A", "x"))
    chosen = Selector(corpus).select(spec_for())[0]
    assert (chosen.chart, chosen.year, chosen.title, chosen.artist) == (
        Chart.HOT_100,
        1985,
        "A",
        "x",
    )
