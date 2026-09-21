"""The two grants a PKCE client makes against a token endpoint."""

import datetime as dt

import httpx

from jukebox.oauth.errors import AuthorizationDenied
from jukebox.oauth.token import Token

FORM = {"Content-Type": "application/x-www-form-urlencoded"}


class TokenClient:
    """Exchanges an authorization code, and refreshes an expired token."""

    def __init__(self, token_url: str, client_id: str, client: httpx.Client | None = None) -> None:
        self._token_url = token_url
        self._client_id = client_id
        self._client = client or httpx.Client(timeout=30.0)

    def exchange(self, code: str, verifier: str, redirect_uri: str, now: dt.datetime) -> Token:
        """Redeem an authorization code for a token."""
        return self._grant(
            {
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": redirect_uri,
                "client_id": self._client_id,
                "code_verifier": verifier,
            },
            now,
            None,
        )

    def refresh(self, token: Token, now: dt.datetime) -> Token:
        """Renew an access token, carrying the refresh token forward if none is returned."""
        return self._grant(
            {
                "grant_type": "refresh_token",
                "refresh_token": token.refresh_token,
                "client_id": self._client_id,
            },
            now,
            token,
        )

    def _grant(self, form: dict, now: dt.datetime, previous: Token | None) -> Token:
        response = self._client.post(self._token_url, data=form, headers=FORM)
        payload = response.json()
        if "error" in payload:
            raise AuthorizationDenied(payload.get("error_description") or str(payload["error"]))
        response.raise_for_status()
        return Token.issued(payload, now, previous)
