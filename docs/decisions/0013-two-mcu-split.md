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
| LED data, two strips | 2 |
| UART to display board | 2 |
| USB D+/D− | 2 |
| **Total** | **14** of ~30 usable |

Sixteen pins of headroom, against two before.

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

## Physical placement: three zones

> Naming, to avoid confusion: **the DAC itself is not in the instrument.** It
> lives in the rack module (ADR 0004). The mid-body board is the real-time MCU —
> the board that *drives* the DAC down the umbilical.

| Zone | Contents |
|---|---|
| **Top** | Display board (AMOLED + WiFi), breath sensor + ADC on a short tube, upper key cluster |
| **Middle** | Real-time MCU |
| **Bottom** | IMU, umbilical connector, power entry and 3.3 V regulation, protection |

### Mid-body placement halves the worst-case run

Centring the MCU is what a star topology buys: nothing is far from it.

| Destination | MCU mid-body | MCU at the bottom |
|---|---|---|
| Display | 170 mm | 360 mm |
| Breath ADC | 145 mm | 335 mm |
| Left-hand cluster | 75 mm | 265 mm |
| Right-hand cluster | 75 mm | 115 mm |
| IMU | 175 mm | 15 mm |
| Umbilical | 205 mm | 15 mm |
| **Worst case** | **205 mm (8.1 in)** | **360 mm (14.2 in)** |

Longest run drops from 14 inches to 8. Nothing in this design *needs* that —
UART and slow SPI were both fine at 14 inches — but it buys margin on every
link at once, and margin is what stops intermittent faults.

It also puts the heaviest board near the U-bolt and therefore near the centre of
gravity, which makes balance more predictable (ADR 0009).

### Two physical constraints on the middle

**The U-bolt passes through the inter-hand gap.** That gap is 50 × 57 mm, and
the strap anchor through-bolts the whole stack right there (ADR 0009). A
mid-body board shares that window and must route around it. Worth laying out
together rather than discovering at assembly.

**The cavity is not a clear box.** Switch bodies protrude into it along the
centreline for the full length of both key runs, and thumb switches protrude
upward from the bottom face. What is actually free is:

- The upper section, above the left-hand key run
- The inter-hand gap, minus the U-bolt
- The lower section, below the right-hand key run
- **Two side channels** either side of the switch column — narrow, but
  continuous end to end, and the natural route for the wiring looms

Board outlines want planning against that shape, not against the raw envelope.
A long narrow board running alongside the switch column is a legitimate
alternative to fitting a square one into the inter-hand gap.

### Is the third board worth it?

The alternative is two boards, with the real-time MCU riding on the bottom board
alongside the power entry, IMU and connector. That saves a board and an
inter-board connector — fewer things to fail — at the cost of 14-inch runs
instead of 8-inch ones.

Both work. The three-board split is preferred because the instrument has the
room, the runs get shorter everywhere at once, and mass lands near the
suspension point. But if the inter-hand gap turns out too crowded once the
U-bolt and its backing plate are drawn, collapsing to two boards is a clean
fallback rather than a redesign.

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
