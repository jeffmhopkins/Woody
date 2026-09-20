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

**18 × 2.25 × 1.5 inches** — 457 × 57 × 38 mm.

### Keys run in a single line

The instrument stays long and slender like a flute, with keys in **one
longitudinal line**. What makes 18 inches workable is not compressing the key
runs but **shortening the sections above and below them** — there is no acoustic
bore to accommodate, so the mouthpiece region and the tail can both be brief.

### Length closes

18 inches is compact for a wind controller — an EWI USB is around 24 inches, a
clarinet closer to 26. Worth checking rather than assuming, at a 24 mm key
pitch:

| Segment | mm |
|---|---|
| Mouthpiece / breath inlet (short) | 40 |
| Display band | 60 |
| Left hand, 5 keys in line | 96 |
| Inter-hand gap | 50 |
| Right hand, 6 keys in line | 120 |
| Tail: connector + strain relief (short) | 40 |
| End margins | 20 |
| **Total** | **426** |
| **Available** | **457** |
| **Slack** | **31 (1.2 in)** |

It closes with 1.2 inches of slack, and more at a tighter pitch — the MT165 caps
at 16.5 mm allow roughly 18–20 mm before caps collide, against standard 18 mm MX
spacing. Not constrained, but the layout wants designing rather than
improvising, and the display band is now the second largest single claim on
length after the key runs — it grew from 30 mm to 60 mm when the board was
chosen (ADR 0008), which halved the slack. Anything else wanting length should
be checked against this table rather than assumed to fit.

**A useful side effect: the long-run signal concern from ADR 0001 largely
evaporates.** That analysis assumed roughly two feet between the MCU at the top
and the IMU and connector at the bottom. At 18 inches overall the longest run is
more like 14–16 inches, which is comfortable for SPI with ordinary care. RS-485
transceivers stay a contingency rather than a likely requirement.

### Thickness is bounded by switch bodies, not boards

38 mm of stack, consumed roughly as:

```
  aluminium top plate       ~2 mm   <- may become 1.5 mm, see ADR 0002
  oak top                   ~6 mm
  ---- cavity ----          remainder
  oak bottom                ~8 mm   <- sets thumb key inset depth
  thumb switch plate        ~2 mm
```

That leaves around 20 mm of clear cavity — except where switch bodies intrude.
Top switches pass through the plate and oak and protrude slightly into the
cavity; the bottom thumb switches mount to the inside face and protrude *up*
into it by most of their body height.

**The KS-33 is 12.2 mm tall overall**, from Gateron's published specification —
this ADR previously called it unmeasured and deferred it to M1, which was wrong
on both counts: the switch is documented, and the number was available all along
(ADR 0002).

That is good news for the cavity. Against 20 mm of clear space, even if the
entire 12.2 mm sat inside it there would be 8 mm left, and in practice several
millimetres of that height is stem and top housing sitting *above* the plate.
**The earlier worry that "usable cavity may be half of what it is elsewhere" in
the thumb regions looks overstated.**

What is still missing is the **split** — how much of the 12.2 mm falls above
versus below the mounting plane. That is on the dimensioned drawing, and it is
the reason to download the drawing and the STEP model before starting M4 rather
than modelling against a nominal box.

Boards are not the constraint on *depth*. An ESP32-S3-WROOM module on a PCB is
around 5 mm total. 38 mm is comfortable; it is the switch bodies and the U-bolt
that eat the space.

**But the cavity is not a clear box in plan, either.** Switch bodies run down
the centreline for the whole length of both key runs, and thumb switches
protrude upward from the bottom face. The genuinely free volume is the upper
section, the inter-hand gap (minus the U-bolt), the lower section, and two
narrow side channels flanking the switch column — which are the natural route
for wiring looms. Board outlines belong on that plan, not on the raw envelope
(ADR 0013).

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

## Width: 2.25 inches

**57 mm**, in the middle of the 50–60 mm window originally sketched here.

### Why the grip concern is smaller than the heuristic implied

The earlier reasoning assumed the sandwich grip carries the instrument. It does
not — **the strap does** (ADR 0005, U-bolt above). The grip *stabilises* and
positions; it does not bear weight.

That is exactly how a saxophone works: the right thumb hook and left thumb rest
stabilise while the neck strap takes the load, and a tenor body at the grip
point is nearer three inches across. The relevant question is not "can the hand
clamp this" but "can the thumb reach a comfortable opposing position and still
extend to its keys", which is a much weaker constraint.

### Nothing on the instrument binds the width

Two earlier justifications in this ADR turned out not to hold, and both are
worth recording because they were wrong in the same direction — assuming
something needed lateral room that does not.

- **Two-column key clusters.** Void: keys run in a single line (ADR 0010).
- **The left thumb's four-key arc.** Also void, and usefully so — see below.
  Four 16.5 mm caps laid *across* the body would need 66 mm of cap width alone,
  which does not fit at any width under consideration. The arc therefore has to
  run **along** the body, so it consumes length in the left-hand region, not
  width.

What is left is grip feel, display legibility, PCB area, cavity volume, and
enough side-panel height for the edge lighting to read. None of those is tight
at 57 mm, so the width is set by how the instrument should *feel* rather than by
a clearance anywhere.

2.25 inches sits between the slender flute-like 2 inches and the roomier 2.5,
and it is comfortably inside the span where the thumb can oppose the fingers.

### Mass

| Width | Mass |
|---|---|
| 2.00 in | ~735 g (1.62 lb) |
| **2.25 in** | **~778 g (1.72 lb)** |
| 2.50 in | ~825 g (1.82 lb) |

Aluminium plate, oak top and bottom, acrylic sides, plus ~200 g of electronics
and hardware. All three land in EWI territory (~1.5–2 lb); the width barely
moves it, which is another reason to choose on feel.

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

### Breath tube access

The breath system is closed and dead-ended, so condensation is modest and there
is no flow carrying saliva into the sensor (ADR 0003). A small dead-volume trap
at the sensor end handles what accumulates.

The only stack requirement is **access to clear it without disassembly**. Not a
drain plumbed through the body — just a serviceable path to the sensor end of a
short tube near the top.

### The tail carries a display window and a USB port

Two openings in the tail section, below the right-hand key run, clear of the
thumb keys and the U-bolt:

**A window in the oak underside for the 8×8 matrix** on the real-time board
(ADR 0007, ADR 0014). Roughly 22 mm square, facing the player's downward glance
rather than the audience. It is a through-cut in a flat part, so lamination
gives it for free — the cost is entirely in planning, because it constrains
where that board sits and it cannot be added once the stack is bonded.

Three details that have to be in the CAD from the start:

- **A matching cutout in the carrier PCB**, because the board's LED face points
  at the carrier and the light has to pass through it.
- **A diffuser, and not the side panels' material.** The sides are frosted to
  blur the strips into a glow; an 8×8 needs enough diffusion to kill hot spots
  and little enough to keep pixels distinguishable. Thin, and close to the LEDs.
- **Which face of the board carries the matrix** relative to its header rows.
  Confirm on arrival. If it is the wrong way round, the board moves to the
  carrier's underside; if that fails too, a flying harness for 14 signals, which
  is ugly enough to be worth knowing about early.

**A USB-C slot at the tail face**, which the instrument needs regardless of the
window. Flashing and USB MIDI (E5) both require reaching the real-time board's
own connector, and there is no reaching anything once the body is bonded. Keep
that edge of the board at the tail.

**And the umbilical connector, which is the reason the tail face is now
crowded.** The etherCON chassis flange (ADR 0004) is roughly 26 × 31 mm on a
face that measures 57 × 38 mm. Two consequences:

- **It leaves about 3.5 mm of material above and below the cutout**, and
  **oak is not what should be carrying it.** This is the same rule as the
  U-bolt and the key switches: the wood is a shell, not structure (ADR 0002).
  **Mount the connector to an internal backing plate** — aluminium or ply, tied
  into the same stack that carries the keys — and let the oak be the face the
  screws pass through rather than the thing the screws hold.
- **It shares the face with the USB-C slot**, leaving roughly 31 mm beside the
  flange for it. That fits, but it is not the place to discover a conflict.
  Both openings and the backing plate go into the M4 CAD together, and the
  1:1 paper check covers this face as well as the 6HP panel.

Placing the umbilical at the tail also puts it as far as possible from the
mouthpiece, so the cable leaves the instrument at the end that hangs low and
does not foul the player's hands or the strap.

Both are cheap now and unavailable later, which is the recurring shape of every
decision in this section.

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
- **The position must be settled empirically, which is not the same as being
  adjustable.** CG cannot be known accurately from CAD — cable, connector,
  adhesive and finish all add mass that is hard to model, and what matters is
  how it *feels* hanging, not where the model says the centroid is.

  An earlier revision asked for a slot or discrete hole positions "so balance
  can be tuned empirically after assembly." **That is impossible as written**,
  and a review caught it: the backing plate the U-bolt anchors to sits inside a
  bonded cavity. Once the stack is closed, there is nothing to move the bolt
  *to*. An adjustment that requires reaching a part you cannot reach is not an
  adjustment.

  Two ways to have it, and they are exclusive:

  - **Dry-assemble, hang, balance, then bond.** The stack goes together
    unbonded with everything in it that contributes mass, it hangs from a
    temporary strap, the position is marked, and only then does the adhesive
    come out. This is free, and it folds naturally into the **M8 pre-bond gate**
    — which exists anyway, for other reasons.
  - **Or make the anchorage reachable from outside** — a captive plate in a
    machined recess accessible through the bottom face, with the slot in the
    external hardware rather than the internal plate.

  **Take the first.** The second adds a serviceability feature to a part of the
  instrument that will be adjusted exactly once.

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
- **The two side channels are shared: LED strips on both sides, looms alongside.**
  An earlier revision assigned the channels to the wiring looms while ADR 0014
  assigned the same two to the LED strips — a direct contradiction between two
  accepted decisions, and one that made ADR 0014's own instruction ("keep the LED
  runs away from the breath wiring") unsatisfiable.

  **It is resolved by the sensor moving to the bottom** (ADR 0003). The analog
  breath pair no longer runs the length of the body at all, so what shares the
  channels with pulsed LED current is the SPI key chain, the UART and power —
  all digital and all tolerant. Digital beside pulsed LED current is a far weaker
  objection than analog beside it would have been.

  **The key chain still needs a ground return per signal** (ribbon with
  alternating grounds, or twisted pairs) — that requirement is independent of
  what else is in the channel, and it is the one thing that makes this sharing
  safe.

  Diffusion gap between strip and acrylic is a prototype question and it
  constrains the channel depth.

## Things that are free now and impossible later

A body that is bonded shut is a body that is never opened again. These four cost
almost nothing while the stack is apart and cannot be had afterwards at any
price.

**Bond the aluminium plate to `PWR_GND`. Never to `AGND`.** Nothing currently
bonds it. It floats under the player's hands, one to two millimetres from
eighteen switch pins that are wired directly to shift-register inputs — and a
corrupted chain read becomes a spurious note-on at full velocity (ADR 0001). An
unbonded plate means the instrument fires random notes when touched in a dry
room, and that will be blamed on firmware forever. The choice of *which* ground
matters as much as the bonding: tying it to `AGND` would put the player's body
capacitance straight onto the breath channel's voltage reference.

**Run two spare conductors in every internal loom.** The looms are hand-built,
once, into a stack that cannot be reopened. A spare pair costs a few cents and
some crimping now; discovering you need one signal more after bonding costs the
instrument.

**Conformal-coat the boards.** The instrument is breathed into for hours, behind
eighteen unsealed switch cutouts, in a body whose interior runs 10–20 K above
ambient. There is no coating anywhere in the BOM and nothing else in the design
addresses humidity inside the cavity.

**Mask both pressure-sensor ports before coating.** The breath sensor's
reference port has to stay open to the cavity, and coating that seals it turns
the reference chamber into a trapped volume that gains ~5.2 kPa when the body
warms — clipping the output to zero and presenting as a dead sensor that works
from cold and fails ten minutes in (ADR 0003). Adhesive during lamination can do
the same thing, so orient the part with neither port facing a glue line.

**Dry-assemble and balance before bonding**, per the U-bolt section above. This
is the M8 gate in the roadmap, and the U-bolt position is one of several things
it is the last chance to settle.

## Open

- CAD tool, which decides whether `mechanical/cad/` holds Fusion, FreeCAD or
  neutral STEP.
- Oak thickness for the bottom panel, which sets thumb key travel.
