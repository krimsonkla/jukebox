"""The three-way difference between wanted, live, and last written.

Two lists cannot tell a manual addition from a track the spec has dropped: both
are simply present on the playlist and absent from the desired list. The record
of what jukebox itself last wrote is what separates them, and keeping the
user's own additions depends entirely on having it.
"""

from jukebox.reconcile.changes import Changes
from jukebox.reconcile.plan import Plan
from jukebox.reconcile.three_way import ThreeWay
from jukebox.specs.selected import Selected


class Reconciler:
    """Works out what applying a spec would change."""

    def __init__(self, keep_manual: bool = True) -> None:
        self._keep_manual = keep_manual

    def plan(
        self, spec: str, playlist_id: str | None, lists: ThreeWay, unresolved: list[Selected]
    ) -> Plan:
        """The plan, computed and returned without writing anything."""
        manual = [uri for uri in lists.live if uri not in lists.last and uri not in lists.desired]
        kept = manual if self._keep_manual else []
        # An interrupted write truncates the playlist, so what it was carrying is
        # missing from `live` and recoverable only from what was recorded first.
        recovered = [
            uri
            for uri in lists.interrupted
            if uri not in lists.live and uri not in lists.desired and uri not in kept
        ]
        final = lists.desired + kept + recovered
        return Plan(
            spec=spec,
            playlist_id=playlist_id,
            final=tuple(final),
            desired=tuple(lists.desired),
            diff=Changes(
                adds=tuple(uri for uri in final if uri not in lists.live),
                removes=tuple(uri for uri in lists.live if uri not in final),
                manual_kept=tuple(kept),
                recovered=tuple(recovered),
                reordered=final != lists.live,
            ),
            unresolved=tuple(unresolved),
        )
