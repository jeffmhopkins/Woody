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
| `led-pwm` | The LED row switches between blank and lit at the WS2815's 2 kHz PWM, every LED in phase. Breath is held at 2 kPa, pitch at 0 V and the mods at mid-scale. Corners: the rack PSU's resistance, `C2`'s ESR, `C-STRIP-BULK`'s ESR and the cable's gauge. This is ROADMAP M8's bench test, "pitch scoped while the LEDs sweep" (ADR 0006). | Pitch under ADR 0027's residual (`pitch_bound`). Breath's ripple (`breath_ripple_mv`, below) under half the jack's own noise, peak to peak (`breath-jack-noise`). The header rails under `led-pwm-rail-ripple`, the worst `power-entry/sim` finds. The solver's floor under 1 % of every result. |
| `led-pattern` | The same, at 200 Hz: a light pattern inside the breath and pitch bands. | Pitch under a tenth of `pitch-cents-budget`. Breath's ripple under a tenth of what the −12 V path `breath-output-stage.md` names would carry unfiltered: since #32 that leg is filtered at 6.7 Hz. |
| `led-off` | The row stays blank: the deck's own floor. | Both jacks still. |
| `burst` | Eight back-to-back DAC frames at the link's 2 MHz, mode 1. MOSI toggles on every clock, and `CS_MOD` goes high between frames for one period. `U-LVL-MOD`'s copies go into the DAC's pins, and mod channel 1 steps 2 V at each frame's end. Breath is held. | Breath under half the jack's own noise. Pitch under a tenth of `pitch-cents-budget`. |
| `burst-spi` | The same burst with no DAC output moving: the SPI edges alone. | The same. |
| `hot-plug` | The instrument is plugged into a running module, with the `+12 V` contact first and with it 1 ms late. The ESP32's pads are high-impedance and the breath is at rest. | No LT1641 latch, and `U-ISO` under half its threshold. No SCLK or MOSI spike reaches the lowest `V_T+` once `CS_MOD` could select the DAC. `CS_MOD` ends above `V_T+` max. Held pitch and mod CV still. The breath jack below 0 V with no instrument, and near 0 V with one at rest. |
| `cable-check` | `UMB_LUMPED`, the two π-sections the scenarios use, against ngspice's CPL lossy lines with the same matrices. The test is an SCLK edge into the breath pair, at three common-mode impedances. | Peak, integral and common mode within 5 %. |
| `opamp-check`, `inamp-check` | `BOPA` and `BINA` against TI's OPA2197 and INA828 macromodels, which are banked under `datasheets/analog/`. Never better than TI's model. `BOPA`'s V− rejection is within 1 dB of TI's and its V+ rejection under 9 dB worse, 1–10 kHz. `BINA`'s common-mode rejection is no more than 6 dB worse than TI's from 2 kHz up. |

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
  check sims hold both to TI's model. `BOPA` matches TI's rejection of V−
  and is up to 8 dB worse on V+, because its gain stages' own midpoint term
  adds there. `bopa.lib` records three ways of cancelling that term that each
  broke something else. `BINA` is never better than TI's model; it is worse at
  dc by design, and up to 30 dB worse on V+ at 2 kHz, which is still under a
  microvolt for every rail ripple here. Every result is therefore pessimistic
  where the models differ. No noise is modelled; `breath-output-stage/sim` does noise.
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

These are the figures the findings below rest on. `results.yaml` holds all of
them, and each is `[sim]`. "Worst" is the worst corner.

| Scenario | Pitch jack | Breath jack | Other |
|---|---|---|---|
| `led-pwm` | 0.0034 cents p-p nominal, 0.011 at the worst corner (`led-pwm-pitch`) | ripple 0.027 mV p-p, 0.058 worst (the 500 Hz mode); `breath_mv` 0.72, 1.58 worst, is the row's turn-on ramp (below) | header ±12 V 1.0 mV p-p, 3.4 worst; the instrument's ground against the module's 3.7 mV, 13 worst |
| `led-pattern`, 200 Hz | 0.033 cents p-p, 0.067 worst | ripple 0.20 mV p-p, 0.44 worst; `breath_mv` 0.71, 1.50 worst | header ±12 V 15 mV p-p, 32 worst |
| `led-off` | 1 × 10⁻⁸ cents | 0.3 µV | the deck's floor |
| `burst` | 0.025 cents | 0.68 mV | the in-amp's output 0.48 mV; mod 1 swings 3.5 V (500 Hz mode) |
| `burst-spi` | 0.011 cents | 0.56 mV | the SPI edges alone |
| `led-pwm-wide` | as `led-pwm` | ripple 0.061 mV p-p, 0.32 worst; `breath_mv` 0.76, 1.76 worst | WIDE (#32), recorded |
| `burst-wide` | 0.025 cents | **1.25 mV** | WIDE, recorded: the in-amp's output 1.35 mV. Over the 500 Hz mode's bar (1.08 mV, half that mode's noise p-p), under WIDE's own (half of 1.45 mV rms × 6.6 = 4.8 mV) |
| `hot-plug` | 0.008 cents | −1.32 V absent, −0.10 V at rest, a 76 mV transient | `U-ISO` 0.33 A peak; no latch; the instrument up in 0.125 s; SCLK/MOSI at the receiver 1.2–1.3 V at contact |

## Findings

**Confirmed.**

- **Breath is measured as ripple since #32, and that is a change of measure,
  not of bar.** `C-BREATH-OFFNEG` (owner, 2026-10-04: *"Add RC filter
  (Recommended)"*) filters the −12 V leg at 6.7 Hz, so when the row lights,
  the step in the −12 V rail's mean reaches the breath jack as a ramp over
  ~0.1 s instead of settling inside `t_led_skip`. The 8 ms window then holds
  part of that ramp: 0.72 mV of `breath_mv` at the nominal `led-pwm` corner,
  against 0.05 mV p-p of ripple in each PWM period (checked on the waveform).
  `breath_ripple_mv` is the last LED period's peak to peak less half its net
  change, and the bars apply to it; `breath_mv` is recorded. The ramp's size
  is the rail term `breath-output-stage.md` accepts (*Why −12 V is acceptable
  here*). `system.lib` also holds the RC's split at its DC value until 6 ms
  before `t_settle` (a solver aid, like `power-entry/sim`'s `ledpwm.cir`), or
  its power-on settling reads as 4.7 µV in `led-off`.
- **The drift is a recorded figure, by the owner's decision.** Offered *"1.6
  mV slow step only when the LED pattern changes; far below anything audible
  or musically meaningful. Record it as a known figure and keep the
  ripple-only measure."*, the owner chose **"Accept, record it
  (Recommended)"** (2026-10-04, ADR 0003, *The owner's three answers*, item
  4). Recorded, not passed: `breath_mv` **0.72 mV nominal, 1.58 mV at the
  worst corner** in `led-pwm` (0.71 and 1.50 in `led-pattern`), a ramp of
  about 0.1 s each time the row's mean current steps. Asserted: `breath_ripple_mv`.
- **The case's rails stay under `led-pwm-rail-ripple` for the LED row's
  PWM**, the worst `power-entry/sim` finds, at every corner. The breath jack moves by a fraction of a
  millivolt, as `power-entry/sim` found.
- **The breath link rejects the LED row's ground movement.** The
  instrument's ground moves up to 18 mV against the module's at the PWM rate
  and 40 mV with a 200 Hz pattern. The in-amp's output moves by microvolts.
- **The −12 V path to the breath jack is the one `breath-output-stage.md`
  names.** Under a 200 Hz light pattern the breath jack moves by
  `R-BREATH-FB / R-BREATH-OFFNEG` of the −12 V ripple, asserted within 20 %.
  No other path of that size shows up.
- **A burst of DAC frames at the link's full rate leaves the breath jack
  quiet.** It moves 0.68 mV in the 500 Hz mode, under half the jack's own
  noise peak to peak (`breath-jack-noise`); it was 0.2 mV behind the old
  459 Hz pole and 480 Hz jack RC. In WIDE (#32) it is 1.25 mV, recorded:
  under half WIDE's own noise, over the 500 Hz mode's bar. The SPI edges'
  spikes at the in-amp's output are what the toggle's filter lets through.
- **A hot-plug is clean at the jacks.** The LT1641 does not latch, and
  `U-ISO` peaks at about 0.34 A. That is under `hotplug-iso-ocp`,
  because this deck's `U-ISO` has its datasheet's transient
  impedance where `power-entry-instrument/sim`'s is a stiff source. The held
  pitch and mod CVs move by microvolts. The breath jack sits at −1.3 V with no
  instrument and settles near 0 V once one is plugged in at rest, so no gate
  is held open. On the way it overshoots by about 76 mV while the
  instrument's reference and sensor come up.
- **`CS_MOD` ends above `V_T+` max once the instrument is up**, so whatever
  the contact clocked into the DAC is discarded (`spi-link.md`).

**Refuted, and fixed on the page.**

- **ADR 0027's LED-PWM pitch figure.** The figure is right for the jack
  against the module's own ground. A receiver at the PSU end of the bus sees
  about four times it, and over ten times at the worst corner
  (`led-pwm-pitch`, registered here). About half of that is the jack board's
  `AGND_MOD` moving against the receivers' ground, a path `power-entry/sim`
  does not have. The worst corner is over the ADR's "under 0.01 cents"
  residual, though that residual is about breath-correlated error, and still
  more than fifty times under `pitch-cents-budget`. ADR 0027, `power-entry.md`
  and ROADMAP M8 now cite the figure.
- **`spi-link.md`'s "no edge to shift" while plugged in.** That holds in the
  steady state but not at the moment of contact. With `+12 V` making last,
  the contact's spike reaches `U-RX-MOD` at about 1.3 V while `CS_MOD` is
  already low: one rising edge on SCLK and one on MOSI. That is above the
  lowest `V_T+`, so a low-threshold part clocks a bit. The page now says so,
  and why it is harmless: the `SYNC` edge when the instrument's 3V3 arrives
  discards the partial word.

**For the owner.** These are not defects in a page; they are what the system
does.

- **A light pattern inside the audio band is a different load from the
  PWM.** At 200 Hz, with the whole row switching blank to lit, nothing
  filters it:
  - the case's ±12 V move 15 mV p-p at the header, and 32 mV with a 200 mΩ
    rack supply and 24 AWG;
  - the breath jack moves 5.8 mV, and 12.5 mV at the worst corner: three to
    seven times its own noise, peak to peak (`breath-jack-noise`);
  - the pitch jack moves 0.03–0.07 cents.

  ADR 0027 bounds the PWM, not patterns. If the firmware is to animate the row
  at tens to hundreds of hertz, the −12 V path to the breath jack (`R-OFFNEG`)
  is the one to look at. The rail number belongs in E6's scope session.
- **A DAC burst moves the held pitch jack by about 0.025 cents.** About half of
  that is the SPI edges' return currents (`burst-spi`), and half is mod
  channel 1 stepping 3.5 V. That is a thirtieth of `pitch-cents-budget`,
  noted because it is the largest pitch disturbance the deck found apart from
  the light pattern.

## Not covered

- **Noise.** No noise is modelled; `breath-output-stage/sim` covers it.
- **`U-ISO`'s 550 kHz switching**, and its common-mode current, which are
  `power-entry/sim`'s `cm-loop`.
- **Temperature.**
- **LEDs drifting out of phase.** `power-entry/sim`'s `led-pwm-pattern` shows
  that spreading the pulses lowers the ripple, so in-phase is the worst case.
- **A shield.** The etherCON shells are on no net.
