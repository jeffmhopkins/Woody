# S8 — BOM reconciliation against the schematic pages

**Date:** 2026-09-21. **Scope:** `hardware/bom.csv` (127 rows) against the eight
schematic pages (`hardware/module/*.md` ×6, `hardware/controller/*.md` ×2),
`docs/decisions/**`, `config/key-layout.yaml`.

**Method.** Refdes index built mechanically: every BOM `ref` searched against
whitespace-normalised page text (the pages hard-wrap at ~80 columns, so a naive
line-based grep produces ~47 false "missing" hits — that is a measurement
artifact, not a defect); and every refdes-shaped token in the pages
(`(R|C|D|U|J|L|SW|FB|TRIM|POT|LK|TP|HDR|MECH|PCB|KNOB|F|SKT|LED|ADH|CABLE|WIRE)-...`)
matched back against the BOM. Quantities were then hand-checked against the
drawings and the per-board component tables. Nothing in this repo was edited.

**Headline.** The refdes-naming crisis the last sweep found is *mostly* closed:
`R-SCLK-SER`/`R-MOSI-SER`/`R-CS-SER` are retired in favour of `R-SPI-SER` (qty 3,
now drawn in `carrier.md` §4), `R-OE-PU` and `R-LED` are deleted with the
comparator, `R-SPI-SER` is no longer an orphan, and `R-CHAIN-SER`, `U-TVS-CHAIN`,
`F-CHAIN`, `LK-SER`, `R-SER-TERM`, `D-CLAMP-BREATH`, `R-LDAC`, `R-BIAS-DAC` all
have rows. What is left is a smaller, harder set: **three connectors and one
op-amp stage that are drawn and unbuyable**, **one op-amp package double-counted
across two rows**, **two power-entry topologies that the BOM and the drawing
describe differently**, and a spread of stale notes that survived the parts they
described.

---

## A. Drawn but not in the BOM

Every refdes (or unlabelled drawn part) that appears in a current schematic and
has no row. "Proposed" marks pages that flag the part as new themselves — the
page knowing it is missing does not make it buyable.

| Refdes | Page | What it is | Why it matters | Severity |
|---|---|---|---|---|
| `J-LED-L`, `J-LED-R` | `carrier.md` §1, §5 | 4-way strip connectors (12 V, GND, DI, BI) | `LED-SIDE` (the WS2815 reel) has a row; the two connectors it lands on do not. The carrier cannot be populated. `WIRE-LOOM` covers ribbon, not headers | **Showstopper** |
| `J-DISP` | `carrier.md` §1, §6 | 9-way display loom connector | Same: the whole display interface has no purchasable part. Also the only remaining home for buck B's output | **Showstopper** |
| `ON`-pin network (4 passives, no refdes) | `power-entry.md`, *"Still not designed: the `ON` pin"* | UVLO divider, pull-down, debounce on the LT1641 enable | The page states it plainly: "no divider, no logic level, no supply, no pull-down, no debounce and no UVLO threshold specified anywhere — four missing passives on the node that decides whether the instrument powers up at all." No rows, no refdes | **Showstopper** |
| N-FET (no refdes) | `power-entry.md` | DPAK/SO-8 pass FET for `U-LOADSW` | Bundled into `U-LOADSW`'s `part` field ("LT1641-1CS8 + DPAK/SO-8 N-FET + sense R"). A BOM extract yields no FET part number, and the part must be selected against a single-pulse SOA curve. The same field also re-books the sense resistor that `R-ILIM` already owns | High |
| `R1` 20 k, `R2` 10 k, divider 2 × 10 k | `breath-output-stage.md` §4 | Response-shaper resistors | `POT-RESP`, `R-RESP`, `D-RESP`, `U-RESP` all got rows; the four fixed resistors in the same drawing did not. The page's own cost table names them ("R1 20 k, R2 10 k, divider 2 × 10 k") | High |
| `C-ADC-BULK` | `carrier.md` §2 | 10 µF X7R at MCP3202 `VDD`/`VREF` | Proposed. The part has a derivation (WS2815 PWM ~2 kHz against a 4 kHz sampler) and no row | Medium |
| `R-LED-PD` ×2 | `carrier.md` §5 | 10 kΩ pull-downs on IO1/IO2 | Proposed, unretrofittable by the page's own argument (boot-window float → random pixel data on a 12 V strip). Its mirror on the module side, `R-SPI-PULL`, has a row | Medium |
| `LK-CLR` | `digital-and-supervision.md` | Solder pad to ground beside the DAC `CLR` pin | Drawn in the live circuit. `R-CLR-PU`'s note describes it in prose but no row exists; `LK-SER` (the analogous cluster-board link) does have one | Low |
| `TP-*` (test points), LA header | `carrier.md` component table | Testability | The page lists them as proposed with no BOM entry. E14 and M8 have no documented means of measurement | Low |

Correctly *absent* (deleted parts still named in prose, no row needed, no defect):
`R-SCLK-SER`, `R-MOSI-SER`, `R-CS-SER`, `R-OE-PU`, `R-LED`, `R-CLR-PD`,
`R-OFFINJ`, `R-TERM-CHAIN`, `R-PRESENCE` (the presence comparator is deleted;
`digital-and-supervision.md`'s *Still open* still asks for "a corrected
`R-PRESENCE` row" — that ask is stale, not a missing part).

Label aliases, not missing parts (the drawings use a local name for a row that
exists — worth normalising, no build impact): `C-TIMER`/`C_GATE` →
`C-TIMER-LOADSW`/`C-GATE-LOADSW`; `J-UMB` → `J-UMBILICAL`; `J-CHAIN-IN/OUT` →
`J-CHAIN`; `R-ADCDIV-U/L` → `R-ADCDIV`; `R-IN`/`R-FB` → `R-BREATH-SUM`;
`R-OFF`/`R-OFFNEG` → `R-BREATH-OFF`; `R-78E5` → `U-BUCK`; `R1`/`R2` (pitch) →
`R-PRECISION`; `R1`/`R2` (mods) → `R-MODGAIN`; `R_G` → `R-GAIN-INAMP`;
`C_diff`/`C_cm` → `C-FILT-BREATH`; `D1`–`D3` → `D-REVPOL`; `FB1`–`FB4` →
`FB-IN`; `C1`–`C4` → `C-BULK-RAIL`; `U-BOLT` → `MECH-UBOLT`.

---

## B. In the BOM but drawn nowhere

| Refdes | Qty/status | Finding | Severity |
|---|---|---|---|
| `R-LDAC` | 1, candidate | `digital-and-supervision.md` states flatly: **"`LDAC` is not in this design anywhere"**, and lists tying it as an open item. The row says it is tied. One of the two is wrong; as drawn, the DAC's `LDAC` is a floating CMOS input | High |
| `HDR-DEV` | 6, open | Budgeted for two dev boards. `carrier.md` §"One dev board, not two" draws **one** socket pair — the display board is 360 mm away and reaches the carrier by loom, not by socket. Four of the six strips have no drawn destination | High |
| `C-BULK-DISP` | 1, open | Display-board local bulk. **There is no display-board schematic page at all**, so it, `U-DISP` and the display end of `J-DISP` cannot be reconciled against anything | Medium |
| `J-USB` (1), `U-ESD-USB` (1), `SW-BOOT` (2) | not-needed | Correctly undrawn — but they carry non-zero quantities while the only other `not-needed` row (`U-OPA-GEN`) carries qty 0. A quantity rollup orders four parts the BOM says are not needed | Medium |
| `U-TVS-MODULE` | 1, open | Undrawn **deliberately** and the note says so ("DELIBERATELY open, not forgotten … retrofittable"). Not a defect | — |
| `R-TRIM-RANGE` | 4, open | Only implied on the pages ("`TRIM-OFFSET 10k` + range resistors"). Neither trimmer's range network is drawn, so qty 4 is unverifiable. `pitch-stage.md` says `TRIM-OFFSET` "is not buildable as described" without it | Medium |
| `U-MCU-SPARE`, `U-DISP`, `U-IMU`, mechanical rows (`MECH-*`, `PLATE-*`, `BODY-OAK`, `SIDE-ACRYLIC`, `ADH-*`), `TUBE`, `CABLE-UMB`, `SW-THUMB`, `CAP1-n`, `KNOB-BREATH`, `PANEL`, `BENCH`, `PCB-*` | — | Non-schematic by nature (dev boards, enclosure, consumables, board blanks). Not defects | — |

---

## C. Quantity disagreements

### C.1 Verified correct against the drawings

Stated explicitly so the next sweep does not re-derive them.

| Refdes | Qty | Derivation |
|---|---|---|
| `R-KEY-PU` | **24** ✓ | `cluster-boards.md` component table: LH 6 + LT 6 + RH 6 + RT 6. 21 switch positions (18 fitted + 3 reserved) **plus** the 3 genuinely free bits (22, 23, 31). `key-layout.yaml` `spare_bits_free: 3` agrees |
| `R-KEY-SER` / `C-KEY` | **21 / 21** ✓ | LH 5 + LT 4 + RH 6 + RT 6 = 21 each. The 8 marker bits strap direct to the rails (no resistor, no cap) and the 3 free bits get a pull-up only — so 24/21/21 is exactly what the pages say |
| `U-KEYS`, `C-DECOUPLE-165`, `PCB-CLUSTER` | **4 / 4 / 4** ✓ | One per cluster board |
| `J-CHAIN` | **8** ✓ | Carrier 1 + RT 2 + RH 2 + LT 2 + LH 1. `SER`/`QH` are point-to-point, so every board but the chain end carries IN and OUT |
| `LK-SER` (4), `R-SER-TERM` (1), `R-CHAIN-SER` (3) | ✓ | Match the cluster table and the §3 drawing |
| `J-CV`, `R-OUT-PROT`, `D-JACK-CLAMP` | **6 / 6 / 6** ✓ | Pitch + 4 mods + breath |
| `R-OPAMP-IN` | **7** ✓ | Pitch, mods 1–4, mod-offset buffer, `VREFOUT` follower — enumerated identically in the row and in `mod-channels.md` |
| `R-MODGAIN` (8), `C-FILT-MOD` (4), `R-BIAS-DAC` (6) | ✓ | Two-resistor form × 4 channels; 6 populated DAC channels |
| `R-SPI-PULL` | **6** ✓ | 3 cable-side + 3 DAC-side of the 74AHCT125 |
| `R-SER-BREATH-INST` (2), `R-SER-BREATH` (2), `R-BIAS-INAMP` (2), `C-FILT-BREATH` (3), `R-GAIN-INAMP` (1), `D-CLAMP-BREATH` (2) | ✓ | R1/R1b, R2/R3, R4/R5, C_diff + 2 × C_cm, R_G, both legs |
| `R-BREATH-SUM` (2), `R-BREATH-OFF` (2), `R-GAIN-FLOOR` (1) | ✓ | R-IN/R-FB, R-OFF/R-OFFNEG, the 7.15 k floor |
| `D-REVPOL` (3), `FB-IN` (4), `C-BULK-RAIL` (4) | ✓ (count) | D1–D3, FB1–FB4, C1–C4. See C.2 for `FB-IN`'s *rating* |
| `C-DECOUPLE` module | **19** ✓ | 6 × OPA2197 ×2 + INA828 ×2 + DAC ×2 + '125 + LT1641 + LM317 = 19. The 21→19 drop is the deleted LM311's two caps. Correct **only if** no seventh op-amp package is fitted — see C.3 |
| `C-DECOUPLE-CARRIER` | **7** ✓ | MCP3202, REF5050, OPA2197, 74AHCT125, MPXV4006DP, 2 × R-78E5 inputs |
| `KNOB-BREATH` | **3** ✓ | `POT-GAIN` + `POT-OFFSET` + `POT-RESP`, and the 10HP panel budget (97 mm of ~110 mm) is derived against three pots in one row |
| `C-STRIP-BULK` (2), `R-ADCDIV` (2), `C-AA-ADC` (1), `D-TVS-BREATH` (2), `U-BUCK` (2), `J-UMBILICAL` (2), `U-BREATH` (2) | ✓ | All match the drawings and their stated reasons |

### C.2 Disagreements

| Refdes | BOM | Drawn / implied | Finding | Severity |
|---|---|---|---|---|
| `C-REF-OUT` | **2** × 10 µF | One 10 µF on the REF5050 output, plus a 100 nF that `C-DECOUPLE-CARRIER` already books | The row's note describes **one** output capacitor ("Per the REF50xx datasheet's recommended output capacitance, with a 100 nF from `C-DECOUPLE-CARRIER` alongside"), so qty 2 is unexplained. `carrier.md` flags the same thing twice ("Qty 2 for one part — say whether that is parallel or in+out"). If it is in+out, then `C-DECOUPLE-CARRIER`'s "REF5050 **in**" is double-booking the input cap; if it is parallel, the stability analysis behind `R-ISO-REF` (which assumes 10 µF) is against the wrong load | **High** |
| `L-BUCK-IN` vs `C-BUCK-IN` | 1 vs **2** | `carrier.md` §1 draws **one** L and **one** C, feeding both R-78E5.0s. ADR 0004 specifies "**a** real LC between the umbilical node and the buck input" (singular) | Three sources, two topologies. `C-BUCK-IN`'s note ("One per buck") is the outlier against both the drawing and the ADR. Either `C-BUCK-IN` is 1, or `L-BUCK-IN` is 2 and a second inductor is missing. The damping calculation (f0 3.39 kHz, Q 0.5–0.9, 220× margin) is done for one 22 µH / 100 µF pair and does not survive the other reading | **High** |
| `HDR-DEV` | **6** | One board's worth (2 strips) + spares | See B. The row's own note ("2 strips for the ESP32-S3-Matrix, 2 for the T-Display-S3 AMOLED, 2 spare") is written against a two-boards-on-one-carrier topology that ADR 0013's zone table and `carrier.md` both abandoned | **High** |
| `U-OPA-PITCH` (6) + `U-RESP` (1) | 7 packages, 14 halves | `breath-output-stage.md` §4: the response shaper "consumes **both remaining** OPA2197 halves" — i.e. no new package | Double-count. Either the shaper is inside `U-OPA-PITCH`'s six packages (then `U-RESP` is a duplicate row) or it is a seventh package (then `U-OPA-PITCH`'s note "Six packages, twelve halves, TEN used … TWO SPARE" is wrong, and `C-DECOUPLE` must go 19 → 21). Separately, the `POT-OFFSET` buffer half that `U-RESP`'s note says the extra package is *for* is **drawn nowhere and allocated nowhere** | **High** |
| `R-LED-SER` | **4** | `carrier.md` §5 draws 4, its component table says "×2–4", and the BI gates are marked "IF NEEDED" | Qty 4 presumes the WS2815 backup line is driven — which the page lists as an open datasheet question that also decides whether the 74AHCT125 is the right part at all. Ordering 4 is the safe call; the contradiction with `U-LVLSHIFT`'s "Two spare gates" is real (see D) | Medium |
| `FB-IN` | **4**, one part number ≥1 A | FB1 +12 V analog (~45 mA), FB2 +12 V umbilical (360–620 mA), FB3 −12 V (~10–20 mA), FB4 +5 V (one 74AHCT125, ~mA) | Count is right; the *specification* is one rating across a 100:1 current spread. ADR 0004's reason for ≥1 A applies to the two +12 V branches only ("both +12 V branches exceed [300 mA]"). A ≥1 A bead on the −12 V and +5 V branches buys materially less impedance at 100 MHz than a lower-current part of the same size — the row spends its filtering where it is not needed and standardises on the wrong end of the range | Medium |
| `C-REG-ADJ` | **2** | One `[C 1µF]` drawn on the LM317 output | The note explains both (ADJ bypass 10 µF + output 1 µF) but the drawing shows one; the ADJ bypass is undrawn. Low risk, but the LM317's noise figure in the note depends on the undrawn one | Low |
| `SW1-n` (21, **purchased**) vs `SW-THUMB` (4, open) | 21 + 4 | 18 fitted positions, 21 networked | `SW-THUMB`'s note says "If taken, `SW1-n` drops by 4" — impossible for a row already marked `purchased`. As it stands the two rows total 25 switches for 21 positions | Low |
| `MECH-PTFE` | **2** | One plug, one port ("Pressure port only — the DP's reference port is unplumbed") | Qty 2 is unexplained by the note (spare? two jobs are named, but they are two jobs of *one* part) | Low |
| `C-TIMER-LOADSW`, `C-GATE-LOADSW` | 1, 1, `TBD`, `open` | Values deliberately unset | **Not a defect.** Both rows correctly say `TBD`, name the equation, name the target (150 ms timer, 100 ms ramp), name the disagreement (I_TIMER 3 µA → 365 nF vs 76 µA → 9.25 µF) and name what resolves it (the LT1641 datasheet). The package field was already corrected off "0805 C0G". This is the right state | — |

---

## D. `part` / `package` / `status` / `notes` contradicting a drawing or another row

| Refdes | Field | Contradiction | Severity |
|---|---|---|---|
| `D-USBOR` | `notes` + `package` | (a) The note describes "**one diode per source** into the shared 5 V node" — an arrangement that cannot be built, because the other source is USB VBUS *inside the dev board* and never appears in any drawing. `carrier.md` draws one diode per **regulator output** and says so: "the OR node is a dev-board pin — `[repo]` note is wrong". (b) `package` is `DO-41 THROUGH-HOLE` while `part` is "1N5817 **or SS14**" — SS14 is SMA. A footprint cannot be chosen from this row | **High** |
| `U-REG-DAC` | `description` | "Adjustable LDO set to **5.25 V**" against `R-REG-SET`'s 150R/475R → **5.21 V**, which is the figure `power-entry.md`, `digital-and-supervision.md`, `TRIM-BREATH-ZERO`, `R-BREATH-OFF`, `R-SPI-PULL` and `R-OPAMP-IN` all use. 5.25 V survives from ADR 0004's block diagram, which still carries it | **High** |
| `R-LDAC` | `notes` vs schematic | Row says the pin is tied; the schematic page says `LDAC` "is not in this design anywhere" and lists tying it as open. See B | High |
| `U-RESP` / `U-OPA-PITCH` | `notes` | Mutually exclusive accounts of the same two op-amp halves (see C.2) | High |
| `C-DECOUPLE` | `notes` | The enumeration still reads "… **LM311 on +/-12V = 2** …" and sums to **21**, contradicting its own qty of 19 and the appended sentence that removes those two. The enumeration also predates any seventh op-amp package | Medium |
| `C-BULK-RAIL` | `notes` | Its +12 V-vs-−12 V decay argument counts "the LM317's divider, the DAC **and the comparator**, about 22 mA" — the comparator (LM311) is deleted. The 22 mA that justifies 100 µF on +12 V is therefore overstated | Medium |
| `PCB-MODULE` | `description` | "DAC, scaling, jacks, power entry, load switch, **watchdog**" — stale. The row's own note says so ("'watchdog' in this row's description is stale — that part is DELETED"). Self-acknowledged, still uncorrected | Medium |
| `R-KEY-SER` | `notes` | "press is ~1 µs (100R × **10 nF**) … release is ~93 µs (**10 k** × 10 nF)" — both parts changed. `C-KEY` is 47 nF and `R-KEY-PU` is 2.2 kΩ, giving 4.7 µs / 103 µs (`cluster-boards.md` §2). `C-KEY`'s own row carries the corrected arithmetic; its neighbour does not | Medium |
| `R-BREATH-SUM` | `part`/`notes` | "40.2 k … **same E96 feedback part as `R-MODGAIN`**, bought on the same reel" — `R-MODGAIN` is now 10 k/**30 k** after the two-resistor redraw. `breath-output-stage.md`'s values table repeats the same stale claim. Two rows now believe they share a reel they do not | Medium |
| `U-LVLSHIFT` vs `R-LED-SER` | `notes` | "**Two spare gates**" against "FOUR not two … the level shifter's two spare gates are exactly what it needs". Both cannot be true | Medium |
| `POT-OFFSET` vs `POT-RESP`/`U-RESP` | `notes` | `POT-OFFSET`: "Wiper does **NOT** need buffering … which for an offset knob is feel rather than error." `POT-RESP` and `U-RESP`: the unbuffered wiper "is why its zero sits ~20° past centre at +0.605 V", and the fix "wants a half". The same fact is a non-issue in one row and a funded review finding in two others | Medium |
| `U-LOADSW` | `notes` | Sizing numbers predate the foldback rebuild: "A 1.0 A ramp at ~6 V mean for 75 ms is ~6 W and 0.45 J" and "Set the limit at 1.0 A" against `power-entry.md`'s corrected 0.940 A limit (47 mV threshold, not 50), ~4 W peak with foldback, 0.158 J, and a ~62 ms loaded start. The row also bundles three distinct parts (controller + FET + sense R) in one `part` field, re-booking `R-ILIM` | Medium |
| `R-ILIM` | `notes` | "1.0 A target … The stated 0.9–1.13 A window" — superseded by 0.940 A at 50 mΩ. The row's E6-selects-on-the-bench conclusion still holds | Low |
| `R-OUT-PROT` | `package`/notes vs pages | Row and `breath-output-stage.md` say 1206 **≥500 mW**; `pitch-stage.md` says 1206 **≥250 mW** in two places. The row's own worst case (192 mW steady state) is why 500 mW was chosen | Medium |
| `C-FB-PITCH` | value | Row says **2.2 nF**; `pitch-stage.md` draws "`C-FB-PITCH` 1 nF" in the ASCII schematic and again in the loop-handover table, while its values table and prose say 2.2 nF. The drawing — which is what a layout gets built from — carries the superseded value | Medium |
| `C-DECOUPLE-CARRIER` | `notes` vs drawing | Enumerates "REF5050 **in**"; `carrier.md` §2 draws the 100 nF on the REF's **output**, beside `C-REF-OUT`. As drawn, the reference has no input bypass | Medium |
| `KNOB-BREATH` | `notes` | "Match the shaft of the **`POT-BREATH`** variant ordered" — `POT-BREATH` is not a refdes in this BOM; the parts are `POT-GAIN`, `POT-OFFSET`, `POT-RESP`, and they are not guaranteed to be one shaft type | Low |
| `WIRE-LOOM` | `notes` | "**five connectors** must match: one on the carrier and one per cluster board" — superseded the same day by `J-CHAIN`'s **eight** (IN and OUT on every board but the chain end). Both rows are dated 2026-09-21 and disagree | Medium |
| `C-KEY` | `notes` | Press crosses V_IL "in ~5.7 µs" vs `cluster-boards.md`'s 5.92 µs, and "44×" vs the page's "42×". Same model, different rounding | Low |
| `U-LVL-MOD`, `LED-PANEL`, `R-LED-PANEL` | `notes` | All three still narrate the deleted presence comparator. Correct as history, and each states the deletion — but `LED-PANEL`'s justification ("with LT1641-1 latching off on a fault, this still says why the instrument went dark") is **false** on the rail it is now fitted to: `power-entry.md` shows +12 V analog is live in every latching fault, so the indicator indicates nothing | Medium |
| `carrier.md` vs BOM | page prose | The page still says `F-CHAIN` is "**Proposed, not in the BOM**", that `R-CHAIN-SER`/`U-TVS-CHAIN`/`F-CHAIN` "have no BOM entry yet", and that for shunt links "the BOM has none". All four now have rows (`F-CHAIN`, `R-CHAIN-SER`, `U-TVS-CHAIN`, `LK-SER`). The staleness is on the schematic side this time | Medium |
| `config/key-layout.yaml` line 131 | comment | "The **5** genuinely free bits are FLOATING CMOS INPUTS and must be pulled" against `spare_bits_free: 3` nine lines later. `R-KEY-PU` = 24 is derived from the 3; a reader who takes the 5 gets 26 | Low |
| `C-TIMER-LOADSW`, `C-GATE-LOADSW` | `status`/`part` | **Correct by design.** `TBD` + `open` is the honest state for two values that a datasheet decides; both rows name the equation, the target and the blocker. Not defects | — |

---

## ADR column audit

**Every `adr` value resolves to an ADR that exists** (0001–0009, 0013, 0014; no
blanks, no 0010/0011/0012 references, no dangling numbers). Coverage defects are
about *fit*, not existence:

- **`POT-RESP`, `R-RESP`, `D-RESP`, `U-RESP` → 0006.** ADR 0006 does not cover a
  hardware response control; it **assigns the job elsewhere**: "Firmware still
  shapes the response curve upstream of the DAC. The knobs fit the *range* to the
  patch; the firmware shapes the *feel*." ADR 0003 repeats it ("Panel knobs
  (ADR 0006) handle range fitting; firmware handles response feel"). Four rows
  and a third panel knob now point at a decision that argues against them.
  **This needs an ADR, not a pointer.** Medium.
- **Panel-control rows point at three different ADRs**: `POT-GAIN`/`POT-OFFSET` →
  0003, `POT-RESP` → 0006, `KNOB-BREATH` → 0004. ADR 0006's channel table is
  where GAIN 0.5–4× / OFFSET ±5 V is actually specified. Low.
- **`U-MCU-RT` → 0007** (IMU selection). Defensible only because 0007 records the
  board choice; the MCU decision is 0001/0013. Low.
- **`PCB-CLUSTER` → 0002** (key switches) while the existence of four cluster
  boards is ADR 0001's partitioning decision. Low.
- **`C-OUT-BREATH` → 0006** while every other breath-path row points at 0003. Low.
- **`D-REVSHUNT` → 0004 vs `D-TVS-PWR` → 0005** for two parts on the same
  umbilical power pair at the same end. Low.
- **`BENCH` → 0006** is arbitrary (tooling row). Low.
- Checked and **correct**: `L-BUCK-IN`, `C-BUCK-IN`, `FB-IN`, `C-BULK-RAIL`,
  `U-REG-DAC`, `R-REG-SET` → 0004 (ADR 0004 §"Power entry" specifies the LC, the
  ≥1 A ferrites, the bulk-at-the-load rule and the LM317); `R-SPI-*` → 0004;
  `R-KEY-*`/`C-KEY`/`J-CHAIN`/`U-KEYS`/`LK-SER`/`R-SER-TERM`/`F-CHAIN`/
  `U-TVS-CHAIN` → 0001; LED chain → 0014; enclosure → 0009.

## `status` vocabulary audit

No definition of the BOM's status values exists anywhere in the repo
(`docs/decisions/README.md` defines **ADR** statuses only). Observed usage:
`candidate` 83, `open` 31, `selected` 6, `not-needed` 4, `purchased` 2,
`available` 1. Inconsistencies:

1. **`open` carries two incompatible meanings** — "value/part unknown"
   (`C-TIMER-LOADSW`, `PLATE-TOP`, `R-ILIM`) and "fully specified but not yet
   adopted" (`R-CHAIN-SER` 100R 1%, `U-TVS-CHAIN` SOT-23-6, `F-CHAIN` 100 mA
   polyfuse, `LK-SER`, `R-SER-TERM`, `R-RESP` 15k). A buyer cannot tell which
   rows block an order.
2. **Decided rows still marked provisional.** `J-CHAIN` (note: "DECIDED
   2026-09-21") is `candidate`; `WIRE-LOOM` (note: "DECIDED 2026-09-21") is
   `open`; `U-DAC` ("GRADE LOCKED TO C") and `U-LOADSW` (suffix argued to a
   conclusion, drawn on two pages) are `candidate`.
3. **`not-needed` is not applied uniformly**: `U-OPA-GEN` is qty 0, while
   `J-USB`, `U-ESD-USB` and `SW-BOOT` keep qty 1/1/2.
4. **`purchased` interacts badly with open options**: `SW1-n` is purchased at 21
   while `SW-THUMB` still proposes swapping 4 of them.

---

## Summary table

| # | Refdes | Defect class | Severity |
|---|---|---|---|
| 1 | `J-LED-L`, `J-LED-R` | A — drawn, no row (carrier LED connectors) | **Showstopper** |
| 2 | `J-DISP` | A — drawn, no row (display loom connector) | **Showstopper** |
| 3 | LT1641 `ON`-pin network (4 passives) | A — drawn/required, no refdes, no rows | **Showstopper** |
| 4 | `U-LOADSW` pass FET | A — drawn, bundled into another row's `part` field | High |
| 5 | Response shaper `R1` 20 k, `R2` 10 k, 2 × 10 k divider | A — drawn, no rows | High |
| 6 | `R-LDAC` | B/D — row says tied, schematic says absent | High |
| 7 | `HDR-DEV` | B/C — qty 6 against one drawn socket pair | High |
| 8 | `C-REF-OUT` | C — qty 2 for one REF5050, purpose undefined | High |
| 9 | `L-BUCK-IN` (1) vs `C-BUCK-IN` (2) | C — two topologies, ADR 0004 says one LC | High |
| 10 | `U-OPA-PITCH` (6) + `U-RESP` (1) | C — 2 op-amp halves double-counted; `POT-OFFSET` buffer half unallocated | High |
| 11 | `D-USBOR` | D — note describes an unbuildable "one per source"; `package` DO-41 for an SMA part | High |
| 12 | `U-REG-DAC` | D — 5.25 V description vs 5.21 V divider | High |
| 13 | `C-DECOUPLE` | D — enumeration still sums to 21 and still lists the LM311 | Medium |
| 14 | `C-DECOUPLE-CARRIER` | D — books "REF5050 in"; drawing puts the cap on the output | Medium |
| 15 | `FB-IN` | C — one ≥1 A rating across four branches spanning ~100:1 | Medium |
| 16 | `R-LED-SER` (4) vs `U-LVLSHIFT` ("two spare gates") | C/D — gate budget contradiction | Medium |
| 17 | `R-OUT-PROT` | D — ≥500 mW in the BOM, ≥250 mW on `pitch-stage.md` | Medium |
| 18 | `C-FB-PITCH` | D — 2.2 nF in the BOM, 1 nF in the schematic drawing | Medium |
| 19 | `R-KEY-SER` | D — debounce arithmetic still on 10 nF / 10 kΩ | Medium |
| 20 | `R-BREATH-SUM` | D — "same part as `R-MODGAIN`"; `R-MODGAIN` is now 30 k | Medium |
| 21 | `U-LOADSW` | D — 6 W / 0.45 J / 1.0 A sizing predates the foldback rebuild | Medium |
| 22 | `C-BULK-RAIL` | D — rail-decay argument still counts the deleted comparator | Medium |
| 23 | `PCB-MODULE` | D — description still lists "watchdog" (self-acknowledged) | Medium |
| 24 | `WIRE-LOOM` | D — "five connectors" against `J-CHAIN`'s eight | Medium |
| 25 | `LED-PANEL` | D — stated justification false on the +12 V analog rail | Medium |
| 26 | `POT-OFFSET` vs `POT-RESP`/`U-RESP` | D — wiper buffering is a non-issue in one row, a finding in two | Medium |
| 27 | `C-ADC-BULK` | A — proposed, derived, no row | Medium |
| 28 | `R-LED-PD` ×2 | A — proposed, unretrofittable, no row | Medium |
| 29 | `R-TRIM-RANGE` | B — qty 4 unverifiable; neither trimmer's range network is drawn | Medium |
| 30 | `C-BULK-DISP`, `U-DISP`, display end of `J-DISP` | B — no display-board schematic exists to reconcile against | Medium |
| 31 | `J-USB`, `U-ESD-USB`, `SW-BOOT` | B/status — `not-needed` with qty > 0 | Medium |
| 32 | `POT-RESP`, `R-RESP`, `D-RESP`, `U-RESP` | ADR — 0006 assigns response shaping to firmware | Medium |
| 33 | `carrier.md` prose | D — still calls `F-CHAIN`/`R-CHAIN-SER`/`U-TVS-CHAIN`/links "not in the BOM" | Medium |
| 34 | BOM-wide `status` vocabulary | status — `open` has two meanings; decided rows still `candidate`; `not-needed` inconsistent | Medium |
| 35 | `C-REG-ADJ` | C — qty 2, one drawn | Low |
| 36 | `SW1-n` / `SW-THUMB` | C — 25 switches for 21 positions; `SW1-n` already `purchased` | Low |
| 37 | `MECH-PTFE` | C — qty 2 unexplained | Low |
| 38 | `LK-CLR` | A — solder pad drawn, no row (`LK-SER` has one) | Low |
| 39 | `TP-*` / LA header | A — proposed testability, no rows | Low |
| 40 | `KNOB-BREATH` | D — references non-existent `POT-BREATH` | Low |
| 41 | `R-ILIM` | D — 1.0 A / 0.9–1.13 A window superseded by 0.940 A | Low |
| 42 | `C-KEY` | D — 5.7 µs / 44× vs the page's 5.92 µs / 42× | Low |
| 43 | `key-layout.yaml` L131 | D — "5 genuinely free bits" vs `spare_bits_free: 3` | Low |
| 44 | `U-MCU-RT`, `PCB-CLUSTER`, `C-OUT-BREATH`, `D-REVSHUNT`, `BENCH`, `POT-*`/`KNOB-BREATH` | ADR — pointer fits loosely or splits a decision across ADRs | Low |
| 45 | `C-TIMER-LOADSW`, `C-GATE-LOADSW` | **Not a defect** — `TBD`/`open` is the correct state and both rows say what decides them | — |
| 46 | `U-TVS-MODULE` | **Not a defect** — deliberately open and documented as retrofittable | — |
| 47 | `R-KEY-PU` 24 / `R-KEY-SER` 21 / `C-KEY` 21 | **Verified correct** — 21 networked positions + 3 pull-only free bits | — |
| 48 | `C-DECOUPLE` 19, `J-CHAIN` 8, `U-KEYS` 4, `PCB-CLUSTER` 4, `KNOB-BREATH` 3, `J-CV` 6, `R-SPI-PULL` 6, `R-OPAMP-IN` 7 | **Verified correct** against the drawings | — |
