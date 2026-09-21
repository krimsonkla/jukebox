"""Choosing a music service, and the application to act as.

Without these, a person must set an environment variable before launching the
client — which is the configuration step the surface exists to remove.
"""

from jukebox.mcp.session import SessionConfig
from jukebox.providers import registry


def list_providers(session: SessionConfig) -> dict:
    """Which music services this build can talk to, and what each needs."""
    return {
        "providers": [
            {"name": provider.name, "needs": provider.needs}
            for provider in registry.PROVIDERS.values()
        ],
        "default": registry.DEFAULT,
        "using": session.provider,
        "configured": session.configured,
    }


def use_provider(session: SessionConfig, provider: str, client_id: str) -> dict:
    """Use this service and application for the rest of the session.

    Nothing is written to disk: the choice lives for the life of this
    connection. A client id is not a secret, which is why it may be spoken; a
    client secret is refused.
    """
    registry.named(provider)
    session.use(provider, client_id)
    return {"using": session.provider, "configured": session.configured}
