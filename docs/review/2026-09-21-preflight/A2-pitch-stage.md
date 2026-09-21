# A2 — Pitch stage (`hardware/module/pitch-stage.md`)

**Preflight wave, 2026-09-21. Cold: no `docs/review/**` was read.**

Slice: the 1 V/oct chain, `VREFOUT` → reference buffer → LT5400 → OPA2197 →
`PITCH` jack. Error budget in cents; **1 mV at the jack = 1.2 cents** `[calc:
1 V/oct = 1200 cents/V]`.

Every load-bearing number on the page has been re-checked against the banked
PDFs. Provenance on every claim; `[calc]` shows its arithmetic.

**Documents used**

| Short form | File | Doc |
|---|---|---|
| `SBAS430E` | `datasheets/texas-instruments/DAC8568CIPW.pdf` | DAC7568/8168/8568, Jan 2009 rev Jan 2014, 62 pp |
| `SBOS737C` | `datasheets/texas-instruments/OPA2197.pdf` | OPA197/2197/4197, Jan 2016 rev Mar 2018, 56 pp |
| `5400fa` | `datasheets/other-semi/LT5400.pdf` | LT5400 rev fa, 10 pp |
| `ERA-A` | `datasheets/discrete-and-power/ERA-3A-thin-film-0p1pct.pdf` | Panasonic ERA 1A/2A/3A/6A/8A |

---

## 0. Summary of what changed

Nine decisions, all with values. Sections 1–6 derive them.

| # | Item | Decision |
|---|---|---|
| 1 | `TRIM-OFFSET` | Rebuilt as **divide-and-gain-back**: pot **1 kΩ** (was 10 kΩ) + `R-TRIM-B` 24.3 kΩ + gain-back ×1.0200 from `R-TRIM-F` 200 Ω / `R-TRIM-G` 10.0 kΩ. Centre **2.4996 V**, authority **±50.4 mV**, constant 98.8 µA load on `VREFOUT` |
| 2 | `R-BIAS-DAC` | **1 MΩ**, not 100 kΩ. 100 kΩ against the DAC's 4 Ω output impedance is a **−40 ppm gain error = 0.46 cents**; 1 MΩ makes it 0.005 cents. Position (at the DAC pin) was already right |
| 3 | `TRIM-GAIN` | **Deleted.** Fit a **0 Ω 0805 link**, keep the land pattern. It has no downward authority, it puts a 100–250 ppm/°C cermet inside the one ratio the LT5400 was bought to protect, and firmware's 11-point table already owns gain |
| 4 | Fail-open trimmers | `TRIM-GAIN`'s 2-terminal problem **disappears with the part**. `TRIM-OFFSET` is 3-terminal and cannot be strapped — it gets **`R-TRIM-BLEED` 1 MΩ** wiper→pot-bottom, degrading a lost wiper to −51 mV (61 cents flat) instead of a rail |
| 5 | Spare LT5400 sections | Use die **R2 (pins 2–7)** and **R3 (pins 3–6)** for the 1 V/oct pair; **tie R1 (pins 1, 8) and R4 (pins 4, 5) to `AGND_MOD`** as on-die guards. Do **not** parallel them into the network — it halves R2 and breaks the settled `C-FB-PITCH` compensation |
| 6 | Exposed pad | **`AGND_MOD`**, the analog-return region, stitched local to the stage. **Zero DC effect on the transfer function** — the pad is not DC-connected to any resistor. Forbidden: floating, either rail, `DIG_GND`, `PWR_GND`, umbilical `AGND` |
| 7 | `pitch-cents-budget` | **0.61 cents RSS** static + 10 °C thermal, post-calibration (1.20 over a 0–40 °C rack, 1.47 linear sum). **System total ~8.1 cents**, of which ~8.0 is the two ground terms |
| 8 | `C-REF-TRIM` | **New, 100 nF**, wiper node to `AGND_MOD`. 1.27 kHz on the reference tap; removes the LED-pickup exposure the whole `VREFOUT` argument exists to create |
| 9 | Net naming | Bare `AGND` on this page is the **module analog return** and collides with the umbilical's in-amp sense conductor of the same name. Rename to **`AGND_MOD`** here |

**Two stale figures found on the page itself**, both CLAUDE.md-class (a value
changed, derived numbers did not follow) — §5.1 and §5.4.

---

## 1. `TRIM-OFFSET` — the buildable network

### 1.1 The constraint nobody has written down

The page correctly says a divider from `VREFOUT` can only go below it. It then
offers two routes — "dividing `VREFOUT` and gaining it back, or injecting a
small bipolar correction". **The second route does not exist**, and proving that
narrows the design to one answer.

`[calc]` The whole value of referencing the offset to `VREFOUT` is the tracking
identity the page derives: `Vout = (1+δ)(2·Vdac − 2.500)` for a fractional
reference drift δ, which converts a reference error into a pure *gain* error.
That holds **only if every term in the intercept is proportional to `VREFOUT`**.
So write the reference path as a linear combination of `VREFOUT`-derived
sources with coefficients `cᵢ`:

```
V_ref = VREFOUT · Σ cᵢ ,  and we need Σ cᵢ = 1 at centre.
```

A passive divider can only produce `cᵢ < 1`. A sum of terms each `< 1` reaches 1
only if at least one coefficient exceeds 1 — i.e. **a gain greater than unity is
mandatory somewhere in the reference path.** An injected correction from
anything that is *not* `VREFOUT` (a rail, a second reference) satisfies the
arithmetic but breaks the tracking identity, which is the only reason the
reference is `VREFOUT` at all.

**Divide-and-gain-back is not one option of two. It is the only topology that
keeps the argument the page is built on.**

### 1.2 The second constraint: a follower does not isolate `VREFOUT` from the trimmer

`[repo docs/decisions/0006-cv-channel-allocation.md:~610]` ADR 0006 says:
"Hanging a *trimmer* directly on `VREFOUT` would make the reference move as the
trimmer is turned… A follower breaks that."

**A follower does not break that.** The trimmer is *ahead* of the follower, so it
is a **load** on `VREFOUT`, and the follower is downstream of the loading.
`[datasheet SBAS430E p.4]` the reference's load regulation is **30 µV/mA
sourcing**, so a trim network whose current changes with wiper position moves
`VREFOUT`, and the DAC's full scale is `2 × VREFOUT`.

The fix is in the topology, not the buffer: **a 3-terminal divider draws a
current set only by its end-to-end resistance**, because the wiper feeds an
op-amp input (`I_B` ≤ ±20 pA at 25 °C `[datasheet SBOS737C p.7]`). Load is
constant with wiper position by construction. A 2-terminal (rheostat) connection
is not, and the current BOM row implies one.

### 1.3 The third constraint: the divider's own tempco is an *offset* drift

`[calc]` `V_ref` sets the intercept, and intercept error is the expensive kind
(1.2 cents/mV at every note, vs. a gain error's 0 cents at the bottom of the
range). For a symmetric 2:1 divider built from two independent resistors with
tempcos α_A, α_B, the ratio drifts at `(α_B − α_A)/2`. Two ordinary ±25 ppm/°C
parts drifting oppositely give **25 ppm/°C of ratio → 250 ppm over 10 °C →
625 µV on `V_ref` → 0.75 cents.** That would be the largest static term in the
whole budget, on a stage that spent $8 on a matched network to avoid exactly
this.

**The escape is to make both the division and the gain-back small
perturbations.** If the division is `1 − p` and the gain-back is `1/(1 − p)`, the
tempco of each is attenuated by `p`:

```
[calc]  divider:    d(D)/D  ≈ p·(α_pot − α_B)
        gain-back:  d(G)/G  = (x/(1+x))·(α_F − α_G),  x = R_F/R_G ≈ p
```

At `p ≈ 0.02` a 50 ppm/°C resistor mismatch becomes **1 ppm/°C**. This is the
design's key idea and it is why no spare LT5400 section is needed here.

### 1.4 The network

```
                    ┌──────────────────────────────────────────────┐
  VREFOUT ──┬───────┤ TRIM-OFFSET  1 kΩ, 25-turn cermet, 3-terminal │
  (2.500 V) │       └───┬──────────────────────────────────┬───────┘
            │       wiper                                  │
            │           │                                  │
            │           ├──[R-TRIM-BLEED 1 MΩ]─────────────┤
            │           │                                  │
            │           ├──[C-REF-TRIM 100 nF]── AGND_MOD  │
            │           │                                  │
            │           └──[R-OPAMP-IN 1 kΩ]──┐    [R-TRIM-B 24.3 kΩ 0.1% 10 ppm]
            │                                 │            │
            │                          ┌──────┴──────┐  AGND_MOD
            │                          │ +           │
            │                          │  ½ OPA2197  ├──┬── V_REF_BUF ≈ 2.500 V
            │                          │ −           │  │   → LT5400 R1 bottom
            │                          └──────┬──────┘  │
            │                                 │         │
            │            AGND_MOD ──[R-TRIM-G 10.0 kΩ]──┤
            │                                 │         │
            │                                 └──[R-TRIM-F 200 Ω]──┘
            │                                        G = 1.0200
```

| Ref | Value | Part class |
|---|---|---|
| `TRIM-OFFSET` | **1 kΩ**, 25-turn cermet, **3-terminal** | was 10 kΩ |
| `R-TRIM-B` | **24.3 kΩ** ±0.1 %, ±10 ppm/K | ERA-6ARB2432C `[datasheet ERA-A p.1]` |
| `R-TRIM-F` | **200 Ω** ±0.1 %, ±10 ppm/K | ERA-6ARB2000C |
| `R-TRIM-G` | **10.0 kΩ** ±0.1 %, ±10 ppm/K | ERA-6ARB1002C |
| `R-TRIM-BLEED` | **1 MΩ** 1 % 0805 | ordinary thick film |
| `C-REF-TRIM` | **100 nF** X7R 0805 | new |

`[datasheet ERA-A p.1]` size/TCR codes read off the ordering table: **3A = 0603
0.1 W, 6A = 0805 0.125 W, 8A = 1206 0.25 W**; TCR `R` = ±10×10⁻⁶/K, `P` = ±15,
`E` = ±25, `H` = ±50, `K` = ±100. **`bom.csv` gives `R-TRIM-RANGE` the package
`0805`, which is ERA-*6*A, not the ERA-3A that is banked.** Specify 6A.

### 1.5 The arithmetic

`[calc]` Centre division, wiper at half travel:

```
D = (R_B + R_P/2) / (R_P + R_B) = (24 300 + 500) / 25 300 = 0.980237
G = 1 + R_F/R_G = 1 + 200/10 000 = 1.020000
V_ref(centre) = 2.500 × 0.980237 × 1.020000 = 2.49960 V
```

Centre error **−0.40 mV = −0.48 cents**, against ±50 mV of authority: 125×
margin, so the 0.1 % parts never run the trimmer out of range.

`[calc]` Authority:

```
ΔV_wiper(full travel) = 2.500 × R_P/(R_P+R_B) = 2.500 × 1000/25 300 = 98.81 mV
ΔV_ref               = 98.81 mV × 1.0200      = 100.8 mV span  =  ±50.4 mV
                                              =  ±60.5 cents of intercept
```

Matches `bom.csv`'s stated intent for the part ("~±50 mV… ~60 cents") — which
until now had no network behind it.

`[calc]` Resolution on a 25-turn pot: 100.8 mV / 25 = **4.03 mV/turn =
4.84 cents/turn**. A comfortable screwdriver.

`[calc]` Load on `VREFOUT`: `2.500 / 25 300 = 98.8 µA`, **independent of wiper
position**. Against ±20 mA capability and 30 µV/mA `[datasheet SBAS430E p.4]`
→ **2.96 µV** of static reference droop, and **zero movement while trimming** —
the property ADR 0006 wanted and did not get.

`[calc]` Tempco, worst case, per °C:

```
divider    : p(α_pot − α_B)          = 0.0198 × (100 − 10)  = 1.78 ppm/°C
gain-back  : (x/(1+x))(α_F − α_G)    = 0.0196 × 20          = 0.39 ppm/°C
                                                    total   ≈ 2.2 ppm/°C
over 10 °C : 22 ppm × 2.500 V = 55 µV of V_ref = intercept  = 0.066 cents
```

**The design is robust to the one figure I cannot bank.** The corpus disagrees
with itself about cermet tempco — ADR 0006's own trimmer table is built on
**250 ppm/°C** `[calc: 0.95×10 + 0.05×250 = 22, 0.9×10+0.1×250 = 34,
0.8×10+0.2×250 = 58, reproducing its three rows exactly]`, while
`pitch-stage.md:289` and `bom.csv` TRIM-GAIN use **~100 ppm/°C** `[from
memory]`. No trimmer datasheet is banked. At 250 ppm/°C this term is
**0.133 cents** instead of 0.066 — still small, because the 2 % perturbation
attenuates it 50:1. **The disagreement does not need resolving to build this;
it did need resolving for the 200 Ω in the gain ratio, which is one more reason
that part goes (§3).**

### 1.6 Fail-open

A 3-terminal pot **cannot** take the page's "strap the wiper to one end" remedy
— that shorts out part of the track and destroys the divider. `R-TRIM-BLEED`
1 MΩ from the wiper node to the pot's ground-side terminal does the equivalent
job:

- **Wiper open** → the buffer's (+) input is pulled to the bottom-of-pot
  potential: `V_ref = 2.500 × (24 300/25 300) × 1.0200 = 2.4492 V` `[calc]`,
  i.e. **51 mV low = 61 cents flat**. The instrument still plays. Not a rail.
- **Loading cost while healthy** `[calc]`: the bleed sees
  `V_wiper − V_bottom = 2.500 × 500/25 300 = 49.4 mV` → 49.4 nA, into a wiper
  source impedance of `R_P/4 = 250 Ω` at mid-travel → **12 µV = 0.015 cents**.

`C-REF-TRIM` 100 nF gives the tap a **1.27 kHz** corner `[calc: R_wiper 250 Ω +
R-OPAMP-IN 1 kΩ; 1/(2π·1250·100n) = 1.27 kHz]`, which is the missing piece of
the `VREFOUT` argument: ADR 0006 moved the offset reference off the ±12 V rail
to escape ~22 cents of LED-correlated FM, and then left the new reference tap as
a bare 25 kΩ node with no shunt at all.

---

## 2. The exposed pad — what it actually does, and where it goes

### 2.1 Confirmations

`[datasheet 5400fa p.2]` "MS8E PACKAGE / 8-LEAD PLASTIC MSOP / **EXPOSED PAD
(PIN 9) IS FLOATING**", θJA 40 °C/W, θJC 10 °C/W.

`[datasheet 5400fa p.8]` package drawing, "8-Lead Plastic MSOP, Exposed Die
Pad": **`1.68 ± 0.102` × `1.88 ± 0.102` mm**, with "EXPOSED PAD DIMENSION DOES
NOT INCLUDE MOLD FLASH" and a RECOMMENDED SOLDER PAD LAYOUT on the same page.
**The 1.88 × 1.68 figure the corpus carries from a KiCad footprint name is now
datasheet-sourced.**

`[datasheet 5400fa p.4]` Distributed Capacitance: **Resistor to Exposed Pad
5.5 pF; Resistor to Resistor 1.4 pF.**

`[datasheet 5400fa p.6, "Where to Connect the Exposed Pad"]` verbatim: "The
exposed pad is not DC connected to any resistor terminal… The exposed pad can be
tied to any voltage (such as ground) as long as the absolute maximum ratings are
observed… To avoid interference, **do not tie the exposed pad to noisy signals
or noisy grounds.** Connecting the exposed pad to a quiet AC ground is
recommended as it **acts as an AC shield and reduces the amount of
resistor-resistor capacitance.**"

`[datasheet 5400fa p.4, Note 2]` the ±80 V Total Voltage abs-max explicitly
includes "the voltage across any pin **with respect to the exposed pad of the
package**". **The pad is a rated node, not a mechanical feature.**

### 2.2 The DC answer, which is the one the budget needs

**The pad contributes exactly zero to the 1 V/oct transfer function at DC,
whatever it is tied to, because it is not DC-connected to any resistor
terminal** `[datasheet 5400fa p.6]`. It does not appear in §4's budget. Anyone
worried it might is worrying about the wrong thing; the hazard is entirely AC.

### 2.3 The AC answer, quantified

`[calc]` Model the distributed 5.5 pF per resistor as a π-network: **2.75 pF
from each resistor end to the pad.** For the two active sections that puts
**5.5 pF from the (−) summing node to the pad**, 2.75 pF from `V_REF_BUF` to
the pad, and 2.75 pF from the jack node to the pad.

**Pad tied to a quiet AC ground — the recommended case.**

`[calc]` The summing-node capacitance rises to
`5.5 (pad) + 6.4 (OPA2197 Z_IC) + 1.6 (Z_ID) + ~2 (layout) ≈ 15.5 pF`
`[datasheet SBOS737C p.7 for the two op-amp figures]`. On its own that would put
a noise-gain zero at `1/(2π · R1‖R2 · C_n) = 1/(2π · 5000 · 15.5p) =` **2.05 MHz**,
uncomfortably inside a 10 MHz GBW.

**It never develops.** `C-FB-PITCH` 2.2 nF ties the same node to the op-amp
output, and `2.2 nF / 15.5 pF = 142`. Above the 14.5 kHz handover the node
follows the output and the 15.5 pF sees no differential voltage. **The pad
capacitance at the summing node is swamped 142:1 and cannot destabilise this
loop.** The other two 2.75 pF terms land on an op-amp output (363× below the
OPA2197's 1 nF drive limit `[datasheet SBOS737C p.1 Features, §7.3.5 p.22]`) and
in parallel with `C-FILT-PITCH` 10 nF (a 0.0275 % addition).

**Pad left floating — what happens if the layout ignores it.**

`[calc]` The pad becomes a floating node common to all four sections.
Jack → pad → summing node is `2.75 pF` in series with `2.75 pF` = **1.375 pF**,
in parallel with the direct 1.4 pF, so **a floating pad roughly doubles the
stray from the jack to the summing node, 1.4 → 2.78 pF.** As feedback that is a
*lead* (zero at `1/(2π·10k·2.78p)` = 5.7 MHz) and harmless. **The hazard is not
stability, it is that a floating pad opens a direct capacitive path from an
external connector with 2 m of patch cable on it into a precision summing node,
bypassing `R-OUT-PROT` and `C-FILT-PITCH` entirely.** At 100 MHz, 2.78 pF is
573 Ω. This is an RF-rectification path, and RF rectification is a DC error.

**Pad tied to a noisy node — the case the datasheet forbids, priced.**

`[calc]` Below the `C-FB-PITCH` handover, a pad voltage `V_n` injects
`V_n·jωC_pad` into the summing node, which the loop must sink through R2:

```
error at op-amp output = V_n · 2π f · 5.5 pF · 10 kΩ
  at 1 kHz  : 3.46e-4 → 0.42 cents per volt of pad noise
  at 10 kHz : 3.46e-3 → 4.2  cents per volt
```

Above the handover it flattens at `C_pad/C_fb = 5.5p/2.2n = 2.5e-3` (−52 dB).
So 100 mV of pour noise at 10 kHz is **0.42 cents** — the same order as the
entire static budget, injected past every filter in the chain.

### 2.4 Decision

**Pin 9 → `AGND_MOD`**, the module analog-return region, stitched to the pour
local to the pitch stage and joining the ADR 0004 star point with the rest of
that region.

That region is a quiet AC ground **by construction, not by hope**:
`[repo docs/decisions/0004-cv-interface-module.md:600–630]` `PWR_GND` (~360 mA
of instrument current) and `DIG_GND` each run to the star on their own copper,
touching no other return — which is the entire mechanism behind the 5.7–7.2 cent
ground term. **The pad's requirement and the grounding plan's requirement are
the same requirement**; if the star rule is followed the pad has a quiet ground
to sit on, and if it is not, the pad is not the reason the stage is broken.

**Forbidden, explicitly, on the drawing:**

| Net | Why not |
|---|---|
| *floating* | doubles jack→summing-node stray; opens an unshielded RF path from the connector; leaves pin 9 at an undefined potential against the p.4 Note 2 abs-max |
| `+12V_A` / `−12V_A` | rails; and `V_jack(pin) − V_pad` reaches 24 V against 80 V for no benefit |
| `PWR_GND`, `DIG_GND` | the two nets ADR 0004 names as the dirtiest on the board |
| umbilical `AGND` | **not a ground** — it is the in-amp's sense conductor (§6) |
| `V_REF_BUF`, jack, summing node | turns a shield into a feedforward capacitor |

**Abs-max check** `[calc, datasheet 5400fa p.4 Note 2]`: with the pad at
`AGND_MOD`, the largest pin-to-pad voltage is the jack node driven to ±12 V by a
neighbouring module through a patch cable. **12 V against an 80 V rating —
6.7× margin.** Not binding, but it is now checked rather than assumed.

### 2.5 The LT5400's ESD exposure — already solved, by a part bought for something else

`[datasheet 5400fa p.6]` "The LT5400 can withstand up to ±1 kV of electrostatic
discharge (ESD, human body). To achieve the highest precision matching, the
LT5400 is designed **without explicit ESD internal protection diodes.**" Figure 1
names a **BAV99** to the supply rails for the "EXTERNAL CONNECTOR" case.

**Pitch taps DC feedback at the jack, so the LT5400's R2 pin *is* the external
connector case** — and `D-JACK-CLAMP` does **not** protect it: `[repo bom.csv
D-JACK-CLAMP]` that BAV99 was deliberately moved to the **driver side** of
`R-OUT-PROT` to stop 42 mA/jack of back-powering. The R2 tap is on the jack
side, outside the clamp. The page flagged this ("check the clamp actually stands
between the jack and every LT5400 pin"). **It does not.**

**It does not need to.** `[calc]` `C-FILT-PITCH` 10 nF sits directly on the jack
node. An IEC 61000-4-2 8 kV contact discharge is 150 pF through 330 Ω; charge
sharing into 10 nF gives `8000 × 150/(150+10 000) = 118 V` at the node — **8.5×
below the LT5400's own ±1 kV HBM rating**, before `R2`'s 10 kΩ is counted. A
second clamp would reintroduce the back-powering the BOM row exists to prevent,
and buys nothing.

**This converts `C-FILT-PITCH` from a nice-to-have into a protection part**, and
it carries a hard layout constraint: the order on the copper must be
**`J-CV` tip → `C-FILT-PITCH` → `R2` tap → `R-OUT-PROT`**, with the cap
physically closest to the connector. If `R2` taps ahead of the cap, the argument
above is void.

### 2.6 The two spare sections

`[datasheet 5400fa p.2]` the `-1` option is four equal 10 kΩ sections: die R1 on
pins 1–8, R2 on 2–7, R3 on 3–6, R4 on 4–5, and the option table pairs them
"R2 = R3" and "R1 = R4". `[datasheet 5400fa p.4]` matching is specified "Any
Resistor to Any Other Resistor", so any pair is legal.

**Assignment:** die **R2 (pins 2–7)** and **R3 (pins 3–6)** carry the 1 V/oct
network, with the **summing node on pins 2 and 3** (adjacent — shortest trace,
least stray to anything else), `V_REF_BUF` on pin 7 and the jack on pin 6.
**Die R1 (pins 1, 8) and R4 (pins 4, 5) tie all four pins to `AGND_MOD`.**

Three things that buys, at zero cost:

1. Every pin has a defined potential, satisfying the p.4 Note 2 abs-max cleanly.
2. The 1.4 pF resistor-to-resistor coupling from the active pair now terminates
   on ground instead of on a floating node.
3. Pin 5 (grounded) becomes the jack pin's neighbour on one side; its only
   non-ground neighbour is pin 7, which is a buffer-driven low-impedance node.

**What I considered and rejected: paralleling the spares into the network**
(R1‖R4 and R2‖R3, keeping the ratio exactly 1:1 and improving the match by ~√2).
`[calc]` It halves the network to 5 kΩ, which moves the `C-FB-PITCH` handover
from 14.5 kHz to 29 kHz and raises the ringing `Q` by √2 — taking the existing
10 nF jack cap from `Q = 0.70` (flat) to `Q = 0.99` (overshoot). Recovering it
needs `C-FB-PITCH` at 4.7 nF, i.e. changing a `settled` figure
(`pitch-compensation`) to buy 0.005 cents. **Not worth it.**

---

## 3. `TRIM-GAIN` — delete it

### 3.1 Every reason for it has been withdrawn, by the documents that gave them

| Original reason | Status |
|---|---|
| "The gain ratio was not buildable" (9/5 from a matched quad) | **Retracted by ADR 0006 itself** — the stage is an exact 1:1 |
| "Firmware calibration has no offset authority" | **Retracted by ADR 0006 itself** when the per-load affine model went in |
| "±5 % absorbs the load divider" | **Gone with the divider** when feedback moved to the jack |
| "Every commercial 1 V/oct module has scale and offset trimmers" | **False, and ADR 0006 says so**: two surveys found *zero* trimmers on DAC-derived CV outputs across eight designs |

### 3.2 And it is actively harmful

`[repo hardware/module/pitch-stage.md:130]` It is one-sided, 0 → +2 %, with
nominal dead on 2.000 — **no downward authority at all.**

`[datasheet 5400fa p.4]` Absolute tolerance is **±7.5 % (A) / ±15 % (B)**, so
the real authority is `200/10 750 = 1.86 %` to `200/9 250 = 2.16 %` `[calc]` —
still entirely one-sided.

`[calc]` It puts a cermet inside the ratio the LT5400 was bought to protect:

```
f = 200/10 200 = 0.0196
ratio drift = (1−f)·(LT5400 tracking) + f·(α_cermet − α_LT5400,abs)
            = 0.98 × 1 + 0.0196 × (100 − 8)  = 2.78 ppm/°C   at 100 ppm/°C
            = 0.98 × 1 + 0.0196 × (250 − 8)  = 5.72 ppm/°C   at 250 ppm/°C
→ over 10 °C × 2.25 V lever × 1.2 cents/mV  = 0.075 / 0.154 cents
```

against **0.027 cents** for the bare network. It costs **2.8× to 5.7× the
network's own drift**, for a range that points the wrong way. ADR 0006 wrote the
charge against it in its own words — "any external resistor added to reach it
puts its absolute tempco inside the ratio, exactly the failure the matched
network was bought to prevent" — and then kept the part.

### 3.3 What firmware already has

`[repo docs/decisions/0006-cv-channel-allocation.md:476]` an 11-point-per-octave
correction table, plus the per-load affine model. A gain correction in firmware
costs DAC code, and the window is 0.25–4.75 V out of 0–5 V — **10 % of headroom
at each end** `[repo ADR 0006]`. The residual gain error it must absorb is
`[datasheet SBAS430E p.3]` ±0.15 % of FSR max (DAC gain error) plus
`[datasheet 5400fa p.4]` ±0.010 % (LT5400 A-grade matching). **0.16 % against
10 % of headroom: 62× margin.**

### 3.4 Decision

**Delete `TRIM-GAIN`. Fit a 0 Ω 0805 link in its place and keep the land
pattern** so E9 can substitute a trimmer if the bench contradicts this.

Consequences, all of which must follow into the page and BOM:

- The fourth open item — "a two-terminal series trimmer fails open to the rail"
  — **disappears with the part.** It was only ever about this trimmer;
  `TRIM-OFFSET` is 3-terminal and is handled in §1.6.
- `[calc]` Nominal gain becomes **2.000000**, not the 2.020000 the page states.
  **`pitch-stage.md:263`'s "the exact DC solve gives gain 2.020000 for every
  load" is that trimmer at full travel and must change.**
- `[calc]` The LT5400's voltage coefficient term goes to **identically zero**.
  In a 1:1 non-inverting stage with the reference at the bottom of the divider,
  R1 and R2 always carry the same voltage — at the jack extremes,
  `V_R2 = 7.000 − 4.750 = 2.250 V` and `V_R1 = 4.750 − 2.500 = 2.250 V`; at the
  other end both are −2.250 V. The `<0.1 ppm/V` coefficient
  `[datasheet 5400fa p.4]` cancels exactly. **The 200 Ω broke that cancellation
  by 44 mV.** A structural property nobody had noticed, restored by a deletion.
- The calibration procedure's step 1 keeps its structure but moves to firmware.
  Step 2 (offset, at the lowest note) stays a screwdriver. The page's convergence
  argument survives unchanged, and improves: with the gain trim gone, the trims
  no longer interact **at all**.

---

## 4. `R-BIAS-DAC` — right place, wrong value

### 4.1 The position is right and now sourced

`[repo bom.csv R-BIAS-DAC]` "AT THE DAC PIN, not after `R-OPAMP-IN` — 100 k
after the 1 k would form a divider and cost 1 % of gain." `[calc]` Confirmed:
`1 − 100k/(100k+1k) = 0.99 %`. The position argument is correct.

### 4.2 The value was never derived, and it costs 0.46 cents

`[datasheet SBAS430E p.3]` the DAC8568's **DC output impedance is 4 Ω at
mid-code**. `R-BIAS-DAC` sits directly across it.

`[calc]` `100 kΩ` in parallel with a 4 Ω source is a **−40 ppm gain error**:

```
V_dac(actual)/V_dac(ideal) = 100 000/(100 000 + 4) = 0.99996
at V_dac = 4.75 V : −190 µV at the DAC → −380 µV at the jack → −0.456 cents
```

**0.46 cents, larger than every term in the page's own budget except the
reference.** It is a fixed gain error and calibration removes it — but it is also
a **drift** term: the 4 Ω and the 100 kΩ both move with temperature, and ~20 %
of 40 ppm over 10 °C is 8 ppm → 0.09 cents `[calc]`, which is on the same order
as everything else left in the budget.

### 4.3 What actually constrains the value

The resistor's only job is to hold the op-amp's (+) input at a defined DC
potential in the window before power-on reset, when the DAC pin may be high-Z.
`[repo bom.csv R-BIAS-DAC]`

`[datasheet SBOS737C p.7]` the op-amp's input bias current is **±5 pA typ /
±20 pA max at 25 °C, and ±5 nA max over −40 °C to +125 °C** (the ±15 nA figure
is "PW package only" — TSSOP — and **does not apply**; `U-OPA-PITCH` is SOIC-8).

`[calc]` So at 1 MΩ the held node sits within `5 nA × 1 MΩ = 5 mV` of ground at
the absolute temperature extreme, and within ~60 µV at 40 °C. **During that
window the output only needs to be *defined*, not accurate**, so 5 mV is ample.

**Nothing in the requirement calls for 100 kΩ.** And critically: while the DAC
is active, its 4 Ω swamps the bias resistor, so the op-amp's own bias current
flows into 4 Ω, not into `R-BIAS-DAC` — the value has **no** bearing on
normal-operation offset.

### 4.4 Decision

**`R-BIAS-DAC` = 1 MΩ 1 % 0805, at each DAC output pin (qty 6).**

| Value | Gain error | In cents | High-Z hold at 40 °C |
|---|---|---|---|
| 100 kΩ (current) | −40 ppm | **−0.456** | 6 µV |
| **1 MΩ (proposed)** | **−4 ppm** | **−0.046** | 60 µV |
| 10 MΩ | −0.4 ppm | −0.005 | 600 µV |

1 MΩ is the knee, and it matches `R-BIAS-INAMP` (already 1 MΩ in this BOM),
which is the same fix on the same class of node. `[calc]` Interaction with
`C-AA-PITCH`: with the DAC high-Z the 10 nF discharges through
`1 kΩ + 1 MΩ`, τ = 10 ms — irrelevant against a power-up sequence.

---

## 5. Re-checking every `[from memory]` and `[calc]` on the page

### 5.1 ⚠ STALE — the shelf's pole and zero did not follow `C-FB-PITCH` to 2.2 nF

`[repo hardware/module/pitch-stage.md:185–192]` states, for
`G(s) = 1 + (R2/R1)/(1 + sR2C)`: "**Pole at 15.9 kHz, zero one octave above at
31.8 kHz.**"

`[calc]` Those are the **1 nF** numbers: `1/(2π·10k·1n) = 15.92 kHz`,
`2/(2π·10k·1n) = 31.83 kHz`. At the current **2.2 nF**:

```
pole = 1/(2π · 10 kΩ · 2.2 nF) =  7.23 kHz
zero = 2/(2π · 10 kΩ · 2.2 nF) = 14.47 kHz
```

**Both figures are wrong by 2.2×.** This is the exact defect CLAUDE.md is
written about — and it is **in the same section that catches the other
instance**: line 179 says "This row said 1 nF / ~16 kHz until 2026-09-21; the
value went to 2.2 nF and this row did not follow." One instance was fixed, the
other, eight lines below, was not.

The conclusion that survives untouched: **max attenuation 6.02 dB for any
capacitor value** `[calc: 20·log₁₀(2) = 6.021 dB]`. It is a shelf, not a pole.

`[calc]` The corrected 14.5 kHz handover is also the number §2.3 needs, and it
is the frequency above which the pad capacitance is swamped.

### 5.2 ⚠ WRONG — "less two Schottky drops"

`[repo hardware/module/pitch-stage.md:154]` "An OPA2197 on ±12 V less two
Schottky drops reaches ~±11.45 V."

**One Schottky per rail, not two.** `[repo docs/decisions/0004-cv-interface-module.md:~300]`
the power tree puts one `1N5817` in the module's analog +12 V, one in the
umbilical +12 V (a *parallel* branch, not in series), and one in −12 V.
`[repo bom.csv D-REVPOL]` qty 3, "THREE not two: the module's analog +12V and
the umbilical feed must NOT share a diode."

And the page omits the op-amp's own swing limit. `[datasheet SBOS737C p.8]`
`V_O` from rail: **95 typ / 125 max mV at R_L = 10 kΩ; 430 typ / 500 max mV at
R_L = 2 kΩ**.

`[calc]` Corrected worst case:

```
bus +12 V at −5 %                       = 11.40 V
less 1N5817 V_f at ~25 mA (~0.25 V)     = 11.15 V     [repo figures.yaml diode-split-rationale, 0.24 V at 245 mA]
less OPA2197 swing-from-rail (light)    = 11.03 V
less OPA2197 swing-from-rail (2 kΩ)     = 10.65 V
```

The **conclusion survives** — the ±600-cent reserve needs +7.500 V at the jack
plus 275 µA of feedback current through `R-OUT-PROT`, i.e. **7.775 V**, leaving
3.25 V of headroom `[calc]` — but the stated number is arrived at wrongly.

### 5.3 ✅ CONFIRMED — the ringing formula and both overshoot figures

`[repo hardware/module/pitch-stage.md:268–271]` `Q = √(R_eff·C_load / R2·C_fb)`,
"safe to about 10 nF… 44–67 % overshoot" into MOD (82 nF) or BREATH (330 nF).

`[calc]` with `R_eff` = `R-OUT-PROT` 1 kΩ, `R2` = 10 kΩ, `C_fb` = 2.2 nF, and
overshoot `= exp(−πζ/√(1−ζ²))`, `ζ = 1/2Q`:

| `C_load` | Q | ζ | overshoot |
|---|---|---|---|
| 10 nF (`C-FILT-PITCH` alone) | 0.674 | 0.742 | 0 % (flat) |
| 10.8 nF (+ 2 m of cable, 800 pF) | 0.700 | 0.714 | 0 % — **maximally flat** |
| **11.0 nF** | **0.707** | 0.707 | **the Butterworth limit** |
| 92 nF (+ `C-FILT-MOD` 82 nF) | 2.045 | 0.244 | **45.5 %** |
| 340 nF (+ `C-OUT-BREATH` 330 nF) | 3.929 | 0.127 | **67.0 %** |

`[repo bom.csv C-FILT-MOD, C-OUT-BREATH]` confirms 82 nF and 330 nF.
**The page's "44–67 %" and "safe to about 10 nF" are both right** — and
`[calc]` the maximally-flat limit is exactly `C_load = R2·C_fb/(2·R_eff) =
11.0 nF`, which means **`C-FILT-PITCH`'s own 10 nF already spends 91 % of the
budget.** The 2.2 nF was chosen to land the 10 nF + 2 m of cable on Butterworth,
which is precisely what the page claims and is now verified.

### 5.4 ⚠ STALE ELSEWHERE — ADR 0006's precision table has a 4× pivot error, in three rows

The page correctly identifies the pivot: `∂Vout/∂k = Vdac − V_ref`, max lever
**2.25 V** for a ratio drift; `∂Vout/∂δ = Vout`, max lever **7.00 V** for a
reference drift. `[repo hardware/module/pitch-stage.md:280–283]`

`[repo docs/decisions/0006-cv-channel-allocation.md:~360]` ADR 0006's table
still uses a **9 V** lever throughout:

| ADR 0006 row | Its figure | Correct `[calc]` | Ratio |
|---|---|---|---|
| DAC internal reference, 5 ppm/°C | 0.54 cents | **0.42** (50 ppm × 7.000 V × 1.2) | 1.3× |
| Discretes, 25 ppm/°C each, opposing | 5.40 cents | **1.35** (500 ppm × 2.250 V × 1.2) | 4.0× |
| Matched network, 1 ppm/°C | 0.11 cents | **0.027** (10 ppm × 2.250 V × 1.2) | 4.0× |

The page's own "Three documents used 9 V, 7 V and 2.5 V for the same term" is
right, and **the 9 V one is still live in the ADR.** Its *conclusion* —
"resistor tracking dominates reference drift by roughly ten to one" — **does not
survive**: on the correct levers it is `1.35 / 0.42 = 3.2×`, not 10×, and
against the LT5400 the reference is **15× larger**, which is what the page
already says two sections later.

`[calc]` The page's own "two 0.1 % / 10 ppm discretes would give 0.38 cents" is
an **RSS** of two 10 ppm/°C parts (`10√2 = 14.1 ppm/°C → 141 ppm × 2.25 V ×
1.2 = 0.38`). The worst case (opposing) is **0.54 cents**. Both are defensible;
the page should say which it means.

### 5.5 ⚠ ADR 0006's INL figures are 11 % low

`[repo docs/decisions/0006-cv-channel-allocation.md:476]` "±4 LSB typical is
0.66 cents, ±12 LSB is 2.0 cents."

`[calc]` An LSB is `FSR/65536`, and `[datasheet SBAS430E p.3]` for a C-grade
part FSR = **5.000 V**, not the 4.5 V usable window:

```
1 LSB = 5.000/65536 = 76.294 µV at the DAC = 152.59 µV at the jack = 0.1831 cents
±4  LSB = 0.732 cents    (ADR says 0.66)
±12 LSB = 2.197 cents    (ADR says 2.0)
```

The ADR's numbers come from dividing the 4.5 V window by 65536, which is not
what an LSB is.

### 5.6 ✅ CONFIRMED

| Claim | Verdict |
|---|---|
| Slope `9/4.5 = 2.000`, intercept `−2 − 2(0.25) = −2.500 V` | ✅ `[calc]` |
| "Offset 1 mV = 1.2 cents at both ends; gain 100 ppm = 0.24 at −2 V, 0.84 at +7 V" | ✅ `[calc: 100e-6 × 2000 mV × 1.2 = 0.24; × 7000 × 1.2 = 0.84]` |
| "LT5400 ratio tracking 0.027 cents / 10 °C" | ✅ `[datasheet 5400fa p.4: ±0.2 typ, ±1 max ppm/°C]` + `[calc: 10 ppm × 2.25 V × 1.2]` |
| "DAC internal reference 0.42 cents / 10 °C" | ✅ `[datasheet SBAS430E p.4: C/D grade 2 typ / 5 max ppm/°C]` + `[calc: 50 ppm × 7.000 V × 1.2]` |
| "OPA2197 offset drift < 0.1 cents" | ✅ **0.060** `[datasheet SBOS737C p.7: ±0.5 typ / ±2.5 max µV/°C]` × noise gain 2 × 10 °C × 1.2 |
| "The deleted 10 nF gave −16 dB at 100 kHz and −36 dB at 1 MHz" | ✅ `[calc: 1 kΩ·10 nF = 15.92 kHz; 1/√(1+(100/15.92)²) = −16.1 dB; 1/√(1+(1000/15.92)²) = −36.0 dB]` |
| "−41 dB at 1 MHz with the shelf" | ✅ `[calc: 6.02 + 36.0 = 42.0 dB]`, 1 dB of rounding |
| "`R-OPAMP-IN` contributes no gain error at all" | ✅ with a number: `[datasheet SBOS737C p.7]` I_B ±20 pA max at 25 °C → **20 nV**; bounded at **0.012 cents** even at the ±5 nA full-temperature max. The blanket "draws no current" is now sourced |
| "Power-on is 0.000 V, not subsonic" | ✅ `[datasheet SBAS430E, via bom.csv U-DAC, verbatim]` grades A/C power up at zero scale, and the internal reference defaults OFF after any power cycle in **both** Static and Flexible modes — so both terms are zero |
| "the reference-enable must be firmware's first DAC write" | ✅ `[repo firmware/README.md:72]` "that firmware writes once: the internal-reference enable, and the clear-code" + sticky-register refresh at :77 |
| LT5400 option table, grades, absolute tolerance, ESD, pad coupling | ✅ all verbatim `[datasheet 5400fa pp.2, 4, 6]`; and **the 1.88 × 1.68 mm pad is now datasheet-sourced at p.8**, not footprint-name-sourced |

### 5.7 The `Zo` = 375 Ω correction does not reach this page

`[repo config/figures.yaml opa2197-output-impedance]` warns that every pole
derived from the back-solved 75.8 Ω moves ~5× the wrong way.

**Checked: no pole on the pitch page is derived from `Zo`.** The 14.5 kHz
handover is `R1‖R2 · C_fb`; the 15.9 kHz jack corner is `R-OUT-PROT · C-FILT`;
the 15.9 kHz anti-alias corner is `R-OPAMP-IN · C-AA`. All are set by explicit
resistors. **The pitch stage is unaffected by that correction** — it lands on
the `R-ISO-REF` compensation in `carrier.md`, not here.

One consequence *does* reach here, and it is favourable: `[datasheet SBOS737C
p.8 and Figure 26]` `Zo` is 375 Ω from 100 Hz to 300 kHz, so the op-amp's own
output impedance is **375 Ω inside a 1 kΩ `R-OUT-PROT`** — a 27 % addition to
the effective series resistance above the loop's reach. `[calc]` Against
`C-FILT-PITCH` that moves the far-out-of-band corner from 15.9 kHz to
`1/(2π·1375·10n) = 11.6 kHz`, which only matters above the handover where the
loop is not correcting it. Worth putting in the SPICE deck; not worth a change.

---

## 6. `pitch-cents-budget` — one table, settled

### 6.1 Why the four candidates disagreed

`[repo config/figures.yaml pitch-cents-budget]` lists 0.42, 0.85 RSS, 1.35
linear, and "~1.2 RSS over 0–40 °C". **They are the same budget at four
different scopes**, which is why no reviewer could settle it by argument:

- **0.42** is one *row* — the DAC reference over 10 °C. `[repo]` `power-entry.md`
  scaled the ground-path finding against it; **that row is unchanged below**, so
  its citation survives.
- **0.85** ≈ the 10 °C thermal RSS combined with **raw** ±4 LSB INL
  `[calc: √(0.42²+0.12²+0.27²+0.66²) = 0.836]` — which double-counts the
  curvature firmware's 11-point table removes.
- **1.35** ≈ the **linear sum** of the same terms.
- **~1.2 over 0–40 °C** is the same RSS over a **25 °C** span instead of 10 °C.
  `[calc]` That reviewer was right; they were just using a different Δ**T**.

**So the table must state its scope, its combination rule, and its calibration
assumption on its face.** All three were missing.

### 6.2 Conversions used throughout

```
[calc]  1 mV at the jack                      = 1.2 cents
        1 LSB (16-bit, FSR = 5.000 V)         = 76.294 µV at DAC
                                              = 152.59 µV at jack = 0.1831 cents
        gain-type fraction g                  = g × 7.000 V × 1.2  = g × 8400 cents
        ratio-type (k) fraction r             = r × 2.250 V × 1.2  = r × 2700 cents
        DAC-referred offset ΔV                = ΔV × 2 × 1.2       = 2.4 cents/mV
        op-amp input-referred offset ΔV       = ΔV × 2 × 1.2       = 2.4 cents/mV
```

### 6.3 THERMAL, per 10 °C — with `TRIM-GAIN` deleted and `R-BIAS-DAC` at 1 MΩ

| Term | Source | Arithmetic | cents |
|---|---|---|---|
| **DAC internal reference tempco**, C grade, 5 ppm/°C max | `[datasheet SBAS430E p.4]` | 50 ppm × 7.000 V × 1.2 | **0.420** |
| **DAC gain tempco**, ±1 ppm of FSR/°C | `[datasheet SBAS430E p.3]` | 10 ppm × 5.000 V = 50 µV at DAC → 100 µV | **0.120** |
| `TRIM-OFFSET` network (`G·D` product) | `[calc §1.5]` | 2.2 ppm/°C → 22 ppm × 2.500 V = 55 µV, offset | **0.066** |
| **OPA2197 V_os drift**, pitch amp, ±2.5 µV/°C max | `[datasheet SBOS737C p.7]` | 25 µV × NG 2 = 50 µV | **0.060** |
| **DAC zero-code error drift**, ±2 µV/°C | `[datasheet SBAS430E p.3]` | 20 µV × 2 = 40 µV | **0.048** |
| **OPA2197 V_os drift**, reference buffer | `[datasheet SBOS737C p.7]` | 25 µV × G 1.02 = 25.5 µV on V_ref → intercept | **0.031** |
| **LT5400 ratio tracking**, ±1 ppm/°C max | `[datasheet 5400fa p.4]` | 10 ppm × 2.250 V | **0.027** |
| `R-BIAS-DAC` loading drift, 1 MΩ | `[calc §4.4]` | ~0.08 ppm × 7.000 V | **0.001** |
| **OPA2197 I_B imbalance** at 40 °C | `[datasheet SBOS737C p.7]` + `[calc §7.3]` | ~60 pA × 8 kΩ = 0.5 µV | **0.001** |
| **LT5400 voltage coefficient** | `[datasheet 5400fa p.4]` + `[calc §3.4]` | cancels by topology | **0.000** |
| | | **RSS** | **0.450** |
| | | **linear sum** | **0.773** |

`[calc]` RSS: `√(0.420²+0.120²+0.066²+0.060²+0.048²+0.031²+0.027²) = √0.20264 = 0.4501`.

*Note the refinement the page can claim and does not:* `[datasheet SBAS430E p.8,
Figure 6]` characterises grades C/D over **0 °C to +125 °C** at **1.2 typ /
3 max ppm/°C**, against the EC table's 2/5 over −40/+125. A rack never goes
below 0 °C. The **guaranteed** number is 5 ppm/°C and the table above uses it;
3 ppm/°C would take this row to **0.252 cents** and the RSS to **0.30**.
Recorded, not claimed.

### 6.4 NON-THERMAL, after gain-and-offset calibration

| Term | Source | cents |
|---|---|---|
| **DAC reference thermal hysteresis**, 25 ppm additional cycles | `[datasheet SBAS430E p.4]` | **0.210** *per power cycle* |
| **DAC DNL**, ±1 LSB max, 16-bit monotonic | `[datasheet SBAS430E p.3]` | **0.183** |
| **DAC INL residual** after an 11-point/octave table | `[calc, assumption]` — the table removes the fitted curve; residual is inter-point curvature, taken as ~40 % of the ±4 LSB typical | **~0.300** |
| **LT5400 long-term matching drift**, <2 ppm / 2000 h at 35 °C | `[datasheet 5400fa p.4]` | **0.005** |
| *first-cycle* reference hysteresis, 100 ppm | `[datasheet SBAS430E p.4]` | *0.840, once after assembly — calibrate after a thermal cycle, not before* |
| *reference aging*, 50 ppm / 0–1900 h | `[datasheet SBAS430E p.4]` | *0.420 per ~80 days — recalibratable, see §6.7* |
| *DAC INL raw*, ±4 LSB typ / ±12 LSB max | `[datasheet SBAS430E p.3]` | *0.732 / 2.197 — before firmware; the figure ADR 0006 gets 11 % low* |

### 6.5 DYNAMIC — the terms that move while you play

| Term | Source | cents |
|---|---|---|
| **The module's internal ground path** | `[repo docs/decisions/0004-cv-interface-module.md:617, 0006:625]` | **5.7–7.2** |
| **The rack's shared bus ground** | `[repo docs/decisions/0004:632, 0006:626]` | **~4.8** |
| Noise, 0.1–10 Hz, reference + DAC + op-amp | `[datasheet SBAS430E p.4: 12 µVpp ref, 2.6 µVpp DAC; SBOS737C p.7: 1.30 µVpp]` | `[calc]` 12 µV/2.5 V = 4.8 ppm × 7 V = 33.6 µV, + 2.6 µV×2 + 1.3 µV×2 ≈ 41 µVpp | **0.049** |
| Load dependence of the transfer function | jack-side tap, any resistive load ≥ 2.3 kΩ | **0.000** |
| OPA2197 PSRR on the ±12 V rails, ±3 µV/V max | `[datasheet SBOS737C p.7]` | 50 mV step → 0.3 µV | **0.000** |
| OPA2197 CMRR over the 4.5 V input swing, 120 dB min | `[datasheet SBOS737C p.7]` | `[calc]` 1 µV/V × 4.5 V × 2 = 9 µV | **0.011** |
| `D-REVPOL` V_f modulation → LM317 → AVDD → PSRR | `[repo figures.yaml diode-split-rationale]` | **0.00044** |

**The two ground rows are the largest live terms in the design and were not in
either of the page's tables.** Nothing in the precision chain is within an order
of magnitude of them.

### 6.6 Totals

```
[calc]
static + 10 °C thermal, RSS   = √(0.450² + 0.210² + 0.183² + 0.300²)
                              = √(0.2025 + 0.0441 + 0.0335 + 0.0900) = 0.608
static + 10 °C thermal, linear = 0.773 + 0.210 + 0.183 + 0.300       = 1.466
static + 25 °C thermal, RSS   = √(1.125² + 0.210² + 0.183² + 0.300²) = 1.197

SYSTEM, including the ground terms (module at 6.45, rack at 4.8):
                              = √(0.608² + 6.45² + 4.8²) = √65.01      = 8.06
```

### 6.7 Proposed `config/figures.yaml` entry

```yaml
  - id: pitch-cents-budget
    quantity: Total pitch error budget
    value: "0.61 cents"
    status: settled
    owner: hardware/module/pitch-stage.md
    scope: "STATIC + 10 degC thermal, RSS, POST-CALIBRATION. The precision
      chain only. It is NOT the error at the jack - see system_total."
    derivation: "RSS of: thermal 0.450 (DAC ref tempco 0.420 at 5 ppm/degC max
      [SBAS430E p.4] x 7.000 V lever; DAC gain tempco 0.120 at 1 ppm FSR/degC
      [p.3]; TRIM-OFFSET network 0.066; OPA2197 Vos drift 0.060 pitch + 0.031
      reference buffer at 2.5 uV/degC max [SBOS737C p.7]; DAC zero-code drift
      0.048 at 2 uV/degC [p.3]; LT5400 tracking 0.027 at 1 ppm/degC max
      [5400fa p.4]); reference thermal hysteresis 0.210 at 25 ppm additional
      cycles [SBAS430E p.4]; DNL 0.183 at 1 LSB max [p.3]; INL residual 0.300
      after an 11-point/octave table. Levers: gain-type terms pivot at
      Vout = 0 with a 7.000 V maximum; ratio-type terms pivot at Vout = +2.5 V
      with a 2.250 V maximum; 1 mV at the jack = 1.2 cents."
    over_25_degC: "1.20 cents RSS - the figure for a real 0-40 degC rack."
    linear_sum: "1.47 cents."
    system_total: "~8.1 cents RSS, and the precision chain is 0.6 of it. The
      other two terms are owned elsewhere and are not restated here: the
      module's internal ground path and the rack's shared bus ground, both in
      docs/decisions/0004-cv-interface-module.md. E6/E9 measure them."
    forbidden: ["0.85 cents RSS", "1.35 cents linear", "Pole at 15.9 kHz, zero one octave above at 31.8", "gain 2.020000 for every load", "less two Schottky drops"]
    note: "The four prior candidates were ONE budget at FOUR scopes: 0.42 is a
      single row (the DAC reference over 10 degC, which power-entry.md cites and
      which is unchanged); 0.85 is the 10 degC thermal RSS'd with RAW INL,
      double-counting what firmware removes; 1.35 is the linear sum of the same;
      1.2 is the same RSS over 25 degC rather than 10. None was wrong; none
      stated its scope. Assumes TRIM-GAIN deleted and R-BIAS-DAC at 1 M."
```

---

## 7. Impedance and loading

### 7.1 What the DAC presents, and why `C-AA-PITCH`'s position is load-bearing

`[datasheet SBAS430E p.3]` DAC8568 output: **DC output impedance 4 Ω at
mid-code**; slew rate **0.75 V/µs**; settling **5 µs typ / 10 µs max** (¼ to ¾
scale, ±0.024 %); short-circuit current **11 mA**; and —

> **Capacitive load stability: 1000 pF at R_L = ∞, 3000 pF at R_L = 2 kΩ.**

**`C-AA-PITCH` is 10 nF. That is 10× the DAC's own open-circuit stability
limit.** The page places it "from the `R-OPAMP-IN` node to `AGND`", i.e. on the
**far** side of the 1 kΩ, so the DAC sees `1 kΩ + 10 nF` and never a bare
capacitor. **The page states this placement and gives no reason for it. The
reason is that the other placement violates a datasheet limit by 10×.** Put it
on the drawing.

`[calc]` The resulting chain: τ = 1 kΩ × 10 nF = 10 µs, corner 15.92 kHz. Total
settling ≈ DAC's 10 µs max + ~2.2τ ≈ **32 µs**, against a 250 µs update period
at the 4 kHz loop `[repo firmware/README.md:22]` — **13 %.** Fine.

### 7.2 `R-OPAMP-IN` — the clamp calculation, which turns out to be tight

`[datasheet SBOS737C p.5]` Absolute Maximum Ratings, Signal input pins:
common-mode `(V−) − 0.5` to `(V+) + 0.5` V, **Current ±10 mA**.

`[datasheet SBAS430E p.3]` DAC short-circuit current: **11 mA**.

`[calc]` **11 mA > 10 mA.** With `R-OPAMP-IN` shorted out, a DAC on 5.21 V
driving an op-amp whose rails are at 0 V could push its full 11 mA into an input
clamp rated for 10 mA. With 1 kΩ in place:

```
I = (5.21 V − 0.5 V) / 1 kΩ = 4.71 mA   →  2.1× margin against ±10 mA
```

**`R-OPAMP-IN` is not belt-and-braces; the part it protects is out of spec
without it, by 10 %.** `bom.csv` asserts it bounds clamp current; this is the
arithmetic, and 1 kΩ is confirmed as the right value.

### 7.3 Source impedance and bias current

`[calc]` With `TRIM-GAIN` deleted and `R-BIAS-DAC` at 1 MΩ:

| Node | Impedance |
|---|---|
| (+) input source | `1 kΩ + (4 Ω ‖ 1 MΩ) = 1.004 kΩ`, shunted by `C-AA-PITCH` 10 nF |
| (−) input source | `R1 ‖ R2 = 5.00 kΩ` |
| **imbalance** | **4.00 kΩ** |

`[calc]` Output error from bias currents, non-inverting form:

```
V_err = I_B(−)·R2 − I_B(+)·R_source·(1 + R2/R1) = I_B·(10 kΩ − 2 kΩ) = I_B × 8 kΩ
  at 25 °C (±20 pA max)   : 0.16 µV      = 0.0002 cents
  at 40 °C (~±60 pA)      : 0.48 µV      = 0.0006 cents
  at +125 °C (±5 nA max)  : 40 µV        = 0.048  cents
```

`[calc]` The exact null is `R_source = R2/(1 + R2/R1) = 5.00 kΩ`, but 5 kΩ
against `C-AA-PITCH` would drop the anti-alias corner to 3.2 kHz — inside the
audio band. **Not worth it: the term is 0.0006 cents at any temperature this
instrument will see.** Left unbalanced, deliberately, and now on the record.

### 7.4 `R-OUT-PROT` inside the DC loop

`[calc]` DC: the loop removes it. `[datasheet SBOS737C p.7]` `A_OL` ≥ **120 dB**
(min, R_L = 2 kΩ) → loop gain `10⁶ × 0.5 = 5×10⁵` → residual at +7 V is
**14 µV = 0.017 cents**. This is why the "gain is identically load-independent"
claim holds, and it now has a number behind it.

`[calc]` Op-amp output excursion, with the feedback current through R2 included:

| Load at the jack | `V_opamp` at `V_jack` = +7.500 V | Headroom to 11.03 V |
|---|---|---|
| open circuit | 7.775 V | 3.26 V |
| 100 kΩ (one VCO) | 7.850 V | 3.18 V |
| 25 kΩ (four VCOs on a mult) | 8.075 V | 2.96 V |
| **2.30 kΩ** | **11.03 V** | **0 — the limit** |

`[calc]` **Minimum load: 2.30 kΩ at the +7.500 V reserve extreme, 1.72 kΩ at
+7.000 V.** The page says "every load from open circuit to 2 kΩ"; that is true at
+7 V and **false at the +7.5 V reserve**, by 15 %. State the condition.

`[calc]` Into a dead short: the op-amp rails, `I = 11.03 V / 1 kΩ = 11.03 mA`,
`P = 122 mW` in `R-OUT-PROT` — well inside the 0.66–1 W `bom.csv` specifies, and
far below the `[datasheet SBOS737C p.8]` ±65 mA `I_SC`. The op-amp never reaches
its own short-circuit limit.

`[datasheet SBOS737C p.8]` Overload recovery **200 ns**. `[calc]` So the
"every patch-in is a brief rail excursion" case recovers in `200 ns + ~3τ` where
τ = `1 kΩ × 10 nF` = 10 µs → **~30 µs**. A click, not a musical event.
**And nothing leaves the module during it**: the jack is shorted by the plug, so
the excursion is entirely behind `R-OUT-PROT`.

I checked whether a high-value resistor from the op-amp output to the (−) node
could keep the loop closed through a jack short. `[calc]` It cannot: holding the
(−) node at 4.75 V against a shorted jack needs `(4.75−2.5)/10k + 4.75/10k =
700 µA`, which from an 11 V rail demands **9.36 kΩ** — the same order as R2, which
destroys the topology. **The rail excursion on jack short is structural.
Document it; do not try to fix it.**

### 7.5 The passive-mult case

Covered quantitatively in §5.3. The operational statement for the manual:
**`PITCH` may share a passive mult with other `PITCH`-class destinations and with
2 m of cable, but joining it to `MOD` or `BREATH` on one mult produces 45 % and
67 % overshoot** — several semitones of transient on every note. `[calc]` The
budget is `C_load ≤ 11.0 nF` total and `C-FILT-PITCH` already occupies 10 nF, so
**the available external allowance is ~1 nF, i.e. about 2.5 m of patch cable.**
That is a much tighter statement than "safe to about 10 nF" and it is the one
E9 should test against.

---

## 8. Netlist readiness

### 8.1 The name collision — two nets, one name

`[repo hardware/module/pitch-stage.md:202, 136]` uses bare **`AGND`** for
`C-AA-PITCH`'s and `C-FILT-PITCH`'s returns, meaning the module analog return.

`[repo docs/decisions/0004-cv-interface-module.md:600–612]`, the return table:

> | `AGND`, from the etherCON | **Nothing.** It is an in-amp input, not a ground (ADR 0003) |
>
> "`AGND` is not in this list. It terminates at the in-amp's IN+ and at the two
> 1 MΩ bias resistors, and that is all it does. **Anything that makes it a
> return path breaks the reason a 2 m analog run works at all.**"

**A netlist generated from the current names will short the breath sensor's
sense conductor to the module's analog pour**, destroying the differential
measurement at the one place the design is least able to notice. No grep finds
this; both documents read correctly alone.

**Rename on this page: `AGND` → `AGND_MOD`.** (The umbilical conductor's name is
`umbilical.md`'s to settle; `SENSE_LO` or `BREATH_RTN` would both be
unambiguous. Flagged, not touched.)

### 8.2 Canonical net list for the pitch stage

| # | Net | Members | Notes |
|---|---|---|---|
| 1 | `VREFOUT` | U-DAC pin 8 (`VREFIN/VREFOUT`), `TRIM-OFFSET` top | `[datasheet SBAS430E p.6]` pin 8 on TSSOP-16 |
| 2 | `VREF_TRIM_W` | `TRIM-OFFSET` wiper, `R-TRIM-BLEED`, `C-REF-TRIM`, `R-OPAMP-IN(ref)` | high-Z; keep short |
| 3 | `VREF_TRIM_B` | `TRIM-OFFSET` bottom, `R-TRIM-B` top, `R-TRIM-BLEED` other end | |
| 4 | `VREF_BUF_IN` | `R-OPAMP-IN(ref)` → U-OPA (+) | |
| 5 | `VREF_BUF_FB` | U-OPA (−), `R-TRIM-F`, `R-TRIM-G` | |
| 6 | **`V_REF_BUF`** | reference-buffer output, `R-TRIM-F`, **LT5400 pin 7** | the page's `V_ref`; **name it, it is currently prose only** |
| 7 | `PITCH_DAC` | U-DAC pin 4 (`VOUTA`), `R-BIAS-DAC`, `R-OPAMP-IN` | see §8.3 |
| 8 | `PITCH_INP` | `R-OPAMP-IN`, `C-AA-PITCH`, U-OPA (+) | `C-AA` **must** be on this side of the 1 kΩ (§7.1) |
| 9 | `PITCH_INN` | U-OPA (−), **LT5400 pin 2**, **LT5400 pin 3**, `C-FB-PITCH` | pins 2 and 3 adjacent: shortest possible summing node |
| 10 | `PITCH_OPOUT` | U-OPA output, `C-FB-PITCH`, `D-JACK-CLAMP` centre, `R-OUT-PROT` | |
| 11 | `PITCH_JACK` | `R-OUT-PROT`, `C-FILT-PITCH`, **LT5400 pin 6**, `J-CV` pin 3 (tip) | copper order in §2.5 |
| 12 | **`AGND_MOD`** | `C-AA-PITCH`, `C-FILT-PITCH`, `C-REF-TRIM`, `R-TRIM-B` bottom, `R-TRIM-G`, `R-BIAS-DAC`, `J-CV` pin 1 (sleeve), **LT5400 pins 1, 4, 5, 8**, **LT5400 pin 9 (exposed pad)** | renamed from `AGND` |
| 13 | `+12V_A` / `−12V_A` | U-OPA rails, `D-JACK-CLAMP` anodes/cathodes | one `1N5817` each (§5.2) |
| 14 | `AVDD_DAC` | U-DAC pin 3 | 5.21 V `[repo figures.yaml dac-rail]`, hard floor 5.00 V |

### 8.3 Three remaining ambiguities a transcriber will hit

1. **"DAC ch1" is not a pin.** `[repo hardware/module/pitch-stage.md:21]` says
   "DAC ch1"; `[repo bom.csv U-DAC]` says "Populate 6 of 8: pitch, 4 mods, mod
   offset". `[datasheet SBAS430E p.6]` the part's pins are `VOUTA`…`VOUTH`, and
   the SPI address field is a third numbering. **Fix the mapping explicitly —
   pitch = `VOUTA` = TSSOP-16 pin 4 = SPI address `0h` — before transcription**,
   or six channels get assigned by guess.
2. **`V_ref` has no net name**, only prose. Proposed `V_REF_BUF` above.
3. **`J-CV` pin 2 is a free normalling contact.** `[repo bom.csv J-CV]` "PIN 3 =
   TIP, PIN 2 = TIP-NORMAL switch contact — NORMALLY CLOSED TO PIN 3 AND OPENING
   WHEN A PLUG IS INSERTED — PIN 1 = SLEEVE… nothing in the design uses it yet."
   A netlist must state that pin 2 is **deliberately unconnected** on `PITCH`, or
   the ERC will flag it every run and someone will eventually tie it somewhere.

---

## 9. Corrected drawing, for transcription

```
                  ┌──[R-TRIM-F 200R]──────────────────┐
                  │                                   │
   AGND_MOD ──[R-TRIM-G 10.0k]──┐                     │
                                │                     │
   VREFOUT ─┬──[TRIM-OFFSET 1k]─┼─┬──[R-TRIM-B 24.3k]─┼── AGND_MOD
   (2.500V) │    3-terminal   w │ │                   │
            │        │          │ │                   │
            │        ├─[1M bleed]─┘                   │
            │        ├─[100n]── AGND_MOD              │
            │        │                                │
            │        └──[R-OPAMP-IN 1k]──┐            │
            │                     ┌──────┴──────┐     │
            │                     │ +  ½ OPA2197├─────┴── V_REF_BUF = 2.4996 V
            │                     │ −           │            │   (±50.4 mV)
            │                     └──────┬──────┘            │
            │                            └───────────────────┘
                                                         G = 1.0200
                                                              │
                                                      [LT5400 R2, pins 7→2]
                                                              │  10k
   U-DAC VOUTA ─┬──[R-OPAMP-IN 1k]──┬─────────────────────────┤
   0.25…4.75 V  │                   │                         │
                │              [C-AA-PITCH 10n]               │
        [R-BIAS-DAC 1M]             │                         │
                │              AGND_MOD                       │
           AGND_MOD                 │                         │
                                    │       ┌─────────────────┴─────┐
                                    └───────┤ +                     │
                                            │      ½ OPA2197        ├──┬── PITCH_OPOUT
                              ┌─────────────┤ −                     │  │
                              │             └───────────────────────┘  │
                              ├──[C-FB-PITCH 2.2n]─────────────────────┤
                              │                                        │
                              │                  [D-JACK-CLAMP BAV99]──┤── ±12V_A
                              │                                        │
                              │                  [R-OUT-PROT 1k, 1206, 0.66-1W]
                              │                                        │
                              └──[LT5400 R3, pins 3→6]──┬──────────────┴── PITCH_JACK
                                        10k             │                     │
                                    (0R link where      │              [C-FILT-PITCH 10n]
                                     TRIM-GAIN was)     │                     │
                                                        │                 AGND_MOD
                                                    J-CV tip (pin 3)

   LT5400 pins 1, 4, 5, 8 (die R1, R4)  → AGND_MOD   (guards)
   LT5400 pin 9 (exposed pad)            → AGND_MOD   (AC shield)
   Copper order at the connector: J-CV tip → C-FILT-PITCH → R3 tap → R-OUT-PROT
```

---

## 10. What I could not settle

| Item | Why | What decides it |
|---|---|---|
| **Cermet tempco: 100 or 250 ppm/°C** | No trimmer datasheet is banked; ADR 0006 uses 250, the page and BOM use 100 | A `MANIFEST.csv` row for the chosen part. **Not blocking** — §1.5 shows the `TRIM-OFFSET` term is 0.066 or 0.133 cents, and §3 removes the cermet from the gain ratio where it *was* blocking |
| **INL residual after an 11-point table: ~0.30 cents** | `[calc, assumption]` — the residual depends on INL *shape*, and SBAS430E publishes no INL-vs-code curve for the 8568 | E9, with a 6½-digit meter and the real table. It is the largest term in §6.4 and the only one in the budget that is an estimate |
| **Rev fc of the LT5400** | rev **fa** is banked; `bom.csv` names **fc** canonical; `analog.com` still unreachable | Nothing on this page depends on the difference. Rev fa's option table ends at `-6`, so `LT5400-7` remains **not-in-document**, not refuted |
| **The −3 dB at 12.2 kHz** | `[repo]` — plausible against the corrected 7.23/14.5 kHz shelf plus the 15.9 kHz jack pole, but I did not recompute the combined response by hand | The SPICE deck this wave feeds. It is the one frequency-domain number on the page I am passing through unverified, and I am saying so |
| **Whether `AGND_MOD` is quiet enough for the pad** | The 5.7–7.2 cent ground term is a *review estimate*, not a measurement `[repo ADR 0004:617 "a review measured this as"]` | E6/E9, which `ROADMAP.md:200` already schedules. §2.4's recommendation is correct either way — if that region is not quiet, the pad is not the stage's problem |
