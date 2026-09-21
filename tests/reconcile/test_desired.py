"""A tracklist becomes URIs, and says which entries have none."""

import datetime as dt

from jukebox.charts import Chart, ChartEntry, EntryKind
from jukebox.reconcile import Desired
from jukebox.resolve import Method, Resolution, ResolutionStore
from jukebox.specs import Ordering, Selected, Tracklist

TODAY = dt.date(2026, 9, 7)


def selected(rank: int, title: str, artist: str) -> Selected:
    """A selected chart entry."""
    return Selected(
        chart=Chart.HOT_100,
        year=1985,
        entry=ChartEntry(kind=EntryKind.RANKED, rank=rank, title=title, artist=artist),
    )


def store_with(tmp_path, *pairs) -> ResolutionStore:
    """A resolution store holding these (title, artist, uri) answers."""
    store = ResolutionStore(tmp_path)
    store.save(
        {
            Resolution.key_for(title, artist): Resolution(
                key=Resolution.key_for(title, artist),
                uri=uri,
                title=title,
                artist=artist,
                method=Method.SEARCH,
                confidence=0.9,
                resolved=TODAY,
            )
            for title, artist, uri in pairs
        },
    )
    return store


def a_tracklist(*entries: Selected) -> Tracklist:
    """A tracklist over these entries."""
    return Tracklist(name="s", entries=entries, considered=len(entries), dropped_to_cap=0)


def test_entries_become_uris_in_tracklist_order(tmp_path):
    store = store_with(tmp_path, ("A", "x", "u:a"), ("B", "y", "u:b"))
    uris, missing = Desired(store).uris(a_tracklist(selected(1, "A", "x"), selected(2, "B", "y")))
    assert uris == ["u:a", "u:b"] and not missing


def test_an_unresolved_entry_is_reported_rather_than_dropped(tmp_path):
    store = store_with(tmp_path, ("A", "x", "u:a"))
    uris, missing = Desired(store).uris(a_tracklist(selected(1, "A", "x"), selected(2, "B", "y")))
    assert uris == ["u:a"]
    assert [entry.title for entry in missing] == ["B"]


def test_the_same_track_selected_twice_appears_once(tmp_path):
    # A song can chart on two charts, or as a double A-side; a playlist should
    # not hold it twice.
    store = store_with(tmp_path, ("A", "x", "u:a"))
    uris, _ = Desired(store).uris(a_tracklist(selected(1, "A", "x"), selected(2, "A", "x")))
    assert uris == ["u:a"]


def test_nothing_resolved_yields_nothing(tmp_path):
    uris, missing = Desired(ResolutionStore(tmp_path)).uris(a_tracklist(selected(1, "A", "x")))
    assert not uris and len(missing) == 1


def released(key: str, uri: str, when, title: str = "t") -> Resolution:
    """A resolution carrying the date the catalogue gave, or none."""
    return Resolution(
        key=key,
        uri=uri,
        title=title,
        artist="a",
        method=Method.SEARCH,
        confidence=0.9,
        resolved=dt.date(2026, 9, 7),
        released=when,
    )


def charted(title: str) -> Selected:
    """One selected year-end row."""
    return Selected(
        chart=Chart.HOT_100,
        year=1985,
        entry=ChartEntry(kind=EntryKind.RANKED, title=title, artist="a", rank=1),
    )


def tracklist_of(order: Ordering, *titles: str) -> Tracklist:
    """A tracklist in the order the shaper would have left it."""
    return Tracklist(
        name="A List",
        entries=tuple(charted(title) for title in titles),
        considered=len(titles),
        dropped_to_cap=0,
        order=order,
    )


def store_of(tmp_path, *rows: Resolution) -> ResolutionStore:
    """A resolution cache holding these answers, dates and all."""
    store = ResolutionStore(tmp_path / "resolutions")
    store.save({row.key: row for row in rows})
    return store


def test_a_release_ordering_sequences_by_the_date_the_catalogue_gave(tmp_path):
    # The chart says when a song was popular and never when it came out, so this
    # order can only be settled once the catalogue has answered.
    store = store_of(
        tmp_path,
        released(Resolution.key_for("late", "a"), "u:late", dt.date(1985, 11, 1)),
        released(Resolution.key_for("early", "a"), "u:early", dt.date(1983, 2, 1)),
        released(Resolution.key_for("middle", "a"), "u:middle", dt.date(1984, 6, 1)),
    )
    uris, _ = Desired(store).uris(tracklist_of(Ordering.RELEASE, "late", "early", "middle"))
    assert uris == ["u:early", "u:middle", "u:late"]


def test_any_other_ordering_keeps_the_sequence_the_shaper_chose(tmp_path):
    store = store_of(
        tmp_path,
        released(Resolution.key_for("late", "a"), "u:late", dt.date(1985, 11, 1)),
        released(Resolution.key_for("early", "a"), "u:early", dt.date(1983, 2, 1)),
    )
    uris, _ = Desired(store).uris(tracklist_of(Ordering.YEAR, "late", "early"))
    assert uris == ["u:late", "u:early"]


def test_a_recording_the_catalogue_did_not_date_sorts_last(tmp_path):
    # Sorting a missing date as the start of time would put the least-known
    # recordings at the front, which is the opposite of what was asked for.
    store = store_of(
        tmp_path,
        released(Resolution.key_for("undated", "a"), "u:undated", None),
        released(Resolution.key_for("dated", "a"), "u:dated", dt.date(1990, 1, 1)),
    )
    uris, _ = Desired(store).uris(tracklist_of(Ordering.RELEASE, "undated", "dated"))
    assert uris == ["u:dated", "u:undated"]


def test_an_unresolved_entry_is_still_reported_when_ordering_by_release(tmp_path):
    store = store_of(
        tmp_path, released(Resolution.key_for("known", "a"), "u:known", dt.date(1985, 1, 1))
    )
    uris, missing = Desired(store).uris(tracklist_of(Ordering.RELEASE, "known", "unknown"))
    assert uris == ["u:known"]
    assert [entry.title for entry in missing] == ["unknown"]
