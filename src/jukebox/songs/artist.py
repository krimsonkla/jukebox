"""An artist, and the songs the corpus credits to them."""

from pydantic import BaseModel


class Artist(BaseModel):
    """One credited act, named as the corpus first wrote it.

    `billings` keeps the other spellings seen, because a chart credits guests
    differently week to week and losing that would misreport what was published.
    """

    key: str
    name: str
    billings: tuple[str, ...] = ()
    songs: tuple[str, ...] = ()

    @property
    def total(self) -> int:
        """How many distinct songs the corpus credits to this artist."""
        return len(self.songs)
