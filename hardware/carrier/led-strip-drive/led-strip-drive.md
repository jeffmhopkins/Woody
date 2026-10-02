# LED drive and the LED row — schematic

**Status:** Split out of `carrier.md` 2026-09-21 (Phase B). **The lights are
on the main board since 2026-09-30**
([ADR 0028](../../../docs/decisions/0028-on-board-leds.md)): WS2815B-V1
on the top face, `lighting.led_count` of them on one data line — one in the
tail corner beside the etherCON adapter, where the data arrives (ADR 0028's
amendment of 2026-10-02), then one row down the centreline — in place of
the strip ADR 0016 laid there. The directory keeps its name. What the
circuit used to be is in [`notes.md`](notes.md).

The 74AHCT125 that lifts the ESP32-S3's 3.3 V data to the LEDs, the pull-down
that holds it quiet through reset, the series damping at the driver, and the
LEDs themselves, each with its 100 nF. **The 12 V feed and
`C-STRIP-BULK` are not here** — they belong to
[`power-entry-instrument`](../power-entry-instrument/power-entry-instrument.md).

**The sheet:** [`led-strip-drive.sch.png`](led-strip-drive.sch.png) (KiCad:
[`led-strip-drive.kicad_sch`](led-strip-drive.kicad_sch)) is the SOURCE for
this circuit (ADR 0019): edit it in KiCad 9, and [`netlist.yaml`](netlist.yaml)
is exported from it. The main board's project places it. The ASCII drawing
below is a representation of it.

## Interfaces

Every net that crosses this circuit's boundary. Quantities appear **only** as a
citation into `config/figures.yaml` — this table names nodes, it does not
restate values.

The `Dir` and `Peer` columns are defined once in
[`hardware/README.md`](../../README.md#the-interfaces-table).

| Node | Dir | Peer | Figure | Note |
|---|---|---|---|---|
| IO1 | in | `J-MCU` | — | High-impedance through the bootloader window; `R-LED-PD` is what holds it down in it. IO2 is spare (ADR 0016) |
| 5 V | in | `carrier/power-entry-instrument` | `matrix-led-current` | The buck. The 74AHCT125's rail; TTL thresholds on this rail are why 3.3 V in reads high |
| `INST_POS12` | in | `carrier/power-entry-instrument` (`C-STRIP-BULK` at the row's feed) | `umbilical-current`, `led-row-current` | Every LED's `VDD` and its 100 nF. Since ADR 0027 it is the module's isolated 12 V, through the load switch; on this board it is the node behind `Q-INRUSH`, the hot-plug inrush limiter, so the LEDs' 1.4 µF of `C-LED` `[calc: 14 × 100 nF]` charges on its ramp and not off the plug |
| `PWR_GND` | ref | `carrier/power-entry-instrument` | `dig-gnd-topology` | The LEDs' ground, LED 1's `DIN2`, the spare gates and enables |
| `OE_INST` ×4 | ref | — | — | `U-LVLSHIFT`'s four enables, tied LOW on this board, which is why the pull-down is needed rather than optional. **Not `OE_MOD`**, the module buffer's |

## §5 LED data

*Connectivity is **[`netlist.yaml`](netlist.yaml)**, not this drawing.
The drawing is a representation of it, `tools/check-netlist.py` checks that
the two agree, and where they do not the netlist wins.*


```
  IO1 ──┬──[R-LED-PD 10k]── GND
        │
        └──►│ 74AHCT125 gate A ├──[R-LED-SER 330R]── LED_DI
                                                        │
    LED_DI ──┬──► DIN1 [D-LED-1 WS2815B-V1] DO ── LED_D1 ──┬──► DIN1 [D-LED-2 WS2815B-V1] DO ── LED_D2 ──► ...
             │    DIN2 ◄── GND                             │    DIN2 ◄── LED_DI
             │                                             │
             └─────────────────────────────────────────────┘ (LED_DI also feeds D-LED-2's DIN2)

    LED k:  DIN1 = LED_D(k-1)   (the DO of the LED before)
            DIN2 = LED_D(k-2)   (the DIN1 of the LED before: the backup line)
    D-LED-14's DO drives nothing.
    D-LED-1 is the tail corner's LED; D-LED-2 to D-LED-14 the centreline
    row from its tail end (pcb-geometry.echo 'led', in this order).

  each LED: VDD (pin 2) = +12V, GND (pin 5), pin 1 NC
            [C-LED-1 100nF] ... [C-LED-14 100nF], one at each LED's VDD pin

  gates B, C, D SPARE, inputs tied to GND
  74AHCT125 rail = 5 V (TTL thresholds, so 3.3 V in reads high)
  OE ×4 tied LOW
  [C-DECOUPLE-LED 100nF] at the package
```

**`R-LED-PD` is the fix for a real hole.** ADR 0014's defence against latched
LEDs is "blank the strip and the matrix as the first act at boot" `[repo] 0014`
— a firmware rule that cannot run in the window it matters. On reset GPIO1 is
high-impedance for the bootloader window (order 100–300 ms `[from memory]`),
`OE` is tied low so the buffer is enabled, and an AHCT input floating near its
threshold does not sit still. The buffer squares up whatever it sees into
clean 5 V edges and sends them to every LED in the row, on a 12 V rail. WS281x
has no framing beyond a reset gap, so that is random pixel data — the exact
state the thermal clamp exists to prevent, at the moment no firmware is
running to clamp it. One 0805, and it cannot be added later.

**Decided: fitted, 10 kΩ.** The hole is confirmed on paper: the ESP32-S3's
GPIO1 comes out of reset with its input enabled and **neither weak pull
enabled**, at reset and after it `[ds datasheets/logic/ESP32-S3-datasheet-v2.2.pdf
p.16, the pin table: GPIO1 "IE", where GPIO0 is "WPU, IE"]`. So no test at E1
could make the part unnecessary — a board that happens to show no stray
pixels is a floating input that happened to sit still. The value `[calc]`:
held against the buffer's input leakage, ±1 µA over temperature
`[ds datasheets/logic/SN74AHCT125.pdf p.4, I_I]`, 10 kΩ keeps the input at
10 mV, against a 0.8 V `V_IL` `[same, p.3]`; and IO1 drives it at
3.3 V / 10 kΩ = 0.33 mA when firmware takes the line high, a negligible load.
Anything from about 1 kΩ to a few hundred kΩ would work; 10 kΩ is the value
already on the sheet and a JLC Basic part.

The module page has the same idea for the same reason: `R-SPI-PULL`, six of
them, both sides of its 74AHCT125 `[repo] digital-and-supervision.md`.

### The data level, against the WS2815B-V1

The banked sheet (`datasheets/led/WS2815B-V1.pdf`) gives, at `VDD = 12 V`
`[ds p.3, Electrical Characteristics]`:

| | Min | Max |
|---|---|---|
| `V_IH` (DIN) | 2.7 V | 5.7 V |
| `V_IL` (DIN) | −0.3 V | 1.5 V |

and a logic-input absolute maximum of −0.3 to 5.7 V `[ds p.2]`. **This table's
conditions line says `VDD = 12 V`**, the supply on pin 2, so there is no
second `VDD` to misread here as there was on the old WS2815 V1.1 sheet
(`notes.md`).

- **High:** the 74AHCT125 on 5 V drives ~4.4 V minimum `[repo, the
  U-LVLSHIFT row]` against a 2.7 V `V_IH`: **1.7 V of margin** `[calc: 4.4 −
  2.7]`.
- **The ceiling:** the gate cannot drive above its own 5 V rail, which is
  under the 5.7 V maximum `[calc: 5.7 − 5.0 = 0.7 V]`. **Do not feed the row
  from a 12 V-logic driver**, or from anything whose rail can rise past 5.7 V.
- **Low:** the gate's low output is a few tenths of a volt against 1.5 V.
- **Would 3.3 V drive it directly?** Nominally yes (3.3 > 2.7), but the
  ESP32-S3's `V_OH` at load is 0.8 × VDD `[from memory]`, 2.64 V, **under**
  2.7 V. The buffer stays.

### The backup line

The WS2815B-V1 has two data inputs: `DIN1` (pin 4) and `DIN2` (pin 6)
`[ds p.2]`. Its own sheet draws only the main cascade `[ds p.4]`. The
connection comes from the WS2815's "Recommended application circuit"
`[ds datasheets/led/WS2815.pdf p.4, rendered and read]`:

- **LED 1's `DIN2` goes to GND** (L1 pin 6 to pin 5). The head of the row has
  nothing to lag.
- **Every later LED's `DIN2` is the `DIN1` of the LED before it**, which is
  the `DO` of the LED two back (L2's `BI` is drawn back to the `DI` line ahead
  of L1). The backup line runs one LED behind the main one. If one LED stops
  passing data, the next reads the same frame on `DIN2` and the rest of the
  row keeps working: one dot missing, not the row dark. The switch-over is
  sticky until power-off `[ds WS2815.pdf p.1]`.
- **So `LED_DI` feeds two inputs**, `D-LED-1`'s `DIN1` and `D-LED-2`'s `DIN2`,
  15 pF each `[ds WS2815B-V1.pdf p.3, C_I]`, through `R-LED-SER`.
- **What it does not cover** `[inferred from the scheme]`: two dead LEDs side
  by side, an LED whose `DO` keeps driving garbage (the next one still sees a
  signal on `DIN1`), and an LED that shorts its supply.

**`R-LED-SER`** (330 Ω, at the buffer) damps the fastest edge in the
instrument at its source and protects the buffer's output. The run is short
now, so the case is weaker than it was for a strip; it stays, as one 0805.
**Decided: 330 Ω.** `[calc]` It drives two LED inputs, 15 pF each
`[ds WS2815B-V1.pdf p.3, C_I]`: 330 Ω × 30 pF = 9.9 ns, a 10–90 % edge of
2.2 × 9.9 ≈ 22 ns, a tenth of the shortest pulse the LED must see
(`T0H`, 220 ns minimum `[same, p.3, Data Transfer Time]`), so a few pF of
trace more does not reach it. **Simulated 2026-09-30, re-run 2026-10-02** (`sim/`): with the gate's own
output resistance and the trace added — about 100 mm since the fourteenth
LED, out to the tail corner and back to the row — the edge is about two
thirds slower than this (37 ns nominal, 50 ns at the worst corner), still
under a quarter of `T0H`, and a 220 ns high arrives within a few
nanoseconds of itself at either end of the LED's threshold window — so the
firmware's `T0H` must sit clear of the 220 ns minimum, not on it. Into a shorted data pin it holds the gate to
5 V / 330 Ω ≈ 15 mA, inside its ±25 mA absolute maximum
`[ds datasheets/logic/SN74AHCT125.pdf p.3]`; at 100 Ω, the bottom of the
useful range, a short would be 50 mA, past it.

### Decoupling

**100 nF at every LED, from `VDD` (pin 2) to `GND` (pin 5)** — the vendor's
bypass (`C1 is bypass filter capacitor, its value of 100NF`, `[ds WS2815.pdf
p.4]`). The B-V1's pin 1 is **NC** `[ds WS2815B-V1.pdf p.2]`, not the internal
supply pin the WS2815 V1.1 decoupled there, so the cap goes on the 12 V pin.
`C-STRIP-BULK` is the row's bulk, at its feed end.

### The current

`led-row-current` (owned here, in `config/figures.yaml`) is the row at full
white. Its derivation:

- **The datasheet bounds it.** The B-V1's power consumption is 0.1–0.18 W
  per LED `[ds p.2, Absolute Maximum Ratings]`, so at 12 V a lit LED draws at
  most 15 mA `[calc: 0.18 / 12 = 0.015 A]`, and the fourteen at most 210 mA
  `[calc: 14 × 15]`.
- **Measurements of WS2815 tape agree**: 13.1–13.7 mA per LED at full white
  (`[web https://www.ledlab.io/chips/ws2815]`,
  `[web https://auschristmaslighting.com/threads/power-requirements-for-ws2815-led-strips.14653/]`,
  both via the trade study of 2026-09-29), so ~183 mA for the fourteen
  `[calc: 14 × 13.1]`.
- **Blanked, it is not zero:** under 2 mA quiescent each `[ds p.3]`, ~28 mA
  for the fourteen `[calc: 14 × 2]`, always on.
- **ADR 0014 read "15 mA" as per channel**, 45 mA per LED. On the B-V1 that
  reading would be 0.54 W per LED, three times the datasheet's own maximum
  `[calc: 0.045 × 12]`, so this page does not use it — but it is a reading of
  a document, not a measurement, and **E6 measures the row** (ROADMAP).

**Against the supply** (ADR 0027): the 12 V reaches this row from the module's
isolated converter through the load switch. The whole row at full white on
top of `umbilical-current` (which already carries a lit share of the lights)
is still more than 0.2 A under the load switch's minimum trip
(`module/umbilical-load-switch`), and the converter's own limit is above that
trip (ADR 0027 point 2). A latched full-white row after a brownout — ADR
0014's failure — now sits on 12 V at a fifth of an amp, not on the MCU's 5 V
rail, so it cannot fold the buck back and stop blank-at-boot from running.

---

## Component table

| Ref | Value | Job | Confidence |
|---|---|---|---|
| `U-LVLSHIFT` | 74AHCT125 SOIC-14 | LED data, 5 V rail. One gate used | `[repo]`, `[ds]` |
| **`R-LED-PD`** | **10 kΩ** | **Holds the row's data low through reset** | `[ds]`, `[calc]` |
| **`R-LED-SER`** | **330 Ω** | **Damps the data line at its source** | `[ds]`, `[calc]` |
| `D-LED-1` … `D-LED-14` | WS2815B-V1 (LCSC C5446699) | `D-LED-1` in the tail corner, then the row: 12 V, backup-chained. **The body's chamfer marks pin 1 (NC)**, as the sheet's numbered pin drawing places it (footprint `woody:LED_WS2815B-V1_PLCC6_5.4x5.0mm_P1.6mm`, `hardware/lib/README.md`) | `[ds]` |
| `C-LED-1` … `C-LED-14` | 100 nF X7R 50 V 0805 | One at each LED's `VDD` | `[ds]` |

Where the LEDs sit is the body CAD's: `config/body.yaml` `lighting.*` and the
`led` records in `mechanical/export/pcb-geometry.echo` (numbered along the data
line: `LED1` the corner's), checked by `mechanical/drc.echo` *"LED row on the
main board"* and *"LED in the tail corner clear of its neighbours"*.

### The LED in the tail corner

Added 2026-10-02 (the owner: "Add it"; ADR 0028's amendment, after ADR 0021's
study of the full-width tail). The row cannot light the tail's near side: the
regulator block, 12.5 mm tall on that side in front of `J-MCU`, shadows it.
**It is first on the data line**, because the data arrives at the tail:
`R-LED-SER` → `D-LED-1` (the corner) → `D-LED-2` (the row's tail end) → … The
backup line is ADR 0028 point 5 unchanged: `D-LED-1`'s `DIN2` to GND, and
`D-LED-2`'s `DIN2` from the feed, `LED_DI`. So `R-LED-SER` still drives two
inputs and the edge derivation above stands; the feed's trace is longer, about
50 mm from `R-LED-SER` to the corner and 55 mm back along `LED_D1` to the row
`[from ADR 0021's study]`: ~12 pF of trace `[from memory, ~1.2 pF/cm over a
plane]` beside the inputs' 30 pF, which the simulation above already carries.
It is about six times nearer the near side than the row is to either side, so
firmware scales it down (`firmware/README.md`, *The lights*).
