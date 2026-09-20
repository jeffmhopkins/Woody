# B5 — Module power entry and distribution

Independent review. Sources read: `README.md`, `ROADMAP.md`, `docs/decisions/0001`–`0014`,
`docs/reference/`, `hardware/bom.csv`. `docs/review/` and `docs/log/` deliberately not read.

## Datasheet provenance

Figures I assert, and how I got them:

| Figure | Source | Status |
|---|---|---|
| TPS2553: 2.5–6.5 V input, 85 mΩ, ILIM 75 mA–1.7 A, ±6 % accuracy at the top of range, constant-current (`-1` suffix = latch-off), thermal hiccup | TI TPS2553 datasheet, retrieved via search summary | **Verified this session** (summary of the datasheet text; I could not open the PDF — TI is blocked by the egress proxy) |
| WS2815: PWM refresh 2 kHz; quiescent current < 2.1 mA per LED; 12 V | Worldsemi WS2815 datasheet, via search summary | **Verified this session** |
| R-78E5.0-1.0: input 7–28 V; switching frequency 330 kHz at Vin = 12 V; output ripple 120 mV p-p | Recom R-78E-1.0 datasheet, via search summary | **Verified this session** |
| DAC8568: AVDD recommended 2.7–5.5 V; V_IH min = 0.625 × AVDD for 4.5 V ≤ AVDD ≤ 5.5 V | TI DAC8568 datasheet, via search summary | **Verified this session.** Note this contradicts ADR 0004's "0.7 × AVDD" |
| LM317L: V_ref 1.20–1.30 V over line/load/temp; I_ADJ ≤ 100 µA; minimum load ~2.5–3.5 mA | TI / onsemi LM317L datasheets, via search summary | **Verified this session** (the ±4 % envelope and the 100 µA cap; I did not read the table directly) |
| 1206L050 PPTC: I_hold 0.50 A, I_trip 1.0 A at 23 °C, voltage variants from 6 V to 48 V | Littelfuse 1206L datasheet, via search summary | **Verified this session** |
| 1206 500 mA PPTC R_initial ≈ 0.3–0.9 Ω; hold-current derating ≈ ×0.7 at 50 °C ambient | — | **From memory.** Shape of the derating curve is standard across vendors; the exact numbers must be read off the chosen part |
| 1N5817 V_F ≈ 0.33–0.40 V at 0.5 A, 25 °C (max spec 0.45 V at 1.0 A); I_FSM 25 A | — | **From memory** of the onsemi/Fairchild curve |
| OPA2197 PSRR ≈ 100 dB at 2 kHz (120 dB DC, −20 dB/decade above ~1 kHz) | — | **From memory** of the PSRR-vs-frequency curve. Everything I conclude from it survives a 20 dB error |
| 1206/1210 ferrite bead, 600 Ω @ 100 MHz class: low-frequency L ≈ 1 µH, DCR 50–100 mΩ | — | **From memory**, but the conclusion (Z at 2 kHz = DCR) is insensitive to a 3× error in L |
| 28 AWG 0.212 Ω/m, 26 AWG 0.134 Ω/m, 24 AWG 0.0842 Ω/m; 1 oz copper 0.5 mΩ/square | Standard wire tables | From memory, standard |

## The current budget I work from

ADR 0004 states ~320 mA on +12 V and flags it as "the least trustworthy number in this
document". Rebuilding it from the design's own constituent numbers:

| Item | mA @ +12 V | Basis |
|---|---|---|
| 50 × WS2815 driver quiescent | **105** | 50 LEDs (0.84 m at 60/m) × 2.1 mA max, datasheet-verified. ADR 0005's "~120 mA" is right |
| Lit LEDs, inside the 3 W firmware clamp | **145** | 3 W / 12 V = 250 mA total lighting, less the 105 mA quiescent |
| R-78E5.0 input for 400 mA of 5 V load | **183** | 400 mA × 5 V = 2.0 W, ÷ 0.91 efficiency ÷ 11 V = 183 mA |
| REF5050 + OPA2197 on raw +12 V | **6** | ADR 0003 |
| **Umbilical total, steady** | **≈ 440** | |
| Module's own analog + LM317 branch | **≈ 45** | ADR 0004 |
| **Module +12 V bus draw, steady** | **≈ 485** | |
| WiFi TX burst, ~2 ms | **+110 peak** | 350 mA @ 3.3 V ≈ 1.2 W ≈ 110 mA @ 12 V |

If the 3 W clamp is interpreted as *emitted light* with the 105 mA of driver quiescent
sitting outside it — which is how ADR 0014's table reads, since it tabulates LED states
and not driver idle — the umbilical figure is **545 mA** and the bus figure **590 mA**.

**I use 440 mA umbilical / 485 mA bus steady, 600 mA peak** throughout, and say where the
higher reading changes the answer. Every finding below gets worse, not better, on the
higher reading.

---

# Findings

## 1. The specified load switch is a 5 V USB part and will be destroyed by the rail it is placed on

**Severity: SHOWSTOPPER**

**Where.** `hardware/bom.csv`:

> `U-LOADSW,module,TPS2553DBV,TI,Current-limited load switch on the umbilical +12V feed,SOT-23-6`

and ADR 0005:

> "**The toggle drives a TPS2553-class current-limited load switch on the umbilical +12 V
> feed**, rather than breaking the current itself."

and ADR 0004's power tree: `└──[ferrite]──[bulk]──[TPS2553]── umbilical +12V`.

**Why.** The TPS2553 is a **USB power-distribution switch with a 2.5 V to 6.5 V input
range** (verified this session against the TI datasheet text; the datasheet's own
application diagram is labelled "5 V USB Input"). Absolute maximum on IN is in the 7 V
region. Placing it across the module's protected +12 V node applies roughly **2× its
absolute maximum** at the instant the rack comes up. This is not a derating argument; it
is a part that conducts, smokes, and takes the umbilical short-to-12 V behaviour with it
— which is the opposite of what a protection device is for.

ADR 0005 defends the part on *package* grounds ("SOT-23-6 … at 0.95 mm pitch it is
coarser than the TSSOP-16 DAC already accepted") and never states its voltage rating.
That is the tell: the review that accepted it checked the pin pitch and not the abs-max
table.

**Proposal.** Re-specify for a 12 V rail. The function wanted is: enable input, adjustable
current limit, controlled dV/dt ramp, fault output, auto-retry or latch (see finding 4 for
why the ramp behaviour is not optional). Candidate families, all of which need their own
datasheet pass before selection:

- **TI TPS259x / TPS166x eFuse** (e.g. TPS2592, TPS1663) — 4.5–18 V and 4.2–60 V classes,
  adjustable limit and programmable dV/dt. Package is the thing to check; several are SON.
- **A hot-swap controller driving an external FET** — LM5069 (MSOP-10, 9–80 V, programmable
  current limit, power limit and fault timer) plus a DPAK N-FET. MSOP is inside the stated
  package policy, and the external FET is what finding 4 requires anyway.

Keep the panel toggle on the controller's enable, exactly as designed — that part of the
decision is right and survives the part change unchanged.

**Confidence: very high** on the defect (the voltage range is a datasheet headline figure
I verified). **Medium** on which specific replacement is best — that is a parts-selection
exercise, not a review finding.

**Falsified by:** reading the TPS2553 datasheet's Absolute Maximum Ratings table and
finding an IN rating above 12 V. (It will not.)

---

## 2. The instrument-end polyfuse sits at 100 % of its hold current in normal play, and reinstates the runaway loop ADR 0014 believes it deleted

**Severity: SHOWSTOPPER**

**Where.** `hardware/bom.csv`:

> `F-POLY,controller,PPTC 1206 500mA hold,multiple,Resettable fuse at umbilical entry`

ADR 0005: "**Fuse the instrument at the umbilical entry.** … A polyfuse is cheap insurance".

ADR 0014, having described the thermal runaway in detail, concludes:

> "**The module's current-limited load switch** (ADR 0005) replaces a slow, self-heating,
> thermally-hysteretic protection device with a fast fixed limit that does not run away."

The load switch was added. **The slow, self-heating, thermally-hysteretic device was not
removed.** It is still in the BOM, still in series, still at 500 mA.

**Why — arithmetic.**

The umbilical carries ≈440 mA steady in the *legal, clamped, intended* state, and 545 mA
on the other reading of the clamp. Against a 500 mA hold rating that is 88–109 % before
any derating.

PPTC hold current is specified at ~23 °C ambient. The ambient here is the instrument's
sealed oak-and-acrylic interior, which ADR 0014 states runs **10–20 K above room**, plus
~9 K of the lighting budget's own rise:

- room 22 °C + 15 K interior + 9 K lighting = **46 °C ambient at the fuse**
- standard PPTC derating at 46 °C ≈ **×0.72** → effective hold ≈ **360 mA**
- effective trip ≈ 2 × hold ≈ **720 mA**

So at 440 mA the device sits **22 % above its derated hold current** — in the region where
a PPTC does not trip and does not stay cold either. It self-heats, its resistance climbs
from R_initial (~0.35 Ω) toward R_1max (multiple ohms), the rail sags, the buck is a
constant-power load so it draws *more* input current, the fuse heats further. That is
verbatim the loop ADR 0014 wrote out and believed it had broken.

The module's load switch does not break it, because **the polyfuse is downstream of the
load switch**. A current limit upstream of a thermally-unstable series resistance does not
stabilise it; it only caps the final current.

And the voltage drop is not small even before trip: 440 mA × 0.35 Ω = **154 mV** cold,
440 mA × 0.9 Ω = **396 mV** warm — 15–40 % of the entire end-to-end loss budget spent on
a component that is actively working against the design.

Secondary defect in the same line: the BOM specifies neither a voltage rating nor a part
number. The most-stocked 1206L050 variants are rated **6 V and 8 V**; the 15 V variant
exists but must be asked for. A 6 V-rated PPTC on a 12 V rail cannot safely interrupt.

**Proposal.** **Delete `F-POLY`.** Its job — "a short inside the instrument otherwise pulls
on the rack's +12 V rail" — is now done, faster and without thermal hysteresis, by the
module's load switch, which is exactly ADR 0014's own argument. If a last-ditch instrument-
end device is still wanted for a shorted umbilical *between* the switch and the instrument,
use a **fast-acting glass or chip fuse at 1.5–2 A, ≥ 32 V**, which is a one-shot device with
no hold/trip grey zone and ~30 mΩ of resistance, and accept that clearing it means opening
a bonded body — which is itself an argument for not fitting one.

**Confidence: high** on the mechanism and on the ≥88 %-of-hold arithmetic (the 440 mA
figure is built from the design's own datasheet-verified constituents). **Medium** on the
exact derating factor — verify against the chosen part's curve.

**Falsified by:** running the instrument at its full clamped lighting state for 30 minutes
with a thermocouple on the PPTC body and a 4-wire measurement across it. If the device
stays below ~35 °C and its resistance does not climb, the derating is gentler than I
assume. Measure this at E6 alongside the inrush measurement the roadmap already schedules.

---

## 3. The module's ground carries the instrument's entire return current, and that IR drop lands directly on every CV output — with no PSRR to save it

**Severity: MAJOR** — and in my view this is the most important finding in the review,
because it is free to fix on a board that does not exist yet and impossible to fix after.

**Where.** Nowhere. That is the finding. ADR 0004's power tree shows only the positive
rails. ADR 0003 spends five pages on ground:

> "**Give the analog signal its own return conductor that carries no power current** …
> `AGND` then sits at true instrument-ground potential at both ends"

with a table showing 16.8 / 33.7 / 58.9 mV of offset at 100 / 200 / 350 mA — and solves
the problem for the 2 m of Cat5. **The same current keeps flowing after it reaches the
module**, through ~40 mm of PCB copper and ~360 mm of ribbon, and no document assigns a
topology to that copper.

Meanwhile ADR 0004 devotes its longest technical passage to branching the **+12 V** rail
so "the buck's pulsed draw is absorbed locally instead of modulating the rail the pitch
scaling stage is referenced to."

**Why — arithmetic, both paths, side by side.**

*The +12 V path the ADR worries about.* Take the WS2815 PWM: 2 kHz (datasheet-verified),
~300 mA p-p of current modulation at the strips.

- Instrument-end bulk 2 × 470 µF = 940 µF. |Z_C| = 1/(2π × 2000 × 940e-6) = **84.7 mΩ**,
  plus ~50 mΩ of parallel ESR → **≈ 0.13 Ω**.
- Path back to the bus: PPTC 0.50 + cable 0.27 (26 AWG, 2 m) + contacts 0.017 + load
  switch 0.085 + bead DCR 0.05 + 1N5817 dynamic r_d (1.1 × 25.9 mV / 0.5 A = 0.057) +
  ribbon 0.038 + rack source ≈ 0.10 = **1.12 Ω**.
- Fraction of the 300 mA drawn from upstream = 0.13 / (0.13 + 1.12) = **10.4 %** = 31 mA p-p.
- Voltage on the module's shared node = 31 mA × (0.057 + 0.038 + 0.10) = **6.0 mV p-p**.
- Through the analog branch's bead (50 mΩ) into its 470 µF (|Z| 169 mΩ + ESR 100 mΩ):
  divider 0.27 / 0.32 = 0.84 → **5.1 mV p-p at the op-amp rails**.
- OPA2197 PSRR ≈ 100 dB at 2 kHz → 51 nV referred to input, × pitch stage gain ≈ 2 →
  **≈ 0.1 µV at the jack**.

0.1 µV is **0.07 % of one 153 µV LSB**, or 0.00012 cents. The +12 V problem is solved by
roughly four orders of magnitude, and the argument about beads and branching is a debate
about a non-issue.

*The ground path nobody wrote about.* The module must return **≈485 mA DC** (and, at
breath rate, a further **±145 mA** as the strips brighten and dim, which the local bulk
does *not* filter because breath is a 1–20 Hz signal) from the etherCON's `PWR_GND` pin to
the 16-pin header's ground pins.

- 40 mm of 1 mm-wide 1 oz trace = 40 squares × 0.5 mΩ = **20 mΩ**.
- Ribbon ground, 6 × 28 AWG at 0.356 m = 6 × 75.6 mΩ in parallel = **12.6 mΩ**.

If the analog section's reference is tapped anywhere along the etherCON→header run, the CV
outputs sit at:

| Where analog ground is tapped | DC offset on every CV output | On pitch, at 83.3 mV/semitone |
|---|---|---|
| At the etherCON end (the natural place if you route by proximity) | 485 mA × 32.6 mΩ = **15.8 mV** | **19 cents** |
| Kelvin'd to the header ground pins | 485 mA × 12.6 mΩ = **6.1 mV** | **7.3 cents** |

And the part that no calibration can remove, because it moves:

| Modulating term | Offset swing | Pitch swing |
|---|---|---|
| Strips 105 → 250 mA at breath rate, tapped at etherCON | 145 mA × 32.6 mΩ = **4.7 mV** | **5.7 cents, in time with the player's breath** |
| Same, Kelvin'd to the header | 145 mA × 12.6 mΩ = **1.8 mV** | **2.2 cents** |
| WiFi TX burst, 110 mA, 2 ms | 110 mA × 32.6 mΩ = **3.6 mV** | 4.3 cents, as a tick |

A fraction of this current also leaves through patch-cable grounds. Solving the network —
485 mA into the module ground, 12.6 mΩ of own ribbon in parallel with (patch cable ~0.1 Ω +
receiving module's ribbon 12.6 mΩ) — gives 11.3 mΩ of effective impedance and leaves the
module's ground **6.5 mV** above the receiving module's ground. The number depends on what
you patch into and how many things you mult to, which is the worst possible property for a
tuning error to have.

**For scale, against this project's own accepted standard:** ADR 0006 rejects BAT54S clamp
diodes because "a BAT54S's ~2 µA of Schottky leakage through the 1 kΩ output resistor is
2 mV, which is **2.4 cents** of temperature-dependent pitch error — reintroducing exactly
what the matched network and the trimmers were bought to remove." The ground path is
**2.5× to 8× that**, it is breath-correlated rather than merely temperature-dependent, and
it has never been costed.

**Proposal.** Three things, all free at layout time, all impossible afterwards:

1. **Route the umbilical return as a dedicated wide pour** — etherCON `PWR_GND` pin
   straight to the 16-pin header's ground pins, ≥ 4 mm wide or a poured zone, on its own,
   carrying nothing else. Target < 5 mΩ.
2. **Kelvin the analog reference to the header ground pins**, not to the nearest copper.
   Everything that defines a CV output voltage — the DAC's GND, the op-amp reference
   returns, the trimmer and matched-network bottom ends, the LM317's ADJ divider bottom,
   and the jack sleeves — returns on separate copper that meets the power return at
   exactly one point, at the bus header. Star it there, not at the etherCON.
3. **Make the remaining 12.6 mΩ smaller if the measurement says you must.** A single 20 AWG
   wire from the module's header ground to the bus board's ground stud (0.5 m, ~5 mΩ) in
   parallel with the ribbon takes 12.6 → 3.6 mΩ and the DC error from 6.1 → 1.7 mV. Ugly,
   effective, and reversible.

Also write this down as a decision. The absence of a ground-topology ADR in a project that
has fourteen ADRs and one of them is about LED colour is conspicuous.

**Confidence: high** on the mechanism and on the order of magnitude. **Medium** on the
20 mΩ figure for the in-module run — that is my assumed geometry, and a good layout could
be 5 mΩ or a bad one 60 mΩ. The point is that the figure is currently unbounded.

**Falsified by:** at E6/E7, with the module racked and a test pattern driving pitch to a
fixed code, measure the pitch jack tip **against the receiving module's ground** (not
against the module's own ground) with a 6½-digit meter while switching the instrument's
LEDs between blank and the full clamped state. If the reading moves by less than ~0.5 mV,
the ground is already good enough and this finding is over-stated. I predict 2–15 mV.

---

## 4. The inrush energy is fixed at ~86 mJ by the instrument's bulk; no SOT-23-6 can absorb it, and a 500 mA limit cannot start the load at all

**Severity: MAJOR**

**Where.** `hardware/bom.csv`:

> `U-LOADSW … Adjustable limit set ~500mA. Inrush ramp into the instrument bulk caps`

and ADR 0005:

> "**Inrush limiting.** The instrument's bulk capacitance is a near-short at the instant of
> connection. … a load switch ramps the output instead."

**Why — arithmetic.**

*The energy is not negotiable.* Charging a capacitance C from a fixed source to V
dissipates exactly ½CV² in the pass element, independent of how slowly you do it. The
instrument's bulk is 2 × 470 µF at the strip feed points (ADR 0014) + `C-BULK-DISP` +
the buck's input capacitance ≈ **1200 µF**:

> ½ × 1200 µF × (12 V)² = **86 mJ**

For scale, a TPS2553 in its designed application charges a USB port's 120 µF to 5 V:
½ × 120e-6 × 25 = 1.5 mJ. **The Woody umbilical is 57× that.** A SOT-23-6 with a junction-
to-ambient resistance around 200 K/W and a transient thermal impedance of perhaps
30–50 K/W at 30 ms sees 86 mJ / 30 ms = 2.9 W average, plus the load-current term
(see below) — a junction excursion of well over 100 K per switch-on.

*And the ~500 mA limit cannot start the load.* During the ramp the switch must supply
capacitor charging **plus** the load, and the load does not wait for the ramp to finish:

- 30 ms ramp → charging current = C·dV/dt = 1200 µF × 12 V / 30 ms = **480 mA**
- WS2815 quiescent, which is present from the moment the strips see ~9 V = **105 mA**
- the buck's UVLO releases at 7 V (datasheet-verified) and it immediately demands
  2.2 W / 7 V = **314 mA**
- **total ≈ 900 mA**, against a limit whose *nominal* is 500 mA

With TPS2553-class current-limit accuracy — ±6 % is the figure at the *top* of its range
and it degrades substantially at low settings — a 500 mA nominal could be 425 mA in the
worst unit. The switch enters constant-current regulation during the whole ramp, the
output never reaches 12 V, and:

*What happens at the limit is worse than "it limits".* The buck is a constant-power load.
In constant-current mode the switch holds I and lets V fall; the buck responds to falling
V by demanding more I. The operating point runs away downward until the buck's 7 V UVLO
drops it out, at which point the load falls, the voltage recovers, the buck restarts, and
the cycle repeats. That is **motorboating at a few tens of hertz**, and between each cycle
the MCU resets and the WS2815s hold their last latched colour (ADR 0014's own failure
description). The load switch does break the polyfuse's *thermal* runaway term, but if its
limit is set inside the normal operating envelope it substitutes an electrical one.

**Proposal.**

1. **Set the limit from measurement at ≥ 2× the measured worst-case legal draw.** The
   roadmap already schedules this ("Inrush with a current probe, on switch-on *and*
   hot-plug", E6). From my budget that means **1.0–1.2 A**, not 500 mA. A limit that a
   legal instrument state can reach is not a protection device, it is a fault generator.
2. **Use a pass element that can eat 86 mJ.** A hot-swap controller plus an external FET in
   DPAK (R_θJC ~3 K/W; 86 mJ over 30 ms = 2.9 W → ~10 K rise) rather than an integrated
   SOT-23-6. This also resolves finding 1.
3. **Program the ramp by dV/dt, not by letting the current limit do it.** A gate capacitor
   giving a 20–30 ms ramp keeps charging current at ~480 mA, well clear of a 1.2 A limit,
   so the switch never enters regulation on a normal switch-on. Then the current limit only
   ever operates on a genuine fault, which is what it is for.
4. **Check the fault timer against the ramp.** Any part with a fixed blanking or fault
   timer shorter than the ramp will latch off during every normal start. State the ramp
   time and the timer in the same sentence in the BOM.
5. **Bring `/FAULT` to the panel LED** the module already carries. A current-limit event
   should be visible, not present as "the instrument is being weird".
6. **Reduce what you have to charge.** If finding 7's measurement allows 470 µF rather than
   2200 µF at the strips, keep it there — inrush energy scales linearly with it.

**Confidence: high** on the 86 mJ (it is arithmetic on the design's own capacitor values)
and on the "500 mA cannot start it" conclusion. **Medium-high** on the motorboating: the
exact behaviour depends on the replacement part's latch-vs-retry choice.

**Falsified by:** the E6 inrush measurement. Current probe on the umbilical +12 V,
switch-on into the fully assembled instrument, scope on the umbilical node. If the peak
charging current is well under 300 mA and the node reaches 11 V monotonically in under
50 ms, my capacitance estimate is too high. Repeat with the strips latched full-white from
a previous session, which is the worst real case.

---

## 5. The LM317's real output tolerance straddles both edges of the DAC's requirement; and "full scale is the supply" is the wrong mechanism

**Severity: MAJOR**

**Where.** ADR 0004:

> "**So: an LM317LZ set to 5.25 V** … 5.25 V nominal keeps worst-case tolerance
> (±4 % on the LM317 reference) inside the DAC's 5.5 V recommended maximum while staying
> above the 4.75 V top of the used output window"

`hardware/bom.csv`:

> `R-REG-SET … Vout = 1.25*(1+768/240) = 5.25V. Worst-case +-4% = 5.04-5.46V, inside the DAC8568 5.5V max`

**Why — two problems.**

*(a) The tolerance calculation omits two terms.* The LM317 output equation is

> V_out = V_ref × (1 + R2/R1) + I_ADJ × R2

The BOM computes only the first term and only the reference's ±4 %. Adding the terms
actually present:

- V_ref over line, load and temperature: **1.20 to 1.30 V** (datasheet-verified)
- R1, R2 at 1 % each: the ratio 768/240 = 3.200 can be 3.135 to 3.265, so
  (1 + R2/R1) spans **4.135 to 4.265**
- I_ADJ ≤ 100 µA (datasheet-verified) across R2 = 768 Ω adds **0 to 77 mV**

> V_out(max) = 1.30 × 4.265 + 0.077 = **5.62 V**
> V_out(min) = 1.20 × 4.135 + 0.000 = **4.96 V**

**5.62 V exceeds the DAC8568's 5.5 V recommended operating maximum** (datasheet-verified),
and the BOM's claim that worst case is 5.46 V is short by 160 mV.

*(b) There is no nominal value that works.* The requirement is two-sided:

- ceiling: AVDD ≤ 5.5 V
- floor: AVDD must exceed the top of the used output window (4.75 V) by the DAC output
  buffer's headroom. ADR 0006 itself budgets 250 mV for this, so **AVDD ≥ 4.95 V**

A regulator with ±5.6 % total spread (the LM317L's ±4 % plus the divider's ±1.6 %) needs
V_nom ≤ 5.5/1.056 = 5.21 V and V_nom ≥ 4.95/0.944 = 5.24 V. **The window is empty.** The
LM317L cannot satisfy this specification at any setting, and the design is currently
relying on typical parts.

*(c) The stated mechanism is wrong, and correcting it matters.* ADR 0004 says repeatedly:

> "**The DAC's full-scale output is its supply.** DAC8568 at internal reference × 2 spans
> 0–5 V, so full scale *equals* AVDD."

The DAC8568 uses an **internal 2.5 V bandgap reference** (which ADR 0006 correctly notes
must be explicitly enabled). Its output is 2.5 V × gain × code/65536 — referenced to the
bandgap, **not** ratiometric to AVDD. AVDD sets only the ceiling the output buffer can
swing to. So within the used 0.25–4.75 V window the DAC's output is essentially independent
of AVDD; what AVDD does is decide **whether the top of the window clips**. That is why a
4.75 V bus rail is genuinely bad (a commanded 4.75 V would saturate around 4.6 V, exactly
as ADR 0004 says) and why the *dynamic* argument for a local regulator is right — but it
also means the requirement is a one-sided floor and a one-sided ceiling, not a target to
hit accurately. Which is the framing that makes problem (b) visible.

A fourth, smaller consequence of the same confusion: ADR 0004 computes the level shifter's
job against "0.7 × AVDD — 3.68 V at AVDD = 5.25 V". The DAC8568 datasheet specifies
**V_IH min = 0.625 × AVDD** for 4.5 V ≤ AVDD ≤ 5.5 V (verified), which is 3.28 V at
5.25 V — meaning 3.3 V logic is marginally in spec direct, and comfortably so at a lower
AVDD. The 74AHCT125 is still the right call for noise margin over 2 m of cable, but the
threshold figure driving that decision is wrong by 400 mV.

**Proposal.**

1. **Target 5.10 V, not 5.25 V**, and **use a regulator with a ≤ ±1 % reference.** An
   LP2951-class adjustable LDO (SOIC-8, 30 V input, 100 mA, 1.235 V reference at ±0.5 %)
   gives, with 1 % resistors, roughly 5.03–5.17 V — clear of the 5.5 V ceiling by 330 mV
   and clear of the 4.95 V floor by 80 mV, with 155 mV of V_IH margin improvement thrown in.
   A fixed 5.0 V ±1 % part (LP2950-5.0) is even simpler and lands at 4.95–5.05 V, which
   grazes the floor — so prefer the adjustable version set slightly high.
2. **If the LM317LZ is kept for build-effort reasons**, then the arithmetic must be closed
   from the other end: reduce the used DAC window's top from 4.75 V to **4.50 V** (ADR 0006
   already establishes the trimmer has full authority over the resulting gain change), which
   moves the floor to 4.70 V and makes 5.10 V nominal fit with margin at both ends.
   Measure the delivered rail on each built unit and record it — it is a one-off.
3. Either way, **write the two-sided inequality into the ADR** so the next person sizing a
   divider sees the constraint rather than a nominal value.

**Confidence: high** on the arithmetic and on the internal-reference mechanism. **High** on
5.62 V exceeding 5.5 V; **medium** on how much the DAC actually minds — 5.5 V is a
recommended-operating limit, not an absolute maximum, so this is a reliability and
specification-compliance issue rather than an instant failure.

**Falsified by:** building the LM317 circuit with worst-corner resistors (R1 at −1 %, R2 at
+1 %) and measuring V_out over −0 to +50 °C on three sample LM317LZs. If the spread is
inside 5.0–5.4 V, the datasheet envelope is far more pessimistic than production silicon —
likely true, but not something to build a calibrated instrument on.

---

## 6. The unprotected +5 V bus entry does not fail the way the ADR claims: the buffer's outputs go straight into the DAC

**Severity: MAJOR**

**Where.** ADR 0004:

> "Leaving it there keeps its switching current off the DAC's supply, and it means the only
> thing hanging on the unprotected bus +5 V pin is a $0.30 buffer. **A reversed or
> row-offset ribbon that puts +12 V onto that pin kills the buffer and nothing else**,
> which is why the +5 V entry gets no protection network of its own."

**Why.** The 74AHCT125's three outputs are wired to the DAC8568's `SCLK`, `DIN` and `SYNC`
pins, and the BOM shows no series impedance between them — `R-MOSI-SER` (220 Ω) is
explicitly "*at the driving end*", i.e. in the instrument, 2 m upstream of the buffer. So:

*Fault case.* +12 V on the buffer's V_CC. The buffer's outputs pull toward 12 V. The DAC's
input ESD structure clamps at AVDD + 0.3 = 5.55 V and conducts into the 5.25 V rail. With
the AHCT125's output impedance of ~30–50 Ω:

> (12 − 5.55) / 40 Ω = **161 mA per pin**, ~480 mA total

The LM317 cannot sink, so the 5.25 V rail is pumped upward against a load of only ~10 mA
until something breaks. **The DAC8568 — the module's most expensive and least replaceable
part, a 0.65 mm TSSOP — dies, and so does the LM317, and probably the 74HC123 watchdog if
it shares either rail.** The claim of graceful failure is wrong, and it is the stated
justification for leaving the pin unprotected.

*Sequencing case, which happens on every single power-down, not only on a fault.* Hold-up
times from the design's own capacitor values:

| Rail | Bulk | Load | Time to fall out of usefulness |
|---|---|---|---|
| Bus +5 V branch | 470 µF (`FB-IN`: "470uF at the load per branch") | ~13 mA | 470 µF × 3 V / 13 mA = **108 ms** |
| +12 V analog branch | 470 µF | ~55 mA | 470 µF × 4.7 V / 55 mA = **40 ms** (to the LM317's dropout) |
| DAC AVDD | follows the above | | **≈ 40 ms** |

**The +5 V logic domain outlives the DAC's supply by ~70 ms, every time the rack is
switched off.** During that window anything driving a DAC pin from the +5 V domain forward-
biases the DAC's input protection into a collapsed AVDD.

Three of the pins are accidentally saved: ADR 0004 gates the 74AHCT125's `OE` from
umbilical +12 V presence, and the umbilical node collapses in 940 µF × 3 V / 440 mA ≈
**6 ms** — long before 40 ms. That is a real and undocumented second purpose for the OE
gating and it should be written down as load-bearing, because a future revision that moves
the gating for a good-looking reason will reintroduce the hazard silently.

But `U-WATCHDOG` (74HC123) drives the DAC's `CLR` pin and is **not** gated by anything. Its
rail is not stated anywhere in the BOM or the ADRs. If it is on bus +5 V — the obvious
place, next to the level shifter — it drives `CLR` for 70 ms into a dead DAC on every
power-down. `LDAC`, `RSTSEL` and any other statically-driven DAC pin are in the same
position.

**Proposal.** Three parts, about 15 cents:

1. **220–470 Ω in series in every line between a +5 V-domain driver and a DAC8568 pin** —
   the three buffered SPI lines, `CLR`, `LDAC`, and any strapped control pin driven from
   logic rather than tied to its own rail. At 470 Ω the fault clamp current falls from
   161 mA to **13.7 mA per pin**, which the DAC's input structure survives. The delay cost
   is 470 Ω × ~10 pF = **4.7 ns** against a 0.6 MHz SPI clock with a 1.7 µs period — three
   orders of margin.
2. **Put a 1N5817 in the +5 V entry too.** At 10 mA its drop is ~0.20 V, giving
   4.75 − 0.20 = 4.55 V worst case; an AHCT125 at 4.55 V and microamp loading drives
   ~4.45 V against a V_IH of 0.625 × 5.1 = 3.19 V — **1.26 V of margin**. The ADR's own
   objection to protecting this pin was the drop, and at 10 mA the drop does not exist.
   Cost: one diode, already in the BOM as a line item.
3. **Reduce the +5 V branch bulk from 470 µF to 10 µF + 100 nF.** 470 µF on a 10 mA load
   serves no purpose except to create the 108 ms hold-up that causes the sequencing hazard,
   and to present an inrush load to whatever small regulator makes the case's +5 V.

**Better still, consider deleting the bus +5 V dependency entirely.** A second TO-92
regulator off the protected +12 V costs (11.6 − 5) × 10 mA = **66 mW** and removes an
unprotected, unsequenced, third-rail entry point from the design. ADR 0005 pre-empts this
with "A module that also worked in cases without a +5 V rail would be engineering for a
case this instrument is never in" — but that is answering a different question. The reason
to derive it locally is not portability; it is that the bus +5 V pin is the only entry in
the module with no protection, no defined sequencing relative to the DAC's rail, and a
direct electrical path into the DAC's input pins.

**Confidence: very high** on the fault-path analysis (it is straight circuit topology).
**High** on the 108 ms vs 40 ms hold-up asymmetry, given the BOM's stated capacitor values.
**Medium** on whether the watchdog is on +5 V — the BOM does not say, which is itself the
problem.

**Falsified by:** scope on AVDD, on bus +5 V and on the DAC's `CLR` pin, triggered on rack
power-down. If `CLR` reaches 0.5 V before AVDD falls below 1 V, the sequencing is safe and
only the fault case remains.

---

## 7. Every capacitor value in the filtering scheme is a function of one frequency, and the frequency is now verified — but the value derived from it is not

**Severity: MINOR** (it was a MAJOR until the datasheet checked out)

**Where.** ADR 0004:

> "*A ferrite bead is a wire at the frequencies that actually matter here.* The WS2815
> strips modulate their current at the PWM rate, **around 2 kHz**."

and ADR 0014: "**470–1000 µF at each strip feed point.**"

**Why.** I checked, because the entire filtering argument and every capacitor value hangs
on this one number and the ADRs assert it without a source. The WS2815 datasheet states
"Refresh Frequency updates to 2KHz" — **so the figure is right**, and the 470 µF follows
from it exactly:

> C ≥ ΔI / (2π · f · ΔV) = 0.30 A / (2π × 2000 Hz × 0.050 V) = **478 µF**

which is where 470 µF comes from, whether or not it was derived that way.

What is *not* established is the two inputs on either side: ΔI = 300 mA and ΔV = 50 mV.
And the sensitivity is brutal — the same formula at a 400 Hz refresh (which is what
WS2812B-class parts run, and what a substituted or counterfeit strip will do) gives:

> 0.30 / (2π × 400 × 0.050) = **2390 µF**

i.e. **5× the specified bulk**, at which point ADR 0014's "470–1000 µF" is wrong by a
factor of three to five and finding 4's inrush energy triples with it.

Two further notes on the same frequency question:

- **The buck's switching frequency is 330 kHz, not 496 kHz.** The Recom R-78E-1.0 datasheet
  gives 330 kHz at Vin = 12 V (verified). `C-AA-ADC`'s BOM note reasons from "a 496 kHz
  buck folds to 100 Hz". At 330 kHz and a 4 kHz sample rate the fold is 330000 mod 4000 =
  **2000 Hz**, not 100 Hz — above the 500 Hz corner rather than inside the breath band, so
  the conclusion survives, but the number in the BOM is someone else's part.
- **`L-BUCK-IN` is specified without the capacitance it works against.** "10–47 µH power
  inductor" forms an LC with whatever is at the buck's input; if that is only the module's
  internal input capacitance (~4.7 µF), f₀ = 1/(2π√(22 µH × 4.7 µF)) = **15.7 kHz** with
  Z₀ = √(22/4.7) = **2.16 Ω**. The stability check passes comfortably — the buck's negative
  input resistance is −V²/P = −(11)²/2.2 = **−55 Ω**, and the filter's peak output impedance
  with ~1 Ω of series damping is Q·Z₀ = 2.16 × 2.16 = **4.7 Ω**, about 21 dB below it. But
  the 8th harmonic of a 2 kHz square wave lands at 16 kHz, right on that resonance, and
  will ring. Specify the capacitor (10 µF X7R + a 47 µF electrolytic for damping puts f₀ at
  6 kHz with Z₀ = 0.6 Ω) rather than leaving it to whatever is inside the module.

**Proposal.** At E6, put a current probe on one strip's feed and capture the current
waveform: record the actual PWM rate, the actual ΔI at the clamped brightness, and the
resulting ΔV at the feed point. Then size C from the formula above with the measured
numbers and a stated ΔV budget, and **record the formula in the ADR**, so the value is
traceable to a measurement rather than being a number that happens to be right.

**Confidence: high** on the sensitivity arithmetic; the 2 kHz figure itself is now verified
so the immediate risk is low.

**Falsified by:** the current-probe capture above. If ΔI at the clamped brightness is 100 mA
rather than 300 mA, 220 µF is enough and the inrush energy halves.

---

## 8. Moving all the bulk to the load discards the only component that could do the second filtering job the ADR declares impossible

**Severity: MINOR**

**Where.** ADR 0004:

> "*And the second claimed job is not done at all.* 'Keeping the module out of the rack'
> cannot work by branching, because both branches are common upstream at the bus header.
> Filtering downstream of a shared node does not isolate that node."
>
> "**Bulk belongs at the load, not at the entry.** 470–1000 µF at each WS2815 feed point …
> rather than at the module end of a 14-inch cable."

**Why.** The first quotation is correct and is the sharpest observation in the power
documents. The conclusion drawn from it is not. Branching cannot isolate a shared node —
but **a low-impedance shunt at that node can**, and that is precisely what entry bulk is.
The ADR identifies the right problem, then deletes the right component.

From finding 3's numbers, the module injects 31 mA p-p at 2 kHz into a shared-node
impedance of 0.195 Ω = **6.0 mV p-p on the rack's +12 V bus**, for every other module in
the case to enjoy. Adding 1000 µF at the diode cathode (|Z| = 80 mΩ at 2 kHz, + ~60 mΩ ESR
= 0.14 Ω) puts that in parallel:

> 0.195 ∥ 0.14 = 0.081 Ω → 31 mA × 0.081 = **2.5 mV p-p** — a 7.5 dB improvement

and it comes with a second benefit the load-side capacitor cannot give: it reduces the
**current** that leaves the module, not just the voltage, so it helps the 330 kHz buck
content and the SPI-edge content too, where the instrument-end bulk's ESL has already given
up.

This is also the honest answer to E6's exit criterion, "*no noise injected back into the
rack*", which as the design currently stands has no component assigned to it at all.

**Proposal.** Keep both. 470–1000 µF at each WS2815 feed point (correct, keep it) **and**
1000 µF plus a 10 µF ceramic at the module's entry node, downstream of the 1N5817 and
upstream of the branch beads. The cost is one radial can in a 6HP module that has room for
it and 86 mJ of extra inrush at rack power-on — which the 1N5817 handles (I_FSM 25 A;
charging 1000 µF through ~0.2 Ω of bus impedance from a supply that ramps over
milliseconds gives a peak well inside it).

Restate the ADR's rule as: *bulk at the load bounds the current the load pulls from
upstream; bulk at the entry bounds the voltage that current develops on the shared node.
They are different jobs and you need both.*

**Confidence: medium-high.** The arithmetic is sound but every term (rack source
impedance, bus-board copper, bulk ESR) is an estimate within ~2×.

**Falsified by:** scope, AC-coupled, 20 MHz bandwidth-limited, on the +12 V bus at an
*adjacent module's* power header, with the instrument's LEDs switching between blank and
the clamped state. If the injected ripple is under 1 mV p-p without entry bulk, the rack's
own bus capacitance is doing the job and this is unnecessary.

---

## 9. Series-resistance budget: the cable gauge is unspecified, and the end-to-end drop is 3× the ADR's figure

**Severity: MINOR**

**Where.** ADR 0005's table gives "12 V / 250 mA / 84 mV drop / arrives as 11.92 V / 0.7 %
error", from "2 m of 24 AWG, round trip ~0.34 Ω". And `hardware/bom.csv`:

> `CABLE-UMB … Cat5e STP patch lead, STRANDED, ~2m`

**Why.** The ADR is right to insist on stranded patch lead (solid core does work-harden and
fracture — that reasoning is sound). But **stranded Cat5e patch leads are commonly 26 AWG,
and "slim" patch leads are 28 AWG.** 24 AWG stranded patch cord exists but has to be
specified deliberately:

| Gauge | Ω/m | Round trip, 2 m | Drop at 440 mA |
|---|---|---|---|
| 24 AWG | 0.0842 | 0.34 Ω | 148 mV |
| **26 AWG** (the likely default) | 0.1345 | **0.54 Ω** | **237 mV** |
| 28 AWG (slim patch) | 0.2129 | 0.85 Ω | 375 mV |

Full series budget at 440 mA umbilical / 485 mA bus, 26 AWG, from a worst-case
11.40 V bus:

| Element | Drop |
|---|---|
| Ribbon, 2 × 28 AWG in parallel (37.8 mΩ) | 18 mV |
| 1N5817 at 0.485 A | 350 mV |
| Ferrite bead DCR, umbilical branch (50 mΩ) | 22 mV |
| Load switch (85 mΩ, TPS2553 figure) | 37 mV |
| etherCON/RJ45 contacts, 2 mated pairs × 2 conductors | 35 mV |
| Umbilical +12 V and PWR_GND, 26 AWG | 237 mV |
| PPTC (finding 2), 0.5 Ω | 220 mV |
| Module and ribbon ground copper | 33 mV |
| **Total** | **≈ 0.95 V** |
| **Arrives at the instrument as** | **≈ 10.45 V** |

Against the ADR's claimed "11.92 V, 0.7 % error", the real figure is **8.3 % error**. The
consequences are all survivable, which is why this is MINOR and not worse:

- **R-78E5.0:** needs ≥ 7 V (verified). 10.45 V is fine, with 3.45 V to spare.
- **WS2815:** nominally 12 V. At 10.45 V the strips will be dimmer and slightly
  colour-shifted, and the shift will *track the instrument's own current* — the LEDs get
  dimmer as they get brighter. Visually this is a soft compression, not a fault, but it is
  worth knowing before someone chases it as a firmware gamma bug.
- The ADR's headline conclusion — **12 V up the cable, not 5 V** — is correct and in fact
  *more* correct than stated: at 5 V the same power would need ~1.06 A, dropping
  1.06 × 0.54 = **570 mV** and arriving at 4.43 V, far outside the MPXV4006DP's
  4.75–5.25 V window rather than merely at its edge.

**Proposal.** Specify the gauge: "Cat5e STP stranded patch lead, **24 AWG conductors**,
2 m" in `CABLE-UMB`, and note that 26/28 AWG slim leads are an acceptable emergency spare
that costs ~90 mV of rail. Deleting the PPTC (finding 2) recovers 220 mV of this on its
own. Re-run the arrival-voltage line in ADR 0005 at the corrected current.

**Confidence: high.** The wire tables are standard and the arithmetic is straightforward.

**Falsified by:** a 4-wire measurement of the actual patch lead's loop resistance at DC,
and a meter on the instrument's +12 V node at full clamped load.

---

## 10. Small things

**10a. The ±12 V headroom claim is optimistic by ~40 %, though still adequate.**
MINOR. ADR 0006: "±12 V rails less ~0.35 V of Schottky leaves ±11.65 V, and an OPA2197
reaches ~±11.45 V — 1.45 V of margin at ±10 V." But the two Schottkys carry very different
currents — 485 mA on +12 V (V_F ≈ 0.35 V) and 40 mA on −12 V (V_F ≈ 0.22 V) — and the bus
itself can be at 11.40 V, not 12.00 V. Real rails: **+11.03 V / −11.18 V**, asymmetric by
150 mV, with the OPA2197 reaching roughly +10.88 V. Margin at a 10 V output is **880 mV**,
not 1.45 V. Still fine; the pitch channel only needs +7 V. Worth correcting because the
+12 V side's drop *moves* with the light show (0.32 V at 200 mA to 0.36 V at 600 mA =
40 mV of rail movement), which is handled by ~100 dB of PSRR but should be stated rather
than discovered.

**10b. The `FB-IN` BOM line is ambiguous and under-specified.** NIT.
`FB-IN,module,Ferrite bead >=1A + 470uF at the load per branch,…,qty 4` covers three rails
(+12 V ×2 branches, −12 V, +5 V) and two component types in one row with a single quantity.
Split it: bead part number with its DCR and rated current, cap value and voltage per rail.
The 470 µF on the +5 V branch in particular is actively harmful (finding 6).

**10c. Ferrite bead DC-bias derating is a real effect but not the binding one here.** NIT.
ADR 0006 correctly warns that "a saturated bead does not degrade gracefully". Worth adding:
a 1 A-rated bead typically loses 30–50 % of its rated impedance at half rated current, so
the ≥1 A part is already partly derated at 485 mA. This does not matter, because — as
finding 3 shows — the bead's impedance at the frequencies with energy in them is its DCR
regardless. The bead earns its place at 10–100 MHz (SPI edges, buck harmonics, radiated
pickup), where it really does give 100–400 Ω. **The part choice is right; the stated reason
is not.**

**10d. The watchdog's supply rail is not specified anywhere.** NIT (but see finding 6).
`U-WATCHDOG,module,74HC123 …` has no rail assignment in the BOM or in ADR 0004. Note that a
74HC (not HCT) part on a 5 V rail has a V_IH of 3.5 V, so whatever drives its retrigger
input must be 5 V logic, not the 3.3 V-domain SPI — which is presumably why it sits after
the level shifter, but that is inferred, not written.

---

# Where the design is right

This matters as much as the findings, because several of these are non-obvious and a
future revision could undo them.

1. **Ferrite beads rather than series resistors at entry.** Correct, and the arithmetic is
   worse than ADR 0004 states: at my 485 mA rather than its 290 mA, a 2.2 Ω resistor drops
   **1.07 V and burns 0.52 W** in an 0805, and 10 Ω drops **4.85 V**. Decisively right.

2. **The self-correction that "a bead is a wire at 2 kHz".** Verified: a 1206 600 Ω @ 100 MHz
   bead has roughly 1 µH of low-frequency inductance, so ωL at 2 kHz = 2π × 2000 × 1 µH =
   **12.6 mΩ**, against a DCR of 50–100 mΩ. The bead *is* a resistor at that frequency. This
   is the kind of correction most projects never make.

3. **Bulk at the WS2815 feed points.** Right principle, and the 470 µF value is right for
   the now-verified 2 kHz refresh (478 µF by the formula, for a 50 mV budget at 300 mA).

4. **The admission that branching cannot isolate a shared upstream node.** Correct,
   precisely stated, and rare. (Finding 8 only disputes what follows from it.)

5. **12 V up the umbilical rather than 5 V.** Correct, and understated — see finding 9.

6. **`L-BUCK-IN`: a real inductor, not a bead.** Correct, and it works: at 330 kHz a 22 µH
   inductor is **45.6 Ω**, which against the buck's input capacitance leaves well under a
   milliamp of switching current reaching the umbilical node. The Middlebrook stability
   check passes with ~21 dB of margin (finding 7). Only the companion capacitor is missing.

7. **The LM317's divider satisfies the minimum-load requirement.** 1.25 V / 240 Ω =
   **5.21 mA**, against the LM317L's 2.5–3.5 mA minimum load. This is the single most
   common LM317 mistake and it was avoided. Related: no ADJ protection diode is needed at
   5.25 V with a 10 µF ADJ cap — TI's rule is that they become necessary above ~25 V or
   ~25 µF, and both are comfortably clear.

8. **The LM317's dropout and dissipation are non-issues, correctly.** Input 11.03 V, output
   5.25 V → **5.78 V** of differential against the ~1.7 V the LM317L needs. Dissipation
   5.78 V × ~12 mA = **69 mW** in a TO-92 at ~180 K/W = **12 K rise**. (ADR 0004's "135 mW"
   is conservative, which is the right direction to be wrong in.) Output noise with the
   10 µF ADJ bypass is ~40 µV RMS, which against a 76 µV DAC LSB and a supply the DAC's
   output is not referenced to is irrelevant. All correct.

9. **1 kΩ in series with each op-amp input driven by the DAC.** The right fix for the one
   cross-rail sequencing hazard the design did catch — and finding 6 is the same idea
   applied to the pins it did not.

10. **Keeping the 74AHCT125's switching current off the DAC's AVDD.** Right instinct, and
    worth keeping when the rail is re-derived.

11. **Gating the level shifter's `OE` from umbilical +12 V presence.** Correct for the
    stated reason (floating CMOS inputs, stray `CS` edges) and, unrecorded, it is also what
    makes the power-down sequencing safe for the three SPI lines — 6 ms of umbilical decay
    against 40 ms of DAC rail. Document that second purpose so nobody optimises it away.

12. **The 1N5817 is comfortably rated.** 485 mA against a 1 A part is 49 %; dissipation
    0.35 V × 0.485 A = **0.17 W** in a DO-41 at ~80 K/W = **14 K rise**; surge rating
    I_FSM 25 A covers rack-insertion inrush into the module's own bulk. No issue.

13. **Pulling `CS` high and `SCLK`/`MOSI` low at the module, and recognising
    "module alive, instrument off" as the normal state rather than a fault.** Correct, and
    the reasoning about crowbar current and stray `CS` edges is sound.

---

# What I would do first

In order, on the grounds of "cannot be fixed after the board is fabbed or the body is
bonded":

1. **Finding 3 — the ground topology.** It is free now, impossible later, it is the largest
   single error term reaching the pitch CV, and there is no decision record covering it.
2. **Finding 1 — replace the load switch.** The current part cannot be built with.
3. **Finding 6 — series resistors on the DAC's digital pins, a diode on +5 V.** 15 cents,
   and both the fault case and the power-down case are real.
4. **Finding 2 — delete the polyfuse.** One BOM line, and it removes a component that is
   actively fighting the design.
5. **Finding 5 — re-specify the DAC rail** before E7, since E7's exit criterion ("DAC
   saturation vs AVDD — record the actual saturation code at the actual rail") is the
   measurement that will expose it anyway.

Findings 4, 7, 8, 9 and 10 are all E6-bench work and can wait for the measurements the
roadmap already schedules — provided the load switch's limit is not frozen before the
current probe comes out.
