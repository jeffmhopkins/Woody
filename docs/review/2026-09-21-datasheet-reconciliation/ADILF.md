# ADILF — LT5400 and SP0504BAHT datasheet findings

Wave R7, 2026-09-21. Researcher, not editor. No repo file touched except the two
banked PDFs.

Both assigned documents were **FETCHED and BANKED**. Neither is BLOCKED.

| Part | File | SHA-256 | Source |
|---|---|---|---|
| LT5400 | `datasheets/other-semi/LT5400.pdf` | `b396e782bab1d4021b91c53924fe3907c248141bbcdb40a68569aad2587de434` | `https://docs.rs-online.com/e83c/0900766b8109be20.pdf` |
| SP0504BAHT | `datasheets/discrete-and-power/SP0504BAHT.pdf` | `0085f933cf4d87c6e655a23d96f8a216ff8677af15c24b45b69ecfeab24dfd2c` | `https://www.farnell.com/datasheets/47249.pdf` |

Both verified: start with `%PDF`, >10 kB, part number present in `pdftotext -layout`
output (LT5400: 83 hits, zero `LT4256` hits — the mislabelled-mirror trap the brief
warned about did **not** fire here; SP0504: 9 hits, SOT-23 family doc).

---

## HEADLINE: three repo claims are REFUTED, two of them load-bearing

1. **The MS8E has an exposed pad. `bom.csv` R-PRECISION's package field is wrong.**
   The layout question is settled: the `EP1.68x1.88mm` footprint is the correct one.
2. **`SP0504BAHT` is SOT-23-**5**, not SOT-23-6.** Every repo row and page says -6.
   The SOT-23-6 member of this family is `SP0505BAHTG`, which is a **5**-channel part.
3. **The TVS array's package power dissipation is 0.225 W, not 0.98 W.** The
   unsourced reviewer figure is optimistic by 4.4×. And there is **no peak-pulse
   power rating of any kind in the document** — NOT-IN-DOCUMENT, loudly.

---

# PART 1 — LT5400

**Document banked:** Linear Technology `5400fa`, "LT5400 — Quad Matched Resistor
Network", 10 pages, © 2011, print code `LT 0811 REV A`.

**REVISION CAVEAT, read this first.** The repo consistently names `5400fc.pdf` as
canonical (`MANIFEST.csv:57`, `bom.csv:15`). **I banked rev `fa`, not `fc`.**
`www.analog.com` remained dead for the whole session (see BLOCKED-routes log below),
and the RS mirror carries rev fa. Rev fa's own Revision History (p.9) reads:

> `REV A | 8/11 | Added LT5400-4, LT5400-5, LT5400-6. Changes reflected throughout
> the data sheet. | 1-10`

So rev fa is the revision that *introduced* options -4/-5/-6. Anything numbered
above -6 would have arrived in a later revision (fb/fc) that I do not have. **This
matters for exactly one claim — see F-7.** Every other finding below is a package,
grade or drift spec that is stable across revisions.

## F-1 — EXPOSED PAD: REFUTED (this is the layout-blocking answer)

**Repo believes** `[repo] hardware/bom.csv:15` — package field is
`MSOP-8 (0.65mm pitch)` with no pad, while the same row's note warns
*"CAUTION, LAYOUT-BLOCKING: the E in MS8E means EXPOSED PAD. One committed footprint
uses MSOP-8-1EP_3x3mm_P0.65mm_EP1.68x1.88mm, another a plain MSOP-8. This row's
package field says MSOP-8 with NO PAD."*

**Datasheet says — three independent places:**

`[datasheet 5400fa p.2]`, Pin Configuration block, verbatim:

> ```
> MS8E PACKAGE
> 8-LEAD PLASTIC MSOP
> θJA = 40°C/W, θJC = 10°C/W
> EXPOSED PAD (PIN 9) IS FLOATING
> ```

`[datasheet 5400fa p.8]`, Package Description heading, verbatim:

> `MS8E Package`
> `8-Lead Plastic MSOP, Exposed Die Pad`
> `(Reference LTC DWG # 05-08-1662 Rev I)`

`[datasheet 5400fa p.4]`, Electrical Characteristics, has a row that only exists if
a pad exists:

> `Distributed Capacitance | Resistor to Exposed Pad | 5.5 | pF`
> `                        | Resistor to Resistor    | 1.4 | pF`

### VERDICT

- *"The E in MS8E means EXPOSED PAD"* — **CONFIRMED**, verbatim, p.8.
- *`bom.csv` package field `MSOP-8 (0.65mm pitch)` with NO pad* — **REFUTED.**
  The package is an 8-lead MSOP **with an exposed die pad**, designated **pin 9**.
- *The committed `MSOP-8-1EP_3x3mm_P0.65mm_EP1.68x1.88mm` footprint* —
  **CONFIRMED CORRECT**, to the hundredth of a millimetre. See F-2.
- *The committed plain `MSOP-8` footprint* — **WRONG. Do not use it.**

## F-2 — Exposed pad EXACT dimensions

`[datasheet 5400fa p.8]`, "BOTTOM VIEW OF EXPOSED PAD OPTION":

> `1.88 (.074)` × `1.68 (.066)`

and the RECOMMENDED SOLDER PAD LAYOUT on the same page gives the land with
tolerance:

> `1.88 ± 0.102 (.074 ± .004)`  ×  `1.68 ± 0.102 (.066 ± .004)`

Note 6, p.8, verbatim:

> `6. EXPOSED PAD DIMENSION DOES NOT INCLUDE MOLD FLASH. MOLD FLASH ON E-PAD`
> `   SHALL NOT EXCEED 0.254mm (.010") PER SIDE.`

**Exposed pad = 1.88 mm × 1.68 mm.** The KiCad footprint name `EP1.68x1.88mm` is an
exact match. **CONFIRMED.**

## F-3 — What the exposed pad must be connected to

This is the question the BOM row needed answered and could not reach. The datasheet
devotes a whole Applications-Information subsection to it.

`[datasheet 5400fa p.6]`, section heading **"Where to Connect the Exposed Pad"**,
verbatim and complete:

> "The exposed pad is not DC connected to any resistor terminal. Its main purpose is
> to reduce the internal temperature rise when the application calls for large
> amounts of dissipated power in the resistors. The exposed pad can be tied to any
> voltage (such as ground) as long as the absolute maximum ratings are observed.
>
> There is capacitive coupling between the resistors and the exposed pad, as
> specified in the Electrical Characteristics table. To avoid interference, **do not
> tie the exposed pad to noisy signals or noisy grounds**.
>
> **Connecting the exposed pad to a quiet AC ground is recommended** as it acts as
> an AC shield and reduces the amount of resistor-resistor capacitance."

Corroborated by the closing application circuit, `[datasheet 5400fa p.10]`, caption
under "Precision Single-Ended to Differential Conversion":

> `GROUNDING EXPOSED PAD RESULTS IN STABLE, NO OVERSHOOT RESPONSE`

And the absolute-max note that bounds it, `[datasheet 5400fa p.4]` Note 2:

> "...This includes the voltage across any resistor, **the voltage across any pin
> with respect to the exposed pad of the package**, and the voltage across any two
> unrelated pins."

### The two statements that look contradictory, and are not

p.2 says `EXPOSED PAD (PIN 9) IS FLOATING`; p.6 and p.10 recommend grounding it.
**These are not in conflict.** p.2 is a statement about the *die*: the pad is
electrically floating **internally**, i.e. not bonded to any resistor terminal — it
is a thermal/shield pad, not a circuit node. p.6 is the instruction about what *you*
should do with it **externally**. The datasheet's own recommendation is:

**Tie pin 9 to a quiet AC ground. Not to a noisy ground. Not left unconnected.**

For Woody this is a real decision, not a formality: the pitch stage is the one node
in the module where a 5.5 pF coupling path from a noisy plane would land directly on
the 1 V/oct output. `[datasheet 5400fa p.4]` gives that coupling as **5.5 pF
resistor-to-exposed-pad**, against only **1.4 pF resistor-to-resistor** — the pad is
the *dominant* stray on this part, and grounding it to the wrong plane injects more
than it shields. **Flagging for the lead: this is a new open question the BOM row
did not know it had.** ADR 0006's power tree already establishes that the LED
current is the noisy return in this instrument.

## F-4 — MS8E full outline

All `[datasheet 5400fa p.8]`, drawing `MSOP (MS8E) 0910 REV I`, dimensions in
mm/(inch):

| Feature | Value |
|---|---|
| Body (D, note 3) | `3.00 ± 0.102 (.118 ± .004)` |
| Body (E1, note 4) | `3.00 ± 0.102 (.118 ± .004)` |
| Lead span incl. leads (E) | `4.90 ± 0.152 (.193 ± .006)` |
| Lead pitch | `0.65 (.0256) BSC` |
| Height max (A) | `1.10 (.043) MAX` |
| Lead width (b) | `0.53 ± 0.152 (.021 ± .006)` |
| Lead thickness (c) | `0.22 – 0.38 (.009 – .015)` |
| Standoff (A1) | `0.1016 ± 0.0508 (.004 ± .002)` |
| Exposed pad | `1.88 × 1.68` |
| Lead coplanarity (note 5) | `0.102mm (.004") MAX` |
| θJA / θJC | `40°C/W` / `10°C/W` `[p.2]` |

**Recommended solder pad layout** `[p.8]`, the numbers to lay the land pattern to:

| Land feature | Value |
|---|---|
| Thermal land | `1.88 ± 0.102` × `1.68 ± 0.102` |
| Signal land length | `0.889 ± 0.127 (.035 ± .005)` |
| Signal land width | `0.42 ± 0.038 (.0165 ± .0015)` TYP |
| Land pitch | `0.65 (.0256) BSC` |
| Overall land span | `5.23 (.206) MIN` |
| Row-to-row (inner) | `3.20 – 3.45 (.126 – .136)` |

**`bom.csv`'s "(0.65mm pitch)" — CONFIRMED.** That half of the package field is right;
only the missing pad is wrong.

## F-5 — Options table: full, verbatim

`[datasheet 5400fa p.2]`, "Available Options", complete and verbatim:

| PART NUMBER | R2 = R3 (Ω) | R1 = R4 (Ω) | RESISTOR RATIO |
|---|---|---|---|
| LT5400-1 | 10k | 10k | **1:1** |
| LT5400-2 | 100k | 100k | 1:1 |
| LT5400-3 | 10k | 100k | 1:10 |
| LT5400-4 | 1k | 1k | 1:1 |
| LT5400-5 | 1M | 1M | 1:1 |
| LT5400-6 | 1k | 5k | 1:5 |

That is the entire table in rev fa. Six options.

### VERDICT

- *"the '-1' option is the four-equal-10k 1:1 quad"* `[repo] bom.csv:15` —
  **CONFIRMED.** LT5400-1 is R2=R3=10k, R1=R4=10k, ratio 1:1. All four equal, all
  10 k.
- *"10k is available in the MS8E"* — **CONFIRMED.** LT5400-1 and -3 both carry 10 k
  and every orderable part in the table is MS8E.
- *"there is no 1:3 option at all"* `[repo] bom.csv:15` — **CONFIRMED** for rev fa.
  Ratios offered are 1:1, 1:10 and 1:5 only.
- *`pitch-stage.md:313`: "The claim that two spare sections can build the mod
  channels' 1:3 is arithmetically impossible"* — the datasheet independently
  supports the conclusion by a second route: **there is no 1:3 part to buy either.**
  **CONFIRMED.**

## F-6 — Order code structure: CONFIRMED, with a correction to how the repo writes it

`[datasheet 5400fa p.3]`, Order Information. Thirty-four orderable parts, all
`8-Lead Plastic MSOP`. The `-1` block verbatim:

| LEAD FREE FINISH | TAPE AND REEL | PART MARKING | PACKAGE DESCRIPTION | SPECIFIED TEMP RANGE |
|---|---|---|---|---|
| `LT5400ACMS8E-1#PBF` | `LT5400ACMS8E-1#TRPBF` | LTFVR | 8-Lead Plastic MSOP | 0°C to 70°C |
| `LT5400BCMS8E-1#PBF` | `LT5400BCMS8E-1#TRPBF` | LTFVR | 8-Lead Plastic MSOP | 0°C to 70°C |
| `LT5400AIMS8E-1#PBF` | `LT5400AIMS8E-1#TRPBF` | LTFVR | 8-Lead Plastic MSOP | –40°C to 85°C |
| `LT5400BIMS8E-1#PBF` | `LT5400BIMS8E-1#TRPBF` | LTFVR | 8-Lead Plastic MSOP | –40°C to 85°C |
| `LT5400AHMS8E-1#PBF` | `LT5400AHMS8E-1#TRPBF` | LTFVR | 8-Lead Plastic MSOP | –40°C to 125°C |
| `LT5400BHMS8E-1#PBF` | `LT5400BHMS8E-1#TRPBF` | LTFVR | 8-Lead Plastic MSOP | –40°C to 125°C |
| `LT5400BMPMS8E-1#PBF` | `LT5400BMPMS8E-1#TRPBF` | LTFVR | 8-Lead Plastic MSOP | –55°C to 150°C |

**The true structure is two independent letter fields, not one:**

`LT5400` + **⟨matching grade: A or B⟩** + **⟨temperature grade: C, I, H or MP⟩** +
`MS8E` + `-⟨option⟩` + `#PBF` (add `TR` before `PBF` for tape and reel).

- **`bom.csv:15` writes it as `LT5400<grade>CMS8E-1#PBF`** — this hardcodes the `C`
  (0 °C to 70 °C) temperature grade into what it calls the template, which makes the
  template **misleading**: it reads as if `C` were part of the fixed stem. It is
  not; it is the *narrowest* temperature grade and the one Woody is least likely to
  want. **PARTIALLY REFUTED — the template is malformed, though the specific string
  it produces is a real orderable part.**
- **The three orderable examples the BOM cites from GitHub BOMs
  (`LT5400ACMS8E-1#PBF`, `LT5400BIMS8E-1#PBF`, `LT5400AHMS8E-1#PBF`) — all three
  appear verbatim in the datasheet's own order table. CONFIRMED.**
- Note `#PBF` and lead-free finish — **CONFIRMED** as the datasheet's own suffix.
- Part marking for every `-1` variant is `LTFVR` — useful for incoming inspection,
  and the marking does **not** encode the grade. `[p.3]` footnote, verbatim:
  *"\*The temperature grade is identified by a label on the shipping container."*
  **So an A-grade and a B-grade part are physically indistinguishable once out of
  the reel.** Worth a build note.
- *"MUST be the MS8 (MSOP) option, not the leadless DFN"* `[repo] bom.csv:15` —
  **CONFIRMED and moot in rev fa**: MS8E is the *only* package offered. There is no
  DFN in this document at all. (A DFN may exist in a later revision; rev fa has none.)

## F-7 — The `LT5400-7` claim: NOT-IN-DOCUMENT (rev fa)

`[repo] docs/log/2026-09-20-review-resolution.md:64-65`:

> "The claim that the LT5400 comes only in 1:1:1:1 or 10:1 ratios — **false**.
> LT5400-7 builds the required gain exactly."

**There is no LT5400-7 in rev fa.** The options table stops at -6 and the revision
history shows -4/-5/-6 were the newest additions as of 8/11.

**Verdict: NOT-IN-DOCUMENT, and I cannot settle it.** A `-7` option may genuinely
exist in rev fb/fc — the repo's own belief that `fc` is current is consistent with
further options having been added after 2011. **This is the one claim where the
missing rev fc actually costs us something.** Two mitigating facts for the lead:

1. `docs/log/` is explicitly **not corpus** (`CLAUDE.md` §4) — this is a historical
   record and must not be "corrected" regardless.
2. The design does not depend on it. `S9-adr-status.md:330` and `pitch-stage.md`
   both record that the mod channels are built from 1 % discretes, not from an
   LT5400 ratio, and `pitch-stage.md:313` kills the spare-sections route on
   arithmetic. So `-7` is of archaeological interest only.

**Do not let anyone "fix" ADR 0006's 1:4 claim by citing rev fa's absence of a 1:4
option as proof.** Rev fa proves only that 1:4 did not exist *in 2011*.

## F-8 — Grade A vs B matching: CONFIRMED

**Repo believes** `[repo] bom.csv:15`: *"Grade A = 0.01% matching, B = 0.025%."*

`[datasheet 5400fa p.1]` Features, verbatim:

> `n Excellent Matching`
> `  – A-Grade: 0.01% Matching`
> `  – B-Grade: 0.025% Matching`

`[datasheet 5400fa p.4]` Electrical Characteristics, the full ∆R/R row:

| SYMBOL | PARAMETER | CONDITIONS | MAX | UNITS |
|---|---|---|---|---|
| ∆R/R | Resistor Matching Ratio (Any Resistor to Any Other Resistor) | A-Grade | ±0.010 | % |
| | | A-Grade, TA = 0°C to 70°C | ±0.010 | % |
| | | A-Grade, TA = –40°C to 85°C | ±0.0125 | % |
| | | A-Grade, TA = –40°C to 125°C | ±0.0125 | % |
| | | B-Grade | ±0.025 | % |
| (∆R/R)CMRR | Matching for CMRR | A-Grade (Note 6) | ±0.005 | % |
| | | B-Grade (Note 6) | ±0.015 | % |

### VERDICT: **CONFIRMED.** A = ±0.010 %, B = ±0.025 %.

**One nuance the repo does not have.** The A-grade 0.01 % is the **25 °C / 0–70 °C**
number. Over **–40 °C to 85 °C it degrades to ±0.0125 %**, and over –40 °C to 125 °C
likewise. A Eurorack module is an `I`-grade application, so the honest A-grade
matching figure for Woody is **±0.0125 %, not ±0.01 %**. B-grade is flat at ±0.025 %
across all ranges. **New fact — flag to the lead.**

**And the definition is unusually strict, which is in Woody's favour.**
`[datasheet 5400fa p.6]`, "Matching Specification", verbatim:

> "The LT5400 specifies matching in the most conservative possible way. In each
> device, **the ratio error of the largest of the four resistors to the smallest of
> the four resistors** meets the specified matching level. Looser definitions would
> compare each resistor value to the average of the resistor values, which would
> typically result in specifications that appear twice as good as they are per the
> LT5400's more conservative definition."

So the ±0.0125 % is a true worst-case any-to-any, not an RSS or average-referred
number. A competitor's "0.01 %" may be 2× worse in the same terms.

## F-9 — Matching temperature drift: CONFIRMED, and the repo used the right number

**Repo believes** the tracking term is **1 ppm/°C**, giving **0.027 cents over
10 °C**. `[repo] docs/review/2026-09-21-staleness-sweep/S5-pitch-mod.md:315`:
*"LT5400 tracking, 1 ppm/°C | 10 ppm × 2.25 V = 22.5 µV | 0.027"*, and
`[repo] hardware/module/pitch-stage.md:288`: *"LT5400 ratio tracking | 0.027 cents"*.

`[datasheet 5400fa p.4]`, verbatim:

| SYMBOL | PARAMETER | CONDITIONS | MIN | TYP | MAX | UNITS |
|---|---|---|---|---|---|---|
| (∆R/R)/∆T | Resistor Matching Ratio Temperature Drift | (Note 5) | | **±0.2** | **±1** | ppm/°C |

`[p.1]` Features states the typical: `n 0.2ppm/°C Matching Temperature Drift`.
Note 5, `[p.4]`: *"This parameter is not 100% tested."*

### VERDICT: **CONFIRMED.**

The repo's 1 ppm/°C is the **datasheet MAX**, which is the correct figure for a
worst-case error budget. `[calc]` 1 ppm/°C × 10 °C = 10 ppm; 10 ppm × 2.25 V lever =
22.5 µV; the repo's 0.027 cents follows. **The arithmetic and the sourcing are both
sound.** The *typical* is 5× better (±0.2 ppm/°C → 0.0054 cents), so the part is
very likely better in practice than the budget table says — the budget is
conservative in the right direction.

`[datasheet 5400fa p.5]` gives the distribution behind this: "Distribution of
Matching Drift" histogram, x-axis −1 to +1 ppm/°C, peak at 0 — i.e. the ±1 ppm/°C
max really is the tail, not the centre.

**Two more drift/stability specs the repo does not cite and probably should**
`[datasheet 5400fa p.4]`:

| Parameter | Condition | Value |
|---|---|---|
| Resistor Matching Ratio Long-Term Drift | 35 °C, 2000 h, 10 mW | `<2 ppm` |
| Resistor Matching Ratio Long-Term Drift | 70 °C, 2000 h, 10 mW | `<4 ppm` |
| Resistor Matching Ratio Moisture Resistance | 85 °C / 85 % RH, 168 h | `<2 ppm` |
| Resistor Matching Ratio Thermal Shock/Hysteresis | –50 °C to 150 °C, 5 cycles | `<3 ppm` |
| **Resistor Matching Ratio IR Reflow** | **25 °C to 260 °C, 3 cycles** | **`<3 ppm`** |
| Resistor Matching Ratio Accelerated Shelf Life | 150 °C, 1000 h | `10 ppm` |
| Resistor Voltage Coefficient | | `<0.1 ppm/V` |
| Excess Current Noise | Mil-Std-202 Method 308 | `<–55 dB` |
| Harmonic Distortion | 20 Vp-p, 1 kHz, difference amp | `–120 dBc` |

The `<3 ppm` **IR reflow** figure is the one worth having on a board built once: the
act of soldering the part costs ~3 ppm of matching, i.e. `[calc]` 3 ppm × 2.25 V =
6.75 µV, about 0.008 cents — a third of the whole 10 °C drift term. It is small, and
it is a one-time offset that calibration absorbs. **Confirms the "calibrate after
assembly, not before" posture.**

## F-10 — Absolute value and tolerance: NEW, and it is much looser than anyone expects

`[datasheet 5400fa p.4]`, verbatim:

| SYMBOL | PARAMETER | CONDITIONS | MAX | UNITS |
|---|---|---|---|---|
| ∆R | Absolute Resistor Tolerance | A-Grade | **±7.5** | % |
| | | B-Grade | **±15** | % |
| ∆R/∆T | Absolute Resistor Value Temperature Drift | (Note 5), MIN –10, TYP 8 | 25 | ppm/°C |

**Absolute value is ±7.5 % (A) / ±15 % (B).** This is not a defect — it is the
deliberate trade of a matched network: the *ratio* is 100× better than a 1 % discrete
while the *absolute* is 7.5× worse. Nobody in the repo has written it down.

**Consequence for `TRIM-GAIN` that the repo has not noticed.** `[repo] bom.csv:110`
sizes the 200 Ω trimmer as *"0 to +2 % of the ratio"*, arithmetic that assumes
R2 = 10 kΩ exactly: `[calc]` 200 / 10 000 = 2.00 %. With a B-grade part R2 may be
anywhere in 8.5 k–11.5 k, so the trimmer's actual authority ranges
`[calc]` 200/11 500 = **1.74 %** to 200/8 500 = **2.35 %**. With A-grade,
`[calc]` 200/10 750 = **1.86 %** to 200/9 250 = **2.16 %**.

**The trimmer is one-sided (0 → +N %) and `pitch-stage.md`'s "Still open" section
already worries it "has no downward authority at all."** The worst case for that
worry is the *low* end — **1.74 % on a B-grade part** — 13 % less range than the
2 % the BOM row claims. It does not break anything, but the "2 %" figure is a
nominal that the datasheet does not guarantee. **Flag to the lead: if A vs B is
being chosen on matching alone, note that B also widens the trimmer-authority
spread.**

Also `[datasheet 5400fa p.1]` Features: `8ppm/°C Absolute Resistor Value Temperature
Drift` — typ 8, max 25, min −10 ppm/°C `[p.4]`. Irrelevant to a ratio, relevant if
any section is ever used single-ended against a discrete.

## F-11 — Power rating per element: 800 mW

`[datasheet 5400fa p.2]`, Absolute Maximum Ratings, verbatim:

> `Power Dissipation (Each Resistor) (Note 3)........ 800mW`
> `Total Voltage (Across Any 2 Pins) (Note 2).……….±80V`
> `Maximum Junction Temperature ........................... 150°C`
> `Storage Temperature Range.................... –65°C to 150°C`

Note 3, `[p.4]`: *"In order to keep the junction temperature within the Absolute
Maximum Rating, maximum power dissipation should be derated at elevated ambient
temperatures."*

`[datasheet 5400fa p.6]`, "Thermal Considerations", verbatim:

> "Each resistor is rated for relatively high power dissipation, as listed in the
> Absolute Maximum Ratings section of this data sheet. To calculate the internal
> temperature rise inside the package, add together the power dissipated in all of
> the resistors, and multiply by the thermal resistance coefficient of the package
> (θJA or θJC as applicable). For example, if each resistor dissipates 250mW, for a
> total of 1W, the total temperature rise inside the package equals 40°C. **All 4
> resistors will be at the same temperature, regardless of which resistor dissipates
> more power.**"

**"All 4 resistors will be at the same temperature" is a genuinely useful fact for
Woody** and is the physical reason the matching spec holds: self-heating cannot
create a ratio error, only a common-mode absolute shift. Woody's dissipation is
trivial `[calc]`: with 10 k sections and ≤7 V across one, P ≤ 7²/10 k = 4.9 mW,
i.e. **0.6 % of the 800 mW rating** and a temperature rise of `[calc]` ~4.9 mW ×
2 sections × 40 °C/W = 0.4 °C. **Non-issue, and now sourced.**

**±75 V operating / ±80 V absolute max** `[p.1, p.2]` — vastly beyond Woody's ±12 V
rails. Non-issue, now sourced.

## F-12 — ESD: the LT5400 has NO internal protection diodes

`[datasheet 5400fa p.6]`, section "ESD", verbatim:

> "The LT5400 can withstand up to **±1kV** of electrostatic discharge (ESD, human
> body). **To achieve the highest precision matching, the LT5400 is designed without
> explicit ESD internal protection diodes.** ESD beyond this voltage can damage or
> degrade the device including causing pin-to-pin shorts."

and immediately after:

> "To protect the LT5400 against large ESD strikes, external protection can be added
> using diodes to the circuit supply rails or bidirectional Zeners to ground
> (Figure 1)."

Figure 1 `[p.6]` shows exactly two options, labelled: **`BAV99`** to `V–`/`V+` for a
part reached from an EXTERNAL CONNECTOR, or **`UMZ36K`** bidirectional Zener to
ground.

**±1 kV HBM is low** — an ordinary op-amp is 2–4 kV. **NEW, and it matters:**
`pitch-stage.md` puts this network in the feedback path of the output stage, and
`[repo] pitch-stage.md` records that *"pitch feedback is tapped at the jack"* — i.e.
**an LT5400 terminal has a path to a panel jack, which is exactly the "EXTERNAL
CONNECTOR" case the datasheet's Figure 1 is drawn for.** A patch cable into a
Eurorack jack is an ESD event.

**The datasheet's named remedy is `BAV99`, and Woody already has BAV99 in the BOM**
(`[repo] datasheets/discrete-and-power/BAV99.pdf` is banked, and
`R2-bipolar-cv-outputs.md:476` refers to *"The `BAV99` clamps"*). So the fix may
already be present — **but whether the existing BAV99 clamps sit between the jack
and the LT5400 node, or only elsewhere, is a schematic question I am not authorised
to edit and did not trace.** **Filing as a finding for the lead: node = the pitch
stage feedback tap at the output jack; check that a clamp stands between it and any
LT5400 pin.** This is the kind of semantic dependency `CLAUDE.md` §4 says the
checker cannot catch.

## F-13 — Pin configuration and temperature grades

`[datasheet 5400fa p.2]`, Pin Configuration, TOP VIEW: pins 1–8 with `R1` between
1 and 8, `R2` between 2 and 7, `R3` between 3 and 6, `R4` between 4 and 5. Each
resistor is a fully independent two-terminal element — `[p.1]` Description: *"All
four resistors can be accessed and biased independently."* **Confirms the repo's
"two of four sections used, two spare" framing is physically possible.**

Operating / specified temperature ranges `[p.2]`:

| Grade | Operating | Specified |
|---|---|---|
| LT5400C | –40 °C to 85 °C | **0 °C to 70 °C** |
| LT5400I | –40 °C to 85 °C | –40 °C to 85 °C |
| LT5400H | –40 °C to 125 °C | –40 °C to 125 °C |
| LT5400MP | –55 °C to 150 °C | –55 °C to 150 °C |

Note 4 `[p.4]`, verbatim: *"The LT5400C is guaranteed functional over the operating
temperature range of –40°C to 85°C. The LT5400C is designed, characterized and
expected to meet specified performance from –40°C to 85°C **but is not tested or QA
sampled at these temperatures.** The LT5400I is guaranteed to meet specified
performance from –40°C to 85°C."*

**Relevant to the `C` baked into `bom.csv`'s order-code template (F-6):** a `C` part
is only *specified* 0–70 °C. `I` costs little and is guaranteed to 85 °C.

---

# PART 2 — SP0504BAHT

**Document banked:** Littelfuse `SP050xBA Lead-Free/Green`, "TVS Diode Arrays —
Surface Mount TVS Avalanche Diode Array", 8 pages, internal PDF title
`CH05 silicon protection`, printed page numbers **220–227** (it is an extract from a
Littelfuse databook section, not a standalone part datasheet). **No document number
and no revision date appear anywhere in it** — that is a real limitation of this
document and should be recorded as such.

This is a **family** datasheet covering SP0502BA / SP0503BA / SP0504BA / SP0505BA /
SP0506BA in nine package variants. Everything below is either family-wide or
explicitly the SP0504BAHT(G) row.

## F-14 — PACKAGE: REFUTED. It is SOT-23-**5**, not SOT-23-6.

**Repo believes**, in at least three places:
- `[repo] hardware/bom.csv:103` — `U-TVS-SPI,controller,SP0504BAHT or equivalent
  4-channel 5V array,...,SOT-23-6 (0.95mm pitch),1,candidate`
- `[repo] hardware/controller/carrier.md:825` — `| U-TVS-SPI | SP0504BAHT, SOT-23-6
  | SCLK, MOSI, CS + spare, to PWR_GND |`
- `[repo] hardware/controller/carrier.md:812` — `U-TVS-CHAIN | 4-ch array, SOT-23-6`
- `[repo] hardware/bom.csv:96` — `U-TVS-CHAIN,controller,4-channel TVS array,,...,SOT-23-6`

`[datasheet SP050xBA p.1]`, Ordering Information table, verbatim and complete:

| Part Number | CH | Package Type | Quantity Per Reel |
|---|---|---|---|
| SP0502BAHTG | 2 | SOT23 | 3000 |
| SP0503BAHTG | 3 | SOT143 | 3000 |
| **SP0504BAHTG** | **4** | **SOT23-5** | 3000 |
| **SP0505BAHTG** | **5** | **SOT23-6** | 3000 |
| SP0504BAATG | 4 | TSSOP-8 | 2500 |
| SP0506BAATG | 6 | MSOP-8 | 2500 |
| SP0502BAJTG | 2 | SC70-3 | 3000 |
| SP0504BAJTG | 4 | SC70-5 | 3000 |
| SP0505BAJTG | 5 | SC70-6 | 3000 |

Corroborated by the outline drawing `[datasheet SP050xBA p.6]`, headed
**`SP0504BAHTG - SOT23-5`**, package table `Package: SOT23-5 / Pins: 5 / JEDEC:
MO-178`; and `[p.7]`, headed **`SP0505BAHTG - SOT23-6`**, `Package: SOT23-6 /
Pins: 6`.

### VERDICT: **REFUTED, in four places.**

**`SP0504BAHT` is a 5-pin SOT-23 (SOT-23-5 / JEDEC MO-178). The SOT-23-6 part in
this family is `SP0505BAHTG`, and it is a FIVE-channel device, not a four-channel
one.** The repo has consistently paired the right part number with the wrong
package.

**This is not cosmetic.** `[repo] bom.csv:103` was written specifically to *replace*
`U-TVS-UMB`, whose stated sin was that *"that part is obsolete AND uDFN-14, not the
SOT-23-6 the row claimed."* The replacement row repeated the same class of error:
**it asserted a package it had not checked.** The footprint that gets committed for
`U-TVS-SPI` must be **SOT-23-5**, and a SOT-23-6 land pattern will not take this part.

**Two clean ways out, both supported by this document — the lead's call:**
1. Keep `SP0504BAHT`, change the package field to **SOT-23-5**. Four channels is
   exactly what the row asks for (`SCLK`, `MOSI`, `CS` + one spare).
2. Move to **`SP0505BAHTG`**, which *is* SOT-23-6 and gives **five** channels —
   three used, two spare. Same family, same die, same specs, one extra pin.

Option 2 also has a bearing on `U-TVS-CHAIN` `[repo] bom.csv:96`, which wants to
protect **four** signals leaving the carrier. A 4-channel `SP0504BAHT` in SOT-23-5
covers that exactly, with no spare. Note that `U-TVS-CHAIN` is currently written as
`SOT-23-6` too, and is equally wrong.

**Pin pitch: the repo's "(0.95mm pitch)" is CONFIRMED.** `[datasheet p.6]`,
SOT23-5 table: `e = 0.95 BSC`, `e1 = 1.90 BSC`. Same pitch on SOT23-6 `[p.7]`. So
the *pitch* half of the package field is right on both rows — only the pin count is
wrong. **And 0.95 mm is comfortably outside the ADR 0013 fine-pitch ban**, so the
package-policy reasoning in the row survives intact.

## F-15 — Four channels and the pin/channel map: CONFIRMED

`[datasheet SP050xBA p.1]`, Ordering Information: `SP0504BAHTG | CH = 4`. **4
channels — CONFIRMED.**

`[datasheet SP050xBA p.1]`, Pinout diagram for `SP0504BAHTG / SP0504BAJTG` (read
from the rendered page — the diagram is vector art and does not extract as text):

```
        ┌─────────────┐
   1 ───┤ ▶|      |◀  ├─── 5
        │  ●───────●  │
   2 ───┤─────┬─────  │          pin 2 = COMMON / GROUND
        │  ●───────●  │
   3 ───┤ ▶|      |◀  ├─── 4
        └─────────────┘
```

- **Pin 2 is the common / ground pin.**
- **Pins 1, 3, 4 and 5 are the four protected channels.**
- Each channel is a back-to-back pair (avalanche diode + forward diode) from the
  channel pin to the common rail.

Cross-checks in the same drawing set: the 2-channel `SP0502BAHTG` uses pin 3 as
common with pins 1, 2 as channels; the 5-channel `SP0505BAHTG` (SOT23-6) uses
pins 1, 2, 3, 4, 5, 6 with one common.

**`[repo] carrier.md:825` — `SCLK, MOSI, CS + spare, to PWR_GND` — the TOPOLOGY is
CONFIRMED** as buildable: three signal channels plus one spare, all returning to a
single common pin which goes to `PWR_GND`. **Only the package is wrong.**

> Aside, noted not adjudicated: `[repo] S2-umbilical.md:428` and
> `S12-findings-reconciliation.md:99` record an **unresolved** disagreement about
> whether `U-TVS-SPI` should return to `PWR_GND` while `U-TVS-CHAIN` returns to
> `DIG_GND`. The datasheet cannot settle that — it is a system grounding question.
> But it confirms the constraint that makes it sharp: **all four channels share ONE
> common pin.** There is no per-channel ground. So a single array cannot straddle
> two grounds, and if the three SPI lines and the chain's four signals must return
> to different nets, **they genuinely need two separate packages.** That supports
> the existence of both BOM rows.

## F-16 — POWER RATING: REFUTED. 0.225 W, not 0.98 W.

**Repo believes** — and `[repo] datasheets/README.md:60` flags it as the open
question: *"**SP0504BAHT** — the TVS array's power rating has never had a source."*
`[repo] datasheets/MANIFEST.csv:63`: *"THE POWER RATING IS THEREFORE NOT ESTABLISHED
— the reviewer's 0.98W-into-SOT-23-6 figure has no datasheet behind it."*

`[datasheet SP050xBA p.2]`, Absolute Maximum Ratings, verbatim and complete:

| Parameter | Rating | Unit |
|---|---|---|
| Storage Temperature Range | -65 to + 150 | ˚C |
| **Package Power Dissipation** | | |
| SC70 | **0.2** | W |
| **SOT23-3, SOT23-5, SOT23-6, SOT143** | **0.225** | **W** |
| TSSOP, MSOP | 0.5 | W |

Independently corroborated on the package outline page `[datasheet SP050xBA p.7]`,
in the `SOT23-6` dimension table's final row, verbatim:

> `PD@70°C   .225W`

### VERDICT: **REFUTED. The "0.98 W" claim is wrong by 4.4×.**

`[calc]` 0.98 / 0.225 = 4.36. The reviewer's figure was not merely unsourced, it was
**materially optimistic**, and in the unsafe direction. The banked document now
settles it.

**The honest figure to carry: `0.225 W` steady-state package power dissipation,
specified at 70 °C ambient, and it is the same 0.225 W for SOT23-5 and SOT23-6 —
so this finding does not change with the F-14 package correction.**

Per `CLAUDE.md` §3 — *"A number read off a banked document beats one from a
review"* — this is a fourth figure that has moved this way.

## F-17 — PEAK PULSE POWER: **NOT-IN-DOCUMENT.** Loudly.

The brief asked for peak pulse power dissipation and the waveform it is specified
for (8/20 µs? 10/1000 µs? tp?).

**It is not in this document. At all.**

I searched the full extracted text of all 8 pages for `peak`, `pulse`, `8/20`,
`8x20`, `Watt`, `thermal`, `θ`, `Rth`, `derat`. **The only hit for "pulse" in the
entire document** is a graph caption, `[datasheet SP050xBA p.3]`:

> `Typical Input VI Characteristics`
> `(Pulse-mode measurements, pulse width = 0.7 mS nominal)`

— and that is a *measurement condition for a V-I curve*, not a rating.

**There is no `I_PP`. No peak pulse power. No 8/20 µs or 10/1000 µs rating. No
surge-current curve. No pulse-derating curve. No thermal resistance (θJA/θJC) for
any package.**

### VERDICT: **NOT-IN-DOCUMENT.**

**What this means, and it is the substantive answer to the brief's question:**

`SP050xBA` is specified as an **ESD-suppression array, not a surge/lightning TVS.**
Its transient capability is stated *only* as ESD immunity levels (F-18) and an
ESD clamp voltage — never as a joule or watt rating. **The document offers no basis
whatsoever for any peak-pulse-power number, 0.98 W or otherwise.** Anyone who wants
a peak pulse figure for this part must either get it from a different Littelfuse
document or accept that the part is not characterised for it.

**This independently confirms `datasheets/README.md:60` and `MANIFEST.csv:63` were
right to flag it** — and goes further: the figure is not merely unsourced, **it is
unsourceable from the part's own datasheet.** The correct disposition is not "find
the source" but "the part is specified in ESD terms; use those."

**Good news for Woody:** `[repo] carrier.md` puts this array on SPI lines inside a
2 m umbilical — an **ESD** threat (a person touching the connector), not a
lightning-surge threat. **The ESD specification is the relevant one, and it is
generous** (F-18). So the missing peak-pulse rating does not block anything; it just
means the 0.98 W line must be deleted rather than corrected.

## F-18 — Electrical specification, complete and verbatim

`[datasheet SP050xBA p.2]`, "Electrical Specifications, TA = +25 °C, Unless
Otherwise Specified":

| PARAMETER | TEST CONDITIONS | MIN | TYPICAL | MAX | UNITS |
|---|---|---|---|---|---|
| Reverse Standoff Voltage | I = 10 µA | **5.5** | - | - | V |
| Reverse Standoff Leakage Current | V = 5.0 V | | **1** | **100** | nA |
| **Signal Clamp Voltage — Positive** | **I = 10 mA** | **5.6** | **6.8** | **8** | **V** |
| **Signal Clamp Voltage — Negative** | **I = 10 mA** | **-1.2** | **-0.8** | **-0.4** | **V** |
| Clamp Voltage during ESD, MIL-STD-883 Method 3015 (HBM), 8 kV | | | **12** | | V |
| Clamp Voltage during ESD, 8 kV | | | **-8** | | V |
| **ESD Test Level** — IEC-61000-2 [sic], Contact discharge | | **20** | | | kV |
| **ESD Test Level** — MIL-STD-883 Method 3015 (HBM) | | **30** | | | kV |
| **Capacitance** | **2.5 V @ 1 MHz** | | **30** | | **pF** |
| Turn on/off Time | | | **<1** | | ns |
| Temperature Range — Operating | | -40 | | 85 | °C |
| Temperature Range — Storage | | -65 | | 150 | °C |
| Diode Dynamic Resistance — Forward Conduction | | | **1.0** | | Ω |
| Diode Dynamic Resistance — Reverse Conduction | | | **1.4** | | Ω |

Note (1) `[p.2]`, verbatim: *"ESD voltage applied between channel pins and ground,
one pin at a time; all other channel pins are open; all ground pins are grounded."*

Features page `[datasheet SP050xBA p.1]`, verbatim:

> `• ESD Capability Standards`
> `    IEC 61000-4-2, Direct Discharge . . . . 20kV (Level 4)`
> `    IEC 61000-4-2, Air Discharge  . . . . . 30kV (Level 4)`
> `    MIL STD 883 3015.7 . . . . . . . . . . . . . . 30kV`
> `• Input Protection for Applications Up to 5VDC`
> `• Fast Response Time . . . . . . . . . . . . . . . < 1ns`
> `• Low Input Capacitance . . . . . . . . . . . . 30pF Typical`
> `• Operating Temperature Range. . . . . . . -40°C to 85°C`

> **Document defect, noted for honesty:** the Electrical Specifications table
> writes the contact-discharge standard as **"IEC-61000-2"**. The Features page and
> the Description both write **"IEC 61000-4-2"**. The table is a typo. Cite the part
> as IEC 61000-4-2.
>
> Also note the Features page and the table disagree on how the 30 kV air-discharge
> and 30 kV HBM figures are grouped. Features: air discharge 30 kV *and* MIL-STD-883
> 30 kV. Table: contact 20 kV and MIL-STD-883 30 kV, with no air-discharge row. Both
> agree on **20 kV contact / 30 kV HBM**; treat air discharge 30 kV as Features-page
> only.

### Verdicts against the brief's checklist

| Asked for | Answer | Verdict |
|---|---|---|
| V_RWM (working voltage) | **5.5 V min at I = 10 µA** | Found |
| V_BR (breakdown) | **Not stated as such.** Nearest is the 5.5 V standoff at 10 µA | **NOT-IN-DOCUMENT** |
| V_C clamping at specified I_PP | **6.8 V typ / 8 V max at I = 10 mA** — but 10 mA is *not* an I_PP; there is no I_PP in the document. ESD clamp: **12 V typ at 8 kV HBM** | Found, with caveat |
| ESD IEC 61000-4-2 contact | **20 kV (Level 4)** | Found |
| ESD IEC 61000-4-2 air | **30 kV (Level 4)** (Features page) | Found |
| ESD HBM | **30 kV**, MIL-STD-883 Method 3015.7 | Found |
| Channel capacitance per line | **30 pF typ at 2.5 V, 1 MHz** | Found |
| Leakage at V_RWM | **1 nA typ / 100 nA max at V = 5.0 V** | Found |
| Peak pulse power + waveform | — | **NOT-IN-DOCUMENT** (F-17) |
| Steady-state power | **0.225 W**, SOT23-5/-6 | Found (F-16) |
| Thermal resistance | — | **NOT-IN-DOCUMENT** |
| 4-channel 5 V array | **CONFIRMED** — CH = 4, "up to 5VDC" | **CONFIRMED** |
| SOT-23-6 | — | **REFUTED** — it is SOT-23-5 (F-14) |

## F-19 — The array is effectively UNI-DIRECTIONAL. New, and worth knowing.

The negative clamp is **-0.4 / -0.8 / -1.2 V at I = -10 mA** `[datasheet p.2]` —
that is a plain forward diode drop, not an avalanche knee. `[datasheet p.3]`'s
"Typical Input VI Characteristics" curve confirms the shape: it conducts hard below
about −0.8 V and holds off up to ~+6 V.

**So each channel is: avalanche to ~6.8 V positive, forward diode at ~0.8 V
negative.** It protects a **0 V to +5 V** signal referenced to the common pin. It is
**not** a symmetric bipolar clamp.

**For `U-TVS-SPI` this is exactly right** — `SCLK`, `MOSI`, `CS` are 0–3.3 V logic
referenced to a ground. **Nothing to fix.** But it is a fact the BOM row's phrase
*"4-channel 5V array"* does not convey, and anyone reaching for this part to clamp a
**bipolar CV** line would be misled. Given that `R2-bipolar-cv-outputs.md` exists
and that Woody has ±12 V CV elsewhere, **flagging so the part is not reused on a
bipolar node.**

## F-20 — 30 pF on an SPI line: quantified, and it is fine

`[datasheet p.2]`: **30 pF typ per channel at 2.5 V, 1 MHz.** `[datasheet p.3]`'s
"Typical Diode Capacitance vs Reverse Voltage" curve shows it falling from ~55 pF at
0 V to ~25 pF at 5 V — so 30 pF is the mid-bias figure and the value at a logic high
is somewhat lower.

**30 pF is high** for a signal-line TVS (modern parts hit 0.5 pF), and the repo has
never accounted for it. `[datasheet p.1]` Applications lists *"Computer port,
keyboard (USB1.1)"* — this is a **low-speed** part by design.

**But it is fine here, and here is the arithmetic so nobody has to redo it.**
`[repo] carrier.md:594` — SPI2 runs at **2 MHz** for the DAC down the umbilical.
`[repo] config/figures.yaml:101-103` — there is a **100 Ω** series resistor at the
driving end (`R-SPI-SER`, qty 3).

`[calc]` The TVS adds 30 pF to a line that already carries ~2 m of Cat5 at roughly
50 pF/m ≈ 100 pF. Total ≈ 130 pF. With the 100 Ω series resistor:
τ = 100 Ω × 130 pF = **13 ns**; 10–90 % rise ≈ 2.2 τ = **29 ns**.
At 2 MHz the half-period is **250 ns**. The edge consumes `[calc]` 29/250 = **12 %**
of the half-period.

**Verdict: acceptable, with margin.** The TVS is `[calc]` 30/130 = **23 %** of the
line's total capacitance — a real but not dominant contribution. **Two notes for the
lead:** (a) this is the first time the TVS capacitance has been entered into the
umbilical's edge budget at all, and (b) if SPI2 is ever pushed much above 2 MHz, the
30 pF becomes the cheapest thing to attack — low-capacitance arrays in the same
package are commodity parts.

`[datasheet p.2]`: turn-on/off time **<1 ns**, so the clamp itself is not the limit.

---

# Repo claim ledger

Every claim I was asked to adjudicate, and a few I found on the way.

## LT5400

| # | Repo claim | Location | Verdict |
|---|---|---|---|
| 1 | Package is `MSOP-8 (0.65mm pitch)` with **no pad** | `bom.csv:15` | **REFUTED** — exposed pad, pin 9 |
| 2 | "the E in MS8E means EXPOSED PAD" | `bom.csv:15` | **CONFIRMED** verbatim p.8 |
| 3 | Footprint `...EP1.68x1.88mm` | `bom.csv:15` | **CONFIRMED CORRECT** — exact match |
| 4 | Footprint plain `MSOP-8` | `bom.csv:15` | **REFUTED** — wrong footprint |
| 5 | 0.65 mm lead pitch | `bom.csv:15` | **CONFIRMED** — 0.65 BSC |
| 6 | `-1` is the four-equal-10k 1:1 quad | `bom.csv:15` | **CONFIRMED** p.2 |
| 7 | "there is no 1:3 option at all" | `bom.csv:15` | **CONFIRMED** (rev fa) |
| 8 | Order code `LT5400<grade>CMS8E-1#PBF` | `bom.csv:15` | **PARTIALLY REFUTED** — two letter fields (matching **and** temperature); the `C` is not part of the stem |
| 9 | `LT5400ACMS8E-1#PBF`, `LT5400BIMS8E-1#PBF`, `LT5400AHMS8E-1#PBF` orderable | `bom.csv:15` | **CONFIRMED** — all three in the order table p.3 |
| 10 | "MUST be the MS8 (MSOP), not the leadless DFN" | `bom.csv:15` | **CONFIRMED** — MS8E is the only package in rev fa |
| 11 | Grade A = 0.01 % matching | `bom.csv:15` | **CONFIRMED**, with the –40/85 °C caveat (±0.0125 %) |
| 12 | Grade B = 0.025 % matching | `bom.csv:15` | **CONFIRMED**, flat across range |
| 13 | Ratio tracking 1 ppm/°C → 0.027 cents / 10 °C | `pitch-stage.md:288`, `S5:315` | **CONFIRMED** — 1 ppm/°C is the datasheet max; typ is 0.2 |
| 14 | "10k available in MS8E" | implied `bom.csv:15` | **CONFIRMED** — LT5400-1 |
| 15 | "Two of four sections used, two spare" | `bom.csv:15` | **CONFIRMED** physically — all four independently accessible p.2 |
| 16 | `LT5400-7 builds the required gain exactly` | `docs/log/2026-09-20:64-65` | **NOT-IN-DOCUMENT** (rev fa stops at -6). Historical record, not corpus — do not edit |
| 17 | ADR 0006: "Gain of 4 is a 1:4 ratio, which the LT5400 family offers directly" | `S9:334`, `S5:395` | **NOT-IN-DOCUMENT** — no 1:4 in rev fa. Cannot fully refute without rev fc |
| 18 | `TRIM-GAIN` 200 Ω = "0 to +2 % of the ratio" | `bom.csv:110` | **QUALIFIED** — true at nominal; ±7.5 %/±15 % absolute tolerance makes the real range 1.74–2.35 % (B) / 1.86–2.16 % (A) |
| 19 | Canonical doc is `5400fc.pdf` | `MANIFEST.csv:57` | **UNVERIFIED** — I banked rev **fa**. analog.com unreachable all session |

## SP0504BAHT

| # | Repo claim | Location | Verdict |
|---|---|---|---|
| 20 | `U-TVS-SPI` package `SOT-23-6` | `bom.csv:103` | **REFUTED** — SP0504BAHT is **SOT-23-5** |
| 21 | `SP0504BAHT, SOT-23-6` | `carrier.md:825` | **REFUTED** — same |
| 22 | `U-TVS-CHAIN` `4-ch array, SOT-23-6` | `carrier.md:812`, `bom.csv:96` | **REFUTED** — the 4-ch part in this family is SOT-23-5 |
| 23 | "(0.95mm pitch)" | `bom.csv:103` | **CONFIRMED** — e = 0.95 BSC |
| 24 | Not fine-pitch / ADR 0013-compliant | `bom.csv:103` | **CONFIRMED** — 0.95 mm, leaded |
| 25 | "4-channel 5V array" | `bom.csv:103` | **CONFIRMED** — CH = 4, up to 5 VDC |
| 26 | `SCLK, MOSI, CS + spare` to one common | `carrier.md:825` | **CONFIRMED** — 4 channels, pin 2 common |
| 27 | **"0.98 W into SOT-23-6"** | prior review, cited `MANIFEST.csv:63` | **REFUTED — it is 0.225 W. Wrong by 4.4×** |
| 28 | "the power rating has never had a source" | `README.md:60`, `MANIFEST.csv:63` | **CONFIRMED, and now sourced** |
| 29 | Peak pulse power / I_PP / 8-20 µs waveform | asked by brief | **NOT-IN-DOCUMENT** — the part is ESD-rated only |
| 30 | Thermal resistance | asked by brief | **NOT-IN-DOCUMENT** |
| 31 | V_BR breakdown voltage | asked by brief | **NOT-IN-DOCUMENT** as a distinct spec |

---

# New open questions this wave created

For the lead. None of these existed before the documents were read.

1. **Where does the LT5400's exposed pad go?** (F-3) The datasheet *requires* a
   decision — "a quiet AC ground", explicitly **not** a noisy ground — and the
   coupling is 5.5 pF onto the 1 V/oct node. `bom.csv` did not know it had a pad, so
   nothing in the corpus says where it lands. **Layout-blocking in its own right,
   after the footprint is fixed.**
2. **Is there an ESD clamp between the pitch output jack and the LT5400?** (F-12)
   The part has **no internal ESD diodes** and only ±1 kV HBM, and feedback is
   tapped at the jack. The datasheet's own named remedy is `BAV99`, which Woody
   already stocks. Needs a schematic trace I did not perform.
3. **SOT-23-5 or switch to `SP0505BAHTG`?** (F-14) Both are defensible; the second
   gives a 5th channel in the SOT-23-6 the repo already thinks it has.
4. **A-grade's real matching over temperature is ±0.0125 %, not ±0.01 %** (F-8),
   and A/B parts are visually identical out of the reel (F-6).
5. **The 0.98 W line should be deleted, not corrected** (F-17) — there is no
   peak-pulse rating to replace it with.

---

# Routes tried and their exact results

## LT5400 — SUCCEEDED on the 3rd URL

| URL | Result |
|---|---|
| `https://www.analog.com/media/en/technical-documentation/data-sheets/5400fc.pdf` | **HTTP 000**, empty reply. Retried with `--http1.1`, with `--tlsv1.2 --http1.1`, browser UA, and after a pause. Failed every time. Origin-side, consistent with the brief's note |
| `https://www.analog.com/media/en/technical-documentation/data-sheets/5400fa.pdf` | **HTTP 000**, empty reply |
| `https://www.analog.com/media/en/technical-documentation/data-sheets/LT5400.pdf` | **HTTP 000**, empty reply |
| `https://www.arrow.com/en/products/lt5400acms8e-1%23pbf/analog-devices` | **HTTP 403** |
| **`https://docs.rs-online.com/e83c/0900766b8109be20.pdf`** | **HTTP 200, 225 068 bytes, `%PDF`. ✅ BANKED** |

**The brief's RS-mirror warning did not fire.** The repo recorded this URL as "rev fa
mirrored at ..." and it is genuinely the LT5400: PDF title `LT5400 - Quad Matched
Resistor Network`, 83 occurrences of `LT5400`, **zero** occurrences of `LT4256`. The
mislabelling that caught the LT1641 is not present here. **Verified by hand, as
`CLAUDE.md` asks.**

**What remains genuinely BLOCKED: rev `fc` specifically.** Only claim 16/17 (the
`-7` / 1:4 options) depend on it.

## SP0504BAHT — SUCCEEDED on the 1st URL

| URL | Result |
|---|---|
| **`https://www.farnell.com/datasheets/47249.pdf`** | **HTTP 200, 330 885 bytes, `%PDF`. ✅ BANKED** |
| `https://datasheet.lcsc.com/lcsc/1811081119_Littelfuse-SP0504BAHTG_C129412.pdf` | HTTP 200 but body is **`<!doctype html>`** — an HTML page with a `.pdf` filename, exactly the trap the brief warns about. Discarded |
| `https://www.littelfuse.com/assetdocs/littelfuse-tvs-diode-array-sp050xba-datasheet?assetguid=...` | **HTTP 403** |
| `https://m.littelfuse.com/media?resourcetype=datasheets&itemid=...` | **HTTP 403** |

**Note for the manifest:** `MANIFEST.csv:63` and `.manifest-R4.csv:12` both record
farnell.com as returning *"HTTP 000 connect_rejected at the egress proxy."*
**That is no longer true.** `www.farnell.com/datasheets/47249.pdf` — the exact URL
already listed in the BLOCKED row's `source_url` field — returned 200 on the first
attempt this session. The proxy's reachability changed, or the earlier probe was
transient. **Worth re-probing the other farnell URLs in BLOCKED rows.**

---

# Caveats on my own work

- **Rev fa, not fc.** Stated wherever it matters. Claims 16, 17 and 19 are affected;
  nothing else is.
- **The SP050xBA document carries no document number and no date.** It is a databook
  extract (pages 220–227). I could not establish its revision. Recorded in the
  manifest note.
- **The SP0504 pinout came from a rendered page image**, not text extraction — the
  diagram is vector art. I read it at 200 dpi and cross-checked against the 2-, 5-
  and 6-channel diagrams on the same page for internal consistency. Confidence high,
  but it is an image reading, not a text quote, and I am marking it as such.
- **I did not trace the schematic** for F-12 (BAV99 between jack and LT5400). I am
  filing it as a question, not a finding.
- **I edited no repo file** except adding the two PDFs. `MANIFEST.csv`, `bom.csv`,
  `figures.yaml` and every `.md` are untouched.
