# Firmware

**One image** ([ADR 0015](../docs/decisions/0015-one-mcu-no-display.md)):

- `realtime/` — the ESP32-S3-Matrix. Keys, breath, IMU, DAC loop, the LEDs
  (WS2815B-V1 on the main board, `lighting.led_count`, ADR 0028) and the 8×8 matrix
  (the only display), USB MIDI and USB configuration. Owns all state and
  persistence. This is the instrument.

There is no display board and no radio: WiFi and BLE stay off.

PlatformIO, ESP-IDF underneath. Nothing here yet — Track F follows Track E
(see [ROADMAP.md](../ROADMAP.md)).

## Architecture constraints

These come from [ADR 0001](../docs/decisions/0001-mcu-and-board-partitioning.md)
and [the latency budget](../docs/reference/latency-budget.md), and they are not
negotiable without revisiting those:

- **4 kHz loop** for sensor read and DAC update, pinned to one core.
- **Lighting renders on the other core, through RMT.** A matrix or LED-row
  update must never block the output loop.
- **Asymmetric key debounce** — a note-on needs **two consecutive agreeing
  chain reads** and nothing more (ADR 0001, *Two firmware rules the chain
  depends on*); only the release is filtered. The two-sample gate rejects one
  corrupted frame, not contact bounce, and costs one loop period
  (`latency-budget.md`, *Key path*). A symmetric window puts its full length
  into the attack. The release window is sized against `ks33-contact-bounce`, which is now a
  tracked figure read verbatim off Gateron's own drawing for this exact part
  — so the starting number is published, not guessed, and is deliberately not
  restated here. M1 still measures it, because a vendor maximum at a stated
  actuation speed is not this keyboard's bounce at a player's speed; what M1
  changed is that it now confirms or moves a documented figure instead of
  supplying the only one. Either way, not the conventional 20 ms the 2021
  firmware used.
- **Per-channel smoothing in software**, not in the analog filter. The
  instrument's analog filter (`C-AA-ADC`, the 1.5 kHz setting) is fixed;
  firmware knows what each channel carries. The module's breath band-limit is
  a panel toggle (500 Hz / 1.5 kHz / wide, ADR 0003, *Amendment, 2026-10-04*)
  that firmware neither sees nor sets: it acts on the jack, not on the ADC.
- **Nothing expressive touches the ESP32's internal ADC.** It is noisy and
  nonlinear, and breath drives a 0–10V output where that shows.
- **There is no radio.** WiFi and BLE are never started, so no transmit burst
  can preempt the output loop or land on the rail the breath path shares
  ([ADR 0015](../docs/decisions/0015-one-mcu-no-display.md)).
- **Refresh everything, every pass. Never write-on-change.** The umbilical is
  write-only — `MISO` was deleted from the cable (ADR 0004) — so nothing
  downstream can ever be read back. *With no readback, shared state can only be
  made safe by being made stateless.* This is the rule, not an optimisation
  note; see below for the failure that produced it.

### Why statelessness, specifically

The design review found this by one route and two diagnostics findings arrived
at it from the opposite direction, so it is worth stating the case once.

The mod channels are `Vout = 4·Vdac − 3·V_ref`, with `V_ref` the shared
**3.3333 V** from DAC channel 7 — **refreshed every pass, like the other five** (ADR 0006, corrected 2026-09-21). *(The
value changed with the two-resistor redraw in `mod-channels.md`; writing the
old 2.5 V into channel 7 against the current 10 k/30 k network gives a
−7.5…+12.5 V window — wrong span, and it clips positive.)* When `CLR` is
asserted, every DAC channel including channel 7 goes to zero scale. Firmware
then rewrites the five signal channels, because those are the ones it thinks of
as signals, and `Voffset` stays at 0. Every mod jack pins at `4 × Vdac`
≈ +11.45 V and stays there.

**`CLR` is asserted by two things, and neither of them is optional.** The
DAC's own **power-on reset**, which fires on every rack power-up — so this is
not a fault case, it is the boot path. And the **`LK-CLR` solder pad**
(`bom.csv`), which asserts `CLR` by hand and exists precisely so that E7–E10
can drive the module into this state deliberately. *(This paragraph said "when
the module watchdog asserts `CLR`" until 2026-09-21. The 74HC123 frame watchdog
is deleted — `digital-and-supervision.md` — and the rule below is the most
load-bearing firmware constraint in the repo, so its stated cause had to be one
that still exists. A reader who checks the old premise, finds the watchdog
gone, and relaxes the rule reintroduces +11.45 V on four jacks.)*

With no `MISO` this is undetectable, and it survives until the next power
cycle. The same shape of bug is latent in every other register the DAC holds
that firmware writes once: the internal-reference enable, and the clear-code
register itself.

The fix costs nothing. **The latency budget already books six DAC words per
pass while five are written**, so the sixth channel fits inside a budget that
was already paid — and refreshing the reference-enable and clear-code registers
periodically costs a word every few thousand passes.

**Breath is outside all of this.** It never passes through the DAC, and since
the in-amp's `REF` pin is grounded rather than driven by a firmware zero
(ADR 0003), no DAC register touches the breath jack at all. Firmware's breath
zero is a subtraction applied to its own ADC copy — the representation it can
actually measure — and never leaves the instrument.

## What the hardware requires of firmware

*Added 2026-10-01 (pre-layout review, A5-3). Every line below is a condition
a hardware page relies on and that nothing but firmware can meet. Each names
the page or figure that owns it; the numbers stay there. If a line here and
its owner disagree, the owner wins and this line is the defect.*

### SPI2 — the DAC down the umbilical, and the breath ADC

One host, two devices, two clocks (`interfaces/spi-link`, *The two SPI
hosts*). Pins: `SCLK` IO35, `MOSI` IO36, `CS_MOD` IO34, `MISO` IO37 (the ADC's
`DOUT` only), `CS_ADC` IO39 (`hardware/carrier/netlist.yaml`).

- **DAC8568 (`CS_MOD`): SPI mode 1** (CPOL 0, CPHA 1), **2 MHz**, one 32-bit
  frame per transaction, six frames per pass. The DAC clocks `DIN` on `SCLK`'s
  falling edge `[ds DAC8568CIPW.pdf p.6]`, so the host must launch on the
  rising one; mode 0 would change `DIN` on the edge the DAC samples.
- **`CS_MOD` timing at the pads** — the receiver's RC delays a falling edge
  far more than a rising one, so `CS_MOD` needs margin the DAC's own table
  does not show. `interfaces/spi-link/sim` `frame-timing` holds the DAC's
  t1, t4, t5, t8 and its clock and data times at its pins, at every corner,
  when firmware keeps all three of these:
  - `CS_MOD` falls **no later than** `SCLK`'s first rising edge;
  - `CS_MOD` stays low **at least 250 ns after `SCLK`'s last falling edge**;
  - `CS_MOD` stays high **at least 250 ns** between two frames.

  Released on the last falling edge, `SYNC` rises before that edge reaches
  the DAC and the frame is lost (`frame-timing-cs-released-at-last-edge`).
  In ESP-IDF terms `cs_ena_posttrans` ≥ 1 is one bit, 500 ns at 2 MHz
  `[from memory: spi_device_interface_config_t]`; whatever the setting, **E11
  confirms the three intervals with a logic analyser at the pads and at the
  DAC's pins**, because how the S3 places `CS` against the last edge in
  mode 1 is not in any banked document.
- **MCP3202 (`CS_ADC`): its own clock, 0.9 MHz** (`spi-link.md`, *The MCP3202
  cannot run at 2 MHz*: ESP-IDF sets the clock per device), **mode 0,0 or
  1,1** `[ds MCP3202-CI-SN.pdf p.1]`, a 24-clock (three-byte) transaction
  `[ds p.17, Figure 6-1]`, `CS` low at least 100 ns before the first rising
  clock and high at least 500 ns between conversions `[ds p.3, tSUCS, tCSH]`.
- **One MCP3202 conversion per pass: 4 kHz, not faster** (#32,
  `breath-adc.md`, *The sample rate stays 4 kHz*). The anti-alias pole is at
  1.5 kHz, so the converter does alias; that page bounds what folds and shows
  why a second read per pass does not fit `loop-budget` at its serialised end.
  Do not add reads to the pass to decimate. If E9 finds a 4 kHz tone (the LED
  row's refresh) in the breath reading, the fix is two conversions per pass
  averaged as a pair, and only once the loop's measured pass time shows it
  closes.
- **Polling transactions on an acquired bus.** With interrupt-driven
  transactions the loop does not close at 4 kHz (`loop-budget`, owned by
  `docs/reference/latency-budget.md`).
- **Refresh all six DAC words every pass**, and the DAC's control registers
  periodically (*Why statelessness*, above). `MISO` is not on the umbilical;
  nothing reads the DAC back.

### SPI3 — the key chain

Four SN74HCS165 (`U-KEYS`), one chain of 32 bits (`interfaces/key-chain-loom`).
Pins: `SCK` IO38, `SH/LD` IO7, chain-end `SER` IO33, `QH` IO40.

- **SPI mode 2** (CPOL 1, CPHA 0), **1 MHz**, 32 bits, **receive only**
  (`spi-link.md`, *The two SPI hosts*: the register shows `H` on `QH` from
  the load, so mode 2's first sample lands before the first shift).
- **`SH/LD` is high for the whole transfer and pulsed low between
  transfers.** Low loads the parallel inputs; high shifts. Driven as an
  ordinary active-low `CS` it would hold the chain in load for the whole
  transfer and every read would return 32 copies of one bit. Drive it as a
  **positive-polarity `CS`** on IO7 (low while idle, so the chain loads
  continuously, high for the transaction), or as a GPIO pulse ahead of the
  transaction. `SH/LD` low at least 7 ns, and high at least 21 ns before
  the first `CLK`↑ — the 2 V column over temperature, so conservative at
  3.3 V `[ds SN74HCS165-ti-scls828a.pdf p.6, p.7]`.
- **Check the marker on every read** (ADR 0001; the bits are
  `key-marker-and-bits.md`). A frame that fails it **holds the previous
  frame** and increments a **visible error counter**, shown on the matrix.
  The marker is a framing check: a reload in the middle of a shift is not
  guaranteed to fail it (`key-marker-and-bits.md` §4).
- **Note-on after two consecutive agreeing reads**, release filtered
  (*Architecture constraints*, above).
- **`IO33` is static in play.** It is a shield on the `J-MCU` ribbon
  (`carrier.md`, *The pin map*), so SPI3 is configured with no `MOSI` pin and
  `IO33` stays an input (the chain end is held high by `R-SER-TERM`) or a
  static output.
- **The chain self-test drives `IO33` as a GPIO, changed only while `SCK` is
  idle.** Clocked as SPI3's `MOSI` in mode 2, `IO33` would change on the
  same `CLK`↑ that `left_hand` samples it on, and which wins depends on two
  RC edges (`key-chain-loom.md`, *The chain-end serial input*). Shift a
  constant level through the whole chain and read it back, then the other
  level: those are exact. A walking pattern, if used, accepts a one-bit
  shift as a pass.
- **The chain's hop hold time is a bench item, not a firmware one**:
  `key-chain-loom/sim` `hop-hold-lt-to-rh` and E14. A hold failure shows as
  a framing error, and the marker counter is how it is seen.

### Other pins

- **`IO2` and `IO3` driven low after boot** — shields on the ribbon
  (`carrier.md`, *The pin map*; recovery ladder, below).

### The lights

- **Blank the LED row and the matrix as the first act at boot**, and keep
  the **shared lighting budget** across both, scaling down rather than
  refusing a write (ADR 0014, *The clamp, restated on thermal grounds*; the
  row's current is `led-row-current`).
- **Write the LED row only while its 12 V is present.** On USB power alone
  `INST_POS12` is dead — no breath, no LED supply — but the LED buffer
  (`U-LVLSHIFT`) runs from the Matrix's own 5 V, so a write would drive
  5 V edges into LEDs with no supply (`power-entry-instrument.md`, *On USB
  power alone*). There is no 12 V sense pin; **the breath reading is one**:
  the sensor sits on the 12 V rail, and with it up the ADC reads the
  sensor's zero-pressure offset (`breath-adc.md`, the *rest* line), with it
  down it reads near zero. Gate the row on the reading sitting above about
  half the rest count, and blank it when it falls below.
- **Cap the matrix while a USB host is attached** (owner, 2026-10-03, #18
  E1: "Firmware cap"). With the rack up and USB plugged in, the Matrix's
  `VCC_5V` is fed from both the buck (through `D-USBOR`) and `VBUS` (through
  the Matrix's own `D1`, a B5819WS), and tens of millivolts decide which
  carries it: at the corners all of it comes through `D1`
  (`power-entry-instrument.md`, *Rack and USB together*). So whenever the
  USB-Serial-JTAG (or, with MIDI on, the USB-OTG) peripheral reports a host
  connected, clamp the **matrix's** LEDs to **about 120 mA** of estimated
  current `[calc: the ~283 mA ADR 0014 derives for D1 at a 60 °C interior,
  *Current: sparse is free, full field is not*, less ~160 mA for the
  ESP32-S3 through the ME6217, #18 E1's table]`, scaling down as the shared
  budget does. It applies on top of the shared lighting budget, not instead
  of it; the LED row is fed from `INST_POS12`, not `VCC_5V`, and is not
  touched. Lift it when the host goes away. The per-LED current behind the
  estimate is `matrix-led-current`, still blocked on E1's measurement, so the
  clamp is a setting E1 confirms, not a constant.
- **Thirteen pixels (`lighting.led_count`), one row, tail end first.** The
  data line reaches the row's tail end first (ADR 0028, amendments of
  2026-10-03: one row at one pitch, its tail-end LED then removed), so a frame
  is pixel 0 for the tail-end LED, then pixels 1–12 toward the mouth end.
  Anything drawn *along* the body (the breath bar, a sweep) addresses pixels
  0–12 in order;
  every pixel is a step of it. Every pixel takes the same gain: no LED stands
  nearer its acrylic than the rest.

## The instrument must stay recoverable

The body comes apart by cutting its silicone (ADR 0025), and answering a
failed flash that way means cutting the oak top free, unscrewing the key plate
from the cassette's columns, unplugging the Matrix's ribbon and the key
boards' ribbons from the main board (ADR 0017), and bonding it all back with
fresh silicone. Everything here exists so that it never has to be the answer.

- **Two app partitions, with `CONFIG_BOOTLOADER_APP_ROLLBACK_ENABLE`.** There
  is no OTA — no radio — but an image flashed over USB into the inactive slot
  that does not mark itself valid is still rolled back by the bootloader on the
  next boot. It turns the most likely bricking event into a reboot.
- **USB MIDI is opt-in, not the default.** On the ESP32-S3 the internal PHY
  routes to USB-Serial-JTAG *or* USB-OTG, never both. The moment the
  application claims OTG the `DTR`/`RTS` download-mode path is gone. Leaving
  MIDI off until the player enables it keeps the serial-JTAG reset path alive
  through every boot that has not been asked for MIDI.
- **The recovery ladder, in order.** (1) Rollback to the other app slot. (2) USB-Serial-JTAG
  through the tail USB-C slot — which is why MIDI is opt-in. (3) The console
  header on the main board, with the body opened (ADR 0025 — there is no
  service cover since 2026-09-26), for watching a board that boots
  but misbehaves. (4) **The Matrix's own BOOT and RESET buttons.** Since 2026-10-03 the
  Matrix is **programmed and recovered over USB-C only** (owner: "Program
  over USB only"; ADR 0021, *Amendment, 2026-10-03*): `EN` and `IO0` are not
  wired out, and `HDR-SERVICE` carries the console's TXD, RXD and GND only
  (`hardware/carrier/service-uart/`). Hold BOOT, press RESET, and the ROM's
  download mode takes a flash over USB-Serial-JTAG through the tail USB-C -
  so a corrupted *bootloader* is recovered without a UART. The buttons are
  on the Matrix's underside, over its carrier; how they are reached with the
  lid lifted is open (ADR 0021, *Amendment, 2026-10-03*, *Open*). The two spare GPIO on the ribbon (`IO2`, `IO3`) sit beside fast
  lines as shields; drive them low after boot (`IO3` is a strapping pin
  [from memory], harmless once booted) — pin map in `hardware/carrier/carrier.md`.
- **Exercise the ladder at M8**, before the body closes, so it is known good
  rather than assumed.

## The lights are instrument-side, and so is everything about them

**The LED row and the matrix read the MCU's own digitised breath value.** Not
the jack, not anything that has been through the module's panel knobs — there
is no return path for that and no reason to want one. The lights show what the
player is doing; the knobs scale what the rack receives. See ADR 0014.

Three numbers, all firmware, none of them constants in the source:

- **Zero** — the power-on ADC capture, shared with the note-gating zero.
- **Deadband** — zero plus a measured noise margin. Without it the bottom LED
  flickers with nobody blowing, which looks like a fault and is arithmetic.
  Size it from E2's measured standard deviation; the auto-zero's "quiet" gate
  needs the same figure.
- **Span** — where full brightness lands. A setting, because the sensor's range
  is about twice what real playing produces, so a fixed mapping wastes the top
  of the display.

## Data, not code

Two things are explicitly configuration rather than compiled constants
([ADR 0010](../docs/decisions/0010-key-layout-as-data.md),
[ADR 0006](../docs/decisions/0006-cv-channel-allocation.md)):

- **Fingering table** — a custom fingering system takes a lot of playing to get
  right, and a recompile per experiment is the wrong loop. It covers the 15
  `note` keys only; the four right-thumb switches are `control` and must never
  enter it (ADR 0010).
- **Routing matrix** — four mod channels, each with source, scale, offset, curve
  and slew.

Both live in NVS and are edited over USB.

## Bring-up fixtures

Throwaway test firmware for E-track milestones belongs in `fixtures/`, not in
the instrument firmware. It is a tool, not a deliverable.

## Configuration is over USB

Config is a page on a computer, talking to the instrument over its own USB-C
port, not a menu system and not a phone
([ADR 0015](../docs/decisions/0015-one-mcu-no-display.md)). The matrix shows
status only.

**The transport follows the USB PHY rule above.** With MIDI off — the default —
the only USB function is USB-Serial-JTAG, so configuration rides it (Web Serial
from a browser, or a host tool). With MIDI on, the same framed messages go as
SysEx, which Web MIDI can reach. One message format, two carriers; do not let
configuration be the reason MIDI stops being opt-in.

**Single source of truth:** every config edit round-trips. The page edits, the
instrument validates, applies, persists and echoes back. The page never holds
authoritative state.

Build live telemetry over the same link early — it is a test instrument for the
mechanical and calibration work, not just a configuration convenience.

## USB MIDI

A **bring-up tool, not a feature.** Keys, fingering and breath response get
validated in a DAW before any analog hardware exists (milestone E5). The
instrument is a tethered rack device; USB MIDI does not get to constrain the
design.
