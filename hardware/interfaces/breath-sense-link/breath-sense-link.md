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
inside a body that opens only by cutting its silicone and lifting the key
plate off the cassette's columns (ADR 0025).

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
| `BREATH_SENSE` | instrument → module | out | `carrier/carrier.md` §2 → `module/breath-receive-stage` | `umbilical-pinmap`, `sensor-full-scale` | The sensor's buffered output, on `J-UMB`. Leaves through the instrument-side `R1` and drives `IN−` through `R3`. **Not `BREATH_OUT`**, the module's jack, which is the far end of the output stage |
| `AGND_SENSE` | instrument → module | out | `carrier/carrier.md` §2 → `module/breath-receive-stage` | `umbilical-pinmap`, `dig-gnd-topology` | The instrument's analog star exported on `J-UMB`. Leaves through the instrument-side `R1b` and drives `IN+` through `R2`. **A signal leg, not a local ground**, and the twisted pair's other conductor. It is neither `AGND_MOD` nor `AGND_INST` — `R1b` is between it and the star |
| `R1`, `R1b` (`R-SER-BREATH-INST`) | instrument | — | — | — | This circuit's own parts, drawn in `carrier.md` §2, one in each leg. Both legs' series resistance sets the differential pole against `C_diff`, and their match is what the bias pair's balance is measured against. Unretrofittable |
| `U-BREATH` (MPXV4006DP) | instrument | — | — | `sensor-full-scale`, `breath-working-point` | This circuit's own part, drawn in `carrier.md` §2, **soldered to the main board at its mouth end** (*Mounting*, below). Sets the span the module end multiplies and the pedestal `TRIM-BREATH-ZERO` nulls |
| `VS` excitation | instrument | in | `carrier/breath-excitation-reference` | `riso-ref-topology`, `cref-out-node`, `opa2197-output-impedance` | The sensor's excitation, and its own circuit |
| buffered sensor output | instrument | out | `carrier/breath-adc` | — | The same node that feeds `R1`. The instrument's own copy of breath leaves here and does not cross |
| `D-TVS-BREATH` ×2 | instrument | — | — | — | This circuit's own parts, at the connector, on both legs, **to `PWR_GND`** (the plane at `J-UMB`, `power-entry-instrument.md` §2), never to the analog island |
| `R2`, `R3`, `C_diff`, `C_cm` ×2, `R4`, `R5` | module | — | `module/breath-receive-stage` | — | The receive filter and the common-mode bias return, all module-side |
| in-amp output | module | out | `module/breath-receive-stage` → `module/breath-output-stage` | `inamp-full-scale` | Into the panel GAIN/OFFSET stage, which inverts. **The figure is owned at the module end and derived here** |
| `REF` | module | in | `module/breath-receive-stage` | `breath-zero-ref`, `dac-rail` | The buffered trimmer that nulls the instrument's pedestal, fed from the `DAC AVDD` rail. Its own section stayed on the module page |
| `AGND_MOD` | module | ref | `module/breath-receive-stage` | `dig-gnd-topology` | The module's own analog star, sourced by `module/power-entry`. Where `R4`, `R5`, both `C_cm` and the output RC return. **Not `AGND_SENSE`**, the conductor on the pair |
| `±12 V` | module | in | `module/breath-receive-stage` | — | The module analog rails, sourced by `module/power-entry`: the INA828, both OPA2197 halves, and the BAV99 legs |
| presence detect on the pair | module | — | `module/link-supervision` | — | **Not fitted.** The deleted LM311 watched `BREATH_SENSE`/`AGND_SENSE` to gate `OE_MOD`; its threshold sat inside the breath signal's own range |
| `CLR` | module | — | — | — | **Reaches no part of this circuit.** It is `module/dac8568`'s, and nothing drives it |

---

## The sheet, and which board places what

**The source is [`breath-sense-link.kicad_sch`](breath-sense-link.kicad_sch)**
(ADR 0019; render [`breath-sense-link.sch.png`](breath-sense-link.sch.png)).
[`netlist.yaml`](netlist.yaml) is exported from it
(`python3 tools/kicad.py export hardware/interfaces/breath-sense-link`) and must
not be edited. It was first written from the hand-written netlist and compared
with it part by part and net by net: no change. The sensor's N/C pins (1, 5–8)
are on the symbol and on no net, as before. The drawing on
[`carrier.md`](../../carrier/carrier.md) §2 stays a representation.

**Every part on this sheet is on the main board, and the main board places
this sheet once** (`hardware/boards/main-board`, since 2026-09-30). The
umbilical conductors leave it on `interfaces/spi-link` (`J-UMB` pins 1 and 2),
and the module end (`R-SER-BREATH`, the in-amp) is
`module/breath-receive-stage`'s. So the board follows this sheet rather than
restating it, and `tools/kicad.py export hardware/boards/main-board` carries
every change here into `board-netlist.yaml`:

| Part on this sheet | BOM row | Main-board reference |
|---|---|---|
| `U-BREATH` | `U-BREATH` | `U10` |
| `R1`, `R1b` | `R-SER-BREATH-INST` | `R38`, `R39` |
| `D-TVS-BREATH-SIG`, `D-TVS-BREATH-RET` | `D-TVS-BREATH` | `D5`, `D6` |
| `C-SENSOR-VS-BULK`, `C-SENSOR-VS-HF`, `C-SENSOR-OUT` | their own rows | `C201`, `C202`, `C203` (added 2026-10-01; the board's layout has to place them) |

The placement replaced five parts drawn on the board's root sheet; the board's
flattened netlist was compared before and after, net by net and pin by pin,
and is unchanged `[repo, board-netlist.yaml]`.

## Mounting — `U-BREATH` is soldered to the main board

*Written 2026-09-26, not moved. The verbatim sections below are unaffected.*

**The MPXV4006DP is a surface-mount part, and it solders straight to the main
board. There is no socket.** Every datasheet figure here is read off
`datasheets/analog/MPXV4006DP.pdf` (Freescale MPXV4006, 22 pages); page numbers
are the sheet's own.

| Fact | Where |
|---|---|
| MPXV4006DP, case 1351, is ticked **Surface Mount** in the ordering table; the through-hole cases are 1560, 482B and 482C | `[ds p.1]`; p.2 files case 1351-01 under "Small Outline Package Surface Mount" |
| Case 1351-01 is an 8-lead gull-wing small outline package: body 11.81–12.32 mm square, lead pitch `e` 2.54 mm BSC, lead width `b` 0.96–1.07 mm, tip-to-tip `E` 17.27–17.78 mm, foot `L` 1.02–1.52 mm, height `A` 9.39–9.91 mm, both ports on one face, `F` 6.10–6.60 mm long | `[ds p.7]` outline (drawn, not in the text layer), `[ds p.20]` the same with its dimension table |
| Pinout **Style 2**: pin 2 `VS`, pin 3 `GND`, pin 4 `VOUT`, pins 1 and 5–8 N/C | `[ds p.4]` Figure 1, the MPXV4006's own schematic: `VS` pin 2, `GND` pin 3, `Vout` pin 4, *"Pins 1, 5, 6, 7, and 8 are NO CONNECTS for small outline package device"* — which is Style 2 of the case outline `[ds p.8, p.20]`. Buzz it out on arrival as a check, not as the source |
| P1 is the **side with the part marking** | `[ds p.6]` Table 3 |
| The ports are **staggered** on the port face: `M` 6.86–7.37 mm apart vertically and `N` 4.06–4.57 mm apart laterally | `[ds p.7]` — `M` is dimensioned in the **side** view, `N` in the **end** view; both in the p.20 table. With the marking on top as mounted, **P1 is the upper port and P2 the one nearest the board** — an inference, the same one `config/body.yaml` `boards.sensor_port_z` models (and `boards.sensor_port_offset` the stagger). Check the marking on the part in hand |
| The recommended footprint, Figure 6, is drawn for **case 482**, not 1351 | `[ds p.6]` |
| No reflow profile, no hand-soldering guidance and no soldering temperature anywhere in the sheet | `[ds pp.1–22]`, searched. p.6 says only that the packages self-align under reflow on the right footprint |
| Mounting stress and position shift the zero; the output must be auto-zeroed after installation | `[ds p.3]` Note 5 |
| Media other than dry air may affect performance and reliability | `[ds p.5]` |

### Land pattern — from the case 1351-01 outline, with Figure 6's pad

Figure 6 is 8 pads of 2.54 × 1.52 mm (along × across the lead) at 2.54 mm
pitch, the two rows 16.76 mm apart **centre to centre** `[ds p.6]` — read off
the figure's vector geometry, whose dimension lines land on the pad centres.
That spacing fits case 482's wider lead span (`S` 18.01–18.41 mm `[ds p.11]`).
For case 1351 the rows close up to the feet, and the pads are lengthened
inward so the heel gets at least the toe's margin `[calc]`:

```
foot centre to foot centre = E_nom − L_nom = 17.525 − 1.27 = 16.26 mm   [ds p.20]
feet can occupy  E_min − 2·L_max … E_max  =  14.23 … 17.78 mm

Figure 6's 2.54 mm pad centred on the feet (±8.13):
   copper 13.72 … 18.80   toe (18.80 − 17.78)/2 = 0.51   heel (14.23 − 13.72)/2 = 0.25

lengthened inward to 2.80 mm, outer edge kept at ±9.40:
   inner edge 9.40 − 2.80 = 6.60   →  copper 13.20 … 18.80
   pad centre (9.40 + 6.60)/2 = 8.00  →  rows 16.00 mm centre to centre
   toe  (18.80 − 17.78)/2 = 0.51 mm   heel (14.23 − 13.20)/2 = 0.515 mm
   clear of the body: 6.60 − E1_max/2 = 6.60 − 6.16 = 0.44 mm
pad gap across the pitch: 2.54 − 1.52 = 1.02 mm of solder mask
```

A 0.25 mm heel is thin against the ~0.35 mm IPC-7351 nominal heel for
gull-wing leads `[from memory]`, and the heel fillet is the one that holds a
gull-wing joint, so the pad grows inward — the toe and the outer edge do not
move, and the pad still stops short of the body. Figure 6 as printed would
still put every 1351 foot on copper, but centred 0.25 mm outboard of the feet
on each side. **Use 2.80 × 1.52 mm pads, rows 16.00 mm centre to centre.**
Solder mask between pads, as p.6 asks.

### Where it sits

**At the mouth end of the main board, on the far side from the tube, ports
towards the tail, beside the breath trap** (ADR 0017), parts face up. It is not
under a key board: the room it has is `mechanical/drc.echo` "breath sensor fits
at the mouth end". **The buffered breath signal runs the board's length to
`J-UMB`** (ADR 0017), so `U-BUF` sits beside the sensor and what makes the run
is the buffer's output, never `SENSOR_RAW`. Route it over its own ground, clear
of the LED row's data and 12 V and the chain's clock; **E11 is the test**.

**`AGND_SENSE` is taken at the sensor's own `GND` pin** (U-BREATH pin 3),
not at the star, and runs beside the buffered output as the pair's partner
the length of the board to `J-UMB` `[calc]`: the in-amp at the module reads
`BREATH_SENSE − AGND_SENSE`, and the buffer (a follower) reproduces `VOUT` as
it stands against the sensor's own pin 3. Taken there, whatever the ~13 mA
of analog supply return (below) drops across `AGND_INST` between the sensor
and the star is common to both legs and cancels in the in-amp; taken at the
star, it would be in the difference. Same net, `AGND_INST`, so the netlist
does not change: it is a layout rule — `R1b`'s star end is a trace of its own
from pin 3's pad, not a via into the pour. E11 is still the test of the whole run.

### NXP's Figure 3, at the sensor

**Fitted 2026-10-01 (owner): 1.0 µF and 0.01 µF on `VS`, 470 pF on `VOUT`,
exactly as the datasheet draws them** `[ds datasheets/analog/MPXV4006DP.pdf p.5,
Figure 3]` — the circuit its min/typ/max output curves were taken with.
`C-SENSOR-VS-BULK` and `C-SENSOR-VS-HF` go at pin 2, returning to pin 3;
`C-SENSOR-OUT` at pin 4, ahead of `U-BUF` B's follower, so neither the link
nor the ADC divider sees it. AN1646's 750 Ω + 0.33 µF is **not** fitted: it
would change the conditions the datasheet's accuracy was measured under. The
`VS` pair is also the reference buffer's load; its loop and step with them are
`breath-excitation-reference/sim` (`*-as-built`).

### Keeping the zero honest (Note 5)

- **Solder it flat, with no preload**, and keep standoffs and screws out from
  under it, so closing the lid does not bend the board beneath it.
- **The tube must not pull on P1.** Support it off the board. A load present
  at power-on is zeroed with everything else; one that changes after power-on
  is an offset the zero never saw.
- **Nothing liquid into either port**, flux or cleaner included `[ds p.5]` —
  solder the leads, not the port face, and do not wash the board with the
  sensor fitted.
- **Mask both ports before `MECH-COAT`** (ADR 0003 and ADR 0009). P2 is open to
  the cavity and must stay open.

### How it stays a replaceable wear part

ADR 0003 buys two. The spare goes in with an iron, and nothing else:

1. **Open the body** — cut the oak top free and unscrew the key plate from the
   cassette's columns (ADR 0025). The key boards come away with it on their
   ribbons (ADR 0017), and the main board's parts face up, so the sensor is in
   reach in place.
2. **Pull the tube off P1.**
3. **Cut the eight leads at the body** with flush cutters — the part is scrap
   anyway — and lift each stub with the iron. Clear the pads with braid.
4. **Fit the spare**: marked face up, ports towards the tail. Tack one corner
   lead, check it sits flat and square, then solder the other seven. Eight
   gull-wing leads at 2.54 mm pitch with a millimetre of mask between pads are
   ordinary iron work; no hot air.
5. **Re-mask both ports and touch up `MECH-COAT`** over the eight joints.
6. **Re-zero both paths.** Power-cycle for the firmware's power-on zero
   (`firmware/README.md`), and re-null `TRIM-BREATH-ZERO` at the module for
   the jack (Note 5 `[ds p.3]`).

**Soldering conditions are open:** the sheet gives none. **Decided by banking
NXP's soldering note for its pressure-sensor packages, AN3150**, which could
not be fetched on 2026-09-30 (`datasheets/.manifest-R32.csv`, `BLOCKED`, with
every URL tried); it must be banked before the sensor is first soldered, at
the main board's assembly. Until then: a modest iron temperature, one lead at
a time, short dwell, because the body is thermoplastic (PPS, `[ds p.1]`).

### Not taken: a breakout board on 2.54 mm headers

A small board carrying the sensor and plugged into the main board on 2.54 mm
headers would make the swap tool-free. Not taken, because:

- **Height.** It lifts the sensor, both ports and the tube by a board thickness
  plus a mated header pair — `[from memory]` 7–10 mm for 2.54 mm parts — which
  is most or all of the spare in `mechanical/drc.echo` "breath sensor fits at
  the mouth end", and moves the tube off the height "breath tube crosses the
  strip clear of it" was checked at.
- **Three contacts in the ratiometric path.** `VS`'s DC feedback is taken on
  the main board (`R-FB-REF`), so a header contact on `VS`, `VOUT` or `GND` is
  outside the loop — small, but not zero and not stable.
- **The swap it buys is already available.** The sensor is replaced perhaps
  once in the instrument's life, with the lid off either way, and the leads
  are iron-reworkable.

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
`R-SER-BREATH-INST` at **qty 2**, and the ~459 Hz
differential pole (*Component values*) is derived with 1 kΩ in *both* legs. Only one was drawn.

Its real job is **source-impedance balance on the twisted pair** — 1 kΩ
against ~0 Ω is what a difference amplifier's CMRR actually responds to —
and that justification appears nowhere in the repo. Without it the link
CMRR falls from **70.2 dB to 60.2 dB** `[calc, A2]` against an independently
derived requirement of 58.5 dB — and 60.2 dB is the nominal: at the worst
tolerance corner the unmatched link is **below** the requirement
(`breath-link-cmrr`, simulated). With `R1b` fitted the worst case clears it
at mains; it does not hold to the 500 Hz edge of the breath channel, because
the `C_cm` mismatch grows with frequency (same figure).

**The requirement's band is DC to 500 Hz** — the breath channel's band
(ADR 0004: `BREATH` is "band-limited ~500 Hz"), because a common-mode
disturbance anywhere inside it reaches `BREATH_OUT` as breath, and nothing
after the in-amp removes it. It was stated with no band until 2026-10-03
(#5 finding 5). Its derivation is not in the corpus; the 2026-09-21
pre-merge review reconstructs it to 0.1 dB as the `PWR_GND` drop at ADR
0003's 350 mA (58.9 mV) held to 1 LSB of 10 V at 16 bits at the in-amp output,
referred to its input `[calc, docs/review/2026-09-21-pre-merge-review/A1-breath-chain.md]`.
**Against that band the worst corner fails**, from about 480 Hz to the band's
edge, by under half a decibel (`module/breath-receive-stage/sim`,
`cmrr-as-netlisted`). Deciding it is the owner's: a tighter `C_cm` match, or
accepting the band's top 20 Hz. The band was not moved to make it pass. Both parts are inside a
body that is expensive to reopen (ADR 0009).

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
work `[repo] 0004`. The local analog pour joins `PWR_GND` at **one** tie —
under the ADC since the board went to four layers, `power-entry-instrument.md` §2.

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
| **C_diff** | 15 nF C0G | **~459 Hz** differential pole, **ahead of the in-amp**: 2 × 11 kΩ against 15 nF plus the two `C_cm` in series across the pair, 0.75 nF `[calc: 1/(2π × 22 kΩ × 15.75 nF)]`. Not 482 Hz, which left `C_cm` out; not 531, which had no `R1b` |
| **C_cm** | 1.5 nF C0G ×2 | Common-mode poles, deliberately 1/10 of C_diff |
| **R_G** | 42.2 kΩ 0.1 % | INA828, `G = 1 + 50k/R_G` = **2.185** |
| **REF** | buffered trimmer, **0 → +1.0 V** | Nulls the pedestal *ahead* of the gain pot, which is what makes the panel knobs independent. Range covers the sensor's whole 0.152–0.378 V spec band, not just its typical. From the DAC rail (`dac-rail`), never `VREFOUT`, and never a bare divider — see above |
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
survivable**, and it is instrument-side, behind a gasket and a lid.
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
every other term still to come. What `R1b` buys back is about **13.5 dB** at the
worst corner, not the 34 dB between this term and the 0.1 % parts' 94 dB: with
it fitted the floor is the 1 MΩ bias pair's ~73 dB `[sim, breath-link-cmrr]`.

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

## Where the two ends disagree — closed 2026-09-30

`carrier.md` §2 filed a correction against the receive page's case for `R1b` —
"fifty times" against about 13 dB. **The breath-link CMRR simulation settled
it**: `R1b` buys about 13.5 dB of worst case, so "about 13 dB" stands and "fifty
times" is withdrawn (`breath-link-cmrr`,
`hardware/module/breath-receive-stage/sim/README.md`). The quoted correction
earlier on this page is kept as the record of the argument.
