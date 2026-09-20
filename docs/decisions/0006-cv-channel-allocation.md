# 0006 — CV channel allocation and calibration

**Status:** Accepted

## Decision

**Six channels from an octal DAC, two dedicated and four assignable.**

| Ch | Function | Range | Panel control | Precision |
|---|---|---|---|---|
| 1 | **Pitch** | −2 to +7V, 1V/oct | none | Calibrated |
| 2 | **Breath** | 0–10V | gain + offset knobs | Trimmed |
| 3–6 | **Mod 1–4** | 0–10V | none — configured on the instrument | Trimmed |

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

So the precision parts concentrate on channel 1: low-drift op-amp (OPA2197-class,
not TL072 — offset drift on pitch is drift in tuning), 0.1% thin-film resistors,
and a clean path from a precision voltage reference rather than the supply rail.
Channels 2–6 run on ordinary 1% parts.

This is materially less expensive and less work than treating all six as
precision outputs.

## Labelling

Channels 1 and 2 are silkscreened. Mod 1–4 are numbered with a write-on strip,
with the instrument's display as the authority on what is actually routed where.

Optional later: an LED per jack tracking that channel's value, for instant
visual confirmation of what is doing what. Costs a driver and six LEDs; not
worth designing in now.

## Open

**A 4.5-digit multimeter is needed for E9** and is not yet confirmed as
available. Calibration realistically cannot be done without one. Roughly a $50
purchase, and it blocks the milestone that decides whether the instrument plays
in tune.
