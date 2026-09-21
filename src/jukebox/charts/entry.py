"""One row of the corpus.

A ranked row and a number-one row carry different fields, and a row that claims
one kind while carrying the other's fields is the defect this validation exists
to reject. Spec §Consequence for the corpus model.
"""

import datetime as dt

from pydantic import BaseModel, model_validator

from jukebox.charts.entry_kind import EntryKind


class ChartEntry(BaseModel):
    """A song's appearance on a chart, either ranked for the year or at number one."""

    kind: EntryKind
    title: str
    artist: str
    also: tuple[str, ...] | None = None
    """Further songs sharing the position, where a double A-side charted as one."""
    rank: int | None = None
    reached: dt.date | None = None
    weeks: int | None = None

    @model_validator(mode="after")
    def _fields_match_the_kind(self) -> "ChartEntry":
        if self.kind is EntryKind.RANKED:
            _require(self.rank is not None, "a ranked entry needs a rank")
            _require(self.reached is None, "a ranked entry carries no reached date")
        else:
            _require(self.reached is not None, "a number one needs a reached date")
            _require(self.rank is None, "a number one carries no rank")
        return self

    def order(self) -> tuple:
        """Sort key: rank for ranked rows, date then title for number ones."""
        if self.kind is EntryKind.RANKED:
            return (self.rank,)
        return (self.reached, self.title)


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)
