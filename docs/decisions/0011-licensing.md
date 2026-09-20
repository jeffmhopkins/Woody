# 0011 — Licensing

**Status:** Accepted

## Context

The previous project, Open Woodwind Project, was public with **GPLv3** firmware
(the licence header appears in `src/owp/owp.ino`). This project is also public.

Hardware and CAD are not well served by software licences, so open hardware
projects typically split them.

## Decision

**Three share-alike licences, one per kind of work.**

| Path | Licence | SPDX |
|---|---|---|
| `firmware/`, `tools/` | GNU General Public License v3.0 only | `GPL-3.0-only` |
| `hardware/`, `mechanical/` | CERN Open Hardware Licence v2 — Strongly Reciprocal | `CERN-OHL-S-2.0` |
| `docs/`, `README.md`, `ROADMAP.md` | Creative Commons Attribution-ShareAlike 4.0 | `CC-BY-SA-4.0` |
| `config/` | `GPL-3.0-only` **or** `CERN-OHL-S-2.0`, at the user's option | both |

Full texts live in `LICENSES/`, and the root `LICENSE` file is the summary a
reader will actually find.

### Why not one licence for everything

Because the wrong licence is not merely untidy — it is unenforceable or
meaningless against work it was not written for.

The GPL is built around "source code", "object code" and "linking". None of
those terms has a sensible reading against a DXF, a bill of materials or a
laminated stack drawing. CERN-OHL is built around "Available Component",
"Product" and "Design"; none of *those* has a sensible reading against a
firmware image. Picking one for the whole repository means picking one that does
not fit two thirds of it, and the reciprocal obligation — the only reason to
choose these licences rather than MIT and CC-BY — is exactly what stops working
when the terms do not map.

All three are share-alike, so the intent is uniform even though the instruments
are not: **derivatives stay open on the same terms.**

### Why these three specifically

- **GPLv3 continues the 2021 project**, whose firmware carried it. Anyone
  deriving from both gets one licence, not a compatibility problem.
- **CERN-OHL-S is the strong-reciprocal open hardware licence**, and the closest
  analogue to GPLv3 in intent. It is also what comparable open instrument and
  Eurorack projects use, which matters more than elegance — a licence nobody in
  the field recognises creates friction without creating freedom.
- **CC-BY-SA is the normal choice for documentation**, and the ADRs are the most
  reusable thing in this repository.

### `config/` is dual-licensed on purpose

`config/key-layout.yaml` is the single source of truth for both the firmware's
key-to-bit mapping and the DXF that cuts the aluminium plate (ADR 0010). It is
genuinely a source file *and* a hardware design document.

So it carries both licences, usable under either. **This is not a technicality
to be tidied away later.** The entire reason that file exists is that one
artefact feeds both sides; drawing a licence boundary through the middle of it
would recreate precisely the divergence it was created to prevent.

## Consequences

- Settled early, which is the only time it is cheap. Relicensing later requires
  the agreement of every contributor, and that cost only grows.
- Contributors accept that derivative firmware, hardware and documentation all
  stay open. That is the intent, not a side effect.
- A commercial derivative is not prevented, but it cannot be closed.
- New top-level directories need a row in the table. The root `LICENSE` file is
  the one to update; individual files may carry `SPDX-License-Identifier`
  headers, which are authoritative where present.
