"""Resolutions are vendored: slow to compute, corrected by hand, committed."""

import datetime as dt
import json

from jukebox.resolve import Method, Resolution, ResolutionStore

TODAY = dt.date(2026, 9, 7)


def a_resolution(key: str) -> Resolution:
    """One stored answer."""
    return Resolution(
        key=key,
        uri=f"spotify:track:{key}",
        title="t",
        artist="a",
        method=Method.SEARCH,
        confidence=0.9,
        resolved=TODAY,
    )


def test_nothing_stored_reads_as_nothing(tmp_path):
    assert ResolutionStore(tmp_path).load() == {}


def test_a_saved_resolution_reads_back(tmp_path):
    store = ResolutionStore(tmp_path)
    store.save({"k": a_resolution("k")})
    assert store.load()["k"].uri == "spotify:track:k"


def test_rows_are_written_in_key_order_so_a_rerun_diffs_as_content(tmp_path):
    store = ResolutionStore(tmp_path)
    store.save({"b": a_resolution("b"), "a": a_resolution("a")})
    written = json.loads(store.path.read_text())
    assert [row["key"] for row in written] == ["a", "b"]


def test_writing_twice_produces_identical_bytes(tmp_path):
    store = ResolutionStore(tmp_path)
    rows = {"a": a_resolution("a")}
    store.save(rows)
    first = store.path.read_bytes()
    store.save(rows)
    assert store.path.read_bytes() == first


def test_one_answer_serves_every_chart_that_carried_the_song(tmp_path):
    # A recording that charted on four lists is one lookup and one answer; a
    # chart year is not a boundary the cache can see past.
    store = ResolutionStore(tmp_path)
    store.save({"a": a_resolution("a")})
    assert store.load()["a"].uri == "spotify:track:a"


def test_a_key_survives_a_corpus_refetch_that_respells_the_row():
    # The key is the song's identity, so an editor fixing punctuation does not
    # orphan the answer and make it be paid for again.
    assert Resolution.key_for("Take On Me", "a-ha") == Resolution.key_for("Take on Me!", "A-ha")
    assert Resolution.key_for("A", "b") != Resolution.key_for("B", "a")


def test_two_billings_of_one_recording_share_a_key():
    # Charts credit guests differently week to week; the lead is what they agree
    # on, and two searches for one recording is the waste this key exists to end.
    assert Resolution.key_for("Gangsta's Paradise", "Coolio") == Resolution.key_for(
        "Gangsta's Paradise", "Coolio featuring L.V."
    )
