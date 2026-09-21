"""A workspace on disk with a small corpus, and a fake account."""

import datetime as dt

import pytest

from jukebox.charts import Chart, Corpus
from jukebox.mcp import Workspace
from jukebox.resolve import Method, Resolution, ResolutionStore

from tests.support.corpus import write_number_ones, write_ranked

TODAY = dt.date(2026, 9, 7)


@pytest.fixture(name="workspace")
def _workspace(tmp_path) -> Workspace:
    corpus = Corpus(tmp_path / "charts")
    write_ranked(corpus, Chart.HOT_100, 1985, (1, "A", "x"), (2, "B", "y"), (3, "C", "x"))
    write_number_ones(corpus, Chart.COUNTRY, 1985, ("D", "z", 1, 2))
    ResolutionStore(tmp_path / "resolutions").save(
        {
            Resolution.key_for(title, artist): Resolution(
                key=Resolution.key_for(title, artist),
                uri=f"u:{title}",
                title=title,
                artist=artist,
                method=Method.SEARCH,
                confidence=0.9,
                resolved=TODAY,
            )
            for title, artist in (("A", "x"), ("B", "y"), ("C", "x"))
        },
    )
    return Workspace.here(tmp_path)


@pytest.fixture(name="unresolved")
def _unresolved(workspace) -> Workspace:
    """The same workspace with nothing matched yet, so a lookup is needed."""
    for path in workspace.resolutions.path.parent.glob("*.json"):
        path.unlink()
    return workspace
