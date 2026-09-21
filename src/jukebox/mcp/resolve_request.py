"""What a caller wants resolved, and how much it may spend doing it."""

import dataclasses

from jukebox.charts.entry_filter import EntryFilter
from jukebox.resolve.attempt import Attempt


@dataclasses.dataclass(frozen=True)
class ResolveRequest:
    """Which charts and years to resolve, narrowed, under a lookup budget.

    `rows` narrows before a lookup is spent rather than after, so resolving
    what a spec selects costs what that selection costs.
    """

    years: tuple[int, int]
    charts: list[str] | None = None
    limit: int = 200
    rows: EntryFilter = dataclasses.field(default_factory=EntryFilter)
    retry_missed: bool = False
    """Whether to look again for songs an earlier pass did not find.

    Off by default: a lookup costs the same whether it answers or not, so
    re-paying for known failures spends a budget without advancing.
    """

    def attempt(self, limit: int | None) -> Attempt:
        """This request as one chart year's pass, under what budget is left."""
        return Attempt(limit=limit, rows=self.rows, retry_missed=self.retry_missed)
