"""How much a pass may spend, and what it may spend it on."""

import dataclasses

from jukebox.charts.entry_filter import EntryFilter


@dataclasses.dataclass(frozen=True)
class Attempt:
    """One pass over a chart year: its budget, its rows, and what it retries.

    `retry_missed` decides whether songs an earlier pass failed to find are
    looked for again. They are skipped by default, because a lookup costs the
    same whether it answers or not and re-paying for known failures is how a
    backfill spends a budget without advancing.
    """

    limit: int | None = None
    rows: EntryFilter = dataclasses.field(default_factory=EntryFilter)
    retry_missed: bool = False
