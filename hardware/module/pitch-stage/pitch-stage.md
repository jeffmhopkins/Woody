# Pitch stage — schematic

**Status:** Drawn 2026-09-21. Second module page, after
[the breath receive stage](../breath-receive-stage/breath-receive-stage.md).

The ADRs specify this channel's *behaviour* in detail — 1 V/oct, −2 to +7 V,
trimmers for gain and offset, an LT5400 matched network, an offset reference
divided from the buffered `VREFOUT` — and have never specified its *topology*.
Drawing it changes the answer.

## Interfaces

Every net that crosses this circuit's boundary. Quantities appear **only** as a
citation into `config/figures.yaml` — this table names nodes, it does not
restate values.

The `Dir` and `Peer` columns are defined once in
[`hardware/README.md`](../../README.md#the-interfaces-table).

| Node | Dir | Peer | Figure | Note |
|---|---|---|---|---|
| `VREFOUT` | in | `module/dac8568` | — | The DAC's own reference out. Trimmed by `TRIM-OFFSET`, then buffered. The whole tracking argument below depends on this being the same node the DAC's full scale references |
| `DAC ch1` | in | `module/dac8568` | `dac-rail` | Through `R-OPAMP-IN` into the (+) input |
| `PITCH` | out | `module/panel` | `pitch-cents-budget` | The panel jack. **DC feedback is tapped here, not at the op-amp output** — so whatever is patched in sits inside the loop |
| `MODULE ANALOG +12V`, `MODULE ANALOG −12V` | in | `module/power-entry` | — | `D-JACK-CLAMP` returns to both rails |
| `AGND_MOD` | ref | `module/power-entry` | `dig-gnd-topology` | The module analog star, drawn `AGND`. `C-AA-PITCH` and `C-FILT-PITCH` shunt to it. Not a return path — see the figure |

## The circuit

```
   VREFOUT ──[TRIM-OFFSET 10k]──┬── ½ OPA2197 ──┬── V_ref ≈ 2.500 V
   (2.500 V)   + range resistors│   follower    │   (trimmed, buffered)
                                └───────────────┘
                                                │
                                          [R1 10k]  ┐ LT5400
                                                │   │ 1:1 pair
                                                │   │
   DAC ch1 ──[R-OPAMP-IN 1k]──┐                 │   │
   0.25…4.75 V                │                 │   │
                              │           ┌─────┴───┴───┐
                              └───────────┤ +           │
                                          │  ½ OPA2197  ├──┬── op-amp output
                              ┌───────────┤ −           │  │
                              │           └─────────────┘  │
                              │                            │
                              ├──[C-FB-PITCH 2.2nF]──────────┤   ← AC feedback
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

*(Why this is the topology's defining identity rather than a lucky coincidence,
and what that means for the mod channels — [`notes.md`](notes.md).)*

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
| **R-OUT-PROT** | 1 kΩ 1 %, **1206 ≥500 mW** (shared spec, qty 6 — ≥250 mW here until
2026-09-22, which is `R-SER-BREATH-INST`'s rating, a different part) | Short protection, **inside the DC feedback loop** |
| **C-FB-PITCH** | **2.2 nF C0G** | **From the op-amp OUTPUT to the (−) input — NOT "across R2".** See the warning below; this is the net that decides whether the stage is stable |
| **C-AA-PITCH** | **10 nF C0G** | 15.9 kHz against `R-OPAMP-IN`, **ahead of the op-amp**, outside any loop. Filters the DAC before it is amplified |
| **C-FILT-PITCH** | **10 nF C0G** | Restored at the jack. The low-impedance shunt at the connector, which nothing else provides |

**Power-on is 0.000 V, not "subsonic".** `V_ref` is the DAC's internal
reference, which is **disabled until firmware writes an enable** — so *both*
terms are zero and the jack sits at **0 V, a VCO's base note**, until that
write. After it, `CLR` parks at −2.500 V. ADR 0006's power-on table asserts
"below −2 V" for both; they are different states, 2.5 V apart.

**This is the same argument that moved the breath zero off `VREFOUT`, and it
was not applied here.** Pitch cannot move off it — the whole tracking argument
above depends on referencing the same node the DAC's full scale references —
so this is an accepted compromise rather than a defect, and it carries a
firmware requirement: **the reference-enable must be firmware's first DAC
write**, before any channel data, and it is in the sticky-register set that
gets periodically refreshed (`firmware/README.md`).

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
| `C-FB-PITCH` **2.2 nF** from the **op-amp output** | above ~12 kHz | Takes over before `R-OUT-PROT` and the cable can put phase in the loop. This row said **1 nF / ~16 kHz** until 2026-09-21; the value went to 2.2 nF when `C-FILT-PITCH` was restored below, and this row did not follow |

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

**The network stays, and the ranking is the reason it needed deciding.** Two
0.1 % / 10 ppm discretes would give 0.38 cents — fifteen times worse than the
LT5400 and yet *comparable to the DAC reference term above it*, which cannot be
trimmed at all. So the network's advantage is real and currently masked.

It is kept anyway, on a one-off: $8 permanently solves the one term in the
chain that can be permanently solved, on a board built once. If the reference
term is ever attacked — an external reference is the obvious way — the network
has to be there already for that to be worth doing, and retrofitting it to a
populated board is not a five-minute job. The option-code lookup is.
*(The superseded version of this table, which contradicted the live one twelve
lines above it, is in [`notes.md`](notes.md).)*

Nothing here approaches the **20-odd cents** of the dynamic, LED-correlated
terms that ADR 0006 fixes in the power tree and the ground plan. That remains
the right order of priority: the static budget was never the problem.

## Still open

- **The LT5400's exposed pad has nowhere to go, and it is layout-blocking.**
  The pad is 1.88 × 1.68 mm, floating, and couples **5.5 pF** to the resistors
  against only 1.4 pF resistor-to-resistor — so it is the dominant stray on the
  1 V/oct network, and nothing in this corpus says which ground it attaches to.
  ADI says not a noisy one. **Decided by:** the 2-layer-or-4 decision and the
  layout, not after it. Full reading of the banked datasheet, including the
  option suffix that closed and the revision caveat, is in
  [`notes.md`](notes.md).
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
- **Whether 200 Ω is the right `TRIM-GAIN`.** It is 0 → +2 % and one-sided,
  and with the load divider gone it has no downward authority at all. Whether
  it should be bipolar (fixed leg slightly under nominal, trimmer bracketing
  it) or deleted in favour of firmware is an E9 question.
- **A two-terminal series trimmer fails open to the rail.** Strap the wiper to
  one end so a dirty track degrades to a known resistance rather than an open
  circuit. That is a footprint decision, not a value.
- **The seventh `R-OPAMP-IN` has no home.** The row is qty 7 and
  [`mod-channels.md`](../mod-channels/mod-channels.md) allocates it as pitch,
  the four mods, the mod reference buffer and *the `VREFOUT` follower* — but
  the follower's input is drawn straight off `TRIM-OFFSET`'s wiper with no
  series resistor, and the value table above does not list one. Six are placed
  in netlists and `tools/check-netlist.py` prints the shortfall every run.
  **Decided by:** whether that (+) input needs clamp-current protection when
  the DAC pin reaches it through a 10 kΩ trimmer. If it does, the part belongs
  here and the drawing gains a label; if it does not, the row is qty 6.
- **The two spare LT5400 resistors.** Available, matched, and currently doing
  nothing. Worth a look when the mod channels are laid out.
