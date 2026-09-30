# Breath output stage — simulation

`sims.yaml` says what is simulated and what every run must show; `bos.cir`
(transient) and `bos-ac.cir` (the loop, and the −12 V rail's path to the jack)
are the decks; `results.yaml` is **generated** by
`python3 tools/sim.py run hardware/module/breath-output-stage/sim`.
`docs/reference/tooling.md` §5 explains the tool.

**No part value is written here.** The decks read this circuit's netlist and,
for a passive mult, the pitch and mod jacks' parts. Both halves are TI's
OPA2197 model. `DAC_AVDD` is `dac-rail`, cited, varied over the C grade's
5.00–5.50 V window. Each pot is two resistors about its wiper.

## What it shows

| Sim | What | Result |
|---|---|---|
| `offset[p_off=…]` | breath at rest, `POT-OFFSET` at CCW, centre, the page's zero (p = 0.567) and CW | +5.06, +0.61, 0.00 and −4.91 V at the nominal: **the page's table to 1 mV**, its wiper-impedance term included. The 1 % resistors and the rail's window move each point by up to ±0.8 V, which the knob absorbs |
| `gain[p_gain=…]` | a 1 V breath step at the gain knob's ends and noon | 0.503×, 2.156× and 4.020× (`R-BREATH-FB`/`R-BREATH-IN` is 4.02, not 4) |
| `clip` | offset +5 V, gain 4×, a hard blow | stops at **+11.89 V** on the deck's ideal +12.0 V rail: a hard wall, as the page says. Its "about ±11.5 V" is the same clip on the module's rails less their Schottky drops |
| `step-mult`, `loop` | a hard-blow step and the summer's loop, into a module input and passive mults to the PITCH and a MOD jack | no overshoot (under 0.03 %) at any load; phase margin 95.6° at every load |
| `rail` | the −12 V rail's movement, through `R-BREATH-OFFNEG` | 0.418 V/V: **4.05 mV at the jack** for ADR 0027's 9.7 mV, the page's 4.1 mV |

## What a result is worth

A screen against TI's macromodel. `D-JACK-CLAMP` is left out (reverse-biased
inside the rails). The loop is broken by THE STATED BREAK (a) at the summer's
(−) input.
