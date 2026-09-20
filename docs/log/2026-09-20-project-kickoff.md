# 2026-09-20 — Project kickoff and architecture

First session. No hardware built. Switches and keycaps purchased; everything
else was decided in conversation and is now recorded in `docs/decisions/`.

## Starting point

Second iteration of the Open Woodwind Project (2021), which reached working
prototype but not past it. That build was a Teensy 3.2, two MPR121 capacitive
touch controllers, a BNO055 IMU, a pressure transducer, and a Teensy Audio
Library synthesizer.

This iteration keeps the concept and almost none of the implementation.

## Purchased

- Gateron KS-33 low-profile switches, MX stem
- Tai-Hao MT165-MX keycaps, 16.5 × 16.5 mm blank black

## Mined from the old repository

Part numbers only, as requested — no lessons-learned pass.

- IMU: **BNO055**, consistent between README and firmware
- Breath: **contradictory**. README says MPXV4006GP; `src/owp/owp.ino` header
  says MPX2010GS. Recorded as open in ADR 0003
- Firmware licence: GPLv3
- Incidental: the 2021 firmware already had a `CONTROLLER_MODE_MODULAR`, and it
  was the default mode. Modular was on the table five years ago

## How the architecture arrived

Worth recording, because the design moved a long way in one sitting and the
route matters.

**Started** with: ESP32-S3 in the instrument, onboard battery, boost and
inverting supplies for bipolar rails, DAC and analog scaling inside the wooden
body, 0–12V CV out, USB MIDI as a feature.

**Ended** with: a 6HP Eurorack module holding all analog hardware, powered by
the rack, connected to a purely digital instrument by one ruggedised cable.

Three turns did most of the work:

1. **Flat sandwich construction means no CNC is needed.** Every part is a 2D
   through-cut, which is laser and waterjet work. And lamination replaces
   pocketing entirely, which matters given no mill access. The left-thumb inset
   then falls out of the bottom panel thickness for free. (ADR 0009)

2. **Moving the analog section to a rack module** deleted the battery, the boost
   converter, the inverting supply, the charger, the lithium safety problem, the
   power budget and the weight-balance problem in a single stroke — and put
   precision analog in a shielded box inches from its jacks instead of two feet
   down a wooden instrument next to LED power. It also split the project into
   two deliverables that can be built in parallel and tested independently.
   (ADR 0004, ADR 0005)

3. **Dedicating pitch and breath, leaving four channels generic** resolved a
   tension that full genericity had created: output filters cannot be generic,
   because pitch needs a fast corner and breath needs a slow one. Dedicating the
   first two gives both optimal treatment. It also collapsed the calibration
   work — only channel 1 needs to be musically accurate, so the precision parts
   and the careful VCO-verified procedure concentrate on one channel instead of
   six. (ADR 0006)

## Reversals worth remembering

- **Analog-all-the-way breath was rejected on its own terms.** The latency
  budget showed the transducer dominates at ~1 ms — the entire digital path
  costs less than the sensor's own settling. Fully analog would have saved
  ~400 µs against a 1 ms floor while giving up curve shaping, ambient zeroing
  and threshold logic. But the analysis *did* confirm keeping the analog
  **sensor**: digital I2C pressure parts are slower than an analog transducer
  read by a fast SAR ADC.

- **IMU recommendation flipped** from ICM-42688-P to BNO085 on discovering the
  old firmware consumed Euler angles from chip-side fusion. Preserving that
  firmware shape is worth more than the ICM's raw advantages.

- **0–12V was abandoned for 0–10V**, not by preference but by physics: a
  rail-to-rail op-amp on the rack's +12V swings to roughly +11.5V. 0–10V is also
  what Eurorack inputs expect, so the outputs went from out of spec to in spec.

## Still open

Blocking mechanical work: key count, and instrument dimensions.
Blocking E9: confirmation of a 4.5-digit multimeter.
Also open: breath sensor identity, IMU part, display, connector, licence.

## Next

M1 the day the switches arrive — measure the KS-33 plate cutout with calipers
and cut a test coupon at ±0.1 mm steps. Everything mechanical inherits that
number.

Track E can start immediately; it is not gated on anything.
