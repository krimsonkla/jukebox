"""The local resolution cache.

Machine-local rather than committed. Spotify's developer terms permit only
temporary caching of metadata and forbid storing, aggregating or building
databases of Spotify Content beyond what running the app strictly requires; a
file in version control is permanent, redistributable and the opposite of
temporary. So this lives with the user's cache, and what a repository keeps is
the chart corpus, which is not Spotify's.

Keyed by song rather than by chart row. A recording that charted on four lists
is one lookup and one answer, and a chart-year is not a boundary the cache can
see past.

The cost is that a rebuild is reproducible only as far as the catalogue is
stable: the corpus and the spec pin what is asked for, not what Spotify answers.
"""

import json
import pathlib

from jukebox.paths import Paths
from jukebox.resolve.miss_store import MissStore
from jukebox.resolve.resolution import Resolution


class ResolutionStore:
    """Reads and writes resolutions, keyed by the identity of the song."""

    def __init__(self, root: pathlib.Path) -> None:
        self._root = root

    @property
    def path(self) -> pathlib.Path:
        """Where the resolutions live."""
        return self._root / "songs.json"

    @property
    def misses(self) -> MissStore:
        """The failures, beside the answers and under the same root.

        Both record what a lookup produced, so one root answers for both and
        no caller has to know where the second one lives.
        """
        return MissStore(self._root)

    def load(self) -> dict[str, Resolution]:
        """Every resolution held, keyed by song identity."""
        if not self.path.exists():
            return {}
        rows = json.loads(self.path.read_text(encoding="utf-8"))
        return {row["key"]: Resolution.model_validate(row) for row in rows}

    def save(self, resolutions: dict[str, Resolution]) -> pathlib.Path:
        """Write them back in key order, so a re-run diffs as content."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        body = [resolutions[key].model_dump(mode="json") for key in sorted(resolutions)]
        self.path.write_text(
            json.dumps(body, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        return self.path


def resolutions_root(override: pathlib.Path | None = None) -> pathlib.Path:
    """Where resolutions are cached: the user's cache, never the repository."""
    return override or Paths.resolve().resolutions
