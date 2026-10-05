# 0015 — One MCU, no display board

**Status:** Accepted. **Amended 2026-10-04** (issue #37): Wi-Fi in a configuration mode only, the tail-face USB-C removed, MIDI out on a TRS jack (*Amendment, 2026-10-04*).

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

> **Amended 2026-10-04 (issue #37):** the tail-face USB-C and `CBL-USB-EXT`
> are gone. Configuration and updates are planned over Wi-Fi, in a
> configuration mode that does not run the output loop. MIDI leaves on a TRS
> jack, and USB MIDI is not built. *Amendment, 2026-10-04*, below.

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
  to update over; firmware goes on over USB. *(Reinstated for configuration
  mode only by the amendment of 2026-10-04, below.)* The recovery ladder in
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

## Amendment, 2026-10-04 — a radio for configuration only; the external USB closes; TRS MIDI out

**Decided by the owner, 2026-10-04** (issue #37), in four steps:

> "What's the ability for us to write a firmware that can do over-the-air
> updates so we can close up the USB all together? The only requirement then
> would be a TRS connector on the bottom for midiout, and adding a midi circuit
> to the main board"
>
> "the idea is probably we have a button configuration that we press that puts
> it into configuration mode where Wi-Fi is turned on but Wi-Fi isn't turned on
> all the time"
>
> "TRS should be able to be swapped from TRS a to b, ideally just in firmware"
>
> Of the jack: "I think you need it on the bottom face, and then just do a
> connector to the main board instead of actually mounting it to PCB". Of the
> firmware: "Let's not worry about the firmware now. Just add the capability".

### What is decided

1. **The ESP32-S3's Wi-Fi is used again, in a configuration mode only.** It is
   entered by a key combination and is always a fresh boot. **The radio is off
   at every boot.** The output loop does not run in it, and the DAC is held at
   a safe state. This decision's objection to Wi-Fi was bursts on the same
   chip, regulator and ground as the live 4 kHz loop and breath ADC. That case
   cannot arise, because the loop is not live while the radio is on.
2. **Firmware updates go over the air** into the inactive app slot, with the
   bootloader's rollback, from a page the instrument serves to a phone.
   **The firmware is deferred** (owner: "Just add the capability"). The
   hardware already supports it: the Matrix's ESP32-S3 has the radio and the
   flash. The draft design is a research note,
   [`docs/research/2026-10-04-config-mode-ota-draft.md`](../research/2026-10-04-config-mode-ota-draft.md),
   not yet this corpus's authority. `firmware/README.md` records what the
   hardware now requires.
3. **The tail face's USB-C extension is removed**: `CBL-USB-EXT`, the slot,
   its overmould pocket and the lead. The Matrix's own USB-C stays, as a
   recovery and bench port reached with the lid off. The carrier's slot under
   the receptacle and the oak's pocket over a plug are kept for it
   (`mechanical/drc.echo` *"recovery USB-C plug clear of the oak top"*).
4. **MIDI out on a 3.5 mm TRS jack through the oak bottom**, in the lane
   beside the etherCON the USB-C receptacle stood in: a panel-mount jack on a
   lead to a header on the main board's freed tail corner. The circuit is
   CA-033's 5 V row, driven by two spare gates of `U-LVLSHIFT`. TRS Type A or
   B is a firmware setting (owner, above), because the two lines are
   identical. The jack is [`hardware/carrier/midi-out/`](../../hardware/carrier/midi-out/midi-out.md),
   which owns the derivation.
5. **USB MIDI is not built into the instrument.** Nothing claims the USB-OTG
   peripheral, so USB-Serial-JTAG is alive at every boot.

### What it changes

- **The recovery ladder** (`firmware/README.md`) gains OTA rollback at the
  top, once the firmware exists. Its wired rungs are reached with the lid off
  (ADR 0025): the Matrix's own USB-C, the console header, and BOOT and RESET.
  **What is lost** is a cheap wired path for a failure rollback cannot reach,
  such as a broken Wi-Fi image that validated, or a bootloader or partition
  table flashed wrong.
- **Live configuration while playing is not reinstated.** USB allowed it.
  Configuration mode stops the loop.
- **Ground:** with no USB lead to a computer the instrument has no second path
  to the rack's ground. A MIDI receiver is opto-isolated and does not ground
  pin 2 [ds connectors/MIDI-CA-033-ELECTRICAL-SPEC-UPDATE-2014.pdf p.3]. ADR
  0027's caveat about a USB lead becomes a bench-only one.
- **The Matrix ribbon** carries the MIDI tip line on `J-MCU` pin 23, which
  was spare since 2026-10-03, and the ring line on pin 5, IO2, the spare
  shield. Pin 24 cannot be routed on the carrier (`midi-out.md`, *The ribbon
  conductors*).
- **The Matrix ribbon's closed fold has more room.** The extension's plug set
  its forward limit until now. The carrier keeps its height (drc.echo
  *"Matrix ribbon closed: its folds between the sockets"*).
- **The main board gains `J-MIDI` and its parts in the freed corner.** They
  are not yet placed on the layout, which issue #35 has open.

### Open, and what decides each

| Open | What decides it |
|---|---|
| The loop current at the 5 V row's low edge (`midi-out.md`, *The loop current*) | An E-test with a 6N138 DIN interface through an RP-054 adapter, and a TRS synth |
| Type B's switching line (IO2) beside `IO1` and `IO7` on the ribbon | No marker errors while playing in Type B (E11/E14) |
| The jack's panel thickness, and its counterbore | The part in hand, and a test hole in the chosen oak |
| `J-MIDI`'s placement and routing | The main board's layout, after #35 |
| Configuration mode and OTA | The firmware, deferred |
