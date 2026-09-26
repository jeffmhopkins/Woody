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
- **Tail end:** the last key board, a fastener pair and the etherCON's depth;
  or the underside chain after the right thumb — service cover, Matrix window,
  then the connector; or the right-thumb cluster against the tail cap.
- **Between:** the key gaps, and `layout.gap` between the hands.

Every render aims at the body's centre or tail (`origin` in `outputs.yaml`),
so a length change reframes nothing.

## What the first model found

Each item is a rule in `drc.echo`; read the current value there. These are
the questions M4 has to answer, and several contradict something an ADR
currently says. None has been fixed by editing a document: fixing them is a
decision, not a correction.

1. **The etherCON panel stack.** ADR 0009 puts the connector's screws through
   the oak tail cap into a backing plate. The NE8FDP's maximum panel thickness
   is smaller than the oak cap alone. *Rule: "etherCON panel stack within the
   connector's maximum".* Options: pocket the oak around the flange so only the
   backing plate is clamped, or a thinner cap.
2. **The etherCON body is taller than the cavity.** Centred on the tail face,
   the connector body (taken at the bore diameter — the real body is at least
   that) reaches into the oak top and bottom. *Rule: "etherCON body inside the
   cavity height".* The lamination can take through-cuts at the tail, but they
   must be in the DXF before gluing.
3. **The Matrix's USB-C cannot reach the tail face.** ADR 0009 says "keep that
   edge of the board at the tail", but the etherCON body fills the tail's
   depth and there is not room beside it for the Matrix board. *Rules: "Matrix
   USB-C at the tail face", "room beside the etherCON body".* A short
   panel-mount USB-C extension is the obvious answer; it is a BOM line.
4. **The display is what sets the mouth end.** On the underside it cannot
   share the space under the left-hand run with the thumb arc, so it adds
   roughly its own length in front of the keys. *Rule: "what sets the mouth
   end".* Moving it is the largest remaining length lever.
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

## Not modelled yet

The breath tube and its route, the sensor and trap, the looms, the thumb rest
lip, gasket beads, plate stiffening (ADR 0002 — open, and it changes the lid),
the diffuser standoff, and anything in the display band beyond the board. The
carrier and cluster boards are rectangles, because their outlines are M3/M4
outputs.
