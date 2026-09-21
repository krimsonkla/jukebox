"""Asking the corpus about songs and artists, in chart words only."""

import pytest

from jukebox.charts.errors import UnknownChart
from jukebox.mcp.tools import artist_songs, build_index, crossovers, find_song, index_status


@pytest.fixture(name="built")
def _built(workspace):
    """A workspace whose index has been built from the corpus."""
    build_index(workspace, (1985, 1985))
    return workspace


def test_building_reports_what_it_read(workspace):
    built = build_index(workspace, (1985, 1985))["built"]
    assert built["songs"] > 0
    assert built["appearances"] >= built["songs"]


def test_an_unbuilt_index_says_so_and_says_what_to_do(workspace):
    status = index_status(workspace)
    assert status["built"] is False
    assert "build_index" in status["advice"]


def test_a_built_index_reports_its_contents(built):
    status = index_status(built)
    assert status["built"] is True
    assert status["songs"] > 0


def test_a_song_is_found_and_carries_its_chart_history(built):
    found = find_song(built, "A", "x")
    assert found["found"] is True
    assert found["charts"] == ["hot-100"]
    assert found["years"] == [1985]


def test_a_song_the_corpus_lacks_is_reported_as_absent(built):
    assert find_song(built, "Not A Real Song", "Nobody")["found"] is False


def test_an_artist_lists_the_songs_credited_to_them(built):
    # The corpus credits "x" with two of the three ranked rows.
    found = artist_songs(built, "x")
    assert found["found"] is True
    assert found["total"] == 2


def test_an_artist_the_corpus_lacks_is_reported_as_absent(built):
    assert artist_songs(built, "Nobody At All")["found"] is False


def test_an_artist_listing_is_truncated_rather_than_unbounded(built):
    found = artist_songs(built, "x", limit=0)
    assert found["songs"] == []
    assert found["truncated"] is True


def test_a_crossover_names_the_charts_it_was_asked_about(built):
    found = crossovers(built, ["hot-100", "rnb"])
    assert found["charts"] == ["hot-100", "rnb"]
    assert found["total"] == len(found["songs"])


def test_a_crossover_listing_is_truncated_rather_than_unbounded(workspace):
    build_index(workspace, (1985, 1985))
    found = crossovers(workspace, ["hot-100"], limit=0)
    assert found["songs"] == []
    assert found["truncated"] is True


def test_an_unknown_chart_is_a_refusal_rather_than_a_traceback(built):
    with pytest.raises(UnknownChart):
        crossovers(built, ["not-a-chart"])


def test_no_tool_returns_a_track_uri(built):
    # Spotify's terms forbid its content reaching a model; these answer in the
    # vocabulary Billboard published and nothing else.
    answers = [
        find_song(built, "A", "x"),
        artist_songs(built, "x"),
        crossovers(built, ["hot-100"]),
        index_status(built),
    ]
    assert "spotify" not in repr(answers).lower()
    assert "uri" not in repr(answers).lower()
