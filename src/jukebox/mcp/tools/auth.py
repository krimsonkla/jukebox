"""Authorizing the account from the conversation.

An assistant that cannot authorize can only tell someone to go and run a
command, which is the same dead end as being unable to fetch the corpus.

Logging out is deliberately absent. It is the one account operation with no use
in a conversation about playlists, and an agent that can discard a credential
unprompted is a hazard with no matching benefit; `jukebox auth logout` does it.
"""

from jukebox.ports.provider_auth import ProviderAuth


def auth_status(service: ProviderAuth) -> dict:
    """Whether the account is authorized, without contacting the service."""
    return _reported(service.status())


def auth_login(service: ProviderAuth) -> dict:
    """Open the consent page in the user's browser and wait for them to approve.

    Blocks until they approve or the wait runs out. Nothing is read or written
    on their account; this only obtains the permission to do so later.
    """
    return _reported(service.login())


def _reported(status) -> dict:
    return {
        "provider": status.provider,
        "authorized": status.authorized,
        "expires_at": status.expires_at.isoformat() if status.expires_at else None,
        "scopes": list(status.scopes),
    }
