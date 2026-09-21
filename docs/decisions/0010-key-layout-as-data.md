# 0010 — Key layout as data

**Status:** Accepted

## Context

The fingering system is custom — not EWI, not saxophone, not recorder. That
means the layout is a design deliverable in its own right, and it will change
repeatedly during ergonomic iteration (ADR 0009) and again during playing.

## Decision

**Define the key layout once, as a data file, and generate from it.**

`config/key-layout.yaml` is the single source of truth. Both sides consume it:

- **Mechanical** — key positions drive the plate DXF cutout locations
- **Firmware** — key IDs drive the 74HC165 bit mapping and the fingering table

When a key moves during iteration, the plate and the firmware stay in sync by
construction rather than by remembering to update both.

## The fingering table is not compiled in

A custom fingering system takes a lot of playing to get right, and a recompile
per experiment is the wrong loop. The table lives in NVS and is editable — over
USB from a host tool (F7), and where practical from the instrument itself.

This mirrors the previous project's instinct: `owp_synth` ran a CC-driven
modulation scheme with breath and modulation routed to a dozen destinations.
The same shape applies here to CV routing (ADR 0006) — four mod channels with
source, scale, offset, curve and slew, defined as data rather than code.

## Consequences

- A small generator in `tools/` turns the layout file into DXF cutout geometry
  and a firmware header or config blob.
- Layout revisions are reviewable as diffs, and every ergonomic iteration is
  recorded rather than lost.
- The schema needs to exist before M2, since the first laser-cut plate should be
  generated from it rather than drawn by hand.

## Key count

**18 switches**, decided:

| Group | Count | Face | Role |
|---|---|---|---|
| Left hand | 5 | top | note |
| Right hand | 6 | top | note |
| Left thumb | 4 | bottom, inset (ADR 0009) | note |
| Right thumb | 3 | bottom, offset from the rest | **control** |

## Not every switch is a note key

The right thumb's three switches are **control inputs, not fingering inputs** —
modulation and IMU gating (ADR 0007). The fingering table covers 15 keys, not
18, and the layout file carries a `role` field so firmware and the plate
generator both know the difference.

This matters more than it looks. A control switch inside the fingering table
would produce phantom notes; a note key treated as a control would silently drop
fingerings. Keeping the distinction in data rather than in code is the point of
this ADR.

## The right thumb rests; the left thumb works

The right thumb's normal state is resting on the instrument, with its three
switches offset from the rest position so they are reachable without giving up
support. This is idiomatic — on a saxophone the right thumb hook carries the
instrument while the left thumb works the octave key.

**This corrects a concern raised earlier in this ADR.** The worry was that four
left-thumb keys were ambitious for a thumb also carrying the instrument's
weight. With the right thumb as the primary rest, the left thumb is largely
freed to actuate, and four register keys under it is conventional rather than
ambitious.

The arc-versus-line consideration still stands — a thumb rolls more easily than
it reaches, so lay the four along an arc matching the thumb's rotation. But the
risk is lower than first assessed, and the paper-at-1:1 step will settle it.

## Top keys run in a single line

Eleven top keys — five left hand, six right hand — in **one longitudinal line**,
flute-style. No second column, no lateral side-key bank.

### Spacing will not be uniform, and should not be

A single line of 6 keys at a relaxed 24 mm pitch spans 120 mm. A relaxed adult
four-finger span, index to little, is roughly 80–90 mm. Six keys in a line is
therefore **beyond a fixed hand position by design** — and that is how real
woodwinds work: three or four keys sit under the fingers at comfortable spacing,
and the outermost are **pinky-reach** keys that the little finger extends to,
clustered tighter at the end of the run.

So the pitch should vary along the line: comfortable spacing under
index/middle/ring, tighter grouping for the keys the pinky reaches.

**The layout file already supports this**, and it is a good example of why it is
structured the way it is. Keys carry explicit `x`/`y` positions rather than a
pitch parameter, so non-uniform spacing needs no schema change — it is just
different numbers.

### What M2 has to establish

- Where the natural finger positions actually fall for each hand.
- Which keys are under-finger and which are pinky-reach.
- Whether 6 in a strict line works for the right hand, or whether the outermost
  one or two want a small lateral offset. A modest offset preserves the
  single-line character while relieving the reach; it is the obvious fix if the
  mockup says the stretch is bad.

## How the left thumb actually works

The left thumb's primary job is **sandwiching** — opposing the fingers on the
top face to grip the instrument. It actuates keys with the **end of the thumb**,
extending from that grip position, not with the pad.

Three things follow, and they constrain the layout more than the key count does:

**The grip patch and the key cluster must be separate.** If the keys sit where
the thumb bears down while gripping, they will trigger constantly. The thumb has
to *deliberately move* to reach them. This is the same principle as the right
thumb's rest-versus-switches offset, and it means the plate needs a defined
grip area that has no switches in it.

**The four keys lie on the thumb tip's sweep, not in a line.** The tip traces an
arc as the thumb extends and rotates away from the grip. Laying the keys along
that arc is what makes four reachable; laying them in a straight line is what
makes four too many. This supersedes the earlier arc-versus-line note — it is no
longer a preference, it is the mechanism.

**That arc runs along the body, not across it.** Four 16.5 mm caps laid
laterally would need 66 mm of cap width before margins, which exceeds the
instrument's 57 mm width (ADR 0009). So the arc is primarily longitudinal —
roughly 57 mm of travel down the body with perhaps 15–25 mm of lateral
deviation, sitting underneath the left-hand key run rather than beside it. It
consumes length in that region, not width.

**Actuation force has to suit a thumb tip at an awkward angle.** A thumb tip
extending from a grip has far less available force than a finger pressing
straight down, and it is doing so while partly giving up its grip. Light linear
switches are almost certainly right here; anything tactile or heavy will fight
the gesture.

### The inset rim is a tactile locator

Bottom panel thickness sets the thumb key inset depth (ADR 0009). Since these
keys are operated entirely by feel — the player cannot see the underside of the
instrument — **the rim of that recess is a feature, not a side effect.** A felt
edge tells the thumb where the key is without looking.

Worth designing deliberately: rim profile, chamfer versus sharp, and whether
adjacent keys share a recess or get individual ones. Individual recesses locate
better; a shared one is easier to sweep across. That is an M2 question.

## Spare inputs are reserved in the plate, not just in the chain

`config/key-layout.yaml` describes 14 spare shift-register bits as "free
expansion" for octave, mode and hold. **The bits are free. The plate cutouts are
not**, and a switch that is not in the DXF never exists — a deadline at **M3,
layout lock**, earlier than anything else in the mechanical track.

The switches themselves are easily sourced and can be bought later. So:

- **Reserve cutouts for three spare switches in the plate DXF** — the expected
  assignment is octave up, octave down, and a hold/preset input, which is what
  the 2021 firmware drove from key combinations and what dedicated inputs
  obviously improve.
- **Placement is an M2 question**, decided with hands on the mule, not now.
- **Eight of the spare chain bits belong to the marker pattern** (decided
  2026-09-21; this line said "four to six" until then)
  (ADR 0001) and are not available for switches. **Six remain** — three reserved
  spare-switch positions and three genuinely free. This line said "eight to ten"
  while the marker was four to six; both halves were corrected 2026-09-21. What is
  more than three.

Populating them is optional; cutting them is not.

## Tuning: equal temperament

**The instrument is 12-TET.** Microtonality, alternate temperaments and
retunable scales are declined — not because they are hard, but because they are
not wanted, and leaving the door open has a real cost in firmware surface.

So the fingering table stores **a note index**, which is what a MIDI note number
already is, and the pitch for a fingering is that index against a single
reference. Two fields stay available and default to zero because they cost
nothing and serve calibration rather than tuning:

- **A per-entry cents offset**, which is how an alternate fingering that should
  sound the *same* note gets nudged into agreement.
- **A master tune**, because A = 440 is a convention and not a law.

The multi-point calibration table (ADR 0006) already works in cents and is
unaffected — it corrects the *hardware*, not the *tuning*.

## Open

**Finger assignment within each hand.** Five keys across four left-hand fingers
means one finger takes two, or one is a side key. Six on the right hand
likewise. Left as `null` in the layout file rather than guessed; assign during
M2 when there is something to put hands on.

**What the left thumb keys actually do.** Marked `note` on the assumption they
are octave/register keys, as on a conventional woodwind. The 2021 firmware used
three left-thumb inputs for octave selection across a four-octave span,
including bridged positions. Confirm at M2.
