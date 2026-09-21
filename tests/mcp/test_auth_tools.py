"""Authorizing from the conversation, rather than sending someone to a shell."""

import datetime as dt

import pytest

from jukebox.mcp import tools
from jukebox.mcp.tools import auth_login, auth_status
from jukebox.oauth import AuthorizationDenied
from jukebox.ports import AuthStatus

NOW = dt.datetime(2026, 9, 7, 12, 0, tzinfo=dt.UTC)


class FakeAuth:
    """An authorizer that answers without opening a browser."""

    name = "spotify"

    def __init__(self, status: AuthStatus, refuse=None) -> None:
        self._status, self._refuse = status, refuse
        self.logins = 0

    def login(self) -> AuthStatus:
        """Consent, or refuse the way the real flow would."""
        self.logins += 1
        if self._refuse:
            raise self._refuse
        return self._status

    def status(self) -> AuthStatus:
        """The stored authorization."""
        return self._status

    def logout(self) -> bool:
        """Unused by this surface."""
        raise AssertionError("the MCP surface must not discard a credential")


AUTHORIZED = AuthStatus(
    provider="spotify", authorized=True, expires_at=NOW, scopes=("playlist-modify-private",)
)
UNAUTHORIZED = AuthStatus(provider="spotify", authorized=False)


def test_status_reports_an_authorization_with_its_scopes():
    found = auth_status(FakeAuth(AUTHORIZED))
    assert found["authorized"] is True
    assert found["scopes"] == ["playlist-modify-private"]
    assert found["expires_at"].startswith("2026-09-07")


def test_status_without_one_says_so_and_carries_no_expiry():
    found = auth_status(FakeAuth(UNAUTHORIZED))
    assert found["authorized"] is False and found["expires_at"] is None


def test_logging_in_returns_the_authorization_it_obtained():
    service = FakeAuth(AUTHORIZED)
    assert auth_login(service)["authorized"] is True
    assert service.logins == 1


def test_a_refused_login_carries_its_advice():
    with pytest.raises(AuthorizationDenied, match="redirect URI"):
        auth_login(FakeAuth(AUTHORIZED, refuse=AuthorizationDenied("access_denied")))


def test_the_surface_offers_no_way_to_discard_a_credential():
    assert not [name for name in tools.__all__ if "logout" in name]
