"""Why a (chart, year) has no page.

Absence is data. A gap without a reason is indistinguishable from a bug.
"""

import enum


class GapReason(enum.Enum):
    """The closed set of reasons a chart is missing for a year."""

    CHART_DID_NOT_EXIST = "chart did not exist that year"
    NO_ARTICLE = "no registry entry covers this chart and year"
