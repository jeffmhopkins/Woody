# Module power entry — simulation

`sims.yaml` says what is simulated and what every run must show; `poweron.cir`,
`poweroff.cir`, `groundshift.cir`, `cm.cir`, `isoin.cir` and `dacrail.cir` are the decks; `results.yaml` is what the last run found, **generated** by
`python3 tools/sim.py run hardware/module/power-entry/sim`.
`python3 tools/sim.py show <this dir>` prints it as a table.
`docs/reference/tooling.md` §5 explains the tool.

**No part value is written here.** The deck reads this circuit's netlist and
`module/pitch-stage`'s, because the claims being checked are about what the
pitch jack does while this circuit's rails arrive.

## What it shows

Rack power-on, every node starting at 0 V: the bus rails rising at
`J-PWR-EURO`, `D1`/`D3`, the beads as their DC resistance, the bulk capacitors,
`U-REG-DAC`, the LT3042, making `DAC_AVDD` (behavioural, `lt3042.lib`: no
vendor model could be banked - fragment R43-F8), and the pitch
stage on those rails with the DAC at its power-on-reset zero scale.

| Sim | What | Holds |
|---|---|---|
| `as-netlisted[dt_neg=…]` | the rails, `DAC_AVDD` and the pitch jack, the −12 V rail arriving 1 ms early, together, and 5 ms late | `DAC_AVDD` settles at or above `dac-rail`'s hard floor and never reaches the DAC8568's 6 V absolute maximum; the pitch jack stays within 100 mV of 0 V throughout |
| `d3-reversed` | a what-if: `D3` fitted with its anode at the bus | `MODULE_ANALOG_NEG12` never arrives |
| `poweroff[dt_neg_off=…]` | `poweroff.cir`: rack power-off — the bus rails falling (−12 V 2 ms early, together, 2 ms late), `D1`/`D3` reverse-biasing, each analog rail decaying on `C1` or `C3` into `module-own-draw`, and the netlisted pitch stage (`pitch-stage/sim`'s `pitch-stage.lib`, trims at mid-travel) parked on them | the pitch jack within 100 mV of 0 V all the way down. **Recorded:** the two rails reach half 16–23 ms after the bus goes, −12 V first; the jack moves (77 mV) only once the op-amps are out of supply |
| `gnd-before[r_bus_seg=…,i_swing=…]` | `groundshift.cir`: the rack's copper — the bus board from the PSU to this module's tap, the power ribbon's rails and ground — with the instrument's breath-following current returning through the star, as it did until ADR 0027 | several cents of pitch error at every bus position and swing (4.2–21 cents over the sweep) |
| `gnd-isolated[…]` | the same rack with the instrument behind `U-ISO`: its power drawn rail to rail, its output floating and tied to the star | under 0.01 cents, and under a microamp in the tie |
| `gnd-sense[…]` | option (b): the pitch reference on a current-free ribbon conductor | the ribbon's share goes, the bus board's stays |
| `gnd-balanced[…]` | option (c): a dummy load holding the instrument's total constant to 1 % | a fraction of a cent, for 2.3–4.4 W of heat |
| `cm-loop` | `cm.cir`: `U-ISO`'s 550 kHz common-mode current, driven through its 1100 pF isolation capacitance, home through `C-ISO-Y` or round the module's grounds and the star, with `L-CM-ISO` in the converter's input (pre-layout review A4-1), across the choke's core loss and inductance, the ribbon and `C-ISO-Y` | under the owner's 10 % across the star at 550 kHz, 1.65 MHz and 5.5 MHz, and nowhere above it from 500 kHz to 30 MHz |
| `cm-loop-y-1n` | a what-if: the choke with the 1 nF `C-ISO-Y` it replaced | more than 10 % on the star at the core-loss corner — why `C-ISO-Y` is 22 nF |
| `iso-input-z` | `isoin.cir`: the impedance `U-ISO` sees looking back into its input filter, `L-CM-ISO`'s leakage included, and the share of its input current that reaches the rack | over 20× inside the converter's −V²/P at every corner; under 1 % at the rack at 550 kHz |
| `dac-rail-spread` | `dacrail.cir`, DC: `DAC_AVDD` at every corner of the LT3042's guaranteed SET current (98–102 µA) and offset (±2 mV), `R-SET-DAC`'s 0.1 % and drift, 100 nA of SET leakage either way, the input from a tripped fuse to the bus maximum, and the load | inside the DAC8568 C grade's 5.00–5.50 V with 50 mV to spare at both ends, and nominally `dac-rail` — **no trim** |
| `dac-rail-aged` | the same with `R-SET-DAC` at its ±0.5 % endurance limit as well (1000 h at rated power, 70 °C) | still inside 5.00–5.50 V |
| `dac-rail-open-rset` | `R-SET-DAC` open | **recorded, not fail-safe**: the rail goes *up*, to the input less the dropout, over the DAC's 6 V absolute maximum — the one single failure that does |
| `dac-rail-short-cset` | `C-SET-DAC` (or `R-SET-DAC`) shorted | the rail goes down, to the offset |
| `dac-rail-startup` | `poweron.cir` across the SET current, `R-SET-DAC` and `C-SET-DAC` | the soft start never overshoots the window; over the 5.00 V floor within 50 ms; the pitch jack within 100 mV of 0 V |
| `ptc-tripped` | `poweron.cir` with both rail fuses at 6.0 Ω, their worst an hour after a trip | `DAC_AVDD` still comes up inside the window; the pitch jack within 100 mV |

**The power-on runs have the rail fuses in them** (`PTC-POS12`, `PTC-NEG12`,
ADR 0027) at their fitted resistance, 0.40 Ω, and `ptc-tripped` at 6.0 Ω,
their worst an hour after a trip. *(Until 2026-10-01 that case was arithmetic
only: TI's LM317L model, the regulator then, did not converge with 6.0 Ω in
series.)*

**The ground sims are resistive and say so.** Every resistance is a param with
its provenance in `sims.yaml` — two review calculations for the ribbon and the
bus board — and `r_bus_seg` is swept from 1 mΩ (the receiver in the next slot;
ngspice will not take 0) to the whole 0.25 m trace. They show where the
instrument's current flows and what it moves, which is the question; they
do not model the converter's switching (see ADR 0027 for why it is out of
band) or any cable's inductance.

**`cm.cir` and `isoin.cir` are small-signal and their copper is estimated.**
The parts on the loop come from the netlist; every trace, ESL, bead bias point
and the rack's own decoupling is a param marked `[assumption]` in `sims.yaml`,
taken from the deck that found the problem
(`docs/review/2026-10-01-pre-layout-review/F3-u-iso-cm-loop/`). `L-CM-ISO`'s
core loss at 550 kHz is not published — only its 20 dB band from 500 kHz —
so it is swept from 500 Ω to 3.6 kΩ per winding, and the low end is the one
that sizes `C-ISO-Y`. Neither deck says how much current the converter makes:
that is RECOM's to publish and E6's to measure.

**`U-REG-DAC` is behavioural, and says so.** ADI ships the LT3042's model
inside LTspice and analog.com did not answer, so `lt3042.lib` builds it from
the banked datasheet: the SET current into SET, the unity-gain buffer to `OUT`
with its offset, the dropout, UVLO, GND current, the overshoot-recovery sink
and the SET-to-OUTS clamp. It holds the DC spread and the soft start, which is
what is asked; it does not hold the loop's dynamics, noise or PSRR.
`digital-and-supervision/sim` includes the same file.

**`D3` must have its cathode at the bus.** The rail it passes flows out of the
module into the bus's −12 V, so a diode with its anode at the bus is
reverse-biased by it: the module's −12 V node then sits at about +0.3 V
(leakage and the loads), and every op-amp on it runs single-supply. This run
found the sheet drawn that way; the sheet was corrected on 2026-09-30, and
`d3-reversed` keeps the failure on record. **The deck types `D3`'s orientation
(`d3_flip`) rather than reading it from the netlist**, so a change to `D3` on
the sheet must be mirrored in `sims.yaml`.

## What it does not show

- **What `VREFOUT` does before firmware enables the reference.**
  `pitch-stage.md` says it is 0 V, so the jack sits at 0 V. The DAC8568's
  datasheet says the internal reference is disabled by default and the pin is
  then `VREFIN`, an input. The deck holds it at 0 V, which is the page's claim,
  not a finding. **Bracketed since 2026-10-01 by
  [`dac8568/sim`](../../dac8568/sim/)**: the pin as 3-state with
  `C-VREF-DAC` and ±1 µA of leakage moves the parked jack about 9 mV per
  µA; the real leakage is still the bench's (E9).
- The DAC's outputs before its own power-on reset has run: the deck holds the
  channel at zero scale from the start. `R-BIAS-DAC` is what the page relies on
  for that window. The datasheet's power-on glitch is in
  [`dac8568/sim`](../../dac8568/sim/).
- **`LOGIC_5V` and the DAC's SPI pins.** `U-REG-LOGIC` is not in this deck;
  its race with `DAC_AVDD`, and the requirement that `SYNC`, `SCLK_DAC` and
  `DIN` stay under `DAC_AVDD + 0.3 V` through it, are
  [`digital-and-supervision/sim`](../../digital-and-supervision/sim/)'s.

## What a result is worth

The 1N5817 has no banked vendor model (fragment R29 records the URLs that
failed): it is a diode fitted to the two points the `D-REVPOL` row reads off
the banked curve, and `sims.yaml` shows the arithmetic. Loads are stated
assumptions. **A simulated transient is a screen, not a spec**: it either
agrees with the bench or tells you where to look.
