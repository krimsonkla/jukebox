"""One attempt's authorization request."""

import dataclasses
import urllib.parse

from jukebox.oauth.pkce import METHOD, Pkce


@dataclasses.dataclass(frozen=True)
class AuthorizationRequest:
    """Everything the consent URL carries.

    The verifier stays behind: only its challenge travels, which is the whole
    point of PKCE.
    """

    endpoint: str
    client_id: str
    redirect_uri: str
    scopes: tuple[str, ...]
    pkce: Pkce
    state: str

    def url(self) -> str:
        """The URL to send the user to."""
        query = urllib.parse.urlencode(
            {
                "response_type": "code",
                "client_id": self.client_id,
                "redirect_uri": self.redirect_uri,
                "scope": " ".join(self.scopes),
                "code_challenge_method": METHOD,
                "code_challenge": self.pkce.challenge,
                "state": self.state,
            }
        )
        return f"{self.endpoint}?{query}"
