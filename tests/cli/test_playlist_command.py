"""`jukebox playlist` plans without writing, and confirms before it writes."""

import datetime as dt

import pytest
from typer.testing import CliRunner

from jukebox.charts import Chart, Corpus
from jukebox.cli import app
from jukebox.oauth.errors import NotAuthorized
from jukebox.resolve import Method, Resolution, ResolutionStore
from jukebox.specs import Selection, Spec, SpecStore

from tests.support.corpus import write_ranked

runner = CliRunner()
TODAY = dt.date(2026, 9, 7)


@pytest.fixture(name="workspace")
def _workspace(home, service, monkeypatch):
    write_ranked(
        Corpus(home.charts),
        Chart.HOT_100,
        1985,
        (1, "A", "x"),
        (2, "B", "x"),
    )
    ResolutionStore(home.resolutions).save(
        {
            Resolution.key_for(title, "x"): Resolution(
                key=Resolution.key_for(title, "x"),
                uri=f"u:{title}",
                title=title,
                artist="x",
                method=Method.SEARCH,
                confidence=0.9,
                resolved=TODAY,
            )
            for title in ("A", "B")
        },
    )
    SpecStore(home.specs).save(
        Spec(name="Best of 85", select=Selection(charts=[Chart.HOT_100], years=(1985, 1985)))
    )
    monkeypatch.setattr("jukebox.cli.playlist.build_session", object)
    monkeypatch.setattr("jukebox.cli.playlist.SpotifyPlaylists", lambda _: service)
    return home


@pytest.mark.usefixtures("workspace")
def test_plan_reports_the_change_and_writes_nothing(service):
    result = runner.invoke(app, ["playlist", "plan", "Best of 85"])
    assert result.exit_code == 0, result.output
    assert "new playlist" in result.output and "2 tracks" in result.output
    assert service.writes == []


@pytest.mark.usefixtures("workspace")
def test_apply_asks_before_touching_the_account(service):
    result = runner.invoke(app, ["playlist", "apply", "Best of 85"], input="n\n")
    assert result.exit_code == 0
    assert "nothing written" in result.output
    assert service.writes == []


@pytest.mark.usefixtures("workspace")
def test_apply_writes_when_confirmed(service):
    result = runner.invoke(app, ["playlist", "apply", "Best of 85"], input="y\n")
    assert result.exit_code == 0, result.output
    assert service.writes and service.writes[0][1] == ["u:A", "u:B"]
    assert "open.spotify.com/playlist/" in result.output


@pytest.mark.usefixtures("workspace")
def test_yes_skips_the_question(service):
    result = runner.invoke(app, ["playlist", "apply", "Best of 85", "--yes"])
    assert result.exit_code == 0
    assert service.writes


@pytest.mark.usefixtures("workspace")
def test_applying_an_unchanged_playlist_does_nothing(service):
    runner.invoke(app, ["playlist", "apply", "Best of 85", "--yes"])
    before = len(service.writes)
    result = runner.invoke(app, ["playlist", "apply", "Best of 85", "--yes"])
    assert "nothing to do" in result.output
    assert len(service.writes) == before


@pytest.mark.usefixtures("workspace")
def test_a_manual_addition_is_kept_across_an_apply(service):
    runner.invoke(app, ["playlist", "apply", "Best of 85", "--yes"])
    playlist_id = service.writes[0][0]
    service.playlists[playlist_id].append("u:mine")
    result = runner.invoke(app, ["playlist", "apply", "Best of 85", "--yes"])
    assert "added by hand — kept" in result.output
    assert "u:mine" in service.playlists[playlist_id]


@pytest.mark.usefixtures("workspace")
def test_replacing_manual_additions_must_be_asked_for(service):
    runner.invoke(app, ["playlist", "apply", "Best of 85", "--yes"])
    playlist_id = service.writes[0][0]
    service.playlists[playlist_id].append("u:mine")
    runner.invoke(app, ["playlist", "apply", "Best of 85", "--replace-manual", "--yes"])
    assert "u:mine" not in service.playlists[playlist_id]


@pytest.mark.usefixtures("workspace")
def test_an_unknown_spec_lists_what_exists():
    result = runner.invoke(app, ["playlist", "plan", "nope"])
    assert result.exit_code == 1 and "best-of-85" in result.output


@pytest.mark.usefixtures("workspace")
def test_nothing_resolved_says_to_run_the_backfill(home):
    ResolutionStore(home.resolutions).path.unlink()
    result = runner.invoke(app, ["playlist", "plan", "Best of 85"])
    assert result.exit_code == 1 and "resolve backfill" in result.output


@pytest.mark.usefixtures("workspace")
def test_without_authorization_it_says_how_to_get_it(monkeypatch):
    def refuse():
        raise NotAuthorized("spotify")

    monkeypatch.setattr("jukebox.cli.playlist.build_session", refuse)
    result = runner.invoke(app, ["playlist", "plan", "Best of 85"])
    assert result.exit_code == 1 and "auth login" in result.output
