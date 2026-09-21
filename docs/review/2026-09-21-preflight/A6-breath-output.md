# A6 — Breath gain / offset / response output stage

**Slice:** `hardware/module/breath-output-stage.md` — everything between the
INA828 output and the `BREATH` output jack.
**Reviewer:** cold. No prior review directory was opened. Sources read:
`hardware/module/breath-output-stage.md`, `breath-receive-stage.md`,
`pitch-stage.md`, `power-entry.md`, `docs/decisions/0003-breath-sensing-path.md`,
`0006-cv-channel-allocation.md`, `docs/reference/latency-budget.md`,
`config/figures.yaml`, `hardware/bom.csv`, and six banked datasheets.
**Date:** 2026-09-21.

## Provenance key

`[datasheet <doc> p.N]` read out of a banked PDF · `[datasheet … digitised]` read
off a vector plot in one, with the axis calibration stated · `[repo file:line]` ·
`[calc]` with the arithmetic shown · `[from memory]` · `[conjecture]`.

Every model result below comes from one script, `T2`/`T1` in the appendix, with
the diode taken from the **banked BAV99 forward curve**, not from an ideal-diode
assumption. Where a figure is sensitive to the diode law I give the bracket.

---

## 0. Headline

The page is unusually good and its two big judgements — *shaper before the gain
pot*, and *gain as a buffered attenuator rather than a feedback rheostat* — are
both right, and I confirm them with numbers they did not have. Three things are
wrong, and one of them changes the circuit.

| # | Node | Finding | Severity |
|---|---|---|---|
| **A6-1** | `RESP_MID` / `U-RESP` | **The §4 shaper delivers 1.29× at a hard blow, not the 1.494× its own table claims.** The table ignores the wiper's Thévenin resistance *and* the loading of the `V_in/2` divider by the 50 kΩ track, *and* uses a 0.6 V knee the banked diode curves do not support. Three errors, all in the same direction. | **High** |
| **A6-2** | `RESP_POS` | **"Mathematically linear in the middle, not approximately" is false as drawn.** The `+V_in/2` end is a 10 k/10 k divider with a 5 kΩ source impedance loaded by a 50 kΩ track, so the node is at 0.409·V_in, not 0.5·V_in, and the null lands at **α = 0.450 — 14.0° off centre** on a 280° track. That is the *same* defect the page mocks `POT-OFFSET` for, in the paragraph that claims immunity to it. | **High** |
| **A6-3** | `INAMP_OUT` | **The page's own two tables disagree about a hard blow: −4.69 V in §1, 4.64 V in §4.** −4.69 V is the in-amp's *raw* gain 2.18483; every other figure in the corpus uses the *effective* 2.16106. −4.69 V is the `−10.05 V` configuration `figures.yaml` forbids, at a different operating point, so the checker cannot see it. The derived `≈2.13×` working point is wrong with it; the right number is **2.16×**. | **High** |
| **A6-4** | `U-RESP`, `OFFSET_W` | **The page states, in two places, both that `POT-OFFSET`'s wiper needs no buffer and that it does.** §"Offset" says "does *not* need buffering … feel, not error" and tabulates centre = +0.07 V; the §4 sidebar quotes `A5` saying the same wiper is unbuffered and therefore sits at **+0.605 V**, 19° off. I verified `A5`: it is right. | **High** |
| **A6-5** | `U-RESP` | **The shaper does not need two op-amp halves.** Recast non-inverting it needs one, is *exactly* null at centre by topology, hits the 1.5× target with `R-RESP` unchanged at 15 kΩ, and **deletes `U-RESP` (a whole SOIC-8) from the BOM** while freeing the half `A5` needs. §5 below. | **High (improvement)** |
| **A6-6** | `POT-GAIN` | **"Linear gives a knob that does most of its work in the last quarter turn" is backwards.** `[calc]` Linear crowds the *first* (CCW) quarter: 8.78 / 4.28 / 2.85 / 2.14 dB per quarter. A log (A) taper makes it worse, not better. Linear is correct and the open item closes on paper. | Medium |
| **A6-7** | `R-FB` | The ASCII drawing says `R-FB 40k`; the values table says **40.2 kΩ**. The offset table (+5.04 / −4.89 V) is computed with 40.0 k. With the specified 40.2 k it is **+5.06 / −4.91 V**. | Medium |
| **A6-8** | `BREATH` | **`BREATH` names two different nets** — the umbilical conductor / in-amp input on the receive page, and the output jack here. In a netlist they short. §8. | Medium |
| **A6-9** | `POT-GAIN` | The "0.5× floor" is stated as exact. Both banked 9 mm pot sheets give **±20 % total resistance tolerance**, so the floor is **0.43× to 0.61×**. The 4× end *is* exact (the wiper is buffered, so full-CW attenuation is 1.000 regardless of track value). | Low |
| **A6-10** | `POT-RESP` | The centre detent is load-bearing here, and the only banked part that offers one is the Alpha `0C` suffix at **half the rotational life** — 5 000 vs 10 000 cycles `[datasheet RV09AF-40 p.1]`. The Song Huei R0904N that Thonk actually ships **has no click option at all** `[datasheet R0904N p.1, R0904N-thonk p.1]`. Sourcing risk on a control whose whole argument is "the null is findable in the dark". | Medium |
| **A6-11** | `BREATH_CV` | `C-OUT-BREATH`'s stated job is "reconstruction". **Breath never passes through the DAC**, so there is no ZOH image to reconstruct. Its 330 nF costs 332 µs of group delay — the largest *controllable* term in a 2.83 ms budget `[repo docs/reference/latency-budget.md:42-45]`. 10 nF keeps the RF shunt and returns 322 µs. | Medium (proposal) |
| **A6-12** | — | **ADR 0003 argues that curve shaping is a reason to digitise, and then routes breath around the DAC** — so firmware's `breath_gamma` can never reach the jack. That is a far better argument for `POT-RESP` than "ADDAC310 has one", and the page does not make it. | Low (strengthening) |
| **A6-13** | `INAMP_OUT` | `2.8 kPa` is cited to ADR 0003 **twice on this page**; ADR 0003 does not contain it `[repo grep: the only "2.8" in that file is "2.83 mL" of tube volume, line 262]`. `figures.yaml` already files this as `breath-working-point: DISPUTED`; the page cites the disputed figure as settled. | Medium |

---

## 1. The seven open items, answered

### 1.1 "Where it inserts." — **Confirmed as drawn: between the in-amp and `POT-GAIN`. This is now decided, not open.**

The page's reasoning is right and I can put a number on it. The diode knee is
fixed in *volts*; what makes it a fixed fraction of *breath* is that the signal
feeding the shaper has a scale set only by the in-amp.

Put the shaper after `POT-GAIN` and its input is `a·V_in` with
`a = 0.125 … 1.000`, so the knee pressure moves by exactly the gain range, 8:1:

```
[calc]  knee drive ≈ 2·V_f ≈ 1.0 V at the shaper input
        after POT-GAIN:  |V_in| at the knee = 1.0/a
          a = 1.000  ->  |V_in| = 1.00 V  ->  P = 0.60 kPa
          a = 0.125  ->  |V_in| = 8.00 V  ->  P = 4.83 kPa
        1.65644 V per kPa at the in-amp  [calc: 2.16106 x 0.7665]
```

At the bottom of the gain knob the knee would sit at **4.83 kPa — above every
candidate for a hard blow, including the 4 kPa upper candidate in
`figures.yaml:breath-working-point`.** The control would do nothing at low gain
and everything at high gain. Decisive.

A third position nobody wrote down — **after the summer** — is worse still: the
curve would then depend on the OFFSET knob as well, and the shaper would bend
the *pedestal* rather than the signal. Rejected for the record.

A fourth — **in firmware** — is unavailable, and that is worth stating because
it is the strongest argument for the whole section (A6-12): breath is analog end
to end and touches no DAC channel `[repo hardware/module/breath-receive-stage.md,
"What the jack does on a CLR"]`, so `breath_gamma` shapes the *digital copy*
only. ADR 0003 lists curve shaping first among the things digitising buys, and
then routes the CV around the part that could deliver it. `POT-RESP` is the only
way the promise reaches the jack. **Put that argument on the page in place of the
ADDAC310/NuEVI comparison**, which is evidence that the feature is normal, not
evidence that this design needs it.

### 1.2 `R-RESP` — **15.0 kΩ, final, in the recast topology of §5. Not a bench question.**

`[calc, banked diode curve]` With the non-inverting recast, at a 2.8 kPa hard
blow (`|V_in|` = 4.638 V):

| `R-RESP` | gain ratio, full CW (exp) | full CCW (log) |
|---|---|---|
| 10.0 kΩ | 1.78 | 0.74 |
| **15.0 kΩ** | **1.51** | **0.78** |
| 22.0 kΩ | 1.36 | 0.81 |

15.0 kΩ hits the page's stated ~1.5× target on the nose. **It is insensitive to
the thing the BOM was worried about**: across a 0–40 °C body the ratio moves
1.489 → 1.514, **±0.8 %** `[calc, V_f tempco −2.2 mV/K, §4.1]`, and across the
full plausible diode-law bracket (ideal n = 1 to n = 1.9) it moves 1.51 → 1.53.
The `D-RESP` BOM row's "the 0.6 V knee this shaper depends on is NOT-IN-DOCUMENT"
is a correct provenance complaint with **no design consequence** — once the diode
conducts, `R-RESP` sets the current, not `V_f`. Record that, and close it.

`R-RESP` = **15.0 kΩ 1 % 0805**, E96, unchanged in value and changed in status
from "first sizing" to derived.

*(If the stronger curve of §4.3 is adopted, `R-RESP` becomes 10.0 kΩ. Both
values are E96 and both are derived; the choice is §4.3's, not §1.2's.)*

### 1.3 Diode matching — **the second diode earns its place, and for a reason the page does not give.**

The page's reason (power-on and fault excursions) is real but weak: the branch
is behind 15 kΩ and clamped by the op-amp's own input structure.

The reason that matters is that **breath is unipolar but the shaper is not.**
Full CCW is the *log* half, and there the branch current reverses — the wiper
sits on the op-amp output side of the null and pulls the other way. Without the
antiparallel partner the CCW half of the knob would do nothing at all. That is
not a fault case; it is half the control.

`[calc]` At full CCW, hard blow, the branch carries **−51.8 µA through the second
diode**, against +117.0 µA through the first at full CW. Both legs conduct in
normal play, at every knob position off centre.

So: **keep both, and correct the reason.** They do not need to be *matched* —
nothing compares them — but they should be the same part number so the two
halves of the knob feel the same.

### 1.4 `POT-GAIN` taper — **linear (taper B). Closed on paper; do not spend E10 on it.**

The page's premise is factually backwards. With `R-GAIN-FLOOR` = 7.15 kΩ under a
50 kΩ track and a fixed ×4, attenuation is *linear in rotation* from 0.1251 to
1.000, so gain is linear in rotation from 0.5× to 4×:

```
[calc]  G(u) = 4 x (7.15 + 50u)/57.15
   u = 0      0.500x    -6.01 dB
   u = 0.25   1.375x    +2.77 dB      +8.78 dB in this quarter
   u = 0.50   2.250x    +7.04 dB      +4.28 dB
   u = 0.75   3.125x    +9.90 dB      +2.85 dB
   u = 1.00   4.000x   +12.04 dB      +2.14 dB
```

The crowding is at the **CCW** end, not the CW end. And a log (A) taper — the
obvious "fix" — is worse: `[calc, classic 10 %-at-50 % two-segment A law]`
+2.60 / +2.00 / **+9.10** / +4.35 dB per quarter, a 4.6:1 spread against
linear's 4.1:1, with the crowding moved to the third quarter where the knob is
actually used.

Two further arguments for linear:

- **The working point lands at 47.5 % of rotation** with a linear taper
  `[calc, 2.16× at a = 0.5403]` — dead centre. With an A taper it lands at
  **70.8 %**, pushed toward the end stop, which is exactly the complaint the open
  item was raised about.
- `R-GAIN-FLOOR` is what makes linear tolerable, and this is worth saying
  because it looks like a mute-prevention part and is also a taper part. Without
  it, `G = 4u`, whose dB-per-degree is unbounded at the CCW end.

**`POT-GAIN`: 50 kΩ, taper B (linear).** Order code `…-B50K`. The RV09 datasheet
confirms B = Linear and, separately, warns that **the `A`/`B` in `RV09A`/`RV09B`
is the rotational angle (280° vs 300°), not the taper** `[datasheet RV09AF-40
p.1–2]` — `bom.csv` already carries that trap; the schematic page does not.

### 1.5 `POT-OFFSET` centre detent — **no detent. Buffer the wiper instead.**

The detent is the wrong fix for the problem it is being asked to solve, and the
page contains both halves of the contradiction (A6-4). Verified arithmetic, with
the values table's `R-FB` = 40.2 kΩ:

```
[calc]  i(-12 V leg) = -12 / 95.3k                        = -125.918 uA
        buffered wiper, centre:  i = 2.605/21.0k          = +124.048 uA
            V_jack = -40.2k x (124.048 - 125.918) uA      =   +0.075 V
        unbuffered wiper, centre:  R_th = 10k/4 = 2.50k
                          i = 2.605/(21.0k + 2.50k)       = +110.851 uA
            V_jack = -40.2k x (110.851 - 125.918) uA      =   +0.606 V
        true zero, unbuffered, at p = 0.5669
            = 6.69 % of rotation past centre
            = 18.7 deg on a 280 deg RV09A   /  20.1 deg on a 300 deg RV09B
```

`A5`'s +0.605 V and "~20°" are **confirmed**. +0.606 V is 6 % of a 10 V span
standing at the jack with the knob at its detent — into a VCA that is a note
that never closes.

So a detent at mechanical centre would be a detent **19° away from the thing it
is supposed to find**, which is worse than no detent: it would be authoritative
and wrong. And it costs half the pot's life — **5 000 cycles with the click
against 10 000 without** `[datasheet RV09AF-40 p.1, "Rotation Life: With click:
5,000 cycles, without click: 10,000 cycles"]` — on the knob a player moves most.

**Buffer the wiper** (one op-amp half, freed by §5) and the centre becomes
+0.075 V, 0.75 % of span, and then a detent would be honest. I still would not
fit one: 5 000 cycles on a performance control is about 2–3 years of daily use,
and with the wiper buffered the offset is a smooth, findable zero anyway.

**`POT-OFFSET`: 10 kΩ, taper B (linear), no click, wiper buffered.**

Two smaller things fall out:

- The page's rail-sensitivity paragraph analyses **one of the two legs.** The
  −12 V leg gives `40.2k/95.3k = 0.422` `[calc]`, i.e. 21.1 mV per 50 mV — the
  page's 21 mV, confirmed. The +5.21 V leg gives `p × 40.2k/21.0k = 0.957` at
  centre `[calc]`, **2.3× more sensitive**, and is not mentioned. It is still
  fine (the LM317's line regulation is 0.52 mV/V `[repo
  config/figures.yaml:dac-rail derivation context]`), but the paragraph should
  say so rather than leave a reader to find the bigger term.
- The offset range with the specified 40.2 kΩ is **+5.06 / −4.91 V**, not
  +5.04 / −4.89 (A6-7). The endpoints are exact regardless of buffering and
  regardless of the pot's ±20 % tolerance, because the wiper is at a rail end.

### 1.6 The extra inversion — **polarity is correct as drawn, and the invariant needs writing down.**

Chain from the in-amp output to the jack, as the page draws it:

```
[repo hardware/module/breath-receive-stage.md + breath-output-stage.md]
  in-amp out          0 -> -4.64 V   (negative-going: BREATH on IN-)
  shaper /2 inverting 0 -> +2.32 V
  restore x2 inverting 0 -> -4.64 V
  POT-GAIN attenuator  (no inversion)
  gain buffer          (no inversion)
  summer x4 inverting 0 -> +10 V at the jack        POSITIVE-going   OK
```

Three inversions. **The invariant is: the number of inverting stages between the
in-amp output and the jack must be ODD**, because the in-amp itself was
deliberately made inverting (`BREATH` on IN−) to suit an inverting downstream
stage — a decision whose original justification was deleted and which
`breath-receive-stage.md` explicitly re-grounds on this very topology.

That invariant is the thing to put on the page, because the *obvious*
optimisation — delete the restore half — silently breaks it. The recast in §5
keeps it (one added non-inverting block, one inversion total), which is the
point of the recast.

### 1.7 Commissioning order — **four steps, not three, and the page's "three, not two" is already stale by its own §4.**

```
1.  TRIM-BREATH-ZERO          internal, once at build, no breath:
                              INAMP_OUT = 0.000 V
2.  RESPONSE to centre detent PRECONDITION, not a step. At centre the shaper
                              is exactly unity; set anywhere else, step 3 is
                              being set against a curve that will move.
3.  Panel GAIN                span. Working point 2.16x  [calc, not 2.13x]
4.  Panel OFFSET              rest point. Independent of 2 and 3.
```

And the honest addition the page owes the player: **RESPONSE is not
level-compensated.** Sweeping it from full CCW to full CW multiplies a hard blow
by `1.505 / 0.777 = 1.94×` `[calc]`, so GAIN has to be re-trimmed after it. The
dependency graph is `ZERO → {RESPONSE ↔ GAIN} → OFFSET`, and the page currently
implies all three panel knobs are independent. Only OFFSET is.

---

## 2. The knee — the actual transfer curve

### 2.1 What the banked documents say `V_f` is

The page assumes **0.6 V**, hard. No banked document supports that at the
currents this circuit uses.

| Source | What it gives | Provenance |
|---|---|---|
| NXP 1N4148/1N4448 Fig. 3 | typical 25 °C curve, **linear axes, 0–600 mA** — the lowest plotted point is 0.608 V at 1.42 mA | `[datasheet 1N4148.pdf p.4, digitised: x 348.23 px = 0 V at 80.28 px/V, y 338.89 px = 0 mA at 3.7369 mA/px]` |
| NXP 1N4448 EC table | 0.62–0.72 V at **5 mA** — the only *specified* low-current bound in the bank | `[datasheet 1N4148.pdf p.3]` |
| Vishay BAV99 Fig. 1 | **log-current axis from 0.01 mA**, 25 °C and 100 °C curves — the only banked plot that reaches our operating range | `[datasheet BAV99.pdf p.2, digitised: x 97.65 px = 0 V at 74.85 px/V, y 409.3 px = 0.01 mA at 27.02 px/decade; calibration taken from the axis-label bounding boxes, and the 1.0 V label checks to 0.05 px]` |
| Vishay BAV99 / Diotec 1N4148W EC | max 0.715 V at 1 mA, 0.855 at 10 mA | `[datasheet BAV99.pdf p.2]`, `[datasheet 1N4148W-DIOTEC.pdf p.2]` |

Digitised BAV99 25 °C curve, which is what my model uses:

```
   10 uA  0.399 V      100 uA  0.553 V      1 mA  0.721 V
   20 uA  0.444 V      150 uA  0.581 V     10 mA  0.915 V
   50 uA  0.503 V      200 uA  0.602 V
```

**Two honest caveats, stated because the figure is load-bearing.**
(i) Vishay's own typical curve reads *above* its own guaranteed maximum at 1 mA
(0.721 V plotted against 0.715 V specified), so the plot is indicative, not
authoritative — I treat it as a pessimistic typical.
(ii) Its implied slope is ~162 mV/decade, steeper than an ideal junction. I
cross-checked with an independent bracket (Shockley anchored on the NXP Fig. 3
point, n = 1.0 and n = 1.9): that bracket gives 0.48–0.54 V at 100 µA against the
BAV99 curve's 0.553 V. **All three sources agree the knee is 0.44–0.56 V in the
20–150 µA window, not 0.6 V.** The design answers below move by under 2 % across
that whole bracket, which is the real point.

**Temperature.** The 25 °C and 100 °C curves in the same figure are separated by
**167 mV over 75 K = −2.2 mV/K** `[datasheet BAV99.pdf p.2, digitised]` — the
textbook value, and a good independent check that the axis calibration is right.

### 2.2 The circuit as drawn, solved exactly

The §4 table is built on three simplifications, all optimistic:

1. **The `V_in/2` divider is loaded by the 50 kΩ track**, whose far end is at
   `−V_in/2`. At full CW the wiper *is* that node, so the branch current is drawn
   straight out of it as well.
   `[calc]` node = **0.328·V_in** at full CW, not 0.5·V_in.
2. **The wiper has a source impedance** that the table takes as zero.
3. **`V_f` = 0.6 V**, ~80 mV too high at these currents.

Exact solution, banked diode, `R-RESP` = 15 kΩ, hard blow `|V_in|` = 4.638 V:

| Dynamic | `|V_in|` | page's table | **exact, as drawn** |
|---|---|---|---|
| *pp* | 1.00 V | 1.000 | **1.073** |
| *mp* | 2.50 V | 1.347 | **1.219** |
| *mf* | 3.50 V | 1.438 | **1.261** |
| **hard blow, 2.8 kPa** | 4.638 V | **1.494** | **1.289** |
| full scale, 6 kPa | 9.939 V | 1.586 | **1.342** |

Note the *pp* row: the page has it at exactly 1.000 because 0.50 V is below its
assumed 0.6 V knee. With the real curve the diode is already passing 3.65 µA
there `[calc]`, so **"below the knee — exactly linear" is not true either** — the
bend starts lower and softer than the page says. That is a point in the design's
favour and against the page's description of it.

**The "fully exponential" end of the knob delivers 29 % of extra gain where the
page promises 49 %** — 41 % short of its own target. To reach 1.5× *in the drawn
topology* `R-RESP` would have to come down to about **6.0 kΩ** `[calc]`.

And the null, solved for the wiper voltage crossing zero:

```
[calc]  null at alpha = 0.4500  ->  14.0 deg off centre on a 280 deg track
        with the pot's +/-20% tolerance:  40k -> 17.5 deg, 60k -> 11.7 deg
```

So the claim "unlike `POT-OFFSET` … this null is set by the topology, not by
resistor tolerance" is **doubly wrong as drawn**: the null is 14° off *and* it
moves 6° with the pot's tolerance.

Mitigating, and worth recording so the page is not over-corrected: because the
diode's own turn-on swamps a 0.21 V residue at the wiper, the stage at mechanical
centre is still linear to within **0.02 %** `[calc, ratio 0.9998 at α = 0.50]`.
The *detent is linear*; it is the *symmetry* that is broken — the exp half gets
45 % of the rotation and the log half 55 %.

### 2.3 The recast fixes it and the 15 kΩ becomes right

See §5 for the circuit. With it, at a 2.8 kPa hard blow and `R-RESP` unchanged:

| | full CW (exp) | centre | full CCW (log) |
|---|---|---|---|
| 0 °C | 1.489 | 1.0000 | 0.783 |
| **25 °C** | **1.505** | **1.0000** | **0.777** |
| 40 °C | 1.514 | 1.0000 | 0.773 |

Null at β = 0.500 **exactly**, independent of every resistor value and of the
pot's ±20 % track tolerance, because the pot spans AGND to the op-amp output and
the op-amp holds its own (−) node at half that.

### 2.4 Where the knee lands, against real playing

```
[calc]  the branch turns on when the wiper-to-node drive reaches ~V_f,
        i.e. when |V_in|/2 = 0.44...0.56 V, i.e. |V_in| = 0.9...1.1 V
        1 uA onset:  0.32 kPa (n=1.9 bracket) ... 0.53 kPa (n=1.0 bracket)
```

| hard-blow candidate (`figures.yaml:breath-working-point`) | knee as a fraction of it |
|---|---|
| 2.8 kPa (what the page asserts) | **11–19 %** |
| 3–4 kPa (published wind-controller figures) | 8–18 % |
| 5 kPa (ADR 0003's "0–5 kPa") | 6–11 % |

**The page's ÷2 decision is confirmed and is robust across the entire disputed
range.** It only breaks if a hard blow is below ~1.2 kPa, which no candidate is.
The ÷10 pass it rejected would have put the knee at 3.0–5.3 kPa — the page was
right and for the right reason.

Two corrections to the words around it: the knee is at **11–19 % of a hard blow,
not "about a quarter"**; and the failure it avoided is not "does nothing until
you overblow" but "does nothing at all", since 5.3 kPa is above the sensor's own
working range once the in-amp clips.

### 2.5 The thing nobody has noticed: most of the knob is level, not shape

`[calc]` Normalise each knob position to the same peak — which is exactly what a
player does when they re-trim GAIN after moving RESPONSE — and ask how far the
curve departs from a straight line:

| | gain ratio at a hard blow | max departure from linear, after normalising | at mid-dynamic (1.4 kPa) |
|---|---|---|---|
| full CW (exp) | 1.505 | **−5.1 % of full scale** | −0.74 dB |
| full CCW (log) | 0.777 | **+3.8 %** | +0.52 dB |
| **total sweep** | 1.94× | ~9 % | **1.26 dB** |

**The 1.0 → 1.6 gain-ratio table in §4 is mostly a volume knob.** The actual
*shape* authority, once level is taken out, is about 1.3 dB at mid-dynamic. For
comparison, firmware's `breath_gamma` over 0.5–2.0 spans roughly 19 dB at the
same point `[calc, 0.707 vs 0.25 of full]`.

That is not a reason to delete `POT-RESP` — 1.3 dB of curve at mid-dynamic is
audible on a VCA and this is the only shaping the *jack* can ever have (§1.1).
It is a reason to state honestly what the control does, and to take the free
improvement below.

### 2.6 The free improvement: two diodes per leg, not one

The bend is weak because the knee is low (11–19 % of the range), so almost all of
the playing range sits on the steep segment, and normalising the peak flattens
it. **Raise the knee and the same gain ratio buys twice the shape.** Two diodes
in series per leg doubles the knee and costs nothing else:

| diodes per leg | `R-RESP` | ratio at a hard blow | knee | max departure | mid-dynamic sweep |
|---|---|---|---|---|---|
| 1 | 15.0 kΩ | 1.505 | 0.32–0.53 kPa | −5.1 % / +3.8 % | 1.26 dB |
| **2** | **10.0 kΩ** | **1.513** | **0.62–1.03 kPa** | **−10.4 % / +6.1 %** | **2.88 dB** |
| 3 | 15.0 kΩ | 1.229 | 0.93–1.54 kPa | −7.5 % / +4.5 % | 2.16 dB |

(Ratios, departures and the lower knee figure are on the banked BAV99 curve; the
upper knee figure is the Shockley `n = 1.0` end of the §2.1 bracket, which is the
pessimistic side for this question.)

Same headline gain ratio. **2.3× the shape.** Knee at 22–37 % of a hard blow —
which is precisely where the page *says* it wants it.

And the part is already in the BOM. **`BAV99` is two diodes in series in one
SOT-23** `[datasheet BAV99.pdf p.1, "Small Signal Switching Diode, Dual in
Series" / "Connected in series"]`. Two of them, antiparallel, pin 1 → pin 2 each,
is the whole network in two SOT-23s of a part the module already buys eight of.

**Recommendation: `D-RESP` = 2 × BAV99, antiparallel, `R-RESP` = 10.0 kΩ.** This
also deletes the unresolved `1N4148W` footprint question the BOM records — that
Vishay's part is SOD-123 and Diotec's same-order-code part is SOD-123F, a
different footprint `[datasheet 1N4148W-DIOTEC.pdf p.1; MANIFEST notes]`. One
fewer line item, one fewer manufacturer to pin.

Tempco check on the stronger version: 1.471 (0 °C) → 1.538 (40 °C), **±2.3 %**
`[calc]`. Still nothing.

---

## 3. Impedance — both claims verified

### 3.1 `POT-GAIN`'s wiper must be buffered — **confirmed, and the page understates it**

`[calc]` Unbuffered, the wiper drives `R-IN` = 10 kΩ directly. The wiper's
Thévenin resistance against the track is `R_th(u) = (R_below + R_FLOOR) ‖
(R_above)`, maximum near mid-rotation:

```
   full CCW     R_th = 7.15k ‖ 50k  = 6.26 kOhm  ->  gain error 38.5 %
   u = 0.5      R_th = 32.15k ‖ 25k = 14.06 kOhm ->  gain error 58.4 %
   full CW      R_th = 57.15k ‖ 0   = 0          ->  gain error 0
```

This is not a trim error, it is a **rotation-dependent 0–58 % gain error** that
also makes the taper law meaningless. The buffer is mandatory. The page says so;
it is right; the numbers make it unarguable.

There is a second reason the page does not give: unbuffered, `R-IN` loads the
track and the *attenuation law itself* stops being linear in rotation, so
§1.4's taper answer would not hold either.

### 3.2 `POT-OFFSET`'s wiper "does not need buffering" — **refuted, by the page's own sidebar**

§1.5. Endpoints exact, centre **+0.606 V**, true zero 18.7° off. Buffer it.

I checked the two no-buffer escapes:

- **Lower the pot.** A 1 kΩ `POT-OFFSET` gives `R_th,max` = 250 Ω and a centre
  error of **+0.134 V** `[calc]` — 1.3 % of span, detent ~4° off. Better, not
  fixed, and it costs 5.2 mA of standing current on the LM317 5.21 V rail
  against 0.52 mA today.
- **Raise `R-OFF`/`R-OFFNEG`.** Cannot: `R-FB` is fixed by the signal gain, so
  scaling the offset legs up scales the ±5 V range down proportionally.

**Buffer it. One half, and §5 provides it.**

### 3.3 What the stage presents to the jack, and what it can drive

`R-FB` is taken from the **op-amp output**, not the jack — unlike the pitch stage
`[repo hardware/module/pitch-stage.md:208]` — so `R-OUT-PROT` is *outside* the
loop and the jack's source impedance is a flat **1.000 kΩ**.

```
[calc]   one 100k Eurorack input       x0.9901   -0.99 %
         two on a passive mult (50k)   x0.9804   -1.96 %
         three on a mult    (33.3k)    x0.9708   -2.92 %
         a 10k input                   x0.9091   -9.09 %
```

**A passive mult is fine for breath**, and the page should say so explicitly,
because ADR 0006 says the opposite for pitch (−23.5 cents/octave on two
destinations `[repo docs/decisions/0006-cv-channel-allocation.md:518]`) and a
reader will carry that rule across. On pitch, 2 % is musical; on breath it is
one-tenth of a turn of the GAIN knob.

- **Drive:** `I_SC` = ±65 mA `[datasheet OPA2197.pdf p.8]`. Into a dead short at
  the jack the op-amp sources `11.1 V / 1 kΩ` = **11.1 mA**, 5.9× inside the
  limit. `R-OUT-PROT` then dissipates **123 mW** `[calc]` — well under the
  0.66–1 W the BOM now specifies, and not the worst case (output-to-output
  patching on pitch is, at 322 mW).
- **Capacitive load:** the op-amp sees only `R-FB`, `R-OUT-PROT` and
  `D-JACK-CLAMP` (BAV99, `C_D` 1.5 pF max `[datasheet BAV99.pdf p.2]`) — a few
  pF. `C-OUT-BREATH`'s 330 nF is on the **jack** side of the 1 kΩ and outside
  the loop, so the OPA2197's 1 nF limit `[datasheet OPA2197.pdf p.1 and §7.3.5
  p.22]` is never approached. **Confirmed safe**, and the mechanism is the 1 kΩ,
  so the "jack side, never the op-amp side" note in `bom.csv` is the load-bearing
  one.
- **The output pole barely moves with load:** 482.3 Hz open, 487.1 Hz into one
  input, 496.8 Hz into three `[calc]`.

### 3.4 `C-OUT-BREATH` — the cap is filtering something that does not exist

`[repo hardware/bom.csv:63]` calls it the "Breath output **reconstruction**
cap". There is nothing to reconstruct: breath never passes through the DAC
`[repo hardware/module/breath-receive-stage.md]`, so there is no ZOH image on
this channel — which `bom.csv`'s own `C-FILT-MOD` row states correctly in the
next breath ("FOUR not five: breath does not pass through the DAC").

What it costs: **332 µs of DC group delay**, already booked in
`[repo docs/reference/latency-budget.md:43]`, and it is the **largest term in
that 2.83 ms budget that the design actually controls** — the 1.17 ms tube and
the ~1 ms transducer are not negotiable.

```
[calc]  330 nF x 1k  ->   482.3 Hz,  330 us
         10 nF x 1k  -> 15 915   Hz,   10 us
```

The signal is already band-limited to 482 Hz differentially ahead of the in-amp
`[repo hardware/module/breath-receive-stage.md, C_diff]`, so the second pole adds
delay and almost no band-limiting. 10 nF C0G keeps a hard RF shunt at the
connector — the same value and the same job as `C-FILT-PITCH`.

**Proposal, for ADR 0006 rather than for this page unilaterally: reduce
`C-OUT-BREATH` to 10 nF and return 322 µs — 11 % of the whole breath
latency budget — to the instrument's primary expressive control.**

---

## 4. Headroom — where it clips, and whether to constrain the panel

### 4.1 The rails, which the page asserts and does not derive

The page says "the OPA2197 stops at about ±11.5 V". Derived:

```
[calc]  MODULE ANALOG +12V = Eurorack +12 V - D1 (1N5817) - FB1 DCR
        nominal 12.00 V - ~0.18 V at the ~50 mA analog load  = 11.82 V
        Eurorack -5 % = 11.40 V - 0.18 V                     = 11.22 V
  [datasheet OPA2197.pdf p.8]  V_O from rail, R_L = 10 kOhm: 95 mV typ / 125 mV max
        effective load here = R-FB 40.2k || (1k + 100k) = 28.8 kOhm, i.e. lighter
```

| | clip at the op-amp output |
|---|---|
| nominal rails | **±11.70 V** |
| Eurorack at −5 % | **±11.10 V** |

**±11.5 V is between the two and is not either of them.** This should be a
tracked figure with an owner, because four numbers below are derived from it.

### 4.2 Where it clips

`[calc]` Maximum panel GAIN that passes a 2.8 kPa hard blow without clipping,
against the −5 % worst case:

| RESPONSE | OFFSET +5.06 V | OFFSET centre | OFFSET −4.91 V |
|---|---|---|---|
| full CCW (log) | 1.68× | 3.06× | 4.45× (knob tops out first) |
| **centre (linear)** | **1.30×** | **2.38×** | **3.45×** |
| full CW (exp) | 0.87× | **1.58×** | 2.29× |

And the page's own example, corrected: GAIN 4× with OFFSET +5.06 V clips at
**0.91 kPa — 33 % of a hard blow** `[calc]`, not merely "at a hard blow". With
RESPONSE also full exp, **0.61 kPa, 22 %**.

Three things follow that the page does not say:

1. **GAIN alone clips.** At OFFSET centre the ceiling is **2.38×**, so
   the top 40 % of a knob labelled 0.5–4× cannot be used at full breath. The
   design working point is 2.16×, so the usable arc at a hard blow is
   0.5×–2.38× — the range above exists for quiet players and for negative
   offsets, which is legitimate, but it is not a 0.5–4× knob at full breath.
2. **RESPONSE eats headroom too**, and this interaction is nowhere on the page:
   full exp drops the clean ceiling from 2.38× to **1.58×**.
3. **It is sensitive to the disputed hard-blow figure.** If a hard blow is
   4 kPa `[config/figures.yaml:breath-working-point]`, `|V_in|` is 6.63 V, the
   clean ceiling at OFFSET centre falls to **1.68×**, and the 10 V working point
   to 1.51×. The whole knob shifts down and the top half becomes decorative.

### 4.3 Should the ranges be constrained? **No — state the rule and keep both ranges.**

Constraining GAIN removes the quiet-player case; constraining OFFSET removes the
bipolar-modulation case that §"What it has to do" calls the whole point of the
±5 V spec. Both ranges are individually justified; only their product is not.

The page's instinct — "that is the player's business" — is right. What it should
add is the rule in a form a player can use, which is **one sentence and one
number**:

> The jack clips at ±11 V. `OFFSET + GAIN × 4.64 V` has to fit inside that, so
> at the top of the OFFSET range the GAIN knob is limited to about a third of
> its travel. The clip is a rail clip with no soft region.

And one bench item for E10, which costs nothing: **verify the clip is a clean
rail clip and not a phase-reversal or an overload-recovery artefact.** The
OPA2197 has no phase reversal `[datasheet OPA2197.pdf p.11, Figure 29]` and
recovers in 200 ns `[p.8]`, so it should be clean — but "sounds like a wall"
is a claim about the part, and now it has a citation.

### 4.4 Noise and offset, closed

Neither is on the page and both are asked of any added stage, so:

```
[calc, datasheet OPA2197.pdf p.7]
  added op-amp e_n      10.5 nV/rtHz at 100 Hz
  divider (5 kOhm)       9.1 nV/rtHz
  R-RESP (15 kOhm)      15.8 nV/rtHz, x1.31 noise gain when conducting
  -> ~3 uV RMS at the jack over the 482 Hz band, 130 dB below a 10 V span
  V_OS +/-100 uV max, x2 x4  ->  +/-0.8 mV at the jack
  I_B +/-20 pA max x 5 kOhm source mismatch  ->  0.1 nV. CMOS inputs; ignore.
  V_CM at the (+) input: 0 to -4.97 V, inside (V-)-0.1 to (V+)-3 V where
  CMRR is 120 dB min - the stage never uses the degraded top-of-range region.
```

Nothing here is a constraint. Recorded so it stops being an open question.

### 4.5 Pot ratings, never checked anywhere in the corpus

```
[calc, against 0.05 W - datasheet R0904N.pdf p.1 and R0904N-thonk.pdf p.1]
  POT-GAIN    9.94 V across 57.15k   1.73 mW
  POT-OFFSET  5.21 V across 10k      2.71 mW
  POT-RESP    9.94 V across 50k      1.98 mW
```

All ~20× inside. Max operating voltage AC 50 V / DC 20 V (Song Huei) and 50 V AC
(Alpha) `[datasheet RV09AF-40.pdf p.1]` — our worst is 9.94 V. Clear.

---

## 5. The recast: one op-amp half, exact null, `U-RESP` deleted

This is the one change to the circuit, and it makes four separate problems go
away at once.

```
                              R-RESP-A 10.0k
   INAMP_OUT ─────────────────[========]──────┬────── RESP_MID
   0 … −4.64 V                                │      (= V_in / 2, high-Z tap)
   (the in-amp now drives                [R-RESP-B]
    only this divider)                      10.0k
                                              │
                                            AGND

                                  ┌──────────────┐
                    RESP_MID ─────┤ +            │
                                  │  ½ U-OPA     ├──┬──► RESP_OUT  ──► POT-GAIN top
                    RESP_SUM ─────┤ −            │  │    (= V_in at centre)
                        │         └──────────────┘  │
                        ├──[R-RESP-A2 20.0k]── AGND │
                        │                           │
                        ├──[R-RESP-FB 20.0k]────────┤
                        │                           │
                        │   D-RESP           R-RESP
                        └──[2×BAV99 ▷|◁]──[10.0k]──── RESP_W
                            antiparallel

                                POT-RESP 50k LINEAR (taper B)
                        AGND ──[=========================]── RESP_OUT
                         (CW)              │               (CCW)
                                        RESP_W

            CW  (wiper at AGND, above RESP_MID)   branch adds INPUT current
                                                  -> gain rises with breath: EXP
            centre (wiper = RESP_MID)             no branch current at all
                                                  -> LINEAR, exactly
            CCW (wiper at RESP_OUT, below it)     branch adds FEEDBACK current
                                                  -> gain falls with breath: LOG
```

`R-RESP-A`/`R-RESP-B` halve the in-amp output into a **high-impedance** tap —
the op-amp's `(+)` input draws ±20 pA max `[datasheet OPA2197.pdf p.7]`, so the
divider is exact and nothing loads it. The op-amp's `(−)` node therefore sits at
`V_in/2`, and its output at `V_in`. `POT-RESP` spans AGND to that output, so its
wiper is at `β·V_in` and equals the `(−)` node at **β = 0.500 exactly** — a null
set by the op-amp's own feedback, not by any resistor ratio and not by the pot's
±20 % track tolerance.

| | page as drawn | **recast** |
|---|---|---|
| op-amp halves | 2 | **1** |
| null position | α = 0.450, **14° off**, ±6° with pot tolerance | **β = 0.500 exact** |
| drive at the CW / CCW ends | 0.328·V_in / 0.500·V_in (asymmetric) | **0.500·V_in / 0.500·V_in** |
| wiper `R_th` at the ends | 4.5 kΩ / 0 | **0 / 0** |
| gain ratio at a hard blow, `R-RESP` 15 k | 1.289 | **1.505** |
| net inversions added | 2 (needs a restore stage for polarity) | **0** |
| block gain | ×1 (÷2 then ×2) | ×1 (÷2 then ×2) |
| headroom at the internal nodes | 4.97 V max | 4.97 V (`RESP_MID`), 9.94 V (`RESP_OUT`) — inside ±11.1 V |

**Nothing downstream changes.** The block is unity end to end, so `R-IN` 10 k /
`R-FB` 40.2 k, the 0.5–4× range, the offset legs and the commissioning targets
all stand exactly as written.

### What it buys in the BOM

```
   U-RESP                    DELETE - one SOIC-8 OPA2197
   C-DECOUPLE                19 -> stays 19 (was going to 21)
   op-amp halves  10 used of 12  ->  12 of 12 in six packages:
        + 1  response shaper
        + 1  POT-OFFSET wiper buffer   <- the half A5 needs and could not have
   D-RESP    1N4148 x2  ->  BAV99 x2   (part already in the BOM, qty 8 -> 10)
   NEW:  R-RESP-A 10.0k, R-RESP-B 10.0k, R-RESP-A2 20.0k, R-RESP-FB 20.0k
   DELETE: the page's R1 20k / R2 10k / divider 2 x 10k
```

Net: **one SOIC-8 and two decoupling capacitors removed from a 10 HP module**,
with `A5`'s buffer fitted rather than deferred, and four E96 resistors in place
of four E96 resistors.

`bom.csv`'s `U-RESP` row states the opposite case — "This stage consumes BOTH
remaining spare OPA2197 halves, so the separate `A5` finding … needs this
additional package." That sentence is the strongest argument *for* the recast,
and it is already written down.

---

## 6. `[from memory]` and `[calc]` re-marked against the bank

| Claim on the page | Was | Now |
|---|---|---|
| OPA2197 "stops at about ±11.5 V" | asserted | **corrected**: ±11.70 V nominal / ±11.10 V at Eurorack −5 % `[datasheet OPA2197.pdf p.8, V_O from rail 95 mV typ / 125 mV max at R_L = 10 kΩ; + calc on the rail drop]` |
| "The diode knee is fixed at ~0.6 V" | asserted | **corrected**: 0.44–0.56 V at 20–150 µA `[datasheet BAV99.pdf p.2 Fig. 1, digitised; bracketed by 1N4148.pdf p.3–4]` |
| `i_D` and gain-ratio table, §4 | `[calc]` | **wrong**: assumes an unloaded divider, zero wiper `R_th` and a 0.6 V knee. Replaced, §2.2 |
| "the 0.6 V knee lands at about a quarter of a hard blow" | `[calc]` | **11–19 %** `[calc, banked curve]`. Conclusion unchanged, number was ~2× out |
| "a centre click halves rotational life" | (not on the page) | **confirmed verbatim**: "With click: 5,000 cycles, without click: 10,000 cycles" `[datasheet RV09AF-40.pdf p.1]` |
| `POT-GAIN` / `POT-OFFSET` / `POT-RESP` "50 k / 10 k linear" | asserted | **confirmed orderable**: taper B = Linear, 1 kΩ–500 kΩ + 1 MΩ `[datasheet RV09AF-40.pdf p.1]`; `B50K` and `B10K` both appear in the distributor listing `[p.8]`. **Tolerance is ±20 %** `[datasheet R0904N.pdf p.1]` and is not stated anywhere in the corpus |
| `POT-RESP` centre detent | "an E10 call" | **`0C` suffix, 20–120 gf·cm click torque, 5 000-cycle life** `[datasheet RV09AF-40.pdf p.1]`; **not available at all on the Song Huei R0904N that Thonk ships** `[datasheet R0904N-thonk.pdf p.1 — the order code has no click field]` |
| "50 mV of rail movement is 21 mV at the jack" | `[calc]` | **confirmed** for the −12 V leg: `40.2k/95.3k × 50 mV = 21.1 mV` `[calc]`. Incomplete: the +5.21 V leg is 47.9 mV at centre |
| offset endpoints +5.04 / +0.07 / −4.89 V | `[calc]` | computed with `R-FB` = 40.0 k; **with the specified 40.2 k: +5.06 / +0.075 / −4.91 V** `[calc]` |
| hard blow −4.69 V, "≈2.13×" | `[calc]` | **wrong gain**: uses 2.18483 raw instead of 2.16106 effective. **−4.64 V and 2.16×** `[calc]`, matching `figures.yaml:inamp-full-scale` |
| "2.8 kPa (ADR 0003)" ×2 | `[repo]` | **the citation is false.** ADR 0003 contains no such figure; its only "2.8" is `2.83 mL` of tube volume at line 262 — a plausible transcription origin `[conjecture]`. `figures.yaml:breath-working-point` already files this DISPUTED |
| `C-OUT-BREATH` "~482 Hz" | `[calc]` | **confirmed**: `1/(2π·1k·330n)` = 482.3 Hz `[calc]`; 487.1 Hz into a 100 kΩ load |
| "Ten of twelve halves used … two spare" | `[repo]` | **confirmed** against `bom.csv:13`'s enumeration, and made wrong by §4 of the same page, which takes both. §5 restores it |

---

## 7. Netlist readiness

Every node in the stage, with the name I propose. The stage is otherwise ready:
no floating nodes, no implicit ties, every passive two-terminal, one ground
(`AGND`), one supply pair.

### 7.1 `BREATH` is two nets — rename both

`[repo]` `BREATH` currently means **the umbilical conductor and in-amp input**
(`breath-receive-stage.md`, `figures.yaml:umbilical-pinmap` "1,2 BREATH/AGND",
`bom.csv` `D-TVS-BREATH` "the BREATH and AGND legs") **and the output jack net**
(`breath-output-stage.md`). They are in different voltage domains (0.2–4.8 V
sensor vs ±11 V CV), on different boards, and a netlist that takes both spellings
literally shorts the sensor to the output.

**Proposal — and it is deliberately asymmetric, because one of the two is
already load-bearing in the pin map and should not move:**

| Today | Proposed | Why |
|---|---|---|
| `BREATH` (umbilical pin 1, in-amp input) | **`BREATH_IN`** | keeps the panel/pin-map word "BREATH" recognisable; `_IN` matches the etherCON pin's direction as seen from the module |
| `BREATH` (output jack) | **`BREATH_CV`** | matches `PITCH_CV` / `MOD1_CV` if those are adopted; the jack is a CV output, and the panel legend stays "BREATH" |

The rename touches `figures.yaml:umbilical-pinmap` (whose `forbidden` list should
gain the bare `BREATH` pin-table cell), `bom.csv` `D-TVS-BREATH` and
`D-JACK-CLAMP`, and both schematic pages. It is exactly the class of change
`CLAUDE.md` §2 exists for.

### 7.2 Canonical names for the stage

```
  INAMP_OUT     INA828 output. 0 -> -4.64 V at a hard blow, -9.94 V at 6 kPa.
                  Also the receive page's output; one net, one name, two pages.
  RESP_MID      R-RESP-A / R-RESP-B tap, = INAMP_OUT/2. High-Z; op-amp (+) only.
  RESP_SUM      U-RESP-A (-) input. Virtual node at RESP_MID. Junction of
                  R-RESP-A2, R-RESP-FB and the D-RESP branch.
  RESP_W        POT-RESP wiper.
  RESP_OUT      shaper output = INAMP_OUT at centre. Drives POT-GAIN top and
                  the POT-RESP track. THIS IS THE NET THAT REPLACES INAMP_OUT
                  AT POT-GAIN - the one substitution the recast makes.
  GAIN_W        POT-GAIN wiper -> gain buffer (+).
  GAIN_BUF      gain buffer output -> R-IN.
  OFFSET_W      POT-OFFSET wiper -> offset buffer (+).      [NEW, per A5]
  OFFSET_BUF    offset buffer output -> R-OFF.              [NEW, per A5]
  SUM_NODE      summer (-) input. R-IN, R-OFF, R-OFFNEG, R-FB.
  BREATH_DRV    summer output. D-JACK-CLAMP and R-OUT-PROT attach HERE,
                  on the driver side - which bom.csv already requires and no
                  net name currently distinguishes from the jack.
  BREATH_CV     jack net. R-OUT-PROT, C-OUT-BREATH, PJ398SM tip.
  AGND          module analog ground. Single reference for this entire stage.
  V5R21         LM317 rail feeding POT-OFFSET's top. (bom.csv calls it
                  "the LM317 5.21V rail" in prose and nothing in a netlist.)
```

`BREATH_DRV` vs `BREATH_CV` is the one that matters for correctness: the clamp
being on the driver side of `R-OUT-PROT` is a decision `bom.csv` argues at length
`[repo hardware/bom.csv:52]` and which a single `BREATH` net would silently
discard. **Six output jacks share this pattern**, so the pair should be adopted
across the module, not just here.

### 7.3 Invariants to assert in the netlist checker

```
  1.  odd number of inverting stages between INAMP_OUT and BREATH_CV      (§1.6)
  2.  D-JACK-CLAMP and R-OUT-PROT on BREATH_DRV, never on BREATH_CV      (bom.csv)
  3.  C-OUT-BREATH on BREATH_CV, never on BREATH_DRV                     (bom.csv)
  4.  R-FB returns to BREATH_DRV, not BREATH_CV                (this page, not pitch)
  5.  POT-GAIN wiper -> a buffer input only; no resistive load            (§3.1)
  6.  POT-OFFSET wiper -> a buffer input only; no resistive load          (§3.2)
  7.  RESP_MID drives an op-amp (+) input only                            (§5)
```

1, 5, 6 and 7 are all cheap ERC rules and all four correspond to a real defect
found either here or by `A5`.

---

## 8. Proposed values

Changes in **bold**.

| Ref | Value | Job |
|---|---|---|
| `R-RESP-A`, `R-RESP-B` | **10.0 kΩ 1 %** ×2 | ÷2 tap into the shaper's (+). High-Z, so exact |
| `R-RESP-A2` | **20.0 kΩ 1 %** | shaper gain leg to AGND |
| `R-RESP-FB` | **20.0 kΩ 1 %** | shaper feedback. `+2` restores the ÷2; block gain ×1 |
| `POT-RESP` | 50 kΩ **taper B (linear)**, 9 mm, **no detent needed** but harmless | log ← linear → exp. Null at mechanical centre by topology |
| `R-RESP` | **10.0 kΩ 1 %** (15.0 kΩ if one diode per leg) | curve strength. 1.51× at a hard blow either way |
| `D-RESP` | **2 × BAV99, antiparallel (pin 1→2 each)** | two series diodes per leg. Knee at 22–37 % of a hard blow |
| `U-RESP` | **DELETED** | the shaper is one half of `U-OPA-PITCH` |
| `POT-GAIN` | 50 kΩ **taper B (linear) — closed, §1.4** | attenuator 0.125 → 1.000 (**0.107–0.152 at ±20 %**) |
| `R-GAIN-FLOOR` | 7.15 kΩ 1 % | floor. **0.43×–0.61×**, not exactly 0.5× |
| `R-IN` | 10 kΩ 1 % | summer input |
| `R-FB` | **40.2 kΩ 1 % — and fix the drawing, which says 40 k** | fixed ×4 |
| `POT-OFFSET` | 10 kΩ taper B, **wiper buffered**, **no detent** | **+5.06 / −4.91 V**, +0.075 V at centre |
| `R-OFF` | 21.0 kΩ 1 % | variable positive leg, from `OFFSET_BUF` |
| `R-OFFNEG` | 95.3 kΩ 1 % | fixed negative leg from −12 V |
| `R-OUT-PROT` | 1 kΩ, 1206, 0.66–1 W | 123 mW worst case here; not the module's worst |
| `C-OUT-BREATH` | 330 nF film — **proposed 10 nF C0G, §3.4** | not a reconstruction filter; 332 µs of delay |

**Op-amp halves: 12 of 12, six packages, none spare.** Response shaper 1,
`POT-OFFSET` buffer 1, and the ten `bom.csv` already enumerates.

---

## 9. What I could not settle

- **The 1N4148 / BAV99 forward curve below 1 mA is not *specified* by any banked
  document** — only plotted, and Vishay's plot contradicts Vishay's own table at
  1 mA. Everything above is robust to it (±2 % across the full bracket), so this
  is a provenance gap and not a design risk. If it is ever wanted properly:
  measure one diode at 10 / 50 / 100 / 200 µA at E10, which takes five minutes.
- **`breath-working-point` is still DISPUTED** and this page cites it as settled,
  twice, to a document that does not contain it. Every headroom number in §4
  moves with it, and §4.2 gives the sensitivity. **M1 with a manometer.**
- **The 1.3 dB (or 2.9 dB) of curve authority is a musical judgement**, not an
  electrical one. §2.5 measures it; whether it is enough is E10, with a player.
  That is the *only* part of §4 that was genuinely a bench question, and the page
  sent four things to the bench that arithmetic could close.
- **The panel-rail figure ±11.5 V has no owner.** §4.1 derives ±11.70 / ±11.10 V.
  It should become a `figures.yaml` entry, because six output stages cite it.

## Appendix — model

`T2` (recast) and `T1` (as drawn) are node-admittance solves with the diode
branch iterated to a fixed point (damped, tolerance 1e-14 A). The diode is the
digitised Vishay BAV99 25 °C curve of §2.1, log-interpolated in current and
shifted −2.2 mV/K; `k` diodes in series per leg. `T1` additionally solves the two
loaded nodes `A` and `W` each iteration, which is the step the page's table
omits. Cross-checked against a closed-form Shockley bracket (n = 1.0 and n = 1.9,
anchored on NXP Fig. 3's 0.608 V at 1.42 mA); the two agree to under 2 % on every
figure quoted.
