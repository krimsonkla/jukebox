"""The index on disk.

Derived from the corpus and rebuilt by a command, so it belongs with the cache
rather than the user's data. It holds only what Billboard published — the same
titles and artists the corpus already carries — so no service's content reaches
it.
"""

import json
import pathlib

from jukebox.songs.artist import Artist
from jukebox.songs.index import Index
from jukebox.songs.song import Song


class IndexStore:
    """Reads and writes the song index."""

    def __init__(self, root: pathlib.Path) -> None:
        self._root = root

    @property
    def path(self) -> pathlib.Path:
        """Where the index lives."""
        return self._root / "index.json"

    def exists(self) -> bool:
        """Whether an index has been built."""
        return self.path.exists()

    def save(self, index: Index) -> pathlib.Path:
        """Write it in key order, so a rebuild diffs as content."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        body = {
            "years": list(index.years) if index.years else None,
            "songs": [index.songs[key].model_dump(mode="json") for key in sorted(index.songs)],
            "artists": [
                index.artists[key].model_dump(mode="json") for key in sorted(index.artists)
            ],
        }
        self.path.write_text(
            json.dumps(body, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        return self.path

    def load(self) -> Index:
        """The index as last built, or an empty one."""
        if not self.exists():
            return Index(songs={}, artists={})
        body = json.loads(self.path.read_text(encoding="utf-8"))
        songs = [Song.model_validate(row) for row in body.get("songs", [])]
        artists = [Artist.model_validate(row) for row in body.get("artists", [])]
        held = body.get("years")
        return Index(
            songs={song.key: song for song in songs},
            artists={artist.key: artist for artist in artists},
            years=(held[0], held[1]) if held else None,
        )
