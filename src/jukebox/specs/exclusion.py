"""A song a spec leaves out.

Keyed on the chart's own title and artist rather than on a service's track
identifier. That keeps a spec readable and stable when a resolution changes, and
keeps another service's content out of a file this repository commits.
"""

from pydantic import BaseModel

from jukebox.text.normalize import core_artist, core_title


class Exclusion(BaseModel):
    """One song to drop, however the chart happens to spell it."""

    title: str
    artist: str | None = None

    def matches(self, title: str, artist: str) -> bool:
        """Whether this exclusion covers a chart entry."""
        if core_title(self.title) != core_title(title):
            return False
        return self.artist is None or core_artist(self.artist) == core_artist(artist)
