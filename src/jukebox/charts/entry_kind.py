"""The three kinds of corpus row.

Most genre charts are published only as number ones, so a row cannot always
carry a rank. Spec §Consequence for the corpus model.
"""

import enum


class EntryKind(enum.Enum):
    """Which published measure a row records."""

    RANKED = "ranked"
    """A year-end position: how big the song was across a whole year."""

    NUMBER_ONE = "number_one"
    """A week at the top, with the date it was reached and how long it held."""

    PEAK = "peak"
    """The highest weekly position a song reached.

    A different measure from a year-end rank. A song can peak at three and
    place nowhere on the year-end list, and one that never rose above forty
    can outlast it and finish the year higher.
    """
