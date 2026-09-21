"""The corpus writes stable bytes — spec §AC 9."""

import json

from jukebox.charts import Chart, ChartEntry, ChartFile, Corpus, EntryKind


def a_file() -> ChartFile:
    """A two-entry chart file whose entries are out of rank order."""
    return ChartFile(
        chart=Chart.HOT_100,
        year=1985,
        kind=EntryKind.RANKED,
        source="Billboard Year-End Hot 100 singles of 1985",
        retrieved="2026-09-06",
        entries=[
            ChartEntry(kind=EntryKind.RANKED, title="B", artist="b", rank=2),
            ChartEntry(kind=EntryKind.RANKED, title="A", artist="a", rank=1),
        ],
    )


def test_entries_are_written_in_rank_order(tmp_path):
    Corpus(tmp_path).write(a_file())
    written = json.loads((tmp_path / "hot-100" / "1985.json").read_text())
    assert [e["rank"] for e in written["entries"]] == [1, 2]


def test_writing_twice_produces_identical_bytes(tmp_path):
    corpus = Corpus(tmp_path)
    corpus.write(a_file())
    first = (tmp_path / "hot-100" / "1985.json").read_bytes()
    corpus.write(a_file())
    assert (tmp_path / "hot-100" / "1985.json").read_bytes() == first


def test_the_file_ends_in_a_newline_and_is_indented(tmp_path):
    Corpus(tmp_path).write(a_file())
    raw = (tmp_path / "hot-100" / "1985.json").read_text()
    assert raw.endswith("\n")
    assert "\n  " in raw


def test_a_written_file_reads_back_equal(tmp_path):
    corpus = Corpus(tmp_path)
    corpus.write(a_file())
    assert corpus.read(Chart.HOT_100, 1985).entries[0].title == "A"


def test_a_written_chart_file_records_where_it_came_from(tmp_path):
    """The source and date are the CC BY-SA attribution.

    The corpus is not committed, so nothing in version control carries this;
    the obligation attaches to the file wherever it is written.
    """
    Corpus(tmp_path).write(a_file())
    written = json.loads((tmp_path / "hot-100" / "1985.json").read_text())
    assert written["source"] == "Billboard Year-End Hot 100 singles of 1985"
    assert written["retrieved"] == "2026-09-06"
