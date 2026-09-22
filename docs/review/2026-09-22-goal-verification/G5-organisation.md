# G5 — Organisation, judged as a newcomer experiences it

**Slice brief:** is this repository actually *organised*? Not "does the checker
pass" — does a reader arriving cold get where they need to go, and do the
documents that describe the layout describe the layout that exists?

**Measured against `a4b80b1`**, the revision the wave README names. Every count
below was re-taken from `git show a4b80b1:<path>` blobs rather than from the
working tree, for the reason in G5-0.

**Cold:** I read nothing under `docs/review/`. I listed filenames there
(`ls`, `git ls-tree`) to count waves and to check the freeze diff, and I read
commit *subject lines* via `git log --oneline` on paths under `docs/review/`.
No report body, README, STATUS or VERIFIED file in that tree was opened.

**Method:** filesystem enumeration and scripted comparison against the four
documents that make structural claims (`README.md`, `CLAUDE.md`,
`hardware/README.md`, `docs/reference/repo-maintenance.md`), plus a corpus-wide
exact-duplicate-block detector and a relative-link resolver. Provenance is
marked on every claim.

---

## G5-0 — The freeze is broken again, live, by a concurrent slice

**This is not my brief, but it invalidates `[test]` baselines in every slice of
this wave, so it leads.**

`git status --porcelain` at 14:37 UTC, mid-slice `[test]`:

```
 M README.md
 M tools/check-staleness.py
```

`[repo] git diff README.md` — an appended line
`See [the missing page](g10-does-not-exist.md).`
`[repo] git diff tools/check-staleness.py`:

```
-    link_problems = check_links(files)
+    link_problems = check_links([])  # G10 experiment: wrong argument
```

and later a comment injected into
`hardware/module/pitch-stage/circuit.yaml` line 30, also self-labelled `G10`.

Slice G10 is mutating the corpus **and `tools/`** while the wave runs. I watched
the `PreToolUse` hook's verdict change four times on a tree I had not touched:
`PASS` → `FAIL … 1 links` → `PASS` → `FAIL … 1 stale` → `FAIL … 2 stale`
`[test]` (successive hook outputs across my own read-only `Bash` calls).

Note the second state: `check_links([])` makes the link check scan nothing, so
the sabotaged checker reported **`PASS`** on a tree containing the broken link
G10 had just added. A checker that fails open, again.

`CLAUDE.md`'s "Review waves" section names this exact failure — *"the last
wave's own orchestrator declared a freeze and then committed a tooling fix while
round 2 was running, so two slices running one command twenty minutes apart got
opposite verdicts"*. It has recurred inside the wave whose README was rewritten
to prevent it. The difference this time is that it is uncommitted working-tree
churn, so `git log` does not show it and the next reader will never know it
happened.

**The freeze itself held at the commit level**: `git diff a4b80b1..HEAD --
':(exclude)docs/review/2026-09-22-goal-verification'` is empty `[test]`. The
breach is entirely uncommitted.

---

## Part 1 — The newcomer path

I started at `README.md` with the four questions in the brief and recorded every
backtrack.

| | Reachable from `README.md`? | Cost |
|---|---|---|
| (a) what this project is | **Yes, immediately** | Lines 1–50. Clean. |
| (b) how the hardware is structured | **Yes** | Layout tree at 102–107, then "Where to start reading" entry 2 → `hardware/README.md`. Good. |
| (c) where the authoritative value of a shared number lives | **No — not from `README.md`** | See G5-1. Depth 2 only, via a document the tree steers you away from. |
| (d) what to read before editing anything | **Partially** | See G5-10. |

### G5-1 — `README.md` never names `config/figures.yaml`, and misdescribes the directory it is in

**Highest reader cost in this report.**

`grep -n 'figures\|config/'` over `git show a4b80b1:README.md` returns exactly
one line `[test]`:

```
111:config/           Key layout and routing, as data
```

`config/` holds two files `[repo] config/`: `key-layout.yaml` **and
`figures.yaml`**. `figures.yaml` is the register that rule 1 of `CLAUDE.md` is
built on, that `hardware/README.md:100-105` calls one of "two rules that will
bite you", and that `repo-maintenance.md` §5 devotes a section to. Its own
header calls itself *"the single source of truth"* `[repo]
config/figures.yaml:1`.

The one file a newcomer opens first describes the directory containing it as
"Key layout and routing, as data" — a description of the *other* file — and
never names it. A reader scanning the layout tree for "where do shared numbers
live" is told, in effect, that `config/` is about keys.

It is reachable at depth 2: `README.md` → entry 2 → `hardware/README.md:100`
names it `[repo]`. So the path exists. But it is the single most important
convention in the repository and the tree actively points away from it.

This is the same defect class the README's own italic note at 136–140 records
about `hardware/README.md` having had zero inbound links — fixed for the page,
not for the file the page exists to protect.

### G5-2 — "`docs/review/` holds nine waves" is wrong, in the paragraph that exists to explain why counts are not restated

`README.md:115-121` `[repo]`:

> *(`docs/review/` and `datasheets/` were missing from this tree until
> 2026-09-21. `datasheets/` is the largest directory in the repository;
> `docs/review/` holds nine waves. […] The counts that used to sit in this
> sentence — "77 banked documents", "seven waves" — were true when written and
> wrong within the week, which is the whole reason this repository cites rather
> than restates.)*

At `a4b80b1` `[test]` (`git ls-tree -r --name-only a4b80b1 | grep docs/review`):

- **11** wave directories, not nine.
- Plus **1** loose file, `docs/review/2026-09-20-analog-design-review.md`,
  which is a wave record that is not a directory at all.

The sentence corrects two previously-stale counts and then restates a third in
the same breath. `CLAUDE.md`'s "Review waves" section says plainly: *"`ls -d
docs/review/*/` is the count. There is deliberately no number in this
sentence."* — and then names this as *"the third recorded instance of this
repository's named failure, in the paragraph that exists to describe that
failure."* It is now the fourth, one file over.

`datasheets/` **is** the largest directory — 58 M against `docs/` at 9.2 M
`[test] du -sh --exclude=.git */`. That half is correct.

---

## Part 2 — Do the structural claims hold?

I tested every structural claim in the four navigation documents. Results below,
failures first.

### G5-3 — Three documents give three different sizes for `hardware/unplaced.csv`, and none is right

| Document | Claim |
|---|---|
| `docs/reference/repo-maintenance.md:204` | *"`hardware/unplaced.csv` holds the **50 rows of 138** that no schematic page names"* |
| `hardware/README.md:112` | *"It was 50 rows and is **now 34**."* |
| **Measured** `[test]` | **32 rows of 140** |

`[test]`:
```
python3 -c "import csv; print(len(list(csv.reader(open('hardware/unplaced.csv',newline=''))))-1)"   # 32
python3 -c "import csv; print(len(list(csv.reader(open('hardware/bom.csv',newline=''))))-1)"        # 140
```

This is the signature defect at its purest: one quantity, three documents, three
values. The `hardware/README.md` figure (34) is the closer of the two and is
still wrong; the `repo-maintenance.md` figure (50) is the pre-reassignment value
that `hardware/README.md`'s own next paragraph explains was superseded.

Worse, `repo-maintenance.md`'s §4 blockquote ends with this italic admission
`[repo] docs/reference/repo-maintenance.md:210-213`:

> *This section described `bom.csv` as the file you edit for several hours after
> it stopped being one. Found by a cold reviewer. It is the project's named
> failure mode, in the document that exists to record exactly this trap.*

The paragraph that records the section going stale is itself in a section that
has gone stale again, three sentences above it.

### G5-4 — `repo-maintenance.md` contradicts itself about the hook, within one file

`§2, line 27` `[repo]`:

> Run by a `PreToolUse` hook before every `git commit`, so forgetting it is
> visible rather than silent.

`§6, lines 278-280` of the same file `[repo]`:

> though note `CLAUDE.md` §2: it runs before *every* `Bash` call rather than
> before `git commit`, and it never blocks, it only tells you.

`§6` is correct. `[repo] .claude/settings.json` confirms `"matcher": "Bash"`
with an `"if": "Bash(git commit *)"` sibling key that the hook schema does not
gate on, and the payload emits only `additionalContext` — no
`permissionDecision`. `CLAUDE.md` §2 describes this accurately.

A reader who reads §2 and stops — which is what §-numbered reference documents
are for — gets the wrong model of the one check that runs constantly. The fix
reached §6 and did not reach §2, which is `CLAUDE.md`'s recorded fix-shape
*"a fix that did not reach the pages citing it"*, one file over from itself.

### G5-5 — "24 per-circuit `bom.csv` fragments" matches nothing

`repo-maintenance.md:191` `[repo]`: *"`tools/merge-bom.py` rebuilds it from 24
per-circuit `bom.csv` fragments."*

Measured `[test]` (parsing `ORDER` out of `tools/merge-bom.py`):

- `ORDER` has **27** entries.
- Of those, **23** are per-circuit (one, `link-supervision`, is a declared
  no-parts entry with no file on disk — see G5-14).
- **3** are *board-level* fragments (`hardware/carrier/bom.csv`,
  `hardware/cluster/bom.csv`, `hardware/module/bom.csv`).
- **1** is `hardware/unplaced.csv`.
- **25** fragment files exist on disk `[test] find hardware -name bom.csv`.

22, 23, 25, 26 and 27 are all defensible readings. 24 is not any of them.

The arithmetic itself is sound: fragment rows sum to 108 placed + 32 unplaced =
**140**, exactly the master's row count `[test]`. The generator is consistent;
only the prose about it is wrong.

### G5-6 — §4's explanation of what is in `unplaced.csv` describes contents that are not there

`repo-maintenance.md:206-208` `[repo]`: *"Two of its clusters name circuits this
corpus has no page for — **six identical jack-protection networks** drawn three
times, and **nineteen decoupling capacitors** with no home."*

I dumped all 32 rows `[test]`. There is no jack-protection cluster and no
decoupling-capacitor cluster. Actual composition: `controller` 13,
`mechanical` 11, `module` 7, `tooling` 1. The largest single row is `CAP1-n`,
qty 21 — MT165-MX keycaps, not capacitors, despite the `CAP` prefix.

The sentence survived the reassignment that `hardware/README.md:112-120`
describes; its two examples were exactly the kind of row that got reassigned.

### G5-7 — `repo-maintenance.md` §7 asserts "every tracked file has a row"; 35 tracked files have no row

`§7:310-313` `[repo]`: *"`path-map-2026-09-21.csv` in this directory maps every
old path to its new one — **every tracked file has a row**, including the ones
that did not move, because the question a reader actually asks is 'did this path
change?'"*

And at 345-346: *"**Both assertions hold as of this writing**."*

I ran the four-line check the section itself specifies `[test]`:

```
tracked = set(git ls-files)
placed  = {r.new for r in rows if r.kind != "deleted"}
assert not (tracked - placed)      # FAILS: 35 files
assert not (placed - tracked)      # holds: 0
```

Result: **35 tracked files with no row**, all under `docs/review/2026-09-22-*`
(the two 2026-09-22 waves, 8 + 24 files, plus this wave's README). Zero rows
point at nothing.

**Judgement: this one is mild, and the document half-predicts it** — the very
next line says *"run it whenever files are added, because a new file is an
orphan the moment it is committed."* The absolute claim is nonetheless now
false, and the `created-history` kind exists precisely to absorb these. The cost
is small because the missing rows are all history, which nobody resolves paths
*into*.

### G5-8 — §7's row arithmetic no longer decomposes

`§7:323-324` `[repo]`: *"410 rows: **405 tracked files, plus 4 `deleted` and 1
duplicate destination**."*

Measured `[test]`: 410 rows total ✓. `kind` counts: `unmoved` 104,
`created` 95, `unmoved-history` 150, `created-history` 28, `moved` 29,
`deleted` 4. Non-deleted rows = 406. **Distinct** `new` paths among them = **406**.

A duplicate destination would make the distinct count 405 against 406 rows. It
does not. Either the duplicate was resolved and the sentence not updated, or
405+4+1 was never the decomposition. Low reader cost — nobody acts on it — but
it is a restated count that has moved under its sentence, which is one of
`CLAUDE.md`'s four named fix-shapes.

### G5-9 — `README.md`'s `docs/reference/` description promises a file that does not exist and omits three that do

`README.md:98` `[repo]`: `docs/reference/   Latency budgets, fingering notes, specs`

Actual contents `[test] git ls-tree -r --name-only a4b80b1 | grep docs/reference`:

| File | Covered by "Latency budgets, fingering notes, specs"? |
|---|---|
| `latency-budget.md` | yes |
| `ks33-geometry.md` | "specs", generously |
| `pcb-pipeline.md` | no |
| `repo-maintenance.md` | **no — and `README.md`'s own "Where to start reading" entry 5 calls it essential** |
| `path-map-2026-09-21.csv` | no |

There is **no fingering notes file** anywhere in `docs/reference/`
`[test] grep -ril fingering docs/reference/` → only incidental mentions inside
`ks33-geometry.md` etc., no such document. Fingering as data lives in
`config/key-layout.yaml` and ADR 0010 `[repo]`.

So the layout tree promises a document that has never existed, and omits
`repo-maintenance.md` — the file the same README tells you to read fifth. A
reader using the tree as an index does not find the maintenance rules there.

### G5-10 — `README.md` never mentions `CLAUDE.md`, and the layout tree omits `LICENSES/`

`[test] git show a4b80b1:README.md | grep -n CLAUDE` → no match.

`CLAUDE.md` is the answer to brief question (d) — "what to read before editing
anything". It is 14 kB of exactly that. From `README.md` it is reachable only at
depth 2, via "Where to start reading" entry 5 → `repo-maintenance.md:5`, which
says *"The corpus rules are in `CLAUDE.md`"* `[repo]`.

The layout tree at `README.md:95-113` also omits `LICENSES/` (3 tracked files)
and `CLAUDE.md` itself, while `README.md:89` links `LICENSE` and describes the
three-licence mapping. Tracked top-level entries `[test] git ls-tree --name-only
a4b80b1`: `.claude .gitignore CLAUDE.md LICENSE LICENSES README.md ROADMAP.md
config datasheets docs firmware hardware mechanical tools`. The tree covers 7 of
the 9 non-dotfile entries.

Mitigating: `CLAUDE.md` is agent-facing by convention, and a human newcomer
arguably does not need it. I still count it a gap, because the brief's question
(d) is a real question and `README.md` is where it gets asked.

### G5-11 — Three board-level `bom.csv` fragments exist and no corpus document mentions them

`[test]`:
```
grep -rn 'carrier/bom.csv\|cluster/bom.csv\|module/bom.csv' --include=*.md \
  hardware docs README.md CLAUDE.md | grep -v docs/review
→ NOT MENTIONED in any corpus .md
```

They are real and they carry real parts `[repo]`:

- `hardware/carrier/bom.csv` — 6 rows: `U-MCU-RT` (the ESP32-S3-Matrix),
  `PCB-CARRIER`, `MECH-COAT`, `HDR-DEV`, `WIRE-LOOM`, `SKT-BREATH`
- `hardware/module/bom.csv` — 4 rows: `R-OUT-PROT`, `R-OPAMP-IN`,
  `D-JACK-CLAMP`, `J-CV`
- `hardware/cluster/bom.csv` — 3 rows: `SW1-n` (the KS-33 switches),
  `PLATE-TOP`, `PCB-CLUSTER`

Both layout trees — `README.md:102-108` and `hardware/README.md:7-15` — show
`bom.csv` at exactly two levels: `<board>/<circuit>/bom.csv` (fragment) and
`hardware/bom.csv` (generated). The board level is a third, undocumented tier.

**Reader cost is real, because this is the `bom.csv` trap's blast radius.** The
rule a reader is given is "edit the fragment". A reader looking for the MCU or
the key switches finds them in a file at a path the documentation says does not
exist, and cannot tell from the docs whether it is a fragment (editable) or
generated (edit destroyed). It is a fragment — `ORDER` in `tools/merge-bom.py`
lists all three `[repo]` — but that is only discoverable by reading the tool's
source.

The assignment rule explains *why* they exist (a part whose value no single
circuit page derives), which is coherent. It is just never written down.

### G5-12 — `hardware/README.md` claims the `## Interfaces` definition was de-duplicated; all 23 pages still restate it

`hardware/README.md:47-49` `[repo]`:

> *(This definition sat inline in all 23 circuit pages until 2026-09-21 —
> twenty-three copies of one paragraph, in a repository whose first rule is
> state it once and cite it. It is here, and they cite it.)*

They do cite it. They also still restate it. **All 23** circuit pages carry this
169-character block `[test]`, matched against a whitespace-joined stream because
it hard-wraps (a line-based `grep` finds it in only 5 — the wrap trap
`CLAUDE.md` §2 documents, which is presumably how it survived):

> "Every net that crosses this circuit's boundary. Quantities appear **only** as
> a citation into `config/figures.yaml` — this table names nodes, it does not
> restate values."

The long 39-line version really did move; a condensed paragraph replaced it in
every page. The count of copies is unchanged at 23. The claim "it is here, and
they cite it" is half true and reads as fully true.

The four board-level overview pages (`carrier.md`, `cluster-boards.md`,
`module.md`, `interfaces/README.md`) do **not** restate it `[test]` — correctly.

---

## Part 3 — Convention conformance across all 23 circuits

Stated convention `[repo] hardware/README.md:7-15`: one circuit per directory
holding `<circuit>.md`, `bom.csv`, `circuit.yaml`, `notes.md`, and optionally
`sim/`.

Full enumeration `[test]`:

| Board | Circuit | `.md` | `bom.csv` | `circuit.yaml` | `notes.md` | `sim/` |
|---|---|---|---|---|---|---|
| carrier | breath-adc | ✓ | ✓ | ✓ | **—** | — |
| carrier | breath-excitation-reference | ✓ | ✓ | ✓ | ✓ | ✓ |
| carrier | display-and-service-uart | ✓ | ✓ | ✓ | **—** | — |
| carrier | led-strip-drive | ✓ | ✓ | ✓ | ✓ | — |
| carrier | power-entry-instrument | ✓ | ✓ | ✓ | **—** | — |
| cluster | key-marker-and-bits | ✓ | ✓ | ✓ | ✓ | — |
| cluster | key-register | ✓ | ✓ | ✓ | ✓ | — |
| cluster | key-switch-network | ✓ | ✓ | ✓ | **—** | — |
| interfaces | breath-sense-link | ✓ | ✓ | ✓ | ✓ | — |
| interfaces | key-chain-loom | ✓ | ✓ | ✓ | ✓ | — |
| interfaces | spi-link | ✓ | ✓ | ✓ | ✓ | — |
| module | breath-output-stage | ✓ | ✓ | ✓ | **—** | — |
| module | breath-receive-stage | ✓ | ✓ | ✓ | ✓ | ✓ |
| module | breath-response-shaper | ✓ | ✓ | ✓ | **—** | — |
| module | dac8568 | ✓ | ✓ | ✓ | ✓ | — |
| module | digital-and-supervision | ✓ | ✓ | ✓ | ✓ | — |
| module | link-supervision | ✓ | **—** | ✓ | ✓ | — |
| module | mod-channels | ✓ | ✓ | ✓ | ✓ | — |
| module | panel | ✓ | ✓ | ✓ | **—** | — |
| module | panel-led | ✓ | ✓ | ✓ | ✓ | — |
| module | pitch-stage | ✓ | ✓ | ✓ | ✓ | ✓ |
| module | power-entry | ✓ | ✓ | ✓ | **—** | ✓ |
| module | umbilical-load-switch | ✓ | ✓ | ✓ | ✓ | ✓ |

**23 of 23 have the page, 23 of 23 have `circuit.yaml`, 22 of 23 have
`bom.csv`, 15 of 23 have `notes.md`, 5 have `sim/`.**

### G5-13 — `notes.md` is absent in 8 of 23 and nothing says it is optional

Missing in: `carrier/breath-adc`, `carrier/display-and-service-uart`,
`carrier/power-entry-instrument`, `cluster/key-switch-network`,
`module/breath-output-stage`, `module/breath-response-shaper`, `module/panel`,
`module/power-entry` `[test]`.

Both trees present the four files as the unit, unqualified — `README.md:106`
and `hardware/README.md:13`. `CLAUDE.md`'s "Hardware conventions" likewise:
*"the page, its `bom.csv` fragment, its `circuit.yaml`, and `notes.md` for what
the circuit *used to be*."*

**Judgement: drift, but benign drift, and arguably correct.** A circuit with no
superseded history has nothing to put in `notes.md`, and an empty one would be
worse. The defect is not the missing files, it is that a reader cannot tell
"this circuit has no history" from "somebody forgot", because the convention is
stated absolutely. One clause — "`notes.md` when there is history to record" —
closes it. Cheap to fix, low cost while unfixed.

### G5-14 — `link-supervision`'s missing `bom.csv` is deliberate, and recorded only in a tool's source

`hardware/module/link-supervision/` has no `bom.csv` `[test] ls -la`. This is
**deliberate and well-reasoned** — `tools/merge-bom.py` carries an explicit
`NO_PARTS` dict `[repo] tools/merge-bom.py`:

```python
NO_PARTS = {
    "hardware/module/link-supervision/bom.csv":
        "the watchdog and presence detect are NOT FITTED - the page exists "
        "to record what was deleted and what restoring it would cost",
}
```

with a comment stating *"A circuit is in here because someone decided it owns
nothing — never because a file happened to be missing."* That is exactly right,
and the tool refuses a silently-absent fragment.

**The organisational defect is placement.** The one documented exception to the
directory convention lives in a Python dict in `tools/`, which is outside
`CORPUS_DIRS` `[repo] tools/check-staleness.py:30` and outside the §6 corpus.
A reader who notices the gap and looks in `hardware/README.md` — the page whose
title is "how this directory is organised" — finds nothing. `hardware/README.md`
has a "What is deliberately not here" section at 107-123 that discusses
`unplaced.csv` and does not mention this.

### G5-15 — Naming is internally consistent for circuits, and inconsistent for boards

**Circuits: clean, and worth saying so.** All 23 satisfy
`circuit.yaml: id == "<board>/<dir>"` and `page filename == "<dir>.md"`
`[test]`. Zero mismatches. `depends_on` `circuit:` edges use the same
`board/circuit` spelling `[repo] hardware/module/pitch-stage/circuit.yaml`. This
is the thing the brief flagged as "cheap to find and expensive to hit", and it
holds across all 23. Good.

**Boards: three conventions for four directories** `[repo]`:

| Directory | Overview page | Convention |
|---|---|---|
| `hardware/carrier/` | `carrier.md` | `<dir>.md` |
| `hardware/module/` | `module.md` | `<dir>.md` |
| `hardware/cluster/` | `cluster-boards.md` | `<dir>-boards.md` |
| `hardware/interfaces/` | `README.md` | `README.md` |

`hardware/README.md:19-22` links all four correctly, so following the link
works. Guessing does not: a reader who has learned `carrier/carrier.md` will try
`cluster/cluster.md` and `interfaces/interfaces.md` and miss twice. There is a
defensible reason for `interfaces/README.md` (it is a category, not a board) and
none I can find for `cluster-boards.md`.

---

## Part 4 — Orphans, dead ends, and name/content mismatches

**Link integrity: clean.** I resolved every relative Markdown link in every
corpus `.md` at `a4b80b1` against `git ls-tree`: **0 broken links** out of the
whole corpus `[test]`. Directory links and anchors handled. This is a genuinely
good result and I want it on the record, because it is the thing that most often
rots in a restructure.

**Inbound references: clean.** Strict path-reference analysis over 126 corpus
files finds exactly one file with zero inbound references — `LICENSE`, which is
linked from `README.md:89` as `` [`LICENSE`](LICENSE) `` and therefore only
missed by my `\.(md|csv|yaml|py|txt)$` extension filter `[test]`. **No genuine
orphans.**

### G5-16 — Two sibling review directories whose names differ by one word

`docs/review/2026-09-22-fix-audit/` (24 files, D1–D20) and
`docs/review/2026-09-22-fix-audit-review/` (8 files, E1–E4) `[test] ls`. They
are distinct waves — the second reviews the first, per `git log --oneline`
subjects on those paths `[repo]` — but the names do not say so. `-review` as a
suffix meaning "review *of* the preceding wave" is not a convention used
anywhere else; every other wave name describes its subject.

I did not read either directory (cold). Cost: any citation of the form
"the fix-audit wave" is ambiguous, and `tools/extract-findings.py <wave>` takes
a wave name as an argument.

### G5-17 — One wave is a loose file, so the documented way to count waves undercounts

`docs/review/2026-09-20-analog-design-review.md` is a single file at the top of
`docs/review/`, not a directory `[test] ls -p docs/review/ | grep -v /`.

`CLAUDE.md` states *"`ls -d docs/review/*/` is the count"*. That command returns
11 and there are 12 wave records. The prescribed instrument is off by one
because one record predates the directory convention. Either it should move into
a directory or the instruction should say so.

### G5-18 — `.staleness-report.txt` and `.staleness/report.txt` are different files with near-identical names

`[repo]` both exist, both gitignored `[repo] .gitignore:1-2`. The first holds
the one-line summary; the second holds the detail. The hook has to carry a
correction in its own output to stop readers going to the wrong one `[repo]
.claude/settings.json`:

> Detail is in .staleness/report.txt (**NOT .staleness-report.txt**, which holds
> only this summary)

A parenthetical disclaimer inside every hook message is the tell that the names
are wrong. `.staleness/summary.txt` + `.staleness/report.txt` costs nothing and
removes the disclaimer.

### G5-19 — `path-map-2026-09-21.csv` is a historical record filed in the design corpus

`repo-maintenance.md` §1 classifies `docs/reference/**` as **Design corpus** —
*"Must be self-consistent. This is what `check-staleness.py` checks"* — and
classifies history as `docs/review/**`, `docs/log/**`, `docs/research/**`
`[repo] docs/reference/repo-maintenance.md:15-16`.

`path-map-2026-09-21.csv` is a dated snapshot of one restructure, 410 rows, with
`unmoved-history` and `created-history` `kind` values and an `old` column full
of retired paths `[test]`. It is history by content and corpus by location.
`check-staleness.py` scans it: `CORPUS_DIRS` includes `docs/reference` and
`EXCLUDE` is only `("docs/review", "docs/log", "docs/research")`
`[repo] tools/check-staleness.py:30-32`.

Consequence under `CLAUDE.md` §2b: it is a `.csv`, so *"a forbidden value is a
defect, full stop: no window, no vocabulary, no argument."* A retired path is not
a number so nothing fires today, but any future figure whose old spelling
happens to appear in a filename or a `note` cell would be an unfixable failure —
the file's whole purpose is to hold retired strings.

It is also the only dated filename in `docs/reference/`, which is otherwise
timeless reference material.

### G5-20 — Two vestigial `.gitkeep` files

`tools/.gitkeep` sits beside 8 real tools, and `docs/research/.gitkeep` beside a
populated wave directory `[test] git ls-files | grep gitkeep`. Both directories
have been non-empty for some time. (The three under `mechanical/` are correct —
those directories are genuinely empty.)

Trivial cost. Listed because the brief asks for "directories with one stray
file" and these are the residue of the opposite.

### G5-21 — `module/panel/` and `module/panel-led/` are adjacent and easily confused

Not a defect — both are legitimate circuits and both pages open by saying what
they are `[repo] hardware/module/panel/panel.md:1-8`,
`hardware/module/panel-led/panel-led.md:1-4`. `panel.md` is panel *geometry*
(width, control rows, knob sizes); `panel-led.md` is one resistor and one LED.

I flag it only because tab-completion and `grep panel` both hit the wrong one
first, and `panel.md`'s own header records that it *used to* claim it was not a
circuit at all. Reader cost is one backtrack, once.

**Name/content mismatches found: none serious.** `pcb-pipeline.md` is a pipeline
design document, correctly named. `cluster-boards.md` describes cluster boards.
`link-supervision.md` describes supervision that is deleted, which is what its
`notes.md` and the `NO_PARTS` entry both say.

---

## Part 5 — Duplication

I ran an exact-duplicate-block detector over every corpus `.md` (blocks ≥140
characters, whitespace-normalised so hard wraps do not hide a match) `[test]`.
**8 distinct duplicated blocks, 43 total copies.** Ranked by cost.

### G5-22 — The `## Interfaces` definition: 23 copies

Covered as G5-12. Locations: all 23 circuit pages. 169 characters each.

### G5-23 — `sim/README.md` boilerplate: 5 copies, two blocks

All five `sim/` directories `[repo]`:
`hardware/carrier/breath-excitation-reference/sim/README.md`,
`hardware/module/breath-receive-stage/sim/README.md`,
`hardware/module/pitch-stage/sim/README.md`,
`hardware/module/power-entry/sim/README.md`,
`hardware/module/umbilical-load-switch/sim/README.md`.

- A 418-character block beginning *"That is the rule, not an apology:
  `docs/reference/pcb-pipeline.md` names five simulations worth running and
  records that none has been…"* — **5 copies**, at line 6 of each.
- A 152-character block *"**Nothing here has been run.** This directory holds
  the deck and the procedure…"* — **5 copies**, at line 3 of each.
- A 467-character toolchain table (`ngspice` 42, "Do not use PySpice 1.5…") —
  **2 copies**, `pitch-stage/sim/README.md:29` and
  `breath-excitation-reference/sim/README.md:39`.

10 lines are common to all five files `[test]`. The toolchain table is the
dangerous one: it is a live instruction about which simulator to use, restated
in two places, and absent from the other three — so a reader in
`power-entry/sim/` is not told about the PySpice trap at all.

### G5-24 — The `notes.md` "superseded shelf" preamble: 7 copies in **two** spellings

This is the worst-shaped duplication in the repository, because the copies have
already diverged.

**Spelling A** (355 chars), 5 copies `[repo]`:
`module/breath-receive-stage/notes.md:6`, `module/mod-channels/notes.md:6`,
`module/pitch-stage/notes.md:6`, `carrier/led-strip-drive/notes.md:7`,
`carrier/breath-excitation-reference/notes.md:8` — opening
*"This is the circuit's superseded shelf — **the same convention**
`docs/decisions/README.md` runs at project scope, **one level down**."*

**Spelling B** (341 chars), 2 copies `[repo]`:
`module/umbilical-load-switch/notes.md:7`, `module/panel-led/notes.md:7` —
opening *"This is the circuit's superseded shelf, **on the same convention**
`docs/decisions/README.md` runs at project scope."* — em-dash → comma, and
*"one level down"* dropped.

Seven copies of one paragraph that has already drifted into two variants is the
state immediately before a fix reaches five files and misses two. No
whitespace-normalised grep finds both; a reader fixing A will not match B.

### G5-25 — The KS-33 footprint table: 2 copies, and they have already gone out of sync

`docs/reference/ks33-geometry.md:170` and `hardware/cluster/cluster-boards.md:128`
carry the identical table `[test]`:

| Feature | Position | Size |
|---|---|---|
| Centre pole | (0, 0) | ⌀5.0 mm |
| Pin 1 | (2.6, 5.75) | ⌀1.5 mm drill |
| Pin 2 | (−4.4, 4.7) | ⌀1.5 mm drill |

`cluster-boards.md` cites `[repo] ks33-geometry.md` three times in the
surrounding paragraphs and *then restates the table anyway* — rule 1 broken with
the citation sitting right next to it.

**It is already stale in the direction that matters.** `ks33-geometry.md`
continues immediately after its copy `[repo] docs/reference/ks33-geometry.md:176-180`:

> **Independently confirmed 2026-09-21** by a second footprint from a different
> library […] same two pin positions, drill **⌀1.2** rather than ⌀1.5, centre
> pole **⌀5.25**

`cluster-boards.md`'s copy carries none of that. A reader on the cluster page —
the page you are on when you are laying out a cluster board — gets ⌀1.5 and
⌀5.0 with no indication that a second independent source says ⌀1.2 and ⌀5.25.
These are drill diameters. This is the highest-consequence duplication I found.

Neither number is in `config/figures.yaml` `[test] grep -n '5.0 mm\|1.5 mm
drill' config/figures.yaml` → no match, so nothing tracks it.

### G5-26 — The Phase B split banner: 4 copies

155 characters, verbatim, at line 3 of `carrier/breath-adc/breath-adc.md`,
`carrier/breath-excitation-reference/breath-excitation-reference.md`,
`carrier/display-and-service-uart/display-and-service-uart.md`,
`carrier/led-strip-drive/led-strip-drive.md` `[test]`:

> **Status:** Split out of `carrier.md` 2026-09-21 (Phase B). Every line below
> was moved verbatim; nothing was reworded and no value was touched in the move.

**Judgement: acceptable, and arguably correct.** It is a per-file provenance
statement, and a provenance statement belongs on the file it describes. I list
it for completeness rather than as a defect. Note `module/panel-led/panel-led.md`
makes the same statement in its own wording `[repo]` — a fifth near-copy.

### G5-27 — The repository's own tool reports 211 restated-not-cited values

`.staleness/report.txt` `[test]`, under `RESTATED, NOT CITED (211) - ADVISORY`:
*"A value written out in three or more files with no entry in the register. This
is the state every staleness defect in this repository grew from."*

Top entries: `3.3 V` in 19 files, `1.25 mm` in 17, `0.1 %` in 14, `20 K` in 12,
`20 mm`/`265 mm`/`47 nF`/`5.5 V`/`500 Hz` in 11 each.

This is duplication measured by the project's own instrument, and it dwarfs
everything I found by reading. 37 figures are tracked; 211 values are restated
across three or more files and tracked by nothing. I did not assess which are
genuine single quantities versus coincidental string matches — that needs the
domain slices, not me. I report the number because the brief asked for
duplication and this is where the mass of it is.

---

## What is genuinely well organised

Stated for balance, all verified:

1. **The 23-circuit directory scheme is real and complete.**
   `hardware/README.md:19-22` claims carrier 5, cluster 3, module 12,
   interfaces 3. Measured: **5, 3, 12, 3 — exact** `[test]`. Every one has its
   page and its `circuit.yaml`.
2. **Circuit naming is perfectly consistent** across dirname, page filename,
   `circuit.yaml` `id:`, and `depends_on` `circuit:` edges, 23 for 23 `[test]`.
3. **Zero broken relative links** in the entire corpus `[test]`.
4. **Zero orphan files** in the corpus under strict path-reference analysis
   `[test]`.
5. **The ADR index is correct.** All 14 rows agree with their ADR's
   `**Status:**` line `[test]` — including 0007, 0008 and 0011, the three
   `docs/decisions/README.md` admits were wrong on 2026-09-21. A fix that
   actually landed and has stayed landed.
6. **`README.md`'s "three tracks"** is right: ROADMAP has Track E, Track M,
   Track F `[test] grep -oE 'Track [A-Z]' | sort -u`.
7. **`repo-maintenance.md` §3's "all 60 banked PDFs"** is right:
   `find datasheets -name '*.pdf' | wc -l` → **60** `[test]`.
8. **The BOM generator is arithmetically sound**: 108 fragment rows + 32
   unplaced = 140 master rows `[test]`, 11 columns as documented.
9. **`sim/` appears in exactly 5 circuits**, matching the "five simulations
   worth running" that `pcb-pipeline.md` names `[repo]`. Deliberate, not drift.
10. **`hardware/interfaces/`** is the best-argued directory in the repository.
    `interfaces/README.md` explains *why* these three are not filed under a
    board — "their numbers cannot be derived from one side" — with a worked
    example. That is what a structural document should look like.

The restructure's core claim — one circuit per directory, navigable, no dead
links, no orphans — **holds**. What has not held is the prose *describing* it:
every failure in Part 2 is a sentence about the structure, not the structure.

---

## What I could not check

- **Anything inside `docs/review/`.** Cold rule. So I cannot say whether these
  findings duplicate earlier ones, whether the counts in G5-2/3/5/7/8 were
  already filed, or whether `2026-09-22-fix-audit` vs `-fix-audit-review` is
  explained inside either README.
- **Whether the 211 restated-not-cited values are genuine shared quantities.**
  Needs domain knowledge per value.
- **Whether `unplaced.csv`'s 32 rows are the right 32.** I counted them; I did
  not verify that each is genuinely underived by any page.
- **Semantic orphaning** — a page depending on a deleted part or an argument
  surviving its refutation. `CLAUDE.md` §5's territory, and not mine.
- **`datasheets/` internal organisation.** I counted PDFs and MANIFEST rows
  (102 lines) and checked the "largest directory" and "60 PDFs" claims. I did
  not verify the category directories, run `verify-datasheets.py`, or check
  fragment/manifest consistency.
- **`mechanical/` and `firmware/`** are effectively empty (3 `.gitkeep` files
  and 1 README respectively) `[test]`, so there is no organisation to judge.
  Both READMEs describe future structure honestly.
- **Whether my measurements match what other slices see.** Given G5-0, they may
  not. All mine are pinned to `a4b80b1` blobs.

---

## Ranked summary

**Costs a reader the most**

1. **G5-1** — `README.md` never names `config/figures.yaml` and misdescribes
   `config/`. The repository's central convention is invisible from its front door.
2. **G5-25** — KS-33 footprint table duplicated and already diverged; the cluster
   page gives drill ⌀1.5 where the geometry page now says ⌀1.2, untracked.
3. **G5-3** — `unplaced.csv` size stated as 50, 34 and (actually) 32 across three
   documents.
4. **G5-2** — "nine waves"; there are 11 directories and a 12th loose record.
5. **G5-4** — `repo-maintenance.md` §2 contradicts §6 about the hook.

**Costs a reader real time**

6. **G5-11** — three undocumented board-level BOM fragments, inside the
   generated-file trap's blast radius.
7. **G5-12** — de-duplication claimed, 23 copies remain.
8. **G5-24** — `notes.md` preamble, 7 copies in 2 already-diverged spellings.
9. **G5-9** — `docs/reference/` described as holding a file that does not exist
   while omitting `repo-maintenance.md`.
10. **G5-5**, **G5-6** — `repo-maintenance.md` §4's fragment count and cluster
    examples both describe a state that no longer exists.
11. **G5-10** — `CLAUDE.md` unreferenced from `README.md`.

**Cheap to fix, small standing cost**

12. **G5-23** simulator boilerplate ×5 and the toolchain table in only 2 of 5.
13. **G5-15** three board-page naming conventions for four directories.
14. **G5-13** `notes.md` absent in 8 of 23 with no "when there is history" clause.
15. **G5-14** the one documented convention exception lives in a Python dict.
16. **G5-16**, **G5-17** review-directory naming and the loose wave record.
17. **G5-18** `.staleness-report.txt` vs `.staleness/report.txt`.
18. **G5-7**, **G5-8**, **G5-19**, **G5-20**, **G5-21**, **G5-26**.

**Wave-method, not corpus**

- **G5-0** — the freeze is being breached, uncommitted, by slice G10, in
  `README.md`, `tools/check-staleness.py` and at least one `circuit.yaml`, while
  this wave runs.

**Verdict.** The structure is good and the documents about the structure are
not. Every navigation document in this repository describes a layout slightly
older than the one on disk — which is the project's named failure mode operating
at the navigation layer, exactly as the brief predicted. A newcomer can find the
hardware; a newcomer cannot find `figures.yaml`.
