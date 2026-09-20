# C2 — Passives and discretes review

**Scope:** every resistor, capacitor, inductor, ferrite, trimmer, diode and protective
device in `hardware/bom.csv`, plus every passive the ADRs call for and the BOM does not
list. Assessed for value, tolerance/tempco, rating, dielectric/type, and completeness.

**Sources read:** `hardware/bom.csv` (full), all fourteen ADRs in `docs/decisions/`,
`docs/reference/latency-budget.md`, `docs/reference/ks33-geometry.md`,
`docs/review/2026-09-20-analog-design-review.md`, `docs/log/2026-09-20-review-resolution.md`.

**Headline:** the design's passive selection is mostly sound and the reasoning behind it is
unusually good. Three things are wrong and one is large:

1. **The anti-alias corner at the ADC is off by 5×** — 220 nF against a 6 kΩ source is
   **120.6 Hz**, not the "~600 Hz" ADR 0003 claims, and it puts 1.32 ms of unbudgeted
   group delay into the note-gate path (Finding 1).
2. **Every output reconstruction capacitor is missing from the BOM** — pitch, breath and
   four mod channels. Six parts, all of them corner-setting, none specified (Finding 2).
3. **The polyfuse and the load-switch limit are both below the corrected current budget**
   and will nuisance-trip in normal play (Findings 6, 7).

Everything else is small, and several parts are exactly right for well-stated reasons.

---

## 1. Verdict table — every passive and discrete

### In the BOM

| Ref | Specified | Verdict | One-line reason |
|---|---|---|---|
| `C-AA-ADC` | 220 nF X7R 0805 | **CHANGE** → 47 nF C0G 1206 50 V | 220 nF × 6 kΩ = 120.6 Hz, not the claimed 600 Hz; 1.32 ms of delay into the gate path; X7R is microphonic in a handled instrument |
| `R-ADCDIV` | 10 k / 15 k 1% 0805 | **KEEP** | 0.6× is right, 2.88 V into 3.3 V fits, ≥10 k keeps ESD-clamp current at 363 µA vs a 2 mA limit. Drop "metal film" (not an SMD term) |
| `R-OUT-PROT` | 1 k 0805 ×6 | **CHANGE** package → 1206 (or 0.25 W 0805) | 141 mW in a sustained short vs a 125 mW 0805 rating. Value, tolerance and tempco are all fine |
| `R-OPAMP-IN` | 1 k 1% 0805 ×5 | **CHANGE** qty → 7 | 4.55 mA clamp current vs OPA2197's 10 mA limit is correct; the count misses the two offset-buffer channels |
| `R-PD-BREATH` | 100 k 0805 | **CHANGE** → add two 1 M common-mode bias resistors | Differential-only gives the in-amp no bias-current return when the cable is unplugged; output slams to a rail — the exact failure ADR 0005 says it prevents |
| `R-SPI-PULL` | 10 k 1% 0805 ×3 | **CHANGE** → CS pull-up to 100 k | 10 k to +5 V backfeeds 430 µA through the ESP32's ESD diode into an unpowered 3V3 rail, in the design's *normal* off state |
| `R-MOSI-SER` | 220 Ω 1% 0805 | **CHANGE** → 68 Ω, and add two more for SCLK and CS | 220 Ω launches 0.93 V into 100 Ω; the far end needs 2 round trips (~41 ns) to cross V_IH. Not source termination |
| `R-TERM-CHAIN` | 33–68 Ω 1% 0805 ×2 | **CHANGE** → 68 Ω ×3, or 100 Ω at default GPIO drive | 33 Ω is right only if S3 drive is dropped to 5 mA; the last register's QH return line is unterminated |
| `R-REG-SET` | 240 R / 768 R 1% | **CHANGE** → replace the LM317 with REF5050 + buffer, or select R2 on test | Worst case with I_ADJ and resistor tolerance is **5.62 V**, outside the DAC8568's 5.5 V recommended maximum. Nominal 5.25 V is arithmetically correct |
| `C-REG-ADJ` | 10 µF / 1 µF ceramic or tantalum, 0805/1206 | **UNDERSPECIFIED** | Doesn't say which goes where; "ceramic or tantalum" is a stability decision, not a preference; 10 µF X5R 0805 derates ~50% at bias; no input cap |
| `C-DECOUPLE` | 100 nF ceramic 0805 ×10 | **CHANGE** qty → ≥18; specify X7R 50 V | At least 18 supply pins on the module (5 dual op-amps alone are 10). "Ceramic" is not a dielectric spec |
| `C-DECOUPLE-165` | 100 nF X7R 0805 ×4 | **KEEP**, add 10 µF per satellite | Value and dielectric right; 100 nF alone against ~350 nH of loom inductance resonates near 850 kHz, inside the SPI band |
| `C-STRIP-BULK` | 470–1000 µF electrolytic **16 V** THT | **CHANGE** → 470 µF 25 V 105 °C low-ESR, ≥500 mA ripple | 16 V on a 12 V rail is 1.33× in a sealed body that cannot be reopened; 470 µF gives 0.27 V of 2 kHz ripple, which is adequate |
| `L-BUCK-IN` | 10–47 µH ≥1 A | **UNDERSPECIFIED** | "≥1 A" doesn't say I_sat vs I_rms; the companion capacitor of the "LC" is not specified at all; undamped, the LC lands near the 2 kHz LED PWM rate |
| `FB-IN` | Ferrite ≥1 A + 470 µF, 1206/1210 | **CHANGE** → ≥2 A bead, specify Z@100 MHz, 470 µF **35 V**, 100 µF on the analog branches | No impedance value; ≥1 A is below the 1.2 A the load switch can pass; no capacitor voltage rating on a ±12 V rail; 4 × 470 µF is a lot of module inrush |
| `F-POLY` | PPTC 1206 500 mA hold | **CHANGE** → 1812, 1.1 A hold, ≥16 V, R_init ≤ 0.1 Ω | 500 mA hold against 410–430 mA typical / 600 mA peak is ~1.0×, derating to ~0.95× warm. No voltage rating. Review R17 said this and the BOM did not move |
| `D-REVPOL` | 1N5817 DO-41 ×2 | **CHANGE** → 1N5819 (40 V) or 1N5822 (3 A) | Drop figure (0.33–0.40 V at 0.43 A) is correct; 20 V reverse is 1.67× margin on a protection part and 1 A average is below the fault ceiling |
| `D-JACK-CLAMP` | BAV99 SOT-23 ×6 | **KEEP** | Silicon-not-Schottky is right and the 2 µA → 2 mV → 2.4 cents arithmetic checks. BAV99 leakage at 11 V is nA → <0.12 cents |
| `U-TVS-UMB` | SP3012-06UTG SOT-23-6 | **CHANGE** → keep for the 4 signals, add a separate 16 V TVS for +12 V | SP3012-06 is a **5 V** working-voltage array. On the +12 V conductor it conducts continuously and fails |
| `TRIM-PITCH` | "multiturn cermet, 5–10% of ratio" ×2 | **UNDERSPECIFIED** | No resistance, no turns, no tempco — and the offset trimmer's **reference rail is undefined**, which is a 5-cent ripple path if it lands on raw −12 V |
| `R-PRECISION` | LT5400-class MSOP-8, qty **TBD** | **UNDERSPECIFIED** | No resistance, no ratio variant, no grade, no quantity. The 1 ppm/°C → 0.11 cents figure requires the **A** grade specifically |
| `POT-BREATH` | Alpha 9 mm B50k linear ×2 | **KEEP** part, **UNDERSPECIFIED** network | 50 k linear into a high-Z input is correct; the offset pot's reference rail and both pots' end resistors are unspecified |
| `C-BULK-DISP` | TBD, "1206 / electrolytic THT" | **UNDERSPECIFIED** (flagged `open` in the BOM) | Needs ~220–470 µF 16 V 105 °C radial + 10 µF + 100 nF; a 1206 ceramic alone is 1–2 orders short |
| `MECH-GNDBOND` | Ring terminal + M3 to PWR_GND | **KEEP** | Correct rail (PWR_GND not AGND) for the stated reason |

### Called for by an ADR, absent from the BOM

| What | Where it's specified | Verdict |
|---|---|---|
| BREATH series protection resistor | ADR 0003 ("a series resistor for protection", "can be 10 kΩ") | **MISSING** — recommend 1 k 1% 0805 |
| Instrument-end 500 Hz band-limit RC | ADR 0003 "Band-limit at both ends, around 500 Hz" | **MISSING** — 10 k + 33 nF C0G |
| Module-end 500 Hz band-limit RC | ADR 0003, same sentence | **MISSING** — 2.2 k + 150 nF film |
| Pitch output filter capacitor | ADR 0006 "ordinary series RC", 10–20 kHz (review V1 resolved 5 kHz) | **MISSING** — 33 nF C0G 1206 |
| Mod 1–4 output filter capacitors ×4 | ADR 0006 "~2 kHz" | **MISSING** — 82 nF film/C0G |
| Breath output filter capacitor | ADR 0006 / 0003 | **MISSING** |
| INA821/828 gain resistor R_G | ADR 0003 "absorbs the ~2.13× gain stage" | **MISSING**, and un-specifiable until INA821 vs INA828 is chosen |
| LT5400 surround resistors (pitch) | ADR 0006 | **MISSING** |
| Mod-channel gain-of-4 networks ×4 | ADR 0006 (which contradicts itself: LT5400 1:4 vs "ordinary 1% discretes") | **MISSING** |
| Pitch offset reference (−2.5 V) | Implied by `Vout = 2·Vdac − 2.5` | **MISSING** — and the obvious source (raw −12 V) is the wrong one |
| 74HC123 R_ext / C_ext | ADR 0004 "size N ... well under a second" | **MISSING** — 220 k + 1 µF film → 99 ms |
| TPS2553 R_ILIM, FAULT pull-up, EN pull-down/RC, I/O caps | ADR 0005 "adjustable limit" | **MISSING** — R_ILIM *is* the current limit |
| REF5050 input / output / NR capacitors | ADR 0003 | **MISSING** |
| MCP3202 VDD/VREF decoupling | Review R48: "the decoupling capacitor *is* the voltage reference" | **MISSING** |
| Carrier-board decoupling (OPA2197, 74AHCT125, REF5050) | ADR 0013 "Passives" | **MISSING** — `C-DECOUPLE` is module-only, `C-DECOUPLE-165` is registers-only |
| Bulk at the real-time board 5 V pin | ADR 0014 (matrix steps 160–960 mA) | **MISSING** |
| LM317 input capacitor | ADR 0004 "two resistors and two capacitors" | **MISSING** (only two caps are listed, both on ADJ/OUT) |
| Module +5 V clamp (5.6 V TVS) | Review R27, endorsed by verification pass V2 | **MISSING** |
| Module-end umbilical ESD | — nowhere | **MISSING** — only the instrument end has a TVS array |
| etherCON cable carriers NE8MC-1 | Review R38 | **MISSING** (not a passive, but the same gap) |

---

## 2. Findings

### Finding 1 — The anti-alias corner is 120 Hz, not 600 Hz, and it costs 1.3 ms of gate latency
**Severity: HIGH. Confidence: very high (arithmetic is unambiguous and both inputs are in the docs).**

ADR 0003 states: *"220 nF gives a ~600 Hz corner and **58 dB at 500 kHz**."* The same ADR
sets the divider at 10 k / 15 k. The Thévenin source impedance the cap sees is therefore:

```
R_th = 10 k ∥ 15 k = 6.00 kΩ
f_c  = 1 / (2π × 6000 × 220e-9) = 1 / (8.294e-3) = 120.6 Hz
```

Not 600 Hz. The 600 Hz figure back-solves to a **1.21 kΩ** source:

```
R = 1 / (2π × 600 × 220e-9) = 1206 Ω
```

That is the pre-R49 divider — the one Microchip's "source impedance below ~1 kΩ" rule
wanted. Review R49 then raised the upper leg to ≥10 kΩ for ESD-clamp reasons (correctly),
and **nobody recomputed the corner.** Review finding V4 even noticed R11 and R49 pull in
opposite directions and declared R39's capacitor "the keystone that resolves both" —
without checking what corner it now produces.

Three consequences:

- **Signal loss.** The sensor has ~159 Hz of real bandwidth. At 159 Hz a 120.6 Hz pole
  gives `1/√(1 + (159/120.6)²) = 0.604` → **−4.4 dB**. The digital copy is materially
  slower than the analog CV at the jack, which is the opposite of what is wanted since
  the *gate* runs off the digital copy.
- **Unbudgeted latency.** `τ = R_th·C = 6000 × 220e-9 = 1.32 ms`. For a ramp input — which
  is what a tongue attack is — a single pole adds ~τ of delay. The latency budget's
  digital-copy total is ~2.6–2.9 ms; this pushes it to **3.2–4.2 ms** against a 5 ms
  target. The budget table has no row for it.
- **A false claim about settling.** ADR 0003 says *"Together with the divider it settles
  well inside the 250 µs loop period."* A 1.32 ms time constant needs 8.3τ ≈ **11 ms** to
  settle to 12 bits — 44 loop periods. The ADR conflates the *sample-capacitor acquisition*
  (which the 220 nF reservoir does handle) with the *network's* settling (which it does
  not). Both sentences are in the same paragraph.

On the alias side the cap over-delivers: at 120.6 Hz the rejection at 500 kHz is
`20·log10(500000/120.6) = 72.4 dB`, not 58 dB. So the design is paying 1.3 ms for 14 dB
it did not ask for.

**Change to 47 nF, C0G, 1206, 50 V, ±5%.**

```
f_c = 1/(2π × 6000 × 47e-9)   = 564 Hz     ← the ~600 Hz the ADR claimed
τ   = 6000 × 47e-9            = 282 µs     ← ~one loop period, and explicit
atten @500 kHz = 20·log10(500000/564) = 58.9 dB  ← the 58 dB the ADR claimed
```

47 nF delivers *exactly* the two numbers ADR 0003 asserts. It also sits at the same
~500 Hz the rest of the design band-limits to, which makes the digital and analog breath
paths agree instead of diverging.

Reservoir check, since the cap has a second job: MCP3202's sample capacitor is ~20 pF.
Charge sharing gives `20p/47n = 0.043%` of droop — about 1.8 LSB at 12 bits, constant, and
absorbed by calibration. Steady state with incomplete recharge (`1 − e^(−250/282) = 58.8%`)
lands near 0.073%. Irrelevant for a breath threshold and a 7-bit MIDI CC.

**Dielectric matters here and X7R is the wrong choice regardless of value.** X7R is
ferroelectric: it is piezoelectric (microphonic) and has a voltage coefficient that moves
the corner with signal level. This is a wind instrument that is held, tapped and blown
into, with the sensor board at the bottom next to the umbilical strain relief. C0G has
neither property. 47 nF C0G is readily available in 1206/50 V — 220 nF C0G is not made in
either package, which is a second, independent argument for the lower value.

---

### Finding 2 — Every output reconstruction capacitor is missing, on six channels
**Severity: HIGH. Confidence: very high (they are simply not in the BOM).**

ADR 0006 specifies corner frequencies for all six outputs and ADR 0006 states the pitch
filter *"stays an ordinary series RC"* whose *"corner is set by its own R and C and nothing
else."* The R exists (`R-OUT-PROT`, 1 kΩ, qty 6). **The C does not appear anywhere in the
BOM.** Six filters, six missing capacitors, and each one sets a corner the documents argue
about at length.

With the 1 kΩ already fixed by the short-protection decision, the values follow directly:

| Channel | Target corner | C from `1/(2πRC)` with R = 1 kΩ | Specify |
|---|---|---|---|
| Pitch | 5 kHz (review V1 resolved the 10–20 kHz vs 2–5 kHz argument) | 31.8 nF | **33 nF C0G, 1206, 50 V, ±5%** → 4.82 kHz |
| Mod 1–4 | ~2 kHz | 79.6 nF | **82 nF PPS or PET film, 1206/THT, ≥50 V** → 1.94 kHz |
| Breath | ~500 Hz (ADR 0003) | 318 nF | **330 nF PET film, ≥50 V** → 482 Hz |

Verification that 33 nF on pitch actually meets the requirement, restated as settling time
the way review V1 asked:

```
τ = 1 kΩ × 33 nF = 33 µs
Full-range 9 V step settling to 1 cent (0.833 mV):
t = τ · ln(9000 mV / 0.833 mV) = 33 µs × 9.29 = 307 µs
```

307 µs against a glide-perception threshold in the tens of milliseconds. The review's own
figure for a 5 kHz corner was 296 µs — same answer.

**Dielectric is not optional on these.** These capacitors sit directly in the CV signal
path at ±10 V.

- **Pitch: C0G, no exceptions.** An X7R here is a microphonic element on the one channel
  calibrated to fractions of a cent — the module would literally detune when the rack is
  knocked. It is also a voltage-coefficient nonlinearity, i.e. the corner would move with
  the note being played.
- **Mod 1–4 at ±10 V: film, not X7R.** An 82 nF 50 V X7R 0805 loses roughly 20% of its
  capacitance at 10 V bias, so the corner walks with the modulation. C0G at 82 nF needs
  1210; a PPS or PET film part in 1206 or through-hole is cheaper, smaller-drift and
  perfectly available. For a one-off where cost is a minor consideration, film is the
  obvious call.
- **Breath at 330 nF: film.** Same reasoning, and this is the channel the whole AGND
  argument exists to protect.

Op-amp stability is unaffected: the 1 kΩ isolates the capacitance from the OPA2197's
output, which is precisely why ADR 0006 declined the in-loop dual-feedback version. Drive
check on the worst channel — a mod output at 20 V p-p, 2 kHz — is
`20 V / |1 kΩ + 1/(j2π·2000·82n)| = 20/1.39 kΩ = 14 mA peak`, inside the OPA2197's linear
output range, and mod sources top out near 400 Hz anyway.

---

### Finding 3 — `R-PD-BREATH` gives the in-amp no bias-current return, so an unplugged umbilical slams the breath output to a rail
**Severity: HIGH. Confidence: high.**

ADR 0005: *"Pull down the module's breath receive input, so that an instrument which is
switched off — **or unplugged** — presents 0 V rather than a floating buffer output."*
ADR 0003 then correctly refines it: *"Put the pulldown differentially across BREATH–AGND,
not on one leg"* — right for CMRR, because a 100 kΩ on +IN alone caps CMRR near 19 dB.

But a purely differential 100 kΩ defines only the *difference* between the in-amp's inputs.
It defines nothing about their **common-mode** potential. With the etherCON unplugged, both
INA821 inputs are connected to 100 kΩ, to each other, and to nothing else. An
instrumentation amplifier's input bias currents have no return path, the inputs charge
toward a rail, the input stage leaves its common-mode range, and the output saturates.
On a ±12 V module that is roughly **+11.9 V at the breath jack with no instrument
connected** — the precise failure ADR 0005 added the resistor to prevent, in the precise
state (unplugged) it names.

This is a classic in-amp application error and it is invisible on a netlist, in the same
way R35's AGND-bonding issue was.

**Fix: add two 1 MΩ 1% 0805 resistors, one from each in-amp input to module ground**,
keeping the 100 kΩ differential resistor. Symmetric, so with an in-amp's GΩ inputs there
is no CMRR penalty. The R35 rule (*"AGND connects to the receiver's inverting input and
nothing else"*) is not violated in substance: at 1 MΩ the AGND-to-module-ground path
carries `58.9 mV / 1 MΩ = 59 nA` of the instrument's return current, against the ~97 mA
R35 was written to prevent. Worth adding a sentence to ADR 0003 saying why 1 MΩ is allowed
where a ground pour is not.

**Second, smaller point on the same resistor.** With the (missing) series protection
resistor at the instrument end, the 100 kΩ differential pulldown forms a divider:

```
10 kΩ series → attenuation 100/(100+10) = 0.909   → 9.1% gain loss
 1 kΩ series → attenuation 100/(100+1)  = 0.990   → 1.0% gain loss
```

ADR 0003 sizes the in-amp at 2.13× to map 4.7 V → 10 V, with no allowance for this. It is
absorbed by the panel gain knob, so it is not a fault — but it is another reason to use
**1 kΩ, not 10 kΩ**, for the protection resistor. With the buffer moved to +12 V there is
no fault current to limit (ADR 0003's own argument), so the resistor's only remaining job
is ESD and short-circuit limiting, which 1 kΩ does fine.

---

### Finding 4 — `R-REG-SET` worst case puts 5.62 V on a DAC rated 5.5 V
**Severity: MEDIUM-HIGH. Confidence: high.**

The nominal arithmetic in the BOM is correct:

```
Vout = 1.25 × (1 + 768/240) = 1.25 × 4.2 = 5.250 V   ✓
```

The BOM's worst case is not. It applies ±4% to the *output* (`5.04–5.46 V`) rather than
propagating the LM317's ±4% reference tolerance, the resistors' ±1% each, and the ADJ pin
current, which the datasheet equation includes:

```
Vout = Vref × (1 + R2/R1) + I_ADJ × R2

Worst high: Vref 1.30, R2 = 768 × 1.01 = 775.7, R1 = 240 × 0.99 = 237.6, I_ADJ = 100 µA
          = 1.30 × (1 + 3.265) + 100e-6 × 775.7
          = 5.544 + 0.078 = 5.622 V

Worst low:  Vref 1.20, R2 = 760.3, R1 = 242.4, I_ADJ = 50 µA
          = 1.20 × (1 + 3.137) + 0.038 = 5.002 V
```

**5.62 V is outside the DAC8568's 5.5 V recommended operating maximum** (inside the 6 V
absolute maximum, so it will not destroy the part — it will operate out of spec, which for
a channel calibrated against a VCO is worse than a clean failure).

The low end, 5.00 V, is fine against the requirement: the used DAC window tops at 4.75 V
and the part needs ~200 mV of headroom, so ≥4.95 V is the floor.

The structural problem is that the allowed window is barely wider than the LM317's own
tolerance:

```
Need:  Vn × 1.045 ≤ 5.50  →  Vn ≤ 5.26 V
       Vn × 0.955 ≥ 4.95  →  Vn ≥ 5.18 V
```

An **80 mV window** for a regulator whose reference alone spans 8%. 5.25 V happens to sit
inside it, so the choice is near-optimal — but there is effectively zero design margin,
and I_ADJ pushes the top out.

**Preferred fix, and it uses a part number already in this BOM: delete the LM317LZ and
`R-REG-SET`, and run the DAC's AVDD from a second REF5050 buffered by half an OPA2197** —
identical to the arrangement ADR 0003 already specifies for the breath sensor. That gives
5.000 V ±0.05%, 3 ppm/°C, 250 mV of headroom above the 4.75 V window exactly as designed,
and removes a tolerance stack from underneath the pitch calibration. DAC8568 AVDD current
is ~1–3 mA against the REF5050's 10 mA and the buffer's much more. It also matches the
project's stated "one part number beats saving a few dollars on a one-off" principle.

**Fallback if the LM317 stays:** select R2 on test (this is a one-off with a full bench),
or split R2 into a fixed 750 Ω plus a selected trim, and measure AVDD before fitting the
DAC.

**Two smaller corrections in the same area:**

- The divider's *tempco* does not matter and should not be over-specified. AVDD sets only
  the output headroom, not the DAC's full scale, which comes from the internal 2.5 V
  reference. Ordinary 1% thick-film 0805 is correct; do not pay for thin film here.
- The BOM's dissipation figure is internally inconsistent: *"~5 mA load, 135 mW."* At
  5 mA, `(12 − 5.25) × 5 mA = 34 mW`. Including the 5.2 mA divider current and the DAC's
  ~3 mA it is `6.75 V × 13 mA = 88 mW`. Either way a TO-92 is untroubled. (Useful side
  check: the 240 Ω leg draws `1.25/240 = 5.2 mA`, which satisfies the LM317L's ~3.5 mA
  minimum load requirement on its own — that part of the choice is right and deliberate.)

---

### Finding 5 — `R-OUT-PROT` is over its power rating in exactly the fault it exists for
**Severity: MEDIUM. Confidence: high.**

The value is correct and the reasoning behind keeping it at 1 kΩ (ADR 0006's whole
"pure gain error, the trimmer has full authority" argument) is sound. The **package** is not.

```
Output at a rail, shorted to ground:
  P = (11.9 V)² / 1 kΩ = 141 mW

Output-to-output patching, +10 V against −10 V:
  I = 20 V / 2 kΩ = 10 mA  →  P = (10 mA)² × 1 kΩ = 100 mW each
```

A standard 0805 thick-film is rated **125 mW**. 141 mW is 113% of rating, and the BOM's own
note says the part exists to *"survive shorts and output-to-output patching"* — i.e. this
is a sustained condition, not a transient.

**Change to 1206 (250 mW), 1%, thick film, ≥100 V working.** The BOM already uses 1206 for
`F-POLY` and the ferrites, so nothing is lost. A 0.25 W-rated 0805 (e.g. a high-power
series) is an acceptable alternative if board area is tight.

**Tolerance and tempco are fine and worth confirming explicitly**, because it looks like
they should matter on pitch and they do not. With a 100 kΩ VCO load:

```
D = 100k/(100k + 1k) = 0.990099
dD/D = −(1k/101k) × (dR/R)
At 100 ppm/°C over 10 °C, dR/R = 1000 ppm:
dD/D = −9.9 ppm  →  at 7 V, 69 µV  →  69 µV / 833 µV-per-cent = 0.083 cents
```

0.08 cents over 10 °C. Ordinary 1% thick film with ±100 ppm/°C is entirely adequate; the
divider's *nominal* error is the thing that matters and calibration removes it exactly, as
ADR 0006 argues. **KEEP the value, KEEP 1%, change only the package.**

---

### Finding 6 — `F-POLY` will current-limit during normal play
**Severity: MEDIUM-HIGH. Confidence: high. This was raised as R17 and never actioned.**

Review R17 said the 500 mA part is undersized, unrated for voltage, and in the wrong place.
The resolution log does not list it among the eight decisions and the BOM line is unchanged.

Against the review's own corrected budget (V1: *"300 mA typical, 600 mA peak, ~1.25 A
ceiling"*; R15: *"410–430 mA typical"*):

- 500 mA hold vs 410–430 mA typical = **1.0–1.2×**. Standard practice is ≥2×.
- PPTC hold derates roughly **−0.5%/°C**. ADR 0014 establishes a 10–20 K interior rise, so
  the effective hold falls to ~450–475 mA — **below the typical draw**, before any WiFi
  transient.
- Series resistance is the unbudgeted part. A 1206 500 mA PPTC has `R_init` around
  0.25–0.9 Ω and `R_1max` up to ~1.5 Ω. At 430 mA that is **0.11–0.39 V normally and up to
  0.65 V after any trip event** — against the 84 mV of cable drop that the entire
  "send 12 V not 5 V" argument in ADR 0005 was built on. And per review V3, the WS2815
  strips hang on unregulated +12 V downstream of it, so they eat that drop directly (the
  buck regulates its own away).
- **No voltage rating is specified.** Many 1206 PPTCs are 6 V parts. A 6 V PPTC on a 12 V
  rail fails destructively when it trips, because it cannot hold off the rail in its
  latched high-resistance state.

This is also the exact device in ADR 0014's positive-feedback brownout loop — and ADR 0014
argues the load switch *replaces* "a slow, self-heating, thermally-hysteretic protection
device," while ADR 0005 keeps the polyfuse as "complementary." Whichever is intended, the
part as specified is undersized.

**Change to: PPTC, 1812 package, 1.1 A hold / 2.2 A trip, ≥16 V (24 V preferred),
R_init ≤ 0.1 Ω.** Littelfuse 1812L110/16 class. At 16 V you cannot get ≥1 A hold in 1206 —
1812 is the smallest package that meets both, and the BOM's own rationale for 1206 over
0603 ("easier to place and inspect") argues for it. Drop at 430 mA becomes ~43 mV, which
is inside the original cable-drop budget rather than five times it.

---

### Finding 7 — The TPS2553 limit and the instrument's bulk capacitance are incompatible
**Severity: MEDIUM. Confidence: medium-high (depends on the final bulk total).**

The BOM says *"Adjustable limit set ~500 mA."* Two problems.

**The limit is below the load.** Typical draw is 410–430 mA with 600 mA WiFi peaks. A
500 mA limit trips on radio bursts. The programming resistor follows from the datasheet
relation (I_OS in mA, R_ILIM in kΩ):

```
R_ILIM = 16,100 / I_OS
  500 mA →  32.2 kΩ   (too low a limit)
  1.2 A  →  13.4 kΩ   ← recommend, ~2× typical, ~1.5× WiFi peak
```

**R_ILIM is not in the BOM at all.** It is the component that *is* the current limit, and
it needs to be 1% — the TPS2553's limit accuracy is already ±10–20% and a 5% resistor makes
it worse. Also missing: the FAULT open-drain pull-up (10 kΩ to +5 V), an EN pull-down
(10 kΩ) plus RC debounce for `SW-POWER` (a bouncing toggle restarts the soft-start ramp
repeatedly), and the datasheet's input/output capacitors.

**Startup dissipation.** The instrument's bulk is `C-STRIP-BULK` ×2 plus `C-BULK-DISP`
plus the buck input capacitor:

```
2 × 1000 µF + 470 µF + ~220 µF ≈ 2.7 mF
Constant-current charge at 500 mA:  t = C·V/I = 2.7e-3 × 12 / 0.5 = 65 ms
Average dissipation in the switch:  ½ × 12 V × 0.5 A = 3 W for 65 ms
```

3 W in a SOT-23-6 for 65 ms is close to thermal shutdown, and an auto-retry variant would
hiccup indefinitely. **Hold the total instrument bulk to ≤1.5 mF** (470 µF per strip feed
rather than 1000 µF — see Finding 8 for why 470 µF is already sufficient) and raise the
limit to 1.2 A: `1.5e-3 × 12 / 1.2 = 15 ms` at ~7 W peak / 3.5 W average, which is a
survivable transient.

---

### Finding 8 — `C-STRIP-BULK` is under-rated for a part that can never be replaced
**Severity: MEDIUM. Confidence: high.**

The **value** is right and the reasoning ("bulk belongs where the current swings, a ferrite
is a wire at 2 kHz") is correct. Checking it against the load:

```
One strip, 25 LEDs, worst-case full white ≈ 0.5 A, 2 kHz PWM, 50% duty:
ΔQ = 0.5 A × 250 µs = 125 µC
470 µF  → ΔV = 125e-6 / 470e-6 = 0.27 V
1000 µF → ΔV = 0.13 V
```

0.27 V of ripple on a 12 V LED rail is fine, so **470 µF is sufficient** — which also helps
Finding 7. ESR at 2 kHz matters more than capacitance: at 0.2 Ω a 0.5 A swing adds 0.1 V.

The **rating and type** are wrong for the environment:

- **16 V on a 12 V rail is 1.33×.** Standard practice on a 12 V rail is 25 V. This part
  sits inside a laminated body that ADR 0002 and ADR 0009 say cannot be reopened.
- **No temperature class.** ADR 0014 establishes 10–20 K of interior rise, so the capacitor
  runs at 45–55 °C ambient. An 85 °C part at 50 °C has perhaps 5,000–10,000 hours; a 105 °C
  part at the same temperature has roughly an order of magnitude more. Electrolytic drying
  out is the single most likely long-term failure in a sealed instrument, and it is the one
  failure you cannot get at.
- **No ripple-current rating.** A 0.5 A square at 2 kHz is ~0.25 A RMS; at 2 kHz most
  datasheet ripple figures (quoted at 100 kHz) derate by ~0.7.

**Specify: 470 µF, 25 V, 105 °C, low-ESR (≤0.2 Ω at 100 kHz), ≥500 mA ripple at 100 kHz,
radial THT, ×2.** Nichicon UPW/PW or Panasonic FR class.

---

### Finding 9 — `L-BUCK-IN` is an inductor with no capacitor, and the LC lands on the aggressor
**Severity: MEDIUM. Confidence: medium-high.**

ADR 0004 is right that *"a real LC ... is the component that does the job the bead was
credited with."* But the BOM line specifies only the L. **The C of the LC is not specified
anywhere**, and neither is any damping.

Two things need pinning down.

**Rating ambiguity.** "≥1 A" does not distinguish saturation current from RMS current, and
for a power inductor they are different specs with different consequences. The instrument
draws 300–430 mA typical but the load switch can pass 1.2 A during startup and fault.
**Specify I_sat ≥ 1.5 A and I_rms ≥ 1 A, shielded, DCR ≤ 0.15 Ω.** DCR is not a footnote:
at 0.3 Ω (typical of a small 47 µH part) it costs `0.43 A × 0.3 Ω = 130 mV`, on a rail
whose entire original drop budget was 84 mV.

**Resonance.** With no C specified, take a plausible 100 µF:

```
f_0 = 1/(2π√(47e-6 × 100e-6)) = 2.32 kHz
Z_0 = √(L/C) = √(0.47) = 0.686 Ω,  Q = Z_0/DCR = 2.3 at 0.3 Ω
```

**2.3 kHz with a Q of 2.3 sits directly on the WS2815's ~2 kHz PWM rate** that ADR 0004 and
ADR 0014 both identify as the dominant low-frequency disturber. An undamped LC there
*amplifies* the thing it was added to suppress. (The LEDs are upstream of this LC, on raw
+12 V — but the LC's input node is the shared umbilical node, so the peaking appears there
and propagates back down the cable.) It is also the textbook Middlebrook input-filter
instability condition for the buck downstream.

**Specify: L = 47 µH shielded, I_sat ≥ 1.5 A, DCR ≤ 0.15 Ω; C = 470 µF 25 V 105 °C
electrolytic; plus a damping branch of 100 µF 25 V in series with 1 Ω.** That puts

```
f_0 = 1/(2π√(47e-6 × 470e-6)) = 1071 Hz
```

below the 2 kHz aggressor, and the damping branch flattens the peak. Attenuation at the
buck's ~500 kHz switching frequency is `(500000/1071)² ≈ 218,000` → >100 dB ideal, far more
than needed, so the corner can safely be this low.

---

### Finding 10 — Ferrite beads: the rating is still below the current, and no impedance is specified
**Severity: MEDIUM. Confidence: high.**

ADR 0004 and ADR 0006 both correct the original 0805/600 Ω/300 mA choice to *"≥1 A, 1206 or
1210."* The correction is right in direction and still short in magnitude:

- The +12 V umbilical branch passes up to **1.2 A** during the load switch's constant-current
  startup and fault limiting (Finding 7). A bead rated at exactly 1 A saturates there, and
  ADR 0006's own warning applies: *"a saturated bead does not degrade gracefully — it loses
  its impedance entirely."* **Specify ≥2 A** on that branch. It costs nothing: a 2 A 1206
  bead has DCR around 25–50 mΩ, i.e. `0.43 A × 0.04 Ω = 17 mV`, versus the 0.64 V the ADR
  rejected the series resistor over.
- **No impedance value is given at all.** A ferrite bead is specified by Z at 100 MHz, and
  it is the only number that says what the part does. "≥1 A" describes a rating, not a
  function. Note also that high-current beads are inherently lower impedance — you cannot
  get 1 kΩ at 2 A in 1206. **Specify: 600 Ω @ 100 MHz, 2 A, DCR ≤ 50 mΩ, 1206** for the
  two +12 V branches; 220–600 Ω @ 100 MHz, 1 A, 1206 for −12 V and +5 V is sufficient.
- **The 470 µF has no voltage rating** and it sits on ±12 V. **Specify 35 V, 105 °C.** 25 V
  is only 2× on a rail that can sit at 12.6 V with transients; 35 V is the conventional
  choice and costs cents. Watch polarity on the −12 V branch.
- **Quantity is ambiguous** — qty 4 for a line item described as "bead + 470 µF per branch"
  could mean 4 beads, or 4 assemblies, or 4 parts total. There are four branches, so it
  needs 4 beads and 4 capacitors, i.e. 8 parts.
- **4 × 470 µF = 1.88 mF of module entry capacitance** is large by Eurorack standards and
  is exactly the inrush review R9 flagged. The op-amp branch draws ~45 mA and does not need
  470 µF; **use 100 µF on the +12 V analog, −12 V and +5 V branches and keep 470 µF only on
  the umbilical branch**, dropping the total to 770 µF.

One thing the ADR gets right and is worth confirming with numbers, because the ADR itself
calls it "survivable by accident": at 2 kHz a 470 µF has `|Z| = 1/(2π·2000·470e-6) = 0.17 Ω`
plus ~0.1 Ω ESR, so a 400 mA LED swing puts ~110 mV on the shared node; OPA2197 PSRR at
2 kHz is ~90 dB, giving `110 mV × 10^(−90/20) = 3.5 µV` at the output. Against a 153 µV LSB
that is genuinely negligible. **The branching topology is fine; only the part specs need
tightening.**

---

### Finding 11 — `R-MOSI-SER` at 220 Ω is not source termination
**Severity: LOW-MEDIUM (functional risk is low at 0.6 MHz; the stated purpose is not met).
Confidence: high on the arithmetic.**

ADR 0004: *"220 Ω in series on MOSI at the driving end. **Source termination** on the one
line that runs the full umbilical carrying data."* Source termination means
`R_s + Z_out ≈ Z_0`. Cat5e is 100 Ω; an ESP32-S3 GPIO is ~25–40 Ω at default drive. The
correct value is therefore **60–75 Ω**. At 220 Ω:

```
Launched wave:  V₁ = 3.3 × 100/(100 + 220 + 35) = 0.930 V
Far end (open): 2 × 0.930 = 1.86 V   ← below the 74AHCT125's 2.0 V V_IH
Source reflection coefficient: (255 − 100)/(255 + 100) = 0.437
Next step:  1.86 + 2×0.437×0.930 = 2.67 V
Then:       3.03 V, 3.18 V, 3.23 V ...
One-way delay on 2 m at 0.65c: 10.2 ns; round trip 20.5 ns
```

So the far end takes **two round trips (~41 ns) just to reach a valid logic high** and
~80 ns to settle, arriving as a staircase that crawls through the receiver's threshold
region. At 0.6–1 MHz (500–830 ns per half-cycle) this is not a functional failure, which is
why I rate it low-medium. But it is the opposite of what the ADR says it does, it puts a
slow edge into a plain buffer that ADR 0004 itself notes *"is not a Schmitt trigger,"* and
it skews MOSI ~40–80 ns late relative to SCLK — which has **no series resistor at all**,
despite being the fastest edge in the system and the one ADR 0004's pin assignment goes to
some lengths to isolate.

**Change to 68 Ω, 1%, 0805, and fit the same part on SCLK and CS at the driving end
(qty 3).** `68 + 35 = 103 Ω ≈ 100 Ω` gives a single full-amplitude step at the far end with
no staircase and no reflection back. 1% is over-specified for termination — 5% is fine, but
1% costs nothing and keeps one tolerance across the BOM.

If E11 shows the MOSI→CS crosstalk review R36 predicts (both share pins 4,5), the right
answer is to reduce the S3's GPIO drive strength (free, and review V1 notes nobody
mentioned it) or add a small shunt capacitor at the module end of CS — not to mistune the
termination.

---

### Finding 12 — `R-TERM-CHAIN`: 33 Ω is right only for a GPIO setting nobody has specified
**Severity: LOW-MEDIUM. Confidence: medium (loom Z₀ is an estimate until measured).**

Same relation as Finding 11. An unshielded loom with a dedicated ground return per signal
(which ADR 0001 correctly makes item 1 on its list) has Z₀ around 100–150 Ω.

```
Default S3 drive (20 mA setting):  Z_out ≈ 25 Ω  →  R_s = 75–125 Ω
Low S3 drive (5 mA setting):       Z_out ≈ 80 Ω  →  R_s = 20–70 Ω
```

So the BOM's 33–68 Ω is correct **only** with the drive strength reduced, and badly
under-terminated at the default setting. Since ADR 0001 keeps 74LVC specifically because
its fast edges are safe *"with item 4 above, the series termination,"* the drive-strength
setting is load-bearing and belongs in the ADR.

**Specify 68 Ω 1% 0805 plus `GPIO_DRIVE_CAP` set low in firmware**, or 100 Ω 1% at default
drive. Measure Z₀ at E4 and settle it.

**Quantity should be 3, not 2.** SCK and SH/LD are driven by the MCU and get terminated at
the MCU. The QH return from the **last** register in the chain also runs the full body
length, is driven by a 74LVC165's ±24 mA totem-pole output, and is the line that gets
sampled — ADR 0001's own analysis of the ordering ("data flows toward the clock source")
shows the author knows this line exists. It needs its own 68 Ω at the far satellite board.

---

### Finding 13 — `R-SPI-PULL` backfeeds the instrument through an ESD diode in the normal off state
**Severity: LOW-MEDIUM. Confidence: high.**

ADR 0004's analysis of the floating-input problem is correct and the fix is right in kind.
The value has a side effect the ADR does not consider.

The module's *normal* state is "module alive, instrument off" — ADR 0004 says so explicitly
and calls it *"the state the instrument spends most of its life in."* In that state, CS is
pulled to **+5 V through 10 kΩ at the module**, and the other end of the CS conductor is an
ESP32-S3 GPIO that is **not 5 V tolerant** on a board whose 3V3 rail is at 0 V:

```
I = (5 V − 0.7 V ESD diode − 0 V) / 10 kΩ = 430 µA
```

430 µA continuously into the S3's ESD structure and out onto an unloaded 3V3 rail. It will
not destroy anything (the S3's clamp handles milliamps and the LVC165s/MCP3202 have 6.5 V
and 7 V absolute maxima), but it partially energises the instrument's 3.3 V rail through a
parasitic path, to an undefined voltage, whenever the module is powered and the instrument
is not. That is a poorly-defined power state on a board that also carries the ADC whose
VDD *is* its voltage reference.

**Change the CS pull-up to 100 kΩ, 0805.** Backfeed drops to 43 µA. The 74AHCT125's input
leakage is ±1 µA maximum (typically <100 nA), so 100 kΩ holds the input at worst 0.1 V from
the rail — comfortably inside V_IH. The OE gating from +12 V presence, which ADR 0004
already specifies, is the real defence; the pull only has to stop the input floating.

**SCLK and MOSI at 10 kΩ to ground are fine** — pull-downs create no backfeed path, and the
DC load on the driving GPIO is `3.3 V / 10 kΩ = 330 µA`, trivial. Worth confirming the
interaction with Finding 11's series resistor: with 68 Ω series and a 10 kΩ pull-down, the
AHCT input sees `3.3 × 10000/10068 = 3.28 V`, against V_IH of 2.0 V. No issue. (With the
current 220 Ω it is 3.23 V — also fine.)

1% is unnecessary on all three; 5% would do.

---

### Finding 14 — `TRIM-PITCH` has no value, and its offset reference is an undeclared noise path
**Severity: MEDIUM-HIGH for the reference question, UNDERSPECIFIED for the rest.
Confidence: high.**

The BOM says *"multiturn cermet trimmer, 5-10% of ratio"* — a trim *range*, not a part.
Missing: resistance, turns count, tempco, tolerance, and — the important one — **what the
offset trimmer is referenced to.**

**The reference source is a real gap, not a detail.** The pitch transfer function is
`Vout = 2 × Vdac − 2.5 V` (gain 2 from the 0.25–4.75 V window into −2…+7 V; the LT5400's
equal resistors give exactly 2). That requires a **−2.5 V** offset, and there is no −2.5 V
reference anywhere in the BOM. The obvious construction — a divider from the −12 V rail —
is precisely the mistake review R26 flags for the *breath* offset pot and which the
verification pass kept as *"correct and important."* Nobody applied it to pitch, which is
the channel that actually matters:

```
Rack −12 V ripple (typical Eurorack, 100/120 Hz): ~20–50 mV p-p
Divider attenuation to −2.5 V: 2.5/12 = 0.208
Ripple at the offset node: 4.2–10.4 mV
On pitch, at 0.833 mV per cent:  5–12 cents of rail-correlated wander
```

Five to twelve cents, on a channel where the LT5400 was bought to fight 5.4 cents and the
matched network's own contribution is 0.11 cents. It would present as tuning that moves
when another module in the case draws current — the worst class of fault to diagnose.

**Fix: derive the pitch offset from the DAC8568's own buffered 2.5 V `VREFOUT`**, inverted
by one OPA2197 half to −2.5 V, with the trimmer adjusting around it. That also makes the
offset track the same reference as the gain, which is the argument ADR 0006 already makes
for the mod channels' DAC-sourced offset. A dedicated LM4040-2.5 or REF5025 is the
alternative. It is *not* a second offset authority — ADR 0006's "no split brain" rule is
about two *adjustable* authorities in series, and this is a fixed reference the single
trimmer sits on top of.

**Values.** With an LT5400 at 10 kΩ per element:

- **Scale trimmer: 1 kΩ**, 25-turn cermet, in series with the feedback element → ±10% of
  gain. Resolution: 25 turns over 10% is 0.4% per turn; a careful quarter turn is 0.1%,
  which at 5 octaves is `5 V × 0.001 = 5 mV = 6 cents`. Multiturn is correctly specified —
  a 3-turn part would not resolve this.
- **Offset trimmer: 10 kΩ**, 25-turn cermet, as a divider on the buffered −2.5 V.

**Tempco should be specified, and it buys about a third of the error back.** ADR 0006's
table implies a 250 ppm/°C trimmer:

```
Net ratio tempco = (1 − f)·T_fixed + f·T_trim,  T_fixed = 10 ppm/°C
f = 0.10, T_trim = 250:  0.9×10 + 0.1×250 = 34 ppm/°C   ← the ADR's figure ✓
f = 0.05, T_trim = 250:  0.95×10 + 0.05×250 = 22 ppm/°C ← the ADR's figure ✓
```

The ADR's arithmetic is correct and self-consistent (22 ppm/°C × 10 °C × 9 V = 1.98 mV =
2.4 cents ✓). But a **±100 ppm/°C** cermet is a stock part at the same price:

```
f = 0.10, T_trim = 100:  0.9×10 + 0.1×100 = 19 ppm/°C → 190 ppm × 9 V = 1.71 mV = 2.05 cents
f = 0.05, T_trim = 100:  0.95×10 + 0.05×100 = 14.5 ppm/°C → 1.31 mV = 1.57 cents
```

**Specify: 25-turn sealed cermet, ±10% tolerance, ≤100 ppm/°C, top-adjust, through-hole
(Bourns 3296W or 3266W class). 1 kΩ for scale, 10 kΩ for offset.** Sealed matters — this is
a module that lives in a rack and gets handled.

---

### Finding 15 — `R-PRECISION`: no value, no ratio, no grade, no quantity, and ADR 0006 contradicts itself on where it goes
**Severity: MEDIUM. Confidence: high.**

The BOM calls it *"the highest-value precision part in the design"* and then specifies
neither the resistance, the ratio variant, the grade, nor the quantity ("TBD").

**Grade is not optional.** ADR 0006's entire precision argument rests on one number:
*"Matched network, 1 ppm/°C tracking → 0.09 mV → 0.11 cents."* Verified:
`1 ppm/°C × 10 °C × 9 V = 90 µV; 90 µV / 833 µV-per-cent = 0.108 cents` ✓. But 1 ppm/°C
tracking is the **A grade** (0.01% matching). The C and D grades are several times worse and
carry the same "LT5400" name — the identical trap ADR 0006 spends a section on for the
DAC8568's grade letter. **Specify LT5400A**, and the BOM's own instruction — *"Specify the
full orderable part number ... The grade letter is the whole decision and it is invisible
in the generic name"* — should be repeated verbatim on this line.

**Value: 10 kΩ**, 1:1 quad (LT5400A-2 class), MSOP-8. 10 kΩ balances Johnson noise
(12.8 nV/√Hz, negligible over a 5 kHz pitch bandwidth) against the OPA2197's 10 pA bias
current (100 nV of offset). 1 kΩ loads the DAC unnecessarily; 100 kΩ raises noise and makes
leakage matter.

**Quantity depends on an unresolved contradiction in ADR 0006.** The mod-channel section
says *"Gain of 4 is a 1:4 ratio, **which the LT5400 family offers directly** — no external
resistor, so no absolute tempco leaks into the gain."* The calibration section says
*"Channels 2–6 run on ordinary 1% discretes."* These cannot both be built. Either is
defensible — the mod channels only need to be linear and repeatable, and firmware has both
`a` (scaling) and `b` (the ch7 DAC offset), so 1% discretes are genuinely sufficient — but
the documents must pick one, and if it is the discrete route then **16 resistors (4 per mod
channel) are missing from the BOM.**

For the discrete route, specify: 4× (10 kΩ + 40 kΩ) per channel, 0.1% thin film, 25 ppm/°C,
0805. That gives gain 4 ± 0.2% before firmware, against ±2% for 1% parts. At a few cents of
cost on a one-off, 0.1% is the easy call.

**Related, and minor:** the DAC internal reference's contribution (0.54 cents) is computed
from the **typical** 5 ppm/°C. Check the DAC8568 datasheet's *maximum* drift for the chosen
grade before relying on it — at 30 ppm/°C the contribution is `300 ppm × 9 V = 2.7 mV =
3.24 cents`, comparable to the trimmer rather than an order of magnitude below the
resistors, which would change ADR 0006's conclusion that *"a separate precision reference
buys nothing measurable."*

---

### Finding 16 — `C-DECOUPLE` quantity is roughly half what the note requires, and "ceramic" is not a dielectric
**Severity: MEDIUM. Confidence: high.**

The note says *"One per supply pin, close to the pin."* Counting the module's supply pins:

| IC | Supply pins | 100 nF needed |
|---|---|---|
| OPA2197 × 5 | V+ and V− each | **10** |
| INA821/828 | V+, V− | 2 |
| DAC8568 | AVDD (+ DVDD if separate) | 1–2 |
| 74AHCT125 | VCC | 1 |
| 74HC123 | VCC | 1 |
| LM317LZ | IN | 1 |
| TPS2553 | IN, OUT | 2 |
| **Total** | | **18–19** |

The BOM says **10**. The five dual op-amps alone account for ten. **Change qty to 20.**

**Dielectric and voltage rating are unspecified.** "100 nF ceramic" spans C0G, X7R, X5R,
Y5V and Z5U, and the last two lose most of their capacitance over temperature. For
decoupling, **X7R is correct** (C0G at 100 nF is 1206+ and unnecessary here). Voltage
rating matters more than it looks on ±12 V rails: a 16 V X7R 0805 loses roughly 20–30% of
its value at 12 V DC bias. **Specify 100 nF, X7R, 50 V, 0805, ±10%.**

**Separately, the controller side has almost no decoupling in the BOM at all.**
`C-DECOUPLE-165` covers only the four shift registers. Nothing covers the MCP3202, the
REF5050, the OPA2197 or the 74AHCT125 on the carrier — and review R48's point applies with
force to one of them: *"For a VDD-referenced ADC the decoupling capacitor **is** the voltage
reference."* The MCP3202 takes its reference from VDD; its decoupling is a precision
component, not housekeeping. **Add: 100 nF X7R 50 V 0805 × 5, plus 10 µF X7R 25 V 1206 at
the MCP3202 VDD and at the REF5050 VIN/VOUT.**

The REF5050 in particular needs its datasheet network specified and it is absent: 100 nF +
10 µF at VIN, 10 µF at VOUT for stability, and optionally 1 µF on the TRIM/NR pin, which
cuts its low-frequency noise substantially — cheap insurance on a part whose whole job is
to be the breath channel's scale factor.

---

### Finding 17 — `C-DECOUPLE-165` is right, but 100 nF alone resonates with the loom
**Severity: LOW. Confidence: medium.**

Value (100 nF), dielectric (X7R) and package (0805) are all correct, and the reasoning —
*"a 74x165's output edges brown out a local rail that has no reservoir"* — is right. Charge
check: one QH edge into ~50 pF of loom at 3.3 V is 165 pC, which drops a 100 nF cap by
1.65 µV. Ample.

The gap is the impedance between the satellite board and the regulator. A 14-inch supply
run is roughly 350 nH:

```
f_res = 1/(2π√(350e-9 × 100e-9)) = 851 kHz
```

An 851 kHz series resonance with essentially no damping sits inside the key-chain's 1 MHz
SPI band. **Add a 10 µF X7R 25 V 1206 per satellite board** alongside the 100 nF. That
pushes the resonance to 85 kHz and damps it with the larger part's ESR. Four extra parts,
on boards being fabricated anyway, in a body that cannot be reopened — the same logic ADR
0001 uses for the marker bits.

---

### Finding 18 — `U-TVS-UMB` is a 5 V array and one of the conductors it protects is at 12 V
**Severity: MEDIUM. Confidence: high.**

The SP3012-06UTG is a low-capacitance ESD array with a **5 V working voltage** (V_RWM = 5 V,
breakdown ~6 V). The BOM note says *"8 conductors from outside."*

- On SCLK, MOSI and CS at 3.3 V logic: **correct**, and the ~0.8 pF per line is right for a
  1 MHz bus.
- On BREATH at 0.2–4.8 V: **marginal but acceptable** — 4.8 V against a 5 V V_RWM leaves
  little margin and will contribute leakage. Verify the leakage at 4.8 V and 50 °C against
  the 100 kΩ pulldown; a few hundred nA is harmless, a few µA is not.
- On **+12 V: wrong, and destructive.** A 5 V array on a 12 V rail conducts continuously
  and cooks. The +12 V conductor needs its own device.

**Fix: keep the SP3012-06 for the four signal lines (it has six channels, so there are two
spare), and add a separate TVS on the +12 V conductor: SMAJ15A or SMBJ15A, 15 V stand-off,
uni-directional, ≥400 W.** 15 V stands off a 12.6 V rail with margin and clamps below the
24 V that the downstream electrolytics and the R-78E's 28 V input maximum can survive.

**And the module end of the umbilical has no ESD protection at all.** The cable is 2 m of
constantly-handled conductor between two boxes. Fit the same pair at the module: one
6-channel array for the signals, one 15 V TVS on the +12 V feed (upstream of the TPS2553).

---

### Finding 19 — `D-REVPOL`: right part family, one size too small
**Severity: LOW-MEDIUM. Confidence: high.**

The 1N5817's forward drop at 0.29–0.43 A is 0.33–0.40 V, which matches ADR 0004's
0.3–0.4 V exactly. The choice of Schottky-over-silicon for a rail that passes the
instrument's current is right, and it is the community-standard part.

Two ratings are thin:

- **Current: 1 A average.** The +12 V branch carries the module's ~45 mA plus everything the
  instrument takes. At the corrected typical of 410–430 mA it is fine; during a
  current-limited startup or fault at 1.2 A (Finding 7) plus module load it is at ~125% of
  rating, sustained for as long as the fault lasts. Dissipation then is
  `1.25 A × 0.45 V = 560 mW` in a DO-41 with Rθja ~50–100 °C/W → a 28–56 K rise.
- **Voltage: 20 V reverse.** The fault it protects against applies up to 12 V reverse
  (24 V if a rail swap is postulated). 1.67× on a protection device is thin, and 1N5817's
  reverse leakage is already high — up to 1 mA at 20 V and an order of magnitude worse hot.

**Change to 1N5819 (1 A, 40 V — pin-identical, same drop, same price) as a minimum, or
1N5822 (3 A, 40 V, DO-41) for the +12 V leg.** An SS34/SK34 in SMA is the SMD equivalent if
the board would rather not have leaded parts.

**The absence of a diode on +5 V is a correct decision**, and ADR 0004's reasoning (the only
load is a $0.30 buffer, the protected rails are what matter) holds. But review R27's
conclusion — a 5.6 V TVS as ten-cent blanket insurance, explicitly endorsed by the
verification pass — is not in the BOM. **Add: SMAJ5.0A or a 5.6 V zener on the bus +5 V
after the ferrite.**

---

### Finding 20 — `D-JACK-CLAMP` is correct and the reasoning behind it is exactly right
**Severity: none — confirming. Confidence: high.**

BAV99, SOT-23, six off, silicon not Schottky. The decisive arithmetic in ADR 0006 checks:

```
BAT54S leakage 2 µA × 1 kΩ = 2 mV
2 mV / 0.833 mV-per-cent = 2.4 cents, and it is temperature-dependent
```

Correct, and a genuinely good catch. BAV99's reverse leakage is specified at 100 nA
*maximum at 70 V*; at 11 V and room temperature it is sub-nanoamp, so
`100 nA × 1 kΩ = 0.1 mV = 0.12 cents` is a hard worst-case bound, twenty times better.
Ratings (250 mA, 70 V, 350 mW) are ample; junction capacitance of 1.5 pF per diode is
irrelevant against a 33 nF output filter.

**One placement rule that is not written down and matters:** the clamps must be on the
**jack side** of `R-OUT-PROT`. On the op-amp side they clamp nothing useful and put the
op-amp's output directly across an external fault. ADR 0006 says "at the CV jacks", which is
right, but the schematic should be explicit.

**Second rule:** clamp to the **post-diode ±11.65 V rails**, not to the raw bus, so an
external overvoltage dumps into rails the module already has bulk capacitance on.

---

### Finding 21 — `R-OPAMP-IN`: value correct, count short by two, placement rule undocumented
**Severity: LOW. Confidence: high.**

Value verified against the stated purpose:

```
DAC at 5.25 V into an op-amp with no rails:
I = (5.25 − 0.7) / 1 kΩ = 4.55 mA, against the OPA2197's ±10 mA input current limit ✓
```

Correct with 2× margin. Accuracy cost is genuinely zero: OPA2197 input bias is ~10 pA, so
`1 kΩ × 10 pA = 10 pV`, and the Johnson noise contribution over a 5 kHz bandwidth is
`4.07 nV/√Hz × √(5000 × 1.57) = 360 nV RMS` against 83 mV per semitone.

**Count.** DAC-driven op-amp inputs are: pitch (1), mod 1–4 (4), the ch6 breath-zero buffer
(1), and the ch7 mod-offset buffer (1) = **7**. The BOM says 5, having missed the two
offset-buffer channels — which are exactly the two channels ADR 0006 introduced last.

**Placement rule that needs stating.** On the mod channels the op-amp's + input already has
a divider from the LT5400 (R to Vdac, 4R to the offset). The 1 kΩ must go **between the
divider midpoint and the op-amp pin**, where it carries no current and costs nothing. If it
goes between the DAC and the divider it is *inside* the ratio and corrupts the matched
network — the exact failure ADR 0006 bought the LT5400 to prevent. "Outside the feedback
path" does not say this.

**And one rule the opposite way, on the same resistor family:** there must be **no** series
resistance between the ch6 buffer's output and the INA821's `REF` pin. An in-amp's REF pin
is one leg of its output difference amplifier; series impedance there unbalances it
directly. With internal 10 kΩ bridge resistors, 1 kΩ in series with REF caps CMRR at
`20·log10(20000/1000) = 26 dB` — against the 60 dB ADR 0003 says the link needs, destroying
the entire in-amp argument with one misplaced 1 kΩ resistor that looks identical to the six
correct ones. This belongs in ADR 0003 in bold.

---

### Finding 22 — The breath band-limit RCs are specified in prose and absent from the BOM, and their group delay is not in the latency budget
**Severity: MEDIUM. Confidence: high.**

ADR 0003: *"**Band-limit at both ends, around 500 Hz.**"* Neither RC exists in the BOM.

**Instrument end.** Put the pole *ahead* of the buffer, not after it — review R36 makes the
point that a filter downstream of an amplifier permits rectification of out-of-band energy
in the amplifier itself. With an op-amp input drawing ~10 pA, the resistor can be large and
the sensor sees no DC load through it (the capacitor blocks DC), so ADR 0003's
"don't load the sensor" rule is respected:

```
R = 10 kΩ 1% 0805,  C = 33 nF C0G 0805 50 V
f_c = 1/(2π × 10000 × 33e-9) = 482 Hz
```

**Module end**, between the in-amp output and the gain/offset stage:

```
R = 2.2 kΩ 1% 0805,  C = 150 nF PET film
f_c = 1/(2π × 2200 × 150e-9) = 482 Hz
```

C0G at the instrument end because it is inside a handled, breathed-into wooden body where
microphonics have a mechanical excitation source; film at the module end because 150 nF C0G
is an awkward package.

**The latency budget understates this path.** `docs/reference/latency-budget.md` charges
*"Buffer, cable, in-amp, output filter — < 0.2 ms"* for a total of 2.4 ms. Two 482 Hz
single poles contribute:

```
τ per pole = 1/(2π × 482) = 330 µs
Two poles  = 660 µs
Revised breath CV total: 1.17 (tube) + 1.0 (sensor) + 0.66 (filters) = 2.83 ms
```

Still comfortably inside the 5 ms target, so nothing breaks — but the table is wrong by
more than 3×, on the row it is least likely to be checked. The same file is already flagged
in the review's "documentation contradictions" section for describing this path as
differential with a 2 kHz corner.

---

### Finding 23 — `C-REG-ADJ`, `C-BULK-DISP` and the 74HC123 timing network: three underspecified networks
**Severity: LOW-MEDIUM. Confidence: high.**

**`C-REG-ADJ` — "10 µF / 1 µF ceramic or tantalum".** Three things unresolved:

- Which value goes where. Presumably 10 µF on ADJ and 1 µF on OUT. The ADJ bypass forms a
  pole with R2: `1/(2π × 768 × 10e-6) = 20.7 Hz`, which rolls off reference noise. The
  ~50 µV RMS claim is plausible: LM317 output noise without C_ADJ is ~0.003% of V_out =
  157 µV; with C_ADJ it scales toward the 1.25 V reference, `157 × (1.25/5.25) = 37 µV`.
  ✓ The claim is sound.
- **"Ceramic or tantalum" is a stability decision presented as a preference.** The LM317's
  output pole depends on the load capacitor's ESR. A very-low-ESR X7R can leave marginal
  phase margin. **Specify 2.2 µF tantalum (16 V) or a 1 µF X7R 25 V 0805 with a deliberate
  1 Ω in series**, and check the transient response on the bench — a full bench is
  available and this is a two-minute measurement.
- **DC bias derating is ignored.** A 10 µF X5R 0805 at 16 V rating, biased at 4.0 V (the ADJ
  pin sits at V_out − 1.25), retains roughly half its value → the pole moves to 41 Hz. Still
  fine, but specify **10 µF X5R 25 V 1206** to make it predictable.
- **The input capacitor is missing.** ADR 0004 says "two resistors and two capacitors" and
  the two capacitors are both on the output side. Add **100 nF X7R 50 V 0805 at the IN pin**.
- The OUT-to-ADJ protection diode is **not** required here: it is recommended above ~25 V
  output, and this is 5.25 V. Worth a note so nobody adds it.

**`C-BULK-DISP` — explicitly TBD.** Its job is absorbing WiFi TX transients at the display
board, 14 inches from the buck:

```
ESP32-S3 TX burst ≈ 300 mA on the 5 V side, ~2 ms
Buck load-step response ≈ 100–200 µs
C for 200 mV droop over 200 µs: C = 0.3 × 200e-6 / 0.2 = 300 µF
```

**Specify: 330 µF 16 V 105 °C low-ESR radial, plus 10 µF X7R 25 V 1206 and 100 nF X7R 50 V
0805 at the board's 5 V pin.** The BOM's "1206 / electrolytic THT" package hint suggests
someone was considering a ceramic alone; a 1206 ceramic maxes at ~22 µF X5R 6.3 V, which
derates to ~8 µF at 5 V — two orders short.

**And the same part is missing entirely at the real-time board.** The 8×8 matrix steps
160–960 mA on the 5 V rail (ADR 0014's own table), which is a larger transient than WiFi.
**Add 330 µF 16 V 105 °C + 10 µF + 100 nF at the real-time board's 5 V pin.** Given
Finding 7's inrush constraint, keeping both at 330 µF rather than 470 µF is the right side
to err on.

**`U-WATCHDOG` timing network — no values at all.** ADR 0004 says only *"Size N so a busy
loop cannot trip it but a hang is caught in well under a second."* For the 74HC123,
`t_w ≈ 0.45 × R_ext × C_ext`. Targeting 100 ms:

```
R × C = 0.1 / 0.45 = 0.222
R = 220 kΩ 1% 0805, C = 1 µF  →  t_w = 0.45 × 220e3 × 1e-6 = 99 ms
```

**C_ext must be low-leakage and stable — specify 1 µF PET film, ≥50 V, not an electrolytic
and not X7R.** An electrolytic's leakage current directly corrupts a monostable's timing
ramp and drifts with age and temperature; X7R's ±15% tempco and DC-bias coefficient make
the timeout wander by tens of percent. Film is a few cents and makes the watchdog a
deterministic part rather than an approximate one. At 100 ms against a 250 µs loop period
the margin is 400×, which is the right shape.

---

### Finding 24 — `R-ADCDIV`, `POT-BREATH` and the remaining small items
**Severity: LOW. Confidence: high.**

**`R-ADCDIV` (10 k / 15 k) — KEEP.** Every constraint on it checks out:

```
Ratio:     15k/(10k + 15k) = 0.600 ✓
Headroom:  sensor max from the ADR's own transfer function at VS = 5.000 V:
           5.000 × (0.1533 × 6 + 0.04) = 4.799 V   (not the "4.7 V" the ADR states)
           0.6 × 4.799 = 2.879 V into a 3.3 V VREF = 87% of range ✓
Power-up ESD clamp (R49's concern), worst case 5 V up, 3V3 down:
           R_th = 6 kΩ, V_th = 2.879 V
           I = (2.879 − 0.7)/6000 = 363 µA against a ±2 mA family limit ✓ 5.5× margin
```

The ≥10 kΩ rule is satisfied with far more margin than review R49 implied. Tolerance and
tempco genuinely do not matter here — a 2% ratio error is a 2% gain error on a channel that
is auto-zeroed and threshold-normalised. **1% thick film 0805 is correct; do not upgrade.**
One wording fix: *"metal film"* is a leaded-resistor term. For 0805, say **thick film, 1%,
±100 ppm/°C**.

Worth noting the stored-charge question raised by Finding 1's capacitor: at power-up the
filter cap is charged and dumps into the ADC's ESD diode. Energy is
`½ × 47e-9 × 2.879² = 195 nJ` — five orders of magnitude below an HBM ESD event. Non-issue
at either 47 nF or 220 nF.

**`POT-BREATH` — KEEP the part, specify the network.** Alpha 9 mm, B50k linear, PCB
vertical, driving a high-impedance op-amp input: correct, and linear taper is the right call
for CV scaling as ADR 0006 argues. Two gaps:

- **The offset pot's reference rail is unspecified**, and review R26's surviving half says
  it must not be the raw ±12 V bus. Quantified: rack ripple of 50 mV p-p attenuated to a
  ±2 V offset range (0.167) gives 8.3 mV on the breath CV — 0.083% of full scale, at
  100/120 Hz, landing on a VCA control input where it becomes audible hum. **Reference the
  offset pot to a filtered rail: 1 kΩ + 100 µF gives a 1.6 Hz corner and ~37 dB of
  rejection at 100 Hz, for two parts.** Better still, reference it to the same buffered
  2.5 V used for the pitch offset.
- **Both pots' end resistors are missing.** The resistors that set how much gain range and
  how much offset range each pot spans are not in the BOM, and they are what determine
  whether the controls are usable. Not specifiable without the in-amp gain topology, which
  is itself blocked on choosing INA821 vs INA828.

**`R-PD-BREATH` tolerance — not critical.** With a true in-amp, source-impedance balance no
longer affects CMRR (this is the whole point of ADR 0003's switch away from the INA134), so
1% or 5% is equally fine. 0805 is right.

**INA gain resistor — blocked on a part choice.** `G = 1 + 49.4 kΩ/R_G` for the INA821;
`G = 1 + 50 kΩ/R_G` for the INA828. For the 2.13× ADR 0003 specifies,
`R_G = 49400/1.13 = 43.7 kΩ` → **43.2 kΩ 1% 0805** with the INA821 (G = 2.143). The BOM
line says "INA821 **or** INA828", so the resistor cannot be specified until the part is.
Tolerance: 1% is ample; breath gain is knob-trimmed. Tempco 100 ppm/°C over 10 °C is 0.1% of
gain = 10 mV on a 10 V output — inaudible.

**`MECH-GNDBOND` — KEEP**, and the PWR_GND-not-AGND rule is correct and important for the
reason given.

**Cable and drop budget, for the record.** Summing every series element now specified on
the +12 V path at 430 mA:

```
1N5817          0.35 V
Ferrite (2 A)   0.02 V
TPS2553 R_on    0.04 V
Cable (0.34 Ω)  0.15 V
F-POLY (1812)   0.04 V   [0.29 V with the current 1206 500 mA part]
L-BUCK-IN DCR   0.06 V   [buck branch only]
Total           0.60 V → ~11.4 V at the instrument
```

Against the R-78E5.0's 7 V minimum input: ample ✓. Against the WS2815 strips, which sit on
unregulated +12 V after all of that except the inductor: ~11.5 V, inside their operating
range but worth measuring at E6. With the *current* 1206 polyfuse it is ~11.2 V and falling
as the fuse warms — another reason for Finding 6.

---

## 3. Everything that is right

Stated explicitly, because most of it is:

- **`D-JACK-CLAMP` BAV99 over BAT54S.** Correct part, correct reasoning, arithmetic verified.
  One of the best calls in the document set.
- **`R-OUT-PROT` at 1 kΩ.** The value survives the review's attack for the right reason —
  it is a pure `a` error and the trimmer has full authority over it. Only the package needs
  changing.
- **`R-ADCDIV` at 10 k / 15 k.** Ratio, headroom and ESD-clamp current all check out with
  margin. Divide-after-the-buffer is right.
- **`R-OPAMP-IN` at 1 kΩ.** 4.55 mA against a 10 mA limit, zero accuracy cost. Correct value.
- **`C-DECOUPLE-165` at 100 nF X7R.** Right value, right dielectric, right rationale, on a
  board that had none.
- **`C-STRIP-BULK` at 470–1000 µF, at the load.** The "bulk belongs where the current
  swings" correction is right, and 470 µF is genuinely sufficient (0.27 V of 2 kHz ripple).
- **Ferrites rather than a 2.2–10 Ω series resistor.** ADR 0004's drop arithmetic is right
  and so is the conclusion.
- **Branching the two +12 V paths after the diode.** The ADR is honest that it is
  "survivable by accident" at 2 kHz; the numbers say ~3.5 µV at the op-amp output, which is
  fine. Keep it.
- **`R-REG-SET` at 240 Ω / 768 Ω as a nominal.** 5.25 V is arithmetically correct and, given
  the 80 mV window available, near-optimal. Only the worst-case analysis is wrong.
- **`R-SPI-PULL` topology** (CS high, SCLK/MOSI low). Right idea for a designed-in operating
  state most designs would treat as a fault. Only the CS value needs raising.
- **`TRIM-PITCH` as a decision.** The trim-range-vs-tempco table is arithmetically correct
  throughout, and the judgement — that 2.4 cents is comparable to the VCO's own 3.5 cents
  and therefore not the limiting term — is exactly the right way to size a precision budget.
- **`R-PRECISION` as a concept**, and the observation that ratio tracking dominates absolute
  tempco by ten to one. Verified: 0.11 vs 5.40 cents.
- **`F-POLY` at 1206 rather than 0603** for placement and inspection. Right instinct; the
  package should go up again, not down.
- **Passives at 0805/1206 rather than 0402**, per ADR 0013's package policy. Correct for
  hand assembly and it holds throughout the BOM.

---

## 4. Every component the ADRs call for without a value

Consolidated list. Items marked **†** are components with no BOM line at all, not merely
values left open.

**Signal-path capacitors (the largest cluster):**

1. **†** Pitch output filter capacitor — ADR 0006, "ordinary series RC", corner 10–20 kHz
   (review V1: 5 kHz). *Recommend 33 nF C0G 1206 50 V.*
2. **†** Mod 1–4 output filter capacitors, ×4 — ADR 0006, "~2 kHz". *Recommend 82 nF film.*
3. **†** Breath output filter capacitor — ADR 0006/0003. *Recommend 330 nF film.*
4. **†** Instrument-end breath band-limit R and C — ADR 0003, "band-limit at both ends,
   around 500 Hz". *Recommend 10 kΩ + 33 nF C0G.*
5. **†** Module-end breath band-limit R and C — same sentence. *Recommend 2.2 kΩ + 150 nF film.*

**Gain- and reference-setting resistors:**

6. **†** BREATH series protection resistor at the instrument end — ADR 0003, "a series
   resistor for protection", "can be 10 kΩ". *Recommend 1 kΩ 1% 0805.*
7. **†** INA821/828 gain resistor R_G — ADR 0003, "absorbs the ~2.13× scaling stage".
   Un-specifiable until INA821 vs INA828 is chosen.
8. `R-PRECISION` — no resistance, no ratio variant, no grade, quantity "TBD".
   *Recommend LT5400A, 10 kΩ, 1:1 quad, MSOP-8.*
9. **†** Fixed gain and offset resistors surrounding the LT5400 and the pitch trimmers.
10. **†** Mod-channel gain-of-4 networks, ×4 — and ADR 0006 contradicts itself on whether
    these are LT5400 1:4 parts or "ordinary 1% discretes". 16 resistors if discrete.
11. **†** Pitch offset reference source (−2.5 V) — implied by `Vout = 2·Vdac − 2.5`, named
    nowhere, and the obvious construction (a divider from raw −12 V) is a 5–12 cent ripple
    path.
12. `TRIM-PITCH` — no resistance, no turns count, no tempco, no tolerance.
    *Recommend 1 kΩ (scale) and 10 kΩ (offset), 25-turn sealed cermet, ≤100 ppm/°C.*
13. **†** `POT-BREATH` end resistors setting the gain and offset spans, and the offset pot's
    reference rail — review R26's surviving half.
14. **†** `R-PD-BREATH` companion common-mode bias-return resistors — not called for by any
    ADR, which is itself the gap (Finding 3). *Recommend 2 × 1 MΩ 1% 0805.*

**Active-part support networks:**

15. **†** `U-LOADSW` R_ILIM — the resistor that *is* the current limit. *Recommend 13.4 kΩ
    1% for ~1.2 A.* Plus FAULT pull-up (10 kΩ), EN pull-down (10 kΩ), EN debounce RC, and
    the datasheet input/output capacitors.
16. **†** `U-WATCHDOG` R_ext and C_ext — ADR 0004 gives only "well under a second".
    *Recommend 220 kΩ 1% + 1 µF PET film → 99 ms.*
17. **†** `U-REG-DAC` input capacitor — ADR 0004 says "two capacitors" and both listed ones
    are on ADJ/OUT. *Recommend 100 nF X7R 50 V 0805.*
18. `C-REG-ADJ` — which value goes on which pin; "ceramic or tantalum" is an unresolved
    stability decision; no voltage rating; DC-bias derating unaccounted.
19. **†** `U-REF-BREATH` REF5050 input, output and TRIM/NR capacitors. *Recommend
    100 nF + 10 µF at VIN, 10 µF at VOUT, optional 1 µF on NR.*
20. **†** `U-ADC` MCP3202 VDD/VREF decoupling — and review R48 is right that for a
    VDD-referenced converter this capacitor is a precision component. *Recommend 10 µF X7R
    25 V 1206 + 100 nF X7R 50 V 0805.*
21. **†** Carrier-board decoupling generally for OPA2197, 74AHCT125 and REF5050 — ADR 0013
    lists "Passives" and nothing else; `C-DECOUPLE` is module-only and `C-DECOUPLE-165`
    covers only the shift registers.

**Bulk, filtering and protection:**

22. `C-BULK-DISP` — value explicitly TBD, status `open`. *Recommend 330 µF 16 V 105 °C +
    10 µF + 100 nF.*
23. **†** Bulk capacitance at the real-time board's 5 V pin — ADR 0014's own table has the
    matrix stepping 160–960 mA and nothing absorbs it. *Same recommendation as 22.*
24. `L-BUCK-IN` — the capacitor of the "LC" is not specified at all, nor any damping; and
    "≥1 A" does not distinguish I_sat from I_rms. *Recommend 47 µH / I_sat ≥1.5 A / DCR
    ≤0.15 Ω, with 470 µF 25 V plus a 100 µF + 1 Ω damping branch.*
25. `FB-IN` — no bead impedance (Z @ 100 MHz), no capacitor voltage rating, ambiguous
    quantity. *Recommend 600 Ω @ 100 MHz / 2 A / DCR ≤50 mΩ / 1206, and 470 µF 35 V 105 °C
    on the umbilical branch with 100 µF elsewhere.*
26. `F-POLY` — no voltage rating, and the 500 mA hold is below the load.
    *Recommend 1812, 1.1 A hold, ≥16 V, R_init ≤ 0.1 Ω.*
27. `C-STRIP-BULK` — no exact value in the 470–1000 µF range, no temperature class, no ESR,
    no ripple rating, and 16 V is thin. *Recommend 470 µF 25 V 105 °C low-ESR, ≥500 mA
    ripple.*
28. `C-DECOUPLE` — "ceramic" is not a dielectric and no voltage rating is given; quantity is
    about half the stated requirement. *Recommend 100 nF X7R 50 V 0805, qty 20.*
29. **†** +12 V umbilical TVS — the SP3012-06 is a 5 V array and cannot sit on that
    conductor. *Recommend SMAJ15A.*
30. **†** Module-end umbilical ESD protection — none exists at either the signal or power
    conductors.
31. **†** Module +5 V clamp — review R27's 5.6 V TVS, endorsed by the verification pass.
    *Recommend SMAJ5.0A.*
32. **†** I2C pull-ups — named in ADR 0005's power tree. Satisfied by the dev board in
    practice; the tree should say so rather than listing a part that is not bought.
33. **†** etherCON cable carriers (NE8MC-1) — review R38, still absent. Not a passive, same
    class of gap.

---

## 5. Suggested BOM deltas, in one block

```
C-AA-ADC       220 nF X7R 0805        → 47 nF C0G 1206 50 V ±5%
R-OUT-PROT     1 k 0805 ×6            → 1 k 1% 1206 thick film ×6
R-OPAMP-IN     1 k 1% 0805 ×5         → ×7
R-PD-BREATH    100 k 0805 ×1          → ×1, plus 1 M 1% 0805 ×2 (CM bias return)
R-SPI-PULL     10 k 1% ×3             → 100 k (CS) + 10 k ×2 (SCLK, MOSI)
R-MOSI-SER     220 R ×1               → 68 R 1% 0805 ×3 (MOSI, SCLK, CS)
R-TERM-CHAIN   33–68 R ×2             → 68 R 1% 0805 ×3, with S3 drive set low
R-REG-SET      240 R / 768 R          → delete; REF5050 + ½ OPA2197 for DAC AVDD
C-REG-ADJ      10 µF / 1 µF           → delete with the above, or specify fully + input cap
C-DECOUPLE     100 nF ceramic ×10     → 100 nF X7R 50 V 0805 ×20
C-DECOUPLE-165 100 nF X7R ×4          → keep, add 10 µF X7R 25 V 1206 ×4
C-STRIP-BULK   470–1000 µF 16 V       → 470 µF 25 V 105 °C low-ESR ≥500 mA ripple ×2
L-BUCK-IN      10–47 µH ≥1 A          → 47 µH, I_sat ≥1.5 A, DCR ≤0.15 Ω, + 470 µF 25 V
                                          + damping branch 100 µF 25 V in series with 1 R
FB-IN          bead ≥1 A + 470 µF     → 600 R@100 MHz / 2 A / 1206 ×4;
                                          470 µF 35 V 105 °C ×1 (umbilical) + 100 µF 35 V ×3
F-POLY         PPTC 1206 500 mA       → PPTC 1812, 1.1 A hold, ≥16 V, R_init ≤0.1 R
D-REVPOL       1N5817 ×2              → 1N5819 (or 1N5822 on +12 V) ×2
U-TVS-UMB      SP3012-06UTG ×1        → ×2 (both ends) + SMAJ15A ×2 on +12 V
TRIM-PITCH     "5–10% of ratio" ×2    → 1 k + 10 k, 25-turn sealed cermet, ≤100 ppm/°C
R-PRECISION    LT5400-class, TBD      → LT5400A-x, 10 k, 1:1 quad, MSOP-8, qty per topology
C-BULK-DISP    TBD                    → 330 µF 16 V 105 °C + 10 µF 1206 + 100 nF ×2 boards

NEW: pitch output filter          33 nF C0G 1206 50 V ×1
NEW: mod output filters           82 nF PPS/PET film ×4
NEW: breath output filter         330 nF PET film ×1
NEW: breath band-limit (instr)    10 k 1% 0805 + 33 nF C0G 0805 50 V
NEW: breath band-limit (module)   2.2 k 1% 0805 + 150 nF PET film
NEW: BREATH series protection     1 k 1% 0805
NEW: INA gain resistor            43.2 k 1% 0805 (INA821) — pending part choice
NEW: TPS2553 R_ILIM               13.4 k 1% 0805, + 10 k FAULT pull-up, 10 k EN pull-down,
                                     100 nF EN debounce, 100 nF in / 100 nF out
NEW: 74HC123 timing               220 k 1% 0805 + 1 µF PET film 50 V
NEW: REF5050 network              100 nF + 10 µF in, 10 µF out, 1 µF NR (optional)
NEW: MCP3202 VDD network          10 µF X7R 25 V 1206 + 100 nF X7R 50 V 0805
NEW: carrier decoupling           100 nF X7R 50 V 0805 ×5
NEW: RT board 5 V bulk            330 µF 16 V 105 °C + 10 µF + 100 nF
NEW: module +5 V clamp            SMAJ5.0A
NEW: breath offset pot filter     1 k + 100 µF (or reference to buffered 2.5 V)
NEW: pitch offset reference       buffered −2.5 V from DAC VREFOUT via ½ OPA2197
```

---

## 6. Confidence and what I could not check

**High confidence:** all arithmetic above is shown and reproducible from the documents' own
stated values. Findings 1, 2, 3, 4, 5, 6, 10, 11, 13, 14, 16, 18, 21, 22 rest on numbers
that come entirely from this repository plus standard component ratings.

**Medium confidence, needs a datasheet the sandbox could not reach:**

- The DAC8568's internal reference *maximum* temperature drift (Finding 15). ADR 0006 uses
  the typical figure; if the maximum is several times worse, its conclusion that a separate
  reference "buys nothing measurable" needs re-examining.
- The TPS2553's exact I_OS-to-R_ILIM relation and its soft-start behaviour under
  current-limited startup into millifarads (Finding 7). The shape of the problem is right;
  the specific R_ILIM value should be taken from the datasheet.
- The 74HC123's timing constant K (Finding 23) varies between the HC and HCT families and
  between vendors, and with C_ext below ~10 nF.
- The loom's characteristic impedance (Finding 12) — 100–150 Ω is an estimate. E4 should
  measure it with a TDR or a fast edge and a scope; the bench exists.
- OPA2197 input current limit (Finding 21) — I have used ±10 mA, the family-typical figure.

**Not assessed:** mechanical parts (`PLATE-TOP`, `BODY-OAK`, `SIDE-ACRYLIC`, `MECH-WINDOW`,
`MECH-PTFE`, `MECH-COAT`, `TUBE`), connectors, switches, active ICs, the LED strip itself,
and the cable — all outside this review's scope except where a passive's rating depends on
them.

**No repository file was modified.**
