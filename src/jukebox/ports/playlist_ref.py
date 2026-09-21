"""A playlist on a music service."""

import dataclasses


@dataclasses.dataclass(frozen=True)
class PlaylistRef:
    """What a service calls a playlist, and what a person calls it."""

    id: str
    name: str
    url: str = ""
