"""Describing a playlist, rather than assembling one."""

from jukebox.specs.errors import EmptySelection, NoSuchSpec, SpecsError
from jukebox.specs.evaluate import Evaluate
from jukebox.specs.exclusion import Exclusion
from jukebox.specs.ordering import Ordering
from jukebox.specs.selected import Selected
from jukebox.specs.selection import Selection
from jukebox.specs.selector import Selector
from jukebox.specs.shape import Shape
from jukebox.specs.shaper import Shaper
from jukebox.specs.spec import Spec
from jukebox.specs.slug import slugify
from jukebox.specs.store import SpecStore
from jukebox.specs.year_range import BadYearRange, parse_years
from jukebox.specs.tracklist import Tracklist

__all__ = [
    "BadYearRange",
    "EmptySelection",
    "Evaluate",
    "Exclusion",
    "NoSuchSpec",
    "Ordering",
    "Selected",
    "Selection",
    "Selector",
    "Shape",
    "Shaper",
    "Spec",
    "SpecStore",
    "SpecsError",
    "Tracklist",
    "parse_years",
    "slugify",
]
