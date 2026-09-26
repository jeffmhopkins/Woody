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
| `U0TXD` (IO43), `U0RXD` (IO44) | in/out | `carrier/carrier` | — | The real-time board's console pair, to `HDR-SERVICE` |
| GND | ref | `carrier/power-entry-instrument` | `dig-gnd-topology` | The `PWR_GND` pour |
| `EN`, `IO0` | in | `carrier/carrier` | — | The Matrix's reset and boot strap, on two conductors of `CBL-MCU-RIBBON` (`J-MCU` pins 24 and 23). Driven from outside the instrument, to ground only |

## The service header

*Connectivity is **[`netlist.yaml`](netlist.yaml)**, not the drawing below.
The drawing is a representation of it and `tools/check-netlist.py` checks the
two agree.*

```
  HDR-SERVICE  1×5, 2.54 mm, on the main board (lid off):

    pin   1            2            3     4     5
          U0TXD(IO43)  U0RXD(IO44)  GND   EN    IO0
          └─ console pair ─┘              └ reset/boot ┘
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

**Nothing in series, because the schematic gives no reason for it.** Both
lines are pulled up on the Matrix and pulled down by its buttons, and the
buttons still work with the wires on. **Drive them to ground only** — a
button, a jumper, or an adapter's open-collector reset circuit. Nothing may
drive them high; a 5 V adapter doing so would push current through `R8`'s
node into `CHIP_PU`. **`EN` has no capacitor on the Matrix** — `R8` and
`Key1` are all that is on the `RESET` net — so its conductor is on the edge of
`CBL-MCU-RIBBON` with only `IO0` beside it (`carrier.md`, *The Matrix and the
umbilical at the tail end*).

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
