# 0017 — One main board

**Status:** Accepted; amended 2026-09-27 (the key-board chain: 1.27 mm IDC, *Amendment* below)
and 2026-09-29 (four layers, and parts on both faces, *Amendment* below) and
2026-10-04 (through-hole tails over the plate trimmed to a length, *Amendment* below) and
2026-11-20 (both hands' chain headers face the mouth, two *Amendments* below) and
2026-11-21 (the chain headers stand vertical and are 2×5, *Amendment* below); the
wiring details are [ADR 0018](0018-main-board-wiring-decisions.md)

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
  before *(since ADR 0025: one bottom plate)*), **both thumb clusters' registers
  and networks, and everything the centre board carried.**
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
  beside the breath trap *(Amended 2026-10-05, ADR 0003: there is no trap; one clear tube runs from the inlet to the sensor.)*. The thumb switches' pins stand through the board in
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
  carry it between them. *(Since ADR 0025: no notches; every mount stands on
  the one bottom plate, and eight are the cassette's columns.)*

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
  mouth band. *(Amended 2026-10-05, ADR 0003: there is no trap; one clear tube runs from the inlet to the sensor.)* ADR 0003's pipe-mode and delay arguments were written for a long
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

> **Superseded in its parts, 2026-11-21** (the last Amendment below): the
> headers stand vertical and are 2×5, the cable is a straight one made up
> here, and key-board pin n is main-board pin n. Through-hole IDC, one ribbon
> per key board and the hairpin's place stand. What follows is the record of
> the right-angle 2×6 design.

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
- **The cable is a flat IDC ribbon** (superseded 2026-11-21, below), then 12 conductors at 0.635 mm, with a 2×6
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
   code.)* *(Superseded 2026-09-29 by ADR 0025: the lid no longer comes off
   with the key boards. Tightening down is screwing the key plate onto the
   cassette's columns, and the service position is the key plate held
   raised straight up off them (`routing.chain_service`,
   `routing.chain_raise`). Laid beside the body, the ribbon's hairpin would
   reach the left-hand board's tail column.)*

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

## Amendment, 2026-09-29 — four layers, and parts on both faces

The owner: "I am good to go to four layers on this. That makes sense to me."
**The main board is four layers**, at the same 1.6 mm (signal / ground /
power / signal). It gets an unbroken ground plane under the breath signal
chain and under every chain and SPI line. Routing crosses the U-bolt station
on the inner layers too (ADR 0022 point 7). The first placement had judged
two layers feasible, and four better for the analog ground.

And: "don't be afraid to put some of the passives on the other side if we
need to." **Passives may go on the underside**, within the room between the
board and the plate under it. `hardware/boards/main-board/README.md`,
*Open*, gives the rule.


## Amendment, 2026-10-04 — through-hole tails over the plate are trimmed to a length

**The owner, 2026-10-04** (asked in the working chat, review #8-11, choosing
between an insulating sheet on the bottom plate and a trim length): **"Trim
length"**. The hand parts whose tails stand over the grounded bottom plate —
`J-MCU` and both `J-CHAIN` — are cut after soldering, tails and solder, to at
most `hardware.kb_spacer_l` (the board's bottom face above the plate) less
`boards.tail_clear` (the least air between a tail and what is under it) below
the board. No insulating sheet is added. The figure is computed, not stated:
`hardware/boards/main-board/layout.yaml` `hand_trim:` names the two figures
and `tools/pcb.py render` writes the result, with its arithmetic, into the
`Fit` column of `fab/main-board-hand-assembly.csv`, so the sheet follows
`config/body.yaml`. `U-BUCK`'s cut, `boards.tht_trim`, goes on the same
column. The main board's README, *Ordering it* (**Through-hole tails**), says which parts and why
the others need none.

## Amendment, 2026-11-20 — the left hand's chain headers face the mouth

**The owner, 2026-11-20** (in the working chat, on the first hand-placed left
key board, issue #48): **"Seems like maybe we could turn the header 180°?"**,
and, told that the ribbon and the main board follow it, **"Turn it, we will be
reviewing all the boards so this is ok"**.

`J-CHAIN`'s signal pins are its odd row, the row behind its mouth
(`key-chain-loom.md`). With the mouth toward the tail that row faced away from
the key board's register, and the chain's four lines and 3V3 had to wrap the
header's end to reach it. With the mouth toward the instrument's mouth end the
row faces the register and the bus runs straight in
(`hardware/boards/key-board-lh/lh_layout.py`, *The floorplan*).

**What turns.** `config/body.yaml` `routing.chain_fold` for the left hand. It
is one figure for the ribbon's fold and for the way both of that ribbon's
headers face, so the key board's `J-CHAIN` and the main board's `J-CHAIN-LH`
turn together and stay stacked, **both mouths still facing the same way**
(reason 2 above). The ribbon is the same part folded the same way, mirrored:
the same hairpin, the same `-RN2` cable and length code, the same pin map.
The model's own rule then finds the header's place along the body again
(`mechanical/export/pcb-geometry.echo` `chain`), and the `drc.echo` rules
that held the old place hold the new one: "chain headers on the left_hand
boards clear of the switches", "key-chain ribbon hairpin inside the body
(left_hand)", "key-chain ribbon hairpin clear of the columns (left_hand)".

**What follows it.**

- The main board's `J-CHAIN-LH` is no longer where the body CAD puts it, and
  `tools/pcb.py check hardware/boards/main-board` fails on it until that board
  is laid out again (issue #48's plan: after the three small boards).
- The rev A `key-board-lh.kicad_pcb` fails the same check until the
  hand-laid board replaces it.
- [ADR 0025](0025-the-cassette.md)'s "left-hand board's tail column" is, for
  a ribbon too long, now the column at that board's mouth end: the hairpin
  lies on the other side of the header.
- The right hand's ribbon turned the same day, in the next Amendment.

## Amendment, 2026-11-20 — the right hand's chain headers face the mouth too

**The owner, 2026-11-20** (in the working chat, on the hand-placed right key
board, issue #48), told that the rev A board's header opens toward the
register and that the ribbon's hairpin lies under it: **"I didn't want the
header to have the ribbon cable going over the IC"**, and **"If that's the
case, we do need to turn it"**. The same day: **"We'll be redoing the main
board as well. So if we need to relay out the order for the header pins to
make it route better we can do that too"**. The pin order is not changed
here: both key boards route with it as it is.

Two reasons, and the first is the left hand's: the signal row behind the
header's mouth then faces the register
(`hardware/boards/key-board-rh/rh_layout.py`, *The floorplan*). The second is
the owner's: with the mouth toward the tail the hairpin lay along the body
where the register stands; with it toward the mouth end the hairpin lies on
the header's other side.

**What turns.** `config/body.yaml` `routing.chain_fold` for the right hand,
so `J-CHAIN` on the key board and `J-CHAIN-RH` on the main board turn together
and stay stacked. The model's rule finds the header's place along the body
again (`mechanical/export/pcb-geometry.echo` `chain`); it is not the place it
had facing the tail. The `drc.echo` rules hold it: "chain headers on the
right_hand boards clear of the switches", "key-chain ribbon hairpin inside the
body (right_hand)", "key-chain ribbon hairpin clear of the columns
(right_hand)".

**What follows it.**

- The main board's `J-CHAIN-RH` joins `J-CHAIN-LH`: neither is where the body
  CAD now puts it, until that board is laid out again.
- The rev A `key-board-rh.kicad_pcb` fails `tools/pcb.py check` on its header
  until the hand-laid board replaces it.
- `chain_fold`'s reason for folding the right hand toward the tail was the
  regulator block; the model's rule for the header's place still keeps the
  header and the hairpin off the main board's tall parts, wherever they fold.

## Amendment, 2026-11-21 — the chain headers stand vertical, and are 2×5

**The owner, 2026-11-21** (in the working chat, issue #49), on the right-angle
headers of the 2026-09-27 Amendment: **"we might actually want straight on
instead of 90° connectors"**, then **"I think maybe then vertical headers are
what we want to do. If there's not enough room in between the boards, we'll
just want to make sure and offset them enough. But this way the cable only has
one bend in it"**. On the parts: **"when picking parts, we'll need to source
that are common, not end of life and readily available"**. Asked to choose
between the 12-way part and the common 10-way size, the owner chose
**"10-way 2x5, common parts"**.

**What changes.**

- **`J-CHAIN` is a 2×5, 1.27 mm pitch, shrouded, keyed, vertical,
  through-hole box header**, the same part at every `J-CHAIN` position
  (`chain-connectors`, unchanged): CNC Tech 3220-10-0100-00
  `[datasheets/connectors/CNCTECH-3220-XX-0100-00-1.27MM-BOX-HEADER-VERTICAL.pdf]`.
  The main board's stands on its top; the key board's hangs from its underside
  **mouth to mouth** with it, at the same place along the body
  (`config/body.yaml` `boards.chain_mb_shift` is what to raise if they must be
  offset).
- **`CBL-CHAIN` is a straight ribbon made up here**: 0.635 mm flat cable with
  a 2×5 IDC socket crimped at each end, both the same way up and the same way
  round, CNC Tech 3230-10-0103-00
  `[datasheets/connectors/CNCTECH-3230-XX-0103-00-1.27MM-IDC-SOCKET.pdf]`.
  Nothing is built to order.
- **The ribbon has one fold.** A socket goes in along the pins and its ribbon
  leaves it flat, along the body, the way `routing.chain_fold` says; both
  sockets' ribbons leave the same way and the spare length closes in one fold
  between them (`mechanical/drc.echo` "key-chain ribbon fold no tighter than
  its bend radius", "key-chain sockets clear of each other, mouth to mouth").
  The 2026-09-27 Amendment's reasons 1, 3 and 4 stand; its reason 2
  (right-angle headers, stacked) is superseded by this one.
- **The two spare conductors go** (`chain-conductors`): the chain used ten of
  the twelve. Pins 1 to 10 keep their signals.
- **Key-board pin n is main-board pin n** (`key-board-chain-pinmap`): a
  straight ribbon mates conductor n to pin n at both ends. The 2026-09-27
  Amendment's map, key-board pin 13 − n, belonged to the `-RN2` cable and is
  superseded with it. On every header the odd row is now the five grounds and
  the even row the four signals and 3V3.
- **Which way each header's key slot faces follows from the straight ribbon**:
  the two sockets' keys face the same way along the flat ribbon, so, folded,
  one faces the fold and the other faces away from it
  (`hardware/interfaces/key-chain-loom/key-chain-loom.md`, *Pin numbering*).

**Why the 12-way part was not kept vertical.** It fits, and it is not end of
life; but the header and its built-to-length cable are made to order, with
weeks of lead time and no stock held where it was looked for
`[web, 2026-11-21: DigiKey's listings for SHF-106-01-L-D-TH and
FFSD-06-D-02.00-01-N]`. The 2×5 is the size debug connectors use: the header
is stocked in the hundreds of thousands
`[web, 2026-11-21: https://www.digikey.co.uk/en/products/detail/cnc-tech/3220-10-0100-00/3883661]`,
and CNC Tech's drawing does not list a 12-position size at all.

**The Matrix's ribbon is not changed.** `J-MCU` and `J-MCU-C` stay
right-angle: that header lies along the body, so a vertical socket would send
its ribbon across the body, and between the header and the LED row there is no
room for the ribbon's fold (`drc.echo` "J-MCU, its plug and the Matrix ribbon
off the LED row").

**What follows it.** The main board and both key boards are laid out again
round the new footprint (`woody:IDC-Header_2x05_P1.27mm_CNCTech_3220_Vertical`),
and `tools/kicad.py check` holds key-board pin k to main-board pin k. The body
CAD stands each pair where the socket's latches, which are longer than the
header, stay over both boards, and where each header's courtyard leaves a
soldering iron's room beside the nearest switch pin (`boards.chain_stub_room`;
`drc.echo` "chain headers on the left_hand boards clear of the switches").
