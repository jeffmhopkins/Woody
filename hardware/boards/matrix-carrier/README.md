# Matrix carrier — `matrix-carrier`

The board the ESP32-S3-Matrix stands on, hung from the oak top on three
mounts (owner, 2026-10-03: a "SEPARATE SMALL MATRIX CARRIER", "Hang from the
lid", and option A for its outline;
[ADR 0021](../../../docs/decisions/0021-pcb-mount-ethercon.md), *Amendment,
2026-10-03*). It carries nothing but connections: two 1×10 headers under the
Matrix's pad rows, and `J-MCU-C`, a vertical header hung mouth down under its arm, beside the
main board's `J-MCU`, which the Matrix ribbon (`CBL-MCU-RIBBON`) joins.

> **Status: not orderable until the main board's `J-MCU` takes this board's
> pin order** (*The ribbon's pins* below). Two more things are decided with parts in
> hand, before it is ordered (ADR 0021's *Open* table): which side the
> Matrix's 5V..IO1 pad row is on with its USB-C toward the mouth, and the
> recovery plug's overmould (`openings.usb_ext_overmold_w`; the tail-face
> extension it was drawn for is gone since issue #37).

## Where everything comes from

| What | Source |
|---|---|
| The outline (the arm, the USB-C shell's slot), the headers' rows, J-MCU-C's place, the mounts | the body CAD: `mechanical/export/matrix-carrier.dxf`, `pcb-geometry.echo` cluster `matrix` |
| Every connection and each part's identity | `matrix-carrier.kicad_sch` (ADR 0019); `board-netlist.yaml` is exported from it |
| The pin map | **This board sets the ribbon's pin order** (*The ribbon's pins* below); `J-MCU` pin 25 − *k* follows J-MCU-C pin *k*. Each header pin is the Matrix pad it is named for. `tools/kicad.py check` holds both to `hardware/carrier/netlist.yaml` and the header order to the banked Waveshare pin file |
| The layout | `layout.yaml` holds the limits and the fixed parts; **every track is written out in `carrier_layout.py`**, which re-makes the board's copper and says why each line is where it is. No router runs on this board ([ADR 0030](../../../docs/decisions/0030-boards-laid-out-by-hand.md), *Amendment, 2026-11-20*) |

## How this board is laid out

- **Every line is on the top face**, where the Matrix's two pad rows are
  soldered. The top face has no pour.
- **The bottom face is one whole ground plane.** The board's one via takes the
  Matrix's ground pad down to it.
- **No line crosses another**, because the ribbon's pins are in the order the
  lines arrive in. J-MCU-C's front row leaves toward the far pad row and its
  back row toward the near one, each pin on a lane of its own.
- **Three lines neck to the layout's `track_min`** where they pass together
  between two feet of the near pad row. It is the only neck on the board.
- **J-MCU-C's four ground pins join the plane whole**, without thermal
  spokes: the neighbouring pads leave room for one spoke only. They take more
  heat to solder by hand. The mounts join it whole too, being bolted.

## The ribbon's pins

J-MCU-C (`J1`), owner's choice 2026-11-20 ("Re-order the ribbon pins"). The
even pins are the front row, toward the far side; column 1 is the one nearest
the Matrix.

| Column | Odd pin | Net | Even pin | Net |
|---|---|---|---|---|
| 1 | 1 | IO40 | 2 | IO39 |
| 2 | 3 | U0TXD | 4 | IO6 |
| 3 | 5 | PWR_GND | 6 | IO7 |
| 4 | 7 | U0RXD | 8 | IO38 |
| 5 | 9 | IO2 | 10 | DEV_3V3 |
| 6 | 11 | PWR_GND | 12 | IO37 |
| 7 | 13 | IO1 | 14 | IO36 |
| 8 | 15 | IO3 | 16 | IO35 |
| 9 | 17 | PWR_GND | 18 | IO34 |
| 10 | 19 | no net | 20 | IO33 |
| 11 | 21 | PWR_GND | 22 | INST_5V_A |
| 12 | 23 | INST_5V_A | 24 | INST_5V_A |

> **The main board's `J-MCU` has not followed yet.** Its sheet
> (`hardware/carrier/carrier.kicad_sch`) still carries the order this board
> had before, so `tools/kicad.py check` reports the two ends of the ribbon as
> disagreeing until the main board is laid out again (issue #48). Do not order
> either board until that check passes.

## The references

| Reference | BOM row | What it is |
|---|---|---|
| J1 | `J-MCU-C` | the ribbon's carrier end, 2×12 1.27 mm vertical, on the bottom face under the arm, mouth down, key toward the near edge |
| J2 | `HDR-MATRIX` | the Matrix's 5V..IO1 pad row, surface mount |
| J3 | `HDR-MATRIX` | the Matrix's IO33..RX pad row, surface mount |
| H1–H3 | `MECH-MX-*` | the hanging mounts: insert in the oak, spacer, the board, washer, screw |

## Revisions

| Rev | Date | What changed | Where |
|---|---|---|---|
| A | 2026-10-03 | First layout, every track by hand (`carrier_routes.py`): a bottom-face bus at 0.7 mm, one ladder of vias onto the top face, 5V, 3V3 and ground on the top face 0.4 mm, PWR_GND poured both faces and stitched. `pcb.py check` passes. Not yet ordered | `matrix-carrier.kicad_pcb`, `layout.yaml`, `carrier_routes.py` |
| B | 2026-10-04 | IO6, the MIDI out's tip line (issue #37), from J-MCU-C pin 2 straight up the bottom face, a via, and into J2.5 on the top face (`carrier_routes.py`). J-MCU-C pin 1 stays unconnected: the bus boxes it in. `pcb.py check` passes | `matrix-carrier.kicad_pcb`, `carrier_routes.py` |
| C | 2026-11-20 | Laid out again by hand on one face (`carrier_layout.py`, which replaces `carrier_routes.py`): the ribbon's pins re-ordered so no line crosses another, every line on the top face, the bottom face one whole ground plane, one via. `pcb.py check` passes; the ribbon check against the main board fails until `J-MCU` follows. Not yet ordered | `matrix-carrier.kicad_sch`, `matrix-carrier.kicad_pcb`, `layout.yaml`, `carrier_layout.py` |
| D | 2026-11-21 | J-MCU-C is a vertical header (owner, 2026-11-21; ADR 0018, *Amendment, 2026-11-21*), its pads where the right-angle header's were, so no track moved. Its outline is not printed (the insulator overhangs the arm's end); its reference and key side are, beside it. `pcb.py check` passes. Not yet ordered | `matrix-carrier.kicad_sch`, `matrix-carrier.kicad_pcb`, `layout.yaml`, `carrier_layout.py` |
