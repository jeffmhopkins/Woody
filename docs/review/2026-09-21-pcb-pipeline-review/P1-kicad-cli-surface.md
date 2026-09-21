# P1 — the `kicad-cli` command surface

Cold review of `docs/reference/pcb-pipeline.md` (status: Proposed 2026-09-21,
not run). Slice: every `kicad-cli` invocation, subcommand, flag and version
claim in the plan.

## Method and provenance

`kicad-cli` is **not installed in this sandbox** (`which kicad-cli` → not
found; `import pcbnew` → ImportError). **No claim below is marked `[test]`.**
Everything is `[source]` against KiCad's own repository, or explicitly
`[from memory]`.

Source: `gitlab.com/kicad/code/kicad`, project id 15502567, read at
2026-09-21. Branches read: `7.0`, `8.0`, `9.0`, `10.0`. The CLI argument
definitions live in `kicad/cli/command_*.cpp` (one file per subcommand); the
work each one dispatches is in `pcbnew/pcbnew_jobs_handler.cpp`; the argument
parser is the vendored `thirdparty/argparse/include/argparse/argparse.hpp`.

Two facts about the parser govern half the findings below, so they are stated
once:

- **`input` is a positional argument, not a flag.**
  `#define ARG_INPUT "input"` and `m_argParser.add_argument( ARG_INPUT )` —
  `kicad/cli/command.h:34` and `kicad/cli/command.cpp` (`addCommonArgs`),
  ref `9.0`. It has no `default_value`, so argparse requires it.
  `[source]`
- **The parser does no abbreviation or prefix matching.** An argument is
  looked up by exact string in `m_argument_map`; a miss throws
  `"Unknown argument: " + current_argument`
  (`thirdparty/argparse/include/argparse/argparse.hpp:2055` and `:2059`,
  ref `9.0`). A missing positional throws `"Too few arguments"` (`:886`,
  `:914`). `kicad/kicad_cli.cpp` catches `std::exception`, prints the message
  and the subcommand help, and returns `CLI::EXIT_CODES::ERR_ARGS` = **1**
  (`kicad/kicad_cli.cpp` ~L417-465; `include/cli/exit_codes.h:32`, ref `9.0`).
  `[source]`

---

## 1. Verdict table

| # | Quoted claim | Verdict | Evidence |
|---|---|---|---|
| 1 | "Ubuntu noble's stock archive has **KiCad 7 only**" | UNVERIFIABLE | `api.launchpad.net` is blocked from this sandbox (`curl` → `CONNECT tunnel failed, response 403`). `[from memory]` noble shipped kicad 7.0.11, which is consistent — but this is a guess, not a check. |
| 2 | "which has no `kicad-cli pcb drc` — that arrived in KiCad 8" | **CONFIRMED** | Tree of `kicad/cli` at ref `7.0` contains no `command_pcb_drc.*` and no `command_sch_erc.*`; ref `8.0` contains both. `[source]` |
| 3 | (implied) KiCad 8 would therefore suffice for the verify stage | REFUTED — under-stated | `kicad/cli` at ref `8.0` has **no `command_pcb_render.*`**; it first appears at ref `9.0`. The plan's stage 7 uses `pcb render`, so the floor is 9, not 8. The stated justification for the network requirement is weaker than the actual requirement. `[source]` |
| 4 | "**KiCad 9**" is the target; `~/.config/kicad/9.0/…` | REFUTED (stale) | Current stable upstream is **10.0.6**, tagged 2026-08-28 (`/repository/tags`); branch `10.0` exists. An `apt` install from the current `*.kicad.org` repo yields 10.0 and a `~/.config/kicad/10.0/` settings dir. `[source]` |
| 5 | `kicad-cli pcb drc --format json --severity-error --exit-code-violations` | **REFUTED as written** | All four *flag spellings* are correct (`kicad/cli/command_pcb_drc.cpp:33-41`, ref `9.0`). But the required positional board file is absent → `"Too few arguments"`, exit 1. `[source]` |
| 6 | `--severity-error` (as used) | **REFUTED — semantics inverted** | `JOB_RC` default is `m_severity( RPT_SEVERITY_ERROR \| RPT_SEVERITY_WARNING )` (`common/jobs/job_rc.cpp:40`, ref `9.0`). `command_pcb_drc.cpp` only overrides the default `if( severity )`. So `--severity-error` **narrows** the run to errors only — it drops every warning from the report *and* from the `--exit-code-violations` test. `[source]` |
| 7 | `--exit-code-violations` "Return a nonzero exit code if DRC violations exist" | CONFIRMED, value unstated | Returns `CLI::EXIT_CODES::ERR_RC_VIOLATIONS` = **5**, not 1 (`include/cli/exit_codes.h:37`; `pcbnew/pcbnew_jobs_handler.cpp` ~L2119). Exit 1 means *bad arguments*. The plan never distinguishes them. `[source]` |
| 8 | "`<project>.kicad_dru` … read by `kicad-cli pcb drc`" | CONFIRMED with a correction | The rules file is found by taking the **board** filename and swapping the extension: `wxFileName rules = pro; rules.SetExt( FILEEXT::DesignRulesFileExtension ); bds.m_DRCEngine->InitEngine( rules )` (`pcbnew/python/scripting/pcbnew_scripting_helpers.cpp` ~L250-256, ref `9.0`; `FILEEXT::DesignRulesFileExtension` = `"kicad_dru"`, `common/wildcards_and_files_ext.cpp:170`). It must be `<board>.kicad_dru` beside `<board>.kicad_pcb`, not merely "the project's". `[source]` |
| 9 | "the basics (clearance, min track, via sizes) go in the board's design settings" | **REFUTED** | Board design settings and net classes are serialized into the **project** file, not the `.kicad_pcb`: `common/project/project_file.cpp:346` (`std::string bp = "board.design_settings.";`) and `:122` (`m_NetSettings = std::make_shared<NET_SETTINGS>( this, "net_settings" )`), ref `9.0`. They live in `.kicad_pro`. `[source]` |
| 10 | `kicad-cli pcb export gerbers --layers F.Cu,B.Cu,F.Mask,B.Mask,F.Silkscreen,B.Silkscreen,Edge.Cuts` | **REFUTED as written** | Subcommand and `--layers` are right; every layer name resolves. Missing positional input, and missing `-o <dir>`. `[source]` |
| 10a | — layer name `F.Silkscreen` | CONFIRMED | `convertLayerArg` builds two maps: file-canonical (`LSET::Name` → `F.SilkS`) **and** GUI-canonical (`LayerName` → `F.Silkscreen`), and accepts either (`pcbnew/pcbnew_jobs_handler.cpp:329-394`; `common/layer_id.cpp:47-48`, ref `9.0`). Worth knowing: `LSET::NameToLayer` (`common/lset.cpp:117`) knows only `F.SilkS`, so the two spellings are *not* interchangeable everywhere. `[source]` |
| 10b | — subcommand `gerbers` (plural) | CONFIRMED, and the right choice | The singular `pcb export gerber` prints `"This command is deprecated as of KiCad 9.0, please use \"gerbers\" instead"` (`kicad/cli/command_pcb_export_gerber.cpp`, `doPerform`, ref `9.0`). `[source]` |
| 11 | `kicad-cli pcb export drill --format excellon --units mm --drill-origin absolute` | **REFUTED — wrong flag** | **There is no `--units` on this subcommand.** It is `--excellon-units` (short `-u`): `#define ARG_EXCELLON_UNITS "--excellon-units"` … `add_argument( "-u", ARG_EXCELLON_UNITS )` — `kicad/cli/command_pcb_export_drill.cpp:38,72` at ref `9.0`, and identically at refs `8.0` (`:39,71`) and `10.0` (`:39`). Result: `Unknown argument: --units`, exit 1. `[source]` |
| 11a | — `--format excellon`, `--drill-origin absolute` | CONFIRMED (both are already the defaults) | `.default_value( std::string( "excellon" ) )`, `.default_value( std::string( "absolute" ) )` — same file, ref `9.0`. `[source]` |
| 11b | — (unstated) drill `-o` must be a directory | MISSING | `PCB_EXPORT_BASE_COMMAND( "drill", false, true )` — third arg `aOutputIsDir=true`; `doPerform` rejects a non-directory with `"Output must be a directory"` → `ERR_ARGS`. `[source]` |
| 12 | `kicad-cli pcb export step` | CONFIRMED (subcommand), REFUTED as written | Registered as `exportPcbStepCmd{ "step", … }` (`kicad/kicad_cli.cpp:123`, ref `9.0`). Missing positional input and `-o`. `--force`/`-f` ("Overwrite output file") is defined and read into `params.m_Overwrite` (`kicad/cli/command_pcb_export_3d.cpp:82,247`) but I found **no code at ref `9.0` that reads `EXPORTER_STEP_PARAMS::m_Overwrite`** — its effect on a re-run is unverified. `[source]` |
| 13 | `kicad-cli pcb export svg   # per layer, for review` | **REFUTED — wrong mode** | Default generation mode is SINGLE (one combined file). Per-layer output requires `--mode-multi`, and then `-o` is a directory. 9.0 additionally prints `"This command has deprecated behavior as of KiCad 9.0… The new behavior will match --mode-multi"` when neither mode flag is given — still true at ref `10.0`. (`kicad/cli/command_pcb_export_svg.cpp:35-36,177-190`, ref `9.0`.) `[source]` |
| 14 | "Two things still want OpenGL: `kicad-cli pcb render` …  Run both under `xvfb-run -a` with `LIBGL_ALWAYS_SOFTWARE=1`" | **REFUTED** | (a) `kicad-cli` is `IMPLEMENT_APP_CONSOLE( APP_KICAD_CLI )` deriving from `wxAppConsole` — no GUI toolkit init, no X connection (`kicad/kicad_cli.cpp:566,677`, ref `9.0`). (b) The render job uses `RENDER_3D_RAYTRACE_RAM` — a CPU raytracer writing into a RAM buffer, then `wxImage::SaveFile` (`pcbnew/pcbnew_jobs_handler.cpp:720-790`). `3d-viewer/3d_rendering/raytracing/render_3d_raytrace_ram.{h,cpp}` contains no GL call; the only hit for "openGL" is a stale comment at `render_3d_raytrace_ram.cpp:79`. The GL path is the *sibling* class `render_3d_raytrace_gl`, which the CLI does not use. `[source]` |
| 14a | — (unstated) `pcb render` is 9.0-only | MISSING | Absent from `kicad/cli` at refs `7.0` and `8.0`. `[source]` |
| 14b | — (unstated) `pcb render -h` is not help | MISSING | `ARG_HEIGHT_SHORT` is `"-h"`, registered as an alias of `--height` (`kicad/cli/command_pcb_render.cpp:43-44,226`). `-h` on this one subcommand asks for an image height. `[source]` |
| 15 | "**You lose `--schematic-parity`,** because there is no `.kicad_sch`" | **CONFIRMED** | Flag exists (`#define ARG_PARITY "--schematic-parity"`, `kicad/cli/command_pcb_drc.cpp:41`). In CLI the schematic is derived from the board path: `wxFileName schematicPath( drcJob->m_filename ); schematicPath.SetExt( FILEEXT::KiCadSchematicFileExtension );` → falls back to the legacy `.sch` → if neither exists, reports `"Failed to fetch schematic netlist for parity tests."` and sets `checkParity = false` (`pcbnew/pcbnew_jobs_handler.cpp:1998-2020`, ref `9.0`). `[source]` |
| 15a | — (unstated) passing it anyway is not a safety net | MISSING | That failure is a `m_reporter->Report(...)` only. It does not create a violation and does not change the exit code — DRC continues and can still exit 0. `[source]` |
| 16 | Stack table: KiCad 9 does "DRC/**ERC**" | REFUTED — internally inconsistent | `kicad-cli sch erc` exists from 8.0 (`kicad/cli/command_sch_erc.cpp`), but its positional input is a `.kicad_sch`, and the plan's whole architecture is "there is no `.kicad_sch`". ERC in this pipeline comes from SKiDL alone; KiCad contributes none. The stack table credits a capability the design forecloses. `[source]` |
| 17 | "The library tables do not exist until a GUI has run once … Headless, copy the stock ones from `/usr/share/kicad/template/` before anything else" | **REFUTED (first half)** | `IFACE::OnKifaceStart` calls `loadGlobalLibTable()` unconditionally; under `KFCTL_CLI` it skips the GUI dialog and calls `FP_LIB_TABLE::LoadGlobalTable( GFootprintTable )` (`pcbnew/pcbnew.cpp:417,445-472`, ref `9.0`). That function creates the directory and **copies the template table itself**, falling back to writing an empty one (`common/fp_lib_table.cpp:622-660`). The manual copy is unnecessary. |
| 17a | — "set `HOME` to something writable" | CONFIRMED | Same code path does `wxFileName::Mkdir(...)` and `wxCopyFile(...)` under `PATHS::GetUserSettingsPath()`; `SETTINGS_MANAGER::MigrateIfNeeded` also `Mkdir`s it when `m_headless` (`common/settings/settings_manager.cpp:550-566`). A read-only `HOME` fails. `[source]` |
| 18 | "`pos` export gives `Ref,Val,Package,PosX,PosY,Rot,Side`" | **CONFIRMED** | `snprintf( line, sizeof(line), "Ref%cVal%cPackage%cPosX%cPosY%cRot%cSide\n", …)` — `pcbnew/exporters/place_file_exporter.cpp:176`, ref `9.0`. `[source]` |
| 19 | "The Specctra helpers have changed signature across versions. `help(pcbnew.ExportSpecctraDSN)` before writing against it." | **CONFIRMED** (adjacent to slice) | At ref `7.0`, `pcbnew/python/scripting/pcbnew_scripting_helpers.h` declares `ExportSpecctraDSN(wxString&)`, `ExportSpecctraDSN(BOARD*, wxString&)` and `ImportSpecctraSES(wxString&)` — but **not** `ImportSpecctraSES(BOARD*, wxString&)`. That two-argument overload appears at ref `8.0` (`:182`) and persists at `9.0` (`:183`). The one-argument forms operate on "the current BOARD", which a standalone script does not have — stage 4 must use the two-argument forms. `[source]` |
| 20 | "Both are read by `kicad-cli pcb drc`, so what the router obeys and what DRC checks are the same file" | REFUTED as stated | Two files, not one, and neither is the `.kicad_pcb`: custom rules in `<board>.kicad_dru` (row 8) and clearances/netclasses in `<board>.kicad_pro` (row 9). Freerouting reads neither — it reads the `.dsn`, which `ExportSpecctraDSN` writes from the in-memory board. Three representations, one of which is only as good as the last `SaveBoard`. `[source]` |

---

## 2. Detail on each REFUTED / MISSING item

### R1 — Every command line in the plan omits the required board file (rows 5, 10, 11, 12, 13)

This is the single largest defect in the slice: **not one `kicad-cli` line in
`docs/reference/pcb-pipeline.md` will parse.** `input` is positional
(`kicad/cli/command.h:34`), has no default, and argparse throws
`"Too few arguments"` before any work starts. `kicad/kicad_cli.cpp` turns that
into exit 1 plus a help dump.

As written → as it must be:

```sh
# plan
kicad-cli pcb drc --format json --severity-error --exit-code-violations
# correct
kicad-cli pcb drc --format json --severity-all --exit-code-violations \
    -o fab/module/drc.json  pcb/module/module.kicad_pcb

# plan
kicad-cli pcb export gerbers --layers F.Cu,B.Cu,F.Mask,B.Mask,F.Silkscreen,B.Silkscreen,Edge.Cuts
# correct
kicad-cli pcb export gerbers \
    --layers F.Cu,B.Cu,F.Mask,B.Mask,F.Silkscreen,B.Silkscreen,Edge.Cuts \
    --subtract-soldermask -o fab/module/gerbers/  pcb/module/module.kicad_pcb

# plan
kicad-cli pcb export drill --format excellon --units mm --drill-origin absolute
# correct  (--excellon-units, and -o must be a directory)
kicad-cli pcb export drill --format excellon --excellon-units mm \
    --drill-origin absolute --generate-map --map-format pdf \
    -o fab/module/drill/  pcb/module/module.kicad_pcb

# plan
kicad-cli pcb export step
# correct
kicad-cli pcb export step --force --subst-models \
    -o fab/module/module.step  pcb/module/module.kicad_pcb

# plan
kicad-cli pcb export svg         # per layer, for review
# correct  (per-layer needs --mode-multi; -o is then a directory)
kicad-cli pcb export svg --mode-multi --black-and-white \
    --layers F.Cu,B.Cu,F.Mask,B.Mask,F.Silkscreen,B.Silkscreen,Edge.Cuts \
    -o fab/module/svg/  pcb/module/module.kicad_pcb

# plan
xvfb-run -a kicad-cli pcb render # LIBGL_ALWAYS_SOFTWARE=1
# correct
kicad-cli pcb render --side top --quality high -w 2400 --height 1600 \
    -o fab/module/render-top.png  pcb/module/module.kicad_pcb
```

Note `--height` spelled long in the render line: `-h` on that subcommand is
the height alias, not help (row 14b).

### R2 — `--units mm` on `pcb export drill` does not exist

The correct spelling is `--excellon-units mm`, or `-u mm`. This is stable
across three release branches, so it is not a version-skew problem — it is
simply the wrong flag. The name `--units` *does* exist on other subcommands
(`pcb drc --units`, `sch erc --units`, `pcb export odb --units`, and
`pcb export vrml --units`), which is presumably where it came from.

This is the "fails on run one" case the review brief asked for: exit 1,
`Unknown argument: --units`, no drill files.

### R3 — `--severity-error` is a narrowing, not a tightening

The plan reads as though `--severity-error` means "fail on errors". It does
not mean that; `--exit-code-violations` already means that. What
`--severity-error` does is *replace* the default severity mask
`ERROR|WARNING` with `ERROR`, so the JSON report contains no warnings at all
and the non-zero exit ignores them.

On a hand-soldered board that is the wrong trade. KiCad's default-warning
classes include silkscreen-over-soldermask, courtyard overlap, and text
height/thickness violations — exactly the errata a hand-assembly board wants
surfaced. Use `--severity-all` and let `verify.py` decide which warnings are
acceptable, or at minimum `--severity-error --severity-warning`.

### R4 — the OpenGL paragraph is wrong for the version the plan pins

`kicad-cli` is a `wxAppConsole` program. There is no wxWidgets GUI
initialisation and therefore no X11 connection to make. The KiCad 9 render job
runs `RENDER_3D_RAYTRACE_RAM`, the RAM-buffer sibling of the GL raytracer,
introduced precisely so that `pcb render` is headless.

Consequences for `setup.sh`: `xvfb` is not needed for `pcb render`, and the
plan's framing ("Everything else — DRC, gerbers, drill, STEP, SVG — is
genuinely headless") implies a distinction that does not exist. Freerouting
may still want a display; that is a separate, unverified claim and this slice
does not cover it.

Residual risk I could not close: the render path calls `wxImage::SaveFile`,
and `LoadBoard` calls `wxInitAllImageHandlers()`
(`pcbnew_scripting_helpers.cpp:161`), so the handlers exist. I found no
display dependency. I have not run it.

### R5 — `~/.config/kicad/9.0/` is already stale, and the copy is unnecessary

Two separate problems in one paragraph.

*Version*: KiCad 10.0.6 is the current stable tag (2026-08-28). A fresh
`apt` install from the upstream repository produces `~/.config/kicad/10.0/`.
`setup.sh` copying into a hardcoded `9.0/` would be copying into a directory
nothing reads. The settings directory is versioned by
`GetMajorMinorVersion()` (`common/paths.cpp:52`), so it must be derived, not
literal — `kicad-cli version` is the way to derive it (see MISSING-1).

*Necessity*: pcbnew's kiface creates the global footprint table on CLI
startup, copying `/usr/share/kicad/template/fp-lib-table` if it can find it
and writing an empty table if it cannot. The plan's "the GUI writes on first
launch" is true of the GUI and false of `kicad-cli`. What *is* required is a
writable `HOME`, which the plan also says.

The failure mode the plan is reaching for is real but different: if the
template search fails, `LoadGlobalTable` silently installs an **empty** table
and every footprint lookup then fails with a confusing "library not found"
rather than an obvious "no library table". Assert the table is non-empty in
`setup.sh` instead of copying it.

### R6 — three places hold the rules, and the plan says one

`.kicad_dru` (custom rules) is found by board-name-plus-extension.
Clearances, track widths, via sizes and **net classes** live in
`.kicad_pro` (`board.design_settings.*`, `net_settings`), which has been true
since KiCad 6 and is unchanged at 9.0. The `.kicad_pcb` holds neither.

This matters for stage 2. The plan's net-class table is the right idea, but
`build_board.py` must persist it through something that writes the project
file. `SaveBoard( filename, board )` does — its `aSkipSettings` parameter
defaults false, and the non-skip branch writes the `.kicad_pro`
(`pcbnew_scripting_helpers.cpp:589-612`). If a future version of the script
reaches for a raw `PCB_IO` writer instead, or if `pcb/<board>/*.kicad_pro` is
gitignored as "generated", the net classes evaporate and `kicad-cli pcb drc`
quietly checks the board against KiCad defaults while reporting zero
violations. That is precisely this project's named failure mode wearing a
different hat, and no checker would catch it.

### R7 — the stack table claims ERC that the architecture forbids

Row 16. Either drop "/ERC" from the KiCad row, or say explicitly that
`kicad-cli sch erc` is unreachable in this pipeline and SKiDL's `ERC()` is the
only electrical-rules gate. As written, a reader budgeting risk will believe
there are two independent ERC implementations when there is one.

---

## 3. MISSING — `kicad-cli` capabilities the plan should be using and isn't

**M1. `kicad-cli version` — nothing pins the toolchain.**
The plan's flags are version-sensitive in both directions (`pcb drc` needs 8+,
`pcb render` needs 9+, the `svg` default mode is announced to change, the
settings directory is version-named). There is no version gate anywhere.
`kicad-cli version --format about` emits the full build info including the
library versions (`kicad/cli/command_version.cpp:36-38,65-68`, ref `9.0`).
`setup.sh` should record it and `--format plain` should drive the settings-dir
path. `[source]`

**M2. `kicad-cli jobset run` — this is the plan's stated goal, already built.**
Present at ref `9.0` (`kicad/cli/command_jobset_run.cpp`). It takes a project
file positionally plus `--file <jobset>` and `--stop-on-error`, and runs a
declarative list of export jobs. "Entirely from a shell, re-runnably, with
every script in the repo" is the description of a `.kicad_jobset` checked into
the repo. It also removes every hand-written flag string, which is where all
of section 1's defects live. At minimum the plan should say why it is not
using it. `[source]`

**M3. `kicad-cli pcb export ipcd356` — an independent netlist read off the copper.**
`PCB_EXPORT_IPCD356_COMMAND … "Generate IPC-D-356 netlist file"`
(`kicad/cli/command_pcb_export_ipcd356.cpp:30-32`, ref `9.0`). The plan's
`verify.py` wants "board netlist **equals** the SKiDL netlist, ref by ref and
net by net" and "**no two nets merged**". IPC-D-356 is exactly that: net name
per pad/via extracted from the finished board, in a fixed-column text format
that is trivial to diff. It is also what a fab's flying-probe test consumes,
so ordering it costs nothing and gives the assertion and the test the same
input. This is a stronger check than the pcbnew-API netlist walk the plan
implies, and it is one subcommand. `[source]`

**M4. `--generate-map` / `--map-format` / `--generate-report` on drill.**
The plan says "The fab needs gerbers and drill. That is the whole order."
Most fabs also want the drill map, and the plan's own hand-assembly framing
means a human will want the drill report. Three flags, already defined
(`command_pcb_export_drill.cpp:40-42`, ref `9.0`). `[source]`

**M5. The Gerber job file (`.gbrjob`) is generated and should be in the zip.**
`pcb export gerbers` writes it via `GERBER_JOBFILE_WRITER::CreateJobFile`
(`pcbnew/pcbnew_jobs_handler.cpp:1209-1215`, ref `9.0`). It carries the
stackup and finish the fab would otherwise ask for by email. `[source]`

**M6. `--subtract-soldermask` on gerbers.** Defined at
`command_pcb_export_base.h:53`. Trims silkscreen at mask openings — the thing
that otherwise puts ink on a pad. Ordinary fab hygiene the plan does not
decide either way. `[source]`

**M7. `-D` / `--define-var` for traceability.** Every export command calls
`addDefineArg()` (`kicad/cli/command.cpp`, `addDefineArg`). Passing
`-D REVISION=$(git rev-parse --short HEAD)` stamps the board's title block at
export time, so a gerber set can be traced to a commit. For a repo whose
central failure is derived documents drifting from their source, a fab package
that names its own commit is cheap insurance. `[source]`

**M8. `kicad-cli pcb export dxf`** (`command_pcb_export_dxf.cpp`, ref `9.0`)
for the mechanical cross-check. The plan's stage 6 asserts "no copper under
the connector bore or panel cutouts" and its precursors list panel cutouts as
a gate; DXF of `Edge.Cuts` + `F.Cu` is the format the panel drawing is in.
`[source]`

**M9. `pcb export odb` and `pcb export ipc2581`** both exist at ref `9.0`
(`command_pcb_export_odb.cpp`, `command_pcb_export_ipc2581.cpp`). Worth one
sentence saying they were considered and rejected for this fab, rather than
being absent.

**M10. Exit codes are never named.** `ERR_ARGS`=1, `ERR_UNKNOWN`=2,
`ERR_INVALID_INPUT_FILE`=3, `ERR_INVALID_OUTPUT_CONFLICT`=4,
`ERR_RC_VIOLATIONS`=5, `ERR_JOBS_RUN_FAILED`=6
(`include/cli/exit_codes.h:29-38`, ref `9.0`). A pipeline that treats "DRC
found violations" (5) and "you spelled a flag wrong" (1) as the same event
will spend a long time debugging the wrong thing. `[source]`

---

## 4. Ranked — what would break a first run

1. **Every `kicad-cli` line is missing its positional board file.** Six
   commands, six `Too few arguments`, exit 1. Nothing in stages 6 and 7 runs
   at all. (R1)
2. **`--units mm` on `pcb export drill`.** `Unknown argument: --units`,
   exit 1. No drill file, therefore no orderable package. Correct spelling
   `--excellon-units mm` / `-u mm`. (R2)
3. **No `-o` anywhere.** Even once 1 and 2 are fixed, every artifact lands
   beside the `.kicad_pcb` in `pcb/<board>/` rather than in `fab/<board>/`,
   so the plan's own directory contract is violated and the zip step finds
   nothing. Drill additionally *requires* a directory and errors with
   `"Output must be a directory"` otherwise. (R1, row 11b)
4. **`~/.config/kicad/9.0/` hardcoded while upstream stable is 10.0.6.**
   `setup.sh` writes into a directory the installed binary does not read.
   Compounded by the fact that the copy is unnecessary in the first place, so
   the symptom is "footprints not found" with no obvious cause. (R5)
5. **`--severity-error` silently discards every DRC warning**, from the JSON
   report and from the non-zero exit. The verify stage reports green on a
   board with warnings the plan's own hand-assembly constraints care about.
   Wrong-answer-looking-right, which is worse than a crash. (R3)
6. **`export svg` produces one combined file, not per-layer**, and prints a
   deprecation notice saying the default will change under you. The review
   artifact the plan wants is not the artifact it gets. (row 13)
7. **Net classes / design settings assumed to be in the board file.** Stage 2
   is built on this. If `build_board.py` does not persist `.kicad_pro`, DRC
   checks defaults and passes, and Freerouting is given rules the board no
   longer claims. Silent. (R6)
8. **`.kicad_dru` must be named for the board, not the project.** If board
   and project basenames ever diverge, the custom rules are simply not loaded
   — no warning, DRC passes. Silent. (row 8)
9. **`xvfb` + `LIBGL_ALWAYS_SOFTWARE` around `pcb render`.** Harmless if
   xvfb installs, but it is a false dependency in `setup.sh` and a false
   statement in the gotchas list. The cost is a wrong mental model of what is
   headless, not a failed run. (R4)
10. **No version gate.** The plan cannot detect that it is running against
    the wrong major version until a flag fails, and some version differences
    (the `svg` default mode) will not fail — they will change the output.
    (M1)

---

## Note on what this review did not establish

- Nothing here was executed. `kicad-cli` is not installed in the review
  sandbox, so every verdict is source-reading, not behaviour.
- The Ubuntu-archive claim (row 1) could not be checked; Launchpad and the
  Ubuntu package index are blocked. It remains the plan's only unverified
  load-bearing premise for the "one hard network requirement".
- `--force` on `pcb export step` is accepted and plumbed to
  `EXPORTER_STEP_PARAMS::m_Overwrite`, but I could not find the code at ref
  `9.0` that consumes it. Re-run overwrite behaviour for STEP is **unknown**,
  not confirmed either way.
- Freerouting's display requirement, SKiDL, kiutils and the `pcbnew` Python
  module's packaging are outside this slice. The single Specctra finding
  (row 19) is included only because it corroborates the plan's own advice.
