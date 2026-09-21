# Chart corpus implementation plan

> **Superseded in places.** This records the design as it was decided, not as it
> now stands. The chart corpus and the resolution cache were later moved out of
> the repository entirely, playlist specs were moved to the user's data
> directory, and exclusions key on a chart's own title and artist rather than a
> track identifier. `NOTICE.md` and the README describe what is true today.

**Goal:** `jukebox charts fetch --year 1985` writes a vendored, byte-stable chart
corpus and an honest coverage report.

**Architecture:** `ChartSource` fetches rendered HTML from the MediaWiki
`action=parse` API; a rowspan-aware `Grid` reduces any wikitable to dense text;
one mapper per page shape turns a grid into `ChartEntry` rows; `Corpus` writes
`data/charts/<chart>/<year>.json`. A `Registry` of `(chart, year) -> PageRef | Gap`
is the only thing that knows about era name drift.

**Tech Stack:** Python 3.12, httpx, lxml, pydantic, typer, pytest.

Spec: [2026-09-06-charts-corpus-spec.md](2026-09-06-charts-corpus-spec.md).
Fixtures are already committed under `tests/fixtures/pages/` (five real pages).

---

### Task 1: Cell cleaning

**Files:** Create `src/jukebox/charts/cell.py`, `tests/charts/test_cell.py`

- [ ] **Step 1: Failing tests**
```python
def test_br_becomes_a_space():
    assert clean_cell(html("Weeks at<br />number one")) == "Weeks at number one"

def test_reference_superscript_is_removed():
    assert clean_cell(html('George Strait<sup class="reference">[13]</sup>')) == "George Strait"

def test_title_quotes_and_dagger_are_stripped():
    assert clean_title('"Cuts You Up" †') == "Cuts You Up"

def test_two_artist_cell_is_preserved_whole():
    assert clean_cell(html("Philip Bailey and Phil Collins")) == "Philip Bailey and Phil Collins"
```
- [ ] **Step 2:** `pytest tests/charts/test_cell.py -v` → FAIL, no module
- [ ] **Step 3:** Implement: drop `sup.reference`, replace `br` with a space
      before `text_content()`, collapse whitespace; `clean_title` additionally
      strips wrapping `"` and trailing `†`/`*`.
- [ ] **Step 4:** Tests pass. **Step 5:** Commit.

### Task 2: Grid — rowspan and colspan expansion

**Files:** Create `src/jukebox/charts/grid.py`, `tests/charts/test_grid.py`

- [ ] **Step 1: Failing tests**, driven from the committed fixtures:
```python
def test_ranked_grid_is_dense(hot100_1985):
    g = Grid.of(hot100_1985)
    assert len(g.rows) == 101 and g.widths() == {3}
    assert g.rows[1] == ["1", '"Careless Whisper"', "George Michael"]

def test_rowspan_carries_a_title_across_the_weeks_it_held(dance_1985):
    g = Grid.of(dance_1985)
    assert g.rows[3][1] == g.rows[4][1] == '"We Are the Young"'

def test_colspan_duplicates_a_two_level_header(dance_1985):
    assert Grid.of(dance_1985).rows[0][1:3] == ["Hot Dance/Disco Club Play"] * 2
```
- [ ] **Step 2:** FAIL. **Step 3:** Implement the pending-rowspan algorithm
      prototyped against all four fixtures. **Step 4:** Pass. **Step 5:** Commit.

### Task 3: Chart, PageShape, PageRef, Gap

**Files:** Create `src/jukebox/charts/{chart,page_shape,page_ref,gap}.py`,
`tests/charts/test_chart.py`

- [ ] `Chart`: `HOT_100`, `COUNTRY`, `RNB`, `RAP`, `DANCE_CLUB`,
      `DANCE_SALES`, `MAINSTREAM_ROCK`, `MODERN_ROCK`, `LATIN`; each with a
      stable slug used as the corpus directory name.
- [ ] `PageShape`: `RANKED`, `NUMBER_ONES`, `DECADE`.
- [ ] `Gap`: `chart`, `year`, `reason` — reason from a closed set
      (`CHART_DID_NOT_EXIST`, `NO_ARTICLE`).
- [ ] Test that slugs are unique and filesystem-safe. Commit.

### Task 4: Registry

**Files:** Create `src/jukebox/charts/registry.py`, `tests/charts/test_registry.py`

- [ ] **Step 1: Failing tests** — this is where era drift lives:
```python
def test_rnb_resolves_through_its_era_name():
    assert R.resolve(Chart.RNB, 1985).title == "Billboard Year-End Hot Black Singles of 1985"
    assert R.resolve(Chart.RNB, 1995).title == "Billboard Year-End Hot R&B Singles of 1995"

def test_modern_rock_before_the_chart_existed_is_a_gap():
    assert R.resolve(Chart.MODERN_ROCK, 1985).reason is Reason.CHART_DID_NOT_EXIST

def test_every_gap_states_a_reason():
    assert all(g.reason for g in R.gaps(1985))
```
- [ ] **Step 3:** Implement as a declared table of
      `(chart, year_from, year_to, title_template, shape)` rows, resolved by
      year range. No `if year >` branching outside the table.
- [ ] Commit.

### Task 5: ChartSource port and its two implementations

**Files:** Create `src/jukebox/charts/{chart_source,mediawiki_source,fixture_source}.py`,
`tests/charts/test_mediawiki_source.py`

- [ ] `ChartSource` Protocol: `fetch(title: str) -> str`.
- [ ] `FixtureSource` maps a page title to a fixture filename; raises a clear
      error naming the missing fixture.
- [ ] `MediaWikiSource` calls `action=parse&prop=text&formatversion=2`, sets a
      descriptive User-Agent, and raises `PageNotFound` on the API's `error` key.
- [ ] Test `MediaWikiSource` with `respx` — URL, User-Agent, and the error path.
      No live call. Commit.

### Task 6: ChartEntry and the three mappers

**Files:** Create `src/jukebox/charts/entry.py`, `src/jukebox/charts/mappers/*.py`,
`tests/charts/test_mappers.py`

- [ ] `ChartEntry`: `kind` (`ranked` | `number_one`), `title`, `artist`, and
      then `rank` **or** `reached`/`weeks`. Validation rejects a `ranked` entry
      with no rank and a `number_one` with no date.
- [ ] `RankedMapper` — columns by header name (`No.`, `Title`, `Artist(s)`).
```python
def test_ranked_maps_first_and_last(hot100_1985):
    e = RankedMapper().map(Grid.of(hot100_1985), year=1985)
    assert len(e) == 100
    assert (e[0].rank, e[0].title, e[0].artist) == (1, "Careless Whisper", "George Michael")
    assert (e[-1].rank, e[-1].title, e[-1].artist) == (100, "Sugar Walls", "Sheena Easton")
```
- [ ] `NumberOnesMapper` — resolves a one- or two-level header, emits one entry
      per (week, chart column pair), skips `Not issued`, and collapses a title
      repeated by rowspan into a single entry carrying `weeks`.
```python
def test_country_1985_has_one_entry_per_distinct_run(country_1985):
    e = NumberOnesMapper().map(Grid.of(country_1985), year=1985)
    assert e[0].title == "Does Fort Worth Ever Cross Your Mind"
    assert e[0].artist == "George Strait" and e[0].reached.day == 5

def test_dance_page_yields_two_charts(dance_1985):
    by_chart = NumberOnesMapper().split(Grid.of(dance_1985))
    assert set(by_chart) == {"Hot Dance/Disco Club Play", "Hot Dance/Disco 12-inch Singles Sales"}
    assert "Not issued" not in [e.title for e in by_chart["Hot Dance/Disco 12-inch Singles Sales"]]
```
- [ ] `DecadeMapper` — parses the full date and filters to the requested year.
```python
def test_the_1989_straddler_is_not_a_1990_entry(modernrock_1990s):
    e = DecadeMapper().map(Grid.of(modernrock_1990s), year=1990)
    assert "Blues from a Gun" not in [x.title for x in e]
    assert e[0].title == "House" and e[0].weeks == 3
```
- [ ] Commit after each mapper.

### Task 7: Corpus writer

**Files:** Create `src/jukebox/charts/corpus.py`, `tests/charts/test_corpus.py`

- [ ] Writes `data/charts/<chart-slug>/<year>.json` with `chart`, `year`,
      `kind`, `source`, `retrieved`, `entries`; entries sorted by rank, else by
      date then title.
- [ ] **Byte-stability test:** write twice from the same grid, assert identical
      bytes; and assert `json.dumps` uses `indent=2`, `ensure_ascii=False`,
      trailing newline — so a re-fetch diffs as content, not as formatting.
- [ ] Commit.

### Task 8: Coverage report

**Files:** Create `src/jukebox/charts/report.py`, `tests/charts/test_report.py`

- [ ] Lists per chart: resolved title, entry count, or the gap and its reason.
- [ ] Test that a year with a gap still reports success, and that the reason
      text appears. Commit.

### Task 9: CLI wiring

**Files:** Create `src/jukebox/cli/__init__.py`, `src/jukebox/cli/charts.py`,
`tests/cli/test_charts_command.py`

- [ ] `jukebox charts fetch --year 1985 [--source fixture]` composes
      registry + source + grid + mapper + corpus + report; exit code 0 when
      gaps exist, non-zero only on a fetch or parse failure.
- [ ] Test through typer's `CliRunner` against `FixtureSource`, asserting the
      corpus files land and the report names the Modern Rock gap.
- [ ] Commit.

### Task 10: Network guard tests

**Files:** Create `tests/charts/test_live_pages.py`

- [ ] Marked `network`, deselected by default. For every registry title for
      1985, assert HTTP 200 and at least one `table.wikitable`. This is how a
      Wikipedia rename is caught; it is run deliberately, not in the default suite.
- [ ] Commit.

---

## Verification

```bash
devenv shell -- pytest                      # 100% on src/jukebox/charts
devenv shell -- pytest -m network           # deliberate, hits Wikipedia
devenv shell -- jukebox charts fetch --year 1985
devenv shell -- prek run --all-files
```
