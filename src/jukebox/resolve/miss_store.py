"""Where the failures live.

Beside the resolutions and under the same rules: machine-local, disposable, and
holding the chart's own words rather than a catalogue's. What it keeps is that a
question was asked and went unanswered, which is this project's own fact.
"""

import json
import pathlib

from jukebox.resolve.miss import Miss


class MissStore:
    """Reads and writes the songs a pass looked for and did not find."""

    def __init__(self, root: pathlib.Path) -> None:
        self._root = root

    @property
    def path(self) -> pathlib.Path:
        """Where the misses live."""
        return self._root / "missed.json"

    def load(self) -> dict[str, Miss]:
        """Every miss held, keyed by song identity."""
        if not self.path.exists():
            return {}
        rows = json.loads(self.path.read_text(encoding="utf-8"))
        return {row["key"]: Miss.model_validate(row) for row in rows}

    def save(self, misses: dict[str, Miss]) -> pathlib.Path:
        """Write them back in key order, so a re-run diffs as content."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        body = [misses[key].model_dump(mode="json") for key in sorted(misses)]
        self.path.write_text(
            json.dumps(body, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        return self.path
