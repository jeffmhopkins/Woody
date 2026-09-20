# 0001 — MCU selection and board partitioning

**Status:** Accepted

## Context

The previous project used a Teensy 3.2. This iteration wants a modern part with
a display, USB, and enough I/O for a distributed instrument.

Two physical constraints drive the partitioning: the IMU must sit near the
bottom of the instrument (it senses the instrument's tilt, and the lever arm
matters), and the display must sit near the top where it can be read while
playing. In a body roughly two feet long, those cannot share a board.

## Options

**ESP32-S3.** Native USB OTG, so a genuinely class-compliant USB MIDI device
with no serial-bridge workaround and no host drivers. 2.4 GHz WiFi and BLE 5
built in, which ADR 0012 requires for phone-based configuration. Dual core
allows pinning the sensor and output loop to one core while the display and
radio live on the other.
Most nice-display dev boards are S3-based. Note it has **no DAC at all** — the
original ESP32's two 8-bit DACs were dropped on the S3. Irrelevant here, since
8 bits was never usable for pitch CV.

**ESP32-P4.** More capable, real MIPI display support, but **no built-in
radio** and less mature software support. The radio is now a requirement
(ADR 0012), so this is ruled out outright rather than merely disfavoured.

**ESP32-C6.** Single RISC-V core, weaker. Wireless features irrelevant here.

## Decision

**ESP32-S3**, as a bare module on a custom carrier — not a dev board — with
satellite boards distributed along the body.

Topology:

```
TOP   ESP32-S3 module + display (SPI, short) + USB-C
       |  ribbon: power, slow SPI, LED data
MID   74HC165 key chain, daisy-chained per cluster
       |
BOT   IMU, umbilical connector to the rack module
```

The display is the only thing that cannot run far — high-bandwidth SPI with many
signals will ring and crosstalk over any distance. (The instrument is 18 inches
overall per ADR 0009, so the longest run is nearer 14–16 inches than the two
feet this analysis originally assumed. The topology stands; the margin is
better than feared.) So the MCU lives with the display
and everything else runs long and slow. Bandwidth down the body is trivial: six
16-bit channels at 4kHz is ~576 kbit/s, comfortable at 2MHz SPI over twisted
pair.

The two SPI hosts on the S3 get split: display on one, DAC and shift registers
on the other. A display refresh must never block a CV update.

**The core split carries the WiFi stack too.** Sensor read, key scan and DAC
output own one core; display, radio and web server own the other. The radio is
the less polite neighbour of the two — see ADR 0012 for why it is also off
during performance.

## Consequences

- Dev boards remain the bring-up platform and are not wasted — they are the
  reference the custom boards get checked against.
- Buy a **plain** S3 dev board plus a **separate** display module, so the bench
  setup matches the final architecture rather than an integrated-screen board
  that would have to be unlearned later.
- Custom carrier design needed eventually: USB-C, ESD protection, boot/reset,
  3.3V regulation. Espressif publishes reference designs for this.
- The 74HC165 chain suits this geometry well — four wires running the length of
  the body, one register per key cluster. No matrix, no ghosting, no long
  parallel runs, no per-key wiring back to a central point.
- **Chain is 4 registers, 32 bits, for 18 switches** (ADR 0010): one device per
  cluster — left hand, left thumb, right hand, right thumb — ordered down the
  body. One register per cluster wastes 14 bits but makes every satellite board
  identical, and the spare bits are free expansion for octave, mode and hold
  inputs. Full chain reads in ~32 µs at 1 MHz, about 13% of a 250 µs loop
  period, and it can be clocked considerably faster.
- LED power and data run the length of the body too. Keep their ground return
  separate from the analog section and star-ground at one point, or the LEDs
  will be audible.
