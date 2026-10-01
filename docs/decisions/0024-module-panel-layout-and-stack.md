# 0024 — The module's panel layout and board stack

**Status:** Accepted, 2026-09-29. **Amended 2026-09-30** by the owner's
instruction (point 11): the etherCON is the bottom row, the toggle and the LED
are the row above it; **and again the same day** (point 12): the toggle throws
left–right. **Amended 2026-10-01** (point 13): BREATH and PITCH change
places, and so do MOD 2 and MOD 3; **and again the same day** (point 14): the
panel's material and finish, which ADR 0026 point 8 cited as specified here
and which this record had never written down; **and again the same day**
(point 15): the jack board is a plain rectangle ending above the toggle's
row, so the LED and the two low standoffs moved off it; **and again the
same day** (point 16): the light pipe is gone, and the LED is a panel-mount
indicator wired to a header on the main board. Made with the module's mechanical CAD, "up to
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
   the middle knob: BREATH and PITCH on the first row, under the knobs that
   shape breath, BREATH on the left; then MOD 1 and MOD 2 down the left
   column and MOD 3 and MOD 4 down the right (`layout.jacks`, point 13). Then the
   toggle, centred, on a row it shares only with the power LED (in the strip
   to its left), its lever thrown **right** for on (point 12). The NE8FAV
   last, centred, latch up, on the bottom row. *Amended 2026-09-30, point 11:
   this point first had the NE8FAV above the toggle, with the LED beside its
   flange; and point 12: the lever threw up for on.* The rows'
   heights are `layout.*` leaves; what they must clear is in the DRC's panel
   section.
2. **Legend zones are part of the layout** and are derived from what is
   around them, never drawn freehand: the title band; a band under each knob;
   a zone beside each jack on the panel's outer side; a zone between the LED
   and the toggle; the strip right of the flange; one right of the toggle.
   *Amended 2026-10-01: the four MOD jacks' zones were ADR 0004's write-on
   strip; ADR 0026 point 4 dropped the strip, and each zone carries its
   jack's printed pill.* `rules.legend_h` and `rules.legend_w` are
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
6. **The jack board is a plain rectangle** (point 15): full width, from just
   below the bottom jack row's footprints (`boards.jack_y0`) to the top edge
   it shares with the main board. SW-POWER's body, which is deeper than the
   jack board's depth (ADR 0023), and the NE8FAV are below it, so nothing
   passes through it (DRC: *jack board bottom edge*). The main board keeps
   the full outline; both are inside the rail band (`rail.band`) and
   `boards.side_margin` inside the panel's sides. *Amended 2026-10-01, point
   15: this point first made the jack board a U whose notch and step let the
   NE8FAV and the toggle's body through, its two legs carrying the LED and
   the lower standoffs.*
7. **J-B2B-MOD stands between the jack columns**, long axis vertical, and is
   soldered through both boards. Its pin length is derived (DRC: *J-B2B-MOD
   pin length (derived)*).
8. **Two standoffs between the boards** (`standoff.at`), above the pots,
   between them; **the main board's two low mounting points go to the
   panel** (`panel_standoff.at`, point 15). *Amended 2026-10-01: there were
   four between the boards, the low two in the jack board's legs.* **The
   between-board length is derived, not chosen** — the NE8FAV's
   setback less the jack's body and the jack board (DRC: *standoff length
   (derived)*). It cannot be met by moving the jack board, because the jack's
   body fixes that board's depth just as the NE8FAV fixes the main board's.
   So the stock 8 mm spacer is **faced to length**, as the key boards' spacer
   is (DRC: *standoff faced from stock*). ADR 0023 left this open.
9. **The LED is a panel-mount indicator, wired to a header on the main
   board** (point 16): `LED-PANEL` is held in the panel by its own nut, and
   its lead (`CBL-LED-PANEL`) plugs into `J-LED-PANEL` on the main board's
   front face. What it stands behind the panel, and the lead's run, are
   checked (DRC: *LED-PANEL behind the panel*, *CBL-LED-PANEL's run*).
   *Amended 2026-10-01, twice: this point first held a 3 mm LED by a lead
   spacer standing on the jack board's left leg; point 15 then made it an
   0805 on the main board under a press-fit light pipe.*
10. **J-PWR-EURO is on the main board's rear face, low on the right**, long
    axis vertical, pin 1 (−12 V, red stripe) at the bottom as Doepfer wants.
    The ribbon folds over the socket's strain relief and down to the bus
    board. The mated socket and its folded ribbon are the deepest thing in the
    module; the depth is reported against the Intellijel Palette **both ways**
    its manual can be read, from the panel's rear face and from its front
    (DRC: *depth behind the panel, against the Intellijel Palette*). **Since
    2026-09-30 it is an INFO line, not a rule** — the owner: *"Don't worry
    about module depth."*

11. **Nothing the player must reach sits under the umbilical** — amended
    2026-09-30. The owner: *"Power switch should not be underneath the
    connector."* In the layout of 2026-09-29 the toggle's row was directly
    below the NE8FAV, so the mated NE8MX and its cable hung over the switch.
    So the NE8FAV moved to the **bottom row** (`layout.ec_y`, as low as its
    locating pegs clear the rail band), where its cable drops below every
    control, and the toggle's row moved above it (`layout.toggle_y`), its
    lever's sweep between the PUSH tab and the last jack row's plug grips.
    The LED moved with the toggle, into the strip on the toggle's left (since
    point 16, a panel-mount indicator in its own hole); the strip beside
    the flange no longer carries anything but the umbilical's legend.

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
    The jack board's notch became shorter and gained the toggle's step
    (both gone since point 15). J-B2B-MOD, the standoffs, J-PWR-EURO and its ribbon
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

    **ON is to the right**, toward its `on` legend; OFF is to the left,
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
    toward the LED and the `on` legend; both legend zones are derived from
    it and are narrower by what it gained (DRC: *legend zone: LED-PANEL
    legend*, *legend zone: SW-POWER legend*). Across the row it is now the
    nut, so the lever is further from the PUSH tab below and the last jack
    row's plug grips above (DRC: *face parts clear of each other*, *plugs and
    knobs clear of the NE8MX, the PUSH tab, the toggle, the LED and the
    A-screws*) and from the drop zone (DRC: *no panel control under the
    umbilical*). Behind the panel, NKK's terminal field lies along the throw,
    so the body is now wide and short, and lower (since point 15 the jack
    board ends above it: DRC *jack board bottom edge*); the main board's
    wiring keep-out turns with it (`pcb-geometry.echo`). The row's height is unchanged, and so is
    `panel-height-budget`.

13. **BREATH and PITCH change places, and MOD 2 and MOD 3** — amended
    2026-10-01. The owner: *"swap the breath and pitch Jack locations"* and
    *"swap mod 2 and 3 position"*. The first row is BREATH on the left, PITCH
    on the right; the MOD jacks run down the columns, 1 and 2 on the left,
    3 and 4 on the right. Point 1 first had PITCH on the left and the MOD
    jacks across the rows. Each pill moves with its jack (ADR 0026,
    `art.text.jacks`).

    **Only names moved.** The six positions, the columns' pitch and every
    clearance are the same, so every DRC rule passes at the same value; only
    the part each rule names changed. **`J-B2B-MOD`'s allocation follows the
    jacks** — `BREATH_JACK` and `PITCH_JACK` trade pins, as do `MOD2_JACK` and
    `MOD3_JACK` — so each jack's tip still lands on its own column's side of
    the header, and no jack-board trace has to cross the header between its
    pads. That costs four labels on the main board's sheet and nothing in a
    layout, since neither board has one yet; the allocation and why are in
    [`module-main/README.md`](../../hardware/boards/module-main/README.md#j-b2b-mod--the-allocation).
    The DAC channels (ADR 0006) are untouched: MOD 2 is still MOD 2, at a
    new place on the panel.
14. **The panel is 2 mm aluminium, black-anodised, CNC-cut and UV-printed by
    one front-panel vendor** — amended 2026-10-01. ADR 0026 point 8 prints
    on "the black-anodised 2 mm aluminium ADR 0024 already specifies", but
    this record gave only the thickness (`panel.t`, Doepfer's). It is
    written here so the cite resolves: the anodise is the dark ground the
    artwork's knocked-out words read against (ADR 0026 point 1), and the
    vendor that anodises, cuts from `export/panel.dxf` and UV-prints
    `art/panel-art.pdf` with a white underprint is one order (Front Panel
    Express, Schaeffer class), not the key plate's laser or waterjet shop.
    One proof panel first, after the 1:1 paper check. `PANEL`'s BOM row
    orders it so.
15. **The jack board is a plain rectangle, ending above the toggle's row** —
    amended 2026-10-01. The owner, looking at the boards' picture
    (`renders/boards.png`): *"This cut out seems extra. Can we not rectangle
    it out up higher?"* The U of point 6 existed only to let the NE8FAV's
    body and SW-POWER's body through the board, and its two legs reached down
    beside them to carry the LED and the lower standoffs. Ending the board
    above the toggle's row removes the notch, the step and the legs together.

    **The bottom edge** is `boards.jack_y0`: the bottom jack row's footprints
    less `boards.copper_edge`, which leaves SW-POWER's body `boards.toggle_clear`
    or more below it (DRC: *jack board bottom edge*, which reports both
    margins and the NE8FAV's).

    **The LED moved to the main board, under a light pipe** — *superseded
    the same day by point 16; kept as the record of why.* On the main
    board a through-hole LED's leads would come out of the rear face under
    `U-ISO`'s body, which fills that face from the NE8FAV's tails to above
    the toggle's row on the left (`iso.at`). So `LED-PANEL` became an 0805
    (Lite-On LTST-C171GKT, the same GaP green as the 3 mm part it replaces)
    on the main board's **front** face, and `MECH-LED-BEZEL-MOD` a press-fit
    front-mount light pipe (Bivar PLP2-750) in the panel, its flange on the
    face and its end just short of the LED (`led.*`; DRC: *light pipe over
    the LED*, *LED-PANEL on the main board, under its light pipe*). The panel
    hole is the pipe's (`led.hole_d`), smaller than the lens's was. The
    `panel-led` circuit is placed on the main board's sheet now, and
    `J-B2B-MOD` pin 19, which carried its supply, is **spare** on both
    sheets; no other pin moved
    ([`module-main/README.md`](../../hardware/boards/module-main/README.md#j-b2b-mod--the-allocation)).

    **The main board's low mounting points go to the panel.** Moving the
    jack board's lower standoffs up beside the jacks was tried and does not
    fit: on the main board's rear face every place between the NE8FAV's tails
    and the jack rows is taken by `U-ISO`, its filter, `L-CM-ISO`,
    `J-PWR-EURO` and `J-B2B-MOD`'s tails, so there is nowhere for a screw
    head. The two low points stay where the legs' standoffs were (2 mm lower,
    clear of the umbilical's legend zone, `panel_standoff.at`) and are held
    from the **panel**: a PEM FHA-M3-8 self-clinching stud in the panel, a
    metal M3 spacer on it, faced to the NE8FAV's setback, and a screw from
    the main board's rear (`MECH-PANEL-STUD-MOD`, `MECH-PANEL-STANDOFF-MOD`;
    DRC: *panel standoff length (derived), faced from stock*, *panel studs:
    sheet and edge distance (PEM)*, *panel standoffs clear of the NE8FAV,
    SW-POWER, the LED and the jack board*). The jack board is held by its
    six jack nuts and the two standoffs above the pots, which is all it
    needs; its mounting pads are `H1` and `H2`. **The cost** is two flush
    D4.6 stud heads on the panel's face, inside island C.

16. **The LED is a panel-mount indicator with a lead to a header** —
    amended 2026-10-01. The owner: *"Let's remove power led light pipe and do
    a panel mount led with connector to header."* `MECH-LED-BEZEL-MOD` and
    the 0805 under it are gone. `LED-PANEL` is a **Dialight 605-2211-110F**:
    a 3 mm green LED recessed in a chrome M5 housing, in a D5.2 hole in the
    panel (`led.hole_d`), its head standing `led.proud` on the face and its
    nut on the rear face — the same place in the toggle's row, left of the
    toggle. Its leads are cut short and soldered to **`CBL-LED-PANEL`**, a
    two-wire lead with a JST XHP-2 that plugs into **`J-LED-PANEL`**, a JST
    B2B-XH-A on the main board's **front** face, `led.header_below` below the
    LED: pin 1 the anode (`LED_ANODE`), pin 2 the cathode (`AGND_MOD`).
    `R-LED-PANEL` stays on the board beside it. It is plugged in **before**
    the main board goes onto the panel studs.

    **Why this part.** It is a stock panel indicator whose own drawing gives
    the hole, the panel range (2 mm is inside its 3.5 mm maximum) and what
    stands behind the panel, and its M5 hole leaves the panel's left edge a
    web above `rules.web_min` where a 6 mm-hole bezel would not (DRC: *panel
    web from a cut to the panel's edge*). Its two banked catalogue pages
    disagree on the LED inside — 2 V, 15 mA, 70 mcd in 2021, 3 V, 20 mA,
    900–1400 mcd in 2026 — so `R-LED-PANEL` was re-derived across both and
    the panel-led sim re-run on both (`hardware/module/panel-led/sim`).

    **Behind the panel.** The housing, its nut and the leads' sleeved
    joints stand in the gap above the main board, below the jack board's
    bottom edge; the header is far enough below the LED that its mated
    housing is not under them, its tails on the rear face are below
    `U-ISO`'s body, and the wires leave its top with room to turn before the
    panel (DRC: *LED-PANEL behind the panel: in front of the main board*,
    *… clear of the jack board, SW-POWER, the NE8FAV, the panel standoffs
    and J-LED-PANEL*, *J-LED-PANEL on the main board's front face*,
    *J-LED-PANEL's mated housing behind the panel*, *CBL-LED-PANEL's run, LED
    to header*). The legend zone beside the LED is now measured from the
    head's edge (DRC: *legend zone: LED-PANEL legend*); `off` still fits it
    (`art/panel-art-check.txt`).

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

*2026-09-30: the circuit settled which board the toggle's lugs wire to —
both go to the main board, where `SW-POWER` sits in the top leg of the
LT1641's `ON` divider beside `U-LOADSW`
([`umbilical-load-switch.md`](../../hardware/module/umbilical-load-switch/umbilical-load-switch.md),
*The `ON` pin*). Nothing on the jack board connects to it.*

*2026-09-30, the owner: "Metal standoffs." `MECH-STANDOFF-MOD` is metal. Their
pads are on `AGND_MOD` on the jack board and on no net on the main board, so
they add no second ground tie between the boards
([`power-entry.md`](../../hardware/module/power-entry/power-entry.md),
*Grounding*). The part itself, and `config/module.yaml`'s `standoff.*` (which
still cite the polyamide spacer's datasheet), follow from the module CAD.*

*2026-10-01: the panel's legends, once open here, are decided by ADR 0026,
inside the zones this record fixes.*

| Item | Decided by |
|---|---|
| The rail band and the rail's depth (`rail.*`) | A rail maker's drawing banked, or the target case measured |
| The knob's bore depth and its gap to the panel (`knob.gap`) | The first fit, with the knob in hand |
| Whether a thumb on the PUSH tab has room under the toggle (points 11 and 12: the sweep's lower edge, now the nut's, is in the DRC's *face parts clear of each other* above the tab) | The 1:1 paper check with the NE8MX in hand, then the first panel |
| The umbilical's jacket and bend radius (`ethercon.umb_od`, `umb_bend_k`) | CABLE-UMB bought, and its datasheet |
| Whether the panel vendor clinches the two studs and prints over their flush heads (point 15) | The panel vendor's quote; the proof panel |
| The panel spacers' stocked length and part (`panel_standoff.stock_l`) | The metal spacer bought for `MECH-PANEL-STANDOFF-MOD` |
| Whether the LED reads right at its current (point 16): the two catalogues' parts differ by more than tenfold in intensity | The part in hand, looked at in a dim rack; `R-LED-PANEL` moves (up if the InGaN part glares, down if the 2021 part is dim) |
| The LED's nut and lock washer (`led.nut_d`, `led.nut_h`, tbd) | The part in hand |
