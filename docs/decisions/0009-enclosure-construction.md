# 0009 — Enclosure construction

**Status:** Accepted

## Context

No 3D printer and no CNC access; everything is outsourced. Basic wood
construction is available in-house, but not deep pocketing.

The instrument is **not round**. It is a flat sandwich: oak top and bottom,
frosted acrylic sides carrying LEDs, aluminium key plate on top, and three or
four mechanical keys on the underside for the left thumb, inset so the travel
feels right.

## Envelope

**18 inches long (457 mm), 1.5 inches thick (38 mm).** Width not yet decided.

### Length closes, with room

18 inches is compact for a wind controller — an EWI USB is around 24 inches, a
clarinet closer to 26. Worth checking rather than assuming:

| Segment | mm |
|---|---|
| Mouthpiece / breath inlet | 40 |
| Display | 30 |
| Left hand cluster, 5 keys | 90 |
| Inter-hand gap | 50 |
| Right hand cluster, 6 keys | 110 |
| Umbilical connector + strain relief | 40 |
| End margins | 20 |
| **Total** | **380** |
| **Available** | **457** |
| **Slack** | **77 (3.0 in)** |

It closes with three inches of slack. Tight enough that the layout wants
designing rather than improvising, but not constrained. The MT165 caps at
16.5 mm help here — they are smaller than standard 18 mm MX spacing, so key
clusters pack tighter than a keyboard footprint would suggest.

**A useful side effect: the long-run signal concern from ADR 0001 largely
evaporates.** That analysis assumed roughly two feet between the MCU at the top
and the IMU and connector at the bottom. At 18 inches overall the longest run is
more like 14–16 inches, which is comfortable for SPI with ordinary care. RS-485
transceivers stay a contingency rather than a likely requirement.

### Thickness is bounded by switch bodies, not boards

38 mm of stack, consumed roughly as:

```
  aluminium top plate       ~2 mm
  oak top                   ~6 mm
  ---- cavity ----          remainder
  oak bottom                ~8 mm   <- sets thumb key inset depth
  thumb switch plate        ~2 mm
```

That leaves around 20 mm of clear cavity — except where switch bodies intrude.
Top switches pass through the plate and oak and protrude slightly into the
cavity; the bottom thumb switches mount to the inside face and protrude *up*
into it by most of their body height. In the thumb regions, usable cavity may be
half of what it is elsewhere.

**The KS-33 body height below the plate is the number that decides this**, and it
is unmeasured. It comes out of M1 alongside the cutout dimension.

Boards are not the constraint. An ESP32-S3-WROOM module on a PCB is around 5 mm
total, and an OLED module is a few millimetres. 38 mm is comfortable for
electronics; it is the switch bodies and the U-bolt that eat the space.

### 1.5 inches suits the grip

The left hand sandwiches the body between fingers and thumb (ADR 0010). At
1.5 inches thick that is a comfortable pinch — about the span of a thick book
spine. Thinner would make the grip cramped and give the thumb less leverage;
much thicker would strain it.

### Strap placement follows from the layout

The U-bolt goes on the **bottom face, in the inter-hand gap** — the 50 mm band
between the left thumb cluster and the right thumb rest, which is free of
switches and lands near the middle of the instrument where CG will be.

Bottom face is correct for the same reason a saxophone's strap ring is on the
back: the instrument hangs with its key face outward and the attachment toward
the player's body.

**Through-bolt the entire laminated stack.** The U-bolt then does two jobs: it
anchors the strap to the aluminium plate, which is the strongest element in the
sandwich, and it adds clamping force to the lamination at mid-span where it is
otherwise held only by adhesive.

## Width: 2.5 inches

**63.5 mm.** This is above the 50–60 mm window originally sketched here, and
that earlier figure was a heuristic rather than a measurement. Recording why it
is still the right call, and what to watch.

### Why the grip concern is smaller than the heuristic implied

The earlier reasoning assumed the sandwich grip carries the instrument. It does
not — **the strap does** (ADR 0005, U-bolt above). The grip *stabilises* and
positions; it does not bear weight.

That is exactly how a saxophone works: the right thumb hook and left thumb rest
stabilise while the neck strap takes the load, and a tenor body at the grip
point is nearer three inches across. The relevant question is not "can the hand
clamp this" but "can the thumb reach a comfortable opposing position and still
extend to its keys", which is a much weaker constraint.

### What the width buys

- **Two-column key clusters** become possible, instead of a single column with
  side keys. Six right-hand keys as 4 + 2 rather than 6 in a line.
- **This buys length back.** Two-column clusters are shorter longitudinally, so
  the 3 inches of slack in the length budget above grows rather than shrinks.
- Room for a readable display, usable PCB area, and acrylic side panels with
  enough presence for the edge lighting to be worth doing.
- More cavity volume where the thumb switches are eating into it.

### Mass

Rough estimate at this envelope:

| Part | g |
|---|---|
| Aluminium top plate, 2 mm | 157 |
| Oak top, 6 mm | 131 |
| Oak bottom, 8 mm | 174 |
| Acrylic sides, 2 × 4 mm | 164 |
| Electronics and hardware | 200 |
| **Total** | **~825 (1.8 lb)** |

Squarely in EWI territory (~1.5–2 lb), and on a strap that is unremarkable. Not
a reason to reconsider.

### What to check at M2

The paper mockup should answer three specific things, and they are the only real
risks at this width:

1. **Can the left thumb reach its four-key arc** from a comfortable opposing
   position, without the hand shifting?
2. **Is the grip patch far enough from the key arc** that gripping does not
   trigger keys (ADR 0010)?
3. **Does the right thumb rest fall naturally** where the body wants to sit in
   the hand?

If any of those fail, the fix is narrowing toward 55 mm, which costs the
two-column layout. Worth knowing before anything is cut, and it costs one sheet
of paper.

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

### Strap point: U-bolt above the centre of gravity

A U-bolt near the middle of the instrument, **slightly above the centre of
gravity**, carries a neck strap.

Above CG is correct and deliberate: a mass hung below its suspension point is
pendulum-stable and self-rights, while hanging at or below CG is unstable and
wants to flip. *Slightly* above is also right — a large offset gives a strong
restoring torque that fights the player, and a wind controller has to be angled
by the player at will. A small offset gives a gentle centring tendency with
compliance left over.

**This is the highest-stress point in the entire build.** The strap carries the
whole instrument, and it carries it *during play*, not just at rest — the left
thumb momentarily gives up grip every time it extends to a key (ADR 0010).

Two consequences:

- **It must anchor to the structural plate stack, not to the oak.** The wood is
  a shell (ADR 0002) and a U-bolt through oak alone will crush the fibres and
  eventually tear out. Through-bolt to a metal backing plate inside the cavity,
  tied into the same structure that carries the keys.
- **The position must be adjustable.** CG cannot be known accurately from CAD —
  cable, connector, adhesive and finish all add mass that is hard to model, and
  what matters is how it *feels* hanging, not where the model says the centroid
  is. Design in a short slot or two or three discrete hole positions so balance
  can be tuned empirically after assembly. Cheap now, painful to retrofit into a
  finished instrument.

The U-bolt also intrudes into the electronics cavity near the middle of the
body. It is an obstruction that belongs in the CAD from the start, with cable
routing designed around it rather than discovered during assembly.

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
