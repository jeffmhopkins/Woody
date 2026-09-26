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
  nothing else; the fasteners stop in the plate. The top cluster boards hang
  under the plate in the cavity, at the depth the KS-33's pins set
  (`docs/reference/ks33-geometry.md`; `switch.pcb_below_seat`).
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
Three things can claim each end, and the largest wins:

- **Mouth end:** the first top cap plus `layout.mouth_extra`; the first
  thumb recess; or the breath trap, which sits across the mouth band before
  the first key and thumb boards — and then the equal bands (below).
- **Tail end:** the **LED matrix on the top face, centred** after the keys
  (owner, 2026-09-26), with the etherCON's housing behind it; or the key
  board, the last fastener pair, the patch plug and the etherCON's depth in a
  row; or the underside chain after the right thumb (service cover, then the
  connector); or the right-thumb cluster against the tail cap.
- **The tail is stacked** (owner, 2026-09-26: "it's unacceptable to go this
  long" and "the matrix can be up higher out of the way and still allow the
  connectors"). The Matrix **sits against the oak top** under its window,
  wired by a pigtail: the key plate stops short of it, so the board's top
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
- **One LED strip, on the centre board** (ADR 0016): LEDs up along the
  board's tube-side edge, the board's length less an inset, lighting both
  sides through the cavity. There are no side strips, so the tube lane runs
  just inboard of the fastener line and the board widens to the far side;
  the breath sensor takes the far side, and the tube rises to its port
  before it crosses the strip (*"breath tube crosses the strip clear of it"*).
  How evenly the cavity lights the sides is an M6 prototype question.
- **The matrix window is frosted acrylic, flush with the oak top, on a lip of
  oak** (owner, 2026-09-26): a rebate in the oak top's upper face as deep as
  the acrylic, over a smaller opening through the oak lip. Like the
  side grooves it is a router pass, not a through-cut, so it exports on its
  own (`export/oak-rebates.dxf`); the acrylic is `export/matrix-window.dxf`.
  `drc.echo` reports the lip and the LED-to-window distance, which is what
  decides how soft the pixels look. In practice the matrix sets it.
- **There is no carrier board** (owner, 2026-09-26: "we don't need a
  carrier"): the carrier's circuits are on **the centre board**, one flat
  board lying between the thumb boards and the key boards, the length of the
  hands and across the gap between them
  (owner, same day: "a center board that stacks between the upper and lower
  key boards", after trying a board on edge down the side and a wider body
  for it, and going back to 57 mm). Each thumb board plugs into the key board
  above it through a stacking header that passes through the centre board,
  so the key chain runs through all three, and the Matrix's pigtail and the
  patch lead end on it. It sits between the tube
  lane and the far LED strip, on spacers onto the thumb boards and
  standoffs off the oak.
- **Its parts have little height under the keys**, because the board is
  stacked between two others with real clearances (`boards.board_clear`):
  `drc.echo` prints the room. **In the gap between the hands, where no key
  board is overhead**, they have up to the plate, so the breath sensor goes
  there — mid-body, not at the tail end the owner had confirmed for the side
  board: under the right-hand keys there is no height for it. The regulator
  block (one, for the one dev board left) does not fit under the keys as
  specified — *rule "regulator block fits under the key boards"* — so it
  needs low-profile parts.
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
   beside the connector (`CBL-USB-EXT`). *Rules: "USB-C extension receptacle
   beside the etherCON body", "tail cap web between the USB-C cutout and the
   etherCON flange"; the cable run is an INFO line.*
4. **The display set the mouth end — resolved by the owner.** It is gone
   (ADR 0015), and the mouth end is now the equal band. *Rule: "what the
   mouth end needs".*
5. **Individual thumb recesses leave almost no oak between them** at the
   ADR 0010 arc spacing. *Rule: "oak-bottom cuts at least 3 mm apart".* ADR 0010
   already asks shared-versus-individual as an M2 question; the model says
   individual recesses need the arc spread further. The same rule catches
   placeholder fasteners landing on placeholder spares — move one.
6. **The regulator block** stands beside the key boards since the board
   widened (ADR 0016), with the height to the lid. *Rule: "regulator block
   fits where it stands".* Under a key board it would need low-profile parts.
7. **The centre board is placed by the layout** — its length by the key
   runs, its width by the tube lane and the far side — and its stacking headers
   are placed between two thumb keys, clear of both boards' switches, by the
   model (*"stacking header … clear of both boards' switches"*).
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

1. **No cluster board faces another's connector any more.** Each thumb
   board plugs into the key board above it through one 2 × 6 stacking header
   at 2.0 mm pitch (2.54 will not fit between two switches' pins, 19 mm
   apart), passing through the centre board. It engages as the lid closes,
   so it must blind-mate, and its height is the board gap, not a stock size.
2. **No ribbons remain inside the body.** **The hardware pages do not
   follow yet:** `hardware/interfaces/key-chain-loom/`, the J-CHAIN,
   WIRE-LOOM and HDR-DEV rows, and the register's `chain-connectors` still
   describe IDC ribbons and a dev board plugged into one carrier, and change
   when the owner confirms this layout.
3. **The breath tube** runs the tube lane beside the centre board, between
   the cluster boards' parts, to the gap between the hands and onto the
   sensor's port; the board has a slot in front of the lower port.
4. **The middle M3 pair** runs through the U-bolt backplate, which also
   overlaps the thumb plates. (The stations ran through the side strips until
   ADR 0016 removed them.)
5. **The tail is clear.** The etherCON, its rear socket, the patch plug,
   the USB-C plug, receptacle and lead, the Matrix and the last fastener pair
   meet nothing, and the connector fits the cavity without cutting the oak.

Found by the check and fixed as model bugs, not findings: the oak bottom's
missing counterbores, thumb boards drawn with switch holes, the display cut
too tight for the STEP's glass overhang, the etherCON housing drawn through
the tail cap, and several of the check's own first routings.

**Also found, outside the model:** the MPXV4006DP (case 1351-01) is a
**surface-mount** part (its datasheet's p.2 ordering table), not the THT part
`hardware/bom.csv` U-BREATH and SKT-BREATH describe — and a SIP socket cannot
hold it. That is a BOM decision, not a CAD one, and is left open here.

## Not modelled yet

The thumb rest lip, gasket beads, plate stiffening (ADR 0002 — open, and it changes the lid),
and the diffuser standoff. The
centre board and cluster boards are rectangles, because their outlines are
M3/M4 outputs.
