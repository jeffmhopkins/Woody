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

## Open

- Confirm the part.
- Decide whether tilt and roll get dedicated mod channels by default, or are
  simply available as routing sources (ADR 0006). The latter is more flexible
  and costs nothing.
