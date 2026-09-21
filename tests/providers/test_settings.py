"""The callback may only ever be offered to the loopback interface."""

import pytest
from pydantic import ValidationError

from jukebox.providers.spotify import SpotifySettings


def test_the_default_redirect_is_a_loopback_literal():
    assert SpotifySettings(client_id="c").redirect_uri == "http://127.0.0.1:8888/callback"


@pytest.mark.parametrize("host", ["127.0.0.1", "::1"])
def test_a_loopback_address_is_accepted(host):
    assert SpotifySettings(client_id="c", redirect_host=host).redirect_host == host


@pytest.mark.parametrize("host", ["0.0.0.0", "192.168.1.10", "localhost", "example.com"])
def test_anything_routable_is_refused(host):
    # The callback carries an authorization code, and an environment variable
    # must not be able to offer it to the network.
    with pytest.raises(ValidationError, match="loopback"):
        SpotifySettings(client_id="c", redirect_host=host)
