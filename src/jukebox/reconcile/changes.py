"""What applying a plan would alter."""

import dataclasses


@dataclasses.dataclass(frozen=True)
class Changes:
    """The tracks going on, coming off, and being kept.

    Each is the tracks themselves rather than a count, because the reason to
    read a plan before applying it is to see which ones.
    """

    adds: tuple[str, ...]
    removes: tuple[str, ...]
    manual_kept: tuple[str, ...]
    recovered: tuple[str, ...]
    reordered: bool

    @property
    def any(self) -> bool:
        """Whether this would alter the playlist at all."""
        return bool(self.adds or self.removes or self.recovered or self.reordered)
