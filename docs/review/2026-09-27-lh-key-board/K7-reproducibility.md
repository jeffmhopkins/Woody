# K7 — Reproducibility and the checks themselves (left-hand key board)

**Slice:** K7, cold (read only this wave's `README.md` under `docs/review/`).
**Revision measured:** `d46a3b0`, in scratch worktrees (`git worktree add … d46a3b0`),
removed afterwards. `tools/` pinned at that revision. Nothing under
`/home/user/Woody` was modified except this file.
**Environment:** KiCad 9.0.9 (`kicad-cli --version`), `python3` = 3.11.15 importing
`/usr/lib/python3/dist-packages/pcbnew.py`, 4 cores [run: `kicad-cli --version`, `python3 -c "import sys,pcbnew"`, `nproc`].

## Summary

**The board regenerates.** Every documented command succeeded from the sources,
and the result is **geometrically identical** to the committed board. The router is
**deterministic**: two separate runs of `pcb.py layout --force` produced identical
tracks, vias, footprint placements, silkscreen and zone fill. The committed
`.kicad_pcb` is the same geometry again. `fab/`'s BOM, CPL, hand list, pos file,
drill file, edge and job file are byte-identical apart from timestamps. The files
are *not* byte-reproducible, though (K7-13).

**The checks catch most of what they claim**: a moved switch, standoff or header, a
sheet edited without re-exporting, a hand-edited or missing Gerber, a missing
`Assembly` field, and a standoff moved in `body.yaml`, once the CAD is rebuilt.

**They miss six things that matter**, each shown by a deliberate breakage that ended
with **every gate green**:
- a swapped pin on J-CHAIN, against the ribbon's netlist (K7-1);
- a board-thickness change in the body CAD (K7-2);
- a part silently dropped from the order by `Assembly = none` (K7-3);
- a silkscreen label moved off the board in the `.kicad_pcb` (K7-5);
- stray files in `fab/` (K7-6);
- the stale-output message tells you to run a command that crashes (K7-4).

The right-hand geometry (connector facing −x) was exercised with a synthesized
`layout.yaml`, because the RH board has none, and it places and checks correctly.

## Regeneration: what was run and what came out

| Step | Command | Result |
|---|---|---|
| baseline | `python3 tools/kicad.py check` | `kicad: PASS - 3 source sheet(s), 2 board(s), 38 render(s) match their sources` [run] |
| baseline | `python3 tools/pcb.py check hardware/boards/key-board-lh` | `0 error(s), 0 warning(s)` [run] |
| baseline | `cad.py check`, `check-staleness.py`, `check-netlist.py --strict`, `merge-bom.py --check` | all PASS / rc 0 [run] |
| export | `kicad.py export` for key-register, key-switch-network, key-marker-and-bits, key-board-lh | all rc 0, ERC 0/0, **no diff** against committed [run: `git status --short` empty] |
| layout | `pcb.py layout hardware/boards/key-board-lh --force` | rc 0, **4 min 35 s**, every net `ok`, "rip-up round 1: 1 group(s) improved", "9 ground stitching via(s)" [run] |
| geometry vs committed | pcbnew script comparing footprints, tracks, vias, silk, zone fill | tracks 684 = 684, length 676.488 mm = 676.488 mm, vias 44 = 44, sorted segment hash `cc723df1c549` both, via hash `e7e31819e170` both, every footprint's position/rotation/side equal, 31 bottom silk texts equal, filled GND areas 3036.7747 / 2876.4964 mm² both [run] |
| determinism | a second `layout --force` in a separate copy | identical to the first on every measure above; the route logs are identical line for line [run: `diff <(grep route: layout1.log) <(grep route: layout2.log)` → no output] |
| check | `pcb.py check` on the regenerated board | `0 error(s), 0 warning(s)` [run] |
| render | `pcb.py render hardware/boards/key-board-lh` | rc 0, 46 s, 15 fab files [run] |
| fab vs committed | `diff`, ignoring `CreationDate`/`date` lines | **0 differing lines**: `-bom-jlc.csv`, `-cpl-jlc.csv`, `-hand-assembly.csv`, `-pos.csv`, `.drl`, `-job.gbrjob`, `Edge_Cuts`, `F_Paste`, `F_Silkscreen`. **Reordered**: `B_Cu` (1565 lines), `F_Cu` (848), `B_Mask` (212), `B_Silkscreen` (214), `B_Paste` (118), `F_Mask` (23). Sorted, `F_Cu` and `B_Silkscreen` are identical; the rest differ only in aperture numbering (`%ADD13…` ↔ `%ADD15…`) [run] |
| PNGs vs committed | pixel diff | copper-top: 159 px differ, max Δ 1. copper-bottom: 1528 px, max Δ 2. 3D top/bottom: 7.4 % / 5.9 % of pixels, max Δ 173 / 148 [run] |
| final | `kicad.py check` after `pcb.py render` | `PASS` [run] |

## Deliberate breakages

Each breakage was made in a fresh checkout of `d46a3b0`, one at a time.

| # | What was broken | Command | Caught? | Exact message (abridged only where marked …) |
|---|---|---|---|---|
| 1 | SW-LH3 moved +0.5 mm in x in the `.kicad_pcb` | `pcb.py check` | **yes** | `error: [cad] SW-LH3 is at (150.5, 121.5), the body CAD puts it at (150.00, 121.50)`, plus 6 DRC clearance errors; `kicad.py check` repeats them |
| 1b | SW-LH3 rotated 180° about its own centre | `pcb.py check` | **only incidentally**: 39 DRC errors (shorts, unconnected), **no `[cad]` error** | `pcb: … 39 error(s), 4 warning(s)`; no line names the rotation (K7-8) |
| 1c | J-CHAIN moved +0.3 mm | `pcb.py check` | **yes** | `error: [cad] J-CHAIN's pads centre at (132.07500000000002, 107.985), facing +x; the body CAD puts them at (131.78, 107.98) facing +x` |
| 2 | R-KEY-PU value `2k2 1%`→`4k7 1%` on `key-switch-network.kicad_sch`, not exported | `kicad.py check` | **yes** | `hardware/cluster/key-switch-network/netlist.yaml is STALE against its sheet - run: python3 tools/kicad.py export hardware/cluster/key-switch-network`; both board-netlists STALE; 5× `[parity] Value (R-KEY-PU-LH1) doesn't match symbol value (2k2 1%)`; every render and fab file STALE (44 problems) |
| 3 | A line appended to `fab/key-board-lh-F_Cu.gbr` | `kicad.py check` | **yes** | `hardware/boards/key-board-lh/fab/key-board-lh-F_Cu.gbr was edited after it was rendered` |
| 3b | `fab/key-board-lh-B_Paste.gbr` deleted | `kicad.py check` | **yes** | `… key-board-lh-B_Paste.gbr is missing` |
| 3c | A stray `fab/key-board-lh-In1_Cu.gbr` and `fab/old-rev-A-bom.csv` added | `kicad.py check`, `check-staleness.py` | **no** | `kicad: PASS - 3 source sheet(s), 2 board(s), 38 render(s) match their sources`; `PASS no live stale values` (K7-6) |
| 4 | LCSC of R-KEY-PU `C17520`→`C99999` on the sheet, not re-rendered | `kicad.py check` | **yes**, through the ledger's sheet inputs | `hardware/boards/key-board-lh/fab/key-board-lh-bom-jlc.csv is STALE: hardware/cluster/key-switch-network/key-switch-network.kicad_sch changed - run: python3 tools/kicad.py render hardware/boards/key-board-lh/fab`. **The command it names crashes** (K7-4) |
| 5 | `Assembly` field deleted from R-KEY-PU | `pcb.py render` | **yes**, refuses, rc 1, **after wiping `fab/`** | `pcb: R-KEY-PU-LH1 has no Assembly field (machine, hand or none) on its sheet`. Afterwards the three JLC files are deleted, the Gerbers and 3D PNGs are rewritten, and `kicad.py check` says the tool-written files `was edited after it was rendered` (K7-7) |
| 5b | `Assembly` `machine`→`none` on R-KEY-PU, then rendered as documented | `pcb.py render`, `kicad.py render`, `kicad.py check`, `pcb.py check`, `check-netlist.py --strict`, `merge-bom.py --check` | **no** | All PASS. The five pull-ups R-KEY-PU-LH1..5 are in **neither** `-bom-jlc.csv` nor `-hand-assembly.csv` (K7-3) |
| 6 | `hardware.kb_standoff_inset` 3.5→4.0 in `config/body.yaml`, not rebuilt | `cad.py check`; `check-staleness.py`; `pcb.py check`; `kicad.py check` | **yes** (cad) / no (pcb, kicad, by design) | `mechanical/cad/generated/params.scad does not match config/key-layout.yaml + config/body.yaml …`, `FAIL 2 CAD output problem(s)`; the staleness gate `FAIL … 3 cad`; `pcb.py check` `0 error(s)`; `kicad.py check` PASS |
| 6′ | … then `cad.py build pcb-geometry dxf-key-board-lh` | `pcb.py check` | **yes** | `error: [cad] standoff hole H1 is at (100.5, 139.0), the body CAD puts it at (101.00, 138.50)`, and the same for H2–H4 |
| 6b | `boards.key_board_t` 1.2→1.6, full `cad.py build` (+ `build clash`) | `cad.py check`, `check-staleness.py`, `pcb.py check`, `kicad.py check` | **no** | `PASS 43 CAD outputs match their sources`; `PASS no live stale values`; `pcb: … 0 error(s), 0 warning(s)`; `kicad: PASS`. `fab/key-board-lh-job.gbrjob` still says `"BoardThickness": 1.2` (K7-2) |
| 7 | CHAIN_SCK and CHAIN_SHLD labels swapped at J-CHAIN on `key-board-lh.kicad_sch`, then exported | `check-netlist.py --strict`, `kicad.py check` | **only against the old PCB** | `[parity] Pad net (/CHAIN_SHLD) doesn't match net given by schematic (/CHAIN_SCK). - PTH pad 9`; `check-netlist` rc 0 |
| 7′ | … then `layout --force`, `pcb.py render`, `kicad.py render` | `kicad.py check`, `check-netlist.py --strict`, `check-staleness.py` | **no** | `kicad: PASS`, `netlist rc=0`, `PASS no live stale values`. The key board's J-CHAIN.9 is now SCK; `key-chain-loom/netlist.yaml` still says `J-CHAIN-KEY-LH.11` (K7-1) |
| 8a | `layout.yaml` `silk.at` moved off the board | `pcb.py layout` | **yes** | `pcb: silkscreen label 'WOODY key board LH' would sit off the board at (90.0, 137.5)` |
| 8b | `silk.at` at [119.5, 12.5]: anchor inside, text overhanging ~14.6 mm | `pcb.py layout`, `pcb.py check` | **layout: no**. **check: warning only**, which neither check fails on | `warning: [silk_edge_clearance] Silkscreen clipped by board edge … PCB text 'WOODY key board LH' on B.Silkscreen` (text bbox x 179.5–195.65, edge at 181.05) (K7-5) |
| 8c | Silk text `LH3` moved 40 mm off the board in the `.kicad_pcb`, then re-rendered | `pcb.py check`, `pcb.py render`, `kicad.py check` | **no** | `pcb: … 0 error(s), 0 warning(s)`; `kicad: PASS`; the label is in `fab/…-B_Silkscreen.gbr` (K7-5) |
| 9 | SW-LH3's footprint deleted from the `.kicad_pcb` | `pcb.py check` | yes, as a **crash** | `AttributeError: 'NoneType' object has no attribute 'GetPosition'`; `kicad.py check` prints `pcb check failed:` and a traceback, and the DRC report is lost (K7-12) |
| 10 | `rules.power_track` 0.4→3.0, so V3V3 cannot route | `pcb.py layout --force` | layout **exits 0**; `check` catches it | `pcb: could not route V3V3_CHAIN_LH - move parts in layout.yaml and re-run` / `pcb: wrote …` rc 0; then `pcb.py check`: `10 error(s)`, all `[unconnected]` (K7-11) |

## Findings

### K7-1 [high] Nothing checks the key board's J-CHAIN pinout against the ribbon's netlist. A swapped chain pin passes every gate once the PCB is re-laid

**Node:** `J-CHAIN` (key-board-lh) ↔ `J-CHAIN-KEY-LH` (`hardware/interfaces/key-chain-loom/netlist.yaml`); nets `/CHAIN_SCK`, `/CHAIN_SHLD`, and by the same route `V3V3_CHAIN_LH` and `GND_CHAIN`.

- **The two ends are recorded in different places.** The board's J-CHAIN pin map lives only in `key-board-lh.kicad_sch` and its export, `board-netlist.yaml`. The ribbon's pin map for the same connector is `J-CHAIN-KEY-LH` in the loom's hand-written netlist: `CHAIN_SCK: … J-CHAIN-KEY-LH.11`, `CHAIN_SHLD: … J-CHAIN-KEY-LH.9` [repo `hardware/interfaces/key-chain-loom/netlist.yaml:144-158`].
- **Nothing outside `tools/kicad.py` reads `board-netlist.yaml`** [run: `grep -rn "board-netlist" tools/*.py | grep -v '^tools/kicad.py'` → no output].
- **`check-netlist.py --strict` does not join the two ends.** It stayed rc 0 with the pins swapped [run, breakage 7].
- **The only thing that caught the swap was schematic parity against the existing PCB** (breakage 7). After `layout --force` and the renders, every gate passed (breakage 7′).
- **This is the one connection whose error the README says is destructive:** "A cable without `-RN2` puts 3V3 on a ground pin" [repo `hardware/boards/key-board-lh/README.md`, Bring-up 2]. A wrong pin on the board side is the same fault, and nothing catches it.

**Fix.** Have `kicad.py check`, or `check-netlist.py`, resolve each board's `J-CHAIN.<n>` net against the loom netlist's `J-CHAIN-KEY-<suffix>.<n>`, applying the `-RN2` map where it belongs. Better, export the loom's key-board side from the board sheet once the loom migrates.

### K7-2 [high] Board thickness is taken from the body CAD once, at layout, and never checked again. A CAD change to `boards.key_board_t` leaves a 1.2 mm Gerber job under an all-green gate

**Node:** figure `boards.key_board_t`; `pcb-geometry.echo` "board thickness"; `tools/pcb.py` `new_board` / `cmd_check`; `fab/key-board-lh-job.gbrjob`.

- **Layout reads the thickness.** `new_board` sets it from the echo: `ds.SetBoardThickness(MM(geo.get("thickness", 1.6)))` [repo `tools/pcb.py:132`].
- **Check does not.** `cmd_check` compares only switches, standoffs and J-CHAIN [repo `tools/pcb.py:510-528`]. tooling.md §4 lists "board thickness" among what comes from `pcb-geometry.echo` [repo `docs/reference/tooling.md:233`].
- **Demonstrated end to end** (breakage 6b). With `key_board_t: 1.6` and a full CAD build:
  - the echo reads `"board", "thickness", 1.6`;
  - `cad.py check`, `check-staleness.py`, `pcb.py check` and `kicad.py check` all PASS;
  - the job file sent to JLC still says `"BoardThickness": 1.2` [run].
- **The same shape applies to two other layout-time inputs:**
  - the switch model's z offset, from `switch.pcb_below_seat` [repo `tools/pcb.py:394-400`];
  - the outline's shape, from the DXF. Only its size is checked, and only indirectly, through the standoffs, which are inset from the edges.
- **Silent default.** A missing `board` echo row silently defaults to 1.6 mm (`geo.get("thickness", 1.6)`).

**Fix.**
- In `cmd_check`, compare `GetBoardThickness()` with `geo["thickness"]`.
- Compare each `SW-*` model's `m_Offset.z` with `switch.pcb_below_seat`.
- Compare the `Edge.Cuts` segments with `dxf_segments(...)`.
- Make a missing `thickness` a hard error, not 1.6.

### K7-3 [medium] `Assembly = none` on a real part drops it from both the JLC BOM and the hand-assembly list, and every check passes

**Node:** `tools/pcb.py` `assembly_files`; `fab/key-board-lh-bom-jlc.csv`, `fab/key-board-lh-hand-assembly.csv`; `R-KEY-PU-*`.

- **The code.** `assembly_files` writes `machine` parts to the BOM and `hand` parts to the hand list. It passes `none` without a word [repo `tools/pcb.py:552-565`].
- **Demonstrated** (breakage 5b). With R-KEY-PU's `Assembly` set to `none` and everything re-rendered:
  - the BOM lists R-KEY-PU-FREE3 but none of R-KEY-PU-LH1..5, and the hand list does not have them either;
  - `kicad.py check`, `pcb.py check`, `check-netlist.py --strict` and `merge-bom.py --check` all PASS [run].
- **Nothing reconciles the parts actually ordered with the parts on the board.** The board-level count is in `board-netlist.yaml`, and the BOM rows' quantities are in `hardware/*/bom.csv`.

**Fix.** Allow `none` only for an allowlist of row kinds, such as `TP-*` and board-only `H*`, or require a `Note` stating why. Also assert that machine + hand + none covers every placed footprint, and print the `none` list on every render.

### K7-4 [medium] `kicad.py check`'s remedy for a stale PCB render or `fab/` file names the wrong tool, and for `fab/` a directory that makes it crash

**Node:** `tools/kicad.py` `cmd_check` (ledger loop); ledger rows of kind `pcb`.

- **What it prints.** For every stale ledger row, it prints `run: python3 tools/kicad.py render {os.path.dirname(r['render'])}` [repo `tools/kicad.py:484-485`].
  - For `fab/*` that is `kicad.py render hardware/boards/key-board-lh/fab`, which crashes: `CalledProcessError: … kicad-cli sch export pdf … key-board-lh/fab/fab.kicad_sch … exit status 3` [run].
  - For `*.pcb-*.png` it is `kicad.py render hardware/boards/key-board-lh`. That re-renders only the schematic pages, and `ledger_set(kind="sch")` never touches the pcb rows [repo `tools/kicad.py:305`], so they stay stale.
- **The right command** is `python3 tools/pcb.py render hardware/boards/key-board-lh`.
- **Every sheet edit produces 19 such lines** (breakages 2 and 4), so this is the first thing a person fixing a board reads.

**Fix.** Keep the `kind` in the ledger, or infer it from `.pcb-` / `/fab/`, and print `pcb.py render <board>` for pcb rows. Deduplicate the remedy to one line per board.

### K7-5 [medium] The "no silkscreen label off the board" guarantee exists only inside `layout`, and only for the text's anchor. The checks let an off-board label through

**Node:** `tools/pcb.py` `silk_text`, `cmd_check`; `tools/kicad.py` `cmd_check`; B.Silkscreen.

- **What the docs claim.** tooling.md says: "A silkscreen label wholly off the board is not a DRC error … `pcb.py` refuses to place one" [repo `docs/reference/tooling.md`, §4 "Learned the hard way"]. The `.kicad_pcb` is the source after layout, and hand edits are expected [repo `hardware/boards/key-board-lh/README.md`, Files].
- **The guard tests only the anchor point.** It checks it against the edge *bounding box*, not the outline and not the text's extent [repo `tools/pcb.py:230-232`].
- **What the breakages showed:**
  - **8c.** A label moved wholly off the board in the `.kicad_pcb` gave `pcb.py check` 0 errors and 0 warnings, and after `pcb.py render`, `kicad.py check` PASS. The label is in the silkscreen Gerber [run].
  - **8b.** A title anchored inside but overhanging the edge by about 14.6 mm was placed by `layout`. KiCad reports it only as a **warning** (`silk_edge_clearance`). `cmd_check` does not fail on warnings [repo `tools/pcb.py:529-533`], and `kicad.py check` forwards only lines starting `error` [repo `tools/kicad.py:469`].
- A cosmetic point: the guard sits *above* the function's docstring [repo `tools/pcb.py:230-235`], so the "docstring" is a bare string expression.

**Fix.**
- In `cmd_check`, fail on any B/F.Silkscreen item whose bounding box is not inside the `Edge.Cuts` polygon.
- Promote `silk_edge_clearance` to an error, or treat all DRC warnings as errors on this board, which has 0 today.
- In `silk_text`, test the text's bbox against the outline.

### K7-6 [medium] Stray files in `fab/` are invisible to every check, and the README says to upload every `.gbr` in it

**Node:** `tools/kicad.py` `cmd_check` (ledger); `hardware/boards/key-board-lh/fab/`.

- **What the ledger checks.** Only files it lists: missing, edited, stale [repo `tools/kicad.py:473-487`]. An extra `fab/key-board-lh-In1_Cu.gbr` and `fab/old-rev-A-bom.csv` gave `kicad: PASS` and `check-staleness: PASS` (breakage 3c) [run].
- **What the README says.** "Upload `fab/` zipped: every `.gbr` file, the `.drl` and the `.gbrjob`" [repo `hardware/boards/key-board-lh/README.md`, Ordering].
- **Who cleans up.** `pcb.py render` `rmtree`s `fab/` [repo `tools/pcb.py:615`], so a re-render removes strays. Nothing detects them in between, and git would carry one.
- **The same gap applies** to any unledgered `*.pcb-*.png` or `*.sch.png` beside a board.

**Fix.** In `cmd_check`, list `fab/` and every `*.pcb-*.png` / `*.sch.png` in the board directories, and fail on any file without a ledger row. The orphan-output rule `cad.py check` already applies to the body is the model.

### K7-7 [low] A refused `pcb.py render` has already destroyed `fab/` and rewritten the renders

**Node:** `tools/pcb.py` `cmd_render` / `assembly_files`.

- **The order of operations.** `cmd_render` renders the 3D and copper PNGs, runs `rmtree(fab)` and exports Gerbers and drill, and only then calls `assembly_files`, which is where the `Assembly`/`LCSC` refusals are [repo `tools/pcb.py:596-623`].
- **What that leaves** (breakage 5):
  - the three JLC files deleted;
  - 9 Gerbers, the drill, the job file and both 3D PNGs rewritten, with no ledger update;
  - `kicad.py check` then blames a human: `… was edited after it was rendered` [run].

**Fix.** Run `assembly_files`' validation first, from the sheets, before touching any output. Or render into a temporary directory and swap it in only on success.

### K7-8 [low] `pcb.py check` checks each switch's position but not its rotation

**Node:** `tools/pcb.py` `cmd_check`; `SW-LH1..5`; the echo's switch rotation field.

- **The code.** The body CAD emits a rotation per switch, and layout applies `r + switch_rot` [repo `tools/pcb.py:404-407`]. `cmd_check` unpacks `(x, y, r)` and never uses `r` [repo `tools/pcb.py:510-515`].
- **Demonstrated** (breakage 1b). A switch rotated 180° in place produced no `[cad]` line. It was caught only because its pads left their tracks, which a hand re-route would repair [run].
- **Why it matters.** The KS-33's pins are asymmetric (pin 1 at (−4.4, −4.7), pin 2 at (+2.6, −5.75) [repo `hardware/boards/key-board-lh/layout.yaml`, Placement comment]), so a rotated footprint no longer matches the plate cutout's switch.

**Fix.** Compare `fp.GetOrientationDegrees()` with `(r + lay.get("switch_rot", 0)) % 360` and check `not fp.IsFlipped()`.

### K7-9 [low] The "ribbon's no-parts strip" is still documented as coming from `pcb-geometry.echo`, but the body CAD stopped emitting it, and `pcb.py` silently does without

**Node:** `pcb-geometry.echo` kind `ribbon`; `tools/pcb.py` `cad_geometry` / `no_parts`; `docs/reference/tooling.md` §4.

- **The docs.** tooling.md §4's source table lists "the ribbon's no-parts strip" as coming from `pcb-geometry.echo` [repo `docs/reference/tooling.md:233`]. ADR 0020's amendment says "the no-parts strip is under the header, its plug and the ribbon's hairpin" [repo `docs/decisions/0020-key-boards-screw-to-the-plate.md:73-74`].
- **The CAD.** The echo has no `ribbon` row for either cluster [repo `mechanical/export/pcb-geometry.echo`]. The emitter `echo("PCB", cl, "ribbon", …)` was removed in `c696b34` [run: `git show c696b34 -- mechanical/cad/woody_body.scad`].
- **The tool.** `pcb.py` still parses the row and adds the zone only `if geo["ribbon"]` [repo `tools/pcb.py:71-72, 432-434`], so the missing input is silent.
- **The board.** The committed board has **no** `ribbon` rule area [run: `grep -c 'name "ribbon"' key-board-lh.kicad_pcb` → 0].
- **Where the body CAD does keep a strip clear.** Under the hairpin, but only for the *main board's* parts solid [repo `mechanical/cad/woody_body.scad:1038-1040`].
- **Not settled here.** Whether the key board's underside parts must also keep off the hairpin (x 80.4–120.7 mm for LH [repo `mechanical/drc.echo:52`], where the register and LH4/LH5 sit) is a mechanical question for K5 [not verified here].

**Fix.** Either emit the key-board strip again from the CAD and make its absence an error in `cad_geometry`, or delete `no_parts` and the tooling.md row and say where the constraint now lives.

### K7-10 [low] `tools/setup-env.sh` does not install the 3D models the renders need. On a fresh machine `pcb.py render` silently drops every part body, and the ledger accepts it

**Node:** `tools/setup-env.sh`; `tools/pcb.py` `cmd_render`; `*.pcb-3d-*.png`.

- **What the script installs.** `kicad kicad-symbols kicad-footprints`, with `--no-install-recommends` [repo `tools/setup-env.sh`]. It does not install `kicad-packages3d` or fetch the four models. tooling.md says those "came from gitlab.com/kicad/libraries/kicad-packages3D tag 9.0.0 into /usr/share/kicad/3dmodels/", by hand [repo `docs/reference/tooling.md` §4].
- **What this machine has.** Exactly those files, plus an empty `Connector_FFC-FPC.3dshapes/` left from the FFC era [run: `ls /usr/share/kicad/3dmodels/*/`].
- **Simulated fresh machine.** `KICAD9_3DMODEL_DIR` pointed at an empty directory:
  - `kicad-cli pcb render` exits 0 with no warning;
  - the 74HC165 and every 0805 vanish from the picture [run: both PNGs compared by eye and by pixel bbox].
  - `pcb.py render` would ledger that image as current.
- **Other prerequisites** [from memory, not tested: no fresh container was available]. The script calls `curl` and `gpg` before installing anything, and neither is in a minimal `ubuntu:24.04` image. `set -euo pipefail` would stop it there.
- **What *is* covered:** `librsvg2-bin` (`rsvg-convert`) and `shapely` are.

**Fix.** Have setup-env fetch the four `.step` files, or install `kicad-packages3d` if 3 GB is acceptable. Have `cmd_render` fail when a footprint's model path does not resolve (`os.path.exists` after expanding `${KICAD9_3DMODEL_DIR}` / `${KIPRJMOD}`). Add `curl gnupg ca-certificates` to the apt list.

### K7-11 [low] `pcb.py layout` exits 0 when a net fails to route, after overwriting the source board

**Node:** `tools/pcb.py` `cmd_layout`.

- **The code.** A failed route is printed and the board is saved anyway, with return `None` → exit 0 [repo `tools/pcb.py:471-483`].
- **Demonstrated** (breakage 10): `could not route V3V3_CHAIN_LH …` / `pcb: wrote …`, rc 0 [run].
- **Mitigation.** `pcb.py check` does catch it (10 `[unconnected]`). But a script chaining `layout && render` would render a broken board.

**Fix.** Return 1 when `failed` is non-empty. Consider writing to a temporary file and only then replacing the `.kicad_pcb`.

### K7-12 [low] `pcb.py check` crashes instead of reporting when a checked footprint is missing, and the DRC report is lost with it. `layout`/`check` on a board without `layout.yaml` also crash with tracebacks

**Node:** `tools/pcb.py` `cmd_check`, `build`, `drc`.

- **Missing footprint.** `FindFootprintByReference` can return `None`. It is guarded for the standoffs but not for `SW-*` or `J-CHAIN` [repo `tools/pcb.py:511-513, 523-526`]. Breakage 9: `AttributeError: 'NoneType' object has no attribute 'GetPosition'`. The DRC violations it had already collected, including parity's "missing footprint", are never printed [run].
- **The right-hand board.** It has no `layout.yaml` and no `.kicad_pcb` [run: `ls hardware/boards/key-board-rh`].
  - `pcb.py layout` → `FileNotFoundError: … key-board-rh/layout.yaml`.
  - `pcb.py check` → `FileNotFoundError: … drc.json`, because `drc()` ignores kicad-cli's exit status [repo `tools/pcb.py:490-492`] [run].
  - `kicad.py check` correctly skips a board without a `.kicad_pcb`.

**Fix.** Treat a missing footprint as an `error: [cad] SW-x is missing` line. Check the return code in `drc()`. Give `layout` a one-line message pointing at the LH `layout.yaml` as the pattern.

### K7-13 [advisory] Re-layout reproduces the geometry exactly, but no file byte for byte, and nothing in `tools/` can say "same board"

**Node:** `pcb.py layout` output; `fab/`; `hardware/SHEETS.csv`.

- **The `.kicad_pcb`.** Regenerating the unchanged board gave a 7,356-line diff: 3,678 lines each way, all fresh UUIDs and footprint order (SW-LH1/LH2 swapped places in the file). The geometry was identical (table above) [run: `git diff --stat`].
- **Knock-on churn.** The `.kicad_pcb` blob changes, so all 19 pcb/fab ledger rows go stale.
  - The Gerbers change by timestamp, aperture renumbering and object order.
  - The 3D renders change 6–7 % of their pixels (ray-tracer noise).
- **What that costs.** A reviewer asking "did the layout change?" cannot answer it from git or from any check. It had to be answered here with an ad-hoc pcbnew script.

**Fix (optional).**
- Add a `pcb.py fingerprint` (sorted footprints, tracks, vias, filled-zone areas → hash) and record it in the ledger beside the blob.
- Seed KIIDs deterministically, as the sheets already do.
- Pass `--no-x2`, or post-strip `CreationDate`, if byte-stable Gerbers are wanted.

### K7-14 [advisory] None of the PCB checks is in the commit gate, and after layout the board's design rules are checked against nothing

**Node:** `tools/check-staleness.py`; `.claude/settings.json` hook; `layout.yaml` `fab:`.

- **The gate.** `check-staleness.py` runs `cad.py check` but not `kicad.py check` or `pcb.py check` [repo `tools/check-staleness.py:1187`]. This is documented as "Not yet … because that needs KiCad installed" [repo `docs/reference/tooling.md` §4 "Not yet"]. Every breakage in the table left `check-staleness.py` at `PASS` except no. 6. KiCad *is* installed in the sessions that do this work, so the gate could run it when `kicad-cli` is present and skip otherwise.
- **The design rules.** After layout, the design rules live in the `.kicad_pcb`/`.kicad_pro`, and `cmd_check` reads `layout.yaml` only for `cluster` [repo `tools/pcb.py:507-508`].
  - Loosening a clearance or the annular minimum in KiCad's Board Setup would therefore pass silently.
  - The README's claim that JLC's limits "are in `layout.yaml` `fab:`, so KiCad's DRC checks this board against them" is true of the first layout only [repo `hardware/boards/key-board-lh/README.md`, Ordering].

**Fix.**
- Run `kicad.py check` from the staleness gate when `kicad-cli` exists.
- In `cmd_check`, assert the board's design settings are at least as strict as `layout.yaml` `rules:`/`fab:`.

### K7-15 [advisory] The documented full CAD rebuild did not complete within the documented `timeout 590`

**Node:** `docs/reference/tooling.md` §2 step 2; `tools/cad.py build`.

- **What the docs say:** "`timeout 590 python3 tools/cad.py build` … A full rebuild takes 2–5 minutes" [repo `docs/reference/tooling.md:74-76`].
- **What happened here.** The full build after breakage 6b was killed at 9 min 50 s with only `clash` left [run: `cad.py check` → `clash: STALE`]. `cad.py build clash` alone then took 4 min 39 s (user 10 m 50 s) [run].
- **Hedge.** Both ran while another `pcb.py layout` was running on the same 4 cores, so the numbers overstate the solo time. Treat this as "unverified: 2–5 min", not as a measurement of it.
- **Layout time.** The LH `pcb.py layout` took 4 min 35 s when run alone [run]. `pcb_route.Router.blocked` rebuilds a full obstacle grid twice per net [repo `tools/pcb_route.py:131-152, 313-314`], which is most of that.

**Fix.** Re-measure on an idle machine and state the figure with its provenance. Consider `build` without `clash` as the documented inner loop.

### K7-16 [low] The board README's "Rebuild and check" does not rebuild what a sheet edit makes stale

**Node:** `hardware/boards/key-board-lh/README.md` "Rebuild and check".

- **What the README lists:** `kicad.py export <board>`, `pcb.py check`, `pcb.py render`, `kicad.py check` [repo `hardware/boards/key-board-lh/README.md:41-46`].
- **What happens after a circuit-sheet edit** (breakage 2):
  - the circuit's `netlist.yaml` stays stale, because only the board is exported;
  - so do every `*.sch.png` of the circuit and of both boards, and the RH board's netlist, because there is no `kicad.py render`;
  - the final `kicad.py check` fails.
- tooling.md §3 has the full sequence [repo `docs/reference/tooling.md` §3 "Editing a circuit or a board", step 3]. The worked example's README does not point at it.

**Fix.** List the full sequence, or add one `tools/kicad.py rebuild <board>` that exports and renders the board's circuits, the board and every other board placing them, then runs `pcb.py render`.

## Paths this board does not exercise: read and run

- **Connector facing −x (right-hand geometry).** I synthesized an RH `layout.yaml` in the scratch copy: LH part positions shifted +108 mm, three parts added for RH6, and `power_nets: [V3V3_CHAIN_RH]`.
  - `pcb.py layout` routed every net and wrote the board.
  - `place_chain` chose rotation 180°, flipped, with pad 2 at −x of pad 1 (p1 x 251.36, p2 x 250.09): the mouth faces −x, as the echo's `-1` says.
  - `pcb.py check` reported only a courtyard overlap between my ad-hoc TP-3V3-RH and J-CHAIN, and **no `[cad]` error** [run].
  - The pin-1 dot logic (`dx > 0 → +1.0`) puts the dot away from the mouth on both boards [repo `tools/pcb.py:322-326`].
  - The RH board itself has **no `layout.yaml`** in the repository (K7-12).
- **A net with a single pad.** `route_net` returns True for fewer than 2 pads [repo `tools/pcb_route.py:311-312`]. `route()` also skips `unconnected-*` nets [repo `tools/pcb_route.py:417`]. Harmless.
- **A failed route** (breakage 10). The net's partial copper stays on the board and is not reported apart from "FAILED" [repo `tools/pcb_route.py:325-335`]. `failed` is never updated if a later rip-up group happens to route it [repo `tools/pcb_route.py:436-455`], so the "could not route" message can be wrong in the pessimistic direction.
- **A* state.** Turn cost depends on the incoming direction, but the closed set is keyed on `(layer, i, j)` only [repo `tools/pcb_route.py:182-207`]. A cell first reached from a costly direction is never re-expanded from a cheaper one. Routes are therefore not cost-optimal. They are still correct, and DRC is the proof, as the module says.
- **Heap ties.** A tie comparing `None` with a direction tuple cannot occur: pushes happen only on a strictly lower cost, so no state is pushed twice with an equal `g` [repo `tools/pcb_route.py:204, 213`].
- **Outline.** `dxf_segments` reads only `LINE` entities [repo `tools/pcb.py:80-93`]. `board_outline` requires one closed ring [repo `tools/pcb_route.py:70-89`]. An outline with an arc entity, or a cutout (a second ring), would fail with "board outline is not one closed ring". That does not happen today, because OpenSCAD writes `LINE`s.
- **`ledger_set` path matching.** It deletes rows whose `dirname` `startswith(rel)` [repo `tools/kicad.py:305`], so rendering `key-board-lh` would also drop the rows of a sibling named `key-board-lh2`. This is latent: no such sibling exists.
- **Machine side not enforced.** `assembly_files` writes `Top` in the CPL for any machine part on the top side [repo `tools/pcb.py:577`]. Nothing enforces the README's "every machine-placed part is on the bottom", which Economic PCBA requires [repo `hardware/boards/key-board-lh/README.md`, Assembly]. Today all machine parts are on the bottom [run: `-cpl-jlc.csv` Layer column].
