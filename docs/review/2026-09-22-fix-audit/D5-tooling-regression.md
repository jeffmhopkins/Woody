# D5 — Did rebuilding the checks break anything that used to work?

**Slice:** tooling regression audit of `0e68f25` ("Fix the tooling, and the
defects the fixed tooling then found").
**Question:** for every defect class these tools **already caught** before
that commit, is it still caught?
**Verdict:** **six regressions.** The rebuild closes nine holes and opens six.
Four of the six are in `check_figures` — the one check the whole repository
exists for — and two are in `check_links`.

## Method

Three throwaway trees under the session scratchpad:

```
git archive 0e68f25~1 | tar -x -C .../old      # OLD tools, OLD corpus
git archive HEAD      | tar -x -C .../new      # NEW tools, NEW corpus
git archive HEAD      | tar -x -C .../mixed    # NEW corpus, then old tools/*.py copied over
```

The `mixed` tree is the control that matters: old tools against the *same*
corpus the new tools see, so a difference is attributable to the tool change
and not to the 85 corpus files that also moved in this batch. **Every
regression below was confirmed on `mixed`**, not just on `old`.

Each defect was injected mechanically by a script
(`scratchpad/inject.py`, not committed), one defect per fresh copy of a tree,
then `python3 tools/check-staleness.py` was run and the summary line compared.

Baselines, all `[test]`:

```
[old]   PASS no live stale values | corpus 121 files, 23 circuits | 5 unresolved (tracked)
[new]   PASS no live stale values | corpus 123 files, 23 circuits, 37 figures / 218 patterns
        | 5 unresolved (tracked) | 233 restated-not-cited (advisory)
[mixed] FAIL 0 shape + 0 owners + 0 links + 0 sections + 0 deps + 0 generated + 1 stale
        + 0 bom | corpus 123 files | 5 unresolved (tracked)
```

The single `mixed` finding is `[spi-series-r] '220 Ω with'` at
`docs/decisions/0004-cv-interface-module.md:78`, which the **new** tool
correctly exempts: the refutation "is refuted, 2026-09-21" sits on line 77,
one line above, and the new 300-character window reaches it where the old
line-span context did not. That is the window's genuine win, and it is
recorded here so the findings below are not read as "the window is all bad".

---

## THE REGRESSIONS

### R1–R3 — `check_figures`: three new exemption tokens that are ordinary prose

`[repo] tools/check-staleness.py:73,93–106,227–231`

The rebuild made two changes at once: it narrowed the refutation context from
a whole line to a 300-character window (`REFUTATION_WINDOW`), and it changed
the vocabulary — dropping `was`, `old`, `rather than`, `instead of`, `wrong`
and adding **a bare ISO date `\d{4}-\d{2}-\d{2}`, a bare `->`, a bare `→`, and
a case-sensitive `NOT`**.

Those four additions are not correction markers. They are punctuation and
dates that appear all over ordinary technical prose in this corpus. A live
stale value within 300 characters of any of them is now filed under
*"old values present but refuted in place — OK, this is how a correction
reads"* and the tool exits 0.

Injected text, appended to `docs/decisions/0004-cv-interface-module.md`
(`The panel is 8HP` is a live `forbidden` pattern of `panel-width`):

**R1 — an unrelated date.**

```
## Mechanical review note

Bench session 2026-08-14 covered the jack layout only; nothing about the
front plate changed and the mounting screws are unchanged.

The panel is 8HP wide and that is the final width.
```

```
[test] $ python3 tools/check-staleness.py
  [old]   FAIL 0 shape + ... + 1 stale + 0 bom | corpus 121 files            rc=1
  [mixed] FAIL 0 shape + ... + 2 stale + 0 bom | corpus 123 files            rc=1
  [new]   PASS no live stale values | corpus 123 files, 23 circuits, ...     rc=0
```

The exempting token, dumped from the new tool's own window:

```
[test] window text[at-300 : at+len+300], REFUTATION.search() =>
       <re.Match span=(181, 191), match='2026-08-14'>
       REFUTATION_SHOUT.search() => None
```

Under `--verbose` the new tool lists it explicitly as refuted:

```
[test] docs/decisions/0004-cv-interface-module.md:972  [panel-width] 'The panel is 8HP'
       (under "old values present but refuted in place (68) - OK")
```

**R2 — an unrelated arrow.** Same stale sentence, preceded by
`The chain runs SENSOR -> IN-AMP -> ADC with no intermediate buffer.`

```
[test] [old] rc=1 (1 stale)   [mixed] rc=1 (2 stale)   [new] rc=0 PASS
```

**R3 — an unrelated shouted NOT.** Same stale sentence, preceded by
`The rails are NOT drilled at the factory; drill them on the bench.`

```
[test] [old] rc=1 (1 stale)   [mixed] rc=1 (2 stale)   [new] rc=0 PASS
```

**How much of the corpus this shelters.** Measured over the same joined
character stream `check_figures` searches, across all 123 corpus files
(1,196,197 characters):

```
[test] within 300 chars of a bare date / -> / → / NOT ......... 35.5%
[test] NEW exempt region (new vocabulary + NOT, 300-char window) 48.4%
[test] OLD exempt region (old vocabulary, whole line) .......... 33.9%
```

`[calc]` The exemption surface **grew from 33.9% to 48.4% of the corpus**.
The commit message's case for the change is that "23 of 59 exemptions rode on
a bare `was`". On today's corpus, 6 of the new tool's 68 exemptions ride on a
bare date with no correction word and no shouted `NOT` anywhere in the window:

```
[test] chain-connectors 'five connectors must match'  hardware/bom.csv:30                          (2026-09-21)
       chain-connectors 'five connectors must match'  hardware/carrier/bom.csv:6                   (2026-09-21)
       loadswitch-timer 'the reviewers disagree...'   hardware/bom.csv:71                          (2026-09-21)
       loadswitch-timer 'the reviewers disagree...'   hardware/module/umbilical-load-switch/bom.csv:10
       loadswitch-timer '2.4x the ~62ms'              hardware/bom.csv:71
       loadswitch-timer '2.4x the ~62ms'              hardware/module/umbilical-load-switch/bom.csv:10
```

6 of 68 is better than 23 of 59. But the three injections above show the
failure is not rare-in-principle; it is one unrelated date away, in a corpus
where every ADR and every BOM notes cell carries dates by house style.

**What would settle the fix:** require the date/arrow/`NOT` tokens to be
*adjacent* to a correction word (the corpus writes them as
`DECIDED 2026-09-21:`, `2026-09-21: 8HP -> 10HP`,
`*** 2026-09-21 THE PANEL HOLE IS NOT 6.0mm ***`) rather than accepting any of
them standing alone.

### R4 — `check_owners` stopped checking numbers when the value contains a refdes

`[repo] tools/check-staleness.py:864`

```python
toks = sorted(set(idents), key=len, reverse=True)[:2] or \
    sorted(set(nums), key=len, reverse=True)[:1]
```

That is an `or`, not a union. When a figure's value yields an identifier
token, the numeric token is **discarded**, so the owner page is no longer
asked to state the number at all.

Exactly one settled figure is affected, and it is the one this check's
docstring is entirely about:

```
[test] settled figures whose value yields an identifier token:
       spi-series-r -> ['R-SPI-SER'] | value: "100 ohm, R-SPI-SER, qty 3"
```

Injection: in the owner page `hardware/interfaces/spi-link/spi-link.md`,
replace every unglued `100` with the words "one hundred" — i.e. the owner
stops stating its own value, which is precisely the rule-1 breach this check
exists to catch. `R-SPI-SER` is left in place.

```
[test] $ python3 tools/check-staleness.py
  [old]   FAIL 0 shape + 1 owners + 0 links + ...   rc=1
  [mixed] FAIL 0 shape + 1 owners + 0 links + ...   rc=1
  [new]   PASS no live stale values | ...           rc=0
```

Swept across all 24 settled numeric figures (owner file mutated, both token
pickers run in-process against the same tree), the new picker is stronger on
three figures (`cref-out-node`, `loop-budget`, `ferrite-bias-impedance` — the
anchoring fix is real) and weaker on one:

```
[test] figure                     numtoken  old        new
       cref-out-node              100       miss       CATCH
       loop-budget                250       miss       CATCH
       ferrite-bias-impedance     614       miss       CATCH
       spi-series-r               100       CATCH      miss   <== REGRESSION
       (20 others: CATCH / CATCH)
```

`R-SPI-SER` also appears in the BOM, in `circuit.yaml` `depends_on`, and in
three other pages, so it is a far weaker witness to "this page derives 100 Ω"
than `100` is. The fix is one character: `+` instead of `or`.

### R5 — `check_links` stopped seeing every link with a `#anchor`

`[repo] tools/check-staleness.py:903,915`

```python
pat = re.compile(r"\]\(([^)#\s]+)(?:\s+\"[^\"]*\")?\)")
...
tgt = m.group(1).split("#")[0]
```

The character class excludes `#`, so a link written `](page.md#heading)` never
matches the pattern at all — group 1 stops at the `#` and the remainder
`#heading)` fails the `(?:\s+"…")?\)` tail. The `split("#")` on the next line
is dead code that shows the author expected the opposite. The old pattern was
`\]\(([^)#\s]+\.md)[^)]*\)`: the trailing `[^)]*` swallowed the anchor and the
path was checked.

```
[test] injection: [the missing page](../reference/no-such-file-xyz.md#a-heading)
  [old]   FAIL ... 1 links ...   rc=1
  [mixed] FAIL ... 1 links ...   rc=1
  [new]   PASS                   rc=0
```

This is not hypothetical coverage. Counted over the live corpus:

```
[test] inline .md links the OLD regex matched .......................... 159
       links the NEW regex matches (inline any ext + reference style) ... 143
       OLD-matched links the NEW regex no longer matches ................  23
         23 x ](../../README.md#the-interfaces-table)
```

Every one of the 23 circuit pages carries that link. All 23 resolve today, so
nothing is broken — but they are now unguarded, and `README.md#the-interfaces-table`
is the link that a restructure moves. The same restructure that created
`check_links` created these.

Net: the new regex gains reference-style links and non-`.md` targets (both
real wins, R5's sibling test below) and loses 23 anchored ones. Fix: allow
`#` in the path capture and keep the `split("#")` that is already written.

### R6 — `check_links` stopped seeing single-quoted link titles

`[repo] tools/check-staleness.py:903`

The title alternative is `(?:\s+\"[^\"]*\")?` — double quotes only. CommonMark
allows `'…'` and `(…)` too, and the old `[^)]*` tail accepted all of them.

```
[test] injection: [the missing page](../reference/no-such-file-xyz.md 'Title')
  [old]   FAIL ... 1 links ...   rc=1
  [mixed] FAIL ... 1 links ...   rc=1
  [new]   PASS                   rc=0
```

No live corpus link uses this form, so R6 is latent, not active. It is listed
because it is the same defect as R5 in the same regex and the same one-line
fix covers both.

---

## Everything that still works

Injected into both trees; both report. `[test]`, one run per cell.

| Defect class | old | new |
| --- | --- | --- |
| live stale value in prose | FAIL 1 stale | FAIL 1 stale |
| live stale value in a markdown table cell | FAIL 1 stale | FAIL 1 stale |
| live stale value in a CSV notes field (fragment + regenerated master) | FAIL 2 stale | FAIL 2 stale |
| forbidden phrase wrapped across a hard line break | FAIL 1 stale | FAIL 1 stale |
| hand-edited `hardware/bom.csv` (qty changed in the master) | FAIL 1 generated | FAIL 2 generated |
| hand-edited `datasheets/MANIFEST.csv` (notes changed in the master) | FAIL 1 generated | FAIL 34 generated |
| fragment on disk, absent from `ORDER` | FAIL 1 generated | FAIL 2 generated |
| fragment named in `ORDER`, absent from disk | FAIL 1 generated | FAIL 3 generated |
| duplicate refdes claimed by two fragments | FAIL 1 generated | FAIL 2 generated |
| truncated `bom.csv` header | FAIL 1 owners + 1 generated | FAIL 2 generated + 1 bom |
| `circuit.yaml` that will not parse | FAIL 3 deps | FAIL 7 deps |
| `depends_on: circuit:` naming nothing | FAIL 1 deps | FAIL 1 deps |
| `depends_on: refdes:` naming nothing | FAIL 1 deps | FAIL 1 deps |
| `depends_on: fig:` naming nothing | FAIL 1 deps | FAIL 1 deps |
| duplicate `circuit.yaml` id | FAIL 2 deps | FAIL 4 deps |
| broken inline markdown link (plain) | FAIL 1 links | FAIL 1 links |
| dead `§N` section reference | FAIL 1 sections | FAIL 1 sections |
| non-UTF-8 byte in a corpus file | FAIL 1 shape | FAIL 1 shape |
| non-UTF-8 byte in a `bom.csv` fragment | FAIL 1 shape + 11 generated | FAIL 1 shape + 12 generated |
| corpus shrunk below `MIN_CORPUS_FILES` | FAIL 1 shape (41 files) | FAIL 1 shape (41 files) |
| a `TOOL_INPUTS` file moved | FAIL 1 shape, "checks did not run" | FAIL 1 shape, "checks did not run" |
| `verified_against` SHA in no manifest row | FAIL 1 deps | FAIL 1 deps |
| `verified_against` `sha256: BLOCKED` with no `blocked_on` | FAIL 1 deps | FAIL 1 deps |

And nine classes the new tool catches that the old one did not:

| Defect class | old | new |
| --- | --- | --- |
| broken **reference-style** link `[x]: path` | PASS | FAIL 1 links |
| `verified_against` SHA that belongs to a *different* part | PASS | FAIL 1 deps |
| byte-tampered banked PDF | PASS | FAIL 3 datasheets |
| banked PDF deleted from disk | PASS | FAIL 11 datasheets |
| `BLOCKED` manifest row with no `source_url` | PASS | FAIL 2 datasheets |
| an unwired check (`link_problems = [] # check_links(files)`) | PASS | FAIL 1 unwired |
| non-UTF-8 byte under `hardware/**` | **traceback**, rc=1, no PASS/FAIL line | FAIL 1 shape |
| `depends_on` with a typo'd type prefix | not tested (new code path) | reported |
| forbidden pattern containing a literal newline | not reported | reported |

`check-conservation.py` is **purely additive** across this commit
(`[test] diff -u` — head-loss check, multiplicity check, and `head_lost`/
`halved` added to the exit condition; nothing removed). No regression.
`merge-bom.py` is additive (`NO_PARTS` plus the refusal). `merge-manifests.py`,
`verify-datasheets.py` and `rewrite-paths.py` are **byte-identical** across
`0e68f25` (`[test] diff -q`, no output).

---

## Not regressions, but found while testing

**N1 — `WIRE-LOOM` is still exempt, and it is one of the two escapes the
vocabulary change was written to close.**
`[repo] tools/check-staleness.py:84–88` names it:

> `WIRE-LOOM` states a live "five connectors" against a tracked 8, and is
> excused by "rather than starred" 24 characters away.

`rather than` was duly dropped. The row also opens
`DECIDED 2026-09-21:`, and `\d{4}-\d{2}-\d{2}` was duly added, so the escape
survives verbatim — now with a different reason.

```
[test] new tool on HEAD corpus, check_figures():
       ('chain-connectors', '8', 'five connectors must match', 'hardware/bom.csv', 30)  => REFUTED
       ('chain-connectors', '8', 'five connectors must match', 'hardware/carrier/bom.csv', 6) => REFUTED
[repo] hardware/bom.csv:30  "...chained through each cluster board in turn rather than
       starred, so five connectors must match: one on the carrier and one per cluster board."
```

It is in two files because `hardware/bom.csv` is generated from
`hardware/carrier/bom.csv`: one defect, two copies, one edit site.
The sibling escape, `FB-IN`'s `">=1 A"`, **is** closed — its pattern now
matches nothing in the corpus, so the text itself was fixed.

**N2 — the window did not close the BOM-row hole for a dated row.** The window
was introduced because "in `bom.csv` a line is a 2000-word row". Injecting
`The panel is 8HP wide.` immediately after the `2026-09-21` in
`hardware/module/umbilical-load-switch/bom.csv`'s notes cell and regenerating:

```
[test] [mixed] rc=1, but the only finding is the pre-existing spi-series-r one
               (verified with --detail: the injected value is NOT listed)
       [new]   rc=0 PASS
```

Both miss it, for different reasons — old by whole-line vocabulary, new by
window-plus-date. Not a regression; a fix that did not land where it aimed.
Dated markers are the house style for BOM notes, so this is the common shape.

**N3 — `instrument()` does not catch the second shape its own docstring
names.** `[repo] tools/check-staleness.py:936` says both
`link_problems = [] # check_links(files)` and `if False and link_problems:`
"were demonstrated, each giving PASS with a live broken link and
UNWIRED CHECKS = 0". The first is fixed. The second is not — `RAN` records
that the function was *called*, not that its result was *read*:

```
[test] injection: `if link_problems:` -> `if False and link_problems:`, plus a live broken link
  [old] PASS rc=0     [new] PASS rc=0
```

Equal to old, so not a regression, but the new docstring claims otherwise.

**N4 — on the fatal early-return path the hook points the reader at last
run's report.** `main()` writes `.staleness/report.txt` only at the end;
the `TOOL_INPUTS`-missing branch returns before it.

```
[test] clean run  -> .staleness/report.txt = 13251 bytes, first line
                     "corpus: 123 files | bom.csv: 139 rows x 11 cols | figures tracked: 37"
       mv config/figures.yaml; run again
                  -> stdout "FAIL 1 shape | corpus 123 files | checks did not run", rc=1
                  -> .staleness/report.txt = 13251 bytes, SAME first line (untouched)
```

The hook's `additionalContext` then says *"Detail is in .staleness/report.txt
… read it when fixing, do not re-run for detail"* — i.e. it hands the reader a
13 KB report of a clean corpus while the summary says FAIL. Present in the old
tool too, so not a regression; still a fail-open aimed straight at the reader.

**N5 — dead code.** `[repo] tools/check-staleness.py:445–467`: the old
`merge-bom.py`-only fallback sits after an unconditional `return []`. Harmless,
but it reads like a live second branch of `check_bom_generated`.

**N6 — `check_checks` only covers functions inside `check-staleness.py`.**
`check-conservation.py` and `rewrite-paths.py` are wired to nothing at all —
no hook, no caller, no `--check`. Same before and after, so not a regression;
worth noting since "an unwired check" is the class that started all this and
`check-conservation.py` is the tool that proves the splits conserved content.

---

## Runtime, and is the hook still viable?

**Yes, today, with 5.5× of margin — and the shell-outs are not the cost.**

```
[test] $ time python3 tools/check-staleness.py      (3 runs each, wall clock)
       OLD tools, OLD corpus (121 files, 184 patterns) .... 8.73 / 8.64 / 8.64 s
       OLD tools, NEW corpus (123 files, 218 patterns) .... 10.60 / 10.66 s
       NEW tools, NEW corpus (123 files, 218 patterns) .... 11.18 / 11.06 / 11.12 s
```

`[calc]` 8.64 → 11.12 s is +2.48 s, of which **+1.96 s is the corpus and the
register growing** (old tools on the new corpus already cost 10.6 s) and only
**+0.5 s is the rebuild**.

Per-check breakdown of the 11.1 s, measured in-process on the live tree:

```
[test] check_figures        10.51 s
       check_datasheets      0.24 s   <- the new shell-out
       check_bom_generated   0.07 s   <- merge-bom + merge-manifests, both
       check_restated        0.04 s
       check_sections        0.04 s
       load_circuits         0.04 s
       everything else      <0.02 s each
[test] merge-bom.py --check 0.03 s | merge-manifests.py --check 0.03 s
       verify-datasheets.py 0.24 s   | python3 -c pass 0.01 s
```

All three subprocesses together are **0.31 s of 11.1 s**. Adding
`verify-datasheets.py` to the commit path cost 0.24 s and closed three defect
classes; that is the best trade in the commit.

The cost is `check_figures`, which re-reads and re-joins **every corpus file
once per forbidden pattern** — 218 × 123 = 26,814 file reads and 26,814
character-by-character joins per run. It is exactly linear in the pattern
count:

```
[test] real check_figures(), register patterns duplicated in memory:
         218 patterns -> 10.81 s   (0.050 s/pattern)
         436 patterns -> 21.56 s   (0.049 s/pattern)
         654 patterns -> 32.12 s   (0.049 s/pattern)
```

`[calc]` At 0.049 s/pattern the hook's `timeout: 60` is reached at about
**1,220 patterns**, or at 218 patterns with a 5.5× larger corpus. The register
went **184 → 218 patterns (+18%) in this one commit**, and `CLAUDE.md` rule 2
instructs the maintainer to add one pattern per spelling found. This is not
urgent and it is not a regression — but it is the line item that will end the
hook, and the fix is to invert the loops (read each file once, then test all
218 patterns against it), which is a ~40× reduction in I/O and joining.

## The hook itself (`.claude/settings.json`)

The file is **unchanged by `0e68f25`** (`[test] git diff 0e68f25~1 HEAD --
.claude/settings.json` is empty; last touched by `1787905`). Its contract with
the tool still holds. Exercised end to end:

```
[test] o=$(python3 tools/check-staleness.py 2>&1); rc=$?
       s=$(printf "%s" "$o" | grep -E "^(PASS|FAIL)" | head -2 | tr "\n" "; ")
       [ -z "$s" ] && s="CHECKER CRASHED (exit $rc) ..."

  clean          -> "staleness: PASS no live stale values | corpus 123 files, 23 circuits,
                     37 figures / 218 patterns | 5 unresolved (tracked) | 233
                     restated-not-cited (advisory);"                     (146 chars)
  broken link    -> "staleness: FAIL 0 shape + 0 owners + 1 links + 0 sections + 0 deps
                     + 0 generated + 0 register-vs-bom + 0 datasheets + 0 dead-patterns
                     + 0 unwired + 0 stale + 0 bom | corpus 123 ... "    (281 chars)
  figures.yaml gone -> "staleness: FAIL 1 shape | corpus 122 files | checks did not run;"
  raise in main()   -> "staleness: CHECKER CRASHED (exit 1) - no PASS/FAIL line"
```

Findings, all minor:

1. **The grep still works.** Both new summary lines start at column 0 with
   `PASS`/`FAIL`, and the fatal path's problem lines are indented two spaces so
   `head -2` cannot swallow them. No change needed.
2. **The FAIL line went from ~150 to 281 characters**, and the hook emits it
   twice per commit (`systemMessage` + `additionalContext`), so ~600 characters
   of eleven mostly-zero counters. It reads worse than it did. Not a defect.
3. **The FAIL line drops the advisory counts** that the PASS line carries
   (`restated-not-cited`). A run that fails therefore says less about coverage
   than a run that passes, which is backwards.
4. **N4 above** — the hook's "Detail is in `.staleness/report.txt`" instruction
   is wrong on the fatal path, where that file is last run's.
5. `.staleness/` and `.staleness-report.txt` are both in `.gitignore`
   `[repo] .gitignore:1-2`, and `git status` is clean after every run. Good.

## Priority

| # | Regression | Live impact today |
| --- | --- | --- |
| R1–R3 | date / `->` / `NOT` exempt a stale value within 300 chars | **High.** 48.4% of corpus text is inside an exempt window (was 33.9%). Six live exemptions already ride on a bare date. |
| R5 | `](path#anchor)` links unchecked | **Medium.** 23 live links silently dropped out of coverage. |
| R4 | `check_owners` ignores the number when a refdes is present | **Medium.** One figure — `spi-series-r`, the one the docstring is about. |
| R6 | `](path 'Title')` links unchecked | Low. Latent; no corpus link uses it. |

All four fixes are small and local: gate the three new tokens on an adjacent
correction word; `+` instead of `or` at line 864; allow `#` in the link path
capture and accept `'…'` and `(…)` titles at line 903.

## Provenance

`[test]` = injected into a scratchpad tree and run; command and summary line
quoted. `[repo] path:line` = read in the working tree at `HEAD`. `[calc]` =
arithmetic shown. Nothing here is from memory and nothing under
`docs/review/**` was read.
