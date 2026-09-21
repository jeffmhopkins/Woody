# LOGIC — 74HC165 3.3 V threshold question (wave R7)

**Headline: the 0.75/0.25 move is REFUTED by a published 3.0 V row.**
ON Semiconductor's MC74HC165A datasheet tabulates `VCC = 3.0 V` explicitly:
**`VIH` = 2.1 V, `VIL` = 0.9 V — i.e. 0.70 / 0.30 × VCC.** The ratio the repo
argued "breaks below 4.5 V" is in fact published, flat, at 3.0 V.

Three documents banked this session. Two of them (Nexperia, Toshiba) confirm the
repo's *factual* premise — they too omit a 3 V row — and the third overturns the
*inference* the repo built on that omission.

---

## Documents banked

| File | Doc no. / rev / date | Pages | 3.0 V row? |
|---|---|---|---|
| `datasheets/other-semi/74HC165-nexperia.pdf` | Nexperia `74HC_HCT165`, **Rev. 8 — 9 May 2025** | 20 | **NO** |
| `datasheets/other-semi/74HC165-onsemi.pdf` | onsemi `MC74HC165A/D`, **Rev. 13, April 2025** | 16 | **YES** |
| `datasheets/other-semi/74HC165-toshiba.pdf` | Toshiba `TC74HC165P/F`, 1986 `TC74HC` series databook, scan pp. 225–230 | 6 (excerpt) | **NO** |

Already in repo: `datasheets/other-semi/74HC165.pdf` = TI `SCLS116E`, Dec-1982
rev Sep-2003 — **NO** 3 V row (re-verified by hand this session, see Q0).

---

## Q0. Is the repo's description of SCLS116E correct?

**Repo belief** `[repo] hardware/controller/cluster-boards.md:156-165`, restated
in `config/figures.yaml:48`: SCLS116E tabulates exactly 2 V (1.5/0.5), 4.5 V
(3.15/1.35), 6 V (4.2/1.8) and has no 3.3 V row.

**Datasheet text** `[datasheet SCLS116E p.4]`, "recommended operating conditions":

```
                                            VCC = 2 V     1.5          1.5
 VIH   High-level input voltage             VCC = 4.5 V   3.15         3.15      V
                                            VCC = 6 V     4.2          4.2
                                            VCC = 2 V           0.5          0.5
 VIL   Low-level input voltage              VCC = 4.5 V         1.35         1.35 V
                                            VCC = 6 V           1.8          1.8
```

**Verdict: CONFIRMED.** Three rails only, values exactly as the repo quotes them,
given as **absolute volts** (not as fractions of VCC). Grepping the whole
extracted text for `3.0 V` / `3.3 V` in a threshold context returns nothing.

Minor note, not a defect: the repo quotes SCLS116E's double-clocking warning
`[repo] cluster-boards.md:176-178`. That footnote is real `[datasheet SCLS116E
p.4, footnote ‡]` but is **scoped to the 2 V rail** — "from `VILmax` = 0.5 V to
`VIHmin` = 1.5 V … operating with the inputs at `tt` = 1000 ns and `VCC` = 2 V".
Quoting it as a general reason not to shave margin is fair; quoting it as a 3.3 V
statement would not be.

---

## Q1. Nexperia 74HC_HCT165 — does it have a 3.0 V row?

**Verdict: NO. NOT-IN-DOCUMENT.** The brief's expectation that Nexperia HC parts
"commonly tabulate 3.0 V, 4.5 V and 6.0 V" does **not** hold for this part. That
pattern belongs to Nexperia's AHC/LVC families, not 74HC.

`[datasheet 74HC_HCT165 Rev.8 p.6, Table 6 "Static characteristics"]`, verbatim:

```
74HC165
VIH   HIGH-level input   VCC = 2.0 V    1.5    1.2    -     1.5   -    1.5   -   V
      voltage            VCC = 4.5 V    3.15   2.4    -     3.15  -    3.15  -   V
                         VCC = 6.0 V    4.2    3.2    -     4.2   -    4.2   -   V
VIL   LOW-level input    VCC = 2.0 V    -      0.8    0.5   -     0.5  -     0.5 V
      voltage            VCC = 4.5 V    -      2.1    1.35  -     1.35 -     1.35 V
                         VCC = 6.0 V    -      2.8    1.8   -     1.8  -     1.8 V
```

- **VCC columns present: 2.0 / 4.5 / 6.0 only.** Same three rails as TI.
- Values **identical to TI** at every shared rail.
- Given as **absolute volts**, min for `VIH`, max for `VIL`.
- Column headings verbatim: `25 °C` (Min/Typ/Max), `-40 °C to +85 °C` (Min/Max),
  `-40 °C to +125 °C` (Min/Max).
- Searching the full 20-page text for `3.0 V` / `3.3 V` / `2.7 V` returns exactly
  **one** hit, and it is not a threshold row: a features bullet `[p.1]`
  "Complies with JEDEC standards: • JESD8C (2.7 V to 3.6 V)". Worth knowing —
  JESD8C is the 3.3 V LVCMOS interface standard and specifies `VIH` = 0.7 × VDD,
  `VIL` = 0.3 × VDD — so Nexperia's own compliance claim points at **0.70/0.30**
  at 3.3 V, not 0.75/0.25. That is a second, independent strike against the move,
  though it is a standards reference rather than a tabulated row.
- Dynamic table `[p.8-9, Table 7]` also has only 2.0/4.5/6.0 (plus a
  `VCC = 5.0 V; CL = 15 pF` typ-only column).

### Extracted figures (Nexperia, 74HC165 side)
| Parameter | Value | Cite |
|---|---|---|
| `tpd` CP or CE → Q7/Q7 | 2.0 V: 165 ns max; **4.5 V: 33 ns max** (19 typ); 6.0 V: 28 ns max; 5.0 V/15 pF: 16 ns typ | p.8 |
| `tpd` PL → Q7/Q7 | 4.5 V: 33 ns max (18 typ) | p.8 |
| `tpd` D7 → Q7/Q7 | 4.5 V: 24 ns max (13 typ) | p.8 |
| `fmax` | 2.0 V: 6 MHz min; **4.5 V: 30 MHz min** (51 typ); 6.0 V: 35 MHz min | p.9 |
| `tsu` DS→CP | 4.5 V: 16 ns min | p.9 |
| `th` | 5 ns min, all rails | p.9 |
| `CI` input capacitance | **3.5 pF typ** | p.6 |
| `ICC` | **8.0 µA max** @ 25 °C, VCC = 6.0 V (80 µA ≤85 °C) | p.6 |
| `CPD` | 35 pF per package | p.9 |
| `Δt/ΔV` input transition rate | 4.5 V: **139 ns/V max**; 2.0 V: 625 ns/V | p.6, Table 5 |
| Overvoltage tolerance | inputs tolerant to **15 V** | p.1 |

**No 3.3 V figure for any of these** — nearest rail is 4.5 V throughout.

---

## Q2. Toshiba TC74HC165 — does it have a 3.0 V row?

**Verdict: NO. NOT-IN-DOCUMENT.**

The modern `TC74HC165AP_datasheet_en.pdf` is **unreachable** (403 at every
Toshiba host tried — see BLOCKED list below). What I did obtain is Toshiba's own
`TC74HC` series databook (1986), which carries the `TC74HC165P/F` data pages.

`[datasheet Toshiba TC74HC series databook 1986, scan p.228 = excerpt p.4,
"TC74HC165P/F — DC ELECTRICAL CHARACTERISTICS"]`, verbatim (OCR of a scan):

```
                              VCC    MIN.   TYP.  MAX.  MIN.  MAX.
                              2.0    1.5     -     -    1.5    -
        VIH                   4.5    3.15    -     -    3.15   -    V
                              6.0    4.2     -     -    4.2    -
                              2.0     -      -    0.5    -    0.5
Low-Level     VIL             4.5     -      -   1.35    -   1.35   V
                              6.0     -      -    1.8    -    1.8
```

- **VCC columns present: 2.0 / 4.5 / 6.0 only.** Absolute volts.
- Values **identical to TI and Nexperia** at every shared rail.
- Column headings verbatim: `Ta=25°C` (MIN./TYP./MAX.), `Ta=-40~85°C` (MIN./MAX.).
- Other extracted figures `[excerpt p.4-5]`: `fMAX` = 48 MHz typ at VCC = 5 V,
  25 MHz min at 4.5 V; `tpHL/tpLH` (CK, CK INH → QH/QH) 4.5 V: 38 ns max;
  `CIN` = **5 pF typ, 10 pF max**; `ICC` = 4.0 µA max at 25 °C;
  `tr,tf` 0–500 ns at VCC = 4.5 V. Supply range 2–6 V.

**Honesty flags on this document.** (a) It is a **1986 databook, not the current
datasheet**, and it documents `TC74HC165P/F`, **not** the `TC74HC165AP` the brief
named — the "A" is a later speed grade. (b) The banked file is a **6-page excerpt**
(scan pages 225–230) cut from a 23.6 MB, 675-page book with `pdfseparate`/`pdfunite`;
banking the whole book would have near-doubled `datasheets/` (28 MB today). The
parent document's SHA-256 is recorded in the manifest notes so the excerpt is
checkable against it. (c) It is an OCR'd scan; I read the `VIH`/`VIL` rows as
clean, and they agree digit-for-digit with two independent modern datasheets,
which is the cross-check that makes them trustworthy.

---

## Q3. THE CRUX — ON Semi MC74HC165A publishes the missing row

**Verdict: REFUTES the 0.75/0.25 move.**

`[datasheet MC74HC165A/D Rev.13 p.4, "DC ELECTRICAL CHARACTERISTICS (MC74HC165A)"]`,
verbatim:

```
                                                                    Guaranteed Limit
                                                          VCC
Symbol    Parameter                  Test Conditions       V    -55 to 25°C   ≤85°C   ≤125°C  Unit
  VIH     Minimum High-Level Input   Vout = 0.1 V or       2.0      1.5        1.5     1.5     V
          Voltage                    VCC - 0.1 V           3.0      2.1        2.1     2.1
                                     |Iout| ≤ 20 µA        4.5      3.15       3.15    3.15
                                                           6.0      4.2        4.2     4.2
  VIL     Maximum Low-Level Input    Vout = 0.1 V or       2.0      0.5        0.5     0.5     V
          Voltage                    VCC - 0.1 V           3.0      0.9        0.9     0.9
                                     |Iout| ≤ 20 µA        4.5      1.35       1.35    1.35
                                                           6.0      1.80       1.80    1.80
```

- **VCC columns present: 2.0 / 3.0 / 4.5 / 6.0.** This is the one document of the
  four that characterises the family at 3 V.
- **`VIH` at 3.0 V = 2.1 V = 0.70 × VCC. `VIL` at 3.0 V = 0.9 V = 0.30 × VCC.**
- Absolute volts, not fractions. Column headings verbatim as above.
- Corroborated elsewhere in the same document: the Recommended Operating Ranges
  table `[p.3]` also carries a 3.0 V row (`tr, tf`, `VCC = 3.0 V`, 0–600 ns), and
  the AC table `[p.4]` carries 3.0 V rows throughout — so 3 V is a fully
  characterised rail for this part, not a stray line.

### Extracted figures (ON Semi, MC74HC165A) — including the 3.0 V rail
| Parameter | 2.0 V | **3.0 V** | 4.5 V | 6.0 V | Cite |
|---|---|---|---|---|---|
| `VIH` min | 1.5 | **2.1** | 3.15 | 4.2 V | p.4 |
| `VIL` max | 0.5 | **0.9** | 1.35 | 1.80 V | p.4 |
| `fmax` (50 % duty) | 6 | **18** | 30 | 35 MHz | p.4 |
| `tPLH/tPHL` CLK (or CLK INH) → QH/QH, max | 150 | **52** | 30 | 26 ns | p.4 |
| `tPLH/tPHL` SH/LD → QH/QH, max | 175 | **58** | 35 | 30 ns | p.4 |
| `tPLH/tPHL` input H → QH/QH, max | 150 | **52** | 30 | 26 ns | p.4 |
| `tTLH/tTHL` output transition, max | 75 | **27** | 15 | 13 ns | p.4 |
| `tr, tf` input, max | 1000 | **600** | 500 | 400 ns | p.3 |
| `Cin` max | — | 10 pF (all rails) | — | — | p.4 |
| `ICC` max (per package) | 4 µA @25 °C, VCC = 6.0 V (40 µA ≤85 °C, 160 µA ≤125 °C) | | | | p.4 |
| `CPD` | 40 pF typ @ 5.0 V | | | | p.4 |

The 3.0 V column values above are the **nearest published rail to 3.3 V** and are
what the repo should cite for timing as well as thresholds.

---

## Q4. Why the repo's inference was wrong, precisely

The repo's argument `[repo] config/figures.yaml:48`:

> "The 0.70/0.30 ratio holds at 4.5 V and above and BREAKS at 2 V, so
> extrapolating it DOWN to 3.3 V runs through the one datapoint that contradicts
> it. The conservative bound is the 2 V ratio."

The reasoning treats the 2 V point as evidence of a **trend** — that the ratio
rises as VCC falls, so somewhere between 2 V and 4.5 V it must be above 0.70, and
0.75 is the safe bound. The published data says otherwise: the HC family's ratio
is **flat at 0.70/0.30 for every rail from 3.0 V upward**, and **2.0 V is the sole
exception**, at the very bottom of the operating range.

So 3.3 V is not an extrapolation at all — it is **bracketed on both sides by
published 0.70/0.30 rows** (3.0 V and 4.5 V). Nothing needs to be run through the
2 V datapoint.

`[calc]` Linear interpolation in absolute volts between ON Semi's two bracketing
rows, which needs no ratio assumption whatsoever:

```
VIH(3.3) = 2.1  + (3.3-3.0)/(4.5-3.0) × (3.15 - 2.1 ) = 2.1  + 0.2 × 1.05 = 2.31 V   (= 0.7000 × 3.3)
VIL(3.3) = 0.9  + (3.3-3.0)/(4.5-3.0) × (1.35 - 0.9 ) = 0.9  + 0.2 × 0.45 = 0.99 V   (= 0.3000 × 3.3)
```

Interpolation and the flat ratio give the **same answer to four decimal places**.

**Strength of the transfer to the fitted part.** The 3.0 V row is ON Semi's, and
the repo's banked TI/Nexperia documents do not publish it. What makes it
transferable: all four documents agree **exactly**, digit for digit, at every rail
they share — 2.0 V: 1.5/0.5; 4.5 V: 3.15/1.35; 6.0 V: 4.2/1.8. These are JEDEC HC
family input-threshold numbers, not vendor-specific trims. A document that matches
the others at all three shared points and adds a fourth is supplying the row the
others omit, not asserting a different device. `hardware/bom.csv:8` lists `U-KEYS`
manufacturer as **"multiple"**, so an MC74HC165A is itself a legitimate fit.

---

## Q5. Corrected figures — arithmetic, reusing figures.yaml's derivations exactly

Constants from `[repo] config/figures.yaml:47,58`: VCC = 3.3 V, pull-up 2.2 kΩ,
switch leg 100 Ω, C = 47 nF.

```
Pressed node:  V_p = 3.3 × 100/(2200+100) = 330/2300 = 0.143478 V
```

**Release (crossing `V_IH`), τ = 2.2 kΩ × 47 nF = 103.40 µs**
```
t = -103.40 × ln((3.3 - 2.31)/(3.3 - 0.143478))
  = -103.40 × ln(0.99 / 3.156522)
  = -103.40 × ln(0.313634)
  = -103.40 × (-1.159473)
  = 119.894 µs  →  119.9 µs
```

**Press (crossing `V_IL`), τ = (2.2 kΩ ∥ 100 Ω) × 47 nF = 95.6522 Ω × 47 nF = 4.4957 µs**
```
t = -4.4957 × ln((0.99 - 0.143478)/(3.3 - 0.143478))
  = -4.4957 × ln(0.846522 / 3.156522)
  = -4.4957 × ln(0.268171)
  = -4.4957 × (-1.316235)
  = 5.917 µs  →  5.92 µs
```

| Figure | Repo value now | Corrected | Note |
|---|---|---|---|
| `V_IH` at 3.3 V | 2.475 V (0.75×) | **2.31 V (0.70×)** | ON Semi 3.0 V row + 4.5 V row bracket it |
| `V_IL` at 3.3 V | 0.825 V (0.25×) | **0.99 V (0.30×)** | same |
| `key-release-time` | 138.7 µs | **119.9 µs** | |
| `key-press-time` | 6.89 µs | **5.92 µs** | still 42× inside the 250 µs scan |

**The corrected values are exactly the ones the move discarded.** 119.9 µs and
5.92 µs, and the thresholds 2.31 V / 0.99 V, are all currently sitting in the
`forbidden` lists of `key-release-time` and `key-press-time`
`[repo] config/figures.yaml:49,60`. The `[from memory]` values the page originally
carried were right; the "correction" moved away from them.

Reverting therefore requires the full three-step procedure **with the forbidden
lists inverted** — `"138.7 us"`, `"6.89 us"`, `"0.75 x VCC = 2.475"` and
`"0.25 x VCC = 0.825"` become forbidden, and `119.9`/`5.92`/`2.31`/`0.99` must come
**out** of the forbidden lists or the checker will reject the corrected text.
Note `key-release-time`'s existing `false_positive_note` about bare `125`: the
`119.9`-family strings being removed are phrase-matched, so this is a
list-inversion, not a loosening.

**This is a correctness fix, not a safety regression.** 0.75/0.25 is the more
pessimistic bound in both directions, and the page itself says neither figure
changes a conclusion `[repo] cluster-boards.md:169-171`. If the project wants to
keep the pessimistic number as design margin, the honest framing is "designed
against 0.75/0.25 for margin; the published family value at 3.3 V is 0.70/0.30" —
what is not defensible is the present text, which states 0.75/0.25 **as the
datasheet threshold** and says the 0.70 ratio "breaks".

---

## Q6. Dependents — what has to move with it

`grep -rn "74HC165\|V_IH\|V_IL\|138.7\|6.89\|119.9\|5.92" --include=*.md --include=*.csv --include=*.yaml`
over the design corpus (`docs/review/`, `docs/log/`, `docs/research/` excluded as
historical records per CLAUDE.md §4):

| Location | What it says | Action |
|---|---|---|
| `config/figures.yaml:44,47,48,49` | `key-release-time` 138.7 µs, derivation, `threshold_note`, `forbidden` | **Revert value; rewrite `threshold_note` around the ON Semi 3.0 V row; invert `forbidden`** |
| `config/figures.yaml:55,58,59,60` | `key-press-time` 6.89 µs, ditto | **Same.** The separate τ-parallel fix (4.4957 µs, not 4.7 µs) in this note is **independent and correct** — keep it |
| `hardware/controller/cluster-boards.md:151-152` | "`V_IH` = 0.75 × VCC = 2.475 V, `V_IL` = 0.25 × VCC = 0.825 V `[repo, verified against SCLS116E]`" | **Change to 0.70/2.31 and 0.30/0.99**; the `[repo, verified against SCLS116E]` mark is misleading — SCLS116E has no such row to verify against |
| `hardware/controller/cluster-boards.md:154-178` | the whole "no 3.3 V row / ratio breaks" block, incl. the 3-row table and "119.9 → 138.7 µs and 5.92 → 6.89 µs" | **Rewrite.** The 3-row table is a correct description of SCLS116E and can stay as such; the *inference* drawn from it must go, replaced by the ON Semi 3.0 V row |
| `hardware/controller/cluster-boards.md:184-185` | timing table: 138.7 µs, 6.89 µs, "36× inside the 250 µs scan" | **119.9 µs, 5.92 µs, 42×** `[calc]` 250/5.917 = 42.2 |
| `hardware/controller/cluster-boards.md:4-5` | "No datasheet was reachable from this sandbox, so the 74HC165 pin map below is `[from memory]`" | **Stale as of this session** — three are banked now |
| `hardware/controller/cluster-boards.md:91` | pin map marked `[from memory: pin map]` | **Confirmed correct, see Q7** — promote the marking |
| `hardware/controller/cluster-boards.md:502-503` | open question: "Every number in this page's timing table rests on `V_IH` = 0.7 × VCC and `V_IL` = 0.3 × VCC `[from memory]`. Five minutes with a datasheet." | **Already self-contradictory today** — see below. Resolvable and closable |
| `datasheets/MANIFEST.csv:38,51,52` | row 38 notes "Nexperia … and Toshiba … not found"; rows 51/52 BLOCKED | **Rows 51/52 now OK**; row 38's note needs its "not found" clause dropped; add ON Semi row |
| `hardware/bom.csv:8` (`U-KEYS`) | 74HC165, mfr "multiple", `CLK INH` tied low at all four | **No change.** `CLK INH` low confirmed correct `[datasheet MC74HC165A p.3 function table]` |

**An internal contradiction already live in the repo, independent of my finding:**
`cluster-boards.md:502-503` still asserts the page's numbers rest on
`V_IH` = 0.7 × VCC / `V_IL` = 0.3 × VCC `[from memory]`, while `:151-152` of the
same file now says 0.75/0.25. The staleness checker cannot see this — it greps
values, and `0.7 × VCC` there is prose in an open-questions list. This is exactly
the CLAUDE.md §4 "fixes land where the editing is happening, not where the reader
looks" failure, and it happened **inside the commit that made the 0.75 move**.
Amusingly the stale line is the one that was right.

Historical records containing the old numbers — `docs/research/.../R10-keyscan-and-adc.md`,
`docs/review/2026-09-21-staleness-sweep/S2-umbilical.md`, `docs/log/` — are
correctly excluded and **must not be touched** `[repo] CLAUDE.md §4`.

---

## Q7. Bonus — the `[from memory]` pin map is CONFIRMED

`cluster-boards.md:4-5` and `:502` flag the pin map as unverified. Both banked
modern datasheets confirm it exactly.

`[datasheet MC74HC165A/D Rev.13 p.1, Figure 1 "Pin Assignments"]`: 1 SERIAL
SHIFT/PARALLEL LOAD, 2 CLOCK, 3 E, 4 F, 5 G, 6 H, 7 QH̄, 8 GND, 9 QH, 10 SA,
11 A, 12 B, 13 C, 14 D, 15 CLOCK INHIBIT, 16 VCC.

`[datasheet 74HC_HCT165 Rev.8 p.4, Table 2 "Pin description"]`: PL 1; CP 2;
Q7 7 "complementary output from the last stage"; GND 8; Q7 9 "serial output from
the last stage"; DS 10 "serial data input"; **D0 to D7 = pins 11, 12, 13, 14, 3,
4, 5, 6**; CE 15; VCC 16.

That maps D0→11(A) … D3→14(D), D4→3(E) … D7→6(H) — matching the repo's drawing
pin for pin, including its `E (D4)` … `H (D7)` annotations. Also confirmed:
**`QH_bar` pin 7 is an output** (so the repo's "left open — do NOT ground it" is
right), and the bit order claim — the function table `[MC74HC165A p.2]` gives
parallel load `a…h` → `QH = h`, so `H` appears at `QH` immediately, exactly as
`cluster-boards.md:108` states. **An open question that can be closed.**

---

## BLOCKED / not obtained

| Target | URLs tried | Result |
|---|---|---|
| Toshiba TC74HC165AP (current datasheet) | `https://toshiba.semicon-storage.com/info/TC74HC165AP_datasheet_en.pdf` | **403** |
| | `…/info/TC74HC165AP_datasheet_en.pdf?did=9640&prodName=TC74HC165AP` | **403** |
| | `…/info/TC74HC165AP_datasheet_en_20140301.pdf?did=11268&prodName=TC74HC165AP` | **403** |
| | `…/us/semiconductor/product/logic-ics/detail.TC74HC165AP.html` | **403** |
| | `…/ap-en/semiconductor/product/logic-ics.html` | **403** |
| | `https://www.semicon.toshiba.co.jp/info/TC74HC165AP_datasheet_en.pdf` | DNS/connect failure, HTTP 000 |
| ST M74HC165 | `https://www.st.com/resource/en/datasheet/m74hc165.pdf` (HTTP/2 and `--http1.1`) | curl 92 / curl 52 **empty reply**, HTTP 000 |
| | `https://www.st.com.cn/resource/en/datasheet/m74hc165.pdf` | curl 52 empty reply |
| Diodes Inc 74HC165 | `https://www.diodes.com/assets/Datasheets/74HC165.pdf` | **404** (HTML error page) |
| onsemi via .com | `https://www.onsemi.com/pdf/datasheet/mc74hc165a-d.pdf`, `/download/data-sheet/pdf/mc74hc165a-d.pdf`, `/pub/Collateral/MC74HC165A-D.PDF` | **403** — obtained via **`www.onsemi.cn`** instead, which served it 200 |
| Nexperia via www | `https://www.nexperia.com/document/pdf/74HC_HCT165.pdf`, `www.nexperia.cn/...` | **404** — but `assets.nexperia.com` **succeeded (200)** this session, contradicting the brief's "403 at the proxy" and MANIFEST rows 51/52 |

**Mirror traps caught** (per the brief's LT1641/LT4256 warning):
`https://www.farnell.com/datasheets/2299370.pdf` returned a genuine 359 kB PDF
that contains **no occurrence of "165"** — mislabelled, discarded, not banked.
`mouser.com` and `datasheet.lcsc.com` both served 9–14 kB HTML bot pages under
`.pdf` URLs; `docs.rs-online.com/1c4d/0900766b8123d1bb.pdf` returned 403 XML.
All discarded.

**Two network facts worth propagating:** `assets.nexperia.com` is reachable now
(MANIFEST rows 51/52 record it as unreachable, HTTP 000), and `www.onsemi.cn`
serves what `www.onsemi.com` 403s.

---

## Verdict summary

| Question | Verdict |
|---|---|
| Does SCLS116E lack a 3.3 V row, with the values the repo quotes? | **CONFIRMED** |
| Does Nexperia 74HC_HCT165 Rev.8 publish a 3.0/3.3 V row? | **NOT-IN-DOCUMENT** (2.0/4.5/6.0 only) |
| Does Toshiba TC74HC165P/F publish a 3.0/3.3 V row? | **NOT-IN-DOCUMENT** (2.0/4.5/6.0 only) |
| Does *any* manufacturer publish a 3.0 V row? | **YES — onsemi MC74HC165A: `VIH` 2.1 V, `VIL` 0.9 V = 0.70/0.30** |
| Is the 0.75/0.25 move correct? | **REFUTED.** 3.3 V is bracketed by two published 0.70/0.30 rows |
| `key-release-time` = 138.7 µs? | **REFUTED → 119.9 µs** `[calc]` |
| `key-press-time` = 6.89 µs? | **REFUTED → 5.92 µs** `[calc]` |
| Is the `[from memory]` pin map right? | **CONFIRMED** (two datasheets, pin for pin) |

*Researcher note per brief rule 1: no repo file was edited. The three PDFs were
dropped into `datasheets/other-semi/`; `MANIFEST.csv`, `figures.yaml` and all
`.md`/`.csv` files are untouched. Proposed manifest rows are in `LOGIC.rows.csv`.*
