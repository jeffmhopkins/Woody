# VERIFIED — fixer F3 (A4, A5)

**Base:** `claude/car-instrument-cad-design-xvqwv2` at `9956171`, merged into
this branch. `tools/` not modified. **Ids owned:** every `A4-*` and `A5-*`
(29). Each was checked against the corpus at the base before acting.

**Counts:** 26 CONFIRMED (three of them advisory), 3 PARTLY (A4-12, A5-9,
A5-14), 0 REFUTED, 0 DUPLICATE. Fixed in full in this fixer's domain: 17.
Fixed here and handed in part: 6 (A4-1, A4-9, A4-10, A4-12, A5-9, A5-10).
Handed whole: 4 (A4-3, A4-5, A4-11, A5-6). OWNER: 3 (A4-1, A4-4, A5-2), each
with options below; A4-4 and A5-2 are also recorded on their pages.

**Domain** (from the orchestrator): `hardware/carrier/power-entry-instrument`,
`led-strip-drive`, `service-uart`, the carrier root; `hardware/interfaces/spi-link`,
`key-chain-loom`; `hardware/cluster/*`; `firmware/**`;
`docs/reference/latency-budget.md`; ADRs 0001, 0015, 0027, 0028; ROADMAP rows
about power, LEDs, the link and keys; their figures. **HANDED** below names
files outside it; the fixer owning each is not named in this brief, so the
path is given and the orchestrator routes it.

| Id | Verdict | Action | Evidence |
|---|---|---|---|
| A4-1 | CONFIRMED | ADR 0027 point 4 amended and a dated amendment added (*the converter's common-mode current*); bench item added to ADR 0027 and ROADMAP E6. **OWNER** (below). **HANDED**: the same claim in `hardware/module/power-entry/power-entry.md` (≈218–224) and the `C-ISO-Y` BOM row (`module/power-entry/bom.csv`) | `[repo] module/power-entry/netlist.yaml`: the loop `PWR_GND`→`NT-UMB-MOD`→`DIG_GND`→`NT-DIG-MOD`→`BUS_GND`→`NT-AGND-MOD`→`AGND_MOD`→`C3`→`FB3`→`D3`→`PTC-NEG12`→`D4`→`FB4`→`ISO_VIN_NEG` exists as the report says. `[sim]` AC deck `F3-u-iso-cm-loop/` (template, runner, `results.txt`), ngspice 42, unit CM drive through 1.1 nF, beads from `[ds MI1206K601R-10-ferrite-bead.pdf]` (≈2.2 µH at 0 A, ≈0.85 µH at 250 mA), other parasitics estimated: as netlisted 1–2 % of the 550 kHz fundamental through `C-ISO-Y`, 88–98 % across the star, 12–43 % through `AGND_MOD`. Bigger `C-ISO-Y` alone resonates with the loop (47 nF: star 308 % at 550 kHz) |
| A4-2 | CONFIRMED | ROADMAP E6, E12 and the LED-sweep row rewritten to ADR 0027 / `dig-gnd-topology`; E6 gains the −12 V load, `replug-early`, and the two noise checks | `[repo] ROADMAP.md:47,53,203` against `0027:198-201` and `0004`'s own amendment |
| A4-3 | CONFIRMED | **HANDED**: `docs/decisions/0005-power-architecture.md` ≈446–449 ("typical only") | `[ds RECOM-RPA20-AW.pdf PD-5]` "Over Current Protection 110 %-160 %"; ADR 0027 point 2 and the sim's `i_ocp` already use the 110 % minimum |
| A4-4 | CONFIRMED | Gap stated on `power-entry-instrument.md`, *The 13.5 V rating on this rail*. **OWNER** (below); no part added | `[ds WS2815B-V1.pdf p.2]` VDD +9.5…+13.5 V; `[ds LITTELFUSE-SMAJ-SERIES-SMAJ15A.pdf]` V_BR 16.7 V min; `[ds RECOM-RPA20-AW.pdf PD-5]` OVP 115–150 % (13.8–18 V) |
| A4-5 | CONFIRMED | **HANDED**: `hardware/module/umbilical-load-switch/umbilical-load-switch.md:24` ("divided from the raw bus" → `ISO_POS12`) | `[repo] umbilical-load-switch/netlist.yaml` `R-ON-HI.1` on `ISO_POS12` |
| A4-6 | CONFIRMED | Fixed: the `PWR_GND` interface row on `power-entry-instrument.md` now returns to `U-ISO`'s 0V and cites `dig-gnd-topology` | `[repo] module/power-entry/netlist.yaml` `PWR_GND` = `U-ISO.0V`, `C-ISO-Y.2`, `C-ISO-OUT.2`, `NT-UMB-MOD.1` |
| A4-7 | CONFIRMED | Fixed: `carrier.md` §2 drawing ends `R1b` at `U-BREATH` pin 3 by its own trace, the island's single tie drawn separately (no bracketed label, so the drawing parser is unaffected) | `[repo] breath-sense-link.md`, *Where it sits*; `check-netlist --strict` 0 problems after |
| A4-8 | CONFIRMED | Fixed: `firmware/README.md` says the LED row (ADR 0028) and "matrix or LED-row update"; the advisory part — shared lighting budget and blank-at-boot — is now in *What the hardware requires*, *The lights* | `[repo] firmware/README.md:5-6,21` at base |
| A4-9 | CONFIRMED | Fixed in ADR 0027 *Consequences* (dated amendment: the hot-plug now draws `hotplug-iso-ocp`; `replug-early` 0.1–0.45 ms at the 1.84 A clamp, ~1.2 A per rail; a `Q-INRUSH` short). **HANDED**: `hardware/module/power-entry/power-entry.md:191` and `:260` (`PTC-ISO` "0.68 A hot-plug") | `[sim] python3 tools/sim.py show hardware/carrier/power-entry-instrument/sim`: `replug-early` `i_iso_peak` 1.837 A, `t_at_ocp` 97–453 µs |
| A4-10 | CONFIRMED | Fixed in ADR 0027 (now cites `led-row-current`, owner `led-strip-drive.md`). **HANDED**: `hardware/module/power-entry/sim/sims.yaml:49` `i_swing` source tag (a module sim; changing it re-runs that dir) | `[repo] config/figures.yaml` `led-row-current` |
| A4-11 | CONFIRMED | **HANDED**: `docs/reference/pcb-pipeline.md` ≈265–274 (not in F3's domain list) | `[repo] hardware/boards/module-main/board-netlist.yaml` `PWR_GND` has nine endpoints |
| A4-12 | PARTLY | `power-entry-instrument.md`'s derivation now says the arriving voltage is ~11.8 V and that 11.4 V is the conservative side (margin ~130× at 11.8 V). **Not changed**: `power-entry-instrument/sim` `v_nom` 11.4 (conservative for every assertion there; re-deriving it moves settled figures, so it waits on ADR 0005). **HANDED**: ADR 0005:96 (the 400 mV Schottky term) and ADR 0004 ≈299–301 per-rail figures | `[calc]` 12 V − 19 mV (sense + FET) − ~0.1 V cable − 22 mV `Q-INRUSH` ≈ 11.85 V; `[repo] power-entry-instrument.md:190` already used 11.8 V |
| A4-13 | CONFIRMED (advisory) | Recorded as a residual row in ADR 0027 and as an E6 check (bus ±12 V at 2–4 kHz, row at mid brightness). Not analysed further: the input LC is the module's (`power-entry.md`) | `[ds WS2815B-V1.pdf p.1]` 2 kHz scan / 4 kHz refresh; `[repo] power-entry.md` f₀ ≈ 3.3 kHz |
| A4-14 | CONFIRMED (advisory) | Ground-offset paragraph added to `spi-link.md` (fits the 0.57 V margin). `CABLE-UMB` (`hardware/unplaced.csv`) no longer asks for a shield nobody terminates; `hardware/bom.csv` regenerated | `[calc]` 0.36 A × 0.09 Ω = 32 mV; 1.10 A × 0.23 Ω = 0.25 V; `[repo] 0027` *What it is not* (G tabs on no net) |
| A4-15 | CONFIRMED (advisory) | `power-entry-instrument.md` *On USB power alone*; firmware rule in `firmware/README.md` *The lights*: write the row only while the breath ADC reads the sensor's zero-pressure offset (the existing hardware as a 12 V sense — no part added) | `[repo] led-strip-drive.md` `OE` ×4 tied low; `breath-adc.md` *rest* line; sensor, `U-REF-BREATH`, `U-BUF` on `INST_POS12` |
| A5-1 | CONFIRMED | **Settled by simulation and moved into the firmware contract.** New `spi-link/sim` deck `frame.cir`, sims `frame-timing` (asserted, 195 runs) and `frame-timing-cs-released-at-last-edge` (recorded). With `CS_MOD` falling by `SCLK`'s first rising edge, held 250 ns past the last falling edge and high 250 ns between frames, the DAC's t1/t4/t5/t8/t6/t7/t9/t10 hold at its pins at every corner and `z_cm`, worst receiver-threshold pair, full 2×74AHCT14 + 74AHCT125 spread (19.5 ns). Tightest: t8 ≥ 121 ns, t4 ≥ 206 ns. Released on the last edge: t8 = −103…−128 ns, frame lost. Required at the pads: hold ≥ 139 ns, high ≥ 124 ns. Written into `firmware/README.md`, `spi-link.md`, `sim/README.md`. **E11** confirms at the pads and at the DAC pins | `[ds DAC8568CIPW.pdf p.7]` t1 10, t4 80, t5 13, t8 10, t9 6, t10 4 ns; `[ds SN74AHCT14.pdf p.6]` 1–8 ns at 15 pF; `[ds SN74AHCT125.pdf p.4]` 1–6.5 ns; `[sim] python3 tools/sim.py run hardware/interfaces/spi-link/sim`: 1430 runs, 32 assertions, 0 failed |
| A5-2 | CONFIRMED | **Simulated; not closable from the datasheet → OWNER + bench.** New `key-chain-loom/sim` deck `hold.cir`: `hop-hold-lt-to-rh` (asserted against the bench criterion) and `hop-hold-with-series-r` (recorded). Only `left_thumb` → `right_hand` can race (the other two hops feed a main-board register, clocked first). Clock skew 5.7–12.1 ns; with zero propagation delay the data beats `right_hand`'s clock by 0.7–10.9 ns, so the hop holds only if `left_thumb`'s CLK→QH ≥ 10.9 ns; TI publishes a maximum only. **E14 must show**: at `right_hand`'s pins, `SER` (J-CHAIN pin 7) steady ≥ 1 ns after `CLK` (pin 11) crosses mid-rail on both data edges, marker counter zero over a long run. Page: `key-chain-loom.md` *The hop hold time*; `key-register.md`, ADR 0001 amendment | `[ds SN74HCS165-ti-scls828a.pdf p.7]` tpd max 16/18 ns at 4.5 V, SER hold 0 ns; `[sim] python3 tools/sim.py run hardware/interfaces/key-chain-loom/sim`: 338 runs, 11 assertions, 0 failed |
| A5-3 | CONFIRMED | Fixed: `firmware/README.md` gains *What the hardware requires of firmware* — SPI2 (DAC mode 1, 2 MHz, `CS_MOD` intervals from A5-1, MCP3202 0.9 MHz mode 0,0/1,1, 24 clocks, tSUCS/tCSH, polling on an acquired bus, refresh-all), SPI3 (mode 2, 1 MHz, receive-only, `SH/LD` as positive-polarity CS or a GPIO pulse with its 7 ns low / 21 ns setup, marker check and its limit, two-sample gate, `IO33` static, self-test drive), `IO2`/`IO3`, `EN`/`IO0`, the lights. "Fire immediately" replaced by ADR 0001's two-sample gate | `[ds MCP3202-CI-SN.pdf p.1, p.3, p.17]`; `[ds SN74HCS165 p.6-7]`; `[repo] spi-link.md:217,240`; `key-marker-and-bits.md` (mid-shift reload) |
| A5-4 | CONFIRMED | Fixed in contract and page: self-test drives `IO33` as a GPIO changed only while `SCK` is idle; constant-level tests exact, a pattern test accepts a one-bit shift (`key-chain-loom.md`, `firmware/README.md`). Not simulated: the direction of the race depends on the two RC loads, and the contract removes it rather than sizing it | `[ds SN74HCS165 p.7]` SER hold 0 ns; `[repo] key-chain-loom.md` main-board end (SCK's load is both thumbs + two ribbons + TVS) |
| A5-5 | CONFIRMED | Fixed: `latency-budget.md` header, rules 3 and 4 and the characterisation table rewritten to ADR 0015 (one MCU, no radio, lighting on the other core via RMT); WiFi-burst and inter-MCU UART rows replaced by a loop-timing-with-lights row | `[repo] docs/decisions/0015-one-mcu-no-display.md:5-7` |
| A5-6 | CONFIRMED | **HANDED**: `hardware/module/digital-and-supervision/bom.csv` `R-RX-MOD` and `digital-and-supervision.md` ≈104–106 — the settled high is ~3.26 V at the cable node, not 2.97 V | `[repo] digital-and-supervision/netlist.yaml` pulls at the cable node; `[calc]` 3.3 × 10 000 / 10 117 = 3.26 V |
| A5-7 | CONFIRMED | Fixed: `R-CS-PULL-MOD` row (`spi-link/bom.csv`) now names `U-RX-MOD`, its 0.5 V `V_T−` and the 50 mV margin; `spi-link.md`'s four-state table now reads the receiver's band and marks the instrument-off row "not guaranteed, harmless" | `[ds SN74AHCT14.pdf p.5]` V_T− 0.5 V min; `[calc]` 5 × 10k/110k = 0.455 V |
| A5-8 | CONFIRMED | Fixed: "still disputed" removed from the `J-UMB` row; `hardware/bom.csv` regenerated | `[repo] config/figures.yaml` `dig-gnd-topology` `status: settled` |
| A5-9 | PARTLY | Fixed on `spi-link.md` ("three of the five `R-SPI-PULL`"); the section heading "six, not three" counts pulls, not `R-SPI-PULL` rows, and stands. **HANDED**: `digital-and-supervision.md:30` and its drawing label ≈63–64, and `link-supervision.md` ("the six `R-SPI-PULL`") | `[repo] spi-link/bom.csv` `R-SPI-PULL` qty 5 |
| A5-10 | CONFIRMED | Fixed: `spi-link.md` (dated note under the pulls section) and the `R-SPI-PULL` row now say why the DAC-side pulls stay; ADR 0001 "number on the display" amended to the matrix. **HANDED**: `hardware/module/link-supervision/link-supervision.md` ("a display to report on") | `[repo] digital-and-supervision/netlist.yaml` `U-LVL-MOD.*OE` on `DIG_GND`; ADR 0015 |
| A5-11 | CONFIRMED | Fixed: `spi-link.md` now gives the datasheet's second FSPI IO_MUX set and says the design has `SCLK`/`MOSI` reversed against it, not swapped (shielding order) | `[ds ESP32-S3-datasheet-v2.2.pdf Table 2-4, p.21-22]` GPIO34 FSPICS0, 35 FSPID, 36 FSPICLK, 37 FSPIQ (re-read) |
| A5-12 | CONFIRMED | Fixed: `spi-link.md` (table row and paragraph), the `R-SPI-SER` row and `spi-series-r`'s derivation say 40 mA is typical drive, not a limit. No value moves | `[ds ESP32-S3-datasheet-v2.2.pdf p.64 Table 5-1]` cumulative 1500 mA only, 24 h short footnote; `p.65 Table 5-4` |
| A5-13 | CONFIRMED | Fixed: `loop-budget` re-derived and moved per CLAUDE.md rule 2 to **186–227 µs of 250 µs** (polling; chain concurrent vs serialised; 7 or 8 transactions × 9 µs + 122.7 or 154.7 µs). ADC term unified at 24 clocks / ~27 µs; key-path DAC term ~106 µs like the breath path; totals 0.42–0.67 ms. Old spellings grepped first (`196–241 µs`, `196-241 us`) and added to `forbidden` with the two old row spellings | `[calc]` 7 × 9 + 96 + 26.7 = 185.7; 8 × 9 + 154.7 = 226.7; interrupt 290.7 / 346.7. The old 196/241 reproduce from no transaction count |
| A5-14 | PARTLY (advisory) | ADR 0001's Consequences line amended to cite `config/key-layout.yaml` `counts` and say which bits the old sentence leaves out. The existing 2026-09-26 note already flagged the move; the advisory part was the unexplained 3 | `[repo] config/key-layout.yaml` `counts.total: 19` |

## OWNER items

### A4-1 — `U-ISO`'s common-mode current crosses the star

Analysis in ADR 0027's 2026-10-01 amendment; the deck is
`F3-u-iso-cm-loop/` in this directory (`python3 run.py` regenerates
`results.txt`; every parasitic not in a banked document is marked an
estimate in the template).

| Option | Star share at 550 kHz / 1.65 MHz | Cost | Note |
|---|---|---|---|
| 1. CM choke at `U-ISO`'s input (~1 mH CM, ≥1 A), `C-ISO-Y` 1 nF | 8 % / 0.8 % | one two-line SMD choke, ~$0.5–1.5 `[from memory]`, to be chosen and banked | **Recommended.** Its leakage joins `L-ISO-IN`: re-sim the input filter's damping |
| 1b. the same with `C-ISO-Y` 10 nF | 0.8 % / 0.1 % | the same | |
| 2. `C-ISO-Y` 220 nF + 1 Ω series | 45 % / 7 % | two passives | partial; no magnetics |
| 3. leave it, probe at E6/E11 | 88–98 % / ~100 % | none now | a respin if it shows |
| (not recommended) `C-ISO-Y` 10–47 nF alone | 109–308 % | — | resonates with the loop |

### A4-4 — nothing clamps `INST_POS12` between 13.5 V and 16.7 V

| Option | Parts | Cost | Note |
|---|---|---|---|
| a. Accept: a converter that fails regulating high is out of scope | none | — | **Recommended** unless the owner wants the LEDs protected against a supply fault: RECOM's OVP (13.8 V min) is close above, and the window is a fault of the converter itself |
| b. Crowbar on `INST_POS12`: a TL431 reference with a 1 % divider set ~13.0 V driving a small SCR (or an N-FET) across the rail, so the module's LT1641-1 limits and latches | TL431, SCR/FET, 3 resistors, 1 cap (~6 parts) | ~$0.2 + placement | Window is tight: normal max 12.37 V (12 V + 3.1 %), abs max 13.5 V. A plain zener (BZT52C13, 12.4–13.7 V) is too wide; the TL431 holds ~±1.5 %. `Q-INRUSH` carries the LT1641's limit until its timer latches |
| c. A lower TVS (SMAJ11A/12A) | 1 | ~$0.1 | **Not a fix**: SMAJ12A breaks down at 13.3–14.7 V and clamps far above that at current; SMAJ11A's 11 V standoff is under the rail's 12.37 V worst |

### A5-2 — the `left_thumb` → `right_hand` hop holds only on an unpublished delay

| Option | Margin with zero propagation delay | Cost |
|---|---|---|
| a. Accept, and make E14 show it (criterion above) | −0.7 to −10.9 ns (needs tpd ≥ 10.9 ns) | none |
| b. 2.2 kΩ in series at `left_thumb`'s `QH` on `HOP_LT_RH` (main board) | +3.2 to +22 ns (`hop-hold-with-series-r`) | one resistor on the main board's sheet and layout; data still arrives within 30 ns of a 1 µs period |
| c. Clock the chain from the data end (reverse `SCK` routing) | not simulated | a re-route of the loom |

Recommendation: **b** if the main board is not yet frozen — it costs one
resistor and removes the dependence on a figure TI does not publish; else **a**.

## HANDED (files outside F3's domain)

- `hardware/module/power-entry/power-entry.md` ≈218–224 and the `C-ISO-Y` row: the "way home beside the converter" claim (A4-1) — point at ADR 0027's 2026-10-01 amendment.
- `hardware/module/power-entry/power-entry.md:191, :260`: the 0.68 A hot-plug rows (A4-9).
- `hardware/module/power-entry/sim/sims.yaml:49`: `i_swing` source tag → cite `led-row-current` (A4-10).
- `docs/decisions/0005-power-architecture.md` ≈446–449 "typical only" (A4-3) and :96 the 11.4 V with the Schottky (A4-12); `docs/decisions/0004-cv-interface-module.md` ≈299–301 per-rail figures (A4-12).
- `hardware/module/umbilical-load-switch/umbilical-load-switch.md:24` (A4-5).
- `docs/reference/pcb-pipeline.md` ≈265–274 (A4-11).
- `hardware/module/digital-and-supervision/bom.csv` `R-RX-MOD` and `digital-and-supervision.md` ≈104–106: 2.97 V → ~3.26 V at the cable node (A5-6); `digital-and-supervision.md:30` and the drawing label ≈63–64 (A5-9).
- `hardware/module/link-supervision/link-supervision.md`: "six `R-SPI-PULL`" (A5-9) and "a display to report on" (A5-10).

## Found on the way

- The DAC8568 frame is 32 bits; the A5-1 report's "31st falling edge" interrupt rule is right, and the sim shows a `CS_MOD` released on the last edge rises at the DAC ~100 ns *before* that edge arrives there.
- `hardware/bom.csv` was not regenerated in this fixer's first commit after the `spi-link` fragment edit; a later commit regenerated it, and `merge-bom --check` passes at the head.

## Gates at the head

`check-netlist --strict` 0 problems; `merge-bom --check` 0 problems;
`verify-datasheets` 270 verified, 0 problems; `sim.py check` PASS, 20 dirs;
`check-staleness` PASS; `kicad.py check` PASS (22 sheets, 6 boards, 129 renders).
