"""The chart entry a resolution is trying to answer."""

import dataclasses


@dataclasses.dataclass(frozen=True)
class Sought:
    """What the chart says: a song, its credited artist, and the year it charted."""

    title: str
    artist: str
    year: int
