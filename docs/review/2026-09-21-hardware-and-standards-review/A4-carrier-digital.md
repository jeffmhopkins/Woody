# A4 — Carrier, digital side

**Reviewer:** cold hardware review, 2026-09-21. I did not read `docs/review/**`
or `docs/research/**`. Primary source `hardware/controller/carrier.md` §3–§7,
plus `hardware/bom.csv`, ADRs 0001/0004/0007/0008/0012/0013/0014,
`docs/reference/latency-budget.md`, `firmware/README.md`, and
`hardware/module/digital-and-supervision.md` for the far end of the SPI link.

**Network:** `ti.com`, `microchip.com`, `espressif.com`, `waveshare.com`,
`farnell.com`, `digikey.*`, `alldatasheet.com` and every WS2815 datasheet mirror
I tried were refused by the egress proxy. `raw.githubusercontent.com` works, so
the ESP32-S3 facts below come from **ESP-IDF's own documentation sources and
CircuitPython / Zephyr board definition files fetched in this session** — which
is better evidence than a vendor product page. Datasheet facts I could not fetch
are marked `[from memory]` or `[web]` with the search summary named.

**Evidence marks:** `[repo] <file>` · `[calc]` arithmetic inline ·
`[web] <url>` · `[board-def] <file>` fetched this session · `[from memory]`.

Findings are indexed by **circuit node or BOM reference**, not by document
section. Rank and confidence are on every one.

---

## Summary of what I found

| # | Node / ref | Finding | Rank | Confidence |
|---|---|---|---|---|
| D1 | `J-UMB` pins 4/5 | `MOSI` and `CS` share one twisted pair with no ground between them | **Showstopper** | High |
| D2 | loop budget | Real per-pass cost is 196–241 µs, not 122.7 µs; the driver default does not close at all | **High** | High |
| D3 | `R-SCLK-SER`/`R-MOSI-SER`/`R-CS-SER` | 220 Ω overdamps a 100 Ω line; first step lands **below** the receiver's `V_IH` | **High** | High |
| D4 | `U-ADC` SCLK/DIN | The MCP3202's clock and data inputs are **not drawn anywhere** | **High** | High |
| D5 | `IO3`/`IO4` + `J-UMB` pin 3 | A working presence detect is available for two resistors and a spare pin | **High** | High |
| D6 | recovery ladder | Rung 2 is deleted by a persisted NVS setting, and `GPIO0` is inside the body | **High** | High |
| D7 | `MECH-SERVICECOVER` | `BOOT`/`RESET` can be reached through the cover that already exists | **High** | Medium |
| D8 | `J-LED-*` / WS2815 `DIN` | The literal datasheet `V_IH` is 8.4 V; 5 V works by consensus, not by spec | **High** | Medium |
| D9 | matrix on `GPIO14` | SPI2 is claimed by the matrix in the vendor-adjacent config; must be RMT | **High** | High |
| D10 | `IO7`/`IO38`/`IO33` | No idle-state pulls on the key chain. Unretrofittable | **Medium** | High |
| D11 | `J-DISP` | Shrunk to 9-way; the freed conductors should have become grounds | **Medium** | High |
| D12 | `U-MCU-RT` matrix rail | Full-field matrix is 129–136 % of the 5 V regulator, and blank-at-boot cannot run | **Medium** | Medium |
| D13 | `U-ADC` clock | 0.9 MHz is the 2.7 V endpoint, not an interpolation | **Medium** | High |
| D14 | `U-IMU` I2C | A 12-byte IMU read is longer than the whole loop period. Unbudgeted | **Medium** | High |
| D15 | `R-SPI-PULL` (module) | Cable-side `CS` pull-up names a 3V3 rail the module does not have | **Medium** | High |
| D16 | `R-CHAIN-SER` | The chain's driven lines are ESP-fast, not HC-slow. The resistors are right; ADR 0001's objection to them is not | **Medium** | High |
| D17 | flash cache | An NVS commit stalls the 4 kHz loop for tens of ms | **Medium** | Medium |
| D18 | `U-LVLSHIFT` gates | Zero spare gates, not two. LED loom is 8 conductors, not 6–8 | **Low** | Medium |
| D19 | 5 V rail at `HDR-DEV` | No bulk capacitance at the largest load step on the rail | **Low** | High |
| D20 | `R-LED-SER` | Three different values in three places | **Low** | High |
| D21 | `F-CHAIN` | 3.9× hold-current margin, ~2× after cavity derating | **Low** | Medium |
| D22 | `IO39`/`IO40` | Pad-JTAG is gone — but it was never available. No action | Note | High |
| D23 | `IO3` | Strapping pin (JTAG source select). Constrains future use only | Note | High |
| D24 | `J-UMB` pairs | Delay skew 0.9 ns, loss 0.05 dB. Both negligible — say so and stop worrying | Note | High |
| D25 | `J-CHAIN` | The lumped-load claim is correct, with 7× margin | Note (confirmed) | High |
| D26 | `R-LED-PD` | Correct, necessary, and the AHCT125 has no input clamp to VCC, so it is also safe | Note (confirmed) | High |
| D27 | `HDR-DEV` | 2 × 10-way confirmed against the board definition | Note (confirmed) | High |
| D28 | SPI2 IO_MUX | The page's `[from memory]` claim is correct, and the consequence is nil at 2 MHz | Note (confirmed) | High |
| D29 | watchdog | The carrier does not need one. The S3 has three | Note | High |

---

## Part 1 — Pin assignment, verified against the real board

This is the item the brief called highest-value, so it is first and it is
exhaustive.

### The header inventory is correct

Two independent open-source board definitions, both fetched this session:

- `[board-def]` CircuitPython `ports/espressif/boards/waveshare_esp32_s3_matrix/pins.c`
  (`https://raw.githubusercontent.com/adafruit/circuitpython/main/ports/espressif/boards/waveshare_esp32_s3_matrix/pins.c`)
  — left column, preceded by `5V`, `GND`, `3.3V`: **IO7 IO6 IO5 IO4 IO3 IO2 IO1**.
  Right column: **IO33 IO34 IO35 IO36 IO37 IO38 IO39 IO40 IO43 IO44**.
  Then, *not* on the headers: `NEOPIXEL = GPIO14`, `IMU_SDA = GPIO11`,
  `IMU_SCL = GPIO12`, `IMU_INT1 = GPIO10`, `IMU_INT2 = GPIO13`.
- `[board-def]` Zephyr `boards/waveshare/esp32s3_matrix/esp32s3_matrix_esp32s3_procpu.dts`
  — `flash0 reg = DT_SIZE_M(4)`, **`psram0 size = DT_SIZE_M(2)`**,
  `button0 gpios = <&gpio0 0 ...>` label `"BOOT Button"`,
  `led_strip: ws2812@0 ... chain-length = <64>` on `&spi2` with
  `pinmux = <SPIM2_MOSI_GPIO14>`, and `chosen zephyr,console = &usb_serial`.

`[calc]` 3 power + 7 GPIO in the left column, 10 GPIO in the right = **2 × 10
positions, 17 GPIO**. That confirms three things the design leans on:

- `HDR-DEV` is genuinely **2 × 10-way** (D27), which is the input to §7's
  geometry arithmetic (`10 × 2.54 mm = 22.86 mm`).
- **`EN` and `IO0` really are absent.** `IO0` appears only as the BOOT button's
  GPIO in Zephyr's `gpio-keys` node, never as a header pin. `bom.csv`'s
  `HDR-SERVICE` note and §6 are both right `[repo] bom.csv`.
- **PSRAM is 2 MB, i.e. quad.** `[board-def]` Zephyr states the size directly.
  Octal PSRAM consumes `GPIO33–37` (`SPIIO4`…`SPIDQS`) `[from memory]`, so
  ADR 0007's "settled on paper" conclusion is now settled on a devicetree too.
  **`GPIO33–37` are free.** `[repo] 0007`

### Every assigned pin, checked

| Pin | Carrier's use | Silicon role | Verdict |
|---|---|---|---|
| `IO1` | WS2815 strip L data | `ADC1_CH0`, RTC GPIO. Not strapping | **OK.** High-Z at reset → `R-LED-PD` required, see D26 |
| `IO2` | WS2815 strip R data | `ADC1_CH1`, RTC GPIO. Not strapping | **OK**, same |
| `IO3` | *spare* | **Strapping: JTAG signal source select** | OK as spare; see D23 and D5 |
| `IO4` | *spare* | `ADC1_CH3`. No special role | OK; **spend it**, see D5 |
| `IO5` | UART1 TX → display RX | `ADC1_CH4`. No special role | OK |
| `IO6` | UART1 RX ← display TX | `ADC1_CH5`. No special role | OK |
| `IO7` | `SH/LD` latch | `ADC1_CH6`. No special role | OK electrically; **no idle pull**, D10 |
| `IO33` | chain `SER` out | `SPIIO4` — octal PSRAM only | **OK** (quad confirmed). No idle pull, D10 |
| `IO34` | DAC `CS` down the umbilical | `SPIIO5` — octal PSRAM only | **OK.** Idle state matters, D15 |
| `IO35` | SPI2 `SCK` | `SPIIO6` — octal PSRAM only | **OK** |
| `IO36` | SPI2 `MOSI` | `SPIIO7` — octal PSRAM only | **OK** |
| `IO37` | SPI2 `MISO` | `SPIDQS` — octal PSRAM only | **OK** |
| `IO38` | SPI3 `SCK` | No reserved role | OK; no idle pull, D10 |
| `IO39` | MCP3202 `CS` | **`MTCK`** (pad JTAG) | OK — see D22 |
| `IO40` | SPI3 `MISO` (`QH`) | **`MTDO`** (pad JTAG) | OK — see D22 |
| `IO43` | UART0 `TXD` console | **`U0TXD`** — ROM boot log at 115200 | OK, intended |
| `IO44` | UART0 `RXD` console | **`U0RXD`** | OK, intended |
| — | not on the header | `GPIO0` BOOT (strapping), `GPIO45` `VDD_SPI` (strapping), `GPIO46` ROM-log (strapping) `[from memory]` | **No strapping pin is wired to anything.** Good |
| — | not on the header | `GPIO19`/`GPIO20` = USB D−/D+ `[web]` | Reserved for recovery, see D6 |
| — | onboard | `GPIO10–13` QMI8658C, `GPIO14` 8×8 matrix `[board-def]` | See D9, D14 |

`[web]` USB pin confirmation:
`https://raw.githubusercontent.com/espressif/esp-idf/master/docs/en/api-guides/jtag-debugging/configure-builtin-jtag.rst`
gives `esp32s3` D− = GPIO19, D+ = GPIO20.

**Net result: no pin conflict, no strapping collision, and the assignment in
ADR 0007 is buildable as drawn.** That is a genuinely clean result and it is
worth stating plainly, because the rest of this report is not.

---

### D22 — `IO39`/`IO40` take two JTAG pads. Note only. Confidence: high

`IO39 = MTCK` and `IO40 = MTDO` `[from memory]`. Pad JTAG needs all four of
`MTCK`/`MTDO`/`MTDI`/`MTMS` = `GPIO39–42`, and **`GPIO41`/`GPIO42` are not on
the header at all** `[board-def]`. So pad JTAG was never available on this
board and assigning 39/40 costs nothing. Debug is over USB-Serial-JTAG
(`GPIO19/20`), which is what `firmware/README.md` already assumes `[repo]`.
**No action.** Recorded so it is not raised as a finding by someone counting
pin functions.

### D23 — `IO3` is a strapping pin. Note. Confidence: high

`GPIO3` selects the JTAG signal source at reset, but only when the
`STRAP_JTAG_SEL` eFuse is burned; unburned (the shipped state) it is ignored
`[from memory]`. It floats at reset with no internal pull. Harmless today.
**Rule to write down:** if `IO3` is ever given an external load, do not burn
that eFuse, and do not put a hard pull-down on it.

### D28 — SPI2 cannot use IO_MUX. Confirmed; consequence nil. Confidence: high

The page says this `[from memory]` and it is right. `[web]`
`https://raw.githubusercontent.com/espressif/esp-idf/master/docs/en/api-reference/peripherals/spi_master.rst`
lines 526–531 give the ESP32-S3 SPI2 IO_MUX pins explicitly:

```
CS = GPIO10   CLK = GPIO12   MOSI = GPIO11
MISO = GPIO13  HD = GPIO9    WP  = GPIO14
```

Every one of those is spent on the QMI8658C (10–13) or the matrix (14), or is
not broken out (9). So SPI2 on `IO34–37` routes through the GPIO matrix.

The same document then removes the consequence:

> "When an SPI Host is set to 40 MHz or lower frequencies, routing SPI pins via
> the GPIO matrix will behave the same compared to routing them via IOMUX."
> `[web]` `spi_master.rst` line 535

At 2 MHz this is a non-event. The page's instinct to record it so it is not
rediscovered is right; the record can now say "confirmed, and irrelevant".

---

### D9 — SPI2 is claimed by the onboard matrix in the reference config. **High.** Confidence: high

`[board-def]` Zephyr drives the 64 WS2812C parts **on SPI2**:

```
&spi2 { pinctrl-0 = <&spim2_ws2812_led>; led_strip: ws2812@0 { chain-length = <64>; } }
&pinctrl { spim2_ws2812_led { pinmux = <SPIM2_MOSI_GPIO14>; output-low; } }
```

The carrier also puts the DAC8568 **and** the MCP3202 on SPI2, with `MOSI` on
`IO36`. **A host has one `MOSI`.** These configurations are mutually exclusive
and nothing in the repo says so — ADR 0007 records "driven over SPI2 in
Zephyr's configuration" as a curiosity `[repo] 0007` and does not draw the
consequence.

**Firmware constraint, write it into `firmware/README.md`:** on the real-time
board the 8×8 matrix must be driven from **RMT** on `GPIO14`, never from a
GPSPI host. SPI3 is not an alternative — it is the key chain's, and a WS2812
bit-bang over SPI needs `MOSI`, which SPI3 spends on nothing but `MISO`.

**RMT budget, since three LED outputs now land on it** (`IO1`, `IO2`, `GPIO14`):
`[web]` `components/soc/esp32s3/include/soc/soc_caps.h` gives
`SOC_RMT_MEM_WORDS_PER_CHANNEL 48` and `SOC_RMT_SUPPORT_DMA 1`. The ESP32-S3
has 4 TX channels `[from memory]`, so three fit.

`[calc]` cost of *not* using DMA, per LED frame:

```
one WS281x bit = one RMT symbol = 1 word; 48 words per channel
ping-pong threshold at half = 24 symbols = 24 bits
at 1.25 µs/bit that is a refill ISR every 30 µs while a channel is transmitting

strip (25 LEDs at 60/m over 420 mm): 25 × 24 = 600 bits = 750 µs, 25 ISRs
matrix (64 LEDs):                     64 × 24 = 1536 bits = 1.92 ms, 64 ISRs
all three, per animation frame:       25 + 25 + 64 = 114 ISRs
at a 50 Hz animation rate:            5 700 ISRs/s
against a 4 kHz loop:                 5700 / 4000 = 1.4 ISRs per 250 µs period
at ~3 µs each [from memory]:          ~4 µs of jitter injected per loop pass
```

4 µs of 250 µs is tolerable but it is free to avoid: **pin the RMT ISRs and the
LED task to the core that does not run the output loop.** ADR 0013 moved the
display to a second chip, so core 1 of the real-time board is idle `[repo] 0013`
— this is exactly what it is for. Alternatively put the matrix (the big one) on
the one DMA-capable RMT channel.

### D14 — the IMU read is longer than the loop period, and nobody budgeted it. **Medium.** Confidence: high

`[board-def]` the QMI8658C is on **I2C** (`IMU_SDA = GPIO11`, `IMU_SCL = GPIO12`).

`[calc]` a 12-byte burst (accel XYZ + gyro XYZ, 16-bit each) at 400 kHz
Fast-mode I2C:

```
address byte + register byte + repeated start + address byte + 12 data bytes
= 15 bytes × 9 bits (8 + ACK) = 135 bits, plus ~2 bits of start/stop/restart
137 bits / 400 kHz = 343 µs
at 1 MHz Fast-mode-plus:            137 kbit / 1 MHz = 137 µs
```

**343 µs is longer than the entire 250 µs loop period**, and 137 µs is more than
half of it. `docs/reference/latency-budget.md` does not mention the IMU in
either table or in its rules list `[repo]`, and ADR 0007 treats acceleration as
a first-class control `[repo] 0007`.

This is not fatal — it is a scheduling fact that has to be written down before
someone puts `imu_read()` in the 4 kHz loop and spends a week wondering why the
DAC jitters. **Rule:** the IMU is read on core 1, or from its FIFO at a few
hundred hertz, never inline in the output loop. `IMU_INT1 = GPIO10` exists for
exactly this `[board-def]`; use it. Gesture bandwidth is tens of hertz, so
nothing is lost.

---

## Part 2 — SPI2, two devices, two clock rates

### D-confirmed — ESP-IDF does support this, and the page's assumption is right

`[web]` `spi_master.rst`:

- `clock_speed_hz` lives in `spi_device_interface_config_t`, i.e. **per device
  on a shared host**. The driver recalculates it: *"The actual clock frequency
  of a device may not be exactly equal to the number you set, it is
  re-calculated by the driver to the nearest hardware-compatible number… You
  can call `spi_device_get_actual_freq()`"* (line 607).
- There is even a per-*transaction* override: `spi_transaction_t::override_freq_hz`
  (line 609).

`[calc]` what the two devices actually get, from an 80 MHz GPSPI source
`[from memory]`:

```
DAC 2.0 MHz : 80 / 40 = 2.000 MHz exactly
ADC 0.9 MHz : 80 / 88 = 909.1 kHz (above target, rejected)
              80 / 90 = 888.9 kHz  ← what the driver will pick
              24 clocks / 0.8889 MHz = 27.0 µs, not the page's 26.7 µs
```

**The reconfiguration cost is not a separate line item.** It is register writes
inside the driver's device-setup path, and it is already inside the measured
per-transaction overhead below. It is not free, but it is not the thing that
breaks the budget. **The thing that breaks the budget is the per-transaction
overhead itself, which the page omits entirely.**

### D2 — the loop budget. **High.** Confidence: high

`[web]` `spi_master.rst` §"Transaction Duration" gives ESP32-S3 numbers
directly (lines 577–598, `IDF_TARGET_MAX_TRANS_TIME_*`, `esp32s3` column):

| Mode | µs |
|---|---|
| Interrupt transaction via DMA | **26** |
| Interrupt transaction via CPU | **24** |
| Polling transaction via DMA | **11** |
| Polling transaction via CPU | **9** |

These are *"the typical transaction duration for one byte of data"*, measured
with `CONFIG_SPI_MASTER_ISR_IN_IRAM` enabled. The document also gives the
closed form for interrupt transactions: **`20 + 8n/F_spi` µs** (line 662).

`[calc]` **Case A — the driver default (`spi_device_transmit`, interrupt-driven):**

```
DAC : 6 × (24 µs overhead + 32 bits / 2.000 MHz)  = 6 × (24 + 16.0) = 240.0 µs
ADC : 1 × (24 µs overhead + 24 bits / 0.8889 MHz) = 1 × (24 + 27.0) =  51.0 µs
SPI2 total                                                          = 291.0 µs
                                        against a 250 µs period → 116 %
```

**It does not close.** Not marginally — by 41 µs, before a single line of
application code runs.

`[calc]` **Case B — polling transactions wrapped in `spi_device_acquire_bus()`,**
which is what the docs recommend for exactly this ("*strongly recommended to wrap
a series of polling transactions… to avoid the overhead*", line 153). Taking
9 µs as pure fixed overhead is pessimistic (it includes a byte of transfer);
taking 5 µs is the optimistic reading:

```
DAC, pessimistic : 6 × (9 + 16.0) = 150.0 µs      optimistic : 6 × (5 + 16.0) = 126.0 µs
ADC, pessimistic : 1 × (9 + 27.0) =  36.0 µs      optimistic : 1 × (5 + 27.0) =  32.0 µs
CS setup/hold, cs_ena_pretrans = cs_ena_posttrans = 1 bit each:
     DAC 6 × 2 × 500 ns = 6.0 µs ;  ADC 1 × 2 × 1.125 µs = 2.3 µs   → 8.3 µs
SPI2 subtotal                       194.3 µs                          166.3 µs
```

`[calc]` **the key scan is not free either**, whichever way it is done:

```
SPI3, 32 bits at 1.000 MHz = 32.0 µs of BUS time
  polled:            9 + 32.0 = 41.0 µs of CPU, serialised with SPI2's polling
  interrupt + DMA:   26 µs of ISR time, which PREEMPTS the SPI2 busy-wait
                     → still ~26 µs added to wall clock on the same core
  on core 1:         0 µs on the real-time core   ← the only version that is free
```

`[calc]` **the honest per-pass total on the real-time core**, before any
fingering resolution, breath scaling, mod-matrix evaluation, slew, UART status
frame or LED buffer preparation:

```
SPI2 (polling, bus acquired)              166 – 194 µs
SPI3 key scan (same core)                  26 –  41 µs
timer ISR entry + FreeRTOS dispatch [fm]    4 –   6 µs
                                          ─────────────
                                          196 – 241 µs  of 250 µs = 78 – 96 %
```

**Against the page's `122.7 µs of 250 µs → 49 %`** `[repo] carrier.md §4`. The
page counted *bus* time and called it *loop* time. The gap is 60–95 %.

`latency-budget.md` is closer but still low: its rule-1 arithmetic
(`ADC 24 + keys 16 + DAC 96 = 136 µs`) also books zero driver overhead, and its
key-chain figure of 16 µs does not match ADR 0001's 32 µs at 1 MHz `[repo]`.

**What this means.** 4 kHz closes, but only under a specific configuration that
is currently written down nowhere, and the margin at the pessimistic end is
9 µs. The page's own warning box in `latency-budget.md` — *"If the measured
round trip comes back near 200 µs… the answer is not a faster ADC, it is that
4 kHz does not close and the loop rate has to move"* `[repo]` — is pointing at
exactly this, and it is already true on paper.

**Five mitigations, in order of value.** The first three are free.

1. **Polling transactions inside `spi_device_acquire_bus()`/`release_bus()`.**
   Not optional. Write it into `firmware/README.md` as an architecture
   constraint, next to "4 kHz loop pinned to one core". Worth ~100 µs/pass.
2. **Move the key scan to core 1.** SPI3 is independent hardware and the chain
   has its own host precisely so it does not contend `[repo] 0001`. Worth
   26–41 µs/pass. Hand the 32-bit word across with a double buffer, not a lock.
3. **`CONFIG_SPI_MASTER_IN_IRAM` + `CONFIG_SPI_MASTER_ISR_IN_IRAM`
   (+ `CONFIG_FREERTOS_IN_IRAM`).** The quoted 9 µs figure *assumes*
   `ISR_IN_IRAM`; without it, add a cache-miss per call. This also happens to
   be the fix for D17.
4. **Raise the DAC clock once E11 has measured the cable.** `[calc]` at 4 MHz
   the six DAC frames cost `6 × (9 + 8.0) = 102 µs` instead of 150 µs — **48 µs
   back per pass, for free.** This is the same fix as D3: the cable's real
   limit is not 2 MHz, and 220 Ω is what makes it look like it might be.
5. **Do not try to cut the six DAC words.** `firmware/README.md`'s statelessness
   rule is load-bearing and its reasoning is correct `[repo]`. Channel 7 carries
   `V_ref` and must be refreshed with the rest.

**Interrupt latency, for completeness.** ESP-IDF level-1 interrupt entry on the
Xtensa LX7 is ~1.5–2 µs, and an `esp_timer` callback dispatches from a task, so
it inherits scheduler latency on top `[from memory]`. **Do not time the loop
from `esp_timer`.** Use a `GPTimer` ISR that notifies a pinned task, or run the
whole pass in the ISR. Jitter of ±10 µs against a 250 µs period is ±4 % of a
sample interval on a signal band-limited to ~500 Hz, which is inaudible
`[calc]` — the reason to care is not the jitter, it is that scheduler latency is
unbounded when something else misbehaves.

### D13 — the MCP3202's real ceiling at 3.3 V. **Medium.** Confidence: high

The datasheet PDF is unreachable (every Microchip, Farnell, DigiKey, mikroe and
alldatasheet mirror was refused by the proxy). What two independent searches
agree on `[web]`
(`https://www.digikey.sg/htmldatasheets/production/48341/0/0/1/mcp3202.html`,
`https://www.farnell.com/datasheets/1669376.pdf`, both via search summary only):

```
f_SAMPLE(max) = 100 ksps at VDD = 5.0 V
f_SAMPLE(max) =  50 ksps at VDD = 2.7 V
f_CLK = 18 × f_SAMPLE
→ 1.8 MHz at 5.0 V, 0.9 MHz at 2.7 V
Figure 4-2 "Maximum Clock Frequency vs. Input Resistance" is plotted for both
VDD = 5 V and VDD = 2.7 V — the two endpoints, not a continuum
```

**So 0.9 MHz is the 2.7 V *endpoint*, not an interpolation at 3.3 V.** The page
and `latency-budget.md` both describe it as an interpolation `[repo]`. It is
not; it is the conservative floor, and the design is safe *because* of the
mislabel rather than in spite of it.

`[calc]` the actual interpolation:

```
f_SAMPLE(3.3 V) ≈ 50 k + (3.3 − 2.7)/(5.0 − 2.7) × (100 k − 50 k)
                = 50 k + 0.2609 × 50 k = 63.0 ksps
f_CLK(3.3 V)    ≈ 18 × 63.0 k = 1.134 MHz
24 clocks at 1.134 MHz = 21.2 µs  (against 27.0 µs at 888.9 kHz)
```

**Recommendation: design to 0.9 MHz, correct the wording, and bank 1.13 MHz as
measured headroom for D2.** It is worth ~6 µs/pass if the loop turns out tight,
and the "ADC + SPI round trip" bench measurement `latency-budget.md` already
requires will settle it `[repo]`. Note that Microchip's spec is a *sampling*
limit tied to droop on the internal sample capacitor, so it is not a hard
digital ceiling — running faster degrades accuracy rather than failing, which is
the wrong failure mode for a note gate. Do not exceed the measured number.

### D4 — the MCP3202's `SCLK` and `DIN` are not drawn anywhere. **High.** Confidence: high

§4 draws:

```
IO37 MISO ── MCP3202 DOUT only (never leaves the board)
IO39 CS   ── MCP3202 CS
```

and §2 draws the MCP3202 with `CH0`, `CH1`, `VDD/VREF` and decoupling. **The
part's `CLK` and `DIN` pins appear in neither drawing.** They must tap `IO35`
and `IO36`, and **which side of `R-SCLK-SER`/`R-MOSI-SER` they tap is a real
electrical decision that the schematic has to take:**

- **Tap at the MCU pin, ahead of the series resistors** — correct. The
  resistors then have exactly one job, driving the cable, and the ADC sees a
  clean 3.3 V edge from a low-impedance pad. `[calc]` the stub to the ADC is a
  few tens of millimetres; at 2 MHz with a ~2 ns edge, a 30 mm stub is
  `2 × 30 mm × 5.5 ns/m = 0.33 ns` round trip against a 2 ns edge — a lumped
  10 pF load, invisible.
- **Tap after the resistors** — wrong. The ADC then sits behind 220 Ω in
  parallel with 2 m of cable, its input edge is degraded by the cable's ~200 pF,
  and the cable's reflections land on the ADC's clock.

**Draw it, on the pin side, before E13.** This is the kind of hole that becomes
a layout decision made silently by whoever routes the board.

---

## Part 3 — the umbilical, `J-UMB`

### D1 — `MOSI` and `CS` share one twisted pair. **Showstopper.** Confidence: high

The block diagram gives `J-UMB` as:

```
1 BREATH  2 AGND  3 +12V  6 PWR_GND  4 MOSI  5 CS  7 SCLK  8 DIG_GND
```

`[from memory]` T568B pairing: pins **1–2** = pair 2, **3–6** = pair 3,
**4–5** = pair 1, **7–8** = pair 4. So:

| Pair | Conductors | Comment |
|---|---|---|
| 2 | `BREATH` / `AGND` | correct — signal against its own sense return |
| 3 | `+12V` / `PWR_GND` | correct — power against its own return |
| 4 | `SCLK` / `DIG_GND` | correct — the fast edge against its own return |
| **1** | **`MOSI` / `CS`** | **two independent single-ended signals in one pair, with no return between them** |

ADR 0004's conductor budget states this deliberately — *"`MOSI` / `CS`"*
`[repo] 0004` — as if it were a neutral pairing. **It is the opposite of
neutral.** A twisted pair is an *intentionally* tightly coupled structure; it
is engineered so that two conductors share flux and charge as completely as
possible. Putting two unrelated signals in one is the worst available
arrangement, not a default.

**And the victim is the one signal in the system whose corruption is sticky.**
`hardware/module/digital-and-supervision.md` says so itself:

> "A stray edge on `CS` re-frames the 32-bit word, and a DAC8568 frame carries
> the software reset, the clear-code register and the internal-reference enable
> — so a mis-framed word is a **sticky** failure that the 4 kHz refresh does not
> clear, unlike a corrupted data bit which self-heals in 250 µs." `[repo]`

So the design has placed its most fragile signal in the tightest possible
coupling with its busiest aggressor, and has documented, separately, exactly why
that is the worst outcome.

`[calc]` **magnitude.** Capacitive divider model (which ADR 0001 correctly
insists on over `Q/C` `[repo] 0001`):

```
Cat5e mutual capacitance, pair: ≤ 5.6 nF / 100 m = 56 pF/m  [from memory, TIA-568]
  over 2 m:  C_m ≈ 112 pF
conductor-to-everything-else for a UTP conductor ≈ 30–40 pF/m [from memory]
  over 2 m:  C_v ≈ 60–80 pF

coupled step on an OPEN victim = V_agg × C_m/(C_m + C_v)
                               = 3.3 V × 112/(112 + 70) = 3.3 × 0.615 = 2.03 V
```

The victim is not open at the near end — `IO34` drives it through 220 Ω. But
the near-end driver's influence takes one cable transit to arrive:

```
Cat5 velocity factor ≈ 0.67 → 4.98 ns/m → 2 m = 10.0 ns one way, 20 ns round trip
```

**So for the first ~20 ns after every `MOSI` edge, the far end of `CS` is
electrically open and sees the full coupled step.** Derate the 2.03 V hard — by
half, for the twist averaging out some of it — and you still get ~1 V on a node
whose DC level is:

```
CS held low: 3.3 V × 250 Ω /(250 Ω + 10 kΩ pull-up) = 80 mV
80 mV + 1.0 V = 1.08 V   against 74AHCT125 V_IL(max) = 0.8 V  → already violated
80 mV + 2.0 V = 2.08 V   against 74AHCT125 V_IH(min) = 2.0 V  → frame terminated
```

The 74AHCT125 at the module has **no input hysteresis** and ~5 ns of propagation
delay `[from memory]`, so it will faithfully pass a 20 ns excursion. And the
module's `R-SPI-PULL` pulls `CS` **up**, which biases the glitch in the
dangerous direction.

**Failure signature:** the DAC's `SYNC` rises mid-frame, the frame is discarded,
and the *next* 32 clocks land misaligned across a frame boundary. A misaligned
DAC8568 word can land on the software-reset command, the clear-code register or
the internal-reference-enable — the exact sticky set `digital-and-supervision.md`
names. It will be rare, load-dependent, and will present as "the pitch jack
occasionally goes somewhere odd and stays there until a power cycle".

**Fixes, ranked. Take at least two.**

1. **Swap the pair assignment.** Put `CS` with `DIG_GND` on pair 4 (pins 7/8)
   and `SCLK` + `MOSI` together on pair 1 (pins 4/5). Free at both connectors;
   nothing else changes. **It converts the worst failure mode into the
   mildest**, by the module page's own taxonomy: `MOSI`→`SCLK` crosstalk costs
   at most a corrupted data bit, which self-heals in 250 µs. The cost is that
   `SCLK` loses its dedicated return and its return current flows in the `CS`
   pair — a larger loop, but `SCLK` is a clock and a slightly noisier clock is
   not a sticky failure. **This is the single highest-value change in this
   report and it costs nothing but a pinout decision taken before E13.**
2. **Adopt the 74AHCT14 hex Schmitt at the module.**
   `digital-and-supervision.md` already wants it for three other reasons —
   `CLR` inversion, edge cleanup on all three lines, and two prior reviews
   `[repo]`. At 5 V an AHCT14 has roughly 0.4–0.9 V of hysteresis
   `[from memory]`, which swallows this glitch outright. **One part, now four
   jobs.** The module page declined it as "a design decision rather than a
   correction" and said it should be taken with the SPI edge-cleanup question.
   This *is* the SPI edge-cleanup question. Take it.
3. **Drop the series resistance to 100 Ω** (D3). It halves the near-end source
   impedance and so halves the residual glitch once the near-end driver's wave
   arrives.
4. **Do not rely on firmware.** `cs_ena_pretrans`/`posttrans` separate `CS` and
   `MOSI` *edges* in time, which is worth setting anyway, but the hazard here is
   a `MOSI` edge glitching a `CS` that is held static mid-frame. No SPI driver
   setting reaches that.

### D3 — 220 Ω on `SCLK`/`MOSI`/`CS` is the wrong value. **High.** Confidence: high

The page derives 220 Ω from an **RC corner** — "220 Ω into ~200 pF of cable is a
3.62 MHz corner" `[repo] carrier.md §4`. That model is not applicable. `[calc]`:

```
t_r of an ESP32-S3 pad ≈ 2–5 ns [from memory]
cable one-way delay    = 2 m × 4.98 ns/m = 10.0 ns ; round trip 20 ns
lumped-model validity  requires t_r > ~6 × T_pd = 60 ns
2–5 ns ≪ 60 ns → this is a transmission line, and Z0 = 100 Ω, not a capacitor
```

Treat it properly. Source = series resistor + pad impedance (take 40 Ω; the
conclusion is unchanged at 25 Ω or 60 Ω). Far end = an AHCT125 input, ~5 pF and
10 kΩ — effectively open, so `ρ_L = +1`.

`[calc]` **220 Ω** (`R_s = 260 Ω`, `ρ_s = (260−100)/360 = +0.444`):

```
incident wave      V1 = 3.3 × 100/(100+260)                = 0.917 V
t = 10 ns, far end = 2 × 0.917                             = 1.833 V   ← PLATEAU
t = 30 ns, far end = 1.833 + 2 × 0.917 × 0.444             = 2.648 V
t = 50 ns          = 2.648 + 2 × 0.407 × 0.444             = 3.010 V
t = 70 ns                                                  = 3.171 V
```

**The first tread of the staircase is 1.833 V. The 74AHCT125's `V_IH(min)` is
2.0 V. The receiver's input therefore sits 0.17 V below its own switching
threshold — inside the forbidden band between `V_IL` 0.8 V and `V_IH` 2.0 V —
for a full 20 ns on every single edge.** At 25 Ω of pad impedance it is 1.913 V;
at 60 Ω it is 1.77 V. The conclusion does not move.

20 ns in the linear region of a non-hysteretic AHCT gate is the textbook
condition for output oscillation, and on a **clock** line the consequence is
double-clocking. It also comfortably violates TI's AHC/AHCT input transition-rate
guidance `[from memory]`. This is not "margin against a 3.62 MHz corner"; it is a
receiver being held at its trip point 4 million times a second.

`[calc]` **68 Ω**, which ADR 0004's corrected text already prefers
`[repo] 0004` (`R_s = 108 Ω`, `ρ_s = +0.038`):

```
incident          V1 = 3.3 × 100/208 = 1.587 V
t = 10 ns, far end   = 3.17 V      ← full swing in ONE transit, clean
residual steps       ±0.12 V
```

Electrically excellent. **But** it gives up the other job the resistors were
bought for — `D1-missing-protection.md` finding 10 asked for *"series current
limiting"* `[repo] carrier.md §4`:

```
fault current into a shorted conductor: 3.3 V / 68 Ω  = 48.5 mA
ESP32-S3 pad VOH/VOL are specified to 40 mA [from memory] → 48.5 mA is over spec
                                       3.3 V / 220 Ω = 15.0 mA  (safe, but see above)
```

`[calc]` **100 Ω resolves both** (`R_s = 140 Ω`, `ρ_s = (140−100)/240 = +0.167`):

```
incident          V1 = 3.3 × 100/240 = 1.375 V
t = 10 ns, far end   = 2.750 V   ← 0.75 V ABOVE V_IH on the first step
t = 30 ns            = 2.750 + 2 × 1.375 × 0.167 = 3.209 V
fault current        = 3.3 / 100 = 33 mA  ← inside the 40 mA pad spec
robustness: at 25 Ω pad → 2.93 V first step ; at 60 Ω pad → 2.54 V. Both clear 2.0 V
```

**Recommendation: 100 Ω on all three of `R-SCLK-SER`, `R-MOSI-SER` and
`R-CS-SER`.** Not 220 Ω, not 68 Ω. It clears `V_IH` on the incident step with
0.54–0.93 V of margin across the plausible pad-impedance range, and it keeps a
shorted conductor inside the pad's own rating. `R-MOSI-SER` already exists at
220 Ω with qty 1 `[repo] bom.csv`; change the value and the quantity together.

**And this unlocks D2's mitigation 4.** With 100 Ω the line settles in ~30 ns.
At 4 MHz the half period is 125 ns. The clock rate is limited by the module's
setup/hold and by E11's measurement, not by the cable — so the 48 µs/pass that
the loop budget needs is available once someone puts a logic analyser on it.

### D24 — pair skew and cable loss are non-issues. Note. Confidence: high

Stated so they stop being worried about. `[calc]`:

```
delay skew between Cat5 pairs: ≤ 45 ns / 100 m [from memory, TIA-568]
  over 2 m: 0.9 ns — against a 250 ns SCLK half period and a DAC8568
  setup time of order 10 ns [from memory]. Three orders of margin.

insertion loss, Cat5e: ~2.1 dB/100 m at 1 MHz, ~2.6 dB/100 m at 2 MHz [from memory]
  over 2 m: 0.05 dB. Not a term.
```

**Crosstalk from `SCLK` into the `BREATH`/`AGND` pair** — the thing ADR 0004
warns about `[repo] 0004`:

```
Cat5e pair-to-pair NEXT ≥ 35.3 − 15·log10(f/100 MHz) dB   [from memory, TIA-568]
at 2 MHz: 35.3 + 25.5 = 60.8 dB → 3.3 V × 10^(−60.8/20) = 3.0 mV differential
single-ended drive of one conductor is worse than the balanced case the spec
assumes; derate by 10× → ~30 mV of differential noise at 2 MHz and harmonics
```

Then the receive path kills it `[calc]`:

```
receive filter at 482 Hz, one pole [repo] latency-budget.md
attenuation at 2 MHz = 20·log10(2e6/482) = 72.4 dB
30 mV → 7.5 µV at the in-amp. Against a 10 V output span: 0.00008 %.
```

**Linear coupling is a non-event.** The real hazard is **rectification**, and
`breath-receive-stage.md` already puts the filter ahead of the in-amp
*"because that is the only place it can stop RF rectification"* `[repo]` —
which is the correct and sufficient answer. One thing to look for at E11 that
nobody has named: **SPI2 is silent for ~25 % of each 250 µs period and bursts
for the rest, so any rectified residue is amplitude-modulated at exactly
4 kHz** — an audible tone, not a hiss. Scope the breath jack with the SPI link
running and idle, and difference them.

### D15 — the module's cable-side `CS` pull-up names a rail that does not exist. **Medium.** Confidence: high

`bom.csv` `R-SPI-PULL`: *"CABLE-SIDE CS PULLS TO 3V3, NOT +5V"* `[repo] bom.csv`.
`[calc]` I grepped every module page for a 3.3 V rail: `power-entry.md`,
`digital-and-supervision.md`, `mod-channels.md`, `pitch-stage.md`,
`breath-receive-stage.md` and ADR 0004's power tree give **±12 V, bus +5 V and
the LM317's 5.21 V, and nothing else.** There is no 3V3 anywhere on the module.
**The row is un-buildable as written.**

The row's own reasoning is also why it cannot simply become +5 V:

```
[calc] with the instrument unpowered and the cable connected, +5 V through 10 kΩ
into the ESP32's input clamp:  (5 − 0.7) / (10 kΩ + 220 Ω) = 421 µA
and the node then sits at ~0.7 V, so "CS idle high" is not achieved
```

That matches the BOM's 430 µA figure `[repo]`.

**Recommendation — and it lands on this board, which is why it is in this
report.** Put the `CS` idle pull-up **on the carrier**, at the carrier's 3V3,
where the rail genuinely exists: `10 kΩ from IO34 to 3V3`. With the instrument
powered — which is every state in which SPI traffic exists — the whole cable's
`CS` is then held high by a rail that is present, referenced to the driver that
owns it. With the instrument unpowered, the module's **DAC-side** pull to AVDD
5.21 V is what protects the DAC, and it already does `[repo] bom.csv`. The
cable-side pull then has only one job left — stopping the AHCT125's input
crowbarring — for which +5 V through 10 kΩ, sitting at 0.7 V, is adequate:
`SCLK` and `MOSI` are pulled **down** at both ends, so a `SYNC` held low with no
clock edges shifts nothing.

Cost: one 0805 on the carrier. It also removes the only rail the module does not
have.

---

## Part 4 — the key chain, `J-CHAIN` / `R-CHAIN-SER`

### D25 — the lumped-load claim is correct, with 7× margin. Confirmed. Confidence: high

ADR 0001 stakes the whole per-cluster topology on *"HC's slow edges make 265 mm
an ordinary LUMPED LOAD rather than a transmission line"* `[repo] 0001`. It
holds, in the `QH` direction. `[calc]`:

```
ribbon, alternating ground: Z0 ≈ 100 Ω, ε_r ≈ 2.5 → 5.3 ns/m [from memory]
265 mm → T_pd = 1.4 ns one way, 2.8 ns round trip

load: 0.265 m × 50 pF/m = 13 pF ribbon
    + 4 connectors × ~2 pF = 8 pF
    + 4 × 74HC165 input, 3.5 pF each = 14 pF
                                    ≈ 35 pF  (ADR 0001 says ~26 pF; same order)
74HC165 drive at 3.3 V ≈ ±3.2 mA [from memory, interpolating the 4.5 V ±4 mA spec]
edge = C·ΔV/I = 35 pF × 1.65 V / 3.2 mA = 18 ns
plus R-CHAIN-SER 100 Ω × 35 pF = 3.5 ns
                              → t_r ≈ 20 ns

lumped criterion t_r > 6 × T_pd(one way) = 8.4 ns.  20 ns / 8.4 ns = 2.4× — pass
against round trip: 20 / 2.8 = 7× — comfortably lumped
```

Against a 1 MHz clock (500 ns half period) this is two orders of margin. **The
chain is fine and 1 MHz is not close to anything.** ADR 0001's "should not be
pushed much past it" is prudent rather than necessary.

### D16 — but the *driven* lines are not HC-slow, and `R-CHAIN-SER` is right. **Medium.** Confidence: high

ADR 0001's lumped-load argument covers `QH` (HC165 → MCU) and HC-to-HC. It does
**not** cover `SCK`, `SH/LD` and `SER`, which are driven by the **ESP32-S3**
`[repo] carrier.md §3`. `[calc]`:

```
ESP32-S3 pad t_r ≈ 2–5 ns [from memory]  against round trip 2.8 ns
→ t_r ≈ T_pd(round trip). These three ARE transmission lines over 265 mm.
```

So `R-CHAIN-SER` is needed, and it is needed for a reason ADR 0001 does not
give. The page's framing — *"edge-rate damping at the source, which is a
different job and survives that argument"* `[repo] carrier.md` — is right.

**And ADR 0001's reason for deleting the earlier resistors does not survive
arithmetic.** It says series termination is wrong because *"these lines drop on
four boards, where intermediate receivers sit at the incident half-step; at
68 Ω that step can land at 1.96 V against a 2.0 V threshold"* `[repo] 0001`.
`[calc]`, with the 100 Ω now proposed:

```
loaded line impedance:  C0 = T_pd/Z0 = 1.4 ns / 100 Ω = 14 pF
                        loads ≈ 22 pF (4 × HC165 input + 8 connector pins)
                        Z0' = 100/√(1 + 22/14) = 62 Ω
source = 100 Ω + ~30 Ω pad = 130 Ω
incident step at an intermediate receiver = 3.3 × 62/192 = 1.07 V
74HC165 at 3.3 V: V_IL = 0.99 V, V_IH = 2.31 V → 1.07 V is inside the band ✓ the objection is real

HOW LONG: the far-end reflection reaches the nearest cluster (115 mm) after
2 × (265 − 115) mm × 5.3 ns/m = 1.6 ns
```

**The intermediate receivers dwell in the forbidden band for about 1.6 ns,
against a 74HC165 propagation delay of tens of nanoseconds.** An HC gate cannot
respond to a 1.6 ns excursion; the part is its own low-pass filter. **The
objection is arithmetically real and practically nil**, and ADR 0001 deleted a
correct fix on it.

**Endorse `R-CHAIN-SER` at 100 Ω. Do not go above ~150 Ω** — the incident step
falls with `R_s` and the dwell lengthens, and there is no benefit past the point
where the edge is slower than the round trip.

### D10 — the key chain has no idle-state pulls. **Medium, unretrofittable.** Confidence: high

§5 gets this exactly right for the LED lines and then says the quiet part out
loud: *"The module page has the same idea for the same reason: `R-SPI-PULL`, six
of them… **The instrument end has none.**"* `[repo] carrier.md §5`. It then adds
two resistors for `IO1`/`IO2` and stops.

**The same hole exists on the chain, and it is worse there.** `[repo] carrier.md §3`:

| Line | Pin | State through the bootloader window | Far end |
|---|---|---|---|
| `SCK` | `IO38` | high-Z input, 100–300 ms `[from memory]` | 4 × 74HC165 `CP`, 265 mm away |
| `SH/LD` | `IO7` | high-Z input | 4 × 74HC165 `SH/LD`, asynchronous and **level-sensitive** |
| `SER` | `IO33` | high-Z input | far device's serial input |

A floating CMOS input has no defined state — which is ADR 0001's own stated
reason for fitting `R-KEY-PU` at all `[repo] 0001` — and these three run 265 mm
through a channel shared with WS2815 data, into four devices each of which
crowbars while its input sits near threshold. ADR 0001 also records that a
glitch on `SH/LD` *"reloads all four registers mid-shift and corrupts the whole
32-bit word"* `[repo] 0001`.

`[calc]` the fix is three 0805s on the carrier, at the driving end:

```
SH/LD  10 kΩ to 3V3   (high = shift mode; the benign state, and the one that
                       cannot reload a register)
SCK    10 kΩ to GND   (idle low; SPI mode 0)
SER    10 kΩ to GND
load on the ESP pad when driving against the pull: 3.3 V / 10 kΩ = 330 µA — nil
```

Note these must be on the **carrier**, not the cluster boards, because the
window they cover is the one in which the carrier's MCU is not driving. The
cluster boards' 3V3 arrives down the same loom, so a cluster-side pull is
powered at the same time and would work too — but the carrier is where the
driver is and where the convention already lives.

**Unretrofittable once the body is bonded.** Same argument as `R-LED-PD`, same
cost, and the page made it in §5 without carrying it to §3.

### D21 — `F-CHAIN` margin. **Low.** Confidence: medium

The 100 mA polyfuse proposed in §3 `[repo]`. `[calc]`:

```
nominal load: 18 keys closed × 1.43 mA = 25.8 mA [repo] 0001
hold-current margin at 25 °C: 100 / 25.8 = 3.9×
polyfuse hold current derates roughly 50 % at 60–70 °C [from memory];
the cavity runs 10–20 K above ambient [repo] 0014 → effective hold ~50–60 mA
margin in the body: ~2×  — thin but adequate

series resistance of a 100 mA polyfuse: R_i ≈ 2–5 Ω [from memory]
drop at 18 keys held: 25.8 mA × 2–5 Ω = 52–130 mV, and it MOVES with key count
against 74HC165 V_IH = 2.31 V at 3.3 V: 130 mV is 5.6 % of the 0.99 V margin
```

Harmless, but two things follow. **(1)** Size it at 150 mA rather than 100 mA if
the part is available — the fault it covers is a hard short, not a 30 % overload.
**(2)** Put it downstream of the MCP3202's `VDD` tap, not upstream, so the ADC's
reference does not also see the fuse's key-dependent drop on top of the LDO's
load regulation that §2 already costs at 3.2 LSB `[repo] carrier.md §2`.

Keep the part. The failure it covers — *"the instrument is dead and there is no
way to look inside"* `[repo]` — is exactly right for a bonded body.

---

## Part 5 — LED data, `U-LVLSHIFT` / `R-LED-PD` / `R-LED-SER` / `J-LED-*`

### D8 — WS2815 `V_IH`: the datasheet does not support 5 V. **High.** Confidence: medium

ADR 0014 flags this as the one thing to check before committing `[repo] 0014`,
and it is still open. Every WS2815 datasheet mirror I tried was refused by the
proxy (`ledyilighting.com`, `led-stuebchen.de`, `normandled.com`,
`superlightingled.com`, `advateklighting.com`, `industrialmonitordirect.com`).
What two independent search summaries agree the datasheet *says* `[web]`
(`https://www.ledyilighting.com/wp-content/uploads/2025/02/WS2815-datasheet.pdf`,
`https://www.normandled.com/upload/201808/WS2815%20LED%20Datasheet.pdf`):

```
V_IH = 0.7 × VDD ; V_IL = 0.3 × VDD, for the DIN and SET pins
VDD in the same table is the 12 V supply
→ taken literally: V_IH = 8.4 V, V_IL = 3.6 V
```

**A 74AHCT125 on a 5 V rail delivers ~4.6–5.0 V. That is below the literal
`V_IH` of 8.4 V and above the literal `V_IL` of 3.6 V — i.e. in the forbidden
band, by the datasheet's own numbers.**

What the same summaries say about practice: the part carries an internal
regulator dropping 12 V to a ~5 V logic rail, the `0.7 × VDD` row is understood
to refer to that internal rail (→ `V_IH` ≈ 3.5 V), and 5 V logic is what the
entire ecosystem ships. That is almost certainly true. **It is also exactly the
kind of "most 12 V addressable strips accept 5 V logic, but 'most' is not a
basis for a sealed build" that ADR 0014 refused to accept** `[repo] 0014`, and I
agree with ADR 0014.

**Recommendation.** This is not resolvable from a desk and it should stop being
treated as a documentation task.

1. **Measure it on the actual reel, at M6, before the body bonds.** One AHCT125,
   one 12 V supply, one strip, a scope on `DIN` and a thermometer. Sweep the
   drive voltage down from 5 V and find where it fails; the margin to 5 V is the
   answer. Do it on the reel you will install, not a sample — this parameter
   varies with the die revision the strip vendor happened to buy.
2. **Reserve the fallback on the PCB now.** If 5 V turns out marginal the answer
   is a 12 V open-drain driver or a 74HCT-class part on 12 V — neither of which
   drops into a SOIC-14 AHCT125 footprint. Two unpopulated pads per strip for a
   pull-up to 12 V and a small N-FET is a few square millimetres and it is the
   difference between a firmware-era problem and a rebuild.
3. The AHCT125's `V_OH` matters here. `[calc]` at 5.0 V and the −8 mA it will be
   sourcing, `V_OH ≈ 4.2–4.4 V` `[from memory]`; the R-78E5.0 output is nominal
   5 V but the strips' own `V_IH` moves with **their** 12 V rail if the internal
   regulator tracks it. **If the umbilical +12 V sags under LED load, the strip's
   threshold may rise while the buffer's drive does not.** Measure at the low
   end of the 12 V range (ADR 0004 puts ~11.5 V at the instrument `[repo] 0004`),
   not at 12.0 V.

### D18 — `BI`, gate count and the LED loom width. **Low.** Confidence: medium

Two sources disagree and I could not open the datasheet:

- `[web]` (search summary, `https://www.superlightingled.com/PDF/WS2815-12v-addressable-led-chip-specification-.pdf`)
  — *"For the first pixel on the strand you should ground the backup input… to
  force it as 'not valid' pixel data."*
- `[web]` (same summary set) — WS2815 strips ship with four wires at the input,
  `12 V / GND / DIN / BIN`, and the redundancy works by each LED's `BIN` taking
  the output of the LED two positions upstream, which leaves the head with
  nothing to take.

`bom.csv` has already decided: `R-LED-SER` qty **4**, *"FOUR not two: the
WS2815's BACKUP data line is cited as a reason for the part choice… and was
connected to nothing — the level shifter's two spare gates are exactly what it
needs"* `[repo] bom.csv`.

**Driving `BI` with the same data as `DI` is the safe reading** — it is what the
head LED would see if a predecessor existed, and it cannot be wrong. Grounding
`BI` is only safe if the IC treats a static low as invalid rather than as data;
that is an assumption about undocumented silicon behaviour in a sealed body.
**Drive it.** Three consequences the page and BOM have not reconciled:

```
[calc] gate count: 2 strips × (DI + BI) = 4 gates of a 74AHCT125's 4 → ZERO SPARE
[calc] LED loom:   2 strips × (12 V + GND + DI + BI) = 8 conductors, not "6–8"
```

- `bom.csv` `U-LVLSHIFT` still says *"Two spare gates"* `[repo]` — **stale**, and
  it contradicts `R-LED-SER`'s own note in the same file.
- The carrier's component table repeats it as *"Gate count depends on `BI`"*
  `[repo] carrier.md` — it does not depend on anything any more; the BOM decided.
- The loom conductor table's *"WS2815: 12 V, GND, `DI` per strip (+`BI` if
  needed) | 6–8"* `[repo] carrier.md` settles at **8**, so the ~28–30 total
  becomes ~30.
- **Nothing here changes if `OE` is later driven from a GPIO** (see D26) — `OE`
  is an input pin, not a gate.

### D26 — `R-LED-PD` is correct and necessary, and the AHCT125 is safe. Confirmed. Confidence: high

The reasoning in §5 is sound and I want to say so explicitly, because this is
one of the two genuinely unretrofittable items on the page. `[calc]` the
arithmetic that makes it work:

```
74AHCT125 input current: ±1 µA max [from memory]
across R-LED-PD 10 kΩ: 10 µA × 10 kΩ = 10 mV worst case
against V_IL(max) = 0.8 V → 80× margin. 10 kΩ is right; 100 kΩ would also work
and 1 kΩ would waste 3.3 mA when driven high
```

Two things I can add that strengthen it:

**The reverse direction is safe too, which was not obvious.** `[web]` TI's own
E2E support forum on the SN74AHCT125
(`https://e2e.ti.com/support/logic-group/logic/f/logic-forum/715101/sn74ahct125-q1-input-pin`):
*"For this device there is no clamp diode between the input and VCC."* And the
part carries `Ioff`: *"The Ioff circuitry disables the outputs, preventing
damaging current backflow through the devices when they are powered down."*
So a powered ESP32 driving 3.3 V into an unpowered AHCT125 — which happens on
every USB-only bench session if the buffer sits on the load side of `D-USBOR` —
**does not back-power the 5 V rail and does not stress the input.** Good.

**One caveat, from the same datasheet family.** `[web]` search summary of
`https://www.ti.com/lit/ds/symlink/sn74ahct125.pdf`: *"To ensure the
high-impedance state during power up or power down, `OE` should be tied to VCC
through a pullup resistor."* The page ties `OE ×4` **low** `[repo] carrier.md §5`.

That is contrary to TI's recommendation, but **the outcome is the same here and
I would leave it alone**, because `R-LED-PD` holds the *input* at 0 V through
every window that matters, so an enabled buffer can only drive 0 V. The
alternative — `OE` from `IO4` with a 10 kΩ pull-up to 5 V, so the outputs are
Hi-Z until firmware enables them — is tempting and is *worse*: it leaves the
strips' `DIN` floating instead of low, which is precisely the state `R-LED-PD`
was bought to prevent, and it would need a second set of pull-downs on the strip
side of the buffer. **Keep `OE` low, keep `R-LED-PD`, and spend `IO4` on D5
instead.**

### D20 — `R-LED-SER` has three values. **Low.** Confidence: high

`bom.csv` says **330 Ω** `[repo]`; §5's drawing says **220R**; §5's text and the
component table say **100–330 Ω** `[repo] carrier.md`. `[calc]` any of them
works:

```
AHCT125 output impedance ≈ 5 V / 8 mA with ~0.7 V drop → Z_out ≈ 75 Ω [from memory]
420 mm of loose wire: Z0 ≈ 120 Ω, T_pd = 2.1 ns one way, 4.2 ns round trip
WS2815 V_IH (internal-rail reading) ≈ 0.7 × 5 = 3.5 V

R = 330 Ω → R_s = 405 Ω, ρ_s = 0.543
  incident 5 × 120/525 = 1.14 V → far end 2.29 V at 2.1 ns
                                → 3.53 V at 6.3 ns   ← crosses 3.5 V here
R = 220 Ω → R_s = 295 Ω, ρ_s = 0.42
  incident 1.45 V → 2.89 V at 2.1 ns → 4.01 V at 6.3 ns

WS2815 bit period = 1.25 µs. A 6.3 ns settling edge is 0.5 % of a bit. Both fine.
```

**Settle on the BOM's 330 Ω** and change the drawing, not the BOM. Two reasons
beyond consistency: it is the more standard value at an addressable-LED driver,
and `[calc]` it halves the injection into an unpowered strip —
`(5 − 0.7)/330 = 13 mA` against `(5 − 0.7)/220 = 19.5 mA` — which matters for D25
below.

### D25b — the USB-only bench case, and the 5 V node's ambiguity. **Low.** Confidence: medium

§1 draws the 5 V node as:

```
[R-78E5.0 A] ──▷|── ┬── dev board 5V
             D-USBOR├── 74AHCT125
                    └── (8×8 matrix, via the board)
```

**It is not clear whether the 74AHCT125 is on the regulator side or the dev-board
side of `D-USBOR`.** It matters:

- **Regulator side:** the buffer is dead on USB power. Bench LED bring-up is
  impossible. Safe.
- **Dev-board side:** USB VBUS powers the buffer, so on a USB-only session the
  buffer drives 5 V data into WS2815 `DIN` pins whose 12 V rail is absent
  (the strips are fed straight from `J-UMB` pin 3 `[repo] carrier.md §1`).
  `[calc]` injection per line through the strip's ESD clamp:
  `(5 − 0.7)/330 Ω = 13 mA`, against a typical 10–20 mA continuous clamp rating
  `[from memory]` — marginal, ×4 lines.

**And the firmware cannot tell the difference**, because the presence detect was
deleted at the module and never added at the instrument. D5 fixes that. In the
meantime: **draw the node unambiguously, and put the buffer on the regulator
side** — then the failure mode is "the LEDs do not light on the bench", which is
a comment in a bring-up script rather than a slow degradation of four LEDs in a
bonded body.

### D12 — the matrix can overload the 5 V regulator, and blank-at-boot cannot save it. **Medium.** Confidence: medium

ADR 0014 documents the strips' latch-up loop in detail and declares it broken by
the module's current-limited load switch `[repo] 0014`. **That device is on the
+12 V umbilical at the module. The matrix hangs on the instrument's own 5 V
regulator, which is downstream of it, and the load switch cannot protect it.**

`[calc]` from ADR 0014's own figures `[repo] 0014`:

```
matrix full-field white:   64 LEDs × 15 mA = 960 mA at 5 V
both dev boards:                            330–400 mA
                                          ────────────
                                           1 290–1 360 mA
R-78E5.0-1.0 rating                        1 000 mA
                                          → 129 – 136 %
```

ADR 0014 states the 1.36 A figure itself. What it does not do is close the loop:

> "Blank both strips *and the matrix* as the first act at boot… The matrix is on
> the MCU that resets, so it latches too." `[repo] 0014`

**Blank-at-boot cannot run if the board cannot boot.** The sequence is: warm
reset with the matrix latched bright → 5 V rail still up → matrix still drawing
960 mA → regulator current-limits or hiccups → the dev board's 3V3 LDO loses
headroom → brownout → reset → the matrix, being a chain of latching WS2812C
parts on a rail that never fell, holds its state → repeat. `[calc]`:

```
R-78E5.0 output at current limit, say 4.2 V [from memory]
dev board LDO (AMS1117-class, ~1.1 V dropout [from memory]) → 3V3 sags to ~3.1 V
ESP32-S3 brownout detector default trips near 2.9 V [from memory]
→ the margin between "limps" and "resets" is a few hundred millivolts, which is
  exactly the regime ADR 0014 describes for the polyfuse: "the MCU misbehaves at
  reduced voltage before it resets"
```

Cold start is safe — WS281x parts power up dark `[from memory]`. The dangerous
case is the **warm** reset, which is the common one.

**So ADR 0014's own conclusion is wrong for the matrix.** It says *"The firmware
clamp is a comfort feature against the electrical failure, and a real one against
the thermal failure"* `[repo] 0014`. For the strips, with a load switch upstream
of them, that is true. **For the matrix the clamp is the *only* electrical
defence**, because nothing between the regulator and the LEDs limits current and
the recovery mechanism is downstream of the thing that fails.

**Recommendations, all free:**

1. **Make the clamp a hard cap on the *commanded* state, enforced before every
   write, with no configuration path around it.** ADR 0014 already says this for
   thermal reasons `[repo] 0014`; the electrical justification makes it
   non-negotiable. A commanded state that never exceeds ~3 W total can never be
   the latched state, so the loop cannot start.
2. **Add the cap as a compile-time constant checked in the driver**, not as a
   runtime setting, and cap the *sum* of the three outputs — a per-output cap
   cannot see that all three are drawing.
3. **Check the R-78E5.0's overload behaviour at E1.** If it is hiccup-mode with
   auto-recovery the loop is self-limiting and this is a nuisance; if it is
   foldback it is a lock-up. That is a datasheet line nobody has read
   (`recom-power.com` was not reachable from here).
4. Note the derating question the page already raises stands `[repo] carrier.md §1`:
   68–78 % of a 1 A part inside a body running 10–20 K above ambient wants the
   curve, not an assumption.

### D19 — no bulk capacitance at the 5 V node. **Low.** Confidence: high

`C-DECOUPLE-CARRIER` qty 7 covers *"MCP3202, REF5050 in, OPA2197 +12V,
74AHCT125, MPXV4006DP, and both R-78E5 inputs"* `[repo] bom.csv`. `C-BUCK-IN` is
on the regulator **inputs** `[repo]`. **Nothing is on the 5 V output.**

ADR 0004's own rule is *"bulk belongs at the load, not at the entry"*, and
ADR 0014 applies it to the strips with `C-STRIP-BULK` 470–1000 µF ×2
`[repo] 0004, 0014`. **The matrix is the largest current step on the 5 V rail
and got nothing** — despite ADR 0014 explicitly covering both light sources
under one decision *"because the easiest way to get those wrong is to design
them separately"* `[repo] 0014`.

`[calc]`, using the same model ADR 0014 used for the strips:

```
matrix at the 3 W clamp, say 1.5 W at 5 V = 300 mA, PWM'd at ~2 kHz [repo] bom.csv
square-wave sag with no bulk: ΔV = I × (T/2)/C = 0.3 A × 250 µs / C
  for 200 mV ripple:  C = 375 µF
  for  50 mV ripple:  C = 1 500 µF
the R-78E5.0's control loop is far below 2 kHz [from memory], so it does not help
```

How much does 200 mV on 5 V actually cost? `[calc]` it reaches the MCP3202's
reference only through the dev board's 3V3 LDO:

```
LDO PSRR at 2 kHz ≈ 60 dB [from memory] → 0.2 V → 0.2 mV on the 3.3 V reference
0.2 mV / 3.3 V = 0.006 % = 0.25 LSB of 4096
```

**So the ADC consequence is small** — smaller than the 3.2 LSB the page already
accepts from the key pull-ups `[repo] carrier.md §2`, and I would not justify
`C-ADC-BULK` on it. But 100–470 µF plus a 100 nF at the socket's 5 V pin, on the
**load side of `D-USBOR`**, is two parts and it is the right place for them by
the project's own stated rule. Put them there and `C-ADC-BULK` becomes optional
rather than load-bearing.

---

## Part 6 — the display loom, `J-DISP`

### D11 — the freed conductors should have become grounds, not disappeared. **Medium, free, unretrofittable.** Confidence: high

§6 withdrew `EN` and `IO0` and shrank `J-DISP` from 11-way to 9-way `[repo]`,
with this justification:

> "What runs in it now is a UART pair and a console pair — all four framed,
> byte-oriented and recoverable by retry, which is exactly what `EN` and `IO0`
> were not." `[repo] carrier.md §6`

**Two of those four are not framed.** `U0TXD`/`U0RXD` is the boot console. It
carries ROM bootloader output, second-stage bootloader output and panic dumps —
none of which has a checksum, a retry or a reader that can ask again. It is the
third rung of the recovery ladder `[repo] bom.csv`, used precisely when
something is wrong, and a corrupted panic backtrace is a wasted debugging
session on a board that cannot be opened.

**And the environment is the one the project already decided is hostile.**
ADR 0001 made *"a ground return per signal"* the highest-value SI item in the
project and spent four extra conductors on `J-CHAIN` for it `[repo] 0001`.
`J-DISP` runs 360 mm — **136 % of the key chain's 265 mm** — through *"a side
channel with an 800 kHz data line and 12 V LED power"* `[repo] carrier.md §6`,
with **two grounds for four signals**.

`[calc]` ADR 0001's own corrected coupling figure, applied here:

```
ADR 0001: an unfiltered wire next to WS2815 data sees 1.36 V of swing [repo] 0001
ESP32-S3 V_IL(max) = 0.25 × 3.3 = 0.83 V ; V_IH(min) = 0.75 × 3.3 = 2.48 V [fm]
a 1.36 V excursion on a line idling high at 3.3 V lands at 1.94 V
                                                  → inside the forbidden band
UART1 bit time at 921 600 baud = 1.085 µs ; WS2815 data edges are ~10–20 ns
→ a coupled glitch is ~1–2 % of a bit: it will corrupt a bit, not a whole frame
```

ADR 0013's framed protocol with checksums absorbs that on UART1 `[repo] 0013`.
**Nothing absorbs it on the console pair.**

**Recommendation — go back to 11-way and spend the freed conductors on grounds:**

```
1  5 V (or +12 V — see Still open)
2  GND
3  IO5 → display RX      ┐
4  GND                   │ UART1, framed
5  IO6 ← display TX      ┘
6  GND
7  U0TXD                 ┐
8  GND                   │ console, unframed — this is the one that needs it
9  U0RXD                 ┘
10 spare
11 spare  (ADR 0009's rule, preserved)
```

Every signal has a ground on at least one side and the two unframed ones have a
ground between them. **This costs two conductors in a loom that had them
yesterday, it costs nothing at either connector, and it cannot be added after the
body bonds.** The page's own §3 argues this case at length for `J-CHAIN` and
then, in §6, treats the same conductors as savings.

*(The withdrawal of the `EN`/`IO0` RC networks is correct and should stand — the
networks existed for the lines, and the lines are gone.)*

---

## Part 7 — presence, recovery, and the things that cannot be fixed later

### D5 — a presence detect is available for two resistors and a pin that is already spare. **High, free, unretrofittable.** Confidence: high

Both versions of the module's presence detect were deleted, for good reasons
`[repo] 0004, digital-and-supervision.md`:

| Version | Why it failed |
|---|---|
| Gate `OE` from "+12 V on the umbilical" | The tap was **downstream of the module's own load switch**, so it read *present* with nothing attached |
| Watch the breath line through an LM311 | Threshold inside the breath signal's own range; locked out every standalone module milestone; failed toward "present" |

And `digital-and-supervision.md` concludes: *"**The knowing moved to the
instrument**, which digitises breath anyway and has a display to report on."*
`[repo]` **But nothing was actually added at the instrument.** The knowing moved
to a board that has no way to know.

**It has one, for two 0805s and a pin ADR 0007 already set aside.** ADR 0007
says *"GPIO 3 and 4 are ADC1 channels, so either can become an analog input if
something later wants one"* `[repo] 0007`. Something does.

```
J-UMB pin 3 (+12 V) ──[R-PRESENCE-U 100 k]──┬──── IO4  (ADC1_CH3)
                                             │
                                  [R-PRESENCE-L 33 k]
                                             │
                                          PWR_GND
```

`[calc]`:

```
ratio          = 33 k / (100 k + 33 k) = 0.2481
at +12.0 V     → 2.98 V   against ESP32-S3 ADC1 full scale ~3.1 V at 12 dB atten [fm]
at +11.5 V     → 2.85 V   (ADR 0004's figure at the instrument after cable drop)
at  +6.0 V     → 1.49 V   (a clear "sagging, not absent" reading)
at   0.0 V     → 0.00 V
divider current = 12 V / 133 kΩ = 90 µA — nothing against a 928 mA budget
clamp safety while the 5 V rail is up and 3V3 is not, the same hazard §2 costs
for R-ADCDIV:  (12 − 0.7) / 100 kΩ = 113 µA, against a family-typical ±2 mA [fm]
```

**Why this version works where the module's did not.** At the *instrument* end,
+12 V is downstream of the cable **and** downstream of the module's load switch
**and** downstream of the panel toggle. It reads exactly what nobody could read
before: *the link is connected and the far end is delivering power.* The
module's version failed because it sampled upstream of the cable, on its own
board — the one place where the answer is always "yes".

**What it buys, none of which exists today:**

- The matrix can show an alarm when the umbilical is out — ADR 0014 reserves
  exactly this behaviour and says alarms *"are not assignable away"* `[repo] 0014`.
- Firmware can stop driving the DAC into a dead cable, which is the difference
  between "no output" and "no output plus a puzzle".
- It disambiguates the USB-only bench state (D25b), which is currently
  indistinguishable from normal operation to the firmware.
- A sagging rail becomes visible *before* it becomes a brownout, which is the
  early-warning D12's latch loop does not otherwise have.

**What it does not buy:** it does not stop the rack droning when the cable is
pulled. There is no return path and there cannot be one — the umbilical is
write-only by decision `[repo] 0004`. The module's own answer to that is the
`CLR`-from-presence idea in `digital-and-supervision.md` `[repo]`, which is a
separate decision at the other end.

**Two resistors, one already-spare pin, and it cannot be added after the body
bonds.** Take it at E13. Use `IO4`, not `IO3` — `IO3` is a strapping pin (D23)
and there is no reason to put a permanent divider on one.

### D6 — the recovery ladder's second rung is deleted by a setting stored on the board being recovered. **High.** Confidence: high

`firmware/README.md` and `bom.csv` give the ladder: *"(1) OTA rollback. (2)
USB-Serial-JTAG through the tail USB-C slot — which is why MIDI is opt-in. (3)
The console header… A corrupted *bootloader* therefore ends the instrument"*
`[repo]`. The reasoning behind (2) is correct and well-found:

> "On the ESP32-S3 the internal PHY routes to USB-Serial-JTAG *or* USB-OTG,
> never both. The moment the application claims OTG the `DTR`/`RTS`
> download-mode path is gone." `[repo] firmware/README.md`

**ESP-IDF's own documentation states the consequence and the remedy, and the
remedy is not available in this instrument.** `[web]`
`https://raw.githubusercontent.com/espressif/esp-idf/master/docs/en/api-guides/usb-serial-jtag-console.rst`
line 79:

> "If the application accidentally reconfigures the USB peripheral pins or
> disables the USB Serial/JTAG Controller, the device disappears from the
> system. After fixing the issue in the application, you need to **manually put
> the ESP32-S3 into download mode by pulling low GPIO0 and resetting the
> chip**."

`GPIO0` is the BOOT button `[board-def]` and is not on the header `[board-def]`.
`EN` is on the reset circuit and is not on the header `[repo] bom.csv`. **So the
documented remedy for losing rung 2 is the thing the design explicitly cannot
do.**

**One good piece of news, which I want to record because it is load-bearing and
I have not seen it stated.** `[web]` esptool's ESP32-S3 target
(`https://raw.githubusercontent.com/espressif/esptool/master/esptool/targets/esp32s3.py`)
carries `RTC_CNTL_FORCE_DOWNLOAD_BOOT_MASK` and the comment
*"Is download mode forced over USB?"*, and clears it *"to avoid chip being stuck
in download mode"*. **While USB-Serial-JTAG is alive, esptool forces download
mode over USB without touching `GPIO0` at all.** Rung 2 genuinely does not need
a BOOT button — *as long as the controller is alive*. The hole is precisely the
case the ESP-IDF doc names: the controller having been switched off.

**So the exposure is narrower than "no hardware boot-force" suggests, and
sharper.** It is one specific state: *USB MIDI enabled*. And that state is
reached by a documented, advertised, user-facing feature, and it is **persisted
in NVS on the very board that needs recovering** `[repo] firmware/README.md`
("It holds the config, the calibration and the NVS").

**Recommendations:**

1. **Make USB MIDI enablement non-persistent.** Enabling it is a gesture or a
   config-mode action each session, never a saved setting. Then every power
   cycle restores rung 2 unconditionally, and the worst case is "unplug it and
   plug it back in". ADR 0012 already establishes a config-mode entry via a
   spare shift-register input or a gesture `[repo] 0012`; reuse it.
2. If it must persist, **persist it with a boot counter**: clear the flag after
   N consecutive boots that do not reach "application validated". This is the
   same shape as `CONFIG_BOOTLOADER_APP_ROLLBACK_ENABLE`, which the design
   already uses `[repo] firmware/README.md`, and it costs a few lines.
3. **Exercise this specific case at M8**, not the ladder in general: enable MIDI,
   flash a deliberately broken image, and recover it. `firmware/README.md` says
   *"Exercise the ladder at M8, before the body closes"* `[repo]` — make this the
   named test.

### D7 — `BOOT` and `RESET` can be reached through a cover that already exists. **High, free.** Confidence: medium

The strongest recovery fix available is not electrical and nobody has proposed
it.

- `MECH-SERVICECOVER` is *"a screwed cover plate ~12 × 40 mm + 2 × M2… over
  `HDR-SERVICE` on the tail underside… Same laminated layer as the matrix
  window, beside it"* `[repo] bom.csv`.
- §7 proposes mounting the dev board on the carrier's **underside, LED face
  outward** `[repo] carrier.md §7` — i.e. facing the same tail underside the
  cover and the matrix window are on.
- The ESP32-S3-Matrix carries both a BOOT button (`GPIO0`, confirmed
  `[board-def]` Zephyr `gpio-keys`) and a reset button `[repo] bom.csv`, which
  are *"soldered to the dev board"* and therefore inside the body — **but they
  are on the board, not buried in the PCB stack.**

**If the buttons land on a face that the service cover or a 3 mm aperture can
see, a toothpick recovers the instrument from every firmware failure short of a
corrupted bootloader — including the one in D6.**

This converts `bom.csv`'s *"A corrupted BOOTLAODER ends the instrument; that is
accepted"* `[repo]` from an accepted loss into a much narrower one, and it
converts D6 from High to Low.

**What it costs:** a line in the M4 CAD, which is already drawing the matrix
window, the service cover, the etherCON backing plate and the USB-C slot on that
same face `[repo] 0013, 0009`. **What it needs:** the same confirmation §7
already gates on — *"which face carries the matrix relative to the header rows"*
`[repo] carrier.md §7`, plus "and where are the two buttons". **One extra line
in a measurement that is already scheduled.**

**Do this.** If the geometry does not permit it, that is worth knowing at M4
rather than discovering that it would have been free.

### D17 — an NVS commit stops the 4 kHz loop. **Medium.** Confidence: medium

`digital-and-supervision.md` raises this at the module end and gets the mechanism
right: *"An ESP32-S3 NVS commit or OTA write disables the instruction cache and
can stall non-IRAM code on both cores"* `[repo]`. **It applies to the carrier
harder**, because the carrier is where the loop runs and where the NVS lives
`[repo] 0013`.

`[calc]`:

```
a 4 kB flash sector erase takes tens of milliseconds [from memory]
during it, the instruction cache is disabled on BOTH cores; only IRAM code runs
the 4 kHz loop period is 250 µs
→ tens of ms is ~100–200 missed loop passes; the DAC holds its last value
```

ADR 0012 and ADR 0013 both want *live configuration while playing* —
*"adjusting a routing matrix and hearing the result immediately is a different
instrument to one you stop playing to configure"* `[repo] 0013` — and
`firmware/README.md` requires every config edit to *"validate, apply, persist and
echo back"* `[repo]`. **Persisting is a flash write. It is on the path of every
live config edit.**

**Recommendations:**

1. `CONFIG_SPI_MASTER_IN_IRAM`, `CONFIG_SPI_MASTER_ISR_IN_IRAM`,
   `CONFIG_FREERTOS_IN_IRAM`, and `IRAM_ATTR` on the loop body, the DAC service
   routine and everything they call. The ESP-IDF SPI docs call this out
   specifically: *"The default config puts only the ISR into the IRAM. Other
   SPI-related functions… might suffer from cache misses"* `[web]` `spi_master.rst`.
   **This is the same action item as D2's mitigation 3.**
2. **Separate "apply" from "persist".** Apply the edit to RAM immediately — that
   is what "hearing the result" needs — and defer the NVS commit to a moment
   when no note is sounding, with a short timeout. One flag and one condition.
3. **Measure it at E1**, as `digital-and-supervision.md` already asks: *"Measure
   the real stall before tuning the RC"* `[repo]`. The RC is gone but the
   measurement is still the right one, and it now gates live configuration
   rather than a watchdog.

### D29 — the carrier does not need a watchdog. Note. Confidence: high

For completeness, since the brief names it. The deleted watchdog was the
**module's** frame watchdog, and `digital-and-supervision.md` argues its deletion
well `[repo]`. The **instrument** is not unguarded: the ESP32-S3 carries an RTC
watchdog, an interrupt watchdog and a task watchdog `[from memory]`, and
`[board-def]` Zephyr's devicetree for this exact board exposes `wdt0` and aliases
it as `watchdog0`. A hung real-time board reboots itself, and ADR 0014's
blank-at-boot then clears the strips `[repo] 0014`.

**The residual gap is not on this board.** It is the one
`digital-and-supervision.md` already tabulates: cable unplugged mid-note, or the
instrument losing power mid-note, leaves the DAC holding and the rack droning
`[repo]`. D5 lets the instrument *notice* the first of those. Neither D5 nor
anything else on the carrier can *fix* it, because the link is write-only. That
is the module's decision to revisit, via the `CLR`-from-presence idea its own
page already describes.

---

## What I would do, in order

Everything in group A is unretrofittable once the body bonds, and most of it is
free.

**A — before E13 / the board goes out**

1. **D1** — swap `J-UMB` pins so `CS` pairs with `DIG_GND` and `SCLK` pairs with
   `MOSI`. Pinout decision, zero cost, converts the worst failure into the
   mildest.
2. **D3** — `R-SCLK-SER`/`R-MOSI-SER`/`R-CS-SER` at **100 Ω**, qty 3.
3. **D10** — three 10 kΩ idle pulls on `SH/LD`↑, `SCK`↓, `SER`↓.
4. **D5** — `R-PRESENCE-U` 100 k / `R-PRESENCE-L` 33 k from `J-UMB` pin 3 to `IO4`.
5. **D11** — `J-DISP` back to 11-way, with grounds in the freed positions.
6. **D15** — 10 kΩ from `IO34` to 3V3 on the carrier.
7. **D4** — draw the MCP3202's `CLK`/`DIN`, tapped at the MCU pins ahead of the
   series resistors.
8. **D18/D20** — `U-LVLSHIFT` has zero spare gates; `R-LED-SER` is 330 Ω ×4;
   LED loom is 8 conductors.
9. **D19** — 100–470 µF + 100 nF at `HDR-DEV`'s 5 V pin, load side of `D-USBOR`.
10. **D25b** — draw the 5 V node so the buffer's position relative to `D-USBOR`
    is unambiguous; put it on the regulator side.

**B — at M4, in CAD that is already being drawn**

11. **D7** — check where the dev board's `BOOT` and `RESET` buttons land and
    align `MECH-SERVICECOVER` or a small aperture with them. Highest-value
    recovery fix in the project.

**C — firmware constraints to write into `firmware/README.md` now, before anyone
writes code against the current numbers**

12. **D2** — polling transactions inside `spi_device_acquire_bus()`; key scan on
    core 1; SPI driver and loop in IRAM. Record the 196–241 µs figure, not 122.7.
13. **D9** — the 8×8 matrix is RMT, never a GPSPI host. LED RMT ISRs off the
    real-time core.
14. **D14** — the IMU is never read inline in the 4 kHz loop.
15. **D12** — the lighting clamp is a hard compile-time cap on the summed
    commanded current, with no configuration path around it.
16. **D6** — USB MIDI enablement does not persist across a power cycle.
17. **D17** — apply config edits to RAM immediately; defer the NVS commit to
    silence.

**D — measurements that gate things, to add to `latency-budget.md`'s table**

18. **D8** — WS2815 `V_IH` on the actual reel, at 11.5 V rail, at M6. Reserve a
    12 V-drive fallback footprint until it passes.
19. **D2/D13** — real per-pass loop cost on a logic analyser, and the MCP3202's
    real ceiling at 3.3 V. Both gate the loop rate.
20. **D24** — breath-jack noise with SPI2 running versus idle, looking for a
    4 kHz tone rather than broadband hash.
21. **D12** — the R-78E5.0's overload behaviour (hiccup or foldback) at E1.
22. **D6/D7** — the specific recovery case at M8: MIDI enabled, deliberately
    broken image, recover it.

---

## What I checked and found correct

Recorded so nobody re-derives it.

- **The pin assignment.** All 17 header pins verified against two independent
  board definitions. No conflict, no strapping collision, quad PSRAM confirmed
  from a devicetree. ADR 0007 is buildable as written.
- **`HDR-DEV` is 2 × 10-way**, which validates §7's geometry arithmetic.
- **SPI2 cannot use IO_MUX, and it does not matter at 2 MHz.** Confirmed against
  ESP-IDF's own documentation, including the explicit statement that ≤40 MHz
  through the GPIO matrix behaves identically.
- **ESP-IDF supports per-device clock rates on a shared host.** The page's
  assumption is correct; the omission was the per-transaction overhead, not the
  mechanism.
- **The key chain is a lumped load at 1 MHz**, with 7× margin. ADR 0001's
  central claim survives arithmetic.
- **`R-LED-PD` is correct, necessary and sufficient**, and the AHCT125 has no
  input clamp to VCC, so the reverse-drive case is safe too.
- **Pair skew and cable loss over 2 m of Cat5 are non-terms**, and linear
  `SCLK`→`BREATH` crosstalk is 7.5 µV after the receive filter.
- **The carrier needs no watchdog.** The S3 has three, and the residual gap is
  at the module.
- **`bom.csv`'s `HDR-SERVICE` note is right**: `EN` and `IO0` really are absent,
  confirmed against the board definitions rather than against a product listing.

---

## Sources fetched in this session

- [CircuitPython `waveshare_esp32_s3_matrix/pins.c`](https://raw.githubusercontent.com/adafruit/circuitpython/main/ports/espressif/boards/waveshare_esp32_s3_matrix/pins.c)
- [CircuitPython `waveshare_esp32_s3_matrix/mpconfigboard.h`](https://raw.githubusercontent.com/adafruit/circuitpython/main/ports/espressif/boards/waveshare_esp32_s3_matrix/mpconfigboard.h)
- [Zephyr `esp32s3_matrix_esp32s3_procpu.dts`](https://raw.githubusercontent.com/zephyrproject-rtos/zephyr/main/boards/waveshare/esp32s3_matrix/esp32s3_matrix_esp32s3_procpu.dts)
- [Zephyr `esp32s3_matrix-pinctrl.dtsi`](https://raw.githubusercontent.com/zephyrproject-rtos/zephyr/main/boards/waveshare/esp32s3_matrix/esp32s3_matrix-pinctrl.dtsi)
- [ESP-IDF `spi_master.rst`](https://raw.githubusercontent.com/espressif/esp-idf/master/docs/en/api-reference/peripherals/spi_master.rst)
- [ESP-IDF `usb-serial-jtag-console.rst`](https://raw.githubusercontent.com/espressif/esp-idf/master/docs/en/api-guides/usb-serial-jtag-console.rst)
- [ESP-IDF `configure-builtin-jtag.rst`](https://raw.githubusercontent.com/espressif/esp-idf/master/docs/en/api-guides/jtag-debugging/configure-builtin-jtag.rst)
- [ESP-IDF `components/soc/esp32s3/include/soc/soc_caps.h`](https://raw.githubusercontent.com/espressif/esp-idf/master/components/soc/esp32s3/include/soc/soc_caps.h)
- [esptool `targets/esp32s3.py`](https://raw.githubusercontent.com/espressif/esptool/master/esptool/targets/esp32s3.py)

Search summaries only (PDF blocked by the egress proxy):
[MCP3202 via DigiKey](https://www.digikey.sg/htmldatasheets/production/48341/0/0/1/mcp3202.html) ·
[MCP3202 via Farnell](https://www.farnell.com/datasheets/1669376.pdf) ·
[WS2815 via LEDYi](https://www.ledyilighting.com/wp-content/uploads/2025/02/WS2815-datasheet.pdf) ·
[WS2815 via NormandLED](https://www.normandled.com/upload/201808/WS2815%20LED%20Datasheet.pdf) ·
[WS2815 via SuperLightingLED](https://www.superlightingled.com/PDF/WS2815-12v-addressable-led-chip-specification-.pdf) ·
[SN74AHCT125 input pin, TI E2E](https://e2e.ti.com/support/logic-group/logic/f/logic-forum/715101/sn74ahct125-q1-input-pin) ·
[SN74AHCT125 datasheet](https://www.ti.com/lit/ds/symlink/sn74ahct125.pdf)

Refused by the proxy and therefore **not** read: `ti.com`, `microchip.com`,
`ww1.microchip.com`, `espressif.com`, `docs.espressif.com`, `waveshare.com`,
`farnell.com`, `digikey.*`, `mouser.com`, `alldatasheet.com`, `mikroe.com`,
`nexperia.com`, `diodes.com`, `onsemi.com`, and every WS2815 datasheet mirror.
Anything sourced from those is marked `[from memory]` or `[web]`-via-summary and
**must be checked against the datasheet before ordering.**
