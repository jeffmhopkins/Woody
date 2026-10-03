# 0023 — The module's etherCON is the NE8FAV too, and the module is two boards

**Status:** Accepted, 2026-09-29. Decided by the owner, from the module parts
research (fragment R26). It settles ADR 0004's open question *which etherCON
variant at each end* **for the module's end**. The instrument's end was settled
by ADR 0021. **Amended 2026-09-29 by [ADR 0024](0024-module-panel-layout-and-stack.md)**
(point 3: the panel has no slot for the PUSH tab), at a dated note below.
**Amended 2026-10-03 by the owner** (point 2: the module is three boards - the
instrument's isolated supply on a board of its own, behind the main board;
issue #22), at a dated note below.

## Context

ADR 0004 left the module's etherCON open. Its panel budget was read off the
D-series feedthrough (NE8FDP), and `J-UMBILICAL`'s row named a "D-series
chassis (variant TBD)". A D-series feedthrough presents an RJ45 on the back.
So the module would have needed a patch lead to its board, with the same two
extra contact interfaces that ADR 0021 removed at the instrument's end.

A Eurorack module's board sits parallel to its panel. That is what a
"vertical PCB" etherCON is made for.

## Decision

1. **The module's etherCON is a Neutrik NE8FAV** (`J-UMBILICAL`): the
   A-series receptacle for a vertical PCB, mounted from behind the panel.
   It is the same part as the instrument's end, with the same footprint
   (`hardware/lib/woody.pretty/Neutrik_NE8FAV_etherCON_Vertical`) and the
   same 3D model. It solders straight into the module's main board, with no
   adapter, no patch lead and no extra contact interface. It is stocked at
   LCSC, C368526, which a D-series vertical part (NE8FDV) is barely
   [web LCSC, 2026-09-29].
2. **The module is two boards**, because the etherCON sets the depth of the
   board it is soldered to:
   - **the jack board**, behind the panel where the jacks' bodies put it: the
     jacks, pots and LED. It has a cut-out for the etherCON's body;
   - **the main board**, where the NE8FAV puts it, the flange's face to the
     PCB face (`config/body.yaml` `ethercon.pcb_setback`): the etherCON, every
     IC, the trimmers and the power header.

   A 2 × 10 header soldered through both boards joins them. Standoffs hold
   them apart. The toggle is panel-mounted and wired: its body is deeper
   than the gap in front of the jack board.

   *Amended 2026-10-03 by the owner (issue #22): "probably good to go to 3
   pcbs if needed", then "3 boards for module is correct". **The module is
   three boards**: the two above, and **the iso board** (`PCB-MODULE-ISO`),
   parallel to the main board and behind it, carrying the instrument's
   isolated supply - `U-ISO` and its filter (`L-ISO-IN`, `L-CM-ISO`, `C2`,
   `C-ISO-IN`, `C-ISO-Y`, `C-ISO-OUT`), ADR 0027. Why: the main board could
   not be routed cleanly inside its outline with a 25 mm converter's pins, its
   isolation gap and its return pour in the middle of the DAC's corner - re-placing
   that corner first left more connections unrouted, not fewer
   (`hardware/boards/module-main/README.md`). It is held off the main board's
   rear face by stock spacers used uncut (`MECH-STANDOFF-ISO`; the gap is
   their length) and joined to it by `J-B2B-ISO`, a 2 × 5 header soldered
   through both, its pins 5-6 left open as the isolation gap. Its outline,
   the gap and the header's pin length are derived in the module CAD
   (`config/module.yaml` `iso_board`, `b2b_iso`; `mechanical/module/drc.echo`):
   below the rear trimmers, so each stays adjustable from behind, and clear of
   `J-PWR-EURO` and its ribbon. The deepest thing behind the panel is now
   `L-CM-ISO` on the iso board (`mechanical/module/drc.echo`, *depths of the
   deep things*), still inside the Intellijel Palette's depth - reported, not
   ruled, since the owner's "Don't worry about module depth" (ADR 0024 point
   10). The main board still carries the etherCON, every other IC, the
   trimmers and the power header. The paragraphs above are what this point
   said before the amendment.*
3. **The power header is 2 × 8, while the module takes the bus's +5 V**:
   only the 16-pin bus carries it [ds `DOEPFER-A100-TECHNICAL-DETAILS-a100t_e.html`].
   Deriving +5 V locally instead is still open
   (`hardware/module/digital-and-supervision/digital-and-supervision.md`,
   *the bus +5 V rail*), and would allow a 10-pin header. The shroud is keyed,
   but a keyed shroud does not make a reversed ribbon impossible: Doepfer's
   own bus boards are unkeyed, "red strip down". `D-REVPOL` protects the
   ±12 V rails; the +5 V branch has no reverse protection, which is one of
   that open question's arguments.

   *Amended 2026-09-30 by the owner: "Create the 5v locally", and "We keep the
   standard header, we just don't use the 5 volt. This keeps commonality of
   all the Eurorack cable connectors." **The header stays 2 × 8 and the bus
   +5 V is not used**: its pins (and the CV and Gate pins) are no-connects,
   and the module makes its own 5 V from the protected +12 V
   (`hardware/module/power-entry/power-entry.md`, *The logic 5 V*). With the
   +5 V pins unconnected, a reversed ribbon has no unprotected rail to land
   on, so the concern above is resolved. The paragraph above is what this
   point said before the amendment.*
4. **The panel is the Doepfer A-100 standard at 10HP**, with four M3 screws
   and washers. The standard's dimensions are in `panel-width` and
   `panel-height-budget` (`config/figures.yaml`), from the banked Doepfer
   pages.

## Consequences

- **Depth.** The stack is set by the jacks' bodies at the front and the
  NE8FAV's setback behind them. The mated power plug is the deepest thing, and
  it clears an Intellijel Palette's 45.5 mm middle depth
  [ds `INTELLIJEL-PALETTE-CASE-MANUAL-2020-11-30.pdf`]. The module layout
  checks it with the parts in place.
- **The standoffs are not a stock length.** The gap between the boards is
  the NE8FAV's setback less the jack board's depth and thickness. That is a
  fraction of a millimetre off the stock M3 lengths, so the standoff is faced
  to length like the key boards' spacer, or the jack board's depth is set to
  suit. Decided at the module layout (`MECH-STANDOFF-MOD`).
- *Amended 2026-09-29 by [ADR 0024](0024-module-panel-layout-and-stack.md):
  **no slot.** The STEP, sliced, has nothing of the connector outside the
  bore's circle within `ethercon.tab_back` of the flange face, so the tab
  stands in front of any panel the NE8FAV accepts. The paragraph below is
  what this record concluded before the slice.*
  **The panel needs a slot for the PUSH tab as well as the bore.** On a
  rear-mounted NE8FAV the tab stands in front of the flange and above the
  bore (`config/body.yaml` `ethercon.tab_*`), so a thin panel must clear it.
  The instrument's tail cap has the same recess (ADR 0021). The panel drawing
  takes both from the NE8FAV's drawing and 3D model, and the first panel is
  test-fitted.
- **ADR 0004's D-series figures describe a part the module no longer uses:**
  the 24 mm bore, the 19 × 24 screw pattern, the 26 × 31 flange and the depth
  behind the panel. The NE8FAV is smaller on every one. So `panel-height-budget`
  keeps the D-series flange's height as a conservative allowance until the
  panel is laid out, and its conclusion is unchanged: the toggle still gets a
  row of its own, because the webs beside a 25 mm flange are still too thin.
- **The shell is plastic** where the D-series is zinc, and the panel may be
  3 mm thick at most. The standard 2 mm panel is inside that.
- **One connector part at both ends.** Both ends can be bought together, from
  one datasheet.

## Open, and what decides each

*2026-09-29: the module layout (ADR 0024) settled the first two rows: the
standoff is faced to the length `mechanical/module/drc.echo` derives, the jack
board's depth is the jack's body, and the panel's cut-out is Neutrik's with no
tab slot.*

| Item | Decided by |
|---|---|
| The standoff length and the jack board's exact depth | The module layout, with the jacks and the NE8FAV in hand |
| The panel's bore, tab slot and screw holes | The panel drawing, from the NE8FAV drawing and STEP; test-fitted |
| Whether the NE8MX cable connector latches in the NE8FAV | Before buying the cable connectors (ADR 0021) |
