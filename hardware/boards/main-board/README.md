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

> **Status: first layout written by `tools/pcb.py` (`kind: main`), not yet
> clean.** `main-board.kicad_pcb` is placed from the body CAD and `layout.yaml`,
> four layers, planes and the analog island in, routed by the tool and
> Freerouting; what `pcb.py check` still fails on is under *Open*, below. The
> sheets are the source and pass KiCad's ERC. Every part has its footprint and bought part on its
> symbol (`Footprint`, `Manufacturer`, `MPN`, `LCSC`, `Assembly`), from
> selections whose datasheets are banked, except those under *Open*. The
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
| `*.sch.png` | Renders, recorded in `hardware/SHEETS.csv` |
| `fp-lib-table` | Registers `hardware/lib/woody.pretty` (the KS-33, `J-CHAIN`, MPXV4006DP and WS2815B-V1 footprints) for this project |
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
| C25–C37 | `C-LED` | led-strip-drive |
| C3, C6, C7, C8, C12 | `C-DECOUPLE-CARRIER` | breath-adc, breath-excitation-reference, led-strip-drive |
| C9 | `C-FB-REF` | breath-excitation-reference |
| C15, C16, C17, C18, C19, C20, C21, C22, C23, C24 | `C-KEY` | LT1, LT2, LT3, LT4, RT1, RT2, RT3, RT4, sw+, sw- |
| C4, C5 | `C-REF-OUT` | breath-excitation-reference |
| C10 | `C-STRIP-BULK` | power-entry-instrument |
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
| R5 | `R-ADCDIV-L` | breath-adc |
| R4 | `R-ADCDIV-U` | breath-adc |
| R34, R35, R36 | `R-CHAIN-SER` | root |
| R8 | `R-FB-REF` | breath-excitation-reference |
| R9 | `R-FBX-REF` | breath-excitation-reference |
| R7 | `R-ISO-REF` | breath-excitation-reference |
| R12, R14, R16, R18, R20, R22, R24, R26, R28, R30, R32, R33 | `R-KEY-PU` | LT1, LT2, LT3, LT4, RT1, RT2, RT3, RT4, sw+, sw-, FREE1, FREE2 |
| R13, R15, R17, R19, R21, R23, R25, R27, R29, R31 | `R-KEY-SER` | LT1, LT2, LT3, LT4, RT1, RT2, RT3, RT4, sw+, sw- |
| R10 | `R-LED-PD` | led-strip-drive |
| R11 | `R-LED-SER` | led-strip-drive |
| R6 | `R-REF-IN` | breath-excitation-reference |
| R38, R39 | `R-SER-BREATH-INST` | breath-sense-link |
| R37 | `R-SER-TERM` | root |
| R1, R2, R3 | `R-SPI-SER` | carrier |
| SW1, SW2, SW3, SW4, SW5, SW6, SW7, SW8, SW9, SW10 | `SW1-n` | LT1, LT2, LT3, LT4, RT1, RT2, RT3, RT4, sw+, sw- |
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
| **Connections left unrouted.** `pcb.py check` fails on each by name (`[unconnected]`); the layout prints the list when it writes the board. The breath pair, every plane pin's via, and all but these are routed; what is left is in the densest corners: the reference's feedback network at the mouth edge, the register pins walled in by their own key lines, the long `U-ADC` to `J-MCU` lines, and a chain hop into `J5` | Routed by hand in KiCad, or a re-run once the footprints below are final (placement moves change what is left) |
| **`J-MCU`'s footprint is KiCad's bare 2 × 12 1.27 mm pad grid.** The XKB header wants 0.70 drills and its shroud's outline and courtyard [ds `XKB-X1270WR-2x12A-9TV01.pdf`]; the bare grid's 0.175 mm rings also fail the board house's 0.18 minimum, 24 `[annular_width]` failures in `check` | The `woody.pretty` footprint being drawn from the banked drawing; then re-check `layout.yaml` `connectors: J-MCU` (its pad-row offset is the placeholder's) and re-run the layout |
| **`J-UMB`'s footprint is KiCad's horizontal 1 × 8 header**, placed by its pin row 1.5 mm in front of the insulator, a figure of that footprint | The Hanxia footprint; then re-check `layout.yaml` `connectors: J-UMB` |
| **The LED row's chamfer**: the WS2815B-V1's marks pin 4, not pin 1; the LEDs stand where the body CAD puts them, LED 1 at the tail where the data arrives (`pcb-geometry.echo` `main` `led`) | The assembler's rotation preview, first order |
| **Passives may go on the underside** (owner, 2026-09-29). The underside faces the grounded bottom plate, `hardware.kb_spacer_l` below it, over the board's whole length since the cassette (ADR 0025). At `boards.board_clear` that leaves no room for a part (`mechanical/drc.echo` *"main board underside room over the bottom plate"*), so an underside part needs a **window cut through the bottom plate** under it, down to the oak (the second figure on that line), and must be clear of the thumb switches' housings, pins and the mounts' spacers. Through-hole tails face the plate too: `J-CHAIN`'s clear it (*"J-CHAIN pin tails clear of the bottom plate"*), `J-MCU`'s must be checked against its drawing, and the plate stops short of `J-UMB`. The first layout needed none: every passive is on the top | A later layout that needs the room; each window goes into the bottom plate's outline in the body CAD |
| **The references with no clear place on the silkscreen** stay on the fabrication layer; the layout names them when it writes the board | Hand-placed in KiCad, or room made round them |
| **The umbilical adapter** (`PCB-UMB-ADAPTER`) is a separate small board: its schematic is [`../umb-adapter/`](../umb-adapter/README.md), not laid out | With this board's layout |

What the first layout settled, and where it is held:
- **Four layers** (ADR 0017 amendment 2026-09-29), JLCPCB's stack `JLC04161H-7628`
  [ds `datasheets/fab/JLCPCB-IMPEDANCE-STACKUPS.pdf`]: layer 2 `PWR_GND`, layer 3
  the +12 V (`UMBILICAL_POS12`), the rails that are tracks in `layout.yaml`
  `net_classes:`. **`AGND_INST` is an island on layer 2** round the analog block,
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

## Revisions

| Rev | Date | What changed | Where |
|---|---|---|---|
| — | 2026-09-29 | Schematic: the carrier circuits migrated to KiCad and placed with the thumb clusters and the interfaces' main-board parts. Not laid out | git history of this directory |
| A | 2026-09-30 | First layout by `tools/pcb.py` (`kind: main`): placed, four layers, planes and island, routed but for the connections under *Open* | `layout.yaml`, `main-board.kicad_pcb` |
