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
| The register's place | level with LH3 | level with RH3, 0.5 further from the key row, for the room those lines need. **Marginal**: `layout.yaml` records what else was tried |
| The rail's reservoir | C7 | **C8** |
| SER comes from / QH goes to | the main board / the left thumb (`/CHAIN_SER_LH`, `/HOP_LH_LT`) | the left thumb / the right thumb (`/HOP_LT_RH`, `/HOP_RH_RT`), `key-chain-loom.md` |
| Its rail | `V3V3_CHAIN_LH` | `V3V3_CHAIN_RH` |

Everything else is the same part, placed the same way: every key's network
the same T round its own switch (`layout.yaml` `networks:`, the same
pattern), the six test pads in one row under the register, J1 where the body
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
| TP1-TP6 | `TP-CHAIN` | the test pads: QH, SER, GND, SCK, SH/LD, 3V3 |
| H1-H4 | (board only) | the corner mounts' holes |

## Ordering

As the left-hand board, with this board's `fab/` files. It is a **separate
design and a separate order**: one instrument needs one of each. For the
hand assembly, buy **six** switches, not five. `J-CHAIN`'s stock (the
left-hand page) has to cover both boards.

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
| A | 2026-09-28 | First layout, from the left-hand board's (`layout.yaml`). Not yet ordered | git history of this directory |

## Open, and what decides each

The left-hand page's *Open* table holds for this board too. This board adds
nothing to it.
