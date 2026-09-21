# Module power entry — simulation

**Nothing here has been run.** This directory holds the deck and the procedure.
It holds no results, and it will not hold any until a run produces them.

That is the rule, not an apology: `docs/reference/pcb-pipeline.md` names five
simulations worth running and records that **none has been**. A plausible
number written here would sit next to figures read off banked datasheets and
be indistinguishable from them. `datasheets/README.md` is explicit that a
fabricated document is worse than an honest gap; a fabricated simulation
result is the same thing with fewer bytes.

## The sim this circuit needs, and why it is not optional

**Power-on / reset transient.** `pcb-pipeline.md` ranks it on a gap rather than
on a disagreement: the corpus makes power-on claims on several pages and holds
no transient anywhere. This is the page most of those claims are made *about* —
the four rails arrive here, and `dac-rail` is produced here from one of them.

The claims are not in conflict with each other. They are simply unchecked, and
they are all steady-state reasoning applied to an edge: what order the rails
reach their loads in, what the LM317 does while its own input is still rising,
and what the DAC's supply is doing at the moment firmware's first write lands.
Nothing in this corpus has looked at that window, and every page that asserts
something about it asserts it from the settled values.

## The deck's contract

| | |
|---|---|
| Simulator | `ngspice`, per `pcb-pipeline.md` §2 — no allowlist change needed |
| **Do not use** | PySpice 1.5 — it treats every non-`Warning:` stderr line as fatal and ngspice prints a solver banner to stderr on every run. Raw netlists plus `subprocess` |
| Models | The LM317 and the entry Schottky. **Bank each model in `datasheets/` with a SHA-256 first**, like every other document. The Schottky's own curve is already banked at `datasheets/discrete-and-power/1N5817.pdf` and is what a model has to reproduce |
| Stimulus | The bus rails arriving at `J-PWR-EURO`, and the same edge in reverse |
| Loads | The analog rails at their real load, not open circuit — the bead impedances are bias-dependent (`ferrite-bias-impedance`) and an unloaded deck gets the wrong ones |
| Pass condition | `dac-rail`'s stated floor, which is a hard one. It is in the register and in the page; this file does not restate it |

## What a result is worth when it arrives

**A simulated transient is a screen, not a spec.** It is worth exactly the
models it was run on, and both of the ones above are vendor macromodels of
parts whose real behaviour on this edge is what is in question. A number from
here either agrees with the bench or it tells you where to look.

Results land in `config/figures.yaml` with their provenance marked — not in
this file, and not in the page.
