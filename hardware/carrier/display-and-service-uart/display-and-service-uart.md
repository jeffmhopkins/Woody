# Display loom and service UART — schematic

**Status:** Split out of `carrier.md` 2026-09-21 (Phase B). Every line below was
moved verbatim; nothing was reworded and no value was touched in the move.

`J-DISP`, the nine-conductor loom to the display board 360 mm up the body, and
`HDR-SERVICE`, the 2×3 console header under the tail-underside cover.

> **Half of this circuit is undrawn, and saying so is better than implying
> symmetry.** `J-DISP` and `HDR-SERVICE` both terminate on the **display
> board**, and *the display board has no schematic page in this corpus*. Every
> row in the table below whose peer is the display board therefore names a
> connector whose far end nothing in `hardware/**` draws. What that end needs —
> its regulator, its bulk capacitance, its console pinout — is asserted in
> ADR 0013 and in `bom.csv` and is drawn nowhere.

## Interfaces

Every net that crosses this circuit's boundary. Quantities appear **only** as a
citation into `config/figures.yaml` — this table names nodes, it does not
restate values.

The `Dir` and `Peer` columns are defined once in
[`hardware/README.md`](../../README.md#the-interfaces-table).

| Node | Dir | Peer | Figure | Note |
|---|---|---|---|---|
| IO5, IO6 | in/out | `HDR-DEV` | — | UART1, out to the display board on `J-DISP`. **Far end undrawn** |
| `U0TXD` (IO43), `U0RXD` (IO44) | in/out | `HDR-DEV` | — | The real-time board's console pair, to `HDR-SERVICE` and up `J-DISP` |
| display board `U0TXD`, `U0RXD` | in/out | `HDR-SERVICE` | — | **Far end undrawn** — three of `HDR-SERVICE`'s six pins belong to a board with no page |
| 5 V (or `+12V`) on `J-DISP` | in | `carrier/power-entry-instrument` | — | Buck B, and it leaves this circuit again on `J-DISP`. Which of the two rails it is depends on where buck B lives, which is open in `carrier.md` |
| GND ×2 on `J-DISP` | ref | `carrier/power-entry-instrument` | `dig-gnd-topology` | The `PWR_GND` pour. One with the supply, one with the UART pairs |
| two spare conductors | — | — | — | Per ADR 0009, unallocated |
| `EN`, `IO0` | — | — | — | **Not wired** — withdrawn, see below. They are not on the dev board's headers |

## §6 Display loom and service header

*Connectivity is **[`netlist.yaml`](netlist.yaml)**, not the conductor list
below. The list is a representation of it and `tools/check-netlist.py` checks
the two agree.*


**This section's open question has been answered, against it.** The draft asked
whether `EN` and `IO0` reach the ESP32-S3-Matrix's headers and said "settle it
before this board is laid out". `bom.csv` row `HDR-SERVICE` has since settled
it: **they do not.** The vendor's board definition accounts for every pin on
both header rows — 3 power and 17 GPIO — and neither appears; `IO0` is under
the BOOT button and `EN` is on the reset circuit, so reaching either means
soldering to the dev board, which ends its life as a swappable module and
breaks `HDR-DEV`'s "sockets, not solder-down" rule `[repo] bom.csv, 0009`.

**`HDR-SERVICE` is therefore 2×3, six pins, not 2×5** — a UART pair and a
ground for each board, and nothing else. The recovery ladder absorbs the loss:
OTA rollback first, USB-Serial-JTAG through the tail slot second, this header
third. A corrupted bootloader ends the instrument, and that is accepted
`[repo] bom.csv`.

**Two conductors and three passives per line come out of the loom with it:**

```
  J-DISP  ──  9 conductors, 360 mm, up a side channel

    5 V (or +12 V — see Still open)        1
    GND                                     1
    IO5 → display RX, IO6 ← display TX      2      UART1, 921600 baud
    U0TXD                                   1  ┐  service, per ADR 0009
    U0RXD                                   1  │  and firmware/README.md
    GND                                     1  ┘
    two spare conductors (ADR 0009)         2

  No EN, no IO0, and so no RC networks for them.


  HDR-SERVICE  2×3, under the tail-underside cover:

    real-time board:  U0TXD(IO43)  U0RXD(IO44)  GND
    display board:    U0TXD        U0RXD        GND
```

**ADR 0013's "four broken-out pins — UART pair and power"** `[repo] 0013` is a
statement about the display board's *pin* requirement, not about the loom.
The loom is nine conductors over 360 mm, sharing a side channel with an 800 kHz
data line and 12 V LED power. What runs in it now is a UART pair and a console
pair — all four framed, byte-oriented and recoverable by retry, which is
exactly what `EN` and `IO0` were not. **The proposed RC networks are withdrawn
along with the lines they protected.**

---

## Component table

*Rows moved verbatim from `carrier.md`'s component table.*

| Ref | Value | Job | Confidence |
|---|---|---|---|
| `HDR-SERVICE` | **2×3** | UART pair + GND per board. `EN`/`IO0` are not on the headers and are not wired — §6 | `[repo] bom.csv`, settled |
| **`J-DISP`** | **9-way** | **Proposed — see §6. Was 11-way before `EN`/`IO0` were withdrawn** | proposed |

---

## Still open

- **Whose console pair runs up the loom.** The Interfaces table says the
  real-time board's `U0TXD`/`U0RXD` go "to `HDR-SERVICE` **and up `J-DISP`**",
  and it also says the **display board's** `U0TXD`/`U0RXD` arrive at
  `HDR-SERVICE` with the far end undrawn. There is **one** service trio in the
  nine-conductor loom and **two** boards' console pairs, so at most one of
  those readings can be true of it. **Decided by:** which board's console the
  service header is for when only one can travel — and it changes nothing
  else, because the conductor count is the same either way.
  [`netlist.yaml`](netlist.yaml) leaves those four pins unasserted rather than
  picking.
