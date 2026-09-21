"""Reading the strings a chart publishes.

Titles and artist cells are written for a reader, not for a lookup: the same
recording is spelled differently by two charts and differently again by a
catalogue. Reducing them is neither the corpus's business nor a service
adapter's, and both need it, so it lives on its own beneath both.
"""

from jukebox.text.artists import credited, lead
from jukebox.text.normalize import core_artist, core_title, normalize

__all__ = ["core_artist", "core_title", "credited", "lead", "normalize"]
