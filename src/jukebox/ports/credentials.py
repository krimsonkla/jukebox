"""The port the playlist operations will authenticate through.

Kept deliberately narrow: an operation needs a usable bearer credential and does
not care whether it was refreshed, read from disk, or minted seconds ago.
"""

from typing import Protocol


class Credentials(Protocol):
    """Supplies a currently valid credential for one music service."""

    def bearer(self) -> str:
        """A credential valid right now, refreshing it first if required."""
        raise NotImplementedError
