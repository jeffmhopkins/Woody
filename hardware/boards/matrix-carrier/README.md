# Matrix carrier — `matrix-carrier`

The board the ESP32-S3-Matrix stands on, hung from the oak top on three
mounts (owner, 2026-10-03: a "SEPARATE SMALL MATRIX CARRIER", "Hang from the
lid", and option A for its outline;
[ADR 0021](../../../docs/decisions/0021-pcb-mount-ethercon.md), *Amendment,
2026-10-03*). It carries nothing but connections: two 1×10 headers under the
Matrix's pad rows, and `J-MCU-C`, hung under its arm straight above the main
board's `J-MCU`, which the Matrix ribbon (`CBL-MCU-RIBBON`) joins.

> **Status: orderable as a prototype.** Two things are decided with parts in
> hand, before it is ordered (ADR 0021's *Open* table): which side the
> Matrix's 5V..IO1 pad row is on with its USB-C toward the mouth, and the
> extension plug's overmould (`openings.usb_ext_overmold_w`).

## Where everything comes from

| What | Source |
|---|---|
| The outline (the arm, the USB-C shell's slot), the headers' rows, J-MCU-C's place, the mounts | the body CAD: `mechanical/export/matrix-carrier.dxf`, `pcb-geometry.echo` cluster `matrix` |
| Every connection and each part's identity | `matrix-carrier.kicad_sch` (ADR 0019); `board-netlist.yaml` is exported from it |
| The pin map | J-MCU-C pin *k* is `J-MCU` pin 25 − *k*; each header pin is the Matrix pad it is named for. `tools/kicad.py check` holds both to `hardware/carrier/netlist.yaml` and the header order to the banked Waveshare pin file |
| The layout | `layout.yaml` places the parts; **every track is drawn by `carrier_routes.py`**, which re-makes the board and says why the bus has one ladder. The `.kicad_pcb` is the source afterwards |

## The references

| Reference | BOM row | What it is |
|---|---|---|
| J1 | `J-MCU-C` | the ribbon's carrier end, 2×12 1.27 mm, on the bottom face under the arm |
| J2 | `HDR-MATRIX` | the Matrix's 5V..IO1 pad row, surface mount |
| J3 | `HDR-MATRIX` | the Matrix's IO33..RX pad row, surface mount |
| H1–H3 | `MECH-MX-*` | the hanging mounts: insert in the oak, spacer, the board, washer, screw |

## Revisions

| Rev | Date | What changed | Where |
|---|---|---|---|
| A | 2026-10-03 | First layout, every track by hand (`carrier_routes.py`): a bottom-face bus at 0.7 mm, one ladder of vias onto the top face, 5V, 3V3 and ground on the top face 0.4 mm, PWR_GND poured both faces and stitched. `pcb.py check` passes. Not yet ordered | `matrix-carrier.kicad_pcb`, `layout.yaml`, `carrier_routes.py` |
