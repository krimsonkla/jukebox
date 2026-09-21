"""What a backfill managed, and what it did not."""

import dataclasses

from jukebox.resolve.method import Method
from jukebox.resolve.outcome import Outcome
from jukebox.resolve.tally import Tally


@dataclasses.dataclass(frozen=True)
class Coverage:
    """Per-chart resolution counts and the entries left unanswered."""

    chart: str
    year: int
    counted: Tally
    methods: dict[Method, int]
    """How the answers were arrived at, counted by method."""

    unresolved: tuple[Outcome, ...]

    @property
    def total(self) -> int:
        """Rows the chart published, which is not how many lookups they cost."""
        return self.counted.total

    @property
    def distinct(self) -> int:
        """Songs those rows name, once each. Two rows for one song is one lookup."""
        return self.counted.distinct

    @property
    def attempted(self) -> int:
        """Lookups this pass actually spent, which is what a caller budgets."""
        return self.counted.attempted

    @property
    def skipped(self) -> int:
        """Songs a previous pass already failed to find, not paid for again.

        Reported because a pass that spends less than expected should say why:
        the budget was not wasted, it was not needed.
        """
        return self.counted.skipped

    @property
    def by_isrc(self) -> int:
        """Answers an exact recording identifier settled."""
        return self.methods.get(Method.ISRC, 0)

    @property
    def by_search(self) -> int:
        """Answers the scorer settled from a search."""
        return sum(count for method, count in self.methods.items() if method is not Method.ISRC)

    @property
    def resolved(self) -> int:
        """How many of this year's songs produced a track."""
        return self.by_isrc + self.by_search

    def render(self) -> str:
        """The report as the CLI prints it."""
        rate = (self.resolved / self.distinct * 100) if self.distinct else 0.0
        rows = f" of {self.total} rows" if self.total != self.distinct else ""
        lines = [
            f"  {self.chart:<16} {self.resolved:>3}/{self.distinct:<3} ({rate:.0f}%){rows}  "
            f"isrc {self.by_isrc}, search {self.by_search}"
        ]
        if self.skipped:
            lines.append(f"      {self.skipped} already known missing, not looked up again")
        lines += [
            f"      unresolved: {outcome.title} — {outcome.artist}" for outcome in self.unresolved
        ]
        return "\n".join(lines)
