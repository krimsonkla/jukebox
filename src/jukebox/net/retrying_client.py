"""An HTTP client that waits out the failures worth waiting out.

A rate limit and a bad gateway are the two answers a long backfill will meet,
and both usually pass. Letting either reach the caller ends a run that was
minutes from finishing.
"""

import datetime as dt
import email.utils
import time
from collections.abc import Callable

import httpx

from jukebox.net.errors import Throttled, TransientFailure
from jukebox.net.pacer import Pacer
from jukebox.net.retry_policy import RetryPolicy

RETRYABLE = frozenset({429, 500, 502, 503, 504})


def _utcnow() -> dt.datetime:
    return dt.datetime.now(dt.UTC)


def _reason(response: httpx.Response) -> str | None:
    """What the service called its refusal, where the body says.

    Read defensively: a refusal is exactly when a body is least likely to be
    the shape the documentation promises, and losing the whole answer over a
    missing field would discard the delay as well as the reason.
    """
    try:
        body = response.json()
    except ValueError:
        return None
    if not isinstance(body, dict):
        return None
    error = body.get("error")
    named = error.get("reason") if isinstance(error, dict) else body.get("reason")
    return named if isinstance(named, str) else None


class RetryingClient:
    """Repeats a request while the answer is one that tends to change."""

    def __init__(
        self,
        client: httpx.Client | None = None,
        sleep: Callable[[float], None] = time.sleep,
        policy: RetryPolicy | None = None,
        pacer: Pacer | None = None,
        now: Callable[[], dt.datetime] = _utcnow,
    ) -> None:
        self._client = client or httpx.Client(timeout=30.0)
        self._sleep = sleep
        self._policy = policy or RetryPolicy()
        self._pacer = pacer or Pacer(0.0)
        self._now = now

    def get(
        self, url: str, params: dict | None = None, headers: dict | None = None
    ) -> httpx.Response:
        """The response, having waited out any retryable status."""
        return self._attempt(lambda: self._client.get(url, params=params, headers=headers), url)

    def send(
        self,
        method: str,
        url: str,
        json: dict | None = None,
        headers: dict | None = None,
    ) -> httpx.Response:
        """A write, having waited out any retryable status.

        A write is retried on exactly the statuses a read is. The alternative
        is a rate limit part-way through a multi-request write, which leaves
        the thing being written half-changed.
        """
        return self._attempt(
            lambda: self._client.request(method, url, json=json, headers=headers), url
        )

    def _attempt(self, call, url: str) -> httpx.Response:
        response = None
        for attempt in range(self._policy.attempts):
            self._pacer.wait()
            response = call()
            if response.status_code not in RETRYABLE:
                return response
            asked = self._requested(response)
            if asked is not None and self._policy.too_long(asked):
                raise Throttled(url, asked, _reason(response))
            if attempt + 1 < self._policy.attempts:
                self._sleep(self._policy.pause(attempt) if asked is None else asked)
        raise TransientFailure(url, response.status_code, self._policy.attempts)

    def _requested(self, response: httpx.Response) -> float | None:
        """The delay named by Retry-After, in seconds, or None if it named none.

        The header is either a count of seconds or an HTTP date. A value in
        neither form is read as the ceiling rather than as absent, so an
        unparseable refusal slows the caller down instead of speeding it up.
        """
        header = response.headers.get("Retry-After")
        if header is None:
            return None
        text = header.strip()
        if text.isdigit():
            return float(text)
        try:
            when = email.utils.parsedate_to_datetime(text)
        except (TypeError, ValueError):
            return self._policy.ceiling
        if when.tzinfo is None:
            when = when.replace(tzinfo=dt.UTC)
        return max(0.0, (when - self._now()).total_seconds())
