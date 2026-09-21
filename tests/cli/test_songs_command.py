"""`jukebox songs` — and that the MCP surface can do everything it can."""

import pytest
from typer.testing import CliRunner

from jukebox.charts import Chart, Corpus
from jukebox.cli import app, songs
from jukebox.mcp import tools

from tests.support.corpus import write_number_ones, write_ranked

runner = CliRunner()


@pytest.fixture(name="root")
def _root(tmp_path):
    """A workspace root holding a small corpus."""
    corpus = Corpus(tmp_path / "charts")
    write_ranked(corpus, Chart.HOT_100, 1985, (1, "A", "x"), (2, "B", "y"))
    write_number_ones(corpus, Chart.COUNTRY, 1985, ("A", "x", 1, 2))
    return tmp_path


def run(*args: str):
    """Invoke the CLI against a workspace root."""
    return runner.invoke(app, ["songs", *args])


@pytest.fixture(name="built")
def _built(root):
    """The same root with its index built."""
    assert run("build", "--years", "1985", "--root", str(root)).exit_code == 0
    return root


def test_building_reports_what_it_read(root):
    result = run("build", "--years", "1985", "--root", str(root))
    assert result.exit_code == 0
    assert "songs by" in result.stdout


def test_status_before_building_says_what_to_run(root):
    result = run("status", "--root", str(root))
    assert result.exit_code == 1
    assert "songs build" in result.stdout


def test_status_after_building_reports_the_contents(built):
    result = run("status", "--root", str(built))
    assert result.exit_code == 0
    assert "songs" in result.stdout


def test_showing_a_song_prints_its_chart_history(built):
    result = run("show", "--title", "A", "--artist", "x", "--root", str(built))
    assert result.exit_code == 0
    assert "hot-100" in result.stdout
    assert "country" in result.stdout


def test_showing_a_song_the_corpus_lacks_fails_rather_than_printing_nothing(built):
    result = run("show", "--title", "Nope", "--artist", "Nobody", "--root", str(built))
    assert result.exit_code == 1
    assert "no song matching" in result.stdout


def test_an_artist_lists_their_songs(built):
    result = run("artist", "--name", "x", "--root", str(built))
    assert result.exit_code == 0
    assert "1 songs" in result.stdout


def test_an_artist_the_corpus_lacks_fails(built):
    result = run("artist", "--name", "Nobody", "--root", str(built))
    assert result.exit_code == 1
    assert "no artist matching" in result.stdout


def test_a_crossover_prints_songs_on_every_named_chart(built):
    result = run("crossover", "--chart", "hot-100", "--chart", "country", "--root", str(built))
    assert result.exit_code == 0
    assert "1 songs on all of" in result.stdout


def test_a_song_with_no_ranking_prints_without_a_peak(built):
    result = run("crossover", "--chart", "country", "--root", str(built))
    assert result.exit_code == 0
    assert "2w at #1" in result.stdout


def test_every_songs_command_has_a_tool_of_the_same_purpose():
    # The MCP surface must be able to do anything the CLI can: an assistant that
    # can only tell someone to go and run a command ends the conversation.
    commands = {command.name for command in songs.commands.registered_commands}
    assert commands == {"build", "status", "show", "artist", "crossover"}
    for name in ("build_index", "index_status", "find_song", "artist_songs", "crossovers"):
        assert hasattr(tools, name)
