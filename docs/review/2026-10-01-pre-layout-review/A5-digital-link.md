# A5 - The digital link and key path: SPI over Cat5, MCU pin allocation, key chain timing, self-test, firmware contract

**Slice:** A5. SPI2 over the 2 m umbilical (`R-SPI-SER`, `U-TVS-SPI`, `U-RX-MOD` and its RC, `CS_MOD` pulls, `U-LVL-MOD`), the ESP32-S3-Matrix pin allocation at `J-MCU`, the SPI3 key chain (SN74HCS165 x4, ribbons, `R-CHAIN-SER`, `R-SER-TERM`), the chain self-test, and the firmware contract the hardware assumes.
**Revision measured:** 13197f8 (`git archive` copy; `tools/` pinned at the same revision)
**Tools:** `python3 tools/check-netlist.py --strict` (0 problems); `python3 tools/check-staleness.py` (FAIL only on 2 `cad` items, outside this slice); `python3 tools/kicad.py check` (PASS, KiCad 9.0.9); `python3 tools/sim.py run hardware/interfaces/spi-link/sim` (1170 runs, 26 assertions, 0 failed); `pdftotext -layout` on SN74AHCT14, SN74AHCT125, SN74HCS165, SP0504BAHT, DAC8568CIPW, ESP32-S3 datasheet v2.2, Waveshare Matrix schematic.

## Summary

- **Holds:** the transmission-line arithmetic for `spi-series-r`, the 74AHCT14 threshold figures, the four `CS_MOD` link states, the strapping-pin and reset-state claims for GPIO34, the SPI3 mode-2 argument for the 165 chain's MISO direction, the key-network crossing times, the bit allocation and marker levels, and the netlists. Every check tool passes, and the SPI-link sim reproduces.
- **Does not hold, timing:** the receiver RC delays falling edges much more than rising ones. That eats the DAC's `SYNC`-to-`SCLK` margins (t8, t4), and those depend on a CS hold time and SPI mode that no document fixes (A5-1). The key chain's hop hold race at the shared `CLK` edge is never analysed: every page argues only the setup side (A5-2). The self-test's `SER` input changes on the same edge that captures it (A5-4).
- **Does not hold, contract:** `firmware/README.md` is the firmware contract, and it omits most of what the hardware needs from firmware. It also still says "fire immediately on press" against ADR 0001's two-sample gate (A5-3). `latency-budget.md` owns `loop-budget` and `scan-period`, and it still argues from the two-MCU architecture that ADR 0015 superseded (A5-5).
- **Partial-fix shapes found:** the BOM rows and pages for the 2026-09-30/10-01 receiver change still describe the pre-receiver node (A5-6, A5-7). A settled figure is still called "disputed" in a CSV (A5-8). The "six `R-SPI-PULL`" count is stale in three places (A5-9). Two arguments outlive their premise (A5-10).

## Findings

### A5-1 - The DAC's SYNC/SCLK edge timing (t8, t4) through the new RC receiver depends on a CS hold time and SPI mode that are written nowhere, and the sim's skew figure understates the cross-edge skew
**Severity:** medium
**Node:** `CS_MOD`/`SYNC` against `SCLK`/`SCLK_DAC`. Refdes `R-RX-MOD`, `C-RX-MOD`, `U-RX-MOD`, U-DAC (DAC8568).

- The DAC8568 requires **t8 = 10 ns min from `SCLK` falling to `SYNC` rising**, **t4 = 80 ns min `SYNC` high time** and t5 = 13 ns `SYNC`-to-`SCLK`-falling setup `[ds DAC8568CIPW.pdf p.7, timing table rows t4, t5, t8]`. If `SYNC` rises before the 31st falling edge, the frame is discarded `[ds p.6]`.
- `[sim] hardware/interfaces/spi-link/sim/README.md` checks only rising edges (`s_delay_min`/`s_delay_max` both measure crossings of `V_T+` on a rising edge, `sims.yaml` `pair_post`): 28–39 ns to the lowest `V_T+` and 66–91 ns to the highest. From that it concludes "a skew of up to 63 ns … leaves more than 150 ns" against a 250 ns half-period. That covers DIN setup and hold. **It does not cover the CS edges.** Those are set by where the host puts CS relative to SCLK, not by the half-period.
- `[calc]` In the same RC (1 kΩ × (47 pF + 2–10 pF C_in) ≈ 49–57 ns), a **falling** edge from ~3.27 V reaches the lowest `V_T−` (0.5 V `[ds SN74AHCT14.pdf p.5]`) after τ·ln(3.27/0.5) = 1.88τ ≈ 92–107 ns. A **rising** edge reaches the lowest `V_T+` (0.9 V) after τ·ln(3.27/2.37) = 0.32τ ≈ 16–18 ns. Both add the same cable flight. A package whose thresholds sit at the low end of both bands (`V_T+` 0.9, `V_T−` 0.5, hysteresis 0.4 V, which is legal) therefore moves `SYNC`'s rising edge **~75–90 ns earlier** relative to the last `SCLK` falling edge than at the ESP32's pads. It shortens a CS-high pulse by up to the same amount: a rising edge crossing `V_T+` max 2.1 V is slow, ~0.9τ ≈ 45–55 ns, and a falling edge crossing `V_T−` max 1.7 V is fast, ~0.65τ ≈ 32–37 ns, so that pulse shrinks by ~10–20 ns at the other corner, and the low-threshold corner stretches it instead. The low-threshold corner is the one that matters for t8.
- So at the pad, CS must stay low **≥ ~100 ns after the last SCLK falling edge** (t8 10 ns + ~90 ns skew + two gates' 1–9 ns spread `[ds SN74AHCT14.pdf p.6]`). With SPI mode 1 (CPOL 0, CPHA 1), which is what the sim assumes (`sims.yaml` `opp`: "a mode-1 host launches it on the rising edge"), the last falling edge sits mid-bit. Whether the ESP32 then holds CS for the remaining half bit (250 ns) or releases it sooner depends on `cs_ena_posttrans` and the controller's CPHA implementation `[from memory]`. A `cs_ena_posttrans` ≥ 1 (one 500 ns bit) closes it with margin.
- **No document states the DAC's SPI mode, the CS pre/post-transaction setting, or a minimum CS-high time between the six frames.** A grep of the corpus for `CPOL|CPHA|mode 1|posttrans|cs_ena` finds only the SPI3 mode-2 line `[repo] spi-link.md:217,254`. The sim encodes mode 1 as a parameter, not as a requirement that reaches firmware.

**What would settle it:** add a falling-`SCLK`/rising-`CS` pair to `spi-link/sim` that measures the skew at `U-RX-MOD`'s output against t8, and write the DAC device config (mode 1, `cs_ena_posttrans` ≥ 1, `cs_ena_pretrans` ≥ 1) into the firmware contract. At E11, put a logic analyser on `SCLK_DAC`/`SYNC` at the DAC pins and confirm t8 > 10 ns at the last bit.

### A5-2 - The key chain's hop hold race (QH changing on the same CLK↑ the next register samples SER on) is never analysed; every page argues only the setup side
**Severity:** medium (uncertain; see settle line)
**Node:** `HOP_LT_RH`, `HOP_RH_RT`, `HOP_LH_LT` (key-chain netlist); `SCK`; `R-CHAIN-SER-SCK`; `U-TVS-CHAIN`; `U-KEYS` ×4.

- The pages say: "`QH` → next `SER` is data, sampled at the *next* rising `CLK`, one period later (1 µs …); `SER` setup is at most 14 ns and hold 0 ns" `[repo] hardware/cluster/key-register/key-register.md` §1, `key-chain-loom.md` *The protection parts*, ADR 0001 amendment 2026-09-27. That is the **setup** argument. The register also samples `SER` on the **same** `CLK↑` that makes the upstream `QH` change `[ds SN74HCS165-ti-scls828a.pdf p.13 §8.1 "On the rising edge of the clock … data from the serial input will be loaded"]`. Hold at that edge needs the upstream `tpd(CLK→QH)` **minimum** plus the hop's flight to exceed the downstream register's `CLK` arrival minus the upstream's.
- TI publishes `tpd` as a **maximum only** (16/18 ns at 4.5 V, 32/45 ns at 2 V `[ds p.7]`) and `SER` hold as 0 ns `[ds p.7]`. The minimum `tpd` is unpublished.
- `[calc]` `SCK` is deliberately slowed. `R-CHAIN-SER` 100 Ω plus pad 17–35 Ω drives `U-TVS-CHAIN` (30 pF typ at 2.5 V, more at 0 V `[ds SP0504BAHT.pdf p.2]`), the main board's load (`c_main` 20 pF assumed, `key-chain-loom/sim/sims.yaml`) and two ribbons: τ ≈ 135 Ω × ~85 pF ≈ 11 ns. The registers' `V_T+` spread at 3.3 V is 0.7–2.475 V on the page's own extrapolated bound `[repo] key-switch-network.md` §2. A register with `V_T+` at 0.7 V crosses at 0.24τ ≈ 3 ns and one at 2.475 V at 1.39τ ≈ 15 ns. **Up to ~12 ns of threshold-induced clock skew between two registers on one net**, before ribbon flight (~1–2 ns). That is the same order as a plausible HC-family minimum `tpd` at 3.3 V `[from memory]`. A hold violation duplicates a bit and shifts the rest of the frame by one, which the marker would usually catch as a framing error rather than a wrong note.
- `key-chain-loom/sim` checks `SCK` for double clocking (`sck-to-key-board`) and `QH` for false edges (`qh-to-main-board`), but **no sim or page compares `SCK` arrival skew against `QH`'s earliest change** `[repo] hardware/interfaces/key-chain-loom/sim/README.md` table.

**What would settle it:** a two-register deck in `key-chain-loom/sim` with the upstream `QH` launched at a stated minimum `tpd`, opposite threshold corners on the two registers' `CLK`, and the hold margin measured. Failing that, at E14 scope `SCK` at `right_hand`'s pin 2 against `left_thumb`'s `QH` at `right_hand`'s pin 10. If it is tight, the classic fix is to clock the chain from the data end (reverse the clock routing) or to keep the RC off the far registers.

### A5-3 - The firmware contract (`firmware/README.md`) omits nearly every requirement the hardware places on firmware, and contradicts ADR 0001 on the press path
**Severity:** medium
**Node:** firmware ↔ `U-KEYS` chain (`IO38`/`IO7`/`IO33`/`IO40`), SPI2 (`IO34`–`IO37`, `IO39`), `IO2`/`IO3`.

- `[repo] firmware/README.md:23-24`: "**Asymmetric key debounce** — fire immediately on press, filter only the release." ADR 0001 requires "**two consecutive agreeing samples before a note-on**" `[repo] docs/decisions/0001-mcu-and-board-partitioning.md:368`. `latency-budget.md:99` was corrected for exactly this ("This row read 'Debounce (press) — 0, fire immediately', which contradicted the ADR"), and the fix did not reach the firmware page. This is shape 1: a fix that did not reach the pages citing it.
- Requirements stated only on hardware pages, several with "written nowhere else" against them:
  - SPI3 **mode 2** for the 165 chain, which the page itself calls "A firmware line, written nowhere else" `[repo] spi-link.md:217`.
  - The MCP3202 at **0.9 MHz per device** on a shared SPI2, while the DAC runs at 2 MHz. The page says "**It is written nowhere.**" `[repo] spi-link.md:240-241`.
  - **Polling transactions on an acquired bus** as the condition for 4 kHz to close at all `[repo] latency-budget.md:185-189`, `config/figures.yaml` `loop-budget`.
  - The **marker check**: hold the previous frame and count errors, and do not count on the marker to catch a mid-shift reload `[repo] key-marker-and-bits.md` §4.
  - How `SH/LD` (`IO7`) is driven. It must be high for the whole transfer and pulsed low between transfers. If firmware drives it as an ordinary active-low SPI CS, the chain loads continuously and every read returns 32 copies of `RT1`. Positive-polarity CS or a GPIO pulse ahead of the transaction works, with `SH/LD high before CLK↑` ≥ 21 ns `[ds SN74HCS165 p.7]`. Not stated anywhere `[repo]` (grep of `SH/LD` across the corpus).
  - `IO33` must stay static outside the self-test, because it is used as a shield ("`IO33` moves only for the chain self-test" `[repo] carrier.md:418`). A full-duplex SPI3 transaction would drive MOSI.
  - The DAC SPI mode and CS timing (A5-1).
  - Only `IO2`/`IO3` driven low and the 4 kHz / six-word refresh do appear `[repo] firmware/README.md:20,40,117`.
- Firmware has no code yet `[repo] firmware/README.md:11`, so nothing is wrong in a build. But this is the document F-track will be written from, and the review rules treat restating as the defect. Here the facts are not even restated, they are absent.

**What would settle it:** a "What the hardware requires" list in `firmware/README.md` that cites each owning page by name.

### A5-4 - The chain self-test's SER input changes on the same CLK↑ that captures it
**Severity:** low
**Node:** `IO33` → `R-CHAIN-SER-SER` → `left_hand` `SER` (key-chain netlist), `R-SER-TERM`.

- In SPI mode 2 (CPOL 1, CPHA 0) the host launches MOSI on the **trailing** edge, which is rising `[from memory: SPI mode definition]`. That is the edge on which `left_hand` loads `SER` `[ds SN74HCS165 p.13]`, with `SER` hold 0 ns `[ds p.7]`.
- `IO33` and `SCK` (`IO38`) each pass a 100 Ω `R-CHAIN-SER` into different loads, and both carry a channel of `U-TVS-CHAIN` `[repo] key-chain-loom.md` *The main-board end*. Whether `left_hand` captures the old bit or the new one depends on which RC edge arrives first. The page presents the self-test as "shift a known pattern in at `left_hand` and read it back" `[repo] key-chain-loom.md` *The chain-end serial input*, with no edge analysis.
- Consequence: the pattern may read back shifted by one bit, or unstably at a corner. That is a self-test false failure, not a play fault. Mode 2 is right for the MISO direction (`QH`), and no single SPI mode is clean for both directions of a rising-edge register.

**What would settle it:** have the self-test firmware tolerate a ±1-bit alignment, or drive `IO33` as a GPIO changed while `SCK` is high and stable. Check at E4.

### A5-5 - `latency-budget.md`, owner of `loop-budget` and `scan-period`, still argues from the two-MCU split that ADR 0015 superseded
**Severity:** medium
**Node:** figures `loop-budget`, `scan-period`; the output loop.

- `[repo] docs/reference/latency-budget.md:8-16`: "**The display and radio are on a separate MCU** (ADR 0013), so neither can preempt the loop… That isolation is physical." Rule 4, line 226: "**The WiFi stack and display are on a different MCU entirely** (ADR 0013)." Lines 154–155 book "WiFi transmit transients … (ADR 0013)" and an "Inter-MCU UART link" measurement.
- `[repo] docs/decisions/0015-one-mcu-no-display.md:5-7`: "Supersedes … the two-MCU split of ADR 0013", decided 2026-09-26. `firmware/README.md:3-9` agrees: one image, no display board, no radio.
- The isolation argument is gone, and the conclusion survives it. That is shape 4. What replaces it is a scheduling rule ("Lighting renders on the other core, through RMT", `firmware/README.md:21`), and the budget does not book it. The 8×8 matrix and the LED row now share the MCU with the 4 kHz loop, which is exactly the "blocking display refresh" the page's opening paragraph warns about.

**What would settle it:** rewrite the header and rules 3–4 against ADR 0015 (one MCU, radio off, lighting on the other core via RMT), and drop or retarget the inter-MCU UART and WiFi characterisation rows.

### A5-6 - `R-RX-MOD`'s "settled high 2.97 V" puts the 10 kΩ pull-down behind the 1 kΩ; the netlist has it at the cable node
**Severity:** low (conservative error; the conclusion holds)
**Node:** `R-RX-MOD` row; `SCLK`/`MOSI` cable node; `R-PULL-SCLK`, `R-PULL-MOSI`.

- `[repo] hardware/module/digital-and-supervision/bom.csv` `R-RX-MOD`: "Against a 10k pull-down the settled high at the input is 3.3 x 10k / (10k + 1.1k) = 2.97V". The page repeats it `[repo] digital-and-supervision.md:104-106`.
- `[repo] hardware/module/digital-and-supervision/netlist.yaml` `SCLK: [port SCLK, R-PULL-SCLK.1, R-RX-SCLK.1]` and `MOSI: [port MOSI, R-PULL-MOSI.1, R-RX-MOSI.1]`, so the pulls sit at the cable node, ahead of the 1 k. The sim README says the same ("the pulls stay at the cable node").
- `[calc]` The divider is 10 kΩ against `R-SPI-SER` 82 Ω + pad 17–35 Ω + cable DCR ~0.2 Ω: 3.3 × 10 000 / 10 117 ≈ 3.26 V at the node. The Schmitt input draws ≤ 1 µA `[ds SN74AHCT14.pdf p.5]`, so the 1 k drops ≤ 1 mV. The settled high is **~3.26 V, not 2.97 V**. The 1.1 k in the formula is the 1 k plus a ~100 Ω source in the wrong place. Same shape as "a fix whose own explanation restates the wrong value": the receiver was added and the explanation computes a topology that was not built.

### A5-7 - `R-CS-PULL-MOD`'s row still describes the node before the receiver: "the rail of the part it holds, U-LVL-MOD", against the 74AHCT125's 0.8 V `V_IL`
**Severity:** low
**Node:** `CS_MOD` cable node; `R-CS-PULL-MOD` (`R-PULL-CS`); `U-RX-MOD` gate 5.

- `[repo] hardware/interfaces/spi-link/bom.csv` `R-CS-PULL-MOD`: "from CS_MOD to LOGIC_5V - the rail of the part it holds, U-LVL-MOD … the node at ~0.45V, below the buffer's 0.8V V_IL [ds SN74AHCT125.pdf p.3] … holds the buffer input within 0.1V of 5V".
- `[repo] netlist.yaml` (`digital-and-supervision`): `CS_MOD` → `R-RX-CS` → `CS_RC` → `U-RX-MOD.5A`. The pull holds **`U-RX-MOD`'s** input, and `U-LVL-MOD` is on `DAC_AVDD`. `spi-link.md:53` already says so ("the rail of the part that pull holds. Not the 74AHCT125's"). The fix reached the page and not the row.
- The threshold matters. Against `U-RX-MOD`'s `V_T−` minimum of **0.5 V** `[ds SN74AHCT14.pdf p.5]`, the "instrument off" node at 0.45 V `[calc] 5 × 10k/110k` has **50 mV** of margin, not 350 mV. A dead 3V3 rail sitting at ≥ 0.06 V instead of 0 V, `LOGIC_5V` high, or 1 % resistors at their extremes put it inside the band. `spi-link.md:328` notes the spread "reads every row the same way". On this row it does not read guaranteed. Either reading is harmless, because `SCLK` is held low and a later `SYNC` rise interrupts the frame (`spi-link.md:340-344`), so this is accuracy, not function.

### A5-8 - The `J-UMB` BOM row calls the module ground topology "still disputed"; `dig-gnd-topology` is settled
**Severity:** low
**Node:** `J-UMB` row; figure `dig-gnd-topology`.

- `[repo] hardware/interfaces/spi-link/bom.csv` `J-UMB` notes, regenerated into `hardware/bom.csv:64`: "The module end is dig-gnd-topology, still disputed."
- `[repo] config/figures.yaml` `dig-gnd-topology`: `status: settled`, owner's decision 2026-09-30. The register's own `false_positive_note` says "spi-link.md (interfaces) still calls this figure disputed … report, do not add a pattern that only fires there". The page no longer does (`spi-link.md:46,124`), but this CSV row does. Under CLAUDE.md rule 2b a CSV carries no history, so this is a live stale statement.

### A5-9 - "Six `R-SPI-PULL`" is a count that moved: the row is qty 5 since `CS_MOD`'s pull became its own row
**Severity:** low
**Node:** `R-SPI-PULL` (qty 5), `R-CS-PULL-MOD`.

- `[repo] hardware/interfaces/spi-link/bom.csv` `R-SPI-PULL`: qty **5**, "FIVE OF THE MODULE'S SIX SPI PULLS - the sixth … is its own row, R-CS-PULL-MOD".
- Still saying six `R-SPI-PULL`: `spi-link.md:51` ("The DAC-side three of the six `R-SPI-PULL`"), `digital-and-supervision.md:30` (same words), and `link-supervision.md` ("what the six `R-SPI-PULL` resistors are for"). The drawing at `digital-and-supervision.md:63-64` labels the cable-side group "[R-SPI-PULL x3] SCLK↓ MOSI↓ CS↑(100k)", but there are two `R-SPI-PULL` there plus `R-PULL-CS` of row `R-CS-PULL-MOD`. `check-netlist.py` passes because that label is not in `[REFDES value]` form. This is the stated-count shape.

### A5-10 - Two arguments that outlive their premise: the DAC-side pulls justified by an `OE` that can no longer be disabled, and "a display to report on"
**Severity:** advisory
**Node:** `R-PULL-SCLK-DAC`, `R-PULL-DIN`, `R-PULL-SYNC`; `OE_MOD`.

- `[repo] spi-link.md:291-296` and the `R-SPI-PULL` row: the DAC-side pulls exist because "with `OE` disabled the buffer's outputs are Hi-Z". `OE` is tied to `DIG_GND`, permanently enabled (`netlist.yaml`: `U-LVL-MOD.1OE…4OE` on `DIG_GND`). Since 2026-10-01 the buffer's `VCC` is the DAC's own rail, so the pulled-to rail and the driven rail are the same one. The pulls are harmless but no longer argued correctly. The remaining case is a buffer with `VCC` absent, where the pull rail is absent too.
- `[repo] hardware/module/link-supervision/link-supervision.md`: "The knowing moved to the instrument, which … has a display to report on." There is no display (ADR 0015). The same stale premise appears in ADR 0001:399-401 ("a number on the display"), which is a historical ADR, `[repo] docs/decisions/0001…:399`.

### A5-11 - "SPI2 cannot use IO_MUX" is `[from memory]`, and the banked datasheet refutes it: GPIO34–37 are FSPI IO_MUX pins, and the design has SCLK and MOSI swapped against them
**Severity:** advisory
**Node:** `IO35` (`SCLK`), `IO36` (`MOSI`), `IO34` (`CS_MOD`), `IO37` (`MISO`).

- `[repo] spi-link.md:257-262`: "The S3's FSPI IO_MUX pins are GPIO9–14 `[from memory]` … SPI2 on GPIO35/36/37 therefore routes through the GPIO matrix."
- `[ds ESP32-S3-datasheet-v2.2.pdf, Table 2-4 IO MUX Functions, p.21-22]`: function F2 on GPIO33 = FSPIHD, **GPIO34 = FSPICS0, GPIO35 = FSPID (MOSI), GPIO36 = FSPICLK, GPIO37 = FSPIQ (MISO)**, GPIO38 = FSPIWP. The second set is GPIO9–14.
- The design matches on CS (34) and MISO (37) and has **SCLK on 35 and MOSI on 36, the reverse of the IO_MUX assignment** `[repo] hardware/carrier/netlist.yaml` (`IO35`→`R-SPI-SER-SCLK`, `IO36`→`R-SPI-SER-MOSI`). At 2 MHz it makes no difference, as the page says. Whether ESP-IDF would use the second IO_MUX set at all is `[from memory]` doubtful. Rule 3 says a banked document beats memory, so the sentence should be corrected rather than relied on. Swapping the two now would change the `J-MCU` ribbon order, which was chosen for shielding (`carrier.md:410-414`), so do not swap without a reason.

### A5-12 - The "40 mA pad limit" the series-R choice is argued against is a typical drive figure, not a limit
**Severity:** advisory
**Node:** `R-SPI-SER` (`spi-series-r` derivation).

- `[repo] config/figures.yaml` `spi-series-r`: "33 mA at the pad's strongest drive, under its 40 mA". `spi-link.md:192,197`: "48 mA fault current against a 40 mA pad spec", "3.3 V / 82 Ω alone is 40 mA, at the pad's limit".
- `[ds ESP32-S3-datasheet-v2.2.pdf p.65, Table 5-4]`: `IOH` **typ** 40 mA at `VOH` ≥ 2.64 V with `PAD_DRIVER` = 3, which is a characteristic and not a maximum. Table 5-1, the absolute maximum ratings, gives only "Cumulative IO output current 1500 mA". Its footnote says the part "proved to be fully functional after all its IO pins were pulled high while being connected to ground for 24 consecutive hours". The 68 Ω row's rejection rests on this. 82 Ω is justified independently by `cs-fall-reentry`, so no value changes.

### A5-13 - `loop-budget` does not reproduce from its own derivation, and the ADC and DAC terms disagree across pages
**Severity:** low
**Node:** figure `loop-budget`; the SPI2 transactions.

- `[repo] config/figures.yaml` `loop-budget`: "196-241 us … Bus time 148-155 us PLUS ESP-IDF per-transaction overhead (24 us interrupt / 9 us polling) … 291 us with driver defaults."
- `[calc]` The 291 µs reproduces as 7 SPI2 transactions (6 DAC + 1 ADC) × 24 µs + 96 + 26.7 = 290.7 µs, with the key chain concurrent on SPI3. The polling case on the same basis is 7 × 9 + 122.7 = **185.7 µs**. Serialising the chain (+32 µs and +9 µs) gives 226.7 µs. Neither end is 196 or 241, and the derivation does not say what bounds the range.
- The ADC term is "24 clocks @ 0.9 MHz = 26.7 µs" `[repo] spi-link.md:248` and "~24 µs, 18 clocks" `[repo] latency-budget.md:60`, two different transaction lengths. The key path books "DAC update + settle ~60 µs" `[repo] latency-budget.md:102`, while the breath path books ~96 µs + ~10 µs for the same six-word burst `[repo] latency-budget.md:62-63`.

**What would settle it:** the owner page (`latency-budget.md`) stating the transaction count and the polling-vs-interrupt split that produces 196 and 241.

### A5-14 - ADR 0001's Consequences still count 18 switches and 14 spare bits
**Severity:** advisory
**Node:** `U-KEYS` chain; `config/key-layout.yaml` `counts`.

- `[repo] docs/decisions/0001-mcu-and-board-partitioning.md:473-475`: "Chain is 4 registers, 32 bits, for 18 switches … The 14 spare bits … 8 of them carry the marker pattern and 3 stay free". An amendment note says the counts "each moved by one". `[repo] config/key-layout.yaml` `counts.total: 19`, and the chain comment gives "19 used, 13 spare". 18 + 14 = 32 and 19 + 13 = 32, but "14 spare … 8 marker … 3 free" leaves 3 unexplained, where the current split is 2 spare-switch + 8 marker + 3 free = 13. The amendment note covers it, so this is advisory.

## Checked and holds

- **`spi-series-r` arithmetic** `[calc]`: the far end's first rising step is 3.3 × 2 × 100/(R_s + 100) = 3.04 V at R_s = 117 Ω and 3.32 V at 99 Ω. The falling step is 0.00–0.26 V. 3.3/(82 + 17) = 33 mA, 3.3/(82 + 35) = 28 mA, and 0.033² × 82 = 89 mW. The historical 220 Ω and 100 Ω table rows reproduce with a 35–40 Ω pad.
- **74AHCT14 thresholds** `[ds SN74AHCT14.pdf p.5]`: `V_T+` 0.9–2.1 V, `V_T−` 0.5–1.7 V, hysteresis ≥ 0.4 V over 4.5–5.5 V, `I_I` ±1 µA at `VCC` 0–5.5 V, `tpd` 1–8/9 ns. All as stated on the page, the BOM row and the sim.
- **SP0504BAHT** 30 pF typical at 2.5 V, 1 MHz `[ds SP0504BAHT.pdf p.2]`. The netlist has `U-TVS-SPI` on the pad side, nets `IO34`/`IO35`/`IO36`, and common to `PWR_GND` `[repo] carrier/netlist.yaml`.
- **The spi-link sim reproduces**: 1170 runs, 26 assertions, 0 failed `[sim] hardware/interfaces/spi-link/sim`.
- **`CS_MOD` link states** `[calc]`: 5 × 10k/110k = 0.455 V, (3.3/10k + 5/100k)/(1/10k + 1/100k) = 3.4545 V, 45 µA, ≤ 17 µA. All arithmetic right (but see A5-7 on the threshold).
- **GPIO34** is input-enabled only at reset, with no pull, and so are GPIO33–37 `[ds ESP32-S3 p.17 pin table]`. The strapping pins are GPIO0, 3, 45 and 46 `[ds p.26, as cited]`. The Matrix's SoC is **ESP32-S3FH4R2**, with quad flash and PSRAM `[repo] datasheets/mechanical/WAVESHARE-ESP32-S3-MATRIX-SCHEMATIC.pdf`, so GPIO33–37 are not taken by an octal PSRAM. `IO7` and `IO38` have no IE and no pull at reset `[ds p.16-17]`, so `SH/LD` and `SCK` float while the Matrix resets. That is harmless into Schmitt inputs.
- **The `J-MCU` pin map** in `carrier.md:403-406` matches `carrier/netlist.yaml` pin for pin (IO35/10, IO36/12, IO34/14, IO37/18, IO39/16, IO38/8, IO7/6, IO33/19, IO40/20). `R-CS-PULL-INST` is on `IO34` to `DEV_3V3` at `J-MCU.13` `[repo]`. `tools/kicad.py check` PASS holds the boards to the sheets.
- **SPI3 mode 2 for MISO** `[ds SN74HCS165 p.13, p.7]`: `QH` shows `H` from load and shifts on `CLK↑`, so a mode-2 sample on each falling edge lands half a period after the shift. Mode 1 loses bit 0, and modes 0 and 3 rely on the unpublished minimum `tpd`. Correct.
- **Key-network timings** `[calc]`: release 103.4 µs × ln(3.1565/0.825) = 138.8 µs. Press 4.496 µs × ln(3.1565/0.3515) = 9.87 µs. 1.43 mA per key and 27.3 mA at 19 keys.
- **Allocation**: `allocation.yaml` matches the page table and the marker levels (RT B=1/A=0, RH B=0/A=1, LT D=0/C=1, LH C=0/B=1). Counts are 19 switches + 2 spare-switch + 8 marker + 3 free = 32, consistent with `key-layout.yaml` `counts` `[repo]`.
- **The self-test override** `[calc]`: `IO33` through 100 Ω against `R-SER-TERM` 10 kΩ sits 3.3 × 100/10 100 = 33 mV from the rail. The timing caveat is A5-4.
- **SCK/QH ringing**: the `key-chain-loom/sim` checks for double clocks and false edges exist and cover what they claim (`sck-to-key-board`, `qh-to-main-board`). Not re-run here.
- **The MCP3202 clock**: 1.8 MHz at 5 V and 0.9 MHz at 2.7 V, as cited `[repo] spi-link.md:219-241`. Not re-read from the PDF in this slice.
