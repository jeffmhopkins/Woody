# PCB pipeline — finished design to orderable boards, headless

**Status:** Proposed 2026-09-21. Not run. This is the tooling concept, not a
record.

The goal: take a settled schematic page set and produce a zip a fab house will
accept, entirely from a shell, re-runnably, with every script in the repo. No
GUI, no manual step that cannot be replayed.

---

## The stack

| Tool | Job | Install |
|---|---|---|
| **KiCad 9** (`kicad-cli` + `pcbnew` Python) | Board object model, DRC/ERC, all fab export | apt, needs `*.kicad.org` or `ppa.launchpadcontent.net` allowlisted |
| **SKiDL** 2.3.0 | **Circuit as Python.** Generates the netlist and runs ERC | pip — *verified downloadable from this sandbox* |
| **kiutils** 1.4.8 | Reads/writes `.kicad_sch` and `.kicad_pcb` S-expressions where `pcbnew` won't | pip — verified |
| **Freerouting** 2.x | Autorouter, Specctra DSN in / SES out | GitHub release `.jar`; Java 21 already present |
| **xvfb** | Virtual display for the two things that still want GL | apt |

Ubuntu noble's stock archive has **KiCad 7 only**, which has no
`kicad-cli pcb drc` — that arrived in KiCad 8, and the verify stage depends on
it. This is the one hard network requirement.

## The architectural choice: circuit as code, not a parsed drawing

The obvious pipeline is *parse the ASCII schematics into a netlist, then build a
board*. Don't. A one-shot parse of hand-drawn art is the highest-risk step in
the whole chain, it produces an artifact nobody can review, and it re-derives
differently every run.

**Transcribe each schematic page into a SKiDL module instead.** The
transcription is done once, by hand or by an agent, and after that:

- it is **executable**, so the netlist is *generated*, not *interpreted*
- it is **diffable**, so a change to a page shows up as a code diff
- it is **reviewable** by the same cold node-indexed method this project
  already uses for everything else
- SKiDL has **`ERC()`** built in — unconnected pins, output-to-output, power
  pins with no driver
- it is **re-runnable forever**, which is the whole point

```
pcb/src/module/
    power_entry.py        one module per schematic page
    digital.py
    pitch.py
    mods.py
    breath_rx.py
    breath_out.py
    module.py             imports the six, emits module.net
```

The netlist becomes a build artifact. `hardware/module/*.md` stays the human
source of truth, and the SKiDL modules are the machine-readable statement of the
same thing — with a parity check between them (below) so they cannot drift.

**You lose `--schematic-parity`,** because there is no `.kicad_sch`. Replace it
with something stronger: assert directly in Python that the board's netlist
equals the SKiDL netlist, ref by ref and net by net. That checks the thing
parity was a proxy for.

*(If a human-readable schematic is wanted for review, render it with `kiutils`
after the fact. It is a nice-to-have, not a pipeline dependency.)*

---

## Headless gotchas, all of which will bite

These are the ones that stop a first run dead. Handle them in `setup.sh`.

**`pcbnew` is built against the system interpreter.** It lands at
`/usr/lib/python3/dist-packages/pcbnew.py` + `_pcbnew.so`. A venv will not see
it. Either use system `python3`, or create the venv with
`--system-site-packages`, or set `PYTHONPATH=/usr/lib/python3/dist-packages`.

**The library tables do not exist until a GUI has run once.** `kicad-cli` and
`pcbnew` resolve footprints through `~/.config/kicad/9.0/fp-lib-table` and
`sym-lib-table`, which the GUI writes on first launch. Headless, copy the stock
ones from `/usr/share/kicad/template/` before anything else, and set
`HOME` to something writable.

**Two things still want OpenGL**: `kicad-cli pcb render` and, depending on
version, Freerouting. Run both under `xvfb-run -a` with
`LIBGL_ALWAYS_SOFTWARE=1`. Everything else — DRC, gerbers, drill, STEP, SVG — is
genuinely headless.

**Probe the API, don't assume it.** The Specctra helpers have changed signature
across versions. `help(pcbnew.ExportSpecctraDSN)` before writing against it.

**Freerouting wants a bounded run.** Pass `-mp <passes>` *and* wrap it in a
shell timeout. An unbounded autoroute on a dense analog board will run until the
session ends.

## Prove the toolchain on a board you can eyeball

**Before touching the real design, push a two-resistor board through every
stage.** Outline, two footprints, one net, export DSN, route, import SES, pour,
DRC, gerbers, zip. Ten minutes, and it proves every install, every API
signature, every export flag, on something where the correct answer is obvious.

`pcb/smoke/` — keep it in the repo and run it first every time. Every failure it
catches is a failure that would otherwise have surfaced halfway through the real
board.

**One thing to prove specifically: that locked tracks survive the round trip.**
The whole hand-route-then-autoroute strategy depends on KiCad marking a track
locked, the DSN export writing it into the `(wiring …)` section as protected,
and Freerouting leaving it alone. Route one trace in the smoke board, lock it,
autoroute, and diff it. If it does not survive, the strategy changes and it is
much better to learn that on two resistors.

---

## Stages

### 1. Netlist

```
python3 pcb/src/module/module.py      # SKiDL: ERC, then emit module.net
```

Fail the build on any ERC error. Then the parity check against the design BOM
(below) before anything downstream runs.

### 2. Board bring-up — `build_board.py`

Outline onto `Edge.Cuts` first; Freerouting has no boundary without it.
Load footprints, assign every pad to its net, place.

**Net classes are how trace widths happen.** Do not try to tell Freerouting
about power nets directly — define classes on the board, and `ExportSpecctraDSN`
writes them into the `.dsn` as rules the router honours:

| Class | Nets | Width |
|---|---|---|
| `Default` | signal | 0.25 mm |
| `Power` | `+12V`, `-12V`, `+5V`, `AVDD`, `PWR_GND` | **derive it** — see below |
| `Analog` | `BREATH`, pitch and mod outputs | 0.25 mm, routed by hand |

**Derive the power width rather than defaulting it.** 0.5 mm of 1 oz copper is
roughly a 1 A trace at a 10 °C rise, and the load switch's path is specified at
1.0 A. That is no margin. Compute it from IPC-2221 for the actual current and
put the arithmetic in the script.

Custom fab rules go in `<project>.kicad_dru`; the basics (clearance, min track,
via sizes) go in the board's design settings. Both are read by `kicad-cli pcb
drc`, so what the router obeys and what DRC checks are the same file.

### 3. Hand-route and lock the critical nets

Specctra cannot express any of these. They are routed before Freerouting sees
the board, and locked.

- **`AGND`** — a sense-only star, never a return. This is what makes the analog
  breath channel survive 2 m of cable.
- **`BREATH` / `AGND` pair**, connector to in-amp — matched and parallel. 60 dB
  of CMRR was already spent on one unmatched resistor.
- **`PWR_GND` / `DIG_GND`** — separate copper, one tie at the inlet.
- **Pitch feedback** — tap at the jack, compensation cap from the op-amp
  *output*, protection resistor inside the DC loop. The netlist gets this right;
  the loop *area* is a layout judgement.
- **The 1 A load-switch path** and the FET's thermal pad.

### 4. Autoroute the rest

```
pcbnew.ExportSpecctraDSN(...)
timeout 1800 xvfb-run -a java -jar freerouting.jar -de board.dsn -do board.ses -mp 100
pcbnew.ImportSpecctraSES(...)
```

Then **diff the locked nets against their pre-route geometry** before doing
anything else.

### 5. Pour — three grounds, two zones, one star

> A single `GND` pour ties `PWR_GND`, `DIG_GND` and `AGND` together. It passes
> DRC, it fabricates, and it silently destroys ADR 0004's star rule. The
> module's own ground is already the largest *live* term in the pitch error
> budget at 5.7–7.2 cents.

Freerouting does not do zones, so this happens after the import:

- **`PWR_GND` and `DIG_GND` as separate zones**, with explicit **zone
  priorities** so they do not flood into each other, and a single deliberate tie
  at the power inlet.
- **`AGND` gets no zone at all** — a routed star, plus a keepout so neither
  ground zone floods across it.
- **Thermal reliefs on every through-hole pad.** This board is hand-soldered.
  A solid connection from a THT pad into a large pour sinks the iron's heat and
  gives a cold joint or a lifted pad. Solid pours are for reflow.
- `pcbnew.ZONE_FILLER(board).Fill(board.Zones())`, then re-fill after *any*
  later change.

### 6. Verify — DRC is necessary, not sufficient

```
kicad-cli pcb drc --format json --severity-error --exit-code-violations
```

Plus assertions that each pass DRC on their own, in `verify.py`:

- board netlist **equals** the SKiDL netlist, ref by ref, net by net
- **no two nets merged**; `AGND`, `PWR_GND`, `DIG_GND` still distinct
- `AGND` tied exactly once
- locked nets geometrically unchanged by the autoroute
- every decoupling cap within ~2 mm of the pin it serves
- zero unrouted
- no copper under the connector bore or panel cutouts

Five full iterations, then stop and report rather than thrashing placement.

### 7. Fab output — and what you actually need

```
kicad-cli pcb export gerbers --layers F.Cu,B.Cu,F.Mask,B.Mask,F.Silkscreen,B.Silkscreen,Edge.Cuts
kicad-cli pcb export drill --format excellon --units mm --drill-origin absolute
kicad-cli pcb export step        # mechanical fit against the panel and enclosure
kicad-cli pcb export svg         # per layer, for review
xvfb-run -a kicad-cli pcb render # LIBGL_ALWAYS_SOFTWARE=1
```

**This board is hand-assembled, and that removes real work.** You do not need a
pick-and-place file, you do not need the fab's BOM format, and you do not need
the rotation-correction table that catches everyone doing JLC assembly. **The
fab needs gerbers and drill.** That is the whole order.

*(If assembly is ever bought: KiCad's `pos` export gives
`Ref,Val,Package,PosX,PosY,Rot,Side` and JLC wants
`Designator,Mid X,Mid Y,Layer,Rotation` — a column transform, plus per-footprint
rotation offsets. Write it then, not now.)*

## BOM: there are three, and two of them must be checked against each other

| BOM | Lives | For |
|---|---|---|
| **Design** | `hardware/bom.csv`, 11 columns, refdes-keyed, with `status` and reasoning | The source of truth for *what part and why* |
| **Generated** | from the SKiDL netlist | What the board actually has on it |
| **Purchasing** | `fab/<board>/order.csv` | Distributor PNs, pack sizes, **spares**, minimum quantities |

**`tools/check-bom-parity.py` diffs the first two by refdes** and fails on any
part present in one and not the other, or with a different value. Two sources of
truth drifting is this project's named failure mode, and this is the one place
in the pipeline where it would otherwise happen silently.

The purchasing BOM is a separate artifact because it answers different
questions: passives come in reels of 100 not 3, the sensor is bought in twos
because it is a wear part, dev boards are bought with spares, and pot tapers are
ordered per variant. Generate it from the design BOM, but do not conflate them.

**Add a `footprint` column to `hardware/bom.csv`** (12 columns — update
`CLAUDE.md` and the column check in `tools/check-staleness.py` in the same
commit). Prefer the footprints already banked in `datasheets/`; `MANIFEST.csv`
records which are vendor-issued and which are community-authored, and that
distinction has to survive into the layout.

## Where things go

`tools/check-staleness.py` scans `hardware/`, `docs/decisions/`,
`docs/reference/`, `config/`, `firmware/`, `README.md`, `ROADMAP.md` — so the
repo root keeps generated files out of the design corpus with no checker change:

```
pcb/
  setup.sh            toolchain install + the gotchas above
  smoke/              two-resistor proof board
  scripts/            build_board.py  route.py  pour.py  verify.py  export.py
  src/<board>/        SKiDL modules, one per schematic page
  <board>/            .kicad_pro  .kicad_pcb  .kicad_dru  *.net
fab/<board>/          gerbers, drill, svg, step, order.csv, <board>-fab.zip
```

**Nothing generated under `hardware/`.** That directory is reviewed prose.

---

## Precursors

Per board, before the pipeline is worth starting:

1. Every BOM row `selected`, with a real package and a footprint. A placement
   built around a wrong footprint is the one expensive thing to redo here.
2. No *topological* item left in that page set's **Still open** — values and
   bench questions are fine, redraws are not.
3. Tracked figures the layout depends on out of `disputed` in
   `config/figures.yaml`.
4. Mechanical inputs settled: panel cutouts, board outline, connector
   orientation, standoffs.

Then: module PCB and its panel (E12), then carrier and the four cluster boards
(E13). ROADMAP puts them in that order because the carrier will spin at least
once.
