"""Configuration for the Spotify adapter.

The client id is configuration rather than a secret: PKCE exists for public
clients and Spotify issues no client secret for one. The refresh token is the
credential, and it lives in the token store.
"""

import pathlib

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from jukebox.paths import Paths

LOOPBACK = ("127.0.0.1", "::1", "[::1]")


class SpotifySettings(BaseSettings):
    """Everything the Spotify authorization flow needs, from the environment."""

    model_config = SettingsConfigDict(env_prefix="JUKEBOX_SPOTIFY_", extra="ignore")

    client_id: str = ""
    redirect_host: str = "127.0.0.1"
    redirect_port: int = 8888
    state_dir: pathlib.Path = Field(default_factory=lambda: Paths.resolve().credentials)
    """Where the refresh token is kept — the user's data directory, not the cwd."""

    @field_validator("redirect_host")
    @classmethod
    def _must_be_loopback(cls, host: str) -> str:
        """Refuse anything but a loopback literal.

        Spotify permits HTTP for a redirect only on a loopback address, and the
        callback carries an authorization code. Binding a routable interface
        would offer that code to the network and put the app out of terms at the
        same time — not something an environment variable should be able to do.
        """
        if host not in LOOPBACK:
            raise ValueError(
                f"{host!r} is not a loopback address; use one of {', '.join(LOOPBACK)}"
            )
        return host

    @property
    def redirect_uri(self) -> str:
        """The loopback address Spotify sends the user back to.

        Spotify permits HTTP only for a loopback IP literal and rejects
        `localhost` outright, so the host is an address rather than a name.
        """
        return f"http://{self.redirect_host}:{self.redirect_port}/callback"
