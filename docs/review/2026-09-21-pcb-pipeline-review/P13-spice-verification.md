# P13 — SPICE verification of the analog design

**Slice:** stage 2 of `docs/reference/pcb-pipeline.md`. Cold review: no prior
review directory was read.

**Method.** Everything marked `[test]` was run on this machine and the command
output is reproduced or quoted. `[calc]` shows the arithmetic. `[repo]` gives
file:line. `[source]` gives repo + path. `[from memory]` means I could not
check it.

**Summary of the verdict.** The stage is the right idea and the wrong list.
Two of its six items cannot answer the question asked of them, one has had its
question answered without it since the plan was written, and the single
highest-cost claim in the whole analog design — the breath link's CMRR — is not
on the list at all. Separately, the plan's tooling claim is half wrong in a way
that matters: **PySpice 1.5 does not work against ngspice 42 out of the box, and
SKiDL does not use PySpice.**

I ran real simulations against the real design. Six of the corpus's own
numbers were checked; four are confirmed, two are not.

---

## 0. What I actually got running, first, because everything below rests on it

```
$ apt-get install -y ngspice libngspice0 libngspice0-dev
  ngspice        42+ds-3build1   amd64
  libngspice0    42+ds-3build1   amd64
$ ngspice --version
  ** ngspice-42 : Circuit level simulation program
```
`[test]` Stock noble archive, no allowlist change. The plan is right about this.

TI's `OPAx197.LIB` downloads (`HTTP 200`, 16,625 B) `[test]`, and **it runs in
ngspice 42 only with `set ngbehavior=psa`**. Without it:

```
Netlist line no. 0: Undefined parameter [temp]
Netlist line no. 0: Cannot compute substitute
ERROR: fatal error in ngspice, exit(1)
```
`[test]` `set ngbehavior=ps` inside a `.control` block is **too late** — the
netlist is already parsed. It has to be in `.spiceinit` for the `ngspice -b`
CLI path, or issued via `exec_command()` before the analysis under PySpice.
Both were verified working `[test]`. This is one line in `setup.sh` and it is
the difference between "the model is available" and "the model is usable";
the plan does not mention it.

With that, an OPA2197 unity-gain follower on ±12 V solves at
`v(out) = 2.500022 V` from a 2.500 V input `[test]` — a 22 µV offset, which is
the model doing its job.

---

## 1. Verdict on each proposed simulation

### 1.1 Pitch loop gain / phase margin into 0, 200 pF, 800 pF, 10 nF and a dead short

**Verdict: worth running, but it is not the highest-risk item on that page, and
one of its five cases cannot be run as an AC sweep at all.**

I built the pitch stage as drawn (`R-OPAMP-IN` 1 k, `C-AA-PITCH` 10 nF, LT5400
1:1 at 10 k, `TRIM-GAIN` 200 Ω, `C-FB-PITCH` 2.2 nF from the op-amp **output**
to the (−) input, `R-OUT-PROT` 1 k, `C-FILT-PITCH` 10 nF at the jack) and swept
loop gain by voltage injection at the op-amp's (−) **pin** — valid here because
the OPA2197 is FET-input, so removing it from the summing node loads nothing.

| Load at the jack (on top of `C-FILT-PITCH`) | Crossover | Phase margin |
|---|---|---|
| open | 9.98 MHz | **69.3°** |
| 200 pF | 9.98 MHz | **69.3°** |
| 800 pF | 9.98 MHz | **69.3°** |
| 10 nF | 9.98 MHz | **69.3°** |
| 100 nF | 9.99 MHz | **69.3°** |

`[test]` Identical to three significant figures at every load.

So `pitch-stage.md`'s claim stands, and stands for the reason the page gives:
`C-FB-PITCH` ties the (−) input to the op-amp *output*, so β(∞) = 1 and the
jack is outside the loop above the handover `[repo] hardware/module/pitch-stage.md`
("The feedback network is a **lead** at every passive load tried… Cable
capacitance is structurally incapable of putting lag in this loop"). The
crossover landing on the part's GBW is the same fact seen from the other side.

**But that makes the simulation confirmatory, not discriminating.** It will be
green whatever the cable does, because the topology makes it green. The page
calls this "the highest-risk item on the page"; after running it, that sentence
should be withdrawn. The risk on that page is somewhere else — see 2.2.

**The "dead short" case is not an AC question.** With the jack shorted
(0.1 Ω), the DC operating point rails:

```
RSHORT = 0.1
v(jack) = 1.163952e-03
v(out)  = 1.151697e+01
```
`[test]` — and the loop gain then has **no 0 dB crossover anywhere from 1 Hz to
100 MHz** `[test]`. DC feedback through `R2` is exactly zero, so there is no
loop to have a margin. An AC sweep linearised about a saturated operating point
is not an answer, it is a plausible-looking plot. The page's own text says this
("With the jack shorted, DC feedback is exactly zero and the amp rails")
`[repo] hardware/module/pitch-stage.md`; the plan then lists it as an AC case
anyway. **Replace that row with a transient** (insert the plug, recover).

Incidentally the short is survivable: 11.517 V across `R-OUT-PROT` 1 kΩ is
11.5 mA and `11.517² / 1000 = 132.6 mW` `[calc]`, inside the 1206 ≥250 mW
`bom.csv` specifies.

### 1.2 `R-ISO-REF` reference buffer into 100 nF, with and without the resistor

**Verdict: the most valuable item on the list. Run it. And it returns a result
the corpus has not absorbed: the circuit as drawn is not a fix.**

Voltage injection at the op-amp input pin, 100 nF at the sensor's `VS` node:

| Configuration | Crossover | Phase margin |
|---|---|---|
| No `R-ISO-REF` (buffer straight into 100 nF) | 215 kHz | **8.8°** |
| `R-ISO-REF` = 10 Ω, feedback tapped at `VS` — **as drawn** | 212 kHz | **8.4°** |
| `R-ISO-REF` = 10 Ω, feedback tapped at the op-amp output | 320 kHz | 75.2° |

`[test]` DC loop gain 134.8 dB in every case, which is the OPA2197's `A_OL`.

Three things follow.

**The problem is real.** 8.8° of margin is a circuit that rings violently and
is one tolerance away from oscillating. `carrier.md` is right to have flagged
it.

**The numbers in `carrier.md` are not.** It states "**2.6°** of phase margin
and oscillation near **458 kHz**" `[repo] hardware/controller/carrier.md`.
Those follow exactly from the back-solved `Ro = 75.8 Ω`:
`fc = √(GBW · f_pole) = √(10 MHz × 21 kHz) = 458 kHz` and
`PM = 90° − arctan(458/21) = 2.6°` `[calc]`. The arithmetic is right and the
input was wrong. With a real `Ro`, `f_pole = 1/(2π × 375 × 100 nF) = 4.24 kHz`
and `fc = √(10 MHz × 4.24 kHz) = 206 kHz` `[calc]` — which is the 215 kHz the
macromodel returns. The corpus has since caught this itself
(`config/figures.yaml`, `opa2197-output-impedance`, 375 Ω, SBOS737C now banked),
and the two figures now agree by two routes.

**The drawn fix does not work, and this is the finding.** Putting
`R-ISO-REF` inside the loop with feedback at `VS` moves the margin from 8.8° to
8.4° — *worse*, not better. `carrier.md` says as much in prose ("puts the R·C
pole back inside the loop — 159 kHz, 7.2° of margin, still unstable"), but the
schematic on that page still **draws** the in-loop tap, and the plan's line
"Verify the problem *and* the fix" implies there is a drawn fix to verify.
There is not. Node `VS` / ref `R-ISO-REF`: the page's compensation is an
unadopted proposal in a block quote, and the drawing is the unstable version.

### 1.3 AC sweep of the OPA2197 macromodel's `Zo`

**Verdict: the question it was commissioned to answer has since been answered
without it. Keep it, but reframe it as model validation — which is worth more.**

First, the direct question asked of this slice: *can an AC sweep of a
Green–Williams–Lis macromodel actually give a meaningful `Ro`, or is that a
misunderstanding?*

**It can. It is not a misunderstanding.** The GWL architecture models open-loop
output impedance versus frequency as an explicit, separately-fitted block. It
is item (g) in the model file's own list of what it models — *"OPEN-LOOP OUTPUT
IMPEDANCE VS. FREQUENCY (Zo)"* — and the block is a named subcircuit,
`ZO_SRC_OPAx197`, instantiated at `X_U32` `[source] chevalierid/alan-setup,
fab/kicad/libraries/pspicetilib/OPAx197.LIB`. I measured it, by breaking the
loop with a 1 TH inductor (DC short, AC open) and injecting 1 A:

| Frequency | Measured `|Zo|` | `figures.yaml` / SBOS737C Fig. 26 |
|---|---|---|
| 1 kHz | **359 Ω** | 375 Ω plateau (100 Hz – 300 kHz) |
| 10 kHz | **359 Ω** | 375 Ω |
| 100 kHz | **358 Ω** | 375 Ω |
| 1 MHz | **300 Ω** | 301 Ω |

`[test]` vs `[repo] config/figures.yaml`, `opa2197-output-impedance`.

Agreement within 4 % at the plateau and 0.3 % at 1 MHz. That is a real
measurement of a real modelled quantity.

**The misunderstanding to avoid is a different one: expecting a scalar.** `Zo`
is frequency-shaped by construction, which is why the corpus's own note that
"arithmetic on the netlist does not [answer it]" is correct. And it is why
75.8 Ω was not a wild guess — it is approximately the part's **10 MHz** value
(`figures.yaml` records Fig. 26 at ~73 Ω there). It was the right kind of number
read at the wrong frequency.

**What has changed since the plan was written** is that the plan's stated
payoff — *"This retires a blocked item without the datasheet"* — no longer
exists. `datasheets/texas-instruments/OPA2197.pdf` is banked and
`opa2197-output-impedance` is `settled` at 375 Ω `[repo] config/figures.yaml`.
Per CLAUDE.md §3, "a number read off a banked document beats one from a
review" — and it beats one from a macromodel too. Run the sweep anyway, once,
as the thing that licenses trusting this macromodel for the twenty other
questions in section 2. Do not run it as the source of `Ro`.

### 1.4 DC transfer-function sweeps of every stage

**Verdict: worth running, cheapest item on the list, and "every stage" is the
wrong unit.**

They work. I built the breath receiver as drawn — `R1` 1 k and `R1b` 1 k
instrument-side, `R2`/`R3` 10 k module-side, the 1 MΩ bias pair, `R_G` 42.2 k,
`REF` at +0.437 V — around the real INA828 macromodel:

```
at rest (V_diff = 0):   v(out) = 4.370796e-01    (= V_REF exactly)
at V_diff = 1 V:        v(out) = 2.598157e+00
```
`[test]` → differential gain `(2.598157 − 0.437080) / 1 = 2.1611` `[calc]`,
against `breath-receive-stage.md`'s derived "effective **2.1611**"
`[repo] hardware/module/breath-receive-stage.md` and `figures.yaml`'s
`inamp-full-scale` derivation (`2.16106`). **Five significant figures, first
try.** These sweeps are worth having.

**But the defect this project actually produces is between stages, not inside
them.** CLAUDE.md names it: "a value changes, and the documents derived from it
do not follow." A per-stage DC sweep re-derives each stage against itself. It
cannot catch a sign that flips when a stage is inserted — and the corpus is
*asking for exactly that check* and the plan does not list it. See 2.4.

### 1.5 Monte Carlo over resistor tolerance and reference drift on the pitch chain

**Verdict: cannot answer the question asked of it. It moves the argument, and
it moves it somewhere worse.**

The plan's justification is that `pitch-cents-budget` is disputed and "a
distribution settles it." Read why it is disputed:

> `decided_by`: "pitch-stage.md has two contradictory budget tables back to
> back and states no total. One coherent table, then cite it."
> `[repo] config/figures.yaml:180`

The dispute is **not** over the spread of known terms. It is over *what the
terms are*. `pitch-stage.md` really does carry two tables in sequence that
disagree with each other about the same quantities — LT5400 tracking at
0.027 cents in one and ~0.1 cents in the other, the DAC reference at 0.42 and
~0.5 `[repo] hardware/module/pitch-stage.md`. A Monte Carlo needs that list and
those distributions as **inputs**. Whichever table the author transcribes is
what comes out, wearing a histogram.

Three further reasons it cannot settle this:

1. **The two largest terms have no SPICE model.** The DAC internal reference
   drift and DAC INL (±4 LSB) belong to the DAC8568, for which no model exists
   (section 4). They would enter the run as hand-typed distributions — i.e. the
   disputed numbers, laundered through a simulator and returned looking settled.
   That is precisely the failure CLAUDE.md is built to prevent, with a new coat
   of paint on it.
2. **The largest live term is not in the budget at all.** `power-entry.md` puts
   the ground-path, breath-correlated terms at **7.4 cents** (power ribbon),
   **8–18 cents** (busboard to a neighbour) and ~7 cents (shield bonding), and
   says so explicitly: "The carefully engineered part of the pitch path is one
   to two orders of magnitude below an effect that appears in no document"
   `[repo] hardware/module/power-entry.md`. Monte Carlo over the sub-cent terms
   is an expensive way to refine the wrong digit.
3. **It is not blocked on a tool.** It is blocked on someone writing one
   coherent table. Doing the run first inverts the order.

**What Monte Carlo *is* good for here**, once the table exists: the **resistor
network alone** — `R1`/`R2` ratio error, `TRIM-GAIN`'s 200 Ω tempco, and above
all the mod channels' 10 k/30 k discrete pair, where `mod-channels.md` states
"±50.5 mV" zero and "19.703–20.303 V" span from a four-corner enumeration
`[repo] hardware/module/mod-channels.md`. That has real inputs (1 % parts,
stated), a real question (are four corners enough when reel-adjacent parts
track?), and a real consequence (±18 cents/octave if a mod channel is used for
pitch). Move the Monte Carlo there.

### 1.6 The breath response shaper's diode knee

**Verdict: worth running — the one item where a sweep genuinely replaces a
spreadsheet. But as listed it under-asks by three questions.**

The shaper's gain table is explicitly `[calc]`
`[repo] hardware/module/breath-output-stage.md:236` on a nonlinear element, and
the page records that a ÷10 scaling "would have put the knee above a hard blow"
— a mistake a DC sweep catches in one plot. Right instinct.

Three things it should also ask, none of which are on the list:

- **Does the centre null survive tolerance?** The page's strongest claim is that
  the wiper sits at 0 V at `p = 0.5` "for every input voltage… mathematically
  linear in the middle, not approximately linear." That rests on the two 10 kΩ
  divider resistors making exactly `V_in/2` against a stage output of exactly
  `−V_in/2` — i.e. on `R1` 20 k / `R2` 10 k being exactly 2:1. At 1 % that null
  is not exact, and the residual is a diode current at centre detent. Sweep the
  pot, not just the input.
- **`.temp`.** The 1N4148's knee moves about −2 mV/°C `[from memory]`, so the
  ~0.6 V breakpoint that "is the entire design" drifts with the module's
  internal temperature. A three-point temperature sweep costs nothing and the
  design is built around that one voltage.
- **Where it inserts.** The page says the stage adds "**both remaining OPA2197
  halves**" into the breath chain and that "the existing chain's polarity was
  never re-derived with a stage inserted." That is section 2.4, and it is the
  more expensive question.

---

## 2. The missing simulations, ranked by what the claim costs if it is wrong

This is the main deliverable. Ranked by consequence, not by effort.

### 2.1 Breath-link CMRR — the in-amp front end with real component mismatch

**Node: `BREATH` / `AGND` pair, J-UMB pins 1–2. Refs: `R1`, `R1b`
(`R-SER-BREATH-INST`), `R2`, `R3`, `C_cm` ×2, `C_diff`, `R4`, `R5`, `U-INAMP`.**

**Nothing in the plan touches the INA828 or CMRR.** This is the single largest
omission.

Every load-bearing number in the 2 m analog architecture is a `[calc]` CMRR
figure, and they are all unretrofittable:

| Claim | Where | Provenance |
|---|---|---|
| `R1` without `R1b` costs the **entire** 60 dB budget: `\|1M/1.011M − 1M/1.010M\| = 9.79e-4 → 60.2 dB` | `breath-receive-stage.md` | `[calc]` |
| With `R1b`, the floor is **73 dB**, set by the 1 MΩ pair — so `R1b` buys ~13 dB, not the "fifty times" the receive page claims | `carrier.md` | `[calc, A2]` |
| Requirement is **58.5 dB** → **1.7 dB of margin**, "resting on two parts' tolerance, inside a body that cannot be reopened" | `carrier.md` | `[calc, A2]` |
| `C_cm` at ±5 % gives **~46 dB**; ±1 % is needed to clear 60 | `breath-receive-stage.md` | `[calc]` |
| A single-ended cap on one leg caps CMRR at **~15 dB at 100 Hz** | `breath-receive-stage.md` | `[calc]` |

`[repo] hardware/module/breath-receive-stage.md`, `hardware/controller/carrier.md`.

Every one of these is a resistive/capacitive divider balance against a real
in-amp, at a real frequency, and **an AC sweep with the INA828 macromodel
settles all of them in one run** — including the frequency dependence that the
hand calculations do not have at all. The hand numbers are DC balance ratios;
CMRR at 50/60 Hz, at the WS2815's ~2 kHz PWM rate, and at the 2 MHz SPI rate
are three different numbers and only the first is approximated by that
arithmetic.

The model exists and runs — I used it in 1.4. It is not in the plan's model
list, which says only "`DAC8568`, `MPXV4006` and the reference are behavioural."

**Cost if wrong:** the instrument-side parts are inside a bonded body that
cannot be reopened (`breath-receive-stage.md`, `carrier.md`). A CMRR figure that
is 13 dB optimistic is a breath channel with mains hum and LED-correlated
rubbish on it, permanently, on the instrument's primary expressive output. The
claimed margin is 1.7 dB. **Rank 1, and by a wide margin.**

Run it as: AC CMRR sweep 10 Hz – 1 MHz, with (a) `R1b` fitted and omitted,
(b) `C_cm` at ±1 % and ±5 % mismatch, (c) `R2`/`R3` at 0.1 % worst case. That is
a small Monte Carlo with *real* inputs — which is where the Monte Carlo budget
from 1.5 should go.

### 2.2 Pitch transient into a passive mult — the claim the listed AC sweep is blind to

**Node: `PITCH` jack. Refs: `R-OUT-PROT`, `C-FILT-PITCH`, `C-FB-PITCH`, `R2`.**

`pitch-stage.md` states, under "Two new bounds to check at E9":

> **It does not oscillate; it rings.** `Q = √(R_eff·C_load / R2·C_fb)`. Safe to
> about 10 nF, but joining PITCH to the MOD (82 nF) or BREATH (330 nF) jacks
> through a passive mult gives **44–67 % overshoot** — several semitones of
> transient on every note. That failure mode did not exist with op-amp-side
> feedback. `[repo] hardware/module/pitch-stage.md`

I ran it. Step the DAC so the jack moves 1.010 V, measure the peak:

| Total C at the jack | Peak | Overshoot |
|---|---|---|
| 10 nF (`C-FILT-PITCH` alone) | 3.6264 V | **11.5 %** |
| 92 nF (+ one MOD jack) | 3.9325 V | **41.8 %** |
| 340 nF (+ BREATH jack) | 4.1579 V | **65.4 %** |

`[test]`, overshoot `= (V_peak − V_final)/step` `[calc]`. Against the page's
hand-derived "44–67 %" that is a confirmation, and a good one.

**The point is what the plan's own item 1.1 says about the same circuit at the
same loads: phase margin 69.3°, unchanged, at every one of them** `[test]`.

That is the finding. **The listed simulation returns a clean pass on a circuit
that overshoots 65 % and puts several semitones of pitch transient on every
note.** It is not that the AC sweep is wrong — the loop genuinely is stable,
because `C-FB-PITCH` makes β(∞) = 1 and the crossover sits at the part's GBW,
ten decades above where the ringing lives. The ringing is a *closed-loop
response* phenomenon between the ~1.9 kHz pole of `R-OUT-PROT` into the mult
capacitance and the ~12 kHz handover where the loop stops watching the jack.
Loop gain cannot see it.

**Cost if wrong:** an audible, musical defect on every note, on the output the
whole instrument exists to produce, discovered at E9 on a board already
fabricated. **Rank 2.** One transient, five loads, ten minutes.

Add to the same run: the plug-insertion transient (jack shorted then released),
since `pitch-stage.md` says "every patch-in is a brief rail excursion recovering
through the loop" and nothing has measured the recovery time or the
`D-JACK-CLAMP` current during it.

### 2.3 A behavioural LT1641 — the circuit that has already been proven not to start

**Node: `UMBILICAL +12V`. Refs: `U-LOADSW`, `R-ILIM`, `C-TIMER`, `C-GATE`,
`R-FB-HI`, `R-FB-LO`, the N-FET.**

The plan writes this off: "**`LT1641` has no model anywhere** … so the load
switch is not simulable and stays a bench question."

**That does not follow from the plan's own premises.** Two lines earlier it says
`DAC8568`, `MPXV4006` and the reference "are behavioural sources and need no
vendor model." The LT1641 is now in exactly that position, because
`power-entry.md` has written its behaviour down as equations:

> Sense threshold **47 mV**, and only when `V_FB` ≥ 0.5 V. Foldback law:
> **12 mV at `V_FB` = 0, linear to 47 mV at `V_FB` = 0.5 V, flat above** —
> linear in `V_FB`, **not** in `V_OUT`. `I_TIMER` 3 µA down / net ~77 µA
> ramping. Fault at `TIMER` = 1.233 V. `I_GATE` 10 µA.
> `[repo] hardware/module/power-entry.md`

That is a behavioural model. A current-limit amplifier whose threshold is a
piecewise-linear function of one pin, a timer integrator, a latch and a gate
charge pump — every one of those is an ngspice `B` source and a couple of
switches, and it is less work than the INA828 sim above.

Why it matters more than anything else in the power section: **this circuit has
been shown not to start, three times, by three independent routes, and the fix
has never been exercised.** `power-entry.md` records that `FB` was connected to
nothing, that the part therefore held its foldback floor at 240 mA forever, that
the `-1` suffix latches, and that "no value of `C-TIMER` fixes it." The
correction — a divider to `FB` crossing 0.5 V early in the ramp — is a
*sequencing* claim about a race between three time constants (the ramp, the
timer, and the far-end load coming up), and the page's own integration gives
51.5 ms bare / ~62 ms loaded against a 150 ms timer target, with the sizing case
being a **hot-plug** where "the FET is fully enhanced before the plug is even
inserted, so the ramp cannot help."

Nothing in the plan tests that race. A transient with the 2.2 mF far-end
capacitance, the ~360 mA load, and the hot-plug case does, and it would also
size `C-TIMER` and `C-GATE` against the actual start rather than against a
target.

**The honest caveat, and it is a big one:** every LT1641 parameter above is
`[web, search-index]` and `analog.com` is BLOCKED through four review waves
`[repo] datasheets/MANIFEST.csv`. **A green start simulation would confirm the
transcription, not the part.** That is worth saying out loud in the sim's own
output, because a plot showing a clean 62 ms ramp is exactly the kind of
artifact that gets cited later as if it settled something.

**Cost if wrong:** the instrument does not power up. It is a Eurorack module
with a load switch that latches off and a panel LED that (per the same page)
cannot indicate the latch. **Rank 3**, held below 1 and 2 only because the
model's inputs are unverified.

### 2.4 The breath chain end to end, with the §4 shaper inserted

**Chain: `U-BREATH` → in-amp → shaper (`POT-RESP`) → `POT-GAIN` attenuator →
buffer → summer → `R-OUT-PROT` → `BREATH` jack.**

The corpus asks for this in terms, and the plan does not list it:

> **The extra inversion.** This stage inverts twice, so polarity is restored —
> but the existing chain's polarity was **never re-derived with a stage
> inserted**. Check it end to end before layout, not after.
> `[repo] hardware/module/breath-output-stage.md`

The plan's answer to this is "DC sweeps of every stage's transfer function",
which is the one decomposition that cannot catch it. The whole point of the
finding is that each stage is individually correct.

The chain also carries several end-to-end claims nobody has checked together:

- Rest = 0.00 V, hard blow = −4.69 V at the in-amp, −9.94 V at sensor full
  scale — but `breath-working-point` is **disputed** in `figures.yaml`
  (2.8 kPa is "cited to ADR 0003, which does not contain it; the two schematic
  pages cite each other"). A sweep does not settle the kPa, but it makes the
  sensitivity to it explicit instead of implicit.
- "offset at +5 V and gain at 4× puts a hard blow at +23 V, and the OPA2197
  stops at about ±11.5 V… a *rail* clip with no soft region."
- The shaper's insertion point is justified by the signal there having "a
  **fixed** scale set by the in-amp" — an end-to-end sweep is what proves the
  scale is fixed.
- `POT-OFFSET`'s unbuffered wiper: the review finding quoted on that page says
  "zero at centre" actually sits ~20° past centre at **+0.605 V**. That is a
  two-axis DC sweep (wiper position × input), not a transfer function.

**Cost if wrong:** a breath CV that goes the wrong way, or clips, on a board
with three panel knobs built around it — and it is the kind of error that
survives a per-stage review by construction. **Rank 4.**

### 2.5 Power-on and reset of the analog path — the plan has no transient at all

**Nodes: `AVDD` (5.21 V), `+12V`/`−12V` analog, `VREFOUT`, `CLR`, `PITCH`,
`MOD 1–4`, `BREATH`.**

The plan lists six simulations and not one of them is a power-up. The corpus has
at least five power-on claims that a single transient would settle together:

- **Pitch at 0 V, not −2.5 V.** "`V_ref` is the DAC's internal reference, which
  is **disabled until firmware writes an enable** — so *both* terms are zero and
  the jack sits at **0 V**… After it, `CLR` parks at −2.500 V. ADR 0006's
  power-on table asserts 'below −2 V' for both; they are different states,
  2.5 V apart." `[repo] hardware/module/pitch-stage.md`
- **The (+) input has no DC path to ground.** "Its only connection is a DAC pin
  that may be high-Z before power-on reset, so the output can sit at **either
  rail** during that window." The fix, `R-BIAS-DAC`, is listed under *Still
  open* — i.e. the rail excursion is currently live.
- **Mod channels at 0 V on `CLR`**, which depends on the DAC's C grade
  (`4X − 3X = X`, zero only because the grade zero-scales). `mod-channels.md`
  notes a B/D part would put **+2.5 V on all four jacks**, and that firmware
  refreshing five of six channels pins them at **+11.45 V**.
- **The rails do not come up together.** `+12 V`/`−12 V` arrive through
  `D1`/`D3` and beads; `AVDD` comes up behind an LM317 from the same +12 V.
  The op-amps are live before the DAC is.
- **Breath rests where the sensor rests**, and the output stage's offset
  reference is the LM317 5.21 V rail — which is why `breath-receive-stage.md`
  rejected `VREFOUT` ("the jack would rest at ~0 V at every boot and then *step*
  to where the player parked it, by up to 2 V").

**Cost if wrong:** six CV outputs doing something unplanned into somebody's
modular at every rack power-up. A rail excursion on `PITCH` is a VCO jumping
seven octaves; on a MOD jack driving a filter it is worse. **Rank 5.** One
transient with piecewise-linear rail sources and a high-Z DAC pin covers all of
it.

### 2.6 Input LC damping — the `[from memory]` number carrying a stability conclusion

**Refs: `L-BUCK-IN`, `C-STRIP-BULK`, the umbilical, the far-end ~2 mF.**

`power-entry.md`, *Still open*:

> **Damping the input LC.** `L-BUCK-IN` (10–47 µH) in front of a
> constant-power switching load, with 2 m of cable and ~2 mF at the far end, is
> the textbook negative-resistance instability and **no damping leg is
> specified**. `[repo] hardware/module/power-entry.md`

And against it, `carrier.md:124`:

> **The input LC is stable** `[calc]` … ESR of a 100 µF / 25 V radial ≈ 0.5–1 Ω
> **[from memory]** → Q ≈ 0.5–0.9, no peaking

A stability conclusion resting on an ESR the author could not look up. This is
the plan's own stated reason for having a SPICE stage — "the corpus is full of
hand-derived transfer functions and stability arguments" — and it is the purest
example of one in the repo, and it is not on the list.

It is also genuinely simulable without any vendor model: a negative-resistance
behavioural load (`I = P/V`), the cable's L and R, the bulk capacitance, and a
parameter sweep over ESR. That converts "[from memory] ≈ 0.5–1 Ω" into "damped
for ESR above X, and here is the damping leg if the real part is below it."

**Cost if wrong:** an oscillating supply two metres from a precision analog
front end, on a rail that also feeds the WS2815 strip. **Rank 6.**

### 2.7 Mod-channel crosstalk through the shared reference buffer

**Node: `V_ref` 3.3333 V (DAC ch7 buffer output). Ref: the shared ½ OPA2197.**

`mod-channels.md` makes a DC argument for one buffer serving four channels —
"all four channels share exactly the same offset error, so a residual appears as
a common shift across the mod set rather than as four channels disagreeing" —
and then says "**Do not be tempted to split it into four buffers.**"

The AC version of that question is not addressed anywhere: when channel 1 slews,
its 10 kΩ input resistor pulls on the shared buffer's output, and the buffer's
finite closed-loop `Z_out` turns that into a voltage on `V_ref`, which appears
on channels 2–4 as `−3 × ΔV_ref`, i.e. **amplified by three**. With `Ro` now
known to be 375 Ω rather than 75.8 Ω, the buffer's `Z_out` at audio frequencies
is five times what anyone assumed.

Same run should check the buffer's own stability into 4 × 10 kΩ plus four
`R-OPAMP-IN` and the board capacitance, and the mod output stages' claim that
"their feedback comes from the op-amp output, so `R-OUT-PROT` isolates the
capacitor" for `C-FILT-MOD` 82 nF — free, since the netlist is already built.

**Cost if wrong:** four mod outputs that modulate each other. Recoverable in
firmware only if it is DC, and it is not. **Rank 7.**

### 2.8 ADC front-end settling — 10 kΩ into a 20 pF sample cap

**Refs: `R-ADCDIV-U` 10 k, `R-ADCDIV-L` 15 k, `C-AA-ADC` 47 nF, MCP3202 CH0.**

`carrier.md` computes sample-cap charge sharing `[calc]` against "20 pF sample
cap, 1.5 clocks of acquisition" and the divider's source impedance. A 10 kΩ
source into a SAR's sampling network is the classic place this goes wrong, and
it is one transient. It is also the only thing standing between the display's
breath bar and the jack's actual value — and `breath-receive-stage.md` has
already ruled that "**E10 scopes the jack**, not the display… a flat bar on the
screen is no longer evidence about the output." **Rank 8.**

### 2.9 Lower, but cheap and on the same netlists

- **Pitch jack-referred frequency response.** `pitch-stage.md` claims the
  2.2 nF + 10 nF combination is "maximally flat: −3 dB at 12.2 kHz… and −41 dB
  at 1 MHz against the 6 dB the shelf gives alone." The plan's DC sweep does not
  produce this; the loop-gain sweep is a different transfer function. One AC
  magnitude sweep from the DAC node to the jack.
- **`C-AA-PITCH`'s 15.9 kHz** is derived against `R-OPAMP-IN` 1 kΩ alone, which
  assumes the DAC8568 output impedance is zero. It is not, and this node is
  outside every loop.
- **`.temp` on the shaper** (1.6 above).
- **`D-RESP` asymmetry.** "Breath is unipolar, so only one of the antiparallel
  pair ever conducts in normal play. The second is there for the
  power-on/fault excursions the review catalogued" — which ties it to 2.5.

### 2.10 One process gap, not a simulation

**Nothing in the plan says where a SPICE result goes.** Every other number in
this repo is governed by `config/figures.yaml`: stated once, cited by name,
with `forbidden` carrying the old value. A phase margin produced by a
simulation is exactly a tracked figure — it has an owner, a derivation and a
provenance. If stage 2's outputs are written into schematic pages as prose, they
become instance ninety-one of the failure this project is named after. They
should land in `figures.yaml` with the netlist and the model named in
`derivation:`.

And, under the same rule: **the macromodels are datasheets.** `OPAx197.LIB` is a
TI-issued document, dated, versioned ("Final 1.3"), with a URL that returns 200
and content that hashes. CLAUDE.md §3 says datasheets are banked with a
`MANIFEST.csv` row and a SHA-256, not linked. The plan downloads the model from
GitHub at run time and banks nothing — so a simulation result in this repo would
be reproducible only as long as one stranger's repository stays up. Bank the
`.LIB` files.

---

## 3. Tooling: tested answers

### 3.1 PySpice 1.5 against ngspice 42 — **it fails, and the plan's "verified" is wrong**

`PySpice 1.5` installs from pypi against ngspice 42. A two-resistor divider:

```
$ python t1.py
PySpice 1.5
Unsupported Ngspice version 42
Using SPARSE 1.3 as Direct Linear Solver
  ...
PySpice.Spice.NgSpice.Shared.NgSpiceCommandError: Command 'run' failed
```
`[test]`

The plan lists PySpice as "pip — verified". What was verified was that it
*downloads*. It does not run.

**Root cause, and it is silly.** The simulation completes correctly — the debug
log shows `No. of Data Rows : 1`. Then `_send_char` classifies stderr:

```python
# PySpice/Spice/NgSpice/Shared.py, _send_char
if prefix == 'stderr':
    self._stderr.append(content)
    if content.startswith('Warning:'):
        func = self._logger.warning
    else:
        self._error_in_stderr = True      # <-- everything else is "an error"
```
and `exec_command` then raises on `self._error_in_stderr`. `[test]`, source
inspected at `venv/lib/python3.11/site-packages/PySpice/Spice/NgSpice/Shared.py`.

ngspice 42 writes **`Using SPARSE 1.3 as Direct Linear Solver`** to stderr on
every `run`. It is an informational banner. PySpice 1.5 predates it, so every
analysis raises.

**Workaround, verified.** A ten-line monkeypatch that clears
`_error_in_stderr` when every captured stderr line is on a benign list:

```
DC:  V(vout) = 2.5                                    (exact)
AC:  RC low-pass gain at 1000.0 Hz = -3.010 dB        (expect -3.01)
TI OPAx197 macromodel follower: 2.500022126453464 V
```
`[test]` — all three under PySpice 1.5 / ngspice 42.

So PySpice is *usable*, with a patch to a third-party library's private
callback. That is a maintenance liability in a repo that will be picked up
months later.

**Recommended fallback, and it is better than the workaround: raw ngspice
netlists driven by `subprocess`.** Every result in this report — the Zo sweep,
four phase-margin configurations, five pitch loads, the transient overshoot
table — was produced that way, with `.meas` and `wrdata` in the netlist and
`numpy.loadtxt` reading the columns. No wrapper, no version gate, no patch, and
the netlist that produced a figure is a reviewable artifact you can paste into a
bug report. Nothing in stage 2 needs a simulator driven interactively; it needs
netlists generated and columns read.

A second fallback exists and is worth knowing about: **InSpice**, the maintained
PySpice fork — see below, because SKiDL already depends on it.

### 3.2 SKiDL's SPICE path — **it works, but not the way the plan says**

**`skidl.pyspice` does not use PySpice.** It imports **InSpice**. SKiDL 2.3.0
pulls InSpice in as a dependency; the object `generate_netlist()` returns is an
`InSpice.Spice.Netlist.Circuit`, not a PySpice one `[test]`. Installing both, as
the plan's stack table implies, gives you two different SPICE wrappers with
incompatible APIs in one venv. Calling PySpice's `circuit.simulator()` on a
SKiDL circuit raises `NameError: Deprecated API` `[test]`.

**It is Python-version-gated.** On Python 3.11, SKiDL 2.3.0 pulls
`InSpice 1.6.3.3`, which does not import:

```
File ".../InSpice/Spice/NgSpice/Shared.py", line 1147
    command += f' after {kwargs['after']}'
SyntaxError: f-string: unmatched '['
```
`[test]` — a PEP 701 nested-quote f-string, legal only on Python 3.12+. So
`from skidl.pyspice import *` succeeds and netlist generation works, but
*simulation* is a SyntaxError.

On Python 3.12 (`python3.12` is present; `python3.12 3.12.3-1ubuntu0.12`
installed) SKiDL pulls `InSpice 1.7.0.7` and the whole path works, **with no
patch needed** — InSpice's `_send_char` has since learned to whitelist
ngspice's informational stderr:

```
$ ./v312/bin/python sk3.py
InSpice.Spice.Netlist
SKiDL->InSpice->ngspice42 OK: {'n_2': 2.5, 'n_1': 5.0}
```
`[test]`

**This collides with the plan's own headless gotcha.** The plan warns that
"`pcbnew` is built against the system interpreter" and recommends
`--system-site-packages`. If KiCad 9's `pcbnew` is built for a different Python
than InSpice needs, `--system-site-packages` does not reconcile them. These two
constraints have to be checked together before `setup.sh` is written; the plan
treats them as unrelated rows in a table.

### 3.3 "One SKiDL source emits both a KiCad netlist and a SPICE circuit"

**Tested. Technically true, practically not the claim the plan is making.**

From one source I generated both. The SPICE circuit simulates correctly. The
KiCad netlist emits — with three hard errors for a three-component circuit:

```
ERROR: No footprint for V/VS added at sk3.py:4.
ERROR: No footprint for R/R1 added at sk3.py:5.
ERROR: No footprint for R/R2 added at sk3.py:5.
INFO: 3 errors found while generating netlist.
KICAD OK
```
`[test]`

And in the `.net` file, every part:

```
(comp (ref "R1") (value "1 kΩ") (footprint "")
      (libsource (lib "NO_LIB") (part "R")))
```
plus `VS` — a SPICE *stimulus* — present as a board component. `[test]`

The SPICE primitives come from SKiDL's own pyspice library and carry no KiCad
symbol, no footprint and no library. Going the other way is worse: a part
instantiated from a KiCad symbol library has no `pyspice` attribute and cannot
be emitted into a SPICE netlist at all.

So in practice you maintain a **board** description (KiCad symbols, footprints,
connectors, jacks, test points, mounting holes) and a **simulation** description
(stimuli, macromodels, load models, no connectors) — and they are two documents
that can drift. Which means the plan's strongest argument for SKiDL,

> Circuit-as-code pays off twice here. SKiDL emits a PySpice circuit from the
> same source that emits the KiCad netlist, so there is **one description of the
> circuit, not two that can drift**.

does not survive contact with the SPICE path, and should be struck. SKiDL is
still the right tool for the *netlist* — `ERC()`, diffability, re-runnability
all hold. The simulation is not free with it.

**A cheaper way to get the anti-drift property it was after:** the parity check
the plan already proposes for the board netlist. Assert in Python that each
simulation netlist's R/C values and connectivity for a given page match the
SKiDL board module's, for the subset of nets the sim covers. That is the check
`--schematic-parity` was a proxy for, applied in the other direction.

---

## 4. Model availability

All `[test]` unless noted: URL fetched and, where marked "runs", loaded and
solved in ngspice 42 on this machine.

| Part | Model found? | Where | Good enough for what |
|---|---|---|---|
| **OPA2197 / OPAx197** | **Yes** — TI, Green–Williams–Lis, "Final 1.3", 23JUN2022 | `raw.githubusercontent.com/chevalierid/alan-setup/master/fab/kicad/libraries/pspicetilib/OPAx197.LIB` — HTTP 200, 16,625 B. **Runs** | Everything: `A_OL` 134.8 dB measured, `V_os` 22 µV, `Zo` vs f, stability, transient, clipping. Validated against the banked datasheet to 4 % (§1.3). Needs `ngbehavior=psa` |
| **INA828** | **Yes** — TI GWL, SBOS792A | **Same directory**, `INA828.LIB` — HTTP 200, 18,933 B. **Runs** | Gain (reproduced the corpus's 2.1611 to five figures), `REF` additivity, **CMRR vs frequency** — i.e. §2.1, the biggest missing sim. *The plan does not mention this part at all* |
| **REF5050** | **Yes** — TI, "ALL IN ONE", SBOS410E | **Same directory**, `REF5050.LIB` — HTTP 200, 8,015 B. **Runs**: `v(out) = 5.0025 V` | Line/load regulation, the buffer's real source impedance and noise. **Contradicts the plan's "the reference … need[s] no vendor model."** Gotcha: ships with both grade blocks commented out — one four-line group must be un-commented by hand, and `ref5050-grade` is `disputed` in `figures.yaml`, so which one is not yet decided. Pin order is `VIN TEMP GND TRIM VO` |
| **LM317** | **Yes** | `raw.githubusercontent.com/KiCad/kicad-source-mirror/master/demos/simulation/power_supplies/LM317_power_supply/LM317.lib` — HTTP 200, 2,262 B | The 5.21 V `AVDD` rail's power-on ramp and line rejection (§2.5). Provenance is KiCad's demo collection, not TI — weaker than the two above, fine for a rail transient, **not** for the 0.52 mV/V line-regulation figure the pitch argument uses |
| **DAC8568** | **No** — GitHub code search returns documentation hits only, no `.SUBCKT` | — | Behavioural PWL voltage source is the correct answer, and the plan says so. **But note the consequence:** the two largest terms in the pitch error budget (internal reference drift, ±4 LSB INL) belong to this part, so §1.5's Monte Carlo cannot source them from a model |
| **MPXV4006DP** | **No** — no SPICE model in any indexed repo | — | Behavioural source (0.2 V + 0.766 V/kPa) is correct and sufficient. The "20 mV in 10 V over warm-up" drift stays unverifiable — `breath-receive-stage.md` already says so, and `nxp.com` is blocked |
| **LT1641-1** | **No** (researcher's finding, not re-tested here) | — | **But see §2.3:** the foldback law, timer currents and thresholds are now written out as equations in `power-entry.md`, which is a behavioural model in all but syntax. The plan's "not simulable" is a conclusion it does not have to accept |
| **LT5400** | **Not needed** | — | Two ideal resistors plus a tracking parameter models a matched network better than any vendor file would. Its real open question is an order code, not a model |
| **1N5817, 1N4148, BAV99** | **Yes**, standard `.model` / `.SUBCKT` cards, widely mirrored — e.g. `kicad-spice-library/KiCad-Spice-Library` `[source]` | | Clamp currents, the shaper's knee shape, entry-diode drop at DC. **Not** the 1N5817 `V_f` modulation: `figures.yaml`'s 120 mV is digitised off the actual curve and calibrated against two guaranteed points, and per CLAUDE.md §3 that beats a generic model. Do not let a sim overwrite it |
| **N-channel FET (load switch)** | n/a — part not selected (`TBD`) | | Blocked on part choice, and the binding question is Spirito/SOA, not SPICE |
| **74AHCT125, 74HC165** | No, and not wanted | | Digital timing is a datasheet question; the corpus already treats it that way |

### 4.1 Is a generic op-amp macromodel adequate for stability work?

**It tells you a topology has a problem. It never tells you the problem is
solved.** Concretely, for this design:

**What a generic one-pole model (GBW, `A_OL`, `Ro`) CAN tell you:**
- Whether a loop has a stability problem *at all* — a 9° margin and a 70° margin
  are far enough apart that no reasonable model confuses them.
- The **direction and rough size** of a compensation change.
- The DC transfer function, the sign, the endpoints, the clipping points.
- **Relative** comparisons: whether the in-loop tap beats the out-of-loop tap
  (§1.2), whether 10 Ω beats 47 Ω. It got the in-loop/out-of-loop answer
  qualitatively right.

**What it CANNOT tell you:**
- A phase-margin number to order parts against. The three things that set the
  answer — `Zo` versus frequency, the second and third poles, and output-stage
  behaviour into a capacitive load — are exactly the three things a one-pole
  generic model does not have.
- The magnitude of the error when `Ro` is guessed. This corpus is the proof:
  a back-solved 75.8 Ω against a specified 375 Ω moved **every derived pole by
  ~5×, in the unsafe direction** (`figures.yaml`, `opa2197-output-impedance`).
  One number wrong in a model that only has three.

**And here is the part worth pinning up.** Even the *vendor's own* macromodel is
optimistic against the *vendor's own* tabulated answer for the same part and the
same load. `carrier.md` quotes SBOS737C Table 3 p.23 for 0.1 µF: `R_ISO` 6.2 Ω
for 45° and 15.8 Ω for 60°. The macromodel, same load, feedback at the op-amp
output:

| `R-ISO-REF` | Macromodel PM `[test]` | TI Table 3 `[repo] carrier.md` | Optimism |
|---|---|---|---|
| 6.2 Ω | **54.4°** | 45° | +9° |
| 15.8 Ω | **93.7°** | 60° | +34° |

Some of that gap is definitional — TI's table is for a specified measurement
setup and mine is voltage injection at the input pin — which is precisely the
point: **a simulated phase margin and a tabulated phase margin for the same
part are not the same quantity, and they differ here by up to 34°.** Treat a
simulated PM as a screen with a ±10° bar around it at best, never as a spec.

**Where a generic model would be actively misleading in this design:**
- Anything where `Zo` *is* the mechanism — `R-ISO-REF`, the shared mod reference
  buffer. A generic model's `Ro` is whatever you typed.
- Anything where output-stage current limiting matters — the shorted pitch jack,
  the `D-JACK-CLAMP` fault cases.

Since vendor GWL models exist here for all three active parts that matter
(OPA2197, INA828, REF5050) and all three run, **this project does not need a
generic op-amp anywhere.** The plan's paragraph about generic models is
contingency for a situation it does not have.

---

## 5. What SPICE cannot settle here

So that nobody mistakes a green simulation for a working board. In rough order
of how badly it would be mistaken:

1. **Layout — and layout holds the largest live error term in the design.**
   `power-entry.md` puts the ground-path, breath-correlated pitch terms at
   **7.4 / 8–18 / ~7 cents**, against a static budget of 0.42 cents. Every one
   of those is a millivolt of IR drop in a return path. **A netlist-level
   simulation computes all of them as exactly zero.** Every net in pipeline
   stage 4 — `AGND` as a sense-only star, the matched `BREATH`/`AGND` pair, the
   `PWR_GND`/`DIG_GND` split, the pitch feedback loop *area* — is a geometry
   question that stage 2 cannot see. A clean stage 2 says nothing about them,
   and the pipeline's own text ("the loop *area* is a layout judgement") already
   knows it.
2. **RF rectification at the in-amp input.** This is the stated reason the
   500 Hz filter is ahead of the INA828 rather than after it, with a 2.4 GHz
   radio two metres away on the same bundle. Macromodel inputs are linear;
   input-stage nonlinear rectification is not modelled by any of the three
   models above. A green CMRR sweep at 1 MHz says nothing about it.
3. **The LT1641, even with the behavioural model of §2.3.** The law being
   modelled is `[web, search-index]` from a BLOCKED datasheet. A green start
   simulation confirms that somebody transcribed the equations consistently.
4. **Which side of the buffer `C-REF-OUT` sits on.** `carrier.md` records that
   three files disagree, that "no grep finds that", and that "which is true
   changes the whole compensation." A simulation of either version is a
   simulation of a circuit nobody has agreed to. **Settle the schematic first —
   simulating an ambiguity produces a confident answer to an undecided
   question**, which is the most expensive thing on this list.
5. **Component tolerance, unless someone supplies real distributions.** SPICE
   will Monte Carlo happily over numbers that were guessed, and hand the result
   back with a standard deviation. §1.5.
6. **The MPXV4006DP's offset tempco** — the explicitly "unverified" ~20 mV/10 V
   warm-up drift. No model, `nxp.com` blocked.
7. **The FET's Spirito / linear-mode derating at `V_DS` = 12 V.** An SOA-chart
   question. A transient showing 4 W of peak dissipation does not tell you
   whether that particular trench part survives it.
8. **Thermal anything.** `R1`'s 139 mW in an 0805, `R-OUT-PROT`'s 133 mW on a
   short, the DPAK's 0.6 °C/W at 50 ms. SPICE gives you the watts and nothing
   about where they go.
9. **Phase margin to better than ~±10°.** §4.1.
10. **Feel.** `POT-GAIN`'s taper, `POT-OFFSET`'s detent, how strong "fully
    exponential" feels, where a hard blow actually lands in kPa. Three pages say
    these are bench questions with a real player. They are, and a curve that
    looks right is not evidence.
11. **Anything the netlist does not contain.** The defect this project keeps
    producing is semantic — an argument surviving its own refutation,
    `mod-channels.md` justifying its topology on a deleted watchdog. A
    simulation is a grep with better maths. CLAUDE.md §4 already says the
    checker cannot catch semantics; **stage 2 cannot either**, and it should not
    be allowed to feel like it does.

---

## What I would change in stage 2, in one list

1. Strike "AC sweep of the macromodel's `Zo`" as a way to retire a blocked item
   — the datasheet landed. Keep it as a one-off model validation.
2. Strike the "dead short" row from the loop-gain sweep; it has no crossover.
   Make it a transient.
3. Strike the pitch page's "highest-risk item on that page" framing: measured
   69.3° at every load.
4. Move Monte Carlo off the pitch cents budget (which it cannot settle) and onto
   the breath CMRR network and the mod-channel resistor pair (where it has real
   inputs).
5. **Add §2.1 (breath CMRR with the INA828 model) at the top of the list.**
6. **Add §2.2 (pitch transient into a mult) second** — and note in the plan
   itself that the loop-gain sweep cannot see it.
7. Add the behavioural LT1641, the end-to-end breath chain, the power-on
   transient and the input-LC damping sweep.
8. Fix the stack table: PySpice 1.5 does **not** run against ngspice 42
   unpatched; SKiDL uses **InSpice** and needs **Python ≥ 3.12**; add
   `set ngbehavior=psa` to `setup.sh`.
9. Strike "one description of the circuit, not two that can drift" — tested,
   and the SPICE and board descriptions are two documents.
10. Bank the `.LIB` files in `datasheets/` with SHA-256 rows, and route every
    simulated figure into `config/figures.yaml`.
