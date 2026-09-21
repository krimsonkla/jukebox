"""The port every page fetch goes through.

The only seam that touches the network, so parsing is testable offline.
Spec §Design.
"""

from typing import Protocol


class ChartSource(Protocol):
    """Somewhere rendered chart pages come from."""

    def fetch(self, title: str) -> str:
        """The rendered HTML of the page with this title."""
        raise NotImplementedError
