# 0007 — IMU selection

**Status:** Open

## Context

The previous project used a **BNO055**, consuming Euler angles directly from the
chip's onboard sensor fusion. Tilt drove modulation (`deg_y` against up/down
limits) and pitch bend; roll drove expression, with a deadband so that shakes
self-centred while sustained angle changes produced full bends.

That mapping worked and the same shape is wanted here, now driving CV rather
than MIDI CC.

The IMU sits near the bottom of the instrument (ADR 0001), remote from the MCU,
on a slow bus down the body.

Only relative tilt matters, not absolute heading — so yaw drift is irrelevant
and no magnetometer is required.

## Options

**BNO085 / BNO086.** Direct successor to the BNO055. Runs fusion in-chip and
hands back Euler angles or quaternions, at 400 Hz rather than the BNO055's 100.
Preserves the existing firmware shape almost exactly. More expensive, and the
fusion is a black box.

**ICM-42688-P.** Excellent 6-axis part, lower noise, cheaper, well supported.
Hands back raw data — the complementary or Kalman filter is yours to write. More
control, more work, and tuning a filter for an instrument that is being waved
around is not trivial.

**BNO055.** Still available, but aging, soft-deprecated by Bosch, higher power,
and capped at 100 Hz fusion output. No reason to repeat it.

## Leaning

**BNO085**, on the grounds that the previous instrument's expression mapping
depended on chip-side fusion and reproducing that is the fastest path to a
playable result. The ICM-42688-P is the better part on raw merits and worth
revisiting if the BNO085's fusion behaviour disappoints.

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
  but longer angle changes do full pitch bends."* Shakes and playing movement
  fall inside it; deliberate gestures escape it.
- **Two independent axes.** Tilt (`deg_y`) drove gated pitch bend; roll
  (`deg_z`) drove expression continuously, outside the gate, with its own
  deadband and limits.
- **Acceleration as a separate source** from angle, with its own damping —
  useful for articulation in a way that angle is not.

### What the three right-thumb switches should support

- **Momentary gate** — hold to enable, capturing zero on press. The default.
- **Latch** — press to enable and capture, press again to release, for gestures
  longer than a thumb wants to hold.
- **Source or destination select** — which mod channel the IMU drives (ADR 0006).

All three are behaviours over the same switches, configured rather than wired,
and they belong in the routing matrix alongside everything else.

## Option: use an IMU already on one of the boards

Integrated screen boards in this category frequently carry a 6-axis
accelerometer and gyroscope — Waveshare's AMOLED range advertises one, commonly
a QMI8658-class part. If a board being bought anyway has one, buying a separate
IMU may be avoidable.

Three shapes this can take:

**A — IMU on the top display board.** Costs nothing at all. Tilt works
perfectly: **angle is position-independent**, so a sensor anywhere on a rigid
body reads the same pitch and roll (ADR 0001). What is lost is
**acceleration-gesture sensitivity** — a sensor near the top sits closer to the
pivot at the hands and neck, so shakes and jabs read smaller. The 2021 firmware
used acceleration as a modulation source separate from angle, so this is a real
loss, though possibly an acceptable one if tilt carries most of the expression.

**B — a second identical board at the bottom, used as the real-time MCU.** Its
onboard IMU then sits exactly where it is wanted, and two identical boards means
one BSP, one pinout to learn and interchangeable spares. The costs are real
though: paying for a second display that is never used, giving up cavity volume
to it in a space already constrained by switch bodies (ADR 0009), and moving the
real-time MCU from mid-body to the bottom, which takes the worst-case internal
run from ~8 in back to ~14 in (ADR 0013).

**C — a separate IMU at the bottom, MCU mid-body.** The current plan. Costs one
part and an I2C run, keeps the star topology and allows a part chosen on merit
rather than on what happened to be on a board.

### Which is right depends on two things

**How much acceleration matters versus tilt.** If tilt does the expressive work
and acceleration is a minor gesture source, A is free and good enough. If
shakes and jabs are meant to be a real control, the sensor wants to be low.

**Whether the onboard part is good enough.** A bare 6-axis with no onboard
fusion means writing the complementary or Kalman filter — the ICM-42688-P
trade-off above, arriving by a different route. The BNO085's appeal was
preserving the 2021 firmware's use of chip-side Euler angles.

## Open

- **Which board.** Needed before any of this resolves, and it decides whether
  option B is even available — the real-time role needs an S3 for USB MIDI and
  the core split (ADR 0001), so a C6-based board can be the display but not the
  bottom MCU.
- Whether that board has an IMU, and which part.
- Whether tilt alone carries the expression, which decides whether option A's
  loss matters.
- Whether tilt and roll get dedicated mod channels by default, or are simply
  available as routing sources (ADR 0006).
