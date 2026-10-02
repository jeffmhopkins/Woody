# Instrument power entry — simulation

`sims.yaml` says what is simulated and what every run must show; `pei-z.cir`
(the impedance the buck sees) and `pei-start.cir` (the start: cold,
hot-plugged, and pulled and put back) are the decks; `results.yaml` is **generated** by
`python3 tools/sim.py run hardware/carrier/power-entry-instrument/sim`.
`docs/reference/tooling.md` §5 explains the tool.

**No part value is written here.** The decks read every netlist the path
crosses: this circuit's (`C-STRIP-BULK`, `L-BUCK-IN`, `C-BUCK-IN`), the load
switch's (`R-ILIM`, the gate network, `C-TIMER-LOADSW`, the FB divider) and the
module's power entry (`C-ISO-OUT`), and this circuit's inrush limiter
(`Q-INRUSH` and its gate network). The LT1641 is `umbilical-load-switch/sim`'s
behavioural part, included from there, and its datasheet parameters are
imported from that `sims.yaml` (`params_from`), not restated.
**`Q-LOADSW` is chosen now** (PSMN2R0-30YLE): its threshold, `R_DS(on)` at
4.5 V and `C_iss` are from its banked sheet. `U-ISO` (RPA20-2412SAW) is a 12 V
source that soft-starts over 8–16 ms and is **clamped at its lowest
over-current threshold, 1.84 A** (110 % of 1.67 A, where it hiccups — its
PD-5). The umbilical is one conductor each way, R and L from the banked Cat5e
datasheet, the resistance swept up to 28 AWG because the gauge is open. The
buck is a constant-power load (1.26 W, from `umbilical-current`'s derivation)
from its 8 V input minimum up. `Q-INRUSH` (AO3401A) is a level-1 P-FET fitted
to its banked sheet's threshold, `R_DS(on)`, `C_iss`, `C_rss` and body diode;
`J-UMB`'s node carries `D-TVS-PWR`'s capacitance, read off its sheet's curve.

**The deck starts from its operating point**, with the `+12 V` contact as a
switch. A hot-plug is the contact closing on a load switch whose FET is
enhanced with nothing on its output — the state the module is in, instrument
or not — so the FET's `V_GS` before the plug is `dV_GATE`, as it is on the
bench. (The deck this replaced started a hot-plug from initial conditions that
put `V_GS` at 16.5 V with the output at 12 V.)

## What it shows

| Sim | What | Result |
|---|---|---|
| `input-z` | the impedance at `C-BUCK-IN`, looking back through `L-BUCK-IN`, `C-STRIP-BULK` and the cable | peak 0.57 Ω at 3.8 kHz at the nominal; **55× (35 dB) under the buck's −103 Ω at the worst corner**, 180× at the nominal |
| `cold-start` | the rack powers up with the instrument plugged in | starts at every corner in 109–239 ms; `U-ISO` never above 0.54 A; the buck's input never falls back once it has started; nothing near `D-TVS-PWR`'s 15 V |
| `hot-plug` | the instrument plugged into a running module, 65 corners | starts at every corner in 94–183 ms, no fault latch. **`U-ISO` peaks at 0.50–0.56 A at every corner, 3.3× under its 1.84 A over-current threshold** (`hotplug-iso-ocp`); `VCC` at the load switch does not move (11.996 V); the ring at `J-UMB` peaks at 14.2 V, under `D-TVS-PWR`'s standoff; `Q-INRUSH` dissipates 1.8 W at most |
| `replug-late` | running, pulled, and put back 200 ms later | starts again from off: `U-ISO` 0.51–0.53 A |
| `replug-early` | running, pulled, and put back 30 ms later | **A recorded hazard:** the bulk still holds a few volts and `Q-INRUSH` is still enhanced, so the replug reaches `U-ISO`'s threshold, as every hot-plug did before `Q-INRUSH`; see `results.yaml` for how long, and `VCC`'s dip, at every corner including the LT1641's highest gate drive |

## What it says that the page does not

- **The damping claim holds, for a different reason than the page gives.**
  The page puts `Q` between 0.25 and 1.8 by reading `C-BUCK-IN`'s ESR between
  its two datasheet *maxima*; a real part sits below its maximum, so that range
  is not a worst case. The run sweeps the ESR down to a third of the 100 kHz
  maximum and finds the margin still 55×, because `C-STRIP-BULK` (470 µF, its
  own ESR) sits at the input node ahead of the LC and the cable's resistance
  behind it: they, not `C-BUCK-IN`'s ESR alone, set the peak. Keep the
  electrolytic — the conclusion survives, the arithmetic behind it does not.
- **Without `Q-INRUSH` a hot-plug reached `U-ISO`'s current limit**, at
  every corner, for over 100 µs — longer at the LT1641's higher gate drives.
  The load switch's FET is enhanced whenever the module runs, so the plug put
  the instrument's ~570 µF straight onto `C-ISO-OUT` through the cable; the
  LT1641's limit then had to pull a gate that `C-GATE-LOADSW` was holding up
  through `R-GATE-COMP`, and the model's amplifier (its transconductance is an
  assumption, the datasheet gives none) let the current overshoot until it
  had. `umbilical-load-switch/sim` could not see this: it models `U-ISO` as a
  resistance with no limit.
- **`Q-INRUSH` takes the question away from the LT1641.** Everything that
  holds charge is behind a Miller ramp, so the plug sees only `J-UMB`'s node,
  and the load switch never enters its limit. What is left is a replug while
  the instrument still holds charge (`replug-early`): whether the RPA20
  hiccups on it depends on how long its over-current detection waits, which
  RECOM does not publish. **E6 decides**: pull and replug the instrument
  quickly with a current probe on `U-ISO`'s output.

## In the register

This README owns, in `config/figures.yaml`:

- `instrument-input-z-margin`: 55x worst corner, 180x nominal (peak 0.57 ohm at 3.8 kHz)
- `hotplug-iso-ocp`: 0.50-0.56 A at every corner, 3.3x under the threshold and never at it

## What a result is worth

A behavioural LT1641, a converter modelled as a clamped source, and a level-1
P-FET. The start itself is `umbilical-load-switch/sim`'s result, confirmed here
with the chosen FET, the cable and a constant-power buck; what is new is the
converter's limit and the inrush limiter in front of the instrument's bulk. How
fast the instrument drains after an unplug, which sets how long `replug-early`'s
window lasts, is the model's loads, not a measurement.
