"""What a spec's tracklist means in track URIs.

Resolution lives in a machine-local cache, so an entry can be selected and still
have no track. Those are carried through to the plan rather than dropped: a
playlist shorter than the spec is a question, and silence is not an answer.

This is also where a release ordering is settled. Every other ordering is a
chart's own, and the shaper applies it against the corpus alone; a release date
is a catalogue fact, so the sequence it names can only be known once the
catalogue has answered.
"""

import datetime as dt

from jukebox.resolve.resolution import Resolution
from jukebox.resolve.store import ResolutionStore
from jukebox.specs.ordering import Ordering
from jukebox.specs.selected import Selected
from jukebox.specs.tracklist import Tracklist


class Desired:
    """Turns selected chart entries into the URIs a playlist should hold."""

    def __init__(self, store: ResolutionStore) -> None:
        self._store = store

    def uris(self, tracklist: Tracklist) -> tuple[list[str], list[Selected]]:
        """The URIs in the tracklist's order, and the entries that have none."""
        held = self._store.load()
        matched: list[Resolution] = []
        missing: list[Selected] = []
        seen: set[str] = set()
        for chosen in tracklist.entries:
            # Keyed by the song, so a resolution earned on one chart answers for
            # the same song on another rather than reading as unresolved.
            row = held.get(_key(chosen))
            if row is None:
                missing.append(chosen)
            elif row.uri not in seen:
                seen.add(row.uri)
                matched.append(row)
        if tracklist.order is Ordering.RELEASE:
            matched.sort(key=_released)
        return [row.uri for row in matched], missing


def _key(chosen: Selected) -> str:
    return Resolution.key_for(chosen.title, chosen.artist)


def _released(row: Resolution) -> tuple:
    """Oldest first, with undated recordings last rather than earliest.

    A catalogue does not always give a date. Sorting a missing one as the start
    of time would put the least-known recordings at the front of the playlist,
    which is the opposite of what the ordering was asked for.
    """
    return (row.released is None, row.released or dt.date.min, row.title.casefold())
