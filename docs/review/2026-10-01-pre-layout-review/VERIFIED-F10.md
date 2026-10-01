# VERIFIED — fixer F10 (A8-8: the anti-sulfur `R-SET-DAC` reverted)

**Fixer F10, 2026-10-01.** Base `claude/car-instrument-cad-design-xvqwv2` at
`6ceb178`. `tools/` unchanged.

| Id | Verdict | Action | Evidence |
|---|---|---|---|
| A8-8 mitigation 1 — part | **REVERTED** (owner) | The owner, 2026-10-01: *"Yes revert, no need for these specialized parts bifurcation"* — anti-sulfur parts judged unnecessary. `R-SET-DAC` back from F9's Vishay TNPW060352K3BEEA (0603, C4241066) to F8's **Viking ARG05BTC5232**, 52.3 kΩ ±0.1 % ±25 ppm/°C, 0805, LCSC C2758300. Sheet fields (Manufacturer, MPN, LCSC, Footprint `R_0805_2012Metric`, Note — anti-sulfur clause removed, layout clause kept), export, renders (power-entry, module-main), BOM fragment and master. The accepted failure now has **two** mitigations: placement and the first-build check (`power-entry.md` *Its failures*, ADR 0005 amendment, module-main README) | `[ds VIKING-ARG-THIN-FILM-RESISTOR.pdf p.3]` TCR/tolerance; `[repo]` `git show b35b18a` for the F8 values restored |
| A8-8 — register | **DONE** | `dac-rail`: derivation cites the ARG again; `ARG05BTC5232` removed from `forbidden` (it is the live part); `TNPW0603`, `TNPW 0603`, `TNPW e3`, `C4241066`, `ASTM B 809` added, with a `note` saying what they were. "anti-sulfur" deliberately *not* a pattern: the prose recording the owner's decision has to name it | `[repo] config/figures.yaml` |
| A8-8 — the spread holds | **VERIFIED** | `dac-rail-aged` back to the ARG's ±0.5 % endurance limit (tol ±0.7 % with the 0.2 % initial+drift) | `[sim] power-entry/sim` 166 runs, 41 assertions, 0 failed: aged **5.082–5.379 V** (as F8), spread unchanged 5.107–5.352 V. `[calc]` 5.23² / 52.3 kΩ = 0.52 mW of 1/8 W = 0.4 % |
| A8-8 — citation page | **CORRECTED** | F8 cited the ARG's endurance (±0.5 %) and the bending test at `p.3`; in the banked PDF both are on **p.4** (Bending Strength ΔR ±0.1 %, 3 mm amplitude). The flex sentence in `power-entry.md` now cites the ARG's 3 mm test, not the TNPW's 2 mm | `[ds VIKING-ARG-THIN-FILM-RESISTOR.pdf p.4]` (pdftotext per page) |
| A8-8 mitigation 2 — layout | **UNCHANGED** | Placement rule kept: away from standoffs, connectors and board edges, long axis along the board's long edge, inside the `SET` guard ring. module-main README: part named as the ARG05 0805; the "never substitute without an anti-sulfur claim" bullet deleted | `[repo]` |
| A8-8 mitigation 3 — E7 | **UNCHANGED** | First build: assemble without `U-DAC` and `U-LVL-MOD`, measure `DAC_AVDD` at E7, hand-fit | `[repo] ROADMAP.md` E7 (not touched) |
| A8-8 — the banked Vishay sheet | **KEPT** | `VISHAY-TNPW-E3-THIN-FILM-RESISTOR.pdf` and its `.manifest-R44-F9.csv` row stay as records (rule 4); `verify-datasheets` passes with them | `[test]` 281 verified, 0 problems |
