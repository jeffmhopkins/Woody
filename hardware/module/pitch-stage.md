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
| **V_ref** | 2.500 V, trimmed then buffered from `VREFOUT` | One op-amp half. `TRIM-OFFSET` sits **ahead** of the buffer |
| **TRIM-GAIN** | **200 Ω** multiturn cermet, **in series** with R2 | 0 → +2 % of ratio, **one-sided and now pointing the wrong way**: the justification was that the load divider only ever *reduces* gain, and the jack-side tap deleted the divider. Nominal is dead on 2.000 and the trimmer has no downward authority. Firmware's affine covers it, but the stated reason is stale — resolve at E9 |
| **TRIM-OFFSET** | 10 kΩ multiturn cermet + range resistors | **Before** the buffer, so it scales `V_ref` and therefore the intercept alone. `R-OFFINJ` is deleted |
| **R-OPAMP-IN** | 1 kΩ 1 % | Clamp-current protection on the (+) input. No gain error |
| **R-OUT-PROT** | 1 kΩ 1 %, **1206 ≥250 mW** | Short protection, **inside the DC feedback loop** |
| **C-FB-PITCH** | **2.2 nF C0G** | **From the op-amp OUTPUT to the (−) input — NOT "across R2".** See the warning below; this is the net that decides whether the stage is stable |
| **C-AA-PITCH** | **10 nF C0G** | 15.9 kHz against `R-OPAMP-IN`, **ahead of the op-amp**, outside any loop. Filters the DAC before it is amplified |
| **C-FILT-PITCH** | **10 nF C0G** | Restored at the jack. The low-impedance shunt at the connector, which nothing else provides |

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

**`C-FB-PITCH` is not a filter, and an earlier version of this page said it
was.** A capacitor across the feedback resistor of a **non-inverting** stage
cannot take the gain below unity:

```
G(s) = 1 + (R2/R1)/(1 + sR2C) = (2 + sRC)/(1 + sRC)
```

Pole at 15.9 kHz, **zero one octave above at 31.8 kHz**, flattening at gain 1.
**Maximum attenuation 6.02 dB, at any frequency, for any capacitor value.** It
is a shelf, not a pole, and that is topology rather than component choice. The
deleted 10 nF gave −16 dB at 100 kHz and −36 dB at 1 MHz.

At the 4 kHz update rate neither part does much about the zero-order-hold image
— ADR 0006 concedes that itself — so what was actually lost is the only
**low-impedance shunt at the connector**: DAC glitch energy, SPI hash in the
100 kHz–1 MHz decade, and RF arriving on two metres of patch cable.

**So the filtering is done twice, in the two places that work**, and
`C-FILT-PITCH` comes back:

- **`C-AA-PITCH`**, 10 nF from the `R-OPAMP-IN` node to `AGND` — 15.9 kHz
  against a node with **no loop around it**, filtering the DAC before it is
  amplified. This is what the corpus means by filtering upstream.
- **`C-FILT-PITCH`**, 10 nF back at the jack. **The reason given for deleting
  it does not survive**: two independent loop analyses put 10 nF at the jack
  and found the phase margin unchanged, because `C-FB-PITCH` ties the (−) input
  to the op-amp *output*, so β(∞) = 1 exactly and `R-OUT-PROT` isolates the
  jack above the handover. The feedback network is a **lead** at every passive
  load tried — open circuit, 200 pF, 800 pF, 10 nF, dead short. Cable
  capacitance is structurally incapable of putting lag in this loop.
- **`C-FB-PITCH` goes to 2.2 nF**, which with the jack cap restored is
  maximally flat: −3 dB at 12.2 kHz, inside ADR 0006's own 10–20 kHz window,
  and −41 dB at 1 MHz against the 6 dB the shelf gives alone.

> ### ⚠ `C-FB-PITCH` goes from the op-amp OUTPUT to the (−) input
>
> **Not "across the feedback resistor".** With the tap at the jack, `R2` spans
> *jack → (−)*, so a capacitor across `R2` connects the same two nodes and
> leaves `R-OUT-PROT` inside the loop at every frequency — which is the
> capacitive-load-in-the-loop case, at **18° of phase margin with 2 m of cable
> and under 10° with four destinations.**
>
> The drawing above is right. Three other places said "across the feedback
> resistor" and were wrong, and prose is what a layout gets built from.

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

**The load no longer matters**, which is the point of the jack-side tap: the
exact DC solve gives gain 2.020000 for every load from open circuit to 2 kΩ,
with about 1 ppm of residual. An earlier version of this section said to trim
against the real patch because the 1 kΩ divided against it. That error is gone.

**Two new bounds to check at E9**, both created by the tap:

- **It does not oscillate; it rings.** `Q = √(R_eff·C_load / R2·C_fb)`. Safe to
  about 10 nF, but joining PITCH to the MOD (82 nF) or BREATH (330 nF) jacks
  through a passive mult gives 44–67 % overshoot — several semitones of
  transient on every note. That failure mode did not exist with op-amp-side
  feedback.
- **With the jack shorted, DC feedback is exactly zero** and the amp rails. A
  3.5 mm plug shorts tip to sleeve on every insertion, so every patch-in is a
  brief rail excursion recovering through the loop.

## What limits accuracy, in order

**The 6× disagreement this table used to flag is resolved, and both published
numbers were wrong.** It was a pivot error: `∂Vout/∂k = Vdac − V_ref`, so a
*ratio* drift pivots at `Vout` = +2.5 V with a maximum lever of 2.25 V, while a
*reference* drift pivots at `Vout` = 0 with a lever of 7 V. Three documents
used 9 V, 7 V and 2.5 V for the same term.

| Term | Over 10 °C | Note |
|---|---|---|
| **DAC internal reference** | **0.42 cents** | **The largest term, and untrimmable** |
| LT5400 ratio tracking | 0.027 cents | |
| `TRIM-GAIN` tempco | **0.068 cents** | 200 Ω cermet. Second *smallest*, not "the largest line here" — so it does **not** defeat the matched network, costing 0.04 cents |
| LT5400 ratio tracking | ~0.1 cents | The reason it is not two discrete 0.1 % parts, which would be ~1.2 cents |
| DAC internal reference | ~0.5 cents | A gain term, per above |
| OPA2197 offset drift | <0.1 cents | An offset term, but a tiny one |
| DAC INL, ±4 LSB typical | ~0.4 cents | Curvature; firmware's multi-point correction, not a trimmer's job |

Nothing here approaches the **20-odd cents** of the dynamic, LED-correlated
terms that ADR 0006 fixes in the power tree and the ground plan. That remains
the right order of priority: the static budget was never the problem.

## Still open

- **Whether the LT5400 is worth it at all.** The trimmer does not defeat it —
  but with the DAC reference dominating at 0.42 cents, two 0.1 % / 10 ppm
  discretes give 0.38 cents, which is *comparable to a term you cannot trim*,
  for about $0.30 against about $8. The network's advantage is real and it is
  buried under a larger error. Worth a decision rather than an assumption.
- **The LT5400 option suffix**, if it stays. A 1:1 quad is the requirement and
  the orderable code must come off the option table, which this sandbox cannot
  reach. The claim that two spare sections can build the mod channels' 1:3 is
  **arithmetically impossible** — three sections against the fourth is all four.
- **`TRIM-OFFSET` is not buildable as described.** `V_ref` nominal *is*
  `VREFOUT`, and a divider can only go below it, so the nominal sits at an end
  stop with no downward authority. The trim network has to put 2.500 V at
  mid-travel — which means dividing `VREFOUT` and gaining it back, or injecting
  a small bipolar correction. E10, with `R-TRIM-RANGE`.
- **The (+) input has no DC path to ground.** Its only connection is a DAC pin
  that may be high-Z before power-on reset, so the output can sit at either
  rail during that window. This project already fixed the identical problem on
  the breath in-amp with `R-BIAS-INAMP`. `R-BIAS-DAC` now does it here — at the
  **DAC pin**, not after `R-OPAMP-IN`, where 100 kΩ would cost 1 % of gain.
- **Whether `TRIM-GAIN` is 1 kΩ or 500 Ω.** ±5 % of a 10 kΩ ratio wants ~1 kΩ
  of adjustment; whether that is too coarse for a comfortable multiturn feel is
  a bench question at E9.
- **The two spare LT5400 resistors.** Available, matched, and currently doing
  nothing. Worth a look when the mod channels are laid out.
