# 0017 — One main board

**Status:** Accepted; amended 2026-09-27 (the key-board chain: 1.27 mm IDC, *Amendment* below)

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
  (`mechanical/DESIGN.md`). *(Amended 2026-09-27, below: through-hole
  1.27 mm IDC headers and an IDC ribbon replace the flat flex and ZIF
  connectors; the lid is laid beside the body with the ribbons plugged in,
  not tilted, and they are unplugged, not unlatched.)*
- **The breath sensor moves to the mouth end** (owner's choice between the
  mouth end, the middle with the strip jumpered around it, and keeping
  separate boards): on the far side from the tube, ports towards the tail,
  beside the breath trap. The thumb switches' pins stand through the board in
  two bands along the body, the LED strip takes the band between them, and
  the sensor is too wide to sit beside the strip anywhere along it.
- **The Matrix and the umbilical plug into its tail end** (owner, same day):
  a flat ribbon from the Matrix's pad rows to J-MCU *(24-way since
  [ADR 0018](0018-main-board-wiring-decisions.md))*, unplugged when
  the lid comes off; the etherCON's patch lead to J-UMB, placed where the
  lead's minimum bend radius lands it (`mechanical/DESIGN.md`) *(since
  [ADR 0021](0021-pcb-mount-ethercon.md): no patch lead — the etherCON is
  soldered to an adapter, and J-UMB, a right-angle header, joins the adapter
  to a tongue of this board)*.
- **The LED strip runs down the centreline** (ADR 0016's strip, moved from the
  board's edge), from past the sensor to the board's tail end.
- **Holes in the board over the U-bolt's nuts**, which stand above its
  underside, and notches at the screws its edges reach. *(Since ADR 0022
  point 7: the board is in the U-bolt's clamp, with a clearance hole for each
  leg and the nuts on its top face.)* **Standoffs** off the
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
  the key boards *(IDC ribbons since the 2026-09-27 amendment)*. *(Done 2026-09-26: `hardware/interfaces/key-chain-loom/`
  now describes the ribbons, and `chain-connectors` in `config/figures.yaml`
  is re-derived from them. The chain order and its 32-bit map are unchanged.)*
- **The dev board is not socketed, and there is no loom.** The Matrix's
  ribbon unplugs at `J-MCU` and is desoldered to swap the board
  (`hardware/carrier/carrier.md`); the patch lead plugs into `J-UMB`
  (`hardware/interfaces/spi-link/`) *(since ADR 0021: `J-UMB` is soldered to
  the etherCON's adapter; nothing unplugs there)*. The Matrix's pad rows have one ground
  pad, so the ribbon's extra conductors are 5 V and ground soldered to its
  test points, decided in [ADR 0018](0018-main-board-wiring-decisions.md). The breath sensor is surface
  mount and is soldered down (`hardware/interfaces/breath-sense-link/`,
  *Mounting*).
- **The main board is long** — its size is in `mechanical/drc.echo` "main
  board (derived)". Worth checking against the board house's panel and the
  cost of a long, narrow 2-layer board before M4.

## Amendment, 2026-09-27 — the key chain goes to through-hole IDC

*Corrected the same day against the banked full prints: the key-board pin
map, the cable's part, the hairpin's legs and the header's height
(`hardware/interfaces/key-chain-loom/notes.md` has what it said).*

**Decided by the owner, 2026-09-27.** The key chain's connectors change from
flat flex to through-hole IDC. The ribbon decision above stands — each key
board still reaches the main board by one ribbon, and the lid still comes off
with nothing to line up blind — but its parts, its path and its length change:

- **`J-CHAIN`** is a **2×6, 1.27 mm pitch, shrouded, keyed, right-angle,
  through-hole IDC header**, the same part at every `J-CHAIN` position
  (`chain-connectors`; stand-in Samtec SHF-106-01-L-D-RA,
  `datasheets/connectors/SAMTEC-SHF-1XX-01-X-D-XX-PRINT.pdf`).
  `chain-connectors` is unchanged.
- **The cable is a flat IDC ribbon**, 12 conductors at 0.635 mm, with a 2×6
  IDC socket at each end, bought as an assembled length, **its notch
  reversed on the key-board end** (stand-in Samtec FFSD-06-D-xx.xx-01-N-RN2,
  `datasheets/connectors/SAMTEC-FFSD-XX-X-XX.XX-01-PRINT.pdf`). Its
  BOM row is renamed `FFC-CHAIN` → **`CBL-CHAIN`**.

**The owner's reasons:**

1. **Mechanical robustness.** Through-hole pins take the cable's pull into
   the board; SMT ZIF pads do not.
2. **Right-angle headers, stacked.** On each key board the header hangs from
   its underside directly over the main board's, both in the far band beside
   the LED strip, both mouths facing the same way along the body.
3. **The ribbon lies flat, so it does not block the LED strip.** It comes out
   of both plugs and folds back on itself: closed, a flat hairpin along the
   body, both legs between the two plugs' heights (`mechanical/drc.echo`
   "key-chain ribbon closed: hairpin leg and fold radius" and "key-chain
   ribbon fold no tighter than its bend radius"; which way each folds is
   `config/body.yaml` `routing.chain_fold`). *(Amended 2026-09-27, after the
   key board's review: this said the main board's leg lay on the main board
   and the key board's hung just under its socket. With the `-RN2` cable
   the main board's socket's cable leaves upward, so both legs lie between
   the plugs; see the pin-map bullet below.)*
4. **Long enough to connect with the lid off** — "to have the top off and
   still connect the ribbon before tightening down". The service position is
   the lid laid face down beside the body off its far edge, the ribbon running
   up from the main board over the far side's top edge and down to the key
   board (`routing.chain_service`, `routing.chain_slack`; the length is
   `drc.echo` "key-chain ribbon length (derived)"). The lid comes off by
   lifting it, laying it beside the body and unplugging the two sockets.
   *(Amended 2026-09-27, after the key board's review: the service length
   now includes the lift of the body standing on its U-bolt
   (`routing.chain_service`), and the cable is ordered by a separate line,
   `drc.echo` "key-chain cable to order (FFSD length code)": the FFSD length
   field is inches, overall over both sockets, with its tolerance covered.
   The derived length is millimetres of free ribbon and is not the order
   code.)*

**Why the old reason against IDC no longer holds.** The decision above
rejected IDC as too tall for the gap. That was judged from memory, about
2.54 mm parts. Measured this time from banked drawings: a 2.54 mm IDC header
and plug stack 13.1 mm (14.6 mm worst case) `[datasheet, the banked 2.54 mm
header and socket drawings in datasheets/connectors/]` between the
boards. The gap is `drc.echo` "key board to main board gap"; with parts on
both boards what a main-board part may stand in is "main board parts room
under the key boards", and against that the 2.54 mm stack fits nominally but
not at its worst case `[calc: 13.1 and 14.6 against the room drc.echo
prints]`. *(Amended 2026-09-27: this sentence said "fits nowhere", which
the room it is measured against does not support; "not at its worst case"
is the finding, and it is still a reason to reject it.)* *(Amended 2026-09-27: this
bracket cited the gap as twice the ribbon's fold radius plus
`boards.chain_hdr_h`. That was true only of the first hairpin, and it no
longer derives the gap; the gap itself did not move.)* The 1.27 mm right-angle header stands only `boards.chain_hdr_h` off
each board (off the banked full print), and fits.

**Consequences.**

- **The key board's pin numbers differ, and the cable sets them.** A keyed
  socket always mates its position n to header pin n, so the map is how the
  cable assembly is built. The key board's header is the main board's part
  upside down; with the cable's second socket's notch reversed (Samtec
  `-RN2`), both sockets' cables leave on their key's side, so **the main
  board's leaves upward and the key board's downward**, facing each other,
  with no twist, and main-board pin n arrives at key-board pin 13 − n
  `[datasheet, both full prints: FFSD sheet 1 fig 1, sheet 2 fig 3]`
  (`hardware/interfaces/key-chain-loom/`). *(Amended 2026-09-27, after the
  key board's review: this said the key board's ribbon "leaves downward like
  the main board's", from a rule — "a socket's cable leaves on the side away
  from its notch" — that the print does not support. A cable whose ends both
  leave downward is the standard one, without `-RN2`, and it puts 3V3 on a
  ground; every cable is metered before it is first powered.)*
- **The key header's pin tails stop short of the plate.** They come up
  through the key board toward the grounded plate, across the plate-to-board
  gap (the spacer and washer's since ADR 0020's Amendment 2), and `drc.echo` "J-CHAIN pin tails clear of the key plate" checks they
  stay clear of it. *(Amended 2026-09-27, after the key board's review:
  this bullet gave the plate a window over the tails. The print's tail
  length shows they stand short of the plate, so the window is gone.)*
- **No ZIF latches.** Any text telling a builder to flip ZIF latches, or
  that the lid tilts a little with the ribbons attached, is superseded.
- `config/body.yaml`'s `boards.ffc_conn_*` became `boards.chain_hdr_*` and
  `boards.chain_plug_*` (see [ADR 0020](0020-key-boards-screw-to-the-plate.md)'s
  amendment note).
