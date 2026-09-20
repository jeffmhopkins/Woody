# 0008 — Display selection

**Status:** Open

## Context

**Revised by ADR 0012.** The display was originally the instrument's entire UI,
since the module is deliberately dumb (ADR 0004) and everything had to live
here. Configuration has since moved to a phone over WiFi, which changes this
decision substantially.

The display is now a **status** surface: current note, breath level, active
channels, config-mode and link state. It no longer has to host a navigable
four-channel routing matrix, a fingering table editor, or a calibration
workflow.

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

## Leaning

**OLED**, which the narrowed scope now favours. The argument against it was that
a four-channel routing matrix needed screen real estate to navigate; with
configuration on a phone that objection disappears, and the OLED's advantages —
excellent off-axis legibility at the steep angle this is read from, very low
power on a mostly-black status layout — apply directly to what it now has to do.

Burn-in remains worth designing around for a display showing static labels for
years: dim aggressively, shift the layout periodically, blank when idle.

## Open

Not final. Buy a candidate of each during E1 and look at both from playing
position before committing — the question is ergonomic rather than technical,
and it is cheap to answer properly.
