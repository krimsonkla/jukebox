"""The two kinds of corpus row.

Most genre charts are published only as number ones, so a row cannot always
carry a rank. Spec §Consequence for the corpus model.
"""

import enum


class EntryKind(enum.Enum):
    """Whether a row records a year-end rank or a week at number one."""

    RANKED = "ranked"
    NUMBER_ONE = "number_one"
