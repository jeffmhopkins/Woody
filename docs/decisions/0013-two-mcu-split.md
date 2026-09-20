# 0013 — Two-MCU split

**Status:** Accepted

Revises the board partitioning in [ADR 0001](0001-mcu-and-board-partitioning.md).
The MCU family choice there still holds for the real-time board.

## Context

Two problems had converged on the same place:

- **Pin budget was the binding constraint on board choice** (ADR 0008). An
  integrated AMOLED board had to break out 10 free GPIO, which the most
  attractive compact boards do not.
- **Integrated screen boards are often ESP32-C6**, which fails two architectural
  gates: single core turns the sensor/display core split from a guarantee into a
  software discipline, and the absence of a USB OTG peripheral removes
  class-compliant USB MIDI and with it the whole DAW-based bring-up strategy.

Both problems come from asking one chip to run a 4 kHz deterministic loop, a
QSPI display, a WiFi stack and a web server at once.

## Decision

**Two microcontrollers, joined by a UART.**

| | **Real-time board** | **Display board** |
|---|---|---|
| Part | ESP32-S3 | Anything with a screen and a radio |
| Owns | Keys, breath, IMU, DAC, USB MIDI | AMOLED panel, WiFi, web app |
| Nature | Hard real-time, deterministic | Soft, interactive |
| State | **Authoritative** | None |

### The real-time board owns everything that matters

Sensor read, key scan, fingering resolution, the 4 kHz output loop, SPI down the
umbilical, and USB MIDI. It holds the config, the calibration and the NVS. It is
the instrument.

Its pin budget is now comfortable rather than binding:

| Function | Pins |
|---|---|
| SPI2: SCK, MOSI, MISO | 3 |
| CS: DAC, CS: breath ADC | 2 |
| Shift register latch | 1 |
| I2C: IMU | 2 |
| LED data | 1 |
| UART to display board | 2 |
| USB D+/D− | 2 |
| **Total** | **13** of ~30 usable |

Seventeen pins of headroom, against two before.

### The display board is a terminal

It renders what it is told and forwards what the user does. It needs **four
broken-out pins** — UART pair and power — instead of ten.

That reopens the entire category of compact integrated screen boards, including
the ones already on hand. **A C6 is perfectly good in this role**: single core is
irrelevant when nothing real-time runs on it, and the missing USB OTG peripheral
does not matter because USB MIDI lives on the other board.

### Single source of truth

**The real-time board is the authority. The display board persists nothing.**

The web app's assets live in the display board's flash, but every piece of
configuration data round-trips: the phone edits, the display board forwards, the
real-time board validates, applies, persists and echoes back the new state.

Two authorities that can disagree is the failure mode that makes split-brain
designs miserable, and it is avoided by rule rather than by care.

## The link

**UART, two pins, framed protocol with checksums.**

Chosen over SPI and I2C because it is symmetric — both ends can initiate without
an interrupt line, which matters because config arrives asynchronously from the
phone while status flows the other way continuously.

At 921600 baud, 60 Hz status updates of ~32 bytes use **2% of capacity**. There
is room for an order of magnitude more without thinking about it.

Traffic:

- **Real-time → display:** note, breath level, channel values, mode, link state.
  Continuous, ~60 Hz, small.
- **Display → real-time:** config edits, calibration commands, preset changes.
  Infrequent, occasionally a larger blob.

It is also trivial to debug with a logic analyser, which is on the bench
already.

## What this costs

Honestly, so it is not discovered later:

- **Two firmware images**, two flashing procedures, two things to keep in
  version step. A protocol version field in the frame header is worth having
  from day one.
- **A protocol to design and debug.** Small, but real.
- Slightly more power and board area. Neither is tight.

## What it buys beyond the pin budget

**Isolation is now at the chip level rather than the core level**, which is a
materially stronger guarantee. WiFi and display rendering cannot preempt the
output loop because they are not on the same silicon. The core-split discipline
in ADR 0001 stops being something to maintain carefully and becomes a physical
fact.

**Live configuration while playing becomes possible.** ADR 0012 requires the
radio off during performance for two reasons; the CPU contention reason is now
gone entirely. The current-transient reason remains, but is containable: give
each board its own regulator from the umbilical +12V, with local bulk
capacitance on the display board, so WiFi bursts are absorbed locally rather
than reaching the analog section.

Being able to adjust a routing matrix and hear the result immediately is worth
real effort, and this comes close to free.

## Physical placement

**Display board at the top. Real-time board at the bottom.**

An earlier revision put both at the top, on the reasoning that the breath sensor
is analog and must stay near the mouthpiece. That constraint does not exist —
**a pneumatic tube carries the pressure to wherever the sensor is** (ADR 0003),
which is how wind controllers normally do it. The sensor and its ADC therefore
follow the real-time board rather than pinning it.

Putting the real-time board at the bottom is strictly better, because the two
things it most wants to be near are already there:

- **The IMU**, which belongs low in the instrument for leverage (ADR 0001). No
  I2C run down the body at all now.
- **The umbilical connector**, so SPI to the DAC exits immediately instead of
  traversing the instrument first.

### What runs down the body becomes far more benign

| Before | After |
|---|---|
| SPI (3) + chip selects to the DAC | — exits at the bottom |
| I2C to the IMU | — IMU is at the bottom |
| Shift register chain | Shift register chain |
| LED data | LED data |
| — | UART to the display board |
| — | Power to the display board |

**UART is close to the most robust thing that can be sent down a wooden
instrument.** It is asynchronous and self-clocking, with no setup-and-hold
relationship to preserve and wide tolerance to skew and slew — unlike SPI, which
needs clock and data to stay aligned. Trading a clocked bus for an async pair
over that distance is a real gain.

Balance improves slightly too: mass distributed between the ends rather than
concentrated at the top.

## Considered and rejected

**A non-ESP real-time MCU** — RP2350 in particular, whose PIO is genuinely
excellent for deterministic shift-register reads and hardware-timed DAC updates,
with native USB. Rejected to keep **one toolchain and one ecosystem** across both
boards, which is worth more than PIO on a solo project. Worth revisiting only if
the S3 turns out to struggle with loop determinism, which is not expected at
13 pins and one job.

## Open

- Frame format and protocol versioning.
- Whether the display board is flashed over its own USB or via the real-time
  board. Its own is simpler; one connector is tidier.
