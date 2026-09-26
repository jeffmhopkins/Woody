# 0017 — One main board

**Status:** Accepted

Replaces the **centre board** and the two **thumb boards** with one board.
The centre board is named in ADRs 0009, 0013, 0014, 0015 and 0016 and in
`mechanical/DESIGN.md`; read it as this board from here on. Amends
[ADR 0001](0001-mcu-and-board-partitioning.md)'s four cluster boards (the two
thumb clusters are now on this board) and
[ADR 0003](0003-breath-sensing-path.md)'s sensor placement. Decided by the
owner, 2026-09-26.

## Context

The body CAD had arrived at five boards inside the cavity: two thumb boards on
the thumb plates, the centre board above them carrying the carrier's circuits,
and the two key boards under the plate. Each thumb board plugged into its key
board through a stacking header that passed through the centre board, which
stood on spacers off the thumb boards and standoffs off the oak.

The centre board was squeezed between the two layers of cluster boards. Under
the key boards its parts had the smallest room of anywhere in the body, and
the regulator block had to be kept beside them.

## Decision

**One board — the main board — at the thumb boards' level, from the mouth cap
to the end of the right hand, the full width inside the sides.** (Owner:
"instead of individual bottom boards, and the center board, maybe we can do
one big long board?")

- **It carries the thumb switches** (soldered, clipped into the thumb plates as
  before), **both thumb clusters' registers and networks, and everything the
  centre board carried.**
- **Its parts face up.** At this level they have the height between it and the
  key boards' parts, and more where no key board is overhead — both are in
  `mechanical/drc.echo` ("main board parts room …"). That is more than the
  centre board had, so the regulator block fits anywhere on it.
- **The key boards connect to it by ribbon** (owner, same day, after asking
  how they connected): one 12-way flat flex ribbon per key board, ZIF
  connectors on both boards, the ribbon a single clean C toward the far side
  wall (the owner's choice over a longer folded ribbon). The key boards hang
  from the lid, so blind-mating stacking headers would have had to re-mate
  blind every time it closed; with ribbons the lid tilts open a little with
  them attached (`mechanical/drc.echo`), and comes off after flipping two ZIF
  latches - no tools, and nothing to line up on the way back. Flat flex rather than IDC because an IDC box header and
  plug are too tall for the gap with parts on both boards
  (`mechanical/DESIGN.md`).
- **The breath sensor moves to the mouth end** (owner's choice between the
  mouth end, the middle with the strip jumpered around it, and keeping
  separate boards): on the far side from the tube, ports towards the tail,
  beside the breath trap. The thumb switches' pins stand through the board in
  two bands along the body, the LED strip takes the band between them, and
  the sensor is too wide to sit beside the strip anywhere along it.
- **The Matrix and the umbilical plug into its tail end** (owner, same day):
  a flat 20-way ribbon from the Matrix's pad rows to J-MCU, unplugged when
  the lid comes off; the etherCON's patch lead to J-UMB, placed where the
  lead's minimum bend radius lands it (`mechanical/DESIGN.md`).
- **The LED strip runs down the centreline** (ADR 0016's strip, moved from the
  board's edge), from past the sensor to the board's tail end.
- **Holes in the board over the U-bolt's nuts**, which stand above its
  underside, and notches at the screws its edges reach. **Standoffs** off the
  oak or the thumb plates where nothing else is; the soldered thumb switches
  carry it between them.

## Options considered

- **Keep the centre board and the thumb boards.** Five boards, spacers and
  standoffs in a stack, and the least parts height in the body. Rejected.
- **Sensor in the middle, strip jumpered around it.** Keeps the sensor off the
  mouth end, at the cost of cutting the strip and four short wires. Not chosen.

## Consequences

- **ADR 0003's "no internal analog run" is gone.** ADR 0003 put the sensor at
  the tail so the analog breath pair never ran inside the body; since this ADR
  it starts at the mouth end, and the buffered breath signal runs the length
  of the main board to the umbilical. It is a PCB trace on one board now, not
  a wire in a side channel, which is the manageable version of the problem:
  route it over its own ground, away from the strip's data and 12 V feed and
  the chain's clock. **E11's "breath output clean while the matrix and LEDs
  are exercised" is the test**, and it matters more than it did.
- **The breath tube gets short.** Mouth cap, trap, sensor, all within the
  mouth band. ADR 0003's pipe-mode and delay arguments were written for a long
  tube and get easier; the ROADMAP re-derivation item stands.
- **Four cluster boards become two key boards plus the main board.**
  `PCB-CLUSTER` drops to two and `PCB-CARRIER` is the main board. The key
  chain is now on-board traces for the thumbs and two flat flex ribbons to
  the key boards. *(Done 2026-09-26: `hardware/interfaces/key-chain-loom/`
  now describes the ribbons, and `chain-connectors` in `config/figures.yaml`
  is re-derived from them. The chain order and its 32-bit map are unchanged.)*
- **The dev board is not socketed, and there is no loom.** The Matrix's
  ribbon unplugs at `J-MCU` and is desoldered to swap the board
  (`hardware/carrier/carrier.md`); the patch lead plugs into `J-UMB`
  (`hardware/interfaces/spi-link/`). The Matrix's pad rows have one ground
  pad, so how the ribbon's five spare positions are used — spare GPIO or
  extra grounds — is open until M4 and E11. The breath sensor is surface
  mount and is soldered down (`hardware/interfaces/breath-sense-link/`,
  *Mounting*).
- **The main board is long** — its size is in `mechanical/drc.echo` "main
  board (derived)". Worth checking against the board house's panel and the
  cost of a long, narrow 2-layer board before M4.
