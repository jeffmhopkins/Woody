# Breath receive stage — simulation

**Nothing here has been run.** This directory holds the deck and the procedure.
It holds no results, and it will not hold any until a run produces them.

That is the rule, not an apology: `docs/reference/pcb-pipeline.md` names five
simulations worth running and records that **none has been**. A plausible
number written here would sit next to figures read off banked datasheets and
be indistinguishable from them. `datasheets/README.md` is explicit that a
fabricated document is worse than an honest gap; a fabricated simulation
result is the same thing with fewer bytes.

## The sim this circuit needs, and why it is not optional

**Breath-link CMRR with the INA828.** `pcb-pipeline.md` ranks it **first of
five**, ahead of the reference-buffer stability work, on one argument: the
margin is thin and the parts that set it cannot be changed afterwards.

`hardware/interfaces/breath-sense-link/breath-sense-link.md` puts the link at **60.2 dB** `[calc, A2]` against
an independently derived requirement of **58.5 dB** — **1.7 dB**, resting on
two parts' tolerance. Both of those parts, `R1` and `R1b`, are instrument-side,
in the bonded body, and `bom.csv` marks them unretrofittable. So this is not a
number that gets checked at E9 and adjusted: if it is wrong, it is wrong in a
body that does not open.

**And the corpus does not agree with itself about the size of the term.** The
page's `### `R1` is a 1206, and it has a twin` argues that the unmatched case
spends the entire budget and that `R1b` buys "fifty times" the rejection;
the carrier-side text replies that with `R1b` fitted the floor is **73 dB**,
set by the bias pair, so `R1b` buys about **13 dB**. Both agree the part must
be fitted.

*(Both halves of that disagreement now sit in the SAME file — the
consolidation moved them together without resolving them, which is what a
content freeze requires. They are still an order of magnitude apart about
what `R1b` buys, and this deck is what settles it. Until 2026-09-21 this
section credited `carrier.md` with all three figures; that page derives none
of them any more, and nothing could see it: the path still resolved, and
this file was written during the restructure so it was never a conservation
source.)*
They disagree by roughly an order of magnitude about what it is worth, which is
exactly the kind of disagreement a model settles and a reading does not.

**Three terms have to appear in the same deck**, because the claim is about
their sum and each is currently argued on its own page:

| Term | Where it is argued | What the deck must vary |
|---|---|---|
| Source-impedance balance on the twisted pair | `carrier.md`, the `R1`/`R1b` pair | `R1b` fitted and omitted, and both at their stated tolerance |
| The bias pair against the series legs | this page, `R4`/`R5` | The bias resistors' tolerance, which sets the floor `carrier.md` quotes |
| Common-mode capacitor mismatch | this page, `### Why C_diff is ten times C_cm` | `C_cm` at **±1 %** and at **±5 %** — the page puts the ±5 % case near **46 dB**, i.e. below the requirement on its own, and that is the reason the ±1 % spec exists |

Two things the deck must get right or it is measuring something else:

- **`AGND` is a signal leg here, not a ground.** It arrives from the
  instrument's analog star through `R1b` and drives `IN+` through `R2`. A deck
  that ties it to the module's `AGND` node has deleted the common-mode
  excitation it was built to apply.
- **`REF` is driven from a buffer, and its source impedance is part of the
  answer.** `bom.csv` carries TI's number verbatim from SBOS792A §8.1 — keep
  the source impedance at the `REF` terminal below **5 Ω** — because `R_REF`
  sits in series with one of the internal 40 kΩ difference-amp resistors and
  unbalances the bridge. Model the buffer, not an ideal source, or the deck
  cannot see the failure the buffer was added to prevent.

## Running it

| | |
|---|---|
| Simulator | `ngspice` 42, stock Ubuntu archive, no allowlist change needed |
| **Do not use** | PySpice 1.5 — it treats every non-`Warning:` stderr line as fatal and ngspice prints a solver banner to stderr on every run. Raw netlists plus `subprocess` |
| Model | TI's INA828 macromodel. `pcb-pipeline.md` records that one exists, in the same directory as the OPA2197 macromodel whose URL is in the `BLOCKED` row of `datasheets/MANIFEST.csv`. **Bank it in `datasheets/` with a SHA-256 first**, like every other document |
| `.spiceinit` | needs `set ngbehavior=psa` — **inside `.control` is too late** |
| Sweep | AC, common-mode drive on both legs together, differential output referred to the input. The band that matters is the mains harmonics and the SPI hash, not DC |
| Spread | The claim is a **worst case over tolerance**, not a typical. A nominal run that clears 58.5 dB answers nothing — the parts' tolerance is the whole of the 1.7 dB |

## What a result is worth when it arrives

**A simulated CMRR is a screen, not a spec.** It is a ratio of two large
numbers and it is sensitive to exactly the parasitics a macromodel does not
carry — the pour asymmetry `pcb-pipeline.md` calls out for the `BREATH`/`AGND`
keepout window is not in any netlist. A number from here either agrees with the
bench at E9 or it tells you where to look.

What it *can* settle without a bench is the ranking: which of the three terms
dominates, and whether `R1b` is worth 13 dB or fifty times. That decides
whether the ±1 % `C_cm` spec is load-bearing or belt-and-braces, and it has to
be decided before the instrument-side parts are soldered into a body that does
not reopen.

Results land in `config/figures.yaml` with their provenance marked — not in
this file, and not in the page.
