# VERIFIED — fixer F8 (the DAC rail: a precision-set LDO, no trimmer)

**Base:** `claude/car-instrument-cad-design-xvqwv2` at `d9b932f` (F6 merged),
then F7's head `e0cd402` merged in before the end. **Scope:** finding A8-8
only, on the owner's decision below. Not touched: `config/module.yaml`,
`mechanical/**`, `hardware/lib/**` (F4), every main-board `.kicad_pcb`, the
breath response shaper (F7). `tools/` unchanged. New part footprint is KiCad's
stock `Package_SO:MSOP-10-1EP_3x3mm_P0.5mm_EP1.68x1.88mm`, so nothing is handed
to F4.

## A8-8 — superseded again, 2026-10-01

**The owner, 2026-10-01:** replace the LM317L and the trimmer with a
precision-set LDO that needs no adjustment (LT3042 or similar, a ±1 % `SET`
current, one 0.1 % resistor), so `DAC_AVDD` lands inside the window on every
part with no trimming and no way to misadjust it. **This supersedes F6's
A8-8 row** (`VERIFIED-F6.md`: `TRIM-DAC-RAIL`, `R-REG-SET-HI` 150 Ω,
`R-REG-SET-LO` 523 Ω, `dac-rail` 5.20 V) and F6's *OWNER, if this is not
acceptable* note, which proposed exactly this.

**Why the window, kept as the requirement** `[repo, ds]`: the DAC8568 C grade's
0–5 V range at the internal reference × 2 is specified only for `AVDD` ≥ 5 V —
*"AVDD ≥ 5V; grades C and D: maximum output voltage 5V when using internal
reference"* and the reference-input row *"Grades C/D, AVDD = 5.0V to 5.5V"*
`[datasheets/analog/DAC8568CIPW.pdf p.3, p.4]`; under it the buffer cannot
reach full scale and the top calibration point lands in its compression (ADR
0004). 5.5 V is the operating maximum, 6 V absolute `[p.2]`. Now written into
`dac-rail`'s `floor` with the quotation.

| What | Landed | Evidence |
|---|---|---|
| Part | **`U-REG-DAC` = ADI LT3042EMSE#TRPBF**, MSOP-10 with exposed pad, machine (LCSC C461518; JLC 3,447 in stock, extended). Refdes kept so the pages citing it follow. EN/UV and PGFB tied to IN (fast start-up off: its 2 mA SET current cannot be left on), PG open, ILIM to GND, OUTS to OUT at `C-REG-OUT`, exposed pad on `AGND_MOD` | `[ds ADI-LT3042.pdf p.2, p.12, p.18]`; `[web jlcpcb.com parts API 2026-10-01]` |
| Set resistor | **`R-SET-DAC` 52.3 kΩ ±0.1 % ±25 ppm/°C**, Viking ARG05BTC5232 (C2758300, JLC 31,645) | `[ds VIKING-ARG-THIN-FILM-RESISTOR.pdf p.2–3]` |
| SET capacitor | **`C-SET-DAC` 100 nF NP0** (Walsin 1206N104J500CT, C170182): no piezo noise, no bias loss, 5 GΩ min | `[ds ADI-LT3042.pdf p.16]`, `[ds WALSIN-MLCC-GENERAL-NP0-X7R.pdf p.6, p.13]` |
| In/out caps | **`C-REG-DAC`**, 10 µF 50 V X7R 1206 TDK CGA5L1X7R1H106KT0Y0N (C531431) ×2: `C-REG-IN` (new), `C-REG-OUT` (was 1 µF). `C-DEC-REG-IN` kept | `[ds ADI-LT3042.pdf p.15, p.17]`; bias derating `[from memory]` — open |
| Removed | `R-REG-SET-HI`, `R-REG-SET-LO`, `TRIM-DAC-RAIL`, `C-REG-ADJ`; nets `REG_ADJ`, `REG_TRIM`; new net `DAC_REG_SET` | `[repo]` sheet, `netlist.yaml` export, BOM fragment |
| **`dac-rail` 5.20 V → 5.23 V** | per CLAUDE.md rule 2: grepped the corpus for the old value and the trim wording first; forbidden added: `5.20 V`, `5.20V`, `5.20 / 10k`, `trims \`DAC AVDD\` to`, `trims \`DAC_AVDD\` to`, `trim \`DAC_AVDD\` to \`dac-rail\``, `E7 trims`, `as E7 trims it`, `trimmed to \`dac-rail\``, `trimmed to dac-rail`, `TRIM-DAC-RAIL 50R`, `Selected on the bench, per the figure's floor`. Every live hit moved | `[calc]` 100 µA × 52.3 kΩ = 5.230 V |
| **Spread, no trim: 5.107–5.352 V** at 65 corners: 107 mV over the floor and 148 mV under the top | I_SET 98–102 µA and V_OS ±2 mV over line, load and temperature; R-SET-DAC ±0.2 % (0.1 % + 25 ppm/°C × 40 °C); SET leakage ±100 nA; input 10.8–12.6 V; load 2–9 mA | `[ds ADI-LT3042.pdf p.3]`; `[sim] power-entry/sim dac-rail-spread`; `[calc]` 98 µA × 52.3k × 0.998 − 0.1 µA × 52.2k − 2 mV = 5.108 V, 102 µA × 52.3k × 1.002 + 0.1 µA × 52.4k + 2 mV = 5.353 V |
| Aged | R-SET-DAC at its ±0.5 % endurance limit as well: 5.082–5.379 V, inside | `[sim] dac-rail-aged` |
| Failures | **open `R-SET-DAC` → rail UP**, 10.5–12.3 V (recorded, asserted as the hazard, not fail-safe; owner question below); shorted `C-SET-DAC`/`R-SET-DAC` → rail down (≤ 2 mV) | `[sim] dac-rail-open-rset`, `dac-rail-short-cset` |
| Start-up | soft start R-SET-DAC × C-SET-DAC ≈ 5.2 ms: ≥ 4.5 V at 9.6–12.1 ms, ≥ 5.00 V at 14.1–21.3 ms, no overshoot at any corner of I_SET, R-SET-DAC, C-SET-DAC; pitch jack within 100 mV | `[sim] dac-rail-startup` |
| Fuses tripped | both rail PTCs at 6.0 Ω: DAC_AVDD comes up inside the window (the LM317L model never converged here, so this was arithmetic before) | `[sim] ptc-tripped` |
| SYNC fix still holds | `rails-and-sync` re-run on the LT3042: SYNC, SCLK_DAC, DIN ≤ DAC_AVDD + 0.3 V on and off at every corner (now including C-SET-DAC ±5 %); LOGIC_5V first (0.9–1.3 ms vs 10.2–11.3 ms to 4.5 V). The what-if's **power-off arm no longer bites** (0.25 V over, under 0.3 V: the LT3042's 0.3 V dropout lets DAC_AVDD follow LOGIC_5V down); its assertion now holds power-on only and records power-off | `[sim] digital-and-supervision/sim` |
| Sequencing against the rest | the DAC's power-on reset needs no ramp rate `[ds DAC8568CIPW.pdf p.38]`; the instrument's start through U-ISO and the load switch takes ≥ 42 ms (`umbilical-load-switch/sim cold-start`), and firmware refreshes reference-enable and clear-code (`firmware/README.md`); the breath offset dividers are ratiometric and follow the rail | `[repo]`, `[sim]` |
| `module-own-draw` ~37 → **~32 mA** on +12 V | the LM317L branch (12.4 mA, 7.5 of it its divider) became the LT3042's ~8.2 mA (4.5 mA load + 3.6 mA GND max + 0.1 mA SET). Forbidden added; dependents moved: `diode-split-rationale` (D1 r_d 2.8 → 3.2 Ω), fuse drops (15 → 13 mV, 0.27 → 0.19 V), jacks-shorted 97 → 92 mA, `power-entry/sim` `i_mod_pos`, `r_d_light` | `[calc]` in `module-own-draw` |
| Pages | `power-entry.md` (Interfaces row 32 no longer says "Selected on the bench"; drawing; *The DAC rail*, replacing *The DAC rail's load* / *trim*; fuses; Still open), `dac8568.md` + U-DAC row, `digital-and-supervision.md`, breath receive/output pages and rows, `breath-sense-link.md`, `spi-link` row, `module.md`, `nets.yaml`, ADR 0003/0004 (third amendment)/0005 (amendment)/0006/0027, ROADMAP E7 (measure and record, no trim) and *DAC saturation*, `tooling.md` §5 | `[repo]` |
| Sims replaced | `dac-trim-*` and `trim-ends-poweron` → `dac-rail-spread`, `-aged`, `-open-rset`, `-short-cset`, `-startup`, `ptc-tripped`; behavioural `power-entry/sim/lt3042.lib` (no vendor model: BLOCKED row) shared with `digital-and-supervision/sim` | `[sim]` |
| Datasheets | `.manifest-R43-F8.csv`: LT3042, ARG05, Walsin MLCC; LT3042 SPICE model BLOCKED (analog.com unreachable) | `verify-datasheets` |

**Found in passing, fixed:** `digital-and-supervision.md` and `dac8568.md`
cited the DAC8568's *"No device pin should be brought high before power is
applied"* as `[p.31]`; it is on p.38 (p.31 is the reference-capacitor text).

## OWNER

1. **The open-`R-SET-DAC` failure drives the rail up** past the DAC's and
   `U-LVL-MOD`'s absolute maxima. The LM317L design had the same single
   up-going failure (an open `R-REG-SET-LO`) and accepted it as a fixed
   thin-film part. Accept on the same terms, or ask for an over-voltage clamp
   on `DAC_AVDD` (not drawn: a zener cannot be guaranteed between 5.35 V and
   6.0 V at the LT3042's 220 mA limit).
2. **Nominal 5.23 V, not 5.20 V.** 52.3 kΩ is the nearest standard value to
   the window's centre; the nearest below, 51.7 kΩ, gives 5.17 V with less
   margin at the floor.
