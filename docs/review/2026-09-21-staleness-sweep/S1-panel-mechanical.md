# S1 — Panel, enclosure and physical dimensions

**Staleness sweep, 2026-09-21.** Domain: the module panel, the instrument
enclosure, and every physical dimension in the design corpus.

**Corpus audited:** `hardware/**`, `docs/decisions/**`, `config/**`,
`docs/reference/**`, `ROADMAP.md`, `README.md`, `firmware/README.md`.
`docs/review/**`, `docs/log/**` and `docs/research/**` were read for evidence
but are dated records and are **not** reported as stale.

**Nothing was edited.** This file is the only thing written.

Indexed by disputed fact. Each entry lists every corpus file that states the
fact and what each one says.

---

## Summary

| # | Disputed fact | Rank |
|---|---|---|
| [F1](#f1) | Module panel height budget: **97 mm derived** vs **107 mm asserted** — both still in ADR 0004 | **Showstopper** |
| [F2](#f2) | Number of panel controls: **three pots** vs **two knobs** | **Showstopper** |
| [F3](#f3) | Instrument mass: **~778 g** vs **~825 g**, two `### Mass` sections in ADR 0009 | High |
| [F4](#f4) | Service header behind the tail cover: **2×3 / six-pin** vs **2×5** | High |
| [F5](#f5) | Acrylic side thickness **4 mm** — sole source is the stale mass table; BOM says TBD | High |
| [F6](#f6) | etherCON bracing: "good practice **at 8HP**" vs "**At 10HP**" | Medium |
| [F7](#f7) | "Comfortable **at 8HP**" in the M4 paper-check row | Medium |
| [F8](#f8) | ADR 0004: "kept the panel inside **10HP** rather than 10 or 12" | Medium |
| [F9](#f9) | Underside key count: "**three or four** … for the left thumb" vs 4 LT + 3 RT | Medium |
| [F10](#f10) | BOM `PCB-MODULE`: description still lists a **deleted watchdog**, note still asserts 8.27 mm / 40.34 mm | Medium |
| [F11](#f11) | ADR 0009: "**no coating anywhere in the BOM**" vs `MECH-COAT` | Medium |
| [F12](#f12) | ADR 0009 tail face: "**Two openings**", three listed | Low |
| [F13](#f13) | "Knobs fit the range, **firmware shapes the feel**" vs `POT-RESP` | Medium |
| [F14](#f14) | BOM `PANEL` note opens "**8HP not 6HP**" | Low |

| # | Asserted but never derived | Rank |
|---|---|---|
| [N1](#n1) | **~110 mm usable** — the denominator of the whole budget, derived nowhere in the corpus | High |
| [N2](#n2) | The new **97 mm** carries **zero inter-element clearance**, and the reason given for the saving is not where the saving came from | High |
| [N3](#n3) | **≤14 mm knobs** — the calc leaves 1.25 mm of panel edge each side and says so nowhere | Medium |
| [N4](#n4) | The eased etherCON-notch **web is never recomputed** (9.5 mm implied) | Low |
| [N5](#n5) | **Panel mounting holes / slots are specified nowhere** for a laser-cut part | Medium |
| [N6](#n6) | The **4 mm panel-thickness limit vs a 6 mm oak face** is stated four times and resolved nowhere | High |
| [N7](#n7) | **12 × 40 mm** service cover was sized for the withdrawn ten-pin header | Low |
| [N8](#n8) | ADR 0009 mass table: the aluminium row implies **3.01 g/cm³**, and assumes a plate thickness that is open | Medium |
| [N9](#n9) | The length table sums **centre-to-centre** spans; end cap half-widths are never added | Low |

[Verified clean list](#verified-clean) at the end — fourteen facts that are
consistent everywhere they appear.

---

<a name="f1"></a>
## F1 — Panel height budget: 97 mm derived, 107 mm still asserted twice

**Rank: Showstopper.** Two incompatible specifications of the same panel, 85
lines apart in the same document. Today's commit
(`745af8c`) states in its own message that the 107 mm figure "is asserted twice
and derived nowhere. So this commit derives it" — and then leaves **both**
assertions standing. This is the project's chronic failure recurring inside the
commit that was about that failure.

**Says 97 mm (the derived budget):**

- `docs/decisions/0004-cv-interface-module.md:661-667`:
  > | Label / title band | 5 mm |
  > | **Three pots across** — gain, offset, response | 22 mm |
  > | Jacks, 3 rows × 2 columns at 13 mm pitch | 39 mm |
  > | etherCON (31 mm tall) with the toggle and LED beside it | 31 mm |
  > | **Total** | **97 mm against ~110 mm — 13 mm spare** |

- `hardware/module/breath-output-stage.md:277-279`:
  > "The derived layout is in ADR 0004 and comes to **97 mm against ~110 mm,
  > 13 mm spare**."

- `hardware/bom.csv:20` (`PANEL`):
  > "Derived budget: 5 label + 22 pots + 39 jacks (3 rows x 2 cols @13mm) + 31
  > etherCON-with-toggle-and-LED-beside-it = 97mm, 13mm spare"

**Says 107 mm (the withdrawn assertion), in the same ADR:**

- `docs/decisions/0004-cv-interface-module.md:585` — the §"Panel, top to
  bottom" layout section, which is the closest thing the project has to a panel
  specification:
  > "write-on strip. Roughly 107 mm of ~110 mm usable height — full but
  > workable."

- `docs/decisions/0004-cv-interface-module.md:500` — the declined octave switch:
  > "Plus a toggle on a panel already at 107 mm of ~110 mm usable."

**And the same ADR describes the 107 mm as already retired:**

- `docs/decisions/0004-cv-interface-module.md:649-650`:
  > "It also found that **this ADR's own '107 mm of ~110 mm usable' figure is
  > asserted twice and derived nowhere**"

So ADR 0004 simultaneously states 107 mm twice, states 97 mm once, and states
that the 107 mm is a known defect. A reader landing on §"Panel, top to bottom"
— the section named after the thing it describes — gets the withdrawn number
with no marker.

**Related, same section:** `:585` also still describes the panel content as
"Connector, power switch and LED … **two breath knobs**, then six jacks in two
columns", which is F2.

---

<a name="f2"></a>
## F2 — The panel has three pots, or two knobs

**Rank: Showstopper.** `POT-RESP` was added in `efebba9`; the pot count is the
constraint that forced 8HP → 10HP and set the 14 mm knob cap. Five corpus files
still describe a two-control panel.

**Says three:**

- `hardware/bom.csv:84` (`KNOB-BREATH`), qty column: **`3`**, part field
  "Knob to match the pot shaft - **14mm MAX diameter**", description "Knobs for
  the breath gain, offset **and response** pots", note "2026-09-21: THREE, not
  two - POT-RESP added."
- `hardware/bom.csv:80` (`POT-RESP`), qty 1, "50k linear, 9mm vertical, centre
  detent … PROPOSED 2026-09-21".
- `docs/decisions/0004-cv-interface-module.md:664`: "**Three pots across** —
  gain, offset, response | 22 mm".
- `docs/decisions/0004-cv-interface-module.md:654`: "Then `POT-RESP` was added
  … making three controls."
- `hardware/module/breath-output-stage.md:267`: "| Panel | **A third pot and a
  third knob** |".

**Says two:**

- `docs/decisions/0004-cv-interface-module.md:583-585` (§"Panel, top to
  bottom"):
  > "Connector, power switch and LED — the system's only power switch, since the
  > instrument has none — **two breath knobs**, then six jacks in two columns"
- `README.md:47`:
  > "- **Breath** — dedicated, 0–10V, with panel knobs **for gain and offset**"
- `ROADMAP.md:51` (E10):
  > "Analog breath stage: in-amp receiver with `REF` grounded, **gain/offset
  > knobs**. … then gain, then the panel offset, in that order"
- `docs/decisions/0006-cv-channel-allocation.md:273-274`:
  > "**Order is gain first, then offset.** Scale how much of the 0–10V span the
  > breath covers, then position where the floor sits."
  (ADR 0006 is the ADR the BOM cites as `POT-RESP`'s owning decision — row 80's
  `adr` column is `0006` — and ADR 0006 does not mention the control at all.)
- `hardware/module/breath-receive-stage.md:260-272` — the commissioning
  procedure, three numbered steps, none of them the response control.

`ROADMAP.md` and `README.md` contain **no** occurrence of `POT-RESP`, "response
control" or a third knob anywhere. Neither does ADR 0006, which owns the row.

---

<a name="f3"></a>
## F3 — Instrument mass: ~778 g or ~825 g

**Rank: High.** `docs/decisions/0009-enclosure-construction.md` has **two
sections both titled `### Mass`**, 12 lines apart, giving different totals for
the same instrument.

**First (`:163-172`), keyed to width:**

> | Width | Mass |
> | 2.00 in | ~735 g (1.62 lb) |
> | **2.25 in** | **~778 g (1.72 lb)** |
> | 2.50 in | ~825 g (1.82 lb) |

**Second (`:175-188`), presented as current:**

> "Rough estimate at this envelope:"
> | Aluminium top plate, 2 mm | 157 |
> | Oak top, 6 mm | 131 |
> | Oak bottom, 8 mm | 174 |
> | Acrylic sides, 2 × 4 mm | 164 |
> | Electronics and hardware | 200 |
> | **Total** | **~825 (1.8 lb)** |

The second table's total is *exactly* the first table's **2.50 in** row. Git
confirms why: the breakdown table entered at `facc305` ("Width 2.5in; envelope
complete"), and `b005232` ("Width 2.25in") added the comparison table above it
without removing it. **The `~825 g` breakdown is a 2.5-inch calculation
presented as "this envelope" on a 2.25-inch instrument**, and it is the only
component-level mass breakdown in the project — so the wrong one is the one
anything downstream would use. See also [N8](#n8).

---

<a name="f4"></a>
## F4 — The service header is 2×3, and one page still says 2×5

**Rank: High.** A number differs, and it sizes a cover cut into a bonded body.

**Says six pins / 2×3:**

- `docs/decisions/0009-enclosure-construction.md:303-305`: "a screwed service
  cover on the tail underside … over a **six-pin** header on the carrier:
  `U0TXD`, `U0RXD` and `GND` for each board."
- `hardware/bom.csv:97` (`HDR-SERVICE`): "2x3 2.54mm pin header … **SIX pins,
  not ten.**"
- `hardware/controller/carrier.md:673`: "**`HDR-SERVICE` is therefore 2×3, six
  pins, not 2×5**".
- `hardware/controller/carrier.md:785` table row: "| `HDR-SERVICE` | **2×3** |
  … | `[repo] bom.csv`, **settled** |".

**Says 2×5:**

- `hardware/controller/carrier.md:871-872`:
  > "ADR 0003 wants a replaceable wear part and a trap 'clearable without
  > disassembly'; **ADR 0009 gives a 12 × 40 mm cover over a 2×5 header.**"

`carrier.md` contradicts itself twice over — and misattributes the 2×5 to
ADR 0009, which says six. The passage is load-bearing: it is the argument that
`SKT-BREATH` may be decoration.

---

<a name="f5"></a>
## F5 — Acrylic sides are 4 mm, on the authority of a stale table

**Rank: High.** The 49 mm internal width is the number that decides whether the
carrier board and the side channels can coexist, and its entire provenance is
one row of the superseded mass table from F3.

**States 4 mm:**

- `docs/decisions/0009-enclosure-construction.md:184`: "| Acrylic sides,
  2 × 4 mm | 164 |" — inside the `### Mass` section that is a 2.5-inch
  leftover.

**Depends on it:**

- `hardware/controller/carrier.md:821-825`:
  > "**Where they go is the problem.** `[calc]` 57 mm external less 2 × 4 mm
  > acrylic `[repo] 0009` = **49 mm internal**. `PCB-CARRIER` at 45 mm leaves
  > **2 mm per side** … **A 45 mm-wide carrier and open side channels are still
  > mutually exclusive**"
- `hardware/controller/carrier.md:845`: "the U-bolt in **49 mm of internal
  width** and ~20 mm of cavity."

**Contradicts it:**

- `hardware/bom.csv:4` (`SIDE-ACRYLIC`): part field "**TBD**", note
  "Edge-lit" — no thickness, no status other than `candidate`.
- ADR 0009 states the side thickness **nowhere** in its Envelope, Width or
  Decision sections. The Z-stack at `:61-68` lists plate, oak top, cavity, oak
  bottom and thumb plate, and does not mention the acrylic at all.

So a "mutually exclusive" finding on the carrier rests on a dimension that
exists only as an input to a mass estimate for a width the project no longer
builds. `49 mm` appears in no ADR.

---

<a name="f6"></a>
## F6 — etherCON bracing: "good practice at 8HP" vs "At 10HP"

**Rank: Medium.** Wording implies a superseded decision. Both sides are in
files edited today; the ROADMAP line was edited *in the same hunk* that left
the stale clause behind.

- `ROADMAP.md:53` (E12): "**10HP panel cut**, module assembled and racked.
  etherCON braced to the PCB — good practice **at 8HP** rather than the
  structural necessity it was at 6HP."
- `docs/decisions/0004-cv-interface-module.md:691-693`: "**Brace the connector
  to the PCB anyway.** … **At 10HP** this is good practice rather than a
  structural necessity."

`git show 745af8c` shows `8HP panel cut` → `10HP panel cut` in that row with
"good practice at 8HP" untouched.

---

<a name="f7"></a>
## F7 — "Comfortable at 8HP" in the M4 paper-check row

**Rank: Medium.** Same hunk, same defect.

- `ROADMAP.md:183`: "The etherCON flange against a **50.50 mm 10HP panel** *and*
  against the 57 × 38 mm instrument tail beside the USB-C slot. **Comfortable at
  8HP**; the tail is now the tight one (ADR 0004, ADR 0009)"

The row's own numbers are current and its judgement sentence is not. Note the
judgement is now doubly wrong: per [N2](#n2), the panel is not comfortable — the
derived budget carries no clearance at all.

---

<a name="f8"></a>
## F8 — "kept the panel inside 10HP rather than 10 or 12"

**Rank: Medium.** A find-and-replace produced a sentence that contradicts
itself.

- `docs/decisions/0004-cv-interface-module.md:516-519`:
  > "**The module is dumb.** … That discipline is what kept the panel **inside
  > 10HP rather than 10 or 12**."

The original read "inside 8HP rather than 10 or 12" (`git show 745af8c`). The
sentence now claims restraint kept the panel inside the width it grew to, as
against that same width.

---

<a name="f9"></a>
## F9 — What is on the underside: three or four left-thumb keys, or seven keys

**Rank: Medium.** ADR 0009's opening description of the instrument predates the
settled key layout and contradicts the rest of its own file.

**Says three or four, left thumb only:**

- `docs/decisions/0009-enclosure-construction.md:10-13`:
  > "It is a flat sandwich: oak top and bottom, frosted acrylic sides carrying
  > LEDs, aluminium key plate on top, and **three or four mechanical keys on the
  > underside for the left thumb**, inset so the travel feels right."

**Says four left-thumb plus three right-thumb, seven in all:**

- `config/key-layout.yaml:36-40`: `left_thumb: 4`, `right_thumb: 3`,
  `total: 18`.
- `docs/decisions/0010-key-layout-as-data.md:51-52`: "| Left thumb | 4 | bottom,
  inset (ADR 0009) |", "| Right thumb | 3 | bottom, offset from the rest |".
- `hardware/bom.csv:86` (`PLATE-THUMB`): "Carries the **4 left-thumb and 3
  right-thumb** switches."
- `hardware/controller/cluster-boards.md:40`: "both on PLATE-THUMB, inside face
  of the oak bottom".
- ADR 0009 itself, `:137` and `:155`: "the left thumb's **four-key arc**", and
  `:398-401`: "The right thumb rests on the instrument and its **three control
  switches** sit offset from that rest position".

The same paragraph also omits the thumb plate from the sandwich it enumerates,
though `:64-68` includes it.

---

<a name="f10"></a>
## F10 — `PCB-MODULE`: a deleted watchdog and a superseded width, in the row that was edited today

**Rank: Medium.** The row flags its own staleness and does not fix it.

- `hardware/bom.csv:70`, description field: "DAC, scaling, jacks, power entry,
  load switch, **watchdog**"; size field "**~45 x 110mm, 1.6mm**"; note:
  > "10HP, via 8HP, not 6HP: **the 23.8mm hole leaves 8.27mm of panel each side
  > at 40.34mm (ADR 0004)** | 2026-09-21: 8HP -> 10HP, so the board widens
  > ~35mm to ~45mm. … **'watchdog' in this row's description is stale - that
  > part is DELETED**"

The note's leading clause still states 8.27 mm / 40.34 mm in the present tense,
immediately before the clause that supersedes it. And the description field
still lists the watchdog after the note says to stop believing it — a reader or
a script taking the description column gets the deleted part.

**The watchdog is deleted, confirmed:**

- `hardware/module/digital-and-supervision.md:51`: "NOT HERE ANY MORE: the
  74HC123 frame watchdog and the LM311 presence"
- `hardware/module/digital-and-supervision.md:61`: "74HC123 and LM311 were
  deleted — in ADR 0004, in `bom.csv`, and in this" [page]

---

<a name="f11"></a>
## F11 — "There is no coating anywhere in the BOM"

**Rank: Medium.** A statement of absence that is no longer true.

- `docs/decisions/0009-enclosure-construction.md:483-486`:
  > "**Conformal-coat the boards.** … **There is no coating anywhere in the
  > BOM** and nothing else in the design addresses humidity inside the cavity."
- `hardware/bom.csv:53` (`MECH-COAT`): "Acrylic conformal coating … Conformal
  coating for the in-body boards … **MASK BOTH SENSOR PORTS FIRST**", status
  `open`, `adr` column `0009`.
- `hardware/controller/carrier.md:889`: "**`MECH-COAT` must mask both** `[repo]
  0009`" — the carrier page already treats the row as existing.

---

<a name="f12"></a>
## F12 — "Two openings in the tail section", three listed

**Rank: Low.** Stale count, no functional effect, but it is the count that the
M4 CAD and the 1:1 tail check are supposed to work from.

- `docs/decisions/0009-enclosure-construction.md:265-267`:
  > "### The tail carries a display window and a USB port
  >
  > **Two openings in the tail section**, below the right-hand key run, clear of
  > the thumb keys and the U-bolt:"

Then three are described: "**A window in the oak underside for the 8×8
matrix**" (`:269`), "**A USB-C slot at the tail face**" (`:283`), and "**And the
umbilical connector, which is the reason the tail face is now crowded**"
(`:287`). A fourth opening — the service cover at `:303` — is in the same tail
underside and in the same laminated layer.

The heading is stale for the same reason ("a display window and a USB port").

---

<a name="f13"></a>
## F13 — "The knobs fit the range; the firmware shapes the feel"

**Rank: Medium.** Two accepted ADRs assign response shaping exclusively to
firmware, and the panel now has an analog control that does exactly that.
Flagged here because it governs what the panel carries; the breath-domain sweep
may own the signal-path half of it.

**Firmware owns the curve:**

- `docs/decisions/0006-cv-channel-allocation.md:277-278`: "Firmware still shapes
  the response curve upstream of the DAC. **The knobs fit the *range* to the
  patch; the firmware shapes the *feel*.**"
- `docs/decisions/0003-breath-sensing-path.md:96`: "**Panel knobs (ADR 0006)
  handle *range fitting*; firmware handles *response feel*.** Different jobs,
  both kept."
- `docs/decisions/0003-breath-sensing-path.md:84-86` lists "**Curve shaping**"
  as one of "the reasons the fully-analog path was rejected, and none of them
  are recoverable in hardware".

**The panel now shapes the curve in hardware:**

- `hardware/module/breath-output-stage.md:161`: "# §4 Response control —
  `POT-RESP`, log ← linear → exp"
- `hardware/bom.csv:80` (`POT-RESP`): "Breath response: log (CCW) - linear
  (centre) - exponential (CW)" — filed under `adr` **0006**, the ADR that says
  firmware does this.

---

<a name="f14"></a>
## F14 — BOM `PANEL` note opens on the superseded width

**Rank: Low.** Stale phrasing in a row that was otherwise updated today.

- `hardware/bom.csv:20` (`PANEL`), note: "Laser or waterjet from DXF - SAME
  vendor and order as the key plate. **8HP not 6HP: see ADR 0004** | 2026-09-21:
  8HP -> 10HP. …"

The part field is correct ("2mm aluminium, 10HP x 3U (50.50 x 128.5mm)"). The
note reads as an instruction to build 8HP until the reader reaches the dated
clause. Same shape as [F10](#f10).

---

# Facts asserted but never derived

<a name="n1"></a>
## N1 — "~110 mm usable" is the denominator of the entire budget and is derived nowhere

**Rank: High.** This is the same defect class that the 107 mm figure was
condemned for, one level up: the corpus replaced an underived *numerator* and
kept an underived *denominator*.

Every statement of the budget is "X against ~110 mm":

- `docs/decisions/0004-cv-interface-module.md:667`: "97 mm against ~110 mm —
  13 mm spare"
- `docs/decisions/0004-cv-interface-module.md:646`: "~115 mm against ~110 mm
  usable"
- `docs/decisions/0004-cv-interface-module.md:500`, `:585`: "of ~110 mm usable"
- `hardware/module/breath-output-stage.md:272`, `:279`
- `hardware/bom.csv:20`

The only physical panel dimension the corpus records is
`hardware/bom.csv:20`: "10HP x 3U (**50.50 x 128.5mm**)". **Nothing anywhere in
the corpus connects 128.5 mm to 110 mm.** The 18.5 mm difference, the reason for
it (the rails sit behind the panel and a component body that protrudes must land
inside the window), and its source exist only in `docs/review/` — which by the
rules of this sweep is a dated snapshot, not a specification. If 110 mm is
wrong, 97 mm and its 13 mm of spare are wrong with it, and the 13 mm of spare is
smaller than the 18.5 mm of assumption it sits on.

The same gap swallows `hardware/bom.csv:70`, which gives `PCB-MODULE` as
"~45 x **110mm**" — a board exactly as tall as the usable window, with no
statement of whether the window applies to the board, the panel hardware, or
both.

---

<a name="n2"></a>
## N2 — The 97 mm is a sum of component heights with no clearance, and the reason given for the saving is not where the saving came from

**Rank: High.** This is the most valuable finding in the sweep. The arithmetic
is internally correct and the *method* repeats the exact defect that was
diagnosed and announced as fixed.

**The sum checks:** 5 + 22 + 39 + 31 = 97. ✓

**What it left out.** The reconstruction the budget is built on
(`docs/review/2026-09-21-hardware-and-standards-review/B1-eurorack-standards.md:138-149`,
cited as the authority by ADR 0004, `breath-output-stage.md` and the BOM) used
these envelopes:

| Element | B1 | ADR 0004 now | Δ |
|---|---|---|---|
| etherCON | 31 + 1 mm clearance each side = **33** | **31** | −2 |
| gap | 3 | — | −3 |
| Toggle + LED sharing one row | **12** | **0** (moved beside the etherCON) | −12 |
| gap | 3 | — | −3 |
| Pots, one row | 18 (two across) | **22** (three across) | +4 |
| gap | 4 | — | −4 |
| Jacks, 3 × 2 at 13 mm | **42** (8 above first centre + 2 × 13 + 8 below last, to clear plug bodies) | **39** (= 3 × 13) | −3 |
| Label / title band | — | **5** | +5 |
| **Total** | **115** | **97** | **−18** |

Three things follow, and none of them are in any corpus document:

1. **Every inter-element gap is gone.** B1's 10 mm of judgement gaps was
   deleted without comment. B1's own diagnosis of the old 107 mm figure was that
   it "looks like a sum of component heights with **no clearance allowance at
   all**". The replacement is a sum of component heights with no clearance
   allowance at all.
2. **The jack field lost its plug clearance.** 39 mm is pitch × rows. A
   three-row field spans two 13 mm pitches plus room above the first and below
   the last centre for a 3.5 mm plug body — B1's 42 mm. The corpus never states
   which convention 39 mm uses.
3. **The toggle and the LED left the height budget entirely**, on the assertion
   "with the toggle and LED beside it". The etherCON flange is 26 mm wide
   (see [verified](#verified-clean)); on a 50.50 mm panel that leaves 24.5 mm
   total, i.e. ~12 mm per side before edge margin, for a toggle bushing plus
   lever clearance and a 3 mm LED. That may well fit. **No document checks it**,
   and it is the single largest line in the saving.

**Restore only B1's clearances and gaps** (2 + 3 + 3 + 4 + 3 = 15 mm) and the
panel is **112 mm against ~110 mm** — still over. Put the toggle/LED row back
too and it is **124 mm**.

**And the stated rationale does not match the arithmetic.** ADR 0004
`:657-659`:

> "**10HP is 50.50 mm**, and the win is not the width itself — it is that three
> pots fit in **one row instead of two**, which deletes a whole 20+ mm row from
> a budget that was already over."

B1's 115 mm **already had the pots side by side in one row** (`:146`, and
`:151-155`: "that layout already takes every favourable option: … the two pots
are side by side rather than stacked"). The 20+ mm row being deleted exists only
in B1's *stacked* variant (133 mm). Against the 115 mm the ADR quotes as the
problem, the pot row did not shrink — **it grew from 18 mm to 22 mm**. The
entire 18 mm saving comes from deleted clearances and the relocated toggle/LED
row. The document explains the win with the one line item that got worse.

The ADR's own caveat is correct as far as it goes and should be read as covering
all of the above:

- `docs/decisions/0004-cv-interface-module.md:695-698`: "The 97 mm above is
  built from `[from memory]` component envelopes … **The layout is credible and
  it is not verified.**"

---

<a name="n3"></a>
## N3 — The ≤14 mm knob cap leaves 1.25 mm of panel edge, and no document says so

**Rank: Medium.** The arithmetic is right; the assumption is invisible.

- `docs/decisions/0004-cv-interface-module.md:673-681`: "Three pots across
  50.50 mm with 3 mm gaps needs **≤14 mm knobs** `[calc]`" with the table
  20 → 66, 16 → 54, 15 → 51, **14 → 48 fits**.
- `hardware/bom.csv:84` repeats it: "three pots across 50.50mm with 3mm gaps
  needs <=14mm knobs (15mm gives 51mm and does not fit)".

3 × 14 + 2 × 3 = 48 ✓. Against 50.50 mm that is **1.25 mm of aluminium between
each outer knob and the panel edge** — and the panel's true width at minimum
tolerance is 50.30 mm (+0/−0.2, ADR 0004 `:603`), giving 1.15 mm. Neither
figure is stated. The same review that produced this method applied an edge
margin when it checked two knobs at 8HP
(`B1:190-193`: 16 mm knobs leave "**4.17 mm** from each panel edge. Workable,
tight"; 20 mm knobs leave 0.17 mm and "**Does not fit**, and would overhang the
neighbouring module"). By that standard 14 mm knobs at 1.25 mm are nearer the
rejected case than the accepted one. With a 3 mm edge margin each side the cap
falls to ~12.8 mm.

---

<a name="n4"></a>
## N4 — The eased notch web is never recomputed

**Rank: Low.**

- `hardware/bom.csv:70`: "the board widens ~35mm to ~45mm. The etherCON notch is
  now a smaller fraction of the board, which **eases the 4.5mm web** a review
  flagged."

The old figure is derivable — ADR 0004 `:641-642` gives a "~26 mm notch", and
(35 − 26)/2 = 4.5 ✓. The new one, (45 − 26)/2 = **9.5 mm**, is stated nowhere.
"Eases" is the only characterisation, on the dimension that decides whether the
module stays one board.

---

<a name="n5"></a>
## N5 — The panel has no mounting holes anywhere in the corpus

**Rank: Medium.** Not a contradiction — an absence, in a part that is cut once
from a DXF in the same order as the key plate.

`hardware/bom.csv:20` specifies the `PANEL` as "2mm aluminium, 10HP x 3U
(50.50 x 128.5mm)" and nothing else. Searching the corpus for `3.2`, `122.5`,
"mounting hole" and "slot" returns no panel result. ADR 0004's panel sections
(`:603-700`) give width, bore, flange clearance and the height budget, and never
mention rail fixings.

A 3U panel needs two (or four) Ø3.2 mm holes or slots at ~3 mm from the top and
bottom edges, on 122.5 mm centres, or it cannot be racked. This was raised in
the review wave (`B1:80-101`) and has not landed in any corpus document.
Relevant to the height budget too: the fixing holes sit inside the same 128.5 mm
the ~110 mm window is cut from.

---

<a name="n6"></a>
## N6 — The 4 mm panel-thickness limit is stated four times and resolved nowhere

**Rank: High.** Four corpus documents state the constraint and the same remedy;
none of them derives that the remedy satisfies the constraint.

**The constraint:**

- `docs/decisions/0004-cv-interface-module.md:701-703`: "**The instrument end
  still needs a backing plate, not oak** — and the etherCON D is rated for a
  **maximum 4 mm panel thickness**, so it cannot mount through 6 mm oak at all."
- `docs/decisions/0013-two-mcu-split.md:201-203`: "the D-series is rated for a
  **4 mm maximum panel thickness** so it cannot mount through 6 mm oak"
- `hardware/bom.csv:19` (`J-UMBILICAL`) and `hardware/bom.csv:87`
  (`MECH-BACKPLATE`): same sentence twice.

**The remedy:**

- `docs/decisions/0009-enclosure-construction.md:293-296`: "**Mount the
  connector to an internal backing plate** — aluminium or ply, tied into the
  same stack that carries the keys — and **let the oak be the face the screws
  pass through** rather than the thing the screws hold."

**What is never stated anywhere:** the backing plate's thickness
(`hardware/bom.csv:87` `MECH-BACKPLATE` part field: "TBD - aluminium or ply"),
and how a connector rated for ≤4 mm of clamped panel mounts behind a 6 mm oak
face. The flange either sits proud of the oak, or the oak is counterbored, or
the connector recesses and its latch no longer reaches a plug. None of those
three appears in the corpus. The ADR 0009 sentence makes the oak a spacer
between the flange and the plate, which is the one arrangement the 4 mm rating
forbids.

Related and also underived: `docs/decisions/0009-enclosure-construction.md:288-292`
gives "about **3.5 mm** of material above and below the cutout" from a
26 × 31 mm flange on a 57 × 38 mm face — (38 − 31)/2 = 3.5 ✓ — but computes it
from the **flange**, not from the cutout it names.

---

<a name="n7"></a>
## N7 — The service cover was sized for a header that no longer exists

**Rank: Low.**

- `docs/decisions/0009-enclosure-construction.md:313`: "Roughly **12 × 40 mm**,
  two M2 screws into the plate stack"
- `hardware/bom.csv:98` (`MECH-SERVICECOVER`): "Screwed cover plate ~12 x 40mm +
  2x M2"

A 2×3 header on 2.54 mm pitch is 5.08 × 2.54 mm of pins. The 40 mm length was
set when the header was ten-pin (see [F4](#f4)); it has not been revisited, and
`hardware/controller/carrier.md:871-872` shows the old pairing still being
reasoned from.

---

<a name="n8"></a>
## N8 — The mass breakdown's aluminium row does not reconcile, and its plate thickness is an open question

**Rank: Medium.** Applies to the `~825 g` table (`docs/decisions/0009-enclosure-construction.md:175-186`).

`[calc]` at the 457 × 57 mm footprint:

| Row | Stated | Implied density | Expected |
|---|---|---|---|
| Aluminium top plate, 2 mm | **157 g** | **3.01 g/cm³** | ~141 g at 2.70 g/cm³ |
| Oak top, 6 mm | 131 g | 0.838 g/cm³ | consistent with the row below |
| Oak bottom, 8 mm | 174 g | 0.835 g/cm³ | ✓ self-consistent |
| Acrylic sides, 2 × 4 mm | 164 g | 1.18 g/cm³ | ✓ correct for PMMA |

The two oak rows and the acrylic row use consistent, plausible densities. The
aluminium row is ~16 g heavy and matches no aluminium alloy. It also ignores the
eighteen 14 mm cutouts (~3.5 g of removed metal).

Separately, the row assumes a **2 mm** plate while plate thickness is formally
open in five places — `docs/decisions/0002-key-switches-and-mounting.md:196-199`
("**Plate thickness**, pending the clip dimension … Blocks M4 and M5"),
`config/key-layout.yaml:33` (`plate_thickness: null`), `hardware/bom.csv:21`
("THICKNESS OPEN"), `ROADMAP.md:221`, and
`hardware/controller/cluster-boards.md:414-417`. ADR 0009's own Z-stack marks it
("~2 mm ← may become 1.5 mm, see ADR 0002"); the mass table does not.

---

<a name="n9"></a>
## N9 — The length table sums centre-to-centre spans

**Rank: Low.** Consistent convention, unstated assumption.

`docs/decisions/0009-enclosure-construction.md:32-43` gives "Left hand, 5 keys in
line | **96**" and "Right hand, 6 keys in line | **120**" at "a 24 mm key
pitch". `[calc]` 4 × 24 = 96 and 5 × 24 = 120 — these are outer **centre**
spans, not occupied length. Adding half a 16.5 mm cap at each end of each run
costs ~33 mm, against the table's "**Slack | 31 (1.2 in)**". The convention
matches `docs/decisions/0010-key-layout-as-data.md:90` ("A single line of 6 keys
at a relaxed 24 mm pitch spans 120 mm"), so the two documents agree — they agree
on a figure that consumes the whole stated slack if the caps are counted.

---

<a name="verified-clean"></a>
# Verified clean

Checked across every corpus file that states them; consistent everywhere, and
the arithmetic reproduces.

1. **Panel width 50.50 mm.** `(10 × 5.08) − 0.3 = 50.50`, +0/−0.2 ✓ —
   ADR 0004 `:603`, `hardware/bom.csv:19`, `:20`, `ROADMAP.md:183`,
   `hardware/module/breath-output-stage.md:276`. No corpus file states 40.34 mm
   as current.
2. **10HP as the module's form factor** — `README.md:23`, ADR 0004 `:16`,
   `:224`, `hardware/bom.csv:20`, `:70`, `hardware/module/power-entry.md:79`,
   `ROADMAP.md:53`. (The three "8HP" residues are phrasing, F6/F7, not form
   factor.)
3. **Aluminium each side of the bore: 13.35 mm.** `(50.50 − 23.8)/2 = 13.35` ✓
   — ADR 0004 `:611`, `:669`, `hardware/bom.csv:19`. Historical 8.27 mm
   (`(40.34 − 23.8)/2`) and 3.19 mm (`(30.18 − 23.8)/2`) both check ✓ and are
   marked as historical.
4. **Knob fit table.** 20 → 66, 16 → 54, 15 → 51, 14 → 48, all `3n + 6` ✓
   (ADR 0004 `:675-680`), and `hardware/bom.csv:84` agrees.
5. **etherCON flange 26 × 31 mm.** ADR 0009 `:288`, ADR 0013 `:201`, and
   ADR 0004's "12.25 mm of visible panel each side of the flange" `:669`
   — `(50.50 − 26)/2 = 12.25` ✓. The 31 mm row in the height budget and the
   "roughly 31 mm beside the flange" for the USB-C slot (`57 − 26 = 31` ✓,
   ADR 0009 `:297`) both follow from the same figure.
6. **Instrument envelope 457 × 57 × 38 mm (18 × 2.25 × 1.5 in).** ADR 0009
   `:17`, `config/key-layout.yaml:19-21`, `ROADMAP.md:64`, `ROADMAP.md:183`
   ("57 × 38 mm instrument tail"), ADR 0009 `:289`, ADR 0013 `:201`,
   ADR 0010 `:136`, ADR 0008 `:173`. No variant anywhere.
7. **Cavity ~20 mm, and it is derived.** ADR 0009 `:61-71`:
   `38 − 2 − 6 − 8 − 2 = 20` ✓ from a stack that is printed in full. Used
   consistently at ADR 0008 `:187` ("its 10 mm depth clears the ~20 mm cavity"),
   ADR 0014 `:417`, ADR 0013 `:269`, `hardware/controller/carrier.md:658`,
   `:845`, `hardware/controller/cluster-boards.md`.
8. **Length budget sums.** 40 + 60 + 96 + 50 + 120 + 40 + 20 = **426** ✓,
   `457 − 426 = 31` ✓ (ADR 0009 `:32-43`), and ADR 0008 `:190-192` independently
   reports the same 31 mm after the display band grew 30 → 60 mm. The 60 mm
   display band matches ADR 0008's "needs 60 mm of body length" `:185`.
9. **KS-33 geometry.** 14.0 × 14.0 mm cutout, 12.2 mm height, 1.70 mm pretravel,
   3.00 mm travel, 3-pin, no alignment posts — identical in
   `docs/reference/ks33-geometry.md`, ADR 0002 `:111-124`,
   `config/key-layout.yaml:25-29`, `hardware/bom.csv:2`,
   `hardware/controller/cluster-boards.md:374-389`, ADR 0009 `:76-87`,
   `ROADMAP.md:71`. Footprint coordinates match between the reference and the
   cluster-boards page to the digit.
10. **Plate thickness is open, and every document says so** — ADR 0002 `:196`,
    ADR 0009 `:64` and `:551`, `config/key-layout.yaml:31-33`,
    `hardware/bom.csv:21`, `ROADMAP.md:221`,
    `hardware/controller/cluster-boards.md:414-417`. The three candidate values
    (2 / 1.5 / 1.1 mm) and the reason each is in play are stated identically in
    all of them. (Sole exception: the mass table, [N8](#n8).)
11. **Key count 18 = 5 + 6 + 4 + 3.** `config/key-layout.yaml:36-41`,
    ADR 0010 `:48-52`, `hardware/bom.csv:2` (21 = 18 + 3 spares),
    `hardware/bom.csv:86`, `ROADMAP.md:71` ("the four thumb keys … the eleven
    finger keys"), `hardware/controller/cluster-boards.md:25-42`.
12. **Free-volume zones.** "Upper section, inter-hand gap minus the U-bolt,
    lower section, two side channels flanking the switch column" — ADR 0009
    `:96-101`, ADR 0013 `:205-213`, ADR 0014 `:22-32`. The old
    looms-vs-LED-strips conflict is resolved in the same terms in both ADR 0009
    `:433-447` and ADR 0014 `:31-37`. The 50 mm inter-hand / U-bolt band is
    consistent in ADR 0009 `:37`, `:113` and
    `hardware/controller/cluster-boards.md:37`, `:50-52`.
13. **Tail features.** 8×8 matrix window "roughly 22 mm square" — ADR 0009
    `:269`, ADR 0014 `:402-406`, `hardware/bom.csv:69` ("~22mm cutout"),
    `hardware/controller/carrier.md:838`. USB-C slot at the tail face in all
    four. Breath tube ~400 mm — ADR 0009 `:255`, ADR 0003,
    `docs/reference/latency-budget.md:38`, `:76`.
14. **Module PCB 45 mm behind a 50.50 mm panel** keeps the same ~5.5 mm
    panel-to-board margin the 8HP pair had (`40.34 / ~35`), so
    `hardware/bom.csv:70`'s new width is at least internally consistent with the
    convention it replaces.

---

## Adjacent, outside this domain — flagged, not investigated

Noticed while reading; they belong to the analog and breath sweeps.

- `hardware/module/breath-output-stage.md:130-132`: "**Two op-amp halves** …
  **Ten of twelve halves used across the module, two spare.**" §4 of the same
  file (`:262-264`) and `hardware/bom.csv:83` (`U-RESP`) say the response stage
  "consumes **BOTH remaining spare OPA2197 halves**" and adds a package. The
  "two spare" line is stale within its own file.
- `ROADMAP.md:51` (E10): "in-amp receiver with **`REF` grounded**" against
  `hardware/module/breath-receive-stage.md:117` ("**Grounding it makes the panel
  knobs interact**") and `:163` (REF is a buffered trimmer, 0 → +1.0 V).
- `docs/decisions/0003-breath-sensing-path.md:239` calls the sensor a "**gauge**
  sensor with a temperature-dependent offset" where the BOM
  (`hardware/bom.csv:5`) and the rest of ADR 0003 specify the **DP**
  differential part.
