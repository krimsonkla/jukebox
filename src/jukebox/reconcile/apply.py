"""Write a plan to the account.

The only place in jukebox that changes someone's playlists. Planning is a
separate call that touches nothing, so a write is always something asked for
rather than a side effect of asking a question.
"""

import datetime as dt
import pathlib
from collections.abc import Callable

from jukebox.paths import Paths
from jukebox.ports.playlist_service import PlaylistService
from jukebox.reconcile.desired import Desired
from jukebox.reconcile.errors import NothingResolved, PlaylistGone
from jukebox.reconcile.ledger import Ledger
from jukebox.reconcile.ledger_entry import LedgerEntry
from jukebox.reconcile.plan import Plan
from jukebox.reconcile.reconciler import Reconciler
from jukebox.reconcile.three_way import ThreeWay
from jukebox.specs.spec import Spec
from jukebox.specs.tracklist import Tracklist


class Apply:
    """Plans a spec against the live playlist, and writes the plan when asked."""

    def __init__(
        self,
        service: PlaylistService,
        ledger: Ledger,
        desired: Desired,
        today: Callable[[], dt.date] = dt.date.today,
    ) -> None:
        self._service = service
        self._ledger = ledger
        self._desired = desired
        self._today = today

    def plan(self, spec: Spec, tracklist: Tracklist, keep_manual: bool = True) -> Plan:
        """What applying would do. Writes nothing."""
        uris, missing = self._desired.uris(tracklist)
        if not uris:
            raise NothingResolved(spec.name)
        held = self._ledger.read(spec.slug())
        playlist_id, live, last = self._live(spec, held)
        return Reconciler(keep_manual=keep_manual).plan(
            spec=spec.name,
            playlist_id=playlist_id,
            lists=ThreeWay(
                desired=uris,
                live=live,
                last=last,
                interrupted=list(held.attempted) if held else [],
            ),
            unresolved=missing,
        )

    def write(self, spec: Spec, plan: Plan) -> str:
        """Apply the plan, creating the playlist if there is not one yet.

        What is about to be written is recorded before the write and cleared
        after it. A long playlist takes several requests, and a failure
        between them truncates it — the tracks a person added exist nowhere
        else, so they reach disk before anything is destroyed.
        """
        playlist_id = plan.playlist_id or self._service.create(spec.name, spec.description).id
        held = self._ledger.read(spec.slug())
        self._record(spec, playlist_id, held.uris if held else [], list(plan.final))
        self._service.replace(playlist_id, list(plan.final))
        self._record(spec, playlist_id, list(plan.desired), [])
        return playlist_id

    def _record(self, spec: Spec, playlist_id: str, uris: list[str], attempted: list[str]) -> None:
        self._ledger.write(
            LedgerEntry(
                spec=spec.name,
                playlist_id=playlist_id,
                uris=uris,
                attempted=attempted,
                applied=self._today(),
            ),
            spec.slug(),
        )

    def _live(self, spec: Spec, held: LedgerEntry | None) -> tuple[str | None, list, list]:
        if held is None:
            return None, [], []
        if self._service.find(held.playlist_id) is None:
            raise PlaylistGone(spec.name, held.playlist_id)
        return held.playlist_id, self._service.items(held.playlist_id), held.uris


def ledger_root(override: pathlib.Path | None = None) -> pathlib.Path:
    """Where the ledger lives: the user's data, never the repository."""
    return override or Paths.resolve().ledger
