# Pitch stage — schematic

**Status:** Drawn 2026-09-21. Second module page, after
[the breath receive stage](breath-receive-stage.md).

The ADRs specify this channel's *behaviour* in detail — 1 V/oct, −2 to +7 V,
trimmers for gain and offset, an LT5400 matched network, an offset reference
divided from the buffered `VREFOUT` — and have never specified its *topology*.
Drawing it changes the answer.

## The circuit

```
                        buffered VREFOUT, 2.500 V
                        (½ OPA2197, ADR 0006)
                                 │
                                 ├──────────────┐
                                 │              │
                          [TRIM-OFFSET]         │
                            10k cermet          │
                                 │ wiper        │
                            [470k R-OFFINJ]     │
                                 │              │
                                 │         [R1 10k]  ┐
                                 │              │    │ LT5400
                                 │              │    │ 1:1 pair
   DAC ch1 ──[1k R-OPAMP-IN]──┬──┼──────────────┤    │
   0.25…4.75 V                │  │              │    │
                              │  │        ┌─────┴────┴──┐
                              └──┼────────┤ +           │
                                 │        │   ½ OPA2197 ├──┬────────┐
                                 └────────┤ −           │  │        │
                                     ┌────┴─────────────┘  │        │
                                     │                     │        │
                                     └──[R2 10k]──[TRIM-GAIN 1k]───┘
                                          LT5400    (IN SERIES)
                                                                    │
                                          ┌─────────────────────────┘
                                          │
                            [R-OUT-PROT 1k]
                                          │
                                          ├──[C-FILT-PITCH 10nF C0G]── AGND(module)
                                          │
                                          ├──[D-JACK-CLAMP BAV99]── ±12 V
                                          │
                                     PITCH jack
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

## `R-OFFINJ` as drawn is not a pure offset — unresolved

The first version of this page claimed the injection "moves offset without
touching gain". That is true of an *inverting* summer, whose node is a virtual
ground at 0 V. **This node is not.** In a non-inverting amplifier the (−) input
sits at `Vdac`, so the current through `R-OFFINJ` depends on `V_wiper − Vdac`
and the `Vdac` part of it is a **gain** term:

- Nominal gain becomes **2.0213**, not 2.000 — about +1.06 %.
- The trim span is **one-sided, 0 → −53.2 mV**, i.e. ±26.6 mV ≈ **±32 cents
  about a displaced centre** — half the ±64 cents this page and the BOM both
  claim.

It still *works* — the gain trimmer absorbs the 1 % and the range is adequate —
but it is not the clean decoupled trim it was described as, and the numbers in
the BOM are wrong. **Resolve at E10 with the real network**, or reconsider the
trimmers entirely (see below).

## The two trims interact, and the procedure says so

Gain and offset are set by the *same* ratio `R2/R1` — gain is `1 + R2/R1`,
intercept is `−2.5 × R2/R1`. Turning the gain trimmer moves both. That is not a
defect of this topology; it is true of every 1 V/oct module with a gain and an
offset pot, which is why they are all trimmed the same way:

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
