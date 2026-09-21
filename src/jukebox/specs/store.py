"""Where playlist specs live.

Committed, unlike a resolution: a spec is the user's own description of a
playlist, in the charts' vocabulary, and holds no music service's content.
"""

import pathlib

import yaml

from jukebox.specs.errors import NoSuchSpec
from jukebox.specs.slug import slugify
from jukebox.specs.spec import Spec


class SpecStore:
    """Reads and writes specs as YAML."""

    def __init__(self, root: pathlib.Path) -> None:
        self._root = root

    def path(self, slug: str) -> pathlib.Path:
        """Where a spec with this slug is stored."""
        return self._root / f"{slug}.yaml"

    def names(self) -> list[str]:
        """Every stored spec's slug, in order."""
        if not self._root.exists():
            return []
        return sorted(path.stem for path in self._root.glob("*.yaml"))

    def load(self, name: str) -> Spec:
        """One spec, by name or by slug.

        The name is slugified before it becomes a path, exactly as `save` does.
        Without that the caller chooses the path: a model steered by text it
        just fetched could name any file on the machine and receive the parsed
        document or a truncated repr of a credential.
        """
        path = self.path(slugify(name))
        if not path.exists():
            raise NoSuchSpec(name, self.names())
        return Spec.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))

    def save(self, spec: Spec) -> pathlib.Path:
        """Write a spec, replacing any stored under the same slug."""
        destination = self.path(spec.slug())
        destination.parent.mkdir(parents=True, exist_ok=True)
        body = spec.model_dump(mode="json", exclude_defaults=True)
        destination.write_text(
            yaml.safe_dump(body, sort_keys=False, allow_unicode=True), encoding="utf-8"
        )
        return destination
