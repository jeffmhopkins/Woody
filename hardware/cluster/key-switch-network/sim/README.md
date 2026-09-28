# Key switch network — simulation

`sims.yaml` says what is simulated and what every run must show; `key-network.cir`
and `key-network-ac.cir` are the decks; `results.yaml` is what the last run found,
**generated** by `python3 tools/sim.py run hardware/cluster/key-switch-network/sim`.
`python3 tools/sim.py show` prints it as a table. `docs/reference/tooling.md` §5
explains the tool.

**No part value is written here.** Each deck's double-braced names are filled
from `../netlist.yaml`, which is exported from the sheet, so a changed value
reaches the simulation. Until the simulation is re-run, `check-staleness.py`
fails: `results.yaml` hashes every input, the netlist included.

## What it shows

One key's node, from the 3V3 rail through `R-KEY-PU`, with `C-KEY`, `R-KEY-SER`
and the switch, into one SN74HCS165 input. It is run at the nominal and at every
corner of the parts' tolerances, the rail, and the input leakage's sign
(33 runs per sim).

| Sim | Measures | Holds |
|---|---|---|
| `press-and-release` | the press to VT− min, the release to VT+ max and VT+ min, the pressed and released node, the static and peak contact current | the page's two crossing figures (`key-press-time`, `key-release-time`) within 1 %; a press under a tenth of `scan-period`, and a release inside one, at every corner; a pressed key below VT− min and a released one above VT+ max at every corner; `key-scan-current` per key |
| `filter-response` | the released node's pole, and its gain at 800 kHz | the page's *Pole* row: a single pole at 1/(2π·R-KEY-PU·C-KEY), and its rejection at 800 kHz |

The measures without an assertion are recorded for the page's own arguments:
- `t_rel_earliest`, at its minimum, is the longest contact opening that is always swallowed.
- `i_peak` is the press transient into the contact.

## What a result is worth

- **The register is modelled as its inputs.** Its thresholds are the datasheet's
  extreme ratios, applied as measures (`params:`), so a pass means the network
  meets those bounds. It is not a model's opinion of the part.
- **The switch is two resistances**: its contact and insulation figures. It has
  no bounce; the firmware's release window handles bounce.
- **`vcc`'s ±3 % is a placeholder** until the LDO's datasheet is banked. The
  network is a divider and every threshold is a fraction of VCC, so the rail
  moves only the leakage and contact terms.
