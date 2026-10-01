# A7 - The module physically: panel layout and art, jacks/pots/toggle/LED/etherCON, the stack and standoffs, module-main / module-jack and J-B2B-MOD, the 16-pin header, manufacturability

**Slice:** A7 - ADRs 0023, 0024, 0026; `config/module.yaml`; `mechanical/cad/module.scad` and its outputs (`drc.echo`, `export/pcb-geometry.echo`, `export/panel-art.echo`, `art/panel-art-check.txt`, renders); `tools/panel-art.py`; `hardware/boards/module-main`, `module-jack` (sheets' exported netlists, READMEs); BOM rows PANEL, J-CV, POT-*, KNOB-BREATH, SW-POWER, LED-PANEL, MECH-*-MOD, J-B2B-MOD, J-PWR-EURO, CBL-PWR-EURO, PCB-MODULE(-JACK); banked NKK Series M, PJ398SM drawing, R0904N / RV09AF-40, Samtec TSW, Thonk 1900h page.
**Revision measured:** 13197f8 (pinned copy from `git archive`, tools/ pinned with it)
**Tools:** `python3 tools/cad.py check` / `explain`; `python3 tools/check-staleness.py`; `python3 tools/check-netlist.py --strict`; `python3 tools/kicad.py check` (KiCad present); a Python read of both `board-netlist.yaml` files for J-B2B-MOD and the panel parts; `pdftotext -layout` / `pdftoppm` on the banked datasheets.

## Summary

- **Holds:** the panel geometry and every face clearance re-derive from `config/module.yaml` (knobs, plug grips, webs, mounting slots, the drop zone). The stack depths (9 / 10.6 / 18.3 / 19.9) and the derived lengths (standoff 7.7, LED spacer 6.45) re-derive. J-B2B-MOD is netted **identically on both boards** and matches the README table after the jack swap. Each jack's tip lands on its own column's side of the header. The panel-art report places every pill with the post-swap word. `kicad.py check` PASSes and `check-netlist --strict` reports 0 problems.
- **Does not hold:** the corpus **fails its own staleness gate at REV**. `module-photo-detail` is STALE and still shows the **pre-swap** panel (pitch top-left, breath top-right, mod 1 under pitch), and the module README embeds it (A7-1).
- **The PANEL BOM row did not follow ADR 0026.** It orders "laser or waterjet, same vendor and order as the key plate", which is a bare 1.2 mm plate route. It says nothing of the black anodise or the UV print, and nothing of the print vendor (A7-2).
- **Layout trap: J-B2B-MOD on the jack board.** The header enters that board from its rear, but the board needs the *unmirrored* pin map. Nothing records this, and no check can catch it (A7-3).
- **Assorted fixes that did not reach their citing pages:** CBL-PWR-EURO "needs +5V", KNOB-BREATH citing a non-existent `POT-BREATH`, two READMEs saying the layout is "being revised", ADR 0004 / 0024 still carrying the write-on strip, `led.hole_d`'s source contradicting LED-PANEL, and R-ON-HI's row against the sheet (A7-4 … A7-10).

## Findings

### A7-1 - `module-photo-detail` is stale and shows the pre-swap jack layout; `check-staleness.py` FAILs at REV
**Severity:** medium
**Node:** `mechanical/module/renders/photo-detail.png` (J-CV-BREATH, J-CV-PITCH, J-CV-MOD1…4 pills)
- [test] `python3 tools/cad.py check` reports `FAIL 1 CAD output problem(s) of 73 outputs - module-photo-detail: STALE - changed config/module.yaml, art/tex-*.png, export/panel-art.echo, tools/render-module.py`. `python3 tools/check-staleness.py` gives `FAIL ... 2 cad`. All other module outputs are current.
- [test] `cad.py explain module-photo-detail`: built against `config/module.yaml@b2928354b675`, now `@4b122af21e8c`.
- [repo] the image itself, read: the `pitch` pill is on the left of the top row, `breath` is on the right, and `mod 1` is under pitch. This is the layout ADR 0024 point 13 reversed ("Point 1 first had PITCH on the left and the MOD jacks across the rows", `docs/decisions/0024-module-panel-layout-and-stack.md:190`).
- [repo] `mechanical/module/README.md:132` embeds it, captioned "the pitch and breath pills". A reader of the README sees the wrong jack positions.
- This is the shape "a fix that did not reach the pages citing it": the swap moved the config, the echo, the textures and the other photos, but not this one. The PreToolUse hook reports the FAIL without blocking (CLAUDE.md), so it was committed.
**What would settle it:** `python3 tools/cad.py build module-photo-detail`, then `cad.py check` PASSes.

### A7-2 - PANEL row specifies a bare laser/waterjet plate from the key-plate vendor; ADR 0026 specifies black anodise + UV print, CNC-cut by the print vendor
**Severity:** medium
**Node:** BOM row `PANEL` (`hardware/module/panel/bom.csv:2`)
- [repo] The PANEL notes read: "Laser or waterjet from mechanical/module/export/panel.dxf ... - SAME vendor and order as the key plate."
- [repo] The key plate is `PLATE-TOP`, "1.20mm aluminium ... laser or waterjet cut" (`hardware/bom.csv:52`), a bare plate.
- [repo] ADR 0026 point 8 says: "UV print on the black-anodised 2 mm aluminium ... CNC-cut from `export/panel.dxf` by the same vendor, with 'use white ink' and 'underprint white' set (Front Panel Express, Schaeffer)". It adds that one proof panel comes first, after a 1:1 paper print. The PANEL row's part field is "2mm aluminium", with no finish and no print, and the row does not cite `art/panel-art.pdf`.
- [repo] ADR 0026 point 8 also says the anodise is something "ADR 0024 already specifies". `grep -i anodi` over ADR 0024, ADR 0004, `panel/` and `figures.yaml` finds nothing. The only trace is Doepfer's quote in `config/module.yaml` `panel.t`.
- Effect: someone ordering from the BOM gets an unfinished, unprinted panel from a plate vendor. That vendor may not offer anodise or UV white underprint at all.
**What would settle it:** the PANEL row names the finish, the print file and the vendor class from ADR 0026 point 8. It cites ADR 0026, not the key plate.

### A7-3 - J-B2B-MOD on the jack board enters from the rear but needs the front-side (unmirrored) pin map; nothing says so, and no check catches it
**Severity:** medium
**Node:** `J-B2B-MOD` (module-jack `J7`, module-main `J2`)
- [repo] `pcb-geometry.echo` gives both boards the same placement: "J-B2B-MOD", 25.25, 77, 0, "long axis along y, pin 1 at the top left". The boards' KiCad top view is the panel view with y negated (`config/module.yaml:28-29`). Jack-board parts face the panel. The insulator is on the **main** board's front face (BOM J-B2B-MOD; `pcb-geometry.echo` line 6), so the header body is on the jack board's **rear**.
- [calc] Pin *k* is one straight conductor, so it sits at the same panel-frame (x, y) on both boards. Both KiCad top views are panel views, so the jack board needs the **same unmirrored pin map** as the main board: pin 1 at x 23.98, pin 2 at 26.52 (25.25 ∓ 1.27).
  - A layouter who puts the footprint on B.Cu, the natural choice for a part whose body is on the rear, gets a mirrored map. Odd and even columns swap: every jack-board net lands one column over, and the "each jack on its own column's side" argument inverts.
- [repo] No module page mentions mirroring or the side (grep `mirror|B.Cu|back side` over `hardware/boards/module-*`, `mechanical/module/README.md`, ADR 0024: no hits). `tools/kicad.py check` compares the two **sheets**, not pad positions. `tools/pcb.py` has no module-board checks.
- The instrument's J-UMB has the same geometry, so the trap is not new, but neither module README says it.
**What would settle it:** a line in both READMEs and the echo naming the side and the pin map. Better, a pcb-level parity check (pad *k*'s panel-frame position equal on both boards) before the module layout starts.

### A7-4 - CBL-PWR-EURO still says it is 16-way "because ... it needs +5V"
**Severity:** low
**Node:** BOM row `CBL-PWR-EURO`
- [repo] `hardware/bom.csv:211`: "16-WAY, because J-PWR-EURO is 16-pin (it needs +5V)".
- [repo] ADR 0023 point 3 (amended 2026-09-30) and J-PWR-EURO's row: "the bus +5 V is not used ... This keeps commonality". The header is 16-pin for cable commonality. The +5 V pins 11-12 are on no net ([repo] module-main `board-netlist.yaml`: `POS5_11`, `POS5_12` are single-pin nets).
- The conclusion (16-way) still holds; the reason given for it is the retired one. Shape: a fix whose own explanation restates the old reason.

### A7-5 - KNOB-BREATH cites a part that does not exist and does not name the knob the CAD and art are built on
**Severity:** low
**Node:** BOM row `KNOB-BREATH`
- [repo] The row says "Match the shaft of the POT-BREATH variant ordered - D-shaft and knurled are not interchangeable". `grep '^POT-BREATH,'` over `hardware/bom.csv` finds 0 rows: the pots are `POT-GAIN`, `POT-OFFSET` and `POT-RESP`.
- [repo] `config/module.yaml` `knob.d`/`knob.h` are `settled` on the Thonk Davies 1900h clone, T18 (banked product page). `panel.md` says "the chosen Thonk 1900h". `drc.echo` says "KNOB-BREATH, proposed". The pots are ordered as T18 / 18-tooth (POT-OFFSET "KC", POT-RESP "B type ... 18-TOOTH").
- The row that gets ordered is still "Knob to match the pot shaft", with no MPN. A D-shaft knob would not fit.

### A7-6 - Both board READMEs still say the panel layout is "being revised"
**Severity:** low
**Node:** `J-B2B-MOD` allocation reasoning
- [repo] `hardware/boards/module-main/README.md`, "What decides whether this changes": "the panel layout (being revised now; the etherCON and the toggle move)". `hardware/boards/module-jack/README.md` Open table: "The panel layout, now being revised".
- [repo] ADR 0024 points 11-13 landed (2026-09-30 and 2026-10-01). `layout.*` is in `config/module.yaml`, and the allocation's own "Why this order" already reflects point 13. A stated state has moved under the sentence stating it.
- [repo] In the same vein, ADR 0024's Open table still lists "The panel's legends | The artwork". ADR 0026 has decided them.

### A7-7 - ADR 0004's panel paragraph, and ADR 0024 point 2, still promise the MOD write-on strip that ADR 0026 dropped
**Severity:** low
**Node:** J-CV-MOD1…4 legend zones
- [repo] ADR 0004 (`0004-cv-interface-module.md:711-713`): "**PITCH** and **BREATH** silkscreened, **MOD 1–4** numbered with a write-on strip". Its amendment note covers only point 11.
- [repo] ADR 0024 point 2: "a zone beside each jack on the panel's outer side (the MOD write-on strip of ADR 0004 is these four)".
- [repo] ADR 0026 point 4: "ADR 0004's write-on strip for the MOD jacks is dropped with the pads". Point 7 says "the write-on pads ... go". Neither earlier ADR carries an amendment pointer.

### A7-8 - `led.hole_d`'s source says the LED flange "stops behind the panel"; LED-PANEL's row and ADR 0024 point 9 say it cannot
**Severity:** low
**Node:** `LED-PANEL`, `MECH-LED-BEZEL-MOD`, `config/module.yaml` `led.hole_d`
- [repo] `config/module.yaml:451-454`: "a D3.2 hole for the LED; the lens passes, the flange stops behind the panel".
- [repo] `led.flange_d` = 3.2 = `led.hole_d` [ds LTL-4231N via the leaf]. LED-PANEL row: "ITS FLANGE IS D3.2, THE SAME AS THE PANEL HOLE ... so it does not stop against the panel: it needs MECH-LED-BEZEL-MOD". ADR 0024 point 9 says the same.
- [calc] The model is right: the spacer sets the flange 9 − 6.45 = 2.55 behind the rear face, and the lens tip comes out at 2.55 − 5.55 = −3.0, i.e. 1.0 proud of the 2 mm panel (`led.proud`). Only the leaf's source text is wrong, but it is the text a builder reads.

### A7-9 - Metal standoff pads on `AGND_MOD` are decided but are on neither sheet
**Severity:** low
**Node:** `MECH-STANDOFF-MOD` pads, `AGND_MOD` (module-jack)
- [repo] `module-jack/README.md`, `PCB-MODULE-JACK`, `MECH-STANDOFF-MOD` and `power-entry.md` *Grounding* say: the four standoff pads are `AGND_MOD` on the jack board and on no net on the main board.
- [repo] `grep -il "mountinghole\|MECH-STANDOFF"` over every module `.kicad_sch` finds nothing. Neither `board-netlist.yaml` has a mounting-hole part.
- Under ADR 0019 the sheet owns every connection. A connection decided only in prose is not in the netlist the layout imports. The main board's "no net" happens to need nothing; the jack board's AGND tie does.
- [repo] Also, `pcb-geometry.echo`'s "standoff head" keep-out reads "no parts or copper" on both boards. That contradicts a plated AGND pad under the head on the jack board.

### A7-10 - R-ON-HI's row says the toggle's leg hangs off the raw bus +12 V; the sheet puts it on `ISO_POS12`
**Severity:** low (cross-slice: A3)
**Node:** `R-ON-HI` (module-main `R57`), `SW-POWER`
- [repo] `hardware/bom.csv:105` says "Top of the LT1641 ON (UVLO) divider, raw +12 V to the toggle" and "the toggle's wires never carry the bus unlimited".
- [repo] module-main `board-netlist.yaml`: `R57.1` is on `ISO_POS12`. `umbilical-load-switch.md:419` draws `ISO_POS12 ──[R-ON-HI 68k]──ON_SW──o SW-POWER`.
- The row's description predates ADR 0027. The physical consequence for this slice: the toggle's wires and lugs (panel-mounted, in a metal bushing) carry the **isolated** domain, not bus +12 V.
**What would settle it:** A3 confirms which rail is intended; the row follows the sheet.

### A7-11 - No assembly sequence for the module stack, and the stack is over-constrained in depth
**Severity:** advisory
**Node:** `J-B2B-MOD`, `MECH-STANDOFF-MOD`, `SW-POWER` wiring, `PCB-MODULE-JACK`
- [calc] Order matters, and nothing records it:
  - The jack board's own THT joints are on its rear face, which ends up inside the 7.7 mm board gap. So the jacks, pots and LED must be soldered before stacking.
  - J-B2B-MOD's jack-board joints are on that board's front face. They sit in a trench between the jack bodies: tip-side faces at 15.75 + 6 = 21.75 and 34.75 − 6 = 28.75, a 7.0 mm wide, 9 mm deep slot [ds PJ398SM-drawing.jpg front view 6 / 4.5]. They must be soldered before the panel goes on.
  - SW-POWER's wires (footprint `SolderWire-0.25sqmm_1x02`, THT [repo umbilical-load-switch sheet]) can only be soldered from the main board's rear after stacking. So the toggle is wired first, and its wires are fed through the jack board's step as the panel is offered up.
  - [repo] grep for "assembly order|sequence" over module pages: no hits.
- [calc] Three things set the board gap: the standoffs (faced to 7.7), the jack bodies against the panel (9.0, drawing tolerance ±0.15), and the NE8FAV setback (18.3). Add PCB thickness tolerance (typically ±10 % of 1.6 [from memory]) on two boards. Facing the standoff to nominal does not remove this stack. The header, soldered after stacking, freezes whatever gap results.
**What would settle it:** a short build-order note on the module README. The standoff is faced to the gap measured with both boards seated on the panel, not to the nominal.

### A7-12 - Several face clearances pass at a hair over zero against `tbd` envelopes
**Severity:** advisory
**Node:** `jack.nut_d`, `rail.band`, SW-POWER legend zones
- [repo] `drc.echo`:
  - "art: gutter A|B ..." passes at [−0.15, 0.15] against `jack.nut_d` = 8.0, which is `tbd` and "[from memory]".
  - "parts behind the panel clear of the rail band" passes at 0.7 mm (standoff screw head) against `rail.band` = 10, also `tbd`.
  - "everything on the face clear of the panel screws' washers" passes at 0.
- [repo] `art/panel-art-check.txt`: `off` has 0.03 mm air in its zone and `on` 0.10.
- ADR 0026 already names `jack.nut_d` as moving two gutters. This entry records how little room there is: a Thonkiconn nut 0.3 mm larger in diameter than assumed fails the A|B gutter.

### A7-13 - SW-POWER is modelled with its body flat on the panel (front nut only); NKK's D4 hardware includes a second hex nut
**Severity:** advisory
**Node:** `SW-POWER`, keep-out "front: SW-POWER wiring"
- [repo] `module.scad:394-402` draws the body from `zd(0)` (the panel's rear face) and puts one nut on the front. The lugs end at 9.4 + 4.5 = 13.9 behind the rear face, which is 4.4 in front of the main board ([calc] 18.3 − 13.9).
- [ds] `NKK-SERIES-M-TOGGLE.pdf` p.7: D4 standard hardware is 2 hex nuts and 1 lockwasher, with a maximum panel of 2.6 mm "with standard hardware".
- If the builder fits the second nut behind the panel (the usual way to set lever projection), the body moves back by `toggle.nut_h` (2.0, tbd). The lugs then end about 2.4 mm from the main board, not 4.4. The keep-out height and the "room for the wires' bends" both shrink.
**What would settle it:** state "rear nut not fitted" in SW-POWER's row and the echo, or model it.

## Checked and holds

- **Panel outline and mounting cuts.** 50.5 × 128.5 × 2 [ds Doepfer via `config/module.yaml`]. Holes at x 7.5 / 43.06 ([calc] 7.5 + 7 × 5.08) and y 3.0 / 125.5, slotted ±1.5. Also read off the proof image (slot ≈ 6.2 long [calc 3.0 + 3.2]).
- **Knobs.** [calc] Pot pitch 17 with a 14 mm budget gives 3 mm gaps. Edge margins are 8.25 − 7 = 1.25 and 50.5 − 49.25 = 1.25 ([repo] DRC 1.25). 3 × 15 + 2 × 3 = 51 > 50.5, so the "≤14 mm" claim holds.
- **Plug grips.** 13 − 10 = 3 mm down a column. Across, 34.75 − 15.75 − 10 = 9.0. Plug top (88.5 + 5 = 93.5) to knob budget foot (106 − 7 = 99) is 5.5. All match the DRC lines.
- **Toggle hole and switch.** 6.5 mm with a 5.8 (.228") D-flat [ds NKK p.7 accessory panel cut-out] = `panel-toggle-hole`. Bushing 8.9, 2.6 mm panel max, body 7.9 × 13.0 × 9.4, lugs 4.5 and 4.7 pitch [ds NKK p.11 single-pole solder lug]. Contact code G is in the MPN.
- **PJ398SM.** Body 9 deep, bushing 5.5, tails 3.5. Pins at +4.92 / −3.38 / −6.48. Front view 6 / 4.5 [ds PJ398SM-drawing.jpg]. All three pins come out of the back of the body, so the board is parallel to the panel and its depth is 9.0 ([repo] `pcb-geometry.echo`). Jacks on their sides: the 13.85 footprint vs the 13 pitch rule holds.
- **Jack tips toward the header.** Left column at angle 180 puts the tip at 15.75 + 4.92 = 20.67. Right column puts it at 34.75 − 4.92 = 29.83. The header columns are at 23.98 / 26.52. DRC "J-B2B-MOD's pads clear of the jacks' footprints" = 1.16.
- **J-B2B-MOD allocation.** Both exported netlists give pins 1-20 the same nets (module-main `J2`, module-jack `J7`). The set is exactly the README table: BREATH_JACK 11, PITCH_JACK 14, MOD1 15, MOD3 16, MOD2 17, MOD4 20. Odd pins carry the left column (BREATH, MOD1, MOD2); even pins the right (PITCH, MOD3, MOD4).
  - On the jack board, J1 (pitch) and J2 (breath) TIP nets match their sheets, and pots RV1-3 land on the pins the README names.
  - [calc] Every signal pin except 19 (`UMBILICAL_POS12`) has an AGND_MOD pin across or adjacent, as claimed.
  - [repo] `layout.jacks` = `art.text.jacks` order, and `panel-art-check.txt` puts `breath` at x 2-10 and `pitch` at 40-48.5, so the art follows the swap.
- **Stack.** [calc] Main board front 18.3 − jack board rear 10.6 = 7.7 standoff, faced 0.3 off an 8.0 stock part. LED spacer 9 − (5.55 − 1.0 − 2.0) = 6.45. Header length 1.5 + 1.6 + 7.7 + 1.6 + 1.5 = 13.9 ≤ TSW-110-09's 18.54 overall [ds SAMTEC-TSW p.1 lead-style −09: 18.54 / 10.16 / 5.84]. With the insulator on the main front, [calc] the jack side protrudes 10.16 − 5.16 − 1.6 = 3.4 and the main side 5.84 − 1.6 = 4.24. Nothing is in front of the header to foul either.
- **POT-RESP fits the same model as the R0904N.** RV09AF-40 has L measured from the seating plane, a 6.8 + 0.8 body, 3 × ø1.0 pins at 2.5, and 2.1 × 1.8 slots 10.6 apart and 7.0 from the pin row [ds RV09AF-40.pdf p.3]. That matches `Potentiometer_SongHuei_R0904N_Single_Vertical` [repo].
- **16-pin header.** Pins 1-2 NEG12, 3-8 GND, 9-10 POS12, 11-16 unconnected on the sheet [repo board-netlist]. Pin 1 is at the bottom per Doepfer, the red stripe is called out, and `D-REVPOL` covers a reversed ribbon. [calc] Its body (y 21.0-49.0) clears the lower-right standoff head (top 20.0).
- **Depth.** 38.8 behind the rear face (INFO only, per the owner).
- **NE8FAV.** No PUSH-tab slot: the tab plate is 1.8 in front of the panel face [repo DRC]. The drop zone keeps the toggle sweep 9.85 clear. The NE8MX stands 29.7 proud against the tallest control at 17.
- **Tools.** `tools/kicad.py check` PASS (22 sheets, 6 boards). `check-netlist --strict` reports 0 problems. `cad.py check` shows 72 of 73 module and body outputs current; the one exception is A7-1.
