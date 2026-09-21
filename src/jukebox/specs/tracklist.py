"""What a spec evaluates to."""

import dataclasses

from jukebox.specs.ordering import Ordering
from jukebox.specs.selected import Selected


@dataclasses.dataclass(frozen=True)
class Tracklist:
    """The chosen entries in order, and what shaping left behind.

    `dropped` is reported rather than discarded: a playlist shorter than the
    chart is a question, and the answer is usually the per-artist cap.
    """

    name: str
    entries: tuple[Selected, ...]
    considered: int
    dropped_to_cap: int
    order: Ordering = Ordering.CHART

    @property
    def sequenced_later(self) -> bool:
        """Whether the final sequence is settled at resolution rather than here.

        A release ordering needs a date the corpus does not hold, so what a
        preview shows is the order the list was cut in, not the order it will
        be written in. Saying so is the difference between a preview and a
        promise the apply will break.
        """
        return self.order is Ordering.RELEASE

    def composition(self) -> dict[str, int]:
        """How many tracks each chart contributed."""
        counts: dict[str, int] = {}
        for chosen in self.entries:
            counts[chosen.chart.slug] = counts.get(chosen.chart.slug, 0) + 1
        return counts

    def render(self) -> str:
        """The tracklist as the CLI prints it."""
        lines = [
            f"{self.name} — {len(self.entries)} tracks " f"(from {self.considered} chart entries)"
        ]
        if self.dropped_to_cap:
            lines.append(f"  {self.dropped_to_cap} held back by the per-artist cap")
        if self.sequenced_later:
            lines.append("  shown in chart-year order; sequenced by release date when resolved")
        counts = self.composition()
        if len(counts) > 1:
            # A selection drawing on both a ranked chart and a number-ones chart
            # is easily lopsided, because a rank filter narrows only the former.
            share = ", ".join(f"{chart} {count}" for chart, count in sorted(counts.items()))
            lines.append(f"  from: {share}")
        lines += [
            f"  {index:>3}. {chosen.title} — {chosen.artist} "
            f"[{chosen.chart.slug} {chosen.year}]"
            for index, chosen in enumerate(self.entries, start=1)
        ]
        return "\n".join(lines)
