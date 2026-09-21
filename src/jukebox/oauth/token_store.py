"""Where a refresh token lives.

Account state, not project data: per-machine, a credential, and never in the
repository. Written readable only by its owner.
"""

import pathlib
import stat

from jukebox.oauth.token import Token

OWNER_ONLY = stat.S_IRUSR | stat.S_IWUSR


class TokenStore:
    """Reads and writes one service's stored token."""

    def __init__(self, directory: pathlib.Path, provider: str, client_id: str = "") -> None:
        self._path = directory / f"{provider}-token.json"
        self._client_id = client_id

    @property
    def path(self) -> pathlib.Path:
        """Where the token is kept."""
        return self._path

    def load(self) -> Token | None:
        """The stored token, or None if there is not one for this application.

        A token minted for another client id is not merely unhelpful: redeeming
        it fails at refresh with an error that explains none of this. Declining
        it here means the caller is told to authorize, which is the truth.
        """
        if not self._path.exists():
            return None
        token = Token.model_validate_json(self._path.read_text(encoding="utf-8"))
        if token.client_id and self._client_id and token.client_id != self._client_id:
            return None
        return token

    def save(self, token: Token) -> None:
        """Store a token, readable only by its owner, stamped with its application."""
        token = token.model_copy(update={"client_id": self._client_id or token.client_id})
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.touch(mode=OWNER_ONLY, exist_ok=True)
        self._path.chmod(OWNER_ONLY)
        self._path.write_text(token.model_dump_json(indent=2) + "\n", encoding="utf-8")

    def clear(self) -> bool:
        """Forget the stored token; True if there was one."""
        if not self._path.exists():
            return False
        self._path.unlink()
        return True
