# Verified by hand — not agent claims

**In progress. 19 of 20 agents in.**

Everything below was checked directly against the repo in the main session,
independently of the agent that reported it. An agent finding is a *claim*
until it appears here. Earlier waves produced findings that were wrong, and
this wave has already produced one mis-attribution (recorded at the bottom).

Node-indexed, like the reports.

## Confirmed — two documents specify incompatible hardware

| Node | What one says | What the other says | Consequence |
|---|---|---|---|
| **`CLR`** (DAC8568) | `digital-and-supervision.md` draws `[R-CLR-PD 10k]` to `AGND` | `bom.csv` row 67 is **`R-CLR-PU`**, "holding … `CLR` **inactive**" | `CLR` is active low and the watchdog that used to drive it is deleted, so **as drawn it is asserted forever**: six dead CV outputs, no SPI write able to change them |
| **`R1b`** (`R-SER-BREATH-INST`, AGND leg) | `bom.csv` qty **2**, instrument-side, **unretrofittable**; `breath-receive-stage.md`'s 482 Hz pole depends on it | **Zero occurrences** in `carrier.md` — the schematic page for the board that must carry it, which says of itself "layout is now" | The link CMRR budget rests on a part that is not on the drawing |
| **`R-ISO-REF`** | In `bom.csv` | **Zero occurrences** in `carrier.md` §2, drawing *and* component table | A2 independently derives that without it the reference buffer **oscillates** — 100 nF of sensor decoupling on an OPA2197 output whose Ro back-solves to 75.8 Ω |
| **`C-FB-PITCH`** | **1 nF** in the `pitch-stage.md` drawing and its split-loop table | **2.2 nF** in the same page's value table and in `bom.csv` | Two different compensation networks |
| **ADR 0006 vs everything** | ADR 0006 still specifies **"1 nF across the feedback resistor"** (2 occurrences) | `pitch-stage.md` and `bom.csv` say output-to-(−), and that "across the feedback resistor" gives **18° of phase margin with 2 m of cable** | The accepted ADR still prescribes the arrangement the schematic says is unstable |
| **LM311, 74HC123** | Both **deleted** — `digital-and-supervision.md` prose, ADR 0004, `bom.csv` | Both still **drawn** in that same file's schematic, with rails allocated in its supply table, and `bom.csv` `C-DECOUPLE` qty 21 explicitly counts "LM311 on +/−12V = 2" | A board built from the drawing carries two ICs nobody wants; decoupling count should be 19 |
| **Marker allocation** | `key-layout.yaml`, ADR 0001, `cluster-boards.md`: **8 marker / 3 free** | `carrier.md` lines 454–455 still say **6 marker / 5 free** | Hard-wired copper on boards that bond shut |

## Confirmed — reference designators that do not resolve

Drawn in a schematic, absent from `bom.csv`:
`R-SCLK-SER`, `R-MOSI-SER`, `R-CS-SER`, `R-LED`, `R-OE-PU`, `F-CHAIN`,
`U-TVS-CHAIN`, `R-CHAIN-SER`.

In `bom.csv`, used by no schematic: **`R-SPI-SER`** (qty 3).

`carrier.md` §4 additionally claims *"only `R-MOSI-SER` reached the BOM,
qty 1"* — `R-MOSI-SER` is not in the BOM at all. The three series resistors
and the BOM's `R-SPI-SER` are the same three parts under two naming schemes,
and neither side knows about the other.

The last three (`F-CHAIN`, `U-TVS-CHAIN`, `R-CHAIN-SER`) were proposed in
this session's own drawings and never given BOM rows. Same defect, made
today.

## Confirmed — errors introduced in this session

- **`cluster-boards.md` §2 figure wires the switch to 3V3**, not GND,
  contradicting its own caption "shorts to GND when pressed". As drawn a
  press is a 33 mA rail short and the register input never moves.
- **Bits 22, 23 and 31 have no pull-up budgeted.** The component table,
  `bom.csv` and `carrier.md` all carry 21 pull-ups for exactly the 21
  *switch* positions; the three free bits need them too. Floating CMOS
  inputs — the precise fault ADR 0001 fix 6 exists to prevent.
- **`carrier.md` left stale on the marker count** (above), in the same
  session that fixed that pattern twice.

## Agent claims checked and NOT confirmed as stated

- **A6 F2** attributed a channel-7 refresh contradiction to ADR 0006 versus
  `firmware/README.md`. The contradiction is real but sits *inside*
  `firmware/README.md`: its line 50 says channel 7 is "written once at
  boot", while `mod-channels.md` cites that same file's statelessness rule
  as "refresh all six populated channels every pass". Right defect, wrong
  parties.
- **B2's brief was wrong, not the repo.** This session briefed B2 that the
  pitch stage gives ±5 V about a 2.500 V intercept. It gives **−2 to +7 V**.
  The agent judged against the repo rather than the brief, which is correct
  behaviour and worth recording as such.


---

# Convergence — where independent cold agents agreed

The point of running twenty agents that cannot read each other is that
agreement means something. These are conclusions reached **more than once,
from different directions, with no contact**. They carry more weight than
any single finding, including the ones I verified by hand.

## The instrument does not power up

**Three agents now, three routes, no shared inputs.**

**A7** (module power entry, cold design review): `C-TIMER-LOADSW` at 10 nF
is wrong by 40–400× — `t = 1.233·C/I_TIMER` needs 81 nF to 4.1 µF for
50 ms, so the module latches roughly 1 ms into every start. There is **no
gate capacitor anywhere** in the BOM or the schematic, although the FET
sizing, the boot analysis and ADR 0005's 50–100 ms specification all rest
on a "programmed ramp". And the start margin is 1 %, not the 47 % claimed,
because the page's start table has a capacitor-charging row and **no load
row at all**.

**C3** (sequencing falsification): the LT1641's real sense threshold is
**47 mV, not 50**, so `R-ILIM` at 50 mΩ limits at **0.940 A**. Foldback
regulates the sense drop to 12 mV at zero output — **240 mA**, below the
0.53 A programmed ramp — so **every start begins in current limit** and
takes ~62 ms against a ~50 ms timer. It latches at the end of every start.
Delete foldback and the margin is still 4 %, inside the part's own
threshold tolerance.

**B3** (comparative practice) went to the datasheet equation instead:
`C(nF) = 62·t(ms)` gives **~3.1 µF** for 50 ms, and the 3 µA / 1.233 V ramp
gives **~122 nF**. The specified 10 nF is **12× to 300× too small** — a
0.16–4 ms fault timer. It independently reached the foldback conflict too:
the datasheet reduces the limit when `FB` is low, *which is the entire
duration of the start ramp*.

`power-entry.md` programs foldback in one section and asserts "a normal
start never enters current limit" in another. None of the three agents
could see the others' reports, and none of them agree on the exact
replacement value — 81 nF–4.1 µF, ~122 nF, ~3.1 µF — which is itself a
signal that the value must be derived from a read datasheet, not picked
from a review.

B3 adds the sizing case nobody had named: **the hot-plug, not the cold
start.** etherCON invites live insertion; 2.2 mF at 0.94 A is 28 ms against
a 50 ms timer *before* foldback. That also weakens ADR 0005's stated reason
for choosing the latching `-1` over the retrying `-2`.

**Consequence:** the first thing that happens at E6 is that nothing
happens. This is a before-order fix, not a bring-up fix.

## The umbilical pin map is wrong — for three different reasons

Three agents, three mechanisms, one set of pins. The fixes must be
**combined**, not chosen between.

| Agent | Mechanism | Fix |
|---|---|---|
| **B5** | Published RJ45-for-other-purposes standards leave pins 4/5 empty so a misplug into PoE or telephone destroys nothing. `MOSI`/`CS` are on exactly those pins. PoE also delivers power *common-mode* through centre taps; this design puts +12 V/`PWR_GND` **differentially across pins 3-6**, straight across a switch port's transformer | Move `MOSI`/`CS` off 4/5; power onto a compact pair |
| **A4** | `MOSI` and `CS` share one twisted pair, so the signal whose glitch re-frames the DAC word (a *sticky* failure by the repo's own taxonomy) sits in the tightest coupling with its busiest aggressor, no return between them. ~2.0 V coupled step against a 0.8 V `V_IL` | `CS` pairs with `DIG_GND`; `SCLK` pairs with `MOSI` |
| **C3** | `R-SPI-PULL`'s cable-side `CS` is specified to pull up to **3V3 — a rail the module does not have**, and not one of the eight conductors | Re-specify against a rail that exists |

## The series resistor value, with a refinement

**B5** and **A4** both reject the repo's 220 Ω on transmission-line
grounds: 2 m of Cat5 is a 100 Ω line with a ~20 ns round trip against
2–5 ns edges, and at 220 Ω the far end sits at **1.83–1.86 V against a
2.0 V `V_IH`**, dwelling in the forbidden band for ~20 ns per clock edge,
into a part with no hysteresis.

They disagree on the value, and **A4 wins on a number B5 did not check**:
68 Ω is electrically ideal but draws **48 mA of fault current against a
40 mA pad spec**. 100 Ω gives a 2.75 V first step and 33 mA.

## Deleted parts are still load-bearing

**D2**, **A5**, **A7**, **B1**, **B2** and **C3** all hit this
independently. The watchdog and presence comparator are deleted in the
ADRs, the BOM and three prose sections — and still drawn, still allocated
rails, still counted in `C-DECOUPLE` qty 21, and still **depended upon**:
`mod-channels.md` justifies its whole topology on "a watchdog `CLR` parks
all four jacks at 0 V", `firmware/README.md` says "when the module watchdog
asserts `CLR`", and `bom.csv` claims the panel LED explains a latch that
nothing now indicates.

## The breath jack never rests at 0 V

**C2** and **C3** derive this separately, and **A5** and **B2** reach it by
a third route (the offset legs sum *after* the gain stage). ADR 0005 and
ADR 0006 both assert 0 V. The real value depends on the offset knob and
spans roughly **−5.9 V to +4.1 V**, with **+5.06 V at full CCW with no
instrument attached** — a patched VCA wide open at rack power-on.

## Documents defend the easy case

Not a defect but a pattern worth naming, found by **A2**, **C1**, **C2**
and **C4** independently: a claim is supported with the frequency, load or
operating point where it is comfortably true, and the case that actually
bites is not computed. Examples: the anti-alias filter defended at 330 kHz
rather than at 3.84 kHz where the aliasing is; the `SH/LD` glitch margin
argued capacitively (31× safe) when the inductive path is the one that
loads; the ADC reference costed at DC when the disturbance is a step; the
LC damping margin evaluated at typical play rather than at the clamp-legal
worst (220× becomes 56×).


## The arithmetic is sound; the bookkeeping is not

**D1** recomputed 312 numeric claims in Python from the values `bom.csv`
actually specifies. **~232 correct, ~54–61 wrong, 26 resting on inputs it
could not verify.** Its own headline is worth quoting as a result in its
own right: *"the arithmetic in this project is unusually good. Almost every
derivation that is shown is right."*

Nearly every defect is **one failure mode**: a value changed and the
numbers derived from it did not follow. They cluster on four quantities —
the breath in-amp's full-scale output, the pitch compensation capacitor,
the DAC channel count in the loop budget, and the marker-bit allocation —
**each wrong in two or three documents at once**. That is the same
staleness pattern `D2` found in prose, showing up in numbers.

Sharpest instance: the breath in-amp's full scale is stated as **−9.6 V**,
**−9.94 V**, **−10.05 V** and a "9.94 V span" across three files. Correct
is −9.94 V, and D1 notes the −9.6 V figure *"is reproducible from
nothing"*.

## A1 and D1 agree against this session's own figures

Both independently compute the key network as **119.9 µs release / 5.92 µs
press**, against the **125 µs / 5.7 µs** written into `cluster-boards.md`
and ADR 0001 today. Two agents, one from the cluster-board review and one
from a mechanical arithmetic sweep, landing on the same pair. The repo's
figures are mine and should be corrected to theirs.

D1 also confirms the part-family check passed: the crossing times use
0.7/0.3 × VCC, which is right for the 74HC part actually specified rather
than the LVC thresholds ADR 0001 retired.

## D1 and A4 do not actually conflict on the loop budget

They look contradictory and are not, and the distinction matters.

- **D1** audits the arithmetic *as written* and finds one error — the key
  chain is booked at 16 µs (32 bits at 2 MHz) where ADR 0001 and
  `carrier.md` fix the chain at 1 MHz, so **32 µs**. Corrected, the pass is
  148–155 µs of 250 µs and **4 kHz closes**.
- **A4** says the *model* omits a term: ESP-IDF's own documented
  per-transaction overhead on the ESP32-S3 (24 µs interrupt, 9 µs polling),
  which no document counts. Including it, the pass is **291 µs with driver
  defaults** — it does not close — or **196–241 µs** with polling
  transactions on an acquired bus.

So: **the repo's loop budget is arithmetically correct and structurally
incomplete.** Both agents are right about what they measured. The number
to design against is A4's, and the firmware technique it names is not
optional — it is what makes 4 kHz reachable at all.


## Drop the bus +5 V — three agents, three unrelated reasons

| Agent | Reason |
|---|---|
| **B1** | The 16-pin header's reversal hazard exists *because* of pins 11–16. Module ground lands on bus +5 V and +12 V; the rail diodes are not in the ground path, so keying is the only protection. A 10-pin header maps ground to ground and the diodes work |
| **B3** | **0 of 8** published designs that need a sub-12 V rail take it from the bus — 78L05 ×4, LM1117 ×2, AMS1117, R-78E5.0 ×2, ADP150, all local from +12 V. The rail is optional in the standard and absent from many cases |
| **A7** | It is the only rail in this design with **no reverse protection**, and `bom.csv` already documents that a reversed ribbon on it reaches the DAC's `SYNC` pin. `C-BULK-RAIL` on that branch is a through-hole electrolytic that **vents** when reverse-biased at 12 V |

The rail exists for one 74AHCT125. Deriving it locally is one TO-92 and two
capacitors, and it deletes the reversal hazard, the unprotected branch and
the venting capacitor at the same time.

## The instrument's power draw bends the synth's pitch

Two agents, two different segments of the same return path, neither aware
of the other — and the effect is **larger than the entire pitch budget**.

- **A7**: the 367 mA umbilical current *swing* returns through the power
  ribbon's six ground conductors, ≈17 mΩ → **6.2 mV of module ground shift
  = 7.4 cents**, breath-correlated. On a flying bus, 24 cents.
- **B3**: 360 mA through ~20–40 mΩ of differential busboard ground puts
  **7–15 mV between this module's 0 V and a neighbour's = 8–18 cents of
  breath-correlated pitch bend at the receiving module.**

`pitch-stage.md` puts the *whole* pitch error budget at 0.42 cents, and A6
independently bounds the module at ~1.2 cents over 0–40 °C. So the
carefully-engineered part of the pitch path is one to two orders below an
effect that is documented nowhere — and because it tracks breath, it will
sound like an intentional feature that has gone wrong.

`power-entry.md` explicitly dismisses this path ("needing no ground path at
all") in the same sentence that introduces the diode argument.

## Where the design genuinely beats published practice

Recorded so it is not re-litigated by a later reviewer.

- **The current-limited, ramped, fault-timed load switch on the exported
  +12 V.** B3 read 14 published power-entry schematics: hot-swap
  controllers at the rack entry are **0 of 14**, and a GitHub-wide search
  for `LT1641 eurorack` returns 16 hits, *all of them this repository*.
  But the **function is precedented for an exported rail** — Westlicht
  PER|FORMER uses an STMPS2151 current-limited load switch with `EN` and
  `FAULT` on the 5 V it sends to its USB host port, structurally the same
  design one rail down. Exporting 12 V rather than 5 V is what pushed this
  off the shelf of SOT-23 USB switches. **Justified, not over-engineered**,
  and B3's verdict is that the field convention would be actively dangerous
  here.
- **The ferrite bead current rating is specified**, which none of the 14
  do. **The SOA-based FET sizing has no equivalent in the set.** The
  instrument-end shunt-diode-plus-limiter is exactly Mutable's scheme with
  the load switch as the fuse.
- **Pitch accuracy** (A6, B2): best in the published field, ~7× inside the
  VCO's own drift.
- **Breath latency** (B6): ~2× better than the best published wind
  controller figure.
- **The analog breath path itself** (B5, B6): a dedicated sense return
  carrying no power current, received by a true in-amp, beats both direct
  wind-instrument precedents — Yamaha BC and Akai EWI both share the return
  with supply current.

## Jack-tapped feedback is published practice — question closed

The repo defends its jack-tapped DC feedback as an unusual choice. **B4
found three published designs doing it**, by opening and rendering their
schematics: **Ornament & Crime rev2e** uses the identical split loop (100 k
DC feedback from after the 220 Ω, 22 pF from the op-amp output);
**Westlicht PER|FORMER** takes both its 100 k and its 18 pF from after the
220 Ω; and **Winterbloom Sol** takes its 9.10 k from after a 1 kΩ with *no
compensation capacitor at all* — the closest relative of Woody's pitch
stage, and less defended than it.

Also confirmed from primary source: 1 kΩ is the field convention (7 of 12,
the only value that repeats), and Mutable really does uprate the output
resistor and nothing else — `≤1 %, ≥200 mW` 0603 on the output 1 kΩ while
every other resistor on the board is 0402/100 mW, counts matching jack
counts exactly, verified in four BOM spreadsheets.

Corrected: `bom.csv` says "no surveyed design clamps a CV output to the
RAILS at all". Erica clamps gate/clock outputs with BAT85, HAGIWO with a
BAT43 pair behind 470 Ω — both to a rail.

## `R-OUT-PROT` is under-rated — two agents, two ladders

| Agent | Worst case | Against the claim |
|---|---|---|
| **A6** | **322 mW** — output-to-output against a 220 Ω source at ±10 V | `bom.csv` states 192 mW; ≥500 mW survives at **1.55×**, not 2.6× |
| **B4** | **269 / 312 / 464 mW** | Thick-film derating at a 50 °C rack interior leaves a 500 mW 1206 delivering ~350–420 mW → **~1.1×** |

**The only part in the module at real risk from any jack fault**, and only
because it is under-rated. B4 answers the BOM's open question: a 0.66–1 W
1206 exists (ERJ-P08 class).

## Passive-multing PITCH never settles

**A6** computed the ring (41.9 % overshoot, 1.84 kHz into BREATH's 330 nF).
**B4** carried it one step further: the DAC updates every **250 µs** and
the decay is 184–680 µs, so **the ring never settles.** Not the per-note
transient `pitch-stage.md` describes — continuous audio-band junk on the
pitch line for as long as the stackcable is in.

## The umbilical: FOUR agents, and two of them propose the identical swap

**A4** and **A8**, independently, reached the same pin map: `SCLK`+`MOSI`
on one pair, **`CS` paired with `DIG_GND`**. A8 quantifies what the current
map costs — intra-pair backward crosstalk, saturated because
2·T_d = 20 ns ≫ t_r = 2 ns, giving **365–907 mV at the module against
`CS`'s 678 mV `V_IL` margin** — and notes ADR 0004 asserts *twice* that
"each signal sits against a ground in its own twisted pair" while its own
pin table contradicts it. The swap improves `CS` margin from **1.9:1 to
6200:1** and trades a *sticky* failure (a re-framed DAC word writes the
software-reset and reference-enable bits, with no `MISO` to read back) for
one the repo says self-heals in 250 µs.

**A8 also noticed what ADR 0004 spent its reasoning on**: the 13 mm
untwisted plug region, which costs **15 mV** — 25–60× smaller than the
effect it missed.

### …but B5 and A4/A8 genuinely conflict, and this needs a decision

**B5** wants `MOSI`/`CS` *off* pins 4/5 entirely, because published
RJ45-for-other-purposes standards leave those two empty so a misplug into
PoE or a telephone line destroys nothing. **A4/A8's fix puts `SCLK`/`MOSI`
there.**

There are exactly 8 conductors and exactly 8 things to carry, so **pins 4/5
cannot be left empty without deleting a signal.** This is a real design
tension the wave surfaced and did not resolve, and it is the one item here
that is a decision rather than a fix.

## `DIG_GND` is named in three documents and drawn in none

**A8**, showstopper. At the instrument end it appears on no drawing:
`carrier.md` §4 returns `U-TVS-SPI` to `PWR_GND` while §3 returns
`U-TVS-CHAIN` to `DIG_GND`, a net on no schematic. The two possible
answers give **opposite failure modes**. ADR 0004 and the ROADMAP's E12
gate both contradict `power-entry.md`, which A8 judges right on the
engineering.

## Breath-correlated pitch bend: now THREE routes

| Agent | Segment of the return path | Effect |
|---|---|---|
| **A7** | The power ribbon's six ground conductors, ≈17 mΩ | 6.2 mV → **7.4 cents** (24 on a flying bus) |
| **B3** | ~20–40 mΩ of differential busboard ground to a neighbour | 7–15 mV → **8–18 cents** |
| **A8** | The cable shield, if the etherCON shell bonds to the 8HP panel: 12–60 % of return current goes home via rack chassis | **~7 cents** |

Three agents, three segments, one shape. Against a stated pitch budget of
0.42 cents and a module bounded at ~1.2 cents over 0–40 °C. **The
engineered part of the pitch path is one to two orders below an effect
documented nowhere**, and because it tracks breath it will sound like an
intentional feature gone wrong.

## The structural finding

A8's, and it is the reason that review was scoped at all:

> **Eleven of eighteen unretrofittable items are wrong or unspecified, and
> every one is a connector, a keying choice, a conductor gauge or a
> ground.** `WIRE-LOOM` is one qty-1 row covering four physically different
> harnesses; `J-DISP` and `J-LED-L/-R` have no BOM rows at all; the
> internal etherCON-to-carrier tail loom is in no document and no count.
> **Every page describes its own end of every cable and no page owns the
> cable.**

Also: `CABLE-UMB`'s 0.168 Ω/2 m is the **solid-core** figure for a cable
the BOM insists must be **stranded**; TIA's patch-cord limit gives
**0.28 Ω**. Everything derived from it is 1.2–1.67× optimistic. A8
rechecked each — no conclusion flips.

## What A8 confirms is right

- **The analog pair survives by ~80 dB.** `SCLK` → `BREATH` is 57 nV at the
  jack (0.00007 cents); LED PWM through the shared return is 5.7 µV; the
  LED DC step 25 µV. **Zero breath counts** — and the ADC reads before the
  cable anyway. The three choices that earn this (482 Hz filter at the
  module ahead of the in-amp, `AGND` carrying no power current, `C_diff`
  10× `C_cm`) should be protected in any rework.
- **Single-ended-with-sense-return is right, for a reason the repo states
  only in fragments: it is the system's only fail-silent path.** Digitising
  at the instrument is *negative* cost (~16 parts, ~$20, and frees the
  conductor the pin-map fix needs) but converts "cable pulled mid-note =
  silent" into "loud drone forever".
- **The alternating-ground ribbon is validated**: 87 mV coupled against a
  990 mV threshold, 11:1 — versus ADR 0001's own 1.36 V for an ungrounded
  conductor, which is a failure.
- **`C-STRIP-BULK` on the carrier is correct** (0.070 Ω of loom against the
  cap's 0.37 Ω at 2 kHz). Recorded so nobody repeats the check.
- **Input-LC stability closes with the cable in** — the cable's 0.60 Ω is
  added damping, Middlebrook margin 42 dB.

## A8 corrects two things other agents got right for the wrong reason

- **ADR 0014's "0.4 % gain compression"** from the LED→`AGND` loop omits
  the in-amp's CMRR and is **~200× pessimistic** (25 µV, not 40 mV). The
  fix adopted is still right — for the *other* loop.
- **A `SH/LD` glitch is not what ADR 0001, `carrier.md` §3 and `WIRE-LOOM`
  say it is.** It produces a splice of two snapshots ≤32 µs apart, almost
  always benign — **and the marker pattern cannot see it**, while it *does*
  catch an `SCK` glitch. This refines C1, which found the same reload
  passes 11 of 31 times. Decision still right, justification wrong.
