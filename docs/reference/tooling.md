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
| `ngspice` (the distribution's; the version every `results.yaml` was made with is in `tools/toolchain.yaml`) | `sim.py`: every circuit's SPICE simulation (§5) |
| the KiCad 3D models the boards' footprints name (the script's `models` list) | `pcb.py render`. The full `kicad-packages3D` library is 3 GB, so the script fetches only these, from the KiCad project's GitLab at tag `9.0.0`, into `/usr/share/kicad/3dmodels/`. The KS-33's model is banked in `datasheets/`, and the chain header has none |

**Versions are pinned, and checked.** `tools/toolchain.yaml` names the KiCad,
ngspice and OpenSCAD the committed outputs were made with, and
`tools/requirements.txt` the Python packages. The script installs those,
never adds the Ubuntu KiCad archive on another distribution (it says what to
install instead), and ends with a `WARNING` line for every tool that differs;
`tools/commit-gate.py` repeats the warning on every commit made with one. A
different version is a reason to look, not a failure: on KiCad 9.0.2 the
netlists and DRC agreed with 9.0.9 but a loaded board carried no courtyards,
which silently emptied the main board's height check (issue #9, G2; the checks
now build them). Java is not installed: only `route: freerouting` needs it, and
no board uses it now.

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
     **It also lists the near-misses** (issue #34): the minimum distance of
     every pair that comes within reach, each pair sorted into a class in
     `config/clearance.yaml` whose minimum gap carries its provenance (the
     tolerances it adds up). A pair under its class's minimum is
     `UNDER MINIMUM` unless a `near:` rule in the clash-allow file names it
     with its reason; every pair under the file's `report` threshold is
     listed with where it is. The per-solid meshes are cached under
     `~/.cache/woody/clash-solids/`, keyed by what they are built from, so a
     change to the clearance rules alone re-measures without re-rendering.
   - the renders in `mechanical/renders/`, listed in `mechanical/README.md`.
4. **Check before committing**: `python3 tools/cad.py check` (also run by
   `tools/check-staleness.py`) fails on any output that is stale, hand-edited,
   or built by nothing - and on an unexcused `CLASH` or `UNDER MINIMUM` line
   in either model's `clash.txt`. `python3 tools/cad.py explain <output>` says which input
   moved since it was built.

**The Eurorack module is a second model in the same pipeline**:
`config/module.yaml` → `mechanical/cad/module.scad`, with its own spec
(`mechanical/module/outputs.yaml`), ledger (`mechanical/module/OUTPUTS.csv`),
`drc.echo` and `clash.txt` under `mechanical/module/`
([`mechanical/module/README.md`](../../mechanical/module/README.md)). One
`build` or `check` covers both. A module config leaf may say
`ref: config/body.yaml:<path>` instead of a value — the NE8FAV is dimensioned
once for both ends — or `figure: <id>`, which fails the build when that
register figure no longer contains the number.

**Outputs a Python tool makes** are `scripts:` entries in a spec: the tool,
its arguments and **every file it reads** (`inputs`). cad.py runs it with
`--out <file> --fingerprint <fp>`; the tool prints `READ: <path>` for each
file it opens, and the build fails if one is not in `inputs` — the check
OpenSCAD's depfile gets. Two tools use it, both for the module (ADR 0026):

- **`tools/panel-art.py`** — the panel's printed artwork. Reads
  `config/module.yaml` `art.*`, the zones `module.scad` exports to
  `mechanical/module/export/panel-art.echo`, the cut `panel.dxf` and the
  banked Inter TTFs; writes, by `--out`'s name, the SVG master (layers CUT,
  UNDERBASE, SLATE, BAR, WHITE), the spot-colour PDF, the proof PNG, the
  placement report and the render textures, all under
  `mechanical/module/art/`. It **fails and writes nothing** on any placement
  rule (its docstring lists them). `python3 tools/panel-art.py --check` runs
  the rules and prints the report without writing — the loop for editing
  a word or a size. Needs fontTools, shapely, ezdxf and `rsvg-convert`.
- **`tools/render-module.py`** — the module's photographs, Cycles on the
  CPU through `bpy` (Blender 5 as a Python module; `import bpy` under plain
  `python3`). `--view hero|front|detail`. Each takes **tens of minutes** at
  full size, so background `cad.py build` when they are stale. To iterate on
  the scene, render into the scratchpad, never into `renders/`:
  `python3 tools/render-module.py --view hero --percent 25 --samples 32 --out /tmp/…/hero.png`
  (`--blend <file> --no-render` saves the scene to open in Blender).

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
- **Every circuit with a netlist is migrated** (the module's on
  2026-09-30). A circuit whose parts sit on two boards is a parent sheet
  placing two pages, `<circuit>.main.kicad_sch` and `<circuit>.jack.kicad_sch`
  (or `.iso.kicad_sch`, power-entry's iso-board page), and each board places
  its own page.

### Commands

```
python3 tools/kicad.py export hardware/cluster/key-register   # sheet -> netlist.yaml
python3 tools/kicad.py export hardware/boards/key-board-rh    # board -> board-netlist.yaml, with KiCad's ERC
python3 tools/kicad.py render hardware/boards/key-board-rh    # a PNG of every page
python3 tools/kicad.py check                                  # everything above, compared with what is committed
python3 tools/kicad.py check --board key-board-lh             # the same, scoped to one board: its order sheet's gate
```

**`--board <name>`** checks that board's export, ERC, layout (`pcb.py check`)
and renders, and the circuit sheets it places with their renders; the
cross-board checks below still read every board's netlist, because a
connector is only right if it matches its peer. Another board's layout, ERC
and renders are left out, so a board under work does not block an order of a
finished one (review #6-3). The commit gate still runs the full check.

**`kicad.py check` fails when:**
- a sheet was edited and not re-exported;
- a render's sheet moved, or the PNG itself was edited;
- a render or a `fab/` file exists that no ledger row knows (a stray Gerber is uploaded with the rest);
- a board has an ERC error;
- a board with a layout fails `tools/pcb.py check` (§4);
- `J-B2B-MOD` or `J-B2B-ISO`, each soldered through two module boards, is
  netted differently on the two (`module-main` and `module-jack`,
  `module-main` and `module-iso`; pin *k* is one conductor on both);
- a board's umbilical connector is wired differently from its part in
  `hardware/interfaces/spi-link/netlist.yaml`: the main board's and the
  adapter's `J-UMB` against `J-UMB`, the adapter's etherCON against
  `J-UMB-INST`, the module main board's against `J-UMB-MOD`;
- a key board's `J-CHAIN` pins are netted differently from the ribbon's other end in `hardware/interfaces/key-chain-loom/netlist.yaml` (pin k on the key board against pin 13 − k on the main board);
- a board's register is wired differently from
  `hardware/cluster/key-marker-and-bits/allocation.yaml`, that file disagrees
  with the table in `key-marker-and-bits.md` §4, or it names a key that is not
  on that cluster in `config/key-layout.yaml`.

It needs KiCad 9 and takes about a minute, so the commit gate
(`tools/commit-gate.py`, *The commit gate* below) runs it only when the commit
can touch a KiCad input, and says `kicad: SKIPPED` with the reason otherwise.
Run it by hand whenever that reason is wrong.

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
`schematic.yaml` (symbol, pin map, placement — the key-board and main-board
circuits' are in git history) with `hierarchical: true`. Then:
1. `python3 tools/sch.py build <dir>` writes the sheet;
2. `python3 tools/kicad.py export <dir>` to a scratch copy, and compare it
   with the hand-written `netlist.yaml` **part by part and net by net** — the
   migration must change nothing;
3. write the export over `netlist.yaml`, delete `schematic.yaml`, and from
   then on edit the sheet.

What the export can carry beyond one port per net (added with the interfaces,
2026-09-29):
- **A net carrying two ports, or ports and no pin.** Examples are a key-chain
  hop, where one register's `QH` is the next one's `SER`, and a port joined to
  a port by a trace. Draw it as one wire between the two port labels, and name
  the net with a **local** label on the wire, at a vertex (`labels:` entry
  with `local: true`). A local label outranks a hierarchical one in KiCad's
  naming. `kicad.py` reads which ports sit on the net off the sheet's wires
  (`label_groups`), because KiCad's netlist names one label and lists only
  pins. A net of two ports and no local label is refused.
- **A spare pin whose net has a name of its own** (`TVS_CHAIN_SPARE`) keeps
  the name as a label. A lone labelled pin with no port is exported as an
  external endpoint.
- **Parts the page's drawing shows and another circuit owns** (`foreign:` in
  the netlist): one line of sheet text each,
  `FOREIGN <label>: owner <circuit>, row <BOM row>`.
- **A package's N/C leads** (the library types them `no_connect`) that the
  part's `Pins` field does not name are on no net, as in the hand-written
  netlist.

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
| Switch, ribbon-connector and corner-mount positions, which way the connector's mouth faces, each mount's hole and keep-out sizes (the nut across its corners, and the spacer, each grown by `hardware.kb_mount_float`), board thickness | `mechanical/export/pcb-geometry.echo` — the body CAD |
| Switch 3D model height | `config/body.yaml` `switch.pcb_below_seat` |
| Each key network's three parts | `layout.yaml` `networks:` — ONE `pattern` for every key, relative to the key's switch in the body CAD: the T's junction `offset`, the `axis` S and P lie along, the side the series resistor sits (`leg`) and the side the capacitor hangs (`c`); `except:` for a key that cannot take it, with its own `at` and the reason. `network_parts` expands it into a T round the key's node, finding each key's three parts by BOM row (`Row`) and the sheet they sit on (LH1..LH5) - references are plain numbers - and `add_silk` labels every T the same way. `layout` exits on an `except:` key that names no switch, an `axis` other than x or y, a `leg` or `c` other than ±1, a switch not at 0° without its own `at`, and **a key whose three KEY pads are not the three pads nearest its T's junction**. That is a layout-time test only: after a hand edit, `check` holds the switches where the body CAD puts them, and nothing holds the networks' positions round them |
| Which connections and nets route first | `layout.yaml` `connect_first:` — pad-to-pad connections routed before anything else, each with a `max_mm` that **every `check` holds** (the decoupler's return to the register's ground pin). Then `route_first:` — after the power rail, before the rest: nets whose pads can be reached from one side only (a 1.27 mm header's far row) |
| Everything else's place, and the design rules | `layout.yaml` `parts:` and `rules:` |
| The board house's own limits and the stackup | `layout.yaml` `fab:`. `layout` writes the limits into the board's design rules (the `.kicad_pro`), and the finish, mask and silk colours and copper weight into the stackup, which the Gerber job file reports. **Every `check` compares the board's design settings with `rules:` and `fab:`**, so an edit to either side alone fails |
| The silkscreen | generated by `pcb.py`. References are plain numbers (R1, C6, U1: owner, 2026-09-28), and every part's is printed beside it. Parts side (`add_silk`, mirrored): each key network's three references in one fixed arrangement round the T (the resistors' reading along them), with the key's name; everything else's reference (`DNP` after one not fitted); the test pads' references, and a legend of what each probes (their `Probe` field) at `silk:` `legend_at`; J1's pin-1 dot and an arrow out of its mouth; a `MOUTH` marker; and `layout.yaml` `silk:`'s title block, which also goes into the PCB's title block. Switch side (`add_top_silk`): each switch's reference and key (`SW1 LH1`), J1's reference, dot and arrow, `MOUTH`, and the title at `silk:` `top_at`. Every label is sized by its real width in KiCad's font (`text_w`; a per-character guess ran 15-35 % short, and labels checked as clear printed touching), placed clear of every courtyard, pad and hole and 0.25 mm off every other label, reading along the part where across it does not fit; a fixed one that is not clear stops the layout, naming what is in the way. The library footprints' own silkscreen is adapted to `fab:` (`fit_footprint_silk`: strokes widened to the minimum line, strokes near a pad removed), so KiCad's `lib_footprint_mismatch` test is set to *ignore* |
| Part numbers and how each part is fitted | the sheets' `Manufacturer`, `MPN`, `LCSC`, `Assembly` (machine / hand / none) fields |
| Footprints KiCad lacks | `hardware/lib/woody.pretty/` (`hardware/lib/README.md`) |

### Commands

```
python3 tools/pcb.py layout hardware/boards/key-board-lh   # FIRST layout: place, route, pour, fill (refuses if the board exists; --force)
python3 tools/pcb.py check  hardware/boards/key-board-lh   # DRC + parity + fab limits + the body CAD's outline, thickness and positions
python3 tools/pcb.py render hardware/boards/key-board-lh   # 3D both sides, 2D copper, and fab/ (Gerbers, PTH and NPTH drills, placement, and the JLCPCB BOM, CPL and hand-assembly list, with its Fit column)
```

**The hand-assembly list's Fit column.** A board whose `layout.yaml` has
`hand_trim:` (a hand part's reference, `max:` a sum or difference of
`config/body.yaml` figures by name, and `why:`) gets a Fit column: each listed
part's tails, with their solder, cut to at most that length below the board,
the arithmetic in the cell. The layout and `config/body.yaml` then become
inputs of that board's renders, so the length goes stale with its figures. The
main board's is #8-11 (ADR 0017, *Amendment, 2026-10-04*). A symbol's own `Fit` field (how to fit
the part by hand - solder order, tip, what to mask; the main board's `U10`,
#34) goes in the same column; a part with both gets them joined by "; ", and a
board where no hand part has either keeps four columns.

**3D models for `woody` footprints** whose maker's STEP could not be had are
drawn from the banked drawings by `python3 tools/lib-models.py` into
`hardware/lib/woody.3dshapes/` (`--check` to verify); each is built in its
footprint's frame, so the footprint places it at offset 0. `hardware/lib/README.md`
says which footprint has which model and where it came from.

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
- a placed silkscreen mark (a label, dot or arrow) under any part's body - its
  courtyard, on the same side - where it cannot be read with the part fitted;
- two tracks of one net meeting on one layer at under 90° — an acid trap,
  which KiCad's DRC has no test for (`check_tracks`). Joins at a shared end
  and a track ending in the middle of another are both tested; a wedge whose
  apex a via or pad of the net fills is not a trap and is exempt;
- a board with a `layout.yaml` `silk:` block whose title block (title,
  revision, date - the Gerber job's "Revision") differs from it, or whose
  silkscreen lacks the title or its `rev <rev>  <date>` line (`check_title`;
  #33: the main board lost all three in a hand-drawn pass and every check
  passed);
- a hand-soldered part with no iron room (`check_iron`, #34): layout.yaml
  `iron_room:` `rules:` - each `{rows, min}` - holds every such part's pads on
  the face it is soldered on (a through-hole part's far face), grown 0.25 as a
  courtyard is, `min` mm from every other part's courtyard on that face;
  `except:` names a pair that cannot have it, with its reason, and an
  exception no longer needed fails as well;
- a `layout.yaml` `pairs:` entry with a `guard:` whose legs (the pair's
  locked tracks and arcs of its width, on its layer) have any other net's
  track or via - the pair's own nets and its guard net aside - nearer than the
  clearance plus the guard, edge to edge (`check_pair_guard`, #8-4: the router
  keeps it, and until #33 nothing held the board to it after a hand edit);
- a `layout.yaml` `connect_first:` connection with no path in the net's own
  tracks and vias, or a longer one than its `max_mm`; the pour does not count
  (`check_connect_first`);
- the body CAD disagreeing (`check_cad`): the board's thickness against
  `boards.key_board_t` and the echo, its outline against the DXF, each switch's
  position and rotation (on top) and its 3D model's height, each mount hole's
  position, and `J-CHAIN`'s position, the way its mouth faces, and its side
  (the bottom);
- a part on the key board's switch side, which is pressed against the switch
  housings, or one underneath taller than the echo's `smt_height_max`, J-CHAIN
  excepted (`check_key_faces`, issue #19 F2; heights from `layout.yaml`
  `heights:`, and a board without one gets a note that they were not checked);
- a mount hole that is not NPTH at the body CAD's hole size, or any copper —
  track, via, pour or another part's pad — on either layer within its keep-out
  radius: the larger of the echo's two bearing diameters, halved, plus
  `rules.clearance` (`check_cad`; ADR 0020: what bears on the board there is
  the grounded plate's hardware);
- a body CAD export the board is checked against (its outline DXF,
  `pcb-geometry.echo`) that `tools/cad.py`'s ledger calls stale, edited or
  unbuilt (`cad_export_problems`): against a stale export, the checks above
  compare the board with a body that may no longer exist;
- a machine-placed part with polarity (a `D`, `Q`, `U` or `LED` reference, an
  electrolytic) or more than two pads whose LCSC number has no row in
  `hardware/lib/jlc-rotation.csv` (`jlc_rotation_problems`): at offset 0 JLC
  fits a SOIC turned 90° and a SOT-23 180° from KiCad's. A row is proved from
  JLC's own EasyEDA footprint, banked in `datasheets/`, **by pin function, not
  pad number**: JLC's SS34 footprint numbers its anode 1 where KiCad's diode
  numbers its cathode 1. A two-pad passive with no row only warns, at `render`.

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

### The routing policy — quality first, one direction per layer only where needed

**The owner, 2026-10-03:** *"I think maybe the horizontal vertical should only
be used when required, and maybe even just in portions or sections of the
board that is necessary"*, after the module iso board's first, autorouted
layout (*"the strict vertical/horizontal routing is completely unnecessary"*).
So, on every board:

1. **The default is quality routing**: short, direct paths; 45° bends; power
   traces or zones sized for their current; ground and return pours; few vias.
2. **A preferred direction per layer is optional and regional.**
   `layout.yaml` `directions:` takes `regions:` — each a `rect: [x0, y0, x1,
   y1]` in the board's frame (mm), a `name`, a `why`, and the `layers:` it
   directs — and routes free everywhere else. Use one only where congestion
   needs it (a dense bus crossing), and say why in the board's README.
   `directions: layers:` (no region) still directs a layer over the whole
   board, which the controller's boards were laid out with; their re-layout
   follows the rule above. `routed:` lists the layers the router uses
   (layer 3 of a four-layer board when it is a routing layer), `via_cost:` what
   a via costs against a grid step (12 by default).
3. **A power board may be drawn by hand**: the module's iso board is placed in
   current-flow order and its copper - pours per region on both faces,
   stitched, and straight supply runs with 45° bends - is drawn in its
   `.kicad_pcb`, which is the source once it exists (`layout.yaml` `route:
   false`). `pcb.py check` holds it like any other board.
4. **Route in families, in order** (issue #41). **The owner, 2026-10-05:**
   *"we should do families of traces... then do those and then do the next
   ones then do the next ones instead of just letting the auto router go
   Willy-nilly"*. So a board routed by the autorouter is routed family by
   family - power and rails, then sensitive analog with its guard and return,
   then buses as bundles, then the rest - each family finished and fixed
   before the next, not every net in one shortest-first queue where the early
   nets box in the late ones. The mechanism is `layout.yaml` `families:`
   (*The router: families*, below); the method is the `pcb-routing` skill
   (`.claude/skills/pcb-routing/SKILL.md`).

### The router, and its limits

`tools/pcb_route.py` is a small two-layer grid router: A* on a 0.2 mm grid per
layer, vias where they fit, every other net's copper, every hole and the board
edge inflated by the clearance. A layer may have a preferred direction -
over the board, or only in `directions: regions:` (*The routing policy*,
above) - and a turn costs by its angle. The order:
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
for simple digital boards like the key boards; the main board uses its fanout,
pair and moat pieces and `complete` for the rest (*The main board*, below).

### The main board — `kind: main` (`tools/pcb_main.py`)

A board whose `layout.yaml` says `kind: main` is built by `tools/pcb_main.py`
and checked by the same `pcb.py check`, with more. The key boards' own path is
unchanged: their `layout.yaml` names no kind.

| What | From |
|---|---|
| Outline | `mechanical/export/main-board.dxf` less each mount's hole (the mount's footprint drills it); the U-bolt legs' holes and the sensor slot stay in Edge.Cuts, routed and unplated |
| Thumb switches | `pcb-geometry.echo` `main` `switch`, on the **underside**: seen from above a switch hanging face down is the key-board footprint mirrored about the body's x axis, then turned by the CAD's rotation; the KiCad rotation that puts pins 1 and 2 there is found, not assumed. Model height `switch.thumb_pcb_below_seat` |
| Both `J-CHAIN` | `main` `chain`, on the top (`place_chain(..., bottom=False)`); each is the header whose pin 10 is its own side's chain 3V3 |
| `J-MCU`, `J-UMB` | `main` `connector` and `layout.yaml` `connectors:` — the pad row farthest from the mouth at a stated offset from the insulator's face, a figure of each footprint (`hardware/lib/README.md`): re-check it when a footprint changes, and `check` fails the row if it moved |
| `U-BREATH` | `main` `part`, its pads centred there, turned by `cad_parts:` |
| The LED row | `main` `led`, LED *n* the *n*th along the data chain (found from the netlist: DI of the first is the one net no LED drives); each `C-LED` at `led_caps:` offset |
| Mounts | `main` `standoff`, **every one plated on `PWR_GND`** (`mounts:`), on the top face so their courtyard keeps parts off the standoff or nut; rule areas keep every track and via off what bears on each face |
| U-bolt legs | `main` `ubolt`: outer-layer rule areas round the washer and nut above and the spacer below, grown by `ubolt: copper_keepout`; the planes run past |
| Keep-outs | `keepouts:` — the chain ribbons' plug and fold, and the regulator block, as footprint rule areas (their own parts cut out); heights by `heights:` against the echo's rooms (`check_heights`) |
| Key networks | the key boards' T (`networks:`, with `t_parts`), on the top face; `spare:` places the T of a position with no switch |
| Parts the board does not carry | `not_on_board:`, each with its reason; `check` prints them as notes, and any other missing footprint is still an error |
| Layers and stackup | `layers: 4`, `stackup:` (the board house's named stack, banked); plane layers are set to KiCad's *power* type |
| Planes, islands | `planes:` (a zone per layer and net), `islands:` (an island zone over a polygon, cut out of its plane with a `moat`, one `tie`, a `tie_window`, the pads allowed `off_island`) |
| Net classes | `net_classes:`, written into the `.kicad_pro` with a pattern per net. A class may also say where its nets route (`pcb_route.complete`): `layers:` the only outer layers they may use, `layer_cost:` how many times a step on a layer costs (the main board's analog nets kept over the island on layer 1, layer 4 only where nothing else gets through; its power tracks the same way), or `via: [diameter, drill]` the size of the vias its nets take (the main board's power tracks: one 1.0 / 0.6 via where they must change layers, not the signals' 0.3 drill, #8-6) |
| More than one plane via | `fanout_count:` - a pad's plane transition by that many vias, each on its own stub (a power part's drain or return) |
| A guarded pair | `pairs:` `guard:` - every other net's copper the router lays kept that much further off the pair's legs than the clearance (the breath pair beside clock lines: 3W) |
| Parts allowed underneath | `underside_rows:` - the BOM rows that may sit on the underside (the thumb switches); `check` fails any other part there |

**Routing (`route: astar`, the main board's; or `route: freerouting`).** In
this order (step 4 is Freerouting's only):
1. **`pairs:`** — `pcb_route.route_pair`: two nets side by side on one layer,
   routed as one fat track (two widths and the gap) by A* through the `through:`
   points, then split into two offset legs, each leg joined to its own pads by a
   single track of its net. Locked.
2. **`fanout:`** — `pcb_route.fanout`: every SMD pad of a plane net gets its own
   via into its plane on a short straight stub, the nearest legal spot, the via
   inside its plane's region (an island's via on the island, a `PWR_GND` via off
   the island and its moat). Through-hole pads meet the plane themselves. Locked.
3. **`moat_keepout`** — a rule area over each moat on the layer above it, but for
   the tie's window and where a pair crosses.
4. **Freerouting**, `route: freerouting` only (`tools/pcb_freeroute.py`, v2.1.0, the last release on Java
   21; `tools/setup-env.sh` fetches it and the tool checks its SHA-256): KiCad's
   own Specctra DSN export, Freerouting headless, KiCad's own SES import. The
   planes go as planes and the power layers as *power*, so only layers 1 and 4
   are routed; locked copper goes as fixed wiring. On the exported copy only: a
   rule area that keeps out only footprints is taken off (KiCad exports it as a
   routing keep-out), and a keep-out band as wide as the edge clearance goes
   inside every edge (the DSN has no copper-to-edge rule). Bounded by
   Freerouting's own `--router.job_timeout` (20 min), which still writes the
   session; its pass limit is not honoured in batch, and a shell timeout's kill
   writes nothing. Its costs are its defaults: a flatter direction cost and
   cheaper vias were tried on the first layout and left more unrouted; it takes
   no layer direction in batch (step 5).
5. Zones filled, then `pcb.post_route`: `pcb_route.tidy` (doubled, zero-length
   and dangling tracks removed, and a via met on one face only; acute joins squared, collinear runs merged, as on a key
   board; and with `directions: chamfer`, each right-angle corner cut to two
   45-degree bends where the diagonal keeps its clearance); **`pcb_route.complete`**
   - every connection KiCad's DRC still counts missing (under `route: astar`,
   every signal connection; with `families:`, family by family - *The router:
   families*, below), shortest first, routed by A* on both outer layers at once on the lazy 0.2 mm
   grid, a step against its layer's `directions:` costing `against_cost`, a via
   wherever `Obstacles.via_ok` allows, from one item and then, if that search
   is boxed in, from the other. With `rip_up: n`, a connection with no way
   through is searched again through other nets' unlocked routing at a cost per
   cell, the nets that path crosses are taken up whole and queued again pad to
   pad, each at most n times.
   **Why not Freerouting for the main board** (2026-10-01): its batch run takes
   no direction - the same layer use at every `default_undesired_direction_trace_cost`
   tried (2.5 to 50) and with the DSN's layers reordered, and a DSN
   `autoroute_settings` scope zeroes its pass settings (pass 1 in 0.03 s, no
   wiring); it laid layer 4 along the board and layer 1 every way, the preview
   the owner called sloppy. What it cannot route goes to **`pcb.rescue`**, a rip-up: round each
   end of the missing connection (and, for a hop under 10 mm, the ground
   between) the unlocked tracks and vias of other nets are taken up at 1.5, 3
   and 5 mm, never a plane net's or locked copper; the missing connection is
   routed first and the nets taken up are routed again (`complete`), and the
   result is kept only when KiCad's DRC counts fewer problems, unconnected and
   violations together, than before. Then the silkscreen, clear of every via,
   and any stroke of a footprint's own silk on a via removed and named.
6. Zones filled again, stackup written, as for a key board. Whatever is still
   unconnected is printed by name; the board is written anyway, and `check`
   fails on each connection until it is routed by hand.

`layout --no-route` builds and places only (a cheap re-run after a footprint
changes). **`pcb.py finish <board>`** runs the tidy, `complete` and `rescue`
again on the board as it stands, in place, and prints what is still missing:
for after a hand edit, or to try again without a whole layout. It never adds
or moves a part. On a `kind: main` or `module` board it then writes the
silkscreen again (`add_silk_generic`, `silk_off_vias`): every label clear of
the vias as they now stand, and the title block and silk title from `silk:`. A whole layout of the main board takes one to two hours under
`route: astar`, most of it `complete`'s rip-up; a `finish` twenty minutes to an
hour. **`pcb.py update-footprints <board> <ref or footprint>...`** replaces placed
footprints with the library's current ones in the same place, side and turn,
keeping reference, value, sheet path and pad nets (KiCad's "update footprint
from library"), and refuses one whose pads moved.

**`check` adds** for a main board (`pcb_main.check_cad`, `check_heights`,
`check_planes`): every switch underside with its pins where the body CAD's
mirrored switch has them; each chain header, connector, the sensor and each LED
where the echo puts it; each mount plated on its net with no other net's
copper under its hardware on either face; no copper of any net inside a U-bolt
leg's outer-layer keep-out; every top part inside its height room - **every
echo keep-out that carries a height** (under the key boards, the Matrix ribbon,
the USB-C receptacle and its lead; issue #19 F2: only the first two used to be
read) - measured
by its courtyard, which `check` builds itself (a board loaded on KiCad 9.0.2
has none, and the check once skipped every part in silence - a part over
0.1 mm tall with no courtyard is now an error, and so is a board where none was
checked); **no part on the underside but `underside_rows:`** (#19 F2: flipped
parts were skipped); each plane
and island zone present; every island-net pad on the island (but `off_island`)
and every island via inside it, no other plane net's via on it or its moat;
**exactly one tie**, the named net tie; and **no signal track on layer 1 or 4
crossing a split in its reference plane** (layer 2 under layer 1, layer 3 under
layer 4) — a track must lie wholly within one filled area of its reference
layer, antipads (holes under 4 mm²) closed; the tie's window and a pair's
crossing of its moat are exempt.

### The module's boards — `kind: module` (`tools/pcb_module.py`)

`hardware/boards/module-main` (four layers), `hardware/boards/module-jack`
and `hardware/boards/module-iso` (two each) are built by `tools/pcb_module.py` and checked by the same `pcb.py
check`. Coordinates are the module CAD's panel frame (`config/module.yaml`),
which the controller's `to_pcb` serves unchanged: a board's KiCad top view is
the panel view, its front face (toward the panel) is F.Cu.

| What | From |
|---|---|
| Outline | `mechanical/module/export/<main|jack|iso>-board.dxf`, less each standoff's hole |
| Jacks, pots, `J-B2B-MOD`, `J-UMBILICAL`, `J-LED-PANEL`, `J-PWR-EURO`, `U-ISO`, standoffs, keep-outs, thickness | `mechanical/module/export/pcb-geometry.echo`, the board's own lines. Each part is placed **by its pads** (`place_by_pads`): the turn and face that put the named pads on the CAD's places is found, not assumed. `layout.yaml` `jacks:` says which jack is which by the net on its tip; `connectors:` which connectors the CAD places (`J-PWR-EURO`'s `odd_column` is the one its footprint's chirality allows with pin 1 at the bottom); `cad_tall:` `U-ISO`'s pins from `config/module.yaml` `iso.pins` |
| A part whose body is on the other face from its pin map | `connectors:` `body: rear` — the jack board's `J-B2B-MOD`, placed on top for its unmirrored pin map, its courtyard, fab and silk drawn on the rear, where its insulator is |
| Standoff pads | `mounts:` — board-only and on no net (the main board), or the sheet's own (`on_sheet:`, the jack board's `AGND_MOD` pair). The head's keep-out is a rule area on no net; on a net, the courtyard keeps parts off and `check_cad` keeps every other net's copper off |
| Everything else | `parts:` `[x, y, rot]` or `[x, y, rot, rear]` |
| Planes, islands, pours | as `kind: main`, plus `pours:` (an outer-layer zone over a polygon, or `outline: board`) and an island's `ties:` list and `foreign_ok:` pads |

**`check` adds** for a module board (`pcb_module.check_cad`): the thickness
and outline against the CAD; every CAD-placed part's pads where the CAD puts
them, on its face; each standoff pad's place, hole and net, and no other
copper under its head; `rules.edge_clearance` not under
`boards.copper_edge`; every part inside its height room on its face
(`heights:`, `rooms:`, the CAD's height keep-outs); **`J-B2B-MOD` and
`J-B2B-ISO` mating** (`check_b2b`, `b2b:` a list of `{row, other}`): on the top
face, and pin k at the same panel-frame place and on the same net on both
boards (against the other board's `.kicad_pcb`); and
**`U-ISO`'s isolation gap** (`check_isolation`): on every copper layer the
nets `isolation: input` and `output` name keep `gap` apart, pads, tracks,
vias and pours alike, the bridging part (`C-ISO-Y`) left out.

**Every board** (all kinds) now also fails on **a courtyard outside the board
outline** (`check_courtyards`, owner 2026-10-02): KiCad's DRC tests
courtyards only against each other and copper only against the edge, so a part
could hang off a board and pass. A part meant to overhang is named in
`layout.yaml` `courtyard_overhang:` with its `reason:` and `source:`; an entry
for a part that does not overhang fails too.

**`pcb.py route <board>`** routes a placed board (`layout --no-route`) **in
place, resumably**: the pairs, moat keep-outs, plane fanout and
`connect_first:` once (on a multi-layer board `connect_first:` is routed and
locked before anything else), then every missing connection by
`pcb_route.complete` in chunks, the board saved and the zones filled after
each, so a killed run picks up where it stopped; then the rip-up rescue, the
silkscreen clear of every via, and the stackup.

### The router: families (`layout.yaml` `families:`)

Under `route: astar` (the main board, the module's boards, the Matrix carrier),
`families:` turns the one shortest-first queue of `pcb_route.complete` into an
ordered list of families (`pcb_route.route_families`; the owner's rule is point
4 of *The routing policy*). A board without `families:` routes exactly as before:
`route_families` is then `complete` itself, and `tools/pcb_families_test.py
--identity <board>` proves it byte for byte on a scratch copy.

```yaml
families:
  - name: rails                 # why this family, and why here
    nets: [class:power5, UMBILICAL_POS12, "/power-entry-instrument/*"]
    via_cost: 40
  - name: chain
    nets: ["/CHAIN_*"]
    bundle: true
  - name: tail
    nets: ["/midi-out/*", /IO2, /IO6]
    region: [265, 100, 360, 143]
  - name: rest                  # optional: the options for everything not named
    time_s: 600
```

- **`nets:`** names (the leading `/` optional), `fnmatch` globs, or
  `class:<name>` for a `net_classes:` entry's nets. A net belongs to the
  **first** family that names it. Nets no family names go to an implicit last
  family, `rest`; a family named `rest` only sets its options. Plane, island,
  fanout and pair nets are not in any family: `prepare` lays them first.
- **`layers:`** (`[F.Cu, B.Cu]`, …) narrows the routed layers; a net class's
  `layers:` and `layer_cost:` still hold inside it. **`region:`** `[x0, y0, x1,
  y1]` confines the family's negotiated routes to a rectangle in the **board's
  own mm** (KiCad's frame, as `tools/pcb_plot.py` draws it - not the body frame
  of `directions: regions:`). **`via_cost:`** replaces `directions: via_cost:`
  for the family. **`rip_up: true`** lets the family's fallback take up earlier
  families' unlocked copper; by default they are frozen. **`bundle: true`**:
  the cells one `pitch:` off a bundle-mate's track are cheaper, so the family's
  nets run side by side through one corridor (the pitch defaults to the least
  the track and clearance allow, on the grid). **`iterations:`** and
  **`time_s:`** cap the negotiation (`pcb_route.FAMILY_ITERATIONS`,
  `FAMILY_TIME_S`).
- **Inside a family: negotiated congestion** (PathFinder). Every connection
  is routed letting its track share grid cells with the family's other nets -
  never with copper already laid, a keep-out or the edge, which stay hard - at a
  cost of *(step + history) × (1 + present × the other nets there)*. After each
  round every shared cell's history grows and the present factor doubles, and
  all the family's connections are routed again, until none share a cell or a
  cap is reached. The order is **crossing-aware**: fewest airwire crossings
  first, then shortest (the idea from drandyhaas/KiCadRoutingTools, MIT; no
  code taken). A connection that negotiated clear is laid only if every
  segment and via passes `Obstacles`' exact test against the copper then on
  the board; the rest - still shared, unreachable, or failing that test - go
  to `complete`, with the earlier families frozen out of its rip-up.
- **`route_first:`** leads as a family of that name, before the listed ones,
  unless a family is itself called `route_first`. **`connect_first:`** is
  unchanged: `prepare` routes and locks it before any family.
- **`route_fence: [x0, y0, x1, y1]`** (top level, board mm): a run that re-routes
  one section changes copper only inside it. Every track and via outside it is
  fixed as locked copper is: `complete`'s rip-up never takes up a net with
  copper outside it, `pcb.rescue` takes up nothing outside it, and `tidy` never
  deletes, moves, splits or merges it (#40: without it, the tail trial's rescue
  re-routed chain lines from x 123, and `tidy` ate failed nets' runs back to
  their pads). **`tidy` never touches locked copper** either way - before #40 its
  doubled-track and overlap merges, `square_joins` and `merge_tracks` could split,
  move or merge a locked track away.
- **Unchanged:** locked copper is an obstacle to every family and never taken
  up; per-class layers, layer costs and via sizes; 45° moves and turn costs;
  the planes, `prepare` and `tidy`. Each family's copper is fixed for the
  families after it **in this run only** - it is not given KiCad's lock flag,
  and `pcb.rescue`, which runs after all of them, is not family-aware.
- **The report**, one line per family: connections routed of those it had,
  how many negotiated and how many `complete` took, failed, vias, length,
  rounds, cells still shared, seconds. `pcb.py route` goes family by family,
  saving and filling after each, so a killed run resumes at the first family
  with a connection missing; `layout` and `finish` route every family in one
  pass.
- **Inspecting it:** `python3 tools/pcb_plot.py <board or .kicad_pcb> -o
  out.png --family <name>` (or `--nets` with names and globs; `--window`,
  `--labels`, `--layout` for a trial's own `layout.yaml`) draws the family in
  colour over everything else in grey, with each net's length and vias. It
  only reads.

### Learned the hard way

- **A zone's fill is FRACTURED**: KiCad joins each hole to the outline by a
  zero-width slit, so read as a polygon every antipad is a notch in the plane's
  edge, and a split check calls every track to a via a crossing. Unfracture a
  copy (`SHAPE_POLY_SET.Unfracture()`) first (`pcb_main.check_planes`).
- **A board's connectivity does not see a track deleted in the same process**:
  `GetUnconnectedCount()` after `Delete()` and `BuildConnectivity()` gave the same
  count with a link of a route gone, so a "delete it if nothing disconnects" test
  deleted live routing and the dangling sweep then took the rest of each route
  (2026-10-01). And `tidy` run in the process that had just laid `complete`'s
  tracks deleted dozens of them as dangling, where the same board saved and loaded
  afresh lost none, and the filler then crashed on the result: save and reload
  between them. Its `TestTrackEndpointDangling` is as stale: `tidy` used it and
  took hundreds of tracks just laid. Test geometrically, or by DRC on a saved copy
  (`rescue`).
- **`BOARD.Remove()` on a board loaded from a file** can crash the next walk of
  it (`GetFootprints`), silently; `Delete()` does not (`pcb_route.tidy`).
- **Freerouting ignores its pass limit in batch** and a shell `timeout` kill
  writes no session at all: bound it with `--router.job_timeout=HH:MM:SS`, which
  stops the job and still writes the session (a form like `20m` parses as no
  timeout).
- **Freerouting cannot see silkscreen or the edge clearance**: the main board's
  labels go on after routing, and the export carries a keep-out band inside every
  edge.

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
- **References are plain numbers, found by what they are.** The key boards
  once used this repository's descriptive references (`R-KEY-SER-LH1`), too
  long to print beside an 0805, so the silkscreen carried role letters no one
  could match to a parts list. Now a part's BOM row is its `Row` field and a
  key's network is the sheet it sits on, so the tools (`pcb.py ref_of`,
  `kicad.py`'s allocation and chain checks) find parts by those, and the
  reference can be R1. A check that finds its parts by name must fail when it
  finds none: the allocation check once passed a board by finding no register.
- **A courtyard must cover the part as it stands.** The KS-33's was ±7.0 against
  a 15 × 15 switch, so a label beside it passed every check and sat under the
  housing. **A new `pcbnew.BOARD()` switches KiCad's current project**, and the
  board being built then saves with default design rules: measure text on the
  board itself.
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
  the board is a rectangle across the cavity, hung at each corner on an
  M2.5 stud pressed flush into the plate (ADR 0020, Amendment 4; the board
  README's assembly steps), with NPTH holes and copper keep-outs on both
  layers under the nut and under the spacer.
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
| [`main-board.sch.png`](../../hardware/boards/main-board/main-board.sch.png) (+ one PNG per sub-sheet) | the KiCad project `hardware/boards/main-board/main-board.kicad_sch` (**source**) |
| the six main-board circuits' `.sch.png` (`hardware/carrier/**`) | each circuit's `.kicad_sch` beside it (**source**) |
| [`module-main.sch.png`](../../hardware/boards/module-main/module-main.sch.png), [`module-jack.sch.png`](../../hardware/boards/module-jack/module-jack.sch.png) (+ one PNG per sub-sheet) | the KiCad projects under `hardware/boards/module-*/` (**source**) |
| the module circuits' `.sch.png` (`hardware/module/**`; a two-page circuit renders `.p2`/`.p3` too) | each circuit's `.kicad_sch` beside it (**source**) |
| the three interfaces' `.sch.png` (`hardware/interfaces/**`) | each circuit's `.kicad_sch` beside it (**source**). No board places them: each spans boards, and each page's *The sheet, and which board places what* says which board draws which part |

### Not yet

- **The module's layout** is under way (2026-10-02, `kind: module`, above);
  each board's README says where it stands.
  The interfaces migrated on 2026-09-29. The boards still draw their own
  halves of them rather than placing the interface sheets, which span boards
  (each interface page says which board draws which part). The main board is a project placing its circuit sheets
  (2026-09-29); `tools/pcb.py` lays it out in its `kind: main` mode (*The main
  board*, above), and what that first layout left open is in
  `hardware/boards/main-board/README.md`, *Open*.
- **The BOM fragments** become exports once every board is in KiCad, because
  a row's quantity is a count over all of them (ADR 0019).
- **A committed git hook.** The commit gate below is a Claude Code hook, and
  CI (*CI*, below) reports a red push only after it lands; nothing refuses a
  human's red `git commit` before it exists (issue #31).

### The commit gate — `tools/commit-gate.py`

A `PreToolUse` hook on `Bash` (`.claude/settings.json`). For any command that
is not a `git commit` or `git merge` it exits at once and says nothing. For
one that is, it runs, in the work tree the command commits in:

- `check-staleness.py` (everything that needs no KiCad: figures, BOM,
  datasheets, the CAD and sim ledgers), about 30 s;
- `kicad.py check`, at the same time, when `kicad-cli` is installed **and** the
  commit can touch a KiCad input: something staged under `hardware/` or
  `mechanical/export/`, a KiCad tool, or a `git add`, `-a` or merge in the same
  command (whose staging the gate cannot see yet). About 70 s alone, and the
  two together about two minutes on a loaded four-core box (2026-10-03).
  Otherwise the summary says `kicad: SKIPPED` and why.

A FAIL **denies the command** (`permissionDecision: deny`). A commit that has to
go in red — the tree is known-red and this commit does not make it so — says so
in its message, with a trailer line

```
Gate-Red: <which failures, and why this commit goes in with them>
```

and goes ahead with the failures shown. The trailer stays in the log, and
`git log --grep Gate-Red` lists every commit made red. A checker that crashes
or times out (each has 200 s) is a FAIL. Detail is in `.staleness/report.txt`
and `.staleness/gate.txt`. `python3 tools/commit-gate.py --self-test` checks
which commands it treats as commits.

### CI — `.github/workflows/gate.yml`

The hook guards only the commits Claude Code makes. **CI runs the same checks
on every push and pull request, to any branch**, so a commit made any other
way is checked too (issue #31). The hook stays: it refuses a red commit before
it exists, while CI reports one after it is pushed and blocks nothing — there
is no branch protection. Two jobs:

- **`corpus (no KiCad)`** — `check-staleness.py`, then each tool it shells out
  to as a step of its own, so the run names *which* check is red:
  `merge-bom.py --check`, `merge-manifests.py --check`, `verify-datasheets.py`,
  `check-netlist.py --strict`, `adr-index.py --check`, `cad.py check`,
  `sim.py check`, `sim_coverage.py`, `sim_recheck.py`, and
  `commit-gate.py --self-test`. Python and PyYAML only: `cad.py check` reads
  fingerprints and builds nothing.
- **`kicad (kicad.py check, KiCad 9)`** — KiCad 9 from the PPA `setup-env.sh`
  adds (its KiCad part only), the library tables, the pinned `shapely`, then
  `kicad.py check` on the system `python3`, the one `pcbnew` is built for. It
  runs on every push, not only when a KiCad input changed: the hook already
  skips it when nothing staged is one, and CI is where that gets caught. A
  KiCad other than `tools/toolchain.yaml`'s is a warning, as in the hook.

**Nothing is allow-listed.** Every step runs even when an earlier one failed,
and a red tree shows red: no `continue-on-error`, no per-check exemption, and
a `Gate-Red:` trailer explains a red commit in the log without making it green
here. When CI was added (2026-10-04, on `29c8ca7`) both jobs were red on
failures that predate it: `sim_coverage.py` — and so `check-staleness.py` — on
`boards/module-iso`, which has no row in *Coverage* (§5); and `kicad.py check`
on `module-main`, whose `pcb.py check` errors and stale `.sch.png` renders
followed a `power-entry.main.kicad_sch` change. The latest run is the current
list; this paragraph is not.

### Ordering: JLC's stock, not LCSC's

**A machine-placed part is drawn from JLC's own parts library, whose stock is
not LCSC's storefront stock.** On 2026-10-01 three codes read 0 on LCSC's
product API while JLC held them by the hundred thousand (C28260 123,345;
C28323 2,294,300, both Basic), and C51349 no longer resolved on LCSC at all
while JLC held 4,931 [web: LCSC product API and the jlcpcb.com parts-search
API, 2026-10-01]. Check a machine part at JLC — the parts search behind
`https://jlcpcb.com/parts`, or `https://jlcpcb.com/partdetail/<code>`. A
`hand` part is bought wherever it is stocked, and its row says where.

**The exception: a machine part JLC does not hold, sourced for the order.**
JLC's Global Sourcing (or consignment) buys a part into the assembly that
neither its library nor LCSC has in stock; the part stays `machine` and keeps
its MPN. It is used only where the part is chosen on a property its
alternatives do not document, and its row says so. **`FB-IN`** (Laird
MI1206K601R-10, `FB1`–`FB4` on `module/power-entry`) is ordered this way
(owner, 2026-10-01): it is the bead whose datasheet publishes impedance under
DC bias, and LCSC lists it at 0.

## §5. Circuit simulation — `tools/sim.py`

```
python3 tools/sim.py run [<sim dir> ...]   # run every sim/sims.yaml, or those named; write results.yaml
python3 tools/sim.py check                 # no ngspice: each results.yaml matches its inputs and passed
python3 tools/sim.py show <sim dir>        # a results.yaml as a table
python3 tools/sim_coverage.py              # the Coverage table below against the tree
```

A circuit's `sim/` holds three things:
- `sims.yaml`: what is simulated, the model parameters with their sources,
  the tolerance corners, and what every run must show;
- the decks;
- `results.yaml`, which is generated.

**Part values are never written in a sim.** A deck names them by BOM row
(double-braced, `R-KEY-PU`) and the tool fills them from the circuit's exported
`netlist.yaml`. Figures are cited by id (`fig['key-release-time']`).
`params_from:` imports another sim's model parameters, so a threshold ratio or
an input capacitance is stated once.

**Corners, not a guess.** Every `vary:` parameter has a relative range. Each sim
runs at the nominal and at every combination of the range ends, and each
measure is recorded at its nominal, minimum and maximum, with the corner that
gave each. For RC networks and thresholds, which are monotonic in every
parameter, the corners bound the result.

**`generate: board`** builds a deck from a board's `board-netlist.yaml`:
- every part by its row (`parts:`), on the nets it is wired to;
- the nets the rest of the system drives (`drive:`).

A wiring or value mistake on the board therefore shows up in its own
simulation.

**Held like the renders.** `results.yaml` hashes every input: the tool, the
sims.yaml files, the decks, the netlist and the cited figures' values.
`check-staleness.py` runs `sim.py check`, so a changed value, deck or figure,
or a failed assertion, fails the check until the sims are re-run. Proven by
changing `C-KEY` in the netlist, 2026-09-28.

**The hashes cover the inputs, not the results**, so `check-staleness.py` also
runs `tools/sim_recheck.py`: every assert in `sims.yaml` evaluated again on the
recorded min, nominal and max, the recorded sims, measures and asserts held to
`sims.yaml`'s, and a recorded `pass:` its own numbers contradict reported as an
edit. Before it, a hand-set number or an assert's `expr` replaced with `True`
passed every check (issue #9, G5, by mutation). It also reports a `post:`
measure **pinned to a constant of its own definition** — a trough whose window
starts where the signal crosses `v_on + 1` can never read above it, so an
assert that it stays over `v_on + 0.5` passed by construction (G6): a failure
when an assert reads the measure, a note otherwise. It is a separate tool
because `sim.py` hashes itself into every `results.yaml`: an edit to `sim.py`
makes every result stale until every sim is re-run. What it still cannot see:
an edited number that no assert reads.

**One ngspice for every result.** `sim_recheck.py` also fails a `results.yaml`
made on another major version than `tools/toolchain.yaml`'s `ngspice_major`
(#5, 2026-10-03). Results moved between 42 and 44.2 without crossing an
assertion — an unquieted op-amp's noise by 3×, `SYNC`'s overshoot by 8× — so
a corpus with both is not one measurement. Re-run on the pinned version, or
move the pin and regenerate every result.

**What a result is worth.** It proves the arithmetic and the wiring against the
models it was given. Where a model is behavioural, as a Schmitt input modelled
as its datasheet thresholds or a switch as two resistances, `sims.yaml` says
so.

**Learned the hard way:**
- ngspice 42's netlist `.meas` cannot parse `vm()` or `vdb()` in batch mode. On
  `v()` it measures the **real part**: a pole came out at 102 Hz instead of
  159 Hz, with no error. AC measures go in a `.control` block, where they are
  right.
- `v(0)` is not a vector. A measure of the ground net proves nothing anyway,
  so none is taken.
- Do not use PySpice (`hardware/module/pitch-stage/sim/README.md`).
- **A PULSE with a zero width is not a spike.** SPICE reads PW = 0 as unset,
  and it defaults to the whole run: a 5 ns charge pulse became a step that never
  ended, and the rail "rang" 100 times too hard.
- **A false operating point reports every measure.** When a vendor macromodel
  defeats gmin and source stepping, ngspice falls back to a "transient op" and
  says it succeeded wherever the ramp stopped: the reference buffer's `VS` came
  out at 0.55 V with every measure present. `sim.py` refuses a run that needed
  it; `.options rshunt=1e10` (10 GΩ per node) lets the stepping finish.
- **A load step on a regulated node has no step size.** `overshoot()` divides by
  the change in final value, which is ~0 there and gave 5 × 10⁶ %. `rebound()`
  measures the swing back through the final value against the first dip.
- **A diverged run reports a number too.** `sim.py` refuses any measure that is
  not finite or is beyond 1e12.
- **A switched-in capacitor must be switched out.** A 1 GF injection capacitor
  left in place when the same deck is re-used closed-loop for another AC
  question grounds the (−) input at every frequency that matters: the −12 V
  rail's path to the breath jack read 0.67 V/V instead of 0.42. The deck makes
  it a parameter and opens it (`breath-output-stage/sim`, 2026-09-30).
- **A DC sweep into a clip loses the macromodel.** TI's OPA2197 model found no
  operating point where the response shaper's output saturates; a slow
  transient ramp of the input does the same job (`breath-response-shaper/sim`).
- **A current source is not a load.** A fixed current drawn from a node that
  starts at 0 V drives it negative and trips everything upstream; a load that
  is off until its supply arrives is a current scaled by the voltage
  (`power-entry-instrument/sim`).
- **One flat subcircuit shares one node namespace.** In the system deck the
  instrument's reference capacitor's ESR node and the module's −12 V
  decoupler's were both `crn1`: 60 mA of the instrument's return ran through
  the rack's ground, the LED row "moved pitch" by 0.1 cents, and every run
  converged. Name a node by its section, and look for collisions when
  two blocks are pasted into one `.subckt` (`hardware/interfaces/system/sim/`).
- **An op-amp model's output limit is the datasheet's swing, not a guess.** A
  behavioural limiter 0.6 V inside the rails clipped a follower at 0.28 V on a
  single 12 V supply; the breath sensor's buffer sat 0.33 V high and every
  breath result was on a half-saturated stage. The OPA2197 swings to 25 mV
  (`hardware/interfaces/system/sim/`, `v_hr`).
- **A big deck with nanosecond edges dies at its smallest steps.** The system
  deck ran millisecond LED edges and failed "timestep too small" at every SPI
  edge, wherever the edge was — a 3 ns pulse into a 3 pF load with no path to
  anything else did it. What fixed it: `abstol=1e-6` (results unchanged to
  0.1 % on the LED scenario) and no nanohenry ESL on capacitors whose loop has
  no resistance.
- **TI's "noiseless" resistors are noisy in ngspice 42.** TI's macromodels mark
  their bookkeeping resistors `R_NOISELESS` with PSpice's `T_ABS=-273.15`, which
  ngspice 42 ignores for noise: an OPA2197 follower read 868 nV/√Hz, all of it
  one 2.2 Ω resistor, against the datasheet's 5.5. A `.noise` deck silences each
  one by name with `alter … noisy = 0` and proves the result against the
  datasheet (`breath-output-stage/sim`, `noise.cir` and `noise-amps`, 2026-10-01).
- **A long chain of macromodels may find no operating point as one circuit**
  even where each piece does. The breath chain, sensor to jack, does not; cut at
  an op-amp output into two disconnected pieces in one deck, each converges, and
  the noise is recombined as piece A's spectrum × piece B's |H|² plus piece B's
  own (`breath-output-stage/sim/noise.cir`). A non-zero `gminsteps` other than
  the default switches ngspice to spice3 gmin stepping, which helped one piece
  and broke another; `itl1=1000 itl2=1000 gminsteps=0` (no gmin stepping, straight
  to source stepping) found both, at rest and at a hard blow, in under a second
  where the failing gmin attempts had taken ten.
- **A threshold test must not mix parts.** "Never below VT− max after crossing
  VT+ min" fails on a perfect edge, because across the datasheet's spread VT−
  max is above VT+ min. The test is the waveform's swing back after its first
  crossing (`backswing`), held against the smallest hysteresis. It was proven
  to fire on SCK without its series resistor.

| Simulated | Where |
|---|---|
| one key's network, with its press, release, filter and corners | `hardware/cluster/key-switch-network/sim/` |
| the left-hand key board as wired, all keys released and pressed | `hardware/boards/key-board-lh/sim/` |
| the right-hand key board as wired, generated from its board netlist with the left-hand board's models | `hardware/boards/key-board-rh/sim/` |
| the key chain: its 3V3 rail (bead, ribbon, decoupling, the do-not-fit bulk capacitor) and SCK and QH over the ribbon | `hardware/interfaces/key-chain-loom/sim/` |
| the reference buffer's loop, output impedance and load step, and TI's Figure 56 (TI's OPA2197 and REF5050 models) | `hardware/carrier/breath-excitation-reference/sim/` |
| the breath link's CMRR across the umbilical, both ends' parts at every tolerance corner, in each of the bandwidth toggle's three modes with `U-BW-SW` as its datasheet (TI's INA828 and OPA2197) | `hardware/module/breath-receive-stage/sim/` |
| the pitch stage's step into a passive mult, and its loop at the same loads | `hardware/module/pitch-stage/sim/` |
| rack power-on: the rails, `DAC_AVDD` from `U-REG-DAC` (the LT3042, behavioural, its set-point spread and soft start) and the pitch jack; and the instrument's LED row PWM reflected through `U-ISO` onto the rack's ±12 V and into the module's rails and its pitch, mod and breath jacks | `hardware/module/power-entry/sim/` |
| the umbilical load switch's start, with a behavioural LT1641 built from its datasheet | `hardware/module/umbilical-load-switch/sim/` |
| SCLK, MOSI and CS_MOD over the umbilical as coupled lossy lines (ngspice `CPL`), from a banked Cat5e datasheet, through each line's pull and `R-RX-MOD`/`C-RX-MOD` into the receiver `U-RX-MOD` (74AHCT14) | `hardware/interfaces/spi-link/sim/` |
| the four mod channels and their shared reference: range, a stale or wrong `V_ref`, a step and the loop into a passive mult, crosstalk | `hardware/module/mod-channels/sim/` |
| the breath output stage: its offset table, gain ends, clip, a step and the loop into a passive mult, the −12 V rail's path to the jack, and the chain — the response shaper and this stage one after the other, at the commissioned setting and across `POT-RESP`; and the whole breath chain's noise, sensor to jack and to the instrument's ADC, per stage and per bandwidth mode; and the breath LED's driver on its output, against a twin of the stage without it (TI's OPA2197, INA828 and REF5050 models, each held to its datasheet) | `hardware/module/breath-output-stage/sim/` |
| the response shaper's curve at `POT-RESP`'s ends and centre, and its clip, with a behavioural `D-RESP` fitted to the 1N4448W's guaranteed window; `TRIM-RESP` commissioned in the deck (bisected to its target per corner) and at both ends of its travel, 0–40 °C | `hardware/module/breath-response-shaper/sim/` |
| the breath ADC's anti-alias filter, its time constant, and the MCP3202's sample capacitor against it, at 4 kHz and, as what-ifs, 8 and 16 kHz | `hardware/carrier/breath-adc/sim/` |
| the instrument's input LC against the buck's negative resistance, and its start from `U-ISO` through the load switch and the cable, cold and hot-plugged; the 5 V ideal-diode OR (`U-USBOR`, `Q-USBOR`) against the Matrix's USB `VBUS`: back-feed, switch-over and the rail's range (#39) | `hardware/carrier/power-entry-instrument/sim/` |
| the LED row's data line: its edge and `T0H` at the first LED | `hardware/carrier/led-strip-drive/sim/` |
| the MIDI out's current loop: Type A and B into CA-033's receiver, its edges through 1-3 m of cable, shorts at the jack, the power-on default and the wrong A/B setting | `hardware/carrier/midi-out/sim/` |
| the module's two 5 V rails at power-on and power-off, and `SYNC` at the DAC between them (TI's SN74AHCT125 model and the DAC8568's IBIS clamp) | `hardware/module/digital-and-supervision/sim/` |
| the DAC8568's power-on glitch and its 3-state reference, into the pitch and mod jacks | `hardware/module/dac8568/sim/` |
| the breath link's TVS diodes: CMRR, `PWR_GND` rejection, leakage, in each bandwidth mode | `hardware/interfaces/breath-sense-link/sim/` |
| `U-BREATH`'s documented MPXV7007DP fallback, **not fitted**: the offset-and-gain stage at `U-BUF` B into the in-amp, commissioning, ratiometry and a step; and why a drop-in fails (its own directory, so no live result moves) | `hardware/interfaces/breath-sense-link/fallback-mpxv7007/sim/` |
| the panel LED's current and its start | `hardware/module/panel-led/sim/` |
| the whole system, instrument to jacks, from the exported netlists: the rack, `module/power-entry` with `U-ISO`, the load switch, the umbilical's eight conductors as coupled lines, the instrument's power entry with `Q-INRUSH`, its buck and LED row, the breath sensor, buffer and link, the SPI pads and receiver, and the module's breath chain, DAC stages and ground star; three scenarios — the LED row switching (ROADMAP M8's "pitch scoped while the LEDs sweep"), a burst of DAC frames, and a hot-plug — with behavioural op-amps and in-amp held to TI's models | `hardware/interfaces/system/sim/` |

### Coverage — every circuit and board

**`tools/sim_coverage.py` reads the table below**, and `check-staleness.py`
runs it. Every circuit whose `netlist.yaml` has a part, and every board with a `board-netlist.yaml`, must
have a row, and the row must be true: `own` needs that directory's `sim/`;
`covered` must name at least one existing `sim/` directory in backticks, and
says what in it covers what; `n/a` says why in one sentence. A circuit that
grows a `sim/` while its row still says `covered` or `n/a` fails too. Added
2026-10-01, when the owner asked "All the spice was done?" and, for every
circuit without a `sim/`, the answer was written nowhere.

| Circuit | Simulated | What, or why not |
|---|---|---|
| `carrier/carrier` | covered | `hardware/interfaces/spi-link/sim/`: every sim reads this netlist for `R-SPI-SER-*`, `R-CS-PULL-INST` and `U-TVS-SPI`. The rest are a connector (`J-MCU`), a net tie and the bought Matrix, whose pads are those sims' `r_drv`/`tr_drv` |
| `carrier/breath-adc` | own | |
| `carrier/breath-excitation-reference` | own | |
| `carrier/led-strip-drive` | own | |
| `carrier/power-entry-instrument` | own | |
| `carrier/midi-out` | own | |
| `carrier/service-uart` | n/a | A connector, `R-TXD-SER` in series with a UART line and `C-EN` on `EN`: static parts with nothing to simulate against (`EN` and `IO0`'s pulls are the Matrix's own; `C-EN` against `R8` is one RC, τ = 10 ms on the page) |
| `cluster/key-marker-and-bits` | covered | `hardware/boards/key-board-lh/sim/`: the free bit's `R-KEY-PU` is in the board deck, and `m_free_high` holds it over `V_T+` max with every key open and every key pressed |
| `cluster/key-register` | covered | `hardware/boards/key-board-lh/sim/` (`U-KEYS`'s inputs against their thresholds) and `hardware/interfaces/key-chain-loom/sim/` (`C-DECOUPLE-165` against `U-KEYS`'s `C_pd` on the rail; `QH` over the ribbon) |
| `cluster/key-switch-network` | own | |
| `interfaces/breath-sense-link` | own | its TVS diodes; the link's CMRR with `R1`/`R1b` is `hardware/module/breath-receive-stage/sim/` |
| `interfaces/key-chain-loom` | own | |
| `interfaces/spi-link` | own | |
| `module/breath-output-stage` | own | |
| `module/breath-receive-stage` | own | |
| `module/breath-response-shaper` | own | |
| `module/dac8568` | own | power-on; its `SYNC` pin against `DAC_AVDD` is `hardware/module/digital-and-supervision/sim/` |
| `module/digital-and-supervision` | own | power sequencing; the receiver's signals are `hardware/interfaces/spi-link/sim/` |
| `module/link-supervision` | n/a | No parts: the record of two deleted circuits |
| `module/mod-channels` | own | |
| `module/panel` | n/a | No electrical parts: the panel itself |
| `module/panel-led` | own | |
| `module/pitch-stage` | own | |
| `module/power-entry` | own | |
| `module/umbilical-load-switch` | own | |
| `boards/key-board-lh` | own | |
| `boards/key-board-rh` | own | |
| `boards/matrix-carrier` | n/a | Connectors and copper only: the Matrix's two pad-row headers and J-MCU-C, each pin on the conductor `tools/kicad.py check` holds it to; the ribbon's grounds and supplies are `hardware/carrier/breath-adc/sim/`'s (`CBL-MCU-RIBBON`'s length, `drc:Matrix ribbon length`) |
| `boards/main-board` | covered | its placed circuits, each by its own row; its root-sheet parts (`FB-CHAIN`, `R-CHAIN-SER`, `R-SER-TERM`, `U-TVS-CHAIN`) are `hardware/interfaces/key-chain-loom/sim/`'s, except `R-SER-TERM`, a static 10 kΩ pull-up on `SER`, which that sim drives instead and nothing simulates |
| `boards/module-main` | n/a | Places circuit sheets, each covered by its own row; its own parts are two connectors |
| `boards/module-jack` | n/a | Places circuit sheets, each covered by its own row; its own part is a connector |
| `boards/umb-adapter` | covered | Two connectors and the copper between them: all eight of the umbilical's conductors are coupled lines in `hardware/interfaces/system/sim/`, and its SPI conductors CPL lines in `hardware/interfaces/spi-link/sim/` |

---

## §6. Every tool, and where it is documented

One row per script in `tools/`. A tool documented elsewhere is pointed at, not
re-described here.

| Tool | What it does | Documented in |
|---|---|---|
| `cad.py` | The body CAD: parameters, renders, DXFs, `drc.echo`, the clash check, fingerprints | §2 |
| `render-instrument.py` | The controller's photographs in Blender (Cycles), from the body CAD's solids and the boards' `.kicad_pcb`. Run by `cad.py build`, never by hand into `mechanical/renders/`. **Needs Blender as a Python module (`bpy`)**, which `setup-env.sh` installs | its docstring; `mechanical/README.md`; `config/render.yaml` |
| `render-module.py` | The module's photographs, the same way | §2 |
| `panel-art.py` | The module panel's printed artwork | §2 |
| `kicad.py` | Sheets: export, render, set fields, `check` (needs KiCad 9, run by hand) | §3 |
| `sch.py` | A hand-written netlist built into a sheet | §3 |
| `pcb.py`, `pcb_route.py`, `pcb_main.py`, `pcb_freeroute.py` | Board layout, routing, the main board's kind, the Freerouting round trip | §4 |
| `pcb_plot.py` | A board's routing in 2D, nets by name, glob or family (read-only) | §4, *The router: families* |
| `pcb_families_test.py` | The families stage on a constructed boxing-in board; `--identity <board>`: no `families:` routes byte for byte as before | its docstring; §4, *The router: families* |
| `lib-models.py` | 3D models drawn from banked drawings | §4 |
| `sim.py`, `sim_coverage.py` | Circuit simulation and its coverage table | §5 |
| `check-staleness.py` | The commit gate: figures, links and their anchors, generated files, CAD, sims | `repo-maintenance.md` §2 |
| `commit-gate.py` | The Claude Code hook that runs `check-staleness.py` (and `kicad.py check`) on a commit; `.github/workflows/gate.yml` runs the same checks in CI | §4, *The commit gate* and *CI* |
| `check-netlist.py` | Netlists against the BOM and the drawings | `CLAUDE.md`, *Hardware conventions*; `repo-maintenance.md` |
| `merge-bom.py` | Regenerates `hardware/bom.csv` from the fragments; `--check` | `repo-maintenance.md` §4, §6 |
| `merge-manifests.py`, `verify-datasheets.py` | Regenerates `datasheets/MANIFEST.csv`; verifies the banked files | `repo-maintenance.md` §3, §6 |
| `audit-notes.py` | Classifies BOM notes as live content or history (advisory) | `repo-maintenance.md` §6 |
| `check-conservation.py` | Content conservation for a page split | `repo-maintenance.md` §6 |
| `rewrite-paths.py` | The 2026-09-21 restructure's path rewriter | `repo-maintenance.md` §6, §7 |
| `extract-findings.py` | Builds a review wave's `FINDINGS.csv` ledger from its reports (`<wave-dir> [--check]`) | its docstring; `CLAUDE.md`, *Review waves* |
| `adr-index.py` | Regenerates the index in `docs/decisions/README.md` from each ADR's `**Status:**` line; `--check` runs inside `check-staleness.py` | its docstring; `docs/decisions/README.md` |
| `setup-env.sh` | Installs everything above | §1 |
