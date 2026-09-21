# Gateron KS-33 geometry

**Source:** measured out of [`ianmaclarty/ik`](https://github.com/ianmaclarty/ik),
an open-source 52-key split keyboard built on Gateron KS-33 switches — its
published STL top cases and KiCad footprints, not a datasheet and not a caliper.

Gateron's own datasheet and STEP model are the better source and are linked at
the bottom. They are unreachable from this project's sandbox (the egress proxy
rejects `gateron.com` and `gateron.co`), so this file records what could be
obtained, and **the vendor drawing supersedes it wherever the two disagree.**

## Plate cutout: 14.0 × 14.0 mm

**The same as standard MX.** ADR 0002 previously asserted the opposite —
*"Gateron low-profile does not use the standard 14 mm MX cutout"* — and that was
wrong.

Measured by extracting vertical wall loops from the two top-case meshes and
searching for axis-aligned square corner sets:

| | |
|---|---|
| `lefttop.stl` | **23** cutouts at exactly 14.000 × 14.000 mm |
| `righttop.stl` | **24** cutouts at exactly 14.000 × 14.000 mm |
| Key pitch in that design | 19.0 mm (not the 19.05 mm MX standard) |

47 cutouts across a working build, all at the same figure to four decimal
places. That is not a coincidence or a rounding artefact.

## Plate thickness in that build: 1.10 mm

Each cutout's wall spans z = 1.9 → 3.0 mm inside a case whose full extent is
0.7 → 7.0 mm. So the switch passes through a **1.1 mm web**, not through the
full case thickness.

**This is evidence, not specification.** That case is 3D printed and its PCB sits
directly beneath the switches, so the plate may not be doing retention at all
there. What the number is good for is bracketing: standard MX plates are
1.5 mm, this KS-33 build used 1.1 mm, and **neither is 2 mm.** See ADR 0002 for
what that means for an aluminium plate.

## The Z stack, measured off a solid model — 2026-09-21

`datasheets/mechanical/GATERON-KS-33-3D.step` is a five-body STEP solid
(`PRODUCT('Gateron_KS_33_v3')`), measured with OpenCASCADE rather than read off
a drawing. **It is third-party CAD, not a Gateron document** — gateron.com and
the archive are both unreachable and no vendor file exists on GitHub. Treat the
numbers as the best available bracket, not as specification.

Datum: **z = 0 at the underside of the 15 × 15 mm collar** — the only surface
on the switch that can seat on a plate.

| Feature | Position |
|---|---|
| Collar, the plate seat | 15.0 × 15.0 mm, 0.50 mm thick, z = 0 → +0.50 |
| **Section that passes through the cutout** | 14.0 × 14.0 mm, **only 2.50 mm deep** |
| Housing bottom | **−2.50 mm** |
| Pin blades, narrow through-hole section | −3.2 → **−5.10 mm** |
| Centre pole, ⌀5.04 mm | tip at **−5.70 mm** |
| Stem top, MX cross | +7.05 mm |
| Overall | 15.0 × 15.0 × **12.75 mm** |

### This answers the plate-to-PCB standoff, and the answer is "there isn't one"

The pins reach **5.10 mm** below the seat and only the last **1.9 mm** is the
narrow blade that goes through a hole. So the PCB top has to sit within roughly
**3.2–3.6 mm** of the seat for the blade to fill the hole and protrude enough to
solder. A 2 mm plate leaves 1.2–1.6 mm; a 1.5 mm plate leaves 1.7–2.1 mm.

**Either way the board is effectively hard against the plate underside.**
`cluster-boards.md` assumes a standoff exists and uses it for component height
on the plate-facing side. It does not exist. The centre pole also needs a
**⌀5.25 mm clearance hole through the plate *and* the PCB**, protruding ~2 mm
below the board.

### And the retention clip may not be a clip

`ks33-geometry.md` and ADR 0002 have both been waiting on "the clip dimension
from Gateron's drawing". **This model has no horizontal clip shoulder at all.**
What it has is four tapered flexing arms on the ±X sides, whose outer faces run
**14.69 mm at the bottom widening to 14.99 mm just under the collar** — 0.35 to
0.49 mm proud of the 14 mm cutout per side, **widest at the top**. There is no
downward-facing ledge anywhere.

If that is real geometry rather than CAD simplification, retention is an
**interference press against flexing arms**, not a snap — and ADR 0002's "at
2 mm the clips will not engage at all" is the wrong shape of worry. The right
worry is the 2.50 mm through-section: a 2 mm plate consumes 80 % of it.

## Pin and pole positions

From `IansLibrary.pretty/gateron-ks27.kicad_mod` (used with KS-33 switches in
that build — Gateron low-profile 1.0 and 2.0 appear footprint-compatible, though
the footprint carries the older name):

| Feature | Position | Size |
|---|---|---|
| Centre pole | (0, 0) | ⌀5.0 mm |
| Pin 1 | (2.6, 5.75) | ⌀1.5 mm drill |
| Pin 2 | (−4.4, 4.7) | ⌀1.5 mm drill |

**Independently confirmed 2026-09-21** by a second footprint from a different
library, `datasheets/mechanical/GATERON-KS-33-SW_KS33_1u.kicad_mod`
(`descr "Footprint for Gateron KS33 switches"`): same two pin positions, drill
**⌀1.2** rather than ⌀1.5, centre pole **⌀5.25**, and its `Eco2.User` layer
draws the plate cutout as **14.0 × 14.0 mm with R0.5 corners** — a third
independent source for the 14 mm cutout, alongside the 47 STL cutouts above.

The STEP model shows why ⌀1.2 is the better number: **the pins are flat blades,
2.0 × 0.45 mm at the root narrowing to 1.0 × 0.45 mm** through the
board — not round pins.

**There are no alignment posts.** The repository's combined `gateron-ks27-mx`
footprint carries MX's two ⌀1.75 mm posts at (±5.08, 0) *and* MX's own pin
positions at (3.81, 2.54) and (−2.54, 5.08) — all of which are absent from the
low-profile-only footprint.

That is the important structural fact for this project: **an MX switch is
located by its plate cutout and two posts; a KS-33 is located by the cutout
alone.** ADR 0002 calls the cutout "the precision feature of the entire build",
and this is why.

## Published specification

| | |
|---|---|
| Height | 12.2 mm |
| Pretravel | 1.70 mm |
| Total travel | 3.00 mm |
| Pins | 3-pin, SMD LED support |
| Materials | POM stem, PC top housing, nylon bottom |

## Not available anywhere, still needs a scope

Contact bounce duration and the actuation/reset hysteresis gap. Gateron
publishes travel and force but neither of these, for this switch or most others.
Milestone M1.

## Sources to pull when the network allows

- Gateron 3D models: <https://www.gateron.com/pages/3d>
- KS-33 Low Profile 2.0 datasheet: <https://www.gateron.co/pages/gateron-ks-33-low-profile-2-0-mechanical-switch-datasheet>
- Product specification index: <https://www.gateron.com/pages/product-specification>
- GrabCAD community model: <https://grabcad.com/library/gateron-low-profile-ks-33-1>

Drop the STEP into `mechanical/` when obtained, and model the stack against the
real solid rather than the numbers above.
