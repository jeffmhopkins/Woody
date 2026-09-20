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

## Switch weight: red (linear), and swappable by design

**Red** — linear, and the lightest common option in the KS-33 line. Right for
this instrument: tactile or clicky variants add breakaway force that would fight
the left thumb, which actuates with its tip while partly giving up grip
(ADR 0010), and on a wind instrument a tactile bump buys nothing since there is
no typing feedback to want.

Bought to try. Whether it is *right* is a question only playing answers.

### So the final build uses hot-swap sockets

Keeping the option to change switches is worth designing for rather than
retrofitting, for three reasons:

**Feel is genuinely uncertain until played.** A thumb tip extending from a grip
has much less force available than a finger pressing straight down. Red may
still be too heavy there, or fine everywhere. Nobody can answer that from a
datasheet.

**Mixed weights become a free experiment.** This is the interesting one. There
is no reason every key needs the same spring — real woodwinds vary spring weight
across keys for exactly this reason. **The four left-thumb keys could run
lighter than the eleven finger keys**, which directly addresses the force
concern above. With sockets that is a five-minute change; soldered, it is a
rebuild.

**Serviceability in a sealed body.** The instrument is a bonded laminated stack
(ADR 0009). A dead switch in a soldered build means taking it apart. Socketed,
the eleven top keys can be pulled from the outside with a keycap and switch
puller, no disassembly at all. The four thumb switches mount to the inside face
of the bottom panel and are not reachable that way, but eight of eleven beats
none of eighteen.

Sockets cost a little height below the PCB and slightly less retention — but
retention is the plate's job here anyway (above), not the solder joint's.

### What is and is not swappable

Sockets cover **any switch sharing the KS-33 footprint** — other weights in the
Gateron low-profile line, which is the realistic case.

They do **not** cover a change of switch family. Moving to Choc or full-height
MX would need a new plate cutout and a new PCB footprint. The MT165 caps also
pin this: they are MX-stem, so the low-profile MX-stem family is effectively
locked by the keycaps regardless.

## Open

**The KS-33 plate cutout dimension is not yet known and must be measured**, not
taken from a datasheet or from MX convention — Gateron low-profile does not use
the standard 14 mm MX cutout. Milestone M1: measure with calipers, cut a test
coupon at ±0.1 mm steps, find the size that retains solidly without fighting
during assembly. Everything downstream inherits this number.
