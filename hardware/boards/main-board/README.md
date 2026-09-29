# Main board — `main-board`

The one long board at the thumb level (ADR 0017). It carries:
- the thumb switches and both thumb registers;
- the carrier's circuits: the breath sensor's reference, buffer and ADC, power
  entry, the LED strip's drive, the service header and the SPI egress;
- the key chain's two ribbon headers;
- `J-UMB`, where the umbilical arrives from the etherCON's adapter (ADR 0021).

The Matrix is on the lid and reaches it by a ribbon into `J-MCU`. The board
stands on the thumb plates and the oak (ADR 0022).

> **Status: schematic done, layout not started.** The sheets are the source
> and pass KiCad's ERC; its outline and every placement the body fixes are
> exported (`mechanical/export/main-board.dxf`, the `main` entries in
> `mechanical/export/pcb-geometry.echo`). What the layout still has to settle
> is listed under *Open*. The thumb switch positions are provisional until
> M2/M3, as the key boards' are.

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
| `fp-lib-table` | Registers `hardware/lib/woody.pretty` (the KS-33 footprint) for this project |

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
| E1 | `MECH-GNDBOND` | power-entry-instrument |
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
| **Footprints and bought parts** (`Footprint`, `Manufacturer`, `MPN`, `LCSC`, `Assembly` on every symbol) | The part selections banked for this board; set on the sheets with `tools/kicad.py set-field` |
| **`A1` (the Matrix) has no footprint**: it is on the lid, and is on the sheet for its pad-to-pin map | The layout skips a part with no footprint |
| **The spare positions' switches (`sw+`, `sw-`) are not fitted** (`config/key-layout.yaml` `spare_bits_switches`), but their network is. The switch sits in the shared key-network sheet | Marked not-fitted on this board at layout |
| **`NT1` and `NT2` are net ties**: `NT1` at `J-UMB` pin 8 (ADR 0018), `NT2` at the analog star (`carrier.md` §2) | Placed there at layout |
| **The thumb switches go on the underside**, entering from below; the near row is turned 180° (ADR 0022) | `pcb-geometry.echo` `main` |
| **The umbilical adapter** (`PCB-UMB-ADAPTER`) is a separate small board: its schematic is [`../umb-adapter/`](../umb-adapter/README.md), not laid out | With this board's layout |
| **Test points and links** (`carrier.md`, *Component table*: proposed `TP-*`, `LK-*`) | Added to the root sheet with the layout |

## Revisions

| Rev | Date | What changed | Where |
|---|---|---|---|
| — | 2026-09-29 | Schematic: the carrier circuits migrated to KiCad and placed with the thumb clusters and the interfaces' main-board parts. Not laid out | git history of this directory |
