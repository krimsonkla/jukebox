"""The challenge is the verifier's S256 digest — RFC 7636."""

import base64
import hashlib

from jukebox.oauth import Pkce


def test_a_verifier_is_within_the_length_the_spec_allows():
    assert 43 <= len(Pkce.generate().verifier) <= 128


def test_two_attempts_do_not_share_a_verifier():
    assert Pkce.generate().verifier != Pkce.generate().verifier


def test_the_challenge_is_the_unpadded_base64url_sha256():
    pkce = Pkce(verifier="a" * 64)
    digest = hashlib.sha256(b"a" * 64).digest()
    assert pkce.challenge == base64.urlsafe_b64encode(digest).decode().rstrip("=")
    assert "=" not in pkce.challenge
