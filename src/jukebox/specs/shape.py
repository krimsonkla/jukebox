"""How many, in what order, and how much of any one artist."""

from pydantic import BaseModel, Field

from jukebox.specs.ordering import Ordering


class Shape(BaseModel):
    """What the selected entries are cut down to."""

    size: int | None = Field(default=None, gt=0)
    max_per_artist: int | None = Field(default=None, gt=0)
    order: Ordering = Ordering.CHART
    seed: int = 0
    """Only read when the order is a shuffle; fixed so a rebuild repeats it."""
