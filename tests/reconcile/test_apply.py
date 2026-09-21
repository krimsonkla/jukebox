"""Planning touches nothing; writing is the only thing that does."""

import datetime as dt

import pytest

from jukebox.charts import Chart, ChartEntry, EntryKind
from jukebox.reconcile import Apply, Desired, Ledger, LedgerEntry, NothingResolved, PlaylistGone
from jukebox.resolve import Method, Resolution, ResolutionStore
from jukebox.specs import Selected, Selection, Spec, Tracklist

from tests.support.playlists import FakePlaylists

TODAY = dt.date(2026, 9, 7)


def a_spec() -> Spec:
    """A spec over the 1985 Hot 100."""
    return Spec(name="Best of 85", select=Selection(charts=[Chart.HOT_100], years=(1985, 1985)))


def tracklist_of(*titles: str) -> Tracklist:
    """A tracklist over these songs, all by one artist."""
    entries = tuple(
        Selected(
            chart=Chart.HOT_100,
            year=1985,
            entry=ChartEntry(kind=EntryKind.RANKED, rank=index + 1, title=title, artist="x"),
        )
        for index, title in enumerate(titles)
    )
    return Tracklist(name="Best of 85", entries=entries, considered=len(entries), dropped_to_cap=0)


def _resolutions(tmp_path) -> ResolutionStore:
    """A store answering every title the tracklist helper produces."""
    store = ResolutionStore(tmp_path / "resolutions")
    store.save(
        {
            Resolution.key_for(title, "x"): Resolution(
                key=Resolution.key_for(title, "x"),
                uri=f"u:{title}",
                title=title,
                artist="x",
                method=Method.SEARCH,
                confidence=0.9,
                resolved=TODAY,
            )
            for title in ("A", "B", "C")
        },
    )
    return store


@pytest.fixture(name="applier")
def _applier(tmp_path, service):
    store = ResolutionStore(tmp_path / "resolutions")
    store.save(
        {
            Resolution.key_for(title, "x"): Resolution(
                key=Resolution.key_for(title, "x"),
                uri=f"u:{title}",
                title=title,
                artist="x",
                method=Method.SEARCH,
                confidence=0.9,
                resolved=TODAY,
            )
            for title in ("A", "B", "C")
        },
    )
    ledger = Ledger(tmp_path / "ledger")
    return Apply(service, ledger, Desired(store), lambda: TODAY), ledger


def test_planning_writes_nothing(applier, service):
    made = applier[0].plan(a_spec(), tracklist_of("A", "B"))
    assert made.creates and made.final == ("u:A", "u:B")
    assert service.writes == [] and service.created == []


def test_a_first_apply_creates_the_playlist_and_records_it(applier, service):
    apply, ledger = applier
    spec = a_spec()
    made = apply.plan(spec, tracklist_of("A", "B"))
    playlist_id = apply.write(spec, made)

    assert service.created == ["Best of 85"]
    assert service.playlists[playlist_id] == ["u:A", "u:B"]
    assert ledger.read(spec.slug()).uris == ["u:A", "u:B"]
    assert ledger.read(spec.slug()).playlist_id == playlist_id


def test_a_second_apply_reuses_the_same_playlist(applier, service):
    apply, _ = applier
    spec = a_spec()
    first = apply.write(spec, apply.plan(spec, tracklist_of("A")))
    second = apply.write(spec, apply.plan(spec, tracklist_of("A", "B")))
    assert first == second
    assert len(service.created) == 1
    assert service.playlists[second] == ["u:A", "u:B"]


def test_a_track_added_by_hand_survives_the_next_apply(applier, service):
    apply, _ = applier
    spec = a_spec()
    playlist_id = apply.write(spec, apply.plan(spec, tracklist_of("A")))
    service.playlists[playlist_id].append("u:mine")

    made = apply.plan(spec, tracklist_of("A", "B"))
    assert made.manual_kept == ("u:mine",)
    apply.write(spec, made)
    assert service.playlists[playlist_id] == ["u:A", "u:B", "u:mine"]


def test_dropping_a_song_from_the_spec_removes_it_but_not_the_manual_one(applier, service):
    apply, _ = applier
    spec = a_spec()
    playlist_id = apply.write(spec, apply.plan(spec, tracklist_of("A", "B")))
    service.playlists[playlist_id].append("u:mine")

    made = apply.plan(spec, tracklist_of("A"))
    assert made.removes == ("u:B",)
    apply.write(spec, made)
    assert service.playlists[playlist_id] == ["u:A", "u:mine"]


def test_replacing_manual_additions_is_possible_but_must_be_asked_for(applier, service):
    apply, _ = applier
    spec = a_spec()
    playlist_id = apply.write(spec, apply.plan(spec, tracklist_of("A")))
    service.playlists[playlist_id].append("u:mine")

    made = apply.plan(spec, tracklist_of("A"), keep_manual=False)
    apply.write(spec, made)
    assert service.playlists[playlist_id] == ["u:A"]


def test_applying_an_unchanged_spec_reports_no_change(applier):
    apply, _ = applier
    spec = a_spec()
    apply.write(spec, apply.plan(spec, tracklist_of("A")))
    assert not apply.plan(spec, tracklist_of("A")).changes


def test_nothing_resolved_says_to_run_the_backfill(tmp_path, service):
    apply = Apply(
        service, Ledger(tmp_path / "l"), Desired(ResolutionStore(tmp_path / "r")), lambda: TODAY
    )
    with pytest.raises(NothingResolved, match="resolve backfill"):
        apply.plan(a_spec(), tracklist_of("A"))


def test_a_playlist_deleted_from_the_account_is_refused_not_recreated(applier):
    apply, ledger = applier
    spec = a_spec()
    ledger.write(
        LedgerEntry(spec=spec.name, playlist_id="gone", uris=["u:A"], applied=TODAY),
        spec.slug(),
    )
    with pytest.raises(PlaylistGone, match="--recreate"):
        apply.plan(spec, tracklist_of("A"))


def test_the_ledger_records_what_the_spec_placed_not_what_was_preserved(applier, service):
    apply, ledger = applier
    spec = a_spec()
    playlist_id = apply.write(spec, apply.plan(spec, tracklist_of("A")))
    service.playlists[playlist_id].append("u:mine")
    apply.write(spec, apply.plan(spec, tracklist_of("A")))
    # Recording the kept track as jukebox's own would make it indistinguishable
    # from a spec track next time, and the apply after that would delete it.
    assert ledger.read(spec.slug()).uris == ["u:A"]


def test_a_manual_addition_survives_every_later_apply(applier, service):
    # It survived exactly one reconciliation before the ledger stopped claiming
    # preserved tracks as jukebox's own, so once is not enough to prove.
    apply, _ = applier
    spec = a_spec()
    playlist_id = apply.write(spec, apply.plan(spec, tracklist_of("A", "B")))
    service.playlists[playlist_id].append("u:mine")

    for _ in range(3):
        made = apply.plan(spec, tracklist_of("A", "B"))
        assert made.manual_kept == ("u:mine",)
        apply.write(spec, made)
        assert "u:mine" in service.playlists[playlist_id]


def test_a_manual_addition_survives_the_spec_shrinking_around_it(applier, service):
    apply, _ = applier
    spec = a_spec()
    playlist_id = apply.write(spec, apply.plan(spec, tracklist_of("A", "B", "C")))
    service.playlists[playlist_id].append("u:mine")

    apply.write(spec, apply.plan(spec, tracklist_of("A")))
    assert service.playlists[playlist_id] == ["u:A", "u:mine"]

    settled = apply.plan(spec, tracklist_of("A"))
    assert not settled.changes
    assert service.playlists[playlist_id] == ["u:A", "u:mine"]


class Truncating(FakePlaylists):
    """Writes only the first chunk, the way a rate limit part-way through does."""

    def __init__(self, limit: int) -> None:
        super().__init__()
        self._limit = limit

    def replace(self, playlist_id: str, uris: list[str]) -> None:
        """Write a prefix, then fail."""
        self.playlists[playlist_id] = list(uris[: self._limit])
        raise RuntimeError("429 part-way through a multi-request write")


def test_what_is_about_to_be_written_is_recorded_before_the_write(applier, service):
    apply, ledger = applier
    spec = a_spec()
    playlist_id = apply.write(spec, apply.plan(spec, tracklist_of("A")))
    service.playlists[playlist_id].append("u:mine")
    apply.write(spec, apply.plan(spec, tracklist_of("A")))
    # Cleared once the write succeeded, so a later plan is not misled.
    assert ledger.read(spec.slug()).attempted == []


def test_an_interrupted_write_leaves_what_it_was_carrying_on_disk(tmp_path):
    store = _resolutions(tmp_path)
    ledger = Ledger(tmp_path / "ledger")
    spec = a_spec()

    good = FakePlaylists()
    first = Apply(good, ledger, Desired(store), lambda: TODAY)
    playlist_id = first.write(spec, first.plan(spec, tracklist_of("A", "B")))
    good.playlists[playlist_id].append("u:mine")

    breaking = Truncating(limit=1)
    breaking.playlists = good.playlists
    second = Apply(breaking, ledger, Desired(store), lambda: TODAY)
    made = second.plan(spec, tracklist_of("A", "B"))
    with pytest.raises(RuntimeError):
        second.write(spec, made)

    # The playlist is truncated and the hand-added track is gone from it, but
    # what the write was carrying survives on disk.
    assert breaking.playlists[playlist_id] == ["u:A"]
    assert "u:mine" in ledger.read(spec.slug()).attempted


def test_the_next_apply_restores_what_the_interrupted_one_lost(tmp_path):
    store = _resolutions(tmp_path)
    ledger = Ledger(tmp_path / "ledger")
    spec = a_spec()

    good = FakePlaylists()
    first = Apply(good, ledger, Desired(store), lambda: TODAY)
    playlist_id = first.write(spec, first.plan(spec, tracklist_of("A", "B")))
    good.playlists[playlist_id].append("u:mine")

    breaking = Truncating(limit=1)
    breaking.playlists = good.playlists
    second = Apply(breaking, ledger, Desired(store), lambda: TODAY)
    with pytest.raises(RuntimeError):
        second.write(spec, second.plan(spec, tracklist_of("A", "B")))

    third = Apply(good, ledger, Desired(store), lambda: TODAY)
    made = third.plan(spec, tracklist_of("A", "B"))
    assert made.recovered == ("u:mine",)
    assert "restored after an interrupted apply" in made.render()
    third.write(spec, made)
    assert good.playlists[playlist_id] == ["u:A", "u:B", "u:mine"]
