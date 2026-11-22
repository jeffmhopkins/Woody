# Matrix carrier — `matrix-carrier`

The board the ESP32-S3-Matrix stands on, hung from the oak top on three
mounts (owner, 2026-10-03: a "SEPARATE SMALL MATRIX CARRIER", "Hang from the
lid", and option A for its outline;
[ADR 0021](../../../docs/decisions/0021-pcb-mount-ethercon.md), *Amendment,
2026-10-03*). It carries nothing but connections: two 1×10 headers under the
Matrix's pad rows, and `J-MCU-C`, a vertical header hung mouth down under its arm, beside the
main board's `J-MCU`, which the Matrix ribbon (`CBL-MCU-RIBBON`) joins.

> **Status: laid out and checked against the main board's `J-MCU`
> (`tools/kicad.py check`); not yet ordered.** Two things are decided with parts in
> hand, before it is ordered (ADR 0021's *Open* table): which side the
> Matrix's 5V..IO1 pad row is on with its USB-C toward the mouth, and the
> recovery plug's overmould (`openings.usb_ext_overmold_w`; the tail-face
> extension it was drawn for is gone since issue #37).

## Where everything comes from

| What | Source |
|---|---|
| The outline (the arm, the USB-C shell's slot), the headers' rows, J-MCU-C's place, the mounts | the body CAD: `mechanical/export/matrix-carrier.dxf`, `pcb-geometry.echo` cluster `matrix` |
| Every connection and each part's identity | `matrix-carrier.kicad_sch` (ADR 0019); `board-netlist.yaml` is exported from it |
| The pin map | **This board sets the ribbon's pin order** (*The ribbon's pins* below); `J-MCU` pin *k* is J-MCU-C pin *k* (the header is turned half a turn; ADR 0018, *Amendment, 2026-11-22*). Each header pin is the Matrix pad it is named for. `tools/kicad.py check` holds both to `hardware/carrier/netlist.yaml` and the header order to the banked Waveshare pin file |
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
- **J-MCU-C's ground pins join the plane whole**, without thermal
  spokes: the neighbouring pads leave room for one spoke only. They take more
  heat to solder by hand. The mounts join it whole too, being bolted.

## The ribbon's pins

J-MCU-C (`J1`). The order along the header is the owner's choice of
2026-11-20 ("Re-order the ribbon pins"); the numbers are those of a header
turned half a turn (owner, 2026-11-22), so each is `J-MCU`'s pin of the same
number and the ribbon is a bought one, made pin 1 to pin 1 (`CBL-MCU-RIBBON`).
The odd pins are the front row, toward the far side; column 1 is the one
nearest the Matrix. Pin 6 is the ribbon's spare, on ground at both ends.

| Column | Odd pin | Net | Even pin | Net |
|---|---|---|---|---|
| 1 | 23 | IO39 | 24 | IO40 |
| 2 | 21 | IO6 | 22 | U0TXD |
| 3 | 19 | IO7 | 20 | PWR_GND |
| 4 | 17 | IO38 | 18 | U0RXD |
| 5 | 15 | DEV_3V3 | 16 | IO2 |
| 6 | 13 | IO37 | 14 | PWR_GND |
| 7 | 11 | IO36 | 12 | IO1 |
| 8 | 9 | IO35 | 10 | IO3 |
| 9 | 7 | IO34 | 8 | PWR_GND |
| 10 | 5 | IO33 | 6 | PWR_GND |
| 11 | 3 | INST_5V_A | 4 | PWR_GND |
| 12 | 1 | INST_5V_A | 2 | INST_5V_A |

## The references

| Reference | BOM row | What it is |
|---|---|---|
| J1 | `J-MCU-C` | the ribbon's carrier end, 2×12 1.27 mm vertical, on the bottom face under the arm, mouth down, key toward the far side |
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
| E | 2026-11-22 | J-MCU-C turned half a turn, its key toward the far side: pin *k* is `J-MCU` pin *k*, so the ribbon is a stocked pin-1-to-pin-1 assembly (owner, 2026-11-22; pre-fab review F3; ADR 0018, *Amendment, 2026-11-22*). No pad moved, only the numbers. The spare pin (6) is on ground. The Matrix and its two headers stand further toward the tail by half of what the tail grew (`config/body.yaml` `boards.umb_socket_d`), centred in the longer tail's window (owner, 2026-11-22), so the arm's lines are that much longer. `pcb.py check` passes. Not yet ordered | `matrix-carrier.kicad_sch`, `matrix-carrier.kicad_pcb`, `layout.yaml`, `carrier_layout.py` |
| F | 2026-11-22 | Every line that passes between two of J2's pads stands evenly in the gap, the same room pad to line, line to line and line to pad (owner, 2026-11-21; issue #52 W1); the two service lines step into place by a small 45 degree jog once they are clear of the band. The three necked lines between pads 1 and 2 were already even. `pcb.py check` passes | `carrier_layout.py`, `matrix-carrier.kicad_pcb` |
| G | 2026-11-22 | `IO39` and `IO40` leave J-MCU-C's pins on one 45 degree line from the pad's centre, with no short level piece first (owner, 2026-11-22: a track leaves a pin on a line through its centre; issue #52). |
