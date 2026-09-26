# Service UART — schematic

**Status:** Rewritten 2026-09-26, when the display board was removed
(ADR 0015). This page was the display loom *and* the service header; the
loom went with the display board, and the service header is what is left.
The page as it was is in git.

`HDR-SERVICE`, a 1×3 console header on the main board, reached with the
lid off — there is no service cover since 2026-09-26 (ADR 0009):
the real-time board's console pair and a ground.

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
| `EN`, `IO0` | — | — | — | **Not wired.** They are not on the dev board's headers |

## The service header

*Connectivity is **[`netlist.yaml`](netlist.yaml)**, not the drawing below.
The drawing is a representation of it and `tools/check-netlist.py` checks the
two agree.*

```
  HDR-SERVICE  1×3, on the main board (lid off):

    real-time board:  U0TXD(IO43)  U0RXD(IO44)  GND
```

**Why only three pins.** `EN` and `IO0` do not reach the ESP32-S3-Matrix's
headers: the vendor's board definition accounts for every pin on both header
rows — 3 power and 17 GPIO — and neither appears; `IO0` is under the BOOT
button and `EN` is on the reset circuit, so reaching either means soldering to
the dev board `[repo] bom.csv, 0009`. The recovery ladder absorbs the loss:
USB-Serial-JTAG through the tail USB-C slot first, a reflash over the same
port second, this header third. A corrupted bootloader ends the instrument,
and that is accepted.

---

## Component table

| Ref | Value | Job | Confidence |
|---|---|---|---|
| `HDR-SERVICE` | **1×3** | The real-time board's UART pair + GND. `EN`/`IO0` are not on the headers and are not wired | `[repo] bom.csv`, settled |
