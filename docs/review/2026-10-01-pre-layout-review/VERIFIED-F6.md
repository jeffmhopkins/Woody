# VERIFIED — fixer F6 (owner decisions and leftovers)

**Base:** `claude/car-instrument-cad-design-xvqwv2` at `ec20ecf`, merged into
this branch. **Scope:** the owner's decisions of 2026-10-01 on A4-1, A5-2,
A8-3, A8-8, A3-2 and A4-4, and the leftovers handed by F1, F2 and F3. Not
touched: F4's domain (`config/body.yaml`, `key-layout.yaml`, `module.yaml`,
`mechanical/**`, `hardware/lib/**`, `hardware/boards/*/README.md`, key
boards) and every main-board `.kicad_pcb`. Each id was checked against the
corpus at the base before acting. `tools/` changed in one line
(`kicad.py` `CHAIN_MAIN_ROWS`, below).

## Owner decisions

| Id | Decision | What landed | Evidence |
|---|---|---|---|
| A4-1 | Add a ~1 mH common-mode choke at `U-ISO`'s input; decide `C-ISO-Y` with it | **`L-CM-ISO`, Bourns PM3700-40-RC** (1.0 mH min at 1 kHz, 4 A, 0.020 Ω, 3.9 µH leakage, 20 dB 500 kHz–40 MHz, SMD, LCSC C2662215, JLC 99 in stock) between `L-ISO-IN`/`FB4` and the converter's pins, one winding per leg (new nets `ISO_FILT_POS`, `ISO_FILT_NEG`). **`C-ISO-Y` 22 nF C0G** (Murata GRM21B5C1H223JA01L, C77069), not F3's 10 nF. Sheet, export, render, module-main board export and render (`L2`), BOM rows, `U-ISO` and `L-ISO-IN` rows, `power-entry.md` (*The input filter*, *The common mode*, drawing, *Still open*), ADR 0027 (point 4, residual row, *Consequences*, amendment *the choke is fitted*), ROADMAP E6. Datasheet banked, `.manifest-R43-F6.csv` | `[ds BOURNS-PM3700-CM-CHOKE.pdf p.1]`. `[sim] module/power-entry/sim` **`cm-loop`** (asserted, 17 corners: core loss 500 Ω–3.6 kΩ a winding, L ±30 %, ribbon 0.1–1 µH, `C-ISO-Y` ±5 %): star share **0.6–5.4 %** at 550 kHz, ≤ 1.7 % at 1.65 MHz, ≤ 0.19 % at 5.5 MHz, peak 5.9 % over 500 kHz–30 MHz, bound 10 %. **`cm-loop-y-1n`** (what-if, the choke with 1 nF): 15–78 % — F3's deck modelled a lossless choke, and with core loss 10 nF leaves ~11 % `[sim, scratch sweep]`, hence 22 nF. **`iso-input-z`**: the filter's impedance ≤ 1.8 Ω from 100 Hz to 2 MHz, margin ≥ 58× against −104 Ω; 0.06 % of the 550 kHz input current reaches the rack. No hot-plug or input sim held `U-ISO`'s input before (`grep ISO_VIN` over every deck): the two decks are new |
| A5-2 | Add 2.2 kΩ at `left_thumb`'s `QH` on the main board | **`R-HOP-SER`** 2k2 1 % 0603 (UNI-ROYAL 0603WAF2201T5E, C4190, JLC basic), on the interface sheet (`HOP_LT_QH` → `HOP_LT_RH`) and on the main board's root sheet as **`R44`**; both exported and rendered; BOM row in `key-chain-loom/bom.csv`; `key-chain-loom.md` (*The hop hold time*, tables, drawing), `key-register.md`, ADR 0001 amendment, `nets.yaml` `CHAIN_QH_LT`. `tools/kicad.py` `CHAIN_MAIN_ROWS` gains `R-HOP-SER` so `check_chain_main_parts` holds the main-board part to the sheet | `[sim] interfaces/key-chain-loom/sim` **`hop-hold-lt-to-rh`** now asserts `hold_margin > 0` with **zero** `CLK`→`QH` delay at every corner: **+3.2 to +13.4 ns** rising, **+11.7 to +22.3 ns** falling; data at `SER` within 28 ns (asserted < 100 ns). **`hop-hold-without-series-r`** (what-if, asserted to fail): −0.7 to −10.9 ns, `need_tpd` up to 10.9 ns |
| A8-3 | `FB-IN` stays; JLC sources it | `FB-IN` row: ordered as MI1206K601R-10 through JLC Global Sourcing / consignment, `machine`, second source only if that fails; the `FB1`–`FB4` symbols' `Note` says so (`Assembly` stays `machine`); `docs/reference/tooling.md` §4 *Ordering* gains the exception. No figure moved | `[repo]` sheet fields, row |
| A8-8 | A trimmer instead of bench-selecting `R-REG-SET-LO` | **`TRIM-DAC-RAIL`**, Bourns 3224W-1-500E (50 Ω, 12-turn, sealed, top adjust, ±10 %, LCSC C56340, JLC 317) as a rheostat in the LM317L's `OUT`→`ADJ` leg after `R-REG-SET-HI` 150 Ω; **wiper strapped to pin 1 (CCW)**, pin 3 to `R-REG-SET-HI`, so clockwise raises the rail; **`R-REG-SET-LO` 523 Ω 0.1 %** (RESI PTFR0805B523RN9, C47116002). Open wiper → whole track in → rail low; open track → leg open → ~1.3 V. **`dac-rail` moved 5.21 V → 5.20 V** ("trim to 5.20 V"), per CLAUDE.md rule 2: the corpus grepped for the old value first, `"5.21 V"`, `"5.21V"`, `"475R 0.1%"` and `"0.66V worst-case spread"` added to `forbidden`; every live hit moved (ADRs 0003, 0004, 0005, 0006; `dac8568.md`, `breath-receive-stage.md` and its row, `pitch-stage.md`, `breath-output-stage.md` and its sim, `spi-link`, `dac8568` and `module` fragments, ROADMAP E6/E7). ROADMAP E7 rewritten: trim to `dac-rail`, pass 5.00–5.50 V. Datasheet banked | `[sim] module/power-entry/sim` **`dac-trim-*`** (behavioural LM317L across `V_REF` 1.20–1.30 V, `I_ADJ` 0–100 µA, the 0.1 % divider, the trimmer ±10 %; 33 corners each): fully CW **5.32–5.83 V**, fully CCW **4.26–4.85 V**, as shipped 4.73–5.30 V, open wiper = CCW, open track 1.20–1.35 V; trimmed (`dac-trim-e7`) 5.20 V inside 5.0–5.5 V. `trim-ends-poweron` (TI's transient model, both ends): never 6 V on the way up, pitch jack within 100 mV. **The window asked for cannot be met as stated — see below** |
| A3-2 | Accepted, no parts | `power-entry.md` *What the diodes protect against*: "Accepted by the owner, 2026-10-01" with the alternative and the guard (red stripe at both ends) | `[repo]` |
| A4-4 | Accepted, no parts | `power-entry-instrument.md` *The 13.5 V rating on this rail* and an ADR 0027 amendment record the acceptance with the date | `[repo]` |

### A8-8: the trimmer's whole travel cannot stay inside 5.00–5.50 V

The brief asked for a travel that stays inside the DAC8568's 5.0–5.5 V at
both ends and every corner, and that reaches 5.20 V. With the LM317L's
guaranteed reference, 1.20–1.30 V `[ds LM317LZ.pdf p.5]`, both cannot hold
`[calc]`: a travel that reaches the set point on a 1.20 V part and on a 1.30 V
part spans at least 1.30/1.20 = 8.3 %, and the window is 10 %, so the ratio
range left for the ends is under 1.6 % — a trimmer of under 1 Ω with the
150/475 divider. **Chosen instead:** reach the set point on every part with
50 mV to spare, and keep every setting under the DAC's **6 V absolute
maximum** (worst 5.83 V); the 5.0–5.5 V window is E7's to hit by meter, and
the fail-safe direction is down. Recorded on `power-entry.md` (*The DAC
rail's trim*), in `dac-rail`'s derivation and in the sim's assertion text.
**OWNER, if this is not acceptable:** a reference with a tighter
guaranteed `V_REF` (or an LDO with a ±1 % reference) would allow a narrower
travel; nothing was changed in that direction.

## Leftovers

| Id | Verdict | Action |
|---|---|---|
| A3-1 | CONFIRMED (ADR 0027 point 2 still said "every start and every fault") | Point 2 excepts a replug inside `Q-INRUSH`'s window, dated; `power-entry.md` and `U-ISO`'s row already carried it |
| A3-6 | CONFIRMED (ADR 0027 *Consequences* "adds ~45 mA and ~40 mA") | Cites `module-own-draw`; `"load adds ~45 mA and ~40 mA"` added to its `forbidden` (no other live hit; ADR 0004:315 narrates the old pair next to its correction) |
| A8-1 | CONFIRMED (`check-netlist` 6/8) | `C-DECOUPLE-CARRIER` qty 8 → 6, enumerated by refdes (ADC, REF VIN, REF VOUT, `C-DEC-BUF`, LED, SENSOR); "both R-78E5 inputs" and the 2026-09-21 history cut. `check-netlist` now: 161 rows exact, one short (`U-BREATH` 1/2, not this fixer's) |
| (F1 handed) | CONFIRMED | `carrier.md` §1 note: "the two R-78E5.0 bucks" → one, since ADR 0015 |
| A1-13 | CONFIRMED | `latency-budget.md`: receive filter 459 Hz / 347 µs (was 482 Hz / 330 µs), total ~2.86 ms, the two poles 679 µs. `loop-budget` does not use the 330 µs (its derivation is SPI transactions only), so no figure moved |
| (F1 handed) | CONFIRMED | `tooling.md` §5: the breath output stage's row adds the chain sims |
| A1-7 | CONFIRMED | ROADMAP *Cold-start warm-up sweep* (E2): log the breath jack at rest over the 20 minutes; pass inside ±0.53 V, the sensor's own datasheet bound through the commissioned gain (`breath-receive-stage.md`). `breath-output-stage.md` carries no bound of its own; the receive page's is the one banked |
| A8-18 | CONFIRMED (six fragments LF-only) | Converted to CRLF in one commit, content asserted unchanged row by row; `merge-bom --check` passes and `hardware/bom.csv` regenerates identical |

## HANDED

- **To F4 / the module CAD (orchestrator):** `L-CM-ISO`'s envelope on
  module-main, **21.6 mm over the terminals (body Ø 17.78 mm), 11.43 mm tall
  max, SMD**, between `L-ISO-IN` and `U-ISO`'s input pins on the rear face;
  and its footprint, **`woody:L_CommonModeChoke_Bourns_PM3700`**, which does
  not exist yet in `hardware/lib`: four 3.18 mm square pads on a cross,
  21.59 mm pad-to-pad both ways, pin 1 at the polarity mark (datasheet p.1,
  *Recommended Pad Layout*). KiCad's board ERC warns `footprint_link_issues`
  until it does. `TRIM-DAC-RAIL` uses the stock
  `Potentiometer_SMD:Potentiometer_Bourns_3224W_Vertical` (4.8 × 3.5 mm,
  top adjust: it must be reachable with a screwdriver at E7).
- **To the main-board routing agent:** one new part, **`R44`** (`R-HOP-SER`,
  2k2 0603) between `U7` (`left_thumb`) `QH` (net `/HOP_LT_QH`) and `J5`
  pin 6 (`/HOP_LT_RH`); place it at `U7`'s `QH`, not at the connector.
- **To F4 (README in its domain):** `hardware/boards/main-board/README.md`
  and `module-main/README.md` may list parts; they now carry `R44` and
  `L2`/`RV4` respectively.

## Gates at the head

`check-netlist --strict` 0 problems (161 rows exact, `U-BREATH` 1/2 short, not
this fixer's); `merge-bom --check` 0 problems (217 rows); `verify-datasheets`
276 verified, 0 problems; `sim.py check` PASS, 20 dirs (re-run here:
`pitch-stage`, `power-entry`, `breath-output-stage`, `digital-and-supervision`,
`panel-led`, `umbilical-load-switch`, `power-entry-instrument`,
`key-chain-loom`, all 0 failed); `check-staleness` PASS; `kicad.py check`
PASS (22 sheets, 6 boards, 129 renders).
