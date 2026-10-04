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
| `with-tvs-500[v_sensor=…]`, `-1k5`, `-wide` | as netlisted, in each of the bandwidth toggle's modes (#32, `U-BW-SW` as the receive deck has it), the sensor at 1.0, 2.5 and 4.86 V, each diode's capacitance −25 %/+12.5 % on its own, `R1`/`R1b` at their tolerance | the link still clears 58.5 dB at 50 and 60 Hz in every mode (92.4 dB worst), and at each mode's top (89 dB at 1.5 kHz, 75 dB at 10 kHz: the diodes are not what limits it); 100 nA of leakage moves the output by about 0.2 mV. **`PWR_GND` rejection now FAILS its old bound** — below |
| `without-tvs[…]` | both diodes out, WIDE | the same CMRR, for the difference |

**`PWR_GND` noise reaches the in-amp's output more than it did (#32), for the
owner.** Until #32 every mode-less run held it under 1/1000 (−60 dB) at every
frequency to 1 MHz. Two things changed it, and both are the bandwidth's price:

- **Above the band:** with `C_cm` at 68 pF the common-mode pole is ~213 kHz,
  not ~9.6 kHz, so from ~70 kHz to 1 MHz the worst corner reaches **0.0091**
  (500 Hz mode), **0.011** (1.5 kHz) and **0.016** (WIDE) — about −36 to −41 dB.
- **Inside the band:** the diodes' own mismatch (100–160 pF behind 1 kΩ)
  converts `PWR_GND` noise to differential in proportion to frequency, which
  no receive filter undoes inside its own band. In-band the worst corner is
  **5.6 × 10⁻⁴ to 500 Hz** (still under the old bound), **1.8 × 10⁻³ to
  1.5 kHz** and **1.2 × 10⁻² to 10 kHz** (`pg_band_*`).

What reaches the *jack* is `interfaces/system/sim`'s, which runs the LED row
and the SPI frames on `PWR_GND` end to end in WIDE; the bound here was not
moved, and the assertion is left failing for the owner's decision (#32). If
the in-band term matters, the cheap lever is the diodes' match: a
lower-capacitance part on both legs shrinks it in proportion.

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
