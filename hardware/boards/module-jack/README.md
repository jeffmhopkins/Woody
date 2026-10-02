# Module jack board — `module-jack`

The Eurorack module's front board (ADR 0023), behind the panel where the
jacks' bodies put it: the six jacks and the three pots, and nothing else.

**Its outline is a plain rectangle** (ADR 0024 point 15, the owner,
2026-10-01): full width, from just below the bottom jack row's footprints
(`config/module.yaml` `boards.jack_y0`, derived there) to the top edge it
shares with the main board — `mechanical/module/export/jack-board.dxf`. The
toggle's row and the etherCON are below it, so nothing passes through it;
until 2026-10-01 it was a U whose legs reached down beside them.
Everything it connects to is on [`module-main`](../module-main/README.md),
through `J-B2B-MOD`.

> **Status: laid out and routed by `tools/pcb.py` (`kind: module`), 2026-10-02.**
> `pcb.py check` passes: KiCad's DRC with schematic parity is clean, nothing is
> unrouted, every courtyard is inside the board, every CAD-placed part is
> where `mechanical/module/export/pcb-geometry.echo` puts it, and `J-B2B-MOD`
> mates with the main board's pin for pin. Two layers, `AGND_MOD` poured on
> both; layer 1 runs vertically and layer 2 across (`layout.yaml`
> `directions:`). The mask colour is **not decided** — green until the owner
> says (*Open*). The sheets are the source and pass KiCad's ERC. Every part
> has a footprint; the parts still missing a bought part are under *Open*.

## The layout

`layout.yaml` beside this file records how the first layout was made; the
`.kicad_pcb` is the source now. Everything but one part is placed by the
module CAD: the six jacks by their pins along the CAD's pin line, the pots by
their pins, `J-B2B-MOD` on the top face unmirrored, `H1`/`H2` on the CAD's
standoffs. What the layout decided:

- **`D-ESD-PITCH` (`D2`) on the rear, between `J-CV-PITCH`'s tip and its
  switch pad** — pitch-stage.md's *at the jack's tip and sleeve pads, before
  the trace leaves*.
- **`J-B2B-MOD`'s courtyard is drawn on the rear** (`connectors:` `body:
  rear`): its insulator is on the main board's side, so on the front only its
  pins stand between the jacks. On the front it overlapped every jack's
  courtyard.
- **The R0904N's courtyard** (`hardware/lib/woody.pretty`) was its bounding
  box, which reached the standoffs' heads between the pots; it now follows
  the body and the snap-in slots' pads, each 0.25 round.
- The CAD's jack positions put the bottom row's courtyards 0.055 mm inside
  the board's bottom edge (`config/module.yaml` `boards.jack_y0`'s
  derivation), and the outer pots' snap-in lugs 0.4 mm inside the sides.

It places:
- the `jack` pages of [`pitch-stage`](../../module/pitch-stage/pitch-stage.md)
  (`J-CV-PITCH`), [`breath-output-stage`](../../module/breath-output-stage/breath-output-stage.md)
  (`J-CV-BREATH`, `POT-GAIN`, `POT-OFFSET`),
  [`breath-response-shaper`](../../module/breath-response-shaper/breath-response-shaper.md)
  (`POT-RESP`) and [`mod-channels`](../../module/mod-channels/mod-channels.md)
  (`J-CV-MOD1`…`4`);
- **`J-B2B-MOD`** on its root sheet: the same header as the main board's, pin
  for pin. The allocation and its reasoning are in
  [`module-main/README.md`](../module-main/README.md#j-b2b-mod--the-allocation);
  `tools/kicad.py check` fails if the two sheets net a pin differently. This
  instance is `Assembly = none`: the one header is bought once.
  **Lay it out on the TOP side (F.Cu), NOT mirrored**, although its body is
  on this board's rear (the insulator is on the main board's front face).
  Pin *k* is one straight conductor through both boards, so it sits at the
  same panel-frame place on both, and both boards' KiCad top views are the
  panel view (`config/module.yaml` frame note): this board takes the same
  unmirrored pin map as the main board, pin 1 at the top left
  (`mechanical/module/export/pcb-geometry.echo` `J-B2B-MOD`). Put on B.Cu,
  the natural side for a part whose body is on the rear, it mirrors: odd and
  even columns swap and every net lands one column over. `tools/pcb.py
  check` catches that since 2026-10-02 (`pcb_module.check_b2b`): the header
  must be on the top face, and each pin k at the same panel-frame place and
  on the same net as the main board's.

The parts carry the references KiCad gives them on this board (`J1`, `RV2`);
`board-netlist.yaml` gives each one's BOM row (`of`) and circuit (`sheet`).
The same header is `J7` here and `J2` on the main board.

## Files

| File | What it is |
|---|---|
| `module-jack.kicad_sch` (+ the pages it places) | **Source** (ADR 0019) |
| `board-netlist.yaml` | Exported (`python3 tools/kicad.py export hardware/boards/module-jack`), with KiCad's ERC |
| `*.sch.png` | Renders, recorded in `hardware/SHEETS.csv` |
| `fp-lib-table`, `sym-lib-table` | Register `hardware/lib/` (the R0904N pot footprint) |


**The standoff pads are on the sheet:** `H1` and `H2` (`MountingHole_3.2mm_M3_Pad`, Row `MECH-STANDOFF-MOD`, excluded from the BOM) on `AGND_MOD` — the two standoffs above the pots (`standoff.at`), which with the six jack nuts are all that hold this board. It has no low standoffs: the main board's two low mounting points go to the panel (`MECH-PANEL-STANDOFF-MOD`, ADR 0024 point 15). The main board's pads are on no net, so they need no symbol and are placed board-only by the layout.

**The power LED is not on this board** since 2026-10-01: `LED-PANEL` is a panel-mount indicator whose lead plugs into `J-LED-PANEL` on the main board's front face (ADR 0024 points 15 and 16), and `J-B2B-MOD` pin 19, which carried its supply, is spare and unconnected here.

## Decided 2026-09-30

- **Two layers, 1.6 mm.** This board's only ground is `AGND_MOD`, arriving on
  `J-B2B-MOD`'s five ground pins (`dig-gnd-topology`).
- **The metal standoffs' pads are `AGND_MOD` here** and on no net on the main
  board, so they add no second tie between the boards.

## Open, and what decides each

| Item | Decided by |
|---|---|
| The pots and jacks have no LCSC number (Thonk and Song Huei/Alpha, bought by hand) | Nothing to decide: hand-placed, bought from the maker's stockists. `POT-GAIN`/`POT-OFFSET` are Song Huei R0904N with the 18-tooth **KC** shaft the T18 knob needs, `POT-RESP` Alpha's centre-click RV09 (rows) |
| The boards' mask colour (green in `layout.yaml` `fab:` until decided) | The owner, before the first order |
| The pots' shaft against the panel hole: the footprint (from drawing R09N-003, `R0904N.pdf` p.2) puts the snap-in slots, and so the shaft, 7.0 mm from the pin row; the module CAD (`config/module.yaml` `pot.pins`, from the STEP) 6.7. The layout places the pins where the CAD does, so the shaft sits 0.3 mm above the CAD's hole centre, inside the hole's 0.5 mm radial play (`pot.hole_d`) | Reading both banked sources again; the first panel's test-fit (`pot.hole_d`'s own `decided_by`) |
| The pots' rotation sense (which end is clockwise). Checked 2026-09-30 against both banked drawings — `R0904N.pdf` p.2 and `RV09AF-40.pdf` p.3 draw pins 1-2-3 with the shaft at full CCW and say nothing about which end the wiper approaches, so the sheets' "CW toward pin 3" stays `[from memory]` | Goods-in, E10: turn each pot fully CCW and read pin 1 to 2 with an ohmmeter — near 0 Ω confirms the sheets; near the full track means swap `CW`/`CCW` on all three symbols before the legends are drawn |
| Whether the reasons for `J-B2B-MOD`'s allocation still hold once the board is laid out. The panel layout is settled (ADR 0024 points 11–13), and the reasons were re-read against it | The layout, against `mechanical/module/export/pcb-geometry.echo` |
