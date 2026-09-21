"""A long backfill meets rate limits and bad gateways; both usually pass."""

import datetime as dt

import httpx
import pytest
import respx

from jukebox.net import Pacer, RetryingClient, RetryPolicy, Throttled, TransientFailure

URL = "https://service.example/thing"
NOW = dt.datetime(2026, 10, 21, 7, 0, tzinfo=dt.UTC)


def client(waited: list[float], attempts: int = 4) -> RetryingClient:
    """A client that records what it would have slept.

    The jitter is pinned to its own cap so a backoff assertion names one value
    rather than a range; that the default spreads instead has its own test.
    """
    return RetryingClient(
        sleep=waited.append,
        policy=RetryPolicy(attempts=attempts, backoff=1.0, jitter=lambda cap: cap),
        now=lambda: NOW,
    )


@respx.mock
def test_a_good_response_is_returned_without_waiting():
    respx.get(URL).mock(return_value=httpx.Response(200, json={"ok": True}))
    waited = []
    assert client(waited).get(URL).json() == {"ok": True}
    assert not waited


@respx.mock
def test_a_rate_limit_is_retried_and_then_succeeds():
    respx.get(URL).mock(side_effect=[httpx.Response(429), httpx.Response(200, json={"ok": True})])
    waited = []
    assert client(waited).get(URL).status_code == 200
    assert waited == [1.0]


@respx.mock
def test_retry_after_is_honoured_over_the_backoff():
    respx.get(URL).mock(
        side_effect=[httpx.Response(429, headers={"Retry-After": "7"}), httpx.Response(200)]
    )
    waited = []
    client(waited).get(URL)
    assert waited == [7.0]


@respx.mock
def test_a_retry_after_date_is_honoured_as_the_seconds_until_it():
    # The header is either a count of seconds or an HTTP date; reading only the
    # first form makes the client retry sooner than the service asked.
    respx.get(URL).mock(
        side_effect=[
            httpx.Response(429, headers={"Retry-After": "Wed, 21 Oct 2026 07:00:30 GMT"}),
            httpx.Response(200),
        ]
    )
    waited = []
    client(waited).get(URL)
    assert waited == [30.0]


@respx.mock
def test_a_retry_after_date_already_past_waits_no_time_at_all():
    respx.get(URL).mock(
        side_effect=[
            httpx.Response(429, headers={"Retry-After": "Wed, 21 Oct 2026 06:00:00 GMT"}),
            httpx.Response(200),
        ]
    )
    waited = []
    client(waited).get(URL)
    assert waited == [0.0]


@respx.mock
def test_an_unparseable_retry_after_slows_the_caller_rather_than_speeding_it_up():
    respx.get(URL).mock(return_value=httpx.Response(429, headers={"Retry-After": "soon"}))
    with pytest.raises(TransientFailure):
        client([]).get(URL)


@respx.mock
def test_a_naive_retry_after_date_is_read_as_utc():
    respx.get(URL).mock(
        side_effect=[
            httpx.Response(429, headers={"Retry-After": "Wed, 21 Oct 2026 07:00:10"}),
            httpx.Response(200),
        ]
    )
    waited = []
    client(waited).get(URL)
    assert waited == [10.0]


@respx.mock
def test_a_bad_gateway_is_retried_because_it_ended_a_whole_backfill():
    respx.get(URL).mock(side_effect=[httpx.Response(502), httpx.Response(200)])
    waited = []
    assert client(waited).get(URL).status_code == 200


@respx.mock
def test_the_backoff_grows_between_attempts():
    respx.get(URL).mock(side_effect=[httpx.Response(503), httpx.Response(503), httpx.Response(200)])
    waited = []
    client(waited).get(URL)
    assert waited == [1.0, 2.0]


@respx.mock
def test_giving_up_says_what_to_do_and_carries_the_status():
    respx.get(URL).mock(return_value=httpx.Response(502))
    waited = []
    with pytest.raises(TransientFailure, match="continue from what was saved") as refused:
        client(waited).get(URL)
    assert refused.value.status == 502
    assert len(waited) == 3


@respx.mock
def test_a_client_error_is_not_retried():
    route = respx.get(URL).mock(return_value=httpx.Response(404))
    waited = []
    assert client(waited).get(URL).status_code == 404
    assert route.call_count == 1


@respx.mock
def test_a_write_is_retried_on_the_statuses_a_read_is():
    # A long playlist is more than one request, so a rate limit part-way through
    # would otherwise leave it truncated.
    route = respx.put(URL).mock(side_effect=[httpx.Response(429), httpx.Response(200)])
    waited = []
    assert client(waited).send("PUT", URL, json={"uris": []}).status_code == 200
    assert route.call_count == 2


@respx.mock
def test_a_write_that_keeps_failing_says_what_to_do():
    respx.post(URL).mock(return_value=httpx.Response(502))
    with pytest.raises(TransientFailure):
        client([]).send("POST", URL, json={})


@respx.mock
def test_a_write_carries_its_body_and_headers():
    route = respx.put(URL).mock(return_value=httpx.Response(200))
    client([]).send("PUT", URL, json={"uris": ["u:a"]}, headers={"Authorization": "Bearer t"})
    request = route.calls.last.request
    assert b'"uris"' in request.read()
    assert request.headers["authorization"] == "Bearer t"


@respx.mock
def test_a_retry_after_past_the_ceiling_refuses_instead_of_retrying():
    # Waiting whatever the header names hands the dial to the upstream, and
    # retrying inside the pause it asked for spends another request against the
    # window it is already refusing. Neither is worth doing.
    route = respx.get(URL).mock(return_value=httpx.Response(429, headers={"Retry-After": "86400"}))
    waited = []
    with pytest.raises(Throttled, match="asked for 86400s") as refused:
        client(waited).get(URL)
    assert refused.value.seconds == 86400.0
    assert route.call_count == 1
    assert not waited


@respx.mock
def test_refusing_says_how_long_to_wait_and_that_progress_was_kept():
    respx.get(URL).mock(return_value=httpx.Response(429, headers={"Retry-After": "600"}))
    with pytest.raises(Throttled, match="continue from what was saved"):
        client([]).get(URL)


@respx.mock
def test_a_retry_after_at_the_ceiling_is_still_waited_out():
    respx.get(URL).mock(
        side_effect=[httpx.Response(429, headers={"Retry-After": "60"}), httpx.Response(200)]
    )
    waited = []
    assert client(waited).get(URL).status_code == 200
    assert waited == [60.0]


@respx.mock
def test_the_default_backoff_is_jittered_so_failures_do_not_resynchronise():
    respx.get(URL).mock(side_effect=[httpx.Response(503), httpx.Response(200)])
    waited = []
    RetryingClient(sleep=waited.append, policy=RetryPolicy(backoff=8.0)).get(URL)
    assert 0.0 <= waited[0] <= 8.0


@respx.mock
def test_every_request_is_paced_including_the_retries():
    respx.get(URL).mock(side_effect=[httpx.Response(503), httpx.Response(200)])
    paced = []
    RetryingClient(
        sleep=lambda _: None,
        pacer=Pacer(2.0, sleep=paced.append, clock=lambda: 0.0),
    ).get(URL)
    assert paced == [2.0]


@respx.mock
def test_the_backoff_is_capped_too():
    respx.get(URL).mock(return_value=httpx.Response(503))
    waited = []
    with pytest.raises(TransientFailure):
        client(waited, attempts=12).get(URL)
    assert max(waited) == 60.0


@respx.mock
def test_the_default_clock_reads_a_retry_after_date_against_real_time():
    # A date already past yields no wait whatever the wall clock says, which is
    # what makes this assertion stable while still exercising the real clock.
    respx.get(URL).mock(
        side_effect=[
            httpx.Response(429, headers={"Retry-After": "Thu, 01 Jan 1970 00:00:00 GMT"}),
            httpx.Response(200),
        ]
    )
    waited = []
    RetryingClient(sleep=waited.append).get(URL)
    assert waited == [0.0]


@respx.mock
def test_a_refusal_carries_what_the_service_called_it():
    # A quota is a budget on how many requests are made and a rate limit is one
    # on how quickly; only the second is answered by slowing down.
    respx.get(URL).mock(
        return_value=httpx.Response(
            429,
            headers={"Retry-After": "86034"},
            json={"error": {"status": 429, "message": "quota", "reason": "QUOTA_EXCEEDED"}},
        )
    )
    with pytest.raises(Throttled, match="QUOTA_EXCEEDED") as refused:
        client([]).get(URL)
    assert refused.value.reason == "QUOTA_EXCEEDED"


@respx.mock
def test_a_spent_quota_says_that_slowing_down_will_not_help():
    respx.get(URL).mock(
        return_value=httpx.Response(
            429,
            headers={"Retry-After": "86034"},
            json={"error": {"reason": "QUOTA_EXCEEDED"}},
        )
    )
    with pytest.raises(Throttled, match="slowing down will not help"):
        client([]).get(URL)


@respx.mock
def test_a_reason_at_the_top_of_the_body_is_read_too():
    respx.get(URL).mock(
        return_value=httpx.Response(
            429, headers={"Retry-After": "700"}, json={"reason": "RATE_LIMIT"}
        )
    )
    with pytest.raises(Throttled) as refused:
        client([]).get(URL)
    assert refused.value.reason == "RATE_LIMIT"


@respx.mock
def test_a_refusal_with_no_body_still_carries_its_delay():
    # A refusal is when a body is least likely to be the shape documented, and
    # losing the delay over a missing field would be the worse trade.
    respx.get(URL).mock(return_value=httpx.Response(429, headers={"Retry-After": "700"}))
    with pytest.raises(Throttled) as refused:
        client([]).get(URL)
    assert refused.value.reason is None
    assert refused.value.seconds == 700.0


@respx.mock
def test_a_body_that_is_not_an_object_is_not_mistaken_for_a_reason():
    respx.get(URL).mock(
        return_value=httpx.Response(429, headers={"Retry-After": "700"}, json=["nope"])
    )
    with pytest.raises(Throttled) as refused:
        client([]).get(URL)
    assert refused.value.reason is None


@respx.mock
def test_a_reason_that_is_not_text_is_ignored():
    respx.get(URL).mock(
        return_value=httpx.Response(429, headers={"Retry-After": "700"}, json={"reason": 7})
    )
    with pytest.raises(Throttled) as refused:
        client([]).get(URL)
    assert refused.value.reason is None
