"""The three-way difference, which is the whole reason a ledger exists."""

from jukebox.charts import Chart, ChartEntry, EntryKind
from jukebox.reconcile import Reconciler, ThreeWay
from jukebox.specs import Selected


def plan_of(desired, live, last, keep_manual=True):
    """A plan over three lists of URIs."""
    return Reconciler(keep_manual=keep_manual).plan(
        spec="s",
        playlist_id="p",
        lists=ThreeWay(desired=list(desired), live=list(live), last=list(last)),
        unresolved=[],
    )


def test_a_first_apply_adds_everything():
    made = plan_of(["a", "b"], [], [])
    assert made.adds == ("a", "b") and not made.removes
    assert made.final == ("a", "b")


def test_an_unchanged_playlist_needs_no_write():
    made = plan_of(["a", "b"], ["a", "b"], ["a", "b"])
    assert not made.changes
    assert not made.adds and not made.removes and not made.reordered


def test_a_track_the_spec_dropped_is_removed():
    made = plan_of(["a"], ["a", "b"], ["a", "b"])
    assert made.removes == ("b",) and made.final == ("a",)


def test_a_track_added_by_hand_is_kept_and_reported():
    # It is on the playlist and not in the record of what jukebox wrote.
    made = plan_of(["a"], ["a", "mine"], ["a"])
    assert made.manual_kept == ("mine",)
    assert made.final == ("a", "mine")
    assert not made.removes


def test_a_manual_addition_is_dropped_only_when_asked():
    made = plan_of(["a"], ["a", "mine"], ["a"], keep_manual=False)
    assert not made.manual_kept
    assert made.removes == ("mine",)


def test_a_dropped_track_and_a_manual_addition_are_told_apart():
    # Both are on the playlist and absent from the desired list; only the
    # record of what was written distinguishes them.
    made = plan_of(["a"], ["a", "dropped", "mine"], ["a", "dropped"])
    assert made.removes == ("dropped",)
    assert made.manual_kept == ("mine",)


def test_a_manual_addition_the_spec_now_wants_is_not_counted_twice():
    made = plan_of(["a", "mine"], ["a", "mine"], ["a"])
    assert not made.manual_kept
    assert made.final == ("a", "mine")
    assert not made.adds


def test_a_reorder_is_detected_when_the_set_is_unchanged():
    made = plan_of(["b", "a"], ["a", "b"], ["a", "b"])
    assert made.reordered and not made.adds and not made.removes
    assert made.changes


def test_the_desired_order_leads_and_manual_additions_follow():
    made = plan_of(["a", "b"], ["mine", "a"], ["a"])
    assert made.final == ("a", "b", "mine")


def test_a_plan_with_no_playlist_yet_says_it_creates_one():
    made = Reconciler().plan(
        spec="s",
        playlist_id=None,
        lists=ThreeWay(desired=["a"], live=[], last=[]),
        unresolved=[],
    )
    assert made.creates and made.changes
    assert "new playlist" in made.render()


def test_the_report_names_what_it_could_not_match():
    missing = Selected(
        chart=Chart.HOT_100,
        year=1985,
        entry=ChartEntry(kind=EntryKind.RANKED, rank=1, title="Obscure", artist="Nobody"),
    )
    made = Reconciler().plan(
        spec="s",
        playlist_id="p",
        lists=ThreeWay(desired=["a"], live=[], last=[]),
        unresolved=[missing],
    )
    assert "Obscure — Nobody" in made.render()


def test_the_report_states_when_there_is_nothing_to_do():
    assert "nothing to do" in plan_of(["a"], ["a"], ["a"]).render()
