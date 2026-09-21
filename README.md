# jukebox

Build playlists from published lists of recordings, by chatting with Claude.

> "I'm a child of the 80s and 90s, I listen to every kind of popular music —
> make me a playlist for each genre."

jukebox has two ends and a middle. At one end a **source** supplies a published
list of recordings. In the middle a **corpus** holds those lists as fact, and a
**spec** selects from them. At the other end a **provider** finds each recording
in a catalogue and writes the playlist to an account.

Both ends are adapters. This repository ships one of each: Billboard charts read
from Wikipedia, and Spotify. [Extending jukebox](#extending-jukebox) describes
what another one must supply.

## Why it exists

Spotify's Web API cannot answer "what was popular, and in what genre". It has no
`recommendations`, no `related-artists` and no `audio-features` for new apps. It
has no *Get Artist's Top Tracks*, no `Get Several …` batch endpoints, no
`popularity` field on tracks, artists or albums, and no `genres` field on
artists. `/search` returns ten results at most.

What Spotify does well is search, create a playlist, and add items to it.

So jukebox inverts the problem. Billboard's year-end charts record what was
popular, per genre, per year, and Wikipedia publishes them as clean tables.
Those are the source of truth for *what*. Spotify resolves *which recording* and
holds the finished playlist. Claude turns a sentence into selection predicates.

A genre playlist here is a genre *chart*, not a tag someone inferred.

Charts are one kind of source. Any published list of recordings fits: a
station's most-played year, a festival lineup, an awards shortlist, a magazine's
records of the year. The corpus asks for two things. Each row names a title and
an artist, and the list is either ranked or dated.

The types are named for charts. Read `Chart` as "one published list".

## Shape

Claude talks to jukebox over MCP. Below that surface sit three kinds of data,
kept apart because they have three different lifetimes:

| | What | Lifetime | Lives in |
|---|---|---|---|
| **Corpus** | chart rows: rank, title, artist, chart, year | immutable historical fact | your cache directory, rebuilt on demand |
| **Resolutions** | chart entry to Spotify URI, with method and confidence | slow to compute, disposable | your cache directory |
| **Ledger** | per spec: playlist id and the exact URIs last written | live account state | your data directory |

The ledger keeps the whole URI list, not only the playlist id, and that is what
makes your manual edits survive. Two lists can compute a difference but cannot
attribute it. A track on the playlist and absent from the spec is either
something you added or something the spec dropped, and only the record of what
jukebox last wrote tells them apart.

A **spec** describes a playlist. It is a validated object rather than prose, so
the same spec rebuilds the same playlist. Claude writes one from the
conversation.

```yaml
name: 90s Alt-Rock
select:
  charts: [modern-rock]
  years: [1990, 1999]
  max_rank: 40      # ranked charts only
  min_weeks: 2      # number-ones charts only
shape:
  size: 80
  max_per_artist: 2
  order: chart      # or year, or shuffle with a fixed seed
exclude:
  - title: Shout    # by the chart's own words, never a track id
```

A spec is evaluated against the corpus alone, so `jukebox spec preview` contacts
no music service. `max_rank` narrows a year-end list and leaves a number-ones
list untouched, because every row of one was already first. `min_weeks` is its
counterpart. No ordering ranks a year-end position against a week at number one:
those are different published measures, and one sequence over both would be a
composite invented here.

## Resolving a chart entry

Spotify publishes no `popularity`, so "search and take the top hit" has nothing
to rank ten candidates by. Scored search is the default path.

A candidate scores on normalized title and artist. Qualifiers like `(7"
Version)`, `- Remastered` and `- From "Beverly Hills Cop"` are stripped before
comparison. Release year breaks ties and nothing more, since a 1985 master
reissued on a 2010 compilation is still the right recording. Karaoke, tribute,
live and re-recorded pressings are penalized on **whole-word** match: a
substring test reads `Separate Lives` as a live recording and rejects the
correct answer.

A chart cell credits a collaboration as one string, such as `Philip Bailey and
Phil Collins` or `Ray Charles (with Willie Nelson)`. That matches no artist
filter, so each credited artist is tried in turn.

ISRC lookup is opt-in (`--isrc`). Against the 1985 Hot 100, MusicBrainz held an
ISRC for 3 entries in 25, at roughly two seconds a lookup, and search answered
the rest.

Against that same year it resolves 100 of 100. Whatever it cannot place is named
in the report rather than dropped.

A large backfill meets Spotify's rate limit. Two things make that survivable.
Every resolution is cached with the method and confidence that produced it, and
progress reaches disk even when a run dies partway. So the answer to a refusal
is to run it again, never to start over. That cache is machine-local and never
committed: Spotify's developer terms allow only temporary caching of metadata,
so it is disposable and `resolve backfill` rebuilds it.

## Writing to Spotify

Applying a spec is a three-way difference: what the spec wants, what is on the
playlist now, and what jukebox itself last wrote. Your manual additions are
reported and kept. Dropping them takes `--replace-manual`.

`jukebox playlist plan` resolves and diffs and writes nothing. `apply` is the
only command that touches your account, and it asks first unless given `--yes`.

The reconciler settles the whole final ordering before it sends anything, so
add, remove and reorder are one replace with different arguments rather than
three separate edits. Spotify caps a write at a hundred items, so a longer
playlist is a replace followed by appends. That is more than one request, and
therefore interruptible. Two things make it safe: the write retries the statuses
that pass on their own, and what it is about to write reaches disk before
anything is destroyed. If a run is interrupted part-way it leaves a truncated
playlist, and the next apply restores what it was carrying, including tracks you
added by hand that exist nowhere else.

## What works today

The chart corpus, authorization, resolution, playlist specs, the reconciling
writer, and the MCP surface an assistant drives.

### Getting it running

The project is an ordinary uv project, and that is the supported route for
everyone:

```bash
uv sync --all-groups     # a virtualenv with the project and its test deps
uv run pytest            # the suite
uv run jukebox --help
```

A `devenv.nix` also exists. `devenv shell` gives the same venv plus the git
hooks, and it is optional. Both routes build that venv from `pyproject.toml` and
`uv.lock`, so they reach the same Python. CI takes the uv route on every push,
which is what keeps it honest.

### Then

```bash
# create an app at developer.spotify.com/dashboard with redirect URI
# http://127.0.0.1:8888/callback, then either tell the assistant its client id
# when it asks, or for the command line:
export JUKEBOX_SPOTIFY_CLIENT_ID=<your app's client id>

uv run jukebox auth login                          # consent in the browser
uv run jukebox auth status                         # what is stored, until when
uv run jukebox charts fetch --year 1985            # builds the corpus, reports gaps
uv run jukebox resolve backfill --year 1985        # matches entries to tracks
uv run jukebox resolve retry   --year 1985         # asks again for what it missed
uv run jukebox songs build --years 1985            # the corpus as songs and artists
uv run jukebox songs artist --name "Madonna"       # everything one act charted
uv run jukebox spec add "85 R&B" --chart rnb --years 1985
uv run jukebox spec shape "85 R&B" --size 40 --max-per-artist 2
uv run jukebox playlist plan  "85 R&B"             # what would change; writes nothing
uv run jukebox playlist apply "85 R&B"             # asks before touching the account
uv run jukebox serve mcp                           # the surface Claude drives
uv run pytest                                      # the suite, 100% coverage
uv run pytest -m network                           # checks every chart page still parses
```

Coverage runs 1980–1999 across nine charts. What it cannot cover it names with
the reason: rap begins in 1989, modern rock in 1988, mainstream rock in 1981 and
Latin in 1986, because that is when those charts began.

## Extending jukebox

### Adding a provider

Nothing above `jukebox.ports` names Spotify. Four protocols define a provider:

| Port | Answers |
|---|---|
| `ProviderAuth` | obtain, report and discard a user's authorization |
| `Credentials` | the bearer token a request carries |
| `MusicCatalog` | search for a recording, or look one up by ISRC |
| `PlaylistService` | create, find, read and replace a playlist |

`PlaylistService` has four operations and no `add` or `remove`. The reconciler
settles the whole final order before it writes anything, so replacing a list is
the only mutation it needs. Adding, removing and reordering are that same call
with different arguments, and three more chances to get an edit wrong.

Authorization differs completely between services, so `ProviderAuth` describes
no flow. Spotify uses OAuth PKCE over a loopback redirect. Another service can
use a device code or a signed developer token. An adapter obtains credentials
however its service requires, provided it answers those three questions.
Whatever is reusable across services lives in `jukebox.oauth` and names none of
them: PKCE, the loopback catcher, token storage and refresh.

To add one, write `providers/<name>/` and add an entry to `PROVIDERS` in
`providers/registry.py`. The entry gives the name, what the service needs from a
user, and three factory functions. Everything above routes by name already:
`jukebox auth login --provider <name>` on the command line, `list_providers` and
`use_provider` over MCP.

### Adding a source

`ChartSource` is the only seam that touches the network, which is what keeps
parsing testable offline:

```python
class ChartSource(Protocol):
    def fetch(self, title: str) -> str:
        """The rendered HTML of the page with this title."""
```

`MediaWikiSource` reads Wikipedia. `FixtureSource` reads saved files, which is
how the parser tests run without a network.

A source that is not a web page needs no `ChartSource` at all. Write `ChartFile`
objects into the `Corpus` and everything above them works unchanged. Specs
select from them, the resolver matches them, the reconciler writes them, and the
MCP surface reads them.

Three parts of the corpus vocabulary are closed sets. A new kind of list extends
them:

| What | Where | To add one |
|---|---|---|
| the lists themselves | `Chart`, a `StrEnum` of slugs, each with the year it began | add a member |
| the page layouts | `PageShape`, with a mapper per shape under `charts/mappers/` | add a shape and its mapper |
| the row kinds | `EntryKind`: ranked, or number one | add a kind, and give `EntryFilter` its measure |

A ranked row carries a position. A number-one row carries the date it reached
the top and the weeks it held. Those two cover any list that is ranked or dated.
A list measured another way, by play count or by nothing at all, needs a third
kind, and `EntryFilter` needs to know which rows that measure applies to.

That last rule is the one to keep. A measure a row does not publish must never
exclude it. A rank ceiling leaves a number-ones list alone, because every row of
one was already first, and a weeks floor leaves a ranked list alone for the
matching reason.

## Chatting with it

Register the server once, from the clone:

```bash
claude mcp add jukebox -- uv run --directory "$PWD" jukebox serve mcp
```

`--directory` matters because the client launches the server from wherever it
happens to be.

Nineteen tools, and an assistant can run the whole thing without sending you to
a shell. That includes choosing the service and application, so nothing has to
be configured before you launch the client:

| Tools | What they do |
|---|---|
| `list_providers`, `use_provider` | choose the music service and application |
| `auth_status`, `auth_login` | obtain permission |
| `fetch_charts`, `resolve_charts` | fill the corpus |
| `list_charts`, `query_charts` | read it as lists |
| `build_index`, `index_status`, `find_song`, `artist_songs`, `crossovers` | read it as songs and artists |
| `put_spec`, `get_spec`, `list_specs`, `preview_spec` | describe a playlist |
| `plan_playlist` | say what applying would change |
| `apply_playlist` | the only one that alters your account |

Only that last one needs asking about. Fetching reads Wikipedia and writes chart
files. Resolving writes a machine-local cache. Neither touches your account.
There is no logout tool: discarding a credential has no use in a conversation
about playlists, and `jukebox auth logout` does it.

They are query primitives rather than a `suggest_playlist` that returns a
finished tracklist. That tool would answer only the question its author
imagined, and the point of a corpus is that a model can compose over it.

What crosses the wire is the charts' vocabulary and counts: titles and artists
as Billboard published them, never Spotify's catalogue data. The developer terms
forbid ingesting Spotify Content into an AI model, so track identifiers stay
between the resolver and the writer. A test asserts it.

## Where jukebox keeps things

Nothing lives in this checkout. Two roots, because two lifetimes:

| | Holds | Default |
|---|---|---|
| **data** | your playlist specs, the apply ledger, the refresh token | `$XDG_DATA_HOME/jukebox`, else `~/.local/share/jukebox` |
| **cache** | the chart corpus and the resolutions | `$XDG_CACHE_HOME/jukebox`, else `~/.cache/jukebox` |

Nothing in the cache is irreplaceable. `jukebox charts fetch` and `jukebox
resolve backfill` rebuild all of it in about a minute, so deleting it costs only
time. The data directory is the opposite: losing it means re-authorizing and
rewriting playlists by hand.

`JUKEBOX_HOME` overrides both and puts everything under one directory, which is
what a project-local workspace or a test wants.

A spec is your writing rather than this project's content, which is why it lives
with your data and not in the repository.

## Licence

Apache-2.0; see [LICENSE](LICENSE). The Wikipedia-derived test fixtures carry
CC BY-SA 4.0 separately, and [NOTICE.md](NOTICE.md) says which files and why.

## Attribution and terms

The test fixtures are seven Wikipedia article fragments, redistributed under
CC BY-SA 4.0 and attributed per file in NOTICE.md.

The chart corpus is **not** committed. The licence would allow it, but the
assembled corpus is a machine-readable mirror of two decades of Billboard's
compiled charts, which is a further step than citing the facts it holds. It is
gitignored and rebuilt on demand.

ISRC lookup uses MusicBrainz, whose core data is CC0. No Spotify Content is
stored here at all. See [NOTICE.md](NOTICE.md).

**A fresh clone has no corpus.** Run `jukebox charts fetch --year <year>`, or
ask the assistant: `fetch_charts` builds twenty years in about a minute.
