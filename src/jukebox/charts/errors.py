"""What the charts module refuses, and what to do instead."""

from jukebox.errors import JukeboxError


class ChartsError(JukeboxError):
    """Base for the charts module's refusals."""


class NoTableFound(ChartsError):
    """The page rendered, but holds nothing a chart could be read from."""

    def __init__(self, detail: str) -> None:
        super().__init__(
            f"no wikitable in {detail}",
            "check the page still tabulates its chart, then update the registry",
        )


class PageNotFound(ChartsError):
    """The source has no such page."""

    def __init__(self, title: str) -> None:
        super().__init__(
            f"no page titled {title!r}",
            "confirm the title on Wikipedia and correct the registry entry",
        )


class UnexpectedColumns(ChartsError):
    """The table's columns are not the ones this mapper reads."""

    def __init__(self, wanted: str, seen: list[str]) -> None:
        super().__init__(
            f"expected a {wanted} table, saw columns {seen}",
            "check the page shape declared for this chart in the registry",
        )


class UnknownChart(ChartsError):
    """No chart answers to that slug."""

    def __init__(self, slug: str, known: list[str]) -> None:
        super().__init__(
            f"no chart named {slug!r}",
            f"choose one of: {', '.join(known)}",
        )


class UnknownMeasure(ChartsError):
    """A filter named something the charts do not measure."""

    def __init__(self, text: str, known: list[str]) -> None:
        super().__init__(
            f"cannot read {text!r} as a way of narrowing chart rows",
            f"write it as measure=value, where measure is one of: {', '.join(known)}",
        )
