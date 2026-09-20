# B6 — Instrument power: independent analog design review

Scope: everything between the module's +12 V branch and the loads inside the
sealed oak body. Sources read: `README.md`, `ROADMAP.md`, all of
`docs/decisions/`, `docs/reference/`, `hardware/bom.csv`. `docs/review/` and
`docs/log/` deliberately not read.

**Datasheet figures.** Every number I attribute to a datasheet is marked
`[verified]` (I retrieved it this session, source named) or `[memory]` (working
from recollection, treat as a claim to check). Everything else is my own
arithmetic from the repository's own figures.

---

## Working numbers I derived before reading the project's own budget

### 0.1 Load table, built from the ADRs and the BOM

Conversion assumptions, stated so they can be attacked:

- R-78E5.0-1.0 efficiency **91 % at 5 V/1 A** `[verified — Recom R-78E-1.0
  datasheet via distributor summaries]`; I use **88 %** at the 300–600 mA
  operating point, which is where these modules typically sit.
- WS2815 quiescent **≤ 2.1 mA per pixel** `[verified — WS2815 specification,
  "quiescent current less than 2.1 mA"]`. 50 pixels → **105 mA**. This
  independently corroborates ADR 0005's "roughly 120 mA of strip quiescent
  draw", which I had expected to be high.
- WS2815 full white 50 px = 1.01 A at 12 V — ADR 0014's own figure, 20 mA/px,
  consistent with the commonly published 0.2–0.24 W/px `[memory]`.
- WS2812C-2020 matrix: 5 mA/channel, 15 mA/px, 960 mA full field — ADR 0014's
  figure `[memory, not independently checked]`.
- Display board (LilyGO T-Display-S3 AMOLED, ESP32-S3 + RM67162): **150 mA at
  5 V** with the radio off, **250 mA** average with WiFi active, ~400 mA burst
  peak. My estimate; no datasheet exists for a board-level figure.
- Real-time board ESP32-S3 core, radio off: **80 mA at 5 V**.
- Analog on +12 V: REF5050 Iq **0.8–1.0 mA typ, 1.2 mA max** `[verified — TI
  REF50xx datasheet]`, OPA2197 ~1 mA/ch × 2, MPXV4006DP 10 mA max (ADR 0003).
  Total **13 mA**.

| Load | Rail | (A) typical play | (B) clamp-legal worst, light on the matrix | (B′) clamp-legal worst, light on the strips |
|---|---|---|---|---|
| WS2815 quiescent (50 px) | 12 V direct | 105 mA | 105 mA | 105 mA |
| WS2815 commanded light | 12 V direct | 130 mA | 0 | 250 mA |
| 8×8 matrix quiescent | 5 V | 50 mA | 50 mA | 50 mA |
| 8×8 matrix commanded light | 5 V | 10 mA | 600 mA | 0 |
| Display board | 5 V | 150 mA | 250 mA | 250 mA |
| Real-time board core | 5 V | 80 mA | 80 mA | 80 mA |
| 74AHCT125 + all 3V3 loads | 5 V | 15 mA | 15 mA | 15 mA |
| **5 V rail subtotal** | | **305 mA** | **995 mA** | **395 mA** |
| 5 V subtotal reflected to 12 V @ 88 % | 12 V | 144 mA | 471 mA | 187 mA |
| REF5050 + OPA2197 + sensor | 12 V direct | 13 mA | 13 mA | 13 mA |
| **Total at the instrument, 12 V** | | **392 mA** | **589 mA** | **555 mA** |
| **Power dissipated inside the box** | | **4.6 W** | **6.9 W** | **6.5 W** |

The 3.3 V rail: 4 × 74LVC165A (static µA; dynamic `CV·f` ≈ 50 pF × 3.3 V ×
1 MHz ≈ 165 µA per driven node), MCP3202 ≈ 550 µA, I²C pull-ups ≈ 0.4 mA
average, termination. **~5 mA total.** ADR 0005's claim that this is
"comfortably inside the headroom of the real-time board's onboard regulator" is
correct by two orders of magnitude.

The written figures for comparison: ADR 0005's drop table uses **250 mA**;
ADR 0004 uses **~275 mA** and flags a review estimate of 410–430 mA. My typical
is **392 mA** and my clamp-legal worst is **589 mA**. ADR 0004 is right that
this is "the least trustworthy number in this document"; it is low by 1.4× on
typical and 2.1–2.4× on worst case.

### 0.2 What voltage actually arrives

Series elements from the rack bus to the instrument's 12 V node, at 589 mA:

| Element | Value | Drop at 589 mA |
|---|---|---|
| 1N5817 | Vf ≈ 0.38 V at 0.6 A `[memory]` | 0.38 V |
| Ferrite bead, 1206 ≥1 A | DCR ≈ 0.06 Ω | 0.035 V |
| Load switch | RDS(on) 85 mΩ `[verified, TPS2553 — but see finding 1]` | 0.050 V |
| 2 × RJ45 mated pairs, 2 conductors | ≈ 0.04 Ω loop | 0.024 V |
| 2 m Cat5e, 2 conductors (4 m of copper) | 0.38 Ω (24 AWG stranded) | 0.224 V |
| **PPTC, 1206L050 class** | **Rmin 0.75 Ω** `[memory]` | **0.44 V** |
| **Total** | | **1.15 V** |

At a 12.00 V bus the instrument node sits at **10.85 V**; at a realistic
11.8 V loaded bus, **10.65 V**. The single largest term is the polyfuse — larger
than four metres of cable.

### 0.3 My own thermal resistance estimate

Envelope 457 × 57 × 38 mm (ADR 0009). Face areas: aluminium top 0.0261 m²,
oak bottom 0.0261 m², acrylic sides 0.0347 m², ends 0.0043 m². Conductivities:
oak 0.16 W/m·K, PMMA 0.19 W/m·K, aluminium ~200 W/m·K. Film coefficient: for a
small still-air object at ΔT ≈ 15–20 K, natural convection h_c ≈ 3.5–6 W/m²K
plus radiation h_r = 4εσT³ = 4 × 0.9 × 5.67e-8 × 300³ = 5.5 W/m²K; take
h ≈ 9 W/m²K outside (R″ = 0.111) and 7.7 inside (R″ = 0.13, stagnant).

| Face | R″ in + wall + out (m²K/W) | R (K/W) | Conductance (W/K) |
|---|---|---|---|
| Aluminium top 2 mm | 0.13 + ~0 + 0.111 | 9.25 | 0.1081 |
| Oak bottom 8 mm | 0.13 + 0.050 + 0.111 | 11.2 | 0.0893 |
| Acrylic sides 2 × 4 mm | 0.13 + 0.021 + 0.111 | 7.55 | 0.1325 |
| Ends | 0.13 + 0.02 + 0.111 | 61 | 0.0164 |
| **Parallel total** | | **2.89 K/W** | **0.3463** |

**ADR 0014's "call it ~3 K/W" is a good estimate and I confirm it
independently.** With the player's hands covering the aluminium plate — 31 % of
the total conductance — it rises to **4.2 K/W**.

Interior rise: typical play 4.6 W × 2.9 = **13 K**; clamp-legal worst
6.9 W × 2.9 = **20 K**, or **29 K** with hands on the plate. At a 22 °C room
the interior reaches **42–51 °C**.

---

## Findings

### 1. The umbilical load switch is a 6.5 V part sitting on a 12 V rail

**SHOWSTOPPER.**

**Where.** `hardware/bom.csv`:

> `U-LOADSW,module,TPS2553DBV,TI,Current-limited load switch on the umbilical
> +12V feed,SOT-23-6,1,candidate,,0005,Adjustable limit set ~500mA`

and ADR 0005: *"The toggle drives a TPS2553-class current-limited load switch on
the umbilical +12 V feed"*; ADR 0004 repeats it in the power-entry diagram:
`──[ferrite]──[bulk]──[TPS2553]── umbilical +12V`.

**Why.** The TPS2553 is a USB port power switch. Its input range is
**2.5 V to 6.5 V** `[verified this session — TI TPS2553 product page and
datasheet summaries: "0.075-1.7A adjustable current limit, 2.5-6.5V, 85mΩ USB
power switch"]`. Absolute maximum on IN is 7 V `[memory]`. The design puts
12 V (and, at rack power-on, whatever the supply overshoots to) across it. It
will fail on first power-up, and its failure mode as a series FET is
unpredictable — short to the instrument is as likely as open.

ADR 0005 goes further and defends the choice on package grounds — *"The part is
SOT-23-6, which looks like a step away from the package policy in ADR 0013 and
is not"* — which is an argument about solderability applied to a part that
cannot be powered. Nothing in either ADR checks the input rating.

The whole protection architecture rests on this part: ADR 0014's entire
resolution of the polyfuse-runaway problem is *"The module's current-limited
load switch (ADR 0005) replaces a slow, self-heating, thermally-hysteretic
protection device with a fast fixed limit that does not run away."* That
sentence is currently backed by a part that does not exist at 12 V.

**Proposal.** Replace with a 12 V-capable eFuse in a hand-solderable package:
**TPS2592** (4.5–18 V, adjustable limit, adjustable dV/dt slew, SON — check
package policy), **TPS1663** (4.5–60 V, HTSSOP-20 — inside the accepted TSSOP
tier), or **TPS26600** (4.2–60 V). If leaded parts are mandatory, a discrete
P-FET high-side switch with a sense resistor and a comparator does the job and
is all through-hole. Whatever is chosen must have an adjustable current limit
**and** an adjustable output slew rate, because of finding 3.

**Confidence: very high** on the input rating; **certain** that the design as
written cannot work if that rating is right.

**Falsified by.** Reading TI SLVSAQ1 (TPS2552/TPS2553) section 6.1, "Absolute
Maximum Ratings", VIN row. If it reads anything above 12 V, this finding is
void. I expect 7 V.

---

### 2. The current limit and the polyfuse are both set below the steady-state load the design's own thermal clamp permits

**MAJOR.**

**Where.** `hardware/bom.csv`: `U-LOADSW ... Adjustable limit set ~500mA` and
`F-POLY,controller,PPTC 1206 500mA hold`. ADR 0005's drop table assumes
**250 mA**; ADR 0004 assumes **~320 mA** total on +12 V of which *"~275
instrument"*.

**Why.** From §0.1, a *clamp-compliant* state — 3 W of commanded light, exactly
what ADR 0014 authorises, with WiFi active as ADR 0013 promises is now possible
while playing — draws **555–589 mA** at the instrument. Even ordinary playing
draws **392 mA**.

The arithmetic that gets there in the worst case: 3 W of commanded matrix light
is 600 mA at 5 V, plus 50 mA of matrix quiescent, plus 250 mA of display board,
plus 80 mA of real-time board, plus 15 mA of shifter and 3.3 V loads = 995 mA
on the 5 V rail; at 88 % that is 5.65 W = 471 mA at 12 V; plus 105 mA of strip
quiescent and 13 mA of analog = **589 mA**.

Three things break at once:

- A 500 mA limit is **below the legal steady load**. The instrument enters
  current limit while doing exactly what the firmware permits.
- Worse, it cannot start. At switch-on the limiter must supply the steady load
  *and* charge 2 × 470–1000 µF of strip bulk plus the buck input. Constant-
  current charging of 1 mF to 11 V at the 500 mA limit takes
  t = CV/I = 1e-3 × 11 / 0.5 = **22 ms** — during which the steady load gets
  nothing, the buck never reaches its 8 V UVLO, and a limiter with foldback or
  a thermal-latch timer may simply latch off. This is the classic
  "won't start into a capacitive load" failure.
- The PPTC hold current is specified at 23 °C and derates. A typical PPTC hold
  derating is ×0.70–0.75 at 50 °C `[memory — check the "Thermal Derating"
  table in the Littelfuse 1206L datasheet]`, so a 500 mA part in a 45–50 °C
  interior (§0.3) holds **350–375 mA**. Typical playing at 392 mA already sits
  above hold. It will not trip cleanly; it will creep up its R–T curve,
  exactly the runaway ADR 0014 describes and believes it has escaped.

**Proposal.** Size the limiter from the load table, not from the stale figure:
**1.0 A limit with a 1.5 A, 10 ms trip characteristic**, which is 1.7× the
clamp-legal load and still 0.7× of what a shorted umbilical would otherwise
pull. Set the output slew rate so inrush is ~100 mA on top of the steady load:
dV/dt = I/C = 0.1/1e-3 = 100 V/s → a 110 ms ramp to 11 V. Check that against
the FET's SOA: 1 mF × 11 V²/2 = 60 mJ delivered over 110 ms at an average FET
drop of 5.5 V = 0.55 W average — trivial. Keep E6's inrush measurement, but use
it to *confirm* a designed number rather than to discover one.

**Confidence: high** on the load table being 1.4–2.4× the written figure;
**high** on the startup analysis.

**Falsified by.** E6 with a current probe: measure total umbilical current with
both strips and the matrix commanded to the 3 W clamp and the display board
associating to WiFi. If it stays under 450 mA, my display-board and matrix
estimates are wrong and the 500 mA setting survives. Also measure PPTC hold
current with the instrument soaked at 45 °C interior.

---

### 3. The polyfuse is the largest resistance in the 12 V path, dissipates a quarter of a watt inside the sealed box, and is redundant behind a module-side limiter

**MAJOR.**

**Where.** ADR 0005: *"Fuse the instrument at the umbilical entry... A polyfuse
is cheap insurance for a fault that takes down more than just this project"*,
and later: *"This is the same job as the instrument-end polyfuse, done faster
and self-resetting, and the two are complementary rather than redundant."*
BOM: `F-POLY ... PPTC 1206 500mA hold ... 1206 not 0603 - larger package is
easier to place and inspect`.

**Why.** A 1206-size, 500 mA-hold PPTC has **Rmin ≈ 0.75 Ω** and R1max
(post-reflow, pre-trip) up to **2.5 Ω** `[memory — 1206L050 class; check the
electrical characteristics table]`. Against my §0.2 budget:

- 0.75 Ω × 0.589 A = **0.44 V** of drop — more than the 0.38 V of the Schottky
  and the 0.22 V of four metres of Cat5 combined.
- 0.75 Ω × 0.589² = **0.26 W dissipated inside a sealed insulating box**, in a
  3.2 × 1.6 mm package. Its own self-heating is the mechanism by which it
  creeps toward trip.
- It is the dominant source impedance for the LED animation current. A step
  from dark to clamp-legal strips is 250 mA; through 1.15 Ω of total path
  resistance that is **0.29 V of rail movement at animation rate**, versus
  0.10 V if the polyfuse were deleted.

And it cannot do its job. Once a fast 1.0 A limiter sits upstream at the module,
the polyfuse can never see the ≥1 A it needs to trip: the module clamps first,
every time, on every fault the polyfuse exists for. It is not complementary; it
is dead weight in series with the only power conductor.

**Proposal.** **Delete `F-POLY`.** The module-side electronic limiter is
strictly faster, has no thermal memory, has no series resistance worth
measuring, and is on the accessible side of a body that cannot be reopened. If
a belt-and-braces device is wanted inside the instrument, use a plain fast-blow
chip fuse at 1.5 A — zero-ish resistance, no derating drama — accepting that
blowing it ends the instrument's life, which is exactly the argument for not
fitting one.

**Confidence: high.** The redundancy argument does not depend on the resistance
figure; the resistance figure is what makes deletion an improvement rather than
a wash.

**Falsified by.** Measure the actual part's DC resistance at 25 °C and at
50 °C with a 4-wire meter at 500 mA. If it is under 0.2 Ω, the drop and
dissipation arguments weaken (the redundancy argument stands regardless).

---

### 4. The buck's input LC is specified with an inductor and no capacitor, and as drawn it is an undamped filter feeding a negative resistance

**MAJOR.**

**Where.** BOM: `L-BUCK-IN,controller,"10-47uH power inductor, >=1A",,LC between
the umbilical node and the buck input ... "A real inductor, not a bead. This is
the part the bead was wrongly credited for"`. ADR 0004 repeats it: *"A real LC
between the umbilical node and the buck input — 10–47 µH of inductance, not a
bead."*

**Why.** There is no capacitor in the BOM for the buck input. Searching
`hardware/bom.csv` for capacitors returns `C-BULK-DISP` (at the display board),
`C-STRIP-BULK` (at the strips), `C-DECOUPLE-165`, `C-AA-ADC`, and module-side
parts. **The "LC" is currently an L.** An inductor alone in series with a
switching converter's input is worse than nothing: it turns the converter's
pulsed input current into voltage spikes at the converter pins.

Recom specifies a **10 µF, 50 V MLCC input capacitor** for the R-78E family
`[verified — R-78E-1.0 datasheet recommended external components]`. Add that
and the filter is real but marginal. Take L = 22 µH, C = 10 µF ceramic,
inductor DCR 0.2 Ω:

- f₀ = 1/(2π√LC) = 1/(2π√(2.2e-10)) = **10.7 kHz**
- Z₀ = √(L/C) = √2.2 = **1.48 Ω**
- Q = Z₀/R_series = 1.48/0.2 = **7.4**
- Filter output impedance at resonance = Q·Z₀ = **11 Ω**

A buck is a constant-power load, so its incremental input resistance is
negative: R_in = −V_in²/P_in = −10.85²/5.65 = **−20.8 Ω** at the clamp-legal
operating point. Middlebrook's criterion wants |Z_out,filter| ≪ |Z_in,conv|,
conventionally by 6–10×. The ratio here is **1.9**. The filter fails the
criterion outright, and its 10.7 kHz resonance sits in the middle of the
control-loop crossover region of a 330 kHz converter — the textbook recipe for
subharmonic oscillation, audible whine, and a 5 V rail that rings when the LED
load steps.

**Proposal.** Add a damping branch at the buck input: **10 µF X7R ceramic in
parallel with 100 µF/25 V aluminium electrolytic** whose ESR (0.5–1 Ω) sets the
damping. Z_out,peak then falls to roughly the damping ESR, ~0.7 Ω, and the
criterion passes by 30×. Cost: one electrolytic. Add the BOM lines explicitly —
`C-BUCK-IN-HF` and `C-BUCK-IN-DAMP` — rather than leaving "LC" to be
interpreted at build time. Also check L-BUCK-IN's DCR drop: 0.2 Ω × 0.471 A =
94 mV and 44 mW, acceptable, but specify DCR ≤ 0.3 Ω or the drop starts
mattering against finding 7.

**Confidence: certain** that the BOM has no input capacitor; **high** on the
damping analysis, which is standard input-filter design.

**Falsified by.** Build the buck with the specified inductor and the Recom
10 µF alone, step the 5 V load 100 → 600 mA, and scope the buck's input and
output. Absence of ringing at ~10 kHz and no subharmonic content in the output
spectrum would falsify it — but the damping capacitor costs less than the
measurement, so fit it anyway.

---

### 5. The reference buffer drives the sensor's supply decoupling capacitor directly, which is outside the OPA2197's capacitive-load rating

**MAJOR.**

**Where.** ADR 0003:

> ```
> umbilical +12V ──[REF5050 5.000V]──[OPA2197 ½ buffer]──┬── MPXV4006DP VS
>                                                        └── (10 mA available)
> ```
>
> *"Buffered by half an OPA2197 running on +12 V. The reference alone can source
> 10 mA against the sensor's ~10 mA, which is inside its rating and has no
> margin; the buffer removes the question and costs nothing"*

and BOM: `C-DECOUPLE,module,100nF ceramic,,HF decoupling at every IC ... One per
supply pin, close to the pin`.

**Why.** The buffer is a unity-gain follower whose load is a supply pin, and a
supply pin gets a decoupling capacitor — 100 nF by the project's own rule, and
the MPXV4006 family's own datasheet recommends a 1 µF supply bypass `[memory]`.
The OPA197/OPA2197 drives **up to 1 nF of pure capacitive load in unity gain**;
beyond that TI's datasheet calls for a **10–20 Ω R_ISO** in series
`[verified this session — TI OPA2197 datasheet, capacitive-load-drive
discussion]`. 100 nF is 100× that limit, and 1 µF is 1000×.

The consequence is not a burst of smoke, it is a buffer that rings or
oscillates at a few hundred kHz on a supply that is *the breath sensor's scale
factor*. The MPXV4006DP is ratiometric, so any oscillation on VS multiplies
straight into the breath reading and into the analog CV that goes down the
umbilical. This is the single node in the instrument where the project has spent
the most effort on precision — a 3 ppm/°C reference, buffered, on its own rail —
and it has an unstable output stage in front of it.

The naive fix conflicts with the ratiometric requirement: a 10 Ω R_ISO outside
the feedback loop drops 10 Ω × 10 mA = **100 mV**, i.e. **2 % of a 5.000 V
reference**, which throws away everything the REF5050 bought.

**Proposal.** The standard composite: **R_ISO = 10 Ω in the loop, with feedback
taken from the sensor's VS pin (Kelvin), plus a 100 pF feedback capacitor from
the buffer output to its inverting input** to keep the loop stable at high
frequency. DC accuracy is then set at the sensor pin, not at the op-amp pin, so
the 100 mV is regulated out. Draw it on the schematic explicitly; it is the kind
of thing that gets "simplified" during layout. Verify on the bench at E2 with a
step on the reference and a scope on VS.

**Confidence: high** on the OPA2197 1 nF figure (verified); **high** that a
supply pin will get ≥100 nF; **medium** that the result would actually
oscillate rather than merely ring — an unloaded follower into 100 nF with a
phase margin already degraded is usually ringing, sometimes oscillation.

**Falsified by.** Breadboard the REF5050 → OPA2197 → 100 nF → MPXV4006DP chain,
inject a small square wave into the buffer's non-inverting input through the
reference's output, and look at VS on a scope with a 20 MHz bandwidth limit off.
Clean settling with <5 % overshoot falsifies it.

---

### 6. Breath CV survives a brown-out that kills everything the module's watchdog can reach

**MAJOR.**

**Where.** ADR 0004: *"A stuck CV is worse than a dead one... **Assert `CLR` at
the module when no valid frame has arrived for N milliseconds.**... This also
gives umbilical disconnection the same behaviour as a hang, which is correct:
both mean 'the instrument is no longer telling me anything.'"* ADR 0005:
*"**Pull down the module's breath receive input**, so that an instrument which
is switched off — or unplugged — presents 0 V rather than a floating buffer
output."* BOM: `R-PD-BREATH,module,100k`.

**Why.** The watchdog reaches the DAC, and the DAC carries pitch and the four
mod channels. **Breath is analog end to end** (ADR 0003) and does not pass
through the DAC at all. So the watchdog covers five of six outputs.

Now consider the failure mode the project itself predicts. ADR 0004 calls the
cable *"a consumable"* and says *"Replace the lead at the first sign of
intermittency"* — i.e. the expected failure is rising contact or conductor
resistance, which is a **slow sag**, not a clean disconnect. Trace what happens
as the instrument's 12 V node falls:

- **8.0 V** — the R-78E5.0-1.0 hits its minimum input voltage and stops
  `[verified — R-78E-1.0 input range is 8–28 V]`. Both MCUs die. SPI stops.
  The module's watchdog fires and parks pitch and mods.
- **7.2 V** — the REF5050 is still in regulation (it needs Vout + ~0.2 V of
  dropout; its specified VIN range starts at 5.2 V for a 5 V output)
  `[verified — TI REF50xx: "minimum input voltage is 5.2 V"]`. The OPA2197
  runs happily on 7 V. **The breath buffer is still driving a perfectly valid
  0.2–4.7 V onto the umbilical, referenced to a 5.000 V reference that has not
  moved.**

So across a **1.2 V window of rail sag** — and for however long the rail dwells
there, which for a degrading cable is indefinitely — the rack sees: pitch
parked, mods parked, and **breath live and responding to the player's
diaphragm**. Whether that is silent or a screaming drone is a property of the
patch, not of the instrument. It is exactly the failure ADR 0004 designed the
watchdog to prevent, on the one channel the watchdog cannot see.

The 100 k pulldown does not help. It only works into a high-impedance source
(instrument unplugged). Against a live OPA2197 output through a 1 kΩ series
resistor, a 100 k pulldown attenuates by 1 %.

**Proposal.** Give the watchdog authority over breath too. Cheapest version:
one gate of a 74HC4066 (or a small N-FET) shunting BREATH to AGND at the module
end, driven by the same 74HC123 output that asserts DAC `CLR`. That makes "no
valid frame" mean the same thing on all six channels, and it also covers the
MCU-hang case, where today breath keeps tracking the player while pitch is
parked subsonic. Second, add a UVLO supervisor in the instrument that pulls the
buffer's input to the sensor's zero when the 12 V node falls below ~9.5 V — but
the module-side fix is strictly better because it is independent of the thing
that failed, which is ADR 0004's own stated principle.

**Confidence: high.** The 8 V buck UVLO and the ~5.2 V reference dropout are
both verified datasheet figures, and the gap between them is the whole finding.

**Falsified by.** On the bench, feed the instrument from a variable supply and
sweep it 12 V → 6 V while blowing into the mouthpiece, with a meter on the
module's BREATH jack. If breath collapses to 0 V at or above the point where
the MCUs reset, this is void. I expect breath to remain valid for about a volt
below the MCU reset point.

---

### 7. The single shared buck contradicts two other documents and, at the clamp-legal load, runs at 99.5 % of rating

**MAJOR.**

**Where.** ADR 0005's power tree:

> ```
>                  ├── 12V→5V buck ──┬── display board  5V pin
>                  │                 ├── real-time board 5V pin
>                  │                 └── LED data level shifter
> ```

against ADR 0013: *"give **each board its own regulator** from the umbilical
+12V, with local bulk capacitance on the display board, so WiFi bursts are
absorbed locally rather than reaching the analog section"*, and
`docs/reference/latency-budget.md`: *"**Each board gets its own regulator** and
local bulk capacitance for that reason."*

**Why.** Two problems, one architectural and one numerical.

*Architectural.* ADR 0004 makes precisely the right argument about the module's
rails and then the instrument does the opposite: *"'Keeping the module out of
the rack' cannot work by branching, because both branches are common upstream at
the bus header. **Filtering downstream of a shared node does not isolate that
node.**"* With one buck feeding both boards, the display board's WiFi burst and
the real-time board's supply share a node — the buck's output — and
`C-BULK-DISP` is downstream of it. It reduces the *loop area* of the burst, but
the burst still modulates the shared 5 V rail by the burst current times the
buck's output impedance plus the loom's. That rail is the input to the
real-time board's 3.3 V LDO, which is the **MCP3202's reference** (BOM:
`U-ADC ... VDD-referenced so no separate ref chip`). ADR 0013 identified this
and specified two regulators; ADR 0005 quietly reduced it to one and did not
argue the reduction.

*Numerical.* From §0.1, state (B) puts **995 mA** on a **1 A** part. That is not
a margin, it is a coincidence. ADR 0014 already saw half of this — *"a full-field
matrix would ask for about 1.36 A from a 1 A part"* — and concluded the firmware
clamp handles it. But the clamp is set in *LED watts*, and 3 W of LED watts on
the matrix is 600 mA on this rail. The clamp does not know the difference
between 3 W spent on the strips (which never touch the buck) and 3 W spent on
the matrix (which is 60 % of the buck's rating). **The clamp is denominated in
the wrong quantity to protect the converter.**

The good news, which is worth stating: if the R-78E does hit its limit it enters
continuous short-circuit protection with automatic recovery `[verified — R-78E
datasheet: "Short Circuit Protection (SCP) with continuous, automatic
recovery"]`, and because the matrix is *on* the collapsing rail, the load falls,
the rail recovers, the MCU boots and blanks the matrix. ADR 0014's
blank-at-boot rule genuinely closes this loop. It is ugly but it is not a latch.

**Proposal.** Two options, both cheap:

1. **Two R-78E5.0-1.0 modules**, as ADR 0013 and the latency budget already
   specify — one for the display board, one for the real-time board and the
   level shifter. They are 3-pin SIP parts on 7805 footprints; adding a second
   costs a footprint and a few dollars, and it restores the isolation ADR 0013
   claims as a benefit of the two-MCU split.
2. **Denominate the clamp in rail current, not LED watts.** Track commanded
   matrix current separately and cap it at, say, 400 mA at 5 V, with the strips
   getting the remainder of the thermal budget. This is a firmware change and
   costs nothing, and it should be done *as well as* (1).

Either way, reconcile ADR 0005 with ADR 0013 and the latency budget, because
three documents currently describe two different power trees.

**Confidence: certain** on the contradiction; **high** on the 995 mA figure,
which depends mainly on my display-board estimate.

**Falsified by.** E1's idle-current measurement, extended: measure each dev
board's 5 V current at idle, with the display at full brightness, and with WiFi
associating and transmitting. If the two boards together stay under 300 mA with
WiFi active, the headroom argument softens (the isolation argument does not).

---

### 8. The anti-alias filter is at 120 Hz, not the 600 Hz claimed, and the buck runs at 330 kHz, not 496 kHz

**MAJOR** (for the latency consequence; the filtering itself is over-adequate).

**Where.** `hardware/bom.csv`:

> `C-AA-ADC,controller,220nF X7R,,Anti-alias cap at the MCP3202 input pin ...
> "~600Hz corner, 58dB at 500kHz. Without it a 496kHz buck folds to 100Hz,
> straight into the breath band. Also the sample-cap reservoir"`
>
> `R-ADCDIV,controller,10k / 15k 1% metal film,,0.6x divider from the breath
> buffer to the ADC`

**Why.** Three arithmetic errors compound.

*The corner.* The 0.6× divider requires a 10 k upper leg and a 15 k lower leg
(15/(10+15) = 0.6). The source impedance the cap sees is the Thévenin
resistance, **10 k ∥ 15 k = 6.0 kΩ**, not 10 k and not 1 k:

  f_c = 1/(2π · 6000 · 220 × 10⁻⁹) = 1/(2π · 1.32 × 10⁻³) = **120.6 Hz**

The stated 600 Hz needs 44 nF, not 220 nF. The two stated numbers — "600 Hz" and
"58 dB at 500 kHz" — are self-consistent with each other (500 000/600 = 833 =
58.4 dB), so the error is in the component value, not the reasoning.

*The switching frequency.* The R-78E5.0-1.0 switches at **330 kHz** `[verified —
R-78E-1.0 datasheet]`, not 496 kHz. The "folds to 100 Hz" figure is also wrong
in kind: at a 4.000 kHz sample rate, 330 kHz aliases to 330 000 − 82 × 4000 =
**2000 Hz**, exactly Nyquist, and it walks across the entire 0–2 kHz band as the
converter's frequency drifts with line, load and temperature. There is no fixed
alias frequency to design against, which is the real argument for filtering
hard — a better argument than the one written down.

*The consequence, which is the finding.* A 120 Hz single pole has a time
constant of **1/(2π × 120.6) = 1.32 ms**. That term appears nowhere in
`docs/reference/latency-budget.md`. The digital-copy table reads:

> | Sampling period | 0–250 µs |
> | SAR ADC conversion | 50–200 µs |
> | SPI to MCU + firmware | < 20 µs |
> | ... | |
> | **Total** | **~2.6–2.9 ms** |

Add 1.32 ms and the real total is **3.9–4.2 ms against a 5 ms target**. Still
passes, but the margin drops from ~2× to ~1.2×, and the missing term is larger
than every other digital term combined. It also lands on the note-gate decision,
which ADR 0003 identifies as the latency-critical path: *"the threshold that
starts a note is on the latency-critical path."*

**Proposal.** **Change `C-AA-ADC` to 47 nF.** f_c = 1/(2π · 6000 · 47n) =
**565 Hz**, matching the intended 600 Hz, τ = 282 µs, and attenuation at
330 kHz = 330 000/565 = 584 = **55 dB**, which is ample. The cap is still
2350× the MCP3202's ~20 pF sample capacitor, so its reservoir job is unaffected.
Then add the filter's group delay to the latency budget as an explicit line.

**Confidence: certain** on the RC arithmetic; **verified** on 330 kHz.

**Falsified by.** Build the divider and cap, inject a swept sine at the buffer
output, and find the −3 dB point at the ADC pin. If it is near 600 Hz my reading
of which leg is which is wrong — check the divider orientation first.

---

### 9. The thermal clamp governs 3 W of a 7 W budget, and the budget is stated as an increment rather than a total

**MAJOR.**

**Where.** ADR 0014:

> | Lighting state | Power | Interior rise it would add |
> | Realistic use — single hue tracking breath | ~1.5 W | ~4 K |
> ...
> *"3 W is twice realistic use and about a sixth of the pathological case, and
> it costs roughly 9 K of interior rise — inside what the design already
> tolerates."*

and *"The existing electronics dissipate roughly 5 W for an interior rise of
10–20 K, so call it ~3 K per watt."*

**Why.** My independent thermal model (§0.3) gives **2.89 K/W**, which confirms
the 3 K/W figure — so I am not disputing the coefficient. I am disputing what it
is multiplied by.

Decompose my clamp-legal worst case (6.9 W total) into what firmware can and
cannot control:

| | W |
|---|---|
| **Clamped** — commanded LED light | **3.0** |
| WS2815 quiescent, 50 px × 2.1 mA × 12 V | 1.26 |
| Matrix driver quiescent (ADR 0007's own estimate) | 0.28 |
| Display board at 250 mA/5 V, reflected through the buck | 1.42 |
| Real-time board core | 0.45 |
| Level shifter + 3.3 V loads | 0.09 |
| REF5050 + OPA2197 + sensor | 0.16 |
| Buck conversion loss at 88 % | 0.68 |
| PPTC self-dissipation (finding 3) | 0.26 |
| **Unclamped subtotal** | **4.6** |

**The firmware clamp bounds 43 % of the thermal load.** ADR 0014's own numbers
say as much — *"The existing electronics dissipate roughly 5 W"* — but then the
lighting increment is compared against the tolerance rather than added to the
baseline. By ADR 0014's own 3 K/W the total is 8 W → **24 K**, not the 9 K
quoted. By mine it is 6.9 W → **20 K**, or **29 K** with the player's hands
covering 31 % of the escape path. At a 22 °C room the interior reaches
**42–51 °C**.

That is not an emergency — it is well short of the "too hot to hold" 53 K case —
but three things follow that are not currently written down:

- **The aluminium plate is fine and the acrylic is the hot spot.** The plate is
  isothermal; at ~2.2 W through it and an interior film resistance of
  0.13/0.026 = 5 K/W, the plate sits ~11 K below interior, so **~35 °C** under
  the hands. Comfortable. The acrylic side channels, which contain the strips
  *and* their local dissipation, are the hottest surfaces.
- **The electrolytics are the only wear-out parts in a body that cannot be
  reopened, and their grade is unspecified.** BOM: `C-STRIP-BULK,"470-1000uF
  electrolytic, 16V"` — no temperature rating, no hours. An 85 °C/1000 h part at
  a 50 °C interior gives 1000 × 2^((85−50)/10) = **11 300 h ≈ 1.3 years** of
  continuous operation. A 105 °C/2000 h part gives 2000 × 2^5.5 = **90 000 h**.
  Same footprint, same price bracket.
- **16 V on a 12 V rail with no overvoltage clamp** (finding 11) is 75 %
  derating with no transient margin. 25 V costs nothing in a radial can.

**Proposal.** (a) Restate the budget as a **total instrument dissipation target**
— I suggest 6 W, which lands at 17 K by my model — and let the lighting clamp be
whatever is left after the fixed loads, computed rather than assumed. (b) Specify
**105 °C, ≥2000 h, low-ESR, 25 V** for every electrolytic in the body. (c) At
M8, instrument the soak with three thermocouples, not one: breath sensor,
R-78E5.0 case, and an acrylic channel next to a strip.

**Confidence: high** on the decomposition; **medium-high** on 2.89 K/W — my
film coefficient is an engineering estimate and could be off by ±30 %, which
moves the rise by ±5 K.

**Falsified by.** M8's soak. Run at exactly the 3 W clamp with WiFi active,
measure total umbilical power with a meter and interior air temperature at the
sensor. If the measured K/W is under 2 or the total power is under 5 W, I am
over-stating it.

---

### 10. A VDD-referenced ADC on a dev-board LDO on the LED-modulated 5 V rail is where the gate-chatter budget is actually spent

**MINOR** (but it is the mechanism behind a MAJOR symptom).

**Where.** BOM: `U-ADC,MCP3202-CI/SN ... VDD-referenced so no separate ref
chip`. ADR 0005: *"3.3 V does not need its own converter... all comfortably
inside the headroom of the real-time board's onboard regulator."* ADR 0014
identifies the symptom: *"Through the ADC it is positive feedback, via reference
depression from shared-ground LED current... the symptom is not gain error, it
is note-gate chatter."*

**Why.** ADR 0014 diagnoses this correctly and prescribes two firmware fixes
(hysteresis sized from measurement; drive the animation from the post-gate
value). Both are right. But the *hardware* reason it is a problem is worth
stating with a number, because it decides whether the firmware fixes are enough.

The 8×8 matrix is physically on the real-time board. Its current — up to 600 mA
at the clamp-legal worst — must flow through that board's 5 V and GND header
pins and the carrier's ground pour, and it is PWM'd. The MCP3202 sits on the
same carrier, referenced to the same pour, and its reference *is* its VDD, taken
from the same board's 3.3 V LDO. If the ADC's ground reference and the matrix's
return share even **20 mΩ** of pour and header contact:

  0.6 A × 0.020 Ω = **12 mV**, against 3.3 V/4096 = 0.806 mV/LSB → **15 LSB**

modulated at the matrix's PWM and animation rates. Against a full-scale breath
span of roughly 2.82 V (4.7 V × 0.6) = 3500 counts, that is 0.43 % of full
scale of brightness-correlated noise sitting directly on the gate threshold.
This is a path you cannot Kelvin away, because the matrix is on the same board
as the LDO.

It also quietly undoes the precision argument: ADR 0003 buys a REF5050 at
3 ppm/°C so the sensor's scale factor is stable, and the digital copy of that
signal is then divided by an uncharacterised dev-board LDO inside a box that
warms 20–29 K.

**Proposal.** Give the MCP3202 its own 3.3 V supply on the carrier — a small
LDO off the buck's 5 V, referenced to the analog ground at the sensor star point
(ADR 0003 already defines that star point). ~5 mA of load, a SOT-23-5 or TO-92
part, two capacitors. That decouples the ADC's reference from the matrix's
return path entirely and makes the digital breath copy as stable as the analog
one. It costs one part and directly contradicts ADR 0005's "3.3 V does not need
its own converter" — which is true on *current* and false on *reference
integrity*.

**Confidence: medium-high.** The 20 mΩ is an estimate; the mechanism is certain.

**Falsified by.** E4's existing measurement, extended: with the sensor at a
fixed pressure, log ADC counts while cycling the matrix between blank and the
clamp-legal full field. Under 3 LSB of correlated step and this is a non-issue
and the firmware fixes suffice.

---

### 11. One ESD array cannot protect a 12 V conductor, 3.3 V logic and a 0–5 V analog line, and +12 V has no overvoltage clamp at all

**MINOR.**

**Where.** BOM:

> `U-TVS-UMB,controller,SP3012-06UTG or similar array,multiple,TVS array on
> umbilical entry,SOT-23-6 (0.95mm pitch),1,candidate,,0004,"Multi-line array
> beats discretes for placement. 8 conductors from outside"`

**Why.** The note says "8 conductors" and the part has six channels. More
importantly, a TVS array has **one working voltage**, and the eight conductors
span three domains: +12 V/PWR_GND, 3.3 V SPI (SCLK, MOSI, CS, DIG_GND), and
BREATH/AGND at 0–5 V. A ~5 V array `[SP3012 family V_RWM — memory, not
verified]` on the +12 V conductor is a short circuit across the supply the first
time the instrument is powered. A 14 V array on the SPI lines lets 3.3 V logic
see 14 V before clamping, which protects nothing.

Netting it out: only four conductors actually need channels — SCLK, MOSI, CS
(3.3 V) and BREATH (0–5 V); the three grounds do not. A six-channel 5 V array
covers all four comfortably. **The +12 V rail needs its own part, and does not
have one.** Today nothing inside the instrument clamps the 12 V node, and the
WS2815's supply range tops out around 13.5 V `[memory — WS2815 spec:
+9.5 to +13.5 V]`, with the strip bulk caps rated 16 V (finding 9).

**Proposal.** Keep the array for the four signal conductors, at a working
voltage of 5–5.5 V. Add **one SMBJ13A** (V_RWM 13 V, V_BR 14.4 V min, 600 W)
from +12 V to PWR_GND at the umbilical entry — one part, DO-214, and it also
bounds what a rack-supply transient or a hot-plug LC ring can do to the strips
and the caps. Fit it *downstream* of nothing; put it right at the connector.

**Confidence: high** on the architectural point (one array, three voltage
domains); **medium** on the specific SP3012 working voltage.

**Falsified by.** Reading the SP3012-06UTG datasheet's V_RWM. If it happens to
be a 12 V-rated array, the +12 V line is covered and only the SPI-line clamping
argument remains.

---

### 12. The cable gauge is unspecified, and the drop arithmetic assumes solid-core resistivity for a cable the design requires to be stranded

**MINOR.**

**Where.** ADR 0005: *"Over 2 m of 24 AWG, round trip ~0.34 Ω"* and the table
deriving 84 mV / 0.7 % error. BOM: `CABLE-UMB,"Cat5e STP patch lead, STRANDED,
~2m" ... "STRANDED not solid-core: solid core work-hardens and fractures under
constant flexing"`.

**Why.** 0.34 Ω for 4 m implies 0.085 Ω/m, which is the resistivity of
**solid** 24 AWG copper (0.0842 Ω/m). Stranded conductors of the same AWG have
5–20 % higher DC resistance because of the lay and the reduced effective copper
area — call it 0.095 Ω/m, **0.38 Ω** for the round trip.

The bigger exposure is that "Cat5e patch lead" does not mean 24 AWG. Slim and
"snagless" patch leads are routinely **26 AWG** (0.134 Ω/m → **0.54 Ω**) and
increasingly **28 AWG** (0.213 Ω/m → **0.85 Ω**). At my clamp-legal 589 mA:

| Conductor | Round-trip R | Drop at 589 mA |
|---|---|---|
| 24 AWG solid (the ADR's assumption) | 0.337 Ω | 0.198 V |
| 24 AWG stranded | 0.38 Ω | 0.224 V |
| 26 AWG stranded | 0.54 Ω | 0.318 V |
| 28 AWG stranded | 0.85 Ω | 0.501 V |

A 28 AWG lead costs 0.30 V more than assumed. On its own that is survivable —
the buck's 8 V floor is 2.6 V away — but it stacks with finding 3's 0.44 V of
polyfuse and finding 2's load. And the project has explicitly designated this
part a consumable to be replaced from a drawer, which is exactly the situation
in which a 28 AWG lead gets fitted by accident.

**Proposal.** Write **"24 AWG stranded, 7/32, shielded"** into the BOM line and
into the build notes, and make "check the AWG printed on the jacket" part of the
cable-replacement procedure. Also: the two spare conductors are currently idle
(MISO deleted in ADR 0004, one reserved). **Parallel them onto +12 V and
PWR_GND.** That halves the power-pair resistance to 0.19 Ω at no cost, and the
T568B pair mapping still keeps BREATH/AGND on pins 1,2 adjacent only to power.
It is free margin in the one part of the system that is guaranteed to degrade.

**Confidence: high** on the resistivity figures; **high** on 26/28 AWG patch
leads being common.

**Falsified by.** Four-wire-measure the actual lead end to end. If it comes in
under 0.35 Ω, it is a 24 AWG lead and only the specification gap remains.

---

### 13. No bulk capacitance is specified at the buck's output, or at the largest PWM load on the 5 V rail

**MINOR.**

**Where.** BOM: `C-BULK-DISP,controller,TBD,,Local bulk capacitance at the
display board,1206 / electrolytic THT,1,open` — value open, package ambiguous.
Nothing at the buck output; nothing at the real-time board's 5 V pin.

**Why.** ADR 0014 states the principle correctly — *"Bulk capacitance belongs
where the current swings"* — and applies it to the WS2815 strips and nowhere
else. But the 8×8 matrix is **the largest PWM load on the 5 V rail** at up to
600 mA, and it has no local bulk specified. Neither does the buck's own output
(Recom recommends 22 µF `[memory — the R-78E datasheet's recommended external
components table lists an output MLCC; I verified only the 10 µF input figure]`).

Sizing `C-BULK-DISP`: an ESP32-S3 WiFi TX burst is ~350 mA `[memory]` for
1–2 ms. The R-78E's loop responds in roughly 1/(2π × 20 kHz) ≈ 8 µs, but the
loom between the buck and the display board — ~400 mm if the display is at the
top and the carrier at the bottom, per ADR 0013's zone table — contributes
~0.7 µH. The burst's rising edge, ~350 mA in ~1 µs, gives
V = L·di/dt = 0.7 µH × 0.35 A/µs = **245 mV** of spike at the board unless it is
absorbed locally. For the slower settling, C = I·Δt/ΔV = 0.35 × 50 µs / 0.1 V =
**175 µF**.

**Proposal.** `C-BULK-DISP` = **220 µF, 10 V, 105 °C low-ESR electrolytic in
parallel with 10 µF X7R**, not "1206 / electrolytic TBD" — a 1206 ceramic alone
is 10–22 µF and is an order of magnitude short. Add **100 µF + 10 µF at the
real-time board's 5 V header pins** for the matrix, and **22 µF X7R at the buck
output**. Four parts, all in the accepted package tiers.

**Confidence: high** on the sizing arithmetic; **medium** on the 0.7 µH loom
inductance, which depends on how the pair is routed (twisting the 5 V and its
return halves it).

**Falsified by.** Scope the display board's 5 V pin during WiFi association
with only the board's own onboard capacitance fitted. Under 50 mV of excursion
falsifies the need for 220 µF.

---

### 14. The "~2.5 mA into the ADC ESD clamp" figure is not traceable to the specified parts

**NIT.**

**Where.** BOM: `R-ADCDIV ... ">=10k upper leg: 5V-before-3V3 sequencing
otherwise pushes ~2.5mA into the ADC ESD clamp on every power-up"`.

**Why.** The sequencing concern is real and correctly identified: the REF5050
and OPA2197 run from raw +12 V and are live from the first millisecond, while
the MCP3202's VDD waits for the buck's UVLO, its soft-start, the dev board's
LDO, and ESP32-S3 boot — hundreds of milliseconds. But the arithmetic does not
reach 2.5 mA with the specified parts. Worst case is someone blowing at
power-on, sensor output at 4.7 V, ADC VDD at 0 V, clamp at ~0.7 V:

  I = (4.7 − 0.7)/10 kΩ = **400 µA**

against the MCP3202's ~±2 mA clamp rating. 2.5 mA would require a ~1.6 kΩ upper
leg. The conclusion — that ≥10 k is sufficient — is right; the number supporting
it is 6× high and appears to come from an earlier divider. Worth correcting
because a wrong number invites someone to later "optimise" the divider down and
discover the margin was 6× smaller than the note implied.

**Confidence: high.** **Falsified by.** Measuring the clamp current with the
ADC held in reset and the buffer driven to 4.7 V.

---

## Where the design is right

These are not filler; several are choices I expected to have to argue against
and did not.

1. **12 V up the cable rather than 5 V.** ADR 0005's drop table is arithmetically
   correct for the current it assumes (0.25 A × 0.337 Ω = 84 mV), and the
   conclusion survives at my 2.4×-higher current: 0.589 A × 0.38 Ω = 0.224 V,
   1.9 % — still an order of magnitude better than 5 V distribution would be
   (which at 1.4 A would drop 0.53 V, 11 %). The ratiometric-sensor argument for
   why that matters is exactly right.

2. **The sensor's supply is derived from +12 V, not from the buck.** This is the
   single best decision in the power design. It keeps the one ratiometric,
   precision-critical rail off the switching converter and off the rail the LEDs
   modulate. Dissipation checks out: the OPA2197 buffer drops (12 − 5) V × 10 mA
   = **70 mW** in a SOIC-8 at θJA ≈ 125 K/W `[memory]` = 9 K rise. Fine.
   (Finding 5 is about the *stability* of that buffer, not the topology.)

3. **Bulk at the load, not at entry.** ADR 0004's correction — *"470–1000 µF at
   each WS2815 feed point, where the current actually swings, rather than at the
   module end of a 14-inch cable"* — is right, and my transient arithmetic
   confirms it works. Per strip, 25 px, full-white peak 0.5 A, 125 µs on-time at
   a 25 % duty at 2 kHz: capacitive droop = 0.5 × 125 µs/470 µF = **133 mV**,
   plus ESR step 0.5 A × 0.15 Ω = **75 mV**, total **~210 mV** local, recovering
   between pulses. With 1000 µF low-ESR it halves. The rail never moves enough
   to matter to anything, and the reference sees it through 60+ dB of PSRR.

4. **`AGND` as a sense return that carries no power current.** This is what makes
   the 2 kHz LED ground bounce harmless. My number: 0.5 A of strip current in
   2 m of 24 AWG ground conductor is 0.5 × 0.19 = **95 mV** of PWR_GND offset
   between instrument and module, modulated at the PWM rate — and because the
   in-amp senses BREATH against AGND and both are referenced to the instrument's
   analog star point, it is pure common mode into ~90 dB of CMRR. **3 µV.** The
   decision is correct and ADR 0014 is right that lighting validates it.

5. **Feeding the dev boards 5 V into their `5V`/`VBUS` pins.** Correct, and for
   the correct reason — backfeeding a `3V3` pin fights the onboard regulator and
   contends with USB during flashing.

6. **3.3 V off the real-time board's onboard LDO.** My load tally is **~5 mA**
   against an ESP32-S3 taking 80–100 mA on a ≥500 mA regulator. "Comfortably
   inside the headroom" is an understatement. (Finding 10 argues for a separate
   rail on reference-integrity grounds, not current.)

7. **No power switch on the instrument.** The reasoning in ADR 0005 —
   that the strips are upstream of the buck so killing the buck leaves a lit
   instrument with dead logic, and that the working version is a fat P-FET in a
   body that cannot be reopened — is correct and well argued.

8. **Blank-at-boot for both strips and the matrix.** Necessary, and it is what
   makes the R-78E's hiccup-mode overload behaviour self-clearing rather than
   latching (see finding 7). Keep it as the literal first statement in `setup()`.

9. **The WS2815 logic-threshold worry resolves in the design's favour.** ADR 0014
   flags it as an open risk: *"if its logic threshold is referenced to 12 V
   rather than an internal rail, 5 V shifting will not be enough."* It is not.
   The WS2815 contains an internal regulator that supplies its logic at 5 V, and
   V_IH = 0.7 × 5 V = 3.5 V `[verified this session — WS2815 specification gives
   V_IH = 0.7 VDD with the logic VDD = 4.5–5.5 V, separate from the 9.5–13.5 V
   power supply]`. A 74AHCT125 on 5 V clears it with ~1.1 V of margin, and with
   the R-78E's ±5 % worst-case output of 4.75 V `[verified]` it still drives
   ~4.6 V. **Close this open item; the part choice is correct.**

10. **The thermal coefficient.** 3 K/W is a good bounding estimate. My
    independent model says 2.89 K/W. Finding 9 disputes what it gets multiplied
    by, not the number itself.

---

## Summary of proposed changes, by cost

| # | Change | Cost |
|---|---|---|
| 1 | Replace TPS2553 with a 12 V-rated eFuse | 1 part swap, **blocking** |
| 2 | Raise the current limit to 1.0 A; design the inrush ramp | resistor values |
| 3 | Delete `F-POLY` | −1 part |
| 4 | Add 10 µF ceramic + 100 µF damping electrolytic at the buck input | +2 parts |
| 5 | R_ISO 10 Ω in-loop + 100 pF feedback cap on the reference buffer | +2 parts |
| 6 | Watchdog-gated shunt across BREATH at the module | +1 analog switch |
| 7 | Second R-78E5.0 (per ADR 0013); clamp in rail current not LED watts | +1 part, firmware |
| 8 | `C-AA-ADC` 220 nF → 47 nF; add the pole to the latency budget | value change |
| 9 | 105 °C/2000 h/25 V electrolytics; restate the budget as a total | spec text |
| 10 | Dedicated 3.3 V LDO for the MCP3202 at the analog star point | +3 parts |
| 11 | SMBJ13A on +12 V; 5 V array on signal conductors only | +1 part |
| 12 | Specify 24 AWG stranded; parallel the two spare conductors onto power | free |
| 13 | Size `C-BULK-DISP` at 220 µF; add bulk at the buck output and the matrix | +4 parts |
| 14 | Correct the clamp-current note | text |

Net part count: roughly **+12 passives and two ICs**, one deletion, one
substitution. Nothing here changes the architecture; finding 1 is the only one
that must be resolved before a PCB can be laid out.
