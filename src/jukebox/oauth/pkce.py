"""The PKCE verifier and the challenge derived from it.

A public client cannot keep a secret, so it proves possession instead: it sends
the hash when it asks, and the original only when it redeems.
"""

import base64
import dataclasses
import hashlib
import secrets

METHOD = "S256"


@dataclasses.dataclass(frozen=True)
class Pkce:
    """One authorization attempt's verifier."""

    verifier: str

    @classmethod
    def generate(cls) -> "Pkce":
        """A fresh verifier, within the 43-128 characters the spec allows."""
        return cls(verifier=secrets.token_urlsafe(64)[:96])

    @property
    def challenge(self) -> str:
        """The S256 challenge: base64url of the verifier's SHA-256, unpadded."""
        digest = hashlib.sha256(self.verifier.encode("ascii")).digest()
        return base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")
