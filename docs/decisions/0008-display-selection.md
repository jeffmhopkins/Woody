# 0008 — Display selection

**Status:** Accepted. Board selected: LilyGO T-Display-S3 AMOLED (base, not Plus).

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

> Superseded in effect by [ADR 0013](0013-two-mcu-split.md), which splits the
> display and radio onto their own MCU. The analysis below is what *forced* that
> split, and is kept for that reason. The display board now needs four pins, not
> ten.

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
| LED data (two strips) | 2 |
| USB D+/D− (fixed, GPIO19/20) | 2 |
| **Total** | **21** |

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

**Is it an S3?** ~~Many are ESP32-C6, which breaks the core split and removes
USB MIDI.~~ **No longer a gate** — [ADR 0013](0013-two-mcu-split.md) moved the
display and radio onto their own MCU, so a C6 is perfectly good in this role.
Single core is irrelevant when nothing real-time runs on it, and USB MIDI lives
on the other board.

**Is it actually AMOLED?** Most of this category ship IPS LCD, not AMOLED — the
1.47-inch class in particular. An LCD gives up the off-axis legibility that
drove this decision in the first place.

S3 + AMOLED boards in the same form factor do exist and are the ones to look at:
Waveshare's ESP32-S3-Touch-AMOLED series (1.43-inch round and 1.8-inch),
LilyGO's T-Display-S3 AMOLED (1.91-inch, RM67162), and LilyGO's T4-S3
(2.41-inch). Specifications to verify per board rather than take from here.

**And the pin count question is largely dissolved.** It was ten free GPIO, which
disqualified most of this category. Under ADR 0013 the display board needs
**four** — a UART pair and power — because everything else moved to the
real-time board. Almost anything in this category clears that.

## Recommended board: LilyGO T-Display-S3 AMOLED

Boards are being bought new, so this is a free choice rather than a constraint.

| | |
|---|---|
| Panel | 1.91 in AMOLED, 536 × 240, RM67162, QSPI |
| Active area | 44.22 × 19.8 mm |
| Board outline | 60 × 25.5 × 10 mm |
| Breakout | 28 pins — 18 GPIO plus 3V3 / GND / VBUS |

### Why this one

**The aspect ratio is close to purpose-made for a narrow instrument.** 536 × 240
is a 2.2:1 strip, and a 44 × 20 mm active area is exactly the shape of a status
bar — current note, breath meter, channel indicators in a row. Squarer panels
waste area on a body only 57 mm wide, and the display's job here is status
rather than a navigable UI (ADR 0012).

**Pin breakout is generous** — 18 GPIO against the 4 this role needs.

**It carries little that goes unused.** Boards in this category often bundle a
PMIC, battery charging and an onboard IMU. None of that helps here: there is no
battery (ADR 0005), and an IMU at the top of the instrument is the wrong end —
see ADR 0001 on why the IMU belongs low.

### Fit

**It must mount lengthwise.** At 60 mm the board is 3 mm wider than the
instrument, so it cannot sit crosswise. Lengthwise it needs 60 mm of body length
and 25.5 mm across, and its 10 mm depth clears the ~20 mm cavity comfortably.

Lengthwise is arguably better anyway: text runs along the body, which is the
natural reading direction looking down the instrument while playing.

The cost is the display band growing from 30 mm to 60 mm, which takes the length
budget from 61 mm of slack to **31 mm (1.2 in)**. Still closes, but no longer
generously — worth knowing before anything else claims length (ADR 0009).

### Notes

- **The base version, not the Plus.** Touch is redundant with configuration on a
  phone, and it costs pins and complexity.
- Order the version whose header suits the build — some ship with pins
  pre-soldered, which may or may not be wanted inside a sealed body.
- Verify the 60 mm outline against the final display band before committing.

### This does not undo the two-MCU split

With 18 free GPIO, this board could in principle run the whole instrument — the
pin budget that originally forced ADR 0013 is no longer binding. **The split
stands anyway**, because its real value is isolation: WiFi and display rendering
on different silicon from the 4 kHz loop is a physical guarantee rather than a
scheduling discipline. The pin budget was the symptom, not the reason.

Placement reinforces it — the display belongs at the top, the real-time board
mid-body (ADR 0013).

## Alternatives considered

**Waveshare ESP32-S3-Touch-AMOLED-1.8** — 368 × 448, SH8601, capacitive touch,
7 GPIO broken out on 1.27 mm pads, onboard PMIC and 6-axis IMU. Perfectly
capable, and the pin breakout clears the requirement. Rejected on shape: a
nearly square panel suits a 57 mm-wide instrument less well than a strip, and
the PMIC, battery support and IMU are all unused here. Worth revisiting if a
larger, denser display turns out to be wanted.

The rest of the Waveshare AMOLED range (1.43 and 1.75 in round, 1.64, 2.06 in)
was not pursued — round panels are attractive but waste area for text, and the
larger ones do not fit the length budget.

## Open

- Nothing blocking. Confirm the board outline on arrival and lay out the display
  band against it.
