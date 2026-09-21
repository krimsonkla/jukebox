"""A refresh that returns no refresh token must not lose the one held."""

import datetime as dt

from jukebox.oauth import Token

NOW = dt.datetime(2026, 9, 7, 12, 0, tzinfo=dt.UTC)


def granted(**over) -> dict:
    """A token endpoint response."""
    return {"access_token": "a", "expires_in": 3600, "scope": "s1 s2", "refresh_token": "r"} | over


def test_expiry_is_measured_from_the_grant():
    assert Token.issued(granted(), NOW).expires_at == NOW + dt.timedelta(hours=1)


def test_a_refresh_without_a_new_refresh_token_carries_the_old_one():
    held = Token.issued(granted(), NOW)
    renewed = Token.issued({"access_token": "b", "expires_in": 3600}, NOW, previous=held)
    assert renewed.refresh_token == "r"
    assert renewed.access_token == "b"


def test_a_refresh_that_does_return_one_replaces_it():
    held = Token.issued(granted(), NOW)
    renewed = Token.issued(granted(refresh_token="r2"), NOW, previous=held)
    assert renewed.refresh_token == "r2"


def test_a_first_grant_with_no_refresh_token_stores_an_empty_one():
    assert Token.issued({"access_token": "a", "expires_in": 60}, NOW).refresh_token == ""


def test_a_token_is_expired_a_minute_before_it_actually_expires():
    token = Token.issued(granted(expires_in=120), NOW)
    assert token.expired(NOW + dt.timedelta(seconds=61))
    assert not token.expired(NOW + dt.timedelta(seconds=30))
