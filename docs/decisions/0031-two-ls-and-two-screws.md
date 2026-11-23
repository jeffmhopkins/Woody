# 0031 — The body is two glued L's, held together by one screw through each end cap

**Status:** Accepted, 2026-11-22. Decided by the owner, in the working chat.
Tracked in #58. It amends [ADR 0025](0025-the-cassette.md) (how the shell
closes round the cassette, and how it is opened) and
[ADR 0009](0009-enclosure-construction.md) (the adhesives' table, the lid's
joints); each carries a dated note pointing here.

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

## Decision

1. **Two glued L's.** Read with the instrument held upright:
   - the **back L** is the oak bottom and the tail cap, glued. It carries the
     cassette, bonded to the oak bottom's inside face as ADR 0025 has it and
     clamped by the U-bolt, and on the tail cap the etherCON with its adapter
     and the MIDI jack;
   - the **front L** is the oak top and the mouth cap, glued. It carries the
     Matrix on its carrier, on the inserts already in the oak top
     (ADR 0021, amendment 2026-10-03), and the breath inlet.

   The acrylic sides stand in the back L's grooves, glued there as before,
   and the front L's grooves come down over them.
2. **Nothing is bonded between the L's.** The key plate's top face is no
   longer bonded to the oak top, and the oak top's grooves are no longer
   glued to the sides. The oak top rests on the key plate.
3. **One screw through each end cap holds the L's together**
   (`config/body.yaml` `closure`; `MECH-CLOSE-SCREW`):
   - **at the mouth**, through the mouth cap, which is the front L's, into a
     PEM right-angle clinch nut pressed into the key plate's mouth end, which
     is the back L's (`MECH-CLOSE-NUT`). The main board fills the bottom of
     the mouth end, so the key plate is the only part of the back L there to
     thread into;
   - **at the tail**, through the tail cap, which is the back L's, into a
     threaded insert in the end of an oak block glued under the oak top, which
     is the front L's (`BLOCK-CLOSE-LID`, `MECH-CLOSE-INSERT`). The block
     stands in the lane beside the etherCON that the MIDI jack does not use.

   The breath inlet has the mouth cap's centre and the etherCON the tail
   cap's, so neither screw is on the centreline, and the breath sensor and the
   MIDI jack put both toward the same long edge (*"closure: the two end
   screws"*).
4. **Each screw's head sits in a flat pocket cut from outside**, leaving
   `closure.panel` of oak under it. The tail screw's pocket is the etherCON's
   recess, widened round the screw, so no fin of oak stands between them
   (*"closure: oak under each screw's head"*, *"closure: tail screw pocket in
   the tail face"*, *"closure: mouth screw pocket clear of the breath
   inlet"*).
5. **Two corner blocks in the back L, each screwed through the tail cap.**
   An oak block is glued to the oak bottom and the tail cap in each lane
   beside the etherCON, and a screw through the tail cap threads into an
   insert in each block's end. The owner asked for more fasteners in the end
   pieces the same day: *"We can do four fasteners on each end piece, to them
   helps secure the wood and stronger during the l and glue."* The blocks
   carry the umbilical's pull from the tail cap into the oak bottom, and the
   screws clamp that joint while its glue sets and back it up after
   (`BLOCK-CLOSE-CORNER`; *"closure: corner screws in the tail face and their
   blocks"*). **The tail face takes three screws, not four:** the fourth
   corner is the MIDI jack's (issue #45). **The corner screws stay in:** the
   body opens by the lid screw above the near one, and the mouth screw. The
   front L's corner has no block: the key plate lies directly under the oak
   top at that end.
6. **Three wood screws through the mouth cap into the oak top's end**, for
   the same request. Offered small wood screws, glue alone, hidden dowels
   and, when they asked *"what if we dove tail?"*, an interlocking corner, the
   owner chose: *"Lets do the the screws."* Asked whether they could run in
   threaded inserts so nothing bites the wood: not in a panel this thin - an
   insert is wider than the screw and leaves less oak either side of it -
   and these are driven once into a glued joint and stay in. Every screw
   that is undone to open the body threads into metal (`MECH-CLOSE-PIN`;
   *"closure: mouth cap's wood screws into the oak top"*).
   **Finish** (owner, same day): *"black oxide stainless would be better,
   brass as alternate."* That is every screw head the end caps show.
7. **Between the L's there are two connections**, both made with the lid
   held raised: the Matrix ribbon at `J-MCU` (*"Matrix ribbon length"*,
   unchanged) and the breath tube onto the inlet's inner barb.

## Options considered

- **Four screws on the key face, into four of the eight columns.** The
  columns already stand under the oak top at eight points, so this clamps the
  lid along its length with parts the design has. Recommended to the owner as
  the first option; the owner chose the end faces, which keep the playing
  face unbroken. It stays the fallback (*Open*, below): a column's blind
  pocket becomes a through hole, and nothing else moves.
- **Long screws from the back into inserts in the oak top.** Only the tail
  lane has a clear path from face to face. Everywhere else the main board is
  in the way, and its copper is finished.
- **Keep the RTV.** It is what the owner asked to replace: the body is to
  come apart and go back together.

## Consequences

- **Opening the body is two screws.** Undo both, lift the front L straight
  up off the sides, unplug the Matrix ribbon and pull the breath tube off its
  barb. The cassette is then open from above as ADR 0025 describes: eight
  column screws free the key plate and both key boards.
- **Assembly.** The back L is glued up with its two corner blocks and its
  sides, the corner screws drawing the tail cap onto the blocks as its clamp;
  the cassette, tested on the bench, is set down between them and slid toward
  the tail, `J-UMB` into the adapter's socket - the back L has no mouth cap,
  so it is open at that end and there is room to slide - then bonded to the
  oak bottom and clamped by the U-bolt. The front L is glued up with its block, and the Matrix carrier
  screwed to its inserts. The ribbon and the tube are connected, the front L
  lowered over the sides and the switches, and the two screws put in. The
  keycaps go on last, through the oak's slots.
- **The mouth screw's pull goes through the cassette.** The mouth cap is
  drawn against the key plate's mouth edge, and the key plate holds the front
  L to the back L through the columns, the bottom plate and its bond to the
  oak bottom. So that bond and the U-bolt's clamp are now part of how the
  body closes, and ADR 0025's open question, whether the bottom plate's bond
  is ever cut in ordinary service, matters more: with the lid off, the main
  board comes out only with the bottom plate.
- **The key plate has one more hole**, rectangular, for the nut, and the
  plate vendor presses the nut as it presses the studs.
- **ADR 0025's "nothing screws into the wood" holds for the playing face and
  the back.** The screws that open the body pass through the end caps and
  thread into metal. Only the mouth cap's three wood screws thread into
  wood, in a glued joint, and they are not undone.
- **The cassette's height against the shell's is no longer taken by a bead
  on top.** The oak top sits on the key plate, so the sides' height in their
  grooves must let it (*"cassette height at the hardware's tolerance
  limits"*; ADR 0025's open row).

## Open, and what decides each

| Item | Decided by |
|---|---|
| Whether the lid needs holding down between its two screws. Nothing does over *"closure: lid span between its two screws"*, the oak beside the cap slots is two narrow rails, and both screws are toward one long edge. If it lifts or buzzes, hidden column screws become lid screws (*Options considered*) | M4, the first assembly |
| The right-angle nut's drawing. Its catalogue page gives the lettered dimensions without the drawing that says which face each one measures, so every `closure.nut_*` figure is `tbd` and says how it was read | PEM bulletin RA, fetched by hand and banked (`datasheets/.manifest-R63-issue58-body-closure.csv`, the `BLOCKED` row) |
| Whether `closure.panel` of oak under a screw head takes repeated closing, or wants a metal seat | M4, with the caps cut |
| The insert in the lid's block: sold for plastic, set in oak with epoxy as the Matrix carrier's are | An insert set in a block of the chosen oak and pulled |
| Whether the bottom plate stays bonded to the oak bottom, or is screwed to it so the main board comes out without cutting | Owner, after the first assembly (ADR 0025's open row) |
| The glue for each L's corner, and whether the front L's corner needs a block as the back L's has | M4, on the first glue-up |
| Whether a 2 mm wood screw goes into the end of the chosen oak top without splitting it (`closure.pin_d`, `tbd`) | M4: a pilot drilled and a screw driven into an offcut's end |
