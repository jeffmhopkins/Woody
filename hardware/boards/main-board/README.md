# Main board — `main-board`

The one long board at the thumb level (ADR 0017). It carries:
- the thumb switches and both thumb registers;
- the carrier's circuits: the breath sensor's reference, buffer and ADC, power
  entry, the LED strip's drive, the service header and the SPI egress;
- the key chain's two ribbon headers;
- `J-UMB`, where the umbilical arrives from the etherCON's adapter (ADR 0021).

The Matrix is on the lid and reaches it by a ribbon into `J-MCU`. The board
is part of the cassette (ADR 0025): every one of its mounts stands on the one
bottom plate, and eight of them are columns up to the key boards (ADR 0022 as
amended).

> **Status: schematic done, layout not started.** The sheets are the source
> and pass KiCad's ERC. Every part has its footprint and bought part on its
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
| `fp-lib-table` | Registers `hardware/lib/woody.pretty` (the KS-33, `J-CHAIN` and MPXV4006DP footprints) for this project |

The root sheet places, once per instance:
- **the six carrier circuits**;
- **the two thumb registers** (`REG-LT`, `REG-RT`);
- **one key network per thumb key**, plus one at each of the right thumb's
  two reserved spare positions (`sw+`, `sw-`);
- **one pull-up per free bit** (`FREE1`, `FREE2`).

The registers' inputs are wired as `hardware/cluster/key-marker-and-bits/allocation.yaml`
says. Its own parts are the interface circuits' main-board halves:
- from key-chain-loom: both `J-CHAIN` headers, the series resistors, the
  SER terminator, the two beads and the clamp;
- from breath-sense-link: the sensor, its series pair and its two ESD diodes;
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
| C3, C6, C7, C8, C12 | `C-DECOUPLE-CARRIER` | breath-adc, breath-excitation-reference, led-strip-drive |
| C9 | `C-FB-REF` | breath-excitation-reference |
| C15, C16, C17, C18, C19, C20, C21, C22, C23, C24 | `C-KEY` | LT1, LT2, LT3, LT4, RT1, RT2, RT3, RT4, sw+, sw- |
| C4, C5 | `C-REF-OUT` | breath-excitation-reference |
| C10 | `C-STRIP-BULK` | power-entry-instrument |
| D1 | `D-REF-CLAMP` | breath-excitation-reference |
| D2 | `D-REVSHUNT` | power-entry-instrument |
| D5, D6 | `D-TVS-BREATH` | root |
| D3 | `D-TVS-PWR` | power-entry-instrument |
| D4 | `D-USBOR` | power-entry-instrument |
| FB1, FB2 | `FB-CHAIN` | root |
| J2 | `HDR-SERVICE` | service-uart |
| J4, J5 | `J-CHAIN` | root |
| J3 | `J-LED` | led-strip-drive |
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
| R38, R39 | `R-SER-BREATH-INST` | root |
| R37 | `R-SER-TERM` | root |
| R1, R2, R3 | `R-SPI-SER` | carrier |
| SW1, SW2, SW3, SW4, SW5, SW6, SW7, SW8, SW9, SW10 | `SW1-n` | LT1, LT2, LT3, LT4, RT1, RT2, RT3, RT4, sw+, sw- |
| U2 | `U-ADC` | breath-adc |
| U10 | `U-BREATH` | root |
| U5 | `U-BUCK` | power-entry-instrument |
| U3 | `U-BUF` | breath-excitation-reference |
| U7, U8 | `U-KEYS` | REG-LT, REG-RT |
| U6 | `U-LVLSHIFT` | led-strip-drive |
| A1 | `U-MCU-RT` | carrier |
| U4 | `U-REF-BREATH` | breath-excitation-reference |
| U9 | `U-TVS-CHAIN` | root |
| U1 | `U-TVS-SPI` | carrier |

## Open, and what decides each

Before the layout (`tools/pcb.py` does not yet have a main-board mode — its
key-board mode reads `pcb-geometry.echo` by cluster, and this board is `main`):

| Item | Decided by |
|---|---|
| **`J-MCU`'s footprint is KiCad's bare 2 × 12 1.27 mm pad grid.** The XKB header wants 0.70 drills and its shroud's outline and courtyard [ds `XKB-X1270WR-2x12A-9TV01.pdf`], so it gets a `woody.pretty` footprint the way `J-CHAIN`'s Samtec did | Drawn at layout, from the banked drawing |
| **Four layers, decided** (owner, 2026-09-29; ADR 0017 amendment of that date): signal / ground / power / signal, 1.6 mm, JLCPCB stock [ds `JLCPCB-PCB-CAPABILITIES.pdf`, *Thickness*]. Unbroken ground under the breath reference, buffer and ADC and every chain and SPI line. `tools/pcb.py` routes two layers today: its main-board mode needs the inner layers as planes, ground by a via at each pin, and the analog star (`AGND_INST`, one tie `NT-AGND`, `carrier.md` §2) kept as its own island on the plane layer, not lost to one solid pour | The main-board mode of `tools/pcb.py` |
| **Passives may go on the underside** (owner, 2026-09-29). The underside faces the grounded bottom plate, `hardware.kb_spacer_l` below it, over the board's whole length since the cassette (ADR 0025). At `boards.board_clear` that leaves no room for a part (`mechanical/drc.echo` *"main board underside room over the bottom plate"*), so an underside part needs a **window cut through the bottom plate** under it, down to the oak (the second figure on that line), and must be clear of the thumb switches' housings, pins and the mounts' spacers. Through-hole tails face the plate too: `J-CHAIN`'s clear it (*"J-CHAIN pin tails clear of the bottom plate"*), `J-MCU`'s must be checked against its drawing, and the plate stops short of `J-UMB`. The thumb switches are already underside parts | The layout; each window goes into the bottom plate's outline in the body CAD |
| **Every mount grounds the plates** (ADR 0022 point 6, ADR 0025): each is `MountingHole:MountingHole_2.7mm_M2.5_Pad_TopBottom` on `PWR_GND`, pads on both faces (not `_Pad_Via`, whose ring of vias breaks the board house's hole-to-hole rule, as the key board found). The spacer bears on the underside pad and bonds the bottom plate; a column's standoff or an end mount's nut bears on the top pad, and through the column the key plate is bonded too. There are no unplated mounts and no edge notches | Layout; the mounts' places are `pcb-geometry.echo` `main` `standoff … "column"` and `… "end"` |
| **The regulator block holds `U-BUCK` and one can, not four parts.** `U-BUCK`, `C-STRIP-BULK`, `C-BUCK-IN` and `L-BUCK-IN` together take about twice the block's area. Only `U-BUCK` and `C-STRIP-BULK` need its height; `C-BUCK-IN` (5.8 mm) and `L-BUCK-IN` (2.8 mm) go where the room over them is enough (`mechanical/drc.echo`, *main board parts room under the key boards*) | Layout |
| **`A1` (the Matrix) has no footprint**: it is on the lid, and is on the sheet for its pad-to-pin map | The layout skips a part with no footprint |
| **The spare positions' switches (`sw+`, `sw-`) are not fitted** (`config/key-layout.yaml` `spare_bits_switches`), but their network is. The switch sits in the shared key-network sheet | Marked not-fitted on this board at layout |
| **`NT1` and `NT2` are net ties**: `NT1` at `J-UMB` pin 8 (ADR 0018), `NT2` at the analog star (`carrier.md` §2) | Placed there at layout |
| **The thumb switches go on the underside**, entering from below; the near row is turned 180° (ADR 0022) | `pcb-geometry.echo` `main` |
| **The umbilical adapter** (`PCB-UMB-ADAPTER`) is a separate small board: its schematic is [`../umb-adapter/`](../umb-adapter/README.md), not laid out | With this board's layout |

## Revisions

| Rev | Date | What changed | Where |
|---|---|---|---|
| — | 2026-09-29 | Schematic: the carrier circuits migrated to KiCad and placed with the thumb clusters and the interfaces' main-board parts. Not laid out | git history of this directory |
