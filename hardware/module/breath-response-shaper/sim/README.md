# Breath response shaper — simulation

`sims.yaml` says what is simulated and what every run must show; `shaper.cir`
is the deck; `results.yaml` is **generated** by
`python3 tools/sim.py run hardware/module/breath-response-shaper/sim`.
`docs/reference/tooling.md` §5 explains the tool.

**No part value is written here.** The deck reads this circuit's netlist; both
halves of `U-RESP` are TI's OPA2197 model. **`D-RESP` is behavioural**: no
1N4148W SPICE model could be banked (fragment R38 records the URLs tried), so
it is a SPICE diode fitted to the banked sheets — the 1N4448W's guaranteed
0.62–0.72 V at 5 mA sets its saturation current, swept across that window, and
its emission coefficient (1.8) is an assumption. The in-amp's output is swept
from 0 V to `inamp-full-scale` as a slow ramp.

## What it shows

The stage's gain ratio, `BREATH_SHAPED` over the in-amp's output (1 is the
linear stage), at the page's table's points:

| In-amp | Page's table (CW) | **CW, fully exp** | **Centre** | **CCW, fully log** |
|---|---|---|---|---|
| *pp* 1.00 V | 1.000 | 1.07 | 1.000 | 0.88 |
| *mp* 2.50 V | 1.347 | 1.23 | 1.000 | 0.74 |
| *mf* 3.50 V | 1.440 | 1.27 | 0.999 | 0.70 |
| hard blow 4.64 V | 1.494 | **1.30** | 0.999 | 0.68 |
| full scale | 1.586 | clipped at −11.95 V | 0.993 | 0.64 |

(nominal diode; its spread moves the CW column by about ±0.02.)

| Sim | Holds |
|---|---|
| `centre` | +1 within the four 1 % resistors' ±2 % at the detent (0.978–1.020 at a hard blow), and linear across real playing within 0.25 % at every corner |
| `clip` | at the fully-exponential end the output clips from an in-amp output of **−8.86 V** (−8.82 to −8.89 V over the diode's spread) |

## What it says that the page does not

- **The curve is weaker than the table.** The table computes the diode branch
  from a node at exactly `V_in/2`. On the netlist that node is the
  `R-RESP-DIV` pair's midpoint, a 5 kΩ source, and `POT-RESP`'s 50 kΩ track
  from it to `V_shaped` (−`V_in`/2) loads it to 0.41 `V_in` at the CW end
  `[calc: 0.5 − 5k × 1.0/55k]`. At a hard blow the fully-exponential gain is
  **1.30×, not ~1.5×**, and it is not "exactly linear" below the knee: at *pp*
  the diode already carries enough to make it 1.07×. Getting 1.5× at a hard
  blow from this network takes `R-RESP` near 7 kΩ (8.2 kΩ gives 1.44×, run by
  hand); `R-RESP` is E10's decision, and this is what that decision starts
  from.
- **The clip starts at −8.9 V, not −7.4 V**, for the same reason: still inside
  the sensor's range and beyond real playing, so the page's conclusion stands.
- **The centre detent is linear, not exactly linear.** The same loading means
  the wiper is not at 0 V at `p = 0.5`: it sits at −0.045 `V_in`
  `[calc: (0.409 − 0.5)/2]`, 0.39 V in the run at full scale. The diodes barely conduct
  there (3.5 µA at full scale, 0.2 µA at a hard blow), so the stage stays
  within 0.25 % of linear across real playing and 1.1 % at full scale — but
  the null "set by the topology" is set by the divider's source impedance
  against the pot, and it sits about 5 % of the rotation clockwise of the
  detent `[calc: V_wiper = 0 at 0.45 of the track from CW]`.

## In the register

This README owns, in `config/figures.yaml`:

- `shaper-exp-gain`: 1.30x at a hard blow; clips from an in-amp output of -8.86 V

## What a result is worth

A screen: the diode is fitted, not a vendor model, and its emission
coefficient is assumed. The gain ratios are robust to it (the table above
moves by about 0.02); the conclusions about the divider's loading are
arithmetic the run confirms.
