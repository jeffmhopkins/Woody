# Breath excitation reference — simulation

**Nothing here has been run.** This directory holds the deck and the procedure.
It holds no results, and it will not hold any until a run produces them.

That is the rule, not an apology: `docs/reference/pcb-pipeline.md` names five
simulations worth running and records that **none has been**. A plausible
number written here would sit next to figures read off banked datasheets and be
indistinguishable from them. `datasheets/README.md` is explicit that a
fabricated document is worse than an honest gap; a fabricated simulation result
is the same thing with fewer bytes.

## The sim this circuit needs

**`R-ISO-REF` stability.** `pcb-pipeline.md` names it second in its ranked list,
and the reason it ranks there is that the sweep has already found the drawn
circuit to be the unstable one — the numbers are in that table and in
`riso-ref-topology`, and are not repeated here.

Two things have changed since that row was written, and both make the run more
worth doing rather than less:

- The row records the sim as **blocked on `cref-out-node` first**. That figure
  is now settled, so the block is lifted and the deck can be built against a
  known load.
- The compensation the page now draws is TI's dual-feedback network rather than
  the bare series resistor the sweep condemned. Its margins are cited in
  `riso-ref-topology` as simulated, and a simulated margin is what this
  directory exists to reproduce independently rather than inherit.

What the run has to answer is not "is it stable at nominal" — the topology
argument on the page already claims that, and claims it across a wide range of
`Zo` and `C_L`. It is whether the claimed **robustness** survives a deck built
by someone else: the same margins at the ends of that range, not just at the
middle of it.

## Running it

| | |
|---|---|
| Simulator | `ngspice` 42, stock Ubuntu archive, no allowlist change needed |
| **Do not use** | PySpice 1.5 — it treats every non-`Warning:` stderr line as fatal and ngspice prints a solver banner to stderr on every run. Raw netlists plus `subprocess` |
| Model | TI's OPA2197 macromodel. **Bank it in `datasheets/` with a SHA-256 first**, like every other document |
| `.spiceinit` | needs `set ngbehavior=psa` — **inside `.control` is too late** |

The load is not a bare capacitor. The sensor draws real current from `VS`, and
the handover frequency is what stops that current appearing as a scale-factor
error, so a deck that models the load as a capacitance alone cannot see the
failure the network was designed against.

## What a result is worth when it arrives

**A simulated phase margin is a screen with a ±10° bar, not a spec.** TI's own
macromodel runs optimistic against TI's own tabulated figures. A number from
here settles nothing on its own; it either agrees with the bench at E13 or it
tells you where to look.

Results land in `config/figures.yaml` with their provenance marked — not in
this file, and not in the page.
