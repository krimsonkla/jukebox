"""Spotify's authorization endpoints and the scopes jukebox asks for."""

AUTHORIZE_URL = "https://accounts.spotify.com/authorize"
TOKEN_URL = "https://accounts.spotify.com/api/token"

# Only what building playlists needs: read the user's playlists so a spec can be
# reconciled against one, and modify the playlists it owns. No listening
# history, no playback control, no profile.
SCOPES = (
    "playlist-read-private",
    "playlist-modify-private",
    "playlist-modify-public",
)
