# Spec — the chart corpus

> **Superseded in places.** This records the design as it was decided, not as it
> now stands. The chart corpus and the resolution cache were later moved out of
> the repository entirely, playlist specs were moved to the user's data
> directory, and exclusions key on a chart's own title and artist rather than a
> track identifier. `NOTICE.md` and the README describe what is true today.

Slice 1 of the build order in
[the brainstorm](2026-09-06-jukebox-brainstorm.md). Scope is the `charts` module
and nothing else: no Spotify, no resolver, no specs, no MCP.

## Problem

Every later slice consumes the corpus, so if the corpus is wrong or thin, the
whole project is. The brainstorm asserted that Billboard year-end charts are
available per genre per year on Wikipedia as uniform tables. **Investigation
before writing this spec refuted that**, and the corrected picture is what this
slice is designed around.

### What Wikipedia actually publishes

Three different page shapes, not one — and within shape B, four distinct
layouts that a single mapper has to absorb:

| Shape | Example title | Columns | Coverage |
|---|---|---|---|
| **A — year-end ranked**, per year | `Billboard Year-End Hot 100 singles of 1985` | rank, title, artist | Hot 100 every year; R&B and Rap for some years only |
| **B — number-ones**, per year | `List of Hot Country Singles number ones of 1985` | issue date, title, artist | most genre charts, most years |
| **C — number-ones**, per decade | `List of Billboard Modern Rock Tracks number ones of the 1990s` | song, artist, reached number one, weeks at number one; **year comes from the full date in the date column** | the rock charts |

Three further complications, all confirmed by inspection rather than assumed:

- **Chart names drift within the era.** *Hot Black Singles* becomes *Hot
  R&B Singles*; *Top Rock Tracks* becomes *Mainstream Rock*. The title of the
  page for a given chart depends on the year.
- **Shape C pages straddle year boundaries.** The 1990s Modern Rock page opens
  with an entry dated 30 December 1989. Year is taken from the parsed date and
  rows outside the requested year discarded. Section headings are not usable:
  the page has a single `Number-one songs` heading, and the only per-year marker
  is an `{{anchor}}` buried mid-cell.
- **One chart page can hold two charts.** The 1985 dance page tabulates Club Play
  and 12-inch Singles Sales side by side under a two-level header, with `rowspan`
  cells carrying a title across the weeks it held the top spot and `Not issued`
  placeholders where a chart did not run that week.
- **Coverage is genuinely absent in places**, not merely differently named.
  There is no year-end Country, Dance, Mainstream Rock, Modern Rock or Latin
  article for 1985. Modern Rock does not exist as a chart before September 1988.
- **A page can separate its years with a banner row.** The mainstream rock
  decade page is an issue-date table whose dates carry no year; the year is
  announced by a row whose every cell is `1990`. It also gives weeks at number
  one as a column rather than by repeating a row.
- **The rank header is spelled two ways.** Several year-end pages head the rank
  column `№` rather than `No.`.

### Ranges are declared only where they parse

Resolving to a live page is not evidence: the 1982–1984 dance pages resolve and
then tabulate different columns, and the 1980 dance page is a redirect. So each
registry range was swept against the live encyclopaedia and narrowed to the
years that actually map to entries. `tests/charts/test_live_pages.py` repeats
that sweep for every declared range across 1980–1999, and is the mechanism that
catches a rename or a re-layout.

### Consequence for the corpus model

A row cannot be "rank N in year Y" because shapes B and C have no rank. The
corpus therefore carries two row kinds, and a playlist spec selects over both:

- `ranked` — carries `rank`; from shape A
- `number_one` — carries `reached` (date) and `weeks` (integer, where the page
  gives it); from shapes B and C

Both remain published indexes. A playlist of every Country number one from
1980–1999 is a defensible "popular country music of the era" and requires no
invented score — which was the point of using charts at all.

## Goal

A committed corpus covering the eight target charts for **one year (1985)**,
produced by a re-runnable CLI command, parsed behind a port, and reported on
honestly — including where coverage does not exist.

1985 is chosen deliberately: it exercises shape A (Hot 100), shape B (Country,
Dance, R&B via *Hot Black Singles*), an era-drifted name, and a chart that does
not yet exist (Modern Rock, which begins in 1988). A year where everything
worked would prove less.

## Design

### Parse rendered HTML, not wikitext

Investigation settled this. In wikitext a country row reads:

```
!scope=row|{{dts|January 5}}
|"{{sort|Best|[[The Best Year of My Life (song)|The Best Year of My Life]]}}"
|{{sortname|Eddie|Rabbitt}}
```

Parsing that means reimplementing `{{sortname}}`, `{{sort}}`, `{{dts}}` and link
piping, and it still leaves `rowspan` — which on the dance page carries a title
across several weeks — as something to simulate by hand.

The MediaWiki `action=parse` API returns the same row as HTML with every
template already expanded and `rowspan`/`colspan` as explicit attributes. A
single rowspan-aware grid extractor then reduces any of the shapes to a dense
table of plain strings, and each shape becomes a column mapping rather than a
parser. Prototyped against all four fixtures before this spec was finalised: 101
rows for Hot 100, 53 for country, 54 for the two-chart dance table, 168 for the
modern rock decade.

```
src/jukebox/charts/
  chart.py            Chart          — the eight charts as an enum
  page_shape.py       PageShape      — RANKED | NUMBER_ONES | DECADE
  page_ref.py         PageRef        — title and shape for one (chart, year)
  gap.py              Gap            — a (chart, year) with no page, and why
  registry.py         Registry       — (chart, year) -> PageRef | Gap
  chart_source.py     ChartSource    — Protocol: fetch(title) -> html
  mediawiki_source.py MediaWikiSource — action=parse over httpx
  fixture_source.py   FixtureSource  — reads tests/fixtures/pages/, no network
  grid.py             Grid           — rowspan/colspan expansion to dense text
  cell.py             clean_cell     — br to space, strip refs, quotes, daggers
  entry.py            ChartEntry     — one corpus row
  mappers/
    ranked.py         RankedMapper       — shape A
    number_ones.py    NumberOnesMapper   — shape B, incl. the two-chart header
    decade.py         DecadeMapper       — shape C, filters by parsed date year
  corpus.py           Corpus         — load, merge, write data/charts/
  report.py           CoverageReport — what was found, what is absent, and why
```

The registry is data, not code branching on year: a table of
`(chart, year_from, year_to) -> (title_template, shape)`. A missing entry is a
first-class **gap** with a recorded reason (`chart did not exist`,
`no article published`), never a silent empty result. Gaps are asserted in
tests, so a chart quietly vanishing from Wikipedia fails the suite rather than
producing a shorter playlist.

`ChartSource` is the only thing that touches the network. Mappers take a grid
and return rows, so every mapper test runs against committed fixtures offline.

### Corpus on disk

One JSON file per chart per year, `data/charts/<chart>/<year>.json`, sorted by
rank then date so a re-fetch produces a reviewable diff rather than a reordering.

```json
{
  "chart": "hot-100",
  "year": 1985,
  "kind": "ranked",
  "source": "Billboard Year-End Hot 100 singles of 1985",
  "retrieved": "2026-09-06",
  "entries": [
    {"rank": 1, "title": "Careless Whisper", "artist": "George Michael"}
  ]
}
```

## Acceptance criteria

1. `jukebox charts fetch --year 1985` writes corpus files for every chart the
   registry resolves, and prints a coverage report naming each gap and its
   reason.
2. The Hot 100 file for 1985 contains exactly 100 ranked entries, rank 1 is
   *Careless Whisper* by George Michael, and rank 100 is *Sugar Walls* by Sheena
   Easton.
3. The Country file for 1985 contains 52 `number_one` entries, the first being
   *Does Fort Worth Ever Cross Your Mind* by George Strait dated 5 January.
4. R&B for 1985 resolves through the era name *Hot Black Singles*, and R&B for
   1995 resolves through *Hot R&B Singles* — the same `Chart.RNB` in both cases.
5. Modern Rock for 1985 is reported as a gap with reason "chart did not exist",
   and the command exits zero. Absence is data, not failure.
6. The decade mapper takes each row's year from its parsed date and drops rows
   outside the requested year — specifically, the 30 December 1989 Modern Rock
   entry does not appear in the 1990 file.
7. Cell text is plain: reference superscripts removed, `<br />` rendered as a
   space (so the header reads `Weeks at number one`, not `Weeks atnumber one`),
   wrapping double quotes and `†` markers stripped from titles, and a
   multi-artist cell preserved as written rather than split.
10. The grid expands `rowspan` and `colspan`, so the 1985 dance table yields a
   dense six-column grid in which a title held for three weeks appears against
   each of those weeks, and `Not issued` is recorded as absent rather than as a
   song.
11. The two-level dance header resolves to distinct charts, so Club Play and
   12-inch Singles Sales are written as separate corpus files.
8. Every parser test runs from a committed fixture with no network access.
9. Re-running fetch against unchanged fixtures produces a byte-identical corpus.

## Testing strategy

- **Grid tests** against committed HTML fixtures — rowspan carry, colspan
  duplication, two-level headers, and the `Not issued` placeholder.
- **Mapper unit tests**, one per shape, plus the awkward cells found in the real
  pages: a footnote superscript, a `<br />` header, a dagger-marked title, an
  unlinked plain-text title, and a two-artist cell.
- **Registry tests** — name drift resolves to the right title per year, and
  every declared gap has a reason. A staleness test fails if a gap entry stops
  being reachable, so the gap list cannot quietly rot.
- **Corpus round-trip** — write, re-read, compare; and fetch twice, assert
  byte-identical output.
- **Network tests** marked `network` and deselected by default, asserting that
  each registry title still resolves to HTTP 200 and still contains a wikitable.
  These are how a Wikipedia rename gets caught, and they are run deliberately.
- Coverage floor is 100% on `src/jukebox/charts/`, per the repo's DoD.

## Out of scope

Years other than 1985 (the full 1980–1999 backfill is a later slice, and is a
loop over this command once the registry is complete), Spotify, MusicBrainz,
resolution, specs, reconciliation and the MCP surface.
