"""What jukebox last wrote for one spec."""

import datetime as dt

from pydantic import BaseModel


class LedgerEntry(BaseModel):
    """The playlist a spec owns, and the exact URIs last written to it.

    Storing the whole list rather than only the playlist id is what makes a
    manual addition recognisable. With the id alone, a track someone added by
    hand is indistinguishable from one the spec has since dropped, and
    reconciliation silently eats the first while claiming to remove the second.
    """

    spec: str
    playlist_id: str
    uris: list[str]
    applied: dt.date
    attempted: list[str] = []
    """What the last apply was about to write, cleared once it succeeded.

    A playlist longer than a hundred tracks is written in more than one request,
    so a failure part-way through leaves it truncated. Whatever was on it that
    the spec does not name — the tracks a person added — exists nowhere else, so
    it is recorded here before the write rather than mourned after it.
    """
