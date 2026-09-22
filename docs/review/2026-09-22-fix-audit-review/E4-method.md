# E4 — the review method, and whether ten waves are converging

**Slice:** the fix-audit wave audited against the five properties `CLAUDE.md`
names, and the question of whether this project's review waves are converging
or spinning.

**Method:** read `docs/review/2026-09-22-fix-audit/**` in full (README, twenty
reports, `VERIFIED.md`, `STATUS.md`), plus `CLAUDE.md`, the git log, and
per-wave diffstats. Measurements over the twenty reports were scripted and the
scripts are described inline so they can be re-run. **Cold:** nothing under
`docs/review/2026-09-22-fix-audit-review/` other than this wave's `README.md`,
and nothing from any earlier wave — one incidental exception, recorded in §8.

**Provenance:** `[repo] path:line`, `[test]` a command and its real output,
`[calc]` with the arithmetic shown, `[git]` a revision.

---

## 0. The headline, and one thing that happened while I was measuring

**The method largely held, and the wave was worth its cost. The apparatus
around the method did not hold: 198 numbered findings exist in the twenty
reports and `VERIFIED.md` and `STATUS.md` cite exactly zero of them by
identifier.** There is no closeable ledger. That single gap explains more of
"every wave finds the last round's fixes partial" than any failure of
reviewer care does.

And while this slice was running, the thing being audited moved.

`[git]` `0576a95` opened round 2 at **03:01:39**. At **03:05:52** I found
`tools/check-staleness.py` modified in the working tree; at **03:07:25**
`566159e` "Fix the instrument: the verdict is reproducible again" landed fix-order
items 1–3 from `STATUS.md`.

`[test]` ten consecutive runs at `566159e`, tree otherwise clean:

```
FAIL 0 shape + 0 owners + 0 links + 0 sections + 0 deps + 0 generated
   + 0 register-vs-bom + 0 datasheets + 0 dead-patterns + 0 unwired
   + 8 stale + 0 bom | corpus 123 files, 23 circuits, 37 figures / 218 patterns
```

— ten identical lines. `[test]` `PYTHONHASHSEED` 0 through 7, eight runs: eight
identical lines. **The instrument is deterministic now, and it reports eight
live stale values where the entire fix-audit wave measured `PASS`.**

Three consequences, all of them method findings rather than tooling findings:

1. **The fix-audit's two headline claims are confirmed by construction.** The
   repair of `check_owners` produced determinism; the withdrawal of the four
   prose markers produced a non-empty live list. `[test]` the eight are
   `chain-connectors` ×1, `loadswitch-timer` ×2 and `panel-toggle-hole` ×1,
   each doubled through `hardware/bom.csv` and its fragment — and one of them
   is `WIRE-LOOM`'s `five connectors must match`, the row D3 identified as
   still live. A wave that predicts what a repair will reveal, and is right, is
   not spinning.
2. **Every `[test]` baseline in the twenty reports has stopped reproducing.**
   Each of D1, D2, D3 and D20 opens by quoting `PASS no live stale values |
   corpus 123 files …`. At HEAD that command prints `FAIL … 8 stale`. The
   reports are still right about the tree they measured; they are no longer
   re-runnable against HEAD without `git archive 092b364`, and none of them
   says so because none of them could have known.
3. **Round 2's "the corpus is frozen" was honoured on the letter and broken on
   the substance.** `tools/**` is not in `CLAUDE.md` §6's corpus list, so
   `566159e` is not literally a freeze violation. But round 2's README tells
   every slice *"where a report leans on a tool run, re-run it yourself,
   several times, and say so"* — and the tool changed six minutes into the
   round. Two round-2 slices running the same command twenty minutes apart get
   opposite verdicts for reasons that have nothing to do with the corpus.

**Recommendation to the orchestrator: freeze `tools/` for the duration of a
round that audits tooling claims, or state the pinned revision in the round's
README.** One line — *"measure against `092b364`; `tools/` may move"* — would
have cost nothing and removed the ambiguity entirely.

---

## 1. Did the cold rule hold?

### 1a. Declarations

Fifteen of twenty reports declare their cold status explicitly, most in the
first ten lines. `[repo]` D11:6, D12:5, D13:7, D14:4, D15:3, D16:5, D17:14,
D20:18, D5:509, D6:6-7, D9:5, D8:13, D10:735, D19 (method block), D18 (implied
by its subject statement).

**Five do not declare it at all: D1, D2, D3, D4, D7.** All five are tooling or
register slices, and all five instead declare something adjacent and stronger —
that nothing in the corpus was modified, and that every test ran in a scratch
tree. `[repo]` D1:11 *"Nothing in the corpus was modified. `git status` shows
this file only"*; D3:10; D7:7-9. The omission is uniform across exactly the
slices whose subject is code, which reads as a template difference rather than
five independent lapses. It is a defect by the wave's own rule — an
undeclared cold status is unfalsifiable — but a low-severity one.

### 1b. Accidental contamination: none detected

`[test]` I tokenised all twenty reports with code fences stripped, built the
set of 8-word shingles for each, and intersected all 190 pairs. The largest
overlaps are:

| shingles | pair | what the shared text is |
|---|---|---|
| 97 | D11 / D13 | `figures.yaml` note text, quoted verbatim by both |
| 96 | D14 / D15 | the checker's own `PASS` line, and a `figures.yaml` note |
| 86 | D10 / D9 | `merge-bom.py`'s docstring rule, quoted by both |
| 48 | D1 / D3 | `CLAUDE.md` §2 — *"is worse than no pattern, because its cheapest fix is to make the sentence wrong"* |

**Every high-overlap pair is co-quotation of a corpus source, not of each
other.** I found no passage in any report that could only have come from a
sibling report. D1:388 refers to *"this very wave (D16/D17)"* by slice number
and topic — that is in the wave README's slice roster `[repo]` README:63-77, so
it is brief-derived, not contamination.

Two further signals that the slices really were blind to each other, and both
are the good kind:

- **D1 and D2 found the same defect with different denominators.** `[repo]`
  D1:202 titles it *"examines 1 figure of 32"*; `[repo]` D2:20 says *"reaches
  one figure out of thirty-seven"*. `[test]` `grep -cE '^\s*-?\s*id:'
  config/figures.yaml` → **37**. Two agents who could see each other would have
  agreed on the denominator. Two who could not, did not — and the agreement on
  the numerator is therefore worth something. `STATUS.md` silently adopted 37
  and never mentions that two slices counted.
- **D3 and D5 measured the exemption surface independently and got different
  numbers.** `[repo]` D3:548 — **47.9 %** at the shipped window; `[repo]`
  D5:123-127 — **48.4 %**, and the only measurement of the *before* state
  (33.9 %). `STATUS.md:47` presents this as *"D3 and D5 measured that
  independently"* against the pair `33.9 % → 48.4 %`. That is a fair claim about
  the endpoint and an overstatement about the delta: only D5 measured 33.9, and
  the two endpoint figures differ by half a point because the methods differ.
  The convergence is real and the synthesis rounded it into something tidier
  than it was.

### 1c. Deliberate contamination: worth it, and the evidence says so plainly

Roughly twelve claims were passed between slices in the briefs as *"sibling
claims"*. `[repo]` D10 Part 2, D11:649, D12:535, D13:203 and :509, D14:478,
D15:429, D3:337, D7:72. Outcomes:

| outcome | count | examples |
|---|---|---|
| Confirmed, at the line named | 6 | D12-9 `0004:506-510`; D14-9 `ROADMAP.md:71` |
| Confirmed **and widened** by the receiving slice | 3 | D13:203 *"CONFIRMED and is wider than stated"*; D10 Claim B — *"worse than the claim … the whole block is stale, on six numbers"* |
| **Refuted** | 1 | D10 Claim A: `360 mA` occurrences confirmed, staleness refuted |
| The **brief itself** shown wrong | 1 | D7-12 — the fourth pattern removal the brief describes does not exist in git |
| Corpus instance found for a brief's *hypothetical* | 1 | D3:337 — `DO NOT CUT THE PANEL HOLE`, 57 characters from a match |

**This was worth it, and D10 Claim A is the proof.** `[repo]` D10:603-640: the
claim was *"`360 mA` appears in 6 corpus files against a register that says
`359 mA`"*. D10 confirmed every occurrence, then `[test]` checked the register's
own history — the value was `"359 mA"` in all twenty recorded versions of
`config/figures.yaml`, so nothing ever moved — then `[calc]` walked the
arithmetic at `umbilical-load-switch.md:222` and showed the conclusion holds at
either value. Its recommendation is a `false_positive_note`, not a pattern.
That is `CLAUDE.md` §2's trap being caught **before** a forbidden pattern was
written that would have made a correct page wrong. A cold agent with no claim
to check would not have looked at that number at all.

The cost is real but small: a passed claim is a prior, and confirmation is
cheaper than refutation. The mitigation the wave used, and should keep, is
visible in every confirmation — D12, D13, D14 and D15 all re-derived the claim
from `[repo]`/`[calc]`/`[test]` rather than repeating it. **One refutation and
one brief-was-wrong out of twelve is a healthy rate; if a future wave passes
twelve claims and confirms twelve, that is the number to worry about.**

---

## 2. Was provenance actually marked?

### 2a. The counts

`[test]` markers per report, code fences included:

| report | lines | `[repo]` | `[calc]` | `[test]` | `[datasheet]` | `[git]` | `[from memory]` | markers / 100 lines |
|---|---|---|---|---|---|---|---|---|
| D20 | 194 | 67 | 37 | 12 | 2 | 0 | 1 | **61.3** |
| D15 | 497 | 100 | 34 | 14 | 4 | 0 | 2 | **31.0** |
| D14 | 568 | 59 | 11 | 9 | 13 | 0 | 7 | 17.4 |
| D9 | 512 | 55 | 5 | 14 | 0 | 12 | 0 | 16.8 |
| D13 | 721 | 61 | 39 | 11 | 0 | 0 | 4 | 16.0 |
| D6 | 449 | 51 | 4 | 12 | 2 | 0 | 0 | 15.4 |
| D11 | 710 | 38 | 29 | 18 | 18 | 0 | 4 | 15.1 |
| D8 | 638 | 35 | 12 | 23 | 8 | 11 | 0 | 13.9 |
| D4 | 783 | 52 | 5 | 47 | 0 | 4 | 0 | 13.8 |
| D18 | 528 | 21 | 2 | 38 | 0 | 6 | 0 | 12.7 |
| D12 | 665 | 35 | 12 | 15 | 13 | 0 | 3 | 11.7 |
| D10 | 744 | 59 | 10 | 8 | 5 | 0 | 0 | 11.0 |
| D16 | 656 | 42 | 1 | 27 | 0 | 0 | 0 | 10.7 |
| D19 | 497 | 12 | 0 | 41 | 0 | 0 | 0 | 10.7 |
| D17 | 635 | 35 | 1 | 23 | 0 | 0 | 0 | 9.3 |
| D2 | 515 | 15 | 5 | 28 | 0 | 0 | 0 | 9.3 |
| D3 | 621 | 17 | 1 | 37 | 0 | 0 | 0 | 8.9 |
| D7 | 672 | 35 | 5 | 15 | 0 | 4 | 0 | 8.8 |
| D5 | 509 | 10 | 4 | 30 | 0 | 0 | 0 | 8.6 |
| D1 | 748 | 28 | 9 | 25 | 0 | 0 | 0 | 8.3 |

**Every report marks. Not one is bare assertion.** Density is a bad ranking,
though, and I want to say so before it gets quoted: D1 and D5 sit at the bottom
of this table and are two of the most rigorous reports in the wave, because a
tooling slice binds twenty claims to one fenced `[test]` transcript where a
content slice needs twenty `[repo]` citations. `[repo]` D5:250-292 is a
**46-row before/after table** of defect classes against the old and new tool,
every cell an observed verdict, carried by a single method block. That is more
evidence per claim than any `[repo] path:line`, and the marker count does not
see it.

### 2b. Where markers are genuinely missing

`[test]` I split each report outside code fences into paragraphs, kept those
containing a bolded numeric claim, and counted those with no marker anywhere in
the paragraph. The raw rates run 11 % (D15) to 64 % (D5). **I then read a sample
of the flagged paragraphs and the metric is mostly wrong**: the unmarked
paragraphs are overwhelmingly headlines and section summaries that restate a
claim proved with markers elsewhere in the same report. `[repo]` D2:20
*"`check_bom_figures()` reaches one figure out of thirty-seven"* is unmarked in
the headline and fully evidenced at D2:498.

So the honest finding is narrower and worse than the raw number:

**Every report's headline is unmarked, and `STATUS.md` is built out of
headlines.** The wave's own worst finding is exactly this failure mode one level
down: `[repo]` `VERIFIED.md`:682 records that ADR 0014 used *"arithmetic I did
not do as evidence"* — `2.1 × 50 = 105`, published as 123 *"exactly"*. A
headline that carries no pointer to its evidence is the same shape of artefact.
`STATUS.md`'s *"23 defect classes still caught after the rebuild, and 9 newly
caught"* is a case in point: the 9 is D5's own sentence `[repo]` D5:294, and the
23 is a **row count of D5's table that no report states** — `[test]` counting
that table gives exactly 23, so the synthesis is correct, and a reader has no
way to know where it came from.

### 2c. Rigorous versus asserting

- **Most rigorous:** **D20** (61 markers per 100 lines, every one of its 21
  findings re-derived at HEAD rather than at the commit that made it, and its
  method paragraph states the spellings it grepped — spaced, unspaced, hyphen,
  en dash, CSV, drawing); **D15** (31 per 100, and the only report that
  routinely cites `git log -L` to date a defect to a commit); **D5** and **D1**
  on the evidence-per-claim measure rather than the density measure.
- **Most honest about its own weakness:** **D14**, with seven `[from memory]`
  markers — the highest in the wave — on mechanical dimensions, alongside
  thirteen `[datasheet]` citations. D14 was also the report `VERIFIED.md`:730
  records as *"right in direction, wrong in magnitude"*; the marking is why that
  was checkable.
- **Weakest marking, relative to what it claims:** **D17**. 34 paragraphs with
  bolded numeric claims, **one `[calc]` marker in 635 lines**, and a finding set
  built on edge counts and directions (*"10 of 96 directed edges"*,
  `[repo]` D17:620). Edge arithmetic is arithmetic. **D16** is adjacent — one
  `[calc]`, and its flagship *"7 of 29 do"* `[repo]` D16:22 is a count presented
  without the enumeration, though `VERIFIED.md`:10 spot-checked and confirmed it.
- **D19** carries zero `[calc]` markers across four numeric conservation proofs.
  Its `[test]` scripts are described inline, which covers it, but a conservation
  proof whose arithmetic is never shown as arithmetic is one transcription error
  from asserting the opposite of the truth.

---

## 3. Were findings node-indexed, and did the collisions happen?

### 3a. The index axis fragmented, and mostly for good reasons

`[test]` finding-table headers across the wave:

| axis | slices |
|---|---|
| node / refdes / figure id | D13 (*"Findings, node-indexed"*), D15 (`Node / figure`), D9 (per-refdes), D6 (per-figure), D3 (`file:line` + figure) |
| code symbol (tool + function) | D1 (F1–F13), D2, D4 (`# / Tool / Finding`), D5 (R1–R6) |
| graph edge | D17 (`# / Edge / Rows at end A / Rows at end B`) |
| prose, numbered only | D11, D16, D7, D8, D18 |
| section hierarchy, no ID | D10, D19, D20 |

**The rule as written — "filed against a circuit node or BOM reference" — does
not fit half this wave**, because half this wave's subject is a Python file. A
defect in `check_owners` has no node. The slices that had a node used one; the
tooling slices substituted the function name, and that substitution worked
exactly as the rule intends (see below). The rule should be generalised rather
than enforced literally.

### 3b. The collisions happened, and they are the wave's best evidence

Indexing on a stable name produced real, visible collisions between agents who
could not see each other:

- **`WIRE-LOOM`** — named in **six** reports: D1, D3, D5, D6, D7, D10, four of
  them substantively. D3 owns the finding (`[repo]` D3:607: the row is live
  against `chain-connectors` = 8, exempted by a date 222 characters away); D5
  reaches it from the regression side; D7 from the pattern-list side; D1 from
  the adversarial side. `[test]` at `566159e` the repaired checker prints that
  exact row as one of its eight live stale values. **Four independent routes to
  one refdes, and the repaired instrument agrees with all four.**
- **`check_bom_figures`** — D1 (F3), D2 (D2-1) and D4 all reach the same defect
  from different directions, with the denominator disagreement noted in §1b.
- **`C-GATE-LOADSW`** — D1, D2, D9, D10 and D19. D2 used it as the reproduction
  case for the flagship fix's failure; D9 and D10 reached the same part from the
  BOM side.
- **The duplicate YAML key** — `STATUS.md` records D12 and D20 finding it
  independently, and `[repo]` D12:476 and D20:58 confirm that both did.
- **`D-CLAMP-BREATH`** — six reports (D4, D9, D10, D16, D19, D20). D19 found the
  corrupted drawing from the conservation side; D9 found the mislabelled part
  from the refdes side. Neither could see the other, and the two findings are
  different halves of one edit.

**Node-indexing earned its keep more clearly than any other property this
wave.** It is the mechanism that turned twenty isolated reports into corroborated
findings. It failed in exactly one place, and that place matters:

### 3c. The indexing stops at the report boundary

`[test]` `grep -oE '\bD[0-9]{1,2}[-.][0-9]+\b'` over `VERIFIED.md` → **0
matches**. Over `STATUS.md` → **0 matches**.

**198 numbered findings exist across fifteen reports** (`[test]` counting only
IDs matching each file's own slice number: D4 23, D16 16, D17 16, D6 16, D13 15,
D15 15, D9 14, D11 13, D2 12, D7 12, D12 10, D14 10, D3 10, D8 10, D18 6), plus
D20's A1–C6 (21), D1's F1–F13 (13), D5's R1–R6 (6) and the unnumbered section
findings of D10 and D19 — call it **250 or so**. `[test]` `VERIFIED.md` carries
**44 `**Confirmed`** and **14 `**Accepted`** verdicts: **58 bolded verdicts,
about a quarter of the findings**, and each one is addressed by restating the
claim in prose rather than by citing its ID.

The consequences are all downstream:

1. **Nobody can tell which findings were verified and which were not.** The
   round-2 README says *"twenty reports and roughly a hundred findings"*. The
   real number is about 250. The orchestrator's own estimate of the wave's
   output is out by a factor of two and a half, which is what happens when the
   things being counted have no register.
2. **`STATUS.md:9` reads *"twenty reports, every one of them hand-verified"***.
   That is true of reports and untrue of findings, and a fast reader takes the
   second meaning.
3. **Round 3 has no list to be complete against.** This is the mechanical reason
   "the last round's fixes were partial" has been true ten times running. It is
   not a failure of diligence. There is literally no artefact in this repository
   that a fixer can tick off.

**This is my strongest recommendation and the cheapest one in this report: a
`FINDINGS.csv` per wave** — `id, slice, node, severity, verdict, landed_in`,
one row per finding, generated by the orchestrator as reports land and closed
by the next round's fixer. It is the same move this project already made for
`config/figures.yaml` and `hardware/bom.csv`: state it once, in a machine
-readable place, and cite it. The wave's own §1 rule applied to the wave's own
output.

---

## 4. Are these waves converging, or spinning?

Both, on different layers, and the split is measurable.

### 4a. The measurement that matters most

`[test]` `git ls-files … | xargs wc -l` at HEAD:

| | lines |
|---|---|
| The design corpus (`CLAUDE.md` §6) | **16,450** |
| `docs/review/**` | **138,093** |
| `docs/log/` + `docs/research/` | 6,808 |
| `tools/` | 2,347 |

**The review apparatus is 8.4× the artefact it reviews.** Per wave `[test]`
`git diff --numstat` between opening commits:

| wave | corpus lines changed | review lines written | ratio |
|---|---|---|---|
| pcb-pipeline | 1,541 | 11,993 | 7.8 : 1 |
| preflight | 774 | 13,720 | 17.7 : 1 |
| restructure | 9,012 | 6,051 | **0.7 : 1** |
| pre-merge | 3,226 | 18,747 | 5.8 : 1 |
| fix-audit | **0** | 12,826 | ∞ (report-only by design) |

The restructure wave is the outlier in the healthy direction, and it is the one
that produced structural change. Every other wave produced between six and
eighteen times more prose about the corpus than change to it.

### 4b. The object of review has escalated, wave over wave

`[git]` in order: the analog design → the schematics → the PCB pipeline → the
repository's structure → the corpus's self-consistency → the checks that
enforce it → **the fixes to the checks** → **the audit of the fixes to the
checks**. Round 2 is the eighth step in that sequence and the second in a row
that does not touch the instrument's subject at all.

**That is the treadmill signature**, and it is the honest reading of the
question. But it is not the whole picture, because:

### 4c. The defect class has shifted, decisively, in the right direction

`[repo]` D20:214 — the finding `STATUS.md` correctly calls the shape of the
wave:

> All four tools are green at HEAD, and **every one of the nineteen is invisible
> to all four.** Not one is a wrong value at the site of an edit. **Fifteen of
> nineteen are on a page that cites the page that was fixed.**

Set that against `[git]` the state nine waves ago: *"Clear the mechanical
staleness backlog: 47 to 0"* (`65bbb83`), *"Clear the semantic staleness
backlog: 12 deletions, 5 still depended on"* (`ed79a01`), *"Four live values for
one quantity, and the fifth instance in an owner doc"* (`c4fb614`).

**The early waves found wrong numbers in the design. The tenth found stale
counts in documents about the repository, and reach failures on pages that cite
the page that was fixed.** By severity the four merge blockers are *all*
apparatus defects — three tooling, one a class of wrong fixes. By count the wave
is still roughly half design (D9–D17, ~129 findings) and half apparatus
(D1–D8, D18, ~113 findings). The design is converging; the apparatus is not,
because the apparatus keeps growing.

### 4d. The verdict

**Not a treadmill, but on the way to becoming one, and the sequence tells you
when it tips.** The evidence for genuine convergence is strong and specific:

- `[test]` This wave predicted precisely what a repair would reveal, and at
  `566159e` the repair revealed it — eight live stale values including the exact
  row D3 named. A spinning process does not make falsifiable predictions about
  its own instrument and get them right.
- D10 **refuted** a passed claim and prevented a forbidden pattern that would
  have made a correct page wrong. That is the loop closing rather than turning.
- D20's class analysis is itself a convergence measurement nobody had made
  before, and it says the defects have retreated from the design into the
  citation graph.

The evidence for spinning is one number and one trend: **8.4 : 1**, and an
object of review that has moved one level of abstraction further from the
instrument at each of the last four waves. `CLAUDE.md`'s own §5 draws the line
in the right place — *"For that, run a review wave. **At gates, not per
commit**"* — and the last three waves have run one per commit batch, which is
per commit with extra steps.

**The thing to measure at the next gate is not the defect count. It is whether
any finding of that wave would have changed a soldering iron's path.** The
fix-audit has several that would — `D-CLAMP-BREATH` drawn as the wrong part,
the 1.30 mm standoff, the `U-LOADSW` row that is three parts in one, the
inverted lighting clamp. Round 2 so far, on this slice's evidence, has none.

---

## 5. What should change in `CLAUDE.md`

Answering the question directly: **which of the five earned its keep?**

| property | verdict this wave |
|---|---|
| **Cold** | **Earned, decisively.** No accidental contamination detectable across 190 report pairs. The 32-versus-37 denominator split and the 47.9-versus-48.4 split are the fingerprints of genuine independence, and they are *worth more* than clean agreement would have been. |
| **Slice by fact domain** | **Earned.** `[test]` the #4 and #5 most-changed files in the batch — `pcb-pipeline.md` (+157) and `repo-maintenance.md` (+156) — had **no owning slice**, and were nonetheless read by nine and thirteen slices respectively, with real defects found in both. Fact-domain slicing covered by fact what file-slicing would have needed two more agents to cover by location. |
| **Provenance on every claim** | **Earned in the body, failed in the headline.** Twenty for twenty on marking. Zero for twenty on marking the summary sentence that `STATUS.md` then quotes. |
| **Node-indexed findings** | **Earned, and the best of the five** — six-way collision on `WIRE-LOOM`, three-way on `check_bom_figures`, two independents on the duplicate YAML key. But the index dies at the report boundary (§3c) and needs generalising beyond "circuit node". |
| **One agent auditing the previous round** | **Over-earned, to the point of imbalance.** The *entire wave* was that audit, and D20 was a dedicated completeness slice on top. Ten for ten on "the last round was partial" is now a result so reliable it has stopped being informative — it should be a standing assumption, not a finding. |

### Proposed edits to the "Review waves" section

**1. Replace the "Nine have run" sentence.** `[repo]` `CLAUDE.md`:114-115 says
*"**Nine have run.** … said 'three' for months while the directory held nine."*
`[test]` `ls -d docs/review/*/` → **11** at HEAD (ten waves plus round 2). The
sentence that explains this project's named failure mode is committing it for
the third recorded time (D20 filed it as A8 at ten). **Delete the count and cite
instead**: *"`docs/review/` is the index; it holds one directory per wave, and
this list has never been kept in sync by anything."*

**2. Add a sixth property: a finding ledger.**

> - **One row per finding, in `FINDINGS.csv`.** A wave's reports are prose; its
>   findings are a list. `id, slice, node, severity, verdict, landed_in`,
>   written as reports land and closed by the next round's fixer. Ten waves have
>   each found the last round's fixes partial, and there has never been a list
>   to be complete against. `VERIFIED.md` records *how* a finding was checked;
>   the ledger records *that* it was, and which ones were not.

**3. Amend the node-indexing rule** to cover the half of a wave that reviews
code:

> - **Findings indexed by the thing the fact is about** — a circuit node, a BOM
>   refdes, a figure id, a `depends_on` edge, or a tool's function name — rather
>   than a file and line. The index is what makes two slices collide visibly.
>   `WIRE-LOOM` was reached by four slices from four directions in one wave, and
>   that agreement is the finding.

**4. Add one line to the provenance rule:**

> An unmarked claim is a defect in the report — **and that includes the
> headline.** A summary sentence must point at the marked claim it summarises,
> because the wave's `STATUS.md` is assembled from summary sentences, and a
> headline is exactly where "arithmetic I did not do" survives.

**5. Add a freeze clause to the wave method:**

> **Name the revision the wave measures against, in the wave's README.** A round
> that audits tooling claims must pin `tools/` as well as the corpus, or say
> that it does not. The fix-audit's twenty `[test]` baselines stopped
> reproducing six minutes into the round that reviews them.

**6. Demote the previous-round audit from a property to an assumption:**

> **Assume the previous round's fixes are partial** — ten waves for ten. The
> useful question is no longer *whether*, it is *in which of the four recorded
> shapes*: a fix that landed on the owner and not on its citers; a retired value
> live in the owning document; a count that went stale inside its own batch; a
> note written in the wrong tense. Slice for those four directly.

---

## 6. The orchestrator's role: one actor, three hats

The same actor wrote the fix batch, wrote the twenty briefs that audit it, and
hand-verified every finding in `VERIFIED.md`. Where that concentration shows:

### 6a. Where it did *not* go wrong, and this matters

`[test]` `VERIFIED.md` contains **44 `Confirmed` and 14 `Accepted` verdicts and
not one rejection**. On any other project that ratio would be the finding. Here
the direction is inverted: **every finding is a criticism of the verifier's own
work, and he confirmed all of them.** `[repo]` `VERIFIED.md`:682 — *"`0014:141`
— my own sentence — is wrong … the evidence was arithmetic I did not do"*;
:336 — *"the wrong claim is now recorded in `hardware/bom.csv`'s own note"*;
:337 — *"Accepted; my stated reason was wrong"*; :30 — *"I removed a drawing
label and did not update the row that exists to describe it."*

`CLAUDE.md`'s stated worry is *"one was wrongly marked disputed by me — which is
worse, because a wrong finding gets caught by the next reviewer while a finding
filed as handled does not."* **This wave has zero findings filed as disputed and
zero filed as handled.** The named failure did not occur. Credit where it is
due: the concentration did not corrupt the verification.

### 6b. Where it shows anyway

1. **The briefs carry the fixer's own taxonomy.** The slices are *tooling,
   register, BOM, content, tables/graph, cross-cutting* — which is the shape of
   the work he had just done, not the shape of the corpus. It happened to
   cover the diff (§5, row 2), but the coverage is a lucky consequence of
   fact-domain slicing rather than of the slicing choice.
2. **One brief was factually wrong and only the fixer's own note could settle
   it.** `[repo]` D7:72-82 — *"the brief's fourth removal does not exist in
   git … they were taken out **before** the commit, so there is no committed
   state in which they existed. That is not a defect in the fix; it is a gap in
   what an auditor can check. The note is the only record, and I could not
   independently verify either."* **This is the clearest single instance of the
   concentration biting.** The fixer's uncommitted intermediate state is
   unauditable by construction, and the only account of it is the account he
   wrote.
3. **The synthesis smoothed two measurements.** `STATUS.md`'s *"D3 and D5
   measured that independently"* (47.9 vs 48.4, and only D5 measured the
   before), and its adoption of D2's `1 of 37` over D1's `1 of 32` without
   mentioning that two slices counted. Both are small; both are the same
   reflex — a synthesiser reconciling his own reviewers, which is the one job a
   synthesiser should not do silently.
4. **`STATUS.md` presents a hand-verified quarter as a hand-verified whole**
   (§3c). 58 verdicts against ~250 findings, described as *"every one of them
   hand-verified"*.
5. **The round-2 freeze was broken by the actor who declared it**, six minutes
   in (§0). The fix itself was right and urgent. Declaring it in the round's
   README was free and was not done.

### 6c. What a different arrangement would have caught

| check a separated arrangement catches | evidence it was missed here |
|---|---|
| **A brief that describes a state that never existed** | D7-12. A brief writer who was not the fixer would have written the brief *from git*, and the fourth removal would never have been asserted. |
| **Findings counted rather than narrated** | ~250 findings summarised as *"roughly a hundred"*; 58 verdicts described as *"every one"*. A verifier with no authorship stake keeps a tally because he cannot hold the set in his head. |
| **Two slices' disagreeing numbers surfaced rather than reconciled** | 32 vs 37; 47.9 vs 48.4. A separate synthesiser has no basis for choosing and must print both. |
| **A pinned measurement revision** | The `566159e` problem is structurally invisible to someone who is both the auditee and the repair crew, because from inside, fixing the instrument *is* progress. |
| **The uncommitted intermediate state** | Nothing catches this except a rule: commit the intermediate state, or record it in the corpus rather than in a note. |

### 6d. The arrangement I would use next time

Not more agents — twenty was enough, and three of the twenty (D1, D3, D20)
carried most of the load. **Split the three hats across time rather than across
people, which this project can actually do:**

1. **The fixer writes no briefs.** He writes a **change register** instead: one
   row per assertion the fix batch makes, generated from the commits, with the
   revision at which it was true. `[repo]` D20 already built this by hand from
   seven commit messages — its method paragraph is the specification. Making it
   an artefact removes the brief author's taxonomy from the slicing.
2. **A single cold agent slices from the register**, seeing the assertions and
   the diff and not the fixer's account of them. That agent also writes the
   freeze clause and pins the revision.
3. **Verification is a slice, not a postscript.** `VERIFIED.md` was written by
   the author of the work being verified, concurrently, as reports landed. Make
   it one more cold slice whose subject is `FINDINGS.csv` — verify by ID,
   record a verdict for every row including *"not checked"*, and let the count
   of unchecked rows be visible.
4. **Keep the deliberate cross-seeding.** It produced one refutation, one
   brief-was-wrong and three widenings out of twelve. Keep it, and keep it
   sourced from the register rather than from the fixer's recollection.

That arrangement costs one extra agent and the discipline of a CSV. It would
have caught four of the five items in §6b outright.

---

## 7. Findings

| # | Finding | Severity | Provenance |
|---|---|---|---|
| E4-1 | **No finding ledger.** ~250 numbered findings across twenty reports; `VERIFIED.md` and `STATUS.md` cite **zero** by ID, and carry 58 bolded verdicts (~25 % coverage). This is the mechanical reason ten consecutive rounds have been "partial" — there is no list to be complete against | **high** | `[test]` `grep -oE '\bD[0-9]{1,2}[-.][0-9]+\b'` over both files → 0 |
| E4-2 | **The wave's twenty `[test]` baselines stopped reproducing six minutes after round 2 opened.** `566159e` landed at 03:07 against a round opened 03:01 whose README says the corpus is frozen; `tools/` was not named either way | **high** | `[git]` `0576a95` 03:01:39, `566159e` 03:07:25; `[test]` HEAD prints `FAIL … 8 stale` where D1/D2/D3/D20 all quote `PASS no live stale values` |
| E4-3 | **The fix-audit's two headline findings are confirmed by the repair.** Deterministic across 8 hash seeds and 10 repeat runs, and 8 live stale values including `WIRE-LOOM`'s `five connectors must match` — the exact row D3 predicted | — *(confirmation, not defect)* | `[test]` 10 identical runs; `PYTHONHASHSEED` 0–7 identical; `.staleness/report.txt` |
| E4-4 | **`CLAUDE.md`:114 says nine waves; the directory holds eleven.** The sentence explaining this project's named failure commits it, for the third recorded time | medium | `[repo]` CLAUDE.md:114-115; `[test]` `ls -d docs/review/*/` → 11 |
| E4-5 | **Five of twenty reports never declare cold status** (D1, D2, D3, D4, D7) — all five tooling/register slices, all five declaring corpus-untouched instead. A template gap, not five lapses | low | `[repo]` heads of all twenty |
| E4-6 | **No accidental contamination detectable.** All 190 report pairs shingled at n=8; every high-overlap pair is co-quotation of a corpus source | — *(the rule held)* | `[test]` shingle intersection over fence-stripped text |
| E4-7 | **Deliberate cross-seeding paid.** ~12 passed claims → 6 confirmed, 3 confirmed-and-widened, **1 refuted** (D10's `360 mA`, preventing a pattern that would have broken a correct page), **1 brief shown wrong** (D7-12) | — *(keep it)* | `[repo]` D10:603-640, D7:72-82, D12:535, D13:203, D14:478, D15:429 |
| E4-8 | **Node-indexing produced the wave's best evidence** — `WIRE-LOOM` reached by four slices independently, `check_bom_figures` by three, `C-GATE-LOADSW` by five, the duplicate YAML key by two. The rule as written ("circuit node or BOM reference") does not cover the half of the wave whose subject is Python | medium *(rule wording)* | `[test]` cross-report token grep |
| E4-9 | **Every headline is unmarked, and `STATUS.md` is assembled from headlines.** Same shape as the wave's own worst finding — ADR 0014's "123 mA exactly", which was arithmetic nobody did | medium | `[test]` paragraph scan + sample read; `[repo]` `VERIFIED.md`:682 |
| E4-10 | **Two independent measurements were reconciled silently in synthesis.** D3 47.9 % / D5 48.4 %, presented as one number "measured independently"; D1 `1 of 32` / D2 `1 of 37`, 37 adopted without note | low-medium | `[repo]` D3:548, D5:123-127, D1:202, D2:20, `STATUS.md`:47 |
| E4-11 | **`STATUS.md`:9 — *"every one of them hand-verified"*** is true of reports and false of findings (58 of ~250) | medium | `[test]` verdict count in `VERIFIED.md` |
| E4-12 | **D17 and D16 assert counts with almost no `[calc]`** — one marker each in 635 and 656 lines, against findings built on edge and row arithmetic. D19 runs four conservation proofs with zero `[calc]` | low-medium | `[test]` marker counts; `[repo]` D17:620, D16:22 |
| E4-13 | **The review apparatus is 8.4× the artefact.** 138,093 lines under `docs/review/` against a 16,450-line corpus; four of the last five waves wrote 6–18 lines of review per line of corpus changed | medium *(process)* | `[test]` `git ls-files` piped to `wc -l`; `git diff --numstat` per wave |
| E4-14 | **The defect class has genuinely converged even as the apparatus has not.** Wave 1–3: live wrong values in the design. Wave 10: 0 of 19 at the site of an edit, 15 of 19 on a page citing the page that was fixed | — *(convergence evidence)* | `[repo]` D20:214; `[git]` `65bbb83`, `ed79a01`, `c4fb614` |
| E4-15 | **The fixer's uncommitted intermediate state is unauditable and the only record of it is his own note** | medium *(structural)* | `[repo]` D7:72-82 |

## 8. What I could not check, and one cold-rule note

- **I did not read any earlier wave's directory**, so every cross-wave claim in
  §4 rests on `CLAUDE.md`'s own summary, the commit log, and diffstats between
  opening commits. In particular I cannot state earlier waves' defect counts,
  so "is the defect count per wave falling" is answered by **class**, not by
  **count**, and I have said so where it matters.
- **One incidental exposure.** `[repo]` D19:60 quotes a grep result naming
  `docs/review/2026-09-21-restructure-design/D3-staleness-paradigm.md` — a path
  in a `grep -rn` transcript, not a reading. I read that line of D19 in the
  course of auditing D19 and did not open the file it names. Recorded because an
  undeclared exposure is worse than a declared one. D19's point about it is
  worth carrying forward on its own: the corpus's only statement that ownership
  lives in exactly one place now survives **only** in a directory reviewers are
  forbidden to read.
- **I did not re-verify the twenty reports' engineering findings.** That is
  other slices' work; this slice's claims about them are claims about their
  *form*, their provenance and their collisions, not about whether the
  underlying numbers are right.
- **I did not read the briefs**, which are not in the repository. Everything in
  §1c and §6b about brief content is inferred from what the reports quote of
  them, and D7-12 in particular rests entirely on D7's account.
