# 0002 — Key switches and mounting

**Status:** Accepted

## Context

The previous project used two MPR121 capacitive touch controllers. Capacitive
sensing on a wind instrument suffers from drift, moisture sensitivity and false
triggers — the instrument is played with wet hands, near a wet mouth, under
changing temperature. Getting away from that is a primary goal of this
iteration.

## Decision

**Gateron KS-33 low-profile switches with Tai-Hao MT165-MX keycaps.** Both
purchased. MX-stem switches with 16.5 × 16.5 mm blank caps.

## Consequences

### Keys are binary

KS-33 is a mechanical switch with no position sensing. No half-holing, no
per-key pressure, no continuous key expression — ever, without changing the
switch. This is an accepted trade: definite actuation and no drift, in exchange
for expression coming entirely from breath and the IMU. Those two now carry the
whole expressive load, which raises the bar on both.

Hall-effect switches would have given analog travel with the same caps, but the
switches are bought and this is settled.

### Mounting is the hard part

Resisting downward force is easy. Resisting *rocking* is the real problem. A
keyboard solves it with a rigid flat plate that the switch clips into, but a
woodwind breaks every assumption behind that: ergonomic rather than gridded key
positions, fingers pressing at angles, and low-profile switches with shallower
retention tabs than full-height MX.

Three things must be true:

1. **The plate cutout captures the switch laterally.** This is the precision
   feature of the entire build.
2. **Something backs the switch** so it cannot push through. Most commonly
   forgotten, and the first thing to fail.
3. **The plate does not flex.** A thin plate spanning several keys is a
   trampoline; it needs ribs, a backer, or a PCB acting as stiffener.

### The wood is not structural

Switch pockets do not get cut into the oak. Wood moves with humidity, this is an
instrument that will have moisture breathed into it for hours at a time, and
repeatable cutout tolerances in wood are not achievable. A rigid plate assembly
carries the keys and mounts to the body at a few points. The wood is a shell.

### Build approach

Hand-wired on laser-cut plates during ergonomic iteration (hours per iteration),
moving to PCB once the layout is locked. PCB turnaround is a week and is the
enemy of ergonomic iteration, so it comes after M3, not before.

## Switch weight: red (linear)

**Red** — linear, and the lightest common option in the KS-33 line. Right for
this instrument: tactile or clicky variants add breakaway force that would fight
the left thumb, which actuates with its tip while partly giving up grip
(ADR 0010), and on a wind instrument a tactile bump buys nothing since there is
no typing feedback to want.

Bought to try. Whether the action is right is settled **by hand at M1**, before
anything is built — press one with a fingertip, then with the tip of a thumb
held as it would grip the instrument. That is a ten-minute question with
switches on the bench and no hardware.

Switches are soldered in the final build. An earlier revision of this ADR
argued for hot-swap sockets, which was over-engineering: the decision happens
once, up front, not repeatedly at runtime.

### Weights need not be uniform

Worth deciding at M1 rather than defaulting: **the four left-thumb keys may want
a lighter spring than the eleven finger keys.** A thumb tip extending from a
grip has considerably less force available than a finger pressing straight down,
and real woodwinds vary spring weight across keys for exactly this reason.

Since this is settled before the build, mixed weights cost nothing but ordering
four of something different.

### Accepted consequence

A failed switch means taking the instrument apart — six fasteners, lid off,
and the switch is soldered to a plate that is inside the lid (ADR 0009). That
is an afternoon, not a rebuild; this paragraph said "a bonded laminated body"
and meant a rebuild. Accepted either way — mechanical switches are reliable,
this is a one-off, and designing the whole build around a failure that probably
never comes is the wrong trade.

## The switch is documented; use the documentation

An earlier revision of this ADR said the cutout dimension *"must be measured,
not taken from a datasheet"*. **That was wrong.** Gateron publishes a KS-33 Low
Profile 2.0 datasheet and downloadable 3D models for this exact switch, there is
a community CAD model on GrabCAD, and at least one open-source keyboard
([ianmaclarty/ik](https://github.com/ianmaclarty/ik)) is built on KS-33 with a
real plate whose geometry is in the repository.

**And a caliper is the worse instrument for this.** Measuring a moulded plastic
housing gives you *that sample's* dimension including draft angle and mould
flash — not the design intent, and not the tolerance band. The drawing gives
both. Measuring was the right instinct for a part nobody documents; it is the
wrong one here.

**The cutout is 14.0 × 14.0 mm — the same as standard MX.** An earlier revision
of this ADR asserted that Gateron low-profile *"does not use the standard 14 mm
MX cutout"*. Measured out of a working KS-33 build's published top-case meshes,
it is exactly 14.000 mm square, 47 times across two halves. Details and method
in [the geometry reference](../reference/ks33-geometry.md).

Known from the published specification, pending the drawing itself:

| | |
|---|---|
| Height | **12.2 mm** |
| Pretravel | 1.70 mm |
| Total travel | 3.00 mm |
| Pins | 3-pin, SMD LED support |
| Materials | POM stem, PC top housing, nylon bottom |

**Download the datasheet and the STEP model before any CAD starts.** They are at
[gateron.com/pages/3d](https://www.gateron.com/pages/3d) and the
[KS-33 Low Profile 2.0 datasheet page](https://www.gateron.co/pages/gateron-ks-33-low-profile-2-0-mechanical-switch-datasheet).
Put the STEP in `mechanical/` so the stack is modelled against the real solid
rather than a nominal box.

## What still has to be measured, and why

Two things, narrower than before.

**The plate thickness, which is now a live question rather than a given.**
ADR 0009 specifies a ~2 mm aluminium top plate. Standard MX plates are 1.5 mm;
the reference KS-33 build uses **1.1 mm**. Neither is 2 mm, and a low-profile
switch has shallower retention tabs than full-height MX to begin with.

At 2 mm the clips will not engage at all — **though "clips" may be the wrong
word.** A solid model measured 2026-09-21
(`docs/reference/ks33-geometry.md`) shows **no horizontal clip shoulder**, only
four tapered flexing arms that are *widest just under the collar*. If that is
real, retention is an interference press and there is no ledge to miss. **The
constraint that does bite either way: the through-cutout section is only
2.50 mm deep**, so a 2 mm plate consumes 80 % of it and a 1.5 mm plate 60 %. **That is survivable but it changes
which requirement is load-bearing:** the switch still seats on its top flange,
the cutout still captures it laterally, and it is still soldered — but
requirement 2 above, *"something backs the switch so it cannot push through"*,
stops being belt-and-braces and becomes the only thing resisting push-through.
That requirement is already flagged as "most commonly forgotten, and the first
thing to fail."

Two ways out, and the cheap one is available: **take the plate to 1.5 mm and
recover the stiffness from the lamination**, which is ADR 0009's whole thesis
anyway — a 1.5 mm plate bonded to oak is not a 1.5 mm plate. Or keep 2 mm and
design the backer as a structural member rather than a spacer. **Decide with the
vendor drawing's clip dimension in hand**, which is the one number that settles
it and the one this project does not yet have.

**The bond is RTV silicone, and that still supports this.** ADR 0009 settles the
plate-to-oak joint as a compliant silicone layer rather than a rigid adhesive,
because oak moves 0.6–0.9 mm across the grain with humidity and aluminium does
not. A first reading says that kills the argument above — a compliant bond
cannot stiffen a plate.

It does not, because the loads are different in the two directions. The wood
movement the silicone has to permit is **in-plane shear**, where a silicone
layer is genuinely compliant. A key press is **normal compression** into a thin
layer bonded on both faces, which cannot squeeze out sideways and is therefore
very stiff. The oak backs the plate against exactly the load a key applies,
while declining to fight the load the seasons apply.

What does change is requirement 2 — *something backs the switch so it cannot
push through* — which is now being met by a silicone layer rather than by a
rigid bond, and wants confirming by hand at M1 with a real switch in a real
offcut rather than by argument.

**There are also no alignment posts.** An MX switch is located by its cutout
*and* two ⌀1.75 mm posts at ±5.08 mm; the low-profile footprint has neither.
The cutout is the only lateral location feature there is, which is the evidence
behind calling it "the precision feature of the entire build".

**The achieved fit, which is a process question rather than a geometry one.**
The drawing gives the nominal cutout; it cannot tell you what *your* cutter
produces in *your* material. Kerf varies with machine, material and thickness,
and this is a press fit at ±0.1 mm. **So the test coupon survives** — cut the
nominal dimension plus a ladder of steps either side, and find which one retains
solidly without fighting during assembly. That is a half-hour at the vendor's
minimum order, not a discovery exercise.

**Contact bounce and the actuation/reset hysteresis gap, which Gateron does not
publish.** Travel and force are specified; bounce duration and the reset point
are not, for this switch or for most. These genuinely need a scope, and they set
the debounce windows on the most latency-sensitive path in the instrument
(ADR 0001). Measure on fast press, slow press, fast release, slow release, and a
worn switch — the slow cases matter because a legato release can park the
plunger in the hysteresis gap and chatter for tens of milliseconds.

## Open

**Plate thickness**, no longer pending a clip dimension — the best available
model says there is no clip shoulder, and Gateron's own drawing is unreachable
from anywhere (`datasheets/MANIFEST.csv`). Decide it against the 2.50 mm
through-section and the zero standoff instead — 1.5 mm
with lamination doing the stiffening, or 2 mm with a structural backer. Blocks
M4 and M5.

Otherwise nothing: the cutout is 14.0 mm, the fit comes from a coupon, and the
timing from a scope.
