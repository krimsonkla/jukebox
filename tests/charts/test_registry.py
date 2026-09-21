"""Era drift lives in the registry, not in branching — spec §AC 4, 5."""

import pytest

from jukebox.charts import Chart, GapReason, PageShape, Registry


@pytest.fixture(name="registry")
def _registry():
    return Registry.billboard()


def test_rnb_resolves_through_its_era_name(registry):
    assert registry.resolve(Chart.RNB, 1985).title == (
        "Billboard Year-End Hot Black Singles of 1985"
    )
    assert registry.resolve(Chart.RNB, 1995).title == ("Billboard Year-End Hot R&B Singles of 1995")


def test_the_same_chart_can_change_shape_with_the_era(registry):
    assert registry.resolve(Chart.HOT_100, 1985).shape is PageShape.RANKED
    assert registry.resolve(Chart.COUNTRY, 1985).shape is PageShape.NUMBER_ONES
    assert registry.resolve(Chart.MODERN_ROCK, 1990).shape is PageShape.DECADE


def test_a_chart_that_did_not_exist_yet_is_a_gap(registry):
    gap = registry.resolve(Chart.MODERN_ROCK, 1985)
    assert gap.reason is GapReason.CHART_DID_NOT_EXIST


def test_every_gap_states_a_reason(registry):
    assert all(gap.reason is not None for gap in registry.gaps(1985))


def test_a_year_the_registry_does_not_cover_is_a_gap(registry):
    # The Hot 100 ran in 1970; the registry simply declares no page for it.
    assert registry.resolve(Chart.HOT_100, 1970).reason is GapReason.NO_ARTICLE


def test_a_year_before_the_chart_existed_says_so_instead(registry):
    assert registry.resolve(Chart.HOT_100, 1899).reason is GapReason.CHART_DID_NOT_EXIST


def test_decade_pages_resolve_to_one_title_for_every_year_of_the_decade(registry):
    titles = {registry.resolve(Chart.MODERN_ROCK, y).title for y in (1990, 1995, 1999)}
    assert titles == {"List of Billboard Modern Rock Tracks number ones of the 1990s"}
