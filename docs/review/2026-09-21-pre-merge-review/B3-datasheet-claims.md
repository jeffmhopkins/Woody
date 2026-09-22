# B3 — Numbers the corpus claims to have read off a banked document

**Agent:** B3, cold (no `docs/review/**` read).
**Date:** 2026-09-21.
**Slice charter:** CLAUDE.md §3 — *a number read off a banked document beats one
from a review*. Re-verify every corpus figure whose derivation or provenance
cites a banked artefact, against the artefact on disk.

**Method.** `pdftotext` is not installed in this sandbox; `pip install pymupdf`
works and was used for both text extraction and rendering. Vector drawings were
rendered at 150–900 dpi and read by eye, and where the answer turned on a curve
(1N5817 Fig. 2, Laird MI1206 bias family, OPA2197 Fig. 26) the Bézier/segment
geometry was extracted from the PDF content stream and digitised numerically
against the gridlines, so the reading is reproducible rather than eyeballed.

**Provenance convention used below.** `[datasheet <file> p.N]` = read off the
banked document at that page. `[repo] path:line` = read off this repository.
`[calc]` = arithmetic shown. **Nothing in this report is `[from memory]`.**

---

## Summary

**28 datasheet-sourced claims re-verified; 21 are exactly right, several
impressively so.** The three figures CLAUDE.md §3 names as having moved (74HC165
threshold, 1N5817 `V_f` modulation, WS2815 `V_IH`) are all now correct in the
corpus, and the corrections are correctly reasoned. The ferrite bias
digitisation, the Gateron plate dimension, the NKK panel cutout, the LT1641
electrical picture, the panel-height artefacts and the SP0504BAHT reading are
all confirmed to the digit.

**Six findings have teeth**, and five of the six are the same mechanism: **a
value moved, and the spelling in `hardware/bom.csv` and its fragments is not the
spelling in the `forbidden` list**, so the checker reports PASS over live stale
numbers. `tools/check-staleness.py` reports *no live stale values* while five
places carry the retired sensor full scale and three carry retired key timings.

| # | Node / refdes | Severity | One line |
|---|---|---|---|
| **B3-01** | `U-DIFFRX`, `BREATH` | **high** | `-9.6V` live in two files; the forbidden pattern has a space and the files do not |
| **B3-02** | `U-BREATH`, `BREATH` | **high** | The retired 4.7 V sensor full scale is live in **five** places, in four spellings — including the owner ADR and the sensor's own BOM row |
| **B3-03** | `C-KEY`, `R-KEY-SER` | **med-high** | BOM fragment carries `~5.7us` / `~125us` / `44x` against the owner page's 5.92 / 119.9 / 42× |
| **B3-04** | `D1`/`D2` power entry | **med-high** | `r_d 69 mΩ at 392 mA` is contradicted by the same banked curve (≈335 mΩ) and by the figure's own 120 mV chord |
| **B3-05** | `GATE`, the load-switch FET | **med** | The LT1641 guarantees only **4.5 V** of gate drive at 12 V `V_CC`; absent from the page's verification table and from the FET criteria |
| **B3-06** | `U-KEYS` `V_IH`/`V_IL` | **med** | "the 3.0 V row is the family's, not one vendor's" — Nexperia and Toshiba **have no 3.0 V row**; only onsemi does |

Plus eleven lower-severity condition/citation findings (B3-07 … B3-17) and two
informational notes.

---

## Part 1 — Findings

### B3-01 · Node `U-DIFFRX` output / `BREATH` — `-9.6V` is live, and the forbidden pattern cannot see it

`config/figures.yaml` `inamp-full-scale` is **−9.94 V**, `status: settled`, and
its forbidden list is `["-9.6 V", "−9.6 V", "-10.05 V", "−10.05 V"]` with the
note *"-9.6 V is derived from nothing and matches no configuration"*
`[repo] config/figures.yaml:27-32`.

Live in the corpus:

- `[repo] hardware/bom.csv:103` (`U-DIFFRX`) — *"Output is 0V at rest to
  **-9.6V** at full (Vout = -2.185*(V_BREATH - V_AGND) + V_REF …)"*
- `[repo] hardware/unplaced.csv:15` — the same row, same text. **This is the
  fragment**: `hardware/unplaced.csv` is in `merge-bom.py`'s `ORDER`
  `[repo] tools/merge-bom.py:69`, and no per-circuit fragment carries `U-DIFFRX`
  (checked all 24). So the fix lands in `unplaced.csv`, then `merge-bom.py`.

**Why it escaped.** Exhaustive string search over the design corpus: `"-9.6 V"`
and `"−9.6 V"` occur **only inside `config/figures.yaml` itself**; the two live
instances are spelled `-9.6V`, no space. `tools/check-staleness.py` reports
`PASS no live stale values` `[repo] .staleness-report.txt`.

**Second defect in the same sentence.** The row's own formula `-2.185 × (…)` is
the *raw* in-amp gain. `inamp-full-scale`'s derivation is the **effective** gain
2.16106 (raw 2.18483 × the 1M/(1M+11k) bias divider). `[calc]` raw gain × the
4.599 V span = −10.05 V — which is the *other* forbidden value. So the row's
formula and the row's stated result disagree with each other **and** both
disagree with the register. The gain equation itself is right:
`[datasheet datasheets/analog/INA828IDR.pdf p.5]` *"1 + (50 kΩ / RG)"*, and
`[calc]` 1 + 50000/42200 = 2.184834.

**Fix lands at:** `hardware/unplaced.csv:15`, then re-run `tools/merge-bom.py`.
Add `"-9.6V"` and `"−9.6V"` (no space) to the forbidden list.

---

### B3-02 · Node `U-BREATH` / `BREATH` — the retired 4.7 V full scale is live in five places, in four spellings

`sensor-full-scale` is **4.86 V**, owner `docs/decisions/0003-breath-sensing-path.md`,
with a 26-entry forbidden list and *two* escape notes recording that this exact
figure has already escaped a forbidden list four and five times
`[repo] config/figures.yaml:34-90`.

**First, what the document actually says.** Re-read against the banked PDF:

| Claim | Verdict |
|---|---|
| `Vout = VS*[(0.1533*P) + 0.053]` | **CONFIRMED verbatim, twice** `[datasheet datasheets/analog/MPXV4006DP.pdf p.5]`, once at ±5.0 % VFSS and once at ±2.46 % VFSS |
| 4.864 V at VS = 5.0 V, P = 6 kPa | `[calc]` 5 × (0.9198 + 0.053) = **4.864 V** ✓ |
| Pedestal 0.265 V | **CONFIRMED** — Table 1 `Voff` 0.152 / **0.265** / 0.378 V `[datasheet … p.3]`; also 5 × 0.053 = 0.265 `[calc]` |
| `VFSS` 4.6 V typ | **CONFIRMED** Table 1 `[datasheet … p.3]` |
| Sensitivity 766 mV/kPa | **CONFIRMED** Table 1 `[datasheet … p.3]` |
| The cover-page line | It reads **"0.2 to 4.8 V Output"** `[datasheet … p.1]` — **4.8, not 4.7** |

That last row matters: **`0.2–4.7 V` matches nothing in the document at all** —
not the transfer function, not the cover page. It is a third value.

**Live instances** (exhaustive string search of `hardware/**`,
`docs/decisions/**`, `docs/reference/**`, `config/**`, `firmware/**`,
`README.md`, `ROADMAP.md`):

1. `[repo] docs/decisions/0005-power-architecture.md:74` — *"The MPXV4006DP is a
   5 V part outputting **0.2–4.7 V** (ADR 0003)."* Byte check: the dash is
   **U+2013 EN DASH with no surrounding spaces**. The forbidden list holds
   `"0.2-4.7 V"` (hyphen) and `"0.2 – 4.7 V"` (en dash **with** spaces). This is
   verbatim the escape shape `escape_note` describes — *"an en dash with no
   spaces"* — **still live, in a file the note never looked at.** It also cites
   ADR 0003 by name while contradicting it.
2. `[repo] docs/decisions/0003-breath-sensing-path.md:565` — *"The sensor reaches
   4.7 V while the ADC runs on 3.3 V"*. **This is the owner document**, and line
   560 of the same file correctly says *"full scale, 0.265–4.86 V"*. Five lines
   apart. (`escape_note_2` already records the fifth instance being in the owner
   document; this is a sixth.)
3. `[repo] hardware/bom.csv:41` + fragment
   `[repo] hardware/interfaces/breath-sense-link/bom.csv:2` — `U-BREATH`, the
   sensor's own row: *"identical transfer function (766mV/kPa, **0.2-4.7V**)"*.
   The worst-placed one: the fitted part's row calls the refuted pair "the
   transfer function". (766 mV/kPa is right; only the range is wrong.)
4. `[repo] hardware/bom.csv:20` + fragment
   `[repo] hardware/carrier/breath-adc/bom.csv:4` — `R-ADCDIV`: *"Sensor reaches
   **4.7V** into a 3V3 ADC"*, while the page that sizes the divider has it right:
   *"full scale = 4.86 V × 0.6 = 2.92 V"* `[repo] hardware/carrier/breath-adc/breath-adc.md:35`.
5. `[repo] hardware/bom.csv:43` + fragment
   `[repo] hardware/interfaces/breath-sense-link/bom.csv:4` — `D-TVS-BREATH`:
   *"BREATH's normal top of range is **4.7V** against a 5V array's V_RWM - **300mV
   of margin**"*. The margin is **derived from the stale value**: `[calc]`
   5.00 − 4.86 = **0.14 V**, not 0.30 V. The row's conclusion (use a 12 V
   standoff, not 5 V) gets *stronger*, so nothing breaks — but a derived number
   is wrong by 2.1×.

**Not defects** (different quantities, checked): `~4.7 V` at the dev-board 5 V
pins after a Schottky `[repo] hardware/bom.csv:7`; `~4.7 V` delivered rail on a
hypothetical 5 V umbilical `[repo] docs/decisions/0005-power-architecture.md:96,99`;
`−4.7 V` at the in-amp for a ~3 kPa blow `[repo] hardware/module/breath-receive-stage/breath-receive-stage.md:126,194`
and `[repo] hardware/module/breath-output-stage/breath-output-stage.md:43,59`.

**Fix lands at:** the two ADRs directly; `hardware/interfaces/breath-sense-link/bom.csv`
lines 2 and 4 and `hardware/carrier/breath-adc/bom.csv:4`, then re-run
`tools/merge-bom.py`. Add `"0.2–4.7 V"` (en dash, no spaces), `"0.2-4.7V"`,
`"reaches 4.7 V"` and `"is 4.7V"` to the forbidden list. **Per CLAUDE.md §2,
grep for the old value before writing those patterns — that is how the four
spellings above were found.**

---

### B3-03 · Node `C-KEY` / `R-KEY-SER` — the BOM fragment carries the pre-correction key timings

`key-release-time` = **119.9 µs**, `key-press-time` = **5.92 µs**, and
`key-press-time`'s `conservative_bound` says *"Margin inside the 250 us scan is
42x at 5.92 us"* `[repo] config/figures.yaml:149-170`. The owner page agrees:
*"crosses `V_IH` at **119.9 µs**"*, *"crosses `V_IL` at **5.92 µs** — 42× inside
the 250 µs scan"* `[repo] hardware/cluster/key-switch-network/key-switch-network.md:102-103`.

Live in the BOM:

- `[repo] hardware/cluster/key-switch-network/bom.csv:5` (`C-KEY`, mirrored to
  `hardware/bom.csv:36`) — *"Press crosses HC165's VIL (0.99V at 3.3V) in
  **~5.7us**, so 'press is instant' survives - **44x margin** against the 250us
  scan period. Release crosses VIH (2.31V) at **~125us**."*
  All three numbers are the superseded ones. `[calc]` 250/5.7 = 43.9 ≈ 44, so the
  margin figure is derived from the stale crossing time. The register's own note
  says 125 µs *"is the error the 125 us figure came from"* (starting the
  exponential from 0 V instead of the 0.1435 V divider node).
  **The thresholds in the same sentence are correct** (0.99 V / 2.31 V), which is
  the confusing part: right datasheet reading, wrong arithmetic downstream.
- `[repo] hardware/cluster/key-switch-network/bom.csv:4` (`R-KEY-SER`, mirrored
  to `hardware/bom.csv:35`) — *"press is ~1us (100R x 10nF) … release is **~93us**
  (10k x 10nF)"*. This describes the **superseded 10 k / 10 nF network**
  (`R-KEY-PU` is 2k2, `C-KEY` is 47 nF) as live fact, and `93 us` is a forbidden
  value.

**Why they escaped.** The forbidden patterns are markdown-spelled —
`` "`V_IH` at **125" ``, `` "`V_IL` at **5.7" ``, `"release ~93 us"` — and occur
only inside `figures.yaml`. The CSV spells them `at ~125us`, `in ~5.7us`,
`release is ~93us`.

**Arithmetic re-derived independently, both correct in the register:**
`[calc]` τ_release = 2200 × 47 n = 103.40 µs; t = −103.40·ln((3.3−2.31)/(3.3−0.1435)) = **119.87 µs**.
`[calc]` τ_press = (2200∥100) × 47 n = 95.652 × 47 n = 4.4957 µs;
t = −4.4957·ln((0.99−0.1435)/(3.3−0.1435)) = **5.917 µs**.

**Fix lands at:** `hardware/cluster/key-switch-network/bom.csv` lines 4 and 5,
then `tools/merge-bom.py`.

---

### B3-04 · Node `D1`/`D2` (module power entry) — `r_d = 69 mΩ at 392 mA` is refuted by the curve it is attributed to

`diode-split-rationale`'s **value** field is
*"fault isolation and HF isolation (**r_d 69 mohm at 392 mA**)"*
`[repo] config/figures.yaml:469`, restated as live fact at
`[repo] hardware/module/power-entry/power-entry.md:112-113`, where the `69 mΩ`
carries **no provenance mark** (the `[repo, digitised from Fig. 2 …]` tag two
paragraphs up attaches to the 120 mV claim, not to this one).

**The 120 mV claim is confirmed.** I digitised the 1N5817 trace of Fig. 2 from
the PDF's Bézier control points against the extracted gridlines
`[datasheet datasheets/discrete-and-power/1N5817.pdf p.2]`:

| I_F | corpus | B3 independent digitisation |
|---|---|---|
| 1.0 A | 0.454 V | **0.468 V** (spec max 0.450 V `[datasheet … p.1]`) |
| 3.0 A | 0.746 V | **0.763 V** (spec max 0.750 V `[datasheet … p.1]`) |
| 245 mA → 612 mA | 0.24 → 0.36 V, **Δ = 120 mV** | 0.256 → 0.375 V, **Δ = 119.9 mV** |

The Δ — the quantity the argument uses — reproduces to 0.1 mV. The corpus's
calibration claim ("good to about ±0.01 V", "the plotted curve sits essentially
on the max spec") is **confirmed**.

**The 69 mΩ does not.** From the same digitisation `[calc]`:
`dV/dI` at 392 mA = (V(412 mA) − V(372 mA))/40 mA = **335 mΩ**. The corpus's own
chord agrees with me and not with itself: `[calc]` 120 mV / (612 − 245) mA =
**327 mΩ**. **69 mΩ is 4.8× low**, and it is the `value` field of the entry whose
`derivation` field implies 327 mΩ.

69 mΩ looks like the *ideal-diode* small-signal resistance: `[calc]`
n·kT/qI at n = 1.05, I = 392 mA = 69 mΩ. That is a textbook expression, not a
number off this curve — a real Schottky at 392 mA is dominated by series
resistance, which is why the plotted slope is ~5× higher.

**Consequence:** the "HF isolation" argument for keeping two diodes is weaker by
~5× than stated (a bigger `r_d` is *better* isolation, so the conclusion —
*keep both diodes* — survives and in fact strengthens). But the figure is wrong
and it is in the `value` field, so anything that cites `diode-split-rationale`
inherits it.

**Conditions not stated**: Fig. 2 is labelled `T_j = 25 °C, Pulse Width =
300 ms, 2 % Duty Cycle` `[datasheet … p.2]`, and the V_FM table entries carry
Note 2, *"Short duration test pulse used to minimize self-heating effect"*
`[datasheet … p.1]`. Neither condition appears in the corpus.

---

### B3-05 · Node `GATE` / the load-switch N-FET — the 4.5 V gate-drive limit at 12 V is not in the corpus

`hardware/module/umbilical-load-switch/umbilical-load-switch.md:126-141` is a
twelve-row table headed *"The electrical picture, now read off the document"*.
**I re-verified every row against the banked PDF and all twelve are correct**
(see Part 2). One parameter is missing from it, and it is the one that differs
between ADI's circuit and this one:

> *"An internal charge pump guarantees at least 10V of gate drive for supply
> voltages above 20V and **4.5V gate drive for supply voltages between 10.8V and
> 20V**."* `[datasheet datasheets/discrete-and-power/LT1641.pdf p.5]`

and in the EC table: `ΔV_GATE` (External N-Channel Gate Drive, `V_GATE − V_CC`)
= **4.5 min / 18 max V** at `V_CC = 10.8 V to 20 V`; 10 min / 18 max at
`V_CC = 20 V to 80 V` `[datasheet … p.2]`.

The module runs from **+12 V**, so the guaranteed gate drive is **4.5 V, not
10 V**. The FET must be fully enhanced at `V_GS = 4.5 V` while carrying ~1 A.
The page's "What sizes the FET" section names single-pulse SOA, Spirito/linear-
mode derating and dismisses `R_DS(on)` as *"irrelevant at 360 mA"*
`[repo] hardware/module/umbilical-load-switch/umbilical-load-switch.md:316-327` —
it never mentions gate drive, and `R_DS(on)` is *not* irrelevant at
`V_GS = 4.5 V` for a standard-threshold part.

**Why this is the §3 failure mode exactly.** The page copies `R-GATE-SER 10 Ω`
and the ON-pin divider form *from ADI's Figure 5*
`[repo] hardware/module/umbilical-load-switch/umbilical-load-switch.md:289,341`,
and Figure 5 is drawn at **`VIN = 24 V`** with an IRF530
`[datasheet … p.8]` — i.e. in the regime where 10 V of drive is guaranteed. The
one parameter that changes between 24 V and 12 V is the one not carried across.

**Recommend:** add a `ΔV_GATE 4.5 V min @ V_CC 10.8–20 V [164112fc p.2, p.5]`
row to that table, and add "fully enhanced at V_GS = 4.5 V" to the `U-LOADSW`
FET criteria in `hardware/module/umbilical-load-switch/bom.csv`.

---

### B3-06 · Node `U-KEYS` input thresholds — "the 3.0 V row is the family's" is not supported by the three documents cited for it

`key-release-time.threshold_note` says:

> *"TI, Nexperia (Rev. 8) and Toshiba agree with onsemi digit for digit at every
> shared rail, **so the 3.0 V row is the family's, not one vendor's.** All four
> PDFs are banked."* `[repo] config/figures.yaml:153`

What the four banked documents actually tabulate:

| Document | `V_CC` rows tabulated | 3.0 V row? |
|---|---|---|
| onsemi MC74HC165A Rev. 13 (Apr 2025) p.4 | 2.0 / **3.0** / 4.5 / 6.0 | **yes** — `V_IH` 1.5/**2.1**/3.15/4.2, `V_IL` 0.5/**0.9**/1.35/1.80 |
| TI SCLS116E p.4 (rec. op. cond.) | 2 / 4.5 / 6 | **no** |
| Nexperia 74HC165 Rev. 8 (9 May 2025) | 2.0 / 4.5 / 6.0 | **no** |
| Toshiba TC74HC165P/F, 1986 excerpt | 2.0 / 4.5 / 6.0 | **no** |

`[datasheet datasheets/logic/74HC165-onsemi.pdf p.4]`,
`[datasheet datasheets/logic/74HC165-ti-scls116e.pdf p.4]`,
`[datasheet datasheets/logic/74HC165-nexperia.pdf]`,
`[datasheet datasheets/logic/74HC165-toshiba-1986-excerpt.pdf]`.

The **first half** of the sentence is true and I verified it digit for digit:
all four give 1.5/3.15/4.2 and 0.5/1.35/1.80 at 2.0/4.5/6.0 V. The **inference**
does not follow. Agreement at three shared rails shows they share the JEDEC HC
family limits at *those* rails; it is no evidence that Nexperia, Toshiba or TI
would *guarantee* 0.70/0.30 at 3.0 V. Only onsemi publishes that row.

**Why it bites.** `[repo] hardware/bom.csv:31` specifies `U-KEYS` as
`74HC165, manufacturer "multiple"`. The `conservative_bound` field names TI as
the one exception — *"If a TI SN74HC165 is the part fitted, its own datasheet
guarantees nothing at 3.3 V"* — when in fact **three of the four banked vendors
guarantee nothing at 3.3 V.** Nothing in the design breaks (42× / 36× margin is
the same answer either way, and the page says so), but the sentence as written
would let a future reader assume any 74HC165 is covered.

**Also:** `datasheets/README.md` lists the Toshiba excerpt as one of three
**surrogates** that *"must never be cited as the fitted part's datasheet"*. It is
cited here as corroborating evidence. That use is defensible — it is a bracket,
and `U-KEYS` names no vendor — but it is not labelled as a bracket at the point
of use, which is what §3 of my charter asks about.

**Recommend:** restate as *"only onsemi's MC74HC165A publishes a 3.0 V row; TI,
Nexperia and Toshiba tabulate 2.0/4.5/6.0 only and agree with onsemi at all
three. 2.31 V is therefore an onsemi-guaranteed interpolation, not a family
guarantee."* The interpolation itself is sound and correctly done:
`[repo] hardware/cluster/key-switch-network/key-switch-network.md:74-75`
`V_IH(3.3) = 2.1 + (0.3/1.5)(3.15−2.1) = 2.31 V` `[calc]` ✓, which equals
0.70 × 3.3 exactly.

---

### B3-07 · Node `VS` / `R-ISO-REF` — TI's Figure 56 text explicitly forbids the transfer the corpus makes

`riso-ref-topology` asserts *"IT TRANSFERS TO OUR 100 nF LOAD BECAUSE R_ISO IS
SET BY Zo, NOT BY C_L"* `[repo] config/figures.yaml:402`, repeated at
`[repo] hardware/bom.csv:14`.

**Figure 56 itself is confirmed verbatim**: `R_F` 1 MΩ, `C_L` 10 µF, `R_ISO`
37.4 Ω, `R_Fx` 10 kΩ, `C_F` 39 nF, *"loop gain phase margin of 89°"*, closed-loop
bandwidth 4 kHz `[datasheet datasheets/analog/OPA2197.pdf p.30, section 8.2.3]`.

But the same paragraph ends:

> *"**Any other load capacitances require recalculation of the stability
> components: RF, RFx, CF, and RISO.**"* `[datasheet … p.30]`

The corpus does not quote or acknowledge that sentence anywhere. Its own
analysis (the pole-zero cancellation argument, the 85.9°/896 kHz simulation, and
the model validated at 87.4° against TI's printed 89°) may well be right — it is
a real derivation, not an assertion — but a claim of the form *"TI's worked
answer transfers"* should say that TI's text says it does not, and defend the
transfer against that.

Minor, same node: *"37.4 ohm is Zo/10"* `[repo] config/figures.yaml:402` —
`[calc]` 375/10 = 37.5; 37.4 is the E96 neighbour. TI gives no Zo/10 rule
anywhere in SBOS737C; the rationalisation is the corpus's own and is not marked
as such.

---

### B3-08 · Node `VS` / `U-BUF` — `Zo = 375 Ω` is the mid-band plateau, not the 1 MHz value TI's own row attaches it to

`opa2197-output-impedance` = **375 Ω**, quoted verbatim from the EC row
*"ZO Open-loop output impedance | f = 1 MHz, IO = 0 A, See Figure 26 | 375 | ohm"*
`[repo] config/figures.yaml:507-510`. **The row is confirmed**, and it appears on
**both** pages the corpus cites: p.8 (the `V_S = ±4 V to ±18 V` table) and p.10
(the `V_S = ±2.25 V to ±4 V` table) `[datasheet datasheets/analog/OPA2197.pdf p.8, p.10]`.

I digitised Figure 26 `[datasheet … p.16]` against its decade gridlines:

| f | corpus | B3 |
|---|---|---|
| 0.1 Hz | ~3.26 kΩ | ~3 kΩ (off-scale top, consistent) |
| 10 Hz | 482 Ω | **≈485 Ω** |
| plateau | "375 from 100 Hz to 300 kHz" | **≈377 Ω, from ≈35 Hz to ≈300 kHz** |
| 1 MHz | 301 Ω | **≈313 Ω** |
| 10 MHz | ~73 Ω | **≈74 Ω** |

**The digitisation is excellent.** The problem is TI's: **the EC row's stated
test condition (`f = 1 MHz`) is where Figure 26 reads ~310 Ω, not 375 Ω.** 375 Ω
is the plateau. The corpus quotes both numbers, three lines apart, without
noticing they are inconsistent — and then uses 375 Ω as the Zo for a
compensation problem whose simulated crossover is **896 kHz**
`[repo] config/figures.yaml:402`, i.e. inside the roll-off, where Figure 26 gives
~315 Ω.

**Consequence is small** (`R_ISO/Zo` moves from 0.0997 to 0.119, worth a degree
or so of phase margin, and the `robustness` field already claims >76° across
TI's whole published Zo range 73 Ω–3.26 kΩ). But the figure's `quantity` field
says "OPA2197 open-loop output impedance" unconditionally, and it is not
unconditional: it is 375 Ω from ~35 Hz to ~300 kHz, 3.3 kΩ at 0.1 Hz, and 74 Ω
at 10 MHz. Add the band to the `value` or the `quantity`.

*(This also vindicates the corpus's own note that the old back-solved 75.8 Ω "is
roughly the 10 MHz value" — my digitisation gives 74 Ω there.)*

---

### B3-09 · Page citation — OPA2197 PSRR is SBOS737C **p.7**, not p.8

`±1 µV/V typ / ±3 µV/V max`, `T_A = −40 °C to +125 °C`, is on **page 7**
`[datasheet datasheets/analog/OPA2197.pdf p.7]` (the `V_S = ±4 V to ±18 V` EC
table begins on p.7 and continues on p.8; PSRR is in the OFFSET VOLTAGE block on
p.7, and the second copy is on p.9 in the low-voltage table). **Page 8 carries no
PSRR row.**

Cited as p.8 in three places: `[repo] config/figures.yaml:471`,
`[repo] hardware/module/power-entry/power-entry.md:101`, and the
`U-BUF` / `U-OPA-PITCH` / `U-RESP` notes `[repo] hardware/bom.csv:12,67,76`.

The **values** are confirmed exactly, and the corpus's derived `110.5 dB worst
case` is right `[calc]` 20·log10(1/3e-6) = 110.46 dB. Only the page is wrong.

*(By contrast `cref-out-node`'s citation of `I_B ±5 pA typ, ±20 pA max at 25 °C`
to **p.7** is correct `[datasheet … p.7]`, as is `riso-ref-topology`'s
over-temperature `I_B` of `±5 nA` — and the SOIC-8 `D` package is the right one,
since the `±15 nA` row is marked "PW package only" and `U-BUF` is `OPA2197IDR`
`[repo] hardware/bom.csv:12`.)*

---

### B3-10 · Node `AVDD` — the LM317 line regulation in the pitch chain is a typical, in a chain that claims to use guaranteed maxima

`diode-split-rationale` computes `120 mV → LM317 line reg (0.52 mV/V) → 62 µV on
AVDD → OPA2197 PSRR → 0.00044 cents` `[repo] config/figures.yaml:469`, and its
`provenance_note` makes a point of having replaced the PSRR typical with the
**guaranteed maximum**: *"Using the guaranteed maximum scales the result by
1.50x"*.

The LM317L datasheet gives **Input voltage regulation** as a percentage of `V_O`
per volt of input change:

| condition | typ | max |
|---|---|---|
| `T_J = 25 °C` | 0.01 %/V | 0.02 %/V |
| `I_O = 2.5 mA to 100 mA` | 0.02 %/V | **0.05 %/V** |

`[datasheet datasheets/discrete-and-power/LM317LZ.pdf p.4]` (SLCS144E). Footnote:
*"Input voltage regulation is expressed here as the percentage change in output
voltage per 1-V change at the input."*

`[calc]` At `V_O = 5.21 V`: 0.01 %/V → **0.521 mV/V**. So the corpus's 0.52 mV/V
is the **typical at `T_J = 25 °C`**. The guaranteed maximum over the load range
is 0.05 %/V = **2.6 mV/V**, 5× worse — which would take the chain from 0.00044 to
**0.0022 cents** `[calc]`. Still five orders of magnitude below every other term,
so **nothing changes**; but the one link in the chain that is a typical is the
one the provenance note does not mention.

*(Other LM317L claims confirmed: reference 1.20 / 1.25 / 1.30 V; ripple
regulation 65 dB typ, **66 min / 80 typ with a 10 µF ADJUSTMENT capacitor** —
`[repo] hardware/bom.csv:112` quotes this exactly; peak output current 100 mA
typ; minimum load 1.5 typ / 2.5 max mA against the row's ~13 mA
`[datasheet … p.4]`.)*

---

### B3-11 · Node `U-REF` — `ref5050-grade` enumerates two grades; the table it cites has three

`ref5050-grade` is `DISPUTED` with `candidates: [REF5050AIDR = Standard, REF5050IDR = High]`
and `decided_by: "Changing one letter in the order code"`
`[repo] config/figures.yaml:537-545`.

**Table 4-2 is confirmed verbatim** and the corpus's headline finding is right —
*the "A" suffix is the worse grade*:

| Device | Grade | Tempco | Initial accuracy | Noise | V_IN max | I_Q max |
|---|---|---|---|---|---|---|
| REF50xx**EI** | Enhanced | 2.5 ppm/°C | ±0.025 % | 0.5 µV_PP/V | 42 V | 480 µA |
| REF50xx**I** | High | 3 ppm/°C | ±0.05 % | 3 µV_PP/V | 18 V | 1.2 mA |
| REF50xx**AI** | Standard | 8 ppm/°C | ±0.1 % | 3 µV_PP/V | 18 V | 1.2 mA |

`[datasheet datasheets/analog/REF5050.pdf p.3, Table 4-2]`

The **Enhanced** grade is in the same table the entry cites, is better on every
axis relevant to the stated purpose (ratiometric scale-factor stability), and is
available in the same SOIC-8 as **REF5050EID** `[datasheet … p.3, Table 4-1]`.
It costs the same "one letter in the order code". A disputed entry that
enumerates two of three published options will be decided between two of three.

**Recommend:** add REF5050EID as a third candidate.

---

### B3-12 · Node REF5050 `VOUT` — the cited bullet asks for 1 µF; the corpus allocates 100 nF

`C-DECOUPLE-CARRIER` went qty 7 → 8 on the strength of:

> *"SBOS410O section 9.4.1.1 pp.29-30 wants both: a VIN bypass AND 'a
> high-frequency, **1uF** capacitor in parallel between the output and ground'"*
> `[repo] hardware/bom.csv:22`

**The quote is exact** and the page range is right — the bullet list of
§9.4.1.1 begins on p.29 and this bullet falls on p.30
`[datasheet datasheets/analog/REF5050.pdf p.30]`. But `C-DECOUPLE-CARRIER` is a
**100 nF** part, and the settled allocation puts one of them at REF5050 VOUT
`[repo] config/figures.yaml:386`. The row cites a 1 µF requirement and fits
100 nF — 10× under — without noting the difference.

In practice 100 nF alongside `C-REF-OUT`'s 10 µF is ordinary, and §8.4.1's hard
requirement (*"Confirm that a output capacitor (CL) is connected from VOUT to
GND … ESR ≤ 1.5 Ω"*, `C_L` = 1 µF to 50 µF for REF50xxI/AI, Figure 8-6) is met by
the 10 µF. **Both of those are confirmed verbatim** `[datasheet … p.26, §8.4.1]`,
as is §9.4.1.1's *"A resistor in series with the output capacitor is optional"*
`[datasheet … p.29]` and the 0.9 µV_rms/V, 10 Hz–1 kHz output noise
`[datasheet … p.7]` behind the corpus's 4.5 µV_rms `[calc]` 0.9 × 5.000.
So this is a wording defect, not a design defect — but the row currently reads
as if the 100 nF satisfies a 1 µF instruction.

---

### B3-13 · Node `PLATE-TOP` — the vendor's *plate* tolerance is +0.01/−0.05, not ±0.05

`plate-thickness` = **1.20 mm**, derivation: *"Sheet 6's elevation dimensions the
plate slot 1.20 +/-0.05 mm; sheet 3 section 8 shows the same 1.20 against a
hatched plate section"* `[repo] config/figures.yaml:498-501`.

**Both citations check out**, and I was wrong to doubt the second one on a first
pass. Rendered at 150–900 dpi (the sheet is vector, `pdftotext` returns nothing
numeric — confirmed, no `1.2` anywhere in the text layer):

- PDF page 6, the KS-33H10B050NN-Y24 drawing sheet, **Version 2, drafted
  2023-01-03** (all confirmed in the title block): the left elevation dimensions
  the switch's plate slot **1.20 ± 0.05**, alongside 13.75, 5.75±0.05,
  2.50±0.05, **14.00 ± 0.05**, 14.70, Ø1.00.
  `[datasheet datasheets/mechanical/GATERON-KS-33-VENDOR-SPEC-DRAWING.pdf p.6]`
- PDF page 3, **§8 "Mounting Options: The suggestion dimension of mounting"**,
  hatched plate section: **14.00 +0.05/−0.02** square and **1.20 +0.01/−0.05** on
  the plate section, with Ø5.25, 2.60, 4.40, 0.90, 5.00, 1.80, 2.25, 4.70, 2.00,
  5.75, 6.30. `[datasheet … p.3, §8]`

**So `"Cutout confirmed and tightened to 14.00 +0.05/-0.02 square"` is exactly
right** — it comes off §8, not off the elevation.

**The one real discrepancy:** the entry's note computes the acceptance window
from the **±0.05 slot** tolerance — *"1.5 mm is 0.25 mm over the upper limit"*
(→ upper limit 1.25) and *"1.10 mm is 0.05 mm under the lower limit"* (→ lower
limit 1.15) `[repo] config/figures.yaml:503`. But §8's **plate** recommendation
is 1.20 **+0.01/−0.05** = **1.15 to 1.21 mm**. The ±0.05 belongs to the slot in
the switch (1.15–1.25), which is the clearance, not the plate. A 1.25 mm plate
would be at zero clearance against a minimum slot. The conclusion (both
candidates are outside the window; 1.20 is the answer) is unaffected; the stated
upper limit should be **1.21 mm**, from the sheet that section 8 is on.

---

### B3-14 · Node `PANEL` / `SW-POWER` — every NKK number is right; the "no text layer" claim is not

`panel-toggle-hole` = *"6.5 mm diameter with a 5.8 mm D-flat … read off
datasheets/connectors/NKK-SERIES-M-TOGGLE.pdf, **rendered at 150 dpi because the
drawing is vector with no text layer**"* `[repo] config/figures.yaml:307-311`.

**All the values are confirmed** (I rendered p.7 at 170 dpi to read the cutouts):

| Claim | Verdict `[datasheet datasheets/connectors/NKK-SERIES-M-TOGGLE.pdf p.7]` |
|---|---|
| Bushing is M6×0.75 | **CONFIRMED** — D4 = "6mm/.350" (8.9mm) Threaded with D Flat", callout `M6 P0.75` |
| 6.5 mm hole, 5.8 mm D-flat | **CONFIRMED** — panel cutout "For D1, D4, D3 or D8 Bushing with D Flat": `(6.5) Dia .256` and `(5.8) .228` |
| Thread length 8.9 mm | **CONFIRMED** — `(8.9) .350` |
| Max panel thickness 2.6 mm | **CONFIRMED** — *"Maximum Panel Thickness with Standard Hardware: .102" (2.6mm)"* |
| 2 mm panel leaves 6.9 mm of thread | `[calc]` 8.9 − 2.0 = 6.9 ✓ |
| No plain round option in the metric range | **CONFIRMED** — metric options are S4 (keyway), D4 and D8 (D flat) only |
| S4 with locking ring: 2.2 mm hole at 6.5 mm centres | **CONFIRMED** — `(2.2) Dia .087` |
| Lever 10.5 mm at a **25°** throw (in `panel-height-budget`) | **CONFIRMED** — *"Angle of Throw: 25°"* `[datasheet … p.1]` |

**But the PDF has a complete text layer** carrying every one of those callouts
(1 000–3 600 characters per page; `M6 P0.75`, `(6.5) Dia`, `(5.8)`, `.102" (2.6mm)`
all extract as text). Cosmetic, but the provenance sentence is a statement about
the artefact and it is wrong, and it is the kind of statement a later agent will
rely on when deciding whether re-reading is cheap.

Minor: the entry attributes both the 5.6 mm flat and the 2.2 mm anti-rotation
hole to "the S4 keyway option … if the locking ring is used instead". The sheet
shows these as **two different S4 cutouts** — one for the keyway (with a flat)
and one for the locking ring (with the 2.2 mm hole).

---

### B3-15 · `datasheets/README.md` — the SP0504BAHT framing is superseded by its own BOM row

`datasheets/README.md` says:

> *"**SP0504BAHT** — banked, and it settled the power question by **not having
> one**: there is no peak-pulse-power spec in the document at all, so the 0.98 W
> figure is **unsourceable rather than merely wrong**."*

`hardware/bom.csv:46` / `hardware/interfaces/spi-link/bom.csv:4` explicitly
corrects that, and logs the correction: *"CORRECTION LOGGED 2026-09-21 - the
superseded sentence claimed this part 'specifies no steady-state or pulse power
either', which contradicted the 0.225 W it cited in the same clause"*.

**The BOM row is right and the README is not.** Verified:

- **Absolute Maximum Ratings, Package Power Dissipation: SOT23-3, SOT23-5,
  SOT23-6, SOT143 → 0.225 W** `[datasheet datasheets/discrete-and-power/SP0504BAHT.pdf p.2]`,
  corroborated `PD@70degC .225W` `[datasheet … p.7]`. So 0.98 W is **refuted by a
  sourced number 4.4× lower**, not unsourceable.
- **No pulse rating**: the string "power" occurs exactly twice in all 8 pages —
  the title and that Abs Max row. No `I_PP`, no 8/20 µs, no surge curve. The
  README's "no peak-pulse-power spec" half is true.
- `SP0504BAHTG | 4 CH | SOT23-5` **CONFIRMED** `[datasheet … p.1, p.6]`.
- *"Low Input Capacitance … 30pF Typical"* **CONFIRMED** `[datasheet … p.1]`.
- ESD level IEC 61000-4-2 20 kV contact / 30 kV air **CONFIRMED** `[datasheet … p.1]`.

This is the named failure mode with the polarity reversed: the fix landed
thoroughly in the BOM row, and **the entry point a reader hits first still
carries the superseded sentence**. `datasheets/README.md` is outside the checked
corpus (CLAUDE.md §6 lists root `README.md`, not this one), so no tool can catch
it.

---

### B3-16 · Node `J-LED-L`/`J-LED-R` — "~4.4 V minimum" is the quiet-output *dynamic* `V_OH`

`hardware/carrier/led-strip-drive/led-strip-drive.md:65-69` says the 74AHCT125 at
5 V *"delivers ~4.4 V minimum"* into a `V_IH` of 3.15–3.85 V.

4.4 V is **`V_OH(V)`, "Quiet output, minimum dynamic V_OH"**, and it sits under a
note reading *"Characteristics are for surface-mount packages only"*
`[datasheet datasheets/logic/SN74AHCT125.pdf p.4]`. The **DC** `V_OH` minimum is
**3.80 V** at `I_OH = −8 mA, V_CC = 4.5 V` `[datasheet … p.3]`.

Against a worst-case `V_IH` of 3.85 V (0.7 × 5.5 V) that DC minimum would be
*negative* margin on paper. In reality the margin is large and the conclusion
holds, for two reasons worth writing down rather than leaving implicit:
(1) the WS2815 logic `VDD` and the 74AHCT125 `V_CC` are the **same 5 V rail**, so
`V_IH = 0.7·V_CC` and `V_OH` track together; (2) the WS2815 `DIN` input current
is **±1 µA max** `[datasheet datasheets/led/WS2815.pdf p.3]`, not 8 mA, so `V_OH`
is within millivolts of the rail. Say that, rather than quoting a dynamic figure
as a minimum.

*(`V_IH = 2 V / V_IL = 0.8 V` TTL thresholds **CONFIRMED** `[datasheet … p.3]`, so
"3V3 reads high" is right.)*

---

### B3-17 · Node `E1` matrix supply — `V_F ≈ 0.46 V` for the B5819WS is an assumption, and it is the optimistic direction

`matrix-led-current.supersedes_the_constraint` derives *"~435 mA at 25 °C and
~283 mA at a 60 °C interior `[calc at V_F ~0.46 V]`"* `[repo] config/figures.yaml:526`.

**The ratings are confirmed exactly**: SOD-323, `I_F(AV)` 1 A, **`P_D` 200 mW**
(Note 2: device mounted on FR4 with the recommended pad layout), **`R_θJA`
500 °C/W**, `T_J` max +125 °C
`[datasheet datasheets/discrete-and-power/B5819WS.pdf p.2]`. The arithmetic is
right: `[calc]` (125−25)/500 = 200 mW → 200/0.46 = 435 mA; (125−60)/500 = 130 mW
→ 130/0.46 = 283 mA.

The `V_F ≈ 0.46 V` is flagged as an assumption, correctly, but it is **not the
datasheet number**: the B5819WS's specified `V_F` is **0.60 V max at 1 A**
`[datasheet … p.2]`. Using the specified value gives `[calc]` **333 mA at 25 °C
and 217 mA at 60 °C** — *lower*, so the argument that the Schottky and not the
1 A R-78E5.0 is the binding constraint gets **stronger**. Worth saying, because
the assumption currently makes the limit look higher than the datasheet supports.

---

## Part 2 — Confirmed against the banked documents

Everything below was opened and read; none of it needs to change.

**MPXV4006DP** — transfer function, both instances, p.5; `Voff` 0.152/0.265/0.378 V,
`VFSS` 4.6 V, 766 mV/kPa, `V_S` 4.75/5.0/5.25 V, all Table 1 p.3. The corpus's
`TRIM-BREATH-ZERO` row correctly sizes the trimmer against the **spec band**
0.152–0.378 V rather than the typical `[repo] hardware/bom.csv:68`.

**INA828 (SBOS792A)** — `G = 1 + (50 kΩ/R_G)` p.5. §8.1 *"For the best
performance, keep the source impedance to the REF terminal, RREF, below 5 Ω"*
**verbatim, p.22**. Table 2 EMIRR **exactly as quoted**: 400 MHz 48/87,
900 MHz 52/98, 1.8 GHz **94/51**, 2.4 GHz 66/57 — including the inversion the
BOM row flags. RFI filter −3 dB at **53 MHz** p.5. Abs max: supply ±18 V, signal
inputs **±40 V**, REF ±18 V p.4. Output swing (V−)+0.15 to (V+)−0.15, so −9.94 V
fits on ±12 V with 1.9 V to spare.

**OPA2197 (SBOS737C)** — `Z_O` 375 Ω on **both** p.8 and p.10 (see B3-08 for the
condition); PSRR ±1/±3 µV/V (p.**7**, see B3-09); `I_B` ±5 pA typ / ±20 pA max at
25 °C, ±5 nA over temperature, ±15 nA **PW package only** (the fitted part is
`OPA2197IDR`, SOIC-8, so ±5 nA applies); *"High Capacitive Load Drive Capability:
1 nF"* p.1 and §7.3.5 *"in a unity-gain configuration, directly drives up to 1 nF
of pure capacitive load"* **p.22**; Table 3 `R_ISO` p.23; `R_θJA` **107.9 °C/W**
for the OPA2197 vs 115.8 for the single OPA197 — the corpus is right that these
are different tables; Figure 56 p.30 exactly as quoted.

**REF5050 (SBOS410O, rev O Oct 2025)** — Table 4-2 p.3 verbatim (**the "A" suffix
is the worse grade — confirmed**); §8.4.1 p.26 verbatim including the ESR ≤ 1.5 Ω
ceiling; Figure 8-6 `C_L` = 1 µF–50 µF for REF50xxI/AI; §9.4.1.1 p.29 *"A resistor
in series with the output capacitor is optional"*; load regulation 20 typ / 30
max ppm/mA, 50 over temperature, p.7; output noise 0.9 µV_rms/V, 10 Hz–1 kHz, p.7;
§8.3.6 p.26 (the NR capacitor halves output noise).

**DAC8568 (SBAS430E)** — grades A/C power up to **zero scale**, B/D to midscale,
verbatim; reference output drift **grades C/D 2 typ / 5 max ppm/°C** vs A/B 5/25;
output range 0–AVDD with *"AVDD ≥5V; grades C and D: maximum output voltage 5V
when using internal reference"*; external `VREFIN ≤ AVDD/2` on C/D vs `≤ AVDD` on
A/B. The `dac-rail` **5.00 V hard floor** is supported: the grade-C conditions
are stated as `AVDD = 5.0 V to 5.5 V` in the `VREFIN` row and `AVDD ≥ 5 V` in the
OUTPUT CHARACTERISTICS row, against a global table condition of 2.7–5.5 V.

**LT1641-1 (164112fc)** — I re-checked **all twelve rows** of the verification
table in `umbilical-load-switch.md:126-141` and every one is correct, including
the `-1`/`-2` quotes, the pinout, the 1.5 nF minimum `C-TIMER`, `θ_JA` 110 °C/W
and the CS8/IS8 temperature ranges. Specifically: TIMER pulled to GND by a **3 µA**
source, **80 µA** pull-up when active, slope **77 µA/C_TIMER**, `C(nF) = 62·t(ms)`,
threshold **1.233 V** — all p.8 verbatim; foldback **12 mV at `V_FB` = 0, 47 mV at
`V_FB` ≥ 0.5 V** — p.5 SENSE pin and p.8 verbatim; `I_TIMERUP` −24/−80/−132 µA,
`I_TIMERON` 1.5/3/5 µA, `I_GATEUP` −5/−10/−20 µA (at `V_GATE = 7 V`), `V_FBH`
1.280/1.313/1.345 V, `V_FBL` 1.221/1.233/1.245 V, `V_LKO` 7.5/8.3/**8.8** V,
`V_SENSETRIP` 39/47/55 mV at `V_FB` = 1 V and 8/12/17 mV at `V_FB` = 0 — all p.2.
Sizing arithmetic re-derived: `[calc]` 10 µF × 1.233 V / (24−3) µA = 587 ms,
/(80−3) = 160 ms, /(132−3) = **95.6 ms** ✓; `[calc]` 5/82 n = 61 V/s, 10/82 n =
122, 20/82 n = 244 → 197/98/**49 ms** to 12 V ✓.

**74HC165 (four vendors)** — onsemi Rev. 13 p.4 3.0 V row `V_IH` 2.1 / `V_IL` 0.9
verbatim; TI/Nexperia/Toshiba 2.0/4.5/6.0 rows agree digit for digit (see B3-06
for what that does and does not prove).

**1N5817 (DS23001 Rev. 8)** — `V_FM` 0.450 V at 1 A, 0.750 V at 3 A; `V_RRM` 20 V;
`I_FSM` 25 A; `R_θJL` 15 °C/W. Fig. 2 digitisation reproduces the corpus's
calibration points to ±0.015 V and its 120 mV modulation to 0.1 mV (see B3-04
for the one number that does not reproduce).

**Laird MI1206K601R-10, rev E** — this one deserves a note: I extracted the five
bias traces from the content stream and read them at 100 MHz against the
calibrated gridlines. The corpus's digitisation is **essentially exact**:

| bias | corpus | B3 (vector extraction) |
|---|---|---|
| 0 A | ~614 Ω | **616 Ω** |
| 250 mA | ~431 Ω | **434 Ω** |
| 500 mA | ~157 Ω | **157 Ω** |
| 1000 mA | ~72 Ω | **73 Ω** |
| 1500 mA | ~51 Ω | **52 Ω** |

`Z@100 MHz` 600 nominal / 450 min / 750 max, DCR 0.080 Ω, rated 1500 mA, op temp
−40…+125 °C including self-heating — all confirmed. `[calc]` linear interpolation
gives 313 Ω at 359 mA and 277 Ω at 392 mA, which sit at the top of the corpus's
stated "~280–310" and "~245–275" bands — conservative, fine. The
**HI1206N601R-10** cross-check also holds: ~136–145 Ω at 0.5 A against the
MI1206's 157 Ω, so the corpus's finding that a 3000 mA part is *slightly worse*
at the same bias is **confirmed**.

**WS2815 V1.1** — this is CLAUDE.md §3's own example and the corpus handles it
correctly. The datasheet genuinely reuses `VDD`: Absolute Maximum Ratings give
*"Power supply voltage VDD +9.5~+13.5 V"* (p.2), while the Electrical
Characteristics table declares *"(TA=−20~+70 ℃, **VDD=4.5~5.5V**, VSS=0V)"* in its
own header (p.3) and then specifies `V_IH ≥ 0.7 VDD` for `DIN, SET`. So `V_IH` is
**3.15–3.85 V** and the 8.4 V reading used the pin-2 meaning. **Confirmed, and
the corpus's explanation of the trap is accurate.** I also did the visual check
the page asks for: rendered p.4 at 900 dpi, and in the *Recommended application
circuit* **L1 pin 6 (`BI`) is tied to pin 5 (`GND`) and thence to the GND rail**,
while the `DI` node runs on its own vertical to L2's `BI`. Both claims confirmed.

**WS2812B-2020 / WS2812C / XINGLIGHT surrogates** — *"Working Current 12mA"* per
channel, 36 mA white, *"Quiescent Current：<0.6mA"*, test condition DC = 5 V, all
on **p.4** as cited; WS2812C *"The working current of each channel is 5mA"*
confirmed. **Surrogate labelling is correct**: both XINGLIGHT rows open with
*"SURROGATE ONLY - NOT THE FITTED PART"* `[repo] datasheets/MANIFEST.csv:57,58`,
ADR 0014 names them as surrogates in the table and in prose
`[repo] docs/decisions/0014-lighting.md:384`, and `matrix-led-current` is
`blocked` rather than carrying either number. **No place in the corpus cites a
surrogate as the fitted part's spec.** This slice's item 3 comes back clean.

**Panel artefacts** — both banked non-PDF artefacts confirm `panel-height-budget`
exactly. `EURORACK-3U-PANEL-HP-TABLE-make_blanks.py`: `HEIGHT = 128.5`,
`HOLE_Y = (3.0, 125.5)`, `HOLE_DIA = 3.2`, `10: {"width": 50.50, "holes": …
[7.50, 43.06]}` `[repo] datasheets/mechanical/EURORACK-3U-PANEL-HP-TABLE-make_blanks.py:39-57`.
`EURORACK-3U-3HP-PANEL-apfaudio-pmod-r3.1.kicad_pcb`: I measured the Edge.Cuts
layer — **x −3.0…12.0 (w = 15.000), y 0.0…128.500 (h = 128.500)**, with the
mounting slots' arcs centred at **y = 3.0 and y = 125.5** spanning 1.4…4.6 in y
(**3.2 mm**, M3 clearance). Two independent artefacts, agreeing. `panel-width`
`[calc]` (10 × 5.08) − 0.3 = 50.50 ✓.

**LT5400 (5400fa)** — Distributed Capacitance **resistor-to-exposed-pad 5.5 pF,
resistor-to-resistor 1.4 pF**; exposed pad **1.88 × 1.68 mm**; *"EXPOSED PAD
(PIN 9) IS FLOATING"*; *"The exposed pad can be tied to any voltage (such as
ground) … To avoid interference, do not tie the exposed pad to [a noisy node]"* —
all confirmed. The option list runs **-1 through -6 only**, so the corpus's
caveat that rev fa predates the `-7` option and that `LT5400-7` is *not in
document* rather than refuted is **confirmed**.

**MCP3202-CI/SN** — abs max *"All Inputs and Outputs w.r.t. VSS: −0.6 V to
VDD + 0.6 V"*; single supply 2.7–5.5 V; 100 ksps at 5 V / 50 ksps at 2.7 V. Note
for the record: **the B/C suffix is the INL grade (±1 vs ±2 LSB), not a supply
grade** — so unlike the DAC8568, running this part at 3.3 V is not a grade
question. The `R-ADCDIV` ≥10 kΩ rule exists for the 5 V-before-3V3 power-up case
and is the right shape.

**ME6217C33M5G** — Note 4 verbatim: *"IOUTMAX: Due to restrictions on the package
power dissipation, this value may not be satisfied … **This specification is
guaranteed by design.**"* The corpus's characterisation is exact.

**SP0504BAHT** — see B3-15; every BOM-row claim checks out.

**NKK Series M** — see B3-14; every value checks out.

**Gateron KS-33** — see B3-13; both sheets check out.

---

## Part 3 — Slice item 5: absolute maximums

No circuit in the corpus violates a banked absolute maximum under any stated
condition, **including power-up**, as far as I can check without a layout. What I
verified:

| Part | Abs max | Design condition | Margin |
|---|---|---|---|
| INA828 | supply ±18 V; **signal inputs ±40 V**; REF ±18 V | ±12 V rails; `BREATH` fault case is a sustained +12 V | OK — and the ±40 V input rating is why the "+12 V fault is harmless" argument works |
| OPA2197 | 40 V total supply; *"Supply voltages larger than 40 V can permanently damage the device"* p.30 | ±12 V = 24 V | OK |
| DAC8568 | grade C specified 5.0–5.5 V AVDD | LM317 nominal 5.21 V, **hard floor 5.00 V at E7** | OK, and the floor is correctly tracked |
| MCP3202 | inputs −0.6 V to VDD+0.6 V | 5 V-before-3V3 on cold start | Handled by the ≥10 kΩ `R-ADCDIV` upper leg |
| LT1641-1 | VCC −0.3…100 V; TIMER −0.3…44 V; FB/ON −0.3…60 V; **C grade 0…70 °C** | +12 V | OK. The I grade (−40…+85 °C) is already recommended in the row |
| LM317L | `V_I − V_O` ≤ 35 V; peak 100 mA | 6.8 V differential, ~13 mA | OK, and above the 2.5 mA max minimum load |
| B5819WS (dev board) | `P_D` 200 mW, `R_θJA` 500 °C/W | the matrix's full-field current | **Violated at full white** — which is the corpus's own finding, correctly reached (see B3-17) |
| 1N5817 | `V_RRM` 20 V, `I_O` 1 A at `T_L` 90 °C | +12 V rail | OK |
| SP0504BAHT | package `P_D` 0.225 W; ESD-rated only, no pulse spec | SPI lines | OK, and the absence of a pulse rating is correctly recorded |
| WS2815 | VDD +9.5…+13.5 V; `T_opt` −25…+85 °C | 12 V | OK |
| NKK Series M | op temp −30…+85 °C; **max panel 2.6 mm** | 2 mm aluminium | 0.6 mm spare, as stated |

**One unstated operating-range constraint, worth a line somewhere:** the
**MPXV4006DP's operating temperature range is +10 °C to +60 °C**, and `Pmax` is
**24 kPa**, both in Table 2 Maximum Ratings
`[datasheet datasheets/analog/MPXV4006DP.pdf p.4]`. Figures 4 and 5, which carry
the transfer function, are both plotted for `TEMP = 10 to 60 °C` p.5. Nothing in
the corpus states a system operating range at all, so nothing contradicts this —
but a woodwind played in a cold room is below the sensor's specified floor, and
`sensor-full-scale` cites the transfer function with no temperature condition
attached. The instrument-body pages note the cavity runs 10–20 K above ambient
`[repo] hardware/cluster/key-switch-network/key-switch-network.md:118`, which
helps at the bottom and is the thing to check at the top.

**One arithmetic nit, B3-19:** `loadswitch-timer`'s worst-case fault time uses
`I_TIMERON` **typ** 3 µA against `I_TIMERUP` **max** 132 µA. A true worst case
pairs max pull-up with min pull-down: `[calc]` 10 µF × 1.233 / (132 − 1.5) µA =
**94.5 ms**, not 95.6 ms, so the ratio against the 47.5 ms hot-plug start is
**1.99×** rather than 2.01×. It crosses the "2×" the entry quotes. Cosmetic, but
the entry states 2.01× as if it were the guaranteed number.

---

## Part 4 — Slice item 6: the two BOM parts with no manifest row

`python3 tools/verify-datasheets.py` reports `77 verified, 21 recorded as blocked
or not-fetched, 0 problems`, and names two BOM parts with **no manifest row at
all** — not banked, and not recorded as a gap either.

**`U-ESD-USB` — USBLC6-2SC6. Nothing rests on it.**
`[repo] hardware/bom.csv:105` / `hardware/unplaced.csv:17`: qty 1, status
**`not-needed`**, *"Dev boards carry these. Only required if a custom MCU carrier
is ever built (ADR 0013)"*. No page draws it, no figure derives from it, no
argument depends on it. **Correctly a zero-consequence gap.** If anything, the
row should be a `BLOCKED`/`NOT-FETCHED` manifest entry purely so that
`verify-datasheets.py` stops naming it, or it should move out of the BOM
entirely — it is a contingency note, not a part.

**`D-TVS-BREATH` — PESD12VS1UB or equivalent 12 V-standoff ESD diode. Three
numeric claims rest on it, none of them sourced.**
`[repo] hardware/interfaces/breath-sense-link/bom.csv:4` (→ `hardware/bom.csv:43`),
qty **2**, status `candidate`, drawn at the connector on both `BREATH` legs
`[repo] hardware/carrier/carrier.md:118,137,290` and listed in
`[repo] hardware/interfaces/breath-sense-link/circuit.yaml:59`. So it is a real,
drawn, unretrofittable part on the project's DC-accurate analog output.

Its row carries these, all unmarked for provenance:

1. *"a 5V array's `V_RWM`"* — a claim about a part nobody has a document for.
2. *"**300 mV of margin**"* — **derived from the stale 4.7 V** (B3-02); the real
   figure is 140 mV `[calc]` 5.00 − 4.86.
3. *"**1.5 µA of leakage** into a 1k output resistor"* — a specific leakage
   current with no source anywhere in the repository.

The row's **conclusion** (12 V standoff, not 5 V) is independently supported by an
argument that needs no datasheet at all — ADR 0003 puts the buffer on +12 V
precisely so a sustained +12 V fault on `BREATH` is harmless, and a 5 V clamp
would turn that designed-safe case into a part that conducts until something
fails. That reasoning stands on its own. But **three numbers in the row are
citations to a document that does not exist in this repository**, and one of
them is demonstrably wrong.

**Recommend:** either bank a PESD12VS1UB (or whichever 12 V array is chosen) and
re-derive the three numbers, or add a `BLOCKED` row with the exact URLs per
CLAUDE.md §3 and mark the three claims `[from memory]` in the BOM row so a
reader can see which parts of it are load-bearing and which are not. As written
they read as spec.

---

## Appendix — reproducing this

```
pip install pymupdf          # pdftotext/pdftoppm are absent in this sandbox
# text:   doc[i].get_text("text")
# render: doc[i].get_pixmap(dpi=150).save(...)   # 600-900 dpi for a crop
# curves: doc[i].get_drawings() -> group line/curve items by stroke colour,
#         calibrate against the axis gridlines (also in get_drawings()),
#         then evaluate at the frequency/current of interest.
```

The numeric digitisations in B3-04 and the Laird table were produced this way
rather than by eye; my first eyeball reading of the Laird curves was wrong by up
to 60 % and the vector extraction corrected it, which is a reason to prefer the
geometry over the render when the answer is a number off a curve.
