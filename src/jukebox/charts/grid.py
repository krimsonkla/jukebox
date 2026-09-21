"""A wikitable as a dense rectangle of strings.

Rowspan and colspan are what make the chart tables hard: a dance title held for
three weeks is written once and spans the rows it held, and a two-chart page
groups its columns under a spanning header. Expanding both here means every
mapper reads a plain rectangle. Spec §Acceptance criteria 10, 11.
"""

from dataclasses import dataclass

import lxml.html
from lxml.html import HtmlElement

from jukebox.charts.cell import clean_cell
from jukebox.charts.errors import NoTableFound

# A span is attacker-influenced text on a publicly editable page; a bare int()
# raises on `2px` and a large value allocates before anything checks it.
MAX_SPAN = 100


@dataclass(frozen=True)
class Grid:
    """Every cell of one table, with spans expanded into repeated values."""

    rows: list[list[str]]

    @classmethod
    def of(cls, html: str) -> "Grid":
        """The first wikitable in a rendered page."""
        tables = lxml.html.fromstring(html).xpath('//table[contains(@class,"wikitable")]')
        if not tables:
            raise NoTableFound("the rendered page")
        return cls(rows=_expand(tables[0]))

    def widths(self) -> set[int]:
        """The distinct row widths; a dense grid has exactly one."""
        return {len(row) for row in self.rows}


def _expand(table: HtmlElement) -> list[list[str]]:
    rows: list[list[str]] = []
    carried: dict[int, tuple[str, int]] = {}
    for tr in table.xpath(".//tr"):
        rows.append(_expand_row(tr.xpath("./td|./th"), carried))
    return rows


def _expand_row(cells: list[HtmlElement], carried: dict[int, tuple[str, int]]) -> list[str]:
    row: list[str] = []
    column = index = 0
    while index < len(cells) or column in carried:
        if column in carried:
            text, remaining = carried.pop(column)
            row.append(text)
            if remaining > 1:
                carried[column] = (text, remaining - 1)
            column += 1
            continue
        column = _place(cells[index], row, column, carried)
        index += 1
    return row


def _place(
    cell: HtmlElement, row: list[str], column: int, carried: dict[int, tuple[str, int]]
) -> int:
    text = clean_cell(cell)
    rowspan = _span(cell.get("rowspan"))
    for _ in range(_span(cell.get("colspan"))):
        row.append(text)
        if rowspan > 1:
            carried[column] = (text, rowspan - 1)
        column += 1
    return column


def _span(value: str | None) -> int:
    """A row or column span, clamped and never raising on rubbish."""
    try:
        span = int(value) if value is not None else 1
    except (TypeError, ValueError):
        return 1
    return max(1, min(span, MAX_SPAN))
