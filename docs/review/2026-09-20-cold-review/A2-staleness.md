# A2 — Staleness audit: claims that were true once and are not any more

Scope: `README.md`, `ROADMAP.md`, `docs/decisions/*`, `docs/reference/*`,
`hardware/bom.csv`, `config/key-layout.yaml`, `firmware/README.md`.
`docs/review/` and `docs/log/` were read for provenance only and are excluded as
deliberate historical record, as are ADR passages that quote their own earlier
text in order to reverse it.

Findings are ordered roughly by severity. Line numbers are as of `741a4b8`.

---

## 1. **README still says licensing is undecided, three commits after it was settled**

**Severity:** High — it is the last section of the front door, and it contradicts
`LICENSE`, `LICENSES/`, ADR 0011 and the README's own "Licence" section 25 lines
above it.

Stale text — `README.md`, final section "Licensing" (lines 108–112):

> ## Licensing
>
> Not yet decided — see
> [ADR 0011](docs/decisions/0011-licensing.md). The previous project's firmware
> was GPLv3.

Superseded by commit `a478df9` "Settle licensing", which set ADR 0011 to
**Accepted** (`docs/decisions/0011-licensing.md:3`) and added the README's own
"## Licence" section (lines 77–85) naming GPL-3.0-only / CERN-OHL-S-2.0 /
CC-BY-SA-4.0. The duplicate stale section was never deleted.

**Proposed replacement:** delete the whole "## Licensing" section (lines
108–112). The "## Licence" section already covers it.

**Confidence:** Certain.

---

## 2. **The ADR index lists three ADRs as open that are all decided**

**Severity:** High — the index is the navigation surface for the decision
record, and commit `e9a80e5` claimed in its message that "All 14 ADRs are now
Accepted with their parts named" while leaving the table untouched.

Stale text — `docs/decisions/README.md`, "## Index" (lines 47, 48, 51):

> | [0007](0007-imu-selection.md) | IMU selection | Accepted (board open) |
> | [0008](0008-display-selection.md) | Display selection | Accepted (board open) |
> | [0011](0011-licensing.md) | Licensing | Open |

Superseded by: `0007-imu-selection.md:3` — "**Status:** Accepted. Board
selected: Waveshare ESP32-S3-Matrix." (commit `551d59e`);
`0008-display-selection.md:3` — "**Status:** Accepted. Board selected: LilyGO
T-Display-S3 AMOLED (base, not Plus)." (commit `e9a80e5`);
`0011-licensing.md:3` — "**Status:** Accepted" (commit `a478df9`).

**Proposed replacement:**

```
| [0007](0007-imu-selection.md) | IMU selection | Accepted |
| [0008](0008-display-selection.md) | Display selection | Accepted |
| [0011](0011-licensing.md) | Licensing | Accepted |
```

**Confidence:** Certain.

---

## 3. **README repeats the "controller is purely digital" claim that ADR 0004 explicitly retracted**

**Severity:** High — ADR 0004 says in terms that this sentence "was already false
when written and it let a review finding through unchallenged". It is still the
README's one-paragraph summary of the architecture, and it hides where most of
the project's analog risk lives.

Stale text — `README.md`, "What it is" (lines 28–31):

> The controller is purely digital and carries no analog signal path and no
> battery.

Superseded by `docs/decisions/0004-cv-interface-module.md:20–27` ("**It does not
become purely digital, and an earlier version of this line said it did.** … The
instrument still carries the pressure sensor, a precision reference, two op-amp
stages and the analog drive onto the umbilical") and by ADR 0003's own
correction at `0003-breath-sensing-path.md:585–588`.

**Proposed replacement:**

> The controller carries no battery and no *output* analog — no jacks, no
> bipolar rails. It does still carry the pressure sensor, its precision
> reference and two op-amp stages, which is where most of the project's analog
> risk lives (ADR 0003). It takes power from the rack over the umbilical and
> sends channel data down the same cable as SPI, with the breath signal riding
> alongside as analog. All *scaling and conversion* happens in the module,
> inches from the jacks it drives.

**Confidence:** Certain.

---

## 4. **ADR 0013's three-zone placement table still puts the real-time MCU mid-body and the breath sensor at the top**

**Severity:** High — this is the largest single block of stale content in the
repository, and it contradicts four other ADRs plus the latency budget. Anyone
laying out the carrier or the loom from ADR 0013 builds the wrong instrument.

Stale text — `docs/decisions/0013-two-mcu-split.md:144–169`:

> | Zone | Contents |
> |---|---|
> | **Top** | Display board (AMOLED + WiFi), breath sensor + ADC on a short tube, upper key cluster |
> | **Middle** | Real-time MCU |
> | **Bottom** | IMU, umbilical connector, power entry and 3.3 V regulation, protection |
>
> ### Mid-body placement halves the worst-case run
> … | **Worst case** | **205 mm (8.1 in)** | **360 mm (14.2 in)** |
> Longest run drops from 14 inches to 8.

Superseded by commit `0f0c0fe` ("Sensor to the bottom") →
`0003-breath-sensing-path.md:204` "**Sensor placement: at the bottom, with the
real-time board**" and `:400` (the star point is "the analog ground pour on the
bottom cluster board"); by commit `551d59e` → `0007-imu-selection.md:221–224`
"**the very bottom tip**"; and by `0014-lighting.md:261` "The real-time board
sits at the very bottom tip of the instrument". The IMU is also no longer a
zone occupant in its own right — it is onboard the real-time board
(`0007-imu-selection.md:144`). The whole "Is the third board worth it?" section
(`:192–203`) argues for a three-board split whose premise (MCU in the middle) no
longer holds.

**Proposed replacement** for the table and the two sections that follow it:

> | Zone | Contents |
> |---|---|
> | **Top** | Display board (AMOLED + WiFi), upper key cluster |
> | **Middle** | Key clusters, looms, U-bolt |
> | **Bottom (tail)** | Real-time board with its onboard IMU and 8×8 matrix, breath sensor + reference + buffers + ADC, umbilical connector, power entry and 5 V regulation, protection |
>
> ### Bottom placement, and what it costs
>
> An earlier revision of this ADR put the real-time MCU mid-body, on the grounds
> that centring it halves the worst-case run (205 mm against 360 mm). That was
> traded away deliberately: the IMU wants maximum acceleration sensitivity at the
> tip (ADR 0007), the matrix wants the tail window (ADR 0014), and the breath
> sensor wants to be away from the AMOLED's heat and next to the umbilical, with
> no internal analog run at all (ADR 0003). Those four requirements agree on the
> bottom. What it costs is a 14-inch key-chain run and a 14-inch UART to the
> display, both of which were already shown to be fine at that length, plus the
> 400 mm breath tube that the latency budget absorbs.
>
> The two-board outcome is now the design, not a fallback: the real-time board
> and the power/analog entry share the bottom carrier.

**Confidence:** High on the staleness; the replacement's framing (two-board
outcome) should be confirmed against the author's intent for the "third board".

---

## 5. **ADR 0008 asserts the real-time board is mid-body**

**Severity:** Medium-High — same fact as finding 4, landed in a second document.

Stale text — `docs/decisions/0008-display-selection.md:212–213`:

> Placement reinforces it — the display belongs at the top, the real-time board
> mid-body (ADR 0013).

Superseded by the same sources as finding 4.

**Proposed replacement:**

> Placement reinforces it — the display belongs at the top and the real-time
> board at the tail, so they are at opposite ends of the body and share only a
> UART pair and power (ADR 0013, ADR 0007).

**Confidence:** Certain.

---

## 6. **ADR 0009 still describes the breath sensor as being on a short tube near the top**

**Severity:** Medium-High — it is a *stack* requirement (serviceable access),
and it points the CAD at the wrong end of the instrument.

Stale text — `docs/decisions/0009-enclosure-construction.md`, "### Breath tube
access":

> The only stack requirement is **access to clear it without disassembly**. Not a
> drain plumbed through the body — just a serviceable path to the sensor end of a
> short tube near the top.

Superseded by `0003-breath-sensing-path.md:204` and the 400 mm tube
(`:244–245`), and by `hardware/bom.csv` row `TUBE`: "~400mm — the sensor sits at
the BOTTOM with the real-time board (ADR 0003), not at the top."

**Proposed replacement:**

> The only stack requirement is **access to clear it without disassembly**. Not a
> drain plumbed through the body — just a serviceable path to the sensor end of
> the 400 mm tube, which terminates at the bottom carrier beside the umbilical
> connector (ADR 0003).

**Confidence:** Certain.

---

## 7. **Three documents still say the instrument's local converter makes 3.3 V**

**Severity:** High — the rail voltage is load-bearing (the sensor buffer needs
5 V, and the BOM part is an R-78E5.0), and ADR 0005 contradicts itself inside
one file.

Stale text:

- `docs/decisions/0005-power-architecture.md:43–44` (in the **Decision**):
  > The rack already provides ±12V, regulated and filtered. The instrument takes
  > +12V up the cable and derives 3.3V locally with a small buck converter.
- `docs/decisions/0004-cv-interface-module.md:36`:
  > `+12V, GND, GND      power (3.3V derived locally in the instrument, small buck)`
- `docs/decisions/0014-lighting.md:72–73`:
  > The instrument has +12 V from the umbilical and derives 3.3 V locally
  > (ADR 0005).

Superseded by `0005-power-architecture.md:69–82` ("### The rail that matters is
5 V, not 3.3 V … An earlier revision of this ADR specified a 12 V to 3.3 V buck.
**That is wrong**"), its power tree at `:129–151` ("**3.3 V does not need its own
converter**" — it comes off the real-time board's onboard regulator), and
`hardware/bom.csv` row `U-BUCK` = R-78E5.0-1.0, 12 V→5 V.

**Proposed replacement** (same edit in all three places): "derives **5 V**
locally with a small buck module (R-78E5.0); 3.3 V comes off the real-time
board's own regulator."

**Confidence:** Certain.

---

## 8. **ADR 0006 and the latency budget still call the breath link differential**

**Severity:** High — the difference between "differential" and "single-ended
with a dedicated sense return" is the entire AGND argument, the conductor
budget, and the choice of receiver.

Stale text:

- `docs/decisions/0006-cv-channel-allocation.md:12` (the Decision table):
  > | **Breath** | **analog, differential over the umbilical** | 0–10V | gain + offset knobs | Trimmed |
- `docs/reference/latency-budget.md:116–118` (Rule 1):
  > **Breath output never digitised at all** — it goes down the umbilical as a
  > differential analog signal (ADR 0003)

Superseded by commit `e20e70e` "Analog breath goes single-ended with a dedicated
sense return" → `0003-breath-sensing-path.md:298–306`: "**Give the analog signal
its own return conductor that carries no power current** … it means the
instrument end needs **only a buffer** … No differential line driver," and
`:326–328` ("Full differential signalling was considered and is not needed").

**Proposed replacement:**

- ADR 0006 table cell: `**analog, single-ended over the umbilical against a dedicated AGND sense return**`
- Latency budget Rule 1: "it goes down the umbilical as a single-ended analog
  signal sensed against its own `AGND` return (ADR 0003)"

**Confidence:** Certain.

---

## 9. **ADR 0004's module parts list still specifies the INA134 difference amp**

**Severity:** High — it is a part number in a parts section, and the part was
replaced precisely because a difference amp could not meet the CMRR requirement
with the protection resistors this design needs.

Stale text — `docs/decisions/0004-cv-interface-module.md:162–164`:

> **INA134 for the breath difference amp.** On-chip matched resistors give ~90 dB
> CMRR against the 60 dB needed (ADR 0003), with no external matching network to
> place or match.

Superseded by commit `5d27543` "Breath receiver becomes a true instrumentation
amp" → `0003-breath-sensing-path.md:322–345` ("**But the receiver is a true
instrumentation amplifier (INA821 / INA828), not a difference amplifier** … a
difference amp's CMRR is set by source-impedance balance, not by the chip"), and
`hardware/bom.csv` row `U-DIFFRX` = "INA821 or INA828".

**Proposed replacement:**

> **INA821 or INA828 for the breath receiver.** A true instrumentation amp, not
> a difference amp: its buffered gigaohm inputs make source-impedance balance
> irrelevant, so the protection resistors can be 10 kΩ and unmatched with no
> CMRR penalty (ADR 0003). It also absorbs the ~2.13× scaling stage, and its
> `REF` pin is where the firmware ambient-zero is injected from DAC channel 6.

**Confidence:** Certain.

---

## 10. **ADR 0003's "Parts" section still shops for a differential driver/receiver pair**

**Severity:** Medium — it is three paragraphs below the sections that decided
there is no driver and the receiver is an in-amp.

Stale text — `docs/decisions/0003-breath-sensing-path.md:518–523`:

> ### Parts
>
> A precision op-amp differential driver and receiver pair is sufficient at this
> bandwidth — no audio-specialty part is required, though THAT1606/THAT1200 or
> DRV134/INA1650 are drop-in options if convenient. What matters is the
> receiver's CMRR and low offset drift, since this feeds a 0–10 V output.

Superseded within the same ADR by `:298–306` (buffer only, no driver) and
`:322–335` (INA821/INA828), and by the BOM rows `U-BUF` (OPA2197IDR) and
`U-DIFFRX`.

**Proposed replacement:**

> ### Parts
>
> Instrument end: half an **OPA2197** as the buffer, on +12 V, sharing its
> package with the reference buffer. Module end: an **INA821 or INA828**
> instrumentation amp sensing `BREATH` against `AGND`. No line driver and no
> audio-specialty differential part — the link is single-ended against a sense
> return, and what matters is the receiver's CMRR and offset drift, since this
> feeds a 0–10 V output.

**Confidence:** Certain.

---

## 11. **The umbilical link budget is still computed at the withdrawn 2 kHz mod rate**

**Severity:** Medium-High — four documents quote a payload and an SPI clock that
are half the real figure, and one of them (ROADMAP E11) is the acceptance
criterion for the link.

Stale text:

- `docs/decisions/0003-breath-sensing-path.md:371`:
  > | **Breath analog, 5 channels at 2 kHz** | **0.32 Mbit/s** | **~0.6 MHz** |
- `docs/decisions/0004-cv-interface-module.md:48–54` — same table, plus "the
  digital link carries only pitch, four mod channels and the zero offset at
  2 kHz".
- `ROADMAP.md:52` (E11): "SPI (~0.6 MHz) and the analog breath pair over the real
  cable at length"
- `docs/reference/latency-budget.md:102`: "~0.6 MHz now that breath is analog"

Superseded by commit `b03a4de` → `docs/decisions/0006-cv-channel-allocation.md:141–160`:
"| Pitch | **4 kHz** … | Mod 1–4 | **4 kHz** | … **The table used to say 2 kHz
and it was wrong twice over.**" At 4 kHz the same five channels are ~0.64 Mbit/s
and want ~1.2 MHz at 50 % bus use. That commit touched only ADRs 0003 (other
sections), 0006 and the BOM; the link-budget tables were not chased.

**Proposed replacement** (ADR 0003 and ADR 0004 tables):

> | **Breath analog, 5 channels at 4 kHz** | **0.64 Mbit/s** | **~1.2 MHz** |

and, in the prose, "the digital link carries only pitch, four mod channels and
the zero offset at 4 kHz (ADR 0006)". ROADMAP E11 → "SPI (~1.2 MHz)"; latency
budget characterisation row → "~1.2 MHz now that breath is analog". Plain
single-ended SPI over twisted pair is still unremarkable at that rate, so the
RS-485-stays-contingent conclusion survives unchanged.

**Confidence:** High. (The 0.32 Mbit/s arithmetic checks out only at 2 kHz:
5 × 32 bits × 2 kHz.)

---

## 12. **Two more SPI clock figures for the same wire: "~2 MHz" and "~1 MHz"**

**Severity:** Medium — three different numbers for one bus across four
documents.

Stale text:

- `docs/decisions/0004-cv-interface-module.md:37`: `SCLK, MOSI, CS      SPI to the DAC, ~2 MHz`
- `docs/decisions/0004-cv-interface-module.md:63`: `SCLK      / DIG_GND     SPI to the DAC, ~1 MHz`
- `docs/reference/latency-budget.md:47`: `| SPI to DAC over umbilical | ~50 µs | 2 MHz |`

Superseded by the link-budget table (finding 11) and by ROADMAP E11. The 2 MHz
figures date from before breath went analog (ADR 0003 commit `8a0ee2d`/`e20e70e`).

**Proposed replacement:** make all of them **~1.2 MHz**, matching finding 11; in
the latency budget keep the ~50 µs stage time (it is dominated by the 32-bit
frame plus overhead and is not sensitive at this precision) but change the note
column to "1.2 MHz".

**Confidence:** Medium-High — the exact number to standardise on is a judgement
call, but the three-way disagreement is definitely stale.

---

## 13. **ADR 0001's Decision still specifies a bare module on a custom carrier, not dev boards**

**Severity:** High — it is the Decision line of ADR 0001 and it contradicts the
build strategy the whole project is now organised around (E13, the package
policy, and three BOM rows marked `not-needed`).

Stale text — `docs/decisions/0001-mcu-and-board-partitioning.md:119–120` and the
Consequences at `:168–172`:

> **ESP32-S3**, as a bare module on a custom carrier — not a dev board — with
> satellite boards distributed along the body.

> - Buy a **plain** S3 dev board plus a **separate** display module, so the bench
>   setup matches the final architecture rather than an integrated-screen board
>   that would have to be unlearned later.
> - Custom carrier design needed eventually: USB-C, ESD protection, boot/reset,
>   3.3V regulation. Espressif publishes reference designs for this.

Superseded by commit `383a5be` → `0013-two-mcu-split.md:205–227` ("**Do not
design a custom ESP32-S3 carrier** … **Instead: keep both dev boards as modules,
on a carrier that has no MCU on it at all**"), by ROADMAP E13, by
`0007-imu-selection.md:147–151` ("the carrier is **passive**, the dev boards plug
into it and stay there"), and by the BOM rows `J-USB`, `U-ESD-USB`, `SW-BOOT`
(all `not-needed`, "Dev boards carry these"). The instrument's selected boards
are an integrated-matrix board and an integrated-AMOLED board — exactly what the
second bullet says not to buy.

**Proposed replacement:**

> **ESP32-S3.** The family choice stands; the packaging does not — **ADR 0013
> keeps both dev boards as modules on a passive carrier**, so there is no custom
> S3 carrier and no bare module. Satellite shift-register boards still
> distribute along the body.

and, in Consequences:

> - Dev boards are not a bring-up stage that gets unlearned — they *are* the
>   final MCUs (ADR 0013). Buy the two selected boards: Waveshare ESP32-S3-Matrix
>   and LilyGO T-Display-S3 AMOLED.
> - No custom carrier circuitry is needed: USB-C, ESD, boot/reset and 3.3 V
>   regulation all live on the dev boards. The carrier is passive.

**Confidence:** Certain.

---

## 14. **ADR 0001's topology diagram and bandwidth figure predate both the MCU split and the analog breath path**

**Severity:** Medium — the status note at the top of ADR 0001 says partitioning
was revised by ADR 0013, but the diagram still asserts a single MCU at the top
with the IMU at the bottom, and the bandwidth line still counts six digital
channels.

Stale text — `docs/decisions/0001-mcu-and-board-partitioning.md:124–139`:

> ```
> TOP   ESP32-S3 module + display (SPI, short) + USB-C
>        |  ribbon: power, slow SPI, LED data
> MID   74HC165 key chain, daisy-chained per cluster
>        |
> BOT   IMU, umbilical connector to the rack module
> ```
> … Bandwidth down the body is trivial: six 16-bit channels at 4kHz is
> ~576 kbit/s, comfortable at 2MHz SPI over twisted pair.

Superseded by ADR 0013 (two MCUs), by ADR 0007 (IMU is onboard the real-time
board at the tail, not a separate satellite), and by ADR 0003 (breath is analog,
so five channels go down the link, not six — see finding 11).

**Proposed replacement:**

> ```
> TOP   Display board (ESP32-S3 + AMOLED) + USB-C on that board
>        |  loom: power, UART pair, LED data
> MID   74x165 key chain, daisy-chained per cluster
>        |
> TAIL  Real-time board (ESP32-S3 + onboard IMU + 8×8 matrix), breath sensor
>       and analog front end, umbilical connector
> ```
> … Bandwidth down the umbilical is trivial: five 16-bit channels at 4 kHz is
> ~0.64 Mbit/s, comfortable at ~1.2 MHz SPI over twisted pair (ADR 0003,
> ADR 0006).

**Confidence:** High.

---

## 15. **ADR 0003 still carries "The ADC specification needs revisiting" and the MCP33131 part number**

**Severity:** Medium-High — an open item that is closed, and a part name that
changed. The same ADR names the MCP3202 four times further down as though it
were settled (it is).

Stale text — `docs/decisions/0003-breath-sensing-path.md:57–71`:

> ### The ADC specification needs revisiting
>
> MCP33131-10 (16-bit, 500 ksps) was chosen when the breath **output** was going
> to be digitised. It no longer is … So 16 bits at 500 ksps is considerable
> overkill, and a cheaper, simpler part at 12–16 bits and a few tens of ksps
> would do.

Superseded by commit `383a5be` → `hardware/bom.csv` row `U-ADC` =
`MCP3202-CI/SN`, 12-bit 2-channel SAR, SOIC-8; by
`0013-two-mcu-split.md:220` (carrier contents); by `0007-imu-selection.md:185`
(SPI2 assignment "DAC8568 + MCP3202"); and by this ADR's own later sections
(`:459`, `:494`) which design the divider and anti-alias cap around the MCP3202.

**Proposed replacement:**

> ### The ADC is the MCP3202, and the specification came down with the output path
>
> MCP33131-10 (16-bit, 500 ksps) was chosen when the breath **output** was going
> to be digitised. It no longer is — the CV path is analog end to end — and what
> the ADC serves now is threshold and note gating, a modulation source, the
> display and USB MIDI. **So the part is an MCP3202**: 12-bit, 2-channel SAR,
> SOIC-8, VDD-referenced so no separate reference chip, 50 ksps against the 4 kHz
> loop, with a spare channel. The SAR-not-delta-sigma rule still holds, and it
> stays external rather than using the ESP32's internal ADC.

**Confidence:** Certain.

---

## 16. **ADR 0003 still says the ambient zero is captured once at startup, in two places**

**Severity:** Medium-High — continuous auto-zero is one of the three named
defences against silent failure in the ROADMAP, and ADR 0003 both asserts it
(`:167`) and contradicts it.

Stale text — `docs/decisions/0003-breath-sensing-path.md:512–516`:

> **Ambient zeroing.** Not lost — solved with a spare DAC channel. … Firmware
> measures ambient at startup exactly as the 2021 code did, and nulls it by
> moving that offset.

and `:231–234`:

> **Thermal.** … this is a **gauge sensor with a temperature-dependent offset
> whose zero is captured once at cold startup.**

Superseded by commit `b03a4de` → `0006-cv-channel-allocation.md:175–186`
("### Ambient zero is continuous, not startup-only … **A zero captured once at
startup is wrong by the time the first piece ends** … decay the zero toward the
current reading whenever breath has been sub-threshold for about 2 seconds"),
echoed at `0003-breath-sensing-path.md:165–168` and in ROADMAP's silent-failure
table. The injection point named here ("the module's analog summing stage") was
also superseded by the in-amp `REF` pin (`0003:578–580`).

**Proposed replacement:**

> **Ambient zeroing.** Not lost — solved with a spare DAC channel. The DAC is
> octal with channels going spare, so **channel 6 drives a firmware-controlled
> DC offset into the breath in-amp's `REF` pin.** Firmware measures ambient as
> the 2021 code did and then keeps doing it: the zero decays toward the current
> reading whenever breath has been sub-threshold for ~2 s (ADR 0006).

and, in the thermal bullet: "this is a sensor with a temperature-dependent
offset, continuously auto-zeroed but only between notes — heat next to it means
the correction is always chasing."

**Confidence:** Certain.

---

## 17. **The tube table is labelled "Helmholtz" but carries the superseded quarter-wave numbers**

**Severity:** Medium — the text six lines below says the quarter-wave model is
wrong and gives a different figure, so the ADR states two resonances for the
same tube.

Stale text — `docs/decisions/0003-breath-sensing-path.md:242–245`:

> | Tube | Delay | Helmholtz |
> |---|---|---|
> | 30 mm (old) | 0.09 ms | 2858 Hz |
> | **400 mm (chosen)** | **1.17 ms** | **214 Hz** |

214 Hz and 2858 Hz are c/4L for 400 mm and 30 mm — quarter-wave figures carried
over from the deleted placement-options table (commit `4391d5d`). Superseded
five lines later by `:249–253`: "**A quarter-wave standing wave is the wrong
model once there is a trap volume at the end** — it is a **Helmholtz
resonator**, and at 3 mL of trap it lands near **320 Hz**."

**Proposed replacement:**

> | Tube | Delay | Quarter-wave (wrong model, kept for scale) | Helmholtz at 3 mL |
> |---|---|---|---|
> | 30 mm (old) | 0.09 ms | 2858 Hz | — |
> | **400 mm (chosen)** | **1.17 ms** | 214 Hz | **~320 Hz** |

with the trap specified at ≤1 mL, which is what actually gets built, and the
restrictor sized at E2 to put the resonance above 500 Hz.

**Confidence:** High.

---

## 18. **ADR 0003's condensation section still argues from "Option A" and short tubes**

**Severity:** Medium — the reasoning is floating: Option A was the 30 mm
top-mounted placement, deleted by commit `0f0c0fe`, and the chosen tube is
400 mm, the *longest* option considered.

Stale text — `docs/decisions/0003-breath-sensing-path.md:615`:

> - Short tubes accumulate less, which Option A gives for free.

Superseded by `:204` (sensor at the bottom) and `:245` (400 mm chosen). There is
no Option A anywhere in the current document.

**Proposed replacement:** delete the bullet, and add in its place:

> - The 400 mm tube accumulates more than a short one would. That is a cost of
>   the placement decision, paid for by the trap and the PTFE plug rather than
>   avoided.

**Confidence:** Certain.

---

## 19. **ADR 0003 says the moisture handling and the resonance model "remain open"; both are decided in the same document**

**Severity:** Medium — a decided thing described as open, in a document a reader
will scan for open items.

Stale text — `docs/decisions/0003-breath-sensing-path.md:551–552`:

> Two consequences that do *not* follow from the bleed question and remain open:
> the moisture handling below, and the tube resonance model.

Superseded by `:249–260` (Helmholtz model, PTFE restrictor, trap ≤1 mL) and by
`:620–645` (vapour: PTFE plug, restrictor limits pumping, sensor is a wear part,
buy two) — both added after this sentence, in commits `0f0c0fe` and `b03a4de`.

**Proposed replacement:**

> Two consequences that do *not* follow from the bleed question are settled
> separately below: the moisture handling, and the tube resonance model. Both
> are decided; what remains is bench sizing of the PTFE restrictor at E2.

**Confidence:** High.

---

## 20. **ADR 0005 specifies the breath pulldown as one resistor on one leg — the arrangement ADR 0003 and the BOM forbid**

**Severity:** Medium — a one-line instruction that, followed literally, caps
CMRR near 19 dB against a 60 dB requirement.

Stale text — `docs/decisions/0005-power-architecture.md:212–215`:

> **Pull down the module's breath receive input**, so that an instrument which is
> switched off — or unplugged — presents 0 V rather than a floating buffer output.
> One resistor, and it means powering down the instrument silences the patch
> instead of leaving a stuck level (ADR 0003).

Superseded by `0003-breath-sensing-path.md:347–350`: "Put the pulldown
**differentially across BREATH–AGND**, not on one leg … 100 kΩ on the + input
alone would cap CMRR near 19 dB," and by `hardware/bom.csv` row `R-PD-BREATH`:
"DIFFERENTIAL across BREATH-AGND not one leg".

**Proposed replacement:**

> **Pull down the module's breath input differentially — one 100 kΩ across
> `BREATH`–`AGND`, not a shunt on one leg** (ADR 0003), so an instrument that is
> switched off or unplugged presents 0 V rather than a floating buffer output.
> One resistor, and powering down the instrument silences the patch instead of
> leaving a stuck level.

**Confidence:** Certain.

---

## 21. **The BOM still tells you to measure the plate cutout, in the same cell that says not to**

**Severity:** High — the BOM is the buy-and-build document, and this is the
single fact that two recent commits were written to correct.

Stale text — `hardware/bom.csv`, row `SW1-n`, notes column:

> "Binary. **Plate cutout must be measured.** Soldered. Thumb keys may want a
> lighter spring - decide at M1. 12.2mm tall … Datasheet and STEP model published
> by Gateron - use them, do not caliper the housing"

Superseded by commits `a051e34` and `25028a8` →
`0002-key-switches-and-mounting.md:110–114` ("**The cutout is 14.0 × 14.0 mm —
the same as standard MX** … An earlier revision of this ADR asserted [the
opposite]"), `docs/reference/ks33-geometry.md`, ROADMAP M1, and
`config/key-layout.yaml:29` (`plate_cutout: 14.0`). Commit `25028a8` edited this
very cell to append the datasheet sentence and left the contradiction in place.

**Proposed replacement** for the notes cell:

> "Binary. Plate cutout 14.0 x 14.0mm, same as standard MX (docs/reference/ks33-geometry.md)
> - the M1 coupon finds the ACHIEVED fit in real material, it does not discover the
> nominal. Soldered. Thumb keys may want a lighter spring - decide at M1. 12.2mm tall,
> 1.70mm pretravel, 3.00mm total travel, 3-pin. Datasheet and STEP model published by
> Gateron - use them, do not caliper the housing"

**Confidence:** Certain.

---

## 22. **A keycap BOM row carries a shift-register recommendation that ADR 0001 decided against**

**Severity:** Medium — wrong row, and the advice contradicts both ADR 0001's
decision and the `U-KEYS` row two lines below.

Stale text — `hardware/bom.csv`, row `CAP1-n` (Tai-Hao MT165-MX keycaps), notes
column:

> "Sold in 5-packs - 18 keys needs 4 packs. Smaller than 18mm MX spacing. **74HC
> preferred over LVC for ~2x input noise margin, not for speed - over an
> unterminated loom LVC's faster edges are worse**"

Superseded by `0001-mcu-and-board-partitioning.md:138–149`: "**the part stays
74LVC165A** … Either family works here. LVC is kept because it is specified
natively at 3.3 V and is already selected — but it is kept **with item 4 above**,
the series termination," and by row `U-KEYS` which states exactly that.

**Proposed replacement** for the notes cell:

> "Sold in 5-packs - 18 keys needs 4 packs. Smaller than 18mm MX spacing"

(the shift-register note belongs only in `U-KEYS`, where it already is, in its
corrected form).

**Confidence:** Certain.

---

## 23. **`key-layout.yaml` orders the shift-register chain "nearest the MCU first" from the wrong end**

**Severity:** Medium — the file is the declared single source of truth for the
bit mapping, and ADR 0001 makes chain ordering an electrical requirement
(propagation skew eats setup, not hold, only if data flows toward the clock
source), which cannot be retrofitted into a bonded body.

Stale text — `config/key-layout.yaml:97–104`:

> # Shift register chain, ordered by physical position down the body, nearest
> # the MCU first (ADR 0001). One 74HC165 per cluster: 4 devices, 32 bits, 18
> # used, 14 spare.
> chain:
>   - cluster: left_hand    # bits 0-7   — 5 used, 3 spare
>   - cluster: left_thumb   # bits 8-15  — 4 used, 4 spare
>   - cluster: right_hand   # bits 16-23 — 6 used, 2 spare
>   - cluster: right_thumb  # bits 24-31 — 3 used, 5 spare

The two halves of the comment can no longer both be true: the left hand is the
*upper* cluster (`:58`, "Left hand is upper (nearer the mouthpiece)") while the
MCU is now at the tail (ADR 0007 `:221–224`, ADR 0003 `:204`). Nearest the MCU is
`right_thumb`.

**Proposed replacement:**

```
# Shift register chain. The real-time board sits at the TAIL (ADR 0007), so the
# chain runs up the body from it: right_thumb is nearest the MCU. Order it so
# serial data flows TOWARD the clock source (ADR 0001) - that makes propagation
# skew eat setup margin, which is recoverable by clocking slower, rather than
# hold margin, which is not. One 74LVC165A per cluster: 4 devices, 32 bits,
# 18 used, 14 spare.
chain:
  - cluster: right_thumb  # bits 0-7   — 3 used, 5 spare   (nearest the MCU)
  - cluster: right_hand   # bits 8-15  — 6 used, 2 spare
  - cluster: left_thumb   # bits 16-23 — 4 used, 4 spare
  - cluster: left_hand    # bits 24-31 — 5 used, 3 spare   (farthest, top)
```

**Confidence:** Medium-High on the ordering being stale (the comment is
self-contradictory as it stands); the exact bit assignment should be confirmed
against whichever end firmware wants as bit 0.

---

## 24. **`key-layout.yaml` treats all 14 spare chain bits as free expansion; ADR 0001 has since claimed 4–6 of them**

**Severity:** Medium — ADR 0001 calls the marker pattern something that "cannot
be added later", and the layout file is where the bit map is supposed to live.

Stale text — `config/key-layout.yaml:106–110`:

> # Spare chain bits are free expansion. Candidates: octave up/down, a mode or
> # menu button, a hold/sustain switch. …
> spare_bits: 14

Superseded by `0001-mcu-and-board-partitioning.md:151–161`: "**Use 4–6 of the 14
spare chain bits as a fixed marker pattern.** The pins, the wires and the devices
already exist, so this costs nothing but the decision to wire it — and it cannot
be added later," and by ADR 0012 `:80–82`, which wants a config-mode entry on a
spare input.

**Proposed replacement:**

```
# Spare chain bits: 14 total, and they are no longer all free.
#   - 4-6 are a FIXED MARKER PATTERN tied high/low at the registers (ADR 0001).
#     Firmware checks them on every read; a frame that fails holds the previous
#     frame and increments a visible error counter. Wire-only, cannot be added
#     after bonding.
#   - 1 is the config-mode input (ADR 0012).
# The rest are free expansion: octave up/down, mode, hold/sustain.
spare_bits: 14
marker_bits: 4        # assign explicit bit positions before the looms are built
config_mode_bits: 1
free_bits: 9
```

**Confidence:** High that the consequence was not chased; the exact split
(4 vs 6) is the author's call.

---

## 25. **ADR 0010 and `firmware/README.md` still route configuration over USB from a host tool**

**Severity:** Medium — configuration moved to a phone over WiFi in ADR 0012, and
the milestone cited (F7) is now the status display.

Stale text:

- `docs/decisions/0010-key-layout-as-data.md:26–27`:
  > The table lives in NVS and is editable — over USB from a host tool (F7), and
  > where practical from the instrument itself.
- `firmware/README.md`, "Data, not code":
  > Both live in NVS and are editable from the display and over USB.

Superseded by `0012-configuration-interface.md:16–18` ("**Configure over WiFi
from a phone, using a web app served by the instrument**"), by ROADMAP F5 (web
config app) and F7 ("Status display … Status only — config lives on the phone"),
and by `firmware/README.md`'s own "Configuration lives on a phone" section
further down the same file.

**Proposed replacement:**

- ADR 0010: "The table lives in NVS and is editable from the web config app over
  WiFi (F5, ADR 0012). The display is status only."
- firmware README: "Both live in NVS on the real-time board and are edited from
  the web config app; every edit round-trips through the real-time board, which
  is the only authority."

**Confidence:** Certain.

---

## 26. **Two documents still describe the display as sharing the MCU, on its own core and SPI host**

**Severity:** Medium — both files contradict themselves two bullets later, where
they state the display is on a different chip.

Stale text:

- `docs/reference/latency-budget.md:130–132` (Rule 3):
  > **Display rendering never blocks the output loop.** Separate SPI host,
  > separate core. A full-screen refresh on a colour LCD is orders of magnitude
  > longer than the whole budget above.
- `firmware/README.md`, Architecture constraints:
  > - **Display renders on the other core, on its own SPI host.** A display
  >   refresh must never block the output loop.

Superseded by ADR 0013 (separate MCU), stated in the very next rule/bullet of
each file, and by the fact that the real-time board's second SPI host is now the
74x165 chain, not the display (`0001:100–104`, `0013:46`).

**Proposed replacement** (both places):

> **Display rendering cannot block the output loop.** It is on a different chip
> (ADR 0013), not merely a different core, and the real-time board's second SPI
> host belongs to the key chain. What remains to manage is the current transient
> a WiFi burst puts on the shared rail.

**Confidence:** Certain.

---

## 27. **ADR 0012 still recommends a small monochrome OLED**

**Severity:** Medium — ADR 0008 decided AMOLED, and the board is bought.

Stale text — `docs/decisions/0012-configuration-interface.md:99–101`:

> That materially changes ADR 0008. A small OLED, previously marginal because a
> four-channel routing matrix needed depth to navigate, is now comfortable and
> arguably preferable.

Superseded by `0008-display-selection.md:23–26` ("**AMOLED.** This supersedes an
earlier lean toward a monochrome OLED") and `:3` (board selected: LilyGO
T-Display-S3 AMOLED), and by BOM row `U-DISP`.

**Proposed replacement:**

> That materially changed ADR 0008, which went on to choose an AMOLED strip
> panel sized for status rather than navigation — the shrunken job made the
> choice cheaper, not the panel smaller.

**Confidence:** Certain.

---

## 28. **ADR 0009 carries two contradictory mass estimates, one of them for the rejected 2.5 in width**

**Severity:** Medium — two sections with the same heading, ~50 g apart, and the
second one totals the width that was not chosen.

Stale text — `docs/decisions/0009-enclosure-construction.md`, the **second**
"### Mass" section:

> | Aluminium top plate, 2 mm | 157 |
> … | **Total** | **~825 (1.8 lb)** |

The first "### Mass" table, three lines above, gives 2.25 in → **~778 g
(1.72 lb)** and 2.50 in → ~825 g. Superseded by commit `b005232` "Width 2.25in",
which added the comparison table and left the older per-part table behind.

**Proposed replacement:** delete the second "### Mass" section, and fold its
per-part breakdown into the first one recalculated at 57 mm (aluminium plate at
whatever thickness ADR 0002 settles — the 2 mm row is itself an open question,
`0002:177–181`).

**Confidence:** High.

---

## 29. **ADR 0009 offers to narrow the body "which costs the two-column layout" — a layout that no longer exists**

**Severity:** Medium — floating rationale: the same ADR declares the two-column
premise void 40 lines earlier.

Stale text — `docs/decisions/0009-enclosure-construction.md`, "What to check at
M2":

> If any of those fail, the fix is narrowing toward 55 mm, which costs the
> two-column layout.

Superseded by the same file's "Nothing on the instrument binds the width" —
"**Two-column key clusters.** Void: keys run in a single line (ADR 0010)" — and
by `0010-key-layout-as-data.md:83–86`.

**Proposed replacement:**

> If any of those fail, the fix is narrowing toward 55 mm, which now costs
> nothing in layout — keys run in a single line — only grip feel and side-panel
> height for the edge lighting.

**Confidence:** Certain.

---

## 30. **ADR 0009's Context still says "three or four" thumb keys**

**Severity:** Low — count settled at four everywhere else.

Stale text — `docs/decisions/0009-enclosure-construction.md`, Context:

> … and three or four mechanical keys on the underside for the left thumb, inset
> so the travel feels right.

Superseded by `0010-key-layout-as-data.md:43–52` ("**18 switches**, decided …
Left thumb | 4"), `config/key-layout.yaml:38`, and the rest of ADR 0009 itself
("the left thumb's four-key arc").

**Proposed replacement:** "…and **four** mechanical keys on the underside for the
left thumb, inset so the travel feels right (ADR 0010)."

**Confidence:** Certain.

---

## 31. **ADR 0008 says the dev boards are already on hand; it later says they are being bought new**

**Severity:** Low-Medium — one of the two was a decision input, and the other
removed it.

Stale text — `docs/decisions/0008-display-selection.md:36–37`:

> - Existing dev boards in this form factor are already on hand from another
>   project.

Contradicted at `:159` in the same file: "Boards are being bought new, so this is
a free choice rather than a constraint," which is what the selection of the
LilyGO board rests on (commit `b57ad9b`, after the scope cleanup in `e394738`).

**Proposed replacement:** delete the bullet. If the on-hand boards matter as
bench stand-ins, say so where it does not read as a selection criterion.

**Confidence:** Medium-High.

---

## 32. **ADR 0014 sizes the LED GPIO question against "17 broken out and 12 needed"**

**Severity:** Low-Medium — the real-time board is selected and the numbers are
known: 16 broken out, 14 used, 2 spare.

Stale text — `docs/decisions/0014-lighting.md:55–56`:

> Two data lines cost one extra GPIO, against roughly 17 broken out and 12 needed
> on the real-time board (ADR 0007).

Superseded by `0007-imu-selection.md:181–192` (broken out: GPIO 1–7, 34–40, 43,
44 = 16; used 14, spare 3 and 4) and `0013:53–58`.

**Proposed replacement:**

> Two data lines cost one extra GPIO, against 16 broken out and 14 used on the
> selected ESP32-S3-Matrix — GPIO 1 and 2, with 3 and 4 spare (ADR 0007).

**Confidence:** Certain.

---

## 33. **ADR 0014's wiring rationale still places the breath sensor at the top**

**Severity:** Low-Medium — floating premise. The conclusion (two independent
strips) survives, but one of the two congested ends is described wrongly, in a
file that elsewhere states the correct placement.

Stale text — `docs/decisions/0014-lighting.md:50–53`:

> chaining needs a data wire crossing the cavity at one end of the runs, and
> **both ends are the congested ones** — the display board and breath sensor at
> the top, the real-time board, IMU and umbilical connector at the bottom.

Superseded by `0003:204` and by this file's own `:261` and `:394` ("The breath
buffer and sensor now live at the bottom with the real-time board").

**Proposed replacement:**

> … **both ends are the congested ones** — the display board at the top, and at
> the tail the real-time board with its IMU and matrix, the breath sensor and its
> analog front end, and the umbilical connector.

**Confidence:** Certain.

---

## 34. **The instrument current figure is quoted as 290–295 mA in three places after it moved to ~320 mA (and a review says 410–430 mA)**

**Severity:** Medium — ADR 0004 itself flags this as "the least trustworthy
number in this document", then computes two ferrite/resistor decisions from an
older, smaller value, and the BOM repeats it.

Stale text:

- `docs/decisions/0004-cv-interface-module.md:205–209`: "it **rules out the
  series-resistor variant**, which is harmless at 50 mA and is not at 290 mA:
  | 2.2 Ω | 0.64 V |"
- `hardware/bom.csv` row `D-REVPOL`: "~0.3-0.4V drop at 290mA"
- `hardware/bom.csv` row `FB-IN`: "NOT a series resistor - we pass 295mA so even
  2.2ohm costs 0.64V"

Superseded by `0004:199` ("~320 mA … **estimated, and a review put it nearer
410–430 mA. Measure at E6 before sizing the load switch**") and by
`0007-imu-selection.md:205–219` (the ~50 mA of idle matrix drivers that moved it).

**Proposed replacement:** quote one figure everywhere — "**~320 mA estimated,
410–430 mA on a review's independent estimate; measured at E6**" — and rerun the
two-line drop table at 400 mA (2.2 Ω → 0.88 V, 10 Ω → 4.0 V), which strengthens
the conclusion rather than weakening it.

**Confidence:** High.

---

## 35. **The BOM states a load-switch current limit that ADR 0004 says must come from measurement**

**Severity:** Low-Medium — a decided-looking number standing on a figure the ADR
disowns; and at 410–430 mA of real draw a ~500 mA limit has little margin.

Stale text — `hardware/bom.csv`, row `U-LOADSW`:

> "Adjustable limit set ~500mA. Inrush ramp into the instrument bulk caps;
> foldback on an umbilical fault…"

Superseded by `0004:216–219` ("**E6 measures the real draw with a current
probe**, and the load switch's current limit is set from that measurement") and
ROADMAP's bench-measurement row "Inrush with a current probe … Sizes the load
switch's current limit from measurement rather than from a guess".

**Proposed replacement:**

> "Adjustable limit - set the R_ILIM resistor from the E6 current-probe
> measurement, not from the estimate (~320mA nominal, review says 410-430mA).
> Inrush ramp into the instrument bulk caps; foldback on an umbilical fault so
> the rack rail is not pulled down"

**Confidence:** High.

---

## 36. **"74HC165" survives in seven places where the selected part is the 74LVC165A**

**Severity:** Low-Medium — a part name that changed. Newer text deliberately
writes "74x165" when the family is not the point; these are older mentions that
name the wrong family outright, and one of them is the file firmware will
generate its bit map from.

Stale text:

- `ROADMAP.md:44` (E4): "74HC165 chain reads all switches"
- `docs/decisions/0001-…:73` (topology diagram), `:189` ("The 74HC165 chain suits
  this geometry well") — in the same ADR that decides "the part stays 74LVC165A"
- `docs/decisions/0005-…:144` (power tree): "74HC165 chain"
- `docs/decisions/0008-…:108`: "The 74HC165 chain reads all 18 switches"
- `docs/decisions/0010-…:18`: "key IDs drive the 74HC165 bit mapping"
- `docs/reference/latency-budget.md:73`: "74HC165 chain read"
- `config/key-layout.yaml:5` and `:98`

Superseded by `0001-mcu-and-board-partitioning.md:138–149` and BOM row `U-KEYS`
(74LVC165A, with 74HC165 named only as the drop-in fallback if E4 misbehaves).

**Proposed replacement:** write **74x165** wherever the family is immaterial
(the majority of these), and **74LVC165A** where a specific part is meant
(BOM-adjacent text, the power tree, the layout file's generator comment).

**Confidence:** High.

---

## 37. **ADR 0006 still numbers the channels as though breath were DAC channel 2**

**Severity:** Low-Medium — internally inconsistent with its own allocation table,
where breath is analog and channels 6 and 7 are internal offsets.

Stale text — `docs/decisions/0006-cv-channel-allocation.md`:

- `:197`: "With breath locked to channel 2 there is no genericity conflict…"
- `:214` and `:245`: "Channels 2–6 need only to be linear and repeatable…" /
  "Channels 2–6 run on ordinary 1% discretes"
- `:430`: "Channels 1 and 2 are silkscreened."
- `:156`: "the loop budget, which already assumes six DAC channels serviced every
  250 µs pass" (and the same six-channel figure in
  `docs/reference/latency-budget.md:122–125`)

Superseded by this ADR's own Decision table (`:8–20`): pitch is ch 1, mods are
ch 2–5, ch 6 is the breath ambient zero, ch 7 is the shared mod offset, breath
never enters the DAC. Five channels are written per pass, not six.

**Proposed replacement:**

- ":197" → "With breath out of the DAC entirely there is no genericity conflict,
  so the knobs sit directly in the analog path…"
- ":214"/":245" → "Channels 2–5, the mod outputs, need only to be linear and
  repeatable…"
- ":430" → "The pitch and breath jacks are silkscreened."
- The loop-budget references → "five DAC channels serviced every 250 µs pass
  (pitch and four mods; the two offset channels are written slowly or once)",
  and the latency budget's 8 kHz arithmetic re-run at 80 µs of DAC time instead
  of 96 µs — which does not change the conclusion that 8 kHz does not close.

**Confidence:** Medium-High (the arithmetic change is small; the numbering is
definitely stale).

---

## 38. **Smaller residue, grouped**

**Severity:** Low. Each is a number or label that a later decision moved past.

| # | Stale text | Superseded by | Proposed replacement |
|---|---|---|---|
| a | `0013:60` "Fourteen chip pins of headroom, against two before." | The table above it now totals **18** of ~30 (commit `551d59e` changed the total and not the sentence) | "Twelve chip pins of headroom, against two before — and, what actually decides the board, two spare broken-out pins." |
| b | `0013:262–263` "not expected at **13 pins** and one job" | Same table: 18 chip pins, 14 broken out | "…at 14 broken-out pins and one job." |
| c | `hardware/bom.csv` row `U-ADC`: "50ksps at 3V3 vs **4-8kHz** needed" | `latency-budget.md:116–126` — "**The 8 kHz end of the old '4–8 kHz' range does not close** … 4 kHz is the number" | "50ksps at 3V3 vs the 4kHz loop" |
| d | `hardware/bom.csv` row `PANEL`: "6HP x 3U (**30.0** x 128.5mm)" | `0004` "A 6HP panel is **30.18 mm** wide — `(6 × 5.08) − 0.3`, +0/−0.2" (commit `4896951`) | "6HP x 3U (30.18 x 128.5mm, +0/-0.2)" |
| e | `hardware/bom.csv` row `U-OPA-PITCH`: "pitch, mod 1-4, **breath scaling**", qty 5 | `0003:335–338` — the in-amp "**absorbs the ~2.13× scaling stage**", so there is no separate breath scaling op-amp in the module | "pitch, mod 1-4, the 2.5V mod offset buffer" — and re-derive the quantity, which is probably 4 duals, not 5 |
| f | `ROADMAP.md:11` Track M "Gated by **Switches arriving; key count decided**" | Switches and caps are purchased (`README.md:15`) and the key count is decided (ADR 0010, 18 switches) | "Gated by — nothing outstanding; M1 can start with switches on the bench" |
| g | `ROADMAP.md:41` E1 cites "(ADR 0008)" for both boards | The Waveshare ESP32-S3-Matrix is ADR 0007; only the LilyGO is ADR 0008 | "Waveshare ESP32-S3-Matrix (ADR 0007) + LilyGO T-Display-S3 AMOLED (ADR 0008)" |
| h | `0007:209`, `0006:177`, `0014:149` "**gauge** sensor" | The part is the MPXV4006**DP**, a differential part whose reference port is left open to reproduce gauge behaviour (`0003:113–146`) | "the breath sensor" / "a temperature-sensitive pressure sensor" — reserve "gauge" for the passage in ADR 0003 that contrasts DP with GP |
| i | `0004:36–39` pre-revision cable block: "MISO — unused today — module ID and presence detect" and "spare — reserved" | `0004:58–72` "**Revised conductor budget** … MISO goes, and with it the planned module-ID line" | Delete the first block; the revised budget is the decision, and keeping both invites someone to wire the wrong pinout |

**Confidence:** High on each individually; (e) is Medium — the op-amp quantity
should be recounted against the schematic rather than taken from here.

---

## Documents that are current

- **`docs/decisions/0002-key-switches-and-mounting.md`** — fully current. The
  cutout, the height, the plate-thickness open item and the "must be measured"
  retraction are all consistent with `ks33-geometry.md`, the ROADMAP and the
  layout file. (Its consequence in `hardware/bom.csv` is not — finding 21.)
- **`docs/reference/ks33-geometry.md`** — fully current.
- **`docs/decisions/0011-licensing.md`** — fully current. (Its index row and the
  README's trailing section are not — findings 1 and 2.)
- **`docs/decisions/0007-imu-selection.md`** — current apart from finding 38(h).
  Its open items are genuinely open.
- **`docs/decisions/0010-key-layout-as-data.md`** — current apart from finding 25
  and the part name in finding 36.
- **`ROADMAP.md`** — substantially current, and the most diligently chased
  document in the repository: the M1/M4 gating, the pre-bond gate, the
  bench-measurement table and the silent-failure table all match the ADRs.
  Exceptions are findings 11, 36 and 38(f), 38(g).

## Pattern worth naming

Three decisions account for most of the staleness above, and each was chased
into the ADR that made it but not into the ones that consumed it:

1. **The sensor and the real-time board moved to the tail** (`4557a8b` →
   `4391d5d` → `f08ee57` → `0f0c0fe` → `551d59e`). Chased into ADRs 0003, 0007,
   0009 (partly), 0014 (partly) and the latency budget; **not** into ADR 0013's
   own placement section, ADR 0008, ADR 0009's breath-tube section, or ADR 0014's
   strip-wiring rationale. Findings 4, 5, 6, 33.
2. **Breath output went analog and single-ended** (`8a0ee2d` → `e20e70e` →
   `5d27543`). Chased into ADR 0003; **not** into ADR 0004's parts list, ADR
   0006's decision table, ADR 0005's pulldown rule, or the latency budget's
   rules. Findings 8, 9, 10, 20.
3. **The mod channel rate went 2 kHz → 4 kHz** (`b03a4de`). Chased into ADR 0006
   only; the link-budget tables it invalidates are in ADRs 0003 and 0004, the
   ROADMAP and the latency budget. Finding 11.
