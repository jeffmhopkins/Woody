# Breath gain and offset stage — schematic

**Status:** Drawn 2026-09-21. Sixth module page, and the last block on the
board.

This stage was drawn as a box labelled "panel knobs" for as long as the module
existed, and in that time it produced findings in **five separate reviews**
while remaining undrawn. That is the pattern: whatever is a block is where the
defects hide.

## What it has to do

**Panel GAIN 0.5× to 4×, panel OFFSET −5 V to +5 V.** The offset range is the
interesting requirement — a breath CV that can rest anywhere in a ±5 V window
drives bipolar modulation inputs and inverted envelopes, not just a VCA.

What arrives from the receiver, with the pedestal nulled at the in-amp's `REF`
(`breath-receive-stage.md`):

| | Sensor | In-amp output |
|---|---|---|
| Rest | 0.265 V | **0.00 V** |
| Hard blow, real playing (~2.8 kPa) | 2.411 V | **−4.64 V** |
| Sensor full scale (6 kPa) | 4.864 V | −9.94 V |

**Real playing only reaches about 2.8 kPa against the sensor's 6 kPa range**
(ADR 0003), so the stage's working input is 0 to about −4.7 V. Reaching 10 V at
the jack from that needs **≈2.16×** — comfortably inside 0.5–4, which is the
point of specifying the range from playing rather than from the sensor.

> **Corrected 2026-09-21** against `sensor-full-scale`. The sensor column moved
> with the pedestal (0.200 → 0.265 V) and the full-scale figure (4.80 → 4.86 V).
> **The in-amp column moved for a second, independent reason**: −4.69 V was
> computed with the in-amp's *raw* 2.18483, and the working point is the
> *effective* 2.1611 that the bias pair leaves — the same gain the −9.94 V in
> the row below already uses. The span is unchanged, so −9.94 V is untouched.
> `[calc]` `(2.411 − 0.265) × 2.1611 = 4.638`; `10 / 4.638 = 2.156`.

## The circuit

```
   from the INA828                    ┌──────────────┐
   0 … −4.7 V ──────[POT-GAIN 50k]────┤ +            │
   (rest at 0)            │           │  ½ OPA2197   ├──┬── buffered
                          │           │  follower    │  │   attenuator
                     [R-GAIN-FLOOR]   └──────────────┘  │   0.125 … 1.000
                        7.15k         └────────────────┘│
                          │                              │
                     AGND(module)                  [R-IN 10k]
                                                         │
   buffered +5.21 V ──[POT-OFFSET 10k]                   │
   (LM317 rail)             │ wiper                      │
                            │                            │
                       [R-OFF 21.0k]────────────────┬────┤
                                                    │    │
              −12 V ────[R-OFFNEG 95.3k]────────────┘    │
                                                         │
                                            ┌────────────┴───┐
                                            │ −          ┌───┤
                                            │  ½ OPA2197 │   │
                                            │ +          └───┤
                                            └────┬───────────┘
                                          AGND   │
                                                 ├──[R-FB 40k]── (to −)
                                                 │
                                    [D-JACK-CLAMP BAV99]── ±12 V
                                                 │
                                   [R-OUT-PROT 1k, 1206]
                                                 │
                                                 ├──[C-OUT-BREATH 330nF film]── AGND
                                                 │
                                           BREATH jack
```

## Gain: a buffered attenuator ahead of a fixed ×4

**Not a rheostat in the feedback path**, which is the obvious way and the wrong
one — it makes the gain and the offset share a resistor, so the knobs fight.
That is the same coupling the `REF` trimmer was added to remove one stage
upstream, and putting it back here would be the third time this project
relocated that defect rather than fixing it.

Instead the pot attenuates *before* the summing node, where it cannot touch the
offset at all:

```
attenuation = 0.125 … 1.000      ×  fixed gain R-FB/R-IN = 4      =  0.5 … 4.0
```

`R-GAIN-FLOOR` (7.15 kΩ under a 50 kΩ track) sets the bottom: `7.15/57.15` =
0.125. Without it the knob reaches zero gain, which is a mute nobody asked for
and an easy way to think the instrument is dead.

**The wiper must be buffered.** It drives `R-IN`, so an unbuffered wiper makes
the attenuation depend on a source impedance that varies with rotation — a gain
error, not just a feel. One op-amp half, and it is the only one this stage adds
beyond the summer.

## Offset: bipolar, from rails that are already there

The summing node takes two more currents — one fixed and negative, one variable
and positive — and their sum crosses zero at mid-rotation:

| Pot | Wiper | Offset at the jack |
|---|---|---|
| Full CCW | 0 V | **+5.04 V** |
| **Centre** | 2.605 V | **+0.07 V** |
| Full CW | 5.21 V | **−4.89 V** |

`R-OFFNEG` pulls a constant from −12 V; `R-OFF` pushes a variable from the
buffered 5.21 V. **No extra op-amp half, and no negative reference to
generate** — which is what makes ±5 V cost two resistors instead of a part.

**This wiper does *not* need buffering.** Its source impedance varies from 0 at
either end to `R/4` at centre, so the endpoints are exact and the middle is
slightly non-linear in rotation. For an offset knob that is feel, not error.

**Why −12 V is acceptable here and would not be on pitch.** ADR 0006 moved the
*pitch* offset off a rail divider because 50 mV of rail movement is 12.5 cents
of transposition. Here 50 mV moves the jack by `40k/95.3k × 50 mV` = **21 mV,
0.21 % of span** — and the −12 V rail carries no LED current, because the
strips run from +12 V.

## Values

| Ref | Value | Job |
|---|---|---|
| **POT-GAIN** | 50 kΩ, **taper from the bench** | Attenuator, 0.125 → 1.000 |
| **R-GAIN-FLOOR** | 7.15 kΩ 1 % | Sets the 0.5× floor |
| **R-IN** | 10 kΩ 1 % | Summer input |
| **R-FB** | 40.2 kΩ 1 % | Fixed ×4. Same E96 part as `R-MODGAIN` |
| **POT-OFFSET** | 10 kΩ linear | ±5 V, zero at centre |
| **R-OFF** | 21.0 kΩ 1 % | Variable positive leg |
| **R-OFFNEG** | 95.3 kΩ 1 % | Fixed negative leg from −12 V |
| **R-OUT-PROT** | 1 kΩ, 1206 ≥500 mW | Shared spec with the other five outputs |
| **C-OUT-BREATH** | 330 nF film | ~482 Hz, jack side, feedback from the op-amp |

**Two op-amp halves**, which settles a count that has been wrong in the BOM
twice: gain buffer and summer. Ten of twelve halves used across the module,
two spare.

## Headroom, and the combination that clips

Gain and offset are independent, which means they can be set to a combination
the rails cannot deliver: **offset at +5 V and gain at 4× puts a hard blow at
+23 V**, and the OPA2197 stops at about ±11.5 V.

That is the player's business and it is what the gain knob is for — but it is
worth knowing that the clip is a *rail* clip with no soft region, so it will
sound like a wall rather than compression. The honest usable rule: the offset
sets where breath rests, and the gain sets how far it travels from there; their
sum has to fit in ±11.5 V.

## Still open

- **`POT-GAIN`'s taper.** Linear gives a knob that does most of its work in the
  last quarter turn. A log or pseudo-log taper (or a second floor resistor
  across part of the track) is a feel question, and feel is a bench question —
  E10, with a real sensor and someone blowing into it.
- **`POT-OFFSET` detent at centre**, which is now a meaningful position rather
  than an arbitrary one. A centre-detent pot would make "no offset" findable in
  the dark; whether that is worth the part is an E10 call.
- **Commissioning order** is now three steps, not two: `TRIM-BREATH-ZERO` for
  the pedestal, then GAIN for the span, then OFFSET for where it rests. The
  first is internal and set once; the other two are performance controls.

---

# §4 Response control — `POT-RESP`, log ← linear → exp

**Proposed 2026-09-21.** Requested after the review wave, and independently
asked for by it: `B6` found that the nearest commercial equivalent
(ADDAC310 Pressure-to-CV) ships Response — exp ↔ lin ↔ log — alongside
slew, offset and gain, and that NuEVI ships thirteen curves and does not
default to linear. This module has two knobs and no shaping at all. `B6`
ranked that a High finding and noted "the module has two spare OPA2197
halves".

## The property the circuit is built around

An inverting stage sits at a virtual ground. Span a pot between **a signal
that is `+V/2`** and **the stage's own output, which is `−V/2`**, and the
wiper voltage is

```
   V_wiper = (V/2) + p·(−V/2 − V/2) = (V/2)(1 − 2p)
```

which is **exactly zero at p = 0.5, for every input voltage**. So a
nonlinear branch hung off the wiper carries no current at all at centre
detent — **the stage is mathematically linear in the middle, not
approximately linear.** Turn either way and the wiper develops a voltage
proportional to the signal, which drives that branch into one leg or the
other.

```
                              R1 20k
   in-amp out ──┬──────────[====]────┬───── X (virtual gnd)
     (0…−9.94V) │                    │        │
                │   R2 10k           │        │
                │  ┌──[====]─────────┴────────┴──► V_shaped = −V_in/2
                │  │                          │
           [10k]│  │                     ┌────┴────┐
                ├──┼─────────────────────┤ ½ U-RESP│
           [10k]│  │                     └─────────┘
                │  │
               GND │
                │  │      POT-RESP 50k LINEAR
       V_in/2 ──┴──┼──────[===========]──────┘  (other end = V_shaped)
                   │            │
                   │          wiper
                   │            │
                   │        [R-RESP 15k]
                   │            │
                   └──────[▷|◁]─┴──► X          D-RESP, 1N4148 antiparallel
                        two diodes
```

**CW (wiper toward `V_in/2`)** → the branch injects extra *input* current
at high breath → gain rises with pressure → **expansive, "exponential"**.
Harder to get loud; more expression at the top.

**CCW (wiper toward `V_shaped`)** → extra *feedback* current at high breath
→ gain falls with pressure → **compressive, "logarithmic"**. Easier to get
loud; the top compresses.

**Centre detent** → wiper at 0 V → no diode current → **linear**, exactly.
This is the one place a centre detent is honestly warranted on this panel,
and unlike `POT-OFFSET` (whose detent the review found lands ~20° off its
true zero) this null is set by the topology, not by resistor tolerance.

## Scaling — and the mistake this nearly shipped with

The diode knee is fixed at ~0.6 V. **Where the playing range sits relative
to that knee is the entire design.** A first pass at ÷10 scaling was
checked and thrown out:

```
÷10:  hard blow 4.64 V at the in-amp → 0.464 V at the node
      knee is 0.6 V → the control does NOTHING until you overblow
```

At **÷2** the knee lands at about a quarter of a hard blow, so the curve
acts across the playing range rather than above it `[calc]`:

| Dynamic | In-amp | Node | `i_D` | Gain ratio |
|---|---|---|---|---|
| *pp* | 1.00 V | 0.50 V | 0 | **1.000** (below the knee — exactly linear) |
| *mp* | 2.50 V | 1.25 V | 43 µA | 1.347 |
| *mf* | 3.50 V | 1.75 V | 77 µA | 1.440 |
| hard blow | 4.64 V | 2.32 V | 115 µA | 1.494 |
| full scale | 9.94 V | 4.97 V | 291 µA | 1.586 |

## What this is, stated honestly

**A soft single-breakpoint shaper, not a true exponential law.** Below the
knee it is exactly linear; above it the gain rises smoothly toward ~1.6×
and then flattens, because once well past the knee the diode is just a
resistor. The character is *flat, then bend* — which is what most
"response" controls in this format actually are.

A mathematically exact exp/log law needs a matched log/antilog transistor
pair with tempco compensation, which is temperature-sensitive, needs a
matched pair and a tempco resistor, and is a great deal of trouble for a
breath curve. **Not recommended.** If more curvature is wanted later, the
cheap route is a *second* diode/resistor breakpoint biased through a
divider — two more parts per side, piecewise, and no thermal behaviour.

## What it costs, and the decision it forces

| | |
|---|---|
| Op-amp | **Both remaining OPA2197 halves** — one shapes at ÷2 inverting, one restores ×2 inverting to put scale and polarity back |
| Passives | `POT-RESP` 50 k lin (same part as `POT-GAIN`), `R-RESP` 15 k, `D-RESP` ×2 1N4148, R1 20 k, R2 10 k, divider 2 × 10 k |
| Panel | **A third pot and a third knob** |

> ### The panel goes to 10HP — decided 2026-09-21
>
> `B1` reconstructed the panel bottom-up from real component envelopes and
> got **~115 mm against ~110 mm usable** — already over *before* this
> control — and found that ADR 0004's "107 mm of ~110 mm usable" figure is
> asserted twice and **derived nowhere**.
>
> **10HP is 50.50 mm, and the win is not the extra width.** It is that three
> pots fit in **one row instead of two**, which deletes a 20+ mm row from a
> budget that had already overrun. The derived layout is in ADR 0004 and
> comes to **97 mm against ~110 mm, 13 mm spare**.
>
> **The cost is knob diameter.** Three pots across 50.50 mm with 3 mm gaps
> needs **≤14 mm knobs**; 15 mm already gives 51 mm and does not fit. So
> 10HP buys the height back by spending the knob size 8HP was supposed to
> have bought. Three controls at 14 mm beats two at 16 mm — but ADR 0004's
> claim of "16–20 mm knobs" is withdrawn rather than quietly left standing.
>
> It also makes room for the op-amp package the *other* review finding
> needs: `A5` showed `POT-OFFSET`'s wiper is unbuffered, which is why its
> "zero at centre" actually sits ~20° past centre at +0.605 V. That fix
> wants a half, and this stage takes the last two.

## Open before layout

- **The extra inversion.** This stage inverts twice, so polarity is
  restored — but the existing chain's polarity was never re-derived with a
  stage inserted. Check it end to end before layout, not after.
- **Where it inserts.** Drawn here between the in-amp and the gain
  attenuator, deliberately: the signal there has a **fixed** scale set by
  the in-amp, so the knee sits at a known fraction of full breath. Put it
  after `POT-GAIN` instead and **the curve would change every time you
  moved the gain knob**, which is the one arrangement that must not happen.
- **`R-RESP` at 15 kΩ is a first sizing**, targeting ~1.5× at a hard blow.
  It is the knob that sets how strong "fully exponential" feels and it
  wants a bench pass with a real player, not a spreadsheet.
- **Diode matching.** Breath is unipolar, so only one of the antiparallel
  pair ever conducts in normal play. The second is there for the
  power-on/fault excursions the review catalogued, not for symmetry.
