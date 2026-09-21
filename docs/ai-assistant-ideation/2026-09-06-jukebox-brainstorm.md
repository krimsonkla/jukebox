# jukebox — brainstorm

> **Superseded in places.** This records the design as it was decided, not as it
> now stands. The chart corpus and the resolution cache were later moved out of
> the repository entirely, playlist specs were moved to the user's data
> directory, and exclusions key on a chart's own title and artist rather than a
> track identifier. `NOTICE.md` and the README describe what is true today.

Status: approved 2026-09-06.

## Problem

Build Spotify playlists on the developer's own account by describing what is
wanted in conversation, rather than by assembling them by hand. The motivating
request: *"I'm a child of the 80s and 90s, I listen to every kind of popular
music — create playlists for each genre."*

## The constraint that shapes everything

The Spotify Web API cannot answer the question the premise assumes.

- **2024-11-27**: `audio-features`, `audio-analysis`, `recommendations`,
  `related-artists`, featured and category playlists were restricted to apps
  that already held a quota extension. No replacement, no waitlist, and eighteen
  months later no reversal.
- **February 2026**: *Get Artist's Top Tracks* removed. Every `Get Several …`
  batch endpoint removed. `popularity` removed from track, artist and album.
  `genres` removed from artist. `/search` `limit` reduced from 50 to 10.
  Playlist item endpoints restructured to `/playlists/{id}/items`.

What survives and is load-bearing here: `/search` (including the `isrc:` and
`year:` filters), create playlist, and playlist item add/remove/reorder.
`external_ids` — and therefore a track's ISRC — was removed in February 2026 and
reinstated in March 2026.

The consequence is that Spotify can no longer supply the taxonomy or the
popularity ordering. Both must come from outside it.

## Approach

Billboard year-end charts already record what was popular, per genre, per year,
and Wikipedia publishes them as uniform wikitables of rank / title / artist.
They are the source of truth for *what*. Spotify resolves each entry to a URI
and receives the writes. Claude turns a sentence into selection predicates.

A genre playlist is therefore a genre *chart*, not an inferred tag — a published
index rather than a composite invented here.

## Decisions

| Decision | Chosen | Rejected, and why |
|---|---|---|
| Interface | **MCP server**; Claude Desktop / Claude Code is the chat | A standalone chat app means building and paying for a conversation loop that already exists. A spec-only CLI is reproducible but abandons the conversational premise. |
| Chart data | **Vendored snapshot** — a CLI scrapes Wikipedia once, parsed rows are committed | Live fetch makes every build network-dependent and non-reproducible. Adding MusicBrainz/Last.fm genre tags buys finer genres at the cost of two more APIs and a crowd-sourced folksonomy in place of a published chart. |
| Resolver | **ISRC-first via MusicBrainz, fuzzy fallback** | Fuzzy-only is simplest but its misses are silent, and with `popularity` gone there is nothing to rank ten search hits by. Reviewing every uncertain match is the most accurate and makes a two-decade backfill a wall of questions. |
| Write model | **Reconcile in place**, manual additions kept by default | Create-new-each-time fills the library with near-duplicates. Tool-owns-completely is the simplest reconciler but deletes hand-picked tracks without warning. |

## Structure

Three kinds of data with three different lifetimes, kept in three stores.
Conflating them is what would make the system slow and non-reproducible.

| | Lifetime | Location |
|---|---|---|
| Corpus — chart rows | immutable historical fact | `data/charts/`, committed |
| Resolutions — entry to URI, with method and confidence | slow to compute, human-correctable | `data/resolutions/`, committed |
| Ledger — playlist id and the exact URIs last written, per spec | live account state | `.jukebox/`, gitignored |

Modules, one purpose each, with ports at the external boundaries
(`ChartSource`, `Resolver`, `SpotifyClient`) so the corpus and resolver are
testable against fixtures with no network:

```
src/jukebox/
  charts/     wikipedia fetch, wikitable parse, the chart-name-per-year map
  catalog/    corpus query API — the primitives the model composes over
  resolve/    musicbrainz ISRC lookup, spotify isrc: search, fuzzy fallback
  spotify/    OAuth PKCE + a thin typed client on February-2026 shapes
  specs/      spec model, validation, selection to tracklist
  reconcile/  desired vs live vs last-applied, then apply
  mcp/        the tool surface
  cli/        auth login, charts fetch, resolve backfill, build
```

## The spec

A validated structured object, not prose. Claude writes it from the
conversation; being structured is what makes a rebuild deterministic, and what
keeps a second LLM call out of the tool layer.

```yaml
name: "90s Alt-Rock"
select:
  charts: [modern-rock]
  years: [1990, 1999]
  max_rank: 40
shape:
  size: 80
  max_per_artist: 2
  order: chart_rank
  exclude:
    - title: Shout        # by the chart's words, never a track id
```

## MCP surface

Primitives the model composes, and a hard separation between reading and
writing. A tool that returned a finished tracklist would answer only the
question its author imagined.

- `list_charts()` — coverage per chart, per year
- `query_charts(charts, years, rank_range, artist)` — rows
- `put_spec(spec)` / `get_spec(name)` / `list_specs()`
- `preview_spec(name)` — resolves and diffs; **writes nothing**
- `apply_spec(name)` — the only tool that touches the account
- `record_resolution(entry, uri)` — a correction, made once

## Reconciliation

`live − last_applied` is the set of manual additions. `desired − live` is the
work. The ledger stores the full URI list rather than only the playlist id,
because without it a hand-added track is indistinguishable from one the spec has
abandoned.

## Out of scope

Web UI, playback control, cover-art generation, genre inference beyond which
chart a song appeared on, non-US and non-Billboard charts, anything multi-user.
The app stays in Spotify development mode: one account, no quota extension.

## Build order

The two genuine unknowns come first, because both are cheap to measure on a
single year and expensive to discover after a full backfill.

1. Parse one year across all charts — proves wikitable parsing and, more
   importantly, twenty years of chart-name drift (*Hot Black Singles* to *Hot
   R&B/Hip-Hop*, *Top Rock Tracks* to *Mainstream Rock Tracks*).
2. Resolve that one year — measures the real ISRC hit rate on 1980s catalogue.
   If it is 40% rather than 90%, the fuzzy fallback is the main path and gets
   the effort budget.
3. Full backfill 1980–1999, spec model and evaluation, reconciler, MCP surface.

## Chart set

Hot 100 (as pop), Country, R&B, Dance/Club Play, Mainstream Rock, Modern Rock,
Rap (from 1989), Latin — each under its era-correct name per year.

## Sources

- <https://developer.spotify.com/blog/2024-11-27-changes-to-the-web-api>
- <https://developer.spotify.com/documentation/web-api/references/changes/february-2026>
- <https://developer.spotify.com/documentation/web-api/concepts/rate-limits>
- <https://en.wikipedia.org/wiki/Billboard_Year-End>
