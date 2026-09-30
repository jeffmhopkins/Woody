# 0022 — How the main board is held, and how thick it is

**Status:** Accepted, 2026-09-29, as part of the owner's instruction to "finalize
everything and get us to the line before board layout". It settles
`switch.pcb_t` and `switch.thumb_pcb_below_seat`, which ADR 0020 point 6 and
`docs/reference/ks33-geometry.md` had left open until the main board's own
mount existed. **Amended 2026-09-29 by [ADR 0025](0025-the-cassette.md)**:
every mount is on one bottom plate, the oak mounts are gone, the columns run
through to the key plate, and the U-bolt clamps the bottom plate (*Amendment*,
below).

## Context

The main board (ADR 0017) carries the thumb switches. It is the same Gateron
KS-33 as on the key boards, turned to face down, its pins soldered into the
board and its latch clipped into a thumb plate on the oak bottom. The body
CAD drew the board 1.6 mm thick on generic hex standoffs "off the oak or the
thumb plates", with no fastener behind them. Its depth below the switches'
seat was a placeholder in the middle of the pins' window.

Two things were therefore unanswered:

- **The pins.** At 1.6 mm a thumb switch shows about 0.1 mm of pin to solder.
  That arithmetic took the key boards to 1.2 mm (ADR 0020 point 6), and it
  applies here unchanged (`docs/reference/ks33-geometry.md`).
- **What holds the board.** A standoff needs something to screw into. The
  thumb plates are 1.2 mm aluminium, like the key plate. The rest of the
  floor is oak, and ADR 0009 does not let the oak carry structure.

## Decision

1. **The main board is 1.2 mm** (`switch.pcb_t`), as the key boards are.
   *(Since ADR 0020 Amendment 6: 1.6 mm, as the key boards now are, its top
   pressed against the thumb switches' housings.)*
2. **Over a thumb plate it is held exactly as a key board is** (ADR 0020,
   Amendment 4), with the same parts *(since ADR 0025: on the bottom plate,
   which replaced the thumb plates, at every mount; at a column the nut is the
   column's standoff)*:
   - the PEM FHL-M2.5 stud pressed into the thumb plate, its head flush in
     the plate's underside, so the plate still lies flat on the oak;
   - the key boards' spacer;
   - the board;
   - their nut.

   So the board's depth below the thumb switches' seat is the key boards'
   depth: the plate plus `hardware.kb_spacer_l`
   (`switch.thumb_pcb_below_seat`). It sits inside the pins' window, and
   `mechanical/drc.echo` checks it (*"main board mount sets its depth"*,
   *"main board depth and thickness inside the switch pins' window"*).
3. **Where no thumb plate is under it, it stands on the oak** *(superseded by
   ADR 0025: there are no oak mounts; the bottom plate is under the whole
   board)*:
   - an M2.5 threaded insert for hardwood, set into a blind hole in the oak
     bottom's inside face;
   - a spacer as tall as the plate and the key boards' spacer together;
   - the board;
   - an M2.5 low-head screw from above.

   Nothing shows on the outside. The load is the board's own weight and the
   push of the breath tube onto the sensor. That is locating, not structure,
   so ADR 0009's rule holds.
4. **The body CAD places the mounts** wherever nothing else is: clear of
   pins, the strip, the lid screws, the U-bolt, the sensor, the regulator
   block and the chain headers (*"main board standoffs found clear of
   everything"* lists how many land on each). Each gets a hole in the board,
   and each stud a hole in its thumb plate. *(Since point 8: the mounts
   follow the key boards' mounts, with a pair at each end.)*
5. **The thumb switches in the row nearer the centreline are turned 180°**
   (`config/key-layout.yaml`: LT1, LT3, RT1, RT3). A KS-33's pins sit off its
   centre. On the thinner board they stand proud of the top face, and in the
   near row they pointed at the LED strip's edge. Turned, they point away. A
   square cap on a cross stem feels the same either way.

6. **Each thumb plate is grounded through its own mounts** (owner, 2026-09-29).
   *(Since ADR 0025: the bottom plate, through every mount, and the key plate
   with it, through the columns.)*
   A plate mount's hole in the main board is plated, with a `PWR_GND` pad on
   both faces: the spacer bears on the underside pad and the nut on the top
   one. The stud's clinch and the spacer's face bond the plate to the board's
   ground with no part added. The thumb plates had no bond before. Unbonded,
   a plate floats a millimetre or two from the thumb switches' pins, and a touch
   on it fires spurious notes, as the key plate's would (ADR 0009). The oak mounts stay
   unplated: nothing metal is under them.

7. **The main board is in the U-bolt's clamp** (owner, 2026-09-29: "I think we
   can have the standoffs be part of the actual stackup"). Up each leg go
   *(since ADR 0025: the oak, the bottom plate, a spacer, the main board, a
   washer, the nyloc; there is no backplate)*:
   - the oak;
   - the backplate;
   - a washer (`MECH-UBOLT-WASHER`);
   - the main board;
   - a second washer;
   - the nyloc.

   The backplate and one washer fill the oak to the board's underside, as an
   oak mount's spacer does (*"main board in the U-bolt's clamp"*). So the
   station in the middle of the board is also a mount, with no part added
   but four washers.

   Before this, the nuts stood on the backplate and up through holes in the
   board. Each hole was a nut's corners plus the parts clearance, and it
   merged with the middle screws' notch. The two bites left a neck of board
   about 10 mm wide, which every trace between the two halves had to cross.
   Now the board has a clearance hole for each leg. It keeps copper off
   under the washers and nuts on its outer layers only. The inner layers
   route past the hole (*"main board neck at the U-bolt station"*). The legs'
   holes are unplated: the U-bolt is outside metal on the strap, and it stays
   off the circuit's ground.

   The owner's rule: no big holes in the board, and no narrowing of it here.
   So the notches at the lid screws were cut down as well. They are now the
   screw's clearance hole plus the board's copper-to-edge clearance, opened
   to the edge. The parts' clearance (`boards.board_clear`) had set them
   before, and it still keeps parts away from the screw. It no longer cuts
   the board.

8. **One mount pattern through the instrument** (owner, 2026-09-29: the key
   boards' "standoff locations go all the way down through the instrument
   and down to the main board", "and maybe an extra set of standoffs in the
   very top and the very bottom"). The main board is held:
   - under each of the key boards' eight mounts;
   - by a pair at the mouth end;
   - by a pair on the tongue before J-UMB, which takes the umbilical's mating
     push;
   - by the U-bolt's clamp in the middle (point 7).

   A column is two stacks, not one standoff. The key boards hang from the
   lid's key plate, and the lid lifts off with them plugged in (ADR 0017).
   So the lid's stack ends at the key board. The main board's stands under
   it, on the oak or on a thumb plate, by point 2 or 3. *(Superseded by ADR
   0025: a column is one stack, from the bottom plate to the key plate, and
   vertical, so the key board's mount moves to it rather than the main
   board's.)*

   The column nearest the mouth in each hand stands over a thumb plate,
   0.4 mm too close to a thumb switch's cutout for the stud's edge distance.
   Its main-board mount stands 0.5 mm nearer the mouth than the key board's.
   The thumb plate reaches round it. A column may move up to 1 mm, along the
   body only (*"main board mounts under the key boards' mounts, and a pair
   at each end"*). The mouth pair's far mount stands clear of the breath
   sensor, so it is further in than the near one.

   The search for clear places in point 4 is gone. The counts are in
   *"main board standoffs found clear of everything"*.

## Consequences

- **The main board and the key boards share one stack** and one set of
  hardware on the plates. The oak mounts add three small parts
  (`MECH-MB-INSERT`, `MECH-MB-OAK-SPACER`, `MECH-MB-SCREW`, open until M4).
  *(Since ADR 0025 there are no oak mounts and no such parts.)*
- **The board is a long one** (a standard 1.6 mm since ADR 0020 Amendment 6),
  about
  `mechanical/drc.echo` *main board* long. Where it spans between mounts it
  is carried by the soldered thumb switches, as before. The first board
  confirms how stiff that is.
- **The oak bottom gets blind holes for the inserts.** Like the counterbores
  they are not in its DXF, which carries through-cuts only; the body CAD
  places them. *(Superseded by ADR 0025: no inserts, no holes.)*
- **The thumb plates are ordered un-anodised**, or masked round each stud
  hole, because the bond is metal to metal (`PLATE-THUMB`). Bring-up meters
  each plate to `PWR_GND`. *(Since ADR 0025: the bottom plate, `PLATE-BOTTOM`,
  and the key plate round its column holes.)*
- **The main board's plate mounts are plated holes on `PWR_GND`**
  (`MountingHole_2.7mm_M2.5_Pad_Via`), where the key boards' mounts are
  unplated and keep copper clear. *(Corrected 2026-09-29, ADR 0025:
  `MountingHole_2.7mm_M2.5_Pad_TopBottom`. `_Pad_Via`'s ring of vias breaks the
  board house's hole-to-hole rule, as the left-hand key board's layout found.)*
- **The strap's pull passes through the main board** as compression between
  the washers. At ADR 0009's 80 N jerk that is a few MPa on FR-4 [calc: 80 N
  over a DIN 433 M3 washer's ~20 mm² annulus]. The nylocs are snugged, not
  torqued.
- **The U-bolt's position is fixed by the board's holes.** Moving it after
  the M8 balance check is a board change. It was already, while the board
  had holes over the nuts.
- **Taking the main board out frees the U-bolt and its backplate**, because
  the same nuts hold all three. *(Since ADR 0025 there is no backplate; the
  nuts hold the U-bolt, its spacers and the main board.)*
- **The Matrix keeps its own thickness** (`boards.matrix_t`). It had been
  borrowing the main board's.

## Open, and what decides each

| Item | Decided by |
|---|---|
| ~~The insert, the oak spacer and the screw: parts and lengths (`hardware.mb_*`)~~ Gone with the oak mounts (ADR 0025) | — |
| Whether the long span sags between mounts | The first board |

## Amendment, 2026-09-29 — every mount on the bottom plate ([ADR 0025](0025-the-cassette.md))

The owner made the internals one bonded unit, the cassette, with nothing
screwed into the wood. For this board that means:

- **One bottom plate replaces the two thumb plates** (`PLATE-BOTTOM`). Every
  mount stands on it: the stud, its head flush in the plate's underside, the
  spacer and the board (point 2). So the board's depth is set everywhere as it
  was over a thumb plate, and *"main board mount sets its depth"* is unchanged.
- **The oak mounts are gone** (point 3): no insert, no oak spacer, no screw
  (`MECH-MB-INSERT`, `MECH-MB-OAK-SPACER`, `MECH-MB-SCREW`, `hardware.mb_*`).
  There is no blind hole in the oak bottom.
- **At each of the key boards' eight mounts the stack is one column** (point
  8). The stud comes up through the main board, and a hex standoff threaded
  onto it clamps the board and carries the key board and the key plate above.
  A column is vertical: the main board's mount no longer moves toward the mouth
  at the first thumb row. The key board's mount moves instead
  (`boards.kb_end_margin`). The mouth pair and the tongue pair keep a nut.
  *"Main board mounts on the bottom plate"* gives the count, and *"columns
  vertical: the main board's mounts under the key boards'"* the check.
- **The U-bolt's backplate and the under-board washer are gone** (point 7).
  The bottom plate takes the legs, and a spacer faced to the plates' spacer
  length fills the gap to the board (*"main board in the U-bolt's clamp"*).
  The board has no lid-screw notches left to narrow the station
  (*"main board neck at the U-bolt station"*).
- **Grounding** (point 6): every mount is a plated `PWR_GND` hole with pads on
  both faces, footprint `MountingHole:MountingHole_2.7mm_M2.5_Pad_TopBottom`.
  They bond the bottom plate, and through the columns the key plate too. The
  key boards' mounts are all unplated (ADR 0020 Amendment 7).
- **The underside faces the plate everywhere.** A part on the underside needs
  a window through the bottom plate (ADR 0025, *Consequences*).

Supersedes point 3, point 7's backplate and washer, point 8's two stacks and
its nudge of the main board's mount, and the Consequences bullets on the oak
mounts' parts, the oak's blind holes and the backplate. Each is marked in place.
