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

**Soldering conditions are AN3150's**, the family's soldering note
(`datasheets/analog/MPXV-AN3150-SOLDERING-PRESSURE-SENSORS.pdf`); the sensor's
own sheet gives none.

- **245 °C maximum on the part**, for an MPXV with the DP suffix, "with
  minimized duration" — and rework is "not recommended, but should it be
  necessary" held to the same limit `[AN3150 p.3, Table 1]`. It is a limit on
  the body, which is thermoplastic (PPS, `[ds p.1]`), not on the iron's tip:
  one lead at a time, short dwell.
- **No-clean flux, and no washing.** No pressure spray, and no ultrasonic
  cleaning, which can break the wire bonds `[AN3150 p.1]`. If the board is
  ever washed, cap both ports first.
- **No vapour-phase and no IR reflow** `[AN3150 p.2]` — which is one more
  reason the sensor is fitted by hand after the board is assembled.

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

## Fallback: MPXV7007DP — ready to apply, not fitted

*Written 2026-10-03 for issue #30. **The design stays on the MPXV4006DP**
(owner, 2026-10-03, ADR 0003: "Buy now + study fallback"). This section is the
change to make if no MPXV4006DP can be bought. Nothing here is on a sheet, and
no figure in `config/figures.yaml` describes it. Every datasheet number below
is read off `datasheets/analog/MPXV7007DP.pdf` (Freescale MPXV7007 Rev 3,
10/2012, 11 pages); page numbers are the sheet's own.*

**Do not drop it in.** The MPXV7007DP fits the same pads and takes the tube
the same way, but its output is a different shape. Fitted with nothing else
changed, the module cannot null its zero and the breath range shrinks to about
a third. Make all three changes under *Apply it* together.

### The two transfer functions

| | MPXV4006DP (fitted) | MPXV7007DP (fallback) |
|---|---|---|
| Range | 0–6 kPa, `P1 > P2` | −7 to +7 kPa, either way `[ds p.2]` |
| Transfer function, ratiometric with `VS` | `sensor-full-scale`'s derivation | `VS × (0.057·P + 0.5)` `[ds p.5]` |
| Slope at `VS` = 5 V | `breath-sensor-slope` | 0.285 V/kPa `[calc: 5 × 0.057]`; the sheet's 286 mV/kPa `[p.2]` |
| Output at 0 kPa (the pedestal) | `sensor-full-scale`'s pedestal | **2.5 V**, mid-supply `[calc: 5 × 0.5]` |
| Output at 6 kPa | `sensor-full-scale` | 4.21 V `[calc: 5 × (0.342 + 0.5)]` |
| Offset spread | `breath-receive-stage.md`'s `V_off` band | `V_off` 0.33 / 0.5 / 0.67 V, ±0.17 V, taken at −7 kPa `[p.2]`. The p.5 error band is ±0.5 kPa = ±0.1425 V. **±0.17 V is used at 0 kPa** because it is the wider of the two |
| Accuracy | 2.46 %`V_FSS` | 5.0 %`V_FSS`, 0–85 °C `[p.2]` |
| Supply | 4.75–5.25 V, 10 mA | the same range, 7.0 typ / 10 max mA `[p.2]` |
| Response | 1.0 ms | 1.0 ms `[p.2]` |
| Maximum pressure | 24 kPa, `P1 > P2` | 75 kPa `[p.3]` |
| Operating temperature | +10 to +60 °C | −40 to +125 °C `[p.3]` |
| Decoupling the curves were taken with | Figure 3: 1.0 µF, 0.01 µF, 470 pF | **the same three** `[p.4, Figure 3]` |

Over the breath range, 0 to 6 kPa, the MPXV7007DP gives **1.71 V of swing on
a 2.5 V pedestal**. The MPXV4006DP gives 4.6 V on a pedestal near ground. The
slope ratio is 0.1533 / 0.057 = **2.689** `[calc]`. Both parts are
ratiometric with `VS` over the same 4.75–5.25 V, so the REF5050 excitation
(`breath-excitation-reference`) carries over unchanged.

**A drop-in fails twice** (sim `drop-in`, below):

- The in-amp's `REF` would have to reach 5.0–5.8 V to null the pedestal. The
  live `TRIM-BREATH-ZERO` reaches about 1 V.
- 6 kPa makes −3.70 V at the in-amp instead of `inamp-full-scale`. The ADC's
  counts per kPa fall by the same 2.689.

### What changes: `U-BUF` B becomes an offset-and-gain stage

**Make the fallback's output look like the MPXV4006DP's** — the same slope,
and a pedestal near ground — and almost nothing downstream moves. `U-BUF` B is
today a follower on `INST_POS12`/`AGND_INST`
(`breath-excitation-reference`). Open its feedback short and add three
resistors at its (−) input:

```
              R-BUFB-VS 8.25k 0.1%
   VS ──────────/\/\/──────┐
                           │         R-BUFB-FB 10.0k 0.1%
                           ├─────────/\/\/───────┐
   SENSOR_RAW ──── (+)     │                     │
                  U-BUF B ─┼─────────────────────┴── SENSOR_BUFFERED_OUT
                   (−) ────┘
                           │
                           └──/\/\/── AGND_INST
              R-BUFB-GND 21.0k 0.1%

   Vo = Vin · (1 + Rf/Ra + Rf/Rb) − VS · Rf/Ra        [calc, KCL at (−)]
      = Vin · 2.6883 − VS · 1.2121
   with Vin = VS · (0.057·P + 0.5):
   Vo = VS · (0.15323·P + 0.13204)
```

`Rf` is R-BUFB-FB, `Ra` is R-BUFB-VS and `Rb` is R-BUFB-GND.

- **Slope.** At `VS` = 5 V the slope is 0.76617 V/kPa. That is
  `breath-sensor-slope` less 0.04 % `[calc: 5 × 0.057 × 2.68831]`.
- **Pedestal.** It is **0.660 V** `[calc: 5 × 0.13204]`.
- **Full scale.** It is **5.257 V** at 6 kPa.
- **Ratiometric.** The offset is taken from `VS` itself, so the pedestal and
  the slope both stay ratiometric (sim `ratio_dev`, below). The REF5050 still
  sets the scale, and nothing else does.
- **The values are E96 at 0.1 %.** They were searched for the slope closest
  to `breath-sensor-slope` with the pedestal in 0.64–0.67 V. With 0.1 % parts
  the stage adds ±8 mV to the pedestal and ±0.13 % to the slope `[calc; sim]`.

**Why the pedestal is 0.66 V and not the MPXV4006DP's.** The stage multiplies
the sensor's offset spread too. ±0.17 V × 2.688 = ±0.457 V at the stage's
output, against ±0.113 V for the fitted part. The lowest unit's pedestal must
stay above the OPA2197's 125 mV maximum swing to its negative rail at 10 kΩ
(`[ds datasheets/analog/OPA2197.pdf p.8]`, ADR 0003). If it fell below, the
bottom of the breath range would be a dead band.

- **The band at the stage's output** is 0.197–1.123 V in the sim.
- **The low end** clears the 125 mV swing by 72 mV.
- **The high end at 6 kPa** is 5.72 V.

**Loads.** These are small against what the sim and the pages already cover
`[calc]`:

- `VS` gains a resistive load through R-BUFB-VS: 0.30 mA at rest, falling to
  0.10 mA at 6 kPa, against the sensor's 7–10 mA.
- `U-BUF` B sinks 0.18 mA through R-BUFB-FB at rest.

### What changes at the module: `TRIM-BREATH-ZERO`'s range

The in-amp's gain does not change. `R-GAIN-INAMP` stays, so a kPa still makes
the same in-amp volts. The null moves:

- **At a typical pedestal**, the null is 0.660 × 2.16106 = **1.427 V**
  `[calc; sim 1.427 V]`. This replaces `breath-zero-ref`.
- **Across the band**, it is **0.43–2.43 V** `[sim]`.

**`R-ZERO-TOP` 42.2k → 8.25k 1 %** (the same value as R-BUFB-VS, one fewer
line on the order). The trimmer then spans 0 V to `dac-rail` × 10/18.25. At
the worst corner — the rail at its lowest (`dac-rail`'s derivation), the track
10 % low and `R-ZERO-TOP` 1 % high — that is **2.65 V** `[calc]`. It clears
the band's 2.43 V. `DAC_AVDD` carries 0.19 mA more `[calc: 5.23/18.25k −
5.23/52.2k]`, inside the load range `dac-rail` is derived over. A 2.7×
coarser trimmer is still fine on a multiturn.

### What does not change, and what does

**Unchanged:**

- **The in-amp's full scale.** 6 kPa still reaches `inamp-full-scale`:
  −9.934 V nominal, and −9.922 to −9.947 V at every corner `[sim]`.
- **The commissioning voltage.** 2.8 kPa (`breath-working-point`'s candidate)
  gives −4.636 V at the in-amp, which is the voltage the response shaper is
  commissioned at.
- **Everything downstream of the in-amp:** the output stage, the shaper, the
  panel knobs and the jack span.
- **The ADC's counts per kPa**, because the slope is the same.

**These do move:**

- **The ADC's rest reading.** It rises from about 197 counts to about 492
  `[calc: 0.660 × 0.6 / 3.3 × 4096]`. The firmware zero is a power-on capture,
  so it does not care. The LED row's 12 V gate (`firmware/README.md`, "half
  the rest count") still works, with more margin.
- **The ADC's top for a high-offset part.** A part at the top of its offset
  band clips the ADC copy at **5.72 kPa** rather than above 6 kPa `[sim
  p_clip]`. A nominal part clips at 6.32 kPa. Leave the divider alone unless
  E2 (`breath-working-point`) finds hard blows near 6 kPa. If it does,
  `R-ADCDIV-U` 10k → 11.0k moves the clip past 6 kPa for every part, for 3.8 %
  fewer counts.
- **The power-up injection** (`breath-adc.md`) becomes (5.72 − 0.7) / 10 kΩ =
  0.50 mA at most, under the 1 mA that page judges against `[calc]`.
- **The jack with the instrument unplugged.** The in-amp rests at `REF`, which
  is now 1.43 V typical rather than `breath-zero-ref`. So ADR 0006's standing
  level grows by the same factor: up to about 5.7 V below the OFFSET knob at
  the top of the GAIN range for a typical part `[calc: 1.427 × 4.02]`. ADR 0006
  already accepts a jack with no defined level with the instrument absent. This
  makes the level larger, not new.
- **Noise.** No datasheet gives either part's noise; `breath-jack-noise`
  assumes one for the MPXV4006DP. If the MPXV7007DP's output noise in volts is
  the same, it is 2.69× more per kPa: about 0.79 mV rms at the jack
  (−82 dB of 10 V) and about 0.22 LSB rms at `ADC_IN` `[calc, on that figure's
  assumption]`. The stage's own noise (5.5 nV/√Hz at a noise gain of 2.69, and
  about 6 kΩ at its (−) input) is negligible beside it. E11 measures the real part.
- **Accuracy.** The datasheet's error is 5.0 %`V_FSS` against 2.46 %, so
  about ±0.5 kPa absolute against about ±0.15. Playing does not use absolute
  pressure: the zero is captured or trimmed, and the panel GAIN fits the span.
  ADR 0003's E2 comparison against a manometer is the one place it shows.

### Footprint and ports — the same

- **Same case.** The MPXV7007DP is case 1351-01 Issue O, surface mount, both
  ports on one face `[ds p.1, p.8]`. Its dimension table is the MPXV4006DP
  sheet's p.20 table **value for value**: `E` 17.27–17.78, `L` 1.02–1.52,
  `b` 0.96–1.07, `M` 6.86–7.37, `N` 4.06–4.57, `A` 9.39–9.91 mm. So
  `woody:NXP_Case1351-01_SOP-8_P2.54mm` and the land pattern under *Mounting*
  fit unchanged. Its Figure 5 is drawn for case 482 at 16.76 mm, like the
  MPXV4006DP's Figure 6 `[p.6]`; do not copy it.
- **Same pinout.** Style 2: pin 2 `VS`, pin 3 `GND`, pin 4 `VOUT`
  `[p.1 Table 1, p.3 Figure 1, p.8]`. The sheet's pins and nets carry over.
  Pins 1 and 5–8 are *"internal device connections. Do not connect to external
  circuitry or ground"* `[p.1]`. That is stricter wording than the
  MPXV4006DP's "no connects", and the footprint already obeys it: those pads
  are on no net. Keep them out of any pour.
- **Same ports.** P1 is the **side with the part marking** `[p.6, the P1/P2
  identification table]`, as on the MPXV4006DP. Mount it marked face up,
  ports towards the tail. The tube goes on P1 and P2 stays open to the cavity.
  The 1351 port stagger is the same, so `config/body.yaml`'s sensor port
  positions hold.
- **Same handling.** The MPXV7007DP is also an MPXV with the DP suffix, so
  AN3150's soldering limits and the iron-swap procedure above apply as
  written. The decoupling capacitors, `C-SENSOR-*`, are its own Figure 3.
  `datasheets/analog/MPXV7007-CASE-1351-01-HAXO-3D.step`, already banked for
  the render, is a model of this part.

### Simulated

`fallback-mpxv7007/sim/` (`python3 tools/sim.py run
hardware/interfaces/breath-sense-link/fallback-mpxv7007/sim`). It runs the
stage with TI's OPA2197 model, the ADC divider and `C-AA-ADC`, `R1`/`R1b`, the
receive stage and the INA828 with TI's model, as netlisted. The three stage
resistors and the new `R-ZERO-TOP` are params, because they are on no sheet.
It runs 17 corners: the sensor offset ±0.17 V and each stage resistor ±0.1 %.
It does not touch any live sim's results.

| Measure | Nominal | Range over corners |
|---|---|---|
| Pedestal at the stage's output | 0.660 V | 0.197–1.123 V |
| Output at 6 kPa | 5.257 V | 4.796–5.719 V |
| Slope | 0.7662 V/kPa | 0.7652–0.7671 (within 0.5 % of `breath-sensor-slope`) |
| `REF` to null | 1.427 V | 0.425–2.427 V (the trimmer reaches 2.65 V at worst) |
| In-amp after the null, rest / 2.8 kPa / 6 kPa | 0.00 / −4.636 / −9.934 V | 6 kPa within 1 % of `inamp-full-scale` at every corner |
| ADC clip pressure | 6.32 kPa | 5.72–6.92 kPa |
| Ratiometric error, `VS` 5.00 → 5.25 V | 4 ppm | under 13 ppm |
| 2.8 kPa step at the stage's output | 0.13 % overshoot | settles to 1 mV in 10 µs |
| **Drop-in** (follower, live trimmer): `REF` to null / span at 6 kPa | 5.40 V / −3.70 V | 5.04–5.77 V, against a trimmer that reaches about 1 V |

The sim is a screen, not a bench result. The sensor is its transfer function
and nothing else: no noise, no response time, no temperature. The datasheet's
offset spread stands in for a measured one.

### Apply it

1. **`U-BREATH`** → MPXV7007DP, same footprint, same ports. Buy from ST direct
   or an authorized distributor.
2. **`breath-excitation-reference` sheet:** take `U-BUF` B's (−) input off its
   output, and add **R-BUFB-FB 10.0k 0.1 %**, **R-BUFB-VS 8.25k 0.1 %** and
   **R-BUFB-GND 21.0k 0.1 %**, thin film, beside `U-BUF` on the main board.
   Re-export; re-place the main board.
3. **`breath-receive-stage` sheet:** **`R-ZERO-TOP` → 8.25k 1 %.**
4. **Figures**, by rule 2 (grep first):
   - `sensor-full-scale` becomes the conditioned output at 6 kPa, 5.257 V on
     a 0.660 V pedestal, owned here.
   - `breath-zero-ref` becomes 1.427 V.
   - `breath-sensor-slope` stays as the slope the stage reproduces.
   - `inamp-full-scale` does not move.
   - Then fix what the checker names: `breath-adc.md`'s divider block, ADR
     0003's sensor section, ADR 0006's standing level, and the sims that cite
     these figures.
5. **Re-run every sim:** `breath-excitation-reference` (the extra `VS` load),
   `breath-adc`, `breath-output-stage` (noise), and `interfaces/system`. Then
   move this directory's params onto the netlists.
6. **Commission as now:** power-cycle for the firmware zero, then null
   `TRIM-BREATH-ZERO`.

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
at mains, and with `C_cm` a matched pair (below) to the 500 Hz edge of the
breath channel as well (same figure).

**The requirement's band is DC to 500 Hz** — the breath channel's band
(ADR 0004: `BREATH` is "band-limited ~500 Hz"), because a common-mode
disturbance anywhere inside it reaches `BREATH_OUT` as breath, and nothing
after the in-amp removes it. It was stated with no band until 2026-10-03
(#5 finding 5). Its derivation is not in the corpus; the 2026-09-21
pre-merge review reconstructs it to 0.1 dB as the `PWR_GND` drop at ADR
0003's 350 mA (58.9 mV) held to 1 LSB of 10 V at 16 bits at the in-amp output,
referred to its input `[calc, docs/review/2026-09-21-pre-merge-review/A1-breath-chain.md]`.
**With two independent ±1 % `C_cm` the worst corner failed that band**, from
about 480 Hz to its edge, by under half a decibel. **The owner's choice,
2026-10-03 (#5-5): "Tighten cap matching"** — `C-CM-BREATH` is bought as a
matched pair, each within 0.5 % of the pair's mean (*And `C_cm` needs a
tolerance*, below), and the worst corner then holds 58.5 dB across the whole
band (`module/breath-receive-stage/sim`, `cmrr-as-netlisted`;
`breath-link-cmrr`). The band was not moved to make it pass. Both parts are inside a
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
| **R1** | 1 kΩ 1 %, **1206 ≥250 mW**, anti-surge (ERJ-P08, owner 2026-10-03) | Instrument-side series protection, on the driver's output. **Not 0805** — see below |
| **R1b** | 1 kΩ 1 %, 1206, anti-surge (ERJ-P08) | **Its twin in the `AGND` leg.** Free, and it is what keeps CMRR from collapsing — see below |
| **R2, R3** | 10 kΩ 0.1 % | Module-side series protection. **Matched** — but see below |
| **R4, R5** | 1 MΩ | **Common-mode bias return.** Without these the in-amp's inputs float when the cable is unplugged and it saturates to a rail |
| **C_diff** | 15 nF C0G | **~459 Hz** differential pole, **ahead of the in-amp**: 2 × 11 kΩ against 15 nF plus the two `C_cm` in series across the pair, 0.75 nF `[calc: 1/(2π × 22 kΩ × 15.75 nF)]`. Not 482 Hz, which left `C_cm` out; not 531, which had no `R1b` |
| **C_cm** | 1.5 nF C0G ×2, a matched pair (±0.5 % about its mean) | Common-mode poles, deliberately 1/10 of C_diff |
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
survivable**, and it is instrument-side, inside a body glued shut (ADR 0025)
and reached only by cutting it open.
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

**And `C_cm` needs a match, which a tolerance alone does not give.** At ±5 %
the common-mode capacitor mismatch alone gives ~46 dB; at ±1 % each the link
clears mains but not the band's 500 Hz top at the worst corner (above). No
1.5 nF C0G is catalogued tighter than ±1 % `[web jlcpcb.com parts search,
2026-10-03]`, so **the two are a matched pair**: the ±1 % C0G (Yageo
CC0805FRNPO9BN152) from one reel, measured on one LCR meter at 1 kHz, and
fitted by hand only as a pair whose readings are each within 0.5 % of their
mean — the `C-CM-BREATH` row and both parts' `Note` say how. Owner,
2026-10-03: "Tighten cap matching".

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
