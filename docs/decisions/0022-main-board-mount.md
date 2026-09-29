# 0022 — How the main board is held, and how thick it is

**Status:** Accepted, 2026-09-29, as part of the owner's instruction to "finalize
everything and get us to the line before board layout". It settles
`switch.pcb_t` and `switch.thumb_pcb_below_seat`, which ADR 0020 point 6 and
`docs/reference/ks33-geometry.md` had left open until the main board's own
mount existed.

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
2. **Over a thumb plate it is held exactly as a key board is** (ADR 0020,
   Amendment 4), with the same parts:
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
3. **Where no thumb plate is under it, it stands on the oak**:
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
   and each stud a hole in its thumb plate.
5. **The thumb switches in the row nearer the centreline are turned 180°**
   (`config/key-layout.yaml`: LT1, LT3, RT1, RT3). A KS-33's pins sit off its
   centre. On the thinner board they stand proud of the top face, and in the
   near row they pointed at the LED strip's edge. Turned, they point away. A
   square cap on a cross stem feels the same either way.

## Consequences

- **The main board and the key boards share one stack** and one set of
  hardware on the plates. The oak mounts add three small parts
  (`MECH-MB-INSERT`, `MECH-MB-OAK-SPACER`, `MECH-MB-SCREW`, open until M4).
- **The board is 0.4 mm thinner and a long board**, about
  `mechanical/drc.echo` *main board* long. Where it spans between mounts it
  is carried by the soldered thumb switches, as before. The first board
  confirms how stiff that is.
- **The oak bottom gets blind holes for the inserts.** Like the counterbores
  they are not in its DXF, which carries through-cuts only; the body CAD
  places them.
- **The Matrix keeps its own thickness** (`boards.matrix_t`). It had been
  borrowing the main board's.

## Open, and what decides each

| Item | Decided by |
|---|---|
| The insert, the oak spacer and the screw: parts and lengths (`hardware.mb_*`) | M4, with the parts bought |
| Whether the long span sags between mounts | The first board |
