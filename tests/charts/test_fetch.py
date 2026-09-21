"""Fetch composes the module — spec §Design, fetch.py.

The decade path needs its own year: 1985 resolves no decade chart, so a fetch
of 1985 alone never exercises the shape the rock charts are published in.
"""

import datetime as dt

from jukebox.charts import Chart, Corpus, EntryKind, Registry
from jukebox.charts.fetch import Fetch


def _modern_rock_only() -> Registry:
    """The real registry, narrowed to one chart.

    Restating the entry here would duplicate the registry and quietly stop
    describing it the moment the registry moves.
    """
    return Registry(
        entries=tuple(
            entry
            for entry in Registry.billboard().entries
            if entry.chart is Chart.MODERN_ROCK and entry.covers(1990)
        )
    )


MODERN_ROCK_1990S = _modern_rock_only()


def test_a_decade_chart_is_fetched_parsed_and_written(tmp_path, fixture_source):
    corpus = Corpus(tmp_path)
    report = Fetch(MODERN_ROCK_1990S, fixture_source, corpus, today=dt.date(2026, 9, 6)).year(1990)

    assert [found.chart for found in report.resolved] == [Chart.MODERN_ROCK]
    written = corpus.read(Chart.MODERN_ROCK, 1990)
    assert written.kind is EntryKind.NUMBER_ONE
    assert written.retrieved == dt.date(2026, 9, 6)
    assert written.entries[0].title == "House"
    assert all(entry.reached.year == 1990 for entry in written.entries)


def test_the_gaps_of_a_narrow_registry_are_still_reported(tmp_path, fixture_source):
    report = Fetch(MODERN_ROCK_1990S, fixture_source, Corpus(tmp_path)).year(1990)
    assert {gap.chart for gap in report.gaps} == set(Chart) - {Chart.MODERN_ROCK}
    assert report.ok
