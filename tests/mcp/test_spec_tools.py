"""A spec is the durable artifact of the conversation."""

import pytest

from jukebox.mcp.tools import get_spec, list_specs, preview_spec, put_spec
from jukebox.specs import NoSuchSpec

A_SPEC = {
    "name": "Test 85",
    "select": {"charts": ["hot-100"], "years": [1985, 1985]},
    "shape": {"size": 2, "max_per_artist": 1},
}


def test_a_stored_spec_reports_what_it_selects(workspace):
    stored = put_spec(workspace, A_SPEC)
    assert stored["stored"] == "test-85"
    assert stored["tracks"] == 2 and stored["considered"] == 3
    assert stored["dropped_to_cap"] == 1


def test_storing_a_spec_contacts_no_service_and_returns_chart_words(workspace):
    stored = put_spec(workspace, A_SPEC)
    assert [entry["title"] for entry in stored["entries"]] == ["A", "B"]
    assert "spotify" not in str(stored).lower()


def test_a_stored_spec_is_listed_and_read_back(workspace):
    put_spec(workspace, A_SPEC)
    assert list_specs(workspace)["specs"] == ["test-85"]
    assert get_spec(workspace, "Test 85")["spec"]["name"] == "Test 85"


def test_previewing_repeats_the_selection(workspace):
    put_spec(workspace, A_SPEC)
    assert preview_spec(workspace, "Test 85")["tracks"] == 2


def test_an_unknown_spec_is_refused_with_advice(workspace):
    with pytest.raises(NoSuchSpec, match="spec add"):
        preview_spec(workspace, "nope")


def test_an_invalid_spec_is_refused(workspace):
    with pytest.raises(ValueError):
        put_spec(workspace, {"name": "bad", "select": {"charts": [], "years": [1985, 1985]}})


def ordered(order: str) -> dict:
    """The same spec, sequenced the named way."""
    return {**A_SPEC, "shape": {**A_SPEC["shape"], "order": order}}


def test_a_preview_says_which_order_its_entries_are_in(workspace):
    put_spec(workspace, ordered("year"))
    found = preview_spec(workspace, "Test 85")
    assert found["order"] == "year"
    assert found["sequenced_at_resolution"] is False


def test_a_preview_says_when_the_sequence_is_settled_at_resolution(workspace):
    # A release ordering needs a date the corpus does not hold, so a preview
    # that did not say so would promise an order the apply would not produce.
    put_spec(workspace, ordered("release"))
    found = preview_spec(workspace, "Test 85")
    assert found["order"] == "release"
    assert found["sequenced_at_resolution"] is True
