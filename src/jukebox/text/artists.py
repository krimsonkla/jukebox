"""Split a chart's artist cell into names a catalogue will recognise.

A chart writes a collaboration as one cell — `Philip Bailey and Phil Collins`,
`Ray Charles (with Willie Nelson)`, `Patti LaBelle/ Harold Faltermeyer`. Sent
whole to a search filter that expects one artist the row matches nothing, which
is why the credited artists are tried individually as well as the cell.
"""

import re

_PARENTHETICAL = re.compile(r"\s*\(([^)]*)\)")
_JOINER = r"featuring|feat\.?|ft\.?|with|and|&|x|vs\.?"
_SPLIT = re.compile(rf"\s*(?:/|,)\s*|\s+(?:{_JOINER})\s+", re.IGNORECASE)
_LEADING_JOINER = re.compile(rf"^(?:{_JOINER})\s+", re.IGNORECASE)


def credited(cell: str) -> tuple[str, ...]:
    """The artist strings worth searching, most complete first.

    The whole cell comes first because a duo whose name contains `&` is one
    artist, not two, and only the catalogue can settle which this is.
    """
    whole = cell.strip()
    candidates = [whole, _PARENTHETICAL.sub("", whole).strip()]
    for source in (whole, _PARENTHETICAL.sub(" ", whole)):
        candidates += [part.strip(" .") for part in _SPLIT.split(source)]
    return _unique(_LEADING_JOINER.sub("", name).strip() for name in candidates)


def lead(cell: str) -> str:
    """The artist the cell credits first.

    Two charts bill the same recording differently — `Coolio` on one and
    `Coolio featuring L.V.` on another — so the billing is what differs and the
    lead is what they agree on. It is the identity a song is known by; the
    guests are part of how it was credited that week.
    """
    whole = _PARENTHETICAL.sub(" ", cell).strip()
    first = _SPLIT.split(whole)[0].strip(" .")
    return _LEADING_JOINER.sub("", first).strip() or cell.strip()


def _unique(names) -> tuple[str, ...]:
    seen, ordered = set(), []
    for name in names:
        folded = name.lower()
        if name and folded not in seen:
            seen.add(folded)
            ordered.append(name)
    return tuple(ordered)
