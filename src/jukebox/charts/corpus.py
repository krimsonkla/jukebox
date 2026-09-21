"""Reading and writing the vendored corpus.

Written so that re-fetching an unchanged page produces byte-identical output:
a diff should be a chart that changed, never a reordering or a reformat.
Spec §Acceptance criteria 9.
"""

import json
import pathlib

from jukebox.charts.chart import Chart
from jukebox.charts.chart_file import ChartFile


class Corpus:
    """The corpus on disk, one JSON file per chart per year."""

    def __init__(self, root: pathlib.Path) -> None:
        self._root = root

    def path(self, chart: Chart, year: int) -> pathlib.Path:
        """Where this chart and year live."""
        return self._root / chart.slug / f"{year}.json"

    def write(self, chart_file: ChartFile) -> pathlib.Path:
        """Write one chart file, and return where it went."""
        destination = self.path(chart_file.chart, chart_file.year)
        destination.parent.mkdir(parents=True, exist_ok=True)
        payload = chart_file.model_copy(update={"entries": chart_file.sorted_entries()})
        body = payload.model_dump(mode="json", exclude_none=True)
        destination.write_text(
            json.dumps(body, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        return destination

    def read(self, chart: Chart, year: int) -> ChartFile:
        """Read one chart file back."""
        return ChartFile.model_validate_json(self.path(chart, year).read_text(encoding="utf-8"))
