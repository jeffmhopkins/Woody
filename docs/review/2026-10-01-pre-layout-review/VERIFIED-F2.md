# Pre-layout review — fixer F2's verification ledger

**Fixer F2**, 2026-10-01. Owned: every `A2-*` and `A3-*`, `A8-7`, `A8-8`. Base
`9956171` on `claude/car-instrument-cad-design-xvqwv2`, then merged with F3's
landing before finishing. Domain: module pitch-stage, mod-channels, dac8568,
power-entry, umbilical-load-switch, digital-and-supervision, link-supervision;
the module-main and module-jack sheets; ADRs 0004, 0005, 0006 (dated
amendments); their figures. Each finding was re-checked against the corpus
before acting; provenance as the wave's README asks.

**Counts:** 36 owned. **CONFIRMED 34, PARTLY 2** (A2-12, A3-2: the finding's
facts hold, the fix is partly an owner decision), REFUTED 0, DUPLICATE 0.
**OWNER: 3** (A2-12, A3-2, A8-8). **HANDED: 3** (to F3: A3-1, A3-6 in ADR 0027;
to F4: A2-20's board README note). Nine items received from F3 are at the end.

Commits: `4a9d0d6` (D-ESD-PITCH), `f53001d`, `7961558`, `46a14d2`, the C-ISO-Y
commit and the closing commit on this branch.

| Id | Verdict | Action | Evidence |
|---|---|---|---|
| A2-1 | CONFIRMED | **Fixed (docs only, the owner's decision).** New figure `mod-jack-range` (owner `mod-channels.md`); the page's range sentence, comparison table and tolerance table now say op-amp output vs jack; ADR 0006 decision table and dated amendment cite it; `mod-channels/sim` `why` no longer says the page lacks it | `[sim] mod-channels/sim range`: jack −9.9009/+9.9007 V nominal; worst corner 9.8026 / −9.7048 V. `[calc]` 19.703 × 100/101 = 19.508 V (−2.46 %), 20.303 × 100/101 = 20.102 V (+0.51 %); −29.6/+6.1 cents/oct at 1200 × error; nominal −11.9 |
| A2-2 | CONFIRMED | **Fixed (the owner's decision): `D-ESD-PITCH`**, Nexperia PESD15VL1BA,115 (LCSC C85378, 28 274 in stock at JLCPCB, extended), bidirectional, tip to sleeve on `pitch-stage.jack.kicad_sch` — the module jack board, before `J-B2B-MOD`. Datasheet banked (`discrete-and-power/NEXPERIA-PESD15VL1BA.pdf`, fragment `.manifest-R43-f2-prelayout.csv`). BOM row, exports, renders. `pitch-stage.md` *The jack-side ESD clamp*; `notes.md`'s old layout item answered. **Sim:** every pitch deck now places the stage twice, with and without the clamp, and asserts the difference | `[repo] pitch-stage/netlist.yaml` JACK_TIP → TRIM-GAIN.CCW → GAIN_TRIM_MID → RN-PITCH.R2B confirmed. `[ds LT5400.pdf p.6]` no ESD diodes, ±1 kV HBM; Figure 1 second option "bidirectional Zeners to ground"; p.2 80 V across any two pins. `[ds PESD15VL1BA p.3–4]` V_RWM 15 V, V_BR 17.1 V min, I_RM 50 nA max, C_d 16 pF typ, V_CL 25 V @ 1 A / 44 V @ 5 A. `[sim] pitch-stage/sim` (209 runs, 25 assertions, 0 failed): DC shift < 1 µV (measured 0); overshoot change ≤ 0.034 point (VCO, 0/200/800 pF cable, every corner, c_esd up to 32 pF); phase-margin change ≤ 6 × 10⁻⁶ ° at every load and cable |
| A2-3 | CONFIRMED | **Fixed.** ADR 0006: dated *Superseded* note under the precision table; "resistor tracking dominates" and "the DAC's internal reference is sufficient … buys nothing measurable" rewritten to the budget's ranking; `pitch-stage.md`'s aside that endorsed the 0.54 rewritten | `[calc]` 5 ppm/°C × 10 °C × 7 V = 350 µV = 0.42 cents (reference) against 0.027 (LT5400) — `pitch-cents-budget` |
| A2-4 | CONFIRMED | **Fixed** in ADR 0006, all five points: TRIM-GAIN ±1 % bipolar about R-GAIN-CTR, ~1 ppm/°C; "5 to 10 %" annotated with the built ±1 %; offset trimmer across VREFOUT ahead of the follower; the "a follower breaks that" rationale replaced with the negligible-effect arithmetic; "last spare op-amp half" → "`U-PITCH` half A" | `[repo] pitch-stage/netlist.yaml` VREFOUT = {R-VREF-SER.1, TRIM-OFFSET.CW}; `[ds DAC8568CIPW.pdf p.4]` 30 µV/mA sourcing load regulation; `[calc]` ~0.1 mA × 30 µV/mA ≈ 3 µV |
| A2-5 | CONFIRMED | **Fixed** (ADR 0006 bullet now says the node carries `C-FILT-PITCH` and why the loop tolerates it) | `[repo]` JACK_TIP includes C-FILT-PITCH.1 |
| A2-6 | CONFIRMED | **Fixed:** `pitch-stage.md` split-loop table (DC to ~7 kHz / above ~7 kHz) and the shelf's pole/zero; `C-AA-PITCH` BOM note | `[calc]` 1/(2π · 10.1 kΩ · 2.2 nF) = 7.16 kHz, zero 14.3 kHz. Not checked: the page's overall "−3 dB at 12.2 kHz" (no sim measures it; unchanged) |
| A2-7 | CONFIRMED | **Fixed:** "gain 2.020000" → the same gain for every load, 2.000 at mid-travel | `[sim] pitch-stage/sim dc-transfer`: gain 2.0000, intercept −2.5002 V |
| A2-8 | CONFIRMED | **Fixed:** the deck is rebuilt as `pitch-stage.lib`, one subcircuit with every part between VREFOUT, the DAC pin and the jack (TRIM-OFFSET halves, R-VREF-SER/INJ, follower at 1 + R-VREF-FB/R-VREF-GND, R-GAIN-CTR, TRIM-GAIN's section at `t_gain`, both at mid-travel); new `dc-transfer` and trim-end sims; `pitch-mult-overshoot` moved 41.8/64.1 → 41.6/64.0 % (old spellings now forbidden). TI's model loses its operating point away from jack 0 V with the network in, so the decks start there (README says why). **Also found:** `power-entry/sim/poweron.cir` carries the same pre-2026-09-30 pitch stage; its claim (jack 0 V with DAC and VREFOUT at 0) does not depend on the network, so it is left, noted here | `[sim]` trim-gain-ccw/cw 1.9901 / 2.0099 = 1 + 10k/10.1k, 1 + 10.2k/10.1k; trim-offset-ccw/cw V_ref 2.4396 / 2.5500 V; loop PM 69.33° (was 69.34°) |
| A2-9 | CONFIRMED | **Fixed:** the drawing's top half redrawn so `R-GAIN-CTR` and `R1` hang from `V_ref`, with `R-VREF-FB` closing to the follower's output and `R-VREF-GND` to AGND; `D-ESD-PITCH` added at the jack. `check-netlist --strict` 0 problems | `[repo]` VREF_BUFFERED = {R-GAIN-CTR.2, R-VREF-FB.1, U-PITCH.OUTA} |
| A2-10 | CONFIRMED | **Fixed:** "±10.05 V uses the DAC's full span" → ±10.000 V; the comparison table no longer restates the retired number | `[repo] mod-channels.md` |
| A2-11 | CONFIRMED | **Fixed:** zero at mid-code is `2.5(1 + k) − (10/3)k = 2.5 − (5/6)k`, 0 at k = 3, ∓50.5 mV for Δk = 0.0606 | `[calc]` (5/6) × 0.0606 = 0.0505 V |
| A2-12 | PARTLY | **Text fixed; the specification is OWNER.** The "one reel" sentence (impossible for 10k and 30k) replaced: the table is the 1 % spec, the sheet buys RT0805BRD07 0.1 % / 25 ppm thin film from one series, which shrinks the op-amp-output rows about tenfold and leaves the load row | `[repo]` sheet MPNs RT0805BRD0710KL / RT0805BRD0730KL ×4 each; value fields "10k 1%" / "30k 1%". **OWNER:** (a) keep 1 % as the spec and 0.1 % as what is bought (no change; the page now says so) or (b) make the value fields 0.1 % so the spec matches the part and the tolerance table tightens to ±5 mV / ±0.15 %. **Recommend (b)** — the part is already chosen and costs nothing more |
| A2-13 | CONFIRMED | **Fixed** in the `R-PRECISION` row: ±0.86 % to ±1.16 % on the B part; `notes.md` (history) left | `[calc]` ±100/(11 500 + 100) = ±0.86 %, ±100/(8 500 + 100) = ±1.16 %, against `[ds SBAS430E p.3]` ±0.15 % FSR gain error |
| A2-14 | CONFIRMED | **Fixed:** ADR 0006 *Labelling* and ADR 0004 *Panel*, each with a dated note | `[repo]` ADR 0026 points 4 and 7; ADR 0024 point 13 |
| A2-15 | CONFIRMED | **No change — already fixed at the base.** `9956171` re-rendered the module detail photo; module photos are the orchestrator's | `[repo] git log 9956171`; `check-staleness.py` at the end of this round (see the gates) |
| A2-16 | CONFIRMED | **Fixed** in `ROADMAP.md`: open item 5 now "R-OPAMP-IN is six"; the E9 load sweep reworded to verify a zero | `[repo] pitch-stage.md` *Settled 2026-09-30* |
| A2-17 | CONFIRMED | **Fixed:** decision table "Trimmed" → "Firmware-scaled, no trimmer"; "breath locked to channel 2" and "Channels 2–6" reworded to outputs; the amendment states the numbering | `[repo] 0006` |
| A2-18 | CONFIRMED | **Fixed:** ADR 0006 power-on table says 0 V to the zero-code error (+8 mV pitch, −12…+16 mV mods); `pitch-stage.md` likewise; `dac8568/sim` README says its exact 0 V is a model property | `[ds DAC8568CIPW.pdf p.3]` zero-code error 1 typ / 4 max mV |
| A2-19 | CONFIRMED | **Fixed:** page and `TRIM-OFFSET` BOM row say 72 cents one way and 60 the other | `[sim]` trim-offset-ccw/cw −60.4 / +50.0 mV of V_ref; `[calc]` × 1.2 cents/mV |
| A2-20 | CONFIRMED | **Partly fixed, partly HANDED.** Layout notes added where the parts are specified: `C-FILT-PITCH` at `J-B2B-MOD` pin 14 (`pitch-stage.md`), `C-FILT-MOD` at their jacks' pins (`mod-channels.md`). **HANDED TO F4:** if `hardware/boards/module-main/README.md` keeps placement notes, add C29 (`C-FILT-PITCH`) and C36–C39 (`C-FILT-MOD-1…4`) at `J-B2B-MOD` | `[repo] module-main/board-netlist.yaml` /PITCH_JACK = {C29, J2.14, R34, RV3.CCW} |
| A3-1 | CONFIRMED | **Fixed** in `power-entry.md` (table row and *Protection*), the `U-ISO` BOM row and ADR 0005's 2026-09-30 amendment: the load switch decides every start and fault except a replug inside `Q-INRUSH`'s window, ~1.2 A per rail of hiccup, below `PTC-ISO`'s trip; E6 scopes `ISO_POS12` and `ON`. **HANDED TO F3:** ADR 0027 point 2 (≈129–131, "the LT1641 decides every start and every fault") | `[repo] carrier/power-entry-instrument/sim/README.md` replug-early; figure `hotplug-iso-ocp`; `[calc]` 1.84 × 12 / 0.85 / 22.2 ≈ 1.2 A |
| A3-2 | PARTLY | **Text fixed; protection is OWNER.** The claim held only for a ±12 V swap. `power-entry.md` and `J-PWR-EURO` now say what a 16-pin cable turned at the bus does and that nothing on the module stops it. **The report's remedy does not work:** a 2×5 module header leaves the same bus-end reversal (cable wire *k* lands on bus pin 17 − *k*; the module's ground wires 3–8 still meet bus 14–9) | `[calc]` pin 17 − k; `[repo] power-entry/netlist.yaml` J-PWR-EURO pins; `[ds DOEPFER-A100-TECHNICAL-DETAILS-a100t_e.html]`. **OWNER:** (a) accept and document, as now — the generic 16-pin Eurorack hazard (**recommended**, the owner kept the 16-pin header for commonality, ADR 0023 point 3); (b) net only `J-PWR-EURO` pins 3–4 as ground and leave 5–8 unconnected: a bus-end reversal then lands module ground on the bus's CV (13–14) instead of +5 V/+12 V, so the module no longer bridges the rack's supplies and stays unpowered — zero cost, but two ground pins instead of six (the module's ground current is its own tens of mA since ADR 0027) and a departure from A-100 practice |
| A3-3 | CONFIRMED | **Fixed:** `umbilical-load-switch.md` Interfaces row and the `R-ON-HI` BOM description/notes say `ISO_POS12` (also F3's A4-5) | `[repo]` R-ON-HI.1 on ISO_POS12 |
| A3-4 | CONFIRMED | **Fixed:** `U-REG-LOGIC` sheet Note (`kicad.py set-field`, re-exported) and BOM description | `[repo] digital-and-supervision/netlist.yaml` LOGIC_5V = {U-RX-MOD.VCC, C-DEC-RX, R-PULL-CS}; U-LVL-MOD.VCC on DAC_AVDD |
| A3-5 | CONFIRMED | **Fixed:** `NT-AGND-MOD` sheet Note and BOM description say `BUS_GND` | `[repo]` NT-AGND-MOD.2 on BUS_GND |
| A3-6 | CONFIRMED | **Fixed:** new figure `module-own-draw` (~37 / ~20 mA, owner `power-entry.md`); rack totals → ~0.26 / ~0.24 A; clamp-legal −12 V → ~0.39 A; PTC drop row; `power-entry/sim` `i_mod_pos/neg` 0.037 / 0.020 from the figure; FB-IN row; ADR 0004's amendment. **HANDED TO F3:** ADR 0027 ≈180 "adds ~45 mA and ~40 mA" → cite `module-own-draw` (its spelling is not yet a forbidden pattern, so as not to fail F3's file) | `[calc]` 18.2 + 0.85 + 12.4 + 5.1 = 36.6 mA; 18.2 + 0.85 = 19.1 mA; 0.225 + 0.037 = 0.26 A, 0.225 + 0.020 = 0.245 A |
| A3-7 | CONFIRMED | **Fixed:** `C-BULK-RAIL` notes at the derived loads (no comparator); the conclusion holds | `[calc]` 37 mA / 100 µF = 0.37 V/ms, 20 mA / 47 µF = 0.43 V/ms; `[sim] power-entry/sim poweroff` |
| A3-8 | CONFIRMED | **Fixed:** FB2's sheet Note (U-ISO's +12 V leg, ~0.22 A, `ferrite-bias-impedance`) | `[repo] config/figures.yaml ferrite-bias-impedance` |
| A3-9 | CONFIRMED | **Fixed:** `hardware/nets.yaml` DAC_AVDD `carries` and the `U-REG-DAC` row now give headroom as the reason, and say the bus +5 V is unused | `[repo] 0005:131-141` |
| A3-10 | CONFIRMED | **Fixed:** `dac-rail` derivation adds I_ADJ × R2 (24/48 mV, 5.23 V typ) and the static spread 4.99–5.47 V; `digital-and-supervision/sim`'s assertion text now says the LM317L is at its model's nominal | `[ds LM317LZ.pdf p.5]` V_REF 1.20/1.25/1.30 V, I_ADJ 50/100 µA; `[calc]` as A8-8 |
| A3-11 | CONFIRMED | **Fixed** in ADR 0005's 2026-09-30 amendment (dated note): 110–160 %, 1.84 A minimum (also F3's A4-3) | `[ds RECOM-RPA20-AW.pdf PD-5]` |
| A3-12 | CONFIRMED | **Fixed:** ADR 0004 "qty 3" → 4 with what each is; a dated note under the pre-0027 power-tree diagram; ADR 0006's two "goes to three" likewise | `[repo] power-entry/netlist.yaml` D1–D4 |
| A3-13 | CONFIRMED | **Fixed:** `interfaces/spi-link` removed from the DAC AVDD row's peers | `[repo] hardware/nets.yaml` DAC_AVDD receivers |
| A3-14 | CONFIRMED | **Fixed:** `power-entry/sim` has a `poweroff` sim (`poweroff.cir`, the netlisted pitch stage from `pitch-stage.lib`, loads at `module-own-draw`, −12 V falling 2 ms early / together / late): the pitch jack stays within 100 mV (77 mV, only once the op-amps are out of supply). **Recorded:** −12 V reaches half first, 16.3 vs 20.1 ms | `[sim] power-entry/sim` 23 runs, 26 assertions, 0 failed |
| A8-7 | CONFIRMED | **Fixed:** `breath-excitation-reference/sim` assertions held to 2.5 mV and name the High grade (`ref5050-grade`); README row | `[sim]` vref_op 5.00247 V — TI's model is not grade-specific and sits on the 0.05 % edge, which the `why` says |
| A8-8 | CONFIRMED | **Spread corrected; the assembly is OWNER.** 0.66 V → 4.99–5.47 V static in `dac-rail`, ADR 0004 (dated), ADR 0006, `U-REG-DAC` | `[calc]` 1.20 × (1 + 475·0.999/(150·1.001)) = 4.99 V; 1.30 × (1 + 475·1.001/(150·0.999)) + 100 µA × 475 Ω = 5.47 V; `[repo]` sheet R-REG-SET-LO TC0525B4750T5G, Assembly = machine. **OWNER:** (a) make `R-REG-SET-LO` `Assembly = hand` and fit it at E7 from 475 / 478 / 481 Ω after measuring (**recommended**: the bench selection the documents describe, no rework); (b) keep it machine-placed at 475 Ω and rework only a unit that lands under 5.00 V — the low corner is 4.99 V; (c) machine-place 478 Ω — clears 5.00 V by 16 mV and 5.50 V by 1 mV before temperature `[calc]`, so it is not a fit either |

## Received from F3 (handed into this domain)

| From | Item | Action |
|---|---|---|
| A4-1 | `power-entry.md` *The common mode* and the `C-ISO-Y` row claimed a way home beside the converter | **Fixed**: both now give the AC deck's shares (1–2 % through `C-ISO-Y`, 88–98 % across the star, 12–43 % through `AGND_MOD`), warn against simply enlarging it, and point at ADR 0027's options; **OWNER** (F3's: CM choke recommended / 220 nF + 1 Ω / measure) |
| A4-3 | ADR 0005 "typical only" | **Fixed** (= A3-11) |
| A4-5 | `umbilical-load-switch.md:24` raw bus | **Fixed** (= A3-3) |
| A4-9 | `power-entry.md` 0.68 A hot-plug rows | **Fixed**: an ordinary hot-plug is `hotplug-iso-ocp`, ~0.36 A per rail `[calc: 0.54 × 12 / 0.82 / 22.2]`; 0.68 A is the early replug at the LT1641's limit (table and `PTC-ISO` row) |
| A4-10 | `power-entry/sim` `i_swing` source | **Fixed**: cites `led-row-current` |
| A4-12 | ADR 0005:96 (the 11.4 V subtracts a Schottky the feed no longer passes) and ADR 0004 ≈299–301 per-rail figures | **Fixed**: dated notes; ~11.8 V arrives; ADR 0004 per-rail figures cite `module-own-draw` |
| A5-6 | the receiver's settled high, 2.97 V | **Fixed** in `digital-and-supervision.md` and `R-RX-MOD`: ~3.26 V, the cable node's `[calc: 3.3 × 10k / 10 117]` |
| A5-9 | "six `R-SPI-PULL`" | **Fixed**: `digital-and-supervision.md` Interfaces row and drawing (two cable-side `R-SPI-PULL` plus `R-PULL-CS`); `link-supervision.md` |
| A5-10 | `link-supervision.md` "a display to report on" | **Fixed** (LEDs, ADR 0028; USB, ADR 0015). **Also found and fixed:** ADR 0006 and `mod-channels.md` still set ranges "on the instrument's display", which ADR 0015 removed — now the configuration over USB |

## Received from F5 (handed into this domain)

| Item | Action |
|---|---|
| `power-entry.md` "`r_d` is 69 mΩ at 392 mA" (and the `D-REVPOL` row's "r_d 69 mohm") | **Fixed**: ~0.55 Ω in `D2` at 0.22 A, ~2.8 Ω in `D1` at 37 mA, citing `diode-split-rationale` (F5's re-derivation); both spellings added to that figure's `forbidden` |
| `umbilical-load-switch.md` ≈327–330 described the 0805 C0G package defect already fixed in `C-TIMER-LOADSW` (A8-16) | **Fixed**: the paragraph now states the low-leakage requirement the row carries |
| `C-BULK-RAIL` buys two different parts (100 µF, 47 µF) in one row | **Not split — not clean this round.** The row name is read by `config/module.yaml` (`C-BULK-RAIL` sets a module CAD envelope and its `decided_by`) and from there by `mechanical/cad/generated/module-params.scad`, so a split re-generates module CAD and stales the orchestrator's module photos, and changes both sheets' `Row` fields (re-export, every module sim that hashes `power-entry/netlist.yaml` re-runs). **Next:** split into `C-BULK-POS12` (C1, 100 µF, UCM1H101MCL1GS on the sheet) and `C-BULK-NEG12` (C3, 47 µF), with the module.yaml envelope pointed at the 100 µF row, in a round that also re-renders the module |
| A9-5: `hardware/nets.yaml` (≈582, ≈706) and the `U-LVL-MOD` row "six R-SPI-PULL" | **Fixed**: five `R-SPI-PULL` and `R-PULL-CS` |

Also: `power-entry/sim`'s new derived values now tolerate the two sims that
import its params without the pitch netlist (`digital-and-supervision/sim`,
`panel-led/sim` failed on it once, re-run and passing).

## Open, with what decides each

- **A2-12** — the mod resistors' specification, 1 % or 0.1 %: the owner.
- **A3-2** — fewer ground pins on `J-PWR-EURO`, or accept: the owner.
- **A8-8** — how E7 selects `R-REG-SET-LO`: the owner.
- **A4-1** (received) — the converter's common-mode return: the owner, before the module layout (ADR 0027).
- **The pitch ESD clamp on the bench** — E9's existing stability row covers it; nothing new.
