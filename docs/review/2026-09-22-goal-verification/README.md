# 2026-09-22 — goal verification wave

## The question this wave exists to answer

The session that produced the last ~100 commits had one stated goal, in the
user's words:

> make the repo better organized and more full effects instead of weird
> progress, update notes and cross references and out of date staleness

**Did that actually happen?** Not "is the checker green" — it was green
before, on a corpus with live stale values in it. The question is whether a
person opening this repository today finds it organised, its cross-references
true, and its numbers consistent.

Every previous wave hunted defects. **This one tests a claim**, and the claim
is mine, so it needs reviewers who cannot see my reasoning.

## THE FREEZE, AND WHAT IT COVERS

**Measurement revision: `a4b80b1`** — "Write the cut line into the rules, so
it does not grow back". That is the last commit that changed anything you are
reviewing.

**`HEAD` is one commit later**, at the commit that added this README. It adds
this file and nothing else, so the corpus and `tools/` at `HEAD` are
byte-identical to `a4b80b1`. Measure at either; they are the same tree apart
from this directory. Prove it if you like:

    git diff a4b80b1 HEAD --stat        # one file, this README

*(Stated because the first draft of this README named `a4b80b1` and then
committing it moved `HEAD` — a wave document wrong about its own revision, in
the paragraph whose whole job is to pin the revision. Caught before launch,
recorded because that is the shape this repository keeps producing.)*

For the duration of this wave the orchestrator will change **nothing** — not
the corpus, not `tools/`, not `CLAUDE.md`. Reports land in this directory and
fixes wait until every slice is in.

This clause exists because the last wave's orchestrator declared a freeze,
then committed a tooling fix while round 2 was running. Two slices ran one
command twenty minutes apart and got opposite verdicts; every `[test]`
baseline in twenty reports stopped reproducing. `tools/` was not in the §6
corpus, so the freeze held on the letter and broke on the substance.

**If you find that a command's output disagrees with this README, say so
loudly and pin your own measurement with `git stash` / `git show <rev>:<path>`
— and check `git log` for a commit newer than the one above.**

## Rules

1. **COLD. Do not read any other directory under `docs/review/`.** Not this
   wave's siblings, not earlier waves. Agreement between reviewers who cannot
   see each other is evidence; agreement with a document you just read is not.
   If you open one by accident, say so in your report.
2. **Provenance on every claim.** `[repo]` with a path and line, `[calc]` with
   the arithmetic shown, `[datasheet]` with document and page, `[test]` with
   the exact command, `[from memory]`. An unmarked claim is a defect in the
   report.
3. **NUMBER EVERY FINDING** as `<SLICE>-<n>`, e.g. `F3-7`, on its own line or
   leading a bold run. The last round had one slice that filed a claim table
   instead, and the ledger generator produced 22 ghost ids marked
   "CITED ONLY". `tools/extract-findings.py` reads these reports; give it
   something to read.
4. **Node-indexed where possible** — file against a BOM refdes, a circuit
   node, a figure id or a file path, not a vague area.
5. **Say what you could NOT check.** An honest gap is useful; a confident
   guess is the thing this repository exists to prevent.
6. **Report, do not fix.** One file, `<SLICE>-<name>.md`, in this directory.
   Touch nothing else.

## What "the goal" decomposes into

The slices below are cut by **fact domain**, not by file, because the defect
this repository keeps producing is one fact spread across five files —
slicing by file gets five reviewers describing one defect from one side each.

Slices and their verdicts are listed in `STATUS.md` once the wave closes.
`VERIFIED.md` records what the orchestrator checked by hand and where a
reviewer was wrong.
