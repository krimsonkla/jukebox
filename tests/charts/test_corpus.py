"""The corpus writes stable bytes — spec §AC 9."""

import json

from jukebox.charts import Chart, ChartEntry, ChartFile, Corpus, EntryKind
from jukebox.charts.attribution import Attribution


def a_file() -> ChartFile:
    """A two-entry chart file whose entries are out of rank order."""
    return ChartFile(
        chart=Chart.HOT_100,
        year=1985,
        sources=[
            Attribution(title="Billboard Year-End Hot 100 singles of 1985", retrieved="2026-09-06")
        ],
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
    assert written["sources"] == [
        {"title": "Billboard Year-End Hot 100 singles of 1985", "retrieved": "2026-09-06"}
    ]


def peak(title: str, rank: int) -> ChartEntry:
    """A placing, as an artist's own article records one."""
    return ChartEntry(kind=EntryKind.PEAK, title=title, artist="An Act", rank=rank)


def ranked(title: str, rank: int) -> ChartEntry:
    """A year-end position."""
    return ChartEntry(kind=EntryKind.RANKED, title=title, artist="An Act", rank=rank)


def source(title: str) -> Attribution:
    """One page, read today."""
    return Attribution(title=title, retrieved="2026-09-29")


def test_refetching_a_chart_keeps_the_placings_another_page_contributed(tmp_path):
    corpus = Corpus(tmp_path)
    corpus.refresh(Chart.HOT_100, 1985, [ranked("A", 1)], source("the chart"))
    corpus.merge(Chart.HOT_100, 1985, [peak("B", 30)], source("a discography"))
    corpus.refresh(Chart.HOT_100, 1985, [ranked("A", 1)], source("the chart"))
    held = corpus.read(Chart.HOT_100, 1985)
    assert sorted(entry.title for entry in held.entries) == ["A", "B"]
    assert sorted(carried.title for carried in held.sources) == ["a discography", "the chart"]


def test_a_chart_page_wins_where_it_names_the_same_song(tmp_path):
    corpus = Corpus(tmp_path)
    corpus.merge(Chart.HOT_100, 1985, [peak("A", 30)], source("a discography"))
    corpus.refresh(Chart.HOT_100, 1985, [ranked("A", 1)], source("the chart"))
    held = corpus.read(Chart.HOT_100, 1985)
    assert [(e.title, e.kind) for e in held.entries] == [("A", EntryKind.RANKED)]


def test_a_chart_page_alone_is_credited_alone(tmp_path):
    corpus = Corpus(tmp_path)
    corpus.merge(Chart.HOT_100, 1985, [peak("A", 30)], source("a discography"))
    corpus.refresh(Chart.HOT_100, 1985, [ranked("A", 1)], source("the chart"))
    assert [c.title for c in corpus.read(Chart.HOT_100, 1985).sources] == ["the chart"]


def test_a_song_listed_twice_in_one_reading_is_stored_once(tmp_path):
    corpus = Corpus(tmp_path)
    added = corpus.merge(Chart.HOT_100, 1985, [peak("A", 7), peak("A", 9)], source("a discography"))
    assert added == 1
    assert len(corpus.read(Chart.HOT_100, 1985).entries) == 1


def test_reading_a_page_again_records_the_day_it_was_last_read(tmp_path):
    corpus = Corpus(tmp_path)
    corpus.merge(Chart.HOT_100, 1985, [peak("A", 30)], source("a discography"))
    corpus.merge(
        Chart.HOT_100,
        1985,
        [peak("B", 12)],
        Attribution(title="a discography", retrieved="2027-01-04"),
    )
    held = corpus.read(Chart.HOT_100, 1985)
    assert len(held.sources) == 1
    assert held.sources[0].retrieved.isoformat() == "2027-01-04"
