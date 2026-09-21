"""The grants, against a mocked token endpoint."""

import datetime as dt

import httpx
import pytest
import respx

from jukebox.oauth import AuthorizationDenied, Token, TokenClient

URL = "https://accounts.example/api/token"
NOW = dt.datetime(2026, 9, 7, 12, 0, tzinfo=dt.UTC)
GRANT = {"access_token": "a", "expires_in": 3600, "refresh_token": "r", "scope": "s"}


@respx.mock
def test_exchange_sends_the_verifier_and_no_secret():
    route = respx.post(URL).mock(return_value=httpx.Response(200, json=GRANT))
    token = TokenClient(URL, "cid").exchange("code", "verif", "http://127.0.0.1:8888/callback", NOW)
    body = dict(pair.split("=", 1) for pair in route.calls.last.request.content.decode().split("&"))
    assert body["grant_type"] == "authorization_code"
    assert body["code_verifier"] == "verif"
    assert body["client_id"] == "cid"
    assert "client_secret" not in body
    assert token.access_token == "a"


@respx.mock
def test_refresh_sends_the_refresh_grant():
    route = respx.post(URL).mock(
        return_value=httpx.Response(200, json={"access_token": "b", "expires_in": 3600})
    )
    held = Token(access_token="a", refresh_token="r", expires_at=NOW)
    renewed = TokenClient(URL, "cid").refresh(held, NOW)
    assert "grant_type=refresh_token" in route.calls.last.request.content.decode()
    assert renewed.refresh_token == "r"


@respx.mock
def test_an_error_payload_is_raised_with_its_description():
    respx.post(URL).mock(
        return_value=httpx.Response(
            400, json={"error": "invalid_grant", "error_description": "code expired"}
        )
    )
    with pytest.raises(AuthorizationDenied, match="code expired"):
        TokenClient(URL, "cid").exchange("code", "v", "uri", NOW)


@respx.mock
def test_an_error_without_a_description_still_names_the_error():
    respx.post(URL).mock(return_value=httpx.Response(400, json={"error": "invalid_client"}))
    with pytest.raises(AuthorizationDenied, match="invalid_client"):
        TokenClient(URL, "cid").exchange("code", "v", "uri", NOW)


@respx.mock
def test_a_server_failure_is_not_swallowed():
    respx.post(URL).mock(return_value=httpx.Response(503, json={}))
    with pytest.raises(httpx.HTTPStatusError):
        TokenClient(URL, "cid").exchange("code", "v", "uri", NOW)
