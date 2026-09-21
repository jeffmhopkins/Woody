# Breath receive stage — schematic

**Status:** Drawn 2026-09-21. This page did not exist, and its absence was the
single largest source of findings in the cold review.

Five separate findings — the zero's polarity, the missing bias return, the
missing gain resistor, the open-loop zero correction, and half of "nothing mutes
breath" — turned out to be **five symptoms of one absent document**. Two expert
reviewers built two *different* schematics from the same ADR prose and disagreed
on the resistor count; six different in-amp gains were derived, each
arithmetically correct for a different reading. The ADR names the parts and none
of the topology.

This is the topology. Where it disagrees with ADR 0003's prose, this page wins
and the ADR gets corrected.

## The circuit

```
  INSTRUMENT (bottom cluster board)                 |  2 m Cat5  |   MODULE
                                                    |            |
   MPXV4006DP ──┬── ½ OPA2197 ───[R1 1k]──────────── BREATH (pin 1) ──┐
   (VS = REF5050 5.000 V)                            (twisted pair)   │
                 │                                                    │
                 └── 0.6× divider ── C-AA-ADC ── MCP3202 CH0          │
                                                                      │
   analog star ─────────────────────────────────── AGND   (pin 2) ──┐ │
   (no power current)                                               │ │
                                                                    │ │
  ──────────────────────────────────────────────────────────────────┼─┼───────
                                                                    │ │
                              BAV99 to ±12 V, both legs  ◄──────────┼─┤
                                                                    │ │
                                    ┌───[R2 10k 0.1%]───────────────┘ │
                                    │                                 │
                                    │       ┌───[R3 10k 0.1%]─────────┘
                                    │       │
                                    ├──[C_cm 1.5nF]── AGND(module)
                                    │       │
                                    ├───────┼──[C_diff 15nF]───┐
                                    │       │                  │
                                    │       ├──[C_cm 1.5nF]── AGND(module)
                                    │       │                  │
                    [R4 1M]─────────┤       ├──────[R5 1M]     │
                         │          │       │           │      │
                    AGND(module)    │       │      AGND(module) │
                                    │       │                  │
                                 ┌──▼───────▼──┐               │
                                 │  IN−     IN+ │  INA828       │
                                 │              │               │
                                 │  R_G 42.2k   │◄── G = 2.185  │
                                 │              │               │
                                 │  REF ────────┼── AGND(module), HARD
                                 │              │   (no divider, no DAC)
                                 └──────┬───────┘
                                        │  Vout = −2.185·(V_BREATH − V_AGND)
                                        │       = −0.44 V at rest, −10 V at full
                                        │
                                  ┌─────▼──────────────────────┐
                                  │  INVERTING gain + offset   │
                                  │  POT-GAIN then POT-OFFSET  │
                                  │  ½ OPA2197                 │
                                  └─────┬──────────────────────┘
                                        │
                                   [1k]─┴─[C 330nF]── BREATH jack
```

## `REF` ties to ground, and the polarity question dissolved twice

**The original showstopper.** The MPXV4006DP sits at **+0.2 V at zero pressure
by design** (spec range 0.152–0.378 V). An in-amp is additive at `REF`:
`Vout = G·(V+ − V−) + V_REF`. With BREATH on IN+, nulling that pedestal needs
`V_REF ≈ −0.43 V`, and the DAC channel proposed to drive `REF` is unipolar
0–5 V — it can only push the floor *up*. That left 4–9 % of full scale standing
at the jack at rest and an auto-zero with authority in one direction only.

**The first fix was to swap the inputs.** With BREATH on IN−, a *positive* `REF`
subtracts, which is what a unipolar DAC can produce.

**Then the DAC channel was deleted entirely** — it was correcting a signal
firmware cannot measure (ADR 0003, ADR 0006) — which removes the premise the
swap was argued from. So the swap needs a reason of its own, and it has one:

**`REF` now ties hard to module analog ground.** The in-amp output is
`−2.185·(V_BREATH − V_AGND)`: −0.44 V at rest, −10 V at full breath, entirely
within the −12 V rail. The downstream stage is **inverting**, which is the
topology that wants a negative-going input — an inverting summer does gain and
offset with two pots into one virtual ground, where a non-inverting stage would
have the offset injection interact with the gain setting. One op-amp half
instead of two, and the panel knobs behave independently, which is what
"gain first, then offset" (ADR 0006) means physically.

So the swap survives on the downstream stage's topology rather than on the DAC's
unipolarity. Recorded explicitly because a decision whose original justification
has been removed is exactly the kind of thing that survives by inertia.

**`REF` must tie *hard*, or to a buffer — never through a divider.** Source
impedance at an in-amp's `REF` pin adds directly to its internal resistor
network and degrades CMRR one-for-one. It is the same class of mistake as a
single-ended capacitor on one input leg, and it is easy to make because `REF`
looks like an input.

## Component values

| Ref | Value | Job |
|---|---|---|
| **R1** | 1 kΩ | Instrument-side series protection, on the driver's output |
| **R2, R3** | 10 kΩ 0.1 % | Module-side series protection. **Matched** — but see below |
| **R4, R5** | 1 MΩ | **Common-mode bias return.** Without these the in-amp's inputs float when the cable is unplugged and it saturates to a rail |
| **C_diff** | 15 nF C0G | 531 Hz differential pole, **ahead of the in-amp** |
| **C_cm** | 1.5 nF C0G ×2 | Common-mode poles, deliberately 1/10 of C_diff |
| **R_G** | 42.2 kΩ 0.1 % | INA828, `G = 1 + 50k/R_G` = **2.185** |
| **REF** | hard to `AGND`(module) | Output reference. No DAC, no divider — see above |
| **Output RC** | 1 kΩ + 330 nF film | ~480 Hz reconstruction at the jack |

### The gain, derived

| | |
|---|---|
| Sensor span, 0.2 → 4.8 V | 4.6 V |
| Jack span wanted | 10 V |
| Raw gain needed | 2.174 |
| Loss in the 2 × 1 MΩ bias pair against 2 × 11 kΩ series | ×0.9891 |
| Gain needed at the in-amp | 2.198 |
| **R_G = 42.2 kΩ → G = 2.1848, effective 2.1611** | **jack span 9.94 V** |

The 0.6 % shortfall is absorbed by the panel gain knob, which exists to fit the
span to the patch. Do not chase it with a non-standard resistor.

### Why the bias resistors do not break the sense return

ADR 0003's rule is that `AGND` carries no power current. 1 MΩ to module analog
ground diverts tens of nanoamps against a ~350 mA power return — about 0.2 ppm.
The rule survives in substance. **But the rule as written in ADR 0003 forbids
the thing that makes the receiver work, and must be restated** to mean "no
*power* current", which is what it always meant.

### Why C_diff is ten times C_cm

A single-ended capacitor to ground on one leg is a common-mode-to-differential
converter, and the review found a proposal to do exactly that — it would cap
effective CMRR at about 15 dB at 100 Hz, which is worse than every other term in
the design combined. Making the differential capacitor dominant means a
mismatch between the two common-mode capacitors is divided by the ratio before
it reaches the difference signal.

### Why the filter is ahead of the in-amp, not after it

Two reasons, and one proposal in the review got this backwards. A filter after
the amplifier cannot prevent **RF rectification** at the input stage — and there
is a 2.4 GHz radio two metres away on the same cable bundle. It also cannot
prevent the amplifier slewing on out-of-band energy.

## What this settles

| Finding | Resolution |
|---|---|
| Ambient zero has the wrong polarity | **Deleted** — there is no ambient-zero injection. `REF` is grounded and the panel offset knob is the analog path's only zero authority |
| The zero correction is open-loop across two representations | **Deleted with it** — firmware now zeroes only the copy it measures |
| No common-mode bias return | **Fixed** — R4, R5 |
| No in-amp gain resistor | **Fixed** — R_G = 42.2 kΩ, derived above |
| The 100 kΩ differential pulldown | **Deleted.** R4/R5 do its job without its 1–17 % attenuation, and the review could not agree which figure applied |
| "Six different in-amp gains" | One gain, one derivation, shown |
| Which in-amp | **INA828** — the E96 value lands cleanly and its lower bandwidth suits a 500 Hz channel |
| Where the 500 Hz pole goes | Ahead of the in-amp, differential-dominant |

## Commissioning

With the body at room temperature and no breath at the mouthpiece, set the
**panel offset knob** so the jack reads 0 V on a meter, then the **gain knob**
for the span the patch wants. That is the analog path's zero, and it is the only
one. Thermal drift afterwards is ~23 mV in 10 V over a full warm-up — a quarter
turn if it ever bothers you.

**E10 scopes the jack**, not the display. The two representations are calibrated
separately on purpose, so a flat bar on the screen is no longer evidence about
the output.

## Still open

- **What the jack does when the watchdog fires.** `CLR` reaches the DAC
  channels; breath touches none of them — and now that `REF` is grounded, it
  touches the breath stage in no way at all, where previously `CLR` would have
  yanked the zero out from under it. An analog path cannot latch at a level the
  player is not producing: it follows the sensor, and the sensor follows the
  room. Accepted risk pending E10.
- **The downstream gain/offset stage** is drawn as a block. Its own values, its
  offset reference (the buffered `VREFOUT` created for pitch is the obvious
  node), and whether the gain pot's wiper needs a buffer are E10 work.
