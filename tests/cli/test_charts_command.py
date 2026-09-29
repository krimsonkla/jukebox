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


def test_a_discography_is_read_into_the_corpus(tmp_path):
    result = runner.invoke(
        app,
        [
            "charts",
            "discography",
            "--artist",
            "A Fictional Act",
            "--years",
            "1980-1999",
            "--source",
            "fixture",
            "--out",
            str(tmp_path),
        ],
    )
    assert result.exit_code == 0, result.output
    assert "4 placings, 4 new" in result.output
    assert "mainstream-rock 3" in result.output
    written = json.loads((tmp_path / "mainstream-rock" / "1985.json").read_text())
    assert [entry["title"] for entry in written["entries"]] == [
        "The Loud One",
        "The Promo",
        "The Quiet One",
    ]
    assert written["sources"] == [
        {"title": "A Fictional Act discography", "retrieved": written["sources"][0]["retrieved"]}
    ]


def test_an_act_with_no_article_is_named_and_the_rest_are_still_read(tmp_path):
    result = runner.invoke(
        app,
        [
            "charts",
            "discography",
            "--artist",
            "Nobody At All",
            "--artist",
            "A Fictional Act",
            "--years",
            "1980-1999",
            "--source",
            "fixture",
            "--out",
            str(tmp_path),
        ],
    )
    assert result.exit_code == 0, result.output
    assert "Nobody At All: no article at Nobody At All discography" in result.output
    assert "A Fictional Act: 4 placings" in result.output
