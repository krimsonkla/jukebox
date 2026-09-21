"""The port for authorizing against a music service.

Authorization differs completely between services — Spotify is OAuth PKCE over a
loopback redirect, another may be a device code or a signed developer token — so
the CLI depends on this and never on a flow. An adapter is free to obtain
credentials however its service requires, provided it can answer these three.
"""

from typing import Protocol

from jukebox.ports.auth_status import AuthStatus


class ProviderAuth(Protocol):
    """Obtains, reports and discards a user's authorization for one service."""

    name: str

    def login(self) -> AuthStatus:
        """Interactively obtain authorization, storing whatever it yields."""
        raise NotImplementedError

    def status(self) -> AuthStatus:
        """Report the stored authorization without contacting the service."""
        raise NotImplementedError

    def logout(self) -> bool:
        """Discard the stored authorization; True if there was any."""
        raise NotImplementedError
