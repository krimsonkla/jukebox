"""The ways Wikipedia lays out chart data.

Spec §Problem — investigation found three chart layouts, not the one the
brainstorm assumed. A discography is the fourth, and differs in kind: it is
keyed by an artist rather than by a chart and a year, and one page carries
rows for many of both.
"""

import enum


class PageShape(enum.Enum):
    """How to read a page's tables."""

    RANKED = "ranked"
    NUMBER_ONES = "number-ones"
    DECADE = "decade"
    DISCOGRAPHY = "discography"
