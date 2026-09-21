"""Where jukebox keeps things, and which of them you can safely delete.

Everything used to be resolved against the current working directory, which
meant running the command from elsewhere silently produced a second, empty
everything — and it put the user's own playlist specs inside the project's
repository, next to code, where they were neither the project's to ship nor
the user's to find.

Two roots, because two lifetimes.

Data holds the refresh token, the apply ledger, and the specs a person wrote.
None of it is reproducible: losing it means re-authorizing and rewriting
playlists by hand.

Cache holds the chart corpus and the resolutions. Both are rebuilt by a command
in about a minute, so deleting this one costs only time.

`JUKEBOX_HOME` overrides both and puts everything under one directory, which is
what a project-local workspace or a test wants.
"""

import dataclasses
import os
import pathlib

APP = "jukebox"


@dataclasses.dataclass(frozen=True)
class Paths:
    """The resolved data and cache roots."""

    data: pathlib.Path
    cache: pathlib.Path

    @classmethod
    def resolve(cls, environ: dict | None = None, home: pathlib.Path | None = None) -> "Paths":
        """The roots for this machine, honouring JUKEBOX_HOME then the XDG variables."""
        env = os.environ if environ is None else environ
        explicit = env.get("JUKEBOX_HOME")
        if explicit:
            root = pathlib.Path(explicit).expanduser()
            return cls(data=root, cache=root / "cache")
        house = home or pathlib.Path.home()
        data = pathlib.Path(env.get("XDG_DATA_HOME") or house / ".local" / "share")
        cache = pathlib.Path(env.get("XDG_CACHE_HOME") or house / ".cache")
        return cls(data=data / APP, cache=cache / APP)

    @property
    def specs(self) -> pathlib.Path:
        """Playlist specs — the user's own writing, not the project's."""
        return self.data / "specs"

    @property
    def ledger(self) -> pathlib.Path:
        """What was last written to each playlist."""
        return self.data / "ledger"

    @property
    def credentials(self) -> pathlib.Path:
        """Where a provider's refresh token is kept."""
        return self.data

    @property
    def charts(self) -> pathlib.Path:
        """The chart corpus — rebuilt by `jukebox charts fetch`."""
        return self.cache / "charts"

    @property
    def index(self) -> pathlib.Path:
        """The song index — rebuilt by `jukebox songs build`."""
        return self.cache / "index"

    @property
    def resolutions(self) -> pathlib.Path:
        """Chart entry to track URI — rebuilt by `jukebox resolve backfill`."""
        return self.cache / "resolutions"
