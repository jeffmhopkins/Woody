# Gateron KS-33 geometry

**Source:** measured out of [`ianmaclarty/ik`](https://github.com/ianmaclarty/ik),
an open-source 52-key split keyboard built on Gateron KS-33 switches — its
published STL top cases and KiCad footprints, not a datasheet and not a caliper.

**Both better sources have since been obtained and are banked**, so the
third-party measurements below are kept as the working record and as a check on
each other, and **the vendor drawing supersedes them wherever the two
disagree**:

| | |
|---|---|
| Vendor specification and drawing, 6 pp | `datasheets/mechanical/GATERON-KS-33-VENDOR-SPEC-DRAWING.pdf` |
| Solid model, five bodies | `datasheets/mechanical/GATERON-KS-33-3D.step` |

*This paragraph said both were "unreachable from this project's sandbox"
until 2026-09-21. `gateron.com` answers 200 now and the drawing is in the
bank; the sentence outlived its own refutation by the length of this page.*

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

> **✅ SUPERSEDED BY THE VENDOR DRAWING, 2026-09-21. The answer is 1.20 mm.**
> `gateron.com` answers 200 from this sandbox for the first time — it was
> HTTP 000 through every earlier wave — and the drawing for the exact part,
> **KS-33H10B050NN-Y24, Version 2, drafted 2023-01-03**, is banked at
> `datasheets/mechanical/GATERON-KS-33-VENDOR-SPEC-DRAWING.pdf` (6 pp).
> Sheet 6's elevation dimensions the plate slot **1.20 ±0.05 mm**; sheet 3 §8
> shows the same 1.20 against a hatched plate section. **Read by rendering both
> sheets, and that was necessary for these two numbers specifically**: the
> file's *dimension callouts* are outlined vector and yield nothing to a text
> extractor. Its *prose* is a different matter — see the bounce figure below.
>
> **Every candidate this page bracketed is outside the vendor window.** 1.5 mm
> is 0.25 mm over the upper limit, 2 mm is 0.75 mm over, and the 1.10 mm this
> section measured off the third-party build is 0.05 mm *under* the lower limit
> — close, but not the specification, and the reasoning above for why it might
> not be doing retention still applies to it.
>
> The cutout is **confirmed and tightened**: 14.00 +0.05/−0.02 × 14.00
> +0.05/−0.02, not a bare 14.0 × 14.0. The Z stack measured off the STEP solid
> below is confirmed almost exactly — collar 15.00 × 15.00, body 14.00 ±0.05,
> latch span 14.70, housing bottom 2.50 ±0.05, pin tips 5.10, centre pole
> ⌀5.05 ±0.05 reaching 5.75 ±0.05, MX cross 1.10 ±0.04 × 4.00 with a second
> 1.28 ±0.04 arm. **Overall height is NOT-IN-DOCUMENT**: neither the 12.75 mm
> measured off the STEP nor the BOM's 12.2 mm is confirmed or refuted.

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

### This answers the plate-to-PCB standoff, and at the settled thickness there is one

The pins reach **5.10 mm** below the seat and only the last **1.9 mm** is the
narrow blade that goes through a hole. So the PCB top has to sit within roughly
**3.2–3.6 mm** of the seat for the blade to fill the hole and protrude enough to
solder. Subtract the plate `[calc]`:

| Plate | Gap between plate underside and PCB top |
|---|---|
| 2 mm — over the vendor window, ruled out | 1.2–1.6 mm |
| 1.5 mm, the MX standard — over the vendor window, ruled out | 1.7–2.1 mm |
| **1.20 mm — `plate-thickness`, settled, and this page owns it** | **2.0–2.4 mm** |

> **⚠ THIS SECTION'S CONCLUSION IS REVERSED, 2026-09-21, AND SO IS THE LAYOUT
> RULE DERIVED FROM IT.** It read *"the answer is 'there isn't one'"* and
> *"either way the board is effectively hard against the plate underside"* —
> but it only ever computed the gap at 1.5 mm and 2 mm, **both of which the
> vendor drawing has since ruled out**. At the settled 1.20 mm the gap is
> **2.0–2.4 mm**, which is a standoff, not the absence of one. The old
> conclusion was arithmetic applied to two thicknesses that are no longer
> candidates.

**What that clearance actually buys**, taken at the tight end of the range and
against a plate that is grounded through `MECH-GNDBOND` and is therefore a
short waiting to happen:

| Part | Height | Clearance, worst case |
|---|---|---|
| 0402 / 0603 chip passive | ~0.5–0.6 mm | ~1.4–1.5 mm — comfortable |
| SOT-23 | ~1.1–1.45 mm | ~0.55–0.9 mm — workable |
| SOIC-16 (the `74HC165`) | 1.75 mm max | **~0.25 mm — do not** |

So the rule is **not** "there is no plate-facing side". It is: **chip passives
and SOT-23 may sit on the plate-facing side; nothing with a body over about
1.4 mm may.** That keeps the ICs on the far face, which is where they were
going anyway, and stops forcing every decoupling capacitor across to join them.

The centre pole still needs a **⌀5.25 mm clearance hole through the plate *and*
the PCB**: its tip is at −5.70 mm against a PCB top at −3.2 to −3.6 mm, so on a
1.6 mm board it protrudes **0.5–0.9 mm** below the underside `[calc]`.

> **`hardware/cluster/cluster-boards.md` §"Three layout rules that are not
> obvious" still carries the reversed conclusion** — *"there is no plate-facing
> side: put every passive on the far face"*, cited to this page, and computed
> against the same withdrawn 1.5–2 mm bracket. **That page has to follow this
> one**; it is outside this file to change.

### And the retention clip may not be a clip

> **The wait is over: the drawing is banked and the slot is 1.20 ±0.05 mm** (see
> above). What follows was written from the STEP solid while the drawing was
> unobtainable. It is not refuted — Gateron dimensions the *slot*, not the
> mechanism that fills it — and the observation below about the 2.50 mm
> through-section is now moot for 2 mm plates, which are simply out of spec.

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
| **Contact bounce** | **5 ms max, at 16 in/sec actuation speed** |
| Operating force | 50 ±15 gf |
| Electrical rating | 12 V AC/DC max, 2 V DC min; 10 mA max, 10 µA min |
| Contact / insulation resistance | 200 mΩ max / 100 MΩ min at 100 V DC |

> **The bounce figure is vendor-published and was recorded here as
> unobtainable for four review waves.** It is item 5 of the specification block
> on sheet 6 of `datasheets/mechanical/GATERON-KS-33-VENDOR-SPEC-DRAWING.pdf`,
> verbatim: *"Bounce Time: 5msec Max.(at 16 in/sec. actuation speed)"* — and
> it is in that sheet's **extractable text layer**, not only in the picture.
> This page, `repo-maintenance.md` §3 and `pcb-pipeline.md` all described that
> document as vector CAD that yields no text. It yields 11 kB of it; what it
> does not yield is the *dimension callouts*, which is why the plate thickness
> genuinely did have to be read off a render and the bounce time never did.
>
> **It is a maximum at a stated actuation speed, not a typical**, and 16 in/sec
> (≈0.41 m/s) is a brisk keystroke. Milestone M1's job changes from "find out
> whether there is a number" to "measure the typical at a musical actuation
> speed, and confirm it comes in under the published maximum."
>
> **The consequence is in `docs/reference/latency-budget.md`**, which books the
> release-filter window and now states what this bound does to it. ADR 0001's
> note-on gate is two samples 250 µs apart — twenty times shorter than this
> window — so the gate does not reject bounce and was never meant to; the
> asymmetric release filter does.

## Not available anywhere, still needs a scope

The actuation/reset **hysteresis gap**. Sheet 6 draws a force-travel diagram
with an *operating point* and a *reset point* marked, and dimensions neither:
pretravel is given (1.70 mm), the reset travel is not, so the gap cannot be
derived from the published numbers. Milestone M1.

## Sources — all four reached, both artefacts banked

- Gateron 3D models: <https://www.gateron.com/pages/3d>
- KS-33 Low Profile 2.0 datasheet: <https://www.gateron.co/pages/gateron-ks-33-low-profile-2-0-mechanical-switch-datasheet>
- Product specification index: <https://www.gateron.com/pages/product-specification>
- GrabCAD community model: <https://grabcad.com/library/gateron-low-profile-ks-33-1>

*This section was headed "Sources to pull when the network allows" and ended
"drop the STEP into `mechanical/` when obtained". It has been obtained:
`datasheets/mechanical/GATERON-KS-33-3D.step` is the solid the Z-stack section
above is measured from, and the vendor drawing is banked beside it. The stack
has been modelled against the real solid; the instruction is done.*

**What is still third-party** and should be treated as a bracket rather than
specification: the 14.0 mm cutout evidence from `ianmaclarty/ik`'s STL cases,
the 1.10 mm web measured in that build, and the pin/pole positions from the two
KiCad footprints. Each is confirmed by the vendor drawing where the drawing
says anything, and each is the only source where it does not.
