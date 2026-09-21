"""The ports are contracts, and a bare contract implements nothing.

They exist so that nothing above them names a music service; these assert the
shape an adapter has to satisfy rather than any adapter's behaviour.
"""

import pytest

from jukebox.ports import (
    Credentials,
    IsrcSource,
    MusicCatalog,
    PlaylistService,
    ProviderAuth,
)


def test_provider_auth_declares_the_three_operations():
    for operation in ("login", "status", "logout"):
        with pytest.raises(NotImplementedError):
            getattr(ProviderAuth, operation)(object())


def test_credentials_declares_a_bearer():
    with pytest.raises(NotImplementedError):
        Credentials.bearer(object())


def test_the_catalogue_declares_search_and_isrc_lookup():
    for operation, args in (("search", ("t", "a")), ("by_isrc", ("X",))):
        with pytest.raises(NotImplementedError):
            getattr(MusicCatalog, operation)(object(), *args)


def test_the_isrc_source_declares_a_lookup():
    with pytest.raises(NotImplementedError):
        IsrcSource.isrcs_for(object(), "t", "a")


def test_the_playlist_service_declares_the_four_operations_a_reconciler_needs():
    # Four, because a reconciler settles the whole ordering before writing, so
    # replacing a list is the only mutation it needs.
    for operation, args in (
        ("create", ("name",)),
        ("find", ("p1",)),
        ("items", ("p1",)),
        ("replace", ("p1", [])),
    ):
        with pytest.raises(NotImplementedError):
            getattr(PlaylistService, operation)(object(), *args)
