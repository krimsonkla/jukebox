"""The three collaborators every OAuth interaction needs together.

A store to read and write the token, a client to obtain one, and a clock to
judge expiry. They are always passed as a set, so they travel as one.
"""

import dataclasses
import datetime as dt
from collections.abc import Callable

from jukebox.oauth.token_client import TokenClient
from jukebox.oauth.token_store import TokenStore


@dataclasses.dataclass(frozen=True)
class Flow:
    """Where tokens live, how they are obtained, and what time it is."""

    store: TokenStore
    client: TokenClient
    clock: Callable[[], dt.datetime]
