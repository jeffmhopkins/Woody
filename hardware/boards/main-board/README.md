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
| `fp-lib-table` | Registers `hardware/lib/woody.pretty` (the KS-33, `J-CHAIN`, `J-MCU`, `J-UMB`, MPXV4006DP and WS2815B-V1 footprints, and through them their 3D models) for this project |
| `sym-lib-table` | Registers `hardware/lib/woody.kicad_sym` (the WS2815B-V1's symbol) for this project |

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

Before the layout (`tools/pcb.py` does not yet have a main-board mode — its
key-board mode reads `pcb-geometry.echo` by cluster, and this board is `main`):

| Item | Decided by |
|---|---|
| **Four layers, decided** (owner, 2026-09-29; ADR 0017 amendment of that date): signal / ground / power / signal, 1.6 mm, JLCPCB stock [ds `JLCPCB-PCB-CAPABILITIES.pdf`, *Thickness*]. Unbroken ground under the breath reference, buffer and ADC and every chain and SPI line. `tools/pcb.py` routes two layers today: its main-board mode needs the inner layers as planes, ground by a via at each pin, and the analog star (`AGND_INST`, one tie `NT-AGND`, `carrier.md` §2) kept as its own island on the plane layer, not lost to one solid pour | The main-board mode of `tools/pcb.py` |
| **White solder mask, both faces** (owner, ADR 0028): the top face is the LED row's first reflector. Record it in `layout.yaml` `fab: mask` when the main-board layout is written (the key boards' are green) | Decided; the layout writes it |
| **The LED row's places** are the body CAD's (`pcb-geometry.echo` `main` `led`, *"LED row on the main board"* in `mechanical/drc.echo`): one row on the centreline, LED 1 at the tail end where the data arrives, the U-bolt station midway between two LEDs. Laid out as it stands, and reshuffled if the diffusion test moves count or pitch (owner's choice (b), ADR 0028 amendment). **The WS2815B-V1's chamfer marks pin 1 (NC)**; the footprint's silk triangle marks the chamfer, and JLCPCB's own footprint agrees (`hardware/lib/README.md`), so the placement preview should need no rotation offset: pass it only when the chamfer lands on the triangle | Layout; the first order's placement preview |
| **Passives may go on the underside** (owner, 2026-09-29). The underside faces the grounded bottom plate, `hardware.kb_spacer_l` below it, over the board's whole length since the cassette (ADR 0025). At `boards.board_clear` that leaves no room for a part (`mechanical/drc.echo` *"main board underside room over the bottom plate"*), so an underside part needs a **window cut through the bottom plate** under it, down to the oak (the second figure on that line), and must be clear of the thumb switches' housings, pins and the mounts' spacers. Through-hole tails face the plate too: the next row. The thumb switches are already underside parts | The layout; each window goes into the bottom plate's outline in the body CAD |
| **Through-hole tails under the board** (2026-10-01): every part with plated through-hole pins pokes its tails out of the underside toward the grounded bottom plate — `J-CHAIN` ×2, `J-MCU`, `J-UMB`, `HDR-SERVICE` and `U-BUCK` (`config/body.yaml`, *THE THROUGH-HOLE TAILS UNDER THE MAIN BOARD*, says which and why these). `mechanical/drc.echo` *"through-hole tails under the main board clear of the bottom plate"* tests each against what is under it, and the body model draws them for `clash.txt`. `J-CHAIN`'s and `J-MCU`'s clear the plate as supplied. The plate ends short of `J-UMB`'s tail row, and has a window to the oak under `HDR-SERVICE` and under the regulator block (`pcb-geometry.echo` `main` `plate`). **`U-BUCK`'s pins are cut to `boards.tht_trim` below the board after soldering** — as supplied they reach the oak even through the window. `HDR-SERVICE` stands where `boards.service_hdr_at` puts it and `U-BUCK` inside the regulator block, or the window moves with them | A part moved off its window: move `boards.service_hdr_at` (or the block) and rebuild the body CAD; a new through-hole part: add it to `tht_tails` in `mechanical/cad/woody_body.scad` |
| **Every mount grounds the plates** (ADR 0022 point 6, ADR 0025): each is `MountingHole:MountingHole_2.7mm_M2.5_Pad_TopBottom` on `PWR_GND`, pads on both faces (not `_Pad_Via`, whose ring of vias breaks the board house's hole-to-hole rule, as the key board found). The spacer bears on the underside pad and bonds the bottom plate; a column's standoff or an end mount's nut bears on the top pad, and through the column the key plate is bonded too. There are no unplated mounts and no edge notches | Layout; the mounts' places are `pcb-geometry.echo` `main` `standoff … "column"` and `… "end"` |
| **The regulator block holds `U-BUCK` and one can, not four parts.** `U-BUCK`, `C-STRIP-BULK`, `C-BUCK-IN` and `L-BUCK-IN` together take about twice the block's area. Only `U-BUCK` and `C-STRIP-BULK` need its height; `C-BUCK-IN` (5.8 mm) and `L-BUCK-IN` (2.8 mm) go where the room over them is enough (`mechanical/drc.echo`, *main board parts room under the key boards*) | Layout |
| **`U-BREATH`'s pins 1–4 (`Vs`, `GND`, `Vout`) face the board's far edge, not the analog island**, once its ports face the tail as `breath-sense-link.md` places it: the part's pin 1 is fixed relative to its ports (case 1351-01's top view, `datasheets/analog/MPXV4006DP.pdf` p.20; `hardware/lib/README.md`). A first scratch placement (2026-09-30) that put pins 1–4 toward the island had the ports pointing at the mouth. The island's parts go on that side or the pins reach them round the part | Layout |
| **`A1` (the Matrix) has no footprint**: it is on the lid, and is on the sheet for its pad-to-pin map | The layout skips a part with no footprint |
| **The spare positions' switches (`sw+`, `sw-`) are not fitted** (`config/key-layout.yaml` `spare_bits_switches`), but their network is. The switch sits in the shared key-network sheet | Marked not-fitted on this board at layout |
| **`NT1` and `NT2` are net ties**: `NT1` at `J-UMB` pin 8 (ADR 0018), `NT2` at the analog star (`carrier.md` §2) | Placed there at layout |
| **The thumb switches go on the underside**, entering from below; the near row is turned 180° (ADR 0022) | `pcb-geometry.echo` `main` |
| **The umbilical adapter** (`PCB-UMB-ADAPTER`) is a separate small board: its schematic is [`../umb-adapter/`](../umb-adapter/README.md), not laid out | With this board's layout |

## Revisions

| Rev | Date | What changed | Where |
|---|---|---|---|
| — | 2026-09-29 | Schematic: the carrier circuits migrated to KiCad and placed with the thumb clusters and the interfaces' main-board parts. Not laid out | git history of this directory |
