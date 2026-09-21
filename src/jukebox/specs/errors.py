"""What the specs module refuses, and what to do instead."""

from jukebox.errors import JukeboxError


class SpecsError(JukeboxError):
    """Base for the specs module's refusals."""


class NoSuchSpec(SpecsError):
    """No spec is stored under that name."""

    def __init__(self, name: str, known: list[str]) -> None:
        super().__init__(
            f"no spec named {name!r}",
            f"known specs: {', '.join(known) or 'none yet'}; write one with `jukebox spec add`",
        )


class EmptySelection(SpecsError):
    """The selection matched no chart entry."""

    def __init__(self, name: str) -> None:
        super().__init__(
            f"the selection in {name!r} matched nothing",
            "widen the years or charts, or fetch the years it names — "
            "`jukebox charts fetch --year <year>`, or the fetch_charts tool",
        )
