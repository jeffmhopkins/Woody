# COLD review — content conservation across the 2026-09-21 restructure

**Scope:** did anything get *lost* between `f94e91d` and `HEAD`. Not
correctness, not design.

**Cold:** nothing under `docs/review/**` was read. Sources are `git show
f94e91d:<path>`, the working tree, `git log`, and `git diff`.

**Provenance marks:** `[repo] path:line` — read in the tree. `[cmd]` — the
command whose output the claim rests on. `[calc]` — arithmetic shown.

---

## 0. What the gate structurally cannot catch

`tools/check-conservation.py` `[repo] tools/check-conservation.py:1-61` builds
a set of 8-word shingles from the **destinations named on its command line**
and asks, for each 8-word shingle of the source, "is it in that set?". From the
code, four blind spots follow directly:

1. **Unlisted destinations.** `dests = sys.argv[3:]` — a block moved somewhere
   not on the command line reads as a REAL GAP; a block moved somewhere that
   *was* listed reads as present no matter how wrong the home is.
2. **Duplication.** `have` is a `set()`. Two copies and one copy are the same
   membership test. The check never counts.
3. **Adjacency.** Beyond 8 words, order is not represented. A paragraph moved
   to where it no longer follows from what precedes it passes.
4. **Sub-threshold.** `N = 8`. A dropped table row, list item or heading, or a
   changed number inside an otherwise identical sentence, is invisible unless it
   happens to break 8 consecutive words.

Everything below is an attack on one of those four.

---

## 1. Anything lost

**Nothing of substance. I could not find a single lost passage, table row,
list item, heading or numeric value.** The searches that establish that are in
§4. The near-misses, and why each is not a loss, are here so the next reader
does not have to re-derive them.

### 1.1 Against the *whole* current `hardware/` tree, not the listed destinations

I rebuilt the gate's shingle index over **every** file under `hardware/`
(93 files, 62,567 distinct shingles) and ran all 8 original pages against it
`[cmd] python3 — shingle index of hardware/**/*.{md,yaml,csv} vs git show
f94e91d:hardware/<page>`. That closes blind spot 1: text moved to a directory
nobody listed would still be found.

**16 REAL GAPS total**, across 6 of the 8 pages. Every one is a deliberate
edit, not a loss. Traced individually:

| Gap | Old page | Why it is not a loss |
|---|---|---|
| 13 w | `controller/carrier.md` @1889 | `datasheets/texas-instruments/OPA2197.pdf` → `datasheets/analog/`. Surrounding prose intact `[repo] hardware/carrier/breath-excitation-reference/notes.md:24` |
| 9 w | `controller/carrier.md` @4538 | `cluster-boards.md §4` reference rewritten |
| 8 w | `controller/carrier.md` @5097 | `other-semi/MCP3202-CI-SN.pdf` → `analog/`. Text at `[repo] hardware/interfaces/spi-link/spi-link.md:90` |
| 8 w | `controller/carrier.md` @5743 | `other-semi/WS2815.pdf` → `led/` |
| 8 w | `controller/carrier.md` @8366 | `hardware/controller/cluster-boards.md` → `hardware/cluster/` |
| 8 w | `controller/cluster-boards.md` @1245 | `other-semi/74HC165.pdf` → `logic/74HC165-ti-scls116e.pdf` |
| 8 w | `controller/cluster-boards.md` @2502 | seam at the `## §4 The 32 bits` heading; §4 is whole at `[repo] hardware/cluster/key-marker-and-bits/key-marker-and-bits.md:22-35` |
| 9 w | `controller/cluster-boards.md` @3768 | `carrier.md §1` reference dropped (§1 left the file); see finding 2.4 |
| 12 w | `module/breath-receive-stage.md` @285 | the ASCII drawing's `+0.437 V` → the tracked figure `breath-zero-ref`. Drawing otherwise intact `[repo] hardware/module/breath-receive-stage/breath-receive-stage.md:48-115` |
| 8 w | `module/breath-receive-stage.md` @539 | `+0.579 V` → `0.573 V`, the corrected in-amp gain `[repo] config/figures.yaml:94` |
| 8 w | `module/breath-receive-stage.md` @2815 | path rewrite |
| 8 w | `module/breath-receive-stage.md` @2925 | path rewrite |
| 10 w | `module/mod-channels.md` @5 | status line rewritten for the new location |
| 13 w | `module/mod-channels.md` @1651 | *"At 2.5 V into 2.5 kΩ that is 1 mA"* → *"At `mod-reference` into 2.5 kΩ that is 1.33 mA"*, with the old text quoted in place `[repo] hardware/module/mod-channels/mod-channels.md:197-200`. A correction, and a **good** one — the old figure was a survival from the four-resistor circuit |
| 8 w | `module/pitch-stage.md` @7 | status line rewritten |
| 8 w | `module/pitch-stage.md` @2753 | `other-semi/LT5400.pdf` → `analog/` |

`module/breath-output-stage.md`, `module/digital-and-supervision.md` and
`module/power-entry.md` had **0 REAL GAPS** against the whole tree.

### 1.2 Sub-8-word structure (blind spot 4)

Every line of the 8 original pages that is a heading, a table row, or a list
item — normalised for whitespace and for a `> ` blockquote prefix, because
moving a block *into* a blockquote is legitimate — matched against every
`.md` under `hardware/`, `docs/decisions/`, `docs/reference/`, plus
`README.md` and `ROADMAP.md` `[cmd] python3 — structural-line diff`.

**4 unmatched lines out of the corpus, all explained:**

- `cluster-boards.md:162` — a table row whose only change is the 74HC165
  datasheet path.
- `breath-receive-stage.md:334` — a list item whose only change is a page path.
- `breath-receive-stage.md:339` — heading demoted `###` → `##` on the move
  `[repo] hardware/module/breath-receive-stage/notes.md:83`.
- `power-entry.md:475` — heading demoted `###` → `##` on the move
  `[repo] hardware/module/panel-led/panel-led.md:28`.

No table row, list item or heading was dropped.

### 1.3 Numbers (blind spot 4, the worse half)

Every numeric token in the 8 original pages, checked for presence anywhere
under `hardware/` now `[cmd] python3 — re.findall(r'\d[\d.,]*') old vs new`.

**One token absent: `165.`** — from the filename `74HC165.pdf`, now
`74HC165-ti-scls116e.pdf`. **Every other number in all eight pages survives**,
including inside the ASCII drawings.

### 1.4 `hardware/bom.csv` — 138 rows in, 138 rows out

`[cmd] python3 csv diff, f94e91d:hardware/bom.csv vs hardware/bom.csv`

- 138 rows before, 138 after; header identical; **no refdes added, none lost**.
- 119 rows byte-identical. 19 changed: `D-CLAMP-BREATH`, `D-REVPOL`,
  `F-CHAIN`, `LK-SER`, `R-LED-SER`, `R-MODGAIN`, `R-PRECISION`, `R-SER-TERM`,
  `TRIM-BREATH-ZERO`, `U-ADC`, `U-BREATH`, `U-BUF`, `U-DAC`, `U-DIFFRX`,
  `U-LVL-MOD`, `U-OPA-PITCH`, `U-REF-BREATH`, `U-REG-DAC`, `U-RESP`. I read all
  19 diffs: every one is a path rewrite or a figure replaced by a citation, and
  **every change is additive** — no note text was truncated.
- `F-CHAIN`'s change is a genuine repair: the row cited
  `MF-PSMF010X.pdf` where the banked file is `MF-PSMF010X-polyfuse.pdf`.

### 1.5 `datasheets/` — blob-level, not path-level

`[cmd] git ls-tree -r f94e91d datasheets/ vs HEAD, compared by blob SHA`

87 files before, 87 after. **The only blob that differs is `MANIFEST.csv`**;
`.moves.csv` is new. Every PDF is byte-identical and still present under its
new function-axis path. The one deletion,
`datasheets/mechanical/WS2815-worldsemi-datasheet.pdf`, was byte-identical to
`other-semi/WS2815.pdf` (both now `led/WS2815.pdf`), and **both manifest rows
were kept** `[repo] datasheets/MANIFEST.csv:55-56` — the de-duplication removed
a file, not a record. `MANIFEST.csv`: 98 rows before, 98 after, no
`(part, sha256)` pair lost `[cmd] python3 csv set-diff`.

### 1.6 Corpus files that were never a "source" (blind spot 1, other direction)

`git diff --stat f94e91d HEAD -- . ':!docs/review' ':!hardware' ':!tools'`
lists 39 files. I read every deleted line in `docs/decisions/**` and
`config/key-layout.yaml` `[cmd] git diff … | grep '^-'`. All of them are either
path rewrites or in-place corrections that leave a dated record of what they
replaced — e.g. ADR 0003's `0.04` → `0.053` offset coefficient, each with
*"this line carried … until 2026-09-21"*.

The largest deletion, ADR 0006's refutation blockquote (the `110.5 dB`,
`0.22 µV`, `0.00027 cents` chain), is **not lost**: it is in
`config/figures.yaml`'s `diode-split-rationale` entry, in full, with the
arithmetic, and ADR 0006 now cites it by name `[repo] config/figures.yaml:422-450`.
That is rule 1 in `CLAUDE.md` applied correctly.

`docs/decisions/README.md` lost three index rows to *replacement*, not deletion
— 0007, 0008 and 0011 were corrected against the ADRs they point at
`[repo] docs/decisions/README.md:39-64`.

---

## 2. Anything duplicated

This is where the restructure actually cost something. Total old-page text now
live in two or more current files: **497 words in 49 runs, 1.57 % of the
original 31,755** `[cmd] python3 — shingle→{files} index over hardware/**/*.md`.
Small in mass; two of the runs matter.

### 2.1 The ADC-reference-loading derivation is now in two files in full, and a third in summary — **and none of its numbers are tracked**

The block that derives *"key pull-ups move the MCP3202's reference"* exists
twice, in full, with the same five numbers:

- `[repo] hardware/carrier/carrier.md:167-184`
- `[repo] hardware/interfaces/key-chain-loom/key-chain-loom.md:110-131`

and a third time in summary at
`[repo] hardware/cluster/key-switch-network/key-switch-network.md:105, 126-127, 140`,
plus once more inside the `F-CHAIN` BOM note `[repo] hardware/bom.csv:50`
and once in `[repo] docs/decisions/0001-mcu-and-board-partitioning.md:230,239`.

Shared figures: **1.43 mA**, **25.8 mA**, **0.077 %**, **3.2 LSB**,
**~1594 counts**. `[cmd] grep -rn "25\.8\|3\.2 LSB\|1594"` over the corpus
confirms six live statements of 25.8 mA and six of 3.2 LSB.

Three things make this the project's named failure mode rather than harmless
repetition:

1. **`carrier.md` explicitly claims sole ownership** — *"This argument stayed,
   because it is owned by neither circuit"* `[repo] hardware/carrier/carrier.md:162-165`
   — while `key-chain-loom.md` carries an equally complete copy that makes no
   such concession.
2. **None of the five figures is in `config/figures.yaml`** `[cmd] grep -n
   "1.43\|25.8\|1594" config/figures.yaml` → no match. So
   `check-staleness.py` cannot see a divergence between the two copies.
3. **The split made it worse, not better.** At `f94e91d` both copies were in
   *one* file, 90 lines apart `[repo] git show f94e91d:hardware/controller/carrier.md:412,509`
   — visible to one reader scrolling one page. They are now in two directories
   on two different boards.

**Claim, moderately confident.** What would settle whether this is a defect or
a deliberate both-ends-of-the-loom decision: whether the split intended the
loom page to own the load and the carrier page to own the reference. If so,
one of the two should state the number and the other should cite it; today
both state it.

### 2.2 The LT5400 exposed-pad stray is stated twice on the same circuit

`5.5 pF` against `1.4 pF`, and the sentence *"the dominant stray on the 1 V/oct
network, and nothing in this corpus says …"*:

- `[repo] hardware/module/pitch-stage/pitch-stage.md:306-313`
- `[repo] hardware/module/pitch-stage/notes.md:92-96`

Mitigated: the `Still open` entry links to `notes.md` explicitly. But it
restates both capacitances rather than citing, and neither is tracked.
**Low severity.**

### 2.3 New-file boilerplate: five `sim/README.md`, three interface `notes.md`

`[cmd] python3 — % of each file's shingles that appear in a sibling`

| Family | Mutual overlap |
|---|---|
| 5 × `sim/README.md` (2,824 w) | **33.6 %** of shingles appear in a sibling; `pitch-stage/sim/README.md` is **61.3 %** shared |
| 15 × `notes.md` (5,925 w) | 17.0 % overall; the three `interfaces/*/notes.md` are **75–78 %** shared with each other |

The five `sim/README.md` files also each restate the same 20-word operational
trap from `docs/reference/pcb-pipeline.md` — *"it treats every non-`Warning:`
stderr line as fatal and ngspice prints a solver banner to stderr on every
run"* `[cmd] python3 — hardware shingles ∩ docs/reference, minus old-page
shingles`. Five copies of one gotcha that has an owner document.

I read `pitch-stage/sim/README.md` against `power-entry/sim/README.md`
`[cmd] diff`: the shared part is genuinely a template (the *deck's contract*
table skeleton, the *"a simulated X is a screen, not a spec"* closing), and the
per-circuit content differs completely. **Low severity — but the ngspice trap
is a fact with an owner and should be cited, not copied five times.**

### 2.4 Stale attribution created by the consolidation — `sim/README.md` credits a file that no longer holds the claim

`[repo] hardware/module/breath-receive-stage/sim/README.md:19` reads
*"`hardware/carrier/carrier.md` puts the link at **60.2 dB**"*, and line 29
*"`carrier.md` replies that with `R1b` fitted the floor is **73 dB**"*.

`[cmd] grep -rn "60\.2 dB\|58\.5 dB\|73 dB" hardware` — **`carrier.md`
contains none of them.** All three now live in
`[repo] hardware/interfaces/breath-sense-link/breath-sense-link.md:77-83,192`.

This is exactly blind spot 1 in reverse: `sim/README.md` was *written during*
the restructure and was never a conservation source, so no run of the gate ever
looked at it. `check-staleness.py` cannot see it either — the path exists and
the file exists; only the content moved.

Worse, and worth a second look by someone doing semantics rather than
conservation: the sim README frames this as *"the corpus does not agree with
itself"* between two pages — but **both sides of that disagreement are now in
the same file**, `breath-sense-link.md:81-84` against `:195-197`, still
disagreeing by an order of magnitude about what `R1b` buys. The consolidation
moved a cross-file contradiction inside one file without resolving it.

### 2.5 `hardware/bom.csv` is a full duplicate of its 24 fragments — by design

20,489 words in the master, 20,512 in the fragments (the difference is exactly
23 extra header lines, one per extra fragment) `[calc] 24 fragments − 1 master
header = 23`. This is the generated-file pattern, and it is guarded:
`merge-bom.py --check` is wired into `check-staleness.py`
`[repo] tools/check-staleness.py:178`. **Not a defect.** Noted so the word
accounting in §3 is not read as 20 k words of unmanaged duplication.

---

## 3. Word-count accounting

All counts use `check-conservation.py`'s own `words()` tokenizer, so they are
comparable to what the gate saw `[cmd] python3 — cons.words() over each set`.

### The totals

```
AT f94e91d
  8 schematic pages                      31,755
  hardware/bom.csv                       20,256
                                       ─────────
                                         52,011

AT HEAD, everything under hardware/
  circuit + board .md        (25 files)  36,575
  notes.md                   (15 files)   5,925
  sim/README.md               (5 files)   2,824
  circuit.yaml               (23 files)   3,535
  hardware/bom.csv  (generated)          20,489
  24 BOM fragments + unplaced.csv        20,512
                                       ─────────
                                         89,860

GROWTH                       [calc] 89,860 − 52,011 = +37,849
```

### Where the growth is

```
+20,512  BOM fragments             mechanical duplicate of the master (§2.5)
+   233  BOM master                [calc] 20,489 − 20,256; the 19 changed rows
+ 3,535  circuit.yaml              entirely new — 0 % carried from any old page
+ 2,824  sim/README.md             entirely new — 0.0-1.1 % carried
+ 5,925  notes.md                  8-78 % carried; history lifted out of the pages
+ 4,820  circuit + board .md       [calc] 36,575 − 31,755
                                 ─────────
                                  +37,849
```

### How much of the prose is old and how much is new

Over all 45,009 8-word shingles in `hardware/**/*.md` today, **30,847 come from
the 8 original pages** `[cmd] python3 — current md shingles ∩ old-page
shingles` → **68.5 %**, i.e. roughly **30,854 of 45,324 md words are carried
text and ~14,470 are newly written.**

From the other direction: **30,717 of the old corpus's 31,615 distinct
shingles survive** somewhere under `hardware/` → **97.2 % of the original
word-mass is still present verbatim** `[cmd] python3 — |old_shingles ∩
current_shingles|`. The missing 2.8 % is the 16 gaps of §1.1 plus 111 seams
(33 + 16 + 6 + 12 + 13 + 11 + 7 + 13 `[calc]`), all of which I traced to
deliberate edits.

**Duplication is 497 words, 1.57 % of the original** (§2). So of the
+14,470 new md words:

```
  2,824   sim/README.md                      (of which ~937 shingles are sibling boilerplate)
  ~5,000  notes.md framing + moved-verbatim stubs + `## Interfaces` tables
  ~6,150  genuinely new prose: the 2026-09-21 corrections, the interface
          tables' Figure/Peer columns, the pointer paragraphs
    497   old text now living in two places
```

The last line is the only part of the growth that is a defect, and it is
1.1 % of what was added.

---

## 4. What I checked and found clean

So the next reader knows the shape of the search, not just its hits.

1. **Whole-tree conservation.** All 8 source pages against an index of every
   file under `hardware/` (not the gate's named destinations). 16 gaps, all
   traced to deliberate edits (§1.1).
2. **Structural lines.** Every heading, table row and list item in the 8 pages,
   blockquote-normalised, against all `.md` in `hardware/`,
   `docs/decisions/`, `docs/reference/`, `README.md`, `ROADMAP.md`. 4
   unmatched, all explained (§1.2).
3. **Every numeric token** in the 8 pages against all of `hardware/`. One
   absent, and it is a filename fragment (§1.3).
4. **BOM**: 138 → 138 rows by refdes, and all 19 changed rows read by hand
   (§1.4).
5. **Datasheets**: blob-SHA comparison of all 87 files; `MANIFEST.csv` 98 → 98
   rows by `(part, sha256)` (§1.5).
6. **Deletions outside `hardware/`**: every `-` line in `docs/decisions/**` and
   `config/key-layout.yaml` (§1.6).
7. **Dangling repo paths.** Every `hardware/… docs/… config/… datasheets/…
   firmware/… tools/…` path token in the live corpus, checked against the
   filesystem `[cmd] python3 — regex path extraction + os.path.exists`.
   **Zero dangling paths in the corpus.** The only misses are inside
   `path-map-2026-09-21.csv` itself (which by definition names old paths) and
   three entries in `merge-bom.py`'s `ORDER` list for fragments that do not
   exist — `hardware/module/{digital-and-supervision,link-supervision,panel}/bom.csv`
   — which the tool skips by design `[repo] tools/merge-bom.py:92-93` and which
   cost no rows, since the BOM is conserved at 138.
8. **Section references into files that lost the section.**
   `[cmd] grep -rn "carrier\.md §1\|§5\|§6"` and the equivalent for
   `cluster-boards.md §1/§2/§4` and the six module pages: **no hits.** The
   cross-file `§`-references were cleaned up.
9. **Duplication of live ADR text into new hardware files.** Only the five
   `sim/README.md` ngspice lines (§2.3).
10. **`hardware/unplaced.csv`** holds **50 of the 138 BOM rows (36 %)** and is
    named in **no Markdown file anywhere in the repo**
    `[cmd] grep -rn "unplaced" --include=*.md .` → no match outside
    `tools/merge-bom.py:69,81`. Not a *loss* — every row is conserved — but a
    reader has no way to learn what "unplaced" means or what would resolve it,
    which is what `CLAUDE.md`'s *"mark unresolved things with what decides
    them"* asks for. Related: `docs/reference/repo-maintenance.md` §4
    `[repo] docs/reference/repo-maintenance.md:126-144` still describes
    `hardware/bom.csv` as the file you edit — *"validate column count and
    duplicate refdes after any edit"* — and the tool list at
    `[repo] docs/reference/repo-maintenance.md:180-185` does not mention
    `merge-bom.py` at all. `MANIFEST.csv`'s identical trap has a written
    warning; `bom.csv`'s does not. **This is the restructure's own derived
    document failing to follow its own change.**

### Adjacency (blind spot 3) — what I found

The `§`-stubs are handled well *between* files, and less well *within* them.

- `[repo] hardware/carrier/carrier.md:182` — *"See §3 and *Still open*"* — and
  `:367`, `:372`, which also cite §3. `carrier.md`'s §3 is now a nine-line
  pointer with no content `[repo] hardware/carrier/carrier.md:198-207`. A
  reader following the reference lands on a forwarding address, not the
  argument.
- `[repo] hardware/carrier/carrier.md:393` — *"closed 2026-09-21, §4"* — the
  supporting text is in `[repo] hardware/interfaces/spi-link/spi-link.md:90`.
- `[repo] hardware/cluster/cluster-boards.md:99` and `:218` cite *"§4's
  table"*; `cluster-boards.md` no longer has a §4 heading at all. A paragraph
  at `:23-31` does name the destination, so this is recoverable, just not from
  the reference itself.

**Claim, confident on the facts, uncertain on severity.** Nothing is lost;
navigation degraded. What would settle it: whether the convention is that a
retained `§` number is a forwarding address (in which case these are fine and
the stub should say so at each citation) or an anchor (in which case the three
carrier citations should point at `interfaces/key-chain-loom/`).

The block diagram at `[repo] hardware/carrier/carrier.md:39-78` still labels
`§1`, `§5` and `§6`, which no longer exist in that file — but the three
pointer paragraphs immediately below it name every destination, so I read that
as deliberate and correct.

---

## 5. What I could not check

1. **Paraphrase.** Every method here is exact-match at some granularity. Text
   that was *rewritten* on the way into its new home — same claim, different
   words — reads as "lost" from the old page and "new" in the new file, and I
   would have classified it under the 16 gaps only if it broke 8 words. A
   paraphrase that dropped a qualifier would be invisible to all of it. Only a
   section-by-section human read of all eight pages against their ~23
   destinations settles that; I read six of the sixteen gap regions that way.
2. **Whether each block landed in the *right* circuit.** Conservation says the
   text exists somewhere. It cannot say that the charge-sharing derivation
   belongs in `breath-adc/` rather than `key-switch-network/`. That is the
   `D4` assignment rule and a semantic question.
3. **`circuit.yaml`'s 294 edges.** 3,535 words of entirely new content with no
   predecessor to conserve against. I verified it duplicates no old-page prose
   (one 11-word run, `breath-response-shaper.md` ↔ its own `circuit.yaml`) but
   not that any edge is true.
4. **Whether the 19 changed BOM rows are *correct*.** I verified they are
   additive and lose no prior text. Whether `0.573 V` is the right in-amp
   output, or `120 mV` the right `V_f` modulation, is a datasheet question.
5. **`mechanical/`, `firmware/`, `docs/log/`, `docs/research/`.** Untouched by
   the restructure per `git diff --stat`, so not examined.
6. **Anything in `docs/review/**`** — excluded by the cold rule, including
   whatever the gate was actually invoked with on each split. I inferred the
   gate's limits from its source, not from its logs.

---

## Summary

| | |
|---|---|
| Content lost | **none found** — 16 gaps, 4 structural lines, 1 numeric token, all traced to deliberate edits |
| Content duplicated | **497 words, 1.57 %** of the original — one that matters (§2.1), one minor (§2.2), plus new-file boilerplate (§2.3) |
| Broken by the restructure, invisible to both checkers | `sim/README.md` crediting `carrier.md` for claims now in `breath-sense-link.md` (§2.4); `repo-maintenance.md` §4 not following `bom.csv` becoming generated (§4.10) |
| Navigation degraded | three in-file `§3` citations in `carrier.md` now land on a stub (§4) |
| BOM | 138 rows in, 138 out |
| Datasheets | 87 files, every blob conserved; 98 manifest rows in, 98 out |
