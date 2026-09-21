"""Which music services jukebox can talk to.

Adapters are built from an application identifier supplied at runtime, so
choosing a service is something a conversation can do rather than something the
environment must have settled before the process started.
"""

from jukebox.errors import JukeboxError
from jukebox.providers import spotify
from jukebox.providers.provider import Provider
from jukebox.providers.spotify.settings import SpotifySettings


def _spotify(client_id: str) -> SpotifySettings:
    return SpotifySettings(client_id=client_id)


PROVIDERS: dict[str, Provider] = {
    spotify.NAME: Provider(
        name=spotify.NAME,
        needs=(
            "a client id from an app at https://developer.spotify.com/dashboard, "
            "with redirect URI http://127.0.0.1:8888/callback"
        ),
        auth=lambda client_id: spotify.build_auth(_spotify(client_id)),
        catalog=lambda client_id: spotify.SpotifyCatalog(
            spotify.build_session(_spotify(client_id))
        ),
        playlists=lambda client_id: spotify.SpotifyPlaylists(
            spotify.build_session(_spotify(client_id))
        ),
    ),
}

DEFAULT = spotify.NAME


class UnknownProvider(JukeboxError):
    """No adapter answers to that name."""

    def __init__(self, name: str, known: list[str]) -> None:
        super().__init__(
            f"no music service named {name!r}",
            f"choose one of: {', '.join(known)}",
        )


def named(name: str) -> Provider:
    """The provider with this name."""
    if name not in PROVIDERS:
        raise UnknownProvider(name, sorted(PROVIDERS))
    return PROVIDERS[name]


def build_auth(name: str) -> object:
    """The authorizer for a named provider, configured from the environment.

    The command line keeps this path: a person who has already set the client id
    in their environment should not have to repeat it at every invocation.
    """
    named(name)
    return spotify.build_auth()
