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

## Sensor: MPXV4006GP

0–6 kPa gauge, integrated signal conditioning, ~0.2–4.7 V out. Directly usable
by a SAR ADC with no instrumentation amplifier.

The old repository contradicted itself — its README said MPXV4006GP while
`src/owp/owp.ino` said MPX2010GS, which is uncompensated and unamplified at
~25 mV full scale and would have needed an instrumentation amp. That question is
moot now that parts are being bought new: **specify the MPXV4006GP.**

The 0–6 kPa range was well chosen in 2021 and stands. Normal wind-controller
playing sits around 0–5 kPa. Gauge, not differential, is correct for breath.

## Sensor placement: near the top, short tube

The sensor does not have to sit at the mouthpiece — a pneumatic tube carries
mouth pressure to it. But it also does not have to travel far, and the tube is
the most expensive part of the breath path, so keep it short.

### The SPI bus already runs the full length of the body

This is what makes placement cheap, and it is easy to miss. The 74HC165 key
chain reaches the **left-hand cluster, which is the upper one** — so SCK, MISO
and LATCH already run from the real-time board at the bottom all the way to the
top of the instrument (ADR 0001, ADR 0013).

Putting the breath ADC up there therefore **shares an existing bus**. It costs a
chip select, plus MOSI if the converter takes commands. It is not a new run.

### Options

| Option | Tube | Delay | Resonance | Extra wires |
|---|---|---|---|---|
| **A — top, sharing the left-hand cluster board** | 30 mm | **0.09 ms** | 2858 Hz | CS + MOSI |
| B — mid-body, on a cluster board | 200 mm | 0.58 ms | 429 Hz | CS + MOSI |
| C — bottom, with the real-time board | 400 mm | 1.17 ms | 214 Hz | none |

**Option A.** Tube delay effectively disappears, resonance is pushed to 2858 Hz
— far outside any band that matters and trivially filtered — and the cost is two
wires on a bus that is already there. The breath path returns to being dominated
by the transducer itself:

| Stage | ms |
|---|---|
| Tube propagation, 30 mm | 0.09 |
| Pressure transducer | 1.00 |
| SAR ADC | 0.20 |
| SPI + firmware | 0.02 |
| SPI to DAC over umbilical | 0.05 |
| DAC settling | 0.01 |
| Op-amp + reconstruction filter | 0.16 |
| **Total** | **~1.5** |

Option C remains a legitimate fallback if the top-end board gets crowded — it
costs about 1.1 ms, which the budget can absorb. Tube length is a lever that
stays available either way.

## Update rate: well above audio, but not where you would expect

The CV output should update **considerably above audio rate**. That requirement
is right, and it lands somewhere counter-intuitive — so it is worth separating
two things that look like one.

### The sensor cannot produce information above ~160 Hz

A 1 ms transducer response is a first-order corner around **159 Hz**. Sampling
above roughly 2 kHz captures **no additional breath information whatsoever**.
Any rate beyond that buys *reconstruction smoothness*, not signal.

That is not an argument against a high rate. It is an argument about **where the
high rate has to be**: on the DAC side, not the ADC side.

### Why smoothness genuinely matters here

Output steps are not a theoretical concern when the destination is a modular
rack. Breath CV driving a VCA means staircase ripple becomes amplitude
modulation, and that is audible.

During a fast tongue attack — full range in ~5 ms — step size by update rate:

| Rate | Samples across the attack | Step | Images (2-pole @ 2 kHz) |
|---|---|---|---|
| 4 kHz | 20 | **500 mV** | 12 dB down, at 4 kHz |
| 24 kHz | 120 | 83 mV | 43 dB down |
| 48 kHz | 240 | 42 mV | 55 dB down |
| **96 kHz** | **480** | **21 mV** | **67 dB down, at 96 kHz** |
| 192 kHz | 960 | 10 mV | 79 dB down |

At 4 kHz those are half-volt steps landing squarely in the audio band, barely
filtered. That is the buzz worth designing out.

### Decision

**Target 96 kHz on the breath channel**, 48 kHz as the fallback if the link
proves difficult. Images land at 96 kHz, far outside the audio band and 67 dB
down.

**The ADC stays slow.** Run it at 4–8 kHz — already several times the sensor's
own bandwidth — and generate the high-rate DAC stream in firmware with a
smoothing filter running at the output rate, its time constant set just below
the sensor's corner so it does not slow the response.

Use a filter rather than interpolation between samples: interpolation needs the
*next* sample and therefore adds a full sample period of latency, while a
one-pole IIR at the output rate costs only its own group delay and no lookahead.

This is the cheap version of the requirement. A faster ADC and a faster sensor
would buy nothing; only the DAC side needs the rate.

## Condensation, in proportion

**This is a closed, dead-ended system** — the tube terminates at the sensor and
no air flows through it. Pressure transmits without bulk flow.

An earlier revision of this ADR called saliva reaching the sensor a certainty
and the most likely thing to ruin the instrument. That was overstated: it
assumed a flow path carrying droplets along, which a sealed dead-end does not
have. What actually happens is **condensation forming slowly on the tube walls**
as warm breath meets cooler surfaces.

Still worth handling, cheaply:

- A **small dead-volume trap at the sensor end** catches what does accumulate.
  Low cost, no downside, and it works regardless of where the sensor sits.
- Make it **clearable without disassembly**. Not a drain plumbed through the
  body — just access.
- Short tubes accumulate less, which Option A gives for free.

Not a stack-level design problem, and not a reason to choose one sensor position
over another.

