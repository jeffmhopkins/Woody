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

## Pin and pole positions

From `IansLibrary.pretty/gateron-ks27.kicad_mod` (used with KS-33 switches in
that build — Gateron low-profile 1.0 and 2.0 appear footprint-compatible, though
the footprint carries the older name):

| Feature | Position | Size |
|---|---|---|
| Centre pole | (0, 0) | ⌀5.0 mm |
| Pin 1 | (2.6, 5.75) | ⌀1.5 mm drill |
| Pin 2 | (−4.4, 4.7) | ⌀1.5 mm drill |

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
