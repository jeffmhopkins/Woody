# Module power entry — simulation

`sims.yaml` says what is simulated and what every run must show; `poweron.cir`,
`poweroff.cir`, `groundshift.cir`, `cm.cir`, `isoin.cir`, `dacrail.cir` and `ledpwm.cir` are the decks; `results.yaml` is what the last run found, **generated** by
`python3 tools/sim.py run hardware/module/power-entry/sim`.
`python3 tools/sim.py show <this dir>` prints it as a table.
`docs/reference/tooling.md` §5 explains the tool.

**No part value is written here.** The decks read this circuit's netlist and
`module/pitch-stage`'s, because the claims being checked are about what the
pitch jack does while this circuit's rails arrive; `ledpwm.cir` also reads
`mod-channels`, `breath-output-stage`, `umbilical-load-switch` and
`carrier/power-entry-instrument`, and takes the instrument side's estimates
(cable, ESRs, `U-ISO`'s output resistance, the buck's power) from
`power-entry-instrument/sim` and `umbilical-load-switch/sim` (`params_from`).

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
| `iso-input-z` | `isoin.cir`: the impedance `U-ISO` sees looking back into its input filter, `L-CM-ISO`'s leakage included, and the share of its input current that reaches the rack | over 20× inside the converter's −V²/P at every corner; under 1 % at the rack at 550 kHz; **no gain from 1 to 10 kHz** (at most 75 % reaches the rack: the LC's 3.1 kHz corner is overdamped by `D2`, `D4`, `PTC-ISO` and the beads in the same loop) |
| `led-pwm[f_pwm=…]` | `ledpwm.cir`: every WS2815B-V1 on the instrument's main board (fourteen, counted from the LED drive's netlist) pulsing in phase at half duty, 2–4 kHz and the LC's corner, through `C-STRIP-BULK`, the umbilical, the load switch, `U-ISO` (input = output power / η), its input filter and the rack; the rails at the header and the bus tap, the module's analog rails, `DAC_AVDD`, and the pitch, mod 1 and breath jacks (TI's OPA2197 model) | under the review's 13 mV on the case's rails; pitch under ADR 0027's 0.01 cents (it reaches ~0.001); mod 1 under one LSB; breath under 1 mV. **Recorded:** `led-pwm-rail-ripple`, worst at 2 kHz, `C2`'s highest ESR and a 200 mΩ supply |
| `led-pwm-duty[d_led=…]` | the same at 2 kHz, duty 1/256 to 255/256 | the same; half duty is the worst |
| `led-pwm-pattern[n_lit=…,spread=…]` | seven of the fourteen lit; all fourteen's pulses spread over the period, as free-running oscillators land | the same; spread evenly, fourteen half-duty pulses sum to a constant and the ripple vanishes in the model (each LED's own oscillator drifts, so in phase is the bound) |
| `led-pwm-at-iso[f_pwm=…]` | a what-if, the review's premise: the row's whole current out of `U-ISO`, no instrument bulk | **recorded**: the header reaches 15–19 mV with a 200 mΩ supply — the review's 13 mV was not a bound on its own premise; the instrument's bulk is what keeps the design under it |
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

## The LED PWM runs (A4-13)

**What the row draws.** Each WS2815B-V1 is a pulse of its share of
`led-row-current`'s top end (`i_swing` / 13) less its 2 mA quiescent, on top
of the quiescent, at duty = brightness / 256. The datasheet does not draw its
output stage, so the pulse is the whole pixel's current whichever channels are
lit — at a given brightness, white is the worst. Its oscillator tolerance is
not published: the sweep covers the stated 2 kHz scan to 4 kHz refresh and
the filter's corner, and the response falls monotonically with frequency
across it, so a slower oscillator would be worse; at 1 kHz the filter passes
75 % (`iso-input-z`) and the instrument's bulk keeps less.

**`U-ISO` is behavioural, and conservative.** Its input draws its output power
over η (0.82) from whatever its input pins see, instantly: its negative input
resistance is in the run, and the whole PWM step reaches its input. A real
loop (250 µs to recover from a 25 % step, `[ds PD-5]`) and its output
capacitance would hold some of it back; and its incremental efficiency is
higher than its average (off the dissipation curve, ~1.11 W in per W out
against 1/0.82 = 1.22), so the step at its input is overstated by ~10 %. Its
own input capacitance is not published: 4.7 µF assumed, nothing beside `C2`.

**The op-amps hang on copies of the rails.** TI's OPA2197 model found no
operating point with two or more instances beside this network, so the run is
a power-on from 0 V (`uic`, every supply ramped over 1 ms, settled for 25 ms
before the 10 ms window), and the five op-amps sit on the rails' DC plus each
rail's ripple through a 1 ms high-pass, drawing nothing from the network
(`module-own-draw` is their current). `DAC_AVDD` is its set point plus +12 V's
ripple at 80 dB, an assumed floor under the LT3042's typical curves (100–118 dB
at 1–10 kHz with 0.47 µF on SET; `C-SET-DAC` is 0.1 µF) since `lt3042.lib`
has no PSRR; the DAC8568 publishes no AC supply rejection, so all of
`DAC_AVDD`'s ripple is passed to `VREFOUT` and both DAC outputs. Even so
`DAC_AVDD` moves by a fraction of a microvolt; pitch is set by the op-amps'
rejection of the ±12 V ripple.

**The rack is estimated.** Its copper, decoupling and PSU resistance are the
`cm.cir`/`isoin.cir` params; `r_psu` at 200 mΩ is the worst corner of every
measure, so a stiffer case does better. Its ground carries none of `U-ISO`'s
current and is ideal here.

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
