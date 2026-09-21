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

**Redrawn 2026-09-21** after a 20-agent review found this drawing still
carried two deleted parts, a `CLR` net pulled the wrong way, and the
superseded umbilical pin map. See *What this redraw changed* below.

```
  etherCON            NEW PIN MAP - see ADR 0004
  ─┬── 4 SCLK ──┬─────────────────────────┐
   │            │                         │
   ├── 5 MOSI ──┼──┬──────────────────────┤     SCLK+MOSI share pair (4,5)
   │            │  │                      │     CS+DIG_GND share pair (7,8)
   ├── 7 CS  ───┼──┼──┬───────────────────┤
   │            │  │  │                   │
   └── 8 DIG_GND│  │  │              ┌────┴─────────┐
        │   [R-SPI-PULL x3]          │  74AHCT125   │
        │    SCLK↓ MOSI↓ CS↑         │  bus +5V     │
        │        │  │  │             │  OE x4 → GND │  tied ENABLED
        │    DIG_GND                 └────┬─────────┘
        │                                 │
        │                        [R-SPI-PULL x3]
        │                         SCLK↓ MOSI↓ CS↑
        │                                 │
        │                  ┌──────────────┴────────┐
        │                  │   DAC8568C            │
        │                  │   AVDD 5.21V          │
        │                  │                       │
        │          AVDD ───┤ CLR  ◄── [R-CLR-PU]   │   PULL-UP. Active low.
        │           5.21V  │          10k          │   Held INACTIVE.
        │                  │            │          │
        │                  │      [LK-CLR pad]     │   solder pad to GND,
        │                  │            │          │   bring-up only
        │                  │           GND         │
        │                  │                       │
        │           GND ───┤ LDAC ◄── [R-LDAC]     │   STRAP TO GND, 0 ohm.
        │                  │          0R           │   NOT a pull-up - see below.
        │                  └───────────────────────┘
        │
        └── analog star, single tie (ADR 0004)

   NOT HERE ANY MORE: the 74HC123 frame watchdog and the LM311 presence
   comparator. Both deleted; see "What this redraw changed".
```

## What this redraw changed

The previous drawing was wrong in four ways, all found independently by
more than one reviewer in `docs/review/2026-09-21-hardware-and-standards-review/`.

**1. It still drew the deleted watchdog and presence comparator.** The
74HC123 and LM311 were deleted — in ADR 0004, in `bom.csv`, and in this
page's own prose two sections below — and were still drawn here, still
allocated rails in the table below, and still counted in `bom.csv`'s
`C-DECOUPLE` quantity. **`C-DECOUPLE` drops from 21 to 19.** Neither part
ever had a BOM row, so a board built from the old drawing would have had
two footprints and no parts to fit.

**2. `CLR` was drawn as a pull-DOWN on an active-low pin.** `[R-CLR-PD 10k]`
to `AGND`, against `bom.csv`'s `R-CLR-PU`. With the watchdog deleted
nothing else drives that pin, so **as drawn `CLR` was asserted permanently:
six dead CV outputs, and no SPI write able to change them.** This was the
single cheapest way in the whole design to end up with a module that does
nothing at all.

**3. `OE` gating is gone.** It was driven from the presence comparator's
collector, pulled up through `R-OE-PU` to bus +5 V, and shared a node with
the panel LED through an 820 Ω resistor. With the comparator deleted, `OE`
is **tied low — permanently enabled** (`bom.csv` `U-LVL-MOD` already says
so). `R-OE-PU` and the 820 Ω had no BOM rows; `R-LED-PANEL` is 2.2 kΩ from
+12 V analog and is drawn on the power page, not here.

**4. The umbilical pin map is the corrected one.** `SCLK` and `MOSI` now
share pair (4,5); **`CS` is paired with `DIG_GND` on (7,8)**. Previously
`MOSI` and `CS` shared a pair with **no return conductor between them** —
two unrelated fast edges twisted tightly together, which is the most
efficient possible coupling rather than the cancellation twisting is for.
Two reviewers independently computed **365–907 mV of saturated intra-pair
crosstalk against `CS`'s 678 mV `V_IL` margin** and independently proposed
this exact swap. It improves the margin from about **1.9:1 to 6200:1** and
costs nothing but the pin assignment.

> **Why `CS` is the one that must not glitch.** It frames the word. A
> glitch restarts the bit count mid-message, so every bit lands in the
> wrong field — including the software-reset and internal-reference-enable
> bits. ADR 0004 deleted `MISO`, so **firmware can never read back what the
> DAC actually received.** It is the only failure in the digital path that
> does not self-heal on the next update; everything else is corrected 250 µs
> later.
>
> Pairing `SCLK` with `MOSI` is safe *by construction*: the receiver only
> samples `MOSI` on a `SCLK` edge, so coupling between them lands where it
> is not being looked at.

> **Still open — the bus +5 V rail.** Three reviewers independently want it
> dropped: it is what makes a reversed 16-pin ribbon dangerous (module
> ground lands on bus +5 V and +12 V), **zero of eight** surveyed published
> designs take a sub-12 V rail from the bus, and it is the only rail here
> with no reverse protection — on a branch whose bulk capacitor vents when
> reverse-biased. It exists for this one 74AHCT125. Deriving it locally from
> the protected +12 V is one TO-92 and two capacitors, and would allow a
> 10-pin header. **Not changed here, because it is a rail change and a
> connector change, not a drawing correction.**

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

## There is no presence detect either

Deleted with the watchdog, and for converging reasons. Two versions were built:
one gating the buffer's `OE` from "+12 V on the umbilical" — a node downstream
of the module's own load switch, which reads *present* with nothing attached —
and one watching the breath line through an LM311.

The second failed review three ways: its threshold sat **inside the breath
signal's own range**, because the sensor is differential with its reference
port open to the cavity and drawing breath moves toward the trip point; it
**locked out every standalone module milestone**, since a dev board on a patch
lead drives nothing into that pair; and it **failed toward "present"** on the
most likely single fault in its own chain.

**`OE` is tied enabled**, which is what every surveyed Eurorack module does.
The floating-CMOS case it was protecting against is what the six `R-SPI-PULL`
resistors are for. The panel LED becomes an ordinary power indicator.

**The knowing moved to the instrument**, which digitises breath anyway and has
a display to report on. The accepted loss is that the instrument's ADC reads
*before* the umbilical, so a broken conductor in the cable is invisible to it —
audible immediately, and in a replaceable part rather than a sealed one. Full
reasoning in ADR 0004.

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

### The obvious way to get the link coverage back — and what it actually costs

> **This section was headed "for no new parts" and written in the present tense
> until 2026-09-21.** Both were wrong. The presence comparator is deleted on
> this same page, so it reports nothing; restoring this coverage means
> restoring **an LM311, its two decoupling caps, `R-PRESENCE` and a 74AHCT14** —
> four parts, none of which has a BOM row today. The proposal may well be
> right. It has to be costed as a restoration, and it has to answer the three
> faults that deleted the comparator in the first place (ADR 0004), of which
> the threshold problem below is one.

`CLR` **could** be driven from a **restored presence comparator** instead of
from a monostable. Such a comparator would report cable connected, far-end
power, reference alive, sensor alive and both analog conductors intact — which
is precisely the set of failures the watchdog actually covered. Presence drops,
outputs park.

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

- **Whether to restore link supervision at all**, and at what cost. The section
  above is the candidate; it is four parts, not zero. This is the one open
  supervision question, and it subsumes the three that used to stand here.
- **An ESP32-S3 NVS commit or OTA write disables the instruction cache** and can
  stall non-IRAM code on both cores. With no watchdog there is no `CLR` to fire
  mid-note, so the consequence is now a *stalled refresh* rather than a reset:
  the jacks hold their last value for the duration of the stall, which is the
  benign direction. Still worth measuring, and the DAC service routine still
  belongs in IRAM.

### Three bullets retired here, 2026-09-21

All three designed a part that this page deletes 55 lines above. Left standing,
an engineer working the open list would have sized an RC and a retrigger regime
for a footprint that is not on the board.

| Retired bullet | Why |
|---|---|
| A power-on reset RC on the '123's own `CLR` | There is no '123 |
| The retrigger arithmetic (~2400 retriggers per timeout, the 220 nF / 83 pC question, "a dedicated watchdog IC may be better") | Same — and if supervision is ever restored, the section above is where that work starts, not here |
| The presence tap point "needs a corrected `R-PRESENCE` row" | `R-PRESENCE` is in no BOM and never was. Nothing to correct |
| The comparator threshold "may sit inside the breath signal's own range" | True, and it is one of the **three reasons the comparator was deleted** (ADR 0004), not an open item about tuning it |

### Two bullets closed here, 2026-09-21

- **`LDAC` — corrected 2026-09-21, and it was drawn wrong.** SBAS430E p.38,
  verbatim: *"For such synchronous updates, the LDAC pin is not required and
  **it must be connected to GND permanently**."* The same page: the internal
  LDAC register defaults to `0x00`, and *"if the LDAC register bit is set to
  '0', the DAC channel is controlled by the LDAC pin."* So with the register at
  its default and the pin pulled **high**, the buffer-to-DAC-register transfer
  is **gated** — and with no `MISO`, firmware can never discover it. A module
  that accepts every word and moves no output.

  This is the pull-down-on-`CLR` defect mirrored: same page, same redraw, same
  class, opposite polarity. `R-LDAC` is now a **0 Ω strap to GND**.

  *(The old escape hatch — "it becomes a GPIO, and the pin is already broken
  out" — was false twice: there is no pad, and all eight umbilical conductors
  are allocated, so there is nothing at the module end to drive it.)*

- ~~`LDAC` — closed. `R-LDAC`, 10 kΩ to `AVDD`, is drawn above and carries a
  `bom.csv` row. Tied, not driven: a hardware `LDAC` was considered and
  declined, so the six populated channels update as each word lands rather than
  together. The cost is real and accepted — every exit from `CLR` throws
  intermediate values at the mod jacks for 100–200 µs and no write order avoids
  it. If E10 finds that audible it becomes a GPIO, and the pin is already
  broken out.
- **`SCLK` has no series resistor and `MOSI` does** — closed. It is
  `R-SPI-SER` ×3, 100 Ω, one on each of `SCLK`, `MOSI` and `CS` at the driving
  end (`carrier.md`, `bom.csv`, and ADR 0004 now agrees). That also closes the
  back-powering path found separately in the power review.
