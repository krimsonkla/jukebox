"""A spec is the user's description, in the charts' vocabulary."""

import pytest
from pydantic import ValidationError

from jukebox.charts import Chart
from jukebox.specs import Exclusion, Ordering, Selection, Shape, Spec


def a_spec(**over) -> Spec:
    """A minimal valid spec."""
    return Spec(
        name="90s Alt-Rock",
        select=Selection(charts=[Chart.MODERN_ROCK], years=(1990, 1999)),
        **over,
    )


def test_a_spec_slugs_to_a_filename():
    assert a_spec().slug() == "90s-alt-rock"


def test_a_selection_needs_at_least_one_chart():
    with pytest.raises(ValidationError):
        Selection(charts=[], years=(1990, 1999))


def test_a_selection_knows_the_years_it_spans():
    selection = Selection(charts=[Chart.HOT_100], years=(1990, 1992))
    assert list(selection.span()) == [1990, 1991, 1992]
    assert selection.covers(1991) and not selection.covers(1989)


def test_a_size_must_be_positive():
    with pytest.raises(ValidationError):
        Shape(size=0)


def test_the_default_shape_takes_everything_in_chart_order():
    shape = a_spec().shape
    assert shape.size is None and shape.max_per_artist is None
    assert shape.order is Ordering.CHART


def test_an_exclusion_matches_however_the_chart_spells_it():
    rule = Exclusion(title="Don't You (Forget About Me)", artist="Simple Minds")
    assert rule.matches("Dont You (Forget About Me)", "The Simple Minds")


def test_an_exclusion_without_an_artist_drops_the_song_by_anyone():
    assert Exclusion(title="Shout").matches("Shout", "Tears for Fears")
    assert Exclusion(title="Shout").matches("Shout!", "Otis Day")


def test_an_exclusion_with_an_artist_leaves_other_versions_alone():
    rule = Exclusion(title="Shout", artist="Tears for Fears")
    assert not rule.matches("Shout", "Otis Day")


def test_a_spec_reports_what_it_excludes():
    spec = a_spec(exclude=[Exclusion(title="Shout")])
    assert spec.excluded("Shout", "Tears for Fears")
    assert not spec.excluded("Take On Me", "a-ha")


def test_a_spec_names_no_music_service():
    # Specs are committed; another service's identifiers must not reach the repo.
    assert "spotify" not in a_spec().model_dump_json().lower()
