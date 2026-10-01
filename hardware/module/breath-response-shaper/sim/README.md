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
its emission coefficient (1.8) is an assumption. **The 1N4448W is the part
bought** (since 2026-10-01): a 1N4148W, which guarantees only a maximum, gave
1.477× at the worst corner at its own 0.715 V-at-1 mA limit. The runs are at
27 °C; the knee moves up as the module cools, and the worst corner is 1.496×
at 15 °C (`shaper-exp-gain`, its `diode_note`). The in-amp's output is swept
from 0 V to `inamp-full-scale` as a slow ramp.

## What it shows

`R-RESP` is 3.9 kΩ (owner, 2026-09-30: *"need 1.5x gain"* at a hard blow).
The stage's gain ratio, `BREATH_SHAPED` over the in-amp's output (1 is the
linear stage), at the page's table's points, nominal diode (its spread moves
the CW column by about ±0.03):

| In-amp | Page's table (CW, 15 kΩ, unloaded) | **CW, fully exp** | **Centre** | **CCW, fully log** |
|---|---|---|---|---|
| *pp* 1.00 V | 1.000 | 1.11 | 1.000 | 0.82 |
| *mp* 2.50 V | 1.347 | 1.48 | 1.000 | 0.55 |
| *mf* 3.50 V | 1.440 | 1.58 | 1.000 | 0.48 |
| hard blow 4.64 V | 1.494 | **1.64** | 0.999 | 0.44 |
| full scale | 1.586 | clipped at −11.95 V | 0.991 | 0.36 |

| Sim | Holds |
|---|---|
| `exp-end` | **at least 1.5× at a hard blow at every one of 513 corners** — 1.64× nominal, 1.51× at the worst: the diode's spread, every resistor at its 1 % ends and `POT-RESP`'s track at ±20 % (the RV09 sheet gives no tolerance; ±20 % is an assumption). The worst corner is the pot low and the stage's linear gain low. The output clips from an in-amp output of **−6.95 V** nominal, −6.51 V at the worst corner — past 1.3× a hard blow everywhere (`shaper-exp-gain`) |
| `centre` | +1 within the four 1 % resistors' ±2 % at the detent (0.978–1.020 at a hard blow), and linear across real playing within 0.3 % at every corner |

The E24 value above, 4.3 kΩ, gives 1.49× at the worst corner (run by hand
with the same corners, 2026-09-30); 3.9 kΩ is the largest that holds 1.5×.

## What it says that the page's table does not

- **The curve is weaker than the table's arithmetic.** The table computes the
  diode branch from a node at exactly `V_in/2`. On the netlist that node is the
  `R-RESP-DIV` pair's midpoint, a 5 kΩ source, and `POT-RESP`'s 50 kΩ track
  from it to `V_shaped` (−`V_in`/2) loads it to 0.41 `V_in` at the CW end
  `[calc: 0.5 − 5k × 1.0/55k]`. That is why `R-RESP` is 3.9 kΩ rather than the
  table's 15 kΩ, and why the curve is not "exactly linear" below the knee: at
  *pp* the diode already carries enough to make it 1.11×.
- **The clip starts earlier with a stronger curve**: still past 1.3× a hard
  blow and inside the sensor's range, so beyond real playing.
- **The centre detent is linear, not exactly linear.** The same loading means
  the wiper is not at 0 V at `p = 0.5`: it sits at −0.045 `V_in`
  `[calc: (0.409 − 0.5)/2]`, 0.36 V in the run at full scale. The diodes barely
  conduct there (5 µA at full scale, 0.2 µA at a hard blow), so the stage stays
  within 0.3 % of linear across real playing and 1.5 % at full scale — but
  the null "set by the topology" is set by the divider's source impedance
  against the pot, and it sits about 5 % of the rotation clockwise of the
  detent `[calc: V_wiper = 0 at 0.45 of the track from CW]`.

## In the register

This README owns, in `config/figures.yaml`:

- `shaper-exp-gain`: 1.64x at a hard blow, 1.51x at the worst corner; clips from an in-amp output of -6.95 V, -6.51 V at the worst corner

## What a result is worth

A screen: the diode is fitted, not a vendor model, and its emission
coefficient is assumed. The gain ratios are robust to it (the table above
moves by about 0.03); the conclusions about the divider's loading are
arithmetic the run confirms.
