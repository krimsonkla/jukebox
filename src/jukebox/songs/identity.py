"""What makes two chart rows the same song.

A chart file is a list, and the same recording appears on as many lists as it
charted on — twice in one year when a number one straddles New Year, twice
again when a song tops both halves of the dance chart. Nothing in the corpus
says those rows are one song, so every consumer either repeats the work or
repeats the answer.

Identity is that missing statement: the reduced title and the leading credited
artist, which is what two chart tables agree on when their spellings differ.
"""

import dataclasses

from jukebox.text.artists import lead
from jukebox.text.normalize import core_artist, core_title

SEPARATOR = "␟"


@dataclasses.dataclass(frozen=True, order=True)
class Identity:
    """A song, independent of which chart wrote it down or how."""

    title: str
    artist: str

    @classmethod
    def of(cls, title: str, artist: str) -> "Identity":
        """The identity of a chart row's song."""
        return cls(title=core_title(title), artist=core_artist(lead(artist)))

    @classmethod
    def parse(cls, key: str) -> "Identity":
        """The identity a key names."""
        title, _, artist = key.partition(SEPARATOR)
        return cls(title=title, artist=artist)

    @property
    def key(self) -> str:
        """The identity as one string, for a filename or a cache key."""
        return f"{self.title}{SEPARATOR}{self.artist}"
