"""One chart entry's answer."""

import datetime as dt

from pydantic import BaseModel

from jukebox.resolve.method import Method
from jukebox.songs.identity import Identity


class Resolution(BaseModel):
    """What a song resolved to, how, and how well.

    `key` is the song's identity rather than the row that happened to ask, so
    one answer serves every chart and year the song appears on, and a re-fetch
    that respells a title does not orphan it.
    """

    key: str
    uri: str
    title: str
    artist: str
    method: Method
    confidence: float
    resolved: dt.date
    released: dt.date | None = None
    """When the catalogue says the recording came out, where it says at all.

    Kept because a chart cannot answer it: ordering a playlist by release needs
    a catalogue fact, and paying for the lookup twice to learn it again would be
    the waste this cache exists to avoid.
    """

    @staticmethod
    def key_for(title: str, artist: str) -> str:
        """The identity of the song a chart row names."""
        return Identity.of(title, artist).key
