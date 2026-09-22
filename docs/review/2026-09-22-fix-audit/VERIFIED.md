# Verified by hand — fix-audit wave

A finding is a claim. This file records what was checked against the corpus
and where an agent was right or wrong. Checked as reports land.

## D16 — the net renames

| Claim | Check | Verdict |
|---|---|---|
| The reconciliation promise is mostly unkept: `hardware/README.md`, `pcb-pipeline.md` and `breath-sense-link.md` all state that **every** qualified row names the drawing's own spelling; **7 of 29 do**, and 3 of those 7 are cleanly correct | Spot-checked the two named as outright wrong | **Confirmed on both.** |
| `pitch-stage.md:26` says `AGND_MOD` is "drawn `AGND`", and that page's drawing contains no `AGND` | `grep -c AGND` on the file | **Confirmed. Two hits, and neither is in a drawing** — one is that row itself, one is prose at `:201`. The reconciliation instruction points at a spelling that is not there |
| `breath-output-stage.md:23` still instructs the reader that the drawing "restates the figure's value in the label" — **after** `79f5c4a` removed that label | Read the row and grepped the page for `5.21` | **Confirmed.** The label is gone; the row still describes it. `5.21 V` does survive at `:126` and `:129`, but in a table and in prose, not the label the row names |

The third one is the finding. **It is this project's named failure mode,
occurring inside the commit that was fixing that failure mode, in the one row
whose entire content is a reconciliation instruction.** I removed a drawing
label and did not update the row that exists to describe it.

And the first one indicts the decision, not just the execution. Leaving the
drawings alone was defensible *only because* every qualified row was supposed
to name the drawing's spelling. 22 of 29 do not, so the mitigation that
justified the decision is largely absent. D16's recommendation — relabel the
drawings, ~25–30 genuine net tokens across 9 files, verifiable in one grep —
is the right call, and `79f5c4a` already did exactly that for
`digital-and-supervision.md` and left three identical cases.

## D18 — the path map

| Claim | Check | Verdict |
|---|---|---|
| **The map's content is sound** — old side an exact bijection onto `81c081d`, all 22 datasheet corrections right, WS2815 SHAs confirmed | Re-measured the shape | **Confirmed.** 410 rows, and the corrections hold |
| `repo-maintenance.md` §7's unhedged "every tracked file has a row" is **already false at HEAD** | `git ls-files` against the map | **Confirmed. Exactly one orphan: `docs/review/2026-09-22-fix-audit/README.md`** |
| §7's "410 rows: 405 tracked files, plus 4 `deleted` and 1 duplicate destination" | Counted | **Confirmed wrong, in both parts.** 406 non-deleted rows, **406 distinct destinations, zero duplicates**, 4 deleted. 405+4+1 sums to 410, which is why it reads correct |
| Nothing runs the four-line check §7 tells a maintainer to run | Grepped the tools and the hook | **Confirmed.** The one artefact with a written, tested invariant is the only one not wired to the commit hook |

**The orphan is the commit that opened this wave.** The map was whole for
exactly two commits and broke on the next one — which was me writing the
README for the audit that then found it. A census that must be hand-maintained
goes stale on the first commit after it is written, and this is the proof.

D18's structural point is the one worth keeping: the map does **two** jobs.
Resolving a path quoted in a dated record needs only the 287 old-side rows
plus the moves and deletes, its domain is an immutable tree, and it *cannot*
go stale. The 123 `created`/`created-history` rows — 30 % of the file — exist
only to satisfy a census, answer no question a reader of a pre-restructure
record can ask, and are the half that breaks on every commit.

Its measurement is the thing nobody had done: **429 distinct path tokens in
the review and log records, 6,027 occurrences, 91.4 % resolving with no
effort and 96.1 % resolving at all.** That is the only number that says
whether the mechanism works.
