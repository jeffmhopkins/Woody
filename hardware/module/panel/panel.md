# Module panel — geometry and control layout

**The module's front panel** — width, clear height, how many rows of
controls fit and how big the knobs may be. The tracked figures for that are
`panel-width` and `panel-height-budget` in `config/figures.yaml`, whose owner
is `docs/decisions/0004-cv-interface-module.md` — this page cites them and
does not restate them. It exists so that panel reasoning is collected here
rather than filed under whichever circuit happened to provoke it.

**This page used to call itself "a board-level page, not a circuit" and carry
no `## Interfaces` table**, while carrying a `circuit.yaml` that two circuits
declared a dependency on. It is a circuit directory like the others; the
contradiction is resolved that way rather than by deleting the graph node,
because a panel-mounted part is where another circuit's net ends, and every
one of this module's jacks, pots and the toggle is a panel-mounted part.
What crosses this boundary is mechanical rather than electrical — a
cutout, a bushing, a knob envelope — so every row's `Dir` is `—`.

## Interfaces

Every part of this circuit that another circuit's net terminates on.
Quantities appear **only** as a citation into `config/figures.yaml` — this
table names nodes, it does not restate values.

The `Dir` and `Peer` columns are defined once in
[`hardware/README.md`](../../README.md#the-interfaces-table).

| Node | Dir | Peer | Figure | Note |
|---|---|---|---|---|
| `POT-GAIN`, `POT-OFFSET` | — | `module/breath-output-stage` | `panel-width`, `panel-height-budget` | Two of the three pots. What they do electrically is on that page; the row they sit in and the knob envelope are here |
| `POT-RESP` | — | `module/breath-response-shaper` | `panel-width`, `panel-height-budget` | The third pot — the one that made three-across a single row instead of two |
| `PITCH` jack | — | `module/pitch-stage` | `panel-height-budget` | A panel cutout. The net is that circuit's |
| `BREATH_OUT` jack | — | `module/breath-output-stage` | `panel-height-budget` | A panel cutout. The net is that circuit's |
| `MOD 1`–`MOD 4` jacks | — | `module/mod-channels` | `panel-height-budget` | Four cutouts in the jack rows. The nets are that circuit's |
| `LED-PANEL` light pipe | — | `module/panel-led` | `panel-height-budget` | In the toggle's row, left of the toggle (ADR 0024 point 11); the figure's `toggle_row` note is what establishes that the row fits. A press-fit light pipe in the panel (`MECH-LED-BEZEL-MOD`, `led.hole_d`) over the LED on the main board (ADR 0024 point 15) |
| panel studs | — | — | — | Two self-clinching studs (`MECH-PANEL-STUD-MOD`) holding the main board's low spacers (ADR 0024 point 15): two holes in the cut file, and two flush heads that show on the face, inside island C (`panel_standoff.*`) |
| `SW-POWER` toggle | — | `module/umbilical-load-switch` | `panel-toggle-hole`, `panel-height-budget` | The shaped hole this page owns — it has to be in the DXF because it cannot be cut afterwards. The switch's net is that circuit's |
| etherCON flange | — | — | `panel-width` | The umbilical connector's panel cutout |

## The layout

**Placed by [ADR 0024](../../../docs/decisions/0024-module-panel-layout-and-stack.md)**
and modelled in `mechanical/cad/module.scad`; every position is a leaf of
`config/module.yaml` (`layout.*`, with its status and source), and every
clearance is a rule in `mechanical/module/drc.echo`. Nothing below restates
either. The drawing is `mechanical/module/renders/panel.png`, and the cut
file is `mechanical/module/export/panel.dxf` — generated, fingerprinted, and
the one that goes to the cutter.

Top to bottom it is ADR 0004's five rows: the title band under the top
screws' washers; the three knobs across, gain, offset, response (legend *curve*, ADR 0026); the six
jacks in two columns straddling the middle knob — BREATH and PITCH first,
then MOD 1 and 2 down the left column and MOD 3 and 4 down the right (ADR 0024
point 13) — **lying on their sides**, pins across, because a PJ398SM's
footprint is longer than the column pitch; `SW-POWER` centred on a row of its
own, in the shaped hole `panel-toggle-hole` gives, with `LED-PANEL`'s light
pipe in the strip to its left; and the NE8FAV centred, latch up, **on the
bottom row**. Low on the left and right, beside the NE8FAV, two self-clinching
studs hold the main board's low spacers (ADR 0024 point 15); their flush heads
show.

- **The toggle throws left–right, ON to the right** (ADR 0024 point 12, the
  owner's instruction of 2026-09-30, "to avoid inadvertent triggering"). The
  hole's D-flat is therefore on its **left**: the M2011 is ON with the lever
  away from the flat, by NKK's own circuit table. The drawing outlines the
  lever's sweep and marks ON; `layout.toggle_on` owns the side, and the flat
  turns with it in the cut file.
The four mounting cuts are Doepfer's holes slotted sideways, as a fabricated
panel cuts them.

- **Nothing the player must reach is under the umbilical** (ADR 0024 point
  11, the owner's instruction of 2026-09-30). The NE8FAV is the bottom row so
  that the mated NE8MX and its cable drop below every control. The drawing
  shades the *drop zone* — the NE8MX's grip and the strip its cable hangs in —
  and the DRC rule *no panel control under the umbilical: clear of the
  NE8MX's grip and its cable's drop zone* keeps every knob, plug grip, the
  toggle and the LED out of it.

- **There is no slot for the NE8FAV's PUSH tab** (ADR 0024 point 3): the tab
  stands in front of any panel the connector accepts. The bore and the two
  screw holes are Neutrik's rear-mount cut-out.
- **The legend zones are derived, not drawn**: each is the space its
  neighbours leave, and each is DRC'd against every knob, plug grip, nut and
  screw head. The artwork goes inside them.
- **The printed graphics are [ADR 0026](../../../docs/decisions/0026-module-panel-graphics.md)**:
  a dark three-tone language after Pittsburgh Modular's black Lifeforms
  panels — grey islands for the breath knobs, the outputs and power/link,
  a light-grey header pill, white lowercase Inter, no scales but OFFSET's −
  and +; every jack is an output and its word — *pitch, breath, mod 1–4* —
  is knocked out of a light-grey pill. *woody* sits between the two top
  screws, *space coast synthesizers* under it. The knobs read **gain, offset, curve** (the owner,
  2026-09-30: POT-RESP's legend is *curve*); the toggle **off / on** in
  words. The words are `config/module.yaml` `art.text.*`; the print file is
  `mechanical/module/art/panel-art.pdf`, generated by `tools/panel-art.py`
  from the CAD's zones and failed on any placement rule
  (`mechanical/module/art/panel-art-check.txt`). Open: curve's end marks,
  until `breath-response-shaper` says which end is linear.
- **The knob is sized by `KNOB-BREATH`'s 14 mm budget** for spacing, and by
  the chosen Thonk 1900h for the picture; both are checked.
- `panel-height-budget` is unchanged and holds: the rows are the ones it
  sums, in a different order, and the NE8FAV's flange is shorter than the
  D-series allowance the figure keeps. The 1:1 paper check is still the gate
  — with the NE8MX in hand, for the thumb on its PUSH tab under the toggle.

## Where the panel width came from

*The block below moved verbatim from
`hardware/module/breath-output-stage/breath-output-stage.md`, 2026-09-21,
where it sat inside the response control's cost section — a cold review called
it the single most misfiled range in the corpus. Only the blockquote prefixes
were stripped.*

### The panel goes to 10HP — decided 2026-09-21

`B1` reconstructed the panel bottom-up from real component envelopes and
got **~115 mm against a "~110 mm usable" that was itself never derived** —
already over *before* this control — and found that ADR 0004's "107 mm"
figure was asserted twice and **derived nowhere**.

**10HP is 50.50 mm, and the win is not the extra width.** It is that three
pots fit in **one row instead of two**, which deletes a 20+ mm row from a
budget that had already overrun. The derived layout is in ADR 0004 and the
total is the tracked figure `panel-height-budget` — **110 mm of content
against 115.5 mm of clear panel**, with the usable height finally derived
rather than asserted, and the toggle on a row of its own.

**The toggle needs a shaped hole, not a round one** — `panel-toggle-hole`,
the other figure this page owns: **6.5 mm diameter with a 5.8 mm D-flat**.
The flat is what stops the switch rotating in the panel, and it has to be in
the DXF because it cannot be added afterwards. The sourced bushing is 6 mm
metric, so a 6.0 mm round hole is *not* the right cut — that spelling of the
hole is superseded.

**The cost is knob diameter.** Three pots across 50.50 mm with 3 mm gaps
needs **≤14 mm knobs**; 15 mm already gives 51 mm and does not fit. So
10HP buys the height back by spending the knob size 8HP was supposed to
have bought. Three controls at 14 mm beats two at 16 mm — but ADR 0004's
claim of "16–20 mm knobs" is withdrawn rather than quietly left standing.

It also makes room for the op-amp package the *other* review finding
needs: `A5` showed `POT-OFFSET`'s wiper is unbuffered, which is why its
"zero at centre" is not at centre — where it is, and which way of centre,
is on [`breath-output-stage.md`](../breath-output-stage/breath-output-stage.md),
which owns both numbers. That fix
wants a half, and this stage takes the last two.
