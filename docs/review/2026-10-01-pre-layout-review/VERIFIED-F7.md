# Pre-layout review — fix round, F7 (curve trimmer, mod resistor spec)

**Fixer F7, 2026-10-01.** Base `ec20ecf` on `claude/car-instrument-cad-design-xvqwv2`,
merged into this worktree's branch. Two owner decisions carried out: the A1-3
residual (owner: *"With trimmer again?"*) and A2-12 (owner: make the mod gain
resistors' specification 0.1 %). `tools/` not modified.

| Id | Verdict | Action | Evidence |
|---|---|---|---|
| A1-3 (residual) | **FIXED** (owner) | `TRIM-RESP` added in series with `R-RESP` on the shaper's `main` sheet: **Bourns 3224W-1-103E**, 10 kΩ ±10 %, 12-turn sealed cermet, top adjust, LCSC C81348 (26,461 at JLC `[web jlcpcb.com parts search, 2026-10-01]`), `Assembly = hand`, module-main `RV4`; wiper strapped to its CCW end (net `RESP_TRIM`), CW end to `DIODE_BRANCH`. `R-RESP` 3.9 k → **2.7 k** (UNI-ROYAL 0805W8F2701T5E, C17530, Basic). Datasheet banked (`.manifest-R44-F7.csv`). Sheet exported, circuit and module-main rendered, BOM fragment (`R-RESP` row rewritten, `TRIM-RESP` row new), page (*Settled*, *Headroom*, *Still open*, new *Commissioning*), ROADMAP E10, output-stage page, both sims, `shaper-exp-gain` and `breath-chain-curve-clip` re-derived, old spellings forbidden | `[ds BOURNS-3224-TRIMPOT.pdf p.1]` ±10 %, end resistance 1 % or 2 Ω, 12 turns, sealed, "wiper idles" at the stops, 1 CCW / 2 wiper / 3 CW. `[sim, breath-response-shaper/sim]` 2607 runs, 0 failed: **`exp-end-trimmed`** (the deck bisects the trimmer to 1.55× per corner, 256 corners incl. the trimmer's track, commissioned at 15 °C and 30 °C) reaches 1.5498–1.5502× everywhere; **1.5198× minimum at 0 °C** (trimmed at 30 °C; 1.5345× trimmed at 15 °C); 1.558–1.576× at 40 °C; clip from −7.19 V worst. **`exp-end-trim-cw`** (end resistance only, 513 corners): ≥ 1.564× at 15 °C (target reachable), ≥ 1.549× at 0 °C, clip −6.16 V worst at 40 °C = **1.33× a hard blow**, so the strongest end keeps `BREATH_SHAPED`'s clip outside real playing. **`exp-end-trim-ccw`** (whole track, = open wiper, 1025 corners incl. trimmer ±10 %): 1.24–1.45× at 30 °C — under the target everywhere, still expansive (fail-safe). The set point lands at 0.77–4.62 kΩ of the 10 k track |
| A2-12 | **FIXED** (owner) | Value fields of all eight `R-MODGAIN-IN`/`-FB` instances → `10k 0.1%` / `30k 0.1%` (the sheet already bought RT0805BRD07); BOM part fields and notes; page drawing, *Values*, tolerance table and the zero-point paragraph; ADR 0006 (two places); `mod-jack-range` re-derived; mod sim's span assertion; README | `[ds YAGEO-RT-…-RT0805FRE0710KL.pdf p.2]` B = ±0.1 %, TCR D = 25 ppm/°C. `[calc]` k = 3 × 0.999/1.001 … 3 × 1.001/0.999 = 2.9940–3.0060; zero ∓(5/6) × 0.0060 = ∓5.0 mV (was ±50.5 mV); span 5 × (1 + k) = 19.970–20.030 V; at the jack × 100/101 = 19.772–19.832 V, −1.14 %/−0.84 %; −13.7 to −10.1 cents/oct worst (resistors alone ±1.8). `[sim, mod-channels/sim range]` span 19.97–20.03 V; jack −9.8811/+9.8908 and −9.9207/+9.9106 V at the corners, the calc to 1 mV |

## Choices, and what decides them

- **Target 1.55×, not 1.5×** at commissioning: a unit trimmed warm (30 °C)
  loses ~0.03 by 0 °C `[sim]`; 1.55× leaves 1.52×. The target lives in
  `sims.yaml` (`g_trim`) and the figure; the page cites the figure.
- **R-RESP 2.7 k, trimmer 10 k.** 2.4 k fixed puts the strongest corner's clip
  at exactly 1.30× at 40 °C (explored in scratch, not committed); 3.0 k fails to
  reach 1.55× at the weak corner at 15 °C once the trimmer's end resistance is
  added. A 5 k trimmer would almost do (needs 4.62 k; 5 k −10 % = 4.5 k) — 10 k
  leaves room for E2 moving the working point, at 12 turns the resolution is
  ample.
- **Temperature model:** ngspice `temp`, SPICE-default diode tempco (XTI 3,
  EG 1.11) — an assumption; the 1N4448W sheet gives no tempco. E10 is the
  measurement.
- **Commissioning by injected DC, not breath**: the breath pair driven from a
  bench supply until the in-amp reads −4.64 V, then `TRIM-RESP` until
  `BREATH_SHAPED` = 1.55 × that. A ratio, so independent of what pressure a
  volt is; re-checked when E2 settles `breath-working-point`.

## Not better than today in one place, stated

`breath-chain-curve-clip` (GAIN at noon, curve fully CW — A1-1's open case):
as commissioned the jack clips from 0.79× a hard blow (today 0.76×). With
`TRIM-RESP` left at its **clockwise end** it clips from **0.73×** — 0.03 worse
than today; at its CCW end 0.90×. The shaper's own clip stays past 1.3× at every
corner at both ends (asserted). Squaring this completely would need `R-RESP`
high enough that the weak corner cannot reach the target; A1-1 option A
(commission GAIN with the curve fully CW) removes the jack clip whatever the
trimmer does.

## HANDED

- **Orchestrator / module-main layout (and F4 for `config/module.yaml`)**:
  `TRIM-RESP` (module-main `RV4`, Bourns 3224W, 4.8 × 5.1 mm body, top adjust,
  SMD) goes on the **main board's rear face beside the other three trimmers**
  (`tall.at`'s `trim` row near y = 95), reached from behind with the module out
  of the rack, like them. It is SMD on the rear face, so it is **hand-soldered**
  (`Assembly = hand`) unless the board gets two-sided assembly. Keep it within
  a few mm of `R-RESP`/`D-RESP` (the branch is a high-impedance node into the
  virtual ground) — or, if the shaper sits far from the trimmer row, short
  traces on the `RESP_TRIM`/`DIODE_BRANCH` side matter more than on the
  `WIPER` side. `config/module.yaml` `tall.at` gains a fourth `trim` envelope
  (the 3224W is a few mm tall, far under the 3296W's 10 mm — read its height
  off `BOURNS-3224-TRIMPOT.pdf` p.1 before adding it; not done here). No panel cut-out: it is not a panel control.
- **Orchestrator — ROADMAP E10 row**: I added the `TRIM-RESP` step; the same row
  still ends "Four mod channels trimmed", but the mod channels have no trimmer
  (ADR 0006: firmware-scaled). Not mine to settle; flagged.
- **Merge note**: `pitch-stage/sim` and `dac8568/sim` results re-run only for the
  mod-channels netlist hash; nothing moved. `breath-output-stage/sim` re-run
  after both changes.

## Open, with what decides each

- The trimmer's real range against a real diode and pot: E10's commissioning
  (a unit that cannot reach 1.55× from either end is outside every simulated
  corner — measure `POT-RESP` first).
- The commissioning voltage (−4.64 V) rides on `breath-working-point`: E2.
- A1-1 (curve knob vs commissioned GAIN): still the owner's.
