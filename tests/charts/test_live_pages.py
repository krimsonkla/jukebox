"""Every registry title still resolves — run deliberately, not in the suite.

This is how a Wikipedia rename is caught. It is the only test that leaves the
machine, which is why it carries the marker.
"""

import pytest

from jukebox.charts import Grid, MediaWikiSource, Registry
from jukebox.charts.fetch import map_page

pytestmark = pytest.mark.network


@pytest.mark.parametrize("year", list(range(1980, 2000)))
def test_every_declared_chart_still_parses(year):
    source = MediaWikiSource()
    for page in Registry.billboard().resolved(year):
        entries = map_page(page, Grid.of(source.fetch(page.title)), year)
        assert entries, f"{page.title} parsed to nothing for {page.chart.slug} {year}"
