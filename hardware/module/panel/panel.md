# Module panel — geometry and control layout

**A board-level page, not a circuit**, so it carries no `## Interfaces` table.
Its subject is the module's front panel: width, clear height, how many rows of
controls fit and how big the knobs may be. The tracked figures for that are
`panel-width` and `panel-height-budget` in `config/figures.yaml`, whose owner
is `docs/decisions/0004-cv-interface-module.md` — this page cites them and
does not restate them. It exists so that panel reasoning is collected here
rather than filed under whichever circuit happened to provoke it.

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

**The cost is knob diameter.** Three pots across 50.50 mm with 3 mm gaps
needs **≤14 mm knobs**; 15 mm already gives 51 mm and does not fit. So
10HP buys the height back by spending the knob size 8HP was supposed to
have bought. Three controls at 14 mm beats two at 16 mm — but ADR 0004's
claim of "16–20 mm knobs" is withdrawn rather than quietly left standing.

It also makes room for the op-amp package the *other* review finding
needs: `A5` showed `POT-OFFSET`'s wiper is unbuffered, which is why its
"zero at centre" actually sits ~20° past centre at +0.605 V. That fix
wants a half, and this stage takes the last two.
