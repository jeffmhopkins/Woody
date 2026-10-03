# Service UART — schematic

**Status:** Rewritten 2026-09-26, when the display board was removed
(ADR 0015). This page was the display loom *and* the service header; the
loom went with the display board, and the service header is what is left.
The page as it was is in git.

`HDR-SERVICE`, a 1×5 header on the main board, reached with the lid off —
there is no service cover since 2026-09-26 (ADR 0009): the real-time board's
console pair, a ground, and its `EN` and `IO0` (owner, 2026-09-26,
[ADR 0018](../../../docs/decisions/0018-main-board-wiring-decisions.md)).

## Interfaces

Every net that crosses this circuit's boundary. Quantities appear **only** as a
citation into `config/figures.yaml` — this table names nodes, it does not
restate values.

The `Dir` and `Peer` columns are defined once in
[`hardware/README.md`](../../README.md#the-interfaces-table).

| Node | Dir | Peer | Figure | Note |
|---|---|---|---|---|
| `U0TXD` (IO43), `U0RXD` (IO44) | in/out | `carrier/carrier` | — | The real-time board's console pair, to `HDR-SERVICE`; `U0TXD` through `R-TXD-SER` |
| GND | ref | `carrier/power-entry-instrument` | `dig-gnd-topology` | The `PWR_GND` pour |
| `EN`, `IO0` | in | `carrier/carrier` | — | The Matrix's reset and boot strap, on two conductors of `CBL-MCU-RIBBON` (`J-MCU` pins 24 and 23). Driven from outside the instrument, to ground only. `C-EN` on `EN` |

## The service header

*Connectivity is **[`netlist.yaml`](netlist.yaml)**, not the drawing below.
The drawing is a representation of it and `tools/check-netlist.py` checks the
two agree.*

```
  HDR-SERVICE  1×5, 2.54 mm, on the main board (lid off):

    pin   1            2            3     4     5
          TXD_HDR      U0RXD(IO44)  GND   EN    IO0
          └─ console pair ─┘              └ reset/boot ┘

  U0TXD(IO43) ──[R-TXD-SER 499R 1%]── TXD_HDR ── pin 1     (at J-MCU pin 22)
  EN ──┬── pin 4
       └──[C-EN 1uF]── GND                                (at J-MCU pin 24)
```

**The ground is pin 3, between the console pair and the control pair**, so a
UART edge has a ground beside it before it reaches `EN`.

**Where `EN` and `IO0` come from.** Neither is on the ESP32-S3-Matrix's pad
rows, so their conductors are soldered to its buttons
`[repo] datasheets/mechanical/WAVESHARE-ESP32-S3-MATRIX-SCHEMATIC.pdf`:

```
   Matrix 3V3 ── R8 10k ──┬── RESET = EN (CHIP_PU)
                          ├── Key1 ── GND
                          └── ribbon conductor 24 ─► J-MCU 24 ─► HDR-SERVICE 4

   Matrix 3V3 ── R10 10k ─┬── IO0 (GPIO0)
                          ├── Key2 (BOOT) ── GND
                          └── ribbon conductor 23 ─► J-MCU 23 ─► HDR-SERVICE 5
```

Each wire goes on the button terminal on the resistor side, **not** the one
on `GND`: with a meter, the right terminal reads about 10 kΩ to the 3V3 pad
and the wrong one 0 Ω to the `GND` pad. The drawing's resistors are the
Matrix's own, not rows in this BOM.

**Nothing in series on `EN` or `IO0`.** Both
lines are pulled up on the Matrix and pulled down by its buttons, and the
buttons still work with the wires on. **Drive them to ground only** — a
button, a jumper, or an adapter's open-collector reset circuit. Nothing may
drive them high; a 5 V adapter doing so would push current through `R8`'s
node into `CHIP_PU`. **`EN` has no capacitor on the Matrix** — `R8` and
`Key1` are all that is on the `RESET` net — so its conductor is on the edge of
`CBL-MCU-RIBBON` with only `IO0` beside it (`carrier.md`, *The Matrix and the
umbilical at the tail end*).

**`C-EN` is the capacitor the Matrix leaves out** (#14 A2, #11 F7). Espressif
asks for *"an RC delay circuit at the CHIP_PU pin … usually R = 10 kΩ and C =
1 μF"*, and for the `CHIP_PU` trace to be short
`[ds logic/ESP-HARDWARE-DESIGN-GUIDELINES-ESP32S3.pdf p.11]`. `R8` is the R;
this board's 1 µF at `J-MCU` pin 24 is the C. With it `EN` rises with
τ = 10 kΩ × 1 µF = 10 ms `[calc]` after the 3V3 rail, well past the 50 µs
`t_STBL` `[ds ESP32-S3-datasheet-v2.2.pdf Table 2-13 p.30]`, and a spike
coupled onto the long conductor meets 1 µF instead of a bare 10 kΩ node.
`Key1`, a jumper or an open-collector reset discharges it in microseconds, so
the recovery procedure below is unchanged. It sits at the board end of the
ribbon, not at the pin: the pin is on the Matrix, which carries no such part.
(Espressif's warning against large capacitance is about `GPIO0`, which has
none.)

**`R-TXD-SER` is Espressif's other ask**: *"connect a 499 Ω series resistor
to the U0TXD line to suppress harmonics"* (same document, p.16, *UART*). It is
the first part on `IO43` after the ribbon, and it limits the current a
discharge to header pin 1 can push back into the pin. `U0RXD` is an input
and is not in that guidance.

**In-place recovery is decided: yes** (ADR 0018). The recovery ladder is
USB-Serial-JTAG through the tail USB-C receptacle (`CBL-USB-EXT`) first, a
reflash over the same port second, and this header third — which now reaches
download mode without taking the Matrix out: hold `IO0` low, pulse `EN` low,
and the ROM loader answers on the console pair. The procedure is
`firmware/README.md`'s. A corrupted bootloader no longer means a bench trip.

---

## Component table

| Ref | Value | Job | Confidence |
|---|---|---|---|
| `HDR-SERVICE` | **1×5**, 2.54 mm | The real-time board's UART pair, GND, `EN` and `IO0` | `[repo] bom.csv`; decided (ADR 0018) |
| `R-TXD-SER` | 499 Ω 1 % | In series with `U0TXD`, at `J-MCU` pin 22 | `[ds]` Espressif guidelines p.16 |
| `C-EN` | 1 µF X7R | `EN` to ground at `J-MCU` pin 24: the C of `CHIP_PU`'s RC, with the Matrix's `R8` | `[ds]` Espressif guidelines p.11; ESP32-S3 datasheet p.30 |
