# R2 — The key board's standoff, washer, screw and depth

**Slice:** R2 of wave `2026-09-27-lh-key-board-r2`. **Revision measured:** `eebcdfb`
(HEAD `36341bf`, which adds only the wave README), working tree clean.
**Tools:** run as frozen, nothing rebuilt into the repository. Experiments ran
on a `git archive` copy in the scratchpad.
**Cold:** nothing under `docs/review/` read except this wave's README.

**Fact domain:** how a key board is held to the key plate, and at what depth.
That covers PEM MSO4-M2-3, the ISO 7092 washer, the M2 screw,
`switch.pcb_below_seat` / `_window` / `thumb_pcb_below_seat`, the depth rules
and the tolerance stack, the owner's fallback, the BOM rows `MECH-KB-*`, the
assembly steps, and the PCB keep-out.

## Re-derivation (the numbers every finding below uses)

| Quantity | Value | Provenance |
|---|---|---|
| MSO4-M2: hole 3.18 +0.05, C max 3.16, H nom 3.96, L 2 or 3 (+0.05/−0.08), min sheet 0.3, C/L to edge 3 | — | [datasheets/mechanical/PEM-MPF-MICROPEM-FASTENERS.pdf p5 (MPF-5), rendered at 150 dpi] |
| L is overall, head included. The bore is threaded the full length (through-threaded) | — | [same, p5 drawing] |
| "apply only enough squeezing force to embed the head of the standoff flush in the sheet" | — | [same PDF, p16 (MPF-16), MSO4 installation step 3]. **Not on p5** |
| MSO4 for sheet hardness HRB 88 / HB 183 or less. 400 series stainless | — | [same PDF, p14 table] |
| Washer ISO 7092 / DIN 433 M2: ID 2.2–2.34, OD 4.2–4.5, t 0.25–0.35 (0.3 nom) | — | [web https://www.aspenfasteners.com/m2-din-433-iso-7092-metric-flat-washers-small-outside-diameter-a2-stainless-steel/, fetched 2026-09-27] |
| Board-top depth, nominal | 3.0 + 0.3 = **3.30** | [calc] |
| Board-top depth, limits | 3 − 0.08 + 0.25 = **3.17**; 3 + 0.05 + 0.35 = **3.40** | [calc], matches [mechanical/drc.echo:66] |
| Window | [3.2, 3.6]. Its middle is **3.4** | [config/body.yaml switch.pcb_below_seat_window] |
| Standoff barrel below a 1.2 plate | 3 − 1.2 = **1.8**. The model draws `kb_gap − washer` = 2.1 − 0.3 = 1.8 | [calc]; [mechanical/cad/woody_body.scad:683-684] |
| Pin shown below the board, nominal | 5.10 − 3.30 − 1.2 = **0.60** | [calc]; 5.10 from [docs/reference/ks33-geometry.md] |
| Pin shown below the board, worst | 5.10 − 3.40 − 1.32 = **0.38** (board 1.2 ±10 % [from memory, typical board-house tolerance]) | [calc] |
| Screw M2×4 (ISO 4762 length 3.76–4.24, dk 3.80, k 2.00) | — | [web https://www.fasteners.eu/standards/ISO/4762/] |
| Screw tip above the standoff's lower end, nominal | 4 − 1.2 − 0.3 = 2.5. So it stops **0.5** below the plate's top face | [calc] |
| Screw tip, worst long | 4.24 − 1.08 − 0.25 = 2.91, against a standoff of L min 2.92. It stops **0.01** below the top face | [calc] |
| Thread engaged, worst short | 3.76 − 1.32 − 0.35 = **2.09 mm** ≈ 5.2 pitches of 0.4 ≈ 1.05 D | [calc] |

`[run: python3 tools/cad.py check]` → `PASS 43 CAD outputs match their sources`.

drc.echo lines 61–69 read `[run: grep]`:
- (derived) 2.1
- window [2, 2.4]
- cutouts PASS 3.60555
- depth PASS 3.3
- window PASS [3.3,[3.2,3.6]]
- tolerance NOTE [3.17, 3.4] "…starts 0.03 mm into the hole"
- standoffs [4,4]
- lid screws PASS 3
- chain header PASS 17.24

J-CHAIN tails PASS 1.15 [mechanical/drc.echo:54]. clash.txt has `CLASH 0` and no allow rule that names a standoff, washer or screw [mechanical/clash.txt; mechanical/clash-allow.yaml].

---

## Findings

### R2-1 [medium] "Standoff length (derived)" = 2.1 is still presented as the standoff's length, and the part is 3 mm

**Node:** `MECH-KB-STANDOFF` / `hardware.kb_standoff_l` / drc.echo "key-board standoff length (derived)".

**Evidence:** the standoff is MSO4-M2-3. Its length is 3 overall, head flush in the top face, which leaves 1.8 below the plate [calc above]. These places still say or print that the standoff's length is derived from the gap, and the gap is 2.1:
- `mechanical/drc.echo:61` prints `"key-board standoff length (derived)", 2.1`. Line 62 prints `"key-board standoff length window", [2, 2.4]` and calls them "the lengths that keep the switch pins' blades in the board". The scad source is `woody_body.scad:1364-1370`.
- `hardware/cluster/cluster-boards.md:172-174`: "the standoff length is derived as `mechanical/drc.echo` "key-board standoff length (derived)", and it is the standoff below the plate plus its washer". The standoff below the plate plus its washer is 1.8 + 0.3 = 2.1, so the sentence is arithmetically true of the gap. It still names the result "the standoff length".
- `mechanical/DESIGN.md:42`: "the standoff's length is derived (*"key-board standoff length (derived)"*)".
- `config/body.yaml:731-736` (the `hardware:` comment block): "The standoff's length is not a parameter: it is the plate-to-board gap…". It also says MSO4 "is a candidate, not a choice". Both are now false: `kb_standoff_l` is a parameter, and the part is the owner's choice (ADR 0020, *Consequences*).
- `mechanical/cad/woody_body.scad:649-651` ("Its length is the gap the switch pins set") and `:1364-1366` (the same).
- ADR 0020 point 2, last bullet: "The model prints it as … "key-board standoff length (derived)", and the BOM row cites that line". The amendment note above that bullet reverses the derivation but leaves this bullet standing. `MECH-KB-STANDOFF` no longer cites the line; only `MECH-KB-SCREW` does, and it uses the line correctly, as a gap.

**Why medium:** MSO4-M2-**2** is a stocked part [PDF p5]. A reader who takes "standoff length = 2.1" and rounds to the nearest stocked length gets a board top at 2 + 0.3 = 2.3 below the seat [calc]. That is 0.9 shallower than the window. The pins' 2.0 mm root cannot enter a 1.2 mm hole there, so the board could not be fitted at all.

**Fix:** rename the INFO lines to what they print, for example "key-board plate-to-board gap" and "…gap window". Rewrite the five prose sites to say the standoff is chosen (`hardware.kb_standoff_l`) and the gap follows from it. Delete the stale `body.yaml` comment sentences. Add a `forbidden` pattern for "standoff length is derived" / "standoff's length is derived" (rule 2).

### R2-2 [medium] The copper keep-out leaves 0.19 mm round the washer, less than the washer's own float on the screw

**Node:** H1–H4 on `key-board-lh`; `GND_CHAIN` pour on F.Cu; `hardware.kb_washer_od`.

**Evidence:**
- The keep-out radius is `max(head, od)/2 + rules.clearance` = 4.5/2 + 0.2 = 2.45 [tools/pcb.py:682; hardware/boards/key-board-lh/layout.yaml:19].
- It is drawn as a 32-gon, so its flats are at 2.438 [run: pcbnew 9.0.9 script over key-board-lh.kicad_pcb in scratch]. The filled `GND_CHAIN` pour on F.Cu and B.Cu reaches **2.438 mm** from every hole centre [same run].
- The washer's radius is 2.25. Its position is not controlled to 0.19 mm:
  - The washer can move on the screw by (2.34 − 1.886)/2 ≈ 0.23. The washer's ID range is from the web source above; the M2 6g major diameter minimum of 1.886 is [from memory].
  - The screw can move in the 2.2 NPTH hole by about (2.25 − 1.886)/2 ≈ 0.18 [calc; drill +0.05 from memory].
  - Worst case, the washer edge lands at about 2.25 + 0.41 = 2.66 from the hole centre. That is about **0.22 mm over** the pour [calc].
- The steel washer is at plate potential (plate → standoff → washer) and is clamped onto solder mask over `GND_CHAIN` copper. ADR 0020 point 4 says "No track, via or pour reaches the standoff or the screw head". Only the mask then separates the plate from `GND_CHAIN`, which is the second ground bond the ADR rejects.
- The underside is fine: the head radius is 1.9, and with the 0.18 screw float that is ≤ 2.08 < 2.438 [calc].

**Fix:** size the keep-out from the washer's worst position rather than from track clearance. For example, give `pcb_geometry()` a float allowance: washer OD/2 + (washer ID max − screw major min)/2 + (hole − screw)/2 + clearance ≈ 2.25 + 0.23 + 0.18 + 0.2 ≈ 2.9 mm radius. Check that 2.9 still clears the board edge: the inset is 3.0, and `edge_clearance` needs no copper there anyway. Alternatively, ask for a washer with a tighter bore. This needs a `tools/` change, so it waits for the freeze to lift.

### R2-3 [medium] The owner's fallback (nut in an oak pocket) does not fit the model it claims to share

**Node:** ADR 0020 *Consequences*, fallback bullet; `MECH-KB-STANDOFF` notes; `MECH-KB-SCREW`.

**Evidence:**
1. **The oak pocket breaks into the cap slot at three of the eight positions.** In the scratch copy, the distance from each standoff centre to the oak top's cap slot (`keys_2d`, keycap + 2 × `stack_cap_clear` = 18.0) is **1.0 mm** at left_hand (118, 10.5), left_hand (118, 46.5) and right_hand (244, 10.5) [run: openscad `part="pcb_geom"` with an appended echo, scratch `r2.echo`]. An M2 nut (ISO 4032, 4 AF, corner radius 2.31 [from memory]) in a pocket centred there opens ≥ 1.3 mm into the slot the cap travels in [calc: 2.31 − 1.0]. The distance to the 16.5 cap's own outline is about 2.2 [calc: collar gap 2.915 − 0.75], so the nut's corners also sit under the cap's skirt. Whether the cap reaches 1.6 mm above the plate at full travel depends on the cap height, which is unpublished (`switch.keycap_top_above_seat` tbd). **Open.**
2. **The screw in the BOM cannot be used.** The fallback stack is board 1.2 + washer 0.3 + spacer 1.8 + plate 1.2 + nut 1.6 = 6.1 [calc]. M2×6 falls short of the nut's top, so the fallback needs M2×8. `MECH-KB-SCREW` and README step 2 name only M2×4.
3. **Plate thickness enters the depth again.** The fallback depth is plate + spacer + washer. So `plate-thickness` (1.20 ±0.05) returns to the stack that the MSO4's flush head removed ("whatever the plate's thickness"). The rule "key-board standoff and washer set the board depth" checks `kb_standoff_l + kb_washer_t`, so it would still PASS on hardware that is not fitted.
4. **The plate DXF would be wrong.** It cuts `kb_standoff_hole` = 3.2 [woody_body.scad:354]. The fallback needs an M2 clearance hole. The earlier bullet in the same ADR still says "The CAD geometry is the same either way". It is marked replaced, but nothing says the geometry now differs.

**Fix:**
- State the fallback's spacer length (1.8, = `kb_standoff_l − plate-thickness`), its screw (M2×8), and its plate hole.
- Before it is ever selected, move the three corner standoffs, or accept that the pocket joins the cap slot and check the cap's travel.
- Put a `hardware.kb_mount: clinch|nut` switch in the model so that the depth rule and the plate hole follow what is fitted.
- Note in `switch.pcb_below_seat` (status `settled`) that it is settled only for the clinch option.

### R2-4 [low] The screw is specified in a standard that has no M2, and its length is checked by nothing

**Node:** `MECH-KB-SCREW`; `hardware.kb_screw_head_d`, `kb_screw_head_h`.

**Evidence:**
- **The standard:** DIN 7984's dimension table starts at M3 (dk 5.5, k 2.0) [web https://www.fasteners.eu/standards/din/7984/]. The row's "M2 low-head cap screw (DIN 7984)" therefore names a part that standard does not define. The head sizes 3.8 × 1.6 are `[from memory]` in body.yaml. The standard M2 socket cap screw is ISO 4762, dk 3.80 and k **2.00** [web https://www.fasteners.eu/standards/ISO/4762/]. The 3.8 is right; the 1.6 is not for any named standard. Nothing clashes at 2.0: the key board to main board gap is 17.5 [drc.echo:58].
- **The length:** the screw's length is not a parameter. The model draws only the head [woody_body.scad:685-686], so clash.txt cannot see a tip that stands proud. The BOM row's formula gives 1.2 + 2.1 + 1.2 = 4.5 ≥ 4 [calc], which holds at nominal. At worst case the tip stops 0.01 mm below the top face [re-derivation table]. The margin is zero, and it is not checked.
- **Where a proud tip would land:** at the three positions in R2-3 the standoff head sits 1.0 mm from the cap slot, so a proud tip would stand in the slot rather than against the oak.

**Fix:**
- Name the screw ISO 4762 M2×4 (or an ISO 14580/7045 pan head, whose sizes should be read off a banked source), and set `kb_screw_head_h` from it.
- Add `hardware.kb_screw_l` (with its tolerance) and a DRC rule: tip below the plate's top face at the long limit, and engagement ≥ 1 D at the short limit.
- Model the shank so clash sees it.

### R2-5 [low] Depth 3.4 survives in the pin-protrusion figure and in the window's own source text

**Node:** `switch.pcb_below_seat_window`; `boards.key_board_t`; ADR 0020 point 6.

**Evidence:**
- `config/body.yaml:270`, window source: "pcb_below_seat is its middle". The window's middle is 3.4; `pcb_below_seat` is 3.3.
- These three places say "about 0.5 mm" of pin shows below a 1.2 mm board. That figure is 5.10 − **3.4** − 1.2 [docs/reference/ks33-geometry.md:112-113]. At the key boards' depth it is 0.6 [calc].
  - ADR 0020 point 6: "on 1.2 mm about 0.5 mm".
  - `config/body.yaml:448`, `boards.key_board_t` source: "1.2 mm ~0.5 mm".
  - `docs/reference/tooling.md:392`: "leaves about 0.5 mm".
- `ks33-geometry.md` itself gets this right ("a little higher than the middle, so they show a little more pin").
- `thumb_pcb_below_seat` = 3.4 is correctly the window's middle, and it is correctly separate [body.yaml:235-239].

**Fix:** change the window source to "the band … `pcb_below_seat` sits inside it". Change the three "about 0.5 mm" sites to cite `ks33-geometry.md` instead of restating it (rule 1), or to state 0.6 at `switch.pcb_below_seat`. Add a forbidden pattern for "is its middle".

### R2-6 [low] ADR 0020's own text still describes the pre-washer hardware in three places

**Node:** ADR 0020 points 2 and 4, and *Consequences*.

**Evidence:**
- Point 4: "On top it is covered by the standoff's end face", and "`tools/pcb.py` places the keep-out from the CAD's standoff diameter and screw head". Now the washer covers the top, and the keep-out uses `max(standoff od, washer od)` [woody_body.scad:699-701; pcb-geometry.echo lines 7-10, last field 4.5]. The same stale sentence is in the comment at `tools/pcb.py:677` ("The standoff's end face presses on the top copper"). The code is right; its comment is not.
- *Consequences*, the bullet at line 149: "`drc.echo` "key-board standoff stocked lengths against the window" prints both and the shim". No such line exists [run: grep over the repository, excluding docs/review → only ADR 0020:149].
- Point 2's BOM citation: see R2-1.

**Fix:** amend point 4 to say "the washer (`MECH-KB-WASHER`)". Strike or annotate the non-existent drc line as withdrawn. Fix the pcb.py comment after the freeze.

### R2-7 [low] "The washer lifts the board" gets the direction wrong

**Node:** `MECH-KB-WASHER`; `hardware.kb_washer_t`.

**Evidence:**
- The row's notes say "It lifts the board from the 3 mm standoff's reach into the switch pins' window" [hardware/unplaced.csv:26]. `body.yaml:764` says "it lifts the board from the 3 mm standoff's 1.8 below the plate into the pins' window".
- In fact the board hangs under the plate. The washer moves the board top from 3.0 to 3.3 below the seat [calc], which is further from the plate, and therefore down.
- The README has it right: "Without it the board sits too high on the pins" [hardware/boards/key-board-lh/README.md:189].

**Fix:** "it spaces the board 0.3 mm further from the plate".

### R2-8 [advisory] Provenance slips on correct numbers

**Node:** `hardware.kb_standoff_l`, `kb_screw_hole`, `kb_standoff_*` decided_by; `MECH-KB-STANDOFF`.

**Evidence:**
- **"head installed flush":** `kb_standoff_l` and the BOM row both cite p5. p5 does not say it [run: pdftotext -f 5 -l 5 | grep -ci flush → 0]. p16 does (MSO4 installation step 3).
- **`kb_screw_hole` 2.2:** its source says "ISO 273 medium". ISO 273 M2 is fine 2.2, medium 2.4 and coarse 2.6 [from memory], so 2.2 is the *fine* series. The value is sensible, because a tighter hole limits the float in R2-2.
- **`decided_by`:** `kb_standoff_od`, `_edge` and `_inset` still say "with the standoff chosen", but it has been chosen. What remains open is the clinch confirmation.

**Fix:** cite p16 for "flush", change "medium" to "fine", and reword `decided_by` to "PEM / plate vendor confirm the clinch".

### R2-9 [advisory] Small gaps in the rules and in the assembly steps, all currently passing

- **The edge-distance rule only checks the switch cutouts.** PEM's figure applies to any sheet edge. From the scratch echo:
  - Distance to the plate's side edges is **4.3** from every standoff (u_y0 + groove_clear edge).
  - Distance to the nearest M3 lid-fastener tap hole is **≥ 7.5** [calc].
  - Both pass `kb_standoff_edge` = 3. A rule would keep them passing when `board_clear` or `fastener_inset` moves.
- **The tolerance stack leaves out two contributors** that PEM does not dimension: the flush-installation tolerance of the head, and the mask/laminate under the washer (about 0.02) [from memory]. The NOTE at 3.17 is already 0.03 past the shoulder, so the first board is the real test, as the ADR says.
- **README step 2 does not say the plate lies face down.** Washers "on the end of each standoff" only stay put that way, and the washer's 2.2 bore does not locate on the 3.16 barrel's end face. The "check a sample washer with calipers" instruction also comes after the steps that fit it.
- **The heads show through the cap slot at three positions.** The standoff heads (H 3.96, flush) are 1.0 mm from the cap slot's edge at the three positions in R2-3. About 1 mm of each head, and its through-bore, is visible beside the cap [calc]. Cosmetic; the owner may want to know.

---

## Checked and found correct

- **MSO4-M2 numbers match p5 exactly** [PDF p5]: `kb_standoff_od` 3.16 = C max; `kb_standoff_hole` 3.2 is within 3.18 +0.05; `kb_standoff_edge` 3.0; `kb_standoff_l` 3 and `_l_tol` [−0.08, +0.05]. The SO bulletin has no M2, and the MANIFEST row agrees [datasheets/MANIFEST.csv:91-92].
- **Flush head in a 1.2 mm sheet is consistent with the part.**
  - The minimum sheet is 0.3 and no maximum is published. L includes the head, so the end sits L below the top face whatever the sheet thickness.
  - The HRB 88 limit is a maximum and aluminium is softer [p14; from memory for aluminium hardness].
  - No aluminium or 1.2 mm data is published. The ADR, the BOM row and README *Open* all correctly carry this as open with the vendor.
- **Washer:** ID, OD and thickness match the cited Aspen page. Choosing the small series rather than DIN 125 (OD 5.0 [from memory]) is correct for the keep-out.
- **Depth rules:**
  - The "standoff and washer set the board depth" arithmetic is 3 + 0.3 = 3.3 = `pcb_below_seat` [calc; drc.echo:64].
  - "inside the window" is correct.
  - The "tolerance limits" values [3.17, 3.40] reproduce, including the 0.03 overshoot text [calc; drc.echo:66].
  - The ADR's "reaches the window's shoulder end by a few hundredths" is a fair summary.
- **Model self-consistency:**
  - The standoff solid height `kb_gap − kb_washer_t` = 1.8 equals `kb_standoff_l − plate_thickness` for any plate thickness once the depth rule passes [calc: kb_gap = (L + t_w) − t_p].
  - The washer sits from `kb_top` to `kb_top + 0.3`. The screw head sits under the board.
  - The plate DXF hole is `kb_standoff_hole`.
  - The parts envelope keeps out `max(head, standoff od)` on the underside, which is correct because the washer is on top [woody_body.scad:1097].
- **"J-CHAIN pin tails clear of the key plate"** = 1.15. At the depth and plate-thickness limits it is still ≈ 0.97 ≥ 0.5 [calc: 1.15 − 0.13 − 0.05].
- **Screw engagement** at the short limit is ≈ 2.09 mm (~1 D) in a through-threaded 400-stainless bore: adequate. At nominal the tip stops 0.5 below the plate top and cannot reach the oak [calc].
- **Placement rules:**
  - Standoff-to-cutout distance is 3.606 ≥ 3.0 [drc.echo:63].
  - The screw head is 17.24 from J-CHAIN [drc.echo:69].
  - Count [4, 4] = BOM qty 8 for all three `MECH-KB-*` rows [hardware/unplaced.csv:25-27]. `hardware/bom.csv:150-152` carries identical rows.
  - `kb_standoff_inset` 3.0 − 3.8/2 = 1.1 [calc].
- **`thumb_pcb_below_seat`** is 3.4, tbd, the window's middle, and decided by the main board's standoffs. `cluster-boards.md` §5, `mechanical/DESIGN.md:46` and the ADR all keep it separate from the key boards' hardware. The model uses it only for `thumb_z` [woody_body.scad:788].
- **PCB:**
  - Four NPTH 2.2 holes, each flipped to the bottom with a B.CrtYd of r 2.45 > the head's r 1.9.
  - Rule areas are on F.Cu and B.Cu.
  - The nearest non-pour copper to any hole edge is ≥ 4.69 mm (R-KEY-SER-LH4 / R-KEY-PU-LH5 pads).
  - No pad sits inside any keep-out [run: pcbnew script].
- **README assembly step 2:**
  - The order is right: clip the switches, fit washers, lower the board, screw it, *then* solder, so the hardware fixes the depth before the joints do.
  - M2×4 and the washer series are named correctly.
  - The "without it the board sits too high" direction is right.
- **No live 2.2 standoff length or 3.4 key-board depth** was found in the corpus other than the items in R2-1 and R2-5 [run: grep over hardware, docs/decisions, docs/reference, config, mechanical].
