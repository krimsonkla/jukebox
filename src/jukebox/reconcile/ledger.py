"""Where the record of what was written lives.

Account state, not project data: it names a playlist on someone's account and
holds that service's identifiers, so it sits under `.jukebox/` beside the token
and never enters the repository.
"""

import pathlib

from jukebox.reconcile.ledger_entry import LedgerEntry


class Ledger:
    """Reads and writes what jukebox last applied, one file per spec."""

    def __init__(self, root: pathlib.Path) -> None:
        self._root = root

    def path(self, spec_slug: str) -> pathlib.Path:
        """Where this spec's record is kept."""
        return self._root / f"{spec_slug}.json"

    def read(self, spec_slug: str) -> LedgerEntry | None:
        """What was last written for this spec, or None if it has never been applied."""
        path = self.path(spec_slug)
        if not path.exists():
            return None
        return LedgerEntry.model_validate_json(path.read_text(encoding="utf-8"))

    def write(self, entry: LedgerEntry, spec_slug: str) -> pathlib.Path:
        """Record what has just been written."""
        destination = self.path(spec_slug)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(entry.model_dump_json(indent=2) + "\n", encoding="utf-8")
        return destination
