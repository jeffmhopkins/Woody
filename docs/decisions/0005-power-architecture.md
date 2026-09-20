# 0005 — Power architecture

**Status:** Accepted

## Context

Output requirements are 0–10V on breath and modulation channels and −2 to +7V on
pitch. Both need rails beyond what USB or a single cell provides directly.

## Superseded approach: onboard battery

The original plan was an onboard rechargeable cell with USB charging, making the
instrument fully self-contained. It was abandoned, and the reasoning is kept
here because it was real work and the constraints could return.

From a single Li-ion cell at 3.0–4.2V it would have required:

- A boost converter to roughly +15V, since a +12V output needs headroom above it
- An inverting supply for the negative rail
- A power-path charger IC (BQ24074-class, not a bare TP4056) so the instrument
  runs while charging instead of browning out
- Cell protection, and lithium safety handling for a cell sealed in a wooden box
  held against the player's face

Three problems bit:

- **Noise.** Switching converters put ripple on the rails and that ripple lands
  directly on the CV outputs — as tuning instability on pitch, as hiss on
  breath. The fix (boost to +18V, LDO down to +15V for the analog rail) costs
  efficiency.
- **Power budget.** ESP32-S3 40–80 mA, display backlight 20–100 mA, op-amps
  10–20 mA, and the acrylic LEDs potentially dwarfing all of it at ~60 mA per
  WS2812 at full white. Boosting is lossy. Roughly 400 mA reflected at the cell,
  around 5 hours from 2000 mAh.
- **Weight and balance.** The cell is the single heaviest component, and a
  nose-heavy wind controller is exhausting within twenty minutes.

## Decision

**Power the instrument from the Eurorack supply, over the umbilical (ADR 0004).
No battery.**

The rack already provides ±12V, regulated and filtered. The instrument takes
+12V up the cable and derives 3.3V locally with a small buck converter.

### Physics settles the output range

A rail-to-rail op-amp on a +12V rail swings to roughly +11.5V under light load;
conventional parts considerably less. **0–12V is not achievable from rack power
— the design target is 0–10V.** That is also what Eurorack inputs actually
expect, so the outputs are now in spec rather than above it.

Pitch at −2 to +7V is comfortable on ±12V with ample headroom.

A local boost in the module could raise the rails, but it would reintroduce
exactly the switching noise this decision escapes. Not worth it.

### The rail that matters is 5 V, not 3.3 V

An earlier revision of this ADR specified a 12 V to 3.3 V buck. **That is
wrong**, and the reason is the breath sensor.

The MPXV4006GP is a 5 V part outputting **0.2–4.7 V** (ADR 0003). A buffer
running on 3.3 V would clip the top 30% of the breath range. So the analog front
end needs 5 V, and a rail-to-rail op-amp on 5 V reaches 4.7 V with margin to
spare.

Feeding the dev boards 5 V is also the right way round. Both carry their own
3.3 V regulators and their own USB power paths; driving their `5V`/`VBUS` pins
lets that circuitry do its job, rather than backfeeding a `3V3` pin and
contending with USB when it is plugged in for flashing.

### Power tree

```
umbilical +12V ──┬── WS2815 LED strips          (direct, no conversion)
                 │
                 ├── 12V→5V buck ──┬── display board  5V pin
                 │                 ├── real-time board 5V pin
                 │                 ├── MPXV4006GP breath sensor
                 │                 ├── breath buffer op-amp (RRIO, must reach 4.7V)
                 │                 └── LED data level shifter
                 │
                 └── polyfuse / input filter at entry

real-time board 3V3 out ──┬── 74HC165 chain
                          ├── breath ADC
                          └── I2C pull-ups
```

**3.3 V does not need its own converter.** The loads on it are the shift register
chain (microamps), the ADC (milliamps) and pull-ups, all comfortably inside the
headroom of the real-time board's onboard regulator.

**Fuse the instrument at the umbilical entry.** A short inside the instrument
otherwise pulls on the rack's +12 V rail and can brown out every other module in
the case. A polyfuse is cheap insurance for a fault that takes down more than
just this project.

### Power switch on the instrument

**Switch the buck converter's enable pin, not the +12 V rail.**

The instrument draws a few hundred milliamps at 12 V. Breaking that with a panel
switch means a switch rated for it, arcing over time, and a fat conductor routed
to wherever the switch sits. Switching the regulator's `EN` pin instead carries
no current at all, so it can be a tiny slide switch anywhere convenient, wired
with signal-gauge wire.

Placement has to be **reachable but not reachable by accident** — there is very
little free surface on a body whose top face is a key run and whose underside
carries thumb keys. The upper section above the left hand, or the tail below the
right, are the candidates.

This does not replace the switch on the module panel (ADR 0004). That one is a
hard power cut at the source; this one is a local enable. Both are cheap and
they do different jobs.

**Pull down the module's breath receive input**, so that an instrument which is
switched off — or unplugged — presents 0 V rather than a floating buffer output.
One resistor, and it means powering down the instrument silences the patch
instead of leaving a stuck level (ADR 0003).

### USB power for the bench, not as a feature

**OR the umbilical power with USB power** — it costs a diode, and it means the
instrument runs on the bench during development without a rack attached. That
is worth a diode.

It is not a standalone mode and should not be designed toward. The instrument's
outputs are CV; unplugged from the module it has nowhere to send them.

## Consequences

- The highest-risk electrical subsystem in the project is deleted outright.
- The instrument is tethered during CV use. Accepted — it is playing into a rack.
- Rack current draw needs budgeting, including the acrylic LEDs, which are the
  least predictable line item.
- Balance is no longer dominated by a battery, but strap attachment points still
  need designing into the oak rather than being added later — with left-thumb
  keys on the underside, the left hand both supports and actuates.
