# 0021 — The instrument's etherCON is PCB-mounted, on an adapter joined to the main board

**Status:** Accepted. Decided by the owner, 2026-09-29. It settles ADR 0004's
open question *which etherCON variant at each end* **for the instrument's end
only**. The module's end is still open, as ADR 0004 left it.

## Context

The instrument's etherCON was a feedthrough (Neutrik NE8FDP, `J-UMBILICAL`)
with an RJ45 socket at its back. A short patch lead (`CBL-UMB-PATCH`) ran from
that socket to a latching header (`J-UMB`) on the main board. That added two
contact interfaces to every conductor of the umbilical, including the +12 V
path and the breath pair. ADR 0004 recorded that as the cost of the
feedthrough and deferred the choice. The patch plug and its boot were also
the longest item behind the last key, so they set the body's length
(`mechanical/drc.echo`, *what the tail end needs*).

Owner, 2026-09-29: *"it's about time that we convert the ethercon connector
to a PCB type, if we need to make a little adapter board to hook the flex
connector to that's fine, otherwise, it might just be easier to extend the
main board down and mount it directly to that."*

## Decision

1. **The instrument's etherCON is a Neutrik NE8FAV** (`J-UMBILICAL-INST`):
   an A-series receptacle for a vertical PCB, mounted from behind the panel.
   Its drawing, data sheet and 3D model are banked
   (`datasheets/connectors/NEUTRIK-NE8FAV-*`). Every number the body CAD uses
   is in `config/body.yaml` `ethercon:`, each with its source.

2. **It is soldered to a small board of its own, the umbilical adapter**
   (`PCB-UMB-ADAPTER`). The adapter stands parallel to the tail cap, the
   flange's outline in size. Its tracks run each etherCON pin to the
   same-numbered pin of `J-UMB`, and it carries nothing else.

3. **`J-UMB` is now a 1 × 8, 2.54 mm right-angle pin header, soldered into
   both boards.** Its short legs go through the adapter and its long legs
   through a **tongue of the main board** that runs from the main board's
   tail end to the adapter's rear face. Pin N is still etherCON pin N, so
   every "`J-UMB` pin N" on the carrier's pages still means the same
   conductor. There is no cable and no mated contact between the etherCON
   and the main board. `CBL-UMB-PATCH` is gone.

4. **Latch up.** ADR 0009 turned the NE8FDP 90° so that its 26 × 31 flange
   fitted the body's height. The NE8FAV's flange is square, so that reason
   no longer applies. The PUSH tab is on top, where a thumb finds it. The
   contact rows sit above the axis, which leaves the band below the axis
   for `J-UMB`'s row (`ethercon.rotated`).

5. **The tail cap has a recess from outside for it.** The NE8FAV allows a
   3 mm panel at most (`ethercon.panel_max`) and the oak cap is thicker, so
   a router pocket leaves exactly that much oak where the flange clamps. The
   recess takes the flange's outline, the PUSH tab and a margin
   (`ethercon.recess_margin`, decided with the cable connector in hand).
   Two of Neutrik's A-series screws go through its floor into the flange
   (`MECH-ETHERCON-SCREW`).

6. **Its two locating pegs are cut off flush.** They stand below the flange
   (`ethercon.peg_below`) and, with the connector on the floor latch up,
   point into the oak bottom. Drilling the floor for them would locate the
   connector a second time, against the cap's screws, across oak that moves;
   standing it higher would take more body than `body-thickness` has.

## Why not mount it on the main board directly

That was the owner's first suggestion, and the NE8FAH (the same connector
for a horizontal PCB) would do it. Both the NE8FAH and the NE8FAV put the
axis 12.5 mm above the flange's lower edge
[ds `NEUTRIK-NE8FAH-DRAWING.pdf`, `NEUTRIK-NE8FAV-DRAWING.pdf`]. On a
horizontal board that is also the height above the board's top face, and
the main board's top face is fixed by the thumb switches soldered into it
(`switch.thumb_pcb_below_seat`). The connector's body, a flange's height
above that face, would then stand 3 mm above the oak top's underside. Its
PUSH tab, which rises above the flange's outline, would stand about 7 mm
above it, through the cap's top edge [calc from `mechanical/drc.echo`'s
tail Z levels and the NE8FAH model]. The main board cannot drop at the tail
because it is one flat board, so the body would have to grow by at least
the first figure and the cap would lose its top edge to the second. The vertical-PCB part
on an adapter stands on the floor as the NE8FDP did.

A flex cable between the adapter and the main board was the other way to
join them. A right-angle header does the same job with no connector and no
cable. Its pins carry more current than the etherCON's own contacts do, and
ADR 0004 counted every contact interface as a cost.

## Consequences

- **Two contact interfaces fewer in every umbilical conductor**, and one
  cable fewer to make by hand.
- **The tail is shorter.** Removing the patch plug took away the claim that
  set the tail's length. The Matrix, centred after the keys, now sets it,
  and the body shortens by what `mechanical/drc.echo` *overall length*
  reports. The gap between the hands follows the keys-to-Matrix gap (owner,
  2026-09-26) and is now at its minimum, `layout.gap`. So the right-hand
  cluster moved toward the mouth. The left-hand ribbon's hairpin moved
  because it clears the lid screw between the hands. Both key boards were
  re-laid out from the body CAD.
- **The body could be thinner.** `mechanical/drc.echo` *body thickness takes
  the etherCON on the floor* reports the spare. `body-thickness` is the
  owner's figure and was not changed here.
- **The main board is longer, by the tongue.** The tongue is as wide as the
  adapter and notched where the last lid screws pass. It has standoffs
  under J-UMB's end.
- **Taking the main board out means unscrewing the etherCON from outside
  first.** The connector, the adapter and the board come out as one piece.
  The nose sits in the cap's bore, so the assembly slides back before it
  lifts.
- **The cable connector is unconfirmed.** The NE8FAV names "NE8MC* or any
  standard RJ45 plug" and excludes the NE8MC6-MO and NKE6S* cables. It does
  not name the NE8MX, the NE8MC's successor (`J-UMBILICAL-CABLE`).

## Open, and what decides each

| Item | Decided by |
|---|---|
| `J-UMB`'s part, and its insulator and row height (`boards.umb_joint_*`) | M4, with the part |
| The recess margin round the flange and the PUSH tab | M4, with the cable connector in hand |
| The mounting screws' part and length for a 3 mm panel | M4, with the connector |
| Whether the NE8MX latches in the NE8FAV | Before buying the cable connectors |
| The module's end | E12/M7 (ADR 0004) |
