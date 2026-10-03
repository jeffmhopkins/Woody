# Module main board — `module-main`

The Eurorack module's rear board (ADR 0023): the etherCON, every IC, the
trimmers and the power header. It sits where the NE8FAV's setback puts it,
behind the jack board ([`module-jack`](../module-jack/README.md)), and
`J-B2B-MOD` joins the two. Positions, outlines and keep-outs come from the
module CAD (ADR 0024, `mechanical/module/export/`), not from this project.

> **Status: placed for the iso board, routing NOT complete (2026-10-03). `pcb.py check` fails.**
> `U-ISO` and its filter are on [`module-iso`](../module-iso/README.md) since
> 2026-10-03 (ADR 0023 point 2, amended: the owner, *"3 boards for module is
> correct"*), joined here by `J-B2B-ISO` (`J5`, on this board's top face, its
> insulator on the rear) and held by two `MECH-STANDOFF-ISO`. The board is
> placed inside its outline and the placement is DRC-clean. Routed under the
> owner's routing policy (`docs/reference/tooling.md`, *The routing policy*):
> free, no direction per layer anywhere yet (`layout.yaml` `directions:
> regions: []`). **31 connections are still unrouted** - 11 of them the DAC's
> (`DAC_CH1`-`CH5`, `DIN`, `SYNC`, `DAC_AVDD`), the rest scattered through the
> pitch stage, the rails and `PWR_GND` at the etherCON - with three shorts and
> two crossings left by the router in the load switch, and five
> `connect_first:` Kelvin/branch runs it could not lay (*Open*). Four layers.
> The mask colour is **not decided** (green in `layout.yaml` until the owner
> says; *Open*). The sheets are the source and pass KiCad's ERC.

What each circuit does, and why, is on its page:
- [`power-entry`](../../module/power-entry/power-entry.md)
- [`umbilical-load-switch`](../../module/umbilical-load-switch/umbilical-load-switch.md)
- [`dac8568`](../../module/dac8568/dac8568.md)
- [`digital-and-supervision`](../../module/digital-and-supervision/digital-and-supervision.md)
- [`breath-receive-stage`](../../module/breath-receive-stage/breath-receive-stage.md)
- [`breath-output-stage`](../../module/breath-output-stage/breath-output-stage.md), page `main`
- [`breath-response-shaper`](../../module/breath-response-shaper/breath-response-shaper.md), page `main`
- [`pitch-stage`](../../module/pitch-stage/pitch-stage.md), page `main`
- [`mod-channels`](../../module/mod-channels/mod-channels.md), page `main`
- [`panel-led`](../../module/panel-led/panel-led.md) — since 2026-10-01
  (ADR 0024 points 15 and 16): `R-LED-PANEL` and **`J-LED-PANEL` (J4)**, a
  JST B2B-XH-A on this board's **front** face at `pcb-geometry.echo`'s
  `J-LED-PANEL`, below the LED. `LED-PANEL` itself (D16 on this sheet) is
  a panel-mount indicator with **no footprint**: its lead plugs into J4,
  **pin 1 the anode** (`LED_ANODE`), pin 2 the cathode (`AGND_MOD`) — put
  `1` and `A` on the silk. Nothing taller than `pcb-geometry.echo`'s
  *front: under LED-PANEL* keep-out goes under the LED

## The layout (2026-10-02)

`layout.yaml` beside this file records how the first layout was made; the
`.kicad_pcb` is the source now (`docs/reference/tooling.md` §4, *The module's
boards*). Every part the module CAD fixes is placed by its pads from
`mechanical/module/export/pcb-geometry.echo` and held there by `pcb.py
check`: `J-UMBILICAL`, `J-B2B-MOD`, `J-LED-PANEL`, `J-PWR-EURO` (rear, pin 1
at the bottom), `U-ISO` (rear, at `config/module.yaml` `iso.at` and
`iso.pins`) and the four standoff pads (board-only, on no net). Every
courtyard is inside the board.

**Layers** (*Grounding*, `power-entry.md`: "Layers 1 and 3 carry parts and
signals; the analog rails route on layer 3"): 1 parts and signals; 2 the one
plane, `AGND_MOD`, with a `DIG_GND` island; 3 signals and the analog ±12 V as
0.4 mm tracks; 4 the rear parts, signals, and `PWR_GND`'s own copper. The
first try kept +12 V as a layer-3 plane and routed on layers 1 and 4 only, as
the controller's main board does (94 connections left). On three routing
layers the directional router (`pcb_route.complete`: layer 1 vertical, 3
horizontal, 4 vertical) left 74; Freerouting, which takes no layer direction
in batch, routed most of the rest, so the committed board is not one-way on
every layer (*Status*).

**The floor plan**, seen from the panel:

| Where | What |
|---|---|
| Bottom, front | `J-UMBILICAL`; `J-LED-PANEL` and `SW-POWER`'s wire pads to its left; the fuses right of `J-PWR-EURO`'s tails; `NT-AGND-MOD` and `NT-DIG-MOD` at its ground pins (the star) |
| Bottom, rear | the load switch (left), the SPI receiver, `U-REG-LOGIC` and `NT-UMB-MOD` under the etherCON's contacts, `J-PWR-EURO` (right) |
| Middle | `U-ISO` on the rear with `L-CM-ISO` at the module CAD's envelope, turned 45°; the input filter (`L-ISO-IN`, the beads, `C-ISO-BULK`) on the front right, `D2`/`D-REVPOL` on the rear between; `U-LVL-MOD` and the DAC on the front left, the DAC on the island's edge |
| Upper, front | the mod channels either side of `J-B2B-MOD` (MOD1/2 left, MOD3/4 right, as its columns), breath output left, pitch right with the LT5400 |
| Top | breath receive (front left, by its trimmer), the DAC rail's LDO (front middle), the response shaper (rear right); the four trimmers on the rear where the module CAD holds their envelopes |

**DIG_GND island** (`layout.yaml` `islands:`): the lower left of layer 2,
under the etherCON's contacts, the receiver, `U-REG-LOGIC`, the load switch and
`U-LVL-MOD`; its edge crosses `U-DAC` between its digital pins (1, 2, 15, 16)
and its analog ones, `GND` (14) on `AGND_MOD` `[ds DAC8568CIPW.pdf p.49]`.
Its ties are `NT-DIG-MOD` at the star and `NT-UMB-MOD` at the etherCON;
`check` holds every `DIG_GND` pad on it and every other plane net's pad off
it, but `J-LED-PANEL` pin 2, the panel LED's return to `AGND_MOD` by design,
whose place is the module CAD's (`foreign_ok:`).

### Every layout note in the corpus, and how it is met

| Note | Where it says so | How |
|---|---|---|
| `R-SET-DAC` away from the standoffs, connectors and board edges | `power-entry.md`, *The DAC rail*; this README | front, top middle: ≥ 5 mm from every edge, standoff and connector (`pcb.py check`'s DRC does not test this: read off the placement, `layout.yaml` `parts:`) |
| `R-SET-DAC`'s long axis parallel to the board's long edge | same | turned 90/270 (along y), the placement's only allowed turns for it |
| Guard ring round `SET` at `OUT`'s potential, both sides | same | a `DAC_AVDD` pour on layers 1 and 4 round `R-SET-DAC`, `C-SET-DAC` and `SET` (`layout.yaml` `guards:`), joined to `OUT`/`OUTS` |
| `OUTS` Kelvin to `C-REG-OUT`; `R-SET-DAC`'s and `C-SET-DAC`'s grounds to `C-REG-OUT`'s | same | `connect_first:` - each its own track, routed and locked first; `check` holds each to its `max_mm` |
| LT3042 exposed pad to `AGND_MOD` | same | netlisted; its pad fans out into the layer-2 plane |
| `U-LVL-MOD`'s `DAC_AVDD` on its own branch from `C-REG-OUT`, not through the DAC's pin | `power-entry.md`, *The DAC rail's load* | `connect_first: [C6.1, U4.14]` and `[C6.1, U3.3]`, separate tracks |
| `C-VREF-DAC`, `C-DEC-LVL`, `C-DEC-RX` at their pins; every op-amp's decouplers at its supply pins | `dac8568.md`, `digital-and-supervision.md` | placed against the pin (2-4 mm) |
| `C-FILT-PITCH` and `C-FILT-MOD` at `J-B2B-MOD`'s pins, not at the op-amp | `pitch-stage.md`, this README | placed against `J-B2B-MOD` pins 14, 15, 16, 17, 20 |
| LT5400's exposed pad to `AGND_MOD` | `pitch-stage.md` | netlisted; fanned out to layer 2 |
| The LT1641's `SENSE` and `VCC` Kelvin to `R-ILIM`'s pads, the tab short to `R-ILIM` | `umbilical-load-switch.md` | `connect_first: [U2.7, R3.2]`, `[U2.8, R3.1]`; `Q-LOADSW` beside `R-ILIM` |
| `TRIM-RESP` and every trimmer on the rear, adjustable from behind | `breath-response-shaper.md`, `mechanical/module/drc.echo` | all four at the module CAD's envelopes on the rear |
| `L-CM-ISO` between `L-ISO-IN` and the converter's input pins | ADR 0027, `power-entry.md` | in the circuit, yes. On the board the module CAD fixes it on the rear above `J-PWR-EURO`, so `ISO_VIN_POS`/`NEG` run back to `U-ISO`'s pins |
| `C-ISO-Y` beside the converter | `power-entry.md` | at `U-ISO`'s pin 1, across the barrier |
| `U-ISO`'s isolation: input side apart from output side | ADR 0027 | `layout.yaml` `isolation:` - a 2.0 mm functional gap on every layer, held by `check` (`check_isolation`); the `PWR_GND` pour drawn to keep it |
| `PWR_GND` its own copper on layer 4, meeting `DIG_GND` only at the etherCON | `power-entry.md`, *Grounding* | a layer-4 pour under `U-ISO` and round the load switch; `NT-UMB-MOD` at pins 6/8 |
| `DIG_GND` under the etherCON, `U-LVL-MOD`, `U-REG-LOGIC` and the SPI traces; `AGND_MOD` under the analog block; the DAC at the boundary | `power-entry.md`, *Grounding* | the island above |
| The breath pair: `BREATH_SENSE` and `AGND_SENSE` symmetric | `breath-receive-stage.md` | `pairs:` - side by side on layer 4 from the etherCON's pins up the board's left edge |
| `J-B2B-MOD` unmirrored on both boards | this README, `module-jack/README.md` | `check_b2b` against the jack board's `.kicad_pcb`, pin by pin |
| Nothing taller than the CAD's rooms under the LED, the toggle's lugs, the jack board | `pcb-geometry.echo` keep-outs | `check_heights` (`layout.yaml` `heights:`, `rooms:`) |

## Files — what is source, what is generated

| File | What it is |
|---|---|
| `module-main.kicad_sch` (+ the circuit sheets it places) | **Source.** Every connection, and each part's identity (ADR 0019) |
| `board-netlist.yaml` | Exported (`python3 tools/kicad.py export hardware/boards/module-main`), with KiCad's ERC over the whole hierarchy. Each part's `of` is its BOM row and `sheet` the circuit it belongs to, which is how a reference (`R17`) is looked up |
| `*.sch.png` | Renders, recorded in `hardware/SHEETS.csv` |
| `module-main.kicad_pcb`, `module-main.kicad_pro` | **Source** since the first layout (`python3 tools/pcb.py layout`, then `route`): edit in KiCad 9; `python3 tools/pcb.py check hardware/boards/module-main` holds it |
| `layout.yaml` | How the first layout was made: the parts' places, the rules, planes and checks' inputs |
| `module-main.pcb-*.png`, `fab/` | Written by `python3 tools/pcb.py render`, recorded in `hardware/SHEETS.csv` |
| `fp-lib-table`, `sym-lib-table` | Register `hardware/lib/` (the NE8FAV footprint, the DAC8568 symbol) for this project |

## How the circuits are placed

The root sheet places each circuit sheet once. A circuit with parts on both
boards is drawn as a parent sheet with two pages, `main` and `jack`
(`pitch-stage`, `breath-output-stage`, `breath-response-shaper`,
`mod-channels`); this board places each one's `main` page, the jack board its
`jack` page, and `J-B2B-MOD` carries the nets between them. On the boards those nets
take the names in the allocation below (a page's `JACK_TIP` is `PITCH_JACK` or `BREATH_JACK` here, the shaper's
`WIPER` is `RESP_WIPER`, and so on).

The root sheet's own parts are the two connectors:
- **`J-UMB-MOD`** (row `J-UMBILICAL`, the NE8FAV), named by
  [`spi-link`](../../interfaces/spi-link/spi-link.md) as the module's end of
  the umbilical. Pin *k* is wired to the net that sheet puts `J-UMB-MOD.k` on,
  and `tools/kicad.py check` holds it there. The G tab is not a pin of the
  umbilical and goes nowhere, as that sheet says.
- **`J-B2B-MOD`**, below.

**The jack filters sit at `J-B2B-MOD`** (pre-layout review A2-20, handed from
F2): the jack board carries only the jacks, the pots and the header,
so "at the jack" in `pitch-stage.md` and `mod-channels.md` means this board's
side of the header. Place `C29` (`C-FILT-PITCH`) and `C36`–`C39`
(`C-FILT-MOD`) against `J-B2B-MOD`'s `PITCH_JACK` and `MODn_JACK` pins, with
the pitch stage's DC tap (`RV3`'s CCW end, `TRIM-GAIN`) taken there too, so the
low-impedance shunt those pages argue for is at the connector the jack's wire
leaves by.

## J-B2B-MOD — the allocation

A 2 × 10 header soldered through both boards: **pin *k* is one conductor on
both**, so each board's sheet nets it the same way, and `tools/kicad.py check`
fails if they differ (a pin moved on one sheet only would pass each board's
ERC alone). The jack board's instance is marked `Assembly = none`; one header
is bought.

Fourteen signals cross, and five `AGND_MOD` pins, and one pin is spare: six
jack tips and the three pots' eight nets. Every return current of the jack
board (the six sleeves, the offset pot's bottom end) comes back on the five
ground pins. **Pin 19 is spare**, unconnected on both sheets, since the LED
whose supply it carried moved to this board (ADR 0024 point 15); no other pin
moved. Pin 1 is at the top left
(`pcb-geometry.echo`, `J-B2B-MOD`); odd pins are the left column.

| Pins | Left (odd) | Right (even) |
|---|---|---|
| 1, 2 | `BREATH_SHAPED` | `AGND_MOD` |
| 3, 4 | `GAIN_WIPER` | `RESP_V_IN_HALF` |
| 5, 6 | `AGND_MOD` | `RESP_WIPER` |
| 7, 8 | `GAIN_FLOOR` | `RESP_V_SHAPED` |
| 9, 10 | `OFFSET_WIPER` | `AGND_MOD` |
| 11, 12 | `BREATH_JACK` | `DAC_AVDD` |
| 13, 14 | `AGND_MOD` | `PITCH_JACK` |
| 15, 16 | `MOD1_JACK` | `MOD3_JACK` |
| 17, 18 | `MOD2_JACK` | `AGND_MOD` |
| 19, 20 | spare (no net) | `MOD4_JACK` |

Why this order:
- **Grounds interleaved on a diagonal** (2, 5, 10, 13, 18): each ground pin
  is next to three pins (the one across and the ones above and below it), so
  five of them can border the fourteen signals, and every signal has a ground
  beside it.
- **The pots' nets on the top rows**, because the pots are above the header
  (ADR 0024: the pot row, then the jacks). The breath-gain chain
  (`BREATH_SHAPED`, `GAIN_WIPER`, `GAIN_FLOOR`) is the left column, on the
  gain pot's side; the response pot's three nets are the right column, on its
  side; the offset pot, in the middle, closes the group (`OFFSET_WIPER` on
  pin 9). The grounds on pins 10 and 13 stand between the pots' wipers and
  the jack outputs below them, except in the left column, where
  `OFFSET_WIPER` (9) is directly above `BREATH_JACK` (11) with no ground
  between.
- **Each jack on its own column's side**: `BREATH`, `MOD1`, `MOD2` are the
  left column of jacks and take odd pins; `PITCH`, `MOD3`, `MOD4` the right
  column and even pins. The order down the header is the jacks' order down
  the panel. When the owner moved four jacks (ADR 0024 point 13,
  2026-10-01), their pins moved with them, on both sheets: keeping the
  pins would have put four jack-board traces across the header, between
  its pads, to reach the far column.
- **Pin 19 stays spare rather than being reused**: renumbering would move
  every pin below it on both sheets for nothing. It is free for a future net
  that needs no ground beside it.

What decides whether this changes: the board layout. The panel layout is
settled (ADR 0024 points 11–13: the etherCON at the bottom, the toggle
throwing left–right, the jack swap). The allocation is correct wherever the parts
go; the *reasons* above are about positions, so re-read them when
`pcb-geometry.echo` moves the pots, the jack columns or the header.


## `R-SET-DAC` placement — a rule, not a preference

The owner accepted (2026-10-01) that an open `R-SET-DAC` drives `DAC_AVDD` to
about 11 V, over the DAC8568's 6 V absolute maximum, with no clamp. Layout is one
of the two mitigations (`module/power-entry/power-entry.md`, *The DAC rail*,
*Its failures*):

- Keep `R-SET-DAC` (Viking ARG05, 0805 thin film) **away from the
  standoffs, the connectors and the board edges** — where the board flexes as it
  is screwed down and the cables are plugged — because flex cracking is what
  opens a chip resistor that carries no stress.
- **Orient its long axis parallel to the board's long edge**, so bending runs
  along the chip, not across its terminations.
- Put it inside the `SET` guard ring at `OUT`'s potential, on both sides, with
  `C-SET-DAC` beside it and both grounds Kelvin to `C-REG-OUT`'s
  (`[ds ADI-LT3042.pdf p.14–15]`).
- First build: order the assembly without `U-DAC` and `U-LVL-MOD`, measure
  `DAC_AVDD` (ROADMAP E7), then hand-fit them.

## Circuits the boards do not place

- [`link-supervision`](../../module/link-supervision/link-supervision.md) —
  **no parts**: the watchdog and the presence comparator were deleted before
  layout and never had a BOM row, and the owner decided on 2026-09-30 not to
  restore them. It has nothing to draw. `CLR`, which it
  would drive, is a net inside `dac8568`: `R-CLR-PU` ties it inactive and
  `LK-CLR` asserts it by hand.
- [`panel`](../../module/panel/panel.md) — **no electrical parts**: its one
  BOM row is the aluminium panel. The controls on it belong to the circuits
  that net them (the jacks and pots to their stages, `LED-PANEL` to
  `panel-led`, `SW-POWER` to `umbilical-load-switch`).

## Decided 2026-09-30

- **Four layers, 1.6 mm** (owner). The ground scheme is `dig-gnd-topology`:
  one star at `J-PWR-EURO`'s ground pins, `NT-AGND-MOD` and `NT-DIG-MOD` the
  only ties ([`power-entry.md`](../../module/power-entry/power-entry.md),
  *Grounding*).
- **Standoff pads**: the metal standoffs (owner) land on pads on **no net**
  on this board — plated, clear of every plane. The jack board's are
  `AGND_MOD`. Since 2026-10-01 (ADR 0024 point 15) this board has **four**:
  the two `MECH-STANDOFF-MOD` above the pots, shared with the jack board, and
  its two low mounting points, `MECH-PANEL-STANDOFF-MOD`, spacers from the
  panel's rear face on self-clinching studs (`config/module.yaml`
  `panel_standoff.at`; `pcb-geometry.echo` lists all four and their
  keep-outs). The jack board no longer reaches down to them.
- **`J-B2B-MOD`** is Samtec `TSW-110-09-G-D` (row), insulator on this board's
  front face. On **both** boards its footprint goes on the top side, **not
  mirrored** — the jack board's too, though the header's body is on that
  board's rear ([`module-jack/README.md`](../module-jack/README.md)).
- **Both `SW-POWER` lugs** wire to this board, beside `U-LOADSW`.

## Open, and what decides each

| Item | Decided by |
|---|---|
| The metal standoffs' part (the CAD's `standoff.*` still cites the polyamide spacer), and the panel spacers' (`panel_standoff.stock_l`, tbd) | The module CAD owner; the pads' nets are settled above |
| The module CAD's envelopes against the layout: `U-ISO` and the trimmers are where the CAD holds them; the layout moved `L-CM-ISO` up 3.5 mm (to clear `J-B2B-MOD`'s pins and keep the isolation gap; still turned 45°), and put `C-ISO-BULK` and `L-ISO-IN` on the front by the input filter and the bulk caps on the rear upper right (`layout.yaml` `parts:`), so `config/module.yaml` `iso.filter` and `tall.at` no longer describe where they are and the CAD's clash and depth checks do not see them there | The module CAD owner: move the envelopes to the layout's places and re-run its checks |
| The boards' mask colour (green in `layout.yaml` `fab:` until decided) | The owner, before the first order |
| **The routing** (*Status*): 31 connections, three shorts and two crossings in the load switch, five `connect_first:` runs. The DAC corner is the hard part; a `directions: regions:` entry there is the tool for it if free routing cannot close it | Finishing the route - by the router where it can, by hand-drawn tracks where it cannot (as `module-iso`'s) |
| `U-ISO`'s supply: the RPA20 is end-of-life, 20 at DigiKey on 2026-09-30 (the row); the RP20-2412SAW drops into the same footprint with pads 4 and 6 swapped (ADR 0027) | The order — buy spares now |
| The bus's +5 V, CV and Gate pins (11–16) are unused, on no net | Nothing: the module makes its own 5 V and takes no bus CV (ADR 0023 point 3, amended) |
