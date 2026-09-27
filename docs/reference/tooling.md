# Tooling — installing and using the body CAD and the schematic pipeline

Two pipelines turn data in this repository into pictures and design files:

| Pipeline | Source (edit these) | Tool | Generated (never edit) |
|---|---|---|---|
| **Body CAD** | `config/body.yaml`, `config/key-layout.yaml`, `mechanical/cad/*.scad` | `tools/cad.py` (OpenSCAD) | `mechanical/renders/*.png`, `mechanical/export/*.dxf`, `mechanical/drc.echo`, `mechanical/clash.txt`, `mechanical/OUTPUTS.csv`, `mechanical/cad/generated/params.scad` |
| **Schematics** | the KiCad sheets: each circuit's `<circuit>.kicad_sch`, each board's project under `hardware/boards/` (ADR 0019) | `tools/kicad.py` (KiCad 9) | a migrated circuit's `netlist.yaml`, `board-netlist.yaml`, `*.sch.png`, `hardware/SHEETS.csv` |

Both follow the same rule, the one this repository exists to enforce
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
- a board has an ERC error;
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

The left-hand key board (`hardware/boards/key-board-lh/`) is the proof of
concept: placed, routed and checked here, from the same sources as everything
else.

### Where a layout comes from

| What | From |
|---|---|
| Netlist, footprints, references | the board's KiCad sheets (§3); a part's footprint is its sheet's `Footprint` field |
| Board outline | `mechanical/export/key-board-lh.dxf` — the body CAD's key board |
| Switch and ribbon-connector positions | `mechanical/export/pcb-geometry.echo` — the body CAD |
| Switch 3D model height | `config/body.yaml` `switch.pcb_below_seat` |
| Everything else's place, and the design rules | `layout.yaml` beside the board |
| Footprints KiCad lacks | `hardware/lib/woody.pretty/` (`hardware/lib/README.md`) |

### Commands

```
python3 tools/pcb.py layout hardware/boards/key-board-lh   # FIRST layout: place, route, pour, fill (refuses if the board exists; --force)
python3 tools/pcb.py check  hardware/boards/key-board-lh   # KiCad DRC + schematic parity + switches where the CAD puts them
python3 tools/pcb.py render hardware/boards/key-board-lh   # 3D both sides, 2D copper, and fab/ (Gerbers, drill, placement)
```

**After `layout`, the `.kicad_pcb` is the source**, like the sheets: open the
project in KiCad 9 and move or re-route by hand. `tools/kicad.py check` runs
`pcb.py check` on every board that has a layout, and the renders and `fab/`
files are in `hardware/SHEETS.csv`, so an edited board with stale Gerbers is
reported by name.

### The router, and its limits

`tools/pcb_route.py` is a small two-layer grid router: A* on a 0.2 mm grid per
layer, vias where they fit, every other net's copper, every hole and the board
edge inflated by the clearance. Signals first (shortest first), the power rail
wider, ground last as a net of its own, then a ground pour on both layers and
a stitching via beside every single-sided ground pad. **It proves nothing about
itself** — KiCad's DRC does, with schematic parity and zero unrouted
connections. It is for simple digital boards like the key boards. **The main
board's analog routing is done by hand** (`docs/reference/pcb-pipeline.md`).

### Learned the hard way

- **KiCad's zone filler crashes Python, silently,** on a board built in the
  same process: the file was never written. Fill in a fresh process after
  saving (`pcb_route.fill_zones`).
- **SWIG iterators hand out copies**: `for m in fp.Models(): m.m_Offset.z = …`
  changes nothing. Index into the list.
- **A stub that is not an obstacle becomes a short**: every piece of copper the
  router adds, however small, must enter its obstacle list.
- **KiCad may write an empty global `fp-lib-table`** on first run, and then
  every footprint "is not in the configuration". `tools/setup-env.sh` replaces
  an empty one.
- **3D models**: `kicad-packages3d` is 3 GB; the four this board needs came
  from `gitlab.com/kicad/libraries/kicad-packages3D` tag `9.0.0` into
  `/usr/share/kicad/3dmodels/`. The Molex connector has no model there, so it
  renders as pads.
- **Reference text as long as `R-KEY-SER-LH1` cannot be silkscreened on an
  0805**: references go on the fabrication layer, which the assembly drawing
  reads.

### Findings the first layout made

- **The ribbon connector is deeper than the body CAD assumes.** The CAD's
  envelope is 5.5 mm deep (`boards.ffc_conn_w`, from memory); the first
  stand-in footprint (Würth 68611214422) needed 9.9 and could not fit beside
  the switch holes, and the one used (Molex 200528-0120) needs 6.7 — it
  clears LH2's centre hole by about 1.2 mm. `J-CHAIN`'s part is open until
  M4; when it is chosen, its real depth goes into `config/body.yaml`.
- **The switch pins barely reach through.** The pin blades' tips are 5.10 mm
  below the seat and the PCB top is `switch.pcb_below_seat` below it, so on a
  1.6 mm board about 0.1 mm of pin shows to solder (`docs/reference/ks33-geometry.md`).
  A 1.2 mm board would leave about 0.5 mm. Open, and cheap to decide before
  the first order.

### Where the sheets are

| Sheet | Status |
|---|---|
| [`key-board-rh.sch.png`](../../hardware/boards/key-board-rh/key-board-rh.sch.png) (+ one PNG per sub-sheet) | **source**, `hardware/boards/key-board-rh/` |
| [`key-board-lh.sch.png`](../../hardware/boards/key-board-lh/key-board-lh.sch.png) (+ pages) | **source**, `hardware/boards/key-board-lh/` |
| [`key-register.sch.png`](../../hardware/cluster/key-register/key-register.sch.png), [`key-switch-network.sch.png`](../../hardware/cluster/key-switch-network/key-switch-network.sch.png), [`key-marker-and-bits.sch.png`](../../hardware/cluster/key-marker-and-bits/key-marker-and-bits.sch.png) | **source**, the three key-board circuits |
| [`led-strip-drive.sch.png`](../../hardware/carrier/led-strip-drive/led-strip-drive.sch.png) | generated from YAML — not yet migrated |

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
