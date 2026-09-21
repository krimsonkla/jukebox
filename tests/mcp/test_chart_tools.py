"""The corpus is exposed as primitives, not as a finished answer."""

from jukebox.charts.entry_filter import EntryFilter
from jukebox.mcp import ChartQuery
from jukebox.mcp.tools import list_charts, query_charts


def test_coverage_names_each_chart_and_its_years(workspace):
    found = list_charts(workspace)
    assert found["charts"] == {"hot-100": [1985], "country": [1985]}
    assert found["empty"] is False


def test_a_year_range_with_no_corpus_reports_empty(workspace):
    assert list_charts(workspace, (1990, 1999))["empty"] is True


def test_a_query_returns_rows_rather_than_a_playlist(workspace):
    found = query_charts(workspace, ChartQuery(charts=["hot-100"], years=(1985, 1985)))
    assert found["total"] == 3
    assert found["entries"][0]["title"] == "A"
    assert found["entries"][0]["rank"] == 1


def test_a_rank_ceiling_narrows_a_year_end_chart(workspace):
    assert (
        query_charts(
            workspace,
            ChartQuery(charts=["hot-100"], years=(1985, 1985), rows=EntryFilter(max_rank=2)),
        )["total"]
        == 2
    )


def test_a_rank_ceiling_leaves_number_ones_alone(workspace):
    found = query_charts(
        workspace, ChartQuery(charts=["country"], years=(1985, 1985), rows=EntryFilter(max_rank=1))
    )
    assert found["total"] == 1
    assert found["entries"][0]["weeks_at_number_one"] == 2


def test_an_artist_filter_matches_loosely(workspace):
    assert (
        query_charts(
            workspace,
            ChartQuery(charts=["hot-100"], years=(1985, 1985), rows=EntryFilter(artist="X")),
        )["total"]
        == 2
    )


def test_several_charts_are_queried_together(workspace):
    found = query_charts(workspace, ChartQuery(charts=["hot-100", "country"], years=(1985, 1985)))
    assert {row["chart"] for row in found["entries"]} == {"hot-100", "country"}


def test_a_year_with_no_file_is_skipped_rather_than_failing(workspace):
    assert query_charts(workspace, ChartQuery(charts=["hot-100"], years=(1984, 1986)))["total"] == 3


def test_a_long_result_is_truncated_and_says_so(workspace):
    found = query_charts(workspace, ChartQuery(charts=["hot-100"], years=(1985, 1985), limit=1))
    assert len(found["entries"]) == 1 and found["truncated"] is True
    assert found["total"] == 3
