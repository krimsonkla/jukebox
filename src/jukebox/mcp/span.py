"""A pair of chart years, as an agent supplies them.

The same shape a spec's `years` field takes, so the vocabulary an agent writes
in one place is the vocabulary it queries with in another.
"""

from jukebox.errors import JukeboxError

DEFAULT = (1980, 1999)
MAX_YEARS = 20


class TooManyYears(JukeboxError):
    """One call asked for more years than a call should answer."""

    def __init__(self, years: tuple[int, int]) -> None:
        super().__init__(
            f"{years[0]}-{years[1]} is too many years for one call",
            f"ask for at most {MAX_YEARS} years at a time, then call again for the rest",
        )


class BadYears(JukeboxError):
    """The years were not a first and a last."""

    def __init__(self, value: object) -> None:
        super().__init__(
            f"cannot read {value!r} as chart years",
            "pass two years, first then last, for example [1980, 1989]",
        )


def span(years: list[int] | None) -> tuple[int, int]:
    """The pair of years, defaulting to the era the corpus covers."""
    if years is None:
        return DEFAULT
    if len(years) != 2 or years[1] < years[0]:
        raise BadYears(years)
    bounded = (years[0], years[1])
    # Bounded here rather than in the two tools that happened to check, so the
    # next tool taking a span is not the third site to forget.
    if bounded[1] - bounded[0] + 1 > MAX_YEARS:
        raise TooManyYears(bounded)
    return bounded
