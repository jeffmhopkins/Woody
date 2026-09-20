# Roadmap

## Principle: three tracks in parallel, converging late

Mechanical and electrical work are independent until final integration. Running
them in sequence wastes months; the slow track (outsourced cutting, PCB
turnaround) should always be in flight while the other progresses.

| Track | Covers | Gated by |
|---|---|---|
| **M — Mechanical** | Key mounting, layout, laminated stack, body | Switches arriving; key count decided |
| **E — Electronics** | Board bring-up, sensors, ADC, DAC, CV module | Nothing — can start immediately |
| **F — Firmware** | Instrument firmware, routing matrix, UI | Follows E |

Bring-up firmware — the throwaway fixtures that prove a DAC or an ADC works —
is not tracked under F. It belongs to whichever E milestone needs it. F is the
real instrument firmware, and it genuinely is the tail end of this project.

## The shortest path to a playable instrument

Deliberately skips CV entirely:

> **E1 → E2 → E4 → E5 on a bench, mounted to M2.**
>
> Dev board, breath sensor, key scan, USB MIDI, on a laser-cut test plate.

That is a real instrument you can play into a DAW. It validates the ergonomics
and the fingering system with actual playing, and it is a working fallback if
the CV track runs long. Everything else — the module, the aluminium, the wood —
comes after and none of it blocks the others.

---

## Track E — Electronics

The module track (E6 onward) can run start to finish without the instrument
existing. Drive it from any dev board with a test pattern and a multimeter.

| ID | Milestone | Done when |
|---|---|---|
| E1 | Dev board evaluation | Plain ESP32-S3 board + separate display module chosen and running; matches final architecture, not an integrated-screen board |
| E2 | Breath sensing | Analog sensor read through external SAR ADC, ambient zeroing works, stable reading |
| E3 | IMU | Tilt and roll angles read reliably at rate |
| E4 | Key scan | 74HC165 chain reads all switches; debounce asymmetric (instant press, filtered release) |
| E5 | **USB MIDI out** | Plays into a DAW. Fingering table exercised. First playable milestone |
| E6 | Module power | ±12V from rack, input filtering, no noise injected back into the rack |
| E7 | DAC raw | Commanded codes produce expected voltages on the meter, all six channels |
| E8 | Pitch channel scaled | Channel 1 hits −2V and +7V, linear between |
| E9 | **Pitch calibration** | Two-point fit stored in NVS; 1V/oct verified against a real VCO, not just a meter |
| E10 | Remaining channels | Breath 0–10V with working gain/offset knobs; four mod channels trimmed |
| E11 | Umbilical link | SPI over the real cable at length, no errors, module-present detect works |
| E12 | Module PCB + panel | 6HP panel cut, module assembled and racked |
| E13 | Controller PCBs | Custom carrier + satellite boards; replaces the dev board |

**E9 is the milestone that decides whether this is an instrument or a thing
that is always slightly out of tune.** Verify against a VCO.

## Track M — Mechanical

The envelope is set at 18 × 2.5 × 1.5 in (ADR 0009). At that width the hand
clusters can run two columns rather than one, which shortens them
longitudinally and grows the slack in the length budget.


| ID | Milestone | Done when |
|---|---|---|
| M1 | Switch characterisation | KS-33 plate cutout measured with calipers; test coupon cut at ±0.1mm steps; retention verified by hand; **contact bounce scoped** and debounce windows set from the measurement; switch weight variant confirmed and thumb-tip actuation force assessed |
| M2 | Layout mule | Full key count on a laser-cut plate, hand-wired, mounted to a mock body; playable |
| M3 | Layout locked | Ergonomics settled after 2–3 iterations of M2. No aluminium cut before this |
| M4 | Stack design | Full laminated stack in CAD, every layer a 2D part |
| M5 | Aluminium top plate | Cut, fitted, switches retained solidly |
| M6 | Body | Oak top and bottom, frosted acrylic sides, LEDs, strap points |
| M7 | Integration | Electronics mounted in the body, umbilical connector fitted and strain-relieved |

**M1 is the first thing that happens when the switches arrive.** That cutout
measurement is the single most important input to the entire mechanical design;
everything downstream inherits it.

**Nothing expensive gets cut before M3.** The ergonomic iteration ladder is
paper at 1:1, then laser-cut acrylic, then aluminium — cheapest first, and
every expensive mistake made in the cheap material.

## Track F — Firmware

| ID | Milestone | Done when |
|---|---|---|
| F1 | Key and fingering engine | Custom fingering table driven from config, not hardcoded |
| F2 | Breath response | Curve shaping, ambient zeroing, threshold and note gating |
| F3 | Channel output | Fixed-rate DAC loop, per-channel smoothing in software |
| F4 | Routing matrix | Four mod channels: source, scale, offset, curve, slew |
| F5 | **Web config app** | SoftAP, captive portal, web app served from flash. Fingering table, routing matrix, breath curves |
| F6 | Live monitoring | WebSocket telemetry to the phone: breath, IMU angles, commanded CV |
| F7 | Status display | Note, breath, active channels, mode. Status only — config lives on the phone |
| F8 | Persistence | Config and calibration in NVS; presets |

---

## Phase view

| Phase | Contains | Outcome |
|---|---|---|
| **0** | This repository | Decisions recorded, structure in place |
| **1** | E1–E5, M1–M2 | Playable USB MIDI instrument on a test plate |
| **2** | M3, E6–E9 | Layout locked; pitch CV calibrated and accurate |
| **3** | E10–E12, M4–M5 | Module complete and racked; aluminium plate |
| **4** | M6–M7, E13 | Real instrument in a real body |
| **5** | F4–F8 | Routing matrix, web config, monitoring, presets |

## Out-of-order work worth pulling forward

**F6 (live monitoring) is worth building well before its phase.** A phone
showing live breath pressure, IMU angles and commanded CV over a WebSocket is a
test instrument, not just a convenience:

- **M2/M3** — see which keys actually register while trying a layout, instead of
  inferring it by ear
- **E9** — watch commanded against measured while trimming calibration, instead
  of alternating between a meter and a menu
- **E2** — see the breath response curve while playing against it

It depends only on E1 and a WiFi stack, so it can be built as soon as there is a
dev board on the bench.

## Open items blocking work

| Blocks | Question | Tracked in |
|---|---|---|
| E2 | Which breath sensor is actually in hand | [ADR 0003](docs/decisions/0003-breath-sensing-path.md) |
| E12 | Connector choice, pending panel fit check | [ADR 0004](docs/decisions/0004-cv-interface-module.md) |
| E1 | Display type | [ADR 0008](docs/decisions/0008-display-selection.md) |
| E3 | IMU part | [ADR 0007](docs/decisions/0007-imu-selection.md) |
