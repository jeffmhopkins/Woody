# Module main board — `module-main`

The Eurorack module's rear board (ADR 0023): the etherCON, every IC, the
trimmers and the power header. It sits where the NE8FAV's setback puts it,
behind the jack board ([`module-jack`](../module-jack/README.md)), and
`J-B2B-MOD` joins the two. Positions, outlines and keep-outs come from the
module CAD (ADR 0024, `mechanical/module/export/`), not from this project.

> **Status: schematic done, layout not started.** The sheets are the source
> and pass KiCad's ERC. Every part has a footprint, and a bought part where one
> is selected (`Footprint`, `Manufacturer`, `MPN`, `LCSC`, `Assembly` on each
> symbol). The parts still missing one are listed under *Open*.

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

## Files — what is source, what is generated

| File | What it is |
|---|---|
| `module-main.kicad_sch` (+ the circuit sheets it places) | **Source.** Every connection, and each part's identity (ADR 0019) |
| `board-netlist.yaml` | Exported (`python3 tools/kicad.py export hardware/boards/module-main`), with KiCad's ERC over the whole hierarchy. Each part's `of` is its BOM row and `sheet` the circuit it belongs to, which is how a reference (`R17`) is looked up |
| `*.sch.png` | Renders, recorded in `hardware/SHEETS.csv` |
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

## J-B2B-MOD — the allocation

A 2 × 10 header soldered through both boards: **pin *k* is one conductor on
both**, so each board's sheet nets it the same way, and `tools/kicad.py check`
fails if they differ (a pin moved on one sheet only would pass each board's
ERC alone). The jack board's instance is marked `Assembly = none`; one header
is bought.

Fifteen signals cross, and five `AGND_MOD` pins, which is exactly 20: six
jack tips, the three pots' eight nets and the LED's supply. Every return
current of the jack board (the six sleeves, the offset pot's bottom end, the
LED) comes back on the five ground pins. Pin 1 is at the top left
(`pcb-geometry.echo`, `J-B2B-MOD`); odd pins are the left column.

| Pins | Left (odd) | Right (even) |
|---|---|---|
| 1, 2 | `BREATH_INAMP_OUT` | `AGND_MOD` |
| 3, 4 | `GAIN_WIPER` | `RESP_V_IN_HALF` |
| 5, 6 | `AGND_MOD` | `RESP_WIPER` |
| 7, 8 | `GAIN_FLOOR` | `RESP_V_SHAPED` |
| 9, 10 | `OFFSET_WIPER` | `AGND_MOD` |
| 11, 12 | `PITCH_JACK` | `DAC_AVDD` |
| 13, 14 | `AGND_MOD` | `BREATH_JACK` |
| 15, 16 | `MOD1_JACK` | `MOD2_JACK` |
| 17, 18 | `MOD3_JACK` | `AGND_MOD` |
| 19, 20 | `UMBILICAL_POS12` | `MOD4_JACK` |

Why this order:
- **Grounds interleaved on a diagonal** (2, 5, 10, 13, 18): each ground pin
  is next to three pins (the one across and the ones above and below it), so
  five of them can border fifteen signals. Every signal has a ground beside it
  except the LED's `UMBILICAL_POS12`, which is DC.
- **The pots' nets on the top rows**, because the pots are above the header
  (ADR 0024: the pot row, then the jacks). The breath-gain chain
  (`BREATH_INAMP_OUT`, `GAIN_WIPER`, `GAIN_FLOOR`) is the left column, on the
  gain pot's side; the response pot's three nets are the right column, on its
  side; the offset pot, in the middle, closes the group. A ground row
  (9–10 and 13) separates the pots' high-impedance wipers from the jack
  outputs.
- **Each jack on its own column's side**: `PITCH`, `MOD1`, `MOD3` are the
  left column of jacks and take odd pins; `BREATH`, `MOD2`, `MOD4` the right
  column and even pins. The order down the header is the jacks' order down
  the panel.
- **The LED's supply at the bottom**, because the LED is low in the jack
  board's left leg.

What decides whether this changes: the panel layout (being revised now; the
etherCON and the toggle move). The allocation is correct wherever the parts
go; the *reasons* above are about positions, so re-read them when
`pcb-geometry.echo` moves the pots, the jack columns or the header.

## Circuits the boards do not place

- [`link-supervision`](../../module/link-supervision/link-supervision.md) —
  **no parts**: the watchdog and the presence comparator were deleted before
  layout and never had a BOM row. It has nothing to draw. `CLR`, which it
  would drive, is a net inside `dac8568`: `R-CLR-PU` ties it inactive and
  `LK-CLR` asserts it by hand.
- [`panel`](../../module/panel/panel.md) — **no electrical parts**: its one
  BOM row is the aluminium panel. The controls on it belong to the circuits
  that net them (the jacks and pots to their stages, `LED-PANEL` to
  `panel-led`, `SW-POWER` to `umbilical-load-switch`).

## Open, and what decides each

| Item | Decided by |
|---|---|
| `RN-PITCH` (`R-PRECISION`, LT5400) has no MPN on the symbol | Its BOM row's selection |
| `J-B2B-MOD` has no MPN: a long-pin header or a stock one with its insulator moved | `mechanical/module/drc.echo`, *J-B2B-MOD pin length (derived)* |
| Whether the standoffs carry ground between the boards (metal or nylon) | The layout's grounding scheme (ADR 0024) |
| 2 × 8 or 2 × 5 power header: whether the module keeps the bus +5 V | `digital-and-supervision.md`, *the bus +5 V rail* (ADR 0023) |
| The bus's CV and Gate pins (13–16) are unused, on no net | Nothing: the module takes no bus CV |
