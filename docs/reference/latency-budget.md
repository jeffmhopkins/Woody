# Latency budget

The constraint that shapes most of the electrical design. Written down because
it is the thing most likely to be violated accidentally by a change that looks
harmless — a blocking display refresh, an oversampled ADC, a filter corner set
too low.

> **The display and radio are on a separate MCU**
> ([ADR 0013](../decisions/0013-two-mcu-split.md)), so neither can preempt the
> loop these figures describe. That isolation is physical rather than a
> scheduling discipline.
>
> What remains is the **current transient** a WiFi burst puts on the rail, which
> reaches the analog section through shared power rather than shared CPU. Each
> board gets its own regulator and local bulk capacitance for that reason. Verify
> by measurement before trusting configuration-while-playing.

## Target

**Under 5 ms from gesture to output.** That is roughly the line between an
instrument and a toy. Everything below has comfortable margin against it.

## Breath path

| Stage | Time | Notes |
|---|---|---|
| Tube propagation | ~0.09 ms | 30 mm at the speed of sound. A *design* parameter — a 400 mm tube would cost 1.17 ms instead (ADR 0003) |
| Pressure transducer | **~1 ms** | Dominant term. A property of the sensor, not the design |
| *(breath output is analog from here — differential driver, cable, receiver and scaling add only propagation and filter group delay, well under 0.2 ms total)* | | |
| SAR ADC conversion | 50–200 µs | SAR, not delta-sigma — see below |
| SPI to MCU + firmware | < 20 µs | |
| SPI to DAC over umbilical | ~50 µs | 2 MHz, ~30% utilised |
| DAC settling | ~10 µs | |
| Op-amp + reconstruction filter | ~160 µs | ~2 kHz corner on breath |
| **Total** | **~1.5 ms** | |

For scale: a hard tongue attack has a rise time of roughly 5–15 ms. Diaphragm
dynamics are far slower. The chain has roughly 10x margin against the fastest
gesture physically available.

## Key path

| Stage | Time |
|---|---|
| Switch mechanical actuation | mechanical |
| 74HC165 chain read | < 10 µs via SPI DMA |
| Debounce (press) | 0 — fire immediately |
| Debounce (release) | filtered |
| Firmware note resolution | < 20 µs |
| DAC update + settle | ~60 µs |
| Pitch filter (~10–20 kHz corner) | ~10 µs |

**Debounce asymmetrically.** Fire on the leading edge and filter only the
release. Symmetric debounce puts its full window directly into the attack, which
is the one place latency is audible.

## Characterisation — measure these, do not assume them

Every figure in the tables above is a datasheet number or an estimate. A full
bench is available (scopes, logic analysers, signal generators), so these should
be replaced with measurements as the relevant milestones come up. Several are
load-bearing enough that being wrong about them would change the design.

| What | How | Why it matters |
|---|---|---|
| **Breath transducer response** | Step the pressure, scope the sensor output, measure rise time | A large term and a datasheet figure. If it is really 3 ms the margin shrinks; if it is 200 µs there is far more headroom than assumed |
| **Tube delay and ringing** | Step the pressure at the mouthpiece, scope at the sensor. Measure both the delay and any quarter-wave ringing | Small at 30 mm, but it is the one term that is tunable by design, so confirm it is where it should be (ADR 0003) |
| **KS-33 contact bounce** | Scope a switch, measure bounce duration on press *and* release | The 2021 firmware used a flat 20 ms debounce. If these switches settle in 2 ms, setting the window from data buys back 18 ms of the most latency-sensitive path in the instrument |
| **ADC + SPI round trip** | Logic analyser on the bus | Datasheet conversion time excludes driver overhead. The real number includes it |
| **SPI over the umbilical at length** | Logic analyser at the module end, cable at full length | Setup/hold margin, ringing, double-clocking. This is where a long cable bites, and it is invisible without an LA. Gates E11 |
| **DAC settling and filter corners** | Scope a commanded step | Confirm settling to within an LSB, and that the pitch and breath filters actually sit where they were designed to |
| **Rack rail ripple, both directions** | Scope +12V at the module with the instrument running | Incoming ripple lands on the CV outputs; outgoing noise from the local buck lands on every other module in the rack. Gates E6 |
| **WiFi transmit transients** | Scope the rail during a TX burst with the radio enabled | Now the *only* path by which WiFi can affect the outputs (ADR 0013). Decides whether configuration-while-playing is usable |
| **Inter-MCU UART link** | Logic analyser on the pair, under load | Frame integrity and whether status traffic is jitter-free at rate (ADR 0013) |
| **Umbilical link** | Logic analyser at the module end, cable at length | ~0.6 MHz now that breath is analog — confirm it is clean and that RS-485 stays unnecessary (ADR 0004) |
| **Breath channel noise** | Scope the breath jack while sweeping display brightness, LED animation and a WiFi burst | The end test for the analog breath decision. Any of those appearing on the output means AGND is picking up power return current, or the module is sensing against local ground (ADR 0003) |
| **End-to-end, in one shot** | Two scope channels: one on the sensor output, one on the CV jack | Measures the real gesture-to-output time directly instead of summing estimates. This is the number that actually matters, and it is the one measurement that validates or refutes the entire table above |

A signal generator driving a known waveform into the ADC front end also
characterises the full digitise-process-output chain's frequency response and
exposes any aliasing.

**Record the measured numbers back into this document** as they are taken, and
mark which rows are measured rather than assumed. A budget made of estimates is
a hypothesis; a budget made of measurements is a constraint.

## Rules that follow

1. **Sensor read at 4–8 kHz. Breath output never digitised at all** — it goes
   down the umbilical as a differential analog signal (ADR 0003), so there is no
   output rate to get wrong and no staircase to filter. The ADC exists for
   thresholds, note gating, mod routing and MIDI, not for the breath jack.
2. **SAR ADC, never delta-sigma.** A delta-sigma's decimation filter has real
   group delay — potentially milliseconds — which would consume the entire
   budget on its own.
3. **Display rendering never blocks the output loop.** Separate SPI host,
   separate core. A full-screen refresh on a colour LCD is orders of magnitude
   longer than the whole budget above.
4. **The WiFi stack and display are on a different MCU entirely** (ADR 0013).
   Nothing on the real-time board competes with the output loop.
5. **Pitch output filter stays fast** (10–20 kHz). A low corner is an audible
   glide on every note.
6. **Smoothing happens in software**, where it can be set per channel according
   to what that channel carries — not in the analog filter, which is fixed.

## Things that do not matter

- **Bit depth beyond 16.** One LSB at 16-bit over a 10V span is ~150 µV. The
  noise floor of human breath sits orders of magnitude above that.
- **Knob latency.** Panel knobs are turned by hand; a millisecond is nothing.
- **Stepping artefacts on slow channels.** Step size is bounded by signal slew
  rate, not full scale.
