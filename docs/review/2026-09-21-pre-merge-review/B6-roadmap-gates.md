# B6 — Is the plan buildable in the order it states?

**Agent:** B6, cold pre-merge review, 2026-09-21
**Slice:** `ROADMAP.md` ordering, irreversibility, the bench-measurement table,
the blocked/disputed figures, the gates, and whether the 23-circuit restructure
invalidated the PCB pipeline.
**Cold rule observed:** nothing under `docs/review/**` was opened. Where a
figure entry or an ADR quotes a review directory, I took the quoting document's
word and marked it as such.
**Provenance:** every claim is `[repo] path:line`, `[calc]`, or `[from memory]`.
Findings are indexed by **milestone**, not by file.

---

## Verdict

The three ordering rules the ROADMAP records as fixed are genuinely fixed. What
it has not caught falls into four repeating shapes:

1. **The F track is not in the plan.** F1, F2 and F3 appear in no phase, and
   four E milestones state acceptance criteria that are F-track work.
2. **"LEDs" is written into five acceptance tests that happen before the LEDs
   exist.** The ROADMAP invented M8 for exactly this reasoning and then did not
   apply it to the other four.
3. **The measurement table schedules a milestone, and `config/figures.yaml`
   expects a different measurement at it.** Twice.
4. **`docs/reference/pcb-pipeline.md` predates the whole restructure** and is
   the single largest correctness gap in the plan — it does not appear in the
   ROADMAP at all, and its central assumption (six schematic pages) is now
   twelve.

Twenty-four findings. Nine I would call blocking for a merge that claims the
plan is the deliverable.

---

## 1. Dependency order

### B6-01 — **E9 depends on F8, which is three phases later** (blocking)

E9's done-when requires calibration "**Stored in NVS with a version and a
checksum, in its own slot away from presets**" `[repo] ROADMAP.md:50`. F8 is
"Config and calibration in NVS; **presets**" `[repo] ROADMAP.md:149`. E9 is
Phase 2, F8 is Phase 5 `[repo] ROADMAP.md:159,162`.

The escape clause does not cover this. `[repo] ROADMAP.md:15-17` exempts
"throwaway fixtures that prove a DAC or an ADC works". A versioned, checksummed
NVS slot that must not collide with a preset store is not a fixture — it is a
storage-layout decision binding on F8, taken in Phase 2 by a milestone that
never names F8.

### B6-02 — **F1, F2 and F3 are in no phase at all** (blocking)

The phase table `[repo] ROADMAP.md:155-162` allocates E1–E14, M1–M8 and
**F4–F9**. F1 `[repo] :141`, F2 `[repo] :142` and F3 `[repo] :143` appear in the
F table and nowhere else. `grep -n "F1\|F2\|F3" ROADMAP.md` returns only their
own three rows `[repo]`.

This is not cosmetic, because Phase 1's stated outcome is "Playable USB MIDI
instrument on a test plate" `[repo] :158` and three Phase-1 milestones require
them by name:

| Milestone | Acceptance text | Needs |
|---|---|---|
| E2 `[repo] :42` | "Ambient zeroing tracks, no condensation artefacts" | F2 (`:142`, ambient zeroing of the digital copy) |
| E5 `[repo] :46` | "Fingering table exercised" | F1 (`:141`, fingering table driven from config) |
| E7/E8/E10 `[repo] :48,49,51` | commanded codes, trimmed channels | F3 (`:143`, fixed-rate DAC loop) |

E5's case is the sharpest: F1's whole content is "**custom** fingering table
driven from config, not hardcoded", and E5 is the milestone that exercises it.

### B6-03 — **E10 contains a test whose precondition is E11** (blocking)

E10 requires "**Pull the umbilical mid-note with the mouthpiece at rest**",
observing that "pitch and the four mod jacks hold their last value indefinitely"
`[repo] ROADMAP.md:51`. Holding a last value is a statement about what happens
when SPI frames stop arriving over the umbilical. E11 is the milestone that
brings the umbilical link up — "SPI **at 2 MHz** ... over the real cable at
length" `[repo] ROADMAP.md:52`, the next row.

`docs/decisions/0004-cv-interface-module.md:535` assigns the same test to E10
("**E10 checks it rather than assuming it:** with the mouthpiece at rest, pull
the umbilical mid-note and watch the jack"), so the two documents agree — but
they agree on an inversion, not against it. Either the test moves to E11, or
E10's row states that it runs on a bench-length cable and is re-run at E11.

Note also that the same ADR sentence ends "If it does not, we find out **before
anything is bonded**" `[repo] docs/decisions/0004-cv-interface-module.md:537` —
see B6-14.

### B6-04 — **E14 re-validates module milestones on the carrier, and nothing
re-validates the module** (blocking)

E14 is "**E1–E11 re-run on the carrier**, not on dev boards. Everything before
this was proven on a different physical thing" `[repo] ROADMAP.md:55`.

E6–E11 are module-side milestones: module power `[repo] :47`, DAC raw
`[repo] :48`, pitch scaling `[repo] :49`, pitch calibration `[repo] :50`,
remaining channels `[repo] :51`, umbilical link `[repo] :52`. Re-running module
power "on the carrier" is a category error.

The reasoning E14 embodies applies with full force to the module and is not
applied: E6–E11 are proven on breadboard, E12 assembles the module PCB
`[repo] :53`, and **no milestone re-runs E6–E11 on that PCB**. The asymmetry is
invisible because E12 reads as a build step and E13/E14 read as a build step
plus a gate.

Suggested shape: E12 grows an "E6–E11 re-run on the module PCB" clause, and
E14's text narrows to E1–E5 plus the carrier end of E11.

### B6-05 — **M5 is ordered after E13 but not after E14, and the ordering rule
itself predicts a respin** (blocking)

The rule says "**M5 must not precede E13** ... Cut the plate after the carrier
layout exists" `[repo] ROADMAP.md:92-95`, and the next rule says "the carrier
*will* spin at least once — the SPI split alone changes its topology"
`[repo] ROADMAP.md:98-99`.

E14 is the milestone that discovers the respin `[repo] :55`. Phase 4 contains
"E13, E14, M5–M7, M8" `[repo] :161` with no internal order, and M5's own row
says only "Not before E13" `[repo] :75`. So the aluminium plate — named by the
ROADMAP itself as "the most expensive irreversible part" `[repo] :93` — may
legally be cut between E13 and E14, i.e. before the revision the plan expects.

Contrast the care taken elsewhere: Phase 3's row carries an explicit "**M5 moves
to Phase 4**" note `[repo] :160`. The same explicitness is absent inside Phase 4.

### B6-06 — **"The body does not close until the carrier is revision-final" is
prose only** (medium)

`[repo] ROADMAP.md:97-103` states the rule. The phase table puts E13, E14, M5,
M6, M7 and M8 in one undifferentiated row `[repo] :161`. Nothing in the table or
in M7's row `[repo] :77` encodes E14 → M7. A reader working from the phase view,
which is the view a schedule is built from, has no ordering.

### B6-07 — **Ordering constraints stated in ADRs that the ROADMAP does not
carry** (medium)

Three deadlines live only in ADRs:

- "The schema needs to exist **before M2**, since the first laser-cut plate
  should be ..." `[repo] docs/decisions/0010-key-layout-as-data.md:40`
- "a switch that is not in the DXF never exists — **a deadline at M3**"
  `[repo] docs/decisions/0010-key-layout-as-data.md:162`
- "**Choose the adhesives before M8, not at M8.** Two products, split by joint"
  `[repo] docs/decisions/0009-enclosure-construction.md:535`, against
  `ADH-WOOD` and `ADH-RTV` both still `candidate`
  `[repo] hardware/unplaced.csv` (rows 44–45 by order).

M2 `[repo] :72`, M3 `[repo] :73` and M8 `[repo] :78` say none of this. The
ROADMAP is the document a reader plans from; a deadline that exists only in an
ADR is a deadline nobody reads at the moment it binds.

### B6-08 — F-table rows are out of numeric order (trivial)

F9 `[repo] ROADMAP.md:148` sits between F7 and F8 `[repo] :147,149`. Harmless
until someone reads the table as a sequence, which is exactly what a
"Done when" table invites.

---

## 2. Irreversibility

The irreversible steps are: M2's laser-cut plate `[repo] :72` (cheap,
deliberately), **M5 aluminium** `[repo] :75`, **M6 body — oak, acrylic, matrix
window and diffuser, USB-C slot** `[repo] :76`, **E12's 10HP panel cut**
`[repo] :53`, and **E13's populated carrier and four cluster boards**
`[repo] :54`.

Three of the five are correctly fenced. Two are not.

### B6-09 — **E12 cuts the panel; the paper fit check that validates it is hung
on M4, in the same phase, with no order between them** (blocking)

The measurement is "**1:1 paper fit check, both faces** | **M4** | The etherCON
flange against a 50.50 mm 10HP panel *and* against the 57 × 38 mm instrument
tail" `[repo] ROADMAP.md:190`. E12 is "10HP panel cut, module assembled and
racked" `[repo] :53`. Phase 3 is "E10–E12, M4" `[repo] :160` — one row, no order.

The margin being checked is 5.5 mm of slack over five rows, i.e. 1.4 mm per row
boundary `[repo] config/figures.yaml:283` (`panel-height-budget` derivation), and
`panel-height-budget`'s own note says "**WHAT IS STILL WORTH DOING, and ADR 0004
already asks for it: print at 1:1 and check**" `[repo] config/figures.yaml:300`,
corroborated at `[repo] docs/decisions/0004-cv-interface-module.md:832`.

A 1.4 mm-per-boundary panel, cut in 2 mm aluminium by an outside vendor, with
the paper check formally unordered against the cut. This is the same shape as
the M5/E13 violation the ROADMAP already fixed, one track over.

### B6-10 — **M6 cuts the matrix window, and the prototype that decides whether
the matrix works through a window is scheduled at M6** (blocking)

M6 delivers "**tail matrix window + diffuser** and USB-C slot" `[repo] :76`.
The measurement is "**Matrix diffusion prototype** | **M6** | Can an 8×8 at
2.6 mm pitch stay pixel-distinct through a window, or only as a blurred bar?
**Decides whether the 2-D IMU assignment is usable**" `[repo] :191`.
`[repo] docs/decisions/0014-lighting.md:541-543` agrees and widens it: "Diffusion gap
and material for the side panels, and separately for the matrix window, which
wants pixel definition rather than blur. **Both are M6 prototype questions**".

So the gap, the material and the go/no-go on the feature all resolve at the
milestone that cuts the window into oak and acrylic. The prototype needs no
body — it is a diffuser sheet, a window aperture and the dev board's own matrix,
all of which exist from E1 `[repo] :41`. It belongs at M2 or M4, in the cheap
material, which is the ladder the ROADMAP states for everything else
`[repo] :86-88`.

### B6-11 — **The "time-critical" argument rests on a bonded body that no longer
exists** (medium, and it is an argument surviving its own refutation)

"**The key-chain and restrictor measurements are the time-critical ones** — both
inform wiring and plumbing that get **sealed inside a bonded body at M6**"
`[repo] ROADMAP.md:206-207`.

Two things are wrong and the ROADMAP itself says so 129 lines earlier: M8's own
row states "**The body is no longer bonded shut — it closes on six fasteners
onto an RTV gasket, ADR 0009**" `[repo] ROADMAP.md:78`, and
`docs/decisions/0009-enclosure-construction.md:493-494` is explicit — "The body
is not bonded shut any more, so the items below are no longer *impossible*
later". Separately, wiring is not sealed at M6 in any case: M6 builds the body,
M7 mounts the electronics and fits the umbilical `[repo] :77`, M8 puts the lid
on `[repo] :78`.

This is CLAUDE.md §5's named failure mode with the ROADMAP as both victim and
witness: the fix landed in the M8 row where the editing was happening, and not
in the sentence that ranks the measurements.

The consequence is a real mis-ranking. Both named measurements are already
early — restrictor at E2 `[repo] :204`, key-chain at E4 `[repo] :202`, both
Phase 1 — so they were never at risk. The measurements that *are* time-critical
by the surviving version of the argument are B6-09's paper fit check and
B6-10's diffusion prototype, and neither is named here.

### B6-12 — M5's "bonded to `PWR_GND`" has no milestone that verifies it (low)

M5 delivers the plate "**bonded to `PWR_GND`**" `[repo] :75`. `PWR_GND` is the
module-side power return, one of four returns the pipeline asserts must stay
distinct `[repo] docs/reference/pcb-pipeline.md:225-226`, and its topology is
one leg of the `dig-gnd-topology` dispute `[repo] config/figures.yaml:387-398`.
No milestone measures the plate bond — not M7 `[repo] :77`, not M8 `[repo] :78`.
`docs/decisions/0009-enclosure-construction.md:514` states the failure mode
("unbonded plate means the instrument fires random notes when touched in a dry
room"), which is a silent failure of exactly the class §"Failures that are
silent" catalogues `[repo] ROADMAP.md:215-219` and is not in that table either.

---

## 3. The measurement table

Sixteen rows `[repo] ROADMAP.md:187-204`. Each names a milestone. Checked each
for (a) does the milestone happen before the decision it informs, (b) is the
thing it measures still in the design.

### B6-13 — **E1 measures the wrong quantity for the figure that is blocked on
it** (blocking)

The ROADMAP row: "**Real-time board idle current** | **E1** | 64 **unlit**
`WS2812B-0807` drivers are an estimated ~50 mA and 0.25 W ... **E1 measures it,
spent whether or not anything is displayed**" `[repo] ROADMAP.md:189`. Its
bracketing surrogates are 22 mA, <38 mA and 160 mA — all quiescent figures.

The blocked figure: `matrix-led-current`, "ESP32-S3-Matrix LED current, **full
white, 64 LEDs**", `status: blocked`, candidates 960 / 2304 / 3648 mA,
`decided_by: "A BENCH MEASUREMENT AT E1"`
`[repo] config/figures.yaml:516-522`.

These are different measurements by a factor of ~20 [calc: 2304 mA / ~50 mA ≈
46; against the 160 mA high surrogate, ~14]. The ROADMAP schedules the idle
sweep at E1 and **schedules no full-white measurement anywhere**. The blocked
figure's own note says "**THIS NUMBER IS LOAD-BEARING**" and that ADR 0014's
non-configurable brightness cap rests on it
`[repo] config/figures.yaml:526`.

Worse, the same entry says the binding constraint is thermal, not electrical:
the dev board's single B5819WS Schottky is "~435 mA at 25 degC and ~283 mA at a
60 degC interior" `[repo] config/figures.yaml:524`. The interior temperature
that selects between those two numbers is measured at **M8**
`[repo] ROADMAP.md:192` — the last milestone in the project. See B6-15.

### B6-14 — **Five acceptance tests exercise LED strips that do not exist until
M6** (blocking)

The ROADMAP diagnosed this once, precisely, and then left the other four:

> "**M8 exists because E11 tests a topology that does not survive to the
> finished instrument.** At E11 the LED strips are not installed — **they arrive
> at M6** — and the body is not closed, so the loom under test is not the final
> loom." `[repo] ROADMAP.md:105-109`

The strips are M6 `[repo] :76`, Phase 4 `[repo] :161`. Every row below is
Phase 1–3:

| Where | Text | Phase | Re-run at M8? |
|---|---|---|---|
| E11 `[repo] :52` | "Breath output clean while display, **LEDs** and WiFi are exercised" | 3 | **yes** — `[repo] :78` |
| E4 measurement `[repo] :202` | "Key-chain error counter over an hour, **LEDs and WiFi active**" | 1 | **no** |
| E6/E9 measurement `[repo] :200` | "Pitch jack **while sweeping the LEDs**, and while the rack is busy" | 2 | yes, but the table does not say so — only M8's row does `[repo] :78` |
| M4 measurement `[repo] :203` | loom fit "against the real cavity section **alongside the LED strips** and the breath tube" | 3 | **no** |
| ADR 0014 `[repo] docs/decisions/0014-lighting.md:261` | "Measure the step at **E4 with the strips running**" | 1 | **not in the ROADMAP at all** |

The E4 error counter is the sharpest. Its stated purpose is "A non-zero count
says **the looms need work while the body is still openable**", and the row was
recently edited to say "**This covers the loom again** now that the chain runs
through it" `[repo] ROADMAP.md:202`. At E4 — Phase 1, dev boards on a bench,
against M2's hand-wired mule `[repo] :72` — there is no final loom and there are
no strips. This is the identical defect M8 was invented to fix, and M8's
enumerated re-runs `[repo] :78` do **not** include the key-chain error counter.

The ADR 0014 row is a second, independent gap: it sizes the note-on/note-off
hysteresis "from the measured LED-induced step, **not from a guessed value**"
`[repo] docs/decisions/0014-lighting.md:259-261`, that hysteresis is F2's note
gating `[repo] ROADMAP.md:142`, and the measurement appears in no ROADMAP row.

### B6-15 — **The 3 K/W that sizes the lighting budget is measured at M8, after
every decision it informs** (blocking)

"**Interior temperature rise under load** | **M8** | The lighting budget is set
from an **estimated 3 K/W**" `[repo] ROADMAP.md:192`.
`docs/decisions/0014-lighting.md:183-184`: "**Validate it at M8's thermal
soak**, which exists anyway, rather than trusting 3 K/W. **That figure is a
bounding estimate, not a measurement.**"

What 3 K/W already decided, all before M8: the 3 W shared clamp and its
"roughly 9 K of interior rise" `[repo] docs/decisions/0014-lighting.md:177-178`;
the brightness cap ADR 0014 "deliberately makes non-configurable"
`[repo] config/figures.yaml:526`; the LED density, count and placement built
into M6 `[repo] ROADMAP.md:76`; and, through B6-13, the Schottky derating that
decides whether the matrix is electrically survivable at all.

If the soak fails, the remedy is at M6 (strips, density, diffuser) or in the
firmware clamp (F9, Phase 5 `[repo] :162`) — both upstream of the milestone that
discovers it. M8's row says "Nothing closes until this passes" `[repo] :78`,
which is true and is not a schedule.

The companion row is handled correctly and shows the contrast: "**Breath zero vs
cavity temperature** | M8 | ... **The body opens, so a vent can be added at M8
or afterwards**" `[repo] :194`. That row reasons about reversibility. The 3 K/W
row does not.

### B6-16 — **`breath-working-point` is assigned to a milestone with no breath
apparatus in it** (blocking)

`breath-working-point`, `status: disputed`, `decided_by: "M1, with a player and
a manometer. Sets the panel gain range AND the ADC headroom."`
`[repo] config/figures.yaml:315-322`.

M1 is "**Switch characterisation**" — cutouts, retention, bounce, hysteresis,
spring weight `[repo] ROADMAP.md:71`. It contains no sensor, no tube, no
mouthpiece and no manometer. M1 is also gated on "Switches arriving"
`[repo] :11`, which has nothing to do with a player blowing into a tube.

The milestone that does have a player, a mouthpiece, a tube and a trap is **E2**
— "**a human plays it for 20 minutes** through a real mouthpiece, tube and
trap" `[repo] ROADMAP.md:42`. `docs/decisions/0003-breath-sensing-path.md:742`
confirms E2 needs only a bare tube, so nothing blocks it.

And the ROADMAP's measurement table has **no row for the breath working point at
all** `[repo] ROADMAP.md:187-204`, so a disputed, load-bearing figure points at a
milestone whose row does not know it exists. Its two consumers — "the panel gain
range" (E10, Phase 3 `[repo] :51`) and "the ADC headroom" (E2, Phase 1
`[repo] :42`) — straddle the phase boundary, so if it really did resolve at M1
one of the two consumers would still be fine and the other would already be
built.

### B6-17 — **The latency budget's characterisation table attaches milestones to
3 rows of 13, and the one row that validates the whole table has none** (medium)

The ROADMAP delegates: "The full characterisation table lives in [the latency
budget]" `[repo] ROADMAP.md:183-184`, implying those measurements are scheduled.
They are not. Of thirteen rows `[repo] docs/reference/latency-budget.md:116-127`,
three name a milestone — restrictor/E2 `[repo] :117`, SPI-at-length/E11
`[repo] :120`, rack ripple/E6 `[repo] :122` — and ten do not, including:

- "**End-to-end, in one shot** ... **the one measurement that validates or
  refutes the entire table above**" `[repo] docs/reference/latency-budget.md:127`
- "**ADC + SPI round trip** ... Datasheet conversion time excludes driver
  overhead" `[repo] :119`
- "**KS-33 contact bounce**" `[repo] :118` — which the ROADMAP does schedule, at
  M1 `[repo] ROADMAP.md:71`, but the latency budget does not say so, so the two
  tables are independently maintained copies of one plan.

This matters because `loop-budget` is `settled` at "196-241 us of 250 us"
`[repo] config/figures.yaml:429-432` — 78–96 % duty [calc: 196/250 = 78.4 %,
241/250 = 96.4 %] — and its own escape note records that the owner document
carried a comfortable 136 µs / 54 % figure while the register carried the true
one `[repo] config/figures.yaml:438-450`. At 96 % worst case, the measurement
that refutes it forces an architecture change (loop rate, SPI topology, or the
carrier). It is scheduled nowhere.

Also missing from the ROADMAP: "Rack rail ripple, both directions ... **Gates
E6**" `[repo] docs/reference/latency-budget.md:122` — a measurement that
declares itself a gate on a milestone, and the ROADMAP's E6 row `[repo] :47` and
its two E6 measurement rows `[repo] :199,200` do not carry it.

### B6-18 — E6 sizes `R-ILIM` from a load that does not exist until Phase 4 (medium)

"**Inrush with a current probe, on switch-on *and* hot-plug** | **E6** | Sizes
the load switch's current limit from measurement rather than from a guess"
`[repo] ROADMAP.md:199`, and the part row says "Sense resistor, **value from
E6**", `status: open`
`[repo] hardware/module/umbilical-load-switch/bom.csv:5`.

E6 is Phase 2 `[repo] :159`. The load it must limit is the whole instrument —
`umbilical-current` 359 mA typical play `[repo] config/figures.yaml:458-462` —
whose LED strips arrive at M6 and whose display board and final loom arrive at
M7, both Phase 4 `[repo] :161`. At E6 the draw is a dev board on a bench.

The window is tight enough to care: the LT1641's own sense threshold is ±17 %
(39/47/55 mV), giving 0.78 / 0.94 / 1.10 A at 50 mΩ, and the BOM row already
records that the ±11 % target window is **narrower than the part's own
tolerance** `[repo] hardware/module/umbilical-load-switch/bom.csv:5`. Selecting
against a partial load and never re-measuring against the full one spends that
margin blind. Nothing in E14 `[repo] :55` or M8 `[repo] :78` re-measures it.

---

## 4. Blocked and disputed figures

`config/figures.yaml` holds 35 entries: 30 `settled`, 4 `disputed`, 1 `blocked`
[calc: `grep -o "status: [a-z]*" | sort | uniq -c` gives 30/4/1]. The commit
hook agrees — "5 unresolved (tracked)" `[repo]` hook output.

| Figure | Status | `decided_by` | Milestone that resolves it | Ordering |
|---|---|---|---|---|
| `matrix-led-current` | blocked | "A BENCH MEASUREMENT AT E1" `[repo] figures.yaml:522` | E1 exists, but measures idle | **broken — B6-13** |
| `breath-working-point` | disputed | "M1, with a player and a manometer" `[repo] :321` | M1 has no breath apparatus | **broken — B6-16** |
| `pitch-cents-budget` | disputed | "one coherent table, then cite it" `[repo] :330` | **none** | **B6-19** |
| `dig-gnd-topology` | disputed | "The 2-layer vs 4-layer decision" `[repo] :396` | **none** | **B6-20** |
| `ref5050-grade` | disputed | "Changing one letter in the order code" `[repo] :543` | **none** | **B6-21** |

### B6-19 — E9 is the project's decisive milestone and has no numeric pass
threshold (blocking)

"**E9 is the milestone that decides whether this is an instrument or a thing
that is always slightly out of tune.**" `[repo] ROADMAP.md:57-58`. Its criterion
is "1V/oct verified against a real VCO ... loaded the way it will be played"
`[repo] :50` — a method, not a threshold.

The threshold is `pitch-cents-budget`, `status: disputed`, candidates 0.42 /
0.85 / 1.35 / ~1.2 cents `[repo] config/figures.yaml:324-329`. The spread is
3.2× [calc: 1.35 / 0.42]. Its resolution is a documentation fix — "pitch-stage.md
has two contradictory budget tables back to back and states no total"
`[repo] :330` — needing no bench and no hardware, so it can be closed today, and
the ROADMAP schedules nothing that closes it.

Second-order: `hardware/module/pitch-stage/circuit.yaml` declares
`fig:pitch-cents-budget` **and** `fig:dig-gnd-topology` as dependencies
`[repo] hardware/module/pitch-stage/circuit.yaml`, so the pitch page is
declared-dependent on two disputed figures and is the owner of one of them.

### B6-20 — The 2-vs-4-layer decision gates a disputed figure, has no milestone,
and E12 asserts one of the disputed answers as its done-when (blocking)

`dig-gnd-topology` is disputed between three mutually exclusive candidates, one
of which is ADR 0004's "**Its own path to the star**"
`[repo] config/figures.yaml:391-394`, and `decided_by` is "The 2-layer vs
4-layer decision, which is upstream of it" `[repo] :396`.

E12's done-when states: "**Ground laid out to the star rule in ADR 0004** — one
origin at the power inlet, `PWR_GND` and `DIG_GND` **each on their own copper**"
`[repo] ROADMAP.md:53`. That is candidate 1, written as settled, in a milestone
row, while the register says the question is open and that
`power-entry.md` "states that ADR 0004 was corrected on this point. **IT WAS
NOT**" `[repo] config/figures.yaml:398`.

`docs/reference/pcb-pipeline.md:245-249` calls 2-vs-4 "**Open**", "a cost
decision", and "**upstream of stage 3**". Meanwhile all three PCB rows in the
BOM already assert two layers — `PCB-CARRIER` "2-layer PCB - real-time carrier"
`[repo] hardware/bom.csv:27`, `PCB-CLUSTER` "2-layer PCB - key cluster board"
`[repo] hardware/bom.csv:40`, `PCB-MODULE` "2-layer PCB - 10HP CV interface"
`[repo] hardware/bom.csv:121`, all `status: open`.

So: the register says open, the pipeline says open and upstream, the BOM says
2-layer three times, and the ROADMAP states the consequence as a completed
design rule. No milestone owns the decision.

### B6-21 — `ref5050-grade` is a part change with no milestone and a stated
downstream block (medium)

"`REF5050AIDR` is the *Standard* grade ... not the ±0.05 % / 3 ppm/°C the corpus
asserts in three places ... **it is a part change, not a documentation fix**"
`[repo] config/figures.yaml:537-543`. The pipeline adds: "**So this blocks
precursor 1 for that row**, not just the figures list"
`[repo] docs/reference/pcb-pipeline.md:82-86`.

The part sits on the carrier `[repo] hardware/carrier/breath-excitation-reference/`
and is in the ratiometric breath scale-factor path — i.e. it is load-bearing
from E2 onward `[repo] ROADMAP.md:42` and must be correct before parts are
ordered for E13 `[repo] :54`. The ROADMAP's "Open items blocking work" table
does not list it.

### B6-22 — The ROADMAP's "Open items blocking work" table and the register's
unresolved set are disjoint (blocking)

`[repo] ROADMAP.md:226-231` lists exactly four open items: plate stiffening
(M4, M5), CAD tool (M4), oak thickness (M4), inter-MCU frame format (E4b).

`config/figures.yaml` lists five unresolved figures (B6-13, B6-16, B6-19,
B6-20, B6-21). **The two sets do not intersect.** Neither does the pipeline's
own open set — 2-vs-4 layers, the LT5400 exposed pad, and (formerly)
`cref-out-node` `[repo] docs/reference/pcb-pipeline.md:88-107`.

The table's title claims completeness for the thing a planner reads. It is
missing every figure the project's own register marks unresolved, and it lists
nothing at all against E6–E14 or M6–M8.

One genuine positive: `cref-out-node` and `riso-ref-topology` both moved to
`settled` on 2026-09-21 `[repo] config/figures.yaml:364-368, 400-404`, and
`cref-out-node`'s note records that it **unblocked** `riso-ref-topology`
`[repo] config/figures.yaml:381`. That dependency was handled correctly and in the right order.
(I did not open the preflight report those entries cite; I am reporting what the
register states, per the cold rule.)

---

## 5. Gates

### Which milestones are genuine gates, and whether they say so

| Milestone | Genuinely a gate? | Stated as one? |
|---|---|---|
| **M3** Layout locked | yes | **yes** — "No aluminium cut before this" `[repo] :73`, restated `[repo] :86` |
| **M8** Final-assembly gate | yes | **yes** — "Nothing closes until this passes" `[repo] :78` |
| **E13** (for M5) | yes | **yes** — as a rule `[repo] :92-95`, not in M5's row beyond "Not before E13" `[repo] :75` |
| **E14** Carrier re-validation | **yes** — it is what makes M7 safe `[repo] :97-103` | **no** — the row states a scope, not a gate `[repo] :55`; see B6-05, B6-06 |
| **E9** Pitch calibration | **yes** — the ROADMAP says so in prose `[repo] :57-60` | **no** — the row has no pass threshold, and its threshold figure is disputed; see B6-19 |
| **E1** PSRAM | **no longer** | **stated as one anyway** — see B6-23 |
| **E2** breath/restrictor | yes for the latency budget `[repo] latency-budget.md:39,85` | partially — E2's row is thorough `[repo] :42` but does not say the budget cannot close without it |
| **The 2-vs-4-layer decision** | yes, "upstream of stage 3" `[repo] pcb-pipeline.md:249` | **not a milestone at all** — B6-20 |

### B6-23 — E1 still states a done-when that two other documents call settled (medium)

E1: "Both running; **PSRAM confirmed quad, not octal**, and **idle current
measured** before the carrier is laid out (ADR 0007)" `[repo] ROADMAP.md:41`.

The measurement table, 154 lines later: "**PSRAM mode on the ESP32-S3-Matrix** |
E1 | **No longer a gate** — settled on paper two ways ... Print the pin list
anyway; it costs thirty seconds" `[repo] ROADMAP.md:195`. ADR 0007 agrees in the
strongest terms: "This was carried as a gate on E1 and a blocker on the carrier
layout. **It is neither** ... the carrier layout is not blocked on it"
`[repo] docs/decisions/0007-imu-selection.md:231-241`.

The idle-current half of that sentence *is* still a real precondition on the
carrier layout `[repo] docs/decisions/0007-imu-selection.md:220`, and E1 ≪ E13
so it orders fine. It is the PSRAM half that should be demoted from a done-when
to the pin-list print the ADR asks for.

### B6-24 — M8's reasoning survives the restructure; its three loudness fixes do
not (medium)

**The reasoning holds.** I checked each clause of "M8 exists because E11 tests a
topology that does not survive" `[repo] ROADMAP.md:105-110`:

- "At E11 the LED strips are not installed — they arrive at M6" — **still true**
  `[repo] :76,161`.
- "the body is not closed, so the loom under test is not the final loom" —
  **still true**; the body closes at M7/M8 `[repo] :77,78`.
- "The single test that validates the entire analog-breath decision was running
  against a configuration that changes afterwards" — **still true**; that test
  is `[repo] docs/reference/latency-budget.md:126`, "the end test for the analog
  breath decision".

The one thing that moved is the **cost** of failing it: ADR 0009 says "failing
one of them after M8 is now a **repair rather than a rebuild**"
`[repo] docs/decisions/0009-enclosure-construction.md:640`, and M8's own row now
says it is "the last gate before the instrument is treated as finished rather
than the last moment it can be opened" `[repo] :78`. So "**This was the most
important missing milestone in the project**" `[repo] :110` is still defensible
on validity grounds, and is no longer defensible on irreversibility grounds. The
sentence does not distinguish the two, and its neighbours (B6-11) still argue
from the irreversibility version.

**One consequence is unexplored:** since the body opens, nothing requires the
E11 re-run to wait for the lid. Running it at M7, with the final loom and the
strips installed and the lid off, finds the same defects while a probe still
fits. M8 would then re-run it closed, as a confirmation rather than a discovery.

**The three "free" firmware fixes are all late.** `[repo] ROADMAP.md:215-219`
ranks the silent failures and says "All three fixes are firmware and all three
are free":

| Fix | Needs | Phase | Silence begins |
|---|---|---|---|
| CRC the calibration blob; hard **UNCALIBRATED** state on the display | F8 `[repo] :149` + F7 `[repo] :147` | 5 | **E9**, Phase 2 `[repo] :50` |
| Flag any key closed at boot or held beyond N seconds | F1 `[repo] :141` | **unphased (B6-02)** | **E4/E5**, Phase 1 `[repo] :44,46` |
| Continuous auto-zero + show the current zero | F2 `[repo] :142` + F7 | 5 / unphased | **E2**, Phase 1 `[repo] :42` |

"Free" is true of the code and false of the schedule. Each fix is three to four
phases behind the milestone whose failure it makes loud, and the table's own
argument is that these failures "get blamed on the player or on firmware for
years" `[repo] :212` — i.e. the damage is done during the interval the plan
leaves open.

---

## 6. Does the restructure change the plan?

**Yes, and `docs/reference/pcb-pipeline.md` has not followed it.**

### The dating is unambiguous

`pcb-pipeline.md` was last written at `547134f` `[repo] git log -- docs/reference/pcb-pipeline.md`.
In `git log --oneline`, that commit is **#58**; the restructure plan `81c081d`
is **#34**, Phase A's move `9daec7f` is **#32**, the Phase B pilot `c52ed75` is
**#28**, and the dependency graph `07c7ae8` is **#10** `[repo]`. So the pipeline
predates every commit of the restructure, and no later commit touched it.

At `547134f` the module directory held **exactly six pages**
`[repo] git ls-tree -r --name-only 547134f -- hardware`:
`breath-output-stage.md`, `breath-receive-stage.md`, `digital-and-supervision.md`,
`mod-channels.md`, `pitch-stage.md`, `power-entry.md`. Boards lived under
`hardware/controller/` and datasheets under `hardware/datasheets/`.

### B6-25 — "the six" is now twelve, in three places (blocking)

`[repo] docs/reference/pcb-pipeline.md`:

- `:58` — "Reconcile net names across the **six pages** first."
- `:67` — "Seven rails, **six modules**."
- `:113-116` — "`pcb/src/module/*.py`, **one module per schematic page**,
  `module.py` importing **the six**."

`hardware/module/` now holds **12** circuit pages plus the board page
`[repo] ls hardware/module/*/*.md`, which `hardware/README.md:21` states
independently ("The 10HP Eurorack module — **12 circuits**"). Two of the three
`interfaces/` circuits also terminate on the module —`spi-link` and
`breath-sense-link` `[repo] hardware/interfaces/README.md` — so the transcription
set is 12–14 pages, not six.

Stage 3's placement contract inherits it: "`hierplace` **groups by module = by
schematic page**" `[repo] :152-153`. Twelve groups instead of six changes the
placement, and three of the twelve have **no BOM fragment at all** —
`digital-and-supervision/`, `link-supervision/`, `panel/` `[repo]` (checked by
`for d in hardware/*/*/; do [ -f "$d/bom.csv" ] || echo "$d"; done`) — so they
produce empty SKiDL modules and empty groups.

### B6-26 — A page-by-page netlist omits 50 BOM rows, including the DAC (blocking)

`hardware/unplaced.csv` holds "the BOM rows **no schematic page names**"
`[repo] hardware/README.md:42-45`. It has **50 rows / 105 units** against a
master of 138 rows / 388 units [calc: summed `qty` over both files]. Excluding
`not-needed`, that is **24 module rows / 49 units** and **10 controller rows /
33 units** [calc].

Verified by grep that these refdes appear **only** in `bom.csv` and
`unplaced.csv` and in no schematic page: `U-DAC`, `J-CV`, `J-UMBILICAL`,
`U-REG-DAC`, `R-REG-SET`, `FB-IN`, `C-TIMER-LOADSW`, `C-GATE-LOADSW`,
`D-REVPOL` `[repo] grep -R over hardware/`.

So stage 1 as written — one SKiDL module per schematic page, six or twelve —
emits a module netlist with:

- **no DAC8568** (`U-DAC`, the part the whole module exists to carry — and
  `hardware/module/dac8568/dac8568.md` draws its pins `SCLK`/`SYNC`/`DIN`/
  `LDAC`/`CLR`/`VREFOUT`/`AVDD` and its two support resistors `R-CLR-PU`,
  `R-LDAC`, but never names the part refdes `[repo]`)
- **no CV jacks** (`J-CV` ×6)
- **no etherCON** (`J-UMBILICAL` ×2)
- **no AVDD rail** (`U-REG-DAC`, `R-REG-SET`, `C-REG-ADJ`) — the rail E6 brings
  up `[repo] ROADMAP.md:47` and E7 trims `[repo] :48`
- **no input ferrites** (`FB-IN` ×4), **no reverse protection** (`D-REVPOL` ×3),
  **no bulk** (`C-BULK-RAIL` ×4), **no module TVS** (`U-TVS-MODULE`)
- **neither load-switch timing capacitor** (`C-TIMER-LOADSW`,
  `C-GATE-LOADSW`) — both `status: selected`, both owning a settled figure
  `[repo] config/figures.yaml:333-353`

ERC will not catch it. A part that is never instantiated raises no unconnected
pin. This is the pipeline's own failure class — "the merge happened before
anything could see it" `[repo] docs/reference/pcb-pipeline.md:62-63` — relocated
by the restructure from net names to part existence.

### B6-27 — The pipeline covers one board of six (medium)

Stage 1 emits `module.net`; stage 4 opens `pcb/module/module.kicad_pcb`
`[repo] docs/reference/pcb-pipeline.md:116,179`. The tree now has four board
directories `[repo] hardware/README.md:17-22`, and E13 builds "**Carrier +
cluster PCBs**" — a carrier plus four identical cluster boards
`[repo] ROADMAP.md:54`, `PCB-CLUSTER` qty 4 `[repo] hardware/bom.csv:40`. That is
six physical boards; the pipeline describes one, and the ROADMAP never mentions
the pipeline (see B6-28).

The carrier is not the easy case: `cref-out-node` and `riso-ref-topology` are
both carrier figures owned by `hardware/carrier/carrier.md`
`[repo] config/figures.yaml:368,404`, and two of the five sim decks sit under
carrier and interface circuits.

### B6-28 — There is no milestone between E11 and E12 (blocking)

`grep -n "pipeline\|SKiDL\|KiCad\|netlist\|layer" ROADMAP.md README.md` returns
nothing relevant `[repo]` — no hit in either file. The E track goes E11 "SPI at
2 MHz ... over the real cable" `[repo] :52` → E12 "10HP panel cut, **module
assembled and racked**" `[repo] :53`.

Between those two rows sits an entire 280-line document describing six stages,
an open cost decision that gates the grounding scheme
`[repo] docs/reference/pcb-pipeline.md:245-249`, three ground questions that
"must be decided in one sitting" `[repo] :88`, five SPICE decks, a netlist
precursor list, and a manual routing handoff. None of it is a milestone, none of
it is in a phase, and none of it is in the "Open items blocking work" table
(B6-22).

### B6-29 — The pipeline's own blockers have moved under it (medium)

Three items in `pcb-pipeline.md` are now out of date in the corpus's favour, and
one against:

- **`cref-out-node` is settled** `[repo] config/figures.yaml:364-368`. The
  pipeline still lists it as the third of "Three ground questions that must be
  decided in one sitting" `[repo] docs/reference/pcb-pipeline.md:104-105`, and
  still blocks the `R-ISO-REF` stability sim on it — "**Blocked on
  `cref-out-node` first**" `[repo] :127`. It is not blocked.
- **`riso-ref-topology` is settled**, with TI's worked answer adopted —
  R_ISO 37.4 Ω, 85.9° simulated `[repo] config/figures.yaml:400-405`. The
  pipeline presents that same SBOS737C §8.2.3 result as the thing still to be
  established `[repo] :127`.
- **`opa2197-output-impedance` (375 Ω) and `ferrite-bias-impedance` landed** —
  the pipeline's "Two numbers to check any EMC or stability work against"
  `[repo] :141-146` are now `settled` register entries
  `[repo] config/figures.yaml:505-509, 528-531`, so that paragraph should be a
  citation, not a restatement (CLAUDE.md rule 1).
- **Against:** "1.7 dB of claimed margin, **unretrofittable inside a bonded
  body**" `[repo] :126` — the body is not bonded
  `[repo] docs/decisions/0009-enclosure-construction.md:493-494`. Same surviving
  argument as B6-11, and here it is the stated reason that sim is ranked first.

One thing the restructure improved that the pipeline does not know about:
precursor 1's `AGND`/`BREATH` collisions `[repo] :58-63` are now structurally
addressed — the three cross-board circuits are one directory each, each page
carries an `## Interfaces` table with an **End** column naming which side of the
cable a node sits on, and "**the breath table states both collisions
explicitly**" `[repo] hardware/interfaces/README.md`. A transcription run today
should read those tables rather than re-derive the collisions from the drawings
the precursor warns about.

Also landed since the pipeline was written: precursor 5's `U-TVS-SPI` is now
`SOT-23-5` in the BOM `[repo] hardware/bom.csv:46`. Precursor 6
(`ref5050-grade`) is still open `[repo] config/figures.yaml:540`.

### B6-30 — E12's bracing rationale is stated against a superseded panel width (low)

"etherCON braced to the PCB — good practice **at 8HP** rather than the
structural necessity it was at 6HP" `[repo] ROADMAP.md:53`. `panel-width` is
"50.50 mm (**10HP**)", settled `[repo] config/figures.yaml:270-273`.

The checker cannot see it: `panel-width`'s `forbidden` list carries "The panel is
8HP", "inside 8HP", "at 8HP this", "Comfortable at 8HP"
`[repo] config/figures.yaml:276` — and E12's spelling is "at 8HP rather than",
which matches none of them. Exactly the class of near-miss CLAUDE.md §2
describes. Under rule 1 the row should cite `panel-width` and state no width.

---

## 7. Checked and found correct

Recording these so the next reviewer does not re-derive them.

- **The shortest path is buildable.** "E1 → E2 → E4 → E5 on a bench, mounted to
  M2" `[repo] ROADMAP.md:23` skips E4b `[repo] :45`, and that is **correct**:
  the real-time board owns USB MIDI, not the display board
  `[repo] docs/decisions/0013-two-mcu-split.md:30,37`. E5 does not need the
  inter-MCU link. (It does need F1 — B6-02.)
- **M1 no longer gating M4 holds.** `[repo] ROADMAP.md:80-84`, confirmed by
  `[repo] docs/decisions/0009-enclosure-construction.md:89` and by
  `plate-thickness` being settled off the vendor drawing
  `[repo] config/figures.yaml:494-498`.
- **E2 is not blocked on the mouthpiece.** "A raw tube end is acceptable ... E2
  and E5 can proceed on a bare tube"
  `[repo] docs/decisions/0003-breath-sensing-path.md:740-742`, and E2 is where
  the bore is settled `[repo] :753-763`, matching E2's row `[repo] ROADMAP.md:42`.
- **The restrictor ordering is right.** Sized at E2 `[repo] :204`, and the
  latency budget cannot close without it `[repo] docs/reference/latency-budget.md:39,85,117`
  — E2 is Phase 1, so it lands before everything that consumes it.
- **`dac-rail` / E7 is not an inversion.** E6 brings up a 5.21 V rail
  `[repo] ROADMAP.md:47` and E7 selects `R-REG-SET` on the bench `[repo] :48`.
  I expected a conflict; the BOM row resolves it — the register value "is the
  **starting point**", the part is "SELECTED ON THE BENCH at E7 (this is a
  population of one)", "Buy a handful of neighbouring E96 values"
  `[repo] hardware/bom.csv:111`. The 5.00 V hard floor is stated in all three
  places consistently `[repo] ROADMAP.md:48`, `config/figures.yaml:236`,
  `hardware/bom.csv:94`. **Correct as written.**
- **`cref-out-node` → `riso-ref-topology` was sequenced correctly**, per the
  register's own record `[repo] config/figures.yaml:381,411`.
- **The five SPICE decks followed the restructure**, one per circuit directory:
  `module/umbilical-load-switch/sim`, `module/breath-receive-stage/sim`,
  `module/power-entry/sim`, `module/pitch-stage/sim`,
  `carrier/breath-excitation-reference/sim` `[repo] find hardware -type d -name sim`
  — matching the pipeline's five ranked sims `[repo] pcb-pipeline.md:124-130`.
  The pipeline does not name the new locations, but the content did not go stale.
- **"Three ordering rules a design review found violated"** `[repo] :90` — all
  three rules are present and each is still correctly argued, except the
  bondedness clause noted in B6-24.

## 8. Limits of this review

- **Cold rule:** I did not open `docs/review/**`. Where `config/figures.yaml`
  cites a preflight report as its authority (`cref-out-node`,
  `riso-ref-topology`), I report the register's claim, not a verification of it.
- I did not verify the *electrical* correctness of any circuit, only the order
  in which the plan builds them.
- B6-03 (E10/E11) is the one finding where a benign reading exists — E10 on a
  bench-length cable, E11 on the real one. I file it because neither document
  says so and both assign the test to E10.
- B6-26's headline count (50 rows) includes mechanical and tooling rows that
  legitimately have no netlist presence. The **24 module rows / 49 units**
  figure is the one that bears on the netlist, and the named parts were each
  verified by grep.
