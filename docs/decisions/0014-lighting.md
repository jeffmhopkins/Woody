# 0014 — Lighting

**Status:** Accepted

## Requirement

An addressable LED run down the length of the instrument, driven by breath and
other instrument state, diffused through the frosted acrylic side panels
(ADR 0009).

## Geometry: two runs, one chain

A single strip "down the middle" is not available — switch bodies occupy the
centreline for the full length of both key runs (ADR 0009, ADR 0013). The free
volume is the **two side channels flanking the switch column**, which is also
exactly where the light needs to be: immediately behind the acrylic it has to
illuminate.

So: **one run per side**, roughly 420 mm each, 0.84 m total.

**Both channels carry LEDs, and the wiring looms share them.** ADR 0009
previously assigned these same channels to the looms — a contradiction between
two accepted decisions. It resolves because the breath sensor moved to the
bottom of the instrument (ADR 0003), so no analog signal traverses the body and
the looms carry only digital traffic. The instruction below to keep LED runs
away from the breath wiring now costs nothing, because the breath wiring is not
in the body.

### Two independent strips, not one chained pair

Three ways to wire two runs:

| | GPIO | Crossover wire | Sides can differ |
|---|---|---|---|
| **A** — chained, data loops end to end | 1 | **yes** | yes |
| **B** — two independent data lines | 2 | no | yes |
| **C** — parallel, same data to both | 1 | no | no, always mirrored |

**B.** The deciding factor is physical: chaining needs a data wire crossing the
cavity at one end of the runs, and **both ends are the congested ones** — the
display board and breath sensor at the top, the real-time board, IMU and
umbilical connector at the bottom. Adding a signal wire across either, inside a
bonded stack that cannot be reopened, is a liability for no benefit.

Two data lines cost one extra GPIO, against roughly 17 broken out and 12 needed
on the real-time board (ADR 0007). The ESP32-S3 drives both on separate RMT
channels without effort.

Splitting also means each run installs and is replaced independently during
assembly, and each gets its own power feed, which halves the current per tap.

**C is the fallback if GPIO ever gets tight.** A single GPIO can drive both
strips' data inputs in parallel with no extra parts — each strip's first LED is
a high-impedance input. The cost is that the two sides can never show different
content, which for a symmetric instrument light is probably not a loss. It is
worth knowing the option exists rather than treating one GPIO as a constraint.

Buy one 1 m strip and cut two 420 mm runs from it.

## Rail: use a 12 V strip

The instrument has +12 V from the umbilical and derives 3.3 V locally
(ADR 0005). A 5 V strip would need a third rail for nothing but LEDs.

**WS2815 (12 V, individually addressable)** avoids that, and wins on three
counts:

- **No extra rail.** Runs directly from the umbilical supply.
- **Half the current** for the same light, because the power arrives at 12 V
  rather than 5 V.
- **Backup data line.** WS2815 carries a redundant data path, so a single failed
  LED does not kill everything downstream of it. In a bonded laminated body that
  cannot be opened casually (ADR 0002), that matters more than it would in a
  serviceable build.

Against: slightly less common and a little more expensive than WS2812B/SK6812.
Worth it here.

## There is no LED driver, but there is a level shifter

Addressable strips carry a controller in every LED, so no external constant-
current driver, no multiplexing and no PWM generator is needed. One GPIO per
strip is the whole interface.

**What is needed is level shifting on the data line.** The ESP32-S3 drives
3.3 V logic; addressable strips generally want a logic high near 0.7 × their
supply. A **74AHCT125** is the standard answer — powered from 5 V with TTL input
thresholds, so a 3.3 V input reads as high and it outputs a clean 5 V edge. One
package covers both strips.

**Verify the WS2815's data threshold against its datasheet before committing.**
It is a 12 V part, and if its logic threshold is referenced to 12 V rather than
an internal rail, 5 V shifting will not be enough and the part choice needs
revisiting. Most 12 V addressable strips accept 5 V logic, but "most" is not a
basis for a sealed build.

This is a classic source of intermittent, maddening LED behaviour — strips that
work on the bench and glitch in the build — so it is worth getting right rather
than discovering empirically.

## Power budget, and the cap that is not optional

0.84 m total, by density and use:

| Density | Full white | Single hue, full | Single hue, 40% |
|---|---|---|---|
| 30/m (25 LEDs) | 0.50 A | 0.17 A | **0.07 A** |
| 60/m (50 LEDs) | 1.01 A | 0.34 A | **0.13 A** |

**Eurorack supplies commonly provide 1–3 A on +12 V for the entire case.** Full
white at 60/m would take a third to a whole rail on its own, and it is not a
mode anyone intends to use — but it is one bug away.

**So the brightness cap is enforced in firmware as a hard limit, not exposed as
a setting.** Sum the commanded channels, and clamp before writing to the strip.
A display bug that sets 50 LEDs to white at full brightness must not be able to
brown out the rack, which would take every other module with it.

Realistic use — a single hue tracking breath at moderate brightness — sits
around **0.1 A**, which is unremarkable.

60/m is the sensible default: denser than 30/m for smoother diffusion, and well
inside budget once capped.

## Diffusion is a prototype question

Frosted acrylic close to an LED shows the LED. Even illumination needs either
distance between emitter and diffuser, or enough density that the dots overlap
before they reach it.

The cavity gives roughly 20 mm to play with. Whether 60/m at that distance reads
as a continuous glow or a row of points is not answerable from here, and it is
cheap to settle: a length of strip and an offcut of the intended acrylic,
held at a few distances. Do that before committing to a density or a channel
depth.

Visible points are not automatically wrong — a row of discrete lights can look
deliberate. But it should be a choice.

## Grounding

LED current is switched and pulsed, and its return flows in `PWR_GND` alongside
the instrument's other power current.

**This is precisely why the analog breath channel has its own sense return**
(ADR 0003). Without `AGND`, the light show would appear on the breath CV — a
34 mV ground offset that moves with the animation. The lighting decision
validates that choice rather than complicating it.

The breath buffer and sensor now live at the bottom with the real-time board
(ADR 0003), so there is no long analog run to keep clear of. Keep the LED return
off the analog section's local ground at that end, and give the SPI key chain
its own ground return per signal where it shares a channel with the strips.

## Open

- Density, pending the diffusion test.
- What the lighting actually does. Breath level is the obvious driver; note,
  active mod channels and config-mode state are all available.
