"""Which rows of a chart year a caller wants.

A spec selecting from the corpus, a query answering a question about it, and a
backfill deciding what to spend a lookup on all narrow the same rows in the
same vocabulary. Written once each, they drift: the spec could filter by weeks
and the query could not, the query could filter by artist and the spec could
not, and the backfill could not filter at all, so it paid for rows nothing had
asked for.
"""

from typing import Annotated

from pydantic import BaseModel, BeforeValidator, ConfigDict, ValidationError

from jukebox.charts.entry import ChartEntry
from jukebox.charts.entry_kind import EntryKind
from jukebox.charts.errors import UnknownMeasure


def _listed(value: object) -> object:
    """One name and a list of names are the same measure, written two ways."""
    return [value] if isinstance(value, str) else value


Names = Annotated[list[str], BeforeValidator(_listed)]


class EntryFilter(BaseModel):
    """A predicate over one chart row, in the charts' own measures.

    A measure a row does not publish never excludes it. A year-end list ranks
    one to a hundred and a number-ones list does not rank at all, because every
    row of one was already first; filtering those by rank would silently drop
    the strongest rows in the selection. The same holds in reverse for weeks at
    number one, which a year-end row does not carry.

    There is a measure for each: `max_rank` reads a year-end position,
    `max_peak` reads how high a record got, and `min_weeks` reads how long it
    stayed. A song can be the fortieth biggest of its year without ever rising
    above thirty, so one option answering both would answer neither.

    `artists` holds a set because a collection is usually a group of acts rather
    than one. Any name matching keeps the row, so the measure reads as "these
    acts" and a single act is the one-name case.
    """

    model_config = ConfigDict(extra="forbid")

    max_rank: int | None = None
    max_peak: int | None = None
    min_weeks: int | None = None
    artists: Names = []
    title: str | None = None

    @classmethod
    def named(cls, pairs: list[str] | None) -> "EntryFilter":
        """A filter written as `measure=value`, the way a command line says it.

        One option that carries the measures rather than one option per measure,
        so a measure added here reaches the command line without another flag.
        A measure written more than once collects, which is how a set of names
        is said on a command line.
        """
        named: dict[str, list[str]] = {}
        for pair in pairs or []:
            measure, sep, value = pair.partition("=")
            if not sep or not measure.strip():
                raise UnknownMeasure(pair, list(cls.model_fields))
            named.setdefault(measure.strip(), []).append(value.strip())
        try:
            return cls.model_validate({key: _one(given) for key, given in named.items()})
        except ValidationError as refused:
            raise UnknownMeasure(", ".join(pairs or []), list(cls.model_fields)) from refused

    def matches(self, entry: ChartEntry) -> bool:
        """Whether this row is one the caller asked for."""
        return (
            self._ranks(entry) and self._peaked(entry) and self._held(entry) and self._named(entry)
        )

    def narrows(self) -> bool:
        """Whether this filter excludes anything at all."""
        return any((self.max_rank, self.max_peak, self.min_weeks, self.artists, self.title))

    def _ranks(self, entry: ChartEntry) -> bool:
        if self.max_rank is None or entry.kind is not EntryKind.RANKED:
            return True
        return entry.rank <= self.max_rank

    def _peaked(self, entry: ChartEntry) -> bool:
        if self.max_peak is None or entry.kind is not EntryKind.PEAK:
            return True
        return entry.rank <= self.max_peak

    def _held(self, entry: ChartEntry) -> bool:
        if self.min_weeks is None or entry.kind is not EntryKind.NUMBER_ONE:
            return True
        return (entry.weeks or 1) >= self.min_weeks

    def _named(self, entry: ChartEntry) -> bool:
        """Substring, folded — a search over how the chart wrote it, not an identity."""
        if self.artists and not _any_of(self.artists, entry.artist):
            return False
        return not (self.title and self.title.casefold() not in entry.title.casefold())


def _one(given: list[str]) -> str | list[str]:
    """A measure said once reads as itself; said twice it reads as a set."""
    return given[0] if len(given) == 1 else given


def _any_of(names: list[str], credited: str) -> bool:
    folded = credited.casefold()
    return any(name.casefold() in folded for name in names)
