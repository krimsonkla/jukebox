"""Order, then cap, then cut — in that order."""

import datetime as dt

from jukebox.charts import Chart, ChartEntry, EntryKind
from jukebox.specs import Ordering, Selected, Selection, Shape, Shaper, Spec


def ranked_at(
    rank: int, title: str, artist: str, year: int = 1985, chart: Chart = Chart.HOT_100
) -> Selected:
    """A ranked selection."""
    return Selected(
        chart=chart,
        year=year,
        entry=ChartEntry(kind=EntryKind.RANKED, rank=rank, title=title, artist=artist),
    )


def number_one(
    month: int, title: str, artist: str, year: int = 1985, chart: Chart = Chart.COUNTRY
) -> Selected:
    """A number-one selection."""
    return Selected(
        chart=chart,
        year=year,
        entry=ChartEntry(
            kind=EntryKind.NUMBER_ONE,
            title=title,
            artist=artist,
            reached=dt.date(year, month, 1),
            weeks=1,
        ),
    )


def spec_with(**shape) -> Spec:
    """A spec whose shaping is under test."""
    return Spec(
        name="s", select=Selection(charts=[Chart.HOT_100], years=(1985, 1985)), shape=Shape(**shape)
    )


def test_chart_order_follows_the_rank():
    chosen = [ranked_at(3, "C", "z"), ranked_at(1, "A", "x"), ranked_at(2, "B", "y")]
    shaped = Shaper().shape(spec_with(), chosen)
    assert [entry.title for entry in shaped.entries] == ["A", "B", "C"]


def test_number_ones_fall_into_date_order():
    chosen = [number_one(3, "C", "z"), number_one(1, "A", "x")]
    shaped = Shaper().shape(spec_with(), chosen)
    assert [entry.title for entry in shaped.entries] == ["A", "C"]


def test_year_order_puts_the_earlier_year_first():
    chosen = [ranked_at(1, "B", "y", year=1986), ranked_at(2, "A", "x", year=1985)]
    shaped = Shaper().shape(spec_with(order=Ordering.YEAR), chosen)
    assert [entry.title for entry in shaped.entries] == ["A", "B"]


def test_a_shuffle_is_the_same_every_time_for_a_seed():
    chosen = [ranked_at(i, f"T{i}", f"a{i}") for i in range(1, 12)]
    first = Shaper().shape(spec_with(order=Ordering.SHUFFLE, seed=7), chosen)
    again = Shaper().shape(spec_with(order=Ordering.SHUFFLE, seed=7), chosen)
    assert [e.title for e in first.entries] == [e.title for e in again.entries]


def test_a_different_seed_gives_a_different_order():
    chosen = [ranked_at(i, f"T{i}", f"a{i}") for i in range(1, 12)]
    one = Shaper().shape(spec_with(order=Ordering.SHUFFLE, seed=1), chosen)
    two = Shaper().shape(spec_with(order=Ordering.SHUFFLE, seed=2), chosen)
    assert [e.title for e in one.entries] != [e.title for e in two.entries]


def test_the_per_artist_cap_keeps_the_best_placed_and_counts_the_rest():
    chosen = [
        ranked_at(1, "A", "Madonna"),
        ranked_at(2, "B", "Madonna"),
        ranked_at(3, "C", "Wham!"),
    ]
    shaped = Shaper().shape(spec_with(max_per_artist=1), chosen)
    assert [entry.title for entry in shaped.entries] == ["A", "C"]
    assert shaped.dropped_to_cap == 1


def test_the_cap_ignores_case_in_an_artist_name():
    chosen = [ranked_at(1, "A", "Madonna"), ranked_at(2, "B", "madonna")]
    assert len(Shaper().shape(spec_with(max_per_artist=1), chosen).entries) == 1


def test_the_cap_is_applied_after_ordering_not_before():
    # Capping first would drop the entry the ordering ranks highest.
    chosen = [ranked_at(9, "Low", "Madonna"), ranked_at(1, "High", "Madonna")]
    shaped = Shaper().shape(spec_with(max_per_artist=1), chosen)
    assert [entry.title for entry in shaped.entries] == ["High"]


def test_size_cuts_the_list_after_the_cap():
    chosen = [ranked_at(i, f"T{i}", f"a{i}") for i in range(1, 6)]
    assert len(Shaper().shape(spec_with(size=3), chosen).entries) == 3


def test_asking_for_more_than_exists_yields_what_exists():
    chosen = [ranked_at(1, "A", "x")]
    assert len(Shaper().shape(spec_with(size=50), chosen).entries) == 1


def test_the_tracklist_counts_what_it_considered():
    chosen = [ranked_at(i, f"T{i}", f"a{i}") for i in range(1, 6)]
    assert Shaper().shape(spec_with(size=2), chosen).considered == 5


def test_the_report_names_each_chart_that_contributed():
    chosen = [ranked_at(1, "A", "x"), number_one(1, "B", "y")]
    shaped = Shaper().shape(spec_with(), chosen)
    assert shaped.composition() == {"hot-100": 1, "country": 1}
    assert "from: country 1, hot-100 1" in shaped.render()


def test_a_single_chart_selection_does_not_report_a_split():
    shaped = Shaper().shape(spec_with(), [ranked_at(1, "A", "x")])
    assert "from:" not in shaped.render()


def test_the_report_states_what_the_cap_held_back():
    chosen = [ranked_at(1, "A", "Madonna"), ranked_at(2, "B", "Madonna")]
    assert "1 held back" in Shaper().shape(spec_with(max_per_artist=1), chosen).render()


def test_a_release_ordering_cuts_and_caps_in_chart_year_order():
    # The date it will finally sequence by is not knowable from the corpus, so
    # what survives the size must still be decided by something the corpus knows.
    chosen = [
        ranked_at(1, "C", "z", year=1987),
        ranked_at(1, "A", "x", year=1985),
        ranked_at(1, "B", "y", year=1986),
    ]
    shaped = Shaper().shape(spec_with(order=Ordering.RELEASE, size=2), chosen)
    assert [entry.title for entry in shaped.entries] == ["A", "B"]


def test_a_tracklist_says_when_its_sequence_is_not_yet_final():
    shaped = Shaper().shape(spec_with(order=Ordering.RELEASE), [ranked_at(1, "A", "x")])
    assert shaped.sequenced_later is True
    assert "sequenced by release date when resolved" in shaped.render()


def test_any_other_ordering_is_final_where_it_is_shaped():
    shaped = Shaper().shape(spec_with(order=Ordering.YEAR), [ranked_at(1, "A", "x")])
    assert shaped.sequenced_later is False
    assert "release date" not in shaped.render()
