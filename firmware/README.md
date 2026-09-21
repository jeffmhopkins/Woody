# Firmware

**Two images** ([ADR 0013](../docs/decisions/0013-two-mcu-split.md)):

- `realtime/` — ESP32-S3. Keys, breath, IMU, DAC loop, USB MIDI. Owns all
  state and persistence. This is the instrument.
- `display/` — the AMOLED board. Panel, WiFi, web app. Renders what it is told
  and forwards what the user does. **Persists nothing.**

Joined by a framed UART. Put a protocol version in the frame header from the
first commit — two images that can drift apart need a way to notice.

PlatformIO, ESP-IDF underneath. Nothing here yet — Track F follows Track E
(see [ROADMAP.md](../ROADMAP.md)).

## Architecture constraints

These come from [ADR 0001](../docs/decisions/0001-mcu-and-board-partitioning.md)
and [the latency budget](../docs/reference/latency-budget.md), and they are not
negotiable without revisiting those:

- **4 kHz loop** for sensor read and DAC update, pinned to one core.
- **Display renders on the other core, on its own SPI host.** A display refresh
  must never block the output loop.
- **Asymmetric key debounce** — fire immediately on press, filter only the
  release. A symmetric window puts its full length into the attack. The release
  window is set from **measured** KS-33 bounce (milestone M1), not from the
  conventional 20 ms the 2021 firmware used.
- **Per-channel smoothing in software**, not in the analog filter. The analog
  filter is fixed; firmware knows what each channel carries.
- **Nothing expressive touches the ESP32's internal ADC.** It is noisy and
  nonlinear, and breath drives a 0–10V output where that shows.
- **WiFi and the display are on the other MCU.** They cannot preempt the output
  loop. What remains is the current transient a transmit burst puts on the
  shared rail, handled with separate regulators rather than by scheduling
  ([ADR 0012](../docs/decisions/0012-configuration-interface.md),
  [ADR 0013](../docs/decisions/0013-two-mcu-split.md)).
- **Refresh everything, every pass. Never write-on-change.** The umbilical is
  write-only — `MISO` was deleted from the cable (ADR 0004) — so nothing
  downstream can ever be read back. *With no readback, shared state can only be
  made safe by being made stateless.* This is the rule, not an optimisation
  note; see below for the failure that produced it.

### Why statelessness, specifically

The design review found this by one route and two diagnostics findings arrived
at it from the opposite direction, so it is worth stating the case once.

The mod channels are `Vout = 4·Vdac − 3·V_ref`, with `V_ref` the shared
**3.3333 V** from DAC channel 7 — **written once at boot** (ADR 0006). *(The
value changed with the two-resistor redraw in `mod-channels.md`; writing the
old 2.5 V into channel 7 against the current 10 k/30 k network gives a
−7.5…+12.5 V window — wrong span, and it clips positive.)* When the module
watchdog asserts `CLR`, every DAC channel including channel 7 goes to zero
scale. Firmware then rewrites the five signal channels, because those are the
ones it thinks of as signals, and `Voffset` stays at 0. Every mod jack pins at
`4 × Vdac` ≈ +11.45 V and stays there.

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

## The instrument must stay recoverable

The body is bonded. Everything here exists because a failed flash cannot be
answered by opening the instrument.

- **Two OTA partitions, with `CONFIG_BOOTLOADER_APP_ROLLBACK_ENABLE`.** An
  image that does not mark itself valid is rolled back by the bootloader on the
  next boot. Free, and it turns the most likely bricking event into a reboot.
- **USB MIDI is opt-in, not the default.** On the ESP32-S3 the internal PHY
  routes to USB-Serial-JTAG *or* USB-OTG, never both. The moment the
  application claims OTG the `DTR`/`RTS` download-mode path is gone. Leaving
  MIDI off until the player enables it keeps the serial-JTAG reset path alive
  through every boot that has not been asked for MIDI.
- **The recovery ladder, in order.** (1) OTA rollback. (2) USB-Serial-JTAG
  through the tail USB-C slot — which is why MIDI is opt-in. (3) The console
  header under the service cover (ADR 0009), for watching a board that boots
  but misbehaves. **There is no hardware boot-force**: `EN` and `IO0` are not
  broken out on the ESP32-S3-Matrix, and soldering to them would end the dev
  board's life as a swappable module. A corrupted *bootloader* therefore ends
  the instrument — narrow, behind two mitigations, accepted.
- **The display board is flashed over its UART, by the real-time board.** That
  closes ADR 0013's open question and removes the one case where a board with
  no external connector of its own needed hardware recovery. It gets the same
  two OTA partitions.
- **Exercise the ladder at M8**, before the body closes, so it is known good
  rather than assumed.

## The lights are instrument-side, and so is everything about them

**The strips and the matrix read the MCU's own digitised breath value.** Not
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
  `note` keys only; the three right-thumb switches are `control` and must never
  enter it (ADR 0010).
- **Routing matrix** — four mod channels, each with source, scale, offset, curve
  and slew.

Both live in NVS and are editable from the display and over USB.

## Bring-up fixtures

Throwaway test firmware for E-track milestones belongs in `fixtures/`, not in
the instrument firmware. It is a tool, not a deliverable.

## Configuration lives on a phone

Config is a web app served from the display board's flash over SoftAP, not a
menu system ([ADR 0012](../docs/decisions/0012-configuration-interface.md)). The
display shows status only.

**Single source of truth:** every config edit round-trips. The phone edits, the
display board forwards, the real-time board validates, applies, persists and
echoes back. The display board never writes authoritative state — two
authorities that can disagree is the failure mode worth designing out.

Build the live-telemetry WebSocket early — it is a test instrument for the
mechanical and calibration work, not just a configuration convenience.

## USB MIDI

A **bring-up tool, not a feature.** Keys, fingering and breath response get
validated in a DAW before any analog hardware exists (milestone E5). The
instrument is a tethered rack device; USB MIDI does not get to constrain the
design.
