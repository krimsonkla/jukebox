"""Render a refusal for an agent.

Every refusal in jukebox carries advice — what to do instead — and an agent that
receives only "it failed" guesses the recovery, which costs another call. The
advice is the field worth putting on the wire.
"""

from collections.abc import Callable

from jukebox.errors import JukeboxError


def run(action: Callable[[], dict]) -> dict:
    """Run a tool, turning a refusal into a result the agent can act on."""
    try:
        return action()
    except JukeboxError as refusal:
        return {"error": str(refusal), "advice": refusal.advice}
    except Exception as unexpected:  # pylint: disable=broad-exception-caught
        # A traceback across the wire tells an agent nothing it can act on, and
        # every escape found so far sat on a value the caller chose. The type is
        # named so a real defect is still diagnosable from the transcript.
        return {
            "error": f"{type(unexpected).__name__}: {unexpected}",
            "advice": "this is a defect in jukebox rather than something to retry; "
            "report it with the call that produced it",
        }
