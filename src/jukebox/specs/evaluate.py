"""Turn a stored spec into a tracklist."""

from jukebox.charts.corpus import Corpus
from jukebox.specs.errors import EmptySelection
from jukebox.specs.selector import Selector
from jukebox.specs.shaper import Shaper
from jukebox.specs.spec import Spec
from jukebox.specs.tracklist import Tracklist


class Evaluate:
    """Selects, then shapes."""

    def __init__(self, corpus: Corpus) -> None:
        self._selector = Selector(corpus)
        self._shaper = Shaper()

    def tracklist(self, spec: Spec) -> Tracklist:
        """The tracklist this spec describes."""
        selected = self._selector.select(spec)
        if not selected:
            raise EmptySelection(spec.name)
        return self._shaper.shape(spec, selected)
