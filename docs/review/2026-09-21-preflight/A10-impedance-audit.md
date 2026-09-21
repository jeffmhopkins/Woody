# A10 — Impedance at every boundary

**Cold review, 2026-09-21.** Slice: **what each stage presents to the next**,
whether the driver can drive it, and what the loading costs. Per-page reviewers
own the insides of their stages; this report owns only the interfaces between
them, which is what a page-by-page decomposition structurally cannot see.

**Prior review directories were not read.** Design corpus, `config/figures.yaml`,
`hardware/bom.csv` and the 75 banked datasheets were read freely. Where the
corpus cites a prior review by label (`A2`, `A5`, `B1`, `B6`, `R10`) I took the
citation as repo text and re-derived the number rather than reading the source.

**Provenance on every claim.** `[datasheet <doc> p.N]`, `[repo file:line]`,
`[calc]` with the arithmetic shown, `[from memory]`. Unmarked = defect.

---

## The table

| # | Boundary | Z_source | Z_load | Error it causes | Verdict |
|---|---|---|---|---|---|
| **1** | DAC8568 out → `R-OPAMP-IN` → op-amp (+), pitch | **4 Ω** dc `[datasheet SBAS430E p.3]` | 1 kΩ + 10 nF; 100 kΩ `R-BIAS-DAC` at the pin | **40 ppm** gain (0.10–0.34 cents); Ib term **0.012 cents**; settling **104 µs** of 250 µs | **FINE — stop worrying.** Trimmable, and 3 orders below the 0.42 cents reference term |
| **1b** | Same, mod channels 1–4 | 4 Ω | 1 kΩ, **no shunt cap** | No dc error; the 4 kHz ZOH image and DAC glitch reach the op-amp ungated and are gained ×4 | **ASYMMETRY, not a defect.** State it; `C-AA-PITCH` is qty 1 `[repo bom.csv C-AA-PITCH]` |
| **2** | REF5050 → ½ OPA2197 → `R-ISO-REF` → sensor `VS` | Buffer **Z_cl = 18 mΩ at 482 Hz** `[calc from Zo 375 Ω, GBW 10 MHz]` | **0–10 mA** (spec has no typ) + 100 nF + `R-ISO-REF` | DC error **0 in-loop**; **2.0 % out-of-loop at 10 Ω, 7.5 % at TI's 37.4 Ω**. Loop margin 8.4° as drawn | **WORST BOUNDARY IN THE DESIGN.** Unstable, unretrofittable, and it *is* the breath scale factor |
| **3** | Divider → `C-AA-ADC` → MCP3202 CH0 | **6.0 kΩ** Thévenin | R_SS + 20 pF in 1.5 clocks | With the 47 nF: **83 τ, nil**. Without it: **0.39 LSB at 3.3 V**, and Fig. 4-2 forbids it | **FINE, BUT FOR THE WRONG REASON.** `C-AA-ADC` is load-bearing for accuracy, not just alias |
| **4** | `R1`/`R1b` → 2 m Cat5 → `R2`/`R3` → INA828 | 1 kΩ + cable, **balanced** | 100 GΩ ∥ 10 pF; 1 MΩ bias pair | CMRR floor **73 dB at dc, 66 dB at 482 Hz** (C_cm ±1 %) vs a 58.5 dB requirement | **ADEQUATE, MARGIN OVERSTATED.** 7.5 dB at the top of band, not 14.7 dB |
| **4b** | INA828 `REF` pin | Buffer **18 mΩ at 482 Hz** | **40 kΩ**, spec'd **< 5 Ω** `[datasheet SBOS792A p.22]` | 127 dB CMRR floor against the 78 dB the 5 Ω limit implies | **FINE — stop worrying.** 270× margin |
| **5a** | `POT-GAIN` wiper → `R-IN` | 0 → **12.5 kΩ** with rotation | 10 kΩ | Buffered: 0. Unbuffered would be **−56 % gain at mid-rotation** | **BUFFERED, AND CORRECTLY SO.** Corpus claim verified |
| **5b** | `POT-OFFSET` wiper → `R-OFF` | 0 → **2.5 kΩ** with rotation | 21.0 kΩ + a virtual ground | **+0.53 V at centre, +0.64 V peak** = 6.4 % of the ±5 V span; "zero" lands **18.7–20.1° past centre** | **DEFECT. The corpus states both answers and the wrong one is in two of three places** |
| **6** | Op-amp → `R-OUT-PROT` 1 kΩ → jack → rack (mods + breath) | **1 kΩ**, outside the loop | 100 kΩ typical; 50/33/25 kΩ on a passive mult; 10 kΩ on some inputs | **−0.99 % / −1.96 % / −3.85 %**; **−99 mV to −385 mV** on a ±10 V mod | **UNBUDGETED ON 5 OF 6 JACKS.** Pitch was fixed; nothing else was |
| **6b** | Same, **pitch** | ~**0 Ω** (1 kΩ inside the loop) | as above | **0 for any load** open→2 kΩ | **FIXED AND CORRECT.** ADR 0006's old section still argues the opposite |
| **7** | ESP32 GPIO → 100 Ω → 2 m Cat5 → 74AHCT125 | ~140 Ω (40 Ω pad + 100 Ω) | Z0 **100 Ω only for `CS`**; `SCLK`/`MOSI` have **no return in their own pair** | First step 2.75 V (CS) / ~3.67 V (SCLK, MOSI est.) vs V_IH 2.0 V | **PASSES, MODEL IS WRONG.** The 100 Ω figure does not apply to two of the three lines |
| **7b** | 74AHCT125 → DAC8568 digital ins | ~30–150 Ω | 3 pF + 10 kΩ pull, V_IH = **3.256 V** at AVDD 5.21 | V_OH 4.4 V min → **1.14 V** margin | **FINE — stop worrying.** A short board trace, not a line |
| **8** | Dev-board 3V3 → `F-CHAIN` → 265 mm loom → 4 clusters | LDO + **1.0–7.5 Ω** polyfuse `[datasheet MF-PSMF010X p.1]` | 25.7 mA peak (18 keys) | Fuse **26–193 mV**; loom itself **5.0 mV** | **FINE — stop worrying.** The BOM's objection is 3.9× overstated |

---

## Boundary 1 — DAC8568 output → op-amp input

**What the DAC presents.** `[datasheet SBAS430E p.3]` "DC output impedance | At
mid-code input | **4** | Ω". Output current capability ±20 mA; short-circuit
current 11 mA; settling 5 µs typ / 10 µs max (¼→¾ scale, ±0.024 %, unloaded);
slew 0.75 V/µs; **capacitive load stability 1000 pF at R_L = ∞, 3000 pF at
R_L = 2 kΩ**.

**What the pitch stage presents to it.** `R-OPAMP-IN` 1 kΩ, then `C-AA-PITCH`
10 nF to `AGND` on the op-amp side of that resistor `[repo hardware/module/pitch-stage.md:135-139]`,
then an OPA2197 (+) input, plus `R-BIAS-DAC` 100 kΩ to ground **at the DAC pin**
`[repo bom.csv R-BIAS-DAC]`.

### The 10 nF is not a capacitive load on the DAC

This is the first thing to check and it passes. The DAC's 1000 pF stability
limit applies to capacitance *on the pin*; `R-OPAMP-IN`'s 1 kΩ stands between
the pin and the 10 nF, which is three decades of isolation. Peak charging
current for a 5 V step is 5 mA `[calc: 5 V / 1 kΩ]` against ±20 mA capability.
**No action.**

### What the series resistor costs in settling

`[calc]` τ = 1 kΩ × 10 nF = 10 µs. One cent at the pitch jack is 1/1200 of an
octave = 0.833 mV at the jack, 0.417 mV at the DAC (gain 2). A worst-case 5 V
step settles to that in ln(5 / 0.000417) = **9.39 τ = 93.9 µs**. Add the DAC's
own 10 µs max and the pitch channel is settled to one cent in **104 µs of the
250 µs loop period** — 2.4× margin, and successive updates 250 µs apart leave
e^−25 of residual, i.e. nothing.

> **This term is not in `docs/reference/latency-budget.md`.** That page books
> bus time and ESP-IDF overhead `[repo config/figures.yaml loop-budget]` and no
> analog settling at all. It does not break the budget — the settling runs
> concurrently with the next loop's bus traffic — but a reader sizing the loop
> from that page has no idea the CV is still moving 104 µs after the write.
> Same class as the 282 µs ADC RC that `carrier.md` already flags as unapplied
> `[repo hardware/controller/carrier.md:365-370]`.

### Bias current across the series resistor — the answer is no

`[datasheet SBOS737C p.7]` I_B = ±5 pA typ, **±20 pA max at 25 °C**, and
**±5 nA max over −40 to +125 °C** (the D/SOIC-8 rows; the PW package is worse at
±15 nA). `[calc]` Even at the over-temperature maximum, 5 nA × 1 kΩ = **5 µV**
at the (+) input, ×2 through the stage = 10 µV at the jack = **0.012 cents**.
At 25 °C it is 0.02 µV. The 1 kΩ is free, exactly as `pitch-stage.md:91-95`
claims. **Verified; stop worrying.**

### `R-BIAS-DAC` is not free, but it is trimmable

`R-BIAS-DAC` sits **at the DAC pin** `[repo bom.csv R-BIAS-DAC]`, which is the
right side of `R-OPAMP-IN` — the page's reasoning that 100 kΩ after the 1 kΩ
would cost 1 % of gain is correct `[calc: 100/101 = 0.990]`. What nobody has
costed is what it costs *where it is*: the DAC's 4 Ω output impedance divides
against it.

```
[calc]  4 Ω / 100 kΩ = 40 ppm of gain, constant across code
        Using pitch-stage.md's own cents-per-gain table (:118-122):
          at −2 V:  40e-6 × 2 V = 0.080 mV = 0.096 cents
          at +7 V:  40e-6 × 7 V = 0.280 mV = 0.336 cents
```

**0.10–0.34 cents.** That is larger than the LT5400 ratio-tracking term
(0.027 cents) and comparable to the DAC INL term in the same table. It is a
pure static gain error, so `TRIM-GAIN` and firmware's affine both have full
authority over it and it does not belong in the *untrimmable* column — but it
belongs in the table, and it is not there `[repo hardware/module/pitch-stage.md:286-292]`.

### The mod channels have no filter at this boundary

`C-AA-PITCH` is qty 1 `[repo bom.csv C-AA-PITCH]`, and `mod-channels.md`'s
drawing shows `[1k]` into the (+) input with nothing shunting it
`[repo hardware/module/mod-channels.md:20-38]`. So on mods 1–4 the DAC's
zero-order-hold steps and its 0.1 nV-s code-change glitch `[datasheet SBAS430E p.3]`
arrive at the op-amp at full amplitude and are amplified **×4**, and the only
filtering is `C-FILT-MOD` 82 nF at the jack, *after* the gain. Pitch filters
before the gain; the mods filter after it. ADR 0006's own table records the
asymmetry without naming it as one `[repo docs/decisions/0006-cv-channel-allocation.md:752-757]`.

Not a defect — a modulation CV does not need it — but **say it is deliberate**,
because the next reader will find `C-AA-PITCH` at qty 1 and assume the other
five were forgotten.

---

## Boundary 2 — reference → buffer → sensor `VS`

This is the most expensive boundary in the instrument and the one the corpus is
furthest from closing. Three facts set it.

**1. The load is a spec band with no typical.** `[datasheet MPXV4006DP Table 1 p.3]`
"Supply Current | I_S | — | — | **10** | mAdc" — min and typ are both em-dashes.
Supply voltage 4.75–5.0–5.25 V, "Device is ratiometric within this specified
excitation range" (footnote 1). So **the buffer must hold 5.000 V into an
unknown 0–10 mA**, and every milliohm between the reference and the `VS` pin
multiplies by a current nobody can bound better than 0–10 mA.

**2. The corpus's 375 Ω correction is right, and the consequence for the DC
error is the opposite of what the corpus concluded.**

```
[calc]  DC error of an isolation resistor OUTSIDE the loop, at I_S = 10 mA max:
          R-ISO-REF at 10 Ω   → 100 mV → 2.00 % of 5.000 V
          TI's Figure 56 37.4 Ω → 374 mV → 7.48 % of 5.000 V
```

`bom.csv` and `breath-receive-stage.md` both reject out-of-loop isolation on the
2 % figure `[repo bom.csv R-ISO-REF; hardware/module/breath-receive-stage.md:345-348]`.
At TI's value the penalty is **7.5 %**, which does not merely lose the argument,
it ends it. The out-of-loop option is dead at any resistor large enough to
matter.

**3. TI's worked answer is not the out-of-loop option, and the corpus half-says
so.** `[datasheet SBOS737C §8.2.3 p.30, Figure 56]` "Precision Reference Buffer"
driving 10 µF: R_ISO 37.4 Ω, **R_F 1 MΩ taken at V_OUT**, R_Fx 10 kΩ + C_F 39 nF
at the op-amp output, 89° phase margin, 4 kHz bandwidth, *"any other load
capacitances require recalculation."* **R_F taken at V_OUT means the DC loop
closes at the load, so the DC error through R_ISO is zero.** Figure 56 is the
*in-loop* option with an AC path added — it is not a third choice between the
two the corpus has been arguing about, it is the resolution of that argument.
`figures.yaml`'s `riso-ref-topology` entry lists it as "none of the above"
`[repo config/figures.yaml riso-ref-topology]`; it is in fact the first option,
made stable.

### Can the buffer hold it?

`[datasheet SBOS737C p.8]` Z_O = 375 Ω, GBW 10 MHz, A_OL 120 dB min at ±18 V
into 2 kΩ, I_SC ±65 mA, output swing from rail 95/125 mV at R_L = 10 kΩ.

```
[calc]  Closed-loop output impedance of a unity follower, Z_cl(f) ≈ Zo / (1 + A(f)),
        with A(f) = GBW/f:      Z_cl(f) ≈ 375 × f / 10 MHz
           at dc      →  sub-µΩ (A_OL 120 dB min)
           at 100 Hz  →  3.8 mΩ
           at 482 Hz  →  18 mΩ      ← top of the breath band
           at 4 kHz   →  150 mΩ
        Z_cl reaches 5 Ω at f = 133 kHz.
```

So **within the signal band the buffer is a hard voltage source and the
10 mA load costs nothing at all** — provided the loop is closed and stable.
It is the stability, not the drive, that is the problem. 10 mA against I_SC
±65 mA is 6.5× margin; the output sits 5 V above the negative rail and 7 V
below the positive one, nowhere near the swing limits.

### The reference itself is not loaded, and that is worth saying

`[datasheet SBOS410O p.7]` REF5050 load regulation, Standard grade: 20 ppm/mA
typ, **30 ppm/mA max** at 25 °C, **50 ppm/mA over temperature**; recommended
output current **±10 mA**; I_SC 25 mA.

**Had the sensor been driven from the reference directly it would have sat at
100 % of the part's recommended output current** and cost up to 10 mA × 50 ppm/mA
= 500 ppm = 2.5 mV of scale factor, drifting with breath-correlated supply
current `[calc]`. It is not: the buffer's input draws picoamps, so the
reference's dc load is zero and the load-regulation term is **0 ppm**. The
buffer earns its place twice — for the drive and for the load regulation — and
the corpus only ever argues the first.

### Two load-capacitance facts the SPICE stage must be given explicitly

- **The `VS` node carries 100 nF, not 1 µF.** `C-DECOUPLE-CARRIER` is 100 nF and
  its row names the MPXV4006DP as one of its seven `[repo bom.csv C-DECOUPLE-CARRIER]`.
  But **the sensor datasheet's own Figure 3 recommends 1.0 µF on `V_s`**
  `[datasheet MPXV4006DP p.5, "Recommended Power Supply Decoupling"]`, with
  0.01 µF and 470 pF on the output. If anyone "follows the datasheet" during
  layout the load goes up 10× and every compensation number on this node is
  void. **Write 100 nF down as a decision, with the datasheet's 1 µF named and
  declined**, or the next reader will silently fix it.
- **`C-REF-OUT`'s 10 µF may or may not be on this node.** That is the open
  `cref-out-node` dispute `[repo config/figures.yaml cref-out-node]` and it is
  the single highest-value thing to settle before SPICE runs, because 100 nF and
  10.1 µF are two different circuits. Its resolution also lands the REF5050's
  own **1–1.5 Ω ESR requirement** `[datasheet SBOS410O §8.4.1 p.26, §9.2.1.2 pp.28-29]`,
  which an X7R 1206 does not meet and which `bom.csv` already flags as a missing
  series resistor `[repo bom.csv C-REF-OUT]`.

### What to change

Adopt SBOS737C Figure 56's topology, recalculated for 100 nF (or for 10.1 µF,
once `cref-out-node` is settled): R_ISO at TI's 37.4 Ω, DC feedback from the
`VS` pin through R_F, AC feedback from the op-amp output through R_Fx/C_F. DC
error stays zero — which is what `bom.csv`'s in-loop argument wanted — and the
89° comes from the second path, which the corpus's in-loop version never had.
`R-ISO-REF` at 10 Ω is not a small version of this; it is the unstable circuit
with a token resistor.

---

## Boundary 3 — sensor → divider → MCP3202

**Where the divider actually is, is drawn two different ways.** This is a live
topology disagreement of exactly the `cref-out-node` class, and no grep finds it:

- `hardware/controller/carrier.md:180-186` hangs `R-ADCDIV-U` off the **buffer's
  output**, alongside `R-SER-BREATH-INST`.
- `hardware/module/breath-receive-stage.md:22-26` hangs the "0.6× divider" off
  the **sensor's output node**, in parallel with the buffer's input.

**It matters.** On the buffer output the divider's source is a hard voltage
source, both representations (analog CV and digital ADC) come off one node, and
the ADC's 6 kΩ Thévenin is exact. On the sensor output the divider draws
`[calc]` 4.8 V / 25 kΩ = **192 µA** from a pin with **no output drive
specification and no minimum load anywhere in the datasheet** — Figure 3 shows
only capacitors `[datasheet MPXV4006DP p.5]` — and any on-chip output impedance
becomes a scale-factor difference *between* the two representations, which the
corpus's "the two are calibrated separately on purpose"
`[repo hardware/module/breath-receive-stage.md:283-285]` would then be papering
over in hardware rather than in firmware. **Settle it: the buffer output is
right.**

### Does it settle to 12 bits in 1.5 clocks?

`[datasheet MCP3202 DS21034F p.13]` "the source impedance (R_S) adds to the
internal sampling switch (R_SS) impedance, directly affecting the time that is
required to charge the capacitor, C_SAMPLE". `[p.2]` R_SS 1 kΩ, C_SAMPLE 20 pF,
C_PIN 7 pF. `[p.14 Fig 4-1]` acquisition = 1.5 clock cycles.

**The 1 kΩ is a 5.5 V number.** `[datasheet DS21034F p.2, table header]` "all
parameters apply at **V_DD = 5.5 V**". Figure 4-2's two curves make the
consequence visible — and this is the same trap the corpus just climbed out of
on the 74HC165's thresholds `[repo hardware/controller/cluster-boards.md:120-160]`.

`[calc]` Back-solving R_SS from Figure 4-2 (rendered at 900 dpi and read against
the log-x gridlines; the 0.1 LSB criterion needs N = ln(4096/0.1) = 10.6 τ):

| V_DD | Fig 4-2 at R_S = 6 kΩ | implied R_SS |
|---|---|---|
| 5 V | ~1.0 MHz | **~1.1 kΩ** — agrees with the spec'd 1 kΩ |
| 2.7 V | ~0.45 MHz | **~9.7 kΩ** |
| 3.3 V | not plotted | **~3 kΩ** `[calc, 1/(V_DD − V_th) fit, V_th ≈ 2.44 V]` |

At the design's 0.9 MHz with a 6.0 kΩ source and **no** capacitor at the pin:

```
[calc]  τ = (6.0 k + 3.0 k) × 20 pF = 180 ns ; t_acq = 1.5/0.9 MHz = 1.667 µs
        N = 9.26 τ  →  e^-9.26 × 4096 = 0.39 LSB
        f_CLK for 0.1 LSB = 1.5 / (10.6 × 9 kΩ × 20 pF) = 786 kHz  <  900 kHz
```

**So the bare divider is out of bounds against the datasheet's own criterion by
about 15 %**, and on the guaranteed 2.7 V curve — the curve the corpus
deliberately designs against for f_CLK `[repo hardware/controller/carrier.md:441-448]` —
it is out by 2×.

### `C-AA-ADC` is what makes it legal, and no document says so

With 47 nF C0G sitting on the ADC pin, the sampling switch does not see 6 kΩ at
all; it sees a capacitor 2350× larger than C_SAMPLE with milliohms of ESR.

```
[calc]  τ = (ESR + R_SS) × 20 pF ≈ 1 kΩ × 20 pF = 20 ns  →  83 τ in 1.667 µs
        Charge-sharing droop per sample = 20 pF / 47 nF = 426 ppm of the step
        Steady state: I_avg = 20 pF × 4 kHz × V = 80 nA/V
                      ΔV = 80 nA/V × 6.0 kΩ = 480 µV/V = 0.048 % = 1.97 LSB
```

The **1.97 LSB is a pure gain term** and `carrier.md:378-386` already derives it
correctly. What is missing is the sentence that matters: **the 47 nF is not an
optional anti-alias filter, it is the part that makes a 6 kΩ source legal at
900 kHz.** `carrier.md`'s component table half-knows this — "47 nF C0G | 564 Hz,
and the ADC's charge reservoir" `[repo hardware/controller/carrier.md:800]` —
but nothing states the consequence of shrinking or deleting it, and it sits on a
board where someone will eventually want the 282 µs τ smaller.

**If the 282 µs τ is ever reduced** (it exceeds the 250 µs loop period and
`carrier.md` flags it as unapplied to the latency budget), reduce it by lowering
the *divider*, not the capacitor: 4.02 k / 6.04 k keeps the 0.6 ratio at a
2.41 kΩ Thévenin, which halves the charge-sharing gain term as well `[calc]`.

**Minor, for SPICE:** CH1 is spare and undriven `[repo hardware/controller/carrier.md:190]`.
A floating mux input is a leakage path to the shared sample cap. Tie it to
`AGND` or to the CH0 node.

---

## Boundary 4 — instrument → 2 m Cat5 → INA828

### The REF pin: the requirement is met with 270× to spare

`[datasheet SBOS792A p.3]` pin 5 REF: "This pin must be driven by a low impedance
source." `[p.6]` R_IN = 40 kΩ, gain to output 1 V/V, reference gain error 0.01 %.
`[§8.1 p.22]` "any resistance at the reference terminal … is in series with one
of the internal 40-kΩ resistors … **keep the source impedance to the REF
terminal, R_REF, below 5 Ω**."

```
[calc]  5 Ω / 40 kΩ = 125 ppm of bridge imbalance → 78 dB CMRR floor.
        That is what TI's 5 Ω is buying.
        The OPA2197 buffer gives 18 mΩ at 482 Hz (Boundary 2) → 0.45 ppm → 127 dB.
```

`TRIM-BREATH-ZERO` is buffered `[repo bom.csv TRIM-BREATH-ZERO;
hardware/module/breath-receive-stage.md:151-160]` and the drawing shows nothing
in series after the buffer. **Verified, closed, stop worrying** — with one
layout rule: nothing may be added between that buffer's output and pin 5, not a
0 Ω link, not a test-point stub with a resistor in it. 5 Ω is three squares of
thin trace.

### Source-impedance balance: `R1b` is right and its stated benefit is right

```
[calc]  Reproducing breath-receive-stage.md:213-217 exactly:
        Without R1b, legs are 11 kΩ and 10 kΩ against the 1 MΩ bias pair:
          |1M/1.011M − 1M/1.010M| = 9.793e-4  →  60.18 dB
        With R1b, both legs 11 kΩ; residual is the 1 MΩ pair's own tolerance:
          δ = (11 k/1 M) × 2 % = 2.20e-4  →  73.15 dB
        R1b therefore buys 12.97 dB, not "fifty times".
```

Both figures reproduce to the digit. `carrier.md:150-157` states 13 dB and
corrects the receive page's "fifty times"; **the receive page was not corrected**
and still says "throws away fifty times that" at `:215`. One of the two is
wrong and the arithmetic says it is the receive page.

`[calc]` The 1 % series parts contribute nothing: a 1 % mismatch between `R1` and
`R1b` is 10 Ω against 1 MΩ = 10 ppm = 100 dB; the 0.1 % `R2`/`R3` pair gives the
same. **`R-BIAS-INAMP`'s tolerance is the entire dc CMRR budget.** It is 1 %
`[repo bom.csv R-BIAS-INAMP]`. Specifying 0.1 % on those two parts alone —
two 0805s, instrument-side, and therefore unretrofittable like everything else
here — takes the floor from **73 dB to 93 dB** `[calc]`. Against a stated
requirement of 58.5 dB `[repo hardware/controller/carrier.md:155]` that is free
margin nobody has claimed.

### The margin is smaller than stated, because the floor is frequency-dependent

The 73 dB figure is a dc number. `C_cm` mismatch converts common mode to
differential in proportion to R_series/X_c, which rises with frequency:

```
[calc]  δ ≈ (11 kΩ / X_c) × ΔC/C,   X_c = 1/(2π f × 1.5 nF)
        at  50 Hz, ±1 %: X_c 2122 kΩ → 85.7 dB       ±5 %: 71.7 dB
        at 482 Hz, ±1 %: X_c  220 kΩ → 66.0 dB       ±5 %: 52.0 dB
        at 2 kHz,  ±1 %: X_c   53 kΩ → 53.7 dB       ±5 %: 39.7 dB
```

So the receive page's "±5 % gives ~46 dB, ±1 % is needed to clear 60"
`[repo hardware/module/breath-receive-stage.md:220-223]` is the right conclusion
from the right mechanism, and the **±1 % C0G specification stands**. But the
number to carry forward is that **at the top of the 482 Hz signal band the CMRR
floor is 66 dB, not 73 dB** — 7.5 dB of margin over the 58.5 dB requirement, not
14.7 dB. At 2 kHz (the WS2815 PWM rate, which is the aggressor the corpus worries
about most `[repo bom.csv C-STRIP-BULK via carrier.md:388-392]`) it is **53.7 dB
and the requirement is not met at all** — though 2 kHz is four times the
differential pole, so what gets converted is then attenuated by `C_diff`.

**Hand SPICE both numbers and let it settle the 2 kHz case**, because it is a
two-pole interaction and this report's single-term arithmetic cannot close it.

### What the cable itself adds

`[calc]` 2 m of 24 AWG is 0.168 Ω per conductor, which is ADR 0003's own figure
`[repo hardware/controller/carrier.md:265-274]`. Against 11 kΩ of series
resistance that is 15 ppm — nothing differentially. `[from memory]` Cat5e pair
capacitance is of order 50 pF/m, so ~100 pF per 2 m conductor; against 11 kΩ that
is a 145 kHz pole, three decades above `C_diff`'s 482 Hz, so the cable does not
move the response. **The cable is not the problem at this boundary; the 1 MΩ
pair's tolerance is.**

### One thing the in-amp does present that nothing has costed

`[datasheet SBOS792A p.6]` INA828 closed-loop output impedance **1.3 Ω at
10 kHz**, load capacitance stability **1000 pF**, I_SC ±18 mA, settling 12 µs to
0.01 % on a 10 V step at G = 1–100. The in-amp drives `POT-GAIN`'s 50 kΩ track
plus `R-GAIN-FLOOR` = 57.15 kΩ `[repo hardware/module/breath-output-stage.md:118-119]`
and, if `POT-RESP` is adopted, R1's 20 kΩ as well `[repo hardware/module/breath-output-stage.md:190-210]`.
`[calc]` 10 V / 14.7 kΩ = 0.68 mA against ±18 mA. **Comfortable. Stop worrying** —
but note that `POT-RESP` inserts *two* more inverting stages between the in-amp
and the gain pot, and the in-amp's 12 µs settling is then in series with them;
at a 4 kHz loop that is still 20× of margin `[calc]`.

---

## Boundary 5 — the two panel wipers

### `POT-GAIN` must be buffered — confirmed

`[repo hardware/module/breath-output-stage.md:86-89]` claims it; the arithmetic
agrees, and the size of the error is worth recording because it is not a
rounding term.

```
[calc]  Wiper Thévenin of a pot spanned between two sources: R_th = p(1−p)·R_track.
        For a 50 kΩ track that peaks at 12.5 kΩ at mid-rotation.
        Driving R-IN = 10 kΩ into a virtual ground, an unbuffered wiper gives
        an extra divider 10 k/(10 k + R_th):
           mid-rotation: 10/22.5 = 0.444  →  −55.6 % of commanded gain
        and it vanishes at both end stops, so it is a rotation-dependent
        gain law, not a trimmable offset.
```

**Buffered, correctly, and the corpus's reason is the right one.**

### `POT-OFFSET` does *not* need buffering — and the corpus contradicts itself

The claim `[repo hardware/module/breath-output-stage.md:106-109]`: "This wiper
does **not** need buffering. Its source impedance varies from 0 at either end to
`R/4` at centre, so the endpoints are exact and the middle is slightly
non-linear in rotation. For an offset knob that is feel, not error."

**The endpoints are exact. The middle is not "slightly non-linear"; it is
0.53 V out, on a knob whose whole selling point is that zero is at centre.**

```
[calc]  Summing node at virtual ground. I_off = V_th/(R_OFF + R_th),
        I_neg = −12 V / 95.3 kΩ, V_jack = −R_FB (I_off + I_neg).
        R_OFF 21.0 k, R_OFFNEG 95.3 k, R_FB 40.0 k, rail 5.21 V, pot 10 kΩ linear.

        p       buffered      unbuffered     error
        0.000   +5.037 V      +5.037 V       0
        0.250   +2.556 V      +2.759 V       +0.203 V
        0.500   +0.075 V      +0.603 V       +0.528 V   ← "zero at centre"
        0.678   −1.674 V      −1.041 V       +0.634 V   ← peak
        1.000   −4.887 V      −4.887 V       0

        Unbuffered zero crossing:  p = 0.5669
        → 18.7° past centre on an RV09A (280° total rotation)
          20.1° past centre on an RV09B (300°)   [datasheet RV09AF-40 p.1]
```

**The table printed in the same document at `:96-100` — CCW +5.04 V, centre
+0.07 V, CW −4.89 V — is the buffered answer.** `bom.csv`'s `POT-OFFSET` row
prints the same three numbers *and* the sentence "Wiper does NOT need buffering"
in the same field `[repo bom.csv POT-OFFSET]`. The correct answer does appear in
the corpus, once: `breath-output-stage.md:287-290`, inside the `POT-RESP`
section, reports "~20° past centre at +0.605 V" and calls it a fix that "wants a
half" — 0.605 V against my 0.603 V, i.e. the same calculation.

**This is the project's named failure mode, on an impedance boundary.** The fix
landed in the §4 aside where the editing was happening; the Offset section and
the BOM row, which are where a builder looks, still carry the wrong claim beside
the right numbers. Nothing in `figures.yaml` tracks it, and no grep finds it
because both values are legitimate for *some* topology.

**What to change.** Three options, in ascending cost:

1. **Restate the numbers unbuffered and delete the "zero at centre" claim.**
   +5.04 / +0.60 / −4.89 V, zero at ~57 % rotation. Costs nothing, and the
   centre-detent idea `[repo hardware/module/breath-output-stage.md:170-173]`
   must go with it, because a detent 19° off the null is worse than no detent.
2. **Re-centre in resistors.** `[calc]` The error is
   `V_th·R_th/(R_OFF(R_OFF+R_th))·R_FB`; raising `R_OFF` from 21.0 kΩ to, say,
   100 kΩ shrinks it to +0.13 V at centre, at the price of rescaling `R_OFFNEG`
   and `R_FB` to keep ±5 V. One evening of algebra, no new part, and the
   endpoints stay exact. **This is the cheapest real fix and nobody has proposed it.**
3. **Buffer it** — which is what `:287-290` asks for, and which collides head-on
   with `POT-RESP` taking the last two OPA2197 halves
   `[repo hardware/module/breath-output-stage.md:255-258; bom.csv U-OPA-PITCH]`.
   A seventh package for one follower.

**Also, for SPICE:** `R-FB` is **40 kΩ** in the drawing at `:56` and **40.2 kΩ**
in the values table at `:123`. The offset table's numbers are the 40 kΩ ones
`[calc: at 40.2 kΩ they become +5.062 / +0.075 / −4.912 V]`. Pick one before
simulating.

**And a bound the pot datasheet does not give.** `[datasheet RV09AF-40 p.1]`
lists rotational angle, torque, life, insulation and dielectric — **and no total
resistance tolerance at all**. `[from memory]` this class of 9 mm carbon pot is
commonly ±20 %. At ±20 % on the 10 kΩ track the unbuffered centre error ranges
0.44–0.72 V `[calc]`, and `POT-GAIN`'s 0.125 floor against `R-GAIN-FLOOR`'s
7.15 kΩ 1 % ranges 0.107–0.152, i.e. the "0.5× floor" is really **0.43×–0.61×**
`[calc]`. Neither is fatal; both should be written down rather than discovered.

---

## Boundary 6 — six jacks into the outside world

### The load divider was fixed on pitch and on nothing else

| Output | Feedback taken at | `R-OUT-PROT` | Load divider |
|---|---|---|---|
| PITCH | **the jack** `[repo hardware/module/pitch-stage.md:150-166]` | inside the loop | **none, any load** |
| MOD 1–4 | the op-amp output `[repo hardware/module/mod-channels.md:20-38]` | outside | **full** |
| BREATH | the op-amp output `[repo hardware/module/breath-output-stage.md:56-62]` | outside | **full** |

```
[calc]  k = R_L/(R_L + 1 kΩ), error = 1 − k:
   100 kΩ  one Eurorack input      k 0.99010   −0.99 %    −99 mV on ±10 V
    50 kΩ  two, passive mult       k 0.98039   −1.96 %   −196 mV
    33 kΩ  three                   k 0.97085   −2.92 %   −292 mV
    25 kΩ  four                    k 0.96154   −3.85 %   −385 mV
    10 kΩ  one low-Z input         k 0.90909   −9.09 %   −909 mV
```

**`mod-channels.md`'s headline claim is an unloaded claim.** The page's whole
case for the two-resistor redraw is that it "lands on **exactly ±10.000 V**"
where the four-resistor version needed a 40.2 kΩ fudge to reach ±10.05 V
`[repo hardware/module/mod-channels.md:74-79]`. Into one 100 kΩ VCO input it
lands on **±9.901 V**, which is 99 mV *below* the number the four-resistor
version was criticised for missing by 50 mV. The tolerance table on the same
page — zero point ±50.5 mV, span 19.703–20.303 V `[repo hardware/module/mod-channels.md:120-124]` —
**does not contain the load term, and the load term is 2× to 8× larger than
everything the table does contain.**

The same page tells you where this bites: "anything pitch-like belongs on
channel 1" `[repo hardware/module/mod-channels.md:133-135]` — i.e. pitch, the
one output that is immune. So the *musical* cost is genuinely low: a modulation
CV 2 % short is a modulation CV. **The cost is to the documents**, and these
numbers are about to be simulated.

**What to change:** add one row to `mod-channels.md`'s tolerance table and one to
`breath-output-stage.md`'s values table stating the load divider, with the
±10.000 V and ±5 V figures marked *unloaded*. Do **not** move the mods to
jack-side feedback — pitch's own page shows what that costs in stability work
`[repo hardware/module/pitch-stage.md:206-230]`, and mods do not need it.

### ADR 0006 still argues against the change it later adopts

`docs/decisions/0006-cv-channel-allocation.md:507-582`, "The pitch output keeps
its 1 kΩ series resistor", is **live, unmarked text** that:

- prints −11.9 and −23.5 cents/octave as the pitch channel's tracking error;
- declines jack-side feedback as *"real stability work, on a board without one,
  to fix something a screwdriver already fixes"* `[:556-560]`;
- mandates a per-load affine `(gain, offset)` pair, a named preset per patch and
  a display line `[:547, :577]`;
- instructs the player to *"Use a buffered mult for pitch, not a passive one"* `[:572-575]`.

Every one of those is retracted 140 lines later in the same file: *"**Adopted.**
Pitch now closes its DC loop at the jack"* `[:691]`, *"The load-divider error is
gone, for any load"* `[:719]`, *"The per-load affine preset stops being
load-bearing"* `[:726]`. `pitch-stage.md:154-157` knows the earlier section is
there — it says ADR 0006 "paid for it with a per-load affine preset, a display
page, an operating instruction, and most of the gain trimmer's range" — and did
not go and mark it.

**The pointer is broken too.** Line 722 says the cents figures "**below** become
historical". They are 200 lines **above**. A reader who takes the instruction
literally looks below, finds nothing, and leaves the live text standing — which
is what happened.

**This is semantic, so `tools/check-staleness.py` cannot see it**, and it is
precisely the class `CLAUDE.md` §4 describes. Two documents disagree about
whether the pitch output has a load divider, and one of them is the ADR.

### Stability into what is actually plugged in

`pitch-stage.md:238-246` already carries the right warning: `Q = √(R_eff·C_load /
R2·C_fb)`, safe to about 10 nF, 44–67 % overshoot if PITCH is joined to the MOD
(82 nF) or BREATH (330 nF) jacks through a passive mult.

`[from memory]` a 3.5 mm patch lead is of order 100 pF/m, so a 0.5 m cable is
~50 pF and two multed VCOs are ~150 pF including input capacitance — **two
decades below the 10 nF bound**. Normal patching is nowhere near the limit. The
failure case is specifically **this module's own outputs joined to each other**,
which is a user error, not a load. **Verdict: fine in use; keep the E9 sweep
because it is the one output whose loop the patch cable enters.**

`[datasheet SBOS737C p.8]` I_SC ±65 mA; `[calc]` a shorted jack draws
11.5 V/1 kΩ = 11.5 mA and two outputs fighting at ±10 V through 2 × 1 kΩ draw
10 mA. **Current is not the issue; dissipation in `R-OUT-PROT` is, and
`bom.csv` has already raised that row to 0.66–1 W** `[repo bom.csv R-OUT-PROT]`.

`[datasheet PJ398SM drawing via bom.csv J-CV]` rated DC 30 V / 0.5 A. ±11.5 V at
11.5 mA is 2.6× inside the voltage rating and 43× inside the current rating.
**Stop worrying about the jacks.**

---

## Boundary 7 — MCU → 2 m Cat5 → level shifter → DAC

**First, the direction.** The 74AHCT125 is on the **module** side, after the
cable `[repo hardware/module/digital-and-supervision.md:24-46]`. The
transmission line is **MCU → cable → level shifter**; the level-shifter-to-DAC
hop is a short board trace. Any framing of this boundary as "level shifter →
2 m of Cat5 → DAC" has the topology backwards, and it matters because the line's
driver is a 3.3 V GPIO, not a 5 V buffer.

### The near-end series termination arithmetic reproduces

```
[calc]  V_far(first step) = 2 · 3.3 V · Z0/(Z0 + R_s),  open far end, R_s = 100 Ω + ~40 Ω pad
        Z0 = 100 Ω:  R_s 140 Ω → 2.750 V     ✓ matches carrier.md:471
                     R_s 260 Ω → 1.833 V     ✓ matches "1.83–1.86 V"
                     R_s 108 Ω → 3.173 V     ✓ matches "3.25 V" within the pad estimate
```

Against the 74AHCT125's **V_IH = 2 V min** `[datasheet SCLS264O p.3,
recommended operating conditions]` the 100 Ω choice clears by 0.75 V on the
first transit and 220 Ω does not. `carrier.md`'s §4 conclusion is sound.

### But Z0 = 100 Ω is true of exactly one of the three signals

The pin map is `1,2 BREATH/AGND | 3,6 +12V/PWR_GND | 4,5 SCLK/MOSI | 7,8
CS/DIG_GND` `[repo config/figures.yaml umbilical-pinmap]`. `[from memory]` T568B
pairs are (1,2), (3,6), (4,5), (7,8). So:

- **`CS` has its return, `DIG_GND`, twisted against it in pair (7,8).** For that
  line, and only that line, "2 m of Cat5 is a 100 Ω transmission line" is
  literally true.
- **`SCLK` and `MOSI` share pair (4,5) with each other and with no return at
  all.** Their return is `DIG_GND` on pin 8 — in a *different* pair. The
  characteristic impedance of a conductor in one pair referenced to a conductor
  in another is `[from memory]` of order 150–200 Ω, not 100 Ω, and the loop area
  is a pair-to-pair separation rather than a twist pitch.

`[calc]` At Z0 = 175 Ω with R_s = 140 Ω the first step is **3.67 V** — larger,
not smaller, so the V_IH margin *improves* and nothing breaks. The costs are
elsewhere and are real:

1. **Overshoot and ring.** Γ_source = (140 − 175)/(140 + 175) = −0.11, so the
   line is slightly over-terminated and rings mildly rather than stepping
   cleanly. Into an AHCT input with **no hysteresis** — which is exactly the
   property `carrier.md:479-481` identifies as what makes dwell dangerous — that
   is worth measuring.
2. **`SCLK` and `MOSI` return their current through the conductor twisted
   against `CS`.** Twisting cancels *differential* coupling between the two
   conductors of a pair; it does nothing about the fact that the two fastest,
   busiest signals in the loom are now developing their return voltage across
   the same conductor `CS` is referenced to. That is **common-impedance
   coupling**, and it is the one coupling mechanism the pin-map fix does not
   address. `digital-and-supervision.md:78-94` argues the swap improves
   `CS`'s margin "from about 1.9:1 to 6200:1"; that number is an *intra-pair*
   crosstalk number and does not cover this path.

**`CS` is the signal that must not glitch** — "A glitch restarts the bit count
mid-message … firmware can never read back what the DAC actually received"
`[repo hardware/module/digital-and-supervision.md:96-104]`. So the one signal
whose reference conductor carries two other signals' return current is the one
signal with no recovery path. The pin map is still the right pin map — there are
four pairs and five nets that want one — but **the argument for it is
incomplete, and the incompleteness is on the vulnerable line.**

**What to change.**

- **Measure Z0 of (4,5)-against-(7,8) with a TDR at E12** before trusting any
  reflection number for `SCLK`/`MOSI`. One measurement retires an estimate.
- **Consider splitting `R-SPI-SER`.** `[calc]` If Z0 is ~175 Ω, matching wants
  ~135 Ω of series on `SCLK`/`MOSI` (135 + 40 = 175) and 60 Ω on `CS`. Even the
  crude version — leave `CS` at 100 Ω, take `SCLK`/`MOSI` to 150 Ω — still gives
  a first step of 2.96 V at Z0 = 175 Ω, well over V_IH, while halving the
  reflection `[calc: 2 × 3.3 × 175/(175+190) = 3.16 V; Γ_s = +0.04]`. The BOM
  row is three identical 100 Ω parts today `[repo bom.csv R-SPI-SER]`; two
  values cost the same.
- **The 74AHCT14 already on the table would make all of this moot.**
  `digital-and-supervision.md:212-220` proposes it for edge cleanup and
  polarity inversion. Hysteresis on `CS` is the single cheapest answer to
  everything in this section.

### The level shifter → DAC hop is a non-boundary

`[datasheet SBAS430E p.4]` V_INH = **0.625 × AVDD** for 4.5 ≤ AVDD ≤ 5.5 V;
V_INL = 0.3 × AVDD; input current ±1 µA; **pin capacitance 3 pF**.
`[calc]` At AVDD = 5.21 V `[repo config/figures.yaml dac-rail]` that is
**V_IH = 3.256 V, V_IL = 1.563 V**.

`[datasheet SCLS264O p.4]` V_OH ≥ 4.4 V at I_OH = −50 µA, ≥ 3.8 V at −8 mA;
V_OL ≤ 0.44 V at 8 mA. Load is 3 pF plus a 10 kΩ `R-SPI-PULL`, i.e. under
600 µA, so **V_OH 4.4 V min against 3.256 V = 1.14 V of margin**. Fine.

> **And this is the number that justifies the part existing.** `[calc]` A direct
> 3.3 V drive would clear V_INH by **44 mV** — 3.300 − 3.256 — which is not a
> margin, it is a coincidence. If AVDD ever moves up (the LM317 spread is
> ±0.66 V worst case `[repo config/figures.yaml dac-rail]`, floor 5.00 V, so the
> top is ~5.5 V) the requirement becomes 3.44 V and a direct drive **fails**.
> The 74AHCT125 is load-bearing and no document says why in numbers.

**One back-power path, found here and worth one line.** The DAC-side
`R-SPI-PULL` on `CS` pulls to AVDD `[repo hardware/module/digital-and-supervision.md:40-46;
bom.csv R-SPI-PULL]`. The '125's *outputs* are clamped both ways — I_OK ±20 mA
for V_O > VCC `[repo bom.csv U-LVL-MOD, quoting SCLS264O abs-max]` — so with the
bus +5 V rail down and AVDD up, `[calc]` (5.21 − 0.7)/10 kΩ = **451 µA** flows
through that clamp into the dead rail. Small, and it argues (mildly) for the
"derive +5 V locally from the protected +12 V" proposal already open on that
page `[repo hardware/module/digital-and-supervision.md:106-118]`.

---

## Boundary 8 — the 3V3 loom

**The real load is 25.7 mA, and the BOM costed the fuse at 100 mA.**

```
[calc]  18 fitted switches × 1.43 mA = 25.74 mA   [repo hardware/controller/cluster-boards.md:208]
        21 networks (spares fitted too)          = 30.03 mA
        Marker straps draw nothing — copper to GND or 3V3, no resistor
                                                  [repo hardware/controller/cluster-boards.md:499]
        R-SER-TERM 10 kΩ                          = 0.33 mA
```

`[datasheet MF-PSMF010X p.1]` I_hold 0.10 A, I_trip 0.30 A, V_max 15 V,
**R_min 1.0 Ω, R1_max 7.5 Ω** at 23 °C, max time to trip 0.5 s at 1.5 A.
Thermal derating table: I_hold 0.09 A at 40 °C, 0.08 A at 50 °C, 0.07 A at 60 °C.

```
[calc]  Drop at 25.74 mA:
          R_min  1.0 Ω →  25.7 mV,  cluster VCC 3.274 V
          R1_max 7.5 Ω → 193.1 mV,  cluster VCC 3.107 V
          post-trip, ~2 × R1_max → 386 mV, cluster VCC 2.914 V   [from memory: PTC R rises after a trip]
        Loom itself (265 mm of 28 AWG ribbon, 5 parallel grounds, 8 IDC contacts at ~15 mΩ):
          0.0615 + 0.0123 + 0.12 ≈ 0.19 Ω → 5.0 mV
```

**`bom.csv`'s `F-CHAIN` row states "0.1 TO 0.75V OF DROP" and concludes "The
fuse would cause the fault it exists to prevent"** `[repo bom.csv F-CHAIN]`.
That is the drop at the fuse's *hold current*, not at the circuit's current. At
the real load it is **26–193 mV, overstated by 3.9×** `[calc: 0.75/0.193]`.

**And the drop is harmless even at R1_max, for a reason nobody has stated: the
rail is ratiometric to everything that runs off it.**

```
[calc]  74HC165 V_IH = 0.70 × VCC  [repo hardware/controller/cluster-boards.md:104, four datasheets]
        At VCC = 3.107 V:  V_IH = 2.175 V,  V_IL = 0.932 V
        The key pull-ups are on the SAME rail, so the release transient is
        V(t) = VCC(1 − e^{−t/τ}) crossing 0.70·VCC at t = τ·ln(1/0.30) = 1.204 τ
        — INDEPENDENT of VCC. The 119.9 µs figure does not move.
                                    [repo config/figures.yaml key-release-time]
        Marker straps tie inputs to the local rail or the local ground, so they
        are at VCC or 0 by construction.
        QH returns 3.107 V into an ESP32-S3 input (V_IH ≈ 0.75 × 3.3 = 2.475 V) — clears.
        74HC165 minimum VCC is 2.0 V; even the post-trip 2.914 V clears by 46 %.
```

**Verdict: the loom is fine, the fuse is fine, and the only thing wrong with the
boundary is the number in the BOM.** What genuinely is wrong:

- **The package.** `[datasheet MF-PSMF010X p.2]` 2.00–2.30 × 1.20–1.50 mm =
  **0805**. The BOM row says 1206 `[repo bom.csv F-CHAIN]`. Confirmed defect.
- **The trip point is well chosen and should not be "improved".** The obvious
  swap — MF-PSMF020X in the same family, R 0.65–3.5 Ω, half the drop
  `[datasheet MF-PSMF010X p.1, same table]` — raises I_trip to 0.50 A, which is
  **above** the dev board's ME6217C33M5G real capability (~250–500 mA
  `[repo config/figures.yaml matrix-led-current]`). The fuse would then not trip
  before the thing it protects folds back. **Keep the 010X.**
- **What the fuse does not cover.** It is in series with 3V3 only. The failure the
  row actually names — the 3V3 conductor shorting to the 12 V LED power it runs
  beside — back-feeds 12 V through 1.0–7.5 Ω into the register VCCs and the LDO
  output, and a PTC in that path does nothing about it. `[calc]` A polyfuse
  cannot protect against an overvoltage, only an overcurrent. If that specific
  failure is the justification, the part that covers it is a clamp, not a fuse.
  **Say which failure `F-CHAIN` is for.**

---

## Ranking

### Most expensive first

**1. Boundary 2 — reference buffer → sensor `VS`.** Everything else on this list
is an error budget line. This one is a stability question on an
**instrument-side, unretrofittable** node that *is* the breath scale factor, and
the circuit as drawn does not work: 8.4° of simulated phase margin in-loop
against 8.8° with no resistor at all `[repo config/figures.yaml riso-ref-topology]`,
now known to be against a 375 Ω Z_O rather than the back-solved 75.8 Ω. It is
blocked on a *drawing* question (`cref-out-node`) that costs one afternoon and
one sentence. **TI has published the answer for this exact circuit and it is
the in-loop topology with a second AC path — not a third option.** Settle the
node, adopt Figure 56, recalculate for 100 nF. Nothing else on this page should
be worked on first.

**2. Boundary 5b — `POT-OFFSET`.** 0.53 V at the detent on a ±5 V knob, and the
corpus states the right answer in one place and the wrong one in two, including
the BOM row a builder reads. Cheapest real fix is re-scaling `R-OFF` (option 2
above), which nobody has proposed because everyone framed it as "buffer or not".

**3. Boundary 6 — the five unbudgeted output dividers, and ADR 0006's live
retracted section.** The musical cost is small; the documentary cost is large,
and one of the two documents that disagree about whether the pitch output has a
load divider is the ADR. These numbers feed SPICE next week.

**4. Boundary 4 — CMRR margin.** 66 dB at the top of the signal band, not 73 dB;
7.5 dB of margin, not 14.7 dB. Fixable for free by specifying `R-BIAS-INAMP` at
0.1 % instead of 1 % — 20 dB for two 0805s on a board that gets bonded shut.

**5. Boundary 3 — the ADC's source impedance.** Correct answer, wrong derivation:
the 1 kΩ R_SS is a 5.5 V figure and at 3.3 V the bare divider would be out of
bounds. `C-AA-ADC` rescues it and no document says it is doing so.

**6. Boundary 7 — the SPI line model.** Passes on margin, but "100 Ω
transmission line" is true of `CS` alone, and the cost of that falls on `CS`.
One TDR measurement and, possibly, a second value in one BOM row.

### Already fine — stop worrying about these

**Boundary 1 (DAC → op-amp).** 4 Ω into 1 kΩ. The bias-current term is
0.012 cents at the over-temperature maximum, four orders below the budget. The
only entry it earns is a 40 ppm trimmable gain line from `R-BIAS-DAC`, and a
settling figure the latency budget should carry. **The corpus is right about
this boundary and can stop re-litigating it.**

**Boundary 4b (INA828 `REF`).** 18 mΩ against a 5 Ω requirement. 270×. The part
is buffered, the buffer is the right part, and the only remaining obligation is
a layout rule. Three documents currently repeat the "source impedance on `REF`
degrades CMRR one-for-one" warning to each other
`[repo hardware/module/breath-receive-stage.md:151-160 and :162-166; bom.csv U-DIFFRX;
bom.csv TRIM-BREATH-ZERO]`. It is handled. **Close it.**

**Boundary 5a (`POT-GAIN`).** Buffered, correctly, for the right reason.
Verified.

**Boundary 6b (pitch into any load).** Zero error open-circuit to 2 kΩ. The
remaining risk is a patching error, not a load.

**Boundary 7b (level shifter → DAC).** 1.14 V of margin on a board trace.

**Boundary 8 (3V3 loom).** 5 mV of loom and a fuse whose worst case is 193 mV on
a rail whose thresholds move with it. The BOM's objection is 3.9× overstated and
should be withdrawn rather than acted on.

---

## What SPICE needs to be told, and what it must not be allowed to assume

The stage after this one will produce confident numbers. These are the inputs
that are currently ambiguous in the corpus; each one changes a result by more
than the thing being measured.

| Quantity | The ambiguity | Use this |
|---|---|---|
| OPA2197 `Zo` | 375 Ω specified vs 75.8 Ω back-solved | **375 Ω**, with Figure 26's shape: 3.26 kΩ at 0.1 Hz, 482 Ω at 10 Hz, 375 Ω plateau 100 Hz–300 kHz, 301 Ω at 1 MHz, 73 Ω at 10 MHz `[datasheet SBOS737C p.8, p.10, Fig 26]` |
| `C-REF-OUT` node | REF5050 output vs buffer output — three files disagree | **Unresolved. Run both.** `[repo config/figures.yaml cref-out-node]` |
| Sensor `VS` load | 100 nF fitted vs 1.0 µF in the datasheet's Figure 3 | **100 nF**, and record that the datasheet asks for 1 µF |
| Sensor `I_S` | 10 mA max, **no typ, no min** | **Sweep 0–10 mA.** A single value hides the whole problem |
| ADC divider node | Buffer output (`carrier.md`) vs sensor output (`breath-receive-stage.md`) | **Buffer output** |
| MCP3202 `R_SS` | 1 kΩ is a **5.5 V** figure | **~3 kΩ at 3.3 V** `[calc from Fig 4-2]`, and model the 47 nF explicitly |
| `R-FB` (breath summer) | 40 kΩ in the drawing, 40.2 kΩ in the table | Pick one; the published offset table used **40 kΩ** |
| `POT-OFFSET` wiper | Buffered in the tables, unbuffered in the text | **Unbuffered**, `R_th = p(1−p)·10 kΩ` |
| Pitch jack node | `C-FILT-PITCH` 10 nF present (`pitch-stage.md`, ADR 0006:693) vs "carries no capacitor at all" (ADR 0006:742-746) | **10 nF present** — `C-FB-PITCH` was raised 1 nF → 2.2 nF *because* it came back |
| Mod/breath output load | Tables are unloaded | **Sweep 100 k / 50 k / 25 k / 10 k** |
| Umbilical `Z0` | 100 Ω assumed for all three SPI lines | **100 Ω for `CS` only.** Measure (4,5)-vs-(7,8) |

---

## Findings index — by node

| # | Node / refdes | Finding | Class |
|---|---|---|---|
| A10-1 | `POT-OFFSET` wiper | Unbuffered wiper puts "zero at centre" +0.53 V and 19° off centre; the document and the BOM row both print the buffered numbers beside the claim that no buffer is needed | **Defect — contradiction** |
| A10-2 | pitch jack / ADR 0006 §"keeps its 1 kΩ" | 75 lines of live, unmarked text arguing against the jack-side feedback the same ADR adopts 140 lines later; the retraction's own pointer says "below" and means "above" | **Defect — semantic staleness** |
| A10-3 | MOD 1–4 jack, BREATH jack | Load divider (−0.99 % to −3.85 %, up to −385 mV) absent from both tolerance tables; `mod-channels.md`'s "exactly ±10.000 V" is an unloaded figure | **Defect — omission** |
| A10-4 | ADC divider node | `carrier.md` and `breath-receive-stage.md` hang the 0.6× divider on different sides of the breath buffer | **Defect — topology disagreement** |
| A10-5 | MCP3202 CH0 | `R_SS` = 1 kΩ is a 5.5 V figure; at 3.3 V a bare 6 kΩ source at 900 kHz is out of bounds against Fig 4-2. `C-AA-ADC` is what makes it legal and nothing says so | **Defect — derivation** |
| A10-6 | `R-BIAS-INAMP` | 1 % tolerance is the entire dc CMRR floor (73 dB); 0.1 % gives 93 dB for two 0805s on an unretrofittable board | **Improvement — free** |
| A10-7 | `C_cm` / INA828 inputs | CMRR floor is 66 dB at 482 Hz, not the 73 dB dc figure; margin over the 58.5 dB requirement is 7.5 dB, not 14.7 dB | **Correction** |
| A10-8 | `R-ISO-REF` / sensor `VS` | Out-of-loop isolation costs 7.5 % at TI's 37.4 Ω, not the 2 % the corpus quotes at 10 Ω; and SBOS737C Figure 56 is the *in-loop* option made stable, not a fourth choice | **Correction — unblocks a dispute** |
| A10-9 | `R-BIAS-DAC` | 4 Ω DAC output impedance into 100 kΩ = 40 ppm gain = 0.10–0.34 cents, absent from the pitch error table | **Omission — trimmable** |
| A10-10 | `J-UMB` pins 4,5 | `SCLK`/`MOSI` have no return conductor in their own pair, so the 100 Ω line model applies to `CS` alone, and their return current flows in `CS`'s reference conductor | **Defect — model** |
| A10-11 | `F-CHAIN` | Drop costed at the fuse's hold current (100 mA), not the circuit's 25.7 mA — overstated 3.9×; the rail is ratiometric so even 193 mV is harmless; package is 0805 not 1206; and a PTC does not cover the 12 V short the row names | **Correction — withdraw the objection** |
| A10-12 | `R-FB` (breath summer) | 40 kΩ in the drawing, 40.2 kΩ in the values table | **Defect — minor** |
| A10-13 | pitch jack node | ADR 0006 says both "`C-FILT-PITCH` (10 nF) stays at the jack" (:693) and "that node … carries no capacitor at all" (:742-746), ~50 lines apart | **Defect — contradiction** |
| A10-14 | MCP3202 CH1 | Spare mux input left floating | **Improvement — minor** |
| A10-15 | `C-DECOUPLE-CARRIER` at `U-BREATH` | 100 nF fitted against the sensor datasheet's recommended 1.0 µF on `V_s`; every compensation number on that node depends on which | **Omission — record the decision** |
| A10-16 | `R1b` / `breath-receive-stage.md:215` | Still says `R1b` buys "fifty times"; `carrier.md:150-157` corrects it to 13 dB and the arithmetic agrees with `carrier.md` | **Defect — uncorrected** |

---

## Where I could be wrong

Per `CLAUDE.md`, findings are claims. The ones most worth checking before acting:

- **A10-5's ~3 kΩ R_SS at 3.3 V** is an extrapolation from a curve I digitised
  by rendering Figure 4-2 at 900 dpi and reading against log gridlines. The
  bracketing values (≈1.1 kΩ at 5 V back-solved, against a spec'd 1 kΩ) give me
  confidence in the method, but the 3.3 V number is a fit, not a datum. **The
  conclusion does not depend on it**: with `C-AA-ADC` fitted, R_SS could be
  10 kΩ and the boundary would still settle in 83 τ.
- **A10-10's 150–200 Ω pair-to-pair Z0** is `[from memory]`, not measured and not
  from any banked document. The *structural* claim — that `SCLK` and `MOSI` have
  no return in their own pair — is read directly off the pin map and is not in
  doubt. The number is.
- **A10-11 contradicts a conclusion already recorded in `bom.csv`.** Per
  `CLAUDE.md`, a finding filed as handled is more dangerous than one filed
  wrong, so this one cuts the risky way: I am saying a *fix* was wrong. The
  arithmetic is one multiplication (7.5 Ω × 25.7 mA) and the load figure is the
  corpus's own `[repo hardware/controller/cluster-boards.md:208]`. Check it
  before withdrawing anything.
- **A10-7's 2 kHz case (53.7 dB, requirement not met)** is a single-term
  calculation that ignores `C_diff`'s attenuation of the converted signal. It is
  flagged for SPICE rather than filed as a defect, deliberately.
- **The 58.5 dB CMRR requirement** is cited from `carrier.md:155`, which
  attributes it to a prior review's calculation. I did not read that review and
  have not re-derived it. Every margin statement in Boundary 4 inherits its
  uncertainty.
