"""The corpus read as songs and artists rather than as lists.

A chart file answers "what was on this list". Every other question — did this
song cross over, what else did this artist chart, how many distinct recordings
are we about to look up — needs the same rows grouped by what they are about,
and grouping them at each call site is how the same song gets resolved four
times.

This is a projection, not a second source of truth: the corpus stays the fact
and the index is rebuilt from it.
"""

import dataclasses

from jukebox.charts.chart import Chart
from jukebox.charts.corpus import Corpus
from jukebox.songs.appearance import Appearance
from jukebox.songs.artist import Artist
from jukebox.songs.identity import Identity
from jukebox.songs.song import Song
from jukebox.text.artists import lead
from jukebox.text.normalize import core_artist


@dataclasses.dataclass(frozen=True)
class Index:
    """Every song and artist the corpus holds, keyed by identity.

    `years` is the span it was built over. Building is a replace rather than a
    merge, so a narrower span produces a narrower index; carrying the span means
    a caller can see that rather than reading a healthy-looking smaller number.
    """

    songs: dict[str, Song]
    artists: dict[str, Artist]
    years: tuple[int, int] | None = None

    @classmethod
    def of(cls, corpus: Corpus, charts: list[Chart], years: tuple[int, int]) -> "Index":
        """Build the index by reading every chart-year the corpus holds."""
        songs: dict[str, Song] = {}
        artists: dict[str, Artist] = {}
        for chart in charts:
            for year in range(years[0], years[1] + 1):
                if not corpus.path(chart, year).exists():
                    continue
                for entry in corpus.read(chart, year).entries:
                    _absorb(songs, artists, chart, year, entry)
        return cls(songs=songs, artists=artists, years=years)

    def song(self, title: str, artist: str) -> Song | None:
        """The song a title and artist name, however either is spelled."""
        return self.songs.get(Identity.of(title, artist).key)

    def artist(self, name: str) -> Artist | None:
        """The artist a name names, however it is spelled."""
        return self.artists.get(core_artist(lead(name)))

    def crossovers(self, charts: list[Chart]) -> list[Song]:
        """Songs that appeared on every one of these charts."""
        wanted = tuple(charts)
        return sorted(
            (song for song in self.songs.values() if song.crossed(wanted)),
            key=lambda song: (song.years[0], song.title),
        )

    def counts(self) -> dict:
        """What the index holds and over which years, for a caller deciding whether to rebuild."""
        rows = sum(len(song.appearances) for song in self.songs.values())
        return {
            "songs": len(self.songs),
            "artists": len(self.artists),
            "appearances": rows,
            "years": list(self.years) if self.years else None,
        }


def _absorb(songs, artists, chart, year, entry) -> None:
    identity = Identity.of(entry.title, entry.artist)
    appearance = Appearance(
        chart=chart,
        year=year,
        kind=entry.kind,
        rank=entry.rank,
        reached=entry.reached,
        weeks=entry.weeks,
    )
    held = songs.get(identity.key)
    if held is None:
        songs[identity.key] = Song(
            key=identity.key,
            title=entry.title,
            artist=entry.artist,
            appearances=(appearance,),
        )
    else:
        songs[identity.key] = held.model_copy(
            update={"appearances": (*held.appearances, appearance)}
        )
    _credit(artists, identity, entry.artist, identity.key)


def _credit(artists, identity: Identity, billing: str, song_key: str) -> None:
    held = artists.get(identity.artist)
    if held is None:
        artists[identity.artist] = Artist(
            key=identity.artist, name=billing, billings=(billing,), songs=(song_key,)
        )
        return
    artists[identity.artist] = held.model_copy(
        update={
            "billings": _added(held.billings, billing),
            "songs": _added(held.songs, song_key),
        }
    )


def _added(existing: tuple[str, ...], value: str) -> tuple[str, ...]:
    return existing if value in existing else (*existing, value)
