"""The HTTP client Spotify's adapters use.

Spotify enforces two separate things. A rate limit counts calls in a rolling
thirty-second window, and pacing is what answers it. A quota counts how many
calls are made at all, and pacing answers nothing there: a development-mode
budget is spent rather than outrun, and a run that spaces itself out arrives at
the same total more slowly.

So the interval below is protection against the first and no help with the
second. A refusal naming QUOTA_EXCEEDED means waiting, not slowing down.
"""

from jukebox.net.pacer import Pacer
from jukebox.net.retrying_client import RetryingClient

# Neither limit is published. This is inside any plausible rolling window, and
# a backfill is a background pass, so the spacing costs minutes and buys the one
# refusal it can actually prevent.
INTERVAL = 0.5


def spotify_client() -> RetryingClient:
    """A retrying client paced for Spotify's rolling rate-limit window."""
    return RetryingClient(pacer=Pacer(INTERVAL))
