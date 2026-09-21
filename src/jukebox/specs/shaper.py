"""Order the selected entries, then cut them to size.

Order first, cap second, size last. Capping before ordering would let the cap
discard an entry the ordering would have ranked above one it kept, which makes
the result depend on corpus layout rather than on the spec.
"""

import random

from jukebox.charts.entry_kind import EntryKind
from jukebox.specs.ordering import Ordering
from jukebox.specs.selected import Selected
from jukebox.specs.shape import Shape
from jukebox.specs.spec import Spec
from jukebox.specs.tracklist import Tracklist


class Shaper:
    """Turns selected entries into a tracklist."""

    def shape(self, spec: Spec, selected: list[Selected]) -> Tracklist:
        """Order, cap per artist, and cut to size."""
        ordered = _ordered(selected, spec.shape)
        kept, capped = _capped(ordered, spec.shape.max_per_artist)
        sized = kept[: spec.shape.size] if spec.shape.size else kept
        return Tracklist(
            name=spec.name,
            entries=tuple(sized),
            considered=len(selected),
            dropped_to_cap=capped,
            order=spec.shape.order,
        )


def _ordered(selected: list[Selected], shape: Shape) -> list[Selected]:
    if shape.order is Ordering.SHUFFLE:
        shuffled = list(selected)
        random.Random(shape.seed).shuffle(shuffled)
        return shuffled
    if shape.order in (Ordering.YEAR, Ordering.RELEASE):
        # A release ordering is settled at resolution, but the cap and the size
        # are settled here, so they are applied to the closest thing the corpus
        # knows: the year it charted. Leaving it unordered would make which
        # entries survive the cap depend on corpus layout.
        return sorted(selected, key=lambda chosen: (chosen.year, *_within(chosen)))
    return sorted(selected, key=lambda chosen: (chosen.chart.slug, *_within(chosen)))


def _within(chosen: Selected) -> tuple:
    """A chart's own order: rank where it ranks, otherwise date."""
    entry = chosen.entry
    if entry.kind is EntryKind.RANKED:
        return (0, entry.rank, "")
    return (1, 0, entry.reached.isoformat() if entry.reached else "")


def _capped(ordered: list[Selected], limit: int | None) -> tuple[list[Selected], int]:
    if limit is None:
        return ordered, 0
    seen: dict[str, int] = {}
    kept, dropped = [], 0
    for chosen in ordered:
        artist = chosen.artist.casefold()
        if seen.get(artist, 0) >= limit:
            dropped += 1
            continue
        seen[artist] = seen.get(artist, 0) + 1
        kept.append(chosen)
    return kept, dropped
