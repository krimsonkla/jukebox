"""What the HTTP layer refuses, and what to do instead."""

from jukebox.errors import JukeboxError

# A quota is spent, not outrun: waiting is the only thing that refills it, and
# pacing the requests further apart does not.
_ADVICE = {
    "QUOTA_EXCEEDED": "the budget for this period is spent; slowing down will not help — "
    "wait it out and re-run to continue from what was saved",
}


class NetError(JukeboxError):
    """Base for the HTTP layer's refusals."""


class TransientFailure(NetError):
    """A request kept failing in a way that usually passes on its own."""

    def __init__(self, url: str, status: int, attempts: int) -> None:
        super().__init__(
            f"{url} answered {status} on {attempts} attempts",
            "the service is rate limiting or unwell; re-run to continue from what was saved",
        )
        self.status = status


class Throttled(NetError):
    """The service asked for a longer pause than this client will hold for.

    Retrying inside the pause it asked for spends another request against the
    window already exceeded, so the caller is told how long it wants instead.

    `reason` is what the service called it, where it says. A quota is a budget
    on how many requests are made at all and a rate limit is one on how quickly;
    spacing requests further apart answers only the second. Without the reason
    a caller cannot tell which lever to reach for, and slowing down against a
    quota reads as a fix while changing nothing.
    """

    def __init__(self, url: str, seconds: float, reason: str | None = None) -> None:
        named = f" ({reason})" if reason else ""
        super().__init__(
            f"{url} asked for {seconds:.0f}s before the next request{named}",
            _ADVICE.get(
                reason,
                "the service is rate limiting hard; wait that out and "
                "re-run to continue from what was saved",
            ),
        )
        self.seconds = seconds
        self.reason = reason
