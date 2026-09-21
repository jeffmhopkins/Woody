# P7 — Fab deliverables: what a board house actually needs

**Subject:** `docs/reference/pcb-pipeline.md` §7 "Fab output — and what you
actually need", plus everything §7 implies and omits.

**Method:** cold. I did not read `docs/review/**` or any other agent's output.
Claims are tagged `[source]` (repo path, or upstream repo + path + branch),
`[test]` (I ran it in this sandbox), `[calc]`, `[from memory]`.

**Reachability note:** JLCPCB/PCBWay vendor sites are blocked, as briefed. I
did not guess at their requirements. Instead I read the two independent
open-source codebases that encode those requirements and are themselves
derived from vendor documentation: **GerberZipper**
(`g200kg/kicad-gerberzipper`, `plugins/Manufacturers/*.json` — six vendor
profiles) and **KiBot** (`INTI-CMNB/KiBot`,
`kibot/resources/config_templates/{JLCPCB,PCBWay,Elecrow}.kibot.yaml`, whose
header comments state they are "Based on setting used by Gerber Zipper").
Where all six profiles agree, I treat that as settled. `[source]`

**Version note, and it matters for half this report:** the plan pins **KiCad 9**
(`docs/reference/pcb-pipeline.md:16,22`). I checked every flag below against
the **`9.0` branch** of `gitlab.com/kicad/code/kicad`, not just `master`. Three
of the most useful things I found are `master`-only. They are marked.

---

## 1. Verdict table

| # | Claim in the plan | Verdict | Why |
|---|---|---|---|
| F-01 | Gerber layer list `F.Cu,B.Cu,F.Mask,B.Mask,F.Silkscreen,B.Silkscreen,Edge.Cuts` | **Correct and complete** | Exactly matches all six vendor profiles. Nothing is missing. |
| F-02 | Layer names spelled `F.Silkscreen` (not `F.SilkS`) | **Correct** | CLI accepts both spellings. I nearly filed this as a defect; it is not one. |
| F-03 | Neither export command has an input file or `-o` | **Broken — will not run** | Both are mandatory. |
| F-04 | `kicad-cli pcb export drill … --units mm` | **Broken — `--units` is not a drill flag** | The flag is `-u` / `--excellon-units`. |
| F-05 | `--drill-origin absolute` | Correct but redundant | It is already the default. Harmless; keep it as documentation. |
| F-06 | PTH/NPTH left at default | **Wrong for this board** | KiCad's CLI default is *merged*. Four of six vendor profiles want *separate*. |
| F-07 | No drill map requested | **Half right** | Right for the fab's zip, wrong for your own review. `--generate-map`, not `--generate-map-file`. |
| F-08 | Protel vs `.gbr` extensions, not mentioned | Right by luck | Protel is the KiCad CLI default and is what all six profiles want. **Do not** pass the disable flag. Its real spelling is `--no-protel-ext`. |
| F-09 | X2 attributes, not mentioned → left ON | **Wrong** | All six vendor profiles disable X2 *and* netlist attributes. |
| F-10 | Aperture macros, not mentioned → left ON | **Wrong for a cheap house** | All six profiles disable them. |
| F-11 | `.gbrjob`, not mentioned | **Missing — and it is emitted whether you want it or not** | No CLI flag suppresses it. It is also the only machine-readable stackup statement you will produce, and it will be blank. |
| F-12 | "The fab needs gerbers and drill. That is the whole order." | **FALSE. This is the headline defect.** | See §3. At least eight order facts live nowhere in gerbers or drill. |
| F-13 | "You do not need a pick-and-place file / BOM / rotation table" | **True for the fab, false for you** | Correct that the *fab* needs none. But hand assembly creates a need the plan then never meets. |
| F-14 | No paste layers | **Correct** | Confirmed against both toolchains. |
| F-15 | No F.Fab / Courtyard / Adhesive | **Correct** | Not manufacturing data. |
| F-16 | No fab-notes / drawing layer | **Missing, but not as a gerber** | Ship a PDF + a plain-text order sheet. Reasons below. |
| F-17 | STEP "for mechanical fit against the panel and enclosure" | **Half right, and aimed at the wrong artefact** | STEP is right for depth-behind-panel. It is useless for the two things that actually get cut. |
| F-18 | Stackup / thickness / copper / finish / mask colour | **Absent from the whole repo, not just the plan** | And `1 oz` is asserted inside this very file and used to derive a trace width. |
| F-19 | "The panel" treated as a pipeline output | **Category error** | The panel is 2 mm aluminium from a laser cutter. It is not a PCB and not this vendor. |
| F-20 | V-score / mouse bites / panelisation | Correctly absent | But say so explicitly on the order sheet. |
| F-21 | Impedance control | Correctly absent | Genuinely not needed here. Say so on the order sheet so the quote does not stall. |
| F-22 | Electrical test | **Missing, and it is the cheapest insurance on this board** | KiCad exports an IPC-D-356 netlist for exactly this and the plan never mentions it. |
| F-23 | Verification: `export svg` + `render` "for review" | **Verifies the wrong object** | Both read the `.kicad_pcb`. Neither touches the files you are about to pay for. |
| F-24 | An invalid `--layers` token | **Silent** | KiCad reports it and *continues, exit 0*. A typo ships a board with no soldermask. |
| F-25 | Zones and the gerber export | **Unguarded on KiCad 9** | `--check-zones` exists only on `master`. On 9.0 nothing re-fills before plot. |

---

## 2. The corrected, complete export command set

Every flag below was read out of the KiCad **9.0** branch source, not from
memory. Sources are cited per block.

```sh
set -euo pipefail

BOARD=pcb/module/module.kicad_pcb
OUT=fab/module            # what you pay for
REV=fab/module/_review    # what you look at, and never zip
mkdir -p "$OUT/gerber" "$REV"
```

### 2.0 Precondition: zones must be current *in the saved file*

`kicad-cli pcb export gerbers` on 9.0 has no zone-refill step. The
`--check-zones` flag that adds one exists **only on `master`** — I read it in
`kicad/cli/command_pcb_export_gerber.cpp` on `master` (`ARG_CHECK_ZONES`,
wired to `aJob->m_checkZonesBeforePlot`) and grepped the 9.0 copy of the same
file for `check_zones|checkZones`: **no match**. `[source: gitlab.com/kicad/code/kicad, kicad/cli/command_pcb_export_gerber.cpp @ master vs @ 9.0]`
On `master`, `pcbnew_jobs_handler.cpp` guards the whole plot loop with
`if( aGerberJob->m_checkZonesBeforePlot ) … FillAllZones(…)`. `[source: same repo, pcbnew/pcbnew_jobs_handler.cpp @ master, ~line 1702]`

So on KiCad 9 the refill has to be yours, and it has to be **saved**:

```sh
python3 pcb/scripts/pour.py --fill --save   # ZONE_FILLER(board).Fill(...); board.Save()
```

The plan's §5 already says "re-fill after *any* later change". What it does not
say is that the export reads the file from disk, so an in-memory fill that was
never saved plots as stale copper. Make `pour.py --save` a hard precondition of
`export.py`, not a convention.

### 2.1 Gerbers

```sh
kicad-cli pcb export gerbers "$BOARD" \
  --output "$OUT/gerber/" \
  --layers F.Cu,B.Cu,F.Mask,B.Mask,F.Silkscreen,B.Silkscreen,Edge.Cuts \
  --no-x2 \
  --no-netlist \
  --disable-aperture-macros \
  --subtract-soldermask \
  --precision 6 \
  --ev
```

Flag by flag:

- **positional `"$BOARD"` and `--output`.** Both mandatory and both absent from
  the plan. `PCB_EXPORT_BASE_COMMAND` is constructed `IO_TYPE::FILE,
  IO_TYPE::DIRECTORY`, and `populateJob()` hard-fails with *"Board file does not
  exist or is not accessible"* on a missing input. `-o`/`--output` is added by
  `addCommonArgs`. `[source: kicad/cli/command_pcb_export_gerber.cpp @ 9.0; kicad/cli/command.cpp @ master, the `add_argument( "-o", ARG_OUTPUT )` block]`
  The output must be a **directory** for `gerbers` (plural); it is a file for
  `gerber` (singular). **F-03.**
- **`--layers` as written is right. F-01.** All six GerberZipper profiles map
  exactly `F.Cu, B.Cu, F.SilkS, B.SilkS, F.Mask, B.Mask, Edge.Cuts` (+ inner
  copper, + paste only in the `_w-stencil` variants). `[source: g200kg/kicad-gerberzipper, plugins/Manufacturers/{JLCPCB,PCBWay,Elecrow,FusionPCB,PCBGogo,P-Ban}.json]`
  KiBot's shared default is the same seven: `_KIBOT_GERBER_LAYERS: copper,
  F.SilkS, B.SilkS, F.Mask, B.Mask, Edge.Cuts`. `[source: INTI-CMNB/KiBot, kibot/resources/config_templates/JLCPCB.kibot.yaml, definitions block]`
  **Nothing is missing from this list.** Do not add to it.
- **`F.Silkscreen` is accepted. F-02.** I nearly filed this as a defect because
  `LSET::NameToLayer()` in 9.0 only knows `"F.SilkS"`. `[source: common/lset.cpp @ 9.0, line 126]`
  But the CLI does not use that function. `PCBNEW_JOBS_HANDLER::convertLayerArg()`
  builds **two** maps — `layerMasks[ LSET::Name(layer) ]` (file names, `F.SilkS`)
  and `layerGuiMasks[ LayerName(layer) ]` (GUI canonical, `F.Silkscreen`) — and
  tries the second if the first misses. `[source: pcbnew/pcbnew_jobs_handler.cpp @ 9.0, lines 330–346 and 375–390]`
  Both spellings work. Recording this so the next reviewer does not re-file it.
- **`--no-x2` and `--no-netlist`. F-09.** KiCad's CLI leaves both ON:
  `m_useX2Format = !ARG_NO_X2` and `m_includeNetlistAttributes = !ARG_NO_NETLIST`.
  `[source: kicad/cli/command_pcb_export_gerber.cpp @ 9.0, lines 129 and the adjacent populateJob block]`
  Every one of the six vendor profiles sets `"UseExtendedX2format": false` and
  `"IncludeNetlistInfo": false` — JLCPCB, PCBWay, Elecrow, FusionPCB, PCBGogo
  **and** P-Ban, which is the one profile that keeps X2 for its *drill map* and
  still disables it for the plot. `[source: g200kg/kicad-gerberzipper, all six Manufacturers/*.json]`
  KiBot mirrors it: `use_gerber_x2_attributes: false`,
  `use_gerber_net_attributes: false`. `[source: INTI-CMNB/KiBot, JLCPCB/PCBWay/Elecrow templates]`
  Six-for-six is as close to settled as this gets. X2 is not *wrong*; it is
  extra `%TO…` object attributes and `%TF…` file attributes that a cheap
  auto-quote parser has no reason to handle. The downside of turning it off is
  nil for a one-off.
- **`--disable-aperture-macros`. F-10.** Same six-for-six:
  `"disable_aperture_macros": true` in KiBot, and the GerberZipper plugin sets
  the equivalent `PCB_PLOT_PARAMS` field. Costs you a larger file and nothing
  else.
- **`--subtract-soldermask`.** Split four/two across profiles (JLCPCB, Elecrow,
  PCBGogo true; PCBWay, FusionPCB, P-Ban false) `[source: same six JSONs, "SubtractMaskFromSilk"]`.
  Take it. It clips silkscreen out of mask openings, and this is a
  **hand-soldered** board: silk ink on a pad is a wetting problem you will meet
  one joint at a time with an iron.
- **`--ev`, and deliberately *not* `--erd`.** `--ev` drops value text from the
  silk, `--erd` drops reference designators. JLCPCB's profile is
  `PlotFootprintValues: false, PlotFootprintReferences: true` `[source: JLCPCB.json]`
  and that is exactly right here for a reason the profile does not know:
  **you are placing every part by hand from `hardware/bom.csv`, which is
  refdes-keyed** `[source: /home/user/Woody/CLAUDE.md, "hardware/bom.csv is 11 columns"]`.
  Refdes on the silk is your assembly aid. Values are clutter that will not fit
  on 0805s anyway.
- **`--precision 6`.** Already the default; all six profiles want 4.6 format,
  which is `--precision 6`. `[source: "CoodinateFormat46": true in all six JSONs; gerber_precision: 4.6 in KiBot]`
- **Do NOT pass `--no-protel-ext`. F-08.** KiCad's CLI default *is* Protel:
  `m_useProtelFileExtension = !m_argParser.get<bool>( ARG_NO_PROTEL_EXTENSION )`
  with `#define ARG_NO_PROTEL_EXTENSION "--no-protel-ext"`. `[source: kicad/cli/command_pcb_export_gerber.cpp @ 9.0 line 131; command_pcb_export_gerber.h @ 9.0 line 35 — identical on master]`
  All six profiles want Protel (`.gtl .gbl .gts .gbs .gto .gbo .gm1`), and so
  does the one **real, fabricated, shipped** Eurorack fab package I pulled:
  Ornament & Crime's `ornament_2e_enc.zip` is `.gm1 .gbl .gtl .gts .gbo .gto`
  plus a drill `.txt`. `[source: github.com/mxmxmx/O_C, hardware/gerbers/ornament_2e_enc.zip — I extracted and listed it]`
  Note the answer to "which way should the flag go in 2026": **you never pass
  it.** The flag only exists to opt *out* of the thing you want.
- **Not `--board-plot-params`.** That flag makes the export read plot settings
  stored in the `.kicad_pcb` instead of the command line. `[source: kicad/cli/command_pcb_export_gerbers.cpp, ARG_USE_BOARD_PLOT_PARAMS]`
  For a pipeline whose whole premise is "every script in the repo,
  re-runnably", reading hidden state out of the board file is the wrong
  direction. Keep the flags explicit.

**F-11, the `.gbrjob` you did not ask for.** `JOB_EXPORT_PCB_GERBERS` is
constructed with `m_createJobsFile( true )` and there is **no CLI flag** to set
it false — the only `add_argument` the `gerbers` subcommand adds on top of the
base is `--board-plot-params`. `[source: common/jobs/job_export_pcb_gerbers.cpp, constructor; kicad/cli/command_pcb_export_gerbers.cpp]`
So `"$OUT/gerber/module-job.gbrjob"` appears whether the plan wants it or not.
Both KiBot vendor templates explicitly set `create_gerber_job_file: false`.
`[source: INTI-CMNB/KiBot, JLCPCB and PCBWay templates]` Decide, and write the
decision down — see §3.2, because this file is the crux of the stackup problem.

### 2.2 Drill — two runs, not one

```sh
# (a) what goes in the zip: no map, no report
kicad-cli pcb export drill "$BOARD" \
  --output "$OUT/gerber/" \
  --format excellon \
  --excellon-units mm \
  --excellon-zeros-format decimal \
  --excellon-oval-format alternate \
  --excellon-separate-th \
  --drill-origin absolute

# (b) what you review: map + report, into a directory you never zip
kicad-cli pcb export drill "$BOARD" \
  --output "$REV/" \
  --format excellon --excellon-units mm --excellon-separate-th \
  --drill-origin absolute \
  --generate-map --map-format pdf \
  --generate-report --report-path "$REV/drill-report.rpt"
```

- **`--units mm` does not exist. F-04.** The drill command's argument list is
  `--format --excellon-mirror-y --excellon-min-header --excellon-separate-th
  --excellon-zeros-format --excellon-oval-format --gerber-precision
  --excellon-units --generate-map --generate-report --report-path
  --generate-tenting --map-format --drill-origin`, and units is added as
  `add_argument( "-u", ARG_EXCELLON_UNITS )`. There is no `--units`. `[source: kicad/cli/command_pcb_export_drill.cpp @ 9.0, the #define block at lines 32–44 and line 73 — master is identical apart from --generate-tenting]`
  KiCad's CLI uses p-ranav `argparse`, which does not do Python-style unambiguous
  prefix matching, so this is an unrecognised-argument failure rather than a
  silent no-op. Either way the command as written in the plan is not a command
  that runs.
- **`--excellon-separate-th`. F-06, and this is the one that can cost money.**
  The job field is `m_excellonCombinePTHNPTH = !m_argParser.get<bool>(
  ARG_EXCELLON_SEPARATE_TH )` `[source: same file, line 252]` — so the CLI
  **default is merged**, one `.drl` containing both plated and non-plated holes.
  JLCPCB, Elecrow and PCBGogo all want separate (`"MergePTHandNPTH": false`,
  with an explicit `"NPTH": "*-NPTH.drl"` filename); PCBWay, FusionPCB and P-Ban
  merge. `[source: the six Manufacturers/*.json]` KiBot's JLCPCB template:
  `pth_and_npth_single_file: false, pth_id: '-PTH', npth_id: '-NPTH'`.
  Separate is the safe default because it is unambiguous in both directions —
  a merged file leaves "which of these do I plate?" to the CAM operator's
  parser. On this board that question has a real answer: the Eurorack panel
  mounting pattern is M3 clearance (⌀3.2 mm) `[source: /home/user/Woody/datasheets/MANIFEST.csv, "Eurorack 3U panel" rows — HOLE_DIA=3.2]`
  and the etherCON's two chassis holes are ⌀3.2 mm min clearance `[source: /home/user/Woody/docs/decisions/0004-cv-interface-module.md, "two clearance holes only, diagonally opposite, ⌀3.2 mm min, at 19 ±0.1 mm × 24 ±0.1 mm"]`.
  Those are NPTH. Get them plated and the ⌀ moves and the tolerance on a
  ±0.1 mm pattern is gone.
- **`--generate-map`, not `--generate-map-file`.** The flag the slice brief
  asked about does not exist under that name. `[source: #define ARG_GENERATE_MAP "--generate-map"]`
  Values for `--map-format`: `pdf` (default), `gerberx2`, `ps`, `dxf`, `svg`.
- **Map in the zip: no. F-07.** JLCPCB, PCBWay, Elecrow, FusionPCB and PCBGogo
  all have `"DrillMap": ""` — no map file at all. Only P-Ban asks for one
  (`*-drl_map.gbr`) and a `.rpt`. `[source: the six Manufacturers/*.json]`
  A stray `.gbr` sitting next to seven Protel-extension files is exactly the
  kind of thing an auto-quote parser reads as an eighth layer or a second board
  outline. Generate it for **your** eyes, in `$REV`, and keep the zip to the
  seven gerbers + two drill files.
- **`--excellon-zeros-format decimal` and `--excellon-oval-format alternate`**
  are both already the defaults `[source: same file, the `.default_value` calls]`
  and both match the JLCPCB profile (`"DecimalFormat": true`,
  `"RouteModeForOvalHoles": false`). Stated explicitly because a default that
  matters should be visible in the script, not inferred.
- **`--drill-origin absolute`. F-05.** Already the default, and correct: all
  six profiles set `"UseAuxOrigin": false`. Keep it written down.
- **`--excellon-min-header`: do not pass it.** Only PCBWay wants a minimal
  header (`"MinimalHeader": true`). The full header carries KiCad's
  `;TYPE=PLATED` / tool-size comments, which is what makes a *merged* file
  readable at all, and is free insurance in a separated one.

### 2.3 The three exports the plan does not have

```sh
# IPC-D-356 netlist — hand this to the fab with the E-test option. F-22.
kicad-cli pcb export ipcd356 "$BOARD" --output "$OUT/module.ipc"

# 1:1 fab drawing / paper check. F-16, F-17.
kicad-cli pcb export pdf "$BOARD" \
  --output "$REV/module-fab-drawing.pdf" \
  --layers Edge.Cuts,User.Drawings,User.Comments,F.Fab \
  --mode-single --ibt

# Panel cut file — DXF, not STEP, and a different vendor. F-19.
kicad-cli pcb export dxf panel/panel.kicad_pcb \
  --output "$REV/panel.dxf" \
  --layers Edge.Cuts,User.Drawings \
  --output-units mm --uc --mode-single
```

`pcb export ipcd356`, `pcb export pdf`, `pcb export dxf`, `pcb export odb` and
`pcb export ipc2581` all exist on the 9.0 branch — I checked each file returns
HTTP 200 on `gitlab.com/kicad/code/kicad/-/raw/9.0/kicad/cli/`. `[test]`
DXF flags: `--output-units` (`--ou`), `--use-contours` (`--uc`),
`--use-drill-origin` (`--udo`), `--mode-single`/`--mode-multi`. `[source: kicad/cli/command_pcb_export_dxf.cpp @ 9.0]`
`--uc` matters: it plots graphics as **contours** rather than centrelines,
which is what a laser cutter needs for anything that is not a bare outline.

### 2.4 STEP — keep it, aim it, and stop overclaiming it. F-17

```sh
kicad-cli pcb export step "$BOARD" \
  --output "$REV/module.step" \
  --subst-models --no-unspecified --no-dnp --force
```

Flags confirmed present on 9.0: `--drill-origin --grid-origin --no-unspecified
--no-dnp --subst-models --force --min-distance --user-origin --board-only
--cut-vias-in-body --no-board-body --no-components --include-tracks
--include-pads --include-zones --include-silkscreen --include-soldermask
--fuse-shapes --fill-all-vias --no-optimize-step --net-filter --format`. `[source: kicad/cli/command_pcb_export_3d.cpp @ 9.0]`

**Is STEP the right format for checking against a wooden enclosure and an
aluminium plate? Partly — and it is the wrong one for the two things that
actually get cut.**

- STEP **is** right for the one genuinely 3-D question on this module: how far
  the etherCON sticks out behind the panel against how far behind the panel the
  PCB sits. The repo has the numbers — etherCON flange 26 × 31 mm with
  **34.55–36.3 mm behind the panel**, jacks putting the PCB about 7 mm behind
  it `[source: /home/user/Woody/config/figures.yaml, panel-height-budget `decided_by`; /home/user/Woody/docs/decisions/0004-cv-interface-module.md, "the connector body extends 30–40 mm behind the panel while the jacks put the PCB about 7 mm behind it"]`.
  That is a solid-body interference question and STEP answers it.
- STEP is **useless** for the panel and the enclosure, because neither is
  machined from a solid. ADR 0009 names the vendor and the format: *"OSH Cut
  will cut aluminium, acrylic and plywood **from a DXF**"* `[source: /home/user/Woody/docs/decisions/0009-enclosure-construction.md, line ~215]`.
  And `hardware/bom.csv` row `PANEL` reads *"2mm aluminium, 10HP x 3U (50.50 x
  128.5mm) … Laser or waterjet **from DXF** — SAME vendor and order as the key
  plate"* `[source: /home/user/Woody/hardware/bom.csv line 21]`.
  A STEP file cannot be sent to that vendor. **The pipeline produces no DXF at
  all.**
- STEP is also useless for the check ADR 0004 explicitly mandates: *"Print the
  panel at 1:1 on paper and check it is actually usable before cutting"*, and
  again *"Still a 1:1 paper check at M4 … Print it and lay the real parts on
  it."* `[source: /home/user/Woody/docs/decisions/0004-cv-interface-module.md]`
  That is a 1:1 PDF. The pipeline produces no PDF either.
- Two practical STEP caveats the plan should carry. (i) Without 3D models
  assigned to footprints the export gives you a bare board extrusion and
  nothing to interfere with — `--subst-models` and a populated
  `KICAD9_3DMODEL_DIR` are preconditions, not options. `[from memory, flagged as such]`
  (ii) If all you want is the outline against the enclosure, `--board-only` is
  seconds instead of minutes.

**So: STEP for depth-behind-panel, DXF for anything that gets cut, 1:1 PDF for
the paper check. The plan has one of three.**

### 2.5 The zip

The plan's tree ends at `fab/<board>/…, <board>-fab.zip` with no statement of
what goes in it. Specify it, because the one real shipped Eurorack fab zip I
opened demonstrates the failure: `ornament_2e_enc.zip` contains a nested
directory **and a full set of macOS `__MACOSX/._*` resource-fork files**.
`[source: github.com/mxmxmx/O_C, hardware/gerbers/ornament_2e_enc.zip — listed with zipfile]`
When I pointed a strict parser at that zip it aborted before reading a single
aperture: `SystemError: Ambiguous layer names: top copper
(._ornamentv3_2e_encoders_copperTop.gtl, ornamentv3_2e_encoders_copperTop.gtl), …`
`[test: gerbonara 1.5.0, `gerbonara meta`]`. A fab's parser will do something
similar or, worse, something different and silent.

Rules: **flat, no directories, no dotfiles, no `__MACOSX`, exactly nine files**
(7 gerbers + `-PTH.drl` + `-NPTH.drl`), deterministic mtimes so the zip hashes
reproducibly, and the SHA-256 of the zip recorded next to it with the git SHA
that produced it. That last is not ceremony — it is the same discipline
`datasheets/MANIFEST.csv` already enforces on every banked document `[source: /home/user/Woody/CLAUDE.md, §3]`,
applied to the one artefact in this repo you spend money on.

---

## 3. What is missing from the order package entirely

> **"The fab needs gerbers and drill. That is the whole order."** — the plan,
> §7. This is the claim I was asked to break, and it breaks cleanly. Gerbers
> and drill are the *geometry*. An order is geometry **plus the physical
> specification of the thing the geometry is cut into**, and not one byte of
> that specification is in a gerber.

### 3.1 Eight order facts that exist in no exported file

| Fact | Where it is now | Consequence of leaving it to the default |
|---|---|---|
| Board thickness | **nowhere in the repo** | 1.6 mm is the usual default, but Eurorack depth behind the panel is already tight |
| Copper weight | **asserted once, in `pcb-pipeline.md` itself**, as "1 oz" | see §3.3 — this one is load-bearing |
| Base material / Tg | nowhere | FR-4 TG130 is fine; say it |
| Surface finish | nowhere | HASL / lead-free HASL / ENIG. You hand-solder THT and 0805 with an iron — leaded HASL is the friendliest, ENIG the flattest |
| Solder mask colour | nowhere | affects nothing electrical; affects the module you look at for years |
| Silkscreen colour | nowhere | ditto |
| Fab / order-number marking | nowhere | cheap houses **print their order number on the board** unless told otherwise or given a place for it. On a module whose silkscreen is a visible product surface, this is worth one line |
| Electrical test | nowhere | see §3.4 |

None of these is in the gerbers, none is in the drill file, and the plan does
not produce an order sheet. **Add `fab/<board>/README-FAB.txt`**, generated,
and put all eight in it, plus the three explicit negatives from §3.5.

### 3.2 There *is* one machine-readable place for some of it, and the plan will ship it blank

`kicad-cli pcb export gerbers` writes `<board>-job.gbrjob` unconditionally
(§2.1, F-11). `GERBER_JOBFILE_WRITER` fills it from
`GetDesignSettings().GetBoardThickness()` and
`GetDesignSettings().GetStackupDescriptor()`, emitting
`GeneralSpecs.BoardThickness`, `GeneralSpecs.Finish`,
`GeneralSpecs.ImpedanceControlled`, castellated-pads and edge-plating flags,
and a full `MaterialStackup` array with per-layer thickness, material and
colour. `[source: pcbnew/exporters/gerber_jobfile_writer.cpp, addJSONGeneralSpecs/addJSONMaterialStackup, lines ~254–290 and ~556–660]`

All of that comes from **Board Setup → Physical Stackup**, stored in the
`.kicad_pcb`. The plan's `build_board.py` never sets it. The same writer even
warns about exactly this state: `if( m_reporter && !uptodate &&
…m_HasStackup ) m_reporter->Report( _( "Board stackup settings not up to
date." ), RPT_SEVERITY_ERROR )` `[source: same file, line ~568]`.

Two ways out, and either is fine as long as it is chosen on purpose:

1. **Set the physical stackup in `build_board.py`** (thickness, copper weight,
   finish, mask/silk colour), ship the `.gbrjob`, and now the zip carries its
   own specification. This is the version that matches the rest of this
   project's philosophy.
2. **Delete the `.gbrjob` before zipping** — what KiBot's JLCPCB and PCBWay
   templates do (`create_gerber_job_file: false`) — and put everything in
   `README-FAB.txt` instead.

What is not fine is the current plan, which does neither, and therefore ships
an empty stackup declaration it does not know it is shipping.

### 3.3 F-18 is this project's named failure mode, pointed at the fab

`CLAUDE.md` §1: *"If a quantity is in that register, the owning document states
it and every other document cites it by name."* `[source: /home/user/Woody/CLAUDE.md]`

I grepped the whole design corpus for `1 oz|1oz|35 µm|copper weight|1.6 mm|
board thickness|ENIG|HASL|solder mask`. Outside of `docs/log`, `docs/research`
and `docs/review`, there are **three** hits and none of them is a tracked
figure: `ks33-geometry.md:68` (plate thickness, unrelated),
`digital-and-supervision.md:229` (a false match on "measuring"), and
`pcb-pipeline.md:183` itself. `[test: grep over config/, docs/decisions/, docs/reference/, hardware/, firmware/, README.md, ROADMAP.md]`
`config/figures.yaml` has 21 ids; none is a stackup parameter. `[test]`

And the single assertion is load-bearing. `pcb-pipeline.md:183`: *"0.5 mm of
**1 oz copper** is roughly a 1 A trace at a 10 °C rise, and the load switch's
path is specified at 1.0 A … Compute it from IPC-2221 for the actual current
and put the arithmetic in the script."* `[source: /home/user/Woody/docs/reference/pcb-pipeline.md:183]`

So the copper weight is: (a) an input to an IPC-2221 derivation that sets a
power trace width on a 1.0 A path, (b) a number the fab must be told, (c) stated
in exactly one place, in prose, in a document that is not its owner, and (d) not
in `config/figures.yaml`. If anyone ever orders 2 oz outer — which is a
one-click option and a tempting one on a 1 A path — the trace width derivation
in this file becomes silently wrong and `tools/check-staleness.py` cannot see
it, because it greps for values and `1 oz` is not a tracked value `[source: /home/user/Woody/CLAUDE.md, §4 "What the checker cannot catch"]`.

**Recommendation:** add four entries to `config/figures.yaml` —
`pcb-copper-weight`, `pcb-thickness`, `pcb-surface-finish`, `pcb-layer-count` —
owned by `docs/reference/pcb-pipeline.md`, and make `README-FAB.txt` and the
IPC-2221 derivation both cite rather than restate. This is a four-line change
that closes a class of defect this project has found ninety times.

### 3.4 Electrical test, and the file that makes it worth buying. F-22

For a one-off 2-layer prototype it is tempting to skip E-test. Don't, on *this*
board, and the reason is in the plan's own §5:

> *"A single `GND` pour ties `PWR_GND`, `DIG_GND` and `AGND` together. It
> passes DRC, it fabricates, and it silently destroys ADR 0004's star rule."*
> `[source: /home/user/Woody/docs/reference/pcb-pipeline.md:179–182]`

The plan is alert to that failure in *layout*. The same failure happens in
*fabrication* — an under-etched hairline between two adjacent pours — and it is
invisible to every check in §6, because §6 checks the design, not the artefact.
On a board whose whole analog argument is three separated grounds, a
fabrication short between `PWR_GND` and `AGND` presents as "the pitch is
slightly wrong", which is the single hardest symptom to diagnose in this
instrument and the one ADR 0006 already budgets 5.7–7.2 cents for.

Ship an **IPC-D-356 netlist** with the order (`kicad-cli pcb export ipcd356`,
§2.3) and tick E-test. It makes the fab's flying probe compare the board
against *your intended netlist* rather than against a net list it reverse-
engineered from your own gerbers — which is the difference between catching a
short and confirming one.

### 3.5 Three explicit negatives — write them down so they are decisions

- **Panelisation / V-score / mouse bites / tab-route: none.** One board,
  ~45 × 110 mm, ordered as single pieces. `[source: task brief; consistent with hardware/bom.csv]`
  At that size there is no minimum-order geometry to work around. Say "single
  pieces, no panel" on the order sheet so nobody helpfully panelises five up.
- **Impedance control: not required.** There is no controlled-impedance net on
  this board. The only fast digital run in the system is SPI, and ADR 0009 puts
  it *inside the instrument* — *"At 18 inches overall the longest run is more
  like 14–16 inches, which is comfortable for SPI with ordinary care"* `[source: /home/user/Woody/docs/decisions/0009-enclosure-construction.md]`
  — not on the module PCB. The module's signals are DC-to-audio analog CV and a
  serial link over 2 m of Cat5. Nothing on a 45 × 110 mm 2-layer board here has
  an edge rate that cares about Zo. Note it explicitly: an unanswered
  "impedance?" on a quote form stalls the order.
- **Castellation, edge plating, gold fingers, blind/buried vias, countersinks:
  none.** The `.gbrjob` would assert the first two as `false` if the stackup
  were set; on the order sheet, say them.

### 3.6 F-13 — "no pick-and-place file" is right, and then the plan stops too soon

The plan is correct that the *fab* needs no position file, no LCSC BOM and no
rotation-correction table, and correct to defer the JLC column transform. But
it draws the wrong conclusion from it — that hand assembly is purely a
*subtraction* of work.

It is not. It moves the work to you. The plan already produces a refdes-keyed
design BOM `[source: /home/user/Woody/hardware/bom.csv]` and is about to add a
`footprint` column (§"BOM", 12 columns). The missing artefact is the thing that
joins those to the board: an **interactive HTML BOM**. `InteractiveHtmlBom`
runs headless — its CLI checks `INTERACTIVE_HTML_BOM_NO_DISPLAY` and only
demands wxPython if that is unset `[source: github.com/openscopeproject/InteractiveHtmlBom, InteractiveHtmlBom/generate_interactive_bom.py, main()]`
— reads the `.kicad_pcb` directly, and gives you a click-a-row-highlight-the-pad
placement aid for a board you will populate one 0805 at a time with an iron.
It costs one line in `export.py` and it is the single highest-value output the
pipeline is not producing.

That is the honest version of the hand-assembly claim: *the fab needs no
assembly data; you do, and it is a different file.*

### 3.7 F-19 — the panel is not a fab deliverable, and the pipeline says it is

`ROADMAP.md` E12 is "Module PCB + panel" and the plan's Precursors end with
*"Then: module PCB and its panel (E12)"* `[source: /home/user/Woody/docs/reference/pcb-pipeline.md, "Precursors"; /home/user/Woody/ROADMAP.md:53]`,
with everything filed under `fab/<board>/`. That bundles two items that share
nothing:

| | Module PCB | 10HP panel |
|---|---|---|
| Material | FR-4, 2 layer | **2 mm aluminium** |
| Vendor | prototype board house | **laser/waterjet — same order as the key plate** |
| Format | gerbers + Excellon | **DXF** |
| Source | `.kicad_pcb` | not a KiCad board today |

`[source: /home/user/Woody/hardware/bom.csv line 21 (PANEL row); /home/user/Woody/docs/decisions/0009-enclosure-construction.md]`

Two consequences the plan should carry:

1. `fab/<board>/` must not imply the panel. Give the panel its own directory
   and its own output (`mechanical/export/` already exists and is **empty** —
   as are `mechanical/cad/` and `mechanical/drawings/` `[test: ls]`).
2. **If** the panel is ever drawn as a `.kicad_pcb` to reuse KiCad's geometry —
   and there is a strong reason to, because the repo has already banked a real
   fabricated 3HP Eurorack panel *as a `.kicad_pcb`* with its geometry measured
   `[source: /home/user/Woody/datasheets/MANIFEST.csv, "A REAL, FABRICATED 3HP Eurorack panel (KiCad PCB) … outline 15.000 x 128.500 mm. Two obround mounting SLOTS, 3.2mm wide (R1.6 end arcs)…"]`
   — then note that **the Doepfer mounting features are obround slots, not
   round holes**. In a PCB flow those are either routed ovals in the Excellon
   (`--excellon-oval-format`, and `alternate`/G85 vs `route` is a real
   divergence between fabs — P-Ban sets `"RouteModeForOvalHoles": true`, JLCPCB
   sets it false `[source: the six Manufacturers/*.json]`) or cuts on
   `Edge.Cuts`. In a laser-cut aluminium flow they are just DXF geometry and
   none of this applies. Either way, slots are the single most commonly
   mis-fabricated feature on a Eurorack panel and the plan does not mention
   them.

Answering the slice question directly: **the panel needs no gerber package at
all, no finish, and no copper — because it is not a PCB.** If that ever changes
to an FR-4 panel (a legitimate cheaper option), it becomes a *different*
conversation: no copper at all is the wrong answer even then, because a panel
PCB with zero copper warps and most houses will refuse or surcharge it; the
convention is a full ground pour on both sides with the graphics in silkscreen,
and then finish and mask colour become the product's appearance rather than a
technicality.

---

## 4. How to verify gerbers headless, before paying

### 4.1 The plan verifies the wrong object. F-23

```
kicad-cli pcb export svg         # per layer, for review
xvfb-run -a kicad-cli pcb render
```

Both read `module.kicad_pcb`. So does `kicad-cli pcb drc`. So does every
assertion in §6. **Nothing in the plan ever opens a file from the zip.** The
entire §7 export step — layer selection, extension convention, X2, aperture
macros, drill merge, zone-fill staleness, the `.gbrjob` nobody asked for — sits
*downstream* of every check the plan performs. That is precisely where money is
lost, because it is the only stage whose output is the thing you upload.

**Rule: verification runs against the unzipped contents of the zip you are
about to send, not against the board that produced it.**

### 4.2 F-24 — a bad `--layers` token does not fail the build

This is the one that would actually get a board ordered wrong. `convertLayerArg`
handles an unknown token like this:

```cpp
else
{
    m_reporter->Report( wxString::Format( _( "Invalid layer name \"%s\"\n" ), token ) );
}
```

`[source: pcbnew/pcbnew_jobs_handler.cpp @ 9.0, lines ~388–392]`

It **reports and continues**. No exception, no non-zero exit. Misspell
`B.Silkscren` and you get six gerbers, exit code 0, a green light from every
check in §6, and a board with no bottom silkscreen. Misspell `F.Mask` and you
get a board with **no soldermask on the component side** — bare copper, and on
a hand-soldered board with 0805s, unbuildable.

`set -euo pipefail` does not save you here. **Assert the output file list
explicitly** after the export: exactly nine files, exact names, each non-empty.

### 4.3 The verification chain, in order

**Tier 0 — structural, no parser needed, takes a second.**

```sh
# exact file set
test "$(ls "$OUT/gerber" | wc -l)" -eq 9
for f in F_Cu.gtl B_Cu.gbl F_Mask.gts B_Mask.gbs F_Silkscreen.gto \
         B_Silkscreen.gbo Edge_Cuts.gm1 PTH.drl NPTH.drl; do
  ls "$OUT/gerber" | grep -q -- "$f" || { echo "MISSING $f"; exit 1; }
done
# nothing empty, nothing zero-aperture
find "$OUT/gerber" -size -100c -print -exec false \; 
# every gerber terminates properly
for g in "$OUT/gerber"/*.g??; do tail -c 4 "$g" | grep -q 'M02' || echo "NO M02: $g"; done
```

Catches F-24, catches a crashed export, catches an empty layer. `[from memory for the M02 terminator; the file-count assertion is a direct consequence of the F-24 source finding above]`

**Tier 1 — parse and measure, from the zip.**

`gerbonara` (pip) is the right tool on KiCad 9. I installed and ran it here:
version **1.5.0** on Python 3.11 (pypi lists 1.6.3 but pip resolves 1.5.0 on
3.11 — `pip install gerbonara==1.6.3` silently left 1.5.0 in place). CLI
subcommands: `bounding-box, layers, merge, meta, render, rewrite, transform,
kicad, protoboard`. `[test]`

The checks that matter:

- `gerbonara bounding-box <Edge_Cuts>` — **assert the board outline equals the
  intended outline.** This is the one number that, if wrong, makes every other
  file wrong and the board unusable in the rack.
- `gerbonara meta <dir>` — layer auto-identification. If gerbonara cannot work
  out which file is which from the names, neither can the fab's parser.
- `gerbonara render <dir> out.svg` — a composite render **of the deliverable**,
  to eyeball against `kicad-cli pcb export svg` of the board. Different code
  paths, same picture, or something is wrong.
- Drill hits: assert every hole lies inside the Edge.Cuts bounding box, and
  assert the PTH/NPTH counts against the board's pad and mounting-hole counts.

Two honest caveats, both from running it `[test]`:

1. gerbonara aborted on the real O_C zip because of `__MACOSX` junk (§2.5).
   Clean input or clean it first.
2. On the extracted files it then rejected a real, fabricated, *shipped* board:
   `SyntaxError: …silkBottom.gbo:11 "ADD10R,0.240000X0.080000X0.220000X0.060000":
   RectangleAperture.__init__() takes from 3 to 4 positional arguments but 5
   were given`. A `R` aperture takes X, Y and optionally one hole diameter;
   that Eagle file emits four modifiers, which is out of spec. gerbonara is
   *right* and the fab built it anyway. **Read that carefully: a strict parser
   is a conformance check, not a simulation of the fab's CAM.** A gerbonara
   failure means "look at this"; a gerbonara pass does not mean "the fab will
   like it". KiCad output will not trip this particular one — I flag it so the
   first failure is not mistaken for a broken board.

**Tier 2 — KiCad's own gerber tooling. `master` only; NOT in KiCad 9.**

`master` grew a whole `kicad-cli gerber` command tree whose description is
literally *"View and compare existing Gerber/Excellon files. To export Gerbers
from a PCB, use 'pcb export gerbers'"* `[source: kicad/cli/command_gerber.h @ master]`:

| Command | Flags that matter |
|---|---|
| `kicad-cli gerber info` | `--strict` ("Fail on any parse warnings or errors"), `--area`, `--format`, `--units` |
| `kicad-cli gerber png` | `--strict`, `--dpi`, `--width/--height`, `--origin-x/-y`, `--window-width/-height`, `--foreground/--background`, `--transparent`, `--no-antialias` |
| `kicad-cli gerber diff` | `file1 file2`, `--exit-code-only`, `--tolerance`, `--dpi`, `--no-align`, `--strict` |

`[source: kicad/cli/command_gerber_info.cpp, command_gerber_convert_png.cpp, command_gerber_diff.cpp @ master]`

This is exactly the missing verification stage, in-toolchain, headless, with a
`--strict` that *does* fail and an `--exit-code-only` diff built for CI. And it
does not exist on 9.0: fetching `kicad/cli/command_gerber_info.cpp` returns
**404 on both the `9.0` and `8.0` branches** and **200 on `master`**. `[test: HTTP status per branch]`

**Consequence for the plan.** §"The stack" justifies its one hard network
requirement — *"Ubuntu noble's stock archive has KiCad 7 only, which has no
`kicad-cli pcb drc` — that arrived in KiCad 8, and the verify stage depends on
it"* `[source: /home/user/Woody/docs/reference/pcb-pipeline.md:22–24]`. The same
argument now applies one version further up: **the fab-output verify stage
wants KiCad 10.** Either take KiCad 10 and get Tier 2 plus `--check-zones` for
free, or stay on 9 and own that gerbonara is the only parser in the chain. Both
are defensible. Silently getting 9 and thinking you have verification is not.

**Tier 3 — a human looks at a picture.** `gerbv` (apt, and it exports headless
with `gerbv -x png -o out.png *.gtl *.gts …`) or the Tier-2 `gerber png`.
`[from memory for the gerbv flag]` Render the **top copper + top mask + top
silk composite from the zip** at 600 dpi and look at it. Every plausible
disaster in this stage — a missing mask layer, a mirrored layer, silk over
pads, a pour that did not fill, an outline with a gap — is obvious in that one
image and invisible in every numeric check above it.

### 4.4 One thing DRC will not do for you

`kicad-cli pcb drc` checks the board against **your** `.kicad_dru` and design
settings `[source: /home/user/Woody/docs/reference/pcb-pipeline.md:147–149]`.
It has no idea what your fab can build. The plan says *"Custom fab rules go in
`<project>.kicad_dru`"* and never says where the numbers in it come from.

Write it down: the `.kicad_dru` values (min track, min clearance, min annular
ring, min drill, min silk width, mask sliver, edge clearance) are **transcribed
from the chosen fab's capability sheet**, and the file records which fab and
which date. Otherwise "DRC passes" means "passes the rules I invented", the
board fails CAM review, and you find out a week later.

---

## 5. Summary of what to change in `docs/reference/pcb-pipeline.md`

1. Replace §7's four commands with §2 above — they do not currently run (F-03,
   F-04) and, once they do, produce X2 gerbers with netlist attributes, aperture
   macros, and a merged PTH/NPTH drill file that three of six target fabs do not
   want (F-06, F-09, F-10).
2. Delete the sentence **"The fab needs gerbers and drill. That is the whole
   order."** and replace it with `README-FAB.txt` + the physical-stackup
   decision (F-12, F-18, §3.1–3.2).
3. Add `pcb-copper-weight`, `pcb-thickness`, `pcb-surface-finish`,
   `pcb-layer-count` to `config/figures.yaml`, owned by this file, and make the
   IPC-2221 derivation at line 183 cite `pcb-copper-weight` instead of saying
   "1 oz" (F-18 — this is `CLAUDE.md` §1, applied to the one number in the file
   that is both a fab instruction and a design input).
4. Add IPC-D-356 export + E-test to the order (F-22), and the 1:1 PDF and panel
   DXF (F-17, F-19) that ADR 0004 and ADR 0009 already require by name.
5. Split the panel out of `fab/<board>/`. It is aluminium, a different vendor,
   and a DXF (F-19).
6. Add an assertion stage that runs on the **zip**, not the board (F-23), and
   an explicit output-file-list assertion, because an invalid layer name exits 0
   (F-24).
7. State the KiCad-version consequence: `--check-zones` and the whole
   `kicad-cli gerber info|png|diff` verification tree are KiCad 10, not 9
   (F-25, §4.3).
8. Add an interactive HTML BOM to `export.py` — the hand-assembly artefact the
   plan correctly reasons its way to and then does not build (F-13).

---

## 6. What I checked by hand, and what I did not

**Ran in this sandbox `[test]`:** installed gerbonara 1.5.0 in a venv and
confirmed its CLI subcommand list; ran `gerbonara meta` against the O_C zip
(failed on `__MACOSX`) and against its extracted contents (failed on an
out-of-spec Eagle aperture); listed the O_C zip's contents; cloned
`g200kg/kicad-gerberzipper` and `openscopeproject/InteractiveHtmlBom`; fetched
KiBot's three vendor templates; fetched eleven KiCad source files from the
`9.0` and `master` branches and diffed the flag sets; probed branch-existence by
HTTP status for five `kicad-cli` subcommand source files; grepped the Woody
design corpus for stackup terms and for `128.5`.

**Not verified, flagged as such:** the gerbv headless flag and the M02
terminator convention are `[from memory]`. I did not verify any vendor's
current order form — those sites are blocked, and everything vendor-specific
here is attributed to GerberZipper or KiBot rather than to the vendor. I did not
run `kicad-cli` itself: it is not installed in this sandbox
(`which kicad-cli` → nothing, `import pcbnew` → `ModuleNotFoundError`) `[test]`,
so **every flag above is read from source, not from `--help` output.** The
smoke-board stage the plan already proposes (§"Prove the toolchain on a board
you can eyeball") is the right place to confirm them, and confirming §2's flag
set should be added to what that smoke board proves.

**One finding I withdrew before filing:** `F.Silkscreen` vs `F.SilkS` (F-02).
`LSET::NameToLayer()` accepts only `F.SilkS`, which looks damning, but the CLI
does not call it — `convertLayerArg()` carries a second map of GUI canonical
names. Recording the withdrawal so the next reviewer does not re-file it.
