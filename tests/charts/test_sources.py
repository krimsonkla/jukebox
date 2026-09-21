"""ChartSource is the only thing that touches the network — spec §Design."""

import httpx
import pytest
import respx

from jukebox.charts import MediaWikiSource, PageNotFound
from jukebox.net import RetryingClient, TransientFailure

API = "https://en.wikipedia.org/w/api.php"


def source() -> MediaWikiSource:
    """A source that neither sleeps nor waits between retries."""
    return MediaWikiSource(RetryingClient(sleep=lambda _: None), sleep=lambda _: None)


def test_fixture_source_serves_a_committed_page(fixture_source):
    assert "<table" in fixture_source.fetch("Billboard Year-End Hot 100 singles of 1985")


def test_fixture_source_names_the_page_it_lacks(fixture_source):
    with pytest.raises(PageNotFound, match="No Such Page"):
        fixture_source.fetch("No Such Page")


@respx.mock
def test_mediawiki_source_requests_rendered_html():
    route = respx.get(API).mock(
        return_value=httpx.Response(200, json={"parse": {"text": "<table/>"}})
    )
    assert source().fetch("A Page") == "<table/>"
    request = route.calls.last.request
    assert request.url.params["action"] == "parse"
    assert request.url.params["prop"] == "text"
    assert request.url.params["page"] == "A Page"
    assert "jukebox" in request.headers["user-agent"]


@respx.mock
def test_mediawiki_source_raises_on_a_missing_page():
    respx.get(API).mock(return_value=httpx.Response(200, json={"error": {"code": "missingtitle"}}))
    with pytest.raises(PageNotFound, match="Gone"):
        source().fetch("Gone")


@respx.mock
def test_a_transient_failure_is_waited_out_rather_than_raised():
    # Publishing multiplies the caller, so the highest-volume client is the one
    # that most needs to wait rather than give up.
    respx.get(API).mock(
        side_effect=[httpx.Response(503), httpx.Response(200, json={"parse": {"text": "<i/>"}})]
    )
    assert source().fetch("A Page") == "<i/>"


@respx.mock
def test_an_upstream_that_stays_down_is_reported_with_its_advice():
    respx.get(API).mock(return_value=httpx.Response(503))
    with pytest.raises(TransientFailure, match="continue from what was saved"):
        source().fetch("A Page")


@respx.mock
def test_the_fetch_paces_itself_between_pages():
    waited = []
    respx.get(API).mock(return_value=httpx.Response(200, json={"parse": {"text": "<i/>"}}))
    MediaWikiSource(RetryingClient(sleep=lambda _: None), sleep=waited.append).fetch("A Page")
    assert waited and all(pause > 0 for pause in waited)
