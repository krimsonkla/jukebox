"""Where one corpus file's rows came from.

Chart data is Wikipedia-derived and carries CC BY-SA 4.0, so a corpus file
names the pages it was built from and the day each was read. A file can draw on
more than one page: a chart's own article says who reached number one, and an
artist's discography says where everything else stopped.
"""

import datetime as dt

from pydantic import BaseModel


class Attribution(BaseModel):
    """One page a corpus file draws on."""

    title: str
    retrieved: dt.date
