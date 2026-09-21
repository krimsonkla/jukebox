"""Everything the tools read and write, built once from the working directory.

The MCP surface holds no logic; it holds this, so each tool receives the stores
it needs rather than assembling them and no tool decides where anything lives.
"""

import dataclasses
import pathlib

from jukebox.charts.corpus import Corpus
from jukebox.paths import Paths
from jukebox.reconcile.ledger import Ledger
from jukebox.resolve.store import ResolutionStore
from jukebox.songs.store import IndexStore
from jukebox.specs.store import SpecStore


@dataclasses.dataclass(frozen=True)
class Workspace:
    """The corpus, the index over it, the specs, the resolutions and the ledger."""

    corpus: Corpus
    index: IndexStore
    specs: SpecStore
    resolutions: ResolutionStore
    ledger: Ledger

    @classmethod
    def here(cls, root: pathlib.Path | None = None) -> "Workspace":
        """The workspace for this machine, or one rooted at a directory.

        `root` puts everything under one directory, which is what a test or a
        deliberately project-local workspace wants. Otherwise each store lands
        where its kind belongs: specs and the ledger with the user's data, the
        corpus and resolutions in the cache.
        """
        if root is not None:
            return cls(
                corpus=Corpus(root / "charts"),
                index=IndexStore(root / "index"),
                specs=SpecStore(root / "specs"),
                resolutions=ResolutionStore(root / "resolutions"),
                ledger=Ledger(root / "ledger"),
            )
        paths = Paths.resolve()
        return cls(
            corpus=Corpus(paths.charts),
            index=IndexStore(paths.index),
            specs=SpecStore(paths.specs),
            resolutions=ResolutionStore(paths.resolutions),
            ledger=Ledger(paths.ledger),
        )
