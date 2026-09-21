"""What applying a spec would do, before anything is written."""

import dataclasses

from jukebox.reconcile.changes import Changes
from jukebox.specs.selected import Selected


@dataclasses.dataclass(frozen=True)
class Plan:
    """The difference between what a spec wants and what is on the playlist."""

    spec: str
    playlist_id: str | None
    final: tuple[str, ...]
    desired: tuple[str, ...]
    """What the spec asked for, which is what the ledger records.

    Never `final`: that includes tracks a person added, which jukebox preserved
    rather than placed. Recording those as its own makes them indistinguishable
    from spec tracks on the next run, and the next apply deletes them — so a
    manual addition would survive exactly one reconciliation.
    """

    diff: Changes
    unresolved: tuple[Selected, ...]

    @property
    def adds(self) -> tuple[str, ...]:
        """Tracks going on."""
        return self.diff.adds

    @property
    def removes(self) -> tuple[str, ...]:
        """Tracks coming off."""
        return self.diff.removes

    @property
    def manual_kept(self) -> tuple[str, ...]:
        """Tracks a person added, which the spec does not name but keeps."""
        return self.diff.manual_kept

    @property
    def reordered(self) -> bool:
        """Whether the sequence changes."""
        return self.diff.reordered

    @property
    def recovered(self) -> tuple[str, ...]:
        """Tracks an interrupted write lost, restored from what it recorded first."""
        return self.diff.recovered

    @property
    def creates(self) -> bool:
        """Whether applying this would make a new playlist."""
        return self.playlist_id is None

    @property
    def changes(self) -> bool:
        """Whether applying this would alter the account at all."""
        return self.diff.any or self.creates

    def render(self) -> str:
        """The plan as the CLI prints it."""
        where = "new playlist" if self.creates else self.playlist_id
        lines = [f"{self.spec} -> {where}", f"  {len(self.final)} tracks after applying"]
        lines += [
            f"  +{len(self.adds)} add   -{len(self.removes)} remove"
            f"   {'reorder' if self.reordered else 'order unchanged'}"
        ]
        if self.manual_kept:
            lines.append(f"  {len(self.manual_kept)} added by hand — kept")
        if self.recovered:
            lines.append(f"  {len(self.recovered)} restored after an interrupted apply")
        if self.unresolved:
            lines.append(f"  {len(self.unresolved)} not matched to a track:")
            lines += [f"      {entry.title} — {entry.artist}" for entry in self.unresolved[:10]]
        if not self.changes:
            lines.append("  nothing to do")
        return "\n".join(lines)
