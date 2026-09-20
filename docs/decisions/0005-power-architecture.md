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

### The breath sensor is not on the 5 V rail at all

The section below was written when the breath sensor shared the buck's 5 V rail
with both dev boards. **It no longer does.** The MPXV4006GP is ratiometric to
its supply and the breath path is analog to the jack, so it runs from a REF5050
precision reference buffered by half an OPA2197, straight off +12 V — see
ADR 0003. The breath buffer moved to that same +12 V package.

What remains below still holds for what is left on the 5 V rail: the two dev
boards and the LED data level shifter.

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

### Why 12 V goes up the umbilical, not 5 V

The rack supplies a regulated +5 V rail alongside ±12 V, so sending 5 V up the
cable and deleting the instrument's buck converter looks attractive. **The drop
maths says otherwise.**

The instrument's load is roughly 3 W. Over 2 m of 24 AWG, round trip ~0.34 Ω:

| Delivered at | Current | Drop | Arrives as | Error |
|---|---|---|---|---|
| **12 V** | 250 mA | 84 mV | **11.92 V** | **0.7%** |
| 5 V | 600 mA | 202 mV | 4.80 V | 4.0% |

The same power at a lower voltage means proportionally more current, and drop
scales with current. At 5 V the instrument would see **4.80 V** — inside the
MPXV4006GP's 5.00 ±0.25 V specification with no margin left, and that sensor is
**ratiometric**, so supply variation reads directly as breath variation.

This is simply why power distribution uses higher voltages, and it applies at
two metres as much as at two kilometres.

Two further reasons the question does not arise:

- **The WS2815 strips need 12 V anyway** (ADR 0014). A 5 V-only umbilical would
  force 5 V strips, giving up the backup data line that matters in a sealed
  body — and drawing more current while doing it.
- **The R-78E5.0 is a 3-pin through-hole module**, among the lowest-effort parts
  in the design. Deleting it saves almost no build effort to begin with.

### The module's 5 V splits: bus rail for logic, local regulator for the DAC

The module sits in the rack on a short ribbon with negligible drop, so the bus
+5 V rail is free and convenient. It is used — but **only for the 74AHCT125
level shifter**, around 10 mA.

**The DAC gets its own LM317LZ set to 5.25 V, off the protected +12 V rail.**
The DAC8568's full-scale output *is* its supply, so a rail the rack is allowed
to move ±5 % moves the top of the pitch range and the pitch calibration with it.
That belongs on a regulated supply of its own. Reasoning in full in ADR 0004.

The target rack supplies +5 V, so the level shifter's rail is a **requirement,
not an option**. No jumper, no unpopulated fallback footprint. A module that
also worked in cases without a +5 V rail would be engineering for a case this
instrument is never in (see the design scope in the README).

### Power tree

```
umbilical +12V ──┬── WS2815 LED strips          (direct, no conversion)
                 │
                 ├── REF5050 5.000V ──[OPA2197 ½]── MPXV4006GP breath sensor
                 │
                 ├── OPA2197 V+  (½ reference buffer, ½ breath buffer)
                 │
                 ├── 12V→5V buck ──┬── display board  5V pin
                 │                 ├── real-time board 5V pin
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

### There is no power switch on the instrument. Switching happens at the module.

An earlier revision of this ADR specified a panel switch on the instrument that
**switched the buck converter's enable pin, not the +12 V rail** — carrying no
current, so it could be a tiny slide switch anywhere convenient. A design review
found that it cannot be built as written and would not work if it could.

**The regulator has no enable pin.** The Recom R-78E5.0 is a 3-pin SIP on a 7805
footprint: IN, GND, OUT. The switch as specified has nothing to switch.

**And switching the buck would not turn the instrument off.** The WS2815 strips
run on raw umbilical +12 V, *upstream* of the buck, because they need 12 V and
the buck makes 5 V. Killing the buck leaves roughly 120 mA of strip quiescent
draw and the strips **holding their last latched colours** — an instrument still
lit, still drawing current, with its logic dead.

The version that actually works is a high-side P-FET on raw +12 V, which means a
FET, a gate network, and a fat conductor routed to a panel location inside a
bonded body that cannot be reopened to change the decision.

**So `SW-PWR-INST` is deleted.** Nothing on the instrument switches anything.

### The module's toggle drives a current-limited load switch

The module panel already carries a rated SPST toggle (ADR 0004), one reach away
in the same rack the instrument is patched into. That is upgraded rather than
duplicated.

**The toggle drives a TPS2553-class current-limited load switch on the
umbilical +12 V feed**, rather than breaking the current itself. That buys two
things the bare toggle does not have:

- **Inrush limiting.** The instrument's bulk capacitance is a near-short at the
  instant of connection. A toggle takes that surge across its contacts every
  time; a load switch ramps the output instead.
- **Short-circuit foldback.** A fault in the umbilical — a crushed cable, a
  connector half-inserted — is current-limited at the module instead of pulling
  on the rack's +12 V rail and browning out every other module in the case. This
  is the same job as the instrument-end polyfuse, done faster and self-resetting,
  and the two are complementary rather than redundant.

The part is SOT-23-6, which looks like a step away from the package policy in
ADR 0013 and is not: at 0.95 mm pitch it is *coarser* than the TSSOP-16 DAC
already accepted, and it has six leads rather than sixteen.

The toggle now carries no load current, so its rating stops mattering — it
drives an enable pin. It stays a rated part anyway because it is already
specified and costs nothing to keep.

**The honest cost of deleting the instrument switch:** there is no way to kill
the instrument without reaching the rack. For a tethered instrument whose
outputs go nowhere but that rack, there is nowhere else to be standing (see the
design scope in the README).

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
