# 0020 — The key boards are screwed to the key plate

**Status:** Accepted. Decided by the owner, 2026-09-27, and amended the same
day (points 3 and 6, and point 5's notes; *Amendment* below). **Amended again
2026-09-27: the owner made through-wood fastening the standard** (*Amendment 2
— screws through the wood* below). There is no standoff any more, so nothing
waits on a plate vendor's clinch data; what stays open is in that amendment's
last list.

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
   - The plate is grounded through `MECH-GNDBOND` (`hardware/cluster/cluster-boards.md`).
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

6. **The key boards are 1.2 mm thick** (`boards.key_board_t`).
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
| Wooden plug, glued into the bore over the head | `MECH-KB-PLUG` | `hardware.kb_bore_d`, `kb_plug_glue_gap`, `kb_plug_min_depth` |
| A bore through the wood top, down to the plate | — | `hardware.kb_bore_d` |
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
  `boards.kb_tail_margin` may be.
- "key-board screw heads bear on plate metal", "key-board spacers and washers
  clear of the switch cutouts", "key-board plugs deep enough to hold",
  "key-board screw: thread past the nut", "key-board screw ends clear of the
  main board's parts" and "key-board nuts clear of the chain header" hold the
  rest. The count per board is "key-board mounts".
- The PCB's keep-outs: point 4's note.

### Assembly, and service

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
wood.

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
  beside a slot.
- `hardware.kb_mount_inset` and `kb_spacer_l`: confirmed at M4 with the
  board's first fit.
- The wood's species (above).
