"""A one-shot HTTP server that catches the authorization redirect.

Services that permit HTTP for a redirect permit it only for a loopback IP
literal, so this binds an address rather than a name, serves exactly one
request, and stops. Nothing is reachable off the machine, and nothing outlives
the login.
"""

import http.server
import threading
import urllib.parse

from jukebox.oauth.callback import Callback
from jukebox.oauth.errors import AuthorizationTimedOut

PAGE = b"<html><body><h1>jukebox</h1><p>Authorized. You can close this tab.</p></body></html>"

# An agent-driven login blocks a tool call while it waits, so waiting cannot be
# forever: someone who never reaches the consent page must get an answer.
TIMEOUT = 300.0


class Loopback:
    """Serves one request on the loopback interface and reports its query."""

    def __init__(self, host: str, port: int, timeout: float = TIMEOUT) -> None:
        self._host = host
        self._port = port
        self._timeout = timeout
        self._caught: list[Callback] = []
        self._server: http.server.HTTPServer | None = None

    def bind(self) -> "Loopback":
        """Take the port before anyone is sent to the consent page.

        Opening the browser first means a squatter on the port receives the
        redirect and the user consents for nothing. PKCE and the state check
        keep the code unusable, so what is lost is the attempt rather than the
        account — but a clean refusal beats a wasted consent and a traceback.
        """
        self._server = http.server.HTTPServer((self._host, self._port), _handler_for(self._caught))
        self._server.timeout = self._timeout
        return self

    def close(self) -> None:
        """Give the port back without waiting for a redirect."""
        if self._server is not None:
            self._server.server_close()
            self._server = None

    def wait(self) -> Callback:
        """Block until the browser is redirected here, or until the wait runs out."""
        if self._server is None:
            self.bind()
        server = self._server
        try:
            thread = threading.Thread(target=server.handle_request)
            thread.start()
            # The accept had a deadline and the read did not, so one silent
            # connection held this open for ever on the path that matters.
            thread.join(self._timeout + 1.0)
            if thread.is_alive():
                server.server_close()
                thread.join(1.0)
        finally:
            server.server_close()
            self._server = None
        if not self._caught:
            raise AuthorizationTimedOut(self._timeout)
        return self._caught[0]


def _handler_for(caught: list[Callback]) -> type[http.server.BaseHTTPRequestHandler]:
    class Handler(http.server.BaseHTTPRequestHandler):
        """Records one redirect and tells the browser it may close."""

        def do_GET(self) -> None:  # pylint: disable=invalid-name
            """Record the redirect and tell the browser it may close."""
            query = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            caught.append(
                Callback(
                    code=_first(query, "code"),
                    state=_first(query, "state"),
                    error=_first(query, "error"),
                )
            )
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(PAGE)

        def log_message(self, *_: object) -> None:
            """Silence the stdlib's per-request logging."""

    return Handler


def _first(query: dict[str, list[str]], key: str) -> str | None:
    values = query.get(key)
    return values[0] if values else None
