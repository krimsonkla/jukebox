"""The refresh token is a credential: owner-readable only, never in the repo."""

import datetime as dt
import stat

from jukebox.oauth import Token, TokenStore

NOW = dt.datetime(2026, 9, 7, 12, 0, tzinfo=dt.UTC)


def a_token() -> Token:
    """A stored token."""
    return Token(access_token="a", refresh_token="r", expires_at=NOW, scope="s")


def test_nothing_stored_reads_as_nothing(tmp_path):
    assert TokenStore(tmp_path, "spotify").load() is None


def test_a_saved_token_reads_back(tmp_path):
    store = TokenStore(tmp_path, "spotify")
    store.save(a_token())
    assert store.load().refresh_token == "r"


def test_the_token_file_is_readable_only_by_its_owner(tmp_path):
    store = TokenStore(tmp_path, "spotify")
    store.save(a_token())
    assert stat.S_IMODE(store.path.stat().st_mode) == 0o600


def test_rewriting_keeps_the_permissions(tmp_path):
    store = TokenStore(tmp_path, "spotify")
    store.save(a_token())
    store.path.chmod(0o644)
    store.save(a_token())
    assert stat.S_IMODE(store.path.stat().st_mode) == 0o600


def test_each_provider_keeps_its_own_token(tmp_path):
    TokenStore(tmp_path, "spotify").save(a_token())
    assert TokenStore(tmp_path, "tidal").load() is None


def test_clearing_reports_whether_there_was_anything(tmp_path):
    store = TokenStore(tmp_path, "spotify")
    assert store.clear() is False
    store.save(a_token())
    assert store.clear() is True
    assert store.load() is None


def test_the_directory_is_created_on_demand(tmp_path):
    store = TokenStore(tmp_path / "deep" / "nested", "spotify")
    store.save(a_token())
    assert store.load() is not None


def test_a_token_minted_for_another_application_is_declined(tmp_path):
    # Redeeming it fails at refresh with an error explaining none of this, so
    # the store declines and the caller is told to authorize instead.
    TokenStore(tmp_path, "spotify", "app-one").save(a_token())
    assert TokenStore(tmp_path, "spotify", "app-two").load() is None
    assert TokenStore(tmp_path, "spotify", "app-one").load() is not None


def test_a_token_saved_before_applications_were_recorded_still_loads(tmp_path):
    # Nobody should have to re-authorize because a field was added.
    TokenStore(tmp_path, "spotify").save(a_token())
    assert TokenStore(tmp_path, "spotify", "app-one").load() is not None


def test_saving_stamps_the_application_that_obtained_it(tmp_path):
    store = TokenStore(tmp_path, "spotify", "app-one")
    store.save(a_token())
    assert store.load().client_id == "app-one"
