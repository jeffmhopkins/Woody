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

`Dir` is this circuit's side of the net — `in`, `out`, `in/out`, `ref` (a
return or reference) or `—` (no connection here, the row is context). `Peer`
is a bare `board/circuit` id when the other end is a circuit in this tree, a
reference designator or part name when it is not, and `—` when there is
nothing on the other end.

| Node | Dir | Peer | Figure | Note |
|---|---|---|---|---|
| `SCLK` | in | `interfaces/spi-link` | `umbilical-pinmap`, `spi-series-r` | From the carrier on `J-UMB`. Pulled **down**, cable side and DAC side. **Not `SCLK_DAC`**, this buffer's output |
| `MOSI` | in | `interfaces/spi-link` | `umbilical-pinmap`, `spi-series-r` | From the carrier on `J-UMB`. Pulled **down**, both sides. Shares a pair with `SCLK` |
| `CS_MOD` | in | `interfaces/spi-link` | `umbilical-pinmap`, `spi-series-r` | From the carrier on `J-UMB`. Pulled **up**, both sides. Shares a pair with `DIG_GND` |
| `DIG_GND` | ref | `interfaces/spi-link`, `module/power-entry` | `umbilical-pinmap`, `dig-gnd-topology` | `CS_MOD`'s return partner. Where it ties is the disputed figure, not a fact this page settles |
| `SCLK_DAC`, `DIN`, `SYNC` | out | `module/dac8568`, `interfaces/spi-link` | — | **Sourced here** — the 74AHCT125 (`U-LVL-MOD`) is this circuit's part. The DAC-side three of the six `R-SPI-PULL` sit on these |
| bus `+5V` after `FB4`/`C4` | in | `module/power-entry` | — | Through `FB4` and `C4`. Supplies the 74AHCT125 and nothing else, and it is the one rail with no diode. Open — see below |
| `OE_MOD` ×4 | ref | `module/link-supervision` | — | This buffer's four enables, tied to `GND` and permanently enabled. The circuit that used to gate them is not fitted. **Not `OE_INST`**, the carrier level shifter's |

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

*The line above is as it was written earlier on 2026-09-21, when the blockquote
it introduces was still here. That blockquote moved verbatim to
[`../../interfaces/spi-link/`](../../interfaces/spi-link/spi-link.md) on
2026-09-21, with the six pulls, and now sits beside `carrier.md` §4's driving
end: the pairing is an argument about what couples into what inside the cable,
and neither end of a cable states it alone. The drawing above stays here.*

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
