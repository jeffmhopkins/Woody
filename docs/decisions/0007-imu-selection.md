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

## Open

- Confirm the part.
- Decide whether tilt and roll get dedicated mod channels by default, or are
  simply available as routing sources (ADR 0006). The latter is more flexible
  and costs nothing.
- Which of the three gating behaviours each right-thumb switch defaults to.
