"""Planning and applying a spec to the authorized account.

These are the only tools that reach a music service, and `apply_spec` is the
only one in jukebox that changes anything. What they return is deliberately the
chart's vocabulary and counts rather than the service's catalogue data: the
Spotify developer terms forbid ingesting Spotify Content into a model, so track
identifiers stay between the resolver and the writer.
"""

from jukebox.mcp.workspace import Workspace
from jukebox.ports.playlist_service import PlaylistService
from jukebox.reconcile.apply import Apply
from jukebox.reconcile.desired import Desired
from jukebox.reconcile.plan import Plan
from jukebox.specs.evaluate import Evaluate
from jukebox.specs.spec import Spec

PLAYLIST_URL = "https://open.spotify.com/playlist/"


def plan_playlist(
    workspace: Workspace, service: PlaylistService, name: str, replace_manual: bool = False
) -> dict:
    """What applying a spec would change on the account. Writes nothing."""
    spec, made, _ = _planned(workspace, service, name, replace_manual)
    return _reported(spec, made)


def apply_playlist(
    workspace: Workspace, service: PlaylistService, name: str, replace_manual: bool = False
) -> dict:
    """Bring the playlist into line with the spec.

    This changes the user's account: it creates or rewrites a playlist. Tracks
    the user added by hand are kept unless `replace_manual` is set.
    """
    spec, made, applier = _planned(workspace, service, name, replace_manual)
    if not made.changes:
        return _reported(spec, made) | {"applied": False}
    playlist_id = applier.write(spec, made)
    return _reported(spec, made) | {"applied": True, "playlist_url": f"{PLAYLIST_URL}{playlist_id}"}


def _planned(
    workspace: Workspace, service: PlaylistService, name: str, replace_manual: bool
) -> tuple[Spec, Plan, Apply]:
    spec = workspace.specs.load(name)
    tracklist = Evaluate(workspace.corpus).tracklist(spec)
    applier = Apply(service, workspace.ledger, Desired(workspace.resolutions))
    return spec, applier.plan(spec, tracklist, keep_manual=not replace_manual), applier


def _reported(spec: Spec, made: Plan) -> dict:
    """Counts and chart entries — never the catalogue's own data."""
    return {
        "name": spec.name,
        "creates_playlist": made.creates,
        "changes": made.changes,
        "tracks_after": len(made.final),
        "adding": len(made.adds),
        "removing": len(made.removes),
        "reordering": made.reordered,
        "kept_because_you_added_them": len(made.manual_kept),
        "unmatched": [{"title": entry.title, "artist": entry.artist} for entry in made.unresolved],
    }
