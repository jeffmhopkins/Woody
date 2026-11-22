# F — copper against the fabricator's rules

Revision `940fee3d`. Limits are JLCPCB's, from
`datasheets/fab/JLCPCB-PCB-CAPABILITIES.pdf` `[ds]` unless marked. The boards
are white mask, 1 oz outer copper; the main board is 4-layer with 0.5 oz inner
copper, the other four are 2-layer `[repo: each layout.yaml]`.

## Findings, most serious first

### F1-1 — main-board: seven via holes stand in or against an SMD pad's mask opening

**Severity: high** (assembly: starved joints, not a bare-board reject)

Nodes: `R34 pin 2` `/CHAIN_SCK`, `R35 pin 2` `/CHAIN_SHLD`, `R36 pin 2` `/CHAIN_SER_LH`,
`L1 pin 1` `INST_POS12` (two vias), `R5 pin 2` and `C1 pin 2` `AGND_INST`.

| Pad | Via centre (file mm) | Hole edge to the pad's mask opening `[test]` |
|---|---|---|
| R34 pin 2 | 312.20, 124.19 | **−0.125** (hole overlaps the opening) |
| R35 pin 2 | 309.20, 124.19 | **−0.125** |
| R36 pin 2 | 315.20, 124.19 | **−0.125** |
| L1 pin 1 | 308.10, 135.10 and 309.00, 135.10 | **0.000** |
| R5 pin 2 | 80.91, 131.60 | 0.050 |
| C1 pin 2 | 85.45, 131.55 | 0.075 |
| C203 pin 2 | 69.95, 124.49 | 0.175 (holds, thin) |
| Q1 pin 3 | 351.00, 134.55 | 0.185 (holds, thin) |

The mask opening is the pad, 1:1 `[test: board mask expansion 0]`. A tented
via only stays tented where mask can stand between the pad's opening and the
hole, and the smallest mask web on white is 0.13 mm `[ds: Soldermask bridge,
black/white]`. The first seven have less than that or none, so the hole is
open to the pad and paste runs down it in reflow. On R34–R36 the via's centre
is exactly on the pad's edge, half the hole inside the opening.

Pictures: `img/F1-1-vias-in-pads-R34-R35-R36.png`,
`img/F1-1-vias-at-pad-L1.png`, `img/F1-1-vias-at-pads-R5-C1.png`.

**Proposed fix:** stand each via off so its hole edge is at least 0.25 mm from
the pad (via centre at least 0.40 mm from the pad's edge), on a short neck.
The thirteen LED ground vias already sit at exactly 0.25 mm `[test]` and are
the pattern to copy. C203 pin 2 and Q1 pin 3 are worth moving in the same pass.

### F1-2 — the "no via in a pad" check tests the via's centre, not its hole

**Severity: medium** (why F1-1 passed)

`tools/pcb.py:1985` reports a via only when its centre is strictly inside the
pad's bounding box `[repo]`. A centre on the edge, or 0.2 mm outside it with a
0.15 mm hole radius, passes. **Proposed fix:** test hole edge to pad edge
against a mask dam (0.25 mm suggested) instead.

### F2-1 — umb-adapter: two unplated post holes are 0.15 mm from the board edge

**Severity: high** (bare board: the web breaks out or the fab queries it)

Node: `J1` (NE8FAV), the two Ø1.7 mm plastic-post holes at (82.70, 119.45) and
(94.30, 119.45); board edge at y = 118.45 `[test]`.
`[calc: 119.45 − 0.85 − 118.45 = 0.15 mm]`. The routed outline is ±0.2 mm at
regular precision and ±0.1 mm at high `[ds: Outline, Routed]`, so the web can
come out as nothing. The banked page gives no hole-to-edge figure; common
practice is 0.5 mm or more `[from memory]`. The outline is the connector's
flange `[repo: umb-adapter/layout.yaml]`, which is why the posts land there.

Pictures: `img/F2-1-adapter-posts-at-edge.png`,
`img/F2-1-adapter-posts-closeup.png`.

**Proposed fix, either:** grow that edge of the board by about 1 mm if the tail
cap has the room (a body-CAD question), or open the two holes into 1.7 mm
notches in the outline (unplated slots of 1.0 mm and wider are standard
`[ds: Min. Non-Plated Slots]`).

### F3-1 — the 1.27 mm headers' plated holes have a 0.185 mm ring

**Severity: medium**

Nodes: `J4`, `J5`, `J1` on main-board; `J1` on key-board-lh, key-board-rh and
matrix-carrier. Hole 0.70 mm, pad 1.07 mm across the pitch
`[calc: (1.07 − 0.70) / 2 = 0.185]` `[test]`.

Limits `[ds: PTH annular ring]`: 2-layer, 0.25 mm recommended and 0.18 mm
absolute minimum; multilayer, 0.20 mm recommended and 0.15 mm absolute. So the
three 2-layer boards clear the absolute minimum by 0.005 mm, and the main
board is under the recommended figure. The pads are 1.5 mm long the other way,
so a drill that wanders across the pitch thins a ring but does not open a
joint. Picture: `img/F3-1-header-rings-J4.png`.

**Options:** accept it (a 1.27 mm pitch forces something close to this), or
widen the pads to 1.12 mm, which gives a 0.21 mm ring and leaves 0.15 mm
between pads: over the 0.13 mm white-mask web and JLC's 0.10 mm spacing, but
under the boards' own 0.2 mm clearance rule, so it needs a recorded exception.
A smaller hole is not advised without the header's drawing: a 0.4 mm square
pin is 0.57 mm corner to corner `[calc]` `[from memory: pin size]` and the hole
tolerance is −0.08 mm `[ds]`.

### F4-1 — main-board: both inner planes run 0.3 mm from the U-bolt cut-outs

**Severity: medium**

Nodes: `INST_POS12` (In2) and `PWR_GND` (In1), at the two Ø4.0 mm cut-outs
drawn on `Edge.Cuts` at (193.0, 111.5) and (193.0, 131.5) `[test]`. That meets
the 0.2 mm copper-to-routed-edge minimum `[ds]`, but the routed edge is
±0.2 mm, so the 12 V plane can finish 0.1 mm from the wall of a hole a steel
U-bolt leg passes through. The keep-outs there cover the top face only
`[test: rule areas "U-bolt leg 1 top", "U-bolt leg 2 top", F.Cu]`.
Picture: `img/F4-1-ubolt-cutouts-12V-plane.png`.

**Proposed fix:** a keep-out on In1 and In2 that pulls both planes back 1 mm
round each cut-out.

### F5-1 — J1's ground pins join their plane with no thermal relief

**Severity: low**

Nodes: `J1` pins 4, 6, 8, 14, 20 `PWR_GND`, on main-board In1 and on
matrix-carrier B.Cu `[test]`. ADR 0030 records this for the carrier; the main
board's end is the same. These are hand-soldered pins `[repo: hand-assembly
lists]` and will want more heat. Every other through-hole ground pin has two
to four 0.4 mm spokes `[test]`: the chain headers three, the switches four,
`U5 pin 2` and `J6 pin 6` two and three. No SMD pad on any board sits on a pour, so no
SMD ground pad is heat-sunk. Pictures:
`img/F5-1-J1-ground-pins-no-relief-main.png`,
`img/F5-1-J1-ground-pins-no-relief-carrier.png`.

**Proposed fix:** none needed if the owner accepts it for the main board as
for the carrier; otherwise one spoke per pin on In1.

### F6-1 — the 2-layer boards' vias and large plated holes have a 0.2 mm ring

**Severity: low**

Nodes: the vias on key-board-lh (4), key-board-rh (4) and matrix-carrier (1),
0.7 mm on a 0.3 mm hole; the KS-33 pin pads, 3.4 mm on 3.0 mm; the carrier's
mount pads, 3.1 mm on 2.7 mm `[test]`. All 0.2 mm: over the 2-layer absolute
minimum of 0.18 mm, under the recommended 0.25 mm `[ds]`. On the 4-layer main
board 0.2 mm is the recommended figure. Picture: `img/F6-1-two-layer-via.png`.

**Proposed fix:** 0.8 mm vias on the three 2-layer boards (nine vias). The
switch and mount pads are the owner's call: 3.5 mm and 3.2 mm pads would reach
0.25 mm.

### F7-1 — supply return through spokes in 0.5 oz inner copper

**Severity: advisory**

Nodes: `J6 pin 6` (the umbilical's `PWR_GND` pin, three 0.4 mm spokes into In1) and
`U5 pin 2` (the regulator's ground, two) `[test]`. By IPC-2221's internal-layer
formula a 0.4 mm × 0.0152 mm spoke carries about 0.34 A for a 10 °C rise
`[calc: 0.024 × 10^0.44 × (15.75 mil × 0.6 mil)^0.725]`, so three carry about
1.0 A against the figure `umbilical-current`. The formula is for long traces
and these spokes are 0.3 mm long, so the real margin is larger. No change
proposed; four spokes on `J6 pin 6` would cost nothing.

## Checked and passed

| Check | Worst on any board `[test]` | Limit `[ds]` |
|---|---|---|
| Track width | 0.20 mm | 0.10 (2-layer), 0.09 (multilayer) |
| Copper to copper, different nets, every layer | 0.20 mm | 0.10 / 0.09 |
| Via hole to other copper | 0.40 mm | 0.20 |
| Plated pad hole to other copper, all layers | 0.385 mm | 0.28 (0.35 recommended); 0.30 inner |
| Unplated hole to copper | 0.28 mm | 0.20 |
| Hole to hole | 0.49 mm (via to pad hole) | 0.20 via, 0.45 pad |
| Copper to board edge | 0.30 mm | 0.20 |
| Drill sizes | 0.30 mm smallest | 0.15 (0.30 is the no-surcharge size) |
| Plated slot (adapter) | 2.0 × 8.6 mm | 0.5 wide, length ≥ 2 × width |
| Mask web between openings | 0.20 mm | 0.13 on white |
| Mask opening to foreign copper | 0.20 mm | 0.09 |
| Vias tented | all, both faces; no via aperture in any mask Gerber | — |
| Silk text / line | 1.0 mm high, 0.18 / 0.15 mm | 1.0 / 0.15 |
| Silk on pads, holes, edge | none | 0.15 to a pad |
| Plane features under 0.2 mm (slivers) | none | — |
| Acute track joins | none outside a pad | — |
| Dangling track ends | none | — |
| Outline: inside corners, notches under 1 mm | none | — |
| `fab/` Gerbers and drills against the boards | re-exported with KiCad 9.0.9, identical | — |

**Order as tented, not plugged.** Plugging wants vias no wider than 0.5 mm and
0.35 mm from any opening `[ds: Plugged vias]`; these are 0.7 mm.

**Tombstoning.** Every two-pad chip is 0805 or 1206 except six 0603
resistors on the main board, and none has a pad on a pour `[test]`. The
largest copper imbalance is two 0.4 mm tracks against one 0.25 mm, on 0805
parts, which is not a tombstoning risk at that size. The real assembly risk is
F1-1.

**Current, IPC-2221, 1 oz outer copper, 10 °C rise `[calc]`:** 0.25 mm carries
0.87 A, 0.4 mm 1.23 A, 0.5 mm 1.45 A, 0.6 mm 1.65 A.

| Net | Narrowest track `[test]` | Load `[repo: power-entry-instrument.md]` | Verdict |
|---|---|---|---|
| `UMBILICAL_POS12` | 0.5 mm main, 0.6 mm adapter | `umbilical-current`; the limiter's worst-case trip is higher | passes at the trip |
| `INST_POS12` | In2 plane, 28 vias | as above | passes |
| `INST_5V_A` | 0.6 mm main trunk; 0.4 mm on the carrier (28.5 mm) | the 5 V rail's clamp-legal worst case | passes; about 35 mΩ on the carrier `[calc: 0.0172 / (0.4 × 0.035) × 0.0285]` |
| `V3V3_CHAIN_*`, `DEV_3V3` | 0.4 mm, 0.2 mm | `key-scan-current` | far inside |

The one via on `INST_5V_A` feeds only the level shifter and its capacitor
`[test]`, not the trunk.
