"""A candidate recording from a music service."""

import dataclasses
import datetime as dt


@dataclasses.dataclass(frozen=True)
class TrackMatch:
    """One recording a catalogue offered, in service-neutral terms.

    `uri` is opaque: whatever the service uses to name a track. `released` is
    the album's release date where the service gives one, and is a tiebreaker
    rather than a filter — a 1985 recording reissued on a 2010 compilation is
    the same master.
    """

    uri: str
    title: str
    artist: str
    album: str = ""
    released: dt.date | None = None
