# Breath ADC — simulation

`sims.yaml` says what is simulated and what every run must show; `adc-ac.cir`
(the anti-alias filter, small-signal) and `adc.cir` (the input with the
MCP3202 sampling it) are the decks; `results.yaml` is **generated** by
`python3 tools/sim.py run hardware/carrier/breath-adc/sim`.
`docs/reference/tooling.md` §5 explains the tool.

**No part value is written here.** The decks read this circuit's netlist;
the sensor's full scale is `sensor-full-scale`, cited. **The MCP3202 is
behavioural** (no model is published): its datasheet's input model, a 1 kΩ
sampling switch into 20 pF, closed for 1.5 clocks (1.67 µs at 900 kHz) once
per 250 µs loop — both typicals only, so both are varied — and, the worst
case, the sample capacitor discharged by each conversion.

## What it shows

| Sim | Page's claim | Result |
|---|---|---|
| `filter` | 564 Hz; 55 dB at the buck's ~330 kHz | **564 Hz** (532–600 Hz at the 1 %/5 % corners); **55.3 dB** (54.8 dB worst) |
| `step` | τ = 282 µs, the latency term | **283 µs** (266–300 µs at the corners); the sampling does not move it |
| `kickback` | 480 µV/V, "a pure gain term" | **2.6 LSB** at the nominal, **3.3 LSB** at the worst corner, proportional to the input: a gain term, as the page says, and larger. The sample capacitor charges fully inside its window at every corner (R_SS × C_SAMPLE = 20 ns against 1.67 µs) |

## What it says that the page does not

The page's 480 µV/V is the *average* current, 20 pF × 4 kHz per volt, through
6 kΩ. Each sample also takes an instantaneous share of `C-AA-ADC`'s charge,
20 pF/47 nF = 0.043 % `[calc]`, which the 282 µs time constant has only
partly restored by the next sample 250 µs later. The two together are what
the run measures. It stays invisible for the page's reason — the zero is
tracked in firmware and the span is a panel knob — so nothing changes but the
number.

## In the register

This README owns, in `config/figures.yaml`:

- `adc-sample-kickback`: 2.6 LSB nominal, 3.3 LSB worst corner

## What a result is worth

A screen: the sampling model is the datasheet's typical, with an assumed
spread and a pessimistic reset. The filter and time constant are the
netlist's RC and exact.
