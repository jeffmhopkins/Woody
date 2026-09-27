# Body CAD — design notes

> **Status:** first model, 2026-09-26. Back to the [README](README.md).

How the stack is modelled, where the numbers come from, and what the first
model found. **This page does not restate dimensions or DRC results** — they
move, and a number copied here is the defect this repository keeps finding.
Values live in `config/body.yaml` and `config/key-layout.yaml` (each with a
source and a status); measured results live in [`drc.echo`](drc.echo),
regenerated on every build.

## Where the numbers come from

Three kinds, and `config/body.yaml` marks every leaf with one:

- **settled** — read off a banked document or decided in an ADR. The KS-33
  geometry, the NE8FDP flange and holes, the Matrix board outline, the plate
  thickness (the register's `plate-thickness`).
- **nominal** — an ADR's working estimate: the oak thicknesses, the length
  budget, the side thickness.
- **tbd** — no document gives a number, so the model carries a placeholder and
  a `decided_by`. `drc.echo`'s second line lists every one in play, so no
  result can quietly rest on a guess.

Vendor geometry is **imported, not retyped**: the KS-33 is the banked STEP
solid meshed by `tools/cad.py`, and the etherCON is drawn from its banked
drawing.

## How the stack is modelled

- **The lid** is the oak top **on** the aluminium key plate — the plate is
  underneath, because keys are **flush with the top face at full travel**
  (decided 2026-09-26, ADR 0009). The oak top's thickness is not a parameter:
  it is the cap's height above the seat less the travel, derived in the model
  and printed in `drc.echo`. The oak carries one clearance hole per cap and
  nothing else; the fasteners stop in the plate. The two key boards are
  screwed up to the plate's underside on M2 standoffs pressed into it (ADR
  0020), at the depth the KS-33's pins set (`docs/reference/ks33-geometry.md`;
  `switch.pcb_below_seat`). Each board is a rectangle across the cavity with a
  standoff in each corner, the standoff's edge distance from every switch
  cutout (*"key-board standoffs clear of the switch cutouts"*); the
  standoff's length is derived (*"key-board standoff length (derived)"*).
  The key board's chain header's through-hole pin tails come up through the
  board toward the grounded plate and stop short of it (*"J-CHAIN pin tails
  clear of the key plate"*), so the plate is not cut over them
  (2026-09-27; the first layout cut a window there).
- **Thumb keys are flush with the bottom face at full travel** too (same date).
  The thumb plate is on the oak bottom's inside face, so the oak bottom is
  derived by the same rule as the oak top.
- **There is no display board** (owner, 2026-09-26: "remove the upper
  display ... we can do all this with the matrix led, keep things more
  compact and cleaner"; ADR 0015). The LED matrix on the top face is the
  instrument's only display, configuration is over USB, and the body lost the
  display band at the mouth end.
- **The sides sit between the oak panels, in grooves** (decided 2026-09-26).
  Oak top and bottom run the full width; each acrylic side is one sheet
  standing in a groove along each panel's inner face, behind an oak lip
  (`stack.side_inset`, `groove_depth`, `groove_clear`). Glued into the bottom
  grooves, the U is still one sub-assembly; the top grooves locate the lid.
  **The grooves are the one cut in the stack that is not a through-cut** — a
  saw or router pass, exported on their own as `export/oak-grooves.dxf` so
  the through-cut outlines stay clean. The plate sits between the sides.
- **Thumb keys** mount upside down in a thumb plate on the oak bottom's inside
  face; the through-cut in the oak is the recess (ADR 0009). Each thumb
  cluster has its own plate.
- **Key positions**: a key with `x`/`y` in `config/key-layout.yaml` is placed
  there. A key without one is placed on the provisional layout in
  `config/body.yaml`, where each run's spacing is its length over its gaps —
  there is deliberately no separate pitch value.
- **Every part is a 2D module** in its own sheet frame; the assembly only
  places them. `export/*.dxf` are those modules exactly.

## The length is derived

Since 2026-09-26 the owner's rule is *minimize total length*: the body is the
keys, a little at the mouth, and room for the connector at the tail. So the
model computes the length rather than reading it (`config/key-layout.yaml`'s
`envelope.length` is null), and `drc.echo` prints it with what set each end.
Several things can claim each end, and the largest wins:

- **Mouth end:** the first top cap plus `layout.mouth_extra`; the first
  thumb recess; the breath trap, which sits across the mouth band before the
  first key board; or the breath sensor, which must stop short of the first
  thumb row's pins — and then the equal bands (below).
- **Tail end:** the **LED matrix on the top face, centred** after the keys
  (owner, 2026-09-26), with the etherCON's housing behind it; or the key
  board, the last fastener pair, the patch plug and the etherCON's depth in a
  row; or the right-thumb cluster against the tail cap. (There is no service
  cover since 2026-09-26.)
- **The tail is stacked** (owner, 2026-09-26: "it's unacceptable to go this
  long" and "the matrix can be up higher out of the way and still allow the
  connectors"). The Matrix **sits against the oak top** under its window,
  wired by a ribbon: the key plate stops short of it, so the board's top
  face is on the oak and its LEDs stand up into the window opening, under the
  acrylic (owner, same day: "led matrix tighter to the acrylic"). Under it, side by side: the extension's **right-angle USB-C plug**
  off its mouth edge, and — because the NE8FDP is a feedthrough with an RJ45
  socket at its back — the etherCON's rear socket and a patch lead's plug,
  down the left side lane. Only the connector's full-height housing queues
  behind the Matrix. The connector **stands on the floor**, and the body is
  thick enough for it (owner, same day: set the body rather than pocket the
  oak — `body-thickness`, ADR 0009). Past the plate's end the ceiling is the
  oak top, so it is the connector's flange, floor to oak, that sets the
  thickness. `drc.echo` itemises "behind the Matrix", confirms the socket
  passes under, and gives the thinnest body that works. **With the matrix centred, anything in front of or
  behind it counts twice, and the gap between the hands copies the result** —
  a straight USB-C plug cost about 24 mm of body, which is why the plug is
  right-angle (`openings.usb_plug_l`).
- **The last fastener pair** stands just in front of the tail equipment,
  where the patch plug is not yet in the side lane.
- **One LED strip, on the main board** (ADR 0016, ADR 0017): LEDs up down
  the board's centreline, between the thumb switches' two rows of pins, from
  past the breath sensor to the board's tail end, lighting both sides through
  the cavity. How evenly the cavity lights the sides is an M6 prototype
  question.
- **Every outer oak edge is rounded, as if sanded** (owner, 2026-09-26):
  the top and bottom panels' long edges, the lips beside the acrylic, and
  both end caps' outer faces and corners, at `stack.edge_r`. It goes on after
  cutting (router or sandpaper), so the DXFs carry square outlines except
  the caps' corners. The radius stays under the lip width
  (*"sanded edge radius leaves the lips a flat"*). Both end caps are oak.
- **The matrix window is frosted acrylic, flush with the oak top, on a lip of
  oak** (owner, 2026-09-26): a rebate in the oak top's upper face as deep as
  the acrylic, over a smaller opening through the oak lip. Like the
  side grooves it is a router pass, not a through-cut, so it exports on its
  own (`export/oak-rebates.dxf`); the acrylic is `export/matrix-window.dxf`.
  `drc.echo` reports the lip and the LED-to-window distance, which is what
  decides how soft the pixels look. In practice the matrix sets it.
- **There is no carrier board, and one main board** (ADR 0017; owner,
  2026-09-26: "instead of individual bottom boards, and the center board,
  maybe we can do one big long board?"). The thumb switches, both thumb
  registers and the carrier's circuits are on one board at the thumb level,
  from the mouth cap to the end of the right hand, the full width inside the
  sides. Its parts face up; the two key boards connect to it by ribbons (below);
  the Matrix's ribbon and the patch lead end on it. It has holes
  over the U-bolt's nuts, notches at the screws (one bite where a notch and a
  hole would leave a sliver between them), and standoffs off the oak or
  the thumb plates wherever nothing else is (*"main board standoffs found
  clear of everything"*); the soldered thumb switches carry it between them.
  (Before it: a centre board stacked between the thumb boards and the key
  boards — that history is in git and ADR 0017.)
- **Its parts have room** — `drc.echo` prints the height under the key boards
  and where none is overhead, and both clear the regulator block and the
  breath sensor. **The breath sensor is at the mouth end** (owner, with this
  board), beside the breath trap, ports toward the tail: the thumb switches'
  pins leave the strip the centreline band, and the sensor is too wide to sit
  beside it (*"breath sensor fits at the mouth end"*; the mouth end also
  claims room for it, *"what the mouth end needs"*).
- **Board clearances are real ones** (`boards.board_clear`): the owner
  rejected a model that put one board 0.5 mm over another's parts
  (2026-09-26: "once components are installed you'd have issues").
- **Between:** the key gaps, and the space between the hands.

**Equal bands (owner, 2026-09-26).** The space before the left hand and the
space between the hands are the same: the larger either needs, measured as
the plan drawing labels them (body end to first key centre, last left key to
first right key). `layout.equal_bands` switches it; `layout.gap` is then only
a minimum.

**The gap between the hands matches the keys-to-matrix gap (owner, same
date)** — the clear space from the last left cap to the first right cap equals
the clear space from the last cap to the matrix window's near edge
(`layout.gap_matches_matrix`). It overrides the equal bands for the gap, so
the mouth end and the gap are no longer equal; `layout.gap` stays a minimum,
for the U-bolt and thumb rest underneath. `drc.echo` prints both clear gaps.

**The LED matrix is centred after the keys (owner, same date)** — midway
between the last cap's slot edge and the tail face — and **only the tail
grows for it** (`layout.matrix_centred`). The connector still has to fit
behind the matrix, so the tail must be at least the cap edge plus twice
(half the board + clearance + connector depth). That makes the tail the
longest band; `drc.echo` prints what the tail needs and confirms the centring.

Every render aims at the body's centre or tail (`origin` in `outputs.yaml`),
so a length change reframes nothing.

## What the first model found

Each item is a rule in `drc.echo`; read the current value there. These are
the questions M4 has to answer, and several contradict something an ADR
currently says. None has been fixed by editing a document: fixing them is a
decision, not a correction.

1. **The etherCON panel stack — resolved by the owner.** ADR 0009 put the
   connector's screws through the oak tail cap into a backing plate, which
   exceeded the NE8FDP's maximum panel. The owner freed the mounting
   (2026-09-26): flange and chassis sit behind the tail cap, and the panel
   limit no longer applies.
2. **The etherCON body is taller than the cavity — resolved by the owner.**
   The body is now thick enough to take the connector standing on the floor,
   with its rear socket under the Matrix (`body-thickness`, 2026-09-26).
   *Rules: "etherCON body inside the cavity height", "body thickness takes
   the etherCON on the floor".*
3. **The Matrix's USB-C reaches the tail through an extension** (owner,
   2026-09-26). Its port cannot reach the face — the etherCON fills the
   tail's depth — so a panel-mount USB-C extension runs to a receptacle
   beside the connector (`CBL-USB-EXT`). **The receptacle stands on end**
   (`openings.usb_slot_portrait`, 2026-09-26): the rotated etherCON's flange
   already sits against one side, and a landscape slot beside it left too
   little oak to the flange on the face the cables plug into. On end it sits
   centred in the lane between the flange and the other side; USB-C is
   reversible, so the user never sees the difference. Moving the etherCON
   (already against the side), widening the body or a backing plate were
   the alternatives; un-rotating it would give the width back but stand its
   flange taller than the cavity behind the cap.
   **The plug has to reach it, and it has no screw ears** (2026-09-26). The
   tail cap is much thicker than the panel a panel-mount receptacle is made
   for, and a plug's overmould is bigger than the receptacle's cutout, so the
   cap is **pocketed from the tail face**, overmould-sized, down to a thin
   panel; the receptacle's nose passes that panel's slot, its face level with
   the pocket floor (`openings.usb_overmold`, `usb_panel_t`, `usb_nose_l`).
   The pocket is a router pass: `export/tail-cap.dxf` carries the slot, the
   render shows the pocket. On end, a receptacle's screw ears would run up
   and down the face and land outside the cavity, so it is **earless**,
   clamped against the panel from behind (`openings.usb_mount`) — the clamp
   is not modelled. A front-mounted receptacle was the alternative; its
   flange would need the tail face's width that the lane does not have.
   *Rules: "USB-C extension receptacle beside the etherCON flange", "tail cap
   web between the USB-C cutout and the etherCON flange", "USB-C plug
   overmould reaches the receptacle", "USB-C receptacle mount inside the
   cavity"; the cable run is an INFO line.*
4. **The display set the mouth end — resolved by the owner.** It is gone
   (ADR 0015), and the mouth end is now the equal band. *Rule: "what the
   mouth end needs".*
5. **Thumb recesses and the oak between them.** *Rule: "oak-bottom cuts at
   least 3 mm apart".* Since the thumb keys went to two rows across the body
   either side of each rest, at the top keys' pitch with one oak slot per row,
   and the spare cutouts went (owner, 2026-09-26), every cut passes. The
   left thumb's tail row is what nears the U-bolt legs (*"U-bolt legs clear
   of the thumb recesses"*). The arc and spares
   before it left 0.5 mm webs; that history is in git.
6. **The regulator block** fits wherever it stands on the main board.
   *Rule: "regulator block fits where it stands".*
7. **The main board is placed by the layout** — its length by the mouth cap
   and the right hand, its width by the sides — and each key board's chain
   header, with the main board's under it, is placed clear of the switches by
   the model (*"chain headers on the … boards clear of the switches"*).
8. **M3 into a 1.20 mm plate** is about two threads. The BOM already says
   "insert or tapped boss"; the model says plain tapping is not one of the
   options.

## The interference check

`mechanical/clash.txt` is every named solid in the model intersected with
every other (`tools/cad.py`, manifold3d), regenerated on every build. Parts
that go INTO each other by design are excused in `mechanical/clash-allow.yaml`,
each with its reason; a rule that stops matching is reported. Every solid is
an envelope — many sizes are tbd in `config/body.yaml` — so a clean pair is
only as good as those envelopes. Group the report's lines by these causes
(read the counts there, not here):

1. **Each key board is on a ribbon** (owner, 2026-09-26, ADR 0017), not a
   blind-mating header — and since 2026-09-27 a **through-hole IDC** one
   (ADR 0017's amendment): a 2×6 1.27 mm shrouded right-angle header on each
   board (`boards.chain_hdr_*`), the key board's **hanging from its underside
   directly over the main board's** — stacked, at the same place along the
   body — both in the far band beside the LED strip and **both mouths facing
   the same way along the body**, clear of the switch pins above and below.
   The ribbon comes out of both plugs and **folds back on itself: closed, it
   is a flat hairpin lying along the body**: the `-RN2` cable leaves the main
   board's socket upward and the key board's downward, facing each other,
   and both legs lie between the two plugs' heights, running the same way to
   the fold, so it never stands across the LED strip's light
   (`renders/section-ribbon.png`; *"key-chain ribbon closed: hairpin leg and
   fold radius"*, *"key-chain ribbon fold no tighter than its bend radius"*,
   *"key-chain ribbon hairpin inside the body"*, *"key-chain ribbon hairpin
   clear of the lid screws"*). Which way each hand's hairpin folds is
   `routing.chain_fold`, which says why. **Its length is the service
   position's** (owner: long enough "to have the top off and still connect
   the ribbon before tightening down"): the lid laid face down beside the
   body off its far edge, the body standing on its U-bolt, the ribbon running
   up from the main board over the far side's top edge and down to the key
   board (`routing.chain_service`, `routing.chain_slack`; *"key-chain ribbon
   length (derived)"*). The cable is ordered by *"key-chain cable to order
   (FFSD length code)"*, which is the FFSD part number's length field, in
   inches. To take the lid off, lift it, lay it beside the body and unplug
   the two sockets. The key header's pin tails stop short of the plate
   (above).
2. **The hardware pages follow**: `hardware/interfaces/key-chain-loom/`
   describes the two ribbons (`J-CHAIN`, `CBL-CHAIN`) and the thumb chain in
   traces, and `chain-connectors` is derived from them. The key-board header
   is the main board's part mounted upside down, facing the same way, and the
   cable is ordered with its second socket's notch reversed (`-RN2`), which
   is what sends the two ends' cables toward each other; that makes the key
   board's pin numbers differ from the main board's — `key-chain-loom.md`
   says how.
3. **The breath tube** is short: mouth cap, trap, then across over the strip
   and back onto the sensor's port, all in the mouth band; the board has a
   slot in front of the sensor's lower port.
4. **The middle M3 pair and the U-bolt backplate share a station**, the
   middle of the gap between the hands. Across the body the plate stops
   short of the pair's clearance circle, by more than it floats on its legs
   (`hardware.backplate_clear`), and is located by the U-bolt's legs alone,
   so the screws never pass through it and it comes out with the U-bolt
   (*"U-bolt nuts bear on the backplate, which stops at the gap fasteners'
   clearance"*). How far the fasteners stand in from the sides
   (`hardware.fastener_inset`) is a window between two rules: the oak between
   each clearance hole and the side groove's wall, where the oak ends
   (*"oak-bottom cuts inside the U"*), and the middle pair's counterbores
   against the U-bolt's leg holes (*"oak-bottom cuts at least 3 mm apart"*).
   A wider U-bolt or a bigger screw closes the window; `config/body.yaml`
   gives both bounds. **The screws are low-head** (`hardware.fastener_head_h`):
   the counterbore comes up beside the side groove, and a standard socket
   head's counterbore would share the groove's depth across a sliver of oak
   (*"fastener counterbores clear of the side grooves"*, *"fastener heads at
   or below the bottom face"*). **The U-bolt is M3, and the main board sized
   it**, not the load: its nuts stand up through holes in the main board
   beside the LED strip, an M4 or M5 nut's hole reaches under the strip, and
   widening the span to clear it closes the fastener window
   (`hardware.ubolt_rod_d` has the arithmetic; *"LED strip clear of the U-bolt
   nut holes"*, *"main board neck at the U-bolt station"* — the strip of board
   every trace between the two halves must pass). (The stations ran through
   the side strips until ADR 0016 removed them.)
5. **The Matrix and the umbilical are wired onto the main board's tail
   end** (owner, 2026-09-26). The Matrix, on the lid, has a flat 24-way
   ribbon soldered to its pad rows, two test points and two button pads
   (allocation on `CBL-MCU-RIBBON`, ADR 0018): out past its mouth edge above the patch plug, down in the gap
   between the right-hand key board's end and the plug, and level into
   J-MCU beside the regulator block; it unplugs there when the lid comes
   off. The etherCON's patch lead runs from its plug in an S-bend at the
   lead's minimum bend radius (`routing.umb_bend_r_per_od`) into J-UMB, which
   the model places as far in as that bend needs (*"J-UMB on the main
   board…"*). The LED strip stops short of J-MCU. The rows are `J-MCU` and
   `CBL-MCU-RIBBON` (`hardware/carrier/`), `J-UMB` and `CBL-UMB-PATCH`
   (`hardware/interfaces/spi-link/`).
6. **The tail is clear.** The etherCON, its rear socket, the patch plug,
   the USB-C plug, receptacle and lead, the Matrix and the last fastener pair
   meet nothing, and the connector fits the cavity without cutting the oak.

Found by the check and fixed as model bugs, not findings: the oak bottom's
missing counterbores, thumb boards drawn with switch holes, the display cut
too tight for the STEP's glass overhang, the etherCON housing drawn through
the tail cap, and several of the check's own first routings.

**Also found, outside the model:** the MPXV4006DP (case 1351-01) is a
**surface-mount** part (its datasheet's p.1 ordering table). It is now
soldered to the main board, with no socket; how it is fitted and swapped is in
`hardware/interfaces/breath-sense-link/breath-sense-link.md`, "Mounting".

**Found by the first PCB layout (2026-09-27, `docs/reference/tooling.md` §4):**
the key boards' ribbon connector was deeper than the envelope assumed, and
on a 1.6 mm board the KS-33's pins would show only about 0.1 mm below it.
Both were settled in ADR 0020: the key boards are `boards.key_board_t` thick,
and the connector's envelope now comes from the IDC header's banked full print
(`boards.chain_hdr_*`, ADR 0017's 2026-09-27 amendment). The model
now exports each key board's outline (`export/key-board-*.dxf`) and its
switch and connector positions (`export/pcb-geometry.echo`), which the PCB is
placed from.

## Not modelled yet

The thumb rest lip, gasket beads, plate stiffening (ADR 0002 — open, and it changes the lid),
and the diffuser standoff. The main board is a rectangle because its
outline is an M3/M4 output. The key boards are rectangles by decision (ADR
0020 point 3): their outlines are generated now (`export/key-board-*.dxf`),
and only their size moves, with the switch positions, which are provisional
until M3.
