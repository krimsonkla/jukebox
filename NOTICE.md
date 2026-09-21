# Third-party data and terms

jukebox reads from three services, under three different regimes. This file
records what is redistributed in this repository and under what terms.

## Wikipedia — CC BY-SA 4.0, redistributed here

One kind of file in this repository is derived from the English Wikipedia:
`tests/fixtures/pages/*.html`, seven captures kept so the parser tests run
without a network. Each is the unaltered payload of a MediaWiki
`action=parse&prop=text` request — the article's rendered HTML fragment rather
than a whole page, which is why none carries an in-band licence notice.

Attribution therefore has to travel here, since it cannot travel in the files:

| File | Article | History |
|---|---|---|
| `hot100-1985.html` | Billboard Year-End Hot 100 singles of 1985 | <https://en.wikipedia.org/wiki/Billboard_Year-End_Hot_100_singles_of_1985?action=history> |
| `rnb-1985.html` | Billboard Year-End Hot Black Singles of 1985 | <https://en.wikipedia.org/wiki/Billboard_Year-End_Hot_Black_Singles_of_1985?action=history> |
| `country-1985.html` | List of Hot Country Singles number ones of 1985 | <https://en.wikipedia.org/wiki/List_of_Hot_Country_Singles_number_ones_of_1985?action=history> |
| `dance-1985.html` | List of Billboard number-one dance/disco singles of 1985 | <https://en.wikipedia.org/wiki/List_of_Billboard_number-one_dance/disco_singles_of_1985?action=history> |
| `modernrock-1990s.html` | List of Billboard Modern Rock Tracks number ones of the 1990s | <https://en.wikipedia.org/wiki/List_of_Billboard_Modern_Rock_Tracks_number_ones_of_the_1990s?action=history> |
| `mainstreamrock-1980s.html` | List of Billboard Mainstream Rock number-one songs of the 1980s | <https://en.wikipedia.org/wiki/List_of_Billboard_Mainstream_Rock_number-one_songs_of_the_1980s?action=history> |
| `mainstreamrock-1990s.html` | List of Billboard Mainstream Rock number-one songs of the 1990s | <https://en.wikipedia.org/wiki/List_of_Billboard_Mainstream_Rock_number-one_songs_of_the_1990s?action=history> |

Each article's authors are its contributors, listed in the linked history.

The chart corpus itself is **not** redistributed here. See *The corpus is not
committed* below.

Wikipedia text is licensed
[CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/). Attribution is
to the contributors of each named article; the article title in a chart file's
`source` field identifies it, and its history is at
`https://en.wikipedia.org/wiki/<article title>`.

**Changes made:** none. The bytes are the API payload as served.

**Share-alike:** these files, and any adaptation of them, carry CC BY-SA 4.0.
That obligation attaches to the Wikipedia-derived fixtures, not to the source
code in `src/`, which is a separate work that merely reads them.

## The corpus is not committed

`jukebox charts fetch` writes `data/charts/`, which is gitignored and rebuilt on
demand in seconds by that command or the `fetch_charts` tool.

Wikipedia's licence would permit redistributing it with attribution, so this is
a choice rather than a requirement. The reason is what the corpus *is*: a
machine-readable mirror of two decades of Billboard's compiled charts across
nine of them. Citing that a record was number one is using a fact, which no
copyright reaches; publishing the complete compilation is a further step, and
one that sits differently under database rights outside the United States.

A corpus file records the article it came from in `source` and the date in
`retrieved`, so attribution travels with that data too — but the corpus is not
redistributed here, and the table above is what discharges the obligation for
what is.

## Billboard — facts, obtained from Wikipedia

jukebox is not affiliated with, endorsed by, or sponsored by Spotify, Billboard,
Wikipedia or MusicBrainz. Those names are used only to say what the tool talks
to. The charts themselves are compiled by Billboard. jukebox does not access
billboard.com, its API, or any Billboard property, and is not affiliated with or
endorsed by Billboard. It reads chart positions as published by Wikipedia
contributors, and does not redistribute the assembled result.

## MusicBrainz — CC0 core data

ISRC lookup uses the MusicBrainz Web Service. Core database data is released
under [CC0](https://musicbrainz.org/doc/About/Data_License) and requires no
attribution; supplementary data is CC BY-NC-SA and is not used here. The client
sends a descriptive User-Agent and paces itself to roughly one request a second,
as the service asks. No MusicBrainz data is stored in this repository.

## Spotify — nothing is stored in this repository

The Spotify Developer Terms permit only *temporary* local caching of metadata
and forbid storing, aggregating, or building databases or compilations of
Spotify Content beyond what running the application strictly requires, and
forbid storing it indefinitely.

Accordingly, no Spotify Content is committed here. Resolutions — the mapping
from a chart entry to a track URI — are a machine-local cache under `.jukebox/`,
which is gitignored, and may be deleted at any time; `jukebox resolve backfill`
rebuilds them. Access and refresh tokens live in the same place.

The same terms forbid using Spotify Content to train a machine learning or AI
model, or otherwise ingesting it into one. jukebox is driven by an AI
assistant, so the boundary matters: the assistant reasons over the **chart
corpus**, which is Wikipedia's and Billboard's, and Spotify identifiers are
produced and written by ordinary code rather than passed to a model.

**Attribution when displaying:** the developer policy requires metadata shown to
a user to link back to the corresponding Spotify content, and forbids offering
metadata as a standalone service or product. A surface that displays track
metadata must satisfy that; the current command line reports counts and the
names taken from the charts.
