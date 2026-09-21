"""A playlist, described rather than assembled.

The spec is what makes a rebuild deterministic: it records what was asked for,
in the charts' vocabulary, so the same file produces the same tracklist. It
names no music service and holds no service's identifiers.
"""

from pydantic import BaseModel, Field

from jukebox.specs.exclusion import Exclusion
from jukebox.specs.selection import Selection
from jukebox.specs.slug import slugify
from jukebox.specs.shape import Shape


class Spec(BaseModel):
    """One playlist's definition."""

    name: str = Field(min_length=1)
    description: str = ""
    select: Selection
    shape: Shape = Shape()
    exclude: list[Exclusion] = []

    def slug(self) -> str:
        """The filename this spec is stored under."""
        return slugify(self.name)

    def excluded(self, title: str, artist: str) -> bool:
        """Whether an entry is one the spec drops."""
        return any(rule.matches(title, artist) for rule in self.exclude)
