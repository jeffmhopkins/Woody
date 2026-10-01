# The system — one deck, instrument to module

`sims.yaml` says what is simulated and what every run must show; `system.lib`
is the circuit (one subcircuit, `SYS`), `cable.lib` the umbilical, and
`led.cir`, `burst.cir`, `plug.cir` and `cable.cir` the scenarios;
`results.yaml` is **generated** by
`python3 tools/sim.py run hardware/interfaces/system/sim` (long: background
it). `docs/reference/tooling.md` §5 explains the tool.

This is not a circuit and has no netlist of its own. It is every circuit the
instrument's supply, the breath signal and the SPI link cross, joined as the
corpus joins them: the rack, `module/power-entry` (with `U-ISO`),
`module/umbilical-load-switch`, the panel LED, the umbilical with all eight
conductors, `carrier/power-entry-instrument` (with `Q-INRUSH`),
`carrier/led-strip-drive`'s row, `carrier/breath-excitation-reference`,
`interfaces/breath-sense-link`, the carrier's SPI pads,
`module/digital-and-supervision`'s receiver and level shifter,
`module/breath-receive-stage`, `module/breath-response-shaper`,
`module/breath-output-stage`, `module/pitch-stage` and
`module/mod-channels`.

**No part value is written here.** Every part is `{{ROW}}` or `{{ref}}` from
the fourteen netlists `sims.yaml` lists (the LED row's size is
`n:D-LED`, counted off `carrier/led-strip-drive`'s netlist). Every model
parameter is imported from the sim that owns it (`params_from:` — the rack's
copper and `U-ISO`'s input filter from `module/power-entry/sim`, the LT1641
from `umbilical-load-switch/sim`, `Q-INRUSH` and the buck from
`power-entry-instrument/sim`, the cable and the pads from `spi-link/sim`, the
diode fits from `breath-response-shaper/sim` and `panel-led/sim`, the TVS
fit from `breath-sense-link/sim`); what this directory adds is in its own
`params:`, each with its source.
