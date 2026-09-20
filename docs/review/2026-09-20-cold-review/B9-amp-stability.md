# B9 — Amplifier stages: stability, loading and swing

Independent review. Sources read: `README.md`, `ROADMAP.md`, `docs/decisions/0001`–`0014`
(0003, 0004, 0005, 0006 in full), `docs/reference/latency-budget.md`,
`docs/reference/ks33-geometry.md`, `hardware/bom.csv`. `docs/review/` and `docs/log/`
deliberately not read.

## Datasheet provenance

Network egress to ti.com, mouser and octopart is blocked from this environment, so no
datasheet PDF could be opened. What follows is marked accordingly.

**Verified** (from TI product-page text returned by search, not the PDF itself):

- OPA197/OPA2197: 10 MHz gain bandwidth, 20 V/µs slew, ±65 mA output current, "directly
  drives up to 1 nF of pure capacitive load in unity gain"; TI's own text recommends
  "a small (10 Ω to 20 Ω) resistor in series with the output" for additional capacitive
  drive. The overshoot-vs-capacitive-load curve is **Figure 48, "Small-Signal Overshoot
  vs Capacitive Load"**, characterised at V_S = ±18 V, R_L = 10 kΩ, C_L = 100 pF — I have
  **not** read the curve itself and do not quote percentages from it.
- INA821: gain = 1 + 49.4 kΩ/R_G, the 49.4 kΩ being the sum of two internal trimmed
  24.7 kΩ resistors; 4.7 MHz bandwidth at unity gain; super-beta bipolar inputs.

**From memory, flagged at each use**: OPA197 open-loop output impedance (~100 Ω), input
capacitance (~6–9 pF CM), V_OS 25 µV max, drift 0.25 µV/°C typ, I_B ~5 pA (CMOS input),
input-current absolute maximum ±10 mA; INA821/828 input bias current (sub-nA to ~2 nA)
and output swing (~0.2 V from rail at light load); INA828 gain = 1 + 50 kΩ/R_G; LM317
reference tempco ~0.01 %/°C; MPXV4006DP supply current 6–10 mA. Every conclusion below is
written so that it survives a factor of 2–4 error in any of these; where it would not,
I say so.

---

## 0. The amplifier inventory, and the package count

The ADRs never list the amplifier stages in one place, so here is the enumeration I
derived. "Channel" = one op-amp half.

### Instrument (controller board), single +12 V rail from the umbilical

| # | Stage | Part | Config | Gain / noise gain | Load |
|---|---|---|---|---|---|
| A1 | Reference buffer | ½ U-BUF OPA2197 | follower | 1 / 1 | MPXV4006DP V_S, 6–10 mA, **plus its decoupling** |
| A2 | Breath buffer | ½ U-BUF OPA2197 | follower, band-limited | 1 / 1 | 2 m cable (~200 pF) + 25 kΩ ADC divider |

Required 2, carried 2 (1 × OPA2197 dual). **No spare half.**

### Module, ±12 V less ~0.35 V of Schottky = ±11.65 V nominal

| # | Stage | Part | Config | Gain / noise gain | Load |
|---|---|---|---|---|---|
| B1 | Pitch scaling | ½ OPA2197 | non-inv or difference, + trimmers, LT5400 | 2.000 / 2 (non-inv) or 3 (difference) | 1 kΩ + filter C + patch cable |
| B2–B5 | Mod 1–4 | 2 × OPA2197 | difference, V = 4(V_dac − 2.5) | 4 / **5** | 1 kΩ + filter C + patch cable |
| B6 | Mod shared 2.5 V offset buffer (DAC ch 7) | ½ OPA2197 | follower | 1 / 1 | 4 × R1 ≈ 2.5 kΩ, ±1 mA dynamic |
| B7 | Breath ambient-zero buffer (DAC ch 6) | ½ OPA2197 | follower | 1 / 1 | in-amp REF pin |
| B8 | Breath receiver | INA821/INA828 (3 internal amps) | in-amp | ~2.13 as specified / — | gain pot |
| B9 | Breath gain stage | ½ OPA2197 | pot-dependent | ≤1 / ≥1 | offset summer |
| B10 | Breath offset / output | ½ OPA2197 | summer | 1 / ≥2 | 1 kΩ + filter C + patch cable |

Required **9 discrete op-amp channels**, carried **10** (`U-OPA-PITCH`, OPA2197 × 5).
Add the in-amp's three internal amplifiers and the module holds **13 amplifier stages**.

**Count verdict.** The BOM quantity is correct but has exactly one spare half, and only if
B9/B10 are implemented as two stages. If the breath gain pot needs a buffer between wiper
and summer — and it does, see finding 10 — the count is 10 of 10, zero spare. The BOM's
note on `U-OPA-PITCH` lists six uses ("pitch, mod 1-4, breath scaling") against a quantity
of five duals; that reads as coincidence rather than a count anyone did. Nothing in the
repository states how many amplifier channels the module needs, and the number is 9–10.

System total: **15 amplifier stages** (2 instrument + 10 module op-amp channels as loaded,
3 inside the in-amp), in 7 packages.

---

## 1. The breath ambient-zero cannot subtract — a unipolar DAC at the in-amp REF pin can only add

**Severity: SHOWSTOPPER**

**Where.** ADR 0003: *"its **REF pin is the natural injection point** for the firmware
ambient-zero, driven from a low-impedance buffer rather than a divider"*, and *"The zero is
injected at the module, into the in-amp's `REF` pin, from DAC channel 6"*. ADR 0006 table:
*"(internal) | DAC ch 6 | — | — | Breath ambient-zero offset"*. BOM `U-DIFFRX`: *"REF pin
takes the ambient-zero injection"*.

**Why.** An instrumentation amplifier computes

```
V_out = G · (V_in+ − V_in−) + V_REF
```

The design senses BREATH on the + input against AGND on the − input (ADR 0003: *"have the
module sense `BREATH` against `AGND`"*). At zero breath the MPXV4006DP sits at its
specified 0.2 V pedestal, so with G = 2.13:

```
V_out(no breath) = 2.13 × (0.200 − 0) + V_REF = 0.426 V + V_REF
```

To null it, V_REF = **−0.426 V**. DAC8568 A/C grade with internal reference ×2 spans
**0 V to +5 V**, single-ended to its own ground. It cannot produce a negative volt. The
REF pin adds; the correction has to subtract. The sign is wrong.

It is worse than a single missing volt, because ADR 0006 makes the zero *continuous*:
*"decay the zero toward the current reading whenever breath has been sub-threshold for
about 2 seconds"*, tracking a 10–20 K interior rise on a gauge part with temperature-
dependent offset. That requires **bidirectional** authority around the pedestal — roughly
±0.2 V at the sensor, ±0.43 V at the in-amp output — and a 0–5 V unipolar channel referenced
to ground has authority in one direction only, the wrong one.

Second-order consequence, which is itself a defect: the watchdog (ADR 0004) asserts `CLR`,
which clears **all** channels including ch 6. Breath does not pass through the DAC, so the
watchdog cannot park it — and clearing ch 6 *raises* the breath floor by 0.426 V × the
downstream gain. The mechanism installed to stop the rack droning forever nudges the breath
VCA open by ~0.4–1 V when it fires.

**Proposal.** Any one of three; I prefer (a).

(a) **Swap the in-amp inputs** — AGND to +IN, BREATH to −IN — so V_out = −G·V_breath + V_REF.
Now V_REF = +0.426 V nulls the pedestal and a 0–5 V channel has authority in both directions
around it. The signal is inverted, and the downstream breath gain stage (B9) becomes
inverting, restoring polarity at no part cost and giving a place to put the gain that
finding 8 says is missing.

(b) Do the zero subtraction at the downstream summing stage (B10) instead, where the
summing node can accept a positive DAC voltage through an inverting input.

(c) Level-shift ch 6 with a two-resistor network to −12 V so 0–5 V maps to about
−1.25…+1.25 V. Works, but puts the rack's −12 V rail into the breath zero — see finding 3
for why that habit is expensive.

Whichever is chosen, say in the ADR which input is which, because the sign of the whole
channel depends on it and no document currently states it.

**Confidence: high** on the arithmetic and on the DAC being unipolar. **Medium-high** that
BREATH is the + input — ADR 0003 says "sense BREATH against AGND", which reads that way,
and nothing contradicts it. If the polarity is already the other way round, the finding
evaporates and the design is fine; that it is impossible to tell from the documents is
itself worth fixing.

**Falsified by.** On the bench: 0.2 V into the BREATH input, AGND to 0 V, sweep the REF pin
over 0–5 V and look for an output of 0.000 V. If it exists, I am wrong.

---

## 2. A purely differential pulldown gives the in-amp no common-mode bias return; unplugged, the breath output saturates instead of parking at 0 V

**Severity: SHOWSTOPPER**

**Where.** ADR 0003: *"Put the pulldown **differentially across BREATH–AGND**, not on one
leg. A shunt on a single leg does not symmetrise the way a series element does — 100 kΩ on
the + input alone would cap CMRR near 19 dB."* BOM `R-PD-BREATH`: qty **1**, *"DIFFERENTIAL
across BREATH-AGND not one leg"*. ADR 0006 power-on table: *"**Breath** | 0 V | The
receiver's differential pulldown holds it there"*. ADR 0005 contradicts both: *"**Pull down
the module's breath receive input**, so that an instrument which is switched off — or
unplugged — presents 0 V rather than a floating buffer output. **One resistor**"*.

**Why.** A resistor *between* the two inputs constrains only their difference. Neither input
is referenced to module ground by anything. While the umbilical is connected there is a DC
path — through AGND, the instrument's ground pour, and back down PWR_GND — so the stage
works. The failure is in the state the system spends most of its life in.

ADR 0004 is explicit that *"the ordinary powered-down state is: module alive, DAC alive"*
with the instrument off, and ADR 0004 treats the cable as a consumable to be unplugged and
replaced. With the umbilical out, both in-amp inputs float behind the 10 kΩ protection
resistors and the 100 kΩ differential resistor. Their common-mode potential is then set by
input bias current into stray capacitance:

```
dV/dt = I_B / C ≈ 1 nA / 20 pF = 50 V/ms
```

(I_B for INA821/828 from memory, sub-nA to ~2 nA; the inputs are bipolar super-beta —
verified — so I_B is nanoamps, not picoamps. Even at 100 pA the node reaches a rail in
seconds.) Both inputs ramp to a supply rail, the in-amp's common-mode range is exceeded,
and the output goes wherever the saturated input stage puts it. Through the 1 kΩ output
resistor the BREATH jack then sits at roughly ±10 V — **a fully open VCA, held indefinitely,
in exactly the condition ADR 0005 installed the pulldown to prevent.** The frame watchdog
cannot save it, because breath is analog end to end and never passes through the DAC.

The 19 dB figure the ADR quotes for a single-leg shunt is **correct, and stays correct with
the in-amp**, which is worth stating because it is the reason this is not a free fix. The
imbalance comes from the 10 kΩ series resistor working against the shunt, not from the
receiver's input impedance:

```
one leg divides by 100k/(100k+10k) = 0.9091 → 9.09 % CM→DM conversion
CMRR = 20·log10(1/0.0909) = 20.8 dB
```

So ADR 0005's "one resistor" and ADR 0003's "differential only" are both wrong, in opposite
directions, and the BOM implements one of them.

**Proposal.** Two resistors, not one, symmetric: **1 MΩ from each in-amp input to module
analog ground**, placed on the connector side of the 10 kΩ protection resistors. The
common-mode path now exists and the symmetry preserves CMRR:

```
each leg divides by 1M/(1M+10k) = 0.99010 — identical on both legs
leg-to-leg mismatch with 1 % parts ≈ (10k/1M) × 2 % = 2.0 × 10⁻⁴
CMRR ≈ 20·log10(1/2.0e-4) = 74 dB   (against the 60 dB ADR 0003 requires)
```

With 0.1 % resistors it is 94 dB. Keep the 100 kΩ differential resistor if you like — it now
does only the job it was bought for, defining the differential level — but the two 1 MΩ
parts are what make "unplugged means 0 V" true. Bias-current offset cost: I_B × 1 MΩ ≈ 1 mV
common-mode, which the in-amp rejects, and I_OS × 1 MΩ ≈ 1 mV differential referred to
input — 2 mV at the jack, absorbed by the zero (once finding 1 is fixed) and by the offset
knob.

**Confidence: high.** The topology is stated unambiguously in three documents and the BOM
quantity is 1.

**Falsified by.** Power the module from the rack with the umbilical unplugged, wait two
minutes, and measure the BREATH jack. If it reads within a few millivolts of 0 V there is a
bias path I did not find. Repeat with the instrument connected but switched off.

---

## 3. Nothing in the module generates the pitch stage's offset, and both obvious sources break something the ADRs promise

**Severity: MAJOR**

**Where.** ADR 0006: *"**Use the DAC's 0.25–4.75 V window rather than its full 0–5 V
span**"*, *"**Trimmers set gain and offset.** Two per pitch channel"*, and the power-on
table: *"**Pitch** | Bottom of its range, below −2 V | Subsonic"*. ADR 0006 also deletes the
alternative: *"**The DAC's internal reference is sufficient.** … a separate precision
reference buys nothing measurable. One fewer part."*

**Why.** Work out the transfer function the chosen window actually requires:

```
gain   = (7 − (−2)) / (4.75 − 0.25) = 9 / 4.5 = 2.000   exactly
offset:  V_out = 2·V_dac − 2.500 V
```

(En route: this also retires ADR 0004's table entry *"Gain the scaling stage must supply …
1.8×"*, and ADR 0006's claim that *"the 1.8× gain … is 9/5, which cannot be made from a
matched resistor quad"*. Once the window moved to 0.25–4.75 V the ratio became exactly 2:1,
which a matched quad builds directly as series-pair against single element. The offset
argument for the trimmers still stands; the ratio argument no longer does.)

The 2.500 V offset term is an **absolute voltage**, not a ratio, and the module contains no
source for it. The ADR's own drift table costs everything *except* this term. Take the two
candidates:

*A divider from the rack's −12 V rail* (the only negative voltage in the module, and the
obvious build if the stage is drawn as an inverting summer). The rail's movement reaches the
output with gain 2.5/12 = 0.2083:

```
1 % of −12 V = 120 mV → 25.0 mV at the pitch jack → 25.0 / 83.33 = 30.0 cents
```

Eurorack bus rails are specified ±5 % and move with case load. A 100 mV dip when another
module powers up is 25 cents and it is *not* calibratable, because it moves. Against
ADR 0006's own table — DAC reference 0.54 cents, discrete resistor tracking 5.40 cents,
trimmer tempco 2.4 cents — this unbudgeted term is **6× to 55× the ones that were
budgeted**, and it lands on the one channel the whole precision argument exists for.
ADR 0004 removed the rack's +5 V from under the pitch calibration for precisely this
reason; the −12 V rail would put it straight back.

*A divider from the LM317's 5.25 V.* Better, still poor: LM317 reference drift ~0.01 %/°C
(memory) is 0.1 % over 10 K = 2.5 mV on a 2.5 V offset = **3.0 cents**, six times the
reference term, plus line and load regulation and the ±4 % initial tolerance the BOM already
notes.

*Taking it from DAC channel 8 (the spare), buffered, the way the mod channels do* looks
attractive and breaks the power-on state: ADR 0006 notes the DAC's internal reference is
*"disabled by default"* and the part clears to zero scale, so both terms would be zero and
pitch would park at **0 V** — mid-range on a VCO, audible, held — instead of the subsonic
−2.5 V the ADR promises. The mod channels get away with this exactly because they want 0 V;
pitch wants the opposite.

**Proposal.** Build the stage **non-inverting with the offset at the bottom of the gain
resistor**, from a dedicated small series reference:

```
+IN = V_dac (through the 1 kΩ of R-OPAMP-IN)
R1 from the inverting node to V_off, Rf from the inverting node to V_out, Rf = R1 (LT5400 pair)

V_out = V_dac(1 + Rf/R1) − V_off·(Rf/R1) = 2·V_dac − V_off
V_off = +2.500 V  →  V_dac 0.25 V → −2.000 V ;  V_dac 4.75 V → +7.000 V   ✓
```

Three things fall out. The offset source is now **positive**, so a $1.50 series reference
(REF3025-class, or another REF5050 divided) serves it — no negative reference, no rail.
It is **always on**, coming up with the rails before firmware, so pitch parks at −2.500 V at
rack power-on, subsonic, which is what ADR 0006 claims and currently has no mechanism for.
And the noise gain is **2**, the lowest of the candidate topologies (a difference-amp form
would be 3), which helps finding 6.

Drift cost: 3 ppm/°C × 2.5 V × 10 K = 75 µV = **0.09 cents**, an order below the DAC
reference term. ADR 0006's deletion of "a separate precision reference" was argued entirely
about the *gain* path, where it is right — gain is a ratio and the reference cancels. The
offset path is not a ratio and the deletion left it homeless. This is one part, and it is
the difference between 0.09 cents and 30 cents.

Note in passing that this gives pitch a fixed-reference offset plus a trimmer, which does
**not** violate ADR 0006's "two offset authorities in series would be a split-brain failure"
rule: the reference is a constant, not an authority. Say so in the ADR, or someone will
delete one of them later.

The same question applies to the breath panel offset knob, which also needs a voltage to
inject. There a rail-derived offset is defensible because breath is "Trimmed", not
"Calibrated", and the player closes the loop by ear — but decide it deliberately rather than
by default.

**Confidence: high** that no offset source is specified anywhere (I grepped; there is none).
**Medium** on which one would get built — the −12 V divider is the most likely and the worst.

**Falsified by.** Build the pitch stage, tune it, then load the rack's −12 V rail with a
resistor drawing 200 mA and re-measure the pitch output. Movement under 1 mV means the
offset is not rail-derived and the 30-cent number does not apply.

---

## 4. The breath anti-alias filter sits at 121 Hz, not the 600 Hz claimed — a factor of five, inside the signal band

**Severity: MAJOR**

**Where.** BOM `C-AA-ADC`: *"220nF X7R … ~600Hz corner, 58dB at 500kHz"*. BOM `R-ADCDIV`:
*"10k / 15k 1% metal film … 0.6x divider from the breath buffer to the ADC"*. ADR 0003:
*"220 nF gives a ~600 Hz corner and **58 dB at 500 kHz**"* and *"Together with the divider
it settles well inside the 250 µs loop period."*

**Why.** The cap sits at the ADC pin, so it works against the divider's Thévenin impedance,
not against one leg:

```
R_th = 10 kΩ ∥ 15 kΩ = 6.000 kΩ
f_c  = 1 / (2π · 6000 · 220 nF) = 120.6 Hz      (claimed: ~600 Hz)
τ    = 6000 × 220 nF = 1.32 ms                  (claimed: "well inside 250 µs")
```

The divider ratio itself is right: 15/(10+15) = 0.600, and 4.7 V × 0.6 = 2.82 V into a 3.3 V
ADC, 85 % of range. The ≥10 kΩ upper-leg rule is also right — during the 5 V-before-3.3 V
window the clamp current is (4.7 − 0.7)/10 kΩ ≈ 400 µA minus 47 µA shunted, well inside the
±2 mA family limit. It is only the capacitor that is wrong.

Consequences, in order of how much they matter:

- **The "settles well inside the 250 µs loop period" claim is wrong by a factor of ~40.**
  One time constant is 1.32 ms; settling to one LSB of 12 bits (2.4 × 10⁻⁴) takes 8.3 τ =
  **11 ms**. The sampled breath copy never settles between samples; it tracks with a 1.32 ms
  lag.
- **It eats the signal band.** The sensor's own corner is ~159 Hz (BOM: *"~1ms response =
  ~159Hz corner"*). A 120.6 Hz pole costs **−4.4 dB and 53° of phase at 159 Hz**, and drops
  the sampled path's overall bandwidth to 1/√(1/159² + 1/120.6²) = **96 Hz**. Nobody chose
  that. The digital copy feeds note-gating, the mod-channel modulation source, the display
  and USB MIDI; the mod-source use is the one that will show it.
- **Note-on latency degrades modestly, not catastrophically** — a threshold set low on the
  rise is crossed at ~0.1 τ, so ~130 µs rather than a full time constant. The
  latency-budget table has no line for this filter at all, in either direction.
- Aliasing rejection is *better* than claimed: 20·log10(500 kHz / 120.6 Hz) = **72.4 dB**
  against the stated 58 dB. The one claimed number that the wrong value improves.

**Proposal.** **47 nF instead of 220 nF.** Then:

```
f_c = 1 / (2π · 6000 · 47 nF) = 564 Hz          — the ~600 Hz the ADR intended
attenuation at 500 kHz = 20·log10(500k/564) = 58.9 dB  — the 58 dB the ADR claims
τ = 282 µs, −0.6 dB at 159 Hz
```

Both published numbers become true at once, which is strong evidence that 47 nF is what the
arithmetic was done for and 220 nF is a transcription error. Sample-capacitor reservoir duty
survives: the MCP3202's sample cap is tens of pF, so 47 nF is still ~2000:1 and the charge-
sharing step is ~0.05 %. τ = 282 µs is marginally longer than the 250 µs loop period, so
add a line to the latency budget's digital-copy table saying so rather than pretending it
settles.

**Confidence: very high.** This is arithmetic on three values all of which are in the BOM.

**Falsified by.** Inject a swept sine at the buffer output and measure −3 dB at the ADC pin.
If it is at 600 Hz with 220 nF fitted, the divider is not 10 k/15 k.

---

## 5. The six output reconstruction filters exist in the ADRs and in no BOM line, and their placement relative to the 1 kΩ is never stated — on the wrong side of it every output stage oscillates

**Severity: MAJOR**

**Where.** ADR 0006: *"**Pitch must not be filtered slowly.** … Corner it around 10–20 kHz"*,
*"**Mod 1–4** get a uniform **~2 kHz** filter"*, *"**The pitch output filter stays an
ordinary series RC.** With no in-loop compensation capacitor, the filter's corner is set by
its own R and C and nothing else."* ROADMAP: *"**Pitch stability into worst-case cable
capacitance** | E9 | Confirms the plain series RC is unconditionally stable where an in-loop
version would not have been"*. BOM: `R-OUT-PROT` 1 kΩ × 6, `C-DECOUPLE` 100 nF × 10 *"One
per supply pin"* — and no other capacitor on the module.

**Why.** Two separate problems.

*The parts do not exist.* Taking the 1 kΩ output resistor as the filter's R, the values are

```
pitch, 15.9 kHz:  C = 1/(2π · 1 kΩ · 15.9 kHz) = 10.0 nF
mod/breath, 2 kHz: C = 1/(2π · 1 kΩ · 2.00 kHz) = 79.6 nF  (82 nF → 1.94 kHz)
```

Six capacitors, none in the BOM. Nor are the mod channels' gain-setting resistors, the
in-amp's R_G, the breath band-limiting RCs at either end of the umbilical, or the breath
buffer's series protection resistor. The BOM carries every *protective* passive on the
module and not one *functional* one. That is a pattern worth fixing before layout, because
these are the parts whose values set the transfer functions the ADRs argue about.

*The placement decides whether the module works.* With the capacitor on the **jack** side of
the 1 kΩ and feedback taken at the op-amp output pin, the load pole is outside the loop and
the stage is unconditionally stable for any load capacitance — the ROADMAP's E9 claim is
correct, and this is the right topology. With the capacitor on the **op-amp** side, the
1 kΩ isolates nothing and the amplifier drives 82 nF directly. Using OPA197 open-loop output
impedance R_o ≈ 100 Ω (**from memory**; the verdict is unchanged anywhere from 50 Ω to
400 Ω):

```
load pole = 1/(2π · 100 Ω · 82 nF) = 19.4 kHz
mod stage noise gain 5 → loop crossover ≈ 10 MHz / 5 = 2.0 MHz
the load pole is 100× below crossover → ~90° of extra lag at crossover
phase margin ≈ 0°  → sustained oscillation, hundreds of kHz, inside the precision box
```

TI's own text says the part drives **up to 1 nF** in unity gain (verified). 82 nF is 82× that.
Even 1 nF on the pin puts the pole at 1.59 MHz, and at the mod stage's 2.0 MHz crossover
that is arctan(2.0/1.59) = 51° of extra lag → **PM ≈ 39°** before the amplifier's own excess
phase: ringing, ~25 % overshoot, on every mod channel.

A patch cable, by contrast, is a non-problem *given the right placement*: a 1 m Eurorack
lead is ~50–150 pF, sitting behind the 1 kΩ and behind the 82 nF, and it shifts the corner
by under 0.2 %. The 1 kΩ output resistor is the single best stability decision in the
module, and finding 5 is only about not throwing it away.

**Proposal.** Add the six capacitors to the BOM with values and dielectrics, and write the
placement into the ADR as a rule, not an assumption: *op-amp output → 1 kΩ → filter cap to
analog ground → BAV99 → jack; feedback always from the op-amp output pin.* Use **C0G/NP0**
for the 10 nF pitch capacitor — an X7R's voltage and temperature coefficients (−10 % to
−20 % of capacitance at working voltage is normal) sit directly in the pitch channel's
transfer function, and the whole channel exists to avoid that kind of term. X7R is fine for
the five 82 nF parts.

**Confidence: high** on the missing parts (I read the BOM line by line) and on the
arithmetic. **Medium** that anyone would actually place the cap on the op-amp side — but
nothing in the repository says not to, and it is the placement that makes the pitch filter's
corner independent of load, which is a plausible reason to choose it.

**Falsified by.** Command a 10 kHz square wave on a mod channel and scope the **op-amp
output pin**, not the jack, at 100 ns/div with a 10× probe. Clean settling means the
placement is right; a burst at 200 kHz–2 MHz on the edges means it is not.

---

## 6. The reference buffer drives the sensor's supply pin, which must be decoupled; a follower into 100 nF has no phase margin

**Severity: MAJOR**

**Where.** ADR 0003: *"umbilical +12V ──[REF5050 5.000V]──[OPA2197 ½ buffer]──┬── MPXV4006DP
VS"*, *"**Buffered by half an OPA2197** … The reference alone can source 10 mA against the
sensor's ~10 mA, which is inside its rating and has no margin; the buffer removes the
question and costs nothing"*. ADR 0005 power tree repeats it.

**Why.** The buffer's load is a **supply pin**. Every supply pin gets a decoupling capacitor
— NXP's own application drawings for this sensor family show one at V_S (**from memory**) —
and the BOM's own rule elsewhere is *"100nF ceramic … One per supply pin, close to the
pin"*. So A1 is a unity-gain follower driving 100 nF, and quite possibly 1–10 µF of local
bulk as well. Against TI's verified "drives up to 1 nF in unity gain":

```
load pole = 1/(2π · 100 Ω · 100 nF) = 15.9 kHz      (R_o ≈ 100 Ω, from memory)
unity-gain crossover = 10 MHz
the pole is ~630× below crossover → essentially the full 90° of extra lag
phase margin ≈ 0°  → oscillation
```

Three things make this worse than the usual version of this mistake. The oscillation lands
on a **ratiometric** supply, so it is multiplied straight into the breath scale factor
rather than merely being noise. It is in the **same package** as the breath buffer, sharing
a die and a supply pin, so it couples into the signal it was bought to clean up. And it is
**inside a sealed oak body that cannot be reopened** (ADR 0009), 400 mm from the connector,
which is the worst place in the project to discover a marginal loop.

**Proposal.** Use the compensation TI's own text recommends (verified: *"a small (10 Ω to
20 Ω) resistor in series with the output"*), and decide deliberately where the feedback
comes from:

- **10 Ω between the buffer output and the decoupling capacitor, feedback taken at the
  op-amp pin.** Unconditionally stable for any capacitance. Cost: a load-dependent drop of
  10 Ω × I_sensor. The sensor draws 6–10 mA (**from memory**) and — this is the part that
  makes it safe — that current is essentially *constant*, because the MPXV4006DP is a
  conditioned bridge whose supply current barely moves with pressure. A constant 60–100 mV
  drop is a fixed 1–2 % scale error that the module's breath gain knob absorbs on the first
  breath. Measure the current-versus-pressure variation at E2 before committing: if it moves
  by more than ~100 µA the 1 mV of scale modulation is still nothing, but check rather than
  assume.
- Move the bulk capacitance to the **REF5050's own output**, where it belongs anyway (the
  REF50xx family expects an output capacitor — value from memory, 1–10 µF — and it is
  outside the buffer's loop there), leaving only 1–10 nF at the sensor pin behind the 10 Ω.

If the 60–100 mV drop is judged unacceptable, the alternative is R_iso *inside* the loop with
a small feedback capacitor across it — but that is a compensation network to design and
measure, for 1 % of a scale factor that a knob already sets. Do not use it here.

**Confidence: high** that the node needs decoupling and that an uncompensated follower into
100 nF is unstable. **Medium** on R_o = 100 Ω and therefore on the exact pole frequency; the
verdict does not depend on it.

**Falsified by.** Build the buffer with its real decoupling and scope the buffer output with
the probe's bandwidth limit **off**, at 1 µs/div. Anything periodic between 50 kHz and
5 MHz confirms it. A 20 MHz-limited probe will hide it, which is how this one usually gets
shipped.

---

## 7. The feedback networks have no compensation capacitor, and at unspecified resistor values the inverting-node pole takes most of the phase margin

**Severity: MAJOR**

**Where.** ADR 0006: *"Vout = 4 × (Vdac − 2.5 V)"*, *"**Gain of 4 is a 1:4 ratio**, which the
LT5400 family offers directly"*, *"Channels 2–6 run on ordinary 1% discretes"*. No resistor
values appear anywhere in the ADRs or the BOM for the mod channels; `R-PRECISION` is
qty **TBD**.

**Why.** Stability is set by the **noise gain**, not the signal gain, and the noise gain
rises with frequency because the inverting node's capacitance to ground (op-amp input
capacitance ~6–9 pF **from memory**, plus the LT5400 package, the trimmer, and board strays
— call it 15 pF total) works against the feedback resistor:

```
NG(s) = (1 + Rf/R1) + s·Rf·C_in
```

The difference-amp mod channel has signal gain 4 and **noise gain 5**. Running the numbers
at two plausible resistor choices, against a 10 MHz gain-bandwidth (verified):

| R1 / Rf | NG (DC) | NG zero | Loop crossover | NG at crossover | Phase margin |
|---|---|---|---|---|---|
| 10 k / 40 k | 5 | 1.33 MHz | 1.63 MHz | 6.1 | **≈ 39°** |
| 100 k / 400 k | 5 | 133 kHz | 515 kHz | 19.4 | **≈ 14°** |
| pitch, 10 k / 10 k (non-inv, finding 3) | 2 | 2.12 MHz | 3.26 MHz | 3.1 | **≈ 33°** |

Worked for the first row: zero at 5/(2π·40 kΩ·15 pF) = 1.33 MHz; the loop crosses where
10 MHz/f = f/265 kHz, i.e. f = 1.63 MHz; the zero contributes arctan(1.63/1.33) = 51° of lag
in the loop, leaving 39° before the amplifier's own excess phase at 1.6 MHz is counted.
Realistically low 30s → ~25–30 % overshoot on a step. At 100 kΩ the rate of closure is 40 dB
per decade and **14°** is a circuit that rings for tens of cycles and that a little extra
stray capacitance turns into an oscillator.

None of this is exotic — it is the default behaviour of every inverting stage — but the
design has (a) no specified resistor values, (b) no compensation capacitor in the BOM, and
(c) an explicit decision in ADR 0006 that reads like it disposes of the question:
*"**The pitch output filter stays an ordinary series RC.** With no in-loop compensation
capacitor …"*. That passage is about a *different* capacitor — the dual-feedback output
isolation network — and declining it does not remove the need for this one. They are
different parts in different places doing different jobs, and someone reading the ADR later
will not know that.

**Proposal.** Specify **10 kΩ / 40 kΩ** for the mod channels and **10 kΩ / 10 kΩ** for pitch
(Johnson noise of 10 kΩ is 12.8 nV/√Hz, which is nothing in a channel band-limited to 2 kHz,
and low values keep the noise-gain zero above crossover). Add a **5–10 pF C0G capacitor
across each feedback resistor**: at Rf = 40 kΩ, 5 pF places a noise-gain pole at
1/(2π·40 kΩ·5 pF) = 796 kHz, below crossover, flattening the noise gain back to 5 and
restoring phase margin above 60°. Five capacitors, one line in the BOM. Note in the ADR
that this is *not* the in-loop capacitor that was declined.

**Confidence: medium-high.** The arithmetic is standard; the input-capacitance figure is
from memory and the total stray is a layout property. What I am confident about is that the
question is currently unasked and unbudgeted, and that the answer depends on a resistor
value nobody has chosen.

**Falsified by.** Step a mod channel by 10 V with the feedback cap omitted and scope the
op-amp output pin. Under ~10 % overshoot with no ringing means the strays are smaller than I
assumed and the capacitors are optional.

---

## 8. The in-amp's 2.13× gain cannot reach the specified 10 V once the sensor pedestal is removed

**Severity: MINOR**

**Where.** BOM `U-DIFFRX`: *"Absorbs the ~2.13x gain stage"*. ADR 0006 channel table:
*"**Breath** | analog … | 0–10V"*.

**Why.** 2.13 is 10 V / 4.7 V — the number you get if the sensor's 0.2 V pedestal is treated
as signal. The design removes it (ADR 0003's ambient zero), so the usable span is 4.5 V:

```
2.13 × (4.700 − 0.200) = 9.58 V      — 4.2 % short of the specified 10 V
required gain = 10.00 / 4.50 = 2.222
```

A panel gain knob implemented as a potentiometer can only attenuate, so the shortfall is
permanent: the breath channel would top out at 9.6 V and no adjustment reaches 10 V.

**Proposal.** R_G = **40.2 kΩ, 1 %**. For INA821 (gain equation verified: 1 + 49.4 kΩ/R_G,
from two internal trimmed 24.7 kΩ resistors) that gives G = 2.229 and a 10.03 V maximum. For
INA828 (1 + 50 kΩ/R_G, **from memory**) the same resistor gives 2.244 and 10.10 V. Do *not*
go higher for "headroom" — at a rack rail 5 % low the module's analog supply is
11.4 − 0.35 = 11.05 V, and a G = 2.4 design would need 10.8 V from an in-amp output stage
whose swing-from-rail is weaker than an op-amp's (~0.2 V at light load, **from memory**),
leaving under 100 mV. G = 2.23 leaves a full volt. R_G is not in the BOM; add it.

**Confidence: high** on the arithmetic, **medium** on whether 2.13 was meant as final or as
shorthand.

**Falsified by.** Apply 4.700 V to BREATH with the zero nulled and confirm 10.00 V at the
jack with the gain knob at maximum.

---

## 9. `R-OPAMP-IN` is specified at five, and there are seven DAC-to-amplifier-input connections

**Severity: MINOR**

**Where.** BOM `R-OPAMP-IN`: *"1k 1% … Series resistor on each op-amp + input driven by the
DAC"*, qty **5**. ADR 0006: *"**1 kΩ in series with each op-amp's non-inverting input where
the DAC drives it.** The DAC runs from its own 5.25 V regulator and the op-amps from ±12 V,
so the two supplies do not come up or collapse together."*

**Why.** Count the DAC channels that land on an amplifier input: ch 1 pitch, ch 2–5 mods,
**ch 6 breath ambient-zero buffer**, **ch 7 mod offset buffer** = **seven**. The two offset
buffers are exactly as exposed as the five signal stages — same two supplies, same
sequencing, same input clamp. With the resistor, the clamp current during the window where
±12 V is absent and 5.25 V is present is (5 − 0.7)/1 kΩ = **4.3 mA**, inside the OPA197's
±10 mA input-current absolute maximum (**from memory**). Without it, the current is limited
only by the DAC8568's output drive.

The reverse sequencing case — ±12 V present, 5.25 V absent — is benign in both
configurations: the op-amp input is simply pulled toward ground through the DAC's output
stage.

**Proposal.** Change the quantity to 7. Two 0805 resistors.

**Confidence: high.** It is a count against a stated rule.

**Falsified by.** Nothing to measure; either there are seven such connections or the channel
allocation changed.

---

## 10. The breath knob chain, as described, reintroduces the gain/offset interaction it was ordered to avoid — and consumes the last spare amplifier half

**Severity: MINOR**

**Where.** ADR 0006: *"**Order is gain first, then offset.** Scale how much of the 0–10V span
the breath covers, then position where the floor sits. The reverse ordering makes the two
controls fight each other."* BOM `POT-BREATH`: *"Alpha 9mm vertical PCB mount, B50k
linear"*, qty 2.

**Why.** Ordering fixes one interaction and the implementation can reintroduce another. A
50 kΩ pot used as a divider has a wiper source impedance of R·k·(1−k), maximum **R/4 =
12.5 kΩ at mid-rotation** and zero at both ends. If the wiper feeds a resistive summing
network directly, that varying impedance is in series with the summing resistor:

```
with a 10 kΩ summing resistor, the signal leg's weight runs from
1.000 at either end of travel to 10k/(10k + 12.5k) = 0.44 at centre
```

while the offset leg's weight stays fixed — so the offset knob's effect in volts at the jack
changes as the gain knob is turned, which is the fight ADR 0006 is trying to prevent. The
pot's own taper is irrelevant; this is its output impedance.

Two further points in the same stage. The **zero survives the gain knob correctly** and this
is worth recording as right: the ambient zero is injected at the in-amp REF, so the floor is
nulled *before* the gain control, and gain × 0 = 0 at any knob position. Putting the zero
downstream of the gain knob would have made a firmware-controlled null that the player could
detune with a knob the firmware cannot see. The order chosen is the correct one.

And the **spare half disappears**. Nine channels are required in the module against ten
carried; buffering the wiper makes it ten of ten. An unused half, if one remains, must be
wired as a follower with its input at analog ground — an OPA2197 half with floating pins on
±12 V is a high-gain stage with an undefined input in the same package as the pitch
amplifier. Nothing in the repository says to do this, and it cannot be fixed on a fabbed
board if the pins are left unconnected.

**Proposal.** Either buffer the wiper (B9 becomes a follower, B10 the inverting summer), or
put the gain pot in the feedback path of B9 rather than in front of B10 — the pot's wiper
then drives a virtual ground and its impedance cancels. Say which in the ADR, and state the
termination of any spare amplifier half.

**Confidence: medium.** The stage is not drawn anywhere; this is a warning about the most
likely implementation rather than a defect in a stated one.

**Falsified by.** Set the offset knob to place the floor at 2 V, then sweep the gain knob
end to end and watch the floor. Movement over ~50 mV confirms the interaction.

---

## 11. One missing supply rail turns the designed-safe power-on state into an audible one

**Severity: MINOR**

**Where.** ADR 0006 power-on table: *"**Pitch** | Bottom of its range, below −2 V | Subsonic.
A VCO there is inaudible"*. ADR 0004: *"**A stuck CV is worse than a dead one** … the rack
drones forever."*

**Why.** The whole safe-state argument assumes both rails. Consider +12 V present and −12 V
absent — a bent bus pin, a row-offset ribbon that misses the −12 V row, a failed 1N5817,
all ordinary Eurorack events:

- **Pitch** wants −2.5 V and can only reach ~0 V. 0 V on a 1 V/oct VCO is the middle of its
  range: an audible note, held indefinitely.
- **Mod 1–4** want to reach −10 V and clamp at 0 V. Benign.
- **Breath** saturates. For a three-op-amp in-amp at G = 2.23 with BREATH at 4.7 V and AGND
  at 0, the internal first-stage outputs sit at

  ```
  A1 = V1 + (V1 − V2)·(G−1)/2 = 4.70 + 4.70 × 0.615 = 7.59 V
  A2 = V2 − (V1 − V2)·(G−1)/2 = 0 − 2.89 = −2.89 V
  ```

  Both are comfortable on ±11.65 V — 3.9 V of margin at the worst node, which is the
  headroom check for normal operation and it passes. With no negative rail, A2 cannot reach
  −2.89 V, the input stage clips and the output goes to a rail.

So a single missing rail produces an audible held pitch **and** an open breath VCA: precisely
the failure ADR 0004 built a monostable watchdog to prevent, reached by a route the watchdog
cannot see, because the watchdog only clears the DAC and the DAC is not what is clamping.

**Proposal.** This is a one-off in a rack with a bench beside it, so the honest answer is
procedural rather than a part: add "verify both rails at the module before patching the
outputs" to the E7/E9 bring-up checklist, and note in ADR 0006 that the power-on table
assumes both supplies. If a part is wanted anyway, the cheap version is a −12 V presence
comparator on the same monostable that drives `CLR`, gating a mute — but that is a real
circuit for a rare fault and I would not build it here.

**Confidence: high** on the behaviour, **high** that it is unrecorded.

**Falsified by.** Power the module from a bench supply with −12 V disconnected and measure
the PITCH and BREATH jacks.

---

## 12. Arithmetic in the timing documents that has drifted out of date

**Severity: NIT**

**Where and why**, three items, none of which changes a decision:

*The analog breath path's filter delay is understated ~3×.* `latency-budget.md`:
*"Buffer, cable, in-amp, output filter | < 0.2 ms"*. ADR 0003 specifies band-limiting at
*"both ends, around 500 Hz"*. A single-pole 500 Hz filter has a DC group delay of
1/(2π·500) = **318 µs**; two of them, **637 µs**. Cable propagation over 2 m is ~10 ns. The
line should read ~0.65 ms and the analog breath total ~2.8 ms rather than 2.4 ms — still
well inside the 5 ms target, which is why it is a nit.

*The filter entries are time constants presented as settling times.* "Op-amp +
reconstruction filter ~160 µs, ~2 kHz corner" is 2.0 τ (τ = 79.6 µs) = 13.5 % settled; 1 %
settling is 4.6 τ = 366 µs. "Pitch filter (~10–20 kHz corner) ~10 µs" is one τ at 15.9 kHz =
63 % settled; a 9 V note jump settling to one cent (0.83 mV, 9.2 × 10⁻⁵ of the step) takes
ln(1/9.2e-5) = 9.3 τ = **93 µs**, making the key-path total ~180 µs rather than ~100 µs.
Since the rows are being summed as delays, they should be settling times.

*Ratiometric error is quoted at the sensor and labelled at the jack.* ADR 0003's table is
headed *"Error at the breath jack"* and gives 21 mV for a 0.4 % rail excursion — which is
0.4 % of the sensor's ~5 V supply, i.e. the error at the *sensor output*. At the jack it is
multiplied by the in-amp: 0.4 % × 4.7 V × 2.23 = **42 mV**. The conclusion (put the sensor
on a reference) is right and gets stronger, not weaker.

**Confidence: high** on all three. **Falsified by** a scope on a commanded step at the jack.

---

## Where the design is correct

Said explicitly, because most of this part of the design is right and several of the choices
are better than they look.

- **The 1 kΩ series resistor on every output is the single best stability decision in the
  module**, and ADR 0006's defence of it against removal is correct on every count. With the
  filter capacitor on the jack side of it and feedback taken at the op-amp pin, the amplifier
  never sees the patch cable at all: a 1 m lead's 50–150 pF is behind 1 kΩ *and* behind the
  filter capacitor, and shifts the corner by under 0.2 %. The ROADMAP's E9 claim that *"the
  plain series RC is unconditionally stable where an in-loop version would not have been"* is
  true, and declining TI's dual-feedback topology on a board with no other compensation work
  was the right call. The analysis of the resistor as a pure gain error that the trimmer has
  full authority over is also correct, as is the distinction from the offset error that
  firmware could not reach.
- **Output swing has real margin everywhere.** ±12 V less 0.35 V of Schottky is ±11.65 V,
  and ±10 V is required: 1.65 V of margin, or 1.05 V at a rack rail 5 % low. The three
  different numbers quoted for OPA2197 swing (11.5 V in ADR 0005, 11.45 V in ADR 0006, 11.9 V
  in the BOM) span a range that does not change any conclusion. Load current is trivial —
  10 V into 1 kΩ plus a 100 kΩ VCO input is 99 µA — and even a **dead short on an output is
  only 11.45 mA**, against ±65 mA of output capability (verified), so a shorted jack does not
  take the stage out of its linear range. Worst-case dissipation with both halves shorted is
  ~275 mW in a SOIC-8, roughly a 35 K rise, which is fine.
- **The choice of a CMOS-input precision part makes input bias current a non-issue**, and the
  design gets that for free rather than by analysis. At ~5 pA (from memory) through the 1 kΩ
  DAC series resistor the error is nanovolts, and the unbalanced source impedances (1 kΩ on
  the + input against 8 kΩ at the inverting node) cost ~35 nV. A bipolar-input part would
  have made that imbalance a real offset term. Offset and drift are likewise nowhere near
  binding: 25 µV max V_OS at noise gain 2 is 50 µV at the pitch output = **0.06 cents**, and
  0.25 µV/°C over 10 K is 0.006 cents, against a 0.54-cent reference term and a 2.4-cent
  trimmer term. ADR 0006's *"Still use a low-drift op-amp (OPA2197-class, not TL072)"* is the
  right conclusion, though the real reasons are output swing and common-mode range, not drift
  — a TL072 on these rails could not reach ±10 V and would contribute ~0.65 cents of drift,
  which is comparable to the reference, not dominant over it.
- **The mod channels' power-on state genuinely works**, and the reasoning is sound: taking the
  offset from a DAC channel that clears to zero scale makes both terms of 4·(V_dac − V_off)
  zero at reset, so the outputs sit at exactly 0 V with no extra parts. The A/C-grade
  specification and the "put the full orderable part number in the BOM" instruction are
  exactly right. (Pitch is the channel where this does not work — finding 3.)
- **The shared 2.5 V offset buffer is adequately loaded.** Four difference stages at
  R1 = 10 kΩ present 2.5 kΩ and draw a dynamic ±1 mA as the four channels swing. At DC a
  follower's output impedance is milliohms, so channel-to-channel crosstalk through the shared
  node is a transient only — at ~1 MHz the buffer's Z_out is ~10 Ω and the worst-case
  disturbance is ~10 mV, ×4 at the outputs, for about a microsecond. The 2 kHz reconstruction
  filter removes it entirely. This is fine *provided the filter is built* (finding 5).
- **The instrument's breath buffer is comfortable on every axis.** Input common mode
  0.2–4.7 V on a 0–12 V supply; output swing needs to reach 0.2 V on a rail-to-rail output
  part; load is a 25 kΩ divider plus ~200 pF of cable. The ADR's own check —
  *"~200 pF of cable and a 100 Ω source … the corner sits at 8 MHz against a 160 Hz signal"* —
  verifies: 1/(2π·100·200 pF) = 7.96 MHz. Note that the ADC divider's 220 nF does *not* load
  the buffer, because the 10 kΩ upper leg is between them. Worth flagging one caveat that is
  not addressed: at 200 pF with only ~100 Ω of isolation the OPA2197 is being asked to drive
  a capacitance a fifth of its rated 1 nF with little isolation, and Figure 48 (which I could
  not read) is the place to check the overshoot. The 500 Hz band-limit at the buffer output —
  if built as series R then shunt C, which is the natural form — makes this moot, because the
  amplifier then sees the series resistor and the cable sits behind the capacitor.
- **Moving the breath buffer to +12 V to dissolve the protection-resistor/CMRR conflict is
  elegant and correct**, and so is the observation that a buffered-input in-amp makes source
  impedance irrelevant. Both are real insights, not rationalisations.
- **The BAV99-not-BAT54S arithmetic is right**: 2 µA of Schottky leakage through 1 kΩ is 2 mV,
  and 2 mV / 83.33 mV per semitone is 2.4 cents, temperature-dependent. BAV99's leakage is
  nanoamps, so the same path costs ~0.002 cents.
- **The LM317 divider is correct**: 1.25 × (1 + 768/240) = **5.25 V**, and ±4 % is
  5.04–5.46 V, inside the DAC8568's 5.5 V maximum and above the 4.75 V top of the used output
  window. The REF5050 line-regulation claim also verifies: 5 ppm/V × 5 V = **25 µV** per volt
  of +12 V movement.
- **The ADC divider's ≥10 kΩ rule is right for the right reason**: during the
  5 V-before-3.3 V window the clamp current is ~350 µA against a ±2 mA family limit.
- **The output-rate and image arithmetic in ADR 0006 is correct**: the first zero-order-hold
  image of a 400 Hz source at a 4 kHz update lands at 3.6 kHz, attenuated by
  |sinc(0.9)| = −19.2 dB. The conclusion drawn from it is overstated (finding 13 below), but
  the number is right.

---

## 13. Addendum: the 2 kHz corner puts 6 dB on the image, not "real attenuation"

**Severity: MINOR**

ADR 0006: *"Give the mod channels a lower reconstruction corner than pitch — around 2 kHz.
Their sources top out near 400 Hz, so the corner costs nothing in signal and puts real
attenuation on the image."*

A single pole at 2.00 kHz evaluated at the 3.6 kHz image:

```
20·log10(1/√(1 + (3.6/2)²)) = −6.27 dB
total image suppression = −19.2 (sinc) − 6.3 (filter) = −25.5 dB
cost at 400 Hz = −0.17 dB, 11° of phase
```

−6.3 dB is not much for a stage described as putting "real attenuation" on the image. For
comparison, a second identical pole costs one resistor and one capacitor, buys another
6.3 dB (−31.8 dB total) and costs 0.34 dB and 23° at 400 Hz; alternatively a single pole at
1 kHz gives −11.5 dB at the image for −0.65 dB at 400 Hz. −25 dB may well be enough for a
modulation channel driving a filter cutoff — that is a judgement, not a calculation — but the
ADR should record −6 dB and decide, rather than assert.

**Confidence: high** (arithmetic). **Falsified by** an FFT of a mod output with a 400 Hz sine
commanded, measuring the 3.6 kHz component relative to the fundamental.

---

## Summary table

| # | Finding | Severity | Confidence |
|---|---|---|---|
| 1 | Ambient zero at the in-amp REF has the wrong sign; unipolar DAC cannot subtract | SHOWSTOPPER | High |
| 2 | Differential-only pulldown leaves no CM bias return; breath saturates when unplugged | SHOWSTOPPER | High |
| 3 | Pitch offset term has no source; rail-derived costs 30 cents per 1 % of rail | MAJOR | High / Medium |
| 4 | Anti-alias filter is at 121 Hz, not 600 Hz — 220 nF should be 47 nF | MAJOR | Very high |
| 5 | Six reconstruction capacitors missing from the BOM; placement unstated, one side oscillates | MAJOR | High / Medium |
| 6 | Reference buffer drives the sensor's decoupled supply pin with no isolation | MAJOR | High / Medium |
| 7 | No feedback compensation capacitor; PM 14–39° depending on unspecified resistor values | MAJOR | Medium-high |
| 8 | In-amp gain 2.13 tops out at 9.58 V against a 10 V spec | MINOR | High |
| 9 | `R-OPAMP-IN` qty 5 against seven DAC-to-amplifier connections | MINOR | High |
| 10 | Passive gain pot into a resistive summer makes the two breath knobs fight | MINOR | Medium |
| 11 | A single missing rail makes pitch audible and breath saturated | MINOR | High |
| 12 | Timing-document arithmetic: 500 Hz group delay, τ quoted as settling, error at sensor labelled at jack | NIT | High |
| 13 | 2 kHz corner gives −6.3 dB on the image, not "real attenuation" | MINOR | High |

**The three things to do before layout**, in order: settle the sign and injection point of
the breath ambient zero (1); add the two 1 MΩ common-mode return resistors at the in-amp (2);
decide and document where the pitch offset voltage comes from (3). All three are cheap now
and two of them are unreachable once the instrument is bonded shut or the module is fabbed.
