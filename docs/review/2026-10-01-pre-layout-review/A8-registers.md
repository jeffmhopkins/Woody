# A8 - The registers: figures.yaml, BOM orderability, datasheet bank, SPICE coverage

**Slice:** A8. `config/figures.yaml` entry by entry, the BOM's orderability (LCSC/JLC, CRLF, 11 columns, fragments against the master), the datasheet bank (MANIFEST against the files, how honest the BLOCKED rows are), and SPICE coverage (`docs/reference/tooling.md` §5 against the tree).
**Revision measured:** 13197f8 (a `git archive` copy; `tools/` pinned at the same revision)
**Tools:** `check-staleness.py` (with `--detail`, and `check_figures()` imported to list all 41 exemptions), `merge-bom.py --check`, `verify-datasheets.py`, `merge-manifests.py --check`, `check-netlist.py --strict`, `sim.py check` / `sim.py show`, `sim_coverage.py`, `cad.py explain`, ngspice 42 present, `pdftotext -layout` on banked sheets. I wrote a parser that pulls every placed symbol's fields out of the 30 circuit `.kicad_sch` files and the 6 board sheets (319 symbols). I looked up every LCSC code on the sheets through the LCSC product API (`https://wmsc.lcsc.com/ftps/wm/product/detail?productCode=Cxxxx`, 2026-10-01) and the unresolved one on `https://jlcpcb.com/partdetail/`.

## Summary

- **The mechanical registers hold.** BOM: 210 rows, 26 fragments, 11 columns, CRLF master, 0 problems. Datasheet bank: 312 rows, 270 verified files, no orphan or missing file, every sha256 matches. `check-netlist --strict`: 0 problems. 20 sim directories: `sim.py check` and `sim_coverage.py` both PASS. Every sim-derived register figure I compared with its `results.yaml` reproduces (list under *Checked and holds*). All 41 refuted-in-place exemptions are legitimate corrections.
- **The LCSC codes are real.** Of the 99 distinct codes on the sheets, 98 resolve to exactly the MPN on the sheet. One (C51349, both 22 µH inductors) no longer resolves on LCSC. **Stock is the gap:** FB-IN, which the `ferrite-bias-impedance` figure is tied to, has 0 in stock and is machine-placed ×4. C-FB-PITCH, U-LOADSW and U-BUCK also show 0.
- **One part is missing from a sheet:** `C-DECOUPLE-CARRIER` is bought ×8, but only 5 are drawn, and `U-BUF` (OPA2197) has no supply bypass at all. Its row's enumeration still counts two R-78E5 bucks.
- **A settled figure rests on a disputed one.** `shaper-exp-gain`'s "hard blow" (in-amp −4.64 V) is exactly 2.8 kPa, a candidate of the disputed `breath-working-point`.
- **Partial fixes, in all four recorded shapes:**
  - the module-board layer decision did not reach `pcb-pipeline.md` or ADR 0018;
  - the REF5050 grade change did not reach its sim;
  - `repo-maintenance.md` §4 still tells editors to keep history in BOM notes;
  - the register's own prose carries three stale notes.
- **The gate fails at REV:** `check-staleness.py` reports FAIL (`module-photo-detail` stale), and it counts that one problem as "2".

## Findings

### A8-1 - `C-DECOUPLE-CARRIER` is bought ×8 but only 5 are drawn, and `U-BUF` (OPA2197) has no supply bypass
**Severity:** medium
**Node:** `C-DECOUPLE-CARRIER`; `U-BUF.V+` on `INST_POS12` (main board `U3`)

- **The row asks for 8 and names them.** "One per supply pin: MCP3202, REF5050 IN AND OUT, OPA2197 +12V, 74AHCT125, MPXV4006DP, and both R-78E5 inputs", qty 8 [repo] `hardware/bom.csv` row C-DECOUPLE-CARRIER.
- **5 are placed:** `check-netlist.py --strict` reports "C-DECOUPLE-CARRIER 5/8". The five are C-DEC-ADC, C-DEC-REF-VIN, C-DEC-REF-VOUT, C-DEC-SENSOR and C-DECOUPLE-LED [repo] sheet fields, and `hardware/boards/main-board/README.md:85`.
- **The OPA2197's slot is not drawn.** `U-BUF.V+`'s net `INST_POS12` holds `C-STRIP-BULK`, 13× `C-LED`, 13× `D-LED.VDD`, `L-BUCK-IN`, `Q-INRUSH.D`, `R-INRUSH-GD`, `R-REF-IN` and `U3.V+` [repo] `hardware/boards/main-board/board-netlist.yaml` net INST_POS12. There is no capacitor at the op-amp. Locally, `U-BUF.V+` shares `INST_POS12` only with `R-REF-IN` [repo] `hardware/carrier/breath-excitation-reference/netlist.yaml:146-150`. So the reference/breath buffer's only bypass is the LED row's decouplers, wherever layout puts them.
- **"Both R-78E5 inputs" is a stated count that moved under its sentence.** Since ADR 0015 there is one buck: `U-BUCK` qty 1, "ONE" [repo] `hardware/bom.csv` U-BUCK. `carrier.md:87` still says "the two R-78E5.0 bucks".

**What would settle it:** draw a 100 nF at `U-BUF.V+` (and at `U-BUCK`'s input, if that slot is still wanted), then set the qty to what is drawn: 6 or 7, not 8.

### A8-2 - `FB-IN` (MI1206K601R-10) has zero LCSC stock, is machine-placed ×4, and the register figure is tied to that exact part
**Severity:** medium
**Node:** `FB-IN` (FB1–FB4), LCSC C2441375; figure `ferrite-bias-impedance`

- **No stock.** LCSC reports `stockNumber` 0 for C2441375 (MI1206K601R-10, Laird, 1206) [web] wmsc.lcsc.com product API, 2026-10-01. The sheet sets Assembly=machine [repo] sheet fields.
- **No easy substitute.** The figure's whole basis is that this part "is the only >=1A 600R 1206 part found whose datasheet publishes an IMPEDANCE-UNDER-DC-BIAS curve" [repo] `config/figures.yaml:861-864`, and Murata BLM and Wurth WE-CBF are rejected on that ground. A JLC "equivalent" would quietly void the ~440–480 Ω on FB2/FB4.

**What would settle it:** JLC global sourcing or consignment for C2441375, or a second part whose sheet publishes a bias curve, chosen now rather than by the assembler.

### A8-3 - Other orderability gaps at LCSC (2026-10-01)
**Severity:** low
**Node:** `C-FB-PITCH`, `U-LOADSW`, `U-BUCK`, `U-BREATH`

All stock figures are [web] LCSC product API, 2026-10-01.

- `C-FB-PITCH` CL21C222JBFNNNE (C28260): stock 0, machine. A 2.2 nF C0G 0805 has many substitutes, so this only needs a swap.
- `U-LOADSW` LT1641-1IS8#PBF (C664552): stock 0, hand. It is single-source ADI and the load switch's whole derivation is on this die. Source it elsewhere (not checked).
- `U-BUCK` R-78E5.0-1.0 (C3033024): stock 0, hand.
- `U-BREATH` MPXV4006DP (C5190605): stock 3 against a BOM qty of 2 (one fitted plus the spare, which is why `check-netlist` shows 1/2 placed).
- Thin but sufficient: `R-PRECISION` LT5400 16, `J-MCU` 70, `U-KEYS` 112 (needs 4), `C-INRUSH-GS`/`C-REG-OUT` C28323 20.

### A8-4 - `shaper-exp-gain` is "settled" on a working point that is a candidate of the disputed `breath-working-point`
**Severity:** medium
**Node:** figure `shaper-exp-gain`; `R-RESP`; `BREATH_SHAPED`

- **The hard blow is 2.8 kPa.** `shaper-exp-gain` is defined "at a hard blow (in-amp −4.64 V)" [repo] `config/figures.yaml:668`. [calc] 4.64 V / 2.16106 (effective in-amp gain) = 2.147 V at the sensor; / 0.7665 V/kPa = **2.80 kPa**.
- **2.8 kPa is a disputed candidate.** `breath-working-point` is `disputed`, and its first candidate is "2.8 kPa (cited to ADR 0003, which does not contain it; the two schematic pages cite each other)" [repo] `config/figures.yaml:513-519`.
- **The corpus disagrees with itself about it:**
  - `breath-adc.md:41` labels 2.8 kPa "one candidate of breath-working-point, open until E2";
  - `breath-output-stage.md:41,44` states "Real playing only reaches about 2.8 kPa" as fact;
  - the shaper's sim asserts against it [repo] `hardware/module/breath-response-shaper/sim/sims.yaml:95`;
  - `R-RESP` 3.9 k was sized to it ("need 1.5x gain") [repo] `config/figures.yaml:672`.
- **E2 can move it.** If E2 measures the 3–4 kPa candidate, both the 1.64× value and the R-RESP choice move.

**What would settle it:** mark `shaper-exp-gain` as conditional on `breath-working-point` (with `decided_by` E2), or restate it as a function of in-amp voltage.

### A8-5 - The module board's layer count is "still open" on the PCB pipeline page, which cites a register field that no longer exists; ADR 0018 still calls `dig-gnd-topology` open
**Severity:** medium
**Node:** figure `dig-gnd-topology`; `PCB-MODULE`

- **The pipeline page says open.** "The module board is still open … Four layers dissolves it (`dig-gnd-topology`'s `proposed_if_four_layers`)" [repo] `docs/reference/pcb-pipeline.md:320-327`. The register entry has no `proposed_if_four_layers` key; its fields are value, layers, decided and the rest [repo] `config/figures.yaml:591-600`. The owner decided four layers on 2026-09-30 [repo] `config/figures.yaml:597`.
- **The same page also says settled:** "`dig-gnd-topology` — settled" [repo] `pcb-pipeline.md:115`.
- **ADR 0018 says open:** "The register's `dig-gnd-topology` dispute is about the module end and stays open" [repo] `docs/decisions/0018-main-board-wiring-decisions.md:55-57`, with no amendment.
- **The register's own `false_positive_note` is stale:** "spi-link.md (interfaces) still calls this figure disputed" [repo] `config/figures.yaml:599`. spi-link.md now just cites it [repo] `hardware/interfaces/spi-link/spi-link.md:46,124`.
- **No pattern catches any of these spellings.** This is the shape "a fix that did not reach the pages citing it", on the page a layout author reads first.

### A8-6 - `repo-maintenance.md` §4 still tells editors to keep history in BOM notes, against CLAUDE.md 2b
**Severity:** medium
**Node:** `hardware/bom.csv` notes column (all rows)

- **The instruction:** "The `notes` column is append-only in practice: corrections are added after a ` | ` with a date, and the superseded text is left in place. That is what makes the checker's refutation detection work" [repo] `docs/reference/repo-maintenance.md:233-235`.
- **The rule it contradicts:** CLAUDE.md 2b says the exemption is prose-only, that "In a `.csv` … a forbidden value is a defect, full stop", and "CUT what tells them WHAT SOMEONE USED TO THINK". The checker enforces this [repo] `tools/check-staleness.py:367`. So following the maintenance doc re-grows the 2026-09-22 trim, and `audit-notes.py --regrown` would then flag it.
- **A stated count that moved, same section:** `unplaced.csv` "Two of its clusters name circuits this corpus has no page for — six identical jack-protection networks drawn three times, and nineteen decoupling capacitors with no home" [repo] `repo-maintenance.md:217-219`. `hardware/unplaced.csv` (44 rows) holds neither: it is mechanical parts, cables, PCBs, not-needed USB parts and `J-B2B-MOD` [repo].

### A8-7 - The REF5050 grade change did not reach its sim: assertions still cite the Standard grade's 0.1 %
**Severity:** low
**Node:** `U-REF-BREATH`; figure `ref5050-grade`

- **The sim still describes the Standard grade:**
  - "within its 0.1 % initial accuracy of 5.000 V (A grade, SBOS410O Table 4-2)" [repo] `hardware/carrier/breath-excitation-reference/sim/sims.yaml:120`;
  - "the reference's own 0.1 % initial accuracy" [repo] same file, :71;
  - "5.000 V within 0.1 %" [repo] `sim/README.md:25`.
- **The bought part is the High grade:** REF5050IDR, ±0.05 % [repo] `config/figures.yaml:868`; sheet MPN REF5050IDR, LCSC C24696 [web] LCSC 2026-10-01, 4373 in stock.
- **Nothing catches it.** The register's `forbidden` list does not catch "0.1 % initial accuracy" or "A grade". The assertions pass, but they are twice as loose as the part and name the wrong grade.

### A8-8 - `R-REG-SET-LO` is the E7 select-on-test part but the sheet machine-places a fixed SMD value, and the 0.66 V spread predates the 0.1 % divider
**Severity:** low
**Node:** `R-REG-SET-LO`, `R-REG-SET-HI`, `U-REG-DAC`; figure `dac-rail`

- **The documents say the bench picks it:** "E7 SELECTS THIS ONE on the bench" [repo] BOM R-REG-SET-LO; ROADMAP E7; `dac-rail.floor`. U-REG-DAC's row says "a TO-92 part, two through-hole resistors and a voltmeter".
- **The sheet fixes it instead:** 475R 0.1 % 0805, TC0525B4750T5G, Assembly=**machine** [repo] sheet fields; [web] LCSC C50670161 "RES 475Ω ±0.1%". A machine-placed SMD part has to be reworked to be "selected".
- **The spread may be out of date:** 0.66 V against a ~0.55 V window [repo] ADR 0004:188. [calc] With the divider now bought at 0.1 % and TI's LM317L limits (V_REF 1.20–1.30 V, I_ADJ ≤100 µA [ds] `LM317LZ.pdf` §6.5):
  - low end: 1.20 × (1 + 3.1604) = 4.99 V;
  - high end: 1.30 × (1 + 3.1730) + 100 µA × 475 Ω = 5.47 V;
  - so about 0.48 V static, against the C grade's 5.0–5.5 V. 1 % resistors give about 0.62 V, which suggests the 0.66 V came from a 1 % divider.
- **What would settle it:** re-derive the spread at the bought tolerance, including temperature and line/load terms. Then either make R-REG-SET-LO hand-fit or through-hole, or drop "selects".

### A8-9 - LCSC C51349 (both 22 µH inductors) no longer resolves on LCSC
**Severity:** low
**Node:** `L-BUCK-IN`, `L-ISO-IN`

- **The sheets and BOM cite it:** SWPA6028S220MT, LCSC C51349 [repo] sheets; BOM notes; MANIFEST row.
- **LCSC does not know it:** the API returns `result: null` and `https://www.lcsc.com/product-detail/C51349.html` returns 404. The same two checks on C524819 return the part and 200 [web] 2026-10-01.
- **JLC still lists it:** `https://jlcpcb.com/partdetail/C51349` is titled "SWPA6028S220MT | Sunlord" [web]. Stock is unverified.

**What would settle it:** JLC's parts search for C51349 stock, or a current LCSC code for SWPA6028S220MT.

### A8-10 - `tooling.md` §5's "Simulated" table names the wrong receiver and leaves out one of the 20 sim directories
**Severity:** low
**Node:** `U-RX-MOD`; `hardware/boards/key-board-rh/sim/`

- **Wrong receiver:** the spi-link row reads "… into the module's 74AHCT125" [repo] `docs/reference/tooling.md` §5 table. The sim's receiver is U-RX-MOD, the 74AHCT14 Schmitt stage behind R-RX/C-RX [repo] `hardware/interfaces/spi-link/sim/sims.yaml:4`, and `cs-fall-reentry` is defined against it.
- **Missing row:** the table has 19 rows against 20 `sim/` directories; `key-board-rh/sim` is missing. The Coverage table lists it, and `sim_coverage.py` passes.

### A8-11 - `diode-split-rationale` quotes `r_d` at 392 mA, a +12 V current that ADR 0027 removed
**Severity:** low
**Node:** `D1`/`D2` (`D-REVPOL`); figure `diode-split-rationale`

- **The register quotes the old current:** "(r_d 69 mohm at 392 mA)", with a `false_positive_note` saying "392 mA is the MODULE total on +12 V (instrument + module)" [repo] `config/figures.yaml:749,734`; also `power-entry.md:122-123`.
- **That current no longer exists.** Since ADR 0027:
  - `D2` carries U-ISO's ~0.22 A [repo] `power-entry.md:186`;
  - `D1` carries the module's analog ~37–45 mA [repo] `power-entry.md:253`, ADR 0027:176.
- **The conclusion (HF isolation) survives.** Only the quoted operating point is stale.

### A8-12 - Stale prose inside the registers themselves
**Severity:** low
**Node:** figures `opa2197-output-impedance`, `umbilical-current`, `marker-bits`/`free-bits`

- **`opa2197-output-impedance.note`** says "Not recomputed yet, because it is blocked on a prior question: three files disagree about which side of the buffer C-REF-OUT sits on" [repo] `config/figures.yaml:842`. `cref-out-node` and `riso-ref-topology` are both settled [repo] :568-630.
- **`umbilical-current`'s value does not match its derivation:** value 359 mA, but the derivation's own result is "358.1 mA" [repo] :727,731. [calc] 226 × 5 / (0.9 × 11.4) + 248 = 358.14.
- **The checker loses its decider:** the entry gives its decider as `blocked_on`, so `check-staleness` prints "decided by: -" for it [repo] `.staleness/report.txt`.
- **`config/key-layout.yaml`, owner of `marker-bits`/`free-bits`,** says "the right thumb is only its three" [repo] :157-158. The same file counts `right_thumb: 4` (RT1–RT4) [repo] :52,112-115.

### A8-13 - The owner of `chain-connectors` never states its value
**Severity:** low
**Node:** `J-CHAIN`; figure `chain-connectors`

- **The owner page only cites itself:** `key-chain-loom.md:19-21` writes "… (`J-CHAIN`) on each board — `chain-connectors` in all". The number 4 appears only in the register, the BOM qty and the sheets.
- **The checker cannot help:** `check-staleness` lists this owner as UNCHECKED ("no token distinctive enough") [repo] `.staleness/report.txt`.
- **The value itself is right.** BOM J-CHAIN qty 4; main-board J4/J5 plus J1 on each key board [repo] sheets.

### A8-14 - Nothing checks the bought-part identity fields that ADR 0019 puts on the sheet
**Severity:** advisory
**Node:** all rows: `MPN`/`LCSC`/`Manufacturer`/`Assembly` sheet fields

- **The scanner never reads them.** `check-staleness.py` reads only `.md/.csv/.yaml/.yml` [repo] `tools/check-staleness.py:170`. The exported `netlist.yaml` carries `value` and `note` but not MPN or LCSC [repo] e.g. `breath-excitation-reference/netlist.yaml`.
- **The only check that touches them:** `pcb.py` requires a machine part to have *an* LCSC field [repo] `tools/pcb.py:1314`.
- **So:**
  - a sheet MPN regressing to REF5050AIDR would pass `ref5050-grade`'s "REF5050AID" pattern unseen;
  - so would an MPN that disagrees with its BOM row's part, or an LCSC code that points at a different part.
- **I checked them by hand this time:** all 98 resolvable codes match their MPN [web] LCSC API. That is a one-off, not a check.

### A8-15 - `check-staleness.py` FAILs at REV, and miscounts the failure
**Severity:** low
**Node:** `mechanical/module/renders/photo-detail.png`

- **The failure:** `module-photo-detail: STALE - changed config/module.yaml, tex-albedo/height/roughness.png, panel-art.echo, tools/render-module.py` [repo] `cad.py explain`, run in the pinned copy. REV's own commit re-rendered the front photo but not the detail.
- **The miscount:** the summary says "2 cad" and "CAD OUTPUTS STALE OR EDITED (2)" while the body says "FAIL 1 CAD output problem(s) of 73". `check_cad()` returns every non-PASS line of `cad.py check`, including its FAIL summary, and `len()` counts those lines [repo] `tools/check-staleness.py:1192-1195,1284`.

### A8-16 - The `loadswitch-timer` owner page still reports a BOM package defect that has been fixed
**Severity:** low
**Node:** `C-TIMER-LOADSW`

- **The page:** "the **0805 C0G package in `bom.csv` is wrong for 10 µF by three orders of magnitude**", present tense [repo] `hardware/module/umbilical-load-switch/umbilical-load-switch.md:327-330`.
- **The fix already landed:** the row reads "THROUGH-HOLE radial or 1210 ceramic" [repo] BOM. The sheet buys GRM32DR71E106KA12L, 10 µF 25 V X7R 1210 [web] LCSC C77100.

### A8-17 - `shaper-exp-gain`'s "worst corner" bounds a proxy diode, not the part bought
**Severity:** low
**Node:** `D-RESP`

- **The sim's diode is a proxy:** D-RESP is a behavioural diode fitted to "the 1N4448W's 0.62–0.72 V at 5 mA" [repo] `breath-response-shaper/sim/sims.yaml:5-8,24`.
- **The part bought is different:** 1N4148W-E3-08 [repo] sheet MPN; [web] LCSC C241939. Its sheets give "only maxima" (same sims.yaml line), and its own BOM row says the 0.6 V knee is "NOT-IN-DOCUMENT AS A SPEC" [repo] BOM D-RESP.
- **So the bound does not cover the fitted part.** The disclosure is honest, but the register entry is `settled` and reads "1.51x at the worst corner" without the qualifier.

### A8-18 - Six BOM fragments are LF while the master is CRLF
**Severity:** advisory
**Node:** fragments `carrier/`, `carrier/breath-excitation-reference/`, `interfaces/spi-link/`, `module/digital-and-supervision/`, `module/power-entry/`, `module/umbilical-load-switch/`

- **The count:** those six have 0 CRLF line endings; the other 20 fragments and the master are all-CRLF [calc] byte count.
- **No harm today:** `merge-bom.py --check` passes, because the tool normalises.
- **The risk:** the "always pass `lineterminator="\r\n"`" rule [repo] `repo-maintenance.md:227-229` will turn the next scripted edit of any of these into a whole-file diff.

### A8-19 - Small inconsistencies in the sheets' ordering fields and the ledgers
**Severity:** advisory
**Node:** `J-UMBILICAL-INST`, `U-MCU-RT`, `J-B2B-MOD`, `C-BULK-RAIL`, MANIFEST "Gateron KS-33 vendor drawing"

- `J-UMBILICAL-INST` (NE8FAV) has an empty LCSC field, while `J-UMBILICAL` buys the same part as C368526 [web] LCSC: NE8FAV, 876 in stock.
- `U-MCU-RT` carries no Manufacturer, MPN, LCSC or Assembly fields [repo] sheet.
- `J-B2B-MOD` is in `hardware/unplaced.csv`, "rows no schematic page names", but it is placed as J2 on module-main and J7 on module-jack [repo] board sheets.
- `C-BULK-RAIL` is one row bought as two different parts (100 µF C165558 and 47 µF C371230), which is fine for hand assembly but breaks "one row, one part".
- `merge-manifests.py`'s superseded-heuristic does not flag the BLOCKED "Gateron KS-33 vendor drawing" row, although the drawing is banked as `mechanical/GATERON-KS-33-VENDOR-SPEC-DRAWING.pdf` [repo] MANIFEST.

## Checked and holds

- **Gates at REV:**
  - `merge-bom.py --check`: 210 rows, 26 fragments, 0 problems.
  - Master BOM: 211 lines, all 11 columns, all CRLF [calc].
  - `verify-datasheets.py`: 270 verified, 42 blocked or not-fetched, 0 problems.
  - MANIFEST: every file is on disk and every banked file has a row; all sha256 recomputed and matching [calc].
  - `check-netlist.py --strict`: 0 problems; 153 rows placed to qty. The only shorts are A8-1 and `U-BREATH` (one spare by design).
- **Arithmetic re-derived and right [calc]:**
  - `inamp-full-scale`: 1 + 50/42.2 = 2.18483; ×1/1.011 = 2.16106; ×4.6 = 9.941.
  - `sensor-full-scale`: 5 × (0.9198 + 0.053) = 4.864. The transfer function and the 0.265 V typical offset were read off [ds] `MPXV4006DP.pdf`.
  - `breath-zero-ref`: 0.265 × 2.16106 = 0.5727.
  - `key-scan-current`: 3.3 / 2300 = 1.435 mA; ×19 = 27.3 mA.
  - `key-release-time` = 138.75 µs and `key-press-time` = 9.868 µs. The SN74HCS165 VT+ max of 1.5/3.15/4.2 V and VT− min of 0.3/0.9/1.2 V were read off [ds] `SN74HCS165-ti-scls828a.pdf` p.6.
  - `dac-rail`: 5.208 V.
  - `mod-reference` window and its 1.33 mA load.
  - `panel-width`: 50.50; `panel-height-budget`: 115.5 / 116.9 / 112.5 clear, 110 of content.
  - `pitch-cents-budget`: sum 0.763, RSS 0.452.
  - `loadswitch-timer`: 9.37 µF; 587/160/95.6 ms; 2.01×.
  - `loadswitch-gate-cap`: 61/122/244 V/s, 197/98/49 ms.
  - `loadswitch-fb-divider`: 10.49 V (10.05–10.93), 3.99 V.
  - `spi-series-r` first steps 3.04–3.32 V and 33 mA. (Its "1.83 V at 220R" I could not reproduce exactly; the source-side assumptions are not stated.)
  - `led-row-current`: 195/170 mA.
  - `matrix-led-current` B5819WS: 435/283 mA.
  - `hotplug-iso-ocp`: 1.837/0.544 = 3.38.
- **Sim figures against `results.yaml` [sim] `sim.py show` (minimum stated first where a figure gives a range):**
  - `riso-ref-phase-margin`: 118.53° minimum, fc 1.23–1.27 MHz at 47 nF; Figure 56 at 90.09° against TI's 89°.
  - `breath-link-cmrr`: 70.53 dB at 60 Hz, 70.87 dB at 50 Hz, 477 Hz crossing, 60.07/58.20 dB without R1b, 45.48 dB at C_cm ±5 %.
  - `pitch-mult-overshoot`: 41.77 % / 64.11 %; with R-OUT-PROT 15.29 % / 41.81 %; loop 69.3° at about 10 MHz.
  - `cs-fall-reentry`: 0.0986 V worst, negative nominal; TVS-at-line what-if 0.45/0.66 V.
  - `spi-pair-crosstalk`: 0.209/0.256/0.288 V nominal, 0.254/0.295/0.329 V worst.
  - `shaper-exp-gain`: 1.641 / 1.507, clip at −6.95 / −6.51 V.
  - `adc-sample-kickback`: −2.60 / −3.34 LSB.
  - `instrument-input-z-margin`: 181× / 55.7×, 0.570 Ω at 3846 Hz.
  - `hotplug-iso-ocp`: 0.491–0.544 A.
  - `U-TVS-SPI`'s 30 pF in the decks matches [ds] `SP0504BAHT.pdf` p.2.
- **Owners `check-staleness` cannot verify, checked by hand:**
  - `marker-bits` 8 and `free-bits` 3: key-layout.yaml:164,166, with 19 + 8 + 2 + 3 = 32.
  - `chain-conductors` 12; `key-board-chain-pinmap` 13 − k: key-chain-loom.md:134,195,277.
  - `mcu-ribbon-ways` 24-way: carrier.md:330,462.
  - `key-pullup-qty` 24: key-switch-network.md:36. The BOM agrees: R-KEY-PU 24, R-KEY-SER/C-KEY 21. The key-board JLC BOMs place 6 pull-ups and 5 networks (LH) and 6 and 6 (RH).
  - `umbilical-pinmap`: ADR 0004:961-966.
  - `loadswitch-timer` 10 µF; `dig-gnd-topology`: power-entry.md:364-369; `ks33-contact-bounce`: ks33-geometry.md:270.
  - The one owner gap is A8-13.
- **All 41 refuted-in-place exemptions read individually** (listed with `check_figures()`). Each is a dated correction or a `notes.md` history line; none carries a live stale value, and live = 0.
- **Retired spellings grepped across the corpus with none live:**
  - SPI 100 Ω and 220 Ω, R-RESP 15k/4.3k, 83 nF, 50–100 ms, 0.437/0.579, −9.6 V, 38/42 mm body, 40.34 mm, 0.85/1.35 cents;
  - HC165 0.99/2.31 V outside notes.md, REF5050AIDR, 20-way ribbon, eight connectors, 585 mA LED row.
  - Exceptions: A8-5 and A8-7.
- **Sheet MPN against BOM part, and LCSC model against MPN:** 98 of 99 codes agree on manufacturer part, package and value. The value spot-checks included R-SPI-SER 82 Ω, R-ISO-REF 37.4 Ω, C-GATE-LOADSW 82 nF C0G, C-TIMER-LOADSW 10 µF 25 V X7R 1210, R-FB-HI 35.7 k 0.1 %, R-ILIM 50 mΩ 1 W, U-DAC DAC8568ICPWR, U-REF-BREATH REF5050IDR and U-KEYS SN74HCS165DR. The key boards' JLC BOMs use only in-stock codes.
- **SPICE coverage:**
  - `tooling.md` §5's Coverage table has a row for every one of the 28 circuits and boards with parts; `sim_coverage.py` PASS.
  - `spi-link/sim` really reads `hardware/carrier/netlist.yaml` for R-SPI-SER-*, R-CS-PULL-INST and U-TVS-SPI, as the `carrier/carrier` row claims.
  - No deck hard-codes a part value. The only literals are sim fixtures (1 G breaks) and one behavioural soft-start capacitor.
