"""The three ways Wikipedia lays out a Billboard chart.

Spec §Problem — investigation found three, not the one the brainstorm assumed.
"""

import enum


class PageShape(enum.Enum):
    """How to read a chart page's table."""

    RANKED = "ranked"
    NUMBER_ONES = "number-ones"
    DECADE = "decade"
