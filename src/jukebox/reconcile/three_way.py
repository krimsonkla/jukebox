"""The three lists a reconciliation compares."""

import dataclasses


@dataclasses.dataclass(frozen=True)
class ThreeWay:
    """What is wanted, what is there, and what jukebox last put there.

    Two of these would be enough to compute a difference and not enough to
    attribute it: a track present on the playlist and absent from the desired
    list is either something a person added or something the spec dropped, and
    only `last` says which.
    """

    desired: list[str]
    live: list[str]
    last: list[str]
    interrupted: list[str] = dataclasses.field(default_factory=list)
    """What a previous apply was writing when it failed, if one did."""
