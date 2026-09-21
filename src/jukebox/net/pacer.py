"""Spacing requests so a rolling rate limit is not reached in the first place.

A service that limits on a rolling window answers 429 to a caller that arrives
too fast, and waiting only once refused makes the refusals themselves the
signal — each one is a request already counted against the window. Spacing the
calls keeps the refusals rare.
"""

import time
from collections.abc import Callable


class Pacer:
    """Holds a caller to a minimum interval between requests."""

    def __init__(
        self,
        interval: float,
        sleep: Callable[[float], None] = time.sleep,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._interval = interval
        self._sleep = sleep
        self._clock = clock
        self._released: float | None = None

    def wait(self) -> None:
        """Block until the interval since the previous request has passed."""
        now = self._clock()
        if self._released is not None:
            remaining = self._interval - (now - self._released)
            if remaining > 0:
                self._sleep(remaining)
                now += remaining
        self._released = now
