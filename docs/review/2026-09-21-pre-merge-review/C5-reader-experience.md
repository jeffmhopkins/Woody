# C5 — Reader experience: can someone who has never seen this repository use it?

**Slice:** newcomer journeys against the restructure branch
(`claude/codebase-restructure-thp3ek`), 2026-09-21.
**Method:** I opened `README.md` and followed only the links it offers, then ran
each of the documented procedures end to end. Where a procedure had to be
executed to know whether it works, I ran it in a throwaway copy of the tree at
`/tmp/.../scratchpad/sand`, never in the working tree. Nothing under
`docs/review/**` was read.

**Provenance marks:** `[repo] path:line` — read in this tree. `[run]` — a
command executed, with its output quoted. `[calc]` — arithmetic shown.
`[from memory]` — unverified background.

---

## Summary — the worst five

1. **The whole of `hardware/` is unreachable by following links from
   `README.md`.** `hardware/README.md` — the map the restructure exists to
   provide — has **zero inbound links from anywhere in the repository**
   `[run]`. `README.md` links five things and none of them is a board page
   `[repo] README.md:15,89-90,122-124`. A newcomer asking "where is the breath
   circuit?" or "where is the DAC?" cannot get there by reading; they have to
   guess that `hardware/` has a README, or grep. (F1)

2. **A newcomer can change a resistor by the documented procedure, run every
   tool the documentation names, get `PASS`, and leave the corpus stating two
   different values.** I changed `R-SPI-SER` from 100R to 220R in its fragment,
   ran `merge-bom.py` then `check-staleness.py`, and got
   `PASS no live stale values` — while `config/figures.yaml` and the owner page
   both still say 100 Ω, and 220 Ω is the value the figure's own derivation
   exists to reject `[run]`. Nothing compares a BOM row against the figures
   register, and no document tells you to check whether a part value is
   tracked before editing it. This is the project's named failure mode,
   reachable by following the rules. (F2)

3. **`ROADMAP.md`'s E12 milestone is one panel revision stale, and the checker
   files the stale text as a correction.** E12 reads "good practice at 8HP"
   where ADR 0004 reads "At 10HP this is good practice"
   `[repo] ROADMAP.md:53`, `[repo] docs/decisions/0004-cv-interface-module.md:830`.
   It escapes twice: no `forbidden` pattern matches that spelling, and when I
   added one the checker classified the hit as *"old values present but refuted
   in place — OK, this is how a correction reads"*, because the same table cell
   contains "it **was** at 6HP" `[run]`. (F3)

4. **`CLAUDE.md` says three review waves have run; there are nine directories
   plus a loose file, and for two of the three it names, the file it promises
   is absent.** `[repo] CLAUDE.md:92-96`, `[run]`. `README.md` says seven
   `[repo] README.md:117`. There is no `docs/review/README.md` index. CLAUDE.md
   also tells the reader to consult `docs/review/<wave>/STATUS.md`
   `[repo] CLAUDE.md:125` — the two waves that have one are not among the three
   it names `[run]`. (F4)

5. **Two entry points still describe a body that is bonded shut**, a premise
   ADR 0009 and `ROADMAP.md` itself explicitly retired
   `[repo] firmware/README.md:88`, `[repo] ROADMAP.md:207` vs
   `[repo] ROADMAP.md:78,102`. In `firmware/README.md` it is the stated
   justification for the entire recovery section — `CLAUDE.md` §5's "an argument
   survives its own refutation", in the corpus, today. (F8)

---

## Findings

Indexed by the task the reader was trying to do.

### F1 — Task: "What is this project, and where is the hardware?" — `hardware/` is link-unreachable from `README.md`

`README.md` offers exactly five link targets: the 2021 project on GitHub,
`ROADMAP.md`, `LICENSE`, `docs/decisions/0011-licensing.md`, and the three
"Where to start reading" entries (`ROADMAP.md`, `docs/decisions/`,
`docs/reference/latency-budget.md`) `[repo] README.md:8,15,89-90,122-124`.

The "Repository layout" block `[repo] README.md:93-113` names `hardware/` but
it is a fenced code block — no link `[repo] README.md:102-108`.

Transitive closure from `README.md`:

- `ROADMAP.md` links only into `docs/decisions/` and `docs/reference/` — **zero
  links into `hardware/`** `[run]`.
- `docs/reference/latency-budget.md` has one outbound link, to ADR 0013
  `[run]` — a leaf.
- Of the fourteen ADRs, four lines link into `hardware/`, all of them deep
  inside long documents and all landing on leaf circuit pages, never on a board
  page or the hardware index: `[repo] docs/decisions/0003-breath-sensing-path.md:397`,
  `[repo] docs/decisions/0006-cv-channel-allocation.md:83,84,373`, plus
  `carrier.md`/`cluster-boards.md` from
  `[repo] docs/decisions/0001-mcu-and-board-partitioning.md` `[run]`.

Inbound-link count, whole corpus excluding `docs/review/**` `[run]`:

| Page | Inbound links |
|---|---|
| `hardware/README.md` | **0** |
| `hardware/module/module.md` | 2, both from inside `hardware/` |
| `hardware/interfaces/README.md` | 2, both from inside `hardware/` |
| `hardware/carrier/carrier.md` | 1 external (ADR 0001) |
| `hardware/cluster/cluster-boards.md` | 1 external (ADR 0001) |

**Where the reader gets stuck and what they conclude:** they finish `README.md`
believing the repository is decision records plus a roadmap, and that the
schematics are "somewhere under `hardware/`" in a shape described only by a
three-line code block. `hardware/README.md` — which contains the board table,
the generated-file warning and the directory contract — is never offered. The
restructure's central artefact is invisible to the reading path.

**What would settle it:** nothing; the link graph is mechanical. The fix is one
line in `README.md`'s "Where to start reading".

### F2 — Task: "I want to change one resistor value" — the documented procedure passes green while leaving the corpus inconsistent

I followed the procedure as written. `CLAUDE.md`'s Hardware conventions and
`docs/reference/repo-maintenance.md` §4 both say: edit the fragment, re-run
`merge-bom.py`, and the hook will catch a hand edit
`[repo] CLAUDE.md:135-146`, `[repo] docs/reference/repo-maintenance.md:120-140`.

**Step 0 is missing: nothing tells you which fragment holds the row.** There is
no refdes → fragment index. `merge-bom.py` builds one internally
(`seen[r[0]] = f"{rel}:{i}"` `[repo] tools/merge-bom.py:120`) and never prints
it. I found `R-SPI-SER` by grepping 24 fragments `[run]`.

**Steps 1–2 work, loudly.** Editing the fragment and *not* re-running the tool
fails with a precise message `[run]`:

```
hardware/bom.csv does not match its fragments, first difference at line 45.
It is GENERATED - edit the fragment, not the master, then re-run this tool
```

**Step 3 is where it breaks.** After `merge-bom.py`, every documented check
passes `[run]`:

```
bom.csv: wrote 138 rows from 24 fragments | 0 problems
PASS no live stale values | corpus 121 files, 23 circuits | 5 unresolved (tracked)
```

At that moment the tree says, simultaneously:

- `hardware/bom.csv` / `hardware/interfaces/spi-link/bom.csv`: `220R 1%`
- `config/figures.yaml`: `spi-series-r` `value: "100 ohm, R-SPI-SER, qty 3"`
  `[repo] config/figures.yaml:210-216`
- `hardware/interfaces/spi-link/spi-link.md:54,61`: "**All three are
  `R-SPI-SER`, and the value is 100 Ω**" and "**The value is 100 Ω, not 220**"

The reason is structural, not a bug: `check_owners` verifies that the *owner
document* states the register's value, matching the longest numeric token
`[repo] tools/check-staleness.py:475-538`. The register and the owner still
agree with each other. **Nothing in the toolchain relates a `bom.csv` row to the
figure that governs it**, and no document adds "check `config/figures.yaml`
first" to the BOM-edit procedure. The `forbidden` mechanism cannot help either:
it lists spellings a value *used to* have, so a newly-introduced wrong value is
invisible to it by construction.

**What the reader concludes:** "the tooling checks this, and it passed." That
is the most expensive possible conclusion in this repository.

**What would settle the scope of it:** a count of how many of the 35 register
entries have a value that also appears as a BOM field. From inspection at least
`spi-series-r`, `key-pullup-qty`, `panel-toggle-hole`, `loadswitch-timer`,
`loadswitch-gate-cap`, `loadswitch-fb-divider`, `pitch-compensation`,
`plate-thickness` and `ref5050-grade` are in that class `[repo] config/figures.yaml`.

#### F2b — Two tracked figures name a GENERATED file as their owner

`key-pullup-qty`, `panel-toggle-hole` and `ref5050-grade` all carry
`owner: hardware/bom.csv` `[repo] config/figures.yaml:206,309` and and the
`ref5050-grade` entry `[run]`. `CLAUDE.md` §2 step 1 and
`repo-maintenance.md` §5 both say to update the owner
`[repo] CLAUDE.md:50-58`, `[repo] docs/reference/repo-maintenance.md:186-192`.
The owner is a file both documents elsewhere describe as silently destroying
edits `[repo] docs/reference/repo-maintenance.md:120-140`.

A newcomer doing exactly what §5 says will edit `hardware/bom.csv`. They are
rescued — `merge-bom --check` fails loudly — but only after the fact, and
neither §5 nor the register entries warn that an owner may be generated.

### F3 — Task: "What do I do next?" — `ROADMAP.md` E12 is stale, and the refutation heuristic hides it

`[repo] ROADMAP.md:53`:

> E12 | Module PCB + panel | 10HP panel cut, module assembled and racked.
> etherCON braced to the PCB — good practice **at 8HP** rather than the
> structural necessity it was at 6HP.

`[repo] docs/decisions/0004-cv-interface-module.md:830`:

> At **10HP** this is good practice rather than a structural necessity.

The row states the current panel width and the superseded one in the same
sentence. Two independent escapes, both verified:

1. `panel-width`'s `forbidden` list is
   `["panel is 40.34 mm", "The panel is 8HP", "inside 8HP", "at 8HP this",
   "Comfortable at 8HP"]` `[repo] config/figures.yaml:276`. The ROADMAP
   spelling is `at 8HP rather` — missed by one word, which is precisely the
   mechanism `repo-maintenance.md` §2 documents as the fourth recorded
   instance `[repo] docs/reference/repo-maintenance.md:46-63`.
2. I added `"at 8HP rather"` to the list in the scratch copy and re-ran. The
   checker found it and **filed it as refuted** `[run]`:

```
old values present but refuted in place (60) - OK, this is how a correction reads
  ROADMAP.md:53  [panel-width] 'at 8HP rather'
```

Because `REFUTATION` matches per-line context `[repo] tools/check-staleness.py:62-67,176-182`
and the cell contains "it **was** at 6HP", a refutation of a *different* number
launders the live one. This is a class of escape not described in
`repo-maintenance.md` §2's list of things the checker will not catch, and it is
not obvious from reading the tool.

**What the reader concludes:** planning E12, that the etherCON brace is
optional-ish at the module's width. The conclusion happens to survive, but the
number they will quote onward is wrong.

#### F3b — `ROADMAP.md` contradicts `hardware/cluster/bom.csv` on the plate cutout, and the page it cites leads with the superseded value

`[repo] ROADMAP.md:71` (M1): "**Cutout is 14.0 × 14.0 mm**, measured from a
working KS-33 build ([reference](docs/reference/ks33-geometry.md)) … Test coupon
cut at ±0.1mm around 14.0".

`PLATE-TOP` in `hardware/cluster/bom.csv` says the vendor drawing is banked and
"The cutout is CONFIRMED and TIGHTENED: 14.00 +0.05/-0.02 x 14.00 +0.05/-0.02,
**not a bare 14.0 x 14.0**" `[run]`.

The page M1 links opens with **"Source: measured out of `ianmaclarty/ik` … not a
datasheet"** and "[Gateron's datasheet and STEP model] are unreachable from this
project's sandbox" `[repo] docs/reference/ks33-geometry.md:3-10`, and its
section heading is still `## Plate cutout: 14.0 × 14.0 mm`
`[repo] docs/reference/ks33-geometry.md:12`. The correction — vendor drawing
banked, plate 1.20 mm, cutout tightened — is 45 lines further down inside a
blockquote `[repo] docs/reference/ks33-geometry.md:42-59`, and the drawing is in
fact in the repository at
`datasheets/mechanical/GATERON-KS-33-VENDOR-SPEC-DRAWING.pdf` `[run]`.

**Where the reader gets stuck:** they act on M1, open the cited reference, read
the first ten lines and the section heading, and cut a test coupon around a
tolerance the BOM says is superseded — and believe the vendor drawing cannot be
obtained while it sits in the tree.

### F4 — Task: "How much review has this had, and what landed?" — the two entry points disagree with each other and with the tree

| Source | Claim |
|---|---|
| `[repo] CLAUDE.md:92-96` | "**Three have run**" — names cold-review, hardware-and-standards-review, staleness-sweep |
| `[repo] README.md:117` | "`docs/review/` is **seven waves**" |
| `[run]` `ls -d docs/review/*/` | **nine directories** plus `2026-09-20-analog-design-review.md` |

CLAUDE.md continues: "Each directory's `README.md` states its method;
`VERIFIED.md` records what was checked by hand." Measured `[run]`:

| Wave | README | VERIFIED | STATUS |
|---|---|---|---|
| `2026-09-20-cold-review/` *(named by CLAUDE.md)* | yes | **no** | no |
| `2026-09-21-hardware-and-standards-review/` *(named)* | yes | yes | no |
| `2026-09-21-staleness-sweep/` *(named)* | **no** | yes | no |
| `2026-09-21-datasheet-reconciliation/` | yes | yes | no |
| `2026-09-21-pcb-pipeline-review/` | yes | yes | no |
| `2026-09-21-preflight/` | yes | yes | **yes** |
| `2026-09-21-restructure-design/` | yes | yes | **yes** |
| `2026-09-21-schematic-review/` | **no** | **no** | no |
| `2026-09-21-pre-merge-review/` *(this wave)* | yes | yes | no |

So: for two of the three waves CLAUDE.md names, the file it says each directory
has is missing; six waves it does not mention exist; and `CLAUDE.md:125`'s
pointer to `STATUS.md` ("what that wave produced versus what actually landed")
points at a file that exists only in two waves, **neither of which CLAUDE.md
names**. There is no `docs/review/README.md` index `[run]`.

**What the reader concludes:** that three waves have run and that everything in
`docs/review/` is covered by the method CLAUDE.md describes. Both false, and the
second is the dangerous one — CLAUDE.md's own warning that "a wave with thirteen
reports and four landed slices looks finished from the outside and is not"
applies to waves it does not tell the reader to look at.

### F5 — Task: "Add a new tracked figure" / "Add a new circuit" — neither procedure is written anywhere

`grep` across the corpus for `new figure|add a figure|adding a figure|new
circuit|add a circuit` returns exactly one hit, inside a Python docstring
`[run]` — `tools/merge-bom.py:23`, "Adding a circuit …".

**Adding a figure.** `CLAUDE.md` §2 and `repo-maintenance.md` §5 document
*changing* one `[repo] CLAUDE.md:48-70`, `[repo] docs/reference/repo-maintenance.md:182-206`.
Neither states the required fields. `repo-maintenance.md:194` says "Fields in
use **beyond the documented ones**" and lists the optional ones — but there is
no document that documents the base ones. `config/figures.yaml`'s own header
states four rules and a `STATUS` legend, not a schema
`[repo] config/figures.yaml:1-21`.

I wrote the minimal entry a newcomer would write (`id`, `quantity`, `value`) in
the scratch copy. Result `[run]`:

```
Traceback (most recent call last):
  ...
    unresolved = [f for f in spec["figures"] if f["status"] in ("disputed", "blocked")]
KeyError: 'status'
```

Exit 1, so a commit is blocked, and the `PreToolUse` hook does translate a
crash into `CHECKER CRASHED (exit N) …` `[repo] .claude/settings.json`. But the
message a human sees is a `KeyError`, and nothing anywhere says `status` and
`owner` are mandatory or that `owner` must be a file that literally restates the
value.

**Adding a circuit.** A fragment on disk that `ORDER` does not name is caught
with a good message `[run]`:

```
hardware/module/new-thing/bom.csv exists but is not in ORDER in tools/merge-bom.py
 - it would be silently dropped
```

But **that a new circuit requires editing a hand-written list in a Python file
is stated only in that file's docstring** `[repo] tools/merge-bom.py:23-27`.
`hardware/README.md`, `CLAUDE.md` and `repo-maintenance.md` §4 all describe the
fragment→master relationship without mentioning `ORDER`. Nor does anything
document the `circuit.yaml` schema: the `depends_on` type prefixes
(`adr:`/`circuit:`/`fig:`/`refdes:`/`node:`) and the `id`-must-match-directory
rule exist only in `tools/check-staleness.py:333-385`
`[repo] tools/check-staleness.py:357-385`, and `hardware/README.md:12` describes
the file in four words.

Note also that `node:` edges resolve against a `provides:` key
`[repo] tools/check-staleness.py:349-351,381-383` — **no `circuit.yaml` in the
tree has a `provides:` key and none uses a `node:` edge** `[run]`; the four keys
actually used are `id`, `title`, `last_reviewed`, `depends_on`, in all 23 files
`[run]`. A newcomer reading the tool to learn the schema will implement half of
it against dead code.

### F6 — Entry-point audit: `hardware/README.md` describes a tree slightly different from the one on disk

`hardware/README.md` is otherwise the best page in the repository (see "What
works"). Three concrete mismatches:

1. **`sim/` — "an ngspice deck and its contract. No results"**
   `[repo] hardware/README.md:14`. Five `sim/` directories exist and **every one
   contains only `README.md`** `[run]`. No deck exists anywhere. The pages
   themselves say "This directory holds the deck and the procedure"
   `[repo] hardware/module/pitch-stage/sim/README.md:3` — it holds a
   description of the deck that should be written. A reader opening `sim/`
   expecting a `.cir`/`.sp` finds prose.
2. **Board-level `bom.csv` fragments are undocumented.** The diagram shows
   `bom.csv` only at `<board>/<circuit>/` `[repo] hardware/README.md:8-14`, but
   `hardware/carrier/bom.csv`, `hardware/cluster/bom.csv` and
   `hardware/module/bom.csv` exist and are in `ORDER`
   `[repo] tools/merge-bom.py:45-71` `[run]`. They hold the board-level parts
   (`PCB-CARRIER`, `PLATE-TOP`, `R-OUT-PROT`, …) `[run]`. A newcomer told "a row
   lives with the circuit whose page derives its value" has no slot for a part
   no circuit derives, and the diagram gives them none.
3. **The `<circuit>.md` naming rule has three exceptions at board level.** The
   contract is `<board>/<circuit>/<circuit>.md` `[repo] hardware/README.md:8`,
   but the board-level pages are `carrier/carrier.md`,
   `cluster/cluster-boards.md` (basename ≠ directory), `module/module.md` and
   `interfaces/README.md` (a fourth convention) `[run]`. Following the table's
   links works; guessing a path does not.

### F7 — "23 circuits" overstates what exists by at least three

`hardware/README.md:19-22` totals 5 + 3 + 12 + 3 = 23, and
`check-staleness.py` prints `23 circuits` on every run `[run]`. Three of them
are not circuits in the sense a newcomer assumes:

- `module/panel/panel.md:3` — "**A board-level page, not a circuit**, so it
  carries no `## Interfaces` table" `[repo]`. It has a `circuit.yaml` with
  `id: module/panel` anyway `[run]`.
- `module/link-supervision/link-supervision.md:3` — "**NOT FITTED. Nothing in
  this directory is on the board.** … There is no circuit to draw here and no
  part to buy" `[repo]`.
- `module/breath-response-shaper/breath-response-shaper.md:9` — "**Proposed
  2026-09-21.**" `[repo]`.

`module.md`'s table flags "**Not fitted.**" for one of them
`[repo] hardware/module/module.md:18`, but `hardware/README.md`'s count and the
checker's headline number do not, and the directory names carry no marker.

Related: `breath-response-shaper.md`'s own `#` heading is
**"§4 Response control"** `[repo] hardware/module/breath-response-shaper/breath-response-shaper.md:1`
— a section number inherited from a page it no longer lives in. A reader
arriving from `module.md`'s table sees a page titled §4 with no §1–§3.

### F8 — Superseded premises surviving in two entry points

**`firmware/README.md:88`:** "**The body is bonded.** Everything here exists
because a failed flash cannot be answered by opening the instrument." `[repo]`

Refuted three ways in the corpus:
`[repo] ROADMAP.md:78` — "The body is no longer bonded shut — it closes on six
fasteners onto an RTV gasket, ADR 0009";
`[repo] ROADMAP.md:102` — "when the body became serviceable (ADR 0009)";
`[repo] docs/decisions/0009-enclosure-construction.md:493-494` — "The body is
not bonded shut any more".

This is not cosmetic: it is the stated justification for the whole "The
instrument must stay recoverable" section, and that section's own third
recovery rung is "The console header under the service cover (ADR 0009)"
`[repo] firmware/README.md:99-101` — a header that exists *because* the body
opens. The argument and its refutation are eleven lines apart on one page.

**`ROADMAP.md:207`:** "both inform wiring and plumbing that get sealed inside a
**bonded body** at M6" `[repo]` — four lines after a row that says the loom test
must run "while the body is still openable" `[repo] ROADMAP.md:203`.

Neither is reachable by `check-staleness.py`: "bonded" is not a value.

### F9 — "Cite, do not restate" is not followed by the document `README.md` sends the reader to first

`CLAUDE.md` §1 and `hardware/README.md:32-38` both state the rule as absolute
`[repo]`. `README.md` obeys it — it restates none of the 35 register values I
sampled `[run]`. `ROADMAP.md` does not: it restates `dac-rail` ("5.21V",
`[repo] ROADMAP.md:47`), `panel-width` ("50.50 mm", `[repo] ROADMAP.md:190`),
`plate-thickness` ("1.20 mm", `[repo] ROADMAP.md:228`) and the SPI rate
("2 MHz", `[repo] ROADMAP.md:52`) `[run]`.

**What the reader concludes:** that restating a number is normal, because the
second document they read does it four times. There is no notation that
distinguishes a citation from a restatement — `hardware/**` pages use an
`## Interfaces` table with a `Figure` column
`[repo] hardware/module/dac8568/dac8568.md:14-24`, but nothing outside
`hardware/` uses any marker at all, and the convention is never described as a
notation the reader should imitate.

### F10 — "What is open?" has two disjoint answers

`ROADMAP.md`'s "Open items blocking work" table has **four** rows
`[repo] ROADMAP.md:224-231`. `check-staleness.py` prints
`5 unresolved (tracked)` on every run `[run]`, and those five are
`breath-working-point`, `pitch-cents-budget`, `dig-gnd-topology`,
`matrix-led-current`, `ref5050-grade` `[run]`.

**The two sets do not intersect.** Three of the register's five block named
ROADMAP milestones by their own `decided_by` text — `dig-gnd-topology` is
"upstream" of the 2-layer/4-layer choice that E12 lays out,
`matrix-led-current` is "A BENCH MEASUREMENT AT E1", `breath-working-point` is
"M1, with a player and a manometer" `[run]`. None appears in the ROADMAP table,
and nothing in `ROADMAP.md` links to `config/figures.yaml` `[run]`.

**Where the reader gets stuck:** they ask "what is blocked?", get four answers
from the roadmap, and never learn that the register carries five more that gate
the same milestones.

### F11 — The safety net the documentation promises does not exist for a human contributor

`CLAUDE.md:62-64`: "A `PreToolUse` hook runs the checker before every
`git commit`, so forgetting step 3 is visible rather than silent." `[repo]`
`repo-maintenance.md:30`: "Run by a `PreToolUse` hook before every `git commit`"
`[repo]`. `repo-maintenance.md:134`: "`check-staleness.py` runs it, so **the
commit hook** fails on a hand edit." `[repo]`

Measured `[run]`: `.git/hooks/` contains only `*.sample`; there is no
`pre-commit`; `core.hooksPath` is unset; there is no `.github/` directory and no
CI. The only hook is the Claude Code `PreToolUse` entry in
`.claude/settings.json`, gated on `if: "Bash(git commit *)"` `[repo]`.

**What the reader concludes:** "commits are checked." A human cloning this
repository and running `git commit` in a terminal gets no check of any kind, and
nothing tells them to install one. The phrase "the commit hook" is doing work it
cannot do outside an agent session.

### F12 — `repo-maintenance.md` §7's path map cannot answer the question §7 says it answers

§7: "**`path-map-2026-09-21.csv` … maps every old path to its new one** — every
tracked file has a row, including the ones that did not move, because the
question a reader actually asks is 'did this path change?'"
`[repo] docs/reference/repo-maintenance.md:218-222`.

Measured `[run]`: 288 rows — 126 `unmoved`, 150 `unmoved-history`, **8 `moved`**,
3 `deleted`. The eight moves are all labelled "Phase A1". **116 currently-tracked
files do not appear as a `new` path in the map at all**, including
`hardware/README.md`, every one of the twenty circuit directories created by the
Phase B splits, and the map file itself `[run]`.

The consequence is sharper than the count. The map has one row for
`hardware/module/digital-and-supervision.md → hardware/module/digital-and-supervision/digital-and-supervision.md`
`[run]`. That file was subsequently split three ways: the DAC half is now
`module/dac8568/` ("Split out of `../digital-and-supervision/digital-and-supervision.md`
on 2026-09-21" `[repo] hardware/module/dac8568/dac8568.md:3-6`) and the
watchdog/presence half is now `module/link-supervision/` ("Moved verbatim from
`../digital-and-supervision/digital-and-supervision.md`"
`[repo] hardware/module/link-supervision/link-supervision.md:10-12`). A reader
resolving a historical reference to the watchdog through the map lands in the
file that no longer contains it, with no indication that it moved again.

**What would settle it:** whether Phase B moves were deliberately excluded. If
so, §7's sentence needs to say "as of Phase A1", because as written it promises
file-granularity coverage the reader will apply at content granularity.

### F13 — `hardware/unplaced.csv` is defined to the reader as something it is not

Three entry points define it identically: "a count of parts nobody has drawn"
`[repo] CLAUDE.md:143`; "the BOM rows **no schematic page names** … a part
nobody has drawn" `[repo] hardware/README.md:42-45`; "the 50 rows of 138 that no
schematic page names … a part nobody has drawn"
`[repo] docs/reference/repo-maintenance.md:130-136`.

The file's 50 rows include `U-DAC` (DAC8568CIPW), `U-DIFFRX` (INA828),
`U-REG-DAC` (LM317LZ), `J-CV`, `J-UMBILICAL`, `C-TIMER-LOADSW`,
`C-GATE-LOADSW` `[run]`. All of those parts **are** drawn:
`DAC8568` appears on six hardware pages including a dedicated one,
`INA828` on seven, `LM317` on seven, `etherCON` on five, `LT1641` on six
`[run]`. What is true is narrower — no page names them **by reference
designator**; `grep` for each of those refdes across all `.md` returns nothing
`[run]`.

`module.md` states the real situation honestly — "`hardware/unplaced.csv` holds
this board's principal ICs — the DAC, the in-amp, the LM317 — because BOM
assignment matched on reference designator and these are drawn by part number"
`[repo] hardware/module/module.md:37-40`. The three entry points do not, and
`module.md` is reachable only from `hardware/README.md`, which is reachable from
nothing (F1).

**What the reader concludes:** that fifty parts have no schematic. The number of
genuinely undrawn parts is smaller and nobody states it.

### F14 — `carrier.md`'s block diagram labels six sections; the page has four, and the checker is designed not to notice

`hardware/carrier/carrier.md`'s block diagram — the first thing on the page —
labels blocks `§1` POWER ENTRY, `§2` ANALOG FRONT END, `§3` CHAIN DRIVE, `§4`
SPI EGRESS, `§5` '125 LED data, `§6` J-DISP `[repo] hardware/carrier/carrier.md:39-87`.
The page's headings are `§2`, `§3`, `§4`, `§7` `[run]`.

The pointers exist but not as headings: `§1` in an italic line at
`[repo] hardware/carrier/carrier.md:83-86`, `§5` and `§6` in one italic
paragraph at `[repo] hardware/carrier/carrier.md:231-236`. A reader using the
rendered heading list (GitHub's outline sidebar) sees a page that skips from §4
to §7 and never learns where §5 and §6 went.

`check_sections` exists for exactly this class of defect but **skips
self-references by design**: `if target == os.path.basename(path): continue`
`[repo] tools/check-staleness.py:466-467`, and its regex requires a
`something.md` before the `§` `[repo] tools/check-staleness.py:439`. A page
whose own diagram points at its own missing sections is out of scope. (Its
cross-file coverage does work — 0 problems, and I found no broken cross-file
`§` reference by hand `[run]`.)

Compounding it: `module.md` is a clean board page with a circuits index table
and no live values `[repo] hardware/module/module.md:6-30`, while `carrier.md`
and `cluster-boards.md` are still schematic pages carrying live circuit content
*and* partial splits, and **`carrier.md` has no circuits index at all** — its
five circuit directories are reachable only from italic "moved verbatim to"
notes scattered through the body `[run]`. Three boards, three different page
shapes.

### F15 — A `forbidden` pattern that can never match, produced by following the documented rule

`spi-series-r`'s forbidden list contains `"220 Ω with\n~200 pF"`
`[repo] config/figures.yaml:216`. In a YAML double-quoted scalar `\n` is a real
newline; `yaml.safe_load` returns it as one `[run]`. `check_figures` joins the
corpus into a stream using **one space** per line break and never emits a
newline `[repo] tools/check-staleness.py:159-169`, so that pattern cannot match
any input. It is the only such pattern in the register `[run]`.

This is a direct consequence of the rule as written. `CLAUDE.md` §2 and
`repo-maintenance.md` §2 both say "grep the corpus for the OLD value first, and
add one pattern per spelling you find"
`[repo] CLAUDE.md:52-56`, `[repo] docs/reference/repo-maintenance.md:36-40` —
and a spelling you find in a hard-wrapped corpus is frequently a spelling that
spans a line break. Neither document says "patterns are matched against a
line-joined stream, so write the wrapped spelling with a single space and no
newline." The next person to follow the rule will write another dead pattern,
and it will report zero hits exactly as the fourth recorded instance did.

### F16 — Minor, but they cost a reader time

- `README.md:98` — "`docs/reference/` Latency budgets, fingering notes, specs".
  There are no fingering notes there; fingering lives in `config/key-layout.yaml`
  `[run]`. The line also omits `repo-maintenance.md` and `pcb-pipeline.md`, the
  two files in that directory a contributor most needs.
- `README.md:24` — the Controller column reads "Keys, breath sensor, IMU,
  display, MCU" (singular). ADR 0013 splits the instrument across **two** MCUs
  and `firmware/README.md:3-9` ships two images `[repo]`. `README.md` never
  names `carrier`, `cluster` or `module` — the three board names that organise
  the entire `hardware/` tree — anywhere `[run]`.
- `ROADMAP.md:137-152` — Track F rows run F1…F7, **F9, F8** `[repo]`. The Phase
  view then says Phase 5 contains "F4–F9" `[repo] ROADMAP.md:161`.
- `docs/decisions/README.md:36-42` carries its own warning that the index table
  is hand-maintained and was wrong in three of fourteen rows `[repo]`. The rows
  read correct today `[run]`, but the table restates a fact each ADR owns —
  rule 1 broken in the project's own index, as the warning itself says.
- No `README.md` in `docs/`, `docs/log/`, `docs/reference/`, `docs/research/`,
  `docs/review/`, `config/`, `tools/`, `mechanical/`, or any of the three board
  directories `[run]`. `docs/reference/repo-maintenance.md` — the file
  `CLAUDE.md` calls required reading — sits in an unindexed directory and is
  linked from `CLAUDE.md` only `[run]`.

---

## What genuinely works — do not re-open

These were tested and are good. Several are better than anything I expected to
find, and at least two are load-bearing enough that weakening them would be a
regression.

1. **Every markdown link in the corpus resolves.** I walked all `.md` outside
   `docs/review/` and checked every relative target: **0 broken links**
   `[run]`. After a restructure of this size that is a real result.

2. **`merge-bom.py --check` is the best-engineered thing in the repository.**
   It catches a hand edit on the generated master with the first differing line
   named, catches a fragment on disk that `ORDER` does not name, and catches two
   circuits claiming one refdes with both locations printed
   `[repo] tools/merge-bom.py:96-130,148-156`. I triggered the first two
   deliberately and both messages told me exactly what to do `[run]`. The CRLF
   discipline is enforced in code rather than by asking
   `[repo] tools/merge-bom.py:133-141`, and a three-row edit produced a 4-line
   diff `[run]`.

3. **`hardware/README.md` is the right page.** Board table with working links,
   the directory contract, the generated-file trap and the citation rule, in
   forty lines. Its only real problem is that nothing links to it (F1). The
   `interfaces/README.md` companion is equally good and answers the question a
   newcomer actually has — *why* are these three not under a board — with a
   concrete argument (the `AGND`/`BREATH` name collisions) rather than a
   convention `[repo] hardware/interfaces/README.md:15-40`.

4. **`module.md` is the model board page.** Index table, one line per circuit,
   no restated values, an explicit "Still open" that names what is unresolved
   including the `unplaced.csv` situation `[repo] hardware/module/module.md`.
   If `carrier.md` and `cluster-boards.md` are ever reshaped, this is the
   target.

5. **The `## Interfaces` table convention.** Node / Dir / Peer / Figure / Note,
   with quantities appearing only as a figure citation
   `[repo] hardware/module/dac8568/dac8568.md:9-24`. It is the one place in the
   corpus where a reader can tell a citation from a restatement at a glance, and
   it is applied consistently across the circuit pages I opened.

6. **`sim/README.md`'s refusal to hold fabricated results.** "Nothing here has
   been run. … A plausible number written here would sit next to figures read
   off banked datasheets and be indistinguishable from them"
   `[repo] hardware/module/pitch-stage/sim/README.md:3-11`. The *labelling* in
   `hardware/README.md` needs fixing (F6.1); the policy does not.

7. **`docs/reference/latency-budget.md`** — README's only technical entry point,
   and it earns the slot. It states its target, its actual margin ("about 1.6×,
   not the 10× that was claimed elsewhere"), separates the analog and digital
   breath paths that "used to be one table", and marks the one unmeasured term
   as `? — sized at E2` `[repo] docs/reference/latency-budget.md:1-45`. A
   newcomer learns the real constraint in one hop.

8. **`repo-maintenance.md` §6's "what each tool refuses to do, and why it now
   refuses" table** `[repo] docs/reference/repo-maintenance.md:242-256`. Four
   fail-open bugs, each with the reproduction that found it. This is the format
   the rest of the corpus should be jealous of, and `check-staleness.py`'s
   corpus-count floor and `check_checks()` self-wiring assertion
   `[repo] tools/check-staleness.py:37-56,576` are genuinely unusual defences.

9. **`.gitignore` covers `__pycache__`**, so running the tools does not dirty
   the tree `[run]` — with the reason recorded inline
   `[repo] .gitignore:9-13`.

10. **`config/figures.yaml`'s `escape_note` / `false_positive_note` fields.**
    Reading `sensor-full-scale` teaches a newcomer more about how this project
    fails than any prose page does, and `false_positive_note` is what stops the
    next reader "fixing" a legitimate quotation
    `[repo] config/figures.yaml:34-91`. F15 and F2 are about the *mechanism*
    around these notes, not the notes.

---

## Note on method

Everything marked `[run]` was executed against `/home/user/Woody` read-only, or
against a `tar`-copied throwaway tree under the session scratchpad. The working
tree was not modified: `git status` after this report shows exactly one new
file, this one `[run]`.
