# X5 — BOM ↔ schematic ↔ ADR reconciliation

**Date:** 2026-09-21
**Subject:** `hardware/bom.csv` against the five pages in `hardware/module/`, and
against `docs/decisions/`, in both directions.
**Method:** CSV parsed with Python's `csv` module (quoted `notes` fields contain
commas). Every claim below cites a file and a row or line number.

> **State note.** `hardware/bom.csv`, `pitch-stage.md` and `mod-channels.md` were
> all edited *while this review was being written* (mtime 03:48:47). Everything
> below describes the files **as they now stand**. Where a finding was resolved
> by that edit it is recorded in §0 rather than dropped, because two of the
> resolutions are exactly the recounts this review produced. `breath-receive-stage.md`
> was then edited again at 03:52 while §1 was being written; that revision is
> reflected below. This report is a **snapshot of a moving tree** — re-check the
> five pages' mtimes against `hardware/bom.csv` before acting on it.

## Mechanical check of the file — passes

`hardware/bom.csv` has 108 lines: 1 header + **107 data rows**, and **every row
parses to exactly 11 fields**. No short rows, no long rows, no duplicate `ref`
values, no non-numeric or empty `qty`. Header as specified. Re-verified after the
03:48 edit. Nothing to report here.

Category split: module 48, controller 48, mechanical 10, tooling 1.

## Scope limit that shapes everything below

**Only 48 of 107 rows are checkable against a drawing.** The five pages cover the
module. `hardware/controller/` contains nothing but `.gitkeep`, so the 48
`controller` rows, the 10 `mechanical` rows and the 1 `tooling` row have no
schematic to be reconciled against. That is a gap in the drawing set, not a
defect in those rows, and it is stated once here rather than repeated 59 times.

---

## 0. Resolved during this review

| Finding | State |
|---|---|
| `C-DECOUPLE` qty 19 → **22** | **Applied.** The row now reads 22 with the note "6 x OPA2197 on +/-12V = 12, INA828 = 2, **LM311 on +/-12V = 2**, DAC8568 AVDD+DVDD = 2, 74AHCT125, 74HC123, LT1641 VCC, LM317 in". That is the same arithmetic reached independently below (§3) |
| `R-MODGAIN` qty 16 → **8** | **Applied.** The `qty` field now agrees with the note that had said "EIGHT, not sixteen" all along |
| `pitch-stage.md` component table stale (`TRIM-GAIN` 1 kΩ, `R-OFFINJ`, `C-FILT-PITCH`) | **Applied.** Table now reads **200 Ω / +2 %**, `TRIM-OFFSET` + range resistors, `C-FB-PITCH` 1 nF, `R-OUT-PROT` 1206 ≥250 mW. Matches the BOM. **But the rest of the page was not swept — see §1** |
| `mod-channels.md` Values table stale (40.2 kΩ, V_OFF 2.500 V) | **Applied.** Now R2 = **30 kΩ**, V_ref = **3.3333 V**, "gain `1 + k` = exactly 4". Matches the drawing and the BOM. **But the rest of the page was not swept — see §1** |
| `R-OE-PU` note contradicted both schematics on the pull-up rail | **Applied to the note, not the description.** The note now correctly says bus +5 V and preserves the supervision-rail argument where it does apply. The `description` field **still reads "Pull-up from the `LM393` open collector"** — a part the BOM deleted |
| — | **New conflict introduced: `TRIM-BREATH-ZERO`'s source rail. See §1 and Table 1** |

---

## Table 1 — Parts drawn with no BOM row

| # | Part as drawn | Page / line | Why there is no row | Severity |
|---|---|---|---|---|
| 1 | **`C_T`** — LT1641 timer capacitor | `power-entry.md:33` `[C_T]`; the page sizes it: "**Timer ≈ 50 ms**", "must be longer than a current-limited start… **26 ms**" | No row anywhere. `grep -i "timer\|C_T" hardware/bom.csv` returns nothing. `U-LOADSW` mentions "a programmed 50-100ms ramp" but buys no capacitor | **Missing part.** The load switch cannot be built |
| 2 | **BAV99 ×2** on the module-side `BREATH` / `AGND` legs | `breath-receive-stage.md:32` "BAV99 to ±12 V, both legs" | The only BAV99 row is `D-JACK-CLAMP`, described as "Clamp diodes on the **DRIVER side of R-OUT-PROT**", qty 6 = one per CV **output**. These are **input** clamps at the receiver — different location, different count | **Missing part**, ~2 packages |
| 3 | **Range resistors** around `TRIM-OFFSET` | `pitch-stage.md:15` "+ range resistors"; `:131` now states it in the component table too — "10 kΩ multiturn cermet **+ range resistors**" | `TRIM-OFFSET` buys the 10 kΩ pot only. Its note claims "Range ~50mV on a 2.5V reference", which a bare pot across `VREFOUT` cannot produce | **Missing part.** The page asserts it twice now; the BOM still does not buy it |
| 4 | The divider inside **`TRIM-BREATH-ZERO`** | `breath-receive-stage.md:53` | `part` = "10k multiturn cermet **+ divider from the LM317 5.21V rail**". Two components on one line; the divider's values appear nowhere | **Un-orderable line** (Table 4) |
| 5 | Downstream breath **gain + offset** stage passives | `breath-receive-stage.md` — drawn as a block: "INVERTING gain + offset / POT-GAIN then POT-OFFSET / ½ OPA2197" | No rows for the summer's input, feedback or pot-terminating resistors. Only the pots exist (`POT-BREATH`) | **Knowingly deferred** to E10 by the page's "Still open". Not an error — but it is unbuilt circuit, and it is the block whose half-count drives §3 |
| 6 | Power-on reset RC on the 74HC123 `CLR` | `digital-and-supervision.md` "Still open"; `U-WATCHDOG` note says the same | No row | **Knowingly open** |
| 7 | **`R-CLR-PD`** | `digital-and-supervision.md:41`, `:137` | The BOM's ref is **`R-CLR-PU`** — whose own `description` reads "Pull-**DOWN** on the DAC8568 CLR line" | **Designator mismatch, not a missing part.** Rename the row to `R-CLR-PD` |
| 8 | LM317 **ADJ bypass** (10 µF) | `power-entry.md:22` draws only `[C 1µF]` on the LM317 output | `C-REG-ADJ` qty 2 buys both the 10 µF ADJ bypass and the 1 µF output cap | **Drawing omission; BOM correct** |
| 9 | `R-OPAMP-IN` on the `VREFOUT` follower | Not drawn — `pitch-stage.md:14` runs `VREFOUT` straight through `TRIM-OFFSET` into the follower | `R-OPAMP-IN` qty 7 counts it; `mod-channels.md` counts it too ("qty 7 covers pitch, the four mods, this buffer and the `VREFOUT` follower") | **Drawing omission**, assuming the BOM is right (§3) |

---

## Table 2 — Rows with no place

Distinguishing **dead** (delete) from **undrawn** (add to a drawing).

| Ref | Verdict | Evidence |
|---|---|---|
| `U-OPA-GEN` | **Dead — but deliberate.** qty 0, `not-needed`, part "(none — OPA2197 used throughout)" | A tombstone recording that a second op-amp part was considered and rejected. Keeping it is defensible; it is the one row that is pure history |
| `J-USB` | **Dead row with a live quantity.** `not-needed` but **qty 1** | "Dev boards carry these. Only required if a custom MCU carrier is ever built". Should be **qty 0**, following `U-OPA-GEN`'s precedent |
| `U-ESD-USB` | Same — `not-needed`, **qty 1** | Same note |
| `SW-BOOT` | Same — `not-needed`, **qty 2**; `part` also "TBD" | Same note |
| `U-TVS-MODULE` | **Undrawn, deliberately.** `open`, qty 1 | "DELIBERATELY open, not forgotten… retrofittable… Fit at E12". Correctly absent from `digital-and-supervision.md` |
| `C-DECOUPLE` | **Undrawn, and it should be.** qty 22 | Decoupling appears on none of the five pages. Normal practice — but it means the quantity had no drawing to be checked against, which is how it drifted to 19 in the first place |
| `PANEL`, `PCB-MODULE`, `KNOB-BREATH` | **Not schematic items** | Panel, board, knob. No action |
| `BENCH` | **Not a part at all** — test equipment on a bill of materials | Also carries `status: available`, outside the stated vocabulary (§6) |
| 59 rows in `controller` / `mechanical` / `tooling` | **Unverifiable, not dead** | No instrument schematic exists |

**No row was found that is dead in the sense of "buys a component the design no
longer contains", beyond the four above.** The sweep that produced rows like
`C-FB-PITCH` ("REPLACES `C-FILT-PITCH`") and `R-BIAS-INAMP` ("REPLACES
`R-PD-BREATH`") removed the superseded rows rather than leaving them behind.

---

## Table 3 — Quantity mismatches

| Ref | BOM qty | Recount | The count that produces it |
|---|---|---|---|
| **`U-OPA-PITCH`** | **6** | **5** | 9 halves drawn → 5 packages, 1 spare half. Arithmetic below |
| **`D-JACK-CLAMP`** | **6** | **5 drawn, + 2 unrowed** | Outputs clamped in the drawings: pitch 1 + mods 4 = **5**. The breath output (`breath-receive-stage.md`, `[1k]─┴─[C 330nF]── BREATH jack`) has an `R-OUT-PROT` but **no clamp drawn**. Separately the 2 input-side BAV99s have no row at all (Table 1 #2). The row's own back-powering argument ("254 mA across **six** jacks") applies to the breath jack too, so **6 is probably right and the breath page is missing one** |
| **`R-OPAMP-IN`** | **7** | **6 drawn** | pitch ch1 + mod signal inputs ×4 + mod offset buffer = 6. The 7th, on the `VREFOUT` follower, is claimed in two places and drawn in none (Table 1 #9) |
| `J-USB` / `U-ESD-USB` / `SW-BOOT` | 1 / 1 / 2 | **0** | `status: not-needed` |
| `C-REF-OUT` | **2** | **1?** | One `U-REF-BREATH` (qty 1); `description` says "**Output** capacitor on the REF5050", singular. Nothing explains the second. *Unverified* — no instrument schematic, REF50xx datasheet proxy-blocked. If it is an input cap too, say so |
| `L-BUCK-IN` | **1** | **1 or 2 — undecided** | `U-BUCK` qty 2 ("ONE PER DEV BOARD"), `C-BUCK-IN` qty 2 ("One per buck"). If the LC is per-buck the inductor is 2; if one shared filter sits at the umbilical node, `C-BUCK-IN`'s "the C of `L-BUCK-IN`'s LC" is loose. *Flagged, not asserted* |
| `R-REG-SET` | **2** | **>2** | The row says "**Buy a handful of neighbouring E96 values**" because R2 is bench-selected at E7. qty 2 buys the nominal pair only |

### Quantities recounted and found **correct** — no change

- **`R-OUT-PROT` = 6** ✓. One per output: pitch (`pitch-stage.md:33`), mod 1–4
  (`mod-channels.md:35` ×4), breath (`breath-receive-stage.md`, the `[1k]` ahead
  of the 330 nF). Six outputs, six resistors — **matches the brief's expectation
  exactly.**
- **`D-REVPOL` = 3** ✓. `power-entry.md` draws `D1`, `D2`, `D3`; the bus +5 V pin
  explicitly gets none ("The bus +5 V pin gets no diode… a reversed ribbon that
  kills the buffer and nothing else is an acceptable outcome").
- **`FB-IN` = 4** ✓. `FB1`–`FB4`: +12 V analog, +12 V umbilical, −12 V, +5 V.
- **`C-BULK-RAIL` = 4** ✓. `C1`–`C4` 47 µF; the page states "**Entry bulk is
  4 × 47 µF**" and worries about it in "Still open".
- **`R-SPI-PULL` = 6** ✓. `digital-and-supervision.md` draws `[R-SPI-PULL ×3]`
  twice, cable side and DAC side, and the page heading says so: "**six, not
  three**".
- **`C-DECOUPLE` = 22** ✓ *(as of the 03:48 edit)*. Arithmetic below.
- **`R-MODGAIN` = 8** ✓ *(as of the 03:48 edit)*. `mod-channels.md` drawing:
  `R1 10k` + `R2 30k` per channel × 4.
- **Key-network rows = 21 each** ✓. `R-KEY-PU`, `R-KEY-SER`, `C-KEY` all 21,
  against `SW1-n` = 21 ("18 keys + 3 spares"), `config/key-layout.yaml`
  `counts.total: 18` (left_hand 5 + right_hand 6 + left_thumb 4 + right_thumb 3),
  and `PCB-CARRIER`'s independent cross-check: "21 sets of
  `R-KEY-PU`/`R-KEY-SER`/`C-KEY`, which is **63 passives**" = 21 × 3. Three ways
  of counting agree. `SW-THUMB` qty 4 matches `counts.left_thumb: 4` and its note
  handles the interaction ("If taken, `SW1-n` drops by 4").
- `J-CV` = 6, `C-FILT-MOD` = 4, `C-DECOUPLE-165` = 4, `C-DECOUPLE-CARRIER` = 7,
  `HDR-DEV` = 6, `R-PRESENCE` = 3, `C-FILT-BREATH` = 3 ✓ — each matches its own
  enumeration.

### `C-DECOUPLE` — the arithmetic

The row's method is "one per supply pin". Against the ICs **as the BOM specifies
them now**:

| IC | Packages | Supply pins each | Total |
|---|---|---|---|
| OPA2197 on ±12 V (`U-OPA-PITCH`) | 6 | 2 | **12** |
| INA828 on ±12 V (`U-DIFFRX`) | 1 | 2 | 2 |
| **LM311 on ±12 V** (`U-PRESENCE`) | 1 | **2** | **2** |
| DAC8568 (AVDD + DVDD) | 1 | 2 | 2 |
| 74AHCT125 (`U-LVL-MOD`) | 1 | 1 | 1 |
| 74HC123 (`U-WATCHDOG`) | 1 | 1 | 1 |
| LT1641 V<sub>CC</sub> (`U-LOADSW`) | 1 | 1 | 1 |
| LM317 input (`U-REG-DAC`) | 1 | 1 | 1 |
| | | | **22** |

The two terms that had drifted: the row previously assumed **5** OPA2197
packages where `U-OPA-PITCH` says 6 (`power-entry.md:12` confirms "OPA2197 **×6**,
INA828, LM311" on the analog rail), and it counted **`LM393`** at one supply pin
where the part is now an **LM311 on ±12 V** — two pins, and it runs on ±12 V
precisely so it can see a negative input (`U-PRESENCE`;
`digital-and-supervision.md` draws "LM311 / ±12 V").

**This now reads 22 in the file.** Note the dependency: if `U-OPA-PITCH` is
corrected to 5 packages, `C-DECOUPLE` becomes **20**. The two rows must move
together, and nothing in either row says so.

### `U-OPA-PITCH` — the arithmetic

Halves actually drawn across the three analog pages:

| Page | Halves | What |
|---|---|---|
| `pitch-stage.md` | 2 | `VREFOUT` follower; pitch amplifier |
| `mod-channels.md` | 5 | offset-channel follower; mod 1–4 |
| `breath-receive-stage.md` | 2 | `REF`-zero buffer; the downstream **inverting gain + offset** block |
| | **9** | |

9 halves → **5 packages (10 halves), one spare half.**

The row claims "Twelve halves, **eleven** used" and enumerates: *pitch, mod 1-4,
mod offset buffer, breath gain, breath offset, VREFOUT follower, breath REF-zero
buffer.* **That list has ten items, not eleven** — the row is off by one against
itself. It is off by a second one against the drawings, because it counts "breath
gain" and "breath offset" as two halves, where `breath-receive-stage.md` draws
them as **one** block labelled `½ OPA2197`, and `U-DIFFRX` independently says the
downstream stage "does gain-then-offset with two pots **in one op-amp half**".

The row's stated justification for 6 — "Was 5 packages with zero spare" — needs
10 halves used. At 9, five packages already leave the spare the row wants.

**This is a decision, not an edit.** Either the breath downstream stage is one
half (→ `U-OPA-PITCH` 5, `C-DECOUPLE` 20) or it is two (→ the note's "eleven"
should read "ten", 6 stands with two spare halves, `C-DECOUPLE` 22). The
schematic and one other BOM row currently say one half; the `U-OPA-PITCH` note is
alone in saying two. **It cannot be settled without deciding what the E10 block
actually is**, which is Table 1 #5.

---

## Table 4 — Un-orderable rows

**Network note: the proxy blocks every distributor and vendor datasheet domain.
Nothing below was checked against a stock page or a parametric search.** Where
orderability turns on that, the row names the part and the parameter to check
rather than asserting a verdict.

| Ref | Problem | What must be resolved |
|---|---|---|
| **`U-LOADSW`** | **Three components on one line**, one with no part number: "LT1641-1CS8 **+ DPAK/SO-8 N-FET + sense R**", qty 1. The FET is unspecified as to package *and* part; the "sense R" duplicates the separate `R-ILIM` row | Select an N-FET MPN against its **single-pulse SOA curve** at the page's sizing point — `power-entry.md` computes **12 W for 50 ms = 0.6 J**, and is explicit that "SOA is the only specification that matters" here. Then split into three rows. **Blocked: analog.com and FET vendor SOA curves** |
| **`R-ILIM`** | `part` = "Sense resistor, **value from E6**". No value, no tolerance, no power rating, no part number | `power-entry.md` already derives it: **R_SENSE = 50 mV / 1.0 A = 50 mΩ**, 18 mV / 6 mW at 360 mA. Put 50 mΩ in the row as the starting value with the bench-selection caveat, exactly as `R-REG-SET` does |
| **`C-FILT-MOD`** | **82 nF C0G/NP0**, `package` = "**1210 or film - VERIFY**". Two package families on one line, neither confirmed. The row says so itself: "PACKAGE IS PROBABLY WRONG… almost certainly does not exist in 0805" | **Check: does 82 nF C0G/NP0 exist in 1210 at ≥16 V?** C0G volumetric density makes it doubtful even at 1210. The fallbacks the row lists (film, or raise the corner) are the right ones. *One of the two the brief expected — the 0805 has been corrected out of the `package` field, but the row is still not orderable* |
| **`C-AA-ADC`** | **47 nF C0G/NP0** in **0805** — and **the row does not flag it** | **Check: 47 nF C0G in 0805.** By the same density argument `C-FILT-MOD` makes one row later in the same file, this is very likely unavailable; 1206/1210 is the plausible package. *Same class of error; the 82 nF sweep did not reach it* |
| **`C-FILT-BREATH`** | **15 nF C0G (diff) + 1.5 nF C0G (cm ×2)** in **0805** — two values on one line, qty 3, and 15 nF is again near the top of C0G density in 0805 | **Check: 15 nF C0G in 0805.** Split the line: 1 × 15 nF + 2 × 1.5 nF. The 10:1 ratio is load-bearing (the page: "C_diff must be ~10x C_cm or a CM mismatch converts to DM"), so the two values must not drift apart on one line |
| **`C-OUT-BREATH`** | **330 nF film**, `package` = "**1206 or THT**". 330 nF in a 1206 *film* part is well above the usual ceiling for that footprint | **Check: 330 nF film in 1206.** If unavailable the row's own "or THT" is the answer — but then it is a through-hole part and the package field should say so and nothing else |
| **`C-REG-ADJ`** | "**10uF / 1uF ceramic or tantalum**", `package` = "0805 / 1206". Two values, two dielectric families, two packages, qty 2 | Pick the dielectric — it matters: a ceramic 10 µF on an LM317 ADJ pin has a DC-bias and ESR story a tantalum does not. Then split into two rows with voltage ratings |
| **`R-PRECISION`** | "LT5400 **1:1 quad (four equal 10k), MSOP-8 option**" — **no option/suffix code**, so no orderable part number. The row states the gap; `pitch-stage.md` repeats it in "Still open" | **Check: the LT5400 option table** — which option code is four-equal-10 kΩ in MS8, and which tolerance grade. **analog.com blocked** |
| **`TRIM-BREATH-ZERO`** | "10k multiturn cermet **+ divider from the LM317 5.21V rail**" — the divider that sets the 0 → +0.6 V range has no values | Specify the two range resistors, or split them out. Same shape as `TRIM-OFFSET`'s missing range resistors |
| **`U-TVS-MODULE`** | `part` = "**Same three groups, module end of the etherCON**", `package` = "**as above**", qty 1. Not a line anyone can buy | Deliberately `open`, and the row says why. Acceptable **provided it never leaves `open`** |
| **`FB-IN`** | "Ferrite bead **>=1A 600R@100MHz**", `package` = "1206 or 1210", no manufacturer, no series | `power-entry.md` is emphatic that the **series**, not the footprint, sets the rating: "within one vendor's 0805 600 Ω line there are 600 mA and 2.3 A versions, and another '600' part is 60 Ω at 3 A. **Read the series, not the footprint.**" A generic description cannot be ordered safely. **Blocked: vendor series data** |
| **`J-UMBILICAL`** | "Neutrik etherCON D-series chassis (**variant TBD**)", qty 2 — and the two ends are different parts (module panel chassis vs. instrument tail on a backing plate) | Variant is scheduled for E12/M7. Until then not orderable, and `status: candidate` overstates it (§6) |
| **`C-BULK-DISP`** | `part` = "TBD", `package` = "**1206 / electrolytic THT**" — two mutually exclusive package families | Pick one |
| `PLATE-TOP`, `BODY-OAK`, `SIDE-ACRYLIC`, `PLATE-THUMB`, `MECH-BACKPLATE`, `MECH-THUMBREST`, `SW-BOOT` | `part` = **"TBD"** | Fabricated or deferred parts, listed for completeness. `PLATE-TOP` and `PLATE-THUMB` carry `status: candidate` over a TBD part — the status problem in §6 |

### Not un-orderable — checked and cleared

- **`U-DAC` is now clean.** `part` = `DAC8568CIPW`, a complete orderable number,
  with "**GRADE LOCKED TO C**" and the full reasoning: the grade letter selects
  **reference gain** (A/B = gain 1 → 2.500 V FS; C/D = gain 2 → 5.000 V FS), so
  an A-grade part halves pitch to −2…+2.25 V, mods to ±5 V, and leaves channel 7
  unable to reach 2.500 V at all. It also captures the independent second
  consequence — C clears to **zero** scale where B/D clear to **midscale** and
  would park pitch octaves up. *This is the second item the brief expected; it is
  fixed.* Residual: **datasheet confirmation against SBAS430 (ti.com blocked)**,
  which the row already records.
- **78 of 107 rows have an empty `manufacturer` and 105 of 107 an empty
  `source`.** Mostly generic passives, where that is fine. Recorded as one fact
  about the file, not 78 findings.

---

## 1. Schematic → BOM, page by page

### `power-entry.md`

| Drawn | BOM row | Match? |
|---|---|---|
| 16-pin shrouded keyed IDC | `J-PWR-EURO` | ✓ |
| `D1`,`D2`,`D3` 1N5817 | `D-REVPOL` qty 3, DO-41 | ✓ value, package, qty |
| `FB1`–`FB4` | `FB-IN` qty 4 | ✓ qty; series un-orderable (Table 4) |
| `C1`–`C4` 47 µF | `C-BULK-RAIL` 47 µF 25 V qty 4 | ✓ |
| LM317LZ | `U-REG-DAC` TO-92 | ✓ |
| 150R/475R 0.1 % | `R-REG-SET` qty 2 | ✓ values; qty understates the bench buy |
| `[C 1µF]` on the LM317 output | `C-REG-ADJ` qty 2 | Page draws 1 of 2; BOM correct |
| `R-ILIM` **50 mΩ** | `R-ILIM` — *no value* | **✗** The page pins the value; the row does not carry it |
| LT1641-1 CS8 | `U-LOADSW` | ✓ part and suffix (`-1` latching, argued on both page and row); compound row |
| N-FET, **DPAK** | `U-LOADSW`, same line | **✗** no part number. Page and row agree it is DPAK/SO-8 sized on SOA |
| `[C_T]` | — | **✗ no row** |
| panel toggle | `SW-POWER` | ✓ signal-level only, both agree |
| `R-OE-PU 10k` → **bus +5 V** | `R-OE-PU` | ✓ **as of 03:48** (note fixed); `description` still names LM393 |
| `R-LED 820R` → bus +5 V, LED | `R-LED-PANEL`, `LED-PANEL` | ✓ The page's `(5.21 − 2.0)/4 mA ≈ 800 Ω → 820 Ω` matches the row's note verbatim |
| LM311 | `U-PRESENCE` | ✓ |
| 74AHCT125 | `U-LVL-MOD` | ✓ |
| "OPA2197 **×6**, INA828, LM311" on the analog rail | `U-OPA-PITCH` qty 6 | Consistent with the BOM, **inconsistent with the 9 halves drawn** (§3) |

### `pitch-stage.md`

Every drawn part has a row: `TRIM-OFFSET`, `R-PRECISION` (R1/R2), `R-OPAMP-IN`,
`C-FB-PITCH`, `D-JACK-CLAMP`, `R-OUT-PROT`, `TRIM-GAIN`, `J-CV`, `U-OPA-PITCH`
halves. After the 03:48 edit the **component table agrees with the BOM on every
value** — 200 Ω trimmer, +2 % of ratio, 1206 ≥250 mW, `C-FB-PITCH` 1 nF,
`R-OFFINJ` and `C-FILT-PITCH` gone.

**The edit did not sweep the rest of the page.** Three places still carry the
1 kΩ / ±5 % trimmer:

- `:208` — "that error is what the gain trim's **±5 %** range exists to absorb"
- `:213` — the accuracy table: "Cermet at ~100 ppm/°C contributing **~5 %** of
  the ratio", which is what makes that row's "0.4–2.4 cents" figure the largest
  line on the page. At 200 Ω it is 2 % of the ratio, so **the headline accuracy
  number on this page is computed from the superseded value**
- `:229` — "Still open: **Whether `TRIM-GAIN` is 1 kΩ or 500 Ω.** ±5 % of a
  10 kΩ ratio wants ~1 kΩ" — a question the table and the BOM have both answered
  with a third number

**Drawing omission:** the `VREFOUT` follower has no `R-OPAMP-IN`, though the BOM
and `mod-channels.md` both count one (Table 1 #9).

### `mod-channels.md`

Every drawn part has a row. After the 03:48 edit the Values table agrees with the
drawing and the BOM: R1 = 10 kΩ, **R2 = 30 kΩ**, **V_ref = 3.3333 V**, gain
exactly 4, span exactly ±10.000 V.

**The edit did not sweep the rest of the page**, which still computes in the
superseded 40.2 kΩ / gain-4.02 world:

- `:132` — "**±10.05 V** uses the DAC's *full* 0–5 V span"
- `:146` — "`Vout = 4.02 × (0 − 0) = 0 V`"
- `:152` — "`4.02 × (0 − 2.5) = −10.05 V`"
- `:157` — "pins the jacks at `4.02 × Vdac` ≈ **+11.45 V**"

None of these change the *conclusions* they support (0 V on `CLR`; a rail on a
half-refresh), and none affects a BOM row — `R-MODGAIN` is correct at 8 × 10 k/30 k.
Recorded so the numbers get swept, not because a part is wrong.

### `breath-receive-stage.md`

Instrument side all matched: `U-BREATH`, `U-REF-BREATH`, `U-BUF`,
`R-SER-BREATH-INST` (R1 1 k), `R-ADCDIV` (0.6×), `C-AA-ADC`, `U-ADC`.

Module side matched: `R-SER-BREATH` (R2/R3 10 k 0.1 %, matched-pair note ✓),
`C-FILT-BREATH` (C_diff 15 nF + C_cm 1.5 nF ×2, qty 3 ✓), `R-BIAS-INAMP`
(R4/R5 1 M ✓), `U-DIFFRX` (INA828), `R-GAIN-INAMP` (42.2 k — the page's
`G = 1 + 50k/42.2k = 2.185` and the row's figure agree exactly),
`TRIM-BREATH-ZERO`, `POT-BREATH` (GAIN/OFFSET), `R-OUT-PROT` + `C-OUT-BREATH`.

Three mismatches:

1. **The BAV99 input clamps have no row** (Table 1 #2).
2. **`U-DIFFRX`'s description is stale and contradicts this page directly.** The
   row reads "**REF ties HARD to module AGND - no divider**" and "Output is
   **-0.44V at rest** to -10V at full". The page has replaced both: `REF` is
   driven from a **buffered trimmer at +0.437 V**, and the in-amp "**rests at
   0 V and reaches −9.6 V at full**". `TRIM-BREATH-ZERO` describes the new
   arrangement correctly, so **the BOM disagrees with itself** about what drives
   the `REF` pin. `U-DIFFRX` carries `status: selected`, which makes the stale
   text more likely to be believed, not less.
3. **`TRIM-BREATH-ZERO`'s source rail — BOM and page prose now agree, the
   drawing does not.** The row reads "divider **from the LM317 5.21V rail**…
   **FROM THE LM317'S 5.21V, NOT VREFOUT**", because `VREFOUT` is the DAC's
   internal reference and is **disabled at power-on until firmware writes an
   enable** — which `U-DAC` independently confirms ("Internal ref DISABLED by
   default, enable at boot"). The page's component table (`:149`) now says the
   same: "From the LM317 rail, never `VREFOUT`". **But the drawing still says
   otherwise** — `:53–54`, "`½ OPA2197 ◄─[TRIM-BREATH-ZERO]` buffered **from
   VREFOUT**" — and `:240` still calls "the buffered `VREFOUT` created for
   pitch" the obvious node for the downstream stage's offset reference, which
   has exactly the same power-on problem. Fix the ASCII drawing and `:240`.
4. **`TRIM-BREATH-ZERO`'s range — the page moved, the BOM did not.** The page
   now specifies **0 → +1.0 V** (`:87`, `:149`) on a good argument: the
   MPXV4006DP's pedestal is a **spec band, not a number** (0.152–0.378 V),
   needing `REF` anywhere from 0.332 V to 0.826 V, so the old 0 → +0.6 V "covers
   pedestals only to 0.275 V" and a sensor at the top of its own datasheet band
   would have been un-nullable. The BOM row still reads "**Range 0 to ~+0.6V**".
   **The page is right and the row is one edit behind.** This matters
   dimensionally, not just editorially: the range is set by the divider
   resistors the row does not specify (Table 1 #4), so the BOM number is the one
   someone would build from.

### `digital-and-supervision.md`

Every drawn part has a row: `J-UMBILICAL`, `R-SPI-PULL` ×6, `U-LVL-MOD`,
`U-DAC`, `R-CLR-PU`/`R-CLR-PD`, `U-WATCHDOG` (74HC123), `R-WDT` 1 M, `C-WDT`
220 nF — `t ≈ 0.45·R·C = 99 ms` agrees across the page and both rows —
`U-PRESENCE` (LM311), `R-PRESENCE` including the 1 M hysteresis, `R-OE-PU`,
820R + LED.

**The page's accusation against the BOM is out of date.** It states: "**The
BOM's `R-PRESENCE` note still describes the old −200 mV arrangement and is
wrong.**" It no longer does — `R-PRESENCE` now reads "Threshold ~+100mV,
**POSITIVE** - no negative reference needed. The earlier -200mV arrangement
sensed the in-amp OUTPUT, which stopped working the moment `TRIM-BREATH-ZERO`
nulled the pedestal and put both states at 0V." Meanwhile the page's **own
drawing** still labels "threshold −200 mV (from −12 V)" at `:52`, which its own
prose then argues against. **Here the BOM is ahead of the schematic**, and both
the drawing label and the accusation should go.

---

## 5. The `adr` column

All 107 citations point at ADRs that exist (0001–0014). No row cites 0010, 0011
or 0012, which is right — layout-as-data, licensing and the config interface buy
no parts. Checking each row's subject against the text of its cited file clears
all but one family.

**The failing citations are the ESD protection rows.**

| Ref | Cites | Finding |
|---|---|---|
| **`U-TVS-SPI`** | **0004** | `grep -icE "\bTVS\b\|ESD\|transient\|surge\|standoff"` over `0004-cv-interface-module.md` returns **1** — line 471, "A bare toggle would take that **surge** across its contacts", about the panel switch. **ADR 0004 never mentions ESD protection, a TVS array, or protecting the umbilical's signal lines.** It specifies the pinout, the idle pulls, the 220 Ω source termination and the cable — not this part |
| **`U-TVS-MODULE`** | **0004** | Same ADR, same absence |
| **`D-TVS-BREATH`** | **0003** | The same grep over `0003-breath-sensing-path.md` returns **1** — line 530, "the **ESD clamp**", meaning the **MCP3202's own internal input clamp** and the divider impedance feeding it. ADR 0003 discusses the BREATH conductor's *series protection resistor* and the +12 V-buffer decision at length and **never specifies an ESD protection diode** |

For contrast `D-TVS-PWR` (cites 0005) **is** covered:
`0005-power-architecture.md:195` draws "TVS array / LC filter at entry".

So the accurate statement is not "one row cites the wrong ADR" but: **ESD
protection on the umbilical's signal lines has no ADR at all.** Three rows cite
the ADR that governs the *interface* they sit on, and each of those ADRs is
silent on the *component*. `U-TVS-SPI` is the sharpest case, because its note
carries the strongest reasoning in the set — "REPLACES `U-TVS-UMB`, which named
SP3012-06UTG: that part is obsolete AND uDFN-14, not the SOT-23-6 the row
claimed — leadless fine pitch, banned by the ADR 0013 package policy" — and that
reasoning lives **only** in the BOM. The fix is an ADR, not a citation edit.

Citations that *look* wrong and are not, checked explicitly so they are not
re-flagged later:

- `BENCH` → 0006: covered, `0006:697` "Resolved — a full bench is available:
  oscilloscopes, logic analysers…"
- `C-OUT-BREATH` → 0006 (a breath part on the CV-allocation ADR): covered,
  `0006:635` tabulates "Breath | 1 kΩ | 330 nF film | ~480 Hz"
- `C-DECOUPLE` → 0004: covered, `0004:237` "100 nF ceramics at every IC"
- `R-OPAMP-IN` → 0006: covered, `0006:668` "**1 kΩ in series with each op-amp's
  non-inverting input where the DAC drives**"
- `KNOB-BREATH` → 0004: covered, `0004:528` "two breath knobs"
- `R-KEY-PU` / `C-KEY` / `R-KEY-SER` → 0001: covered, `0001:171` "**the inputs
  need pull-ups, and there were none**" and `0001:241` on the filter
- `U-LVL-MOD` → 0004: covered and **already corrected once** — its note records
  "Cited 0006 before, which never mentions a level shifter". That is the same
  defect as the TVS rows, caught previously; the sweep did not reach the ESD rows

---

## 6. The `status` column

In use: `candidate` 77, `open` 18, `selected` 5, `not-needed` 4, `purchased` 2,
**`available` 1**.

**Outside the vocabulary:** `BENCH` carries `status: available` — one row, and
it is the one row that is not a part.

### Understates a decision that is settled

At `candidate` while the question has closed, usually in the row's own
capitalised note:

| Ref | Why it is settled |
|---|---|
| `U-DAC` | "**GRADE LOCKED TO C**", full MPN, reset and reference-gain behaviour argued through. → `selected` |
| `U-PRESENCE` | "**LM311, NOT LM393**", with the emitter-pin argument and two shipping precedents; `digital-and-supervision.md` reaches the same conclusion independently. → `selected` |
| `U-OPA-PITCH` | "**ONE op-amp part throughout the module**" — the package *count* is contested (§3), the *part* is not. → `selected` |
| `U-LVL-MOD`, `U-LVLSHIFT` | 74AHCT125 fixed by ADR 0014 and ADR 0004; the same part deliberately used twice. → `selected` |
| `U-KEYS` | "ALL FOUR ON THE CARRIER (ADR 0001)… Kept for its native 3V3 spec"; ADR 0001 settles 74LVC165A. → `selected` |
| `R-OUT-PROT` | Value, package and power rating all argued and fixed — 1 kΩ, 1206, ≥250 mW, with the Mutable/Winterbloom precedent. → `selected` |
| `D-REVPOL` | "**THREE not two**", with the ~80 mV / ~20 cents argument, and `power-entry.md` agrees. → `selected` |
| `R-MODGAIN` | `mod-channels.md`: "Two resistors, not four — **settled**"; qty now fixed. → `selected` |
| `C-DECOUPLE` | Count now derived and matched; the method is not in dispute. → `selected` |

`U-DIFFRX` is already `selected` ✓ — correct for the *part*, but its description
is stale (§1), and `selected` makes stale text more dangerous.

### Overstates a decision that is not made

| Ref | Why `candidate` is too strong |
|---|---|
| `C-FILT-MOD` | The row's own note says "**PACKAGE IS PROBABLY WRONG**" and offers three fallbacks. A part that may not exist in any package the row names is not a candidate. → `open` |
| `J-UMBILICAL` | "variant TBD", "Variant decided at E12/M7". → `open` |
| `PLATE-TOP` | `part` = TBD and "**THICKNESS OPEN**" — which `config/key-layout.yaml` confirms: `plate_thickness: null`, "OPEN, and it blocks M4/M5". → `open` |
| `PLATE-THUMB` | `part` = "TBD - ~2mm", same geometry question. → `open` |
| `BODY-OAK`, `SIDE-ACRYLIC` | `part` = TBD. → `open` |
| `TRIM-GAIN` | The BOM and the page table now both say 200 Ω, but `pitch-stage.md:229` still lists the value under "Still open". Until that line goes, the value is formally contested |
| `R-PRESENCE` | "Final values at E10", and the tap point itself is under "Still open" on `digital-and-supervision.md`. → `open` |
| `C-REG-ADJ` | Dielectric undecided (Table 4). → `open` |
| `TRIM-BREATH-ZERO` | Its source rail now contradicts the schematic (§1). → `open` until the page is redrawn |

### Quantity / status contradictions

`J-USB` (1), `U-ESD-USB` (1), `SW-BOOT` (2) are `not-needed` with non-zero
quantities. `U-OPA-GEN` shows the right pattern: `not-needed`, **qty 0**.

---

## 7. One cross-cutting row that is still half-wrong

**`R-OE-PU`.** Its `notes` were corrected at 03:48 and are now right: pull-up to
the 74AHCT125's own bus +5 V, with the supervision-rail argument correctly
narrowed to the comparator and the watchdog (which do sit on 5.21 V, as
`digital-and-supervision.md`'s rail table says). That resolves what was a
four-against-one contradiction with `power-entry.md`, `digital-and-supervision.md`,
`R-LED-PANEL` ("Same rail as `R-OE-PU`") and `U-PRESENCE` ("pull the collector to
+5V").

**Its `description` field was not touched**, and still reads:

> "Pull-up from the **LM393** open collector to bus +5V"

`LM393` is the part `U-PRESENCE` deleted, on the grounds that it "cannot do the
job" — its output emitter is tied internally to V−, so on a split supply it would
pull the AHCT125's `OE` pins to −12 V. That is a destructive failure, and the
deleted part's name is still sitting in the description of the resistor that
connects to it. One-word fix, but worth doing before anyone builds from the
description rather than the note.

---

## Summary of actions

**BOM edits, high confidence:**

1. `R-OE-PU` description: **LM393 → LM311**.
2. Rename `R-CLR-PU` → **`R-CLR-PD`**, matching both drawings and its own description.
3. `J-USB`, `U-ESD-USB`, `SW-BOOT` qty → **0**.
4. Rewrite `U-DIFFRX`'s description: `REF` is a buffered trimmer, output **0 V at rest to −9.6 V**.
5. `TRIM-BREATH-ZERO` note: range **0 → +1.0 V**, not "~+0.6V" — the page moved for a dimensional reason (the sensor's 0.152–0.378 V pedestal band) and the row did not follow.
6. Put **50 mΩ** in `R-ILIM`'s part field.
7. `BENCH` status `available` → one of the five allowed values.
8. Split `U-LOADSW` into three rows; split `C-REG-ADJ` and `C-FILT-BREATH` into two each.

**New rows needed:** `C_T` (LT1641 timer cap); 2 × BAV99 breath-input clamps;
`TRIM-OFFSET` range resistors; `TRIM-BREATH-ZERO` divider resistors.

**Schematic edits this review implies:**

- `breath-receive-stage.md:53–54` — the drawing still says `TRIM-BREATH-ZERO` is buffered "from `VREFOUT`", which the same page's component table (`:149`) and the BOM both now contradict; `:240` has the same problem for the downstream stage's offset reference.
- `pitch-stage.md:208`, `:213`, `:229` — sweep the residual **1 kΩ / ±5 %** trimmer; `:213` recomputes the page's largest accuracy term.
- `mod-channels.md:132`, `:146`, `:152`, `:157` — sweep the residual **4.02 / ±10.05 V**.
- `digital-and-supervision.md:52` — the "−200 mV (from −12 V)" label, and the paragraph accusing the BOM of being stale about it.
- `pitch-stage.md` — draw the 7th `R-OPAMP-IN` on the `VREFOUT` follower, or drop it from the BOM.
- `breath-receive-stage.md` — draw the breath output's clamp, or reduce `D-JACK-CLAMP` to 5.

**Decisions required before the BOM can be right:**

- **`U-OPA-PITCH` 5 or 6**, and `C-DECOUPLE` 20 or 22 with it. Turns on whether the breath downstream gain+offset stage is one op-amp half or two — which is undecided because the stage itself is deferred to E10.
- **`D-JACK-CLAMP` 5 or 6** — is the breath output clamped?
- **An ADR covering ESD protection on the umbilical signal lines**, which would give `U-TVS-SPI`, `U-TVS-MODULE` and `D-TVS-BREATH` a citation that means something.

**Blocked on the network — part and parameter to check:**

| Part | Parameter |
|---|---|
| 82 nF C0G (`C-FILT-MOD`) | Availability in 1210 at ≥16 V |
| 47 nF C0G (`C-AA-ADC`) | Availability in 0805 — probably not; find the real package |
| 15 nF C0G (`C-FILT-BREATH`) | Availability in 0805 |
| 330 nF film (`C-OUT-BREATH`) | Availability in 1206; otherwise it is a THT part |
| LT5400 (`R-PRECISION`) | Option code for 1:1 four-equal-10 kΩ in MS8, plus tolerance grade |
| N-FET (`U-LOADSW`) | Single-pulse SOA at 12 W / 50 ms |
| LT1641-1 (`U-LOADSW`) | Pin names, foldback network topology, whether `-1` needs a reset cycle on `ON` after latch-off |
| Ferrite bead (`FB-IN`) | A series rated ≥1 A at 600 Ω@100 MHz — series, not footprint |
| DAC8568C (`U-DAC`) | SBAS430 confirmation of the grade → reference-gain mapping |
| REF5050 (`C-REF-OUT`) | Recommended output capacitance — does it justify qty 2? |
