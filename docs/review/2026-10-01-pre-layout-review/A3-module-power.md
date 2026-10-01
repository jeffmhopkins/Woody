# A3 - Module power and sequencing

**Slice:** Eurorack entry (J-PWR-EURO), reverse protection (D-REVPOL D1-D4), the rail PTCs, U-ISO (RECOM RPA20-2412SAW, ADR 0027) and its input filter, the umbilical load switch (LT1641-1, Q-LOADSW, ON/FB dividers), LOGIC_5V (ADP7118), DAC_AVDD (LM317L, R-REG-SET-HI/LO), U-LVL-MOD on DAC_AVDD, the order of every rail going up and coming down, budgets and thermal.
**Revision measured:** 13197f8 (a `git archive` copy; `tools/` pinned at the same revision)
**Tools:** `tools/check-staleness.py` (FAIL only on 2 `cad`, which come from the archive copy having no git blob ids and are outside this slice), `tools/check-netlist.py --strict` (0 problems), `tools/merge-bom.py --check` (0 problems), `tools/sim.py run` on `module/power-entry/sim` (20 runs, 23 assertions, 0 failed), `module/umbilical-load-switch/sim` (198 runs, 5 assertions, 0 failed), `module/digital-and-supervision/sim` (8 runs, 6 assertions, 0 failed), `module/dac8568/sim` (51 runs, 12 assertions, 0 failed); `pdftotext -layout` on RECOM-RPA20-AW, LM317LZ (TI SLCS144E), ADI-ADP7118, BOURNS-MF-MSMF, and the Doepfer A-100 technical HTML.

## Summary

- **What holds:** the topology as netlisted. U-ISO's input is across the two rails, D2 and D4 point the right way, PTC-ISO is on the +12 V leg ahead of D2, and C-ISO-Y sits on that fused side. PWR_GND, DIG_GND and AGND_MOD reach BUS_GND only through NT-UMB-MOD, NT-DIG-MOD and NT-AGND-MOD. The LM317L divider is now right way round: 150 Ω from OUT to ADJ and 475 Ω from ADJ to AGND_MOD, which gives 5.21 V, and the sheet's MPN fields match the values. U-LVL-MOD is on DAC_AVDD and the sequencing sim's requirement holds. Every U-ISO budget number, every PTC rating, both ON thresholds and the LDO dissipation figures re-derive within rounding from the banked datasheets.
- **What does not hold:**
  - The module pages say the LT1641 "decides every start and every fault" and that U-ISO "never acts first". The carrier's own `replug-early` sim says otherwise (A3-1).
  - The claim that "a reversed ribbon has no unprotected rail to land on" is true only for a ±12 V swap. A 16-pin cable reversed at a 16-pin bus header puts the bus +12 V and +5 V onto the module's ground pins (A3-2).
- **Partial-fix shapes found:** fixes from 2026-09-30 and 2026-10-01 that did not reach the sheet notes, the BOM descriptions, `nets.yaml` or ADR 0004/0005:
  - the "raw bus" wording on the `ON` divider;
  - `U-REG-LOGIC` described as "for U-LVL-MOD";
  - `NT-AGND-MOD` described as a tie "to PWR_GND";
  - FB2 described as "THE UMBILICAL BRANCH";
  - `D-REVPOL` "qty 3";
  - "Decouples DAC full scale from the rack's +5 V";
  - the converter limit described as "typical only".
  
  Also one quantity carried two ways: the module's own rail draw, derived as 37/20 mA and asserted as 45/40 mA.
- **Sequencing:** power-on is simulated for every rail. Power-off is simulated only for LOGIC_5V against DAC_AVDD. The ±12 V analog decay order rests on an unsimulated BOM-row argument with stale currents (A3-7, A3-14).

## Findings

### A3-1 - "The LT1641 decides every start and every fault; U-ISO never acts first" is contradicted by the replug-early sim
**Severity:** medium
**Node:** U-ISO / U-LOADSW / ISO_POS12; figure `hotplug-iso-ocp`
- **The claim, in four places:**
  - [repo] `hardware/module/power-entry/power-entry.md:193`: "the LT1641 decides every start and fault".
  - [repo] `power-entry.md:231-232`: U-ISO "never acts first, because the load switch trips below its 1.84 A minimum".
  - [repo] `docs/decisions/0027-isolated-instrument-supply.md:130-131`: "so the LT1641 decides every start and every fault".
  - [repo] `hardware/module/power-entry/bom.csv` row U-ISO: "THE MINIMUM, 1.84A, IS ABOVE THE LT1641's 1.10A WORST-CASE TRIP, so the load switch decides every start and every fault".
- **The contradiction:**
  - [repo] `hardware/carrier/power-entry-instrument/sim/README.md:42`: in `replug-early` the bulk "still holds a few volts and `Q-INRUSH` is still enhanced, so the replug reaches `U-ISO`'s threshold".
  - [repo] `config/figures.yaml` `hotplug-iso-ocp` derivation records that run as "a recorded hazard".
- **Why the argument fails:** on insertion the FET is already fully enhanced. The first current edge is therefore set by C-ISO-OUT, the cable and the LT1641's loop response, not by its static 1.10 A trip. A static-threshold comparison cannot establish that the switch acts first.
- **Consequence [calc]:** U-ISO's output at 1.84 A gives an input of roughly 1.84 × 12 / 0.85 / 22.2 ≈ 1.2 A per rail for the hiccup's duration. That is below PTC-ISO's 1.5 A trip, so it is probably benign. The pages still state as certain something the sims record as a hazard.
- **What would settle it:**
  - Reword the four places to "decides every start except a replug inside Q-INRUSH's window (`hotplug-iso-ocp`)".
  - At E6, scope ISO_POS12 and the LT1641's `ON` pin during a quick replug. A U-ISO hiccup also pulls `ON` under 9.62 V, which un-latches the -1, so the recovery path should be confirmed.

### A3-2 - "A reversed ribbon has no unprotected rail to land on" holds only for a ±12 V swap, not a reversed 16-pin cable
**Severity:** medium
**Node:** J-PWR-EURO, BUS_GND
- **The claim:**
  - [repo] `power-entry.md:158-160`: "There is no +5 V branch: the bus +5 V is not used, so a reversed ribbon has no unprotected rail to land on — the gap this paragraph used to accept is closed."
  - [repo] J-PWR-EURO BOM row: "with the +5V pins unconnected a reversed ribbon has no unprotected rail to land on".
- **The pinout:** [repo] `power-entry/netlist.yaml` J-PWR-EURO pins are 1-2 −12 V, 3-8 GND, 9-10 +12 V, 11-12 +5 V, 13-14 CV, 15-16 Gate. That is the A-100 order [from memory, consistent with the Doepfer HTML banked under `datasheets/`].
- **The case the row itself raises:** the same row says Doepfer bus headers are unkeyed, so the case is a 16-pin cable fitted backwards at a 16-pin bus header. Module pin k then meets bus pin 17−k [calc]:
  - module GND pins 3-8 meet bus pins 14-9, which are CV, +5 V and +12 V;
  - module +12 V pins 9-10 meet bus GND;
  - module −12 V pins 1-2 meet Gate.
- **Consequence:** BUS_GND copper shorts the rack's +12 V to its +5 V (and CV). Nothing on the module is in that path: it is upstream of every PTC and diode. D1-D4 do keep the module's own rails from conducting.
- **Doepfer's own warning:** [ds DOEPFER-A100-TECHNICAL-DETAILS-a100t_e.html] a wrongly turned cable "will destroy the module".
- **Scope:** this is the generic 16-pin Eurorack hazard, not a new defect. The defect is the page saying the gap is closed.
- **What would settle it:** restate the claim as covering the ±12 V swap (the 10-pin or row-offset case) and name the 16-pin reversal as unprotected by design. The owner kept the 16-pin header for commonality (ADR 0023 point 3), so a 2×5 header is the only fix and it is the owner's call.

### A3-3 - The `ON` divider is still described as fed from the raw bus
**Severity:** low
**Node:** ON, R-ON-HI, ISO_POS12
- [repo] `hardware/module/umbilical-load-switch/umbilical-load-switch.md:24`, Interfaces row `ON`: "divided from the raw bus by `R-ON-HI`/`R-ON-LO`".
- [repo] R-ON-HI BOM description: "Top of the LT1641 ON (UVLO) divider, raw +12 V to the toggle". Its notes: "the toggle's wires never carry the bus unlimited".
- **The truth:** [repo] the netlist puts R-ON-HI.1 on ISO_POS12, and the page's own drawing (line 419) and the sheet note on R-ON-HI both say so.
- **Shape:** an ADR 0027 fix that did not reach the row or the Interfaces table.

### A3-4 - U-REG-LOGIC is still described as the level shifter's supply
**Severity:** low
**Node:** U-REG-LOGIC, LOGIC_5V
- **Stale text:**
  - [repo] the sheet Note on U-REG-LOGIC, exported to `power-entry/netlist.yaml`: "The module's own 5 V, for U-LVL-MOD".
  - [repo] the U-REG-LOGIC BOM description: "for the SPI level shifter".
- **The truth since 2026-10-01:**
  - [repo] the `digital-and-supervision/netlist.yaml` LOGIC_5V net holds only U-RX-MOD.VCC, C-DEC-RX and R-PULL-CS.
  - [repo] U-LVL-MOD.VCC is on DAC_AVDD.
- **Shape:** a fix that did not reach the sheet field or the BOM row. Note that `power-entry.md:33`, `nets.yaml` and the page body are all correct.

### A3-5 - NT-AGND-MOD is described as a tie to PWR_GND; it ties to BUS_GND
**Severity:** low
**Node:** NT-AGND-MOD, BUS_GND
- **Stale text:**
  - [repo] BOM description: "The module analog star's single tie: AGND_MOD to PWR_GND at one point".
  - [repo] sheet Note: "single tie to PWR_GND".
- **The truth:** [repo] the netlist has NT-AGND-MOD.2 on BUS_GND, and PWR_GND reaches the star only through NT-UMB-MOD and then NT-DIG-MOD (ADR 0027 point 3; `dig-gnd-topology`).
- **Risk:** at layout, a reader following the BOM row places the tie on the wrong copper.

### A3-6 - The module's own rail draw is carried two ways: derived 37/20 mA, asserted 45/40 mA
**Severity:** low
**Node:** MODULE_ANALOG_POS12, MODULE_ANALOG_NEG12
- **Derived:** [repo] `power-entry.md:248-253` gives "~37 mA on +12 V and ~20 mA on −12 V". [calc] +12 V: 18.2 + 0.85 + 12.4 + 5.1 = 36.6 mA. −12 V: 18.2 + 0.85 = 19.1 mA.
- **Asserted, and used for the totals:**
  - [repo] `power-entry.md:199`: "its own ~45 mA and ~40 mA". The rack totals ~0.27/~0.26 A come from this.
  - [repo] `power-entry.md:430`: "~0.41 A clamp-legal … U-ISO plus the module's own ~40 mA".
  - [repo] ADR 0027:177: "~45 mA and ~40 mA".
  - [repo] `power-entry/sim/sims.yaml:46-47`: `i_mod_neg` 0.040, sourced to "ADR 0004 power table".
  - That table, [repo] ADR 0004:295, is an undated "~40 mA".
- **Second disagreement:** ADR 0004's 2026-09-30 amendment (lines 300-301) says ~0.26 A from +12 V and ~0.25 A from −12 V, against power-entry's ~0.27 and ~0.26 A.
- **Effect:** none on any margin. The −12 V figure is overstated by about 2×, which errs safe for the case-rating check. But one quantity has two values and no owner.
- **What would settle it:** make the derived pair a figure, or cite it, from `power-entry.md`'s *Fuses* table, and point sims.yaml at it.

### A3-7 - The C-BULK-RAIL row's power-down argument uses stale currents and a deleted part
**Severity:** low
**Node:** C1, C3 (C-BULK-RAIL)
- **Stale text:** [repo] the C-BULK-RAIL notes say "The +12V branch carries the LM317's divider, the DAC and the comparator, about 22mA against -12V's 10mA". The comparator (LM311) is deleted [repo] `digital-and-supervision.md:75-76`, and the loads are now 37/20 mA (A3-6).
- **The conclusion survives [calc]:**
  - +12 V: 37 mA / 100 µF = 0.37 V/ms.
  - −12 V: 19 mA / 47 µF = 0.40 V/ms.
  - The decay is still roughly balanced.
- **Shape:** a conclusion whose stated numbers have moved under it. It is also the only argument for the analog rails' power-down order (see A3-14).

### A3-8 - FB2's sheet note still calls it "THE UMBILICAL BRANCH", at half its nameplate
**Severity:** low
**Node:** FB2 (FB-IN), figure `ferrite-bias-impedance`
- **Stale text:** [repo] FB2's Note in the `power-entry` sheet and netlist: "THE UMBILICAL BRANCH. At its real operating current this bead gives roughly half its nameplate impedance - see the FB-IN row, which is the only one of the four where that matters".
- **The truth since ADR 0027:**
  - [repo] the figure: FB2 and FB4 carry U-ISO's input at ~0.22 A, about 440-480 Ω.
  - [repo] `power-entry.md:319`: "FB2 and FB4 are the ones that matter".
- **Shape:** the figure's own forbidden list guards the `.md` spellings, not this sheet note.

### A3-9 - DAC_AVDD's stated purpose, "decouples DAC full scale from the rack's ±5 % +5 V", is refuted twice
**Severity:** low
**Node:** DAC_AVDD, U-REG-DAC, figure `dac-rail`
- **Stale text:**
  - [repo] `hardware/nets.yaml` DAC_AVDD `carries`: "Local LM317 rail. Decouples DAC full scale from the rack's +/-5% +5 V".
  - [repo] U-REG-DAC BOM notes: "Decouples DAC full scale from the rack's +/-5% +5V rail".
- **Refutation 1:** [repo] ADR 0005:131-141 says "The reason is headroom, not accuracy … full scale at 5.000 V, set by the reference and not by AVDD".
- **Refutation 2:** the bus +5 V is not used at all since 2026-09-30.
- **Risk:** a reader of the master net list is handed the refuted rationale.

### A3-10 - dac-rail's derivation drops I_ADJ × R2, and the sim's "every corner" does not vary the LM317L
**Severity:** advisory
**Node:** U-REG-DAC, R-REG-SET-HI/LO, figure `dac-rail`
- **The omitted term:** [ds LM317LZ.pdf p.8-9, Eq. 2/3] V_OUT = V_REF(1 + R2/R1) + I_ADJ × R2. I_ADJ is 50 typ / 100 max µA [p.5], and R2 = 475 Ω (R-REG-SET-LO). [calc] That adds 24 mV typ and 48 mV max, so the typical output is 5.232 V, not the figure's 5.208 V.
- **The worst-case low corner [calc]:** V_REF min 1.20 V [p.5] × (1 + 475·0.999/(150·1.001)) = 4.99 V. That is under the 5.00 V hard floor before the I_ADJ term is added.
- **The sim's coverage:**
  - [sim] `digital-and-supervision/sim` reports `avdd_final` = 5.219 V at all 5 corners. Those corners vary only `k_clamp` and `t_ss`, not the LM317L's V_REF or I_ADJ.
  - Its assertion text "DAC_AVDD at or over dac-rail's 5.00 V floor, at every corner" therefore claims more than it tests.
- **Why only advisory:** E7's bench selection of R-REG-SET-LO (BOM row) is the stated mitigation, and it does cover this.
- **What would settle it:** add the I_ADJ term to the derivation, and either word the assertion as "at the model's nominal" or sweep V_REF over 1.20-1.30 V.

### A3-11 - ADR 0005's amendment still says the converter's limit is "typical only"
**Severity:** low
**Node:** U-ISO
- **Stale text:** [repo] `docs/decisions/0005-power-architecture.md:446-448`: "the converter's own limit is meant to sit above them — typical only on its datasheet, so E6 confirms it".
- **Where it came from:** that describes the RP20 (150 % typical, no minimum; ADR 0027:34-35).
- **The fitted part:** the RPA20 is specified at "110%-160% Output Current, Hiccup" [ds RECOM-RPA20-AW.pdf PD-5], a guaranteed minimum of 1.84 A, which is what ADR 0027 and power-entry.md say.
- **Shape:** the RP20 → RPA20 swap did not reach ADR 0005.

### A3-12 - ADR 0004 still states "D-REVPOL qty 3"
**Severity:** low
**Node:** D-REVPOL
- **Stale text:** [repo] `docs/decisions/0004-cv-interface-module.md:375`: "(`D-REVPOL` qty 3, ADR 0006.)".
- **The truth:** [repo] the BOM row is qty 4 (D1-D4), and check-netlist places 4.
- **Shape:** a stated count that has moved under the sentence stating it.
- **Related:** the ASCII power diagram at ADR 0004:340-354 still shows the bus +5 V branch and the load switch on bus +12 V. The amendment two paragraphs above it covers only the table.

### A3-13 - power-entry's Interfaces row names interfaces/spi-link as a DAC AVDD peer
**Severity:** low
**Node:** DAC_AVDD
- **The row:** [repo] `power-entry.md:32` lists `interfaces/spi-link` as a peer.
- **The netlists:** [repo] no `hardware/interfaces/*/netlist.yaml` has a DAC_AVDD endpoint. `hardware/nets.yaml` DAC_AVDD receivers are dac8568, breath-output-stage, breath-receive-stage and digital-and-supervision. R-PULL-SYNC, the last spi-link-adjacent load, is in `digital-and-supervision`.
- **Note:** check-netlist does not compare Interfaces tables against `nets.yaml`, so it did not catch this.

### A3-14 - Power-down order of the analog rails is argued, not simulated
**Severity:** advisory
**Node:** MODULE_ANALOG_POS12/NEG12, DAC_AVDD, LOGIC_5V
- **What is simulated:**
  - [repo] `power-entry/sim/README.md` covers power-on only, with −12 V arriving early, together and late.
  - [sim] `digital-and-supervision/sim` covers LOGIC_5V against DAC_AVDD at power-off. It confirms DAC_AVDD falls first and that SYNC/SCLK_DAC/DIN stay under AVDD + 0.3 V.
- **What is not:**
  - which of ±12 V analog collapses first once D1/D3 reverse-bias;
  - what the pitch jack does while that happens.
  
  This rests only on the C-BULK-RAIL row (A3-7).
- **What would settle it:** a power-off transient in `power-entry/sim` with the derived loads. The deck already exists, so this is cheap.

## Checked and holds

**Netlist and sheet**

- D1/D2 have anode to bus, D3/D4 cathode to bus. PTC-POS12, PTC-NEG12 and PTC-ISO are ahead of their diodes. C-ISO-Y runs from ISO_VIN_POS to PWR_GND, on the fused leg. [repo] `power-entry/netlist.yaml`.
- The LM317L divider is now correct: R-REG-SET-HI 150 Ω from OUT to ADJ, R-REG-SET-LO 475 Ω from ADJ to AGND_MOD. 1.25 × (1 + 475/150) = 5.208 V [calc]. The sheet MPNs match the values: RT0805BRD07150RL for 150 Ω and TC0525B4750T5G for 475 Ω [repo sheet fields]. I did not confirm that TC0525's package matches the 0805 footprint.
- The RPA20 symbol is +Vin 1, −Vin 2, −Vout 4, Trim 5, +Vout 6, matching [ds RECOM-RPA20-AW.pdf PD-8] and [repo] `hardware/lib/woody.kicad_sym`.
- The LT1641 netlist matches the page: VCC, R-ILIM and R-ON-HI on ISO_POS12; every return on PWR_GND; the FB divider on the output; R-GATE-COMP in series with C-GATE.

**U-ISO, against [ds RECOM-RPA20-AW.pdf]**

- Datasheet values confirmed: UVLO on 8-9 V and off 7-8 V; quiescent current 20/55 mA; 550 kHz; OCP 110-160 % with hiccup; isolation capacitance 1100 pF typ; 0.02 %/K; accuracy ±2 % max, line ±0.2 %, load ±0.1 %; 12.5 K/W with PCB at 0.1 m/s; 1000 µF maximum capacitive load; recommended input fuse 3 A slow blow (PD-1, PD-5, PD-6).
- Output tolerance ±3.1 % over 40 K [calc].
- Typical draw: 4.31 W out, 5.26 W in, 0.225 A per rail at 23.4 V [calc].
- Clamp-legal worst: 0.37 A per rail. Overload held under trip: 0.49 A. Hot-plug at the LT1641's 1.10 A: 0.68 A [calc].
- Input floor: 22.2 V, 13 V above UVLO [calc].
- Input filter: f₀ 3.3 kHz, Z₀ 0.46 Ω, against a negative input resistance of −104 Ω; 76 Ω of inductor reactance at 550 kHz [calc].
- C-ISO-OUT plus the instrument's 570 µF is 670 µF, under the 1000 µF maximum [calc].

**PTCs, against [ds BOURNS-MF-MSMF.pdf]**

- MF-MSMF020/60: 0.20/0.40 A; Rmin 0.40 Ω, R1max 6.0 Ω; 60 V; hold 0.15 A at 50 °C and 0.13 A at 60 °C.
- MF-MSMF075/33X: 0.75/1.5 A; 0.11/0.40 Ω; 33 V; hold 0.56 A at 50 °C and 0.49 A at 60 °C.
- Rail floors with a post-trip PTC: 10.9 V, and 10.5 V with six jacks shorted [calc].

**LM317L, against [ds LM317LZ.pdf]**

- Datasheet values confirmed: V_REF 1.20/1.25/1.30 V; minimum output current 1.5/2.5 mA; θJA 139.5 °C/W (LP); 2.5 V minimum differential; line regulation 0.01/0.02 %/V; load regulation 5 and 10 mV/V; ADJ protection diode only required above 6 V out, so not needed here.
- Load 12.4 mA, 89 mW, +12 °C; 79 mW without the buffer [calc].

**ADP7118, against [ds ADI-ADP7118.pdf]**

- Datasheet values confirmed: 20 V maximum input; dropout 30/60 mV at 10 mA; 380 µs start-up; SOT θJA 170 °C/W; at least 1.5 µF on input and output; UVLO falling at 2.2 V.
- 38 mW, +6.4 °C [calc].

**LT1641 ON thresholds**

- 10.24 V on, 9.62 V off; worst case 9.81-10.68 V and 9.36-9.88 V [calc]. These agree with the page's 9.79-10.70 V and 9.33-9.90 V, which also include the input current.
- 0.94 V of margin under U-ISO's −3.1 % floor [calc].

**Sequencing**

- Power-on order: LOGIC_5V at 0.9-1.25 ms, then DAC_AVDD at 8.6 ms [sim `rails-and-sync`], then U-ISO (8-16 ms start-up [ds PD-5]), then the LT1641 ramp of 49-197 ms (`loadswitch-gate-cap`).
- Power-off: DAC_AVDD falls before LOGIC_5V [sim]. U-LVL-MOD's inputs above its VCC are inside its rating [ds SN74AHCT125.pdf p.3-4, as cited; not re-read].
- The `what-if-lvl-on-logic-5v` run still fails, as intended, at 3.4 V over AVDD and 10-17 mA of clamp current [sim].

**Not checked**

- The RPA20 efficiency curve value at 21 % load: it is graphical.
- L-ISO-IN's current rating: the Sunlord PDF is image-only.
- The PSMN2R0-30YLE SOA margins: they are graphical (A4/A6 scope).
