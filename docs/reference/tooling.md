# Tooling — installing and using the body CAD, the schematics and the PCB layout

Three pipelines turn data in this repository into pictures and design files.
The third reads the other two:

| Pipeline | Source (edit these) | Tool | Generated (never edit) |
|---|---|---|---|
| **Body CAD** | `config/body.yaml`, `config/key-layout.yaml`, `mechanical/cad/*.scad` | `tools/cad.py` (OpenSCAD) | `mechanical/renders/*.png`, `mechanical/export/*.dxf`, `mechanical/export/pcb-geometry.echo`, `mechanical/drc.echo`, `mechanical/clash.txt`, `mechanical/OUTPUTS.csv`, `mechanical/cad/generated/params.scad` |
| **Schematics** | the KiCad sheets: each circuit's `<circuit>.kicad_sch`, each board's project under `hardware/boards/` (ADR 0019) | `tools/kicad.py` (KiCad 9) | a migrated circuit's `netlist.yaml`, `board-netlist.yaml`, `*.sch.png`, `hardware/SHEETS.csv` |
| **PCB layout** | a board's `<board>.kicad_pcb` and `.kicad_pro` once laid out; before that, its `layout.yaml`; `hardware/lib/woody.pretty/` | `tools/pcb.py` (KiCad 9's `pcbnew`), `tools/pcb_route.py` | `*.pcb-*.png`, `fab/` (Gerbers, drills, placement, the board house's BOM/CPL/hand list), their rows in `hardware/SHEETS.csv` |

All three follow the same rule, the one this repository exists to enforce
(`CLAUDE.md`): **each fact lives in one source, and everything derived from
it is generated and fingerprinted**, so a derived file that no longer
matches its source is reported by name instead of silently lying. For the
body the source is data (`config/body.yaml`); for the electronics it is the
KiCad sheets.

---

## §1. Install

On Ubuntu 24.04, one command, safe to re-run:

```
sudo bash tools/setup-env.sh
```

It installs:

| Package | For |
|---|---|
| `openscad` (2021.01, Ubuntu's) | the body model, renders and DXFs |
| `xvfb` | OpenSCAD renders need a display; `xvfb-run` fakes one on a server |
| `libxft2`, `gmsh` (pip) | meshing the vendor STEP files (the etherCON, the Matrix) |
| `pillow` (pip) | stamping the fingerprint into each render's footer |
| `manifold3d`, `trimesh`, `numpy` (pip) | the clash check: every pair of solids intersected |
| `kicad`, `kicad-symbols` **9.0**, from the KiCad project's own archive | writing, checking and rendering schematic sheets |
| `poppler-utils` | `pdftoppm` renders sheets to PNG; `pdftotext` reads banked datasheets |
| `librsvg2-bin` | `rsvg-convert`: `pcb.py render` turns its SVG copper plots into PNGs |
| `shapely` (pip) | `pcb.py check`'s silkscreen and outline geometry, and the router's clearances |
| three KiCad 3D models (0805 resistor and capacitor, SOIC-16) | `pcb.py render`. The full `kicad-packages3D` library is 3 GB, so the script fetches only these, from the KiCad project's GitLab at tag `9.0.0`, into `/usr/share/kicad/3dmodels/`. The KS-33's model is banked in `datasheets/`, and the chain header has none |

**KiCad must be 9, not Ubuntu's 7.0.** KiCad 7's command line has no ERC, and
the sheets are written in KiCad 9's format. The script adds the KiCad 9 archive
(`ppa:kicad/kicad-9.0-releases`, key fetched from Launchpad) itself. It also
copies KiCad's default symbol-library table into `~/.config/kicad/9.0/`;
without it KiCad's ERC warns that every part's library is "not in the current
configuration".

**In a Claude Code cloud session** the container is rebuilt for every new
session, so anything installed by hand is gone next time. Put
`bash tools/setup-env.sh` in the environment's **setup script** (the cloud
environment menu in the session's title bar → Edit → Setup script) and every
new session starts with both pipelines ready. Without it, run the script at the
start of a session; it takes about three minutes, mostly KiCad.

**On your own machine** you only need KiCad 9 to open the sheets
(`*.kicad_sch` open directly — no project file needed) and OpenSCAD to open
`mechanical/cad/woody_body.scad` interactively. The generated PNGs need
nothing.

---

## §2. The body CAD — `tools/cad.py`

The full reference is [`mechanical/README.md`](../../mechanical/README.md)
(what every file is, how staleness is tracked) and
[`mechanical/DESIGN.md`](../../mechanical/DESIGN.md) (why the body is shaped
the way it is). This is the working summary.

### The loop

1. **Change a number** in `config/body.yaml` — each entry is
   `value` / `status` (`tbd` or `settled`) / `source` (with provenance) /
   `decided_by`. Key positions and counts are `config/key-layout.yaml`.
   **Never type a number into a `.scad` file**; the model reads them from the
   generated `params.scad`.
2. **Build**: `timeout 590 python3 tools/cad.py build`. It regenerates
   `params.scad`, then rebuilds every output whose inputs moved. A full rebuild
   takes 2–5 minutes; the clash check is most of it. To iterate on one thing,
   build just that: `python3 tools/cad.py build drc clash` or
   `python3 tools/cad.py build hero section-long`.
3. **Read the results**:
   - `mechanical/drc.echo` — every design rule as `PASS` / `FAIL` / `NOTE` /
     `INFO` with its measured value. A `FAIL` is a design fault, not a build
     failure. Pages cite rules **by name**, never by value (`CLAUDE.md`).
   - `mechanical/clash.txt` — every pair of named solids that overlap. An
     overlap that is meant (a nut on its bolt) goes in
     `mechanical/clash-allow.yaml` with its reason; a rule nothing matches any
     more is reported, so the list cannot rot.
   - the renders in `mechanical/renders/`, listed in `mechanical/README.md`.
4. **Check before committing**: `python3 tools/cad.py check` (also run by
   `tools/check-staleness.py`) fails on any output that is stale, hand-edited,
   or built by nothing. `python3 tools/cad.py explain <output>` says which input
   moved since it was built.

### Adding things

- **A new render**: add an entry to `mechanical/outputs.yaml` (source file,
  camera, `defines`), usually a `mechanical/cad/fig_*.scad` that includes the
  model. Highlight lists (`highlight`) name solids; an entry ending in `*`
  matches by prefix.
- **A new solid**: wrap it in `P(colour, see_through, "name")` in
  `woody_body.scad`; the name is what `clash.txt` and highlights refer to.
- **A new design rule**: an `echo("DRC", "PASS"|"FAIL", "name", value, "unit
  and meaning")` in the model's `drc` part. Measure what the name claims — a
  cold review found rules that measured the wrong face and passed.

### Traps that have cost time

- **OpenSCAD evaluates top-level variables in file order**; a forward
  reference is silently `undef`. Use a function, or move the definition up.
- **An OpenSCAD WARNING fails the build**, on purpose.
- **Preview drops parts built with `intersection()`/`difference()` behind
  see-through parts**: wrap them in `render()` (the end caps are), and draw
  see-through parts last.
- **Run `cad.py params` before running OpenSCAD by hand**, or you are testing
  yesterday's numbers.

---

## §3. Schematics — KiCad is the source (ADR 0019)

### What is the source

- **A circuit's `<circuit>.kicad_sch` is the source of truth** wherever it
  exists (its title block says `circuit: ...`). It owns every connection and
  each part's identity, as KiCad fields on the symbol:

  | Field | Holds |
  |---|---|
  | `Row` | the BOM row the part buys from (`R-KEY-PU`) |
  | `Pins` | the pin map, `name=number(KiCad's name)`: `SHLD=1(~{PL}) CLK=2(CP) …` |
  | `Pins_source` | the banked datasheet page that proves the map |
  | `Note` | what a builder must know about this part |

  **Ports are hierarchical labels**, with fields `Dir` (in/out/ref),
  `From` / `To` and `Figure`. A label with `Kind = endpoint` is an input a
  board wires up — the register's eight inputs.
- **A board is a KiCad project** under `hardware/boards/<board>/`. Its root
  sheet places circuit sheets as sub-sheets, **once per instance**: a key
  board places the register once and the key network once per key. KiCad
  gives each instance its own references (`R-KEY-PU-RH1`). Change a circuit
  sheet once and every instance on every board follows.
- **Everything else is exported and must not be edited**: a migrated
  circuit's `netlist.yaml` (which `check-netlist.py`, `nets.yaml` and the BOM
  checks keep reading exactly as before), each board's `board-netlist.yaml`
  (its flattened netlist, what a PCB is laid out from), and the PNG renders,
  recorded in `hardware/SHEETS.csv`.
- **Not yet migrated circuits** keep a hand-written `netlist.yaml`. The LED
  strip drive's sheet is still *generated* from its YAML by `tools/sch.py`.

### Commands

```
python3 tools/kicad.py export hardware/cluster/key-register   # sheet -> netlist.yaml
python3 tools/kicad.py export hardware/boards/key-board-rh    # board -> board-netlist.yaml, with KiCad's ERC
python3 tools/kicad.py render hardware/boards/key-board-rh    # a PNG of every page
python3 tools/kicad.py check                                  # everything above, compared with what is committed
```

**`kicad.py check` fails when:**
- a sheet was edited and not re-exported;
- a render's sheet moved, or the PNG itself was edited;
- a render or a `fab/` file exists that no ledger row knows (a stray Gerber is uploaded with the rest);
- a board has an ERC error;
- a board with a layout fails `tools/pcb.py check` (§4);
- a key board's `J-CHAIN` pins are netted differently from the ribbon's other end in `hardware/interfaces/key-chain-loom/netlist.yaml` (pin k on the key board against pin 13 − k on the main board);
- a board's register is wired differently from
  `hardware/cluster/key-marker-and-bits/allocation.yaml`, that file disagrees
  with the table in `key-marker-and-bits.md` §4, or it names a key that is not
  on that cluster in `config/key-layout.yaml`.

It needs KiCad 9, so it is **not** in the commit hook; run it before
committing anything under `hardware/` that touches a sheet, a netlist or the
allocation.

### Editing a circuit or a board

1. Open the board project in KiCad 9 (`hardware/boards/key-board-rh/key-board-rh.kicad_pro`)
   — the sub-sheets open from it — or a circuit's `.kicad_sch` on its own.
   **Edit a replicated circuit from inside a board**, so its instance
   references stay attached; KiCad writes the change to the shared circuit
   file.
2. A new part needs its fields: `Row`, `Pins` (every pin the netlist should
   name, in order), `Pins_source`, `Note`. A new port is a hierarchical label
   with `Dir` and `From`/`To`. **Every net must carry a label** — the export
   refuses an unnamed net with two or more pins.
3. Save, then `kicad.py export` the circuit **and every board that uses it**,
   `kicad.py render` them, and `kicad.py check`.
4. Then run the usual gates (`check-netlist.py --strict`,
   `check-staleness.py`): they read the exported netlists.

A sheet opened alone reports ERC errors for its hierarchical ports — they have
no parent there. **ERC means something on a board**, where every port is
wired; `kicad.py export` of a board runs it.

**What no check can prove: a pin-number map.** A wrong map draws a
consistent, wrong sheet. That is why `Pins` carries KiCad's own name for each
pin wherever the library names it, and `Pins_source` the page that proves it.

### Migrating a circuit that is still YAML

`tools/sch.py` writes a circuit's first sheet from its `netlist.yaml` plus a
`schematic.yaml` (symbol, pin map, placement — `hardware/carrier/led-strip-drive/schematic.yaml`
is one, and the key-board circuits' are in git history) with `hierarchical: true`. Then:
1. `python3 tools/sch.py build <dir>` writes the sheet;
2. `python3 tools/kicad.py export <dir>` to a scratch copy, and compare it
   with the hand-written `netlist.yaml` **part by part and net by net** — the
   migration must change nothing;
3. write the export over `netlist.yaml`, delete `schematic.yaml`, and from
   then on edit the sheet.

### KiCad behaviour learned the hard way

- **Power nets are named after the power symbol's value** (KiCad 8+).
- **A field's justification is read in the rotated symbol's frame**, so on a
  rotated part "left" draws as "right".
- **Library symbols that `extends` another** (KiCad 9's `74AHCT125` extends
  `74LS125`) are flattened into the sheet, as KiCad itself does.
- **Strings in a sheet file cannot contain raw newlines** — `\n` escapes only.
- **A single-pin net is named `unconnected-…`** in KiCad's netlist whatever
  label it carries; the export names a lone no-connect pin after the pin.
- **KiCad 7 has no command-line ERC**, and cannot read these sheets; use 9.

## §4. PCB layout — `tools/pcb.py`

The left-hand key board (`hardware/boards/key-board-lh/`) is **the worked
example**: placed, routed, checked, labelled and made orderable here, from the
same sources as everything else. Its [`README.md`](../../hardware/boards/key-board-lh/README.md)
is the pattern for every board's: what is source, how to order it, how to
assemble and bring it up, what is open.

### Where a layout comes from

| What | From |
|---|---|
| Netlist, footprints, references | the board's KiCad sheets (§3); a part's footprint is its sheet's `Footprint` field |
| Board outline | `mechanical/export/key-board-lh.dxf` — the body CAD's key board |
| Switch, ribbon-connector and corner-mount positions, which way the connector's mouth faces, each mount's hole and keep-out sizes (the nut across its corners, and the spacer or washer, each grown by `hardware.kb_mount_float`), board thickness | `mechanical/export/pcb-geometry.echo` — the body CAD |
| Switch 3D model height | `config/body.yaml` `switch.pcb_below_seat` |
| Each key network's three parts | `layout.yaml` `networks:` — ONE `pattern` for every key, relative to the key's switch in the body CAD: the T's junction `offset`, the `axis` S and P lie along, the side the series resistor sits (`leg`) and the side the capacitor hangs (`c`); `except:` for a key that cannot take it, with its own `at` and the reason. `network_parts` expands it into a T round the key's node, and `add_silk` letters every T the same way. `layout` exits on an `except:` key that names no switch, an `axis` other than x or y, a `leg` or `c` other than ±1, a switch not at 0° without its own `at`, and **a key whose three KEY pads are not the three pads nearest its T's junction**. That is a layout-time test only: after a hand edit, `check` holds the switches where the body CAD puts them, and nothing holds the networks' positions round them |
| Which connections and nets route first | `layout.yaml` `connect_first:` — pad-to-pad connections routed before anything else, each with a `max_mm` that **every `check` holds** (the decoupler's return to the register's ground pin). Then `route_first:` — after the power rail, before the rest: nets whose pads can be reached from one side only (a 1.27 mm header's far row) |
| Everything else's place, and the design rules | `layout.yaml` `parts:` and `rules:` |
| The board house's own limits and the stackup | `layout.yaml` `fab:`. `layout` writes the limits into the board's design rules (the `.kicad_pro`), and the finish, mask and silk colours and copper weight into the stackup, which the Gerber job file reports. **Every `check` compares the board's design settings with `rules:` and `fab:`**, so an edit to either side alone fails |
| The silkscreen | generated by `pcb.py`. Parts side (`add_silk`, mirrored): each key network's parts lettered C/S/P with the key's name, in one fixed arrangement round the T; short names for the rest (`PF`, `CD`, `CB DNP`); test-pad names; `J-CHAIN`'s pin-1 dot and an arrow out of its mouth; a `MOUTH` marker; and `layout.yaml` `silk:`'s title block, which also goes into the PCB's title block. Switch side (`add_top_silk`): the keys' names, `J-CHAIN`'s dot and arrow, `MOUTH`, and the title at `silk:` `top_at`. Each searched label is placed clear of every courtyard, pad and hole and 0.25 mm off every other label; a fixed one that is not clear stops the layout. The library footprints' own silkscreen is adapted to `fab:` (`fit_footprint_silk`: strokes widened to the minimum line, strokes near a pad removed), so KiCad's `lib_footprint_mismatch` test is set to *ignore* |
| Part numbers and how each part is fitted | the sheets' `Manufacturer`, `MPN`, `LCSC`, `Assembly` (machine / hand / none) fields |
| Footprints KiCad lacks | `hardware/lib/woody.pretty/` (`hardware/lib/README.md`) |

### Commands

```
python3 tools/pcb.py layout hardware/boards/key-board-lh   # FIRST layout: place, route, pour, fill (refuses if the board exists; --force)
python3 tools/pcb.py check  hardware/boards/key-board-lh   # DRC + parity + fab limits + the body CAD's outline, thickness and positions
python3 tools/pcb.py render hardware/boards/key-board-lh   # 3D both sides, 2D copper, and fab/ (Gerbers, PTH and NPTH drills, placement, and the JLCPCB BOM, CPL and hand-assembly list)
```

**`layout`** builds in a scratch directory and moves the board and its
`.kicad_pro` in only when both are complete. If a net cannot be routed it
prints which, exits 1, and leaves any existing board as it was.

**`check` fails on**, every line an error:
- any KiCad DRC violation, **warnings included** (the board-house tests such as
  text height and hole-to-hole only ever warn in KiCad), an unrouted
  connection, or a schematic-parity difference;
- a design setting that no longer matches `layout.yaml` `rules:`/`fab:`, or
  **any** DRC test set to *ignore* in the `.kicad_pro` that is not on
  `pcb.py`'s `IGNORE_OK` allowlist, each entry with its reason (an ignored test
  drops out of KiCad's report, so an ignored `unconnected_items` once passed a
  board with a whole net unrouted) — `check_rules`;
- what KiCad's DRC does not test (`check_silk`): a silkscreen line narrower
  than `fab: silk_line_min` (DRC's minimum applies to text only), a filled
  silk shape with no part as wide as that line, text under `fab:`'s height or
  stroke, silk nearer a pad's mask opening than `fab: silk_to_pad` (DRC flags
  only an overlap), silk on a via's copper (a tented via has no mask opening,
  but the ink lands on its tent over an open hole), and silk partly or wholly
  off the board. A pad with no number, such as a mount hole's, is named as
  "H1's hole";
- two tracks of one net meeting on one layer at under 90° — an acid trap,
  which KiCad's DRC has no test for (`check_tracks`). Joins at a shared end
  and a track ending in the middle of another are both tested; a wedge whose
  apex a via or pad of the net fills is not a trap and is exempt;
- a `layout.yaml` `connect_first:` connection with no path in the net's own
  tracks and vias, or a longer one than its `max_mm`; the pour does not count
  (`check_connect_first`);
- the body CAD disagreeing (`check_cad`): the board's thickness against
  `boards.key_board_t` and the echo, its outline against the DXF, each switch's
  position and rotation (on top) and its 3D model's height, each mount hole's
  position, and `J-CHAIN`'s position, the way its mouth faces, and its side
  (the bottom);
- a mount hole that is not NPTH at the body CAD's hole size, or any copper —
  track, via, pour or another part's pad — on either layer within its keep-out
  radius: the larger of the echo's two bearing diameters, halved, plus
  `rules.clearance` (`check_cad`; ADR 0020: what bears on the board there is
  the grounded plate's hardware).

**`render`** refuses a board that fails `check`, and a board naming a 3D
model that is not installed (kicad-cli would render the part as nothing and
say nothing). It makes everything in a scratch directory and swaps it in at
the end, so a failure half-way leaves the old renders and `fab/` as they were.
Plated and unplated holes go in separate drill files
(`<board>-PTH.drl`, `<board>-NPTH.drl`), as JLCPCB takes them.

**Which generated files are not byte-stable.** `layout` is deterministic in
geometry but not in text: two runs give the same tracks, vias, footprints,
silk and fills, but a different `.kicad_pcb` (fresh UUIDs, and KiCad's
footprint order changes), so a no-op re-layout is a whole-file diff and marks
every render and `fab/` file STALE in `hardware/SHEETS.csv` until `render`
runs. `render` rewrites every Gerber and drill file with a new creation
timestamp, and the 3D PNGs can change bytes with nothing changed on the board.
Re-layout only to change the layout, and commit a `render` with it.

**After `layout`, the `.kicad_pcb` is the source**, like the sheets: open the
project in KiCad 9 and move or re-route by hand. `tools/kicad.py check` runs
`pcb.py check` on every board that has a layout, and the renders and `fab/`
files are in `hardware/SHEETS.csv`, so an edited board with stale Gerbers is
reported by name.

### The router, and its limits

`tools/pcb_route.py` is a small two-layer grid router: A* on a 0.2 mm grid per
layer, vias where they fit, every other net's copper, every hole and the board
edge inflated by the clearance. Each layer has a preferred direction (top
along the board, bottom across it) and a turn costs by its angle. The order:
1. **`connect_first:`** pad-to-pad connections, before anything else, the most
   direct path the board allows (a decoupler's return to its IC's ground pin,
   which ground, routed last and round everything, would not give).
2. **The power rail** (`power_nets:`; it visits every network and is the
   widest track, so it takes the straight way).
3. **`route_first:`** nets, in their listed order.
4. The other signals, shortest first. A net that cannot route at all is
   retried after ripping up every net whose tracks cross the box round its
   pads, and kept only if all of them route. Then rip-up and reroute: a net
   that took a real detour is ripped up with the nets crossing its corridor,
   routed first, and the result kept only if the group's total cost fell.
5. **Ground last**, as a net of its own. Ground pins the main ground tree
   cannot reach are still joined to each other, in whatever groups they can
   reach.
6. **Stitching vias** (`stitch_gnd`): a single-layer ground pad gets a via
   beside it into the other plane, placed where the via's stub keeps at least
   90° from every track already leaving the pad. A pad the main ground tree
   reaches goes without a via when no such spot exists; any other pad takes
   the via wherever it fits. So not every single-layer ground pad has one.
7. **`square_joins`**: where two tracks of a net meet at under 90° — at a
   bend, or a branch starting mid-track, which first splits that track — the
   joining track's end moves to the foot of the perpendicular and the join
   becomes a right-angle T, where the moved track keeps its clearance, stays
   off holes and keep-outs and inside the edge clearance. A wedge a via or pad
   of the net fills is left. `check` reports anything it could not square.
8. **`merge_tracks`**: collinear segments of one net and layer are merged, so
   the board carries one track per straight run — never at a via, a third
   track, or inside a pad.
9. A ground pour on both layers, filled in a fresh process.

Along the way: **no via goes in or on any SMD pad**, its own net's included,
because a via in a pad wicks its solder away; **no via goes under silkscreen**
(the legend would print onto a tented hole); a pad stub that would meet its
path at an acute angle is left out, the path already ending inside the pad;
and the mount holes' copper keep-outs (ADR 0020) are obstacles on both layers.
**It proves nothing about itself** — KiCad's DRC and `pcb.py check` do. It is
for simple digital boards like the key boards. **The main board's analog
routing is done by hand** (`docs/reference/pcb-pipeline.md`). The module's
own header docstring still says every single-sided ground pad gets a via;
step 6 is what the code does.

### Learned the hard way

- **KiCad's zone filler crashes Python, silently,** on a board built in the
  same process: the file was never written. Fill in a fresh process after
  saving (`pcb_route.fill_zones`).
- **SWIG iterators hand out copies**: `for m in fp.Models(): m.m_Offset.z = …`
  changes nothing. Index into the list.
- **A stub that is not an obstacle becomes a short**: every piece of copper the
  router adds, however small, must enter its obstacle list. A stub is also a
  straight line off the grid, so it must be checked for clearance before it is
  laid; a stitching via's stub once crossed a signal track.
- **A pour can be cut into islands by tracks.** A ground pin inside a loop of
  signal tracks on both layers gets no ground, and a pin at the board edge can
  get only one thermal spoke. DRC reports both. Room fixes it: on the first,
  smaller outline the left-hand register's place was good to only about
  ±0.1 mm, and on the corner-mount board it is not near either limit.
- **Placement makes the routing tidy, not the router.** The left-hand
  register is turned so its inputs face the key row in the keys' own order;
  the routes then need almost no crossings.
- **KiCad may write an empty global `fp-lib-table`** on first run, and then
  every footprint "is not in the configuration". `tools/setup-env.sh` replaces
  an empty one.
- **3D models**: `kicad-packages3d` is 3 GB, so `tools/setup-env.sh` fetches
  only the three this board takes from it (the 0805 resistor and capacitor,
  and the SOIC-16), from `gitlab.com/kicad/libraries/kicad-packages3D` tag
  `9.0.0`. The KS-33's model is banked in `datasheets/mechanical/` and reached
  through `${KIPRJMOD}`. The chain header's footprint is the repository's own
  (`woody:IDC-Header_2x06_P1.27mm_Samtec_SHF_Horizontal`), so it has no 3D
  model and renders without a body. **A missing model is silent**:
  kicad-cli renders the part as nothing and exits 0, which is why `render`
  checks every model first.
- **KiCad's DRC only warns on several board-house limits** (text height,
  hole to hole, silk at the edge), and does not check silk line width or
  silk to a pad's opening at all. `pcb.py check` counts every warning as a
  failure and checks the silkscreen itself.
- **The design rules live in the `.kicad_pro`, not in `layout.yaml`.** The
  first layout copies them there; after that KiCad reads only the project.
  `check` compares the two, so a limit changed in one place only is caught.
- **Reference text as long as `R-KEY-SER-LH1` cannot be silkscreened on an
  0805**: references go on the fabrication layer, and the silkscreen gets the
  short labels above. The copper-bottom render plots that layer, but its
  references and values overprint each other: it is not an assembly drawing.
- **A plated hole is not an obstacle to its own pad's track.** The router once
  kept every drilled hole clear of every track; at 1.27 mm pitch the keep-away
  ring around a 0.65 mm drill is wider than the pad, and the header's pads
  were sealed off from their own tracks. Plated holes (pads and vias) are now
  kept apart from vias only; their copper keeps other nets away.
- **Rerouting a net with all the others in place cannot improve it** - it
  faces the same obstacles or more. The first rip-up pass did exactly that and
  improved nothing, every run. A real rip-up removes the blockers too.
- **Put the board house's limits in the DRC, not in a README.** Adding JLC's
  0.18 mm minimum ring caught the header's pads (Ø1.0 on 0.65 = 0.175). That
  figure is the page's PTH ring; for vias it asks only a diameter 0.1 mm over
  the hole (0.15 preferred) `[datasheets/fab/JLCPCB-PCB-CAPABILITIES.pdf, "Vias"
  and "PTH annular ring"]`, but KiCad's one annular-width rule applies to both,
  so the vias grew to 0.7 on 0.3 as well - over both figures.
- **KiCad's Python API cannot set the stackup** (finish, mask and silk colour,
  copper weight), and the zone fill re-saves the board: `pcb.py` writes the
  whole stackup into the saved file after the fill (`set_stackup`).
- **A silkscreen label wholly off the board is not a DRC error** - one sat
  outside the edge unreported. `pcb.py` refuses to place one, and `check`
  fails on any silk shape that is partly or wholly off the board.

### Findings the first layout made

- **The ribbon connector was deeper than the body CAD assumed.** The CAD
  then took its envelope from the footprint's size (ADR 0020 point 5). Since
  ADR 0017's amendment `J-CHAIN` is a through-hole 2×6 1.27 mm shrouded
  right-angle IDC header, stand-in Samtec SHF-106-01-L-D-RA, and the CAD's
  envelope is `boards.chain_hdr_*`, from its banked full print. Its source is
  open (none stocked at JLC - the board's README).
- **Nothing held the board.** The first layout had no mounting at all. Now
  the board is a rectangle across the cavity, hung at each corner on an M2
  screw through the plate, its head in a blind pocket in the wood top's
  underside (ADR 0020, Amendment 3; the board README's assembly steps), with NPTH holes and copper keep-outs on both layers under
  the nut and under the spacer and washer.
- **The switch pins barely reached through** a 1.6 mm board. The key boards
  are now `boards.key_board_t`; how much pin that leaves is in
  `docs/reference/ks33-geometry.md` (ADR 0020).

### Where the sheets are

Each render is generated; what it is rendered from is the source.

| Render | Rendered from |
|---|---|
| [`key-board-rh.sch.png`](../../hardware/boards/key-board-rh/key-board-rh.sch.png) (+ one PNG per sub-sheet) | the KiCad project `hardware/boards/key-board-rh/key-board-rh.kicad_sch` (**source**) |
| [`key-board-lh.sch.png`](../../hardware/boards/key-board-lh/key-board-lh.sch.png) (+ pages) | the KiCad project `hardware/boards/key-board-lh/key-board-lh.kicad_sch` (**source**) |
| [`key-register.sch.png`](../../hardware/cluster/key-register/key-register.sch.png), [`key-switch-network.sch.png`](../../hardware/cluster/key-switch-network/key-switch-network.sch.png), [`key-marker-and-bits.sch.png`](../../hardware/cluster/key-marker-and-bits/key-marker-and-bits.sch.png) | each circuit's `.kicad_sch` beside it (**source**) |
| [`led-strip-drive.sch.png`](../../hardware/carrier/led-strip-drive/led-strip-drive.sch.png) | a sheet itself generated from YAML — not yet migrated |

### Not yet

- **The main board, the module and the interfaces** are still YAML; each
  migrates as described above, the main board as a project placing its
  circuit sheets like the key boards do.
- **The BOM fragments** become exports once every board is in KiCad, because
  a row's quantity is a count over all of them (ADR 0019).
- **The right-hand key board's layout**, the same way as the left-hand one
  (§4); its sheets already carry footprints.
- **The commit gate.** `check-staleness.py` runs `cad.py check` but not
  `kicad.py check`, because that needs KiCad installed; run it by hand.
