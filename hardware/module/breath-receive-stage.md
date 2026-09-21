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
                                 │  REF ◄───────┼── ½ OPA2197 ◄─ DAC ch6
                                 │              │   (ambient zero, 0…+5 V)
                                 └──────┬───────┘
                                        │  Vout = −2.185·(V_BREATH − V_AGND) + V_REF
                                        │
                                  ┌─────▼──────────────────────┐
                                  │  INVERTING gain + offset   │
                                  │  POT-GAIN then POT-OFFSET  │
                                  │  ½ OPA2197                 │
                                  └─────┬──────────────────────┘
                                        │
                                   [1k]─┴─[C 330nF]── BREATH jack
```

## Why BREATH drives IN− — this is the fix, not a detail

**This one wiring choice dissolves the polarity showstopper.**

An in-amp is additive at REF: `Vout = G·(V+ − V−) + V_REF`. The MPXV4006DP sits
at **+0.2 V at zero pressure by design** (spec range 0.152–0.378 V). With BREATH
on IN+, nulling that pedestal needs `V_REF ≈ −0.43 V` — and DAC channel 6 is
unipolar 0–5 V and can only push the floor *up*. The result would be 4–9 % of
full scale standing at the jack at rest, an auto-zero with authority in only one
direction, and the panel offset knob conscripted into a technical job.

**With BREATH on IN−, a positive REF subtracts**, which is exactly what the
unipolar DAC can produce. The in-amp output is then negative-going, and the
downstream gain/offset stage — which exists anyway for the panel knobs — is made
inverting. **Zero extra parts.**

ADR 0003 states both injection points 174 lines apart: "its REF pin is the
natural injection point" and "into the module's analog summing stage". The REF
pin is correct, and the input swap is what makes it work.

## Component values

| Ref | Value | Job |
|---|---|---|
| **R1** | 1 kΩ | Instrument-side series protection, on the driver's output |
| **R2, R3** | 10 kΩ 0.1 % | Module-side series protection. **Matched** — but see below |
| **R4, R5** | 1 MΩ | **Common-mode bias return.** Without these the in-amp's inputs float when the cable is unplugged and it saturates to a rail |
| **C_diff** | 15 nF C0G | 531 Hz differential pole, **ahead of the in-amp** |
| **C_cm** | 1.5 nF C0G ×2 | Common-mode poles, deliberately 1/10 of C_diff |
| **R_G** | 42.2 kΩ 0.1 % | INA828, `G = 1 + 50k/R_G` = **2.185** |
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
| Ambient zero has the wrong polarity | **Dissolved** — inputs swapped, downstream stage inverting |
| No common-mode bias return | **Fixed** — R4, R5 |
| No in-amp gain resistor | **Fixed** — R_G = 42.2 kΩ, derived above |
| The 100 kΩ differential pulldown | **Deleted.** R4/R5 do its job without its 1–17 % attenuation, and the review could not agree which figure applied |
| "Six different in-amp gains" | One gain, one derivation, shown |
| Which in-amp | **INA828** — the E96 value lands cleanly and its lower bandwidth suits a 500 Hz channel |
| Where the 500 Hz pole goes | Ahead of the in-amp, differential-dominant |

## Still open

- **The zero correction is open-loop across two representations.** Firmware
  reads the ADC *before* the umbilical; the zero is injected *after* it. Firmware
  can null the digital copy perfectly while the jack sits at a standing offset.
  Not fixable here — it needs either a readback or an acceptance that the two
  are separately calibrated. Recorded, not solved.
- **What the jack does when the watchdog fires.** `CLR` reaches the five DAC
  channels; breath does not pass through the DAC. One reviewer notes the
  severity collapses once this schematic is built, because an analog path cannot
  latch at a level the player is not producing — it follows the sensor, and the
  sensor follows the room. Left as an accepted risk pending E10.
- **The downstream gain/offset stage** is drawn as a block. Its own values, and
  whether the gain pot's wiper needs a buffer, are E10 work.
