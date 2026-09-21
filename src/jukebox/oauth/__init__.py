"""Reusable OAuth 2.0 PKCE machinery, naming no particular music service."""

from jukebox.oauth.authorization_request import AuthorizationRequest
from jukebox.oauth.callback import Callback
from jukebox.oauth.errors import (
    AuthorizationDenied,
    AuthorizationTimedOut,
    NotAuthorized,
    OAuthError,
    StateMismatch,
)
from jukebox.oauth.flow import Flow
from jukebox.oauth.loopback import Loopback
from jukebox.oauth.pkce import Pkce
from jukebox.oauth.session import Session
from jukebox.oauth.token import Token
from jukebox.oauth.token_client import TokenClient
from jukebox.oauth.token_store import TokenStore

__all__ = [
    "AuthorizationDenied",
    "AuthorizationRequest",
    "AuthorizationTimedOut",
    "Callback",
    "Flow",
    "Loopback",
    "NotAuthorized",
    "OAuthError",
    "Pkce",
    "Session",
    "StateMismatch",
    "Token",
    "TokenClient",
    "TokenStore",
]
