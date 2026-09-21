# X5 — BOM ↔ schematic ↔ ADR reconciliation

**Date:** 2026-09-21
**Subject:** `hardware/bom.csv` against the five pages in `hardware/module/`, and
against `docs/decisions/`, in both directions.
**Method:** CSV parsed with Python's `csv` module (quoted `notes` fields contain
commas). Every claim below cites a file and a row or line.

## Mechanical check of the file — passes

`hardware/bom.csv` has 108 lines: 1 header + **107 data rows**, and **every row
parses to exactly 11 fields**. No short or long rows, no duplicate `ref` values,
no non-numeric `qty`. The header is
`ref,category,part,manufacturer,description,package,qty,status,source,adr,notes`
as specified. Nothing to report here.

Category split: module 48, controller 48, mechanical 10, tooling 1.

## Scope limit that shapes everything below

**Only 48 of 107 rows are checkable against a drawing.** The five pages in
`hardware/module/` cover the module only. `hardware/controller/` contains
nothing but `.gitkeep`, so the 48 `controller` rows, the 10 `mechanical` rows
and the 1 `tooling` row have no schematic to be reconciled against. That is a
gap in the drawing set, not a defect in those rows, and it is stated once here
rather than repeated 59 times in the tables.

---

## Table 1 — Parts drawn with no BOM row

| # | Part as drawn | Page / line | Why there is no row | Severity |
|---|---|---|---|---|
| 1 | **`C_T`** — LT1641 timer capacitor | `power-entry.md:33` `[C_T]`; the page sizes it at "**Timer ≈ 50 ms**" | No row anywhere. `grep -i "timer\|C_T" hardware/bom.csv` returns nothing. `U-LOADSW` (row 19) mentions "a programmed 50-100ms ramp" but buys no capacitor | **Missing part.** The load switch cannot be built |
| 2 | **BAV99 ×2** on the module-side `BREATH` / `AGND` legs | `breath-receive-stage.md:32` "BAV99 to ±12 V, both legs" | The only BAV99 row is `D-JACK-CLAMP` (row 52), described as "Clamp diodes on the **DRIVER side of R-OUT-PROT**" with qty 6 = one per CV **output**. These are **input** clamps at the receiver, a different location and a different count | **Missing part.** ~2 packages |
| 3 | Range resistors around **`TRIM-OFFSET`** | `pitch-stage.md:19` `[TRIM-OFFSET 10k]` + literal text "**+ range resistors**" | Row 106 buys the 10 kΩ pot only. Its note claims "Range ~50mV on a 2.5V reference", which a bare pot across `VREFOUT` cannot produce — it needs the range resistors the drawing names | **Missing part** |
| 4 | The divider inside **`TRIM-BREATH-ZERO`** | `breath-receive-stage.md` — "Range 0 to ~+0.6 V from `VREFOUT`" | Row 108's `part` field reads "10k multiturn cermet **+ divider**". Two components on one line; the divider's values appear nowhere | **Un-orderable line** (also Table 4) |
| 5 | Downstream breath **gain + offset** stage passives | `breath-receive-stage.md` — drawn as a block, "INVERTING gain + offset / POT-GAIN then POT-OFFSET / ½ OPA2197" | No rows for the summer's input, feedback or pot-terminating resistors. The pots themselves are `POT-BREATH` (row 17) | **Knowingly deferred** — the page's "Still open" assigns this to E10. Not an error, but it is unbuilt silicon |
| 6 | Power-on reset RC on the 74HC123 `CLR` | `digital-and-supervision.md` "Still open"; also `U-WATCHDOG` note (row 54) | No row | **Knowingly open** |
| 7 | **`R-CLR-PD`** | `digital-and-supervision.md:41`, `:137` | The BOM's ref is **`R-CLR-PU`** (row 71) — whose own `description` reads "Pull-**DOWN** on the DAC8568 CLR line" | **Designator mismatch, not a missing part.** The part exists; the reference name is a leftover from when it really was a pull-up. Rename the row to `R-CLR-PD` |
| 8 | LM317 **ADJ bypass** (10 µF) | `power-entry.md:22` draws only `[C 1µF]` on the LM317 output | `C-REG-ADJ` (row 40) buys both the 10 µF ADJ bypass and the 1 µF output cap | **Drawing omission, BOM correct.** The page under-draws by one cap |
| 9 | `C-FILT-PITCH` 10 nF C0G; `R-OFFINJ` 470 kΩ | `pitch-stage.md` "Component values" table | Both are **deleted** by the same page's prose ("**`C-FILT-PITCH` is deleted**"; "`R-OFFINJ` is deleted") and by `C-FB-PITCH`/`TRIM-OFFSET` notes (rows 107, 106) | **The page's table is stale; the BOM is right.** No BOM action — fix the page |

---

## Table 2 — Rows with no place

Distinguishing **dead** (delete) from **undrawn** (add to a drawing).

| Ref | Row | Verdict | Evidence |
|---|---|---|---|
| `U-OPA-GEN` | 14 | **Dead — but deliberate.** qty 0, `not-needed`, part "(none — OPA2197 used throughout)" | It is a tombstone recording that a second op-amp part was considered and rejected. Keeping it is defensible; if the project wants a clean order file, it is the one row that is pure history |
| `J-USB` | 29 | **Dead row with a live quantity.** `not-needed` but **qty 1** | Note: "Dev boards carry these. Only required if a custom MCU carrier is ever built". Should be **qty 0**, matching `U-OPA-GEN`'s precedent |
| `U-ESD-USB` | 30 | Same — `not-needed`, **qty 1** | Same note |
| `SW-BOOT` | 31 | Same — `not-needed`, **qty 2** | Same note. Also `part` = "TBD" |
| `U-TVS-MODULE` | 98 | **Undrawn, deliberately.** `open`, qty 1 | Note: "DELIBERATELY open, not forgotten… retrofittable… Fit at E12". Not on `digital-and-supervision.md`, correctly |
| `C-DECOUPLE` | 43 | **Undrawn, and it should be.** qty 19 | Decoupling is not drawn on any of the five pages. Normal practice — but it means the quantity has no drawing to be checked against, which is exactly how it drifted (Table 3) |
| `PANEL`, `PCB-MODULE`, `KNOB-BREATH` | 21, 74, 84 | **Not schematic items.** Panel, board and knob | No action |
| `BENCH` | 25 | **Not a part at all** — test equipment on a bill of materials | It carries `status: available`, a value outside the stated vocabulary (see §6). Harmless, but it is one of two rows that will never be ordered |
| 59 rows in `controller` / `mechanical` / `tooling` | — | **Unverifiable, not dead** | No instrument schematic exists. See "Scope limit" above |

**No row was found that is dead in the sense of "buys a component the design no
longer contains" other than the four listed above.** The sweep that produced
rows like `C-FB-PITCH` ("REPLACES `C-FILT-PITCH`") and `R-BIAS-INAMP`
("REPLACES `R-PD-BREATH`") appears to have removed the superseded rows rather
than leaving them behind.

---

## Table 3 — Quantity mismatches

| Ref | Row | BOM qty | Recount | The count that produces it |
|---|---|---|---|---|
| **`C-DECOUPLE`** | 43 | **19** | **22** | See arithmetic below |
| **`R-MODGAIN`** | 68 | **16** | **8** | `mod-channels.md` drawing: `R1 10k` + `R2 30k` per channel × 4 channels = 8. The row's own note says "**EIGHT, not sixteen**" — the note was updated and the `qty` field was not |
| **`U-OPA-PITCH`** | 13 | **6** | **5** | 9 halves drawn (below) → 5 packages, 1 spare half |
| **`R-OPAMP-IN`** | 51 | **7** | **6 drawn** | pitch ch1 (`pitch-stage.md:24`) 1 + mod signal inputs × 4 + mod offset buffer (`mod-channels.md:16`) 1 = 6. The 7th, on the `VREFOUT` follower, is **claimed in two notes but drawn nowhere** — `pitch-stage.md:19` runs `VREFOUT` straight through `TRIM-OFFSET` into the follower with no series resistor |
| **`D-JACK-CLAMP`** | 52 | **6** | **6 drawn as 5, plus 2 unrowed** | Outputs clamped in the drawings: pitch 1 + mods 4 = **5**. The breath output (`breath-receive-stage.md`, `[1k]─┴─[C 330nF]── BREATH jack`) has an `R-OUT-PROT` but **no clamp drawn**. Separately, the 2 input-side BAV99s (Table 1 #2) have no row. Either the qty is 5 and the breath output is deliberately unclamped, or the qty is 6 and the breath page is missing one — the back-powering argument in the row's note applies equally to the breath jack, so **6 is probably right and the drawing is wrong** |
| `J-USB` / `U-ESD-USB` / `SW-BOOT` | 29–31 | 1 / 1 / 2 | **0** | `status: not-needed` |
| `C-REF-OUT` | 79 | **2** | **1?** | One `U-REF-BREATH` (row 26, qty 1); `description` says "**Output** capacitor on the REF5050", singular. Nothing in the row explains the second. *Unverified* — no instrument schematic, and the REF50xx datasheet is proxy-blocked. If it is an input cap as well, say so in the row |
| `L-BUCK-IN` | 48 | **1** | **1 or 2 — undecided** | `U-BUCK` qty 2 ("ONE PER DEV BOARD"), `C-BUCK-IN` qty 2 ("One per buck"). If the LC is per-buck the inductor is 2; if it is one shared filter at the umbilical node, `C-BUCK-IN`'s "the C of `L-BUCK-IN`'s LC" is loose. *Flagged, not asserted* |
| `R-REG-SET` | 39 | **2** | **>2** | The row's own note says "**Buy a handful of neighbouring E96 values**" because R2 is bench-selected at E7. qty 2 buys the nominal pair only |

### Quantities recounted and found **correct** — no change

- **`R-OUT-PROT` = 6** ✓ (`bom.csv:42`). One per output: pitch (`pitch-stage.md:33`), mod 1–4 (`mod-channels.md:35`, ×4), breath (`breath-receive-stage.md`, the `[1k]` before the 330 nF). Six outputs, six resistors. **Matches the brief's expectation exactly.**
- **`D-REVPOL` = 3** ✓. `power-entry.md` draws `D1`, `D2`, `D3`; the +5 V pin explicitly gets none ("The bus +5 V pin gets no diode"). The row's note gives the same reasoning.
- **`FB-IN` = 4** ✓. `FB1`–`FB4` drawn: +12 V analog, +12 V umbilical, −12 V, +5 V.
- **`C-BULK-RAIL` = 4** ✓. `C1`–`C4` 47 µF drawn; the page states "**Entry bulk is 4 × 47 µF**".
- **`R-SPI-PULL` = 6** ✓. `digital-and-supervision.md` draws `[R-SPI-PULL ×3]` twice — cable side and DAC side.
- **Key-network rows = 21 each** ✓. `R-KEY-PU`, `R-KEY-SER`, `C-KEY` all 21, against `SW1-n` = 21 ("18 keys + 3 spares"), `config/key-layout.yaml` `counts.total: 18` (5+6+4+3), and `PCB-CARRIER`'s independent cross-check: "21 sets of `R-KEY-PU`/`R-KEY-SER`/`C-KEY`, which is **63 passives**" = 21 × 3. Three ways of counting agree.
- `J-CV` = 6, `C-FILT-MOD` = 4, `C-DECOUPLE-165` = 4, `C-DECOUPLE-CARRIER` = 7, `HDR-DEV` = 6, `R-PRESENCE` = 3, `C-FILT-BREATH` = 3 ✓ — each matches its own enumeration.

### `C-DECOUPLE` — the arithmetic

The row's method is "one per supply pin". Against the ICs **as the BOM specifies
them today**:

| IC | Row | Packages | Supply pins each | Total |
|---|---|---|---|---|
| OPA2197 on ±12 V | 13 | 6 | 2 | **12** |
| INA828 on ±12 V | 28 | 1 | 2 | 2 |
| DAC8568 (AVDD + DVDD) | 12 | 1 | 2 | 2 |
| 74AHCT125 | 35 | 1 | 1 | 1 |
| 74HC123 | 54 | 1 | 1 | 1 |
| LT1641 V<sub>CC</sub> | 19 | 1 | 1 | 1 |
| LM317 input | 38 | 1 | 1 | 1 |
| **LM311 on ±12 V** | 99 | 1 | **2** | **2** |
| | | | | **22** |

The row's stored note computes: "5 x OPA2197 on +/-12V = 10, INA828 = 2,
DAC8568 AVDD+DVDD = 2, 74AHCT125, 74HC123, LT1641 VCC, LM317 in, **LM393**" =
10+2+2+1+1+1+1+1 = **19**. Two errors, both from parts that moved after the note
was written:

1. It uses **5** OPA2197 packages; `U-OPA-PITCH` (row 13) now says **6**. `power-entry.md:12` confirms "OPA2197 **×6**, INA828, LM311" on the analog rail. **+2**
2. It counts **`LM393`** at one supply pin. That part was replaced by the **LM311** (row 99: "LM311, NOT LM393"), which runs on **±12 V** — two pins — precisely so it can see a negative input. `digital-and-supervision.md` draws "LM311 / ±12 V". **+1**

**→ 22.** If `U-OPA-PITCH` is corrected to 5 (below), it becomes **20**. Either
way, **19 is wrong**, and the row still names a deleted part.

### `U-OPA-PITCH` — the arithmetic

Halves actually drawn across the three analog pages:

| Page | Halves | What |
|---|---|---|
| `pitch-stage.md` | 2 | `VREFOUT` follower; pitch amplifier |
| `mod-channels.md` | 5 | offset-channel follower; mod 1–4 |
| `breath-receive-stage.md` | 2 | `REF`-zero buffer; the downstream **inverting gain + offset** block |
| | **9** | |

9 halves → **5 packages (10 halves), one spare half.**

The row claims "Twelve halves, **eleven** used" and then enumerates: *pitch, mod
1-4, mod offset buffer, breath gain, breath offset, VREFOUT follower, breath
REF-zero buffer.* **That list has ten items, not eleven** — the row is off by one
against itself. It is off by a second one against the drawings, because it
counts "breath gain" and "breath offset" as two halves, where
`breath-receive-stage.md` draws them as **one** block labelled `½ OPA2197`, and
`U-DIFFRX` (row 28) independently says the downstream stage "does gain-then-offset
with two pots **in one op-amp half**".

So the row's stated justification for 6 — "Was 5 packages with zero spare" —
rests on a count of 10 used. At 9 used, 5 packages already leaves the spare the
row wants. **This needs a decision, not just an edit:** if the breath downstream
stage really is one half, qty is 5; if the author intends two halves there, the
note's "eleven" should read "ten" and 6 stands with two spare halves.

---

## Table 4 — Un-orderable rows

Rows that could not be handed to a distributor as written. **Network note: the
proxy blocks every distributor and vendor datasheet domain, so nothing below was
checked against a stock or parametric page.** Where orderability turns on that,
the row names the part and the parameter to check rather than a verdict.

| Ref | Row | Problem | What must be resolved |
|---|---|---|---|
| **`U-LOADSW`** | 19 | **Three components on one line**, one with no part number: "LT1641-1CS8 **+ DPAK/SO-8 N-FET + sense R**", qty 1. The FET is unspecified as to package *and* part; the "sense R" duplicates the separate `R-ILIM` row | Select an N-FET MPN against its **single-pulse SOA curve** at the page's sizing point — `power-entry.md` computes **12 W for 50 ms = 0.6 J**. Then split into three rows. **Datasheet check needed: analog.com / a FET vendor SOA curve — both blocked** |
| **`R-ILIM`** | 65 | `part` = "Sense resistor, **value from E6**". No value, no tolerance, no power rating, no part number. status `open` | `power-entry.md` already derives it: **R_SENSE = 50 mV / 1.0 A = 50 mΩ**, 18 mV / 6 mW at the 360 mA operating point. Put 50 mΩ in the row as the starting value with the bench-selection caveat, as `R-REG-SET` does |
| **`C-FILT-MOD`** | 67 | **82 nF C0G**, `package` = "**1210 or film - VERIFY**". Two package families on one line, neither confirmed. The row says so itself: "PACKAGE IS PROBABLY WRONG… almost certainly does not exist in 0805" | **Check needed: does 82 nF C0G/NP0 exist in 1210 at ≥16 V?** C0G volumetric efficiency makes this doubtful even at 1210. The row lists the fallbacks correctly (film, or raise the corner). *This is one of the two the brief expected; the 0805 has already been corrected out of the `package` field, but the row is still not orderable* |
| **`C-AA-ADC`** | 45 | **47 nF C0G/NP0** in **0805**. Same failure mode as `C-FILT-MOD`, one row earlier in the same family, and **not yet flagged in the row** | **Check needed: 47 nF C0G in 0805.** By the same C0G-density argument the row 67 note makes, this is very likely unavailable; 1206/1210 is the plausible package. *Same class of error, one that the 82 nF sweep did not reach* |
| **`C-FILT-BREATH`** | 63 | **15 nF C0G (diff) + 1.5 nF C0G (cm ×2)** in **0805** — two different values on one line, qty 3, and the 15 nF is again near the top of C0G density in 0805 | **Check needed: 15 nF C0G in 0805.** Split the line: 1 × 15 nF + 2 × 1.5 nF |
| **`C-OUT-BREATH`** | 64 | **330 nF film**, `package` = "**1206 or THT**". 330 nF in a 1206 *film* part (PPS/PEN) is well above the usual ceiling for that footprint | **Check needed: 330 nF film in 1206.** If unavailable, the row's own "or THT" is the answer — but then it is a through-hole part and the package field should say so |
| **`C-REG-ADJ`** | 40 | "**10uF / 1uF ceramic or tantalum**", `package` = "0805 / 1206". Two values, two dielectric families, two packages, qty 2 | Pick the dielectric — it matters: a ceramic 10 µF on an LM317 ADJ pin has a DC-bias and ESR story a tantalum does not. Then split into two rows with voltage ratings |
| **`R-PRECISION`** | 15 | "LT5400 **1:1 quad (four equal 10k), MSOP-8 option**" — **no option/suffix code**, so no orderable part number. The row states the gap, and `pitch-stage.md` repeats it in "Still open" | **Check needed: the LT5400 option table** — which option code is four-equal-10 kΩ in MS8, and which tolerance grade (A/B/C). **analog.com blocked** |
| **`TRIM-BREATH-ZERO`** | 108 | "10k multiturn cermet **+ divider**" — the divider that sets the 0 → +0.6 V range has no values | Specify the two range resistors, or split them out |
| **`U-TVS-MODULE`** | 98 | `part` = "**Same three groups, module end of the etherCON**", `package` = "**as above**", qty 1. Not a line anyone can buy | Deliberately `open`, and the row says why. Acceptable **provided it never leaves `open`** |
| **`FB-IN`** | 41 | "Ferrite bead **>=1A 600R@100MHz**", `package` = "1206 or 1210", no manufacturer, no series | `power-entry.md` is emphatic that the **series**, not the footprint, sets the rating — "within one vendor's 0805 600 Ω line there are 600 mA and 2.3 A versions". A generic description cannot be ordered safely. **Needs a specific series/MPN; vendor sites blocked** |
| **`J-UMBILICAL`** | 20 | "Neutrik etherCON D-series chassis (**variant TBD**)", qty 2 — and the two ends are different parts (module panel chassis vs. instrument tail on a backing plate) | Variant is scheduled for E12/M7. Until then not orderable, and `status: candidate` overstates it (§6) |
| **`C-BULK-DISP`** | 32 | `part` = "TBD", `package` = "**1206 / electrolytic THT**" — two mutually exclusive package families | Pick one |
| `PLATE-TOP`, `BODY-OAK`, `SIDE-ACRYLIC`, `PLATE-THUMB`, `MECH-BACKPLATE`, `MECH-THUMBREST`, `SW-BOOT` | 22–24, 88, 87, 89, 31 | `part` = **"TBD"** | Fabricated or deferred parts; listed for completeness. `PLATE-TOP` and `PLATE-THUMB` carry `status: candidate` over a TBD part, which is the status problem in §6 |

### Not un-orderable — checked and cleared

- **`U-DAC` (row 12) is now clean.** `part` = `DAC8568CIPW`, a complete orderable
  number, with "**GRADE LOCKED TO C**" and the full reasoning: the grade letter
  selects **reference gain** (A/B = gain 1 → 2.500 V FS; C/D = gain 2 → 5.000 V
  FS), so an A-grade part halves pitch to −2…+2.25 V, mods to ±5 V, and leaves
  channel 7 unable to reach 2.500 V at all. The row also captures the second,
  independent consequence — C clears to **zero** scale where B/D clear to
  **midscale** and would park pitch octaves up. *This is the second item the
  brief expected; it has been fixed.* The residual is a **datasheet confirmation
  against SBAS430 (ti.com blocked)**, which the row already records.
- **78 of 107 rows have an empty `manufacturer` field and 105 of 107 have an
  empty `source` field.** Most are generic passives where that is fine. It is
  noted as a fact about the file, not counted as 78 findings.

---

## 1. Schematic → BOM, page by page

### `power-entry.md`

| Drawn | BOM row | Match? |
|---|---|---|
| 16-pin shrouded keyed IDC (`J-PWR-EURO`) | 36 | ✓ |
| `D1`,`D2`,`D3` 1N5817 | 37 `D-REVPOL` qty 3, DO-41 | ✓ value, package, qty |
| `FB1`–`FB4` | 41 `FB-IN` qty 4 | ✓ qty; package/series un-orderable (Table 4) |
| `C1`–`C4` 47 µF | 80 `C-BULK-RAIL` 47 µF 25 V, qty 4 | ✓ |
| LM317LZ | 38 `U-REG-DAC` TO-92 | ✓ |
| 150R/475R 0.1 % | 39 `R-REG-SET` qty 2 | ✓ values; qty understates the bench buy |
| `[C 1µF]` on the LM317 output | 40 `C-REG-ADJ` qty 2 | Page draws 1 of 2; BOM correct |
| `R-ILIM` **50 mΩ** | 65 `R-ILIM` — *no value* | **✗** The page pins the value; the row does not carry it |
| LT1641-1 CS8 | 19 `U-LOADSW` | ✓ part and suffix; compound row |
| N-FET, **DPAK** | 19, same row | **✗** no part number; page and row agree it is DPAK/SO-8 and sized on SOA |
| `[C_T]` | — | **✗ no row** (Table 1) |
| panel toggle | 18 `SW-POWER` | ✓ |
| `R-OE-PU 10k` to **bus +5 V** | 101 `R-OE-PU` | **✗ rail conflict** — see §7 |
| `R-LED 820R` to bus +5 V, LED | 83 `R-LED-PANEL` 820R; 82 `LED-PANEL` | ✓ value and rail; the page's `(5.21 − 2.0)/4 mA ≈ 800 Ω → 820 Ω` matches the row's note |
| LM311 | 99 `U-PRESENCE` | ✓ |
| 74AHCT125 | 35 `U-LVL-MOD` | ✓ |
| "OPA2197 **×6**, INA828, LM311" on the analog rail | 13 qty 6 | Consistent with the BOM, **inconsistent with the 9 halves drawn** (Table 3) |

### `pitch-stage.md`

All drawn parts have rows: `TRIM-OFFSET` (106), `R-PRECISION` R1/R2 (15),
`R-OPAMP-IN` (51), `C-FB-PITCH` (107), `D-JACK-CLAMP` (52), `R-OUT-PROT` (53→42),
`TRIM-GAIN` (105), `J-CV` (16), `U-OPA-PITCH` halves (13).

Two value disagreements, and in **both the BOM is current and the page is stale**:

1. **`TRIM-GAIN`.** The drawing (`pitch-stage.md:37`) says `[TRIM-GAIN 200R]` and
   `bom.csv:105` says "**200R, not 1k**", computing 0 → **+2 %** of the ratio.
   But the same page's "Component values" table says "**1 kΩ** multiturn cermet"
   with "**0 → +5 %** of ratio", and its "Still open" section asks "**Whether
   `TRIM-GAIN` is 1 kΩ or 500 Ω**" — a question the BOM has already answered with
   a third number. 200 Ω in series with a 10 kΩ R2 is +2 % of the ratio, which is
   arithmetically what the BOM says and not what the table says.
2. **`R-OFFINJ` and `C-FILT-PITCH`** remain in the page's component table after
   the page's own prose deletes them. The BOM has correctly dropped both.

One drawing omission: the `VREFOUT` follower has **no `R-OPAMP-IN`** in the
drawing although two notes say it has one (Table 3).

### `mod-channels.md`

All drawn parts have rows. **The page contradicts itself twice, and the BOM
matches the drawing both times:**

| | Drawing | The page's "Values" table | BOM row 68 |
|---|---|---|---|
| R2 | **30 kΩ** | 40.2 kΩ | "R1=10k, **R2=30k** per channel" ✓ drawing |
| V_ref | **3.3333 V** | "V_OFF 2.500 V from DAC ch7" | "V_ref = **3.3333V** from the offset channel" ✓ drawing |
| Resulting span | ±10.000 V | ±10.05 V | "EXACTLY +-10.000V" ✓ drawing |

The Values table is the un-updated remains of the four-resistor version. The
BOM's `part` field ("10k / 30k 1% metal film") and note are correct; only its
`qty` (16, should be 8) was left behind.

`C-FILT-MOD` 82 nF ✓ qty 4 ✓; `D-JACK-CLAMP` and `R-OUT-PROT` ×4 ✓;
`R-OPAMP-IN` on ch2–ch5 and on the ch7 buffer ✓.

### `breath-receive-stage.md`

Instrument side all matched: `U-BREATH` (5), `U-REF-BREATH` (26), `U-BUF` (27),
`R-SER-BREATH-INST` R1 1 k (66), `R-ADCDIV` 0.6× (46), `C-AA-ADC` (45),
`U-ADC` (6).

Module side: `R-SER-BREATH` R2/R3 10 k 0.1 % (62) ✓ matched-pair note ✓;
`C-FILT-BREATH` C_diff 15 nF + C_cm 1.5 nF ×2 (63) ✓ qty 3 ✓;
`R-BIAS-INAMP` R4/R5 1 M (61) ✓; `U-DIFFRX` INA828 (28) ✓;
`R-GAIN-INAMP` 42.2 k (60) ✓ — the page's `G = 1 + 50k/42.2k = 2.185` and the
row's identical figure agree; `TRIM-BREATH-ZERO` (108) ✓;
`POT-BREATH` GAIN/OFFSET (17) ✓; `R-OUT-PROT` + `C-OUT-BREATH` 330 nF (64) ✓.

Two mismatches:

1. **The BAV99 input clamps have no row** (Table 1 #2).
2. **`U-DIFFRX`'s description is stale, and contradicts this page directly.**
   Row 28 reads "**REF ties HARD to module AGND - no divider**" and "Output is
   **-0.44V at rest** to -10V at full". The page has replaced that: `REF` is
   driven from a **buffered trimmer at +0.437 V**, and the in-amp "**rests at
   0 V and reaches −9.6 V at full**". The row also still says "The DAC ch6 zero
   injection that originally justified the input swap is deleted", which is
   consistent, but the `REF` sentence is the live contradiction. `TRIM-BREATH-ZERO`
   (108) describes the new arrangement correctly, so the BOM disagrees with itself.

### `digital-and-supervision.md`

All drawn parts have rows: `J-UMBILICAL` (20), `R-SPI-PULL` ×6 (49),
`U-LVL-MOD` (35), `U-DAC` (12), `R-CLR-PU`/`R-CLR-PD` (71),
`U-WATCHDOG` 74HC123 (54), `R-WDT` 1 M (69), `C-WDT` 220 nF (70) — `t ≈ 0.45·R·C
= 99 ms` agrees across page and both rows; `U-PRESENCE` LM311 (99),
`R-PRESENCE` incl. 1 M hysteresis (100), `R-OE-PU` (101), 820R + LED (83, 82).

**The page's own claim about the BOM is out of date.** It states: "**The BOM's
`R-PRESENCE` note still describes the old −200 mV arrangement and is wrong.**"
It no longer does — `bom.csv:100` now reads "Threshold ~+100mV, **POSITIVE** - no
negative reference needed. The earlier -200mV arrangement sensed the in-amp
OUTPUT, which stopped working the moment `TRIM-BREATH-ZERO` nulled the pedestal".
Meanwhile the page's **own drawing** still shows "threshold −200 mV (from −12 V)"
at line 52, which its prose then argues against. **Here the BOM is ahead of the
schematic**, and the schematic's accusation should be deleted along with its
drawing label.

---

## 5. The `adr` column

All 107 citations point at ADRs that exist (0001–0014; no 0010/0011/0012
citations, which is expected — layout-as-data, licensing and the config
interface buy no parts). Spot-checking each row's subject against its cited file
clears all but one family.

**The failing citations are the ESD protection rows.**

| Row | Ref | Cites | Finding |
|---|---|---|---|
| 95 | **`U-TVS-SPI`** | **0004** | `grep -iE "\bTVS\b\|ESD\|transient\|surge\|standoff" 0004-cv-interface-module.md` yields **one** hit — line 471, "A bare toggle would take that **surge** across its contacts", about the panel switch. **ADR 0004 never mentions ESD protection, a TVS array, or protecting the umbilical's signal lines.** It specifies the pinout, the pulls, the 220 Ω source termination and the cable — not this part |
| 98 | **`U-TVS-MODULE`** | **0004** | Same ADR, same absence |
| 96 | **`D-TVS-BREATH`** | **0003** | The same grep over `0003-breath-sensing-path.md` yields **one** hit — line 530, "the **ESD clamp**", referring to the **MCP3202's own internal input clamp** and the divider impedance feeding it. ADR 0003 discusses the BREATH conductor's *series protection resistor* and the +12 V-buffer decision at length, but **never specifies an ESD protection diode** |

For contrast, `D-TVS-PWR` (row 97, cites 0005) **is** covered:
`0005-power-architecture.md:195` draws "TVS array / LC filter at entry".

So the honest statement is not "one row cites the wrong ADR" but: **ESD
protection on the umbilical's signal lines has no ADR at all.** Three rows
(`U-TVS-SPI`, `U-TVS-MODULE`, `D-TVS-BREATH`) cite the ADR that governs the
*interface* they sit on, and each of those ADRs is silent on the *component*.
`U-TVS-SPI` is the sharpest case, because it carries the strongest reasoning in
its note ("REPLACES `U-TVS-UMB`, which named SP3012-06UTG: that part is obsolete
AND uDFN-14… banned by the ADR 0013 package policy") and that reasoning lives
**only** in the BOM. The fix is an ADR, not a citation edit.

Two citations that *look* wrong and are not, checked explicitly:

- `BENCH` (row 25) cites **0006** — covered, `0006:697` "Resolved — a full bench
  is available: oscilloscopes, logic analysers…".
- `C-OUT-BREATH` (row 64) cites **0006** for a breath part — covered,
  `0006:635` tabulates "Breath | 1 kΩ | 330 nF film | ~480 Hz".
- `C-DECOUPLE` (row 43) cites **0004** — covered, `0004:237` "100 nF ceramics at
  every IC".
- `R-OPAMP-IN` (row 51) cites **0006** — covered, `0006:668`, "**1 kΩ in series
  with each op-amp's non-inverting input where the DAC drives**".
- `KNOB-BREATH` (row 84) cites **0004** — covered, `0004:528`, "two breath knobs".

---

## 6. The `status` column

Values actually in use: `candidate` 77, `open` 18, `selected` 5, `not-needed` 4,
`purchased` 2, **`available` 1**.

**Outside the vocabulary:** `BENCH` (row 25) carries `status: available`. One row,
and it is the one row that is not a part.

### Understates a settled decision

These rows sit at `candidate` while the design has closed the question, usually
in the row's own capitalised note:

| Ref | Row | Why it is settled |
|---|---|---|
| `U-DAC` | 12 | "**GRADE LOCKED TO C**", full MPN, reset and gain behaviour argued through. → `selected` |
| `U-PRESENCE` | 99 | "**LM311, NOT LM393**", with the emitter-pin argument and two shipping precedents; `digital-and-supervision.md` reaches the same conclusion independently. → `selected` |
| `U-OPA-PITCH` | 13 | "**ONE op-amp part throughout the module**" — the package count is contested (Table 3), the part is not. → `selected` |
| `U-LVL-MOD` / `U-LVLSHIFT` | 35, 34 | 74AHCT125 fixed by ADR 0014 and ADR 0004, same part deliberately used twice. → `selected` |
| `U-KEYS` | 8 | "ALL FOUR ON THE CARRIER (ADR 0001)… Kept for its native 3V3 spec"; ADR 0001 settles 74LVC165A. → `selected` |
| `R-OUT-PROT` | 42 | Value, package and power rating all argued and fixed (1 kΩ, 1206, ≥250 mW). → `selected` |
| `D-REVPOL` | 37 | "**THREE not two**", with the ~80 mV / ~20 cents argument. → `selected` |
| `R-MODGAIN` | 68 | `mod-channels.md`: "Two resistors, not four — **settled**". → `selected` (after the qty fix) |
| `U-DIFFRX` | 28 | Already `selected` ✓ — correct, but the row's *content* is stale (§1) |

### Overstates a decision that is not made

| Ref | Row | Why `candidate` is too strong |
|---|---|---|
| `C-FILT-MOD` | 67 | The row's own note says "**PACKAGE IS PROBABLY WRONG**" and offers three fallbacks. A part that may not exist is not a candidate. → `open` |
| `J-UMBILICAL` | 20 | "variant TBD", "Variant decided at E12/M7". → `open` |
| `PLATE-TOP` | 22 | `part` = TBD and "**THICKNESS OPEN**", which `config/key-layout.yaml` confirms (`plate_thickness: null`, "OPEN, and it blocks M4/M5"). → `open` |
| `PLATE-THUMB` | 88 | `part` = "TBD - ~2mm", same geometry question as `PLATE-TOP`. → `open` |
| `BODY-OAK`, `SIDE-ACRYLIC` | 23, 24 | `part` = TBD. → `open` |
| `TRIM-GAIN` | 105 | The BOM says 200 Ω; `pitch-stage.md` lists the value under "Still open". Until that page is reconciled the value is contested. → `open`, or fix the page |
| `R-PRESENCE` | 100 | "Final values at E10", and the tap point itself is listed under "Still open" on `digital-and-supervision.md`. → `open` |
| `C-REG-ADJ` | 40 | Dielectric undecided (Table 4). → `open` |

### Quantity/status contradictions

`J-USB` (1), `U-ESD-USB` (1), `SW-BOOT` (2) are `not-needed` with non-zero
quantities. `U-OPA-GEN` (row 14) shows the right pattern: `not-needed`, **qty 0**.

---

## 7. One cross-cutting contradiction that belongs in no single table

**`R-OE-PU` (row 101) contradicts the schematics, the neighbouring BOM rows, and
itself.**

- Its `description` reads: "Pull-up from the **LM393** open collector **to bus +5V**".
- Its `notes` read: "Pull-up from the **LM311** open collector. **FROM THE
  LM317'S 5.21V, NOT BUS +5V**".

Those two fields disagree about the rail. Three other sources agree with the
`description` and against the `notes`:

- `power-entry.md` draws `bus +5V ──┬──[R-OE-PU 10k]──── OE ×4` and argues for it:
  pulling `OE` to a higher rail "would have dragged that node toward 12 V…into
  the 74AHCT125's input clamp".
- `digital-and-supervision.md`'s rail table assigns "`OE` pull-up and the LED →
  **bus +5 V**", with the fail-safe argument (rail dies → buffer unpowered →
  outputs off).
- `R-LED-PANEL` (row 83) says the LED resistor is on bus +5 V and "**Same rail as
  `R-OE-PU`**", and `U-PRESENCE` (row 99) says "**pull the collector to +5V**".

So four places say bus +5 V and one field of one row says 5.21 V. **The
`R-OE-PU` note is the stale one** — it is the argument from before the LED and
`OE` were found to share the comparator's collector node. The `LM393` in the
description is the same vintage. The row needs both fields rewritten; the
supervision-must-not-share-a-rail principle it is defending still applies to the
LM311 and the 74HC123, which the schematic correctly keeps on 5.21 V / ±12 V.

---

## Summary of actions

**BOM edits, high confidence:**

1. `C-DECOUPLE` qty 19 → **22** (or 20 if `U-OPA-PITCH` goes to 5); delete "LM393" from the note.
2. `R-MODGAIN` qty 16 → **8** — the note already says eight.
3. Rename `R-CLR-PU` → **`R-CLR-PD`** to match both drawings and its own description.
4. `J-USB`, `U-ESD-USB`, `SW-BOOT` qty → **0**.
5. Rewrite `R-OE-PU`'s description and note: **LM311**, **bus +5 V**.
6. Rewrite `U-DIFFRX`'s description: `REF` is a buffered trimmer at +0.437 V, output **0 V at rest to −9.6 V**.
7. Put **50 mΩ** in `R-ILIM`'s part field.
8. `BENCH` status `available` → one of the five allowed values (`not-needed` is the honest one).

**New rows needed:** `C_T` (LT1641 timer cap); 2 × BAV99 input clamps;
`TRIM-OFFSET` range resistors. Split `U-LOADSW` into three rows and
`C-REG-ADJ` / `C-FILT-BREATH` into two each.

**Decisions required before the BOM can be right:**

- `U-OPA-PITCH` 5 or 6 — turns on whether the breath downstream stage is one
  op-amp half or two.
- `D-JACK-CLAMP` 5 or 6 — turns on whether the breath output is clamped.
- `TRIM-GAIN` 200 Ω (BOM) or 1 kΩ (pitch page table).
- `R2` 30 kΩ / V_ref 3.3333 V (drawing + BOM) or 40.2 kΩ / 2.500 V (mod page
  table) — the BOM and the drawing already agree; the page table needs deleting.
- An ADR covering ESD protection on the umbilical signal lines.

**Blocked on the network, listed with the parameter to check:**

| Part | Parameter |
|---|---|
| 82 nF C0G (`C-FILT-MOD`) | Availability in 1210 at ≥16 V |
| 47 nF C0G (`C-AA-ADC`) | Availability in 0805 — probably not; find the real package |
| 15 nF C0G (`C-FILT-BREATH`) | Availability in 0805 |
| 330 nF film (`C-OUT-BREATH`) | Availability in 1206; otherwise THT |
| LT5400 (`R-PRECISION`) | Option code for 1:1 four-equal-10 kΩ in MS8, plus tolerance grade |
| LT1641 + N-FET (`U-LOADSW`) | FET single-pulse SOA at 12 W / 50 ms; LT1641 pin names and foldback network |
| Ferrite bead (`FB-IN`) | A series rated ≥1 A at 600 Ω@100 MHz — series, not footprint |
| DAC8568C (`U-DAC`) | SBAS430 confirmation of the grade → reference-gain mapping |
| REF5050 (`C-REF-OUT`) | Recommended output capacitance — does it justify qty 2? |
