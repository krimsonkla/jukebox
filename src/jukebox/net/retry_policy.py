"""How long a client keeps trying, and how long it waits between attempts."""

import dataclasses
import random
from collections.abc import Callable

ATTEMPTS = 4
BACKOFF = 1.0

# Retry-After is a courtesy, not an instruction: waiting whatever it names hands
# a hostile or broken upstream the dial on how long a call is held. Past the
# ceiling a client refuses rather than retries, because a retry inside the pause
# the service asked for is another request against the window it is already
# refusing.
CEILING = 60.0


def full_jitter(cap: float) -> float:
    """Somewhere in [0, cap], so repeated failures do not resynchronise."""
    return random.uniform(0.0, cap)


@dataclasses.dataclass(frozen=True)
class RetryPolicy:
    """The waiting a retrying client does, as one value it can be given."""

    attempts: int = ATTEMPTS
    backoff: float = BACKOFF
    ceiling: float = CEILING
    jitter: Callable[[float], float] = full_jitter

    def pause(self, attempt: int) -> float:
        """How long to wait after `attempt` when the service named no delay."""
        return self.jitter(min(self.backoff * (2**attempt), self.ceiling))

    def too_long(self, seconds: float) -> bool:
        """Whether a delay the service asked for is longer than this will hold for."""
        return seconds > self.ceiling
