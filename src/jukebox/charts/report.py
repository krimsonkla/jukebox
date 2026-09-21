"""What a fetch covered, and what it could not.

A gap is an outcome, not a failure: Modern Rock has no 1985 because the chart
began in 1988. Reporting that plainly is what stops a thin corpus reading as a
complete one. Spec §Acceptance criteria 5.
"""

from dataclasses import dataclass

from jukebox.charts.gap import Gap
from jukebox.charts.resolved import Resolved


@dataclass(frozen=True)
class CoverageReport:
    """Per-chart coverage for one year."""

    year: int
    resolved: list[Resolved]
    gaps: list[Gap]

    @property
    def ok(self) -> bool:
        """A year with gaps still succeeded; only a fetch or parse failure does not."""
        return True

    def render(self) -> str:
        """The report as the CLI prints it."""
        lines = [f"charts for {self.year}"]
        lines += [
            f"  {found.chart.slug:<16} {found.entries:>4} entries  {found.title}"
            for found in self.resolved
        ]
        lines += [f"  {gap.chart.slug:<16}    - no data  ({gap.reason.value})" for gap in self.gaps]
        return "\n".join(lines)
