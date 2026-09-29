# Umbilical adapter — `umb-adapter`

The small board behind the tail cap that carries the instrument's etherCON
(`J-UMBILICAL-INST`, an NE8FAV) and joins it to the main board (ADR 0021). Eight
tracks, each etherCON pin to the same-numbered pin of `J-UMB`, the right-angle
header whose posts are soldered here and tails into the main board's
tongue. Nothing else is on it: the clamps are on the main board at `J-UMB`, and
the connector's G (shield) tab goes nowhere — its housing is plastic, isolated
to panel ground [ds].

> **Status: schematic done, layout not started.** Its outline is the flange's,
> `mechanical/cad/woody_body.scad` "umbilical adapter"; its thickness is
> `config/body.yaml` `boards.umb_adapter_t`.

| File | What it is |
|---|---|
| `umb-adapter.kicad_sch` | **Source.** `J1` (the NE8FAV) and `J2` (the adapter's end of `J-UMB`: the header's posts, a straight 1 × 8 row here). `J2` is the same part as the main board's `J-UMB`, bought and fitted once with the main board, so its `Assembly` is `none` |
| `board-netlist.yaml` | Exported (`tools/kicad.py export hardware/boards/umb-adapter`) |
| `*.sch.png` | Renders, recorded in `hardware/SHEETS.csv` |

The pin map is `interfaces/spi-link`'s, where both ends are netlisted; this
sheet draws the adapter's half of it.

## Open, and what decides each

| Item | Decided by |
|---|---|
| The NE8FAV's footprint (`woody:Neutrik_NE8FAV_etherCON_Vertical`, `hardware/lib/README.md`) is drawn from Neutrik's layout, mirrored because Neutrik draws it from the solder side | The first adapter, with the connector pushed into it before soldering |
| The pairs side by side on the adapter (`spi-link.md`) | Layout |

## Revisions

| Rev | Date | What changed | Where |
|---|---|---|---|
| — | 2026-09-29 | Schematic. Not laid out | git history of this directory |
