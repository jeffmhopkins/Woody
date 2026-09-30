# 0025 — The cassette: the internals are one bonded unit, dropped into the shell

**Status:** Accepted, 2026-09-29. Decided by the owner. It amends
[ADR 0009](0009-enclosure-construction.md) (how the body closes and opens),
[ADR 0020](0020-key-boards-screw-to-the-plate.md) (how the key boards are held,
and Amendment 5's ground bond) and [ADR 0022](0022-main-board-mount.md) (how the
main board is held); each carries a dated note pointing here.

## Context

Until this decision the body closed on six M3 screws. They came up through
counterbores in the oak bottom and threaded into the key plate (ADR 0009, *The
body comes apart*). The lid was the oak top bonded to the key plate, with the
key boards hanging from studs pressed into the plate (ADR 0020, Amendment 4).
The main board stood on two thumb plates and, where no thumb plate was under
it, on threaded inserts in the oak bottom (ADR 0022). The U-bolt clamped its
own backplate. The lid came off with the key boards plugged in, and was laid
beside the body.

The owner, 2026-09-29:

> "I think overall if the insides were aluminum plate to aluminum plate, all
> one solid piece with standoffs in between the boards and the aluminums, that
> we could just drop it into the instrument with a little bit of silicone to
> glue it to the top and bottom wood and when everything is clamped down and
> glued in place for the acrylic etc. You would all be good so no need to like
> screw into the wood except for maybe the u-bolt."

And, answering the follow-up questions:

- **Service is by cutting the silicone.** The body is glued shut, and nothing
  screws into the wood.
- **The plates are tied by continuous columns.**
- "The double columns going up in the center of the board that are outside of
  the top pcbs, shouldn't need to be there ... we can just have just the holes
  for the u-bolt, and then rely on the stackups to the top boards for the
  rigidity. Once fully assembled, the whole thing is going to be in wood anyway
  and that is the main structure." The middle station keeps the U-bolt and
  nothing else.

## Decision

1. **The cassette.** The key plate, one bottom plate, the two key boards and
   the main board, tied into one unit by eight columns. It is built and tested
   on the bench with its ribbons plugged, dropped into the shell, and bonded
   with RTV silicone: the key plate's top face to the oak top's underside, and
   the bottom plate's underside to the oak bottom's inside face. **No height
   changes.** The key plate and the bottom plate stay where the key plate and
   the thumb plates were, because the flush-key rule puts them there (ADR 0009).
2. **One bottom plate** (`PLATE-BOTTOM`) replaces the two thumb plates. It is
   the same 1.20 mm aluminium, in the same place, on the oak bottom's inside
   face. It carries the thumb switches' cutouts, as the thumb plates did, the
   U-bolt's leg holes, and a stud at every one of the main board's mounts. It
   runs from the mouth cap to just short of `J-UMB` at the tongue's end.
   `J-UMB`'s through-hole tails stand below the tongue, and behind it the
   etherCON's adapter stands on the oak (`mechanical/export/plate-bottom.dxf`).
3. **A column at each of the key boards' eight corners.** From the bottom:
   - a PEM FHL-M2.5-10 stud pressed into the bottom plate, its head flush in
     the plate's underside (`MECH-MB-STUD`);
   - a spacer (`MECH-MB-SPACER`);
   - the main board;
   - an M2.5 female-female hex standoff, threaded onto the stud and clamping the
     main board. It is faced to the gap up to the key board
     (`MECH-COL-STANDOFF`; `mechanical/drc.echo` *"column standoff length
     (derived)"*). That length is not stocked, so it is bought at the next stock
     length and faced, as ADR 0023 does for `MECH-STANDOFF-MOD`;
   - the key board;
   - a spacer (`MECH-KB-SPACER`), which sets the key board's depth as before;
   - the key plate, through a clearance hole;
   - an M2.5 low-head screw, down into the standoff's top (`MECH-COL-SCREW`).

   The screw's head sits in a blind pocket drilled up into the oak top's
   underside. The oak top's DXF carries through-cuts only, so the pockets are
   exported on their own (`mechanical/export/oak-pockets.dxf`), like the side
   grooves and the window's rebate. The screws go in before the oak top goes on.

   **A column is vertical.** The main board's mount is the key board's mount,
   at the same place. The column nearest the mouth in each hand stands over the
   first thumb row, where ADR 0022 point 8 had moved only the main board's
   mount toward the mouth. Now the key boards' mouth ends move instead
   (`boards.kb_end_margin`; *"columns vertical: the main board's mounts under
   the key boards'"*). The tail corners' pockets must keep wood from the last
   keys' cap slots, and that lengthens the tail ends a little
   (`boards.kb_tail_margin`; *"key-board tail margin, least"*).

   Each end of the standoff has thread for its part. The stud goes up into it
   and the screw comes down into it, each by at least
   `hardware.thread_engage_min` diameters at its shortest. The two never meet
   inside it (*"column: stud thread in the standoff"*, *"column: screw thread
   in the standoff"*, *"column: stud and screw ends apart in the standoff"*).
4. **The main board's other mounts are on the bottom plate too.** There is a
   pair at the mouth and a pair on the tongue (ADR 0022 point 8), each a stud,
   a spacer, the board and a nut (`MECH-MB-NUT`). The oak mounts are gone:
   no insert, no oak spacer, no screw into the wood. The count is *"main board
   mounts on the bottom plate"*.
5. **The six M3 body fasteners are gone,** with everything that existed only
   for them:
   - the screws, and their counterbores in the oak bottom;
   - their tap holes in the key plate;
   - their clearance holes;
   - the main board's edge notches (it has none now);
   - the fastener window across the body (`hardware.fastener_inset`);
   - the lane rules that kept things off them;
   - the space the last pair took in front of the tail equipment.

   With that space gone, the length the model derives is a little shorter
   (*"overall length (derived)"*).
6. **The U-bolt.** Up each leg go:
   - the oak bottom;
   - the bottom plate;
   - a spacer, faced to the plates' spacer length (Ettinger 5.53.015,
     `MECH-UBOLT-SPACER`);
   - the main board;
   - a washer;
   - the nyloc.

   The backplate is gone (`MECH-BACKPLATE`), because the bottom plate spreads
   the load. *"Main board in the U-bolt's clamp"* holds the spacer to the gap.
   The middle station has only the two leg holes through the main board.
7. **Grounding: both plates are grounded in one place, the main board's
   `PWR_GND`.** Every mount on the bottom plate is a plated hole with a
   `PWR_GND` pad on both faces (ADR 0022 point 6). The footprint is
   `MountingHole:MountingHole_2.7mm_M2.5_Pad_TopBottom`, the footprint the key
   board's bond was proven with. ADR 0022 named `_Pad_Via`, whose ring of vias
   breaks the board house's hole-to-hole rule. The bond runs this way:
   - the stud's clinch and the spacer's face bond the bottom plate;
   - each column's screw, standoff and stud tie the key plate to the same pads.

   **Every key-board mount is unplated** (NPTH, with its copper keep-out).
   Neither plate touches a key board's `GND_CHAIN`, so no ground loop runs
   through a ribbon. ADR 0020 Amendment 5, the one plated mount on the
   left-hand key board, is superseded. The left-hand board is laid out again
   without it. `tools/pcb.py` keeps its `bond_mount` feature, which is general,
   and no board uses it now.
8. **The key-chain ribbon is as long as the cassette's service needs.** It is
   no longer as long as a lid laid beside the body needs
   (`routing.chain_service`, `routing.chain_raise`). Assembly and service
   both come down to screwing the key plate onto its columns, or taking it
   off. So the key plate, with both key boards on it, is held raised off its
   columns while a hand plugs or unplugs the main board's sockets. Then it is
   lowered and screwed down, and the ribbon folds itself into its hairpin
   (*"key-chain ribbon length (derived)"*).

   A ribbon long enough to lay the plate beside the body would close into a
   hairpin about as long as before. That hairpin runs into the left-hand
   board's tail column, which now stands through the whole gap the hairpin
   lies in. With a column there, no header position on that board both clears
   the columns and takes a hairpin that long (*"key-chain ribbon hairpin clear
   of the columns"*).

   The shorter hairpin changes where the model's own rule puts each board's
   `J-CHAIN`: nearest its keys' middle (`pcb-geometry.echo`), so both key boards
   are laid out again.

## Options considered

- **Keep the six fasteners and add the columns.** That would keep a body that
  opens with a screwdriver. It would also keep six holes in the wood, the
  counterbores beside the side grooves, the fastener window that sized the
  U-bolt, and the main board's notches, which is everything the owner asked to
  drop.
- **Keep ADR 0022's split mount** (studs on the thumb plates, inserts in the
  oak). The owner asked for nothing to screw into the wood. A column cannot
  stand on an insert in oak and still tie the plates together.
- **A column in the gap between the hands, beside the U-bolt.** The owner:
  it should not be there. The stack under the key boards gives the rigidity,
  and the U-bolt's clamp holds the main board in the middle.

## Consequences

- **Service is by cutting silicone.**
  1. Cut the oak top free. That means its bead to the key plate and its joints
     at the side grooves, which are glued now, not a gasket.
  2. Undo the eight column screws.
  3. Raise the key plate with both key boards off the columns and unplug the
     ribbons.
  4. Undo the U-bolt's nylocs.
  5. To take the whole cassette out, cut the bottom plate's bond as well.

  The cassette goes back with fresh beads. ADR 0009's lid screws and gasket
  are gone, and so is its promise that the body opens with a screwdriver.
- **Assembly and test happen on the bench, before anything is closed.**
  1. Clip the switches into both plates.
  2. Press the studs into the bottom plate. The plate vendor does this, as
     for any PEM part.
  3. Put a spacer on each stud, then the main board, soldered to its thumb
     switches, then the standoffs, tightened to no more than
     `hardware.stud_torque`, and the end mounts' nuts.
  4. Plug the ribbons with the key plate raised. Lower it with its spacers
     and screw it down.
  5. Solder the key switches once the hardware has fixed their depth.

  The cassette is then a working instrument without its wood. It is flashed,
  played and metered (both plates to `PWR_GND`) before the shell is closed
  round it.
- **The Matrix is not in the cassette.** It sits under the oak top's window
  (ADR 0009), so it belongs to the oak top, and it reaches the cassette only
  by `CBL-MCU-RIBBON` into `J-MCU`. For the bench test it is plugged in with
  the oak top held over the cassette, or before it is fixed into the oak top.
  `J-MCU` is the last plug before the oak top is bonded, and the first thing
  unplugged once it is cut free. Every page that says "with the lid off" now
  means with the oak top cut free. The ribbon's length rule is unchanged
  (*"Matrix ribbon length"*, `CBL-MCU-RIBBON`).
- **The shell is the structure; the cassette only has to survive the bench.**
  A key press goes from the switch into the key board and the plate, down the
  columns in compression to the bottom plate, and into the oak bottom. Before,
  it hung the key plate from the oak top's silicone.

  ADR 0009 has a sentence that the plate "is pushing *into*" its silicone
  layer under a key press. That was written for a plate on top of the wood.
  It has not held since the plate went under the oak top (2026-09-26), where a
  press pulls the plate away from the wood. The columns now take that load,
  and ADR 0009 carries a note.
- **Tolerance: the silicone takes the oak's, and the standoffs take the
  boards'.** The cassette's height is fixed by its parts, and the shell's by
  the oak and the grooves. The beads fill the difference.

  Most of the cassette's own tolerance is the two boards' thickness
  (`boards.pcb_t_tol`). The one part made to length, the column standoff, is
  faced to the boards as measured. That leaves only the plates' and spacers'
  tolerance for the beads (*"cassette height at the hardware's tolerance
  limits"*).
- **The flush-key rule is untouched.** Both plates keep their heights, so the
  oak top and the oak bottom are still derived from the cap's height, and the
  keys and thumb keys are still flush at full travel.
- **The U-bolt pulls on the bottom plate.** The strap's pull goes from the
  legs through the nylocs, the washers and the main board, and the spacers
  put it into the bottom plate. The plate bears on the oak bottom's inside face
  over its whole area, not over a 16 mm backplate. So the oak under the
  U-bolt, which ADR 0009 called the weak link, is loaded far more gently. The
  cassette's own weight reaches the U-bolt through the columns and never
  through a bead.
- **The U-bolt could be M4 again.** The fastener window that forbade the wider
  span an M4's nuts need beside the LED strip is gone
  (`hardware.ubolt_rod_d`). It stays M3 until the strap hardware is chosen.
- **The main board's underside faces grounded aluminium over its whole
  length.** Before, much of it was over oak. An underside part or a
  through-hole tail now has the plate's gap less the parts clearance, which is
  nothing at `boards.board_clear` (*"main board underside room over the
  bottom plate"*). So an underside part, which ADR 0017's amendment allows,
  needs a window cut through the bottom plate under it. A window costs nothing
  on a laser-cut plate. `J-CHAIN`'s tails clear the plate (*"J-CHAIN pin tails
  clear of the bottom plate"*).
- **Both plates are bonded metal to metal.** The screws' heads bear on the key
  plate's top face, and the studs' clinches and the spacers are in the bottom
  plate. So both plates are ordered un-anodised, or masked round each column
  hole and each stud hole (`PLATE-TOP`, `PLATE-BOTTOM`).
- **The key boards grow slightly at both ends and are laid out again.** Their
  mounts are at the new corners. Their `J-CHAIN` headers are where the
  shorter ribbon lets the model put them, and the left-hand board has no bonded
  mount.

## Note, 2026-09-30 — one standoff where there were two

The owner, 2026-09-30:

> "there's one spot where we have double standoffs right next to each other,
> probably from top key board. Good to reduce it to the one standoff there"

The mouth end mount nearer the far edge stood beside the left hand's first
column, the one under the key board's mount. The column already holds the
board there, so the end mount is gone. The rule is general, so this cannot
come back: an end mount is dropped when a column's mount stands within
`hardware.end_mount_merge_d`. *"End mounts dropped beside a column"* in
`mechanical/drc.echo` names each one dropped and how far it stood from the
column, and *"main board mounts on the bottom plate"* gives the count that
`MECH-MB-STUD`, `MECH-MB-SPACER` and `MECH-MB-NUT` follow. The other mouth
end mount and the tongue pair stay.

The same day, on a marked-up render of the main board: *"I'm ok with it being
more narrow, but ... my red line is inset just slightly which is not
needed."* The tongue stays narrow, but on the side where it stepped in by a
millimetre and a half from the main board's edge it now runs flush
(ADR 0021's dated note; *"main board's tongue flush with its edge on the near
side of the adapter"*). The tongue's mounts do not move.

## Open, and what decides each

| Item | Decided by |
|---|---|
| The column standoff: across flats, material, and whether it is tapped through or deep enough from each end after facing (`hardware.col_standoff_*`; *"column standoff: thread it needs from each end"*) | M4, with the standoff bought (`MECH-COL-STANDOFF`) |
| The column screw: head and length tolerance (`hardware.col_screw_*`) | M4, with the screw bought (`MECH-COL-SCREW`) |
| `hardware.thread_engage_min`, 1.5 d from memory: an aluminium standoff wants more than brass or steel | M4, with the standoff's material known |
| How the silicone is cut: a wire drawn along the plate-to-wood bead and the groove joints, and whether the bottom plate's bond ever needs cutting in ordinary service | M8, on the mule |
| How the end caps are held. ADR 0009's table said "fasteners into the stack", which were never drawn, and the owner wants nothing screwed into the wood | Owner, with the caps cut (M4) |
| `routing.chain_raise`: how high a hand needs the key plate to reach the main board's sockets | M4, on the first assembly |
| The cassette's height against the shell's: the standoffs faced to the measured boards, and the bead's thickness | M4, on the first assembly |
| The U-bolt: M3, or M4 at a wider span now that no fastener window bounds it | M4, from the strap hardware chosen |
| Windows in the bottom plate under any underside part of the main board | The main board's layout |
