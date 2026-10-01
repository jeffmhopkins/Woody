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
1.477× at the worst corner at its own 0.715 V-at-1 mA limit. **Temperature
is a corner** (ngspice's `temp`: the diode moves by the SPICE defaults, an
assumption; the sheet gives no tempco). The in-amp's output is swept from 0 V
to `inamp-full-scale` as a slow ramp.

**`TRIM-RESP` is commissioned in the deck.** With `trimmed: 1`, `shaper.cir`
does the builder's step before it measures: `POT-RESP` fully clockwise, at the
workshop's temperature `t_comm`, it bisects the trimmer between its end
resistance and its whole track until a hard blow gives the target `g_trim`,
then runs the sim's own setting. So every corner is trimmed the way a real unit
would be, and what the sims assert is what the built module does.

## What it shows

`R-RESP` is 2.7 kΩ with `TRIM-RESP` (10 kΩ, ±10 %) in series, set at
commissioning to **1.55×** at a hard blow at the fully-exponential end (`g_trim`
in `sims.yaml`; the owner's floor is 1.5×, *"need 1.5x gain"*, 2026-09-30, and
the margin is what 0 °C takes from a unit trimmed warm). The stage's gain ratio,
`BREATH_SHAPED` over the in-amp's output (1 is the linear stage), at the page's
table's points, trimmed at 22 °C and run at 27 °C, nominal diode:

| In-amp | Page's table (CW, 15 kΩ, unloaded) | **CW, fully exp** | **Centre** | **CCW, fully log** |
|---|---|---|---|---|
| *pp* 1.00 V | 1.000 | 1.11 | 1.000 | 0.83 |
| *mp* 2.50 V | 1.347 | 1.42 | 1.000 | 0.59 |
| *mf* 3.50 V | 1.440 | 1.50 | 1.000 | 0.53 |
| hard blow 4.64 V | 1.494 | **1.55** | 0.999 | 0.49 |
| full scale | 1.586 | clipped at −11.95 V | 0.991 | 0.42 |

| Sim | Holds |
|---|---|
| `exp-end-trimmed` | **the built module.** Trimmed at a 15 °C and at a 30 °C workshop, at every one of 256 corners (the diode's spread, the 1 % resistors that set the drive, `POT-RESP`'s track at ±20 % — the RV09 sheet gives none, an assumption — and `TRIM-RESP`'s at ±10 %): the bisection **reaches 1.55× within 0.0002 everywhere**, so the target is reachable at every corner; at **0 °C** the gain is **1.52× at the worst** (trimmed at 30 °C; 1.53× trimmed at 15 °C) — the 1.5× floor holds; at 40 °C it is 1.56–1.58×, and `BREATH_SHAPED` clips from an in-amp output of −7.19 V at the worst corner (−7.28 V nominal, trimmed at 15 °C), 1.55× a hard blow. The trimmer ends up between 0.77 kΩ and 4.62 kΩ of its track |
| `exp-end-trim-cw` | `TRIM-RESP` at its clockwise end (its end resistance only), untrimmed: at least **1.56×** at every corner at 15 °C, so the target is reachable from any workshop at 15 °C or warmer; 1.55× at the worst corner at 0 °C. The strongest bend the trimmer allows clips `BREATH_SHAPED` from −6.16 V at the worst corner at 40 °C, **1.33× a hard blow**: past 1.3× everywhere, so a trimmer turned fully clockwise cannot put the shaper's own clip inside real playing |
| `exp-end-trim-ccw` | its counter-clockwise end, the whole track in series, at a 30 °C workshop: **1.24–1.45×**, 1.34× nominal — under the target everywhere, so every unit can be brought down to it; and this is what an **open wiper** gives: a gentler expansive curve, never a runaway |
| `centre` | +1 within the four 1 % resistors' ±2 % at the detent (0.978–1.020 at a hard blow), and linear across real playing within 0.3 % at every corner |

## What it says that the page's table does not

- **The curve is weaker than the table's arithmetic.** The table computes the
  diode branch from a node at exactly `V_in/2`. On the netlist that node is the
  `R-RESP-DIV` pair's midpoint, a 5 kΩ source, and `POT-RESP`'s 50 kΩ track
  from it to `V_shaped` (−`V_in`/2) loads it to 0.41 `V_in` at the CW end
  `[calc: 0.5 − 5k × 1.0/55k]`. That is why the branch is 2.7–12.7 kΩ rather
  than the table's 15 kΩ, and why the curve is not "exactly linear" below the knee: at
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

- `shaper-exp-gain`: trimmed at commissioning to 1.55x at a hard blow; at every corner at least 1.52x at 0 C and at most 1.58x at 40 C; clips from an in-amp output of -7.28 V nominal, -7.19 V at the worst corner

## What a result is worth

A screen: the diode is fitted, not a vendor model, and its emission
coefficient is assumed. The gain ratios are robust to it (the table above
moves by about 0.03); the conclusions about the divider's loading are
arithmetic the run confirms.
