# A6 - The instrument's boards physically

**Slice:** main and key board footprints (J-MCU, J-UMB, J-CHAIN, U-BREATH, D-LED and its rotation), 3D models, mounts and columns, the cassette (ADR 0025), the U-bolt clamp, body CAD (config/body.yaml, drc.echo, clash), board outlines vs pcb-geometry, JLC assembly fields.
**Revision measured:** 13197f8 (git archive copy; tools/ pinned at the same revision)
**Tools:** `tools/cad.py check`; `tools/check-staleness.py`; `tools/kicad.py check` (PASS); `tools/pcb.py check` on both key boards (0 errors); OpenSCAD re-run of `woody_body.scad part=drc` with a probe echo (the output reproduces `mechanical/drc.echo` byte for byte); pcbnew Python (footprint flip and pad geometry, Edge.Cuts); kicad-cli BOM export of the main-board sheets; pdftoppm of the banked Hanxia, R-78E and WS2815B-V1 drawings.

## Summary

- **Holds:** the column stack arithmetic, the U-bolt clamp, mount positions and counts (8 + 3), the key-board outlines and NPTH mounts against the body CAD, the main-board DXF against pcb-geometry, the J-CHAIN tails, U-BREATH's orientation and port slot, the LED-row data direction, and the near thumb row's 180° turn as `pcb.py place()` implements it.
- **Does not hold:** three through-hole parts on the main board have tails longer than the 1.3 mm gap to the grounded bottom plate. One of them, J-UMB, is documented as handled ("the plate stops short of J-UMB"), but the plate ends 0.3 mm past its tail row (A6-1, A6-2).
- **The WS2815B-V1 chamfer claim is contradicted by its own datasheet page** and by JLC's footprint. The repo's orientation instruction may place 13 LEDs 180° wrong, with 12 V reversed (A6-3).
- **The regulator block is under the RH key board.** The DRC says it is not, and its 7.7 mm margin is really 3.0 mm (A6-4).
- **Main-board assembly fields would stop `pcb.py`'s fab export:** A1, NT1 and NT2 (A6-5).
- **Several "fix did not reach the derived page" items:** the LED courtyard in body.yaml, the KS-33 pad size in the docs, and the J-MCU, MECH-UBOLT and MECH-SERVICECOVER BOM rows.

## Findings

### A6-1 - J-UMB's 3.00 mm tails stand over the grounded bottom plate, which they reach
**Severity:** high
**Node:** J6 / `J-UMB` (all 8 umbilical conductors, including +12 V), `PLATE-BOTTOM`, `PWR_GND`

**Evidence:**
- The plate ends at `bplate_x1 = ua_x0 - umb_joint_d - board_clear` [repo mechanical/cad/woody_body.scad:459]. That is 299.9 - 2.5 - 1.5 = **295.9** [OpenSCAD probe: `bplate_x1 = 295.9, ua_x0 = 299.9`]. The rule clears J-UMB's *insulator* (297.4-299.9, [repo mechanical/export/pcb-geometry.echo:35]), not its tails.
- The tail row is 1.80 mm behind the insulator's back: footprint pads at x = 0, insulator from x = 1.8 to 4.3 [repo hardware/lib/woody.pretty/PinHeader_1x08_P2.54mm_Horizontal_Hanxia_PZ2.54-WZ.kicad_mod; hardware/lib/README.md]. So the row is at 297.4 - 1.8 = **295.6** [calc]. The 0.64 mm square tail spans 295.28-295.92, all of it over the plate.
- The tail is **3.00 ±0.2** mm [ds HANXIA-HX-PZ2.54-1x8P-WZ.pdf, side view], and the BOM says so too ("the 3.00 mm tails down through the tongue", [repo hardware/bom.csv J-UMB]). Below a 1.6 mm tongue that is 1.4 ±0.2 mm [calc].
- The gap from the tongue to the plate is 1.3 mm: `cb_z - z_bplate_top` = 8.5 - 7.2 [OpenSCAD probe]. The tongue's end mounts carry the same spacer [repo drc.echo:50].
- So the tails need 1.4 mm and have 1.3 mm: **-0.1 mm** nominal, between -0.3 and +0.1 at the tolerance limits [calc], onto aluminium bonded to `PWR_GND`.
- The main-board README says "the plate stops short of `J-UMB`" [repo hardware/boards/main-board/README.md:139], and ADR 0025 point 2 says "`J-UMB`'s through-hole tails stand below the tongue". No DRC tests these tails. The body CAD models J-UMB as its insulator cube only [repo woody_body.scad:1108], so clash.txt cannot see them.

**What would settle it:** set `bplate_x1` from the tail row plus its pad (295.6 - 0.85 - clearance), or cut a window, and add a DRC line like *"J-CHAIN pin tails clear of the bottom plate"*. The BOM's alternative, Samtec TSW-108-08-G-S-RA (tail 2.29), would leave 0.61 mm.

### A6-2 - U-BUCK's and HDR-SERVICE's through-hole tails also cross the plate gap, and nothing lists them
**Severity:** high
**Node:** U5 / `U-BUCK` (R-78E5.0-1.0, +Vin pin), J2 / `HDR-SERVICE`, `PLATE-BOTTOM`

**Evidence:**
- **U-BUCK:** the R-78E's pins are **4.10** long below the body [ds datasheets/discrete-and-power/R-78E5.0-1.0.pdf, dimension drawing]. Below a 1.6 board that is 2.5 mm, into a 1.3 mm gap: **-1.2 mm** [calc]. The regulator block stands at x 229.8-239.8 [repo pcb-geometry.echo:37], over the plate, which runs to 295.9.
- **HDR-SERVICE:** HX PZ2.54-1x5P ZZ, tail **3.00 ±0.2** [ds HANXIA-HX-PZ2.54-1x5P-ZZ.pdf]. That is 1.4 mm below the board: **-0.1 mm** [calc]. It is anywhere over the plate, since pcb-geometry does not place it.
- The README's list of tails facing the plate names only J-CHAIN, J-MCU and J-UMB [repo hardware/boards/main-board/README.md:139]. drc.echo checks only J-CHAIN [repo drc.echo:54].
- Both parts are `Assembly = hand` [kicad-cli BOM of main-board.kicad_sch]. Clipping their tails flush is possible, but no page says to do it. The board_clear rule (1.5) that every other underside item is held to is not met either way.

**What would settle it:** a window in `PLATE-BOTTOM` under each part, as ADR 0025's *Open* allows for underside parts, or a stated trim length with a DRC line.

### A6-3 - The WS2815B-V1 datasheet puts the chamfer at pin 1 on its pin-out drawing, so the footprint's "chamfer = pin 4" rotation guidance may reverse all 13 LEDs
**Severity:** high (blocking if confirmed: the LEDs would get 12 V reversed)
**Node:** D7-D19 / `D-LED`, `woody:LED_WS2815B-V1_PLCC6_5.4x5.0mm_P1.6mm`

**Evidence:**
- On p.2 the **PIN Configuration** drawing (a top view, lens visible) puts 4 DIN1 at top-left, 3 DO at top-right, 1 NC at bottom-right, and **draws the corner chamfer at the bottom-right, at pin 1 (NC)** [ds datasheets/led/WS2815B-V1.pdf p.2, rendered at 300 dpi].
- The *Mechanical Dimensions* top view on the same page shows C0.9 at top-left but has **no pin numbers**. The repo's claim, "the body's chamfer (C0.9) is at pin 4, not pin 1 [ds p.2]" [repo hardware/lib/README.md; ADR 0028:126; hardware/bom.csv D-LED], only follows if that unnumbered view is in the same orientation as the pin-out. The numbered drawing says otherwise.
- JLC's own footprint for C5446699 also puts pin 1 at the chamfer [repo hardware/lib/README.md, citing datasheets/led/EASYEDA-C5446699-WS2815B-V1-FOOTPRINT.json]. The repo treats that as JLC's numbering differing. It agrees with the pin-out drawing.
- The community STEP was "checked" against the footprint [lib README], which only shows it was drawn from the same reading.
- The order instruction is "pass it only when the preview's chamfer lands on the silk triangle" [lib README], and the silk triangle is at pad 4 [repo footprint fp_poly at (-3.75,-3)]. If the pin-out drawing is right, that instruction places every LED 180° wrong: VDD (2) and GND (5) swap, putting 12 V reversed across the part, and DO and DIN2 swap.

**What would settle it:** a part in hand, with a meter's diode test identifying VDD and GND against the chamfer, or a second Worldsemi or vendor drawing with numbered pins and the chamfer. Until then, do not tell the assembler to align the chamfer with the triangle.

### A6-4 - The regulator block is under the right-hand key board; drc.echo says "beside the key boards" and reports 7.7 mm spare against the wrong ceiling
**Severity:** medium
**Node:** `REGULATOR-BLOCK` (U-BUCK, C-STRIP-BULK), `PCB-CLUSTER` right_hand

**Evidence:**
- The block spans x 229.83-239.83 and y 34-49 [repo pcb-geometry.echo:37]. The RH key board's Edge.Cuts are a full rectangle, 144.4-251.3 by 7.5-49.5 [pcbnew read of key-board-rh.kicad_pcb; `kb_rect("right_hand") = [144.4, 7.5, 251.3, 49.5]`, OpenSCAD probe]. So the block is wholly under the board.
- `under_keys()` still tests per-key `cluster_pcb_w` squares [repo woody_body.scad:1123]. Those squares predate the full-rectangle boards of ADR 0025, so the function returns false here. The DRC then uses `gap_room` = 20.2 instead of `cb_room` = 15.5 [repo drc.echo:45-46,55].
- The true spare is 15.5 - 12.5 = **3.0 mm**, not 7.7 [calc]. It still passes, and clash.txt finds nothing.
- The labelled reason, "beside the key boards, clear to the lid", is false. Anyone sizing C-STRIP-BULK (`boards.tall_h` is tbd, "lay them down … where drc.echo says they do not fit" [repo config/body.yaml:363]) reads a margin 4.7 mm too generous.

**What would settle it:** test against `kb_rect`, not key squares.

### A6-5 - A1, NT1 and NT2 carry assembly flags that make `pcb.py`'s assembly export exit on the main board
**Severity:** medium
**Node:** A1 / `U-MCU-RT`, NT1 / `NT-DIG`, NT2 / `NT-AGND`

**Evidence:**
- **A1:** the symbol has `(in_bom yes) (on_board yes)`, an empty Footprint and no `Assembly` field [repo hardware/carrier/carrier.kicad_sch:2136-2141]. Its own `Pins_source` says "the Matrix is on the lid (on_board no)" [same symbol].
- **NT1, NT2:** `Assembly = none` with `(in_bom yes)` [repo carrier.kicad_sch ~2265-2278; power-entry-instrument.kicad_sch ~2063-2080].
- `assembly_files()` exits on `none` with in_bom ("Assembly = none but in the BOM"), and on any part with no Assembly field [repo tools/pcb.py:1300-1318]. The key boards never met this because they have neither kind of part.
- The README says "the layout skips a part with no footprint" [repo main-board/README.md:143]. That covers placement, not the fab export.

**What would settle it:** set A1 to on_board no and in_bom no (or Assembly none plus exclude), and tick Exclude from BOM on NT1 and NT2.

### A6-6 - `lighting.led_court` no longer matches the footprint it cites
**Severity:** low
**Node:** `D-LED`, `config/body.yaml lighting.led_court`

**Evidence:**
- The register gives `[6.9, 5.5]`, sourced to "the footprint's courtyard … pads' 6.4 across and the body's 5.0, each with 0.25" [repo config/body.yaml:1088-1091].
- Since commit 3cf3589 added the chamfer triangle, the courtyard is x -3.8..3.45 and y -3.05..2.75 [repo hardware/lib/woody.pretty/LED_WS2815B-V1…kicad_mod]: **7.25 × 5.8**, and asymmetric.
- At rot 180 the 3.8 side faces the tail. *"LED row off the U-bolt station"* reports 4.885 mm from LED7's courtyard to the station. With the true courtyard it is 133 - (124.665 + 3.8) = **4.535** [calc]. It still passes.
- This is shape 1: the footprint fix did not reach the register that copies it. A6-3 may move the triangle again.

### A6-7 - The KS-33 pads are 2.6 mm, not the 2.8 mm (0.3 mm ring) that ADR 0020 Amendment 6 and the lib README state
**Severity:** low
**Node:** `SW1-n` footprint `woody:SW_Gateron_KS33_1u`, key boards SW1-6, main-board SW1-10

**Evidence:**
- The footprint and all 22 placed switch pads read `(size 2.6 2.6) (drill 2.2)` [repo footprint; grep of both key-board .kicad_pcb]. They have been 2.6 since the commit whose message introduced "2.8" (ee94dc4, its diff).
- The ring is (2.6 - 2.2)/2 = **0.2 mm** [calc], not 0.3. That is above `fab: annular_min 0.18` but below the 0.25 recommended [repo key-board-lh/layout.yaml:35].
- The text is wrong in [repo docs/decisions/0020…md:650] and in [repo hardware/lib/README.md, KS-33 row].

**What would settle it:** decide which is meant. JLC's drill oversize for plating, plus 0.08 undersize, at a 0.2 ring argues for 2.8.

### A6-8 - The J-MCU BOM row still says the part is open and the ribbon arrives "from the mouth side"
**Severity:** medium
**Node:** `J-MCU` (BOM row, fragment hardware/carrier/bom.csv), J1

**Evidence:**
- The row's status is `open`. Its notes say "PART NUMBER OPEN [from memory …]", "the envelope is from memory too", "ribbon conductor n = pin n [IDC numbering, from memory - confirm on the socket's drawing]", "the ribbon arriving level from the mouth side; the LED strip stops short of it" [repo hardware/bom.csv J-MCU].
- The sheet has bought the part: XKB X1270WR-2x12A-9TV01, LCSC C5147255, with a footprint drawn from the banked drawing [kicad-cli BOM export; repo hardware/lib/README.md].
- The body CAD faces the mouth to the tail ("+1 the tail - the ribbon comes in over the tongue", [repo woody_body.scad:780-783; pcb-geometry.echo:34]).
- So the row contradicts the sheet on identity and the CAD on direction. This is shape 1.

### A6-9 - MECH-UBOLT, J-CHAIN and CBL-CHAIN notes still argue from the LED strip, and MECH-UBOLT cites a DRC line that no longer exists
**Severity:** low
**Node:** `MECH-UBOLT`, `J-CHAIN`, `CBL-CHAIN` BOM rows

**Evidence:**
- MECH-UBOLT: "SIZED BY THE MAIN BOARD …: its nuts stand on the board's top face beside the LED strip, and an M5 nut's keep-out reaches under the strip … (mechanical/drc.echo, LED strip clear of the U-bolt nuts)" [repo hardware/bom.csv MECH-UBOLT].
- ADR 0028 removed the strip, and body.yaml:927 and DESIGN.md:346 say the strip "that held it to M3 is gone". drc.echo has no "LED strip clear of the U-bolt nuts" line; its successor is *"LED row off the U-bolt station"* [repo drc.echo:35].
- J-CHAIN and CBL-CHAIN still say "beside the LED strip" and "the LED strip's light".

### A6-10 - MECH-SERVICECOVER is a live BOM row (qty 1) for a part ADR 0009 removed
**Severity:** low
**Node:** `MECH-SERVICECOVER`

**Evidence:**
- [repo hardware/bom.csv:189; hardware/unplaced.csv:23] say "Screwed cover … Screws into the plate stack … with the etherCON backing plate".
- ADR 0009:506 says "Superseded (2026-09-26 …): there is no service cover", and service-uart.md:9 agrees.
- After ADR 0025 nothing screws into the body at all. The row is ordered and costed as if live.

### A6-11 - The key boards' J-CHAIN footprints carry no 3D model, so their 3D renders omit the header
**Severity:** low
**Node:** J1 on key-board-lh and key-board-rh

**Evidence:**
- The library footprint names `woody.3dshapes/Samtec_SHF-106-01-L-D-RA.step`. The placed J1 on both boards has an empty model list, though its pads are identical to the library's [pcbnew comparison].
- `key-board-*.pcb-3d-*.png` therefore show no header. That is the one part whose clearance the 3D view is for.
- `pcb.py check` ignores `lib_footprint_mismatch` by design [repo hardware/lib/README.md], so nothing flags it.

### A6-12 - pcb-geometry's U-BREATH record cannot be used as a footprint placement as written
**Severity:** advisory
**Node:** U10 / `U-BREATH`

**Evidence:**
- The echo gives rotation **0** with the lead span 17.8 across y, in the body frame ("ports toward +x") [repo woody_body.scad:788-790].
- The footprint has its ports at -y and its pad rows across x [repo NXP_Case1351-01…kicad_mod]. At rotation 0 it would point the ports across the body. It needs -90 to match the CAD.
- 17.8 is the lead tips. The land is 18.8 (`boards.sensor_land_w`), which the CAD itself uses to centre the part, and its pads end 0.5 mm from the board edge [calc: 39.6 + 9.4 = 49.0 vs 49.5].
- The main-board mode of `pcb.py` should find the rotation from the ports, as `place_chain` does for J-CHAIN [repo tools/pcb.py:201-218], not take it from the echo.

### A6-13 - Two DRC lines report figures that are not the margin they name
**Severity:** advisory
**Node:** drc.echo

**Evidence:**
- *"chain headers on the … boards clear of the switches"* prints 79 and 190, the headers' x positions, under PASS [repo drc.echo:56-57; woody_body.scad:1564]. No margin is visible.
- `boards.smt_h` = 2.3 is sourced to "SMA/SMC diodes 2.29-2.62" [repo config/body.yaml ~345]. That is the minimum of a range whose maximum (SMC SS34, 2.62) exceeds the value.

## Checked and holds

- **CAD outputs are current.** `cad.py check`: the only stale output is `module-photo-detail` (module; A7's). The re-run `part=drc` reproduces drc.echo exactly [OpenSCAD].
- **The column stack is right.** 1.2 + 1.3 + 1.6 + 18.8 + 1.6 + 1.3 + 1.2 = 27.0 = the cassette height [calc; drc.echo:84]. The standoff, 18.8 = 28.9 - 10.1, is faced 1.2 from 20 stock. The rooms check out: 15.5 = 28.9 - 1.8 - 1.5 - 10.1, and 20.2 = 31.8 - 1.5 - 10.1 [calc].
- **Mount positions, counts and BOM quantities agree.** Eight columns at the key boards' corners match the key-board NPTH holes: LH H1-H4 at pcb (100,138.9)…(181.7,104.1) = body (40,11.1)…(121.7,45.9) [pcbnew; pcb-geometry:7-10,51-58]. The end mounts are (11.5,11.5), (278.31,13) and (278.31,30). The dropped mount is at 7.51 mm from its column = √(7.5² + 0.4²) [calc]. The quantities agree: MB-STUD and MB-SPACER 11, MB-NUT 3, COL-STANDOFF, COL-SCREW and KB-SPACER 8 [repo bom.csv].
- **The main-board outline matches pcb-geometry.** main-board.dxf is the 7.5-251.3 × 7.5-49.5 board plus a tongue to 299.9 at y 7.5-34, flush on the low-y side [DXF parse]. Its holes are at the 11 mounts and the U-bolt legs (133, 18.5/38.5, Ø4), with the sensor port slot at x 20.29-28.89, y 39.05-44.35 = P2 at y 41.7 [calc].
- **The neck and U-bolt clamp hold.** The neck is 9 + 16 + 9 = 34 = 42 - 2×4 [calc], and the clamp gap is 1.3 = spacer.
- **The LED row is placed as stated.** 13 LEDs at 16.67: (224.685 - 24.645)/12 = 16.67 [calc], and the station is midway between LED7 and LED6 at 133.0 [calc]. Rot 180 puts DIN1/DIN2 (local -x) toward the tail where the data arrives, matching the pin table [ds WS2815B-V1 p.2]. The orientation issue in A6-3 is separate.
- **The thumb-switch turn does what the ADR says.** `place()` uses a left/right flip, then sets the rotation. I measured it: rot 0 on the bottom puts pads at KiCad y -4.7/-5.75 = body +y, so the near row at 180 points its pins away from the LED row, as ADR 0028 states [pcbnew test]. (I checked this because a naive reading suggests the opposite.)
- **U-BREATH is oriented consistently.** Pins 1-4 face the near board edge (+y), and P1 is on the pins 5-8 side, at -offset, matching the CAD [footprint pads; woody_body.scad:944]. The LED13 courtyard clears the sensor courtyard by 0.65 [calc].
- **J-CHAIN clears its neighbours.** The main board's J-CHAIN tails clear the plate by 0.75 [calc: 2.15 - 1.6 = 0.55; 1.3 - 0.55]. J-MCU's (2.10 tails) clear by 0.8 [calc]. The J-CHAIN headers clear LT4/RT4 and the columns.
- **Both key boards pass.** `pcb.py check`: 0 errors on each. The mounts are NPTH 2.7 (ADR 0025 point 7), and the outlines are 36.4-125.3 and 144.4-251.3 × 7.5-49.5, matching the DXFs.
- **Key-board JLC files are complete.** Every machine part has an LCSC number. The CPL is bottom-side with KiCad rotations uncorrected, by design (pcb.py:1286). The hand list is J1 and the switches.
- **Main-board footprints match their parts.** Every machine part has a footprint, an MPN and an LCSC number. The packages are right: SMC SS34, SMA SMAJ15A and SS14, SOD-123/323, SOT-23(-5), SOIC-8/14/16, SWPA6028 and BLM21 0805. The R-78E-0.5 footprint is the same SIP-3, 11.6 × 8.5 × 10.4, as the R-78E5.0-1.0 [KiCad lib descr; ds]. The 3D model paths in woody.pretty resolve to existing files.
