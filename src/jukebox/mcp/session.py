"""What this connection has been told about the account it is acting on.

Held in memory for the life of the server process, which for a stdio MCP server
is the life of the conversation. Session scope is therefore structural rather
than promised: nothing writes it down, so nothing outlives the session that
chose it.

A client id is not a secret — PKCE exists so a public client need not keep one —
which is why it can be spoken over the wire at all. A client *secret* must never
arrive this way, and `use` refuses anything shaped like one.
"""

import dataclasses

from jukebox.mcp.errors import LooksLikeASecret


@dataclasses.dataclass
class SessionConfig:
    """The provider and application this session is using, if it has been told."""

    provider: str | None = None
    client_id: str | None = None

    @property
    def configured(self) -> bool:
        """Whether this session knows which application to act as."""
        return bool(self.provider and self.client_id)

    def use(self, provider: str, client_id: str) -> None:
        """Record the choice for the rest of this session."""
        cleaned = client_id.strip()
        if _secretish(cleaned):
            raise LooksLikeASecret()
        self.provider = provider
        self.client_id = cleaned


def _secretish(value: str) -> bool:
    """Whether a value looks like a client secret rather than a client id.

    A Spotify client id is 32 hexadecimal characters. Anything carrying a
    separator, a scheme, or a `secret` label is something else, and the cost of
    guessing wrong is a credential in a conversation.
    """
    lowered = value.lower()
    return (
        "secret" in lowered
        or ":" in value
        or (value.count("-") > 0 and len(value) > 40)
        or len(value) > 64
    )
