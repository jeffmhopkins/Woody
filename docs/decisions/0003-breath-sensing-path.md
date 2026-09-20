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

## Breath output is analog, sent differentially

Breath is the one channel where output steppiness reaches the ear: it modulates
continuously, usually into a VCA, so staircase ripple becomes amplitude
modulation. Pitch is static between notes and mod channels are slow, so neither
has the same problem.

**So the breath CV never gets digitised on its way to the jack.** The sensor's
buffered output is driven down the umbilical as an analog signal and scaled in
the module. Zero steps, by construction, at any rate.

### Why a Eurorack patch cable gets away with this, and what to copy

A patch cable carries single-ended CV between modules with no trouble at all,
and understanding *why* is what makes this work here.

**A module's power returns through the bus board's ground rail, not through the
patch cable.** The patch cable's ground carries only the signal current flowing
into a high-impedance input — microamps — so it develops essentially no IR drop
and acts as a pure voltage reference.

| Receiving input | Signal current | Drop across 2 m of 24 AWG |
|---|---|---|
| 100 kΩ | 50 µA | 8.4 µV |
| 1 MΩ | 5 µA | 0.8 µV |

Against a 153 µV LSB on a 10 V output, that is nothing. The patch cable works
because **its ground does exactly one job.**

### The failure mode is a shared conductor, not a cable

The umbilical breaks that condition only if one ground conductor does both jobs.
The instrument draws its power down the same cable, and that return current
through a shared ground develops a real, *moving* offset:

| Instrument draw | Offset on a shared ground |
|---|---|
| 100 mA | 16.8 mV |
| 200 mA | 33.7 mV |
| 350 mA | 58.9 mV |

It moves with display brightness, LED animation and WiFi bursts — breath CV
modulated by the light show.

### So separate the grounds and it is a patch cable again

**Give the analog signal its own return conductor that carries no power
current**, and have the module sense `BREATH` against `AGND` rather than against
its own local ground. `AGND` then sits at true instrument-ground potential at
both ends, and the error falls back to the microvolts in the table above.

This restores exactly the Eurorack condition inside the umbilical, and it means
the instrument end needs **only a buffer** — an op-amp follower, band-limited,
with a series resistor for protection. No differential line driver.

The module end needs a difference amplifier taking `BREATH` and `AGND` as its
two inputs, which is one op-amp. That part is not optional: sensing against
local ground would put the shared-ground offset straight back in.

Full differential signalling was considered and is not needed here. It buys
about 6 dB against induced noise, which a twisted pair band-limited to 500 Hz
does not need, at the cost of a driver in the instrument.

### Impedance and bandwidth are non-problems

Drive low-impedance, receive high-impedance, standard practice. With ~200 pF of
cable and a 100 Ω source the corner sits at 8 MHz against a 160 Hz signal — six
orders of margin. Transmission-line behaviour is irrelevant at this bandwidth.

**Band-limit at both ends, around 500 Hz.** The sensor only has ~159 Hz of real
bandwidth, so a narrow channel costs nothing and rejects almost everything that
could couple in — SPI edges, LED PWM, WiFi bursts and switching-supply hash all
live far above it. A low-bandwidth analog channel is much easier to keep clean
than a wide one.

### It pays for itself on the digital link

| | Payload | SPI clock |
|---|---|---|
| Breath digital at 96 kHz + 5 channels at 2 kHz | 3.39 Mbit/s | ~6.8 MHz |
| **Breath analog, 5 channels at 2 kHz** | **0.32 Mbit/s** | **~0.6 MHz** |

This **cancels the RS-485 escalation** in ADR 0004 and **removes the sub-10 µs
DAC settling requirement** in ADR 0006. Both of those existed only to carry a
96 kHz breath channel that no longer exists.

### The ADC does not go away

The sensor's buffered output splits two ways:

- **To the umbilical buffer** — full scale, 0.2–4.7 V, for the CV output.
- **To the SAR ADC** — for breath threshold and note gating, as a modulation
  source for the mod channels, for the display, and for USB MIDI.

**The ADC branch needs attenuating.** The sensor reaches 4.7 V while the ADC
runs on 3.3 V, so that branch takes a divided copy — roughly 0.6× — to land
inside the converter's input range. The umbilical branch stays full scale.
Divide *after* the buffer, not before, so the divider does not load the sensor.

So curve shaping, thresholds and ambient zeroing still exist in firmware; they
just no longer sit in the path to the breath jack.

### What the analog path gives up, and what replaces it

**Curve shaping on the breath output.** Genuinely lost — `breath_gamma` cannot
apply to a signal firmware never touches. In a modular context this is arguably
correct: sending raw breath and shaping it with the rack's own tools is the
idiom, and the panel gain and offset knobs (ADR 0006) are exactly the Pulp
Logic model. Shaping still applies to the digital copy driving mod channels and
MIDI.

**Ambient zeroing.** Not lost — solved with a spare DAC channel. The DAC is
octal with channels going spare, so **one channel drives a firmware-controlled
DC offset into the module's analog summing stage.** Firmware measures ambient at
startup exactly as the 2021 code did, and nulls it by moving that offset. Digital
control of an analog signal path, for the cost of one already-paid-for channel.

### Parts

A precision op-amp differential driver and receiver pair is sufficient at this
bandwidth — no audio-specialty part is required, though THAT1606/THAT1200 or
DRV134/INA1650 are drop-in options if convenient. What matters is the receiver's
CMRR and low offset drift, since this feeds a 0–10 V output.

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

