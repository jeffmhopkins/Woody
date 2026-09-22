# G10 — tools/: fail-open holes

**Slice:** G10, cold. I read no directory under `docs/review/` — not this wave's
README, not any prior wave. Everything below is from `tools/`, the corpus, and
experiment.

**Revision measured:** `25cc740`. My brief named `a4b80b1` as the freeze; the
only difference between them is one file under `docs/review/`, and `tools/` is
byte-identical at both. Verified: `git diff --stat a4b80b1 25cc740 -- tools/`
returns empty. Results transfer to either revision.

**Where each measurement was taken.** I began by injecting into the shared
working tree `/home/user/Woody`. The coordinator stopped that mid-slice —
correctly; see G10-33 — and I moved to a private clone at `/tmp/g10-probe`,
checked out at `25cc740`, verified identical (`diff -r` over `tools/` reports
no difference; baseline verdict identical). **Every finding below was
re-measured in the clone with the injection verified present at the moment of
measurement**, except where a finding is explicitly marked `[repo]` (source
reading, no injection). No result in this report rests on an unverified
shared-tree run. Both trees were clean at the end.

**Baseline** `[test]` `python3 tools/check-staleness.py` (clone):

```
PASS no live stale values | corpus 123 files, 23 circuits, 37 figures / 217 patterns | 5 unresolved (tracked) | 211 restated-not-cited (advisory)
```

---

## Part 1 — the self-verification: `instrument()`, `check_checks()`, `RAN`

The coordinator asked for judgement here specifically, so this part leads.

**The assertion works for exactly one failure mode and I could not break that
one.** Deleting the call to `check_links` is caught.

**G10-1 — `check_checks()` proves a check was CALLED, never that its result
reaches the verdict. A one-line edit silences any check and the tool prints
PASS with `0 unwired`.**

`[test]`, clone. Positive control first — inject a broken link into `README.md`,
tool untouched:

```
FAIL 0 shape + 0 owners + 1 links + 0 sections + 0 deps + 0 generated + 0 register-vs-bom + 0 datasheets + 0 dead-patterns + 0 unwired + 0 stale + 0 bom
EXIT=1
```

Now keep the broken link, keep the call, discard the result — insert one line
after `check-staleness.py:1117`:

```python
    link_problems = check_links(files)
    link_problems = []  # neutered
```

```
PASS no live stale values | corpus 123 files, 23 circuits, 37 figures / 217 patterns | 5 unresolved (tracked) | 211 restated-not-cited (advisory)
EXIT=0
```

`python3 tools/check-staleness.py --detail | grep -c UNWIRED` → `0`. No
`UNWIRED CHECKS` section is emitted at all.

**G10-2 — same outcome from a wrong argument.** `[test]`, clone. Change the
call to `check_links([])` — one token, the shape of an ordinary refactor slip:

```
PASS no live stale values | corpus 123 files, 23 circuits, 37 figures / 217 patterns | 5 unresolved (tracked) | 211 restated-not-cited (advisory)
EXIT=0
```

`RAN` records the name, so the check is "wired". It ran on nothing.

**G10-3 — renaming a check off the `check_` prefix makes it invisible to
`check_checks()`.** `[test]`, clone. `def check_links` → `def _audit_links`,
call removed: PASS, exit 0, `0 unwired`, broken link live. `check_checks()`
enumerates `globals()` by name prefix `[repo] tools/check-staleness.py:1087-1090`,
so a check it cannot name cannot be missing.

**The boundary, stated fairly.** `[test]`, clone — remove the call entirely and
leave the function defined:

```
FAIL ... + 1 unwired + ... | EXIT=1
```

So the assertion does what its docstring's *first* paragraph claims: it is not
satisfiable by a commented-out call, and it caught the `check_refdes` shape it
was written for.

**G10-4 — judgement: the self-verification was never designed to reach
G10-1/G10-2, and its docstring implies it was.**
`[repo] tools/check-staleness.py:1049-1060`. The `instrument()` docstring names
two bypasses of the *old* source-text assertion:

> `link_problems = []  # check_links(files)` passes, and so does
> `if False and link_problems:`. Both were demonstrated, each giving PASS with
> a live broken link and UNWIRED CHECKS = 0.

The first of those two is closed. **The second is not.** `if False and
link_problems:` still calls `check_links`, so `RAN` still contains it, so
`check_checks()` still returns clean — the exact scenario the docstring offers
as evidence that the new design is strong. I did not test that literal line; I
tested two variants of the same defect (G10-1, G10-2) and both pass. The
sentence "the assertion itself must not be satisfiable by anything short of the
call actually being made" is true and is the wrong bar: **the call being made
is not the property anyone wants.** The property wanted is that the check's
finding can still fail the run.

This is worth naming precisely because it is this repository's signature: a
fix that closed one instance, and a docstring that generalised from it further
than the code went. The docstring's own second example is a live
counter-example to the paragraph containing it.

**What would actually reach it.** Not more instrumentation of calls. The
verdict is a single boolean assembled in `main()` from ~14 named locals. A
self-test that mutates the corpus is the only thing that proves the wiring end
to end — e.g. a `--selftest` mode that writes a known defect of each class into
a scratch copy of the tree, runs `main()` against it, and asserts `fail` is
True and the relevant counter is non-zero. That tests *consumption*, which is
what G10-1 and G10-2 break, and it is the only version that would have failed
on each of my three edits. A cheaper partial: have each check return into a
registry that `main()` iterates, so there is no place to write
`link_problems = []` — the "is it consumed" question stops existing rather than
being asked.

---

## Part 2 — `check-staleness.py`, everything else

**G10-5 — CONFIRMED (independently, from a sibling's claim relayed to me):
eight file extensions inside the corpus are scanned by nothing, and the `.MD`
case-variant is the sharp one.** `[repo] tools/check-staleness.py:158` —
`if n.endswith((".md", ".csv", ".yaml", ".yml"))`, case-sensitive.

`[test]`, clone. The same forbidden value in eight files under `firmware/`:

```
firmware/g10probe.MD  .c  .h  .json  .markdown  .py  .rst  .txt
--- verdict with all 8 live: ---
PASS no live stale values | corpus 123 files, 23 circuits, 37 figures / 217 patterns | 5 unresolved (tracked) | 211 restated-not-cited (advisory)
--- control: same text in a lowercase .md ---
FAIL ... + 1 stale + 0 bom
```

Two sharpenings the relayed claim did not carry, both `[test]`:

- **It is not firmware-specific.** `hardware/g10probe.MD` with the same value:
  `PASS`, corpus still 123 files. Every `CORPUS_DIR` has it.
- **The corpus count cannot notice.** The count stayed at exactly **123** with
  eight extra files sitting in the tree. `MIN_CORPUS_FILES` is a floor on a
  number these files never enter, so the tripwire is structurally blind to
  them, not merely generously set.
- **`verify-datasheets.py` carries the identical filter**
  `[repo] tools/verify-datasheets.py:182`, so its corpus half is blind the same
  way.

**G10-6 — the refutation-exemption list is counted but not printed, including
in the file the hook tells you to read.** `[repo] tools/check-staleness.py:1262-1266`
— the rows are gated on `VERBOSE`, the count is not. `[test]`, clone:

```
-- with --detail:
old values present but refuted in place (24) - OK, this is how a correction reads

-- in .staleness/report.txt after that run:
old values present but refuted in place (24) - OK, this is how a correction reads

-- with --verbose (first 3 rows):
old values present but refuted in place (24) - OK, this is how a correction reads
  hardware/module/breath-receive-stage/breath-receive-stage.md:123  [breath-zero-ref] '+0.579 V'
  hardware/module/breath-receive-stage/breath-receive-stage.md:123  [breath-zero-ref] '0.579 V'
  docs/decisions/0004-cv-interface-module.md:335  [diode-split-rationale] '0.00018 cents'
```

Correction to the relayed claim: they **are** listable, via `--verbose`. The
defect is narrower and worse-placed than "cannot be listed" — the hook's
message says *"Detail is in `.staleness/report.txt` ... read it when fixing, do
not re-run for detail"* `[repo] .claude/settings.json`, and that file is the
one artefact that never contains them. 24 exemptions are the tool's entire
unfalsifiable surface and the instructed path to them is a dead end.

**G10-7 — the detail report goes stale on the one path the tool calls fatal.**
`[repo] tools/check-staleness.py:1108-1114` — the `TOOL_INPUTS` early return
happens *before* `REPORT` is written at line 1269. `[test]`, clone: run once
clean (report holds a PASS run), then `mv config/figures.yaml` away:

```
  this tool reads 'config/figures.yaml', which does not exist. ...
FAIL 1 shape | corpus 122 files | checks did not run
EXIT=1

### what does .staleness/report.txt say NOW?
corpus: 123 files | bom.csv: 140 rows x 11 cols | figures tracked: 37
figure owners this check CANNOT verify (8) - not failures, but not confirmations either
... line count: 84
```

The failing run said "corpus 122 files | checks did not run". The file the hook
directs you to opens with "corpus: 123 files" and 84 lines of a run that
passed. An agent following the hook's instruction literally reads a clean
report for a failed run.

**G10-8 — `verify-datasheets.py` output is truncated at 120 lines silently.**
`[repo] tools/check-staleness.py:777` — `msgs[:120]`. The surrounding comment
records that the previous cap of 40 dropped a real SHA mismatch behind an
advisory, and the fix reordered "hot" lines first and raised the cap. The cap
is still undisclosed: nothing prints "and N more". `restated[:40]` two hundred
lines further down `[repo]:1208-1212` *does* print "... and N more". Same file,
same batch, one disclosed and one not.

**G10-9 — `EXCLUDE` is dead code, and would misfire if it ever woke up.**
`[repo] tools/check-staleness.py:32,148-150`. `EXCLUDE = ("docs/review",
"docs/log", "docs/research")` is tested against paths walked from
`CORPUS_DIRS`, and no `CORPUS_DIR` is an ancestor of any of them `[calc]`:
`CORPUS_DIRS = ["hardware", "docs/decisions", "docs/reference", "config",
"firmware"]`. The exclusion everyone relies on is enforced by `docs/review`
simply not being listed — not by `EXCLUDE`. Two consequences: the protection
CLAUDE.md §6 describes is not where it looks like it is, and the guard is a
`startswith` on a bare prefix, so a future `docs/logistics/` would be silently
excluded by `"docs/log"`.

**G10-10 — `MIN_CORPUS_FILES`' justifying comment states a corpus size that has
moved.** `[repo] tools/check-staleness.py:48-50`: *"the restructure took the
corpus from 33 files to 118"*. `[test]`: the corpus is **123**. `tools/` is
outside `CORPUS_DIRS` by construction, so no check can reach it — which is the
condition `merge-bom.py`'s own docstring `[repo] tools/merge-bom.py:11-15`
identified and responded to by *deleting* its stale number rather than
correcting it. The same treatment was not applied here. Headroom is 23 files
`[calc] 123 - 100`.

**G10-11 — an empty `hardware/bom.csv` crashes `check_bom()` rather than being
reported.** `[repo] tools/check-staleness.py:418` — `hdr, n, problems =
rows[0], ...` with no guard. `[test]`, clone:

```
    hdr, n, problems = rows[0], len(rows[0]), []
                       ~~~~^^^
IndexError: list index out of range
```

`check_corpus_shape` only asserts the file *exists*. **This is fail-closed in
practice** — exit 1, and the hook's crash branch renders it correctly (see
G10-13) — so it is a robustness defect, not a hole. Recorded because the file
is generated and a `REFUSING TO WRITE` path in `merge-bom.py` can plausibly
leave a zero-length master behind.

**G10-12 — determinism: clean.** `[test]`, clone, `PYTHONHASHSEED` ∈
{0,1,2,42,12345,99999}, six runs on a clean tree, piped through `sort -u`:
exactly one unique line, the baseline PASS. Five further runs at seeds
{0,1,7,42,999} with a live stale value present and verified each run: exactly
one unique FAIL line. The `sorted(..., key=lambda t: (-len(t), t))` total order
at `[repo]:965-966` holds. Runtime 13.5–15.4 s.

*Note on a shared-tree artefact I am discarding:* before moving to the clone I
recorded one run reporting `STALE VALUES STILL LIVE (2)` where the next two
reported `(1)`, from a single injection. I could not reproduce it in the clone
across eleven seeded runs and I attribute it to a concurrent sibling slice
mutating the shared tree (see G10-33), not to the tool. **It is not a
determinism finding and should not be cited as one.**

**G10-13 — the hook: what it does, measured, not read.**
`[repo] .claude/settings.json` + `[test]`.

- It fires on **every** `Bash` call, not on `git commit`. Observed on every
  tool call in this slice, including pure reads. The entry carries
  `"matcher": "Bash"` and an `"if": "Bash(git commit *)"` that gates nothing.
  CLAUDE.md already states this; I confirm it behaviourally.
- It emits `systemMessage` and `hookSpecificOutput.additionalContext` only —
  **no `permissionDecision`**. A `FAIL` cannot block anything.
- Cost: 13.5–15.4 s per invocation against a 60 s timeout `[test]`,
  three runs: 13.91 s, 13.63 s, 13.55 s. Roughly a 4× margin, i.e. a corpus
  four times this size, or one slow subprocess, reaches the timeout.
- **The crash branch works.** `[test]`, clone, with an empty `bom.csv`, running
  the hook's own shell pipeline verbatim: `exit=1  hook would say: CHECKER
  CRASHED (exit 1)`. A traceback does not read as silence. That hole is closed.

**G10-14 — exit codes are used where it matters.** `[repo]
tools/check-staleness.py:361-372,743-767` — `check_bom_generated()` and
`check_datasheets()` branch on `res.returncode`, not on parsed output.
`[test]`, clone, all fail-closed:

| injected defect | tool verdict | check-staleness |
|---|---|---|
| hand-edit generated `hardware/bom.csv` | `merge-bom --check` exit 1 | `FAIL ... 2 generated` |
| hand-edit generated `MANIFEST.csv` | `merge-manifests --check` exit 1 | `FAIL ... 34 generated` |
| flip one byte in a banked PDF | `verify-datasheets` exit 1, sha mismatch named | `FAIL ... 3 datasheets` |
| non-UTF-8 byte in a corpus `.md` | — | `FAIL 1 shape` |

**G10-15 — the documented masking bug is genuinely fixed.** `[test]`, clone,
both generated files hand-edited in the same run: the detail names *both*
tools, `MANIFEST.csv does not match its fragments` and `hardware/bom.csv does
not match its fragments`. Recorded as a pass because the comment at
`[repo]:370-374` claims it and claims are what this wave checks.

**G10-16 — rule 2b holds exactly as written.** `[test]`, clone, three
injections of `-9.6 V` (forbidden for `inamp-full-scale`, now `-9.94 V`), each
verified present at measurement:

| where | wording | verdict |
|---|---|---|
| `circuit.yaml` | *"previously said ... superseded ... no longer correct"* | `1 stale` — **not exempt** |
| `pitch-stage.md` | same refutation wording | `PASS` — exempt |
| `pitch-stage.md` | plain statement, no refutation | `1 stale` |

The prose-only exemption is real, and data files carry no history. No hole
found here.

---

## Part 3 — `verify-datasheets.py`

**G10-17 — the corpus half has no shape assertion: rename a `CORPUS` entry and
it goes silent with a clean summary and exit 0.** `[repo]
tools/verify-datasheets.py:169-199` — `CORPUS` is a hand-written list walked
with `os.walk`, which yields nothing for a missing directory. `[test]`, clone,
with a dangling datasheet citation planted in `docs/decisions/`:

```
### 1. dangling citation in docs/decisions -> caught?
  CORPUS PATHS THAT DO NOT RESOLVE (1) of 68 cited:
EXIT=1
### 2. same citation, but docs/decisions renamed away
datasheets: 78 verified, 23 recorded as blocked or not-fetched, 0 problems
EXIT=0
```

This is the identical blind spot `check-staleness.py` documents at
`[repo]:34-51` as *"THE CHECKER'S OWN BLIND SPOT, found 2026-09-21 and
reproduced before fixing"*. The fix — `check_corpus_shape` plus a file-count
floor — went into `check-staleness.py` and not into its sibling, which carries
its own copy of the corpus definition. Same class, same repository, same
fortnight, unfixed next door.

**G10-18 — the coverage number prints only on failure, so a run that checked
zero citations is byte-identical to a healthy one.** `[repo]
tools/verify-datasheets.py:202` — `"... ({len(dangling)}) of {checked} cited"`
is inside `if dangling:`. In the G10-17 transcript, run 1 discloses "of 68
cited"; run 2 checked **0** and says nothing. `check-staleness.py` puts its
coverage on every line, pass or fail, for exactly this reason `[repo]:1283-1291`
— *"emptying every forbidden list in the register produced a PASS line
byte-identical to a healthy run"*. The lesson did not travel one file over.

**G10-19 — `ARTEFACT` and `PATH_RE` are two hand-maintained extension lists in
one file and they disagree: three bankable kinds cannot be citation-checked.**
`[repo] tools/verify-datasheets.py:22-23` vs `:171-173`. `[test]`, clone,
planting a dangling citation of each extension in a corpus page:

```
ext=pdf        caught=1
ext=lib        caught=0
ext=asy        caught=0
ext=jpeg       caught=0
ext=kicad_mod  caught=1

in ARTEFACT (bankable) but NOT in PATH_RE (citation-checked): ['asy', 'jpeg', 'lib']
in PATH_RE but not bankable: ['csv']
```

`.jpeg` is the likely one to bite — `.jpg` is covered and `.jpeg` is not.

**G10-20 — a third definition of "the corpus", differing from the other two.**
`[repo] tools/verify-datasheets.py:169-170` lists `CLAUDE.md`;
`check-staleness.py`'s `CORPUS_DIRS`/`CORPUS_FILES` `[repo]:30-31` does not.
`rewrite-paths.py` maintains a fourth partition (`HISTORY`/`HAND_EDITED`,
`[repo] tools/rewrite-paths.py:44-60`). CLAUDE.md §6 states the corpus once;
rule 1 says cite it. Four hand-written copies is the precondition this
repository exists to prevent, sitting in the tools that enforce it.

---

## Part 4 — `audit-notes.py` (new today)

This is where the most consequential findings are. The tool is green, and the
green is not load-bearing.

**G10-21 — the `HIST` vocabulary is case-sensitive, while `segments()`
guarantees every segment starts with a capital. Ten of the eighteen markers can
never match at the start of a sentence.** `[repo] tools/audit-notes.py:71-72` —
`re.search(p, s)` with no flags; `[repo]:63` — the splitter only breaks a new
segment before `[A-Z*(]`. `[test]`, clone:

```
  lower -> HIST    Capitalised -> PLAIN   This row said DO-214AC.
  lower -> HIST    Capitalised -> PLAIN   Used to be 220nF.
  lower -> HIST    Capitalised -> PLAIN   No longer fitted.
  lower -> HIST    Capitalised -> PLAIN   Superseded by the SS14.
  lower -> HIST    Capitalised -> PLAIN   Retired on 2026-09-01.
  lower -> HIST    Capitalised -> PLAIN   Refuted by the datasheet.
  lower -> HIST    Capitalised -> PLAIN   Was never a pure offset.
  lower -> HIST    Capitalised -> PLAIN   The review caught it.
  lower -> HIST    Capitalised -> PLAIN   Cold review found this.
  lower -> HIST    Capitalised -> PLAIN   Was wrong.
```

The author *did* hand-write uppercase alternates for the shouted forms —
`superseded|SUPERSEDED`, `retired|RETIRED`, `REFUTED|refuted` — and missed the
Capitalised form of every one. `check-staleness.py`'s `REFUTATION` regex uses
`re.I` `[repo]:105`. Two vocabularies for the same concept, one case-folded and
one not.

**G10-22 — consequence: the canonical example from CLAUDE.md and from this
tool's own docstring is live in `hardware/bom.csv` right now, and the tool
cannot see it.** `[test]`, clone, `hardware/bom.csv` row `D-REVSHUNT`:

```
"This row said DO-214AC, which is the SS14's package. [datasheet SS34.pdf p.1] states 'MECHANICAL DATA / Case: SMC (DO-214AB)' ..."
```

`[repo] tools/audit-notes.py:22` gives *"This row said DO-214AC, which is the
SS14's package" goes*, verbatim, as the example of text to cut. CLAUDE.md §2b
uses the same sentence. `[test]` `python3 tools/audit-notes.py D-REVSHUNT`
marks every segment of that row `...` (PLAIN) and never flags it.

Two more in the same state `[test]`, found by re-running the classifier
case-insensitively and diffing:

```
MECH-UBOLT   PLAIN->HIST  This row said "not adjustable afterwards" until 2026-09-21, which was true of a bonded body.
WIRE-LOOM    PLAIN->HIST  This replaces the tail-mounted alternative's 32-44 conductors and ~46 hand-terminated joints
```

The 2026-09-22 trim took the BOM notes 118,198 → 82,129 characters `[test]`
and left its own headline example behind, in the one row whose defect the rule
was written from.

**G10-23 — the dated `| YYYY-MM-DD` rule — the first `HIST` pattern, and the
shape the docstring says all 48 segments took — can never fire, because
`segments()` consumes the `|` it requires.** `[repo]:62` splits on
`r"\s*\|\s*(?=\*{0,3}\s*\d{4}-\d{2}-\d{2})"`, discarding the delimiter;
`[repo]:50` then looks for `r"\|\s*\d{4}-\d{2}-\d{2}"`. `[test]`, clone:

```
HIST dated pattern on a SPLIT segment: False
HIST dated pattern on the UNSPLIT cell: True

dated '| YYYY-MM-DD' markers present in hardware/bom.csv : 12
segments audit-notes classifies as 'dated supersession'   : 0
```

A dated segment carrying no other marker word classifies `PLAIN` — "neutral",
the class that means nothing to see:

```
   [LIVE ] 'Gold contacts, NEVER silver.'
   [PLAIN] '2026-09-01: 220R, per the bench session.'
```

This is exactly the defect `check_patterns()` exists to catch for
`config/figures.yaml` — *"a forbidden pattern that CANNOT match is
indistinguishable from one that matches nothing"* `[repo]
tools/check-staleness.py:305-307`. Nothing audits `audit-notes.py`'s own
vocabulary the same way, and its headline rule is in that state on day one.

**G10-24 — `--regrown` reports zero while seventeen rows carry a history or
ambiguous segment; the threshold is `>= 2` and every row has exactly one.**
`[repo]:128` — `bad = [p for p in per if p[1] >= 2]`. `[test]`, clone:

```
rows by HIST+BOTH count: {0: 123, 1: 17}
0 row(s) still narrating rather than specifying     (exit 0)
```

The distribution has no mass at all above 1. The threshold is not tuned, it is
above the data — so `--regrown` currently reports a clean BOM whatever the 17
rows say, and would keep doing so until some row acquires a second flagged
segment. Combined with G10-21 and G10-23, its green means neither "no history"
nor "history below threshold"; it means the detector and the threshold miss in
opposite directions at once.

**G10-25 — it does have the "fires on correct rows" problem its own `--regrown`
comment warns about; the comment fixed the *length* heuristic and the
*vocabulary* has it instead.** `[repo]:120-127` — *"A threshold that fires on
correct rows is the trap CLAUDE.md names, in the tool written to enforce the
rule."* `[test]`, clone, showing the literal trigger text:

```
--- J-UMBILICAL-CABLE  [HIST] matched-by=['supersession']   trigger: ['REPLACES']
    *** THE SUCCESSOR IS 1.1mm FATTER AND 1.6mm SHORTER THAN THE PART IT REPLACES, AND IT ADDS A 4.5mm LOWER BOUND ON CABLE OD ... - check the chosen Cat5's jacket against it

--- R-PRECISION  [HIST] matched-by=['refutation']           trigger: ['refuted']
    CAVEAT FOR ANYONE EDITING ADR 0006: ... are NOT-IN-DOCUMENT rather than refuted - do not 'correct' ADR 0006 by citing rev fa's silence.

--- R-OUT-PROT  [BOTH] matched-by=['review narration']      trigger: ['reviewers found']
    *** The worst case is output-to-output patching, not a short: ... giving 322mW against a 220R source at +/-10V (two reviewers found this independently ...)

--- D-USBOR  [HIST] matched-by=['refutation']               trigger: ['no longer']
    Both sources drop ~0.3V, leaving ~4.7V at the dev boards' 5V pins ... the breath sensor is no longer on this rail.
```

All four are live builder instructions. `J-UMBILICAL-CABLE`'s is a mechanical
fit warning in shouted capitals — the most consequential sentence in the row —
marked `cut` because it contains the words "THE PART IT REPLACES".
`R-PRECISION`'s is an instruction *not to* treat something as refuted, matched
on the word `refuted`. CLAUDE.md: *"A pattern that fires on a correct sentence
is worse than no pattern, because its cheapest fix is to make the sentence
wrong."* Acting on this tool's output row by row would delete a fit warning.

**G10-26 — `LIVE`'s imperative rule is uppercase-only for `DO NOT` while its
neighbour covers both cases.** `[repo]:42` — `r"\bNEVER\b|\bDO NOT\b|\bMUST\b|\bmust\b"`.
Lowercase "do not" is invisible; lowercase "must" is not. `R-PRECISION` above
classifies `HIST` rather than `BOTH` purely because its imperative is written
"do not 'correct'". Case-folding the whole set moves `LIVE` from 72 to 119
segments `[test]`.

**G10-27 — history the vocabulary misses entirely.** `[test]`, clone, 13
probes; 10 classify `PLAIN`:

```
PLAIN  Previously 8HP.
PLAIN  This row said DO-214AC, which is the SS14's package.
PLAIN  Originally specified as 6HP before the panel grew.
PLAIN  Changed from DO-214AC to SMA on 2026-09-01.
PLAIN  Was 100R.
PLAIN  Corrected 2026-09-20: now 220R.
PLAIN  The 2026-09-21 review caught this.
PLAIN  Obsolete: the LM311 branch is gone.
PLAIN  Deprecated in favour of the DAC8568.
PLAIN  Withdrawn after bench measurement.
PLAIN  This value is stale and was withdrawn.
HIST   An earlier revision of this row carried 4.7 V.
LIVE   NEVER use silver contacts.
```

Not all of this is case sensitivity. `previously`, `corrected`, `obsolete`,
`deprecated`, `withdrawn`, `stale` are all in `check-staleness.py`'s
`REFUTATION` set `[repo]:94-99` and in none of `audit-notes.py`'s. Two
independent hand-written lists of "words that mean a correction was made",
neither citing the other, disagreeing on ten words. That is rule 1 with a
vocabulary as the value.

**G10-28 — `--regrown` is silently ignored when a `REF` is also given.**
`[repo]:91-107` — the `if args:` branch `return 0`s before `regrown` is read.
`[test]` `python3 tools/audit-notes.py R-SPI-SER --regrown` prints the
per-row listing and exits 0. The flag is accepted and discarded.

**G10-29 — an unknown `REF` prints nothing and exits 0.** `[test]`
`python3 tools/audit-notes.py NO-SUCH-REF` → no output, `EXIT=0`. A typo'd
refdes is indistinguishable from a row with nothing to report. No crash on
piping to `head` (`stderr` empty, exit 1 from `SIGPIPE`, no traceback), and no
empty-notes cells exist to crash on `[test]`.

---

## Part 5 — `extract-findings.py`

Tested against a synthetic wave in `/tmp`, written by me. **I read no real
review report** — which also means I cannot say which of these shapes this
wave's reports actually use.

**G10-30 — the verdict is a substring test, so one finding's id closes
another's.** `[repo] tools/extract-findings.py:91` — `"recorded" if r["id"] in
verified`. `[test]`, with `VERIFIED.md` containing only *"Checked X1-11 and
X1-12 by hand. Also X1-4."*:

```
id,slice,line,severity,verdict,headline
X1-1,X1,3,high,recorded,"X1-1 bold run at line start, high severity."
```

`X1-1` is never mentioned in `VERIFIED.md`. It is marked **recorded** because
it is a prefix of `X1-11`. In a wave with more than nine findings per slice —
i.e. every wave this repository runs — `X1-1` and `X1-2` are closed for free by
any verification that touches the teens and twenties. The tool exists because
*"202 numbered findings ... zero of them referenced by id"*; the mechanism
built to make closure checkable silently closes findings by prefix collision.
This is the same defect class as G10-1: a check that reports green inside the
check written to close an earlier one.

**G10-31 — a finding introduced as a Markdown heading is never introduced.**
`[repo]:35` — `INTRO`'s leading class is `(?:[-*>|]\s*)*` and `#` is not in it.
`[test]`:

```
X1-4,X1,,,recorded,CITED ONLY - introduced in no report      <- was "### X1-4 heading introduction, critical"
X1-5,X1,,,NOT ADDRESSED,CITED ONLY - introduced in no report <- was "#### **X1-5** bold heading"
X1-6,X1,,,NOT ADDRESSED,CITED ONLY - introduced in no report <- was "1. X1-6 numbered-list introduction"
```

Bullets, blockquotes, table rows and bold runs all work. Headings and numbered
lists do not — and a heading is the most natural way to introduce a finding in
a long report. The line number, the headline and the severity (`critical`, on
X1-4) are all lost, and the row is mislabelled as a cross-reference to a
sibling's finding. Note X1-4 comes out simultaneously "recorded" and
"introduced in no report".

**G10-32 — finding ids at 100 and above vanish from the ledger entirely.**
`[repo]:28,35` — `[A-Z]\d{1,2}[-.]\d{1,2}`. `[test]`:

```
'X1-100'          ID=[]            INTRO=False
'**X1-100** text' ID=[]            INTRO=False
'X1-99'           ID=['X1-99']     INTRO=True
'ABC1-2'          ID=[]            INTRO=False
'X100-1'          ID=[]            INTRO=False
'E2-8'            ID=['E2-8']      INTRO=True
```

My synthetic report contained twelve findings; the ledger reported eleven and
no error. For a tool whose entire purpose is *"there was no denominator"*, a
silently wrong denominator is the worst available failure. Also lost:
multi-letter slice prefixes (`ABC1-2`) and slice numbers ≥ 100.

**G10-33 — the docstring's own count disagrees with CLAUDE.md.**
`[repo] tools/extract-findings.py:7` says **198** numbered findings;
CLAUDE.md's review-waves section says **202**. Both describe the same last
wave. I cannot adjudicate which is right without reading `docs/review/`, and I
did not. One of them is stale, in the file written to stop counts going stale,
which says so about itself two paragraphs later `[repo]:18-22`.

**G10-34 — minor, `--check`.** The mismatch branch prints a hard-coded
`"FINDINGS: checked {n} | 1 problems"` `[repo]:107` regardless of how many rows
differ. And `extract-findings.py --check <wave>` (flag first) tracebacks with
`FileNotFoundError: '--check'` rather than a usage message — fail-closed, exit
1, but it is a plausible invocation. `--check` itself works: `[test]` appending
one fabricated row to `FINDINGS.csv` is detected, exit 1.

---

## Part 6 — `check-conservation.py`, `merge-bom.py`, `merge-manifests.py`, `rewrite-paths.py`

**G10-35 — `check-conservation.py`'s own claims all hold.** `[test]`, clone,
against `hardware/module/pitch-stage/pitch-stage.md` at `HEAD`:

| case | result |
|---|---|
| identical copy | 0 seams, 0 REAL GAPS, exit 0 |
| interior line deleted | `REAL GAPS: 1`, exit 1 |
| first 6 words deleted | `HEAD: the source's first 8 words are not in any destination`, exit 1 |

The head/tail asymmetry documented at `[repo]:55-71` is genuinely fixed, and
the exit code is genuinely non-zero.

**G10-36 — what it does not check: it is one-directional, and nothing asserts
the destinations are not the source.** `[test]`, clone: appending *"The rail is
-9.6 V and the module is 8HP."* to an otherwise-complete destination gives
`REAL GAPS: 0`, exit 0 — correct for a conservation check, and a reader seeing
"content conservation ... green" may take it for more. More usefully: passing
the **source itself** as its own destination gives `REAL GAPS: 0`, exit 0 —
a split that never happened proves conserved. The destination list is
hand-typed by the caller and the tool has no wired caller `[test]`, so nothing
constrains it.

**G10-37 — `merge-bom.py` and `merge-manifests.py` are the two tools I could
not break.** `[test]`, clone: problems are evaluated before the write
(`REFUSING TO WRITE`, master unchanged); `--check` byte-compares and exits 1;
a fragment on disk but absent from `ORDER` is refused; the 11-column CRLF
render is stable (`140 rows x 11 cols`); `merge-manifests` refuses a
zero-fragment glob. `merge-bom.py`'s docstring correctly *deletes* rather than
corrects the two counts it can no longer verify `[repo]:11-15,31-33` — the only
place in `tools/` that responds to the unreachable-by-any-check problem
properly, and the pattern the other tools should copy.

**G10-38 — `merge-manifests.py` states the fragment count three times in one
file, in three different numbers, none of them right.** `[repo]
tools/merge-manifests.py:5` — *"The **six** researchers wrote to separate
fragments"*; `[repo]:19` — *"a move written as `git mv datasheets/* elsewhere/`
leaves all **eight** behind"*; `[repo]:44` — *"the exact-header check keeps
working on all **eight** fragments"*. `[test]`, clone:

```
$ ls datasheets/.manifest-R*.csv | wc -l
9
MANIFEST.csv: 101 rows from 9 fragments | 78 ok, 22 blocked, 1 other
```

Nine. This is this repository's named failure, three times over, inside a tool,
where §6 guarantees no check can reach it.

**G10-39 — `rewrite-paths.py --verify` excludes five §6-corpus documents by
name, so "0 surviving old-side token(s)" is compatible with old paths surviving
in them — and one does.** `[repo] tools/rewrite-paths.py:101` — `rewritable()`
excludes `HAND_EDITED`, which contains `CLAUDE.md`, `README.md`,
`docs/reference/repo-maintenance.md`, `hardware/module/mod-channels/mod-channels.md`
and `hardware/module/pitch-stage/pitch-stage.md` `[test]`. All five are in the
corpus CLAUDE.md §6 defines. `[test]`, clone:

```
verify: 0 surviving old-side token(s)      (exit 0)

tools/rewrite-paths.py:               2 old-side token(s) still present
docs/reference/path-map-2026-09-21.csv: 29 old-side token(s) still present
docs/reference/repo-maintenance.md:    1 old-side token still present
```

`docs/reference/repo-maintenance.md:375` reads *"split out of
`hardware/module/power-entry.md`, but power-entry has its own"*, and that path
does not exist `[test]`. **I judge that one a legitimate historical mention** —
repo-maintenance.md is §7's path-resolution authority and naming old paths is
its job, and `path-map-…csv` obviously must contain them. CLAUDE.md warns most
hits will be legitimate, and these are. The finding is not the survivor; it is
that `--verify` printing `0` tells you nothing either way about five corpus
documents, and the docstring's *"assert no old-side token survives outside
history"* `[repo]:12` does not mention the second, larger exclusion.

**G10-40 — `--apply` and `--verify` see only tracked files.** `[repo]:95-98` —
`tracked_files()` runs `git ls-files`. A page created during a restructure and
not yet `git add`ed is neither rewritten nor reported. Fail-open, and the
window is exactly the moment the tool is used.

**G10-41 — only one tool is wired to anything automated.** `[test]`, grepping
the corpus and `.claude/` for each tool name, excluding history directories:
`.claude/settings.json` invokes `check-staleness.py` and nothing else.
`merge-bom.py --check`, `merge-manifests.py --check` and `verify-datasheets.py`
run as subprocesses of it (G10-14). `audit-notes.py`, `extract-findings.py`,
`check-conservation.py` and `rewrite-paths.py` have **no automated caller at
all** — every mention is prose in CLAUDE.md or `repo-maintenance.md`. Their
exit codes reach nobody, which is worth knowing before relying on
`audit-notes.py --regrown` returning 1 (G10-24) as a gate.

---

## Part 7 — process

**G10-42 — this wave's freeze clause bound the orchestrator and not the
reviewers, and put an injection-testing slice in the same working tree as
eleven read-only ones.**

I was briefed to inject defects into `/home/user/Woody` and revert them. Eleven
cold slices were reading that tree at the same time. During my injection window
they observed `README.md` carrying a broken link, `tools/check-staleness.py`
patched to `check_links([])`, and `hardware/module/pitch-stage/circuit.yaml`
modified; the `PreToolUse` hook flipped `PASS → FAIL(1 links) → PASS →
FAIL(1 stale)` across another slice's read-only calls, and at least one
reviewer logged my sabotaged checker reporting `PASS` over my own broken link
as a **live fail-open recurrence in the corpus** rather than as an experiment.
Because none of it was committed, `git log` would never have shown it. A second
injection slice's `git checkout -- .` then discarded an in-flight edit that was
not its own, which silently invalidates any measurement taken across that
window — I discarded one of my own results on that basis (see the note under
G10-12) and re-ran every injection in a private clone.

Three things follow, and none of them is about diligence:

1. **A wave that tells any agent to mutate shared state has no reproducible
   baseline for anybody.** Every `[test]` in every slice this round was taken
   against a tree that could have been mid-injection. The last wave's recorded
   failure was an orchestrator committing a tooling fix mid-round so that two
   slices running one command twenty minutes apart got opposite verdicts
   (CLAUDE.md, "Name the revision a wave measures against"). This is the same
   mistake one layer down: the freeze named a revision and said nothing about
   the working tree.
2. **The mitigation is one line and costs nothing**: an injection slice works
   in `git clone <repo> /tmp/<slice>-probe && git checkout <frozen-rev>`. The
   clone is byte-identical (I verified `diff -r` over `tools/` and an identical
   baseline verdict), so every result transfers, and nothing a slice does can
   be seen by anyone else. Adding "slices that mutate files work in a clone" to
   the wave README is the whole fix.
3. **An uncommitted defect is invisible to the record that would explain it.**
   The reviewer who logged my injection as a live finding had no way to
   discover otherwise. If this wave produces a fail-open finding about
   `check_links` returning PASS over a broken `README.md` link, it is mine and
   it is an artefact — but G10-1 and G10-2 are *not* artefacts, and a
   verification round will have to tell them apart. The distinguishing fact:
   my findings reproduce in a clean clone at `25cc740` with the tool's source
   patched, and require that patch.

---

## What I could NOT check

- **Anything in `docs/review/`.** I stayed cold, so: `extract-findings.py` was
  tested only against a synthetic wave I wrote, and I cannot say which report
  shapes the real reports use — G10-31 and G10-32 describe capabilities, not
  measured losses. I could not adjudicate G10-33 (198 vs 202). I could not
  check whether any real `VERIFIED.md` has already been bitten by the prefix
  collision in G10-30.
- **`rewrite-paths.py --apply` and `--invert`.** `--invert` needs the
  restructure's baseline revision and `--apply` mutates the whole tree; I ran
  only `--verify` and read the rest `[repo]`. G10-39/G10-40 are source findings
  with a partial `[test]`.
- **Whether the 24 refutation exemptions (G10-6) are each legitimate.** I
  listed them with `--verbose` and did not audit them; that is a fact-domain
  slice's job, not a tools slice's.
- **Semantic correctness of any figure or circuit.** Out of brief.
- **`merge-manifests.py`'s `.moves.csv`, dedup, `DISTINCTIVE`/`_freq`
  heuristics** beyond confirming the tool runs clean and refuses the cases its
  comments claim. That is a large surface I read but did not attack.
- **Behaviour at the 60 s hook timeout.** I measured the margin (G10-13) but
  did not force a timeout to see what the hook renders.

## Repository state

Both trees clean. `/home/user/Woody`: `git status --short` shows only other
slices' untracked report files plus this one; `git diff --stat` and
`git diff --cached --stat` are empty; `python3 tools/check-staleness.py` reads
`PASS no live stale values | corpus 123 files, 23 circuits, 37 figures / 217
patterns | 5 unresolved (tracked) | 211 restated-not-cited (advisory)` —
byte-identical to the baseline at the top of this report. The clone
`/tmp/g10-probe` is also clean and can be deleted. I wrote exactly one file in
the repository: this one.
