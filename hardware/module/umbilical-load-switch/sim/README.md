# Umbilical load switch — simulation

**Nothing here has been run.** This directory holds the deck and the procedure.
It holds no results, and it will not hold any until a run produces them.

That is the rule, not an apology: `docs/reference/pcb-pipeline.md` names five
simulations worth running and records that **none has been**. A plausible
number written here would sit next to figures read off banked datasheets and
be indistinguishable from them. `datasheets/README.md` is explicit that a
fabricated document is worse than an honest gap; a fabricated simulation
result is the same thing with fewer bytes.

## The sim this circuit needs, and why it is not optional

**Behavioural LT1641.** `pcb-pipeline.md`'s reason for ranking it is exactly
what this directory is for: the page already writes the foldback law as
equations, and this is the circuit that was proven not to start.

Every figure on that page is closed-form arithmetic over a law read off a
banked datasheet — the foldback floor, the output at which the part escapes it,
the hot-plug start time, the `TIMER` margin against it. Closed form is the
right way to get those numbers and the wrong way to check them: a
misreading of the law reproduces itself identically in every line derived from
it, and the page's own history is that three reviewers agreed on a conclusion
and none of them found the mechanism.

So the deck is not here to discover a number. It is here to be a second,
differently-shaped derivation of numbers this corpus already states with their
arithmetic — `loadswitch-timer`, `loadswitch-gate-cap`, `loadswitch-fb-divider`
— and a model that *disagrees* with them is worth more than one that agrees.

## The deck's contract

| | |
|---|---|
| Simulator | `ngspice`, per `pcb-pipeline.md`'s stage 2, *Simulate* — no allowlist change needed |
| **Do not use** | PySpice 1.5 — it treats every non-`Warning:` stderr line as fatal and ngspice prints a solver banner to stderr on every run. Raw netlists plus `subprocess` |
| Model | **Behavioural.** No LT1641 SPICE model is banked; the part is built from the specified law in `datasheets/discrete-and-power/LT1641.pdf`, with the demo manual banked beside it as the corroborating source. If a vendor model is found, bank it with a SHA-256 first and run both |
| Cases | The two the page separates and sizes differently: the cold start, where the FET ramps, and the hot-plug, where it is already enhanced |
| Swept over | The datasheet's min/typ/max on the gate pull-up, the timer currents and the sense threshold. The page states its margins **at the corners**, so a deck run only at typical checks nothing it claims |
| Pass condition | The `TIMER` does not reach the fault threshold before the start completes, on worst-case silicon. Threshold, start time and the ratio between them are on the page and in `loadswitch-timer`; this file does not restate them |

## What a result is worth when it arrives

**A behavioural model cannot refute the datasheet — it can only fail to
reproduce it.** If the deck and the page disagree, one of the netlist, the
transcription of the law, or the arithmetic on the page is wrong, and finding
out which is the entire point. A model built from the same reading that is
being checked would agree with it for free, so the netlist is written from the
PDF and not from the page.

Results land in `config/figures.yaml` with their provenance marked — not in
this file, and not in the page.
