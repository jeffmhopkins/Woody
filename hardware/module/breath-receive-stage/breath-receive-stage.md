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

## Interfaces

Every net and every part that crosses this circuit's boundary. Quantities
appear **only** as a citation into `config/figures.yaml` — this table names
nodes, it does not restate values.

**This circuit is one half of a chain that crosses two boards.** The sensor,
its excitation buffer and `R1`/`R1b` sit on the carrier, at the far end of the
umbilical; the differential pole, the effective gain and the CMRR budget
derived on this page are derived from them. Every row with a `carrier/…` peer
is a number this page uses and does not own — and every part in one is
instrument-side, inside a bonded body, and unretrofittable.

| Node / part | Dir | Peer | Figure | Note |
|---|---|---|---|---|
| `BREATH` | in | `carrier/carrier.md`, umbilical | `umbilical-pinmap`, `sensor-full-scale` | The sensor's buffered output, arriving through the instrument-side `R1`. Drives `IN−` through `R3` |
| `AGND` | in | `carrier/carrier.md`, umbilical | `umbilical-pinmap` | The instrument's analog star, arriving through the instrument-side `R1b`. Drives `IN+` through `R2`: on this page it is **a signal leg, not a local ground**, and the twisted pair's other conductor |
| `R1`, `R1b` (`R-SER-BREATH-INST`) | — | `carrier/carrier.md` | — | Both legs' series resistance sets the differential pole against `C_diff`, and their match is what the bias pair's balance is measured against. Neither part is on this board |
| `MPXV4006DP` and its `VS` reference buffer | — | `carrier/carrier.md` | `sensor-full-scale`, `riso-ref-topology`, `cref-out-node`, `opa2197-output-impedance` | Sets the span this page multiplies and the pedestal `TRIM-BREATH-ZERO` nulls. Not this page's circuit — see [`notes.md`](notes.md) |
| in-amp output | out | `module/breath-output-stage` | `inamp-full-scale` | **Owned here.** Into the panel GAIN/OFFSET stage, which inverts |
| LM317 rail | in | `module/power-entry` | `dac-rail` | Feeds `TRIM-BREATH-ZERO` and its buffer. Never `VREFOUT`, which is disabled until firmware enables it |
| `±12 V` | in | `module/power-entry` | — | The INA828, both OPA2197 halves, and the BAV99 legs on the input pair and at the jack |
| `AGND` (module) | ref | `module/power-entry` | `dig-gnd-topology` | Where `R4`, `R5`, both `C_cm` and the output RC return |
| `CLR` | — | `module/digital-and-supervision` | — | **Reaches no part of this circuit**, which is the whole of what the `CLR` section below settles |

## The circuit

```
  INSTRUMENT (bottom cluster board)                 |  2 m Cat5  |   MODULE
                                                    |            |
   MPXV4006DP ──┬── ½ OPA2197 ───[R1 1k]──────────── BREATH (pin 1) ──┐
                 │                          ↓ to IN−, via R3            │
   (VS = REF5050 5.000 V)                            (twisted pair)   │
                 │                                                    │
                 └── 0.6× divider ── C-AA-ADC ── MCP3202 CH0          │
                                                                      │
   analog star ──[R1b 1k]──────────────────────── AGND   (pin 2) ──┐ │
   (no power current)                       ↑ to IN+, via R2        │ │
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
                                 │  IN+     IN− │  INA828       │
                                 │              │               │
                                 │  R_G 42.2k   │◄── G = 2.185  │
                                 │              │               │
                                 │  REF ◄───────┼── ½ OPA2197 ◄─[TRIM-BREATH-ZERO]
                                 │              │   buffered    from the LM317 5.21 V
                                 └──────┬───────┘   +0.437 V nulls the pedestal
                                        │  Vout = −2.185·(V_BREATH − V_AGND) + V_REF
                                        │       = 0 V at rest, −9.94 V at full
                                        │
                                  ┌─────▼──────────────────────┐
                                  │  INVERTING gain + offset   │
                                  │  POT-GAIN (buffered        │
                                  │  attenuator) then          │
                                  │  POT-OFFSET summing        │
                                  │  TWO × ½ OPA2197 — one     │
                                  │  half cannot do both       │
                                  │  independently             │
                                  └─────┬──────────────────────┘
                                        │
                                   [1k]─┼─[C 330nF]── AGND(module)
                                        │
                                   [BAV99]── ±12 V
                                        │
                                   BREATH jack
```

## `REF` carries a trimmer, and the polarity question dissolved twice

*(The showstopper this heading names, the input swap it forced, and the two
separate premises that were then withdrawn from under the swap — [`notes.md`](notes.md).)*

**`REF` is driven from a buffered trimmer** set once at commissioning. +0.579 V
nulls a *typical* +0.265 V pedestal — but the pedestal is a **spec band, not a
number**: 0.152–0.378 V, which needs `REF` anywhere from **0.332 V to
0.826 V**. The band is the datasheet's own `V_off` min/typ/max
`[datasheet MPXV4006DP p.4: "Voff 0.152 0.265 0.378 V"]`, and **its typical is
0.265 V** — see `sensor-full-scale`. **Range the trimmer 0 → +1.0 V.** An earlier revision specified
0 → +0.6 V, which covers pedestals only to 0.275 V; a sensor at the top of its
own datasheet band would have been un-nullable, leaving 1.4–5.6 % of span
standing at the jack — the same band as the polarity showstopper this trimmer
was added to fix. The in-amp then
rests at 0 V and reaches −9.94 V at full sensor range — about −4.7 V in real
playing.

**The downstream stage is inverting**, which is the topology that wants a
negative-going input. Now that it is drawn (`breath-output-stage.md`) that is
a buffered attenuator ahead of a fixed ×4 summer, with the offset injected at
the summing node — *not* two pots sharing a virtual ground, which is what an
earlier version of this sentence described and which would have made the knobs
fight.

### Why `REF` is trimmed rather than grounded

**Grounding it makes the panel knobs interact, and an earlier revision of this
page claimed the opposite.** With `REF` at 0 V the sensor's pedestal stays in
the signal, *upstream of the gain pot*, and gets multiplied by it: trim the jack
to zero at unity gain, turn GAIN to 2.4×, and the jack idles around **+0.6 V —
into a VCA**. The Yamaha WX5's manual documents this exact interaction on a
shipping instrument ("Wind Zero may change slightly when Wind Gain is adjusted,
so you may have to repeat").

Nulling the pedestal *ahead* of the gain stage is what makes "gain first, then
offset" (ADR 0006) true in hardware rather than only in intent.

**This does not reopen the split-authority rule.** There is still exactly one
zero authority per representation — what changes is that the analog path's
authority is now split by *job*, the same way pitch's is:

| | Calibration | Performance |
|---|---|---|
| Pitch | `TRIM-OFFSET`, set once | firmware's per-load affine |
| **Breath** | **`TRIM-BREATH-ZERO`, set once** | **the panel OFFSET knob** |
| Digital copy | — | firmware, from its own ADC |

What is *not* reintroduced is the DAC channel: firmware still corrects only the
representation it can measure, which is the finding that closed W12.

**The buffer is not optional.** Source impedance on an in-amp's `REF` pin adds
directly to its internal network and degrades CMRR one-for-one, so a bare
trimmer there would spend the entire 60 dB budget. It costs the last spare
OPA2197 half, and `U-OPA-PITCH` goes to six packages so there is still one.

**`REF` must tie *hard*, or to a buffer — never through a divider.** Source
impedance at an in-amp's `REF` pin adds directly to its internal resistor
network and degrades CMRR one-for-one. It is the same class of mistake as a
single-ended capacitor on one input leg, and it is easy to make because `REF`
looks like an input.

## Component values

| Ref | Value | Job |
|---|---|---|
| **R1** | 1 kΩ 1 %, **1206 ≥250 mW** | Instrument-side series protection, on the driver's output. **Not 0805** — see below |
| **R1b** | 1 kΩ 1 %, 1206 | **Its twin in the `AGND` leg.** Free, and it is what keeps CMRR from collapsing — see below |
| **R2, R3** | 10 kΩ 0.1 % | Module-side series protection. **Matched** — but see below |
| **R4, R5** | 1 MΩ | **Common-mode bias return.** Without these the in-amp's inputs float when the cable is unplugged and it saturates to a rail |
| **C_diff** | 15 nF C0G | **482 Hz** differential pole (not 531 — `R1b` makes both legs 11 kΩ), **ahead of the in-amp** |
| **C_cm** | 1.5 nF C0G ×2 | Common-mode poles, deliberately 1/10 of C_diff |
| **R_G** | 42.2 kΩ 0.1 % | INA828, `G = 1 + 50k/R_G` = **2.185** |
| **REF** | buffered trimmer, **0 → +1.0 V** | Nulls the pedestal *ahead* of the gain pot, which is what makes the panel knobs independent. Range covers the sensor's whole 0.152–0.378 V spec band, not just its typical. From the LM317 rail, never `VREFOUT`, and never a bare divider — see above |
| **Output RC** | 1 kΩ + 330 nF film | ~480 Hz reconstruction at the jack |

### The gain, derived

| | |
|---|---|
| Sensor span, 0.265 → 4.86 V | 4.6 V |
| Jack span wanted | 10 V |
| Raw gain needed | 2.174 |
| Loss in the 2 × 1 MΩ bias pair against 2 × 11 kΩ series | ×0.9891 |
| Gain needed at the in-amp | 2.198 |
| **R_G = 42.2 kΩ → G = 2.1848, effective 2.1611** | **jack span 9.94 V** |

The 0.6 % shortfall is absorbed by the panel gain knob, which exists to fit the
span to the patch. Do not chase it with a non-standard resistor.

### `R1` is a 1206, and it has a twin

**Power.** ADR 0003 names a sustained +12 V fault on the `BREATH` conductor as a
*designed-safe* case — the buffer runs from +12 V precisely so that fault sits
at the rail rather than above it. Work out what `R1` then dissipates:

```
I = (12 − 0.2) / 1 kΩ = 11.8 mA      P = 139 mW
```

against an 0805's ~125 mW. **The part fails in the fault the design calls
survivable**, and it is inside the bonded body. `bom.csv` makes exactly this
argument, in full, for the module-side `R-OUT-PROT` — and it was never carried
across to the instrument-side twin.

**And the consequence of an open `R1` is that nothing happens.** Breath dies;
pitch, the mods and the SPI link are untouched, and **no part of the system
reports it**. That is a change of kind, not of degree: this paragraph used to
say an open `R1` de-asserted the presence detect and took the whole SPI link
with it, which was true while the LM311 existed. The comparator is deleted and
`OE` is tied enabled (ADR 0004), so nothing at the module end watches the far
end of the cable any more. An open `R1` is now **silent** rather than
catastrophic — which ADR 0004 identifies as exactly the loss it accepted, and
which is worse for diagnosis even though it is better for blast radius.

The `R1`/`R1b` argument does not depend on that. It stands on the two grounds
above: 139 mW in an 0805 in the fault the design calls survivable, and the
common-mode term below.

**Symmetry.** `R1` sits in the `BREATH` leg with nothing opposite it in the
`AGND` leg, and against the 1 MΩ bias pair that asymmetry is a common-mode
error term on its own:

```
|1M/1.011M − 1M/1.010M| = 9.79e-4  →  60.2 dB
```

That is the **entire** 60 dB budget, spent by one unmatched resistor, with
every other term still to come. The 0.1 % module-side parts buy 94 dB and this
throws away fifty times that.

**`R1b` fixes it for nothing.** The `AGND` leg carries no signal current — the
in-amp's input is gigaohms — so a matching 1 kΩ in it changes the differential
gain not at all and restores the balance the 1 MΩ pair is measured against.
One resistor, instrument-side, and therefore **unretrofittable**.

**And `C_cm` needs a tolerance, which nothing specifies.** At ±5 % the
common-mode capacitor mismatch alone gives ~46 dB; ±1 % is needed to clear 60.
Specify **±1 % C0G** on the two 1.5 nF parts.

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

*(The cold review's findings and the table recording how the drawing closed
them — [`notes.md`](notes.md).)*

## Commissioning

With the body at room temperature and no breath at the mouthpiece:

1. **`TRIM-BREATH-ZERO`**, internal, until the in-amp output reads 0 V. Once,
   at build.
2. **Panel GAIN** for the span the patch wants. The knob does more work than
   this page used to say: real playing tops out around 2.8 kPa against the
   sensor's 6 kPa range, so a hard blow reaches about **−4.7 V** at the in-amp,
   not −10. The downstream stage is **0.5× to 4×**
   (`breath-output-stage.md`), which puts the working point near 2.1× — in the
   middle of the knob rather than at an end stop.
3. **Panel OFFSET** for where you want the jack to rest — **±5 V, zero at
   centre**. Because step 1 nulled the pedestal ahead of the gain pot, step 2
   no longer disturbs this.

Thermal drift afterwards is on the order of 20 mV in 10 V over a full warm-up —
a quarter turn if it ever bothers you. **That figure is unverified**: it rests
on an offset tempco of ~0.5 mV/K that the sensor family's datasheet apparently
does not break out, and nxp.com was unreachable when this was written.

**E10 scopes the jack**, not the display. The two representations are calibrated
separately on purpose, so a flat bar on the screen is no longer evidence about
the output.

## What the jack does on a `CLR` — settled

**Nothing, and that is correct.** `CLR` reaches the DAC channels; breath touches
none of them. `REF` is driven by `TRIM-BREATH-ZERO` through a buffer off the
LM317 rail — not by a DAC channel — so there is no path by which a `CLR` can
yank the zero out from under the stage. An analog path cannot latch at a level
the player is not producing: it follows the sensor, and the sensor follows the
room.

*(Two statements in this section that were stale until 2026-09-21, and why the
conclusion is unchanged under either correction — [`notes.md`](notes.md).)*

**E10 verifies it** by pulling the umbilical mid-note with the mouthpiece at
rest — and note that the same pull leaves pitch and the four mod jacks holding
their last value indefinitely, which is the accepted cost of deleting the
watchdog (`ROADMAP.md`, E10).

## Still open

- **The downstream gain/offset stage** is drawn as a block, and three things
  about it are open:
  - **Its offset reference must come from the LM317 rail, not `VREFOUT`.** An
    earlier version nominated "the buffered `VREFOUT` created for pitch", which
    would have made the jack's resting position depend on a DAC register that
    is disabled until firmware enables it — so the jack would rest at ~0 V at
    every boot and then *step* to where the player parked it, by up to 2 V.
    Moving the `REF` trimmer off `VREFOUT` fixed the small term and left this,
    the larger one. It would also have cross-linked the breath zero to the
    *pitch* offset trimmer, through the same follower.
  - **It needs two op-amp halves, not one.** Independent gain and offset
    require the gain realised as a buffered attenuator *ahead* of the summing
    node; a single inverting summer multiplies any offset at the virtual ground
    by `Rf`, which reintroduces the very interaction the `REF` trimmer was
    added to remove, displaced onto the OFFSET knob.
  - **Drawn**, at last: `hardware/module/breath-output-stage/breath-output-stage.md`. GAIN 0.5–4×
    as a buffered attenuator ahead of a fixed ×4; OFFSET ±5 V with zero at
    centre, from two resistors and no extra op-amp half. Two halves, which
    settles a count that was wrong twice.

*(The instrument-side reference buffer, which is not this page's circuit but
sets the number this page multiplies, settled 2026-09-21 — [`notes.md`](notes.md).)*
