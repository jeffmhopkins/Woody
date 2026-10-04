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

`D-TVS-BREATH-SIG` and `D-TVS-BREATH-RET`, **PESD12VL1BA since #32** (the
PESD12VS1UA before it), each from its leg to `PWR_GND` at `J-UMB`. Each is
19 pF at 0 V and about 13.7 pF at 4 V `[ds NEXPERIA-PESDXL1BA-SER.pdf p.5,
Fig 6]`, so the signal leg's, biased at the sensor's voltage, never matches the
return leg's at 0 V. The capacitance is a junction fitted to Fig 6; the leakage
is the datasheet's 25 °C maximum, 50 nA. The datasheet gives only a typical
capacitance, so each diode is varied ±25 % on its own.

| Sim | What | Holds |
|---|---|---|
| `with-tvs-500[v_sensor=…]`, `-1k5`, `-wide` | as netlisted, in each of the bandwidth toggle's modes (`U-BW-SW` as the receive deck has it), the sensor at 1.0, 2.5 and 4.86 V, each diode ±25 %, `R1`/`R1b` at their tolerance | 58.5 dB at 50 and 60 Hz in every mode (92.4 dB worst); `PWR_GND` to the in-amp output under −60 dB **inside the 500 Hz and 1.5 kHz modes' bands** (6.7 × 10⁻⁵ and 2.1 × 10⁻⁴ worst); WIDE as accepted, below; 50 nA of leakage moves the output by 0.11 mV |
| `without-tvs[…]` | both diodes out, WIDE | the same CMRR, for the difference |

**The owner's decision, 2026-10-04 (#32): *"Accept (Recommended)"*,** offered
as *"The end-to-end simulation holds the output jack within limits in the
500 Hz mode. In wide mode it's about 4× better with a lower-capacitance diode,
so take that too if wide stays at 10 kHz."* (ADR 0003, *The owner's three
answers*). WIDE stays at 10 kHz, so the diode changed. What was measured:

| `PWR_GND` → in-amp output, worst corner | PESD12VS1UA (160 pF) | PESD12VL1BA (19 pF) |
|---|---|---|
| inside 500 Hz | 5.6 × 10⁻⁴ | 6.7 × 10⁻⁵ |
| inside 1.5 kHz | 1.8 × 10⁻³ | 2.1 × 10⁻⁴ |
| WIDE, DC–7 kHz (its requirement band, owner) | — | **1.09 × 10⁻³** |
| WIDE, DC–10 kHz | 1.2 × 10⁻² | 1.38 × 10⁻³ |
| out of band peak, ~70 kHz–1 MHz | 9.1–16 × 10⁻³ | 1.7–2.4 × 10⁻³ |

- **The −60 dB bound now applies inside each mode's band**, and the 500 Hz and
  1.5 kHz modes meet it by a factor of 5 or more. Below each band's edge the
  diodes' own mismatch converts `PWR_GND` noise in proportion to frequency,
  which no receive filter undoes inside its own band.
- **WIDE is the accepted exception**: 1.09 × 10⁻³ at the worst corner inside
  DC–7 kHz, a hair over the −60 dB bound and well under the 1.9 × 10⁻³ the
  owner was shown for the lower-capacitance diode. The assertion holds it under
  that accepted figure, so a worse part cannot slip in; it is not the −60 dB bar.
- **Out of band the peak is recorded, not held**: with `C_cm` at 68 pF the
  common-mode pole is ~213 kHz, not ~9.6 kHz, so ~70 kHz–1 MHz reaches the
  in-amp at up to 2.4 × 10⁻³ (−52 dB). The chain after the in-amp and the
  jack's 15.9 kHz RC take it down; `interfaces/system/sim` holds the jack end
  to end.

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
