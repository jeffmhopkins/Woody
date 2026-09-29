# 0024 — The module's panel layout and board stack

**Status:** Accepted, 2026-09-29. Made with the module's mechanical CAD, "up to
the line before board layout". It takes ADR 0023's two-board decision to
positions and lengths, and it **reverses one of 0023's consequences**: the
panel has no slot for the NE8FAV's PUSH tab (point 3).

Every number this record decides is a leaf of `config/module.yaml`, with its
status and source. Every number it derives is a rule in
`mechanical/module/drc.echo`, named here and not restated. The pictures are in
[`mechanical/module/README.md`](../../mechanical/module/README.md).

## Context

ADR 0004 fixed the panel's rows and budget (`panel-width`,
`panel-height-budget`); ADR 0023 fixed the connector and split the module
into a jack board and a main board. Neither placed anything. The open items
0023 left were the standoff length, the jack board's depth, the panel's bore,
tab slot and screw holes — all "decided at the module layout". That layout is
a model now (`mechanical/cad/module.scad`), with a design-rule report, an
interference check on envelopes and cut files, so each decision below is
checked rather than asserted.

## Decision

1. **The panel, top to bottom, is ADR 0004's five rows, placed.** A title band
   under the top screws' washers. The three pots across, gain, offset,
   response (`layout.pots`). Six jacks in two columns of three that straddle
   the middle knob: PITCH and BREATH on the first row, under the knobs that
   shape breath, then MOD 1–4 read like text (`layout.jacks`). The NE8FAV
   centred, latch up, with the power LED in the strip to its left at its axis
   height. The toggle centred on a row of its own under it, lever thrown up
   for on. The rows' heights are `layout.*` leaves; what they must clear is
   in the DRC's panel section.
2. **Legend zones are part of the layout** and are derived from what is
   around them, never drawn freehand: the title band; a band under each knob;
   a zone beside each jack on the panel's outer side (the MOD write-on strip
   of ADR 0004 is these four); a zone above the LED; the strip right of the
   flange; one beside the toggle. `rules.legend_h` and `rules.legend_w` are
   their minimum sizes; each zone is DRC'd against every knob, plug grip,
   nut, screw head, the NE8MX and the washers.
3. **No slot for the PUSH tab.** Sliced from the banked STEP
   (`NEUTRIK-NE8FAV-3D.stp`, 2026-09-29): nothing of the connector lies
   outside a 22 mm circle within `ethercon.tab_back` of the flange face; the
   tab's plate stands in front of that, and its stem rises inside the bore.
   Any panel up to the NE8FAV's own `panel_max` is therefore behind the plate,
   and Neutrik's rear-mount cut-out (ST-NE8FAV) has no slot either. The
   instrument's tail cap still needs its recess (ADR 0021): the cap is
   thicker than `tab_back`. DRC: *PUSH tab clear of the panel - no slot*.
4. **The mounting cuts are Doepfer's holes, slotted horizontally** by
   `panel.slot_travel`, as the banked fabricated panel
   (`EURORACK-3U-3HP-PANEL-apfaudio-pmod-r3.1.kicad_pcb`) cuts them, so the
   panel takes a rail's nut strip wherever it sits in the HP grid. Four, at
   ADR 0023 point 4. The washers' reach is checked along the whole slot.
5. **The jacks lie on their sides**: pins across the panel, the sleeve toward
   the nearer side edge. A PJ398SM's footprint along its pin line is longer
   than ADR 0004's 13 mm column pitch, so pins down the column would put one
   jack's sleeve pad on the next one's tip pad (DRC: *why the jacks lie on
   their sides*, from the banked `PJ398SM.kicad_mod`). Across, the columns
   are `layout.jack_pitch_x` apart, which is what leaves J-B2B-MOD room
   between them.
6. **The jack board is a U.** Its notch clears the NE8FAV's body by
   `boards.ec_clear` and is open to the bottom edge, so the toggle's body,
   which is deeper than the jack board's depth (ADR 0023), sits in it too.
   Its two legs carry the LED and the lower standoffs. Both boards have the
   same outline, inside the rail band (`rail.band`) and `boards.side_margin`
   inside the panel's sides.
7. **J-B2B-MOD stands between the jack columns**, long axis vertical, and is
   soldered through both boards. Its pin length is derived (DRC: *J-B2B-MOD
   pin length (derived)*).
8. **Four standoffs** (`standoff.at`): two above the pots, between them; one
   low in each leg. **Their length is derived, not chosen** — the NE8FAV's
   setback less the jack's body and the jack board (DRC: *standoff length
   (derived)*). It cannot be met by moving the jack board, because the jack's
   body fixes that board's depth just as the NE8FAV fixes the main board's.
   So the stock 8 mm spacer is **faced to length**, as the key boards' spacer
   is (DRC: *standoff faced from stock*). ADR 0023 left this open.
9. **The LED is held by a lead spacer** standing on the jack board, which
   stops its flange (its flange is the panel hole's size, so nothing on the
   panel can). That is `MECH-LED-BEZEL-MOD`, and its length is derived (DRC:
   *LED lead spacer length (derived)*).
10. **J-PWR-EURO is on the main board's rear face, low on the right**, long
    axis vertical, pin 1 (−12 V, red stripe) at the bottom as Doepfer wants.
    The ribbon folds over the socket's strain relief and down to the bus
    board. The mated socket and its folded ribbon are the deepest thing in the
    module; the depth is checked against the Intellijel Palette **both ways**
    its manual can be read, from the panel's rear face and from its front
    (DRC: *depth behind the panel, against the Intellijel Palette* and *depth
    from the panel's FRONT face, against the same*). Both pass.

## Consequences

- **The module has its own model, config, outputs and ledger**
  (`mechanical/cad/module.scad`, `config/module.yaml`,
  `mechanical/module/outputs.yaml`, `mechanical/module/OUTPUTS.csv`), built by
  the same `tools/cad.py`. A change to the instrument body never marks the
  module's pictures stale, nor the reverse. The NE8FAV's numbers are not
  restated: `config/module.yaml` refers to `config/body.yaml`'s `ethercon.*`,
  and names `panel-width` and `panel-toggle-hole` so that `cad.py` fails if
  either figure moves.
- **The board layout starts from `mechanical/module/export/`**: both
  outlines as DXF, the panel's cut file, and `pcb-geometry.echo` in the body's
  format — every jack, pot, the LED, both connectors, the standoffs, the tall
  parts' envelopes and each face's keep-outs and height limits.
- **Panel-height-budget holds with room.** The NE8FAV's flange is shorter
  than the D-series allowance the figure keeps, and every face rule passes.
  The figure is unchanged; its own note says the 1:1 paper check is still
  the gate, and it still is.
- **Several envelopes are `tbd`** — the rail band, the patch plug's grip, the
  knob's bore, the jack and toggle nuts, the bulk cap's height, the A-screw's
  head. The DRC lists every one in play; each has a `decided_by`.

## Open, and what decides each

| Item | Decided by |
|---|---|
| The rail band and the rail's depth (`rail.*`) | A rail maker's drawing banked, or the target case measured |
| Metal or nylon standoff (`MECH-STANDOFF-MOD`) | Whether the standoffs carry ground between the boards — the layout's grounding scheme |
| Which toggle lug wires go to which board | The board layout; the DRC gives the lugs' clearance in front of the main board |
| The knob's bore depth and its gap to the panel (`knob.gap`) | The first fit, with the knob in hand |
| The panel's legends | The artwork, inside the zones this record fixes |
