"""What one pass over a chart year counted."""

import dataclasses


@dataclasses.dataclass(frozen=True)
class Tally:
    """Rows published, songs named, lookups spent, failures not re-paid for.

    Four numbers that are routinely confused for one another. A chart year
    publishes rows, those rows name fewer songs, only the unanswered ones cost
    a lookup, and the ones a previous pass already failed to find cost nothing
    at all.
    """

    total: int
    distinct: int
    attempted: int
    skipped: int
