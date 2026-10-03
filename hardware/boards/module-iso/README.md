# Module iso board — `module-iso`

The Eurorack module's third board (ADR 0023 point 2, amended 2026-10-03 by the
owner: *"3 boards for module is correct"*; issue #22): **the instrument's
isolated supply** — `U-ISO` (RECOM RPA20-2412SAW, ADR 0027) and its filter
(`L-ISO-IN`, `L-CM-ISO`, `C-ISO-BULK` `C2`, `C-ISO-IN`, `C-ISO-Y`,
`C-ISO-OUT`) — on a board of its own, parallel to
[`module-main`](../module-main/README.md) and **behind it**.

**Why a board of its own.** On the main board's rear face `U-ISO`'s 25 mm body
put its pins, its 2 mm isolation gap and its `PWR_GND` return pour in the
middle of the DAC's corner, where the DAC meets the mod channels. Twenty
connections stayed unrouted there, and re-placing the corner first left more,
not fewer (`module-main/README.md`). Off the main board, the converter takes
none of its copper.

**Its outline is derived** in the module CAD (`config/module.yaml`
`iso_board`; `mechanical/module/export/iso-board.dxf`): the boards' side edges,
a bottom edge just above the NE8FAV's tails, a notch at its lower right that
`J-PWR-EURO` and its mated socket stand in, and a top edge (`iso_board.y1`)
below the rear trimmers, so each stays adjustable from behind
(`mechanical/module/drc.echo`, *trimmers adjustable from behind*). It stands
off the main board's rear face on three stock spacers used uncut
(`MECH-STANDOFF-ISO`): **the gap is the spacer** (*iso board gap*). Its parts
stand on its **rear** face, away from the main board; on the front only
`U-ISO`'s tails and `J-B2B-ISO`'s posts stand in the gap, over main-board
parts no taller than `iso_board.under_h`.

> **Status: laid out and routed by `tools/pcb.py` (`kind: module`), 2026-10-03.**
> Two layers. `pcb.py check` passes: KiCad's DRC with schematic parity, nothing
> unrouted, every courtyard inside the board, every CAD-placed part where
> `pcb-geometry.echo` puts it, the isolation gap, and `J-B2B-ISO` mating with
> the main board's pin for pin (`check_b2b`). The mask colour is **not
> decided** — green until the owner says (*Open*).

## J-B2B-ISO — the allocation

A 2 × 5 header (`J-B2B-ISO`, Samtec TSW-105-09-G-D) soldered through this
board and the main board: **pin *k* is one conductor on both**, so both
sheets net it the same (`tools/kicad.py check`) and both layouts put it on the
**top face, unmirrored**, pin 1 at the bottom left seen from the panel
(`pcb-geometry.echo`). Its insulator is on the main board's rear face; this
board has only its posts. Each net on two pins, for the converter's current:

| Pins | Net | Side of the barrier |
|---|---|---|
| 1, 2 | `PWR_GND` | output: `U-ISO`'s return, to the load switch and `NT-UMB-MOD` on the main board |
| 3, 4 | `ISO_POS12` | output: the isolated +12 V, to the load switch |
| 5, 6 | — (open) | **the isolation gap**: two pitches between the sides |
| 7, 8 | `ISO_FILT_NEG` | input: the −12 V leg after `FB4` |
| 9, 10 | `ISO_FB2` | input: the +12 V leg after `PTC-ISO`, `D2` and `FB2` |

The output pairs are at the left end, under `U-ISO`'s output row; the input
pairs at the right, toward `L-ISO-IN` and `L-CM-ISO`.

## The layout

`layout.yaml` beside this file records how the first layout was made; the
`.kicad_pcb` is the source now. `U-ISO` and `J-B2B-ISO` are placed by the
module CAD, `U-ISO` turned so its output row (pins 4, 5, 6) runs along the
bottom beside the header and its input pins (1, 2) are at the top. The layout
put:

- **`L-CM-ISO` (`L2`) on the right, turned 45°** (`config/module.yaml`
  `iso.filter`), `L-ISO-IN` (`L1`) under it beside the header's input pairs;
- **`C-ISO-BULK` (`C2`) and `C-ISO-IN` (`C44`) across `U-ISO`'s input pins**
  at the top, `C-ISO-OUT` (`C45`) beside the output row and the header;
- **`C-ISO-Y` (`C46`) at the converter's top left**, its `PWR_GND` pad
  outward, so the return's track keeps the gap from the `−Vin` pin;
- **the isolation gap** (`layout.yaml` `isolation:`, 2.0 mm, functional, not
  a safety rating): input nets and output nets this far apart on both layers,
  `C46` bridging it by design;
- tracks 0.8 mm for every supply net (`net_classes:`);
- the three standoff pads on no net (`power-entry.md`, *Grounding*).

## Files

| File | What it is |
|---|---|
| `module-iso.kicad_sch` (+ power-entry's `iso` page) | **Source** (ADR 0019) |
| `board-netlist.yaml` | Exported (`python3 tools/kicad.py export hardware/boards/module-iso`), with KiCad's ERC |
| `*.sch.png` | Renders, recorded in `hardware/SHEETS.csv` |
| `module-iso.kicad_pcb`, `module-iso.kicad_pro` | **Source** since the first layout: edit in KiCad 9; `python3 tools/pcb.py check hardware/boards/module-iso` holds it |
| `layout.yaml` | How the first layout was made |
| `module-iso.pcb-*.png`, `fab/` | Written by `python3 tools/pcb.py render`, recorded in `hardware/SHEETS.csv` |
| `fp-lib-table`, `sym-lib-table` | Register `hardware/lib/` (`U-ISO`'s and `L-CM-ISO`'s footprints) |

## Open, and what decides each

| Item | Decided by |
|---|---|
| The boards' mask colour (green in `layout.yaml` `fab:` until decided) | The owner, before the first order |
| `J-B2B-ISO`'s LCSC part number (the MPN is the TSW family's, as `J-B2B-MOD`) | The module's parts order |
| The spacers' material: `MECH-STANDOFF-ISO` is the same 8 mm metal stock as `MECH-STANDOFF-MOD`, whose metal part is not chosen yet (its row) | The module CAD owner, with `MECH-STANDOFF-MOD` |
