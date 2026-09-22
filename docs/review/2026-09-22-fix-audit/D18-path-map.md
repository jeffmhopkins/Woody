# D18 — `docs/reference/path-map-2026-09-21.csv` and `repo-maintenance.md` §7

Slice: is the path map true, does it do the job `CLAUDE.md` §6 assigns it, and
will it stay true. Report only; nothing in the corpus was changed.

Provenance markers: `[repo]` file:line, `[git]` revision, `[test]` command and
output, `[calc]` arithmetic shown.

**Headline.** The map's *content* is in good shape — the old side is an exact
bijection onto `81c081d`, all 22 datasheet corrections are right including the
two filename renames, and the `deleted` classification is defensible. What is
not in good shape is the *assertion* wrapped around it: two of §7's stated
counts are wrong, one of its coverage assertions is already false at HEAD, and
nothing in the repository runs the four-line check §7 tells a maintainer to
run. The map broke again **one commit after** §7 declared it whole.

---

## 1. The four-line check, run

`[test]` §7's check, transcribed to Python and run against HEAD (`092b364`):

```
tracked 407  placed 406
tracked - placed : ['docs/review/2026-09-22-fix-audit/README.md']
placed - tracked : []
```

**Assertion 1 FAILS at HEAD.** One tracked file has no row.

`[git]` It was added by `092b364` "Open the fix-audit wave" — the commit
immediately after `04b5208`, which is the last commit of the fix batch this
wave audits. §7's own text was finalised at `79f5c4a`, two commits earlier.

`[test]` Running the same check at each commit in the batch:

| rev | tracked | orphans | dangling |
|---|---|---|---|
| `b32c557` (before the fix) | 406 | **144** | **22** |
| `c65083d` (the fix) | 406 | **1** (`datasheets/.manifest-R9.csv`) | 0 |
| `79f5c4a` (§7 rewritten) | 406 | 0 | 0 |
| `04b5208` | 406 | 0 | 0 |
| `092b364` = HEAD | 407 | **1** (fix-audit `README.md`) | 0 |

The map was whole for exactly two commits.

### D18-1 — §7 asserts coverage that is false at HEAD `[live defect, low severity, high diagnostic value]`

`[repo] docs/reference/repo-maintenance.md:294-296` states, unhedged and in the
present tense:

> **`path-map-2026-09-21.csv` in this directory maps every old path to its new
> one** — every tracked file has a row, including the ones that did not move

That sentence is false at HEAD. The blockquote's "Both assertions hold as of
this writing" is *honest* — it was true when written `[git] 79f5c4a` — but it
is the hedged copy of the claim, and the unhedged copy sits four paragraphs
above it where the reader meets it first. This is the corpus's named failure
mode with a path as the value: the owning document states it, the derived
statement does not follow.

Note also that **this report's own file is orphan number two** the moment it
lands, and every further report in this wave adds one.

---

## 2. The two counts in §7 are wrong

### D18-2 — "405 tracked files, plus 4 `deleted` and 1 duplicate destination" `[live defect]`

`[repo] docs/reference/repo-maintenance.md:304-306`:

> - **New side** — HEAD, reconciled against `git ls-files` on 2026-09-21 after
>   the pre-merge review wave closed. 410 rows: 405 tracked files, plus 4
>   `deleted` and 1 duplicate destination.

`[test]` measured on the map as it stood at `79f5c4a`, the commit that wrote
that sentence:

```
rows 410  kinds: unmoved-history 150, unmoved 104, created 95,
                 moved 29, created-history 28, deleted 4
non-deleted rows 406   distinct `new` values 406   duplicates: []
tracked at 79f5c4a: 406   orphans: []   dangling: []
```

`[calc]` 406 + 4 = 410. The sentence's 405 + 4 + 1 also sums to 410, which is
why it looks right, but **both of its parts are wrong**: there are 406
non-deleted rows, not 405, and **there is no duplicate destination at all** —
every `new` value in the file is unique.

The most likely origin, offered as a hypothesis rather than a finding: a draft
in which the WS2815 de-duplication was a second `moved` row onto
`datasheets/led/WS2815.pdf` (which is exactly how `datasheets/.moves.csv`
records it, `[repo] datasheets/.moves.csv:23`). That draft would have had 411
rows, 407 non-deleted, and one genuine duplicate destination. The row was then
reclassified `deleted` (see §4 below) and the prose count was not re-derived.
Whatever the cause, the number describes a file that is not the one in the
repository.

### D18-3 — "143 tracked files with no row" is 144 `[live defect, minor]`

`[repo] docs/reference/repo-maintenance.md:311-313` says the pre-fix state was
"**143 tracked files with no row and 22 rows whose `new` path existed on
*neither* side**".

`[test]` at `b32c557`, the commit before the fix: **144** orphans, 22 dangling
rows (all under `datasheets/`, all `kind=unmoved` — the 22 are confirmed, and
confirmed to have claimed `unmoved`).

The 143 is not a miscount of the defect; it is an accurate count of the *rows
the fix added*. `[test]` at `c65083d` exactly one orphan remained —
`datasheets/.manifest-R9.csv` — and it was patched one commit later at
`79f5c4a`. So §7 reports the size of its own fix as the size of the problem,
and the difference between the two numbers is precisely the file the fix
missed. A reader auditing that paragraph against the tree gets 144 and cannot
tell whether they or the document are wrong.

---

## 3. The 22 datasheet rows, and whether `.moves.csv` is trustworthy

**All 22 verify. `[test]`** Each of the 21 `moved` rows was checked on four
axes: `old` present at `81c081d`, `old` absent from disk now, `new` present on
disk now, and the file's bytes identical across the move. Plus a set equality
against `datasheets/.moves.csv`.

```
moves rows: 22      map datasheet moved/deleted rows: 22      mismatches: 0
```

Both filename renames are correct in the map and carry an explicit flag
`[repo] docs/reference/path-map-2026-09-21.csv:83-84` (sorted, TI on 84):

```
datasheets/other-semi/74HC165.pdf         -> datasheets/logic/74HC165-ti-scls116e.pdf
datasheets/other-semi/74HC165-toshiba.pdf -> datasheets/logic/74HC165-toshiba-1986-excerpt.pdf
```

both with `FILE ALSO RENAMED, the basename is not preserved` in the note. §7's
argument for correcting from `.moves.csv` rather than from directory names is
**sound and load-bearing** — a directory-based correction would have produced
`datasheets/logic/74HC165.pdf` and `datasheets/logic/74HC165-toshiba.pdf`,
neither of which exists, and the `placed - tracked` assertion is the only thing
that would ever have caught it.

### Is `.moves.csv` itself trustworthy? Yes, and on stronger grounds than §7 gives.

1. `[test]` It is *complete and exact* against git. Between `81c081d` and HEAD,
   22 files disappear from `datasheets/` and 23 appear; the 22 disappearances
   are exactly `.moves.csv`'s 22 `old_path` values, and 21 of the 23
   appearances are exactly its 21 distinct `new_path` values. The other two
   appearances are `.moves.csv` itself and `.manifest-R9.csv`, both of which
   have `created` rows in the map.
2. `[repo] tools/merge-manifests.py:54-82` It is **machine-consumed and
   machine-validated** on every manifest merge: header shape, column count,
   empty paths, a path mapped to two destinations, and chained moves each
   produce `REFUSING TO WRITE`. It is not a hand-maintained note that happens
   to be right; it is an input with a guard on it.
3. `[test]` `python3 tools/verify-datasheets.py` → `78 verified, 23 recorded as
   blocked or not-fetched, 0 problems`, and `[repo] datasheets/MANIFEST.csv:56`
   shows the generated manifest already resolving the retired
   `mechanical/WS2815-worldsemi-datasheet.pdf` path through `.moves.csv` to
   `led/WS2815.pdf`.

§7 calls `.moves.csv` "the authority ... not anyone's memory". It is better
than that: it is the only path record in the repository that a tool refuses to
proceed on when it is malformed. Worth saying so in §7, because a reader
currently has no reason to trust it beyond the assertion.

---

## 4. The `deleted` WS2815 row

### SHAs verified `[test]`

```
git blob at 81c081d:datasheets/mechanical/WS2815-worldsemi-datasheet.pdf
  = 9654b8841d47fd01891f2eaa5374fd6344249949
git blob at 81c081d:datasheets/other-semi/WS2815.pdf
  = 9654b8841d47fd01891f2eaa5374fd6344249949
git blob at HEAD:datasheets/led/WS2815.pdf
  = 9654b8841d47fd01891f2eaa5374fd6344249949

sha256 of all three = 72e22d2f740c561db3cd82db1915dad35c546f5e7551b896000445fa4b3ca957
```

The row's note `[repo] docs/reference/path-map-2026-09-21.csv:80` cites
`sha 72e22d2f740c`, which is the correct prefix of that digest, and names
`datasheets/led/WS2815.pdf` as the survivor. **The claim is exactly true**:
identical git blob hash, identical SHA-256, and byte-identical to the file
still banked. `[repo] datasheets/MANIFEST.csv:56-57` confirms the collapse —
two manifest rows (from fragments R2 and R6) now both cite `led/WS2815.pdf`
with that same digest.

### Was `deleted` the right classification?

**Yes, on balance, but the reasoning is not the one §7 implies and the
alternative is not dangerous.**

`[test]` I built the alternative in a sandbox — the row rewritten as
`datasheets/mechanical/WS2815-worldsemi-datasheet.pdf,datasheets/led/WS2815.pdf,moved`
— and ran `python3 tools/rewrite-paths.py --verify`: `0 surviving old-side
token(s)`, exit 0. The only live occurrence of the old token is
`[repo] datasheets/.manifest-R6.csv:13`, and `.manifest-R` is in
`rewrite-paths.py`'s `HISTORY` tuple `[repo] tools/rewrite-paths.py:46-47`, so
it is never rewritten and never reported. `--invert` would also pass, without
needing to be run: the destination is a PDF, so `unrewrite` hits
`UnicodeDecodeError` and compares raw bytes `[repo] tools/rewrite-paths.py:197-199`,
and those bytes are identical to the baseline file by the hashes above.

So the `moved` form is *mechanically harmless*. The arguments that still favour
`deleted`:

- **It is what happened.** `[git] git diff --name-status -M 81c081d HEAD --
  datasheets/mechanical/` reports `D`, a plain deletion, because git attributed
  the rename to `other-semi/WS2815.pdf → led/WS2815.pdf`. One of the two
  duplicates moved and one was removed; `deleted` says that and `moved` does
  not.
- **`moved` is defined as rewritable** `[repo] docs/reference/repo-maintenance.md:352`
  ("Rewritable: `rewrite-paths.py` reads exactly these rows"). There is nothing
  in the rewritable set to rewrite — the sole live occurrence is inside a
  frozen manifest fragment — so a `moved` row would be a standing instruction
  to rewrite a token that must never be rewritten.
- **It keeps the destination set injective**, which is what makes
  `len(placed) == len(tracked)` a usable equality rather than an inequality
  with an explanation attached.

The argument *against*, which should be recorded: a `deleted` row's `new` is
empty, so a reader scanning the `new` column for a destination finds none and
must read the prose note. `[test]` In practice this works — the note names
`datasheets/led/WS2815.pdf` in full, and the token resolves in the sample below
— but it is the one row in the file whose answer is only in prose. If §7's
`deleted` table entry `[repo] docs/reference/repo-maintenance.md:353` said "the `note` names the survivor **in full**" rather
than "if anywhere", the contract would be tighter. Not a defect.

---

## 5. `created` / `created-history`, and whether `rewrite-paths.py` survives an empty `old`

### The mechanism is safe, and the guard is doing real work `[test]`

`[repo] tools/rewrite-paths.py:83-85`:

```python
old, new = r["old"].strip(), r["new"].strip()
if not old or not new or old == new:
    continue
```

`[test]` `load_map()` at HEAD returns **29 pairs, no empty keys, no empty
values**, from a 410-row file containing 95 `created` and 28 `created-history`
rows. `[test]` `python3 tools/rewrite-paths.py --apply` on a pristine sandbox
copy of HEAD: `apply: 0 file(s) rewritten from 29 mapped moves` — no file
touched. `--verify` on the live tree: `0 surviving old-side token(s)`, exit 0.

The guard is not decorative. `[test]` Removing just the `not old` clause and
rewriting a single 44-character line:

```
input : "see hardware/module/power-entry.md for details"          (44 chars)
output: 1356 chars, beginning
        'tools/rewrite-paths.pystools/rewrite-paths.pyetools/rewrite-paths.p…'
```

`str.replace("", x)` inserts `x` between every character. An empty `old` that
reached `rewrite()` would destroy every rewritable file in the corpus on the
first `--apply`. The map has 123 rows with an empty `old`; the one-line guard
is all that stands between them and that.

### D18-4 — §7's justification names the one example where the harm cannot happen `[precision defect, no fix required to the map]`

`[repo] docs/reference/repo-maintenance.md:357-361`:

> `hardware/module/panel-led/panel-led.md` was split out of
> `hardware/module/power-entry.md`, but power-entry has its own `moved` row,
> and putting a second old→new pair on the same old path would make
> `rewrite-paths.py` rewrite every reference to power-entry into a page about
> the LED.

**The conclusion is right. The stated mechanism is not, and the named example
is the safe one.** `load_map()` returns a `dict` keyed on `old`, so two rows
sharing an `old` do not both survive — the later one in file order silently
overwrites the earlier, and the pair count does not change.

`[test]` Filling `panel-led.md`'s `old` with `hardware/module/power-entry.md`
in a sandbox copy:

```
pairs: 29   (not 30)
hardware/module/power-entry.md -> hardware/module/power-entry/power-entry.md
rows in the CSV with that old: 2
```

The map is sorted by `new`, and `hardware/module/panel-led/…` sorts *before*
`hardware/module/power-entry.md`'s row at line 392, so the correct `moved` row
always wins. §7's feared outcome cannot occur for its own example.

`[test]` It can occur for a sibling. Filling the `old` of
`hardware/module/umbilical-load-switch/umbilical-load-switch.md` (line 400,
which sorts *after* line 392) with the same parent:

```
pairs: 29
hardware/module/power-entry.md -> hardware/module/umbilical-load-switch/umbilical-load-switch.md
```

Every reference to power-entry is now rewritten to the load-switch page. And
`[git] git diff -M 81c081d HEAD` detects exactly this pair as a rename
(`hardware/module/power-entry.md -> hardware/module/umbilical-load-switch/umbilical-load-switch.md`),
so it is the split a future maintainer is *most* likely to want to record.

The real hazard is therefore **worse than §7 describes** — it is silent, it is
order-dependent, and the file-order rule that decides it is invisible — and §7
demonstrates it on the case where it is inert. Recommend restating the reason
as: *a duplicate `old` is silently collapsed by `load_map`'s dict, so which
destination wins is decided by CSV sort order and nothing reports the loss.*
Recommend also that whatever check is added (§7 below) assert `old` uniqueness
over non-empty `old` values. `[test]` It holds today: 287 non-empty `old`
values, 287 distinct.

### D18-5 — `created-history` notes do not name a commit, contra the table `[nit]`

`[repo] docs/reference/repo-maintenance.md:355` defines `created-history` as
"Same [as `created`], under `docs/review/**`", and `created` as "The `note`
names the commit". `[test]` All 95 `created` rows name a commit and **all 95
check out** against `git log --diff-filter=A` (including the two
`bom.csv` fragments at lines 369 and 384, whose notes correctly distinguish
`c483829` from "backfilled in `0e68f25`" — that pair is right, and `0e68f25`
is indeed the only commit that adds them). All 28 `created-history` rows name
a **wave directory** instead:

```
25 × "created after the map was written: 2026-09-21-pre-merge-review. …"
 3 × "created after the map was written: 2026-09-21-restructure-design. …"
```

The wave name is arguably more useful to a reader than a hash. The table
should say so rather than promising a commit.

---

## 6. Does it do its job? — the resolution measure

This is the measure the slice brief calls the only one that matters, and it
had not been run. Method: extract every path-shaped token
(`re: [\w.-]+(/[\w.-]+)+\.(md|csv|yaml|py|pdf|json|step|txt|kicad_pcb|sch)`)
from all 167 tracked `.md`/`.csv`/`.txt` files under `docs/review/**` and
`docs/log/**`, then resolve each against the map as a reader would: exact hit
on the `old` column first, then exact hit on `new`, then unique suffix match.

`[test]` Population: **429 distinct tokens, 6,027 occurrences.**

| outcome | distinct | occurrences | share of occurrences |
|---|---|---|---|
| exact hit on `old` — map answers directly | 98 | 4,667 | 77.4% |
| exact hit on `new` — post-restructure path, no change needed | 84 | 846 | 14.0% |
| unique suffix match — resolves, reader must supply the prefix | 123 | 281 | 4.7% |
| ambiguous suffix | 1 | 24 | 0.4% |
| no match anywhere | 123 | 209 | 3.5% |

**91.4% of path references in the historical record resolve with no effort;
96.1% resolve.** `[test]` A seeded 20-token sample drawn in proportion to
occurrence (`random.seed(20260922)`) gives 17 exact hits, 2 suffix
resolutions (`connectors/NE8FDP.pdf`, `module/breath-receive-stage.md`), and
one miss (`ROOT/datasheets/MANIFEST.csv`, which is a placeholder in a tool
description, not a path). **19 of 20.**

Where the remainder goes, which matters more than the percentage:

- **The suffix bucket is almost entirely `datasheets/`-relative spellings.**
  `other-semi/WS2815.pdf` (11×), `texas-instruments/OPA2197.pdf` (5×),
  `mechanical/WS2815-worldsemi-datasheet.pdf` (8×) and about forty more are
  written the way `MANIFEST.csv`'s `file` column writes them — relative to
  `datasheets/`. §7 already flags that `.moves.csv` uses that convention
  `[repo] docs/reference/repo-maintenance.md:340-343`, but the map's keys are
  repo-root paths, so these do not resolve by lookup. **A one-sentence note in
  §7 — "a `datasheets/`-relative path in a record needs the `datasheets/`
  prefix before you look it up" — would move ~4% of all references from
  *resolves with effort* to *resolves*,** and it is the cheapest improvement
  available to this map.
- **The one ambiguous token is `sim/README.md` (24 occurrences)**, which
  suffix-matches five rows (`breath-excitation-reference`,
  `breath-receive-stage`, `pitch-stage`, `power-entry`,
  `umbilical-load-switch`). A reader must use surrounding context. Inherent to
  the bare filename, not a map defect.
- **The 123 no-match tokens are overwhelmingly not repository paths**: vendor
  URLs (`ti.com/lit/ds/symlink/ref5050.pdf`,
  `www.farnell.com/datasheets/47249.pdf`), third-party repos, and
  ellipsis-elided paths (`.../symlink/ref5045.pdf`,
  `docs/research/.../R10-keyscan-and-adc.md`). `[test]` The four that look like
  repo paths — `tools/check-bom-parity.py` (5×), `hardware/OPEN.md` (6×),
  `.staleness/report.txt` (26×), `pcb/module/module.kicad_pcb` (10×) — return
  **nothing from `git log --all`**: none has ever been a tracked file. Three
  are proposals; `.staleness/report.txt` is a real live path but is generated
  and untracked, and the map's domain is tracked files. No map defect, but
  worth one line in §7 that the map covers tracked files only, since
  `.staleness/report.txt` is the single most-cited unresolvable token in the
  record.

**Verdict on the job: it does it.** The map is the documented mechanism for
reading nine waves of review history, and measured against real usage it
answers nine references in ten on the first lookup. That is the strongest thing
in this slice and it deserves to be in §7 as a measured number rather than left
unstated.

---

## 7. Maintainability — D18-6, the structural finding `[live gap]`

§7 says, correctly and in its own voice:

> **A map is not a document you keep true by being careful, it is one you
> assert.** … run it whenever files are added, because a new file is an orphan
> the moment it is committed

`[test]` **Nothing runs it.** `grep -rn 'path-map' --include='*.py'
--include='*.json' --include='*.sh'` outside `docs/review/` returns three
hits, all incidental:

```
tools/rewrite-paths.py:33   MAP = …            (reads it for --apply/--verify)
tools/rewrite-paths.py:61   HAND_EDITED entry
tools/verify-datasheets.py:192  skips it when checking dangling corpus paths
```

`[repo] .claude/settings.json` has one `PreToolUse` hook on `git commit`, and
it runs `tools/check-staleness.py` only. `[repo] tools/check-staleness.py:278-296` (`merge-bom.py --check` at :281)
shows that checker already shelling out to `merge-bom.py --check` and
`merge-manifests.py`, and `:659` to `verify-datasheets.py`. So there is a
working composition point, three tools already hanging off it, and this map —
the one artifact in the repository whose documentation contains a written,
tested, four-line invariant — is the one thing not wired to it.

The consequence is already on the record: the invariant broke at `092b364`,
the very next commit, and would have broken at `c65083d` too had `79f5c4a` not
happened to catch it. The hook is the whole reason the staleness rule survives
step 3 in `CLAUDE.md` §2; the map has the same shape of rule and no hook.

### What would fix it

In rough order of value per line:

1. **`tools/rewrite-paths.py --check`** — the tool already loads the map
   (`load_map`) and already calls `git ls-files` (`tracked_files`,
   `invert_targets`). The check is the four lines §7 prints, plus the `old`
   uniqueness assertion from D18-4, and it should print the offending paths
   rather than just failing. Perhaps twenty lines in a file that already has
   every input it needs.
2. **Call it from `check-staleness.py`** alongside `merge-bom.py --check`, so
   the existing commit hook reports it. A new file then cannot land silently
   as an orphan; the committer is told in the same breath as a stale figure.
3. **Auto-append `created-history` rows.** Every orphan seen in this slice
   (`docs/review/2026-09-22-fix-audit/README.md`, `.manifest-R9.csv`, and the
   25 pre-merge reports before them) is a file whose row is fully derivable:
   path, `created-history`, and the introducing commit or wave directory. A
   `--sync` mode that appends rows for orphans under `docs/review/**`,
   `docs/log/**` and `docs/research/**` and *refuses* for anything else would
   reduce the manual burden to corpus files only, which is where judgement is
   actually needed.

### The deeper point, offered as an argument rather than a finding

The map is doing two jobs and only one of them can go stale.

- **Job A — resolve a path quoted in a dated record.** Needs the 287 old-side
  rows and the 29 `moved` + 4 `deleted` rows. This job is *finished*. Its
  domain is the tree at `81c081d`, which is immutable. It cannot go stale, by
  construction.
- **Job B — a census of every tracked file.** The 123 `created` /
  `created-history` rows, 30% of the file, exist only to satisfy
  `tracked - placed == ∅`. **No reader of a pre-restructure record can ever
  quote a path that did not exist then**, so these rows answer no question
  Job A poses. They carry real provenance value — which commit, split out of
  which page — but that is a different document.

Job B is the half that breaks on every commit, and it is the half the
filename's date (`path-map-2026-09-21.csv`) promises it is not doing. Two
defensible resolutions:

- **Automate Job B** (items 1–3 above) and keep the single file. Recommended,
  because the `created` notes are genuinely useful and because the
  `placed - tracked` assertion — the half that caught the 22 datasheet rows —
  only works if both halves are maintained.
- **Or split them**: freeze the map at its Job A contract and move the
  `created` rows to a provenance index with no coverage invariant. Cheaper to
  keep true, but gives up the assertion that found the only serious defect
  this file has ever had.

Either is better than the present state, which asserts a daily-breaking
invariant and checks it never.

---

## Findings index

| id | claim | severity | status |
|---|---|---|---|
| D18-1 | `repo-maintenance.md:298` asserts "every tracked file has a row"; false at HEAD (`docs/review/2026-09-22-fix-audit/README.md` has no row) | low, high signal | `[test]` confirmed |
| D18-2 | §7's "410 rows: 405 tracked files, plus 4 `deleted` and 1 duplicate destination" — actually 406 + 4, and **zero** duplicate destinations | low | `[test]` confirmed |
| D18-3 | §7's "143 tracked files with no row" — actually 144; 143 is the count the fix landed, and the 144th is the file it missed | low | `[test]` confirmed |
| D18-4 | §7's `created`-row rationale states a mechanism (`rewrite-paths.py` would rewrite) that a dict-keyed `load_map` does not exhibit, and names the one example where the hazard is inert; the real hazard is a silent order-dependent overwrite | medium (doc), none (map) | `[test]` confirmed both directions |
| D18-5 | §7's table promises `created-history` notes name a commit; all 28 name a wave directory | nit | `[test]` confirmed |
| D18-6 | Nothing in the repo runs §7's four-line check, though `check-staleness.py` already composes three sibling tools and the commit hook already calls it | **medium, structural** | `[test]` confirmed |

**Verified correct, no defect:**

- `[test]` Old side is an exact bijection onto `[git] 81c081d`: 287 rows, 287
  tree paths, nothing missing, nothing invented.
- `[test]` No dangling row at HEAD; no duplicate `new`; no duplicate non-empty
  `old`; no `unmoved`/`unmoved-history` row with `old != new`; no `moved` row
  with an empty or identical pair.
- `[test]` `kind` is consistent with path class in all 410 rows: no
  `-history` kind on a non-history path, no `unmoved`/`created` on a
  `docs/review|log|research` path.
- `[test]` All 22 datasheet corrections verified against disk and against
  `.moves.csv`, including byte identity across each move and both filename
  renames. `.moves.csv` is complete against `git diff 81c081d..HEAD` and is
  machine-validated by `merge-manifests.py`.
- `[test]` The WS2815 de-duplication claim is exactly true — identical git
  blob `9654b884…` and identical SHA-256 `72e22d2f740c…` across all three
  paths. `deleted` is the right classification.
- `[test]` `rewrite-paths.py` handles an empty `old` safely; the guard at
  `tools/rewrite-paths.py:83-85` is load-bearing and demonstrated so.
- `[test]` All 95 `created` notes name a commit that is genuinely the
  introducing commit.
- `[test]` 91.4% of the 6,027 path references in `docs/review/**` and
  `docs/log/**` resolve on a direct lookup; 96.1% resolve.
