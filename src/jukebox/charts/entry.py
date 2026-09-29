"""One row of the corpus.

A row that ranks and a row that reached number one carry different fields, and
a row that claims one kind while carrying the other's fields is the defect this
validation exists to reject. Spec §Consequence for the corpus model.
"""

import datetime as dt

from pydantic import BaseModel, model_validator

from jukebox.charts.entry_kind import EntryKind


class ChartEntry(BaseModel):
    """A song's appearance on a chart, in whichever measure the chart published."""

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
        if self.kind is EntryKind.NUMBER_ONE:
            _require(self.reached is not None, "a number one needs a reached date")
            _require(self.rank is None, "a number one carries no rank")
        else:
            _require(self.rank is not None, f"a {self.kind.value} entry needs a rank")
            _require(self.reached is None, f"a {self.kind.value} entry carries no reached date")
        return self

    @property
    def position(self) -> int:
        """The place this row publishes.

        A number-ones page prints no column of positions, but states that the
        song reached the top, so first place is what it publishes.
        """
        return 1 if self.kind is EntryKind.NUMBER_ONE else self.rank

    def order(self) -> tuple:
        """Where this row sits in its file.

        One file can hold rows of more than one measure, so the key groups by
        measure first and only then applies that measure's own order: a week at
        the top sorts by the date it was reached, and a position by the
        position. Comparing the two directly has no meaning.
        """
        if self.kind is EntryKind.NUMBER_ONE:
            return (0, self.reached, 0, self.title)
        return (1, dt.date.min, self.rank, self.title)


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)
