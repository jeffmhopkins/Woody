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
`DAC_AVDD` (`U-REG-DAC`, TI's LM317L model), and `SYNC` — idle high, driven by
`U-LVL-MOD` from `LOGIC_5V` — at the DAC8568's pin.

| Sim | What | Holds |
|---|---|---|
| `rails-and-sync` | as netlisted, no instrument on the cable | both rails settle where their pages say; **`LOGIC_5V` arrives first, and `SYNC` sits past the DAC's `AVDD + 0.3 V` absolute maximum at power-on and at power-off** — a recorded finding, below |
| `what-if-lvl-on-avdd` | `U-LVL-MOD`'s `VCC` moved to `DAC_AVDD` | `SYNC` stays inside the rating, on and off |
| `what-if-series-2k2` | 2.2 kΩ in series at the DAC's input | the current falls under a milliamp; the pin still sits about 1 V over `AVDD` |

## The finding — open for the owner (2026-10-01)

The DAC8568: *"No device pin should be brought high before power is applied to
the device"* `[ds DAC8568CIPW.pdf p.31]`; a digital input's absolute maximum is
`AVDD + 0.3 V` `[p.2]`. As netlisted, the ADP7118's 380 µs soft start puts
`LOGIC_5V` up within about a millisecond of the bus, while the LM317L, slowed by
`C-REG-ADJ`, takes several. `CS_MOD` is pulled up, so `U-LVL-MOD` drives
`SYNC` high from the first moment it has a supply, and for most of 10 ms the
DAC's `SYNC` pin is driven up to about 3.4 V over `AVDD`, feeding `DAC_AVDD`
through the pin's power clamp at 10–17 mA — limited only by the 74AHCT125's
output and the clamp's own resistance. At power-off the LM317L's 1.7 V larger
dropout lets `DAC_AVDD` fall first and it happens again, about 1.2 V over at
about 2 mA. The numbers are `results.yaml`'s.

This is a design question, not a page error, so nothing is changed. The
options the what-ifs bracket:

1. **Supply `U-LVL-MOD` from `DAC_AVDD`** (`what-if-lvl-on-avdd`): its outputs
   then cannot exceed the DAC's supply, on or off, and the 74AHCT125's inputs
   — no clamp to `VCC` — take the 74AHCT14's 5 V high while `DAC_AVDD` is low.
   A schematic change of one net; it adds the buffer's few milliamps to the
   LM317L, which `power-entry.md` would re-derive.
2. **Series resistors at the DAC's three inputs** (`what-if-series-2k2`):
   holds the current under a milliamp, which most parts' protection
   tolerates, but leaves the pin over `AVDD + 0.3 V`, which the datasheet does
   not allow.
3. **Sequence the regulators** — `U-REG-LOGIC`'s `EN` from a divider on
   `DAC_AVDD` — fixes power-on only: at power-off `DAC_AVDD` still leaves first.
   Not simulated.

## What a result is worth

`U-LVL-MOD` is TI's behavioural SPICE model of the SN74AHCT125 (banked,
`datasheets/logic/`), with the output clamp to `VCC` the datasheet's `I_OK`
row implies and the model leaves out. The DAC's `SYNC` pin is the
`[POWER Clamp]` table of TI's IBIS model, its typical column, varied ±20 % for
the other two (`datasheets/analog/DAC8568-ti-ibis-sbam030.ibs`); TI publishes
no SPICE model for the DAC. The ADP7118 and the 74AHCT14 are **behavioural**,
built from their banked datasheets: TI's own 74AHCT14 model is banked too but
not used, because it is the family's generic model with CMOS thresholds, not
this part's TTL ones. The ADP7118 model's UVLO has no hysteresis, which keeps
`LOGIC_5V` up slightly longer at power-off than the part would. A
simulated transient is a screen, not a spec: the bench is where the two rails
and `SYNC` are scoped together.
