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

A failed switch in a bonded laminated body (ADR 0009) means taking the
instrument apart. Accepted — mechanical switches are reliable, this is a
one-off, and designing the whole build around a failure that probably never
comes is the wrong trade.

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

Nothing blocking. The cutout comes from the datasheet, the fit from a coupon,
and the timing from a scope.
