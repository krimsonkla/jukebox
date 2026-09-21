"""What the browser hands back at the loopback address."""

import dataclasses


@dataclasses.dataclass(frozen=True)
class Callback:
    """The redirect query, reduced to what the flow reads."""

    code: str | None
    state: str | None
    error: str | None
