# Panel LED — simulation

`sims.yaml` says what is simulated and what every run must show; `led.cir` is
the deck; `results.yaml` is what the last run found, **generated** by
`python3 tools/sim.py run hardware/module/panel-led/sim`.
`python3 tools/sim.py show <this dir>` prints it as a table.
`docs/reference/tooling.md` §5 explains the tool.

**No part value is written here.** The deck reads this circuit's netlist
(`R-LED-PANEL`) and `module/umbilical-load-switch`'s (`R-ILIM`); the
instrument's current and the breath are `power-entry/sim`'s (`params_from`).

## What it shows

`R-LED-PANEL` and `LED-PANEL` on `UMBILICAL_POS12`, the load switch's output —
**not** the −12 V rail, and not the analog +12 V since 2026-09-30 — returning
to `AGND_MOD` across `J-B2B-MOD`'s five ground pins, with the instrument's
breath-following current drawn through the same switch.

| Sim | Holds |
|---|---|
| `led[i_swing=…]` | about 4.5 mA (4.1–4.8 mA over `U-ISO`'s ±3.1 %, the resistor and the LED's whole V_F spread); the LED reaches 0.1 mA as the output passes 1.9–2.5 V; its current follows the breath by under 10 µA p-p, which moves the jack board's ground against the pitch stage's by about 0.1 µV — ten-thousandths of a cent |

So `panel-led.md`'s 4.5 mA and "about 2 V" hold, and `power-entry.md`'s
"constant" for the LED's share of `NT-DIG-MOD` holds to the precision ADR 0027
asks of the instrument's own current.

## What a result is worth

The LED is a diode fitted to its datasheet's typical curve, shifted across the
table's V_F; the switch is its two resistances; `J-B2B-MOD`'s contact
resistance is an estimate, varied to three times. `U-ISO`'s load regulation
(0.1 %) is left out: it would roughly double the LED's breath-following
current, still four orders of magnitude under the bar.
