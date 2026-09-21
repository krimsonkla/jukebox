"""Recording variants a chart entry does not mean.

With `popularity` gone from the Spotify track object there is nothing to rank
ten candidates by, so a naive top hit takes whatever the search returned. These
are the variants that are the same song and the wrong recording.

Markers match whole words. A substring test fails in the direction that costs
most: `live` occurs inside `Separate Lives`, `cover` inside `Discover`, and
`demo` inside `Demolition`, so it penalises exactly the correct match and
rejects it.
"""

import re

PENALTIES = {
    "karaoke": 1.0,
    "tribute": 1.0,
    "made famous by": 1.0,
    "originally performed": 1.0,
    "in the style of": 1.0,
    "cover": 0.6,
    "live": 0.5,
    "instrumental": 0.5,
    "re-recorded": 0.5,
    "rerecorded": 0.5,
    "remix": 0.3,
    "demo": 0.3,
    "acoustic": 0.3,
}

_MARKERS = {
    marker: re.compile(rf"(?<![\w-]){re.escape(marker)}(?![\w-])", re.IGNORECASE)
    for marker in PENALTIES
}


def penalty(title: str, album: str) -> float:
    """How much to discount a candidate for being the wrong kind of recording."""
    haystack = f"{title} {album}"
    return sum(weight for marker, weight in PENALTIES.items() if _MARKERS[marker].search(haystack))
