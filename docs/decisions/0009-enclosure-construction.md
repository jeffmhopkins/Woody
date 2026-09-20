# 0009 — Enclosure construction

**Status:** Accepted

## Context

No 3D printer and no CNC access; everything is outsourced. Basic wood
construction is available in-house, but not deep pocketing.

The instrument is **not round**. It is a flat sandwich: oak top and bottom,
frosted acrylic sides carrying LEDs, aluminium key plate on top, and three or
four mechanical keys on the underside for the left thumb, inset so the travel
feels right.

## Decision

**A laminated stack of flat parts, every layer a 2D through-cut.**

### No CNC is required

Every part in this design is a flat sheet with through-cuts, which is laser and
waterjet territory rather than milling. Vendors like SendCutSend, Ponoko and
OSH Cut will cut aluminium, acrylic and plywood from a DXF at a fraction of CNC
cost with days of turnaround.

The key plate is the extreme case: a flat plate with a grid of rectangular
cutouts is close to the most laser-friendly part that exists.

### Lamination replaces pocketing

Rather than milling a recess into thick oak, build thickness from thinner layers
where the middle layer has a through-cut. Every layer stays a 2D part that can
be cut on a scroll saw or sent out flat. This is how a cavity gets built without
a mill.

### The thumb inset falls out for free

```
 ┌──────────────────────────┐   aluminium top plate (switch cutouts)
 ├──────────────────────────┤   oak top
 │    electronics cavity    │   spacer layers; frosted acrylic sides + LEDs
 ├───────┬──────────┬───────┤   oak bottom, through-cut at the thumb
 └───────┤  switch  ├───────┘   thumb plate mounted to the INSIDE face
         └──────────┘
```

The thumb switches mount to a plate on the **inside** face of the bottom panel,
and the through-cut in the oak is the recess. **Oak thickness sets the inset
depth** — choose the bottom panel thickness to get the thumb travel wanted, and
the geometry follows. No pocketing anywhere in the design.

### The right thumb rest is a stack feature

The right thumb rests on the instrument and its three control switches sit
offset from that rest position (ADR 0010). That means a **defined thumb rest**,
not bare oak — and on a flat sandwich with no pocketing available, it is another
laminated layer: a small additional piece bonded to the bottom panel forming a
lip or contour for the thumb to sit against.

Consistent with everything else here — a 2D part, cut flat, added by lamination
rather than removed by machining.

## Ergonomic iteration ladder

Without a printer, iteration goes cheapest-first:

1. **Paper at 1:1, taped to a board.** Free, same day. Catches gross errors — is
   the reach right, do the fingers splay naturally.
2. **Laser-cut acrylic test plate**, real switches clipped in, hand-wired.
   ~$20–40 and about a week. This is the real ergonomic test.
3. Iterate step 2 once or twice, then commit to aluminium.

Slower than a printer would be, but cheaper per iteration than 3D printing for
flat parts, and not blocked.

**No aluminium is cut before M3.**

## Consequences

- CAD produces DXF as the primary export. Every part must be expressible as a 2D
  outline with through-cuts; if a part needs 3D machining, the design is wrong.
- The wood remains non-structural (ADR 0002). The plate stack carries the keys
  and mounts to the body at a few points.
- Strap attachment points are hard points through the oak and must be designed
  in, not retrofitted (ADR 0005).
- Acrylic LEDs are edge-lit into the frosted sides. Their power and ground must
  stay off the analog section's return path (ADR 0001).

## Open

- **Instrument dimensions.** Length, width and stack thickness. This constrains
  board sizes, display placement and the umbilical entry point, and it blocks
  M4.
- CAD tool, which decides whether `mechanical/cad/` holds Fusion, FreeCAD or
  neutral STEP.
- Oak thickness for the bottom panel, which sets thumb key travel.
