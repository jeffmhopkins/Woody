# Woody

A custom electronic woodwind instrument: a wooden body with mechanical key
switches, breath and motion sensing, driving control voltage into a Eurorack
system.

This is the second iteration of the
[Open Woodwind Project](https://github.com/jeffmhopkins/Open-Woodwind-Project)
(2021), rebuilt from scratch with modern components. The previous version was a
Teensy 3.2 with capacitive touch keys and an onboard synthesizer. This one keeps
almost none of that: mechanical switches instead of capacitive pads, an ESP32-S3
instead of a Teensy, CV output instead of an onboard synth engine.

**Status: Phase 0.** Design decisions are being recorded; no hardware has been
built. Switches and keycaps are purchased. See [ROADMAP.md](ROADMAP.md).

## What it is

The project splits into two physical deliverables that meet over a single cable:

| | **Controller** | **Interface module** |
|---|---|---|
| Form | Laminated wood/aluminium/acrylic body | 6HP Eurorack module |
| Contains | Keys, breath sensor, IMU, display, MCU | DAC, analog scaling, jacks, knobs |
| Domain | Digital | Analog, ±12V |
| Primary risk | Mechanical and ergonomic | Analog precision |

The controller is purely digital and carries no analog signal path and no
battery. It takes power from the rack over the umbilical and sends channel data
down the same cable as SPI. All analog work happens in the module, inches from
the jacks it drives.

These two can be developed and tested independently, and the module can be
brought up standalone on a bench long before the instrument exists.

### Output

Six CV channels from the module:

- **Pitch** — dedicated, 1V/oct, −2V to +7V, per-unit calibrated
- **Breath** — dedicated, 0–10V, with panel knobs for gain and offset
- **Mod 1–4** — assignable; source, scale, offset, curve and slew configured
  on the instrument's own display

USB MIDI exists on the controller but is a development and practice
convenience, not a product feature. It is how the keys, fingering and breath
response get validated before any analog hardware is built, and it gives the
instrument a standalone mode when it is away from the rack.

There is no onboard synthesizer. There is no battery.

## Repository layout

```
docs/decisions/   Architecture decision records — the important stuff
docs/log/         Dated build log
docs/reference/   Latency budgets, fingering notes, specs
docs/research/    Component comparisons and datasheet notes
hardware/         BOM, schematics, PCB, split by board
firmware/         ESP32-S3 firmware (PlatformIO)
mechanical/       CAD source, 2D cut exports, drawings
config/           Key layout and routing, as data
tools/            Host-side utilities
```

## Where to start reading

1. [ROADMAP.md](ROADMAP.md) — the three tracks and what "done" means for each
2. [docs/decisions/](docs/decisions/) — every choice made so far, and why
3. [docs/reference/latency-budget.md](docs/reference/latency-budget.md) — the
   constraint that shapes most of the electrical design

## Licensing

Not yet decided — see
[ADR 0011](docs/decisions/0011-licensing.md). The previous project's firmware
was GPLv3.
