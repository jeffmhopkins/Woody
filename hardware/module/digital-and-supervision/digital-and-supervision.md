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

The `Dir` and `Peer` columns are defined once in
[`hardware/README.md`](../../README.md#the-interfaces-table).

| Node | Dir | Peer | Figure | Note |
|---|---|---|---|---|
| `SCLK` | in | `interfaces/spi-link` | `umbilical-pinmap`, `spi-series-r` | From the instrument, arriving on `J-UMBILICAL` (`J-UMB-MOD` in the spi-link netlist). Pulled **down**, cable side and DAC side. **Not `SCLK_DAC`**, this buffer's output |
| `MOSI` | in | `interfaces/spi-link` | `umbilical-pinmap`, `spi-series-r` | From the instrument, arriving on `J-UMBILICAL` (`J-UMB-MOD` in the spi-link netlist). Pulled **down**, both sides. Shares a pair with `SCLK` |
| `CS_MOD` | in | `interfaces/spi-link` | `umbilical-pinmap`, `spi-series-r` | From the instrument, arriving on `J-UMBILICAL` (`J-UMB-MOD` in the spi-link netlist). Pulled **up**, both sides: `R-PULL-CS` (100 kΩ to `LOGIC_5V`) here, and 10 kΩ to 3V3 at the instrument. Shares a pair with `DIG_GND` |
| `DIG_GND` | ref | `interfaces/spi-link`, `module/power-entry` | `umbilical-pinmap`, `dig-gnd-topology` | `CS_MOD`'s return partner, and the plane this circuit sits over. It meets the other grounds only at the star (`NT-DIG-MOD`, on `module/power-entry`'s page) |
| `SCLK_DAC`, `DIN`, `SYNC` | out | `module/dac8568`, `interfaces/spi-link` | — | **Sourced here** — the 74AHCT125 (`U-LVL-MOD`) is this circuit's part. The DAC-side three of the six `R-SPI-PULL` sit on these |
| `LOGIC_5V` | in | `module/power-entry` | — | The module's own 5 V (`U-REG-LOGIC`). Supplies the 74AHCT125 and nothing else. The bus +5 V is not used |
| `OE_MOD` ×4 | ref | `module/link-supervision` | — | This buffer's four enables, tied to `GND` and permanently enabled. The circuit that used to gate them is not fitted. **Not `OE_INST`**, the carrier level shifter's |

## The circuit

*Connectivity is **[`netlist.yaml`](netlist.yaml)**, not this drawing.
The drawing is a representation of it, `tools/check-netlist.py` checks that
the two agree, and where they do not the netlist wins.*


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
        │    SCLK↓ MOSI↓ CS↑(100k)   │  LOGIC_5V    │
        │        │  │  │             │  OE x4 → GND │  tied ENABLED
        │    DIG_GND                 └────┬─────────┘
        │                                 │
        │                        [R-SPI-PULL x3]
        │                         SCLK_DAC↓ DIN↓ SYNC↑   ◄ buffer OUTPUTS,
        │                                                 not the same nets
        │                                                 as the three above
        │                                 │
        │
        └── the star, through NT-DIG-MOD (dig-gnd-topology)

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

**The bus +5 V rail — settled 2026-09-30.** Three reviewers wanted it dropped:
it made a reversed 16-pin ribbon dangerous, **zero of eight** surveyed
published designs take a sub-12 V rail from the bus, and it was the only rail
with no reverse protection. The owner: *"Create the 5v locally"* and *"We keep
the standard header, we just don't use the 5 volt."* So the 74AHCT125 runs
from `LOGIC_5V`, `U-REG-LOGIC` on `module/power-entry`, and `J-PWR-EURO`'s
+5 V pins are no-connects (ADR 0023 point 3).

**The cable-side `CS` pull-up — settled 2026-09-30** (owner: *"Fix the SPI
pull up"*). It had no rail on this board. It is now two pulls, both up: 10 kΩ
to 3V3 at the instrument (`R-CS-PULL-INST`, main board) and `R-PULL-CS`
here, weakened to 100 kΩ and taken to `LOGIC_5V` (`R-CS-PULL-MOD`). Why up and
not down, and the four link states, are on
[`spi-link.md`](../../interfaces/spi-link/spi-link.md), *`CS_MOD`'s two pulls*.

*(Supervision — the deleted frame watchdog, the deleted presence detect, and
what restoring either would cost — is in
[`../link-supervision/link-supervision.md`](../link-supervision/link-supervision.md).
Superseded values and the redraw record are in [`notes.md`](notes.md).)*
