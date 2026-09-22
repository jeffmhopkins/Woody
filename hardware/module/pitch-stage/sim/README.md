# Pitch stage — simulation

**Nothing here has been run.** This directory holds the deck and the procedure.
It holds no results, and it will not hold any until a run produces them.

That is the rule, not an apology: `docs/reference/pcb-pipeline.md` names five
simulations worth running and records that **none has been**. A plausible
number written here would sit next to figures read off banked datasheets and
be indistinguishable from them. `datasheets/README.md` is explicit that a
fabricated document is worse than an honest gap; a fabricated simulation
result is the same thing with fewer bytes.

## The sim this circuit needs, and why it is not optional

**Pitch transient into a passive mult.** `pcb-pipeline.md` records measured
**41.8 % overshoot at 82 nF and 65.4 % at 330 nF**, and — the part that makes
this a gate — that **the AC sweep is structurally blind to it** on the same
circuit at the same loads. The page's own *Still open* list carries the same
hazard from the other direction: joining `PITCH` to the `MOD` or `BREATH`
jacks through a passive mult gives several semitones of transient on every
note, a failure mode that did not exist before the feedback tap moved to the
jack.

So this is the one circuit where the DC argument being exactly right and the
AC sweep being clean still does not tell you whether it is safe to patch.

## Running it

| | |
|---|---|
| Simulator | `ngspice` 42, stock Ubuntu archive, no allowlist change needed |
| **Do not use** | PySpice 1.5 — it treats every non-`Warning:` stderr line as fatal and ngspice prints a solver banner to stderr on every run. Raw netlists plus `subprocess` |
| Model | TI's OPA2197 macromodel. **Bank it in `datasheets/` with a SHA-256 first**, like every other document |
| `.spiceinit` | needs `set ngbehavior=psa` — **inside `.control` is too late** |

## What a result is worth when it arrives

**A simulated phase margin is a screen with a ±10° bar, not a spec.** TI's own
macromodel runs optimistic against TI's own tabulated figures. A number from
here settles nothing on its own; it either agrees with the bench at E9 or it
tells you where to look.

Results land in `config/figures.yaml` with their provenance marked — not in
this file, and not in the page.
