"""The corpus as songs and artists rather than as lists."""

from jukebox.songs.appearance import Appearance
from jukebox.songs.artist import Artist
from jukebox.songs.identity import Identity
from jukebox.songs.index import Index
from jukebox.songs.song import Song
from jukebox.songs.store import IndexStore

__all__ = ["Appearance", "Artist", "Identity", "Index", "IndexStore", "Song"]
