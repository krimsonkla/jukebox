"""Whether a music service is currently usable, and until when."""

import dataclasses
import datetime as dt


@dataclasses.dataclass(frozen=True)
class AuthStatus:
    """What an adapter can say about its authorization without making a call."""

    provider: str
    authorized: bool
    expires_at: dt.datetime | None = None
    scopes: tuple[str, ...] = ()
