# 0020 — The key boards are screwed to the key plate

**Status:** Accepted. Decided by the owner, 2026-09-27, and amended the same
day (points 3 and 6, and point 5's notes; *Amendment* below). **Amended twice more
on 2026-09-27**: *Amendment 2* made a screw down through a plugged bore in
the wood top the standard, and *Amendment 3* replaced the bore and plug
with a blind pocket drilled into the wood top's underside. **Amendment 4,
2026-09-28, replaced the screw with a PEM self-clinching stud pressed into the
plate, its head flush with the plate's top face**: nothing above the plate,
no pockets, no epoxy. PEM publishes the stud's data in a 1.2 mm aluminium
sheet, which the standoff this page first chose did not have. **Amendment 7,
2026-09-29 ([ADR 0025](0025-the-cassette.md)), is the current mount:** each
corner is a column from the bottom plate to the key plate, and the key board is
clamped in it by a screw down through the plate. Amendment 5's bonded mount is
superseded.

## Context

The left-hand key board's first layout (ADR 0019, `tools/pcb.py`) showed a
board with nothing holding it. The body CAD said the key boards "hang under
the plate", and nothing in the model or the BOM did the hanging. The switches'
pins are soldered to the board and the switches are clipped into the plate,
so the switches alone held it. Every key press would then push the board
off the clips through the solder joints. (Owner: "I don't see any way to
have standoffs connect to anything and I'm a little bit confused on how it
connects to the top face of the instrument".)

The same layout had placed the ribbon connector `J-CHAIN` in the CAD's
connector envelope using a stand-in size. The real footprint, a Molex 200528
12-way, did not match it.

## Decision

1. **Each key board is screwed to the underside of the key plate.**
   - An M2 self-clinching standoff is pressed into the plate by the plate
     vendor (`MECH-KB-STANDOFF`).
   - An M2 screw goes up through the board into it (`MECH-KB-SCREW`).
   - *(Superseded 2026-09-27 by Amendment 2: no standoff and nothing pressed
     into the plate. The screw comes DOWN through a plugged bore in the wood
     top and the plate, and a nut holds the board: `MECH-KB-SCREW`,
     `MECH-KB-SPACER`, `MECH-KB-WASHER`, `MECH-KB-NUT`, `MECH-KB-PLUG`.)*
     *(Amendment 3, same day: no bore and no plug — the screw drops through
     the plate before the wood goes on, and its head sits in a blind pocket
     in the wood top's underside. `MECH-KB-PLUG` is gone.)*
   - This was the owner's choice over standoffs off the oak or clips.
   - It keeps the board at the depth the switch pins set, and it loads the
     plate, not the solder joints.
2. **The standoff's length is derived, not chosen.** *(Superseded by
   Amendment 2: there is no standoff.)*
   - It is the plate-to-board gap: `switch.pcb_below_seat` less
     `plate-thickness`.
   - *(Amended 2026-09-27: the derivation now runs the other way. No M2
     standoff is made at the derived length, so the owner chose the stocked
     one and a washer under it. The board depth,
     `switch.pcb_below_seat`, is now what they set, and a rule checks it
     (below).)*
   - The model prints it as `mechanical/drc.echo` "key-board standoff length
     (derived)", and the BOM row cites that line.
   - *(Superseded 2026-09-27 by Amendment 2: there is no standoff, so no
     standoff length. That line is now "key-board mount gap (derived)", the
     plate-to-board gap the spacer and washer make, and the depth rule is
     "key-board mount sets the board depth".)*
3. **The board is a rectangle across the cavity, with a standoff in each
   corner.**
   - Across the body it spans the cavity between the side walls, less
     `boards.board_clear` each side. Along the body it runs past the outermost
     switch cutouts by `boards.kb_end_margin`.
   - Each standoff sits `hardware.kb_standoff_inset` in from both edges of
     its corner, outside every switch cutout. The rule "key-board standoffs
     clear of the switch cutouts" checks each is the standoff's edge
     distance (`hardware.kb_standoff_edge`) from every cutout. *(Amended
     2026-09-27: it first checked 0.5 mm of plate round the barrel, a
     drawing convention; the vendor's figure is from the hole centre.)*
   - *(Superseded 2026-09-27 by Amendment 2: each corner holds a screw, not a
     standoff, `hardware.kb_mount_inset` in from both edges; the standoff rule
     is replaced by "key-board screw heads bear on plate metal" and
     "key-board spacers and washers clear of the switch cutouts", and the
     count is `drc.echo` "key-board mounts".)*
   - The count per board is in `drc.echo` "key-board standoffs". "Key boards
     clear of the lid screws" keeps the board edges off the M3 screws that
     close the lid.
   - Where the ribbon runs under the board, from its connector to the far
     edge, no part may go: the model leaves it out of the parts envelope.
     *(Amended 2026-09-27, after the key board's review: this also said "the
     PCB carries it as a rule area". It does not, and needs none. The ribbon
     now folds between the two plugs' heights, below the key board's parts,
     so nothing on the PCB's underside is in its path; the clash check and
     the hairpin rules in `drc.echo` are what keep it clear. The PCB's only
     rule areas are the standoff keep-outs of point 4.)* *(Those are the
     mount keep-outs since Amendment 2.)*
4. **The plate makes no second ground bond through the board.**
   - The plate is grounded at one mount of the left-hand key board (Amendment 5).
     *(Superseded 2026-09-29 by Amendment 7: the plate is grounded through the
     columns at the main board's mounts, and every key-board mount is unplated.)*
   - The board's holes are unplated (NPTH).
   - Each hole sits in a copper keep-out on both layers. On top it is
     covered by the standoff's end face, and underneath by the screw head.
   - No track, via or pour reaches the standoff or the screw head, so the
     screw cannot bond the plate to `GND_CHAIN` or short a signal. `tools/pcb.py` places the keep-out
     from the CAD's standoff diameter and screw head, and the router treats it
     as an obstacle.
   - *(Superseded 2026-09-27 by Amendment 2: on top the washer
     (`MECH-KB-WASHER`, `hardware.kb_washer_od`) bears on the copper, not a
     standoff's end face, and underneath the nut (`MECH-KB-NUT`,
     `hardware.kb_nut_e`), not a screw head. The keep-out is sized from the
     wider of the spacer and washer on top and from the nut underneath, each
     grown by `hardware.kb_mount_float`
     (`mechanical/export/pcb-geometry.echo`). The steel is still the plate's
     potential, so the rule of this point stands unchanged.)*
5. **The ribbon connector envelope is the Molex 200528's footprint.**
   - The size is in `config/body.yaml` `boards.ffc_conn_*`.
   - `J-CHAIN` sits at the board's end with its cable entry facing the
     ribbon's fold.
   - The board stayed the same size (the owner's choice over enlarging it):
     the connector fits once the model is right.
   - The rule "key-board screw heads clear of the ribbon connector" keeps
     the screw heads off it. *(Since Amendment 2 the heads are on the plate
     and the nuts are under the board: "key-board nuts clear of the chain
     header".)*
   - *(Amended 2026-09-27, [ADR 0017](0017-one-main-board.md)'s amendment:
     `J-CHAIN` is now a through-hole 2×6 1.27 mm shrouded right-angle IDC
     header, stand-in Samtec SHF-106-01-L-D-RA, stacked over the main
     board's. `boards.ffc_conn_*` no longer exists: the envelope is
     `config/body.yaml` `boards.chain_hdr_*` and the plug's
     `boards.chain_plug_*`, from the banked Samtec pages. The rule is now
     "key-board screw heads clear of the chain header", and the no-parts
     strip is under the header, its plug and the ribbon's hairpin.)*
     *(Amended again 2026-09-27: that strip is the body model's parts
     envelope, not a keep-out on the PCB — see point 3's note.)*
   - *(Amended 2026-09-27, with point 3: the second and third bullets above
     no longer hold. The board was grown to point 3's rectangle, and
     `J-CHAIN` is not at the board's end: it sits between the switches where
     the body CAD finds room (`mechanical/export/pcb-geometry.echo` "chain",
     checked by `drc.echo` "chain headers on the left_hand boards clear of
     the switches" and its right-hand twin).)*

6. **The key boards are 1.2 mm thick** (`boards.key_board_t`). *(Since
   Amendment 6: 1.6 mm, pressed against the switches' housings.)*
   - The switch pins end 5.10 mm below the seat, and the board's top is
     `switch.pcb_below_seat` below it. How much pin a 1.6 mm and a 1.2 mm
     board leave to solder is worked in `docs/reference/ks33-geometry.md`:
     too little on 1.6 mm, enough on 1.2 mm. *(Corrected 2026-09-27: this
     bullet restated that page's figure at the window's middle, which is not
     where the key boards sit.)*
   - 1.2 mm is a standard thickness at every board house `[from memory]`.
   - The standoff length does not change: it is set by the board's *top*
     face, which is fixed. Only the screw gets shorter. *(Superseded
     2026-09-27 by Amendment 2: no standoff; the spacer and washer set the
     top face's depth, and the board's thickness enters only the screw's
     length, `hardware.kb_screw_l`.)*
   - The main board's thumb switches have the same arithmetic, and it is
     decided when the main board is laid out.

## Amendment, 2026-09-27

Points 3 and 6 replace the first version's placement, which put a standoff
midway between neighbouring switches wherever the plate's web was wide
enough. That left the left hand's LH4/LH5 end with none. It also crowded the
register between two switches' pins, where its position was good to about
±0.1 mm. The owner: "maybe the standoffs need to be from the outside and if
we need to increase the size of the board a little bit that would make sense
and kind of anchor it maybe in each corner", and a bigger board "would also
allow for a less fragile mounting of the IC". The owner also asked whether
1.2 mm is a common thickness; it is, so point 6 adopts it.

## Options considered

- **Standoffs off the oak bottom or the main board.** The key board's
  position relative to the plate is what matters, and this adds the whole
  cavity's tolerance to it. Not chosen.
- **Clip or snap features on the switches only.** This is what the model had
  by default. It loads the solder joints on every press. Rejected.
- **Plated holes bonded to ground.** They are simpler to lay out. But they make a second
  plate-to-ground path, a loop through the plate, next to the key networks.
  Rejected.
- **Standoffs between the switches, on the smallest board** (this ADR's first
  version). Rejected in the amendment: it left one end unheld and the
  register crowded.

## Consequences

- **Open, and it decides the part:** *(This whole list is superseded
  2026-09-27 by Amendment 2: no part is pressed into the plate, so neither
  the stocked standoff length nor the plate's alloy decides anything.)*
  - A self-clinching standoff this short may not be stocked.
  - The plate must also be an alloy and thickness the standoff is rated to clinch into.
  - Both are for the plate vendor at M4. If no stocked length fits, the
    fallback is a self-clinching nut in the plate and a spacer of the
    derived length. The CAD geometry is the same either way.
  - `config/body.yaml` marks the standoff and screw sizes `tbd`.
  - *(2026-09-27, from the banked vendor data.)* PEM makes an M2
    self-clinching standoff only in its microPEM range, the MSO4-M2
    (`datasheets/mechanical/PEM-MPF-MICROPEM-FASTENERS.pdf` p5; its SO
    range starts at M3). Its hole, barrel and edge distance are now the
    model's (`hardware.kb_standoff_*`). It is made only 2 and 3 mm long,
    head flush in the sheet, and neither length lands in the window the
    switch pins allow. *(That rule, "key-board standoff stocked lengths
    against the window", was withdrawn the same day and never replaced; no
    shim was adopted.)*
    PEM publishes no data for it in aluminium or in a 1.2 mm sheet. So the
    first question for the plate vendor and PEM is whether MSO4-M2-3 with a
    shim, or the fallback above, holds the board.
  - *(2026-09-27, the owner's choice; superseded the same day by Amendment 2,
    which keeps the washer and replaces the MSO4 with a spacer, a screw
    through the wood and a nut.)* **MSO4-M2-3, with an M2 small flat
    washer (ISO 7092 / DIN 433, `MECH-KB-WASHER`) between its end and the
    board.**
    - With the head flush in the plate's top face, the board top sits
      `hardware.kb_standoff_l` + `hardware.kb_washer_t` below the seat,
      whatever the plate's thickness. That is `switch.pcb_below_seat` for
      the key boards, inside the pins' window.
    - `drc.echo` "key-board standoff and washer set the board depth" fails
      if the parameter and the hardware disagree.
    - "key-board depth at the hardware's tolerance limits" prints the worst
      case, which reaches the window's shoulder end by a few hundredths.
      The first board confirms the fit.
    - The washer is chosen over filing or printing a spacer: it is a stock
      part at a controlled thickness. A printed spacer would creep under the
      screw's clamp, and the standoff sets the depth every key press loads.
    - The thumb switches' board is not affected: its depth is
      `switch.thumb_pcb_below_seat`, set when the main board's own
      standoffs are.
    - Whether the standoff clinches in the plate is still PEM's and the
      plate vendor's to confirm (`MECH-KB-STANDOFF`).
    - **If it does not, the fallback is the owner's (2026-09-27): nothing
      pressed into the aluminium.** An M2 screw comes up from under the
      board, through the washer and a plain spacer, through a clearance hole
      in the plate. A nut sits on the plate's top face, in a shallow pocket
      in the oak top's underside. Every part is stock. The depth rule still
      holds: spacer plus washer replaces the standoff's reach. The cost is a
      pocket per standoff in the oak, which the body CAD would cut. This
      replaces the self-clinching-nut fallback above. *(Superseded by
      Amendment 2: its nut sat in a pocket that broke into the cap slot at
      three corners and its screw was not in the BOM; the standard puts the
      nut under the board instead, where nothing crowds it.)*
- **Where the standoffs can go is now a rule.** `kb_standoffs()` in
  `mechanical/cad/woody_body.scad` finds them. *(Since Amendment 2 the
  function is `kb_mounts()`, and the rules are the mount rules listed
  there.)* The PCB takes them from
  `mechanical/export/pcb-geometry.echo`, and `tools/pcb.py check` fails if a
  hole moves off the CAD's position.
- **The screw heads are on the parts side.** *(Since Amendment 2 the nuts
  are.)*
  - Each hole footprint's courtyard is on the bottom, so KiCad's courtyard
    check keeps parts clear of the heads.
- **The right-hand board** gets its four the same way when it is laid out.

## Amendment 2, 2026-09-27 — screws through the wood

> **Superseded in part the same day by Amendment 3** (below): the bore
> through the wood top and the glued plug are gone, replaced by a blind
> pocket in the top's underside. Everything below the plate — screw,
> spacer, washer, board, nut — and the depth rules stand as written here.
> The passages about the bore and the plug are marked where they sit.

**The standard mount for the key boards is now a screw down through the wood
top, under a glued wooden plug.** It replaces the PEM MSO4-M2-3
self-clinching standoff, and with it everything in this page that speaks of
a standoff, its length, its clinch in the plate, or the fallback nut in a
pocket. The owner: "We can always do fasteners through the wood, slightly
instead, so that we can put a wooden cap on top so it looks like it's not
there", and then "Yeah let's go ahead and make that the standard".

### The stack, at each corner of each key board, from the top down

| Part | Row | Size |
|---|---|---|
| Wooden plug, glued into the bore over the head *(gone: Amendment 3)* | `MECH-KB-PLUG` | `hardware.kb_bore_d`, `kb_plug_glue_gap`, `kb_plug_min_depth` |
| A bore through the wood top, down to the plate *(now a blind pocket: Amendment 3)* | — | `hardware.kb_bore_d` |
| M2 × 8 socket head cap screw, ISO 4762, A2; head on the plate's top face at the bore's floor | `MECH-KB-SCREW` | `hardware.kb_screw_head_d`, `kb_screw_head_h`, `kb_screw_l` |
| The key plate's M2 clearance hole | `PLATE-TOP` | `hardware.kb_plate_hole` |
| Würth WA-SMST 9774020943R steel spacer, under the plate | `MECH-KB-SPACER` | `hardware.kb_spacer_l`, `kb_spacer_l_tol`, `kb_spacer_od` |
| ISO 7092 / DIN 433 small washer | `MECH-KB-WASHER` | `hardware.kb_washer_t`, `kb_washer_t_range`, `kb_washer_od` |
| The key board, its NPTH hole | — | `boards.key_board_t`, `hardware.kb_screw_hole` |
| ISO 4032 M2 nut, on the board's underside | `MECH-KB-NUT` | `hardware.kb_nut_e`, `kb_nut_m` |

Every part is stock and has a banked drawing (the rows name them). Nothing is
pressed into the aluminium, so the plate's alloy and PEM's missing data for a
sheet like it stop mattering.

### The depth

The head bears on the plate, so the board top sits the plate + the spacer +
the washer below the seat. That sum **is** `switch.pcb_below_seat` for the key
boards, and `drc.echo` "key-board mount sets the board depth" fails if the
parameter and the hardware disagree. The plate's thickness is back in the
stack (the MSO4's flush head had kept it out), with its tolerance
`hardware.kb_plate_t_tol`.

"key-board depth at the hardware's tolerance limits" takes the plate, the
spacer and the washer each to its limit and prints a **NOTE**, not a PASS: at
the high corner the board sits past the window's deep end, and a little less
pin stands proud to solder. It is a NOTE because it is a worst case of three
tolerances at once, and the first board confirms the fit. If it does not
fit, the spacer is the part to change (`hardware.kb_spacer_l`'s
`decided_by`: bought, or filed or printed to length — owner, 2026-09-27).

The plate-to-board gap the spacer and washer make is "key-board mount gap
(derived)". **That line replaces "key-board standoff length (derived)"**; no
part of this mount has a length derived from the pins.

### Where the corners go

- Each screw is `hardware.kb_mount_inset` in from both edges of its board, so
  its bore keeps `hardware.kb_bore_wall` of wood from the side grooves in the
  wood top.
- The tail ends are longer than the mouth ends (`boards.kb_tail_margin`
  against `boards.kb_end_margin`), because the last keys reach the tail
  corners, and each corner's bore must keep `hardware.kb_bore_wall` from that
  key's cap slot.
- Both are checked by "key-board plug bores clear of the wood top's cuts
  (mouth ends)" and "(tail ends)"; the tail line prints the least
  `boards.kb_tail_margin` may be. *(Amendment 3: the bore is now a pocket,
  the wall is `hardware.kb_pocket_wall`, and the rules are "key-board head
  pockets clear of the wood top's cuts (mouth ends)" and "(tail ends)".)*
- "key-board screw heads bear on plate metal", "key-board spacers and washers
  clear of the switch cutouts", "key-board plugs deep enough to hold"
  *(withdrawn with the plug, Amendment 3)*,
  "key-board screw: thread past the nut", "key-board screw ends clear of the
  main board's parts" and "key-board nuts clear of the chain header" hold the
  rest. The count per board is "key-board mounts".
- The PCB's keep-outs: point 4's note.

### Assembly, and service

*(Superseded by Amendment 3's order: the screws go in before the plate is
bonded, and there is no plug. Kept as the record.)*

1. Bore the wood top at every corner (`hardware.kb_bore_d`), through to the
   plate.
2. Bond the plate to the top with RTV (ADR 0009's adhesives table). **Keep
   the beads off the bores**: silicone in a bore keeps the plug's glue from
   holding.
3. Screw from the top, down each bore: screw, then under the plate the
   spacer, the washer, the key board, and the nut.
4. Solder the switches — after the hardware has fixed the depth, not before.
5. **Plug last**, with PVA, wood to wood (ADR 0009), and sand flush. During
   bring-up, dry-fit the plugs and leave them unglued.

For service, drill the plug out, undo the screw, and re-plug with a fresh
one. Plugs are cut from the owner's own stock with a 1/4 in tapered plug
cutter, for grain match; ready-made 1/4 in oak plugs are the fallback
(`MECH-KB-PLUG`).

### The wood

The owner: "we've been calling this oak, but honestly, I'll probably use a
harder wood, but it really doesn't matter for the design aspect". **The
species is open** — a hardwood, the owner's choice (ADR 0009). The part names
keep "oak". The cross-grain movement figure and the plug and bore-wall
placeholders (`hardware.kb_bore_wall`, `kb_plug_min_depth`) assume oak until
the species is chosen; the M2 trial that settles those two uses the chosen
wood. *(Amendment 3: the placeholders are now `hardware.kb_pocket_wall` and
`kb_pocket_skin`; the species is still open.)*

### What this supersedes

- **PEM MSO4-M2-3**, `MECH-KB-STANDOFF`, and every `hardware.kb_standoff_*`
  parameter: gone. The standoff's clinch in the plate was the only open
  question on the part; there is no longer a part to ask about.
- **"The standoff's length is derived"** (point 2), and every "standoff
  length" in the corpus: there is no standoff. The depth is the spacer's and
  the washer's, set above.
- **The owner's earlier fallback** (a nut in a pocket in the oak top's
  underside, *Consequences*): the nut is under the board.
- **The screw.** It was an M2 × 4 up from under the board into the
  standoff; it is now an M2 × 8 down from the top into a nut.
- Marked in place above with a pointer to this amendment; the text they mark
  is the record of what was decided first.

### Options considered

- **The head in a counterbore in the wood, not on the plate** (the owner's
  first wording). With the top as thick as the flush rule makes it (`drc.echo`
  "oak top thickness (flush at full travel)"), a plug of
  `hardware.kb_plug_min_depth`, the glue gap and the head leave about half a
  millimetre of wood under the head `[calc, 2026-09-27: research for this
  amendment]` — too little to clamp on. The head bears on the plate instead;
  the plug still hides it, which is what the owner asked for.
- **Keep the MSO4 and add the plug.** Nothing to plug: the MSO4's head is
  flush in the plate under the wood, and its clinch in aluminium was unproven.
- **A thin DIN 439 nut or a nylon-insert lock nut.** No small-pack US stock
  of the thin nut was found, and DIN 985 / ISO 10511 have no M2 size. The
  plain ISO 4032 nut fits (`drc.echo` "key-board screw: thread past the
  nut").

### Still open

- `hardware.kb_bore_wall` and `kb_plug_min_depth` are placeholders `[from
  memory]`: settled at M2 by boring and plugging a scrap of the chosen wood
  beside a slot. *(Replaced by Amendment 3's list.)*
- `hardware.kb_mount_inset` and `kb_spacer_l`: confirmed at M4 with the
  board's first fit.
- The wood's species (above).

## Amendment 3, 2026-09-27 — the heads hide in blind pockets; no through-holes, no plugs

**The screw heads now sit in blind pockets drilled up into the wood top's
underside.** Nothing goes through the playing face, and there are no plugs.
This replaces Amendment 2's bore and plug; everything else in Amendment 2
stands. The owner: "I don't want to have through holes and plugs in the
wood. I want to have only holes that go half depth in the wood, drilled from
the inside halfway down, enough to be able to fit the head."

### The stack, from the top down

| Part | Row | Size |
|---|---|---|
| The wood top, unbroken on its face; a blind pocket in its underside over each head (1/4 in Forstner, flat floor) | — | `hardware.kb_pocket_d`; depth `drc.echo` "key-board head pocket depth (derived)" = the head's height + `hardware.kb_pocket_clear` |
| M2 × 8 socket head cap screw, ISO 4762, A2; head on the plate's top face, inside the pocket | `MECH-KB-SCREW` | `hardware.kb_screw_head_d`, `kb_screw_head_h`, `kb_screw_l` |
| The key plate's M2 clearance hole | `PLATE-TOP` | `hardware.kb_plate_hole` |
| Würth WA-SMST 9774020943R spacer, under the plate | `MECH-KB-SPACER` | `hardware.kb_spacer_l`, `kb_spacer_l_tol`, `kb_spacer_od` |
| ISO 7092 / DIN 433 small washer | `MECH-KB-WASHER` | `hardware.kb_washer_t`, `kb_washer_t_range`, `kb_washer_od` |
| The key board, its NPTH hole | — | `boards.key_board_t`, `hardware.kb_screw_hole` |
| ISO 4032 M2 nut, on the board's underside | `MECH-KB-NUT` | `hardware.kb_nut_e`, `kb_nut_m` |

The pocket only houses the head: the head bears on the plate, so the depth
rules, the tolerance NOTE, the screw rules and the PCB keep-outs are
Amendment 2's, unchanged. The mount clamps the plate itself between the head
and the spacer.

### The wood's rules

- "key-board head pockets clear of the wood top's cuts (mouth ends)" and
  "(tail ends)": each pocket keeps `hardware.kb_pocket_wall` of wood from
  every cap slot, side groove and window rebate. The tail line still prints
  the least `boards.kb_tail_margin` may be, and `hardware.kb_mount_inset`
  still keeps the pockets off the side grooves.
- "key-board head pockets leave wood over them": the wood between a pocket's
  floor and the playing face, against `hardware.kb_pocket_skin`.
- The pockets are a blind cut, like the side grooves, so they are exported
  on their own: `mechanical/export/oak-pockets.dxf`.
- "key-board plugs deep enough to hold" is withdrawn with the plug.

### Assembly

1. Clip the switches into the plate.
2. Drop the screws down through the plate's holes from its top face.
3. From below: the spacer, the washer, the key board, and the nut. Tighten
   each nut while holding its head with a 1.5 mm hex key from above.
4. **Epoxy each head to the plate** (below) and let it cure fully before
   anything else torques a nut.
5. Solder the switches — after the hardware has fixed the depth.
6. **Then** RTV-bond the plate to the wood top (ADR 0009's adhesives
   table); the heads go up into the pockets. **Keep the RTV beads off the
   pockets.** Each pocket's radius is well over the head's, so the heads
   find their pockets without a jig `[calc: (kb_pocket_d − kb_screw_head_d) / 2
   is over a millimetre]`.

### Service — the heads are epoxied to the plate (decided)

**Once the lid is bonded, the heads cannot be reached or held.** Left
loose, a nut loosened from below would spin its screw in the pocket, and
taking a key board off would mean lifting the plate off the wood, breaking
an RTV joint ADR 0009 calls permanent within the lid.

**So each head is fixed to the plate with a dot of epoxy before the plate
is bonded** (`ADH-EPOXY`). The owner, 2026-09-27: "Yes, add the epoxy dot on
the heads." The head then stays put while its nut is undone from below, and
a key board comes off with the lid in place.

- Put the dot beside the head, where its edge meets the plate — after the
  nut is tightened (step 3), before soldering (step 4), and let it cure
  before any torque goes on a nut again.
- **Keep it inside the pocket's footprint** (`hardware.kb_pocket_d`), and
  **no taller than `hardware.kb_pocket_clear` above the head** — kept below
  the head's top, it is — or the plate will not seat on the wood. Keep it
  out of the hex socket.
- Epoxy is right here and nowhere else in the body: it is metal to metal,
  steel head to aluminium plate, and nothing in that joint moves with the
  wood (ADR 0009's adhesives table).
- A screw that must itself be replaced is the one case that still means
  lifting the plate.

### What this supersedes

- Amendment 2's bore through the wood top (`hardware.kb_bore_d`), its plug
  (`MECH-KB-PLUG`, `hardware.kb_plug_glue_gap`, `kb_plug_min_depth`), its
  wall (`hardware.kb_bore_wall`, now `kb_pocket_wall`), its rules, and its
  assembly order (bore, bond, screw, plug last). Each is marked in place.
- ADR 0009's amendment saying the face "reads as unbroken wood, and is not":
  it is unbroken again (ADR 0009, marked there).

### Still open

- `hardware.kb_pocket_skin` and `kb_pocket_wall` are placeholders `[from
  memory]`: settled at M2 by pocketing a scrap of the chosen wood beside a
  slot and sanding its face.
- `hardware.kb_mount_inset` and `kb_spacer_l`: confirmed at M4 with the
  board's first fit.
- The wood's species (Amendment 2, *The wood*).

## Amendment 4, 2026-09-28 — studs pressed flush into the plate; no pockets, no epoxy

**The key boards now hang from PEM self-clinching flush-head studs pressed
into the key plate.** The owner asked whether the screws could be made flush
with the plate by countersinking. At M2 a flat head is as tall as the plate is
thick (1.20, the switch's plate slot, `plate-thickness`), which leaves a
knife-edge hole; a self-clinching flush-head stud gets the same flush face
without taking the plate's thickness. The owner: "The press and flush looked
good, let's go ahead and convert to that", and a thicker plate was allowed
only if the keys were unaffected — which it would not be, since the switches
clip into 1.20 mm. It is not needed: the stud is rated for this sheet.

### The stack, from the top down

| Part | Row | Size |
|---|---|---|
| The wood top, unbroken, bonded flat on the plate: no pocket | — | — |
| PEM FHL-M2.5-10ZI stud, pressed into the plate, head flush with its top face | `MECH-KB-STUD` | `hardware.kb_stud_hole`, `kb_stud_head_d`, `kb_stud_l`, `kb_stud_s`, `kb_stud_edge` |
| Ettinger 5.52.033 spacer, faced to length, between the plate and the board | `MECH-KB-SPACER` | `hardware.kb_spacer_l`, `kb_spacer_l_tol`, `kb_spacer_od` |
| The key board, its NPTH hole | — | `boards.key_board_t`, `hardware.kb_board_hole` |
| ISO 4032 M2.5 nut, on the board's underside | `MECH-KB-NUT` | `hardware.kb_nut_e`, `kb_nut_m` |

### Why this stud, and why M2.5

- **PEM makes no M2 flush-head stud** in its bulletin; the metric tables
  start at M2.5 [datasheets/mechanical/PEM-FH-SELF-CLINCHING-STUDS.pdf p.FH-5, FH-7]. (One distributor lists a steel FH-M2
  that PEM does not publish, with no data; not used.) So the mount goes to
  M2.5: the nut, spacer and board hole all change with it.
- **FHL, the low-displacement head, not the plain FH.** PEM publishes FHL's
  performance in exactly this sheet — 1.2 mm aluminium: push-out 285 N,
  torque-out 0.55 N·m, nut torque 0.32 N·m (`hardware.kb_stud_torque`)
  [datasheets/mechanical/PEM-FH-SELF-CLINCHING-STUDS.pdf p.FH-31] — and FHL needs 2.8 mm from its hole's centre to an edge,
  where FH needs 5.4 [p.FH-5, FH-7]. A switch cutout is an edge: the model
  puts every stud 5.1 from the nearest cutout or plate edge (`drc.echo`
  "key-board studs clear of the plate's edges and cutouts"), so FH would
  not fit and FHL does.
- **Its sheet:** 1 mm and up, aluminium to HRB 80 / HB 150 [p.FH-7] — 5052
  and 6061 alike, so the plate's alloy stays the vendor's choice.
- **Zinc-plated steel, not stainless:** PEM's finish guide rates stainless
  in aluminium a significant galvanic pair and plated steel acceptable
  [datasheets/mechanical/PEM-TECHSHEET-CHOOSING-A-FASTENER-FINISH.pdf
  pp.3-4].
- **Length 10:** the stack below the head's face, the nut and two pitches,
  at the stud's shortest (±0.4) — `drc.echo` "key-board stud: thread past
  the nut". Its unthreaded shank (`kb_stud_s`) ends inside the spacer.

### The depth, and the spacer that is made, not bought

**The spacer alone sets the board's depth: no washer** (owner, 2026-09-28:
"dropping the washer is the right idea"). The board top sits the plate plus
the spacer below the seat (`drc.echo` "key-board mount sets the board
depth"), so the spacer is the whole 2.3 mm gap. A washer was only ever there
to make up a length no stocked spacer had; here it would have been a 0.5
M2.5 washer under a 1.8 spacer, which is no more stocked than a 2.3. Without
it the stack has one tolerance fewer, and at its limits it stays inside the
switch pins' window ("key-board depth at the hardware's tolerance limits").

**No stocked M2.5 spacer is 2.3** — Ettinger 5.52, Würth WA-SMST and RAF
step through 2.0 to 2.5 or 3.0 — so an Ettinger **5.52.033 (3.0) is faced
down to 2.3**, in metal: the owner's standing allowance to file a spacer
(Amendment 2), and not printed, which would creep under the clamp. The Würth
WA-SMST parts are ruled out in any case: they carry a spigot under the body
for reflow, so they are not the plain spacers they were taken for (the M2 one
that Amendment 2 named included).

**The board stays 1.2 mm.** A thicker board does not move the board's top —
the spacer sets that — it moves the underside further down the pins: at 1.6
the pins end about flush with it and leave nothing to fillet
(`docs/reference/ks33-geometry.md`). Nor does a switch rest on the board:
its housing ends 1.0 above the board's top, and a key press goes into the
plate through the switch's clips, not into the joints. The plated holes fill
from the underside, so the joints need no soldering from the top, where the
switch body covers them.

### Assembly

1. **The plate vendor presses the studs**, on a press, into holes that are
   not deburred, inserted from the punch side and squeezed flush on a
   parallel anvil — for sheet this thin, PEM's countersunk anvil [datasheets/mechanical/PEM-FH-SELF-CLINCHING-STUDS.pdf
   p.FH-18, FH-20]. Never hammered.
2. Clip the switches into the plate.
3. From below, on each stud: the spacer, the key board, and the
   nut, tightened to no more than `hardware.kb_stud_torque`.
4. Solder the switches — after the hardware has fixed the depth.
5. RTV-bond the plate to the wood top (ADR 0009). The beads may run over the
   studs' heads: they are flush and never turn.

**Service:** the clinch holds each stud against turning, so a nut comes off
from below with the lid bonded, and the board comes off. Nothing needs
holding from above, which is why there is no epoxy.

### What this supersedes

- Amendment 3's pockets (`hardware.kb_pocket_*`, the "key-board head
  pocket" rules, `mechanical/export/oak-pockets.dxf`), its epoxy
  (`ADH-EPOXY`), and the M2 screw (`MECH-KB-SCREW`, `hardware.kb_screw_*`,
  `kb_plate_hole`, `kb_screw_hole`, now `kb_stud_hole` and `kb_board_hole`).
- The M2 spacer and nut: now M2.5 (the rows keep their names). The washer
  (`MECH-KB-WASHER`, `hardware.kb_washer_*`): gone, the spacer making up its
  length.
- `hardware.kb_mount_inset`: now set by the M2.5 nut's keep-out, not by the
  pockets' wall to the side grooves.
- `boards.kb_tail_margin` keeps its value so the boards' outlines do not move
  before M3; with no pockets it could be as short as `drc.echo` "key-board
  tail margin, least".
- ADR 0009's notes on the face, the lid screws and the adhesives: marked
  there.

### Still open

- The spacers, faced to `hardware.kb_spacer_l` and measured, at M4, with the
  board's first fit; `hardware.kb_mount_inset` with it.
- A US source for FHL-M2.5-10ZI — the plate vendor who presses them is the
  first to ask — and for the M2.5 nuts.
- The wood's species (Amendment 2, *The wood*); it no longer sets anything in
  the mount.

## Amendment 5, 2026-09-29 — the plate is grounded at one mount of the left-hand board

> **Superseded the same day by Amendment 7** ([ADR 0025](0025-the-cassette.md)):
> the key plate is tied by the cassette's columns to the main board's plated
> mounts on `PWR_GND`, so no key-board mount is plated. The text below is the
> record.

The key plate was grounded by `MECH-GNDBOND`, a ring terminal and a wire from
the main board. The owner replaced it with one of the mounts themselves, the
way the thumb plates are grounded (ADR 0022 point 6):

- **One mount of the left-hand key board is plated**, with a `GND_CHAIN` pad on
  both faces (`hardware/boards/key-board-lh/layout.yaml` `bond_mount`). The
  stud's clinch, the spacer on the top pad and the nut on the bottom one bond
  the plate. `GND_CHAIN` is the main board's `PWR_GND` down the ribbon
  (`hardware/nets.yaml`), so the plate still bonds to `PWR_GND`, never to
  `AGND`.
- **Only one.** Every other key-board mount, on both boards, stays NPTH with
  its keep-out. A second bond would close a ground loop through the two
  ribbons.
- **The plate is ordered un-anodised**, or masked round that stud hole
  (`PLATE-TOP`), because the bond is metal to metal. Bring-up meters the
  plate to `PWR_GND`.
- `MECH-GNDBOND`, its wire and its M3 hardware are gone. `tools/pcb.py check`
  holds the bonded mount to its rule: plated, every pad on the ground net,
  and no other net's copper under the spacer or the nut.

## Amendment 6, 2026-09-29 — standard 1.6 mm boards, pressed against the switches

The owner: the board can be a standard thickness, because the switch sits in
the plate and only its pins go through the board. Gateron's drawing agrees.

- **The board's top is pressed against the switches' housing bottom**, 2.50 mm
  below the seat [ds `GATERON-KS-33-VENDOR-SPEC-DRAWING.pdf` sheet 6]. Each
  switch is held between the plate above (its rim on the plate, its clips
  under it) and the board below (`switch.pcb_below_seat`,
  `switch.pcb_below_seat_window`).
- **The boards are 1.6 mm** (`boards.key_board_t`). The pins end 5.10 mm below
  the seat, so 1.0 mm shows below the board to solder [calc]. That is more
  than the 1.2 mm board at the old depth left.
- **The pin holes are larger:** 2.2 mm on 2.8 mm pads (superseded by
  Amendment 8: 3.0 mm on 3.4 mm)
  (`hardware/lib/woody.pretty/SW_Gateron_KS33_1u`). Each pin is a 0.45 mm
  blade that flares to about 2 mm wide where it leaves the housing, and the
  hole's top now meets that flare [3D, sectioned; `hardware/lib/README.md`].
  Gateron's own layout uses 3.0 mm holes.
- **The mounts keep a spacer, 1.3 mm** (`hardware.kb_spacer_l`), the
  switches' housing below the plate. The switches hold the plate and the
  board apart only where they are. At a mount there is no switch, and without
  the spacer the nut would pull the board up into the plate. It is an
  Ettinger 5.52.015 (1.5 mm), faced to length.
- **The board sits 1.0 mm higher.** The room between the plate and the board
  is now only the housing's 1.3 mm, so nothing but the switches goes on the
  board's plate side. The parts are on the underside already.
- **The stud is 8 mm** (FHL-M2.5-8ZI, `hardware.kb_stud_l`), no longer 10.
  The stack is thinner, and the 10 mm stud's tip reached the ribbon under
  the raised board. The 8 mm stud leaves 1.5 mm of thread past the nut
  (`drc.echo` "key-board stud: thread past the nut").
- **The main board follows** (ADR 0022). Its thumb switches use the same
  mount on the thumb plates, so it is 1.6 mm, pressed against their housings,
  with the same spacer.

Supersedes point 6's 1.2 mm, and Amendment 4's 2.3 mm spacer and 10 mm stud. The first switch
pushed into the first board confirms the holes and the depth.


## Amendment 7, 2026-09-29 — the key boards are held by the cassette's columns

[ADR 0025](0025-the-cassette.md) makes the internals one unit, the cassette,
bonded into the shell. Nothing screws into the wood, and the key plate is tied
to a bottom plate by a column at each key-board corner.

### The stack at each corner, from the top down

| Part | Row | Size |
|---|---|---|
| The oak top, with a blind pocket drilled up into its underside over the screw's head. Nothing breaks the playing face | — | `hardware.col_pocket_d`; depth, the head's height and `col_pocket_clear` |
| M2.5 low-head screw, its head on the key plate's top face | `MECH-COL-SCREW` | `hardware.col_screw_head_d`, `col_screw_head_h`, `col_screw_l` |
| The key plate's clearance hole | `PLATE-TOP` | `hardware.col_plate_hole` |
| The spacer, faced to length, between the plate and the board. It still alone sets the board's depth | `MECH-KB-SPACER` | `hardware.kb_spacer_l`, `kb_spacer_l_tol`, `kb_spacer_od` |
| The key board, its NPTH hole | — | `boards.key_board_t`, `hardware.kb_board_hole` |
| The column standoff, threaded onto the stud from the bottom plate, faced to the gap down to the main board | `MECH-COL-STANDOFF` | `hardware.col_standoff_*`; `drc.echo` *"column standoff length (derived)"* |

Below the standoff are the main board and the bottom plate's stud (ADR 0022,
as amended by ADR 0025).

### What changes, and what does not

- **The depth rules are unchanged.** The spacer bears on the plate's
  underside and the board's top, and the screw clamps the plate, the spacer and
  the board onto the standoff. So *"key-board mount sets the board depth"* and
  *"key-board depth at the hardware's tolerance limits"* read as before.
- **The studs in the key plate are gone** (`MECH-KB-STUD`), and so is the nut
  under the board (`MECH-KB-NUT`). The key plate has a clearance hole at each
  corner, not a stud hole, so PEM's edge distance no longer applies there. The
  screw's head must bear on plate metal (*"column screw heads bear on the key
  plate"*).
- **Service goes through the screws.** Once the oak top is cut free
  (ADR 0025), the heads are reached from above. So there is no stud whose
  clinch holds it against turning, and no nut underneath. The key plate comes
  off the columns with both key boards on it.
- **The pockets are back**, as Amendment 3's were: one per corner, blind, their
  wood checked (*"column screw pockets clear of the wood top's cuts"*,
  *"column screw pockets leave wood over them"*). The tail corners' pockets
  set the least tail margin (`boards.kb_tail_margin`), as they did then.
- **The keep-out under the board is the standoff's hex**, across its corners,
  grown by `hardware.kb_mount_float`. It stands where the nut stood, the same
  size (`hardware.col_standoff_af`, `kb_mount_inset`).
- **The corners are where the columns can stand.** A column is vertical, so
  the key board's mouth corners move until the column's stud in the bottom
  plate clears the first thumb row (`boards.kb_end_margin`).
- **Every key-board mount is unplated.** Amendment 5's bonded mount is
  superseded: the key plate is grounded through the columns to the main
  board's plated mounts, on `PWR_GND`, with the bottom plate. The key plate is
  ordered un-anodised, or masked round each column hole on its top face, where
  the screws' heads bear (`PLATE-TOP`).

### Still open

- The standoff and the screw, bought (ADR 0025's *Open*).
- `hardware.col_pocket_wall` and `col_pocket_skin` are placeholders from
  memory, as Amendment 3's were. They are settled at M2 by pocketing a scrap of
  the chosen wood beside a slot.
**Amended 2026-10-02 (owner): the key plate stays.** With the KS-33 switches
and MT165 caps in hand, the owner asked whether the aluminium plate was needed
at all, since the oak top must be thick enough for the caps to finish flush.
The section figures (`mechanical/renders/section-key.png`,
`section-keycap.png`) show the plate sits *below* the seat, under the oak top,
so it costs the wood nothing: the oak top's thickness is set by the cap's
height above the seat less the travel (`drc.echo` "oak top thickness"). The
owner matched the parts against the sections at scale - "everything seems to
match up with the aluminum plate. I think we're good to keep the aluminum
plate." The plate keeps its three jobs: it takes the keystroke load off the
switches' solder joints, it is what the key boards hang from in the cassette
(this ADR), and it holds the switches square to the oak's slots. Still open:
the cap's height above the seat, by calipers on the parts in hand (M1), which
sets the oak top's thickness exactly.

## Amendment 8, 2026-10-03 — Gateron's 3.0 mm pin holes

Issues #6-1 and #8-2 (the key-board and main-board layout reviews) measured
what Amendment 6's 2.2 mm hole was sized without: **the blades are not
centred in their holes.** Sliced at the board's top face, the root's farthest
point is 1.162 mm from pin 2's hole centre and 1.092 mm from pin 1's [3D,
`mechanical/cad/vendor/ks33.stl`, reproduced 2026-10-03], against the 2.2 mm
hole's 1.10 mm radius, and Gateron gives the pins' positions with no tolerance
of their own, so the drawing's general ±0.2 mm applies [ds
`GATERON-KS-33-VENDOR-SPEC-DRAWING.pdf` sheet 6].

- **The holes are Gateron's own ⌀3.00** (sheet 6, *PCB Layout*), on 3.4 mm pads:
  1.5 mm of radius against a 1.36 mm worst case [calc: 1.162 + 0.2], and a
  0.2 mm ring, over JLC's 0.18 mm two-layer minimum [ds
  `datasheets/fab/JLCPCB-PCB-CAPABILITIES.pdf`]. The review's 2.6 mm on 3.0
  cleared the nominal root by 0.14 mm and not the tolerance.
- **The footprint is shared**, so all three boards take it: the left-hand key
  board re-laid out (its networks 9.0 mm from their switches, where 9.4 put a
  label on the bigger pads), the right-hand one with its own re-layout, and
  the main board's thumb switches in its wave-3 re-layout.
- What the pin leaves to solder, the board's depth and the spacer are
  unchanged: the hole's size moves none of them.

