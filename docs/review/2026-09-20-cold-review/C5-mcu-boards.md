# C5 — Processor architecture and board selection

Review of the two-MCU split, the Waveshare ESP32-S3-Matrix (real-time), the
LilyGO T-Display-S3 AMOLED (display), the inter-processor link, the real-time
throughput budget, and flashing/recovery inside a bonded body.

Scope note: this review does not re-open analog, mechanical or power decisions
except where they bear directly on the processors. No repository file was
modified.

---

## Verdict up front

| Question | Verdict |
|---|---|
| Two-MCU split | **Right — but for a reason the ADRs never state.** Keep it. Rewrite the justification. |
| Real-time board (ESP32-S3-Matrix) | **Adequate, and the pin budget is better than the ADR claims (17 broken out, not 16).** The 8×8 matrix is a real cost that partly undoes the split. |
| Display board (T-Display-S3 AMOLED) | **Right shape, right memory, wrong claim about what it carries.** It has a PMU and a Li-Po charger that ADR 0008 says it doesn't. |
| Inter-processor link | **UART is the right choice.** Rate is fine. Framing and failure behaviour are undesigned. |
| Throughput at 4 kHz | **Closes at 64 % duty — but only if the umbilical SPI runs at ≥ 2 MHz.** At the 0.6 MHz the repo states in two places, it fails outright. |
| Flashing and recovery | **The largest unmitigated risk in the processor architecture.** Neither board can be forced into bootloader mode once the body is bonded, and the display board has no external USB at all. |

---

## Findings

Severity: **Critical** = will brick or silently break the instrument in a way
that cannot be recovered after bonding. **High** = requires a documented
decision change before the carrier is laid out. **Medium** = should be fixed,
recoverable. **Low** = documentation correctness.

---

### F1 — [Critical] Neither board can be put into download mode once the body is bonded

ADR 0009 provides exactly one opening for electronics: a USB-C slot at the tail,
sized for the real-time board's own connector. Both dev boards' `BOOT` and
`RESET`/`EN` buttons are on the boards, inside the lamination. Nothing in the
repository provides an external path to either.

This matters more on the ESP32-S3 than it would on most parts, because of a
specific interaction with USB MIDI:

- With the ROM/IDF **USB-Serial-JTAG** CDC active, `esptool` can reset the chip
  into download mode over the native port using DTR/RTS — no buttons needed.
  This is the mechanism that makes buttonless S3 boards flashable at all.
- **USB MIDI (milestone E5) requires the USB-OTG peripheral**, and on the S3 the
  internal PHY is routed to *either* USB-Serial-JTAG *or* OTG, not both. The
  moment the application selects OTG, the CDC — and with it the DTR/RTS reset
  path — disappears.
- So the recovery path exists only in the window between reset and the
  application claiming OTG. If the application crashes *before* that point, or
  boot-loops, the window is a few hundred milliseconds per power cycle and there
  is no way to hold `GPIO0` low to make the ROM wait.

The consequence is not theoretical: **one bad firmware image flashed the day
before bonding, or any brown-out corruption of the app partition afterwards,
ends the instrument.**

**Fix, all of which must happen before M7/M8 and none of which are available
after:**

1. **Bring `EN` and `IO0` off both dev boards to an external service connector**
   at the tail, alongside the USB-C slot — flying leads soldered to the
   boards' button pads, landing on a 5-pin header (EN, IO0, U0TXD, U0RXD, GND)
   behind a small screwed acrylic cover. This also fixes F9. Cost: five wires
   and a 10 mm slot.
2. **Two OTA partitions plus `CONFIG_BOOTLOADER_APP_ROLLBACK_ENABLE` on both
   images**, so a firmware that fails to call
   `esp_ota_mark_app_valid_cancel_rollback()` self-reverts at the next boot. This
   is the software half of the same guarantee, and it is free.
3. **Make USB MIDI opt-in, not the default.** Boot into USB-Serial-JTAG, hold it
   for a defined window (2–3 s), and switch to OTG only on a command or on a
   held key at boot. USB MIDI is explicitly a bring-up tool (README, firmware
   README) — it should not be what costs the instrument its recovery path.
4. **Implement a software "enter download mode" command** on both the USB
   interface and the UART link: `esp_rom_uart_tx_wait_idle()`, set
   `RTC_CNTL_FORCE_DOWNLOAD_BOOT`, reset.

Confidence: high on the mechanism, high on the consequence. The S3 PHY-routing
behaviour is **from memory** (Espressif TRM / esptool documentation) — verify on
the bench at E1 by flashing a deliberately-broken image with the BOOT button
taped over, and recovering it. That test belongs in E1's done-when.

---

### F2 — [Critical] The display board has no external USB access, and ADR 0013's "open" question is already closed the wrong way

ADR 0013 lists as **Open**: *"Whether the display board is flashed over its own
USB or via the real-time board. Its own is simpler; one connector is tidier."*

That question is not open. ADR 0009 has already answered it by committing to a
single USB-C slot at the **tail**, and ADR 0008/0013 place the display board at
the **top** of a 457 mm body. There is no second opening and the display board's
connector is 300-plus millimetres from the only one there is.

Three consequences that nothing currently addresses:

1. **The display board is flashable exactly once** — on the bench, before
   assembly — unless a path is built.
2. **The display board is the only route from the phone to the real-time board's
   NVS.** ADR 0013's single-source-of-truth rule routes every config edit
   through it. A bricked display board therefore makes a *working* instrument
   permanently unconfigurable: no fingering table edits, no routing matrix, no
   calibration.
3. **OTA is the obvious answer and is currently filed as "nearly free, not a
   priority"** (ADR 0012). In this architecture it is not a nice-to-have, it is
   the display board's primary flash path and it must be built with rollback.

**Fix:**

- **Make WiFi OTA with automatic rollback the display board's primary flash
  path**, promoted from an aside in ADR 0012 to a requirement in ADR 0013.
- **Add a wired fallback**: bring the display board's `U0TXD`, `U0RXD`, `EN`,
  `IO0` down to the real-time board and implement Espressif's
  `esp-serial-flasher` on the real-time side, so a bricked display board can be
  re-flashed through the tail USB-C. This costs **two GPIO** (EN, IO0) — the
  UART pair already exists — and it is the single highest-value use of the
  spare pins. See the pin budget below; it still closes.
- **Add a configuration path that does not go through the display board.** USB
  MIDI SysEx to the real-time board is nearly free once USB MIDI exists, and it
  turns "display board died" from terminal into cosmetic.

Confidence: high. This is a direct contradiction between two Accepted ADRs, of
exactly the kind the 2026-09-20 review found between ADR 0009 and ADR 0014.

---

### F3 — [High] The umbilical SPI clock is stated three different ways, and two of them do not close the 4 kHz loop

| Document | Stated clock |
|---|---|
| ADR 0001 | "comfortable at 2 MHz SPI over twisted pair" |
| ADR 0004, "What goes over the cable" | "SPI to the DAC, ~2 MHz" |
| ADR 0004, "Revised conductor budget" | "SPI to the DAC, **~1 MHz**" |
| ADR 0004, bandwidth table | "**~0.6 MHz**" (from 5 ch × 32 b × **2 kHz**) |
| ROADMAP E11 | "SPI (**~0.6 MHz**)" |
| Latency budget rule 1 | "six DAC channels 96 µs" → implies **2 MHz** |

The 0.6 MHz figure is derived from a **2 kHz** mod-channel update rate. **ADR
0006 subsequently revised that rate to 4 kHz for all five jack channels**, and
made a specific technical argument for it (zero-order-hold image rejection —
see F16, the arithmetic checks out). Nobody propagated that change back to
ADR 0004 or to E11.

At the rate ADR 0006 now requires, the numbers are:

| Umbilical SPI clock | 5 × 32-bit DAC writes | Full loop (my budget, below) | % of 250 µs | Closes? |
|---|---|---|---|---|
| 0.6 MHz (ADR 0004 table, ROADMAP E11) | 282 µs | 348 µs | **139 %** | **No** |
| 1.0 MHz (ADR 0004 conductor budget) | 175 µs | 241 µs | **96 %** | No useful margin |
| **2.0 MHz** (ADR 0001, latency budget) | 95 µs | **161 µs** | **64 %** | **Yes** |
| 4.0 MHz | 55 µs | 121 µs | 48 % | Yes, comfortably |

**The binding number is 2 MHz minimum, and 4 MHz is worth taking if E11 is
clean.** There is no electrical obstacle: 2 m of Cat5e is ~10 ns of propagation,
the DAC8568 accepts 50 MHz, the 74AHCT125 is a 100 MHz-class part, `R-MOSI-SER`
(220 Ω) and `R-SPI-PULL` are already in the BOM.

**The concrete risk is E11 as currently written.** E11's done-when says "SPI
(~0.6 MHz)… on the real cable at length". A clean E11 at 0.6 MHz proves nothing
about the bus the instrument will actually run, and E11 is gated *before* the
body closes. **E11 must be run at the rate the instrument will use, plus
margin** — test at 4 MHz even if you ship 2 MHz.

Confidence: high. Arithmetic independently computed; see the timing budget.

---

### F4 — [High] ADR 0007's broken-out pin list is wrong — the board has 17 usable GPIO, not 16

ADR 0007 states: *"Broken out: **GPIO 1–7** on one side, **GPIO 34–40, 43, 44**
on the other"* → 16. The BOM repeats "16 GPIO broken out (1-7, 34-40, 43, 44)".
ADR 0014 says "roughly 17 broken out and 12 needed".

**ADR 0014 is right and ADR 0007 is wrong.** CircuitPython's board definition
for `waveshare_esp32_s3_matrix` lists the right column as starting at **IO33**:

```
// Top side of the board - right column (bottom to top)
{ MP_ROM_QSTR(MP_QSTR_IO33), MP_ROM_PTR(&pin_GPIO33) },
{ MP_ROM_QSTR(MP_QSTR_IO34), ... }  ... through IO40, then IO43, IO44
```

So the real list is **GPIO 1–7 (7) + GPIO 33–40 (8) + GPIO 43, 44 (2) = 17**.

This is a *good* correction — one more spare than the design thought it had —
and it matters because it is exactly the pin needed for F2's display-board
recovery path. It also raises the stakes on the quad-vs-octal PSRAM question:
**GPIO33 is one of the octal-PSRAM pins**, so if the board ever shipped with
octal PSRAM, the loss would be GPIO33–37 = **five** pins, taking 17 down to 12,
not 16 down to 12.

That question is, however, now settled on paper as well as in Zephyr — the same
CircuitPython board file declares it explicitly:

```
CIRCUITPY_ESP_FLASH_SIZE = 4MB   CIRCUITPY_ESP_FLASH_MODE = qio
CIRCUITPY_ESP_PSRAM_SIZE = 2MB   CIRCUITPY_ESP_PSRAM_MODE = qio
```

**Verified** (source: adafruit/circuitpython `ports/espressif/boards/waveshare_esp32_s3_matrix/{pins.c,mpconfigboard.mk}`, fetched 2026-09-20). The E1
confirmation is still worth doing against the physical board revision, but the
"pin budget collapses to exactly enough" scenario in ADR 0007 is now a
low-probability tail, not a coin flip.

**Fix:** correct ADR 0007's pin list and the BOM note to 17; correct ADR 0007's
octal-PSRAM paragraph from "16 → 12" to "17 → 12".

---

### F5 — [High] "Fourteen chip pins of headroom" is a category error, and the real headroom is three

ADR 0013 closes its pin table with *"**Total on the chip** 18 of ~30 … Fourteen
chip pins of headroom, against two before."*

On a **passive carrier with a fixed dev board**, chip pins that are not brought
to a pad do not exist. The ESP32-S3-Matrix strands GPIO 8, 9, 15, 16, 17, 18,
21, 45, 46, 47, 48 — roughly eleven perfectly good I/O — inside the module, and
no amount of carrier design recovers them. ADR 0013's own build decision (dev
boards as modules, nothing custom) is what makes those pins unreachable, and it
is the right decision; the pin accounting just has to be honest about its price.

The only number that decides anything is **broken-out pins: 17 available**. My
independent count of the requirement is below.

#### My pin budget — real-time board, counted from the ADRs

| # | Function | Source ADR | Pins | Must be broken out? |
|---|---|---|---|---|
| 1 | SPI2 SCK — DAC8568 (umbilical) + MCP3202 | 0001, 0004 | 1 | yes |
| 2 | SPI2 MOSI — same | 0001, 0004 | 1 | yes |
| 3 | SPI2 MISO — MCP3202 `DOUT` only | 0001, 0003 | 1 | yes |
| 4 | `CS`/`SYNC` — DAC8568 | 0004, 0006 | 1 | yes |
| 5 | `CS` — MCP3202 | 0003 | 1 | yes |
| 6 | SPI3 SCK — 74x165 chain (own host; `QH` cannot share MISO) | 0001 | 1 | yes |
| 7 | SPI3 MISO — chain `QH` | 0001 | 1 | yes |
| 8 | `SH/LD` latch — 74x165 chain | 0001 | 1 | yes |
| 9 | WS2815 data, strip A | 0014 | 1 | yes |
| 10 | WS2815 data, strip B | 0014 | 1 | yes |
| 11 | UART1 TX → display board | 0013 | 1 | yes |
| 12 | UART1 RX ← display board | 0013 | 1 | yes |
| 13 | UART0 TXD — console | 0007 | 1 | yes |
| 14 | UART0 RXD — console | 0007 | 1 | yes |
| — | **ADR-stated subtotal** | | **14** | **matches ADR 0007** |
| 15 | Display board `EN` (recovery flash path) | **missing — F2** | 1 | yes |
| 16 | Display board `IO0` (recovery flash path) | **missing — F2** | 1 | yes |
| — | **Honest total** | | **16** | |
| — | Available (F4) | | **17** | |
| — | **Spare** | | **1** (GPIO 3 or 4) | |

Not counted, and correctly so:

| Function | Why it costs no header pin |
|---|---|
| I2C to QMI8658C (GPIO11/12) | Onboard trace — **verified** |
| QMI8658C `INT1`/`INT2` (GPIO10/13) | Onboard trace — **verified**; needed for the FIFO/interrupt scheme in F8 and available at no cost |
| USB D+/D− (GPIO19/20) | Onboard, to the board's own USB-C — **verified** (CircuitPython/Zephyr, per ADR 0007) |
| 8×8 matrix data (GPIO14) | Onboard trace — **verified** |
| DAC8568 `LDAC` | Tie low at the module; the DAC updates on the 32nd SCLK edge |
| DAC8568 `CLR` | Driven by the module's 74HC123 frame watchdog (ADR 0004), not the MCU |
| 74AHCT125 `OE` (×2 boards) | Tied active |
| Config-mode entry | A spare 74x165 chain input (ADR 0012) |

**Conclusion:** the budget closes, with **one** spare pin, not fourteen and not
two. That is enough, but it is not "comfortable", and it means **the next
feature that wants a GPIO does not get one.** If it ever gets tight, the escape
hatch is to buffer the chain's `QH` through a `74AHC125` gate enabled by `CS`
and collapse SPI3 back onto SPI2 — recovering 2 pins at the cost of key-scan /
CV-update contention. Worth writing down as a known option rather than
rediscovering under pressure.

Caution on the spares: **GPIO3 is an ESP32-S3 strapping pin** (JTAG source
select). It is usable as ordinary GPIO but should not be the one you pick first.
Prefer GPIO4. Both are ADC1 channels, as ADR 0007 notes.

---

### F6 — [High] The real-time board's physical position contradicts itself across three ADRs, and ADR 0013's zone table is impossible

| Document | Where the real-time board goes |
|---|---|
| ADR 0013, "Physical placement: three zones" | **Middle** (IMU and umbilical listed separately, at the Bottom) |
| ADR 0013, "Mid-body placement halves the worst-case run" | Middle — worst-case run **205 mm** |
| ADR 0007 | *"the very bottom tip"* — settled, for acceleration sensitivity and the tail matrix window |
| ADR 0009 | Matrix window is in the oak underside **at the tail**; that board must sit there |
| ADR 0003 / ROADMAP E2 | Breath sensor + ADC *"at the bottom with the real-time board"* |

ADR 0013's zone table is not merely inconsistent, it is **physically
impossible**: it puts the IMU at the Bottom and the real-time MCU in the Middle,
when the IMU is soldered to the real-time board. ADR 0007's whole justification
for accepting the Matrix board is that the carrier is passive and "the onboard
IMU *is* the final IMU".

Three documents say bottom; one says middle. **Bottom wins**, and that means
ADR 0013's run-length table is wrong: the real numbers are its own "MCU at the
bottom" column, worst case **360 mm to the display**, not 205 mm.

This is not fatal — it is actually fine — but it needs saying out loud because
the mid-body claim is load-bearing for three other things:

- **It is good for everything except the display link.** Breath ADC drops to
  15 mm (which ADR 0003 explicitly wanted), umbilical to 15 mm, IMU to 15 mm.
  The 360 mm run is the **UART link**, which is the least timing-sensitive
  signal in the instrument — 921600 baud over 360 mm of twisted pair is
  unremarkable.
- **The key chain gets longer**: up to 265 mm to the left-hand cluster, versus
  75 mm mid-body. ADR 0001's five chain-integrity fixes (ground return per
  signal, chained not starred, data flowing toward the clock, 33–68 Ω series
  termination, 100 nF per register) become *more* important, not less. None of
  them change; the margin does.
- **The mass argument disappears.** ADR 0013 justified mid-body partly because
  it puts the heaviest board near the U-bolt and the centre of gravity. At the
  tail it does the opposite, and it is the U-bolt/balance work at M8 that
  absorbs that.

**Fix:** delete the mid-body zone table from ADR 0013, state bottom-tip
placement, and re-derive the loom lengths against it before M4 CAD.

---

### F7 — [High] The 8×8 matrix puts display rendering back on the real-time board

ADR 0013's headline benefit: *"WiFi and display rendering cannot preempt the
output loop because they are not on the same silicon. The core-split discipline
in ADR 0001 stops being something to maintain carefully and becomes a physical
fact."*

ADR 0014 then makes the 64-LED matrix — on the real-time board, on GPIO14 — into
*"the instrument's second display"*: a generic assignable surface rendering
breath bars, a 2-D tilt/roll dot, and preemptive alarm states. That is display
rendering, on the real-time silicon, driven by a peripheral that needs feeding.

The magnitudes, computed:

| Stream | Bits | Wire time @ 800 kHz | Per frame incl. reset | At 30 fps |
|---|---|---|---|---|
| 8×8 matrix (64 × WS2812C) | 1536 | 1.92 ms | **2.22 ms** | 6.7 % of wall time |
| Side strip A (25 × WS2815) | 600 | 0.75 ms | 1.05 ms | 3.2 % |
| Side strip B (25 × WS2815) | 600 | 0.75 ms | 1.05 ms | 3.2 % |

Three RMT TX channels, ~13 % of wall time in transmission. On paper that is
fine — RMT transmits in hardware. The exposure is in **how** it is fed: the
ESP32-S3's RMT has limited per-channel symbol memory, and a non-DMA channel
raises a refill interrupt roughly every 48 symbols, i.e. **every ~60 µs during a
frame**. Three concurrent strands of that on the core running a 250 µs loop is
precisely the class of jitter the two-MCU split was bought to eliminate.

This is recoverable and cheap, but it has to be a decision:

1. **Render on core 0, transmit from core 0, pin the output loop to core 1.** The
   S3's second core is not idle in this architecture — it has the IMU (F8), the
   UART link, USB MIDI and now three LED strands. ADR 0013's claim that the
   real-time board has "one job" is not true and the firmware should not be
   written as if it were.
2. **Use DMA-backed RMT** (or the `led_strip` RMT-with-DMA backend) for the
   matrix specifically, which is the longest strand, and cap the others.
3. **Cap the frame rate.** Nothing on this surface needs 30 fps. 15 fps halves
   every number above and is still smooth for a breath bar.
4. **Blank-and-hold during the critical section** is *not* an option — WS281x
   strands latch on a >280 µs gap, so a deferred refill mid-frame corrupts the
   frame. This is the reason the refill ISR cannot simply be given low priority.

There is also a second-order cost worth stating plainly, because two other
decisions collide on it: **the matrix and the breath sensor are now at the same
end of the instrument.** ADR 0003 moved the sensor to the bottom; ADR 0007 put
the matrix board at the bottom tip; ADR 0014 documents ~0.25 W idle rising to
4.8 W at full field in a body at ~3 K/W, and ADR 0003's breath zero drifts with
temperature. ADR 0014 flags this and M8 measures it, which is the right
response — but the 3 W lighting clamp should be understood as protecting the
*breath zero* as much as the regulator, and that framing is missing.

Confidence: high on the arithmetic, **medium** on the RMT refill interval —
that figure is from memory of the ESP32-S3 TRM and should be confirmed on a
logic analyser at E1, which is a measurement the bench already supports.

---

### F8 — [High] The IMU cannot be read inside the loop, and the accepted fix was never applied anywhere

The 2026-09-20 review's finding R34 established this and the review-resolution
log does not record it being applied. It is still absent from ADR 0007, from the
latency budget's characterisation table, and from the firmware README's
architecture constraints.

My own derivation, independent of R34: the ESP32-S3-Matrix wires the QMI8658C to
**I2C on GPIO11/12** (verified from the CircuitPython board file — `IMU_SDA` =
GPIO11, `IMU_SCL` = GPIO12; SPI is not brought out). A register-burst read of
6 bytes accel + 6 bytes gyro at the QMI8658C's maximum 400 kHz:

```
S + addr(W) + reg + Sr + addr(R) + 12 data bytes, each 9 bit-times
= 3×9 + 12×9 + 2 = 137 bit-times / 400 kHz = 342 µs
```

**342 µs against a 250 µs loop period.** A blocking IDF I2C transaction in the
output loop does not merely cost margin — it guarantees the loop misses. And I2C
is clock-stretchable, so a confused slave stalls the loop indefinitely.

(R34 says 363 µs; I get 342 µs. The difference is bus-turnaround accounting and
is immaterial — both are larger than the period.)

**Fix, and it is straightforward:**

- Read the IMU in a **separate task on core 0** at **200–500 Hz**, never in the
  output loop. The loop consumes the most recent sample from a lock-free slot.
- **Match the QMI8658C's ODR to the read rate.** Reading a 1 kHz sensor stream at
  250 Hz aliases, which would land motion artefacts directly in the modulation
  channel — a failure that presents as "the tilt control feels twitchy" and is
  unfalsifiable by ear. This is R34's most important half and it is the one most
  likely to be lost.
- **Use the FIFO and `INT1`.** Both interrupt lines are already wired (GPIO10,
  GPIO13, verified) and cost nothing.
- Use a **non-blocking / timeout-bounded** I2C driver, and treat a timeout as a
  reportable fault rather than a stall.
- **Add an IMU row to the latency budget.** Gesture-to-CV through the IMU path
  is ~2–5 ms of sampling latency at 200–500 Hz plus filter group delay, which is
  a material fraction of the 5 ms target and currently appears in no table.

Incidentally, this is the concrete reason the real-time board still needs both
cores, and therefore the concrete reason the ESP32-S3 (not a C6) remains correct
for this role even after the display moved off. ADR 0001's core-split argument
survives the two-MCU split; it just changed tenants.

---

### F9 — [Medium] The UART0 console header is inside a body that cannot be opened

ADR 0007 spends two of sixteen pins on *"UART0 console to a carrier test
header"*, and defends it well: *"In a body that cannot be opened, two pins is a
cheap price for keeping a console."*

The reasoning is right and the implementation defeats it. A test header on the
carrier is inside the bonded lamination. Once M6 closes, those two pins drive a
connector nobody can reach, and the console the argument was made for does not
exist.

**Fix:** fold U0TXD/U0RXD into the external service connector proposed in F1.
Same five wires, same slot, and the argument in ADR 0007 becomes true.

---

### F10 — [Medium] The inter-MCU link's framing and failure behaviour are undesigned

The interface choice is right (see "Where the architecture is right"). The rate
checks out: 32 bytes × 10 bit-times × 60 Hz = 19.2 kbit/s = **2.08 %** of
921600 — ADR 0013's "2 %" is **verified correct**. There is a full order of
magnitude of headroom and 921600 is a conservative, well-supported divisor.

What is missing is everything after "framed protocol with checksums":

| Gap | Recommendation |
|---|---|
| **Framing** | **COBS** over the payload, not escape bytes. COBS is self-resynchronising with a guaranteed unambiguous delimiter and bounded 1/254 overhead; an escape scheme desynchronises on a lost byte and needs a timeout to recover. |
| **Integrity** | **CRC-16/CCITT**, not a checksum. ADR 0013 says "checksums". A sum misses transpositions and even-numbered bit errors — exactly what a marginal 360 mm run (F6) alongside an 800 kHz LED data line produces. |
| **Versioning** | Already required by ADR 0013 and the firmware README. Make it the **first byte after the length**, and make a version mismatch a visible state on both surfaces, not a silent drop. |
| **Sequence numbers** | Needed to distinguish "lost frame" from "stale frame". Without one, the display cannot tell a frozen real-time board from a quiet one. |
| **Failure behaviour** | **Undefined today.** It needs writing down explicitly, both directions. |
| **Flow control** | No RTS/CTS pins are available. Use an application-level window: the display board must not send a config blob larger than the real-time board's UART ring without an ACK. At 921600 a 128-byte hardware FIFO overruns in 1.4 ms — well within a garbage-collection pause on the display side. |

**The failure behaviour is the important one**, because it interacts with the
single-source-of-truth rule:

- **Real-time side, link down:** keep playing. Never block the output loop on the
  link. Hold the last validated config. Raise a visible alarm on the surface
  that still works — which, given the display is the thing that died, is the 8×8
  matrix (ADR 0014 already reserves preemptive alarm states for exactly this).
- **Display side, link down or stale:** a status display showing the last-known
  note and breath level is **worse than a blank one** — it is the silent-failure
  pattern the ROADMAP explicitly hunts. Needs a staleness timeout (~250 ms) and
  an unmissable LINK DOWN state.
- **Bidirectional heartbeat**, so each end distinguishes "nothing to say" from
  "gone".
- **The display board's own boot chatter** must not land in the link. ADR 0007
  correctly keeps the *real-time* board's link off UART0 for this reason; the
  same rule has to be applied on the display side, and it is not written down.

---

### F11 — [Medium] The display board carries a PMU and a battery charger that ADR 0008 says it doesn't

ADR 0008's case for the T-Display-S3 AMOLED includes: *"**It carries little that
goes unused.** Boards in this category often bundle a PMIC, battery charging and
an onboard IMU. None of that helps here."*

The LilyGO T-Display-S3 AMOLED has an **SY6970 PMU with Li-Po charging and a
battery connector** (multiple independent sources; the 2026-09-20 review also
lists as a bench item: *"its SY6970 PMU is documented unstable on 5 V without a
battery — in a deliberately battery-free design"*). So the claim is wrong, and
it is wrong in the direction that matters: the unwanted part is not merely
unused, it sits **in the power path** of a board that will be fed 5 V from the
buck (ADR 0005) with no cell attached, inside a body that cannot be opened.

**Fix:**

- **Make this an E1 gate, not a bench curiosity.** Run the display board from
  the R-78E5.0 with no battery, for hours, with WiFi bursting, and scope the
  board's rail. If the PMU misbehaves, the options are (a) a large local bulk
  capacitor at the PMU's `BAT` terminal — `C-BULK-DISP` is already an open BOM
  line and this is what should size it, (b) a small cell, which I would argue
  against on ageing/swelling grounds inside a sealed oak body, or (c) a
  different board.
- Correct ADR 0008's "carries little that goes unused" sentence. It also needs
  to note that an **unpopulated JST battery connector inside a sealed
  cavity is a shorting hazard** and should be removed or insulated before M7.

Confidence: high that the PMU exists (corroborated by web sources and by the
project's own review); **medium** on the specific instability, which is
second-hand in both places. It is a measurement, and the bench exists.

---

### F12 — [Medium] "With 18 free GPIO, this board could in principle run the whole instrument" is probably false

ADR 0008 uses this line to argue that the pin budget which forced ADR 0013 is
"no longer binding", and then keeps the split on isolation grounds anyway. The
conclusion is right; the premise is likely wrong, and it is worth correcting
because it is the sentence someone will quote when they propose collapsing back
to one MCU.

The T-Display-S3 AMOLED is an **ESP32-S3-R8** part — 16 MB flash, **8 MB octal
PSRAM**. Octal PSRAM consumes **GPIO33–37**. If the "18 broken out" figure is
counted from the module's pads rather than from what survives octal PSRAM plus
the on-board QSPI panel (CS, SCK, D0–D3, RST, TE ≈ 8 signals), the usable number
is materially smaller than 18 and quite possibly below the 14–16 this design
needs.

**Fix:** either verify the free-pin count against the board's schematic and
restate it, or delete the claim. Do not leave a sentence in an Accepted ADR
saying a single-MCU build is available on pins if it isn't.

Confidence: **medium.** The R8 variant and the GPIO33–37 octal-PSRAM mapping are
from memory and one corroborating web source; I could not reach LilyGO's wiki
(blocked by the egress proxy) to count the header. Flag as verify-before-quoting.

---

### F13 — [Medium] The module's frame watchdog can be masked by ADC traffic on the shared SPI2 bus

ADR 0004 specifies a retriggerable monostable at the module that asserts the
DAC's `CLR` when *"no valid frame has arrived for N milliseconds"*, parking pitch
subsonic and the mods at 0 V. Good design, and the failure it guards — a hung
real-time board droning the rack forever — is real.

But the DAC and the MCP3202 share **SPI2** (ADR 0001's table, and correctly so —
both tri-state on CS). `SCLK` and `MOSI` therefore run down the umbilical during
**every ADC read as well**, at 4 kHz, whether or not the DAC is being written.

If the 74HC123 is retriggered from `SCLK` — the obvious thing to do, and the
thing "SPI traffic" implies — then a firmware fault that stops updating the DAC
while a healthy breath-sampling task keeps reading the ADC **retriggers the
watchdog forever**, and the rack drones exactly as if the watchdog were not
there.

**Fix:** retrigger the monostable from the **DAC's `CS`/`SYNC` falling edge
only**, which is asserted only for DAC frames. One-line change on a schematic
that does not exist yet; unfixable once the module is built and the instrument
is bonded.

Related, and worth a line in ADR 0004: **the 2 m umbilical is a permanently
attached stub on the ADC's SPI bus.** At the ADC's ~1 MHz ceiling this is
harmless (10 ns propagation), and `R-MOSI-SER` plus the module-side idle pulls
already handle it, but it should be stated so nobody later "simplifies" by
removing them.

---

### F14 — [Medium] No loop-determinism discipline is written down

The whole architecture is justified on determinism, and the firmware README's
"Architecture constraints" section names the 4 kHz loop and the core split but
none of the three things that actually make an ESP32-S3 loop deterministic:

1. **Flash cache stalls.** Any NVS commit, OTA write or SPI-flash erase disables
   the instruction cache, stalling **both cores** for the duration unless the
   code executing is in IRAM. The real-time board persists calibration and
   config to NVS (ADR 0013) — and it does so in response to config edits that
   arrive **while the instrument is being played**, which ADR 0013 now explicitly
   wants to support. The output loop and everything it calls must be
   `IRAM_ATTR`; its tables must be `DRAM_ATTR`; its ISRs must be registered
   `ESP_INTR_FLAG_IRAM`.
2. **PSRAM.** The real-time board's 2 MB of quad PSRAM is unwanted and unused.
   Because it is quad, it costs no GPIO — but leaving it enabled adds a cache
   path with tens-of-microseconds worst-case miss behaviour into the one loop
   that must not have one. **Disable PSRAM entirely in the real-time image.**
   Nothing on that board needs it: the largest structure is the fingering table
   (below), and 512 KB of SRAM is ample.
3. **The fingering table should be a direct index, not a search.** 15 `note` keys
   (ADR 0010) means a 2^15 = 32768-entry lookup. As `uint8` that is 32 KB in
   DRAM and resolution is a single array index — effectively free, and
   constant-time regardless of how baroque the fingering system becomes. That
   property is worth designing in deliberately, because it decouples "the
   fingering system gets more complicated" from "the loop budget".

None of these change any hardware decision. All three belong in the firmware
README next to the 4 kHz rule.

---

### F15 — [Low] Three documents give three different pin counts for the same board

| Document | Broken out | Needed |
|---|---|---|
| ADR 0007 | 16 | 14 |
| ADR 0013 | 16 | 14 |
| `hardware/bom.csv` | 16 | 14 |
| ADR 0014 | ~17 | 12 |

The correct figures are **17 broken out** (F4) and **14 as the ADRs count it**,
**16** once the display-board recovery lines are included (F5). ADR 0014's "12"
appears to predate the SPI2/SPI3 split.

---

### F16 — [Low] Two arithmetic figures are wrong; two others check out

**Wrong:**

- ADR 0001: *"six 16-bit channels at 4kHz is ~576 kbit/s"*. The 16-bit payload is
  6 × 16 × 4000 = **384 kbit/s**; the DAC8568's actual 32-bit frames make it
  6 × 32 × 4000 = **768 kbit/s**. 576 kbit/s is neither, and the figure is used
  to conclude "comfortable at 2 MHz" — which happens to be the right conclusion
  (768 kbit/s is 38 % of 2 Mbit/s), reached from a wrong number.
- `hardware/bom.csv`, `U-ADC`: *"50ksps at 3V3"*. The MCP3202's 50 ksps figure is
  specified at **V_DD = 2.7 V**; 100 ksps at 5 V. At 3.3 V it is nearer
  55–65 ksps, with f_CLK around 1.1–1.2 MHz. Harmless — the design needs 4 ksps —
  but the **f_CLK ceiling** is the number that matters, because it is why the ADC
  and the DAC must be separate `spi_device` handles with different clocks on the
  shared SPI2 host. Worth stating in ADR 0003. *(From memory; confirm against the
  datasheet.)*

**Verified correct, and worth saying so:**

- ADR 0013's UART loading: 32 B × 10 × 60 Hz / 921600 = **2.08 %**. Correct.
- ADR 0006's zero-order-hold argument for 4 kHz mod updates. I recomputed the
  sinc ratios: at f_s = 2 kHz a 400 Hz source's image at 1600 Hz sits **−12.6 dB**
  absolute (−12.0 dB relative to the passed signal); at 4 kHz the image moves to
  3600 Hz at **−19.2 dB**. ADR 0006 states −12.6 dB and −19.2 dB. Both correct.
  This is also the argument that forces the umbilical to ≥ 2 MHz (F3) — ADR 0006
  won that fight and ADR 0004 never heard about it.

---

### F17 — [Low] No configuration path survives a dead display board

Covered under F2 but worth its own line because the fix is cheap and
independent: **USB MIDI SysEx as a config transport to the real-time board.**
USB MIDI already exists (E5), the real-time board already owns and validates all
config (ADR 0013), and SysEx is a well-trodden path for exactly this. It turns
the display board from a single point of configuration failure into a
convenience, and it gives the host-tool path ADR 0010 already assumes
(*"editable — over USB from a host tool"*) something concrete to be.

---

## My timing budget, built from first principles

**Assumptions, stated so they can be attacked:**

- ESP32-S3 at 240 MHz, output loop pinned to core 1, everything else on core 0.
- Umbilical SPI to DAC8568: **2 MHz** (see F3).
- SPI2 to MCP3202: **1.0 MHz** (conservative for V_DD = 3.3 V; f_CLK ceiling
  ~1.1–1.2 MHz).
- SPI3 to the 74x165 chain: **2 MHz** (the chain is limited by loom noise, not
  by setup/hold — accumulated propagation across 4 cascaded 74LVC165A plus
  ~265 mm of wire is ~30 ns against a 250 ns half-period).
- ESP-IDF **polling** transactions with the bus pre-acquired: **~3 µs** software
  overhead each. (Queued/interrupt transactions are 10–25 µs each and would not
  close — that is a firmware requirement, not a detail.)
- DAC8568 frame = **32 bits** (4 prefix + 4 control + 4 address + 16 data +
  4 feature).
- MCP3202 transaction = **24 clocks** (3 bytes).
- Chain = **32 bits** (4 × 74LVC165A, ADR 0001).
- All five jack channels updated every loop (ADR 0006's revised rate table).

### Per-iteration budget, 4 kHz → 250 µs period

| Stage | Derivation | Wire | SW | Total |
|---|---|---|---|---|
| MCP3202 breath read | 24 b ÷ 1.0 MHz | 24.0 µs | 3 µs | **27 µs** |
| `SH/LD` latch pulse | GPIO set/clear | ~1 µs | 1 µs | **2 µs** |
| 74x165 chain read | 32 b ÷ 2.0 MHz | 16.0 µs | 3 µs | **19 µs** |
| Marker-pattern check, 2-sample agreement, asymmetric debounce | integer ops on a 32-bit word | — | — | **2 µs** |
| Fingering resolution | single index into a 32 KB DRAM LUT (F14) | — | — | **1 µs** |
| Breath curve, threshold/note gate, ambient-zero subtraction | ~20 FP ops, hardware FPU | — | — | **3 µs** |
| Routing matrix, 4 channels × (source, scale, offset, curve, slew) | ~60 FP ops | — | — | **6 µs** |
| Pitch DAC write | 32 b ÷ 2.0 MHz | 16.0 µs | 3 µs | **19 µs** |
| Mod 1–4 DAC writes | 4 × 32 b ÷ 2.0 MHz | 64.0 µs | 12 µs | **76 µs** |
| Timer ISR entry/exit, task switch, guard | — | — | — | **6 µs** |
| **Total** | | **121 µs** | **40 µs** | **161 µs** |
| **Period** | | | | **250 µs** |
| **Duty** | | | | **64 %** |
| **Margin** | | | | **89 µs (36 %)** |

**It closes, with 36 % margin.** The dominant term is the DAC transaction at
**59 %** of the used budget — which is why F3's clock question is the one that
decides whether this architecture works at all, and why it is alarming that two
documents state a rate at which it does not.

### Sensitivity

| Variable | Change | New total | Verdict |
|---|---|---|---|
| Umbilical SPI 0.6 MHz | +187 µs | 348 µs | **139 % — fails** |
| Umbilical SPI 1.0 MHz | +80 µs | 241 µs | 96 % — no usable margin |
| Umbilical SPI 4.0 MHz | −40 µs | 121 µs | 48 % — comfortable |
| Queued instead of polling SPI transactions | +~120 µs | 281 µs | **fails** |
| Loop at 8 kHz (125 µs period) | — | 161 µs | **129 % — fails.** Confirms the latency budget's own conclusion by a different route. |
| Two internal DAC channels (ambient zero, mod offset) added every loop | +38 µs | 199 µs | 80 % — closes, but don't. Update them at ~10 Hz. |
| IMU read placed in the loop (F8) | +342 µs | 503 µs | **201 % — fails catastrophically** |

### Work on the other core, which the loop does not pay for but the chip does

| Task | Cost | Rate | Core-0 load |
|---|---|---|---|
| QMI8658C 12-byte I2C read (F8) | 342 µs | 500 Hz | 17 % |
| 8×8 matrix RMT frame (F7) | 2.22 ms | 15–30 fps | 3–7 % |
| Two WS2815 strips (F7) | 1.05 ms each | 15–30 fps | 3–6 % |
| UART link, 60 Hz status | 347 µs of wire | 60 Hz | ~2 % of the UART, negligible CPU |
| USB MIDI (E5 only) | SOF ISR + TinyUSB task | 1 kHz | low single digits |

Core 0 is meaningfully busy — roughly 25–35 %. **That is fine, and it is the
answer to "does the real-time board still need two cores": yes.** It also means
ADR 0013's "13 pins and one job" framing understates what the real-time firmware
is actually doing.

---

## Is the two-MCU split the right architecture?

### The case against, honestly

1. **Both of ADR 0013's stated reasons have since evaporated.** The pin budget
   was the first — and ADR 0008 itself concedes the chosen display board breaks
   out enough GPIO to run the whole instrument (though see F12). The C6 problem
   was the second — and it was never a reason to use two MCUs, only a reason not
   to use a C6 for the real-time role.
2. **The isolation argument is weaker than "physical fact" implies.** A
   dual-core S3 with the loop pinned to core 1, hot code in IRAM, and ISRs
   registered IRAM-safe is *already* strongly isolated from a WiFi stack on core
   0. The genuine cross-core hazards are flash-cache stalls and a handful of
   high-priority radio ISRs, and the first of those is present on the real-time
   board anyway because it owns NVS (F14).
3. **The split's headline benefit is partly undone by ADR 0014**, which puts a
   rendered display back on the real-time board (F7).
4. **The cost is paid in the one currency this project cannot afford: openings
   in a bonded body.** Two MCUs means two flash paths, two recovery paths and
   two ways to brick — through one USB slot (F1, F2). ADR 0013 lists "two
   flashing procedures" as a cost and then never reconciles it with ADR 0009's
   single opening. This is the real price and it is not in the ledger.
5. **Thermal.** A second ESP32-S3 with an AMOLED and an active radio is roughly
   0.5–1 W in an oak-and-acrylic body at ~3 K/W, sharing that budget with a
   breath sensor whose zero drifts with temperature.

### The case for — including the argument the ADRs never make

The decisive argument is not isolation and not pins. It is this chain, all four
links of which are already Accepted decisions:

1. **ADR 0013's package policy forbids QFN/LGA parts** on a hand-assembled
   carrier.
2. **Every 6-axis IMU worth using is LGA-14** (ADR 0007 establishes this).
   Therefore the IMU must arrive pre-reflowed on a module.
3. **The IMU must be low** — not for tilt, which is position-independent, but
   for acceleration, which is a first-class control here (ADR 0007, ADR 0001).
4. **The AMOLED is QSPI and must be short** (ADR 0008), and it must be high,
   where it can be read while playing.

A single MCU cannot satisfy (3) and (4) simultaneously while (1) and (2) force
the IMU onto whatever board the MCU sits on. **The split is not a preference; it
falls out of four prior decisions.** That is a much stronger argument than the
one ADR 0013 makes, and it is the one that should be written down — because it
tells you exactly what would have to change for the split to stop being
necessary.

### Where I land

**Keep the split.** But:

- **Rewrite ADR 0013's Decision section** around the argument above. The current
  justification is a pin budget that no longer binds and a C6 comparison that
  answers a different question.
- **Pay the cost it under-weights.** F1, F2 and F9 are the invoice. Five wires
  and a slot at the tail, OTA with rollback on both images, and USB MIDI made
  opt-in. All of it is cheap now and unavailable after M6.
- **Stop claiming the real-time board has "one job."** It has five (F7, F8), it
  needs both of its cores, and the firmware should be architected that way from
  the first commit rather than discovering it at F3.

---

## Is the real-time board the right one?

**Waveshare ESP32-S3-Matrix — ESP32-S3FH4R2, 4 MB flash, 2 MB quad PSRAM.**

| Criterion | Assessment |
|---|---|
| **Pins** | **17 broken out** (verified), 14 as the ADRs count, **16** honestly (F5). Closes with one spare. Adequate, not comfortable. |
| **Peripherals used** | 2 × SPI host (needed — the `QH` constraint is real), 2 × UART, 3 × RMT TX, 1 × I2C (onboard), USB-OTG. The S3 has 2 general SPI hosts, 3 UARTs, 4 RMT TX, 2 I2C. **Everything the design uses, it has, with nothing left over on SPI.** A third SPI peripheral would require bit-banging or an I2C expander. |
| **Memory** | 512 KB SRAM: ample (largest structure is a 32 KB fingering LUT). 4 MB flash: fits a no-WiFi app plus two OTA slots plus NVS, with no factory partition — acceptable given USB access exists. 2 MB PSRAM: **unwanted; disable it** (F14). |
| **USB** | Native, verified not a bridge — this was correctly identified as decisive. But see F1: native USB is also what creates the recovery problem. |
| **IMU** | QMI8658C, 6-axis, verified. Correct choice (raw accel is the signal; fusion is a liability here). **But I2C-only on this board, and that breaks the loop if read naively** (F8). |
| **Carries unwanted** | 64 × WS2812C (~50 mA / 0.25 W idle, up to 4.8 W), repurposed as a second display — which is clever, and which costs CPU, heat next to the breath sensor, and current the 1 A regulator cannot supply at full field (F7). A WiFi radio that will never be used. |
| **Mechanical** | Requires a matching cutout in the carrier PCB (ADR 0009), so the dev board sits over a hole — a stiffness and header-placement constraint worth drawing early. |

**Verdict: adequate and defensible, chosen for the right reason (the IMU), with
one genuinely unfortunate passenger.** It is not the *best* real-time board; it
is the best one that arrives with a reflowed 6-axis IMU, which is a constraint
the package policy imposed. See Alternatives.

---

## Is the display board the right one?

**LilyGO T-Display-S3 AMOLED (base) — 1.91 in, 536 × 240, RM67162, QSPI,
ESP32-S3-R8, 16 MB flash / 8 MB octal PSRAM.**

| Criterion | Assessment |
|---|---|
| **Panel choice** | **Right.** Off-axis legibility is genuinely the dominant requirement for a display read down the length of a body, and emissive is what wins that. The 2.2:1 strip matches a 57 mm-wide instrument far better than the square alternatives. |
| **Pins** | Needs 2 (UART) + power. Any board clears this. **But see F12** — the "18 free GPIO, could run the whole instrument" claim is probably wrong and should not be relied on. |
| **Memory** | Correctly — even generously — sized. A 536 × 240 × 16 bpp framebuffer is 257 KB and must live in PSRAM; 8 MB covers double buffering with room to spare. 16 MB flash holds LVGL + WiFi + HTTP server + web assets in LittleFS + two OTA slots comfortably. **This is the board's strongest single property and ADR 0008 does not mention it.** |
| **Carries unwanted** | **SY6970 PMU, Li-Po charger and battery connector** (F11), contradicting ADR 0008's explicit claim. Plus a radio (wanted) and, on some revisions, an RTC and TF slot. |
| **Fit** | 60 × 25.5 × 10 mm, lengthwise, taking the length slack from 61 mm to 31 mm. Real, acknowledged, acceptable. |
| **Flashing** | **No external access whatsoever** (F2). This is the finding that matters. |
| **Burn-in** | Correctly identified in ADR 0008. Worth adding one concrete rule: a status display for an instrument should blank on a timeout with no breath and no key activity, not merely dim. |

**Verdict: right board, for mostly right reasons, with one wrong claim (F11) and
one architectural omission (F2).** I would not change it.

---

## Is the inter-processor link sound?

**Interface: UART. Correct, and for the correct reason.** ADR 0013's symmetry
argument is the right one: config arrives asynchronously from the phone while
status flows continuously the other way, and only UART lets both ends initiate
without an attention line. The alternatives are worse here:

| Alternative | Why not |
|---|---|
| **SPI** (real-time as master) | Master-initiated only. The display would need an attention GPIO, so 5 pins instead of 2, and ESP32 SPI-slave mode is awkward to drive reliably. |
| **I2C** | Same asymmetry, plus ESP32 I2C-slave is notoriously unreliable, plus clock stretching would put a peripheral's misbehaviour inside the real-time board's timing. Actively dangerous here. |
| **USB** between the boards | Both would need host/device roles; the real-time board's USB is committed to MIDI. No. |
| **CAN/TWAI** | Robust, symmetric, arbitrated — and complete overkill for 170–360 mm inside one enclosure, with a transceiver to place on a carrier whose whole point is that nothing on it is hard. |

**Rate: fine, and verified.** 2.08 % at 921600. There is room to go to 2 Mbaud
if telemetry (F6 in the roadmap — live breath/IMU/CV to a phone) turns out to
want more, and 360 mm of twisted pair will carry it.

**Framing and failure behaviour: not sound, because they do not exist yet.**
See F10 for the specific recommendations: COBS, CRC-16, version byte, sequence
numbers, bidirectional heartbeat, defined degradation on both sides, and an
application-level window for large config blobs.

**One structural observation.** The link is not only a status channel — under
ADR 0013's single-source-of-truth rule it is the **only** path from the
configuration UI to the authoritative NVS. That makes it a availability-critical
path, not a convenience, and it is the reason F17's USB SysEx backup is worth
building.

---

## Alternatives worth naming

### A1 — Espressif ESP32-S3-DevKitC-1 (N8R2 or N16R8) + a 6-axis IMU breakout

**The alternative I would actually take if the boards were not already chosen.**

What changes:

- **Two USB-C ports**: one native (GPIO19/20, for USB MIDI), and one through a
  **UART bridge with the standard DTR/RTS auto-reset circuit**. That second port
  is a permanent, application-independent flashing, console and recovery path —
  it works when the app has claimed OTG for MIDI, it works when the app is
  crashed, and it works with no buttons. **It dissolves F1 and F9 completely**
  for the cost of one extra slot in the tail face.
- **~36 broken-out GPIO** instead of 17, which makes F2's display-recovery lines
  and anything else free forever.
- **No 64-LED matrix**: removes the RMT load (F7), ~0.25 W of idle heat next to
  the breath sensor, and the 960 mA full-field case the 1 A regulator cannot
  serve. Costs the tail window feature, which the AMOLED already covers for
  alarms.
- **The IMU becomes a breakout module** — Adafruit LSM6DSOX / ISM330DHCX, or
  SparkFun ICM-42688-P. This is **exactly the same move ADR 0013 already makes
  for the MCUs** ("dev boards as modules on a passive carrier"), and ADR 0007
  never considered it: it rejected a bare LGA part and it rejected an IMU on the
  *display* board, but not an IMU breakout on its own, low. Several of those
  breakouts offer **SPI as well as I2C**, which would make F8's 342 µs read into
  a ~10 µs one and could then legitimately live in the loop.
- Costs: 63 × 25.5 mm (fine lengthwise), one more module on the carrier, one
  more connector. Loses the 8×8 second display.

**What it would change in the documents:** ADR 0007's entire "no ESP32-S3 board
exists with a 6-axis IMU and nothing else, so carrying something unwanted is the
price" argument. That argument is only true if the IMU has to be on the MCU
board — and under this project's own build philosophy, it doesn't.

### A2 — Waveshare ESP32-S3-Zero / ESP32-S3-Tiny + an IMU breakout

Same idea, minimal footprint (~24 × 18 mm), ~19–23 broken-out GPIO, native USB,
no LED matrix. Better than A1 on size and pin count; worse than A1 on the point
that matters most, because it has **only** the native USB port and therefore
inherits F1 in full. Take A1's second USB port over A2's smaller outline.

### A3 — Keep the ESP32-S3-Matrix, add the service connector

**This is my recommendation given where the project is**: the boards are
selected, the matrix-as-second-display idea is genuinely good, and F1/F2/F9 are
all fixed by five wires, a small slot and two firmware settings. The delta to A1
is real but not worth a redesign at Phase 0→1 — *provided the service connector
is treated as a hard gate on M8 and not an optional nicety.*

### A4 — RP2350 (Pico 2) for the real-time role

ADR 0013 rejected this for toolchain unity, which on a solo project is a
legitimate and probably correct call. What it gives up is worth recording
accurately, because two of the three are directly relevant to findings above:

- **PIO** would make the 74x165 chain read and hardware-timed DAC updates into
  state machines with zero CPU cost and zero jitter — the key-scan and
  DAC-transaction rows of my timing budget (114 µs of 161 µs) would largely
  vanish.
- **The BOOTSEL ROM bootloader is the best answer to F1 that exists.** An RP2 with
  no valid image in flash falls back to a USB mass-storage bootloader
  automatically — a bricked board re-appears as a drive you drag a `.uf2` onto.
  In a body that cannot be opened, that property is worth a great deal.
- Costs: no radio (the display board has one, so this only matters if the split
  were collapsed), a second toolchain, and no onboard IMU.

**Not recommending it** — but ADR 0013's line *"worth revisiting only if the S3
turns out to struggle with loop determinism"* names the wrong trigger. The
trigger that should reopen it is **recovery**, not determinism, and if F1's
mitigations are judged inadequate then A4 deserves a second look.

### A5 — ESP32-P4 + ESP32-C6 companion radio

ADR 0001 ruled out the P4 for having no radio. That is now a solvable problem —
Espressif's `esp_hosted`/`esp_wifi_remote` pattern pairs a P4 with a C6 over
SDIO. Mentioned only for completeness: it is more silicon, more software and
more RF for an instrument whose real-time load runs at 64 % of a single S3 core.
**Correctly rejected; keep it rejected.**

### A6 — Collapse to one MCU (T-Display-S3 AMOLED at the top + IMU breakout low)

The honest single-MCU option, now that F12 casts doubt on the pin count. It
would buy: one image, one flash path, one recovery problem, one board to brick,
less heat, no protocol. It would cost: LVGL rendering a 257 KB framebuffer and a
WiFi stack on the same silicon as the 4 kHz loop, and it would need its free-pin
count verified against octal PSRAM before it could even be evaluated.

**I do not recommend it** — but it is the strongest argument *against* the split
and ADR 0013 should engage with it rather than with the pin budget it already
beat.

---

## Where the architecture is right

Stated explicitly, because a findings list is a distorted view of a design that
is mostly well reasoned:

1. **The two-MCU split is correct** — forced by package policy + IMU placement +
   QSPI reach, as argued above. The conclusion is right even though the recorded
   reasoning isn't.
2. **UART for the inter-processor link, over SPI and I2C, on symmetry grounds.**
   This is the right call and the right reason, and it would have been easy to
   get wrong.
3. **The dedicated SPI host for the 74x165 chain.** The `QH` totem-pole
   constraint is a genuine hard electrical fact and catching it on paper — before
   a board existed that could never have read its own ADC — is the single best
   piece of work in the repository.
4. **ESP32-S3 over C6 for the real-time role**, for dual-core and USB-OTG. Both
   reasons survive the split (see F8: core 0 is genuinely loaded).
5. **The passive carrier with dev boards as modules.** For a one-off,
   hand-assembled, bonded instrument this is unambiguously right, and holding the
   line against a custom S3 carrier is the correct instinct. Every finding above
   that adds a wire to the carrier should be read as *supporting* that decision,
   not eroding it.
6. **Single source of truth on the real-time board, display persists nothing.**
   Exactly right, and enforced by rule rather than by care, which is the
   distinction that makes it hold.
7. **4 kHz, not 8 kHz.** My independent budget gives 161 µs against a 125 µs
   period at 8 kHz — the same conclusion the latency budget reached by a
   different route and with different numbers.
8. **ADR 0006's zero-order-hold argument for 4 kHz mod updates.** Verified
   correct to a tenth of a dB. It is also the argument that should have forced
   the umbilical clock upward (F3), and it deserved to win that fight too.
9. **Choosing the real-time board for its IMU rather than its antenna**, and
   recognising the onboard IMU as the *final* IMU under a passive-carrier
   architecture. That reframing — from "bring-up convenience" to "this is the
   part" — is the kind of second-order consequence that is easy to miss.
10. **Verifying the board's USB is native rather than a bridge, from
    CircuitPython and Zephyr board definitions rather than product listings.**
    That was decisive, it was done correctly, and it is the methodology that also
    turned up F4 when I repeated it.
11. **Repurposing the 64-LED matrix rather than lamenting it.** F7 is a
    consequence to manage, not an argument against the idea. Given the idle
    current is spent regardless, making it a display is the right response.

---

## Confidence and provenance

| Figure / claim | Status |
|---|---|
| ESP32-S3-Matrix broken-out pins = 1–7, **33**–40, 43, 44 (17) | **Verified** — adafruit/circuitpython `boards/waveshare_esp32_s3_matrix/pins.c`, fetched 2026-09-20 |
| ESP32-S3-Matrix: 4 MB flash `qio`, 2 MB PSRAM `qio` (quad) | **Verified** — same repo, `mpconfigboard.mk` |
| QMI8658C on GPIO11/12, INT1/INT2 on GPIO10/13 | **Verified** — same repo, `pins.c` |
| Matrix (NeoPixel) on GPIO14 | **Verified** — same repo, `pins.c` |
| 12-byte I2C read at 400 kHz = 342 µs | **Derived** (bit-count arithmetic, shown) |
| UART link load = 2.08 % at 921600 | **Derived**, confirms ADR 0013 |
| ZOH image −12.6 dB / −19.2 dB | **Derived**, confirms ADR 0006 |
| Loop budget: 161 µs at 2 MHz, 64 % duty | **Derived** from stated assumptions; SPI driver overhead (~3 µs polling) is **from memory** and is the softest input |
| DAC8568 = 32-bit frame, 50 MHz max SCLK | From memory — verify against datasheet |
| MCP3202 f_CLK ≈ 1.1 MHz and ~55–65 ksps at 3.3 V | From memory — verify against datasheet |
| ESP32-S3 USB PHY routes to *either* USB-Serial-JTAG *or* OTG, not both | From memory (TRM / esptool docs). **The single most load-bearing memory-sourced claim in this review** — F1 depends on it. Test it at E1. |
| ESP32-S3 RMT non-DMA refill interval ~48 symbols | From memory — confirm on a logic analyser at E1 |
| T-Display-S3 AMOLED = ESP32-S3-R8, 16 MB flash / 8 MB octal PSRAM, SY6970 PMU + Li-Po charging | Corroborated by web sources and by the project's own 2026-09-20 review; **LilyGO's wiki was unreachable** (egress proxy). Verify against the board on arrival |
| Octal PSRAM consumes GPIO33–37 | From memory, high confidence |
| "18 free GPIO" on the T-Display-S3 AMOLED is probably overstated (F12) | **Inference**, not verified. Flagged as such |

**Overall confidence:** high on F1–F9 and the timing budget; medium on F11–F13,
where the underlying part behaviour is second-hand; the alternatives section is
judgement, offered as such.

---

## Suggested priority

| Order | Action | Why now |
|---|---|---|
| 1 | **External service connector** (EN, IO0, U0TXD, U0RXD, GND for **both** boards) into the M4 CAD at the tail | F1, F2, F9. Free now, impossible after M6. Nothing else on this list is irreversible. |
| 2 | **Fix the umbilical SPI rate** to ≥ 2 MHz in ADR 0004 and ROADMAP E11 | F3. E11 is a gate, and it currently tests a bus the instrument will not use. |
| 3 | **Resolve the real-time board's position** (bottom, not middle) and re-derive loom lengths | F6. Blocks M4 CAD and the carrier outline. |
| 4 | **Apply R34** — IMU off the loop, ODR matched, FIFO + INT, plus an IMU row in the latency budget | F8. Accepted six months of design ago and never written down. |
| 5 | **OTA + rollback on both images; USB MIDI made opt-in** | F1, F2. Firmware-only, free, and the software half of the recovery guarantee. |
| 6 | **Correct ADR 0007's pin list to 17**, ADR 0008's "carries little unused", ADR 0013's "fourteen chip pins of headroom" and the "one job" framing | F4, F5, F11, F15, F16. Documentation, but these are the sentences future decisions will be made from. |
| 7 | **Watchdog retriggers on DAC `CS`, not `SCLK`** — into ADR 0004 before the module schematic | F13. |
| 8 | **Add the determinism rules** (IRAM/DRAM, PSRAM off, direct-index fingering LUT) to the firmware README | F14. |
