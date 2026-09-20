# 0006 — CV channel allocation and calibration

**Status:** Accepted

## Decision

**Six channels from an octal DAC, two dedicated and four assignable.**

| Output | Source | Range | Panel control | Precision |
|---|---|---|---|---|
| **Pitch** | DAC ch 1 | −2 to +7V, 1V/oct | none | Calibrated |
| **Breath** | **analog, differential over the umbilical** | 0–10V | gain + offset knobs | Trimmed |
| **Mod 1–4** | DAC ch 2–5 | 0–10V | none — configured on the instrument | Trimmed |
| *(internal)* | DAC ch 6 | — | — | Breath ambient-zero offset (ADR 0003) |

Six jacks on the panel as before, but only five of them come from the DAC.
**Breath never enters the digital path on its way out** — it is the one channel
where output steps reach the ear, so it stays analog end to end (ADR 0003).
A sixth DAC channel drives the firmware-controlled zero offset for that analog
stage, leaving two of the octal part's channels still spare.

Use an **octal** 16-bit DAC (DAC8568 or AD5676) and populate six. Eight-channel
parts cost barely more than quads and occupy the same board area; there is no
reason to design into a hard limit of four.

Mod channels are generic rather than fixed-function — a gate can be assigned to
one if wanted, without the design being *limited* to a gate. Per-channel source,
scale, offset, curve and slew are set on the instrument's display.

## Why dedicating pitch and breath is better than full genericity

Fully assignable channels were considered and rejected, because output filtering
cannot be generic:

- **Pitch must not be filtered slowly.** A soft filter on pitch CV is an audible
  glide on every note change. Corner it around 10–20 kHz — enough to kill DAC
  step glitches, fast enough that notes land instantly. Portamento belongs in
  firmware where it can be switched off.
- **Breath wants a gentler filter**, ~2 kHz. It is an inherently slow signal and
  the steps should be smoothed in hardware.
- **Mod 1–4** get a uniform fast filter with smoothing applied in software,
  per-channel, according to what each is assigned to.

Dedicating the first two channels means they get optimal analog treatment rather
than a compromise, and only the generic four need the uniform-filter-plus-
software approach.

Stepping artefacts on the generic channels are not a concern: **step size is
bounded by slew rate, not full scale.** A signal moving over ~10 ms sampled at
4 kHz changes by a fortieth of its excursion per sample, and one LSB at 16-bit
over 10V is ~150 µV. The only large step is a deliberate note change, which
should be fast anyway.

## Channels do not share an update rate

Breath needs a high output rate to keep staircase ripple out of the audio band
(ADR 0003). The others do not, and giving them one would waste the umbilical's
entire bandwidth budget.

| Channel | Rate | Why |
|---|---|---|
| Pitch | 2 kHz, plus **immediate update on note change** | Static between notes; what matters is latency at the transition, not rate |
| Mod 1–4 | 2 kHz | Sources are slow — IMU tops out around 400 Hz |
| Breath zero offset | on demand | Changes only at ambient calibration |

Pitch is the subtle one: it needs no *rate*, but it must not wait for its turn
in a round-robin. Push it the instant the note resolves.

A 96 kHz breath channel was specified before the output went analog, which
implied sub-10 µs DAC settling and ~6.8 MHz on the umbilical. **Both
requirements are withdrawn** — nothing left on the DAC needs that rate
(ADR 0003).

## Breath knobs are analog, in the signal path

With breath locked to channel 2 there is no genericity conflict, so the knobs
sit directly in the analog path: zero latency, tactile, no firmware involvement,
and **no return path needed over the umbilical**.

**Order is gain first, then offset.** Scale how much of the 0–10V span the
breath covers, then position where the floor sits. The reverse ordering makes
the two controls fight each other.

Firmware still shapes the response curve upstream of the DAC. The knobs fit the
*range* to the patch; the firmware shapes the *feel*.

## Calibration effort concentrates on one channel

**Only channel 1 needs to be musically accurate.** 1V/oct tracking, a per-unit
calibration table in NVS, and a two-point fit verified against a real VCO — not
just a meter, because a meter will not catch a scaling error that sounds wrong.

Channels 2–6 need only to be linear and repeatable. Nobody's ear cares whether a
modulation CV is 2% off.

So the precision parts concentrate on channel 1. But **where** that budget goes
is worth checking rather than assuming, and the arithmetic is not what it looks
like.

Over a 10 °C swing on a 9 V span, against one semitone at 83.3 mV:

| Source | Drift | Cents |
|---|---|---|
| DAC internal reference, 5 ppm/°C | 0.45 mV | 0.54 |
| **Discrete resistors, 25 ppm/°C each, drifting oppositely** | **4.50 mV** | **5.40** |
| Matched network, 1 ppm/°C tracking | 0.09 mV | 0.11 |

**Resistor tracking dominates reference drift by roughly ten to one.** The gain
of a scaling stage is a resistor *ratio*, so what matters is not each resistor's
absolute tempco but how well the two track each other — and two discrete parts
do not track at all.

Consequences:

- **Use a matched resistor network for the pitch scaling stage** (LT5400 class,
  MSOP-8), not discrete 0.1% parts. This is the single highest-value precision
  component in the design.
- **The DAC's internal reference is sufficient.** At 0.54 cents over 10 °C it is
  an order of magnitude inside the resistors, so a separate precision reference
  buys nothing measurable. One fewer part.
- Still use a low-drift op-amp (OPA2197-class, not TL072) — offset drift on
  pitch is drift in tuning.

Channels 2–6 run on ordinary 1% discretes; nobody's ear cares whether a
modulation CV moves a few cents' equivalent with temperature.

This is materially less expensive and less work than treating all six as
precision outputs.

## Pitch gets trim pots. Calibration is hardware first, firmware second.

An earlier revision of this ADR specified **no trimmers anywhere**, on the
grounds that a stored firmware fit is better than a screwdriver adjustment. A
design review found two independent reasons that does not work, and the decision
is reversed for the pitch channel.

### Why firmware alone was not enough

**Firmware calibration has no offset authority.** A two-point fit is
`y = a·x + b`. Scaling the DAC code implements `a`. **Nothing implemented `b`.**
If the hardware offset came out at −1.90 V instead of −2.00 V, firmware could
not reach −2 V at all — and the ADR prescribed a deliberate +5 % *gain* bias
while saying nothing about the offset, whose safe bias direction is the opposite
one.

**The gain ratio was not buildable.** The 1.8× gain needed for a 0–5 V DAC span
to become −2…+7 V is 9/5, which cannot be made from a matched resistor quad. Any
external resistor added to reach it puts its absolute tempco inside the ratio —
exactly the failure the matched network was bought to prevent.

A trimmer solves both directly, which is also why every commercial 1V/oct module
has scale and offset trimmers.

### What it costs, honestly

The trimmer is in the gain ratio, so its tempco is too. Against a fixed 0.1 %
10 ppm/°C resistor:

| Trim range | Net ratio tempco | Drift over 10 °C |
|---|---|---|
| 5 % | 22 ppm/°C | **2.4 cents** |
| 10 % | 34 ppm/°C | 3.7 cents |
| 20 % | 58 ppm/°C | 6.3 cents |

That is worse than a matched network (0.11 cents) and comparable to discrete
resistors (5.4 cents). **It is also comparable to what the VCO being driven does
on its own** — a well-compensated analog VCO drifts around 0.35 cents/K, so
3.5 cents over the same 10 °C. The trimmer is therefore not the limiting term in
the system, and the precision-network argument was over-engineering relative to
the load it feeds.

**Keep the trim range small — 5 to 10 % — around a fixed precision resistor.**
The LT5400 can still set the nominal ratio exactly, with the trimmer providing
only the adjustment; that keeps most of the matched-network benefit and adds
trimmability.

### The division of labour

- **Trimmers set gain and offset.** Two per pitch channel, multiturn cermet.
- **Firmware handles what trimmers cannot:** DAC integral nonlinearity, which is
  curvature no gain-and-offset adjustment can remove (±4 LSB typical is
  0.66 cents, ±12 LSB is 2.0 cents). Use a **multi-point** table, roughly one
  point per octave — Mutable's Yarns uses twelve for exactly this reason.

These are complementary, not alternatives. Hardware gets the line straight;
firmware straightens the bow in it.

### Consequences elsewhere

- **The "design the gain 5 % high" kludge is deleted.** It existed only because
  firmware could scale in one direction. A trimmer goes both ways.
- **Use the DAC's 0.25–4.75 V window rather than its full 0–5 V span.** That
  leaves 250 mV of headroom at both rails — the DAC8568 at AVDD = 5 V cannot
  reliably swing to its own supply — and the trimmer absorbs the resulting gain
  change. This achieves the same benefit as respeccing the output range, without
  needing an exactly-constructible resistor ratio.
- **Mod channels stay trimmer-free.** They need to be linear and repeatable, not
  musically accurate; firmware scaling is sufficient there and nobody's ear
  cares about a few cents' equivalent on a modulation CV.

## Labelling

Channels 1 and 2 are silkscreened. Mod 1–4 are numbered with a write-on strip,
with the instrument's display as the authority on what is actually routed where.

Optional later: an LED per jack tracking that channel's value, for instant
visual confirmation of what is doing what. Costs a driver and six LEDs; not
worth designing in now.

## Test equipment

Resolved — a full bench is available: oscilloscopes, logic analysers,
multimeters, signal generators and RF gear. E9 is not gated on tooling.

This raises what is achievable at several milestones. Rather than trusting
datasheet figures, the assumed numbers in
[the latency budget](../reference/latency-budget.md) should be measured; see
the characterisation section there.

For calibration specifically: take the two-point fit with the meter, then verify
tracking against a real VCO by ear and by frequency counter. A meter confirms
the voltage is what was commanded; only the VCO confirms the voltage is
musically right.
