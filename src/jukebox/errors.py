"""The shape every refusal in jukebox takes.

A caller told only that something was refused has to guess the recovery, and a
guess costs another call. Advice is a field the base requires rather than a
sentence a message may or may not carry.
"""


class JukeboxError(Exception):
    """A refusal, carrying what to do instead."""

    def __init__(self, message: str, advice: str) -> None:
        super().__init__(f"{message} — {advice}")
        self.advice = advice
