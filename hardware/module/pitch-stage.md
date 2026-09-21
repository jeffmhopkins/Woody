# Pitch stage — schematic

**Status:** Drawn 2026-09-21. Second module page, after
[the breath receive stage](breath-receive-stage.md).

The ADRs specify this channel's *behaviour* in detail — 1 V/oct, −2 to +7 V,
trimmers for gain and offset, an LT5400 matched network, an offset reference
divided from the buffered `VREFOUT` — and have never specified its *topology*.
Drawing it changes the answer.

## The circuit

```
   VREFOUT ──[TRIM-OFFSET 10k]──┬── ½ OPA2197 ──┬── V_ref ≈ 2.500 V
   (2.500 V)   + range resistors│   follower    │   (trimmed, buffered)
                                └───────────────┘
                                                │
                                          [R1 10k]  ┐ LT5400
                                                │   │ 1:1 pair
                                                │   │
   DAC ch1 ──[1k R-OPAMP-IN]──┐                 │   │
   0.25…4.75 V                │                 │   │
                              │           ┌─────┴───┴───┐
                              └───────────┤ +           │
                                          │  ½ OPA2197  ├──┬── op-amp output
                              ┌───────────┤ −           │  │
                              │           └─────────────┘  │
                              │                            │
                              ├──[C-FB-PITCH 1nF]──────────┤   ← AC feedback
                              │                            │
                              │                   [D-JACK-CLAMP BAV99]── ±12 V
                              │                            │
                              │                  [R-OUT-PROT 1k, 1206]
                              │                            │
                              └──[R2 10k]─[TRIM-GAIN 200R]─┴── PITCH jack
                                  LT5400   (in series)         ← DC feedback
```

## It is a non-inverting amplifier, not a difference amplifier

**Two resistors, not four.** Every prior description in this project implied a
four-resistor difference amp. It does not need one.

Start from the window ADR 0006 already fixed:

| | |
|---|---|
| DAC usable window | 0.25 → 4.75 V |
| Jack range | −2 → +7 V |
| Slope | 9 V / 4.5 V = **exactly 2.000** |
| Intercept | −2 − 2(0.25) = **−2.500 V** |

So `Vout = 2·Vdac − 2.500`, and the two-resistor non-inverting form gives it
directly:

```
Vout = Vdac·(1 + R2/R1) − V_ref·(R2/R1)
     = 2·Vdac − 2.500          when R1 = R2 and V_ref = 2.500 V
```

**The reference sits at the bottom of the feedback divider**, which is where a
non-inverting amp's offset injection belongs, and the matched pair is **1:1** —
the easiest ratio there is to match. Two of the LT5400's four resistors do the
job; the other two are spare.

> **A correction, because the first version of this page got the reason wrong.**
> It said `A = 1 + B` is a *boundary* that pitch's numbers happened to land on,
> and that the mod channels miss it and therefore need four resistors.
>
> `A = 1 + B` is not a boundary. It is the **defining identity** of this
> topology — with `k = R2/R1`, gain is `1 + k` and the intercept is `k·V_ref`,
> for every `k`. The free parameter is not the ratio, it is **`V_ref`**:
>
> ```
> k = A − 1        V_ref = offset / (A − 1)
> ```
>
> Winterbloom's Sol ships this exact circuit and divides its 2.5 V reference
> down to **1.190 V** to land on the gain and offset it wants. Pitch is not a
> lucky case; it is the ordinary case with `V_ref` left at 2.500 V.
>
> The consequence matters: **the mod channels can use two resistors too**, at
> `k = 3` with the offset channel writing **3.3333 V** instead of 2.500 V — and
> the power-on-and-`CLR`-at-0 V property survives, because both terms still go
> to zero. See `mod-channels.md`.

`R-OPAMP-IN` costs nothing here: it feeds an op-amp's (+) input, which draws no
current, so it contributes no gain error at all. It is pure clamp-current
protection for the power-up window where the DAC is on 5.21 V and the op-amp is
on ±12 V (ADR 0006).

## Why the offset reference must be `VREFOUT` — the arithmetic, not the assertion

ADR 0006 moved the offset reference off the ±12 V rail because a bare divider
there costs ~22 cents p-p of LED-correlated FM. That is the *negative* reason.
This is the positive one, and it only becomes visible once the topology is
drawn.

The DAC's full scale is `2 × VREFOUT` — that is what reference gain 2 means. So
let `VREFOUT` drift by a fraction δ. Both terms move together:

```
Vout = 2·Vdac(1+δ) − 2.500(1+δ) = (1+δ)·(2·Vdac − 2.500)
```

**The whole transfer function scales.** A reference drift becomes a pure *gain*
error and never an offset error — and on a 1 V/oct output those are not
comparable:

| Error type | At −2 V | At +7 V |
|---|---|---|
| Offset, 1 mV | 1.2 cents | 1.2 cents |
| Gain, 100 ppm | 0.24 cents | 0.84 cents |

An offset error transposes the whole instrument equally, including the low
notes where it is most audible against a drone. A gain error vanishes at the
bottom of the range and is largest seven octaves up, where nobody is listening
for absolute pitch. Referencing the offset to the same node the DAC references
converts the worse error into the better one, for free.

*(This is also why the ADR's "the DAC's internal reference is sufficient, at
0.54 cents over 10 °C" survives: that figure is a gain term.)*

## Component values

| Ref | Value | Job |
|---|---|---|
| **R1, R2** | 10 kΩ, **1:1 matched** (LT5400) | Sets gain = 2 and the −2.5 V intercept together |
| **V_ref** | 2.500 V, buffered `VREFOUT` | Shared with nothing else; one op-amp half |
| **TRIM-GAIN** | 1 kΩ multiturn cermet, **in series** with R2 | **0 → +5 % of ratio, one-sided** — a series trimmer can only add. That is the right direction for the load divider, which only ever reduces gain, but it is not ±5 % and an earlier revision said it was |
| **TRIM-OFFSET** | 10 kΩ multiturn cermet across `VREFOUT` | Wiper through `R-OFFINJ`. **See the caveat below — this is not yet a clean trim** |
| **R-OFFINJ** | 470 kΩ 1 % | **Value and topology are wrong as drawn**, see below |
| **R-OPAMP-IN** | 1 kΩ 1 % | Clamp-current protection on the (+) input. No gain error |
| **R-OUT-PROT** | 1 kΩ 1 % | Short protection. A load divider the gain trim absorbs (ADR 0006) |
| **C-FILT-PITCH** | 10 nF C0G | 15.9 kHz, **jack side** of the 1 kΩ |

**Headroom.** Full DAC scale 0 → 5.000 V maps to −2.500 → +7.500 V, which is
the ±600 cents of firmware reserve ADR 0006 describes. An OPA2197 on ±12 V
less two Schottky drops reaches ~±11.45 V, so the reserve is real and not
clipped.

## Two changes prior art forced, both improvements

### DC feedback is tapped at the jack, not at the op-amp output

`R-OUT-PROT` divides against whatever is patched in — −11.9 cents/octave into
one 100 kΩ VCO, −23.5 into two on a passive mult. ADR 0006 accepted that and
paid for it with a per-load affine preset, a display page, an operating
instruction, and most of the gain trimmer's range.

**All four surveyed DAC-driven designs** — Ornament & Crime, Westlicht
PER|FORMER, Mutable Yarns, Winterbloom Sol — instead close the DC loop *at the
jack*, so the divider is inside the feedback and the error is identically zero
for any load. ADR 0006 declined this as "real stability work… on a board
without one", on the strength of a claim that the compensation capacitor and
the output filter were the same part and could not coexist. **They are not the
same part**, and three of those four designs ship both.

So the loop is split, which is the standard arrangement:

| Path | Frequency | What it does |
|---|---|---|
| `R2` + `TRIM-GAIN` from the **jack** | DC to ~16 kHz | Sets the transfer function against the load, whatever it is |
| `C-FB-PITCH` 1 nF from the **op-amp output** | above ~16 kHz | Takes over before `R-OUT-PROT` and the cable can put phase in the loop |

**`C-FILT-PITCH` is deleted.** A 10 nF to ground at the jack would now sit on
the feedback node, inside the DC loop, right at the handover — the one place it
must not be. The 15.9 kHz reconstruction pole comes from `C-FB-PITCH` instead,
which is the same corner in a better place, and is what the prior art does: no
DAC-driven module in the corpus puts a capacitor on the jack side of its series
resistor.

**E9 already has the check** — "pitch stability into worst-case cable
capacitance" was in the measurement table before this change, and it is now
load-bearing rather than reassuring. This is the highest-risk item on the page.

*(The mod channels keep their jack-side caps and are unaffected: their feedback
comes from the op-amp output, so `R-OUT-PROT` isolates the capacitor exactly as
intended. Only pitch needs load-independence.)*

### The offset trimmer moved ahead of the reference buffer

The first version put it after, injecting through `R-OFFINJ` into the inverting
node, and claimed that "moves offset without touching gain". That is true of an
*inverting* summer, whose node is a virtual ground. **This node is not** — in a
non-inverting stage it sits at `Vdac`, so the injected current depended on
`V_wiper − Vdac` and the `Vdac` part was a **gain** term: nominal gain 2.0213
rather than 2.000, and a one-sided span of half what was claimed.

Trimming the reference *before* the buffer fixes it exactly. Offset is
`k · V_ref` and gain is `1 + k`, so moving `V_ref` moves the intercept and
touches the gain **not at all**. `R-OFFINJ` is deleted; the trimmer is now two
parts earlier and does a cleaner job.

## The trims still interact one way, and the procedure says so

**Offset no longer touches gain**, per above. **Gain still touches offset**,
because both come from the same ratio: gain is `1 + k`, intercept is
`k · V_ref`. That half of the coupling is intrinsic and is why every 1 V/oct
module with two pots is trimmed the same way:

1. Play the **highest** note in use. Adjust **gain** until it is in tune.
2. Play the **lowest** note. Adjust **offset** until it is in tune.
3. Repeat twice. It converges quickly because the offset trim does not affect
   gain at all — only the gain trim is shared.

**Trim with the real patch connected** (ADR 0006): the 1 kΩ output resistor
divides against whatever is plugged in, and that error is what the gain trim's
±5 % range exists to absorb.

## What limits accuracy, in order

| Term | Over 10 °C | Note |
|---|---|---|
| **TRIM-GAIN tempco** | **0.4–2.4 cents** at +7 V | Cermet at ~100 ppm/°C contributing ~5 % of the ratio. ADR 0006 says 2.4 cents and this page said 0.4; they disagree 6× and **have not been reconciled** — partly because they pivot about different points (reference drift about `Vout` = 0 V, ratio drift about +2.5 V). Either way it is the largest line here |
| LT5400 ratio tracking | ~0.1 cents | The reason it is not two discrete 0.1 % parts, which would be ~1.2 cents |
| DAC internal reference | ~0.5 cents | A gain term, per above |
| OPA2197 offset drift | <0.1 cents | An offset term, but a tiny one |
| DAC INL, ±4 LSB typical | ~0.4 cents | Curvature; firmware's multi-point correction, not a trimmer's job |

Nothing here approaches the **20-odd cents** of the dynamic, LED-correlated
terms that ADR 0006 fixes in the power tree and the ground plan. That remains
the right order of priority: the static budget was never the problem.

## Still open

- **The LT5400 option suffix.** A 1:1 quad is the requirement; the exact
  orderable part number must come off the option table, which this sandbox
  cannot reach. `R-PRECISION` in the BOM carries the same caveat.
- **Whether `TRIM-GAIN` is 1 kΩ or 500 Ω.** ±5 % of a 10 kΩ ratio wants ~1 kΩ
  of adjustment; whether that is too coarse for a comfortable multiturn feel is
  a bench question at E9.
- **The two spare LT5400 resistors.** Available, matched, and currently doing
  nothing. Worth a look when the mod channels are laid out.
