# 0030 — The key boards are laid out by hand, over one whole ground plane

**Status:** Accepted, 2026-11-20. Decided by the owner, in the working chat,
across one review of the left-hand key board's placement and copper (below);
amended the same day for the Matrix carrier (*Amendment* below).
Tracked in #48. It sets ADR 0029's routers aside for the boards laid out under
it; the main board is not yet one of them (*Open*).

## Context

The left-hand key board's first layouts were routed by this repository's own
routers (`tools/pcb_route*.py`, ADR 0029). The result passed every check and
read badly: signal and power lines changed face through vias to get past each
other, ground ran as tracks, and the chain's lines wrapped the register and
the header they came from.

The owner asked for the boards to be made again, and for one thing first,
2026-11-20: *"I want to make sure fable will do the traces by hand?"*

`key-board-lh` was the pilot. Its placement was shown before any copper, then
its copper, and each of the rules below came out of the owner's review of
one or the other.

## Decision

1. **No router of any kind lays these boards' copper.** Not this
   repository's, not Freerouting, not KiCad's. Each board has a script beside
   it (`hardware/boards/key-board-lh/lh_layout.py`) that places every part and
   writes out every track and via, with the reason for each. The script is
   the record of the layout and rewrites the `.kicad_pcb`.
2. **Placement is reviewed before copper.** The floorplan comes from the
   register's pinout, and the owner sees it before a track is drawn.
3. **The switch-side face is the ground plane, and it is whole.** No signal
   or power copper is on it.
4. **The parts face has no pour.** The owner, of the fill the tracks had cut
   into regions joined by necks: *"if we had the ground plane on the bottom,
   we don't need to fill in the top layer correct?"* Correct: a second fill
   adds nothing to a whole plane under lines this slow. Every ground pad
   reaches the plane by its own short way, a neck to a through-hole ground
   pin or a via.
5. **The plane meets every pin it joins through relief spokes.** The owner:
   *"Do the resistors that land on ground need their own ground pad so they
   can actually be soldered?"* The first layout's zones relieved only
   through-hole pads.
6. **Nothing passes between a switch's pin and its pole.** The owner, of the
   key line that did: *"Each of these need work too"*. Each key's series
   resistor and capacitor stand outside the switch's pins, beside them, and
   the key line leaves the end of the node that faces the register.
7. **Lines turn at 45 degrees and cut their corners as far as what stands
   inside allows.** The owner asked for it of the key lines and then of the
   3V3 rail.
8. **The left hand's chain headers face the mouth** (ADR 0017, *Amendment,
   2026-11-20*), which is what lets the chain's lines run straight from the
   header under the register.

The owner, of the board these rules gave: *"Nice! I think that looks much
better."*

## Options considered

- **The 3V3 rail on the switch side** (the owner's question, when the rail
  was cutting the parts-face fill). Not taken: it costs a via at every
  pull-up and a slot the length of the board in the one whole plane. Removing
  the parts-face fill removed the reason for it.
- **One short switch-side link under LH4's key line**, so the rail need not
  ring LH4. Laid and then withdrawn for the same reason: with no fill, the
  ring encloses nothing.
- **A fill keep-out round the register.** Laid and then withdrawn with the
  fill itself.

## Consequences

- `hardware/boards/key-board-lh/layout.yaml` no longer carries a placement or
  a routing order, and `tools/pcb.py layout` is not run on that board.
- The board's README lists the rules under *How this board is laid out*; the
  next boards start from it.
- The main board's `J-CHAIN-LH` and the body CAD's fold turned with the
  header; the main board fails its header position check until it is laid
  out again.

## Amendment, 2026-11-20 — the Matrix carrier, and the order of its ribbon's pins

The Matrix carrier carries nothing but connections, and its first layout
needed both faces and a ladder of vias for them. The cause was not the layout:
the ribbon's pins arrived at `J-MCU-C` in an order that crossed on the way to
the Matrix's pad rows, whatever was drawn. The owner was asked whether to
re-order the ribbon's pins so the carrier routes without crossings, and chose
**"Re-order the ribbon pins"**; shown the result, *"Awesome. Lock that in"*.
The owner had already said of the main board, the ribbon's other end, *"if we
need to relay out the order for the header pins to make it route better we can
do that too"*.

1. **The carrier sets the ribbon's pin order.** The table is in
   `hardware/boards/matrix-carrier/README.md`, *The ribbon's pins*, and the
   sheet `matrix-carrier.kicad_sch` owns it. The main board's `J-MCU` takes
   pin 25 − *k* for `J-MCU-C` pin *k*, as before (ADR 0021, *Amendment,
   2026-10-03*); only which line is on which conductor has moved.
2. **Every line on the top face, the bottom face one whole ground plane.**
   One via, the Matrix's ground pad's. `carrier_layout.py` writes out every
   track and replaces `carrier_routes.py`.
3. **The three 5 V pins stay three and the four ground pins stay four.** One
   5 V pin moved rows so the front row's lanes fit; a ground pin still sits
   between every two signal lines of the back row.
4. **Two things this layout does that the key boards' do not**, both for want
   of room at a 1.27 mm header: three lines neck to the layout's `track_min`
   through one gap in the near pad row, and `J-MCU-C`'s four ground pins join
   the plane whole, with no thermal spokes. The owner was told of both with
   the trial.

**What this breaks until the main board follows.** `J-MCU`'s sheet
(`hardware/carrier/carrier.kicad_sch`), its notes, `hardware/carrier/midi-out`
and ADR 0018's account of pins 23 and 24 still describe the old order, and
`tools/kicad.py check` fails on the ribbon's two ends. They are the main
board's and move with its new layout, in the same change as its `J-MCU`.
`docs/log/2026-11-20-main-board-handover.md` lists them.

## Open, and what decides each

- **Which boards this covers.** The Matrix carrier is done (*Amendment*
  above). The main board is next
  (the owner, 2026-11-20: *"We'll be redoing the main board as well"*).
  The owner has not yet said whether the module's boards follow. The owner
  decides.
- **Grounding the key boards' mounts.** The owner, 2026-11-20: *"I think the
  standoffs can actually be part of the ground plane?"* Not done: ADR 0020
  Amendment 7 leaves all four unplated because the columns already tie the
  key plate to the main board's ground, and a second tie at the key board
  closes a ground loop through the ribbon (ADR 0020 Amendment 5). The owner
  decides whether to amend that.
