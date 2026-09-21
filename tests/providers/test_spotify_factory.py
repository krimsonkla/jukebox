"""The adapter is wired from settings alone — no caller assembles it by hand."""

import datetime as dt

import pytest

from jukebox.oauth import NotAuthorized, Token, TokenStore
from jukebox.providers.registry import build_auth as build_by_name
from jukebox.providers.spotify.factory import _clock
from jukebox.providers.spotify import (
    MissingClientId,
    SpotifySettings,
    build_auth,
    build_session,
)


@pytest.fixture(name="settings")
def _settings(tmp_path) -> SpotifySettings:
    return SpotifySettings(client_id="cid", state_dir=tmp_path)


def test_build_auth_produces_a_working_authorizer(settings):
    service = build_auth(settings)
    assert service.name == "spotify"
    assert service.status().authorized is False


def test_build_session_reads_the_same_store_the_authorizer_writes(settings):
    TokenStore(settings.state_dir, "spotify").save(
        Token(
            access_token="live",
            refresh_token="r",
            expires_at=dt.datetime.now(dt.UTC) + dt.timedelta(hours=1),
        )
    )
    assert build_session(settings).bearer() == "live"


def test_a_session_without_a_stored_token_says_to_log_in(settings):
    with pytest.raises(NotAuthorized, match="auth login"):
        build_session(settings).bearer()


def test_a_session_needs_a_client_id_too(tmp_path):
    with pytest.raises(MissingClientId):
        build_session(SpotifySettings(client_id="", state_dir=tmp_path))


def test_the_registry_builds_the_named_provider(monkeypatch, tmp_path):
    monkeypatch.setenv("JUKEBOX_SPOTIFY_CLIENT_ID", "cid")
    monkeypatch.setenv("JUKEBOX_SPOTIFY_STATE_DIR", str(tmp_path))
    assert build_by_name("spotify").name == "spotify"


def test_the_default_clock_is_utc():
    # A naive local clock would compare against a UTC expiry and mis-report status.
    assert _clock().tzinfo is dt.UTC
