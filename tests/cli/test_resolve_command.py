"""`jukebox resolve` composes the module and reports honestly."""

import datetime as dt

import pytest
from typer.testing import CliRunner

from jukebox.charts import Chart, ChartEntry, ChartFile, Corpus, EntryKind
from jukebox.cli import app
from jukebox.oauth.errors import NotAuthorized
from jukebox.ports import TrackMatch

runner = CliRunner()
TODAY = dt.date(2026, 9, 7)


class EmptyCatalog:
    """Answers nothing, and records what it was asked."""

    def __init__(self) -> None:
        self.searched: list[tuple[str, str]] = []

    def search(self, title: str, artist: str) -> list[TrackMatch]:
        """Nothing at all."""
        self.searched.append((title, artist))
        return []

    def by_isrc(self, _isrc: str) -> list[TrackMatch]:
        """Nothing."""
        return []


class OneHitCatalog:
    """Answers every search with the song it was asked for, and records the asking."""

    def __init__(self) -> None:
        self.searched: list[tuple[str, str]] = []

    def search(self, title: str, artist: str) -> list[TrackMatch]:
        """A perfect match."""
        self.searched.append((title, artist))
        return [TrackMatch(uri="spotify:track:1", title=title, artist=artist)]

    def by_isrc(self, _isrc: str) -> list[TrackMatch]:
        """Nothing."""
        return []


@pytest.fixture(name="corpus_dir")
def _corpus_dir(home):
    Corpus(home.charts).write(
        ChartFile(
            chart=Chart.HOT_100,
            year=1985,
            kind=EntryKind.RANKED,
            source="s",
            retrieved=TODAY,
            entries=[ChartEntry(kind=EntryKind.RANKED, title="Take On Me", artist="a-ha", rank=1)],
        )
    )
    return home


@pytest.mark.usefixtures("corpus_dir")
def test_backfill_resolves_and_reports(monkeypatch):
    monkeypatch.setattr("jukebox.cli.resolve.SpotifyCatalog", lambda _: OneHitCatalog())
    monkeypatch.setattr("jukebox.cli.resolve.build_session", object)
    result = runner.invoke(app, ["resolve", "backfill", "--year", "1985", "--chart", "hot-100"])
    assert result.exit_code == 0, result.output
    assert "1/1" in result.output and "100%" in result.output


@pytest.mark.usefixtures("corpus_dir")
def test_a_chart_with_no_corpus_is_skipped_silently(monkeypatch):
    monkeypatch.setattr("jukebox.cli.resolve.SpotifyCatalog", lambda _: OneHitCatalog())
    monkeypatch.setattr("jukebox.cli.resolve.build_session", object)
    result = runner.invoke(app, ["resolve", "backfill", "--year", "1985"])
    assert result.exit_code == 0
    assert "country" not in result.output


@pytest.mark.usefixtures("corpus_dir")
def test_without_authorization_it_says_how_to_get_it(monkeypatch):
    def refuse():
        raise NotAuthorized("spotify")

    monkeypatch.setattr("jukebox.cli.resolve.build_session", refuse)
    result = runner.invoke(app, ["resolve", "backfill", "--year", "1985"])
    assert result.exit_code == 1
    assert "auth login" in result.output


@pytest.mark.usefixtures("corpus_dir")
def test_isrc_lookup_is_off_unless_asked_for(monkeypatch):
    built = []
    monkeypatch.setattr("jukebox.cli.resolve.SpotifyCatalog", lambda _: OneHitCatalog())
    monkeypatch.setattr("jukebox.cli.resolve.build_session", object)
    monkeypatch.setattr(
        "jukebox.cli.resolve.MusicBrainzIsrcs", lambda: built.append("built") or object()
    )
    runner.invoke(app, ["resolve", "backfill", "--year", "1985", "--chart", "hot-100"])
    assert not built
    runner.invoke(app, ["resolve", "backfill", "--year", "1985", "--chart", "hot-100", "--isrc"])
    assert built == ["built"]


@pytest.mark.usefixtures("corpus_dir")
def test_narrowing_applies_before_a_lookup_is_spent(monkeypatch):
    # Resolving a whole chart to serve a spec that takes its top rows pays for
    # rows nobody asked about, and each is a request against a rate limit.
    catalog = OneHitCatalog()
    monkeypatch.setattr("jukebox.cli.resolve.SpotifyCatalog", lambda _: catalog)
    monkeypatch.setattr("jukebox.cli.resolve.build_session", object)
    runner.invoke(
        app,
        ["resolve", "backfill", "--year", "1985", "--chart", "hot-100", "--narrow", "max_rank=1"],
    )
    assert len(catalog.searched) == 1


@pytest.mark.usefixtures("corpus_dir")
def test_a_measure_the_charts_do_not_publish_is_refused(monkeypatch):
    monkeypatch.setattr("jukebox.cli.resolve.SpotifyCatalog", lambda _: OneHitCatalog())
    monkeypatch.setattr("jukebox.cli.resolve.build_session", object)
    result = runner.invoke(
        app,
        ["resolve", "backfill", "--year", "1985", "--chart", "hot-100", "--narrow", "popular=1"],
    )
    assert result.exit_code != 0


@pytest.mark.usefixtures("corpus_dir")
def test_retry_asks_again_for_what_backfill_did_not_find(monkeypatch):
    empty = EmptyCatalog()
    monkeypatch.setattr("jukebox.cli.resolve.SpotifyCatalog", lambda _: empty)
    monkeypatch.setattr("jukebox.cli.resolve.build_session", object)
    runner.invoke(app, ["resolve", "backfill", "--year", "1985", "--chart", "hot-100"])
    spent = len(empty.searched)
    runner.invoke(app, ["resolve", "backfill", "--year", "1985", "--chart", "hot-100"])
    assert len(empty.searched) == spent, "a known failure is not paid for twice"
    runner.invoke(app, ["resolve", "retry", "--year", "1985", "--chart", "hot-100"])
    assert len(empty.searched) == spent * 2


@pytest.mark.usefixtures("corpus_dir")
def test_a_skipped_failure_is_reported_rather_than_silently_cheap(monkeypatch):
    monkeypatch.setattr("jukebox.cli.resolve.SpotifyCatalog", lambda _: EmptyCatalog())
    monkeypatch.setattr("jukebox.cli.resolve.build_session", object)
    runner.invoke(app, ["resolve", "backfill", "--year", "1985", "--chart", "hot-100"])
    again = runner.invoke(app, ["resolve", "backfill", "--year", "1985", "--chart", "hot-100"])
    assert "already known missing" in again.stdout
