"""A song the catalogue did not answer for, and when it was asked.

A lookup costs the same whether it succeeds or not, and a store that keeps only
the answers re-pays for every failure on every pass. Against a budget counted in
requests rather than results that is the difference between a backfill that
converges and one that never can.

Recorded with the date so a miss can be revisited deliberately: a catalogue
gains recordings, and a scorer that rejected a real match today may accept it
after a change here. A miss is a fact about one attempt, never a verdict.
"""

import datetime as dt

from pydantic import BaseModel


class Miss(BaseModel):
    """One song that a pass looked for and did not find."""

    key: str
    title: str
    artist: str
    attempted: dt.date
    score: float | None = None
    """How close the best candidate came, where there was one at all.

    A miss just under the threshold is a different thing from a miss with
    nothing to score: the first says the scorer was cautious, the second that
    the catalogue was silent, and only the first is worth another lookup.
    """

    @property
    def near(self) -> bool:
        """Whether something was offered and only narrowly rejected."""
        return self.score is not None
