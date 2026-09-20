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

## Switch weight is not yet confirmed

The KS-33 ships in several weights and actuation types. Which variant is in hand
matters, because the left thumb actuates with its tip while partly giving up
grip (ADR 0010), and that gesture has much less force available than a finger
pressing straight down.

**Light linear is almost certainly correct.** Tactile or clicky variants add
breakaway force that will fight the thumb gesture, and on a wind instrument the
tactile bump buys nothing — there is no typing feedback to want.

Confirm at M1, while the switches are on the bench for cutout measurement.

## Open

**The KS-33 plate cutout dimension is not yet known and must be measured**, not
taken from a datasheet or from MX convention — Gateron low-profile does not use
the standard 14 mm MX cutout. Milestone M1: measure with calipers, cut a test
coupon at ±0.1 mm steps, find the size that retains solidly without fighting
during assembly. Everything downstream inherits this number.
