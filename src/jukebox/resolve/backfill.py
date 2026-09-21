"""Resolve a year of the corpus, keeping what is already known."""

import datetime as dt
from collections import Counter
from collections.abc import Callable, Iterable

from jukebox.charts.chart import Chart
from jukebox.charts.corpus import Corpus
from jukebox.charts.entry import ChartEntry
from jukebox.resolve.attempt import Attempt
from jukebox.resolve.coverage import Coverage
from jukebox.resolve.method import Method
from jukebox.resolve.miss import Miss
from jukebox.resolve.outcome import Outcome
from jukebox.resolve.resolution import Resolution
from jukebox.resolve.resolver import Resolver
from jukebox.resolve.store import ResolutionStore
from jukebox.resolve.tally import Tally


class Backfill:
    """Fills in the resolutions a chart year is missing.

    Each resolution is paid for with a network round trip, so what has been
    resolved is written on the way out whether the pass finished or failed. A
    run that dies on the ninetieth entry must not discard the eighty-nine
    before it.

    A failure is written out too. It cost the same round trip as an answer, and
    a store holding only the answers asks for it again on every pass.
    """

    def __init__(
        self,
        corpus: Corpus,
        store: ResolutionStore,
        resolver: Resolver,
        today: Callable[[], dt.date] = dt.date.today,
    ) -> None:
        self._corpus = corpus
        self._store = store
        self._resolver = resolver
        self._today = today

    def year(self, chart: Chart, year: int, attempt: Attempt | None = None) -> Coverage:
        """Resolve what this chart year names, leaving what is known untouched.

        Two rows naming the same song cost one lookup, whichever chart or year
        either of them came from, because the cache is keyed by the song.

        `attempt.rows` narrows before the lookup rather than after it. Resolving
        a whole chart to serve a spec that takes its top forty pays for rows
        nobody asked about, and every one of them is a request against a budget.
        Coverage is then reported over the rows asked for, since the others were
        never attempted and counting them as unresolved would be a failure that
        did not happen.
        """
        pass_ = attempt or Attempt()
        rows = self._corpus.read(chart, year).entries
        entries = [row for row in rows if pass_.rows.matches(row)]
        held = self._store.load()
        missed = self._store.misses.load()
        outcomes: list[Outcome] = []
        skipped = 0
        try:
            skipped = self._attempt(entries, held, missed, outcomes, (year, pass_))
        finally:
            self._store.save(held)
            self._store.misses.save(missed)
        return _coverage((chart, year), held, outcomes, entries, skipped)

    def _attempt(
        self,
        entries: Iterable[ChartEntry],
        held: dict[str, Resolution],
        missed: dict[str, Miss],
        outcomes: list[Outcome],
        this: tuple[int, Attempt],
    ) -> int:
        year, pass_ = this
        attempted, skipped = 0, 0
        for entry in entries:
            key = Resolution.key_for(entry.title, entry.artist)
            if key in held:
                continue
            if key in missed and not pass_.retry_missed:
                skipped += 1
                continue
            if pass_.limit is not None and attempted >= pass_.limit:
                return skipped
            attempted += 1
            outcome = self._resolver.resolve(entry.title, entry.artist, year)
            outcomes.append(outcome)
            self._record(key, entry, outcome, held, missed)
        return skipped

    def _record(
        self,
        key: str,
        entry: ChartEntry,
        outcome: Outcome,
        held: dict[str, Resolution],
        missed: dict[str, Miss],
    ) -> None:
        """Keep the answer, or keep that there was not one."""
        if outcome.resolved:
            held[key] = _resolution(key, outcome, self._today())
            missed.pop(key, None)
            return
        missed[key] = Miss(
            key=key,
            title=entry.title,
            artist=entry.artist,
            attempted=self._today(),
            score=round(outcome.score.value, 3) if outcome.score else None,
        )


def _resolution(key: str, outcome: Outcome, today: dt.date) -> Resolution:
    return Resolution(
        key=key,
        uri=outcome.match.uri,
        title=outcome.match.title,
        artist=outcome.match.artist,
        method=outcome.method,
        confidence=round(outcome.score.value, 3) if outcome.score else 1.0,
        resolved=today,
        released=outcome.match.released,
    )


def _keys(entries: Iterable[ChartEntry]) -> set[str]:
    """The distinct songs a chart year names, which is what a lookup is spent on."""
    return {Resolution.key_for(entry.title, entry.artist) for entry in entries}


def _coverage(
    where: tuple[Chart, int],
    held: dict[str, Resolution],
    outcomes: list[Outcome],
    entries: list[ChartEntry],
    skipped: int,
) -> Coverage:
    """Counted over this chart year's songs, not over everything the cache holds."""
    chart, year = where
    keys = _keys(entries)
    methods: Counter[Method] = Counter(held[key].method for key in keys if key in held)
    return Coverage(
        chart=chart.slug,
        year=year,
        counted=Tally(
            total=len(entries),
            distinct=len(keys),
            attempted=len(outcomes),
            skipped=skipped,
        ),
        methods=dict(methods),
        unresolved=tuple(outcome for outcome in outcomes if not outcome.resolved),
    )
