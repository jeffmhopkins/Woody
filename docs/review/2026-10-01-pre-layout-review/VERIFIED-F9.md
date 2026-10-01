# VERIFIED — fixer F9 (A8-8 accepted; F4's leftovers)

**Fixer F9, 2026-10-01.** Base `claude/car-instrument-cad-design-xvqwv2` at
`e777b44` (F8 merged), then `2918984` (F4 merged) before the end. `tools/`
unchanged. Not touched: `hardware/boards/module-main/README.md` and
`hardware/boards/module-jack/README.md` (another agent's; text handed over in
the report), `mechanical/**`.

| Id | Verdict | Action | Evidence |
|---|---|---|---|
| A8-8 (owner, final) | **ACCEPTED** (owner) | The owner, 2026-10-01: *"Good to accept them"* — `dac-rail` at 5.23 V, and the open-`R-SET-DAC` failure (rail to ~11 V, over the DAC8568's 6 V absolute maximum) **with no protection circuit**, mitigated three ways. Recorded in `power-entry.md` (*Its failures*; removed from *Still open*), ADR 0005 (dated amendment), `dac-rail`'s floor, `power-entry/sim` `dac-rail-open-rset`'s wording | `[sim] power-entry/sim dac-rail-open-rset`: 10.50–12.30 V, nominal 11.70 V |
| A8-8 mitigation 1 — part | **DONE** | `R-SET-DAC` → **Vishay TNPW060352K3BEEA**, 0603, 52.3 kΩ ±0.1 % ±25 ppm/K, anti-sulfur, LCSC C4241066 (JLC 886, LCSC 865 in stock). Sheet fields (Manufacturer, MPN, LCSC, Footprint `R_0603_1608Metric`, Note), export, renders (power-entry, module-main), BOM fragment, `dac-rail` derivation, sims; `ARG05BTC5232` added to `dac-rail`'s forbidden list. Datasheet banked: `.manifest-R44-F9.csv` | `[ds VISHAY-TNPW-E3-THIN-FILM-RESISTOR.pdf p.1]` "Advanced sulfur resistance verified according to ASTM B 809"; p.4 part number B = ±0.1 %, E = ±25 ppm/K; p.2 0603 long-term \|ΔR/R\| ≤ 0.30 % at 225 000 h at P70 (general mode); p.13 substrate bending 2 mm, no open circuit |
| A8-8 — why 0603, not 0805/1206 | **DEVIATION, reported** | The brief allowed 0805 or 1206. No anti-sulfur 52.3 kΩ 0.1 % part in either size was in stock at JLC or LCSC on 2026-10-01 | `[web jlcpcb.com parts API 2026-10-01]` all 1601 hits for "52.3kΩ" scanned; in-stock 0805/1206 0.1 % parts: Viking ARG05BTC5232, Yageo RT0805/RT1206BRD0752K3L, RESI PTFR0805B52K3P9, Uni-Royal TC0525B5232T5G, TE RN73C2A52K3BTDF — none claims sulfur resistance in its datasheet (text-searched; the banked Viking ARG sheet too). Anti-sulfur families at 0 stock at both: TNPW0805/1206 e3 (C1711691, C1713145), KOA RN73H (C4251756, C2557476), Susumu RG (C2132793, C1697562), Panasonic ERA-6A/8A (C6191395, C2089125; and the ERA datasheet makes no sulfur claim) `[web LCSC product API 2026-10-01]` |
| A8-8 — the spread holds | **VERIFIED** | Tolerance and TCR are the ARG05's, so `dac-rail-spread` is unchanged; `dac-rail-aged` now uses the TNPW's ±0.3 % long-term limit (was the ARG's ±0.5 %) | `[sim] power-entry/sim` 166 runs, 41 assertions, 0 failed: spread **5.107–5.352 V** (nominal 5.2295 V), aged **5.092–5.368 V**, both inside 5.00–5.50 V. `[calc]` dissipation 5.23² / 52.3 kΩ = 0.52 mW of 0.110 W |
| A8-8 mitigation 2 — layout | **DONE** | `power-entry.md` *How it is wired*: `R-SET-DAC` away from standoffs, connectors and board edges, long axis parallel to the board's long edge, inside the `SET` guard ring; the same on the sheet's `Note` and the BOM row. The module-main README text is in F9's report for its owner | `[repo]` |
| A8-8 mitigation 3 — E7 | **DONE** | ROADMAP E7: on the first build, measure `DAC_AVDD` before `U-DAC` **and `U-LVL-MOD`** are fitted; both are `Assembly = machine`, so the first assembly order leaves them off and they are hand-fitted after the reading; thereafter measure and record with them fitted. `U-LVL-MOD` added because it runs from the same rail | `[ds SN74AHCT125.pdf]` V_CC absolute maximum 7 V; `[repo]` both sheets' `Assembly` fields |
| A6-8 | **FIXED** | `J-MCU` row: part named (XKB X1270WR-2x12A-9TV01, C5147255, as the sheet buys), status `selected`, mouth faces the tail (ribbon over the tongue), pin-1/numbering and 1 A rating cited to banked drawings; "PART NUMBER OPEN" and the strip sentence removed | `[repo] carrier.kicad_sch J-MCU`; `[repo] pcb-geometry.echo` J-MCU direction +1; `[ds XKB-X1270WR-2x12A-9TV01.pdf]`, `[ds YXCON-IDC3-24232A1AUC1…pdf]` 1 A |
| F4 hand-over: U-BUCK tails | **FIXED** | `U-BUCK` row: cut its pins to `boards.tht_trim` (cited, not restated) after soldering, citing drc.echo's tails rule | `[repo] config/body.yaml boards.tht_trim` (F4) |
| A6-9 | **FIXED** (J-CHAIN, CBL-CHAIN); MECH-UBOLT **already landed** (F4) | "LED strip" → "LED row (ADR 0028)" in both rows | `[repo]` DESIGN.md already says "far band beside the LED row"; `hardware/unplaced.csv` MECH-UBOLT has no strip text after F4 |
| A7-10 | **ALREADY LANDED** (F2, `f53001d`) | none | `[repo]` R-ON-HI row says ISO_POS12; module-main `board-netlist.yaml`: R57.1 on `ISO_POS12`, R57.2 on `ON_SW` with SW1.NO |
| A7-13 | **FIXED** | `SW-POWER` row: fit ONE nut, on the front, with the lockwasher; the rear nut is not fitted, because it would move the body back by `toggle.nut_h` | `[repo] mechanical/cad/module.scad` one front nut, body from the panel's rear face; `[ds NKK-SERIES-M-TOGGLE.pdf p.7]` two nuts, one lockwasher |
| A7-9 | **FIXED** (jack board); main board **by design, no symbol** | module-jack sheet: `H1`–`H4` `MountingHole_Pad` (`MountingHole_3.2mm_M3_Pad`), Row `MECH-STANDOFF-MOD`, Exclude from BOM, `Assembly = none`, pin on `AGND_MOD`; exported (ERC 0/0), rendered. Main board's pads are on no net, so the netlist needs nothing; they follow the key boards' precedent of board-only mounts placed by the layout | `[repo] board-netlist.yaml` `/AGND_MOD` has H1.1–H4.1; `check-netlist --strict` 0 problems, MECH-STANDOFF-MOD placed 4/4 |
| A7-7 | **ALREADY LANDED** | ADR 0004 carries the amendment (*"amended 2026-10-01: this said PITCH and BREATH silkscreened and the mods on a write-on strip"*, ADR 0026 points 4 and 7); ADR 0024 point 2's pointer landed with F4 (F9's own version dropped at the merge in its favour) | `[repo]` |

## Gates (at the head of this branch)

- `check-netlist.py --strict`: 0 problems (U-BREATH 1/2 short, pre-existing).
- `merge-bom.py --check`: 215 rows, 26 fragments, 0 problems.
- `verify-datasheets.py`: 281 verified, 43 blocked or not fetched, 0 problems.
- `sim.py check`: PASS, 20 sim dirs. Re-run: power-entry, power-entry-instrument, digital-and-supervision, panel-led, umbilical-load-switch — 0 failed.
- `check-staleness.py`: 0 stale values; **3 cad**: `module-photo-hero`, `-front`, `-detail` stale on `config/body.yaml`/`config/module.yaml` — from F4's merge, not this round's edits; `python3 tools/cad.py build` by the CAD owner.
- `kicad.py check`: PASS, 22 sheets, 6 boards, 129 renders.

## OWNER

1. **0603, not 0805/1206.** The only in-stock anti-sulfur 52.3 kΩ 0.1 % part.
   The same family in 0805 is `TNPW080552K3BEEA` (C1711691), out of stock;
   ordering it means a footprint change on the sheet and nothing else.
2. **First build, `U-DAC` and `U-LVL-MOD` left off the assembly order** and
   hand-fitted after the `DAC_AVDD` reading (TSSOP-16 and SOIC-14).
