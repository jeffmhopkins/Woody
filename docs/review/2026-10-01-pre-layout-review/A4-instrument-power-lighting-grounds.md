# A4 - Instrument power, lighting and grounds

**Slice:** A4. The umbilical's eight conductors and their currents; the instrument power entry (`Q-INRUSH` soft start, `INST_POS12`, the buck, the TVS); the 13 WS2815B-V1 at 12 V (data chain, decoupling, current); every return path from lighting and digital into the analog breath chain and the module (main board, cable, module).
**Revision measured:** 13197f8 (a `git archive` copy; `tools/` pinned at the same revision).
**Tools:** `python3 tools/check-netlist.py --strict` (0 problems); `python3 tools/check-staleness.py` (FAIL only on 1 CAD output, `module-photo-detail`, which is outside this slice); `python3 tools/sim.py run hardware/carrier/power-entry-instrument/sim` (145 runs, 13 assertions, 0 failed, reproduced the README's figures); `pdftotext -layout` and `pdftoppm` on the banked RPA20-AW, AO3401A, WS2815B-V1, MI1206K601R-10, R-78E5.0, SMAJ15A and UCW sheets; the board netlists (`main-board`, `umb-adapter`, `module-main`) read with Python.

## Summary

- **What holds:** the `Q-INRUSH` design (arithmetic, ratings and simulation), the LED data chain and backup wiring, the decoupling and the row current, the instrument-end ground plan (one `PWR_GND` plane, the `AGND_INST` island with one tie, the clamps at the connector), the module-end DC ground topology (`NT-UMB-MOD` at the etherCON), the rollover-lead fault path, and the per-conductor currents against the etherCON and `J-UMB` ratings. The breath link's common mode from the instrument's return current is about 60 dB smaller than anything that matters (re-derived below).
- **What does not hold:** ADR 0027 point 4 says `C-ISO-Y` keeps the converter's switching common-mode current away from the star. The netlist gives that current a path of about 13 Ω at 550 kHz through the −12 V entry (`FB4`/`D4` → `D3`/`FB3` → `C3` → `AGND_MOD` → the star → `DIG_GND` → `NT-UMB-MOD`). `C-ISO-Y` is 290 Ω at 550 kHz, so it carries the smaller share at the fundamental (**A4-1**).
- **Partial fixes (shape 1, a fix that did not reach the pages citing it), all on the ADR 0027 / 0028 / Q-INRUSH changes:** ROADMAP E6, E12 and the LED-sweep row (**A4-2**); ADR 0005's "typical only" about the converter's current limit (**A4-3**); the load switch's `ON` row (**A4-5**); the `PWR_GND` interface row (**A4-6**); carrier.md's `R1b` drawing (**A4-7**); firmware/README (**A4-8**); the hot-plug rows (**A4-9**); `pcb-pipeline.md` (**A4-11**).
- **Unprotected rating:** the WS2815B-V1's `VDD` absolute maximum is 13.5 V. Nothing on `INST_POS12` clamps between 13.5 V and `D-TVS-PWR`'s 16.7 V breakdown, and `U-ISO`'s own over-voltage protection starts at 13.8 V (**A4-4**).

## Findings

### A4-1 - `C-ISO-Y` does not give `U-ISO`'s switching common-mode current the "way home beside the converter" ADR 0027 claims; at 550 kHz the −12 V entry path through `AGND_MOD` and the star is about 20× lower in impedance

**Severity:** medium
**Node:** `C-ISO-Y`, `ISO_VIN_NEG`, `FB4`/`D4`, `BUS_NEG12_RAW`, `PTC-NEG12`/`D3`/`FB3`, `C3`, `AGND_MOD`, `NT-AGND-MOD`, `BUS_GND`, `NT-DIG-MOD`, `DIG_GND`, `NT-UMB-MOD`, `PWR_GND`.

- The claim: `C-ISO-Y` (1 nF, `ISO_VIN_POS` to `PWR_GND`) "gives the switching common-mode current, driven through the converter's isolation capacitance (1100 pF typ), a way home beside the converter instead of round the star and the ribbon" `[repo] docs/decisions/0027-isolated-instrument-supply.md:139-142`; the same wording is at `[repo] hardware/module/power-entry/power-entry.md:218-224`.
- The netlist `[repo] hardware/module/power-entry/netlist.yaml`:
  - `ISO_VIN_NEG` = `C-ISO-IN.2`, `C2.2`, `FB4.2`, `U-ISO.GND`.
  - `NEG12_D4` = `D4.A`, `FB4.1`.
  - `BUS_NEG12_RAW` = `D4.K`, `PTC-NEG12.1`, the header.
  - `MODULE_ANALOG_NEG12` = `C3.1`, `FB3.2`.
  - `AGND_MOD` includes `C3.2`, `C1.2` and `NT-AGND-MOD.1`.
  - `BUS_GND` = the header grounds, `NT-AGND-MOD.2` and `NT-DIG-MOD.2`.
  - `PWR_GND` = `U-ISO.0V`, `C-ISO-Y.2`, `C-ISO-OUT.2` and `NT-UMB-MOD.1`.
- So a second loop exists from the converter's input side to its output return that does not pass through `C-ISO-Y`: `U-ISO.GND` → `FB4` → `D4` → `PTC-NEG12` → `D3` → `FB3` → `C3` → `AGND_MOD` → `NT-AGND-MOD` → `BUS_GND` → `NT-DIG-MOD` → `DIG_GND` plane → `NT-UMB-MOD` → `PWR_GND`. `D4` and `D3` both carry forward DC (about 0.22 A and 0.04 A), so they pass the AC. A parallel branch runs out the ribbon to the rack PSU's own −12 V and +12 V decoupling.
- At 550 kHz `[ds RECOM-RPA20-AW.pdf PD-2]`:
  - `C-ISO-Y` is 1/(2π·550k·1 nF) = **289 Ω** `[calc]`.
  - The beads (MI1206K601R-10) read about 15 Ω at 1 MHz with no bias and about 5 Ω at 250 mA `[ds datasheets/discrete-and-power/MI1206K601R-10-ferrite-bead.pdf, Z-vs-frequency curve family, read off at its 1 MHz left edge]`, so lower at 550 kHz. That puts `FB4` at about 3 Ω (0.22 A bias) and `FB3` at about 8 Ω `[from the curve, extrapolated]`.
  - The diodes' r_d is about 0.4 and 0.9 Ω, the PTC 0.4 Ω, and `C3`'s ESR is under 1 Ω.
  - Path total ≈ **13 Ω** `[calc, sum]`.
  - `C-ISO-IN` (4.7 µF) ties `ISO_VIN_POS` to `ISO_VIN_NEG` at these frequencies, so `C-ISO-Y` and the −12 V path compete for the same current.
  - Current divides inversely with impedance, so about **95 % of the fundamental goes round the star and through `AGND_MOD`'s `C3` return**. `C-ISO-Y` only wins above roughly 5 MHz: 29 Ω against beads rising to about 50 Ω each.
- The `gnd-isolated` sim does not see this. It is resistive at breath frequency (`f_b` 2 Hz, "the frequency does not enter a resistive result") `[repo] hardware/module/power-entry/sim/sims.yaml:50`.
- How much current: RECOM does not publish it `[ds PD-7 shows no Y-cap and no CM choke]`, so the size of the effect is open. The direction is not. Whether it matters depends on where `C1`/`C3` sit relative to the analog block on `AGND_MOD`, which is a layout fact that does not exist yet.

**What would settle it:** an AC deck of this loop with the bead curve, or at E6 a probe on `AGND_MOD` against `BUS_GND`, and on the pitch jack, at 550 kHz with the instrument drawing. Cheap pre-layout options to evaluate:
- `C-ISO-Y` on `ISO_VIN_NEG` as well, or larger.
- `C3`/`C1` placed at the star with their ground on `BUS_GND` rather than across `AGND_MOD`.
- A common-mode choke at `U-ISO`'s input.

### A4-2 - ROADMAP's E6, E12 and LED-sweep rows still describe the pre-ADR-0027 module: the wrong ground rule at the layout gate, the wrong predicted magnitudes, and no −12 V check

**Severity:** medium
**Node:** `dig-gnd-topology`, `U-ISO`, the rack's −12 V, `PWR_GND`.

- **E12**, the module PCB gate: "**Ground laid out to the star rule in ADR 0004** — one origin at the power inlet, `PWR_GND` and `DIG_GND` each on their own copper" `[repo] ROADMAP.md:53`. ADR 0004's own amendment says those bullets "describe the ground plan before that change" `[repo] docs/decisions/0004-cv-interface-module.md:702-707`. Since ADR 0027, `PWR_GND` is layer-4 copper that **does not reach the header**, joined to `DIG_GND` at the etherCON (`dig-gnd-topology`; `[repo] hardware/module/power-entry/power-entry.md:364-390`). The row sends the layout engineer to the superseded rule.
- **E6:** "±12V … local 5.21V DAC regulator and **bus +5V logic rail** up … load switch limits and ramps" `[repo] ROADMAP.md:47`. The module does not use the bus +5 V `[repo] power-entry.md` Interfaces table. E6 does not mention:
  - `U-ISO`;
  - the PTCs;
  - ADR 0027's own bench item, "the case's −12 V under the instrument's load" `[repo] 0027:198-201`; `grep -n "−12" ROADMAP.md` finds nothing;
  - the `replug-early` measurement that `power-entry-instrument.md` §1a assigns to "E6 decides".
- **"Pitch jack while sweeping the LEDs"**: "this measures the two ground terms that are left — the module's own pour (5.7–7.2 cents) and the rack's shared bus return (~4.8)" `[repo] ROADMAP.md:203`. ADR 0027 removed the instrument's current from both and predicts "**under a hundredth of a cent**" for the same measurement `[repo] 0027:198-200`. The row still budgets the removed terms. This is shape 4: a conclusion that the corrected number now refutes.

**What would settle it:** re-read the three rows against `dig-gnd-topology` and ADR 0027's Consequences.

### A4-3 - ADR 0005's amendment calls `U-ISO`'s current limit "typical only on its datasheet"; the RPA20 sheet gives a range with a minimum

**Severity:** low
**Node:** `U-ISO` over-current protection.

- `[repo] docs/decisions/0005-power-architecture.md:446-449`: "the converter's own limit is meant to sit above them — **typical only on its datasheet, so E6 confirms it**".
- The banked RPA20-AW: "Over Current Protection (OCP) **110%-160%** Output Current, Hiccup" `[ds datasheets/discrete-and-power/RECOM-RPA20-AW.pdf PD-5]`, so the minimum is 1.84 A `[calc 1.1 × 1.67]`. ADR 0027 point 2, `umbilical-load-switch.md:38` and the sim's `i_ocp` all use the 1.84 A minimum.
- "Typical only" is true of the RP20 successor ("150 % typical with no minimum", `[repo] 0027:34-36`) and probably of the MORNSUN part it replaced. The amendment was not updated when `U-ISO` became the RPA20.

### A4-4 - The 13 WS2815B-V1 (`VDD` absolute maximum 13.5 V) are the lowest-rated parts on `INST_POS12`, and no part holds that node below 13.5 V except `U-ISO`'s regulation

**Severity:** low
**Node:** `INST_POS12`, `D-LED-1…13`, `D-TVS-PWR`, `U-ISO`.

- The parts' limits:
  - WS2815B-V1 power supply voltage: absolute maximum **+9.5 to +13.5 V** `[ds datasheets/led/WS2815B-V1.pdf p.2]`; the BOM row repeats it `[repo] hardware/carrier/led-strip-drive/bom.csv:6`.
  - `D-TVS-PWR`: SMAJ15A, 15 V standoff, 16.7 V minimum breakdown, 24.4 V clamp `[ds LITTELFUSE-SMAJ-SERIES-SMAJ15A.pdf]`.
  - `U-ISO`: over-voltage protection at **115–150 % of its output, 13.8–18 V**, hiccup `[ds RECOM-RPA20-AW.pdf PD-5]`.
- A sustained over-voltage from a converter regulation fault, anywhere from 13.5 V up to OVP, therefore reaches 13 parts that cannot be repaired after reflow (ADR 0028) without being clamped. Normal operation is fine: 12 V +3.1 % worst = 12.37 V `[calc, power-entry.md's ±3.1 %]`. Transients are fine as well: an 8/20 µs surge through the on FET into 571 µF moves the node only tenths of a volt `[calc: 10 A × 20 µs / 571 µF = 0.35 V]`, and the hot-plug ring (14.2 V `[sim]`) lands on `J-UMB` while `Q-INRUSH` is off.
- The gap is not stated on any page. `D-TVS-PWR` was sized for a 15 V standoff before the lights became 13.5 V parts.

**What would settle it:** the owner's decision whether a converter fault is in scope. If it is, options include a 13 V-standoff clamp or a crowbar on `INST_POS12` that lets the LT1641 latch.

### A4-5 - The load switch's Interfaces row still says the `ON` divider is "divided from the raw bus"

**Severity:** low
**Node:** `R-ON-HI`, `ON`, `ISO_POS12`.

- `[repo] hardware/module/umbilical-load-switch/umbilical-load-switch.md:24`: "The LT1641's undervoltage-lockout input, divided from the raw bus by `R-ON-HI`/`R-ON-LO`".
- The netlist puts `R-ON-HI.1` on `ISO_POS12` `[repo] umbilical-load-switch/netlist.yaml`, and the same page's §*Its supply* says the `ON` divider is on `ISO_POS12`. Shape 1.

### A4-6 - `power-entry-instrument.md` still sends the instrument's return "to the module star"

**Severity:** low
**Node:** `PWR_GND` at `J-UMB`.

- `[repo] hardware/carrier/power-entry-instrument/power-entry-instrument.md:26`: "This board's only supply return, down the umbilical to the module star".
- Since ADR 0027 it returns to `U-ISO`'s 0V and reaches the star only through `DIG_GND`, carrying none of the instrument's DC current there (`dig-gnd-topology`; `[repo] power-entry.md:385-390`). Shape 1. A reader sizing return copper at the module from this row would get the topology wrong.

### A4-7 - carrier.md's §2 drawing ends `R1b` at the "analog star point"; the layout rule takes `AGND_SENSE` at the sensor's own `GND` pin

**Severity:** low
**Node:** `R-SER-BREATH-INST` (`R1b`), `AGND_SENSE`, `U-BREATH` pin 3.

- The drawing: `J-UMB pin 2 AGND ──[R-SER-BREATH-INST 1k]──┴── analog star point … └──[single tie]── PWR_GND` `[repo] hardware/carrier/carrier.md:156-158`.
- The rule: "`AGND_SENSE` is taken at the sensor's own `GND` pin … not at the star … `R1b`'s star end is a trace of its own from pin 3's pad, not a via into the pour" `[repo] hardware/interfaces/breath-sense-link/breath-sense-link.md`, *Where it sits*.
- The netlist cannot tell the two apart (both are `AGND_INST`; main-board `R39.1` is on `AGND_INST`), so the drawing is the only picture of the rule, and it shows the opposite. That costs a layout engineer the very thing that makes the 13 mA island drop common-mode.

### A4-8 - firmware/README still describes "the LED strip (one, ADR 0016)"

**Severity:** low
**Node:** the LED row (`D-LED-1…13`), firmware contract.

- `[repo] firmware/README.md:5-6` and `:21` ("A matrix or strip update"). The lights are 13 on-board LEDs since ADR 0028. Shape 1.
- Related (advisory): neither the shared thermal clamp nor blank-at-boot, which ADR 0005's load table and ADR 0014 depend on, appears in the firmware contract; `firmware/README.md:123-139` lists only zero, deadband and span, and points to ADR 0014.

### A4-9 - The "hot-plug at the LT1641's 1.10 A limit, ~0.68 A per rail for tens of ms" rows describe a hot-plug that `Q-INRUSH` removed; the cases that remain are different

**Severity:** low
**Node:** `U-ISO`, `PTC-ISO`, the rack rails.

- The stale rows: `[repo] hardware/module/power-entry/power-entry.md:191` (table row) and `:260` (`PTC-ISO` "must hold … 0.68 A hot-plug for tens of ms"); `[repo] docs/decisions/0027-isolated-instrument-supply.md:180-181`.
- What the sim shows since `Q-INRUSH` `[sim hardware/carrier/power-entry-instrument/sim, re-run 13197f8]`:
  - hot-plug: `U-ISO` 0.49–0.54 A;
  - cold-start: 0.50–0.53 A;
  - `t_at_ocp`: 0 on every hot-plug corner.
- The cases left are a `Q-INRUSH` short, which `umbilical-load-switch.md:239-244` keeps as the timer's sizing case, correctly, and `replug-early`. `replug-early` puts `U-ISO` at its **1.84 A** clamp for 97–453 µs `[sim, same run]`, about 1.2 A per rail `[calc: 1.84 × 12 / 0.85 / 22.2]`. That is brief and not the 0.68 A of the row.
- The row is conservative, but it names the wrong event. Shape 2: the explanation restates a mechanism the fix removed.

### A4-10 - ADR 0027 and the power-entry sim restate the LED row's current with the provenance "[owner brief, not yet in the corpus]" instead of citing `led-row-current`

**Severity:** low
**Node:** `led-row-current`.

- `[repo] docs/decisions/0027-isolated-instrument-supply.md:52-54` ("170–195 mA at 12 V full white `[owner brief 2026-09-30, not yet in the corpus]`").
- `[repo] hardware/module/power-entry/sim/sims.yaml:49` (`i_swing` source, same tag).
- The figure is in the register now, owned by `led-strip-drive.md` and blocked on E6. The two restatements will not follow it when E6 moves it, and their provenance tag is false. Rule 1.

### A4-11 - `docs/reference/pcb-pipeline.md` still tells the module layout "`PWR_GND` as a trace … a two-terminal net" and prices the star pad "at 359 mA"

**Severity:** low
**Node:** `PWR_GND` (module), `BUS_GND` star.

- `[repo] docs/reference/pcb-pipeline.md:265-266, 272-274`.
- Since ADR 0027, module `PWR_GND` has nine endpoints on `module-main` (`U-ISO.0V`, `C-ISO-OUT`, `C-ISO-Y`, the load switch's four returns, `NT-UMB-MOD`, `J3.6`) on its own layer-4 copper `[repo] hardware/boards/module-main/board-netlist.yaml`. None of the instrument's 359 mA crosses the star. The page is marked "Proposed … Not run", but it is in the §6 corpus.

### A4-12 - The instrument's arriving voltage is carried at two values; 11.4 V still subtracts a Schottky that has not been in the umbilical path since ADR 0027

**Severity:** advisory
**Node:** `UMBILICAL_POS12` at `J-UMB`, `INST_POS12`.

- `[repo] docs/decisions/0005-power-architecture.md:96` gives "122 mV cable + 400 mV Schottky + 60 mV → ~11.4 V". It is used by:
  - `power-entry-instrument.md:95` (1.26 W at 11.4 V, `R_neg` −103 Ω);
  - the sim's `v_nom` 11.4 `[repo] power-entry-instrument/sim/sims.yaml`.
- `D2` now sits on `U-ISO`'s input `[repo] power-entry.md:52-54`. The instrument sees `U-ISO`'s 12 V less the sense resistor and FET (0.36 A × 53.5 mΩ = 19 mV `[calc]`) and the cable, which is about 11.8 V. `power-entry-instrument.md:190` already uses 11.8 V.
- The 11.4 V side is conservative for `R_neg` and for `umbilical-current`. Separately, ADR 0004's amendment gives ~0.26/0.25 A per rail `[repo] 0004:299-301` where `power-entry.md:193-195` gives ~0.27/0.26 A, another restatement 10 mA apart.

### A4-13 - The LED row's PWM (2 kHz scan, 4 kHz refresh) sits on `U-ISO`'s input-LC resonance (3.3 kHz); audio-band ripple reflected to the rack's ±12 V is not analysed

**Severity:** advisory
**Node:** `L-ISO-IN`/`C2`, `BUS_POS12_RAW`/`BUS_NEG12_RAW`.

- The WS2815B-V1 states "scan frequency is of 2KHz" and "Refresh Frequency updates to 4KHz" `[ds WS2815B-V1.pdf p.1]`.
- `power-entry-instrument.md:303-308` says "the umbilical and the load switch supply most of" the row's PWM step. That current therefore reaches `U-ISO`, and its input current follows it.
- `L-ISO-IN` with `C2` has f₀ = 3.3 kHz and Z₀ = 0.46 Ω against `C2`'s ~0.34 Ω, so Q ≲ 1.35 `[repo] power-entry.md:211-216; calc`. It does not attenuate at 2–4 kHz, and gains about 1.3–1.6 near f₀ `[calc: |1/(1−(f/f₀)²)| with damping]`.
- Upper bound, PWM in phase at mid duty:
  - the 0.195 A step becomes 0.195 × 12 / 0.82 / 23.4 ≈ 0.12 A per rail `[calc]`;
  - with Q that is about 0.16 A p-p;
  - into ~0.08 Ω of ribbon and bus (`r_rib_rail` + `r_bus_rail`, `[repo] power-entry/sim/sims.yaml`) that is about **13 mV p-p of 2–4 kHz on the case's rails** `[calc]`.
- This module's analog rails reject it (OPA2197 PSRR) and pitch is unaffected to under 0.001 cents `[calc: 13 mV × 1e-4]`. Other modules in the case see an audible-band tone. ADR 0027 analyses breath frequency only (`f_b` 2 Hz).

**What would settle it:** E6, a scope on the bus +12 V and −12 V with the row at mid brightness.

### A4-14 - The SPI analysis treats `DIG_GND` as ideal, but pin 8 carries about half the instrument's return; the offset fits in the margin. `CABLE-UMB`'s shield goes nowhere

**Severity:** advisory
**Node:** `DIG_GND` (pin 8), `PWR_GND` (pin 6), `CS_MOD`/`MOSI`, `CABLE-UMB`.

- Pins 6 and 8 are tied at both ends (`NT-DIG`, `NT-UMB-MOD`), so DC splits about half and half `[repo] power-entry.md:391-397`. The instrument's ground therefore sits above the module's by I·R(6∥8):
  - 0.09 Ω at 24 AWG (2 m at 90 Ω/km, two conductors in parallel `[ds BELDEN-1752A …pdf p.1, as the sims read it]`);
  - up to 0.23 Ω at 28 AWG, the gauge `CABLE-UMB` leaves open `[repo] hardware/bom.csv` `CABLE-UMB`.
- The offset is 32 mV typical (0.36 A, 24 AWG), and at worst **0.26 V** (1.10 A just under the trip, 28 AWG) `[calc]`.
- The SPI sims do not include it `[repo] hardware/interfaces/spi-link/sim/README.md`. The worst static case they report is `MOSI` held low at 0.33 V against the 74AHCT14's lowest `V_T+` of 0.9 V, a 0.57 V margin, so the offset fits. It belongs in the record.
- The BOM row asks for "Cat5e **STP** … Shielded preferred", but both etherCONs' G tabs are on no net (ADR 0027, *What it is not*), so the shield is terminated at neither end. Either drop the preference or say what the shield is for.

### A4-15 - On USB power alone, `INST_POS12` is dead, so there is no breath and no LEDs, while the LED buffer is live and can drive unpowered LED inputs

**Severity:** advisory
**Node:** `INST_5V_A`, `U-LVLSHIFT`, `LED_DI`, `INST_POS12`.

- ADR 0005 keeps the USB OR "so the instrument runs on the bench during development without a rack attached" `[repo] 0005:427-431`. Since the REF5050, OPA2197 and LED row moved to the 12 V rail, USB alone powers the MCU, matrix and keys only. No page says so.
- `U-LVLSHIFT`'s `VCC` is `INST_5V_A`, the Matrix's 5 V pad, which USB feeds `[repo] carrier/netlist.yaml` `INST_5V_A`. If firmware writes the row on USB power, 5 V edges go through `R-LED-SER` into `DIN1`/`DIN2` of LEDs whose `VDD` is 0 V. That phantom-feeds `INST_POS12` through the input structure, at up to 5 V / 330 Ω = 15 mA `[calc]`, past the WS2815B-V1's `V_I` −0.3…5.7 V rating referred to a supply that is absent `[ds p.2]`.
- Firmware has no 12 V-present sense to gate on.

**What would settle it:** one line on `power-entry-instrument.md` or ADR 0005, and a firmware rule (or a sense divider on a spare GPIO).

## Checked and holds

**`Q-INRUSH`**
- Plug-in step: ΔV_GS = −12 × 22.055 nF / 1.0227 µF = −0.26 V, against V_GS(th) −0.5 V minimum `[calc; ds AOS-AO3401A.pdf p.2: −0.5/−0.9/−1.3 V]`.
- Delay: τ = 0.5 MΩ × 1.02 µF = 0.51 s, and to the plateau 0.51 × ln(5.9/4.4) = 0.15 s `[calc]`.
- Ramp: 8.8 µA / 22 nF = 400 V/s, which is 0.23 A into 571 µF (470 + 100 + 13 × 0.1) `[calc]`.
- On: R_DS(on) ≤ 60 mΩ at −4.5 V `[ds p.2]`. V_GS ±12 V absolute maximum, V_DS −30 V `[ds p.1]`.
- Single pulse ~12 W and Z_θJA ≈ 0.1 × 125 = 12.5 K/W at 50 ms `[ds p.4 Figs 10–11, read off]`.
- The sim re-run reproduces the README: hot-plug `U-ISO` 0.491–0.544 A, `Q-INRUSH` ≤ 1.79 W, ring 14.24 V under the 15 V standoff, `VCC` 11.996 V; cold-start 108–238 ms; `replug-early` reaches the 1.84 A clamp (a recorded hazard) `[sim]`.

**Rollover lead (3↔6, 7↔8, …)**
- `D-REVSHUNT` (SS34, at `UMBILICAL_POS12` ahead of `Q-INRUSH`) clamps at one diode drop.
- The parasitic path (LED `GND`→`VDD` substrate diode, then `Q-INRUSH`'s body diode) is two drops, so it stays off and the SS34 takes the fault until the LT1641 latches `[repo] power-entry-instrument/netlist.yaml; calc]`.
- The netlist is as drawn: `UMBILICAL_POS12` = `C-INRUSH-GS`, `D-REVSHUNT.K`, `D-TVS-PWR.K`, `Q-INRUSH.S`, `R-INRUSH-GS`.

**The eight conductors**
- Pin map `umbilical-pinmap` at `umb-adapter` (J1.n = J2.n for n = 1…8), main board `J6` and module-main `J3` `[repo] board-netlist.yaml ×3`.
- Pin 3 carries 0.36 A typical, 0.58 A clamp-legal and ≤ 1.10 A just under the trip, against the etherCON's 1.5 A per contact `[repo] bom.csv J-UMBILICAL-INST` and `J-UMB`'s 3 A pins.
- Pins 6 and 8 split the return.
- Pin 2 (`AGND_SENSE`) carries only in-amp bias through 1 MΩ.
- Pins 1, 4, 5 and 7 carry signal only.

**The LED row**
- Data: `LED_DI` → `D-LED-1.DIN1` + `D-LED-2.DIN2`; `LED_Dk` → `D-LED-(k+1).DIN1` + `D-LED-(k+2).DIN2`; `D-LED-1.DIN2` on `PWR_GND`; `D-LED-13.DO` open `[repo] led-strip-drive/netlist.yaml]`.
- 13 `C-LED` on `VDD` (pin 2), and pin 1 is NC `[ds WS2815B-V1.pdf p.2]`.
- Thresholds: `V_IH` 2.7 V, `V_IL` 1.5 V, `C_I` 15 pF, `T0H` 220–380 ns, RES > 280 µs, all at `VDD` = 12 V `[ds p.3]`.
- Row current: 0.18 W / 12 V = 15 mA per LED, 195 mA for the row `[calc; ds p.2]`. Quiescent < 2 mA each `[ds p.3]`.
- PWM sag: 0.195 × 250 µs / 470 µF = 0.10 V `[calc]`, and conservative, because the datasheet also states a 4 kHz refresh.
- `R-LED-SER`: 330 Ω × 30 pF gives a ~22 ns edge, and a shorted pin draws 15 mA against the AHCT's ±25 mA.
- Row plus `umbilical-current` = 0.554 A, 0.226 A under the 0.78 A minimum trip `[calc]`.

**`U-ISO` load arithmetic** (`power-entry.md:186-192`)
- 4.3 W → 0.224 A per rail at 82 %; 6.95 W → 0.369 A; 9.36 W → 0.489 A; 13.2 W → 0.678 A `[calc]`.
- 9–36 V input range, UVLO 8–9 V, quiescent 20/55 mA, 550 kHz, 1000 µF capacitive-load limit for the 2412SAW `[ds PD-1, PD-2]`.
- Output capacitance after a start (`C-ISO-OUT` 100 µF plus the instrument's 571 µF behind the Miller ramp) stays under that limit.

**Ground topology, instrument end**
- `PWR_GND` is one node holding the plane, all clamps (`D-REVSHUNT`, `D-TVS-PWR`, `U-TVS-SPI.GND`, both `D-TVS-BREATH`), `NT-DIG.2`, `NT-AGND.2`, the LED grounds and the `J-CHAIN` grounds.
- `AGND_INST` holds the sensor, REF5050, OPA2197 V−, `U-ADC.VSS`, `D-REF-CLAMP` and `R39.1`, with one tie `NT2` `[repo] main-board/board-netlist.yaml]`.
- `U-TVS-SPI` on the pad side of `R-SPI-SER` is still beside `J-UMB` `[repo] spi-link.md:47, 102-104]`, consistent with §2.

**Ground topology, module end**
- `PWR_GND` = `U-ISO.0V`, the load switch's returns, `C-ISO-Y`, `C-ISO-OUT`, `NT-UMB-MOD`, `J3.6`. `DIG_GND` reaches `BUS_GND` only via `NT-DIG-MOD`. `AGND_MOD` reaches it only via `NT-AGND-MOD` `[repo] module-main/board-netlist.yaml, power-entry/netlist.yaml]`.
- The DC argument of ADR 0027 holds: none of the instrument's DC crosses the star. A4-1 is about the AC.
- The panel LED (`UMBILICAL_POS12` → 2.2 kΩ → `AGND_MOD`) is the one deliberate DC crossing. Its breath-correlated part is 0.195 A × 53.5 mΩ / 2.2 kΩ ≈ 4.7 µA `[calc]`, which is negligible.

**Breath link common mode from the instrument's return current** (re-derived; no page states it)
- Ground offset: DC 32–85 mV typical, and the LED swing 18–46 mV at 24–28 AWG `[calc as A4-14]`.
- Against `breath-link-cmrr` (70.5 dB at 60 Hz worst) that is ≤ 14 µV at the in-amp output at breath frequencies `[calc: 46 mV × 10^(−70.5/20)]`.
- At the 2 kHz PWM, with CMRR falling about 20 dB/decade from 58.5 dB at 480 Hz to roughly 46 dB, it is ≤ 0.23 mV `[calc]`.
- Both are far below the breath channel's resolution, so the plane/island/single-tie scheme holds.

**Input-LC damping:** the sim margin is 55× worst and 181× nominal, with a 0.57 Ω peak at 3.85 kHz `[sim]`, which matches `instrument-input-z-margin`.

**Checkers:** `check-netlist --strict` reports 0 problems. `check-staleness` reports no figure, pattern or BOM failure in this slice.
