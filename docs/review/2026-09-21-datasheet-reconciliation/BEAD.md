# BEAD — R7 researcher report

Assignments: (1) choose, justify and bank a ferrite bead for `FB-IN`;
(2) Gateron KS-33 vendor drawing; (3) Tai-Hao MT165 vendor drawing.

Banked this session (3 files, all verified `%PDF`, >10 kB, part number present in
`pdftotext` output):

| file | sha256 (first 16) | pages |
|---|---|---|
| `datasheets/discrete-and-power/MI1206K601R-10-ferrite-bead.pdf` | `ff9b0702a4d7d97f` | 1 |
| `datasheets/discrete-and-power/HI1206N601R-10-ferrite-bead.pdf` | `273e66b6bc57348d` | 1 |
| `datasheets/mechanical/GATERON-KS-33-VENDOR-SPEC-DRAWING.pdf` | `4ec2109e720af641` | 6 |

Proposed manifest rows are in `BEAD.rows.csv` (6 rows: 3 OK, 3 BLOCKED).

**Method note on every impedance number below.** Laird's curves are vector art with
no data table. Each value was obtained by rendering the page at 600 dpi, locating
the plot frame and the log-decade gridlines by dark-pixel projection, and
classifying curve colour in the pixel column at 100 MHz. Calibration was checked
against features the sheet states independently (the 0 A peak, the low-frequency
asymptote). Reading uncertainty is about **±10 Ω** at the top of the range and
±3 Ω at the bottom, set by the ~6 px line width. Marked `[datasheet …, pixel trace]`.

---

## 1. `FB-IN` — the ferrite bead

### 1.1 The part I chose

**Laird Performance Materials `MI1206K601R-10`** — 1206, Z@100 MHz 600 Ω nominal
(450 min / 750 max), DCR 0.080 Ω max, rated current 1500 mA.
`[datasheet MI1206K601R-10-E Rev E, electrical characteristics table]`

Source: <https://www.laird.com/sites/default/files/mi1206k601r-10-datasheet.pdf> `[web]`
(Laird product page: `.../ferrite-chip-beads/1206-series/mi1206k601r-10`).

**The trade-off I made.** The binding constraint was a published
impedance-vs-DC-bias curve, and that constraint — not price, not stock, not
brand — decided the part.

- **Murata could not satisfy it.** I did reach a genuine Murata BLM31P datasheet
  (via mirror; `www.murata.com/products/productdata/…` and `/webapi/…` are
  returning HTTP 500 "under maintenance" this session, `pim.murata.com/api` 403).
  BLM31PG601SN1L is 600 Ω ±25 %, 1500 mA, 0.09 Ω, 1206 — an almost exact
  electrical twin of the Laird part. But its datasheet carries
  impedance-vs-frequency and a **rated-current-vs-temperature derating** curve and
  **no DC-bias curve at all** — the same deficiency for which Würth WE-CBF was
  correctly declined. I checked the 170-page Murata EMIFIL catalogue C31E-6 too:
  no occurrence of "DC bias" or "superimposition". **The brief's premise that
  "Murata BLM … DO publish DC-bias characteristics" is wrong for the PDF**; Murata
  publishes bias only inside the interactive SimSurfing tool. So I did not bank a
  Murata part, for exactly the reason the earlier researcher did not bank a Würth one.
- **TDK was unreachable** — `product.tdk.com` 403s from Akamai on every path, and
  no MPZ3216 (1206) mirror exists; only the 0603 MPZ1608S601A surfaced, which is
  outside the row's "1206 or 1210".
- **Laird publishes the curve on the face of the drawing.** So I traded
  *second-sourceability and stock depth* (Murata BLM31PG601SN1L is far more widely
  stocked; Laird Performance Materials is now DuPont and this is a 2004-vintage
  drawing last revised 2013) for *a document that answers the question the row
  exists to ask*. The repo's own rule — "a number read off a banked document beats
  one from a review" — says that is the right way round. **Recommended BOM
  handling: specify the Laird part as the characterised part and name
  BLM31PG601SN1L as the approved alternate, flagged "bias behaviour assumed, not
  documented".**
- I also considered, and rejected as the primary, Laird's **`MI1206L601R-10`**
  (same 600 Ω, 2.0 A, 0.08 Ω) — its drawing reuses the *identical* bias graph, so
  it adds no information — and **`HI1206N601R-10`** (600 Ω, 3.0 A, 0.06 Ω), which
  I banked separately because of what §1.3 shows.

Package: **1206 = 3.20 ±0.20 × 1.60 ±0.20 × 1.10 ±0.20 mm**, termination band
D 0.51 ±0.25. `[datasheet, PHYSICAL DIMENSIONS block]` The BOM asks for "1206 or
1210" — **matches**. Land pattern for reflow: two 2.06 × 1.13 mm pads, 4.65 mm
overall (add 0.762 mm for wave). Operating temperature −40 to +125 °C
**including self-heating** (note 4); no separate current-derating curve is given.

### 1.2 THE NUMBER THE ROW EXISTS FOR — impedance at the real operating current

Repo currents cited by id, not restated: `umbilical-current` = the instrument's
typical-play draw down the umbilical; its `false_positive_note` records that the
**module total on +12 V** is a different, larger quantity. Per-branch currents for
the four beads come from `[repo] docs/review/2026-09-21-staleness-sweep/S8-bom-reconciliation.md:111`
(FB1 +12 V analog ~45 mA, FB2 +12 V umbilical, FB3 −12 V ~10–20 mA, FB4 +5 V a few mA).

Measured off the bias curve at **100 MHz** `[datasheet MI1206K601R-10-E Rev E,
"Z vs FREQUENCY / IMPEDANCE UNDER DC BIAS", pixel trace]`:

| DC bias | Z @ 100 MHz | % of the 0 A value |
|---|---|---|
| 0 A | **614 Ω** (608–619) | 100 % |
| 250 mA | **431 Ω** (424–439) | 70 % |
| 500 mA | **157 Ω** (154–160) | 26 % |
| 1000 mA | **72 Ω** (70–75) | 12 % |
| 1500 mA (= rated) | **51 Ω** (49–53) | 8 % |

Per branch, interpolating between the two bracketing curves (`[calc]`, both a
linear and a log interpolation given because the curve is convex — the truth sits
between them):

| Bead | Branch current | Z @ 100 MHz | vs the row's "600 Ω" |
|---|---|---|---|
| FB4 | +5 V, a few mA | ~614 Ω | 100 % |
| FB3 | −12 V, 10–20 mA | ~605–612 Ω | ~100 % |
| FB1 | +12 V analog, ~45 mA | ~576–581 Ω → **~580 Ω** | 95 % |
| **FB2** | **`umbilical-current` (359 mA)** | linear 431 − (109/250)×274 = **312 Ω**; log exp(6.066 − 0.436×1.010) = **277 Ω** → **~280–310 Ω** | **~47 %** |
| FB2 | module total on +12 V (392 mA, the other figure in `umbilical-current`'s note) | linear **275 Ω**, log **243 Ω** → **~245–275 Ω** | ~42 % |
| FB2 | 620 mA (S8's upper umbilical figure) | linear **137 Ω**, log **130 Ω** → **~130 Ω** | **~22 %** |

### 1.3 LOUD FINDING — the row's premise is refuted, and not by a marginal part

**At the actual umbilical current the bead delivers roughly half the impedance the
BOM row names, and at the upper current about a fifth.** `FB-IN` says
*"Rated >=1A - the common 0805 600R part is ~300mA and a saturated bead is a wire."*
The banked curve says the rating does not rescue you:

1. **A 1.5 A-rated 600 Ω bead is already down to 26 % of its impedance at 500 mA**,
   which is *one third* of its rated current. The rated current is a **thermal**
   limit (I²·DCR self-heating inside a −40…+125 °C envelope), not a saturation
   limit. Nothing on the drawing claims otherwise.
2. **Going to a higher-rated part does not help.** I banked
   `HI1206N601R-10` — same 1206, same 600 Ω nominal, **3000 mA rated**, DCR
   0.06 Ω — precisely to test this. Its own bias curve
   `[datasheet HI1206N601R-10-C Rev C, pixel trace]` reads at 100 MHz: 0 A **635 Ω**,
   0.5 A **145 Ω**, 1 A **58 Ω**, 2 A **25 Ω**, 3 A **14 Ω**. At 500 mA the
   **3 A part (145 Ω) is slightly worse than the 1.5 A part (157 Ω)**. Doubling the
   current rating bought 0.02 Ω of DCR and *zero* impedance under bias.
3. Therefore the sentence *"the common 0805 600R part is ~300 mA and a saturated
   bead is a wire"* is directionally right about saturation but **wrong about the
   remedy**. Specifying ">= 1 A" selects for DCR and heat, not for Z-under-bias.
   If the design actually needs ~600 Ω at 359 mA, no 1206 600 Ω bead of any rating
   will give it; that requires either a much larger part, a lower nominal
   impedance accepted honestly, or (as ADR 0004 already decided for `L-BUCK-IN`)
   a real inductor.
4. Equally, the **100:1 current spread across the four beads** flagged in
   `[repo] S8-bom-reconciliation.md:111,220` is now quantified: FB1/FB3/FB4 sit on
   the flat part of the curve and get 95–100 % of nominal, FB2 alone is the one
   that collapses. One part number across all four is *harmless* (the low-current
   branches are not hurt by the 1.5 A part) but it is also *not the thing that
   saves FB2*.

### 1.4 DC resistance and IR drop

DCR **0.080 Ω max** (no typical is published). `[datasheet, electrical table]`

`[calc]` V = I × 0.080 Ω, P = I² × 0.080 Ω:

| Branch current | IR drop (worst case) | Dissipation |
|---|---|---|
| ~20 mA (−12 V) | 1.6 mV | 0.03 mW |
| ~45 mA (+12 V analog) | 3.6 mV | 0.16 mW |
| 359 mA (`umbilical-current`) | **28.7 mV** | 10.3 mW |
| 392 mA (module total on +12 V) | **31.4 mV** | 12.3 mW |
| 620 mA | 49.6 mV | 30.8 mW |

**Cross-check against the repo:** `[repo] docs/review/2026-09-20-cold-review/B10-fault-abuse.md:76`
budgets *"~0.06 V ferrite **[memory]**"*. The banked worst-case number is
**≤ 31 mV** at the module's +12 V total — the memory figure is about 2× pessimistic.
That is a review document (historical record, not corpus), so it is not a defect;
but the ~0.06 V should not be carried into any live budget. The HI part would
drop 23.5 mV at 359 mA if DCR ever matters.

### 1.5 Impedance peak and the R/X split

`[datasheet MI1206K601R-10-E Rev E, "|Z|, R and XL vs FREQUENCY", 0 A, pixel trace]`

- **Peak |Z| ≈ 663 Ω at ≈ 78 MHz** at 0 A (the companion bias graph gives the same
  peak; the |Z|/R/X graph reads 683 Ω on its own calibration, so call it
  **660–680 Ω at 75–80 MHz**).
- At **100 MHz, 0 A**: |Z| ≈ 615–630 Ω, **R ≈ 555–566 Ω**, so **R/|Z| ≈ 0.90** and
  |X| = √(Z²−R²) ≈ **270 Ω, capacitive** — X_L crosses zero at the |Z| peak
  (~75 MHz) and the part is resistive-dominant above it. Good: at 100 MHz this bead
  dissipates rather than reflects.
- Under bias the peak moves up in frequency and down in height: 250 mA ≈ 557 Ω near
  140 MHz, 500 mA ≈ 522 Ω near 230 MHz, 1000 mA ≈ 543 Ω near 310 MHz, 1500 mA ≈
  569 Ω near 370 MHz. (Amplitudes by pixel trace; the peak *frequencies* for the
  250/500 mA traces were read visually because the legend box overlaps the
  automatic search band.) **The bead does not stop working under bias — it moves.
  Its useful band slides out of the 100 MHz region the row specifies.**

### 1.6 Verdicts against the repo

| Repo belief `[repo] hardware/bom.csv:41` | Datasheet | Verdict |
|---|---|---|
| "1206 or 1210" | 3.20 × 1.60 × 1.10 mm = 1206 | **CONFIRMED** |
| ">= 1 A rated", qty 4, one part number | 1500 mA rated | **CONFIRMED** as available |
| "600R@100MHz" | 600 Ω nom (450/750) **at 0 A DC bias** | **CONFIRMED at 0 A, REFUTED in service** — ~280–310 Ω at `umbilical-current`, ~130 Ω at 620 mA |
| ">= 1 A … a saturated bead is a wire" (i.e. rating cures saturation) | 3 A part is no better than the 1.5 A part at 500 mA | **REFUTED** |
| `[repo] B10:76` "~0.06 V ferrite [memory]" | 0.080 Ω max × 392 mA = 31 mV | **REFUTED** (2× pessimistic) |
| `[repo] B5-module-power.md:21` "1206/1210 … DCR 50–100 mΩ **[from memory]**" | 0.080 Ω max (0.060 Ω for the HI part) | **CONFIRMED** |

---

## 2. Gateron KS-33 — vendor drawing OBTAINED (not blocked)

`gateron.com`, `www.gateron.com`, `gateron.co`, `www.gateron.co` and `gateron.cn`
**all answer HTTP 200 this session** (they were 000 in the last wave). Gateron
publishes a per-SKU "Product Specification" index at
<https://www.gateron.com/pages/product-specification>, and the sheet for the
linear Red — the switch `SW1-n` names — is:

<https://gateron.com/u_file/2311/10/file/GATERONKS-33LowProfile20RedSwitchBlackBottomHousing-KS-33H10B050NN-Y24.pdf>

6 pages, banked as `mechanical/GATERON-KS-33-VENDOR-SPEC-DRAWING.pdf`. Sheet 6 is
the engineering drawing: **Drawing No `KS-33H10B050NN-Y24`, Version 2, drafted
2023-01-03 (Cai Jiacai), checked WuFurong, approved He Shiying, scale 5:2, A4,
third angle, sheet ref `DS-02-001-A0`.** This is the document
`docs/reference/ks33-geometry.md` says "supersedes it wherever the two disagree".

### 2.1 It confirms the third-party CAD almost exactly

| Repo belief (from the STEP model) `[repo] docs/reference/ks33-geometry.md`, `datasheets/MANIFEST.csv:26` | Vendor drawing | Verdict |
|---|---|---|
| Collar 15.000 × 15.000 mm | **15.00 × 15.00** | **CONFIRMED** |
| Section through the cutout 14.000 × 14.000 mm | **14.00 ±0.05** | **CONFIRMED** |
| Latch arms 14.69–14.99 mm across | **14.70** | **CONFIRMED** (drawing gives the low end as nominal) |
| Housing bottom −2.50 mm below the collar underside | **2.50 ±0.05** | **CONFIRMED** |
| Pin blades reach −5.10 mm | **2.50 + 2.60 = 5.10** | **CONFIRMED to 0.00 mm** |
| Centre pole tip −5.70 mm, ⌀5.04 | **5.75 ±0.05**, **⌀5.05 ±0.05** | **CONFIRMED** (0.05 apart) |
| MX cross stem 4.0 × 1.1 mm | **1.10 ±0.04 × 4.00 +0.05/−0.10**, second arm **1.28 ±0.04 × 4.00 +0.05/−0.10** | **CONFIRMED**, and the asymmetric 1.10/1.28 arms are new |
| Plate cutout 14.0 × 14.0 mm (47 cutouts in a 3rd-party build) | **14.00 +0.05/−0.02 × 14.00 +0.05/−0.02**, drawn in §8 "the suggestion dimension of mounting" | **CONFIRMED**, tolerance tightened |
| Overall 15.0 × 15.0 × 12.75 mm; BOM "12.2 mm tall" | no overall-height dimension anywhere on the sheet | **NOT-IN-DOCUMENT** |

Also on the drawing but not previously in the repo: top housing 13.75 mm;
actuator top ⌀5.70 ±0.05; pin blade 0.45 mm thick, ⌀1.00 callout; general
tolerance table (±0.2 up to 3 mm, ±0.3 3–10, ±0.4 10–30, ±0.6 30–80, ±0.8
80–180, ±3°); PCB pattern ⌀5.25 centre with ⌀3.00 holes at 2.60/4.40 × 5.75/6.30
and a 5.00 × 1.80 slot at 2.25/4.70; a 2-terminal SPST circuit (the BOM's "3-pin"
means two signal pins plus the centre pole, consistent with the footprint).

### 2.2 **The clip dimension the repo says it is waiting for: 1.20 mm**

`[datasheet KS-33H10B050NN-Y24 sheet 3 §8, hatched plate section]`
**Recommended plate thickness = 1.20 +0.01/−0.05 mm.**
The same 1.20 ±0.05 appears independently on sheet 6's side elevation, between the
collar underside and the latch-arm shoulder.

This resolves two live open items:
- `[repo] hardware/bom.csv:22` `PLATE-TOP`: *"THICKNESS OPEN: 2mm defeats the
  retention clips entirely, MX standard is 1.5mm, the reference KS-33 build uses
  1.1mm. Decide with Gateron's clip dimension."* → **Gateron's answer is 1.20 mm.
  1.5 mm and 2 mm are both outside the vendor's window; the 1.10 mm observed in the
  third-party build is 0.05 mm under the drawing's lower limit (1.15 mm).**
- `[repo] ROADMAP.md:223` and `hardware/controller/cluster-boards.md:509`, which
  both defer plate thickness to "Gateron's clip dimension" / "Gateron's own
  drawing", can now be closed. (`cluster-boards.md:458`'s note that the reference
  build used 1.1 mm stays true as a record.)

### 2.3 Other confirmations and one refutation

`[datasheet, sheet 6 specification block]`
- Pre travel **1.7 ±0.4 mm** — **CONFIRMS** `[repo] bom.csv:2` "1.70mm pretravel".
- Total travel **3.0 ±0.2 mm** — **CONFIRMS** "3.00mm total travel".
- Operating force **50 ±15 gf** — new; relevant to `SW-THUMB`'s open
  lighter-spring question `[repo] bom.csv:86`.
- **Bounce time 5 msec Max (at 16 in/sec actuation speed)** — **REFUTES**
  `[repo] ROADMAP.md:118` *"Gateron publishes neither figure for the KS-33"*.
  Bounce **is** published. The *other* half of that sentence — the
  actuation/reset hysteresis gap — is **still not stated numerically**, but the
  sheet does plot it: the Force-Travel diagram marks an operating point and a
  reset point, which scale to roughly **1.6 mm and 1.3 mm travel, a ~0.3 mm gap**
  `[calc, scaled off an undimensioned chart — bracketing only, does not replace
  the M1 measurement]`. The firmware debounce window
  `[repo] firmware/README.md:27` is still right to be set from measurement, but
  5 ms max is now a documented sanity bound.
- Rating 12 V AC/DC max, 2 VDC min, 10 mA max, 10 µA min; contact resistance
  200 mΩ max; insulation 100 MΩ min @ 100 VDC; withstand 100 VAC 1 min;
  operating −40 to +80 °C.
- **Internal inconsistency in Gateron's own document:** sheet 6 says operation life
  **60,000,000 cycles min**, sheet 3 §6.1/§6.2 say **80,000,000 cycles**. Use the
  drawing's 60 M.
- The precaution text calls the Force-Travel diagram *"soft tactile action"* on a
  part the drawing titles *"Low Profile Red Switch 2.0"* (linear) — boilerplate,
  but worth not quoting.

---

## 3. Tai-Hao MT165 — vendor drawing BLOCKED, but vendor *specs* obtained

Host state this session: `taihao.com.tw` **000**, `www.taihao.com.tw` **000**,
`taihao.com` **000** — unchanged. But **`www.tai-hao.com` and `tai-hao.com` answer
200**, and so does Tai-Hao's own store **`shop.tai-hao.com`** (slow: a product page
timed out at 45 s and completed at 90 s).

**No drawing, PDF, STEP or dimensioned image exists** on tai-hao.com,
shop.tai-hao.com or GitHub. Routes tried, all yielding no drawing:
`https://www.tai-hao.com/search?q=MT165` (404),
`https://www.tai-hao.com/catalog` and all 60 `catalog/ins.php?index_id=N` category
entries (no MT165 entry at all), `https://shop.tai-hao.com/categories/mt165-low-profile-keycaps`,
`https://shop.tai-hao.com/products/mt165-miami-pink`, plus WebSearch. **BLOCKED.**

What the vendor's own store page *does* state, which upgrades the previous
"NOT ESTABLISHED … dimensions and stem type remain unknown" row
`[repo] datasheets/.manifest-R6.csv:16`:

> "Profile: MT165 Profile (Keycap Size: **16.5 × 16.5 mm**) … Version: Blank …
> Material: **PBT** … Compatible with: **MX switches / Choc V1 switches** … Made in
> Taiwan", sold as **18 pcs/set (16 keycaps + 2 bonus keys)**, 1U low profile.
> `[web] https://shop.tai-hao.com/products/mt165-miami-pink`

| Repo belief `[repo] hardware/bom.csv:3` | Vendor page | Verdict |
|---|---|---|
| "Keycap 16.5x16.5mm blank black MX stem" | 16.5 × 16.5 mm, blank, MX | **CONFIRMED (vendor-sourced, first time)** |
| "Sold in 5-packs - 21 keys needs 5 packs" | Tai-Hao direct sells 18 pcs/set | **CONFIRMED for the stated supplier (Beekeeb), context added** — direct from Tai-Hao, 21 keys is 2 sets |
| dimensions/stem type "unknown" (R6 manifest) | now stated by the vendor | **SUPERSEDED** |

Two cautions for the lead:
1. **Tai-Hao's store says "Choc V1"; the BOM's actual supplier (Beekeeb) says
   Choc v2 / Gateron Low Profile 2.0–3.0 / Cherry MX and explicitly *not* Choc v1.**
   They contradict each other. A Choc v1 stem is not a cross, so Tai-Hao's own
   wording is the less plausible one — but this is now a documented disagreement,
   not an assumption. The banked Gateron drawing shows the KS-33 stem is an MX
   cross (1.10/1.28 × 4.00), which is what matters.
2. The corporate catalogue lists a **different** 16.5 mm line — "THM (Tai-Hao
   Thins) Low Profile Keycaps (Blank), Dimensions: **16.5 × 17.5 mm**",
   `https://www.tai-hao.com/catalog/ins.php?index_id=110`. **Do not conflate it
   with MT165**; the store menu lists THM and MT165 as separate products. If
   anyone later "corrects" MT165 to 16.5 × 17.5, that is this trap.

Still unknown because unpublished: keycap **height**, stem depth and cross
tolerances, top-surface profile/dish, wall thickness.

---

## Provenance ledger

- `[datasheet MI1206K601R-10-E Rev E]` — banked, `discrete-and-power/MI1206K601R-10-ferrite-bead.pdf`.
- `[datasheet HI1206N601R-10-C Rev C]` — banked, `discrete-and-power/HI1206N601R-10-ferrite-bead.pdf`.
- `[datasheet KS-33H10B050NN-Y24 Version 2]` — banked, `mechanical/GATERON-KS-33-VENDOR-SPEC-DRAWING.pdf`.
- `[web]` Murata BLM31P datasheet (2006.3.9, read, not banked):
  `https://datasheets.b-cdn.net/files/BLM31PG601SN1L-Murata-datasheet-7593909.pdf`;
  Murata EMIFIL catalogue C31E-6 (read, not banked):
  `https://media.digikey.com/pdf/Data%20Sheets/Murata%20PDFs/EMI_Suppression_Filters_Cat.pdf`.
- `[web]` Laird 1206 series list (part selection):
  `https://www.laird.com/products/inductive-components-emc-components-and-ferrite-cores/ferrite-chip-beads/1206-series`.
- `[web]` `https://shop.tai-hao.com/products/mt165-miami-pink`, `https://www.tai-hao.com/catalog/ins.php?index_id=110`.
- `[calc]` every interpolation and IR-drop number, arithmetic shown inline.
- `[repo]` file:line given at each use.
- **Nothing in this report is `[from memory]`.**

## Repo files touched
Only `datasheets/discrete-and-power/` and `datasheets/mechanical/` (3 new PDFs).
No `.md`, no `bom.csv`, no `figures.yaml`, no `MANIFEST.csv` was edited.
