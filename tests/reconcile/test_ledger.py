"""The record of what was written is account state, not project data."""

import datetime as dt

from jukebox.reconcile import Ledger, LedgerEntry

TODAY = dt.date(2026, 9, 7)


def an_entry(*uris: str) -> LedgerEntry:
    """One applied record."""
    return LedgerEntry(spec="S", playlist_id="p1", uris=list(uris), applied=TODAY)


def test_a_spec_never_applied_has_no_record(tmp_path):
    assert Ledger(tmp_path).read("s") is None


def test_a_written_record_reads_back(tmp_path):
    ledger = Ledger(tmp_path)
    ledger.write(an_entry("a", "b"), "s")
    held = ledger.read("s")
    assert held.playlist_id == "p1" and held.uris == ["a", "b"]


def test_the_whole_list_is_kept_not_just_the_playlist_id(tmp_path):
    # Without the list, a hand-added track cannot be told from a dropped one.
    ledger = Ledger(tmp_path)
    ledger.write(an_entry("a", "b", "c"), "s")
    assert len(ledger.read("s").uris) == 3


def test_each_spec_keeps_its_own_record(tmp_path):
    ledger = Ledger(tmp_path)
    ledger.write(an_entry("a"), "one")
    assert ledger.read("two") is None


def test_applying_again_replaces_the_record(tmp_path):
    ledger = Ledger(tmp_path)
    ledger.write(an_entry("a"), "s")
    ledger.write(an_entry("b"), "s")
    assert ledger.read("s").uris == ["b"]


def test_the_directory_is_created_on_demand(tmp_path):
    ledger = Ledger(tmp_path / "deep" / "nested")
    ledger.write(an_entry("a"), "s")
    assert ledger.read("s") is not None
