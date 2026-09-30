# Module power entry — simulation

`sims.yaml` says what is simulated and what every run must show; `poweron.cir`
is the deck; `results.yaml` is what the last run found, **generated** by
`python3 tools/sim.py run hardware/module/power-entry/sim`.
`python3 tools/sim.py show <this dir>` prints it as a table.
`docs/reference/tooling.md` §5 explains the tool.

**No part value is written here.** The deck reads this circuit's netlist and
`module/pitch-stage`'s, because the claims being checked are about what the
pitch jack does while this circuit's rails arrive.

## What it shows

Rack power-on, every node starting at 0 V: the bus rails rising at
`J-PWR-EURO`, `D1`/`D3`, the beads as their DC resistance, the bulk capacitors,
the LM317L making `DAC_AVDD` (TI's transient model,
`datasheets/discrete-and-power/LM317L-ti-pspice-snvmaw3.lib`), and the pitch
stage on those rails with the DAC at its power-on-reset zero scale.

| Sim | What | Holds |
|---|---|---|
| `as-netlisted[dt_neg=…]` | the rails, `DAC_AVDD` and the pitch jack, the −12 V rail arriving 1 ms early, together, and 5 ms late | `DAC_AVDD` settles at or above `dac-rail`'s hard floor and never reaches the DAC8568's 6 V absolute maximum; the pitch jack stays within 100 mV of 0 V throughout |
| `d3-reversed` | a what-if: `D3` fitted with its anode at the bus | `MODULE_ANALOG_NEG12` never arrives |

**`D3` must have its cathode at the bus.** The rail it passes flows out of the
module into the bus's −12 V, so a diode with its anode at the bus is
reverse-biased by it: the module's −12 V node then sits at about +0.3 V
(leakage and the loads), and every op-amp on it runs single-supply. This run
found the sheet drawn that way; the sheet was corrected on 2026-09-30, and
`d3-reversed` keeps the failure on record. **The deck types `D3`'s orientation
(`d3_flip`) rather than reading it from the netlist**, so a change to `D3` on
the sheet must be mirrored in `sims.yaml`.

## What it does not show

- **What `VREFOUT` does before firmware enables the reference.**
  `pitch-stage.md` says it is 0 V, so the jack sits at 0 V. The DAC8568's
  datasheet says the internal reference is disabled by default and the pin is
  then `VREFIN`, an input. The deck holds it at 0 V, which is the page's claim,
  not a finding; what a disabled reference pin presents to `TRIM-OFFSET` is
  open until the bench (E9) or a model of the pin says.
- The DAC's outputs before its own power-on reset has run: the deck holds the
  channel at zero scale from the start. `R-BIAS-DAC` is what the page relies on
  for that window.

## What a result is worth

The 1N5817 has no banked vendor model (fragment R29 records the URLs that
failed): it is a diode fitted to the two points the `D-REVPOL` row reads off
the banked curve, and `sims.yaml` shows the arithmetic. Loads are stated
assumptions. **A simulated transient is a screen, not a spec**: it either
agrees with the bench or tells you where to look.
