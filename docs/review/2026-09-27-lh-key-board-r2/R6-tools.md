# R6 — The board tools changed today (`tools/pcb.py`, `tools/pcb_route.py`)

**Slice:** R6, cold. I read only this wave's README under `docs/review/`.
**Revision measured:** `eebcdfb` (working tree at `36341bf`, which changes nothing under `tools/` or the board). `tools/` was frozen. I changed nothing in the repository except this file.
**Method:** I read the diff `git diff 383116e..eebcdfb -- tools/` (+301/−42 lines in two files) against `docs/reference/tooling.md` §3/§4 and `hardware/boards/key-board-lh/README.md`. Then I broke scratch copies (`scratchpad/R6/repo`, `layA`–`layD`) and ran the tools on them. Each breakage was made in its own directory, `hardware/v_<name>/key-board-lh/`, a copy of the board placed so that its `../../cluster` sheet paths still resolve. The copy was then mutated through `pcbnew` or by a JSON edit of the `.kicad_pro`, and `python3 tools/pcb.py check` was run on it. A control run (load and save with no change) passed with 0 errors `[run: brk.py control0/control1]`.

Provenance tags: `[repo path:line]`, `[run: …]` with the key output, `[calc]`, `[from memory]`.

---

## Findings

### R6-1 [high] `check_tracks` cannot see a join onto the middle of a track, and the committed board has a live 45° acid trap

**Node:** `pcb.py check_tracks`, `pcb_route.Router.square_joins`, net `/CHAIN_SER_LH` on F.Cu at (140.80, 113.30).

- **How the check works.** `check_tracks` groups track *endpoints* by (net, layer, µm-rounded point) and compares only tracks that share an endpoint `[tools/pcb.py:909-928]`. `square_joins` does the same with exact nm endpoints `[tools/pcb_route.py:425-482]`.
- **How the router makes a mid-segment join.** The router's A\* starts from every cell of the tree `[pcb_route.py:343-348]`. `commit` merges collinear runs into one segment `[pcb_route.py:266-300]`. So a branch usually joins the tree at a cell *inside* an existing segment, and neither function looks there.
- **Evidence on the real board.** I scanned every track endpoint that lies inside the length of a same-net, same-layer track `[run: py/scan.py on the committed .kicad_pcb]`. It found one: `mid-join /CHAIN_SER_LH F.Cu at (140.80,113.30) angles 135/45`.
  - The diagonal runs (142.4,114.9)→(140.6,113.1).
  - The branch runs (140.8,113.3)→(141.8,113.3), and (140.8,113.3) lies on that diagonal.
  - The join point is in no pad `[run: pad HitTest printed nothing]`.
  - The 45° wedge between the two tracks is exactly the acid trap the check exists to catch. `pcb.py check` reports `0 error(s)` `[run: pcb.py check hardware/boards/key-board-lh]`.
- **Deliberate breakage.**
  - A 27° join at a shared endpoint fires: `[run: brk.py t1_acute_end] error: [tracks] /KEY_LH5 on B.Cu: two tracks meet at 27 deg`.
  - A 45° join onto the middle of the segment (175.6,109.9)–(175.6,108.9) produces no `[tracks]` line: `[run: brk.py t4_acute_mid]`. The only output is KiCad's `track_dangling` for my deliberately dangling test stub.
- **Documents contradicted.** The board README revision row claims "no acute track junction" `[hardware/boards/key-board-lh/README.md:251]`, and the commit subject says "no acid traps".
- **Fix.**
  - In `check_tracks`, also test each endpoint against the interior of every same-net, same-layer track (projection parameter 0<k<1, distance under 1 µm), and fail if either angle is under 90°.
  - In the router, split the tree segment at the join cell when `commit` starts from an interior cell, so `square_joins` can see the join. Alternatively, give `square_joins` the same interior test.
  - Then re-layout, or re-route this one join by hand, and correct README rev A.

### R6-2 [high] Setting a non-fab DRC test to *ignore* hides it, and a whole unrouted net then passes `check`

**Node:** `pcb.py check_rules`, `FAB_TESTS` `[tools/pcb.py:824-826]`; the claims "`check` fails on … an unrouted connection, or a schematic-parity difference" `[docs/reference/tooling.md §4]` and `[README.md:77-79]`.

- **Cause.** `check_rules` fails a test set to `ignore` only when the test is in `FAB_TESTS`. `unconnected_items` is not in that list, and neither are the parity tests (`missing_footprint`, `extra_footprint`, `net_conflict`, `footprint_symbol_mismatch`), `shorting_items`, `items_not_allowed` (the standoff keep-outs), `courtyards_overlap`, `starved_thermal` or `track_dangling`. `kicad-cli drc` omits ignored tests from its report, so `check` has nothing to count.
- **Evidence.**
  - Every track and via of `/KEY_LH3` deleted, plus `"unconnected_items": "ignore"` in the `.kicad_pro`: **`0 error(s)`, exit 0** `[run: brk.py g1_whole_net_ign]`.
  - With one track deleted, the unconnected error disappears when the test is set to ignore (3 errors → 2) `[run: brk.py g1_ctl / g1_ign]`.
  - `C-BULK-CHAIN-LH` deleted from the board, plus `missing_footprint: ignore`: the parity error disappears (4 → 3; what remains is incidental `track_dangling`) `[run: brk.py g4_ctl / g4_ign]`.
  - Six such tests set to ignore at once: `0 error(s)` and no `[rules]` line `[run: brk.py g3_many_ignored]`.
  - For contrast, `clearance: ignore` is caught: `error: [rules] DRC test clearance is set to ignore` `[run: brk.py r2_ignore]`.
- **Why it matters.** "The `.kicad_pcb` is the source, edited in KiCad" `[tooling.md §4]`. Right-click → "Ignore this violation type" in KiCad writes exactly this setting into the `.kicad_pro`.
- **Fix.** Invert the list. Fail on *any* `ignore` except an explicit allowlist, each entry with its reason: `lib_footprint_mismatch` (set by `cmd_layout` on purpose), plus the ones this board already carries (`footprint_filters_mismatch`, `footprint_type_mismatch`, `missing_courtyard`, `npth_inside_courtyard`, `pth_inside_courtyard`) `[run: .kicad_pro rule_severities dump]`.

### R6-3 [medium] `network_parts` turns S and P the wrong way round on the `axis: y` pattern, so the KEY pads face *away* from the junction

**Node:** `pcb.py network_parts`, the axis-y branch `[tools/pcb.py:250-254]`; parts `R-KEY-SER-LH1..5` and `R-KEY-PU-LH1..5`.

- **What the code says.** The comment reads "pad 1 faces +y at 90 and -y at 270", and the code sets `rot = 270 if d > 0 else 90`.
- **Measured.** I placed an `R_0805_2012Metric` through `place()` on the bottom at each rotation `[run: inline script]`: at 90, pad 1 is at body (0, **−0.91**); at 270, body (0, **+0.91**). The comment is the wrong way round, and so is the code built on it. The x-branch's claims (−x at 0, +x at 180) measure true.
- **On the committed board** `[run: pad positions relative to each SW centre, PCB mm]`. All five keys are identical, but:

  | Part | Pad | Net | Position relative to its switch |
  |---|---|---|---|
  | S | 1 | KEY | (10, +3.61) |
  | S | 2 | SWITCH_LEG | (10, +1.79) |
  | P | 1 | 3V3 | (10, −1.79) |
  | P | 2 | KEY | (10, −3.61) |
  | C | 1 | KEY | (8.25, 0) |

  The junction is (10, 0). The KEY node therefore spans 7.2 mm, with the SWITCH_LEG and 3V3 pads *between* its S and P ends.
- **What this contradicts.** The code's own intent ("S and P end to end, their KEY pads facing across the junction … the node needs no via" `[pcb.py:212-217]`). Also "a T round its KEY node" `[layout.yaml:57]`, "`network_parts` expands it into a T round the key's node" `[tooling.md:243]`, and "`leg` … its SWITCH_LEG end, toward the switch's pin 1" `[pcb.py:229-231]`. In fact S's SWITCH_LEG pad is the end *nearer the junction*.
- **What still holds.** The board is electrically right (parity passes), and the owner's rule holds: every key's network is the same round its switch.
- **Fix.**
  - Change the branch to `rot = 90 if d > 0 else 270` and correct both comments.
  - Add a layout-time assert that each key's three KEY pads are the three pads nearest the junction.
  - Re-layout. This moves every key network's routing, so R3 should re-review the result.

### R6-4 [medium] Nothing holds the standoff copper keep-outs (ADR 0020) once the board is the source

**Node:** `pcb.py check_cad` (standoffs); the rule areas made by `keepout()` `[tools/pcb.py:581-598, 681-682]`.

- **The gap.** `check_cad` checks each standoff hole's *position* only `[pcb.py:981-986]`. With every rule area deleted from the board, `check` reports `0 error(s)` `[run: brk.py g2_no_keepouts]`. After that, a hand re-route or a re-fill in KiCad can put copper under the washer or the screw head. That is the second ground bond, and the short, that ADR 0020 forbids. The check also does not test that the holes are NPTH or their size.
- **Fix.** In `check_cad`:
  - For each standoff, require a rule area with no tracks, vias or pour, on both copper layers, covering radius `max(head, od)/2 + rules.clearance`.
  - Or, more directly, require that no copper lies within that radius.
  - Assert that H*n* is NPTH at the CAD's hole diameter.

### R6-5 [low] Most single-layer ground pads get no stitching via, and the tools doc still says every one does

**Node:** `pcb_route.Router.stitch_gnd` `[pcb_route.py:384-423]`; `[tooling.md:298-299]` "a stitching via beside every single-sided ground pad"; the docstring "Every single-layer GND pad gets a via" `[pcb_route.py:385]`.

- **Evidence.** I instrumented a scratch copy of `stitch_gnd` and ran `layout --force` `[run: layD]`. **7 of 11** single-layer GND pads got no via:
  - TP-GND at (150.00, 114.00);
  - U-KEYS pins 8 and 15 area: (151.14, 104.02) and (153.67, 104.02);
  - C-DECOUPLE at (153.35, 101.80);
  - C-KEY-LH2/3/4 at (136.35 / 156.35 / 174.35, …).
- **Why.** For 5 of the 7 a clear spot existed (`fallback` ≠ None), but the new rule rejects it because the pad already has a track and no ≥90° direction was free.
- **Why nothing is disconnected today.**
  - Ground routed fully (`route: GND_CHAIN ok`).
  - Every GND pad has at least 2 touching tracks `[run: GND pad scan]`.
  - DRC reports nothing unconnected.
  - No pad is joined *only* through the pour's thermal spokes on this board.
- **The latent case.** When ground routes only partially (`partial - pours and stitching vias must finish it`), `route_rest` islands are "reached by a ground route" too. The new rule can leave such an island with no via, and `layout` writes the board without saying so; only a later `check` finds out.
- **Fix.**
  - Correct the doc and the docstring to describe the rule.
  - In `stitch_gnd`, skip a pad only when its tracks reach the main tree (`route_net` knows which pads it joined), not when any track touches it.

### R6-6 [low] `square_joins` checks clearance against a stale copper list and ignores holes, keep-outs and the edge

**Node:** `pcb_route.Router.square_joins` `[pcb_route.py:456]`.

- **The bookkeeping.**
  - The moved track (X→fb) is tested only against `self.copper`, and `self.copper` is never updated after a move. The new `a2` and the moved `tb` are not appended, and the old `tb` geometry stays in the list. So a later move of *another* net is checked against positions that no longer exist.
  - `self.holes` (NPTH holes and the standoff keep-outs) are not tested, nor is `self.inside` (the edge clearance).
  - After 20 passes the loop stops silently.
  - `fa`/`fb` are SWIG references that alias the tracks' ends. My instrumented print showed `fa` equal to X *after* `ta.SetEnd(X)`. The code is correct only because `a2` is created before `ta` is changed, which is fragile.
- **Effect today.** None. The three squared joins (GND at 135.2,103.7; 3V3 at 160.2,111.9 and at 141.4,113.9 `[run: layD]`) pass DRC.
- **Fix.**
  - Replace the moved entries in `self.copper`.
  - Also test against `self.holes` and against `self.inside.contains(g)`.
  - Print a warning when the 20-pass limit is reached.
  - Copy `fa`/`fb` into new `VECTOR2I`s.

### R6-7 [advisory] `check_tracks` also fires where a via's copper fills the wedge

**Node:** `pcb.py check_tracks`.

- **Evidence.** A GND track leaving a 0.7 mm via at 60° to another is reported: `two tracks meet at 60 deg … an acid trap` `[run: brk.py t3b_via60]`.
- **Why that is not an acid trap** `[calc]`. The inner edges of two 0.25 mm tracks meet at a distance of (w/2)/sin(θ/2) = 0.125/sin 30° = 0.25 mm from the via centre. That is inside the via's radius of 0.35 mm, so the via's copper closes the wedge. By the same formula any join above 41.9° at this via is closed (sin(θ/2) > 0.125/0.35).
- **Where it does fire correctly.** At 21° the check fires and the wedge is real `[run: brk.py t3_via]`. A 90° T is quiet: the committed board has five 3-way junctions at exactly 90.0° and no report `[run: scan.py]`.
- **Fix.** Exempt a join whose inner-edge meeting point lies inside a via or pad of the same net. Or keep the conservative rule and say so in tooling.md.

### R6-8 [low] A filled silk shape is exempt from the line-width check, so a 0.05 mm sliver passes

**Node:** `pcb.py check_silk` `[pcb.py:890-892]` ("a filled shape prints its fill").

- **Evidence.** A filled 5 × 0.05 mm rectangle on B.SilkS in clear board: `0 error(s)` `[run: brk.py s6_sliver_141.0, s6_sliver_131.0]`. It is below `fab.silk_line_min` 0.15 and would not print.
- **Fix.** For a filled shape, fail when `shape.buffer(-line_min/2)` is empty or no longer covers the shape (`area` falls by much more than the perimeter × line_min/2).

### R6-9 [low] The `networks:` input is not validated

**Node:** `pcb.py network_parts` `[pcb.py:237, 245]`.

- An `except:` key that names no switch (`lh3` for `LH3`) is silently ignored, and the pattern is applied `[run: bld.py e2_typo → C-KEY-LH3 still at 157.3,121.5]`. The README's own procedure for the next board ("goes under `except:`, with the reason") depends on this entry working.
- Any `axis` other than `"x"` (`"Y"`, `"z"`) is silently treated as y `[run: bld.py e3_axis]`.
- The message for a turned switch says "give it an except: entry", but an except entry without `at` still exits.
- **Fix.** Exit on an except key that is not in `geo["switches"]`, on `axis` not in {x, y}, and on `leg`/`c` not ±1. Word the message "an except: entry with its own `at`".

### R6-10 [low] tooling.md §4 and the board README do not describe what changed today

**Node:** `[docs/reference/tooling.md §4 "check fails on", "The router"]`, `[hardware/boards/key-board-lh/README.md:77-86]`.

Neither document says:
- that `check` fails on an acute same-net junction;
- that the router squares acute joins (`square_joins`);
- that it drops a pad stub that would make an acute angle (`pad_stub`'s `prev`);
- that it withholds a stitching via from a pad that already has a track (R6-5).

tooling.md still says every single-sided ground pad gets a via. Rule 1 of CLAUDE.md applies: the doc drifted in the same commit as the code.

**Fix.** Add these to both lists, and correct the stitching sentence.

### R6-11 [advisory] Re-running `layout` produces identical geometry but a different file

**Node:** `pcb.py cmd_layout` / `build`.

- **Evidence.**
  - Two independent `layout --force` runs gave identical geometry: every track, via, footprint, silk item and zone-fill area, including against the committed board `[run: py/fpr.py fingerprints of repo, layA and layB → 435 lines each, diff empty]`. Both boards pass `check`.
  - The files themselves differ in 5,022 lines between the two runs, and each run differs from the committed file by 2,685 lines. Only part of that is UUIDs: KiCad's footprint order changes too.
- **Consequence.** A no-op re-layout marks 20 ledger rows STALE and shows as a whole-file diff.
- **Fix.** Derive KIIDs deterministically, e.g. `uuid5` of the reference or the item. Or document that a re-layout must be followed by `render`.

### R6-12 [advisory] `fit_footprint_silk` drops silk without a word

**Node:** `pcb.py fit_footprint_silk` `[pcb.py:333]`.

- **Evidence.** All six test pads' library silk rings are gone. `TestPoint_Pad_D1.0mm` has 1 circle in the library and 0 on the board `[run: library vs board silk item count]`.
- **Why that is acceptable.** The TP labels remain, and the U-KEYS pin-1 polygon was kept, so the README's "pin 1 … marked by its footprint" still holds `[same run: 7/7 items kept]`.
- **Why it still matters.** The removal is silent. A future footprint whose pin-1 mark sits near its pad would lose it with no report.
- **Fix.** Print what was removed per footprint. Fail if a removed item is the footprint's only one on that silk layer, or keep a named pin-1 mark.

### R6-13 [advisory] The silk error message names an unnumbered NPTH pad as "pad ''"

**Node:** `pcb.py check_silk` messages. For example: `… from H1 pad 's mask opening` `[run: brk.py s3_offboard]`.

**Fix.** Name an unnumbered pad by its footprint alone ("H1's hole").

---

## Tested and found working

| What | Breakage | Result |
|---|---|---|
| `check` on the real board | none | `0 error(s)` `[run]` |
| acute join at a shared endpoint | 27° stub at a KEY_LH5 junction | `[tracks] … 27 deg` fires |
| 90° T junctions | 5 on the real board | quiet |
| silk text height | `CB DNP` at 0.8 mm | `[silk]` and KiCad `text_height` both fire |
| silk text stroke | 0.10 mm | `[silk]` and `text_thickness` fire |
| silk line width | board line 0.10 mm; one U-KEYS footprint line 0.10 mm | both fire (`[silk] … 0.1 mm wide`) |
| silk off the board | top title partly off; line wholly off | "partly off" / "wholly off" fire |
| silk to pad | line 0.08 mm from C-KEY-LH1 pad 1, same side | fires at 0.080. The same line on F.SilkS (other side) is correctly quiet |
| design settings | `min_clearance` 0.15, `min_text_height` 0.8, `min_via_annular_width` 0.1 in the `.kicad_pro` | each `[rules]` fires |
| a fab test set to ignore | `clearance: ignore` | fires |
| CAD: switch | SW-LH1 moved 0.1 mm; turned 180°; SW-LH2 model z = 0 | each `[cad]` fires |
| CAD: J-CHAIN | flipped to top; turned 180° about its pad centre | "on the top side", "facing −x" fire |
| CAD: thickness | stackup 1.6 mm | fires |
| CAD: standoff | H1 moved 0.1 mm | fires |
| CAD: outline | one edge segment moved | `invalid_outline` + `[silk]`/`[cad]` "not one closed shape" |
| `layout` determinism | two runs | identical geometry, and identical to the committed board (see R6-11 for the file text) |
| `layout` refusal | `rules.track` 1.1 | `could not route /CHAIN_SHLD, /CHAIN_SER_LH, /HOP_LH_LT, /KEY_LH5 … left as it was`, exit 1; `.kicad_pcb` and `.kicad_pro` md5 unchanged; no `.layout-*` left behind |
| silk refusal | `silk.top_at` on a switch | `pcb: the top silkscreen title at layout.yaml silk.top_at is not clear` (exit before any write) |
| `networks:` pattern | real board | all five keys' pads identical relative to their switches `[run]` (but see R6-3) |
| top and bottom key labels | real board | each `LHn` is nearest its own switch / C-KEY (next nearest ≥ 10 mm away) |
| J-CHAIN marks | real board | the arrows on both sides point the same PCB direction (`mx` ⇔ `dx<0`, `[pcb.py]` logic) |
| `kicad.py check` | stray `fab/stray.gbr`; an edited `F_Cu.gbr`; a deleted `NPTH.drl`; the `.kicad_pcb` changed without re-render | "in no ledger row", "edited after it was rendered", "is missing", "B_Cu.gbr and 19 more STALE" |
| `route_first` | code | sorts after power, in list order `[pcb_route.py:528]` |
| `merge_tracks` after `square_joins` | code | leaves the new T alone (3 ends at X) |
| `pad_stub` acute test | code | sign is correct (dot product > 0 ⇒ < 90°) |
| every GND pad connected | real board | yes, by tracks (R6-5 for the vias) |
