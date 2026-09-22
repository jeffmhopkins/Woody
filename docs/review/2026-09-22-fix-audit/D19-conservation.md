# D19 — Conservation: did the fix batch drop anything?

**Slice:** the 1,228 deleted lines of `0e68f25~1..HEAD`, restricted to the
design corpus (`hardware/**`, `docs/decisions/**`, `docs/reference/**`,
`config/**`, `firmware/**`, `README.md`, `ROADMAP.md`).
**Method:** every deleted hunk classified as *replaced by a citation*,
*superseded deliberately*, *moved elsewhere*, or **gone**; plus four mechanical
conservation proofs (numeric bag, BOM row census, figure-citation census,
`depends_on` edge census) and `tools/check-conservation.py` on every rewritten
page.
**Report, not fix.** Nothing in the tree was changed.

`[test]` provenance below means a script I ran in this session; the script is
described inline so it can be re-run.

---

## The short answer

**Almost nothing was lost, and the batch is unusually clean on conservation.**
`[test]` Zero distinct numeric tokens left the corpus (998 distinct before →
1,041 after; the set difference in the *gone* direction is **empty**). All 18
rows that left `unplaced.csv` landed in a circuit fragment with their `notes`
intact or extended. No file was deleted or renamed. No `depends_on` edge
vanished unreplaced. No figure entry, figure field, or figure citation was
dropped.

**Three things did go.** One is a real loss of design rationale, replicated 23
times and now surviving only in a history directory. Two are navigational.

**And one thing that was *not* lost is worse than if it had been**: the
`unplaced.csv` paragraph was rewritten in `hardware/README.md` and left live
and stale in `docs/reference/repo-maintenance.md`, which is the project's named
failure mode occurring inside the document that names it — §B1.

---

## A. Genuinely gone

### A1. The `circuit.yaml` schema rationale — deleted from all 23 circuits, relocated nowhere

`[repo]` `git show 0e68f25~1:hardware/module/pitch-stage/circuit.yaml`, and
`[test]` the comment block is byte-identical across all 23 `circuit.yaml` files
before the batch (`md5` of `grep '^#'` = `7b69174a…` on all 23) and
byte-identical after (`772b4d7f…` on all 23), so this is **one deletion event
replicated 23 times**, not 23 separate edits.

Three passages were in the old header and are in neither the new header nor
anywhere else in the corpus:

> There is deliberately no `revision`: git holds it exactly and cannot forget.
> And no `figures_owned`: that would put ownership in two files, which is rule 1
> broken in the project's own metadata. `config/figures.yaml owner:` is the one
> declaration.

> `depends_on` is the field that can lie. It fails SILENT — an undeclared edge
> is an unchecked edge — so it is seeded rather than started empty […]

`[test]` `grep -rn "figures_owned" .` outside `.git` returns **three hits, all
in `docs/review/2026-09-21-restructure-design/D3-staleness-paradigm.md`** — a
historical record, explicitly *not* the corpus (`CLAUDE.md` §6). `[test]`
`grep -rni "revision" hardware docs/reference docs/decisions config …` returns
no statement of why the schema has no `revision` key.

**Why this matters and why it is not merely tidying.** The `figures_owned`
sentence is the corpus's only statement that ownership lives in exactly one
place, *asserted about the project's own metadata schema*. It is the rule-1
argument applied reflexively. A future editor who adds `figures_owned:` to a
`circuit.yaml` — a natural thing to want — will now find no objection anywhere
in the corpus, and the objection that exists is in a directory reviewers are
forbidden to read.

The "fails SILENT" half is partly preserved: the new header keeps *what* is
guaranteed ("every edge RESOLVES") but drops *why the field is seeded rather
than started empty*, which is the design decision a reader would otherwise
second-guess.

**Judgement:** a real loss, low blast radius, cheap to fix. Two sentences in
`docs/reference/repo-maintenance.md` (which already owns "what each tool owns")
or in one `circuit.yaml` header would restore it — and per rule 1 it should be
in **one** place this time, not 23.

### A2. Twelve sibling-page hyperlinks, and one page with no route to its own schematic

`[test]` Extracting every `[text](target)` pair per file at both revisions and
differencing: **12 (file, target) link pairs were removed and are not replaced
by any link in the same file.** All 12 are `Peer`-column links in `carrier/**`
and `cluster/**` Interfaces tables, replaced by bare `board/circuit` ids:

| Removed target | From |
|---|---|
| `../power-entry-instrument/power-entry-instrument.md` | `breath-excitation-reference.md`, `display-and-service-uart.md` |
| `../breath-excitation-reference/…`, `../display-and-service-uart/…`, `../led-strip-drive/…` | `power-entry-instrument.md` |
| `../key-register/…`, `../key-switch-network/…`, `../key-marker-and-bits/…` | the three cluster circuit pages, mutually |
| `../carrier.md` | `display-and-service-uart.md` |

Eleven of these are **by design** — `hardware/README.md`'s new "The `##
Interfaces` table" section defines `Peer` as "a bare `board/circuit` id", and
the module pages always used bare ids. Consistency was the point.

The twelfth is not covered by that rule and is the one worth acting on.
`[repo] hardware/carrier/display-and-service-uart/display-and-service-uart.md`
now mentions `carrier.md` three times (lines 3, 31, 87) and **links to it zero
times** `[test] grep -n "carrier\.md"`. Its schematic is drawn in `carrier.md`
and is not redrawn on the page; its sibling `breath-adc.md:9` still carries
`**The schematic is drawn in [`carrier.md`](../carrier.md) §2**`. A reader who
opens the UART page has no clickable route to the drawing it describes.

**Judgement:** small, real, one line to fix. Not a blocker.

### A3. Nothing else

`[test]` Every other deleted passage I classified resolves to one of:

- **replaced by a citation** — `+5.21 V` → `dac-rail`, `4.7 V` → `sensor-full-scale`,
  `766 mV/kPa` → `breath-sensor-slope`, `~1 µs`/`~93 µs`/`~5.7 µs`/`~125 µs` →
  `key-press-time`/`key-release-time`, `Six conductors per hop` →
  `chain-conductors`, `8HP` → `panel-width`, the PANEL height budget →
  `panel-height-budget`, `plate_thickness: null` → `plate-thickness`;
- **superseded deliberately and narrated in place** — the ks33 standoff
  conclusion, the ADR 0006 pitch power-on row, the ADR 0004 `0.7 × AVDD`
  threshold, the ADR 0002 bounce sentence, the latency-budget key-path table,
  `module.md`'s unplaced-ICs bullet (struck through, not removed), `panel.md`'s
  "not a circuit" self-description;
- **moved** — 18 `unplaced.csv` rows, the `PANEL` BOM row (`panel-led/bom.csv`
  → new `panel/bom.csv`), the datasheet text-layer survey (`pcb-pipeline.md` →
  `repo-maintenance.md` §3, with a pointer left behind).

---

## B. Not lost — but the corrected copy did not land where the reader looks

This is not a deletion defect, which is why I nearly did not file it. I am
filing it because it is *produced by* the deletion I was auditing: the
paragraph was rewritten in one file and left untouched in its duplicate.

### B1. `repo-maintenance.md` still says `unplaced.csv` "holds the 50 rows of 138"

`[repo] docs/reference/repo-maintenance.md:204-208`:

> **`hardware/unplaced.csv` holds the 50 rows of 138 that no schematic page
> names.** […] Two of its clusters name circuits this corpus has no page for —
> six identical jack-protection networks drawn three times, and nineteen
> decoupling capacitors with no home.

`[repo] hardware/README.md:69-83` — the same paragraph, **rewritten in this
batch**: "It was 50 rows and is now 34."

`[test]` The tree: **32 rows, 67 units, of a 139-row master.**

So the concrete detail the batch deleted from `hardware/README.md` (the
jack-protection networks, the nineteen decouplers) is not lost — it survives
verbatim in `repo-maintenance.md`. It survives *inside a sentence that is now
wrong by 18 rows*, in the document whose §4 is the authority on `bom.csv`, four
lines above a note that reads *"This section described `bom.csv` as the file you
edit for several hours after it stopped being one. […] It is the project's named
failure mode, in the document that exists to record exactly this trap."*

The checker cannot catch it: "50 rows of 138" is not a tracked figure and
`hardware/unplaced.csv`'s row count is not in `config/figures.yaml`.

### B2. Every count written about `unplaced.csv` in this batch is already wrong

`[test]` Counted with `csv.DictReader` over the working tree:

| Claim | Where | Stated | Actual |
|---|---|---|---|
| `unplaced.csv` rows | `hardware/README.md`, `pcb-pipeline.md` | 34 | **32** |
| `unplaced.csv` units | `pcb-pipeline.md` | 75 | **67** |
| `bom.csv` master | `pcb-pipeline.md` | 138 rows / 388 units | **139 / 390** |
| rows in the 23 fragments | `pcb-pipeline.md` | 104 rows / 313 units | **107 / 323** |
| rows that moved out | `hardware/README.md` | "Sixteen" | **18** |
| rows still unplaced | `repo-maintenance.md` | 50 of 138 | **32 of 139** |

And `[repo] docs/reference/pcb-pipeline.md` names five refdes as "module-board
netlist parts […] missing from `module.net`": `[test]` **`J-CV` ×6 and
`D-CLAMP-BREATH` ×2 are no longer in `unplaced.csv`** — both were moved out by
this same batch, `J-CV` into `hardware/module/bom.csv` and `D-CLAMP-BREATH` into
`hardware/module/breath-receive-stage/bom.csv`. The paragraph's own bolded
punchline — *"`D-CLAMP-BREATH` is the shape of the problem […] its row is still
in `unplaced.csv`"* — describes a state the same commit ended. Its remaining
three (`U-TVS-MODULE`, `R-BREATH-SUM` ×2, `R-BREATH-OFF` ×2) are correct.

**What would settle it:** re-derive all six numbers from the tree in one pass
and cite one of them rather than restating six. The row count of
`unplaced.csv` is exactly the kind of quantity `config/figures.yaml` exists for.

### B3. `hardware/README.md` narrates a deduplication that did not happen

`[repo] hardware/README.md:47-49`:

> *(This definition sat inline in all 23 circuit pages until 2026-09-21 —
> twenty-three copies of one paragraph, in a repository whose first rule is
> state it once and cite it. It is here, and they cite it.)*

`[test]` Reading the pre-batch text of `pitch-stage.md`, `power-entry.md`,
`breath-adc.md` and `spi-link.md`: **no circuit page carried a `Dir`/`Peer`
column definition before this batch.** The columns were used and never defined.
Nothing was moved out of the 23 pages — a one-line pointer was added *to* them,
and `[test]` **22 pages still carry the duplicated "Quantities appear **only**
as a citation … it does not restate values" preamble**, which is the only
paragraph that was ever in 23 copies and is still in 22.

The new section is a genuine improvement and the `Dir`/`Peer` definitions are
new and useful. Only the parenthetical's history is invented. It matters because
this corpus uses those parentheticals as its record of *what was wrong before*,
and a fabricated one teaches the next reader to distrust the true ones.

---

## C. One ASCII drawing was corrupted by the fix

Not a deletion — a regression introduced while adding a refdes, and exactly the
drawing-gutter hazard `CLAUDE.md` §2 warns about.

`[repo] hardware/module/breath-receive-stage/breath-receive-stage.md:67`. The
batch prefixed `[D-CLAMP-BREATH] ` (17 characters) to a drawing line without
re-padding it:

```
-                              BAV99 to ±12 V, both legs  ◄──────────┼─┤
+                              [D-CLAMP-BREATH] BAV99 to ±12 V, both legs  ◄──────────┼─┤
```

`[test]` Column positions of `│┼┐┤` on lines 62–70 of the current file:

```
  63  [68, 70]      66  [68, 70]
  64  [68, 70]      67  [85, 87]   ← the umbilical pair's two rails
  65  [68, 70]      68  [68, 70]
```

The `┼─┤` that tees the BAV99 clamp onto the incoming `BREATH`/`AGND` pair now
sits 17 columns right of the rails it used to join. In the rendered drawing the
clamp connects to nothing and the sense pair has a one-row break in it. The
second edit on the same page (line 110, `[D-CLAMP-BREATH BAV99]── ±12 V`) is
**fine** — `[BAV99]` already spanned the column the vertical runs in, and the
longer label still does.

One-line fix: delete 17 spaces from the run before `◄`.

---

## D. The conservation proofs, with their results

### D1. Numeric conservation — clean

`[test]` Bag of every `\d+([.,]\d+)*` token across every corpus file at both
revisions:

```
old distinct 998   new distinct 1041   GONE 0   NEW 43
```

**No numeric token that existed in the corpus is absent from it now.**

`[test]` Repeated at value+unit granularity (`([-−+]?\d+(\.\d+)?)\s*(V|mV|mA|µs|ms|mm|HP|Ω|…)`),
1,253 → 1,273 distinct pairs, **3 gone**, each verified by eye:

| Token | Was in | Verdict |
|---|---|---|
| `+5.21 V` ×2 | `breath-output-stage.md` | **Replaced by a citation.** Table row and drawing label both now read `DAC AVDD` / `` `dac-rail` ``. Correct under rule 1 |
| `18 ms`, `2 ms` | `latency-budget.md` | **Superseded.** The hypothetical *"if these switches settle in 2 ms … buys back 18 ms"* is replaced by the banked vendor maximum (`5 ms max at 16 in/sec`, → 15 ms bought back). Deliberate, narrated, and better-sourced |

`[test]` Per-file numeric departures were also checked; every one resolves to a
tracked-figure citation added in the same file, a moved BOM row, or a
superseded candidate that survives on its owning page (`1.1 mm`, `2.1 mm`,
`80 %` left `cluster-boards.md` and are all present in `ks33-geometry.md`
lines 42/48/162 and ADR 0002 lines 141/152).

### D2. `hardware/unplaced.csv` — all 18 accounted for

`[test]` 50 rows → 32 rows; 18 refs removed, **0 added**. Each removed ref
checked against every per-circuit `bom.csv` fragment **and** the generated
master:

```
U-DAC          → module/dac8568/            R-SER-BREATH   → interfaces/breath-sense-link/
R-PRECISION    → module/pitch-stage/        C-FILT-BREATH  → module/breath-receive-stage/
J-CV           → module/            (board) C-BULK-RAIL    → module/power-entry/
J-UMBILICAL    → module/power-entry/        C-TIMER-LOADSW → module/umbilical-load-switch/
U-DIFFRX       → module/breath-receive-stage/  C-GATE-LOADSW → module/umbilical-load-switch/
U-LVL-MOD      → module/digital-and-supervision/  D-CLAMP-BREATH → module/breath-receive-stage/
D-REVPOL       → module/power-entry/        R-GAIN-INAMP   → module/breath-receive-stage/
U-REG-DAC      → module/power-entry/        R-REG-SET      → module/power-entry/
C-REG-ADJ      → module/power-entry/        FB-IN          → module/power-entry/
```

**All 18 present in a fragment and in `hardware/bom.csv`. None vanished.**
`[test] python3 tools/merge-bom.py --check` → `checked 139 rows from 26
fragments | 0 problems`, so the master is a faithful regeneration and no row
was lost in the merge.

`[test]` Field-by-field comparison of the 18 moved rows, old `unplaced.csv`
against new fragment: **no row lost any field content.** Four gained text
(`U-DAC` the order-code refutation; `J-CV` and `D-CLAMP-BREATH` a
"moved out of unplaced.csv" note that preserves *why* they were unplaced;
`U-DIFFRX` the corrected effective gain). `U-DIFFRX` is the only one where a
number left — `-9.6 V` → `inamp-full-scale` — and `[test] -9.94 V` survives at
`breath-receive-stage.md:133`, `breath-sense-link.md:165` and in
`breath-receive-stage/bom.csv`'s `R-GAIN-INAMP` row.

`[test]` BOM `notes` fields rewritten to cite rather than restate: six rows
(`R-ADCDIV`, `R-KEY-SER`, `C-KEY`, `U-BREATH`, `D-TVS-BREATH`, `PANEL`). **No
argument was lost with the number in any of them.** The only one where an
argument left a row is `PANEL`, whose line-item height budget
(`5 label + 22 pots + 39 jacks + 31 etherCON = 97 mm`) was removed — and
`[test]` it survives in full in `config/figures.yaml:405`
(`panel-height-budget.derivation`, in the corrected 110 mm form) and as a
derived table at `docs/decisions/0004-cv-interface-module.md:787-809`. Correct
under rule 1: the owner states it, the BOM cites it.

### D3. `config/figures.yaml` — nothing removed that should not have been

`[test]` Parsed both revisions and compared entry-by-entry:

- **0 figure entries removed**; 2 added (`breath-sensor-slope`,
  `ks33-contact-bounce`). 35 → 37.
- **0 fields removed from any entry.** No `escape_note`, `escape_note_2`,
  `escape_note_3`, `false_positive_note` or `derivation` was deleted. (The
  brief flagged "whole `escape_note` blocks removed"; `[test]` I find none —
  the deleted `forbidden:` and `owner:` lines in the raw diff are all *replaced*
  lines, which read as deletions in a line diff.)
- **3 `forbidden` patterns dropped, all three deliberate and documented in the
  file itself:**

| Figure | Pattern | Why it went |
|---|---|---|
| `key-pullup-qty` | `Twenty-one sets` | `figures.yaml:305` comment: it matched `[repo] docs/decisions/0001:217` "Twenty-one sets across the…", **a true sentence**. Exactly the `false_positive_note` discipline `CLAUDE.md` §2 asks for |
| `loadswitch-timer` | `12x to 300x` | `figures.yaml:478` comment: occurs only *inside* the sentence recording the correction. Kept as a `note:` instead |
| `spi-series-r` | `220 Ω with\n~200 pF` | The hard-wrapped pattern `CLAUDE.md` §2 names as one that "can never fire". Split into `220 Ω with` + a `false_positive_note` explaining why `~200 pF` must not be re-added |

`[test]` Nine `owner:` values were repointed (all from a retired parent page —
`hardware/bom.csv`, `carrier/carrier.md`, `module/power-entry/power-entry.md` —
to the circuit that now derives the figure). Every new owner path exists.

### D4. The `depends_on` graph — 7 edges removed, all replaced

`[test]` Edge-set difference per circuit across all 23 `circuit.yaml`:

- **7 `circuit:` edges removed**, every one an instance of the documented
  defect (nets attributed to `module/digital-and-supervision` that come from
  `module/dac8568`, and two `module/power-entry` edges that belong to
  `module/link-supervision` / `module/umbilical-load-switch`). Each removal is
  accompanied by a replacement in the same file.
- **0 `refdes:`, `adr:` or `fig:` edges removed anywhere.** The only additions
  of those kinds are on `module/panel`, which gained an Interfaces table.
- `[test]` The rebuilt graph: **23 circuits, 48 undirected edges, every edge
  declared from both ends, every edge resolves, no isolated circuit.** The new
  header's claims check out exactly.

### D5. The 23 Interfaces tables — one row count changed, no content dropped

`[test]` Parsed the `## Interfaces` table from every circuit page at both
revisions and compared row counts:

| Page | Rows | Verdict |
|---|---|---|
| `breath-output-stage.md` | 7 → 6 | **`−12 V` merged into the `±12 V` row.** `[repo]` its content — *"`R-OFFNEG`'s fixed leg […] chosen over +12 V because that rail carries no LED current"* — is preserved verbatim in the merged row |
| `breath-sense-link.md` | 13 → 14 | gained `presence detect on the pair` |
| `spi-link.md`, `dac8568.md`, `panel-led.md` | +1 each | gained a row |
| `panel.md` | 0 → 8 | gained a table |
| other 17 | unchanged | |

`[test]` Every deleted table row was matched to its replacement by hand. Content
that could have been dropped and was not: `breath-adc`'s `CH1 … Spare input`;
`display-and-service-uart`'s `EN, IO0 … Withdrawn`; `led-strip-drive`'s
`OE ×4 … tied LOW`; all three `link-supervision` "Not fitted" rows;
`mod-channels`' `CLR` row and its park-at-0 V argument; `pitch-stage`'s
`VREFOUT` tracking argument; `key-chain-loom`'s `LK-SER, R-SER-TERM … Proposed`;
`power-entry`'s `+12 V analog` note (merged into the `MODULE ANALOG +12V` row);
`breath-sense-link`'s name-collision preamble (rewritten past-tense and
extended).

The `J-UMB` pin numbers (`pin 1`, `pin 2`, `pin 4`, `pin 5`, `pin 7`, `pin 8`)
left the `Node` cells of `spi-link.md` and `breath-sense-link.md`. `[test]`
That is not a loss: both tables cite `umbilical-pinmap`, whose `value` is
`1,2 BREATH/AGND | 3,6 +12V/PWR_GND | 4,5 SCLK/MOSI | 7,8 CS/DIG_GND` — the
pin numbers were a restatement and are now a citation. Correct under rule 1.

### D6. Figure citations — none lost

`[test]` Counted every occurrence of every one of the 37 figure ids in every
corpus file, both revisions. **No figure is cited fewer times overall, and no
figure is uncited.** Exactly two (file, figure) pairs disappeared —
`diode-split-rationale` and `umbilical-current` leaving `hardware/unplaced.csv`
— and both are because the row carrying them moved into
`hardware/module/power-entry/bom.csv`, where both citations are present.

### D7. `path-map-2026-09-21.csv` — 22 rows deleted, zero lookups lost

`[test]` 287 rows → 410. 22 rows deleted. **The `old` column is a superset: not
one old path became unanswerable.** The 22 deletions are the rows whose `new`
pointed at `datasheets/other-semi/…` and `datasheets/texas-instruments/…` —
directories the re-filing retired — replaced by `moved` rows with real
destinations. This is the repair the file's own new §7 note describes, and it
landed.

### D8. `check-conservation.py` — used as evidence, not proof

`[test]` Run with `<rev> <path> <path>` on all 39 changed corpus `.md` files. It
reported 8 "REAL GAPS" on `pcb-pipeline.md`, 8 on `ks33-geometry.md`, 8 on
`repo-maintenance.md`, 6 on `cluster-boards.md`, 3 on `latency-budget.md`, a
`HEAD` loss on `panel.md`, a `TAIL` loss on `module.md` and `ks33-geometry.md`,
and "REPEATED PASSAGES THINNED" on `cluster-boards.md`, `key-register.md` and
`digital-and-supervision.md`.

**I read every one against the diff. All are seams or deliberate rewrites.**
The thinning reports are the tool seeing a table-cell phrase that appeared 2–3×
in a table whose cells were all rewritten; the `HEAD`/`TAIL` reports are
`panel.md`'s reversed self-description and `module.md`'s struck-through bullet,
both narrated in place. The tool's new head/tail and multiplicity checks did
fire on real edits — they are working — but on this batch they produced no
finding a reader would act on.

The tool was itself changed in `0e68f25`, so I treated it as evidence: **every
one of my four positive findings above came from a hand comparison or a census
script, not from its output.** Conversely, nothing it flagged survived
inspection, which is a weak corroboration of the batch rather than of the tool.

---

## E. Historical records — rule 6 upheld

`[test]` `git diff --name-status 0e68f25~1..HEAD -- docs/review docs/log docs/research`:

```
A  docs/review/2026-09-22-fix-audit/README.md
M  docs/review/2026-09-21-pre-merge-review/STATUS.md
```

`[test]` The one modification is **`+27 / −0`** — a pure append, in commit
`04b5208`, to the file `CLAUDE.md` designates as "what actually landed". No line
of any historical record was changed or removed. `docs/log/` and
`docs/research/` were not touched at all. **Confirmed clean.**

`[test]` Across the whole batch: 83 modified, 4 added, **0 deleted, 0 renamed**.

---

## F. Minor, for completeness

- `[repo] README.md:113-121` replaced "`datasheets/` is 77 banked documents […]
  `docs/review/` is seven waves" with "`docs/review/` holds **nine** waves" —
  in the same sentence that explains *"The counts that used to sit in this
  sentence […] were true when written and wrong within the week, which is the
  whole reason this repository cites rather than restates."* `[test] ls -d
  docs/review/*/` → **10**, because `092b364` (this wave) added the tenth in the
  same batch. The rewrite removed one restated count and left another, already
  stale on arrival. Dropping the number entirely is the fix the sentence itself
  argues for.
- `[repo] CLAUDE.md:114` — the same shape, one file up. The batch corrected
  "Three have run" to "**Nine have run**" and added, in the same sentence,
  *"this list is not kept in sync by anything and said 'three' for months while
  the directory held nine."* `[test] ls -d docs/review/*/` → **10**: commit
  `092b364`, in this batch, made it ten while the paragraph was being written.
  The correction is right about the mechanism and off by one about the count,
  the same day. `[test]` The rest of the `CLAUDE.md` diff is pure addition —
  `check-conservation.py` reports 2 gaps, both this rewrite, and no other loss.
- `[repo] hardware/carrier/breath-adc/breath-adc.md:29` and the other rewritten
  `AGND` rows now say "drawn `AGND-local` in `carrier.md` §2" — the drawings
  themselves still carry the unqualified names, as `pcb-pipeline.md` §1 now
  states. That is a declared, tracked gap, not a loss; flagging only so the next
  reader does not re-file it as one.

---

## What I did not cover

- `datasheets/**` beyond checking that `.manifest-R9.csv` reaches the generated
  master (`[test] python3 tools/verify-datasheets.py` → `78 verified, 23
  recorded as blocked or not-fetched, 0 problems`; the R9 `DAC8568ICPW` row
  resolves through `.moves.csv` to `analog/DAC8568CIPW.pdf` and is in
  `MANIFEST.csv`). D9–D11 own that ground.
- Whether the *replacements* are correct. I checked that content was conserved,
  not that the new text is true. `latency-budget.md`'s rebuilt totals,
  `ks33-geometry.md`'s reversed standoff conclusion and `figures.yaml`'s two new
  figures are D12–D15's and D6–D8's.
- `tools/**`. Not deletions, and D1–D5's. (`CLAUDE.md` is not in the corpus
  list `CLAUDE.md` §6 gives, but it changed in this batch, so I ran the same
  checks on it — see §F.)

## Findings a fixer could act on, ranked

1. **§B1** — `repo-maintenance.md:204-208` is stale by 18 rows, in the document
   that owns `bom.csv`. Highest value: it is the failure mode, in the file about
   the failure mode.
2. **§B2** — six `unplaced.csv`/`bom.csv` counts across three files disagree
   with the tree and with each other, and `pcb-pipeline.md` names two refdes as
   unplaced that this same batch placed.
3. **§C** — one line of ASCII in `breath-receive-stage.md:67`, 17 spaces.
4. **§A1** — two sentences of schema rationale to restore, in **one** place.
5. **§B3** — a parenthetical that narrates a deletion that did not happen.
6. **§A2** — one missing link on `display-and-service-uart.md`.

None of these is a blocker for the merge. Item 1 is the one that will cost
someone an afternoon if it survives another wave.
