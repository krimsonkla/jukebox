"""`jukebox spec` writes a description and previews what it selects."""

import pytest
import yaml
from typer.testing import CliRunner

from jukebox.charts import Chart, Corpus
from jukebox.cli import app

from tests.support.corpus import write_ranked

runner = CliRunner()


@pytest.fixture(name="workspace")
def _workspace(home):
    write_ranked(
        Corpus(home.charts),
        Chart.HOT_100,
        1985,
        (1, "Careless Whisper", "George Michael"),
        (2, "Like a Virgin", "Madonna"),
    )
    return home


def add_one(*extra) -> object:
    """Add a spec over the fixture corpus."""
    return runner.invoke(
        app,
        ["spec", "add", "Best of 85", "--chart", "hot-100", "--years", "1985", *extra],
    )


@pytest.mark.usefixtures("workspace")
def test_adding_a_spec_writes_it_and_previews_the_selection(home):
    result = add_one()
    assert result.exit_code == 0, result.output
    assert (home.specs / "best-of-85.yaml").exists()
    assert "Careless Whisper" in result.output
    assert "2 tracks" in result.output


@pytest.mark.usefixtures("workspace")
def test_the_written_spec_names_no_music_service(home):
    add_one()
    body = (home.specs / "best-of-85.yaml").read_text()
    assert "spotify" not in body.lower()
    assert yaml.safe_load(body)["select"]["charts"] == ["hot-100"]


@pytest.mark.usefixtures("workspace")
def test_shaping_a_stored_spec_records_only_what_was_asked_for(home):
    add_one()
    result = runner.invoke(
        app, ["spec", "shape", "Best of 85", "--size", "1", "--max-per-artist", "1"]
    )
    assert result.exit_code == 0, result.output
    body = yaml.safe_load((home.specs / "best-of-85.yaml").read_text())
    assert body["shape"] == {"size": 1, "max_per_artist": 1}
    assert "1 tracks" in result.output


@pytest.mark.usefixtures("workspace")
def test_shaping_leaves_the_selection_alone(home):
    add_one("--max-rank", "1")
    runner.invoke(app, ["spec", "shape", "Best of 85", "--order", "year"])
    body = yaml.safe_load((home.specs / "best-of-85.yaml").read_text())
    assert body["select"]["max_rank"] == 1
    assert body["shape"]["order"] == "year"


@pytest.mark.usefixtures("workspace")
def test_shaping_a_spec_that_does_not_exist_is_refused():
    assert runner.invoke(app, ["spec", "shape", "nope", "--size", "1"]).exit_code == 1


@pytest.mark.usefixtures("workspace")
def test_a_year_span_is_read_as_first_and_last(home):
    runner.invoke(app, ["spec", "add", "Decade", "--chart", "hot-100", "--years", "1980-1989"])
    body = yaml.safe_load((home.specs / "decade.yaml").read_text())
    assert body["select"]["years"] == [1980, 1989]


@pytest.mark.usefixtures("workspace")
def test_unreadable_years_say_how_to_write_them():
    result = runner.invoke(
        app, ["spec", "add", "Bad", "--chart", "hot-100", "--years", "the eighties"]
    )
    assert result.exit_code == 1
    assert "1980-1989" in result.output


@pytest.mark.usefixtures("workspace")
def test_previewing_a_stored_spec_repeats_the_selection():
    add_one()
    result = runner.invoke(app, ["spec", "preview", "Best of 85"])
    assert result.exit_code == 0
    assert "Careless Whisper" in result.output


@pytest.mark.usefixtures("workspace")
def test_previewing_an_unknown_spec_lists_what_exists():
    add_one()
    result = runner.invoke(app, ["spec", "preview", "nope"])
    assert result.exit_code == 1
    assert "best-of-85" in result.output


@pytest.mark.usefixtures("workspace")
def test_a_spec_selecting_nothing_says_how_to_widen_it():
    result = runner.invoke(app, ["spec", "add", "Empty", "--chart", "latin", "--years", "1985"])
    assert result.exit_code == 1
    assert "charts fetch" in result.output


@pytest.mark.usefixtures("workspace")
def test_listing_shows_stored_specs():
    add_one()
    assert "best-of-85" in runner.invoke(app, ["spec", "list"]).output


@pytest.mark.usefixtures("workspace")
def test_listing_an_empty_workspace_says_so():
    assert "no specs yet" in runner.invoke(app, ["spec", "list"]).output
