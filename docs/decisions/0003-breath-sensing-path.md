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
zero latency.

Loop rate: 4–8 kHz.

### The ADC specification needs revisiting

MCP33131-10 (16-bit, 500 ksps) was chosen when the breath **output** was going
to be digitised. It no longer is — the CV path is analog end to end.

What the ADC actually serves now is much less demanding: breath threshold and
note gating, a modulation source for the mod channels, the display, and USB
MIDI. Only the mod-channel use benefits from real resolution, and MIDI CC is
7 bits.

So 16 bits at 500 ksps is considerable overkill, and a cheaper, simpler part at
12–16 bits and a few tens of ksps would do. The SAR-not-delta-sigma rule still
holds — the threshold that starts a note is on the latency-critical path.

Still worth keeping it external rather than using the ESP32's internal ADC,
which is noisy and nonlinear enough to be visible on a modulation output.

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

## Sensor placement: at the bottom, with the real-time board

**Decided after review. This reverses an earlier placement whose justification
turned out to be false.**

An earlier revision put the sensor at the top on a 30 mm tube, reasoning that
*"the SPI bus already runs the full length of the body … putting the breath ADC
up there shares an existing bus."* **That is wrong.** The 74x165's QH is a
permanently driven output with no output-enable pin, so the shift register chain
and the MCP3202 cannot share MISO at all — the ADC could never have been read.
The stated reason for the short tube did not exist.

With that gone, three things push the sensor down:

- **Routing.** At the top, the analog pair must traverse the whole body through
  side channels shared with pulsed LED current. At the bottom it sits where the
  umbilical leaves, and **there is no internal analog run at all.** That deletes
  the problem rather than managing it — and the internal equivalent of the AGND
  sense-return rule, which no ADR ever wrote, stops being needed.
- **Thermal.** The display board (AMOLED + WiFi) is the hottest single item in
  the instrument and lives in the top zone. The interior rises 10–20 K over
  10–20 minutes, and this is a **gauge sensor with a temperature-dependent
  offset whose zero is captured once at cold startup.** Putting it next to the
  heat source is the worst available placement for both.
- **Serviceability.** The sensor is EOL (below), moisture-sensitive, and the
  most likely part to fail, in a body that cannot be reopened. At the bottom it
  is at least near the one face that is not a key surface.

### The cost, and why it is affordable

| Tube | Delay | Helmholtz |
|---|---|---|
| 30 mm (old) | 0.09 ms | 2858 Hz |
| **400 mm (chosen)** | **1.17 ms** | **214 Hz** |

Breath path goes from ~1.5 ms to ~2.6 ms against a 5 ms target. The tube
displaces the transducer as the dominant term, but there is ample margin against
the 5–15 ms rise of the fastest gesture available.

**The resonance needs handling, and the model matters.** A quarter-wave standing
wave is the wrong model once there is a trap volume at the end — it is a
**Helmholtz resonator**, and at 3 mL of trap it lands near **320 Hz, below the
500 Hz filter corner**, where it would pass straight through. So:

- **Specify the trap volume at ≤1 mL.** "Small" is not a spec.
- Add a deliberate pneumatic restrictor at the sensor port to make the path
  first-order rather than resonant. Sizing depends on orifice length as well as
  diameter and needs a bench check — a porous PTFE plug does the same job and
  doubles as the moisture barrier.
- Tube length is the cheapest remaining lever if measurements come back worse
  than expected.

## The closed tube is correct, and why

A design review raised this as a likely error, on good evidence: no commercial
wind controller uses a sealed pneumatic path. The Akai EWI plugs its sensor tube
and drills a side hole, then runs a second tube dangling free for restricted
airflow. The Yamaha WX has a drain hole with swappable plugs that set blowing
resistance. Against a full occlusion an adult produces 15–20 kPa, and the
reviewer concluded the player could not exhale through the instrument at all.

**The premise was wrong, because the exhale path is not the instrument.** The
player vents through the corners of the mouth, around the mouthpiece — which is
also what makes **circular breathing** possible. Air leaves continuously; it just
never enters the sensor tube.

So the tube to the sensor stays **completely closed**, and this is a deliberate
choice rather than an oversight:

- Embouchure controls pressure directly, with no bleed orifice in series to
  blunt it
- Nothing to clog, tune, or get wrong as a manufacturing tolerance
- No flow through the sensor branch at all, which is the property the
  condensation handling below depends on

**Recorded so it is not re-raised.** The commercial designs solve a problem this
playing technique does not have.

Two consequences that do *not* follow from the bleed question and remain open:
the moisture handling below, and the tube resonance model.

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

