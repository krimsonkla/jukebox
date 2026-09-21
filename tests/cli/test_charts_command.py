"""The command composes the module — spec §AC 1, 5."""

import json

from typer.testing import CliRunner

from jukebox.cli import app

runner = CliRunner()


def test_fetch_writes_the_corpus_and_reports_gaps(tmp_path):
    result = runner.invoke(
        app,
        ["charts", "fetch", "--year", "1985", "--source", "fixture", "--out", str(tmp_path)],
    )
    assert result.exit_code == 0, result.output
    written = json.loads((tmp_path / "hot-100" / "1985.json").read_text())
    assert len(written["entries"]) == 100
    assert "modern-rock" in result.output
    assert "did not exist" in result.output


def test_a_missing_page_fails_loudly(tmp_path):
    result = runner.invoke(
        app,
        ["charts", "fetch", "--year", "1986", "--source", "fixture", "--out", str(tmp_path)],
    )
    assert result.exit_code != 0
