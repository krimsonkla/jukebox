"""Reading and writing the vendored corpus.

Written so that re-fetching an unchanged page produces byte-identical output:
a diff should be a chart that changed, never a reordering or a reformat.
Spec §Acceptance criteria 9.
"""

import json
import pathlib

from jukebox.charts.attribution import Attribution
from jukebox.charts.chart import Chart
from jukebox.charts.chart_file import ChartFile
from jukebox.charts.entry import ChartEntry
from jukebox.charts.entry_kind import EntryKind
from jukebox.text.normalize import core_artist, core_title


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
        payload = chart_file.model_copy(
            update={
                "entries": chart_file.sorted_entries(),
                "sources": chart_file.sorted_sources(),
            }
        )
        body = payload.model_dump(mode="json", exclude_none=True)
        destination.write_text(
            json.dumps(body, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        return destination

    def read(self, chart: Chart, year: int) -> ChartFile:
        """Read one chart file back."""
        return ChartFile.model_validate_json(self.path(chart, year).read_text(encoding="utf-8"))

    def refresh(
        self, chart: Chart, year: int, entries: list[ChartEntry], source: Attribution
    ) -> None:
        """Write what a chart's own page says, keeping what other pages added.

        A chart page is authoritative for the measure it publishes and for
        nothing else. It never records a peak, so a re-fetch that simply
        replaced the file would delete every placing an artist's article had
        contributed, along with the credit owed to it.
        """
        held = self.read(chart, year) if self.path(chart, year).exists() else None
        named = {_song(entry) for entry in entries}
        kept = [
            entry
            for entry in (held.entries if held else [])
            if entry.kind is EntryKind.PEAK and _song(entry) not in named
        ]
        others = [
            carried
            for carried in (held.sources if held else [])
            if kept and carried.title != source.title
        ]
        self.write(
            ChartFile(chart=chart, year=year, sources=[source, *others], entries=entries + kept)
        )

    def merge(self, chart: Chart, year: int, entries: list[ChartEntry], source: Attribution) -> int:
        """Add rows a file does not already hold, and return how many were new.

        A song the file already records keeps the row it has. That row came from
        the chart's own article, which says when the song reached the top and how
        long it held, where a discography says only how high it got.
        """
        held = self.read(chart, year) if self.path(chart, year).exists() else None
        known = {_song(entry) for entry in held.entries} if held else set()
        fresh: list[ChartEntry] = []
        for entry in entries:
            # Guarded inside the loop as well as against the file: one article
            # lists a song under singles and again under other charted songs,
            # and two artists' articles both carry a duet.
            if _song(entry) in known:
                continue
            known.add(_song(entry))
            fresh.append(entry)
        # A page read again carries the day it was last read, because the
        # rows beside it are the rows it held that day and the date is what the
        # attribution promises.
        sources = [
            carried for carried in (held.sources if held else []) if carried.title != source.title
        ]
        sources = [*sources, source]
        self.write(
            ChartFile(
                chart=chart,
                year=year,
                sources=sources,
                entries=(held.entries if held else []) + fresh,
            )
        )
        return len(fresh)


def _song(entry: ChartEntry) -> tuple[str, str]:
    """What makes two rows the same recording, however either spells it."""
    return (core_title(entry.title), core_artist(entry.artist))
