"""Fixtures shared by the suite: the committed Wikipedia pages, and a fake account."""

import os
import pathlib

import pytest

from jukebox.paths import Paths

from tests.support.playlists import FakePlaylists

PAGES = pathlib.Path(__file__).parent / "fixtures" / "pages"


def _page(name: str) -> str:
    return (PAGES / f"{name}.html").read_text(encoding="utf-8")


@pytest.fixture(name="home")
def _home(tmp_path, monkeypatch) -> Paths:
    """A jukebox home of its own, so a test never reads or writes the real one."""
    monkeypatch.setenv("JUKEBOX_HOME", str(tmp_path))
    monkeypatch.chdir(tmp_path)
    # A suite that reads the developer's ambient configuration passes on their
    # machine and nowhere else, which is exactly what it must not do.
    for leaked in [name for name in os.environ if name.startswith("JUKEBOX_SPOTIFY_")]:
        monkeypatch.delenv(leaked, raising=False)
    return Paths.resolve()


@pytest.fixture(name="service")
def _service() -> FakePlaylists:
    """A playlist service that records writes instead of making them."""
    return FakePlaylists()


@pytest.fixture
def hot100_1985() -> str:
    """Shape A: year-end ranked, 100 entries."""
    return _page("hot100-1985")


@pytest.fixture
def rnb_1985() -> str:
    """Shape A under the era name Hot Black Singles."""
    return _page("rnb-1985")


@pytest.fixture
def country_1985() -> str:
    """Shape B: number ones per year, with sortname and dts templates."""
    return _page("country-1985")


@pytest.fixture
def dance_1985() -> str:
    """Shape B carrying two charts under a two-level header, with rowspans."""
    return _page("dance-1985")


@pytest.fixture
def modernrock_1990s() -> str:
    """Shape C: number ones for a whole decade, dated, straddling 1989."""
    return _page("modernrock-1990s")


@pytest.fixture
def mainstreamrock_1990s() -> str:
    """A decade of number ones separated by year banner rows, with a weeks column."""
    return _page("mainstreamrock-1990s")
