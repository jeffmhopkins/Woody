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

Everything else is the same part, placed the same way: every key's network
the same T round its own switch (`layout.yaml` `networks:`, the same
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
| C9 | `C-DECOUPLE-165` | U1's second decoupler, at VCC (pin 16), review #6-5 |

## Ordering

The left-hand page's *Ordering it — JLCPCB* is the order sheet, with
`key-board-rh` in every file name (`cd hardware/boards/key-board-rh/fab && zip
/tmp/key-board-rh-gerbers.zip *.gbr *.drl *.gbrjob`). It is a **separate design
and a separate order**: one instrument needs one of each. Put both in one cart
so they ship together. It is ordered as the left-hand board is, as **Standard
PCBA on JLC-added rails and fiducials** (owner, 2026-10-04; ADR 0028,
*Amendment, 2026-10-04*): 107.0 × 42.1 (`fab/key-board-rh-job.gbrjob`) is under
Standard's 70 × 70 mm minimum across. What differs:

- **The gates**: `python3 tools/pcb.py check hardware/boards/key-board-rh`, 0
  errors, and `python3 tools/kicad.py check --board key-board-rh`, PASS - this
  board and the sheets it places, not another board's layout (review #6-3).

- **The parts** (its step 4) are the same six LCSC parts, with the same Basic/Extended split, stock and rotation offsets. This board places R1–R12, C1–C8 and U1: six of each key part, `C-DECOUPLE-165` is C7, and `C-BULK-CHAIN` is C8.
- **The placement preview** (its step 5): C8, not C7, is beside J1's 3V3 pin; and, as there (item 6, review #6-6), JLC's rails and tooling holes land on the rails, clear of the ground pour, the switch pads and the mounting holes, or the order goes with rails outside the outline.
- **The cost** (its step 6), *estimates*:
  - The board is **wider than 100 mm** (its outline, `mechanical/export/key-board-rh.dxf`), so JLC's $2 price for 5 boards up to 100 × 100 mm `[web https://jlcpcb.com/, 2026-10-01]` does not apply. Expect a few dollars more for the bare boards (*estimate* `[from memory]`). The live quote decides.
  - SMT joints: $0.19 [calc: (20 two-pad parts × 2 + U1's 16) = 56 joints × 2 boards × $0.0017].
  - Parts, 2 boards: about $2.65 [calc: per board 6 × 0.0042 + 6 × 0.0046 + 6 × 0.0173 + 0.0189 + 0.0651 + 1.086 = $1.327, at the left-hand page's 2026-10-01 unit prices].
  - Setup, stencil and the one Extended feeder fee are the same as the left-hand board's, and they are charged again: per design, not per cart. The left-hand page's fees are Economic PCBA's, so for this Standard order they are a floor (its step 6).
- **The hand assembly**: buy **six** switches, not five. `J-CHAIN`'s stock (the left-hand page) has to cover both boards.

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

The letters are design history: the silkscreen and title block read `rev A`
with the latest layout's date until a board is fabricated
(`hardware/boards/main-board/README.md`, *Ordering it*, **Revision**; ADR 0020,
*Amendment 9*).

| Rev | Date | What changed | Where |
|---|---|---|---|
| A | 2026-09-28 | First layout, from the left-hand board's (`layout.yaml`). Not yet ordered; re-laid out 2026-09-29 for the cassette's columns (ADR 0025): the mouth end 0.6 and the tail end 0.2 longer, `J-CHAIN` 13.0 further toward the tail where the shorter ribbon lets the body CAD put it, the register, C7 and C8 following it, the switch side's title moved off the header's tails | git history of this directory |
| B | 2026-10-03 | Laid out again: C9, U1's second decoupler at VCC (pin 16, review #6-5); white mask and black legend (ADR 0028); the KS-33's 3.0 mm holes, with the networks 9.0 mm from their switches as the left-hand board's (9.4 put a label on the bigger pads) and `/KEY_RH4` routed third. The board keeps its original outline: the Matrix is on its own carrier board (`hardware/boards/matrix-carrier/`, ADR 0021 amendment 2026-10-03). Two hand edits after `pcb.py layout`: C9's strap to U1 pin 16 (`connect_first`), which a later rip-up had taken; and `J1` pin 12's thermal, which had one spoke a face - `/CHAIN_SHLD` moved from y 46.3 to 46.85 beside it and `/CHAIN_SCK`'s via and detour off it, and pin 12 tied to pin 10. `pcb.py check` passes. Not yet ordered | `key-board-rh.kicad_pcb`, `layout.yaml` |
| — | 2026-10-04 | Silkscreen and title block dated 2026-10-03, the latest layout's date, still `rev A` (review #6-7; the rule above). No copper moved; renders and `fab/` re-written | `key-board-rh.kicad_pcb`, `layout.yaml` `silk:` |

## Open, and what decides each

The left-hand page's *Open* table holds for this board too. This board adds
nothing to it.
