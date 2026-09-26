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

| Function | Pins | Needs a broken-out pin? |
|---|---|---|
| SPI2: SCK, MOSI, MISO — DAC8568 + MCP3202 | 3 | yes |
| CS: DAC, CS: breath ADC | 2 | yes |
| **SPI3: SCK, MISO — 74x165 chain alone** | **2** | yes |
| Shift register latch | 1 | yes |
| LED data, two strips | 2 | yes |
| UART1 to display board | 2 | yes |
| UART0 console to a test header | 2 | yes |
| I2C: IMU | 2 | **no** — onboard, GPIO11/12 |
| USB D+/D− | 2 | **no** — the board's own USB-C, GPIO19/20 |
| **Total on the chip** | **18** of ~30 | **14 broken out** |

The distinction in the last column is what decides the board, not the raw count:
an onboard IMU and a native USB connector cost chip pins but not *header* pins.
On the selected ESP32-S3-Matrix that is **14 of 17 broken out, three spare** —
see ADR 0007 for the assignment.

Fourteen chip pins of headroom, against two before.

**The chain gets its own SPI host because it has to.** A 74x165's `QH` is a
permanently driven totem-pole output with no output enable, so it cannot share
MISO with the MCP3202 — the ADC would never be readable. This is a hard
electrical constraint, not a partitioning preference; see ADR 0001. An earlier
version of this table showed 14 pins and one shared host, and was wrong.

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
| **Top** | Display board (AMOLED + WiFi), upper key cluster |
| **Middle** | Key clusters, wiring looms, the U-bolt |
| **Bottom (tail)** | **Real-time board** — and with it the **IMU** (soldered to it) and the **8×8 matrix** — plus the **breath sensor and ADC**, the precision reference and buffer, the umbilical connector, power entry, and the USB-C slot |

**This table previously said something physically impossible**, and six review
documents flagged it: it placed the IMU in the Bottom zone and the real-time MCU
in the Middle, when the IMU is *soldered to the real-time board*. It also put
the breath sensor at the top on a short tube, which ADR 0003 reversed, and it
was the load-bearing premise for a "mid-body placement halves the worst-case
run" argument that no longer applies.

### Everything real-time is at the tail, and three decisions put it there

The concentration is not an accident of layout; it is where three independent
arguments landed:

- **The IMU wants to be low.** Acceleration is a first-class control and scales
  with distance from the pivot at the player's hands (ADR 0007).
- **The breath sensor wants to be with the ADC and its reference**, which means
  a long pneumatic tube rather than a long analog run — and it wants to be away
  from the display board's AMOLED, which is the hottest thing in the instrument
  (ADR 0003).
- **The 8×8 matrix wants a window in the player's downward glance**, which is
  the tail underside (ADR 0014).

All three want the same board in the same place, which is rare enough to take
advantage of.

### What it costs: the longest run is 360 mm, not 205

| Destination | Run from the tail |
|---|---|
| Display board | **360 mm** |
| Left-hand cluster | 265 mm |
| Right-hand cluster | 115 mm |
| IMU | on-board |
| Breath sensor / ADC | on-board |
| Umbilical | 15 mm |

An earlier version of this ADR preferred mid-body placement because it halved
the worst case to 205 mm. That advantage is real and it is **spent
deliberately**: the 360 mm run is the **inter-MCU UART**, the least
timing-sensitive link in the instrument, running at 921600 baud with 2 % bus
utilisation. Everything that is timing-sensitive — the sensor, the converter,
the reference, the IMU — is now on-board with a run of zero.

The analog runs went from 400 mm to zero. The pneumatic run went from 30 mm to
400 mm. That trade is argued in ADR 0003 and it is the right way round: a tube's
failure modes are delay and condensation, both bounded and both handled, where a
400 mm analog pair alongside LED power has failure modes that are neither.

### Two physical constraints, now on the tail rather than the middle

**The tail face is crowded.** It carries the umbilical connector, the USB-C
slot, and — on the underside just inboard — the matrix window. A ~26 × 31 mm
etherCON flange on a 57 × 38 mm face leaves little room, the D-series is rated
for a **4 mm maximum panel thickness** so it cannot mount through 6 mm oak, and
all of it must be drawn together at M4 (ADR 0009).

**The cavity is not a clear box.** Switch bodies protrude into it along the
centreline for the full length of both key runs, and thumb switches protrude
upward from the bottom face. What is actually free is:

- The upper section, above the left-hand key run
- The inter-hand gap, minus the U-bolt
- The lower section, below the right-hand key run — now the busiest zone
- **Two side channels** either side of the switch column — narrow, but
  continuous end to end, and the route for the wiring looms and the LED strips

Board outlines want planning against that shape, not against the raw envelope.

### The third board is gone

An earlier version weighed a three-board split (display, mid-body MCU, bottom
I/O) against two. **It is two**: a display board at the top and everything else
at the tail. The third board existed only to hold a mid-body MCU, and the MCU
moved.

## Build approach: dev boards as modules on a passive carrier

Optimising for ease of construction changes the shape of the final build, so it
is worth stating rather than leaving implied by milestone E13.

**Do not design a custom ESP32-S3 carrier.** That means taking on the module
footprint, USB-C, ESD, boot and reset circuitry, power sequencing, antenna
keepout and RF layout rules — a real PCB design with real ways to fail, for an
instrument where none of it is the interesting part.

**Instead: keep both dev boards as modules, on a carrier that has no MCU on it
at all.** The carrier holds only:

- Headers the dev boards plug into
- ~~The shift registers~~ — **no.** This line and ADR 0001 specified opposite
  looms for a long time without either noticing. It is settled the other way:
  **one 74HC165 per cluster, on the board its switches are already on**, which
  keeps 4 ICs and 63 passives off a carrier that is short of room. See ADR 0001
- MCP3202 ADC, REF5050 5.000 V reference, OPA2197 dual (reference buffer +
  breath buffer, both on +12 V)
- 74AHCT125 level shifter
- **Two** R-78E5.0 regulator modules — one per dev board, per the WiFi-isolation
  argument below and ADR 0005's load table — and the umbilical connector. **No
  polyfuse:** the current limit lives at the module end (ADR 0005)
- Passives

Nothing on that board is fast, nothing is RF, and nothing needs more than two
layers. It can be assembled by hand.

**Package policy**, so part choices do not drift later:

| | Pitch | Verdict |
|---|---|---|
| SOIC, SIP, through-hole | 1.27 mm+ | Preferred |
| TSSOP, MSOP | 0.65 mm | Acceptable — drag-solderable with flux |
| QFN, BGA, leadless | 0.5 mm, hidden pads | **Avoid** — needs paste, stencil and a hotplate |

Passives at 0805 or 1206, not 0402. See the `package` column in
`hardware/bom.csv`.

The dev boards already carry USB-C, regulation, boot and reset buttons, and —
in the ESP32-S3-Matrix's case — the IMU. Rebuilding any of that is work for no
gain.

Costs, honestly: the dev board outlines dictate carrier layout, the stack gains
a board-on-board height (affordable against 38 mm of cavity and 10 mm boards),
and a discontinued dev board would mean a redesign. Against a custom S3 carrier
that risks not working at all, this is the better trade.

### RF through the aluminium plate: not a concern

Raised and dismissed. The display board's antenna sits under the aluminium key
plate, but oak and acrylic are effectively RF-transparent and the plate is only one
face of the enclosure. (Since 2026-09-26 the display sits on the underside, below
the plate rather than under a window in it, which only improves this — ADR 0009.)
Recorded so it does not get re-litigated.

## Considered and rejected

**A non-ESP real-time MCU** — RP2350 in particular, whose PIO is genuinely
excellent for deterministic shift-register reads and hardware-timed DAC updates,
with native USB. Rejected to keep **one toolchain and one ecosystem** across both
boards, which is worth more than PIO on a solo project. Worth revisiting only if
the S3 turns out to struggle with loop determinism, which is not expected at
13 pins and one job.

## Open

- Frame format and protocol versioning.
- ~~Whether the display board is flashed over its own USB or via the real-time
  board.~~ **Settled: via the real-time board, over the UART that already joins
  them.** Its own USB is inside the body and reaches nothing in normal use, so
  "simpler"
  was only true on the bench. This also removes the one case where a board with
  no external connector had to be recovered through hardware (ADR 0009).
