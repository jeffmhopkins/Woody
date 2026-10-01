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
to the main board's `AGND_MOD` through `J-LED-PANEL` (the LED is a panel-mount
indicator on a lead, ADR 0024 point 16, so its current does not cross
`J-B2B-MOD`), with the instrument's breath-following current drawn through
the same switch.

| Sim | Holds |
|---|---|
| `led[i_swing=…]` | 4.1–4.5 mA across the two catalogues' V_F (3.8–4.8 mA with `U-ISO`'s ±3.1 % and the resistor's 1 % as well); the LED reaches 0.1 mA as the output passes 1.8–3.2 V; its current follows the breath by under 10 µA p-p |

So `panel-led.md`'s 4.1–4.5 mA and "2–3 V" hold, and `power-entry.md`'s
"constant" for the LED's share of `NT-DIG-MOD` holds to the precision ADR 0027
asks of the instrument's own current.

## What a result is worth

The LED is a diode with a GaP green junction's curve, kept from the previous
LED, shifted across the two catalogues' V_F (the Dialight 605's pages give one
typical point each and no curve); the
switch is its two resistances. `U-ISO`'s load regulation
(0.1 %) is left out: it would roughly double the LED's breath-following
current.
