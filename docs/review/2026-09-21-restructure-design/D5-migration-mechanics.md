# D5 — Migration mechanics: every path reference, and what must not be fixed

**Agent D5, cold.** Slice: the project's named failure mode (a value changes,
derived statements do not follow) with *every path in the repository* as the
value. Deliverable is an executable checklist, not an essay.

**Provenance:** every claim is marked `[repo]` with path:line, `[cmd]` with the
command that produced the number, `[calc]` with the arithmetic, or `[test]`
where I reproduced a failure in a throwaway copy of the tree. Baseline is
`f94e91d` with a clean working tree `[cmd] git status --porcelain` → empty.

**Target layout is not known to me.** The cold rule bars me from reading
`docs/review/**`, including this wave's `README.md`, so I do not know what the
new tree looks like. Everything below is therefore written *parametric on a
rename map* — a file `MAP` of `old,new` pairs — rather than against a specific
destination. That is the right shape anyway: §4 and §5 turn the map into the
single source of truth that the rewrite, the verification and the historical
record all derive from, which is the one structural defence against this
repo's failure mode.

---

## 0. The three findings that change the plan

Read these before the inventory; they reorder the work.

### 0.1 `check-staleness.py` FAILS OPEN on a moved corpus directory

`CORPUS_DIRS` is a hardcoded list `[repo] tools/check-staleness.py:30` and
`corpus_files()` walks each with `os.walk` `[repo] tools/check-staleness.py:47`.
`os.walk` on a directory that does not exist yields **nothing, silently**.

`[test]` In a `git archive HEAD` copy, `mv docs/decisions docs/adr`, then
`python3 tools/check-staleness.py --detail`:

```
corpus: 18 files | bom.csv: 138 rows x 11 cols | figures tracked: 33
PASS no live stale values | 5 unresolved (tracked)          exit=0
```

Baseline is `corpus: 33 files`. **Fifteen files left the corpus and the checker
printed PASS.** `[calc] 33 − 18 = 15`. Simulating the hook's own shell on that
state gives `systemMessage: [staleness: PASS no live stale values | 5
unresolved (tracked);]` — green.

This is the project's failure mode committed *by the tool that exists to
prevent it*. During a restructure it is the single most dangerous thing in the
repo, because the move is exactly the operation that triggers it.

**Mitigation is mandatory and goes in first (see §7.2): a file-count floor.**

### 0.2 `merge-manifests.py` silently destroys `MANIFEST.csv` if the fragments move

`[repo] tools/merge-manifests.py:14` globs `ROOT/datasheets/.manifest-R*.csv`;
`:44` unconditionally overwrites `ROOT/datasheets/MANIFEST.csv` with whatever
it found. Zero fragments → a header-only file, **exit 0**.

`[test]` Same copy, fragments moved to `datasheets/fragments/`, then
`python3 tools/merge-manifests.py`:

```
MANIFEST.csv: 0 rows from 0 fragments | 0 ok, 0 blocked, 0 other   exit=0
```

`MANIFEST.csv` went from 99 lines to 1 `[cmd] wc -l < datasheets/MANIFEST.csv`.
98 rows of SHA-256 provenance gone, exit code clean. `verify-datasheets.py`
does catch it afterwards (`77 problems`) but only if someone runs it, and by
then the destruction is staged.

**Compounding trap:** the eight fragments are **dotfiles**. `[test]`
`mv a/* b/` leaves `.manifest-R1.csv` behind — a plain `*` glob does not match
them. A mover who writes `git mv datasheets/* refs/datasheets/` moves
`MANIFEST.csv` and the PDFs and silently leaves all eight fragments plus
nothing else behind, and the very next `merge-manifests.py` run empties the
manifest. The same trap applies to the eight `.gitkeep` files
`[cmd] git ls-files | grep gitkeep`.

**Rule: move directories whole (`git mv datasheets refs/datasheets`), never
their globbed contents.**

### 0.3 `check_refdes` is dead code — and its `hardware/` assumption still needs fixing

`[repo] tools/check-staleness.py:126` defines `check_refdes(files, bom_refs)`,
whose first act is `if not rel.startswith("hardware/")` at `:132`. `[cmd] grep
-n 'check_refdes' tools/check-staleness.py` → one hit, the definition.
`main()` at `:160-162` calls only `corpus_files`, `check_figures`, `check_bom`;
`bom_refs` is bound and discarded.

So the "schematic refdes with no BOM row" check has **never run**. The brief
lists the `hardware/` prefix as something to fix on the move — correct, and it
must be fixed, because whoever wires the function up later inherits the stale
prefix silently. But note in the Phase A commit message that the check is inert
today, so nobody mistakes "it passes" for "it was checked."

---

## 1. The full inventory of path references

Scope note: **"corpus"** = `hardware/**`, `docs/decisions/**`,
`docs/reference/**`, `config/**`, `firmware/**`, `README.md`, `ROADMAP.md`
`[repo] CLAUDE.md:83-85`, `[repo] docs/reference/repo-maintenance.md:15`.
**"history"** = `docs/review/**`, `docs/log/**`, `docs/research/**`
`[repo] CLAUDE.md:77-81`. 36 tracked corpus files, of which the checker scans
33 (the three `.gitkeep` are skipped by the extension filter at
`[repo] tools/check-staleness.py:57`).

### 1.1 Master tally

| # | Category | Count | Where |
|---|---|---|---|
| A | `owner:` paths in `config/figures.yaml` | **33** | §1.2 |
| B | Other repo-path tokens in `config/figures.yaml` | **25** | §1.2 |
| C | Markdown links `](...md)` in the corpus | **52** | §1.3 |
| D | Markdown links to non-`.md` targets in the corpus | **7** | §1.3 |
| E | Backticked explicit paths (contain `/`) in the corpus | **78** | §1.4 |
| F | Backticked **bare filenames** in the corpus | **143** | §1.5 |
| G | Repo-path tokens in `hardware/bom.csv` (all in `notes`) | **53** | §1.6 |
| H | Hardcoded paths in `tools/*.py` | **18** | §1.7 |
| I | `file`-column paths in `datasheets/MANIFEST.csv` | **77** | §1.8 |
| J | `file`-column paths in the 8 `.manifest-R*.csv` fragments | **77** | §1.8 |
| K | `$CLAUDE_PROJECT_DIR` paths in `.claude/settings.json` | **2** | §1.9 |
| L | Repository-layout tree block in `README.md` | **9 lines** | §1.10 |
| M | `pcb/` future-layout paths in `docs/reference/pcb-pipeline.md` | **4** | §1.11 |
| N | `.gitignore` patterns | **5** (0 path-bound) | §1.12 |
| O | Repo-path tokens in `CLAUDE.md` | **23** | §1.13 |
| P | Repo-path tokens in `datasheets/README.md` | **5** | §1.13 |
| Q | `ADR 0NNN` **name**-references in the corpus | **509** | §1.14 |
| R | `<file>.md §N` section references in the corpus | **10** | §1.15 |
| S | Everything in `docs/review,log,research` — **DO NOT FIX** | **7 837+** | §3 |

Categories overlap by construction (a backticked markdown link is in both C
and E; figures.yaml `owner:` values are in both A and the 58-token total). The
overlaps are deliberate: each row is a *grep you must run*, not a disjoint
partition. The one number that is a true total of non-history repo-path tokens
is **346** `[cmd]` in §1.16.

### 1.2 `config/figures.yaml` — 58 repo-path tokens, only 33 of them `owner:`

```sh
grep -c '^\s*owner:' config/figures.yaml                      # 33
```

Distribution `[cmd] grep -o '^\s*owner:.*' config/figures.yaml | sed 's/^\s*owner:\s*//' | sort | uniq -c | sort -rn`:

```
6 hardware/module/power-entry.md          2 hardware/module/pitch-stage.md
4 hardware/controller/carrier.md          2 docs/decisions/0003-breath-sensing-path.md
4 hardware/bom.csv                        2 config/key-layout.yaml
3 hardware/controller/cluster-boards.md   1 hardware/module/mod-channels.md
3 docs/decisions/0004-cv-interface-module.md   1 hardware/module/breath-receive-stage.md
                                          1 docs/reference/latency-budget.md
                                          1 docs/reference/ks33-geometry.md
                                          1 docs/decisions/0014-lighting.md
                                          1 docs/decisions/0005-power-architecture.md
                                          1 docs/decisions/0001-mcu-and-board-partitioning.md
```

**`owner:` is 33 of 58.** The other 25 are buried in free-text fields —
`derivation`, `note`, `provenance_note`, `blocked_on`, `candidates`,
`decided_by`, `false_positive_note`, `threshold_note`, `floor`,
`caught_late_note`, `supersedes_the_constraint` — which
`[repo] docs/reference/repo-maintenance.md:159-164` documents as "all free
text". A rewrite that walks the YAML and touches only the `owner:` key misses
43% of the file's path references. `[calc] 25/58 = 43%`.

```sh
grep -cE '(hardware|docs|config|firmware|tools|datasheets|mechanical)/[A-Za-z0-9_.*/-]+' config/figures.yaml
```

Named examples, all `[repo]`:

- `:305` `docs/decisions/0004-cv-interface-module.md:627` — **a path with a
  line number**. Phase B will invalidate the line number even if Phase A keeps
  the path. Nothing can rewrite this mechanically; it is flagged for a human in
  §2.7.
- `:286`, `:324` `docs/review/2026-09-21-preflight/A4-carrier.md` — the corpus
  citing history. Legitimate; stays valid only if history does not move (§3.4).
- `:310` "`power-entry.md` states that ADR 0004 was corrected on this point. IT
  WAS NOT" — a bare filename inside prose that also names an ADR by number.
- `:397` `blocked_on: "datasheets/MANIFEST.csv - WS2812B-0807"`.

### 1.3 Markdown links — 52 `.md` + 7 other

```sh
grep -rnoE '\]\([^)]*\.md[^)]*\)' --include='*.md' \
  hardware docs/decisions docs/reference config firmware README.md ROADMAP.md | wc -l   # 52
```

By form `[cmd]` three greps, and they reconcile: `[calc] 19 + 24 + 9 = 52`.

| Form | Count | Command | Rewrite difficulty |
|---|---|---|---|
| Relative, `../`-prefixed | **19** | `grep -rnoE '\]\(\.\./[^)]*\)' …` | **Hard** — depends on both endpoints |
| Bare filename, no slash | **24** | `grep -rnoE '\]\([^)/]*\.md\)' …` | **Hard** — depends on both endpoints |
| Root-relative | **9** (+1 dir link) | `grep -rnoE '\]\((hardware\|docs\|config\|firmware\|datasheets\|mechanical\|tools)/[^)]*\)' …` | **Easy** — map lookup |

Only **9 of 52** are mechanically safe. The other 43 are *sibling-relative* and
break when either endpoint moves, including when only the *source* moves and
the target does not.

Concentration `[cmd] … | awk -F: '{print $1}' | sort | uniq -c | sort -rn`:
`docs/decisions/README.md` 15, `firmware/README.md` 9, `ROADMAP.md` 6,
`README.md` 5, `docs/decisions/0006-cv-channel-allocation.md` 4, then eight
files with 1–2 each. **Four files hold 35 of the 52** `[calc] 15+9+6+5 = 35`.

Non-`.md` targets, 7: three `https://` (do not touch), `LICENSE` ×1,
`docs/decisions/` (a directory link, `README.md:110`), and 2 more `ROADMAP.md`
self-links `[cmd] grep -rnoE '\]\([^)#][^)]*\)' … | wc -l` → 74 total, minus 52
`.md`, minus 15 further web/anchor forms.

**Zero section anchors** `[cmd] grep -rnoE '\]\([^)]*#[^)]*\)' --include='*.md'
<corpus> | wc -l` → 0. Good news: no `](file.md#heading)` links exist, so
Phase B's content splits cannot break an anchor link. They *can* break the ten
`§N` prose references (§1.15).

### 1.4 Backticked explicit paths — 78 occurrences, 42 distinct

Method (reproducible script, §1.16): tokenise inside backticks, keep tokens
containing `/` and a lowercase extension.

Top of the list, all corpus-zone: `firmware/README.md` 10,
`config/key-layout.yaml` 6, `hardware/module/breath-receive-stage.md` 5,
`config/figures.yaml` 5, `hardware/controller/cluster-boards.md` 3,
`hardware/bom.csv` 3, then 36 tokens at 1–2.

**Five of the 42 are not repo paths at all and must not be rewritten:**

| Token | Where | What it is |
|---|---|---|
| `src/owp/owp.ino` | `0003:`, `0011:` | the **previous project's** file |
| `IansLibrary.pretty/gateron-ks27.kicad_mod` | `ks33-geometry.md` | a third-party library |
| `pcb/src/module/*.py` | `pcb-pipeline.md:115` | a layout that does not exist yet |
| `pcb/module/module.kicad_pcb` | `pcb-pipeline.md:179` | ditto |
| `.../pins.c` | `carrier.md` | an elided path |

A rewriter that resolves "token that looks like a path" against the map and
warns on misses will flag these five every run. Put them in an explicit
allow-list in the rewriter, not in a reviewer's head.

### 1.5 Backticked bare filenames — 143 occurrences, 26 distinct. **This is the dangerous category.**

| Bare name | Count | Sources `[cmd]` §1.16 |
|---|---|---|
| `bom.csv` | **51** | carrier 15, cluster-boards 9, power-entry 8, digital-and-supervision 6, +8 more files |
| `key-layout.yaml` | 14 | cluster-boards 12, carrier 2 |
| `power-entry.md` | **10** | 0004 ×3, pcb-pipeline ×3, 0006 ×2, carrier ×2 |
| `carrier.md` | 9 | cluster-boards 6, 0004 ×2, digital-and-supervision 1 |
| `breath-receive-stage.md` | 7 | carrier 3, +4 files |
| `mod-channels.md` | 6 | 0006 ×4, firmware/README 1, pitch-stage 1 |
| `breath-output-stage.md`, `ROADMAP.md`, `ks33-geometry.md`, `digital-and-supervision.md` | 4 each | |
| `LICENSE`, `pitch-stage.md`, `check-staleness.py`, `MANIFEST.csv`, `74HC165-nexperia.pdf` | 3 each | |
| `README.md`, `cluster-boards.md`, `CLAUDE.md`, `latency-budget.md` | 2 each | |
| `verify-datasheets.py`, `R10-keyscan-and-adc.md`, `D2-missing-testability.md`, `74HC165-toshiba.pdf`, `74HC165-onsemi.pdf`, `GATERON-KS-33-3D.step`, `LT1641-DC1354A-demo-manual.pdf` | 1 each | |

`power-entry.md` at exactly 10 confirms my extraction matches the brief's.

**Two of these are already ambiguous today** `[cmd] git ls-files | xargs -n1
basename | sort | uniq -d`:

```
.gitkeep     8      README.md   12      VERIFIED.md   6
```

`README.md` ×12 means the two corpus occurrences of bare `` `README.md` ``
(`0011-licensing.md`, `repo-maintenance.md`) already cannot be resolved by name
alone. `VERIFIED.md` ×6 is cited bare from `CLAUDE.md:92`.

**Two more are cross-zone references the corpus makes into history:**
`R10-keyscan-and-adc.md` and `D2-missing-testability.md`, both from
`hardware/controller/carrier.md`. A bare-name rewrite that resolves against the
whole repo will happily rewrite these into history paths; see §3.3.

### 1.6 `hardware/bom.csv` — 53 repo-path tokens, all in one column

```sh
python3 - <<'EOF'
import csv,re,collections
rows=list(csv.reader(open('hardware/bom.csv',newline='',encoding='utf-8')))
hdr=rows[0]; c=collections.Counter()
for r in rows[1:]:
    for i,cell in enumerate(r):
        c[hdr[i]]+=len(re.findall(r'(?:datasheets|hardware|docs|config|firmware|tools)/[A-Za-z0-9_./-]+',cell))
print(dict(c))    # {'notes': 50}   (+3 bare CLAUDE.md refs → 53 by the §1.16 scanner)
EOF
```

138 rows × 11 columns, CRLF `[repo] docs/reference/repo-maintenance.md:126-136`.
All path tokens are inside `notes`, which is free prose and append-only by
convention `[repo] :139-141`. **There is no path column to rewrite; it is 50
prose edits inside a CRLF CSV.**

`[repo] hardware/bom.csv:97` (row `F-CHAIN`) cites
`datasheets/discrete-and-power/MF-PSMF010X.pdf`. The file on disk is
`MF-PSMF010X-polyfuse.pdf` `[cmd] ls datasheets/discrete-and-power/ | grep -i
psmf`. **This link is broken today, before any move.** It is the only
pre-existing broken repo-path reference in the non-history tree
`[cmd]` §1.16 broken-link scan → 1 real hit (the other nine hits are my
regex truncating `.kicad_mod`/`.manifest-R*` and are false).

Record it in the Phase A baseline (§5.1) so the move does not get blamed for
it, and fix it in a **separate commit before or after** Phase A — never inside
it, because Phase A changes no content (§5).

### 1.7 `tools/*.py` — 18 hardcoded path tokens

`[cmd] grep -nE '"[^"]*(hardware|docs/|config|firmware|datasheets|tools|README|ROADMAP|MANIFEST|manifest|\.staleness|bom)[^"]*"' tools/*.py`

**`tools/check-staleness.py`** (11)

| Line | Literal | Note |
|---|---|---|
| 20 | `ROOT = dirname(dirname(abspath(__file__)))` | **assumes the tool is exactly one level below the repo root** |
| 23, 25 | `.staleness`, `.staleness/report.txt` | must match `.gitignore:1` and `repo-maintenance.md:20` |
| 30 | `CORPUS_DIRS = ["hardware","docs/decisions","docs/reference","config","firmware"]` | **fails open** — §0.1 |
| 31 | `CORPUS_FILES = ["README.md","ROADMAP.md"]` | missing file is skipped silently at `:39-41` |
| 32 | `EXCLUDE = ("docs/review","docs/log","docs/research")` | §3 depends on this |
| 62, 68 | `config/figures.yaml` ×2 | crashes loudly if moved `[test]` |
| 112 | `hardware/bom.csv` | crashes loudly if moved `[test]` |
| 132 | `rel.startswith("hardware/")` | inert today — §0.3 |
| 215 | `.staleness/report.txt` in the user-facing string | |

**`tools/verify-datasheets.py`** (3+): `:19` `DS = ROOT/"datasheets"`,
`:26` `DS/"MANIFEST.csv"`, `:76` `rel in ("MANIFEST.csv","README.md")`,
`:92` `ROOT/"hardware/bom.csv"`, plus `datasheets/README.md` in the docstring
`:14`. Note `:92` guards with `if os.path.exists(bom)` — so **moving
`bom.csv` silently disables the BOM-coverage check** (26 uncovered parts would
stop being reported). Second fail-open, smaller than §0.1 but the same shape.

**`tools/merge-manifests.py`** (4): `:14` fragment glob, `:32-33` the
`datasheets/`-prefix strip, `:44` output path, `:139` the same glob repeated
inline. §0.2.

### 1.8 `datasheets/MANIFEST.csv` and the 8 fragments — 77 + 77 path cells

```sh
python3 -c "
import csv,glob
t=p=0
for f in sorted(glob.glob('datasheets/.manifest-R*.csv')):
    k=[r for r in list(csv.reader(open(f,newline='',encoding='utf-8')))[1:] if len(r)>2 and r[2].strip()]
    t+=len(k); p+=sum(1 for r in k if r[2].strip().startswith('datasheets/'))
print('file cells:',t,'| carrying the datasheets/ prefix:',p)"   # 77 | 33
```

`MANIFEST.csv`: 98 rows, 77 with a `file` value, 21 `BLOCKED`/`NOT-FETCHED`
with none `[cmd]` above. Directory spread: `connectors` 22,
`discrete-and-power` 18, `mechanical` 16, `other-semi` 15,
`texas-instruments` 6.

Fragment row counts `[cmd] for f in datasheets/.manifest-R*.csv; do …`:
R1 2, R2 6, R3 10, R4 13, R5 15, R6 18, R7 32, R8 2 — **98 total, matching**
`[calc] 2+6+10+13+15+18+32+2 = 98`.

**The convention that will trip a rewriter:** `MANIFEST.csv`'s `file` column is
relative to `datasheets/`, **not** to the repo root. `[repo]
tools/merge-manifests.py:26-33` documents exactly this and normalises it —
fragments wrote both spellings and **33 of 77 cells still carry the
`datasheets/` prefix in the fragments**, which the tool strips on merge.

Consequence: the same artefact is spelled two ways depending on which file you
are reading, and one of those spellings collides with a real top-level
directory. `[repo] datasheets/MANIFEST.csv` contains
`mechanical/GATERON-KS-33-3D.step`, `mechanical/WS2815-worldsemi-datasheet.pdf`
and twelve more `mechanical/…` cells — while `mechanical/` at the repo root is
a real directory holding `cad/`, `drawings/`, `export/`
`[cmd] ls -R mechanical/`. **A rewriter given the whole-repo path map and
pointed at `MANIFEST.csv` will resolve `mechanical/…` against the wrong root.**
See §2.5.

The same collision has already leaked upward: `[repo] config/figures.yaml:195`
writes `mechanical/EURORACK-3U-3HP-PANEL-apfaudio-pmod-r3.1.kicad_pcb` and
`mechanical/EURORACK-3U-PANEL-HP-TABLE-make_blanks.py` — manifest-relative
spellings sitting in a file whose convention is root-relative. Neither resolves
from the repo root today.

A third collision is latent: `hardware/datasheets/` exists as an empty tracked
directory `[cmd] git ls-files | grep gitkeep` → `hardware/datasheets/.gitkeep`,
alongside top-level `datasheets/`. Three plausible roots for the token
`datasheets/…`.

### 1.9 `.claude/settings.json` — 2 paths

`[cmd] grep -oE '\$CLAUDE_PROJECT_DIR/[A-Za-z0-9_./-]+' .claude/settings.json`

```
$CLAUDE_PROJECT_DIR/tools/check-staleness.py
$CLAUDE_PROJECT_DIR/.staleness-report.txt
```

Both `[repo] .claude/settings.json:10`. The `if` clause is
`"Bash(git commit *)"` and `matcher` is `"Bash"`. See §7.

### 1.10 `README.md` repository-layout tree — 9 lines, already stale

`[repo] README.md:95-105`:

```
docs/decisions/   docs/log/   docs/reference/   docs/research/
hardware/         firmware/   mechanical/       config/   tools/
```

**`datasheets/` is absent** from a block that claims to be the repository
layout — a directory holding 77 banked artefacts and the MANIFEST. So is
`docs/review/`. `[cmd] ls -d */` vs the block. This block is a derived
statement that did not follow when `datasheets/` was created: the project's
named failure mode, in the file a new reader opens first.

The block is prose in a fenced code block, so no tool validates it. **Phase A
must rewrite it and Phase A's hand-check must diff it against `ls -d */`**
(§5.3). Do not silently fold the `datasheets/` fix into Phase A's no-content
rule — it is a content change; land it in the same *separate* commit as §1.6's
broken link.

Also at `[repo] README.md:15,89,90,109,110,111,117`: 7 markdown links, and
**two contradictory Licence sections** (`:83-91` "Three share-alike licences"
vs `:114-118` "Not yet decided"). The second is out of my slice — flagging it
for whichever agent owns ADR consistency, since a restructure that keeps both
propagates the contradiction into the new tree.

### 1.11 `docs/reference/pcb-pipeline.md` — 4 future-layout paths

`[repo] :115` `pcb/src/module/*.py`, "one module per schematic page,
`module.py` importing the six"; `:116` emits `module.net`; `:155`
`build_board.py`; `:179` `pcb/module/module.kicad_pcb`.

`pcb/` does not exist `[cmd] ls -d pcb 2>&1` → no such file. This is a
*planned* layout, and **"one module per schematic page ... importing the six"
is a count-coupling to `hardware/module/*.md`**, which today holds exactly six
pages `[cmd] git ls-files hardware/module/*.md | wc -l` → 6.

Phase B splits content. **If Phase B turns six schematic pages into seven, this
sentence is stale and no grep finds it** — it is the `mod-channels.md`
watchdog case from `[repo] CLAUDE.md:71-73` exactly. Put it on the Phase B exit
list (§6.4), not the Phase A one.

`pcb-pipeline.md` also holds 3 of the 10 bare `power-entry.md` references
(`:95`, `:130`, `:246`) and `:4` cites `docs/review/2026-09-21-pcb-pipeline-review/`.

### 1.12 `.gitignore` — 5 patterns, none path-bound

`[repo] .gitignore` at `f94e91d`: `.staleness/`, `.staleness-report.txt`,
`*.tmp`, `__pycache__/`, `*.py[cod]`.

`.staleness/` and `.staleness-report.txt` are **anchored to the repo root by
the leading-slash-free-but-first-component rule**, and both are written by
`check-staleness.py` relative to its own `ROOT` `[repo]
tools/check-staleness.py:23-25`. If the tools move deeper and `ROOT` is not
fixed, the report lands somewhere new and **stops being ignored** — it would
start showing up in `git status` and, worse, could be committed. Low cost, but
it is a derived statement and belongs on the checklist.

`__pycache__/` and `*.py[cod]` were added at `f94e91d` with the note that
`tools/__pycache__/check-staleness.cpython-311.pyc` was tracked until
2026-09-21 and the hook rewrote it on every commit. Now untracked
`[cmd] git status --porcelain` → clean. Good; nothing to do, but §7.4 depends
on it staying true.

### 1.13 `CLAUDE.md` (23) and `datasheets/README.md` (5)

`CLAUDE.md` `[cmd]` §1.16: `config/figures.yaml` ×2, `tools/check-staleness.py`
×2, `docs/reference/repo-maintenance.md` ×2, `docs/review/` ×2, `README.md` ×2,
`tools/verify-datasheets.py`, `tools/merge-manifests.py`,
`datasheets/MANIFEST.csv`, `docs/log/`, `docs/research/`, `hardware/bom.csv`,
`ROADMAP.md`, `docs/review/2026-09-20-cold-review/`, plus the five glob forms
`hardware/**`, `docs/decisions/**`, `docs/reference/**`, `config/**`,
`firmware/**` at `:84-85`, and bare `` `MANIFEST.csv` `` ×3,
`` `VERIFIED.md` ``, `` `mod-channels.md` ``, `` `bom.csv` ``.

**`CLAUDE.md:83-85` is the normative definition of the corpus.** It must be
rewritten in the *same commit* as `tools/check-staleness.py:30-32` and
`docs/reference/repo-maintenance.md:15-18`, because those three are three
spellings of one fact. They are a textbook instance of the thing this repo
exists to prevent, and they are currently consistent — keep them that way by
treating them as one atomic edit (§6.1).

`datasheets/README.md`: `tools/merge-manifests.py` ×3,
`tools/verify-datasheets.py` ×2, plus bare `` `MANIFEST.csv` `` ×4 and nine
external URLs that are **not** paths and must be excluded.

### 1.14 `ADR 0NNN` name-references — 509 in the corpus, 4 685 in history

```sh
grep -rhoE 'ADR ?0[0-9]{3}' hardware docs/decisions docs/reference config firmware README.md ROADMAP.md | wc -l   # 509
grep -rhoE 'ADR ?0[0-9]{3}' docs/review docs/log docs/research | wc -l                                            # 4685
grep -rhoE 'ADR ?0[0-9]{3}' datasheets | wc -l                                                                    # 13
```

Plus `hardware/bom.csv`'s `adr` column: **all 138 rows populated**
`[cmd]` §1.6 variant.

**This is a category the brief does not list and it dwarfs everything else.**
It is a *path* reference in substance — `ADR 0004` names
`docs/decisions/0004-cv-interface-module.md` — but it carries none of the
syntax a path rewriter looks for.

**Recommendation, stated as a constraint on the restructure rather than a
migration task: do not renumber or rename the ADRs.** Moving
`docs/decisions/` wholesale costs 9 root-relative links and 33 `owner:` entries.
Renumbering costs 509 corpus references, 138 BOM cells, 4 685 history
references that must *not* be fixed (§3), and a permanent ambiguity where
"ADR 0004" means one document before the restructure and another after. If the
restructure proposes renumbering, that is the single decision most likely to
reproduce this project's failure mode at scale, and it should be argued
explicitly rather than inherited from a directory move.

### 1.15 `<file>.md §N` section references — 10

`[cmd] grep -rhoE '[A-Za-z0-9_.-]+\.md[^.]{0,4}§ ?[0-9]+(\.[0-9]+)?' <corpus> | sort | uniq -c`

```
3  carrier.md §3     2  cluster-boards.md` §4     1  carrier.md §2
2  carrier.md` §2    1  breath-output-stage.md` §4  1  carrier.md §1
```

68 `§` tokens total in the corpus `[cmd] grep -rho '§' <corpus> | wc -l`; 10
of them are cross-file. Phase A does not break these. **Phase B does**, the
moment a page is split and its §3 becomes another file's §1. Plus the one
line-numbered citation at `config/figures.yaml:305`. Total 11 references that
Phase B must re-resolve by hand — §6.4.

### 1.16 The scanner that produced §1.4, §1.5, §1.13 and the 346 total

Save as `/tmp/pathscan.py`; it is the command behind every count in this report
that a one-line grep could not produce honestly.

```python
import os,re,subprocess,collections,sys
ROOT=sys.argv[1] if len(sys.argv)>1 else "."
tracked=subprocess.run(["git","-C",ROOT,"ls-files"],capture_output=True,text=True).stdout.split()
tset=set(tracked); byname=collections.defaultdict(list)
for p in tracked: byname[os.path.basename(p)].append(p)
HIST=("docs/review/","docs/log/","docs/research/")
CORP=("hardware/","docs/decisions/","docs/reference/","config/","firmware/")
PAT=re.compile(r"(?<![A-Za-z0-9_./-])((?:hardware|docs|config|firmware|tools|datasheets|mechanical|LICENSES)/[A-Za-z0-9_.*/-]+|README\.md|ROADMAP\.md|CLAUDE\.md|LICENSE)")
TICK=re.compile(r"`([^`\n]+)`")
tot=collections.Counter(); bare=collections.Counter(); broken=[]
for p in tracked:
    if p.startswith(HIST) or not p.endswith((".md",".yaml",".yml",".csv",".py",".json")): continue
    for i,l in enumerate(open(os.path.join(ROOT,p),encoding="utf-8",errors="replace"),1):
        for m in PAT.finditer(l):
            t=m.group(1).rstrip(".,;:)"); tot[p]+=1
            if "*" not in t and t not in tset and not os.path.exists(os.path.join(ROOT,t)):
                broken.append((p,i,t))
        for m in TICK.finditer(l):
            for tok in re.findall(r"[A-Za-z0-9_.*/-]+",m.group(1)):
                if "/" not in tok and tok in byname: bare[(p,tok)]+=1
print("non-history repo-path tokens:",sum(tot.values()))     # 346
print("backtick bare-filename refs:",sum(bare.values()))
print("unresolvable path tokens:",len(broken))
for b in broken: print("  ",b)
```

`[cmd] python3 /tmp/pathscan.py /home/user/Woody` → **346** non-history
repo-path tokens. Distribution, `[cmd]` the per-source variant:

```
58 config/figures.yaml            25 docs/reference/repo-maintenance.md
53 hardware/bom.csv               23 CLAUDE.md
21 datasheets/MANIFEST.csv        16 README.md
14 .manifest-R6.csv               12 .manifest-R5.csv
11 tools/check-staleness.py       10 hardware/controller/carrier.md
 9 ROADMAP.md                      7 .manifest-R3.csv, .manifest-R7.csv
 … 20 further files at 1–6 each
```

**Six files hold 196 of the 346** `[calc] 58+53+25+23+21+16 = 196`, i.e. 57%.
Those six are `config/figures.yaml`, `hardware/bom.csv`,
`docs/reference/repo-maintenance.md`, `CLAUDE.md`, `datasheets/MANIFEST.csv`,
`README.md` — and **five of the six are on the Phase B freeze list** (§6). That
is the single most useful fact in this report for scheduling: path rewriting
and Phase B contention are concentrated in the same handful of files, so they
must not be worked in parallel.

---

## 2. The rewrite method, per category

The rewrite is driven by one artefact, `MAP` (§3.5), and one program,
`tools/rewrite-paths.py`, written during Phase A. Nothing is rewritten by
hand-run `sed`: a `sed -i` over the corpus is how a bare `bom.csv` inside the
word `subbom.csv` gets mangled, and it leaves no record of what it decided.

### 2.1 Mechanically safe — rewrite from `MAP`, verify by resolution

| Category | Count | Rule |
|---|---|---|
| A `owner:` in figures.yaml | 33 | Parse with `yaml.safe_load`, map `owner`, **re-emit by string substitution on the original text, not by `yaml.dump`** — dumping reflows the whole 45 KB file and destroys the diff, the same class of defect as `lineterminator="\n"` on `bom.csv` `[repo] repo-maintenance.md:132-136` |
| C-root Markdown root-relative links | 9 | `](old)` → `](new)`, exact-string |
| E Backticked explicit paths | 78 − 5 external | Exact-string on the whole token; the 5 externals in an allow-list |
| G bom.csv `notes` | 50 | Exact-string **in the cell**, rewritten via `csv.reader`/`csv.writer` with `lineterminator="\r\n"` `[repo] CLAUDE.md:129-132`. Verify with `git diff --stat`: should touch ≈ the number of rows changed, **not 138** |
| H tools | 18 | By hand, all three files, §2.6 |
| K settings.json | 2 | By hand |
| L README tree | 9 lines | By hand, then diff against `ls -d */` |
| N .gitignore | 0–2 | By hand if `ROOT` changes |
| O, P CLAUDE.md, datasheets/README.md | 28 | By hand, atomically with the tools (§6.1) |

Verification for every mechanical rewrite: **after rewriting, every token that
matched `MAP`'s old side must resolve to an existing file, and zero tokens on
the old side may survive.** That is §5.2's check 3 and it is decidable.

### 2.2 Relative markdown links (19) — recompute, never substitute

`](../reference/latency-budget.md)` is not a string to map; it is a function of
*both* endpoints. Rule:

```
new_link = os.path.relpath(MAP[resolve(src_old, link_old)], os.path.dirname(MAP[src_old]))
```

where `resolve` joins the link against the source file's old directory. This is
correct even when the target does not move, and correct when only the source
moves — both of which happen. Substituting strings here is the error mode:
`../reference/…` from a file that has moved one level deeper silently becomes a
link to nothing, and **markdown links fail silently in every renderer**.

Same rule for the 24 bare-filename markdown links, with the extra resolution
step in §2.3.

### 2.3 Bare filenames (143 backticked + 24 in links) — resolve, then decide

The rule, in order; stop at the first that fires:

1. **Sibling first.** If `os.path.dirname(src_old) + "/" + name` exists at
   HEAD, that is the referent. This resolves the large majority: bare
   `carrier.md` inside `hardware/controller/cluster-boards.md`, bare
   `mod-channels.md` inside `hardware/module/pitch-stage.md`.
2. **Unique in the corpus.** Else, if exactly one corpus file has that
   basename, that is the referent. This catches bare `bom.csv` ×51, bare
   `key-layout.yaml` ×14, bare `power-entry.md` ×10 from `0004` and
   `pcb-pipeline.md`.
3. **Unique in the repo including history.** Else, if exactly one file
   anywhere has that basename — this is how `R10-keyscan-and-adc.md` and
   `D2-missing-testability.md` resolve, both into `docs/research/` and
   `docs/review/`. **Do not rewrite these** (§3.3); emit them to the
   human-decision list instead.
4. **Otherwise: stop, and put it on the human list.** Today this is
   `README.md` (12 candidates) and `VERIFIED.md` (6).

**Then the decision the brief asks for.** A bare name that resolved uniquely at
step 2 may *stop* being unique in the target tree. The rewriter must check:

> For each bare reference that resolved to `T`, is `basename(MAP[T])` unique
> among the basenames of `MAP`'s new side? If yes, **leave the bare name as it
> is** (rewriting it only if `MAP` renames the file). If no, **promote it to an
> explicit path** relative to the new source location.

Promotion is the safe direction and costs only verbosity. Silence is the unsafe
direction: a bare `` `power-entry.md` `` in a tree with `module/power-entry.md`
and `controller/power-entry.md` reads as unambiguous and is not, and nothing
will ever flag it.

**Where a human must decide, exhaustively:**

- the 2 bare `README.md` and 1 bare `VERIFIED.md` (already ambiguous);
- every bare reference that fails step 4 against the *new* tree — unknown to me
  without the target layout, and the rewriter must print this list, not swallow it;
- the 2 corpus→history bare references (§3.3);
- `config/figures.yaml:305`'s `…0004-cv-interface-module.md:627` line number;
- the 10 `§N` references and `pcb-pipeline.md`'s "importing the six" — Phase B,
  §6.4.

### 2.4 Cross-zone references, corpus → history (4)

`[repo] hardware/controller/carrier.md` cites
`docs/review/2026-09-21-schematic-review/S3-carrier.md`, plus bare
`R10-keyscan-and-adc.md` and `D2-missing-testability.md`;
`[repo] hardware/module/digital-and-supervision.md` cites
`docs/review/2026-09-21-hardware-and-standards-review/`;
`[repo] docs/reference/pcb-pipeline.md:4` cites
`docs/review/2026-09-21-pcb-pipeline-review/`;
`[repo] config/figures.yaml:286,324` cite
`docs/review/2026-09-21-preflight/A4-carrier.md`.

These stay correct **iff history does not move**, which §3.4 argues it must
not. Add an assertion to the rewriter: any token resolving under
`docs/review|log|research` is left byte-identical and logged. If the assertion
fires and history *has* moved, the restructure has a much bigger problem than
these four.

### 2.5 `MANIFEST.csv` + fragments (154 cells) — do not rewrite either

**The manifest's `file` column is relative to `datasheets/`
`[repo] tools/merge-manifests.py:26-33`.** Therefore:

- If `datasheets/` moves **as a whole**, **zero manifest cells change.** The
  column is already root-agnostic. This is the strongest argument for moving
  `datasheets/` whole and never restructuring inside it during this migration.
- `MANIFEST.csv` is **generated** `[repo] repo-maintenance.md:17,76-81`. Never
  edit it. If it must change, change a fragment and re-run the tool.
- The fragments are **append-only, per author** `[repo] repo-maintenance.md:18`,
  `[repo] CLAUDE.md:62-66`. A `BLOCKED` row is the honest record of a gap when
  it was written. **A migration is not licence to edit another wave's
  fragment** — and since the cells do not need to change (previous point), the
  question does not arise.
- **The rewriter must exclude `datasheets/**` entirely**, or the 14
  `mechanical/…` cells and the 33 prefixed cells will be resolved against the
  wrong root (§1.8).

The one cell family that *would* need attention is the 33 fragment cells
carrying the `datasheets/` prefix — but they are normalised away on merge, so
they too are inert. Leave them.

### 2.6 The tools (18) — hand-edited, and `ROOT` first

`ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))` appears in
all three tools `[repo] check-staleness.py:20, verify-datasheets.py:18,
merge-manifests.py:11`. **If `tools/` stays exactly one level below the root,
all three are unchanged.** That is a reason to leave `tools/` where it is; if
it must move, all three need `ROOT` recomputed and every relative literal
re-checked, and there is no test that would catch getting it wrong (§0.1).

### 2.7 The list that goes to a human, not a program

Anything in §2.3's step 4, plus: `config/figures.yaml:305` (line number),
`README.md:95-105` (tree block, and the missing `datasheets/`),
`hardware/bom.csv:97` (broken link, §1.6), `README.md:83-91` vs `:114-118`
(licence contradiction), and all four `pcb/` paths (§1.11). **The rewriter must
exit non-zero if this list is non-empty and unacknowledged**, so it cannot be
skipped by a tired operator.

---

## 3. What must NOT be fixed

### 3.1 The rule

`[repo] CLAUDE.md:77-81`: "`docs/review/`, `docs/log/` and `docs/research/` are
historical records. They are **not** the corpus and must never be 'corrected'.
A 2026-09-21 review saying '8HP' is right as a record of what was true when it
was written." Restated at `[repo] docs/reference/repo-maintenance.md:16` and
enforced at `[repo] tools/check-staleness.py:32` (`EXCLUDE`).

**A path is a value.** Everything in the rule applies to path references
without amendment. A 2026-09-21 review saying `hardware/module/power-entry.md`
is right as a record of where that page was when it was written. Rewriting it
would make the review say something its author did not say — which is a
stronger corruption than staleness, because it is undetectable afterwards.

**Confirmed: leave them stale.**

### 3.2 How many

```sh
# root-relative repo-path tokens inside history .md files
python3 /tmp/pathscan.py .   # with the HIST filter inverted
```

| Reference kind, inside `docs/review,log,research` | Occurrences | Distinct |
|---|---|---|
| Root-relative tokens naming corpus files | **3 548** | 88 |
| Backticked **bare** filenames naming corpus basenames | **4 289** | 30 |
| Tokens naming `datasheets/…` | 106 | 42 |
| Tokens naming `tools/…` | 44 | 9 |
| Tokens naming `CLAUDE.md` | 69 | 1 |
| Tokens naming other history files | 160 | 29 |
| `ADR 0NNN` name-references | **4 685** | — |

**141 history `.md` files scanned; 137 of them contain at least one repo-path
reference** `[cmd]` the inverted scanner. Total references that go stale on the
move and must be left alone: **8 216** excluding ADR-by-number, **12 901**
including it `[calc] 3548+4289+106+44+69+160 = 8216; +4685 = 12901`.

For scale: the non-history tree holds 346 such tokens (§1.16). **History
outnumbers the corpus 24:1 on path references** `[calc] 8216/346 = 23.7`. Any
plan that treats "fix the references" as a whole-repo `sed` is off by that
factor and will silently rewrite the project's entire evidentiary record.

### 3.3 The two exceptions that run the other way

`hardware/controller/carrier.md` cites two history documents by bare filename
(`R10-keyscan-and-adc.md`, `D2-missing-testability.md`) — corpus → history, not
history → corpus. These are *live* references in a corpus file. They must
remain resolvable, which they will iff history does not move. Log them; do not
rewrite them.

### 3.4 Therefore: history does not move

The cheapest way to honour §3.1 is to give it nothing to do. If
`docs/review/**`, `docs/log/**`, `docs/research/**` keep their paths:

- all 8 216 outbound references are still *wrong* (their targets moved) — that
  is the intended, recorded outcome;
- the 4 inbound corpus→history references stay *right* at zero cost;
- `tools/check-staleness.py:32` `EXCLUDE` needs no edit;
- `CLAUDE.md:77-85` and `repo-maintenance.md:16` need no edit on the history
  row.

**Recommendation: exclude the three history directories from the restructure
entirely, and say so in the Phase A commit message.** If the restructure does
move them, the count in §3.2 becomes the number of references that must be left
stale *in both directions*, and `EXCLUDE` plus the three normative statements
must move atomically with them (§6.1).

### 3.5 The mapping file: format and location

One file, written once in Phase A's first commit, never edited again.

**Location:** `docs/reference/path-map-2026-09-21.csv`.

Reasoning, against the repo's own four-kinds taxonomy
`[repo] docs/reference/repo-maintenance.md:11-20`:

- It is **not** history — it is written now, about now, and a reader of a 2026
  review needs it in 2027.
- It is **not** generated — regenerating it after the fact is impossible, which
  is exactly why it must be written during the move.
- `docs/reference/` is corpus, so the checker scans it (`.csv` is in the
  extension filter, `[repo] tools/check-staleness.py:57`) and the file stays
  under the same consistency guarantee as everything else. That is a feature.
- Dating the filename makes a second restructure additive rather than a
  rewrite, which is the same discipline as the per-wave manifest fragments.

**Format** — 4 columns, header row, LF (it is a new file; the CRLF rule is
specific to `hardware/bom.csv` `[repo] repo-maintenance.md:132`):

```csv
old,new,kind,note
hardware/module/power-entry.md,<new path>,moved,
docs/decisions/0004-cv-interface-module.md,<new path>,moved,
docs/review/2026-09-21-preflight/A4-carrier.md,docs/review/2026-09-21-preflight/A4-carrier.md,unmoved-history,"Historical record; CLAUDE.md §6"
hardware/bom.csv,<new path>,moved,"Generated-adjacent: 11 cols, CRLF"
datasheets/MANIFEST.csv,<new path>,moved-whole,"file column is relative to datasheets/; cells unchanged"
```

`kind` ∈ `moved` | `unmoved` | `unmoved-history` | `moved-whole` | `split`
(Phase B only) | `deleted`. **Every tracked file gets a row, including the ones
that do not move** — a map with only the movers cannot answer "did this path
change?", which is the question a reader of a 2027 review will actually ask.
`[cmd] git ls-files | wc -l` gives the row count the map must have.

**Pointer, not a copy.** `docs/reference/repo-maintenance.md` gains a §7:

> ## 7. The 2026-09-21 restructure
> Paths changed. `path-map-2026-09-21.csv` maps every old path to its new one.
> **References inside `docs/review/**`, `docs/log/**` and `docs/research/**`
> point at the old paths and are deliberately not corrected** (§1, CLAUDE.md
> §6). Resolve them through the map.

One sentence in `CLAUDE.md` §6 pointing at that §7, and nothing else anywhere.
The rule the map exists to serve is "cite, do not restate"
`[repo] CLAUDE.md:16-19`; a mapping duplicated into three files is that rule
broken in the act of documenting it.

**Fallback:** if a path string in the map collides with a `forbidden` pattern
in `config/figures.yaml` — unlikely, since forbidden patterns are values with
units, but checkable — the checker will say so. `[cmd] python3
tools/check-staleness.py` after adding the map. If it fires, add a
`false_positive_note` to the offending figure `[repo] repo-maintenance.md:162-164`
rather than moving the map out of the corpus.

---

## 4. `git mv` vs rewrite, and commit sequencing

### 4.1 Why rename detection is the whole point

The corpus's defence is its history. `[repo] CLAUDE.md:110-115`: "Findings are
claims. Several have been wrong... Verify before repeating, and record the
verification." Verification means reading back what a figure was and when it
changed. The only instrument for that is `git log --follow` / `git log -p` on a
path — and `docs/review/**`, the other instrument, is about to point at paths
that no longer exist (§3). **After the restructure, history's path references
are stale by design; `--follow` becomes the *primary* way to get from an old
path to its content.** If it breaks, the audit trail for ~90 recorded staleness
defects becomes unreachable without archaeology.

`[cmd] git --version` → 2.43.0. `diff.renames` is unset, i.e. the default
`true`. `[cmd] git log --follow --oneline -- docs/reference/repo-maintenance.md`
works today.

### 4.2 What breaks rename detection

1. **Moving and editing in the same commit.** Rename detection pairs a deleted
   blob with an added one at ≥50% similarity (`-M50%`, the default). Edit
   enough and the pair is not made. The exposure here is small for big files —
   rewriting 50 path cells in `hardware/bom.csv` (126 890 bytes
   `[cmd] wc -c`) is a fraction of a percent — but real for small ones, and
   `--follow` is more fragile than plain `-M` because it makes the decision
   from a *single-path* diff with less to compare against.
2. **Split.** Phase B turning one page into three is a delete plus three adds.
   No amount of `-M` recovers it; `-C`/`--find-copies-harder` sometimes finds
   one of the three. This is inherent, and the reason Phase B must be separated
   from Phase A.
3. **Empty files.** All 8 `.gitkeep` are empty and therefore identical blobs.
   Git pairs identical blobs arbitrarily, so a commit that moves several
   `.gitkeep` at once can report nonsense renames. Harmless in content terms,
   noisy in `git log --stat`, and a reason not to rely on the rename report as
   the only check (§5.2 check 1).
4. **`--follow` follows one rename at a time.** Two renames of the same file in
   the restructure (Phase A moves it, Phase B renames it) still work, but each
   additional hop is another chance to fall below threshold.
5. **`git mv` is not magic.** Git stores no rename; it infers them at read time
   from content. `git mv` and `rm`+`add` produce *identical* trees. So what
   actually preserves detection is **not touching the content**, not the choice
   of command. `git mv` is still the right command — it stages both sides
   atomically and cannot leave a half-staged move — but the discipline that
   matters is the sequencing below.

### 4.3 The sequencing rule

> **A commit either moves files or changes their content. Never both.**

Concretely, Phase A is **three commits**, in this order:

**A0 — guard the tools (content only, nothing moves).**
Add the corpus-file-count floor to `check-staleness.py` (§7.2); make
`merge-manifests.py` refuse to write a manifest from zero fragments (§0.2);
make `verify-datasheets.py` fail rather than skip when `bom.csv` is absent
(§1.7). Write `docs/reference/path-map-2026-09-21.csv` and
`repo-maintenance.md` §7. **This commit must land before anything moves**,
because it is the only thing that will notice if the move goes wrong.
`[test]` justification: §0.1 and §0.2 both produced exit 0 on a broken tree.

**A1 — the move, and nothing else.** Every `git mv`, directories whole
(`git mv datasheets refs/datasheets`, never `datasheets/*` — §0.2). **Zero byte
changes to file contents.** At this commit the repo is knowingly broken: links
dangle, the tools crash or under-report. That is fine and it is the point —
`git log --follow` and `git diff -M --stat HEAD~1` see a pure rename set with
100% similarity on every file, which is the cleanest possible record.

Verify before committing:

```sh
git add -A && git diff --cached -M --stat | tail -1     # must read "0 insertions(+), 0 deletions(-)"
git diff --cached -M --summary | grep -c '^ rename'     # must equal the number of moved files
git diff --cached --numstat | awk '$1!=0||$2!=0'        # must print NOTHING
```

The third is the decisive one: any non-zero add/delete count means content
changed and A1 is not a pure move.

**A2 — the rewrite, and nothing else.** Run `tools/rewrite-paths.py` from
`MAP`; hand-edit the tools, `CLAUDE.md`, `README.md`'s tree,
`.claude/settings.json`, `.gitignore` if needed. **Zero files move.** Verify:

```sh
git diff --cached --summary | grep -E '^ (rename|create|delete)'   # must print NOTHING
```

Because A1 is a pure rename set, `--follow` resolves across it at 100%
similarity; because A2 renames nothing, it cannot confuse detection at all. The
history stays walkable through the restructure in both directions.

**Do not squash A0/A1/A2.** A squash reintroduces exactly the move-plus-edit
commit the split exists to avoid, and it is the kind of tidying that looks
harmless in a PR.

**Do not rebase or amend A1 after A2 lands.** Rewriting A1 rewrites the blob
ids the rename inference is drawn from.

### 4.4 Phase B and `--follow`

Phase B splits content, so `--follow` will not cross a split. Two mitigations,
both cheap:

- Each Phase B split commit's message names the **source path at A1** for each
  new file: `split from hardware/module/power-entry.md (pre-restructure
  hardware/module/power-entry.md)`. `git log --grep` then does what `--follow`
  cannot.
- The `MAP` gains `kind=split` rows, one per new file, all pointing at the same
  `old`. That makes the map answer the split case too, which is the only
  machine-readable record that will exist.

---

## 5. Phase A exit criteria

Phase A is done when **all eight** of the following hold. Each is a command or
a named hand-check; none is a judgement call.

### 5.1 Before A1: capture the baseline

```sh
B=/tmp/phaseA-baseline; mkdir -p $B
git rev-parse HEAD                                              > $B/rev
./numbag.sh HEAD                                                > $B/numbag       # §5.2 check 4
python3 tools/check-staleness.py --detail                       > $B/staleness
python3 tools/verify-datasheets.py                              > $B/datasheets
python3 tools/merge-manifests.py                                > $B/manifest
git ls-files                                                    > $B/files
python3 /tmp/pathscan.py .                                      > $B/paths        # records the 1 known-broken link
git ls-files | while read f; do printf "%s %s\n" "$(git hash-object "$f")" "$f"; done | sort > $B/blobs
```

`$B/paths` must record `hardware/bom.csv:97 →
datasheets/discrete-and-power/MF-PSMF010X.pdf` as a **pre-existing** break
(§1.6), so Phase A is not blamed for it.

### 5.2 The eight checks

**1. The move is a pure rename set.** At A1: `git diff -M --numstat HEAD~1 |
awk '$1!=0||$2!=0'` prints nothing, and
`git diff -M --summary HEAD~1 | grep -c '^ rename'` equals the number of moved
files. *(Caveat: the 8 empty `.gitkeep` may be paired oddly; check them by
name against `MAP`, not by the rename report.)*

**2. Blob identity across A1.** Every file's blob hash is unchanged:

```sh
git ls-files | while read f; do printf "%s %s\n" "$(git hash-object "$f")" "$f"; done \
  | sort -k1,1 | join -j1 <(sort -k1,1 $B/blobs) - | wc -l    # must equal the file count
```

This is stronger than check 1 and does not depend on rename heuristics at all.
It is the real proof that A1 changed no content.

**3. Zero unresolvable path references, and zero survivors of the old side.**
After A2:

```sh
python3 /tmp/pathscan.py .        # "unresolvable path tokens: 1"  ← only the known bom.csv:97 break
python3 tools/rewrite-paths.py --verify   # exit 0: no MAP old-side token survives outside history
```

Any *new* unresolvable token is a Phase A defect.

**4. No number changed. The command:**

```sh
#!/bin/sh   # numbag.sh <rev>
rev="$1"
git ls-tree -r --name-only "$rev" -- <corpus paths at that rev> \
| grep -E '\.(md|csv|ya?ml)$' \
| while read -r f; do git show "$rev:$f"; done \
| sed -E 's#(hardware|docs|config|firmware|tools|datasheets|mechanical|pcb)/[A-Za-z0-9_.*/-]+#<PATH>#g' \
| sed -E 's#\b[A-Za-z0-9_.-]+\.(md|csv|ya?ml|py|pdf|kicad_pcb|kicad_mod|dxf|step|stp)\b#<FILE>#g' \
| grep -oE '[0-9]+(\.[0-9]+)?' | sort | uniq -c
```

`diff $B/numbag <(./numbag.sh HEAD)` must be **empty**.

**Does it work?** Yes, and I validated it. `[cmd]` at HEAD: 965 distinct tokens,
12 871 occurrences, sha `87509a75…`. Identical at HEAD~1 and HEAD~2 (which
touched only `.gitignore`, a `.pyc` and a review file `[cmd] git diff --stat`),
and **different** at HEAD~4 (`a447f15e…`) and HEAD~6 (`9c7498d7…`), which did
change corpus numbers. So it is sensitive to real changes and insensitive to
noise.

**The masking is not optional.** Without it the bag is 13 091 occurrences and
**153 of those numbers live inside path strings**
`[cmd] git grep -hoE '(hardware|docs|…)/[A-Za-z0-9_.*/-]+' HEAD -- <corpus> |
grep -oE '[0-9]+(\.[0-9]+)?' | wc -l` — `0004`, `0807`, `2020`, `3.1`, `78`,
`5400`. A2 rewrites those by design, so an unmasked bag reports 153 spurious
deltas and a real one hides in them. `[calc] masked 12 871 = 13 091 − 220`,
the extra 67 coming from bare-filename masking.

**What it misses — state this in the Phase A commit message, do not let the
green diff imply more than it proves:**

- **Permutation.** Two files swapping a value leaves the bag identical. Real
  risk: A2 edits many files at once.
- **Numbers reached only via the masks.** An edit *inside* a path or filename —
  e.g. `0004-cv-interface-module.md` → `0005-…` — is masked to `<PATH>` and
  invisible. Given §1.14 this is exactly the edit most likely to be made.
- **Non-numeric facts.** `SETTLED`→`disputed`, a refdes, a part number, a
  polarity, `BLOCKED`→`OK`.
- **Binary and non-`.md/.csv/.yaml` files**, i.e. all 77 datasheets.
- **Refutation wording.** The checker's whole refutation mechanism
  `[repo] tools/check-staleness.py:35-40` is textual; deleting a `was` flips a
  refuted value to live and the bag does not move.

**Therefore check 4 is the weak form and check 5 is the strong one.** Run both.

**5. Inverse-rewrite byte identity — the real proof.** For every `old,new` pair
in `MAP`, apply the **inverse** of A2's rewrite to the new file and require it
byte-identical to the old:

```sh
python3 tools/rewrite-paths.py --invert --check-against $B/rev
# for each pair: git show $(cat $B/rev):old  ==  invert(rewrite)(HEAD:new)
# exit 0 iff every pair is byte-identical
```

If A2 changed anything other than a path token from `MAP`, this fails and names
the file and line. It subsumes checks 2 and 4 and closes all five gaps above
except the hand edits (tools, `CLAUDE.md`, `README.md` tree,
`settings.json`), which are excluded by name and reviewed by hand in 5.3.

This is the one check that makes "Phase A changed no content" a *decidable
proposition* rather than a promise, and it is why `MAP` must be complete
(§3.5).

**6. The tools pass, and pass on the right number of files.**

```sh
python3 tools/check-staleness.py --detail | head -1
# corpus: 33 files | bom.csv: 138 rows x 11 cols | figures tracked: 33
python3 tools/verify-datasheets.py     # 77 verified, 21 blocked/not-fetched, 0 problems
python3 tools/merge-manifests.py       # 98 rows from 8 fragments
git diff --stat datasheets/MANIFEST.csv   # MUST BE EMPTY after the merge re-run
```

**The `corpus: 33 files` line is the exit criterion, not the `PASS`** — §0.1.
`figures tracked: 33` and `bom.csv: 138 rows x 11 cols` likewise. And the last
line is load-bearing: if re-running `merge-manifests.py` dirties
`MANIFEST.csv`, a fragment moved or was edited and §0.2 is in play.

**7. The hook fires and reports.** Stage a trivial change and attempt a commit;
the `systemMessage` must read `staleness: PASS …`, not `staleness: ` (§7.1).

**8. `--follow` crosses the restructure.** For three files chosen to span the
tree:

```sh
git log --follow --oneline -- <new path> | wc -l   # ≥ the count at $B/rev
```

### 5.3 What a reviewer checks by hand (nothing else will)

1. **`README.md`'s tree block** against `ls -d */` — including whether
   `datasheets/` and `docs/review/` were added (§1.10).
2. **`CLAUDE.md:83-85` ≡ `tools/check-staleness.py:30-32` ≡
   `repo-maintenance.md:15-18`** — the three spellings of the corpus
   definition, read side by side (§6.1).
3. **`config/figures.yaml` diff is 58 single-token changes at most**, and
   `git diff --stat` on it does not report a reflow.
4. **`git diff --stat hardware/bom.csv` touches ≈50 lines, not 138** — the CRLF
   trap `[repo] repo-maintenance.md:132-136`.
5. **`docs/review/**`, `docs/log/**`, `docs/research/**` are byte-identical.**
   `git diff $B/rev HEAD -- docs/review docs/log docs/research` must be empty
   *or* show only pure renames. This is §3's criterion and it is the one a
   well-meaning rewriter is most likely to violate.
6. **The rewriter's human-decision list** (§2.7) is empty or every entry is
   signed off in the commit message.
7. **`path-map-2026-09-21.csv` has a row for every tracked file**, `wc -l` =
   `git ls-files | wc -l` + 1.

---

## 6. The ordering hazard in Phase B

Phase B runs parallel agents splitting content inside their own directory. Any
file more than one agent may touch is a write race, and the loser's edit
disappears silently — the same shape as the `MANIFEST.csv` trap
`[repo] repo-maintenance.md:76-81`.

### 6.1 The shared files, with a rule for each

| File | Why shared | Rule |
|---|---|---|
| `config/figures.yaml` | 33 `owner:` + 25 free-text paths; **every split changes which file owns a figure** | **Serialised.** No agent edits it. Each emits `figures-<agent>.patch.yaml` (id → new owner / new note). One integrator applies all of them in a single commit after the last split. Non-negotiable: this is the register `[repo] CLAUDE.md:16-19` |
| `hardware/bom.csv` | 138 rows, 11 cols, CRLF, 50 path refs in `notes`; module *and* controller agents both have business here | **Serialised**, same patch-then-integrate. Two agents writing a CRLF CSV concurrently is how a 3-row change becomes a 130-row diff `[repo] CLAUDE.md:129-132` |
| `datasheets/MANIFEST.csv` | **Generated** | **Frozen.** Never edited by anyone. Regenerated only by `merge-manifests.py` |
| `datasheets/.manifest-R1..R8.csv` | Per-author, append-only | **Frozen.** An agent that banks a new document creates `.manifest-R9.csv`; nobody touches R1–R8 `[repo] CLAUDE.md:62-66`, `repo-maintenance.md:18` |
| `tools/check-staleness.py`, `verify-datasheets.py`, `merge-manifests.py` | Corpus definition + the only guards | **Frozen for Phase B.** Changes go in a separate serialised commit with the §6.2 atom |
| `.claude/settings.json` | The hook | **Frozen** |
| `README.md` | Tree block + 16 path tokens; every split can change the tree | **Serialised**, integrator-owned, updated **once** at the end of Phase B |
| `ROADMAP.md` | 9 path tokens, milestone text every agent wants to touch | **Serialised**, integrator-owned |
| `CLAUDE.md` | Normative corpus definition | **Frozen**; §6.2 atom only |
| `docs/reference/repo-maintenance.md` | 25 path tokens; §1's four-kinds table | **Frozen**; §6.2 atom only |
| `docs/decisions/README.md` | ADR index, **15 of the corpus's 52 markdown links** | **Serialised**, integrator-owned |
| `docs/reference/path-map-2026-09-21.csv` | The map | **Append-only**, integrator-owned; `kind=split` rows added as splits land |
| `.gitignore` | Root-anchored patterns | **Frozen** |
| `docs/review/**`, `docs/log/**`, `docs/research/**` | History | **Frozen absolutely** (§3) |

**Twelve files are serialised or frozen. Five of them are in the six files that
hold 57% of all path references (§1.16).** Path-rewriting contention and Phase B
contention land on the same files; that is the scheduling constraint.

### 6.2 The atom

`CLAUDE.md:83-85`, `tools/check-staleness.py:30-32` and
`repo-maintenance.md:15-18` are **one fact in three files**. They must be
edited in one commit, by one agent, always. Splitting them across two commits
is the project's named failure mode with the corpus definition itself as the
value, and it is the single edit whose staleness no tool can detect — the
checker cannot check its own definition.

### 6.3 The mechanism, not just the rule

Freeze rules that live in a prompt get broken. Two cheap enforcements:

- Give each Phase B agent a worktree containing only its own directory plus
  read-only copies of the shared files. It cannot write what it does not have.
- Or: a `PreToolUse` hook on `Bash(git commit *)` that rejects a commit whose
  staged paths intersect the frozen list unless the message contains
  `INTEGRATOR:`. The hook machinery already exists
  `[repo] .claude/settings.json:4-14`.

### 6.4 Phase B's own semantic debt

Not path references, but the same failure mode and no grep finds them:

- The **10 `§N` cross-file references** (§1.15) — re-resolve each by hand after
  the splits.
- `config/figures.yaml:305`'s `…:627` line number.
- `pcb-pipeline.md:115` "one module per schematic page, `module.py` importing
  **the six**" — a count coupled to `hardware/module/*.md`, which is 6 today.
  **If Phase B changes that count, this sentence is stale.** This is the
  `mod-channels.md` watchdog case `[repo] CLAUDE.md:71-73` waiting to happen,
  and it belongs in the Phase B exit checklist explicitly.
- `README.md:83-91` vs `:114-118`, the licence contradiction (§1.10) — decide
  it rather than carry it into the new tree.

---

## 7. The hook

### 7.1 What it does now

`[repo] .claude/settings.json`: `PreToolUse`, `matcher: "Bash"`,
`if: "Bash(git commit *)"`, `timeout: 30`. It runs
`python3 "$CLAUDE_PROJECT_DIR/tools/check-staleness.py"`, writes the full
output to `$CLAUDE_PROJECT_DIR/.staleness-report.txt`, then greps for
`^(STALE VALUES STILL LIVE|BOM INTEGRITY|PASS|FAIL)` and puts the first three
matches in a `systemMessage`.

It is **advisory**: `|| true` swallows the exit code and `jq -n` always
succeeds, so the hook never blocks a commit. `[repo] CLAUDE.md:41-42` describes
it as making the omission "visible rather than silent", which matches.

### 7.2 Mid-migration: it is worse than useless unless A0 lands first

Three states, all reproduced `[test]` in a `git archive HEAD` copy:

| State | Checker | Hook `systemMessage` |
|---|---|---|
| `docs/decisions/` moved, rest in place | exit 0, `corpus: 18 files`, `PASS` | **`staleness: PASS no live stale values | 5 unresolved (tracked);`** |
| `hardware/` moved (`bom.csv` gone) | `FileNotFoundError`, exit 1 | **`staleness: `** (empty) |
| `config/figures.yaml` moved | `FileNotFoundError`, exit 1 | **`staleness: `** (empty) |

Row 1 is the lethal one: **green while 45% of the corpus is unscanned**
`[calc] (33−18)/33 = 45%`. Rows 2 and 3 are merely silent — a traceback matches
none of the four anchored patterns, so `$s` is empty and the message reads
`staleness: ` with nothing after it, which reads like a glitch rather than a
failure.

**So: can the checker pass while paths are half-moved? Yes — and that is the
problem, not the reassurance.**

### 7.3 What to do, in A0, before anything moves

1. **A floor on the corpus file count.** After `corpus_files()`:

   ```python
   MIN_CORPUS_FILES = 33          # bump deliberately when the corpus grows
   if len(files) < MIN_CORPUS_FILES:
       print(f"FAIL corpus shrank to {len(files)} files, expected >= {MIN_CORPUS_FILES} "
             f"- a CORPUS_DIRS entry is missing or a directory moved")
       return 1
   ```

   `FAIL` is already one of the hook's four anchored patterns, so this surfaces
   with no settings change. This single guard converts §0.1 from silent to
   loud, and it is ~5 lines.

2. **Assert the fixed paths exist** rather than letting `open()` raise:
   `config/figures.yaml`, `hardware/bom.csv`. A named `FAIL` line instead of a
   traceback means the hook reports it. Same for `verify-datasheets.py:92`'s
   `if os.path.exists(bom)` — make the absence a failure, not a skip (§1.7).

3. **Guard `merge-manifests.py`:** refuse to write when the fragment glob is
   empty (§0.2). Three lines, prevents the destruction of 98 SHA-256 rows.

4. **Anchor the hook's grep to also catch a crash.** Add `Traceback` to the
   alternation, or have the hook emit `staleness: NO OUTPUT (checker crashed)`
   when `$s` is empty. Without this, A0's own guards are invisible whenever the
   checker dies before reaching them.

### 7.4 During A1 and A2

- **Do not disable the hook.** It is advisory, and its noise across the move is
  information.
- **A1 will FAIL the checker** once A0's floor is in (paths moved,
  `CORPUS_DIRS` not yet updated). **That is correct and expected.** Say so in
  A1's commit message; otherwise the next reader finds a red commit and
  "fixes" it by weakening the guard.
- **A2 must return it to `PASS` with `corpus: 33 files`.** That is exit
  criterion 5.2/6.
- `.staleness-report.txt` and `.staleness/` stay gitignored
  `[repo] .gitignore:1-2` as long as `ROOT` is unchanged (§1.12, §2.6). If
  `tools/` moves, fix `.gitignore` in A2 or the report starts appearing in
  `git status` mid-migration and someone commits it.
- `__pycache__/` is gitignored as of `f94e91d`, so the hook's `.pyc` rewrite no
  longer dirties the tree `[repo] .gitignore:9-13`. Keep it that way; the hook
  runs on every commit attempt and would otherwise stage a binary change into
  A1, breaking exit criterion 5.2/2.

---

## 8. Ten-line summary for whoever executes this

1. **A0 first.** The checker fails open on a moved corpus dir (§0.1) and
   `merge-manifests.py` silently empties `MANIFEST.csv` (§0.2). Add the file-count
   floor and the empty-glob guard *before* anything moves.
2. **Move directories whole.** `git mv datasheets refs/datasheets`, never
   `datasheets/*` — the 8 fragments and 8 `.gitkeep` are dotfiles (§0.2).
3. **Three commits: A0 guards, A1 pure move, A2 pure rewrite.** Never both in
   one (§4.3). `git diff --cached --numstat` must be all zeros at A1.
4. **346 path references outside history** (§1.16), 196 of them in six files,
   five of which are on the Phase B freeze list.
5. **Only 9 of 52 markdown links are root-relative.** The other 43 must be
   *recomputed* from both endpoints, not substituted (§2.2).
6. **143 bare-filename references.** Resolve sibling-first, then corpus-unique;
   **promote to an explicit path whenever the new tree makes the basename
   ambiguous** (§2.3).
7. **Do not rewrite `datasheets/`.** The manifest's `file` column is relative to
   `datasheets/`, so a whole-directory move changes zero cells (§2.5).
8. **8 216 history references go stale on purpose** — 24× the corpus's count.
   Leave every one. Record the mapping once, at
   `docs/reference/path-map-2026-09-21.csv`, pointed to from
   `repo-maintenance.md` §7 and `CLAUDE.md` §6 (§3).
9. **Prove no number changed with the inverse-rewrite byte-identity check**
   (5.2/5). The masked numeric bag (5.2/4) is validated and useful but misses
   permutations, anything inside a path, and every non-numeric fact.
10. **Do not renumber the ADRs.** 509 corpus + 138 BOM + 4 685 history
    references carry no path syntax and no tool can find them (§1.14).

---

### Things I could not check

- The **target layout** — the cold rule bars this wave's `README.md`. Every rule
  above is parametric on `MAP`; a reviewer who *can* read the target must
  re-run §2.3's step-4 ambiguity test against it, because that is the one check
  whose answer depends on the destination.
- Whether `docs/review/**` is in scope for the move. §3.4 argues it must not
  be; if the restructure disagrees, §3.2's counts become bidirectional.
- Whether the hook actually fires on `git commit` in the executing session. I
  observed the staleness line on non-commit `Bash` calls in my own session,
  which suggests the `if` clause may be evaluated more loosely than
  `.claude/settings.json:11` reads. Exit criterion 5.2/7 checks the behaviour
  that matters either way.
