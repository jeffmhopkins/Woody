# R3 — the left-hand key board's PCB as a made thing

**Slice:** R3, cold (no `docs/review/**` read except the wave README).
**Revision measured:** `eebcdfb` (working tree at `36341bf`, which adds only the wave README; `git diff eebcdfb -- hardware tools` is empty) `[run: git diff eebcdfb --stat -- hardware tools]`.
**`tools/` pinned:** I only ran the frozen tools. Nothing in the repository was changed except this file.
**Scratch:** `/tmp/claude-0/-home-user-Woody/e3911cc0-db94-59ad-9e1f-62b9c10df7ff/scratchpad/R3/`. It holds the layer renders (`bsilk.png`, `fsilk.png`, `bcu.png`, `fcu.png`, `tr.png` and crops), the pcbnew scripts (`net.py`, `pads.py`, `tr.py`, `frag.py`, `silk.py`, `sv.py`, `gp.py`, `geo.py`) and a regenerated `fab/`.

Coordinates below are KiCad board mm (y down), as the `.kicad_pcb` stores them. Body CAD maps to the board as board = (body_x + 60, 150 − body_y) `[calc: U-KEYS-LH layout.yaml [90.5, 43.5] -> board (150.5, 106.5)]`.

## Summary

| Id | Sev | Node | Headline |
|---|---|---|---|
| R3-1 | medium | C-DECOUPLE-165-LH, U-KEYS-LH pin 8, GND_CHAIN | The decoupler returns to pin 15 (CLK INH), not to GND pin 8. The copper path to pin 8 is 38.5 mm |
| R3-2 | medium | U-KEYS-LH pin-1 mark, /CHAIN_SHLD via (155.8, 108.9) | The register's pin-1 triangle is printed over a via hole |
| R3-3 | low | B/F silkscreen vs vias | Eleven silk labels and outlines sit on via holes or rings, including `LH3`, `QH`, `GND`, `CD` and both title blocks. The commit's "off every pad and hole" claim is false for vias |
| R3-4 | low | /CHAIN_SER_LH F.Cu (140.8, 113.3) | A 45° acid-trap junction remains. The README's "no acute track junction" is false, and `check_tracks` cannot see a T onto a segment's middle |
| R3-5 | low | `key-board-lh.pcb-copper-bottom.png` | The render the README calls "the assembly drawing" is illegible: Fab references and values overprint each other |
| R3-6 | low | /HOP_LH_LT, /LH4–LH5 SWITCH_LEG | Needless vias and detours: the QH test-pad stub uses 3 vias (5 on the net), LH5's leg uses 2, and LH4/LH5 are routed unlike LH1–3 |
| R3-7 | advisory | V3V3_CHAIN_LH at U pins 12 and 16 | Duplicate parallel 0.4 mm stubs 0.2 mm apart, and 17 track fragments under 0.35 mm |
| R3-8 | advisory | silk text, rule `fab.silk_text_min`/`silk_line_min` | Every silk character sits exactly on JLC's minimums (1.0 mm / 0.15 mm, 1:6.7 against the preferred 1:6) |
| R3-9 | advisory | layout.yaml `parts:` TP comment, README Rev A row | "Test pads in the register's pin order" holds for SCK/SH/LD but not for SER/QH or GND |
| R3-10 | advisory | J-CHAIN pads | The annular ring is 0.185 mm, on JLC's absolute minimum (0.18), not its recommended 0.25. The trade-off is documented, and is recorded here only so the board's ordering risk is visible |

---

### R3-1 [medium] The decoupler returns to pin 15 (CLK INH), not to GND pin 8; its copper path to pin 8 is 38.5 mm

**Node:** C-DECOUPLE-165-LH pad 2 / U-KEYS-LH pins 15 and 8, net GND_CHAIN. **Rule:** the decoupling loop.

**Evidence.**
- `layout.yaml` places C-DECOUPLE-165-LH "across the ends of pins 16 (VCC) and 15 (GND): the loop is two stubs" `[repo hardware/boards/key-board-lh/layout.yaml, parts:]`.
- On the SN74HCS165, pin 15 is **CLK INH**, a clock-inhibit *input*. Ground is **pin 8**, at the diagonally opposite corner of the SOIC `[datasheets/logic/SN74HCS165-ti-scls828a.pdf p.3, Table 5-1]`. TI asks for the capacitor to be "electrically close to both the VCC and GND pins" `[same, p.16 §9.2.2]` and "as close to the power terminal as possible" `[same, p.17 §10]`.
- On the board, pin 15 is on GND_CHAIN only because CLK INH is tied low. Pad 2 of C-DECOUPLE-165-LH (153.35, 101.8) is joined by a stub to pin 15 (153.68, 104.03) and to a GND via at (151.0, 102.1). Pin 8 (146.06, 108.97) has its own GND via at (145.2, 108.3) `[run: pads.py, tr.py]`.
- **Routed tracks only:** the shortest GND_CHAIN track path from C-DECOUPLE pad 2 to pin 8 is **81.6 mm**, by way of J-CHAIN pins 10/8/6/4, C-KEY-LH2, SW-LH3 and TP-GND `[run: scratch gp.py]`.
- **With both pours filled:** I rasterised GND copper (fill + tracks + pads, 0.1 mm grid, both layers, joined at GND vias and PTH pads) and took the geodesic. The path is **38.5 mm** from pad 2 to pin 8, and 40.5 mm from pin 15 to pin 8. The straight line is 10.2 mm `[run: scratch geo.py; calc hypot(7.29, 7.17) = 10.2]`. The two GND vias beside the register are 8.4 mm apart, but the F.Cu pour between them is 34.8 mm long, because the F.Cu signal buses above the register (/CHAIN_SHLD at y 103.1, /HOP_LH_LT at 104.1, /CHAIN_SCK at 106.7, /KEY_LH2 at 109.5, plus the pin-3 V3V3 fence round J-CHAIN) cut the pour into strips `[run: geo.py; render fcu_u.png]`.
- The VCC side is short: pad 1 to pin 16 is 2.3 mm `[calc]`. The problem is the ground half of the loop.

**Why it matters.** This is the project's worked example, and its own comment names the wrong pin as ground. The register drives QH down the ribbon (`/HOP_LH_LT`). The loop that carries its switching current runs through tens of millimetres of fragmented pour. The README (*Bring-up* step 6) already expects the rail to ring through FB-CHAIN.

**Proposed fix.**
- Give pad 2 a direct GND track to pin 8. For example, run it on B.Cu along the register's end and under the body, which today carries V3V3 and the SCK via.
- Or keep the F.Cu pour solid between the two GND vias, by moving the F.Cu buses off the rectangle x 145–152, y 101–109.
- Correct the `layout.yaml` comment to "pins 16 (VCC) and 15 (CLK INH, tied to GND); ground pin 8 is at the opposite corner".
- A `pcb.py` check for "decoupler GND pad to the IC's GND pin, copper geodesic ≤ N mm" would keep the fix in place (R6's domain).

### R3-2 [medium] The register's pin-1 triangle is printed over a via hole

**Node:** U-KEYS-LH pin-1 mark (B.Silkscreen). Via /CHAIN_SHLD at (155.8, 108.9), drill 0.3, Ø0.7.

**Evidence.**
- The footprint's pin-1 triangle has bbox (155.44–155.91, 108.78–109.42). 0.0517 mm² of its 0.1928 mm² (**27 %**) lies over the via's 0.3 mm **hole**, and the rest touches the ring `[run: scratch sv.py, polygon intersection]`.
- In the zoomed render the via sits on the triangle `[render scratch bs_u.png]`.
- Vias are tented (they are not in B.Mask) `[run: sv.py; the B.Mask Gerber has no 0.7 flashes, fab/key-board-lh-B_Mask.gbr apertures]`, so ink lands on the tent over an open 0.3 mm hole and on the ring's dome.

**Why it matters.** The README makes this mark *the* orientation check: "The register's (`U-KEYS-LH`) pin 1 is marked on the silkscreen, and that is the one to look at" `[repo hardware/boards/key-board-lh/README.md, Assembly]`. JLC's preview renders the Gerber, so the mark will look fine there. It is the physical board, at inspection and rework, where a quarter of the mark is printed onto a hole. U-KEYS-LH is the only polarised machine-placed part.

**Proposed fix.** Move the /CHAIN_SHLD via at least 0.5 mm clear of the triangle. There is room toward +y, since the B.Cu segment (155.0, 108.9)→(155.8, 108.9) can lengthen. Also add "silk over a via drill" to `check_silk` (see R3-3).

### R3-3 [low] Eleven silk labels and outlines sit on via holes or rings; "off every pad and hole" is false for vias

**Node:** B.Silkscreen and F.Silkscreen against every via. **Rule:** the commit claim "Labels keep 0.25 mm apart and off every pad and hole" `[run: git show eebcdfb]`.

**Evidence** `[run: scratch sv.py, silk polygon ∩ via drill / via Ø0.7]`:

| Silk item | Via (net, position) | Over |
|---|---|---|
| B `LH3` (a key's name) | GND_CHAIN (156.6, 119.9) | hole |
| B `QH` (test-pad name) | GND_CHAIN (146.4, 111.7) | hole |
| B `CD` | GND_CHAIN (151.0, 102.1) + /KEY_LH5 (152.0, 102.5) | hole + ring |
| B `GND` (test-pad name) | /KEY_LH1 (148.4, 115.9) | ring |
| B `SER` | /CHAIN_SER_LH (142.4, 114.9) | ring |
| B `PF` | /HOP_LH_LT (145.2, 104.1) | edge (visible in `bs_u.png`) |
| F title `WOODY key board LH` | /HOP_LH_LT (145.2, 104.1) | hole |
| F `J-CHAIN` | /HOP_LH_LT (134.2, 104.1) | ring |
| B U-KEYS-LH outline | GND_CHAIN (145.2, 108.3) | ring |
| B C-BULK-CHAIN-LH outline | GND_CHAIN (126.0, 107.9) | ring (64 % of the segment) |
| B `S` of LH1/LH2/LH3 | each SWITCH_LEG via | touching (0.0008 mm²) |

- `check_silk` tests silk against pad **mask openings** only `[repo tools/pcb.py check_silk docstring, l.855–]`. A tented via has no mask opening, so none of these is caught.
- KiCad's DRC passes all of them `[run: kicad-cli pcb drc --schematic-parity --severity-all → 0 violations]`.
- The switch-leg vias also make the owner's "same way round every switch" pattern look inconsistent in silk: only LH3's name has a via under it.

**Proposed fix.** Extend `check_silk` to treat a via's drill (or its Ø) as a keep-out. Then move the listed vias or labels. Most need only 0.3–0.5 mm.

### R3-4 [low] A 45° acid-trap junction remains on /CHAIN_SER_LH; the README's "no acute track junction" is false, and the check cannot see it

**Node:** /CHAIN_SER_LH, F.Cu, junction at (140.8, 113.3). **Rule:** no acute junction (README Revisions, Rev A: "no acute track junction"; commit `eebcdfb`: "0 acute junctions (were 4), and a new pcb.py check fails on any").

**Evidence.**
- The F.Cu track (129.2, 113.1)→(140.6, 113.1) turns 45° down to the via at (142.4, 114.9), which feeds TP-SER.
- The branch to the register, (140.8, 113.3)→(141.8, 113.3)→(142.4, 112.7)→via (142.4, 111.5), **starts in the middle of that diagonal**. The copper leaving rightward and the diagonal leaving down-right enclose 45° `[run: scratch tr.py "ACUTE 45.0 F.Cu /CHAIN_SER_LH (140.8, 113.3)"; render scratch ser.png]`.
- `pcb.py check` passes `[run: python3 tools/pcb.py check hardware/boards/key-board-lh → 0 error(s)]`. Its `check_tracks` groups track **endpoints** that coincide `[repo tools/pcb.py l.909–929]`, so an end landing on another segment's interior is never compared.
- (The other "acute" hits my scan reported, at U-KEYS-LH pins 12 and 16, are overlapping duplicate stubs, not wedges: R3-7.)

**Proposed fix.** Start the branch at the corner (140.6, 113.1) and square it, or take it off the horizontal before the bend. In `check_tracks`, also test an endpoint against the interior of every same-net, same-layer segment (R6 to confirm on a scratch copy). Change the README row to match whatever the check then proves.

### R3-5 [low] The "assembly drawing" render is illegible

**Node:** `hardware/boards/key-board-lh/key-board-lh.pcb-copper-bottom.png`. **Rule:** README, *The silkscreen*: "The full references are on the fabrication layer. `key-board-lh.pcb-copper-bottom.png` plots it with the bottom copper, so that render is the assembly drawing."

**Evidence** `[viewed the PNG]`:
- The six TP references run together into one smear ("TP-TP3-SHLD-SCK-GND…").
- Six "test pad" values overprint along one line.
- "C-DECOUPLE-165-LH" is printed twice.
- `U-KEYS-LH`, `74HCS165` and the `R-KEY-PU-FREE3` reference overlap.
- Every key's `R-KEY-PU-LHn`/`R-KEY-SER-LHn` references (vertical) overprint their `2k2 1%`/`100R 1%` values and the `C-KEY-LHn` reference/value pair.

No designator on the key networks can be read off it.

**Proposed fix.** Plot B.Fab with values hidden and references at about 0.6 mm, or drop the claim and point the README at the parts-side silk plus the CPL.

### R3-6 [low] Needless vias and detours; LH4/LH5 routed unlike LH1–3

**Node:** /HOP_LH_LT (QH, the chain's output), /LH4/SWITCH_LEG, /LH5/SWITCH_LEG.

**Evidence** `[run: scratch v.py, tr.py]`:
- **/HOP_LH_LT: 5 vias, 36.4 mm.** The TP-QH stub leaves the F.Cu segment (134.2→145.2, y 104.1) through a via placed **mid-segment** at (141.4, 104.1). It runs B.Cu down to (141.4, 110.5), via, then F.Cu 4 mm to (145.4, 110.5), via, then B.Cu to TP-QH (146.5, 114). That is B→F→B→F→B for a 13 mm test-pad stub on the chain's output line.
- **SWITCH_LEG.** LH1–LH3 are identical: pin 1 on F.Cu to one via beside R-KEY-SER pad 2 (5 segments, 17.4 mm, 1 via each). LH4 uses a different 3-segment route with its via at (175.2, 134.7). LH5 goes B.Cu from the THT pin to a via at (171.4, 113.1), 6.2 mm of F.Cu, then a second via at (177.6, 113.1). Because pin 1 is plated through, the first via is redundant *if* F.Cu were free there. It is not: /KEY_LH4's F.Cu track to its via at (177.4, 117.5) occupies the F.Cu corridor LH1–3 use.
- The owner's rule is about part placement, and that holds exactly (see "Checked and correct"). A reviewer comparing keys still sees five networks placed identically and wired three different ways.

**Proposed fix.** Re-route /KEY_LH4 so LH4 and LH5 can take the LH1–3 leg route (one via each). Feed TP-QH from a via at U pin 9 through the space between the SOIC rows, or move TP-QH so its stub needs one via.

### R3-7 [advisory] Duplicate V3V3 stubs and short fragments at the register

**Node:** V3V3_CHAIN_LH at U-KEYS-LH pins 12 and 16.

**Evidence** `[run: scratch v.py, frag.py]`:
- Pin 12 has two 0.4 mm stubs leaving it 0.2 mm apart: (149.8, 104.9)→(149.8, 105.1)→(147.8, 107.1), and (150.0, 104.9)→(150.0, 105.1)→(150.6, 105.7). Their copper overlaps.
- Pin 16 does the same: (154.8, 104.9)→(154.8, 105.1)→(154.2, 105.7), and (155.0, 104.9)→(155.0, 106.7).
- 17 segments are shorter than 0.35 mm, most of them pad-exit jogs, and 60 segments are off 45° (all 60 end inside a pad, so they are invisible in copper).
- Electrically harmless. It is what a hand router would clean up, and it is on the worked example.

**Proposed fix.** Merge each pair into one stub (router post-pass, or by hand in KiCad).

### R3-8 [advisory] Silk text exactly on JLC's minimums

**Node:** every silk text item. **Rule:** `layout.yaml` `fab: silk_text_min: 1.0`, `silk_line_min: 0.15`.

**Evidence.**
- All 51 silk texts are 1.0 mm high with a 0.15 mm stroke `[run: scratch silk.py]`.
- JLC: "Characters width less than 0.15mm will be unidentifiable", "Characters height less than … 1.0mm will be unidentifiable", and the preferred width:height ratio is **1:6** `[datasheets/fab/JLCPCB-PCB-CAPABILITIES.pdf p.7, Legend]`. 0.15 / 1.0 is 1:6.7 `[calc]`, thinner than preferred.
- The limits are met, but with zero margin. The mirrored parts-side letters are the ones an assembler reads.

**Proposed fix.** Use a 0.18 mm stroke at 1.0 mm (1:5.6), or 1.1 / 0.18 where space allows. Fitting is `pcb.py`'s job, so this is a `SILK_H`/`SILK_W` change and a re-layout.

### R3-9 [advisory] "Test pads in the register's pin order" is only partly true

**Node:** TP-*-LH row. **Rule:** layout.yaml `parts:` comment ("in the order of the register's own pins above them - SER and QH by pins 10 and 9 …"); README Rev A ("six test pads in the register's pin order").

**Evidence** `[run: scratch pads.py]`:
- Along +x the pads run SER 143.0, QH 146.5, GND 150.0, SCK 153.5, SH/LD 157.0, 3V3 160.5.
- The pins run QH (pin 9) 146.06, SER (pin 10) 147.32, so SER and QH are swapped. GND pin 8 is at 146.06, not near TP-GND. SCK/SH/LD (pins 2/1 at 153.68/154.94) and 3V3 (pin 16) do follow the pins.
- TP-SER is not fed from the register at all but from J-CHAIN's F.Cu branch (R3-4).

**Proposed fix.** Reword to "SCK, SH/LD and 3V3 under their pins; SER and QH next to them". Or swap TP-SER and TP-QH, which could also shorten R3-6's QH stub.

### R3-10 [advisory] J-CHAIN's annular ring sits on JLC's absolute minimum

**Node:** J-CHAIN pads (Ø1.07 on a 0.70 drill).

**Evidence.**
- The ring is (1.07 − 0.70)/2 = 0.185 mm `[calc]`. JLC 2-layer 1 oz: "Recommended 0.25 mm or above; absolute minimum 0.18 mm" `[datasheets/fab/JLCPCB-PCB-CAPABILITIES.pdf p.5]`.
- The 1.27 mm pitch leaves 0.20 mm between pads `[calc 1.27 − 1.07]`, so no larger pad fits.
- The trade-off is documented `[repo hardware/lib/README.md, IDC-Header row]`. I record it only so that the one ring on the board at the minimum is on the ordering checklist.

**Proposed fix.** None needed. Optionally list it in the README's *Open* table ("J-CHAIN ring at JLC's absolute minimum; first order confirms").

---

## Checked and found correct

**The owner's rule (network pattern).**
- For all five keys, relative to SW-LHn's centre:
  - C-KEY sits at (+7.3, 0.0), rotation 180.
  - R-KEY-SER sits at (+10.0, +2.7), rotation 90.
  - R-KEY-PU sits at (+10.0, −2.7), rotation 90.
  - Each pad's net is identical: C pad 1 KEY at +8.25 and pad 2 GND at +6.35; SER pad 2 SWITCH_LEG at +1.79 and pad 1 KEY at +3.61; PU pad 1 3V3 at −1.79 and pad 2 KEY at −3.61.
  - All parts are on the bottom and every switch is at rotation 0 on top `[run: scratch net.py]`.
- `layout.yaml` `networks.except: {}` is empty, and none is needed.
- **Silk labels are identical round every switch.**
  - On the bottom: `LHn` at (+7.3, −1.7), `C` at (+7.3, +1.7), `P` at (+11.7, −2.7), `S` at (+11.7, +2.7).
  - On the top: `LHn` at (0, −7.8) for LH1…LH5 `[run: scratch silk.py]`.

**DRC and checks.**
- `kicad-cli pcb drc --schematic-parity --severity-all` gives 0 violations, 0 unconnected, 0 parity issues `[run, in place, report to scratch]`. Run on a *copy* outside the tree, it gives 23 parity warnings and 6 library warnings, because the hierarchical sheets and `woody.pretty` resolve by relative path. That is expected, not a board fault.
- `python3 tools/pcb.py check hardware/boards/key-board-lh` reports 0 errors `[run]`. `python3 tools/kicad.py check` passes: 3 sheets, 2 boards, 39 renders current `[run]`.
- Design rules in `.kicad_pro` match `layout.yaml`: clearance 0.2, track 0.2, via 0.66 / drill 0.3, annular 0.18, hole clearance 0.28, hole-to-hole 0.45, edge 0.3, silk 1.0/0.15/0.15. No board-house test is set to ignore. The ignored tests are footprint-library and courtyard-membership only `[run: .kicad_pro rule_severities]`.

**Tracks and vias.**
- Every V3V3_CHAIN_LH segment is 0.4 mm (51 of 51); every other net is 0.25 `[run: tr.py]`.
- All 37 vias are 0.7/0.3: ring 0.2, which meets JLC's "via 0.1 larger than hole, 0.15 preferred" `[JLCPCB-PCB-CAPABILITIES.pdf p.4]`.
- No via lands in or on an SMD pad. The nearest via ring to a pad edge is 0.197 mm, same-net (C-BULK-CHAIN-LH pad 2). All vias are tented, and the mask web exceeds JLC's 0.10 mm bridge `[run: scratch via-to-pad scan; p.6]`.
- No dangling track ends, no collinear split joints (0 found), no arcs `[run: tr.py]`.

**Pours and stitching.**
- GND_CHAIN is poured on both layers, one main island each (2935 / 2806 mm²), islands removed. The small remaining outlines are fill between J-CHAIN's pad rows, attached to the GND pins `[run]`.
- Thermal spokes are 0.4 mm with a 0.3 mm gap, and min resolved spokes is 2.
- Four keep-out rule areas, 4.9 mm Ø, surround the M2 holes on both layers. That clears the screw head and washer: the echo gives 3.8 and 4.5 `[repo mechanical/export/pcb-geometry.echo "standoff"]`.
- There is no dedicated stitching array. Layers join at 11 GND vias and 5 THT switch GND pins. Adequate for this board, but see R3-1 for the pour's fragmentation near the register.

**Top-side mask.** The switch pins have B.Mask only, and their top ring is under mask. That is inherited unchanged from the banked marbastlib footprint `[datasheets/mechanical/GATERON-KS-33-SW_KS33_1u.kicad_mod l.44–45]`, so it is deliberate, not a defect.

**J-CHAIN mouth and markers.**
- The echo "chain" gives mouth x 78.5, facing +1 (toward the tail), and mouth-to-far-row 7.86 `[repo mechanical/export/pcb-geometry.echo l.6]`. That puts the pad centre at body x 78.5 − (7.86 − 0.635) = 71.275, board 131.275 `[calc]`. The board has pads at x 130.64/131.91 (centre 131.275) and y 104.81–111.16 (centre 107.985 = 150 − 42.015) `[run: pads.py]`.
- Pads 1→2 point +x, and the footprint puts its mouth at +x from pin 1's row `[repo hardware/lib/woody.pretty/IDC-…kicad_mod descr; tools/pcb.py place_chain]`. The mouth therefore faces +x, toward the tail and away from the MOUTH end. This matches README step 1.
- **Bottom silk:** the J-CHAIN body outline spans x 132.97–138.69 (mouth edge 138.5). The arrow at x 140.7–142.1 points +x, out of the mouth. The pin-1 dot is at x 129.0–129.7, behind pin 1 (130.64), away from the mouth.
- **Top silk:** the pin-1 dot is at the same place. The arrow (133.0–134.4) points +x, over the header's body on the other side.
- Pin 1 is the square pad (unconnected, as are pins 1 and 2). Pin 3 is V3V3, pin 4 GND, pin 5 QH (/HOP_LH_LT), pin 7 SER, pin 9 SH/LD, pin 11 SCK, and every even pin is GND `[run: pads.py]`. `kicad.py check` holds these pins to the loom netlist.

**The MOUTH marker.** It is on both sides at the low-x edge (board x 97.7–99.0 plus text), next to SW-LH1, and the arrows point −x. Body x runs from the mouth and LH1 (body x 50) is the switch nearest it `[pcb-geometry.echo l.1; silk.py]`.

**Key names.**
- Top `LH1…LH5` each sit 7.8 mm on the pole side of their own switch (SW-LH1 at 110, 121.5 … SW-LH5 at 168, 112.5).
- Bottom `LHn` sit beside their own network `[silk.py; fsilk.png, bsilk.png viewed]`.
- **Mirroring:** bottom texts are mirrored and top texts are not (DRC mirrored-text tests pass).

**Title and revision.**
- The silk (both sides) reads "WOODY key board LH" / "rev A  2026-09-27". The title block reads title WOODY key board LH, rev A, date 2026-09-27. `layout.yaml` `silk:` agrees, and the job file carries Revision "A" `[run; fab/key-board-lh-job.gbrjob]`.
- The bottom title's right edge is at x 104 against H1 (100, 139.5; ring 1.1), which clears the screw head.

**Test pads.** Each label matches its pad's net:
- TP-3V3 is V3V3_CHAIN_LH.
- TP-GND is GND_CHAIN.
- TP-SCK is /CHAIN_SCK, which reaches U pin 2 (CLK).
- TP-SHLD is /CHAIN_SHLD, which reaches pin 1.
- TP-QH is /HOP_LH_LT, which reaches pin 9 (QH).
- TP-SER is /CHAIN_SER_LH, which reaches pin 10 (SER).
- The pads are Ø1.0 on B.Cu/B.Mask with no paste. The pin names come from `[SN74HCS165 p.3]` and the nets from `[run: pads.py]`.

**U-KEYS-LH pin 1 location.** The triangle is beside pin 1 (154.94, 108.97), correct apart from R3-2's via. The part is at rotation 90 on the bottom.

**Fab file set.**
- Nine Gerbers (both coppers, pastes, silks, masks, plus Edge.Cuts), PTH and NPTH drill, job file, pos, and the JLC BOM, CPL and hand list, as the README lists.
- I regenerated Gerbers, drills and pos in scratch with `pcb.py render`'s own `kicad-cli` arguments. All 13 match `fab/` apart from dates `[run]`.

**Drill files.**
- **PTH:** 37 × 0.30 vias, 12 × 0.70 (J-CHAIN) and 10 × 1.30 (switch pins).
- **NPTH:** 4 × 2.20 (standoffs) and 5 × 5.25 (switch poles).
- No copper flash on the NPTH holes (no 2.2 or 5.25 aperture in the F.Cu Gerber).
- Pad hole-to-hole on J-CHAIN is 1.27 − 0.70 = 0.57, at least the 0.45 required `[calc; CAPABILITIES p.4]`.

**Job file.**
- 2 layers, thickness 1.2, finish "HAL lead-free", mask Green ×2, legend White ×2, copper 0.035 (1 oz).
- The stackup sums to 1.11 + 2×0.035 + 2×0.01 = 1.20 `[calc]`.
- JLC Economic PCBA offers 1.2 mm in Green/Black with lead-free HASL, 2–30 pcs `[datasheets/fab/JLCPCB-PCBA-CAPABILITIES.pdf p.3]`.

**JLC BOM and CPL.**
- Both hold 18 machine parts: 5 C-KEY, 5 R-KEY-SER, 6 R-KEY-PU (including FREE3), C-DECOUPLE-165-LH and U-KEYS-LH.
- Every row has an LCSC number: C17408, C49678, C17520, C53134, C2864745. The CPL has 18 rows, all Bottom, with coordinates equal to `pos.csv`.
- C-BULK-CHAIN-LH (do not fit) is in neither file, and the footprint is excluded from pos.
- J-CHAIN and the five switches are on the hand list only.
- Rotations: resistors 90, capacitors 180, U 90, with bottom-side values as KiCad emits them. Whether JLC's bottom-side preview needs a correction for the SOIC cannot be settled from the banked guide, which credits corrections only to the Fabrication Toolkit `[datasheets/fab/JLCPCB-KICAD-BOM-CPL-GUIDE.pdf, Method 2]`. The README already makes the preview the check, and I have nothing to add beyond R3-2's physical mark.

**Board-house limits.**
- Track and space are 0.25 / 0.2 against JLC's 0.10 / 0.10.
- PTH-to-track is 0.28 (the minimum, 0.35 recommended; DRC holds 0.28).
- Copper-to-edge is 0.3 against 0.2.
- Silk-to-pad is 0.15, checked by `pcb.py`.
- The mask opening is 1:1, which JLC's LDI accepts `[JLCPCB-PCB-CAPABILITIES.pdf pp.5–7]`.
