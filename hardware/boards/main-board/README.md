# Main board — `main-board`

The one long board at the thumb level (ADR 0017). It carries:
- the thumb switches and both thumb registers;
- the carrier's circuits: the breath sensor's reference, buffer and ADC, power
  entry, the LED drive and the LED row (ADR 0028), the service header and the
  SPI egress;
- the key chain's two ribbon headers;
- `J-UMB`, where the umbilical arrives from the etherCON's adapter (ADR 0021).

The Matrix is on the lid and reaches it by a ribbon into `J-MCU`. The board
is part of the cassette (ADR 0025): every one of its mounts stands on the one
bottom plate, and eight of them are columns up to the key boards (ADR 0022 as
amended).

> **Status: laid out and routed by `tools/pcb.py` (`kind: main`) to the 2026-10-01
> outline, finished by hand (rev D below). The ADR 0021 amendment of 2026-10-02
> (`boards.main_tail` `full`, the full-width tail) is not yet taken, so
> `pcb.py check` FAILS on one error — `[cad]` the Edge.Cuts outline against
> `mechanical/export/main-board.dxf` — until the new outline is laid in (*Open*
> below); `kicad.py check` fails with it.** Everything else `check` tests passed at
> rev D: KiCad's DRC with schematic parity, nothing unrouted, the planes, the
> island and its one tie, the mounts and every CAD-placed part. Layer 1 runs along the board and layer 4 across it
> (`layout.yaml` `directions:`; owner, 2026-10-01). The last connection, `IO34`
> into `J-MCU` pin 14, was routed by a scripted hand edit of the board (*What
> the first layout settled*). The renders (`*.pcb-*.png`) and `fab/` are written
> by `pcb.py render` and ledgered in `hardware/SHEETS.csv`. The sheets are the source and pass KiCad's ERC. Every part
> has its footprint and bought part on its symbol (`Footprint`, `Manufacturer`,
> `MPN`, `LCSC`, `Assembly`), from selections whose datasheets are banked. The
> board's outline and every placement the body fixes are exported
> (`mechanical/export/main-board.dxf`, the `main` entries in
> `mechanical/export/pcb-geometry.echo`). The thumb switch positions are
> provisional until M2/M3, as the key boards' are.

What each circuit does, and why, is on its page:
- [`carrier.md`](../../carrier/carrier.md), the board's own page, and its
  circuits:
  - [`breath-adc`](../../carrier/breath-adc/breath-adc.md)
  - [`breath-excitation-reference`](../../carrier/breath-excitation-reference/breath-excitation-reference.md)
  - [`power-entry-instrument`](../../carrier/power-entry-instrument/power-entry-instrument.md)
  - [`service-uart`](../../carrier/service-uart/service-uart.md)
  - [`led-strip-drive`](../../carrier/led-strip-drive/led-strip-drive.md)
- The thumb clusters:
  - [`key-register`](../../cluster/key-register/key-register.md)
  - [`key-switch-network`](../../cluster/key-switch-network/key-switch-network.md)
  - [`key-marker-and-bits`](../../cluster/key-marker-and-bits/key-marker-and-bits.md)
- The interfaces whose main-board parts the root sheet draws:
  - [`key-chain-loom`](../../interfaces/key-chain-loom/key-chain-loom.md)
  - [`breath-sense-link`](../../interfaces/breath-sense-link/breath-sense-link.md)
  - [`spi-link`](../../interfaces/spi-link/spi-link.md)

## Files — what is source, what is generated

| File | What it is |
|---|---|
| `main-board.kicad_sch` (+ the circuit sheets it places) | **Source.** Every connection, and each part's identity (ADR 0019) |
| `board-netlist.yaml` | Exported from the sheets (`tools/kicad.py export hardware/boards/main-board`), with KiCad's ERC over the whole hierarchy |
| `*.sch.png`, `*.pcb-*.png` | Renders, recorded in `hardware/SHEETS.csv` |
| `fab/` | **Generated** by `tools/pcb.py render` (Gerbers, drill, placement), recorded in the ledger against the board and the sheets. Never edit it by hand: `kicad.py check` fails on a stale file, and on any file in `fab/` that no tool wrote |
| `fp-lib-table` | Registers `hardware/lib/woody.pretty` (the KS-33, `J-CHAIN`, `J-MCU`, `J-UMB`, MPXV4006DP and WS2815B-V1 footprints, and through them their 3D models) for this project |
| `sym-lib-table` | Registers `hardware/lib/woody.kicad_sym` (the WS2815B-V1's symbol) for this project |
| `layout.yaml` | **First-layout input** for `tools/pcb.py layout` (`kind: main`): placement of everything the body CAD does not place, the stackup, planes, the `AGND_INST` island and its tie, the breath pair, net classes, keep-outs, heights. Once the board exists it records how the first layout was made (`docs/reference/tooling.md` §4, *The main board*) |
| `main-board.kicad_pcb`, `main-board.kicad_pro` | **The PCB, source from now on** — written once by `layout`, edited in KiCad after; `pcb.py check` holds it to the sheets, the body CAD and `layout.yaml` |

The root sheet places, once per instance:
- **the six carrier circuits**;
- **`breath-sense-link`**, whose parts are all on this board;
- **the two thumb registers** (`REG-LT`, `REG-RT`);
- **one key network per thumb key**, plus one at each of the right thumb's
  two reserved spare positions (`sw+`, `sw-`);
- **one pull-up per free bit** (`FREE1`, `FREE2`).

The registers' inputs are wired as `hardware/cluster/key-marker-and-bits/allocation.yaml`
says. Its own parts are the interface circuits' main-board halves:
- from key-chain-loom: both `J-CHAIN` headers, the series resistors, the
  SER terminator, the two beads and the clamp;
- from spi-link: `J-UMB`.

On this board the chain's return is `PWR_GND` and its 3V3 is `DEV_3V3`
(`hardware/nets.yaml`).

`tools/kicad.py check` holds the board to three things:
- the registers' wiring against `allocation.yaml`;
- each `J-CHAIN` pin against the loom's `J-CHAIN-MAIN-<LH|RH>`;
- ERC.

## The references

Numeric, as the key boards'. The BOM row each one buys from is its `Row` field.

| References | BOM row | Sheet |
|---|---|---|
| C1 | `C-AA-ADC` | breath-adc |
| C2 | `C-ADC-BULK` | breath-adc |
| C11 | `C-BUCK-IN` | power-entry-instrument |
| C13, C14 | `C-DECOUPLE-165` | REG-LT, REG-RT |
| C3, C6–C8, C12, C204 | `C-DECOUPLE-CARRIER` | breath-adc, breath-excitation-reference, led-strip-drive |
| C9 | `C-FB-REF` | breath-excitation-reference |
| C39 | `C-INRUSH-GD` | power-entry-instrument |
| C38 | `C-INRUSH-GS` | power-entry-instrument |
| C15–C24 | `C-KEY` | LT1, LT2, LT3, LT4, RT1, RT2, RT3, RT4, sw+, sw- |
| C25–C37 | `C-LED` | led-strip-drive |
| C4, C5 | `C-REF-OUT` | breath-excitation-reference |
| C203 | `C-SENSOR-OUT` | breath-sense-link |
| C201 | `C-SENSOR-VS-BULK` | breath-sense-link |
| C202 | `C-SENSOR-VS-HF` | breath-sense-link |
| C10 | `C-STRIP-BULK` | power-entry-instrument |
| D20 | `D-INRUSH-RST` | power-entry-instrument |
| D7–D19 | `D-LED` | led-strip-drive |
| D1 | `D-REF-CLAMP` | breath-excitation-reference |
| D2 | `D-REVSHUNT` | power-entry-instrument |
| D5, D6 | `D-TVS-BREATH` | breath-sense-link |
| D3 | `D-TVS-PWR` | power-entry-instrument |
| D4 | `D-USBOR` | power-entry-instrument |
| FB1, FB2 | `FB-CHAIN` | root |
| J2 | `HDR-SERVICE` | service-uart |
| J4, J5 | `J-CHAIN` | root |
| J1 | `J-MCU` | carrier |
| J6 | `J-UMB` | root |
| L1 | `L-BUCK-IN` | power-entry-instrument |
| NT2 | `NT-AGND` | power-entry-instrument |
| NT1 | `NT-DIG` | carrier |
| Q1 | `Q-INRUSH` | power-entry-instrument |
| R5 | `R-ADCDIV-L` | breath-adc |
| R4 | `R-ADCDIV-U` | breath-adc |
| R34–R36 | `R-CHAIN-SER` | root |
| R40 | `R-CS-PULL-INST` | carrier |
| R8 | `R-FB-REF` | breath-excitation-reference |
| R9 | `R-FBX-REF` | breath-excitation-reference |
| R44 | `R-HOP-SER` | root |
| R42 | `R-INRUSH-G` | power-entry-instrument |
| R43 | `R-INRUSH-GD` | power-entry-instrument |
| R41 | `R-INRUSH-GS` | power-entry-instrument |
| R7 | `R-ISO-REF` | breath-excitation-reference |
| R12, R14, R16, R18, R20, R22, R24, R26, R28, R30, R32, R33 | `R-KEY-PU` | LT1, LT2, LT3, LT4, RT1, RT2, RT3, RT4, sw+, sw-, FREE1, FREE2 |
| R13, R15, R17, R19, R21, R23, R25, R27, R29, R31 | `R-KEY-SER` | LT1, LT2, LT3, LT4, RT1, RT2, RT3, RT4, sw+, sw- |
| R10 | `R-LED-PD` | led-strip-drive |
| R11 | `R-LED-SER` | led-strip-drive |
| R6 | `R-REF-IN` | breath-excitation-reference |
| R38, R39 | `R-SER-BREATH-INST` | breath-sense-link |
| R37 | `R-SER-TERM` | root |
| R1–R3 | `R-SPI-SER` | carrier |
| SW1–SW10 | `SW1-n` | LT1, LT2, LT3, LT4, RT1, RT2, RT3, RT4, sw+, sw- |
| U2 | `U-ADC` | breath-adc |
| U10 | `U-BREATH` | breath-sense-link |
| U5 | `U-BUCK` | power-entry-instrument |
| U3 | `U-BUF` | breath-excitation-reference |
| U7, U8 | `U-KEYS` | REG-LT, REG-RT |
| U6 | `U-LVLSHIFT` | led-strip-drive |
| A1 | `U-MCU-RT` | carrier |
| U4 | `U-REF-BREATH` | breath-excitation-reference |
| U9 | `U-TVS-CHAIN` | root |
| U1 | `U-TVS-SPI` | carrier |

## Open, and what decides each

The first layout is `tools/pcb.py layout hardware/boards/main-board` (`kind:
main`; `docs/reference/tooling.md` §4, *The main board*). What it does not yet
finish, and every other open item:

| Item | Decided by |
|---|---|
| **The LED row's places** are the body CAD's (`pcb-geometry.echo` `main` `led`, *"LED row on the main board"* in `mechanical/drc.echo`): one row on the centreline, LED 1 at the tail end where the data arrives, the U-bolt station midway between two LEDs. Laid out as it stands, and reshuffled if the diffusion test moves count or pitch (owner's choice (b), ADR 0028 amendment). **The WS2815B-V1's chamfer marks pin 1 (NC)**; the footprint's silk triangle marks the chamfer, and JLCPCB's own footprint agrees (`hardware/lib/README.md`), so the placement preview should need no rotation offset: pass it only when the chamfer lands on the triangle | Layout; the first order's placement preview |
| **Passives may go on the underside** (owner, 2026-09-29). The underside faces the grounded bottom plate, `hardware.kb_spacer_l` below it, over the board's whole length since the cassette (ADR 0025). At `boards.board_clear` that leaves no room for a part (`mechanical/drc.echo` *"main board underside room over the bottom plate"*), so an underside part needs a **window cut through the bottom plate** under it, down to the oak (the second figure on that line), and must be clear of the thumb switches' housings, pins and the mounts' spacers. Through-hole tails face the plate too: the next row. The thumb switches are already underside parts | The layout; each window goes into the bottom plate's outline in the body CAD |
| **Through-hole tails under the board** (2026-10-01): every part with plated through-hole pins pokes its tails out of the underside toward the grounded bottom plate — `J-CHAIN` ×2, `J-MCU`, `J-UMB`, `HDR-SERVICE` and `U-BUCK` (`config/body.yaml`, *THE THROUGH-HOLE TAILS UNDER THE MAIN BOARD*, says which and why these). `mechanical/drc.echo` *"through-hole tails under the main board clear of the bottom plate"* tests each against what is under it, and the body model draws them for `clash.txt`. `J-CHAIN`'s and `J-MCU`'s clear the plate as supplied. The plate ends short of `J-UMB`'s tail row, and has a window to the oak under `HDR-SERVICE` and under the regulator block (`pcb-geometry.echo` `main` `plate`). **`U-BUCK`'s pins are cut to `boards.tht_trim` below the board after soldering** — as supplied they reach the oak even through the window. `HDR-SERVICE` stands where `boards.service_hdr_at` puts it and `U-BUCK` inside the regulator block, or the window moves with them | A part moved off its window: move `boards.service_hdr_at` (or the block) and rebuild the body CAD; a new through-hole part: add it to `tht_tails` in `mechanical/cad/woody_body.scad` |
| **The references with no clear place on the silkscreen** stay on the fabrication layer; the layout names them when it writes the board | Hand-placed in KiCad, or room made round them |
| **The full-width tail** (ADR 0021 amendment 2026-10-02, `boards.main_tail` `full`): the body CAD's outline gained the corner beside the etherCON adapter (*"main board's tail end runs full width beside the etherCON adapter"* in `mechanical/drc.echo`) and this board has not. Take the new `main-board.dxf` outline and the USB-C keep-out, extend the pours and planes into the corner, re-check edge clearance along the old tongue's edge (ADR 0021, *What the layout has to do*). Until then `pcb.py check` fails on Edge.Cuts | A hand edit of `main-board.kicad_pcb` in KiCad, then `pcb.py check` and `render` |
| **The revision letter on the silkscreen** reads `rev A  2026-09-30` (`layout.yaml` `silk:`, the `.kicad_pcb`), while the table below runs to D | Owner: bump the silk to this table's letter when the full-width tail is laid in, or declare these letters internal and set the silk at the first order |
| **The umbilical adapter** (`PCB-UMB-ADAPTER`) is a separate small board: its schematic is [`../umb-adapter/`](../umb-adapter/README.md), not laid out | With this board's layout |

What the first layout settled, and where it is held:
- **Four layers** (ADR 0017 amendment 2026-09-29), JLCPCB's stack
  `JLC04161H-7628` [ds `datasheets/fab/JLCPCB-IMPEDANCE-STACKUPS.pdf`]. Layer 2 `PWR_GND`, layer 3
  the +12 V behind `Q-INRUSH` (`INST_POS12`, `power-entry-instrument.md` §1a); the +12 V
  ahead of it and the other rails are tracks (`layout.yaml` `net_classes:`). **`AGND_INST` is an island on layer 2** round the analog block,
  its moat bridged once by `NT-AGND` (NT2) beside `U-ADC`, between its VSS and its
  digital pins (`power-entry-instrument.md` §2); `check` fails a second tie, an
  island pad off the island, and any layer-1 track crossing the moat but at the
  tie or as the breath pair.
- **White solder mask** both faces, black legend (`layout.yaml` `fab:`; ADR 0028).
- **Every mount plated on `PWR_GND`**, pads both faces, no other net's copper under
  its hardware (`check`); the U-bolt legs' holes unplated, the outer layers kept
  clear round their hardware.
- **The regulator block holds `U-BUCK` alone** (a rule area), `C-STRIP-BULK`,
  `C-BUCK-IN` and `L-BUCK-IN` beside it where their heights fit (`check_heights`).
- **`A1` (the Matrix) and the spare switches `SW9`, `SW10`** are on the sheets and
  not on this board (`layout.yaml` `not_on_board:`, reported as notes); the spare
  positions' networks are placed.
- **`NT1`** at `J-UMB` pin 8 (ADR 0018); **`U-TVS-SPI`** on the J-MCU side of
  `R-SPI-SER`, where its three channels now are.
- **The thumb switches on the underside**, where the body CAD puts them, the near
  row turned 180° (ADR 0022).
- **`U-BREATH`'s ports point to the tail**, as the body CAD and
  `breath-sense-link.md` (*Mounting*) put them, which turns its pins 1–4 (`VS`,
  `GND`, `Vout`) to the board's far edge, away from the rest of the analog block;
  the island reaches round them (`layout.yaml` `cad_parts:`, `islands:`).
- **`U-BREATH`'s decoupling** (fix round F1): `C202`, `C8` and `C201` on `VS` beside its
  pins at the far edge, the smallest nearest pin 2, inside the island; `C203` on
  `SENSOR_RAW` at `U-BUF`'s input, since pin 4 is walled in by the sensor's own
  courtyard; `C204` at `U-BUF`'s `V+` (`layout.yaml` `parts:`).
- **`R44`** (`R-HOP-SER`, fix round F6) at `REG-LT`'s `QH`, pin 9 (`layout.yaml` `parts:`).
- **`IO34` into `J-MCU` pin 14, by hand** (2026-10-01, a `pcbnew` script, then the
  zones refilled): `IO36` leaves pin 12 at 45° to one via on its own layer-4 line
  north to the ADC, and runs on layer 1 under `R-SPI-SER`'s `IO35` resistor into its
  own; the router's detour of five vias that only joined pin 12 to that line is gone.
  `IO34` leaves pin 14 at 45° under that via, runs along the board on layer 1 below
  `IO36`, and rises to its via at `R-SPI-SER`'s `IO34` resistor. No part moved. A
  re-run of `pcb.py layout` would lose it: the board is the source now.
- **`Q-INRUSH` and its gate network** on the tongue between `HDR-SERVICE` and the
  end mount, behind the clamps at `J-UMB`; its drain meets the layer-3 plane by
  vias (`layout.yaml` `parts:`).

## Revisions

| Rev | Date | What changed | Where |
|---|---|---|---|
| — | 2026-09-29 | Schematic: the carrier circuits migrated to KiCad and placed with the thumb clusters and the interfaces' main-board parts. Not laid out | git history of this directory |
| A | 2026-09-30 | First layout by `tools/pcb.py` (`kind: main`): placed, four layers, planes and island, routed but for the connections under *Open* | `layout.yaml`, `main-board.kicad_pcb` |
| B | 2026-10-01 | Re-laid out on the merged sheets (`Q-INRUSH`, `INST_POS12` the layer-3 plane) and footprints (`J-MCU`, `J-UMB`, the LED's chamfer at pin 1); `U-BREATH` turned so its ports face the tail; decouplers to their ICs' power pins; the reference's feedback network stacked as its ring; routed by the tool's own router with layer directions and rip-up, Freerouting dropped (owner: "routing is super sloppy... similar horizontal and vertical layers"); `pcb.py check` passed then | `layout.yaml`, `main-board.kicad_pcb`, `docs/reference/tooling.md` §4 |
| C | 2026-10-01 | Re-laid out with fix rounds F1 (`U-BREATH` and `U-BUF` decoupling, `C201`-`C204`), F6 (`R44` at `REG-LT`'s `QH`) and F4 (`KS-33` 2.8 mm pads, by `pcb.py update-footprints --pads-resized`); `VS`'s caps turned so their `VS` pads share a row; all but one connection routed | `layout.yaml`, `main-board.kicad_pcb` |
| D | 2026-10-01 | `IO34` routed into `J-MCU` pin 14 by hand, `IO36`'s escape from pin 12 re-routed (*What the first layout settled*); `pcb.py check` passed then, to the 2026-10-01 outline; renders and `fab/` written | `main-board.kicad_pcb`, `fab/` |
