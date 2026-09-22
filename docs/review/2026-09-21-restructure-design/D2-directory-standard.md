# D2 — The standard for a circuit directory

**Agent D2, cold.** No `docs/review/**`, `docs/log/**` or `docs/research/**` was
read, including this wave's own `README.md`.

**Provenance:** `[repo] path:line` · `[calc]` with arithmetic · `[web]` URL ·
`[from memory]`. Unmarked claims are defects; there should be none.

**Working inside:** content freeze (moves and splits only); circuit blocks are
the primary axis; per-circuit `bom.csv` is a fragment that generates
`hardware/bom.csv` (the generator is another agent's slice — I define where the
file sits and what its rows *mean*).

---

## 0. Measurements this standard is built on

Everything below is designed against these, not against taste.

| # | Measurement | Provenance |
|---|---|---|
| M1 | **39** backtick references to the 8 schematic pages in the live corpus, **every one a bare basename** with no directory path — e.g. `` `power-entry.md` `` ×10 | `[repo]` `grep -rno '`(power-entry\|pitch-stage\|mod-channels\|carrier\|cluster-boards\|breath-receive-stage\|breath-output-stage\|digital-and-supervision)\.md`' --include=*.md .` minus `docs/{review,log,research}` → 39; `power-entry.md` at `docs/reference/pcb-pipeline.md:95,130,246`, `docs/decisions/0004-cv-interface-module.md:320,326,334`, `hardware/controller/carrier.md:125,643`, `docs/decisions/0006-cv-channel-allocation.md:630,643` |
| M2 | Only **3** relative markdown links point between hardware pages | `[repo]` `hardware/module/mod-channels.md:4` (×2), `hardware/module/pitch-stage.md:4` |
| M3 | **27 of 138** BOM rows are named on more than one schematic page; **50** are named on no schematic page at all | `[calc]` over `hardware/bom.csv` × the 8 pages, word-boundary match. Spot-checked: `U-DAC`, `J-CV`, `C-FILT-BREATH`, `R-GAIN-INAMP`, `PCB-MODULE`, `U-LOADSW` appear in `hardware/bom.csv` and nowhere else in `hardware/` or `docs/decisions/` `[repo]` |
| M4 | **47** open bullets across the 8 pages; **13** name a ROADMAP gate; **6** are struck-through/`CLOSED` items still sitting under `## Still open` | `[calc]` parse of the `## Still open` / `## Open before layout` sections |
| M5 | `ROADMAP.md`'s central "Open items blocking work" table has **4** rows | `[repo] ROADMAP.md:224-231` — 4/47 = **8.5 %** coverage `[calc]` |
| M6 | Provenance markers are **concentrated in the two newest pages**: `carrier.md` 111, `cluster-boards.md` 49, all six module pages **11 between them** | `[calc]` `grep -o` counts of `[calc]`/`[repo]`/`[web]`/`[from memory]` per page |
| M7 | **8 of 8** pages carry `**Status:**` on line 3 | `[repo] hardware/*/*.md:3` |
| M8 | `check-staleness.py` walks `CORPUS_DIRS = ["hardware", …]` **recursively** and accepts `.md/.csv/.yaml` at any depth | `[repo] tools/check-staleness.py:30,50-58` |
| M9 | `check_bom()` hard-codes **`hardware/bom.csv`** and is the only column-count/duplicate-refdes check | `[repo] tools/check-staleness.py:111-123` |
| M10 | `check_refdes()` exists, finds 36 drawn-but-unBOMmed tokens, and **is never called from `main()`** | `[repo] tools/check-staleness.py:126-145` vs `159-218`; `[calc]` re-running its body gives 36 tokens incl. `C-GATE`, `C-TIMER`, `R-LED`, `R-OE-PU` and package-name false positives `SOIC-14`, `SOT-23-6` |
| M11 | `config/figures.yaml` has **33** figures; **21** name an owner under `hardware/**` (17 `.md`, 4 `hardware/bom.csv`). `owner:` is **never read** by the checker | `[calc]` over `grep '^    owner:'`; `[repo] tools/check-staleness.py:61-108` uses only `id`, `value`, `forbidden`, `status`, `quantity`, `decided_by` |
| M12 | `carrier.md` is already **7 circuits in one file** (`## §1`…`## §7`), `cluster-boards.md` **5**, and `breath-output-stage.md` contains a second **H1** mid-file (`# §4 Response control`, line 169) | `[repo] hardware/controller/carrier.md:82,162,439,591,683,760,809`; `cluster-boards.md:89,128,237,312,422`; `breath-output-stage.md:169` |

**M12 is the justification for the whole restructure and it is not mine to
argue** — I record it because the file set below has to serve a `carrier/`
that becomes seven directories, not only a `pitch-stage/` that becomes one.

---

## 1. The file set

```
hardware/<board>/<circuit>/
├── <circuit>.md      REQUIRED   the schematic page
├── bom.csv           REQUIRED   this circuit's BOM fragment
├── notes.md          OPTIONAL   the circuit's Superseded shelf
├── sim/              OPTIONAL   ngspice deck + run record
│   ├── <name>.cir
│   └── README.md
└── netlist.py        RESERVED   SKiDL source; slot named, not yet filled
```

### 1.1 What each file owns — one sentence each

| File | Owns, and nothing else does |
|---|---|
| `<circuit>.md` | **The circuit as it is now**: its boundary nets, its topology, and the derivation that sets each value. |
| `bom.csv` | **Part identity and quantity**: refdes, part/value, manufacturer, package, per-circuit qty, status, source. |
| `notes.md` | **What this circuit used to be and what it is not**: rejected options, corrections to earlier versions of the page, closed open-items. |
| `sim/` | **How a simulation was run**: the deck, the banked-model reference, and the command. Never the resulting number. |
| `netlist.py` | **The machine-readable connectivity** of the same drawing. |

The two-files-never-own-the-same-fact test, applied to the pairs that actually
collide in this corpus:

| Collision | Resolution |
|---|---|
| `<circuit>.md` values table vs `bom.csv` `part` column | `bom.csv` owns the **value**; the page owns the **derivation**. See §1.4 — this is the one place the freeze bites and I say so. |
| `<circuit>.md` vs `notes.md` | **Tense.** Present → page. Past → notes. §3.2. |
| `<circuit>.md` vs an ADR | **Blast radius.** Reversing it touches something outside this directory → ADR. §3.1. |
| `sim/` vs `config/figures.yaml` | `pcb-pipeline.md` already decided this: *"Results land in `config/figures.yaml`; `.LIB` files get banked in `datasheets/` with SHA-256"* `[repo] docs/reference/pcb-pipeline.md:139-141`. `sim/` therefore owns the deck and the invocation, figures.yaml owns the number, `datasheets/` owns the model. Three owners, no overlap. |
| `bom.csv` fragment vs `hardware/bom.csv` | Fragment is source, root file is **generated** — same relationship as `.manifest-R*.csv` → `MANIFEST.csv` `[repo] docs/reference/repo-maintenance.md:17-18`. The generated file must therefore carry the §4-style "edits are silently destroyed" banner. |

### 1.2 Justifying every file beyond the owner's four

The owner's sketch was schematic + BOM + SPICE + `notes.md`. I add **one**
slot and **promote one** from file to directory.

| Addition | Why it earns its place | Why not fold it into an existing file |
|---|---|---|
| `sim/` as a **directory**, not a `sim.cir` file | A deck is never one file: it needs the `.control` block, a `.lib` include pointing at a banked model, and the stdout of the run that produced the claim. `pcb-pipeline.md:47-50` records that ngspice 42 needs `set ngbehavior=psa` **in `.spiceinit`, not in `.control`** `[repo]` — that is a second file before the first sim is run. | Folding the deck into the page turns an executable artefact into a code fence that cannot be run, which is how a sim result drifts from its deck. |
| `netlist.py`, **reserved and empty** | `pcb-pipeline.md:115` specifies *"`pcb/src/module/*.py`, one module per schematic page, `module.py` importing the six"* `[repo]`. That mapping is 1:1 with circuits. Naming the slot now means the pipeline lands **beside** the drawing rather than forking a parallel `pcb/` tree whose files nothing links to. `hierplace` groups by module = by schematic page `[repo] docs/reference/pcb-pipeline.md:152`, so the directory boundary and the placement group become the same boundary. | If it goes under `pcb/src/`, "the drawing and the netlist disagree" is a two-directory diff. In the circuit directory it is a one-directory diff. |

`pcb-pipeline.md` is **Proposed 2026-09-21, "Not run"** `[repo]
docs/reference/pcb-pipeline.md:3-4`, so `netlist.py` is **reserved, not
required**. Reserving a name costs nothing; discovering later that the pipeline
built its own tree costs a migration.

**Files I considered and rejected:**

| Rejected | Why |
|---|---|
| `README.md` per circuit directory | See §6. It collides with the corpus's existing meaning of `README.md` (index), and it breaks all 39 basename references (M1). |
| `open.md` per circuit | Open items must be read by the person editing the drawing. A separate file is the project's named failure mode with the polarity reversed — *"Fixes land where the editing is happening; they do not land where the reader looks"* `[repo] CLAUDE.md:11-12`. §4 keeps them in the page and **generates** the central view. |
| `nodes.csv` / machine-readable interface file | The interface table (§2) is six rows. A CSV buys a checker and costs a second place for a node name to live. Revisit only if a tool needs it. |
| `datasheets/` per circuit | `hardware/datasheets/.gitkeep` already exists as an empty second datasheet home `[repo]`. Banking is centralised with SHA-256 + `MANIFEST.csv` `[repo] CLAUDE.md:44-50`. **Do not create a third.** The restructure should delete `hardware/datasheets/`, not multiply it. |

### 1.3 `bom.csv` fragment — what a row *means*

The generator is not my slice. The **semantics** are, and M3 makes them
non-obvious: 27 rows are used by more than one circuit and 50 are used by none.

**Three row kinds, distinguished by the existing `status` column — no schema
change, still 11 columns, still CRLF** `[repo] docs/reference/repo-maintenance.md:126-136`:

| Kind | `status` | Columns filled | Meaning |
|---|---|---|---|
| **Owning** | `candidate` / `open` / `selected` / `purchased` / `available` / `not-needed` (the six values in use, `[calc]` over `bom.csv`) | all 11 | This circuit originates the part. Exactly one fragment per refdes may do this. |
| **Using** | `uses:<board>/<circuit>` | `ref`, `qty`, `status` only; rest empty | This circuit consumes N of a part another circuit owns. Contributes quantity, asserts no identity. |
| **Unplaced** | any owning value | all 11 | Lives in `hardware/unplaced.csv` — the home for the 50 rows no drawing names (M3). |

**`qty` in a fragment is the count used by that circuit, not the purchase
total.** This is the load-bearing decision in this section:

- The alternative — whole-design qty repeated in each fragment — puts a fact
  about circuits the file cannot see *into* the file. That is exactly the
  project's named failure mode `[repo] CLAUDE.md:8-12`.
- It has already bitten once in this corpus: `R-OUT-PROT`'s row records *"POWER
  RATING IS NOT OPTIONAL and the worst case moved when pitch took jack-side
  feedback"* `[repo] hardware/bom.csv`, `R-OUT-PROT`. A pitch-local change moved
  a figure on a row shared with three other circuits.
- With per-circuit qty, adding a mod channel edits one fragment and the total
  follows. With whole-design qty it edits six or goes stale in five.

**Three invariants the generator must enforce, stated here because they are
meaning, not mechanism:**

| # | Invariant | What it catches |
|---|---|---|
| B1 | Exactly one owning row per refdes across all fragments | Two circuits silently disagreeing about a part |
| B2 | Every `uses:` row names a circuit that owns that refdes | A refdes renamed in one place |
| B3 | Published `qty` = Σ owning qty + Σ using qty | The `R-OUT-PROT` 5→6 class of drift, mechanically |

**M9 is a trap the restructure creates and must fix in the same commit:**
`check_bom()` validates only `hardware/bom.csv` `[repo]
tools/check-staleness.py:111-123`. A fragment with 10 columns or a duplicate
refdes is **not checked today** and would only surface as a malformed generated
file. Column-count and duplicate-refdes validation must extend to
`hardware/**/bom.csv`.

**M8 is a trap the restructure creates and cannot fix:** `corpus_files()`
accepts `.csv` at any depth under `hardware/` `[repo]
tools/check-staleness.py:50-58`, so a forbidden value present in both a
fragment and the generated `hardware/bom.csv` is **reported twice**. Every
stale-BOM-value report will double. Not a correctness bug; a noise cost, and
worth pre-announcing so nobody "fixes" it by deleting a real hit.

### 1.4 The one collision the freeze does not let me close

`hardware/module/pitch-stage.md:134` carries `| **C-FB-PITCH** | **2.2 nF C0G**
| … |`. `hardware/bom.csv`'s `C-FB-PITCH` row carries `2.2nF C0G/NP0` `[repo]`.
**Same fact, two files, today.**

Under the standard, `bom.csv` owns the value and the page's table should be
`Ref | Job` with no `Value` column — the value is read from the fragment sitting
in the same directory, which is the first time in this project's history the
two have been adjacent.

**I am not proposing that as part of the restructure.** Dropping a column
deletes content and the freeze forbids it. The sequencing is:

1. **Restructure commit** — move the table verbatim. Duplication persists,
   unchanged in kind and count.
2. **Post-freeze** — drop `Value`, one circuit at a time, each with a
   `git diff --stat` check `[repo] docs/reference/repo-maintenance.md:133-136`.

**And a related boundary I am explicitly *not* drawing.** It is tempting to
rule that `bom.csv`'s `notes` column carries sourcing facts only and design
argument belongs to the page. **That rule would break the checker.**
`repo-maintenance.md:139-141` records that `notes` is append-only, corrections
added after a ` | ` with a date, superseded text left in place, and *"That is
what makes the checker's refutation detection work, and it is why rows are
long"* `[repo]`. Stripping argument out of `notes` strips the refutation wording
the `REFUTATION` regex keys on `[repo] tools/check-staleness.py:36-41`, and rows
that pass today would go live. **`notes` stays exactly as it is.** The rule is
the weaker, safe one: the page never restates a value that the fragment owns;
the fragment never introduces a derivation that has no home on the page.

---

## 2. The schematic page format

### 2.1 Required content

| Element | Required? | Rule |
|---|---|---|
| H1 `# <Circuit> — schematic` | yes | One H1 per file. `breath-output-stage.md:169` has a second `# §4 …` `[repo]` — that second H1 **is** the split boundary. |
| `**Status:**` line, line 3 | yes | 8/8 pages already do this (M7). Vocabulary below. |
| `## Interfaces` node table | yes | §2.3. The only new element, and the split is what creates the need. |
| `## The circuit` + ASCII drawing | yes | Project convention `[repo] CLAUDE.md:128`; 8/8 pages use this heading or a suffixed form `[repo]`. |
| `## Component values` | yes | `Ref \| Value \| Job` (→ `Ref \| Job` post-freeze, §1.4). |
| Derivation sections | as needed | Free headings. Each derived number carries a provenance marker. |
| `## Still open` | yes, even if empty | Exact spelling. §4. |

`Status` vocabulary — small, because ADRs already proved a 3-value vocabulary
is enough `[repo] docs/decisions/README.md:18-22`:

| Value | Meaning |
|---|---|
| `Drawn <date>` | Topology settled; values may still move |
| `Redrawn <date>` | Superseded an earlier drawing; `notes.md` says what changed |
| `Blocked on <token>` | Cannot be drawn until `<token>` resolves; `<token>` is a ROADMAP gate, a `datasheets/` path or a `figures:<id>` |

### 2.2 Provenance markers

`CLAUDE.md:102-104` requires `[repo]` / `[calc]` / `[web]` / `[from memory]` on
**review** claims `[repo]`. The two newest schematic pages have adopted it
anyway — 111 and 49 markers — while the six module pages carry 11 between them
(M6).

**Rule:** every number on a schematic page that is not read straight off the
drawing carries one of the four markers. `[calc]` shows the arithmetic inline,
as `carrier.md:125` already does (`**The input LC is stable** `[calc]``)
`[repo]`.

**Say plainly what this costs:** it is a real gap on six pages, not a formality
already satisfied. `pitch-stage.md` has **zero** markers (M6) against roughly
thirty derived numbers. The split is the cheapest moment to add them, because
each derivation is being touched anyway — but it is work, and the standard
should not pretend otherwise.

### 2.3 `## Interfaces` — the one new element, and why

This is the only thing I require that the current pages do not have, and I want
the justification on the record because it is also the only place I knowingly
add content under a content freeze.

**The split manufactures boundaries that did not exist.** While `carrier.md` is
one file, "§1's rail name matches §3's" is guaranteed by both being in front of
the same reader. After the split it is a cross-directory fact with no owner and
no checker.

The corpus already has a tracked figure that is purely this defect:
`cref-out-node` — *"three drawings disagree about which side of the reference
buffer `C-REF-OUT` sits on"* `[repo] docs/reference/pcb-pipeline.md:104-105`,
`[repo] config/figures.yaml:276` (`- id: cref-out-node`). And `CLAUDE.md:105`
already asks reviews for **node-indexed findings** `[repo]`. The interface table
is what makes a node index exist in the corpus rather than only in reports.

Format — **identifiers only, never quantities**:

| Node | Dir | Peer | Figure | Note |
|---|---|---|---|---|
| `VREFOUT` | in | `module/digital-and-supervision` | — | Buffered reference |
| `PITCH` | out | panel jack `J-CV` | `figures:pitch-cents-budget` | |

A voltage may appear **only** as a `figures:<id>` citation. That keeps the table
out of the "cite, do not restate" rule's way `[repo] CLAUDE.md:16-19`: a node
*name* is an identifier, and identifiers are what citations are made of.

### 2.4 Heading skeleton

````markdown
# <Circuit> — schematic

**Status:** Drawn <date>. <one line: which board, what it sits between>

## Interfaces

| Node | Dir | Peer | Figure | Note |
|---|---|---|---|---|

## The circuit

```
<ASCII drawing — every refdes shown here has a row in bom.csv or a
 `uses:` row; every net crossing the box appears in ## Interfaces>
```

## Component values

| Ref | Value | Job |          <!-- Value column removed post-freeze, §1.4 -->
|---|---|---|

## <derivation heading>          <!-- repeatable; `[calc]` shows the arithmetic -->

## <derivation heading>

## Still open

- **<title>.** <body> **Decided by:** <gate | datasheets/<path> | figures:<id> | owner's call>
````

---

## 3. Where a decision lives — the hard boundary

Three possible homes (ADR, page, `notes.md`) is two too many unless the test is
mechanical. Two rules, applied in order, and a ratchet.

### 3.1 Rule D1 — blast radius decides ADR vs circuit

> **A decision is an ADR if reversing it would change a file outside this
> circuit directory. Otherwise it belongs to the circuit.**

| Reversing it would touch | Home |
|---|---|
| Another circuit, another board, `firmware/`, the panel, `config/`, a purchase | **ADR** |
| Only this directory | **Circuit** |

Worked against real cases:

| Decision | Radius | Home | Evidence |
|---|---|---|---|
| Six DAC channels, two dedicated + four assignable | Pitch, mod ×4, breath, firmware, panel | ADR | is ADR 0006 `[repo] docs/decisions/0006-cv-channel-allocation.md:5-7` |
| Pitch DC feedback tapped at the jack, not the op-amp output | Pitch only — mod channels explicitly unaffected `[repo] hardware/module/pitch-stage.md:231-233` | Circuit | correctly on the page today `[repo]:159` |
| `TRIM-OFFSET` moved ahead of the reference buffer | Pitch only; `R-OFFINJ` deleted | Circuit | `[repo] hardware/module/pitch-stage.md:235-247` |
| Two-resistor form for the mod channels at `k = 3`, offset channel at 3.3333 V | Mod channels **and** ADR 0006's allocation table **and** firmware | ADR | ADR 0006 carries it `[repo]:22`; `mod-channels.md:248` records *"the call belongs to the author"* `[repo]` — correct escalation |

**The escalation case is the one that matters.** `mod-channels.md:210` has a
whole section headed *"The alternative topology, recorded rather than adopted"*
ending *"it is a redraw of a settled page and the call belongs to the author"*
`[repo]:248`. Under D1 that section's *content* is circuit-local (it is one
page's topology) but its *consequence* reaches ADR 0006's table — so it is an
ADR question parked on a page. D1 makes that visible instead of leaving it to
judgement.

### 3.2 Rule D2 — tense decides page vs `notes.md`

> **The page is present tense. `notes.md` is past tense.** The page says what
> the circuit *is*. `notes.md` says what it *was* and what it is *not*.

| Sentence contains | Home |
|---|---|
| "an earlier version of this page", "used to say", "was wrong", "not adopted", "rejected because", "superseded", "CLOSED" | `notes.md` |
| Simple present about the circuit as drawn | page |

`notes.md` is **the circuit's Superseded shelf** — the same convention ADRs
already run at project scope: *"When a decision is reversed, do not edit the old
ADR. Mark it `Superseded` and write a new one"* `[repo]
docs/decisions/README.md:31-33`. One convention, two scopes, no third idea.

### 3.3 Rule D3 — `notes.md` may not hold a live value, and the checker already enforces it

This is the part that makes the third home safe rather than dangerous.

`notes.md` sits under `hardware/`, so `check-staleness.py` scans it with no tool
change (M8). A forbidden value on a line **without** refutation wording is
reported live `[repo] tools/check-staleness.py:105-107`, and the `REFUTATION`
regex is literally a past-tense detector — `was`, `were`, `previously`,
`supersed\w+`, `refuted?`, `no longer`, `used to`, `earlier`, `old`,
`former\w*`, `instead of`, `rather than`, `wrong`, `incorrect`, `corrected`,
`deleted`, `obsolete`, `historical` `[repo] tools/check-staleness.py:36-41`.

> **D2 and the existing checker are the same rule.** A `notes.md` written in the
> past tense passes automatically. One written in the present tense fails the
> commit hook the moment it restates a figure that has since moved `[repo]
> .claude/settings.json`, `if: "Bash(git commit *)"`. **Zero tool changes.**

The residual hole is honest and worth naming: a value that has **never** moved
is not in any `forbidden` list, so an unrefuted present-tense restatement of it
in `notes.md` passes. That is the same hole every corpus file has — *"A figure
with an empty `forbidden` list… protects nothing"* `[repo]
docs/reference/repo-maintenance.md:55-56` — and `notes.md` makes it no worse.

### 3.4 The ratchet — what stops one decision living in two places

| # | Rule |
|---|---|
| R1 | **An ADR is never summarised.** A page or `notes.md` cites `ADR NNNN` and states no part of its reasoning. |
| R2 | **Promotion is one-way.** If a `notes.md` entry turns out to bind another circuit (D1), it becomes an ADR and the entry is **replaced** by the one-line link — not kept alongside. |
| R3 | **Demotion does not exist.** An ADR is never moved into a `notes.md`; it is marked `Superseded` where it stands `[repo] docs/decisions/README.md:31-33`. |
| R4 | **A correction is written once, in the tense that decides its home.** The present-tense claim goes on the page; the account of what it replaced goes in `notes.md`; neither restates the other's number. |

R4 is the one that would have caught the live defect in §7.

---

## 4. The `Still open` / `TBD` convention

**Answer: per circuit, with a generated central index. Both, but only one is
authored.**

| Why not central-only | Why not per-circuit-only |
|---|---|
| An open item is read by the person drawing that circuit. A central-only file is *"Fixes land where the editing is happening; they do not land where the reader looks"* `[repo] CLAUDE.md:11-12` with the polarity reversed. | The central view already exists and is 8.5 % complete: `ROADMAP.md:224-231` lists **4** items against **47** on the pages (M4, M5). Authoring a second copy is a 47-row staleness surface. |

### 4.1 Rules

| # | Rule | Cost today |
|---|---|---|
| O1 | Exactly one `## Still open` per circuit page, that exact spelling | `breath-output-stage.md:302` uses `## Open before layout` `[repo]` — normalise during the split |
| O2 | `## Still open` contains **only open items**. A closed item moves to `notes.md` under `## Closed`, keeping its date and body | **6** struck-through/`CLOSED` items are squatting there now (M4) |
| O3 | Each item: `- **<title>.** <body> **Decided by:** <token>`, token ∈ ROADMAP gate id (`E9`) \| `datasheets/<path>` \| `figures:<id>` \| `owner's call` | **34 of 47** carry no machine-readable token (M4) |
| O4 | `TBD`/`open` in `bom.csv` fragments keeps its existing rule — say what decides it `[repo] CLAUDE.md:133-135` — and the decider token uses the same vocabulary as O3 | none; 33 rows are already `status=open` `[calc]` |
| O5 | `hardware/OPEN.md` is **generated**. Header names the tool and carries the `repo-maintenance.md` §1 "Generated" banner `[repo]:17` | new tool |

### 4.2 How a reader finds them all at once

`hardware/OPEN.md`, generated from the `## Still open` sections:

```markdown
<!-- GENERATED by tools/collect-open.py — edits here are destroyed. -->

| Decided by | Circuit | Item | Source |
|---|---|---|---|
| E9  | module/pitch-stage | Whether 200 Ω is the right `TRIM-GAIN` | pitch-stage.md:361 |
| E10 | module/pitch-stage | `TRIM-OFFSET` is not buildable as described | pitch-stage.md:351 |
| E10 | module/mod-channels | Whether all four channels need the full ±10 V | mod-channels.md:256 |
| …   | | | |

NO DECIDER (34) — items failing O3, listed with file:line
```

Sorted by decider, so `ROADMAP.md`'s E9 row and the four page items that block
E9 are readable together for the first time.

**Staged enforcement, deliberately not a gate.** The generator *reports* the
`NO DECIDER` count rather than failing. That matches how the staleness hook
behaves — it *surfaces* the result so forgetting is *"visible rather than
silent"* `[repo] CLAUDE.md:41-42` — and it avoids a 34-item edit inside a commit
whose subject is a restructure. New and touched items must carry the token;
untouched ones are counted until they are next edited.

---

## 5. Worked example — `hardware/module/pitch-stage/`

Source: `hardware/module/pitch-stage.md`, 369 lines `[repo]`. Every line range
below is a **move**. The only new text is `## Interfaces` (§2.3) and the
`**Decided by:**` tokens (§4.1 O3).

```
hardware/module/pitch-stage/
├── pitch-stage.md    ~255 lines   (moved from :1-308 minus the history)
├── bom.csv           5 owning + 7 using rows
├── notes.md          ~115 lines   (moved history)
└── sim/
    ├── pitch-load.cir
    └── README.md
```

### 5.1 `pitch-stage.md`

````markdown
# Pitch stage — schematic                                    ← :1 verbatim

**Status:** Drawn 2026-09-21. Second module page, after       ← :3-4 verbatim
[the breath receive stage](../breath-receive-stage/breath-receive-stage.md).
                                                    ↑ M2: one of only 3 such links

## Interfaces                                                 ← NEW (§2.3)

| Node | Dir | Peer | Figure | Note |
|---|---|---|---|---|
| `VREFOUT` | in | `module/digital-and-supervision` | — | Buffered 2.500 V reference; trimmed ahead of the follower |
| `DAC ch1` | in | `module/digital-and-supervision` | `figures:dac-rail` | Through `R-OPAMP-IN` |
| `PITCH` | out | panel jack | `figures:pitch-cents-budget` | Feedback is tapped **here**, not at the op-amp output |
| `±12 V` | in | `module/power-entry` | — | `D-JACK-CLAMP` returns to these |
| `AGND` | ref | `module/power-entry` | `figures:dig-gnd-topology` | `C-AA-PITCH`, `C-FILT-PITCH` shunt to it |

## The circuit                                                ← :11-37 verbatim

```
   VREFOUT ──[TRIM-OFFSET 10k]──┬── ½ OPA2197 ──┬── V_ref ≈ 2.500 V
   … (the existing 25-line ASCII drawing, unchanged) …
```

## It is a non-inverting amplifier, not a difference amplifier   ← :39-64, :87-90
                                                     (:66-85 blockquote → notes.md)

## Why the offset reference must be `VREFOUT` — the arithmetic   ← :92-122 verbatim

## Component values                                            ← :124-155 verbatim
                                    (Value column dropped post-freeze, §1.4)

## DC feedback is tapped at the jack, not at the op-amp output ← :176-179 table,
                                                                 :216-226 ⚠ box,
                                                                 :227-233
                          (:157-175, :181-215 narrative → notes.md)

## The trims still interact one way, and the procedure says so ← :249-260, :266-275
                                                     (:261-264 → notes.md)

## What limits accuracy, in order                              ← :285-308
                              (:279-283 → notes.md; :301-304 → notes.md, §7)

## Still open                                                  ← :351-369
                                    (:312-350 CLOSED item → notes.md, O2)

- **`TRIM-OFFSET` is not buildable as described.** `V_ref` nominal *is*
  `VREFOUT`, and a divider can only go below it… **Decided by:** E10
- **The (+) input has no DC path to ground.** … `R-BIAS-DAC` now does it here
  — at the **DAC pin**… **Decided by:** owner's call
- **Whether 200 Ω is the right `TRIM-GAIN`.** … **Decided by:** E9
- **A two-terminal series trimmer fails open to the rail.** … **Decided by:** M3
- **The two spare LT5400 resistors.** … **Decided by:** owner's call
````

Bodies verbatim from `:351-369`; only the `**Decided by:**` tokens are new, and
three of the five are already stated in the existing prose (`E10`,
`an E9 question`, `a footprint decision`) `[repo] hardware/module/pitch-stage.md:355,364,367`.

### 5.2 `bom.csv` — 5 owned, 7 used

```csv
ref,category,part,manufacturer,description,package,qty,status,source,adr,notes
TRIM-GAIN,module,200R multiturn cermet,,Pitch gain trimmer…,THROUGH-HOLE,1,candidate,,0006,"200R, not 1k…"
TRIM-OFFSET,module,10k multiturn cermet,,Pitch offset trimmer…,THROUGH-HOLE,1,candidate,,0006,"MOVED…"
C-FB-PITCH,module,2.2nF C0G/NP0,,"Compensation cap…",0805 (2.0 x 1.25mm),1,candidate,,0006,"FROM THE OP-AMP OUTPUT…"
C-AA-PITCH,module,10nF C0G/NP0,,"Anti-alias/glitch filter…",0805 (2.0 x 1.25mm),1,candidate,,0006,"THE ACTUAL PITCH FILTER…"
C-FILT-PITCH,module,10nF C0G/NP0,,"Reconstruction and RF shunt…",0805 (2.0 x 1.25mm),1,candidate,,0006,"RESTORED…"
R-OUT-PROT,,,,,,1,uses:module/mod-channels,,,
R-OPAMP-IN,,,,,,1,uses:module/mod-channels,,,
D-JACK-CLAMP,,,,,,1,uses:module/mod-channels,,,
R-BIAS-DAC,,,,,,1,uses:module/mod-channels,,,
U-OPA-PITCH,,,,,,1,uses:module/mod-channels,,,
R-TRIM-RANGE,,,,,,2,uses:module/breath-receive-stage,,,
R-PRECISION,,,,,,1,uses:module/mod-channels,,,
```

All owning rows are `hardware/bom.csv`'s existing rows, unchanged `[repo]`. The
12-row fragment against `hardware/bom.csv`'s 138 rows is the measurement that
justifies the split: **pitch owns 5 parts and borrows 7**, and today nothing in
the corpus says so.

Two consequences worth stating rather than discovering:

- `R-OUT-PROT` is used by **four** circuits `[calc]` (M3), so the B3 sum is
  `1+1+1+1+… = 6` `[repo]` — and the row that records *"the worst case moved
  when pitch took jack-side feedback"* `[repo] hardware/bom.csv, R-OUT-PROT`
  becomes mechanically attributable to pitch's fragment.
- `R-TRIM-RANGE` is `qty 4`, `status=open`, serving `TRIM-OFFSET` **and**
  `TRIM-BREATH-ZERO` `[repo] hardware/bom.csv, R-TRIM-RANGE`. Two circuits, one
  open part. Under O4 its decider token is `E10`, and it appears in
  `hardware/OPEN.md` **once**, not twice.

### 5.3 `notes.md`

```markdown
# Pitch stage — decision history

Past tense only. Live values live in `pitch-stage.md` and `bom.csv`. (§3.2, §3.3)

## The `A = 1 + B` correction                        ← moved from :66-85
> **A correction, because the first version of this page got the reason wrong.**
> It said `A = 1 + B` is a *boundary*… `A = 1 + B` is not a boundary. It is the
> **defining identity** of this topology…

## Two changes prior art forced                      ← moved from :157-175, :181-215
`R-OUT-PROT` divides against whatever is patched in… ADR 0006 accepted that…
**`C-FB-PITCH` is not a filter, and an earlier version of this page said it
was.**…

## The offset trimmer moved ahead of the reference buffer   ← moved from :235-247
The first version put it after, injecting through `R-OFFINJ`… That is true of an
*inverting* summer… `R-OFFINJ` is deleted…

## The trim procedure used to say "trim against the real patch"  ← moved from :261-264
An earlier version of this section said to trim against the real patch because
the 1 kΩ divided against it. That error is gone.

## The 6× accuracy disagreement, and the pivot error  ← moved from :279-283
…both published numbers were wrong. It was a pivot error: `∂Vout/∂k = Vdac −
V_ref`… Three documents used 9 V, 7 V and 2.5 V for the same term.

### The superseded budget table                       ← moved from :301-304, §7
| LT5400 ratio tracking | ~0.1 cents | … |
| DAC internal reference | ~0.5 cents | … |
| OPA2197 offset drift | <0.1 cents | … |
| DAC INL, ±4 LSB typical | ~0.4 cents | … |
**Superseded** by the table in `pitch-stage.md` (0.027 and 0.42 cents).

## Closed                                             ← moved from :312-350 (O2)
### The LT5400 option suffix — CLOSED 2026-09-21
`5400fa.pdf` is banked at `datasheets/other-semi/LT5400.pdf`… **But the package
was wrong, and it is layout-blocking**… **Caveat on the revision.** This is rev
**fa**, not the **fc** `bom.csv` names canonical…
```

Every heading in `notes.md` carries past-tense wording the `REFUTATION` regex
matches — `corrected`, `earlier`, `was`, `old`, `superseded` `[repo]
tools/check-staleness.py:36-41` — so D3 holds mechanically with no tool change.

**One item in that move needs care and I flag it rather than resolve it.** The
`CLOSED` LT5400 block is 38 lines and its last three bullets are not closed at
all: the exposed pad's destination is *"nothing in this corpus says where it
goes… **Decide it with the layout, not after**"* `[repo]
hardware/module/pitch-stage.md:332-334`, and the ±7.5 %/±15 % absolute tolerance
*"sharpens the 'no downward authority' worry"* `[repo]:340-343`. Under O2 the
closed *question* goes to `notes.md`; the two live consequences must be lifted
into `## Still open` as items with `**Decided by:** E9` and `M3`. **This is a
split, not a rewrite** — but it is the one place in the worked example where the
mover has to make a judgement, and it should be done with the owner.

### 5.4 `sim/`

```
sim/pitch-load.cir     the deck
sim/README.md          command, banked-model SHA, date, and where the number went
```

`pcb-pipeline.md:128` names this exact simulation — *"Pitch transient into a
passive mult … Measured 41.8 % overshoot at 82 nF, 65.4 % at 330 nF. **The AC
sweep is structurally blind to this**"* `[repo]` — and `pitch-stage.md:268-271`
already carries the matching claim (*"44–67 % overshoot"*) `[repo]`.

**Note the two figures disagree** (41.8/65.4 vs "44–67"). I am not resolving
that — it is a values question, not a structure question — but it is precisely
what a `sim/` directory is for: the deck that produced one of them becomes
inspectable instead of the page and the pipeline each asserting a number.

`sim/README.md` owns: the invocation, the `.spiceinit` requirement `[repo]
docs/reference/pcb-pipeline.md:50`, the banked `.LIB` path and SHA, and the
sentence *"the result is recorded as `figures:<id>`"*. It states **no number**.

---

## 6. Naming

### 6.1 Directory scheme

```
hardware/<board>/<circuit>/
```

| Level | Rule |
|---|---|
| `<board>` | `module`, `controller` — both already exist `[repo] hardware/module/`, `hardware/controller/` |
| `<circuit>` | lowercase, hyphen-separated, **identical to today's page basename minus `.md`** |
| Split children | `<parent>-<block>`, block name taken from the existing `§` heading |

Keeping existing basenames verbatim is not cosmetic: it is what makes all 39
basename references survive the move untouched (M1, §6.2).

For the split children, from the existing `§` headings `[repo]`:

| From | Directories |
|---|---|
| `carrier.md` §1-§7 | `carrier-power-entry`, `carrier-analog-frontend`, `carrier-chain-drive`, `carrier-spi-egress`, `carrier-led-data`, `carrier-display-loom`, `carrier-mounting` |
| `cluster-boards.md` §1-§5 | `cluster-device`, `cluster-key-network`, `cluster-connectors`, `cluster-bit-allocation`, `cluster-mechanical` |
| `breath-output-stage.md` (second H1 at :169) | `breath-output-stage`, `breath-response-control` |

**Cost, stated:** these 14 names are new, so references to `carrier.md` (7
`[calc]` from M1's breakdown) and `cluster-boards.md` (3) must be re-pointed by
hand. That is 10 of the 39. The other 29 point at pages that split into exactly
one directory and do not move.

### 6.2 `README.md` or `<circuit>.md`? — **`<circuit>.md`**

`hardware/module/pitch-stage/pitch-stage.md`.

**The case for `README.md`, stated fairly first.** GitHub auto-renders
`README.md` below a directory listing, so opening
`hardware/module/pitch-stage/` would show the schematic immediately instead of a
four-line file list plus a click. For a repository whose schematics are read far
more often than edited, that is a real benefit and it is the strongest argument
on that side.

**It loses on three counts:**

| # | Argument |
|---|---|
| N1 | **All 39 references are bare basenames** (M1). `` `power-entry.md` `` carries no path, so a *move* leaves all 39 literally correct; a *rename* to `README.md` invalidates every one and, worse, makes them ambiguous — there would be ~15 files named `README.md` under `hardware/`. The content freeze permits moves. It does not permit 39 text edits in the restructure commit. |
| N2 | **`README.md` already means "index of this directory"** in this corpus: `docs/decisions/README.md` is the ADR index `[repo]:36-54`, `datasheets/README.md` `[repo]`, `firmware/README.md` `[repo]`, and each review wave's `README.md` *"states its method"* `[repo] CLAUDE.md:91`. A 369-line schematic is not an index. Overloading a working convention to gain one click is a bad trade. |
| N3 | **Fifteen open editor tabs all called `README.md`.** `grep -n 'C-FB-PITCH' hardware/**/README.md` returns paths whose last segment carries no information. This is small and constant, and it is paid on every single lookup. |

**The compromise I considered and reject:** a short `README.md` stub in each
circuit directory linking the four files. It would have to say what the circuit
*is* in one line — and that line is a fact, in a fifteenth file, that can go
stale. In this repository that is not a neutral cost. If the browsing benefit
is judged decisive by the owner, the stub is the right shape — but it must be
**links only, no descriptive sentence**, or it becomes a sixteenth staleness
surface.

### 6.3 Other names

| Name | Rule |
|---|---|
| `bom.csv` | Same basename in every circuit directory. It is unambiguous under `<board>/<circuit>/`, and it keeps the fragment→generated relationship visually parallel to `hardware/bom.csv`. |
| `notes.md` | Owner's name, kept. `decisions.md` would invite confusion with `docs/decisions/`, which is exactly the boundary §3 is drawing. |
| `sim/` | Directory, §1.2. |
| `hardware/OPEN.md` | Capitalised like `MANIFEST.csv` — this corpus capitalises generated files `[repo] datasheets/MANIFEST.csv`. |
| `hardware/unplaced.csv` | The 50 orphan rows (M3). Lowercase: it is authored, not generated. |

---

## 7. A live defect found while reading the worked example

Not my slice; reporting because it is in the exact text the split moves.

**`hardware/module/pitch-stage.md:301-304` is a superseded accuracy table left
in place, with no header row, after the paragraph that replaced it.**

`[repo]` The live table at `:285-289` gives:

| Term | Over 10 °C |
|---|---|
| DAC internal reference | **0.42 cents** |
| LT5400 ratio tracking | **0.027 cents** |

Lines `:301-304` are four orphaned `|`-rows, following two prose paragraphs and
preceded by no header, giving **~0.5 cents** for the DAC reference and **~0.1
cents** for LT5400 ratio tracking — different numbers for the same two terms, in
the same section, on the same page `[repo] hardware/module/pitch-stage.md:301-302`.

`:279-283` states that this table *was* corrected: *"The 6× disagreement this
table used to flag is resolved, and **both published numbers were wrong**"*
`[repo]`. The correction landed; the old rows did not get deleted.

- **The checker cannot see it.** Neither figure is in `config/figures.yaml`
  `[calc]` — no `forbidden` entry, so no hit. This is the documented hole: *"A
  figure with an empty `forbidden` list… protects nothing"* `[repo]
  docs/reference/repo-maintenance.md:55-56`.
- **Rule R4 (§3.4) is what would have caught it**, and §5.3 shows where the rows
  belong: `notes.md`, under an explicit `**Superseded**` line.
- **Recommendation:** move, do not delete. It is a real superseded value and
  `notes.md` is the shelf for it.

---

## 8. What this standard makes harder

Stated plainly, because a standard that only lists benefits has not been thought
through.

| # | Harder | Size | Mitigation |
|---|---|---|---|
| H1 | **`figures.yaml`'s 21 hardware `owner:` paths all go stale, silently.** `owner:` is free text the checker never reads `[repo] tools/check-staleness.py:61-108` (M11). Nothing fails. | 21 paths, 17 `.md` + 4 `bom.csv` | Add an `owner:`-path-exists assertion to the checker **in the restructure commit**. Three lines. Without it the restructure quietly creates 21 instances of the project's named failure mode. |
| H2 | **Reading one circuit end to end now takes 3-4 files.** A pitch question that used to be one `grep` in one file is now the page + the fragment + possibly `notes.md`. | every read | Real, and partly the point — but it is a cost paid on every read against a benefit paid at every edit. Adjacency inside one directory is what makes it tolerable. |
| H3 | **Two more places to put a decision means two more chances to put it in the wrong one.** D1/D2/D3 are rules; rules get applied by tired people. | ongoing | D3 is the only one with mechanical backing. D1 and D2 are review-wave material — the semantic half the checker cannot reach `[repo] CLAUDE.md:68-75`. |
| H4 | **`carrier.md` and `cluster-boards.md` fragment into 12 directories, and 10 of the 39 basename references must be re-pointed by hand.** | 10 edits | Unavoidable: a genuine split renames things. The other 29 references are protected by §6.2 N1. |
| H5 | **Stale-BOM-value reports double.** A forbidden value in both a fragment and the generated `hardware/bom.csv` is found twice (M8, §1.3). | noise | Pre-announce it in `repo-maintenance.md`, or teach the checker to skip generated files. |
| H6 | **Fragments are unvalidated until `check_bom()` is extended** (M9). A 10-column or duplicate-refdes fragment is not caught today. | correctness hole | Extend `check_bom()` to `hardware/**/bom.csv` in the same commit. |
| H7 | **Provenance markers are a real gap, not a formality.** Six of eight pages have essentially none (M6); `pitch-stage.md` has zero against ~30 derived numbers. | ~150 markers | Stage it: required on new and touched derivations, counted elsewhere — the same staging as O3. |
| H8 | **`## Interfaces` is new content inside a content freeze.** Five rows × ~20 circuits ≈ 100 new assertions, each of which can be wrong. | ~100 rows | The split *creates* these boundaries (§2.3), so the content is genuinely new rather than restated. Every quantity in the table must be a `figures:<id>` citation, never a number — that caps the staleness exposure at the identifier level. |
| H9 | **`hardware/OPEN.md` becomes a fourth generated file** and inherits the `MANIFEST.csv` trap: *"A direct edit… survives until the next run of that tool and then disappears without a word"* `[repo] CLAUDE.md:61-64`. | one trap | Banner at the top of the generated file; a row in `repo-maintenance.md` §1's "Generated" table. |
| H10 | **The value-column duplication survives the restructure.** §1.4 defers it past the freeze. Anyone reading the standard and then the tree will find the rule not yet applied. | 8 tables | Say so in the restructure commit message, and land it circuit-by-circuit afterwards. |

**The one I would not accept without a fix is H1.** It is the project's named
failure mode, created by this restructure, invisible to every existing check,
and closed by three lines in `check-staleness.py`.

---

## 9. Summary of what implementation agents copy

1. `hardware/<board>/<circuit>/` — §6.1, basenames unchanged from today (§6.2 N1).
2. `<circuit>.md` skeleton — §2.4. Required: H1, `**Status:**`, `## Interfaces`,
   `## The circuit`, `## Component values`, `## Still open`.
3. `bom.csv` fragment — §1.3. Owning rows full; using rows are
   `ref,qty,status=uses:<board>/<circuit>` and nothing else. `qty` is
   per-circuit. 50 orphans to `hardware/unplaced.csv`.
4. `notes.md` — past tense only, §3.2. Every closed item lands here (O2).
5. `sim/` — deck + invocation, never a number (§1.2, §5.4).
6. Decision boundary — blast radius, then tense, then the ratchet (§3).
7. Open items — in the page, indexed by `hardware/OPEN.md` (§4).
8. Same-commit tool work: `owner:` path assertion (H1), `check_bom()` over
   `hardware/**/bom.csv` (H6), `tools/collect-open.py` (O5).
