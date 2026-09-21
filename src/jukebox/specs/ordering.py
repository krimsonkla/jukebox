"""How a tracklist is sequenced.

There is deliberately no option that ranks a year-end position against a week at
number one. They are different published measures, and a single ordering over
both would be a composite invented here rather than a chart anyone published.
"""

import enum


class Ordering(enum.StrEnum):
    """The sequence a shaped tracklist comes out in."""

    CHART = "chart"
    """Each chart's own order: rank for a year-end list, date for number ones."""

    YEAR = "year"
    """Chronological, then each chart's own order within a year."""

    SHUFFLE = "shuffle"
    """Deterministic for a given seed, so the same spec rebuilds the same list."""

    RELEASE = "release"
    """When the recording came out, which is a catalogue fact and not a chart one.

    Every other ordering is settled by the corpus alone, so a preview is exact
    and offline. This one is settled at resolution, because a chart says when a
    song was popular and never when it was released. A preview of it shows the
    chronological order it will be cut and capped in, and says that the final
    sequence follows.
    """
