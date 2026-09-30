# Umbilical load switch — simulation

`sims.yaml` says what is simulated and what every run must show;
`loadswitch.cir` is the deck and `lt1641.inc` the part; `results.yaml` is what
the last run found, **generated** by
`python3 tools/sim.py run hardware/module/umbilical-load-switch/sim`.
`python3 tools/sim.py show <this dir>` prints it as a table.
`docs/reference/tooling.md` §5 explains the tool.

**The LT1641 is behavioural.** No SPICE model could be banked (fragment R29
records the URLs), so `lt1641.inc` builds the part from the banked datasheet,
`datasheets/discrete-and-power/LT1641.pdf`: the foldback law, the gate pull-up
and its clamp, the `TIMER` currents, the 1.233 V fault latch. Each is a
parameter set per corner in `sims.yaml` with its page. **One is not in the
datasheet**: the current-limit amplifier's transconductance, an assumption
chosen large enough that its regulation error is under 1 mV. The netlist was
written from the PDF, not from the page, so a misreading of the law on the page
would not be reproduced here for free.

**The supply is `U-ISO`** since ADR 0027 (RECOM RPA20-2412SAW): 12 V ± 3.1 %
(varied; accuracy, line, load and 40 K of tempco `[calc]`), its output
resistance from the datasheet's load regulation, and `C-ISO-OUT` from
`module/power-entry`'s netlist. `hot-plug` also measures `VCC`'s dip and holds
it above the `ON` pin's worst-case turn-off, 9.90 V.

**Values are the netlists'**: this circuit's, and the instrument's input that
the umbilical charges (`carrier/power-entry-instrument`: `C-STRIP-BULK`,
`L-BUCK-IN`, `C-BUCK-IN`), with `R-ILIM` at its row's 50 mΩ. `Q-LOADSW`
(PSMN2R0-30YLE) is a level-1 FET fitted to its datasheet: maximum threshold,
maximum R_DS(on) at the LT1641's minimum 4.5 V gate drive, and C_iss. The instrument's load is `umbilical-current`,
arriving at the buck's 8 V input minimum.

## What it shows

Every sim but `fb-unconnected` runs at the nominal and at every end of the datasheet's min/max on
the sense thresholds (both ends of the foldback), the gate pull-up and both
`TIMER` currents: 33 runs.

| Sim | What | Holds |
|---|---|---|
| `cold-start` | the bus rising, the gate ramping from 0 V | completes without the fault latch at every corner |
| `hot-plug` | the FET already enhanced, the instrument plugged in | the `TIMER` stays below 1.233 V at every corner |
| `hot-plug-page-2m2` | the same with 2.2 mF on the output, the page's figure | the same |
| `fb-unconnected` | `FB` tied to nothing, the circuit before 2026-09-21 | latches off at every `TIMER` corner: the page's §5 reproduces |

## What it says that the page does not

- **The hot-plug start is not "all of it in current limit".** Once the
  current-limit amplifier has pulled `GATE` down, the output can rise only as
  fast as `GATE` does, and `GATE` is held by `C-GATE` through `R-GATE-COMP`:
  the start becomes the same programmed ramp as a cold one, with the limit
  active only for the first moments. The `TIMER` peaks in millivolts, not near
  1.233 V. So the page's 47.5 ms hot-plug arithmetic is a safe upper bound on
  time in current limit, not the start. **The bench at E6 decides**, since the
  amplifier's own dynamics are the one thing the model assumed.
- **`i_peak` in `hot-plug` is not a current anyone will see.** The deck has no
  umbilical between `OUT` and `C-STRIP-BULK`, so the first instant is
  `C-ISO-OUT` into `C-STRIP-BULK` through `R-ILIM` and the FET alone — tens to
  a hundred-odd amps for microseconds, set by the 20 µs step. The plug-in
  current with the cable in it, and what it does to `U-ISO`, is
  `hotplug-iso-ocp` (`config/figures.yaml`), owned by
  `carrier/power-entry-instrument/sim`.
- **The page's 2.2 mF is in no netlist.** The instrument's input as netlisted
  holds `C-STRIP-BULK` and `C-BUCK-IN` only (`C-BULK-DISP` left with the
  display board, ADR 0015). The deck runs the netlisted capacitance and, beside
  it, 2.2 mF: both start.
- **With `FB` unconnected the output does charge**, to where the instrument's
  load arrives — the 12 mV floor carries the capacitors' charging current but
  not the load. The stall there is what trips the timer. The conclusion (it
  never starts) is the page's; the mechanism is slightly different.

## What a result is worth

**A behavioural model cannot refute the datasheet — it can only fail to
reproduce it.** Where the deck and the page disagree, one of the netlist, the
transcription of the law, or the arithmetic is wrong, and the bench decides.
