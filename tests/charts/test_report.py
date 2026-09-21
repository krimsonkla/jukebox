"""Absence is data — spec §AC 5."""

from jukebox.charts import Chart, CoverageReport, Gap, GapReason, Resolved


def test_a_report_names_each_gap_and_its_reason():
    report = CoverageReport(
        year=1985,
        resolved=[Resolved(chart=Chart.HOT_100, title="t", entries=100)],
        gaps=[Gap(chart=Chart.MODERN_ROCK, year=1985, reason=GapReason.CHART_DID_NOT_EXIST)],
    )
    rendered = report.render()
    assert "hot-100" in rendered and "100" in rendered
    assert "modern-rock" in rendered
    assert "did not exist" in rendered


def test_a_year_with_gaps_is_still_a_success():
    report = CoverageReport(
        year=1985,
        resolved=[],
        gaps=[Gap(chart=Chart.MODERN_ROCK, year=1985, reason=GapReason.NO_ARTICLE)],
    )
    assert report.ok is True
