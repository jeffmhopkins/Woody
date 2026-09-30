# K3 — The PCB of the left-hand key board

**Slice:** K3, cold. **Revision:** `d46a3b0`, working tree clean apart from this
wave's directory. `tools/` not modified; every experiment ran on copies under
the session scratchpad.
**Fact domain:** `hardware/boards/key-board-lh/key-board-lh.kicad_pcb`, its
`layout.yaml` (`rules:`, `fab:`), `fab/`, and the footprints in
`hardware/lib/woody.pretty`, against KiCad 9.0.9's DRC and JLCPCB's banked
capability pages.

## Summary

The board passes its gate. `python3 tools/pcb.py check hardware/boards/key-board-lh`
reports `0 error(s), 0 warning(s)`, and a direct `kicad-cli pcb drc
--schematic-parity --severity-all` reports 0 violations, 0 unconnected items and
0 parity issues. Nothing is excluded. Every copper rule in `layout.yaml` is
looser than JLCPCB's banked minimums. The fab set is complete, and its
coordinates line up with the Gerbers. Pin-1 marks and test-pad labels are
correct.

What the gate does not see:

1. **Vias in pads (K3-1, medium).** 20 of the 44 vias sit centred in an SMD pad or
   a test pad, and 5 more overlap one. This happens on the reflowed side, on
   6 of the 74HC165's 16 pins, and on every key network. The router never keeps
   a via out of its own net's pad.
2. **Fab limits that do not gate (K3-2, medium).** Two of the `fab:` limits
   (`silk_line_min`, `silk_to_pad`) are not checked by KiCad's DRC at all. The
   rest are set to `warning`, which `pcb.py check` and `kicad.py check` let
   through. So the README's "KiCad's DRC checks this board against them" is only
   partly true, and the board's gate would pass a board that breaks JLC's
   limits. Both points were demonstrated on a scratch copy.
3. **Smaller defects.** The silkscreen breaks JLC's legend limits in several
   places (K3-3). The drills are tight for both of the board's pin types
   (K3-4, K3-5). The router leaves a 0.2 mm-grid tangle behind it (K3-6, K3-7).
   The job file is missing its revision (K3-9). `layout.yaml` restates a JLC
   figure that the banked page two lines below it contradicts (K3-11).

## Findings

### K3-1 [medium] 20 vias are centred inside SMD or test pads on the reflowed bottom side, and 5 more overlap pads; nothing prevents it

- **Node.** Vias on `B.Cu` pads, drill 0.3 mm, diameter 0.7 mm. Measured by
  `pcbnew` `PAD.HitTest` and the distance to each pad's polygon
  [run: scratch `vip.py`, pcbnew API on the committed board].
- **`U-KEYS-LH` (74HC165, SOIC-16):** vias in pads 3, 8, 9, 10, 13 and 14
  (`/KEY_LH4`, `GND_CHAIN`, `/HOP_LH_LT`, `/CHAIN_SER_LH`, `GND_CHAIN`,
  `/KEY_LH5`). One more via overlaps pad 1 (`/CHAIN_SHLD`).
  - The via is 0.7 mm across and the SOIC pad is 0.6 mm wide, so the via ring
    stands 0.05 mm proud of both sides of the pad [calc: (0.7 − 0.6)/2 = 0.05].
- **Key networks:**
  - `R-KEY-SER-LH1` pad 1, `R-KEY-PU-LH1` pad 2, `R-KEY-PU-LH2` pad 2,
    `R-KEY-SER-LH5` pad 1, `R-KEY-PU-LH5` pad 2 and `R-KEY-SER-LH4` pad 2.
  - `C-KEY-LH2` pad 2 (two vias), `C-KEY-LH3` pad 2 (two vias), `C-KEY-LH4`
    pad 2 and `C-KEY-LH5` pad 2.
  - Overlapping, not centred: `C-KEY-LH1` pad 2, `C-KEY-LH4` pad 2 (a second
    via) and `C-KEY-LH5` pad 2 (a second via).
- **Decoupler:** a via in `C-DECOUPLE-165-LH` pad 2 (`GND_CHAIN`).
- **Test pads:** a via is centred in `TP-3V3-LH`, and another overlaps
  `TP-GND-LH`.
- **Why it matters.**
  - Vias are tented (`(tenting front back)` [repo `key-board-lh.kicad_pcb`
    setup]), but a via inside a pad's mask opening is not.
  - These pads get paste (`B_Paste.gbr` has 50 flashes, one for every SMD pad
    [run: `grep -c D03`]) and are reflowed by JLC's Economic PCBA on this side.
  - An open 0.3 mm barrel in a 0.6 × 1.95 mm or 1.0 × 1.45 mm pad draws solder
    off the joint into the barrel.
  - JLC sells a separate "Via-in-Pad Process — Epoxy Filled & Capped" for
    exactly this [datasheets/fab/JLCPCB-PCB-CAPABILITIES.pdf, p. 6]. The README
    does not order it, and `layout.yaml` does not mention it.
- **Cause.** `tools/pcb_route.py` `blocked(net, width, via=True)` marks where
  *this net* cannot put a via centre. A net's own SMD pads are not obstacles to
  it [repo `tools/pcb_route.py` l.131–137]. `stitch_gnd` says it puts each GND
  pad's via "beside it" (l.367), but in 7 cases it lands in the pad.
- **Fix.**
  - Keep via centres out of every SMD and test-pad polygon, own net included,
    grown by the via radius plus 0.1 mm. That is a tool change, so it waits for
    the post-wave window.
  - Then re-route, or move these 25 vias by hand in KiCad, since the
    `.kicad_pcb` is now the source.
  - Failing that, order via-in-pad filling and say so in the README's order
    table.

### K3-2 [medium] `layout.yaml` `fab:` is not what gates the board. Two limits are unchecked, and the rest only warn, which the gate ignores

- **Rule.** `layout.yaml` `fab:` says "KiCad's DRC checks the board against these
  as well as against rules: above". The board README says "they are in
  `layout.yaml` `fab:`, so KiCad's DRC checks this board against them"
  [repo `hardware/boards/key-board-lh/layout.yaml`, `README.md` "Ordering it"].
- **`fab.silk_to_pad: 0.15` → `min_silk_clearance`.**
  - In KiCad 9 this constrains silk to silk only. Silk to a mask opening is
    flagged only when the two overlap.
  - Demonstrated on a scratch copy: I moved the `J-CHAIN` pin-1 dot to 0.05 mm
    from pad 1 and got no violation. At −0.1 mm (overlapping) I got
    `silk_over_copper` [run: `kicad-cli pcb drc --severity-all` on
    scratch `t.kicad_pcb`, gaps 0.125 / 0.05 / −0.1].
- **`fab.silk_line_min: 0.15` → `min_text_thickness`.** This applies to text
  only. No DRC rule checks the width of silk lines, so K3-3's 0.12 mm and
  0.1 mm lines pass.
- **`hole_to_hole`, `text_height`, `text_thickness`, `silk_overlap`,
  `silk_edge_clearance`, `copper_sliver`, `isolated_copper`, `track_dangling`
  and `via_dangling`** are all `warning` in `rule_severities`
  [repo `key-board-lh.kicad_pro`].
  - `tools/pcb.py cmd_check` returns non-zero only on lines that start with
    `error`, and `tools/kicad.py check` collects only `error` lines
    [repo `tools/pcb.py` l.495–531, `tools/kicad.py` l.466–470].
  - Demonstrated: a scratch copy with a 0.7 mm silk text and two holes 0.35 mm
    apart gave `[text_height] … warning` and `[hole_to_hole] … min 0.4495 mm;
    actual 0.3500 mm … warning` [run: `kicad-cli pcb drc` on scratch
    `t3.kicad_pcb`]. On the real board these would print and still pass.
- **Why medium.** This is the worked example. Every other board copies this
  gate and inherits the belief that JLC's limits are enforced.
- **Fix.**
  - Set the fab-derived severities (`hole_to_hole`, `text_height`,
    `text_thickness`) to `error` in the `.kicad_pro`.
  - Add a `.kicad_dru` custom rule for silk to mask
    (`(constraint silk_clearance (min 0.15mm)) (condition "A.Layer == 'B.Mask' || …")`)
    or check it in `pcb.py`. Check silk line width in `pcb.py` as well.
  - Until then, reword the README and the `layout.yaml` sentence to say which
    limits DRC actually enforces.

### K3-3 [low] The silkscreen breaks JLC's legend limits: 0.12 mm and 0.1 mm lines, and silk 0.128 mm and 0.14 mm from pad openings

JLC's limits are line width ≥ 0.15 mm ("will be unidentifiable" below it) and
pad to silkscreen ≥ 0.15 mm [datasheets/fab/JLCPCB-PCB-CAPABILITIES.pdf, p. 7].
The same limits are in `layout.yaml` `fab.silk_line_min` and `fab.silk_to_pad`.

- **Line width.**
  - Every stock footprint's `B.Silkscreen` outline is 0.12 mm: 16 × R/C 0805,
    the SOIC-16 (6 lines and the pin-1 triangle), 5 × test-pad circles, and the
    `J-CHAIN` shroud rectangle [run: pcbnew dump of footprint graphics].
  - The board-level `J-CHAIN` pin-1 dot (`gr_circle` at 130.14, 111.16, filled)
    has a 0.1 mm stroke [repo `key-board-lh.kicad_pcb` l.5193].
- **Silk to pad.**
  - The `J-CHAIN` pin-1 dot is 0.128 mm from pad 1's opening [calc: pad edge
    131.14 − 0.525 = 130.615; dot edge 130.14 + 0.30 + 0.05 = 130.49; gap 0.125,
    measured 0.128 by polygon].
  - The five `TP-*-LH` rings are 0.14 mm from their pads [run: scratch
    `silk.py`, shapely distance from each silk polygon to each B.Mask pad
    polygon].
  - Every text item is ≥ 0.2 mm from any pad.
- **Effect.** Low: JLC clips or drops silk it cannot print. But the pin-1 dot
  is the mark the README tells the assembler to use ("Pin 1 is the dot on the
  silkscreen").
- **Fix.**
  - Set the footprints' silk line width to 0.15 mm (board-level override, or
    the Woody copies in `hardware/lib`).
  - Move the pin-1 dot to ≥ 0.15 mm from the pad edge (centre x ≤ 130.07, or
    radius 0.25).

### K3-4 [low] `J-CHAIN`: a 0.65 mm finished hole for a 0.41 mm square tail leaves 0.07 mm over the diagonal nominally, and none at JLC's worst-case tolerance

- **Node.** `J-CHAIN` pads 1–12, `woody:IDC-Header_2x06_P1.27mm_Samtec_SHF_Horizontal`:
  a 1.05 mm pad on a 0.65 mm drill [repo `hardware/lib/woody.pretty`].
- **The fit.**
  - The tail is `.016 [0.41] SQ REF (TYP)` [datasheets/connectors/SAMTEC-SHF-1XX-01-X-D-XX-PRINT.pdf,
    sheet 1], so its diagonal is 0.58 mm [calc: 0.41 × √2 = 0.580].
  - JLC's through-hole tolerance is +0.13 / −0.08 mm
    [datasheets/fab/JLCPCB-PCB-CAPABILITIES.pdf, p. 3]. The finished hole is
    therefore 0.57–0.78 mm, and at the low end it is smaller than the tail's
    diagonal [calc: 0.65 − 0.08 = 0.57 < 0.58].
  - The print gives no recommended PCB hole; only the tail is dimensioned, and
    as REF.
- **Annular ring.** 0.20 mm [calc: (1.05 − 0.65)/2]. That is above JLC's
  absolute minimum of 0.18 but below its recommended 0.25 for 2-layer 1 oz
  [same PDF, p. 5]. `layout.yaml` says so.
- **Fix.** Either take a 0.70 mm drill on a 1.07 mm pad, or keep 0.65 mm and
  record the fit risk as open, decided by the first mated part.
  - With 0.70 / 1.07: annular 0.185 ≥ 0.18, pad-to-pad gap 0.20 = the clearance
    rule [calc: 1.27 − 1.07 = 0.20], and the worst-case hole is 0.62 > 0.58.

### K3-5 [low] KS-33: a 1.2 mm round hole for a 0.45 × 1.00 mm blade leaves 0.02 mm at worst case, and the banked vendor drawing contradicts itself on the pattern

- **Node.** `SW-LH1..5` pads 1 and 2: a 2.0 mm pad on a 1.2 mm drill
  [repo `hardware/lib/woody.pretty/SW_Gateron_KS33_1u.kicad_mod`].
- **The fit.**
  - The vendor drawing gives the terminal as 0.45 thick and "ø1.00"
    [datasheets/mechanical/GATERON-KS-33-VENDOR-SPEC-DRAWING.pdf, p. 6].
  - Read as a 0.45 × 1.00 blade, its diagonal is 1.10 mm [calc:
    √(0.45² + 1.00²) = 1.097]. JLC's worst-case finished hole is 1.12 mm
    [calc: 1.2 − 0.08], so the margin is 0.02 mm.
  - With the drawing's general tolerance of ±0.2 mm on features up to 3 mm
    (same page), a wide blade will not go in.
- **The vendor's own two patterns disagree.**
  - PDF page 3 (printed "4"), §8 "Mounting Options", draws the pins as slots 0.90 mm wide.
  - p. 6, "PCB Layout", draws them as ø3.00 holes.
  - The footprint follows neither: it is the community pattern that three
    banked third-party sources share (manifest rows for `SW_KS33_1u`, ergogen
    and the STEP).
- **Fix.** Take a 1.3 mm drill on the 2.0 mm pad (annular 0.35) for 0.12 mm of
  worst-case margin, or keep 1.2 mm and add the 0.02 mm margin to the board
  README's open table, decided by the first switch pushed into the first board.
- *Checked and correct:* the footprint is the mirror of both vendor figures,
  and that is right.
  - p. 6's PCB Layout matches p. 6's bottom view of the housing: pin at 2.60
    left, pin at 4.40 right, RGB window 3.20 to the right. So it is drawn as
    seen from below.
  - The footprint (top view) has pin 1 at (−4.4, +4.7), pin 2 at (+2.6, +5.75),
    and the LED window at x −3.2…+1.8.
  - In `kicad-cli pcb render --side bottom`, the STEP model's blades sit inside
    the plated holes [run: render, scratch `r3d_bot.png`].

### K3-6 [low] The router's output is left on its 0.2 mm grid: 449 unmerged collinear fragments, 4 acute junctions, and 180 mm of ground tracks that `layout.yaml` says are not there

[run: scratch `route.py`, pcbnew API]

- **Fragments.**
  - 684 track segments, of which 463 are shorter than 0.3 mm.
  - At 449 track-to-track joints, two collinear segments meet head to tail and
    could be one.
  - Straight runs are chains of 0.28 mm diagonal steps, e.g. `GND_CHAIN` B.Cu
    (153.0, 101.5)→(153.2, 101.7)→(153.4, 101.9)→(153.6, 102.1).
  - The board is "edited in KiCad" from here on (README), and each of these
    runs has to be hand-selected piece by piece.
- **Acute junctions** (acid traps; the fill cannot enter the wedge):
  - `V3V3_CHAIN_LH` F.Cu at (130.2, 112.3): 45°, a diagonal teeing into the
    0.4 mm rail.
  - `GND_CHAIN` F.Cu at (131.2, 128.1): 45°.
  - `GND_CHAIN` B.Cu leaving `U-KEYS-LH` pad 8: two tracks 4° apart, to
    (146.2, 108.5) and (146.2, 108.7).
  - `GND_CHAIN` B.Cu leaving pad 15: two tracks 18° apart, to (154.0, 101.5)
    and a staircase to (153.6, 102.3). These are redundant parallel ground
    tracks from one pad.
- **Ground tracks.** `layout.yaml` says "ground is a pour on both layers, not
  tracks". The board carries 179.6 mm of `GND_CHAIN` track (F 97.9, B 81.7) and
  23 GND vias.
- **Not a defect: no long detours.** Every net's routed length is 0.66–1.12 ×
  its rectilinear MST (`/CHAIN_SHLD` is the worst at 1.12).
- **Fix.** Merge collinear segments and drop GND tracks that the pours already
  cover (pcbnew `CleanupTracksAndVias`, or the router, after the freeze). Then
  re-fill and re-run DRC. Or correct the `layout.yaml` sentence.

### K3-7 [low] The key-network pad order forces the `KEY_LHn` node across neighbouring pads, which is where most signal vias come from

- **Node.** Each key's C–S–P row at 4 mm pitch, all rotation 0
  [repo `layout.yaml` `parts:`].
  - Along x: `C` pad 1 = KEY, `C` pad 2 = GND, `S` pad 1 = KEY,
    `S` pad 2 = LEG, `P` pad 1 = 3V3, `P` pad 2 = KEY.
  - So the KEY node's three pads are separated by a GND pad, a LEG pad and a
    3V3 pad [run: pcbnew pad dump].
- **Effect.** 13 of the 19 signal vias are on `/KEY_LH1` (3), `/KEY_LH2` (2),
  `/KEY_LH4` (2), `/KEY_LH5` (4) and `/LH4/SWITCH_LEG` (2).
  - `/KEY_LH1` runs 38 mm on F.Cu to reach a B.Cu part row.
  - `/KEY_LH3` routes with 0 vias, which shows the row can be routed without
    them.
- **Fix.** Rotate `C-KEY-LHn` by 180° and `R-KEY-PU-LHn` by 180°, so that the
  KEY pads of C, S and P face one short common stub. Or set P at 90° above the
  S/C boundary. Then re-route. This also removes most of K3-1's
  key-network vias-in-pad.

### K3-8 [advisory] The decoupling loop closes through the F.Cu plane, 12.9 mm between the capacitor's ground via and pin 8's

- **Node.** `C-DECOUPLE-165-LH` (157.0, 103.5), with `U-KEYS-LH` pin 16 (VCC)
  and pin 8 (GND) [run: pcbnew].
- **The supply side** is good: about 3.5 mm of 0.4 mm B.Cu track from pin 16 to
  pad 1 [calc: sum of the segments listed by `route.py`].
- **The ground side.**
  - Pad 2 goes by a via-in-pad (157.6, 102.5) to the F.Cu pour, and by B.Cu
    track to pin 15 (`CLK INH`, tied to ground, not the supply pin).
  - Pin 8 is at the SOIC's opposite corner (146.055, 107.975) with its own
    via-in-pad (146.2, 108.5).
  - The plane path between the two vias is ≥ 12.9 mm [calc:
    √(11.4² + 6.0²) = 12.9].
  - It crosses under the register, where the F.Cu chain tracks (`/CHAIN_SCK`
    at y 105.7 to x 153.6, `/CHAIN_SER_LH`, `/HOP_LH_LT`) cut the plane.
- **Why only advisory.** The pinout puts VCC and GND at opposite corners. At the
  chain's clock this is not a failure, but it is not the example layout either.
- **Fix.** Run a 0.4 mm B.Cu ground track from `C-DECOUPLE-165-LH` pad 2, along
  the SOIC's pin-9–16 side, to pin 8. Or give pin 8 a stitching via on the
  other side of the chain bundle.
- *Checked and correct:* the SCK, SH/LD, SER and QH tracks on F.Cu from
  `J-CHAIN` to the register (x 131–146) run over unbroken B.Cu pour
  [run: `kicad-cli pcb export svg --layers B.Cu`]. The pour breaks only under
  the SOIC's own pads.

### K3-9 [low] The Gerber job file says `"Revision": "rev?"`; the board has no title block, and the stackup has no copper weight or mask colour

- `key-board-lh-job.gbrjob` `GeneralSpecs.ProjectId.Revision` is `"rev?"`, and
  every Gerber's `%TF.ProjectId…,rev?*%` says the same.
- The silkscreen says `rev A  2026-09-27` [repo `fab/key-board-lh-job.gbrjob`;
  `fab/key-board-lh-B_Cu.gbr` header; board text at (104.0, 139.1)].
- The `.kicad_pcb` has no `title_block`, and its `stackup` holds only
  `copper_finish` [repo `key-board-lh.kicad_pcb` l.1–45]. So the job file
  carries thickness (1.2) and finish (HAL lead-free) but no 1 oz copper and no
  green mask; those live only in the README's order table.
- **Fix.** Have `pcb.py layout`/`add_silk` write a title block (title, rev, date
  from `layout.yaml` `silk:`) and a full stackup (copper 0.035, mask colour
  Green).

### K3-10 [advisory] PTH and NPTH share one drill file

- `key-board-lh.drl` is `TF.FileFunction,MixedPlating,1,2`. Its tools are T1
  0.30 (44 vias), T2 0.65 (12), T3 1.20 (10), T4 2.20 NPTH (4) and T5 5.25 NPTH
  (5), each carrying an `AperFunction` Plated/NonPlated attribute
  [repo `fab/key-board-lh.drl`].
- The counts match the board (44 vias, 12 `J-CHAIN`, 10 switch pins, 4 M2 holes
  and 5 switch centre poles).
- My recollection is that JLC's KiCad Gerber guide asks for separate PTH and
  NPTH files [from memory; that guide is not banked, only the BOM/CPL guide is].
- ADR 0020 needs the M2 holes unplated.
- **Fix.** Add `--excellon-separate-th` to `pcb.py render`'s drill export, or
  bank JLC's Gerber/drill guide and cite it.

### K3-11 [low] `layout.yaml` restates JLC's track/space as 0.127 mm "[from memory]"; the page banked two lines below says 0.10/0.10

- `layout.yaml` `rules:` comment: "JLCPCB's standard 2-layer process allows
  0.127 mm track and space [from memory]".
- The banked page gives 0.10 / 0.10 mm (4/4 mil) for 1 oz on 1–2 layers
  [datasheets/fab/JLCPCB-PCB-CAPABILITIES.pdf, p. 5]. The same file's `fab:`
  block, eleven lines further on, cites that page.
- The design rules (0.25/0.2) are unaffected. But this is a restated figure that
  went stale against a banked document (CLAUDE.md rule 3).
- **Fix.** Cite the banked page and give its 0.10/0.10, or delete the number.

### K3-12 [advisory] ADR 0020's "the PCB carries [the ribbon's run] as a rule area" is not on the board

- ADR 0020 §3 says that where the ribbon runs under the board, the PCB carries
  a rule area [repo `docs/decisions/0020-key-boards-screw-to-the-plate.md`].
- The board has exactly 4 rule areas, the standoff keep-outs [run: pcbnew zone
  dump].
- `tools/pcb.py` draws the ribbon area only from a `ribbon` record in
  `mechanical/export/pcb-geometry.echo`. The echo now has a `chain` record and
  no `ribbon` record (l.6) [repo].
- Nothing sits in the header's mouth: the nearest part, `R-KEY-PU-FREE3`, is
  about 2.9 mm beyond the header body's end plus `boards.chain_plug_proud`
  [calc: 143.4 − (139.12 + 1.4) ≈ 2.9, taking the body end from the footprint's
  silk rectangle].
- This belongs to K5 (the ribbon's hairpin). K3 records only that the PCB has
  no keep-out for it and that the ADR sentence has gone stale.

### K3-13 [advisory] The register's only label is printed under its own body

- The `74HC165` silk text sits at the SOIC's centre (146.97–154.03,
  104.65–106.35), between the pad rows, and disappears once the part is placed
  [run: pcbnew text bounding boxes].
- Every other part has its letter (C/S/P, PF, CD) outside its body.
- **Fix.** Move the label to beside pin 9–16's row, e.g. y ≈ 101.3.

## Checked and correct

- **DRC and schematic parity.**
  - `pcb.py check`: 0/0 [run: `python3 tools/pcb.py check hardware/boards/key-board-lh`].
  - `kicad-cli pcb drc --schematic-parity --severity-all` with the project's
    library table: 0 violations, 0 unconnected, 0 parity issues, 0 exclusions
    [run].
  - The body CAD's switch, standoff and `J-CHAIN` positions hold, since
    `pcb.py check` checks them.
- **Rules against JLC** [datasheets/fab/JLCPCB-PCB-CAPABILITIES.pdf pp. 3–7;
  repo `key-board-lh.kicad_pro` `design_settings.rules`]. Each value below is
  the board's, then JLC's minimum.

  | Rule | Board | JLC | Holds |
  |---|---|---|---|
  | Track / space | 0.25 (min 0.2) / 0.2 | 0.10 / 0.10 | ✓ |
  | Via hole / diameter | 0.3 / 0.7 | min 0.15 / 0.25; preferred hole ≥ 0.2; diameter ≥ 0.45 avoids the surcharge; diameter ≥ hole + 0.15 | ✓ all |
  | Via annular ring | 0.2 | — (`min_via_annular_width` 0.18) | ✓ |
  | PTH annular ring | 0.20 (`J-CHAIN`), 0.40 (switches) | 0.18 absolute | ✓ |
  | PTH to track | 0.28 | 0.28 (0.35 recommended) | ✓ |
  | NPTH to track | 0.28 | 0.2 | ✓ |
  | Pad hole to hole | 0.45 | 0.45 | ✓ |
  | Pad to track | 0.2 | 0.1 | ✓ |
  | SMD pad to pad | 0.2 | 0.15 | ✓ |
  | Mask web | 0.67 (SOIC), 0.22 (`J-CHAIN`) | 0.10 | ✓ |
  | Copper to routed edge | 0.3 | 0.2 | ✓ |
  | Min NPTH | 2.2 / 5.25 | 0.5 | ✓ |
  | Silk text | 1.0 high / 0.15 stroke | ≥ 1.0 / ≥ 0.15 | ✓ (all 31 texts) |

  - Via-to-via hole spacing is held to 0.45 against JLC's 0.2.
  - The text's width-to-height ratio is 1 : 6.7 against a preferred 1 : 6
    [calc: 0.15/1.0].
  - DRC does enforce pad annular rings: a scratch pad shrunk to a 0.125 mm ring
    raised `annular_width` [run: `kicad-cli pcb drc` on scratch
    `t2.kicad_pcb`].
- **The 3V3 rail.**
  - All 139 segments of `V3V3_CHAIN_LH` are 0.40 mm (`power_track`), 129 mm in
    total (B 94.4, F 34.7), with 2 vias.
  - The drop at the worst case is well under 1 mV [calc: 1 oz, 0.4 mm ≈ 1.2 mΩ/mm
    × ~70 mm ≈ 86 mΩ × ≤ 10 mA ≈ 0.9 mV].
- **Ground pours.**
  - `GND_CHAIN` fills both layers: F 3026 mm² and B 2762 mm² main outlines on an
    84.1 × 42.1 board.
  - Island removal is "always", so every remaining fragment is connected. The
    fragments are the 0.3–0.5 mm² pieces between `J-CHAIN`'s ground pins, and
    one 8.7 mm² F.Cu strip between the chain tracks.
  - Thermal reliefs are 0.4 mm spokes with a 0.3 mm gap; at least 2 spokes
    resolved on every pad, per DRC.
- **Standoff keep-outs.**
  - Four rule areas, 4.4 mm across, on both copper layers, at the four M2 holes
    = max(`kb_screw_head_d` 3.8, `kb_standoff_od` 4.0)/2 + 0.2 [repo
    `config/body.yaml`, `tools/pcb.py` l.431].
  - No track, via or fill inside them.
  - The holes are NPTH with no copper, as ADR 0020 §4 requires.
- **Test pads.**
  - Five 1.0 mm pads on `B.Cu` at 3.5 mm pitch (145.0–159.0, 112.5). None has
    paste.
  - Each is ≥ 3.0 mm from `U-KEYS-LH`'s pads and ≥ 6 mm from the `J-CHAIN` body.
  - Each is labelled next to the right pad: 3V3 → `V3V3_CHAIN_LH`,
    GND → `GND_CHAIN`, SCK → `/CHAIN_SCK`, SH/LD → `/CHAIN_SHLD`,
    QH → `/HOP_LH_LT` = pin 9 QH [run: pcbnew pad dump; mirrored silk render].
  - Exception: the vias noted in K3-1.
- **The mirrored `B.Silkscreen` render** [run: `kicad-cli pcb export svg --mirror
  --layers B.Silkscreen,B.Mask,Edge.Cuts`, read as an image].
  - Every C/S/P letter sits over its own part: C over `C-KEY-LHn`, S over
    `R-KEY-SER-LHn`, P over `R-KEY-PU-LHn`, for all five keys.
  - LH1–LH5 sit beside their own rows. PF sits by `R-KEY-PU-FREE3` and CD by
    `C-DECOUPLE-165-LH`.
  - The `U-KEYS-LH` pin-1 triangle is at pin 1 (154.945, 107.975). The
    `J-CHAIN` pin-1 dot and square pad are at pad 1.
  - The title and revision read correctly from the bottom.
  - `F.Silkscreen` is empty, by design: the switch side carries only switches.
- **Fab set completeness.**
  - F/B copper, paste, mask and silkscreen, plus `Edge_Cuts`.
  - The drill file holds both PTH and NPTH (K3-10).
  - The job file gives thickness 1.2 and finish "HAL lead-free", which matches
    `layout.yaml` `fab.finish` and JLC's Economic PCBA table (1.2 mm,
    green/black, HASL) [datasheets/fab/JLCPCB-PCBA-CAPABILITIES.pdf].
- **Origins.**
  - The Gerbers, the drill file and `-pos.csv` all use KiCad's absolute page
    origin with Y negated.
  - Example: `U-KEYS-LH` pad 1 flashes at `X154945000Y-107975000` in
    `B_Cu.gbr`, which is the pos centre (150.5, −105.5) plus the pad offset.
  - The drill's T1 list and the via coordinates agree.
  - `-cpl-jlc.csv` copies `-pos.csv` for the 18 machine-placed parts, with
    Bottom and KiCad's rotation. Rotation correctness is K4's.
- **Board-edge holes.** H1–H4 are 3.55 mm in from both edges, symmetric
  [calc: e.g. 100.5 − 96.95].
- **`J-CHAIN` footprint.** The pads are placed so that `pcb.py check`'s
  mouth-direction and pad-centre tests pass. The body's silk rectangle ends
  0.37 mm inside the top edge, and its courtyard ends 0.05 mm inside it.
