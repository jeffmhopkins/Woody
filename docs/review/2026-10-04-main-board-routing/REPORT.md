# Main board routing review — issue #35, pass 1 (read-only)

**Measured against:** `1b70492` (rev I: trace cleanup #33, planes stitched #8-8, iron room #34),
`hardware/boards/main-board/main-board.kicad_pcb`. **`tools/` pinned at the same commit**: every
scratch reroute and check ran in a `git archive 1b70492` copy, never in the working tree. The board
was not touched.

**The owner's complaint** (#35): *"several traces ... still look a little wonky versus expectations
with slight detours in longer runs for no reason. Also a couple places where via transfers doesn't
look like it's actually needed and could have just been routed around or followed up with other
lines easier."* Policy: short, straight, 45° runs; power on zones; ground pours; horizontal/vertical
only where a region needs it.

**Out of scope by instruction, and not reported as defects:** the breath pair
(`/SENSOR_BUFFERED_OUT` / `AGND_INST` on layer 4, its guards, stitching and mount arcs), the locked
analog hand routes (README, *The analog block*), part placement, and anything `check_holes` /
`check_iron` hold.

Coordinates are **KiCad mm**; the board frame of `layout.yaml` and the README is `x − 60`,
`150 − y` (`tools/pcb.py` `OX`, `OY`).

*Committed by the orchestrator: the reviewing agent's harness refused report files, so this text
is its returned report, saved verbatim with the figures it produced.*

## Summary

| Type | Items | Proven | Likely | Worth |
|---|---|---|---|---|
| Detour | 6 (R1–R6) | 5 | 1 | 7.6 mm proven, plus R6's 6.8 mm loop |
| Via | 9 (R7–R13, R15, R16) | 0 | 9 | 19 vias on the chains named; the U8 cluster 10 by scratch rip-up |
| Other | 5 (R17–R21) | 0 | 5 | layer-4 analog leg, overlapping ends, off-centre pad entries, bus pitch, a via mid-track |

The board is clean at the scale of a single run. Of 674 runs and 148 signal vias, a single-run
reroute with every other net held fixed finds only five runs that get legally shorter or straighter.
No via can go without moving another net's copper `[test]`. What the owner sees is concentrated in
**three dense fan-ins**: **U8 / J5**, **J4 / U9** and **U1 / R1–R3 at J-MCU**. In each, the router
laid nets in an order that makes them cross, and each crossing costs a pair of vias or a loop. They
are fixable only by re-laying a group of nets by hand together. The router's own rip-up, given the
same problem in a scratch copy, removes vias but leaves connections open, or adds vias elsewhere.

## Method

Scripts reuse the board's own `tools/pcb_route.py` obstacle model. A path that passes them is legal
by the router's own rules: 0.2 mm clearance to every other net's copper, keep-outs (moat, mounts,
U-bolts, regulator block), unplated-hole clearance, the edge, and the breath pair's 3W guard.

1. **Runs** (`a1_runs.py`): each net's copper per outer layer is cut into runs between terminals
   (pad, via, junction, a T). For each run: routed length against the straight and octilinear
   minimum, jogs (< 2 mm offset between parallel pieces ≥ 2 mm long), zig-zags, acute and off-45°
   pieces. Result: 674 runs; 37 with ratio > 1.15 and excess > 1 mm; 21 jog or zig-zag hits.
2. **Scratch reroute** (`a2_reroute.py`): 255 unlocked signal runs re-searched between the same ends
   on the same layer (`pcb_route.Grid` A*), string-pulled to straight and 45° pieces, each piece
   re-verified by `Obstacles.track_ok`.
3. **Other** (`a3_other.py`): missed ends, overlaps, off-centre pad entry, acute joins, parallel pitch.
4. **Via chains** (`a4_vias.py`): the 148 non-plane vias joined into 64 chains, each tried as one
   layer of the net's width on every face both ends reach. Plane-net vias are by design and not
   reviewed.
5. **Blockers** (`a7_blockers.py`): a soft A* in which other nets' unlocked copper is passable at a
   cost. It reports which nets would have to move, or "walled in".
6. **Group rip-up** (`a6_region.py`): a set of nets taken up in a box and re-laid by
   `pcb_route.complete` with via cost 40 (not 12), then tidied, filled and run through `pcb.py check`.
7. **Proof** (`a8_apply.py`): the fixes applied together, zones filled, then KiCad DRC and
   `pcb.py check` (planes, guard, holes, iron, tracks, CAD).

*Proven* means the copy passes DRC (0 unconnected, 0 violations) and `pcb.py check` (0 errors)
`[test]`. *Likely* means a path or a group re-lay was found but needs another net moved, or the
router's attempt left connections open.

**Withdrawn on proof:**
- **DEV_3V3 B shortcut, 240.9,117.7 → 236.5,122.3:** the old run passes *through* the via at
  236.5,118.7 that feeds R22.1. The run splitter cuts only at track ends, and this is the board's
  only via mid-segment (R21).
- **"One-faced" via at 236.5,118.7:** same cause.
- **Squaring the hook at C206.1** (R18): it joins by overlap, so a clean replacement disconnects it.

## The table

| id | net | layer | location (x, y) | type | excess / vias saved | proposed fix | confidence |
|---|---|---|---|---|---|---|---|
| R1 | `/CHAIN_SHLD` | F | 231.1,108.5 → 240.5,112.9 | detour | 2.0 mm (13.2 → 11.2) | vertical drop and 9 mm across by J5 replaced by one horizontal and one 45° leg | proven |
| R2 | `/KEY_LT4` | B | 145.3,110.5 → 155.9,111.9 (hump 150,106.8) | detour | 1.3 mm (14.3 → 13.0) | flatten the hump toward SW4's pin: rise only to y 108.3 | proven |
| R3 | `/LT3/SWITCH_LEG` | F | R17.2 142.1,136.3 → SW3.1 152.9,136.9 | detour | 1.0 mm (13.2 → 12.2) | north of SW3's centre hole (y 134.9), not south (y 139.5) | proven |
| R4 | `/SCLK` | B | 345.9,127.1 (J6.4 → R1.2) | jog | 0.4 mm offset, 0 mm | one straight run at y 127.1 under D2 | proven |
| R5 | `/IO36` | B | 104.1,133.7 → 258.5,126.3 (steps 254.9,129.9 and x 160–215) | detour / jog | 2.3 mm (168.3 → 166.1) | re-lay as the scratch path: one step after SW1, one before SW7 | proven |
| R6 | `/KEY_RT1` | F | via 248.5,136.1 → U8.6 248.1,132.5 | detour | 6.8 mm (10.6 vs 3.8) | loops round pin 7. Straight up is closed by a `PWR_GND` fanout via at 248.7,135.2 and its stub. Put the via west of pin 6 (or the fanout via east of pin 7) | likely |
| R7 | `/KEY_RT2` | B | U8.5 → R22.2; zig-zag 246.9–247.9, 126.1–129.5 | via / jog | 2 vias; +4.3 mm | re-lay with R11. Alone, a one-layer path is 42.9 mm and crosses CHAIN_QH_RT, CHAIN_SCK, KEY_RT4, DEV_3V3 | likely |
| R8 | `DEV_3V3` | F/B | C14.1 → via 243.5,124.9 | via / detour | 3 vias; 22.2 mm loop round D12 for a 3.4 mm hop | C14.1 straight to that via on F (3.5 mm); crosses only LED_D4's F run | likely |
| R9 | `DEV_3V3` | F/B | → U8.12, vias 249.9,126.1 and 247.7,129.9 | via | 2 vias (7.6 mm) | one F run into pin 12 from the north; the path crosses no net once pin entry is not forced to the centre | likely |
| R10 | `/KEY_RT4` | B/F | U8.3 → C22.1, vias 253.9,122.3; 253.9,125.1; 248.1,130.9; 255.7,116.5 | via | 4 vias (33.9 mm) | one-layer 32.9 mm crosses CHAIN_QH_RT and DEV_3V3: re-lay with R11 | likely |
| R11 | 22 nets | F/B | U8 / J5, box 226,103 – 252,137 | via (group) | 10 vias (101 → 91; DEV_3V3 27 → 15) | hand re-lay in one pass: decouplers' DEV_3V3 on F first, key lines next, IO bus last. The router (via cost 40) left 5 connections open | likely |
| R12 | `/CHAIN_SER_LH`, `/CHAIN_SHLD` | F/B | J4 / U9, vias 129.7,110.3 and 124.1,107.9 | via / detour | 3 vias; SER_LH 15.8 vs 7.2 mm with a U-loop under J4's pins on B; SHLD 20.7 vs 9.5 | U9's pin order crosses J4's. SER_LH over J4 on F (15.2 mm) once SCK/SHLD are re-laid. The router removed SER_LH's 2 vias but left 4 open | likely |
| R13 | `/HOP_LT_RH`, `/CHAIN_SCK`, `/CHAIN_SHLD` | F/B | J5 / U11, via 246.7,106.3 | via / detour | 1 via; HOP 16.4 vs 7.4 mm; SCK +5.2, SHLD +3.7 mm | mirror of R12: three nested loops over J5; one-layer HOP path 15.1 mm. The router got worse (24 → 28 vias, 5 open): hand job | likely |
| R15 | `/RT2/SWITCH_LEG` | F/B | R23.2 → SW6.1, vias 225.9,112.5 and 228.7,106.9 | via / detour | 2 vias; 25.4 → 13.2 mm via-free | one F run once DEV_3V3's y 108.3 run steps aside. The router's attempt cost DEV_3V3 4 vias, so hand only | likely |
| R16 | `/IO36` | F/B | R2.1 → U1.3, vias 337.3,130.9 and 337.3,127.7 | via | 2 vias for 5.4 mm | IO35 and IO36 cross between R1/R2 and TVS U1: swap channel order at U1, or take IO35 under on B | likely |
| R17 | `/SENSOR_BUFFERED_OUT` | B | R4.1 85.7,130.5 → pair tail via 78.3,122.1 | other | 12.7 mm on layer 4 over `INST_POS12`, 1 via | see below | likely (owner) |
| R18 | `DEV_3V3`, `PWR_GND` | F | C206.1 / U7.13 128.3–129.1, 124.7–126.5; U7.14 127.5,127.1 (R18b) | other | 0.9 mm hook with zig-zag; ends joined by overlap | end each track on the other's end or a pad | likely |
| R18c | `BUCK_IN` | F | 306.8,134.9 | other | two runs end 0.2 mm apart, overlapping | join the ends | likely |
| R19 | 125 signal pad entries | F/B | worst: `UMBILICAL_POS12` D2.1 347.9,133.5 (1.5 mm off centre line), D3.1 352.3,125.1 (1.1); `BUCK_IN` U5.1 1.05; `CHAIN_QH_RT` U8.9 0.83; `SCLK` R1.2 0.80 | other | — | end on the pad centre, along its axis (the router stops at the first grid cell inside the pad) | likely |
| R20 | `/IO36` / `/IO37` (also `CHAIN_QH_RT`/`IO36`, `IO35`/`LT1/SWITCH_LEG`) | B (F) | 230.5,139.5 at 0.6 mm; 141.3,139.5 (R20b) at 0.8 mm | other | — | one pitch per bus (0.8 mm). Seen across 53 parallel pairs: 0.6, 0.75, 0.8, 0.85, 1.0, 1.2, 1.4 mm | likely |
| R21 | `DEV_3V3` | B | 236.5,118.7 | other | — | via mid-run 236.5,118.1 → 122.3 (a T through a via): end the run at it; part of R11 | likely |

## Notes

**R1–R5 are proven together:** applied at once, KiCad DRC gives 0 unconnected and 0 violations, and
`pcb.py check` gives 0 errors `[test: a8_apply.py]`.

**R11 is the owner's "via transfers".** 17 of the 19 vias on the named chains are in the U8 / J5
box. `R11-u8-cluster.png` overlays the router's scratch re-lay: fewer vias, but `CHAIN_SCK` /
`CHAIN_SHLD` were left open at J4/U9/U11. Do R6–R10 and R21 as part of it.

**R17 contradicts the README.** *The routing policy* says *"Since the trace cleanup (#33) only `VS`
touches layer 4"*. But the `SENSOR_BUFFERED_OUT` branch to `R4` runs 12.7 mm on layer 4 over
`INST_POS12`, with 0.4 mm over the AGND strip `[test: a5_spot.py]`. A layer-1 path exists only
through `SENSOR_RAW`, `REF_5V` and `REF_VIN`, all locked `[test: a7_blockers.py]`. Either the
sentence or the leg changes: the owner's call. This is the net's unlocked branch, not the breath
pair.

**Acute angles:** none on unlocked nets. The only one is `INST_POS12`'s locked fanout at
339.9,113.5 (60°), which `check_tracks` accepts.

## Checked and kept

- **LED data chain** (LED_D1, D3, D4, D5, D8, D10, D12; 14 vias): re-laying all twelve data nets
  gave 16 `[test: a6_region.py led]`. LED_D5 alone goes via-free at +9.4 mm, which is not worth it.
- **`/KEY_LT1`** (2 vias): its re-lay with KEY_LT3 gave 2 again `[test: lt1]`.
- **`/IO37`, `/U0RXD` and the IO bus:** the jogs at 190.7,135.1 / 205.7,135.7 (IO37), the detour
  round H10 (U0RXD) and the bus's steps at x 176–215 all pass between the H3/H5/H10 mount keep-outs
  and the U-bolt keep-outs. The scratch path lays the same steps.
- **`DEV_3V3` y 108.3 run:** steps at H4/H6 following the pair's guards.
- **`DEV_3V3` to R40.1** (56 mm over H11): no shorter branch to any DEV_3V3 copper on F `[test]`.
- **Small steps:** `CHAIN_QH_RT` 296.9,127.5, `IO33` at L1 and `IO34` at U1 each step round another
  net's via or pad.
- **`V3V3_CHAIN_LH` / `_RH`** round J4/J5: the other pin column blocks both faces.
- **`KEY_FREE1/2`:** walled in by U7 pins and R32/R33 pads.
- **`INST_5V_A`** at J-MCU: the README's hand route (rev F).
- **J-MCU one-via signals** (CS_MOD, MOSI, SCLK, IO35, IO36, IO1, IO7, IO33, IO38): each one-layer
  path crosses 3–7 nets.
- **Long `DEV_3V3` branches at U7** (4 vias at 156.1,112.9; 2 at 131.9,117.5): single-layer only at
  twice the length.

## Figures

- **Overview:** `overview.png` marks every id.
- **Close-ups:** orange is the run under review, green dashed the proposed path (on R7–R16 the soft
  path; on R11 the router's scratch re-lay), red F.Cu, blue B.Cu: `R01-chain-shld-j5`,
  `R02-key-lt4-sw4`, `R03-lt3-leg-sw3`, `R04-sclk-jog`, `R05-io36-long`, `R06-key-rt1-u8`,
  `R07-key-rt2-u8`, `R08-dev3v3-c14`, `R09-dev3v3-u8-12`, `R10-key-rt4`, `R11-u8-cluster`,
  `R12-j4-u9-fanin`, `R13-j5-u11-fanin`, `R15-rt2-leg`, `R16-io36-u1`, `R17-buf-out-layer4`,
  `R18-ends-overlap`, `R18c-buck-in-overlap`, `R19-offcentre`, `R20-bus-pitch`,
  `R20b-bus-pitch-west` (all .png).

## For pass 2 — the scripts

The scripts are in the session scratchpad `review35/` (not in the repository): `common.py`,
`a1_runs.py`, `a2_reroute.py`, `a3_other.py`, `a4_vias.py`, `a5_spot.py`, `a6_region.py`,
`a7_blockers.py`, `a8_apply.py` (`proven.kicad_pcb` is the copy with R1–R5 applied that passed),
`render.py`, `figs.py`. The run splitter cuts only at track ends, so a via in mid-track (one here,
R21) is invisible to it: trust a reroute only after `a8_apply.py`'s DRC passes.
