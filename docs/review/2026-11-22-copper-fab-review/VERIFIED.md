# VERIFIED — the fixes, re-measured

Revision **`02fdab22`** (branch `claude/project-thread-1yybmd`), the main-board
thread's fixes. `tools/` changed in that commit and is still not used here: the
same scripts in this directory's `tools/` were re-run on the five boards as
they stand at that revision, with KiCad 9.0.9. Every figure below is `[test]`.

| Id | Verdict | What was measured at `02fdab22` |
|---|---|---|
| F1-1 | **closed** | Smallest via hole to an SMD mask opening on main-board is now 0.25 mm (was −0.125). R34, R35, R36 pin 2, L1 pin 1 (both vias), R5 pin 2, C1 pin 2, C203 pin 2 and Q1 pin 3 all at 0.25 mm or more. `img/after-F1-1-R34-R35-R36.png`, `img/after-F1-1-L1.png` |
| F1-2 | **closed, by reading** | `tools/pcb.py:1933` now holds `VIA_DAM`, a via's hole to an SMD pad's edge `[repo]`. Not exercised here with a failing case |
| F2-1 | **closed** | The two post holes open into notches in the outline (outline area 625.0 → 619.3 mm²). `img/after-F2-1-adapter-notches.png`. See the note below |
| F3-1 | **left, owner's choice** (2026-11-22) | Rings unchanged at 0.185 mm |
| F4-1 | **closed** | `PWR_GND` (In1) and `INST_POS12` (In2) are 1.0 mm from both U-bolt cut-outs (was 0.3); new rule areas "U-bolt leg 1 planes", "U-bolt leg 2 planes" on In1 and In2 |
| F5-1 | **closed** | J1's ground pins on main-board In1 and matrix-carrier B.Cu each reach the plane by a spoke. `img/after-F5-1-J1-main.png` |
| F6-1 | **closed; one half of it was wrong** | Vias on key-board-lh, key-board-rh and matrix-carrier are 0.8 mm on 0.3 mm, a 0.25 mm ring. At `6510e5f2` the KS-33 pin pads are 3.5 mm on 3.0 mm, a 0.25 mm ring, on both key boards and main-board. **The carrier's mount pads never had a 0.2 mm ring: the reviewer was wrong.** The footprint puts a 5.4 mm pad on F.Cu and on B.Cu over the 3.1 mm barrel pad, so the ring on each face of the 2-layer carrier is 1.35 mm `[calc: (5.4 − 2.7) / 2]`, and both apertures are in the carrier's `F_Cu` and `B_Cu` Gerbers `[repo]`. The first pass measured the 3.1 mm pad alone. It stands alone only on main-board's In1 and In2, where 0.2 mm is the multilayer recommended figure |
| F7-1 | **closed** | J6 pin 6 and U5 pin 2 now have four spokes each |

**Run again at `6510e5f2`** (the KS-33 pads enlarged, this branch merged in): the only measurements that moved are the KS-33 rings above.

**Nothing regressed.** On all five boards, at both revisions: KiCad DRC 0 violations and 0
unconnected; smallest different-net clearance still 0.20 mm; smallest mask web
0.20 mm; edge clearance 0.30 mm; no silk on pads or holes; no acute joins, no
dangling ends, no plane feature under 0.2 mm; the committed `fab/` Gerbers and
drill files are identical to a fresh export.

**Two things to know, neither a defect.**

- **umb-adapter:** `fab/umb-adapter-NPTH.drl` still drills the two Ø1.7 holes
  that the notches now open to the edge. A hole on the outline can draw a
  query from the fabricator; the answer is that the notch is the intent.
- **main-board, R34 and R35 pin 2:** the moved via's ring stands 0.075 mm from
  the pad, joined by its track, which leaves two same-net pockets narrower than
  the etch resolves. They fill with copper and change nothing electrically; the
  mask between the pad's opening and the hole is 0.275 mm
  `[calc: 0.425 − 0.15]`.
