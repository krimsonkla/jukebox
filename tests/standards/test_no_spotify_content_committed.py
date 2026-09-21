"""What may and may not enter version control.

Two different reasons, one rule each. Spotify's developer terms permit only
temporary caching of its content and forbid storing it in a database, so no
Spotify identifier may be committed anywhere. The chart corpus is a different
question: Wikipedia's text is CC BY-SA and freely redistributable, but the
corpus is a machine-readable mirror of two decades of a commercial chart
compilation, which is a further step than citing the facts it holds. It is a
build artifact, rebuilt in seconds, so it stays out.
"""

import pathlib
import re
import subprocess

import pytest

from jukebox.charts.fetch import corpus_root
from jukebox.paths import Paths
from jukebox.reconcile import ledger_root
from jukebox.resolve import resolutions_root

ROOT = pathlib.Path(__file__).resolve().parents[2]


def tracked() -> list[str]:
    """Every path git tracks."""
    listed = subprocess.run(
        ["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=True
    )
    return listed.stdout.split()


def test_every_store_defaults_outside_the_repository():
    """Nothing the user owns or the tool caches may default into a checkout."""
    for resolved in (resolutions_root(), corpus_root(), ledger_root(), Paths.resolve().specs):
        assert resolved.is_absolute(), resolved
        assert ROOT not in resolved.parents and resolved != ROOT, resolved


def test_no_resolution_file_is_tracked():
    assert [path for path in tracked() if "resolutions" in path] == []


def test_no_chart_corpus_file_is_tracked():
    assert [path for path in tracked() if path.startswith("data/charts/")] == []


def test_the_corpus_and_the_caches_are_ignored_wherever_they_are_written():
    ignored = subprocess.run(
        [
            "git",
            "check-ignore",
            "data/charts/hot-100/1985.json",
            "data/resolutions/hot-100/1985.json",
            ".jukebox/token.json",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert ignored.returncode == 0
    assert len(ignored.stdout.split()) == 3


# Scanning only data/ and specs/ meant scanning nothing, since neither is
# tracked any more — a guard that passes because it was handed an empty list.
# Every tracked text file is checked instead, which cannot become vacuous.
SKIP = ("tests/fixtures/", "uv.lock", "devenv.lock", "LICENSE")


def scannable() -> list[str]:
    """Every tracked file whose content this guard can meaningfully read."""
    return [
        path
        for path in tracked()
        if not path.startswith(SKIP) and (ROOT / path).suffix not in {".html", ".png"}
    ]


def test_the_scan_covers_something():
    # The guard this replaces ran against an empty parametrisation and passed.
    assert len(scannable()) > 50


# A concrete identifier, not the prefix. Source legitimately builds a link out of
# `https://open.spotify.com/playlist/` + an id; what may not be committed is an
# id, which is a base62 string of 22 characters.
IDENTIFIER = re.compile(
    r"(?:spotify:(?:track|playlist|album):|open\.spotify\.com/\w+/)[0-9A-Za-z]{22}"
)


@pytest.mark.parametrize("path", scannable())
def test_no_tracked_file_carries_a_spotify_identifier(path):
    found = IDENTIFIER.search((ROOT / path).read_text(encoding="utf-8", errors="ignore"))
    assert found is None, f"{path} carries {found.group(0) if found else ''}"


def test_the_notice_records_every_service_the_code_talks_to():
    notice = (ROOT / "NOTICE.md").read_text(encoding="utf-8")
    for service in ("Wikipedia", "Billboard", "MusicBrainz", "Spotify"):
        assert service in notice
