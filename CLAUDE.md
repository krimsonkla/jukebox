# jukebox

Build Spotify playlists from published record charts, driven by chat over MCP.

## Tech Stack

- Python 3.12, `src/` layout, `uv` (declarative via devenv `uv.sync`)
- `fastmcp` for the MCP surface, `typer` for the CLI, `dishka` for DI
- `httpx` for all HTTP, `rapidfuzz` for fallback matching
- Dev environment: devenv.sh via devenv-layers

## Project Structure

- `docs/ai-assistant-ideation/` — design artifacts; the brainstorm is the source of truth for *why*
- `src/jukebox/ports/` — the vendor-neutral vocabulary; nothing above it names a music service
- `src/jukebox/oauth/` — reusable OAuth 2.0 PKCE machinery, naming no service
- `src/jukebox/providers/<name>/` — one adapter per music service, behind the ports
- `src/jukebox/{charts,resolve,specs,reconcile,mcp,cli}/` — one purpose each
- `src/jukebox/paths.py` — the only module that decides where anything lives
- nothing is stored in the checkout: see **Where things live** below
- playlist specs live with the user's data, never in this checkout; chart
  vocabulary only, never a track id

## The constraint everything is built around

Spotify's API cannot answer "what was popular, in what genre". `recommendations`,
`related-artists` and `audio-features` are gone for new apps; *Get Artist's Top Tracks*,
the `Get Several …` batch endpoints, `popularity` (track/artist/album) and `genres`
(artist) were removed in February 2026, and `/search` returns at most 10 results.

Consequences that bite when writing code here:

- **Never rank search results by `popularity`.** The field does not exist. Ranking is
  ISRC-exact first, then the fuzzy scorer.
- **There is no batch fetch.** One request per id, under a rate limiter.
- **Playlist items live at `/playlists/{id}/items`**, and the playlist object names them
  `items`, not `tracks`.
- **Genre means "appeared on this Billboard chart"** — never an inferred tag. Any code
  that assigns a genre by any other means is a design failure.

## Three stores, three lifetimes

Corpus (immutable fact, committed) / resolutions (slow, correctable, committed) /
ledger (live account state, local). Keep them apart. The ledger holds the full list of
URIs last written, not just the playlist id — without it a track the user added by hand
is indistinguishable from one the spec has abandoned, and reconciliation silently eats
manual edits.

## Reads and writes are separate tools

`preview_spec` resolves and diffs and writes nothing; `apply_spec` is the only tool that
touches the account. A model drives this surface, so a write must never be a side effect
of asking a question.

## Give the model primitives, not conclusions

MCP tools expose callable queries over the corpus (`query_charts`, `list_charts`) so the
model composes its own selection. A tool that returns a finished tracklist answers only
the question its author imagined.

## Build & Test

uv is the route. It is what CI runs and what a fresh clone needs:

```bash
uv sync --all-groups                 # the venv, from pyproject.toml + uv.lock
uv run pytest                        # suite with coverage (network tests deselected)
uv run pytest -m network             # deliberately hit live APIs
```

A `devenv.nix` also exists and wraps the same uv commands, plus the git hooks.
It is optional. `devenv shell -- <command>` and `uv run <command>` reach the
same venv, so use whichever is already on your machine.

```bash
devenv shell -- pytest               # the same suite
devenv shell -- prek run --all-files # the hooks (prek is the pre-commit runner)
```

`prek` only sees files git tracks or has staged, so stage new files before trusting a
green hook run. A hook that reports "files were modified by this hook" invalidates the
test run before it — rerun the suite after the hooks settle.

## Gotchas

### One venv, declared in pyproject.toml

`pyproject.toml` declares the dependencies and `uv.lock` pins them. Both uv and
devenv build the same venv from that pair, so there is one Python and nothing
to keep in step by hand.

To add a dependency, edit `pyproject.toml`, run `uv lock`, and commit `uv.lock`.
Never `pip install`, and never create a second venv: an install that is not in
the lock file is one CI cannot reproduce.

Adding non-Python tooling means a `devenv.nix` change, which only helps people
who use that shell. Prefer a dev dependency in `pyproject.toml`, which everyone
gets.

### Commit with the venv on PATH

The pylint hook resolves this project's imports through the venv. A `git commit`
run with the host PATH, where `typer`, `lxml` and `respx` do not exist, is
rejected with a wall of `E0401 import-error` that says nothing about the change.

Commit from inside `devenv shell`, or use `devenv shell -- git commit`. Without
devenv, activate the venv first: `source .venv/bin/activate`.

### The ledger holds the whole list, not just the playlist id

That is what makes a manual addition recognisable. With the id alone, a track
someone added by hand is indistinguishable from one the spec has since dropped,
and reconciliation silently eats the first while claiming to remove the second.
Anything that trims the ledger to save space breaks the one guarantee the writer
makes.

### The MCP surface returns chart words, not catalogue data

Spotify's terms forbid ingesting Spotify Content into an AI model. Tool results
carry titles and artists as Billboard published them, plus counts — never track
URIs, never Spotify's own metadata. `tests/mcp/test_playlist_tools.py` asserts
it; keep that true when adding a tool.

### An assistant must be able to finish the job without a shell

Every capability the CLI has, the MCP surface has, except discarding a
credential. A tool that can only tell someone to go and run a command ends the
conversation the surface exists to have. When adding a CLI command, ask whether
an assistant would need it mid-conversation.

The exception is least privilege, not omission: no logout tool, because an agent
that can discard a credential unprompted is a hazard with no matching benefit.

### The account adapters re-read the token on every call

So authorizing during a session reaches a server started without a token, with
no restart. `Session.bearer()` loads the store each time; keep it that way.

### The MCP boundary holds registration and nothing else

Rules live under it. A tool module is a plain function over a `Workspace`, and
`server.py` binds it. Nothing below `mcp/` imports it.

### Planning writes nothing; applying is the only writer

`playlist plan` reads. `playlist apply` is the single place in jukebox that
changes someone's account, and it confirms first. Keep it that way: a model
drives this, and a write must never be a side effect of asking a question.

### A spec is evaluated against the corpus, never against a service

`jukebox spec preview` reads `data/charts/` and nothing else. Resolution to track
URIs is a separate step, which is what keeps a spec vendor-neutral, keeps it
committable, and makes a preview instant and offline.

### Where things live is decided in one place

`Paths.resolve()` is the only thing that answers it. Two roots: **data** for what
cannot be rebuilt (specs, ledger, refresh token) and **cache** for what a command
regenerates (corpus, resolutions). Never resolve a store against the working
directory — that produces a second, empty everything when the command is run from
elsewhere, and it is how the user's own specs ended up committed to this repo.

A test must set `JUKEBOX_HOME` (the `home` fixture does it) or it will read and
write the developer's real data.

### Neither the corpus nor the caches are committed

`data/charts/` is gitignored along with `data/resolutions/` and `.jukebox/`, for
two different reasons. Spotify content may not be stored at all. The corpus
could be redistributed under Wikipedia's licence, but it is a machine-readable
mirror of Billboard's compiled charts and is regenerated in seconds, so it is
treated as a build artifact. `tests/standards/` asserts both, and a test never
depends on a committed corpus — build one in `tmp_path` from
`tests/support/corpus.py`, or read the committed fixtures.

### No Spotify Content is ever committed

The developer terms allow only *temporary* caching of metadata and forbid storing
or aggregating Spotify Content into a database; a file in git is permanent and
redistributable. So track URIs, titles and artists from Spotify live only in the
gitignored `.jukebox/` cache, which is disposable and rebuilt by `resolve backfill`.
The chart corpus under `data/charts/` is Wikipedia's and Billboard's, not Spotify's,
and is committed. `NOTICE.md` carries the full position; read it before adding a new
data file or a new service.

The same terms forbid ingesting Spotify Content into an AI model. The assistant
reasons over the chart corpus; Spotify identifiers are produced and written by code.

### A music service is an adapter behind a port

`ports/` holds the contracts (`ProviderAuth`, `Credentials`); `providers/spotify/` is one
implementation. Adding Apple Music or Tidal is a new adapter plus a `providers/registry.py`
entry — no command, spec or operation learns a second vendor's name. Anything reusable
across services (PKCE, the loopback catcher, token storage and refresh) belongs in
`oauth/`, not in an adapter.

### Spotify auth is a public client

OAuth PKCE with a loopback redirect. There is no client secret, so there is no secrets
provider in this repo. The client id is configuration (`JUKEBOX_SPOTIFY_CLIENT_ID`); the
refresh token is a credential and lives only under `.jukebox/`, mode 0600.

Spotify permits HTTP for a redirect **only** for a loopback IP literal, and rejects
`localhost` outright — so the redirect URI is `http://127.0.0.1:8888/callback`. A refresh
response may omit a new refresh token, and the one already held stays valid: dropping it
there silently downgrades the client to one hour of access.

### A Typer object must not share its module's name

`from jukebox.cli.auth import auth` binds `jukebox.cli.auth` to the Typer app and shadows
the module, so anything reaching for the module gets the app. Sub-command modules export
`commands`, and `cli/__init__.py` imports the module.

### External APIs are rate-limited and must be politely so

MusicBrainz asks for ~1 request/second and a descriptive User-Agent. Spotify rate-limits
on a rolling 30-second window and answers 429 with `Retry-After`. A full backfill is a
background job, not an interactive call.

### A Spotify quota is not a rate limit, and pacing only answers one of them

Spotify enforces both. A **rate limit** counts calls in a rolling thirty-second window;
`providers/spotify/client.py` paces requests to stay inside it. A **quota** counts how
many calls are made at all, and spacing them out answers nothing: the budget is spent,
not outrun. A 429 names which, in `error.reason`, and `Throttled` carries it — a refusal
reading `QUOTA_EXCEEDED` means wait, never slow down.

Development mode is the default for a new app and is quota-bound in practice: a few
hundred search calls exhausts a budget that then refuses for the better part of a day,
whatever interval those calls were spaced at.

**The quota is per developer account, not per app.** Since 23 July 2026 every
development-mode client id shares one budget, so a second application inherits the
first's countdown to the second and registering one buys nothing.

**Extended quota mode is not available to a project like this.** Since 15 May 2025
Spotify accepts applications only from organizations with a registered entity, a launched
service and at least 250,000 monthly active users. Plan around the development-mode
budget rather than expecting to escape it: resolution is resumable and every pass is
saved, so the way through is several short runs across days.

Past the ceiling the client refuses instead of retrying, because a retry inside the pause
the service asked for is another request against the window already refusing it.

## Local Conventions

- **One class per module**, named after it; packages group by theme (`ports/`, `values/`).
- **No lint suppressions** — restructure instead of adding `# noqa`, `# type: ignore`, or
  raising a threshold.
- **No historical content in comments, docstrings, or instruction files.** Describe what
  is, never how it got there.
- **Depend on abstractions at the boundaries.** `catalog` and `specs` never import
  `httpx`; network lives behind `ChartSource`, `Resolver`, `SpotifyClient`.
- Chart data and test fixtures are Wikipedia-derived and carry CC BY-SA 4.0. Keep the
  `source` and `retrieved` fields populated — they are the attribution.
