"""One mapper per page shape: a grid in, corpus rows out."""

from jukebox.charts.mappers.decade import DecadeMapper
from jukebox.charts.mappers.number_ones import NumberOnesMapper
from jukebox.charts.mappers.ranked import RankedMapper

__all__ = ["DecadeMapper", "NumberOnesMapper", "RankedMapper"]
