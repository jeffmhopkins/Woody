# 0008 — Display selection

**Status:** Accepted (technology). Specific board open.

## Context

**Revised by ADR 0012.** The display was originally the instrument's entire UI,
since the module is deliberately dumb (ADR 0004) and everything had to live
here. Configuration has since moved to a phone over WiFi, which changes this
decision substantially.

The display is now a **status** surface: current note, breath level, active
channels, config-mode and link state. It no longer has to host a navigable
four-channel routing matrix, a fingering table editor, or a calibration
workflow.

It sits near the top of the instrument, on a short run from the MCU (ADR 0001),
and it is read **from a steep angle while playing** — looking down the length of
the body, not straight on.

## Decision

**AMOLED.**

This supersedes an earlier lean toward a monochrome OLED, which was chosen for
much the same reasons at lower cost and lower ambition. AMOLED is better suited:

- **Off-axis legibility** is the dominant requirement here, and it is what
  emissive panels are best at. No backlight means no contrast collapse at the
  steep angle this is read from.
- **True blacks and high contrast** read well under stage lighting, where an LCD
  washes out.
- **Power follows lit pixels**, so a mostly-black status layout — which is
  exactly what this displays — costs little. The same property that made
  monochrome OLED attractive applies, with far better output.
- Existing dev boards in this form factor are already on hand from another
  project.

### Burn-in still applies

An emissive panel showing static labels for years will retain them. Design for
it: dim aggressively, shift the layout periodically, blank when idle, avoid
static bright elements. This was true of the OLED option and is equally true
here.

## These panels are QSPI, not SPI

The practical consequence worth knowing before any board is committed to.

ESP32-S3 AMOLED modules almost universally use **Quad-SPI** — driver ICs like
the RM67162 and SH8601 need the bandwidth that four data lines provide. So the
display interface is CS, SCK and D0–D3, plus reset, plus usually a tearing-effect
line: **around 8 pins**, not the 4 or 5 a plain SPI panel would take.

**This is fine here, and specifically because of the topology already chosen.**
ADR 0001 put the MCU alongside the display precisely because display links
cannot run far; the long runs down the body are the slow ones. QSPI over a
two-foot ribbon would be a genuine problem. QSPI over a short trace next to the
MCU is unremarkable, and it reinforces the partitioning rather than fighting it.

## Pin budget

The real constraint is **free GPIO count**, not signal translation. Nothing in
this design needs level shifting — the S3, the sensors, the shift registers and
the DAC logic are all 3.3V.

| Function | Pins |
|---|---|
| AMOLED QSPI: CS, SCK, D0–D3 | 6 |
| AMOLED reset | 1 |
| AMOLED TE (tearing effect) | 1 |
| I2C: SDA, SCL (touch + IMU shared) | 2 |
| Touch INT (if the panel has touch) | 1 |
| SPI2: SCK, MOSI, MISO (DAC, ADC, shift regs) | 3 |
| CS: DAC (down the umbilical) | 1 |
| CS: breath ADC | 1 |
| Shift register latch | 1 |
| LED data (WS2812) | 1 |
| USB D+/D− (fixed, GPIO19/20) | 2 |
| **Total** | **20** |

An ESP32-S3-WROOM-1 has ~45 nominal GPIO, but SPI flash and PSRAM claim
GPIO26–32 — and GPIO33–37 as well with octal PSRAM — leaving roughly **30
usable with quad PSRAM, or about 22 with octal**. So a bare module has around 10
pins of headroom, or as little as 2 with octal PSRAM. **Prefer quad PSRAM.**

### On a dev board, the number that matters is 10

The display's 8 pins are already committed on-board and never appear on the
header, and USB's 2 are fixed. So everything else in the instrument needs
**10 free broken-out GPIO**: I2C pair, touch INT, three SPI2 lines, two chip
selects, a shift register latch, and LED data.

That is the single question to ask of any candidate board. Many AMOLED dev
boards break out 10–15 pins, so it is plausible — but it is board-specific and
worth counting against the actual pinout diagram before committing.

### If pins come up short

- **An I2C GPIO expander** (MCP23017-class) can absorb slow, non-timing-critical
  signals — chip selects, LED enables, mode inputs. It must never carry the SPI
  bus itself or anything inside the output loop.
- **The input side is already solved.** The 74HC165 chain reads all 18 switches
  on three pins (ADR 0001), so keys are not competing for GPIO.
- Dropping the TE line and the touch interrupt recovers 2 pins at some cost in
  tearing and polling overhead.

## Two paths

**A — Use the AMOLED dev board as the top assembly.** It becomes the MCU and
display module in one. Simplest by a wide margin, and it works if the free pin
count clears 10.

**B — Bare S3 module plus a separate AMOLED panel on FPC.** More layout freedom,
but meaningfully harder: **AMOLED panels need their own supply rails** (elevated
ELVDD and a negative ELVSS), and dev boards include that circuitry. Sourcing a
bare panel means building that supply, which is real analog work for no benefit
the instrument actually needs.

**Path A is recommended**, with the dev board mounted as the top board and the
umbilical SPI, I2C and LED data running down from its header.

### The integrated screen-and-MCU form factor is the right shape

Compact boards that carry MCU, panel, USB-C and mounting in one assembly — the
"LCD computer" category — are exactly what path A wants. One part, no panel
supply to design, no FPC to route.

Two things to check on any specific board in that category, because the common
ones fail one or both:

**Is it an S3?** Many are ESP32-C6, which breaks the core split and removes USB
MIDI (ADR 0001). The form factor is right; the part underneath often is not.

**Is it actually AMOLED?** Most of this category ship IPS LCD, not AMOLED — the
1.47-inch class in particular. An LCD gives up the off-axis legibility that
drove this decision in the first place.

S3 + AMOLED boards in the same form factor do exist and are the ones to look at:
Waveshare's ESP32-S3-Touch-AMOLED series (1.43-inch round and 1.8-inch),
LilyGO's T-Display-S3 AMOLED (1.91-inch, RM67162), and LilyGO's T4-S3
(2.41-inch). Specifications to verify per board rather than take from here.

**And the pin count question applies hardest to this category.** The more
integrated and compact the board, the fewer pins reach a header. A board that
satisfies both checks above and then breaks out only 6 GPIO is still unusable.
Ten is the number (see above).

## Open

- **Which board.** Needs identifying, against three gates in order: an S3 rather
  than a C6, a genuine AMOLED panel, and at least 10 free broken-out GPIO. The
  third is the one most likely to disqualify an otherwise ideal board.
- Whether the panel has touch, and whether touch is wanted at all — with
  configuration on a phone (ADR 0012), it may be redundant.
- Physical fit: panel active area and board outline against the 30 mm display
  band and 57 mm width (ADR 0009).
