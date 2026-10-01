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
| `offset[p_off=…]` | breath at rest, `POT-OFFSET` at CCW, centre, the page's zero (p = 0.432) and CW | −4.89, +0.61, 0.00 and +5.06 V at the nominal — clockwise positive, as the panel's `+` says: **the page's table to 1 mV**, its wiper-impedance term included. The 1 % resistors and the rail's window move each point by up to ±0.8 V, which the knob absorbs |
| `gain[p_gain=…]` | a 1 V breath step at the gain knob's ends and noon | 0.503×, 2.156× and 4.020× (`R-BREATH-FB`/`R-BREATH-IN` is 4.02, not 4) |
| `clip` | offset +5 V, gain 4×, a hard blow | stops at **+11.89 V** on the deck's ideal +12.0 V rail: a hard wall, as the page says. Its "about ±11.5 V" is the same clip on the module's rails less their Schottky drops |
| `step-mult`, `loop` | a hard-blow step and the summer's loop, into a module input and passive mults to the PITCH and a MOD jack | no overshoot (under 0.03 %) at any load; phase margin 95.6° at every load |
| `rail` | the −12 V rail's movement, through `R-BREATH-OFFNEG` | 0.418 V/V: **4.05 mV at the jack** for ADR 0027's 9.7 mV, the page's 4.1 mV |
| `chain-centre` | the response shaper and this stage together, `POT-RESP` at its click, GAIN at noon, OFFSET at its zero | a hard blow reaches **9.99 V**; `BREATH_OUT` clips from an in-amp output of −5.54 V, 1.19× a hard blow |
| `chain[p_resp=…]` | the same with GAIN left at noon and the curve knob at CCW, ¼, centre, ¾ and CW | see below: `breath-chain-curve-clip` |

## The curve knob after commissioning — `chain`

The shaper's own sim stops at `BREATH_SHAPED`. One stage later, with GAIN where
commissioning leaves it (noon, 2.156×) and the in-amp ramped to full scale,
nominal parts, `BREATH_OUT` (the op-amp output; the jack is 1 % lower into
100 kΩ):

| `POT-RESP` | Shaper at a hard blow | `BREATH_OUT` at a hard blow | Clips from an in-amp output of |
|---|---|---|---|
| CCW (log) | 0.436× | 4.36 V | does not clip (about 7.7 V at full scale) |
| ¼ | 0.834× | 8.34 V | −6.84 V, 1.47× a hard blow |
| centre click | 0.999× | 9.99 V | −5.54 V, 1.19× |
| ¾ | 1.096× | 10.97 V | −5.02 V, 1.08× |
| CW (exp) | 1.641× | 11.97 V (on the rail) | **−3.51 V, 0.76× — inside real playing** |

A hard blow is the in-amp's −4.64 V, the 2.8 kPa candidate of the disputed
`breath-working-point`. The clip is on the deck's ideal ±12 V; the module's
rails, a Schottky drop lower, clip a little earlier.

## In the register

This README owns, in `config/figures.yaml`:

- `breath-chain-curve-clip`: with GAIN at noon, `POT-RESP` fully clockwise clips `BREATH_OUT` from an in-amp output of −3.51 V, 0.76× a hard blow; at the centre click from −5.54 V, 1.19×

## What a result is worth

A screen against TI's macromodel. `D-JACK-CLAMP` is left out (reverse-biased
inside the rails). The loop is broken by THE STATED BREAK (a) at the summer's
(−) input.
