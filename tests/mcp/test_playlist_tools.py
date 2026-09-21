"""Planning reads; applying is the only tool that changes an account."""

import pytest

from jukebox.mcp.tools import apply_playlist, plan_playlist, put_spec
from jukebox.reconcile import NothingResolved

A_SPEC = {
    "name": "Test 85",
    "select": {"charts": ["hot-100"], "years": [1985, 1985]},
    "shape": {"size": 2, "max_per_artist": 1},
}


def stored(workspace) -> None:
    """Store the spec under test."""
    put_spec(workspace, A_SPEC)


def test_planning_reports_the_change_and_writes_nothing(workspace, service):
    stored(workspace)
    found = plan_playlist(workspace, service, "Test 85")
    assert found["creates_playlist"] and found["adding"] == 2
    assert service.writes == [] and service.created == []


def test_applying_creates_the_playlist_and_returns_its_link(workspace, service):
    stored(workspace)
    done = apply_playlist(workspace, service, "Test 85")
    assert done["applied"] is True
    assert done["playlist_url"].startswith("https://open.spotify.com/playlist/")
    assert service.writes


def test_applying_twice_changes_nothing_the_second_time(workspace, service):
    stored(workspace)
    apply_playlist(workspace, service, "Test 85")
    again = apply_playlist(workspace, service, "Test 85")
    assert again["applied"] is False and again["changes"] is False


def test_a_track_added_by_hand_is_reported_and_kept(workspace, service):
    stored(workspace)
    playlist_id = service.writes[0][0] if service.writes else None
    apply_playlist(workspace, service, "Test 85")
    playlist_id = service.writes[0][0]
    service.playlists[playlist_id].append("u:mine")

    found = plan_playlist(workspace, service, "Test 85")
    assert found["kept_because_you_added_them"] == 1
    apply_playlist(workspace, service, "Test 85")
    assert "u:mine" in service.playlists[playlist_id]


def test_replacing_manual_additions_must_be_asked_for(workspace, service):
    stored(workspace)
    apply_playlist(workspace, service, "Test 85")
    playlist_id = service.writes[0][0]
    service.playlists[playlist_id].append("u:mine")
    apply_playlist(workspace, service, "Test 85", replace_manual=True)
    assert "u:mine" not in service.playlists[playlist_id]


def test_an_entry_with_no_resolution_is_named_not_dropped(workspace, service):
    put_spec(
        workspace,
        {
            "name": "Country 85",
            "select": {"charts": ["country"], "years": [1985, 1985]},
        },
    )
    with pytest.raises(NothingResolved, match="resolve backfill"):
        plan_playlist(workspace, service, "Country 85")


def test_nothing_on_the_wire_is_catalogue_data(workspace, service):
    # The developer terms forbid ingesting Spotify Content into a model, so a
    # track identifier must never reach a tool result.
    stored(workspace)
    for result in (
        plan_playlist(workspace, service, "Test 85"),
        apply_playlist(workspace, service, "Test 85"),
    ):
        assert "u:A" not in str(result)
        assert "spotify:track" not in str(result)
