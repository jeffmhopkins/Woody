# Service UART — schematic

**Status:** Rewritten 2026-09-26, when the display board was removed
(ADR 0015), and again 2026-10-03, when the owner chose to program the
Matrix over its own USB-C only. This page was the display loom *and* the
service header; the loom went with the display board, and the service
header is what is left. The page as it was is in git.

`HDR-SERVICE`, a 1×3 header on the main board, reached with the lid off —
there is no service cover since 2026-09-26 (ADR 0009): the real-time board's
console pair and a ground (owner, 2026-09-26,
[ADR 0018](../../../docs/decisions/0018-main-board-wiring-decisions.md)).
It also carried the Matrix's `EN` and `IO0` until the owner's choice of
2026-10-03 — *"Program over USB only"*
([ADR 0021, amendment 2026-10-03](../../../docs/decisions/0021-pcb-mount-ethercon.md)).

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

## The service header

*Connectivity is **[`netlist.yaml`](netlist.yaml)**, not the drawing below.
The drawing is a representation of it and `tools/check-netlist.py` checks the
two agree.*

```
  HDR-SERVICE  1×3, 2.54 mm, on the main board (lid off):

    pin   1            2            3
          TXD_HDR      U0RXD(IO44)  GND
          └─ console pair ─┘

  U0TXD(IO43) ──[R-TXD-SER 499R 1%]── TXD_HDR ── pin 1     (at J-MCU pin 22)
```

**`R-TXD-SER` is Espressif's ask**: *"connect a 499 Ω series resistor
to the U0TXD line to suppress harmonics"*
`[ds logic/ESP-HARDWARE-DESIGN-GUIDELINES-ESP32S3.pdf p.16, UART]`. It is
the first part on `IO43` after the ribbon, and it limits the current a
discharge to header pin 1 can push back into the pin. `U0RXD` is an input
and is not in that guidance. Both are on the Matrix's IO33..RX pad row, so
they reach this header through the carrier's `HDR-MATRIX`, `CBL-MCU-RIBBON`
and `J-MCU` like every other pad-row line.

## Programming and recovery: over the Matrix's USB-C only

The owner's choice of 2026-10-03, *"Program over USB only"*: the Matrix is
programmed and recovered through its own USB-C — USB-Serial-JTAG through the
tail receptacle (`CBL-USB-EXT`) — and, when that fails, by forcing download
mode with its own `BOOT` and `RESET` buttons with the lid off (they are on
its back, under the carrier's notch side, and reachable once the lid is
lifted). The procedure is `firmware/README.md`'s. **`EN` and `IO0` are no
longer wired out**: no button wires, no ribbon conductors (`J-MCU` pins 23
and 24 are on no net), no header pins.

**`EN` keeps only the Matrix's own `R8`** — 10 kΩ to its 3V3 and `Key1` to
`GND`, no capacitor `[repo] datasheets/mechanical/WAVESHARE-ESP32-S3-MATRIX-SCHEMATIC.pdf`.
`C-EN`, the 1 µF this board added for Espressif's `CHIP_PU` RC (#14 A2,
#11 F7: *"usually R = 10 kΩ and C = 1 μF"*
`[ds logic/ESP-HARDWARE-DESIGN-GUIDELINES-ESP32S3.pdf p.11]`), sat at the
board end of the `EN` conductor; with no conductor it has nowhere to go, and
it is removed. **#14 A2's start-up RC is therefore an accepted risk, by the
owner's USB-only choice**: `EN` rises with the Matrix's 3V3 through `R8` and
whatever stray capacitance its own board has, as on every bench Matrix. What
would show it: a Matrix that fails to start on a slow power-up — the E-test
for it is a power cycle with the umbilical's soft start (ADR 0021 amendment
2026-10-03 says what then).

---

## Component table

| Ref | Value | Job | Confidence |
|---|---|---|---|
| `HDR-SERVICE` | **1×3**, 2.54 mm | The real-time board's UART pair and GND | `[repo] bom.csv`; decided (ADR 0018; owner, 2026-10-03) |
| `R-TXD-SER` | 499 Ω 1 % | In series with `U0TXD`, at `J-MCU` pin 22 | `[ds]` Espressif guidelines p.16 |
