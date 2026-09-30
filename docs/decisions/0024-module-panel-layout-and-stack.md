# 0024 — The module's panel layout and board stack

**Status:** Accepted, 2026-09-29. **Amended 2026-09-30** by the owner's
instruction (point 11): the etherCON is the bottom row, the toggle and the LED
are the row above it; **and again the same day** (point 12): the toggle throws
left–right. Made with the module's mechanical CAD, "up to
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
   shape breath, then MOD 1–4 read like text (`layout.jacks`). Then the
   toggle, centred, on a row it shares only with the power LED (in the strip
   to its left), its lever thrown **right** for on (point 12). The NE8FAV
   last, centred, latch up, on the bottom row. *Amended 2026-09-30, point 11:
   this point first had the NE8FAV above the toggle, with the LED beside its
   flange; and point 12: the lever threw up for on.* The rows'
   heights are `layout.*` leaves; what they must clear is in the DRC's panel
   section.
2. **Legend zones are part of the layout** and are derived from what is
   around them, never drawn freehand: the title band; a band under each knob;
   a zone beside each jack on the panel's outer side (the MOD write-on strip
   of ADR 0004 is these four); a zone between the LED and the toggle; the
   strip right of the flange; one right of the toggle. `rules.legend_h` and `rules.legend_w` are
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
   `boards.ec_clear` and is open to the bottom edge; above it, a narrower
   step of the same cut-out clears the toggle's body by
   `boards.toggle_clear`, because that body is deeper than the jack board's
   depth (ADR 0023) and passes through the board (DRC: *jack board notch
   clear of SW-POWER's body*). Its two legs carry the LED and the lower
   standoffs. Both boards have the
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

11. **Nothing the player must reach sits under the umbilical** — amended
    2026-09-30. The owner: *"Power switch should not be underneath the
    connector."* In the layout of 2026-09-29 the toggle's row was directly
    below the NE8FAV, so the mated NE8MX and its cable hung over the switch.
    So the NE8FAV moved to the **bottom row** (`layout.ec_y`, as low as its
    locating pegs clear the rail band), where its cable drops below every
    control, and the toggle's row moved above it (`layout.toggle_y`), its
    lever's sweep between the PUSH tab and the last jack row's plug grips.
    The LED moved with the toggle, into the strip on the toggle's left, which
    the jack board's left leg stands behind; the strip beside the flange no
    longer carries anything but the umbilical's legend.

    **The rule is checkable now.** The *drop zone* is the NE8MX's grip
    (`ethercon.cable_d`, off `NE8MX.pdf`) and a strip that wide from the axis
    down past the panel's bottom edge, which is where a cable leaving the
    plug and bending down under its own weight hangs, seen from the front.
    DRC: *no panel control under the umbilical: clear of the NE8MX's grip and
    its cable's drop zone* measures every knob at its 14 mm budget, every
    patch plug's grip, the toggle's sweep and nut, and the LED against it, and
    wants a plug grip's clearance (`rules.plug_gap_min`). A second rule makes
    the zone hold at every height: *the umbilical's plug stands proud of every
    control* — the NE8MX's back, at its short length (`ethercon.plug_l_min`)
    and fully home to the NE8FAV's PCB face, still stands further out than
    the tallest thing on the face, so no control can get out from under the
    cable by being taller. The cable's bend (`ethercon.umb_od` ×
    `ethercon.umb_bend_k`, both `tbd`) is reported as INFO: how far in front
    of the panel the hanging run stands, and where the bend has turned it
    straight down. The layout of 2026-09-29 fails the first rule: its
    toggle's sweep lay inside the strip.

    **What moved with it, behind the panel.** The main board's NE8FAV moves
    down with the panel's; its depth is unchanged (`ethercon.pcb_setback`).
    The jack board's notch is shorter and gains the toggle's step, which is
    what now sets the least room under the lowest jacks (DRC: *lowest jacks
    above the notch*). J-B2B-MOD, the standoffs, J-PWR-EURO and its ribbon
    route did not need to move: each is re-checked by the rules it already
    had, and the header still clears the NE8FAV's tails, which are now below
    it and to its left. The depth against the Palette is unchanged, because
    nothing moved in depth.

    **ADR 0004's conclusion holds**: the toggle still has a row of its own —
    it is not beside the flange, where the webs are too thin — and shares it
    only with the LED, whose hole (`led.hole_d`) has room in the strip beside it.
    `panel-height-budget` sums the same rows at the same heights in a
    different order, so its value is unchanged; its `toggle_row` note says
    where the LED now is.

12. **The power toggle throws left–right** — amended 2026-09-30. The owner:
    *"I think power switch should just go left to right and [not] up and down
    to avoid inadvertent triggering."* A lever that throws up and down is
    thrown by anything dragged down the panel — a hand reaching for a jack, a
    patch cable pulled out and down, the NE8MX's own cable being mated below
    it. Across the panel, none of those push along the throw.

    **ON is to the right**, toward the POWER legend; OFF is to the left,
    toward the LED (`layout.toggle_on`). The M2011 is ON in NKK's *Down*
    position, the lever away from the bushing's keyway (`NKK-SERIES-M-TOGGLE.pdf`
    p.5, A56, the circuit table's position icons), and the D4 bushing's flat
    is drawn where the S4's keyway is, across from the lever (p.7, A58). **So
    the flat is on the left**, and the panel's D-hole is turned to put it
    there. The model derives the flat, the sweep, the body and its lugs from
    that one leaf, so they cannot disagree with each other again — and they
    did: the layout of 2026-09-29 drew the flat up and called up ON, which by
    NKK's own table is OFF. The D4's hardware is two hex nuts and a
    lockwasher with no locking ring (p.7's hardware table), so the flat is the
    only anti-rotation feature and the panel needs no second hole.

    **What turned with it.** On the face, the sweep now lies along the row,
    toward the LED and the POWER legend; both legend zones are derived from
    it and are narrower by what it gained (DRC: *legend zone: LED-PANEL
    legend*, *legend zone: SW-POWER legend*). Across the row it is now the
    nut, so the lever is further from the PUSH tab below and the last jack
    row's plug grips above (DRC: *face parts clear of each other*, *plugs and
    knobs clear of the NE8MX, the PUSH tab, the toggle, the LED and the
    A-screws*) and from the drop zone (DRC: *no panel control under the
    umbilical*). Behind the panel, NKK's terminal field lies along the throw,
    so the body is now wide and short: the jack board's step for it is wider
    and lower (DRC: *board outlines*, *jack board notch clear of SW-POWER's
    body*), which gives back room under the lowest jacks (DRC: *lowest jacks
    above the notch*); the main board's wiring keep-out turns with it
    (`pcb-geometry.echo`). The row's height is unchanged, and so is
    `panel-height-budget`.

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
| Whether a thumb on the PUSH tab has room under the toggle (points 11 and 12: the sweep's lower edge, now the nut's, is in the DRC's *face parts clear of each other* above the tab) | The 1:1 paper check with the NE8MX in hand, then the first panel |
| The umbilical's jacket and bend radius (`ethercon.umb_od`, `umb_bend_k`) | CABLE-UMB bought, and its datasheet |
