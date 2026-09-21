# A5 — Module breath chain, receive stage to jack

**Reviewer:** cold. Read only `hardware/module/breath-receive-stage.md`,
`hardware/module/breath-output-stage.md`, `hardware/bom.csv`,
`hardware/controller/carrier.md`, `hardware/module/power-entry.md`,
`hardware/module/digital-and-supervision.md`, ADRs 0003 / 0004 / 0006.
**Did not open `docs/review/**` or `docs/research/**`.**

**Network:** every vendor host was refused by the proxy (403 on
`www.ti.com`, `www.mouser.com`, `datasheet.lcsc.com`; the proxy's own
`recentRelayFailures` list shows the same for other hosts). Every device
parameter below is therefore `[from memory]` and flagged as such. Nothing in
this report *depends* on an unverified datasheet number except where it says so.

Indexed by node / BOM reference. Arithmetic inline. Constants used:
4kT at 300 K = 1.656e-20 V²/(Ω·Hz); noise bandwidth of a single pole = π/2 × f_c.

---

## 0. The numbers I get, before the findings

Recomputed from scratch from the drawn values, so that everything below has a
common baseline.

**In-amp gain** `[calc]`, `[repo] bom.csv R-GAIN-INAMP`, `[from memory]` INA828
uses a 50 kΩ internal gain network:
```
G  = 1 + 50k/42.2k = 1 + 1.18483 = 2.18483
```

**Input divider**, both legs identical (R1 1k + cable + R2/R3 10k = 11.0 kΩ,
against R4/R5 1 MΩ to module AGND) `[calc]`:
```
1M / 1.011M = 0.989120
G_eff = 2.18483 × 0.989120 = 2.16106
```

**Endpoints at the in-amp output**, `Vout = -G_eff·(V_BREATH - V_AGND) + V_REF`,
with `V_REF` trimmed to null the pedestal, i.e. `V_REF = G_eff × 0.200 = 0.4322 V`
`[calc]`:

| Sensor | P | V_sensor | In-amp out |
|---|---|---|---|
| Rest | 0 kPa | 0.200 V | **0.000 V** (by construction) |
| "hard blow" as the pages define it | 2.8 kPa | 2.345 V | **−4.638 V** |
| Sensor full scale | 6 kPa | 4.800 V | **−9.941 V** |

**Downstream** `[calc]`, using the *table* values (R-FB 40.2 k, R-IN 10 k,
POT-GAIN 50 k, R-GAIN-FLOOR 7.15 k) `[repo] breath-output-stage.md`,
`[repo] bom.csv R-BREATH-SUM`:
```
fixed stage      = 40.2k/10k = 4.020  (inverting)
attenuation      = 7.15/57.15 = 0.12512  …  1.000
gain at the jack = 0.5030 … 4.020
gain(x) = 4.020 × (7.15 + 50x)/57.15 = 0.5030 + 3.5170·x     (x = rotation, 0…1)
```
Gain is **linear in rotation**, not logarithmic. Keep that: it matters in §8.

**Offset at the jack** `[calc]`:
```
from -12V : -(40.2/95.3) × (-12)   = +5.0619 V   (fixed)
from wiper: -(40.2/21.0) × V_w     = -1.91429·V_w
```

---

## 1. `IN+` / `IN−` / cable — common-mode behaviour actually achieved

The stated budget is 60 dB. **Nowhere in the repo is 60 dB derived**, and the
threat it is sized against is quantified elsewhere as 59 mV of PWR_GND IR drop
`[repo] 0003` — which at 60 dB is 59 µV differential, 128 µV at the jack,
13 ppm of 10 V. So the budget is ~30 dB tighter than the only CM source the
project has costed. I still evaluated against 60 dB, because there is a second,
uncosted CM source: mains-frequency and rack-frequency common mode on a 2 m
unshielded run, which can be hundreds of mV to volts.

### 1.1 Term-by-term stack (my own, at 60 Hz and at the 459 Hz band edge)

**(a) INA828's own CMRR.** `[from memory]` ~100 dB min at G = 1 DC, rising with
gain, with the vs-frequency curve flat to a few hundred Hz at low gain. At
G = 2.185 and ≤500 Hz this is **not the limiting term** and I did not model it
further. Unverified — ti.com refused.

**(b) Series-resistance imbalance, R1/R1b/R2/R3 against R4/R5** `[calc]`.
With R1b fitted, R2/R3 at 0.1 % and R1/R1b at 1 %, the worst leg-to-leg
difference is 10 Ω + 10 Ω = 20 Ω on 11 kΩ:
```
Δ(divider)/divider = ΔR/(Rp+Rs) = 20 / 1.011e6 = 1.98e-5  →  94.1 dB
```

**(c) R4/R5 tolerance — the term neither page analyses, and the dominant
resistive one** `[calc]`. `R-BIAS-INAMP` is **1 MΩ 1 %** `[repo] bom.csv`, so
worst-case leg-to-leg is 2 %:
```
Δ(divider)/divider = Rs/(Rp+Rs) × ΔRp/Rp = (11k/1.011M) × 0.02
                   = 0.010880 × 0.02 = 2.176e-4   →  73.2 dB
```
**73 dB, not 94.** The 0.1 % module-side parts do not buy 94 dB; the 1 % bias
pair throws it back. Substituting 5 % 1 MΩ parts — which a builder would think
harmless for a "bias return" — drops this to 59.2 dB and blows the budget on its
own `[calc]`: `(0.010880 × 0.10) = 1.088e-3 → 59.3 dB`.

**(d) C_cm mismatch.** Deriving it rather than quoting it. With sources at
V_cm through R per leg, C_A/C_B to ground and C_d across:
```
Vd = -jω·δ·Vavg / ( 1/R + jω(C + 2C_d) ),   δ = C_A - C_B
below the differential pole:  |Vd/Vcm| ≈ ω·R·δ
```
At ±1 % on 1.5 nF, δ_max = 30 pF, R = 11 kΩ `[calc]`:
```
60 Hz : 377 × 11e3 × 30e-12 = 1.244e-4  →  78.1 dB
459 Hz: 2884 × 11e3 × 30e-12 = 9.52e-4  →  60.4 dB
```
At ±5 %, δ_max = 150 pF: **64.1 dB at 60 Hz, 46.4 dB at the band edge** —
which is where the page's "~46 dB" comes from. The page's ±1 % conclusion is
**correct**. Its *reasoning* is not — see finding **F-CM-2**.

**(e) Source-impedance imbalance at the instrument end.** BREATH is driven by an
OPA2197 follower; closed-loop Zout at 500 Hz ≈ `100 Ω / (10 MHz/500 Hz)` ≈ 5 mΩ
`[calc]`, `[from memory]` for OPA2197 GBW and open-loop Ro. Negligible against
R1. Good.

### 1.2 Result

`[calc]`, worst-case (arithmetic, not RSS) of (b)+(c)+(d):
```
60 Hz  : 1.98e-5 + 2.176e-4 + 1.244e-4 = 3.62e-4   →  68.8 dB
459 Hz : 1.98e-5 + 2.176e-4 + 9.52e-4  = 1.190e-3  →  58.5 dB
```
**The design achieves roughly 69 dB at mains frequency and 58 dB at its own band
edge** — i.e. it misses its stated 60 dB budget at the top of the band, and the
term responsible is the one nobody wrote down (the 1 MΩ pair), not the one both
pages argue about (R1/R1b).

Referred to signal: 1 V of 50 Hz common mode on the cable gives
`1 V × 3.62e-4 × 2.161 = 0.78 mV` at the jack `[calc]` — about −82 dB of a 10 V
span, inaudible through a VCA. The link works. The *accounting* is wrong.

---

## 2. `R1b` (`R-SER-BREATH-INST`, qty 2) — **it is not in the instrument schematic**

**Showstopper-adjacent; ranked High because it is unretrofittable and layout is
imminent.**

- `[repo] bom.csv R-SER-BREATH-INST`: qty **2**, "R1 in the BREATH leg, R1b its
  twin in the AGND leg … Both are instrument-side and UNRETROFITTABLE".
- `[repo] hardware/module/breath-receive-stage.md` draws R1b and calls it "One
  resistor, instrument-side, and therefore **unretrofittable**".
- `[repo] hardware/controller/carrier.md` §2 — the page that will be laid out,
  and which says of itself "layout is now" — draws
  `J-UMB pin 2 AGND ──┴── analog star point ──[single tie]── PWR_GND`.
  **There is no R1b in it.** The only series part in §2 is
  `R-SER-BREATH-INST 1k` in the BREATH leg, singular.

Three documents say two resistors; the drawing that becomes copper says one. The
part is inside a bonded body `[repo] 0009`.

**Two caveats, because the justification as written is overstated:**

1. The page's own CMRR case for R1b — "60.2 dB, the entire budget, spent by one
   unmatched resistor" — checks out arithmetically `[calc]`
   (`|1M/1.011M − 1M/1.010M| = 9.79e-4 → 60.2 dB`) but is ~13 dB, not "fifty
   times", because §1.1(c) shows the real floor with R1b fitted is 73 dB, not
   94 dB. Against the project's own 59 mV CM figure the difference is
   125 µV vs 28 µV at the jack `[calc]`.
2. R1b's *better* justification is not given anywhere: it balances the
   **source-end** impedance of the twisted pair (1 kΩ vs ~0 Ω), which is what
   converts capacitively-coupled E-field pickup on 2 m of unshielded Cat5 into
   a differential signal. That mechanism is independent of the 1 MΩ pair and is
   the one that actually scales with a hostile environment.

**Action:** place the pad. It is free, it helps for two reasons, and it cannot
be added after M7.

---

## 3. `REF` pin drive — **this one is right**, with two gaps

**Is REF driven from a low impedance across the trim's range? Yes.**
`[repo] breath-receive-stage.md`, `[repo] bom.csv TRIM-BREATH-ZERO`: the wiper
of a 10 k cermet goes into half an OPA2197 configured as a follower, and the
follower's output drives REF. Source impedance at REF is therefore the op-amp's
closed-loop output impedance — **milliohms at DC, rising to perhaps 0.1 Ω at
500 Hz** `[calc]` from GBW/Ro as in §1.1(e) — **at every trimmer position**,
including the 2.5 kΩ worst case at mid-rotation, which the buffer absorbs.
Against the INA828's internal network (`[from memory]` ~50 kΩ at REF) that is
7 orders of margin. The CMRR-degradation hazard both pages warn about is closed.

REF current is trivial `[calc]`: `(V_REF − V_out)/50k`, ≤ 0.2 mA across the whole
output swing, well inside the OPA2197's drive.

**Gap 3a — the trim range has no parts (`R-TRIM-RANGE` is status `open`).**
`[repo] bom.csv`: "Values with the stages at E10". The range is fully determined
now, so here it is `[calc]`: put the 10 k track between a top resistor and
ground, fed from 5.21 V, and choose the top resistor for a 1.0 V ceiling:
```
R_top = 10k × (5.21/1.0 − 1) = 42.1 kΩ   →  E96 42.2 k gives 5.21 × 10/52.2 = 0.998 V
```
A 10-turn trimmer then resolves 100 mV/turn; the 0.437 V target is a hair under
4.4 turns and 1 mV is 0.01 turn. Practical.

**Gap 3b — nothing filters the trimmer.** There is no capacitor at the wiper and
none at the INA828 REF pin. REF is additive at **unity** into the in-amp, then
multiplied by 0.50–4.02 downstream, so everything on the LM317 rail lands at the
jack at `0.0839 × (0.50…4.02)` = 0.042–0.337 `[calc]`, and the LM317's own noise
is `~50 µV RMS` over 10 Hz–10 kHz `[repo] bom.csv C-REG-ADJ`. See §7; a 100 nF
from wiper to AGND (≈640 Hz against the 2.5 kΩ Thévenin) removes it for two
cents `[calc]`.

---

## 4. `R4` / `R5` (`R-BIAS-INAMP`) — bias return, and where the jack actually sits

**Where does each bias current return?**

| State | IN+ return | IN− return | In-amp out | Jack (gain 2.13×, offset 0) |
|---|---|---|---|---|
| Cable in, instrument up | R2+R1b → instrument star | R3+R1 → buffer output | 0 V at rest | 0 V ✓ |
| **Cable unplugged** | R4 → module AGND | R5 → module AGND | **+V_REF** | **−0.93 V** |
| **BREATH conductor open** | R2+R1b → star | R5 → module AGND | **+V_REF** | **−0.93 V** |
| **AGND conductor open** | R4 → module AGND | R3+R1 → buffer | 0 V ± ground shift | 0 V ± 0.27 V, moving |
| Instrument unpowered, cable in | R4 | R5 + buffer ESD structures | ≈ **+V_REF** | ≈ **−0.93 V** |

`[calc]` for the unplugged/open cases: with both inputs tied to module AGND
through 1 MΩ, `V_diff ≈ I_OS × 1 MΩ` (microvolts to a millivolt), so
`V_out ≈ V_REF = 0.432 V`. The downstream stage inverts:
```
0.432 V × 2.13 = 0.92 V, negative at the jack
at POT-GAIN full CW: 0.432 × 4.02 = 1.74 V negative
plus whatever the OFFSET knob is set to
```

### F-BIAS-1 — "the breath jack goes to 0 V" is false, in three documents

- `[repo] 0003`: "so the breath jack goes to a rail rather than to the 0 V
  ADR 0005 promises" — implying R4/R5 restore the 0 V.
- `[repo] 0006` power-on table: "| **Breath** | 0 V | The receiver's
  **differential pulldown** holds it there (ADR 0003) |". The differential
  pulldown was **deleted** `[repo] breath-receive-stage.md`, so this row cites a
  part that no longer exists *and* gets the answer wrong.
- `[repo] breath-receive-stage.md` R4/R5 row: "Without these the in-amp's inputs
  float … and it saturates to a rail" — true, but it never states where it lands
  *with* them.

**It lands at −0.93 V to −1.76 V.** The sign is the safe one (below rest, so a
VCA stays shut), and I would not change the circuit for it — but it is a
documented promise the hardware does not keep, and it is also the **rest state
during every power-up**, because the module powers the instrument: the LM317 and
the REF trim are alive the instant +12 V is, while the sensor's REF5050 and buck
are still coming up. So at every switch-on the jack sits ~1 V *below* the
player's parked offset and then walks up. Into a bipolar modulation input that
is a thump. **Medium.**

If 0 V matters, the fix is a JFET/analog switch or a comparator muting the
summer — but that reintroduces the presence-detect the project deliberately
deleted `[repo] digital-and-supervision.md`. My recommendation is to **correct
the three documents**, not the circuit.

### F-BIAS-2 — broken AGND is the graceful failure, and it is undetectable

`[calc]`: with AGND open, IN+ sits at module AGND instead of instrument ground,
so the error is exactly the PWR_GND IR drop the whole scheme exists to remove:
`59 mV × 2.161 = 128 mV` at the in-amp, `× 2.13 = 272 mV` at the jack, moving
with display brightness and LED animation `[repo] 0003`. The instrument still
plays. Nothing reports it. Worth one line in the E-milestone test list: unplug
AGND and confirm the jack picks up the light show. **Note.**

### F-BIAS-3 — I_OS through 1 MΩ is a real DC term

`[from memory]` INA828 I_OS is a fraction of a nA. At 0.5 nA:
`0.5 nA × 1 MΩ = 0.5 mV` differential → `× 2.161 × 2.13 = 2.3 mV` at the jack
`[calc]`, i.e. 230 ppm of span, and it drifts. Trimmed out at commissioning by
TRIM-BREATH-ZERO along with everything else, so harmless — but it means the
trimmer is nulling I_OS·1MΩ + pedestal + PWR_GND drop, and the "0 → +1.0 V
covers 0.152–0.378 V of pedestal" range calculation has not budgeted for the
other two. Headroom is ample (0.826 V of 1.0 V used at worst case), so this is a
**Note**, not a problem.

---

## 5. `C_diff` / `C_cm` — the 482 Hz corner, and the RF claim

### F-CM-1 — the corner is 459 Hz, not 482 Hz `[calc]`

The two C_cm sit in series across the differential path (0.75 nF) in parallel
with C_diff:
```
C_diff,total = 15 nF + 1.5n/2 = 15.75 nF
f_diff = 1/(2π × 22 kΩ × 15.75 nF) = 459.3 Hz     (page says 482 Hz)
f_cm   = 1/(2π × 11 kΩ × 1.5 nF)  = 9646 Hz
```
4.8 % low. Immaterial musically; it matters only because the page makes a point
of the number ("**482 Hz** … not 531"). **Note.**

### F-CM-2 — "C_diff ten times C_cm divides the mismatch" is wrong in the band

`[repo] breath-receive-stage.md` §"Why C_diff is ten times C_cm": "Making the
differential capacitor dominant means a mismatch between the two common-mode
capacitors is divided by the ratio before it reaches the difference signal."

From the derivation in §1.1(d), **below the differential pole the CM→DM
conversion is `ω·R·δ` and C_diff does not appear in it at all.** C_diff only
enters above the pole, where the denominator `1/R + jω(C + 2C_d)` becomes
reactive. So across 0–459 Hz — the entire signal band — raising C_diff buys
nothing against C_cm mismatch.

Why this matters: it is exactly the kind of statement that gets acted on. If a
bench measurement at E10 shows hum on the breath jack, "make C_diff bigger" is
the move this paragraph licenses, and it will not work. The correct levers are
(i) C_cm tolerance, (ii) *deleting* C_cm and letting C_diff plus the in-amp's
own EMI filtering do the job, (iii) matching the legs. **Medium.**

The page's actual conclusion — **specify ±1 % C0G on the two 1.5 nF parts** — is
right, and `[repo] bom.csv C-FILT-BREATH` still does **not** carry that
tolerance. That row reads `15nF C0G (diff) + 1.5nF C0G (cm x2)` with no
tolerance field. **Medium — unapplied.**

### F-CM-3 — the RF-rectification claim is not supported by these parts

Both pages justify filter placement with "a filter after the amplifier cannot
prevent RF rectification … there is a 2.4 GHz radio two metres away on the same
cable bundle" `[repo] breath-receive-stage.md`, `[repo] bom.csv C-FILT-BREATH`.
The *placement* argument is correct. The *efficacy* claim is not, because at
2.4 GHz neither element is what the schematic says it is `[from memory]` for the
parasitics, `[calc]` for the consequence:
```
0805 10 kΩ thin film: ~0.05–0.1 pF shunt →  Z at 2.4 GHz = 1/(2π·2.4e9·0.08p) ≈ 830 Ω
0805 1.5 nF C0G:      past SRF, ESL ~0.8 nH → Z at 2.4 GHz = 2π·2.4e9·0.8n   ≈ 12 Ω
attenuation = 12/(830+12) = 1/70  →  ~37 dB, not the >60 dB the 482 Hz pole implies
```
And that assumes an ideal ground return for C_cm at 2.4 GHz, which a 0805 pad
and a via do not give.

Real 2.4 GHz protection here is one of: a ferrite bead or small series R in each
leg **at the connector pin**, a 10–47 pF C0G right at the pin with a via to the
same ground plane the INA828 sits on, or the INA828's own integrated EMI filter
if it has one. `[from memory]`: TI's INA818/INA819 advertise integrated EMI
filtering with ~100 dB EMIRR; **whether INA828 does is exactly what I could not
check** (ti.com refused). If it does, the job is done by the chip and the
documents credit the wrong part; if it does not, there is no 2.4 GHz protection
at the module end. **Medium, with the confidence gated on one datasheet page.**

Note that the same filter is *excellent* against the in-band and switching-rate
threats `[calc]`, using the general expression with δ = 30 pF at 330 kHz (the
instrument's buck rate `[repo] carrier.md`):
```
|Vd/Vs| = [ω·δ/(ω(C+2C_d))] × 1/(1+jωRC) = 9.52e-4 / 34.2 = 2.78e-5  → 91 dB
```
So switching ripple is a non-problem. The gap is specifically GHz.

---

## 6. `D-CLAMP-BREATH` — the drawing and the BOM put it in different places

- `[repo] breath-receive-stage.md` draws `BAV99 to ±12 V, both legs` on the
  connector side of the branch, i.e. **ahead of R2/R3**.
- `[repo] bom.csv D-CLAMP-BREATH`: "Silicon, to ±12 V, **behind the 10k series
  resistors**."

These are different circuits. Ahead of R2/R3, the only thing limiting fault
current into the BAV99 is the *instrument-side* 1 kΩ — useless against a fault
injected at the module connector, where the diode sees the source directly
(BAV99 is `[from memory]` 200 mA continuous). Behind R2/R3, the 10 kΩ limits any
sustained fault to ~1.2 mA at ±12 V `[calc]` but the diode no longer protects the
connector pin from ESD, which is what `D-TVS-BREATH` covers at the *instrument*
end only — there is no TVS at the module end at all `[repo] bom.csv`.

The correct answer is both roles: BAV99 **behind** R2/R3 (protects the INA828,
current-limited by 10 kΩ) and, if module-end ESD matters — a panel-adjacent
etherCON that a user handles `[repo] 0004` — a second clamp or TVS at the pin.
**Medium**, and it is a layout-blocking decision.

---

## 7. `POT-OFFSET` / `R-OFF` / `R-OFFNEG` — the offset network

### F-OFF-1 (High) — the unbuffered wiper puts "zero at centre" at **+0.61 V**

`[repo] breath-output-stage.md`: "**This wiper does not need buffering.** Its
source impedance varies from 0 at either end to `R/4` at centre, so the endpoints
are exact and the middle is slightly non-linear in rotation. For an offset knob
that is feel, not error." `[repo] bom.csv POT-OFFSET` repeats it.

The centre is precisely the position the design has made meaningful, and the
page is considering a centre detent for it. Work it out `[calc]`. Thévenin of a
10 k linear pot at fraction k: `V_th = 5.21k`, `R_th = 10k·k(1−k)`. The wiper's
leg is then `R-OFF + R_th`:
```
V_offset(k) = 5.0619 − 40.2k × 5.21k / (21.0k + 10k·k(1−k))
```
| k | R_th | V_offset |
|---|---|---|
| 0.00 | 0 | **+5.062 V** |
| 0.25 | 1.875 kΩ | +2.773 V |
| **0.50** | **2.500 kΩ** | **+0.605 V** |
| 0.75 | 1.875 kΩ | −1.805 V |
| 1.00 | 0 | **−4.911 V** |

Zero crossing, solving `50.619k² + 158.82k − 106.30 = 0` `[calc]`:
```
k = (−158.82 + √(158.82² + 4·50.619·106.30)) / (2·50.619)
  = (−158.82 + √46747) / 101.24 = 57.39/101.24 = 0.567
```
**Zero sits at 56.7 % of rotation — about 20° past centre on a 300° pot.** The
published table (+5.04 / +0.07 / −4.89) is the *unloaded* divider; loading moves
the centre by **+0.53 V, eight times the value stated**, and 6 % of the ±5 V
span. A centre-detent pot would therefore detent at +0.6 V, which is worse than
no detent at all because it is confidently wrong.

Fixes, cheapest first:
- **Buffer the wiper.** `[repo] bom.csv U-OPA-PITCH` says two halves are spare.
  Costs nothing but a half. Restores the published table exactly.
- Use a **1 kΩ** linear pot: `R/4 = 250 Ω` on a 21.0 kΩ leg = 1.2 % error,
  centre at ≈ +0.13 V `[calc]`. Loads the 5.21 V rail with 5.2 mA, which the
  LM317LZ carries (`[repo] 0004` budgets ~13 mA today) but see F-OFF-3.
- Raise R-OFF/R-OFFNEG 10× (210 k / 953 k) — works, but multiplies the summer's
  resistor noise and the op-amp's bias-current error, and I would not.

### F-OFF-2 (Medium) — "zero at centre" is not supported by the tolerance stack either

Even buffered, `[calc]`:
```
resistor term:  R-FB, R-OFF, R-OFFNEG all 1%
   wiper leg  1.914 × 2.605 = 4.987 V, ±2%  → ±100 mV
   -12V leg   5.062 V,        ±2%           → ±101 mV
   worst case                                ±201 mV
pot mechanical centre, typical ±3% of track: ±156 mV of wiper × 1.914 = ±299 mV
LM317 untrimmed:  Vref ±4% → rail 5.00…5.42 V (see F-OFF-3)
   at 5.00 V, k=0.5: −4.786 + 5.062 = +0.276 V
   at 5.35 V, k=0.5: −5.121 + 5.062 = −0.059 V
```
**"Zero at centre" is 0 ± 0.5 V worst case, ±0.2 V typical** — 5–10 % of the
±5 V window. For a performance knob set by ear that is fine and I would ship it.
But the page prints +0.07 V as if it were designed, and the detent proposal
assumes it. Say "approximately centre", or add the buffer and a trim, or accept
and drop the detent.

### F-OFF-3 (Medium–High) — the offset reference is the DAC's supply rail, and the −12 V bus

Two couplings neither page costs:

**(a) −12 V.** `R-OFFNEG` taps the module's −12 V — which `[repo] power-entry.md`
shows as `bus −12V ─[D3 1N5817]─[FB3]─[C3 47µF]`, i.e. the **rack bus rail**
behind a Schottky and a bead, with no regulation. Transfer to the jack is
`40.2/95.3 = 0.4218` `[calc]`, flat in band. The page's sensitivity check uses
**50 mV** of rail movement → 21 mV, "0.21 % of span". But:
```
Eurorack -12V tolerance, ±5% typical  = ±600 mV  →  ±253 mV at the jack (2.5% of span)
1N5817 Vf tempco ~ -1.5 mV/K, 30 K warm-up = 45 mV → 19 mV at the jack
rack bus audio-band noise, say 200 µV RMS → 84 µV RMS at the jack
```
`[from memory]` for the Schottky tempco and the ±5 % rack convention. 50 mV is
an order of magnitude under the rail's own specification, chosen without
justification. The **±253 mV** figure is the honest one, and it means the
breath jack's rest point moves with what else is in the rack. Still acceptable
for a performance offset — but `[repo] 0006` rejected a rail divider on *pitch*
for exactly this reason, and the asymmetry deserves the real number, not a
flattering one.

**(b) The 5.21 V rail is the DAC8568's AVDD.** `[repo] 0004`: the LM317LZ exists
"for the DAC's AVDD". `[repo] breath-output-stage.md` then takes POT-OFFSET from
it, transfer up to `40.2/21.0 = 1.914` `[calc]`, and TRIM-BREATH-ZERO from it
too (transfer 0.0839 × 0.50…4.02). The DAC draws current steps at the 4 kHz
refresh with 2 MHz SPI edges inside them. `[calc]`, with an LM317 closed-loop
output impedance of 0.1–1 Ω at 4 kHz `[from memory]` and ~1 mA of AVDD transient:
```
0.1–1 mV on the rail × 1.914 (offset at full CW) = 0.2–1.9 mV at the breath jack,
at 4 kHz and correlated with DAC traffic
```
Into a VCA that is a 4 kHz tone, not noise. **This is the one architectural
finding.** The entire point of ADR 0003's analog breath path is that "breath
never gets digitised on its way to the jack"; this puts the DAC's supply on the
breath output with a gain of nearly 2. It is not a digitisation, but it is
digital contamination arriving by the back door.

Fix is cheap: **RC-isolate the offset/trim reference tap from AVDD**
— 100 Ω + 10 µF gives a 159 Hz corner `[calc]` and costs two parts, and the tap
draws ≤ 0.8 mA so the 80 mV of drop is a constant the trimmer and the knob both
absorb. Do the same for the TRIM-BREATH-ZERO divider. **Medium–High.**

### F-OFF-4 (Medium) — "buffered +5.21 V" has no buffer

`[repo] breath-output-stage.md` drawing: `buffered +5.21 V ──[POT-OFFSET 10k]`.
`[repo] bom.csv U-OPA-PITCH` enumerates all ten used halves: "pitch, mod 1-4,
mod offset follower, VREFOUT follower, breath REF-zero buffer, breath gain
buffer, breath summer" — **no half for a 5.21 V buffer.** Same page brags "Two
op-amp halves, which settles a count that has been wrong in the BOM twice."

It is still wrong. Either the word "buffered" comes out of the drawing (in which
case F-OFF-3(b) gets worse, because the pot is then directly on AVDD), or a
third half is spent (there are two spare, so it fits). Note that if F-OFF-1 is
fixed by buffering the *wiper*, both problems close with one half: buffer the
wiper, leave the track on the rail.

### F-OFF-5 (Low) — endpoints were computed with R-FB = 40 kΩ, not 40.2 kΩ

`[calc]`: with the BOM's 40.2 k the table is **+5.062 / +0.075 / −4.911**, not
+5.04 / +0.07 / −4.89. The drawing's ASCII says `R-FB 40k` while the values
table and `[repo] bom.csv R-BREATH-SUM` say 40.2 k. Cosmetic; fix the drawing.

---

## 8. `POT-GAIN` / `R-GAIN-FLOOR` / the summer — gain, and gain↔offset interaction

### The topology does decouple them — confirmed

The central claim holds. Offset current enters a virtual ground whose transfer
(`R_FB/R_OFF`, `R_FB/R_OFFNEG`) contains no POT-GAIN term; POT-GAIN attenuates
at a buffered node ahead of R-IN, so its transfer contains no offset term; and
the pedestal is nulled at the in-amp's REF, **ahead** of the pot, so the trim
holds at every gain setting. The WX5 interaction the page cites is genuinely
designed out. Good.

### F-GAIN-1 (Note) — the residual interaction, quantified

Anything that drifts at the in-amp output *after* commissioning is multiplied by
the gain knob `[calc]`:
```
sensor pedestal tempco 0.5 mV/K [repo] 0003 × 20 K = 10 mV at the sensor
→ × 2.161 = 21.6 mV at the in-amp
→ × 0.503 = 10.9 mV at the jack at min gain
→ × 4.020 = 86.9 mV at the jack at max gain
```
So sweeping GAIN after a 20 K warm-up moves the jack's rest point by **76 mV**,
0.76 % of span. The page's flat "step 2 no longer disturbs this" should read
"disturbs it by ~1 % instead of ~100 %". Honest, and still a win.

### F-GAIN-2 (Low) — the "taper" open item points the wrong way

`[repo] breath-output-stage.md` *Still open*: "Linear gives a knob that does most
of its work in the last quarter turn. A log or pseudo-log taper … is a feel
question."

That is the behaviour of a **feedback rheostat**, whose law is 1/x. This is a
buffered attenuator, and `[calc]` its law is `gain(x) = 0.5030 + 3.5170x`,
**linear in gain**. In dB:
```
x=0    : 0.503×  =  -6.0 dB
x=0.5  : 2.262×  =  +7.1 dB     (13.1 dB in the first half)
x=1    : 4.020×  = +12.1 dB     ( 5.0 dB in the second half)
```
It does most of its dB work in the **first** half, not the last quarter. A log
(audio) taper would make that worse; a **reverse-log** taper is what linearises
it. The open item as written will send E10 to the wrong part. Correct the
sentence before anyone buys pots.

### F-GAIN-3 (Note) — R-GAIN-FLOOR is 1 % under a ±20 % track

`[calc]`, with a ±20 % 50 k pot `[from memory]` for typical panel-pot tolerance:
```
40 kΩ track: 7.15/47.15 = 0.1516 → 0.610× at the jack
60 kΩ track: 7.15/67.15 = 0.1065 → 0.428×
```
The "0.5× floor" is really **0.43–0.61×**. The top of the range (1.000 ×4.02) is
exact regardless, because the wiper reaches the top terminal. A 1 % floor
resistor under a 20 % track is spurious precision — but harmless, so leave it.

### F-GAIN-4 (Medium) — the summer's `+` input is the highest-leverage ground node on the board

Undocumented anywhere. `[calc]`, noise gain of the summer:
```
1/10k + 1/21k + 1/95.3k = 100.0 + 47.62 + 10.49 = 158.1 µS  →  R_par = 6.325 kΩ
noise gain = 1 + 40.2/6.325 = 7.36
```
Any offset between the summer's non-inverting reference and the AGND that
R-GAIN-FLOOR, C-OUT-BREATH and the in-amp's REF chain return to appears at the
jack **multiplied by 7.36**. One millivolt of ground bounce there is 7.4 mV at
the jack. The breath stage alone pushes ~0.7 mA into module AGND (POT-OFFSET
0.52 mA, R-GAIN-FLOOR up to 81 µA, R-OFFNEG's 126 µA returning through the
op-amp) `[calc]`. This belongs in the layout notes as an explicit star rule; it
is the single highest-gain path from copper geometry to output error in the
module.

---

## 9. Output stage — drive, short circuit, output-to-output, clipping

I could not fault this part. Recording the checks so nobody redoes them.

**Short to ground** `[calc]`, op-amp clipped at 11.5 V `[from memory]` for
OPA2197 RRIO swing on ±12 V:
```
I = 11.5 V / 1 kΩ = 11.5 mA          P(R-OUT-PROT) = 11.5e-3² × 1k = 132 mW
```
Against `[repo] bom.csv R-OUT-PROT` ≥500 mW. ✓ Op-amp sources 11.5 mA against a
short-circuit limit of `[from memory]` ~65 mA. ✓

**Patched into another module's output** — the worst realistic abuse `[calc]`,
this output clipped high against a neighbour driving −10 V through 220 Ω (the
stiffest common Eurorack output impedance):
```
I = (11.5 + 10) / (1000 + 220) = 17.6 mA
P(R-OUT-PROT) = 17.6e-3² × 1k = 310 mW        against ≥500 mW ✓
```
Against a 100 Ω output: `21.5/1100 = 19.5 mA → 381 mW`, still inside. ✓
Note this is **not** the pitch stage's problem: breath takes feedback at the
op-amp output, not at the jack `[repo] breath-output-stage.md`, so the loop does
not fight the other module. The ≥500 mW spec, argued in the BOM from the *pitch*
case, covers breath with 24 % margin.

**Back-powering.** `D-JACK-CLAMP` is on the op-amp side of R-OUT-PROT
`[repo] bom.csv D-JACK-CLAMP` `[repo] breath-output-stage.md`, so a neighbour
driving the jack sees 1 kΩ before it reaches any clamp — correct, and the BOM's
own argument. ✓

**C-OUT-BREATH placement.** Jack side of R-OUT-PROT, feedback taken at the
op-amp `[repo] breath-output-stage.md` drawing. The 1 kΩ isolates 330 nF from
the op-amp, which is what keeps the summer stable. ✓ `[calc]`
`1/(2π × 1k × 330n) = 482.3 Hz`. ✓ Output impedance 1 kΩ, the Eurorack norm.

**Clipping.** `[repo]` correctly notes offset +5 V with gain 4× reaches
`4.02 × 4.64 + 5.06 = +23.7 V` `[calc]` against a ±11.5 V rail clip, and calls
it the player's business. Agreed. Two things to add:

### F-OUT-1 (Low) — clipping starts closer to the playing range than stated

`[calc]`, at the **nominal** working gain (2.13×) with offset at 0:
```
clip at 11.5 V → |in-amp| = 11.5/2.13 = 5.40 V
→ sensor = 5.40/2.161 + 0.200 = 2.699 V
→ P = (2.699 − 0.200)/0.766 = 3.26 kPa
```
Only **16 % above the 2.8 kPa the gain range was sized from**, and a hard rail
clip with no soft region. A player who overblows by a sixth hits a wall. That is
arguably correct behaviour for a 10 V CV, but it should be stated, and it makes
F-CAL-1 below load-bearing.

### F-OUT-2 (Note) — a 330 nF at the jack is a heavy load for a neighbour

If someone patches a gate or trigger output into this jack (mispatch), that
module must drive 330 nF through its own output resistance: a 1 kΩ output gives
a 330 µs edge `[calc]`. Harmless, but it is the symptom someone will report.

---

## 10. Noise — total, and whether the trim and pot beat the sensor

All referred to the jack at the nominal 2.13× setting. Single-pole noise
bandwidth from the output RC: `π/2 × 482 = 757 Hz`, `√757 = 27.5`.

**In-amp input-referred** `[calc]`, `[from memory]` for INA828 e_n = 7 nV/√Hz and
i_n ≈ 350 fA/√Hz:
```
source Z per leg = 1M ∥ 11k = 10.88 kΩ
thermal, per leg = √(1.656e-20 × 10880) = 13.4 nV/√Hz ; two legs = 19.0 nV/√Hz
current noise    = 350 fA × 10.88 kΩ = 3.8 nV/√Hz ; two legs = 5.4 nV/√Hz
total            = √(7² + 19.0² + 5.4²) = √439 = 21.0 nV/√Hz   ← resistors dominate
```
At the jack: `21.0 nV × 2.161 × 2.13 = 96.7 nV/√Hz → 2.66 µV RMS`.

**POT-GAIN** `[calc]`, worst-case Thévenin at mid-rotation
`25k ∥ (25k+7.15k) = 14.1 kΩ`:
```
√(1.656e-20 × 14100) = 15.3 nV/√Hz × 4.020 = 61.5 nV/√Hz → 1.69 µV RMS
```

**Summer** `[calc]`, noise gain 7.36, `[from memory]` OPA2197 e_n = 5.5 nV/√Hz:
```
op-amp   5.5 × 7.36                    = 40.5 nV/√Hz
R-FB     √(1.656e-20×40200)            = 25.8
R-IN     √(1.656e-20×10000) × 4.020    = 51.9
R-OFF    √(1.656e-20×21000) × 1.914    = 35.8
R-OFFNEG √(1.656e-20×95300) × 0.4218   = 16.8
total = √(1640+666+2694+1281+282) = 81.0 nV/√Hz → 2.23 µV RMS
```

**REF / trim path** `[calc]`, the LM317's ~50 µV RMS over 10 Hz–10 kHz
`[repo] bom.csv C-REG-ADJ` scaled to a 757 Hz band and through the 0.0839
divider, plus the buffer:
```
50 µV × √(757/10000) = 13.8 µV in band × 0.0839 = 1.16 µV at REF
+ OPA2197 buffer 5.5 nV × 27.5 = 0.15 µV
at the jack: 1.17 µV × 2.13 = 2.49 µV RMS
```

**Total** `[calc]`: `√(2.66² + 1.69² + 2.23² + 2.49²) = √21.4 = 4.6 µV RMS` at
the jack, over 10 V of span = **0.46 ppm, 127 dB below full scale.**

### Answer to "do the trim and pot introduce more than the sensor does"

**No, by more than two orders of magnitude.** `[from memory]`, the MPXV4006's
own output noise is on the order of a few hundred µV to ~1 mV RMS in a kHz band,
and the *physical* signal — breath turbulence and diaphragm tremor — is
millivolts at the sensor, which `[repo] 0003` itself says sits "orders of
magnitude" above a 16-bit LSB. Multiply 1 mV of sensor noise by 2.161 × 2.13 and
you get **4.6 mV at the jack, 1000× the whole electronics chain.**

So: **thermal noise is a solved non-problem and should stop being discussed.**
What is *not* solved is **correlated interference**, which is what actually
reaches the ear:

| Path | Transfer to jack | Magnitude |
|---|---|---|
| −12 V bus, audio band | 0.4218 | ~84 µV RMS at 200 µV of bus noise, **18× the entire thermal budget** |
| −12 V bus, DC/thermal | 0.4218 | up to **±253 mV** (F-OFF-3a) |
| LM317 rail = DAC AVDD, 4 kHz | up to 1.914 | **0.2–1.9 mV**, tonal (F-OFF-3b) |
| Everything above, thermal | — | 4.6 µV RMS |

Two capacitors (100 nF at the trim wiper) and one RC (100 Ω + 10 µF isolating
the offset/trim tap from AVDD) remove the two that matter.

---

## 11. Calibration and citation errors that change the design

### F-CAL-1 (Medium) — **2.8 kPa is a false citation, and the gain range rests on it**

`[repo] breath-output-stage.md`: "**Real playing only reaches about 2.8 kPa
against the sensor's 6 kPa range** (ADR 0003)". `[repo] carrier.md` §2 then
cites it back as "[2.8 kPa from breath-receive-stage.md]".

**"2.8 kPa" does not appear in ADR 0003.** I grepped the whole file. What ADR
0003 says is: "Normal wind-controller playing sits around **0–5 kPa**"
`[repo] 0003` line 136. The 2.8 figure has no source in the repo and the two
schematic pages cite each other for it.

It is load-bearing `[calc]`:
```
at 2.8 kPa: in-amp −4.638 V → gain for 10 V = 2.156 → x = (2.156−0.503)/3.517 = 0.470  (mid-knob ✓)
at 5.0 kPa: sensor 4.030 V, in-amp −8.279 V → gain for 10 V = 1.208
                                             → x = (1.208−0.503)/3.517 = 0.200  (a fifth of a turn)
```
If 5 kPa is right, the working point is at 20 % of rotation, the whole upper
three-quarters of the knob is unusable, and the 0.5–4× range is centred in the
wrong place — the argument "which puts the working point near 2.1× — in the
middle of the knob rather than at an end stop" `[repo] breath-receive-stage.md`
fails. If 2.8 kPa is right, the range is well chosen. **Find the source or
measure it at E2/E10 before POT-GAIN's range is frozen.** This is the single
number the gain design depends on and it currently has no provenance.

(If both are wanted: a 0.25–2× range, i.e. R-GAIN-FLOOR ≈ 3.4 k against a fixed
×2, covers 2.8 kPa at x=0.44 and 5 kPa at x=0.20 `[calc]` — but I would settle
the measurement first rather than widen the knob.)

### F-CAL-2 (Low) — three different values for the in-amp's full-scale output

- `[repo] breath-receive-stage.md`: "reaches **−9.6 V** at full sensor range"
- `[repo] breath-output-stage.md` table: "Sensor full scale (6 kPa) … **−10.05 V**"
- `[repo] bom.csv U-DIFFRX`: "Output is −0.44 V at rest to **−10 V** at full"
- The same receive page's own derivation: "**jack span 9.94 V**"

`[calc]` the correct value is `−2.16106 × 4.600 = −9.941 V`. −10.05 is
`2.18483 × 4.600`, i.e. the raw gain without the 0.9891 divider; −9.6 has no
derivation I can reconstruct. Same node, three numbers, one page apart.
Similarly "hard blow −4.69 V" is the raw-gain figure; effective is **−4.64 V**.

### F-CAL-3 (Medium) — stale statements that contradict deleted hardware

All in `[repo] breath-receive-stage.md`:

1. **"if `R1` opens, the presence detect de-asserts and takes the whole SPI link
   with it"** (line 195). `[repo] digital-and-supervision.md` §"There is no
   presence detect either" and `[repo] bom.csv U-LVL-MOD` ("The presence-gated
   OE is deleted along with its comparator") say there is no presence detect.
   The consequence described cannot happen. R1 opening is silent.
2. **"now that `REF` is grounded it touches the breath stage in no way at all"**
   (line 289). REF is not grounded; it carries the trimmer, which is the
   page's own central decision, argued at length 150 lines earlier.
3. The whole §"What the jack does when the watchdog fires" reasons about a
   watchdog that `[repo] bom.csv R-CLR-PU` says is deleted
   ("**THE WATCHDOG IS DELETED** (U-WATCHDOG, R-WDT, C-WDT all gone)").
4. `[repo] bom.csv U-DIFFRX`: "the downstream stage inverts, which is also the
   topology that does gain-then-offset **with two pots in one op-amp half**" —
   contradicted by the same BOM's U-OPA-PITCH row and by
   breath-output-stage.md, both of which say two halves, and which the output
   page calls "a count that has been wrong in the BOM twice". It is wrong a
   third time, in a different row.
5. `[repo] bom.csv U-DIFFRX`: "Output is **−0.44 V at rest**" — the pre-trimmer
   value. With the trimmer it is 0 V, which is the whole point of the trimmer.

These matter because the breath pages are written as the authority that
overrides the ADRs ("Where it disagrees with ADR 0003's prose, this page wins").
An authority document carrying five stale claims is how the next reviewer gets
five findings that are really one.

---

## 12. Power sequencing and fault matrix — consolidated

| Case | In-amp out | Jack (2.13×, offset 0) | Detected? |
|---|---|---|---|
| Normal, at rest | 0 V | 0 V | — |
| Normal, 2.8 kPa | −4.64 V | +9.9 V | — |
| Normal, 6 kPa | −9.94 V | clips at +11.5 V (from 3.26 kPa, F-OUT-1) | no |
| **BREATH conductor open** | +0.432 V | **−0.93 V**, dead | **no** |
| **AGND conductor open** | 0 V + shift | 0 V ± 0.27 V, light-show modulated | **no** |
| **Cable unplugged** | +0.432 V | **−0.93 to −1.76 V** | no |
| **Instrument unpowered, cable in** | ≈ +0.432 V | ≈ −0.93 V | no |
| **Module powered first (every boot)** | +0.432 V → 0 V | **−0.93 V → 0 V over the instrument's boot** | n/a |
| Sustained +12 V on BREATH | at the rail, clipped | clipped high, held | no |
| Jack shorted | unaffected | 0 V, 132 mW in R-OUT-PROT | n/a |
| Jack into another output | unaffected | contested, 310–381 mW in R-OUT-PROT | n/a |

Observations:

- **Nothing in the breath chain is detectable in software.** That is a deliberate
  consequence of the analog path plus the deleted presence detect, and I am not
  arguing against either — but it means every entry in the "no" column is a
  bench-only diagnosis, and the E-milestone list should say so explicitly.
- **The power-on transient is a −0.93 V dip at the jack on every switch-on**, not
  the 0 V `[repo] 0006`'s table promises. Rank it by what the jack drives: into
  a VCA, silent; into a bipolar mod input, a ~1 V step of a few hundred ms.
- **The sustained +12 V "designed-safe" case is designed-safe at the instrument
  only.** At the module, BREATH at +12 V against AGND gives
  `V_out = −2.161 × 12 + 0.432 = −25.5 V` demanded, so the INA828 slams to −11.8 V
  and the jack slams to +11.5 V and holds `[calc]`. `[repo]
  breath-receive-stage.md` notes this ("the jack clips high and *holds*") — worth
  keeping, and worth noting that with the presence detect gone there is nothing
  that will ever say so.

---

## 13. Findings, ranked

| # | Node / ref | Finding | Rank | Confidence |
|---|---|---|---|---|
| F-R1B | `R-SER-BREATH-INST` | R1b is in the BOM (qty 2) and both breath pages but **absent from `carrier.md` §2**, the page about to be laid out. Unretrofittable. | **High** | **High** — verified by grep of the drawing |
| F-OFF-1 | `POT-OFFSET` / `R-OFF` | Unbuffered wiper puts "zero at centre" at **+0.605 V** and the zero crossing at 56.7 % of rotation. Directly contradicts an explicit "does not need buffering". A centre detent would detent at the wrong place. | **High** | **High** — pure arithmetic |
| F-OFF-3 | `R-OFFNEG`, LM317 rail | −12 V rack bus reaches the jack at ×0.4218 (±253 mV over the rail's real ±5 %, not the 50 mV assumed); the 5.21 V rail is the **DAC's AVDD** and reaches it at up to ×1.914, carrying 4 kHz DAC traffic. | **Medium–High** | Medium-High (rail tolerance from memory; mechanism certain) |
| F-CAL-1 | `POT-GAIN` range | **"2.8 kPa (ADR 0003)" is a false citation** — ADR 0003 says 0–5 kPa. The 0.5–4× range and "working point in the middle of the knob" both depend on it. At 5 kPa the working point is at 20 % rotation. | **Medium** | **High** — grepped |
| F-CM-2 | `C_cm`, `C_diff` | "C_diff dominant divides the CM mismatch" is false below the differential pole; the floor is ωRδ, C_diff-independent. Conclusion (±1 % C0G) right, reasoning wrong — and `bom.csv` still carries **no tolerance** on C-FILT-BREATH. | **Medium** | **High** — derived |
| F-CM-4 | `R-BIAS-INAMP` | The 1 MΩ pair at 1 % is the **dominant resistive CMRR term at 73 dB**, undocumented; the design lands at ~58 dB at its band edge, missing its own 60 dB budget. 5 % parts would give 59 dB alone. | **Medium** | Medium-High |
| F-CM-3 | `C_cm`, `R2`/`R3` | The claimed 2.4 GHz RF-rectification protection is ~37 dB, parasitic-limited, not what the 482 Hz pole implies. Needs a real RF element at the pin, or the INA828's own EMIRR — which I could not verify. | **Medium** | **Medium** — gated on one blocked datasheet |
| F-BIAS-1 | `R4`/`R5` | The jack does **not** rest at 0 V unplugged / BREATH-open / during boot; it rests at −0.93 to −1.76 V. Three documents say 0 V, one of them citing a deleted pulldown. | **Medium** | **High** |
| F-CLAMP | `D-CLAMP-BREATH` | Drawing puts the BAV99 ahead of R2/R3; the BOM says behind. Different circuits, different protection, and a layout-blocking choice. No module-end ESD part exists either way. | **Medium** | **High** |
| F-OFF-4 | `U-OPA-PITCH` | "buffered +5.21 V" has no op-amp half in the census, on the page that claims the half count is finally settled. | **Medium** | **High** |
| F-GAIN-4 | summer `+` input | The summer's ground reference is multiplied by a **noise gain of 7.36** to the jack — the highest-leverage ground node in the module, and it is in no layout note. | **Medium** | **High** |
| F-CAL-3 | several | Five stale statements in the pages that are declared authoritative: presence detect (deleted), watchdog (deleted), "REF is grounded" (it isn't), "−0.44 V at rest", "two pots in one op-amp half". | **Medium** | **High** |
| F-OFF-2 | `POT-OFFSET` | Even buffered, "zero at centre" is 0 ± 0.5 V worst case from 1 % resistors, pot centre tolerance and the LM317's untrimmed ±4 %. | **Medium** | Medium-High |
| F-REF-B | `TRIM-BREATH-ZERO` | No filter capacitor at the trim wiper or the REF pin; the LM317's ~50 µV RMS reaches the jack at ×0.042–0.337 and is a co-dominant noise term. 100 nF fixes it. | **Low** | **High** |
| F-RTR | `R-TRIM-RANGE` | Still status `open`. The value is fully determined: **42.2 kΩ** above a 10 k track from 5.21 V gives 0–0.998 V. | **Low** | **High** |
| F-GAIN-2 | `POT-GAIN` | The taper "still open" describes a rheostat's 1/x law, not this attenuator's linear one. It does most of its dB work in the **first** half; a log taper would make it worse. | **Low** | **High** |
| F-CAL-2 | in-amp output | −9.6 / −9.94 / −10.05 / −10 V for the same node across two pages and the BOM; correct value −9.941 V. "Hard blow −4.69 V" should be −4.64 V. | **Low** | **High** |
| F-OFF-5 | `R-FB` | Offset endpoints computed with 40 kΩ; the part is 40.2 kΩ. Correct table: +5.062 / +0.075 / −4.911. | **Low** | **High** |
| F-OUT-1 | `R-OUT-PROT`, rails | At the nominal gain the jack hard-clips from **3.26 kPa**, only 16 % above the design "hard blow". Rail clip, no soft region. | **Low** | **High** |
| F-CM-1 | `C_diff`/`C_cm` | The differential corner is **459 Hz**, not 482 — the two C_cm add 0.75 nF in series across the pair. | **Note** | **High** |
| F-GAIN-3 | `R-GAIN-FLOOR` | 1 % floor resistor under a ±20 % track: the "0.5×" floor is really 0.43–0.61×. Harmless. | **Note** | Medium |
| F-BIAS-2 | `AGND` conductor | Broken AGND degrades gracefully to ±0.27 V of light-show modulation and is undetectable. Worth an explicit E-milestone test. | **Note** | **High** |
| F-SRC | `C-FILT-BREATH` | 15 nF **C0G** in 0805 is at or past the usual limit of the dielectric in that case size; 1206 or a split pair may be needed. Could not check distributors. | **Note** | Low — unverified |
| — | `R-OUT-PROT`, `D-JACK-CLAMP`, `C-OUT-BREATH` | **Output stage passes every abuse check I ran**: short 132 mW, output-to-output 310–381 mW against ≥500 mW, clamp on the correct side of the 1 kΩ, cap outside the loop. Recorded so it is not re-reviewed. | **Pass** | **High** |

---

## 14. What I would do before layout

Ordered by what cannot be undone later:

1. **Put the R1b pad on the carrier** (F-R1B). Instrument-side, unretrofittable,
   free, and two independent mechanisms want it.
2. **Settle `D-CLAMP-BREATH`'s side of R2/R3** and decide whether a module-end
   ESD part exists (F-CLAMP). Both are footprints.
3. **Spend the spare op-amp half on POT-OFFSET's wiper** (F-OFF-1, F-OFF-4).
   Closes the centre-detent question and the phantom "buffered 5.21 V" in one
   part.
4. **RC-isolate the offset/trim reference from the DAC's AVDD** (F-OFF-3b):
   100 Ω + 10 µF. Two parts, and it is the only thing standing between the DAC's
   4 kHz traffic and a signal path that exists to be free of it.
5. **Put the tolerance on `C-FILT-BREATH`** (±1 % C0G on both 1.5 nF) and
   **tighten `R-BIAS-INAMP` to 0.1 %** (F-CM-2, F-CM-4) — the latter moves the
   stack from 58 dB to 71 dB at the band edge for the price of a different reel.
6. **Find or measure the real playing pressure** (F-CAL-1) before POT-GAIN's
   range is frozen.
7. **Fix the arithmetic and the stale prose** (F-CAL-2, F-CAL-3, F-OFF-5,
   F-GAIN-2, F-CM-1, F-BIAS-1). None changes copper; all of them change what the
   next reviewer spends their time on.

## 15. What I could not check

- **INA828**: CMRR vs frequency at G ≈ 2, I_B / I_OS, e_n / i_n, REF input
  impedance, output swing, and **whether it has an integrated EMI filter**.
  ti.com, mouser.com and lcsc.com all returned 403 at the proxy. F-CM-3's rank
  depends on the last of these.
- **MPXV4006DP**: whether the 0.152–0.378 V pedestal band and the 0.5 mV/K
  offset tempco are as quoted. nxp.com not attempted after three refusals; the
  pages themselves flag the tempco as unverified.
- **OPA2197**: GBW, Ro, e_n, output swing under load, short-circuit limit.
- **BAV99**: leakage vs temperature (it does not matter — worst case I computed
  is 238 µV at the jack).
- **LM317LZ**: I_ADJ and temperature stability. `[calc]` with `[from memory]`
  I_ADJ = 50 µA the rail is `1.25 × (1+475/150) + 50 µA × 475 = 5.208 + 0.024 =
  5.232 V`, not the 5.21 V used everywhere — which is inside the noise of the
  ±4 % V_ref tolerance that F-OFF-2 already covers.
- **Distributor availability** of 15 nF C0G 0805, 1.5 nF C0G ±1 % 0805, and a
  1206 1 kΩ at ≥500 mW (`bom.csv` already flags the last one).
