# G4 — The prose-only refutation exemption, attacked

**Slice:** G4, cold. **Date:** 2026-09-22.
**Measured against:** corpus at `a4b80b1`. Confirmed intact: `git diff --name-only
a4b80b1..HEAD` at the time of writing returns nothing outside
`docs/review/` `[test]`. The wave README names `a4b80b1`; the tree HEAD was
`25cc740` when I started and `b4b2f47` when I finished, all of it review
banking.

**Tools pinned:** yes. `tools/check-staleness.py` md5
`26da4e7ba11002bee0b4d6b55d381c88`, identical to `HEAD:tools/check-staleness.py`
`[test]`. Every result below was produced against that byte-identical tool.

**Cold:** I read nothing under `docs/review/`. Two sibling filenames
(`G1-trim-losses.md`, `G5-organisation.md`) appeared in `git status` output I
ran for other reasons; I did not open them or any other file in that tree.

**Where each measurement was taken.** Findings G4-1, G4-8, G4-9, G4-10,
G4-12, G4-13, G4-14, G4-17 are read-only analysis of `/home/user/Woody`.
G4-2 and part of G4-7 were first taken in the shared tree and are marked
where that matters; **every injection result reported below was re-taken in a
private clone** (`git clone /home/user/Woody /tmp/g4-probe && git checkout
25cc740`, verified byte-identical by `diff -rq`) after the coordinator
stopped shared-tree probing. See G4-16.

---

## Verdict

**The change closed the hole it aimed at, and it is a real closure, not a
relabelling.** A forbidden value in a `.csv` or `.yaml` is now reported
whether or not refutation wording sits beside it, and I could not construct a
case that escapes. G4-2.

**It did not close the exemption; it fenced it.** 19.4 % of corpus characters
are still inside an exemption window and therefore still unfalsifiable, the
killer case reproduces unchanged in `.md`, and three of the four structures
the cut line was written to ban — a table row, a data cell, an ASCII drawing
column — are fully exempt as long as they live in a `.md` file. G4-3, G4-4,
G4-7, G4-12.

**The largest remaining hole is not in the rule; it is beside it.** Eight file
extensions in `firmware/`, a directory named in `CORPUS_DIRS`, are scanned by
nothing at all — neither strict nor exempt. G4-6.

**The honest benefit number is 7.2 points, not 48.** G4-12.

---

## 1. The implementation

**G4-1. The file-kind test is one line and it is correct for the four
extensions the scanner actually reads.**

`tools/check-staleness.py:298-300` `[repo]`:

```python
prose = rel.endswith(".md")
(refuted if (prose and REFUTATION.search(near))
 else live).append(rec)
```

`REFUTATION_WINDOW = 300` at `:73`, `REFUTATION` at `:93-104`, and the window
is taken on the line-joined stream at `:258-260` `[repo]`. The corpus globber
at `:158` admits exactly `.md`, `.csv`, `.yaml`, `.yml` `[repo]`. So within the
set of files that are scanned, the partition is total and disjoint: `.md`
prose-exempt, the other three strict. There is no third branch and no way for a
scanned file to get neither treatment.

Today's corpus is 123 files — 70 `.md`, 28 `.csv`, 25 `.yaml`, no `.yml`
`[test]`:

```
$ python3 -c "...corpus_files() ..."
total 123
hardware/bom.csv in scan: True
unplaced.csv in scan: True
Counter({'.md': 70, '.csv': 28, '.yaml': 25})
prose(.md): 70  data: 53
```

**G4-2. The `.csv` / `.yaml` closure is genuine. I could not get a refuted
value past it.**

Three injections in the clone, each reverted and the clone verified clean
`[test]`. The payload is `~275 instrument`, a `forbidden` pattern of
`umbilical-current` `[repo] config/figures.yaml`.

```
### A2 CSV, NO refutation (control)
  path:   docs/reference/path-map-2026-09-21.csv
  result: FAIL ... + 1 stale + 0 bom
### B2 CSV, WITH refutation
  path:   docs/reference/path-map-2026-09-21.csv
  result: FAIL ... + 1 stale + 0 bom
### C2 YAML, WITH refutation
  path:   hardware/module/power-entry/circuit.yaml
  result: FAIL ... + 1 stale + 0 bom
```

B2's injected cell was `This row previously said ~275 instrument mA and that is
superseded and no longer true` — three markers from the `REFUTATION` vocabulary
inside twelve characters of the value. It fails. The old rule passed exactly
this shape.

**G4-3. `.md` files that are really data get the prose exemption. This is the
first place the hole moved.**

Injection, clone, reverted `[test]`:

```
### G2 MD TABLE ROW (markdown that is really data)
  path:   hardware/module/power-entry/power-entry.md
  result: PASS no live stale values | corpus 123 files, ...
```

The injected text was a markdown table, not prose:

```
| Rail | Draw |
|---|---|
| +12 V | ~275 instrument mA, superseded |
| -12 V | 40 mA |
```

That is the `bom.csv` defect shape — a retired value and a refutation word
sharing a data row — and it passes because the row is in a `.md`. The cut line
in `CLAUDE.md` 2b is about what a *segment of a notes cell* does, not about
what file it is in; the implementation is about what file it is in.

This is not hypothetical. **Four of the eighteen live exemption sites are not
prose** `[test]`, classified by whether the matched line is a table row or
inside a fence:

```
TABLE-ROW  docs/decisions/0006-cv-channel-allocation.md:265
TABLE-ROW  docs/decisions/0003-breath-sensing-path.md:118   (2 hits)
TABLE-ROW  docs/decisions/0004-cv-interface-module.md:276
CODE-FENCE hardware/module/breath-receive-stage/breath-receive-stage.md:95
```

That is **5 of the 24 exemption hits, 21 %, sitting in markdown structures that
state rather than narrate.** All five happen to be legitimate today (G4-9) —
but they are legitimate by the author's care, not by the rule.

**G4-4. Inside an ASCII drawing, a refutation in one column exempts a value in
another column.**

`CLAUDE.md` 2b warns that a refutation split *across* a gutter does not count,
and says that trap now applies to prose only. The inverse is the live one: the
join puts unrelated columns into the same 300-character window. Injection,
clone, reverted `[test]`:

```
### H  ASCII DRAWING, refutation in a DIFFERENT column across the gutter
  result: PASS no live stale values | ... | 212 restated-not-cited (advisory)
```

The payload, inside a fenced block:

```
  +---------------+       +----------------+
  | C-BULK 47uF   | ____  | rail draw is   |
  | superseded:   |       | ~275 instrument|
  | was 22uF here |       | mA on +12V     |
  +---------------+       +----------------+
```

The word `superseded` is about the capacitor in the left box. It excuses a live
stale rail current in the right box. Every schematic page in this repository is
"Markdown with ASCII drawings" by convention, so this surface is the house
style, not an edge case.

**G4-5. Both the generated `hardware/bom.csv` and all its fragments are
covered, and identically.** `hardware/bom.csv` and `hardware/unplaced.csv` are
both in the scan set `[test]`, and all 28 `.csv` files take the strict branch
because the branch is on extension, not on path. There is no asymmetry here to
exploit: a value trimmed out of a fragment and a value trimmed out of the
master are both defects. This one is clean.

**G4-6. Eight file extensions fall through the scan entirely — neither strict
nor exempt — and one of them is the language `firmware/` will be written in.**

`firmware/` is in `CORPUS_DIRS` `[repo] :30` and today contains exactly one
file, a `.md` `[test]`. I put a live forbidden value into `firmware/probe.<ext>`
for eight extensions, in the clone, removing each afterwards `[test]`:

```
  firmware/probe.c         -> PASS
  firmware/probe.h         -> PASS
  firmware/probe.py        -> PASS
  firmware/probe.json      -> PASS
  firmware/probe.txt       -> PASS
  firmware/probe.rst       -> PASS
  firmware/probe.MD        -> PASS
  firmware/probe.markdown  -> PASS
--- control: .md in same dir ---
1 stale
```

Three things follow.

- The moment real firmware source lands under `firmware/`, every constant in it
  is invisible to this checker. `firmware/README.md` is already cited as
  normative by `docs/decisions/0006-cv-channel-allocation.md:265` `[repo]`, so
  the directory is not decorative.
- `probe.MD` is the sharp one: a file differing from a scanned file **only in
  the case of its extension** is silently unscanned. There is no case-folding
  anywhere in `:158` or `:298` `[repo]`.
- The `MIN_CORPUS_FILES` tripwire cannot help. `check_corpus_shape` asks only
  that each `CORPUS_DIRS` entry contribute *at least one* file `[repo]
  :191-195`; `firmware/` contributing its single `.md` satisfies that forever,
  however much unscanned code joins it.

---

## 2. The 24 surviving prose exemptions, graded

**G4-7 (method note). They are not reachable with `--detail`.** The brief, and
anyone following it, will reach for `--detail` and `.staleness/report.txt`.
Both print the heading and **none of the rows** `[test]`:

```
$ grep -n "refuted in place" .staleness/report.txt
91:old values present but refuted in place (24) - OK, this is how a correction reads
```

The listing is gated on `VERBOSE`, not `DETAIL`, at `:1264` `[repo]` —
`if VERBOSE:` inside the block whose heading is emitted `detail_only=True`.
Only `--verbose` enumerates them. A count with no list is exactly the shape
`CLAUDE.md` objects to elsewhere: it tells you how many were excused and not
which, so the excused set cannot be reviewed without editing the tool or
reimplementing it.

**G4-8. All 24 are legitimate corrections-in-place. None is a stale value
wearing refutation words.**

I read every one in its file and checked the value it *installs* against
`config/figures.yaml` `[repo]`. Grades:

| Site | Figure | Retired text | Installs | Grade |
|---|---|---|---|---|
| `breath-receive-stage.md:123` ×2 | breath-zero-ref | `+0.579 V`, `0.579 V` | 0.573 V = register | **legit** |
| `breath-receive-stage.md:95` | inamp-full-scale | `−10.05 V` | −9.94 V via `inamp-full-scale` citation | **legit** (in a drawing; refutation on the same line, correct per 2b) |
| `0004:335` | diode-split-rationale | `0.00018 cents` | cites the figure, states no number | **legit, exemplary** |
| `0006:657` | diode-split-rationale | `0.00027 cents` | cites the figure, states no number | **legit, exemplary** |
| `0004:328` ×2 | diode-split-rationale | `about 20 cents`, `20 cents of breath-correlated` | cites `power-entry.md` | **legit** |
| `power-entry.md:102` ×2 | diode-split-rationale | same two | 0.00044 cents = register derivation | **legit** |
| `key-marker-and-bits.md:103` | key-pullup-qty | `21 pull-ups` | qty 24 = register | **legit** |
| `latency-budget.md:183` | loop-budget | `136 µs` | 196–241 µs of 250 µs = register | **legit** |
| `latency-budget.md:184` | loop-budget | `54 % duty` | 78–96 % implied | **legit** |
| `mod-channels.md:201` | mod-reference | `At 2.5 V into 2.5 k` | 1.33 mA `[calc: 3.3333/2500 = 1.3333 mA]` ✓ | **legit** |
| `0006:265` | mod-reference | `written once at boot` | 3.3333 V = register | **legit, but a table row** (G4-3) |
| `0006:722` | pitch-compensation | `1 nF across the feedback resistor` | 2.2 nF, output→(−) = register | **legit** |
| `repo-maintenance.md:43` | sensor-full-scale | `0.2 + 0.766` | quoted as an example of a missed spelling | **legit** |
| `0003:118` ×2 | sensor-full-scale | `0.2–4.80 V` | labelled the datasheet cover-page line | **legit, but a table row**; matches the register's own `false_positive_note` verbatim `[repo]` |
| `0004:78` | spi-series-r | `220 Ω with` | 100 Ω `R-SPI-SER` ×3 = register | **legit** |
| `0004:558` ×2, `spi-link.md:59` ×2 | spi-series-r | `R-SCLK-SER`, `R-CS-SER` | `R-SPI-SER` qty 3 = register | **legit** |
| `0004:276` | umbilical-current | `~275 instrument` | 359 mA = register; `[calc] 45 + 359 = 404` ✓ | **legit, but a table row** |

Every installed replacement matches the register. **This is the strongest
evidence for the change that I found**: the exempt set is currently honest, so
the rule is not carrying rot today. It is also the weakest kind of evidence,
because it is a property of the corpus at one instant, not of the check.

---

## 3. The killer case

**G4-9. A refutation carrying a wrong replacement escapes, reproduced.**

Injection, clone, reverted `[test]`. Both strings are `forbidden` patterns of
`umbilical-current` `[repo]`:

```
### F2 KILLER: refutation whose REPLACEMENT is itself retired
  path:   hardware/module/power-entry/power-entry.md
  result: PASS no live stale values | corpus 123 files, ...
```

Payload:

```
This page previously said ~275 instrument mA down the umbilical. That is
superseded; the corrected figure is: Drop at 290 mA.
```

Two retired values, one of them presented as the *correction*, both excused,
`PASS`. (I first saw this in the shared tree before the stop order; the result
above is the clean re-run.) The commit message for `92afc0b` says the file-kind
rule "closes a case no narrower heuristic could" `[repo]`. It closes it **in
data files only**. In `.md` — 70 % of corpus characters — `TRIM-BREATH-ZERO`'s
exact failure shape still passes.

**G4-10. A live instance in the `.md` corpus: the DAC internal reference is
0.42 cents and 0.54 cents, and a refutation-shaped sentence blesses the wrong
one.**

`hardware/module/pitch-stage/pitch-stage.md:286` `[repo]`, the corrected table:

```
| **DAC internal reference** | **0.42 cents** | **The largest term, and untrimmable** |
```

introduced at `:278-282` by `**The 6× disagreement this table used to flag is
resolved, and both published numbers were wrong.** It was a pivot error … Three
documents used 9 V, 7 V and 2.5 V for the same term.`

165 lines earlier in the same file, `:121` `[repo]`:

```
*(This is also why the ADR's "the DAC's internal reference is sufficient, at
0.54 cents over 10 °C" survives: that figure is a gain term.)*
```

Same quantity, same units, same window ("over 10 °C"). The page's own
correction says the old numbers came from a wrong lever; this sentence says one
of them **survives**. And `docs/decisions/0006-cv-channel-allocation.md:395`
still states it live `[repo]`: `**The DAC's internal reference is sufficient.**
At 0.54 cents over 10 °C it is an order of magnitude inside the resistors`.

`hardware/module/pitch-stage/notes.md:53-54` `[repo]` states the resolution and
names the gap: `LT5400 ratio tracking is **0.027 cents**, not ~0.1, and the DAC
internal reference is **0.42 cents**, not ~0.5. **Neither figure is tracked in**
…

No `forbidden` pattern in the register contains `0.54` `[test]`:

```
$ grep -n "0\.54\|0\.42 cents" config/figures.yaml
479:    candidates: ["0.42 cents (this is a ROW of one table, not a total ...
```

— one hit, and it is the `candidates` list of `pitch-cents-budget`, not a
pattern. So the checker cannot fire on this and never will.

**Honest qualification:** `pitch-cents-budget` is registered `disputed`, and its
`decided_by` reads "pitch-stage.md has two contradictory budget tables back to
back and states no total" `[repo] config/figures.yaml:479-480`. So the page is
flagged. What is *not* flagged is (a) that the contradiction is a specific
number, 0.42 against 0.54, rather than a missing total, and (b) that ADR 0006
restates 0.54 as live in a different file. The dispute entry is about the total;
this is a row. A reader closing the dispute by writing one coherent table would
not necessarily touch `0006:395`.

This is the exact shape `CLAUDE.md` 5 reserves for a human: a sentence whose
refutation wording *endorses* a retired value. It is the class the prose-only
change explicitly does not address, found live.

---

## 4. The window

**G4-11. 300 is three times wider than anything the corpus uses, and the slack
is reachable.**

I measured, for all 24 exemptions, the character distance on the joined stream
from the matched value to the nearest `REFUTATION` marker `[test]`:

```
dist=  93 before  docs/decisions/0003-breath-sensing-path.md:118  '0.2–4.80 V'  <- 'refuted'
dist=  80 before  docs/decisions/0003-breath-sensing-path.md:118  '0.2–4.80 V'  <- 'refuted'
dist=  64 before  docs/decisions/0006-cv-channel-allocation.md:722 '1 nF across the feedback resistor' <- 'until 2026'
dist=  38 before  hardware/interfaces/spi-link/spi-link.md:59  'R-CS-SER'  <- 'previously'
dist=  37 before  hardware/module/power-entry/power-entry.md:102 '20 cents of breath-correlated' <- 'This page used to'
... (tail omitted)
dist=   1 before  hardware/module/breath-receive-stage/breath-receive-stage.md:95 '−10.05 V' <- 'this line carried'
```

**Maximum live distance: 93 characters.** Median under 10. A sweep of the
window in the clone, tool reverted afterwards `[test]`:

```
WINDOW=300  refuted in place (24)  verdict=PASS
WINDOW=200  refuted in place (24)  verdict=PASS
WINDOW=150  refuted in place (24)  verdict=PASS
WINDOW=120  refuted in place (24)  verdict=PASS
WINDOW=100  refuted in place (24)  verdict=PASS
WINDOW=80   refuted in place (22)  verdict=FAIL
```

**The window can be cut from 300 to 100 with literally no effect on this
corpus** — same 24 exemptions, same PASS. At 80 it clips two real corrections
(the two 93/80-character `0003:118` hits) and turns them into false failures.
So ~100–120 is the floor, and 300 carries about 180 characters of pure slack.

That slack is reachable. Injection, clone, reverted `[test]`:

```
### I  WINDOW: refutation about an UNRELATED topic, ~250 chars away
  result: PASS no live stale values
### I-b same but ~400 chars away (outside window)
  result: FAIL ... + 1 stale + 0 bom
```

The payload's refutation is about a capacitor (`The bulk capacitor value was
previously 22 uF and that is superseded.`), followed by 250 characters of filler
about panel assembly, followed by a live stale rail current stated as fact. It
passes. This is the `FB-IN` escape the code comment at `:105-110` describes —
"excused by a `was` 201 characters away, about something else" `[repo]` —
still open at 300, in prose, where the new rule leaves the window in force.

The comment at `:63-72` argues the window exists because "a correction reads
NEXT TO the thing it corrects" `[repo]`. The measurement agrees with the
argument and not with the constant: next to means 93 characters, not 300.

---

## 5. What the change actually bought

**G4-12. The "48 %" figure describes a configuration that no longer exists, and
quoting it as this change's benefit overstates it by roughly 6×.**

The 48.4 % in the code comment at `:116` is explicitly the *pair* — withdrawn
date/arrow/NOT markers **plus** the ±300 window `[repo] :112-124`, and the same
comment warns that conflating the two misleads anyone repeating the work. Those
markers are gone. I measured the excusable surface directly: the fraction of
corpus characters lying within `REFUTATION_WINDOW` of a marker, i.e. where a
forbidden value *would* be excused if placed there `[test]`:

```
=== d69f7fa (pre-trim) ===
  files 123  chars 1,143,596  (.md 63.5% / data 36.5%)
  OLD rule excusable:  30.0% of corpus
  NEW rule excusable:  17.5% of corpus
  data-side closed  :  12.5% of corpus

=== 25cc740 (today) ===
  files 123  chars 1,031,890  (.md 70.7% / data 29.3%)
  OLD rule excusable:  26.6% of corpus
  NEW rule excusable:  19.4% of corpus
  data-side closed  :   7.2% of corpus
```

Read that carefully, because it inverts the credit.

- **On the corpus it actually shipped against, the prose-only rule removes 7.2
  percentage points of excusable surface, 26.6 % → 19.4 %.** Not 48.
- **Had it shipped before the trim it would have removed 12.5 points.** The trim
  did most of the work first and left the rule less to close, by deleting the
  history out of the `.csv` cells rather than by changing what the checker does
  with them.
- **19.4 % of the corpus remains unfalsifiable**, and the fraction *within* `.md`
  is 27.5 % `[test]`.

None of this makes the change wrong — closing the data side permanently is worth
more than the 7.2 points, because it makes the closure structural instead of
contingent on nobody pasting history back. But the corpus is not 0 % exempt and
should not be described as though the question is settled.

**G4-13. The sanctioned destination for retired values is the least falsifiable
part of the corpus, and nothing watches it.**

`CLAUDE.md` 2b: "Where history goes instead: `hardware/**/notes.md`, which is
prose and keeps the exemption, or git."

Measured `[test]`: `notes.md files: 15  chars 36,089  excusable 19,511 = 54.1%
of notes.md`. Over half of the designated history shelf is inside an exemption
window.

And `tools/audit-notes.py` — the tool whose `--regrown` flag exists to catch
history growing back — reads exactly one file: `BOM = os.path.join(ROOT,
"hardware/bom.csv")` at `:38` `[repo]`. It watches the strict zone. **There is
no regrowth detector for the exempt zone.** If history migrates from a BOM cell
into the `notes.md` beside it, `audit-notes.py --regrown` reports improvement,
`check-staleness.py` reports `PASS`, and the values become unfalsifiable on the
way.

**G4-14. The hole was not moved by this change — the trim went to git, not to
`notes.md`.** This is the hypothesis I most expected to confirm and it is false.
`git show --stat` on all six trim commits `9ac7a83 dc4e0c4 ad3a15c c4109ec
192d03e b183696` shows **no `notes.md` in any diffstat** `[test]`; every file
touched is a `bom.csv` or a fragment. The retired text went to git history, as
`CLAUDE.md` 2b's second option says. So G4-13 is a standing risk, not a
realised one. Credit where it is due.

---

## 6. A defect in this wave's method

**G4-15. An injection slice cannot share a working tree with cold reviewers.
Baselines in this wave were contaminated, and I contaminated some of them.**

The wave README promises reviewers a corpus frozen at `a4b80b1`. My brief
instructed me to write forbidden values into corpus files and revert them. Those
are incompatible, and the result was measurable.

Evidence `[test]`, all from `/home/user/Woody` during my run:

- `hardware/module/pitch-stage/circuit.yaml` went `M` in `git status`
  immediately after one of my reverts, in a file I never opened. Its mtime was
  `14:40`, mine were `14:39`.
- `tools/check-staleness.py` and `README.md` both had mtime `14:38:06` with
  md5 **identical to `HEAD`** — written and reverted by another process while I
  was measuring against them.
- The `PreToolUse` hook, which runs the checker on every `Bash` call, reported
  `FAIL ... + 1 stale` between two of my calls on a stale value that was not
  mine.
- Two of my own results, tests D and E, returned a `stale` count one higher
  than my injection could explain. I discarded them and re-ran everything in a
  clone; D2/E2 above are the clean values.
- `ps aux` showed two concurrent `check-staleness.py` processes.

So: at least one sibling slice took a `[test]` baseline while my probe was live,
and I took two while theirs was. **Every `[test]` result produced in the shared
tree today is suspect unless its author verified the tree was clean immediately
before and after.** This is the freeze failure `CLAUDE.md`'s "Review waves"
section describes — declare a revision, then change the thing underneath the
measurements — one layer down: the freeze clause bound the orchestrator's
commits and said nothing about reviewers' working-tree writes, and an
uncommitted write is just as visible to a concurrent reader as a commit.

The fix is one line in the wave README, the same size as the fix that section
already prescribes: *a slice that mutates the tree works in a clone.*

**G4-16. I reverted another agent's in-flight edit.** Carrying out step 1 of the
stop order, I ran `git checkout -- .` in `/home/user/Woody`, which discarded the
modification to `hardware/module/pitch-stage/circuit.yaml`. That edit was not
mine. If a sibling slice was mid-injection on that file, its harness's own
revert became a no-op and its result may be wrong in a way it cannot see. I am
recording it because a silent revert of somebody else's probe is precisely the
"finding filed as handled" failure `CLAUDE.md` warns is worse than a wrong
finding.

**G4-17. The wave README's freeze names `a4b80b1`; HEAD was already `25cc740`
when I started.** The corpus is identical between them — `git diff --name-only
a4b80b1..HEAD` returns only `docs/review/` paths, throughout `[test]` — so no
measurement is affected. Noting it only because the last wave's freeze also held
on the letter.

---

## What I could not check

- **The `.md` corpus semantically, end to end.** I graded all 24 exemption sites
  and ran one targeted hunt (pitch/cents) that found G4-10. The other ~69 `.md`
  files were not read for wrong-replacement cases. There is no mechanical way to
  find them — that is the finding — so absence of further instances here is not
  evidence of absence.
- **The original 48 % measurement.** The vocabulary it used has been deleted
  from the source, so I could not reproduce it; I measured today's vocabulary at
  both revisions instead (G4-12). My 30.0 % at pre-trim is consistent with the
  code comment's own "new vocabulary at the whole-line geometry is 29.3 %"
  `[repo] :121`, which suggests the comparison is sound, but it is not the same
  measurement.
- **`REFUTATION_WINDOW=50`.** The sweep was cut short; I have 300 down to 80.
  The conclusion (100 is free) does not depend on it.
- **Whether the eight hidden stale values cited as motivation were in fact all
  in `.csv`/`.yaml`.** That claim is about a prior wave's corpus and is
  `[from memory]` of the commit message only; I did not verify it, and reading
  the wave that produced it would have broken cold.
- **`.yml`** takes the strict branch by code reading `[repo] :158, :298`; the
  corpus has no `.yml` file, so I could not test it.

---

## If one thing changes

Not the file-kind test — it is right, and it should stay. In order of value per
line of diff:

1. `REFUTATION_WINDOW = 300` → `120`. Zero effect on the corpus today (G4-11),
   removes 180 characters of latent slack, and closes the `FB-IN` shape in prose.
2. Report the 24 under `--detail`, not `--verbose` (G4-7). Three characters.
3. Deny the exemption to `.md` lines that are table rows or inside a fence
   (G4-3, G4-4). This is the cut line applied to the structure rather than to the
   filename, and it would have cost four of today's exemptions a rewrite — all
   four of which restate a figure that is cited elsewhere anyway.
4. Make an unscanned file in a `CORPUS_DIRS` directory a reported problem rather
   than silence (G4-6). The `os.walk` blind spot at `:34-40` was closed by
   asserting the directory exists; this is the same class, one level down —
   asserting the *files* in it were looked at.
