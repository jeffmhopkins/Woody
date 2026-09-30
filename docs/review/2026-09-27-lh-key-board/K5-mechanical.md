# K5 — the left-hand key board in the body

**Slice:** K5, cold. **Revision measured:** `d46a3b0`. `tools/` was not changed. I read only this wave's README under `docs/review/`.
**Method:** I derived every figure below from the model's own variables, dumped by running a copy of `mechanical/cad/*` in the scratchpad (`probe.scad` includes `woody_body.scad` and echoes its internals). I then checked those figures by arithmetic against the banked prints. I read the prints by rendering them (`pdftoppm`, 400–500 dpi), because their dimension callouts are vector graphics.

**Runs:**
- `python3 tools/cad.py check` → `PASS 43 CAD outputs match their sources`.
- `python3 tools/pcb.py check hardware/boards/key-board-lh` → `0 error(s), 0 warning(s)`.
- `mechanical/clash.txt` → `CLASH 0`.

The generated files are current. The findings below are about what they derive.

## Summary

The board sits in the body as the model says. These all check out:
- the outline against the cavity;
- the corner standoffs against the switch positions;
- screw heads against underside parts;
- the 1.2 mm board against the KS-33 pin length;
- the header's envelope against the Samtec print.

The PCB agrees with `pcb-geometry.echo` to 0.05 mm. The assembly order in the board README can be carried out.

**The ribbon is where the model is wrong.**
- **The closed ribbon path starts from a misread of the FFSD print (K5-1, high).** The print shows that a socket's cable leaves on the *same* long side as its notch at the first connector, and on both connectors of an `-RN2` cable. So the main board's socket sends its cable **up**, not down onto the main board.
  - The stacked RA headers and `-RN2` then fit a *straight* cable between the two sockets. That is consistent, and it is probably why `-RN2` is needed at all.
  - It is not the hairpin the model draws: the main-board leg does not lie on the main board 1.05 mm above the thumb poles.
- **The service length is correct as a geometric path, but it is not what should be ordered.**
  - The FFSD order length is overall, outer face to outer face, in inches, ±0.125″ (K5-2).
  - The service position assumes the body lies flat on its bottom face. The U-bolt hangs 18 mm below that face (K5-3).
  - Together, these eat most or all of the 10 mm `routing.chain_slack`.
- **The plate window over J-CHAIN's tails is not needed.** The tails stand about 0.95 mm above the board top, under a 2.2 mm gap (K5-4).
- **Several derived texts did not follow `boards.key_board_t` (1.6 → 1.2) or the board growing to corner standoffs** (K5-8 to K5-11). The DRC's standoff-to-cutout rule is a drawing convention sitting 1.3 mm from the precision cutout (K5-5).

Coordinates are body millimetres: x along the body from the mouth, y across, z up from the bottom face.

These are the values the model derives, from `[run: openscad on a scratch copy, probe.scad]`:
- **Heights:**
  - Plate top 33.0, plate underside 31.8.
  - Key-board top 29.6, key-board underside 28.4.
  - Main-board top 11.0.
- **Chain headers:**
  - Mouth at x = 79.0, centred at y = 42.015.
  - Key plug centre z = 25.35; main plug centre z = 14.05.
- **Ribbon:**
  - `chain_z_low` 12.45, `chain_z_up` 22.325, fold radius 4.9375.
  - `chain_len` 86.27. The drawn closed path measures 85.83.
- **Board:**
  - `kb_rect` = [37, 7.5, 121, 49.5].
  - Standoffs at (40.5, 11), (40.5, 46), (117.5, 11) and (117.5, 46).
  - Tail window at [70.14, 37.84, 73.41, 46.19].

---

## Findings

### K5-1 [high] The FFSD cable leaves the main board's socket upward, not downward: the modelled hairpin and the rule written in four places misread the print

**Node:** `CBL-CHAIN`, `J-CHAIN` (main board), `chain_path()`, `chain_z_low`, drc.echo "key-chain ribbon closed: hairpin leg and fold radius".

**The claim.** The model (`woody_body.scad`, the comment above `chain_thumb_stub`), `key-chain-loom.md` §"Pin numbering" item 2, `hardware/bom.csv` `CBL-CHAIN` and `mechanical/DESIGN.md` §1 all say the same thing: *"An FFSD socket's cable leaves it on the long side away from its notch (sheet 1 fig 1)"*. From that, they conclude that both sockets' cables leave downward, and that the main board's leg lies on the main board `[repo]`.

**What the print shows.**

1. **Sheet 1, Fig 1 (standard `-N`), side view** `[datasheets/connectors/SAMTEC-FFSD-XX-X-XX.XX-01-PRINT.pdf, sheet 1 fig 1, rendered at 400 dpi]`.
   - Both sockets' polarisation keys (the 1.02 REF bumps labelled "-N OPTION") are on the drawing's **right-hand** long side.
   - The cable leaves the left (first) connector to the right, which is **toward its key**.
   - It enters the right (second) connector from the left, which is **away from its key**.
   - The plan view agrees: the second connector's 1.91-wide key is on the side away from the cable.
2. **Sheet 2, Fig 3, `-RN2` side view** `[same file, sheet 2, rendered at 500 dpi]`.
   - The first connector's key is on the cable side.
   - The second connector's key is reversed onto its cable side too. **With `-RN2`, both sockets' cables leave on the same side as their key.**

**Applied to the stack.** I take the loom page's own header orientation, which I confirmed on the SHF print:
- The main board's header slot is in the odd-row wall, away from the board (up).
- The key board's header is the same part upside down, so its slot is down.

`[datasheets/connectors/SAMTEC-SHF-1XX-01-X-D-XX-PRINT.pdf sheet 2 fig 2]`: the ribs and tails are on one face, and the key gap in the opposite wall is beside rows 01/03.

So:
- The main socket (first connector) is keyed up, and its cable leaves **up**.
- The key-board socket (second connector, reversed) is keyed down, and its cable leaves **down**.

The two sockets face each other across 8.25 mm `[calc: key plug underside 25.35 − 1.525 = 23.825; main plug top 14.05 + 1.525 = 15.575]`. An untwisted `-RN2` cable is therefore naturally a **straight vertical run between the two sockets**. This is self-consistent: a straight standard cable would bring the second connector keyed up into a slot that faces down, and `-RN2` is exactly what fixes that.

**What does not follow.** The model's lower leg at z = 12.45 is centred on the main board, 0.3 mm above the thumb poles `[calc: chain_thumb_stub = 5.75 − (3.4 + 1.6) + 0.3 = 1.05]`. To get there, the cable would have to be wrapped 180° around the back of the main socket. `chain_path()` draws it as if it already left that socket downward.

The correct stowed shape has the lower leg above the main socket, at about z ≈ 16.4. That changes:
- the fold radius, to about 2.9 `[calc: (22.325 − 16.4) / 2]`;
- the legs, to about 37.7 `[calc: (86.27 − ~1.5 − π·2.96) / 2]`;
- the main board's keep-out under the hairpin, which becomes about 4 mm of room instead of about 1 mm.

**Consequence for K2.** The loom page derives "key pin = 13 − main pin" partly from this rule. The map should be re-derived from sheet 2 Fig 3's first-position indicators and the headers' pin-1 positions, not from which way the cable leaves. I have not re-derived it; it is outside this slice.

**Fix:**
- Rewrite the rule as *"on an `-RN2` cable both sockets' cables leave on their key's side (sheet 1 fig 1, sheet 2 fig 3)"* in all four places. Edit the fragment `hardware/interfaces/key-chain-loom/bom.csv`, or whichever fragment owns `CBL-CHAIN`, not `hardware/bom.csv`.
- Redraw `chain_path()`: the main exit goes up, and the lower leg runs over the main socket.
- Re-derive `chain_z_low`/`chain_r`, and re-run the build.

### K5-2 [medium] "Order this length": the FFSD length is overall, outer face to outer face, in inches, ±0.125″ — ordering 86.27 mm leaves up to ~9 mm less free cable than the path needs

**Node:** drc.echo "key-chain ribbon length (derived)" (86.27); `CBL-CHAIN` "order that length or the next stock one up"; the board README step 3.

**What the print says** `[FFSD print, sheet 1 fig 1]`:
- The length dimension "XX.XX [XX.X × 25.4] ±1%" runs from the first socket's outer face to the second socket's outer face.
- Note 11: *"For lengths less than 12.5″, tolerance shall be ±.125"*.
- Each socket is 3.05 thick (".120 [3.05] REF").

**Why the numbers do not match.**
- `chain_len` runs from plug centre to plug centre (`chain_zm`, `chain_zk`).
- The free cable is therefore about `chain_len − 2 × 1.525`, and the overall order length about `chain_len + 3.05` = 89.3 mm `[calc]`.
- A buyer who orders 86.27 mm overall and gets the −3.175 tolerance ends up with free cable of 86.27 − 3.175 − 6.1 = 77.0 mm. The path needs 83.2 mm `[calc]`.
- That is 6.2 of the 10 mm `routing.chain_slack` gone before any twist or hand.

**Fix.** drc.echo should print the **order** length, in the unit it is ordered in: `chain_len + chain_plug_t + 3.175`, which is 92.5 mm ≈ 3.64″ at today's values `[calc]`. It should also say "overall, per FFSD print note 11". `CBL-CHAIN` and the README cite that line.

### K5-3 [medium] The service position puts the body flat on its bottom face, and the U-bolt stops it: the key plug ends up 11–23 mm lower relative to the main plug than the length assumes

**Node:** `routing.chain_service`, `chain_ks` / `chain_len` in `woody_body.scad`, `hardware.ubolt_drop`.

**The assumption.** `chain_len` maps the lid laid face down to (2W − y, T − z). That puts the lid's top face and the body's bottom face on one plane, z = 0 `[repo woody_body.scad "THE SERVICE LENGTH"]`.
- The lid can lie that way. Its keys are flush at full travel, so face down it rests on its oak face with the keys pressed.
- The body cannot. The strap U-bolt loop stands `hardware.ubolt_drop` = 18 mm below the bottom face, at x = 133 `[config/body.yaml; run: probe, ubolt_c = [133, 28.5]]`.

**What happens instead.** On a bench, the body rocks on the U-bolt with one end down.
- With the mouth end down, the bottom at the plugs (x ≈ 80) is 18 × 80/133 ≈ 10.8 mm up.
- With the tail end down (x_in1 = 319.6), it is 18 × (1 + 53/186.6) ≈ 23 mm up `[calc]`.
- Either way that exceeds the 10 mm `chain_slack`, on top of K5-2.

`ubolt_drop` is a tbd placeholder, but any strap loop below the face has this effect.

**Fix.** Say how the body is supported in the service position (on a block, on its side, or the lid propped), and include that height in `chain_len`. Alternatively, add `max(0, ubolt_drop)` to the lid-side drop. The README's step 3 should then say how the body is supported.

### K5-4 [low] The plate window over J-CHAIN's tails is not needed: the tails stand ~0.95 mm above the board top under a 2.2 mm gap

**Node:** `chain_tail_rect()`, `mechanical/export/plate-top.dxf` window [64.14–67.41, 31.84–40.19] in the plate frame; `J-CHAIN` BOM row; board README step 1.

**The tail length.** The SHF print, sheet 2, section C-C, gives the tails **.085 [2.15] REF** beyond the header's seating face `[datasheets/connectors/SAMTEC-SHF-1XX-01-X-D-XX-PRINT.pdf sheet 2 C-C, rendered 400 dpi]`. I scaled a check: 136 px at 62.95 px/mm = 2.16 mm `[calc]`.

**The clearance.**
- Through the 1.2 mm board, the tails stand 2.15 − 1.2 = **0.95 mm** above the board top.
- If 2.15 were measured from the body face rather than the 0.51 ribs, they would stand 0.44 mm.
- The plate-to-board gap is `kb_gap` = 2.2 `[calc: 3.4 − 1.2]`. That leaves 1.25 mm of air to the grounded plate, before a solder fillet.
- 1.25 mm of air is ample at 3.3 V [from memory: IPC-2221 B1 is 0.1 mm for 0–15 V].

**Why this matters.** The model's own comment, *"it is grounded, and the gap is 2.2 mm: a window through the plate"*, does not show that the gap is short. The window costs:
- a 3.27 × 8.35 mm hole;
- a 2.34 mm web to LH2's cutout `[calc: 37.84 − 35.5]`;
- a claim repeated in `DESIGN.md`, `J-CHAIN`'s row and the README.

**Fix.**
- Delete the window.
- If it is kept, state the reason with the 0.95 mm tail figure. `boards.chain_hdr_*` should gain a `chain_hdr_tail` value of 2.15 from the print, so that a DRC can compare tail height with `kb_gap`.
- The README's "so they need no trimming" is true without the window.

### K5-5 [medium] The standoff hole sits 1.3 mm from LH4's cutout, the build's precision feature; "key-board standoffs in the plate's web" passes on a drawing convention, not on the clinch vendor's edge distance

**Node:** `kb_standoffs("left_hand")[2]` (117.5, 11) and `[3]`; drc "key-board standoffs in the plate's web" 0.915; `kb_web_min` = 0.5 (drawing convention); `hardware.kb_standoff_hole` 3.2 (tbd); `MECH-KB-STANDOFF`.

**The distances** `[calc]`:
- From the standoff centre to LH4's cutout corner (115, 12.5): √(2.5² + 1.5²) = 2.915. This is confirmed in `plate-top.dxf`: the nearest point to the (111.5, 5) hole is 2.915 away `[run]`.
- From the hole's edge: 2.915 − 1.6 = **1.3 mm of aluminium**.

**Why that is a problem.**
- The cutout is 14.00 +0.05/−0.02 `[repo docs/reference/ks33-geometry.md, citing the vendor drawing]`.
- A self-clinching standoff displaces sheet metal into its shank. Vendors specify a minimum distance from hole centreline to edge, typically several millimetres for M2–M3 [from memory; not banked].
- A cutout edge 1.3 mm from a clinched hole can be pulled out of a −0.02 tolerance.
- The DRC's 0.5 mm is `kb_web_min`, "drawing convention" `[repo woody_body.scad]`, measured from the barrel (OD 4.0, itself from memory), not from the hole.

The right-hand board has the same geometry at RH6 (drc worst case 0.915).

**Fix.**
- Make `kb_web_min` the vendor's centreline-to-edge figure, measured from the hole, once the standoff is chosen. Mark it tbd until then, and do not print PASS.
- Alternatively, move the standoffs off the LH4/LH5 and RH6 corners by raising `boards.kb_end_margin`: at 8, the standoff is 4.5 mm from LH4's cutout in x `[calc]`.

### K5-6 [low] "Buy standoffs this long: 2.2" states a point where the pins allow a window of 2.0–2.4; and pcb-geometry.echo's standoff line puts a different 2.2 first

**Node:** drc.echo "key-board standoff length (derived)"; `MECH-KB-STANDOFF` ("buy that length, not a round number"); `pcb-geometry.echo` `"standoff", "M2", x, y, 2.2, 3.8, 4`.

**The window.** The pins' narrow blade runs 3.2 → 5.10 below the seat, so the board top may sit 3.2–3.6 below it `[repo ks33-geometry.md]`. Less the 1.20 plate, that is a gap of **2.0–2.4** `[calc]`.
- At 2.0, the pins show 0.7 mm below the board.
- At 2.4, they show 0.3 mm `[calc: 5.10 − top − 1.2]`.

ADR 0020 already says a clinch standoff this short may not be stocked. Clinch standoff lengths come in whole millimetres [from memory]. The window, not the point, is what the plate vendor needs.

**The echo line.** `pcb-geometry.echo`'s standoff line gives the screw hole (`hardware.kb_screw_hole`, 2.2) first. That is numerically equal to the standoff length, so a reader can take one for the other `[repo woody_body.scad pcb_geometry()]`.

**Fix.**
- Print "2.2 (2.0–2.4 keeps the pins in their blade and ≥ 0.3 mm to solder)".
- Label the echo fields, or print them as `hole=…`.

### K5-7 [low] MECH-KB-SCREW's length rule covers only a blind standoff; with a through standoff (which the row allows) a screw over 4.6 mm lifts the oak top

**Node:** `MECH-KB-SCREW`, `MECH-KB-STANDOFF` ("blind or through").

From under the screw head to the plate's top face is 1.2 + 2.2 + 1.2 = **4.6 mm** `[calc: board + gap + plate]`. The oak top rests on that face `[repo woody_body.scad, stack]`.
- With a through standoff, an M2×5 stands 0.4 mm into the oak top's underside `[calc]`.
- The row only says "short of the standoff's blind end".

**Fix.** Add "≤ 4.6 under the head with a through standoff (M2×4 [from memory: stock lengths 3, 4, 5])", derived in drc.echo beside the standoff length.

### K5-8 [low] clash-allow.yaml still says the switch pins and pole stand "0.75 mm proud of the cluster board" — that is the 1.6 mm board's figure

**Node:** `mechanical/clash-allow.yaml` line 41; `clash.txt` "parts left_hand × switch LH1..LH5".

On the 1.2 mm board the underside is 3.4 + 1.2 = 4.6 below the seat, so `[calc]`:
- the pole stands out 5.75 − 4.6 = **1.15** (vendor), or 1.10 on the STEP mesh the clash check uses;
- the pins stand out 5.10 − 4.6 = **0.5**.

0.75 is 5.75 − (3.4 + 1.6). That is `key_board_t` moving and a derived sentence not following. Both figures are still inside `boards.cluster_smt_h` 1.8, so the allowance itself is right.

**Fix.** Reword the reason to name the parameters, not a number: "stand proud by `switch.pole_tip_below_seat − switch.pcb_below_seat − boards.key_board_t`".

### K5-9 [low] `switch.pcb_t` (1.6, "settled") cites `PCB-CLUSTER` at 1.6, which is now 1.2; at 1.6 the thumb switches get the same 0.1 mm of pin that ADR 0020 moved the key boards off

**Node:** `config/body.yaml` `switch.pcb_t` (source "[adr] hardware/bom.csv PCB-CLUSTER and PCB-CARRIER, 1.6 mm"); `chain_thumb_stub`; `thumb_z`.

`PCB-CLUSTER` now reads 1.2 mm `[repo hardware/bom.csv]`. `switch.pcb_t` is used only for the main board now (`cb_z`, `thumb_z`, `chain_thumb_stub`).
- On it, the thumb pins show 5.10 − 3.4 − 1.6 = **0.1 mm** `[calc]`.
- ADR 0020 point 6 says this "is decided when the main board is laid out". A leaf marked `settled` with a stale citation hides that.

**Fix.**
- Cite only `PCB-CARRIER`.
- Mark it `nominal`, `decided_by` "M4 main board layout (ADR 0020 point 6)".
- Consider renaming it `boards.main_board_t`.

### K5-10 [low] Two definitions of where a key board ends: `kspan()`/`board_lead` use `cluster_margin` 4, the board itself uses `kb_end_margin` 6

**Node:** `kspan()`, `board_lead`, `gap_x`, `gap_room`, drc "main board parts room where no key board is overhead"; `kb_rect()`.

The difference `[calc]`:
- `kspan("left_hand")[1]` = 108 + 7 + 4 = 119, so `gap_x` starts at 120.5.
- The left-hand board actually ends at 121 `[run: probe, kb_rect = [37, 7.5, 121, 49.5]]`.
- The right-hand board starts at 145, while `gap_x` ends at 145.5 `[run: probe]`.

The "nothing overhead" band (19.3 mm of room, up to the plate) therefore reaches 0.5 mm under each board, with the 1.5 mm `board_clear` gone. At the mouth end, `board_lead` = 11 puts the first board's edge at x = 39 for the breath-trap budget; the board starts at 37.

`clash.txt` is `CLASH 0`, so nothing collides today. But the DRC approximations (`under_keys`, `gap_room`, `tall_room`) measure a board that is 2 mm shorter at each end than the one being built. The board grew under ADR 0020's amendment, and these did not follow.

**Fix.** Derive `kspan()` and `board_lead` from `kb_rect()`, or both from one margin.

### K5-11 [low] ADR 0020 point 3 and the model's comment say the PCB carries a rule area where the ribbon runs; it does not, and no longer needs one

**Node:** `docs/decisions/0020-key-boards-screw-to-the-plate.md` point 3 ("the PCB carries it as a rule area"); the `woody_body.scad` comment above `kb_chain_rect()`; `tools/pcb.py` `no_parts()`.

- `pcb.py` makes that zone only from a `"ribbon"` line in `pcb-geometry.echo`, and `pcb_geometry()` emits none `[repo]`.
- The board has six zones: two `GND_CHAIN` pours and four standoff keep-outs, and no ribbon area `[run: zone list parsed from key-board-lh.kicad_pcb]`.
- The ribbon's upper leg runs at z ≤ 22.725, 3.9 mm below the key board's parts at 26.6 `[calc]`, so no area is needed.

**Fix.** Delete the sentence from the ADR point and the comment. The ADR's amendment line ("the no-parts strip is under the header, its plug and the ribbon's hairpin") describes the model's parts envelope, not the PCB.

### K5-12 [advisory] body.yaml says the Samtec full prints are "not (403)"; both are banked

**Node:** `config/body.yaml` comment above `boards.chain_hdr_l` (line 341); several `decided_by: "M4, with the full print"`.

`datasheets/MANIFEST.csv` rows for `SAMTEC-SHF-1XX-01-X-D-XX-PRINT.pdf` and `SAMTEC-FFSD-XX-X-XX.XX-01-PRINT.pdf` are status OK, and the leaves beneath the comment cite them `[repo]`. What is still missing is the STEP model (MANIFEST row, BLOCKED).

**Fix.** Update the comment. Change `decided_by` to "M4, with the part in hand".

### K5-13 [advisory] `boards.cluster_smt_h` cites the SOIC-16 height "from memory"; the banked Nexperia datasheet gives it

**Node:** `boards.cluster_smt_h` (1.8), `U-KEYS-LH`.

`datasheets/logic/74HC165-nexperia.pdf`, Fig. 11, SOT109-1 table: **A max 1.75** `[datasheet]`. The value is correct. The provenance can be `[ds]`, and the margin is 0.05 mm.

Nothing else on the underside comes near it `[run: footprint list, key-board-lh.kicad_pcb]`:
- 0805s;
- 1.0 mm test pads;
- screw heads at 1.6;
- pins at 0.5;
- poles at 1.15.

J-CHAIN (5.59) is modelled separately.

### K5-14 [advisory] `chain_plug_proud` decides whether the cable clears the shroud at all, not just the fold

**Node:** `boards.chain_plug_proud` (1.4, tbd); `chain_exit()`.

Scaled off the FFSD print, sheet 1 fig 1 side view `[datasheet, scaled — "do not scale"]`:
- the cable lies 0.74–1.37 mm in from the socket's back face;
- the part of the socket that enters the header (the keyed lower body) is about 3.2 mm long.

At a stand-out of 1.39 `[calc: 5.08 − 3.69; pocket depth 3.69 scaled off SHF C-C at 62.95 px/mm, matching body.yaml's "about 3.67"]`, the cable clears the shroud's mouth by about 0.02 mm. The model starts the cable at the socket's back face. In reality it leaves about 1 mm inside that face, on the long side.

**Fix.** At M4, measure both the stand-out and the cable's exit line on the mated pair. Add a DRC that the exit clears the mouth.

### K5-15 [advisory] The board README says the outline DXF has "four M2 holes"; it has only the outline

**Node:** `hardware/boards/key-board-lh/README.md` ("Outline … `mechanical/export/key-board-lh.dxf`: rounded corners, four M2 holes").

`key-board-lh.dxf` has 88 vertices, none inside the board `[run: parsed]`. `key_board_2d()` draws no holes `[repo]`. The holes are `MountingHole_2.2mm_M2` footprints placed from `pcb-geometry.echo`, and `pcb.py check` confirms them.

**Fix.** "The outline from `key-board-lh.dxf`; the four M2 holes from `pcb-geometry.echo`."

### K5-16 [advisory] J-CHAIN's 0.65 mm drills for 0.41 mm square tails

**Node:** `hardware/lib/woody.pretty/IDC-Header_2x06_P1.27mm_Samtec_SHF_Horizontal.kicad_mod`.

- The tail is ".016 [0.41] SQ" `[SHF print sheet 1]`, with a diagonal of 0.58 `[calc]`.
- The 0.65 drill leaves 0.07 mm of diametral clearance, for 12 right-angle tails with a 2° allowed sway `[SHF print sheet 2]`, inserted by hand.
- The drill is KiCad's generic `PinHeader_2x06_P1.27mm` value. Samtec's recommended hole is not banked; I recall it as about 0.7 [from memory].

K3/K4 may own this. It affects step 1 of the hand assembly.

---

## Checked and found correct

| Checked | Result, with provenance |
|---|---|
| Board outline vs cavity | 37–121 × 7.5–49.5; inside faces of the sides at y = 6/51, so 1.5 mm each side = `boards.board_clear` `[run: probe; calc]` |
| Board vs lid screws | Nearest M3 for the left hand is at (133, ·): 133 − 121 − 1.5 = 10.5 mm. The drc's 1.8 is the right-hand board's (250.3 − 247 − 1.5) `[calc]` |
| Standoff length = plate-to-board gap | `kb_gap` = 3.4 − 1.2 = 2.2; the standoff runs 29.6 → 31.8, touching both, with no clash `[calc; clash.txt]` |
| Standoffs in plate metal | Hole ⌀3.2 at all four positions in `plate-top.dxf` `[run: parsed]`. Plate edge at y = 6.2, so 4.8 mm from the standoff at y = 11 `[calc]` (but see K5-5) |
| Screw heads vs underside parts | Head ⌀3.8 × 1.6 (z 26.8–28.4), inside the 1.8 envelope. The nearest part to H4 is R-KEY-PU-LH5, 9 mm centre to centre. PCB keep-out radius 2.2 = max(3.8, 4.0)/2 + 0.2 `[run: kicad_pcb zones; calc]`. drc 28.24 to the header ✓ |
| 1.2 mm board and pin protrusion | Pins end 5.10 below the seat; board 3.4 + 1.2 = 4.6, so 0.5 mm to solder (1.6 would give 0.1) `[repo ks33-geometry.md; calc]`. The blade's shoulder at 3.2 is above the board top at 3.4. The housing bottom at 2.5 clears the board top by 0.9 |
| Header envelope vs print | Length 13.97 = 6 × 1.27 + 6.35 (sheet 1). Height 5.59 includes the 0.51 ribs (sheet 1 fig 1). Depth 5.33, tail rows 1.26 and 2.53 behind the back face, so `chain_hdr_pin_back` 7.86 (sheet 2 C-C). Mouth centre 3.05 = 0.51 + 2.54 (C-C scaled: 191.5 px = 3.04 mm) `[datasheet; calc]` |
| Plug envelope | Plug 5.08 × 11.81 (6 × 1.27 + 4.19) × 3.05; ribbon 12 × 0.635 = 7.62 `[FFSD print sheet 1; calc]` |
| Footprint vs model | J-CHAIN fab body back = pad 2 + 1.26, mouth = pad 1 + 7.86; courtyard to 9.51 = 7.86 + 1.4 + 0.25 `[repo .kicad_mod]`. Pads centred at x = 71.775 = 79 − (7.86 − 0.635) `[calc]` |
| Switch/standoff/header positions vs `pcb-geometry.echo` | `pcb.py check`: 0 errors. By hand, PCB = (x + 60, 150 − y); LH1..LH5, H1..H4 and U-KEYS-LH all map `[run]`. Edge.Cuts 97–181 × 100.5–142.5 = DXF 37–121 × 7.5–49.5 `[run]` |
| Header clear of switches | Tail window/rows at y ≥ 37.84, LH2's cutout ends at 35.5; drc "chain headers … clear" 79 ✓ `[calc]` |
| Legs vs parts, as modelled | Upper leg top 22.725 vs key-board parts at 26.6 (3.9 mm). LH5 pole tip at 27.25. Main-board J-CHAIN top 16.59 vs key header bottom 22.81. Hairpin 80.4–120.73 inside the board's 121 and clear of the U-bolt at 133 and the M3 at 133 `[calc]`. Main-board parts envelope excludes the hairpin band `[repo centre_board_3d]` |
| Fold radius | 4.94 mm, far above what 30 AWG flat cable needs [from memory]. The corrected shape in K5-1 gives ~3 mm, still fine |
| Service path geometry | 22.95 + 14.985 + 23.35 + 14.985 + 10 = 86.27 `[calc]`. Flipping the lid about an x-parallel axis at the far edge keeps both hands' plugs at their x. The two 90° twists the ribbon needs, to cross the edge with its width along y, fit in the ~22 mm rises [calc: an edge conductor over 20 mm is lengthened by ~0.9 mm]. Laying the lid off the far side is the short way (chain_y 15 mm from that edge) |
| Parts envelope vs tallest part | SOIC-16 A max 1.75 ≤ 1.8 (K5-13) |
| README assembly order | Feasible. J-CHAIN goes first, because its tails are soldered from the top and the top is inaccessible once the board is on the plate. Next, clip the switches in, lower the board onto the pins and standoffs (the board is located only by the standoffs, 0.9 mm below the housings), screw from below, then solder the pins from below: the J-CHAIN body and SMT parts do not block any switch pin `[calc: nearest pin (72.6, 22.75) vs header y ≥ 35.03]`. The plugs are reachable in the service position. Caveats: K5-5 (clinching before the switches go in), K5-7 (screw length), K5-3 (how the body is supported) |

**Not checked:**
- the KS-33 vendor sheet itself. I cite `ks33-geometry.md`'s reading of it (pins end 5.10, pole 5.75);
- the right-hand board's own layout;
- the Matrix ribbon, which also leaves the lid, in the service position.
