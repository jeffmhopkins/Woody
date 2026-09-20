# Firmware

**Two images** ([ADR 0013](../docs/decisions/0013-two-mcu-split.md)):

- `realtime/` — ESP32-S3. Keys, breath, IMU, DAC loop, USB MIDI. Owns all
  state and persistence. This is the instrument.
- `display/` — the AMOLED board. Panel, WiFi, web app. Renders what it is told
  and forwards what the user does. **Persists nothing.**

Joined by a framed UART. Put a protocol version in the frame header from the
first commit — two images that can drift apart need a way to notice.

PlatformIO, ESP-IDF underneath. Nothing here yet — Track F follows Track E
(see [ROADMAP.md](../ROADMAP.md)).

## Architecture constraints

These come from [ADR 0001](../docs/decisions/0001-mcu-and-board-partitioning.md)
and [the latency budget](../docs/reference/latency-budget.md), and they are not
negotiable without revisiting those:

- **4 kHz loop** for sensor read and DAC update, pinned to one core.
- **Display renders on the other core, on its own SPI host.** A display refresh
  must never block the output loop.
- **Asymmetric key debounce** — fire immediately on press, filter only the
  release. A symmetric window puts its full length into the attack. The release
  window is set from **measured** KS-33 bounce (milestone M1), not from the
  conventional 20 ms the 2021 firmware used.
- **Per-channel smoothing in software**, not in the analog filter. The analog
  filter is fixed; firmware knows what each channel carries.
- **Nothing expressive touches the ESP32's internal ADC.** It is noisy and
  nonlinear, and breath drives a 0–10V output where that shows.
- **WiFi and the display are on the other MCU.** They cannot preempt the output
  loop. What remains is the current transient a transmit burst puts on the
  shared rail, handled with separate regulators rather than by scheduling
  ([ADR 0012](../docs/decisions/0012-configuration-interface.md),
  [ADR 0013](../docs/decisions/0013-two-mcu-split.md)).

## Data, not code

Two things are explicitly configuration rather than compiled constants
([ADR 0010](../docs/decisions/0010-key-layout-as-data.md),
[ADR 0006](../docs/decisions/0006-cv-channel-allocation.md)):

- **Fingering table** — a custom fingering system takes a lot of playing to get
  right, and a recompile per experiment is the wrong loop. It covers the 15
  `note` keys only; the three right-thumb switches are `control` and must never
  enter it (ADR 0010).
- **Routing matrix** — four mod channels, each with source, scale, offset, curve
  and slew.

Both live in NVS and are editable from the display and over USB.

## Bring-up fixtures

Throwaway test firmware for E-track milestones belongs in `fixtures/`, not in
the instrument firmware. It is a tool, not a deliverable.

## Configuration lives on a phone

Config is a web app served from the display board's flash over SoftAP, not a
menu system ([ADR 0012](../docs/decisions/0012-configuration-interface.md)). The
display shows status only.

**Single source of truth:** every config edit round-trips. The phone edits, the
display board forwards, the real-time board validates, applies, persists and
echoes back. The display board never writes authoritative state — two
authorities that can disagree is the failure mode worth designing out.

Build the live-telemetry WebSocket early — it is a test instrument for the
mechanical and calibration work, not just a configuration convenience.

## USB MIDI

A **bring-up tool, not a feature.** Keys, fingering and breath response get
validated in a DAW before any analog hardware exists (milestone E5). The
instrument is a tethered rack device; USB MIDI does not get to constrain the
design.
