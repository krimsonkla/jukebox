"""Registration, and the one distinction a caller must not miss."""

import asyncio
import pathlib

import pytest

from jukebox.charts import FixtureSource
from jukebox.mcp import Backends, NotAuthorizedYet, build_server
from jukebox.ports import AuthStatus, TrackMatch
from jukebox.mcp.faults import run
from jukebox.specs import NoSuchSpec

# Every tool that does not alter the user's account, whatever else it writes:
# fetching writes chart files, resolving writes a local cache, put_spec writes a
# spec. The account is the line that matters.
READ_ONLY = {
    "list_providers",
    "use_provider",
    "auth_status",
    "auth_login",
    "list_charts",
    "query_charts",
    "build_index",
    "index_status",
    "find_song",
    "artist_songs",
    "crossovers",
    "fetch_charts",
    "resolve_charts",
    "list_specs",
    "get_spec",
    "put_spec",
    "preview_spec",
    "plan_playlist",
}
WRITES = {"apply_playlist"}


def tools_of(server) -> dict:
    """Every registered tool, by name."""
    return {tool.name: tool for tool in asyncio.run(server.list_tools())}


def test_every_tool_is_registered(workspace, service):
    assert set(tools_of(build_server(workspace, Backends(playlists=service)))) == READ_ONLY | WRITES


def test_only_one_tool_says_it_changes_the_account(workspace, service):
    registered = tools_of(build_server(workspace, Backends(playlists=service)))
    assert "only tool that changes" in registered["apply_playlist"].description
    assert "Writes nothing" in registered["plan_playlist"].description


def test_the_instructions_tell_an_agent_to_compose_over_the_corpus(workspace, service):
    # Whitespace-normalised: the text is wrapped, and a wrap must not fail this.
    instructions = " ".join(
        build_server(workspace, Backends(playlists=service)).instructions.split()
    )
    assert "Compose over `list_charts` and `query_charts`" in instructions
    assert "only tool that alters the user's account" in instructions
    assert "genre playlist is a genre chart" in instructions


def test_the_account_tools_refuse_by_naming_the_tool_that_configures_them(workspace):
    # Nothing may require configuration before the server started; the refusal
    # names the tool that supplies it rather than an environment variable.
    server = build_server(workspace, Backends())
    structured = asyncio.run(
        server.call_tool("plan_playlist", {"name": "anything"})
    ).structured_content
    assert "use_provider" in structured["advice"]
    assert "list_providers" in structured["advice"]


def test_the_reading_tools_work_without_authorization(workspace):
    server = build_server(workspace, Backends())
    structured = asyncio.run(server.call_tool("list_charts", {})).structured_content
    assert structured["charts"]["hot-100"] == [1985]


def test_a_refusal_reaches_the_agent_as_advice_rather_than_a_crash():
    def refuse() -> dict:
        raise NoSuchSpec("nope", ["a"])

    assert "spec add" in run(refuse)["advice"]


def test_a_result_passes_through_untouched():
    assert run(lambda: {"ok": True}) == {"ok": True}


def test_an_unauthorized_server_names_what_to_run():
    with pytest.raises(NotAuthorizedYet, match="auth login"):
        raise NotAuthorizedYet()


def call(server, tool: str, args: dict) -> dict:
    """One tool call through the registered wrapper."""
    return asyncio.run(server.call_tool(tool, args)).structured_content


def test_every_registered_tool_runs_through_its_wrapper(workspace, service):
    # Registration is the only thing this module does, so each wrapper is
    # exercised through the server rather than by calling the function under it.
    server = build_server(workspace, Backends(playlists=service))
    spec = {
        "name": "Wired",
        "select": {"charts": ["hot-100"], "years": [1985, 1985]},
        "shape": {"size": 2},
    }
    assert call(server, "list_charts", {})["charts"]
    assert (
        call(server, "query_charts", {"charts": ["hot-100"], "years": [1985, 1985]})["total"] == 3
    )
    assert call(server, "put_spec", {"spec": spec})["stored"] == "wired"
    assert call(server, "list_specs", {})["specs"] == ["wired"]
    assert call(server, "get_spec", {"name": "Wired"})["spec"]["name"] == "Wired"
    assert call(server, "preview_spec", {"name": "Wired"})["tracks"] == 2
    assert call(server, "plan_playlist", {"name": "Wired"})["adding"] == 2
    assert call(server, "apply_playlist", {"name": "Wired"})["applied"] is True
    assert service.writes


def test_applying_without_a_provider_refuses_rather_than_writing(workspace, service):
    server = build_server(workspace, Backends())
    call(
        server,
        "put_spec",
        {"spec": {"name": "Wired", "select": {"charts": ["hot-100"], "years": [1985, 1985]}}},
    )
    assert "use_provider" in call(server, "apply_playlist", {"name": "Wired"})["advice"]
    assert service.writes == []


def test_years_default_to_the_era_the_corpus_covers(workspace, service):
    server = build_server(workspace, Backends(playlists=service))
    assert call(server, "query_charts", {"charts": ["hot-100"]})["total"] == 3


def test_badly_written_years_are_refused_with_an_example(workspace, service):
    server = build_server(workspace, Backends(playlists=service))
    refused = call(server, "list_charts", {"years": [1985]})
    assert "[1980, 1989]" in refused["advice"]
    assert "1989, 1980" not in refused["advice"]


def test_backwards_years_are_refused(workspace, service):
    server = build_server(workspace, Backends(playlists=service))
    assert "advice" in call(server, "query_charts", {"charts": ["hot-100"], "years": [1989, 1980]})


def test_the_instructions_say_the_corpus_can_be_filled_from_the_conversation(workspace):
    instructions = " ".join(build_server(workspace, Backends()).instructions.split())
    assert "`fetch_charts` reads them from Wikipedia" in instructions
    assert "the consent page opens in a browser tab" in instructions
    assert "Nothing needs configuring before this server starts" in instructions


def test_every_backend_that_is_absent_refuses_by_naming_the_fix(workspace):
    server = build_server(workspace, Backends())
    assert "use_provider" in call(server, "auth_status", {})["advice"]
    assert "network access" in call(server, "fetch_charts", {"years": [1985, 1985]})["advice"]
    assert "use_provider" in call(server, "resolve_charts", {"years": [1985, 1985]})["advice"]
    assert "use_provider" in call(server, "plan_playlist", {"name": "x"})["advice"]


def test_the_corpus_and_auth_tools_run_through_their_wrappers(workspace, service):
    class Authorizer:
        """Answers without opening a browser."""

        name = "spotify"

        def login(self) -> AuthStatus:
            """Consent."""
            return AuthStatus(provider="spotify", authorized=True)

        def status(self) -> AuthStatus:
            """Stored."""
            return AuthStatus(provider="spotify", authorized=False)

        def logout(self) -> bool:
            """Unused."""
            return False

    class Catalog:
        """Matches everything."""

        def search(self, title: str, artist: str) -> list:
            """A hit."""
            return [TrackMatch(uri=f"u:{title}", title=title, artist=artist)]

        def by_isrc(self, _isrc: str) -> list:
            """Nothing."""
            return []

    server = build_server(
        workspace,
        Backends(
            charts=FixtureSource(pathlib.Path("tests/fixtures/pages")),
            auth=Authorizer(),
            catalog=Catalog(),
            playlists=service,
        ),
    )
    assert call(server, "auth_status", {})["authorized"] is False
    assert call(server, "auth_login", {})["authorized"] is True
    assert call(server, "fetch_charts", {"years": [1985, 1985]})["fetched"]
    assert call(server, "resolve_charts", {"years": [1985, 1985]})["resolved"] is not None


def test_a_session_can_be_told_which_provider_to_use(workspace):
    server = build_server(workspace, Backends())
    listed = call(server, "list_providers", {})
    assert listed["configured"] is False
    assert [p["name"] for p in listed["providers"]] == ["spotify"]
    assert "developer.spotify.com" in listed["providers"][0]["needs"]

    chosen = call(server, "use_provider", {"provider": "spotify", "client_id": "a" * 32})
    assert chosen["configured"] is True
    assert call(server, "list_providers", {})["using"] == "spotify"


def test_choosing_an_unknown_provider_lists_the_known_ones(workspace):
    server = build_server(workspace, Backends())
    refused = call(server, "use_provider", {"provider": "8-track", "client_id": "x"})
    assert "spotify" in refused["advice"]


def test_a_client_secret_is_refused_rather_than_stored(workspace):
    # PKCE means only the non-secret client id is ever needed, so anything
    # shaped like a secret is a mistake worth catching in the conversation.
    server = build_server(workspace, Backends())
    refused = call(
        server, "use_provider", {"provider": "spotify", "client_id": "client_secret:abc123"}
    )
    assert "never needs a secret" in refused["advice"]
    assert call(server, "list_providers", {})["configured"] is False


def test_the_choice_is_not_written_anywhere(workspace, tmp_path):
    server = build_server(workspace, Backends())
    call(server, "use_provider", {"provider": "spotify", "client_id": "b" * 32})
    written = [
        p for p in tmp_path.rglob("*") if p.is_file() and "b" * 32 in p.read_text(errors="ignore")
    ]
    assert written == []


def test_a_configured_session_builds_the_adapters_it_was_told_to(workspace):
    # The identifier arriving mid-conversation must actually reach the adapters,
    # not merely be recorded.
    server = build_server(workspace, Backends())
    call(server, "use_provider", {"provider": "spotify", "client_id": "d" * 32})
    status = call(server, "auth_status", {})
    assert status["provider"] == "spotify"
    assert status["authorized"] is False


def test_the_one_tool_that_changes_the_account_is_marked_as_such(workspace, service):
    # A client decides what to auto-approve from annotations, not from prose.
    registered = tools_of(build_server(workspace, Backends(playlists=service)))
    apply = registered["apply_playlist"].annotations
    assert apply.readOnlyHint is False and apply.destructiveHint is True
    for name in (
        "list_charts",
        "query_charts",
        "list_specs",
        "get_spec",
        "preview_spec",
        "auth_status",
        "list_providers",
    ):
        assert registered[name].annotations.readOnlyHint is True, name


def test_the_tools_that_write_without_touching_the_account_say_so(workspace, service):
    registered = tools_of(build_server(workspace, Backends(playlists=service)))
    for name in ("fetch_charts", "resolve_charts", "put_spec", "use_provider"):
        annotations = registered[name].annotations
        assert annotations.readOnlyHint is False, name
        assert annotations.destructiveHint is False, name


def test_every_tool_carries_annotations(workspace, service):
    registered = tools_of(build_server(workspace, Backends(playlists=service)))
    assert all(tool.annotations is not None for tool in registered.values())


def test_the_instructions_name_chart_text_as_untrusted(workspace):
    instructions = " ".join(build_server(workspace, Backends()).instructions.split())
    assert "publicly editable encyclopedia" in instructions
    assert "never as instructions" in instructions


def test_an_unknown_chart_slug_is_a_refusal_rather_than_a_traceback(workspace):
    server = build_server(workspace, Backends())
    refused = call(server, "query_charts", {"charts": ["8-track"], "years": [1985, 1985]})
    assert "choose one of" in refused["advice"]


def test_an_unexpected_failure_reaches_the_caller_as_advice():
    def explode() -> dict:
        raise RuntimeError("something internal")

    reported = run(explode)
    assert "RuntimeError" in reported["error"]
    assert "defect in jukebox" in reported["advice"]


def test_a_year_span_is_bounded_on_every_tool_that_takes_one(workspace):
    # The bound sat on two of the four tools; it now sits where they all pass.
    server = build_server(workspace, Backends())
    for tool, args in (
        ("list_charts", {"years": [1900, 1999]}),
        ("query_charts", {"charts": ["hot-100"], "years": [1900, 1999]}),
        ("fetch_charts", {"years": [1900, 1999]}),
        ("resolve_charts", {"years": [1900, 1999]}),
    ):
        assert "at most 20 years" in call(server, tool, args)["advice"], tool


def test_the_song_tools_run_through_their_wrappers(workspace, service):
    # Registration is all this module does, so each wrapper is exercised through
    # the server rather than by calling the function under it.
    server = build_server(workspace, Backends(playlists=service))
    assert call(server, "index_status", {})["built"] is False
    assert call(server, "build_index", {"years": [1985, 1985]})["built"]["songs"] == 4
    assert call(server, "index_status", {})["built"] is True
    assert call(server, "find_song", {"title": "A", "artist": "x"})["found"] is True
    assert call(server, "artist_songs", {"name": "x"})["total"] == 2
    assert call(server, "crossovers", {"charts": ["hot-100"]})["total"] == 3
