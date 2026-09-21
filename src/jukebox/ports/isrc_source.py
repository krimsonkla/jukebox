"""The port an exact recording identifier is looked up through.

Separate from the catalogue: the service that knows a recording's ISRC is
rarely the service that will play it.
"""

from typing import Protocol


class IsrcSource(Protocol):
    """Somewhere a recording's ISRCs can be found."""

    def isrcs_for(self, title: str, artist: str) -> tuple[str, ...]:
        """Every ISRC known for a recording, possibly none."""
        raise NotImplementedError
