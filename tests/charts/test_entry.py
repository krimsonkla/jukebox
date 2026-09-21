"""A row carries the fields its kind requires — spec §Design, entry.py."""

import datetime as dt

import pytest

from jukebox.charts import ChartEntry, EntryKind


def test_a_ranked_entry_needs_a_rank():
    with pytest.raises(ValueError, match="rank"):
        ChartEntry(kind=EntryKind.RANKED, title="x", artist="y")


def test_a_number_one_needs_a_date():
    with pytest.raises(ValueError, match="reached"):
        ChartEntry(kind=EntryKind.NUMBER_ONE, title="x", artist="y")


def test_a_ranked_entry_may_not_carry_a_date():
    with pytest.raises(ValueError, match="reached"):
        ChartEntry(
            kind=EntryKind.RANKED, title="x", artist="y", rank=1, reached=dt.date(1985, 1, 5)
        )


def test_a_well_formed_ranked_entry_is_accepted():
    assert ChartEntry(kind=EntryKind.RANKED, title="x", artist="y", rank=3).rank == 3
