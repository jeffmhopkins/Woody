# 0031 — The body is two glued L's, finger-jointed at all four corners, the lid held by magnets

**Status:** Accepted, 2026-11-22. Decided by the owner, in the working chat.
Tracked in #58. It amends [ADR 0025](0025-the-cassette.md) (how the shell
closes round the cassette, and how it is opened) and
[ADR 0009](0009-enclosure-construction.md) (the adhesives' table, the lid's
joints); each carries a dated note pointing here.
**Amended 2026-11-23** by the owner, in the working chat: the fingers'
inside corners are square, cut on end (point 2); and each magnet pulls on
the flush head of a stud in the key plate, the column screws having moved to
the back ([ADR 0025](0025-the-cassette.md), *Amendment, 2026-11-23*; points
5 and 6).

## Context

Since ADR 0025 the body has been glued shut. The cassette is bonded with RTV
to the oak top and to the oak bottom, the oak top's joints at the side grooves
are glued, and service is by cutting the silicone. How the end caps are held
was left open in ADR 0025's table.

The owner, 2026-11-22, asking for the body CAD to be finished:

> "I want to focus a little bit about how we actually construct this. We
> would make the inside carrier... And maybe the back of the instrument and
> the bottom of the instrument with the [etherCON], and have that secured.
> That makes an l. And then we do the same for the top And front to make
> another l. But then we need some kind of fasteners to basically screw those
> two L's together with the acrylic. And also be able to handle the things
> like the matrix carrier and all that ... really focus on how we do the
> final assembly and have it able to be taken apart"

Three places for the fasteners' heads were put to the owner: four screws on
the key face, down into four of the columns; the end faces only; or long
screws from the back. The owner's answer:

> "I feel like we could have the L's glued. And then two fasteners coming in
> from the mouth side and the [etherCON] side to hold the L's together. Would
> that work?"

That was modelled: a screw through each end cap, one into a clinch nut in the
key plate and one into an insert in an oak block, then more screws at the
owner's word to hold each L's own corner. The owner, the same evening, on
seeing it drawn:

> "Okay I'm not liking this. We need a different solution. I'm okay with
> machining the joints to be finger at glued l"

and, of the nut in the key plate, *"I'm concerned with the aluminum plate
being not sturdy enough here"*. Then:

> "Okay, let's just remove all the fastener nonsense. Let's just go into
> finger joints all around"

Told that dry finger joints locate a lid but do not stop it lifting, and
offered hidden magnets, a snug fit alone, or gluing the body shut:

> "I agree rare Earth magnets for the top plate. Good to model those in.
> You'll need to source the magnets to make sure that we're using the
> correct size"

## Decision

1. **Two glued L's.** Read with the instrument held upright:
   - the **back L** is the oak bottom and the tail cap. It carries the
     cassette, bonded to the oak bottom's inside face as ADR 0025 has it and
     clamped by the U-bolt, and on the tail cap the etherCON with its adapter
     and the MIDI jack;
   - the **front L** is the oak top and the mouth cap. It carries the Matrix
     on its carrier, on the inserts already in the oak top (ADR 0021,
     amendment 2026-10-03), and the breath inlet.

   The acrylic sides stand in the back L's grooves, glued there as before,
   and the front L's grooves come down over them.
2. **All four corners are machined finger joints** (`config/body.yaml`
   `closure.finger_*`; *"closure: finger joints at all four corners"*). The
   body's width is cut into divisions; each cap keeps the outer ones, so the
   body's corners stay the cap's and the sides' grooves end against it, and a
   panel's fingers run out through the cap's thickness. Every inside corner
   is square: the fingers are cut in a second setup with the part stood on
   end, a straight bit along the fingers and passing right through the
   thickness, so the bit's flat end forms the corner (owner, 2026-11-23:
   *"I'm not sure why the finger are not straight cut and they have the
   little radiuses in the corners"*, *"I feel like you just need to re-clamp
   it in another direction and the router should be able to do it?"*;
   `closure.finger_relief_d`). A dovetail bit was asked about and not taken:
   it would make them dovetails, small and fragile at this size (owner:
   *"Okay, keep finger"*). The
   MIDI jack sits low enough in the tail cap that its counterbore keeps oak
   between itself and the lid's notches, so every corner has all its fingers
   (owner, 2026-11-23: *"Seems like we should be able to move the TRS midi
   Jack down lower to get that extra finger in?"*; *"MIDI jack in the tail
   cap"*).
3. **Each L's own corner is glued; the two corners where the L's meet are
   dry.** Glued: oak bottom to tail cap, oak top to mouth cap. Dry: oak top
   into the tail cap, oak bottom into the mouth cap. The dry notches open the
   way the lid comes off, so the front L lowers straight down onto the back L
   and its fingers hold it against moving along or across the body.
4. **Nothing is bonded between the L's.** The key plate's top face is not
   bonded to the oak top, and the oak top's grooves are not glued to the
   sides. The oak top rests on the key plate.
5. **Magnets hold the lid down** (`closure.magnet_*`; `MECH-LID-MAGNET`;
   *"closure: lid magnets over the key plate's studs"*). A neodymium disc is
   glued to the floor of a blind pocket in the oak top's underside over each
   column, and pulls on the steel head of the stud pressed flush into the key
   plate there (ADR 0025, *Amendment, 2026-11-23*; until then it pulled on a
   column screw's head, across a gap, from a deeper pocket). The magnets are
   spread along the lid's length and nothing shows on the lid. **The studs
   must be the steel part, not the stainless one** (`MECH-MB-STUD`).
6. **No screw, nut, insert or block closes the lid.** The end caps carry no
   fastener. What ties the lid to the back L is the magnets' hold on the key
   plate and the column screws from the back, which clamp the oak bottom
   (ADR 0025, *Amendment, 2026-11-23*).
7. **Between the L's there are two connections**, both made with the lid
   held raised: the Matrix ribbon at `J-MCU` (*"Matrix ribbon length"*,
   unchanged) and the breath tube onto the inlet's inner barb.

## Options considered

- **Screws through the key face into the columns.** Four heads on the playing
  face. Not chosen: the owner asked for the end faces.
- **One screw through each end cap**, into a clinch nut in the key plate at
  the mouth and an insert in an oak block at the tail. Modelled, and
  withdrawn by the owner: the nut hung from a thin plate a long way from its
  nearest column, and each addition to make the L's own corners sound was
  another fastener.
- **A flat lid on a tray**: both caps joined to the oak bottom, a wood block
  with an insert under each end of the oak top. It would have cost body
  length or a cap glued on after the electronics went in.
- **A snug fit alone**, or **glued shut**. Offered with the magnets; the owner
  chose the magnets.

## Consequences

- **Opening the body takes no tool.** Pull the front L straight up off the
  magnets, unplug the Matrix ribbon and pull the breath tube off its barb.
  The cassette is then open from above as ADR 0025 describes: eight column
  screws free the key plate and both key boards.
- **Assembly.** The back L is glued up at its finger joint, with its sides;
  the cassette, tested on the bench, is set down between them and slid toward
  the tail, `J-UMB` into the adapter's socket - the back L has no mouth cap,
  so it is open at that end and there is room to slide - then bonded to the
  oak bottom and clamped by the U-bolt. The front L is glued up at its finger
  joint, the magnets glued into their pockets and the Matrix carrier screwed
  to its inserts. The ribbon and the tube are connected and the front L
  lowered over the sides and the switches. The keycaps go on last, through
  the oak's slots.
- **The joints show.** The fingers are visible on the playing face, the
  back and both end faces; so are the column screws' heads on the back.
- **The fingers want a second setup.** The two long panels are held on end
  under the router, which the shop's machine must allow; the caps go in a
  vise.
- **The wood over each magnet** is printed by the rule against
  `hardware.col_pocket_skin`.
- **The cassette's height against the shell's is no longer taken by a bead
  on top.** The oak top sits on the key plate, so the sides' height in their
  grooves must let it (*"cassette height at the hardware's tolerance
  limits"*; ADR 0025's open row).
- **The mouth cap's pull is the lid's.** Nothing pulls on that cap but the
  breath tube and a player's mouthpiece; the umbilical's pull is on the tail
  cap, which is glued to the oak bottom through its fingers.

## Open, and what decides each

| Item | Decided by |
|---|---|
| Whether the magnets hold enough. `closure.magnet_hold` is the maker's figure for direct contact with thick steel; here each pulls across `closure.magnet_recess` onto a stud head smaller than itself, and no sheet gives that | M4: one magnet glued into an offcut's pocket over a stud pressed into a plate offcut, and the pull measured. If it is too little: a thicker disc |
| The fit of a dry finger joint, `closure.finger_fit`: loose enough to lift after the oak has moved with the seasons, tight enough not to rattle | A test joint cut in the chosen oak on the shop's machine |
| Whether the shop's machine can hold the two long panels on end for the fingers. If not, `closure.finger_relief_d` takes the bit's diameter and round reliefs return | The shop's fixture |
| Whether the magnets disturb anything. No part in the body is known to sense a magnetic field - the keys are switches, the breath sensor is a pressure die - but no sheet was read for it | A read of each part's sheet at M4, and the breath zero watched with the lid on and off |
| Whether the bottom plate stays bonded to the oak bottom, or is screwed to it so the main board comes out without cutting | Owner, after the first assembly (ADR 0025's open row) |
