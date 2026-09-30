# Pitch stage — simulation

`sims.yaml` says what is simulated and what every run must show;
`pitch-step.cir` and `pitch-loop.cir` are the decks; `results.yaml` is what the
last run found, **generated** by
`python3 tools/sim.py run hardware/module/pitch-stage/sim`.
`python3 tools/sim.py show <this dir>` prints it as a table.
`docs/reference/tooling.md` §5 explains the tool.

**No part value is written here.** The decks read this circuit's netlist and,
for the loads a passive mult joins to `PITCH`, the other outputs' jack parts:
`mod-channels`' `C-FILT-MOD-1` and `R-OUT-PROT-1`, `breath-output-stage`'s
`C-OUT-BREATH`. Both op-amp halves are TI's OPA2197 model, banked in
`datasheets/analog/`.

## What it shows

An octave step from the DAC (an ideal edge, harder than the DAC8568's own
settling), through `R-OPAMP-IN`/`C-AA-PITCH`, into the stage as netlisted with
the DC loop closed at the jack. Every sim runs at the nominal and every
tolerance end of `C-FB-PITCH`, `C-FILT-PITCH` and `R-OUT-PROT` (9 runs).

| Sim | Load on the jack | Holds |
|---|---|---|
| `step-vco` | one VCO input | under 5 % overshoot at every corner |
| `step-mult[mult=1]`, `[mult=2]` | a passive mult to a MOD jack (its 82 nF) or the BREATH jack (its 330 nF) — the page's own model, the capacitor alone | **a recorded hazard**: over 25 % |
| `step-real-mult[…]` | the same, with that output's own `R-OUT-PROT` to its driver as well | recorded only |
| `loop[mult=…]` | the loop gain at all three loads, broken at `U-PITCH-AMP`'s (−) input | phase margin over 45° after the ±10° screen |

**The result is `pitch-mult-overshoot`: 41.8 % at 82 nF, 64.1 % at 330 nF**,
at the nominal; the corners move it by about a point either way. An octave step
overshooting by 64 % is 7.7 semitones [calc: 0.641 × 12].

**The AC sweep is blind to it, and the run shows why.** The phase margin at
crossover is the same at all three loads to a tenth of a degree, because
`C-FB-PITCH` closes the loop on the op-amp's own output there. The ringing is
lower down, in the handover between that path and the DC path through the jack,
where the loop gain is still large — no crossover, so no margin to read.

With the other output's driver on the jack as well — which is what a patch
cable actually connects — its `R-OUT-PROT` damps the ring: about 15 % at 82 nF
and 42 % at 330 nF. The capacitor-only figure is the page's model and the
worse case.

## How it was made to run

The loop is broken by voltage injection (`tools/sim.py`, the stated break's
option (b)): the 1 GH break found no operating point on this stage at all.
`pitch-loop.cir` states why injection is sound here.

## What a result is worth

**A simulated step is a screen, not a spec.** It either agrees with the bench
at E9 — "pitch stability into worst-case cable capacitance" is in the
measurement table — or tells you where to look.
