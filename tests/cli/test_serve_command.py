"""`jukebox serve mcp` starts the surface, authorized or not."""

import pytest
from typer.testing import CliRunner

from jukebox.cli import app
from jukebox.oauth.errors import NotAuthorized

runner = CliRunner()


@pytest.fixture(name="started")
def _started(monkeypatch, home):
    """A server whose run() is recorded rather than performed."""
    assert home.data  # the isolated home is why this suite never reads real state
    started = {}

    class FakeServer:
        """Records that it was asked to run."""

        def run(self) -> None:
            """Serve."""
            started["ran"] = True

    def build(_workspace, backends):
        started["backends"] = backends
        return FakeServer()

    monkeypatch.setattr("jukebox.cli.serve.build_server", build)
    return started


def test_serving_with_authorization_passes_the_account_through(started, monkeypatch):
    monkeypatch.setenv("JUKEBOX_SPOTIFY_CLIENT_ID", "c" * 32)
    monkeypatch.setattr("jukebox.cli.serve.build_session", object)
    assert runner.invoke(app, ["serve", "mcp"]).exit_code == 0
    assert started["ran"] and started["backends"].playlists is not None


def test_serving_without_authorization_still_starts(started, monkeypatch):
    # The reading tools work from the corpus alone; only the account tools refuse.
    def refuse():
        raise NotAuthorized("spotify")

    monkeypatch.setattr("jukebox.cli.serve.build_session", refuse)
    assert runner.invoke(app, ["serve", "mcp"]).exit_code == 0
    assert started["ran"] and started["backends"].playlists is None
    # Fetching the corpus needs no Spotify, so that backend stays available.
    assert started["backends"].charts is not None
