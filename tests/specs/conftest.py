"""A corpus built in a temporary directory, one chart at a time."""

import pytest

from jukebox.charts import Corpus

from tests.support.corpus import write_number_ones, write_ranked


@pytest.fixture(name="corpus")
def _corpus(tmp_path) -> Corpus:
    return Corpus(tmp_path / "charts")


@pytest.fixture(name="ranked")
def _ranked(corpus):
    def write(chart, year, *rows) -> None:
        write_ranked(corpus, chart, year, *rows)

    return write


@pytest.fixture(name="number_ones")
def _number_ones(corpus):
    def write(chart, year, *rows) -> None:
        write_number_ones(corpus, chart, year, *rows)

    return write
