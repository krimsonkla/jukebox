"""What the MCP surface refuses, and what to do instead."""

from jukebox.errors import JukeboxError


class NotAuthorizedYet(JukeboxError):
    """The server started without a usable Spotify authorization."""

    def __init__(self) -> None:
        super().__init__(
            "this session has no authorization for the chosen provider",
            "call auth_login, or run `jukebox auth login`",
        )


class NoChartSource(JukeboxError):
    """The server started without a way to reach the encyclopaedia."""

    def __init__(self) -> None:
        super().__init__(
            "this jukebox server cannot reach Wikipedia",
            "restart the server with network access to fetch chart pages",
        )


class TooManyYears(JukeboxError):
    """One call asked for more of the corpus than a call should do."""

    def __init__(self, years: tuple[int, int]) -> None:
        super().__init__(
            f"{years[0]}-{years[1]} is too many years for one call",
            "ask for at most twenty years at a time, then call again for the rest",
        )


class NoProviderChosen(JukeboxError):
    """Nothing has told this session which service and application to act as."""

    def __init__(self, known: list[str]) -> None:
        super().__init__(
            "this session has not been told which music service to use",
            "call list_providers to see what is available, then use_provider with "
            f"the name and the application's client id; known: {', '.join(known)}",
        )


class LooksLikeASecret(JukeboxError):
    """The value offered as a client id looks like a client secret."""

    def __init__(self) -> None:
        super().__init__(
            "that looks like a client secret rather than a client id",
            "jukebox uses PKCE and never needs a secret — pass only the client id, "
            "which the dashboard shows unhidden",
        )
