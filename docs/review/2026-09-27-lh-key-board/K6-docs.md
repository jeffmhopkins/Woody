# K6 — The documentation of the left-hand key board

**Slice:** K6, cold. Read: `CLAUDE.md`, this wave's `README.md`, nothing else under `docs/review/`.
**Revision measured:** `d46a3b0` (`git rev-parse --short HEAD`), working tree clean apart from this wave's directory. `tools/` not modified; nothing committed.
**Fact domain:** the board README, `layout.yaml`'s comments, `docs/reference/tooling.md` §3–§4 (and its header/§1 where §4 depends on them), `hardware/lib/README.md`, ADRs 0017 (amendment), 0019, 0020 (and amendment), `docs/decisions/README.md`, `hardware/cluster/cluster-boards.md`, the three key-board circuit pages, `key-chain-loom.md` and its `notes.md`, `mechanical/DESIGN.md`'s key-board and ribbon passages, and `CLAUDE.md`'s hardware conventions. Each was checked against the sheets, the `.kicad_pcb`, `config/body.yaml`, `mechanical/drc.echo`, `mechanical/export/pcb-geometry.echo`, the BOM, `fab/` and the banked JLCPCB pages.

Tools run: `python3 tools/check-staleness.py --detail` (PASS, 0 live stale values, 217 restated-not-cited advisories), `python3 tools/verify-datasheets.py` (88 verified, 0 problems), `python3 tools/audit-notes.py --regrown` (0 rows). I also ran a link and path resolver over every file in the domain: every Markdown link resolves. The only backticked path that does not resolve is `tools/board.py` in ADR 0019, which the ADR correctly calls retired.

## Summary

The board README is accurate about the things it covers. The fab outputs, the Economic-PCBA constraints (checked against the banked capability PDF), the test pads, the bit order, the `-RN2` meter check and the ribbon's service procedure all match the data. Its biggest gap is what it leaves out: **it presents the board as orderable but never says that the five switch positions it is built around are provisional until M2/M3** (K6-1). Around it, the older pages have not followed the board:

- `cluster-boards.md` still says the outline "cannot be drawn yet", and still carries a pre-24-pull-up passive count and open items that the register and ADR 0020 have closed.
- The marker page still counts three spare-switch positions.
- ADR 0020 and `tooling.md` both describe a ribbon no-parts **rule area on the PCB that does not exist**.
- The README names `layout.yaml` `fab:` as what DRC checks, but DRC reads a copy written into the `.kicad_pro`.
- Ownership of part numbers (sheet `MPN`/`LCSC`/`Assembly`) is written only in the README. ADR 0019, `CLAUDE.md` and `tooling.md` §3 do not have it.

As a template, the README has no revision history, no schematic or assembly PDF, no board dimensions, no expected bring-up word and no "next board" steps.

27 findings: 1 high, 7 medium, 13 low, 6 advisory.

---

## Findings

### K6-1 [high] The board README presents the board as ready to order, but the switch positions it is built around are provisional until M2/M3, and no page says so

- **Node:** `hardware/boards/key-board-lh/README.md` "Ordering it" and "Open, and what decides each". Figures `layout.lh_gaps` and `layout.lh_offsets`, and `config/key-layout.yaml` `keys[].x/y`.
- **What the data says:**
  - The body CAD places SW-LH1..5 at (50, 28.5), (70, 28.5), (90, 28.5), (108, 19.5) and (108, 37.5) `[mechanical/export/pcb-geometry.echo]`.
  - Those positions come from `config/body.yaml` `layout.lh_gaps` (status `nominal`, *decided_by "M2 - replaced key by key by x/y in config/key-layout.yaml"*) and `layout.lh_offsets` (status **`tbd`**, *decided_by "M2 - hands on the mule; the sign too"*) `[config/body.yaml lines 147-167]`.
  - `layout_lh_offsets` is in drc.echo's "tbd parameters in play" `[mechanical/drc.echo line 2]`.
  - `config/key-layout.yaml` says "Physical positions are NOT [decided] … Every x/y below is null on purpose", and all 19 keys have `x: null, y: null` `[config/key-layout.yaml lines 11-14, 80-111]`.
  - The roadmap says "M3 Layout locked … No aluminium cut before this" and "Nothing expensive gets cut before M3" `[ROADMAP.md lines 74, 87]`.
- **What the README says:** "This board is the project's worked example. Every other board is laid out, checked and ordered the way this one is", followed by a complete JLCPCB order procedure. The "Open" table lists the plug stand-out, the standoff, J-CHAIN's source, orientation, the 3D model and the main-board end. **It does not list the key positions.** A newcomer following it would order a board whose switch pitch is a research guess.
- **Fix:** add a first row to the Open table: "Switch positions (`layout.lh_gaps`, `layout.lh_offsets`, tbd) | M2 on the mule, locked at M3 (`config/key-layout.yaml` x/y replace them)". Also add one sentence under "Ordering it" saying that an order before M3 is a bring-up or mule board.

### K6-2 [medium] `cluster-boards.md` §5 says the key-board outline "cannot be drawn yet" and will be generated from `key-layout.yaml`. It is drawn, and it comes from `body.yaml`.

- **Node:** `hardware/cluster/cluster-boards.md` §5, the paragraph "The board outline cannot be drawn yet, and that is correct rather than incomplete".
- **Data:** the outline exists as `mechanical/export/key-board-lh.dxf` and as the `.kicad_pcb` Edge.Cuts `[repo]`. It is placed from `config/body.yaml` `layout.*`, `boards.kb_end_margin`, `boards.board_clear` and `hardware.kb_standoff_inset` (ADR 0020 point 3), not from `key-layout.yaml`, whose x/y are all null `[config/key-layout.yaml]`.
- **Related staleness on the same page:**
  - The status line still reads "First draft, 2026-09-21; board split reworked 2026-09-26". It does not mention ADRs 0019 and 0020 or the laid-out board.
  - "they should be laid out from one schematic with a variant table" is now done: hierarchical sheets plus `allocation.yaml` (ADR 0019).
- **Fix:**
  - Replace the paragraph with a citation: "the outline is the body CAD's (`mechanical/export/key-board-*.dxf`, ADR 0020 point 3), a rectangle whose switch positions are provisional until M3 (K6-1)".
  - Update the status line.
  - Change the variant-table sentence to past tense, pointing at ADR 0019 and `allocation.yaml`.

### K6-3 [medium] `cluster-boards.md` "Still open" contradicts its own §5, the register and ADR 0020

- **Node:** `cluster-boards.md` "Still open", item 1: "**Plate-to-PCB standoff, and plate thickness** (§5). Both come from Gateron's drawing; the second blocks M4/M5 already."
- **Data:**
  - `plate-thickness` is `settled`, 1.20 mm `[config/figures.yaml plate-thickness]`. §5 of the same page says "Plate thickness is settled".
  - The standoff is derived, not open: `mechanical/drc.echo` "key-board standoff length (derived)" = 2.2 mm `[mechanical/drc.echo line 54]` (ADR 0020 point 2).
  - What remains open is the stocked part and the plate alloy (ADR 0020 Consequences) and stiffening (ROADMAP line 334).
- **Also:** §5 restates "Plate-to-PCB standoff: 2.0–2.4 mm" rather than citing the drc line. [calc: 3.2–3.6 − 1.20 = 2.0–2.4; drc.echo gives 2.2 at `switch.pcb_below_seat` 3.4.] This is consistent today but uncited.
- **Fix:** rewrite item 1 as "The standoff part (stocked length of drc.echo "key-board standoff length (derived)") and the plate alloy: the plate vendor, M4 (ADR 0020). Plate stiffening: ADR 0002, M4/M5." In §5, cite the drc line instead of the 2.0–2.4 range.

### K6-4 [medium] `cluster-boards.md` totals: "63 network passives" is the pre-24-pull-up count. The table above it sums to 66.

- **Node:** `cluster-boards.md` Component table, the "Totals" line. Figure `key-pullup-qty`.
- **Data:** the same table gives R-KEY-PU 6+6+6+6 = 24, R-KEY-SER 5+4+6+6 = 21 and C-KEY 21 `[cluster-boards.md table; hardware/bom.csv R-KEY-PU qty 24, R-KEY-SER 21, C-KEY 21]`. [calc: 24 + 21 + 21 = 66; 63 = 21 × 3, the count before `key-pullup-qty` went to 24.]
- This is a stated count that moved under the sentence stating it: the "24, not 21" correction was made in the row but not in the total.
- **Fix:** "66 network passives (`key-pullup-qty` pull-ups plus 21 series resistors and 21 capacitors)". Better still, drop the total and cite the BOM rows.

### K6-5 [medium] `key-marker-and-bits.md` "Still open" counts three reserved spare-switch positions. There are two.

- **Node:** `hardware/cluster/key-marker-and-bits/key-marker-and-bits.md` "Still open", item 1: "Where the 3 reserved spare-switch positions go".
- **Data:**
  - `allocation.yaml` `right_thumb: [RT1, RT2, RT3, RT4, sw+, sw-, M1, M0]` gives two `[hardware/cluster/key-marker-and-bits/allocation.yaml]`.
  - The same page's §4 says "`sw+` `sw−` are the two reserved spare-switch positions … There was a third, hold/preset, until 2026-09-26".
- **Fix:** change "3" to "2", or better, "the reserved spare-switch positions (`config/key-layout.yaml` `spare_bits_switches`)" with no number (rule 1).

### K6-6 [medium] ADR 0020 and `tooling.md` §4 say the PCB carries the ribbon/header no-parts strip as a rule area. It does not, and the body CAD no longer exports one.

- **Node:** ADR 0020 point 3 ("the PCB carries it as a rule area") and its point-5 amendment ("the no-parts strip is under the header, its plug and the ribbon's hairpin"). `tooling.md` §4 "Where a layout comes from", row "…the ribbon's no-parts strip… | `mechanical/export/pcb-geometry.echo`".
- **Data:**
  - `pcb-geometry.echo` has no `ribbon` line for either board. Its 23 lines are switch, chain, standoff and board lines only `[run: grep -i ribbon mechanical/export/pcb-geometry.echo]`, apart from the word inside the "board" line's text.
  - `tools/pcb.py` still has the code path (`geo["ribbon"]`, a rule area named `"ribbon"`, lines 60, 71-72, 208-218, 432), but it never fires.
  - The `.kicad_pcb` has six zones: two GND pours and four circular keep-outs at the standoff holes (centres (102.7/179.7, 104/139) in PCB coordinates). None is named `ribbon` `[run: zone listing of key-board-lh.kicad_pcb]`.
- Whether any part actually sits in the hairpin's path is K3's and K5's question. The key board's leg "hangs just under its socket", and U-KEYS-LH, C-DECOUPLE-165-LH, R-KEY-PU-FREE3 and the LH5 network are all at body y 44–46.5, inside the header's span of about y 35–49 around 42.015 `[layout.yaml; pcb-geometry.echo chain line]`. The documentation claims a PCB-level guard that is not there.
- **Fix:** either restore the export and the rule area (a tools and CAD change, outside this wave's freeze), or change ADR 0020 and `tooling.md` to say what actually keeps parts out of the strip, which is the clash check if it models the key board's parts envelope. Remove the dead `ribbon` row from `tooling.md`'s table.

### K6-7 [medium] The README says DRC checks the board against `layout.yaml` `fab:`. DRC reads a copy written into the project at first layout, and nothing compares the two.

- **Node:** `hardware/boards/key-board-lh/README.md` "Ordering it": "Its limits are banked in `datasheets/fab/`, and they are in `layout.yaml` `fab:`, so KiCad's DRC checks this board against them". `tooling.md` §4, the "board house's own limits" row.
- **Data:**
  - `layout.yaml` `fab:` is applied only in `new_board()` (`tools/pcb.py` lines 138-146), which `cmd_layout` alone calls. `set_finish` also runs only in layout (line 481).
  - `cmd_check` reads only `layout.yaml` `cluster` (lines 506-507). DRC reads the values KiCad stored: `min_hole_clearance 0.28`, `min_hole_to_hole 0.45`, `min_via_annular_width 0.18`, `min_text_height 1.0`, `min_text_thickness 0.15`, `min_silk_clearance 0.15` `[hardware/boards/key-board-lh/key-board-lh.kicad_pro lines 124-134]`.
  - They match today. Edit `layout.yaml` `fab:` after layout and nothing changes or complains. Edit the rules in KiCad and `layout.yaml` becomes stale. That is two copies of one fact, and the README names the one that is not read.
  - The same applies to `silk:` (title, rev, date) and `parts:`.
- The README's own Files table ("How the first layout was made") is right. Its Ordering section contradicts it.
- **Fix:** in Ordering, write "they were written into the board's design rules (`key-board-lh.kicad_pro`) from `layout.yaml` `fab:` at first layout; after that, change them in KiCad's Board Setup". Longer term, have `pcb.py check` compare `fab:` against the project (a tools change, K7).

### K6-8 [medium] Who owns the part number (sheet `Manufacturer`/`MPN`/`LCSC`/`Assembly`/`Footprint`) is stated only in the board README. ADR 0019, `CLAUDE.md` and `tooling.md` §3 still list four fields.

- **Nodes:** ADR 0019 Decision "Scope: connections and parts … KiCad fields: `Row`, `Pins`, `Pins_source` and `Note`". `CLAUDE.md` Hardware conventions ("fields `Row`, `Pins`, `Pins_source`, `Note`"). `tooling.md` §3 field table (the same four).
- **Data:**
  - Every part on the key-board sheets carries `Manufacturer`, `MPN`, `LCSC`, `Assembly` and `Footprint`. For example, U-KEYS is `Nexperia` / `74HC165D,653` / `C5613` / `machine` `[run: property dump of hardware/cluster/key-register/key-register.kicad_sch]`.
  - `fab/*-bom-jlc.csv` is generated from them `[tools/pcb.py assembly_files]`.
  - The README says: "The sheets are the source of every part number … The BOM row says what the part must be; the sheet says which one is bought." That is a new ownership rule. ADR 0019 rejected "parts in the BOM fragments … part facts in two places", yet `hardware/bom.csv` still has a manufacturer column, for example `U-KEYS` "multiple" `[hardware/bom.csv line 33]`.
  - `tooling.md` §4 mentions the fields in passing, but §3, which defines what a sheet owns, does not.
- **Fix:**
  - Add the five fields and the README's ownership sentence to ADR 0019 (as an amendment), to the `tooling.md` §3 table, and to `CLAUDE.md`'s hardware conventions.
  - Say which BOM columns the sheet now overrides.
  - Note that `MPN` on `SW1-n` is prose ("KS-33 Red (linear) - bought, BOM row SW1-n"), not an MPN (K4).

### K6-9 [low] `layout.yaml` gives JLC's minimum track as "0.127 mm [from memory]". The banked page, cited ten lines lower, says 0.10 mm.

- **Node:** `hardware/boards/key-board-lh/layout.yaml`, the `rules:` comment.
- **Data:** "Min. track width and spacing (1 oz) … 1- and 2-layer: 0.10 / 0.10 mm (4 / 4 mil)" `[datasheets/fab/JLCPCB-PCB-CAPABILITIES.pdf, "Traces", run: pdftotext]`. CLAUDE.md §3: "A number read off a banked document beats one from a review."
- **Fix:** "JLCPCB's 2-layer 1 oz minimum is 0.10/0.10 mm (datasheets/fab/JLCPCB-PCB-CAPABILITIES.pdf); these are deliberately looser".

### K6-10 [low] `layout.yaml` comments: one garbled placement sentence, and a dated history line in a data file

- **Node:** `layout.yaml`, the placement comment.
  - "LH4 between LH4 and LH5" should be "LH4's between LH4 and LH5". [LH4 at (108, 19.5) and LH5 at (108, 37.5) per `pcb-geometry.echo`; the LH4 network at y 27.0 per `layout.yaml`.] The other sentences check out: LH1's network is at y 34.5 (far side of LH1 at 28.5), LH2/LH3 at 17.5 (near side), and LH5's beside the register (100.5–108.5, 44 against U at 90.5, 44.5).
  - "Placement (2026-09-27, the board grown to a rectangle with corner standoffs, ADR 0020)" is history in a `.yaml` (CLAUDE.md rule 2b: "Data files carry no history").
- **Fix:** correct the typo, and drop the parenthetical or reduce it to "(ADR 0020)".

### K6-11 [low] The README's rebuild sequence leaves out the sheet renders and the prerequisites

- **Node:** `README.md` "Rebuild and check".
- **Data:** `tools/pcb.py render` writes only the `*.pcb-*.png` files and `fab/` `[tools/pcb.py cmd_render lines 586-628]`. The `*.sch.png` renders come from `tools/kicad.py render` `[tools/kicad.py cmd_render line 388; tooling.md §3 Commands]`. After a sheet edit, the README's four commands leave the sheet PNGs stale, and the final `kicad.py check` fails on them.
- The README also never says the commands need KiCad 9 with `pcbnew` (`tools/setup-env.sh`, `tooling.md` §1), or that the PCB renders need the 3D models installed by hand (K6-15).
- **Fix:** add `python3 tools/kicad.py render hardware/boards/key-board-lh` after `export`, and a one-line prerequisite pointing to `tooling.md` §1.

### K6-12 [low] Stale comments in the corpus still describe retired designs (standoffs between switches, full prints unbanked, flat flex)

- **Nodes and data:**
  - `config/body.yaml` lines 713-717: "an M2 self-clinching standoff pressed into the plate **between each pair of neighbouring switches**". That is the placement the ADR 0020 amendment rejected. drc.echo reports "one in each corner" `[mechanical/drc.echo line 56]`.
  - `config/body.yaml` lines 336-341: "both catalogue pages are banked …, **their full prints are not (403)**". Both full prints are banked `[datasheets/.manifest-R12.csv rows 2-3, status OK]`, and the entries directly below cite them.
  - `mechanical/cad/woody_body.scad` line 757: "the key boards are on flat flex".
- These are data and source files, not prose (rule 2b), so there is no exemption for them.
- **Fix:** rewrite each comment to the current design: corners, full prints banked, IDC ribbon.

### K6-13 [low] `tooling.md` still reads as two pipelines, and one "finding" states a retired key in the present tense

- **Nodes:**
  - The title ("…the body CAD and the schematic pipeline") and the header table ("Two pipelines…") have no PCB row. `.kicad_pcb` is not listed as a source, and `*.pcb-*.png` and `fab/` are not listed as generated.
  - The §1 install table omits `librsvg2-bin`, which `pcb.py render` uses as `rsvg-convert` and `setup-env.sh` installs `[tools/setup-env.sh line 16]`.
  - §4 "Findings the first layout made" opens: "the CAD **now uses** the footprint's size (`boards.ffc_conn_*`, ADR 0020)". The parenthetical three lines later says `ffc_conn_*` no longer exists. This is a fix whose own explanation restates the wrong value (one of the four recorded shapes).
- **Fix:**
  - Add a PCB row to the header table and `librsvg2-bin` to §1.
  - Rewrite the finding in the past tense ("the CAD then used… since ADR 0017's amendment it is `boards.chain_hdr_*`"), or move the Würth/Molex narrative to git or a `notes.md`.

### K6-14 [low] The "Where the sheets are" table in `tooling.md` §4 labels the PNG renders as "source"

- **Node:** `tooling.md` §4 "Where the sheets are". The first three rows link `*.sch.png` and mark them **source**.
- **Data:** the PNGs are generated and ledgered (`tooling.md` header table and §3; `hardware/SHEETS.csv`). The source is the `.kicad_sch`.
- **Fix:** relabel the column "Sheet (source) → render", link the `.kicad_sch`, or change the status text to "from the KiCad sheet (source)".

### K6-15 [low] The `tooling.md` note on 3D models miscounts them, and the manual install it describes is not in `setup-env.sh`

- **Node:** `tooling.md` §4 "Learned the hard way": "the four this board needs came from `gitlab.com/kicad/libraries/kicad-packages3D` tag `9.0.0`".
- **Data:** the `.kicad_pcb` references three KiCad library models (`C_0805_2012Metric.step`, `R_0805_2012Metric.step`, `SOIC-16_3.9x9.9mm_P1.27mm.step`). The fourth is the banked `datasheets/mechanical/GATERON-KS-33-3D.step` via `${KIPRJMOD}` `[run: grep model key-board-lh.kicad_pcb]`. `tools/setup-env.sh` does not fetch any of them `[run: grep 3dmodels tools/setup-env.sh → nothing]`, so a fresh environment renders the board without them (K7 to confirm the fingerprint effect).
- **Fix:** "the three KiCad models (C/R 0805, SOIC-16)…", and add the fetch to `setup-env.sh`, or state it as a manual step in §1.

### K6-16 [low] `cluster-boards.md` §5 restates KS-33 geometry, including a centre-pole tip that `body.yaml` has superseded

- **Node:** `cluster-boards.md` §5: "the centre pole, which protrudes 0.9–1.3 mm below the key board (`boards.key_board_t`; tip 5.70 below the seat `[calc]`)". The same section also carries "5.10 mm", "1.9 mm" and "~3.2–3.6 mm".
- **Data:** `config/body.yaml` `switch.pole_tip_below_seat` = 5.75, "the STEP says 5.70; the vendor wins" `[config/body.yaml line 231-234]`. [calc: 5.75 − `pcb_below_seat` 3.4 − `key_board_t` 1.2 = 1.15 mm at the chosen depth; across the 3.2–3.6 window it is 0.95–1.35, not 0.9–1.3.]
- **Fix:** cite `switch.pole_tip_below_seat`, `switch.pcb_below_seat` and `boards.key_board_t` by name and drop the numbers (rule 1). The page already says "Footprint: see `ks33-geometry.md`, and do not copy it here".

### K6-17 [low] The README and the loom page restate `key-scan-current` instead of citing it

- **Node:** figure `key-scan-current` (owner `key-switch-network.md`).
  - README Bring-up step 3: "about 1.4 mA [calc: …]".
  - `key-chain-loom.md` "What the main board still owes the chain": the full "1.43 mA per CLOSED key / 19 closed = 27.3 mA" block, and "27.3 mA" again in the FB-CHAIN paragraph.
- **Data:** the register's `companion` sanctions the *rail step* consequence on the loom page. Its own escape note says "DEDUPLICATING it is still owed … today all three restate it" `[config/figures.yaml key-scan-current]`. The README adds a fourth restatement.
- **Fix:** in the README, write "each pressed key adds its pull-up's current (`key-scan-current`)". In the loom page, keep the consequence and cite the figure for the per-key and total values.

### K6-18 [low] `key-switch-network.md` cites a Toshiba datasheet filename that is not banked, and names the wrong peer for the switch

- **Nodes:**
  - The threshold table row "Toshiba TC74HC165 `74HC165-toshiba.pdf`". The banked file is `datasheets/logic/74HC165-toshiba-1986-excerpt.pdf` `[run: find datasheets -iname '*165*']`.
  - The Interfaces table, row `SW`: Peer `SW-THUMB`. That is the lighter-spring option for LT (cluster-boards.md table). The switch on every position, including the key boards', is BOM row `SW1-n` (sheet field `Row` = `SW1-n`).
- **Fix:** correct the filename, and change the peer to `SW1-n` (`SW-THUMB` option on LT).

### K6-19 [low] Two of the three migrated circuit pages still send the reader to `netlist.yaml` as if it were the thing to edit, and neither links its sheet

- **Node:** `key-register.md` §1 and `key-switch-network.md` §2 both open with "Connectivity is **[`netlist.yaml`](netlist.yaml)**, not this drawing".
- **Data:** both `netlist.yaml` files begin "GENERATED from …kicad_sch by tools/kicad.py - DO NOT EDIT" `[hardware/cluster/key-register/netlist.yaml line 1]`. `key-marker-and-bits.md` does name and link its `.kicad_sch`. The other two pages never mention theirs or their `.sch.png`. A newcomer following those pages edits the exported file, which is the trap CLAUDE.md describes.
- **Fix:** "Connectivity is the KiCad sheet [`key-register.kicad_sch`](key-register.kicad_sch) (render: `key-register.sch.png`); `netlist.yaml` is exported from it and is what the checks read."

### K6-20 [low] ADR 0019 counts the key network as "six times on one board and nineteen in all". The network is built 21 times.

- **Node:** ADR 0019 Options, "A flat sheet per board".
- **Data:** `hardware/cluster/key-switch-network/netlist.yaml` has `replicated: 21`. The two unfitted spares carry full networks (`key-marker-and-bits.md` §4: "21 sets"). 19 is the switch count, not the network count. "Six on one board" is true only of RH; LH has five `[config/key-layout.yaml counts]`.
- **Fix:** "up to six times on one board and 21 in all", or cite the netlist's `replicated:` rather than a number.

### K6-21 [low] `mechanical/DESIGN.md`: "outlines are M3/M4 outputs" contradicts ADR 0020, and the plate window is attributed to a rule that does not check it

- **Nodes:**
  - "Not modelled yet: … The main board and the key boards are rectangles, because their outlines are M3/M4 outputs." ADR 0020 point 3 *decides* that the key board is a rectangle across the cavity with corner standoffs, and the outline is exported (`export/key-board-*.dxf`, DESIGN.md itself lines 340-342).
  - The plate window "…across the standoffs' gap (*"key-board standoff length (derived)"*)". That drc line reports the gap. No drc line checks that the window exists over the header's tails, or that the tails clear the oak top `[run: grep -i window mechanical/drc.echo → only matrix-window lines]`.
  - The README's "so they need no trimming" rests on nothing checkable either.
- **Fix:** say that the key-board rectangle is decided and only its size is provisional (K6-1). For the window, either add a drc rule (window over J-CHAIN's tails; tail tip below the oak), which is a CAD change, or state it as an unchecked design intent and add "J-CHAIN tail length against the plate window and oak" to the README's Open table, decided by the first mated pair (K5).

### K6-22 [low] The README's Open table leaves out an open item that bears on ordering and assembly

- **Node:** `cluster-boards.md` "Still open": "**Conformal coating.** … nothing says whether the key boards are coated". This board's README (Open table, Assembling) does not mention it.
- **Fix:** add a row: "Conformal coating of the key boards | ADR 0009 / M4 (see `cluster-boards.md`)", or record a decision.

### K6-23 [advisory] The README lacks several things the next board will need as a template

The README does not have:

1. **A revision history.** The only revision marker is `layout.yaml` `silk: rev "A"`, date 2026-09-27, which reached the copper at first layout (`gr_text "rev A  2026-09-27"` in the `.kicad_pcb`). After that `layout.yaml` is no longer read (K6-7), and no page says how to bump a revision or where a changelog goes. Add a "Revisions" table (rev, date, what changed, git tag or commit) and say that the silk text is edited in KiCad.
2. **A schematic PDF or assembly drawing.** `tooling.md` says references go on the fabrication layer, "which the assembly drawing reads", but `fab/` holds no assembly drawing. The nearest thing is `*.pcb-copper-bottom.png`, which includes `B.Fab`. Add `kicad-cli sch export pdf` and a `B.Fab`+`B.Silkscreen` PDF to `pcb.py render` (tools change), or say the PNG is the assembly drawing.
3. **Board size.** Neither the order settings nor the Files table gives it. [calc from `pcb-geometry.echo` standoffs at x 40.5/117.5, y 11/46 and `kb_standoff_inset` 3.5: about 84 × 42 mm.] Cite the DXF or print it from the PCB rather than restating it.
4. **The expected bring-up word.** The allocation fixes it. [calc from `allocation.yaml` `left_hand: [LH1..LH5, M0, M1, FREE3]`: idle H..A = 1 1 1 1 1 0 1 1 = 0xFB; each press clears one of the top five bits.] State it as derived from `allocation.yaml`, or cite `marker-bits`. Also give a pass/fail figure for idle supply current.
5. **A silkscreen legend.** The board carries `C`, `S`, `P`, `PF`, `CD` `[run: gr_text dump]`. `tooling.md` explains C/S/P, but a builder holding the board needs `PF` (the free-bit pull-up) and `CD` (decoupling) explained in the README.
6. **A "making the next board from this one" section:** copy `layout.yaml` and change `cluster`/`suffix`, run `pcb.py layout`, and what to check.
7. **A decision on `key-board-lh.kicad_prl`.** It is per-user KiCad view state and is committed. Either add it to `.gitignore` or list it in the Files table.

### K6-24 [advisory] The ADR index and its format rule do not match how 0017 and 0020 were changed

- **Node:** `docs/decisions/README.md` Format: "When a decision is reversed, do not edit the old ADR. Mark it `Superseded` and write a new one."
- **Data:** ADRs 0017 and 0020 had parts reversed on 2026-09-27 (flat flex → IDC; standoffs between switches → corners). Both were amended in place: a dated amendment section plus italic notes inside the original points.
  - 0020's Status line says so. 0017's Status line reads plain "Accepted" `[run: status-line listing]`. The index row does mention the amendment.
  - The index also lists 0014 after 0020.
- **Fix:** add "a partial reversal may be recorded as a dated *Amendment* section, named in the Status line" to the Format section. Put "amended 2026-09-27" on 0017's Status line and re-sort the index. The index's own note already says it should be generated.

### K6-25 [advisory] `key-marker-and-bits.md` still says the pattern is "proposed" and that errors show on "the display"

- **Node:** the "Proposed levels" heading sits under "DECIDED 2026-09-21". "Converting an invisible intermittent fault into a number on the display": there is no display since ADR 0015 (0008 Superseded).
- **Fix:** rename it "Levels". Change "on the display" to "a visible error counter (surfaced as ADR 0015 says)".

### K6-26 [advisory] ADR 0020 point 4 says "reaches the steel". The plate is aluminium.

- **Node:** ADR 0020 point 4: "No track, via or pour reaches the steel, so the screw cannot bond the plate to `GND_CHAIN`". `PLATE-TOP` is "1.20mm aluminium" `[hardware/bom.csv line 41]`, as `mechanical/DESIGN.md` line 30 also says.
- The sentence probably means the steel standoff and screw, but a reader takes "the steel" to be the plate.
- **Fix:** "reaches the standoff or the screw head".

### K6-27 [low] The README's "JLC Basic" claim has no provenance

- **Node:** README "Which parts are in the order": "The parts carry JLC Basic numbers" (C17408, C49678, C17520, C53134). No banked page or dated `[web]` source backs this; only the C5613 "Preferred Extended" rule is sourced (`datasheets/fab/JLCPCB-PCBA-FAQ.pdf` p.301 line, "exempt from the Feeders Loading fee for Economic").
- **Fix:** add `[web URL, date]` or bank the LCSC part pages. K4 owns the check itself.

---

## Checked and found correct

- **README Files table:** the sheet fields `Row`/`Pins`/`Manufacturer`/`MPN`/`LCSC`/`Assembly` are present on every part `[property dump]`. `board-netlist.yaml` is exported. The renders and all 15 `fab/` files are in `hardware/SHEETS.csv` (27 LH rows), with the `.kicad_pcb` and sheets as inputs `[run: grep SHEETS.csv]`. `pcb.py render` writes the Gerbers, drill, pos and the three JLC CSVs `[tools/pcb.py]`.
- **README fab list:** 9 Gerbers (both coppers, pastes, silks, masks, Edge.Cuts), the `.gbrjob` (`BoardThickness 1.2`, `Finish "HAL lead-free"`) and one `.drl`, all present.
- **README order table:**
  - 1.2 mm is a JLC FR-4 thickness `[JLCPCB-PCB-CAPABILITIES.pdf "Thickness"]`.
  - Economic PCBA at 1.2 mm offers Green/Black mask with HASL only `[JLCPCB-PCBA-CAPABILITIES.pdf, "PCB Specs for Economic PCB Assembly"]`.
  - The stackup finish in the `.kicad_pcb` is `copper_finish "HAL lead-free"`.
  - All machine-placed parts are on B.Cu; the switches are on F.Cu `[footprint/layer dump]`.
  - The BOM/CPL/hand lists match the "not in the order" list: switches and J-CHAIN are in the hand list; the TPs and H1–H4 are in neither.
  - C5613 "Preferred Extended" has no loading fee `[JLCPCB-PCBA-FAQ.pdf]`.
  - J-CHAIN is at stock 0 at JLC, matching its BOM row.
  - `datasheets/.manifest-R12.csv` records the blocked STEP.
- **`layout.yaml` `fab:` values** all match the banked PDF: PTH-to-track 0.28, pad hole-to-hole 0.45, via hole-to-hole 0.2, 2-layer 1 oz annular minimum 0.18, silk line 0.15, text 1.0, pad-to-silk 0.15. The via comment holds [calc: (0.7 − 0.3)/2 = 0.2 ≥ 0.18]. The header pads are Ø1.05 on a 0.65 drill [calc: 0.2 ring], as `hardware/lib/README.md` says.
- **README assembly and bring-up:**
  - J-CHAIN is on the bottom, mouth toward the tail (`pcb-geometry.echo` direction +1; `routing.chain_fold` left_hand = +1).
  - The five TPs are on B.Cu with silk labels 3V3/GND/SCK/SH/LD/QH.
  - The `-RN2` meter check holds [calc: 13 − 10 = 3, 13 − 2 = 11].
  - H..D = LH1..LH5 matches `allocation.yaml`.
  - 1.4 mA ≈ 3.3/2300 [calc: 1.43 mA].
  - Four standoffs per board (`drc.echo` "key-board standoffs" [4, 4]).
  - The service position matches `routing.chain_service`.
- **ADR 0020 arithmetic:** standoff = 3.4 − 1.20 = 2.2, matching drc.echo line 54. Pins shown [calc: 5.10 − 3.4 − 1.6 = 0.1; 5.10 − 3.4 − 1.2 = 0.5]. The NPTH holes are `MountingHole_2.2mm_M2` on the bottom, with four both-layer keep-outs at the echo's standoff positions.
- **The pin map is consistent** across ADR 0017's amendment, `key-chain-loom.md` (table and drawings), `cluster-boards.md`, `key-register.md`, `key-switch-network.md`, and the J-CHAIN and CBL-CHAIN BOM rows (key pin = 13 − k; SER 7, QH 5, 3V3 3, SCK 11, SH/LD 9).
- **No live text** outside `notes.md` or an ADR's own history uses 12−n/14−n, ZIF, `ffc_conn_*`, Molex, flat flex or "C toward the wall", except the items in K6-12 and K6-13 `[run: corpus grep]`. The history sits correctly in `key-chain-loom/notes.md`, in past tense.
- **ADR 0019 Consequences** (migrated circuits; `replicated: 3` for the free-bit pull-up, `replicated: 4` for the register; `kicad.py check` needs KiCad 9 and is not in the hook) match the netlists and `tools/kicad.py`.
- **`CLAUDE.md` hardware conventions** on boards, `.kicad_pcb` as source, `pcb.py check` (DRC, parity, zero unrouted, switch positions; it also checks the standoffs and J-CHAIN) and SHEETS ledgering are all true of `tools/pcb.py` and `tools/kicad.py`. Only the field list is incomplete (K6-8).
- **`hardware/lib/README.md`:** the pad size, the SW footprint's `exclude_from_pos_files` and `fp-lib-table`'s `woody` library all match. Body 13.97/5.33 and pin_back 2.53 [calc: 7.86 − 5.33] match `boards.chain_hdr_*`, though they are restated rather than cited (advisory, same shape as K6-16).
- **Links:** every Markdown link in the 16 files resolves, and every backticked repo path exists except `tools/board.py` (correctly called retired).
- **Tools:** `verify-datasheets.py` passes. The JLC PDFs are in `MANIFEST.csv` via `.manifest-R11.csv`. `check-staleness.py` passes with 0 live stale values.
