# SPI link — simulation

`sims.yaml` says what is simulated and what every run must show; `cs.cir` and
`pair.cir` are the decks; `results.yaml` is what the last run found,
**generated** by `python3 tools/sim.py run hardware/interfaces/spi-link/sim`.
`python3 tools/sim.py show <this dir>` prints it as a table.
`docs/reference/tooling.md` §5 explains the tool.

**No part value is written here.** The decks read the carrier's netlist
(`R-SPI-SER-SCLK`, `-MOSI`, `-CS`, `R-CS-PULL-INST`) and the module buffer's
(`R-PULL-SCLK`, `R-PULL-MOSI`, `R-PULL-CS`). The cable is Belden 1752A, a
stranded 24 AWG Cat5e patch cable, banked for this sim
(`datasheets/connectors/BELDEN-1752A-CAT5E-PATCH-24AWG-STRANDED.pdf`,
fragment R38): 100 ± 12 Ω, 70 % velocity, 90 Ω/km. The ESP32-S3's pad, the
74AHCT125's input and U-TVS-SPI are behavioural, from their banked sheets;
`sims.yaml` gives each parameter's page.

## The cable is two different lines

`spi-link.md` models each signal as one 100 Ω line. That is right for
**`CS_MOD`**, which shares pair 7/8 with its own return `DIG_GND`: the pair's
differential impedance is exactly the line `CS` sees. It is **not** right for
`SCLK` and `MOSI`, which share pair 4/5 **with each other** and return on
other pairs. They are two coupled lines: an odd mode at half the pair's
differential impedance (50 Ω, from the datasheet) and an even mode — both
conductors together against the returns — that no datasheet gives. The run
sweeps the pair's common-mode impedance `z_cm` over 70, 100 and 140 Ω, the
range a two-wire estimate gives (`sims.yaml`, `z_cm`), and ngspice's `CPL`
line carries both modes with the conductor's loss.

## What it shows

Every sim runs at the nominal and at every end of the pad's resistance and
edge, the TVS capacitance, the buffer's input capacitance and the cable's
impedance tolerance: 33 runs each.

| Sim | What | Result |
|---|---|---|
| `cs-edges` | `CS_MOD` falls and rises, as netlisted | **A recorded hazard.** The falling edge comes back up through `V_IL` after crossing it: 0.42 V past it at the nominal, 0.63 V at the worst corner (`cs-fall-reentry`) |
| `cs-edges-fix` | a what-if: `U-TVS-SPI` on the pad side of `R-SPI-SER`, and 82 Ω | clean at every corner, undershoot inside −0.5 V |
| `pair-mosi-low` | `SCLK` at 2 MHz, `MOSI` held low | **A recorded hazard.** `MOSI` at the module rises through `V_IL` at every `z_cm` on the worst corner, and at the nominal from 70 Ω up (`spi-pair-crosstalk`) |
| `pair-mosi-high` | the same, `MOSI` held high | dips through `V_IH` from `z_cm` 100 Ω up at the worst corner, at 140 Ω at the nominal |
| `pair-opposite-mosi-falls` | `MOSI` falls as `SCLK` rises | **A recorded hazard.** `SCLK`'s edge at the module crawls up in round-trip steps (22 ns through the band at the nominal, against the buffer's 24 ns limit) and at the worst corner swings back under `V_IH` by 0.42–0.57 V |
| `pair-opposite-mosi-rises` | `MOSI` rises as `SCLK` rises | clean |
| `pair-fix` | a what-if: the `cs-edges-fix` change on both lines, plus 68 pF at each receiver | narrows `MOSI`'s crossing to 36 mV at the top of the range; does not close it |

## What it says that the page does not

- **`CS_MOD`'s falling edge is the tight one, not the rising.** The page's
  first step (2.75 V against a 2.0 V `V_IH`) is the rising edge's. With
  `R-SPI-SER` and the pad above the line's impedance the falling edge's first
  step lands at 3.3 × (135 − 100)/(135 + 100) = 0.49 V `[calc]`, 0.3 V under
  `V_IL`. And `U-TVS-SPI`'s 30 pF sits on the **line** side of `R-SPI-SER`, at
  `J-UMB`: to the returning wave it is a short, so it sends it back inverted,
  and the far end rings back up through `V_IL`, to 1.14 V at the nominal.
  With the TVS capacitance taken out the same bump is 0.63 V, under `V_IL`;
  a lossless `T` line in place of `CPL`, as a check on the line model, gives
  the same 1.2 V.
- **Pairing `SCLK` with `MOSI` is not safe by construction.** ADR 0004 and the
  page reason that coupling lands "at the moment nobody is looking". The DAC
  clocks `DIN` in on `SCLK`'s **falling** edge `[ds DAC8568CIPW.pdf p.6]`, and
  a coupled glitch arrives at the module at the same instant as the edge that
  caused it and lasts about one cable round trip (~20 ns) — against the DAC's
  6 ns setup and 4 ns hold `[same, p.7]`. The ADR's own reviewers put the
  saturated intra-pair crosstalk at 365–907 mV; the run agrees in size (0.89–1.5 V
  at the nominal) and adds where it lands.
- **The receiver has no hysteresis**, which is what turns a swing-back into a
  second edge. That is the page's own premise; these runs are what it costs.

## In the register

This README owns, in `config/figures.yaml`:

- `cs-fall-reentry`: 0.42 V nominal, 0.63 V worst corner
- `spi-pair-crosstalk`: 0.89-1.52 V nominal, 1.15-1.71 V worst corner, over a common-mode impedance of 70-140 ohm

## What a result is worth

**The even mode is an estimate**, and every `SCLK`/`MOSI` result moves with it:
at 70 Ω `MOSI` high is clean, at 140 Ω it is not. Neither the cable's datasheet
nor the standard gives a common-mode impedance, so the bench decides: **E11**,
a scope on `MOSI` and `CS_MOD` at the 74AHCT125's inputs, on the real cable at
length, `SCLK` running — the milestone ADR 0004 already names for threshold
dwell and runt pulses on `CS`, with `MOSI` at `SCLK`'s falling edge added. The
ESP32-S3's pad is a resistance and an edge (Espressif publishes no IBIS), and
the 74AHCT125's input a capacitance: a behavioural screen, not a signal-integrity
sign-off.
