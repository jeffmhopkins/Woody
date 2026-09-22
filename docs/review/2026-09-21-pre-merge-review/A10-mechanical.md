# A10 — Mechanical: does it fit, and can it be built?

**Agent:** A10, cold. No directory under `docs/review/**` was read.
**Date:** 2026-09-21
**Slice:** the 10HP module panel and the laminated instrument body — panel
height budget, the etherCON at both ends, plate thickness and switch
retention, the key cutout and achieved fit, the loom through the side channel,
and the ROADMAP's ordering rules.
**Findings are node-indexed** (BOM refdes or named assembly). **Report only —
nothing was fixed.**

---

## Provenance conventions used here

- `[dxf]` — **extracted** from `datasheets/connectors/NE8FDP.dxf` by parsing
  entities and the text layer. Not read by eye.
- `[step]` — **extracted** from `datasheets/mechanical/GATERON-KS-33-3D.step`
  by parsing `CARTESIAN_POINT` coordinates. Not read by eye.
- `[py]` — **extracted** from the banked
  `datasheets/mechanical/EURORACK-3U-PANEL-HP-TABLE-make_blanks.py`, which is
  plain source.
- `[render, not re-verified]` — **a dimension that exists only in a vector
  drawing with no text layer**, recorded in this repo from a 150 dpi render
  read by eye. **I could not re-read any of these.** This sandbox has no
  rasteriser: no `pdftoppm`, no `mutool`, no `gs`, no PyMuPDF. I decompressed
  every stream in the Gateron PDF and the text is CID-outlined — searching the
  extracted show-operators for `1.20`, `1,20`, `14,00`, `5.25`, `2.50` returns
  **zero** hits. Every figure so marked below rests entirely on the earlier
  render, not on anything I checked.
- `[repo] path:line`, `[calc]` with arithmetic, `[from memory]` as usual.

**One method note that is worth more than a finding.** The corpus records the
Neutrik dimensions as read by rendering `NE8FDP.pdf` (true — that PDF has no
text layer). **Its companion `NE8FDP.dxf`, banked beside it, has a full text
layer and every dimension is machine-extractable.** I took all of them that
way. See A10-06.

---

## Summary

| | |
|---|---|
| Findings | 24 |
| Confirmations (checked, and the corpus is right) | 5 |
| High severity | 8 |
| Tracked figures with a live escaped value | **2** — `panel-height-budget`, `chain-conductors` |
| Checker state while those are live | `PASS no live stale values` |

**The two things worth reading if nothing else:**

1. **`ROADMAP.md:203` — the row that asks my question 5 and gates it "before
   the plate DXF is cut" — states the wrong conductor count**, and escapes its
   own `forbidden` list by letter case alone (A10-24).
2. **The instrument tail does not close.** The etherCON's published **4 mm max
   panel thickness** meets a **6–8 mm oak end cap**, and the corpus's stated
   resolution does not address the clamped thickness at all (A10-09).

---

## 1. The panel height budget

### A10-01 · `PANEL` · CONFIRMED — every number in the budget re-derives

I rebuilt `panel-height-budget` from the banked artefacts rather than from the
owner ADR, and it holds.

Clear height `[py]` + `[calc]` — I re-extracted the Doepfer table from the
banked generator rather than trusting the quotation of it:

```
[py]  HEIGHT = 128.5 ; HOLE_Y = (3.0, 125.5) ; HOLE_DIA = 3.2
      10: {"width": 50.50, "holes": x = 7.50, 43.06}

[calc]  clear = 128.5 − 2 × (3.0 + r)
        ISO 7045 pan head, dk max 5.6, r = 2.8  →  128.5 − 11.6 = 116.9
        DIN 125 M3 washer, OD 7.0,    r = 3.5  →  128.5 − 13.0 = 115.5  ← assumed
        knurled thumbscrew, OD ~10,   r = 5.0  →  128.5 − 16.0 = 112.5
```

Screw-blocked width `[calc]`: `7.50 ± 3.5 = [4.00, 11.00]` and
`43.06 ± 3.5 = [39.56, 46.56]` — matches the register's `[4.0, 11.0]` and
`[39.6, 46.6]`, and the central clear width is `39.56 − 11.00 = 28.56 mm`,
matching "28.6 mm".

Content `[calc]`: `5 + 22 + 39 + 31 + 13 = 110`. Jacks `3 × 13 = 39`. Spare
`115.5 − 110 = 5.5`; per boundary `5.5 / 4 = 1.375 ≈ 1.4`; on the thumbscrew
assumption `112.5 − 110 = 2.5`. All as stated.

Toggle row `[calc]`: `10.5 × sin 25° = 4.437 ≈ ±4.44 mm`. Strips beside the
flange `(50.50 − 26)/2 = 12.25`. D6.5 centred in a strip:
`12.25/2 − 3.25 = 2.875 ≈ 2.88`. D6.2: `6.125 − 3.10 = 3.025 ≈ 3.02`. D3.2 LED
bezel: `6.125 − 1.60 = 4.525 ≈ 4.52`. The 6HP comparator `3.09 mm` is
`(30.18 − 24.0)/2 = 3.09` — the **bore**-referenced web, correctly the same
quantity being compared against.

**The conclusion "it fits on every hardware assumption" is sound.** This is the
best-derived figure in my slice and it should not be reopened.

### A10-02 · `PANEL` · HIGH — the superseded budget is live in `hardware/bom.csv`, and it escaped its own `forbidden` list by a space

`hardware/module/panel-led/bom.csv:2` (the fragment) and therefore
`hardware/bom.csv:62` (the generated master) carry the **four-row** budget that
`panel-height-budget` retired, including its total and its spare:

> `Derived budget: 5 label + 22 pots + 39 jacks (3 rows x 2 cols @13mm) + 31
> etherCON-with-toggle-and-LED-beside-it = 97mm, 13mm spare`

That is the layout in which **the toggle shares the etherCON row** — precisely
the arrangement the register's `toggle_row` note rejects, on a hole a player
flips repeatedly in 2 mm aluminium. The same row also restates `~115mm against
~110mm usable` and `'107mm of ~110mm'`.

**Four retired values, four misses, each by one removed space** `[calc,
verified by running the checker's own matcher]`:

| `forbidden` pattern | actual spelling in `bom.csv` | matches? |
|---|---|---|
| `13 mm spare` | `13mm spare` | no |
| `97 mm against ~110 mm` | `= 97mm` | no |
| `~115 mm against ~110 mm usable` | `~115mm against ~110mm usable` | no |
| `107 mm of ~110 mm usable` | `107mm of ~110mm` | no |

`tools/check-staleness.py:170` matches with `text.find(bad, start)` — a
case-sensitive literal find with no whitespace normalisation `[repo]`. The
checker therefore reports `PASS no live stale values` with all four live.

This is the fifth or sixth recorded instance of the mechanism `figures.yaml`'s
own `escape_note` describes, and it is on **the most-cited file in the
repository**. It is also the exact shape the note predicts: the `forbidden`
list was written in the prose spelling of the ADR being edited, and `bom.csv`
spells millimetres without a space throughout.

**Not a fix, but the shape of one:** `bom.csv` and its fragments spell every
dimension `NNmm`. Any `forbidden` pattern containing ` mm` needs a `NNmm`
sibling, or the matcher needs to normalise whitespace before comparing. The
latter would have caught all four with no list edit.

### A10-03 · `PANEL` · MEDIUM — ADR 0004's closing caveat refers to a number that is no longer in the document, and to blocked sources that are now banked

`docs/decisions/0004-cv-interface-module.md:833`:

> The **97 mm above** is built from `[from memory]` component envelopes — the
> Neutrik drawing, the Thonkiconn panel dimension and the pot bushing were all
> behind a blocked proxy through three review waves. **The layout is credible
> and it is not verified.**

Two problems.

- **There is no 97 mm above.** `grep` finds `97 mm` in exactly two places in
  the whole corpus: this line, and its own `forbidden` entry in
  `config/figures.yaml:285` `[repo]`. The blockquote survived the rewrite that
  deleted what it points at.
- **All three named sources are banked and were read.** The Neutrik drawing is
  `datasheets/connectors/NE8FDP.pdf` + `.dxf` — cited by this same ADR 40 lines
  earlier at `:696` ("now read off the vendor drawing"). The Thonkiconn
  dimension is `connectors/PJ398SM-drawing.jpg` (body 9 × 9 × 8.3, bushing OD 6
  with 4.5 of thread) `[repo] datasheets/MANIFEST.csv`. The pot bushing is
  `connectors/RV09AF-40.pdf` and `R0904N.pdf` (body 9.8 wide, 11.4 across the
  snap-in lugs, shaft ⌀6.0). The caveat's "credible and not verified" is
  therefore harsher than the evidence, and it is the last thing a reader of
  that section sees.

The 1:1 paper check should survive regardless — see A10-04 — but for the reason
in A10-04, not this one.

### A10-04 · `PANEL` · OBSERVATION — the budget's rows are pitch allocations, not component envelopes, and two rows have no clearance inside them

This is not a defect; it is what the "print at 1:1" gate is for, and it is
worth stating so the gate is not skipped as redundant.

- **Jacks, 39 mm.** Three rows at 13 mm pitch occupy `2 × 13 + 9 = 35 mm` of
  actual extent `[calc; jack body 9 mm, banked Thonk drawing PJ398SM]`. The
  allocation is 4 mm generous.
- **etherCON, 31 mm.** That is the flange height exactly `[dxf]`. Zero
  allowance inside the row.
- **Toggle, 13 mm.** Lever sweep `2 × 4.44 = 8.88 mm`, body 7.9 mm `[render,
  not re-verified — NKK Series M p.11]`. ~2 mm of allowance.

So four of the five row boundaries are funded entirely out of the 5.5 mm
global spare — 1.375 mm each. That is a real fit and the ADR says so. Keep the
1:1 print.

### A10-05 · `KNOB-BREATH` · MEDIUM — the knob constraint is right and its edge margin is undocumented

`3d + 2 × 3` reproduces the table exactly: 20 → 66, 16 → 54, 15 → 51, 14 → 48
`[calc]`. Confirmed.

Two things follow that no document states:

- **The 3 mm gaps are knob-to-knob only.** Nothing says so. A reader applying
  3 mm at the panel edges too gets `48 + 6 = 54 mm` and concludes 14 mm does
  **not** fit. Given how many of this project's defects are one reader
  re-deriving a number a different way, the formula wants writing out.
- **The outer knobs clear the panel edge by 1.25 mm** `[calc]`
  `(50.50 − 48)/2`, and `panel-width` is `+0/−0.2`, so worst case **1.15 mm**.
  That is smaller than the 3.09 mm web this same ADR rejected on stiffness
  grounds — a different kind of margin (no hole, no repeated load) so not the
  same objection, but it is the tightest unstated dimension on the panel and
  it belongs on the 1:1 print.

---

## 2. The etherCON at both ends

### A10-06 · `J-UMBILICAL` · CONFIRMED, and the source of record should change

I re-derived the whole Neutrik geometry **by extraction, not by eye**, from
`datasheets/connectors/NE8FDP.dxf` `[dxf]`:

| Quantity | Extracted | Corpus |
|---|---|---|
| Panel bore | ⌀48.000 on paper at 2:1 → **⌀24.000** | ⌀24.0 min ✓ |
| Screw clearance holes | 2 × ⌀6.400 → **⌀3.200** | ⌀3.2 min ✓ |
| Screw hole positions | (±9.500, ±12.000) from the bore centre | (±9.5, ±12.0) ✓ |
| Screw pitch | 19.000 × 24.000 | 19 ±0.1 × 24 ±0.1 ✓ |
| Flange | MTEXT `26` and `31` | 26 × 31 ✓ |
| Depth behind panel | MTEXT `34,55` and `36,3` | 34.55 / 36.3 ✓ |
| Body | `18,05` `4,5` `25,5` `27,64` `13,2` `15,9` `19,8` | same list ✓ |
| Title block | `NE8FDP` ×2, `ST-NE8FDP`, `Payr`, `03.12.02`, changed `04.02.05`, `Aend.-Index B`, `2:1`, `A3` | ✓ |

Every number the corpus holds is correct, and the two screw holes are
genuinely diagonal (dx and dy both change sign together).

**The change worth making:** `docs/reference/pcb-pipeline.md:256` warns that
"the Neutrik outlines" are vector with no text layer and the dimensions "exist
only in the picture". That is true of `NE8FDP.pdf` and **false of the DXF
banked beside it**, which carries the dimensions as `MTEXT`/`TEXT` and the
geometry as real entities at a known 2:1 scale. The DXF is the document a
future reader should be sent to; the manifest already hints at it ("kept
because the panel cutout can be taken from it directly") without saying that
it also makes every dimension re-readable without a renderer.

Also extracted, and not in the corpus anywhere — the drawing names **two
mounting configurations**, which matters for A10-09:

```
[dxf]  "Flansch vorne, Chassis an Frontplatten-Rueckseite
        flange at frontside, chassis at frontpanel-rearside"      → 34,55
       "Flansch u. Chassis an Frontplatten-Rueckseite
        flange and chassis fixed at frontpanel-rearside"          → 36,3
```

### A10-07 · `J-UMBILICAL` · CONFIRMED with one ambiguity

ADR 0009's rotation table re-derives exactly `[calc]`, on a 57 × 38 mm face:

| | as drawn | rotated 90° |
|---|---|---|
| Material above/below flange | `(38−31)/2 = 3.50` ✓ | `(38−26)/2 = 6.00` ✓ |
| Screw-hole edge to face edge | `19 − (12+1.6) = 5.40` ✓ | `19 − (9.5+1.6) = 7.90` ✓ |
| Material above/below bore | `(38−24)/2 = 7.00` ✓ | 7.00 ✓ rotation-invariant |
| Clear width beside flange | `57−26 = 31` ✓ | `57−31 = 26` ✓ |

And on the panel: `(50.50−26)/2 = 12.25`, `(50.50−31)/2 = 9.75` ✓.

**The ambiguity.** The parenthetical says a review's "the orientation is
therefore forced" was a 6HP statement, "at 30.18 mm the rotated case left a
1.49 mm web". 1.49 mm is the **screw-hole** web: `30.18/2 − (12 + 1.6) =
1.49` `[calc]`. It is not the flange web, which at 6HP rotated is
`(30.18 − 31)/2 = −0.41 mm` — the flange is *wider than the panel*. A reader
checking "1.49 mm web" against the flange, as the surrounding sentences do,
gets a contradiction. Say which feature.

### A10-08 · `ENDCAP-TAIL` / `J-UMBILICAL` · HIGH — ADR 0009 settles the rotation and then sizes the USB-C slot on the orientation it rejected

`docs/decisions/0009-enclosure-construction.md` bullet: **"Rotate it 90°.
Settled off the drawing."** Its own table gives the rotated clear width beside
the flange as **26 mm**.

The next bullet, ~15 lines later:

> **It shares the face with the USB-C slot**, leaving roughly **31 mm** beside
> the flange for it. That fits, but it is not the place to discover a conflict.

31 mm is the **as-drawn** figure, from the row of the table that the same
bullet-pair just rejected. The USB-C clearance is asserted on the orientation
that is not being built. 26 mm is still enough for a USB-C slot, so the
conclusion survives — but the number does not, and the sentence that carries
it is the one telling the reader not to discover a conflict late.

A second-order point on the same pair: 31 and 26 are the **total** width not
covered by the flange. They are one contiguous strip only if the connector is
pushed to one side of the face. Centred — which "exits the tail end face,
axially" is usually read as — the strips are `(57−26)/2 = 15.5` or
`(57−31)/2 = 13.0 mm` each `[calc]`. Still enough; still not what the bullet
says.

### A10-09 · `ENDCAP-TAIL` / `MECH-BACKPLATE` · HIGH — the tail is the tight one, and the tight dimension is the one nobody has computed

This is the finding I would act on first.

**The limit is hard and triple-sourced.** Panel thickness **max 4 mm** for the
D-series: `NE8FDP-DATASHEET.pdf` p.2 mechanical table; `NE8FDV-DATASHEET.pdf`
states it twice; and the Product Guide p.13 tabulates 3 mm as the range base
with **4 mm as the D-series exception** — all three banked `[repo]
datasheets/MANIFEST.csv`. The corpus's own J-UMBILICAL row records all of it.

**The material is 6–8 mm.** `ENDCAP-TAIL` is `"TBD - oak, same stock as
BODY-OAK"` `[repo] hardware/bom.csv:130`, and BODY-OAK is 6 mm top / 8 mm
bottom `[repo] 0009:66-69`.

**The corpus's resolution does not resolve it.** ADR 0009: *"Mount the
connector to an internal backing plate — aluminium or ply, tied into the same
stack that carries the keys — and let the oak be the face the screws pass
through rather than the thing the screws hold."* That answers **pull-out**
(which was the stated worry — "oak is not what should be carrying it"). It
does not answer **clamped thickness**, which is what the 4 mm spec bounds. In
the flange-at-front configuration the flange still bears on the outer face of
≥6 mm of oak and the latch has to reach past it. Adding a backing plate behind
the oak makes the clamped stack *thicker*, not thinner.

**No document in the corpus states what thickness the connector clamps at the
tail.** The 4 mm limit is cited four times and always to conclude "it cannot
mount through 6 mm oak" — a conclusion everyone agrees with and nobody
follows to a design.

**Where the answer probably is, and why it needs checking rather than
assuming.** The banked drawing's second configuration — *flange and chassis
both behind the panel*, 36.3 mm `[dxf]` — is a rear-mount in which the panel
carries only the ⌀24 bore. The corpus has the 36.3 number (J-UMBILICAL row,
"36.3mm if flange and chassis both sit behind") and has never connected it to
the thickness question. **But note the two configurations differ by
`36.3 − 34.55 = 1.75 mm` `[calc]`, i.e. the connector sits further back, so
the mating plug has to reach further in — which is plausibly the very thing
the 4 mm limit bounds.** So rear-mounting may not buy anything. Three ways out,
in cost order, and one of them has to be chosen before the tail end cap is
cut:

1. **Rebate the oak locally to ≤4 mm** around the bore. A flat 2D relief in a
   laminated part, i.e. free — the tail cap becomes two laminated layers, the
   outer one with a larger clearance opening.
2. **Rear-mount per the drawing's second configuration**, after confirming the
   4 mm limit against it.
3. **Make the tail end cap 4 mm** and give up "same stock as BODY-OAK".

Every one of these changes a DXF. `ROADMAP.md:190` already books the 1:1 check
of this face at M4 and calls the tail "the tight one of the two" — correctly,
and for a reason it does not name.

### A10-10 · `MECH-BACKPLATE` · MEDIUM — the row contradicts the row above it in the same generated file

`hardware/bom.csv:125`:

> The D-series panel-thickness limit is **somewhere in 1-4mm depending on
> variant** and is **NOT stated on the drawing the repo holds**

`hardware/bom.csv:98` (`J-UMBILICAL`), same file, appended the same day:

> `'somewhere in 1-4mm depending on variant' is simply wrong for NE8FDP and
> NE8FDV, which are both a flat 4mm`

The refutation landed on the row being edited and not on the row that repeats
the claim — the project's named failure mode, inside one generated file. No
`forbidden` pattern covers it. Fragments:
`hardware/unplaced.csv:37` and `:10`.

### A10-11 · `ENDCAP-TAIL` · HIGH, new — the "7.0 mm of material above the bore" is the lid, and the lid lifts off

Nothing in the corpus checks the bore against the **stack**, only against the
envelope. Doing it:

```
[calc]  ⌀24.0 bore centred on a 38 mm face
        → bore top edge sits 38/2 − 12.0 = 7.00 mm below the outer top face

[repo]  0009 stack, top down: plate 1.20 + oak top 6 = 7.20 mm  = THE LID
        (the lid is plate + oak top; the U is oak bottom + acrylic sides)

→ the bore's upper edge is 0.20 mm below the lid/U parting line.
```

Consequences, none of them recorded:

- **The 7.0 mm above the bore is not backing material.** It is the edge of the
  part that comes off on six fasteners. Whatever carries the connector's
  upward load has 0.2 mm of engagement with the lid, or none.
- **Rotation does not help** — the bore margin is rotation-invariant, as ADR
  0009 correctly says.
- **The tail end cap probably has to be removed before the lid can lift**, or
  split at the parting line. ADR 0009 makes end caps "fasteners into the
  stack", so this is recoverable, but it is an assembly-order fact that
  belongs in the CAD, not a discovery at M7.

And the cavity, which the same section never checks against the connector:

```
[calc]  cavity = 38 − 1.20 (plate) − 6 (oak top) − 8 (oak bottom) − 2 (thumb plate)
               = 20.8 mm     — ADR 0009 says "around 20 mm" ✓
[dxf]   largest behind-panel body dimension on ST-NE8FDP = 19.8 mm
→ ~1 mm, and only if the connector is not recessed and the thumb plate is
  absent at the tail.
```

Not a failure. But "roughly 26 × 31 mm on a face that measures 57 × 38 mm" is
the only envelope check ADR 0009 performs on this connector, and the part
protrudes 34.55 mm into a 20.8 mm cavity.

### A10-12 · `J-UMBILICAL-CABLE` · BUILD NOTE

The cable shell exits the tail axially. NE8MC is **discontinued**; NE8MX is the
successor and is **⌀20.1 × 66.4 mm** with a **4.5 mm lower bound** on cable OD
that NE8MC did not have `[repo] datasheets/MANIFEST.csv, from NE8MX.pdf which
does have a text layer`. A thin or booted patch lead that strain-relieved in an
NE8MC may not in an NE8MX. The BOM row records this; nothing in ADR 0009's
tail geometry does, and a ⌀20.1 shell plus its boot swinging at the tail is a
clearance the 1:1 paper check should include.

---

## 3. Plate thickness and switch retention

### A10-13 · `PLATE-TOP` / `PLATE-THUMB` · PROVENANCE — 1.20 mm could not be re-verified, and should be made re-readable

`plate-thickness = 1.20 mm` is sourced to sheet 6's elevation and sheet 3 §8 of
`GATERON-KS-33-VENDOR-SPEC-DRAWING.pdf`, **read by rendering at 150 dpi**
`[render, not re-verified]`.

I could not re-read it. There is no rasteriser in this sandbox. I decompressed
all streams (5.1 MB inflated) and the drawing's text is CID-outlined: zero hits
for `1.20`, `1,20`, `14,00`, `5.25`, `2.50`, `0.05` in the extracted show
operators.

This is not a doubt about the number — the corroboration is good (two
independent sheets, and the STEP stack it predicts checks out exactly, A10-14).
It is an observation that **the single most consequential mechanical figure in
the project is currently readable only by someone with a working renderer**,
and that the repository's own rule is that a banked document beats a review.

**Cheap fix, and it is the same one `MANIFEST.csv` already half-does by
recording renders in prose:** bank a PNG of sheets 3 and 6 beside the PDF, with
a manifest row. `pcb-pipeline.md:254-258` already lists the no-text-layer
documents; it stops short of saying what to do about it.

### A10-14 · `SW1-n` · CONFIRMED by extraction — the STEP Z stack is exactly as recorded

I parsed the 1289 `CARTESIAN_POINT`s of `GATERON-KS-33-3D.step` `[step]`:

| | extracted | `ks33-geometry.md` |
|---|---|---|
| Overall | 15.000 × 15.000 × 12.750 | 15.0 × 15.0 × 12.75 ✓ |
| Z extent | −5.700 … +7.050 | pole tip −5.70, stem top +7.05 ✓ |
| Datum plane | z = 0.00, 453 points | collar underside ✓ |
| Collar top | +0.50 | +0.50 ✓ |
| Housing bottom | −2.50 | −2.50 ✓ |
| Pin tips | −5.10 | −5.10 ✓ |
| `PRODUCT` | `Gateron_KS_33_v3` | ✓ |

The third-party solid and the vendor drawing agreeing to this degree is real
evidence, and it is the strongest reason to trust A10-13's unreadable number.

### A10-15 · `PLATE-TOP` · HIGH — at 1.20 mm the plate-to-PCB conclusion inverts, and nothing followed it

The standoff argument is stated in two live places and **both compute only
1.5 mm and 2 mm**:

- `docs/reference/ks33-geometry.md:91` — *"A 2 mm plate leaves 1.2–1.6 mm; a
  1.5 mm plate leaves 1.7–2.1 mm."* This is in the **live** Z-stack section,
  not in the superseded blockquote. It is the owner document of
  `plate-thickness` and it does not carry its own settled value's consequence.
- `hardware/cluster/cluster-boards.md:159` — *"Against a 1.5–2 mm plate that
  leaves 1.2–2.1 mm — the board is effectively **hard against the plate
  underside**."*

At 1.20 mm `[calc]`, from the same premise (PCB top within 3.2–3.6 mm of the
collar seat):

```
gap between plate underside and PCB top = 3.2 − 1.20 = 2.00 mm
                                       to 3.6 − 1.20 = 2.40 mm
```

**2.0–2.4 mm is not "hard against".** It clears an 0805 (0.5 mm) several times
over. So the rule cluster-boards.md derives from it —

> **"Which collides with the bullet above it."** … now means *there is no
> plate-facing side*: **put every passive on the far face.**

— is no longer supported by its own premise. That is a live layout constraint
on a board that has not been laid out yet, and it is a constraint the settled
figure removes.

Same page, `:171`: *"the through-cutout section is only 2.50 mm deep, of which
a **2 mm plate consumes 80 %**."* At 1.20 mm it is `1.20/2.50 = 48 %` `[calc]`
— which ADR 0002 already states, and cluster-boards.md does not.

The checker cannot see any of this: 1.5 and 2 are legitimate numbers all over
the corpus, and `plate-thickness`'s `false_positive_note` says so explicitly.
This is the `mod-channels.md` shape of defect — an argument that outlived its
premise.

### A10-16 · `PLATE-TOP` · HIGH — `cluster-boards.md` says the thickness is still open

`hardware/cluster/cluster-boards.md:167`:

> **Plate thickness is still open and blocks M4/M5** `[repo] key-layout.yaml,
> 0002, bom.csv`.

It is closed. `config/figures.yaml` `plate-thickness` is `status: settled`;
ADR 0002's `## Open` opens with `~~**Plate thickness.**~~ **CLOSED
2026-09-21 at 1.20 mm**`; `ROADMAP.md:228` says settled. What still blocks
M4/M5 is **stiffening**, which is a different question with a different answer
space.

This matters because `cluster-boards.md` is the page a board designer opens,
and it currently tells them the governing dimension is unknown when the answer
is banked, and tells them to design around 1.5–2 mm when both are out of spec.

### A10-17 · `PLATE-TOP` · MEDIUM — ADR 0009's own mass table still says 2 mm

`docs/decisions/0009-enclosure-construction.md:181`: `| Aluminium top plate,
2 mm | 157 |` — 113 lines below the same ADR's stack diagram at `:68`, which
reads `aluminium top plate 1.20 mm <- SETTLED by Gateron's drawing`.

`plate-thickness`'s `forbidden` carries `"ADR 0009 specifies a ~2 mm aluminium
top plate"`, which is the prose spelling from ADR 0002's *description* of ADR
0009 — not a spelling ADR 0009 itself ever used. The table cell is missed.
Verified: the pattern does not occur in the file; `Aluminium top plate, 2 mm`
does `[calc, run against the checker's matcher]`.

Consequence `[calc]`: `457 × 57 × 1.20 = 31.3 cm³ × 2.70 g/cm³ ≈ 84 g` against
the tabulated 157 g, so the `~825 g` total is **60–70 g high**. The EWI-territory
conclusion survives; the number does not.

### A10-18 · `ADR 0009` · MEDIUM — two `### Mass` sections, disagreeing

`0009:168` gives `2.25 in → ~778 g (1.72 lb)`. `0009:175`, headed `### Mass`
again and introduced "Rough estimate at this envelope", totals `~825 (1.8 lb)`
— which is the *first* table's **2.50 in** row. Two sections, one heading, one
envelope, two answers. One is the leftover of the width decision; the reader
cannot tell which.

### A10-19 · `PLATE-TOP` · OPEN, and correctly open — but unquantified

The corpus's conclusion is right and well argued: at 1.20 mm **stiffening is
compulsory, not optional**, lamination is the floor rather than the cheap
alternative, and ADR 0002's requirement 2 ("something backs the switch") is
load-bearing. ADR 0002's defence of RTV — compliant in shear for the oak's
0.6–0.9 mm of cross-grain movement, stiff in confined normal compression under
a key press — is a genuinely good argument and survives the thickness change.

What is missing is any number at all. No span between supports, no deflection
target, no fastener pitch relative to the key line. The one relevant geometric
fact in the corpus cuts the wrong way: the six fasteners are at ~80 mm pitch
and deliberately **"clear of the key runs"** `[repo] 0009`, so they do not back
the keys — the RTV-to-oak layer does, alone, over the whole key line.

ADR 0002 already asks for the right test: *"wants confirming by hand at M1 with
a real switch in a real offcut rather than by argument."* **M1 precedes M3 and
M4**, so this is orderable now and costs an offcut. It is the cheapest open
item in my slice.

---

## 4. The key cutout and the achieved fit

### A10-20 · `PLATE-TOP` · CONFIRMED — the nominal/achieved distinction is made, and made well

ADR 0002: *"The achieved fit, which is a process question rather than a
geometry one. The drawing gives the nominal cutout; it cannot tell you what
*your* cutter produces in *your* material."* `ROADMAP.md:71` carries the same
split. Credit where due — this is the distinction most projects collapse, and
the accompanying argument that a caliper on a moulded housing gives *that
sample's* dimension including draft and flash, not design intent, is correct.

### A10-21 · `PLATE-TOP` · MEDIUM — the tightened cutout lives only in blockquotes, and the bare nominal is still sourced to the superseded measurement

The vendor value is **14.00 +0.05/−0.02 square**, from sheet 3 §8 `[render,
not re-verified]`. It appears in: a blockquote in `ks33-geometry.md`, a BOM
notes field, and `figures.yaml`'s `plate-thickness` note. That is it.

Still live as a bare `14.0 × 14.0`, with three of the five citing the
**superseded** third-party STL measurement as the source:

| | |
|---|---|
| `docs/reference/ks33-geometry.md:12` | `## Plate cutout: 14.0 × 14.0 mm` — the H2 heading of the owning reference |
| `docs/decisions/0002-...md` | *"Measured out of a working KS-33 build's published top-case meshes"* |
| `docs/decisions/0002-...md` `## Open` | *"the cutout is 14.0 mm"* |
| `ROADMAP.md:71` | *"**Cutout is 14.0 × 14.0 mm**, measured from a working KS-33 build"* |
| `hardware/cluster/cluster-boards.md:51, :117` | `14.0 mm cutouts`, `14.0 × 14.0 mm cutout … measured across 47 cutouts` |

`ROADMAP.md:71` is the sharpest: it sources the cutout to the STL build and, 49
lines later at `:120`, sources the bounce figure to
`GATERON-KS-33-VENDOR-SPEC-DRAWING.pdf`. Same row-block, same milestone, two
generations of source.

**The cutout is not a tracked figure.** Given that it is called "the precision
feature of the entire build", that it now has a vendor tolerance, and that it
is restated in six places, it is a strong candidate for `figures.yaml` — and
`breath-zero-ref`'s own escape note is the argument: *"An untracked quantity
derived from a tracked one has no protection at all."*

### A10-22 · `PLATE-TOP` · MEDIUM — the test-coupon ladder is coarser than the tolerance it is testing

`ROADMAP.md:71` and ADR 0002: *"Test coupon cut at **±0.1 mm** around 14.0 to
find the achieved fit"*, and ADR 0002 *"this is a press fit at ±0.1 mm"*.

The vendor band is **0.07 mm wide** (`+0.05/−0.02`) `[render, not
re-verified]`. A ±0.1 mm ladder's first step either side lands **outside the
drawing's band on both sides** `[calc]`. The ladder was sized when the only
reference was "±0.1 is what a press fit is"; it now has a specification to be
centred on, and it should be re-centred on 14.00 `+0.05/−0.02` with finer
steps.

And the number that actually decides whether a ladder is needed at all —
**the plate vendor's achievable tolerance on a laser or waterjet cut in
1.20 mm aluminium** — appears nowhere in the corpus. ADR 0009 names
SendCutSend, Ponoko and OSH Cut; none of their tolerance figures is recorded.
If the vendor's tolerance is wider than 0.07 mm, the coupon is not a ladder,
it is a sort.

### A10-23 · `SW1-n` · LOW CONFIDENCE — one STEP-derived number may be 0.2 mm off

`ks33-geometry.md:82` gives the pin blade's narrow through-hole section as
`−3.2 → −5.10 mm`, and the PCB-top window `~3.2–3.6 mm` is derived from the
3.2. My `[step]` z-plane histogram shows populated planes at **−3.00** (84
points), −2.50, −2.47, −2.41, −5.10 and −5.70, and **no plane at −3.2**.

If −3.00 is the transition, the narrow blade is 2.10 mm not 1.9 mm and the
PCB-top window is 3.00–3.5 mm. **I do not claim this** — my clustering cannot
separate the five bodies, and the transition may be on a face whose defining
points lie elsewhere. It is a one-line re-measure with the same tool that
produced the table, and it feeds A10-15's arithmetic.

---

## 5. Does the loom physically fit?

### A10-24 · `J-CHAIN` · HIGH — the ROADMAP row that asks this question states half the conductor count, and escapes `forbidden` on letter case alone

`ROADMAP.md:203`, in the open-questions table:

> | **Does the chained key loom fit the side channel?** | M4 | **Six
> conductors per hop** rather than the 32–44 the tail-mounted alternative
> needed — much easier, but still check it against the real cavity section
> alongside the LED strips and the breath tube, **before the plate DXF is
> cut** (ADR 0001, ADR 0009) |

`chain-conductors` is **12** — `settled`, owner ADR 0001, derived as "4 signals
+ 5 alternating grounds + 3V3 + 2 spare, on a 2×6 IDC" `[repo]
config/figures.yaml`.

Its `forbidden` list already anticipates this exact sentence and misses it
`[calc, run against the file]`:

| pattern | present in `ROADMAP.md`? |
|---|---|
| `six conductors per hop` | no |
| `SIX conductors per hop` | no |
| `6 conductors per hop` | no |
| `Six conductors leave` | no |
| **`Six conductors per hop`** | **yes — and it is not in the list** |

Three spellings were written, and the one that is live — **title case, start of
a table cell** — was not. The matcher is case-sensitive `[repo]
tools/check-staleness.py:170`. The checker reports `PASS`.

That this lands on **the row that gates cutting the plate DXF**, in the
document a reader consults for sequencing, is the part that matters. The row
understates the physical bulk of the thing it is asking about by a factor of
two.

### A10-25 · `J-CHAIN` · HIGH — `carrier.md` carries a third count, twice, beside its own correct one

`hardware/carrier/carrier.md`:

- `:350` — *"the channels now carry **one 8–11 way loom** instead of four
  ribbons totalling 40–56 mm of width"*
- `:364` — *"carrier, two LED strips, **one 8–11 way key loom**, the display
  loom, the breath tube and the U-bolt in 49 mm of internal width"*
- `:371`, boxed, same page — *"**Two items were decided rather than left
  open.** `J-CHAIN` is **2×6** with a ground between every signal (§3)."*

And `hardware/interfaces/key-chain-loom/key-chain-loom.md:204` — *"`J-CHAIN` is
a 2×6 IDC boxed header on a **12-way ribbon**"*.

So one tracked figure has three values across two pages, and one page holds two
of them fourteen lines apart. No `forbidden` pattern matches `8–11 way`. The
`key-scan-current` escape note already predicted this shape: *"A split does not
create a duplicate, but it removes the thing that made the duplicate
survivable."*

### A10-26 · `J-CHAIN` · MEDIUM — two superseded premises on the loom page

`hardware/interfaces/key-chain-loom/key-chain-loom.md`:

- `:139` — *"Whether this connector is 6-way or 10-way is a decision this page
  cannot take alone — see *Still open*."* It was taken: 2×6, 12-way, on this
  page's own `:204` and in `carrier.md`'s boxed note. **Neither candidate
  offered is the answer.**
- `:143` — *"The 3V3 conductor leaves this board, runs 265 mm through a
  **bonded body** next to 12 V LED power."* See A10-30.

### A10-27 · side channels · HIGH — the corpus already contains a negative answer, and the ROADMAP row does not carry it

`hardware/carrier/carrier.md:341-346`, live, `[calc]` in the page's own marking:

> 57 mm external less 2 × 4 mm acrylic `[repo] 0009` = **49 mm internal**.
> `PCB-CARRIER` at 45 mm leaves **2 mm per side** for two channels that ADR
> 0009 and ADR 0014 jointly require to carry two WS2815 strips (~10 mm wide
> each `[from memory]`), the key loom and the 400 mm tube. **A 45 mm-wide
> carrier and open side channels are still mutually exclusive.**

I re-derive it: `57 − 8 = 49`; `(49 − 45)/2 = 2.0 mm` `[calc]`. Against that,
in one channel:

| Occupant | Width | Source |
|---|---|---|
| WS2815 strip | ~10 mm | `[from memory]`, carrier.md — **nowhere else in the corpus** |
| `J-CHAIN` ribbon, 12-way at 1.27 mm | `12 × 1.27 = 15.24 mm` | `[calc]` |
| `J-CHAIN` boxed header body | ~20 mm long | `[repo] 3M-303 catalogue, banked` |
| Display loom, 9 conductors, 360 mm | — | `[repo] display-and-service-uart.md:53` |
| Breath tube, 400 mm | **no dimension anywhere** | see A10-28 |

So the answer to my question 5, as the corpus stands, is **no — at the tail**,
and the corpus says so on one page. But `ROADMAP.md:203` frames it as an
unstarted M4 check, does not mention the carrier width, and (A10-24) halves the
loom. A reader working from the ROADMAP does not learn that the answer is
already known to be negative in the one zone where everything converges — the
tail, which also carries the etherCON (A10-09), the USB-C slot, the matrix
window and its carrier cutout, the sensor and the tube's dead-volume trap.

Note the pinch is **local**: the carrier is ~100 × 45 mm in a 457 mm body, so
the channels are only squeezed to 2 mm over the carrier's own length. That
makes it a board-outline problem rather than a body problem, which is how
`carrier.md` files it ("the board outline still depends on the M4 plan
section"). It does not make it smaller — the tail is where every occupant of
the channel has to arrive.

### A10-28 · side channels · MEDIUM — the M4 fit check cannot currently be performed

Two of the three things the ROADMAP row names have **no dimension anywhere in
the design corpus**:

- **The LED strip width.** ADR 0014 gives the part, the run length (two × 420
  mm), the current and the chaining topology; it never gives a physical width
  or a mounting depth. The only figure in the corpus is `~10 mm wide each
  [from memory]` in `carrier.md:344` — explicitly marked as unsourced, and the
  number the whole channel budget turns on. ADR 0009 adds *"Diffusion gap
  between strip and acrylic is a prototype question and it constrains the
  channel depth"* — an acknowledged unknown on top of an unsourced one.
- **The breath tube OD.** `TUBE` gives `~400mm`, a 1.17 ms propagation and a
  ≤1 mL trap `[repo] hardware/bom.csv:107`. No outside diameter, no bend
  radius. `MECH-MOUTH` defers the bore to E2. A ~400 mm tube running the length
  of a channel whose clearance is being argued to the millimetre has no
  diameter.

A WS2815 strip and a silicone tube are the two easiest dimensions to obtain in
this whole slice. Until they exist the M4 check has nothing to check against,
and "still check it against the real cavity section" is not actionable.

### A10-29 · side channels · FOR THE RECORD — what is actually in a channel

`[repo]`, assembled from the pages that each own a piece: **12 conductors per
hop** on a 2×6 IDC (`chain-conductors`), **8 `J-CHAIN` connectors** in the
system (`chain-connectors`), a **9-conductor 360 mm display loom**
(`display-and-service-uart.md:53`), **one WS2815 strip per side** plus its 12 V
power (ADR 0014), and the **400 mm breath tube** in one of the two (ADR 0009).
Plus the two spare conductors ADR 0009 mandates in every internal loom, which
are already inside the 12.

ADR 0009's resolution of the ADR 0009 / ADR 0014 channel contradiction — that
it is safe because the sensor moved to the tail, so everything in the channel
is digital — is sound and survives. It is an EMC argument, not a volume one,
and the volume argument has not been made.

---

## 6. Ordering constraints

### A10-30 · state of each rule

| # | Rule | Where | State |
|---|---|---|---|
| 1 | **No aluminium cut before M3** | `ROADMAP.md:73`; ADR 0009 *"No aluminium is cut before M3"* | **Holds.** Stated twice, both visible. |
| 2 | **Nothing expensive gets cut before M3** | `ROADMAP.md:86` | **Holds.** |
| 3 | **M5 must not precede E13** | `ROADMAP.md:92`, M5 row `:75` | **Holds** — but see A10-31. |
| 4 | **The body does not close until the carrier is revision-final and burned in** | `ROADMAP.md:96` | **Holds as a rule; its supporting corpus does not.** See below. |
| 5 | **M8 exists because E11 tests a topology that does not survive** | `ROADMAP.md:105` | **Holds.** |
| 6 | **M1 no longer gates M4** | `ROADMAP.md:80` | **Holds**, and is the right call — CAD can start against the banked drawing. |
| 7 | **Check the loom before the plate DXF is cut** | `ROADMAP.md:203` | **Rule holds; the row is wrong.** A10-24, A10-27. |
| 8 | **Do not cut the panel hole until the toggle part number is chosen** | `hardware/bom.csv:54` notes | **Satisfied** — `NKK M2011SD4G01` selected. The rule now lives only in a BOM notes field. |
| 9 | **PANEL and PLATE-TOP are one laser order** | three places, below | **VIOLATES #3.** A10-31. |

**On #4.** The rule stands on its own. What has not followed it is the rest of
the corpus: ADR 0009 now says the body comes apart on six fasteners onto an RTV
gasket, and **thirteen live statements in nine files still argue from a body
that cannot be reopened** `[repo]`:

```
hardware/interfaces/breath-sense-link/breath-sense-link.md:14, :79, :169
hardware/interfaces/key-chain-loom/key-chain-loom.md:143
hardware/module/breath-receive-stage/breath-receive-stage.md:28
hardware/module/breath-receive-stage/sim/README.md:22
hardware/carrier/carrier.md:286, :339, :384
docs/decisions/0004-cv-interface-module.md:951
docs/decisions/0005-power-architecture.md:238
docs/decisions/0007-imu-selection.md:199
docs/decisions/0013-two-mcu-split.md:294
docs/decisions/0014-lighting.md:83, :476
docs/decisions/0003-breath-sensing-path.md:186, :248
```

Some of these are load-bearing arguments, not decoration — `carrier.md:384`
*"Whether the sensor is reachable after bonding, which decides whether
`SKT-BREATH` earns its place"* turns on it, and `0007:199` *"In a body that
cannot be opened, two pins is a cheap price"* is the justification for a part
choice. ADR 0009 and the BOM rows that were touched (`MECH-UBOLT`,
`U-TVS-MODULE`) followed the change; nothing else did. Outside my slice to
adjudicate each one, in it to report that the serviceability change is
**half-landed** and that a mechanical premise is doing work in a dozen
electrical arguments.

### A10-31 · `PANEL` / `PLATE-TOP` / `PLATE-THUMB` · HIGH, new — the panel and the key plate are one order, scheduled in two phases separated by an ordering rule

Three documents say they are one order:

- `hardware/bom.csv:62` (`PANEL`) — *"Laser or waterjet from DXF — **SAME
  vendor and order as the key plate**"*
- `hardware/bom.csv:37` (`PLATE-THUMB`) — *"same vendor and same order as
  PLATE-TOP"*
- `docs/reference/pcb-pipeline.md:242` — *"laser or waterjet from DXF, **same
  vendor and order as the key plate**"*

The ROADMAP schedules them apart:

- `PANEL` is cut at **E12** — *"10HP panel cut, module assembled and racked"*
  `[repo] ROADMAP.md:53` — which is **Phase 3** `[repo] :160`.
- `PLATE-TOP` is **M5**, *"Not before E13 — see the ordering rules below"*
  `[repo] :75`, moved to **Phase 4** explicitly: *"**M5 moves to Phase 4** —
  the plate is cut after the carrier layout exists"* `[repo] :160`.

**One order cannot be placed in two phases with a hard ordering rule between
them.** Either the panel waits for E13 — which is free, nothing about the panel
depends on the carrier — or M5 precedes E13, which is the rule a design review
already caught being violated once and which exists because the plate is *"the
most expensive irreversible part"*.

The resolution is almost certainly "the panel waits, and they go together",
since the panel is not on E12's critical path in any other way. But it is
currently unstated, and the two instructions are in different documents.

### A10-32 · visibility — what the restructure made harder to see

The task asked specifically about this, and A10-31 is the example.

- **`hardware/module/panel/` is the only directory in the repo whose subject is
  the panel, and it has no `bom.csv` and no `notes.md`** — only `panel.md` and
  `circuit.yaml` `[repo]`. CLAUDE.md's stated convention is *"the page, its
  `bom.csv` fragment, its `circuit.yaml`, and `notes.md`"*.
- **`tools/merge-bom.py` ORDER names `hardware/module/panel/bom.csv`, which
  does not exist.** Not a tool defect — `load()` does
  `if not os.path.exists(path): continue  # not every circuit owns parts`
  `[repo] tools/merge-bom.py:91-93`, and `--check` reports `138 rows from 24
  fragments | 0 problems`. But ORDER is asserting a fragment that is not there,
  and the asymmetry is worth noting: a fragment on disk missing from ORDER is
  an error; an ORDER entry missing from disk is silent.
- **The `PANEL` row is filed under the LED.** It lives in
  `hardware/module/panel-led/bom.csv` — the 10HP aluminium panel itself, with
  the stale budget of A10-02 and the ordering rule of A10-31 in its notes
  field. CLAUDE.md: *"A row lives with the circuit **whose page derives its
  value**."* PANEL's value is derived by ADR 0004 and by
  `hardware/module/panel/panel.md`. `panel-led.md` cites it in its interfaces
  table but derives nothing about it.
- **The three parts of one laser order are in three board trees.** `PANEL` in
  `module/panel-led/`, `PLATE-TOP` in `cluster/`, `PLATE-THUMB` in
  `cluster/key-marker-and-bits/`. None is a mechanical directory, and
  `mechanical/` is three empty `.gitkeep`s (`cad/`, `drawings/`, `export/`) —
  consistent with M4 being unstarted, but it means there is no place where the
  mechanical order exists as one thing.
- **Net effect:** the ordering rule in A10-31 is visible only to a reader who
  opens two BOM fragments in two board trees, a reference page, and the
  ROADMAP phase table. That is the failure mode `key-scan-current`'s escape
  note names — *"a split does not create a duplicate, but it removes the thing
  that made the duplicate survivable"* — applied to a constraint rather than a
  value.

---

## What I could not check

- **Every vector-drawing dimension.** `plate-thickness` (1.20 ±0.05), the
  cutout tolerance (+0.05/−0.02), the NKK toggle body and bushing, the
  Thonkiconn envelope, and the NE8FDP *panel-thickness* limit as printed on the
  datasheet page. No rasteriser exists in this sandbox. The Neutrik drawing
  dimensions I *did* re-verify came from the DXF's text layer, not from the
  PDF. See A10-13.
- **Whether the etherCON's 4 mm panel-thickness limit is relaxed in the
  rear-mount configuration.** That is a question for Neutrik or a bench part,
  not a document in this repo. A10-09 states it as a question, deliberately.
- **Each of the thirteen "bonded body" statements in A10-30**, individually.
  I confirmed they are live text in corpus files; I did not adjudicate which
  arguments actually change.
- **A10-23's −3.00 vs −3.2.** Flagged low-confidence on purpose.

## Where I disagree with nothing

Five things in this slice are right, checked, and should not be reopened:
`panel-height-budget`'s derivation (A10-01), the etherCON geometry (A10-06,
A10-07), the STEP Z stack (A10-14), the nominal/achieved split (A10-20), and
the RTV shear-vs-compression argument for the plate joint (A10-19). The
`panel-toggle-hole` work — a row that existed for three waves to get one number,
resolved by trying a hostname nobody had tried — is the model the rest of this
report is measured against.
