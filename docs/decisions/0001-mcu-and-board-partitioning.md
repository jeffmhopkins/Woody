# 0001 — MCU selection and board partitioning

**Status:** Accepted. Partitioning revised by
[ADR 0013](0013-two-mcu-split.md) — display and WiFi moved to a second MCU. The
family choice below still holds for the real-time board, and the C6 analysis
still applies to *that* role; a C6 is fine as the display board.

## Context

The previous project used a Teensy 3.2. This iteration wants a modern part with
a display, USB, and enough I/O for a distributed instrument.

Two physical constraints drive the partitioning: the IMU sits near the bottom of
the instrument, and the display sits near the top where it can be read while
playing. In a body roughly two feet long, those cannot share a board.

**On why the IMU goes low** — stated loosely in an earlier revision as "the
lever arm matters", which is only half right. *Tilt angle is
position-independent*: a rigid body has one orientation, and a sensor anywhere
on it reads the same pitch and roll. Position matters for **acceleration**,
where a sensor further from the pivot at the player's hands and neck sees
larger tangential accelerations. The 2021 firmware used acceleration as a
modulation source separate from angle (ADR 0007), so gesture sensitivity is the
real reason to mount low — not tilt sensing.

## Options

**ESP32-S3.** Native USB OTG, so a genuinely class-compliant USB MIDI device
with no serial-bridge workaround and no host drivers. 2.4 GHz WiFi and BLE 5
built in, which ADR 0012 requires for phone-based configuration. Dual core
allows pinning the sensor and output loop to one core while the display and
radio live on the other.
Most nice-display dev boards are S3-based. Note it has **no DAC at all** — the
original ESP32's two 8-bit DACs were dropped on the S3. Irrelevant here, since
8 bits was never usable for pitch CV.

**ESP32-P4.** More capable, real MIPI display support, but **no built-in
radio** and less mature software support. The radio is now a requirement
(ADR 0012), so this is ruled out outright rather than merely disfavoured.

**ESP32-C6.** Rejected, and worth spelling out because C6 boards are common in
the integrated screen-and-MCU form factor this project wants (ADR 0008). Three
consequences, in descending order of severity:

- **Single core.** The whole timing architecture here is a core split: sensor,
  key scan and DAC output own one core; display, WiFi and web server own the
  other. On a single core that guarantee becomes a software discipline instead —
  a 4 kHz high-priority task can still preempt rendering, but any driver that
  blocks with interrupts masked or holds a lock across a DMA wait puts jitter
  straight into the output loop. Workable with care; not the same thing as
  workable by construction.
- **No USB OTG device peripheral.** C6 has USB Serial/JTAG but not the OTG
  controller that class-compliant USB MIDI needs. That removes E5, the first
  playable milestone and the whole strategy of validating keys, fingering and
  breath response in a DAW before any analog hardware exists. WiFi telemetry
  (F6) covers observability but not *playing* the thing.
- **Fewer GPIO**, against a budget (ADR 0008) that is already the binding
  constraint on board choice.

The radio is present on C6, so ADR 0012 is satisfied — but the first two points
are architectural, not preferences.

## Decision

**ESP32-S3**, as a bare module on a custom carrier — not a dev board — with
satellite boards distributed along the body.

Topology:

```
TOP   ESP32-S3 module + display (SPI, short) + USB-C
       |  ribbon: power, slow SPI, LED data
MID   74HC165 key chain, daisy-chained per cluster
       |
BOT   IMU, umbilical connector to the rack module
```

The display is the only thing that cannot run far — high-bandwidth SPI with many
signals will ring and crosstalk over any distance. (The instrument is 18 inches
overall per ADR 0009, so the longest run is nearer 14–16 inches than the two
feet this analysis originally assumed. The topology stands; the margin is
better than feared.) So the MCU lives with the display
and everything else runs long and slow. Bandwidth down the body is trivial: six
16-bit channels at 4kHz is ~576 kbit/s, comfortable at 2MHz SPI over twisted
pair.

The two SPI hosts on the S3 get split — but **not the way this line originally
said**, and not for the reason it gave. ADR 0013 moved the display to a second
MCU, so both of the real-time board's SPI hosts are free, and a hard electrical
constraint decides how they are used:

**The 74x165 chain cannot share MISO with the MCP3202.** `QH` on a 74x165 — any
family — is a permanently driven totem-pole output with no output-enable pin. It
is not an SPI peripheral and cannot be taken off the bus. The ADC's `DOUT` does
tri-state on CS high, so the shift register wins the line unconditionally: the
**ADC could never be read**, and two push-pull drivers would fight continuously.

So:

| Host | Devices | Why together |
|---|---|---|
| **SPI2** | DAC8568 (down the umbilical) + MCP3202 | Both tri-state properly on CS |
| **SPI3** | 74x165 chain alone | `QH` is always driven; it gets a bus to itself |

SPI3 needs only SCK and MISO plus the existing latch GPIO. Two extra pins
against sixteen of headroom — and it has the side benefit the original line was
after, since a key scan and a CV update no longer contend.

### Key-chain signal integrity

The chain runs the length of the body as four unshielded conductors, alongside
LED data and LED power, inside a body that cannot be reopened. Two decisions
elsewhere make a single corrupted read worse than it looks:

- **Asymmetric debounce fires on the first closed sample** (below), so one
  corrupted 32-bit word becomes **one spurious note-on at full velocity, with no
  filtering**. A conventional symmetric 20 ms window would silently absorb it.
- **`SH/LD` is asynchronous and level-sensitive.** Any glitch below V_IL during
  the 32-clock shift re-loads all four registers and corrupts the whole word.

**Before any of that: the inputs need pull-ups, and there were none.** A 74x165's
parallel inputs have no internal pull-up, so every key input floated when its
switch was open — in a side channel shared with WS2815 power and 800 kHz data.
A 12 V LED edge at ~120 V/µs through ~15 pF of loom coupling injects a full
false level, straight into an asymmetric debounce that fires on the *first*
closed sample. Three reviewers found this independently and it is unretrofittable.

**Per switch position: 10 kΩ to 3V3, 100 Ω in series, 10 nF to ground**, on the
cluster board. Press stays instant at ~1 µs; release gains a free ~93 µs
hardware filter; LED coupling drops about 54 dB. Twenty-one sets, so the three
reserved spare-switch bits are covered too. (`R-KEY-PU`, `R-KEY-SER`, `C-KEY`.)

Five further fixes, in descending order of value. The first four are wiring and
cost nothing but planning; they cannot be retrofitted into a bonded body.

1. **A ground return per signal.** The highest-value item on this list. Four
   signals down a 14-inch body sharing one return is a loop antenna next to an
   800 kHz LED data line.
2. **Chain the topology, do not star it.** One run passing through each cluster
   board in turn, not four stubs from a central point.
3. **Order the chain so serial data flows *toward* the clock source.** This
   makes propagation skew eat **setup** margin rather than **hold** margin.
   Setup margin is recoverable by clocking slower; hold margin is not
   recoverable at any speed.

   Concretely, now that the MCU is at the **tail** (ADR 0013): the cluster
   **physically nearest the MCU** is the one whose `QH` drives MISO, and the
   cluster **furthest** takes the loom's `SER` end. Walking outward from the
   tail that is `right_thumb → right_hand → left_thumb → left_hand`. Why it
   works: each device's clock arrives from the MCU *before* its data source's
   does, because the source is further out, so data always arrives late
   relative to the local edge — late is setup, early is hold.

   `config/key-layout.yaml` carries this order, with **bit 0 = the first bit
   clocked out = the device nearest the MCU**. That definition is the thing
   that was ambiguous, and it is the thing that decides which way round to
   build the loom.
4. **33–68 Ω series termination at the MCU** on the clock and latch lines.
5. **100 nF at every register**, on its own board. There is no controller-side
   decoupling in the design at all, and a 74x165's output edges brown out a
   local rail that has no reservoir.

**On family choice: the part stays 74LVC165A, but the recorded reason for it was
backwards.** The BOM justified LVC as *"better drive over a 14 in chain"*. Over
an **unterminated** line, stronger drive and faster edges are exactly what
produces ringing and reflections — the drive that helps into a lumped load hurts
into a transmission line. 74HC165 at 3.3 V has edges slow enough not to need
termination at all, and would have been the lower-risk choice on those grounds.

Either family works here. LVC is kept because it is specified natively at 3.3 V
and is already selected — but it is kept **with item 4 above**, the series
termination, which is what actually makes the drive argument safe rather than
merely confident. If the chain misbehaves at E4 and termination does not settle
it, 74HC165 is a drop-in on the same SOIC-16 footprint.

### Two firmware rules the chain depends on

Both are free, and both are the difference between a detectable error and a
spurious note.

**Require two consecutive agreeing samples before a note-on.** At the 4 kHz loop
rate that is 250 µs of added latency — inaudible, and a twentieth of the 5 ms
budget. (The chain now has its own SPI host, so it *could* be scanned faster
than the output loop if the measurement at M1 says bounce demands it.) Note-*off*
stays filtered as before. This keeps the asymmetric debounce's fast attack while
removing its single-sample credulity.

**Use 4–6 of the 14 spare chain bits as a fixed marker pattern.** The pins, the
wires and the devices already exist, so this costs nothing but the decision to
wire it — and it cannot be added later. Firmware checks the marker on every
read; a frame that fails it **holds the previous frame** rather than acting on
garbage, and increments a **visible error counter**.

That counter is the point. It is a framing check, not an error-detecting code —
it cannot correct anything and will miss some corruptions — but it converts an
invisible intermittent fault into a number on the display that says whether the
looms are good. Without it, a marginal chain presents as occasional wrong notes
that are indistinguishable from playing mistakes.

**The core split carries the WiFi stack too.** Sensor read, key scan and DAC
output own one core; display, radio and web server own the other. The radio is
the less polite neighbour of the two — see ADR 0012 for why it is also off
during performance.

## Consequences

- Dev boards remain the bring-up platform and are not wasted — they are the
  reference the custom boards get checked against.
- Buy a **plain** S3 dev board plus a **separate** display module, so the bench
  setup matches the final architecture rather than an integrated-screen board
  that would have to be unlearned later.
- Custom carrier design needed eventually: USB-C, ESD protection, boot/reset,
  3.3V regulation. Espressif publishes reference designs for this.
- The 74HC165 chain suits this geometry well — four wires running the length of
  the body, one register per key cluster. No matrix, no ghosting, no long
  parallel runs, no per-key wiring back to a central point.
- **Chain is 4 registers, 32 bits, for 18 switches** (ADR 0010): one device per
  cluster — left hand, left thumb, right hand, right thumb — ordered down the
  body. One register per cluster wastes 14 bits but makes every satellite board
  identical, and the spare bits are free expansion for octave, mode and hold
  inputs. Full chain reads in ~32 µs at 1 MHz, about 13% of a 250 µs loop
  period, and it can be clocked considerably faster.
- LED power and data run the length of the body too. Keep their ground return
  separate from the analog section and star-ground at one point, or the LEDs
  will be audible.
