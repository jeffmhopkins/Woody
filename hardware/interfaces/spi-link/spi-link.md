# SPI link — carrier egress to the module's buffer

**Status:** Consolidated 2026-09-21 from the two pages that described one
circuit from opposite ends of the umbilical — `hardware/carrier/carrier.md` §4
and `hardware/module/digital-and-supervision/digital-and-supervision.md`.
Everything below the `## Interfaces` table was **moved verbatim**: nothing was
reworded, no value was edited and no open question was closed.

Three conductors and a return leave the carrier, cross 2 m of Cat5 and arrive
at a 74AHCT125 with no hysteresis. The series resistors are chosen at the
driving end against a threshold at the receiving end, the pulls exist on both
sides of that buffer, and the pin pairing is an argument about what couples
into what inside the cable — none of which can be read from one end alone.

The bus +5 V rail that supplies the buffer is still an open question, and it
stayed on the module page with the rail rather than coming here with the part —
see the `## Interfaces` row for it.

**The carrier end's drawing is not redrawn here.** It is in
[`carrier.md`](../../carrier/carrier.md) §4 and also carries the MCP3202's
board-local `MISO` and `CS`, which never leave that board; dividing it would
mean redrawing it. The module end's drawing is in
[`digital-and-supervision.md`](../../module/digital-and-supervision/digital-and-supervision.md)
and stays there for the same reason — it is the record of a redraw that page
owns, and the note about the gap where the DAC box was belongs with it.

## Interfaces

Every net that crosses this circuit's boundary, and **which end of the
umbilical each one is on**. Quantities appear **only** as a citation into
`config/figures.yaml` — this table names nodes, it does not restate values.

| Node | End | Dir | Peer | Figure | Note |
|---|---|---|---|---|---|
| `SCLK` (`J-UMB` pin 4) | instrument → module | out | `HDR-DEV` IO35 → `74AHCT125` | `umbilical-pinmap`, `spi-series-r` | Series resistor at the driving end, pulled **down** on both sides of the buffer. Shares a pair with `MOSI` |
| `MOSI` (`J-UMB` pin 5) | instrument → module | out | `HDR-DEV` IO36 → `74AHCT125` | `umbilical-pinmap`, `spi-series-r` | Pulled **down**, both sides. Sampled only on a `SCLK` edge, which is why it shares that pair |
| `CS` (`J-UMB` pin 7) | instrument → module | out | `HDR-DEV` IO34 → `74AHCT125` | `umbilical-pinmap`, `spi-series-r` | Pulled **up**, both sides. The one that must not glitch. Shares a pair with `DIG_GND` |
| `DIG_GND` (`J-UMB` pin 8) | instrument ↔ module | ref | `carrier/carrier.md` ↔ `module/power-entry` | `umbilical-pinmap`, `dig-gnd-topology` | `CS`'s return partner. Where it ties is the disputed figure, not a fact either end settles |
| `U-TVS-SPI` | instrument | — | `carrier/carrier.md` component table | — | On all three signals, to `PWR_GND`, at the connector |
| `MISO` | instrument | — | `carrier/breath-adc` | — | IO37 is the MCP3202's `DOUT` and **never leaves the board**. ADR 0004 deleted `MISO` from the umbilical, which is why nothing reads the DAC back |
| SPI2 host | instrument | — | `carrier/breath-adc`, `module/dac8568` | `loop-budget` | One host, two devices, two clocks. The ADC's limit is a fact about a part on the instrument board that constrains the link's budget |
| `SCLK`, `DIN`, `SYNC` | module | out | `module/dac8568` | — | Buffer outputs. The DAC-side three of the six `R-SPI-PULL` sit on these |
| bus +5 V | module | in | Eurorack bus header | — | Supplies the 74AHCT125 and nothing else. **Open**, and the item stayed on [`digital-and-supervision.md`](../../module/digital-and-supervision/digital-and-supervision.md) because it is a rail and connector question about that board, not about this link |
| `OE` ×4 | module | ref | `module/link-supervision` | — | Tied to `GND`, permanently enabled. The circuit that used to gate it is not fitted |

---

## From the instrument end — `carrier.md` §4

*Moved verbatim from `hardware/carrier/carrier.md` §4, 2026-09-21. "This page"
throughout means `carrier.md` as it stood before the move, and the drawing it
names is still in [`carrier.md`](../../carrier/carrier.md) §4.*

**All three are `R-SPI-SER`, and the value is 100 Ω.** The refdes matters:
this page previously drew `R-SCLK-SER`, `R-MOSI-SER` and `R-CS-SER`, **none
of which exist in `bom.csv`**, while the BOM carries `R-SPI-SER` at qty 3
used by no schematic. Same three parts, two naming schemes, neither side
aware of the other. (This page also claimed "only `R-MOSI-SER` reached the
BOM, qty 1" — it is not in the BOM at all.)

**The value is 100 Ω, not 220, and the old derivation used the wrong
model.** Two m of Cat5 is a **100 Ω transmission line**: the round trip is
~20 ns against 2–5 ns edges, so this is a reflection problem, not an RC
corner. Three reviewers agreed on that and two of them computed what 220 Ω
costs `[calc]`:

| Source R | First step at the far end | vs `V_IH` 2.0 V |
|---|---|---|
| **220 Ω** | **1.83–1.86 V** | **below threshold, dwelling ~20 ns per edge in the forbidden band** |
| 100 Ω | **2.75 V** | clean single step |
| 68 Ω | 3.25 V | clean, but **48 mA fault current against a 40 mA pad spec** |

**100 Ω** is the answer: it resolves in one transit and draws 33 mA into a
clamp. 68 Ω is electrically ideal and exceeds what the pin can source.
(ADR 0004's old "7.9 MHz corner" was the figure for 100 Ω all along, quoted
against 220 Ω — the schematic review caught that separately.)

The receiving end has no hysteresis, which is what makes the dwell matter:
a 74AHCT125 given 20 ns in its indeterminate band on every clock edge is
being asked to guess.

### The two SPI hosts, and what claims them

| Host | Devices | Clock |
|---|---|---|
| **SPI2** | DAC8568 down the umbilical, **and** MCP3202 on this board | **2 MHz for the DAC, 900 kHz for the ADC — not one clock** |
| **SPI3** | 74HC165 chain alone, because `QH` is always driven (ADR 0001) | **1 MHz, and not much more** — the chain crosses four connectors and ~265 mm of loom, and HC's slow edges are what keep that a lumped load `[repo] 0001` |

> **The MCP3202 cannot run at 2 MHz.** `[repo, verified]` against Microchip
> DS21034F, now at `datasheets/analog/MCP3202-CI-SN.pdf`. The Timing
> Parameters table gives `fCLK` max = **1.8 MHz at VDD = 5 V** and **0.9 MHz at
> VDD = 2.7 V**. There is no 3.3 V row. ADR 0003, ADR 0004,
> `latency-budget.md` and `power-entry.md` all say "SPI2 at 2 MHz", and ADR 0004
> explicitly says that leaves room "for the MCP3202 sharing the host" `[repo]`.
>
> **0.9 MHz is safer than this page claimed, not shakier.** Two documents called
> it "an interpolation from a search summary". It is not an interpolation at
> all — it is the datasheet's *guaranteed maximum at 2.7 V*, so applying it at
> 3.3 V is strictly conservative. A straight-line interpolation to 3.3 V would
> give ≈1.14 MHz, so there is ~25 % of headroom the design is not claiming.
> Both `fCLK` rows carry Note 2: established by characterisation, not 100 %
> tested.
>
> **And there is a minimum nobody had.** §6.2: the sample capacitor holds
> charge for at least 1.2 ms at 85 °C, so the end of the sample period to the
> last data bit must fit inside that — an effective **`fCLK` ≥ ~10 kHz**. Not
> binding at 900 kHz, but it forecloses "slow the ADC down" as a way to buy
> loop time.
>
> ESP-IDF sets `clock_speed_hz` per *device* on a shared host, so this is a
> firmware line and not a part change. **It is written nowhere.**

**Loop budget with the ADC costed properly** `[calc]` — ADR 0004's version left
it out:

```
SPI2  DAC    6 × 32 bits @ 2.0 MHz =  96.0 µs
SPI2  ADC    24 clocks    @ 0.9 MHz =  26.7 µs
SPI2  total                         = 122.7 µs of 250 µs → 49 %
SPI3  keys   32 bits      @ 1.0 MHz =  32.0 µs, concurrent → 13 %
             (+ four HC165 propagation delays, tens of ns each — noise)
```

**SPI2 cannot use IO_MUX and does not need to.** The S3's FSPI IO_MUX pins are
GPIO9–14 `[from memory]`, and the board spends GPIO10–13 on the QMI8658C and
GPIO14 on the matrix `[board-def] circuitpython .../pins.c`. SPI2 on
GPIO35/36/37 therefore routes through the GPIO matrix, capped around 40 MHz
rather than 80 `[from memory]`. Irrelevant at 2 MHz; recorded so it is not
rediscovered as a problem.

---

## From the module end — `digital-and-supervision.md`

*Moved verbatim from
[`digital-and-supervision.md`](../../module/digital-and-supervision/digital-and-supervision.md),
2026-09-21. The blockquote below sat under that page's "The pin map, and why
the pairing is what it is", which keeps its heading and its own provenance
line; "this page" in it means that page as it stood before the move.*

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
