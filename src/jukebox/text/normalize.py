"""Reduce a title or artist to what two spellings of it share.

Chart tables and streaming catalogues disagree constantly about punctuation,
case, bracketed qualifiers and whether a compound word carries a space, so a
comparison on the raw strings understates almost every true match.
"""

import re
import unicodedata

_BRACKETED = re.compile(r"[\(\[][^\)\]]*[\)\]]")
_SUFFIX = re.compile(r"\s+-\s+.*$")
_APOSTROPHE = re.compile(r"['\u2019]")
_NOISE = re.compile(r"[^a-z0-9 ]+")
_SPACES = re.compile(r"\s+")
_THE = re.compile(r"^the ")


def normalize(text: str) -> str:
    """Casefolded, unaccented, punctuation-free, single-spaced."""
    folded = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    # An apostrophe closes a word rather than breaking it: "Don't" is one token,
    # so replacing it with a space would mismatch every contraction.
    without = _APOSTROPHE.sub("", folded.lower())
    return _SPACES.sub(" ", _NOISE.sub(" ", without)).strip()


def core_title(text: str) -> str:
    """A title without its qualifiers.

    Streaming titles carry the edit in brackets or after a dash — `(7" Version)`,
    `- Remastered`, `- From "Beverly Hills Cop"` — none of which changes which
    song it is.
    """
    return normalize(_BRACKETED.sub(" ", _SUFFIX.sub("", text)))


def core_artist(text: str) -> str:
    """An artist name without a leading article, which the two sides disagree on."""
    return _THE.sub("", normalize(text))
