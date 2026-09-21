"""MusicBrainz answers a recording in two calls, and asks to be asked slowly."""

import httpx
import respx

from jukebox.net import RetryingClient
from jukebox.providers.musicbrainz import MusicBrainzIsrcs

SEARCH = "https://musicbrainz.org/ws/2/recording"


def isrcs(waited: list[float]) -> MusicBrainzIsrcs:
    """An adapter recording what it would have slept."""
    return MusicBrainzIsrcs(RetryingClient(sleep=lambda _: None), sleep=waited.append)


@respx.mock
def test_the_first_recording_carrying_an_isrc_answers():
    respx.get(SEARCH).mock(
        return_value=httpx.Response(200, json={"recordings": [{"id": "mbid-1"}]})
    )
    respx.get(f"{SEARCH}/mbid-1").mock(
        return_value=httpx.Response(200, json={"isrcs": ["GBUM72407046"]})
    )
    assert isrcs([]).isrcs_for("Money for Nothing", "Dire Straits") == ("GBUM72407046",)


@respx.mock
def test_a_recording_without_an_isrc_is_passed_over():
    respx.get(SEARCH).mock(
        return_value=httpx.Response(200, json={"recordings": [{"id": "a"}, {"id": "b"}]})
    )
    respx.get(f"{SEARCH}/a").mock(return_value=httpx.Response(200, json={"isrcs": []}))
    respx.get(f"{SEARCH}/b").mock(return_value=httpx.Response(200, json={"isrcs": ["X"]}))
    assert isrcs([]).isrcs_for("t", "a") == ("X",)


@respx.mock
def test_nothing_known_is_an_empty_tuple():
    respx.get(SEARCH).mock(return_value=httpx.Response(200, json={"recordings": []}))
    assert not isrcs([]).isrcs_for("t", "a")


@respx.mock
def test_the_service_is_asked_about_once_a_second():
    respx.get(SEARCH).mock(return_value=httpx.Response(200, json={"recordings": []}))
    waited = []
    isrcs(waited).isrcs_for("t", "a")
    assert waited and all(pause >= 1.0 for pause in waited)


@respx.mock
def test_a_descriptive_user_agent_is_sent_because_the_service_asks_for_one():
    route = respx.get(SEARCH).mock(return_value=httpx.Response(200, json={"recordings": []}))
    isrcs([]).isrcs_for("t", "a")
    assert "jukebox" in route.calls.last.request.headers["user-agent"]
