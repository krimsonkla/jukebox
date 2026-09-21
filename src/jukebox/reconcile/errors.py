"""What the reconciler refuses, and what to do instead."""

from jukebox.errors import JukeboxError


class ReconcileError(JukeboxError):
    """Base for the reconciler's refusals."""


class NothingResolved(ReconcileError):
    """Not one entry in the tracklist has a known track."""

    def __init__(self, name: str) -> None:
        super().__init__(
            f"no entry in {name!r} has been matched to a track",
            "match the years the spec selects to tracks — "
            "`jukebox resolve backfill --year <year>`, or the resolve_charts tool",
        )


class PlaylistGone(ReconcileError):
    """The playlist the ledger names no longer exists."""

    def __init__(self, name: str, playlist_id: str) -> None:
        super().__init__(
            f"the playlist {name!r} recorded as {playlist_id} is gone from the account",
            "apply again with --recreate to make a new one, "
            "which will not restore anything that was on the old playlist",
        )
