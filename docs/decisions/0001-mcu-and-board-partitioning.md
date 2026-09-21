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

> **Both halves of that sentence are superseded**, by ADR 0013 and by the
> decision below. The MCU is a **dev board on a passive carrier at the tail**,
> not a bare module, and there are **no satellite boards**: all four shift
> registers live on that carrier. The topology diagram that stood here
> described a three-zone instrument with the MCU at the top, which ADR 0013
> also replaced. What survives from this ADR is the *family* choice and the
> signal-integrity reasoning below.

```
TAIL   dev boards on a passive carrier: MCU, IMU, 8×8 matrix, breath sensor,
       ADC, reference, ALL FOUR 74LVC165s, umbilical connector, USB-C
        |
        |  four ribbons: one per key cluster, DC switch lines only
        |
BODY   key clusters — switches, and nothing else
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

### The registers live at the tail, not in the clusters

**Decided after the prior-art review found this ADR and ADR 0013 specifying
opposite looms** — one register per cluster here, all four on the carrier
there — with the BOM carrying rows for both. The loom is hand-built once into a
body that is bonded shut, so this could not stay open.

**All four registers go on the carrier at the tail.** Each switch gets its own
conductor back to it.

| | Registers at the tail | One per cluster |
|---|---|---|
| Conductors down the body | **~23** (18 switches + grounds + spares) | ~10 |
| What they carry | **DC levels, filtered at 100 µs** | clock, latch and serial data with fast edges |
| Boards | **1** | 5 |
| Vulnerable to the LED channel | **No** — see the arithmetic below | Yes, and unfilterable |

**The whole argument is that one option's risk is retrofittable and the
other's is not.** A fat loom is a nuisance you can see, measure and re-route on
the bench. A clocked line that picks up an 800 kHz LED edge gives you a wrong
note, intermittently, inside a body that never opens again — and it cannot be
filtered, because filtering a clock is what breaks it.

**The arithmetic, which is decisive.** A 12 V LED edge through ~15 pF of loom
coupling injects roughly 180 pC. On a switch line that charge lands in
`C-KEY`:

```
ΔV = 180 pC / 10 nF = 18 mV        — nothing
ΔV = 180 pC / ~40 pF of bare wire  = 4.5 V   — a false key press
```

The capacitor is doing all the work, and it is only available because the line
is DC. Everything that made the clocked version dangerous — termination on a
multidrop line, chain ordering, the asynchronous `SH/LD` glitch that reloads
all four registers mid-shift — **stops existing** when the chain never leaves
the board.

What it costs is physical: **about 23 conductors have to fit down a side
channel described as "narrow, but continuous end to end"** (ADR 0009), as four
ribbons, one per cluster, thinning as they drop off. That has not been checked
against the real geometry and is an **M4 CAD item**, not an assumption.

### Key-line signal integrity

The switch lines run the length of the body as unshielded conductors, alongside
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

1. **A ground return every few signals.** Eighteen switch lines down a
   14-inch body sharing one return is a loop antenna next to an 800 kHz LED
   data line. One ground per four signals in each ribbon, which a standard
   ribbon gives for free by alternating.
2. **Star it from the carrier — one ribbon per cluster.** With the registers at
   the tail there is nothing to chain, and four short independent runs are
   easier to build and easier to fault-find than one trunk with taps.
3. ~~**Order the chain so serial data flows toward the clock source.**~~
   **Moot.** This was the rule for a clocked loom, and the research found it
   overstated anyway — the skew between adjacent clusters was ~0.5 ns against a
   propagation delay of 5–14 ns, so the wrong order degraded hold margin by
   roughly 12 % rather than violating it. `key-layout.yaml` said it would have
   put "hold-margin violations" into a bonded body, which was an honesty marker
   pointing the wrong way. The chain is now four devices on one PCB with
   millimetre traces, and the question does not arise.

   **`bit 0` still means the first bit clocked out**, because firmware needs it
   defined. It is now a board-layout detail rather than a loom decision.
4. ~~**33–68 Ω series termination at the MCU** on the clock and latch lines.~~
   **Also moot, and it was wrong as written**: series termination is a
   point-to-point technique, and those lines dropped on four boards. On a
   multidrop line intermediate receivers sit at the incident half-step —
   at 68 Ω that step could land at 1.96 V against a 2.0 V threshold, so the
   BOM's own "33–68 Ω" range spanned fine to marginal, in the counterintuitive
   direction. On one board it is a non-question.
5. **100 nF at every register.** Still required — a 74x165's output edges brown
   out a local rail with no reservoir — but now four caps on the carrier rather
   than one on each of four satellite boards.
6. **Tie `CLK INH` low at all four devices, and pull every unused parallel
   input.** Both are permanent, both were sitting only in a review document,
   and the five "free" spare bits are floating CMOS inputs — the exact fault
   `R-KEY-PU` exists to fix.

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
- The 74x165 chain suits this geometry well. No matrix, no ghosting, no
  diodes. **It does mean per-key wiring back to a central point**, which an
  earlier version of this line listed as a thing the chain avoided — that was
  true of the per-cluster arrangement and is the price of moving the registers
  to the tail. It is the right price; see above.
- **Chain is 4 registers, 32 bits, for 18 switches** (ADR 0010), all four on the
  carrier. The 14 spare bits are free expansion for octave, mode and hold
  inputs, and 4–6 of them carry the marker pattern. Full chain reads in ~32 µs
  at 1 MHz, about 13 % of a 250 µs loop period, and it can be clocked
  considerably faster now that it is all on one board.
- LED power and data run the length of the body too. Keep their ground return
  separate from the analog section and star-ground at one point, or the LEDs
  will be audible.
