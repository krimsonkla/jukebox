"""The console script is wired to the app."""

from unittest import mock

from jukebox.cli import app, main


def test_main_runs_the_app():
    with mock.patch.object(app, "__call__") as invoked:
        with mock.patch("jukebox.cli.app", invoked):
            main()
    assert invoked.called
