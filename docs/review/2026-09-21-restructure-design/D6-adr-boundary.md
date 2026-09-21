# D6 — The ADR boundary

**Agent:** D6, cold wave `2026-09-21-restructure-design`.
**Slice:** where a decision lives once `hardware/**` gains a per-circuit `notes.md`.
**Cold:** no file under `docs/review/**`, `docs/log/**` or `docs/research/**` was read.

Provenance on every claim: `[repo]` path:line, `[calc]` with arithmetic, `[from memory]`.
Section end lines are `[calc]` — next heading minus one, against the heading maps
extracted from each file.

---

## 0. Headline

**Nothing moves.** Not one line of ADR prose relocates into a circuit `notes.md`,
and no ADR is split.

But the boundary question is not really ADR-vs-circuit. The evidence below says
the third home is **already occupied**: the schematic pages under `hardware/**`
already carry dated circuit-local decision records, rejected alternatives and
"settled/retired on 2026-09-21" subsections `[repo]`
`hardware/module/power-entry.md:125`, `hardware/module/mod-channels.md:210`,
`hardware/module/digital-and-supervision.md:232,245`,
`hardware/module/breath-receive-stage.md:339`. A free-form `notes.md` would
duplicate the schematic page, not the ADR — and duplication is this project's
one failure mode `[repo] CLAUDE.md:8`.

So: `notes.md` survives, with **no authority to assert anything**. Scope in §3.

Three facts found while mapping the boundary are defects in the corpus today and
are listed in §7. Two of them are live staleness escapes that
`tools/check-staleness.py` cannot see, and **both are in a document that owns the
figure it gets wrong**. That is the argument against ever moving a live value
into a frozen document, and it is the spine of this report.

---

## 1. The overlap map

Method: heading maps extracted from all 14 ADRs and all 8 schematic pages
`[repo]`. A section is counted **circuit-local** when it states a topology, a
component value, a node, a derivation or a refdes for exactly one circuit block —
i.e. when a schematic page is the document a builder would open.

### 1.1 Per-ADR totals

`body` = lines 5..EOF (after the `# title` / `**Status:**` block) `[calc]`.

| ADR | body | circuit-local | % | schematic pages covering the same ground |
|---|---|---|---|---|
| 0001 mcu-and-board-partitioning | 378 | **191** | 51% | `cluster-boards.md`, `carrier.md` §3 |
| 0002 key-switches-and-mounting | 232 | 0 | 0% | none — 128 lines are *reference*-local (`ks33-geometry.md`) |
| 0003 breath-sensing-path | 807 | **399** | 49% | `carrier.md` §2, `breath-receive-stage.md`, `breath-output-stage.md` |
| 0004 cv-interface-module | 942 | **462** | 49% | `power-entry.md`, `digital-and-supervision.md` |
| 0005 power-architecture | 395 | **168** | 43% | `power-entry.md` |
| 0006 cv-channel-allocation | 825 | **431** | 52% | `pitch-stage.md`, `mod-channels.md` |
| 0007 imu-selection | 245 | 63 | 26% | `carrier.md` §7 |
| 0008 display-selection | 229 | 52 | 23% | `carrier.md` §6 |
| 0009 enclosure-construction | 694 | ~30 | 4% | **none exists** — `mechanical/{cad,drawings,export}` are all empty `[repo]` |
| 0010 key-layout-as-data | 205 | 23 | 11% | `cluster-boards.md` §4 |
| 0011 licensing | 71 | 0 | 0% | — |
| 0012 configuration-interface | 128 | 0 | 0% | — (firmware) |
| 0013 two-mcu-split | 289 | 77 | 27% | `carrier.md` §4, §7 |
| 0014 lighting | 542 | **240** | 44% | `carrier.md` §5, `power-entry.md` |
| **total** | **5982** | **2136** | **36%** | |

The four ADRs the brief flags as very large are also the four most duplicated:
0004 (49%), 0006 (52%), 0003 (49%), 0001 (51%). 0009, the fourth-largest at 698
lines, is the *least* duplicated at ~4% — because it has no circuit counterpart
at all. Size is not the signal. **Having a drawn circuit is the signal.**

### 1.2 Section-level map, the six ADRs that matter

| ADR § (heading) | lines | n | covered by |
|---|---|---|---|
| **0001** `### One register per cluster, on the board its switches are already on` | 120–169 | 50 | `cluster-boards.md` §1 89–127, §2 128–236 |
| **0001** `### And the part changes to the slow family` | 170–187 | 18 | `cluster-boards.md` §1 89–127 |
| **0001** `### Key-line signal integrity` | 188–310 | 123 | `cluster-boards.md` `### Derivations` 150–236 |
| **0001** `### Two firmware rules the chain depends on` | 311–356 | 46 | *firmware*-local, not circuit-local |
| **0003** `## Breath output is analog, sent differentially` + 5 subsections | 292–428 | 137 | `breath-receive-stage.md` 17–255 |
| **0003** `### The sensor runs from a precision reference, not the shared 5 V rail` | 429–498 | 70 | `carrier.md` §2 162–438 |
| **0003** `### The breath buffer moves to +12 V…` | 499–547 | 49 | `carrier.md` §2 162–438 |
| **0003** `### The ADC does not go away` | 548–586 | 39 | `carrier.md` `### Derivations` 347–425 |
| **0003** `### What the analog path gives up, and what replaces it` | 587–638 | 52 | `breath-output-stage.md` 11–168 |
| **0003** `### Parts` | 639–645 | 7 | `bom.csv` |
| **0003** `## The analog ground star point, defined` (+ 703–719) | 675–719 | 45 | `carrier.md` §2; `power-entry.md` `## Grounding` 491–503 |
| **0004** `### The module needs its own logic rail` | 133–158 | 26 | `power-entry.md` 10–124 |
| **0004** `### The DAC gets a local regulator; the level shifter keeps the bus rail` | 159–215 | 57 | `power-entry.md` 10–124 |
| **0004** `### Module parts, chosen for build ease` | 216–247 | 32 | `bom.csv`; `breath-receive-stage.md` |
| **0004** `### Power entry, and why this module is not a typical one` | 248–367 | 120 | `power-entry.md` 10–124, 491–503 |
| **0004** `### The module's normal "off" state has the SPI bus floating` | 368–417 | 50 | `digital-and-supervision.md` 15–132 |
| **0004** `### There is no presence detect, and the buffer runs unconditionally` | 418–439 | 22 | `digital-and-supervision.md` `## There is no presence detect either` 133–156 |
| **0004** `### Why the module does not need to know, and where the knowing went` | 440–467 | 28 | `digital-and-supervision.md` 133–156 |
| **0004** `### A stuck CV is worse than a dead one` + `#### The watchdog's scope…` | 468–546 | 79 | `digital-and-supervision.md` `## There is no frame watchdog` 157–219 |
| **0004** `### Grounding: one origin, named, before the board is laid out` | 593–640 | 48 | `power-entry.md` `## Grounding` 491–503 |
| **0005** `### The module's 5 V splits: bus rail for logic, local regulator for the DAC` | 119–146 | 28 | `power-entry.md` 10–124 |
| **0005** `### The module's toggle drives a current-limited load switch` | 242–259 | 18 | `power-entry.md` `## The load switch` 125–451 |
| **0005** `### Set the limit at 1.0 A, and delete the polyfuse` | 260–381 | 122 | `power-entry.md` 125–451 |
| **0006** `### The topology falls out neatly` | 80–138 | 59 | `pitch-stage.md` 39–123; `mod-channels.md` 48–150 |
| **0006** `### Resolved: what the outputs do at power-on` | 144–236 | 93 | `mod-channels.md` 151–195; `digital-and-supervision.md` 157–219 |
| **0006** `## The pitch output keeps its 1 kΩ series resistor` + `### What this costs…` | 507–582 | 76 | `pitch-stage.md` `### DC feedback is tapped at the jack…` 159–234 |
| **0006** `### The offset reference is VREFOUT, buffered — not the rail` | 583–616 | 34 | `pitch-stage.md` 92–123 |
| **0006** `### And stop modulating the rail in the first place` | 617–662 | 46 | `pitch-stage.md` 92–123; `power-entry.md` |
| **0006** `### Consequence elsewhere` | 663–762 | 100 | `pitch-stage.md` 249–309 |
| **0006** `## Small protective parts on the module` | 784–806 | 23 | `bom.csv`; `pitch-stage.md` |
| **0014** `## There is no LED driver, but there is a level shifter` | 89–118 | 30 | `carrier.md` §5 683–759 |
| **0014** `## Power budget, and the cap that is not optional` (+4 subsections) | 119–241 | 123 | `carrier.md` §5; `power-entry.md` |
| **0014** `## The 8×8 matrix` (+3 subsections) | 309–355 | 47 | `carrier.md` §5; `bom.csv` |
| **0014** `## Grounding` (+ 509–533) | 494–533 | 40 | `carrier.md` §5; `power-entry.md` 491–503 |
| **0007** `## Board: Waveshare ESP32-S3-Matrix` (+ `### Pin assignment` 179–204) | 142–204 | 63 | `carrier.md` §7 809–842; `bom.csv` |
| **0008** `## Pin budget` (+3 subsections) | 61–112 | 52 | `carrier.md` §6 760–808 |
| **0013** `## The link` | 89–109 | 21 | `carrier.md` §4 591–682 |
| **0013** `## Build approach: dev boards as modules on a passive carrier` | 224–279 | 56 | `carrier.md` §7 809–842; `bom.csv` |
| **0010** `## Spare inputs are reserved in the plate, not just in the chain` | 158–180 | 23 | `cluster-boards.md` §4 312–421; `config/key-layout.yaml` |

### 1.3 The corpus already solved this, in five places

Five ADR sections carry a **delegation clause** — a blockquote at the head of the
section naming the schematic page and granting it precedence `[repo]`:

| where | text |
|---|---|
| `0003:394-395` | "Values, derivation and the full topology are in [the schematic]" |
| `0004:231-233` | "…are in `hardware/module/breath-receive-stage.md`, **which supersedes this paragraph and ADR 0003's prose where they disagree**" |
| `0004:482-483` | "…are in `hardware/module/digital-and-supervision.md`. The paragraphs below are kept because the problem they describe is still real" |
| `0005:271` | "the **guaranteed envelope is 49–197 ms** (`hardware/module/power-entry.md`)" |
| `0006:82-86` | "**Drawn now**… Where those pages disagree with the prose here, **they win** — that is the rule the breath page established and the reason it exists" |

There are 16 ADR→`hardware/` pointers in total `[repo]`. The delegation clause is
an existing, working convention that was invented under pressure and never
written down. §3 writes it down.

---

## 2. Does anything move? — No.

**Recommendation: nothing moves. ADRs stay exactly as they are, byte for byte.**

Four arguments, in descending strength.

### 2.1 Moving prose out of an ADR destroys the thing the ADR is for

`docs/decisions/README.md:24-29` states the convention: rejected options are
kept, and a reversed decision is never edited — it is marked `Superseded` and a
new ADR is written `[repo]`. The corpus's most valuable ADR content is exactly
the content a restructure would be tempted to move: **arguments that lost**.

`0006:82-138` is the worked case. That section records, in order: a four-resistor
difference amp that was believed correct; the two-resistor non-inverting form
that replaced it; an LT5400 gain-of-4 claim marked `**Superseded 2026-09-21**`;
and a wrong meta-claim about `A = 1 + B` being "a boundary pitch luckily landed
on", corrected in place with the reason it mattered `[repo] 0006:100-103`. Moved
into `mod-channels.md`, that becomes a schematic page carrying three dead
topologies. Left where it is, it is the reasoning trail the README asks for.

**A schematic page is a statement of what is true now. An ADR is a statement of
what was decided, when, against what.** They are different genres and the
overlap in §1 is not redundancy — it is the same fact serving two readers.

### 2.2 The content freeze forbids it, and the freeze is right here

The restructure "moves and splits only" and "no value gets edited." Moving
`0004:248-367` into `power-entry.md` is not a move — it is a **merge**, because
`power-entry.md:10-124` already covers that ground and **disagrees with it
numerically** (§7.1). A merge cannot be performed without editing, and editing is
frozen. There is no move that is not also a merge for any of the 2136 lines in
§1: every one of them has a live counterpart.

The only freeze-legal "move" would be cut-and-delete, leaving the schematic page
untouched and the ADR gutted. That is strictly worse: it deletes 2136 lines of
dated reasoning to remove zero duplication, because the duplicate that stays is
the one that is sometimes wrong.

### 2.3 ADR numbers are a live foreign key from 138 rows

`hardware/bom.csv` carries an `adr` column and **all 138 rows are populated —
zero blanks** `[repo]` `[calc]`, distributed 0001:11, 0002:4, 0003:29, 0004:25,
0005:13, 0006:23, 0007:2, 0008:1, 0009:17, 0013:8, 0014:5. Plus 39 `ADR 00…`
references in `ROADMAP.md` `[repo]` `[calc]`, 8 `owner:` paths in
`config/figures.yaml`, `docs/decisions` hard-coded in
`tools/check-staleness.py:30` `CORPUS_DIRS`, and reverse links from `README.md`,
`firmware/README.md`, `docs/reference/latency-budget.md`,
`docs/reference/repo-maintenance.md`, `datasheets/MANIFEST.csv` and
`datasheets/.manifest-R7.csv` `[repo]`.

Nothing validates that column. `check_bom()` at `tools/check-staleness.py:110-123`
checks column count and duplicate refdes only `[repo]`. So a renumbering or a
repath breaks 138 rows **silently** — the project's named failure mode, at scale,
with no checker coverage.

### 2.4 Splitting the big ADRs would re-run the defect that produced them

Splitting `0004` (946 lines) into, say, `0004a-module-power` and
`0004b-module-digital` creates two documents whose Context sections must both
restate the partitioning argument at `0004:118-132`. That is one fact in two
files, chosen deliberately. The four ADRs the brief names as split candidates are
the four whose sections are most *mutually* dependent: `0004:496-546` (watchdog
scope) turns on `0003`'s breath path and `0006`'s DAC clear state; `0006:617-662`
turns on `0004`'s power entry.

**What to do instead of splitting:** nothing structural. The large ADRs are large
because they are the cross-cutting ones, and §1.1 shows the correlation — the
three ADRs over 800 lines are the three that bind four or more circuits each.

---

## 3. The rule that stops a decision living in two places

Write this into `docs/decisions/README.md` and into each `notes.md` header.

### 3.1 The rule

> **One document asserts. Every other cites.**
>
> Which document asserts is decided by **scope**, in this order — stop at the
> first yes:
>
> 1. **Is it a number that more than one document needs?**
>    → `config/figures.yaml`, with `owner:` set to the document that *derives*
>    it. Every other document, ADR included, cites the **id**, never the value.
> 2. **Is it true of exactly one circuit block?** (a topology, a node, a value,
>    a refdes, a derivation, a trim procedure)
>    → the **schematic page**, `hardware/<board>/<circuit>.md`.
> 3. **Is it a choice between named alternatives that were weighed, or would
>    have to be re-weighed to reverse it?**
>    → an **ADR**. Reversing an existing one means a *new* ADR, never an edit.
> 4. **Is it an observation made after the page was drawn** — a bench
>    measurement, a bring-up result, a vendor erratum, a part substitution —
>    that does not yet change a value or a choice?
>    → the circuit **`notes.md`**, dated, naming what it would change if
>    confirmed.
> 5. Otherwise it is not a decision. It belongs in the prose of whatever page
>    already covers the subject.
>
> **`notes.md` may not be the `owner:` of any `figures.yaml` entry, and may not
> state a value that is not already stated in its schematic page or the
> register.** It holds pointers and dated observations. Nothing else.
>
> **When an ADR section and a schematic page cover the same circuit, the ADR
> section keeps its prose and gains a delegation clause** naming the page and
> granting it precedence — the form already used at `0004:231`, `0004:482`,
> `0006:82` and `0003:394`.

Rules 2 and 3 are the whole boundary, and they collapse to one sentence:
**more than one circuit → ADR; exactly one circuit → schematic page.**

### 3.2 Why `notes.md` gets rule 4 and nothing else

Rule 4 is the only job none of the other three files can do. An ADR is frozen by
convention and a schematic page is a statement of the current design; neither has
a place for "E6 measured 412 mA on a board with four screws in it, which does not
change the value yet." That is genuinely homeless today and it is what `notes.md`
is for.

Every other candidate job for `notes.md` is already taken — `power-entry.md:125`,
`mod-channels.md:210`, `digital-and-supervision.md:232,245` and
`breath-receive-stage.md:339` are all dated circuit-local decision records living
on the schematic page, correctly `[repo]`.

### 3.3 Worked tests — three real, non-obvious cases

**Test A — the 1N5817 forward-voltage modulation.**

*Looks like:* an ADR fact. It appears in `0004`, `0006` and `bom.csv`, it spans
power entry and pitch, and `0004` argues a part count from it.

*Rule says:* rule 1 first — it is a number four documents need, so it is a
register entry. `diode-split-rationale`, `owner: hardware/module/power-entry.md`
`[repo] config/figures.yaml:359-366`. Rule 2 confirms the owner: the *decision*
it supports (three diodes, not two) is true of exactly one circuit — power entry.
The pitch consequence is a **derived** number, not a decision, so it is not
ADR-worthy at all.

*Corpus today:* `0004:319-320` and `0006:624` both restate it, and both are
**wrong** (§7.1). This is the test's payoff — the rule would have caught it.

**Test B — `V_ref = 3.3333 V` on the mod channels.**

*Looks like:* an ADR 0006 fact. 0006 is literally titled "CV channel allocation",
the reference comes from DAC channel 7, and 0006 states the value **eight times**
— lines 15, 21, 92, 105, 117, 125, 127, 248 `[repo]` `[calc]`.

*Rule says:* split the sentence. "**Mod channels are bipolar, −10 to +10 V**"
(`0006:68`) is a choice between named alternatives — unipolar 0–10 V was the
prior decision `[repo] 0006:70-73` — so rule 3, ADR. "**3.3333 V, from DAC
channel 7**" is what the chosen topology *forces* given 10k/30k at k=3: it is one
circuit's value, rule 1+2, `owner: hardware/module/mod-channels.md` — which the
register already says `[repo] config/figures.yaml:165-169`.

*Consequence:* 0006's eight restatements become eight citations of
`mod-reference`. The eight are correct today. That is precisely why they are
dangerous — nothing would flag them when the ninth is added.

**Test C — where `DIG_GND` returns to.**

*Looks like:* a circuit fact. Two schematic pages assert it, in contradiction.

*Rule says:* rule 2 fails — it is **not** true of exactly one circuit. It is a
board-level return-path policy binding power entry *and* the digital section, and
reversing it means re-weighing star vs pour-under-trace vs single-tie. Rule 3:
**ADR**. And because `0004:627` already asserts one of the three candidates, the
supersession convention forbids editing it: the answer is **write ADR 0015**.

*Corpus today:* `config/figures.yaml:299-311` has it `DISPUTED` with three
candidates in three files — `0004:627`, `power-entry.md:495-498`,
`digital-and-supervision.md:53` — and records that `power-entry.md` **claims ADR
0004 was corrected on this point and it was not** `[repo]
config/figures.yaml:311`. `decided_by` names the real blocker: the 2-layer vs
4-layer choice, which is upstream and **has no ADR at all** `[repo]`. That gap is
the finding: rule 3 says the layer count is an ADR, and there isn't one.

Test C is the case where the answer is "a new ADR" even though every document
currently touching the question is a schematic page. It is the one the rule is
worth having for.

---

## 4. The ADR index and numbering

### 4.1 Home and numbering: unchanged

**ADRs keep `docs/decisions/`, flat, four digits, same numbers.** §2.3 gives the
mechanical reason (138 BOM rows, 39 ROADMAP refs, 8 register owners, one
hard-coded `CORPUS_DIRS` entry, 6 reverse-linking files). The design reason is
stronger: an ADR is cross-cutting by definition, so filing it under one circuit
directory contradicts what it is. `0013` (two-MCU split) has no circuit at all;
`0011` (licensing) has no hardware; `0009` has no drawn counterpart anywhere
because `mechanical/` is empty `[repo]`.

`README.md:100` — "`hardware/` BOM, schematics, PCB, split by board" — is the one
line that must change for the circuit-primary axis. `README.md:96` and
`README.md:110` need no change.

### 4.2 The status table: generate it, do not maintain it

`docs/decisions/README.md:38-52` is a hand-written status table and **3 of its 14
rows disagree with the ADR they point at** `[repo]`:

| ADR | index says | the file says |
|---|---|---|
| 0007 | `Accepted (board open)` (`README.md:47`) | `Accepted. Board selected: Waveshare ESP32-S3-Matrix.` (`0007:3`) — and `## Open` at `0007:245-249` contains no board question |
| 0008 | `Accepted (board open)` (`README.md:48`) | `Accepted. Board selected: LilyGO T-Display-S3 AMOLED (base, not Plus).` (`0008:3`) — `## Open` says "Nothing blocking." (`0008:231`) |
| 0011 | `Open` (`README.md:51`) | `Accepted` (`0011:3`) |

One fact, two places, and the copy the *reader* opens is the stale one — the
named failure mode `[repo] CLAUDE.md:8-12`, inside the ADR index itself.

**Recommendation:** the `Status` column is generated from each ADR's
`**Status:**` line by `tools/`. Two columns, both generated:

| # | Title | Status | Circuits bound |
|---|---|---|---|

`Circuits bound` is generated from `bom.csv`'s `adr` column joined to each BOM
row's circuit, and it is the same data that feeds §5's per-circuit index — one
generator, two outputs, no hand-maintained duplicate. This is the only change to
`docs/decisions/README.md`, and it is a *tooling* change, so it does not touch
ADR content and clears the freeze.

Note also: **zero ADRs are marked `Superseded`** `[repo]`, although
`docs/decisions/README.md:20` defines the status and `0004:9` writes "(see ADR
0005, superseded)". `0005:3` says `Accepted`; only its *section* `## Superseded
approach: onboard battery` at `0005:10-37` is superseded `[repo]`. The
parenthetical at `0004:9` is therefore wrong as written. See §5.3 — the index
cannot represent section-level supersession and must not pretend to.

### 4.3 Should an ADR own a figure? Mostly no.

**8 of the 33 register entries name an ADR as `owner`, not 3** `[repo]`
`config/figures.yaml` lines 38, 116, 148, 186, 194, 231, 354, 394 `[calc]`. The
brief's figure of 3 is understated; the exposure is 2.7× larger than assumed.

The principle: **an ADR is immutable by convention; a `value:` field is mutable
by design.** `docs/decisions/README.md:26-29` forbids editing a reversed ADR in
place; `config/figures.yaml:15` requires the owner to be updated whenever the
figure moves. Putting a live number's single source inside a frozen document is a
category error, and §7.2 shows it failing right now in `0003`.

> **An ADR may own a figure only when the figure is an interface contract between
> blocks and no block is its natural home. If a block exists, the block owns it.**

Applied to the 8:

| id | line | owner | verdict |
|---|---|---|---|
| `chain-conductors` "12" | 112–116 | 0001 | **Move → `hardware/controller/cluster-boards.md`.** `cluster-boards.md` already owns `chain-connectors` ("8", 120–124), `key-press-time` and `key-release-time`. Two halves of one chain spec owned by two documents is the failure mode by construction. |
| `sensor-full-scale` "4.86 V" | 34–38 | 0003 | **Move → `hardware/controller/carrier.md`** §2, which already states `0.265 – 4.86 V` in the drawing (`carrier.md:187`) and cites the id explicitly at `carrier.md:357`. Owning it from a frozen ADR has already produced two live escapes (§7.2). |
| `umbilical-pinmap` | 144–148 | 0004 | **Move → a new `hardware/interfaces/umbilical.md`.** Under a circuit-primary axis the umbilical *is* a block: two connectors, a cable spec, a TVS network and a pin map. It is currently the only block with no page. |
| `panel-width` "50.50 mm (10HP)" | 182–186 | 0004 | **Move → a new `hardware/module/panel.md`**, together with the 10HP derivation at `0004:716-832`. |
| `panel-height-budget` | 190–194 | 0004 | as above |
| `umbilical-current` "359 mA" | 350–354 | 0005 | **Keep ADR-owned for now.** It is *produced* by the instrument load table at `0005:147-179`, which has no circuit home until E6 measures it. Watch it: `0004:275` already restates it with an inline dated correction — "this row said '~320 mA (… ~275 instrument)' until 2026-09-21" `[repo]` — which is the warning shape. |
| `breath-working-point` | 227–231 | 0003 | **Defer** — `status: disputed`. Moving an owner while the value is disputed relocates the dispute without resolving it. |
| `matrix-led-current` | 390–394 | 0014 | **Defer** — `status: blocked` on a datasheet. |

Net: 5 move to circuits (3 existing pages + 2 new pages), 1 stays, 2 deferred.
All 8 are `figures.yaml` edits, not ADR edits, so they are **freeze-legal but out
of scope for a move-and-split restructure** — file them as a follow-up commit and
run the three-step procedure at `CLAUDE.md:27-31` for each.

---

## 5. The reverse risk: ADRs quietly stop being written

Real. The circuit pages are where the work happens — `CLAUDE.md:11` already names
the mechanism ("fixes land where the editing is happening; they do not land where
the reader looks"), and `notes.md` puts a blank page next to the editor's hand.
Nothing in the current toolchain would notice.

### 5.1 Three mechanical brakes, in order of value

**1. Make the `adr` column a gate.** `hardware/bom.csv` is 100% populated today
`[repo]` `[calc]`, and parts are what circuits are made of — you cannot design a
circuit without adding or changing a row. Extend `check_bom()`
(`tools/check-staleness.py:110-123`, which today checks only column count and
duplicate refdes) with: *every row has a non-empty `adr`, and it resolves to a
file in `docs/decisions/`.* Roughly six lines. This is the strongest available
brake because it makes "reasoning drifted into `notes.md` and no ADR was written"
fail at commit time, and it simultaneously closes the silent-break hazard in
§2.3.

**2. Forbid `notes.md` from owning a figure.** Assert in the checker that no
`figures.yaml` `owner:` ends in `notes.md`. Two lines. This is §3.1's scope rule
made mechanical rather than aspirational, which is what `CLAUDE.md:14` asks for.

**3. Add a standing review-wave slice.** `CLAUDE.md:106-108` already mandates one
agent auditing the previous round's fixes. Add a second standing slice: *one agent
auditing whether anything decided since the last wave has no ADR*, using the git
log against `docs/decisions/` as the comparison. Semantic, so it belongs at a
gate, not per commit `[repo] CLAUDE.md:68-75`.

Brakes 1 and 2 are mechanical and cheap. Brake 3 catches what they cannot: a
decision with no part.

### 5.2 How a reader finds all decisions affecting one circuit

The per-circuit `notes.md` opens with a **generated** block:

```
## Decisions binding this circuit
<!-- generated by tools/build-decision-index.py — do not edit -->
| ADR | Title | Status | Sections |
```

Two sources, both already present:
- **`bom.csv` `adr` column** → refdes-level, gives ADR-to-circuit for 138 rows.
- **a `binds:` line added to each ADR's header**, listing circuit paths — the one
  ADR edit this report recommends, and it is metadata, not content, so it does
  not touch the record. It is needed because 0013, 0012 and the grounding
  sections bind circuits they have no BOM row in.

The same generator emits §4.2's `Circuits bound` column. One source, two views,
zero hand-maintained duplicates — the pattern `CLAUDE.md:59-66` already applies to
`MANIFEST.csv`.

`tools/check-staleness.py`'s `check_refdes()` (`:126-144`) scans `hardware/` only
`[repo]`, so refdes drawn inside an ADR get no BOM cross-check while refdes in a
`notes.md` under `hardware/**` would. A second, quieter reason not to move circuit
content into ADRs.

### 5.3 Superseded decisions, which are the point

`docs/decisions/README.md:20` keeps `Superseded` ADRs "for the reasoning trail",
so **a superseded ADR that is missing from a circuit's index is worse than no
index — it looks complete.** Three constraints on the generator:

1. It lists **every** ADR that ever bound the circuit, with the status string
   taken **verbatim** from the ADR's own `**Status:**` line. Never a filter,
   never a re-worded status.
2. **It is ADR-level and cannot be finer.** The corpus's supersession is mostly
   *section*-level: `0005:10-37` is a superseded section inside an `Accepted`
   ADR; `0001:3` reads "Accepted. Partitioning revised by 0013"; `0006:80-138`
   carries three superseded topologies inside an accepted section `[repo]`. An
   index that renders `0005` as "Accepted" is correct and incomplete, and it must
   say so rather than imply completeness.
3. It carries a one-line footer: *"Section-level supersession is not indexed.
   Read the ADR."* Without it, the index becomes the third place a decision
   lives — which is the failure this whole report is about.

The live example of why this matters: `0004:9` writes "(see ADR 0005,
superseded)" while `0005:3` says `Accepted` `[repo]`. A generated index would
have shown that contradiction on the day it was written.

---

## 6. `docs/reference/` — the four files

| file | owns | verdict |
|---|---|---|
| `latency-budget.md` (193 ln) | `loop-budget` "196-241 us of 250 us" (`figures.yaml:341-345`) | **Stays in `docs/reference/`.** A cross-cutting *constraint*, not a circuit and not a decision. It binds firmware, `cluster-boards.md` §2, `carrier.md` §2/§3/§4 and `0003`; the `250 us` figure appears in 7 ADR locations `[repo]` `[calc]`. No circuit is its home, so moving it under `hardware/` means picking one arbitrarily. Its own header states the role (`:3-6`). |
| `ks33-geometry.md` (176 ln) | `plate-thickness` "1.20 mm" (`figures.yaml:368-372`) | **Stays for now; it is really a datasheet.** `:10` says "the vendor drawing supersedes it wherever the two disagree" — that is a banked-document contract, not a reference-page one, and `:6-9` records that `gateron.com` is unreachable from the sandbox. `CLAUDE.md:47-50` already has the mechanism: a `BLOCKED` `MANIFEST` row with the exact URLs. **Add that row, pointing at this file**, and if the file later moves into `datasheets/`, `plate-thickness`'s owner moves with it. Its 8 consumers are all ADRs — `0002:138,167,176,178,181,227,230` and `0009:64` `[repo]` — the same 8-restatements shape as Test B. |
| `pcb-pipeline.md` (274 ln) | — | **Not an instrument fact.** `:3-4` marks it "Proposed 2026-09-21… Not run." It describes how the repo is *operated*. Belongs with `repo-maintenance.md`. |
| `repo-maintenance.md` (186 ln) | — | Same kind. **But do not move it in this restructure** — see the trap below. |

**The split worth making, and the trap in making it.** `docs/reference/` currently
mixes two genres: facts about the instrument that no circuit owns
(`latency-budget`, `ks33-geometry`) and instructions for operating the repo
(`pcb-pipeline`, `repo-maintenance`). A `docs/process/` directory for the latter
two is the clean answer.

It is not free:

1. `tools/check-staleness.py:30` lists `docs/reference` in `CORPUS_DIRS` and
   **not** `docs/process` `[repo]`. Moving the files removes them from staleness
   coverage **silently** — no error, no warning, just two documents that stop
   being checked. Exactly the class of trap `docs/reference/repo-maintenance.md`
   exists to record.
2. `CLAUDE.md:65` and `CLAUDE.md:119-121` both hard-link
   `docs/reference/repo-maintenance.md` by path `[repo]`. Moving it edits
   `CLAUDE.md`.
3. `README.md:98` describes `docs/reference/` as "Latency budgets, fingering
   notes, specs" `[repo]` — which already fails to describe either of the two
   process files.

**Recommendation:** do the split, but in a **separate commit from the hardware
restructure**, and in this order: add `docs/process` to `CORPUS_DIRS` first, in
its own commit; then move the two files; then fix the three call sites. Never in
the same commit as the move — that is the only ordering in which a mistake is
visible rather than silent.

---

## 7. Defects found while mapping the boundary

Filed as claims, per `CLAUDE.md:110-115`. All three are semantic or
spelling-escape, and the checker reports `PASS no live stale values` `[repo]
.staleness-report.txt`.

### 7.1 `diode-split-rationale` is stale in two ADRs and `bom.csv` — three different values

Register value: **120 mV → 0.00044 cents**, `owner:
hardware/module/power-entry.md` `[repo] config/figures.yaml:359-366`, derived
from the digitised curve in `datasheets/discrete-and-power/1N5817.pdf` and stated
at `power-entry.md:60,78-80`.

| location | says | status |
|---|---|---|
| `power-entry.md:60,78-80` | 120 mV → **0.00044 cents** | current |
| `docs/decisions/0004-cv-interface-module.md:319-320` | ~80 mV → **0.00018 cents**, *while citing* `` `power-entry.md` `` | **stale, live** |
| `docs/decisions/0006-cv-channel-allocation.md:624` | ~80 mV → **0.00018 cents** | struck through, refutation-exempt |
| `hardware/bom.csv:37` | ~80mV → **0.00029 cents** | refuted in place, exempt |

Why the checker passes: the `forbidden` list has `"by ~80mV"` and
`"by **~80 mV**"` `[repo] config/figures.yaml:366`, but `0004` line-wraps — "by"
ends line 318 and "~80 mV" opens line 319 — so neither literal matches `[calc]`.
`0006:624` spells it `by ~80 mV` with a space, against a pattern with none.
And **no value of the cents figure is in `forbidden` at all**: not
`0.00018 cents`, not `0.00029 cents`.

The consequential one is `0004:319-320`. It carries a refutation marker ("used
to call that"), so the checker exempts the line — but the **replacement value it
offers is itself superseded**. A refutation that installs a stale number is
invisible to a checker that only looks for old values on unrefuted lines. Three
values of one quantity are live in the corpus.

*Suggested fix, outside the freeze:* add `"0.00018 cents"` and `"0.00029 cents"`
to `diode-split-rationale.forbidden`, grep for every spelling **first** per
`CLAUDE.md:27-31`, then fix what the checker names.

### 7.2 `sensor-full-scale`: the owner ADR states the refuted transfer function twice

Register: `Vout = VS*[(0.1533*P) + 0.053]`, pedestal **0.265 V, not 0.200 V**,
`owner: docs/decisions/0003-breath-sensing-path.md` `[repo]
config/figures.yaml:34-39`.

| line | text | |
|---|---|---|
| `0003:101` | "0.265–4.86 V out — see [register]" | correct |
| `0003:118` | "0.2–4.80 V … cover-page line, refuted by the transfer function inside the same document" | correct, properly refuted |
| `0003:122-123` | "**The transfer function is identical**, and it verifies against this ADR's own figures: `Vout = VS × (0.1533·P + 0.04)` at VS = 5 V is 0.7665 V/kPa with **0.20 V at zero** — the DP's published numbers exactly." | **stale, live** |
| `0003:434` | "`Vout = VS × (0.1533 · P + 0.04)`" | **stale, live** |
| `0003:552` | "full scale, 0.265–4.86 V" | correct |

Four statements of one fact inside one 811-line ADR: two right, two wrong. The
escape is a character: `forbidden` has `"(0.1533*P) + 0.04"` and
`"0.1533 x P) + 0.04"` `[repo] config/figures.yaml:40`; the document writes
`(0.1533·P + 0.04)` with a middle dot and no inner parenthesis `[calc]`. `"0.20 V
at zero"` is not in the list either — `"0.200 V at rest"` and `"0.2 V at rest"`
are.

Downstream, not separately fixed: `0003:522` and `0003:532` compute the buffer's
bottom-of-range margin against a **0.2 V floor** `[repo]`. Against the correct
0.265 V pedestal the margin is 140 mV, not 75 mV `[calc]` `0.265 − 0.125 = 0.140`
vs `0.200 − 0.125 = 0.075`. The conclusion improves, but it is derived from a
refuted number and reads as authoritative.

**This is the argument of §4.3 in one document.** The register points its `owner`
at a document the supersession convention says must not be edited in place, and
the number went stale *inside its own home*. Move `sensor-full-scale`'s owner to
`hardware/controller/carrier.md` §2, which already states it once and cites the
id at `carrier.md:357`.

### 7.3 The ADR status table disagrees with three of its own ADRs

Detailed in §4.2: `0007`, `0008` and `0011` `[repo]`. Generate the column.

---

## 8. What to do, in order

| # | action | freeze-legal | owner |
|---|---|---|---|
| 1 | Nothing moves out of `docs/decisions/`. ADRs unchanged, numbers unchanged, `docs/decisions/` stays their home | yes | restructure |
| 2 | Add §3.1's rule to `docs/decisions/README.md` and to each `notes.md` header | yes (new text) | restructure |
| 3 | Scope `notes.md` to rule 4 + the generated decision index. No assertions, no figure ownership | yes | restructure |
| 4 | Add a `binds:` header line to each of the 14 ADRs (metadata, not content) | yes | restructure |
| 5 | `tools/build-decision-index.py` — emits the per-circuit block and `README.md`'s two generated columns from `bom.csv` + `binds:` | yes (tooling) | restructure |
| 6 | Extend `check_bom()`: non-empty `adr`, resolving to a real ADR file | yes (tooling) | restructure |
| 7 | Assert no `figures.yaml` `owner:` ends in `notes.md` | yes (tooling) | restructure |
| 8 | Add delegation clauses to the §1.2 sections that lack them, in the `0006:82` form | **no** — edits ADR text | follow-up |
| 9 | Move 5 figure owners off ADRs (§4.3); create `hardware/interfaces/umbilical.md` and `hardware/module/panel.md` | **no** | follow-up |
| 10 | Fix §7.1 and §7.2 by the three-step procedure at `CLAUDE.md:27-31` — **grep every spelling first** | **no** | follow-up, urgent |
| 11 | Generate the status column; §7.3 resolves itself | yes (tooling) | restructure |
| 12 | `docs/process/` split — `CORPUS_DIRS` commit **first**, move second, call sites third | **no** | separate |

Items 8–10 are content edits and are out of scope for a move-and-split
restructure. **Item 10 should not wait for it.** Three values of the diode figure
and two of the sensor transfer function are live in the corpus right now, and the
checker says `PASS`.
