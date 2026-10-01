# Digital path — simulation

`sims.yaml` says what is simulated and what every run must show; `seq.cir` is
the deck; `results.yaml` is what the last run found, **generated** by
`python3 tools/sim.py run hardware/module/digital-and-supervision/sim`.
`python3 tools/sim.py show <this dir>` prints it as a table.
`docs/reference/tooling.md` §5 explains the tool.

**No part value is written here.** The deck reads three netlists —
`module/power-entry` (both regulators), this circuit (the pulls and the
receiver's RC) and `module/dac8568` — and takes the bus, the 1N5817 fit and the
module's loads from `power-entry/sim/sims.yaml` (`params_from`).

The link's signals — `SCLK`, `MOSI` and `CS_MOD` over the umbilical into
`U-RX-MOD` — are not simulated here: they are
[`interfaces/spi-link/sim`](../../../interfaces/spi-link/sim/).

## What it shows

Rack power-on and power-off at the module: `LOGIC_5V` (`U-REG-LOGIC`) against
`DAC_AVDD` (`U-REG-DAC`, the LT3042, behavioural: `power-entry/sim/lt3042.lib`), and the three pins `U-LVL-MOD`
drives into the DAC8568 — `SYNC`, idle high, and `SCLK_DAC` and `DIN`, held
high as an instrument powered on its own could hold them.

| Sim | What | Holds |
|---|---|---|
| `rails-and-sync` | as netlisted: `U-LVL-MOD` on `DAC_AVDD` | both rails settle where their pages say; **`SYNC`, `SCLK_DAC` and `DIN` each stay at or under `DAC_AVDD + 0.3 V` at every instant of power-on and power-off, at every corner** — the requirement, below; no DAC input's clamp conducts; `U-LVL-MOD`'s inputs stay inside its rating; `LOGIC_5V` still arrives first |
| `what-if-lvl-on-logic-5v` | `U-LVL-MOD`'s `VCC` moved back to `LOGIC_5V` | the same measures fail: every pin it drives high sits over `AVDD + 0.3 V` at power-on — kept so the requirement is seen to bite |

## The requirement, and how it was met (2026-10-01)

The DAC8568: *"No device pin should be brought high before power is applied to
the device"* `[ds DAC8568CIPW.pdf p.31]`; a digital input's absolute maximum is
`AVDD + 0.3 V` `[p.2]`. The ADP7118's 380 µs soft start puts `LOGIC_5V` up
within about a millisecond of the bus, while `U-REG-DAC`, soft-started by
`R-SET-DAC` × `C-SET-DAC` (~5 ms), takes several; at power-off its 0.3 V
dropout against the ADP7118's 60 mV, on a higher output, lets `DAC_AVDD` fall
first. *(Until 2026-10-01 `U-REG-DAC` was an LM317L, slowed by its `ADJ`
capacitor, with a 1.7 V larger dropout: the same order, and the requirement
below never depended on it.)*

This sim first ran with `U-LVL-MOD` on `LOGIC_5V`, as the sheet then had it,
and recorded the result as an open finding: `SYNC` driven up to about 3.4 V
over `AVDD` for most of 10 ms at power-on, feeding `DAC_AVDD` through the
pin's power clamp at 10–17 mA, and about 1.2 V over at power-off. It set out
three options: supply the buffer from `DAC_AVDD`; series resistors at the DAC's
inputs (the current fell under a milliamp, the pin stayed about 1 V over
`AVDD`, which the datasheet does not allow); or sequence the regulators (fixes
power-on only). The owner chose the first — *"go with option 1"* — and the
sheet now has it. The finding's assertion became the requirement above;
`what-if-lvl-on-logic-5v` reproduces the old wiring and fails it. The numbers
are `results.yaml`'s.

The 74AHCT125's inputs, from `U-RX-MOD` on `LOGIC_5V`, sit above its `VCC`
while `DAC_AVDD` is low. That is in its rating — no input clamp to `VCC`
`[ds SN74AHCT125.pdf p.3, p.4]` — and the deck holds `LOGIC_5V` under the
5.5 V `VI` maximum throughout.

## What a result is worth

`U-LVL-MOD` is TI's behavioural SPICE model of the SN74AHCT125 (banked,
`datasheets/logic/`), with the output clamp to `VCC` the datasheet's `I_OK`
row implies and the model leaves out. Its `VCC` is a source that follows
`DAC_AVDD`, with the current its outputs source into the two pull-downs drawn
from that rail explicitly: TI's model would not converge with its `VCC` on the
rail through a resistance, nor with its own current fed back; it also needs
looser solver settings (`gmin`, `itl4`, `reltol`, in the deck) while its `VCC`
is under a volt with its input high, and on the old wiring it does not finish at
the slow soft-start corner, so `what-if-lvl-on-logic-5v` varies the clamp only.
Each DAC input is its pin capacitance and the
`[POWER Clamp]` table of TI's IBIS model, its typical column, varied ±20 % for
the other two (`datasheets/analog/DAC8568-ti-ibis-sbam030.ibs`); TI publishes
no SPICE model for the DAC. The ADP7118 and the 74AHCT14 are **behavioural**,
built from their banked datasheets: TI's own 74AHCT14 model is banked too but
not used, because it is the family's generic model with CMOS thresholds, not
this part's TTL ones. The ADP7118 model's UVLO has no hysteresis, which keeps
`LOGIC_5V` up slightly longer at power-off than the part would. A
simulated transient is a screen, not a spec: the bench is where the two rails
and `SYNC` are scoped together.
