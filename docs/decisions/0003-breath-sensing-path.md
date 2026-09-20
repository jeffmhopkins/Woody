# 0003 — Breath sensing signal path

**Status:** Accepted

## Context

Breath is the primary expressive control. With binary keys (ADR 0002) it carries
most of the instrument's expression, so its speed and resolution matter more
here than they would on a keyboard-style controller.

The initial instinct was to keep breath analog end to end — sensor straight
through a gain stage to the jack, never touching the MCU — on the grounds that
digitising would cost resolution and speed.

## The latency budget

Measured against the real chain rather than intuition:

| Stage | Time |
|---|---|
| Pressure transducer response | **~1 ms** |
| SAR ADC conversion | ~50–200 µs |
| SPI to MCU, firmware | < 20 µs |
| SPI to DAC over the umbilical | ~50 µs |
| DAC settling | ~10 µs |
| Op-amp and reconstruction filter | ~160 µs |
| **Total** | **< 1.5 ms** |

**The transducer dominates.** The entire digital path costs less than the
sensor's own settling time. Going fully analog would save roughly 400 µs against
a 1 ms floor.

For scale: the fastest physical gesture available is a hard tongue attack, with
a rise time somewhere around 5–15 ms. The digitised path has roughly 10x margin.

On resolution: a 16-bit path gives 65,536 steps. The noise floor of human breath
— turbulence, diaphragm tremor — sits orders of magnitude above that. The
previous instrument ran a 10-bit ADC into 7-bit MIDI CC and played fine. There
is no resolution being left on the table.

## Decision

**Analog sensor → fast external SAR ADC → firmware → DAC → analog scaling → jack.**

The analog *sensor* is kept — and this is a point in favour of the original
instinct. Digital I2C pressure sensors have conversion times of several
milliseconds plus bus overhead; they are *slower* than an analog transducer read
by a fast ADC. The fast configuration genuinely is an analog front end.

**Use a SAR converter, not delta-sigma.** A delta-sigma at high oversampling has
real group delay in its digital decimation filter — potentially milliseconds,
which would consume the entire budget above. SAR converters have essentially
zero latency. Candidate: MCP33131 (16-bit SAR, SPI).

Loop rate: 4 kHz.

## What digitising buys

These are the reasons the fully-analog path was rejected, and none of them are
recoverable in hardware:

- **Curve shaping.** The previous firmware had `breath_gamma` and a `lin_to_log`
  mapping. This is the difference between a breath response that feels like an
  instrument and one that feels like a volume knob.
- **Ambient zeroing.** The old code sampled `ambient_breath_reading` at startup
  for good reason — sensor offset and atmospheric pressure both drift. Analog
  alone means a trim pot adjusted by hand, forever.
- **Threshold logic.** Breath crossing a threshold is what starts a note.
- **Noise.** Filtering in software is free. Amplifying raw sensor noise across an
  entire chain to a jack is not.

Panel knobs (ADR 0006) handle *range fitting*; firmware handles *response feel*.
Different jobs, both kept.

## Open

**Which sensor is actually in hand.** The old repository contradicts itself:

- `README.md` says **MPXV4006GP** — 0–6 kPa gauge, integrated signal
  conditioning, ~0.2–4.7V out. Directly usable.
- `src/owp/owp.ino` header says **MPX2010GS** — 0–10 kPa differential,
  uncompensated and unamplified, ~25 mV full scale. Would need an
  instrumentation amp to be usable.

Probably a stale comment against an upgraded part, but it needs confirming.
Either way the 0–6 kPa range was well chosen: normal wind-controller playing
sits around 0–5 kPa. Gauge, not differential, is correct for breath.

## The sensor is remote, fed by a tube

The sensor does **not** sit at the mouthpiece. A pneumatic tube carries mouth
pressure down the body to wherever the sensor is — standard practice on wind
controllers, and it frees the board placement entirely (ADR 0013). The sensor
and its ADC sit with the real-time board at the bottom of the instrument.

### The tube costs latency, and becomes the largest single term

Pressure propagates at the speed of sound, so a 400 mm tube adds ~1.17 ms before
the transducer sees anything:

| Stage | ms |
|---|---|
| **Tube propagation, 400 mm** | **1.17** |
| Pressure transducer | 1.00 |
| SAR ADC | 0.20 |
| SPI + firmware | 0.02 |
| SPI to DAC over umbilical | 0.05 |
| DAC settling | 0.01 |
| Op-amp + reconstruction filter | 0.16 |
| **Total** | **2.61** |

Still comfortably inside the 5 ms target, but it roughly doubles the breath
path and displaces the transducer as the dominant term. Tube length is now a
latency parameter, not just a routing convenience:

| Tube | Delay | Quarter-wave resonance |
|---|---|---|
| 150 mm | 0.44 ms | 572 Hz |
| 300 mm | 0.87 ms | 286 Hz |
| 400 mm | 1.17 ms | 214 Hz |

**Keep it as short as the layout allows.** If latency measurements come back
worse than expected, moving the sensor to mid-body is the cheapest lever
available — it costs nothing but a slightly longer wire run in place of a
shorter tube.

### Tube resonance

A closed tube rings at its quarter-wave frequency — 214 Hz for 400 mm. That sits
well above the breath signal band, which is mostly under 50 Hz, so it should
filter out cleanly in software. But it is a real mechanism and it is measurable:
a pressure step will show the ringing on a scope.

If it proves troublesome, a deliberate acoustic restriction damps it, at the
cost of a little more delay. Do not add damping pre-emptively.

## Spit and condensation: now a gravity problem

This was previously noted as unsolved. **The tube makes it acute**, and gives it
a specific shape rather than a vague one.

With the sensor below the mouthpiece and a tube between them, **gravity feeds
saliva and condensation directly into the sensor.** That is not a maybe; it is
what will happen, and a wet pressure transducer reads garbage and then stops
reading at all.

The tube therefore needs a **trap at its low point with a drain, upstream of the
sensor** — or a routing that rises before reaching the sensor, so liquid
collects where it can be cleared rather than where it does damage. It must be
drainable without disassembling the instrument.

This is a mechanical requirement on the laminated stack (ADR 0009), not a
detail to resolve during assembly, and it is the single most likely thing to
ruin the instrument three months in.
