# Breath excitation reference — simulation

`sims.yaml` says what is simulated and what every run must show; the `.cir`
files are the decks; `results.yaml` is what the last run found, **generated**
by `python3 tools/sim.py run hardware/carrier/breath-excitation-reference/sim`.
`python3 tools/sim.py show <this dir>` prints it as a table.
`docs/reference/tooling.md` §5 explains the tool.

**No part value is written here.** Each deck's double-braced names are filled
from `../netlist.yaml` and, for the sensor's own capacitors, `interfaces/breath-sense-link/netlist.yaml`. The models are TI's own, banked in `datasheets/analog/`
with their SHA-256: the OPA2197 (`OPAx197-ti-pspice-sboma34d.lib`) and the
REF5050 (`REF5050-ti-pspice-slim175a.lib`).

## What it shows

The reference half of `U-BUF` driving `VS` through `R-ISO-REF`, with the dual
feedback of `riso-ref-topology`, at the nominal and every tolerance corner.

| Sim | What | Holds |
|---|---|---|
| `loop-as-netlisted[c_vs=…]` | loop gain, broken at `U-BUF`'s (−) input; loads 47 nF, 100 nF, 1 µF, 10 µF, 10.1 µF at `VS` | the page's robustness claim (above 76°) less the ±10° screen, at every corner; `VS` within 5 mV of 5.000 V |
| `zout-as-netlisted[c_vs=…]` | the output impedance at `VS`, closed loop | 1.20 Ω at 500 Hz within 10 % |
| `step-as-netlisted[c_vs=…]` | a 0.5 mA load step at `VS` | recovers without ringing through |
| `step-with-10u-added` | the same with 10 µF added at `VS` | **a recorded finding**: it rings |
| `loop-as-built`, `zout-as-built`, `step-as-built` | `VS` loaded with everything netlisted there — `C-DEC-SENSOR` and the sensor's Figure 3 pair from `interfaces/breath-sense-link`, ~1.11 µF | margin 122° minimum; 1.20 Ω at 500 Hz; the ~38 Ω peak at 7.6 kHz; **a recorded finding**: a load step rings back ~45 %, settled in 0.44 ms |
| `reference-alone` | TI's REF5050 model, as netlisted, and a 1 V droop of +12 V | 5.000 V within 0.1 %; under 1 mV of disturbance |
| `loop-bare-follower`, `loop-in-loop-riso-only` | the two circuits the page rejects | both short of 45° |
| `ti-figure-56` | TI's own Figure 56, as printed | TI's published 89° within the screen: the deck and the break are sound |

**The phase margin as netlisted is 118.5 deg minimum, crossover 1.23-1.28 MHz**
(`riso-ref-phase-margin`), the least at 47 nF. Measures with no assertion are
recorded for the page's arguments: `iso_drop` (the DC drop across `R-ISO-REF`,
outside the loop), `z_peak`/`f_peak`, `dip_mv`, `t_settle`.

**10 µF at `VS` is not free.** The crossover margin barely moves, but `|Z_out|`
peaks near `R_ISO` at about 2.5 kHz and a load step swings back through most
of its own dip for about 3 ms. The phase margin cannot see this; the step can.

## How it was made to run

- **The loop break** is `tools/sim.py`'s stated one (1 GH / 1 GF at the
  op-amp input). A series voltage source was tried: it agreed within 0.5° as
  netlisted but not on the bare follower, where 10 kΩ of feedback against the
  model's input capacitance breaks its assumption above 1 MHz.
- **`.options rshunt=1e10`** in every deck with the OPA2197. Without it the
  model's operating point is not found at some corners, and ngspice's last
  resort ("transient op") then reports a false one — `VS` at 0.55 V, every
  measure present. `sim.py` now refuses a run that needed that fallback.
- **The REF5050 is a 5.000 V source in the loop decks.** Its VOUT feeds only
  `U-BUF`'s (+) input; `reference-alone` runs its model and checks the source
  stands for it. A cold start of that model is not simulated: its transient
  from 0 V aborts under ngspice 42 (`ref-startup.cir` says how).
- `D-REF-CLAMP` is left out: it draws leakage at the rail.

## What a result is worth

**A simulated phase margin is a screen with a ±10° bar, not a spec.** TI's
macromodel runs optimistic against TI's own tabulated figures. It either agrees
with the bench at E13 or tells you where to look.
