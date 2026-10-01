# Instrument body — parametric CAD

*Installing the tools and the day-to-day loop: [`docs/reference/tooling.md`](../docs/reference/tooling.md)
(`sudo bash tools/setup-env.sh` installs everything).*

> **Status:** first model, 2026-09-26. **Layout is PROVISIONAL**: every key
> position in `config/key-layout.yaml` is still `null` (they are M2/M3
> outputs), so keys are placed on ADR 0009's length budget and every render
> says so in its footer. Keys are **flush with the top face at full travel**
> — thumb keys included, on the bottom face. **There is no display board**:
> the LED matrix is the instrument's only display (ADR 0015, 2026-09-26).

The body described in [ADR 0009](../docs/decisions/0009-enclosure-construction.md)
— a laminated stack of flat parts, every layer a 2D through-cut — as an
OpenSCAD model, with renders and cut files generated from it and a ledger that
proves each one still shows the model it names.

*The Eurorack module is a separate model in the same pipeline:
[`module/README.md`](module/README.md).*

![The instrument, key face up](renders/hero.png)

![The mouth end close up: oak cap and sanded edges](renders/detail-mouth-end.png)

## Photographs

Rendered in Blender (Cycles) by [`tools/render-instrument.py`](../tools/render-instrument.py),
ledgered and stamped like every other output here. The shell, plates, columns,
keycaps and tail equipment are the body CAD's own solids, one per named solid;
**the boards are the real ones** - each `.kicad_pcb` exported with every part's
3D model, its copper, mask and silk (colours from its `layout.yaml` `fab:`),
placed in the CAD's frame, and refused if its outline disagrees with the CAD's
by more than 0.05 mm. Explode distances are picture conventions in
[`config/render.yaml`](../config/render.yaml). The wood is ADR 0009's finish
(dark stain, grain showing, satin) drawn procedurally - illustrative, not a
photograph of a board. **Sides rendered clear to show the inside; the
instrument's sides are frosted** (ADR 0009) - a render-only choice
(`config/render.yaml` `side_glass`, owner 2026-10-01), said again in each
picture's footer.

![The instrument, three-quarter view](renders/photo-hero.png)

| | |
|---|---|
| ![Open](renders/photo-open.png) Oak top, key plate and the near side off: the cassette in the shell | ![Underside](renders/photo-underside.png) From below, the oak bottom off: the bottom plate and its windows under the through-hole tails |
| ![Mouth end](renders/photo-board-mouth.png) The main board at the mouth end, the LED row lit under the left key board | ![Tail end](renders/photo-board-tail.png) The tail end, key boards off: J-MCU, the regulator, J-UMB on the tongue, the etherCON's adapter |

![The whole instrument pulled apart along its stack](renders/photo-exploded.png)

![The cassette alone, pulled apart in its build order](renders/photo-cassette.png)

## The maker's mark

![The maker's mark on the oak top, between the mouth cap and the first key](renders/photo-logo.png)

The Space Coast Synthesizers orbit-wave mark ([`branding/`](../branding/README.md))
sits on the oak top's playing face **between the mouth cap's seam and the
first left-hand key's cap slot** (owner, 2026-10-01: "Logo should be here,
scale as appropriate"; ADR 0009, *Amended 2026-10-01*). It is turned with
its top to the mouth end, so it reads upright in the plan drawings and to an
audience, its wave running across the body, and centred in that band. It is
**etched and filled with epoxy** in branding's colour-fill scheme - the ring
one pour, the wave and the moon the other - and sanded flush.

Where each number lives, so none is restated here:

- **Scale, turn, offset, etch depth, fill and margins**: `config/body.yaml`
  `logo`, each with its reasoning. The scale is `logo.scale` of the artwork's
  own size, which `branding/export/spec.json` owns.
- **The band, the mark's size on the body, its margins, the oak left over
  the column screws' pockets and its smallest gap once scaled**:
  [`drc.echo`](drc.echo), the rules starting "logo".
- **The artwork and its colours** are read from `branding/` by `tools/cad.py`
  (`branding()`, into `cad/generated/params.scad`), never copied: the DXF is
  imported as it is, the colours are `EPOXY` in `branding/build.py`.
- **The laser file**: [`export/oak-logo.dxf`](export/oak-logo.dxf), the etch
  in the oak panels' frame, as the pockets and rebates are.

**Open:** scaled to fit, the mark's gaps are under branding's laser guideline,
so an **etch test on an offcut** of the top's own board comes first (ROADMAP,
*Bench measurements*).

## The one rule

**Change the YAML, run the build, commit what it produced.** Never draw a
number into the `.scad`, and never touch a file under `renders/`, `export/`
or `cad/generated/`.

```
config/key-layout.yaml ─┐                           ┌─> renders/*.png   (stamped)
config/body.yaml ───────┼─> cad/generated/params.scad ─> woody_body.scad ─┼─> export/*.dxf    (cut files)
datasheets/…  (STEP, DXF)─> cad/vendor/*.stl ────────┘                     └─> drc.echo        (design rules)
                                                         every arrow fingerprinted in OUTPUTS.csv
```

```
python3 tools/cad.py build          # regenerate params, rebuild whatever is stale
python3 tools/cad.py check          # exit 1 if any output no longer matches its sources
python3 tools/cad.py explain hero   # which input moved, and the commit it was built from
```

`check` runs from the commit gate (`tools/check-staleness.py`) and needs
nothing but Python. `build` needs OpenSCAD 2021.01+, `xvfb-run` on a machine
without a display, Pillow (for the stamp), and gmsh (`pip install gmsh`, plus
apt `libxft2`) to mesh the vendor STEP files.

## How staleness is tracked

A picture cannot be grepped, so no forbidden pattern will ever catch a render
of a superseded value. Instead:

- **Every output has a fingerprint**: a hash over its recipe in
  [`outputs.yaml`](outputs.yaml) and the git blob id of **every file it was
  built from**, found by walking `include`/`use`/data-file references from its
  source. The build cross-checks that walk against OpenSCAD's own dependency
  file and refuses to trust a fingerprint the two disagree on.
- **[`OUTPUTS.csv`](OUTPUTS.csv) is the ledger**: fingerprint, the output's own
  hash, and each input's blob id. `check` recomputes all of it. It reports an
  output as **STALE** when an input moved (naming the file), as **edited** when
  the output no longer hashes to what the ledger vouches for, and as an
  **orphan** when a PNG or DXF exists that no spec entry builds.
- **The fingerprint is stamped into every render's footer**, because the reader
  looks at the picture, not the ledger. A render pasted anywhere still says
  `cad <fingerprint>`, and `explain` turns that back into the git commits it was
  built from.
- **A config change is caught before it reaches a picture**: `params.scad`
  must equal what the YAML generates, and `check` lists every output fed by it.
- **Pages here may only show tracked outputs.** An image link in a
  `mechanical/**/*.md` page that is not in the ledger fails `check`.
- **`RECIPE` in `tools/cad.py`** is part of every fingerprint. Bump it when you
  change *how* outputs are made (stamp, mesh settings, render flags) — the
  tool's own source is deliberately not an input, so this is the one manual
  step, and forgetting it was the first bug this pipeline had.

## What is here

| Path | What it is |
|---|---|
| [`cad/woody_body.scad`](cad/woody_body.scad) | The model. Every flat part as a 2D module in its own sheet frame; the assembly places them. `part=` selects one |
| `cad/fig_*.scad` | Figure sources with dimensions and labels, drawn from the same variables as the parts. They sit beside the model because OpenSCAD resolves `import()` against the top-level file |
| `cad/lib/annot.scad` | Dimension and label helpers (from JBrain2's back-plate CAD) |
| `cad/generated/params.scad` | **Generated.** Every number the model uses, with its source and status |
| `cad/vendor/*.stl` | **Generated.** The banked KS-33 STEP solid, meshed |
| [`outputs.yaml`](outputs.yaml) | Every output: cameras, defines, paths. The build does exactly this list |
| [`OUTPUTS.csv`](OUTPUTS.csv) | **Generated.** The fingerprint ledger |
| [`drc.echo`](drc.echo) | **Generated.** The design-rule report — read it after every change |
| [`clash.txt`](clash.txt) | **Generated.** The interference check: every named solid against every other |
| [`clash-allow.yaml`](clash-allow.yaml) | Interference the design intends, each with its reason |
| `export/*.dxf` | **Generated.** One file per flat part, as it goes to the cutter |
| `renders/*.png` | **Generated.** Every image on these pages |
| [DESIGN.md](DESIGN.md) | How the stack is built, where each number comes from, and what the first model found |

## The views

| | |
|---|---|
| ![Underside](renders/underside.png) Underside: thumb recesses, both thumb rests, U-bolt | ![Exploded](renders/exploded.png) The stack, pulled apart |
| ![Internals](renders/internals.png) Oak top and key plate off | ![Internals, far side](renders/internals-far.png) Oak top and key plate off, from the far side: the ribbons |
| ![Tail](renders/tail-detail.png) The tail from inside | |
| ![Main board](renders/main-board-3d.png) The main board: thumb switches and carrier circuits on one board, in yellow | |

![The main board, labelled](renders/main-board.png)

### Breakdowns

![The stack pulled apart, shell ghosted](renders/exploded-stack.png)

| | |
|---|---|
| ![Electronics](renders/breakdown-electronics.png) The electronics in yellow | ![Structure](renders/breakdown-structure.png) The structure in yellow, pulled apart |
| ![Breath path](renders/breakdown-breath.png) The breath path at the mouth end | ![From the tail](renders/view-tail.png) The tail from outside, oak top and key plate off |

![Section through the thumb row](renders/section-thumb-row.png)

| | |
|---|---|
| ![Tail wiring](renders/breakdown-tail-wiring.png) The etherCON on its adapter, joined by J-UMB to the main board's tongue, and the Matrix's ribbon | ![Tail wiring, far side](renders/breakdown-tail-wiring-far.png) The Matrix ribbon's drop into J-MCU |
| ![Ribbons](renders/breakdown-ribbons.png) The key boards' ribbons and connectors, lid, sides and oak bottom off | ![Ribbon fold](renders/section-ribbon.png) Section along the body through the left key board's chain headers: the ribbon's hairpin, closed |

![Plan from above, with the length budget](renders/plan-top.png)

![Top-key spacing, now against the alternatives](renders/key-layouts.png)

Top-key spacing comes from `docs/research/2026-09-26-finger-spacing/`:
graded, wider under index-middle-ring and tighter to the little finger. The
little finger starts on a side-by-side pair, and the right little finger has
a single key below its pair, in line with the pair's outer key (ADR 0010). At
the tightest gap an oak web between individual cap holes would be zero, so
the oak top has **one slot per hand** (`stack.cap_holes`).

![Plan from below](renders/plan-bottom.png)

![Longitudinal section](renders/section-long.png)

| | |
|---|---|
| ![Cross-section through RH3](renders/section-key.png) | ![Tail face](renders/tail-face.png) |
| ![Cross-section through the LED matrix](renders/section-matrix.png) The frosted window, flush on its oak lip | ![Section through a key-board corner](renders/section-kb-mount.png) A column at a key board's corner (ADR 0025): the stud in the bottom plate, a spacer, the main board, the standoff faced to the gap, the key board, a spacer, the key plate, and the screw whose head sits in a blind pocket in the oak top |
