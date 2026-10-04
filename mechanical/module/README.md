# Eurorack module — parametric CAD

The module's panel, its three boards and every part that sets their positions
and depths, as an OpenSCAD model: [`../cad/module.scad`](../cad/module.scad).
The decisions it realises are [ADR 0023](../../docs/decisions/0023-module-ethercon-and-two-boards.md)
(the NE8FAV; the boards - three since its amendment of 2026-10-03, the iso
board behind the main board carrying `U-ISO` and its filter) and [ADR 0024](../../docs/decisions/0024-module-panel-layout-and-stack.md)
(the panel layout and the stack). It goes as far as the line before board
layout: outlines, positions, keep-outs and the cut file, not copper.

**The etherCON is the panel's bottom row** (ADR 0024 point 11, the owner's
instruction of 2026-09-30: *"Power switch should not be underneath the
connector"*). The toggle and the LED are the row above it, so the umbilical's
plug and cable drop below every control. The panel drawing shades that drop
zone, and `drc.echo` holds the rule that keeps controls out of it: *no panel
control under the umbilical: clear of the NE8MX's grip and its cable's drop
zone*, with *the umbilical's plug stands proud of every control* beside it.
Behind the panel, the jack board is a plain rectangle that ends just below
the bottom jack row (ADR 0024 point 15, the owner, 2026-10-01: *"Can we not
rectangle it out up higher?"*), above the toggle's body and the NE8FAV. The
LED is a panel-mount indicator on its own nut, its lead plugged into a
header on the main board's front face (ADR 0024 point 16: the owner,
2026-10-01, *"remove power led light pipe and do a panel mount led with
connector to header"*), and the main board's two low mounting points are spacers from the panel's rear face,
on self-clinching studs.

**The toggle throws left–right, ON to the right** (ADR 0024 point 12, the
owner, 2026-09-30: *"to avoid inadvertent triggering"*). One leaf,
`layout.toggle_on`, turns everything that turns with the switch: the panel
hole's D-flat (on the OFF side, the left — NKK's M2011 is ON with its lever
away from the flat), the lever's sweep and the legends derived from it, the
body's terminal field and lugs, and the main board's wiring keep-out. The panel drawing outlines the sweep and marks ON.

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
| [`../cad/module.scad`](../cad/module.scad) | The model. `part=` selects the assembly, a 2D cut (`panel`, `jack_board`, `main_board`, `iso_board`), the DRC or the PCB geometry |
| `../cad/fig_module_*.scad` | The drawings: the panel, the three boards, the side section |
| `../cad/generated/module-params.scad` | **Generated** from `config/module.yaml` |
| [`drc.echo`](drc.echo) | **Generated.** Every design rule, `PASS`/`FAIL`/`NOTE`/`INFO` with its measured value. Pages cite rules by name |
| [`clash.txt`](clash.txt) | **Generated.** Every named envelope against every other: overlaps, and every pair under its class's minimum gap ([`config/clearance.yaml`](../../config/clearance.yaml)) |
| [`clash-allow.yaml`](clash-allow.yaml) | Interference the design intends (`allow:`) and near-misses it accepts (`near:`), each with its reason |
| `export/panel.dxf` | **Generated.** The panel as it goes to the cutter |
| `export/jack-board.dxf`, `export/main-board.dxf` | **Generated.** The boards' outlines, with the standoff holes |
| [`export/pcb-geometry.echo`](export/pcb-geometry.echo) | **Generated.** Where every board-mounted part is, each face's keep-outs and height limits - the board layout's input, in the body's `pcb-geometry.echo` format |
| [`export/panel-art.echo`](export/panel-art.echo) | **Generated.** Every legend and graphics zone's position, every keep-out on the face, where each part sits - the artwork's and the photographs' input (ADR 0026) |
| `art/` | **Generated** by `tools/panel-art.py`: the print PDF and SVG, the proof, the placement report, the render textures |
| `blender/studio_small_08_1k.hdr` | The photographs' light probe, banked (Poly Haven, CC0) |
| `renders/*.png` | **Generated.** Every image on this page; `photo-*.png` by `tools/render-module.py` |

The clash check and the DRC use **envelopes** from `config/module.yaml`, not
the vendor meshes (`vendor=false`); the meshes are for the pictures. So a
clean clash is only as good as the envelopes, and several are `tbd` — the DRC's
first line lists each one in play.

## The panel's print (ADR 0026)

![The module in a slice of a black case: patched, the umbilical home, the power LED lit](renders/photo-hero.png)

The printed graphics follow Pittsburgh Modular's dark Lifeforms language —
black anodise, three grey islands, a light-grey header pill, white lowercase
Inter, every jack's word knocked out of a light-grey pill (they are all
outputs), no scales but OFFSET's − and + — as an original design
([ADR 0026](../../docs/decisions/0026-module-panel-graphics.md)). Nothing in
it is drawn by hand:

```
config/module.yaml art.*  ──┐
cad/module.scad (part=art) ─┴─> export/panel-art.echo ─┐   every zone's position, every keep-out, every part
export/panel.dxf ──────────────────────────────────────┼─> tools/panel-art.py ─┬─> art/panel-art.pdf   spot inks, to the panel maker
datasheets/fonts/Inter-*.ttf ──────────────────────────┘                        ├─> art/panel-art.svg   the master, Inkscape layers
                                                                                ├─> art/panel-art.png   the proof
                                                                                ├─> art/panel-art-check.txt   every word's zone and air
                                                                                └─> art/tex-*.png ─> tools/render-module.py ─> renders/photo-*.png
```

- `module.scad` derives the islands, the `breath` header pill, the
  OFFSET marks and the name between the top screws from the layout, and `drc.echo` checks each
  (`art:` and `art zone:` rules). The legend zones ADR 0024 already had are
  exported with their positions too.
- `tools/panel-art.py` sets the words and **fails** on any placement rule;
  its report, `art/panel-art-check.txt`, gives every word's ink box, its air
  inside its zone, its distance to a cut and to the nearest keep-out, its
  stem, and each ink pair's contrast. The words themselves are
  `config/module.yaml` `art.text.*` — the knobs read *gain, offset, curve*.
- **To the panel maker**: `export/panel.dxf` (the cut) with
  `art/panel-art.pdf` (UV print, "use white ink" and "underprint white" on).
  A 1:1 paper print of the PDF over a cut template first, then one proof panel.

![The artwork proofed on the anodise, the cuts shown light](art/panel-art.png)

The photographs are Cycles renders of a scripted scene
(`tools/render-module.py`, Blender as a Python module): the panel is
`panel.dxf` extruded, the print is the same textures at
`art.texture.px_mm`, the NE8FAV, the NE8MX and the jacks are the banked
vendor solids, and the knob, the toggle's lever, the nuts, the patch cables
and the case are modelled from `config/module.yaml`. The studio light probe
is Poly Haven's *studio_small_08* (CC0, Sergej Majboroda,
https://polyhaven.com/a/studio_small_08), banked at 1k in `blender/`. Each
render takes tens of minutes on a CPU; `cad.py build` redoes one only when
something it shows moved.

| | |
|---|---|
| ![Straight on, orthographic, no patch cables: the print against the parts](renders/photo-front.png) Straight on — for checking the print against the parts | ![Close-up of the breath knobs and the first outputs' pills](renders/photo-detail.png) The breath knobs, the OFFSET marks, the pitch and breath pills |

## The views

![The panel drawing: cuts, centres, legend zones, the washers' reach along their slots](renders/panel.png)

![The three boards seen from the panel: the jack board a plain rectangle above the toggle and the NE8FAV, the main board with its standoffs (two between the boards, two to the panel, two to the iso board), J-B2B-MOD, J-B2B-ISO, J-LED-PANEL with the LED's nut and its lead's run outlined above it; the iso board's rear face with U-ISO and its filter, its notch round J-PWR-EURO](renders/boards.png)

![Side section through the panel's centre, with every depth and the Palette's limit read both ways](renders/section.png)

| | |
|---|---|
| ![The stack pulled apart](renders/exploded.png) The stack pulled apart | ![From behind](renders/rear.png) From behind: the power header, its socket and the ribbon folded down, the iso board with `U-ISO` (RPA20-2412SAW, ADR 0027) and its filter parts, the trimmers and bulk caps (envelopes) |

## Build order — the stack

The stack can only be soldered in one order, and its depth is set by more
than one part, so neither is left to the builder to discover
(ADR 0024; the depths are `drc.echo`'s, not restated here).

1. **The jack board's own parts first** — jacks and pots. Their joints are
   on the board's rear face, which ends up inside the gap between the boards.
   On the main board, `J-LED-PANEL` is hand-soldered (through-hole).
2. **The panel's own hardware**: the two studs (`MECH-PANEL-STUD-MOD`,
   clinched by the panel vendor); **`LED-PANEL`** from the front, its nut and
   lock washer behind — **mark its anode lead (the dot on the housing's
   back) before cutting the leads** to `led.lead_cut`, then solder
   `CBL-LED-PANEL`'s red wire to the anode, the black to the cathode, and
   sleeve both (*LED-PANEL behind the panel: in front of the main board*);
   and **`SW-POWER`**, one nut on the front and none behind
   (*toggle's lugs in front of the main board*), and its two wires soldered to
   its lugs, long enough to reach the main board.
3. **Offer both boards up to the panel** with every standoff loose and
   `J-B2B-MOD` through both boards, **unsoldered**. Seat the jacks' bushings
   and the NE8FAV's flange against the panel: three things set the gap
   between the boards — the standoffs, the jacks' bodies against the panel
   and the NE8FAV's setback — and each board's thickness tolerance adds to
   it. **Face each standoff to the gap measured here**, not to the nominal
   (*standoff length (derived)*, *standoff faced from stock*), as the key
   boards' spacers are — and each panel spacer to the gap between the
   panel's rear face and the main board with the NE8FAV seated (*panel
   standoff length (derived), faced from stock*): the NE8FAV fixes that gap,
   so a spacer that is off bends the board against the connector.
4. **Take the panel off, stack the boards on the faced standoffs and solder
   `J-B2B-MOD`** — on the jack board's front face first: those joints sit in
   the slot between the jack bodies and cannot be reached once the panel is
   on. Then on the main board's rear face. The header, once soldered, freezes
   the gap.
5. **The iso board** (`PCB-MODULE-ISO`, its parts already on its rear face):
   offer it to the main board's rear on its two spacers
   (`MECH-STANDOFF-ISO`, the stock length uncut: *iso board gap*) with
   `J-B2B-ISO`'s insulator on the main board's rear face and its posts
   through the iso board, screw it home, then solder `J-B2B-ISO` on the iso
   board's rear and on the main board's front. Trim `U-ISO`'s tails and the
   header's ends where a keep-out needs it (*J-B2B-ISO pin length
   (derived)*).
6. **Plug `CBL-LED-PANEL` into `J-LED-PANEL`** (pin 1, the red wire, the
   anode) while the main board is still clear of the panel, and **feed
   `SW-POWER`'s wires** below the jack board's bottom edge and solder
   them to the main board from its rear; fold the LED's lead into the gap
   (*CBL-LED-PANEL's run, LED to header*), then fit the panel (its two spacers
   on their studs), the standoffs' screws and the toggle's nut.
