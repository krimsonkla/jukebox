"""A catalogue that answers from a fixed list, with no network."""

import datetime as dt

import pytest

from jukebox.ports import TrackMatch


class FakeCatalog:
    """Returns prepared candidates and records what it was asked."""

    def __init__(self, by_query=None, by_isrc=None) -> None:
        self._by_query = by_query or {}
        self._by_isrc = by_isrc or {}
        self.searched: list[tuple[str, str]] = []

    def search(self, title: str, artist: str) -> list[TrackMatch]:
        """Candidates prepared for this title and artist."""
        self.searched.append((title, artist))
        return list(self._by_query.get((title, artist), []))

    def by_isrc(self, isrc: str) -> list[TrackMatch]:
        """Candidates prepared for this identifier."""
        return list(self._by_isrc.get(isrc, []))


class FakeIsrcs:
    """Returns prepared identifiers."""

    def __init__(self, mapping=None) -> None:
        self._mapping = mapping or {}

    def isrcs_for(self, title: str, artist: str) -> tuple[str, ...]:
        """Identifiers prepared for this recording."""
        return self._mapping.get((title, artist), ())


@pytest.fixture(name="track")
def _track():
    def make(title, artist, album="", year=1985) -> TrackMatch:
        return TrackMatch(
            uri=f"spotify:track:{abs(hash((title, artist, album))) % 10**10}",
            title=title,
            artist=artist,
            album=album,
            released=dt.date(year, 1, 1),
        )

    return make
