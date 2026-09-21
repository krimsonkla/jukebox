"""Spotify's implementation of the ProviderAuth port.

Authorization Code with PKCE over a one-shot loopback redirect. The flow itself
lives in `jukebox.oauth`; what is Spotify-specific is the pair of endpoints, the
scopes, and the redirect rule that permits HTTP only for a loopback IP literal.
"""

import datetime as dt
import secrets
import webbrowser
from collections.abc import Callable

from jukebox.oauth.authorization_request import AuthorizationRequest
from jukebox.oauth.callback import Callback
from jukebox.oauth.errors import AuthorizationDenied, StateMismatch
from jukebox.oauth.flow import Flow
from jukebox.oauth.loopback import Loopback
from jukebox.oauth.pkce import Pkce
from jukebox.ports.auth_status import AuthStatus
from jukebox.providers.spotify.endpoints import AUTHORIZE_URL, SCOPES
from jukebox.providers.spotify.settings import SpotifySettings

NAME = "spotify"


class SpotifyAuth:
    """Obtains, reports and discards Spotify authorization."""

    name = NAME

    def __init__(
        self,
        settings: SpotifySettings,
        flow: Flow,
        open_url: Callable[[str], bool] | None = None,
        loopback: Loopback | None = None,
    ) -> None:
        self._settings = settings
        self._flow = flow
        self._open_url = open_url or webbrowser.open
        self._loopback = loopback or Loopback(settings.redirect_host, settings.redirect_port)

    def login(self) -> AuthStatus:
        """Send the user to Spotify, catch the redirect, and store the token."""
        pkce, state = Pkce.generate(), secrets.token_urlsafe(24)
        # Bound before the browser opens: a squatter on the port would otherwise
        # take the redirect and the user would consent for nothing.
        listening = self._loopback.bind() if hasattr(self._loopback, "bind") else self._loopback
        self._open_url(
            AuthorizationRequest(
                endpoint=AUTHORIZE_URL,
                client_id=self._settings.client_id,
                redirect_uri=self._settings.redirect_uri,
                scopes=SCOPES,
                pkce=pkce,
                state=state,
            ).url()
        )
        code = _code_from(listening.wait(), state)
        token = self._flow.client.exchange(
            code, pkce.verifier, self._settings.redirect_uri, self._flow.clock()
        )
        self._flow.store.save(token)
        return _status(token.expires_at, token.scope)

    def status(self) -> AuthStatus:
        """Report the stored authorization without contacting Spotify."""
        token = self._flow.store.load()
        if token is None:
            return AuthStatus(provider=NAME, authorized=False)
        return _status(token.expires_at, token.scope, not token.expired(self._flow.clock()))

    def logout(self) -> bool:
        """Discard the stored token; True if there was one."""
        return self._flow.store.clear()


def _code_from(callback: Callback, expected: str) -> str:
    if callback.error:
        raise AuthorizationDenied(callback.error)
    if callback.state != expected:
        raise StateMismatch()
    if not callback.code:
        raise AuthorizationDenied("no code in the redirect")
    return callback.code


def _status(expires_at: dt.datetime, scope: str, authorized: bool = True) -> AuthStatus:
    return AuthStatus(
        provider=NAME,
        authorized=authorized,
        expires_at=expires_at,
        scopes=tuple(scope.split()) if scope else (),
    )
