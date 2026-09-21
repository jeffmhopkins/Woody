# Digital path and supervision — schematic

**Status:** Drawn 2026-09-21. Fifth and last module page.

The SPI link from the umbilical to the DAC, and the three circuits that decide
what the module does when the instrument is absent, asleep, or hung. None of
this carries signal; all of it decides whether the signal is trustworthy.

**No surveyed Eurorack module has any of it.** That is not evidence the problem
is imaginary — it is a consequence of topology. Everyone else's processor is on
the same board as their DAC and can use its own internal watchdog. Woody's is
**two metres away behind a write-only link**, so the module has to supervise
itself.

## The circuit

```
  etherCON ─┬── SCLK ──┬───────────────────────┐
            │          │                       │
            ├── MOSI ──┼──┬────────────────────┤
            │          │  │                    │
            ├── CS  ───┼──┼──┬─────────────────┤
            │          │  │  │                 │
            │      [R-SPI-PULL ×3]        ┌────┴─────────┐
            │       SCLK↓ MOSI↓ CS↑       │  74AHCT125   │
            │          │  │  │            │  bus +5V     │
            │      DIG_GND                │              │
            │                             │  OE ×4 ◄─────┼──┐
            │                             └────┬─────────┘  │
            │                                  │            │
            │                           [R-SPI-PULL ×3]     │
            │                            SCLK↓ MOSI↓ CS↑    │
            │                                  │            │
            │                   ┌──────────────┴────────┐   │
            │                   │   DAC8568C            │   │
            │                   │   AVDD 5.21V          │   │
            │                   │                       │   │
            │                   │   CLR ◄───────────────┼─┐ │
            │                   └───────────────────────┘ │ │
            │                                   │          │ │
            │                          [R-CLR-PD 10k]      │ │
            │                                   │          │ │
            │                              AGND ┘          │ │
            │                                              │ │
            │        ┌──────────────┐    buffered CS       │ │
            │        │  74HC123     │◄───(DAC side)        │ │
            │        │  5.21V rail  │                      │ │
            │        │  1M × 220nF  │──────Q───────────────┘ │
            │        │  ≈ 99 ms     │                        │
            │        └──────────────┘                        │
            │                                                │
            │   in-amp output ──┐                            │
            │   (0 V absent,    │   ┌──────────┐             │
            │    −0.44 V alive) └───┤ LM311    │             │
            │                       │ ±12 V    │             │
            │   threshold −200 mV ──┤ EMIT→GND ├──collector──┤
            │   (from −12 V)        │ 1M hyst  │             │
            │                       └──────────┘             │
            │                                                │
            │                    bus +5V ─┬─[R-OE-PU 10k]────┘
            │                             └─[820R]─▷|── panel LED
```

## Three rails, on purpose

| Circuit | Rail | Why |
|---|---|---|
| 74AHCT125 | **bus +5 V** | Its job is to clear the DAC's 0.7 × AVDD threshold; the bus rail is a stated requirement (ADR 0005) and the only thing exposed to it |
| `OE` pull-up and the LED | **bus +5 V** | Same node as the buffer's inputs — pulling them to a *higher* rail would push the AHCT125's input clamps. Also fail-safe: rail dies → buffer unpowered → outputs off, LED out |
| **LM311, 74HC123** | **LM317 5.21 V / ±12 V** | Supervision must not die with the rail it supervises. A rack +5 V glitch must not be able to clear the outputs mid-phrase |
| DAC AVDD | **LM317 5.21 V** | Same rail as the watchdog, so `CLR` levels are unambiguous |

## Pulls on **both** sides of the buffer — six, not three

The original three were on the cable side, to stop the buffer's inputs floating
and drawing crowbar current when the instrument is absent. Correct, and
incomplete: **with `OE` disabled the buffer's outputs are Hi-Z**, so the pins
actually floating in that state are the **DAC's** `SCLK`, `DIN` and `SYNC` —
which is the state the pulls were bought for, and the cable-side three do not
reach it.

Polarity is the same on both sides: `CS` up, `SCLK` and `MOSI` down. A stray
edge on `CS` re-frames the 32-bit word, and a DAC8568 frame carries the
software reset, the clear-code register and the internal-reference enable — so
a mis-framed word is a **sticky** failure that the 4 kHz refresh does not
clear, unlike a corrupted data bit which self-heals in 250 µs.

## The presence detect, and why it is the breath line

**Sensing umbilical +12 V does not detect the instrument** — that node is
downstream of the module's own load switch, so it reads "present" whenever the
panel toggle is on, with nothing plugged in. It failed in exactly the state it
existed for, and part of ADR 0004's argument for moving the power switch rested
on it.

The breath receiver already reports everything, for free:

| State | In-amp output |
|---|---|
| Cable unplugged | R4/R5 pull both inputs to `AGND` → **`V_REF` ≈ +0.437 V** |
| Instrument alive | `REF` trim nulls the pedestal → **0 V** |

**Threshold at `V_REF`/2, taken off the trim buffer itself.** That is the whole
circuit, and it **self-centres**: both ends of the table scale with the trimmer,
so a sensor anywhere in its 0.152–0.378 V pedestal band gives the same relative
split without anyone re-picking a number. It also degrades correctly — if the
reference dies, the threshold goes with it and the detect reads "absent".

**Two earlier versions of this paragraph were wrong, and the second was worse
than the first.** The first sensed the output against a fixed −200 mV, which
worked only while `REF` was grounded. The second claimed the trimmer had put
*both* states at 0 V and moved the tap onto the in-amp's input node. Both
claims were wrong: the states are 437 mV apart with the **sense inverted**, not
collapsed — it needed a threshold change, not a new tap. And tapping an input
node is this design's cardinal sin twice over:

- **It loads one input leg.** Holding 60 dB of CMRR needs the tap to present
  ≥ 9.75 MΩ; a 100 kΩ network gives **21 dB**.
- **Comparator bias current lands on the 1 MΩ bias pair.** 100–250 nA × 1 MΩ is
  **100–250 mV** against a 198 mV discriminating signal — it would have read
  "present" with nothing plugged in, which is the exact fault the detector
  exists to catch.

**The LM311 and not an LM393**, which the BOM originally specified: an LM393
cannot see an input below its own V−, and on a split supply its open-collector
output pulls to −12 V, because its output emitter is tied internally to V−.
The LM311's separate emitter pin is exactly why synth circuits use it — Expert
Sleepers ships this circuit, at this hysteresis value, in two modules.

One comparator reports cable connected, +12 V reaching the far end, REF5050
alive, sensor alive, buffer alive, and both analog conductors intact. Nothing
else in the design reports any of those.

## There is no frame watchdog

**Deleted.** A 74HC123 monostable used to assert the DAC's `CLR` when SPI
traffic stopped. The part, its timing pair and its decoupling are gone; `CLR`
is pulled **inactive**, with a solder pad beside it so it can be asserted by
hand.

**It was deleted because it could not do the job it was named for.** ADR 0004
built it to catch "the real-time board hangs mid-note and the rack drones
forever" — and it counts `CS` edges, while `firmware/README.md` mandates
refreshing every channel every pass. A hang *above* the output loop emits
healthy edges indefinitely and the watchdog never fires.

**What it could catch was the link going away**, and that coverage is now
gone too:

| Failure | Watchdog | Now |
|---|---|---|
| Firmware hangs above the output loop | **never caught it** | not caught |
| Cable unplugged mid-note | caught | **not caught — the DAC holds and the rack drones** |
| Instrument loses power mid-note | caught | **not caught** |
| Load switch latches off mid-note | caught | **not caught** |
| Module powered, instrument off | `OE` gating | `OE` gating, unchanged |

So the honest cost of deleting it: **pull the umbilical mid-note and the rack
holds that note until you flip the module's toggle.** That is the everyday
case, not an exotic one.

**What it bought back**, which is why the deletion is defensible: a part that
the cold review found four separate problems with — a retrigger regime nobody
could size without a datasheet, an undefined power-up `Q` state that could
leave it disarmed with a note standing, a software-defeasible clear path
through the DAC's clear-code register, and a 99 ms timeout that would have
fought every "write a code, read the meter" step of E7 through E10.

### The obvious way to get the link coverage back, for no new parts

`CLR` can be driven from the **presence comparator** instead of from a
monostable. It already reports cable connected, far-end power, reference alive,
sensor alive and both analog conductors intact — which is precisely the set of
failures the watchdog actually covered. Presence drops, outputs park.

**The complication is polarity.** `OE` is active low and wants the comparator
*asserted* when the instrument is present; `CLR` is active low and wants the
opposite. One open-collector output cannot serve both senses, so it needs an
inversion — and the obvious way to get one is a **74AHCT14 hex Schmitt
inverter**, which two independent reviews already recommended adding as
baseline for edge cleanup on `SCLK`, `MOSI` and `CS` over 2 m of Cat5.

One part, three jobs. Not adopted here because it is a design decision rather
than a correction, and because it should be taken with the SPI edge-cleanup
question rather than separately.

## Still open

- **The presence tap point**, above. It needs the one-line change described and
  a corrected `R-PRESENCE` row.
- **A power-on reset RC on the '123's own `CLR`**, so the power-up safe state is
  guaranteed rather than probable.
- **The retrigger question was posed against the wrong numbers.** Six frames
  per pass means **~2400 retriggers per timeout at ~16 µs intervals**, not ~400
  at 250 µs — and "empties 220 nF" is the wrong quantity, since only ~83 pC
  accumulates between retriggers. The real gates are the '123's discharge
  `R_on` and whether discharge follows the trigger pulse. A dedicated watchdog
  IC may be the better answer.
- **`LDAC` is not in this design anywhere**, which leaves a CMOS input floating
  on the DAC and means six channels cannot update atomically. **Tie it.** The
  consequence of not having it: every exit from `CLR` — hot-plug, watchdog
  recovery, reboot, an OTA stall — throws intermediate values at the mod jacks
  for 100–200 µs, and no write order avoids it.
- **`SCLK` has no series resistor and `MOSI` does.** That is the wrong way
  round: `SCLK` is the fastest edge on the cable. Series resistors now go on
  all three lines at the driving end, which also closes a back-powering path
  found separately in the power review.
- **The threshold may sit inside the breath signal's own range.** The sensor is
  a *differential* part with its reference port open to the cavity, so negative
  differential pressure drives the output toward the detect threshold. The
  sensor's own minimum bounds it, but the margin is thin and it would present
  as `CLR` firing mid-phrase. **The clean answer may be to demote this
  comparator to LED and health duty and gate `OE` from the link itself** — a
  decision, not a component change.
- **An ESP32-S3 NVS commit or OTA write disables the instruction cache** and can
  stall non-IRAM code on both cores. A config save that overruns 99 ms would
  assert `CLR` mid-note. Measure the real stall before tuning the RC, and put
  the DAC service routine in IRAM.
