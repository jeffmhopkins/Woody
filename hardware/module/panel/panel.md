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
| `LED-PANEL` bezel | — | `module/panel-led` | `panel-height-budget` | Beside the etherCON flange; the figure's `toggle_row` note is what establishes that it fits |
| `SW-POWER` toggle | — | `module/umbilical-load-switch` | `panel-toggle-hole`, `panel-height-budget` | The shaped hole this page owns — it has to be in the DXF because it cannot be cut afterwards. The switch's net is that circuit's |
| etherCON flange | — | — | `panel-width` | The umbilical connector's panel cutout |

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
"zero at centre" actually sits ~20° past centre at +0.605 V. That fix
wants a half, and this stage takes the last two.
