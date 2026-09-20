# 0007 — IMU selection

**Status:** Accepted. Board selected: Waveshare ESP32-S3-Matrix.

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

### The angle estimator: stillness-gated bias, not a plain complementary filter

Capture-on-press makes long-term drift irrelevant, but it does **not** make gyro
bias irrelevant — it subtracts the bias's accumulated *offset* at the moment of
the press, while the bias itself keeps integrating for the seconds the gesture
lasts. Over a 3 s gesture, gyro noise contributes about 0.026°. Bias is the
entire story.

A review proposed replacing the complementary filter with a **bias snapshot
taken in a fixed window just before the press.** That is wrong in a specific and
instructive way: the window is sampled at exactly the moment the player is most
likely to be moving, because reaching for the gate button *is* motion. 20 °/s of
real rotation captured as "bias" and then subtracted for three seconds is a
**60° error** — far worse than the drift it was meant to remove.

**The correct version is the hybrid:** maintain a bias estimate continuously,
and **update it only when the instrument is demonstrably still** — gyro
magnitude below a threshold and accelerometer magnitude near 1 g, sustained.
Then:

- End the pre-press sampling window **~50 ms before the press**, not at the
  press, so the reach for the button is outside it.
- **Validity-check the estimate** before trusting it. If the instrument has not
  been still recently enough, hold the last good bias rather than adopting a
  fresh bad one.

Same cost as either alternative, no runaway. It is genuinely a hybrid: gyro-only
inside the gesture, where the complementary filter's accelerometer correction has
barely acted anyway at the τ = 0.5–5 s that linear-acceleration rejection
requires — and accelerometer-referenced only while stationary, which is the one
condition under which the accelerometer is actually measuring gravity.

### What the three right-thumb switches should support

- **Momentary gate** — hold to enable, capturing zero on press. The default.
- **Latch** — press to enable and capture, press again to release.
- **Source or destination select** — which mod channel the IMU drives (ADR 0006).

All three are behaviours over the same switches, configured rather than wired.

## Board: Waveshare ESP32-S3-Matrix

**Selected.** ESP32-S3, onboard **QMI8658C** 6-axis IMU, 16 GPIO broken out
against the 14 this role needs, 4 MB flash, 2 MB quad PSRAM, native USB.

**This is not a bring-up convenience.** An earlier revision of this ADR assumed
the dev board's IMU would be replaced by a bare part on the final carrier. That
is wrong under ADR 0013's architecture: the carrier is **passive**, the dev
boards plug into it and stay there, so the onboard IMU *is* the final IMU.

Which turns out to be the only way to have one at all:

- **Every 6-axis IMU worth using is LGA-14** — QMI8658C, ICM-42688-P, LSM6DSOX
  are all 2.5 × 3.0 mm leadless parts. ADR 0013's package policy rules them out
  as bare components on a hand-assembled board.
- **No ESP32-S3 board exists with a 6-axis IMU and nothing else.** Every one
  carries an LCD, an AMOLED, or an LED array. Carrying something unwanted is the
  price of a reflowed IMU.

### What was verified, and how

Product listings were not trusted. These come from CircuitPython's and Zephyr's
board definitions, which have to be correct for the board to work at all:

- **The IMU is a QMI8658C and it is 6-axis.** CircuitPython names it explicitly
  with `IMU_SDA` = GPIO11, `IMU_SCL` = GPIO12, `IMU_INT1` = GPIO10,
  `IMU_INT2` = GPIO13. One write-up describes the board as 9-axis; that is an
  error. It would not have mattered — only relative tilt is needed, never
  absolute heading, so a magnetometer buys nothing — but the open item is closed.
- **The USB-C is the S3's native USB, not a UART bridge.** Zephyr's devicetree
  sets `zephyr,console = &usb_serial` with no bridge chip present. **This one
  was decisive**: GPIO19 and GPIO20 are not broken out, so had the port gone
  through a CH343P the board could not have done USB MIDI at all and would have
  been disqualified (E5).
- **The matrix is 64 WS2812C parts on GPIO14**, chained, driven over SPI2 in
  Zephyr's configuration. Below.

### Pin assignment

Broken out: **GPIO 1–7** on one side, **GPIO 34–40, 43, 44** on the other.

| Function | Pins | Assigned |
|---|---|---|
| SPI2 — DAC8568 + MCP3202 | 3 | 35, 36, 37 |
| CS: DAC, CS: ADC | 2 | 34, 39 |
| SPI3 — 74x165 chain alone (ADR 0001) | 2 | 38, 40 |
| Shift register latch | 1 | 7 |
| WS2815 data, two strips | 2 | 1, 2 |
| UART1 to the display board | 2 | 5, 6 |
| UART0 console to a carrier test header | 2 | 43, 44 |
| **Used** | **14 of 16** | spare: 3, 4 |

**The inter-MCU link goes on UART1, not on 43/44.** Using UART0 would work and
would save two pins, but it is the boot console — panic output and bootloader
chatter would land in the middle of a framed protocol, and the debug console
would be gone. In a body that cannot be opened, two pins is a cheap price for
keeping a console, and the design has them.

GPIO 3 and 4 stay free. Both are ADC1 channels, so a spare can become an analog
input if something later wants one.

### Two things to carry forward

**The 64 LED drivers are never turned on, and they are not free.** WS2812-class
controllers draw roughly 0.6–1 mA each with their outputs off, so the matrix
represents an estimated **~50 mA and ~0.25 W continuously** — inside a sealed
body with a documented 10–20 K interior rise, near a temperature-sensitive gauge
sensor, for no function. That is about 8 % of the instrument's current budget.

**Measure it at E1** with the board idle, rather than carrying the estimate
forward. Cutting the matrix's supply trace was considered and declined: it is a
permanent modification to a part that is not easily replaced, made against an
estimated number, for a saving that is real but not large. Revisit only if the
measurement is materially worse than 50 mA.

**If the board ships with octal PSRAM, the pin budget collapses to exactly
enough.** Octal PSRAM consumes GPIO33–37, which would take the 16 broken-out
pins down to 12 — precisely the number needed if the UART0 console is sacrificed
and the inter-MCU link moves to 43/44, with nothing spare. Both CircuitPython
and Zephyr declare **quad** (`qio`) PSRAM, so this should not happen. **Confirm
at E1 before laying out the carrier**, because the carrier's pin map depends on
it.

## Open

- Whether tilt and roll get dedicated mod channels by default, or are simply
  available as routing sources (ADR 0006).
- Which of the three gating behaviours each right-thumb switch defaults to.
