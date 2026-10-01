# Key chain — simulation

The chain between the main board and the left-hand key board:
- **its 3V3 rail:** FB-CHAIN, the ribbon, `C-DECOUPLE-165`, and the do-not-fit
  `C-BULK-CHAIN`;
- **its signals over the ribbon:** SCK out to the key board's register, and QH
  back to the next register.

`sims.yaml` says what each run must show and why. The decks beside it are
filled by `tools/sim.py`; `results.yaml` is generated.

**Values come from where they live:**
- the key board's parts from its `board-netlist.yaml`;
- `R-CHAIN-SER` from `hardware/bom.csv`;
- the ribbon's length from `mechanical/drc.echo`;
- the bead from Murata's own SPICE model, banked in
  `datasheets/discrete-and-power/`;
- the thresholds, input capacitance and switch from the key network's
  simulation (`params_from:`).

| Sim | Holds, at every corner |
|---|---|
| `rail-as-ordered` | with C-BULK-CHAIN fitted, the key board's 3V3 stays inside its limit through a clock burst and every key closing at once; DEV_3V3, the ADC's reference, moves under one LSB |
| `rail-without-bulk` | the same holds with it left off: the part makes the rail quieter, it is not what keeps it inside its limit |
| `rail-impedance-*` | the rail's impedance at the register, and its peak: the LC's frequency and height (recorded) |
| `edge-droop-decoupler-alone` | each clock edge's charge, from `C-DECOUPLE-165` alone, dips the register's VCC only a millivolt or so |
| `sck-to-key-board` | SCK at the register: no swing back through its hysteresis (no double clock), no overshoot past its clamp |
| `sck-without-series-resistor` | the same with `R-CHAIN-SER` shorted: at the strong-drive corner it double-clocks and passes the clamp. This is what the resistor is for (recorded) |
| `qh-to-main-board` | QH, with no series resistor, at the next register's SER: no false edge, no overshoot past its clamp |
| `hop-hold-lt-to-rh` | the one hop whose downstream register is clocked later (`left_thumb` → `right_hand`), at the worst threshold pair, with **no** propagation delay, `R-HOP-SER` fitted as netlisted (2.2 kΩ at `left_thumb`'s `QH`, owner 2026-10-01): the data reaches `right_hand`'s `SER` after its clock at every corner and on both edges (`hold_margin` > 0), and within 100 ns of it (`ser_delay`) |
| `hop-hold-without-series-r` | a what-if: `QH` straight into the ribbon, as until 2026-10-01. The clock skew is 6–12 ns and the data beats `right_hand`'s clock, so the hop would hold only on a `CLK`→`QH` delay of ~11 ns that TI does not publish (recorded, asserted to fail) |

## What a result is worth, and what is assumed

- **The bead model is Murata's, stated for 1 MHz – 3 GHz at 0 A bias.** The
  rail's LC sits below 1 MHz, so there it is extrapolated. Bring-up step 6
  confirms on the real rail.
- **The ESP32-S3's GPIO is estimated.** Espressif publishes no output impedance,
  edge rate or IBIS model, so its impedance and edge are swept. **The main
  board's load on SCK and the key board's trace are assumptions** until the main
  board is laid out. Each is marked in `sims.yaml`.
- **The ribbon is 3M 3754's characterisation:** the FFSD's wire and pitch.
  Samtec publishes none for FFSD.
- **Two timescales, two decks.** The rail sees the clock burst as its average
  current (`rail.cir`), and each edge's spike is drawn from the decoupler alone
  (`edge.cir`). Driving 5 ns ideal spikes into the bead's model gave a
  first-edge glitch that no later edge repeated, under every solver setting
  tried: a numerical artefact, recorded so the split is not undone.
