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

- **The lid** is the aluminium key plate on the oak top. **The top cluster
  boards live inside the oak top**, in through-cut windows: the KS-33's pins
  put the PCB a few millimetres under the seat (`docs/reference/ks33-geometry.md`
  gives the window; `switch.pcb_below_seat` in `config/body.yaml` is what the
  model uses), and that is inside the oak top, not in the cavity. The display board sits
  the same way, glass just under the plate.
- **The U** is the oak bottom and two acrylic sides. **Each side is two
  laminae**: the outer full height, the inner stopping at the lid. That is how
  ADR 0009's rebate becomes two through-cuts instead of a routed step, which
  the ADR's own rule ("if a part needs 3D machining, the design is wrong")
  would not allow.
- **Thumb keys** mount upside down in a thumb plate on the oak bottom's inside
  face; the through-cut in the oak is the recess (ADR 0009). Each thumb
  cluster has its own plate.
- **Key positions**: a key with `x`/`y` in `config/key-layout.yaml` is placed
  there. A key without one is placed on the provisional layout in
  `config/body.yaml`, where each run's spacing is its length over its gaps —
  there is deliberately no separate pitch value.
- **Every part is a 2D module** in its own sheet frame; the assembly only
  places them. `export/*.dxf` are those modules exactly.

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
4. **The display band does not hold the display and the first key.** ADR 0009's
   length table counts key runs centre to centre, so LH1's half-cap, its switch
   body and its cluster board all spill into the display band. In the oak top the
   display and LH cluster windows merge; in the plate, the display window and
   LH1's cutout merge. *Rules: "display board clear of the LH cluster board",
   "key plate web between the display window and the nearest cutout".* The
   budget has slack; where it goes is `layout.slack_to`.
5. **Individual thumb recesses leave almost no oak between them** at the
   ADR 0010 arc spacing. *Rule: "oak-bottom cuts at least 3 mm apart".* ADR 0010
   already asks shared-versus-individual as an M2 question; the model says
   individual recesses need the arc spread further. The same rule catches
   placeholder fasteners landing on placeholder spares — move one.
6. **The carrier and the LED strips.** The carrier at the BOM's assumed width
   does not fit between strips in the side channels at the placeholder
   diffusion gap. *Rule: "carrier fits between the LED strips".*
7. **M3 into a 1.20 mm plate** is about two threads. The BOM already says
   "insert or tapped boss"; the model says plain tapping is not one of the
   options.

## Not modelled yet

The breath tube and its route, the sensor and trap, the looms, the thumb rest
lip, gasket beads, plate stiffening (ADR 0002 — open, and it changes the lid),
the diffuser standoff, and anything in the display band beyond the board. The
carrier and cluster boards are rectangles, because their outlines are M3/M4
outputs.
