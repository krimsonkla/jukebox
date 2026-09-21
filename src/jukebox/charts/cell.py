"""Reduce a rendered table cell to the plain text a corpus row stores.

The MediaWiki `action=parse` output expands templates but keeps reference
superscripts, sort-key spans and line breaks. Spec §Acceptance criteria 7.
"""

import re

from lxml.html import HtmlElement

_QUOTED = re.compile(r'"([^"]+)"')
# A dagger is separated from the title by a no-break space.
_TRAILING_MARKERS = re.compile(r"[\s\u00a0]*[\u2020\u2021*]+$")


def clean_cell(element: HtmlElement) -> str:
    """Plain text for one cell: no citations, `<br>` as a space, one space between words."""
    for superscript in element.xpath('.//sup[contains(@class,"reference")]'):
        superscript.getparent().remove(superscript)
    for line_break in element.xpath(".//br"):
        line_break.tail = " " + (line_break.tail or "")
    return " ".join(element.text_content().split())


def titles(text: str) -> tuple[str, ...]:
    """Every song named in a title cell, lead side first.

    A cell can hold more than one song: a double A-side charts as a single
    position and is written `"Rain Forest" / "Sound Chaser"`. Taking the cell
    whole leaves embedded quotes in the middle of a title, which matches
    nothing in any catalogue.
    """
    stripped = _TRAILING_MARKERS.sub("", text.strip())
    quoted = [found.strip() for found in _QUOTED.findall(stripped) if found.strip()]
    if quoted:
        return tuple(quoted)
    return (stripped,) if stripped else ()


def clean_title(text: str) -> str:
    """The lead song a title cell names.

    Quotes are stripped wherever they wrap the title, including when a
    qualifier follows the closing quote — `"Part-Time Lover" (Remix)`.
    """
    found = titles(text)
    return found[0] if found else ""
