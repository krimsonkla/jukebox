"""Where things live, and which of them you can safely delete.

Resolving against the working directory meant running the command from
elsewhere produced a second, empty everything, and it put the user's own specs
inside the project's checkout, where they were neither the project's to ship nor
the user's to find.
"""

import pathlib

from jukebox.paths import Paths

HOUSE = pathlib.Path("/home/someone")


def test_jukebox_home_puts_everything_under_one_directory():
    paths = Paths.resolve({"JUKEBOX_HOME": "/w"}, home=HOUSE)
    assert paths.specs == pathlib.Path("/w/specs")
    assert paths.ledger == pathlib.Path("/w/ledger")
    assert paths.credentials == pathlib.Path("/w")
    assert paths.charts == pathlib.Path("/w/cache/charts")
    assert paths.resolutions == pathlib.Path("/w/cache/resolutions")


def test_jukebox_home_expands_a_tilde():
    assert (
        Paths.resolve({"JUKEBOX_HOME": "~/w"}, home=HOUSE).data == pathlib.Path("~/w").expanduser()
    )


def test_the_xdg_variables_are_honoured():
    paths = Paths.resolve({"XDG_DATA_HOME": "/d", "XDG_CACHE_HOME": "/c"}, home=HOUSE)
    assert paths.specs == pathlib.Path("/d/jukebox/specs")
    assert paths.charts == pathlib.Path("/c/jukebox/charts")


def test_without_any_variable_it_falls_back_to_the_conventional_directories():
    paths = Paths.resolve({}, home=HOUSE)
    assert paths.data == HOUSE / ".local" / "share" / "jukebox"
    assert paths.cache == HOUSE / ".cache" / "jukebox"


def test_jukebox_home_wins_over_the_xdg_variables():
    paths = Paths.resolve(
        {"JUKEBOX_HOME": "/w", "XDG_DATA_HOME": "/d", "XDG_CACHE_HOME": "/c"}, home=HOUSE
    )
    assert paths.data == pathlib.Path("/w")


def test_what_can_be_deleted_is_separate_from_what_cannot():
    # The corpus and the resolutions are rebuilt by a command; the specs, the
    # ledger and the refresh token are not. `rm -rf` on the cache must not
    # reach anything a person would have to rewrite by hand.
    paths = Paths.resolve({}, home=HOUSE)
    for regenerable in (paths.charts, paths.resolutions):
        assert paths.cache in regenerable.parents
    for irreplaceable in (paths.specs, paths.ledger, paths.credentials):
        assert paths.cache not in irreplaceable.parents
        assert irreplaceable == paths.data or paths.data in irreplaceable.parents


def test_nothing_resolves_relative_to_the_working_directory():
    for resolved in Paths.resolve({}, home=HOUSE), Paths.resolve({"JUKEBOX_HOME": "/w"}):
        for path in (
            resolved.specs,
            resolved.ledger,
            resolved.charts,
            resolved.resolutions,
            resolved.credentials,
        ):
            assert path.is_absolute(), path
