"""The consent URL carries the challenge, never the verifier."""

import urllib.parse

from jukebox.oauth import AuthorizationRequest, Pkce


def params() -> dict[str, str]:
    """The query of a built consent URL."""
    request = AuthorizationRequest(
        endpoint="https://accounts.example/authorize",
        client_id="cid",
        redirect_uri="http://127.0.0.1:8888/callback",
        scopes=("a", "b"),
        pkce=Pkce(verifier="v" * 64),
        state="st",
    )
    return dict(urllib.parse.parse_qsl(urllib.parse.urlparse(request.url()).query))


def test_it_requests_a_code_with_an_s256_challenge():
    query = params()
    assert query["response_type"] == "code"
    assert query["code_challenge_method"] == "S256"
    assert query["code_challenge"] == Pkce(verifier="v" * 64).challenge


def test_the_verifier_never_appears_in_the_url():
    assert "v" * 64 not in str(params())


def test_scopes_are_space_separated_and_state_is_carried():
    query = params()
    assert query["scope"] == "a b"
    assert query["state"] == "st"
