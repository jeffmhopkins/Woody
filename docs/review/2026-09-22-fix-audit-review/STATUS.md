# Round 2 — what landed

Four cold slices reviewed the twenty-slice fix-audit wave. This file is the
counterpart to `VERIFIED.md`: that one records what was checked, this one
records what actually changed in the corpus, and what did not.

The convention exists because a wave with thirteen reports and four landed
slices looks finished from the outside and is not.

## Closed, by id

| id | what it was | where it landed |
|---|---|---|
| D3-1 / D3-2 (`WIRE-LOOM`) | "five connectors must match" live against a tracked 8, exempted by a date 222 characters away | `e62114a` — cites `chain-connectors`, and states why it is not one per board |
| D3-3 (`C-TIMER-LOADSW`) | two register-forbidden sentences un-struck; **nothing in the cell ever retired the 62 ms** | `e62114a` — the opening now retires the 150 ms target, its 62 ms justification, the I_TIMER dispute and the "12x to 300x" ratio |
| E2-7 (`panel-toggle-hole`) | pattern fires on a sentence that is **true** and that the cell endorses 1,800 characters later | `e62114a` — pattern withdrawn with a `false_positive_note`; D3 E27/E63 graded it ok and was overruled without citation |
| E1 (no id scheme) — `STATUS.md` §2 | "D3 and D5 measured that independently" is false; the checker's own comment escalated it to "three cold slices" | `e62114a` — comment corrected, E1's vocabulary/window decomposition recorded with it |
| E3 / D10-1d (`U-LOADSW`) | three parts in one row; `+ sense R` double-counted `R-ILIM` | `ad2c173` — `Q-LOADSW` split out with its decider named; retired alternatives and the pre-foldback sizing struck **in the cell that states them** |
| E3 / D10-1c (`D-RESP`) | part and package cannot both be ordered | `ad2c173` — confirmed verbatim against the banked `1N4148.pdf` |
| E3 / D10-1b (`D-USBOR`) | two alternatives, one footprint | `ad2c173` — confirmed against `SS14.pdf` and `1N5817.pdf`; decider named, `candidate` -> `open` |
| E2-1 | "five rows" is **seven**, byte-identical in 23 files | `4c0b747` — all seven enumerated, and the one correctly excluded named |
| E2-2 | "27 of 49" reproducible from no committed state | `4c0b747` — withdrawn, not corrected |
| E2-9 | stale figures in `tools/`, which no check can reach | `4c0b747` — numbers removed rather than corrected; `D4` disambiguated |
| E2-10 | `halved` exits 1 on exactly the deduplication rule 1 prescribes | `4c0b747` — reported, no longer fails the run |
| E2-8 | the hook runs on every `Bash` call and never blocks a commit | `2a3ef3f` — `CLAUDE.md` §2 corrected. **`.claude/settings.json` deliberately not changed** |
| E2-12 | `firmware/README.md` never reached by the `ks33-contact-bounce` figure | `2a3ef3f` — cites the figure, keeps M1, states what M1 now adds |

## Closed as "no corpus change needed", with the check that says so

| id | why |
|---|---|
| E2-13 | The 78-rows-over-76-files flattening is only in `docs/review/`, which is history. `verify-datasheets.py` at HEAD: **78 verified, 23 blocked, 0 problems**. D11 had it right; nothing live restates it |
| E3 on blocker 4 | All five rows are in `STATUS.md` of an earlier wave. History is not corrected. The severity lesson is taken, in `VERIFIED.md` |

## Open, and named rather than quietly dropped

- **E2-3.** The `## Interfaces` rewrite deleted every table's inline links.
  `check_links` proves that links which *exist* resolve — **a link that was
  removed is not a broken link**. The batch's own fail-open shape, on the
  navigation layer. Needs a check that compares link counts across a
  restructure, which is a tool to write, not a line to fix.
- **The 68-line header, still replicated 23 times.** Correcting its facts
  does not make it one statement. Stating it once and citing it is the rule-1
  fix and it is a restructure; it is not going in beside a merge.
- **E2-11.** 9,389 words of commit message across 27 commits, larger than any
  reference document in the tree and sampled by one slice. Four of five
  checkable claims confirmed. An unmeasured area, not a bad one.
- **E2-6.** This round's own `README.md` hands every slice two premises that
  are false at HEAD ("6 PASS / 4 FAIL", "the live list is empty"), because
  the freeze broke under it. The README is the wave's record and keeps its
  words; **this line is the correction**, and the general fix is the clause
  now in `CLAUDE.md`: name the revision a wave measures against, and pin
  `tools/` or say you are not.
- **`FINDINGS.csv`, 110 rows, 6 closed by id.** The ledger's own defect,
  visible in it: E1 uses a claim table rather than numbered findings, so the
  extractor produced 22 `E1-n` ghosts marked "CITED ONLY". A ledger needs the
  reports to carry ids; this one did not ask them to.

## What round 2 changed about round 1's verdict

Round 1 blocked the merge on three instrument defects. They were real and
they are fixed. Round 2's finding is that **it was the wrong list**: the
findings that survive contact with a human — you cannot order this BOM —
were all in one slice and were promoted by nobody. Both lists are now closed.
