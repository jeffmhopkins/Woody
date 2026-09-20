# 0007 — IMU selection

**Status:** Accepted (approach). Specific board open.

## Context

The previous project used a **BNO055**, consuming Euler angles directly from the
chip's onboard sensor fusion. Tilt drove modulation (`deg_y` against up/down
limits) and pitch bend; roll drove expression, with a deadband so that shakes
self-centred while sustained angle changes produced full bends. Acceleration fed
pitch bend separately, with its own damping.

## Decision

**A bare 6-axis IMU, mounted low, on the real-time board.**

Three things drive this, and the third reverses an earlier recommendation.

### Position: low, and it matters

Acceleration is a first-class control here, not a minor gesture source. That
settles a question this ADR previously left open.

**Tilt angle is position-independent** — a rigid body has one orientation, so a
sensor anywhere on it reads the same pitch and roll. **Acceleration is not.** A
sensor further from the pivot at the player's hands and neck sees proportionally
larger tangential accelerations, so shakes and jabs read larger and cleaner low
in the instrument.

Mounting the IMU on the top display board was considered — it would have cost
nothing — and is rejected on exactly this ground.

### Fusion is not wanted here

An earlier revision of this ADR leaned toward the **BNO085**, on the reasoning
that the 2021 firmware consumed chip-side Euler angles and preserving that shape
was the fastest path to a playable result. **That reasoning does not survive
contact with the requirement.**

- **For acceleration, fusion is at best neutral and at worst a liability.** Raw
  accelerometer output is exactly what shake and jab detection wants. Fusion
  algorithms exist to separate gravity from linear acceleration, which is work
  being done *against* the signal of interest.
- **For tilt, drift does not matter.** The gating design below captures the zero
  reference at the moment the gate is pressed, so angle only needs to be good
  for the *seconds a gesture lasts*, not for hours. Long-term drift — the
  problem onboard fusion exists to solve — is architecturally irrelevant here.
- A complementary filter over accelerometer and gyro for pitch and roll is a
  handful of lines, and with re-zeroing on every gesture it is more than
  adequate.

So a bare 6-axis part is not a compromise against the BNO085. For this
application it is the better fit, and it is cheaper and more widely available.

### It rides on the real-time board

The instrument uses **two ESP32-S3s** (ADR 0013): display board at the top,
real-time board low. Choosing a real-time board that carries a 6-axis IMU
onboard means the sensor lands where it is wanted with no separate part, no
breakout and no I2C run.

Note that "the bottom board does not need WiFi" is true but not purchasable —
every S3 has a radio. What it means in practice is **choose that board for its
IMU rather than its antenna**, and leave the radio disabled, which is what
ADR 0012 wants on the real-time side anyway.

## Gating: capture-on-press, not absolute tilt

The most important thing to carry forward from the 2021 firmware, and the reason
the right thumb gets control switches (ADR 0010).

Absolute tilt is unusable as a modulation source. The instrument's resting angle
varies with posture, with standing versus sitting, and from session to session —
there is no fixed zero. The old firmware solved this with a **gate button that
captures the current angle as the reference at the moment it is pressed**:

```c
if (B[3] || B[4] || B[5]) {          // pitch bend gates active
    if (!imu_pb_active) {
        imu_pb_active   = true;
        imu_pb_deg_init = deg_y;     // capture zero HERE, NOW
    }
}
if (!(B[3] || B[4] || B[5])) {
    imu_pb_active = false;
}
```

Every limit and deadband downstream is then computed relative to
`imu_pb_deg_init` rather than to absolute zero. Release the gate and modulation
stops.

Carry forward as well:

- **A deadband around the captured zero.** The old comment is worth preserving
  verbatim: *"this allows for accel shakes inside the deadband to self center,
  but longer angle changes do full pitch bends."*
- **Two independent axes.** Tilt (`deg_y`) drove gated pitch bend; roll
  (`deg_z`) drove expression continuously, outside the gate.
- **Acceleration as a separate source** from angle, with its own damping.

### What the three right-thumb switches should support

- **Momentary gate** — hold to enable, capturing zero on press. The default.
- **Latch** — press to enable and capture, press again to release.
- **Source or destination select** — which mod channel the IMU drives (ADR 0006).

All three are behaviours over the same switches, configured rather than wired.

## Candidate boards

The IMU on a dev board is a **bring-up convenience**. The final custom carrier
(E13) puts the part directly on the board, chosen on merit — using an onboard
IMU now does not lock that choice.

**Waveshare ESP32-S3-Matrix** — ESP32-S3, QMI8658 6-axis, ~17 GPIO broken out
against the ~12 this role needs, compact, and **no LCD to pay for or find room
for**. The 8×8 RGB LED matrix is unused but harmless. Best shape of the options
found.

*One thing to verify:* the product listing says QMI8658 6-axis, while at least
one write-up describes the board as carrying a 9-axis sensor. Either is
sufficient — only relative tilt is needed, never absolute heading, so a
magnetometer buys nothing.

**Waveshare ESP32-S3-Touch-LCD-1.28** — same QMI8658, but a round LCD that would
be paid for and never used.

## Open

- Confirm the board and its actual IMU part and free pin count.
- Whether tilt and roll get dedicated mod channels by default, or are simply
  available as routing sources (ADR 0006).
- Which of the three gating behaviours each right-thumb switch defaults to.
