"""How a tracklist is sequenced.

No ordering ranks a week at number one against a year-end position. Those are
different published measures, and an ordering over both would be a composite
invented here rather than a chart anyone published. How high a song got is not
in that category: a year-end list prints the position, and a number-ones list
states that the song reached first, so both publish a peak and `PEAK` reads it.
"""

import enum


class Ordering(enum.StrEnum):
    """The sequence a shaped tracklist comes out in."""

    CHART = "chart"
    """Each chart's own order: rank for a year-end list, date for number ones."""

    YEAR = "year"
    """Chronological, then each chart's own order within a year."""

    PEAK = "peak"
    """How high it got, best first.

    The measure is the position a chart published, so a number-one entry peaks
    at one and a year-end entry peaks at its rank.

    A row is placed by its own position, not by the song's best across every
    chart. A song that charted twice is two rows and takes two places, the
    better one first; a playlist keeps whichever resolves first and so lands at
    the better position, but a spec capped by size counts both.
    """

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
