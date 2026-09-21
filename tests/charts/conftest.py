"""Fixtures local to the charts suite."""

import pathlib

import pytest

from jukebox.charts import FixtureSource


@pytest.fixture(name="fixture_source")
def _fixture_source() -> FixtureSource:
    return FixtureSource(pathlib.Path(__file__).parent.parent / "fixtures" / "pages")
