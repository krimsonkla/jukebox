"""Read the corpus and keep what a selection names."""

from jukebox.charts.chart import Chart
from jukebox.charts.corpus import Corpus
from jukebox.specs.selected import Selected
from jukebox.specs.spec import Spec


class Selector:
    """Gathers the chart entries a spec draws on."""

    def __init__(self, corpus: Corpus) -> None:
        self._corpus = corpus

    def select(self, spec: Spec) -> list[Selected]:
        """Every entry the spec's selection names, in corpus order."""
        chosen: list[Selected] = []
        for chart in spec.select.charts:
            for year in spec.select.span():
                chosen += self._from(chart, year, spec)
        return chosen

    def _from(self, chart: Chart, year: int, spec: Spec) -> list[Selected]:
        if not self._corpus.path(chart, year).exists():
            return []
        wanted = spec.select.rows()
        return [
            Selected(chart=chart, year=year, entry=entry)
            for entry in self._corpus.read(chart, year).entries
            if wanted.matches(entry) and not spec.excluded(entry.title, entry.artist)
        ]
