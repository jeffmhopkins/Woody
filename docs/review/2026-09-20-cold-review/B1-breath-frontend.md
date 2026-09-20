# B1 — Breath sensing front end: independent analog design review

**Scope reviewed:** mouthpiece → tube → trap/restrictor → MPXV4006DP → REF5050 +
OPA2197 supply → OPA2197 buffer → split to (a) umbilical driver / in-amp
receiver and (b) 10k/15k divider → 220 nF → MCP3202.

**Documents read:** `README.md`, `ROADMAP.md`, `docs/decisions/0001`, `0003`,
`0004`, `0005`, `0006`, `0007`, `0008`, `0009`, `0012`, `0013`, `0014`,
`docs/reference/latency-budget.md`, `hardware/bom.csv`. I did **not** read
`docs/review/` or `docs/log/`.

**Datasheet policy used below.** Every numeric claim is tagged either
`[verified-in-repo]` (arithmetic checked against figures the repo itself
states), `[first-principles]` (physics/circuit arithmetic I did here), or
`[from memory]` (a datasheet figure I am asserting without having the datasheet
in front of me — treat as a claim to check, not as fact). No datasheets are
present in `hardware/datasheets/`, so nothing could be verified against a
primary source.

---

## 1. The ADC anti-alias network's corner is 121 Hz, not 600 Hz, and it puts 1.3 ms of unbudgeted lag on the note-onset path

**Severity: MAJOR**

**Where.** `docs/decisions/0003-breath-sensing-path.md`, "The ADC does not go
away":

> **Size the upper divider resistor at ≥10 kΩ.**

> **And put a 220 nF cap at the ADC input pin.** … 220 nF gives a ~600 Hz corner
> and **58 dB at 500 kHz**.
>
> - Together with the divider it settles well inside the 250 µs loop period.

and `hardware/bom.csv`:

> `R-ADCDIV,controller,10k / 15k 1% metal film,,0.6x divider from the breath buffer to the ADC`
> `C-AA-ADC,controller,220nF X7R,,Anti-alias cap at the MCP3202 input pin,…"~600Hz corner, 58dB at 500kHz…"`

**The arithmetic.** `[first-principles]` A 0.6× divider from 10 k / 15 k has
15/(10+15) = 0.600 ✓, and a Thévenin source resistance of

```
R_th = 10k ‖ 15k = 150/25 = 6.00 kΩ
```

The pole the cap forms is against `R_th`, not against either leg:

```
τ  = 6.00 kΩ × 220 nF = 1.320 ms
f₃dB = 1/(2π·1.32 ms) = 120.6 Hz
```

**121 Hz, not 600 Hz — a factor of five.** To get 600 Hz with 220 nF you need
R_th = 1/(2π·600·220 n) = 1.21 kΩ, i.e. roughly a 2 k / 3 k divider, which is
exactly the low-impedance divider the same paragraph forbids on ESD-clamp
grounds. **The two specifications in that paragraph are mutually exclusive as
written**, and the BOM carries both.

Three consequences, in order of importance:

**(a) 1.32 ms of group delay on the path that starts notes.** `[first-principles]`
A single-pole lag delays a threshold crossing by ≈ τ for a slow ramp. ADR 0003
states that "the threshold that starts a note is on the latency-critical path",
and `latency-budget.md` §"Breath digital copy (sampled)" itemises every term down
to "< 20 µs" of firmware — but contains no filter term at all. 1.32 ms is **five
times the entire listed electronics budget** of that table (sampling 0.125 + conv
0.2 + firmware 0.02 + SPI 0.05 + settle 0.01 + filter 0.16 ≈ 0.57 ms). See
Finding 2.

**(b) The filter is now narrower than the signal it passes.** The repo puts the
sensor's own bandwidth at ~159 Hz (`bom.csv`: "~1ms response = ~159Hz corner").
A 121 Hz pole in front of a 159 Hz signal is not an anti-alias filter, it is a
second signal-band pole. At the 23–70 Hz content of a 5–15 ms tongue attack
(f ≈ 0.35/t_r) `[first-principles]`, the two poles together cost 1.1–4.6 dB and
roughly double the effective rise time.

**(c) "Settles well inside the 250 µs loop period" is false on the repo's own
numbers, and is a category error besides.** Even at the claimed 600 Hz corner,
τ = 265 µs > 250 µs, and 0.5-LSB settling at 12 bits needs ln(8192) = 9.01 τ =
2.4 ms. At the real 121 Hz it needs 11.9 ms. The sentence conflates *filter
settling* (which is deliberately slow and does not need to finish in a loop
period) with *sample-capacitor settling* (which does, and which is fine — see
Confirmation C2).

**What the filter is actually guarding against, quantified.** `[first-principles]`
The stated disturber is the R-78E5.0's switching residue folding to ~100 Hz.
Trace the path with the post-ADR-0003 topology, where the sensor and buffer are
on +12 V and *not* on the buck's 5 V output:

| Step | Value |
|---|---|
| Buck input ripple current at ~500 kHz, isolated by `L-BUCK-IN` 10–47 µH | assume 100 mA p-p |
| Instrument +12 V node impedance at 500 kHz with ~100 µF bulk | ~3 mΩ + ESR, call it 50 mΩ |
| Ripple on the +12 V node | ~5 mV p-p |
| OPA2197 PSRR at 500 kHz `[from memory, ~25 dB]` | 0.28 mV at buffer output |
| × 0.6 divider | 0.17 mV at the ADC pin |
| MCP3202 LSB at VDD = 3.3 V | 3.3/4096 = **0.806 mV** |

**The disturber is ~0.2 LSB before any filtering at all.** The dramatic framing
("indistinguishable from playing", "a wandering tone") is not supported by the
amplitude. The cap is still worth having — it is genuinely useful against SCLK
charge injection during the sample aperture (see Finding 9) — but 220 nF is
between one and two orders of magnitude more than the job needs, and it is paid
for in milliseconds on the most latency-sensitive path in the instrument.

**Proposal.** `[first-principles]`

- **Change `C-AA-ADC` from 220 nF to 4.7 nF.** With R_th = 6.00 kΩ:
  - f₃dB = 1/(2π·6k·4.7n) = **5.64 kHz**
  - attenuation at 500 kHz = 20·log₁₀(500 k / 5.64 k) = **39 dB**, which against
    a 0.2 LSB disturber leaves 0.002 LSB
  - group delay = τ = **28 µs**, i.e. 1.29 ms recovered
  - sample-cap reservoir ratio: 4.7 nF / 20 pF `[from memory: MCP3202 C_sample ≈ 20 pF]`
    = 235:1, giving 0.43 % aperture droop, a **fixed gain error of ~16 LSB (0.4 %)**
    that the breath calibration removes and that does not move with signal
- Keep `R-ADCDIV` at 10 k / 15 k — the ESD reasoning is sound (Finding 8).
- If more stopband is wanted, add a second pole *at the buffer output* where it
  is cheap in delay: 100 Ω + 10 nF = 159 kHz, 10 dB at 500 kHz, 1.6 µs of delay,
  and it also isolates the op-amp from the cable (Finding 7).
- Correct the BOM note and the ADR text: the corner is set by `R_th`, not by
  either resistor, and the "settles inside 250 µs" line should be deleted and
  replaced with the sample-aperture calculation, which is the claim that is
  actually true.

**Confidence: high** on the arithmetic (it is unambiguous), **medium-high** on
the disturber-amplitude estimate, which depends on an assumed buck ripple current
and an asserted PSRR figure.

**What would falsify it.** Build the divider and cap as specified on the E2
bench, inject a 1 V p-p sine into the buffer input with the signal generator, and
sweep 10 Hz – 10 kHz while logging the ADC. If the −3 dB point lands near 600 Hz
rather than 120 Hz, my model of which resistance sets the pole is wrong. Separately,
scope the ADC input pin with the 220 nF *removed* while the buck and LED strips
run, at 100 µV/div AC-coupled with a 1 MHz bandwidth limit: if the switching
residue there exceeds ~0.8 mV, the aggressive filter is justified and Finding 1
is wrong on severity.

---

## 2. The latency budget omits every filter pole the design itself specifies; the note-onset path is ~4.4–4.7 ms against a 5 ms target, not 2.6–2.9 ms

**Severity: MAJOR**

**Where.** `docs/reference/latency-budget.md`, "Breath CV at the jack (analog, no
sampling)":

> | Buffer, cable, in-amp, output filter | < 0.2 ms | Propagation plus filter group delay only |
> | **Total** | **~2.4 ms** | |

and "Breath digital copy (sampled)", whose stages sum to ~2.6–2.9 ms with no
filter term other than "Op-amp + reconstruction filter ~160 µs".

And `docs/decisions/0003-breath-sensing-path.md`:

> **Band-limit at both ends, around 500 Hz.**

> Add a deliberate pneumatic restrictor at the sensor port to make the path
> first-order rather than resonant.

**The arithmetic.** `[first-principles]` Every one of those is a pole, and for a
cascade of real first-order lags the delay of a threshold crossing is the sum of
the time constants.

*Analog CV path, as specified:*

| Term | τ | Source |
|---|---|---|
| Two 500 Hz poles ("at both ends") | 2 × 318 µs = 636 µs | ADR 0003 |
| Module output reconstruction filter, ~2 kHz | 80 µs | ADR 0006 |
| **Sum** | **716 µs** | vs **"< 0.2 ms"** stated |

The analog path is therefore ~1.17 + 1.0 + 0.72 = **2.9 ms**, not 2.4 ms.

*Digital / note-onset path, as specified:*

| Term | ms | Status in the budget |
|---|---|---|
| Tube propagation, 400 mm | 1.17 | listed |
| Pneumatic restrictor + trap/port dead volume | 0.3–0.8 | **absent** (see Finding 3) |
| Transducer | 1.00 | listed |
| ADC anti-alias RC (6 kΩ × 220 nF) | 1.32 | **absent** (Finding 1) |
| Sampling latency, mean / worst | 0.125 / 0.25 | listed |
| SAR conversion | 0.05–0.20 | listed |
| Firmware + SPI to DAC + settle + pitch filter | 0.09 | listed |
| **Total, mean** | **4.06–4.68** | vs **2.6–2.9 stated** |

Against the 5 ms target that is **6–19 % of margin, not the 42–48 % claimed**,
and ADR 0003's headline claim —

> The digitised path has roughly 10x margin.

— becomes about 1.1×. None of the three missing terms is exotic: all three are
components this same ADR specifies, in the same document, a few sections apart.

The pneumatic restrictor term deserves emphasis because it is the one nobody has
sized. `[first-principles]` A porous plug feeding a downstream volume V is a
pneumatic RC with C = V/(γP₀) = 1 mL/(1.4 × 101 325 Pa) = 7.05 × 10⁻¹² m³/Pa.
Placing the pneumatic corner at 200 Hz (where it would actually damp the tube
resonance of Finding 3) needs R = 1/(2π · 200 · 7.05e−12) = 1.13 × 10⁸ Pa·s/m³,
which by Poiseuille (R = 128 µL/πd⁴, µ_air = 1.8 × 10⁻⁵ Pa·s) is a **0.34 mm ×
2 mm orifice** — and costs **0.80 ms**. At a 500 Hz pneumatic corner it costs
0.32 ms and damps the resonance far less. That trade is real, it is the trade
ADR 0003 gestures at ("trap volume and response time are coupled"), and it is
currently absent from the budget in both directions.

**Proposal.**

- Add three rows to `latency-budget.md`: *ADC anti-alias filter*, *pneumatic
  restrictor*, and *analog channel band-limit (2 poles)*, each with its own
  arithmetic, and mark them as design-controlled rather than physical.
- Adopt Finding 1's 4.7 nF, which returns 1.29 ms of the deficit for free.
- **Band-limit asymmetrically, not "at both ends".** Put the 500 Hz pole at the
  *module* end only (where it is doing the EMI job that matters, after 2 m of
  cable), and at the instrument end use a much faster pole — the 159 kHz RC
  proposed in Finding 1 — which still keeps the op-amp's wideband noise and any
  HF pickup off the cable but costs 1.6 µs instead of 318 µs. The cable is
  driven from ~100 Ω through 10 kΩ into a Gigaohm in-amp; nothing about it
  requires 500 Hz at the transmit end.
- Size the restrictor from a *measured* resonance (Finding 3), not from a
  target, and budget whatever it costs.

**Confidence: high.** The individual terms follow from component values the repo
states; the only soft number is the restrictor's, which is soft because nobody
has chosen it.

**What would falsify it.** The budget's own final row — "End-to-end, in one shot:
two scope channels, one on the sensor output, one on the CV jack". Extend it: a
third channel on the pitch gate at the module, a fast solenoid or syringe step at
the mouthpiece, and measure step-to-gate-assert. If that number comes back under
3 ms with the specified 220 nF and a real restrictor fitted, my summation model
(time constants adding) is wrong and so is this finding.

---

## 3. The tube resonance cannot be put above 500 Hz by shrinking the trap; it is set by tube length and lands at 220–440 Hz whatever the trap volume is

**Severity: MAJOR**

**Where.** `docs/decisions/0003-breath-sensing-path.md`, "The cost, and why it is
affordable":

> | Tube | Delay | Helmholtz |
> | 30 mm (old) | 0.09 ms | 2858 Hz |
> | **400 mm (chosen)** | **1.17 ms** | **214 Hz** |

> it is a **Helmholtz resonator**, and at 3 mL of trap it lands near **320 Hz,
> below the 500 Hz filter corner**, where it would pass straight through. So:
>
> - **Specify the trap volume at ≤1 mL.**

and `ROADMAP.md`:

> **Helmholtz restrictor sizing** | E2 | Trap volume and response time are
> coupled. Size the orifice to put the resonance above the 500 Hz filter corner
> (ADR 0003)

**Why the model does not hold.** `[first-principles]` The Helmholtz formula

```
f = (c / 2π) · √( A / (V · L) )
```

is a *lumped* model, valid only when the cavity volume is large compared with the
neck volume — when the neck's air is a mass and the cavity's air is a spring.
Here the "neck" is the entire 400 mm tube. For a 3 mm ID tube:

```
A       = π(1.5 mm)²      = 7.07 mm²  = 7.07 × 10⁻⁶ m²
V_neck  = A · L = 7.07e−6 × 0.4       = 2.83 × 10⁻⁶ m³  = 2.83 mL
```

**The neck volume is 2.83 mL and the trap is specified at ≤1 mL.** The cavity is
*smaller than the neck*. The lumped assumption is violated by roughly 3:1 before
any number is plugged in, and shrinking the trap makes it worse, not better. As
V → 0 the Helmholtz formula sends f → ∞, which is the tell that the model has
left its domain.

The correct model at V ≪ V_neck is a distributed organ pipe, whose first
resonance depends only on length and end conditions:

| End condition at the mouthpiece | Model | f₁ at L = 400 mm, c = 350 m/s |
|---|---|---|
| Low impedance (open, lips off) | quarter-wave, c/4L | **219 Hz** |
| High impedance (lips sealed, cheeks loaded) | half-wave, c/2L | **437 Hz** |

Both are **below the 500 Hz electrical corner**, both are independent of trap
volume, and 219 Hz sits almost exactly on the ADR's own 214 Hz figure — which is
the strongest evidence that the tube, not the trap, is what is resonating.

The ADR's own numbers do not reproduce either. To get 320 Hz from the Helmholtz
formula at V = 3 mL and L = 0.4 m requires

```
A = V · L · (2πf/c)² = 3e−6 × 0.4 × (2π·320/350)² = 3.96 × 10⁻⁵ m²  →  ID = 7.1 mm
```

a 7.1 mm bore. **The tube bore is not specified anywhere in the repository** —
`hardware/bom.csv` gives only `TUBE … silicone tube + dead-volume trap … ~400mm`
— and since f ∝ ID under this model, the two published frequencies (214 Hz and
320 Hz) cannot both be right for one tube.

And even the ≤1 mL spec does not meet its own goal. Solving for the trap volume
that puts a Helmholtz resonance above 500 Hz `[first-principles]`:

| Tube ID | A (mm²) | V for f > 500 Hz |
|---|---|---|
| 3 mm | 7.07 | **≤ 0.22 mL** |
| 4 mm | 12.6 | ≤ 0.39 mL |
| 6 mm | 28.3 | ≤ 0.88 mL |
| 7.1 mm | 39.6 | ≤ 1.23 mL |

**≤1 mL only achieves the stated goal at a bore of 6.4 mm or larger**, and at
that bore the lumped model is even more thoroughly violated (V_neck = 12.9 mL).
The specification and its purpose do not meet at any bore.

**Proposal.** Stop trying to *tune* the resonance and *damp* it instead, which is
what the restrictor was always going to do anyway:

- **Specify the tube bore in the BOM.** It sets the resonance, the propagation
  delay, the restrictor sizing and the condensation surface area. 3 mm ID
  silicone is the sensible default (it keeps V_neck small, which limits the
  per-note vapour pumping of Finding 6).
- **Restate the design intent as damping, not placement:** the restrictor plus
  the sensor-side dead volume forms a pneumatic low-pass whose corner should sit
  *below* the tube's first resonance, so the sensor never sees it. With a 219 Hz
  resonance, a ~150 Hz pneumatic corner gives 3.3 dB of rejection at the
  resonance and, together with a slightly resistive plug, drops the Q enough that
  it is not a ringing mode at all. Cost: τ = 1.06 ms (Finding 2).
- **Then lower the electrical corner or shorten the tube if the measurement
  disagrees.** Tube length is the only lever that moves the resonance itself, and
  at L = 175 mm the quarter-wave lands at 500 Hz — which is worth knowing as the
  fallback, since it also halves the propagation delay.
- Update the E2 roadmap row: it should read "measure the resonance and its Q, then
  size the restrictor to damp it", not "size the orifice to put the resonance
  above 500 Hz".

**Confidence: high** that the Helmholtz model is being applied outside its
validity domain and that trap-shrinking cannot raise the resonance;
**medium-high** on the specific 219–437 Hz bracket, which depends on the
mouth-end acoustic impedance — a real player's embouchure is somewhere between
the two idealisations and will also add loss.

**What would falsify it.** The E2 measurement the roadmap already calls for, run
as a *swept* test rather than a step: drive the mouthpiece end with a small
speaker or a signal-generator-driven pump over 50 Hz – 1 kHz, scope the sensor
output, and plot the magnitude. If the peak moves substantially when the trap
volume is changed between 0.5 mL and 3 mL, the Helmholtz model is the right one
and this finding is wrong. If the peak stays near c/4L and only its *height*
changes, the distributed model is right. Repeat with the tube cut to 200 mm: the
peak should double.

---

## 4. The ambient-zero injection has only one polarity of authority, and it is the wrong one — ~0.43 V (4.3 % of span) of sensor pedestal has nothing to remove it

**Severity: MAJOR**

**Where.** `docs/decisions/0003-breath-sensing-path.md`:

> its **REF pin is the natural injection point** for the firmware ambient-zero,
> driven from a low-impedance buffer rather than a divider

> **The zero is injected at the module, into the in-amp's `REF` pin, from DAC
> channel 6** (ADR 0006).

and `docs/decisions/0006-cv-channel-allocation.md`:

> | *(internal)* | DAC ch 6 | — | — | Breath ambient-zero offset (ADR 0003) |

> | **Breath** | 0 V | The receiver's differential pulldown holds it there (ADR 0003) |

**The arithmetic.** `[verified-in-repo]` ADR 0003 gives the transfer function and
the supply:

```
Vout = VS × (0.1533·P + 0.04),  VS = 5.000 V
```

At P = 0 — which is the resting state, since both diaphragm faces are at cavity
pressure —

```
V_sensor(0) = 5.000 × 0.04 = 0.200 V
```

This is not offset error; it is the part's deliberate zero-pressure pedestal, 4 %
of VS, and it is present on every unit by design.

An instrumentation amplifier's transfer function is

```
V_out = G · (V_IN+ − V_IN−) + V_REF
```

With `BREATH` on IN+, `AGND` on IN−, and the ADR's stated G ≈ 2.13:

```
V_out(no breath) = 2.13 × 0.200 + V_REF = 0.426 V + V_REF
```

To null that, **V_REF must be −0.426 V.** `DAC8568` channel 6 runs from the
module's LM317LZ at 5.25 V with the internal reference × 2, so its output range
is **0 V to ~5 V. It cannot go negative at all.**

So the ambient-zero channel can only push the breath output *up*, never down.
The ~0.426 V pedestal stays. After the panel gain stage that fits the 4.5 V
sensor span to 10 V (total gain 2.22), the residual at the jack is

```
0.200 V × 2.22 = 0.444 V   →  4.4 % of the 0–10 V span, at rest
```

Three things break as a result:

- **ADR 0006's power-on table is wrong for breath.** "Breath — 0 V" is true only
  when the instrument is off (the 100 k differential pulldown holds BREATH at
  AGND). Switch the instrument on and the breath jack sits at 0.44 V with nobody
  blowing. A VCA fed that is not closed; an envelope follower or a threshold
  downstream sees a permanent floor.
- **It forces the panel offset knob into the technical role**, which collides
  head-on with ADR 0006's own rule: *"Two offset authorities in series would be
  a split-brain failure."* The knob is specified for musical floor-setting, and
  it would now be spending its first 4.4 % undoing a sensor artefact — so the
  knob has no neutral position, and its neutral position moves with temperature.
- **It leaves the auto-zero with no headroom in the direction it needs.** ADR
  0006 requires the zero to "decay toward the current reading" continuously as
  the body warms. The sensor's offset tempco moves in both directions; a
  correction authority clipped at 0 can track only one of them.

**Proposal.** `[first-principles]` Reuse the exact topology ADR 0006 already
builds for the mod channels, at 1/10 the gain, on the spare half of an OPA2197:

```
V_REF(in-amp) = 0.4 × (V_DAC6 − V_DAC7)
```

where `V_DAC7` is the same buffered 2.5 V mod-offset channel already specified.
That gives:

| | |
|---|---|
| V_REF range | −1.00 V … +1.00 V |
| Needed to null the pedestal | −0.426 V — comfortably mid-range |
| Resolution at 16 bit over 2 V | 30.5 µV, i.e. **3 ppm of the 10 V output** |
| Extra parts | one op-amp half (already in the package count) + a 1:0.4 divider pair |
| Power-on state | DAC ch 6 and ch 7 both zero-scale ⇒ V_REF = 0 ⇒ output 0 V, so ADR 0006's power-on table becomes true again |

The alternative — subtracting the pedestal at the *instrument*, before the
umbilical — is worse: it would need a second precision reference and it would
put a fixed subtraction in a place firmware cannot see or correct.

**Confidence: high** on the polarity problem (it follows from the in-amp equation
and the DAC's unipolar supply, both of which the repo states). **Medium** on
whether the author already intends an inverting receiver arrangement — the ADRs
never state the in-amp's input polarity, and an inverting arrangement
(`AGND` → IN+, `BREATH` → IN−, plus a downstream inverter) would make the DAC's
unipolar range the correct one. If that is the intent, it is unwritten, and it
needs writing down, because the downstream inverting stage is then mandatory and
is not in the BOM either.

**What would falsify it.** At E10, before fitting the gain knob: power the module
and the instrument, blow nothing, and measure the in-amp output with a DMM while
sweeping DAC channel 6 over its full code range. If the output can be brought to
0.000 V at any code, my reading of the topology is wrong. If the minimum
achievable output is ~0.43 V, the finding stands.

---

## 5. The ADC branch has no defined ground reference — and the free fix (MCP3202 pseudo-differential against AGND, on the channel the BOM already lists as spare) is unused

**Severity: MAJOR**

**Where.** `docs/decisions/0003-breath-sensing-path.md` defines the analog star
carefully —

> **The star point is the analog ground pour on the bottom cluster board, at the
> sensor and reference, immediately adjacent to the umbilical connector.**
>
> Everything analog in the instrument — the sensor, the REF5050, both halves of
> the OPA2197, the ADC divider — sits on that one board

— but never says what the divider's **lower leg**, the anti-alias capacitor, or
the MCP3202's own `VSS` return to. `hardware/bom.csv` records the unused
resource:

> `U-ADC,controller,MCP3202-CI/SN,… VDD-referenced so no separate ref chip. 50ksps at 3V3 vs 4-8kHz needed. One spare channel`

And `docs/decisions/0014-lighting.md` already predicts the symptom:

> **Through the ADC it is positive feedback**, via reference depression from
> shared-ground LED current. Still far from instability — **but the symptom is
> not gain error, it is note-gate chatter.**

**Why it matters.** `[first-principles]` The MCP3202 is VDD-referenced and
single-supply: its conversion result is
`code = 4096 × (V_IN+ − V_IN−) / VDD`, and in single-ended mode `V_IN−` is
internally `VSS`. So whatever potential difference exists between the analog
star (where the divider's bottom sits, if it sits there) and the ADC's `VSS`
(which is the dev board's digital ground) appears **directly, one-for-one, as an
input error**. Every bit of care ADR 0003 spends on keeping `AGND` clean over the
2 m umbilical is undone by an undefined 30 mm of copper on the carrier.

Magnitude, with the loads the bottom of the instrument actually carries — the
umbilical PWR_GND entry, the buck's pulsed input current, the WS2815 feed, and
the 8×8 WS2812C matrix on the real-time board itself:

| Return current in the pour between the star and the ADC's VSS | Pour resistance | Offset | In LSB (0.806 mV) |
|---|---|---|---|
| 100 mA (matrix sparse + logic) | 5 mΩ | 0.5 mV | 0.6 |
| 300 mA (strips animating) | 5 mΩ | 1.5 mV | 1.9 |
| 300 mA over a longer / narrower path | 20 mΩ | 6.0 mV | **7.4** |

That error is not static: it tracks the LED PWM at ~2 kHz *and* the animation
envelope, which is at breath rates because ADR 0014 drives the lights from
breath. ADR 0014 correctly identifies the resulting note-gate chatter and
proposes two firmware mitigations — hysteresis sized from measurement, and
driving the LEDs from the post-gate value. Both are good, and both are patches
around a structural problem that has a structural fix.

**Proposal.** `[from memory: the MCP3202 supports a pseudo-differential mode via
the SGL/DIFF configuration bit, with CH0 as IN+ and CH1 as IN−, and requires IN−
to stay within roughly ±100 mV of VSS — verify against the datasheet, which is
not in the repo.]`

- **Wire CH1 to the analog star point** and run the converter in pseudo-
  differential mode. CH1 is already listed as spare, so this costs one trace.
  The ground offset then appears on both inputs and cancels in the difference,
  and the few-millivolt offsets computed above are two orders of magnitude inside
  the ±100 mV IN− window.
- **State the return topology explicitly in ADR 0003:** the divider's lower leg,
  `C-AA-ADC`, and CH1 all return to the analog star; the MCP3202's `VSS` goes to
  digital ground with the rest of the logic; AGND and PWR_GND meet at exactly one
  point, at the umbilical connector.
- Keep ADR 0014's two firmware mitigations. They are cheap and they defend
  against what remains.

**Confidence: high** that the reference is undefined and that it is the weak
point; **medium-high** on the pseudo-differential mode being available on this
exact part number (`MCP3202-CI/SN`) — if it is not, the same job is done by
switching to an `MCP3201`/`MCP3208` with a separate `VREF`/`AGND` pin, at the
cost of one part number.

**What would falsify it.** At E4, with the strips and the matrix running a full
breath animation and the mouthpiece plugged (so the real breath signal is
constant), log the ADC at 4 kHz for a minute and take its spectrum. Content at
the PWM rate and at the animation rate quantifies the coupling directly. If the
peak-to-peak excursion is under ~1 LSB, the ground path is better than my
estimate and the structural fix is optional rather than needed. Then repeat with
CH1 strapped to the star and pseudo-differential mode enabled — the difference
between the two runs *is* the finding.

---

## 6. The PTFE plug does two jobs that fight each other: succeeding as a water barrier changes its resistance, and the breath attack time drifts with wetting

**Severity: MAJOR**

**Where.** `docs/decisions/0003-breath-sensing-path.md`:

> - **A porous hydrophobic PTFE plug at the sensor port.** It blocks liquid water
>   and it is *the same part as the Helmholtz restrictor above* — one component
>   doing both jobs, which is why the restrictor should be specified as a PTFE
>   plug rather than a drilled orifice.

and `hardware/bom.csv`:

> `MECH-PTFE,controller,Porous hydrophobic PTFE plug,,Helmholtz restrictor AND liquid-water barrier at the sensor port`

**Why it is risky.** `[first-principles]` A hydrophobic porous membrane blocks
water by *pore occlusion* — the water forms a meniscus in each pore that cannot
be pushed through below the bubble point. That is the same physical event as
"the pore stops passing gas". A membrane doing its job well has a fraction of its
pores wetted, and the gas path resistance of a partially wetted membrane is

```
R ∝ 1 / (fraction of open pores)
```

So the part's restrictor value is a function of how much water it has caught.
And the restrictor value sets the sensor's attack time (Finding 2):

| Open-pore fraction | R | Pneumatic corner (from a 150 Hz nominal) | τ | Perceived |
|---|---|---|---|---|
| 1.00 | R₀ | 150 Hz | 1.06 ms | as designed |
| 0.50 | 2R₀ | 75 Hz | 2.12 ms | +1 ms on every attack |
| 0.20 | 5R₀ | 30 Hz | 5.3 ms | **breath response visibly sluggish** |
| 0.10 | 10R₀ | 15 Hz | 10.6 ms | attack unusable; total path > 13 ms |

**This fails gradually, invisibly, and reversibly** — the instrument feels
slightly soft after twenty minutes of playing and crisp again the next morning,
which is exactly the profile of a fault that gets blamed on the player's
embouchure for years. It belongs in `ROADMAP.md`'s "Failures that are silent"
table, which currently lists three and does not list this one.

It is also structurally worse than the alternatives because the two jobs have
*opposite* area requirements: a restrictor wants small, defined area (so its
value is reproducible); a water barrier wants large area (so partial wetting
barely changes anything).

**How much water there is, for proportion.** `[first-principles]` ADR 0003's own
figure — 6 % volume exchange per note at 6 kPa — over a 3 mm × 400 mm tube
(2.83 mL) is 0.17 mL of saturated 34 °C breath per note. At 200 notes in 20
minutes that is 34 mL. Saturated air at 34 °C carries ~37 g/m³; at a 25 °C wall
it carries ~23 g/m³, so the condensable fraction is ~14 g/m³:

```
34 mL × 14 g/m³ = 0.48 mg  ≈ 0.48 µL of water per 20 minutes
```

**That is genuinely small**, and it supports the ADR's "condensation, in
proportion" framing (see Confirmation C6). But the volume is small *and
cumulative at one point*, and the point it accumulates at is the plug — because
the plug is the coldest, narrowest, highest-surface-to-volume element in the
path. 3 µL over a two-hour session is more than enough to wet a small membrane.

**Proposal.** **Split the two jobs into two parts.**

- **Restrictor:** a defined orifice — a short length of small-bore tubing or a
  laser-drilled disc — sized from the E2 resonance measurement (Finding 3). Its
  value is then geometric and does not change with humidity.
- **Water barrier:** a hydrophobic PTFE membrane of **large** area, placed
  upstream of the orifice, sized so that its dry resistance is ≤ 10 % of the
  orifice's. Then even 50 % occlusion of the membrane changes the total by 10 %
  (0.1 ms), not by 100 %.
- Put the **trap between them**, so liquid collects where it can be cleared, at
  the point ADR 0009 already requires access to.
- Add a line to the roadmap's silent-failure table: *"Breath attack slows over a
  session → wetted restrictor. Made loud by: log the 10–90 % rise time of the
  first attack of each session and show it on the display when it exceeds 2× the
  cold value."* That is free in firmware and it makes the failure self-reporting.

**Confidence: high** on the mechanism (it is how hydrophobic vent membranes work);
**medium** on the magnitudes in the table, which assume the plug's resistance
scales inversely with open area — real porous media are messier, and a membrane
with a large enough pore count may show much softer degradation.

**What would falsify it.** At E2, measure the sensor's step response through the
plug when dry; then deliberately wet the plug (a drop of water on the upstream
face, blown off, so only the pores hold liquid) and repeat within seconds. If the
10–90 % rise time changes by less than ~20 %, the coupling is weak and this
finding drops to MINOR. Also worth: run the 20-minute human play test the roadmap
already requires, and scope the rise time of the *first* attack and the *last*
attack of the session.

---

## 7. The 500 Hz band-limiting capacitor must sit on the far side of the 10 kΩ series resistor, and nothing says so

**Severity: MINOR**

**Where.** `docs/decisions/0003-breath-sensing-path.md`:

> the instrument end needs **only a buffer** — an op-amp follower, band-limited,
> with a series resistor for protection.

> protection resistors can be 10 kΩ and unmatched with no CMRR penalty

The physical arrangement of the band-limiting capacitor relative to the series
resistor is never stated.

**The arithmetic.** `[first-principles]` A 500 Hz pole against 10 kΩ needs

```
C = 1/(2π · 500 · 10 k) = 31.8 nF
```

If that capacitor is placed at the **op-amp output**, before the series resistor
— which is the natural reading of "an op-amp follower, band-limited, with a
series resistor for protection", since the band-limiting is named before the
resistor — then the OPA2197 is driving 31.8 nF with no isolation. `[from memory:
the OPA2197 is a 10 MHz unity-gain-stable precision amplifier whose tolerable
direct capacitive load without isolation is on the order of 1 nF; 32 nF is 30×
that.]` The result is peaking or outright oscillation in a follower, and the
symptom — a buffer that rings on breath transients and is clean on a syringe
step, because the syringe step is slower — is a genuinely unpleasant bring-up
bug.

If the capacitor is placed **after** the series resistor (across `BREATH`–`AGND`
at the connector), the op-amp sees only the cable's ~120 pF `[first-principles:
Cat5e pair capacitance ≈ 50 pF/m × 2 m ≈ 100 pF, plus connectors]`, the RC is
formed by the resistor it already has, and everything is stable. The 10 kΩ then
also serves as the isolation resistor, which is the textbook arrangement.

**Proposal.**

- State it in ADR 0003 and in the BOM: **the band-limiting capacitor goes on the
  connector side of the series resistor, never on the op-amp output.**
- Add the capacitor to `hardware/bom.csv` — it is currently absent. The BOM
  carries `R-PD-BREATH` (the 100 k differential pulldown) and `C-AA-ADC`, but no
  part implements the "band-limit at both ends, around 500 Hz" rule at either
  end. The module end has no filter part either.
- If Finding 2's asymmetric band-limiting is adopted, the instrument-end part
  becomes 100 Ω + 10 nF at the op-amp output (159 kHz, and 10 nF is inside a
  100 Ω isolation resistor's comfort zone) with the 500 Hz pole moving to the
  module.

**Confidence: medium-high.** The stability issue is certain if the capacitor
lands in the wrong place; the risk is that it does, given the sentence ordering
and the missing BOM lines.

**What would falsify it.** Build the buffer on the bench with 32 nF directly on
the output and look at the small-signal step response with a 10 mV square wave.
If there is no overshoot beyond a few percent, the OPA2197 tolerates the load and
the placement does not matter. (I would expect substantial ringing; this is a
five-minute test.)

---

## 8. The ≥10 kΩ divider rule is right, but its stated reason no longer applies — the real hazard is the op-amp's output during the +12 V ramp

**Severity: MINOR**

**Where.** `docs/decisions/0003-breath-sensing-path.md`:

> **Size the upper divider resistor at ≥10 kΩ.** On a cold start the 5 V rail
> comes up before the real-time board's 3.3 V regulator, so for a few
> milliseconds the divider drives the ADC input above its own supply and current
> flows through the ESD clamp. A low-impedance divider puts ~2.5 mA into that
> diode, at or over the family-typical ±2 mA limit, on **every power-up**.

**Why the stated reason is stale.** The same ADR moves the sensor, the reference
and the buffer off the 5 V rail entirely:

> ```
> umbilical +12V ──[REF5050 5.000V]──[OPA2197 ½ buffer]──┬── MPXV4006DP VS
> ```

So the "5 V rail comes up before 3.3 V" sequence no longer describes this branch.
`[first-principles]` Once the analog chain is settled, the buffer's output is
0.2 V (zero pressure) and the divider presents 0.12 V to the ADC — far below any
clamp. The paragraph's own scenario cannot happen.

**Why the conclusion survives anyway, for a different and better reason.** The
real hazard is the **+12 V ramp itself**. The TPS2553 load switch ramps the
instrument's +12 V over some milliseconds; during that ramp the REF5050 output is
climbing and the OPA2197's own supply is below its minimum operating voltage. A
rail-to-rail output stage whose feedback loop is not yet valid can sit anywhere
between the rails, including near V+. Worst case, the buffer output is at the
instantaneous +12 V while the ADC's 3.3 V is already up (the buck and the dev
board LDO may well be faster than the analog chain, since they are downstream of
less filtering):

```
I_clamp = (12 V − 4.0 V)/10 kΩ − (4.0 V / 15 kΩ)
        = 0.800 mA − 0.267 mA
        = 0.53 mA          ← comfortably inside ±2 mA
```

With a 2 k / 3 k divider the same event gives

```
(12 − 4.0)/2 k − 4.0/3 k = 4.00 mA − 1.33 mA = 2.67 mA   ← over the limit
```

**So: keep ≥10 kΩ, and rewrite the justification.** The value is right; the reason
in the ADR is a fossil of the pre-REF5050 topology, and a fossil justification is
exactly what gets "optimised away" later by someone who notices the sequence it
describes cannot occur.

**Proposal.** Replace the paragraph's reasoning with the +12 V-ramp case above,
and add one sentence: *"The analog chain (REF5050, OPA2197, sensor) is the last
thing in the instrument to become valid, because it is furthest downstream of the
load switch's ramp. Assume its output is indeterminate until +12 V is settled."*

**Confidence: high** that the stated reason is stale; **medium** that the op-amp
output actually reaches near-rail during the ramp — some RRIO parts pull their
output low during undervoltage, some do not, and the OPA2197 datasheet is not in
the repo.

**What would falsify it.** At E2, scope the buffer output and the +12 V rail
together through a power-up, with the load switch's ramp active. If the output
never exceeds the final 0.2 V, there is no hazard at all and the divider could in
principle be any impedance — though I would keep 10 kΩ regardless, since it costs
nothing now that Finding 1 has removed the settling objection.

---

## 9. The MCP3202 shares SPI2 with a 2 m unterminated umbilical, and only MOSI is source-terminated

**Severity: MINOR**

**Where.** `docs/decisions/0001-mcu-and-board-partitioning.md`:

> | **SPI2** | DAC8568 (down the umbilical) + MCP3202 | Both tri-state properly on CS |

and `docs/decisions/0004-cv-interface-module.md`:

> **220 Ω in series on MOSI at the driving end.** Source termination on the one
> line that runs the full umbilical carrying data.

> SCLK, the fastest edge in the system, is at the far end.

**The problem.** `[first-principles]` `SCLK` runs the full 2 m umbilical into an
unterminated CMOS input at the module — and the breath ADC sits on the *same
net*, as a near-end stub. A 2 m Cat5 pair has a one-way propagation of ~10 ns
(≈5 ns/m) and a 20 ns round trip; an ESP32-S3 GPIO's rise time is a few
nanoseconds, so `t_r ≪ 2·t_prop` and the line is electrically long. An
unterminated far end reflects the full step back, and an ~30 Ω driver source
reflects it again, producing overshoot and a ringing settling pattern at the
driver — which is where the MCP3202's `CLK` pin is.

The failure mode is specific and nasty: **a double-clocked MCP3202 loses frame
alignment**, so the 12-bit result is shifted and the breath reading becomes
garbage — intermittently, correlated with cable movement, and looking exactly
like a failing sensor. ADR 0004 already applies the right fix to MOSI and names
SCLK as the fastest edge in the system, then does not terminate it.

With 220 Ω source termination on SCLK, the near-end ADC sees an intermediate
plateau of `3.3 × 100/(100+220) = 1.03 V` for the 20 ns round-trip time
`[first-principles]`. Against an `MCP3202` V_IH of 0.7 × 3.3 = 2.31 V
`[from memory]`, 1.03 V is well clear of the threshold, so the ADC simply sees
its clock edge delayed by 20 ns — irrelevant at 0.6–2 MHz (500–1667 ns period).

**Proposal.**

- **Add a 220 Ω source termination on SCLK**, matching MOSI, at the driving end,
  and list it in the BOM alongside `R-MOSI-SER`. Same reasoning, same part, one
  more resistor.
- Consider **not** sharing SPI2 between the ADC and the umbilical at all. The
  real-time board has spare GPIO (ADR 0007: "GPIO 3 and 4 stay free"), and
  bit-banging or a third host for a 4 kHz, 16-clock ADC read would take the
  breath converter entirely off a 2 m transmission line. That is a bigger change
  and probably not worth it — but it should be a decision rather than an
  inheritance from a partitioning table whose only stated criterion was "both
  tri-state properly on CS".
- Fold this into the E11 measurement the budget already schedules ("SPI over the
  umbilical at length"), explicitly including a probe on the ADC's CLK pin, not
  only at the module end.

**Confidence: medium-high** on the electrical analysis; **medium** on severity,
since 0.6 MHz is slow and the reflections have ~250 ns to settle within each
half-period. The reason to fix it is that it costs one resistor and the failure
is otherwise a multi-day debugging session inside a body that cannot be reopened.

**What would falsify it.** At E11, with the full 2 m cable fitted, put a
high-bandwidth probe with a short ground spring directly on the MCP3202's `CLK`
pin and look at the rising edge. If overshoot stays below V_DD + 0.3 V and there
is no non-monotonic crossing of the threshold region, no termination is needed.
Run it with the cable coiled, uncoiled, and draped over the rack — the worst case
is a specific cable geometry.

---

## 10. The dead-ended tube presents the player's full occlusion pressure to a 6 kPa part, and the 0–6 kPa choice is asserted rather than measured

**Severity: MINOR**

**Where.** `docs/decisions/0003-breath-sensing-path.md`:

> The 0–6 kPa range was well chosen in 2021 and stands. Normal wind-controller
> playing sits around 0–5 kPa.

and, two sections later, the ADR's own counter-evidence:

> Against a full occlusion an adult produces 15–20 kPa

**The tension.** `[verified-in-repo]` The ADR rebuts the "player cannot exhale"
objection correctly — the player vents around the mouthpiece — but that rebuttal
is about *flow*, not about *pressure*. Mouth pressure is set by embouchure and
diaphragm, and the sealed tube transmits it undiminished. So the same document
that establishes an adult can generate 15–20 kPa also specifies a transducer
whose output saturates at 6 kPa, which is **2.5–3.3× overrange**, and the design
contains nothing — no bleed, no flow resistance, no mechanical stop — that limits
what reaches the die.

Consequences, in order:

- **Dynamic-range compression at the top.** If the author's comfortable *forte*
  sits at 7–8 kPa, the top 15–25 % of their expressive range does nothing at all,
  and — because the tube is dead-ended and there is no flow to feel — there is no
  tactile cue that the range has ended. The player pushes harder and nothing
  happens. Curve shaping cannot recover clipped data.
- **The ADR's 0–5 kPa figure is an assertion with no cited source** and no
  measurement scheduled. E2's roadmap row runs a human for 20 minutes but is
  written around zeroing, restrictor sizing and condensation, not around range.
- **The saturation behaviour is untested.** How the part's integrated conditioner
  behaves at 3× overrange, and how long it takes to recover, is not addressed
  anywhere. `[from memory: the MPXV4006's silicon diaphragm is rated well above
  its full-scale span — hundreds of kPa burst — so damage is unlikely; the
  question is output recovery behaviour, not survival.]`

**What makes this cheap to fix rather than expensive.** `[from memory: the
MPXV5010DP is a 0–10 kPa dual-port device in the same case 1351-01, with the same
0.2–4.7 V ratiometric output form — verify against the datasheet.]` If that holds,
the range is a **drop-in decision**, not a board respin, and ADR 0003's own
"treat the sensor as a wear part … socketed or otherwise replaceable" rule makes
it field-changeable.

**Proposal.**

- Add a row to E2: **measure the author's own playing pressure** with a cheap
  U-tube water manometer or a spare high-range sensor teed into the mouthpiece,
  across *pp* to *ff* and a hard tongue attack. This is an afternoon and it
  converts the project's least-examined assumption into a number. 1 kPa = 102 mm
  of water column, so a 30 cm U-tube covers the whole range visibly.
- **Buy one MPXV5010DP alongside the two MPXV4006DPs.** Same package, same
  footprint, same mounting; it becomes the fallback if the measurement says the
  playing range exceeds ~5 kPa. The cost is one part, and — critically — it has
  to be bought *before* M8, because the body bonds shut.
- Note in the ADR that at 0–10 kPa the sensitivity halves (0.4599 V/kPa vs
  0.7665 V/kPa `[verified-in-repo, from the stated transfer function]`) and the
  in-amp gain must rise from ~2.13 to ~4.44 to keep the 0–10 V output span.
  That is a resistor change at the module, not a redesign — worth recording so
  the swap stays cheap.

**Confidence: medium.** The physics is certain; whether it bites depends entirely
on one unmeasured personal number. The reason to raise it is the asymmetry: the
measurement is trivially cheap and the consequence of guessing wrong is permanent.

**What would falsify it.** The manometer measurement. If sustained *ff* playing
comes in under 4.5 kPa with attacks peaking under 6 kPa, the 0–6 kPa choice is
right and this finding is void.

---

## 11. The breath front end no longer runs on bench USB power, and two milestones assume it does

**Severity: MINOR**

**Where.** `docs/decisions/0005-power-architecture.md`:

> **OR the umbilical power with USB power** — it costs a diode, and it means the
> instrument runs on the bench during development without a rack attached. That
> is worth a diode.

against the same ADR's revised power tree:

> ```
> umbilical +12V ──┬── WS2815 LED strips          (direct, no conversion)
>                  ├── REF5050 5.000V ──[OPA2197 ½]── MPXV4006DP breath sensor
>                  ├── OPA2197 V+  (½ reference buffer, ½ breath buffer)
> ```

**The problem.** USB supplies 5 V. The sensor's supply chain now starts at
**+12 V**, upstream of the buck. A diode OR from USB 5 V can only join the 5 V
node, which is downstream of everything the breath front end needs. So on bench
USB power: the dev boards run, the key chain runs, the display runs, USB MIDI
enumerates — and the REF5050, the OPA2197 and the sensor are all dead. The ADC
reads a hard zero.

That collides with two roadmap milestones:

- **E2** — "a human plays it for 20 minutes through a real mouthpiece, tube and
  trap". Cannot be done on USB alone.
- **E5** — "USB MIDI out. Plays into a DAW. **First playable milestone**." The
  whole point of E5 is that it happens before any module hardware exists. Breath
  is the primary expressive control, so E5 without breath is not a playable
  milestone.

This is not a design error — the +12 V move is right for other reasons (see
Confirmation C3) — it is a **stale sentence that will send someone to a bench
without a supply**, and a missing line item.

**Proposal.**

- Correct the ADR 0005 sentence: *"USB power runs the logic on the bench. The
  breath front end is on +12 V and needs a bench supply; budget for one."*
- Add a line to the bring-up notes: **E1–E5 require a +12 V bench supply**
  (anything ≥ 100 mA; the analog chain draws ~15 mA, the strips are what make it
  large). A lab supply is already on the bench per the BOM's `BENCH` row, so the
  cost is zero — the cost of *not* writing it down is a wasted afternoon.
- While editing: the diode OR's placement should be stated. ORing USB 5 V onto
  the buck's *output* backfeeds the R-78E5.0's output pin, which is normally
  fine for a Recom SIP but is worth a sentence.

**Confidence: high.** This follows directly from two statements in the same
document.

**What would falsify it.** Nothing to measure — it is a documentation
contradiction. It is falsified only if the intended OR point is somewhere I have
not considered, e.g. a boost from USB 5 V to 12 V, which nothing in the repo
mentions.

---

## 12. Three documents still describe the pre-move breath topology, and one of them specifies a part ADR 0003 explicitly rejected

**Severity: NIT** (but the INA134 line is the kind of NIT that gets built)

**Where.**

`docs/decisions/0004-cv-interface-module.md`, "Module parts, chosen for build
ease":

> **INA134 for the breath difference amp.** On-chip matched resistors give ~90 dB
> CMRR against the 60 dB needed (ADR 0003), with no external matching network to
> place or match.

This directly contradicts ADR 0003, which spends a full section rejecting it:

> **But the receiver is a true instrumentation amplifier (INA821 / INA828), not a
> difference amplifier.** A difference amp's CMRR is set by **source-impedance
> balance, not by the chip** … this design's own protection resistor and pulldown
> would have left roughly **19–34 dB against the 60 dB the scheme needs.**

`hardware/bom.csv` has it right (`U-DIFFRX … INA821 or INA828`), but ADR 0004 is
the document someone reads when laying out the module.

`docs/decisions/0013-two-mcu-split.md`, "Physical placement: three zones":

> | **Top** | Display board (AMOLED + WiFi), **breath sensor + ADC on a short tube**, upper key cluster |

and its distance table (`Breath ADC | 145 mm`) — both describing the placement
ADR 0003 reverses, and reverses for good reasons including thermal proximity to
the display board.

ADR 0004's conductor-budget section also still says the analog channel is
**"differential"** in places ("BREATH / AGND … analog, band-limited ~500 Hz,
sense return" is right; ADR 0006's table says "**analog, differential over the
umbilical**", which is not what ADR 0003 decided — it is single-ended against a
dedicated sense return, and ADR 0003 explicitly declines full differential:
"Full differential signalling was considered and is not needed").

**Proposal.** Three edits, no design change:

- ADR 0004: replace the INA134 paragraph with a pointer to ADR 0003's INA821/828
  decision and its reasoning. Leaving a rejected part specified in an accepted ADR
  is the single cheapest way to build the wrong board.
- ADR 0013: update the zone table and the distance table to put the sensor, the
  reference, the buffer and the ADC in the **bottom** zone. Note that this also
  changes the table's conclusion — the ADC run becomes ~205 mm, not 145 mm, which
  is relevant to Finding 9.
- ADR 0006: change "analog, differential over the umbilical" to "analog,
  single-ended against a dedicated sense return".

**Confidence: high.** These are textual contradictions between accepted documents.

**What would falsify it.** Nothing measurable. It is falsified only by a decision
to change the receiver back to a difference amp, which ADR 0003's CMRR arithmetic
argues against convincingly.

---

# Confirmations — things this design gets right

These are as load-bearing as the objections, and several of them are
counter-intuitive enough that a future reviewer might "fix" them by mistake.

## C1. The noise budget is genuinely a non-problem, and the reasoning for that is correct

`docs/decisions/0003-breath-sensing-path.md`: *"A low-bandwidth analog channel is
much easier to keep clean than a wide one."*

`[first-principles]`, referred to the 0–10 V jack with the in-amp at G ≈ 2.13 and
a 500 Hz noise bandwidth (1.57 × 500 = 785 Hz equivalent noise bandwidth for one
pole):

| Source | Spot noise `[from memory]` | Integrated | At the jack (×2.22) |
|---|---|---|---|
| OPA2197 buffer | ~5.5 nV/√Hz | 154 nV rms | 342 nV |
| INA821 input-referred | ~7 nV/√Hz | 196 nV rms | 435 nV |
| REF5050 broadband, ratiometric through the sensor | ~ 15 µV rms `[from memory]` | — | ~32 µV |
| **RSS total** | | | **~32 µV rms** |

Against a 10 V span that is **0.3 ppm**, or 3.3 × 10⁻⁵ % — some 20 dB below the
LSB of the 16-bit DAC driving the other channels, and roughly 100 dB below the
noise floor of human breath (turbulence and diaphragm tremor are percent-level
effects). The reference's own noise dominates the electronics, and even it is
irrelevant. **The design's instinct to narrow the channel rather than fight noise
is correct, and the decision not to use an audio-specialty line driver/receiver
pair is well founded.**

## C2. The source impedance into the MCP3202's sampling capacitor settles, and the ≥10 kΩ divider is not the problem it looks like

This is worth stating because Finding 1 removes the 220 nF that the ADR credits
with fixing it — and the fix was not needed.

`[first-principles, with C_sample ≈ 20 pF and R_switch ≈ 1 kΩ from memory]` The
MCP3202 samples for 1.5 clock cycles. At its 3.3 V maximum clock of ~0.9 MHz
`[from memory]` that is 1.67 µs. Settling to 0.5 LSB at 12 bits needs
ln(2·4096) = 9.01 time constants, so the permitted source time constant is

```
τ_max = 1.67 µs / 9.01 = 185 ns
R_max = 185 ns / 20 pF − 1 kΩ = 9.25 kΩ − 1 kΩ = 8.25 kΩ
```

**The bare 6.00 kΩ Thévenin divider settles on its own, with 27 % margin, and no
reservoir capacitor at all.** The capacitor's real jobs are anti-aliasing and
absorbing SCLK charge injection during the aperture — and for the latter, even
the bare divider is adequate: a 3.3 V edge through 0.5 pF of coupling injects
1.65 pC, which onto ~10 pF of pin capacitance is a 165 mV transient decaying with
τ = 6 kΩ × 10 pF = 60 ns, i.e. 27 time constants inside a 1.67 µs aperture.

Steady-state droop with the 4.7 nF proposed in Finding 1: the average current the
converter draws is `C_s · f_s · V = 20 pF × 4 kHz × V = 80 nA/V`, which across
6.00 kΩ is a **0.048 % gain error** — 2 LSB, fixed, and calibrated out with the
breath span.

## C3. The ratiometric-supply decision is right, and the ADR's own table *understates* how right

`docs/decisions/0003-breath-sensing-path.md`:

> | 5 V rail excursion | Error at the breath jack |
> | 0.4 % (a modest load step) | 21 mV |
> | 1 % | 52 mV |
> | 2 % | 104 mV |

`[first-principles]` Those numbers are referred to the **sensor output**, not to
the jack. At full scale the sensor's ratiometric factor is `0.1533 × 6 + 0.04 =
0.960`, so a 0.4 % (20 mV) rail excursion gives 19.2 mV at the sensor — and then
the in-amp's 2.13× and the output stage's remaining gain multiply it:

| Rail excursion | At the sensor | **At the jack (×2.22 total)** |
|---|---|---|
| 0.4 % | 19.2 mV | **42.6 mV** |
| 1 % | 48.0 mV | **106.6 mV** |
| 2 % | 96.0 mV | **213 mV** |

The table is mislabelled and understates by the in-amp gain. **The conclusion is
more strongly supported than the arithmetic shows**, and the comparison with the
AGND common-mode path (0.13 mV) becomes ~50 dB rather than the stated ~30 dB.
Moving the sensor onto a REF5050 is one of the best decisions in the document.

I also checked whether the +12 V rail is quiet enough for the reference to do its
job at the frequencies that actually exist. `[first-principles]` The instrument's
+12 V node is not quiet at DC — the WS2815 strips pulse hundreds of milliamps at
the ~2 kHz PWM rate through 0.34 Ω of cable `[verified-in-repo]` plus the
TPS2553's Rds(on) plus the PPTC's cold resistance `[from memory: a 1206 500 mA
PPTC is ~0.3–0.8 Ω]`, call it 0.93 Ω total:

```
300 mA × 0.93 Ω = 280 mV p-p at 2 kHz on the instrument's +12 V
```

Through the REF5050 `[from memory: PSRR ≈ 70 dB at 2 kHz]` that is 88 µV on the
5.000 V reference; ratiometrically that is 84 µV at the sensor output and 187 µV
at the jack — **19 ppm of the 10 V span.** The reference earns its place under
exactly the disturbance the instrument actually generates, which is the LED PWM
and not the 500 kHz buck.

## C4. The 5.2 kPa trapped-reference-chamber calculation is correct, and the assembly rules that follow from it are the most valuable paragraphs in ADR 0003

`[first-principles]` At constant volume, `ΔP/P = ΔT/T`:

```
15 K / 288 K = 5.21 %
5.21 % × 101.325 kPa = 5.28 kPa   against a 6 kPa full scale = 88 % of range
```

The ADR's 5.2 kPa is right. More importantly, the *sign* analysis is right and is
the part that saves an instrument: a blocked P2 chamber drives `P1 − P2` negative,
a unidirectional part clips at its 0.2 V pedestal, and the failure appears only
after the body warms. "Reads correctly from cold and fails after ten minutes of
playing" is precisely the profile of a fault that gets misdiagnosed for months,
and the three countermeasures (mask before coating, keep adhesive off both ports,
and watch for *falling* rather than *drifting* output at E2) are correct, cheap
and complete.

The related constraint — **do not gasket the switch cutouts** — is exactly the
kind of cross-decision coupling that only gets caught by writing it down. It is
written down. Good.

## C5. The buffered-instrumentation-amplifier argument against a difference amplifier is correct and the arithmetic holds

`[first-principles]` A difference amplifier's CMRR with a source-impedance
mismatch ΔR against bridge resistance R is approximately
`CMRR ≈ 20·log₁₀(R/ΔR) + ...`; for a unity-gain INA134 with R ≈ 25 kΩ and a
3.3 kΩ unmatched series element, the bound is 20·log₁₀(25 k/3.3 k) = 17.6 dB —
consistent with the ADR's "~24 dB" once the pulldown is included, and nowhere near
the 60 dB needed. The observation that a **buffered-input** in-amp makes source
impedance irrelevant (gigaohm inputs, so ΔR/R → 0) is the correct dissolution of
the conflict, and pairing it with the independent fix (buffer on +12 V, so no
fault current, so no ≥3.3 kΩ requirement) is good engineering practice — two
independent fixes for one problem, in a build that cannot be reopened.

Likewise correct: **the differential pulldown across BREATH–AGND rather than on
one leg.** A single-leg shunt unbalances the source impedances, which is the exact
mechanism the in-amp was chosen to escape.

## C6. "Condensation, in proportion" is right, and the numbers support it

`[first-principles]` Using the ADR's own 6 % per-note volume exchange with a 3 mm
× 400 mm tube (2.83 mL):

- 0.17 mL of saturated 34 °C breath per note
- 200 notes in 20 minutes = 34 mL; condensable fraction ~14 g/m³ ⇒ **0.48 µL per
  20 minutes**, ~3 µL in a two-hour session
- the tube dries out between sessions by diffusion through the mouthpiece:
  `τ ≈ L²/2D = 0.16 m² / (2 × 2.4×10⁻⁵ m²/s) ≈ 3300 s ≈ 55 minutes`

So the tube self-dries overnight and accumulates microlitres, not millilitres.
**The revision that downgraded "saliva reaching the sensor is a certainty" to
"condensation forming slowly on the tube walls" was correct**, and the reasoning
(no bulk flow in a dead-end, so no droplet transport) is the right physical
argument. My only extension is Finding 6: microlitres are still enough to wet a
small membrane, so the water is a *restrictor-value* problem rather than a
sensor-death problem.

## C7. SAR over delta-sigma, and the external ADC over the ESP32-S3's internal one

Both correct, for the reasons given. A delta-sigma's decimation filter group delay
is genuinely on the order of `(N_taps/2)/f_s` and would be milliseconds at these
rates — the same currency as the entire budget. And the ESP32-S3's SAR is
well-known to be nonlinear and noisy enough to be visible on a modulation output.
The note that a *digital* I²C pressure sensor would be slower than an analog part
read by a fast ADC is also right and is the kind of thing that is easy to get
backwards.

## C8. `L-BUCK-IN` as a real inductor rather than a ferrite bead

`[first-principles]` Correct, and the reasoning ("a ferrite bead is a wire at the
frequencies that actually matter here") is right. One caution rather than an
objection: an LC input filter needs damping. With L = 22 µH and ~100 µF of node
capacitance the tank resonates at

```
f₀ = 1/(2π√(22 µH × 100 µF)) = 3.4 kHz
```

which sits close to the WS2815 PWM rate and its harmonics, on the node the
REF5050 and both OPA2197 halves feed from. An undamped Q of 5–10 would turn that
into gain rather than attenuation. A damping leg — an electrolytic of
2–3× the ceramic value with ~1 Ω of ESR in parallel with the filter capacitor,
or a small series resistor in the damping branch — costs one part and makes the
filter's behaviour a design choice rather than a component-tolerance outcome.
Worth adding to the E6 measurement list: sweep the +12 V node impedance and look
for peaking at a few kHz.

---

## Summary and suggested order of attack

| # | Finding | Severity | Cost to fix now | Cost to fix later |
|---|---|---|---|---|
| 1 | AA filter is 121 Hz, not 600 Hz | MAJOR | one capacitor value | 1.3 ms, permanently, inside a bonded body |
| 2 | Latency budget omits all specified filter poles | MAJOR | documentation + #1 + #3 | wrong design decisions downstream |
| 3 | Tube resonance cannot be tuned above 500 Hz by trap volume | MAJOR | rewrite the E2 test; specify bore | wrong restrictor, sealed in |
| 4 | Ambient zero has the wrong polarity of authority | MAJOR | one op-amp half + 2 resistors at the *module* | recoverable — the module opens |
| 5 | ADC branch ground reference undefined | MAJOR | one trace + one config bit | gate chatter, blamed on firmware |
| 6 | PTFE plug's two jobs fight | MAJOR | split into two parts | breath feel drifts, sealed in |
| 7 | Band-limit cap placement unstated | MINOR | one sentence + BOM lines | oscillating buffer at E2 |
| 8 | ≥10 kΩ rule right, reason stale | MINOR | rewrite a paragraph | someone "optimises" it away |
| 9 | SCLK unterminated with the ADC on the net | MINOR | one resistor | intermittent garbage readings |
| 10 | 6 kPa range asserted, not measured | MINOR | a U-tube and an afternoon | permanent, at M8 bond |
| 11 | Breath front end not on bench USB power | MINOR | one sentence | a wasted afternoon |
| 12 | INA134 still specified in ADR 0004 | NIT | three edits | the wrong chip on the board |

**The three that are time-critical** — because they are sealed inside a bonded
body at M6/M8 and cannot be revisited — are **#3 (restrictor and bore)**,
**#6 (splitting the plug's two jobs)** and **#5 (the ADC's ground return on the
carrier)**. #1 and #4 are recoverable after bonding, since a capacitor on the
carrier is unreachable but the module opens; #1's capacitor is *not* reachable, so
it should be treated as sealed too.

**The single most valuable measurement** to add to the roadmap is the one that
tests Findings 1, 2 and 3 at once: at E2, with the final tube, trap and
restrictor, drive a pressure step at the mouthpiece and capture the **sensor
output** and the **ADC input pin** on two channels simultaneously. The difference
between those two traces is the anti-alias filter's real contribution; the ringing
on the first is the tube's real resonance; and the sum is the number the latency
budget should carry.
