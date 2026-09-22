# D9 — the eighteen rows that left `hardware/unplaced.csv`

**Slice:** every BOM row moved out of `hardware/unplaced.csv` on 2026-09-22,
plus the counter-question — what is still in `unplaced.csv` that is drawn.
**Method:** cold. Nothing under `docs/review/**` was read except this wave's
`README.md`. Git history and `git diff` were read; the corpus was read; the
BOM was re-derived independently rather than trusted to `merge-bom.py --check`.

**Provenance:** `[repo] path:line` for a read, `[calc]` with the arithmetic,
`[git] <sha>` for history, `[test]` for a command I ran and its output.

---

## What actually moved

`[git] 0e68f25` removed 16 rows from `unplaced.csv`; `[git] 04b5208` removed 2
more. `[git] b32c557` edited `CABLE-UMB` in place (a note rewrite, not a move).
`PANEL` moved between two circuit fragments in `0e68f25`
(`module/panel-led/` → a new `module/panel/bom.csv`).

`unplaced.csv`: **34 rows before `04b5208`, 32 after** `[test]` wc and csv.reader.
Master: **139 rows / 390 units** `[calc]`.

| # | Row | Destination fragment | Drawn there? | Derived there? | Verdict |
|---|---|---|---|---|---|
| 1 | `U-DAC` | `module/dac8568/` | yes, as `DAC8568C` | yes | **correct** |
| 2 | `R-PRECISION` | `module/pitch-stage/` | yes, as `LT5400` | yes | **correct** |
| 3 | `J-UMBILICAL` | `module/power-entry/` | **no** | **no** | **wrong home** — D9-3 |
| 4 | `U-DIFFRX` | `module/breath-receive-stage/` | yes, as `INA828` | yes | **correct** |
| 5 | `U-LVL-MOD` | `module/digital-and-supervision/` | yes, as `74AHCT125` | yes | **correct** |
| 6 | `D-REVPOL` | `module/power-entry/` | yes, `D1 D2 D3 1N5817` | yes | **correct** |
| 7 | `U-REG-DAC` | `module/power-entry/` | yes, as `LM317LZ` | yes | **correct** |
| 8 | `R-REG-SET` | `module/power-entry/` | yes, `150R/475R 0.1%` | yes | **correct** |
| 9 | `C-REG-ADJ` | `module/power-entry/` | **half** (1 of 2) | partly | weak — D9-11 |
| 10 | `FB-IN` | `module/power-entry/` | yes, `FB1`–`FB4` | yes, owns the figure | **correct** |
| 11 | `R-GAIN-INAMP` | `module/breath-receive-stage/` | yes, as `R_G 42.2k` | **no** — derived on `breath-sense-link.md` | **split** — D9-5 |
| 12 | `R-SER-BREATH` | `interfaces/breath-sense-link/` | no (drawn on `breath-receive-stage.md` as `R2`/`R3`) | yes | **split** — D9-5 |
| 13 | `C-FILT-BREATH` | `module/breath-receive-stage/` | yes, `C_diff`/`C_cm` | **no** — derived on `breath-sense-link.md` | **split** — D9-5 |
| 14 | `C-BULK-RAIL` | `module/power-entry/` | yes, `C1`–`C4` | **refuted there** | **wrong** — D9-4 |
| 15 | `C-TIMER-LOADSW` | `module/umbilical-load-switch/` | yes | yes, owns the figure | **correct** |
| 16 | `C-GATE-LOADSW` | `module/umbilical-load-switch/` | yes, `[C-GATE 82nF]` | yes, owns the figure | **correct** |
| 17 | `J-CV` | `module/bom.csv` (board level) | no page draws a jack body | nowhere | defensible, reason false — D9-8 |
| 18 | `D-CLAMP-BREATH` | `module/breath-receive-stage/` | yes, once | yes | fragment right, **drawing edit wrong** — D9-1, D9-2 |
| (+) | `PANEL` | `module/panel/` | n/a | ADR 0004 owns it | best available home |

Eleven of eighteen are clean. Seven carry a finding, and two of those are in
the one row the fix batch handled last and most carefully.

---

## D9-1 — `D-CLAMP-BREATH`'s second label names the wrong part **(high)**

`[git] 04b5208` edited two lines of `breath-receive-stage.md` to write the
refdes into the drawing, then moved the row. The **first** edit is right. The
**second** is not.

`[repo] hardware/module/breath-receive-stage/breath-receive-stage.md:107-112`

```
                                   [1k]─┼─[C 330nF]── AGND(module)
                                        │
                                   [D-CLAMP-BREATH BAV99]── ±12 V
                                        │
                                   BREATH jack
```

That is the **breath output jack**, not the in-amp input pair. Every other
output jack on this module draws the identical structure and labels it
`D-JACK-CLAMP`:

- `[repo] hardware/module/pitch-stage/pitch-stage.md:48` — `[D-JACK-CLAMP BAV99]── ±12 V`
- `[repo] hardware/module/mod-channels/mod-channels.md:58` — same string
- `[repo] hardware/module/breath-output-stage/breath-output-stage.md:84` — same string, **on this same breath jack**

The counts settle it. `J-CV` qty **6**, `R-OUT-PROT` qty **6**, `D-JACK-CLAMP`
qty **6** `[repo] hardware/bom.csv` — six jacks: pitch, breath, MOD 1–4. The
breath jack is one of the six, so its clamp is one of `D-JACK-CLAMP`'s six.
`D-CLAMP-BREATH` is qty **2** and its own description reads *"Clamp diodes on
the BREATH and AGND legs **at the in-amp inputs**"* `[repo] hardware/bom.csv:84`.
Two legs, two diodes, both accounted for by line 67.

Consequences, all live:

1. The breath output jack now has **no `D-JACK-CLAMP` instance drawn**, while
   the row still claims six.
2. `D-CLAMP-BREATH` appears three times for a quantity of two.
3. The claim was written into the BOM: `D-CLAMP-BREATH`'s note now ends
   *"It was drawn on breath-receive-stage.md **TWICE** and the drawing never
   wrote the refdes"* `[repo] hardware/bom.csv:84`. It was drawn once. A wrong
   finding filed as handled is the class `CLAUDE.md` says is worse than a wrong
   finding.
4. `[repo] docs/reference/pcb-pipeline.md:164-166` is the source of "twice" —
   it says `D-CLAMP-BREATH` "**is drawn** — twice ... as *"BAV99 to ±12 V, both
   legs"*". Note that the quoted string appears only on line 67. The second
   BAV99 does not match that quotation, and nothing checked.

**Second-order:** the two pages draw this node differently.
`breath-output-stage.md:84` puts the clamp **before** `R-OUT-PROT` (op-amp
side), which is what `D-JACK-CLAMP`'s note demands — *"MOVED to the op-amp side
of the 1k"* `[repo] hardware/bom.csv:107`. `breath-receive-stage.md:108-110`
puts it **after** the 1 kΩ, jack side — the position the row says was
abandoned. The line that got mislabelled is also the line that is stale.

**What would settle it:** ask whether the module has 6 jack clamps or 7. If 6,
line 110 must read `D-JACK-CLAMP` and move above the 1 kΩ.

---

## D9-2 — the drawing edit broke the drawing **(high)**

The line-67 edit inserted 17 characters ahead of `BAV99` without re-padding the
tail of the line, so the arrow no longer lands on the conductors it points at.

`[calc]` column indices of `│ ┼ ┤` glyphs, before and after `04b5208`:

| line | before | after |
|---|---|---|
| 65 `───┼─┼───` | 68, 70 | 68, 70 |
| 66 `│ │` | 68, 70 | 68, 70 |
| **67 `◄────┼─┤`** | **68, 70** | **85, 87** |
| 68 `│ │` | 68, 70 | 68, 70 |

The clamp's arrow now terminates in whitespace 17 columns to the right of the
`BREATH`/`AGND` pair. `CLAUDE.md` warns that an ASCII drawing's gutter is
load-bearing; this is the same hazard from the other side — an edit made *to*
a drawing to satisfy a refdes search, which cost the drawing its topology.

---

## D9-3 — `J-UMBILICAL` went to a page that neither draws nor derives it **(high)**

`[test]` grep for `J-UMBILICAL` and `etherCON` across `hardware/**/*.md` — `power-entry.md`
mentions the etherCON **once**, in a parenthetical about shield bonding
`[repo] hardware/module/power-entry/power-entry.md:130`. The connector on its
Interfaces table is `J-PWR-EURO`, the Eurorack IDC `[repo] :26`, and the
drawing's only umbilical is a net leaving the board, `UMBILICAL +12V ──►
instrument` `[repo] :73`. Nothing on the page names the part, its bore, its
flange or its mounting pattern.

Where the connector actually is named as a circuit's own boundary object:
`[repo] hardware/module/panel/panel.md:37` — `| etherCON flange | — | — |
panel-width | The umbilical connector's panel cutout |`. Where its value is
derived: ADR 0004 §"Connector: Neutrik etherCON, both ends"
`[repo] docs/decisions/0004-cv-interface-module.md:673-731`, plus the banked
drawing and datasheet the row cites.

**And the quantity is split across two boards.** The row is qty 2, described as
*"module panel and instrument tail"* `[repo] hardware/bom.csv`. The instrument
unit is carried by the tail end cap and an internal backing plate
`[repo] docs/decisions/0009-enclosure-construction.md:609-616`;
`ENDCAP-TAIL` and `MECH-BACKPLATE` are still in `unplaced.csv` naming it. So
one of the two units is not a module part at all, and both now sit in a module
circuit fragment with `category=module`.

This matters beyond filing: `[repo] docs/reference/pcb-pipeline.md:359` now
directs anyone reading a dimension off the DXF to *"`hardware/module/power-entry/bom.csv`'s
`J-UMBILICAL` row ... this page cites them rather than restating them"* — a
citation pointed at a circuit that derives nothing about the part.

---

## D9-4 — `C-BULK-RAIL`'s new owner contradicts it, twice **(high)**

The row: `100uF (+12V) / 47uF (-12V, +5V) 25V electrolytic`, qty 4, with
*"NOT 47uF on every rail ... 100uF on +12V balances the decay"*
`[repo] hardware/bom.csv`.

Its destination page says the opposite in both registers:

- drawing: `[C1 47µF]`, `[C2 47µF]`, `[C3 47µF]`, `[C4 47µF]`
  `[repo] hardware/module/power-entry/power-entry.md:42,49,75,77`
- prose: *"**Entry bulk is 4 × 47 µF**, which is 2–5× the surveyed norm"*
  `[repo] :190`

Both predate the move (`[git] 7a5236c` wrote the row's 100 µF; `[git] 9daec7f`
wrote the page's 47 µF), so the move did not create the conflict — it made the
page that refutes the row the page that owns it, which is exactly the state the
filing rule exists to prevent. The staleness checker cannot see it: it greps
figure values, and this quantity is in no register entry.

**Also arithmetically incomplete.** The description names three rails for a
quantity of four. `C2` sits on the `D2`/`FB2` umbilical branch `[repo] :49`,
which is neither −12 V nor +5 V and is the branch carrying `umbilical-current`.

---

## D9-5 — one value table, three parts, two fragments **(medium)**

`breath-sense-link.md` carries a `## Component values` table that was *"Moved
verbatim from `breath-receive-stage.md`, 2026-09-21"*
`[repo] hardware/interfaces/breath-sense-link/breath-sense-link.md:133-157`:

| Ref in that table | Value derived there | BOM row | Where it was filed |
|---|---|---|---|
| `R2`, `R3` | 10 kΩ 0.1 % | `R-SER-BREATH` | `interfaces/breath-sense-link/` |
| `C_diff`, `C_cm` ×2 | 15 nF / 1.5 nF, **482 Hz** pole | `C-FILT-BREATH` | `module/breath-receive-stage/` |
| `R_G` | 42.2 kΩ, `G = 1 + 50k/R_G` = 2.185 | `R-GAIN-INAMP` | `module/breath-receive-stage/` |

The same table, in the same section, split two ways in the same commit
`[git] 0e68f25`. All three parts are **drawn** on `breath-receive-stage.md`
`[repo] :69,71,73,75,77,86` and all three are **derived** on
`breath-sense-link.md`, which also owns `inamp-full-scale`
`[repo] config/figures.yaml`, the figure the gain derivation lands on.

Under the governing rule ("the page that derives") all three belong at
`interfaces/breath-sense-link/`. Under "the page that draws" all three belong at
`module/breath-receive-stage/`. No reading puts them in two places. The
inconsistency is invisible to every check, because both destinations are valid
fragments and the master is the union either way.

**A premise in the slice brief is not borne out:** `R-SER-BREATH` is not "one
leg on each board". It is the **module-side pair**, `R2` and `R3`, both at the
in-amp `[repo] breath-receive-stage.md:69,71`. The instrument-side pair is a
separate row, `R-SER-BREATH-INST` (`R1`, `R1b`, 1 kΩ, qty 2), drawn on
`carrier.md` `[repo] hardware/carrier/carrier.md:116,134`. Two rows, two
boards, two units each.

**A second premise is also not borne out:** `R-PRECISION` is not shared between
`pitch-stage` and `mod-channels`. `pitch-stage.md` draws it, names two of four
sections, and derives its ratio, its tempco contribution and its layout hazard
`[repo] hardware/module/pitch-stage/pitch-stage.md:35,53,80,127,287,309`.
`mod-channels.md` names the LT5400 once, as the arithmetic route it describes
and then *does not take* — it adopts eight discrete resistors
`[repo] hardware/module/mod-channels/mod-channels.md:82-87`, and its fragment
holds `R-MODGAIN, 10k / 30k 1% metal film` `[repo] hardware/module/mod-channels/bom.csv`.
`pitch-stage` is the right and only home. **No finding.**

---

## D9-6 — two rows still in `unplaced.csv` are drawn, derived and tabulated **(medium)**

Answering the other direction. Of the 32 remaining rows, **two are drawn on a
schematic page under local labels**, which is the exact defect class
`0e68f25` set out to clear — on a board it cleared, in a fragment it never
opened (`breath-output-stage/bom.csv` is untouched by both commits `[git]`).

### `R-BREATH-SUM` — `10k / 40.2k 1%`, qty 2, "Summer input and feedback - the fixed x4"

Drawn `[repo] hardware/module/breath-output-stage/breath-output-stage.md:67,82`
as `[R-IN 10k]` and `[R-FB 40k]`. Tabulated `[repo] :148-149`:

| Ref | Value | Job |
|---|---|---|
| **R-IN** | 10 kΩ 1 % | Summer input |
| **R-FB** | 40.2 kΩ 1 % | Fixed ×4. Same E96 part as `R-MODGAIN` |

Both values, both jobs, verbatim against the row's `part` and `description`
fields. No `R-IN` or `R-FB` row exists anywhere `[test]` grep for `^R-IN,` and `^R-FB,` over all fragments returns only `R-GAIN-FLOOR`, so `R-BREATH-SUM` *is* their row.

> **Why a grep missed it, worth recording:** the row spells `40.2k`; the page
> spells `40.2 kΩ` in the table and `40k` in the drawing. A literal search for
> the row's own spelling returns nothing on that page `[test]`. This is
> `CLAUDE.md` §2's first trap — *write the pattern in the spelling of the file
> it must match* — reappearing in the assignment problem rather than the
> forbidden-pattern problem.

### `R-BREATH-OFF` — `21.0k / 95.3k 1%`, qty 2, "The two offset legs into the summing node"

Drawn `[repo] :72,74` as `[R-OFF 21.0k]` and `[R-OFFNEG 95.3k]`, tabulated
`[repo] :151-152` as *"Variable positive leg"* and *"Fixed negative leg from
−12 V"*, and given a whole derivation section with a three-row transfer table
and a rail-sensitivity calculation `[repo] :120-138`.

Both rows are **already named** as module-netlist parts still in `unplaced.csv`
by `[repo] docs/reference/pcb-pipeline.md:159-160`. The list was read for
`J-CV` and `D-CLAMP-BREATH` and not for the two rows beside them in the same
sentence.

### The rest of the 32

`[test]` part-number and value-token sweep of every `unplaced.csv` row against
every `hardware/**/*.md`, plus targeted greps for `MT165`, `QMI8658C`,
`RM67162`, `T-Display`, `USBLC6`, `NE8MC`, `WS2815`, `420`, `14mm`.

No other row is drawn. The remainder is honest: mechanical (oak, acrylic,
adhesives, fasteners, end caps, U-bolt, backplate), the breath-path mechanics
(tube, PTFE plug, mouthpiece), cables and shells, the board blanks, the bench,
spares, four `not-needed` rows that are onboard the dev board, and
`U-TVS-MODULE` — a module netlist part that genuinely no page draws, correctly
filed.

Two borderline cases, reported rather than claimed:

- **`KNOB-BREATH`** — *"Knob to match the pot shaft - **14mm MAX** diameter"*.
  That number is derived, with arithmetic, on `panel.md`: *"Three pots across
  50.50 mm with 3 mm gaps needs **≤14 mm knobs**; 15 mm already gives 51 mm and
  does not fit"* `[repo] hardware/module/panel/panel.md:68-69`. A knob is not
  drawn in a schematic, but under "the page that derives its value" this row has
  a home, and `module/panel/bom.csv` now exists to take it.
- **`LED-SIDE`** — the WS2815 strip. `led-strip-drive.md` names it only as a
  peer `[repo] hardware/carrier/led-strip-drive/led-strip-drive.md:25`; the
  reel, the density and the 420 mm cut are derived in ADR 0014
  `[repo] docs/decisions/0014-lighting.md:29,68,246-254`, which is not a
  schematic page. Correctly unplaced by the letter of the rule.

**Answer to the counter-question: 2 of 32 are drawn, both on
`breath-output-stage.md`, both already named in `pcb-pipeline.md`.**

---

## D9-7 — three live stale counts of the quantity the fix changed **(medium)**

The signature defect, in the documents that announce the fix. Current truth,
derived independently `[test]` csv.reader over the master, the 25 fragments and `unplaced.csv`:

| | Rows | Units |
|---|---|---|
| `hardware/bom.csv`, the generated master | **139** | **390** |
| In the per-circuit fragments (25 files) | **107** | **323** |
| In `hardware/unplaced.csv` | **32** | **67** |

Against that:

1. **`[repo] docs/reference/repo-maintenance.md:204`** — *"`hardware/unplaced.csv`
   holds the **50 rows of 138** that no schematic page **names**."* Two waves
   stale. It also still carries *"six identical jack-protection networks drawn
   three times, and nineteen decoupling capacitors with no home"* — a sentence
   `0e68f25` deleted from `hardware/README.md` as wrong, left standing here.
   Both jack-protection rows (`R-OUT-PROT`, `D-JACK-CLAMP`) and the jacks
   themselves are now placed, and no decoupling row remains in `unplaced.csv`.
   This is the file `CLAUDE.md` names as the one to read before touching
   `bom.csv`, and the paragraph sits four lines below the rule this slice
   audits.
2. **`[repo] hardware/README.md:72`** — *"It was 50 rows and is now **34**."*
   True when written `[git] 0e68f25`, made false six hours later by
   `[git] 04b5208`, which moved two more rows and did not touch this file.
3. **`[repo] docs/reference/pcb-pipeline.md:153-174`** — the whole block:
   master `138 / 388`, fragments `104 / 313`, unplaced `**34** / **75**`; then
   *"**`J-CV` ×6** (the CV jacks — the module's whole output connector set),
   `U-TVS-MODULE`, `D-CLAMP-BREATH` ×2, `R-BREATH-SUM` ×2 and `R-BREATH-OFF`
   ×2. **Thirteen units.**"*; then *"its row is **still in `unplaced.csv`**"*;
   then *"**The CV jacks are not** [placed], and neither are the four rows
   beside them."*
   `[git] 04b5208` is the commit that placed `J-CV` and `D-CLAMP-BREATH`, and
   its own message narrates both moves. It did not touch this file. The correct
   remainder is **3 rows / 5 units**: `U-TVS-MODULE` ×1, `R-BREATH-SUM` ×2,
   `R-BREATH-OFF` ×2 `[calc] 13 − 6 − 2 = 5`.

Item 3 is the sharpest instance this slice found of the project's named
failure: the paragraph that explains why a stale `unplaced.csv` is dangerous
is stale, about `unplaced.csv`, because of the commit that fixed it.

---

## D9-8 — `J-CV` at board level: defensible, but the stated reason is false **(low)**

The row's own note records the reasoning: *"Filed at BOARD level, beside
`R-OUT-PROT`, because three circuits drive these six jacks and **`panel.md`
owns only the cutouts** — no single circuit page derives the connector"*
`[repo] hardware/bom.csv`.

`panel.md` says the opposite of itself being cutouts-only, in its opening:

> *"This page used to call itself 'a board-level page, not a circuit' ... **It
> is a circuit directory like the others**; the contradiction is resolved that
> way rather than by deleting the graph node, because a panel-mounted part is
> where another circuit's net ends, and **every one of this module's jacks,
> pots and the toggle is a panel-mounted part**."*
> `[repo] hardware/module/panel/panel.md:10-17`

Its Interfaces table then lists all six jacks by name as this circuit's objects
`[repo] :32-34`, and the `J-CV` row's content is **entirely** the mechanics
that `panel.md` is the page for: bushing ⌀6.0 mm with 4.5 mm of thread, a
6 mm nominal hole, 5.5 mm panel face to body front, body 9 × 9 × 8.3 mm, and a
note to leave a void in the PCB under the barrel. Only the pinout is electrical,
and no page uses it.

**Against:** `R-OUT-PROT` ×6 and `D-JACK-CLAMP` ×6 already sit at board level
for the same "three circuits" reason, so `J-CV` beside them is consistent
practice; and the repo's other panel-mounted parts (`POT-GAIN`, `POT-OFFSET`,
`POT-RESP`) live with the circuit that derives their *electrical* value, which
`panel/` is not.

**What settles it:** `hardware/module/` has a BOM fragment and **no
`circuit.yaml`** `[test]` `ls hardware/module/*/circuit.yaml`, so it is not a
node in the dependency graph, and `module.md` says of itself *"This page is a
board page ... **nothing here restates**"* a value
`[repo] hardware/module/module.md:6-7`. Anything filed there is, by the page's
own statement, derived nowhere. That is not a reason to move `J-CV` on its own
— it is a reason to decide whether the board-level fragment is a legitimate
third category or an `unplaced.csv` with a better name. Three rows already
depend on the answer.

---

## D9-9 — `module.md`'s "Fixed" bullet is a partial list **(low)**

`[repo] hardware/module/module.md:38-44` credits *"The DAC, the in-amp, the
LM317, the entry diodes, the beads, the bulk caps, both load-switch capacitors
and the level shifter"* — eight of the sixteen rows `0e68f25` moved. Missing:
`R-PRECISION` (the LT5400, which `hardware/README.md:75` does name),
`J-UMBILICAL`, `R-GAIN-INAMP`, `C-FILT-BREATH`, `R-SER-BREATH`, and the
`R-REG-SET`/`C-REG-ADJ` pair if "the LM317" is read as the regulator alone.

It also says they are *"filed with the circuits that derive them"* on **this
board**; `R-SER-BREATH` went to `hardware/interfaces/`, off the board page this
bullet belongs to. And `J-CV` — this board's entire output connector set,
which left `unplaced.csv` six hours later — is not mentioned at all, on the
page whose job is to say what the board carries.

---

## D9-10 — `umbilical-load-switch.md` still calls a fixed row wrong **(low)**

`[repo] hardware/module/umbilical-load-switch/umbilical-load-switch.md:284-287`,
present tense: *"the **0805 C0G package in `bom.csv` is wrong** for 10 µF by
three orders of magnitude"*. The row it now owns reads
`THROUGH-HOLE radial or 1210 ceramic` `[repo] hardware/bom.csv`. The row was
corrected; the page that owns it still reports the defect as live. Low harm,
but it is a page asserting a fault in a file it is the authority for.

---

## D9-11 — `C-REG-ADJ` is qty 2 and only one is drawn **(low)**

The row is *"10uF / 1uF ceramic or tantalum"*, qty 2, *"ADJ bypass and output
cap"*, and its whole argument is the ADJ bypass: *"ADJ bypass drops output
noise to ~50 µV RMS ... ripple rejection goes from 65 dB typ to 66 min / 80 typ
**with a 10 µF capacitor from ADJUSTMENT to ground**"* `[repo] hardware/bom.csv`.

The destination drawing shows one capacitor, `[C 1µF]` on the LM317 output
`[repo] hardware/module/power-entry/power-entry.md:47`. The 10 µF ADJ bypass —
the unit the row exists to justify — is in no drawing in the corpus
`[test]` grep for `ADJ` and `10 µF` on that page. The move placed a row half of whose
quantity is still undrawn, which is the condition `unplaced.csv` counts.

---

## D9-12 — the rule has two spellings, and this audit turns on which **(low)**

- `[repo] CLAUDE.md:171` — *"holds the rows no schematic page **names**"*
- `[repo] docs/reference/repo-maintenance.md:204` — *"that no schematic page **names**"*
- `[repo] hardware/README.md:69` — *"holds the BOM rows **no schematic page derives**"* (changed by `0e68f25`)

`repo-maintenance.md:200-202` states the placement rule as *"whose page
**derives** its value — not where it is mentioned, not where it is mounted"*,
and then defines `unplaced.csv` by "names" four lines later. Under "names",
`R-SER-BREATH` is misfiled (`breath-sense-link.md` does not draw `R2`/`R3`);
under "derives", `C-FILT-BREATH` and `R-GAIN-INAMP` are. The two definitions
disagree about D9-5 and about `J-CV`. One of the three files should change.

---

## D9-13 — the BOM's mechanical consistency: clean **(no finding)**

Proved independently rather than by `merge-bom.py --check`.

- **Union.** Multiset of the 139 master rows vs. the 25 fragments + `unplaced.csv`:
  `in master not in any fragment: []`, `in fragments not in master: []`,
  `duplicate refdes across fragments: {}` `[test]` csv.reader + collections.Counter.
- **Byte order.** Rebuilt the master in `ORDER` with `csv.writer(lineterminator="\r\n")`,
  honouring `NO_PARTS` for the absent `module/link-supervision/bom.csv`:
  **byte identical, 131 725 bytes** `[test]`.
- **Shape.** Every file — master, `unplaced.csv` and all 25 fragments — is
  11 columns, CRLF throughout (`lf == crlf` on every file), and ends with a
  newline `[test]`.
- **Row-count history across the batch** `[test]` per-commit csv.reader: master
  138/388 through `6645fb7`; 139/390 from `79f5c4a` (which added `R-LED-PD` ×2
  to the fragment **and** regenerated the master in the same commit — checked
  because a +1 row across a pure move looked wrong, and it is not);
  `unplaced.csv` 34 → 32 at `04b5208`, master unchanged. **The 18 moves are
  net-zero on the master, as moves must be.**
- **Fields.** Every moved row kept its `qty`, `status`, `adr` and `category`
  byte-for-byte `[test]` git diff of the removed and added lines. Quantities
  reconcile with the drawings in every case checked except `C-REG-ADJ` (D9-11)
  and `J-UMBILICAL` (D9-3): `D-REVPOL` 3 = `D1`,`D2`,`D3`; `FB-IN` 4 =
  `FB1`–`FB4`; `C-BULK-RAIL` 4 = `C1`–`C4`; `C-FILT-BREATH` 3 = one `C_diff`
  + two `C_cm`; `R-REG-SET` 2 = 150R + 475R; `R-SER-BREATH` 2 = `R2`,`R3`;
  `D-CLAMP-BREATH` 2 = both legs on line 67.

Two smaller graph observations, noted not filed: `hardware/module/dac8568/circuit.yaml`
declares **no `adr:` edge at all** while now owning an `adr=0006` row, and
`hardware/module/` owns a fragment with no `circuit.yaml` (see D9-8).

---

## D9-14 — "most of it is mechanical" **(low, arguable)**

`[repo] hardware/README.md:81` — *"What remains is genuinely unplaced, and
**most of it is mechanical** — the oak, the acrylic, the adhesives, the
fasteners."* By the `category` column: `controller` **13**, `mechanical` **11**,
`module` **7**, `tooling` **1** `[calc]`. Counting rows that are physically
mechanical regardless of category (adding `TUBE`, `MECH-PTFE`, `MECH-MOUTH`,
`MECH-WINDOW`, `CAP1-n`) gives **16 of 32** — exactly half. "About half" is
supportable; "most" is not, and it was not true at 34 rows either.

---

## Summary

**Correct and complete:** 11 of the 18 moves — `U-DAC`, `R-PRECISION`,
`U-DIFFRX`, `U-LVL-MOD`, `D-REVPOL`, `U-REG-DAC`, `R-REG-SET`, `FB-IN`,
`C-TIMER-LOADSW`, `C-GATE-LOADSW`, and `PANEL` into the new `module/panel/`.
The four with a tracked figure owned by the destination page
(`ferrite-bias-impedance`, `dac-rail`, `loadswitch-timer`,
`loadswitch-gate-cap`) are the cleanest, which is an argument for filing by
figure ownership where a figure exists.

**Wrong or unsupported home:** `J-UMBILICAL` (D9-3), `C-BULK-RAIL` (D9-4), the
`R-SER-BREATH` / `C-FILT-BREATH` / `R-GAIN-INAMP` split (D9-5), `J-CV` on a
false stated reason (D9-8).

**Wrong edit:** the second `D-CLAMP-BREATH` label renames one of
`D-JACK-CLAMP`'s six (D9-1), and the edit that added it broke the drawing's
alignment (D9-2). Both are in the row the batch handled most deliberately.

**Incomplete:** two drawn rows left in `unplaced.csv` (D9-6), and three live
stale counts of the quantity the batch changed (D9-7), one of them in the
paragraph that exists to warn about exactly this.

The wave's premise holds for this slice. The fixes are mostly right; what they
did not do is land everywhere the number they changed is read.
