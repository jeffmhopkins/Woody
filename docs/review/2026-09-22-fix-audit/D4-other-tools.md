# D4 — every tool in `tools/` except `check-staleness.py`

Slice: `check-conservation.py`, `merge-bom.py`, `merge-manifests.py`,
`verify-datasheets.py`, `rewrite-paths.py`. Report only; nothing fixed.

Provenance markers: `[repo] path:line`, `[test]` with the command and its
output, `[calc]` with the arithmetic, `[git]` with the revision. Every
`[test]` was run against `git archive HEAD | tar -x` in a scratch directory,
or a detached worktree, never the corpus.

**Headline.** The two fixes in `0e68f25` are both *correct*; the head/tail
comparison is provably symmetric (D4.1) and the `Counter` check does catch
the halving it was written for. But between them they introduce one new
false-positive class that fires on a formatting-only edit (D4.2), and the
tool still has four ways to read green on a broken split (D4.3–D4.6), one of
which is the repo's own `notes.md` convention. The candidate **seventh
fail-open** is not in `check-conservation.py` at all: it is `msgs[:40]` in
`check_datasheets()`, which drops the real datasheet failures behind
`verify-datasheets.py`'s own "not a failure" advisory block (D4.11).

Findings are numbered D4.n and ordered by tool. Severity: **HIGH** = a green
run on a broken tree, or damage written to disk; **MED** = a check that
fires on a correct change, or a fix that did not land where the reader looks;
**LOW** = latent, cosmetic, or needs a second condition.

---

## `check-conservation.py`

### D4.1 The head comparison IS symmetric with the tail. Verified, not argued. — CORRECT

The fix added `head_lost` next to `tail_lost` `[repo] tools/check-conservation.py:82-84`.

`[calc]` For a single deleted run of `k ≥ 1` words at source position `p` in
a stream of `L` words, the shingle walk breaks the shingles `i ∈
[max(0, p−N+1), min(p+k−1, L−N)]`:

- interior (`p ≥ N−1`, `p+k−1 ≤ L−N`): count `= N+k−1 ≥ N` → classified
  `real`. Always reported.
- near head: count `= p+k`. Hidden (`< N`) **iff** `p+k < N`, i.e. the whole
  deletion lies inside the first `N` words — which is exactly the condition
  under which `was[:N]` is broken, so `head_lost` fires.
- near tail: count `= L−p`. Hidden **iff** `p > L−N`, i.e. the deletion
  starts inside the last `N−1` words — exactly the condition under which
  `was[-N:]` is broken, so `tail_lost` fires.

The two explicit comparisons therefore cover precisely the two regions the
walk cannot, and they cover them identically. `[test]` A 30-case sweep over
the real pitch-stage source (3559 words), deleting 1/3/6/7/8 words at
positions head, head+1, head+4, interior, tail−4, tail:

```
delete  1 word(s) at head      -> rc=1 CAUGHT
delete  6 word(s) at head      -> rc=1 CAUGHT
delete  7 word(s) at head      -> rc=1 CAUGHT
delete  8 word(s) at head      -> rc=1 CAUGHT
delete  1 word(s) at head+1    -> rc=1 CAUGHT
...
delete  8 word(s) at tail-4    -> rc=1 CAUGHT
delete  1 word(s) at tail      -> rc=1 CAUGHT
```

30 of 30 caught, no position or size missed. `[test]` And the reviewer's
original case, on the real split, reproduces the fix:

```
$ python3 tools/check-conservation.py c52ed75~1 \
    hardware/module/pitch-stage/pitch-stage.md t1/pitch-stage.md t1/notes.md t1/sim-README.md
seams (new text inserted between preserved passages): 8
REAL GAPS (source text with no home): 0
  HEAD: the source's first 8 words are not in any destination: Pitch stage — schematic Status: Drawn 2026-09-21. Second
rc=1
```

### D4.2 The `Counter` check fires on a formatting-only change, on a real corpus page — MED

`[repo] tools/check-conservation.py:91-97` compares shingle multiplicity.
`[repo] :103` puts `halved` in the exit expression, so this is a **failure**,
not an advisory.

`[test]` Source = `hardware/cluster/key-marker-and-bits/key-marker-and-bits.md`
at HEAD. The only edit is making one markdown table left-aligned. No word of
prose changes; the diff is one line:

```
33c33
< |---|---|---|---|---|---|---|---|---|---|
> |:--|---|:--|---|:--|---|:--|---|:--|---|
```

```
source ...key-marker-and-bits.md@HEAD: 1216 words
destinations: 1216 words across 1 file(s)
REAL GAPS (source text with no home): 0
  REPEATED PASSAGES THINNED (3): the source states these more times than the destinations do
      4x -> 1x: --- --- --- --- --- --- --- ---
      2x -> 1x: --- --- --- --- --- --- --- right
      2x -> 1x: --- --- --- --- --- --- right thumb
rc=1
```

This is the shape `CLAUDE.md` §2 warns about — "a pattern that fires on a
correct sentence is worse than no pattern, because its cheapest fix is to
make the sentence wrong". Here the cheapest fix is to revert a legitimate
formatting change, or to pad a table back to a shape that satisfies a grep.
`re.sub(r"[`*~_#|>]", " ", ...)` `[repo] :24` strips `|` but not `-`, so a
markdown separator row becomes a run of `---` word tokens and any table of
≥ 8 columns manufactures a repeated 8-gram out of pure furniture.

`[test]` The exposure is corpus-wide, not one page. Scanning
`hardware/**/*.md` + `docs/decisions/*.md` with the tool's own `words()` and
`N=8`: **24 files carry at least one repeated 8-gram.** The repeats include
pure furniture in at least four —

```
hardware/cluster/key-marker-and-bits/key-marker-and-bits.md: 4x  --- --- --- --- --- --- --- ---
hardware/cluster/key-switch-network/key-switch-network.md:   3x  1.5 / 0.5 (absent) 3.15 / 1.35 4.2
hardware/module/breath-receive-stage/breath-receive-stage.md: 2x │ │ ├──[C cm 1.5nF]── AGND(module) │ │
hardware/module/power-entry/power-entry.md:                  3x  module/pitch-stage , module/breath-receive-stage , ...
```

— i.e. table separators, a repeated numeric table row, an ASCII-drawing
gutter line (`│` is U+2502 and is **not** in the furniture class, so drawing
rails survive as words), and a repeated cross-reference list. Any split that
reflows a drawing or renormalises a table on one of those pages now exits 1.

There is no `false_positive_note` equivalent here and no way to exempt a
shingle. Suggested settling: make `halved` advisory (print, do not exit
non-zero) or drop shingles that contain no alphanumeric token.

**Not a false positive on the real splits.** `[test]` Both Phase B splits in
history still pass clean with the new checks:

```
$ python3 tools/check-conservation.py c52ed75~1 hardware/module/pitch-stage/pitch-stage.md <3 dests>
source ...pitch-stage.md@c52ed75~1: 3559 words
destinations: 4414 words across 3 file(s)
seams: 7 | REAL GAPS: 0   rc=0

$ python3 tools/check-conservation.py d88837b~1 hardware/cluster/cluster-boards.md <6 dests>
source ...cluster-boards.md@d88837b~1: 4739 words
destinations: 5848 words across 6 file(s)
seams: 16 | REAL GAPS: 0  rc=0
```

So the fix did not regress the two runs it had to keep green.

### D4.3 The new head check is switched back off by a `notes.md` provenance line — HIGH

The head and tail comparisons ask `sh not in have`, where `have` is the set
of *all* destination shingles `[repo] :36-38`. Any destination text that
happens to reproduce the heading restores it.

This is not a contrived condition — it is this repository's own convention.
`hardware/module/mod-channels/notes.md` carries the 8-gram
`Moved verbatim from Two resistors, not four —` `[test, scan above]`.

`[test]` Delete the H1 *and* the status label from the destination page, then
append one such line to `notes.md`:

```
Moved verbatim from # Pitch stage — schematic  **Status:** Drawn 2026-09-21. Second module page, after
```

```
source ...pitch-stage.md@c52ed75~1: 3559 words
destinations: 4424 words across 3 file(s)
seams (new text inserted between preserved passages): 7
REAL GAPS (source text with no home): 0
rc=0
```

The heading is gone from every page that is meant to carry it, the seam count
is **identical to the clean split (7)**, and rc=0. The `Counter` check does
not save it, because the source states the heading once. The tail check has
the same hole by the same mechanism, so the fix is symmetric in its blindness
as well as in its coverage.

### D4.4 A passage MOVED between destination files is invisible, and so is a wholesale misfile — HIGH (by construction)

The tool concatenates every destination into one word stream `[repo] :32-34`
before building `have`. Nothing is filed *per destination*.

`[test]` Take the real pitch-stage split and swap the whole contents of
`notes.md` and `sim/README.md` — the superseded shelf becomes the sim deck's
contract and vice versa:

```
source ...pitch-stage.md@c52ed75~1: 3559 words
destinations: 4414 words across 3 file(s)
seams: 7 | REAL GAPS: 0
rc=0
```

Byte-for-byte the same verdict as the correct split. `[test]` A single
adjacent-paragraph swap inside one destination:

```
seams (new text inserted between preserved passages): 3
REAL GAPS (source text with no home): 0
rc=0
```

`[test]` A wholesale 59-paragraph shuffle does eventually show — 49 seams and
4 real gaps — but only because shuffling breaks adjacency 49 times, and
"seams" is the counter the report explicitly excuses as benign. There is no
threshold on it and it is not in the exit expression `[repo] :103`.

How bad is this? It is the difference between "no words were lost" and "the
split is correct". `CLAUDE.md` §5 already says the checker cannot see that an
argument survived its own refutation; this is the same class, and the module
docstring's claim that this is "the check a restructure actually needs"
oversells it. A derivation landing on the wrong circuit page — the exact
defect `d88837b` reported for the circuit graph, five edges naming
`module/digital-and-supervision` for nets that come from `module/dac8568`
`[repo] hardware/module/link-supervision/circuit.yaml:4-7` — is invisible
here. A minimum honest fix is one line of output: per-destination word counts,
so a human can see that 0 words landed in `sim/README.md`.

### D4.5 Passing the source as its own destination is a clean pass — MED

`[test]`

```
$ python3 tools/check-conservation.py c52ed75~1 hardware/module/pitch-stage/pitch-stage.md t5/page.md
   # t5/page.md == git show c52ed75~1:hardware/module/pitch-stage/pitch-stage.md
source ...pitch-stage.md@c52ed75~1: 3559 words
destinations: 3559 words across 1 file(s)
seams (new text inserted between preserved passages): 0
REAL GAPS (source text with no home): 0
rc=0
```

Nothing asserts that the destinations differ from the source, that each
destination is non-empty, or that the destination list has no duplicates. A
run against the wrong revision, or against a page that was never actually
split, is indistinguishable from a proven split — including the `0 seams`
that is the strongest-looking result the tool can print.

### D4.6 A source under `N` words is unconditionally green, with every word lost — MED

Both explicit comparisons are guarded by `len(was) >= N` `[repo] :81,83` and
the walk is `while i <= len(was) - N` `[repo] :41`, so below 8 words nothing
runs at all.

`[test]` A 6-word source page, destination discarding all of it:

```
$ python3 tools/check-conservation.py HEAD short.md dest.md    # short.md = "# Panel LED status shelf\n\nSee panel.md.\n"
source short.md@HEAD: 6 words
destinations: 1 words across 1 file(s)
seams: 0 | REAL GAPS: 0
rc=0
```

No corpus page is currently this short, so this is latent. But it is an
unguarded fail-open in the same file as five that were just fixed, and the
cheap fix is to print a refusal rather than a clean summary — the pattern
`verify-datasheets.py` already adopted `[repo] tools/verify-datasheets.py:88-93`.

### D4.7 Is `N=8` right? Yes for the walk; it is the `Counter` check that `N=8` breaks — MED

`[calc]` From D4.1, any interior deletion of `k ≥ 1` words breaks `N+k−1 ≥ N`
shingles, so the `real`/`seam` boundary at `N` is exactly right: a seam
(destination text inserted between two preserved source passages) breaks at
most `N−1 = 7` source shingles, a deletion breaks at least `N = 8`. The
classification is not a heuristic, it is tight, and no other `N` makes it
tighter. `[git]` `d88837b`'s own commit message records the boundary being hit
in practice and solved by restoring adjacency rather than by rewording, which
is the right side of the trade.

Where `N=8` is wrong is the new multiset check: eight words is short enough
that markdown and ASCII-drawing furniture reaches the threshold on 24 corpus
files (D4.2). The two checks want different `N`, and they share one constant.

### D4.8 Nothing runs this tool — MED (completeness)

`[test]` `grep -rln check-conservation` over the corpus (excluding
`docs/review/`, `docs/log/`) returns exactly one file:
`docs/reference/repo-maintenance.md`. It is not in `.claude/settings.json`'s
`PreToolUse` hook `[repo] .claude/settings.json:8-16`, which runs only
`check-staleness.py`, and `check-staleness.py` does not invoke it `[test]
grep -n "conservation" tools/check-staleness.py → no match`. Per `CLAUDE.md`
§5 that is deliberate for a per-commit hook, but "at gates, not per commit"
needs a gate, and there is no file naming the invocation for any split.

---

## `merge-bom.py`

### D4.9 `merge-bom.py` writes the truncated master to disk *before* it reports the problem — HIGH

`[repo] tools/merge-bom.py:196-205`: the `else:` branch writes `MASTER`, and
the `for p in problems: print(...)` loop is after it. `[git] e30d3d8` fixed
exactly this in the sibling tool, and `merge-manifests.py:161-169` now carries
the comment *"PROBLEMS ARE CHECKED BEFORE THE WRITE, not after it. This wrote
the manifest and printed problems thirty lines later, so one bad fragment
header silently dropped that researcher's rows to disk and reported it
afterwards - by which time the damage was on the filesystem."* `merge-bom.py`
was never given the same guard — on the file its own docstring calls "the most
cited file in this repository".

`[test]` Rename one column in one fragment header, then run the tool the way
`repo-maintenance.md` §6 documents:

```
$ python3 tools/merge-bom.py
  hardware/cluster/key-register/bom.csv: header is ['refdes', 'category', ...], expected ['ref', 'category', ...]
bom.csv: wrote 137 rows from 26 fragments | 1 problems
rc=1
$ git diff --stat -- hardware/bom.csv
 hardware/bom.csv | 2 --
```

Two BOM rows are now gone from the generated master, on disk, and the only
notice is a header complaint that does not mention them. The exit code is 1,
so this is recoverable by a careful operator; the sibling tool refuses
instead, and the asymmetry between the two is the finding.

### D4.10 `--check` is byte-exact but proves nothing about the assignment rule: a row moved between ORDER-adjacent fragments is invisible — HIGH

`--check` *is* a real byte comparison — `open(MASTER, encoding="utf-8",
newline="").read()` against `render()`'s output `[repo] :181-192`, no
normalisation on either side, and `render()` passes
`lineterminator="\r\n"` `[repo] :173`. `[test]` The CRLF handling is exact:
every fragment and the master are CRLF (`grep -c $'\r'` equals `wc -l` on
`hardware/bom.csv` 140/140, `hardware/unplaced.csv` 33/33,
`hardware/module/pitch-stage/bom.csv` 10/10), no field anywhere contains an
embedded newline, and a hand edit to the master is caught:

```
$ python3 tools/merge-bom.py --check      # after s/10k 1%/22k 1%/ in the MASTER
  hardware/bom.csv does not match its fragments, first difference at line 15. It is GENERATED - ...
rc=1
```

`ORDER` is also complete and correctly ordered `[test]`: `load()` reports 0
problems, `ORDER ∪ NO_PARTS ⊇ {hardware/**/bom.csv} ∪ {unplaced.csv}`, and
the master's 139 refdes sequence equals the `ORDER`-concatenation exactly
(`[r[0] for r in load()[0]] == master → True`). The shared fragments
(`carrier/`, `cluster/`, `module/`) do sit after their sub-circuits as the
docstring claims.

**The construction `--check` misses.** Because the output is an
order-preserving concatenation, moving a row from the *end* of one fragment to
the *start* of the next fragment in `ORDER` leaves the master byte-identical.
`[test]` `D-CLAMP-BREATH` moved from `hardware/module/breath-receive-stage/bom.csv`
to `hardware/module/breath-output-stage/bom.csv`:

```
$ python3 tools/merge-bom.py --check
bom.csv: checked 139 rows from 26 fragments | 0 problems
rc=0
$ git diff --stat
 hardware/module/breath-output-stage/bom.csv  | 1 +
 hardware/module/breath-receive-stage/bom.csv | 1 -
```

Green, and the commit hook is green with it. The docstring shouts THE
ASSIGNMENT RULE — *"A row lives in the fragment for the circuit WHOSE PAGE
DERIVES ITS VALUE"* `[repo] :17-19` — and nothing checks it. The row now
claims to be derived by a page that does not mention it, which is the input
`check_bom_figures` and `circuit.yaml`'s `refdes:` edges both trust. A check
that would bite: assert every fragment row's refdes appears in that
directory's `.md` page.

Two smaller `--check` blind spots, same run `[test]`:

- an all-empty row appended to a fragment (`,,,,,,,,,,`) → `0 problems`,
  rc=0 (skipped by `if not any(r)` `[repo] :124`);
- fragment header cells given whitespace (`ref , category , part , ...`) →
  `0 problems`, rc=0, because the header is compared stripped `[repo] :121`
  and then re-emitted from the `HDR` constant.

Both are cosmetic; the row move is not.

### D4.10b `NO_PARTS` is justified, and its one entry is honest — CORRECT

`[repo] :44-49` names `hardware/module/link-supervision/bom.csv` only.
`[test]` That directory holds `circuit.yaml`, `link-supervision.md` and
`notes.md` and no `bom.csv`; the page's first line is *"NOT FITTED. Nothing in
this directory is on the board"* and line 5 says *"neither ever had a
`bom.csv` row"* `[repo] hardware/module/link-supervision/link-supervision.md:3-5`.
The two refdeses the page still names resolve elsewhere: `R-CLR-PU` is owned
by `hardware/module/dac8568/bom.csv:2`, whose page derives it `[test] grep`.
So the entry is a decision someone made, not a missing file — which is what
the fix asked for.

One loose end for the BOM slices, not for this one: `LK-CLR`, named on that
page as "the hand assert", has **no** row in any fragment and no row in
`hardware/unplaced.csv` `[test] grep -rn "LK-CLR" hardware/*/*/bom.csv
hardware/*/bom.csv hardware/unplaced.csv → no match`. Either it is not a part
or `unplaced.csv` is missing a row; `merge-bom.py` cannot tell.

### D4.11 `repo-maintenance.md` still says 24 fragments. `0e68f25` made it 26 — MED (completeness)

`[repo] docs/reference/repo-maintenance.md:191` — *"`tools/merge-bom.py`
rebuilds it from 24 per-circuit `bom.csv` fragments."* The tool prints 26 on
every run `[test] "checked 139 rows from 26 fragments"`.

`[git]` The `24` was correct when written: at `d71488e` the tree held 23
circuit fragments plus `hardware/unplaced.csv` = 24. `0e68f25` — the commit
this wave audits — created `hardware/module/digital-and-supervision/bom.csv`
and `hardware/module/panel/bom.csv` (confirmed with
`git log --diff-filter=A -1` on each), taking it to 26, and did not touch the
sentence. This is the named failure mode, in the reference document whose own
§ heading is "The trap", produced by the commit that was fixing the tool.

Two more in the same section that `0e68f25` did not follow
`[repo] docs/reference/repo-maintenance.md:272,276`: "All three are expected
to pass before a commit" and "All three used to fail **open**" both stand
above a code block listing **five** tools and a table of **four** rows; and
the table "What each one refuses to do, and why it now refuses" has no row
for `merge-bom.py`'s silent-skip (fixed in `0e68f25` by `NO_PARTS`) and none
for `check-conservation.py`'s exit-0-on-a-real-gap, head-blindness or
set-vs-multiset fixes. Three fail-opens were closed in the tools and the table
a reader consults to know what the tools guarantee did not move.

---

## `merge-manifests.py` and the ninth fragment

### D4.12 The duplicate-detection guard is keyed on `(part, file)`, so R9's part-string correction bypasses the one report that would have named it — HIGH

`datasheets/.manifest-R9.csv:2` banks `DAC8568ICPW` against
`texas-instruments/DAC8568CIPW.pdf` with the same SHA-256 as
`.manifest-R2.csv:2`, which banks the same file as `DAC8568CIPW`. `.moves.csv`
re-files both onto `analog/DAC8568CIPW.pdf`. The dedup key is
`key = (r[0], r[2])` `[repo] tools/merge-manifests.py:135`, so two different
part strings on one file never collide and the `DE-DUPLICATED` branch
`[repo] :136-149` never runs.

`[test]` The same fragment with the part string left as `DAC8568CIPW` — a true
duplicate — *is* announced:

```
  DE-DUPLICATED: 2 row(s) re-filed onto a path another row already holds, same sha256. ...
        - .manifest-R6.csv:13 WS2815  ->  led/WS2815.pdf
        - .manifest-R9.csv:2 DAC8568CIPW  ->  analog/DAC8568CIPW.pdf
```

As shipped, the only mention of R9's DAC row anywhere in the output is its
contribution to the row count. `[test]` Full run, R9 present vs absent:

```
with R9:     MANIFEST.csv: 101 rows from 9 fragments | 78 ok, 22 blocked, 1 other
without R9:  MANIFEST.csv:  98 rows from 8 fragments | 77 ok, 20 blocked, 1 other
   DE-DUPLICATED: 1 row(s) ...  (identical in both)
```

The guard does not crash and loses nothing — but the one guard that exists for
"two rows, one file" is turned off by a one-column edit, and the tool's
`--check` byte comparison passes `[test] rc=0`.

### D4.13 R9's `SUPERSEDES` declaration is inert: the `declared` rule only looks at `BLOCKED`/`NOT-FETCHED` rows — MED

`[repo] :234-236`: `for r in rows: if r[2] or r[6].upper() not in ("BLOCKED",
"NOT-FETCHED") ... continue`. The row R9 is superseding
(`.manifest-R2.csv:2`) has a file and status `OK`, so it is skipped before the
`"SUPERSEDES" in o[7]` test is ever reached. `[test]` The run prints
`SUPERSEDED (declared): 1 row(s)` and it is the NKK toggle, not the DAC.

R9's note is written exactly the way `:222-226` says a researcher should opt
in — *"SUPERSEDES the part string on the DAC8568CIPW row in
.manifest-R2.csv, which is a TRANSPOSITION"* — and the mechanism does not read
it. The declaration is correct and the tool is deaf to it.

### D4.14 What `MANIFEST.csv` looks like as a result — the un-orderable code sorts first

`[test]` `datasheets/MANIFEST.csv` lines 2–3, sorted by `(file, part)`
`[repo] :151`:

```
2: DAC8568CIPW,Texas Instruments,analog/DAC8568CIPW.pdf,a9b54fef...
3: DAC8568ICPW,Texas Instruments,analog/DAC8568CIPW.pdf,a9b54fef...
```

`"DAC8568CIPW" < "DAC8568ICPW"`, so the **first** DAC row a reader meets is
the transposed code that `docs/decisions/0006-cv-channel-allocation.md:176-178`
says *"appears zero times in SBAS430E"*, carrying no annotation; the
correction and its explanation are on the row below. The BOM cites the right
one (`hardware/module/dac8568/bom.csv:4` and `hardware/bom.csv:77` both say
`DAC8568ICPW`) `[test] grep`, so nothing downstream is wrong — but the
manifest now states a part code the corpus has formally withdrawn, as a live
`OK` row, and per `CLAUDE.md` §3 a banked document is the thing other figures
are supposed to be read off.

`[test]` `file`-bearing rows: 78. Unique files: 76. Two files carry two rows
each (`analog/DAC8568CIPW.pdf`, new with R9; `led/WS2815.pdf`, pre-existing),
so `verify-datasheets.py`'s headline "78 verified" counts rows, hashes those
two files twice, and no longer equals the number of documents banked.

### D4.15 R9 writes the literal string `BLOCKED` into the `sha256` column — LOW

`[test]` Per-fragment scan of file-less rows:

```
.manifest-R1.csv {('BLOCKED', 'sha=empty'): 2}
...
.manifest-R7.csv {('BLOCKED', 'sha=empty'): 4}
.manifest-R9.csv {('BLOCKED', 'sha=BLOCKED'): 2}
```

R9 is the only fragment of nine that puts a non-empty value in `sha256` on a
row with no file; R1–R7 leave it empty. It reaches `MANIFEST.csv` unaltered
(`PESD12VS1UB` and `USBLC6-2SC6`). Nothing validates the column's shape:
`verify-datasheets.py` only reads `sha256` when `file` is non-empty
`[repo] tools/verify-datasheets.py:56-64`, and `merge-manifests.py` only ever
compares it to another row's `[repo] :141`. Harmless today, wrong as a record,
and it is the column any future integrity tool will trust.

### D4.16 `norm()` and `historical` are dead code — the fix they describe never landed — MED

`[repo] :252-268`. `norm()` carries the comment *"Historical-row detection used
exact lowercase equality and under-reported by three"*, `banked` is rebound at
`:261` with the normalised form, `historical` is built at `:262-268` — and
`historical` is never printed, never returned and never in the exit
expression. `[test] grep -n "historical" tools/merge-manifests.py` returns
three lines, all of them inside the block that builds it.

`[test]` Re-running that block by hand against today's `MANIFEST.csv`:
`superseded` (printed) = 10, `historical` (computed, never printed) = 14. The
four extra rows are `2.54mm IDC ribbon socket (mating half)`,
`Gateron KS-33 vendor drawing`, `WS2812B-0807`, `WS2815 LED strip` — which
makes the finding two-sided and worth settling before anyone "fixes" it by
wiring the print: two of those four are precisely the conflations `:213-217`
says the tool must **refuse** (*"WS2812B-0807 against WS2812B-2020 and the
WS2815 strip against the WS2815 IC — different dies and different products"*),
because `norm(a) in b or b in norm(a)` is a substring rule. So either an
intended fix is unlanded, or a rejected experiment was left in the file
wearing a comment that reads like a landed one. Both are defects; the second
is the more dangerous, because the comment invites the wiring.

The guards that **do** still hold, checked: the zero-fragment refusal
`[repo] :22-29`; the `.moves.csv` header, column-count, empty-path,
one-destination and chain refusals `[repo] :57-89`; problems-before-write
`[repo] :161-169`; and `--check` byte comparison `[repo] :153-160`. `[test]`
Baseline run is rc=0 with 23 moves announced.

---

## `verify-datasheets.py` and its new wiring

### D4.17 Its own exit-code semantics are coherent — CORRECT

`[repo] tools/verify-datasheets.py:184` — `sys.exit(1 if (bad or dangling)
else 0)`. `uncovered`, the block printed as *"not a failure, but nothing else
will ever mention them"* `[repo] :148-153`, is correctly **not** in the exit
expression. `[test]` A BOM row for an invented MPN with no manifest row:

```
datasheets: 78 verified, 23 recorded as blocked or not-fetched, 0 problems
  BOM parts with NO manifest row at all (1) - not a failure, but nothing else will ever mention them:
    U-FAKE-PART: LMX9999QDR
rc=0
```

`dangling` *is* in the exit expression and is printed under a heading that
does not claim to be benign. The `REFUSING TO REPORT` path for a missing
`hardware/bom.csv` `[repo] :88-93` exits 1 via `sys.exit(str)`. All three are
self-consistent.

### D4.18 The wiring loses the advisory half, and `msgs[:40]` can drop the real failure entirely — HIGH (latent). Candidate seventh fail-open.

`check_datasheets()` `[repo] tools/check-staleness.py:658-683` returns `[]`
whenever `returncode == 0`, discarding stdout. So the BOM-coverage block —
the one whose whole justification is *"nothing else will ever mention them"* —
is now produced by a machine that throws it away on success. `[test]` With the
invented BOM part above present, `check_datasheets()` returns `[]`. Before the
wiring the tool was run by a human who read the block; after it, the block
reaches nobody unless someone runs the tool by hand. That is a regression in
what gets seen, caused by a fix that is otherwise right.

Worse, on failure the truncation can hide the failure. `verify-datasheets.py`
prints the advisory block *before* the `bad` list `[repo] :148-183`, and
`check_datasheets` keeps only `msgs[:40]` `[repo] tools/check-staleness.py:682`.

`[test]` 45 uncovered BOM parts plus one byte flipped in
`datasheets/analog/OPA2197.pdf`:

```
$ python3 tools/verify-datasheets.py | tail -3
    U-FAKE44: LMX9044QDR
  Clear each by banking the document or adding a BLOCKED row.
  OPA2197IDR: sha256 mismatch on analog/OPA2197.pdf (manifest 27653a7d5e96, file b89a4944f097)
rc=1

$ # what check-staleness actually surfaces
lines returned: 40
LAST line returned:     U-FAKE37: LMX9037QDR
does any returned line mention the sha256 mismatch? False
```

The run still fails — rc is non-zero, so the hook goes red — but the report
names 40 uncovered BOM parts and **never mentions the tampered document**. A
maintainer reading it would bank datasheets until the list emptied and never
find the corrupted file. `[calc]` The advisory block is `1 + 2 + len(uncovered)`
lines ahead of the first `bad` line, so the threshold is
`len(uncovered) ≥ 37`. Today `uncovered` is 0, so this is latent, not live —
but it is guarded by nothing, it grows with the BOM (139 rows against 76
banked documents), and the tampered-PDF case is the exact example
`check_datasheets`'s own docstring gives for why the wiring exists
`[repo] tools/check-staleness.py:663-666`. Same class as the five fail-opens
`0e68f25` closed. Fix: sort `bad` lines first, or filter the advisory block
out by prefix rather than truncating.

`[test]` With one failure and one uncovered part, all four lines come through
verbatim, including the summary line and the sentence that says "not a
failure", presented under the heading *"BANKED DATASHEETS ... which CLAUDE.md
3 requires to pass"* `[repo] tools/check-staleness.py:1037-1041`.

### D4.19 What a green run now means, and one thing it still does not

Wiring it in `[repo] tools/check-staleness.py:668-675` makes a green
`check-staleness.py` newly assert: every `MANIFEST.csv` row's file exists,
is a real PDF where it claims to be, and hashes to its recorded SHA-256; no
artefact sits in `datasheets/` without a row; every `datasheets/…` path cited
from `README.md`, `ROADMAP.md`, `CLAUDE.md`, `hardware/`, `config/`,
`firmware/`, `docs/decisions/`, `docs/reference/` resolves; and
`hardware/bom.csv` exists. `CLAUDE.md` §3's "must pass before committing"
has a mechanism for the first time. It does **not** assert BOM coverage, by
design (D4.17) and now invisibly (D4.18). It also reads the **generated**
`hardware/bom.csv` for coverage rather than the fragments, so coverage is
computed against whatever the master last said; `check_bom_generated`
`[repo] tools/check-staleness.py:281-285` is what keeps that honest, and
`merge-bom.py --check` is wired there as `repo-maintenance.md:196` claims.

---

## `rewrite-paths.py`

### D4.20 `--apply` handles the empty `old` column safely. Tested. — CORRECT

The map is 410 rows `[test]`, `Counter({'unmoved-history': 150, 'unmoved':
104, 'created': 95, 'moved': 29, 'created-history': 28, 'deleted': 4})`. All
123 `created`/`created-history` rows have an empty `old` (`with non-empty
old: 0` for both kinds), and all 4 `deleted` rows have an empty `new`. No row
is short or long, so `r["old"]` is never `None`.

`load_map()` `[repo] tools/rewrite-paths.py:87-95` drops a row on
`if not old or not new or old == new`, *before* the kind test, so every
empty-sided row is excluded structurally rather than by name. `[test]`
`load_map()` returns **29 pairs**, `any(not k for k in pairs) → False` — the
29 `moved` rows exactly, nothing else. An empty string never reaches
`text.replace()`, which would otherwise have inserted the replacement between
every character of every file.

`[test]` On the throwaway copy:

```
$ python3 tools/rewrite-paths.py --apply
apply: 0 file(s) rewritten from 29 mapped moves
rc=0
$ git status --porcelain      # only my own scratch dirs; no tracked file touched
$ python3 tools/rewrite-paths.py --verify
verify: 0 surviving old-side token(s)
```

### D4.21 `--invert` is no longer a valid proof: it reports 112 MISMATCH on a healthy tree, and 92 of them are files the map itself marks `created` — HIGH

`cmd_invert` iterates `invert_targets()` `[repo] :164-176`, which is
`pairs` **plus every tracked rewritable file**, deliberately (*"NOT just the
moved ones"*). It then requires `git show baseline:old` to succeed
`[repo] :181-186`. Any file created after the baseline therefore fails.

`[test]` Against the revision the proof was written for
(`8bb7366`, the A0 parent of A2):

```
$ python3 tools/rewrite-paths.py --invert --baseline 8bb7366
invert: 55 file(s) byte-identical under inversion, 2 hand-edited/skipped, 112 MISMATCH
   # 92 "not present at baseline", 0 "mapped destination does not exist", 20 "inverse differs"
```

`[test]` Attributing the 92: `{new for kind in (created, created-history)}` has
123 entries; **92 of 92** "not present at baseline" lines name one of them,
and none names a path outside the map. The other 31 are excluded upstream —
`created-history` rows live under `docs/review|log|research`, which
`rewritable()` filters `[repo] :123-124`.

So the map now carries, in a `kind` column, exactly the information that would
make the proof re-runnable, and `invert_targets()` does not consult it. Adding
`created`/`created-history` destinations to the skip set would take the run
from 112 mismatches to 20, and those 20 are honest — `[test]` sampling them
shows post-A2 content edits, e.g.
`hardware/module/digital-and-supervision/digital-and-supervision.md` line 15
`was: '## The circuit'` / `now: '## Interfaces'`, which is the `## Interfaces`
section added after A2, not a path defect.

### D4.22 The proof is not reproducible from the repository as it stands, because the map is one mutable dated file — HIGH

`[test]` At the A2 revision with the A2-era map (288 lines), the proof still
reproduces exactly:

```
$ git worktree add --detach <scratch> 8ef7979 && cd <scratch>
$ python3 tools/rewrite-paths.py --invert --baseline 8bb7366
invert: 36 file(s) byte-identical under inversion, 0 hand-edited/skipped, 0 MISMATCH
```

`[test]` The same tree, with **today's** map and today's tool dropped in:

```
  datasheets/led/WS2812C.pdf: mapped destination does not exist
  datasheets/analog/LT5400.pdf: mapped destination does not exist
  datasheets/led/WS2815.pdf: mapped destination does not exist
invert: 34 file(s) byte-identical under inversion, 2 hand-edited/skipped, 21 MISMATCH
```

21 of the 29 `moved` rows are datasheet re-filings whose own `note` column
says *"datasheet re-filing (b631987), AFTER this map was first written"*
`[repo] docs/reference/path-map-2026-09-21.csv`, and `b631987` is well after
`8ef7979`. `cmd_invert` requires every mapped destination to exist on disk
`[repo] :187-189`, so the map has outgrown the revision its proof covers.

`0 MISMATCH` is therefore a result that can only be obtained by checking out
the A2-era map alongside the A2-era tree. Nothing in
`docs/reference/repo-maintenance.md:372-378` says so; it presents
`--invert --baseline <rev>` as a standing proof, and describes it as applying
"the inverse rewrite to every moved file" — which is not what the tool does
(D4.21) and is the reason it now fails. The honest options are to pin the
proof to its revision pair in writing, or to freeze an `A2` copy of the map
beside the live one.

### D4.23 `unrewrite()` orders by `len(old)`, not `len(new)` — LOW

`rewrite()` applies longest-`old` first `[repo] :96-99`, correctly.
`unrewrite()` claims to be "the mirror" and applies
`reversed(list(pairs.items()))` `[repo] :101-105`, i.e. shortest-`old` first —
but it is substituting on the **new** side, so the ordering it needs is by
`len(new)`. `[calc]` The 29 current pairs are all prefix-directory moves with
equal-length or near-equal-length sides and no `new` that is a substring of
another `new`, so no ordering error is reachable today; I could not construct
a failing case from the live map. It is a latent correctness bug in the
proof's own inverse, worth one line of `sorted(..., key=lambda kv:
-len(kv[1]))`.

---

## Summary table

| # | Tool | Finding | Sev |
|---|---|---|---|
| D4.1 | check-conservation | head/tail comparison is symmetric and complete for end deletions — **the fix is correct** | — |
| D4.2 | check-conservation | `Counter` check exits 1 on a table-alignment-only edit; 24 corpus files carry repeated 8-grams | MED |
| D4.3 | check-conservation | head check defeated by a `notes.md` "Moved verbatim from …" provenance line; rc=0, seams unchanged | HIGH |
| D4.4 | check-conservation | passage moved between destinations, or destinations swapped wholesale, is invisible; rc=0 | HIGH |
| D4.5 | check-conservation | source passed as its own destination → `0 seams`, rc=0 | MED |
| D4.6 | check-conservation | source under 8 words → total loss reads green | MED |
| D4.7 | check-conservation | `N=8` is tight for the walk and too short for the multiset check; one constant, two needs | MED |
| D4.8 | check-conservation | not invoked by any hook, check or documented gate | MED |
| D4.9 | merge-bom | writes the truncated master to disk before reporting problems — the bug `e30d3d8` fixed in the sibling tool | HIGH |
| D4.10 | merge-bom | `--check` is byte-exact but blind to a row moved between ORDER-adjacent fragments; THE ASSIGNMENT RULE is unenforced | HIGH |
| D4.10b | merge-bom | `NO_PARTS` entry verified honest; `LK-CLR` has no BOM row anywhere (for the BOM slices) | — |
| D4.11 | merge-bom | `repo-maintenance.md:191` says 24 fragments; `0e68f25` made it 26. Plus "All three" over five tools, and no table row for the fixes | MED |
| D4.12 | merge-manifests | dedup guard keyed `(part, file)`; R9's part-string edit turns off the only report that names a two-row file | HIGH |
| D4.13 | merge-manifests | R9's `SUPERSEDES` is inert — `declared` only reads BLOCKED/NOT-FETCHED rows | MED |
| D4.14 | merge-manifests | `MANIFEST.csv:2` is now the withdrawn `DAC8568CIPW` code, unannotated, sorting above its correction | MED |
| D4.15 | merge-manifests | R9 writes `BLOCKED` into the `sha256` column; nothing validates the column | LOW |
| D4.16 | merge-manifests | `norm()`/`historical` dead code: would report 14 vs 10, and two of the extras are the conflations the file forbids | MED |
| D4.17 | verify-datasheets | exit-code semantics coherent: `uncovered` is not in the exit expression — **correct** | — |
| D4.18 | verify-datasheets | wiring discards the advisory block on success, and `msgs[:40]` hides real failures behind ≥37 advisory lines | HIGH (latent) |
| D4.19 | verify-datasheets | what a green run now means, and that BOM coverage is not part of it | — |
| D4.20 | rewrite-paths | `--apply` safe with the empty `old` column: 29 pairs from 410 rows, 0 files touched — **correct** | — |
| D4.21 | rewrite-paths | `--invert` reports 112 MISMATCH on a healthy tree; 92/92 are map-`created` rows the tool does not consult | HIGH |
| D4.22 | rewrite-paths | the proof is not reproducible: today's map gives 21 MISMATCH on the A2 tree that scored 0 | HIGH |
| D4.23 | rewrite-paths | `unrewrite()` orders by `len(old)` while substituting on `new` | LOW |

## What would settle the uncertain ones

- **D4.4** — is per-destination filing in scope for this tool, or is it
  `circuit.yaml`'s job? The docstring says "must survive somewhere in the
  destination files", which is honest; the module docstring's "the check a
  restructure actually needs" is what oversells it. A one-line output change
  (per-destination word counts) settles it cheaply either way.
- **D4.16** — whether `historical` is an unlanded fix or an abandoned
  experiment. The author knows; the file does not say. Do not wire the print
  without reading `:213-217` first.
- **D4.18** — latent on `len(uncovered) ≥ 37`, which is 0 today. Someone
  should decide whether that is a bug to fix now or a note to leave.
- **D4.23** — I could not construct a failing case from the 29 live pairs.
  Treat as latent unless the map gains a `new` that is a substring of another
  `new`.
