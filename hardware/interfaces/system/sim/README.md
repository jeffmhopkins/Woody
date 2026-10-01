# The system — one deck, instrument to module

`sims.yaml` says what is simulated and what every run must show. `system.lib`
is the circuit, one subcircuit called `SYS`. `cable.lib` is the umbilical, and
`bopa.lib` holds the behavioural op-amps. The scenarios are in `led.cir`,
`burst.cir` and `plug.cir`, and the checks on the models are in `cable.cir`,
`opamp-check.cir` and `inamp-check.cir`. `results.yaml` is **generated** by
`python3 tools/sim.py run hardware/interfaces/system/sim`. The run takes about
half an hour, so run it in the background. `docs/reference/tooling.md` §5
explains the tool.

This is not a circuit and has no netlist of its own. It joins every circuit
that the instrument's supply, the breath signal and the SPI link cross, the
way the corpus joins them:

- the rack;
- `module/power-entry`, with `U-ISO` and its input filter;
- `module/umbilical-load-switch`;
- the panel LED, on module-main;
- the umbilical, with all eight conductors;
- `carrier/power-entry-instrument`, with `Q-INRUSH`;
- `carrier/led-strip-drive`'s row;
- `carrier/breath-excitation-reference`;
- `interfaces/breath-sense-link`;
- the carrier's SPI pads;
- `module/digital-and-supervision`'s receiver and level shifter;
- `module/breath-receive-stage`;
- `module/breath-response-shaper`;
- `module/breath-output-stage`;
- `module/pitch-stage`;
- `module/mod-channels`.

**No part value is written here.** Every part is `{{ROW}}` or `{{ref}}`, filled
from the netlists that `sims.yaml` lists. The LED row's size is `n:D-LED`,
counted off `carrier/led-strip-drive`'s netlist. Every model parameter that
another sim owns is imported from that sim (`params_from:`):

| Parameters | Imported from |
|---|---|
| the rack's copper, `U-ISO`'s input filter | `module/power-entry/sim` |
| the LT1641 | `umbilical-load-switch/sim` |
| `Q-INRUSH`, the buck | `power-entry-instrument/sim` |
| the cable's impedances, the pads, the receiver's thresholds | `spi-link/sim` |
| the diode fits | `breath-response-shaper/sim`, `panel-led/sim` |
| the TVS fit | `breath-sense-link/sim` |

What this directory adds is in its own `params:`, each with its source.

## Scenarios and what they assert

| Sim | What happens | Asserted against |
|---|---|---|
| `led-pwm` | The LED row switches between blank and lit at the WS2815's 2 kHz PWM, every LED in phase. Breath is held at 2 kPa, pitch at 0 V and the mods at mid-scale. Corners: the rack PSU's resistance, `C2`'s ESR, `C-STRIP-BULK`'s ESR and the cable's gauge. This is ROADMAP M8's bench test, "pitch scoped while the LEDs sweep" (ADR 0006). | Pitch under ADR 0027's residual (`pitch_bound`). Breath under a tenth of the sensor's own noise at the jack (`breath-receive-stage.md`). The header rails under ADR 0027's LED bound (`rail_led_bound`). The solver's floor under 1 % of every result. |
| `led-pattern` | The same, at 200 Hz: a light pattern inside the breath and pitch bands. | The same asserts. |
| `led-off` | The row stays blank: the deck's own floor. | Both jacks still. |
| `burst` | Eight back-to-back DAC frames at the link's 2 MHz, mode 1. MOSI toggles on every clock, and `CS_MOD` goes high between frames for one period. `U-LVL-MOD`'s copies go into the DAC's pins, and mod channel 1 steps 2 V at each frame's end. Breath is held. | Breath under a tenth of the sensor's noise. Pitch under a tenth of `pitch-cents-budget`. |
| `burst-spi` | The same burst with no DAC output moving: the SPI edges alone. | The same. |
| `hot-plug` | The instrument is plugged into a running module, with the `+12 V` contact first and with it 1 ms late. The ESP32's pads are high-impedance and the breath is at rest. | No LT1641 latch, and `U-ISO` under half its threshold. No SCLK or MOSI spike reaches the lowest `V_T+` once `CS_MOD` could select the DAC. `CS_MOD` ends above `V_T+` max. Held pitch and mod CV still. The breath jack below 0 V with no instrument, and near 0 V with one at rest. |
| `cable-check` | `UMB_LUMPED`, the two π-sections the scenarios use, against ngspice's CPL lossy lines with the same matrices. The test is an SCLK edge into the breath pair, at three common-mode impedances. | Peak, integral and common mode within 5 %. |
| `opamp-check`, `inamp-check` | `BOPA` and `BINA` against TI's OPA2197 and INA828 macromodels, which are banked under `datasheets/analog/`. | Supply rejection within 1 dB, 1–10 kHz. `BINA` is never better than TI's model. |

Every scenario's measure is a peak-to-peak value, or a deviation from the
value just before the event. Each scenario also measures the same quantity
over a window before its event (`pre_*`), so the solver's own noise is in the
record beside the result.

## What is modelled

- **Every run is a power-on.** The rack's rails ramp, and then `U-ISO`
  starts. The DAC's codes and `VREFOUT` ramp from 0 V. The load switch and
  the instrument start as their own sims start them. Each scenario's event
  comes at `t_settle`, after all of that has settled.

  This deck has no reliable DC operating point. A constant-power buck behind a
  current-limited switch has more than one, and ngspice found whichever its
  stepping reached. A power-on has only one ending.
- **The umbilical's conductors are eight coupled lines.** All eight are
  pinned as `umbilical-pinmap`. The matrices are a perfectly twisted cable's,
  built from `spi-link/sim`'s odd-mode and even-mode impedances and the
  banked Belden datasheet's velocity. The datasheet's maximum capacitance
  unbalance is added from BREATH to `+12 V` and again to SCLK, a deliberate
  double count. The reference conductor floats, because the instrument is
  isolated. `cable.lib` gives the derivation.
- **The grounds are wired as netlisted.** `PWR_GND` runs from `U-ISO` to the
  etherCON. `NT-UMB-MOD`, `DIG_GND` and `NT-DIG-MOD` lead to the star, then
  `AGND_MOD`, then `J-B2B-MOD` to the jack board. The patch-cable sleeves
  return to the receivers at node 0, the PSU end of the bus. On the
  instrument side are `AGND_INST`'s island and `NT-AGND`.
- **The breath chain is the netlist's.** It runs from the sensor through its
  buffer, `R1`/`R1b`, the umbilical, `R3`/`R2`, the bias and differential
  capacitors and the clamps, to the in-amp at `R-GAIN-INAMP`. Then come
  `TRIM-BREATH-ZERO`, the shaper (`D-RESP`), `POT-GAIN`, `POT-OFFSET` and the
  output stage, ending at the jack.
- **The DAC's outputs are sources**, driven by code into the pitch and mod
  stages as netlisted. Its pins are 3 pF loads on `U-LVL-MOD`'s outputs.

## What is idealised, and why

- **`U-ISO` is a source.** It has its set point, its load regulation and a
  dynamic impedance from its datasheet's transient response, and its input
  current is its output power divided by its efficiency. Its 550 kHz
  switching is not modelled. The capacitors at its input therefore carry no
  ESL, and `system.lib` says why.
- **The op-amps and the in-amp are behavioural** (`bopa.lib`). TI's OPA2197
  and INA828 macromodels, which every other sim here uses, found no DC
  operating point in this deck. They also stalled its power-on at random
  corners. Each behavioural block is built from its datasheet: gain, GBW,
  slew, output swing, output impedance, short-circuit current, input
  capacitances and quiescent current. Its supply rejection is fitted to TI's
  model and its common-mode rejection to the datasheet's minimum, and the two
  check sims hold both to TI's model. `BOPA` matches TI's PSRR from either
  rail within 1 dB. `BINA` is never better than TI's model, and is worse at dc
  by design. No noise is modelled; `breath-output-stage/sim` does noise.
- **The REF5050, the LT3042 and the LT1641 are behavioural** too: the first in
  `system.lib`, the other two imported from their sims.
- **The sensor is a VCVS** of its datasheet transfer function behind 100 Ω,
  with no noise.
- **The ESP32's pads are a 3.3 V source behind `r_drv`**, with their clamps.
  The burst takes the clamps out, since its pads stay inside 0–3.3 V.
  `U-LVL-MOD`'s outputs are two switched resistances.
- **The LED row is one current**, blank to lit, smoothly on above 9 V of
  `INST_POS12`, with every LED in phase. That is the worst case: the WS2815s
  run their own oscillators.

## Solver

These are recorded because each one cost a day:

- **`abstol=1e-6` in every scenario.** At ngspice's default `1e-12`, the
  burst failed "timestep too small" at the first SPI edge. A 3 ns pulse into
  a 3 pF load connected to nothing else failed the same way. The LED
  scenario's numbers are unchanged by it, to 0.1 %.
- **No ESL on `C2`, `C-ISO-IN` or `C-ISO-Y`.** `C-ISO-Y`'s nanohenry against
  `U-ISO`'s 1.1 nF barrier capacitance is a loop with no resistance in it,
  and it stalled the solver at sub-nanosecond steps.
- **Burst edges are PULSE sources timed as `t_b0` plus an offset**, a brace
  expression that ngspice sums in double precision. A time written to six
  figures cannot place a nanosecond edge 0.32 s into a run.
- **The CPL line steps at its own delay**, about 10 ns, so no
  millisecond-long run can use it. The scenarios use the lumped form, and
  `cable-check` holds the lumped form to the CPL line. CPL also carries no
  current at DC, so `UMB_CPL` adds a DC path beside each conductor.
- **One flat subcircuit shares one node namespace.** A collision between the
  instrument's reference-capacitor ESR node and the module's −12 V decoupler
  (`crn1`) ran 60 mA of the instrument's return through the rack's ground.
  Every run converged with it in place.

## Results

`results.yaml` holds every corner. Run `python3 tools/sim.py show
hardware/interfaces/system/sim` to see them as a table.

RESULTS_PLACEHOLDER
