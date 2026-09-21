"""The Spotify adapter's half of the flow: state, redirect rules, storage."""

import datetime as dt
import urllib.parse

import httpx
import pytest
import respx

from jukebox.oauth import AuthorizationDenied, Callback, StateMismatch, Token, TokenStore
from jukebox.providers.spotify import MissingClientId, SpotifySettings, build_auth

TOKEN_URL = "https://accounts.spotify.com/api/token"
NOW = dt.datetime(2026, 9, 7, 12, 0, tzinfo=dt.UTC)
GRANT = {
    "access_token": "a",
    "expires_in": 3600,
    "refresh_token": "r",
    "scope": "playlist-modify-private",
}


def state_of(url: str) -> str:
    """The state parameter the adapter generated."""
    return dict(urllib.parse.parse_qsl(urllib.parse.urlparse(url).query))["state"]


@respx.mock
def test_login_opens_consent_then_stores_what_is_granted(build, opened, settings):
    respx.post(TOKEN_URL).mock(return_value=httpx.Response(200, json=GRANT))
    # The adapter mints the state, so the fake echoes back whatever it used.
    service = build(lambda: Callback(code="c", state=state_of(opened[0]), error=None))
    status = service.login()

    assert status.authorized and status.provider == "spotify"
    assert status.scopes == ("playlist-modify-private",)
    assert TokenStore(settings.state_dir, "spotify").load().refresh_token == "r"


def test_a_callback_with_the_wrong_state_is_refused(build):
    with pytest.raises(StateMismatch):
        build(Callback(code="c", state="not-the-one", error=None)).login()


def test_a_denied_authorization_names_the_reason(build):
    with pytest.raises(AuthorizationDenied, match="access_denied"):
        build(Callback(code=None, state=None, error="access_denied")).login()


def test_a_callback_with_neither_code_nor_error_is_refused(build, opened):
    service = build(lambda: Callback(code=None, state=state_of(opened[0]), error=None))
    with pytest.raises(AuthorizationDenied, match="no code"):
        service.login()


def test_status_reports_nothing_before_a_login(build):
    assert build(Callback(None, None, None)).status().authorized is False


def test_status_reports_an_expired_token_as_unauthorized(build, settings):
    TokenStore(settings.state_dir, "spotify").save(
        Token(access_token="a", refresh_token="r", expires_at=NOW - dt.timedelta(hours=1))
    )
    assert build(Callback(None, None, None)).status().authorized is False


def test_status_reports_a_live_token_with_its_scopes(build, settings):
    TokenStore(settings.state_dir, "spotify").save(
        Token(
            access_token="a",
            refresh_token="r",
            expires_at=NOW + dt.timedelta(hours=1),
            scope="s1 s2",
        )
    )
    status = build(Callback(None, None, None)).status()
    assert status.authorized and status.scopes == ("s1", "s2")


def test_logout_reports_whether_anything_was_stored(build, settings):
    service = build(Callback(None, None, None))
    assert service.logout() is False
    TokenStore(settings.state_dir, "spotify").save(
        Token(access_token="a", refresh_token="r", expires_at=NOW)
    )
    assert service.logout() is True


def test_the_redirect_is_a_loopback_literal_not_localhost():
    # Spotify permits HTTP only for a loopback IP literal, and rejects localhost.
    assert SpotifySettings(client_id="c").redirect_uri == "http://127.0.0.1:8888/callback"


def test_without_a_client_id_the_adapter_says_where_to_get_one(tmp_path):
    with pytest.raises(MissingClientId, match=r"developer\.spotify\.com"):
        build_auth(SpotifySettings(client_id="", state_dir=tmp_path))
