# Latency budget

The constraint that shapes most of the electrical design. Written down because
it is the thing most likely to be violated accidentally by a change that looks
harmless — a blocking display refresh, an oversampled ADC, a filter corner set
too low.

## Target

**Under 5 ms from gesture to output.** That is roughly the line between an
instrument and a toy. Everything below has comfortable margin against it.

## Breath path

| Stage | Time | Notes |
|---|---|---|
| Pressure transducer | **~1 ms** | Dominant term. A property of the sensor, not the design |
| SAR ADC conversion | 50–200 µs | SAR, not delta-sigma — see below |
| SPI to MCU + firmware | < 20 µs | |
| SPI to DAC over umbilical | ~50 µs | 2 MHz, ~30% utilised |
| DAC settling | ~10 µs | |
| Op-amp + reconstruction filter | ~160 µs | ~2 kHz corner on breath |
| **Total** | **< 1.5 ms** | |

For scale: a hard tongue attack has a rise time of roughly 5–15 ms. Diaphragm
dynamics are far slower. The chain has about 10x margin against the fastest
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
| **Breath transducer response** | Step the pressure, scope the sensor output, measure rise time | The dominant term in the whole budget. If it is really 3 ms the margin shrinks; if it is 200 µs there is far more headroom than assumed |
| **KS-33 contact bounce** | Scope a switch, measure bounce duration on press *and* release | The 2021 firmware used a flat 20 ms debounce. If these switches settle in 2 ms, setting the window from data buys back 18 ms of the most latency-sensitive path in the instrument |
| **ADC + SPI round trip** | Logic analyser on the bus | Datasheet conversion time excludes driver overhead. The real number includes it |
| **SPI over the umbilical at length** | Logic analyser at the module end, cable at full length | Setup/hold margin, ringing, double-clocking. This is where a long cable bites, and it is invisible without an LA. Gates E11 |
| **DAC settling and filter corners** | Scope a commanded step | Confirm settling to within an LSB, and that the pitch and breath filters actually sit where they were designed to |
| **Rack rail ripple, both directions** | Scope +12V at the module with the instrument running | Incoming ripple lands on the CV outputs; outgoing noise from the local buck lands on every other module in the rack. Gates E6 |
| **End-to-end, in one shot** | Two scope channels: one on the sensor output, one on the CV jack | Measures the real gesture-to-output time directly instead of summing estimates. This is the number that actually matters, and it is the one measurement that validates or refutes the entire table above |

A signal generator driving a known waveform into the ADC front end also
characterises the full digitise-process-output chain's frequency response and
exposes any aliasing.

**Record the measured numbers back into this document** as they are taken, and
mark which rows are measured rather than assumed. A budget made of estimates is
a hypothesis; a budget made of measurements is a constraint.

## Rules that follow

1. **Loop rate 4 kHz** for sensor read and DAC update.
2. **SAR ADC, never delta-sigma.** A delta-sigma's decimation filter has real
   group delay — potentially milliseconds — which would consume the entire
   budget on its own.
3. **Display rendering never blocks the output loop.** Separate SPI host,
   separate core. A full-screen refresh on a colour LCD is orders of magnitude
   longer than the whole budget above.
4. **Pitch output filter stays fast** (10–20 kHz). A low corner is an audible
   glide on every note.
5. **Smoothing happens in software**, where it can be set per channel according
   to what that channel carries — not in the analog filter, which is fixed.

## Things that do not matter

- **Bit depth beyond 16.** One LSB at 16-bit over a 10V span is ~150 µV. The
  noise floor of human breath sits orders of magnitude above that.
- **Knob latency.** Panel knobs are turned by hand; a millisecond is nothing.
- **Stepping artefacts on slow channels.** Step size is bounded by signal slew
  rate, not full scale.
