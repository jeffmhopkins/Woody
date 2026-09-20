# 0008 — Display selection

**Status:** Open

## Context

The display is the instrument's entire UI. The module is deliberately dumb
(ADR 0004), so routing configuration, calibration, presets and status all live
here.

It sits near the top of the instrument, on a short SPI run from the MCU
(ADR 0001), and it is read **from a steep angle while playing** — looking down
the length of the body, not straight on.

## Constraints

- **Viewing angle is the dominant requirement.** A standard TFT washes out badly
  off-axis. IPS at minimum.
- **Power matters** even on rack power, since the instrument's draw comes off
  the Eurorack supply alongside the LEDs.
- **Refresh must never block the output loop.** The display lives on its own SPI
  host, rendering on the core not running the sensor and DAC loop (ADR 0001).

## Options

**Small colour IPS (ST7789-class, 1.9"–2.0").** Good detail for a routing
matrix, decent off-axis, readily available as bare modules on a ribbon. Backlight
is the power cost, 20–100 mA.

**OLED (SSD1306 / SH1107).** Excellent off-angle performance, and a mostly-black
status UI draws very little. Smaller and monochrome, so a four-channel routing
matrix would need more menu depth. Burn-in is a consideration for a display
showing static labels for years.

## Open

Undecided. The choice interacts with how much UI the routing matrix needs — four
channels × five parameters is navigable on a small screen, but not comfortably
on a very small one.

Buy a candidate of each during E1 and look at both from playing position before
committing. This is cheap and the question is genuinely ergonomic rather than
technical.
