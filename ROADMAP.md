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
| E1 | Board bring-up | Waveshare ESP32-S3-Matrix + LilyGO T-Display-S3 AMOLED (ADR 0008). Both running; **PSRAM confirmed quad, not octal**, and **idle current measured** before the carrier is laid out (ADR 0007) |
| E2 | Breath sensing | **Port orientation confirmed with a syringe first** — a reversed DP reads zero, not backwards. Then **a human plays it for 20 minutes** through a real mouthpiece, tube and trap — not a syringe. Ambient zeroing tracks, no condensation artefacts. **The restrictor is sized by ring-down, not by frequency**: tap the mouthpiece end and watch the sensor settle — one time constant, or a decaying oscillation that needs a denser plug. The 214–429 Hz pipe mode is below the filter corner and independent of trap volume, so it is damped, not placed (ADR 0003). **Also settles the tube bore** by playing a bare tube in two or three sizes. Sensor + ADC at the bottom with the real-time board |
| E3 | IMU | Tilt and roll angles read reliably at rate |
| E4 | Key scan | 74HC165 chain reads all switches; debounce asymmetric (instant press, filtered release) |
| E4b | **Inter-MCU link** | Framed UART between the two boards, status flowing, logic-analyser clean (ADR 0013) |
| E5 | **USB MIDI out** | Plays into a DAW. Fingering table exercised. First playable milestone |
| E6 | Module power | ±12V from rack via keyed header + reverse protection, local 5.25V DAC regulator and bus +5V logic rail up, input filtering, load switch limits and ramps the umbilical feed, no noise injected back into the rack |
| E7 | DAC raw | Commanded codes produce expected voltages on the meter, all six channels |
| E8 | Pitch channel scaled | Raw analog gain and offset trimmed to target, linear across the span. The 5%-over kludge is deleted — trimmers go both ways (ADR 0006) |
| E9 | **Pitch calibration** | Two-point fit stored in NVS; 1V/oct verified against a real VCO, not just a meter, loaded the way it will be played (ADR 0006) |
| E10 | Remaining channels | Analog breath stage: differential receiver, gain/offset knobs, DAC-driven ambient zero. Four mod channels trimmed |
| E11 | Umbilical link | SPI **at 2 MHz** (not the stale 0.6 MHz — see ADR 0004; the old figure came from a 2 kHz rate and does not close at 4 kHz) and the analog breath pair over the real cable at length, **on the T568B pin mapping in ADR 0004** — the mapping is reasoned, not measured. Breath output clean while display, LEDs and WiFi are exercised (ADR 0003) |
| E12 | Module PCB + panel | 8HP panel cut, module assembled and racked. etherCON braced to the PCB — good practice at 8HP rather than the structural necessity it was at 6HP (ADR 0004) |
| E13 | Carrier PCB | **Passive** carrier: dev boards plug in, carrier holds shift registers, ADC, buffer, level shifter, regulator, connector. No MCU, no USB, no RF on it (ADR 0013) |
| E14 | **Carrier re-validation** | E1–E11 re-run on the carrier, not on dev boards. Everything before this was proven on a different physical thing |

**E9 is the milestone that decides whether this is an instrument or a thing
that is always slightly out of tune.** Verify against a VCO — and against the
VCO **loaded the way it will be played**, because E9 will otherwise pass while
being wrong (ADR 0006).

## Track M — Mechanical

The envelope is set at 18 × 2.25 × 1.5 in (ADR 0009). Keys run in a **single
line** down the body, flute-style, with short sections above and below the key
runs — which is what makes 18 inches workable.


| ID | Milestone | Done when |
|---|---|---|
| M1 | Switch characterisation | **Cutout is 14.0 × 14.0 mm**, measured from a working KS-33 build ([reference](docs/reference/ks33-geometry.md)); body geometry from Gateron's STEP model, not calipers. Test coupon cut at ±0.1mm around 14.0 to find the *achieved* fit in real material; retention verified by hand; **bounce and the actuation/reset hysteresis gap scoped** on fast press, slow press, fast release, slow release and a worn switch — neither is published; **action assessed by hand** — fingertip vs thumb-tip, and whether the four thumb keys want a lighter spring than the eleven finger keys |
| M2 | Layout mule | Full key count on a laser-cut plate, hand-wired, mounted to a mock body; playable |
| M3 | Layout locked | Ergonomics settled after 2–3 iterations of M2. No aluminium cut before this |
| M4 | Stack design | Full laminated stack in CAD, every layer a 2D part, **modelled against the real KS-33 STEP solid** rather than a nominal box (ADR 0002) |
| M5 | Aluminium top plate | Cut, fitted, switches retained solidly, **bonded to `PWR_GND`**. Not before E13 — see the ordering rules below |
| M6 | Body | Oak top and bottom, frosted acrylic sides, LEDs, strap points, **tail matrix window + diffuser and USB-C slot** (ADR 0009) |
| M7 | Integration | Electronics mounted in the body, umbilical connector fitted and strain-relieved |
| M8 | **Pre-bond gate** | Assembled but **not bonded**. Full E11 breath-noise test re-run on the *final* harness, **thermal soak at the lighting clamp, watching temperature *and the breath zero* at the sensor**, two-hour play test, failure injection, self-test, **pitch scoped while the LEDs sweep** (ADR 0006 — the one test the plan was missing), and **recover both boards through the service header** so the last route in is known good, not assumed (ADR 0009). Nothing closes until this passes |

**M1 no longer gates M4.** An earlier revision made the cutout measurement the
single most important input to the mechanical design, on the assumption it could
only come from calipers. Gateron publishes the drawing and a STEP model
(ADR 0002), so **CAD can start now** — M1 narrows to confirming the *achieved*
fit in real material, and to the two timing figures nobody publishes.

**Nothing expensive gets cut before M3.** The ergonomic iteration ladder is
paper at 1:1, then laser-cut acrylic, then aluminium — cheapest first, and
every expensive mistake made in the cheap material.

### Three ordering rules a design review found violated

**M5 must not precede E13.** As originally sequenced, the aluminium plate — the
most expensive irreversible part — was cut in Phase 3, while the carrier PCB it
has to accommodate was not designed until Phase 4. Cut the plate after the
carrier layout exists.

**The body does not close until the carrier is revision-final and burned in.**
E13 and M7 sat in the same phase with a hard dependency in one direction, and
the carrier *will* spin at least once — the SPI split alone changes its
topology. A bonded body around a board that needs a revision is the one
unrecoverable mistake available in this project.

**M8 exists because E11 tests a topology that does not survive to the finished
instrument.** At E11 the LED strips are not installed — they arrive at M6 — and
the body is not bonded, so the loom under test is not the final loom. The single
test that validates the entire analog-breath decision was running against a
configuration that changes afterwards, and could not be re-run once bonded.
**This was the most important missing milestone in the project.**

### Why M1 measures slow presses, not just bounce

The release window was being sized from the wrong number. For an MX-style switch
the dominant release-side effect is not contact bounce — it is the **gap between
the actuation point and the reset point**. A slow, deliberate release, which is
exactly what a woodwind player does on a legato phrase, can park the plunger
inside that gap and chatter for tens of milliseconds. Gateron publishes neither
figure for the KS-33, so both have to be measured, on a worn switch as well as a
fresh one.

**And release latency is not free on a woodwind.** On a keyboard, filtering the
release costs nothing because the note is already sounding. Here fingerings are
combinational: **lifting a finger is how you start the next note.** A 10 ms
release window delays that new note by 10 ms, landing squarely in the territory
the attack-latency work exists to protect.

So: **apply the release filter to the note decision, not to each key
independently.** A key that opens while others close is part of a transition,
not a release, and should not be filtered as though the phrase were ending.

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
| F9 | **Matrix surface** | 8×8 as a generic assignable sink: breath by default, other sources and render modes from config. Alarm states preempt and cannot be configured off (ADR 0014) |
| F8 | Persistence | Config and calibration in NVS; presets |

---

## Phase view

| Phase | Contains | Outcome |
|---|---|---|
| **0** | This repository | Decisions recorded, structure in place |
| **1** | E1–E5, M1–M2 | Playable USB MIDI instrument on a test plate |
| **2** | M3, E6–E9 | Layout locked; pitch CV calibrated and accurate |
| **3** | E10–E12, M4 | Module complete and racked; stack designed. **M5 moves to Phase 4** — the plate is cut after the carrier layout exists |
| **4** | E13, E14, M5–M7, M8 | Carrier built and re-proven; plate cut; real instrument in a real body, validated before bonding |
| **5** | F4–F9 | Routing matrix, web config, monitoring, presets, matrix surface |

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

## Bench measurements the review asked for

These are not milestones — they are measurements that turn assumed numbers into
known ones. Each hangs off a milestone that is happening anyway. The full
characterisation table lives in
[the latency budget](docs/reference/latency-budget.md); these are the ones that
came out of the analog design review specifically.

| Measure | At | Why |
|---|---|---|
| **Real-time board idle current** | E1 | 64 unlit WS2812C drivers are an estimated ~50 mA and 0.25 W, spent whether or not anything is displayed. The shared lighting budget is sized from this number (ADR 0014) |
| **1:1 paper fit check, both faces** | M4 | The etherCON flange against a 40.34 mm 8HP panel *and* against the 57 × 38 mm instrument tail beside the USB-C slot. Comfortable at 8HP; the tail is now the tight one (ADR 0004, ADR 0009) |
| **Matrix diffusion prototype** | M6 | Can an 8×8 at 2.6 mm pitch stay pixel-distinct through a window, or only as a blurred bar? Decides whether the 2-D IMU assignment is usable (ADR 0014) |
| **Interior temperature rise under load** | M8 | The lighting budget is set from an estimated 3 K/W. Soak with strips and matrix at the clamp, and measure at the breath sensor (ADR 0014) |
| **Cold-start warm-up sweep** | E2 | Run the sensor from cold through 20 minutes of playing. Output that *falls* under warming is a blocked reference chamber; output that *drifts* is ordinary thermal offset (ADR 0003) |
| **Breath zero vs cavity temperature** | M8 | The DP's reference port is open to the cavity, so the cavity must leak. Watch the zero during the same soak — a walking zero means it is sealing more than assumed. **M8 is pre-bond, so a vent can still be added** (ADR 0003) |
| **PSRAM mode on the ESP32-S3-Matrix** | E1 | Quad leaves 16 broken-out GPIO; octal would consume GPIO33–37 and leave exactly 12 with nothing spare. **The carrier pin map depends on this** (ADR 0007) |
| **DAC saturation vs AVDD** | E7 | The output span *is* the supply. Record the actual saturation code at the actual rail rather than claiming +7 V (ADR 0006) |
| **Pitch DC load sweep: open / 100k / 50k / 33k** | E9 | Quantifies the 1 kΩ divider error against the real patch, and tells you how much a re-mult actually shifts tuning (ADR 0006) |
| **Pitch stability into worst-case cable capacitance** | E9 | Confirms the plain series RC is unconditionally stable where an in-loop version would not have been |
| **Inrush with a current probe, on switch-on *and* hot-plug** | E6 | Sizes the load switch's current limit from measurement rather than from a guess (ADR 0005) |
| **Gate-press-while-moving IMU test** | E3 | The failure mode that killed the bias-snapshot proposal. Press the gate mid-gesture and check the stillness-gated estimator does not adopt motion as bias (ADR 0007) |
| **Key-chain error counter over an hour, LEDs and WiFi active** | E4 | The marker pattern's whole purpose. A non-zero count says the looms need work while the body is still openable (ADR 0001) |
| **Helmholtz restrictor sizing** | E2 | Trap volume and response time are coupled. Size the orifice to put the resonance above the 500 Hz filter corner (ADR 0003) |

**The key-chain and restrictor measurements are the time-critical ones** — both
inform wiring and plumbing that get sealed inside a bonded body at M6.

## Failures that are silent, and what makes them loud

A design review ranked the project's failure modes by *how quietly they fail*.
The quiet ones are the expensive ones, because they get blamed on the player or
on firmware for years. All three fixes are firmware and all three are free.

| Failure | Why it is silent | Made loud by |
|---|---|---|
| **Blank or corrupt NVS → default calibration** | The instrument plays. It sounds like an instrument. It is just badly out of tune, with no indication anything is wrong | CRC the calibration blob; a hard **UNCALIBRATED** state on the display the player cannot miss |
| **Stuck-closed switch** | Does not kill a note. Silently returns a *different* note for every fingering that key participates in — presents as "some fingerings feel wrong", which is unfalsifiable by ear inside a body that cannot be opened | Flag any key closed at boot, or held beyond N seconds, as suspect and report it |
| **Stale breath zero** | Thermal drift over a session moves the floor, and the player compensates with their diaphragm without noticing | Continuous auto-zero (ADR 0006), plus showing the current zero on the display |

A fourth is hardware and already handled: a corrupted key-chain read becoming a
spurious note, made countable by the marker pattern (ADR 0001).

## Open items blocking work

| Blocks | Question | Tracked in |
|---|---|---|
| M4, M5 | **Plate thickness** — 1.5 mm with lamination stiffening, or 2 mm with a structural backer. Needs the clip dimension from Gateron's drawing | [ADR 0002](docs/decisions/0002-key-switches-and-mounting.md) |
| M4 | CAD tool — Fusion, FreeCAD, or neutral STEP in `mechanical/cad/` | [ADR 0009](docs/decisions/0009-enclosure-construction.md) |
| M4 | Oak thickness for the bottom panel, which sets thumb key travel | [ADR 0009](docs/decisions/0009-enclosure-construction.md) |
| E4b | Inter-MCU frame format and protocol versioning | [ADR 0013](docs/decisions/0013-two-mcu-split.md) |
