"""Writing and reading playlist specs.

A spec is the durable artifact of a conversation: the model turns what someone
said into selection predicates, and the file is what makes a rebuild repeat it.
"""

from jukebox.charts.corpus import Corpus
from jukebox.mcp.workspace import Workspace
from jukebox.specs.evaluate import Evaluate
from jukebox.specs.spec import Spec


def list_specs(workspace: Workspace) -> dict:
    """Every stored spec."""
    return {"specs": workspace.specs.names()}


def get_spec(workspace: Workspace, name: str) -> dict:
    """One spec, as stored."""
    return {"spec": workspace.specs.load(name).model_dump(mode="json", exclude_defaults=True)}


def put_spec(workspace: Workspace, spec: dict) -> dict:
    """Store a spec, then say what it selects from the corpus.

    Writes a file in the repository and contacts no music service.
    """
    written = Spec.model_validate(spec)
    workspace.specs.save(written)
    return {"stored": written.slug()} | _selection(workspace.corpus, written)


def preview_spec(workspace: Workspace, name: str) -> dict:
    """What a stored spec selects. Reads the corpus only."""
    return _selection(workspace.corpus, workspace.specs.load(name))


def _selection(corpus: Corpus, spec: Spec) -> dict:
    tracklist = Evaluate(corpus).tracklist(spec)
    return {
        "name": tracklist.name,
        "tracks": len(tracklist.entries),
        "considered": tracklist.considered,
        "dropped_to_cap": tracklist.dropped_to_cap,
        "order": tracklist.order.value,
        # A release ordering is settled by the catalogue, so these entries are in
        # the order they were cut in, not the order they will be written in.
        # Saying so is what keeps a preview from promising what an apply breaks.
        "sequenced_at_resolution": tracklist.sequenced_later,
        "from_charts": tracklist.composition(),
        "entries": [
            {
                "title": chosen.title,
                "artist": chosen.artist,
                "chart": chosen.chart.slug,
                "year": chosen.year,
            }
            for chosen in tracklist.entries
        ],
    }
