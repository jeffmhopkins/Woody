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
                 │                          ↓ to IN−, via R3            │
   (VS = REF5050 5.000 V)                            (twisted pair)   │
                 │                                                    │
                 └── 0.6× divider ── C-AA-ADC ── MCP3202 CH0          │
                                                                      │
   analog star ──[R1b 1k]──────────────────────── AGND   (pin 2) ──┐ │
   (no power current)                       ↑ to IN+, via R2           │ │
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
                                 │  IN+     IN− │  INA828       │
                                 │              │               │
                                 │  R_G 42.2k   │◄── G = 2.185  │
                                 │              │               │
                                 │  REF ◄───────┼── ½ OPA2197 ◄─[TRIM-BREATH-ZERO]
                                 │              │   buffered      from VREFOUT
                                 └──────┬───────┘   +0.437 V nulls the pedestal
                                        │  Vout = −2.185·(V_BREATH − V_AGND) + V_REF
                                        │       = 0 V at rest, −9.6 V at full
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

**`REF` is driven from a buffered trimmer** set once at commissioning. +0.437 V
nulls a *typical* +0.200 V pedestal — but the pedestal is a **spec band, not a
number**: 0.152–0.378 V, which needs `REF` anywhere from **0.332 V to
0.826 V**. **Range the trimmer 0 → +1.0 V.** An earlier revision specified
0 → +0.6 V, which covers pedestals only to 0.275 V; a sensor at the top of its
own datasheet band would have been un-nullable, leaving 1.4–5.6 % of span
standing at the jack — the same band as the polarity showstopper this trimmer
was added to fix. The in-amp then
rests at 0 V and reaches −9.6 V at full sensor range. The downstream stage is
**inverting**, which is the topology that wants a negative-going input: an
inverting summer does gain and offset with two pots into one virtual ground,
where a non-inverting stage would have the offset injection interact with the
gain setting.

So the swap survives on the downstream stage's topology rather than on the DAC's
unipolarity. Recorded explicitly because a decision whose original justification
has been removed is exactly the kind of thing that survives by inertia.

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
| **C_diff** | 15 nF C0G | 531 Hz differential pole, **ahead of the in-amp** |
| **C_cm** | 1.5 nF C0G ×2 | Common-mode poles, deliberately 1/10 of C_diff |
| **R_G** | 42.2 kΩ 0.1 % | INA828, `G = 1 + 50k/R_G` = **2.185** |
| **REF** | buffered trimmer, **0 → +1.0 V** | Nulls the pedestal *ahead* of the gain pot, which is what makes the panel knobs independent. Range covers the sensor's whole 0.152–0.378 V spec band, not just its typical. From the LM317 rail, never `VREFOUT`, and never a bare divider — see above |
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

Two consequences nobody had written down: if `R1` opens, the presence detect
de-asserts and takes the **whole SPI link** with it, so pitch and the mods die
with breath; and during the fault the jack clips high and *holds* while the
detect still says "present".

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

## What this settles

| Finding | Resolution |
|---|---|
| Ambient zero has the wrong polarity | **Deleted** — there is no *firmware* injection. `REF` carries a commissioning trimmer, and polarity is a non-issue because a trimmer goes both ways |
| The zero correction is open-loop across two representations | **Deleted with it** — firmware now zeroes only the copy it measures |
| No common-mode bias return | **Fixed** — R4, R5 |
| No in-amp gain resistor | **Fixed** — R_G = 42.2 kΩ, derived above |
| The 100 kΩ differential pulldown | **Deleted.** R4/R5 do its job without its 1–17 % attenuation, and the review could not agree which figure applied |
| "Six different in-amp gains" | One gain, one derivation, shown |
| Which in-amp | **INA828** — the E96 value lands cleanly and its lower bandwidth suits a 500 Hz channel |
| Where the 500 Hz pole goes | Ahead of the in-amp, differential-dominant |

## Commissioning

With the body at room temperature and no breath at the mouthpiece:

1. **`TRIM-BREATH-ZERO`**, internal, until the in-amp output reads 0 V. Once,
   at build.
2. **Panel GAIN** for the span the patch wants. The knob is doing more work
   than this page used to say: real playing tops out around 2.5–2.8 kPa against
   the sensor's 6 kPa range, so a hard blow reaches roughly 4.5 V at the in-amp,
   not 10 V. **The downstream stage needs about 0.6× to 2.5×**, not unity and a
   trim.
3. **Panel OFFSET** for where you want the jack to rest. Because step 1 nulled
   the pedestal ahead of the gain pot, step 2 no longer disturbs this.

Thermal drift afterwards is on the order of 20 mV in 10 V over a full warm-up —
a quarter turn if it ever bothers you. **That figure is unverified**: it rests
on an offset tempco of ~0.5 mV/K that the sensor family's datasheet apparently
does not break out, and nxp.com was unreachable when this was written.

**E10 scopes the jack**, not the display. The two representations are calibrated
separately on purpose, so a flat bar on the screen is no longer evidence about
the output.

## What the jack does when the watchdog fires — settled

**Nothing, and that is correct.** `CLR` reaches the DAC channels; breath touches
none of them, and now that `REF` is grounded it touches the breath stage in no
way at all — where previously `CLR` would have yanked the zero out from under
it. An analog path cannot latch at a level the player is not producing: it
follows the sensor, and the sensor follows the room. Reasoning in full in
ADR 0004, "The watchdog's scope is the DAC channels".

E10 verifies it by pulling the umbilical mid-note with the mouthpiece at rest.

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
  - **Its gain range is 0.6× to 2.5×**, not unity and a trim — real playing
    tops out near 2.5–2.8 kPa against the sensor's 6 kPa span.
