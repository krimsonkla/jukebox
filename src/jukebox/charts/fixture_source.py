"""Rendered chart pages from the committed fixtures.

Every parser test reads through this, so the suite never leaves the machine.
Spec §Acceptance criteria 8.
"""

import json
import pathlib

from jukebox.charts.errors import PageNotFound

MANIFEST = "manifest.json"


class FixtureSource:
    """Serves the pages committed under a fixtures directory."""

    def __init__(self, directory: pathlib.Path) -> None:
        self._directory = directory
        self._titles: dict[str, str] = json.loads((directory / MANIFEST).read_text())

    def fetch(self, title: str) -> str:
        """The committed HTML for `title`."""
        if title not in self._titles:
            raise PageNotFound(title)
        return (self._directory / self._titles[title]).read_text(encoding="utf-8")
