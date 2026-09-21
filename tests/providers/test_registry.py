"""Adapters are built from an identifier supplied at runtime."""

import pytest

from jukebox.providers.registry import DEFAULT, PROVIDERS, UnknownProvider, named


def test_spotify_is_registered_and_is_the_default():
    assert DEFAULT in PROVIDERS


def test_every_provider_says_what_it_needs():
    for provider in PROVIDERS.values():
        assert provider.needs.strip()
        assert provider.name == provider.name.lower()


def test_an_unknown_provider_lists_the_known_ones():
    with pytest.raises(UnknownProvider, match="spotify"):
        named("8-track")


def test_each_adapter_is_built_from_a_client_id_rather_than_the_environment():
    # The identifier can arrive mid-conversation, so nothing may require it to
    # have been in the environment before the process started.
    provider = named(DEFAULT)
    for build in (provider.auth, provider.catalog, provider.playlists):
        assert build("cid") is not None
