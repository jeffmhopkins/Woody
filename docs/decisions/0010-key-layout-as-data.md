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

## Open

**Key count.** Top keys plus three or four left-thumb keys on the underside —
total not yet decided. This blocks M2 and the shift-register chain length.
