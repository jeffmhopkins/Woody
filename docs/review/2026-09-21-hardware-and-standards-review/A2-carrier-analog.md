# A2 — Carrier analog front end: sensor → ADC → umbilical

**Reviewer:** cold hardware review, 2026-09-21. No prior review or research wave
was read (`docs/review/**`, `docs/research/**` deliberately untouched). Where the
carrier page cites a prior wave by name (`R10`, `D1`, `S1`, `C5`, `B*`) I have
re-derived the number rather than taking it.

**Sources read:** `hardware/controller/carrier.md` §1–§2 (and §3–§4 where they
touch the 3V3 reference and the ADC clock), `hardware/bom.csv`,
`docs/decisions/0003-breath-sensing-path.md`, `0005-power-architecture.md`,
`0006-cv-channel-allocation.md`, `hardware/module/breath-receive-stage.md`,
`config/key-layout.yaml`.

**Network:** HTTPS fetches were blocked for every datasheet host I tried —
`ti.com`, `nxp.com`, `st.com`, `farnell.com`, `digikey.*`, `ww1.microchip.com`,
`alldatasheet.com`, `lcsc.com`, `waveshare.com` (proxy returned
`EGRESS_BLOCKED`/403 CONNECT). Web *search* worked, so a few figures below are
marked `[web]` against a search-result summary rather than a datasheet page;
those are weaker than a datasheet reading and are flagged as such. Everything
else about part internals is `[from memory]`.

**Indexing:** by circuit node, then by BOM reference. Node names follow the
§2 drawing.

---

## Nodes under review

| Node | Definition |
|---|---|
| `VREF5` | REF5050 output, OPA2197-A input |
| `VS` | OPA2197-A output = MPXV4006DP `VS` pin = the sensor's scale factor |
| `VSENSE` | MPXV4006DP `Vout`, OPA2197-B input |
| `VBUF` | OPA2197-B output; splits to `R-SER-BREATH-INST` and `R-ADCDIV-U` |
| `BREATH` | `J-UMB` pin 1, after `R-SER-BREATH-INST` |
| `AGND` | `J-UMB` pin 2, sense-only return |
| `ADCIN` | `R-ADCDIV` midpoint = `C-AA-ADC` top = MCP3202 CH0 |
| `VDD_ADC` | MCP3202 `VDD`, **which is also its `VREF`** — the dev board's 3V3 |
| `AGND-local` | the board's analog pour; single tie to `PWR_GND` at `J-UMB` |
| `P1`/`P2` | sensor pressure port / reference port |

---

## Summary of findings, ranked

| # | Node / ref | Finding | Rank | Confidence |
|---|---|---|---|---|
| 1 | `VS` / `U-BUF`, `R-ISO-REF` | The reference buffer as drawn oscillates. `R-ISO-REF` is in `bom.csv` but absent from §2's drawing **and** from §2's component table. The in-loop form the repo specifies is itself incomplete. | **Showstopper** | High |
| 2 | `AGND` / `R-SER-BREATH-INST` | `R1b`, the AGND-leg twin, is in the BOM as instrument-side and unretrofittable; §2 does not draw it and the component table does not say ×2. Costs ~10 dB of link CMRR and breaks the module's 482 Hz pole derivation. | **High** | High |
| 3 | `BREATH` / `D-TVS-BREATH` | Drawn on the op-amp side of `R-SER-BREATH-INST`. The 1 kΩ then absorbs the ESD strike. Order must be connector → TVS → R → silicon. | **High** | Medium-high |
| 4 | `VDD_ADC` | The 0.077 %/3.2 LSB pull-up term is the *smallest and most benign* error on this node. The MCU's own transient load and the buck's 330 kHz ripple are 10–50× larger and are not calibratable. `C-ADC-BULK` as a bare 10 µF does not fix them. | **High** | Medium-high |
| 5 | `AGND-local` ↔ `PWR_GND` | The WS2815 return (0.53–1.0 A, ~2 kHz) is on **this** board. >1 mΩ of copper shared with the ADC's ground reference costs >0.66 LSB of 2 kHz modulation. No layout constraint is written. | **High** | Medium |
| 6 | `P2` | A *partially* sealed reference port is worse than a fully sealed one and is invisible to the digital copy because auto-zero hides it; it wanders on the analog path, which has no auto-zero. E2's warm-up check must be run on the analog output. | **Medium** | Medium-high |
| 7 | `ADCIN` / `C-AA-ADC` | 132 nC dumped into the MCP3202's input clamp on every power-down. One 100 Ω resistor fixes it and costs nothing. | **Medium** | Medium |
| 8 | `ADCIN` anti-alias | 564 Hz gives **16.6 dB** at the frequency that matters (3.84 kHz), not the 55 dB the page quotes at 330 kHz. The corner is still the right choice — but for a reason the page does not give. | **Medium** | High |
| 9 | `VSENSE` | Full scale is **4.799 V**, not 4.7 V. The repo carries both. Every count in §2 is built on the wrong one. | **Low** | High |
| 10 | `ADCIN` | Clamp-current arithmetic ignores the 15 kΩ lower leg; conservative by ~1.5×. | **Low** | High |
| 11 | `ADCIN` | τ = 282 µs is not 282 µs of added rise time. The honest figure is 86 µs, 1.7 % of the 5 ms budget, not 5.6 %. | **Low** | High |
| 12 | `P1` / `TUBE` | A capped mouthpiece plus a flight or a mountain pass puts **26 kPa = 4.3× full scale** across the diaphragm, sustained. | **Note** | Medium |
| 13 | `U-BREATH` | Spec'd +10 to +60 °C. A cold start below +10 °C is outside the part's operating range. | **Note** | Medium |
| 14 | `VS`, `VBUF` | +12 V rail rejection is a **non-problem**: 178 mV of 2 kHz LED ripple lands as 4.5 µV through the REF5050 and 71 µV through the op-amp. Recorded so it is not over-engineered. | **Note** | Medium |
| 15 | `VDD_ADC` | The REF5050's precision serves branch (a) only. Branch (b) inherits the dev board's unspecified LDO, ±2 %. That is fine — but the page reads as though the reference protects both. | **Note** | High |

---

## 1. `VS` — the reference buffer does not close its loop stably

### What is drawn

`REF5050 → ½ OPA2197 follower → MPXV4006DP VS`, with `C-REF-OUT` 10 µF and a
100 nF on the reference side of the buffer `[repo] carrier.md §2`, and a further
100 nF at the sensor's supply pin from `C-DECOUPLE-CARRIER` — whose note lists
"MPXV4006DP" explicitly `[repo] bom.csv:74`.

So the follower's capacitive load is **100 nF** (the sensor's decoupler), or
**10.1 µF** if `C-REF-OUT` turns out to sit on the buffer's output rather than
the reference's — which §2's own *Still open* list admits is undecided
("`C-REF-OUT` qty 2 for one REF5050 — parallel, or input and output?")
`[repo] carrier.md`.

### Why it oscillates

OPA2197: 10 MHz gain-bandwidth, "high capacitive load drive of up to 1 nF"
`[web] https://www.ti.com/product/OPA2197` (search summary; the datasheet page
itself was blocked).

Back-solve the open-loop output resistance from the repo's own figure. The
U-BUF row and `breath-receive-stage.md` both quote "a pole at 21 kHz" for the
100 nF case `[repo] bom.csv:26, breath-receive-stage.md:320`:

```
[calc]  Ro = 1 / (2π · 21 kHz · 100 nF) = 75.8 Ω
```

Check that against TI's own 1 nF claim — a good model should put 1 nF right at
the edge of usability:

```
[calc]  load pole with 1 nF   = 1/(2π · 75.8 · 1e-9)   = 2.10 MHz
        loop crossover        = √(10 MHz · 2.10 MHz)   = 4.58 MHz
        phase margin          = 90° − atan(4.58/2.10)  = 24.6°
```

24.6° is the classic "just barely" number, so **Ro ≈ 76 Ω is self-consistent
with the datasheet's 1 nF limit** `[calc]`. Now run the two candidate loads:

```
[calc]  100 nF at the sensor pin
          load pole  = 1/(2π · 75.8 · 100e-9) = 21.0 kHz
          crossover  = √(10e6 · 21.0e3)       = 458 kHz
          margin     = 90° − atan(458/21.0)   = 2.6°      → oscillates ~458 kHz

[calc]  10.1 µF (if C-REF-OUT lands on the buffer output)
          load pole  = 1/(2π · 75.8 · 10.1e-6) = 208 Hz
          crossover  = √(10e6 · 208)           = 45.6 kHz
          margin     = 90° − atan(45600/208)   = 0.3°      → oscillates ~46 kHz
```

**The open C-REF-OUT question moves the oscillation frequency by a decade and
does not change the verdict.** Note the counter-intuitive part: the *small*
capacitor is the harder case. 100 nF of low-ESR ceramic keeps the load
impedance low all the way out to the op-amp's crossover; 10 µF of electrolytic
brings its own ESR zero along with it.

### The repo half-knows this, and §2 does not

`bom.csv` row `R-ISO-REF` exists — 10 Ω, qty 1, "INSIDE THE LOOP, with feedback
taken at the SENSOR's VS pin" `[repo] bom.csv:114` — and
`breath-receive-stage.md` argues it at length `[repo] :318–332`.

**`carrier.md` §2 draws a bare follower and its component table has no
`R-ISO-REF` row**, although the table's own preamble says "Existing BOM rows are
named as they stand" `[repo] carrier.md`. §2 is the layout input. What is drawn
is what gets built.

### And the specified fix is incomplete as written

"`R-ISO-REF` inside the loop, feedback taken at the sensor's `VS` pin" is not a
stable topology on its own. Taking DC feedback from the far side of the
isolation resistor puts the `R_iso · C_L` pole straight back inside the loop:

```
[calc]  R_iso = 10 Ω, C_L = 100 nF
          in-loop pole = 1/(2π · 10 · 100e-9) = 159 kHz
          crossover    = √(10e6 · 159e3)      = 1.26 MHz
          margin       = 90° − atan(1260/159) = 7.2°       → still oscillates
```

The textbook form needs a **second, local** feedback path: `R_F` from `VS` back
to the inverting input, and `C_F` from the op-amp's *output pin* to the same
node, so the loop is closed locally above the load pole and globally below it.
The sizing rule is `R_F · C_F > R_iso · C_L`:

```
[calc]  R_iso · C_L = 10 Ω × 100 nF = 1.0 µs
        R_F = 10 kΩ, C_F = 1 nF  →  10 µs, a 10× margin
```

Two extra parts, not one. If the 10.1 µF case turns out to be real,
`R_iso · C_L = 101 µs` and `C_F` grows to 10 nF at the same `R_F`.

### Three correct fixes, costed

The repo rejects the obvious one on a specific number: an out-of-loop resistor
costs "10 Ω × 10 mA = 100 mV on 5.000 V — 2 % of a ratiometric scale factor,
against a reference specified to 0.05 %" `[repo] bom.csv:26,
breath-receive-stage.md:325`. That arithmetic is right `[calc] 10 × 0.010 = 0.100 V
= 2.00 % of 5 V`, and the conclusion drawn from it is not, for two reasons.

**(a) 10 Ω is more than the stability criterion needs.** For an out-of-loop
resistor, stability requires the zero at `1/(2π R_iso C_L)` to fall at or below
the new crossover at `GBW · R_iso/(Ro + R_iso)`. Solving for the 100 nF case:

```
[calc]  1/(2π R C) ≤ GBW · R/(Ro+R)
        with C = 100 nF, GBW = 10 MHz, Ro = 75.8 Ω:
        76 + R ≤ 6.283 R²   →   R ≥ 3.56 Ω
```

So 10 Ω carries a 2.8× margin, and the value is *right* — but the minimum is
3.6 Ω, and at 4.7 Ω (E24, 1.3× margin over minimum) the cost is
`[calc] 4.7 × 0.010 = 47 mV = 0.94 %`, not 2 %. Verify the margin at 4.7 Ω:

```
[calc]  zero      = 1/(2π · 4.7 · 100e-9)      = 339 kHz
        crossover = 10e6 · 4.7/(75.8+4.7)      = 584 kHz   (zero is below → phase recovered)
        margin    ≈ 90° − atan(584/339) + 90°  ... phase past the zero is ~0° net → ≈ 60°
```

**(b) ADR 0003 has already ruled that a static scale error does not matter.**
Its own words: "Absolute accuracy is not what matters. Breath is zeroed at
ambient and the module's gain knob sets the span, so a rail that is 4.93 V
instead of 5.00 V calibrates out on the first breath. What does not calibrate
out is *dynamic* excursion" `[repo] 0003`. 4.93 V is a **1.4 %** static error,
larger than the 0.94 % this resistor would cost. The module's GAIN knob spans
0.5–4× `[repo] 0006`. A 0.94 % static term is 0.3 % of that knob's authority.

The dynamic part of an out-of-loop resistor is the sensor's *supply current
modulation* × R. The MPXV4006's output drives only the OPA2197-B input (CMOS,
picoamps `[from memory]`), so there is no output-loading term; the on-chip
amplifier's quiescent current is what it is. If it moved 1 mA over full scale —
which nothing suggests — the error would be `[calc] 1 mA × 4.7 Ω = 4.7 mV =
0.094 % of span`. **Verify the sensor's IDD-vs-pressure on the datasheet before
committing**; that is the one number that could overturn this.

**(c) The zero-DC-error option, which nobody has costed.** Put the damping
resistor in series with the *capacitor*, not the load — a series R–C snubber
from `VS` to `AGND-local`. The sensor's 10 mA bypasses it entirely, so the DC
error is exactly zero, and the op-amp still sees a damped load. This is also
what the REF5050 datasheet is hinting at for its own output: the recommended
output ESR is **1 Ω to 1.5 Ω**, and the output must be decoupled with 1 µF to
50 µF `[web]` (TI E2E / Mouser REF50xx search summaries;
`https://www.mouser.com/datasheet/2/405/1/ref5020-3416452.pdf` and
`https://e2e.ti.com/support/data-converters-group/data-converters/f/data-converters-forum/376073/`).
A deliberate ESR *is* a damping resistor.

**Recommendation for `VS`:** keep `R-ISO-REF` at 4.7–10 Ω but draw it
**out of loop**, or as a series R–C snubber at `VS`. Either way it must appear
on `carrier.md` §2's drawing and in its component table before layout. The
in-loop variant is fine engineering but needs `R_F`+`C_F` specified, and it is
three parts where the snubber is two.

**Secondary question worth asking:** is the buffer needed at all? ADR 0003's
justification is that the REF5050 sources 10 mA against the sensor's 10 mA,
"inside its rating and has no margin" `[repo] 0003`. That is a real concern, but
adding the buffer is what created this entire problem. If a future revision can
find a 5 V reference with ≥20 mA of output — or accept the REF5050 at its limit
with the output cap the datasheet wants — the op-amp half comes free for
something else and the stability question disappears. Not a recommendation,
just: the buffer is not obviously the cheap option it is presented as.

---

## 2. `AGND` — `R-SER-BREATH-INST` is specified ×2 and drawn ×1

`bom.csv` row 64: qty 2, "**TWO, not one** … R1 in the BREATH leg, **R1b its
twin in the AGND leg** … Both are instrument-side and UNRETROFITTABLE"
`[repo] bom.csv:64`. The module page depends on it: its differential pole is
"482 Hz (not 531 — **R1b makes both legs 11 kΩ**)"
`[repo] breath-receive-stage.md:160`.

`carrier.md` §2 draws `R-SER-BREATH-INST` only in the BREATH leg; the AGND leg
runs from the star point to `J-UMB` pin 2 with nothing in it. The component
table's row reads `R-SER-BREATH-INST | 1 kΩ | Output protection. No series cap
here` — no ×2, while the adjacent `D-TVS-BREATH ×2` row does carry its count
`[repo] carrier.md`.

### What its absence costs, quantitatively

The INA828's inputs are gigaohms, so source-impedance imbalance does **not**
degrade CMRR through the amplifier `[repo] 0003`. The mechanism that does is the
2 × 1 MΩ common-mode bias pair `[repo] breath-receive-stage.md:159` forming a
divider with each leg's series resistance. Module-side protection is 10 kΩ per
leg `[repo] breath-receive-stage.md:160, implied by "both legs 11 kΩ"`.

```
[calc]  WITHOUT R1b:  BREATH leg = 1 k + 10 k = 11 kΩ ; AGND leg = 10 kΩ
          ratio_B = 1e6/(1e6+11e3) = 0.989120
          ratio_A = 1e6/(1e6+10e3) = 0.990099
          Δ       = 9.79e-4   →   CMRR = 20·log10(1/9.79e-4) = 60.2 dB

[calc]  WITH R1b:     both legs 11 kΩ, residual from tolerance only
          ΔRs (two 1 % parts, worst case opposite) = 220 Ω → 220/1.011e6 = 2.18e-4
          ΔRb (1 MΩ pair at 1 %)  = 11e3 · 2e4 / 1e12          = 2.20e-4
          RSS                                                   = 3.10e-4
          CMRR = 20·log10(1/3.10e-4) = 70.2 dB
```

**R1b buys ~10 dB.** The requirement, derived independently:

```
[calc]  common mode at the in-amp = instrument return current × cable resistance
        = 350 mA × 0.168 Ω = 58.8 mV      [repo] 0003's own table says 58.9 mV
        budget: 1 LSB of a 10 V / 16-bit output = 153 µV
        referred to the in-amp input: 153 µV / 2.185 = 70 µV
        CMRR needed = 20·log10(58.8e-3 / 70e-6) = 58.5 dB
```

ADR 0003's "60 dB the scheme needs" checks out `[repo] 0003`. **Without R1b the
link lands on 60.2 dB against a 58.5 dB requirement — 1.7 dB of margin.** It
works; it works with nothing to spare, on two parts' tolerance, on a board that
cannot be reopened.

### The rest of the AGND scheme does work — confirmed

The central claim of the grounding design is that `AGND` carries no power
current. Verified:

```
[calc]  AGND's path at the module: R1b 1 kΩ + module 10 kΩ + 1 MΩ bias ≈ 1.011 MΩ
        PWR_GND's path: 0.168 Ω of 24 AWG
        fraction of return current diverted into AGND = 0.168 / 1.011e6 = 1.66e-7
        at 350 mA:  58 nA  →  58 nA × 0.168 Ω = 9.8 nV on the sense pair
```

Nine nanovolts. Against a 153 µV LSB that is 6e-5 LSB. **The sense-only return
is sound**, and the decision in §2 to send the analog section's *supply* return
home on `PWR_GND` rather than `AGND` is correct and costs nothing.

One structural note: `AGND` (pin 2) and `PWR_GND` (pin 6) are **shorted at the
instrument end** by the single tie, and must *not* be shorted at the module end.
`breath-receive-stage.md` does not short them `[repo]`. Worth stating as an
explicit interface rule on both pages, because a well-meaning "tie the grounds
together at the connector" at the module end silently destroys the scheme and
leaves no visible symptom except a breath CV that moves with the light show.

Pairing is right: T568B puts 1–2 on one twisted pair and 3–6 on another
`[from memory]`, so BREATH/AGND is a pair and +12 V/PWR_GND is a pair, which is
what the block diagram's pin assignment achieves `[repo] carrier.md`.

---

## 3. `BREATH` — `D-TVS-BREATH` is on the wrong side of the series resistor

### The standoff voltage is right

12 V standoff on a 0.2–4.80 V signal, justified because the buffer runs on +12 V
so a sustained +12 V fault on the conductor is by design harmless and a 5 V
clamp would turn that into a conducting part `[repo] bom.csv:93, 0003`. That
reasoning is correct and I would not change the part.

But note what it implies: with the buffer on a +12 V rail, **the op-amp's own
output ESD structure conducts before the TVS does**.

```
[from memory]  OPA2197 output clamps to V+ at roughly +12.7 V
[from memory]  PESD12VS1UB: V_RWM 12 V, V_BR ≈ 13.3 V
```

So for any positive transient the op-amp's internal diode is the first thing to
conduct. **The TVS therefore has exactly one job: to be the low-impedance path
at the connector, so that the series resistor stands between the strike and the
silicon.** Its position is the whole of its value.

### As drawn, it is behind the resistor

```
 ├──[½ OPA2197 buffer]──┬──[R-SER-BREATH-INST 1k]── J-UMB pin 1  BREATH
                        │
                        │        [D-TVS-BREATH 12 V standoff]
```

`[repo] carrier.md §2`. The TVS hangs off the node **before** the 1 kΩ. That
leaves `J-UMB` pin 1 — an externally accessible, hot-pluggable contact —
with no clamp at all, and puts the 1 kΩ in series with the strike:

```
[calc]  IEC 61000-4-2 contact discharge, 8 kV: gun is 150 pF / 330 Ω, ~30 A peak
        into 1 kΩ that is 30 kV of demanded drop
[from memory]  a 1206 thick-film resistor's working voltage is ~200 V,
               its single-pulse withstand ~1 kV
```

The resistor flashes over, and after it has done so a few times its value has
moved — on a part that is instrument-side and unretrofittable `[repo] bom.csv:64`
and whose value sets the module's 482 Hz pole
`[repo] breath-receive-stage.md:160`.

**Correct order: `J-UMB` pin 1 → `D-TVS-BREATH` → `R-SER-BREATH-INST` →
op-amp.** Then:

```
[from memory]  PESD12VS1UB clamps to ~20–25 V at amp-level currents
[calc]         current into the op-amp's output clamp = (25 − 12.7)/1 kΩ = 12.3 mA
```

12 mA for tens of nanoseconds into an ESD structure, which is what ESD
structures are for.

The AGND-leg TVS *is* drawn at the connector (`J-UMB pin 2 AGND ──┴── analog
star point … [D-TVS-BREATH]`) `[repo] carrier.md §2`, so the two instances are
inconsistent with each other. Low probability this is deliberate; high
consequence if it is drawn as shown.

### Hot-plug — no analog damage, quantified

etherCON/RJ45 has no defined mating sequence; all eight contacts arrive together
with bounce `[from memory]`. The module is normally already live with its
LT1641 latched on `[repo] 0005`, so a hot plug sees a hard +12 V with no inrush
ramp.

Worst analog case is +12 V (pin 3) mating before PWR_GND (pin 6), with a signal
ground bearing the return:

```
[repo] bom.csv  instrument bulk = C-BUCK-IN 2×100 µF + C-STRIP-BULK 2×470–1000 µF
                                = 1.14 – 2.2 mF
[calc]  loop R ≈ 0.17 Ω conductor + ~0.25 Ω parallel electrolytic ESR = 0.42 Ω
        peak current = 12 / 0.42 = 28.6 A
        τ            = 0.42 × 2.2 mF = 0.92 ms
        AGND (bonded to instrument PWR_GND) swings 28.6 A × 0.17 Ω = 4.9 V
        relative to module ground, for ~1 ms
```

That is a 4.9 V common-mode step at the in-amp inputs. Inside the INA828's
common-mode range on ±12 V `[from memory]`, and the differential result is:

```
[calc]  4.9 V / 1000 (60 dB) = 4.9 mV  →  × 2.185 = 10.7 mV at the in-amp output
```

**Ten millivolts. Inaudible, non-destructive.** The 12 V TVS correctly does not
clamp it. The analog front end survives hot-plug; the exposure is on the digital
pins and the power entry, which are other reviewers' scope.

Hot-*unplug* is also benign:

```
[calc]  dV/dt = I/C = 359 mA / 1.14 mF = 315 V/s  →  12 V decays in 38 ms
```

The breath CV fades over ~38 ms rather than stepping, and the module's 1 MΩ bias
pair then holds the jack at 0 V `[repo] 0003, 0006`. No click.

---

## 4. `VDD_ADC` — ratiometric integrity, and where the real error is

### What cancels and what does not

```
[repo] 0003   sensor:  Vout = VS · (0.1533·P + 0.04)
[repo] §2     divider: ADCIN = 0.6 · Vout
              ADC:     code  = 4096 · ADCIN / VDD_ADC

[calc]        code = 4096 · 0.6 · VS · (0.1533·P + 0.04) / V_3V3
                   ∝  VS / V_3V3
```

**Nothing cancels.** The ratiometric property of the sensor is a statement that
its output tracks *its own supply*. It cancels only if the ADC's reference is
that same node. Here `VS` is the REF5050 and `VREF` is the dev board's LDO, so
the digital reading carries the *product* of two independent errors rather than
the ratio of one.

Sizing them:

```
[repo] bom.csv:25  REF5050:  ±0.05 % initial, 3 ppm/°C, ~5 ppm/V line reg
[calc]             over a 20 K interior rise: 3 ppm/K × 20 K = 60 ppm = 0.006 %
[from memory]      OPA2197 Vos ≈ 25 µV typ / 100 µV max → 100 µV/5 V = 0.002 %
                   → the VS side contributes well under 0.1 %

[from memory]      a small CMOS LDO of the class fitted to these dev boards
                   (ME6211/ME6217 family; the ESP32-S3-Zero uses ME6217C33M5G
                   [web] circuitstate.com — the Matrix's own schematic was blocked)
                   has ±2 % initial accuracy and ~±100 ppm/°C
```

**The 3V3 LDO is ~40× the REF5050's contribution to the digital copy's scale
factor.** That is *fine*, because the digital copy's jobs — note-gate threshold,
mod source, display, MIDI — are all either auto-zeroed or gain-insensitive
`[repo] 0003, 0006`. But it should be said plainly on the page, because §2 reads
as though the precision reference protects the whole chain. **It protects
branch (a), the analog CV to the jack, which is exactly the reason ADR 0003
gives for buying it** `[repo] 0003`. Branch (b) gets nothing from it.

### Is "~0.3 %/100 mA" plausible? No — it is 3–10× pessimistic

```
[repo] carrier.md §2/§3   claim: ~0.3 % per 100 mA  →  9.9 mV/100 mA
[calc]                    that is 0.099 mV/mA, i.e. an effective closed-loop
                          output resistance of 99 mΩ
[from memory]             small CMOS LDOs in this class spec load regulation as
                          6–30 mV over their whole 0→600/800 mA range
[calc]                    = 0.010 – 0.038 mV/mA, i.e. 10–38 mΩ
```

So the repo's figure is at the pessimistic end by 2.6–10×. I could not open a
datasheet to pin it (`lcsc.com`, `alldatasheet.com`, `kriscables.com` all 403).
**Mark the figure as an upper bound and keep it** — it is being used to bound a
tolerated error, and a conservative bound is the right kind of wrong.

### The consequence arithmetic is also overstated, twice

```
[calc]  per closed key:  3.3 V / (2.2 kΩ + 100 Ω) = 1.4348 mA      ✓ repo
        18 keys:                                    25.83 mA        ✓ repo
        × 0.099 mV/mA                             = 2.56 mV = 0.0775 %  ✓ repo
```

The arithmetic to 0.077 % is right. The step from there to "3.2 LSB" is not:

```
[calc]  0.0775 % applied at FULL SCALE (4096)      = 3.17 LSB   ← the repo's number
        0.0775 % applied at the PLAYING code (1747) = 1.35 LSB   ← the honest number
```

It is a *gain* error, as the page correctly says — which means it must be
evaluated at the reading, not at full scale. And 18 keys closed simultaneously
is not a fingering; `config/key-layout.yaml` has 18 fitted switches across four
clusters `[repo]`, and a realistic note-to-note change moves 3–7 of them:

```
[calc]  5-key change = 7.17 mA × 0.099 mV/mA = 0.71 mV = 0.0215 %
        at the playing code 1747: 0.38 LSB
        with a realistic 0.02 mV/mA instead: 0.08 LSB
```

**The play-rate figure is 0.1–0.4 LSB, not 3.2.** The §2 conclusion ("still
fine, and no longer negligible … accepted, not ignored") survives comfortably —
but the number being defended is 8–30× smaller than stated, and the *reason* to
record it (so nobody blames firmware) is worth more than the number.

### The terms that are actually bigger — and are not calibratable

`VDD` *is* `VREF` `[repo] bom.csv:6`, so the MCP3202 has **no supply rejection
by construction**: rail movement appears 1:1 as scale error, at whatever
frequency the rail moves. The page notices this ("the ADC's scale factor is the
dev board's LDO output, and it has no anti-alias filter of its own")
`[repo] carrier.md §2` and then prices only the DC term.

**(i) The MCU's own transient load.** The same LDO powers the ESP32-S3 core.
Its 3V3 current steps by tens of milliamps on flash access and CPU wake, and by
hundreds if the radio is ever used `[repo] 0005 gives 40–80 mA for the ESP32-S3
and a +110 mA row for live config over WiFi`.

```
[from memory]  LDO loop bandwidth ~30 kHz → recovery window 1/(2π·30e3) = 5.3 µs
[from memory]  dev-board output capacitance ~33 µF (module + board bulk)
[calc]  100 mA step: ΔV = 0.1 × 5.3e-6 / 33e-6 = 16 mV = 0.48 %
                     at the playing code 1747 → 8.4 LSB
[calc]  350 mA step: ΔV = 56 mV = 1.7 %       → 30 LSB at the playing code
[calc]  MCP3202 conversion window = 18 clocks / 0.9 MHz = 20 µs
        — longer than the 5.3 µs dip, so a dip lands INSIDE a conversion
```

**8–30 LSB of reference corruption on a random subset of samples**, against the
3.2 LSB the page worries about. It is uncorrelated with the sampler, so it
appears as spikes, not as a gain term — which means auto-zero cannot remove it
and the note-gate threshold can be tripped by it. 30 LSB is 1.9 % of the
~1598-count playable span `[calc] 30/1598`.

**(ii) The buck's switching ripple through the LDO's HF PSRR.**

```
[repo] bom.csv   R-78E5.0 switches at ~330 kHz
[from memory]    its output ripple ≈ 40 mVpp
[from memory]    a small CMOS LDO's PSRR at 330 kHz ≈ 25 dB
[calc]           40 mV × 10^(−25/20) = 2.25 mV on 3V3 = 0.068 % = 1.2 LSB at play
[calc]           alias: 330 000 − 82 × 4000 = 2000 Hz — exactly Nyquist,
                 and it MOVES with the buck's load-dependent frequency
```

Small, but it is a wandering tone and `C-AA-ADC` is powerless against it —
**`C-AA-ADC` filters the input, not the reference.** That asymmetry is the
thing to hold on to.

### The fix: `C-ADC-BULK` should be an R–C, not a C

The `C-ADC-BULK` proposal (10 µF X7R at `VDD`) is the right instinct and the
wrong component count. A capacitor alone does little, because the header pin and
trace between the dev board's LDO cap and the ADC's cap is only ~50 mΩ:

```
[calc]  corner with 50 mΩ + 10 µF = 1/(2π · 0.05 · 10e-6) = 318 kHz — no filtering
```

Add a deliberate series resistor. The MCP3202's own supply current is tiny and
essentially constant, and — crucially — **the 25.8 mA of key pull-up current
does not flow through it**, so the resistor costs almost nothing:

```
PROPOSE:  R-ISO-ADCVDD  10 Ω  +  C-ADC-BULK  47 µF   (keep the 100 nF at the pin)

[calc]  corner = 1/(2π · 10 · 47e-6) = 339 Hz
        at 330 kHz: 20·log10(330000/339) = 59.8 dB → 2.25 mV → 2.3 µV → 0.003 LSB
        at 16 kHz (the MCU dip's characteristic frequency):
                    20·log10(16000/339) = 33.5 dB → 56 mV → 1.2 mV → 0.6 LSB
[from memory]  MCP3202 IDD ≈ 550 µA
[calc]  static drop = 10 Ω × 550 µA = 5.5 mV = 0.17 % — a fixed gain error,
        calibrated out by the panel GAIN knob exactly as ADR 0003 allows
[calc]  droop during a conversion (assume 1 mA peak for 20 µs):
        ΔV = 1 mA × 20 µs / 47 µF = 0.43 mV = 0.53 LSB, systematic, identical
        every conversion → a gain term, not noise
```

**One resistor takes the two largest and least correctable errors on this node
from 8–30 LSB and 1.2 LSB down to 0.6 LSB and 0.003 LSB, and leaves standing
only the DC pull-up term — the small one, which is also the only calibratable
one.** That is the right division of labour and it is two millimetres of board.

Logic-level check: the ADC's `VDD` then sits 5.5 mV below the ESP32's 3V3, so
`CS`/`CLK`/`DIN` arrive 5.5 mV above `VDD` — far inside `VDD + 0.3 V` abs-max
`[from memory]`, and `DOUT` at `VDD − 5.5 mV` is still a valid high into the
ESP32 `[from memory]`.

**Note on the stated reason for `C-ADC-BULK`.** §2 justifies it by the WS2815's
~2 kHz PWM `[repo] carrier.md §2, bom.csv:46`. Trace that path: the strips run
from +12 V directly; the conducted route to 3V3 is +12 V → R-78E5.0 → dev-board
LDO, and both reject the audio band hard:

```
[from memory]  buck audio-band rejection ~40 dB; LDO PSRR at 2 kHz ~50 dB
[calc]         combined 90 dB: 178 mV of 2 kHz ripple → 5.6 µV on 3V3 → 0.007 LSB
```

(The 178 mV is derived in §7 below.) **The WS2815 is not a conducted threat to
the ADC reference.** The reason to fit the R–C is the buck's 330 kHz and the
MCU's own transients. Fit the part; fix the reason on the page, or the next
person to re-derive it will delete it.

---

## 5. `AGND-local` ↔ `PWR_GND` — the missing layout constraint

The §2 decision — analog supply return on `PWR_GND`, `AGND` sense-only, one tie
at the umbilical connector — is right, and §4 above confirms it numerically.
What §2 does not write is the constraint that makes it true on copper.

**This board carries the WS2815 feed points.** `C-STRIP-BULK` 470–1000 µF ×2
sits here, and `J-LED-L`/`J-LED-R` leave from here `[repo] carrier.md §1, §5,
bom.csv:46`. The current is:

```
[repo] 0005   clamp-legal worst: ~531 mA on the umbilical if spent on the strips
[repo] 0005   clamp fails, strips latched full white: 1023 mA
[repo] bom.csv  PWM rate ~2 kHz
```

Half an amp to an amp of 2 kHz-modulated current, returning across a 2-layer
board `[repo] bom.csv:69` that also carries the ADC's ground reference.

```
[from memory]  1 oz copper: 0.5 mΩ per square
[calc]  1 mΩ of copper shared between the MCP3202's ground pin and the bottom
        of R-ADCDIV-L:   0.53 A × 1 mΩ = 530 µV = 0.66 LSB, at 2 kHz
[calc]  10 mΩ shared (≈ 20 squares — a 20 mm run of narrow pour):
                         0.53 A × 10 mΩ = 5.3 mV = 6.6 LSB
```

**Six LSB, modulated by the light show, at exactly the frequency the page is
already nervous about.** Bigger than every other error term on the page put
together, and it is decided at layout, not at schematic.

For contrast, the currents that do *not* matter:

```
[calc]  key pull-up return, 25.8 mA through ~2.5 mΩ  = 65 µV  = 0.08 LSB
[calc]  analog section's own 13 mA [repo] carrier.md through a few mΩ = tens of µV
```

**Write these as layout rules on §2 before `PCB-CARRIER` is drawn:**

1. `C-STRIP-BULK` sits directly at `J-LED-L`/`J-LED-R`'s pins so the 2 kHz
   loop closes locally and does not traverse the board. (§5 already says "bulk
   belongs where the current swings" `[repo] carrier.md §5` — make it a
   placement rule, not a principle.)
2. The LED return path from `J-LED-*` to `J-UMB` pin 6 is a dedicated,
   identified copper path that does **not** overlap the analog region.
3. `AGND-local`'s single tie to `PWR_GND` lands **at `J-UMB` pin 6's pad
   itself**, not at a point in the LED return path.
4. The MCP3202's ground pin, `R-ADCDIV-L`'s low end and `C-AA-ADC`'s low end are
   **the same copper, joined at one point**, with a target of <1 mΩ between them.
5. `MECH-GNDBOND` (plate to `PWR_GND` `[repo] carrier.md §1`) is another high-
   current-capable node in the same pour; keep it off the analog tie too.

---

## 6. `ADCIN` — divider, anti-alias, sequencing, and the power-down dump

### The divider, recomputed

```
[calc]  ratio = 15k/(10k+15k) = 0.600                      ✓ repo
[calc]  R_th  = 10k·15k/25k   = 6.00 kΩ                    ✓ repo
```

But full scale is wrong. The transfer function, evaluated at the part's own
range limit:

```
[repo] 0003   Vout = VS · (0.1533·P + 0.04)
[calc]        at P = 6 kPa, VS = 5.000 V:  5 × (0.9198 + 0.04) = 4.799 V
```

**4.799 V, not 4.7 V.** ADR 0003 says 0.2–4.80 V in its prose and its GP/DP
comparison table; `bom.csv` row 5 and `carrier.md` §2 both say 4.7 V
`[repo] 0003, bom.csv:5, carrier.md`. The repo carries both figures. Redo §2's
counts on the right one:

```
[calc]  full scale:  4.799 × 0.6 = 2.879 V → 2.879/3.3 = 87.3 % → 3575 counts
        (§2 says 85 % / 3502; 4.7 × 0.6 / 3.3 × 4096 = 3500, so 3502 is also
         2 counts off its own premise)
[calc]  real play 2.8 kPa: 5 × (0.1533·2.8 + 0.04) = 2.346 V → 1.408 V → 1747 counts
        (§2 says 2.34 V / 1743)
[calc]  rest 0.2 V → 0.12 V → 149 counts
[calc]  playable span = 1747 − 149 = 1598                  ✓ §2's 1594
```

The conclusions are unaffected. Fix the number so the next derivation starts
from the right place.

**Headroom check §2 does not do.** The sensor does not hard-clip at its range
limit; over-pressure drives its on-chip amplifier toward its own 5 V rail. An
adult against a full occlusion makes 15–20 kPa `[repo] 0003`.

```
[calc]  saturated sensor ≈ 4.9 V → × 0.6 = 2.94 V → 89 % of a 3.3 V reference
```

**Still inside range.** The 0.6× divider survives a saturated sensor with 360 mV
to spare. Worth recording — it is the only thing standing between a sneeze and
a clamp event.

### Anti-alias: the right corner, defended with the wrong number

```
[calc]  f_c = 1/(2π · 6.00 kΩ · 47 nF) = 564.4 Hz            ✓ repo
[calc]  τ   = 6 kΩ × 47 nF             = 282 µs              ✓ repo
[calc]  at 330 kHz: 20·log10(330000/564.4) = 55.35 dB        ✓ repo's 55 dB
```

That last line is the *easy* case. For a 4 kHz sampler the frequency that
matters is the one that folds onto the top of the signal band — with the
sensor's own 159 Hz limit `[repo] bom.csv:5`, that is `4 kHz − 160 Hz`:

```
[calc]  at 3.84 kHz: 20·log10(3840/564.4)  = 16.65 dB
[calc]  at 2.00 kHz (Nyquist): 20·log10(2000/564.4) = 10.99 dB
```

**16.6 dB, not 55.** A single pole at 564 Hz is a very weak anti-alias filter
for a 4 kHz sampler. The page never checks this frequency, so it never has to
answer the question.

**The answer, having checked every path that could put energy at 3.4–4.6 kHz:**

| Source | Frequency | Path | Level at `ADCIN` |
|---|---|---|---|
| Breath signal | DC–70 Hz | direct | in band, not aliased |
| Tube pipe mode | 214–429 Hz `[repo] 0003` | direct | in band, **below** 564 Hz — the filter does not remove it and the ADR says so `[repo] 0003` |
| Sensor's own bandwidth limit | 159 Hz `[repo] bom.csv:5` | — | nothing above it is signal |
| WS2815 PWM + harmonics | ~2, 4, 6 kHz `[repo] bom.csv:46` | conducted: 90 dB down `[calc] §4` ; coupled: **layout** `[calc] §5` |
| R-78E5.0 switching | ~330 kHz `[repo] bom.csv:44` | 55.4 dB `[calc]` |
| Op-amp / sensor noise | broadband | NEB = (π/2)×564 = 886 Hz < fs/2 = 2 kHz `[calc]` → **no folding penalty at all** |

**Nothing lives at 3.4–4.6 kHz on any conducted path, so 16.6 dB is enough.**
564 Hz is the right corner. But it is right by good fortune plus the sensor's
own band limit, not by the 55 dB argument the page makes, and the one path that
*could* break it is the WS2815's coupled 2 kHz — which is §5's layout rule.

If more margin is ever wanted, note that lowering the corner is an expensive way
to buy it:

```
[calc]  100 nF instead of 47 nF: f_c = 265 Hz; at 3.84 kHz = 23.2 dB (+6.6 dB)
        cost: τ = 600 µs, which pushes the added rise time to 0.37 ms = 7.3 %
        of the 5 ms gesture budget
```

A second pole would be cheaper than a lower first pole. Not recommended on the
evidence above; recorded so the trade is visible.

### The τ = 282 µs worry is overstated by 3×

§2 says "τ = 282 µs exceeds the 250 µs loop period … About 5.6 % of the 5 ms
budget" `[repo] carrier.md §2`. A time constant is not a delay. Cascading it
with the sensor's own 1 ms:

```
[calc]  sensor 10–90 rise: 2.2 × 1.0 ms   = 2.200 ms
        RC     10–90 rise: 2.2 × 282 µs   = 0.620 ms
        combined ≈ √(2.200² + 0.620²)     = 2.286 ms
        ADDED   = 2.286 − 2.200           = 86 µs  = 1.7 % of the 5 ms budget
```

**86 µs, not 282 µs; 1.7 %, not 5.6 %.** The page's own conclusion ("not fatal")
is if anything too grudging.

### Sequencing — right conclusion, arithmetic missing the lower leg

```
§2's case A: 3V3 at 0, ADC pin clamped at ~0.7 V
[calc]  through R-ADCDIV-U: (4.799 − 0.7)/10 kΩ = 410 µA
        through R-ADCDIV-L: 0.7/15 kΩ           =  47 µA  ← §2 omits this
        into the clamp:                            363 µA
[from memory]  family-typical input clamp rating ±2 mA → 18 % of it

§2's case B: buffer stuck at +12 V, 3V3 up, pin clamped at 3.3+0.7 = 4.0 V
[calc]  through R-ADCDIV-U: (12 − 4.0)/10 kΩ = 800 µA
        through R-ADCDIV-L: 4.0/15 kΩ        = 267 µA     ← §2 omits this
        into the clamp:                         533 µA     (§2 says 800 µA)
```

Conservative in the safe direction. The ≥10 kΩ upper-leg rule is correct and
should stand.

### The case §2 misses: `C-AA-ADC` dumps into the clamp on every power-down

When 3V3 collapses — normal power-off, a hot-unplug, or pulling the dev board
out of its socket, which `HDR-DEV` makes routine `[repo] bom.csv:71` —
`C-AA-ADC` still holds the ADC input at whatever the divider left there, while
`VDD` goes to zero. The divider resistors limit the *sustained* current; they do
nothing about the charge already on the cap.

```
[calc]  worst case (power cut at full blow): Q = 47 nF × 2.879 V = 135 nC
        at rest:                             Q = 47 nF × 0.12 V  = 5.6 nC
[from memory]  HBM reference: 100 pF × 2 kV = 200 nC
[calc]  discharged in ~100 ns through the clamp → ~1.4 A peak
```

**A sub-HBM but CDM-class pulse into a CMOS substrate diode, on every power-down,
for the life of the instrument.** Not certain to do damage; certainly not
something to leave undesigned on an unretrofittable board.

```
PROPOSE:  R-ADCIN-SER  100 Ω, between the R-ADCDIV/C-AA-ADC node and MCP3202 CH0

[calc]  limits the dump to 2.879/100 = 28.8 mA
[calc]  cost to acquisition: sample cap 20 pF through 100 Ω → τ = 2.0 ns
        against a 1.5-clock acquisition window at 0.9 MHz = 1.67 µs — 835 τ
[calc]  cost to the anti-alias corner: none — the cap stays on the source side
[calc]  cost to charge sharing: unchanged, since C-AA-ADC is still the reservoir
        (§2's own 0.048 % / ~2 LSB constant gain term is unaffected)
```

An alternative is a BAT54 from `ADCIN` to `VDD_ADC`, but that is a part where
100 Ω is a part *and* fixes the sequencing case too.

Related, same node: with `HDR-DEV` being a **socket**, "instrument powered,
dev board removed" is a real bench state. Then `VDD_ADC` floats and the divider
feeds the ADC through its own clamp:

```
[calc]  (2.879 − 0.7)/10 kΩ = 218 µA into a floating VDD node holding only
        C-ADC-BULK; the part sits partially biased in an undefined state
```

Not damaging, but it also back-feeds `J-CHAIN` pin 10's 3V3 to the shift
registers `[repo] carrier.md §3`. The 100 Ω above does not fix this one; a note
on the page ("do not apply +12 V with the dev board out of its socket") is
probably the proportionate response. **Low.**

---

## 7. `VS`, `VBUF` — op-amp loading, and rail rejection

### OPA2197-B driving the cable: stable, and by a wide margin

```
[repo] 0003/0004  ~200 pF of cable at 2 m — consistent with Cat5e's ~50 pF/m
                  mutual capacitance [from memory]
```

The 1 kΩ sits **outside** the loop (the divider tap is taken at the op-amp
output side of it `[repo] carrier.md §2`), so the cable never reaches the
op-amp:

```
[calc]  at the op-amp's crossover (10 MHz) 200 pF is 80 Ω, so the load through
        the 1 kΩ is ~1 kΩ resistive. The divider's 10 kΩ in parallel with the
        1 kΩ, with C-AA-ADC a short at those frequencies, gives 909 Ω.
        Nothing capacitive reaches the output pin.
[calc]  bandwidth into the cable: 1 kΩ × 200 pF = 200 ns → 796 kHz,
        5000× the 159 Hz signal
[web]   output current capability ±65 mA (ti.com/product/OPA2197 search summary)
[calc]  actual load current at 4.8 V into 1 kΩ + 2 m + the module's ~1.01 MΩ:
        4.8 / 1.011e6 = 4.7 µA
```

**The breath buffer half is fine.** Only the reference buffer half is not (§1).
Worth saying explicitly because "OPA2197 stability" is otherwise easy to
conclude either way about the package as a whole.

Output swing at the bottom of range is also fine: the sensor's pedestal spec
band is 0.152–0.378 V `[repo] breath-receive-stage.md:80`, and an OPA2197 on a
single +12 V reaches within ~30 mV of ground `[repo] 0003, from memory`. The
input common-mode at 0.15 V is inside a rail-to-rail-input part's range
`[from memory]`.

### +12 V rail rejection: a non-problem, recorded so it is not over-engineered

The OPA2197's `V+` and the REF5050's input both tap the **raw** umbilical +12 V,
upstream of `L-BUCK-IN` `[repo] carrier.md §1`. That node carries the WS2815
current:

```
[repo] 0003   2 m of 24 AWG = 0.168 Ω per conductor
[repo] 0005   ~531 mA of strip current at the clamp-legal worst
[repo] bom.csv  PWM at ~2 kHz
[calc]  ripple on the local +12 V = 0.531 A × (2 × 0.168 Ω) = 178 mV
```

Through both analog parts:

```
[repo] bom.csv:25  REF5050 line regulation ~5 ppm/V
[calc]             178 mV × 5 ppm/V = 0.89 ppm of 5 V = 4.5 µV on VS
[from memory]      OPA2197 PSRR ≈ 114 dB DC with a ~10 Hz dominant pole
[calc]             at 2 kHz: 114 − 20·log10(2000/10) = 68 dB
[calc]             178 mV × 10^(−68/20) = 71 µV at VBUF
                   × 2.185 at the in-amp = 155 µV of a 10 V output = 16 ppm
                   — and 2 kHz is above the module's 482 Hz pole, so another 12 dB
```

**Four microvolts and seventy microvolts.** No filtering, ferrite or separate
analog rail is needed on `+12 V` for the analog front end. This closes an
argument that would otherwise get re-litigated.

---

## 8. `P1`/`P2` — the sensor, thermally and at altitude

### Altitude: no effect on the measurement — one caveat

With `P2` open to the cavity and the cavity leaking through eighteen switch
cutouts `[repo] 0003`, the measurement is a gauge measurement of tube pressure
against ambient. **Ambient pressure cancels in `P1 − P2` and there is no
altitude term in the reading at all.** The tube is dead-ended at the sensor and
open at the mouthpiece `[repo] 0003`, so it equalises too.

The one caveat is a failure mode nobody has written down: **a capped
mouthpiece.** Capping a mouthpiece is the natural hygiene move and ADR 0003
specifies the mouthpiece as "removable and cleanable" `[repo] 0003`. Cap it and
the 400 mm × 3 mm tube becomes a sealed 2.83 mL volume `[repo] 0003 gives the
2.83 mL`:

```
[calc]  airliner cabin at ~2400 m: 75.3 kPa [from memory]
        trapped tube sits 101.3 − 75.3 = 26.0 kPa above ambient
        = 4.33 × the sensor's 6 kPa full scale, sustained for the flight
```

Whether the diaphragm survives depends on the part's maximum-pressure rating,
which I could not read (`nxp.com`, `st.com` blocked). Even if it does, the
instrument reads pinned until the cap comes off. **Build rule: the mouthpiece is
never capped, and if it is ever given a cap, the cap is vented.** `[Note]`

### Thermal, in normal play: quantified and benign

Two thermal mechanisms, both of which turn out to be non-issues, and it is worth
showing the arithmetic because the closed tube invites the worry:

**(a) The trapped tube volume while the lips seal the mouthpiece.**

```
[calc]  tube air thermal mass = 2.83e-6 m³ × 1.2 kg/m³ × 1005 J/kg·K = 3.41 mJ/K
        tube internal area = π × 3 mm × 0.4 m = 3.77e-3 m²
[from memory]  natural convection inside a small tube h ≈ 10 W/m²·K
[calc]  τ = 3.41e-3 / (10 × 3.77e-3) = 0.090 s
```

So the tube air tracks the tube wall in ~90 ms, and the wall tracks the body
interior over minutes. During a 10-second held note with the lips sealed and the
interior warming at 10 K over 600 s:

```
[calc]  ΔT over the note = 0.167 K
        ΔP = 101.3 kPa × 0.167 / 293 = 57.7 Pa = 0.96 % of full scale
```

**One percent of full scale on the longest realistic held note.** Negligible,
and between notes the lips part and it vents. The closed tube is thermally sound
in play.

**(b) A sealed reference chamber.** ADR 0003's 5.2 kPa checks out, and the worst
case is worse than quoted:

```
[calc]  ΔT = 15 K from 288 K: 101.3 × 15/288 = 5.28 kPa   ✓ repo's 5.2
[calc]  ΔT = 20 K from 293 K: 101.3 × 20/293 = 6.91 kPa   = 115 % of full scale
```

At the top of ADR 0009's own 10–20 K interior rise `[repo] 0009`, the sealed
case is beyond full scale, not merely near it.

### The failure the repo has not costed: a *partial* seal

ADR 0003 treats the reference port as binary — open, or sealed by coating/
adhesive `[repo] 0003`. The realistic outcome of masking a 1351-01 port stub
that has a silicone tube routed past it, on a part that is socketed and then
conformally coated `[repo] bom.csv:53, 77`, is **neither**: a restricted leak.

Model it as a leak with time constant τ against an interior warming at 1 K/min:

```
[calc]  quasi-steady offset = P · (dT/dt) · τ / T
        with τ = 60 s:  101.3e3 × (1/60) × 60 / 293 = 346 Pa = 0.346 kPa
                      = 5.8 % of the 6 kPa full scale, NEGATIVE, sustained
                        through the whole warm-up
[calc]  at 766 mV/kPa: 265 mV at the sensor output
[calc]  × 2.185 at the in-amp: 579 mV at its output
```

**Half a volt of drifting offset at the breath jack, for the first twenty
minutes of every session.** And here is why it is nastier than the full-seal
case:

- **The digital copy hides it.** ADR 0006's auto-zero "decays toward the current
  reading whenever breath has been sub-threshold for ~2 s" `[repo] 0006`, so
  firmware chases the drift and reports a healthy zero throughout.
- **The analog path has no auto-zero at all** — its only zero authority is the
  panel OFFSET knob, by explicit decision `[repo] 0003, 0006`.
- So the instrument reports itself healthy while its CV output wanders by
  hundreds of millivolts, and then re-centres once thermally settled, leaving
  the firmware zero biased the other way.

ADR 0003 names the right test — "Run the sensor from cold through twenty minutes
of playing and watch for output that falls rather than drifts" `[repo] 0003` —
but does not say **which output**. On the ADC reading the test passes even when
the fault is present.

**Recommendation:** E2's warm-up check is a voltmeter on the *analog* path (at
`VBUF`, or at the breath jack with the trimmer set), not on the ADC. And a
cheap firmware diagnostic exists for free: a reading that walks *below* the
cold-start zero by more than a few percent is the blocked-reference signature
and nothing else produces it. ADR 0006's auto-zero already gates on
"sub-threshold *and* quiet" `[repo] 0006`; adding "and not below the cold
zero" costs a comparison.

### Operating temperature range

```
[web]  "2.5 % Maximum Error over +10 °C to +60 °C with Auto Zero",
       "Operating Temperature TA: +10° to +60 °C"
       (search summary of the ST-hosted MPXV4006DP datasheet,
        https://www.st.com/resource/en/datasheet/mpxv4006dp.pdf — the PDF
        itself was blocked)
```

The interior runs 10–20 K above ambient `[repo] 0003, 0009`, so a 20 °C room is
comfortably inside. **A cold start is not.** A rack carried in from a car in
winter, or a cold venue, puts the part below +10 °C where its error is
unspecified. Auto-zero catches the offset part; the span part is uncorrected.
Worth one line in the E2 acceptance criteria and nothing more. `[Note]`

Also unbudgeted anywhere: **TcSpan**. Auto-zero (digital) and the OFFSET trimmer
(analog) both correct *offset*. Nothing corrects span drift over the 10–20 K
rise, and the 2.5 % figure above is the combined accuracy including it. 2.5 % of
span, drifting over twenty minutes, is absorbed by the player's ear and the GAIN
knob. Fine — but say so, rather than leaving it to be discovered. `[Note]`

### Mechanical rules — confirmed, one addition

§2's three rules (route the tube so it cannot cover the reference port; mask both
ports before `MECH-COAT`; settle which port is P1) are the right three
`[repo] carrier.md §2`. One addition, from the geometry: on case 1351-01 both
ports are on the same face on close centres `[from memory] ~7.5 mm`, so the
400 mm silicone tube on `P1` is always within a centimetre of `P2` and is
flexible. **Make it a mechanical restraint, not a routing intention** — a clip,
a printed spacer, or a tube long enough that its natural lie is away from the
stub. "Route it so it cannot" is an instruction to the builder that the builder
cannot verify after bonding.

---

## 9. Loose ends and things I could not check

- **`C-REF-OUT` qty 2 for one REF5050** `[repo] bom.csv:75, carrier.md` — still
  open, and §1 above shows it changes the buffer's oscillation frequency by a
  decade. The REF50xx datasheet wants 1–50 µF with 1–1.5 Ω ESR at the *output*
  `[web]`, which argues for one on the output and the second as the 100 nF's
  bulk partner — but this needs a datasheet reading, not an inference.
- **MPXV4006DP maximum pressure rating** — needed for §8's capped-mouthpiece
  case. Blocked.
- **MPXV4006DP IDD vs pressure** — needed to confirm §1's out-of-loop
  recommendation. Blocked.
- **MCP3202 input clamp current rating and max clock at 3.3 V** — §2 and §4 both
  rest on "family-typical ±2 mA" and 0.9 MHz. Search confirms 1.8 MHz at 5 V and
  ~0.9 MHz at 2.7 V from the datasheet's clock-vs-VDD graph `[web] farnell
  DS21034F summary`; 3.3 V is genuinely unspecified and interpolating to
  ~1.1 MHz would be the optimistic reading. Designing to 0.9 MHz, as §4 does, is
  right.
- **The dev board's actual LDO** — Waveshare's ESP32-S3-Matrix schematic was
  blocked. The sibling ESP32-S3-Zero uses ME6217C33M5G, 800 mA `[web]
  circuitstate.com`. If the Matrix uses the same part, its load regulation,
  PSRR and output capacitance are the three numbers that set §4's whole
  analysis, and none of them is in the repo. **Measure them at E1** — a scope on
  3V3 while toggling 18 key inputs and while running a WiFi burst is a
  ten-minute bench task that replaces three `[from memory]` markers with
  measurements.
- **Whether `D-TVS-BREATH`'s position in §2's ASCII is intentional.** I have
  read it as drawn. If it is drawing shorthand, say so on the page; the position
  is the part's entire function.
- I did not review §3's chain drive, §4's SPI egress beyond the ADC clock, §5's
  LED data or §6/§7, except where they load the 3V3 reference or the analog
  ground.

---

## 10. Concrete changes proposed to `carrier.md` §2

Schematic (unretrofittable, must land before layout):

1. Draw `R-ISO-REF` and say which side of the loop it is on. Recommend
   out-of-loop at 4.7–10 Ω, or a series R–C snubber at `VS` for zero DC error.
   If the in-loop form is kept, add `R_F` 10 kΩ and `C_F` 1 nF and draw the
   feedback at `VS`.
2. Draw `R-SER-BREATH-INST` **×2** — R1 in BREATH, R1b in AGND — and mark the
   count in the component table.
3. Move `D-TVS-BREATH` to the connector side of `R-SER-BREATH-INST`.
4. Add `R-ADCIN-SER` 100 Ω between the divider/`C-AA-ADC` node and MCP3202 CH0.
5. Change `C-ADC-BULK` from `10 µF` to `10 Ω + 47 µF`, and restate its reason as
   the buck's 330 kHz and the MCU's transients rather than the WS2815's 2 kHz.

Layout constraints to write onto §2 now (§5 above):

6. `C-STRIP-BULK` at the `J-LED-*` pins; LED return on identified copper that
   does not cross the analog region; `AGND-local`'s single tie at `J-UMB` pin 6's
   pad; MCP3202 ground / `R-ADCDIV-L` low / `C-AA-ADC` low on one copper node at
   <1 mΩ.

Numbers to correct on the page:

7. Full scale 4.799 V, not 4.7 V; 3575 counts, not 3502; 1747 at play, not 1743.
8. Added rise time 86 µs / 1.7 % of budget, not 282 µs / 5.6 %.
9. Key pull-up reference error at the playing code: 1.35 LSB worst case,
   0.1–0.4 LSB at realistic play-rate steps — not 3.2 LSB. Keep the
   `~0.3 %/100 mA` figure but mark it as an upper bound pending E1 measurement.
10. Clamp currents 363 µA and 533 µA, not 400 µA and 800 µA (the lower divider
    leg was omitted).
11. Anti-alias: quote 16.6 dB at 3.84 kHz alongside the 55 dB at 330 kHz, and
    state the conclusion that survives it — the corner is right because the
    sensor is band-limited to 159 Hz and nothing conducted lives at 3.4–4.6 kHz.

Test-plan additions:

12. E1: measure the dev board's 3V3 load regulation, PSRR at 330 kHz, and
    output capacitance. Three `[from memory]` markers die at once.
13. E2: run the warm-up check on the **analog** output, not on the ADC reading.
14. E2/E14: verify the reference buffer does not oscillate — a scope on `VS`
    with the sensor fitted, before anything else on this board is trusted.
