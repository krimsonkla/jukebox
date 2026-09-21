"""Which rows of a chart year a caller wants.

A spec selecting from the corpus, a query answering a question about it, and a
backfill deciding what to spend a lookup on all narrow the same rows in the
same vocabulary. Written once each, they drift: the spec could filter by weeks
and the query could not, the query could filter by artist and the spec could
not, and the backfill could not filter at all, so it paid for rows nothing had
asked for.
"""

from pydantic import BaseModel, ConfigDict, ValidationError

from jukebox.charts.entry import ChartEntry
from jukebox.charts.entry_kind import EntryKind
from jukebox.charts.errors import UnknownMeasure


class EntryFilter(BaseModel):
    """A predicate over one chart row, in the charts' own measures.

    A measure a row does not publish never excludes it. A year-end list ranks
    one to a hundred and a number-ones list does not rank at all, because every
    row of one was already first; filtering those by rank would silently drop
    the strongest rows in the selection. The same holds in reverse for weeks at
    number one, which a year-end row does not carry.
    """

    model_config = ConfigDict(extra="forbid")

    max_rank: int | None = None
    min_weeks: int | None = None
    artist: str | None = None
    title: str | None = None

    @classmethod
    def named(cls, pairs: list[str] | None) -> "EntryFilter":
        """A filter written as `measure=value`, the way a command line says it.

        One option that carries the measures rather than one option per measure,
        so a measure added here reaches the command line without another flag.
        """
        named: dict[str, str] = {}
        for pair in pairs or []:
            measure, sep, value = pair.partition("=")
            if not sep or not measure.strip():
                raise UnknownMeasure(pair, list(cls.model_fields))
            named[measure.strip()] = value.strip()
        try:
            return cls.model_validate(named)
        except ValidationError as refused:
            raise UnknownMeasure(", ".join(pairs or []), list(cls.model_fields)) from refused

    def matches(self, entry: ChartEntry) -> bool:
        """Whether this row is one the caller asked for."""
        return self._ranks(entry) and self._held(entry) and self._named(entry)

    def narrows(self) -> bool:
        """Whether this filter excludes anything at all."""
        return any((self.max_rank, self.min_weeks, self.artist, self.title))

    def _ranks(self, entry: ChartEntry) -> bool:
        if self.max_rank is None or entry.kind is not EntryKind.RANKED:
            return True
        return entry.rank <= self.max_rank

    def _held(self, entry: ChartEntry) -> bool:
        if self.min_weeks is None or entry.kind is not EntryKind.NUMBER_ONE:
            return True
        return (entry.weeks or 1) >= self.min_weeks

    def _named(self, entry: ChartEntry) -> bool:
        """Substring, folded — a search over how the chart wrote it, not an identity."""
        if self.artist and self.artist.casefold() not in entry.artist.casefold():
            return False
        return not (self.title and self.title.casefold() not in entry.title.casefold())
