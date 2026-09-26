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

Vendor geometry is **imported, not retyped**: the KS-33 and the display board
are the banked STEP solids meshed by `tools/cad.py`, and the display board's
outline is the vendor's own DXF. The one exception is the display board's
overall size, used only to centre it (OpenSCAD cannot measure an import); it is
the DXF's own DIMENSION entities.

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
- **The display is on the underside** (decided 2026-09-26), glass down in a
  through-cut in the oak bottom, recessed by `boards.display_recess`, still in
  the display band at the mouthpiece end.
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

- **Mouth end:** the first top cap plus `layout.mouth_extra`; or the
  **underside display**, which sits nearest the mouthpiece and must clear the
  left-thumb recesses — and in practice it is the display that sets it.
- **Tail end:** the **LED matrix on the top face, centred** after the keys
  (owner, 2026-09-26), with the etherCON's housing behind it; or the key
  board, the last fastener pair, the patch plug and the etherCON's depth in a
  row; or the underside chain after the right thumb (service cover, then the
  connector); or the right-thumb cluster against the tail cap.
- **The tail is stacked** (owner, 2026-09-26: "it's unacceptable to go this
  long" and "the matrix can be up higher out of the way and still allow the
  connectors"). The Matrix **hangs from the lid** under its window, wired by a
  pigtail. Under it, side by side: the extension's **right-angle USB-C plug**
  off its mouth edge, and — because the NE8FDP is a feedthrough with an RJ45
  socket at its back — the etherCON's rear socket and a patch lead's plug,
  down the left side lane. Only the connector's full-height housing queues
  behind the Matrix. The connector **stands on the floor**, and the body is
  thick enough for its socket to clear the Matrix (owner, same day: raise the
  body rather than pocket the oak — `body-thickness`, ADR 0009). `drc.echo`
  itemises "behind the Matrix", confirms the socket passes under, and gives
  the thinnest body that works. **With the matrix centred, anything in front of or
  behind it counts twice, and the gap between the hands copies the result** —
  a straight USB-C plug cost about 24 mm of body, which is why the plug is
  right-angle (`openings.usb_plug_l`).
- **The last fastener pair** stands just in front of the tail equipment,
  where the patch plug is not yet in the side lane; the LED strips stop short
  of it, because the tail equipment fills their channels.
- **The matrix window is frosted acrylic, flush with the oak top, on a lip of
  oak** (owner, 2026-09-26): a rebate in the oak top's upper face as deep as
  the acrylic, over a smaller opening through the oak and the plate. Like the
  side grooves it is a router pass, not a through-cut, so it exports on its
  own (`export/oak-rebates.dxf`); the acrylic is `export/matrix-window.dxf`.
  `drc.echo` reports the lip and the LED-to-window distance, which is what
  decides how soft the pixels look. In practice the matrix sets it.
- **The carrier's height is derived** from what it must pass over: the thumb
  boards' parts, then its own underside parts. It is centred on the gap
  between the hands **as a placeholder** — where it goes is open (below).
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
4. **The display is what sets the mouth end.** On the underside it cannot
   share the space under the left-hand run with the thumb arc, so it adds
   roughly its own length in front of the keys. *Rule: "what the mouth end
   needs".* Moving it is the largest remaining length lever.
5. **Individual thumb recesses leave almost no oak between them** at the
   ADR 0010 arc spacing. *Rule: "oak-bottom cuts at least 3 mm apart".* ADR 0010
   already asks shared-versus-individual as an M2 question; the model says
   individual recesses need the arc spread further. The same rule catches
   placeholder fasteners landing on placeholder spares — move one.
6. **The carrier and the LED strips**, made worse by the grooves, whose oak
   lips come off the interior width twice (*"interior width between the
   acrylic sides"*). The carrier at the BOM's assumed width
   does not fit between strips in the side channels at the placeholder
   diffusion gap. *Rule: "carrier fits between the LED strips".*
7. **The carrier runs under the right-hand cluster board** with little height
   between them for components on both. *Rule: "carrier clears the top
   cluster boards".* It passes; it is the tightest pass in the report.
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

1. **IDC sockets face each other across the cavity.** A mated boxed header
   with its ribbon stands ~15.6 mm off its board, and the gap between a top
   key board and a thumb board is barely more. Where a key board sits over a
   thumb board — the whole left hand, and the right hand over the right
   thumb — their headers collide. Stagger them along the body, use
   low-profile or right-angle headers, or solder the loom.
2. **A through-hole boxed header does not fit on a key board at all.** The
   board is `switch.cluster_pcb_w` wide under 14 mm switches; the header's
   9.1 mm width lands under a switch, and its pin tails stand 3 mm off the
   far face into a 2.2 mm gap to the key plate (or the thumb plate). SMT or
   board-end headers, or a wider board.
3. **The carrier has nowhere to go on a short body.** Since the tail was
   stacked it is off the tail, centred on the gap between the hands — but at
   its BOM size it is several times that gap, so it runs under both key
   runs and over both thumb clusters, into their parts and headers; its
   mated J-CHAIN and J-DISP reach the key plate. It also fills the interior
   width, so it collides with both LED strips. A smaller carrier, a split
   one, or boards that carry what it carries: an owner decision.
4. **The looms and the breath sensor** were routed to the carrier's old
   place under the Matrix; they follow wherever it goes.
5. **The M3 stations** run through the LED strips, and the middle pair
   through the carrier and the U-bolt backplate. The tail pair is clear.
6. **The tail is clear.** The etherCON, its rear socket, the patch plug,
   the USB-C plug, receptacle and lead, the Matrix and the last fastener pair
   meet nothing, and the connector fits the cavity without cutting the oak.

**The ribbons are standard flat ribbon, lying flat** down the body just off
its centreline, stacked, folding off to each socket (owner asked for standard
ribbon, 2026-09-26). Stood on edge, a 15 mm ribbon does not fit between the
thumb boards' parts and the key boards' parts — the check showed that too.

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
the diffuser standoff, and anything in the display band beyond the board. The
carrier and cluster boards are rectangles, because their outlines are M3/M4
outputs.
