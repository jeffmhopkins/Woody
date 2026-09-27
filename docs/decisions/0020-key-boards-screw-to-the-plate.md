# 0020 — The key boards are screwed to the key plate

**Status:** Accepted. Decided by the owner, 2026-09-27, and amended the same
day (points 3 and 6; *Amendment* below). Parts open until M4: the standoff's
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
   - The model prints it as `mechanical/drc.echo` "key-board standoff length
     (derived)", and the BOM row cites that line.
3. **The board is a rectangle across the cavity, with a standoff in each
   corner.**
   - Across the body it spans the cavity between the side walls, less
     `boards.board_clear` each side. Along the body it runs past the outermost
     switch cutouts by `boards.kb_end_margin`.
   - Each standoff sits `hardware.kb_standoff_inset` in from both edges of
     its corner, outside every switch cutout. The rule "key-board standoffs
     in the plate's web" checks each one is in plate metal.
   - The count per board is in `drc.echo` "key-board standoffs". "Key boards
     clear of the lid screws" keeps the board edges off the M3 screws that
     close the lid.
   - Where the ribbon runs under the board, from its connector to the far
     edge, no part may go: the model leaves it out of the parts envelope,
     and the PCB carries it as a rule area.
4. **The plate makes no second ground bond through the board.**
   - The plate is grounded through `MECH-GNDBOND` (`hardware/cluster/cluster-boards.md`).
   - The board's holes are unplated (NPTH).
   - Each hole sits in a copper keep-out on both layers. On top it is
     covered by the standoff's end face, and underneath by the screw head.
   - No track, via or pour reaches the steel, so the screw cannot bond the
     plate to `GND_CHAIN` or short a signal. `tools/pcb.py` places the keep-out
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
  - `config/body.yaml` marks the standoff and screw sizes `tbd`, from memory.
- **Where the standoffs can go is now a rule.** `kb_standoffs()` in
  `mechanical/cad/woody_body.scad` finds them. The PCB takes them from
  `mechanical/export/pcb-geometry.echo`, and `tools/pcb.py check` fails if a
  hole moves off the CAD's position.
- **The screw heads are on the parts side.**
  - Each hole footprint's courtyard is on the bottom, so KiCad's courtyard
    check keeps parts clear of the heads.
- **The right-hand board** gets its four the same way when it is laid out.
