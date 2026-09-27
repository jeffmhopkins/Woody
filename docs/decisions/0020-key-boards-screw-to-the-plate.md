# 0020 — The key boards are screwed to the key plate

**Status:** Accepted. Decided by the owner, 2026-09-27, and amended the same
day (points 3 and 6, and point 5's notes; *Amendment* below). Parts open until M4: the standoff's
length and alloy are the plate vendor's to confirm (below).

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
   - This was the owner's choice over standoffs off the oak or clips.
   - It keeps the board at the depth the switch pins set, and it loads the
     plate, not the solder joints.
2. **The standoff's length is derived, not chosen.**
   - It is the plate-to-board gap: `switch.pcb_below_seat` less
     `plate-thickness`.
   - *(Amended 2026-09-27: the derivation now runs the other way. No M2
     standoff is made at the derived length, so the owner chose the stocked
     one and a washer under it. The board depth,
     `switch.pcb_below_seat`, is now what they set, and a rule checks it
     (below).)*
   - The model prints it as `mechanical/drc.echo` "key-board standoff length
     (derived)", and the BOM row cites that line.
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
     rule areas are the standoff keep-outs of point 4.)*
4. **The plate makes no second ground bond through the board.**
   - The plate is grounded through `MECH-GNDBOND` (`hardware/cluster/cluster-boards.md`).
   - The board's holes are unplated (NPTH).
   - Each hole sits in a copper keep-out on both layers. On top it is
     covered by the standoff's end face, and underneath by the screw head.
   - No track, via or pour reaches the standoff or the screw head, so the
     screw cannot bond the plate to `GND_CHAIN` or short a signal. `tools/pcb.py` places the keep-out
     from the CAD's standoff diameter and screw head, and the router treats it
     as an obstacle.
5. **The ribbon connector envelope is the Molex 200528's footprint.**
   - The size is in `config/body.yaml` `boards.ffc_conn_*`.
   - `J-CHAIN` sits at the board's end with its cable entry facing the
     ribbon's fold.
   - The board stayed the same size (the owner's choice over enlarging it):
     the connector fits once the model is right.
   - The rule "key-board screw heads clear of the ribbon connector" keeps
     the screw heads off it.
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
     `switch.pcb_below_seat` below it. On a 1.6 mm board about 0.1 mm of pin
     would show to solder; on 1.2 mm about 0.5 mm
     (`docs/reference/ks33-geometry.md`) `[calc]`.
   - 1.2 mm is a standard thickness at every board house `[from memory]`.
   - The standoff length does not change: it is set by the board's *top*
     face, which is fixed. Only the screw gets shorter.
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

- **Open, and it decides the part:**
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
    switch pins allow: `drc.echo` "key-board standoff stocked lengths
    against the window" prints both and the shim that would close the gap.
    PEM publishes no data for it in aluminium or in a 1.2 mm sheet. So the
    first question for the plate vendor and PEM is whether MSO4-M2-3 with a
    shim, or the fallback above, holds the board.
  - *(2026-09-27, the owner's choice.)* **MSO4-M2-3, with an M2 small flat
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
- **Where the standoffs can go is now a rule.** `kb_standoffs()` in
  `mechanical/cad/woody_body.scad` finds them. The PCB takes them from
  `mechanical/export/pcb-geometry.echo`, and `tools/pcb.py check` fails if a
  hole moves off the CAD's position.
- **The screw heads are on the parts side.**
  - Each hole footprint's courtyard is on the bottom, so KiCad's courtyard
    check keeps parts clear of the heads.
- **The right-hand board** gets its four the same way when it is laid out.
