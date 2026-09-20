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

| Group | Count | Face |
|---|---|---|
| Left hand | 5 | top |
| Right hand | 6 | top |
| Left thumb | 4 | bottom, inset (ADR 0009) |
| Right thumb | 3 | TBD — see below |

This unblocks M2 and sizes the shift-register chain (ADR 0001).

## Open

**Which face the right thumb keys sit on.** If they are on the underside like
the left thumb, they fold into the existing laminated stack. If they are on the
*side*, the frosted acrylic side panel becomes a switch plate — switches mounted
perpendicular to the main plate, which is a different mechanical problem and
interacts with the edge-lighting. Needs answering before M4.

**Finger assignment within each hand.** Five keys across four left-hand fingers
means one finger takes two, or one is a side key. Six on the right hand likewise.
Left as `null` in the layout file rather than guessed; assign during M2 when
there is something to put hands on.

**Four discrete keys under the left thumb is ambitious.** That thumb is also
carrying the instrument's weight (ADR 0005), and a thumb has limited reach
without the hand shifting. This is exactly why EWI-style instruments use octave
*rollers* rather than discrete thumb keys — a thumb rolls far more easily than
it reaches.

Worth designing for deliberately: arrange the four along an arc matching the
thumb's rotation rather than a straight line, and be open to some of them
becoming a rocker if M2 shows the reach is bad. The paper-at-1:1 step is cheap
and will answer this before anything is cut.
