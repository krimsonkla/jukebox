"""Paging, chunking and the February 2026 field names."""

import json

import httpx
import pytest
import respx

from jukebox.net import RetryingClient
from jukebox.providers.spotify import SpotifyPlaylists

API = "https://api.spotify.com/v1"


class FixedCredentials:
    """A credential that never expires."""

    def bearer(self) -> str:
        """The token."""
        return "tok"


def playlists() -> SpotifyPlaylists:
    """An adapter that will not sleep between retries."""
    return SpotifyPlaylists(FixedCredentials(), RetryingClient(sleep=lambda _: None))


def row(uri: str, **over) -> dict:
    """A playlist item as the API now shapes it."""
    return {"is_local": False, "item": {"uri": uri, "type": "track"}} | over


@respx.mock
def test_creating_a_playlist_posts_to_the_current_user():
    route = respx.post(f"{API}/me/playlists").mock(
        return_value=httpx.Response(
            201, json={"id": "p1", "name": "S", "external_urls": {"spotify": "u"}}
        )
    )
    made = playlists().create("S", "why")
    body = json.loads(route.calls.last.request.read())
    assert body["name"] == "S" and body["public"] is False
    assert (made.id, made.name, made.url) == ("p1", "S", "u")


@respx.mock
def test_items_are_read_from_the_renamed_endpoint_and_field():
    respx.get(f"{API}/playlists/p1/items").mock(
        return_value=httpx.Response(200, json={"items": [row("u:a"), row("u:b")], "next": None})
    )
    assert playlists().items("p1") == ["u:a", "u:b"]


@respx.mock
def test_a_legacy_track_field_is_still_read():
    respx.get(f"{API}/playlists/p1/items").mock(
        return_value=httpx.Response(
            200,
            json={
                "items": [{"is_local": False, "track": {"uri": "u:a", "type": "track"}}],
                "next": None,
            },
        )
    )
    assert playlists().items("p1") == ["u:a"]


@respx.mock
def test_every_page_is_read():
    respx.get(f"{API}/playlists/p1/items").mock(
        side_effect=[
            httpx.Response(200, json={"items": [row("u:a")], "next": "more"}),
            httpx.Response(200, json={"items": [row("u:b")], "next": None}),
        ]
    )
    assert playlists().items("p1") == ["u:a", "u:b"]


@respx.mock
def test_a_local_file_or_an_episode_is_not_a_track():
    respx.get(f"{API}/playlists/p1/items").mock(
        return_value=httpx.Response(
            200,
            json={
                "items": [
                    row("u:a"),
                    row("u:local", is_local=True),
                    {"is_local": False, "item": {"uri": "u:ep", "type": "episode"}},
                    {"is_local": False, "item": None},
                ],
                "next": None,
            },
        )
    )
    assert playlists().items("p1") == ["u:a"]


@respx.mock
def test_replacing_sends_one_request_when_it_fits():
    route = respx.put(f"{API}/playlists/p1/items").mock(
        return_value=httpx.Response(200, json={"snapshot_id": "s"})
    )
    playlists().replace("p1", ["u:a", "u:b"])
    assert route.call_count == 1
    assert json.loads(route.calls.last.request.read())["uris"] == ["u:a", "u:b"]


@respx.mock
def test_a_long_list_is_replaced_then_appended_in_chunks():
    # The write cap is a hundred, so a longer playlist is one replace and then
    # appends; sending it all at once silently truncates.
    put = respx.put(f"{API}/playlists/p1/items").mock(
        return_value=httpx.Response(200, json={"snapshot_id": "s"})
    )
    post = respx.post(f"{API}/playlists/p1/items").mock(
        return_value=httpx.Response(201, json={"snapshot_id": "s"})
    )
    playlists().replace("p1", [f"u:{index}" for index in range(250)])
    assert put.call_count == 1 and post.call_count == 2


@respx.mock
def test_replacing_with_nothing_empties_the_playlist():
    put = respx.put(f"{API}/playlists/p1/items").mock(
        return_value=httpx.Response(200, json={"snapshot_id": "s"})
    )
    playlists().replace("p1", [])
    assert put.call_count == 1
    assert json.loads(put.calls.last.request.read())["uris"] == []


@respx.mock
@pytest.mark.parametrize("status", [403, 404])
def test_a_playlist_that_is_gone_reads_as_absent(status):
    respx.get(f"{API}/playlists/p1").mock(return_value=httpx.Response(status, json={}))
    assert playlists().find("p1") is None


@respx.mock
def test_a_playlist_that_exists_is_returned():
    respx.get(f"{API}/playlists/p1").mock(
        return_value=httpx.Response(200, json={"id": "p1", "name": "S"})
    )
    assert playlists().find("p1").name == "S"


@respx.mock
def test_a_server_error_on_read_is_not_swallowed():
    respx.get(f"{API}/playlists/p1").mock(return_value=httpx.Response(401, json={}))
    with pytest.raises(httpx.HTTPStatusError):
        playlists().find("p1")


@respx.mock
def test_a_failed_write_is_not_swallowed():
    respx.put(f"{API}/playlists/p1/items").mock(return_value=httpx.Response(403, json={}))
    with pytest.raises(httpx.HTTPStatusError):
        playlists().replace("p1", ["u:a"])
