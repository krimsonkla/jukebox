"""A session hands out a bearer that works now."""

import datetime as dt

import httpx
import pytest
import respx

from jukebox.oauth import Flow, NotAuthorized, Session, Token, TokenClient, TokenStore

URL = "https://accounts.example/api/token"
NOW = dt.datetime(2026, 9, 7, 12, 0, tzinfo=dt.UTC)


def session_over(tmp_path) -> tuple[Session, TokenStore]:
    """A session and the store behind it."""
    store = TokenStore(tmp_path, "spotify")
    flow = Flow(store=store, client=TokenClient(URL, "cid"), clock=lambda: NOW)
    return Session("spotify", flow), store


def test_no_stored_token_says_to_log_in(tmp_path):
    session, _ = session_over(tmp_path)
    with pytest.raises(NotAuthorized, match="auth login"):
        session.bearer()


def test_a_live_token_is_handed_back_untouched(tmp_path):
    session, store = session_over(tmp_path)
    store.save(
        Token(access_token="live", refresh_token="r", expires_at=NOW + dt.timedelta(hours=1))
    )
    assert session.bearer() == "live"


@respx.mock
def test_an_expired_token_is_refreshed_and_restored(tmp_path):
    respx.post(URL).mock(
        return_value=httpx.Response(200, json={"access_token": "fresh", "expires_in": 3600})
    )
    session, store = session_over(tmp_path)
    store.save(
        Token(access_token="stale", refresh_token="r", expires_at=NOW - dt.timedelta(minutes=1))
    )
    assert session.bearer() == "fresh"
    assert store.load().access_token == "fresh"
    assert store.load().refresh_token == "r"
