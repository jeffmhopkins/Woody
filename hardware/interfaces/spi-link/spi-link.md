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

The buffer's supply is the module's own `LOGIC_5V` (`U-REG-LOGIC`,
`module/power-entry`); the bus +5 V is not used (owner, 2026-09-30).

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

The `Dir` and `Peer` columns are defined once in
[`hardware/README.md`](../../README.md#the-interfaces-table).

| Node | End | Dir | Peer | Figure | Note |
|---|---|---|---|---|---|
| `SCLK` | instrument → module | out | `J-MCU` IO35 → `module/digital-and-supervision` | `umbilical-pinmap`, `spi-series-r` | On `J-UMB`. Series resistor at the driving end, pulled **down** on both sides of the buffer. Shares a pair with `MOSI`. **Not `SCLK_DAC`**, which is the buffer's output |
| `MOSI` | instrument → module | out | `J-MCU` IO36 → `module/digital-and-supervision` | `umbilical-pinmap`, `spi-series-r` | On `J-UMB`. Pulled **down**, both sides. Sampled only on a `SCLK` edge, which is why it shares that pair |
| `CS_MOD` | instrument → module | out | `J-MCU` IO34 → `module/digital-and-supervision` | `umbilical-pinmap`, `spi-series-r` | On `J-UMB`. Pulled **up at both ends of the cable** — `R-CS-PULL-INST` to 3V3 on the main board, `R-CS-PULL-MOD` to `LOGIC_5V` at the module (*`CS_MOD`'s two pulls*, below) — and on the DAC side of the buffer. The one that must not glitch. Shares a pair with `DIG_GND`. **Not `CS_ADC`**, the MCP3202's, which never leaves the carrier |
| `DIG_GND` | instrument ↔ module | ref | `carrier/carrier` (its `PWR_GND`, at `J-UMB`) ↔ `module/power-entry` | `umbilical-pinmap`, `dig-gnd-topology` | On `J-UMB` pin 8. `CS_MOD`'s return partner. **Tied to the main board's ground at `J-UMB`** (ADR 0018). Where it ties at the **module** end is `dig-gnd-topology` |
| `U-TVS-SPI` | instrument | — | — | — | This circuit's own part: on all three signals, to `PWR_GND`, at the connector |
| `J-UMBILICAL-INST`, `PCB-UMB-ADAPTER`, `J-UMB` | instrument | — | — | `umbilical-pinmap` | This circuit's own parts: the instrument's etherCON, the adapter board it is soldered to, and the header that joins the adapter to the main board. See *The instrument's connector*, below |
| `MISO` | instrument | — | `carrier/breath-adc` | — | IO37 is the MCP3202's `DOUT` and **never leaves the board**. ADR 0004 deleted `MISO` from the umbilical, which is why nothing reads the DAC back |
| SPI2 host | instrument | — | `carrier/breath-adc`, `module/dac8568` | `loop-budget` | One host, two devices, two clocks. The ADC's limit is a fact about a part on the instrument board that constrains the link's budget |
| `SCLK_DAC`, `DIN`, `SYNC` | module | — | `module/digital-and-supervision` → `module/dac8568` | — | **Not sourced here.** The 74AHCT125 is on `module/digital-and-supervision`, which owns that row; these three are a module-board net and do not cross the umbilical. The DAC-side three of the six `R-SPI-PULL` — this circuit's `bom.csv` — sit on them |
| `DAC AVDD` | module | in | `module/power-entry` | `dac-rail` | What the DAC-side `CS` pull returns to, **not** bus `+5V`: on the bus rail a reversed ribbon reaches the DAC's `SYNC` pin. See this circuit's `bom.csv` |
| `LOGIC_5V` | module | in | `module/power-entry` → `module/digital-and-supervision` | — | The module's own 5 V (`U-REG-LOGIC`): the 74AHCT125's supply, and the top of `R-CS-PULL-MOD` — the rail of the part that pull holds. The bus +5 V is not used |
| `OE_MOD` ×4 | module | — | `module/digital-and-supervision` | — | The module buffer's four enables, tied to `GND` and permanently enabled. On that circuit's part, so they reach nothing here; the circuit that used to gate them, `module/link-supervision`, is not fitted. **Not `OE_INST`** |

## The sheet, and which board places what

**The source is [`spi-link.kicad_sch`](spi-link.kicad_sch)** (ADR 0019;
render [`spi-link.sch.png`](spi-link.sch.png)). [`netlist.yaml`](netlist.yaml)
is exported from it (`python3 tools/kicad.py export hardware/interfaces/spi-link`)
and must not be edited. It was first written from the hand-written netlist
and compared with it part by part and net by net: no change.

**No board places this sheet, and none can as it stands.** KiCad places a
sheet whole, and this one is three connectors on three boards joined by a
cable that is not a part. Each board draws its own part and wires it pin N
to the net this sheet puts pin N on:

| Part on this sheet | BOM row | Board | On that board today |
|---|---|---|---|
| `J-UMB-INST` | `J-UMBILICAL-INST` | `hardware/boards/umb-adapter` | `J1` |
| `J-UMB` | `J-UMB` | `hardware/boards/main-board` (its tails) **and** `umb-adapter` (its posts): one part, bought and fitted once | main board `J6` (`Assembly` hand); adapter `J2` (`Assembly` none) |
| `J-UMB-MOD` | `J-UMBILICAL` (`module/power-entry`'s row) | `hardware/boards/module-main` | `J3` |
| `CABLE-UMB`, the adapter's tracks | — | no board: straight conductors, not parts | — |

**`tools/kicad.py check` holds every board's connector to this sheet**, pin
by pin and by net name: the main board's `J6` and the adapter's `J2` against
`J-UMB`, the adapter's `J1` against `J-UMB-INST`, and the module main board's
etherCON against `J-UMB-MOD` — the same way it holds `J-CHAIN` to the key
chain's sheet. A pin moved on a board's sheet is reported by name.

## The instrument's connector — the etherCON on its adapter, and `J-UMB`

*Added with ADR 0017 and rewritten with ADR 0021; not part of the verbatim
consolidation below.*

The etherCON at the instrument end is `J-UMBILICAL-INST`, an NE8FAV (`J-UMB-INST`
in [`netlist.yaml`](netlist.yaml)). It sits behind the tail cap and is
soldered to a small board of its own, `PCB-UMB-ADAPTER`, whose tracks run its
pin N to pin N of **`J-UMB`**. `J-UMB` is a right-angle pin header soldered into
both the adapter and a tongue of the main board. There is no cable and no
mated contact inside the body. So:

- **"`J-UMB` pin N" on every instrument page is the main board's end of the
  umbilical, and the same conductor as the etherCON's pin N.** The pin map is
  `umbilical-pinmap` at every connector in the chain, and the adapter has
  none of its own to get wrong: eight straight tracks, the same argument this
  circuit makes for `CABLE-UMB`.
- **The pairs stay side by side on the adapter.** The pairing is the argument
  on this page, and the adapter's few millimetres are the last stretch of the
  same line.
- **The clamps drawn "at the connector"** — `U-TVS-SPI` here, `D-REVSHUNT`
  and `D-TVS-PWR` on
  [`power-entry-instrument`](../../carrier/power-entry-instrument/power-entry-instrument.md) —
  are on the main board at `J-UMB`, not on the adapter.
- **The +12 V and `PWR_GND` path is rated above the module's current-limit
  trip** (`R-ILIM`), not only `umbilical-current`. A hard short folds the
  limit back (the `R-ILIM` row gives the floor), so the worst case is an
  overload just under the trip, which the load switch carries indefinitely.
  The etherCON's own contacts are the limit here, at the rating in
  `J-UMBILICAL-INST`'s row; `J-UMB`'s header pins carry more.
- **`J-UMB` pin 8, `DIG_GND`, is the main board's ground at the instrument
  end** (owner, 2026-09-26,
  [ADR 0018](../../../docs/decisions/0018-main-board-wiring-decisions.md)): a
  short, wide connection from the pin to `PWR_GND` at `J-UMB`, copper rather
  than a bought part. `carrier/carrier` makes it with `NT-DIG`, a KiCad net
  tie between its `DIG_GND` and `PWR_GND` nets; the name is kept because at
  the module end conductor 8 is its own net.
  **The layout rule that makes it a return:** route `SCLK`, `MOSI` and
  `CS_MOD` from the MCU side of `J-MCU`, through `R-SPI-SER`, to `J-UMB` over
  unbroken ground, so each edge's return runs under its trace to pin 8 and
  the pour; and keep `AGND_SENSE` (pin 2, the analog star's sense leg) off
  this return — it is a signal, not a ground. The module end is
  `dig-gnd-topology`.

**Netlisted here, beside both etherCONs**, because it carries this circuit's
pin map and all eight of its nets: each net is `J-UMB`, `J-UMB-INST` and
`J-UMB-MOD` pin N, and the carrier's nets reach it as this circuit's ports.
`J-UMB`'s part is chosen (the row in this circuit's [`bom.csv`](bom.csv));
its drawing settles the insulator in `config/body.yaml` `boards.umb_joint_*`.

## Simulated — `sim/`, 2026-09-30

The three lines as netlisted, with the cable as lossy transmission lines from
a banked Cat5e datasheet (`sim/README.md`). Two results contradict this page,
and both are E11's to confirm on the real cable:

- **`CS_MOD`'s falling edge re-enters the 0.8–2.0 V band**
  (`cs-fall-reentry`). The rising edge's first step, below, is the easy one:
  the source (`R-SPI-SER` and the pad) is above the line's 100 Ω, so the
  falling edge's first step lands only just under `V_IL`, and `U-TVS-SPI`'s
  capacitance on the line side of `R-SPI-SER` reflects the returning wave back
  up through it. A what-if with `U-TVS-SPI` on the pad side of `R-SPI-SER` and
  82 Ω there is clean at every corner. **A decision for the owner**, not
  made here: it moves a protection part.
- **`SCLK` and `MOSI` in one pair couple, and where it lands is the DAC's
  sampling edge** (`spi-pair-crosstalk`). The pair is two coupled lines over a
  return on other pairs; each `SCLK` edge puts a round-trip-long glitch on a
  static `MOSI` at the module that crosses the buffer's thresholds at the
  worst corner of every common-mode impedance swept, including on the falling
  edge the DAC clocks `DIN` on `[ds DAC8568CIPW.pdf p.6]`. When `MOSI` falls as
  `SCLK` rises, `SCLK`'s edge crawls through the band in round-trip steps and
  can swing back. The even-mode impedance is in no datasheet, so the size is
  bracketed, not known. Nothing in the netlist closes it outright: the what-if
  above plus a capacitor at each receiver narrows it to tens of millivolts at
  the top of the range. **A decision for the owner**: a receiver with
  hysteresis, or measure first at E11.

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
| **SPI3** | The key chain's four `U-KEYS` registers (SN74HCS165) alone, because `QH` is always driven (ADR 0001) | **1 MHz, and not much more** — the serial path crosses both key-board ribbons out and back and runs the main board's length. Each hop's `QH` → `SER` is data sampled a whole clock period after it changes, into a Schmitt input, so a hop need not be a lumped load (it is not one, by `key-chain-loom.md`'s own length rule: `key-register.md`); the edge-sensitive `SCK` and `SH/LD` are `R-CHAIN-SER`'s, scoped at E14 `[repo] 0001, key-chain-loom.md`. **SPI mode 2 (CPOL 1, CPHA 0).** The register shows `H` on `QH` from the load, before any clock, and shifts on `CLK`↑ `[datasheets/logic/SN74HCS165-ti-scls828a.pdf p.11 §8.1, p.13 Table 8-1]`, so the MCU must take its first sample before the first rising edge or on it. Mode 2 samples on each falling edge, half a period after the shift, with no dependence on the register's timing beyond its maximum `tpd` `[calc]`. Modes 0 and 3 sample on the rising edge that shifts, and hold only on the register's unpublished minimum `tpd`; mode 1 samples after the first shift and loses bit 0, which the marker reports as a framing error (ADR 0001). A firmware line, written nowhere else |

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
             (+ one register CLK→QH delay plus flight: each hop is
              re-sampled on the next clock, so the delays do not add; the
              last register's is 18–45 ns max over temperature at 4.5–2 V,
              SN74HCS165 datasheet p.7, against mode 2's 500 ns — noise)
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

*Simulated 2026-09-30 and not borne out: the coupling lands with the edge the
DAC samples on (`spi-pair-crosstalk`, *Simulated* above).*

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

## `CS_MOD`'s two pulls — settled 2026-09-30

The owner, 2026-09-30: *"Fix the SPI pull up."* The cable-side `CS` pull-up
was drawn on the module sheet with its top end on no net, because the only
rail its row allowed — 3V3 — exists only at the instrument. It is now **two
resistors, one at each end of the cable, both pulling up**:

| Part | Where | To | Value |
|---|---|---|---|
| `R-CS-PULL-INST` | main board (`carrier/carrier`), `IO34` beside `J-MCU` pins 13/14, on the MCU side of `R-SPI-SER-CS` | `DEV_3V3` | 10 kΩ |
| `R-CS-PULL-MOD` (`R-PULL-CS` on the sheet) | module main board (`module/digital-and-supervision`), at the buffer's `3A` | `LOGIC_5V` | 100 kΩ |

**Why up at the module, not the proposed weak pull-down.** The 74AHCT125 does
not invert: `3A` drives `3Y`, which is the DAC's `SYNC`, active low. A
pull-down at the module would hold `SYNC` **low — selected —** whenever the
umbilical is out, leaving the DAC's shift register listening to whatever
reaches `SCLK` ("When `SYNC` goes low, it enables the input shift register,
and data are sampled on subsequent falling clock edges" `[ds DAC8568CIPW.pdf
p.6]`). Pulled up, an unplugged module's DAC ignores `SCLK` entirely. The
pull-down's one advantage — no current into an unpowered instrument — is kept
by making the module's pull-up **weak** instead.

**The four states of the link** `[calc]`, from `V_IH` 2.0 V / `V_IL` 0.8 V and
±1 µA input current at the buffer `[ds SN74AHCT125.pdf p.3, p.4]`:

| State | `CS_MOD` at the buffer | `SYNC` | Current into the instrument |
|---|---|---|---|
| Umbilical out, module on | 5 V − 1 µA × 100 kΩ ≥ **4.9 V** | high, deselected | — |
| Plugged in, instrument off (toggle off: its 3V3 is dead, ~0 V) | 5 V × 10k / 110k = **0.45 V** | low | 5 V / 110 kΩ = **45 µA**, into the dead rail through the 10 kΩ — the node is below the ESP32 pad's clamp, so almost none through the clamp |
| Instrument powered, ESP32 in reset or booting (`IO34` has no pull at reset, input-enabled only `[ds ESP32-S3-datasheet-v2.2.pdf p.17]`) | (3.3/10k + 5/100k) / (1/10k + 1/100k) = **3.45 V** | high, deselected | ≤ (5 − 3.3) / 100 kΩ = **17 µA** into the pad clamp |
| Running | driven by `IO34`, push-pull | framed by firmware | ≤ 50 µA extra load on the pin |

The second row is the one the old row was written about: a 10 kΩ pull-up to
5 V at the module drove 430 µA through the ESP32's clamp and parked the node
near 0.7 V. At 100 kΩ it is a tenth of that and goes into the rail, not the
clamp. That state reads **selected**, and is harmless: `SCLK` is held low at
both ends so there is no edge to shift, and when the instrument powers up its
3V3 pulls `CS_MOD` high, and a `SYNC` rising edge before the 31st clock
"acts as an interrupt, and the write sequence is ignored" `[ds DAC8568CIPW.pdf
p.6]` — the first frame the firmware sends starts clean.

**`GPIO34` is not a strapping pin** — those are GPIO0, 3, 45 and 46
`[ds ESP32-S3-datasheet-v2.2.pdf p.26]` — so the instrument's pull-up changes
no boot mode. It is on the MCU side of `R-SPI-SER-CS` so the source
termination the cable sees is unchanged, and it sits at `J-MCU`, where pin 13
(3V3) is beside pin 14 (`IO34`).
