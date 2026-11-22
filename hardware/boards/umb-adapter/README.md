# Umbilical adapter — `umb-adapter`

The small board behind the tail cap that carries the instrument's etherCON
(`J-UMBILICAL-INST`, an NE8FAV) and joins it to the main board (ADR 0021 and
its amendment of 2026-11-22). Two parts and eight tracks: the etherCON on the
front face, and on the rear face `J-UMB-SKT`, the surface-mount socket that
the main board's `J-UMB` plugs into. Nothing else is on it: the clamps are on
the main board at `J-UMB`, and the connector's G (shield) tab goes nowhere —
its housing is plastic, isolated to panel ground [ds].

> **Status: laid out, `tools/pcb.py check` passes.** The socket's pad
> pattern is checked against its maker's drawing, hand included
> (`interfaces/spi-link/bom.csv`, `J-UMB-SKT`). Its outline is the flange's, `mechanical/cad/woody_body.scad`
> "umbilical adapter"; its thickness is `config/body.yaml`
> `boards.umb_adapter_t`.

| File | What it is |
|---|---|
| `umb-adapter.kicad_sch` | **Source.** `J1` (the NE8FAV) and `J2` (`J-UMB-SKT`) |
| `board-netlist.yaml` | Exported (`tools/kicad.py export hardware/boards/umb-adapter`) |
| `adapter_layout.py` | **The record of the copper**: it places both parts from the body CAD's exports and writes out every track, and its header says why each is where it is. No router runs on this board (ADR 0030) |
| `layout.yaml` | The rules and the board house the board is held to |
| `umb-adapter.kicad_pcb` | The board `adapter_layout.py` writes |
| `*.sch.png` | Renders, recorded in `hardware/SHEETS.csv` |

The pin map is `interfaces/spi-link`'s, where both ends are netlisted: the
etherCON's contact 9 − N is on the socket's pin N, which is why the tracks
run straight on one face with no via.

## What is checked

`python3 tools/pcb.py check hardware/boards/umb-adapter`: KiCad's DRC with
schematic parity and the board house's limits, and against the body CAD
(`tools/pcb_adapter.py`) the outline, the etherCON on its axis, each socket
pad over the main board's `J-UMB` post of the same number and net, and the
adapter's rear face standing `boards.umb_socket_d` behind the main board's
tail end.

## Open, and what decides each

| Item | Decided by |
|---|---|
| The NE8FAV's footprint (`woody:Neutrik_NE8FAV_etherCON_Vertical`, `hardware/lib/README.md`) is drawn from Neutrik's layout, mirrored because Neutrik draws it from the solder side | The first adapter, with the connector pushed into it before soldering |
| `J-UMB-SKT` on its pads: the pattern is one hand's only, and the part's order code names the hand (`interfaces/spi-link/bom.csv`, `J-UMB-SKT`: how to tell it with the part in hand) | The part against the bare board before soldering |

## Revisions

| Rev | Date | What changed | Where |
|---|---|---|---|
| — | 2026-09-29 | Schematic. Not laid out | git history of this directory |
| A | 2026-11-22 | Laid out: the etherCON, `J-UMB-SKT` and eight straight tracks on the rear face | `adapter_layout.py` |
