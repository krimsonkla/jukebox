"""`jukebox auth` reports through the port, never through a vendor's flow."""

import datetime as dt

import pytest
from typer.testing import CliRunner

from jukebox.cli import app
from jukebox.oauth import AuthorizationDenied
from jukebox.ports import AuthStatus
from jukebox.providers.spotify import MissingClientId

runner = CliRunner()
NOW = dt.datetime(2026, 9, 7, 12, 0, tzinfo=dt.UTC)


class FakeAuth:
    """A provider that answers without leaving the machine."""

    name = "spotify"

    def __init__(self, status: AuthStatus, stored: bool = True, refuse=None) -> None:
        self._status, self._stored, self._refuse = status, stored, refuse

    def login(self) -> AuthStatus:
        """Authorize, or refuse the way the real adapter would."""
        if self._refuse:
            raise self._refuse
        return self._status

    def status(self) -> AuthStatus:
        """The stored authorization."""
        return self._status

    def logout(self) -> bool:
        """Whether anything was stored."""
        return self._stored


@pytest.fixture(name="install")
def _install(monkeypatch):
    def use(service):
        monkeypatch.setattr("jukebox.cli.auth.build_auth", lambda _: service)

    return use


AUTHORIZED = AuthStatus(provider="spotify", authorized=True, expires_at=NOW, scopes=("a", "b"))
UNAUTHORIZED = AuthStatus(provider="spotify", authorized=False)


def test_status_reports_an_authorization_with_its_scopes(install):
    install(FakeAuth(AUTHORIZED))
    result = runner.invoke(app, ["auth", "status"])
    assert result.exit_code == 0
    assert "authorized until 2026-09-07 12:00 UTC" in result.output
    assert "a, b" in result.output


def test_status_without_one_says_how_to_get_one(install):
    install(FakeAuth(UNAUTHORIZED))
    result = runner.invoke(app, ["auth", "status"])
    assert result.exit_code == 0
    assert "auth login" in result.output


def test_login_tells_the_user_to_look_at_the_browser(install):
    install(FakeAuth(AUTHORIZED))
    result = runner.invoke(app, ["auth", "login"])
    assert result.exit_code == 0
    assert "browser" in result.output


def test_a_refused_login_exits_non_zero_with_its_advice(install):
    install(FakeAuth(AUTHORIZED, refuse=AuthorizationDenied("access_denied")))
    result = runner.invoke(app, ["auth", "login"])
    assert result.exit_code == 1
    assert "redirect URI" in result.output


def test_logout_says_whether_there_was_anything(install):
    install(FakeAuth(AUTHORIZED, stored=True))
    assert "forgotten" in runner.invoke(app, ["auth", "logout"]).output
    install(FakeAuth(AUTHORIZED, stored=False))
    assert "nothing stored" in runner.invoke(app, ["auth", "logout"]).output


def test_an_unknown_provider_is_a_bad_parameter():
    result = runner.invoke(app, ["auth", "status", "--provider", "8-track"])
    assert result.exit_code != 0


def test_a_provider_that_cannot_be_built_reports_its_advice(monkeypatch):
    def refuse(_):
        raise MissingClientId()

    monkeypatch.setattr("jukebox.cli.auth.build_auth", refuse)
    result = runner.invoke(app, ["auth", "status"])
    assert result.exit_code != 0
    assert "developer.spotify.com" in result.output
