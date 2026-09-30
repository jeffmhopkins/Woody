# Instrument power entry — simulation

`sims.yaml` says what is simulated and what every run must show; `pei-z.cir`
(the impedance the buck sees) and `pei-start.cir` (the start, cold and
hot-plugged) are the decks; `results.yaml` is **generated** by
`python3 tools/sim.py run hardware/carrier/power-entry-instrument/sim`.
`docs/reference/tooling.md` §5 explains the tool.

**No part value is written here.** The decks read every netlist the path
crosses: this circuit's (`C-STRIP-BULK`, `L-BUCK-IN`, `C-BUCK-IN`), the load
switch's (`R-ILIM`, the gate network, `C-TIMER-LOADSW`, the FB divider) and the
module's power entry (`C-ISO-OUT`). The LT1641 is `umbilical-load-switch/sim`'s
behavioural part, included from there, and its datasheet parameters are
imported from that `sims.yaml` (`params_from`), not restated.
**`Q-LOADSW` is chosen now** (PSMN2R0-30YLE): its threshold, `R_DS(on)` at
4.5 V and `C_iss` are from its banked sheet. `U-ISO` (RPA20-2412SAW) is a 12 V
source that soft-starts over 8–16 ms and is **clamped at its lowest
over-current threshold, 1.84 A** (110 % of 1.67 A, where it hiccups — its
PD-5). The umbilical is one conductor each way, R and L from the banked Cat5e
datasheet, the resistance swept up to 28 AWG because the gauge is open. The
buck is a constant-power load (1.26 W, from `umbilical-current`'s derivation)
from its 8 V input minimum up.

## What it shows

| Sim | What | Result |
|---|---|---|
| `input-z` | the impedance at `C-BUCK-IN`, looking back through `L-BUCK-IN`, `C-STRIP-BULK` and the cable | peak 0.57 Ω at 3.8 kHz at the nominal; **55× (35 dB) under the buck's −103 Ω at the worst corner**, 180× at the nominal |
| `cold-start` | the rack powers up with the instrument plugged in | starts at every corner in 53–214 ms; `U-ISO` never above 0.50 A; the buck's input never falls back once it has started; nothing near `D-TVS-PWR`'s 15 V |
| `hot-plug` | the instrument plugged into a running module | starts at every corner, no fault latch. **A recorded hazard:** `U-ISO` sits at its 1.84 A over-current threshold for **120–168 µs** at every corner (`hotplug-iso-ocp`), and `VCC` at the load switch dips to 11.44 V |

## What it says that the page does not

- **The damping claim holds, for a different reason than the page gives.**
  The page puts `Q` between 0.25 and 1.8 by reading `C-BUCK-IN`'s ESR between
  its two datasheet *maxima*; a real part sits below its maximum, so that range
  is not a worst case. The run sweeps the ESR down to a third of the 100 kHz
  maximum and finds the margin still 55×, because `C-STRIP-BULK` (470 µF, its
  own ESR) sits at the input node ahead of the LC and the cable's resistance
  behind it: they, not `C-BUCK-IN`'s ESR alone, set the peak. Keep the
  electrolytic — the conclusion survives, the arithmetic behind it does not.
- **A hot-plug reaches `U-ISO`'s current limit.** With the FET already
  enhanced, `C-STRIP-BULK` charges from `C-ISO-OUT` before the LT1641's limit
  takes the gate back, and `U-ISO` is asked for its whole limit for about
  150 µs. Whether the RPA20 then hiccups depends on how long its over-current
  detection waits, which RECOM does not publish. If it does, the load switch's
  `VCC` collapses and the start repeats. **E6 decides**: hot-plug the
  instrument into a running module with a current probe on `U-ISO`'s output.
  `umbilical-load-switch/sim` could not see this: it models `U-ISO` as a
  resistance with no limit.

## In the register

This README owns, in `config/figures.yaml`:

- `instrument-input-z-margin`: 55x worst corner, 180x nominal (peak 0.57 ohm at 3.8 kHz)
- `hotplug-iso-ocp`: 120-168 us at every corner

## What a result is worth

A behavioural LT1641 and a converter modelled as a clamped source. The start
itself is `umbilical-load-switch/sim`'s result, confirmed here with the chosen
FET, the cable and a constant-power buck; what is new is the converter's limit.
