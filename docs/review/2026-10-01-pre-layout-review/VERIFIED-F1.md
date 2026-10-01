# Pre-layout review — fix round, F1 (the breath chain)

**Fixer F1, 2026-10-01.** Base `9956171` on `claude/car-instrument-cad-design-xvqwv2`,
merged into this worktree's branch. Owned ids: every `A1-*`, plus `A8-1` and
`A8-4`. Each finding was re-checked against the corpus before anything was
changed; the evidence column says how. My own decks for the checks that are not
in the repository are under the session scratchpad (`F1/sim/chain.py`,
`a13.py`, `options.py`); the one that settles A1-1 is now in the repository as
`hardware/module/breath-output-stage/sim/chain.cir`.

| Id | Verdict | Action | Evidence |
|---|---|---|---|
| A1-1 | **CONFIRMED** | **OWNER** (options below); the pages now state the behaviour, and a repo sim owns the numbers (`breath-chain-curve-clip`) | `[sim]` the shaper and output stage chained as netlisted (`breath-output-stage/sim`, `chain`, `chain-centre`): GAIN at noon, OFFSET at zero, `POT-RESP` fully CW, `BREATH_OUT` clips from an in-amp output of −3.51 V = **0.76× a hard blow** (≈2.1 kPa `[calc: 3.51/(0.7665 × 2.16106)]`); 9.99 V at the click. Reproduces the reviewer's −3.48 V / 9.99 V. The shaper page's "beyond real playing" was true of `BREATH_SHAPED` only |
| A1-2 | **CONFIRMED** | Fixed (wording): `breath-response-shaper.md` now says the knob changes level as well as shape, and that "harder/easier to get loud" holds only after GAIN is re-set | The repo's own `sim/README.md` table: ratio > 1 at every level at CW (1.11 *pp* → 1.64 hard), < 1 at every level at CCW (0.82 → 0.44). Which behaviour is *intended* is part of A1-1's owner decision |
| A1-3 | **CONFIRMED** | Fixed per owner (buy 1N4448W, no circuit change): `D-RESP` is Vishay **1N4448W-E3-08**, LCSC C3313020 (280 in stock `[web lcsc.com/product-detail/C3313020.html, 2026-10-01]`), same SOD-123 case as the 1N4148W-E3-08 so the footprint stands; datasheet banked (`datasheets/discrete-and-power/1N4448W.pdf`, fragment `.manifest-R43-F1.csv`); sheet fields, BOM row, sim text, `shaper-exp-gain` `diode_note` | `[ds 1N4448W.pdf p.2]` VF 0.62–0.72 V at 5 mA, exactly the window `is_d` is fitted to. `[sim, F1/a13.py]` worst corner reproduced: **1.5066×** (1N4448W slow end, 27 °C) and **1.4770×** (1N4148W at its 0.715 V-at-1 mA limit) — the reviewer's numbers to four places. **Residual, not fixed (owner said no circuit change):** at the same corner 1.4958× at 15 °C and 1.4824× at 0 °C (1.5183× at 40 °C); 3.6 kΩ would give 1.524 / 1.513 / 1.499× at 27/15/0 °C. Recorded on the shaper page and in `shaper-exp-gain` |
| A1-4 | **CONFIRMED** | Fixed at the sheet: `POT-OFFSET`'s ends swapped (CW → `AGND_MOD`, CCW → `DAC_AVDD`), so clockwise is positive and the panel's `+` at the CW end stop is true. **Panel art unchanged** — no photo re-render needed for this. Exported (circuit, `module-jack`), rendered, sims re-run, page table and notes corrected | Polarity: the summer inverts (`R-BREATH-OFF` into the (−) input), so wiper → `DAC_AVDD` drives the jack negative `[sim, offset]`: now −4.91 V at CCW, +5.06 V at CW, zero at p = 0.433 (18.7° **counter-clockwise** of centre). Pin sense: `Pins` `CW=3 CCW=1` on both pots; R0904N drawing R09N-003 `[ds R0904N.pdf p.2]` shows pins 1-2-3 left to right from the front with the shaft drawn full CCW; the conventional "CW toward 3" is `[from memory]` on the sheet and applies identically to `POT-GAIN`, so swapping OFFSET's ends is right whichever way it lands — if it were wrong, GAIN would be backwards too. **HANDED** (panel.md, below) |
| A1-5 | **CONFIRMED** | Fixed per owner: `C-SENSOR-VS-BULK` 1 µF, `C-SENSOR-VS-HF` 10 nF on `VS`, `C-SENSOR-OUT` 470 pF on `SENSOR_RAW`, on the `breath-sense-link` sheet at the sensor (main board `C201`–`C203`), three new BOM rows, the `U-BREATH` row's "OPEN" note closed, page section added | `[ds MPXV4006DP.pdf p.5, Figure 3]` rendered and read: 1.0 µF, 0.01 µF, 470 pF. The 470 pF is ahead of `U-BUF` B (a follower), so it reaches neither the link sims nor the ADC: nothing to re-run there. The `VS` pair is the reference buffer's load: `[sim, breath-excitation-reference/sim *-as-built]` ~1.11 µF total, margin 122° min (was 118.5° worst at 47 nF), `|Z_out|` 1.20 Ω at 500 Hz unchanged, **but the ~38 Ω Z peak moves from 26 kHz to 7.6 kHz and a load step now rings back ~45 %, settling in 0.44 ms** — recorded as a finding with an assert, judged harmless (steady sensor draw, peak far above the breath band). **The main board's layout has to place three new parts** |
| A1-6 | **CONFIRMED** | Fixed: output stage, receive stage, shaper page and both sims' `v_hard` sources now cite 2.8 kPa as `breath-working-point`'s candidate, open until E2; the output page gives the GAIN the 3–4 kPa candidate would need (2.01–1.51×) | `config/figures.yaml` `breath-working-point` is `disputed`; ADR 0003 says 0–5 kPa. `[calc]` 3 kPa → 4.97 V, 4 kPa → 6.63 V at the in-amp |
| A1-7 | **CONFIRMED** | Fixed on `breath-receive-stage.md` (the unsourced "20 mV" withdrawn; the datasheet bound carried, ±0.53 V / ±1.07 V at the jack; open item with what decides it). **HANDED**: ROADMAP E2 row | `[ds MPXV4006DP.pdf p.4, Table 1, Notes 4–5]` ±2.46 % with auto-zero within ±5 °C, ±5.0 % without. `[calc]` 0.0246 × 4.6 × 4.66 = 0.527 V; 0.05 × 4.6 × 4.66 = 1.07 V |
| A1-8 | **CONFIRMED** | Fixed: interface row reworded | Page's own −12 V paragraph and ADR 0027 |
| A1-9 | **CONFIRMED** | Fixed: 0.328–0.817 V on the page and in the `TRIM-BREATH-ZERO` row; three old spellings added to `breath-zero-ref`'s `forbidden` (grepped first: page wrap, page "band's", CSV) | `[calc]` 0.152 × 2.16106 = 0.3285, 0.378 × 2.16106 = 0.8169 |
| A1-10 | **CONFIRMED** | Fixed: ADR 0006 dated amendment, 0.29–2.3 V (3.3 V at the band top), standing CV "about 7 V" (≈8 V at the band top); `"less 0.2 to 1.7 V"` forbidden | `[calc]` 0.573 × 0.503 = 0.288, × 4.02 = 2.30; −4.91 − 2.30 = −7.21; 0.817 × 4.02 = 3.28 |
| A1-11 | **CONFIRMED** (all four parts) | Fixed: `BREATH_INAMP_OUT`'s `To` on the receive sheet → `module/breath-response-shaper` (re-exported); the receive page's drawing now has the shaper box; `U-OPA-PITCH` row's "U-RESP claims both" corrected; "(PROPOSED)" removed from the shaper sheets' title blocks | `hardware/nets.yaml` already named the shaper as receiver |
| A1-12 | **CONFIRMED** | Fixed: "fifty times" replaced with the simulated 13.5 dB; "Where the two ends disagree" closed, citing `breath-link-cmrr` | `breath-receive-stage/sim/README.md`; figure `breath-link-cmrr` settled 2026-09-30 |
| A1-13 | **CONFIRMED** | Fixed: ~459 Hz on `breath-sense-link.md` (twice) and ADR 0006 (~460 Hz). **HANDED**: `docs/reference/latency-budget.md` | `[calc]` 1/(2π × 22 kΩ × 15.75 nF) = 459.3 Hz. The 482 Hz of the jack's 1 k/330 n RC is a different pole and is right |
| A1-14 | **CONFIRMED** | Fixed: interface row and the "buffered 5.21 V" sentence | netlist: `DAC_AVDD` straight to the pot |
| A1-15 | **CONFIRMED** | Fixed: (4.86 − 0.7)/10 k = 416 µA | `[calc]` |
| A1-16 | **CONFIRMED** (advisory) | Fixed: a noise paragraph on `breath-receive-stage.md`, marked as an estimate, E11 the measurement | `[ds MPXV4006-AN1646.pdf pp.1–2]` read: noise 500 Hz–1 MHz, "4 or 5 counts on a 10-bit A/D", RC + 4-sample average ≈ 1 mV pk-pk (measured on the MPX5006 family) |
| A8-1 | **CONFIRMED** | Partly fixed: `C-DEC-BUF` 100 nF drawn at `U-BUF.V+` (excitation sheet, main board `C204`), `C-DECOUPLE-CARRIER` now 6 placed of 8 bought. **HANDED**: the row's qty and notes (in `carrier/led-strip-drive/bom.csv`) and `carrier.md`'s "two R-78E5.0 bucks" | `check-netlist --strict` was 5/8, now 6/8; ADR 0015 one buck (`U-BUCK` qty 1, its input has `C-BUCK-IN`) |
| A8-4 | **CONFIRMED** | Fixed: `shaper-exp-gain` carries `conditional_on: breath-working-point` with what E2 moves (`R-RESP` re-checked then); the shaper page and sims cite the dispute | `[calc]` 4.64 / 2.16106 / 0.7665 = 2.80 kPa |

| A9-13 (handed from F5) | **CONFIRMED** | Fixed: "the table below" → "the table above (*Scaling*)" on `breath-response-shaper.md` | The 15 kΩ table sits under *Scaling*, before the bullet that cites it |

**Counts:** 18 owned ids (plus A9-13, handed in) — 18 confirmed (A1-11 in all four parts), 0 partly, 0
refuted, 0 duplicate. One is an owner decision (A1-1); A1-2's wording is fixed
but which behaviour is intended rides on A1-1.

## A1-1 — OWNER: how the curve knob and the commissioned gain relate

`[sim]` all with the shaper and output stage as netlisted, nominal parts, ideal
±12 V (the module's rails, a Schottky lower, clip slightly earlier). "Hard" is
an in-amp output of −4.64 V, the 2.8 kPa candidate. Clip = the in-amp output
`BREATH_OUT` stops rising at, as a multiple of a hard blow. None of the options
touches the shaper, so **the owner's 1.5× floor (`shaper-exp-gain`) is
unchanged by A, B and C**; D breaks it.

**Today** (commission at the click, GAIN noon 2.156×):

| `POT-RESP` | CCW | ¼ | click | ¾ | CW |
|---|---|---|---|---|---|
| Hard blow at `BREATH_OUT` | 4.36 V | 8.34 V | 9.99 V | 10.97 V | 11.97 V (rail) |
| Clip from | none | 1.47× | 1.19× | 1.08× | **0.76×** |

**A — commission with `POT-RESP` fully CW** (no BOM change; procedure and page
wording only). GAIN lands at p ≈ 0.23 (≈1.31×), putting the exp end's hard
blow at 10.0 V.

| `POT-RESP` | CCW | ¼ | click | ¾ | CW |
|---|---|---|---|---|---|
| Hard blow | 2.66 V | 5.08 V | 6.09 V | 6.68 V | 10.00 V |
| Clip from | none | none | 1.97× | 1.73× | 1.17× |

No curve setting clips a hard blow at the commissioned gain. Cost: the linear
setting gives ~6 V for a hard blow and log ~2.7 V until the player raises GAIN —
the curve knob stays a level control, but now only downward from the
commissioned point.

**B — keep the click, add the rule "re-set GAIN after moving the curve"** (no
BOM change). GAIN for 10 V at a hard blow: CCW **unreachable** (8.13 V at
GAIN's 4.02× top), ¼ p = 0.59, click 0.47, ¾ 0.42, CW 0.23. Once re-set, every
setting clips at 1.17–1.21× a hard blow. This is what the pages say *now*, as
the interim rule.

**C — B plus a wider GAIN range**: `R-BREATH-IN` 10 k → **7.32 k** and
`R-GAIN-FLOOR` 7.15 k → **4.99 k** (two E96 values; `R-BREATH-FB` and the offset
network untouched, so the offset table does not move). Range 0.497×–5.49×
`[sim]`. GAIN for 10 V: CCW p = 0.89 (clip 1.28×), ¼ 0.42, click 0.33, ¾ 0.29,
CW 0.16. Every curve setting can reach 10 V. Costs: the working gain leaves
noon (2.16× sits at p = 0.33; noon is ≈3.0×), the summer's noise gain rises
from 7.4 to 8.8 `[calc: 1 + 40.2k/(R-IN ∥ 21k ∥ 95.3k)]` (the loop margin, 95.6°
today, needs a re-run), and the "gain at noon" text on two pages moves.

**D — an end resistor between `V_IN_HALF` and `POT-RESP`'s CW end** (one part).
To stop CW clipping a hard blow at noon gain it needs ≥ 10 kΩ, and then the exp
end's hard-blow ratio is **1.19×** (20 k: 1.07×, 50 k: 1.00×). **Fails the 1.5×
floor** — listed only to show that limiting the knob cannot be squared with
the floor.

**Recommendation: A**, with the commissioning step and the two pages' wording
changed to match; add C only if the owner wants the log end to reach 10 V for a
hard blow. A costs nothing, removes the only setting that walls off real
playing, and does not depend on E2: commissioning uses the player's own hard
blow, whatever `breath-working-point` turns out to be. (Eurorack VCAs commonly
open fully at 5–8 V `[from memory]`, so ~6 V at the linear setting is a usable
default, not a loss.) A true "shape-only" curve — the shaper's hard-blow gain
normalised to 1 at every setting — needs a second gang or a second op-amp
stage and is a redesign, not recommended at the layout gate.

## HANDED

- **A7 / panel owner — `hardware/module/panel/panel.md` ~line 138**: "its
  'zero at centre' actually sits ~20° past centre at +0.605 V" → the zero now
  sits **~19° counter-clockwise of centre** (POT-OFFSET's ends were swapped
  2026-10-01 so that clockwise is positive, A1-4); the centre still reads
  +0.605 V. The panel art (`config/module.yaml` `art.*`, the `+`/`−` marks) is
  **correct as it stands and needs no change**.
- **Orchestrator — `ROADMAP.md` E2 "Cold-start warm-up sweep" row (A1-7)**: add
  "and log the breath jack at rest across the 20 minutes at the commissioned
  gain, with a pass threshold set there (`breath-receive-stage.md`,
  *Commissioning*)".
- **Orchestrator — `docs/reference/latency-budget.md:42` (A1-13)**: the receive
  filter is ~459 Hz, not 482 Hz: `1/(2π × 22 kΩ × 15.75 nF)`, 347 µs not
  330 µs. Check whether `loop-budget` or any total uses the 330 µs.
- **Orchestrator — `docs/reference/tooling.md` §5 coverage table**: the
  breath output stage's row can add `chain` (the shaper and the stage
  together). (Its 1N4148W → 1N4448W wording had already landed by the merge.)
- **Owner of `hardware/carrier/led-strip-drive/bom.csv` (A8-1)**: row
  `C-DECOUPLE-CARRIER` qty **8 → 6** and its enumeration: MCP3202
  (`C-DEC-ADC`), REF5050 IN and OUT (`C-DEC-REF-VIN`, `C-DEC-REF-VOUT`),
  OPA2197 +12 V (`C-DEC-BUF`, drawn 2026-10-01), 74AHCT125
  (`C-DECOUPLE-LED`), MPXV4006DP VS (`C-DEC-SENSOR`); "both R-78E5 inputs" is
  gone since ADR 0015 (one buck, its input is `C-BUCK-IN`). Cut the
  2026-09-21 history from the cell (CLAUDE.md 2b).
- **Owner of `hardware/carrier/carrier.md`**: line ~87 "the two R-78E5.0
  bucks" → one (ADR 0015); and the §2 drawing, if it draws the sensor's pins,
  can show Figure 3's three capacitors.
- **Main-board layout agent**: four new parts on the main board — `C201`
  1 µF, `C202` 10 nF at `U10` pin 2, `C203` 470 pF at `U10` pin 4 (all to
  pin 3's `AGND_INST`), `C204` 100 nF at `U3` pin 8. References chosen high to
  avoid collisions; renumber if another fixer took them.
- **Orchestrator — merge note**: `pitch-stage/sim` and `mod-channels/sim`
  results were re-run here only because they hash `breath-output-stage`'s
  netlist (the passive-mult load); nothing they use changed. If another fixer
  also re-ran them, take either and re-run after the merge.

## Open, with what decides each

- A1-1: the owner (above).
- A1-3 residual: below ~20 °C in the case the worst corner dips under 1.5×.
  Decided by the owner (accept, or `R-RESP` 3.6 k) or by E10 on a real module.
- A1-6/A8-4: E2's manometer test; `R-RESP` re-checked then.
- A1-7: E2's warm-up log of the jack at rest, with a threshold (ROADMAP, handed).
