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

## D3 — the refutation exemptions, and the worst finding of the wave so far

| Claim | Check | Verdict |
|---|---|---|
| **All 68 forbidden-pattern matches are exempted; the live list is empty** | Ran the checker verbose | **Confirmed.** The `STALE VALUES` section does not print at all. `PASS no live stale values` currently means *nothing fired*, not *nothing matched* |
| `WIRE-LOOM` still says "five connectors must match" against `chain-connectors` = **8**, and `0e68f25`'s own commit message names that row as one of the two escapes it was closing | Read the row; measured the marker distance | **Confirmed, and it is mine.** The pattern `"five connectors must match"` is in the register and it *matches*. The old exemption was an unrelated `rather than` at 24 characters, which that commit dropped — and the new exemption is the dated marker `DECIDED 2026-09-21:` at **222 characters**, a clause I added in the same commit. `J-CHAIN`, two rows away in the same generated file, says "EIGHT of them, not five" |

**I narrowed the vocabulary and added a looser marker in one edit, named this
exact row in the commit message, and the row survived.** Net effect on the
case I claimed to close: zero. The other named case, `FB-IN`, *is* closed —
because it was fixed by editing the text rather than the regex. That contrast
is the lesson.

D3's measurements, which nobody had:

- **47.9 % of the corpus lies within 300 characters of some marker** — that
  much of it is a place where no pattern can ever fire. Concentrated exactly
  where stale values live: every `notes.md` is 85–100 %, BOM fragments 85–93 %.
- **`REFUTATION_SHOUT` is dead weight.** Deleting it changes nothing: 68 → 68.
  It appears in 12 windows and **only 2 are corrections**; the rest are design
  rules like "must NOT share a diode". `DO NOT CUT THE PANEL HOLE` sits 57
  characters from a match in `bom.csv`.
- **The window does not bite at all.** Exempt at w=300 and exempt at
  whole-file are both 68. The data supports **[166, 221]**: the largest
  legitimate distance is 165, the smallest bad one is 222.
- **Three patterns self-exempt and can never fire anywhere**, because they
  contain a marker themselves — `VALUES NOT SET`, `0.2 → 4.8 V`,
  `75 mV → LM317`. One belongs to `sensor-full-scale`. `check_patterns()`
  looks only for newlines and passes all three.
- **Something was lost after all.** The corpus's house style for an ADR
  refutation is "**An earlier revision** …", and `earlier` was dropped: 60
  such openers, **41 with no surviving marker within 300 characters**.

## D17 — the dependency graph

| Claim | Check | Verdict |
|---|---|---|
| The rebuild's numbers are exactly as claimed, and the stated rule is followed without exception | Re-measured | **Confirmed.** 96/48/0/0, 23 ids all matching their directories |
| **Five of 48 edges point at `module/link-supervision`, which is NOT FITTED** | Counted the declaring circuits; read the page | **Confirmed.** Five circuits declare it; the page opens "**NOT FITTED. Nothing in this directory is on the board**", all five of its Interfaces rows begin "Not fitted", and it is the only circuit directory with no `bom.csv`. Its degree is higher than `pitch-stage` or `mod-channels`, which exist |
| The one-source rule is violated by `in-amp output`, and commit `6645fb7` verified that invariant on the DAC's SPI nets only | Grepped both tables | **Confirmed.** `breath-sense-link.md:59` and `breath-receive-stage.md:45` both declare it `out`. I checked the rule where the defect had been reported and did not re-run it generally |

**"Matches the tables" is not "verified", and the header says verified.** The
commit message for `6645fb7` says plainly *"it was seeded from them"*;
`hardware/README.md:12` still says `SEEDED, NOT VERIFIED`. Three wordings,
one graph.

D17 also finds the reciprocity model wrong on its own terms: `Dir` was
present in every row and was discarded when the edges were rebuilt from
`Peer` alone, so every edge is now a 2-cycle and **no topological order
exists** — a bring-up order gets nothing rather than an imperfect answer. And
the three known-false `refdes:` edges are **at least eleven**, two of them
carrying the literal sentence "the part is not here".

Its methodological note is worth keeping: the three `interfaces/**` tables
carry a sixth `End` column, so a fixed column index gives three false
mismatches; and `module/panel` is a substring of `module/panel-led`, so naive
matching invents four edges. Both are traps for the next person who measures
this.
