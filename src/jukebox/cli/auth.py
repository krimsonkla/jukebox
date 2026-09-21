"""`jukebox auth` — authorize a music service, and report or discard it."""

from typing import Annotated

import typer

from jukebox.errors import JukeboxError
from jukebox.oauth.errors import OAuthError
from jukebox.ports.auth_status import AuthStatus
from jukebox.providers.registry import DEFAULT, build_auth

commands = typer.Typer(help="Authorize a music service.")

Provider = Annotated[str, typer.Option("--provider", help="Which music service.")]


@commands.command("login")
def login(provider: Provider = DEFAULT) -> None:
    """Open the service's consent page and store what it grants."""
    typer.echo(f"opening {provider} in your browser; approve the request there")
    _report(_run(provider, lambda service: service.login()))


@commands.command("status")
def status(provider: Provider = DEFAULT) -> None:
    """Say whether there is a usable authorization, without contacting the service."""
    _report(_run(provider, lambda service: service.status()))


@commands.command("logout")
def logout(provider: Provider = DEFAULT) -> None:
    """Discard the stored authorization."""
    service = _resolve(provider)
    typer.echo(f"{provider}: {'forgotten' if service.logout() else 'nothing stored'}")


def _resolve(provider: str):
    try:
        return build_auth(provider)
    except JukeboxError as refusal:
        raise typer.BadParameter(str(refusal)) from refusal


def _run(provider: str, action) -> AuthStatus:
    service = _resolve(provider)
    try:
        return action(service)
    except OAuthError as refusal:
        typer.echo(str(refusal), err=True)
        raise typer.Exit(code=1) from refusal


def _report(state: AuthStatus) -> None:
    if not state.authorized:
        typer.echo(f"{state.provider}: not authorized — run `jukebox auth login`")
        return
    typer.echo(f"{state.provider}: authorized until {state.expires_at:%Y-%m-%d %H:%M} UTC")
    typer.echo(f"  scopes: {', '.join(state.scopes) or 'none reported'}")
