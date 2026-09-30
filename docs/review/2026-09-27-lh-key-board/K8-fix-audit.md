# K8 — Audit of today's fixes (2026-09-27), for the four recorded shapes

**Slice:** K8. **Revision:** `d46a3b0`. **Cold:** nothing under `docs/review/`
read except this wave's README. **Tools:** run, not changed; the tree was
left as found except for this file.

**Scope.** The 14 commits of 2026-09-27 (`34f17f2` … `d46a3b0`), weighted on
the seven that touch the key boards and the chain: `12d447d` (first PCB),
`5595f1a` (standoffs, ADR 0020), `f3fedff` (1.2 mm, corner standoffs),
`9d3dde1` (Samtec catalogue pages), `c696b34` + `27a3476` (flat flex/ZIF →
through-hole IDC, pin map 12−n/14−n), `d46a3b0` (full prints, −RN2, 13−n,
header dimensions, JLC rules, test pads, part numbers, board README).
Corpus per CLAUDE.md §6.

## Summary

Today's headline fixes landed cleanly. **The pin map is right everywhere**:
every live statement of the key-board J-CHAIN pinout says 13 − n (11 SCK,
9 SH/LD, 7 SER, 5 QH, 3 3V3, even pins ground), the two board netlists
agree, and the old 12 − n/14 − n map survives only in `notes.md` as dated
history. **The old header numbers (5.85, 7.1, 2.44) are gone** from every
prose and data file; the only hits are PCB/DXF coordinates. ZIF, FFC,
`ffc_conn_*`, 200528 and "tilt" survive only in dated, refuted-in-place prose.
`check-staleness`, `merge-bom --check` and `check-netlist --strict` pass.

What did not land is at the edges, and it has the recorded shapes:

- **Shape 4 (the serious one): ADR 0017's argument for IDC now cites a
  derivation that no longer derives the gap.** The fix deleted the old
  "17.4 mm gap" number — which was, and still is, the right gap — and left
  a `[calc]` recipe (twice the fold radius plus `boards.chain_hdr_h`) that
  was only true of the retired hairpin. Followed today it gives 15.5 mm
  (K8-1).
- **Shape 1:** the placement fix (corners, grown board) did not reach
  `config/body.yaml`'s own comment block or ADR 0020's point 5, which still
  say "between each pair of neighbouring switches", "the board stayed the
  same size", and "J-CHAIN at the board's end" (K8-2, K8-3). The 1.2 mm fix
  did not reach `switch.pcb_t`'s source line, which cites PCB-CLUSTER as
  1.6 mm and is marked `settled` although ADR 0020 says the main board's
  thickness is still to be decided (K8-4). The full-print fix did not reach
  `hardware/lib/README.md`'s "From" column (K8-6).
- **Shape 3:** tooling.md's "the four [3D models] this board needs" was
  counted when the Molex ZIF was on the board; it is three now (K8-5).
  `repo-maintenance.md` still says `fab/` is Gerbers/drill/placement
  ledgered against the `.kicad_pcb` alone; since `d46a3b0` it also holds the
  JLC BOM/CPL/hand list and every file is ledgered against the sheets too
  (K8-7).
- **Shape 2:** three ADR lines edited today to add "1.27 mm IDC since
  2026-09-27" still say the Matrix ribbon is **20-way** (24-way since ADR
  0018) — a fix line that restates a wrong value (K8-8).
- **Register (rule 2):** no forbidden pattern was added for any value
  retired today. The key-board pin map changed twice in one day and is
  restated in ten files with no register entry (K8-9).

No finding is high: nothing orders a wrong part or nets a wrong pin.

## Findings

### K8-1 [medium] ADR 0017's "why IDC was rejected" rebuttal cites a gap derivation that the hairpin fix broke; followed today it computes 15.5 mm, not the real 17.4 mm

**Node:** ADR 0017 amendment, *"Why the old reason against IDC no longer
holds"*; `drc.echo` "key-chain ribbon closed: hairpin leg and fold radius";
`boards.chain_hdr_h`.

- The paragraph says a 2.54 mm IDC stack of 13.1 mm (14.6 mm worst case) sits
  "in the gap between the boards `[calc: twice the fold radius in drc.echo
  "key-chain ribbon closed…" plus boards.chain_hdr_h]`, with parts on both
  boards, and fits nowhere" `[repo docs/decisions/0017-one-main-board.md:152-158]`.
- At `27a3476` the model's fold was `chain_r = (chain_zk - chain_zm) / 2`
  with both plug centres at `chain_hdr_h / 2` off their boards
  `[run: git show 27a3476:mechanical/cad/woody_body.scad, lines 857-859]`,
  so gap = 2r + `chain_hdr_h` = 2 × 5.775 + 5.85 = 17.4 `[calc; old
  drc.echo line 51: 5.775]`, and the ADR said "a 17.4 mm gap".
- `d46a3b0` moved the legs (main-board leg on the board, key-board leg under
  its socket): `chain_r = (chain_z_up - chain_z_low) / 2` with
  `chain_z_low = cb_top + chain_thumb_stub + ribbon_t/2` and
  `chain_z_up = chain_zk - plug_t/2 - 1.5` `[repo mechanical/cad/woody_body.scad:857-873]`.
  The recipe now gives 2 × 4.9375 + 5.59 = **15.47 mm**
  `[calc; drc.echo:51, body.yaml chain_hdr_h 5.59]`.
- The real gap did not change: `top_z − cb_top` = stub 1.05 + ribbon_t/2 0.4
  + 2r 9.875 + plug_t/2 1.525 + 1.5 + mouth_z 3.05 = **17.40 mm**
  `[calc from woody_body.scad:857-873; stub = 5.75 − (3.4 + 1.6) + 0.3 = 1.05]`.
- The same commit deleted "17.4 mm" from the sentence
  `[run: git show d46a3b0 -- docs/decisions/0017-one-main-board.md]`, so the
  one correct number was removed and the stale recipe kept. A reader who
  follows the recipe gets 15.5 mm, in which the 14.6 mm worst-case stack
  looks close to fitting, and "fits nowhere" then rests only on "with parts
  on both boards". The conclusion is weakened by its own citation.

**Fix:** state the gap by name, not by a formula about the ribbon. Either cite
a `drc.echo` line for the board-to-board gap (the model has `top_z` and
`cb_top`; a NOTE line such as "key board underside to main board top" costs
one `echo`), or cite "main board parts room under the key boards"
(`drc.echo:41`, 14.1 mm), which is the quantity the argument is really about.
Then check whether "fits nowhere" still holds against it.

### K8-2 [medium] `config/body.yaml`'s comment on the key-board standoffs still describes the retired placement ("between each pair of neighbouring switches")

**Node:** `config/body.yaml` `hardware.kb_standoff_*` block comment.

- The comment reads "an M2 self-clinching standoff pressed into the plate
  between each pair of neighbouring switches" `[repo config/body.yaml:714-716]`.
- That was `5595f1a`'s placement. `f3fedff` replaced it with one standoff
  per corner (ADR 0020 amendment), and the model says so:
  `drc.echo` "key-board standoffs" [4, 4] "one in each corner"
  `[repo mechanical/drc.echo:56]`; `pcb-geometry.echo` puts the LH ones at
  x = 40.5 and 117.5, both outside the switch row 50–108
  `[repo mechanical/export/pcb-geometry.echo]`.
- `f3fedff` added `kb_standoff_inset` with its corner rule to the same
  block `[repo config/body.yaml:743-747]` without changing the comment
  above it. This is a `.yaml`, where rule 2b allows no history.

**Fix:** "one M2 self-clinching standoff pressed into the plate at each
corner of the board (ADR 0020, amended), and an M2 screw up through the board
into it."

### K8-3 [medium] ADR 0020 point 5 still says the board "stayed the same size" and that J-CHAIN "sits at the board's end"; the amendment note in the same point corrects neither

**Node:** ADR 0020 decision point 5; J-CHAIN position (`pcb-geometry.echo`
"chain").

- Point 5's bullets: "`J-CHAIN` sits at the board's end with its cable
  entry facing the ribbon's fold" and "The board stayed the same size (the
  owner's choice over enlarging it)" `[repo docs/decisions/0020-key-boards-screw-to-the-plate.md:61-64]`.
- The same ADR's amendment grew the board: "if we need to increase the size
  of the board a little bit that would make sense" `[repo …0020…:93-94]`,
  and point 3 now makes it "a rectangle across the cavity" `[repo …0020…:36-38]`.
- J-CHAIN is mid-board: LH chain at x = 79, between LH2 (70) and LH3 (90),
  on a board spanning 37–121 (standoffs at 40.5/117.5, inset 3.5)
  `[repo mechanical/export/pcb-geometry.echo; calc 40.5 − 3.5, 117.5 + 3.5]`.
- The amendment note under point 5 `[repo …0020…:66-75]` covers the envelope
  and the rule name only.

**Fix:** extend point 5's dated note: "The board was grown in the amendment
(point 3), and `J-CHAIN` now sits between the switches where the model finds
room (`drc.echo` 'chain headers on the left_hand boards clear of the
switches')." Or strike the two bullets. They are prose, so the note may sit
beside them.

### K8-4 [low] `switch.pcb_t` still cites PCB-CLUSTER as 1.6 mm and is marked `settled`, although the key boards are 1.2 mm and ADR 0020 leaves the main board's thickness open

**Node:** `config/body.yaml` `switch.pcb_t` (1.6); PCB-CLUSTER; PCB-CARRIER.

- The source is "[adr] hardware/bom.csv PCB-CLUSTER and PCB-CARRIER,
  1.6 mm", status `settled` `[repo config/body.yaml:257-260]`.
- PCB-CLUSTER is "1.2mm (config/body.yaml boards.key_board_t)" since
  `f3fedff` `[repo hardware/cluster/bom.csv:4]`.
- ADR 0020 point 6: "The main board's thumb switches have the same
  arithmetic, and it is decided when the main board is laid out"
  `[repo docs/decisions/0020-…:84-85]`. That arithmetic gives
  5.10 − 3.4 − 1.6 = 0.1 mm of pin to solder on the main board
  `[calc, body.yaml:432 and 236]`, the same margin ADR 0020 rejected for the
  key boards. `settled` contradicts "decided when laid out" (shape 4).

**Fix:** source "hardware/carrier/bom.csv PCB-CARRIER, 1.6 mm (the key boards
are boards.key_board_t)", status `tbd`, decided_by "the main board's layout —
ADR 0020 point 6: 1.6 mm leaves ~0.1 mm of thumb-switch pin". The comment in
`woody_body.scad:781` needs no change.

### K8-5 [low] tooling.md counts "the four [3D models] this board needs"; since J-CHAIN became the model-less Samtec footprint it is three

**Node:** `docs/reference/tooling.md` §4 *Learned the hard way*, 3D models.

- The text says "the four this board needs came from … kicad-packages3D"
  `[repo docs/reference/tooling.md:295-296]`, written in `12d447d`
  `[run: git log -S'the four this board needs']`.
- At `12d447d` the board referenced four library models: C_0805, R_0805,
  SOIC-16 and `Molex_200528-0120…step` `[run: git show 12d447d:…kicad_pcb | grep model]`.
- At `d46a3b0` it references three library models (C_0805, R_0805, SOIC-16).
  The fifth model is the Gateron STEP from `datasheets/` `[run: grep '(model'
  hardware/boards/key-board-lh/key-board-lh.kicad_pcb]`. The next sentence
  of the same bullet says J-CHAIN "has no 3D model", which is the fix that
  moved the count.

**Fix:** "the three this board needs (0805 R and C, SOIC-16)", or drop the
number and name them.

### K8-6 [low] `hardware/lib/README.md` still says the J-CHAIN footprint's shroud comes from the catalogue page; the footprint and the Changed column say the full print

**Node:** `woody.pretty/IDC-Header_2x06_P1.27mm_Samtec_SHF_Horizontal`,
"From" column.

- From: "the shroud from Samtec's banked catalogue page
  (`datasheets/connectors/SAMTEC-SHF-1.27MM-SHROUDED-IDC-HEADER.pdf`)";
  Changed (same row): "…the full print, `SAMTEC-SHF-1XX-01-X-D-XX-PRINT.pdf`,
  sheet 2 section C-C" `[repo hardware/lib/README.md:9]`.
- The footprint's own `descr` was moved to the full print in `d46a3b0`
  `[run: git show d46a3b0 -- hardware/lib/woody.pretty/IDC-…kicad_mod]`.
- Related, and advisory: three `boards.chain_*` sources still cite the
  catalogue pages (`chain_hdr_l`, `chain_plug_t`, `chain_plug_l`)
  `[repo config/body.yaml:345, 380, 385]`. Four `decided_by` fields still
  say "with the full print" / "and its full print" although the print is
  banked and the values are now `nominal` from it `[repo config/body.yaml:346, 351, 356, 361]`.
  The catalogue values agree with the print (13.97 = 6 × 1.27 + 6.35 on
  both; the print's `(No OF POS x .050[1.27]) + .250[6.35] REF` `[run: pdftotext SHF print]`),
  so no number is wrong. Only the provenance and the open-item text are stale.

**Fix:** point the From column at the full print. Move the three sources to
the prints and rewrite the four `decided_by` as what is actually still open
(the part number and source, M4).

### K8-7 [low] `repo-maintenance.md` describes `fab/` as Gerbers, drill and placement, ledgered against the `.kicad_pcb`; since `d46a3b0` it also holds the JLC BOM, CPL and hand list, and every file is ledgered against the sheets too

**Node:** `docs/reference/repo-maintenance.md` §1 table, "Exported from the
layout".

- It says "`hardware/boards/*/fab/*` (Gerbers, drill, placement) …
  Ledgered in `hardware/SHEETS.csv` against the `.kicad_pcb`"
  `[repo docs/reference/repo-maintenance.md:22]`. Last touched in `12d447d`
  `[run: git log -3 -- docs/reference/repo-maintenance.md]`.
- `fab/` now holds 15 files, three of them the JLC BOM, CPL and hand-assembly
  list. Every ledger row lists `key-board-lh.kicad_sch@…` and the circuit
  sheets as inputs as well as the `.kicad_pcb`
  `[run: ls fab; grep bom-jlc hardware/SHEETS.csv]`. So a part-number edit on a
  circuit sheet makes `fab/` stale, and this page, the one CLAUDE.md says to
  read before touching generated files, does not say so. The board README
  and tooling.md §4 do say it `[repo hardware/boards/key-board-lh/README.md:27; docs/reference/tooling.md:246]`.

**Fix:** "(Gerbers, drill, placement, and the board house's BOM/CPL/hand
list) … ledgered against the `.kicad_pcb` and the sheets it was built from".

### K8-8 [low] Three ADR lines edited today to date the IDC change still call the Matrix ribbon 20-way (24-way since ADR 0018)

**Node:** `CBL-MCU-RIBBON` / `J-MCU` width; ADR 0018 decision 1.

- ADR 0009: "The key boards are on flat flex *(1.27 mm IDC since
  2026-09-27…)* and the Matrix on a 20-way ribbon; how its spare positions
  are used is open on `CBL-MCU-RIBBON`" `[repo docs/decisions/0009-enclosure-construction.md:643-645]`.
- ADR 0013: "…*(1.27 mm IDC ribbons since ADR 0017's 2026-09-27
  amendment)*; the Matrix is on the lid on a 20-way ribbon into `J-MCU`"
  `[repo docs/decisions/0013-two-mcu-split.md:244]`.
- ADR 0001's fenced drawing: "the Matrix is on the lid, 20-way ribbon to
  J-MCU" `[repo docs/decisions/0001-mcu-and-board-partitioning.md:82]`, in
  the block whose next lines `27a3476` edited.
- ADR 0018 decided "The Matrix ribbon is 24-way … It was 20-way"
  `[repo docs/decisions/0018-main-board-wiring-decisions.md:20-31]`, and
  ADR 0017 cites it correctly `[repo docs/decisions/0017-…:59-60]`. ADR 0009's
  "spare positions … open" is also answered by ADR 0018 (the spares became
  5 V and ground).
- `27a3476` edited the ADR 0009 and 0013 lines in place
  `[run: git show 27a3476 -- docs/decisions/0009… 0013…]`. The fix landed on
  the line that carries a stale value and did not touch it. No figure tracks
  the ribbon width, so the checker cannot see it.

**Fix:** "a 24-way ribbon (ADR 0018)" in all three, and drop "open" in 0009.
Consider a figure `mcu-ribbon-ways` (owner `carrier.md`) with forbidden
`20-way ribbon`. ADR 0018:31 and :61 narrate the change and need a
`false_positive_note`.

### K8-9 [medium] No forbidden pattern was added for any value retired today; the key-board pin map changed twice in a day and is restated in ten files with no register entry

**Node:** `config/figures.yaml`; the key-board J-CHAIN pin map
(`key-chain-loom.md` owns it).

- `figures.yaml` was touched once today, to reword two derivations
  `[run: git show 27a3476 -- config/figures.yaml]`. Its 38 figures include
  no pin map, header dimension, board thickness or connector part
  `[run: python3 over config/figures.yaml]`.
- The live 13 − n map is written out, not cited, in `key-chain-loom.md`
  (several places), `bom.csv` J-CHAIN/CBL-CHAIN/R-SER-TERM, `nets.yaml`
  (4 nets), `cluster-boards.md:33`, `key-register.md:21-26`,
  `key-switch-network.md:21,38`, the board README:106 and ADR 0017:163
  `[run: grep 'key-board[^.]{0,40}pins? [0-9]' over the corpus]`. All are right
  today. That is exactly the "restated, not cited" state that rule 1 says
  every past staleness defect grew from, and this fact has already moved
  twice.
- Grep-first counts for the retired spellings, corpus only
  (table below): `12 − k`/`14 − k`/"key-board pin 8" have **1 hit each, all
  in `notes.md`, as dated history**. `12-n`, `14-n`, `12 − n`, `14 − n`,
  `12-k`, `14-k`, "key-board pin 4", "pins 8 and 6", "12 SCK" have 0 hits.
  So patterns can be added now at almost no false-positive cost.

**Fix (rule 2's steps, in the spelling of each file):** add a figure
`key-board-chain-pinmap`, value "key-board pin = 13 − main-board pin (−RN2
cable)", owner `hardware/interfaces/key-chain-loom/key-chain-loom.md`, with
forbidden:
`12 − n`, `14 − n`, `12 − k`, `14 − k` (prose, U+2212),
`12-n`, `14-n`, `12-k`, `14-k` (CSV/YAML spelling),
`key-board pin 8`, `key-board pin 4`, `key-board J-CHAIN pin 8`,
`12 SCK, 10 SH/LD`, `pins 8 and 6`, and a `false_positive_note` for
`notes.md`'s dated paragraph. Add a `J-CHAIN`-part figure (or patterns on
`chain-connectors`) forbidding `ffc_conn`, `FFC-CHAIN` and `200528` outside
prose. Current hits are ADR 0017/0020, tooling.md and notes.md, all prose
with refutation wording; confirm each is exempted before committing. Do
**not** add bare `5.85`, `7.1` or `2.44`: they hit only coordinates in
`.kicad_pcb`/`.dxf`, and would fire on correct geometry.

### K8-10 [low] The JLC via rule is explained with the PTH ring figure, and `layout.yaml` still gives JLC's track/space from memory beside the banked page that contradicts it

**Node:** `layout.yaml` `rules.via` 0.7 and `fab.annular_min` 0.18;
tooling.md "Put the board house's limits in the DRC".

- tooling.md: "Adding JLC's 0.18 mm minimum ring caught the vias (0.6 on a
  0.3 drill = 0.15) and the header's pads … both grew"
  `[repo docs/reference/tooling.md:311-313]`. `layout.yaml` says the same:
  "0.2 ring on the 0.3 drill: JLC's 0.18 minimum" `[repo hardware/boards/key-board-lh/layout.yaml:19]`.
- The banked page gives 0.18 as the **PTH annular ring** absolute minimum
  (2-layer, 1 oz; 0.25 recommended). For **vias** it says only "Via
  diameter should be 0.1mm (0.15mm preferred) larger than Via hole size",
  with a 2-layer minimum of 0.15 hole / 0.25 diameter
  `[datasheets/fab/JLCPCB-PCB-CAPABILITIES.pdf, run: pdftotext, "Vias" and "PTH annular ring" rows]`.
  A 0.6/0.3 via met JLC's via rule. It failed KiCad's single annular-width
  constraint, which applies to vias too. Growing the vias costs nothing and is
  safe, but the stated reason puts a board-house rule on the page that the
  banked page does not state (shape 2).
- `layout.yaml`: "JLCPCB's standard 2-layer process allows 0.127 mm track and
  space [from memory]" `[repo hardware/boards/key-board-lh/layout.yaml:13-14]`;
  the page banked the same day gives 0.10/0.10 mm for 1 oz
  `[datasheets/fab/JLCPCB-PCB-CAPABILITIES.pdf, "Min. track width and spacing (1 oz)"]`.
  CLAUDE.md rule 3: the banked number wins.

**Fix:** tooling.md: "KiCad applies one minimum annular width to pads and
vias; set to JLC's 0.18 PTH minimum, it grew both". `layout.yaml`: cite the
banked 0.10/0.10 and drop `[from memory]`. Also consider citing the banked
page's thickness list (0.4…1.2…2.0) for `boards.key_board_t`, whose "1.2 mm
is a standard thickness at every board house" is still `[from memory]`
`[repo config/body.yaml:432; docs/decisions/0020-…:81]`.

### K8-11 [advisory] `boards.chain_plug_proud` (1.4) is "scaled" off prints that say DO NOT SCALE DRAWING

**Node:** `config/body.yaml` `boards.chain_plug_proud`, which sets the
hairpin's x extent, the footprint courtyard (9.51) and `chain_span`.

- Source: "its 5.08 height less the header's mouth-to-floor, about 3.67,
  which the print does not dimension (scaled)" `[repo config/body.yaml:362-366]`.
- Both banked prints carry "DO NOT SCALE DRAWING" in the title block
  `[run: pdftotext SAMTEC-SHF-1XX-01-X-D-XX-PRINT.pdf, lines 82, 159;
  SAMTEC-FFSD-XX-X-XX.XX-01-PRINT.pdf, line 83]`.
- It is honestly `tbd`, "decided_by: M4, on the first mated pair". It is
  recorded here because it replaced a value (2.44) that was *derived*,
  although from the wrong quantity, and it is now the least certain number
  in the stack. The fix's explanation should say it is a scale reading
  against the print's instruction, so nobody promotes it to `nominal`.

**Fix:** append "[scaled against the print's DO NOT SCALE note — a
placeholder until measured]" to the source.

### K8-12 [advisory] `chain-connectors` (4) is restated as "all four positions" in the row that says not to restate it, and in today's ADR text

**Node:** figure `chain-connectors`; BOM row J-CHAIN.

- J-CHAIN's notes: "Quantity is the tracked figure chain-connectors; do not
  restate it … THE SAME PART AT ALL FOUR POSITIONS" `[repo hardware/interfaces/key-chain-loom/bom.csv:2]`.
  The same phrase is in ADR 0017:120 (written today) and in
  `key-chain-loom.md:112,414`, the owner, which is allowed to state it.
- The value is right. This is the shape-3 precondition: a count stated beside
  the figure that owns it. The checker's patterns for `chain-connectors` are
  all old counts ("eight connectors", "Five connectors"…)
  `[run: figures.yaml chain-connectors.forbidden]`, so a future move from 4
  would not flag these.

**Fix:** "the same part at every `J-CHAIN` position (`chain-connectors`)".

### K8-13 [advisory] Smaller stale edges

- `mechanical/cad/woody_body.scad:757`: "there are no looms since ADR 0017 -
  the key boards are on flat flex and the Matrix on a ribbon" `[repo]`. A
  live comment in the §6 corpus. Changing the `.scad` re-fingerprints the
  renders, so fold it into the next model change.
- `docs/reference/ks33-geometry.md:134-136`: "on a 1.6 mm board it [the
  pole] protrudes 0.5–0.9 mm below the underside" `[repo]`. The page is cited
  as the source of the 1.2 mm decision (ADR 0020:80, body.yaml:432, tooling.md:338),
  but it has no 1.2 mm line. On 1.2 mm the pole protrudes 5.75 − 3.4 − 1.2 =
  1.15 mm (0.9–1.3 over the 3.2–3.6 window) `[calc, body.yaml:232,236]`.
  Nothing today depends on it; the page just has not heard.
- `mechanical/DESIGN.md:338`: the connector envelope "comes from the IDC
  header's banked page" `[repo]` — the full print since `d46a3b0`.
- **Method trap:** the command in this slice's brief,
  `git log --since=2026-09-27`, returns **0 commits**, because a date without
  a time means that date *at the current time of day* `[run: git log
  --since=2026-09-27 --oneline | wc -l → 0; --since='2026-09-27 00:00' → 14]`.
  A slice that trusted it would audit nothing and report clean. Use
  `--since='2026-09-27 00:00'` or an explicit range.

## Checks run

| Command | Result |
|---|---|
| `python3 tools/check-staleness.py --detail` | **PASS** no live stale values; 172 files, 38 figures / 240 patterns; 6 unresolved (tracked); 217 restated-not-cited (advisory); 24 old values refuted in place. Advisory lists include `1.2 mm` in 8 files and `1.6 mm` in 10; drawn-no-row lists `FFC-CHAIN`/`F-CHAIN` from `notes.md` only |
| `python3 tools/merge-bom.py --check` | 156 rows from 26 fragments, 0 problems |
| `python3 tools/check-netlist.py --strict` | exit 0 |
| `python3 tools/verify-datasheets.py` | 88 verified, 24 blocked/not-fetched, 0 problems |

Everything I verified as correct (no finding): the 13 − n map in both
`board-netlist.yaml` (LH: SCK 11, SH/LD 9, SER 7, QH 5, 3V3 3, GND
4/6/8/10/12, 1–2 unconnected) and every page listed in K8-9; "without −RN2,
3V3 lands on pin 10, a ground" (true under the 13 − n sheets); the footprint
body 2.53–7.86 and courtyard 9.51 = 7.86 + 1.4 + 0.25; J-CHAIN pads
(1.05 − 0.65)/2 = 0.20; standoffs 4 + 4 = MECH-KB-STANDOFF/SCREW qty 8;
TP-CHAIN qty 10 = 5 × 2; `fab/` 15 files = 15 ledger rows; board thickness
1.2 and HASL in the `.kicad_pcb`, `.kicad_pro` and `.gbrjob`; standoff length
2.2 = 3.4 − 1.2.

## Greps run (corpus = `hardware docs/decisions docs/reference config firmware mechanical README.md ROADMAP.md`; `fab/`, `*.kicad_pcb`, `*.gbr`, `*.dxf` excluded unless noted)

| Pattern | Hits | Judgement |
|---|---|---|
| `5\.85` | 0 (5 incl. `.kicad_pcb`) | coordinates only |
| `2\.44` | 0 (26 incl. `.kicad_pcb`, `plate-top.dxf`) | coordinates only |
| `7\.1\b` | 2 | `17.1 ms`, `CH7.1` — unrelated |
| `12-n` `14-n` `12 − n` `14 − n` `12 - n` `14 - n` `12-k` `14-k` | 0 | — |
| `12 − k`, `14 − k` | 1 each | `notes.md` history |
| `key-board pin 8` / `pin 4` / `pins 8 and 6` / `12 SCK` | 1 / 0 / 0 / 0 | `notes.md` history |
| `ZIF` | 14 | all dated history or refuted in place (ADR 0001, 0009, 0017, 0018, notes.md) |
| `FFC` / `FFC-CHAIN` | 3 / 3 | ADR 0017 rename line; notes.md |
| `[Ff]lat flex` | 15 | refuted in place, except `woody_body.scad:757` (K8-13) |
| `ffc_` | 5 | ADR 0017/0020, tooling.md — all say "no longer exists" |
| `200528` / `Molex` | 4 / 4 | ADR 0020 context, tooling.md findings, notes.md — history |
| `between neighbouring switches` / `between each pair of` | 1 / 1 | ADR 0020 amendment (history) / **body.yaml:715 (K8-2)** |
| `one at each plug` | 1 | notes.md history |
| `C toward` | 2 | ADR 0017:41 (amended), notes.md |
| `tilt` | 11 | 3 chain ones refuted (ADR 0017:44/51/175, notes.md); rest IMU |
| `latch` (filtered) | ~45 | none about the chain except refuted ADR 0017/0009 lines |
| `SAMTEC-SHF-1.27MM` / `SAMTEC-FFSD-1.27MM` | 3 / 4 | lib README, body.yaml, params.scad (K8-6) |
| `catalogue` | 10 | lib README (K8-6), body.yaml sources, notes.md |
| `1\.6 ?mm` (key-board sense) | 5 | ADR 0020, tooling.md, DESIGN.md (history); body.yaml:260 (K8-4); ks33-geometry.md:136 (K8-13) |
| `via … 0.[3-7]` | 5 | layout.yaml, `.kicad_pro` (0.7, correct); tooling.md:312 history (K8-10) |
| `13\.1 ?mm|14\.6|17\.4|fold radius|chain_hdr_h` | 20 | ADR 0017:152-158 (K8-1) |
| `stayed the same size` / `at the board.s end` | 1 / 2 | ADR 0020:61,63 (K8-3); tooling.md history |
| `the four this board` | 1 | K8-5 |
| `20-way` | 6 | ADR 0018 ×2 history; ADR 0001:82, 0009:334/644, 0013:244 live (K8-8) |
| `all four positions|four connectors` | 5 | K8-12 |
| key-board pin statements `key[- ]board[^.]{0,40}pins? [0-9]…` | 30 | all 13 − n; none stale |
| sheets/layout/netlists for `12-n|ZIF|200528|FFC|catalogue|5.85|2.44|Molex` | 0 | clean |
