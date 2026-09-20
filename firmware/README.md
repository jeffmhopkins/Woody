# Firmware

ESP32-S3, PlatformIO. Nothing here yet — Track F follows Track E
(see [ROADMAP.md](../ROADMAP.md)).

## Architecture constraints

These come from [ADR 0001](../docs/decisions/0001-mcu-and-board-partitioning.md)
and [the latency budget](../docs/reference/latency-budget.md), and they are not
negotiable without revisiting those:

- **4 kHz loop** for sensor read and DAC update, pinned to one core.
- **Display renders on the other core, on its own SPI host.** A display refresh
  must never block the output loop.
- **Asymmetric key debounce** — fire immediately on press, filter only the
  release. A symmetric window puts its full length into the attack.
- **Per-channel smoothing in software**, not in the analog filter. The analog
  filter is fixed; firmware knows what each channel carries.
- **Nothing expressive touches the ESP32's internal ADC.** It is noisy and
  nonlinear, and breath drives a 0–10V output where that shows.

## Data, not code

Two things are explicitly configuration rather than compiled constants
([ADR 0010](../docs/decisions/0010-key-layout-as-data.md),
[ADR 0006](../docs/decisions/0006-cv-channel-allocation.md)):

- **Fingering table** — a custom fingering system takes a lot of playing to get
  right, and a recompile per experiment is the wrong loop.
- **Routing matrix** — four mod channels, each with source, scale, offset, curve
  and slew.

Both live in NVS and are editable from the display and over USB.

## Bring-up fixtures

Throwaway test firmware for E-track milestones belongs in `fixtures/`, not in
the instrument firmware. It is a tool, not a deliverable.

## USB MIDI

Present, and the bring-up path for the whole instrument — keys, fingering and
breath response get validated in a DAW before any analog hardware exists. Also
gives the instrument a standalone mode away from the rack
([ADR 0005](../docs/decisions/0005-power-architecture.md)).
