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

So: **one run per side, chained as a single data line.** Addressable strips
chain natively, so both sides cost one GPIO. Roughly 420 mm of usable run per
side, 0.84 m total.

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

Keep the LED runs and their return physically away from the breath buffer and
its wiring inside the instrument.

## Open

- Density, pending the diffusion test.
- What the lighting actually does. Breath level is the obvious driver; note,
  active mod channels and config-mode state are all available.
