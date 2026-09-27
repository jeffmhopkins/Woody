# Tooling — installing and using the body CAD and the schematic pipeline

Two pipelines turn data in this repository into pictures and design files:

| Pipeline | Source (edit these) | Tool | Generated (never edit) |
|---|---|---|---|
| **Body CAD** | `config/body.yaml`, `config/key-layout.yaml`, `mechanical/cad/*.scad` | `tools/cad.py` (OpenSCAD) | `mechanical/renders/*.png`, `mechanical/export/*.dxf`, `mechanical/drc.echo`, `mechanical/clash.txt`, `mechanical/OUTPUTS.csv`, `mechanical/cad/generated/params.scad` |
| **Schematics** | a circuit's `netlist.yaml` + `schematic.yaml`; a board's `board.yaml` + `schematic.yaml` | `tools/board.py`, `tools/sch.py` (KiCad 9) | `hardware/boards/*/board-netlist.yaml`, `*.kicad_sch`, `*.sch.png` |

Both follow the same rule, the one this repository exists to enforce
(`CLAUDE.md`): **numbers and connections live in one data file, and every
picture is generated from it and fingerprinted**, so a picture that no longer
matches its source is reported by name instead of silently lying.

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

## §3. Schematics — `tools/board.py` and `tools/sch.py`

### What is the source

- **`netlist.yaml` is authoritative for connectivity**, as it is for all of
  `hardware/` (`CLAUDE.md`). Circuits are written once and *replicated*: one
  key-register netlist serves four registers.
- **A board is assembled, not written.** `hardware/boards/<board>/board.yaml`
  names the cluster, the connector and what the circuit's ports are called on
  this board; `tools/board.py` expands the circuit netlists into
  `board-netlist.yaml`, filling each register input from
  `hardware/cluster/key-marker-and-bits/allocation.yaml` (the 32-bit
  allocation as data) and the connector's pins from
  `hardware/interfaces/key-chain-loom/netlist.yaml`. It refuses to build if
  `allocation.yaml` and the table in `key-marker-and-bits.md` §4 disagree, or
  if a key named there is not on that cluster in `config/key-layout.yaml`.
- **`schematic.yaml` is placement only**: which KiCad symbol draws each part,
  each pin's package number (cited to a banked datasheet), and where things
  sit. It is to a sheet what `config/body.yaml` is to the body.

### Commands

```
python3 tools/board.py build hardware/boards/key-board-rh    # assemble the board netlist
python3 tools/sch.py   build hardware/boards/key-board-rh    # write, prove, ERC and render the sheet
python3 tools/sch.py   build hardware/carrier/led-strip-drive   # a single-circuit sheet
python3 tools/board.py check hardware/boards/key-board-rh    # exit 1 if the board netlist is stale
python3 tools/sch.py   check hardware/boards/key-board-rh    # exit 1 if the sheet is stale
```

`sch.py build` prints three things, and all three must pass:

1. **netlist match** — it exports KiCad's own netlist of the sheet it just
   wrote (`kicad-cli sch export netlist`) and compares every net, pin by pin,
   with the netlist. A wire to the wrong pin, a label on the wrong stub, a net
   split in two or two nets merged: all fail.
2. **KiCad ERC** — `kicad-cli sch erc`, KiCad's own electrical rules check.
3. **pin names** — where the KiCad library names a pin (`VCC`, `GND`, `DS`,
   `~{PL}`), the pin map must agree.

**What no check can prove: the pin-number map.** The wires go wherever the map
says, so a wrong map draws a consistent, wrong sheet. That is why every map
cites its datasheet page, and why a map may state the library's pin name too
(`SHLD: [1, "~{PL}"]`) — then a wrong number is caught against the name.

### Drawing a new sheet

1. **For a circuit**: add `schematic.yaml` beside its `netlist.yaml`
   (copy `hardware/carrier/led-strip-drive/schematic.yaml`).
   **For a board**: add `hardware/boards/<name>/board.yaml` and
   `schematic.yaml` (copy a key board's), then `board.py build`.
2. Give every part a `symbol` (`library:name` from
   `/usr/share/kicad/symbols/`), and a `pins` map for anything whose pins are
   not already numbered in the netlist.
3. Place parts with `at: [x, y, rotation]` — millimetres, y down, on the
   1.27 mm grid. Multi-unit parts (a quad gate) place each unit under `units`.
4. Build, then **look at the PNG** — the checks prove connections, not
   legibility. Move things until nothing overlaps.

### How connections are drawn

- A pin named in a `wires` polyline is joined by that wire. Polylines mix pin
  names (`R-LED-SER.1`) and points (`[91.44, 58.42]`) and must be orthogonal.
- Every other pin gets a short stub and then: **a power symbol** if its net is
  in `power` (it points along the stub, away from the part); **a no-connect
  flag** if it is the only pin of an `external_endpoints` net; otherwise **a
  net label** — a global label if the net is a port.
- `labels` put a name on a wire; `power_symbols` put a power symbol at a point.
- `repeat` lays one block down per instance: `for` lists the instances, `{k}`
  in any name is replaced by each, and coordinates are relative to
  `at + i × step`. The six key networks on a key board are one block.
- `supplied` lists power nets that arrive from another board. Drawn alone, a
  sheet cannot see their source, so each gets a `PWR_FLAG` in a labelled group
  at `flags_at`; a circuit's power *ports* get one automatically.

### KiCad behaviour learned the hard way

- **Power nets are named after the power symbol's value** (KiCad 8+), so the
  stock `+3V3` / `GND` symbols are used with the value set to this
  repository's net name (`V3V3_CHAIN_RH`). KiCad 7 named them after the pin.
- **A field's justification is read in the rotated symbol's frame**, so on a
  rotated part "left" draws as "right". `sch.py` flips it.
- **Library symbols that `extends` another** (KiCad 9's `74AHCT125` extends
  `74LS125`) are flattened into the sheet, as KiCad itself does.
- **Strings in a sheet file cannot contain raw newlines** — `\n` escapes only.

### Where the sheets are

| Sheet | Source |
|---|---|
| [`led-strip-drive.sch.png`](../../hardware/carrier/led-strip-drive/led-strip-drive.sch.png) | `hardware/carrier/led-strip-drive/` — the first, a single circuit |
| [`key-board-rh.sch.png`](../../hardware/boards/key-board-rh/key-board-rh.sch.png) | `hardware/boards/key-board-rh/` — the right-hand key board |
| [`key-board-lh.sch.png`](../../hardware/boards/key-board-lh/key-board-lh.sch.png) | `hardware/boards/key-board-lh/` — the left-hand key board |

### Not yet

- **Footprints and a PCB.** The sheets carry no footprints yet; that is the
  next step toward boards, and `docs/reference/pcb-pipeline.md` is the plan
  for it.
- **The main board**, which needs the other circuits' `schematic.yaml` and a
  `board.yaml` that can compose them — `board.py` only knows key clusters so
  far.
- **The commit gate.** `check-staleness.py` runs `cad.py check` but not yet
  `sch.py check` / `board.py check`, because those need KiCad installed; run
  them by hand before committing a change to a netlist, `allocation.yaml` or a
  `schematic.yaml`.
