"""What the Spotify adapter refuses, and what to do instead."""

from jukebox.oauth.errors import OAuthError


class MissingClientId(OAuthError):
    """The app's client id was never configured."""

    def __init__(self) -> None:
        super().__init__(
            "no Spotify client id configured",
            "create an app at https://developer.spotify.com/dashboard with redirect URI "
            "http://127.0.0.1:8888/callback, then set JUKEBOX_SPOTIFY_CLIENT_ID to its client id",
        )
