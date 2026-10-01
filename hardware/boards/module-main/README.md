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

**The jack filters sit at `J-B2B-MOD`** (pre-layout review A2-20, handed from
F2): the jack board carries only the jacks, the pots, the LED and the header,
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

Fifteen signals cross, and five `AGND_MOD` pins, which is exactly 20: six
jack tips, the three pots' eight nets and the LED's supply. Every return
current of the jack board (the six sleeves, the offset pot's bottom end, the
LED) comes back on the five ground pins. Pin 1 is at the top left
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
| 19, 20 | `UMBILICAL_POS12` | `MOD4_JACK` |

Why this order:
- **Grounds interleaved on a diagonal** (2, 5, 10, 13, 18): each ground pin
  is next to three pins (the one across and the ones above and below it), so
  five of them can border fifteen signals. Every signal has a ground beside it
  except the LED's `UMBILICAL_POS12`, which is DC.
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
- **The LED's supply at the bottom**, because the LED is low in the jack
  board's left leg.

What decides whether this changes: the board layout. The panel layout is
settled (ADR 0024 points 11–13: the etherCON at the bottom, the toggle
throwing left–right, the jack swap). The allocation is correct wherever the parts
go; the *reasons* above are about positions, so re-read them when
`pcb-geometry.echo` moves the pots, the jack columns or the header.


## `R-SET-DAC` placement — a rule, not a preference

The owner accepted (2026-10-01) that an open `R-SET-DAC` drives `DAC_AVDD` to
about 11 V, over the DAC8568's 6 V absolute maximum, with no clamp. Layout is one
of the three mitigations (`module/power-entry/power-entry.md`, *The DAC rail*,
*Its failures*):

- Keep `R-SET-DAC` (Vishay TNPW e3, 0603, anti-sulfur) **away from the
  standoffs, the connectors and the board edges** — where the board flexes as it
  is screwed down and the cables are plugged — because flex cracking is what
  opens a chip resistor that carries no stress.
- **Orient its long axis parallel to the board's long edge**, so bending runs
  along the chip, not across its terminations.
- Put it inside the `SET` guard ring at `OUT`'s potential, on both sides, with
  `C-SET-DAC` beside it and both grounds Kelvin to `C-REG-OUT`'s
  (`[ds ADI-LT3042.pdf p.14–15]`).
- Never substitute a part without an anti-sulfur claim in its datasheet.
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
  `AGND_MOD`.
- **`J-B2B-MOD`** is Samtec `TSW-110-09-G-D` (row), insulator on this board's
  front face. On **both** boards its footprint goes on the top side, **not
  mirrored** — the jack board's too, though the header's body is on that
  board's rear ([`module-jack/README.md`](../module-jack/README.md)).
- **Both `SW-POWER` lugs** wire to this board, beside `U-LOADSW`.

## Open, and what decides each

| Item | Decided by |
|---|---|
| The metal standoffs' part (the CAD's `standoff.*` still cites the polyamide spacer) | The module CAD owner; the pads' nets are settled above |
| `U-ISO`'s exact place: RECOM RPA20-2412SAW, 25.4 × 25.4 × 10.2 mm on 5.6 mm pins `[ds RECOM-RPA20-AW.pdf PD-7, PD-8]`, on this board's **rear face** (too tall for the boards' gap), with `L-ISO-IN`, `C2`, `C-ISO-IN`, `C-ISO-OUT` and `C-ISO-Y` beside it, and `NT-UMB-MOD` at the etherCON's pins 6/8 (ADR 0027). The module CAD holds an envelope for it and its filter (`config/module.yaml` `iso.*`, lower left above the NE8FAV's tails, clash-checked) | The layout |
| `U-ISO`'s supply: the RPA20 is end-of-life, 20 at DigiKey on 2026-09-30 (the row); the RP20-2412SAW drops into the same footprint with pads 4 and 6 swapped (ADR 0027) | The order — buy spares now |
| The bus's +5 V, CV and Gate pins (11–16) are unused, on no net | Nothing: the module makes its own 5 V and takes no bus CV (ADR 0023 point 3, amended) |
