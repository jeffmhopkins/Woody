# Breath sense link — the sensor, the pair and the in-amp

**Status:** Consolidated 2026-09-21 from the two pages that described one
circuit from opposite ends of the umbilical — `hardware/carrier/carrier.md` §2
and `hardware/module/breath-receive-stage/breath-receive-stage.md`. Everything
below the `## Interfaces` table was **moved verbatim**: nothing was reworded,
no value was edited, no open question was closed, and where the two ends
disagree **both statements were moved and flagged** rather than reconciled.

This circuit has a directory of its own because it crosses a board boundary.
The differential pole, the effective gain and `inamp-full-scale` with it, the
sensor span and pedestal, the CMRR term and the `R1` power argument are all
derived at the module end from parts fitted at the instrument end, 2 m away,
inside a body that opens only by lifting the lid, disturbing the loom and
re-laying the gasket (ADR 0009).

**Neither schematic is redrawn here.** The instrument end is drawn in
[`carrier.md`](../../carrier/carrier.md) §2, in one connected picture that also
carries the excitation reference and the ADC divider. The whole chain, sensor
to jack, is drawn in
[`breath-receive-stage.md`](../../module/breath-receive-stage/breath-receive-stage.md),
in one that also carries the ADC divider and the output stage. Dividing either
would mean redrawing it, and a redrawn schematic is not a moved one.

## Interfaces

Every net and every part that crosses this circuit's boundary, and **which end
of the umbilical each one is on**. Quantities appear **only** as a citation
into `config/figures.yaml` — this table names nodes, it does not restate
values.

Two names collided across this boundary and the collision was inside this
block, which is why the `End` column exists: `BREATH` was both the conductor
arriving from the instrument and the name of the module's output jack, and
`AGND` was a signal leg on the pair, the instrument's analog star **and** the
module's own analog ground. A netlist taken off the drawings without this
column shorts the in-amp input to the output jack.

**The tables now qualify the names as well as the ends**, because a
transcription reads the Node cell and an `End` column only exists here:
`BREATH_SENSE` is the conductor, `BREATH_OUT` is the module's jack;
`AGND_SENSE` is the conductor, `AGND_INST` is the instrument's star and
`AGND_MOD` is the module's. `R1b` sits between `AGND_INST` and `AGND_SENSE`,
so they are not one net either. The drawings still spell all of these `AGND`,
`AGND-local`, `AGND(module)` and `BREATH`; each row says which.

The `Dir` and `Peer` columns are defined once in
[`hardware/README.md`](../../README.md#the-interfaces-table).

| Node / part | End | Dir | Peer | Figure | Note |
|---|---|---|---|---|---|
| `BREATH_SENSE` | instrument → module | out | drawn in `carrier.md` §2 → `module/breath-receive-stage` | `umbilical-pinmap`, `sensor-full-scale` | The sensor's buffered output, on `J-UMB`. Leaves through the instrument-side `R1` and drives `IN−` through `R3`. **Not `BREATH_OUT`**, the module's jack, which is the far end of the output stage |
| `AGND_SENSE` | instrument → module | out | drawn in `carrier.md` §2 → `module/breath-receive-stage` | `umbilical-pinmap`, `dig-gnd-topology` | The instrument's analog star exported on `J-UMB`. Leaves through the instrument-side `R1b` and drives `IN+` through `R2`. **A signal leg, not a local ground**, and the twisted pair's other conductor. It is neither `AGND_MOD` nor `AGND_INST` — `R1b` is between it and the star |
| `R1`, `R1b` (`R-SER-BREATH-INST`) | instrument | — | — | — | This circuit's own parts, drawn in `carrier.md` §2, one in each leg. Both legs' series resistance sets the differential pole against `C_diff`, and their match is what the bias pair's balance is measured against. Unretrofittable |
| `U-BREATH` (MPXV4006DP) | instrument | — | — | `sensor-full-scale`, `breath-working-point` | This circuit's own part, drawn in `carrier.md` §2. Sets the span the module end multiplies and the pedestal `TRIM-BREATH-ZERO` nulls |
| `VS` excitation | instrument | in | `carrier/breath-excitation-reference` | `riso-ref-topology`, `cref-out-node`, `opa2197-output-impedance` | The sensor's excitation, and its own circuit |
| buffered sensor output | instrument | out | `carrier/breath-adc` | — | The same node that feeds `R1`. The instrument's own copy of breath leaves here and does not cross |
| `D-TVS-BREATH` ×2 | instrument | — | — | — | This circuit's own parts, at the connector, on both legs |
| `AGND_INST` | instrument | ref | `carrier/power-entry-instrument` | `dig-gnd-topology` | The instrument analog star. `R1b`, `U-BREATH`'s ground and both `D-TVS-BREATH` anodes return here, and `netlist.yaml` has said so since it was written. **This row did not exist until 2026-09-26**, so the page that originates the net and this page each named the other nowhere |
| `R2`, `R3`, `C_diff`, `C_cm` ×2, `R4`, `R5` | module | — | `module/breath-receive-stage` | — | The receive filter and the common-mode bias return, all module-side |
| in-amp output | module | out | `module/breath-receive-stage` → `module/breath-output-stage` | `inamp-full-scale` | Into the panel GAIN/OFFSET stage, which inverts. **The figure is owned at the module end and derived here** |
| `REF` | module | in | `module/breath-receive-stage` | `breath-zero-ref`, `dac-rail` | The buffered trimmer that nulls the instrument's pedestal, fed from the `DAC AVDD` rail. Its own section stayed on the module page |
| `AGND_MOD` | module | — | `module/breath-receive-stage` | `dig-gnd-topology` | **Reaches no part of this circuit** — every part it names is `module/breath-receive-stage`'s, which is why the Dir is `—`. The module's own analog star, sourced by `module/power-entry`. Where `R4`, `R5`, both `C_cm` and the output RC return. **Not `AGND_SENSE`**, the conductor on the pair |
| `±12 V` | module | in | `module/breath-receive-stage` | — | The module analog rails, sourced by `module/power-entry`: the INA828, both OPA2197 halves, and the BAV99 legs |
| presence detect on the pair | module | — | `module/link-supervision` | — | **Not fitted.** The deleted LM311 watched `BREATH_SENSE`/`AGND_SENSE` to gate `OE_MOD`; its threshold sat inside the breath signal's own range |
| `CLR` | module | — | — | — | **Reaches no part of this circuit.** It is `module/dac8568`'s, and nothing drives it |

---

## From the instrument end — `carrier.md` §2

*Moved verbatim from `hardware/carrier/carrier.md` §2, 2026-09-21. "This page"
and "this drawing" throughout mean `carrier.md` as it stood before the move,
and the drawing they name is still in [`carrier.md`](../../carrier/carrier.md)
§2.*

### Two parts this drawing was missing, both unretrofittable

Both are in `bom.csv`, both are marked instrument-side and unretrofittable
there, and **neither appeared on this page** — the page that says of itself
"layout is now". Two reviewers found them independently, from opposite
directions.

**`R1b` — the twin 1 kΩ in the `AGND` leg.** `bom.csv` carries
`R-SER-BREATH-INST` at **qty 2**, and `breath-receive-stage.md`'s 482 Hz
differential pole is derived with 1 kΩ in *both* legs. Only one was drawn.

Its real job is **source-impedance balance on the twisted pair** — 1 kΩ
against ~0 Ω is what a difference amplifier's CMRR actually responds to —
and that justification appears nowhere in the repo. Without it the link
CMRR falls from **70.2 dB to 60.2 dB** `[calc, A2]` against an independently
derived requirement of 58.5 dB: **1.7 dB of margin**, resting on two parts'
tolerance, inside a body that is expensive to reopen (ADR 0009).

> One correction to the receive page's own case for `R1b`: it claims the
> part buys "fifty times" the rejection. With `R1b` fitted the real floor
> is **73 dB**, set by the 1 MΩ bias pair, so `R1b` buys about **13 dB**.
> Still worth fitting. The stated reason overstates it.

### Two things this drawing settles that no ADR does

**1. The analog star point is on this board, and `AGND` is sense-only.**
ADR 0003 names the star point as "the analog ground pour on the bottom cluster
board" `[repo] 0003` — a board that does not exist; it means this one. What it
leaves open is whether the analog section's supply return goes home on `AGND` or
on `PWR_GND`.

**Proposed: `PWR_GND`.** `AGND` leaves the board carrying nothing but the in-amp
sense reference, which is what ADR 0004's rule says and what makes the 2 m run
work `[repo] 0004`. The local analog pour joins `PWR_GND` at **one** tie, at the
umbilical connector.

The cost of getting it the other way `[calc]`, using ADR 0003's own cable figure
(0.168 Ω for 2 m of 24 AWG, implied by its 8.4 µV / 50 µA row):

```
REF5050 ~1 mA + OPA2197 2 × ~1 mA + MPXV4006DP 10 mA = ~13 mA   [repo] 0003
13 mA × 0.168 Ω = 2.2 mV on the sense pair
× the in-amp's G = 2.185 → 4.8 mV at the breath jack = 0.048 % of 10 V
```

Survivable either way, because it is DC-constant and `TRIM-BREATH-ZERO` nulls it
at commissioning `[repo] breath-receive-stage.md`. **`PWR_GND` anyway**, because
it is free and it keeps the rule true instead of approximately true.

**2. There is no band-limit capacitor at the instrument end of `BREATH`.**
ADR 0003 says "band-limit at both ends, around 500 Hz" `[repo] 0003`;
`breath-receive-stage.md` puts the whole 500 Hz filter at the receive end, ahead
of the in-amp, "because that is the only place it can stop RF rectification", and
`R-SER-BREATH-INST`'s note says the ADR is superseded `[repo] bom.csv`. **Drawn
that way here. Do not add a cap at `R-SER-BREATH-INST`.**

---

## From the module end — `breath-receive-stage.md`

*Moved verbatim from
[`breath-receive-stage.md`](../../module/breath-receive-stage/breath-receive-stage.md),
2026-09-21. "This page" throughout means that page as it stood before the move;
"see below" and "see above" inside the passage still point inside the passage.
The drawing it names is still on that page, and so are the `REF` trimmer
section, commissioning and the `CLR` section.*

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
survivable**, and it is instrument-side, behind a gasket and a loom.
`bom.csv` makes exactly this
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

---

## Where the two ends disagree

*Both halves are above, verbatim, and neither was edited: `carrier.md` §2 files
a correction against the receive page's own case for `R1b` — "fifty times"
against about 13 dB — and the sentence it is answering is in "`R1` is a 1206,
and it has a twin". They are now adjacent instead of two files apart. **No
winner was picked here**, which is not the same as their agreeing.*
