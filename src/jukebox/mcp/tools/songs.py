"""The corpus asked about by song and by artist.

`query_charts` answers "what was on this list", which is the question a chart
file already shapes. These answer the ones it does not: what else this artist
charted, where this song went, and which songs crossed from one chart to
another. All of it is Billboard's vocabulary — titles, artists and counts as
published — and none of it names a music service.
"""

from jukebox.charts.chart import Chart, chart_named
from jukebox.mcp.workspace import Workspace
from jukebox.songs.index import Index
from jukebox.songs.song import Song

# Chart text is publicly editable, so what reaches the model is bounded.
FIELD = 200
LIMIT = 100


def build_index(workspace: Workspace, years: tuple[int, int]) -> dict:
    """Rebuild the song index from the corpus. Reads no service and no account.

    A replace, not a merge: the index afterwards covers these years and no
    others, so a narrower span than last time is a narrower index.
    """
    index = Index.of(workspace.corpus, list(Chart), years)
    workspace.index.save(index)
    return {"built": index.counts(), "covers": list(years), "replaced": True}


def index_status(workspace: Workspace) -> dict:
    """Whether an index has been built, and what it holds."""
    if not workspace.index.exists():
        return {"built": False, "advice": "call build_index to read the corpus into songs"}
    counts = workspace.index.load().counts()
    # The span is reported because building replaces rather than merges: without
    # it a truncated index reads as a healthy smaller one.
    return {"built": True, "covers": counts.pop("years"), **counts}


def find_song(workspace: Workspace, title: str, artist: str) -> dict:
    """One song's whole chart history, however the title or artist is spelled."""
    song = workspace.index.load().song(title, artist)
    if song is None:
        return {"found": False, "title": title[:FIELD], "artist": artist[:FIELD]}
    return {"found": True, **_song(song)}


def artist_songs(workspace: Workspace, name: str, limit: int = LIMIT) -> dict:
    """Every song the corpus credits to an artist."""
    index = workspace.index.load()
    artist = index.artist(name)
    if artist is None:
        return {"found": False, "artist": name[:FIELD]}
    songs = [index.songs[key] for key in artist.songs if key in index.songs]
    songs.sort(key=lambda song: (song.years[0], song.title))
    return {
        "found": True,
        "artist": artist.name[:FIELD],
        "billings": [billing[:FIELD] for billing in artist.billings],
        "total": artist.total,
        "songs": [_song(song) for song in songs[:limit]],
        "truncated": len(songs) > limit,
    }


def crossovers(workspace: Workspace, charts: list[str], limit: int = LIMIT) -> dict:
    """Songs that appeared on every one of these charts."""
    wanted = [chart_named(slug) for slug in charts]
    found = workspace.index.load().crossovers(wanted)
    return {
        "charts": [chart.slug for chart in wanted],
        "total": len(found),
        "songs": [_song(song) for song in found[:limit]],
        "truncated": len(found) > limit,
    }


def _song(song: Song) -> dict:
    return {
        "title": song.title[:FIELD],
        "artist": song.artist[:FIELD],
        "charts": list(song.charts),
        "years": list(song.years),
        "best_rank": song.best_rank,
        "weeks_at_number_one": song.weeks_at_number_one,
    }
