# Fix-audit wave — the verdict

**Closed 2026-09-22.** Twenty cold slices, twenty reports, every one of them
hand-verified against the corpus and recorded in `VERIFIED.md`.

## Recommendation: do not merge yet. Fix the instrument first.

The restructure's **content** is still sound, and this wave strengthened that
rather than weakening it. What is not sound is the **instrument** that
certifies it, and one day of fixes made it worse in the one place that matters
most.

## Ten for ten

Nine waves had found the previous round's fixes partial. **The tenth is
partial too.** D20 filed nineteen defects and the shape is the finding:

> All four tools are green at HEAD, and **every one of the nineteen is
> invisible to all four.** Not one is a wrong value at the site of an edit.
> **Fifteen of nineteen are on a page that cites the page that was fixed.**

## The four that block a merge

**1. The checker's verdict is not reproducible.** `check_owners` picks its
token with `sorted(set(...), key=len)`, so ties break on set iteration order.
Measured across eight hash seeds, the token it tests `loop-budget` against:
`196 241 196 241 250 241 250 196`. D1 took it end to end with a real rule-1
violation live: **6 PASS / 4 FAIL over ten identical runs.** Not always-green
— green often enough that a re-run clears a surprising FAIL. Every PASS quoted
in the last two days was a sample from a distribution nobody knew existed.

**2. The stale-value half of the checker reports nothing on this corpus.** All
**68** forbidden-pattern matches are exempted; the live list is empty. The
refutation vocabulary was narrowed and four new markers added in the same
commit — a bare ISO date, a bare `->`, a bare `→`, a case-sensitive `NOT` —
and they are ordinary prose. Demonstrated by injection, byte-identical but for
one token:

| injected text | verdict |
|---|---|
| `Bench session 2026-08-14 covered the jack layout` | **PASS** |
| `Bench session covered the jack layout` | **FAIL** |

The exempt region grew from **33.9 % to 48.4 %** of corpus characters — D3 and
D5 measured that independently. And `WIRE-LOOM`, the row the commit message
names as one of the two escapes it was closing, **is still live**, now
exempted by the date that same commit added, 222 characters away.

**3. `check_bom_figures` — the flagship fix — reaches 1 figure of 37.** It
reads `fig["value"]` only; eighteen figures name a real BOM refdes elsewhere
in their entry, in fields it never opens. The failure it exists to prevent
reproduces on the next part anyone tries: `C-GATE-LOADSW` 82 nF → 100 nF by
the documented procedure gives `0 problems` and `PASS`, byte-identical to
baseline.

**4. Some fixes are wrong, not merely incomplete.**

| Fix | What the audit found |
|---|---|
| ADR 0004's DAC threshold | The corrected number **refutes the conclusion stated beside it**. 0.625 × 5.21 = 3.2563 V; 3.3 V CMOS clears it by 44 mV |
| The plate-to-PCB reversal | Right in direction, **wrong in magnitude**. The 3.2–3.6 mm premise is impossible at its upper end (pin protrusion −0.10 mm), and ADR 0002 already held the right answer — 2.50 − 1.20 = **1.30 mm** — in the same batch |
| The ADR 0014 lighting annotation | Uses **arithmetic that was never done** as its evidence: 2.1 mA × 50 = 105 mA, not the 123 mA claimed "exactly". And the correction **inverts the clamp** it was defending — realistic use is 3.60 W against a ~3 W clamp |
| The `D-CLAMP-BREATH` drawing edit | **Labelled the wrong part**, then recorded the wrong claim in the BOM note — and **corrupted the drawing**, pushing one line's rails from column 68/70 to 85/87 |
| `rewrite-paths.py --invert` | **No longer a valid proof.** 112 MISMATCH on a healthy tree, because the path map grew `created` rows and `invert_targets()` never reads `kind` |

## What the wave confirmed as sound

Stated plainly, because it is most of the tree:

- **Conservation.** Zero distinct numeric tokens left the corpus. All 18
  relocated BOM rows landed. No register entry or field removed, no file
  deleted or renamed, the history rule held.
- **BOM mechanics**, proved byte-exact **twice, independently** — 131,725
  bytes, 139 rows, 140 CRLF, exact headers, no duplicate refdes — by two
  slices' own concatenators rather than by `merge-bom.py --check`.
- **Datasheet provenance**: 11 figures checked against their cited documents,
  **10 fully confirmed**, including 51 `LT1641` hits and zero `LT4256`, which
  clears the mislabelled-mirror trap.
- **141 corpus datasheet citations, 0 dangling.** 76 manifest rows against 76
  files, both ways.
- **The path map resolves.** 429 distinct path tokens across the review and
  log records, 6,027 occurrences, **91.4 % resolving with no effort, 96.1 %
  resolving** — the measurement nobody had made.
- **23 defect classes still caught after the rebuild, and 9 newly caught.**
  Latin-1 under `hardware/**` used to traceback and now reports.
- **The order code, the two new figures' values, and both datasheet claims**
  behind the lighting and breath corrections all verified against the banked
  documents.

## The one-line diagnosis

D15 put it best, about its own file, and it generalises to the whole batch:

> The fix was correct arithmetic in one file, and the register was not
> extended to hold any of it in place.

Across twenty slices the pattern holds. **Each fix was verified against the
one case that motivated it. Almost none was verified for reach.** `unplaced.csv`
is the cleanest example: it is defined as the rows no page *names*, sixteen
rows were moved out on the grounds the parts were *drawn*, and **14 of 18 are
named by zero pages.** `pcb-pipeline.md` states the three tests — drawn, named,
placed — and all three were applied to exactly one row.

## Fix order

1. **`check_owners`: the nondeterminism and the exclusive `or`.** Two
   one-line edits. Until the first is fixed, no run of this tool means
   anything precise, so everything below is unverifiable.
2. **The refutation exemption.** Drop the date, the arrows and the shouted
   `NOT`; restore `an earlier revision` as a bigram; decide whether a
   `|`-appended dated segment in a BOM notes cell is a refutation convention,
   and if it is, write it down so the checker can encode it.
3. **The three patterns that can never fire** because they contain a marker,
   and the `#fragment` links that are entirely unchecked.
4. **Re-run every mechanical claim in the fix batch** against the repaired
   tooling. Nothing in this wave's `VERIFIED.md` was measured with a
   deterministic checker.
5. **Then the corpus findings**, and this time grep for reach before claiming
   a fix landed.

## What this wave cost, and whether it was worth it

Twenty agents, and the answer to the question it was opened to settle is *no*.
That is the wave working. The alternative was merging a tree whose green light
flips on a hash seed, with a flagship check covering one figure in
thirty-seven, on the strength of a proof that had already stopped proving
anything.

**Round 2 — a cold review of this wave — is still owed** and is not optional
by this project's own rules. Two things already happened that a round 2 exists
to produce: D10 **reversed** a sibling's claim (the `360 mA` "staleness" is a
rounding the register never held otherwise, and a pattern there would have
broken a correct sentence), and D12 and D20 **independently** found the same
silent duplicate YAML key. Agreement between agents that cannot see each other
is evidence; that is the method earning itself twice in one day.
