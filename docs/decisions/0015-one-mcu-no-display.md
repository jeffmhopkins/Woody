# 0015 — One MCU, no display board

**Status:** Accepted

Supersedes [ADR 0008](0008-display-selection.md) (display selection),
[ADR 0012](0012-configuration-interface.md) (configuration over WiFi) and the
two-MCU split of [ADR 0013](0013-two-mcu-split.md). Decided by the owner,
2026-09-26.

## Context

ADR 0013 split the instrument across two ESP32-S3s: the real-time board (the
Waveshare ESP32-S3-Matrix — keys, breath, IMU, the DAC link, USB MIDI, and
the 8×8 LED matrix) and a display board (the LilyGO T-Display-S3 AMOLED —
the status screen, WiFi, and the phone web app of ADR 0012), joined by a
UART and a nine-conductor loom.

By the time the body was being laid out in CAD (`mechanical/`), the display
board had become the most expensive thing in the instrument in every
currency the layout is short of:

- **Length.** On the underside at the mouth end it could not share space with
  the left-thumb arc, so it added roughly its own length in front of the keys
  — the model's "what the mouth end needs" named it.
- **Parts.** A second dev board, a second regulator with its input capacitor
  and OR diode, local bulk capacitance for its WiFi bursts, a nine-conductor
  loom, a keyed IDC header, a flat-flex link and header sockets.
- **Heat.** It was the hottest single item in the body, the reason ADR 0003
  pushed the breath sensor away from it.

Meanwhile the 8×8 LED matrix on the top face (ADR 0014, ADR 0009) had become
a real display in the player's downward glance.

## Decision

**Remove the display board. One MCU — the ESP32-S3-Matrix — and the 8×8 LED
matrix is the instrument's only display.** (Owner: "remove the upper display
esp32/display. We can do all this with the matrix led, keep things more
compact and cleaner.")

**Configuration is over USB only, and the instrument has no radio.** The
ESP32-S3-Matrix's own USB-C port, already brought to the tail face on an
extension (`CBL-USB-EXT`), carries configuration from a computer — a browser
page or a host tool — over USB-Serial-JTAG by default, and as SysEx when the
player has turned USB MIDI on. `firmware/README.md` owns the transport, and
why it must not make USB MIDI the default. WiFi and BLE stay off. (Owner, choosing "USB only" over
WiFi on the matrix board's ESP32 and over Bluetooth.)

### What the matrix shows

The status role ADR 0008 gave the AMOLED — current note, breath level,
active channels, mode — moves to the 8×8 matrix, within ADR 0014's lighting
budget and its "total current held constant" rule. What it can and cannot
show at 8×8 is a firmware design question (F7); the owner's judgement is that
it is enough.

### What goes

- **The display board** (`U-DISP`) and its spare.
- **UART1 and the display loom** (`J-DISP`), and the header sockets for a
  second board. IO5 and IO6 on the ESP32-S3-Matrix become spare GPIO.
- **The second regulator** (buck B), its OR diode and input capacitor, and
  `C-BULK-DISP`. One R-78E5.0 feeds the dev board, the matrix and the level
  shifter.
- **WiFi, the SoftAP web app, and OTA update** (ADR 0012). There is no radio
  to update over; firmware goes on over USB. The recovery ladder in
  `firmware/README.md` loses its first rung (OTA rollback) and starts at
  USB-Serial-JTAG.
- **The display band** at the mouth end of the body. The CAD derives the
  length, so the body simply got shorter (`mechanical/drc.echo`, "overall
  length").
- The service header shrinks to the one board's console pair
  (`hardware/carrier/service-uart/`).

### What stays

ADR 0013's **build approach** stands for the board that is left: the dev
board as a module, no custom ESP32-S3 layout, a passive board for everything
else (now the centre board, `mechanical/DESIGN.md`). ADR 0013's reasoning
that the real-time board owns everything that matters is now simply true of
the only board.

## Options considered

- **WiFi on the ESP32-S3-Matrix, pinned to the other core.** Keeps the phone
  web app. Rejected by the owner in favour of no radio: it puts WiFi bursts
  on the same chip, regulator and ground as the 4 kHz output loop and the
  breath ADC, the exact thing ADR 0013 split the boards to avoid.
- **Bluetooth only.** Rejected as the primary path in ADR 0012 already: iPhones
  do not support Web Bluetooth.
- **Keep the display board, move it.** Every placement costs length or
  height somewhere, and it would still be the second board, second regulator
  and the loom.

## Consequences

- **The load table in ADR 0005 is an upper bound until E6 measures it.** It
  included the display board, whose share was only ever estimated
  (`hardware/carrier/power-entry-instrument/power-entry-instrument.md`), so
  the register's `umbilical-current` is marked blocked on that measurement
  rather than re-derived from a guess.
- **ADR 0003's thermal argument for the breath sensor's placement** loses its
  main heat source. The analog-routing argument still stands.
- **The configuration surface is a computer, not a phone.** Anything that
  assumed a phone at the rack (ADR 0012, ROADMAP F5) is gone.
- **Hardware pages not yet brought into line with the centre board and this
  ADR** are listed in `mechanical/DESIGN.md`.
