# D14 — the reversed plate-to-PCB conclusion, and everything downstream

**Slice:** a mechanical conclusion that reversed on 2026-09-21/22, and its
propagation. **Method:** cold — nothing under `docs/review/**` was read except
this wave's `README.md`. Git history, the banked PDF, the banked STEP solid and
the corpus were read directly.

Provenance on every claim: `[repo] path:line`, `[calc]`, `[datasheet]`,
`[step]` (measured out of the banked solid, with the command), `[test]`,
`[from memory]`.

---

## Verdict in one paragraph

**The reversal is right in direction and wrong in magnitude, and the corpus
already contains the right number in a second place.** There is a standoff —
the old *"the board is effectively hard against the plate underside"* was
wrong. But the new figure, **2.0–2.4 mm, is not reachable under any assumption
the drawing supports**, and its upper end is arithmetically impossible: it puts
the switch pin tip 0.10 mm *inside* a 1.6 mm PCB, where it cannot be soldered.
The gap that the two vendor dimensions actually give is **1.30 mm**
(2.50 − 1.20), and ADR 0002 states the same subtraction in words —
*"at 1.20 mm the plate consumes only 48 % of the 2.50 mm through-section"*
`[repo] docs/decisions/0002-key-switches-and-mounting.md:181` — in the same fix
batch that wrote 2.0–2.4 mm on the page next door. Two documents, two
incompatible standoffs, from the same two numbers. The height rule derived from
the larger figure permits parts that will touch a grounded plate.

Separately: **the sibling slice's claim about `ROADMAP.md:71` is confirmed, and
there is a fifth spelling at `ROADMAP.md:84`.**

---

## 1. Re-deriving the gap

### 1.1 The inputs, read off the two banked artefacts

`[datasheet]` `datasheets/mechanical/GATERON-KS-33-VENDOR-SPEC-DRAWING.pdf`
sheet 6, elevation view (rendered at 600 dpi, clip `Rect(20,260,220,420)`),
dimension chain from the collar underside downward:

| Dimension | Value | What it spans |
|---|---|---|
| `2.50 ±0.05` | 2.50 mm | collar underside → housing bottom |
| `2.60` | 2.60 mm | housing bottom → pin tips (**5.10 total**) |
| `5.75 ±0.05` | 5.75 mm | collar underside → centre-pole tip |
| `1.20 ±0.05` | 1.20 mm | collar underside → bottom of the latch-arm band |
| `⌀1.00`, `0.45` | — | pin blade, narrow section |

`[datasheet]` sheet 3 §8 *"Mounting Options — the suggestion dimension of
mounting"* (rendered at 400 dpi, clip `Rect(250,570,595,800)`): plate cutout
**14.00 +0.05/−0.02** square; recommended plate thickness **1.20 +0.01/−0.05**
in the edge view; and a **PCB pattern** of ⌀5.25 centre, two **⌀3.00** holes at
2.60/4.40 × 5.75/6.30, and a 5.00 × 1.80 slot.

`[step]` `datasheets/mechanical/GATERON-KS-33-3D.step`, parsed by resolving each
body's `AXIS2_PLACEMENT_3D` and transforming its `CARTESIAN_POINT`s (no
OpenCASCADE in this container; `OCC`, `cadquery`, `OCP` all absent — plain
STEP-entity traversal, reproducible from the snippet in §1.5):

- Bodies: `Base` (z −5.70…+0.50, identity), `Stem` (0…+7.05, identity),
  `Cap` (local −3.00…+2.85, placed at z +0.54 → global −2.46…+3.39),
  `PinA` at `(−4.4,−4.7,−2.5)` with `DIRECTION(0,0,−1)`, `PinB` at
  `(2.6,−5.6,−2.5)` likewise. Overall extent **12.75 mm**, datum z = 0 at the
  collar underside — both as `ks33-geometry.md` states them.
- **The pin blade cross-section, global z (this is the load-bearing one):**

  | z | blade width × thickness |
  |---|---|
  | −1.50 → −2.50 | **2.00 × 0.45** (root, inside the housing) |
  | −2.50 → −3.00 | taper 2.00 → 1.00 |
  | −3.00 → −4.60 | **1.00 × 0.45** (the straight narrow blade) |
  | −4.60 → −5.10 | taper 1.00 → 0.50 (tip lead-in) |

### 1.2 Finding D14-1 — the −3.2 mm blade transition does not exist

`[repo] docs/reference/ks33-geometry.md:92` states
`| Pin blades, narrow through-hole section | −3.2 → −5.10 mm |`, and line 99
*"only the last **1.9 mm** is the narrow blade"*.

`[step]` **The transition is at −3.00, not −3.2.** The set of distinct z values
anywhere in the solid is
`−5.7, −5.1, −3.0, −2.5, −2.469, −2.41, −2.207, −1.97, …` — **−3.2 is not a
coordinate in the file.** The narrow section is 2.10 mm long, not 1.90, of
which the last 0.50 mm is the tip chamfer, so the full-width 1.00 mm blade is
1.60 mm long.

This matters because 3.2 and 1.9 are the only inputs to the published window.

### 1.3 Finding D14-2 — where "3.2–3.6 mm" comes from, and why it cannot hold

`[repo] ks33-geometry.md:99-101`: *"The pins reach 5.10 mm below the seat and
only the last 1.9 mm is the narrow blade… So the PCB top has to sit within
roughly 3.2–3.6 mm of the seat for the blade to fill the hole and protrude
enough to solder."*

**Reconstruction (inference, not stated anywhere):** 3.2 = 5.10 − 1.90 (the
claimed blade length) and 3.6 = 5.10 − 1.50 (a 1.5 mm board with its tip
flush). If that is right, the two ends of the "window" are two different *board
thicknesses*, not a mounting-height range, and **neither end provides any
protrusion at all.**

`[calc]` The window fails its own stated test. With the 1.6 mm PCB the corpus
specifies (`PCB-CLUSTER`, package `small, 1.6mm` `[repo] hardware/bom.csv:59`),
pin protrusion below the board is `p = 5.10 − d − 1.6`:

| PCB top depth `d` | protrusion `p` | verdict |
|---|---|---|
| 3.20 mm | **+0.30 mm** | minimum solderable |
| 3.50 mm | **0.00 mm** | tip flush with the board underside |
| 3.60 mm | **−0.10 mm** | **the pin never emerges** |

So `d = 3.6` — the end that produces the 2.4 mm figure — is not a mounting
position at all. **The upper half of the published range is impossible**, and
the sentence "protrude enough to solder" is false across the whole range bar
its first 0.3 mm.

### 1.4 Finding D14-3 — the real standoff is 1.30 mm, and ADR 0002 says so

The whole 3.2–3.6 construct rests on an unstated premise: *only the narrow
blade may enter the PCB hole*, i.e. a ⌀1.2 mm drill (from a third-party
footprint, `[repo] ks33-geometry.md:179`). **Gateron's own recommended PCB
pattern uses ⌀3.00 mm holes** `[datasheet]` sheet 3 §8 and sheet 6 "PCB Layout",
corroborated by the manifest's own reading of the file
`[repo] datasheets/MANIFEST.csv:70` — *"PCB pattern dia 5.25 centre with dia
3.00 holes at 2.60/4.40 x 5.75/6.30"*. A ⌀3.00 hole takes the 2.00 mm blade
root, which only makes sense if the vendor expects the **PCB to sit against the
housing bottom** — standard plate-mount practice.

`[calc]` **Seated configuration** (PCB against the housing bottom at −2.50):

```
  plate-to-PCB gap  = 2.50 − 1.20                    = 1.30 mm  nominal
                      worst case 2.45 − 1.25         = 1.20 mm  (sheet 6 tols)
  pin protrusion    = 5.10 − 2.50 − 1.6              = 1.00 mm  (normal TH joint)
  pole protrusion   = 5.75 − 2.50 − 1.6              = 1.65 mm  below the board
```

`[calc]` **Stood-off configuration** (the corpus's premise, ⌀1.2 holes). The
2.00 → 1.00 taper runs over −2.50…−3.00, so width ≤ 1.2 mm at −2.90:

```
  d ≥ 2.90 (blade fits a ⌀1.2 hole);  d ≤ 5.10 − 1.6 − 0.3 = 3.20 (0.3 mm protrusion)
  gap = d − 1.20  =>  1.70 … 2.00 mm
```

**2.0 mm is the ceiling, not the floor, and it costs you ADR 0002 requirement
2.** In the stood-off case nothing is under the housing bottom: the switch is
held by the plate interference and the solder joints alone. ADR 0002 calls that
requirement *"most commonly forgotten, and the first thing to fail"*
`[repo] 0002:47-49`, and the PCB is the obvious thing that meets it. **So the
design wants the seated case, and the standoff is 1.30 mm.**

`[repo] 0002:181` already contains this: *"at 1.20 mm the plate consumes only
48 % of the 2.50 mm through-section"*. The unconsumed 52 % **is** the gap. Two
files in the same batch, 1.30 mm against 2.0–2.4 mm, and nothing reconciles
them.

### 1.5 Reproducing the STEP measurement

```python
import re, collections
txt  = open("datasheets/mechanical/GATERON-KS-33-3D.step", errors="ignore").read()
data = txt.split("DATA;", 1)[1]
ents = {int(m.group(1)): (m.group(2).strip("( "), m.group(3)) for m in
        re.finditer(r"#(\d+)\s*=\s*(\(?\s*[A-Z_0-9]+)\s*\((.*?)\);\s*(?=#|ENDSEC)", data, re.S)}
# PinA is reached from the SHAPE_DEFINITION_REPRESENTATION whose subtree holds PRODUCT('PinA');
# its placement is #27 = AXIS2_PLACEMENT_3D at (-4.4,-4.7,-2.5) with DIRECTION(0,0,-1),
# so global_z = -2.5 - local_z.  Group its CARTESIAN_POINTs by local z and print x/y extents.
```

Result, PinA, `global z -> width`: `−1.50 → 2.00`, `−2.50 → 2.00`,
`−3.00 → 1.00`, `−4.60 → 1.00`, `−5.10 → 0.50`; thickness 0.45 throughout.

### 1.6 Two smaller numbers that move with it

- `[repo] ks33-geometry.md:134-136` and `[repo] cluster-boards.md:164-166`:
  *"a ⌀5.25 mm clearance hole through the plate **and** the PCB"*. **The plate
  needs no such hole.** The plate occupies z 0…−1.20, where the switch's
  cross-section is the 14.00 mm body; the pole is inside that outline. Sheet 3
  §8's plate section shows the 14.00 cutout only — the ⌀5.25 and the pin holes
  are in the *PCB pattern* overlay `[datasheet]`. The 14.00 cutout is the
  clearance. This is a fossil of the old "board hard against the plate"
  reading, in which plate and PCB were one surface.
- `[repo] ks33-geometry.md:135-136`: pole tip *"at −5.70 mm"* and protrusion
  *"0.5–0.9 mm"*. The drawing says **5.75 ±0.05** and the page's own rule is
  that the drawing supersedes `[repo] ks33-geometry.md:9-12`. `[calc]` Seated,
  a 1.6 mm board gives **1.65 mm** of pole below the underside — 0.75 mm more
  than the largest figure stated, and the LED channel runs under these boards
  `[repo] cluster-boards.md:94`.
- `[repo] ks33-geometry.md:155`: latch arms *"14.69 mm at the bottom widening
  to 14.99 mm just under the collar"* → 0.49 mm interference per side. The
  drawing dimensions **14.70** across the latch arms `[datasheet]` sheet 6,
  i.e. **0.35 mm per side**, constant through the 1.20 mm band. The STEP
  overstates the interference by ~40 %. Kept in a section the page flags as
  pre-drawing, so this is a "supersede me" that was not taken.

---

## 2. Verifying 1.20 mm against the drawing

**VERIFIED. 1.20 mm is right, the extraction claim is right, and one tolerance
is wrong.**

`[test]` `pip install pymupdf` (already present, PyMuPDF 1.28.2 — the README's
route works; `pdftotext` absent and `pypdf` panics, as documented).

```
pages 6 | per-sheet chars 1266/2199/1356/3916/1495/821 | TOTAL 11053
'1.20' 0   '14.0' 0   '14.00' 0   'Bounce' 1   '5msec' 1
```

- **The dimension-callout claim is confirmed by test:** zero occurrences of
  `1.20`, `14.0` or `14.00` in the text layer of any sheet. The callouts are
  outlined vector.
- **The prose claim is confirmed:** sheet 6 yields, verbatim,
  `5.Bounce Time: 5msec Max.(at 16 in/sec. actuation speed).` and
  `9.Operation Life:60,000,000 Cycles(min)`, and sheet 6's Force-Travel diagram
  yields the labels `operating point` and `reset point` as text with no
  dimension beside them.
- **Rendered and read by hand** (600 dpi, sheet 6 elevation): `1.20±0.05`
  brackets the collar underside down to the bottom of the latch-arm band. A
  900 dpi crop of one latch shows the arm at full width for that 1.20 mm and
  then **tapering inward**, with no downward-facing ledge — which *confirms*
  the STEP-derived "interference press, not a snap, widest at the top"
  `[repo] ks33-geometry.md:150-163` rather than leaving it unrefuted. It also
  explains the figure: 1.20 mm is the height of the interference band, so a
  thicker plate protrudes past it into the taper and grips less.

**Finding D14-4 — the tolerance is quoted from the wrong sheet.** Sheet 6's
`1.20 ±0.05` dimensions the switch's plate-grip band. Sheet 3 §8's *recommended
plate thickness* is **`1.20 +0.01/−0.05`** `[datasheet]`, which the manifest
records correctly `[repo] datasheets/MANIFEST.csv:70` and three corpus
documents do not:

- `[repo] config/figures.yaml:678` — *"sheet 3 section 8 shows the same 1.20"*
  (true of the nominal, silent on +0.01);
- `[repo] config/figures.yaml:682`, `[repo] ks33-geometry.md:63-66`,
  `[repo] 0002:174-176`, `[repo] hardware/bom.csv:40` — all compute
  *"1.5 mm is 0.25 mm over the upper limit"*, which is the sheet-6 band. Against
  the recommended-plate band it is **0.29 mm over**. The conclusion is
  unaffected; the corpus disagrees with its own banked record on the number.

**Also minor:** `figures.yaml:678` says the file yields *"9,680 characters"*,
`repo-maintenance.md:128` says *"11 kB"*, and PyMuPDF measures **11,053**.
Three numbers for one measurement, in one batch.

---

## 3. Is the new height rule right? No.

`[repo] ks33-geometry.md:123-132` and `[repo] cluster-boards.md:158-163`:
*"chip passives and SOT-23 may sit on the plate-facing side; nothing with a
body over about 1.4 mm may"*, with a table headed **"Clearance, worst case"**.

### 3.1 Part heights against real package data

| Part | Height | Source |
|---|---|---|
| SOIC-16, `74HC165` | **A max 1.75 mm** (A1 standoff 0.10–0.25, A2 max 1.45) | `[datasheet]` `datasheets/logic/74HC165-nexperia.pdf` p.14, SOT109-1 / JEDEC MS-012 outline table |
| SOT-23 | 1.45 mm max overall | `[from memory]` |
| 0805 thick-film resistor | ~0.55 mm max | `[from memory]` |
| 0805 X7R MLCC | ~0.85–0.95 mm max at 47/100 nF low-voltage; up to 1.45 mm for high-capacitance parts | `[from memory]` |
| `J-CHAIN` 2×6 boxed header | **9.10 ±0.15 mm shroud above the board** | `[repo] hardware/interfaces/key-chain-loom/bom.csv:2` |

### 3.2 Finding D14-5 — the table evaluates packages this board does not have

The rule's permissive row is *"0402 / 0603 chip passive ~0.5–0.6 mm"*. **Every
passive on these boards is 0805**: `C-DECOUPLE-165`, `R-KEY-PU`, `R-KEY-SER`,
`C-KEY`, `R-SER-TERM`, all `0805 (2.0 x 1.25mm)`
`[repo] hardware/cluster/cluster-boards.md:197-210`, `hardware/bom.csv:36-37`.
And the board carries **no SOT-23 at all** — the rule's other permissive row is
about a package that does not appear in the component table. Meanwhile the part
that actually dominates the plate-facing question, a 9.10 mm connector shroud,
is not mentioned by either page.

### 3.3 Finding D14-6 — the cutoff is below the package it permits

`~1.4 mm` as the limit, with SOT-23 declared "workable", is internally
inconsistent: **SOT-23 max is 1.45 mm**, so a worst-case SOT-23 breaks the rule
that admits it.

### 3.4 Finding D14-7 — nominal gap against maximum part height

The table is headed "worst case" but takes the part at max and the gap at
nominal-tight-end (2.0 mm). `[calc]` Redone against the standoff of §1.4:

| Part (max height) | at 1.30 mm nominal | at 1.20 mm worst case |
|---|---|---|
| 0805 resistor, 0.55 | +0.75 | +0.65 |
| 0805 MLCC, 0.95 | +0.35 | +0.25 |
| 0805 high-cap MLCC, 1.45 | **−0.15** | **−0.25** |
| SOT-23, 1.45 | **−0.15** | **−0.25** |
| SOIC-16, 1.75 | **−0.45** | **−0.55** |

Even in the most generous stood-off case (2.00 mm, §1.4) SOIC-16 leaves 0.25 mm
and SOT-23 0.55 mm — which is the bracket the page itself calls *"do not"*.

### 3.5 Where the clearance should be taken: worst case, stacked

Argument, not preference: **the plate is bonded to `PWR_GND` through
`MECH-GNDBOND`** `[repo] hardware/carrier/carrier.md:294`, so contact is a
short across a key network, not a fit complaint — a one-sided failure that
wants a worst-case budget. And the terms that eat a nominal margin are not
small:

```
[calc]  gap, worst case                                    1.20 mm
        PCB bow, IPC-6012 class 2 at 0.75 % of ~60 mm     −0.45 mm   [from memory]
        solder-paste / standoff and coating               −0.10 mm
        usable                                             0.65 mm
```

So the defensible rule is **≤0.6 mm plate-facing** — 0805 resistors and
low-voltage 0805 caps, nothing else — which in practice is close to the *old*
rule's effect while keeping the decoupling cap the new rule was written to
rescue. Note `C-DECOUPLE-165` is required *"at the package"*
`[repo] cluster-boards.md:198`; a 100 nF 0805 at ~0.9 mm passes at nominal and
fails a stacked worst case, so this is the one part the answer actually turns
on. The engineering fix is an insulating layer — Kapton on the plate underside,
or the conformal coating that is already an open item for these boards
`[repo] cluster-boards.md:240-243` — not a height budget with 0.25 mm in it.

---

## 4. Completeness — every statement downstream of the old conclusion

The reversal landed in `ks33-geometry.md` (commit `79f5c4a`) and was propagated
to `cluster-boards.md` §5 (commit `04b5208`). `plate-thickness` settled earlier,
in `cfcdc6e`. Below, every site that reads either.

| # | Site | State | Detail |
|---|---|---|---|
| 1 | `docs/reference/ks33-geometry.md:96-141` | **followed** (conclusion) / **wrong** (numbers) | Reversal written, cross-reference to the dependent page written. §1 above: the range is unreachable, −3.2 does not exist, the plate needs no ⌀5.25 hole, pole protrusion is 1.65 not 0.5–0.9 |
| 2 | `hardware/cluster/cluster-boards.md:153-172` | **followed** | Bullet rewritten as a height rule, cites `plate-thickness` rather than restating it, carries its own correction note. Inherits every number from #1 |
| 3 | `hardware/cluster/cluster-boards.md:236-237` | **NOT FOLLOWED** | *"**Plate-to-PCB standoff, and plate thickness** (§5). Both come from Gateron's drawing; the second blocks M4/M5 already."* Still lists the standoff as open 70 lines after §5 derives it, and still says **plate thickness blocks M4/M5** — the exact claim the batch closed, in the same file that says two paragraphs earlier that stiffening is what gates M4/M5 (`:175-178`). A reader who checks the "Still open" list gets the pre-fix answer |
| 4 | `config/key-layout.yaml:31-41` | **followed** | `null` → `1.20`, with the citation-chain post-mortem. See #16 for the residual |
| 5 | `docs/decisions/0002-key-switches-and-mounting.md:138-184, 237-243` | **followed** | Closure note, both candidates ruled out, open item restated as stiffening. Contains the 48 % sentence that contradicts #1's 2.0–2.4 (§1.4) |
| 6 | `docs/decisions/0002…:120-129` | **NOT FOLLOWED** | *"Known from the published specification, **pending the drawing itself**"* — the drawing is banked. And *"**Download** the datasheet and the STEP model before any CAD starts… **Put the STEP in `mechanical/`**"*: both are in `datasheets/mechanical/`, and `ks33-geometry.md:246-250` says so explicitly. Live instruction to fetch what is already banked |
| 7 | `docs/decisions/0009-enclosure-construction.md:64` | **followed** | `aluminium top plate 1.20 mm <- SETTLED by Gateron's drawing` |
| 8 | `docs/decisions/0009…:68` | **NOT FOLLOWED** | `thumb switch plate        ~2 mm` in the same stack diagram, four lines below #7. `plate-thickness` covers **PLATE-TOP *and* PLATE-THUMB** `[repo] config/figures.yaml:674`, and `PLATE-THUMB` is already `1.20mm aluminium` in the BOM with a note saying it *"follows PLATE-TOP to 1.20mm - same switch, same vendor drawing, same slot"* `[repo] hardware/bom.csv:38`. 2 mm is 0.75 mm outside the vendor window. **The checker passes on this**, because the one pattern aimed at it is the CSV spelling `PLATE-THUMB,mechanical,TBD - ~2mm` `[repo] config/figures.yaml:680` and the prose spelling is `thumb switch plate        ~2 mm` |
| 9 | `docs/decisions/0009…:71` | **NOT FOLLOWED** (benign) | *"That leaves around 20 mm of clear cavity"* — computed as 38 − 2 − 6 − 8 − 2. `[calc]` At 1.20/1.20 it is **21.6 mm**. Stale but conservative; the conclusion improves |
| 10 | `docs/decisions/0009…:181` | **NOT FOLLOWED** | Mass table row `| Aluminium top plate, 2 mm | 157 |`. `[calc]` At 1.20 mm the plate is 157 × 0.60 = **94 g**, and the total falls from ~825 g to **~762 g (1.68 lb)**. Conclusion ("squarely in EWI territory") survives; the table is a 63 g error against a settled figure |
| 11 | `docs/decisions/0009…:87-92` | **NOT FOLLOWED** | *"What is still missing is the **split** — how much of the 12.2 mm falls above versus below the mounting plane. That is on the dimensioned drawing, and it is the reason to download the drawing and the STEP model before starting M4."* `[step]` The split is measured and banked: **+7.05 above the collar seat, −5.70 below**, total 12.75. The stated blocker is discharged and the sentence still asks for the fetch. (It also leaves 12.2 vs 12.75 unreconciled — `ks33-geometry.md:71-72` records that the drawing confirms neither) |
| 12 | `docs/reference/pcb-pipeline.md:337-357` | **followed** | Blanket "no text layer" claim replaced by a pointer to `repo-maintenance.md` §3. Its *"10HP panel is 2 mm aluminium"* (`:325`) is a genuine different part — correctly covered by the register's `false_positive_note` |
| 13 | `docs/reference/repo-maintenance.md:120-135` | **followed** | Per-document extraction survey, with the Gateron row correct ("prose yes, drawing callouts no"). Chars figure disagrees with `figures.yaml` — §2 |
| 14 | `ROADMAP.md:228` | **followed** | Open-items row restated as plate stiffening, with 1.5 and 2 mm out of spec |
| 15 | `ROADMAP.md:71` and `:84` | **NOT FOLLOWED** | The bounce claim — §6 |
| 16 | `config/key-layout.yaml:29` | **partial** | `plate_cutout: 14.0`, with a comment that an earlier revision wrongly denied the MX figure. The drawing **tightens** it to `14.00 +0.05/−0.02` `[datasheet]` sheet 3 §8, which `ks33-geometry.md:68-70` records as "confirmed and tightened". The tolerance never reached the file the plate DXF is generated from — and this file is the single source of truth for that DXF (ADR 0010) |
| 17 | `hardware/bom.csv:40`, `hardware/cluster/bom.csv:3` (`PLATE-TOP`) | **followed** | `part` = `1.20mm aluminium`; the `THICKNESS OPEN:` text survives as the first segment of the pipe-separated revision history, which is this repo's convention |
| 18 | `hardware/bom.csv:38`, `hardware/cluster/key-marker-and-bits/bom.csv:2` (`PLATE-THUMB`) | **followed, with a self-stale note** | `part` = `1.20mm aluminium`, but the note still reads *"The '~2mm' in **this row's part field** is 0.8mm outside Gateron's window and must change with it"* — the field it points at no longer says that. The sentence should now point at ADR 0009:68 (#8), which is where the ~2 mm actually still lives |
| 19 | `hardware/bom.csv:39`, `hardware/cluster/bom.csv:2` (`SW1-n`) | **NOT FOLLOWED** | Note begins *"Binary. **Plate cutout must be measured.**"* ADR 0002 quotes that exact instruction and says *"**That was wrong**"* `[repo] 0002:98-100`, and the same note two sentences later says *"Datasheet and STEP model published by Gateron - use them, do not caliper the housing"*. The row contradicts itself and the ADR it cites |
| 20 | `hardware/bom.csv:59` (`PCB-CLUSTER`) | **not followed (gap, not error)** | `small, 1.6mm`. The 1.6 mm is now load-bearing for pin protrusion and pole clearance (§1.4) and the row does not say so. Note Gateron's own solderability clause assumes a **1.5 mm** PCB — `(Thickness of PCB=1.5mm)`, sheet 2 `[datasheet]` |
| 21 | `hardware/cluster/key-register/`, `key-switch-network/`, `key-marker-and-bits/` | **n/a** | None of the three carries a board-side or standoff statement. `key-switch-network.md:22` points at `cluster-boards.md` §5 for the plate cutout — a citation, correct either way. Arguably `key-register/` should carry the "IC on the far face" constraint, but absence is not staleness |
| 22 | `docs/decisions/0010-key-layout-as-data.md` | **n/a** | Plate references are all about DXF cutouts and spare-switch positions, none about thickness or standoff |
| 23 | `docs/reference/latency-budget.md:125-134, 148` | **followed** | Bounce row rewritten around the published 5 ms maximum |

**Score: 2 of the 3 documents the batch actually opened were fixed correctly;
7 live statements in 5 files still read the pre-reversal answers, and 1 of the
7 is in the very file the batch fixed.** Tenth wave, same finding as the other
nine.

### 4.1 The checker cannot see any of the seven

`[test] python3 tools/check-staleness.py` →
`PASS no live stale values | corpus 123 files, 23 circuits, 37 figures / 218 patterns | 5 unresolved (tracked) | 233 restated-not-cited (advisory)`

- The four `plate-thickness` patterns `[repo] config/figures.yaml:680` are all
  phrase-specific and none matches `thumb switch plate        ~2 mm`,
  `| Aluminium top plate, 2 mm | 157 |`, or `Plate cutout must be measured`.
  **These are exactly the "spelling of the file it must match" traps CLAUDE.md
  §2 describes**, and the miss is 0.8 mm on a settled mechanical figure.
- **The new value is restated, not cited, in eight files** —
  `ks33-geometry.md` (owner, correct), `0002` (six times), `0009:64`,
  `ROADMAP:228`, `cluster-boards.md:173`, `key-layout.yaml:41`,
  `bom.csv` ×2 rows plus two fragments. Two of those (the BOM part fields and
  the generator field) have to hold the literal. The rest are rule-1
  exposures, and the `RESTATED, NOT CITED` advisory cannot report them because
  it only lists values **with no register entry**
  `[repo] .staleness/report.txt:15`. A tracked figure restated in eight files
  is invisible to the one check built to find that shape.

### 4.2 Adjacent: the *other* reversal in the same batch has the same hole

Not my fact domain, but one instance is in a file I was asked to audit, and it
is the same failure shape, so it is reported rather than left. ADR 0009
retired the bonded body — *"The body is **not** bonded shut any more"*
`[repo] docs/decisions/0009…:493-494, 555-560`, *"six fasteners"*. Live
statements that still assume it:

- `[repo] config/key-layout.yaml:150` — *"the body bonds shut, so it could
  never have become a switch anyway"* (in my slice's file)
- `[repo] hardware/cluster/cluster-boards.md:94` — *"inside something that
  bonds shut"*
- `[repo] hardware/cluster/key-marker-and-bits/key-marker-and-bits.md:69, 133`
- `[repo] docs/decisions/0001-mcu-and-board-partitioning.md:160, 337`
- `[repo] hardware/carrier/carrier.md:339`

Six sites. In at least two the bonded body is the *load-bearing premise* of an
argument (why a free bit can never become a switch; why the loom must be right
first time) — which is CLAUDE.md §5's "an argument survives its own refutation",
and no grep will find it.

---

## 5. What gates M4/M5 — real, but missing its decider

**The stiffening question is real, not invented.** It is the residue of a
genuine change: `1.20 < 1.5 < 2`, so both stiffening plans ADR 0002 was
choosing between — *"thin the plate and recover the stiffness from the
lamination"* or *"keep 2 mm and design the backer as a structural member"*
`[repo] 0002:157-165` — are out of spec, and the cheap one becomes the floor.
It is also not new: ADR 0002 requirement 3 *"The plate does not flex… it needs
ribs, a backer, or a PCB acting as stiffener"* `[repo] 0002:52-54` predates all
of this. The change promoted an option to a requirement; it did not invent a
hole.

`[calc]` And it is quantitatively justified — plate bending stiffness goes as
`t³`:

```
  (1.20/1.50)³ = 0.512   →  51 % of an MX-standard 1.5 mm plate
  (1.20/2.00)³ = 0.216   →  22 % of the 2 mm plate ADR 0009 first specified
```

A 78 % loss of bending stiffness against the original plan, on a part ADR 0009
calls *"the extreme case… a flat plate with a grid of rectangular cutouts"*
`[repo] 0009:218-220`. "Compulsory" is the right word.

**It is tracked**, in two places that agree:
`[repo] ROADMAP.md:228` (open-items table, blocks M4/M5) and
`[repo] docs/decisions/0002…:237-243` (Open section, *"Still blocks M4 and
M5"*), plus `[repo] cluster-boards.md:175-178`.

**Finding D14-8 — it has no decider.** CLAUDE.md requires unresolved things to
be marked *"with what decides them"*. Neither site names one: ROADMAP:228 lists
three options (*"lamination, a structural backer, or a ribbed sub-frame"*) and
no test, calculation or measurement that chooses between them; ADR 0002 says
*"whether it is sufficient on its own at 1.20 mm is a new question this ADR has
not asked"* and stops. Two candidates already exist in the corpus and neither
is wired up: ADR 0002's *"confirming by hand at M1 with a real switch in a real
offcut"* `[repo] 0002:213-215` decides push-through (requirement 2) but not
flex, and the M1 test coupon decides the cutout fit but not stiffness. The
`t³` ratio above, plus a span figure once M3 fixes key positions, would decide
it on paper.

**And one site still names the closed question as the gate** — `[repo]
cluster-boards.md:236-237`, item 3 in §4.

---

## 6. The bounce correction

### 6.1 The hysteresis half is still right — verified

`[test]` The drawing's sheet 6 text layer contains `operating point` and
`reset point` as labels on the Force-Travel diagram, and no reset-travel
dimension anywhere; pre-travel is given (`7.Pre travel: 1.7±0.4mm`) and reset
travel is not. `[datasheet]` A 700 dpi render of the diagram shows both points
marked on an undimensioned chart. The manifest's own reading agrees —
*"a dimensioned actuation/reset hysteresis gap (the Force-Travel diagram plots
both points but is not dimensioned)"* is on its `DOES NOT contain` list
`[repo] datasheets/MANIFEST.csv:70`.

So `[repo] ks33-geometry.md:232-238` and `[repo] 0002:217-221` are correct, and
the register's decision to keep *"the actuation/reset hysteresis gap, which
Gateron does not publish"* out of the forbidden list via
`false_positive_note` `[repo] config/figures.yaml:648-654` was right.

`ROADMAP.md:118-120`'s *"the gap… scales to roughly 0.3 mm"* off the
undimensioned chart is a defensible bracket, and the page says as much. Flagged
only because `repo-maintenance.md` warns that an eyeball pass on a curve in
this repo was once wrong by 60 % `[repo] docs/reference/repo-maintenance.md:143-146`;
the chart's vectors are extractable and could give a calibrated number if it
ever matters.

### 6.2 Finding D14-9 — `ROADMAP.md:71`. The sibling slice's claim is CONFIRMED

`[repo] ROADMAP.md:71`, the M1 row:

> **bounce and the actuation/reset hysteresis gap scoped** on fast press, slow
> press, fast release, slow release and a worn switch — **neither is published**

`[test]` `grep -c "neither is published"` over the corpus → **1**, this line.
None of the five patterns in `ks33-contact-bounce`
`[repo] config/figures.yaml:641` matches it: `does not publish contact bounce`,
`bounce duration and the reset point`, `bounce is not published`,
`no published bounce figure`, `bounce, which Gateron does not`. **A fourth
spelling, live, and the checker is green.** It is also the row that defines
what M1 is *for*, and it is 47 lines from the ROADMAP's own refutation.

### 6.3 Finding D14-10 — a fifth spelling, 13 lines further down

`[repo] ROADMAP.md:84`:

> **CAD can start now** — M1 narrows to confirming the *achieved* fit in real
> material, and to **the two timing figures nobody publishes**.

`[test]` `grep -c "nobody publishes"` → **1**. Also unmatched by all five
patterns. Only one of the two timing figures is unpublished now; the other has
a vendor maximum. Note this sentence sits *inside* the paragraph that celebrates
Gateron publishing the drawing and the STEP model — the same two sentences.

`ROADMAP.md` therefore says bounce is unpublished at `:71` and `:84`, and
published at `:118-120`. Suggested patterns, both of which fire exactly once and
on a false sentence: `neither is published` and
`the two timing figures nobody publishes`.

### 6.4 Everywhere else the corpus touches the availability of the figure

| Site | State |
|---|---|
| `docs/reference/ks33-geometry.md:206, 211-230` | **followed** — published spec table carries it, with the four-wave post-mortem |
| `docs/decisions/0002…:217-226` | **followed** — bounce split out and cited as `ks33-contact-bounce`, hysteresis half kept |
| `docs/reference/latency-budget.md:125-134, 148` | **followed** — *"No longer an unknown, only an unmeasured maximum"* |
| `docs/reference/repo-maintenance.md:128-135` | **followed** — names this as the row that cost something |
| `docs/reference/ks33-geometry.md:232` | **followed** — heading *"Not available anywhere"* now covers only the hysteresis gap, and the body says so |
| `firmware/README.md:25-28` | **gap, not error** — *"the release window is set from measured KS-33 bounce (milestone M1)"* makes no availability claim, but does not cite the figure either, although the register's `companion` field asserts it does: *"firmware/README.md sets the release window from measured bounce at M1, and this is the number M1 must come in under"* `[repo] config/figures.yaml:656`. The 5 ms bound M1 must beat is not stated on the page that implements the window |
| `ROADMAP.md:71`, `:84` | **NOT FOLLOWED** — §6.2, §6.3 |

### 6.5 The figure's owner is unchecked

`[test] .staleness/report.txt:11` —
`[ks33-contact-bounce] value '5 ms max at 16 in/sec actuation' has no token distinctive enough to locate - owner docs/reference/ks33-geometry.md is UNCHECKED`.
So the figure is defended by five hand-written patterns and nothing else, and
two of the five were removed-and-replaced within twenty minutes of being
written `[repo] config/figures.yaml:642-655`. Two live escapes is what that
buys. (Tooling slice's territory; noted here because it is why §6.2 and §6.3
are still live.)

---

## 7. Findings, ranked

| ID | Finding | Confidence | What would settle it |
|---|---|---|---|
| D14-3 | **The standoff is 1.30 mm (2.50 − 1.20), not 2.0–2.4 mm.** The published range's upper end is impossible; its premise (⌀1.2 holes) contradicts Gateron's recommended ⌀3.00 pattern; and the stood-off reading it needs violates ADR 0002 requirement 2. ADR 0002:181 already implies 1.30 | **High** — two vendor dimensions and one subtraction | A decision, recorded nowhere yet: **does the cluster PCB seat against the switch housing bottom?** Everything follows from that one line |
| D14-7 / D14-5 / D14-6 | **The height rule is unsafe as written.** At 1.20–1.30 mm, SOT-23 and high-cap 0805 interfere; the cutoff (1.4) is below the SOT-23 max (1.45) it permits; the table's packages are 0402/0603 and SOT-23 while the board is all-0805 and has no SOT-23, and it omits the 9.10 mm connector | **High** on the arithmetic, **medium** on the 0805 MLCC height (`[from memory]`, varies by part number) | Pick the actual `C-DECOUPLE-165` part number and read its height off a datasheet; then decide Kapton-or-height-budget |
| D14-9 / D14-10 | **`ROADMAP.md:71` and `:84` still say the bounce figure is unpublished** — a fourth and fifth spelling, both unmatched by all five patterns, in the row that defines M1 | **Certain** — `[test]` grep | — |
| #8 (§4) | **`0009:68` still specifies a ~2 mm thumb plate**, 0.75 mm outside the vendor window, for a plate that already reads 1.20mm in the BOM. Checker green | **Certain** | — |
| D14-1 | **The −3.2 mm blade transition is not in the solid** (it is −3.00), so the only input to the published window is wrong | **High** — `[step]`, reproducible | Re-run §1.5 |
| D14-8 | **The M4/M5 gate is real and tracked but names nothing that decides it**, and one site (`cluster-boards.md:236`) still names the closed question as the gate | **High** | Name the decider: the `t³` calc against M3's span, plus the M1 offcut test for push-through |
| D14-4 | Sheet 3's recommended-plate tolerance is **+0.01/−0.05**, not ±0.05; four documents compute "0.25 mm over" from the wrong band while the manifest has it right | **Certain** — `[datasheet]` | — |
| §1.6 | The plate needs **no ⌀5.25 hole** (the 14.00 cutout is the clearance); pole protrusion is **1.65 mm**, not 0.5–0.9; latch interference is **0.35 mm/side**, not 0.49 | **High** | — |
| #6, #11, #19 (§4) | Three live instructions to fetch or measure what is already banked: *"pending the drawing itself"*, *"the reason to download the drawing and the STEP model before starting M4"*, *"Plate cutout must be measured"* | **Certain** | — |
| #9, #10 (§4) | ADR 0009's cavity (~20 → 21.6 mm) and mass table (157 → 94 g, total 825 → 762 g) were computed at 2 mm. Both conclusions survive | **High** — `[calc]` | — |
| §4.1 | A tracked figure is **restated in eight files** and the `RESTATED, NOT CITED` advisory cannot see it, because it only reports values with no register entry | **Certain** — `[test]` | Have the advisory also report tracked values written out anywhere but the owner |
| §4.2 | The **bonded-body reversal has six unfollowed sites**, two of them load-bearing premises. Same shape, different fact domain | **High** | Belongs to whichever slice owns the enclosure |

## 8. What I could not settle

- **0805 MLCC and SOT-23 heights are `[from memory]`.** No banked datasheet
  covers either; nothing in `datasheets/` is a passive or a SOT-23 part. The
  SOIC-16 1.75 is `[datasheet]`-solid, and it is the one the rule fails on
  worst, so the conclusion does not depend on the weak numbers — but the
  0805-MLCC row does, and that is the row the decoupling-cap decision turns on.
- **Whether the PCB seats on the switch housing bottom.** I have argued it must
  (ADR 0002 requirement 2, Gateron's ⌀3.00 pattern, a 1.00 mm pin protrusion
  that is exactly right for a through-hole joint). But it is an inference from
  three pieces of evidence, not a recorded decision, and the entire standoff
  number hangs on it. **This is the single missing sentence in the corpus.**
- **The hysteresis gap to better than "roughly 0.3 mm".** The chart is
  undimensioned; its vectors are extractable and I did not calibrate them.
- **12.2 mm vs 12.75 mm overall switch height.** `[step]` measures 12.75;
  `ks33-geometry.md:71-72` records that the drawing confirms neither; ADR 0009's
  cavity arithmetic uses 12.2. Out of this slice, but it is the same artefact
  and the same batch.
