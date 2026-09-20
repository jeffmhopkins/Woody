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
