"""An access token and the refresh token that renews it."""

import datetime as dt

from pydantic import BaseModel

SKEW = dt.timedelta(seconds=60)


class Token(BaseModel):
    """What a service grants, and when it stops working."""

    access_token: str
    refresh_token: str
    expires_at: dt.datetime
    scope: str = ""
    client_id: str = ""
    """Which application this was minted for.

    A refresh token is only redeemable by the client that obtained it, so a
    token loaded for a different application fails at refresh with an error that
    describes none of that. Recording it lets the store decline instead.
    """

    @classmethod
    def issued(cls, payload: dict, now: dt.datetime, previous: "Token | None" = None) -> "Token":
        """Build a token from a grant response.

        A refresh response may omit the refresh token, in which case the one
        already held remains valid and is carried forward. Dropping it there is
        how a client silently downgrades itself to a single hour of access.
        """
        carried = payload.get("refresh_token") or (previous.refresh_token if previous else "")
        return cls(
            access_token=payload["access_token"],
            refresh_token=carried,
            expires_at=now + dt.timedelta(seconds=int(payload["expires_in"])),
            scope=payload.get("scope", ""),
        )

    def expired(self, now: dt.datetime) -> bool:
        """Whether this token needs renewing, counting a minute of clock skew."""
        return now + SKEW >= self.expires_at
