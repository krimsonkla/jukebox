"""Read a span of chart years written the way a person writes one."""

from jukebox.specs.errors import SpecsError


class BadYearRange(SpecsError):
    """The years could not be read."""

    def __init__(self, text: str) -> None:
        super().__init__(
            f"cannot read {text!r} as a range of chart years",
            "write it as a single year, 1985, or a span, 1980-1989",
        )


def parse_years(text: str) -> tuple[int, int]:
    """`1985` or `1980-1989` as a first and last year."""
    # Empty halves are not dropped: "1980-" would otherwise read as the single
    # year 1980, which is a plausible reading of something the writer did not say.
    parts = [part.strip() for part in text.split("-")]
    if not all(part.isdigit() for part in parts) or len(parts) not in (1, 2):
        raise BadYearRange(text)
    years = [int(part) for part in parts]
    first, last = (years[0], years[-1])
    if last < first:
        raise BadYearRange(text)
    return first, last
