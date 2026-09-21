"""The adapter reports what Spotify offered; it ranks nothing."""

import datetime as dt

import httpx
import pytest
import respx

from jukebox.net import RetryingClient
from jukebox.providers.spotify import SpotifyCatalog

SEARCH = "https://api.spotify.com/v1/search"


class FixedCredentials:
    """A credential that never expires."""

    def bearer(self) -> str:
        """The token."""
        return "tok"


def catalog() -> SpotifyCatalog:
    """A catalogue that will not sleep between retries."""
    return SpotifyCatalog(FixedCredentials(), RetryingClient(sleep=lambda _: None))


def track(**over) -> dict:
    """A Spotify track object."""
    return {
        "uri": "spotify:track:1",
        "name": "Take On Me",
        "artists": [{"name": "a-ha"}],
        "album": {"name": "Hunting High and Low", "release_date": "1985-06-01"},
    } | over


@respx.mock
def test_a_search_is_filtered_by_track_and_artist():
    route = respx.get(SEARCH).mock(
        return_value=httpx.Response(200, json={"tracks": {"items": [track()]}})
    )
    matches = catalog().search("Take On Me", "a-ha")
    request = route.calls.last.request
    assert request.url.params["q"] == 'track:"Take On Me" artist:"a-ha"'
    assert request.url.params["type"] == "track"
    assert request.headers["authorization"] == "Bearer tok"
    assert matches[0].uri == "spotify:track:1"
    assert matches[0].released == dt.date(1985, 6, 1)


@respx.mock
def test_the_page_size_is_the_ten_spotify_now_allows():
    route = respx.get(SEARCH).mock(return_value=httpx.Response(200, json={}))
    catalog().search("t", "a")
    assert route.calls.last.request.url.params["limit"] == "10"


@respx.mock
def test_an_isrc_lookup_uses_the_isrc_filter():
    route = respx.get(SEARCH).mock(return_value=httpx.Response(200, json={}))
    catalog().by_isrc("GBUM72407046")
    assert route.calls.last.request.url.params["q"] == "isrc:GBUM72407046"


@respx.mock
def test_several_artists_are_joined_into_one_credit():
    respx.get(SEARCH).mock(
        return_value=httpx.Response(
            200,
            json={
                "tracks": {
                    "items": [track(artists=[{"name": "Phil Collins"}, {"name": "Marilyn Martin"}])]
                }
            },
        )
    )
    assert catalog().search("t", "a")[0].artist == "Phil Collins, Marilyn Martin"


@respx.mock
@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("1985-06-01", dt.date(1985, 6, 1)),
        ("1985-06", dt.date(1985, 6, 1)),
        ("1985", dt.date(1985, 1, 1)),
        (None, None),
    ],
)
def test_a_partial_release_date_still_reads(value, expected):
    album = {"name": "x"} | ({"release_date": value} if value else {})
    respx.get(SEARCH).mock(
        return_value=httpx.Response(200, json={"tracks": {"items": [track(album=album)]}})
    )
    assert catalog().search("t", "a")[0].released == expected


@respx.mock
def test_no_results_is_an_empty_list_not_a_failure():
    respx.get(SEARCH).mock(return_value=httpx.Response(200, json={"tracks": {"items": []}}))
    assert catalog().search("t", "a") == []


@respx.mock
def test_a_rate_limit_is_waited_out_rather_than_ending_the_run():
    respx.get(SEARCH).mock(
        side_effect=[
            httpx.Response(429),
            httpx.Response(200, json={"tracks": {"items": [track()]}}),
        ]
    )
    assert len(catalog().search("t", "a")) == 1


@respx.mock
def test_an_unauthorized_response_is_not_swallowed():
    respx.get(SEARCH).mock(return_value=httpx.Response(401, json={}))
    with pytest.raises(httpx.HTTPStatusError):
        catalog().search("t", "a")


@respx.mock
def test_a_quotation_mark_in_a_title_does_not_break_the_query():
    # It closed the track: field early and the rest parsed as query syntax, so
    # the result was silently wrong rather than absent.
    route = respx.get(SEARCH).mock(return_value=httpx.Response(200, json={}))
    catalog().search('Say "Hello"', 'The "Band"')
    query = route.calls.last.request.url.params["q"]
    assert query.count('"') == 4
    assert "Hello" in query and "Band" in query
