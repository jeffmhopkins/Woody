# A9 - Audit of this round's fixes (05a5bf3..13197f8)

**Slice:** A9: the 224 commits between 05a5bf3 and 13197f8, checked against the four recorded shapes of a partial fix. Priority went to ADR 0027 (U-ISO RP20 to RPA20), ADR 0028 (LED row), ADR 0025 (cassette), Q-INRUSH, the SPI receiver and 82R, R-RESP 3.9k, U-LVL-MOD on DAC_AVDD, the R-REG-SET swap, the jack swap and the removed panel words.
**Revision measured:** 13197f8 (`git archive` copy at `scratchpad/review/A9/repo`; `tools/` pinned at the same revision). I read commit messages and diffs read-only from `/home/user/Woody` history, and judged the corpus only from the pinned copy.
**Tools:** `check-staleness.py` (FAIL: 1 CAD output), `check-netlist.py --strict` (0 problems), `merge-bom.py --check` (0), `kicad.py check` (PASS: 22 sheets, 6 boards, 129 renders), `sim_coverage.py` (PASS), `cad.py explain module-photo-detail`, `pdftotext` on RECOM-RPA20-AW.pdf and WS2815B-V1.pdf, and the netlist read by script.

## Summary

- **What holds.** The large structural changes landed cleanly where tools can check them: the jack swap (config, art, J-B2B-MOD on both sheets, README allocation and ADR 0024 point 13 all agree; `kicad.py check` PASS), the R-REG-SET swap (netlist, BOM, page, sims and `dac-rail` agree at 5.208 V), the RP20 to RPA20 move (no RP20-era value survives in the corpus), the cassette's mount counts (11 / 8 / 3 agree between drc.echo and the BOM), R-RESP 3.9k, and the 82R / U-RX-MOD figures.
- **What does not.** The fixes that *did not reach* sit in prose and BOM notes that cite the changed part without being part of the change. Examples: the R-CS-PULL-MOD and U-REG-LOGIC rows after U-RX-MOD and U-LVL-MOD moved, the second "no LED current" sentence in breath-output-stage after ADR 0027, ADR 0027's hot-plug consequence after Q-INRUSH, and the module-detail photograph after the panel words and the jack swap. The last one fails the staleness checker at REV.
- **One stated quantity has three values.** The module's own rack draw is ~45/~40 mA in three places and ~37/~20 mA in the page's own worked sum. The totals built on it are 0.26/0.25 A in ADR 0004 and 0.27/0.26 A in power-entry.md.
- **Two explanations restate retired values.** The receiver's "settled high" arithmetic uses 11.1 kΩ (old 100 Ω plus a 1 kΩ that carries no DC). The 68 Ω row's rejection uses a fault-current convention the new 82 Ω row abandons.

## Findings

### A9-1 - The module detail photograph was not re-rendered after the panel-word cut and the jack swap; the checker FAILs at REV
**Severity:** medium
**Node:** `module-photo-detail` (`mechanical/module/renders/photo-detail.png`); `layout.jacks`, `art.text.jacks`
- `[repo]` `python3 tools/check-staleness.py` at 13197f8: `FAIL ... 2 cad`, and the detail lists `module-photo-detail: STALE - changed config/module.yaml, mechanical/module/art/tex-albedo.png, tex-height.png, tex-roughness.png, export/panel-art.echo, tools/render-module.py`.
- `[repo]` `python3 tools/cad.py explain module-photo-detail`: built 2026-09-30, `config/module.yaml built@b2928354b675 now@4b122af21e8c`.
- `[repo]` Commit 4c8afce (panel words) says *"The three photographs follow."* Only two followed: df890e6 (hero) and 13197f8 (front). The jack swap (936b08d/8c34d06) says *"Every module CAD output rebuilt except the three Blender photos."* The detail photo was never redone.
- `[repo]` `mechanical/module/outputs.yaml:175` describes this photo as showing *"the pitch, breath and mod 1 pills"*. Those are the pills ADR 0024 point 13 swapped, so the published image shows PITCH where BREATH now is.
- Shape: a fix that did not reach a page citing it, plus a stated count ("three photographs") that the commit did not meet.
**What would settle it:** `python3 tools/cad.py build`, then the checker returns 0 cad.

### A9-2 - The module's own analog rack draw is stated as ~45 mA / ~40 mA, but the page's own worked sum gives ~37 mA / ~20 mA; the totals built on it disagree between documents
**Severity:** low
**Node:** module +12 V / −12 V rack draw (`PTC-POS12`, `PTC-NEG12`, `U-ISO` input)
- `[repo]` `hardware/module/power-entry/power-entry.md:199`: *"~0.27 A from +12 V and ~0.26 A from −12 V (its own ~45 mA and ~40 mA plus U-ISO)"*.
- `[repo]` The same page at `:247-253`, "The analog rails' load", worst case: *"~37 mA on +12 V and ~20 mA on −12 V"*. Commit 3933e6e moved this from 35 to 37 mA and did not touch line 199.
- `[calc]` −12 V: 14 × 1.3 mA (OPA2197 max) + 0.85 mA (INA828) = 19.05 mA ≈ 20 mA. The "typical" 40 mA is twice the stated worst case. +12 V: 18.2 + 0.85 + 12.4 + 5.1 = 36.6 mA, not 45.
- `[repo]` The 45/40 survives from ADR 0004's pre-ADR-0027 table (`docs/decisions/0004-cv-interface-module.md:296`, "45 mA module incl. the DAC regulator", "−12 V ~40 mA"). It is repeated in `docs/decisions/0027-isolated-instrument-supply.md:177` ("adds ~45 mA and ~40 mA"), in `power-entry.md:259` (PTC drop "at 45 mA"), and in `power-entry.md:429-430` ("~0.41 A clamp-legal ... the module's own ~40 mA").
- `[repo]` The totals disagree with each other. `docs/decisions/0004-cv-interface-module.md:300` (ADR 0027 amendment) says *"~0.26 A from +12 V and ~0.25 A from −12 V"* and cites power-entry.md, which says 0.27/0.26. This is a restated figure that has drifted (rule 1).
- `[calc]` With the page's own 37/20 mA: 0.224 + 0.037 = 0.26 A and 0.224 + 0.020 = 0.24 A. The error is conservative for the rack budget.
- Shape: a stated count that moved under the sentences stating it.

### A9-3 - breath-output-stage still justifies R-OFFNEG's rail with "that rail carries no LED current", which ADR 0027 and the page's own corrected paragraph refute
**Severity:** low
**Node:** `R-OFFNEG` / `MODULE ANALOG −12V`
- `[repo]` `hardware/module/breath-output-stage/breath-output-stage.md:24` (interfaces table): *"`R-OFFNEG`'s fixed leg is on −12 V, chosen over +12 V because that rail carries no LED current"*.
- `[repo]` The same page, `:158-160`, rewritten by commit b8e2a7d for ADR 0027: *"The −12 V rail does carry the instrument's LED current now: U-ISO draws rail to rail ... both rails move ... by 9.7 mV"*.
- `[repo]` At 05a5bf3 the page held the phrase twice. b8e2a7d's message ("The page said -12 V carries no LED current") fixed one of the two.
- Both rails now move equally, so the stated reason for choosing −12 V is void. The 4.1 mV conclusion `[calc: 40.2k/95.3k × 9.7 mV = 4.09 mV]` still holds.
- Shape: a fix that did not reach a second sentence on the same page.

### A9-4 - The R-CS-PULL-MOD and U-REG-LOGIC BOM rows still describe the receive path from before U-RX-MOD and before U-LVL-MOD moved to DAC_AVDD
**Severity:** low
**Node:** `R-CS-PULL-MOD` (`R-PULL-CS`), `U-REG-LOGIC`, net `CS_MOD`
- `[repo]` `hardware/interfaces/spi-link/bom.csv` / `hardware/bom.csv:59`, R-CS-PULL-MOD: *"from CS_MOD to LOGIC_5V - the rail of the part it holds, U-LVL-MOD"*. Its state arithmetic is *"below the buffer's 0.8V V_IL [ds SN74AHCT125.pdf p.3]"*, and it adds *"A PULL-DOWN HERE IS WRONG: the 74AHCT125 does not invert"*.
- `[repo]` In the netlist (`hardware/module/digital-and-supervision/netlist.yaml`), `CS_MOD` = {port, R-PULL-CS.1, R-RX-CS.1}. The pull holds U-RX-MOD's RC input, not U-LVL-MOD, and U-LVL-MOD's VCC is `DAC_AVDD` (net `DAC_AVDD` includes `U-LVL-MOD.VCC`). The page was updated: `spi-link.md:53` says *"the top of R-CS-PULL-MOD - the rail of the part that pull holds. Not the 74AHCT125's, which is on DAC_AVDD"*.
- `[ds SN74AHCT14.pdf p.5]` via the U-RX-MOD row: V_T− is 0.5-1.7 V. The 0.45 V instrument-off state is still below the lowest V_T− (0.05 V margin), so the conclusion holds against a threshold the row does not name.
- `[repo]` `hardware/bom.csv:84` U-REG-LOGIC description: *"The module's own 5V ... for the SPI level shifter"*. Since 66b8472 it supplies only U-RX-MOD and R-PULL-CS (`nets.yaml:539`; `power-entry.md:33`).
- Shape: a fix that did not reach the rows citing the moved part.

### A9-5 - R-SPI-PULL went from six to five this round; two notes still say "R-SPI-PULL's six"
**Severity:** low
**Node:** `R-SPI-PULL` (qty)
- `[repo]` At 05a5bf3, `R-SPI-PULL` had qty 6 (*"SIX, not three"*). At REV it has qty 5 (`hardware/bom.csv:58`, *"FIVE OF THE MODULE'S SIX SPI PULLS - the sixth ... is its own row, R-CS-PULL-MOD"*; split in 5ea051c).
- `[repo]` These still say six: the `U-LVL-MOD` row (`hardware/bom.csv:118`, edited this round), *"what R-SPI-PULL's six resistors are for"*; `hardware/nets.yaml:706`, the same words; `hardware/nets.yaml:582`, *"the DAC-side three of the six R-SPI-PULL"*.
- Shape: a stated count that moved under the sentence stating it.

### A9-6 - The receiver's "settled high" arithmetic puts 1 kΩ and the retired 100 Ω in series with the pull-down
**Severity:** low
**Node:** `SCLK` / `MOSI` cable node, `R-RX-MOD`, `R-PULL-SCLK`/`R-PULL-MOSI`
- `[repo]` `hardware/module/digital-and-supervision/digital-and-supervision.md` ("Why the RC"): *"against the 10 kΩ pull-downs the settled high at the input is 3.3 × 10k / 11.1k = 2.97 V"*.
- `[repo]` In the netlist, `SCLK` = {port, R-PULL-SCLK.1, R-RX-SCLK.1} and `SCLK_RC` = {C-RX-SCLK.1, R-RX-SCLK.2, U-RX-MOD.1A}. The pull-down is on the cable node, ahead of R-RX. R-RX feeds a CMOS input (±1 µA) and carries no DC, so it is not in the divider.
- `[calc]` 11.1 kΩ = 10k + 1k + 0.1k, and the 0.1k is the 100 Ω R-SPI-SER retired by `spi-series-r` (now 82 Ω). The divider as netlisted is 82 Ω plus the pad's 17-35 Ω against 10 kΩ: 3.3 × 10k / 10.117k = 3.26 V to 3.3 × 10k / 10.099k = 3.27 V. The conclusion (above the 2.1 V top of V_T+) holds with more margin.
- Shape: a fix whose own explanation restates the wrong value.

### A9-7 - spi-link.md rejects 68 Ω on a fault-current convention the new 82 Ω row abandons
**Severity:** advisory
**Node:** `R-SPI-SER` / `spi-series-r`
- `[repo]` `hardware/interfaces/spi-link/spi-link.md:190-200`, the 68 Ω row: *"48 mA fault current against a 40 mA pad spec"*, which is 3.3/68 with no pad resistance. The 82 Ω row and `spi-series-r`'s derivation add the pad's 17-35 Ω: *"3.3 V / (82 + 17) = 33 mA"*.
- `[calc]` On the 82 Ω row's own convention, 68 Ω gives 3.3 / (68 + 17) = 38.8 mA, under 40 mA. The stated reason for rejecting it no longer holds by the corrected arithmetic.
- `[calc]` The table's first-step column uses different pad resistances per row. 220 Ω → 1.83 V and 100 Ω → 2.75 V both imply ~40 Ω (3.3 × 200 / (R + 40 + 100)), 68 Ω → 3.25 V implies 35 Ω, and 82 Ω uses 17-35 Ω.
- 68 Ω may still lose on the falling edge: R_s 85 Ω gives a −0.27 V first step `[calc: 3.3 × (85−100)/185]`. That is a different reason from the one written.
- Shape: a conclusion its own corrected number refutes.
**What would settle it:** recompute the table's rows on one pad-resistance convention, and give 68 Ω's actual reason (falling-edge undershoot, or none).

### A9-8 - Q-INRUSH did not reach ADR 0027's consequences or power-entry.md's supply and fuse tables, which still call 0.68 A per rail "a hot-plug"
**Severity:** low
**Node:** `U-ISO` input current, `PTC-ISO`, `hotplug-iso-ocp`
- `[repo]` `docs/decisions/0027-isolated-instrument-supply.md:179-180`: *"a hot-plug start draws up to ~0.68 A per rail for tens of milliseconds"*. `power-entry.md:191`: *"Hot-plug, the load switch at its 1.10 A worst-case limit ... ~0.68 A per rail"*. `power-entry.md:260` (PTC-ISO): *"0.68 A hot-plug for tens of ms"*.
- `[repo]` `config/figures.yaml` `hotplug-iso-ocp` (2e7aee8): U-ISO peaks at 0.49-0.54 A on a hot-plug at every corner, behind Q-INRUSH. `umbilical-load-switch.md:239-244` was updated to say the 1.10 A case is now *"a replug inside Q-INRUSH's window, or Q-INRUSH failed short"*.
- `[calc]` An ordinary hot-plug at 0.544 A out: 0.544 × 12 / 0.82 / 22.2 ≈ 0.36 A per rail, at the clamp-legal level and not 0.68 A. The 0.68 A bound still stands for the replug case, so the sizing is safe. The label is what is stale.
- Shape: a fix that did not reach the pages citing the case it changed.

### A9-9 - `diode-split-rationale` still quotes r_d "at 392 mA", a +12 V total that no diode carries since ADR 0027
**Severity:** low
**Node:** `D1`, `D2`; figure `diode-split-rationale`
- `[repo]` `config/figures.yaml` `diode-split-rationale`: value *"(r_d 69 mohm at 392 mA)"*. Its false_positive_note: *"392 mA is the MODULE total on +12 V (instrument + module)"*. `power-entry.md:122-123`: *"r_d is 69 mΩ at 392 mA"*.
- `[repo]` Since ADR 0027, D1 carries the analog rails (~37 mA, A9-2) and D2 carries U-ISO's input (~0.22 A) (`power-entry.md:188`). The ~0.40 A module +12 V total is named as the past value in `power-entry.md:200` ("where it drew ~0.40 A").
- `[calc]` 69 mΩ × 0.392 A = 27 mV (n·V_T). At 0.22 A, r_d ≈ 0.12 Ω. At 37 mA, ≈ 0.73 Ω. The qualitative HF-isolation argument survives, but the number is for a current that no longer exists.
- Shape: a fix that did not reach a registered figure that depends on it.

### A9-10 - ADR 0027 restates the LED row's current with "not yet in the corpus", but it is now a registered figure
**Severity:** advisory
**Node:** `led-row-current`
- `[repo]` `docs/decisions/0027-isolated-instrument-supply.md:45-47`: *"170–195 mA at 12 V full white [owner brief 2026-09-30, not yet in the corpus]"*.
- `[repo]` `config/figures.yaml` `led-row-current` = "170-195 mA", owner `led-strip-drive.md`, added by 47951fd in this round. Rule 1 says cite it by name, and the provenance tag is now false.

### A9-11 - check-staleness's CAD header and summary count the trailing FAIL line as a problem ("2 cad" for one stale output)
**Severity:** advisory
**Node:** `tools/check-staleness.py` (CAD section)
- `[repo]` The report at REV says `CAD OUTPUTS STALE OR EDITED (2)` above one item and `FAIL 1 CAD output problem(s) of 73 outputs`, and the one-line summary says `2 cad`.
- `[repo]` `tools/check-staleness.py:1284` prints `len(cad_problems)`, and the list holds the summary line as an element.
- A count off by one in the tool whose job is counts. Shape 3, in tooling.

### A9-12 - module-main README calls rows 9-10 and 13 "a ground row" separating the pot wipers from the jacks; pin 9 is OFFSET_WIPER, and after the swap BREATH_JACK sits directly below it
**Severity:** advisory
**Node:** `J-B2B-MOD` pins 9, 11
- `[repo]` `hardware/boards/module-main/README.md:88-90`: *"A ground row (9–10 and 13) separates the pots' high-impedance wipers from the jack outputs"*. The allocation table at `:69-78` has pin 9 = `OFFSET_WIPER`, 10 = `AGND_MOD`, 11 = `BREATH_JACK`.
- This was already false before the swap: pin 11 was PITCH_JACK beside OFFSET_WIPER. Commit 7c0446e rewrote the paragraph around it and kept it. The swap makes the neighbour BREATH_JACK, the same channel as OFFSET_WIPER, which is the less harmful pairing. The fix is to the sentence.

### A9-13 - The shaper page says "the table below" for the table above it
**Severity:** advisory
**Node:** `R-RESP`
- `[repo]` `hardware/module/breath-response-shaper/breath-response-shaper.md:169-172` (in "Settled before layout"): *"The table below was sized at 15 kΩ on unloaded arithmetic"*. The 15 kΩ table is in "Scaling", at `:114-120`, above it. Cosmetic.

## Checked and holds

- **Jack swap.** `config/module.yaml` layout.jacks and art.text.jacks, ADR 0024 point 13, ADR 0026 point 7, panel.md and the module-main README allocation agree. J-B2B-MOD pins 11/14/16/17 match on both sheets (`kicad.py check` PASS). The README's "ground beside every signal" and "order down the header is the jacks' order down the panel" both hold for the new allocation `[calc]`, checking each pin. The render's patch-cable routes moved with the jack names, so the picture is unchanged `[repo]` 936b08d.
- **Panel words.** No `art.text.power` or `art.text.umbilical` remains. `tools/panel-art.py` places only off/on in island C. `word_gap` and `line_gap` are still read (`panel-art.py:468`), so they are not dead config `[repo]`.
- **R-REG-SET swap.** BOM, netlist, power-entry.md:329 and ADR 0004's "150 Ω / 475 Ω" agree. `dac-rail` 1.25 × (1 + 475/150) = 5.208 V `[calc]`. The swapped netlist would have given 1.25 × (1 + 150/475) = 1.645 V `[calc]`, as the commit says. The digital-and-supervision sim settles DAC_AVDD at 5.219 V `[sim]` results.yaml. I_ADJ term 50-100 µA × 475 Ω = 24-48 mV, matching ADR 0004 `[calc]`.
- **U-LVL-MOD on DAC_AVDD.** Netlist VCC = DAC_AVDD with C-DEC-LVL. The DAC rail's load sums: 2.0 + 8.3 + 0.52 + 0.10 = 10.9 ≈ 11.0 mA; +1.4 = 12.4 mA; (12.4 − 5.21) × 12.4 = 89 mW; 79 mW without the buffer `[calc]`. LOGIC_5V's load is 5.1 mA, and its consumers are stated consistently in power-entry.md, spi-link.md, nets.yaml and digital-and-supervision.md (except A9-4).
- **U-ISO / RPA20.** OCP 110-160 % hiccup, 1100 pF typ, ±2.0 % max accuracy, recommended 3 A slow-blow fuse `[ds RECOM-RPA20-AW.pdf, extracted lines 408, 426, 430, 435]`. 1.1 × 1.67 = 1.837 A `[calc]`. Typical 0.359 × 12 = 4.31 W, / 0.82 = 5.25 W, / 23.4 V = 0.224 A per rail `[calc]`. No RP20-era values (±2.2 %, 0.014 Ω, 0.84, 1.5 nF) survive in the corpus `[repo grep]`. The RP20 pin-swap note agrees between the ADR, the footprint descr and the lib README.
- **R-RESP 3.9k.** The BOM, netlist, page, sim README and `shaper-exp-gain` agree, and the 15k spellings are forbidden. Clip at −6.51 V worst is 1.40× a hard blow, matching "past 1.3×"; 6.95/9.94 = 0.70, matching "seven-tenths" `[calc]`.
- **82R / U-RX-MOD.** `spi-series-r` steps: 3.3 × 200/199 = 3.32 V, 3.3 × 200/217 = 3.04 V; falling −0.02..0.26 V `[calc]`. The SPI2 DAC clock is 2 MHz, so the 47 ns RC is compatible. The forbidden list catches 100 Ω spellings; no live 100 Ω R-SPI-SER statement remains outside refutation context `[repo grep]`.
- **Q-INRUSH.** The `hotplug-iso-ocp` value is consistent across register, sim README, power-entry-instrument.md, umbilical-load-switch.md and pcb-pipeline.md. 1.837/0.544 = 3.4 `[calc]`. The old "120-168 µs" appears nowhere else.
- **Cassette.** drc.echo has 11 mounts (8 columns + 3 end mounts, 1 dropped). The BOM has MECH-MB-STUD 11, MECH-MB-SPACER 11, MECH-MB-NUT 3, MECH-COL-* 8 and MECH-KB-SPACER 8. ADR 0025 and ADR 0022 both carry the dropped-mount amendment. The chain ribbon length is cited from drc.echo by the loom sim, not restated.
- **ADR 0028.** J-LED survives only in history (notes.md, superseded ADR text). `led-row-current` arithmetic: 13 × 0.18 / 12 = 195 mA; 13 × 13.1 = 170 mA `[calc]`. WS2815B-V1 V_IH 2.7 V and V_I max 5.7 V `[ds WS2815B-V1.pdf]` match led-strip-drive.md. A full-white row on top of umbilical-current is 359 + 195 = 554 mA, 226 mA under the LT1641's 0.78 A minimum trip, matching "more than 0.2 A" `[calc]`.
- **C-DECOUPLE (module) qty 21:** 14 + 2 + 1 + 1 + 1 + 1 + 1 `[calc]`, and check-netlist places it exactly.
