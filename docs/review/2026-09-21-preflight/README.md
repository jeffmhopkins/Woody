# Preflight — verify every value before SPICE and before transcription

**2026-09-21.** The fourth review wave on the design, and the first one that
can check its own claims against documents.

## Why this wave is different

The three previous waves were argument against argument. Every vendor site was
blocked, so load-bearing numbers carry `[from memory]` or `[calc]` and the best
available check was a second reader doing the algebra again.

**That has changed. `datasheets/` now holds 75 verified documents.** So the
standing instruction for this wave is:

> Every `[from memory]`, `[web]` and `[calc]` claim in your slice is now
> checkable. Check it. A claim confirmed against a banked document gets
> re-marked `[datasheet <doc> p.N]`. A claim that **contradicts** one is the
> most valuable thing you can file.

## What this wave is for

Two concrete deliverables are about to consume these numbers:

1. **SPICE verification** — garbage values in, confident garbage out.
2. **A SKiDL transcription** of every page into executable Python, from which
   the netlist and the board are generated.

So findings must be **actionable values and topology**, not just observations.

## Emphases the owner asked for

- **Impedance** at every boundary — source and load, loading error, what each
  stage presents to the next and whether the stage before it can drive that.
- **Current draw** — per part, per rail, against the budget and against the
  Eurorack clamp limits.

## Method

- **Cold.** No reviewer reads `docs/review/**`, including this file's siblings.
  Agreement between agents that cannot see each other is evidence.
- **Slice by section**, one per schematic page, plus four cross-cutting slices
  for the things a per-page decomposition structurally cannot catch.
- **Provenance on every claim:** `[datasheet <doc> p.N]`, `[repo file:line]`,
  `[calc]` with arithmetic shown, `[from memory]`. Unmarked is a defect.
- **Answer the open questions**, do not just re-find defects. Each brief
  carries its section's live `Still open` items and the `config/figures.yaml`
  entries that touch it.
- **Propose values.** Where a decision belongs to the owner, say so and give a
  recommendation rather than a menu.

`VERIFIED.md` records what was re-checked by hand and where an agent was wrong.
