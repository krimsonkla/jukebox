"""The redirect catcher serves exactly one request, on the loopback interface."""

import socket
import threading

import httpx
import pytest

from jukebox.oauth import AuthorizationTimedOut, Loopback


def free_port() -> int:
    """A port nothing is listening on."""
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return probe.getsockname()[1]


def catch(path: str):
    """Run the loopback and drive one request through it."""
    port = free_port()
    loopback = Loopback("127.0.0.1", port)
    caught = {}

    def run():
        caught["callback"] = loopback.wait()

    thread = threading.Thread(target=run)
    thread.start()
    response = httpx.get(f"http://127.0.0.1:{port}{path}", timeout=5)
    thread.join(timeout=5)
    return caught["callback"], response


def test_a_code_and_state_are_captured():
    callback, response = catch("/callback?code=abc&state=xyz")
    assert (callback.code, callback.state, callback.error) == ("abc", "xyz", None)
    assert response.status_code == 200
    assert b"close this tab" in response.content


def test_a_denial_is_captured_as_an_error():
    callback, _ = catch("/callback?error=access_denied&state=xyz")
    assert callback.error == "access_denied"
    assert callback.code is None


def test_a_bare_redirect_carries_nothing():
    callback, _ = catch("/callback")
    assert (callback.code, callback.state, callback.error) == (None, None, None)


def test_waiting_gives_up_rather_than_blocking_forever():
    # An agent-driven login blocks a tool call while it waits, so a person who
    # never reaches the consent page must still get an answer.
    with pytest.raises(AuthorizationTimedOut, match="redirect port"):
        Loopback("127.0.0.1", free_port(), timeout=0.05).wait()


def test_a_silent_connection_does_not_hold_the_login_open_for_ever():
    """The accept had a deadline and the read did not.

    So the stated timeout worked when nobody connected and was inert the moment
    anybody did — which is the path that matters.
    """
    port = free_port()
    loopback = Loopback("127.0.0.1", port, timeout=0.2).bind()
    with socket.create_connection(("127.0.0.1", port), timeout=5):
        with pytest.raises(AuthorizationTimedOut):
            loopback.wait()


def test_binding_happens_before_anyone_is_sent_to_consent():
    # A squatter on the port would otherwise take the redirect while the user
    # consents for nothing.
    port = free_port()
    first = Loopback("127.0.0.1", port).bind()
    with pytest.raises(OSError):
        Loopback("127.0.0.1", port).bind()
    first.close()


def test_closing_an_unbound_catcher_is_harmless():
    Loopback("127.0.0.1", free_port()).close()
