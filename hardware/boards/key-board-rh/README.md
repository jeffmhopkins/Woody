# Right-hand key board — `key-board-rh`

The right hand's six keys (RH1–RH6) and their register. **It is made, checked,
ordered, assembled and brought up exactly as the left-hand board is**, and
[`../key-board-lh/README.md`](../key-board-lh/README.md) is the procedure for
all of it. This page gives only what differs. Where it says nothing, the
left-hand page holds, with `key-board-rh` for `key-board-lh` in every path.

> **Status: orderable as a prototype, not as the instrument's board**, for the
> same reason as the left-hand board. The six switch positions come from
> `config/body.yaml` `layout.rh_gaps` and `layout.rh_offsets` until M2 fills
> `config/key-layout.yaml`, and M3 locks them.

## What differs from the left-hand board

| | Left hand | This board |
|---|---|---|
| Keys | five, LH1–LH5, on inputs H..D | **six**, RH1–RH6, on inputs H..C |
| The register's other inputs | A is a free input with its pull-up (R11, sheet FREE3); B and C are the markers | **no free input**: A and B are the markers (`key-marker-and-bits/allocation.yaml`) |
| The register's decoupler | C6, across the ends of pins 16 and 15 | **C7, below the register's J-CHAIN end, beside pin 8** (`layout.yaml` says why: two key lines leave the far row here, and the left-hand board's place walls them in) |
| The register's far-row ground pins | reached by the pour | **strapped by tracks of their own**, pin 12 (the low marker) to pin 8 and pin 15 (CLK INH) to pin 12, held by `pcb.py check` (`layout.yaml` `connect_first:`): the far-row key lines box them in, so no pour reaches them |
| The register's place | level with LH3 | 6.0 past RH3's level, where the header's new place leaves room for SCK and SH/LD between them (ADR 0025 moved `J-CHAIN`), and 0.5 further from the key row, for the room those lines need. **Marginal**: `layout.yaml` records what else was tried |
| The rail's reservoir | C7 | **C8** |
| SER comes from / QH goes to | the main board / the left thumb (`/CHAIN_SER_LH`, `/HOP_LH_LT`) | the left thumb / the right thumb (`/HOP_LT_RH`, `/HOP_RH_RT`), `key-chain-loom.md` |
| Its rail | `V3V3_CHAIN_LH` | `V3V3_CHAIN_RH` |
| **The Matrix** | none | **carried on two rails past the tail columns** (owner, 2026-10-02; ADR 0021, *Amendment, 2026-10-02 (2)*): J3 and J4 are bare header pins through the Matrix's pad rows on a shim, J5 four wire pads for its `TP2`, `TP3`, `EN` and `IO0`, and J2 (`J-MCU-KB`) hangs under the board straight above the main board's `J-MCU`, the Matrix ribbon's key-board end. J2's pin k is `J-MCU` pin 25 − k; `tools/kicad.py check` holds all four parts to `hardware/carrier/netlist.yaml`. The Matrix's grounds join `GND_CHAIN`, and its 5 V and 3V3 are power tracks (`layout.yaml`) |
| The outline | a rectangle | the rectangle and the two rails, from the body CAD; the rails' inside edges clear the Matrix's back-side parts and the USB-C plug (`mechanical/drc.echo` *"Matrix on the right-hand key board's rails"*) |
| The key networks | the pattern, every key | **RH6's T is an exception**, under the switch's tail-side edge, because J2 stands where the pattern puts it (`layout.yaml`) |

Everything else is the same part, placed the same way: every key's network
the same T round its own switch but RH6's (`layout.yaml` `networks:`, the same
pattern), J1 where the body
CAD puts it, the four corner mounts, the rules and the board house's limits.

## The references

As the left-hand board's table, for six keys:

| Reference | BOM row | What it is |
|---|---|---|
| SW*n*, *n* = 1-6 | `SW1-n` | the switch of key RH*n* |
| R(2*n*-1): R1, R3, … R11 | `R-KEY-SER` | key RH*n*'s series resistor |
| R(2*n*): R2, R4, … R12 | `R-KEY-PU` | key RH*n*'s pull-up |
| C*n*: C1-C6 | `C-KEY` | key RH*n*'s capacitor |
| C7 | `C-DECOUPLE-165` | the register's decoupler |
| C8 | `C-BULK-CHAIN` | the rail's reservoir, beside J1's 3V3 pin |
| U1 | `U-KEYS` | the register, SN74HCS165 |
| J1 | `J-CHAIN` | the key chain's header |
| H1-H4 | (board only) | the corner mounts' holes |
| J2 | `J-MCU-KB` | the Matrix ribbon's key-board end, hung upside down |
| J3, J4 | `HDR-MATRIX` | pins through the Matrix's 5V..IO1 and IO33..RX pad rows |
| J5 | `W-MATRIX` | four wire pads: `TP2`, `TP3`, `EN`, `IO0` |

## Ordering

The left-hand page's *Ordering it — JLCPCB* is the order sheet, with
`key-board-rh` in every file name (`cd hardware/boards/key-board-rh/fab && zip
/tmp/key-board-rh-gerbers.zip *.gbr *.drl *.gbrjob`). It is a **separate design
and a separate order**: one instrument needs one of each. Put both in one cart
so they ship together. What differs:

- **The parts** (its step 4) are the same six LCSC parts, with the same Basic/Extended split, stock and rotation offsets. This board places R1–R12, C1–C8 and U1: six of each key part, `C-DECOUPLE-165` is C7, and `C-BULK-CHAIN` is C8.
- **The placement preview** (its step 5): C8, not C7, is beside J1's 3V3 pin.
- **The cost** (its step 6), *estimates*:
  - The board is **wider than 100 mm** (its outline, `mechanical/export/key-board-rh.dxf`), so JLC's $2 price for 5 boards up to 100 × 100 mm `[web https://jlcpcb.com/, 2026-10-01]` does not apply. Expect a few dollars more for the bare boards (*estimate* `[from memory]`). The live quote decides.
  - SMT joints: $0.19 [calc: (20 two-pad parts × 2 + U1's 16) = 56 joints × 2 boards × $0.0017].
  - Parts, 2 boards: about $2.65 [calc: per board 6 × 0.0042 + 6 × 0.0046 + 6 × 0.0173 + 0.0189 + 0.0651 + 1.086 = $1.327, at the left-hand page's 2026-10-01 unit prices].
  - Setup, stencil and the one Extended feeder fee are the same as the left-hand board's, and they are charged again: per design, not per cart.
- **The hand assembly**: buy **six** switches, not five. `J-CHAIN`'s stock (the left-hand page) has to cover both boards. Then the Matrix: J2 (`J-MCU-KB`, the same XKB header as `J-MCU`), and the Matrix on its pins and shims (`HDR-MATRIX`, `MECH-MATRIX-SHIM`, `W-MATRIX` say how), **before** the key plate goes on.
- **Before ordering, check against the Matrix in hand** which side its 5V..IO1 row is on with the USB-C edge toward the mouth, and where its `TP2`, `TP3` and button pads are (ADR 0021 amendment, *Other risks*). A mirrored row puts 5 V on IO pins.

## Bring-up

As the left-hand board's, with two differences at step 5 (the chain): the
eight bits out, H first, are RH1..RH6 and then the two marker bits, in
`key-marker-and-bits/allocation.yaml`'s order, and there is no free bit.

## Simulation

`sim/`, generated from this board's netlist as the left-hand board's is,
with that board's register model and parameters imported by path, so they
are stated once. At every corner: every key input H..C clears the register's
thresholds open and closed, the high marker (A) reads high, and the draw with
every key closed is six keys' `key-scan-current`.

## Revisions

| Rev | Date | What changed | Where |
|---|---|---|---|
| A | 2026-09-28 | First layout, from the left-hand board's (`layout.yaml`). Not yet ordered; re-laid out 2026-09-29 for the cassette's columns (ADR 0025): the mouth end 0.6 and the tail end 0.2 longer, `J-CHAIN` 13.0 further toward the tail where the shorter ribbon lets the body CAD put it, the register, C7 and C8 following it, the switch side's title moved off the header's tails | git history of this directory |

## Open, and what decides each

The left-hand page's *Open* table holds for this board too. This board adds:

| Open | What decides it |
|---|---|
| The pad rows' side and the wire pads' place (J3, J4, J5) | the Matrix in hand, before the order |
| The 3V3 track's width to J2: it adds to the breath ADC's reference drop (`hardware/carrier/carrier.md`, *The Matrix's wiring adds to it*) | widen it in KiCad before the order; `layout.yaml` `rules: power_track` is the router's |
| A support under the rails' tips (`config/body.yaml` `boards.matrix_support`) | the IMU tap test on the first instrument (ROADMAP) |
