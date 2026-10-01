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
| `VREFOUT` | in | `module/dac8568` | — | The DAC's own reference out, into the trim network and the follower that make `V_ref`. The whole tracking argument below depends on this being the same node the DAC's full scale references. **3-state until firmware enables the reference** `[ds DAC8568CIPW.pdf p.31]`; `TRIM-OFFSET`'s 10 kΩ to `AGND_MOD` holds it at 0 V until then |
| `DAC ch1` | in | `module/dac8568` | `dac-rail` | Through `R-OPAMP-IN` into the (+) input |
| `PITCH` | out | `module/panel` | `pitch-cents-budget` | The panel jack. **DC feedback is tapped here, not at the op-amp output** — so whatever is patched in sits inside the loop |
| `MODULE ANALOG +12V`, `MODULE ANALOG −12V` | in | `module/power-entry` | — | `D-JACK-CLAMP` returns to both rails |
| `AGND_MOD` | ref | `module/power-entry` | `dig-gnd-topology` | The module analog ground, drawn `AGND`. `C-AA-PITCH`, `C-FILT-PITCH`, `D-ESD-PITCH` (at the jack's sleeve), the LT5400's exposed pad and its two spare sections go to it |

## The circuit

```
   VREFOUT ──┬──[R-VREF-SER 1k]────────┬── (+) ½ OPA2197 ────────────┬── V_ref = 2.500 V
   (2.500 V) │                         │   follower ×1.02            │   at mid-travel
             │                         │                             │
   [TRIM-OFFSET 10k]                   │   (−)──┬──[R-VREF-FB 200R]──┤
   VREFOUT to AGND                     │        │                    │
             │                         │  [R-VREF-GND 10k]── AGND    │
           wiper ──[R-VREF-INJ 22.1k]──┘                     [R-GAIN-CTR 100R]
                                                                     │
                                                              [R1 10k]  ┐ LT5400
                                                                     │  │ 1:1 pair
   DAC ch1 ──[R-OPAMP-IN 1k]──┐                                      │  │
   0.25…4.75 V                │                                      │  │
                              │                                ┌─────┴──┴────┐
                              └────────────────────────────────┤ +           │
                                                               │  ½ OPA2197  ├──┬── op-amp output
                              ┌────────────────────────────────┤ −           │  │
                              │                                └─────────────┘  │
                              ├──[C-FB-PITCH 2.2nF]──────────────────────────────┤   ← AC feedback
                              │                                                 │
                              │                                [D-JACK-CLAMP BAV99]── ±12 V
                              │                                                 │
                              │                              [R-OUT-PROT 1k, 1206]
                              │                                                 │
                              └──[R2 10k]─[TRIM-GAIN 200R]──────────────────────┴──┬── PITCH jack
                                  LT5400   CW end strapped to its wiper            │   ← DC feedback
                                                                       [D-ESD-PITCH PESD15VL1BA]── AGND
                                                                       at the jack: jack board
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
protection for the power-up window where the DAC is on `dac-rail` and the op-amp is
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

*(This is why the DAC's internal reference, a gain term, is the largest entry
in the budget below and still acceptable. ADR 0006's own reference figure and
its "an order of magnitude inside the resistors" ranking predate the matched
network and the corrected pivots; the budget below replaces both, and ADR 0006
says so.)*

## Component values

| Ref | Value | Job |
|---|---|---|
| **R1, R2** | 10 kΩ, **1:1 matched** (LT5400) | Sets gain = 2 and the −2.5 V intercept together |
| **V_ref** | 2.500 V at `TRIM-OFFSET`'s mid-travel, buffered from `VREFOUT` | One op-amp half at gain 1.02. The trim sits **ahead** of the buffer — see *The offset trim* |
| **TRIM-GAIN** | **200 Ω** multiturn cermet, **in series** with R2, CW end strapped to the wiper; **`R-GAIN-CTR` 100 Ω** in series with R1 | Ratio `(R2 + t)/(R1 + 100 Ω)`, t = 0 → 200 Ω: **±1 %, bipolar**, exactly 1 at mid-travel. Bipolar because the DAC's gain error is, ±0.15 % of FSR max `[ds DAC8568CIPW.pdf p.3]`. The strap makes a dirty track fail to a known resistance, not open |
| **TRIM-OFFSET** | 10 kΩ multiturn cermet across `VREFOUT`–`AGND`, wiper through `R-VREF-INJ` 22.1 kΩ; `R-VREF-SER` 1 kΩ from `VREFOUT`; follower gain from `R-VREF-FB` 200 Ω / `R-VREF-GND` 10 kΩ, all four 0.1 % 25 ppm/°C | **Before** the buffer, so it moves `V_ref` and therefore the intercept alone: −60 / +50 mV about 2.500 V. See *The offset trim* |
| **R-OPAMP-IN** | 1 kΩ 1 % | Clamp-current protection on the (+) input. No gain error. The follower's is `R-VREF-SER` |
| **R-OUT-PROT** | 1 kΩ 1 %, **1206 ≥500 mW** (shared spec, qty 6 — ≥250 mW here until
2026-09-22, which is `R-SER-BREATH-INST`'s rating, a different part) | Short protection, **inside the DC feedback loop** |
| **C-FB-PITCH** | **2.2 nF C0G** | **From the op-amp OUTPUT to the (−) input — NOT "across R2".** See the warning below; this is the net that decides whether the stage is stable |
| **C-AA-PITCH** | **10 nF C0G** | 15.9 kHz against `R-OPAMP-IN`, **ahead of the op-amp**, outside any loop. Filters the DAC before it is amplified |
| **C-FILT-PITCH** | **10 nF C0G** | Restored at the jack. The low-impedance shunt at the connector, which nothing else provides |

**Power-on is 0.000 V, not "subsonic".** `V_ref` comes from the DAC's
internal reference, which is **disabled until firmware writes an enable** — and
while it is disabled the `VREFIN/VREFOUT` pin is **3-state**, *"disconnected
from the VREFIN/VREFOUT pin (3-state output)"* `[ds DAC8568CIPW.pdf p.31]`, not
0 V. What makes it 0 V is `TRIM-OFFSET`: its 10 kΩ track runs from that pin to
`AGND_MOD`, so the undriven node sits at ground. With the C grade's zero-scale
power-on, *both* terms are then zero and the jack sits at **0 V, a VCO's base
note** (to the DAC's zero-code error, +8 mV at most: ADR 0006's power-on
table), until that write. After it, `CLR` parks at −2.500 V. ADR 0006's power-on table asserts
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

## The offset trim — made buildable 2026-09-30

The first version divided `VREFOUT` down with the trimmer, which can only go
*below* 2.500 V: the nominal sat at an end stop with no downward authority.
Now the trimmer injects a small correction into the follower, and the
follower gains it back:

```
V_ref = VREFOUT · [1 − a·(1 − w)] · (1 + g)
        a = R-VREF-SER / (R-VREF-SER + R-VREF-INJ + R_w)     R_w = 10 kΩ·w(1 − w), the wiper's own
        g = R-VREF-FB / R-VREF-GND = 0.0200
```

`[calc]` with the values fitted, `w` the wiper's position from the `AGND` end:

| `w` | `a` | `V_ref` | vs 2.500 V |
|---|---|---|---|
| 0 (full CCW) | 0.0433 | 2.4396 V | **−60 mV** |
| 0.5 (mid) | 0.0391 | 2.5002 V | +0.2 mV |
| 1 (full CW) | 0.0433 | 2.5500 V | **+50 mV** |

72 cents of intercept one way and 60 the other `[calc: 60.4 mV and 49.8 mV
at 1.2 cents/mV]` — asymmetric about the nominal, which costs nothing, and the gain `1 + k` is untouched.
`sim/` measures both ends on the stage as netlisted (`trim-offset-ccw`,
`trim-offset-cw`). **Its drift is
small by construction**: the trimmer and `R-VREF-INJ` reach only `a` ≈ 4 % of
`V_ref`, and the follower's gain ratio only `g/(1 + g)` ≈ 2 %, so 25 ppm/°C
parts contribute a few ppm of `V_ref` over 10 °C — the *V_ref trim network*
row below. `R-VREF-SER` is also the follower's clamp-current protection, the
job `R-OPAMP-IN` does for the channels.

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
| `R2` + `TRIM-GAIN` from the **jack** | DC to ~7 kHz | Sets the transfer function against the load, whatever it is |
| `C-FB-PITCH` **2.2 nF** from the **op-amp output** | above ~7 kHz | Takes over before `R-OUT-PROT` and the cable can put phase in the loop. The handover is `R2 + TRIM-GAIN` against 2.2 nF: 1/(2π · 10.1 kΩ · 2.2 nF) = 7.2 kHz `[calc]` |

**`C-FB-PITCH` is not a filter, and an earlier version of this page said it
was.** A capacitor across the feedback resistor of a **non-inverting** stage
cannot take the gain below unity:

```
G(s) = 1 + (R2/R1)/(1 + sR2C) = (2 + sRC)/(1 + sRC)
```

With `R` = `R2 + TRIM-GAIN` = 10.1 kΩ at mid-travel and `C` = 2.2 nF: pole at
7.2 kHz, **zero one octave above at 14.3 kHz** `[calc]`, flattening at gain 1.
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
exact DC solve gives the same gain for every load from open circuit to 2 kΩ,
with about 1 ppm of residual — 2.000 with both trims at mid-travel, which
`sim/` measures on the stage as netlisted (`dc-transfer`). An earlier version of this section said to trim
against the real patch because the 1 kΩ divided against it. That error is gone.

**Two new bounds to check at E9**, both created by the tap:

- **It does not oscillate; it rings.** `Q = √(R_eff·C_load / R2·C_fb)`. Safe to
  about 10 nF, but joining PITCH to the MOD (82 nF) or BREATH (330 nF) jacks
  through a passive mult gives the overshoot in `pitch-mult-overshoot`
  (simulated, `sim/`) — several semitones of transient on every note. That failure mode did not exist with op-amp-side
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

**This is the budget — `pitch-cents-budget`: 0.76 cents worst-case linear
sum, 0.45 cents RSS**, for drift over 10 °C once the trims are set, at the
worst note of −2 → +7 V `[calc]`. At 1 V/oct, 1 mV is 1.2 cents; a gain term
takes the lever of its pivot, an offset term does not.

| Term | Spec | Lever | Over 10 °C |
|---|---|---|---|
| **DAC internal reference** | 5 ppm/°C max, C grade `[ds DAC8568CIPW.pdf p.4]` | 7 V (pivots at 0 V) | **0.42 cents** — the largest, and untrimmable |
| DAC gain temperature coefficient | ±1 ppm of FSR/°C typ `[p.3]` | 10 V of jack span | 0.12 cents (typical: no maximum published) |
| DAC offset drift | ±0.5 µV/°C typ `[p.3]` | ×2 | 0.012 cents |
| LT5400 ratio tracking | 0.2 ppm/°C typ `[ds LT5400.pdf p.1]`, taken at 1 ppm/°C | 2.25 V (ratio pivots at +2.5 V) | 0.027 cents |
| `TRIM-GAIN` against `R-GAIN-CTR` | ~100 ppm/°C cermet, at mid-travel 100 Ω of 10 kΩ | 2.25 V | 0.034 cents |
| *V_ref* trim network | 25 ppm/°C, two ratios scaled by `g/(1+g)` and `a·(1−w)` | ×1 (an offset) | 0.06 cents |
| OPA2197 offset drift, both halves | ±2.5 µV/°C max `[ds OPA2197.pdf p.7]` | follower ×1, stage ×2 | 0.09 cents |
| **Linear sum / RSS** | | | **0.76 / 0.45 cents** |

*Not in it*: what the trims and firmware's affine take out once (DAC INL, the
initial offsets and ratios), and the breath-correlated ground-path terms on
[`power-entry.md`](../power-entry/power-entry.md) — an order of magnitude
larger until 2026-09-30, and removed at the source since by ADR 0027 (the
instrument's supply is isolated; under 0.01 cents is left).

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

Nothing here approached the dynamic, LED- and breath-correlated terms that
`power-entry.md` dealt with in the power tree and the ground plan; since ADR
0027 those are below this budget, which now is the largest term in the pitch
path.

## The jack-side ESD clamp — `D-ESD-PITCH`

**The jack tip reaches the LT5400.** `JACK_TIP` runs through `TRIM-GAIN`'s
CCW–wiper section, 0–200 Ω, to `R2` of `RN-PITCH`, and the LT5400 is *"designed
without explicit ESD internal protection diodes"*: ±1 kV human body, and *"ESD
beyond this voltage can damage or degrade the device including causing
pin-to-pin shorts"* `[ds LT5400.pdf p.6]`. `D-JACK-CLAMP` cannot help — it sits
on the op-amp side of `R-OUT-PROT`, which is where it has to be (`bom.csv`).

**So a bidirectional clamp sits at the jack**, tip to sleeve, on the module
jack board's page of this circuit (`pitch-stage.jack.kicad_sch`) — the
LT5400's own Figure 1 second option, *"bidirectional Zeners to ground"* at the
connector `[ds LT5400.pdf p.6]`. The jack board carries no rails, so the
first option (diodes to the supplies) is not available there, and a clamp to
`AGND_MOD` cannot back-power the module the way a rail clamp at the jack did.
A strike is clamped before it crosses `J-B2B-MOD` to module-main, where
`C-FILT-PITCH` then holds whatever gets past.

| Requirement | `PESD15VL1BA` `[ds NEXPERIA-PESD15VL1BA.pdf p.3–4]` |
|---|---|
| Bidirectional, not conducting anywhere a patch can put the jack: −2.5…+7.5 V driven, ±12 V from another module | V_RWM 15 V, V_BR 17.1 V min |
| Below the LT5400's 80 V across any two pins `[ds LT5400.pdf p.2]` | V_CL 25 V at 1 A, 44 V at 5 A (8/20 µs); IEC 61000-4-2 30 kV contact |
| Low leakage | I_RM 50 nA max at 15 V |
| Low capacitance | 16 pF typ at 0 V |

**It costs no accuracy and no stability.** It is on `JACK_TIP`, the DC
feedback node, so its leakage is a load inside the loop like any VCO, and its
capacitance is 0.16 % of `C-FILT-PITCH`'s 10 nF beside it. `sim/` runs every
deck twice, with the clamp and without, and asserts the difference: under
1 µV at the jack across the DAC's window, under 0.1 point of overshoot on an
octave step into a VCO and 200 pF or 800 pF of cable, under 0.1° of phase margin
at every load, with the clamp's capacitance taken to twice its typical.

**Layout:** at the jack's tip and sleeve pads, before the trace leaves for
`J-B2B-MOD`. `C-FILT-PITCH` on module-main belongs at `J-B2B-MOD` pin 14, not
at the op-amp: the connector end is where the shunt is wanted.

## Settled 2026-09-30

- **The LT5400's exposed pad goes to `AGND_MOD`**, the quiet AC ground the
  datasheet asks for — *"do not tie the exposed pad to noisy signals or noisy
  grounds … connecting the exposed pad to a quiet AC ground is recommended"*
  `[ds LT5400.pdf p.6]`. With the four-layer ground settled
  (`dig-gnd-topology`) `AGND_MOD` is the region under this stage and carries
  neither the umbilical's return nor the SPI's, so it is the quiet one. The
  symbol carries the pad as pin 9 (`EP`), and the two spare sections are tied
  to `AGND_MOD` at both ends so they are not floating plates beside the
  network. Order code **`LT5400BIMS8E-1#PBF`** (`R-PRECISION` gives why B and
  I).
- **`TRIM-OFFSET` is buildable** — *The offset trim*, above.
- **`TRIM-GAIN` is bipolar**, ±1 %, centred by `R-GAIN-CTR`, and its CW end
  is strapped to the wiper.
- **The (+) input's DC path** is `R-BIAS-DAC`, at the DAC pin.
- **`R-OPAMP-IN` is six.** The follower's clamp-current protection is
  `R-VREF-SER`, a thin-film part because it is also half of a ratio that sets
  `V_ref`.

## Still open

- **Pitch stability into worst-case cable, and the ring into a passive
  mult** (*Two new bounds to check at E9*, above). Simulated —
  `pitch-mult-overshoot`, `sim/` — and **decided by E9** on the bench.
