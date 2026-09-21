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

## Interfaces

Every net that crosses this circuit's boundary. Quantities appear **only** as a
citation into `config/figures.yaml` — this table names nodes, it does not
restate values.

| Node | Dir | Peer | Figure | Note |
|---|---|---|---|---|
| `SCLK` | in | `carrier` via the umbilical | `umbilical-pinmap`, `spi-series-r` | Pulled **down**, cable side and DAC side |
| `MOSI` | in | `carrier` via the umbilical | `umbilical-pinmap`, `spi-series-r` | Pulled **down**, both sides. Shares a pair with `SCLK` |
| `CS` | in | `carrier` via the umbilical | `umbilical-pinmap`, `spi-series-r` | Pulled **up**, both sides. Shares a pair with `DIG_GND` |
| `DIG_GND` | ref | `carrier` via the umbilical | `umbilical-pinmap`, `dig-gnd-topology` | `CS`'s return partner. Where it ties is the disputed figure, not a fact this page settles |
| `SCLK`, `DIN`, `SYNC` | out | `module/dac8568` | — | Buffer outputs. The DAC-side three of the six `R-SPI-PULL` sit on these |
| bus +5 V | in | Eurorack bus header | — | Supplies the 74AHCT125 and nothing else. Open — see below |
| `OE` ×4 | ref | `module/link-supervision` | — | Tied to `GND`, permanently enabled. The circuit that used to gate it is not fitted |

## The circuit

**Redrawn 2026-09-21** after a 20-agent review found this drawing still
carried two deleted parts, a `CLR` net pulled the wrong way, and the
superseded umbilical pin map. See *What this redraw changed* below.

*The DAC8568C half of this drawing moved to
[`../dac8568/dac8568.md`](../dac8568/dac8568.md) on 2026-09-21, and "What this
redraw changed" moved to [`notes.md`](notes.md). The gap in the middle of the
block below is where the DAC box was.*

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
        │
        └── analog star, single tie (ADR 0004)

   NOT HERE ANY MORE: the 74HC123 frame watchdog and the LM311 presence
   comparator. Both deleted; see "What this redraw changed".
```

## The pin map, and why the pairing is what it is

*Moved verbatim from the tail of "What this redraw changed", 2026-09-21. The
record of the pin map being corrected is in [`notes.md`](notes.md); the
reasoning below is live, so it stayed here.*

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

## Still open

- **An ESP32-S3 NVS commit or OTA write disables the instruction cache** and can
  stall non-IRAM code on both cores. With no watchdog there is no `CLR` to fire
  mid-note, so the consequence is now a *stalled refresh* rather than a reset:
  the jacks hold their last value for the duration of the stall, which is the
  benign direction. Still worth measuring, and the DAC service routine still
  belongs in IRAM.

> **Still open — the bus +5 V rail.** Three reviewers independently want it
> dropped: it is what makes a reversed 16-pin ribbon dangerous (module
> ground lands on bus +5 V and +12 V), **zero of eight** surveyed published
> designs take a sub-12 V rail from the bus, and it is the only rail here
> with no reverse protection — on a branch whose bulk capacitor vents when
> reverse-biased. It exists for this one 74AHCT125. Deriving it locally from
> the protected +12 V is one TO-92 and two capacitors, and would allow a
> 10-pin header. **Not changed here, because it is a rail change and a
> connector change, not a drawing correction.**

*(Supervision — the deleted frame watchdog, the deleted presence detect, and
what restoring either would cost — is in
[`../link-supervision/link-supervision.md`](../link-supervision/link-supervision.md).
Superseded values and the redraw record are in [`notes.md`](notes.md).)*
