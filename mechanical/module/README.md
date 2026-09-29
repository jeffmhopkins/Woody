# Eurorack module — parametric CAD

The module's panel, its two boards and every part that sets their positions
and depths, as an OpenSCAD model: [`../cad/module.scad`](../cad/module.scad).
The decisions it realises are [ADR 0023](../../docs/decisions/0023-module-ethercon-and-two-boards.md)
(the NE8FAV, two boards) and [ADR 0024](../../docs/decisions/0024-module-panel-layout-and-stack.md)
(the panel layout and the stack). It goes as far as the line before board
layout: outlines, positions, keep-outs and the cut file, not copper.

![The module, three-quarter front](renders/hero.png)

## The one rule, as for the body

**Change `config/module.yaml`, run the build, commit what it produced.** Never
type a number into a `.scad` file, and never touch a file under `renders/`,
`export/` or the generated parameters. The NE8FAV's numbers are not in
`config/module.yaml` at all: its leaves say `ref: config/body.yaml:ethercon.*`
and `tools/cad.py` copies them, so the connector is dimensioned once for both
ends. A leaf that names a register figure (`figure: panel-width`) fails the
build if the figure moves.

```
config/module.yaml ──┐  (+ config/body.yaml ethercon.*, config/figures.yaml)
                     └─> cad/generated/module-params.scad ─> cad/module.scad ─┬─> module/renders/*.png   (stamped)
datasheets/… (STEP) ─> cad/vendor/{ne8fav,pj398sm,r0904n}.stl ────────────────┤─> module/export/*.dxf    (cut files)
                                                                               ├─> module/drc.echo        (design rules)
                                                                               └─> module/clash.txt       (interference)
                                        every arrow fingerprinted in module/OUTPUTS.csv
```

```
python3 tools/cad.py build                       # everything stale, body and module
python3 tools/cad.py build module-drc module-clash
python3 tools/cad.py check
```

The module is **a separate model with its own spec and ledger**
([`outputs.yaml`](outputs.yaml), `OUTPUTS.csv`), built by the same tool as the
body (`mechanical/README.md` says how staleness is tracked). A change to the
body never marks a module picture stale, nor the reverse.

## What is here

| Path | What it is |
|---|---|
| [`../cad/module.scad`](../cad/module.scad) | The model. `part=` selects the assembly, a 2D cut (`panel`, `jack_board`, `main_board`), the DRC or the PCB geometry |
| `../cad/fig_module_*.scad` | The drawings: the panel, both boards, the side section |
| `../cad/generated/module-params.scad` | **Generated** from `config/module.yaml` |
| [`drc.echo`](drc.echo) | **Generated.** Every design rule, `PASS`/`FAIL`/`NOTE`/`INFO` with its measured value. Pages cite rules by name |
| [`clash.txt`](clash.txt) | **Generated.** Every named envelope against every other |
| [`clash-allow.yaml`](clash-allow.yaml) | Interference the design intends, each with its reason (none yet) |
| `export/panel.dxf` | **Generated.** The panel as it goes to the cutter |
| `export/jack-board.dxf`, `export/main-board.dxf` | **Generated.** The boards' outlines, with the standoff holes |
| [`export/pcb-geometry.echo`](export/pcb-geometry.echo) | **Generated.** Where every board-mounted part is, each face's keep-outs and height limits - the board layout's input, in the body's `pcb-geometry.echo` format |
| `renders/*.png` | **Generated.** Every image on this page |

The clash check and the DRC use **envelopes** from `config/module.yaml`, not
the vendor meshes (`vendor=false`); the meshes are for the pictures. So a
clean clash is only as good as the envelopes, and several are `tbd` — the DRC's
first line lists each one in play.

## The views

![The panel drawing: cuts, centres, legend zones, the washers' reach along their slots](renders/panel.png)

![Both boards seen from the panel: the jack board's notch, the standoffs, J-B2B-MOD, the parts on each face](renders/boards.png)

![Side section through the panel's centre, with every depth and the Palette's limit read both ways](renders/section.png)

| | |
|---|---|
| ![The stack pulled apart](renders/exploded.png) The stack pulled apart | ![From behind](renders/rear.png) From behind: the power header, its socket and the ribbon folded down, the trimmers and bulk caps (envelopes) |
