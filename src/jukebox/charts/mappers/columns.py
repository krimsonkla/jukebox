"""Where one chart's fields sit in a number-ones grid."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Columns:
    """The column indices a single chart occupies.

    `weeks` is None on pages that write a run by repeating the row rather than
    by counting it.
    """

    title: int
    artist: int
    weeks: int | None
