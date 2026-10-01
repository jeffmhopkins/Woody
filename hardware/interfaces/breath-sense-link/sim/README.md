# Breath sense link — simulation

`sims.yaml` says what is simulated and what every run must show; `tvs.cir` is
the deck; `results.yaml` is what the last run found, **generated** by
`python3 tools/sim.py run hardware/interfaces/breath-sense-link/sim`.
`python3 tools/sim.py show <this dir>` prints it as a table.
`docs/reference/tooling.md` §5 explains the tool.

**The link's CMRR is not here.** It is
[`breath-receive-stage/sim`](../../../module/breath-receive-stage/sim/), which
reads this circuit's `R1` and `R1b` and owns the figure `breath-link-cmrr`.
That deck leaves out this circuit's two ESD diodes; this one puts them in, on
the same chain (TI's INA828 and OPA2197 models), and takes its operating point
from that deck's `sims.yaml`.

## What it shows

`D-TVS-BREATH-SIG` and `D-TVS-BREATH-RET`, PESD12VS1UA, each from its leg to
`PWR_GND` at `J-UMB`. Each is 160 pF at 0 V and about half that at 5 V
`[ds NEXPERIA-PESD12VS1UA.pdf Figure 5]`, so the signal leg's, biased at the
sensor's voltage, never matches the return leg's at 0 V. The capacitance is a
junction fitted to the figure; the leakage is the datasheet's 25 °C maximum.

| Sim | What | Holds |
|---|---|---|
| `with-tvs[v_sensor=…]` | as netlisted, the sensor at 1.0, 2.5 and 4.86 V, each diode's capacitance −25 %/+12.5 % on its own, `R1`/`R1b` at their tolerance | the link still clears 58.5 dB at 50 and 60 Hz (the diodes move it by under 0.1 dB there); `PWR_GND` noise reaches the in-amp output at under −60 dB at any frequency to 1 MHz; 100 nA of leakage moves the output by about 0.2 mV |
| `without-tvs[…]` | both diodes out | the same CMRR, for the difference |

Only `R1` and `R1b` vary here (2⁴ corners with the diodes); the full-tolerance
CMRR — every part of the balance — is the receive deck's. The sensor's bottom,
0.265 V, is not run: TI's INA828 model finds no operating point there, and it
is the end where the two diodes match best.

## What it does not show

- **The cable's own capacitance** to the other conductors, which adds to each
  diode's in the same way. The receive deck leaves it out as balanced.
- **Leakage at temperature.** Figure 6 rises about a decade per 40 °C; the
  offset is linear in it and `TRIM-BREATH-ZERO` nulls it at commissioning.
- **A fault on the conductor** — `R1`'s dissipation with the leg at a rail —
  which is `breath-sense-link.md`'s arithmetic.

## What a result is worth

A screen: TI's macromodels and a diode fitted to a typical curve. Layout
asymmetry is not in it.
