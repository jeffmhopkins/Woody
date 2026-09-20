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

## Open

**Finger assignment within each hand.** Five keys across four left-hand fingers
means one finger takes two, or one is a side key. Six on the right hand
likewise. Left as `null` in the layout file rather than guessed; assign during
M2 when there is something to put hands on.

**What the left thumb keys actually do.** Marked `note` on the assumption they
are octave/register keys, as on a conventional woodwind. The 2021 firmware used
three left-thumb inputs for octave selection across a four-octave span,
including bridged positions. Confirm at M2.
