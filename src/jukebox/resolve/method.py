"""How a chart entry was matched to a recording."""

import enum


class Method(enum.StrEnum):
    """The path that produced a resolution.

    Recorded per row because the paths have very different reliability, and a
    later pass should be able to find every match that leant on the weakest one.
    """

    ISRC = "isrc"
    SEARCH = "search"
    MANUAL = "manual"
