# S4 — Breath chain, end to end: staleness sweep

**Date:** 2026-09-21
**Scope:** sensor → tube/restrictor → reference and buffers → umbilical analog pair →
INA828 receive stage → **new §4 response shaper** → gain/offset output stage → jack;
plus the ADC copy on the carrier.

**Corpus audited:** `hardware/**` (including `hardware/bom.csv`), `docs/decisions/**`,
`config/**`, `docs/reference/**`, `ROADMAP.md`, `README.md`, `firmware/README.md`.
`docs/review/**`, `docs/log/**` and `docs/research/**` were read for context only and
are **not** reported as stale.

**Nothing was edited except this file.**

**Headline:** the response-shaper landing is the same failure again. §4 of
`breath-output-stage.md` is internally consistent with itself and with four new BOM
rows, and **nothing else moved**: the op-amp budget, the package count, the decoupler
count, the panel-knob prose, the commissioning order, the two block diagrams the
signal actually passes through, and the ADR that says curve shaping is "not
recoverable in hardware" are all still on the pre-§4 state. Separately, the `R1b` /
`R-ISO-REF` drawing fix **did** land cleanly, and the in-amp polarity fix landed —
those are the two genuinely clean results in this sweep.

---

## Index by disputed fact

| # | Disputed fact | Rank |
|---|---|---|
| F1 | How many OPA2197 packages and spare halves the module has | **Showstopper** |
| F2 | The in-amp's full-scale output (five values in circulation) | **Showstopper** |
| F3 | The in-amp's rest output, and what the breath jack does at power-on | **Showstopper** |
| F4 | The 2.8 kPa working point | High |
| F5 | Whether `REF` is grounded or trimmed | High |
| F6 | `POT-OFFSET` at centre: +0.07 V or +0.605 V; buffered or not | High |
| F7 | §4's passives exist on a drawing and in no BOM row | High |
| F8 | `MECH-PTFE` is a Helmholtz restrictor sized to place a resonance | High |
| F9 | The new stage's own headroom | High |
| F10 | Whether hardware curve shaping exists, and which ADR owns it | High |
| F11 | Link CMRR with `R1b` fitted: 70.2 dB, 73 dB, or "fifty times" | High |
| F12 | Sensor full scale: 4.7 V or 4.80 V | Medium |
| F13 | `R-FB`: 40 kΩ or 40.2 kΩ | Medium |
| F14 | `POT-RESP`'s taper | Medium |
| F15 | Breath's reconstruction corner: ~2 kHz or ~480 Hz | Medium |
| F16 | Panel: two knobs / 107 mm, or three knobs / 97 mm / 10HP | Medium |
| F17 | The commissioning order | Medium |
| F18 | The breath latency budget | Medium |
| F19 | Anti-alias attenuation: 58 dB at 500 kHz or 55 dB at 330 kHz | Medium |
| F20 | `C_cm` tolerance | Medium |
| F21 | The two block diagrams the shaper was inserted into | Medium |
| F22 | The deleted breath presence comparator | Medium |
| F23 | Hard blow at the in-amp: −4.69 V or 4.64 V | Medium |
| F24 | Thermal drift: 20 mV or 23 mV, and at which node | Low |
| F25 | The CMRR requirement: 60 dB or 58.5 dB | Low |
| F26 | Raw gain vs effective gain in the `REF` trim arithmetic | Low |
| F27 | Breath analog-path latency total: 2.80 ms or 2.83 ms | Low |
| F28 | The scaling stage's gain: "~2.13×" | Low |

---

## F1 — How many OPA2197 packages and spare halves the module has — **Showstopper**

Six documents, four different answers. This decides what gets ordered.

**Zero spare (the new §4, twice):**

> `hardware/module/breath-output-stage.md` §4:
> "| Op-amp | **Both remaining OPA2197 halves** — one shapes at ÷2 inverting, one
> restores ×2 inverting to put scale and polarity back |"

> `hardware/module/breath-output-stage.md` §4, panel box:
> "That fix wants a half, and **this stage takes the last two.**"

**Two spare (the same file, 135 lines earlier, and the BOM):**

> `hardware/module/breath-output-stage.md` §Values:
> "**Two op-amp halves**, which settles a count that has been wrong in the BOM
> twice: gain buffer and summer. **Ten of twelve halves used across the module,
> two spare.**"

> `hardware/bom.csv` `U-OPA-PITCH`, qty **6**:
> "Six packages, twelve halves, TEN used: pitch, mod 1-4, mod offset follower,
> VREFOUT follower, breath REF-zero buffer, breath gain buffer, breath summer.
> **TWO SPARE.**"

**One spare:**

> `hardware/module/breath-receive-stage.md`:
> "It costs **the last spare OPA2197 half**, and `U-OPA-PITCH` goes to six packages
> **so there is still one.**"

**Six packages (two more places):**

> `hardware/module/power-entry.md`, the rail drawing:
> "`├───┬──[D1 1N5817]──[FB1]──[C1 47µF]──┬── MODULE ANALOG +12V`
> `│   │                                  │   OPA2197 ×6, INA828`"

> `hardware/bom.csv` `C-DECOUPLE`, qty **19**:
> "One per supply pin, close to the pin. **6 x OPA2197 on +/-12V = 12**, INA828 = 2,
> LM311 on +/-12V = 2, DAC8568 AVDD+DVDD = 2, 74AHCT125, LT1641 VCC, LM317 in."

**Seven packages, and a self-contradicting row:**

> `hardware/bom.csv` `U-RESP`, OPA2197IDR, qty **1**, description
> "Response shaper: 1/2 shapes at /2 inverting, 1/2 restores x2 inverting" — note:
> "**This stage consumes BOTH remaining spare OPA2197 halves**, so the separate A5
> finding — POT-OFFSET's wiper is unbuffered … — **needs this additional package**."

That row cannot be read consistently. If the shaper lives in `U-RESP` (its own
package, which is what the row's *description* and the §4 schematic label `½ U-RESP`
both say), then it does **not** consume `U-OPA-PITCH`'s two spares, and those two
spares are still free — so the A5 buffer fix needs no new package at all. If instead
the shaper really does consume the two spares, then `U-RESP` is a package for the A5
fix and its own description is wrong.

**Arithmetic, both readings:**

| | Halves used | Packages | Decouplers (2/package) |
|---|---|---|---|
| Before §4 | 10 of 12 | 6 | 19 (as `C-DECOUPLE` says) |
| Shaper in the 2 spares, A5 fix in a new package | 13 of 14 | **7** | **21** |
| Shaper in `U-RESP`, A5 fix in the 2 spares | 13 of 14 | **7** | **21** |

Either way the module is **7 OPA2197 packages and 21 `C-DECOUPLE` parts**, and
`power-entry.md`'s "OPA2197 ×6", `C-DECOUPLE`'s qty 19 and enumeration, and
`U-OPA-PITCH`'s "TWO SPARE" are all wrong by the same change. The seventh package
also adds ~1 mA of quiescent current to a +12 V budget `power-entry.md` sizes
explicitly; nobody re-ran it.

**Also note the receive page's "still one"** was already wrong *before* §4 — it says
six packages, twelve halves, eleven used. It disagrees with the BOM's ten-used count
on the same day.

---

## F2 — The in-amp's full-scale output — **Showstopper**

The claim exists in **five** forms. This number sets the panel gain range, the
`POT-RESP` knee placement, and every downstream headroom argument.

| Value | Where |
|---|---|
| **−9.6 V** | `breath-receive-stage.md` circuit: "`= 0 V at rest, −9.6 V at full`" |
| **−9.6 V** | `breath-receive-stage.md` prose: "The in-amp then rests at 0 V and **reaches −9.6 V at full sensor range** — about −4.7 V in real playing." |
| **9.94 V span** | `breath-receive-stage.md` derivation table: "**R_G = 42.2 kΩ → G = 2.1848, effective 2.1611** \| **jack span 9.94 V**" |
| **9.94 V** | `breath-output-stage.md` §4 drawing "`(0…−9.94V)`" and §4 table "`\| full scale \| 9.94 V \| 4.97 V \| 291 µA \| 1.586 \|`" |
| **−10.05 V** | `breath-output-stage.md` §1 table: "\| Sensor full scale (6 kPa) \| 4.800 V \| **−10.05 V** \|" |
| **−10 V** | `hardware/bom.csv` `U-DIFFRX`: "Output is **-0.44V at rest to -10V at full**" |
| **9.94 V** | `hardware/bom.csv` `R-GAIN-INAMP`: "Effective 2.161 after the bias/series divider -> **9.94V jack span**" |

**Which is right.** The receive page's own derivation is correct and checks out:

```
sensor span 4.8 − 0.2                         = 4.600 V
G  = 1 + 50k/42.2k                            = 2.18483
bias divider 1M/(1M+11k) per leg              = 0.98912
effective                                     = 2.16106
4.600 × 2.16106                               = 9.941 V   ← the derived figure
4.600 × 2.18483                               = 10.050 V  ← the same gain *un*-derated
```

So **−9.94 V is the number** and **−10.05 V is the same figure with the 1 MΩ bias
divider left out** — `breath-output-stage.md` §1 and §4 print both, 220 lines apart,
in the same file.

**−9.6 V is derived nowhere.** It implies an effective gain of 9.6/4.6 = 2.087, which
matches no resistor, no divider and no combination in the corpus. It survives in the
one page that also contains the correct derivation.

**`bom.csv` `U-DIFFRX` is the pre-trimmer circuit verbatim** — see F3. It is the build
document.

**Consequence.** The §4 shaper's entire scaling argument is pinned to the in-amp's
full scale: "`÷10: hard blow 4.64 V at the in-amp → 0.464 V at the node`". At the
−10.05 V reading the node figures shift ~1 %; at the −9.6 V reading they shift ~3.5 %
and the diode-current column is wrong throughout.

---

## F3 — The in-amp's rest output, and what the jack does at power-on — **Showstopper**

Two separate stale claims that compound.

### (a) Rest output: 0 V vs −0.44 V

> `hardware/module/breath-receive-stage.md`: "`Vout = −2.185·(V_BREATH − V_AGND) + V_REF`
> ` = 0 V at rest`" and "+0.437 V nulls the pedestal"

> `hardware/module/breath-output-stage.md` §1 table: "\| Rest \| 0.200 V \| **0.00 V** \|"

> `hardware/bom.csv` `U-DIFFRX`: "REF is driven by TRIM-BREATH-ZERO through a BUFFER …
> **Output is -0.44V at rest to -10V at full**; the downstream stage inverts, which is
> also the topology that does gain-then-offset with **two pots in one op-amp half**."

−0.44 V is `−2.1848 × 0.200 = −0.437 V`, i.e. **the in-amp with `REF` at 0 V** — the
pre-trimmer circuit. The same BOM row says in its first clause that `REF` *is* driven
by the trimmer, and in its third clause quotes the output of the circuit where it is
not. The row's tail — "two pots in one op-amp half" — is a third fossil: both schematic
pages and `U-OPA-PITCH` say the output stage is **two** halves.

### (b) Power-on / unplugged jack level

> `docs/decisions/0006-cv-channel-allocation.md`, power-on table:
> "\| **Breath** \| 0 V \| **The receiver's differential pulldown holds it there**
> (ADR 0003) \|"

> `docs/decisions/0005-power-architecture.md`:
> "**Pull down the module's breath receive input**, so that an instrument which is
> switched off — or unplugged — **presents 0 V** rather than a floating buffer output.
> **One resistor**, and it means powering down the instrument silences the patch
> instead of leaving a stuck level (ADR 0003)."

against:

> `hardware/module/breath-receive-stage.md`, "What this settles":
> "\| The 100 kΩ differential pulldown \| **Deleted.** R4/R5 do its job without its
> 1–17 % attenuation … \|"

> `docs/decisions/0003-breath-sensing-path.md`: "**The pulldown is deleted and replaced
> by a common-mode bias return.** … **A purely differential element gives the in-amp's
> inputs no DC path to ground at all.** Unplugged, input bias current ramps both inputs
> until the amplifier saturates, **so the breath jack goes to a rail rather than to the
> 0 V ADR 0005 promises.**"

> `hardware/bom.csv` `R-BIAS-INAMP`: "**REPLACES R-PD-BREATH.**"

ADR 0003 *names* ADR 0005's promise as false and ADR 0005 still makes it. ADR 0006
still credits a part that exists in no drawing and no BOM row.

And ADR 0004 already states the correct behaviour, in a third place:

> `docs/decisions/0004-cv-interface-module.md`: "the jack **falls to wherever the panel
> offset knob left it** and stays there."

**What the jack actually rests at** `[calc]`, from `breath-output-stage.md`'s own
values:

*Instrument alive, mouthpiece at rest* (in-amp trimmed to 0 V): the jack carries the
offset term only — the page's own table, **+5.04 V (full CCW) … +0.07 V (centre) …
−4.89 V (full CW)**.

*Instrument off or unplugged* (R4/R5 pull both inputs to AGND, so `Vout = +V_REF =
+0.437 V`; the shaper is below its knee here and passes ×1):

```
jack = V_offset − 0.437 × G_panel
G = 0.5   →  offset − 0.22 V   →  +4.82 … −5.11 V
G = 2.13  →  offset − 0.93 V   →  +4.11 … −5.82 V   (the review's −5.9…+4.1)
G = 4.0   →  offset − 1.75 V   →  +3.29 … −6.64 V
```

**Envelope −6.64 V … +4.82 V.** ADR 0006's table says 0 V. Nothing in the analog path
holds any particular level, and the design is right about that (ADR 0004) — only two
of the five documents say so.

---

## F4 — The 2.8 kPa working point — **High** (and a *never-derived* fact)

Three documents assert it and the citation chain is a loop with a hole in it.

> `hardware/module/breath-output-stage.md`: "**Real playing only reaches about 2.8 kPa
> against the sensor's 6 kPa range** **(ADR 0003)**, so the stage's working input is
> 0 to about −4.7 V."

> `hardware/controller/carrier.md` §2: "`real play  = 2.8 kPa → 0.2 + 0.766 × 2.8 = 2.34 V → 1.40 V → 1743 counts`"
> "`                           [2.8 kPa from breath-receive-stage.md]`"

> `hardware/module/breath-receive-stage.md`, Commissioning: "The knob does more work
> than this page used to say: **real playing tops out around 2.8 kPa** against the
> sensor's 6 kPa range" — **no citation at all.**

The one document cited by name says something else:

> `docs/decisions/0003-breath-sensing-path.md`: "The 0–6 kPa range was well chosen in
> 2021 and stands. **Normal wind-controller playing sits around 0–5 kPa.**"

ADR 0003 contains no "2.8". `grep -rn "2\.8 kPa"` over the whole corpus returns only
the three lines above. So: **output stage → ADR 0003 (which does not contain it);
carrier → receive page; receive page → nowhere.** The number is asserted by the page
that is cited as its source.

**What it is load-bearing for**, both ways:

| | at 2.8 kPa (asserted) | at 5 kPa (ADR 0003) |
|---|---|---|
| Sensor | 2.347 V | 4.033 V |
| In-amp (×2.1611) | −4.64 V | −8.28 V |
| Panel gain for 10 V at the jack | **2.15×** ("≈2.13×", "middle of the knob") | **1.21×** — lower third of the knob |
| ADC counts at full playing | 1743 (span 1594) | 3003 (span 2854) |
| `POT-RESP` knee as a fraction of a hard blow | "about a quarter" | about an eighth |

If ADR 0003's 0–5 kPa is right, the output stage's "comfortably inside 0.5–4, which is
the point of specifying the range from playing rather than from the sensor" argument
loses its force, the carrier's "playable span ≈ 1594 counts" understates by 79 %, and
`R-RESP`'s 15 kΩ first sizing targets the wrong dynamic. **One of the two numbers has
to be retired.** ADR 0003's is at least stated in the document that owns the sensor
decision; the 2.8 kPa figure is stated in the document that cites it.

---

## F5 — Whether `REF` is grounded or trimmed — **High**

The decision (trimmed, buffered, from the LM317 5.21 V rail) is correctly recorded in
`breath-receive-stage.md`'s main argument, ADR 0003, and `bom.csv` `TRIM-BREATH-ZERO`.
Three fossils of the grounded circuit survive, one of them on the page that makes the
argument.

> `hardware/module/breath-receive-stage.md`, "What the jack does when the watchdog
> fires — settled": "`CLR` reaches the DAC channels; breath touches none of them, and
> **now that `REF` is grounded** it touches the breath stage in no way at all"

— forty lines after the same page's "### Why `REF` is trimmed rather than grounded",
which says "**Grounding it makes the panel knobs interact, and an earlier revision of
this page claimed the opposite.**"

> `ROADMAP.md`, E10: "Analog breath stage: **in-amp receiver with `REF` grounded**,
> gain/offset knobs. **Set `TRIM-BREATH-ZERO` first**, until the in-amp output reads
> 0 V"

— the same row specifies the trimmer whose existence the first clause denies.

> `firmware/README.md`: "**Breath is outside all of this.** It never passes through the
> DAC, and since **the in-amp's `REF` pin is grounded rather than driven by a firmware
> zero (ADR 0003)**, no DAC register touches the breath jack at all."

— the conclusion survives, the stated reason is false, and ADR 0003 no longer says it.
ADR 0003's actual text: "`REF` carries a **commissioning trimmer**, buffered, derived
from the LM317's 5.21 V rail."

All three are exactly the kind of clause that outlives the circuit because the
sentence still reads plausibly.

---

## F6 — `POT-OFFSET` at centre: +0.07 V or +0.605 V — **High**

Both figures appear in the same file and in the same BOM.

> `hardware/module/breath-output-stage.md` §Offset table:
> "\| **Centre** \| 2.605 V \| **+0.07 V** \|"
> and "**This wiper does *not* need buffering.** Its source impedance varies from 0 at
> either end to `R/4` at centre, so the endpoints are exact and the middle is slightly
> non-linear in rotation. For an offset knob that is feel, not error."

> `hardware/module/breath-output-stage.md` §4, panel box:
> "`A5` showed `POT-OFFSET`'s wiper is unbuffered, which is why its **"zero at centre"
> actually sits ~20° past centre at +0.605 V.** That fix wants a half"

> `hardware/bom.csv` `POT-OFFSET`: "+-5V at the jack with ZERO AT CENTRE: CCW +5.04V,
> **centre +0.07V**, CW -4.89V. **Wiper does NOT need buffering** — source impedance is
> 0 at both ends and R/4 at centre, so the endpoints are exact and the middle is
> slightly non-linear in rotation, which for an offset knob is feel rather than error."

> `hardware/bom.csv` `U-RESP`: "the separate A5 finding — **POT-OFFSET's wiper is
> unbuffered, which is why its zero sits ~20deg past centre at +0.605V** — needs this
> additional package."

**The arithmetic settles it, and +0.605 V is right** `[calc]`:

```
buffered wiper, R_OFF = 21.0k:
  2.605/21.0k = 124.05 µA ; −12/95.3k = −125.92 µA ; Σ = −1.87 µA
  × R_FB 40k  = −0.075 V  →  jack +0.07 V            ← the page's table

unbuffered 10k pot at centre: R_th = R/4 = 2.5 kΩ, in series with R_OFF
  effective 23.5k → 2.605/23.5k = 110.9 µA ; Σ = −15.06 µA
  × R_FB 40k  = −0.602 V  →  jack +0.60 V            ← A5's figure
```

So the page's own "the middle is slightly non-linear in rotation … feel, not error" is
falsified by a factor of 8 by its own §4, and the offset table it heads is the
buffered-wiper table for a wiper the same page says is not buffered. `bom.csv`
simultaneously specifies "wiper does NOT need buffering" and budgets a package for
buffering it.

The knock-on: `breath-output-stage.md`'s Still-open bullet "**`POT-OFFSET` detent at
centre**, which is now a meaningful position rather than an arbitrary one" is
contradicted by §4's "unlike `POT-OFFSET` (whose detent the review found lands ~20° off
its true zero)". A detent at a position that is 0.605 V away from zero is worse than
no detent.

---

## F7 — §4's passives are drawn and un-BOMed — **High**

§4's cost table lists them:

> `hardware/module/breath-output-stage.md` §4: "\| Passives \| `POT-RESP` 50 k lin (same
> part as `POT-GAIN`), `R-RESP` 15 k, `D-RESP` ×2 1N4148, **R1 20 k, R2 10 k, divider
> 2 × 10 k** \|"

`hardware/bom.csv` has `POT-RESP`, `R-RESP`, `D-RESP`, `U-RESP` and **nothing else**.
The four resistors that set the stage's gain (`−R2/R1 = −0.5`) and generate the
`+V_in/2` leg have **no row, no value tolerance, no package**. `grep -n "20k\|R1 20"`
over `bom.csv` returns nothing for this stage.

This is the identical defect this sweep was called for — a part on a drawing and not in
the build document — running in the opposite direction from `R1b`/`R-ISO-REF`, which
were in the BOM and on no drawing.

**Designator collision, same chain.** §4 names its resistors `R1` and `R2`.
`breath-receive-stage.md` already uses `R1` for the instrument-side 1 kΩ
(`R-SER-BREATH-INST`) and `R2`/`R3` for the module-side 10 kΩ 0.1 % pair. Three of the
five `R1`/`R2`/`R3` symbols in the breath chain now mean two different parts, in two
files, one of which is the build reference for the other.

**Tolerance is load-bearing and unstated.** §4's central claim —

> "which is **exactly zero at p = 0.5, for every input voltage**. So a nonlinear branch
> hung off the wiper carries no current at all at centre detent — **the stage is
> mathematically linear in the middle, not approximately linear.**"
> … "unlike `POT-OFFSET` … **this null is set by the topology, not by resistor
> tolerance.**"

is only true if the `2 × 10 k` divider is exactly 1:1 **and** `R2/R1` is exactly 1:2.
The null is set by *two resistor ratios*, not by topology. At 1 % parts the residual at
centre is of order 1–2 % of `V_in/2` — ~50 mV at a hard blow, well under the 0.6 V
diode knee, so the *practical* claim survives; the *stated* claim does not, and it is
the claim used to justify the centre detent over `POT-OFFSET`'s.

---

## F8 — `MECH-PTFE` is a Helmholtz restrictor sized to place a resonance — **High**

> `hardware/bom.csv` `MECH-PTFE`, description field: "**Helmholtz restrictor** AND
> liquid-water barrier at the sensor port"
> note: "One part, two jobs: **sizes the resonance above the 500Hz corner** and blocks
> liquid. **Size the orifice at E2.** Trap volume <=1mL."

Every clause is refuted by the ADR it cites (`adr` column = 0003):

> `docs/decisions/0003-breath-sensing-path.md`: "**The resonance needs handling, and the
> model this ADR used was invalid.** An earlier revision called it a **Helmholtz
> resonator** at ~320 Hz and prescribed a trap volume to place it. A Helmholtz model
> requires the neck volume to be small against the cavity, and here it is the other way
> round: at a 3 mm bore the 400 mm tube holds **2.83 mL**, which is larger than the
> ≤1 mL trap. **The lumped assumption is violated backwards.**"
>
> "- It sits **below the 500 Hz filter corner either way** …"
> "- It is **independent of trap volume.** **No restrictor *size* moves it.** The
> previous prescription — size the trap to place the resonance — **cannot work** …"
>
> "**So the intent is damping, not placement.** … The same plug still doubles as the
> moisture barrier, which is why it is **specified as porous PTFE rather than as an
> orifice**."
>
> "- **E2 measures the damped response, not the resonant frequency**"

`ROADMAP.md` E2 carries the corrected version — "**The restrictor is sized by ring-down,
not by frequency** … The 214–429 Hz pipe mode is below the filter corner and independent
of trap volume, so it is damped, not placed (ADR 0003)" — so the sweep reached the
ROADMAP and stopped before the BOM. The BOM is the document a part gets ordered and
specified from, and it currently instructs the builder to size an orifice to place a
resonance that no orifice size can move.

---

## F9 — The new stage's own headroom is never derived — **High**

§3 of `breath-output-stage.md` derives the *output* stage's clip condition in detail
("**offset at +5 V and gain at 4× puts a hard blow at +23 V**, and the OPA2197 stops at
about ±11.5 V"). §4 derives **no** headroom at all for the stage it adds, and the stage
it adds sits **upstream of the gain knob** by deliberate choice:

> §4, Open before layout: "**Where it inserts.** Drawn here between the in-amp and the
> gain attenuator, deliberately: the signal there has a **fixed** scale set by the
> in-amp … Put it after `POT-GAIN` instead and **the curve would change every time you
> moved the gain knob**, which is the one arrangement that must not happen."

Taking §4's own gain-ratio column `[calc]` — the restore stage's output is
`V_in × ratio`, since `÷2 × ratio` then `×2`:

| In-amp | §4 ratio | Restore-stage output | vs OPA2197 ±11.5 V |
|---|---|---|---|
| 4.64 V (hard blow, 2.8 kPa) | 1.494 | 6.93 V | fine |
| ~7.4 V (≈4.5 kPa) | ~1.55 | **≈11.5 V** | **at the rail** |
| 8.28 V (5 kPa — ADR 0003's figure) | ~1.56 | **12.9 V** | **clipped** |
| 9.94 V (6 kPa full scale) | 1.586 | **15.8 V** | **clipped hard** |

So with `POT-RESP` at full CW the chain **rail-clips at roughly 4.5 kPa, and the gain
knob cannot prevent it** — that is the price of putting the stage ahead of the
attenuator, and it is the direct cost of the placement decision §4 argues for. Under
the asserted 2.8 kPa working point (F4) it never happens; under ADR 0003's 0–5 kPa it
happens in normal playing. The two disputed facts compound: **F4 is what makes F9
either a non-issue or a showstopper, and neither document resolves F4.**

§3's honest note — "the clip is a *rail* clip with no soft region, so it will sound
like a wall rather than compression" — applies here too and is not repeated.

---

## F10 — Whether hardware curve shaping exists, and which ADR owns it — **High**

`POT-RESP` is analog curve shaping in the signal path. The ADR that rejected the
fully-analog path lists curve shaping as one of the things that is **not recoverable in
hardware**:

> `docs/decisions/0003-breath-sensing-path.md`: "These are the reasons the fully-analog
> path was rejected, and **none of them are recoverable in hardware**:
> - **Curve shaping.** The previous firmware had `breath_gamma` and a `lin_to_log`
> mapping. This is the difference between a breath response that feels like an
> instrument and one that feels like a volume knob."
>
> "**Panel knobs (ADR 0006) handle *range fitting*; firmware handles *response feel*.**
> Different jobs, both kept."
>
> and later: "**Curve shaping on the breath output.** Genuinely lost — `breath_gamma`
> cannot apply to a signal firmware never touches."

> `docs/decisions/0006-cv-channel-allocation.md`: "**Firmware still shapes the response
> curve upstream of the DAC.** The knobs fit the *range* to the patch; the firmware
> shapes the *feel*."

against:

> `hardware/module/breath-output-stage.md` §4 title: "**Response control — `POT-RESP`,
> log ← linear → exp**" … "`B6` … found that the nearest commercial equivalent …
> ships Response — exp ↔ lin ↔ log … **This module has two knobs and no shaping at
> all.**"

The ADR 0006 sentence is doubly wrong: breath never reaches the DAC, so firmware cannot
shape the jack signal by that route either — which is what ADR 0003 says in its own
"what the analog path gives up" section, and which ADR 0006 does not reflect.

**No ADR owns `POT-RESP`.** All four new BOM rows (`POT-RESP`, `R-RESP`, `D-RESP`,
`U-RESP`) carry `adr` = **0006**. ADR 0006's decision table still reads:

> "\| **Breath** \| **analog, differential over the umbilical** \| 0–10V, **offsettable
> ±5 V** \| **GAIN 0.5–4×, OFFSET ±5 V** \| Trimmed \|"

— two panel controls, no response. A stage that consumes a package, a panel position,
a knob and the module's entire op-amp reserve is recorded only in a schematic page's
§4 and four BOM rows pointing at an ADR that does not mention it.

---

## F11 — Link CMRR with `R1b` fitted — **High**

Three numbers, two of them in the same section of the same file.

> `hardware/controller/carrier.md` §2: "Without it the link CMRR falls from **70.2 dB to
> 60.2 dB** `[calc, A2]` against an independently derived requirement of 58.5 dB:
> **1.7 dB of margin**"

> `hardware/controller/carrier.md` §2, twelve lines later:
> "> One correction to the receive page's own case for `R1b`: it claims the part buys
> > "fifty times" the rejection. **With `R1b` fitted the real floor is 73 dB**, set by
> > the 1 MΩ bias pair, so `R1b` buys about **13 dB**. Still worth fitting. The stated
> > reason overstates it."

70.2 dB and 73 dB are both stated as the with-`R1b` floor, in §2 of one page, twelve
lines apart. (60.2 + 13 = 73.2, so the correction box is self-consistent and the
earlier sentence is the stale one.)

**And the correction never reached the page it corrects.** `breath-receive-stage.md`
still reads, unchanged:

> "That is the **entire** 60 dB budget, spent by one unmatched resistor, with every
> other term still to come. **The 0.1 % module-side parts buy 94 dB and this throws
> away fifty times that.**"

The task brief records this as "corrected to ~13 dB". It was corrected in `carrier.md`
as a quoted rebuttal; the original stands verbatim in the receive page, which is the
page `carrier.md` cites as authoritative for this pair. Both the un-matched figure
(60.2 dB) and the matched figure's *derivation* do agree between the two pages —
only the conclusion drawn from them differs.

---

## F12 — Sensor full scale: 4.7 V or 4.80 V — **Medium**

| 4.80 V | 4.7 V |
|---|---|
| ADR 0003: "0–6 kPa … **~0.2–4.80 V** out" | ADR 0003, 420 lines later: "**The sensor reaches 4.7 V** while the ADC runs on 3.3 V" |
| ADR 0003 table: "Output span \| **0.2–4.80 V** \| **0.2–4.80 V**" | `bom.csv` `U-BREATH`: "identical transfer function (766mV/kPa, **0.2-4.7V**)" |
| ADR 0003: "To the umbilical buffer — full scale, **0.2–4.80 V**" | `bom.csv` `R-ADCDIV`: "**Sensor reaches 4.7V** into a 3V3 ADC" |
| `breath-output-stage.md`: "Sensor full scale (6 kPa) \| **4.800 V**" | `bom.csv` `D-TVS-BREATH`: "BREATH's normal top of range is **4.7V** against a 5V array's V_RWM — **300mV of margin**" |
| `breath-receive-stage.md`: "Sensor span, **0.2 → 4.8 V** \| 4.6 V" | `carrier.md` §2 drawing: "MPXV4006DP Vout **0.2 – 4.7 V**" |
| | `carrier.md` §2: "`full scale = 4.7 V × 0.6 = 2.82 V … 3502 counts`" |

**4.80 V is right**, from the transfer function ADR 0003 itself prints and verifies:
`Vout = VS × (0.1533·P + 0.04)` at VS = 5 V, P = 6 → **4.799 V**. `carrier.md` uses
0.766 V/kPa two lines below its own 4.7 V, which is self-inconsistent: `0.2 + 0.766 × 6
= 4.80`.

**What moves** `[calc]`, on the page that sizes the ADC:

```
divider full scale   4.80 × 0.6 = 2.88 V   (not 2.82)  → 87.3 % of 3.3 V  (not 85 %)
counts at full scale 3575                  (not 3502)
ESD clamp worst case (4.80 − 0.7)/10k = 410 µA (not 400) — still inside ±2 mA
D-TVS-BREATH margin  5.0 − 4.80 = 200 mV   (not 300 mV) on a 5 V array
```

Nothing breaks, but the TVS margin claim loses a third of its headroom and the ADC
count figures the whole §2 argument is stated in are 2 % out.

---

## F13 — `R-FB`: 40 kΩ or 40.2 kΩ — **Medium**

> `hardware/module/breath-output-stage.md`, ASCII circuit: "`├──[R-FB 40k]── (to −)`"

> `hardware/module/breath-output-stage.md`, Values table: "\| **R-FB** \| **40.2 kΩ
> 1 %** \| Fixed ×4. Same E96 part as `R-MODGAIN` \|"

> `hardware/bom.csv` `R-BREATH-SUM`: "**R-IN 10k, R-FB 40.2k.** Same E96 feedback part
> as R-MODGAIN"

The Values table and BOM agree on 40.2 kΩ. The drawing says 40 kΩ, and the **offset
table is computed at 40 kΩ** `[calc]`:

```
full CCW: −12/95.3k = −125.92 µA × 40.0k = 5.037 → +5.04 V  ← the page's figure
                                 × 40.2k = 5.062 → +5.06 V
full CW : +122.2 µA             × 40.0k = 4.888 → −4.89 V  ← the page's figure
                                 × 40.2k = 4.912 → −4.91 V
```

Also "`attenuation = 0.125 … 1.000 × fixed gain R-FB/R-IN = 4 = 0.5 … 4.0`" — at
40.2 kΩ the fixed gain is **4.02** and the range is **0.5025 … 4.02×**. Small, but the
page's "0.5× to 4×" is quoted as an exact bound in four other places
(`breath-receive-stage.md` commissioning, `bom.csv` `POT-GAIN`, ADR 0006's table, and
the ADR 0006 channel row).

---

## F14 — `POT-RESP`'s taper — **Medium**

> `hardware/module/breath-output-stage.md` §4: "`POT-RESP` **50 k lin** (same part as
> `POT-GAIN`)"

> `hardware/bom.csv` `POT-RESP`: "**50k linear**, 9mm vertical, centre detent …
> **Same part as POT-GAIN.**"

But `POT-GAIN`'s taper is explicitly undecided, and expected *not* to be linear:

> `hardware/bom.csv` `POT-GAIN`: "50k, **taper TBD at E10** … Taper is a feel question
> and therefore a bench question"

> `hardware/module/breath-output-stage.md`, Still open: "**`POT-GAIN`'s taper.**
> Linear gives a knob that does most of its work in the last quarter turn. **A log or
> pseudo-log taper** (or a second floor resistor across part of the track) is a feel
> question"

> `docs/decisions/0004-cv-interface-module.md`: "Alpha 9 mm vertical pots (**linear
> taper** — predictable for CV scaling)"

"Same part as `POT-GAIN`" and "linear" cannot both be satisfied once `POT-GAIN` goes
log at E10 — and `POT-RESP`'s whole centre-null property (`V_wiper = (V/2)(1 − 2p)`,
zero at `p = 0.5`) **requires a linear track**. On a log track the wiper at mechanical
centre sits around `p ≈ 0.1–0.2`, i.e. nowhere near the null, and the centre detent —
the feature the BOM row is written around — points at a non-linear part of the curve.
ADR 0004 meanwhile asserts all module pots are linear, which is already false for
`POT-GAIN`.

---

## F15 — Breath's reconstruction corner: ~2 kHz or ~480 Hz — **Medium**

Both in ADR 0006, 610 lines apart.

> `docs/decisions/0006-cv-channel-allocation.md`: "- **Breath wants a gentler filter**,
> **~2 kHz**. It is an inherently slow signal and **the steps should be smoothed in
> hardware**."

> `docs/decisions/0006-cv-channel-allocation.md`, filter table and note: "\| Breath \|
> 1 kΩ \| 330 nF film \| **~480 Hz** \| … Breath is the odd one because **it never passes
> through the DAC**: it has **no zero-order-hold image to attenuate**, and it is already
> a 482 Hz channel by the time it reaches the module. **This ADR's earlier "~2 kHz for
> breath" is superseded by that page.**"

The retraction names the exact sentence it supersedes and the sentence is still there.
"the steps should be smoothed in hardware" is also wrong on its own terms — there are
no steps on a path that never enters the DAC.

---

## F16 — Panel: two knobs / 107 mm, or three knobs / 97 mm — **Medium**

The 10HP decision landed in ADR 0004's derivation, `bom.csv` `PANEL`, `KNOB-BREATH` and
`README.md`'s comparison table. Four places still describe the two-knob panel, two of
them inside ADR 0004 itself — including the exact assertion ADR 0004 says is derived
nowhere:

> `docs/decisions/0004-cv-interface-module.md`, "Panel, top to bottom": "Connector,
> power switch and LED … **two breath knobs**, then six jacks in two columns … **Roughly
> 107 mm of ~110 mm usable** — full but workable."

> `docs/decisions/0004-cv-interface-module.md`, octave-switch section: "Plus a toggle
> on a panel **already at 107 mm of ~110 mm usable**."

> the same ADR, 150 lines later: "It also found that **this ADR's own "107 mm of
> ~110 mm usable" figure is asserted twice and derived nowhere** … Derived, finally:
> … **Total \| 97 mm against ~110 mm — 13 mm spare**"

Both assertions are still standing. Also:

> `README.md`: "- **Breath** — dedicated, 0–10V, **with panel knobs for gain and
> offset**"

> `ROADMAP.md` E12: "**10HP panel cut** … etherCON braced to the PCB — good practice
> **at 8HP** rather than the structural necessity it was at 6HP."
> `ROADMAP.md` verification table: "The etherCON flange against a **50.50 mm 10HP
> panel** … **Comfortable at 8HP**"

— ROADMAP states 10HP and 8HP in the same row, twice.

> `hardware/bom.csv` `KNOB-BREATH`: "Match the shaft of the **POT-BREATH variant**
> ordered" — `POT-BREATH` is not a reference in this BOM; the parts are `POT-GAIN`,
> `POT-OFFSET`, `POT-RESP`, which no longer share a taper (F14).

---

## F17 — The commissioning order — **Medium**

Four documents give a three-step order that does not include the new third knob.

> `hardware/module/breath-output-stage.md`, Still open: "**Commissioning order** is now
> **three steps, not two**: `TRIM-BREATH-ZERO` for the pedestal, then GAIN for the span,
> then OFFSET for where it rests."

> `hardware/module/breath-receive-stage.md`, Commissioning: "1. `TRIM-BREATH-ZERO` …
> 2. **Panel GAIN** for the span … 3. **Panel OFFSET** for where you want the jack to
> rest"

> `ROADMAP.md` E10: "**Set `TRIM-BREATH-ZERO` first** … **then gain, then the panel
> offset, in that order**"

> `docs/decisions/0006-cv-channel-allocation.md`: "**Order is gain first, then offset.**
> … The reverse ordering makes the two controls fight each other."

`POT-RESP` changes the stage gain by up to **1.586×** at the top of its range (§4's own
table), so it must be set **before** GAIN — otherwise turning RESP after GAIN rescales
the span GAIN was just set for, which is precisely the interaction the ordering rule
exists to prevent. None of the four documents was updated, and §4 does not state the
order either.

---

## F18 — The breath latency budget — **Medium**

`docs/reference/latency-budget.md` is the corrected, current version (482 Hz = 330 µs,
480 Hz = 332 µs, anti-alias 282 µs, SAR 24 µs, analog total ~2.83 ms + restrictor).
Two documents disagree with it, and one of them disagrees *about* it.

> `docs/decisions/0003-breath-sensing-path.md`, latency table: "\| SAR ADC conversion \|
> **~50–200 µs** \| … \| Op-amp and reconstruction filter \| **~160 µs** \| … \|
> **Total** \| **< 1.5 ms** \|"

— against `latency-budget.md`'s "**This row said 50–200 µs**, which is a generic SAR
allowance and not this part", its 632 µs of filter group delay on the analog path
("The filter line used to read '< 0.2 ms' and **it was the design's own specified
corners that broke it**"), and its ~2.83 ms / ~3.1 ms totals. ADR 0003's own prose
three paragraphs below its table already says "**~3.1 ms**", so the ADR contradicts
itself as well as the reference page. Its table also books "SPI to DAC over the
umbilical ~50 µs" and "DAC settling ~10 µs" **for breath**, a path breath does not
take.

> `hardware/controller/carrier.md` §2: "> **τ = 282 µs exceeds the 250 µs loop period …**
> `latency-budget.md` **and ADR 0003 book "SAR ADC conversion ~50–200 µs" and no RC term
> at all** `[repo]` … Found by `R10-keyscan-and-adc.md` §B-2 and **still unapplied**."

`latency-budget.md` carries "**Anti-alias filter, 564 Hz \| 282 µs \| … Omitted entirely
before**" and "SAR ADC conversion \| **~24 µs**". The fix **was** applied there; the
carrier's claim that it was not is itself the stale statement. ADR 0003 remains
unfixed, so the carrier note is half-right and cites the wrong half.

---

## F19 — Anti-alias attenuation: 58 dB at 500 kHz or 55 dB at 330 kHz — **Medium**

> `docs/decisions/0003-breath-sensing-path.md`: "A buck running at **500 kHz** sampled at
> 4 kHz folds to DC; at **498 kHz** it folds to **2 kHz**, and at **496.1 kHz** to
> **100 Hz — directly into the breath band** … 47 nF gives a ~564 Hz corner and **58 dB
> at 500 kHz**."

> `hardware/bom.csv` `C-AA-ADC`: "the '~600Hz, 58dB at 496kHz' note was **wrong twice
> over** - wrong corner, and **the R-78E5.0 switches at 330kHz not 496kHz**. **55dB at
> 330kHz.**"

> `hardware/controller/carrier.md` §2: "`attenuation at the R-78E5.0's ~330 kHz
> switching rate = 20·log10(330k/564) = 55 dB`"

The corner (564 Hz) is now consistent everywhere — that half of the fix landed. The
switching frequency did not: ADR 0003's entire worked aliasing example (500 / 498 /
496.1 kHz folding to DC / 2 kHz / 100 Hz) is built on a rate the BOM explicitly
retracts, and its 58 dB is the same arithmetic at the wrong frequency
(`20·log10(500k/564) = 58.9 dB`, vs 55.3 dB at 330 kHz). The *conclusion* — fit the cap
— survives; the numbers that justify it do not.

---

## F20 — `C_cm` tolerance — **Medium**

> `hardware/module/breath-receive-stage.md`: "**And `C_cm` needs a tolerance, which
> nothing specifies.** At ±5 % the common-mode capacitor mismatch alone gives ~46 dB;
> **±1 % is needed to clear 60.** **Specify ±1 % C0G** on the two 1.5 nF parts."

> `hardware/bom.csv` `C-FILT-BREATH`: "15nF C0G (diff) + **1.5nF C0G (cm x2)**" — note
> gives the 482 Hz derivation and the ×10 ratio rule, **and no tolerance.**

The page states the requirement and names the consequence of missing it (46 dB against
a 60 dB budget — worse than the `R1b` term the whole §"`R1` is a 1206, and it has a
twin" section exists to fix). The BOM row was updated on 2026-09-21 for the 482 Hz
figure and not for this. A ±1 % 1.5 nF C0G is also a non-trivial sourcing constraint
that nothing flags as `open`.

---

## F21 — The block diagrams the shaper was inserted into — **Medium**

The new stage sits between the in-amp and `POT-GAIN`. Neither drawing of that node was
updated.

> `hardware/module/breath-output-stage.md` §1, "The circuit": "`   from the INA828
> 0 … −4.7 V ──────[POT-GAIN 50k]────┤ +            │`" — the in-amp feeding the
> attenuator directly, with no shaper, 100 lines above §4's "Drawn here **between the
> in-amp and the gain attenuator**".

> `hardware/module/breath-receive-stage.md`, block: "`│  INVERTING gain + offset   │`
> `│  POT-GAIN (buffered        │` `│  attenuator) then          │` `│  POT-OFFSET
> summing        │` `│  TWO × ½ OPA2197 — one     │` `│  half cannot do both       │`"
> — four halves now, and a shaper between this block and the in-amp above it.

> `hardware/module/breath-receive-stage.md`, Still open: "**Drawn**, at last:
> `hardware/module/breath-output-stage.md`. GAIN 0.5–4× … **Two halves, which settles a
> count that was wrong twice.**"

Also `breath-output-stage.md` §1's input label "`0 … −4.7 V`" against §4's
"`(0…−9.94V)`" for the same node — the first is the playing range, the second full
scale, which is defensible, but they are 1 mm apart in the same document and neither
says which.

---

## F22 — The deleted breath presence comparator — **Medium**

`hardware/module/digital-and-supervision.md` says clearly:

> "## There is no presence detect either
> **Deleted** with the watchdog, and for converging reasons. Two versions were built …
> and one **watching the breath line through an LM311**. The second failed review three
> ways: its **threshold sat inside the breath signal's own range** …"

and then, in the same file, proposes and lists work for the deleted part:

> "### The obvious way to get the link coverage back, for no new parts
> `CLR` can be driven from **the presence comparator** instead of from a monostable.
> **It already reports** cable connected, far-end power, reference alive, sensor alive
> and both analog conductors intact"

> "## Still open
> - **The presence tap point**, above. It needs the one-line change described and a
> **corrected `R-PRESENCE` row**."
> - "**The threshold may sit inside the breath signal's own range.** The sensor is a
> *differential* part with its reference port open to the cavity, so negative
> differential pressure drives the output toward the detect threshold … it would present
> as `CLR` firing mid-phrase."
> - "- **A power-on reset RC on the '123's own `CLR`**" — the '123 is deleted in the
> same file.

`hardware/bom.csv` agrees the part is gone (`U-LVL-MOD`: "**The presence-gated OE is
deleted along with its comparator**"; `LED-PANEL`: "**that comparator is DELETED**";
`C-DECOUPLE`: "The two caps counted for the LM311 are removed - that part was
**DELETED**"). The Still-open list asks for a BOM row correction on a part with no BOM
row, and re-raises a breath-threshold defect as open on a circuit that does not exist.

---

## F23 — Hard blow at the in-amp: −4.69 V or 4.64 V — **Medium**

Same file, 220 lines apart, same quantity.

> `hardware/module/breath-output-stage.md` §1: "\| Hard blow, real playing (~2.8 kPa) \|
> 2.347 V \| **−4.69 V** \|" and "the stage's working input is 0 to about **−4.7 V** …
> Reaching 10 V at the jack from that needs **≈2.13×**"

> `hardware/module/breath-output-stage.md` §4: "\| hard blow \| **4.64 V** \| 2.32 V \|
> 115 µA \| 1.494 \|" and "`÷10:  hard blow 4.64 V at the in-amp`"

> `hardware/bom.csv` `R-RESP`: "targeting ~1.5x gain ratio at a hard blow (**4.64V at
> the in-amp**)"

`[calc]` `(2.347 − 0.200) × 2.1848 = 4.691` (raw gain) vs `× 2.16106 = 4.640`
(effective). **4.64 V is the correct one** — it is F2's derived-vs-underated split
again, reappearing at the working point. §1 also states the sensor as 2.347 V where
the transfer function gives `0.2 + 0.7665 × 2.8 = 2.346 V`; negligible.

Downstream: the "≈2.13×" panel-gain figure is `10/4.691`; at 4.64 V it is **2.155×**.

---

## F24 — Thermal drift: 20 mV or 23 mV, and at which node — **Low**

> `hardware/module/breath-receive-stage.md`: "Thermal drift afterwards is on the order of
> **20 mV in 10 V** over a full warm-up — a quarter turn if it ever bothers you. **That
> figure is unverified**"

> `docs/decisions/0003-breath-sensing-path.md`: "the MPXV4006DP's offset drifts roughly
> 0.5 mV/K, so a 20 K interior rise **moves the jack about 23 mV out of 10 V — 0.23 %**"

> `docs/decisions/0006-cv-channel-allocation.md`: "its drift is **~23 mV in 10 V** over a
> full warm-up: a quarter turn, once, if it bothers you at all."

Two of three say 23 mV; the schematic page says 20 mV. **All three are wrong about the
node** `[calc]`: `0.5 mV/K × 20 K = 10 mV at the sensor`; `× 2.161 = 21.6 mV at the
in-amp output`; `× 2.13 panel gain = 46 mV at the jack`, i.e. **0.46 %**, not 0.23 %.
All three sentences say "at the jack" / "in 10 V". With `POT-RESP` at full CW the
factor rises again by up to 1.0–1.5× depending on where the drift sits relative to the
knee.

---

## F25 — The CMRR requirement: 60 dB or 58.5 dB — **Low**

> `docs/decisions/0003-breath-sensing-path.md`: "roughly **19–34 dB against the 60 dB the
> scheme needs**"

> `hardware/module/breath-receive-stage.md`: "That is the **entire 60 dB budget**" and
> "**±1 % is needed to clear 60**"

> `hardware/controller/carrier.md` §2: "against an **independently derived requirement of
> 58.5 dB**: **1.7 dB of margin**"

The "1.7 dB of margin" claim depends on the requirement being 58.5 dB; at the 60 dB the
other two documents use, the un-matched case (60.2 dB) has **0.2 dB**. Neither figure is
derived in the corpus — `carrier.md` calls 58.5 dB "independently derived" and cites
`[calc, A2]`, a review document, not a corpus one.

---

## F26 — Raw gain vs effective gain in the `REF` trim arithmetic — **Low**

The receive page uses the effective gain (2.1611) for the span and the raw gain
(2.1848) for the trimmer, on the same page:

> "+0.437 V nulls the pedestal" — `0.200 × 2.1848 = 0.437`; with the bias divider it is
> `0.200 × 2.16106 = 0.432 V`.
> "which needs `REF` anywhere from **0.332 V to 0.826 V**" — raw; effective gives
> 0.329–0.817 V.

> `hardware/bom.csv` `TRIM-BREATH-ZERO`: "**+1.0V covers 0.458V** with margin" — raw
> (`1.0/2.1848`); effective gives **0.463 V**.

No decision changes (0 → +1.0 V covers the 0.152–0.378 V spec band either way) but the
same page derives its headline number one way and its trimmer the other.

---

## F27 / F28 — Two small internal drifts — **Low**

> `docs/reference/latency-budget.md`, table: "\| **Total** \| **~2.83 ms + restrictor**
> \|" vs the same page's prose: "the budget absorbs it: **2.80 ms against a 5 ms
> target**".

> `docs/decisions/0003-breath-sensing-path.md`: "it **absorbs the ~2.13× scaling stage**
> so net part count is flat or lower" — the in-amp's gain is 2.185 / 2.161 (F2); 2.13 is
> the *panel* gain at the 2.8 kPa working point (F4), a different quantity in a different
> stage.

---

## Facts asserted but never derived

| Fact | Asserted in | Status |
|---|---|---|
| **Real playing tops out at ~2.8 kPa** | `breath-output-stage.md` (cites ADR 0003), `carrier.md` (cites `breath-receive-stage.md`), `breath-receive-stage.md` (cites nothing) | **Not in ADR 0003**, which says 0–5 kPa. Circular citation; no measurement, no source. Sizes the panel gain range, the ADC count budget and `POT-RESP`'s knee. **The single most load-bearing underived number in this chain.** |
| **In-amp full scale −9.6 V** | `breath-receive-stage.md`, twice | Implies an effective gain of 2.087, which matches nothing. The correct derivation is on the same page. |
| **`POT-RESP`'s null is "set by the topology, not by resistor tolerance"** | `breath-output-stage.md` §4 | It is set by two resistor ratios (`2×10 k` divider, `R2/R1 = 1:2`) whose parts have no BOM row and therefore no tolerance (F7). |
| **§4's gain-ratio column (1.000 → 1.586) and `i_D` (0 → 291 µA)** | `breath-output-stage.md` §4, marked `[calc]` | No diode model, saturation current or ideality factor is stated anywhere, and 1N4148 datasheets were unreachable through three review waves per `carrier.md`. The whole "÷2 not ÷10" argument rests on the 0.6 V knee being a fixed number. |
| **The new stage's headroom** | nowhere | Never derived. §4 has no headroom section; §3's exists for the stage downstream of it. See F9 — it rail-clips around 4.5 kPa. |
| **`R-RESP` 15 kΩ** | §4, `bom.csv` `R-RESP` | Honestly marked "a first sizing … wants a bench pass with a real player, not a spreadsheet". Acceptable — but it is pinned to the 4.64 V hard blow, i.e. to the 2.8 kPa figure above. |
| **`POT-OFFSET`'s detent sits "~20°" off zero** | §4, `bom.csv` `U-RESP` | The +0.605 V voltage is reproducible `[calc]`; the 20° figure is not derived anywhere (it requires a rotation law for the pot, which is unspecified — and `POT-OFFSET`'s taper is unstated in the BOM row). |
| **The 58.5 dB link-CMRR requirement** | `carrier.md` §2 | Cited to a review document; the corpus elsewhere says 60 dB (F25). |
| **`Ro = 75.8 Ω` for the OPA2197** | `carrier.md` §2 | **Honestly flagged** by the page itself: "back-solved, not read … Confirm … before committing either network." No action needed. |
| **0.5 mV/K sensor offset tempco** | ADR 0003, `breath-receive-stage.md` | **Honestly flagged**: "That figure is unverified … nxp.com was unreachable." No action needed. |
| **ADR 0004's "107 mm of ~110 mm usable"** | ADR 0004, twice | **Self-flagged in the same ADR** as "asserted twice and derived nowhere" — and both assertions are still in the file (F16). |

---

## Verified consistent

These were checked across every corpus document that mentions them and agree, with
arithmetic reproduced where the corpus shows it.

| Fact | Agreeing documents | Check |
|---|---|---|
| **`R1b` is drawn** | `carrier.md` §2 (both legs drawn, `R1` and `R1b` labelled), `bom.csv` `R-SER-BREATH-INST` qty **2**, `breath-receive-stage.md` component table | **The fix landed.** BOM quantity now matches what is drawn — 2 drawn, 2 in the BOM. This was the specific defect raised. |
| **`R-ISO-REF` is drawn** | `carrier.md` §2 (`** WAS MISSING **`, feedback tapped at `VS`), `bom.csv` `R-ISO-REF` qty 1 "INSIDE THE LOOP", `breath-receive-stage.md` "goes inside the loop, with feedback taken at the sensor's `VS` pin" | **The fix landed**, including the "outside the loop costs 2 % of a ratiometric scale factor" reasoning, identically in all three. |
| **In-amp input polarity** | `breath-receive-stage.md` drawing (`BREATH → R3 → IN−`, `AGND → R2 → IN+`), its prose, its formula `Vout = −2.185·(V_BREATH − V_AGND) + V_REF`, `bom.csv` `U-DIFFRX` "BREATH drives IN-, AGND drives IN+" | The drawing now matches the text. Previously flagged as a showstopper mismatch; resolved. |
| **482 Hz differential pole** | `breath-receive-stage.md`, `bom.csv` `C-FILT-BREATH`, `carrier.md` §2, `latency-budget.md`, ADR 0006 | `1/(2π × 22 kΩ × 15 nF) = 482.3 Hz` ✓. All five give the same reason for it not being 531 Hz ("that assumed 20 kΩ … `R1b` makes both legs 11 kΩ"). **No "459 Hz" exists anywhere in the corpus.** |
| **In-amp gain chain** | `breath-receive-stage.md` derivation, `bom.csv` `R-GAIN-INAMP` | `1 + 50k/42.2k = 2.1848` ✓; `1M/(1M+11k) = 0.98912` ✓; `2.1848 × 0.98912 = 2.1611` ✓; `× 4.6 = 9.94 V` ✓; "0.6 % shortfall" = 0.59 % ✓ |
| **564 Hz anti-alias corner** | `bom.csv` `C-AA-ADC`, `carrier.md` §2 + component table, ADR 0003, `latency-budget.md` | `1/(2π × 6.0 kΩ × 47 nF) = 564.2 Hz` ✓; `10k ∥ 15k = 6.0 kΩ` ✓; `τ = 282 µs` ✓ (only the *attenuation* figure disputes — F19) |
| **`TRIM-BREATH-ZERO` range 0 → +1.0 V** | `breath-receive-stage.md` (with the 0.152–0.378 V spec-band reasoning in full), `bom.csv` `TRIM-BREATH-ZERO`, `R-TRIM-RANGE` | The earlier 0 → +0.6 V is retracted in both places with the same argument. |
| **`REF` from the LM317 5.21 V rail, never `VREFOUT`** | ADR 0003, `bom.csv` `TRIM-BREATH-ZERO`, `breath-receive-stage.md` drawing + prose, `pitch-stage.md` cross-reference | Four documents, same reason (the DAC's internal reference is disabled until firmware writes an enable). The "from `VREFOUT`" fossil is gone from the drawing. |
| **1 MΩ bias pair replaces the 100 kΩ pulldown** | ADR 0003, `breath-receive-stage.md`, `bom.csv` `R-BIAS-INAMP` | Consistent, including the 0.2 ppm sense-return argument. (ADR 0005 and ADR 0006 still reference the deleted part — F3.) |
| **`R-SER-BREATH-INST` is 1206 ≥250 mW** | `bom.csv`, `breath-receive-stage.md` | `(12 − 0.2)/1 kΩ = 11.8 mA`; `P = 139 mW` ✓ against an 0805's ~125 mW. Same arithmetic, same conclusion, both places. |
| **0.6× ADC divider, 10 k / 15 k, ≥10 k upper leg** | ADR 0003, `bom.csv` `R-ADCDIV`, `carrier.md` §2 | `15/(10+15) = 0.600` ✓; the 5 V-before-3V3 ESD-clamp reasoning is identical in all three. |
| **`C-OUT-BREATH` 330 nF film, jack side of `R-OUT-PROT`** | `breath-output-stage.md`, `bom.csv`, ADR 0006 filter table, `latency-budget.md` | `1/(2π × 1 kΩ × 330 nF) = 482 Hz` ✓ (quoted as "~480 Hz" in three places and "~482 Hz" in one — rounding, not a contradiction). Film-not-X7R and jack-side-not-op-amp-side agree everywhere. |
| **Panel is 10HP / 50.50 mm, three knobs at ≤14 mm** | ADR 0004's derived table, `bom.csv` `PANEL` + `KNOB-BREATH`, `README.md`, `ROADMAP.md` E12 | `(10 × 5.08) − 0.3 = 50.50` ✓; `3 × 14 + 2 × 3 = 48 mm` fits, `3 × 15 = 51 mm` does not ✓; `5 + 22 + 39 + 31 = 97 mm` ✓. The "16–20 mm knobs" claim is withdrawn in both ADR 0004 and the BOM. |
| **`POT-GAIN` attenuator 0.125 → 1.000** | `breath-output-stage.md`, `bom.csv` `POT-GAIN`, `R-GAIN-FLOOR` | `7.15/(7.15 + 50) = 0.1251` ✓ |
| **Offset legs from +5.21 V and −12 V** | `breath-output-stage.md`, `bom.csv` `R-BREATH-OFF` | 21.0 k / 95.3 k, the −12 V-is-acceptable-here argument (`40k/95.3k × 50 mV = 21 mV`, 0.21 % ✓) and the no-extra-op-amp-half claim all match. |
| **Sensor transfer function** | ADR 0003 | `VS × (0.1533·P + 0.04)` at 5 V → 0.7665 V/kPa, 0.200 V at zero ✓, 4.799 V at 6 kPa ✓ — internally verified in the ADR. (Which is what makes the 4.7 V figures wrong — F12.) |

---

## What to fix first

1. **F1** — settle the op-amp package count in one place, then propagate to
   `U-OPA-PITCH`, `U-RESP`, `C-DECOUPLE`, `power-entry.md`, `breath-output-stage.md`
   §Values and `breath-receive-stage.md`. Nothing can be ordered until this closes.
2. **F4** — decide whether real playing is 2.8 kPa or 0–5 kPa, in ADR 0003, with a
   derivation or a measurement. **F9, F23, the panel gain range, the ADC count budget
   and `R-RESP`'s sizing all hang off it**, and it is currently a citation loop.
3. **F2 / F3** — pick −9.94 V and 0 V, fix `bom.csv` `U-DIFFRX` (which is three
   revisions behind), and fix ADR 0005's and ADR 0006's rest-state claims.
4. **F7** — give §4's four resistors BOM rows and non-colliding designators before
   layout.
5. **F5** — three one-line deletions ("now that `REF` is grounded" × 3).
