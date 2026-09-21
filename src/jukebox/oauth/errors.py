"""What the OAuth flow refuses, and what to do instead."""

from jukebox.errors import JukeboxError


class OAuthError(JukeboxError):
    """Base for the OAuth flow's refusals."""


class NotAuthorized(OAuthError):
    """No usable credential, and none can be obtained without the user."""

    def __init__(self, provider: str) -> None:
        super().__init__(
            f"not authorized with {provider}",
            f"run `jukebox auth login --provider {provider}`",
        )


class AuthorizationDenied(OAuthError):
    """The service returned an error instead of a code or a token."""

    def __init__(self, reason: str) -> None:
        super().__init__(
            f"the service refused the authorization: {reason}",
            "check the app's redirect URI matches exactly, then run `jukebox auth login` again",
        )


class StateMismatch(OAuthError):
    """The callback did not carry the state this attempt generated."""

    def __init__(self) -> None:
        super().__init__(
            "the authorization callback carried the wrong state",
            "run `jukebox auth login` again, and do not reuse an old browser tab",
        )


class AuthorizationTimedOut(OAuthError):
    """Nobody completed the consent page in time."""

    def __init__(self, seconds: float) -> None:
        super().__init__(
            f"no authorization redirect arrived within {seconds:.0f} seconds",
            "open the URL again and approve it in the browser, or check that "
            "nothing else is listening on the redirect port",
        )
