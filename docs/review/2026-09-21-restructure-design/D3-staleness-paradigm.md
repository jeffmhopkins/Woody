# D3 — Revision and dependency staleness across a restructured corpus

**Agent D3, cold.** Read: `CLAUDE.md`, `config/figures.yaml`, `tools/check-staleness.py`,
`tools/verify-datasheets.py`, `docs/reference/repo-maintenance.md`, `.claude/settings.json`,
the eight `hardware/**` pages, the fourteen ADRs, `hardware/bom.csv`,
`datasheets/MANIFEST.csv`. Not read, per the cold rule: anything under
`docs/review/**`, `docs/log/**`, `docs/research/**` — including this wave's own
directory.

Provenance is marked on every claim: `[repo]` path:line, `[calc]` with arithmetic,
`[measured]` for something I ran in this session, `[inference]` for a judgement.

---

## 0. Eight measurements the design rests on

Everything below is argued from these. They were taken in this session against the
working tree at `f94e91d` `[measured]`.

| # | Measurement | Value |
|---|---|---|
| 1 | Figures in the register | 33 `[repo] config/figures.yaml` |
| 2 | Figures actually **cited by id** anywhere in the corpus | **3** (`cref-out-node` ×3, `riso-ref-topology` ×5, `umbilical-current` ×1) `[measured]` |
| 3 | Distinct `owner:` paths | 15, all currently resolving `[measured]` |
| 4 | Tools that read `owner:` | **0** `[repo] grep -n owner tools/*.py` returns nothing |
| 5 | Markdown links in the corpus | 59 `[measured]` |
| 6 | Bare `foo.md` filename mentions in prose | 177 `[measured]` |
| 7 | `ADR NNNN` prose references | 509 `[measured]` |
| 8 | `datasheets/…pdf` path references in the corpus | 71, across 35 distinct paths, **1 of which does not exist** `[measured]` |

Two of these are findings in their own right and I file them before the design,
because the design is partly a response to them.

### Finding D3-1 — `hardware/bom.csv:97` cites a datasheet path that is not there

`[repo]` `hardware/bom.csv:97` (row `F-CHAIN`) cites
`datasheets/discrete-and-power/MF-PSMF010X.pdf`. `[measured]` The file on disk is
`datasheets/discrete-and-power/MF-PSMF010X-polyfuse.pdf`, and that is also the name
in `datasheets/MANIFEST.csv:35` and `datasheets/.manifest-R4.csv:10`. One character
class apart; nothing in the corpus notices. `verify-datasheets.py` checks the
manifest against the disk, never the corpus against the manifest `[repo]
tools/verify-datasheets.py:26-80`. This is the smallest possible instance of the
class of defect I was asked to close, it is live today, and it costs four lines of
Python to catch.

### Finding D3-2 — `check_refdes()` exists, is a dependency check, and is never called

`[repo]` `tools/check-staleness.py:126-145` defines `check_refdes(files, bom_refs)`
— "Reference designators drawn in a schematic with no BOM row". `[repo]` `main()`
at 159-218 never calls it; `grep -n check_refdes tools/check-staleness.py` returns
only the definition. It is dead code.

`[measured]` I ran it by hand. It returns **36 hits**. Classified by hand:

- **14 are not refdes at all** — `SOIC-14`, `SOIC-16`, `SOT-23-5`, `SOT-23-6`,
  `SOD-323`, `TO-92` (packages); `KS-33`, `KS-33-3D`, `R-78E5`, `ESP-IDF`, `CI-SN`
  (part and standard names); `PULL-UP`, `N-FET`, `U-BOLT` (generic prose).
- **~6 are abbreviations of a real row** — `C-GATE`/`C-TIMER` for
  `C-GATE-LOADSW`/`C-TIMER-LOADSW`, `J-UMB`, `R-LED`, `R-FB`, `R-IN` `[measured]`
  prefix-matched against column 1 of `hardware/bom.csv`.
- **~16 are genuine** — including `R-MOSI-SER`, `R-SCLK-SER`, `R-CS-SER` (the
  superseded names already on the `spi-series-r` forbidden list `[repo]`
  `config/figures.yaml:142`) and `R-PRESENCE` (deleted with the LM311 `[repo]`
  `hardware/module/digital-and-supervision.md:197`).

`[inference]` I think it is unwired because somebody switched it on, saw 36 hits at
a ~1:2 signal-to-noise ratio, and could not justify that in a hook that is
deliberately one line. I cannot verify that without reading review history, which
the cold rule forbids.

**This is the single most useful thing I learned.** It is the whole design in one
data point: *an inferred dependency edge — regex over prose — has an unusable noise
floor, and a check nobody can bear to switch on is worth nothing.* Every check I
propose below is over **declared** edges, where the noise floor is zero by
construction.

---

## 1. The line: what is mechanically catchable and what is not

The brief asks me to draw this explicitly and warns that over-claiming is worse than
a small proposal. So, bluntly:

### Mechanically catchable (I propose checks for all of these)

1. **A reference that does not resolve.** A cited figure id that is not in the
   register; an `ADR 0015` that does not exist; a `depends_on: circuit:…` naming a
   directory that is gone; a `datasheets/…` path with no file. This is decidable
   because both ends are names, and names are comparable.
2. **A snapshot that has moved.** A page that records "I read SBOS410O, sha256
   `abc…`" against a `MANIFEST.csv` row that now says `def…`. Decidable: two hashes,
   compare them.
3. **Two declarations that disagree.** `figures.yaml` says `panel-width` is owned by
   `module/panel`, and `module/panel` does not exist, or a second circuit claims it.
   Decidable because both sides declared.
4. **A dependency that has changed since you last looked.** `last_reviewed: 2026-09-21`
   against `git log` on the dependency's directory. Decidable, but **noisy** — see §5.
   This one is a worklist, not a verdict.
5. **A refdes named in prose with no BOM row** — the existing dead check, once its
   noise is killed by a declared ignore list (§3.6).

### Not mechanically catchable — and I propose nothing for these

6. **Whether the argument is still good.** The named example is exact and I want to
   be precise about it, because I nearly filed it wrong.

   `[repo]` `docs/decisions/0004-cv-interface-module.md:475-482` carries a
   **"Withdrawn 2026-09-21"** block with strikethrough on the heading, recording that
   the 74HC123 frame watchdog was built and deleted. `[repo]` Twenty lines below it,
   at `:496`, a `####` subheading — "The watchdog's scope is the DAC channels, and
   breath is outside it" — reasons from the watchdog as a live mechanism, with no
   marker of its own. I initially read that as a live instance of the failure mode.
   It is not: the section sits inside the withdrawal's scope. But **no tool can know
   that**, because the scope is a human reading convention — a heading level and
   twenty lines of distance — and the checker's refutation detector is per-match
   line context `[repo]` `tools/check-staleness.py:102-107`,
   `docs/reference/repo-maintenance.md:63-68`.

   `mod-channels.md` does this properly: `[repo]`
   `hardware/module/mod-channels.md:159-167` states the dependency's death *inside*
   the argument that used it ("What asserts `CLR`, now that the watchdog is gone").
   A reader is what tells those two apart.

7. **Whether a page still depends on a deleted thing in prose.** ADR 0004:496
   depends on the watchdog and names no refdes, no node, no figure id. There is
   nothing for a checker to grab. If a dependent had written
   `depends_on: [node:CLR-WATCHDOG]` and the provider had deleted that `provides`
   entry, the edge would break loudly — but that is a *narrow* shape, and the real
   dependency in this case was an argument, not a name. **I claim the parts half
   and the named-node half. I do not claim the argument half.**

8. **Whether a figure's `owner` document actually states the figure.** I can check
   the owner *exists*. I cannot check it *says the thing*, because the register
   stores `"-9.94 V"` and the page may legitimately spell it `9.941 V` mid-derivation
   `[repo]` `config/figures.yaml:30`. Trying to check this would rebuild the
   forbidden-pattern problem with the polarity reversed.

9. **Whether a `depends_on` block is complete.** If nobody declares the edge, no
   tool sees it. This is the honest ceiling on the whole scheme and §2 is where I pay
   for it.

### What a review wave still has to do

Unchanged in kind, smaller in volume. Items 6, 7 and 9 are wave work forever. What
changes is that the wave gets a **generated worklist** instead of a blank page:
`--deps` (§3.5) prints every circuit whose dependencies have moved since it was last
read, which is a defensible slicing of "where should twelve cold agents look" and is
currently decided by hand.

---

## 2. The per-directory metadata

**File:** `circuit.yaml`, one per circuit directory.
**Format:** YAML. `check-staleness.py` already imports `yaml` `[repo]`
`tools/check-staleness.py:16`, and the register is YAML, so no new dependency and no
new dialect.

`[measured]` A restructure of the eight `hardware/**` pages into circuit directories
gives 8–12 of these files. That number is load-bearing: at 12 files a declared
dependency graph is maintainable by one person; at 200 it is fiction.

### The file

```yaml
# hardware/module/power-entry/circuit.yaml
id: module/power-entry
title: Power entry, load switch and rail generation

last_reviewed: 2026-09-21

depends_on:
  - adr:0005                          # rail voltages and the umbilical budget
  - adr:0004                          # module scope and panel
  - circuit:controller/carrier        # supplies the load this stage sizes for
  - fig:umbilical-current             # 359 mA — FB2 bias and the LT1641 sizing
  - fig:opa2197-output-impedance
  - refdes:U-LOADSW
  - refdes:FB-IN

provides:
  - node:PWR_GND
  - signal:PWRGD

verified_against:
  - part: LT1641
    sha256: 8b1d…64 hex…
    pages: "2, 8, 9"
    read: 2026-09-21
  - part: MF-PSMF010X
    sha256: BLOCKED
    blocked_on: "polyfuse package not chosen; MANIFEST row is OK-SUBSTITUTE"
```

### Field by field — what it buys, what happens when it rots

| Field | Check it enables | If it is forgotten | Verdict |
|---|---|---|---|
| `id` | Stable name for `owner:` and `depends_on:` to point at; uniqueness across the tree | Set once at creation. Cannot rot. | **Keep** |
| `title` | none | n/a | **Keep** (free, human) |
| `last_reviewed` | dependency-drift warning (§3.5) | **Fails safe** — a stale date makes the tool warn *more*, never less | **Keep** |
| `depends_on` | every ref must resolve (§3.1–3.4) | **Fails silent** — an undeclared edge is an unchecked edge. The highest-risk field. | **Keep, with the mitigations below** |
| `provides` | lets another circuit's `depends_on: node:…` break loudly when the thing is deleted | Rots into fiction if unpruned | **Keep, phase 2, pruned** |
| `verified_against` | SHA drift against `MANIFEST.csv` (§3.3) | Missing entry = lost check, but no false guarantee | **Keep** |
| `revision` | — | — | **Reject, argued below** |
| `figures_owned` | — | — | **Reject, argued below** |

### Reject: `revision`

A hand-maintained revision integer is the archetype of the field nobody maintains.
Worse, in this repo it would be maintained *sometimes*, which is the dangerous state:
`docs/reference/repo-maintenance.md:168-172` already records that "a correct figure
filed as `disputed` is the dangerous kind, because it stops getting re-checked."
A `revision: 3` that has been 3 for four months reads as "nothing changed" and means
"nobody bumped it."

**Git already holds it, exactly and for free.** `git log -1 --format=%H -- <dir>`
is the revision of a circuit, it cannot be forgotten, and it cannot be wrong. The
only thing it over-reports is a typo fix, which §3.5 handles by making the check a
warning that names the changed files.

### Reject: `figures_owned`

This is the tempting one and it is wrong. Listing `figures_owned: [dac-rail,
loadswitch-timer, …]` in `circuit.yaml` puts the ownership fact in two files.
`CLAUDE.md` §1 — "the owning document states it and every other document cites it by
name" — applies to this project's own metadata as much as to its voltages. Make
`figures.yaml` `owner:` point at the circuit id (§4) and **derive** the owned list;
`--deps` prints it. One declaration, no sync step, nothing to forget.

### Mitigating `depends_on` — the field that can lie

Three things, in order of how much they buy:

1. **Typed refs only, every type resolvable.** `adr:`, `circuit:`, `fig:`, `part:`
   (a `MANIFEST.csv` part key), `refdes:` (a `bom.csv` column-1 value),
   `node:`/`signal:` (another circuit's `provides`). A free-text dependency is not
   accepted — it would resolve to nothing and check nothing. `[measured]` My loose
   regex over the corpus matched `figures.yaml rather` and `figures.yaml lists` as
   figure ids, which is exactly what an undelimited syntax buys you.
2. **Seed it from the prose that already exists, once.** `[measured]` 509 `ADR NNNN`
   mentions and 71 datasheet paths are already in the corpus. A one-off extraction
   at restructure time produces a first draft of every `depends_on` block, which a
   human then cuts down. Nobody is asked to invent a graph from nothing — the
   failure mode of every dependency-metadata scheme.
3. **A circuit with an empty `depends_on` is reported, not accepted.**
   `--deps` prints `module/foo: no declared dependencies` in its own short list.
   An empty block is a claim of independence and should look like one. This is the
   same move `repo-maintenance.md:155-156` makes for an empty `forbidden` list: "a
   `disputed` entry protects nothing until it is settled."

I will not pretend this closes the gap. `depends_on` is a declaration, and the
brief's warning applies to it more than to anything else here: **it reads as a
guarantee of completeness and it is not one.** The mitigation is that the three
zero-noise checks (§3.1–3.3) fire on the edges that *are* declared, and nobody is
invited to believe the graph is total. `--deps` should print its coverage —
`12 circuits, 47 declared edges` — precisely so the number stays visible.

---

## 3. The checker

**Recommendation: no `tools/check-links.py`. It goes inside
`tools/check-staleness.py` as `check_links()`.**

Three reasons, the first decisive:

- `[repo]` `tools/check-staleness.py:126` is a dependency check that has been sitting
  in this repo unwired. A check in its own file is a check that can be left out of
  the hook; a check inside the tool the hook already runs cannot be.
- `[repo]` `.claude/settings.json` runs one command on `Bash(git commit *)`. A second
  tool means a second hook command, a second 4.8-second process, and a second line
  of surfaced text — against a rule that says a dump on every invocation is a real
  cost `[repo]` `tools/check-staleness.py:20-21`.
- The checks share the corpus walk (`corpus_files()`), the exclude list, and the
  refutation regex. Duplicating `CORPUS_DIRS` into a second file is a tracked-figure
  restatement in Python.

### The checks

#### 3.1 A citation that does not resolve — **FAIL**

Requires a delimited citation syntax. I propose the one already 3/11 in use
`[repo]` `hardware/bom.csv:27,75,76`: **`figures.yaml `<id>``** — the words
`figures.yaml` followed by a backticked id. The checker resolves every one against
the register.

`[measured]` This is presently near-vacuous: 3 of 33 figures are cited by id, and 11
citations exist corpus-wide. **State that plainly.** The rule "cite, do not restate"
is the corpus's central rule and the corpus follows it three times. The check costs
nothing to build and protects almost nothing until citation is adopted — but it is
the precondition for adoption, because a convention with no checker drifts into
three spellings inside a month.

#### 3.2 A `depends_on` ref that does not resolve — **FAIL**

`adr:0015` with no `docs/decisions/0015-*.md`; `circuit:module/gone`;
`fig:typo-here`; `part:NOT-IN-MANIFEST`; `refdes:U-WATCHDOG` with no `bom.csv` row.
Both ends are declared names, so a hit is a fact, not a guess. **This is the
watchdog case in the shape that is decidable**: `U-WATCHDOG`, `R-WDT` and `C-WDT`
are gone from `bom.csv` `[repo]` `hardware/bom.csv:68` records their deletion, and
any circuit still declaring a dependency on them breaks the build the moment they
go.

#### 3.3 A `verified_against` SHA that no longer matches `MANIFEST.csv` — **FAIL**

Look up `part:` in `datasheets/MANIFEST.csv`, compare `sha256`.

**On the objection that this duplicates a tracked value:** it does not, and the
distinction matters. `MANIFEST.csv` holds *the document that is banked now*.
`circuit.yaml` holds *the document I read when I wrote this page*. They are
different quantities that happen to be equal most of the time, and **their
divergence is the entire signal.** Compare `CLAUDE.md` §3: three figures moved in one
afternoon when someone re-read a banked PDF. If a fourth re-read replaces
`OPA2197.pdf` with SBOS737D, every page carrying the SBOS737C hash lights up, which
is precisely what did not happen automatically for the REF5050 grade
`[repo]` `config/figures.yaml:420` — "fixed in `bom.csv` on 2026-09-21 and NOT in
`docs/decisions/0003-breath-sensing-path.md`, which went on asserting 0.05%/3ppm for
another two commits."

`[measured]` The corpus contains **zero** raw sha256 strings today, so this check
starts empty and grows with adoption.

#### 3.4 Ownership disagreement and dangling paths — **FAIL**

- A `figures.yaml` `owner:` that does not resolve. `[repo]` No tool reads `owner:`
  today — all 33 could be wrong right now and nothing would say so.
- Two circuits claiming the same figure (impossible once ownership is one-sided per
  §2, so this degrades to a uniqueness check on `id`).
- Any `datasheets/…` path mentioned anywhere in the corpus with no file on disk.
  **This catches finding D3-1 today**, and it does not need `circuit.yaml` at all —
  it is eight lines and could land before the restructure.

#### 3.5 Dependency drift — **WARN, and only under `--deps`**

For each `depends_on: circuit:X` and `adr:NNNN`, compare
`git log --since=<last_reviewed> -- <target path>` against this circuit's
`last_reviewed`.

**This check does not run in the hook.** `CLAUDE.md` §5 already draws this line for
semantic work — "at gates, not per commit" — and drift is semantic in everything but
its trigger. It over-fires on typo fixes by construction and there is no honest way
to make it not. Its output is a review wave's worklist, generated at a gate:

```
$ python3 tools/check-staleness.py --deps

DEPENDENCY DRIFT (4 circuits) - not failures, this is the next wave's worklist
  module/power-entry      reviewed 2026-09-21
      adr:0005                    2 commits since   (af6be85, f94e91d)
      circuit:controller/carrier  1 commit  since   (ddfa72c)
  module/mod-channels     reviewed 2026-09-18
      circuit:module/digital-and-supervision  4 commits since
  ...

COVERAGE
  12 circuits, 47 declared edges, 3 with no declared dependencies:
      module/breath-output-stage, controller/cluster-boards, module/pitch-stage
  33 figures, 3 cited by id, 30 restated and guarded only by `forbidden`

unused `provides` (2) - delete these or somebody should be depending on them
  module/power-entry  signal:PWRGD
  module/digital-and-supervision  node:CLR
```

The `unused provides` block is the pruning mechanism that stops `provides` becoming
fiction. A `provides` entry nobody depends on is either dead or an undeclared edge,
and both want a human.

#### 3.6 The refdes check, resurrected — **WARN**

Wire up `check_refdes()` with one addition: a declared ignore list at
`config/refdes-ignore.txt`, seeded from the 14 package and part-name tokens measured
in D3-2. `[calc]` That takes 36 hits to roughly 22, of which ~6 are abbreviations of
real rows and ~16 are genuine. WARN not FAIL, because the abbreviation class
(`C-GATE` for `C-GATE-LOADSW`) is a legitimate prose habit I have no business
outlawing.

### What prints

**The hook budget is one line and I do not exceed it.** `[repo]`
`.claude/settings.json` greps stdout for `^(STALE VALUES STILL LIVE|BOM INTEGRITY|PASS|FAIL)`
and takes `head -3`; but every section in `main()` is emitted `detail_only=True`
`[repo]` `tools/check-staleness.py:148-153,182,187,196,203`, so on a default run
**only the final summary line reaches stdout at all** — confirmed by
`.staleness-report.txt`, which contains exactly `PASS no live stale values |
5 unresolved (tracked)` `[repo]`.

So a new `BROKEN REFERENCES (n)` headline would be invisible to the hook, and a
headline that *did* match the grep would push the PASS/FAIL line past `head -3`.
**The counters go in the existing summary line and the hook is not touched:**

```
PASS no live stale values, no broken refs | 5 unresolved (tracked)
```

```
FAIL 0 stale + 0 bom + 3 refs | 5 unresolved (tracked) | detail: .staleness/report.txt or --detail
```

Detail, in `.staleness/report.txt` as today:

```
BROKEN REFERENCES (3)
  A name that does not resolve. Both ends are declared, so these are facts.

  hardware/bom.csv:97
      datasheets/discrete-and-power/MF-PSMF010X.pdf does not exist
      MANIFEST.csv:35 banks it as MF-PSMF010X-polyfuse.pdf

  hardware/module/power-entry/circuit.yaml
      depends_on: refdes:U-WATCHDOG  - no row in hardware/bom.csv
      (bom.csv:68 R-CLR-PU records this part as deleted)

  hardware/controller/carrier/circuit.yaml
      verified_against: part OPA2197 sha256 a3f1c8..  MANIFEST has 91e4d2..
      the banked document changed after this page was written against it
```

Three lines per defect, each naming the other end. `[inference]` A defect report
that does not name the other end sends the reader to find it, and "fixes land where
the editing is happening" `[repo]` `CLAUDE.md:11` is precisely what happens then.

---

## 4. `figures.yaml owner:` — yes, retype it. Validate it first.

### The arithmetic

`[measured]` 33 entries over 15 distinct owner paths. Retyped as typed refs:

| New form | Entries | Survives a move? |
|---|---:|---|
| `circuit:…` (6 hardware pages) | **17** | yes |
| `adr:NNNN` (5 ADRs) | **8** | yes — the number is the identity, the filename is decoration |
| `file:…` (`bom.csv` ×4, `key-layout.yaml` ×2, `latency-budget.md` ×1, `ks33-geometry.md` ×1) | **8** | no |

`[calc]` 17 + 8 + 8 = 33. **25 of 33 stop breaking on a move.** The remaining 8 are
owned by things that are not circuits and should not be forced into a circuit id
just to make a table look uniform — `hardware/bom.csv` is not a circuit, and
pretending it is would be a worse lie than a fragile path.

### Cost

1. **One mechanical edit of 33 lines**, plus a mapping table. Cheap, and it can be
   generated from the current paths.
2. **A second name space to keep honest.** `circuit:module/power-entry` is a name
   that must exist somewhere — which is `circuit.yaml`'s `id`. §3.4 checks it. This
   is a real cost and it is the cost of the whole scheme, not of this field.
3. **Indirection when reading.** `owner: hardware/module/power-entry.md` can be
   opened; `owner: circuit:module/power-entry` cannot, without a lookup. Mitigation:
   `--deps` prints the resolved path, and the id is a path fragment by convention so
   the lookup is usually unnecessary.

### The part that matters more than the retyping

`[repo]` Nothing reads `owner:` today. Whether it stays a path or becomes an id,
**it should be validated**, and validation is ~6 lines. If the answer to §4 were
"no, keep paths", I would still file that. The retyping buys move-resistance; the
validation buys knowing whether the field was ever true.

Sequence: **validate first, in its own commit; retype second.** If the two land
together and validation fails on an entry that was already wrong, the diff cannot
tell you which change broke it — which is the same confusion the CRLF rule exists to
prevent `[repo]` `docs/reference/repo-maintenance.md:130-134`.

---

## 5. False positives

`repo-maintenance.md:161-165` calls `false_positive_note` "the one that earns its
keep", and it earns it because the forbidden list matches **numerals in prose**,
where a legitimate occurrence is common — `[repo]` `config/figures.yaml:41`,
"0.2-4.80 V is the datasheet's OWN COVER-PAGE line and may be quoted as such";
`[repo]` `:161`, "the MPXV4006DP's supply spec is legitimately 4.75-5.25 V. Match
the regulator, not the numeral."

**My checks in §3.1–3.4 do not have that shape and mostly do not need that hatch.**
A `fig:` id either is in the register or is not. A SHA either matches or does not.
There is no "legitimately spelled this way" case, because both ends are names chosen
to be compared. Claiming a general escape hatch for them would invite muting facts,
and a muted fact is how a wrong finding gets filed as handled `[repo]`
`CLAUDE.md:110-115`.

Two places genuinely need one, and each gets a *specific* hatch that requires the
person to write down what they know:

### 5.1 `sha256: BLOCKED` + `blocked_on:` — an honest gap in `verified_against`

`[repo]` `datasheets/MANIFEST.csv` has 20 `BLOCKED` rows and 1 `NOT-FETCHED`
`[measured]`. A circuit depending on one of those parts cannot record a hash. The
hatch reuses the manifest's own vocabulary and the corpus's own rule —
`CLAUDE.md:133-135`, "mark unresolved things `TBD`/`open` **with what decides them**":

```yaml
  - part: WS2812B-0807
    sha256: BLOCKED
    blocked_on: "bench measurement at E1 - Worldsemi publishes no 0807 datasheet;
                 see figures.yaml `matrix-led-current`"
```

`blocked_on:` is **required** when `sha256: BLOCKED`, and a missing `blocked_on` is
itself a FAIL. That is the difference between an escape hatch and a mute.

### 5.2 `recheck:` — a re-bank that did not move any number

The realistic false positive on §3.3: the PDF is re-fetched, the bytes change (a
different Mouser cover page), the document is the same revision and no figure moves.
The hatch is **not** a suppression flag; it is updating the hash and stating why the
numbers held:

```yaml
  - part: OPA2197
    sha256: 91e4d2…
    pages: "8, 10, 22, 30"
    read: 2026-09-22
    recheck: "re-fetched 2026-09-22, still SBOS737C, pagination unchanged;
              Zo p.8, Fig. 56 p.30 re-read and unmoved"
```

`[inference]` The reason this is better than a mute flag: the note is the thing the
next reader needs, and it is written at the only moment anybody knows it. A
`# noqa`-shaped suppression would be written at the same moment and carry none of it.

### 5.3 The one I refuse to give a hatch

§3.5's drift warning will fire on typo commits. The temptation is per-edge
acknowledgement — "I reviewed `power-entry` through commit `abc1234`". **I reject
that**, because it is a hand-maintained field with a silent failure mode, which is
exactly what §2 rejects `revision` for. The drift check is warn-only and gate-only;
its noise is the price of it not being a lie, and the right response to a noisy
worklist is to bump `last_reviewed` after reading, which is one date.

---

## 6. The three-step rule

### What it becomes

Step 1 and step 3 are unchanged. **Step 2 is the one that gets a tool, and the tool
prints — it does not write.**

```
1. Update `value` in config/figures.yaml.
2. Run `python3 tools/check-staleness.py --moved <figure-id>`.
   It reads the OLD value out of git, scans the corpus for every spelling of it,
   and prints them. Add one `forbidden` pattern per spelling YOU JUDGE to be a
   restatement. It will not write the list for you.
3. Run `python3 tools/check-staleness.py`. Fix everything it names, same commit.
```

### `--moved`, precisely

`[repo]` The old value is already recoverable: `git show HEAD:config/figures.yaml`.
The tool extracts the numeral tokens from the old `value:` string, scans the corpus
for each, and prints every match with its file, line, surrounding words, and whether
the existing refutation regex `[repo]` `tools/check-staleness.py:36-41` already
considers it refuted.

```
$ python3 tools/check-staleness.py --moved sensor-full-scale

sensor-full-scale   was "4.7 V"   now "4.86 V"   (old value from HEAD)

Scanning the corpus for every spelling of the OLD value.
These are CANDIDATES. Read each one. Add a forbidden pattern per spelling that
is a restatement of this figure; leave the rest alone. This list is not written
to figures.yaml and never will be - only you can tell a restatement from a
quotation of the datasheet's own cover page.

token "4.7"  -  34 hits in 12 files
  docs/decisions/0003-breath-sensing-path.md:214   "…0.2 – 4.7 V across the…"        LIVE
  docs/decisions/0003-breath-sensing-path.md:288   "| rest | 0.200 V | 4.700 V |"     LIVE  (table cell)
  hardware/module/breath-receive-stage.md:77       "…full scale = 4.7 V, so the…"     LIVE
  docs/decisions/0003-breath-sensing-path.md:441   "…was 4.7 V, which the datasheet…" refuted
  ...
```

`[measured]` Noise floor, measured against the real corpus: `4.7` → 34 hits in 12
files; `9.6` → 5; `10.05` → 9; `8HP` → 16; `5.25` → 5; `75.8` → 9; `107` → 6;
`83` → 13. Worst cases: `0.2` → 92, `2.5` → 97, `1.5` → 87. Median around 13.
Reading 13 lines — or 92, at the worst — **once per figure change** is exactly the
work step 2 already demands. The tool does not reduce it. It makes it happen.

### Why it must not write the list

`[repo]` `CLAUDE.md:33-39` and `repo-maintenance.md:30-47` record the worst instance:
the `sensor-full-scale` list was written from the owner ADR, the corpus spelled the
number seven other ways, eleven derived statements stayed live and the checker
reported zero hits.

There are two ways to make that easier, and I want both named so nobody proposes
them later:

1. **Auto-generating `forbidden` from the scan.** It would include the legitimate
   occurrences — `[repo]` `config/figures.yaml:41` documents that `0.2-4.80 V` is the
   datasheet's own cover-page line, quoted deliberately in ADR 0003 — so the checker
   would fail on correct text, the author would delete patterns to make it pass, and
   the register would end up shorter than the hand-written one. Worse, the author
   would stop reading the hits, which is the only part of step 2 that actually works.
2. **Letting `--moved` add the entry to `figures.yaml` and run the checker in one
   command.** Convenient, and it removes the moment where a person looks at
   34 lines of their own corpus. That moment is the control.

`--moved` moves the list's *source* from the author's memory of the corpus to the
corpus. It leaves the *judgement* exactly where it is. That is the only change I
will defend.

### One thing the restructure adds to step 2

A figure change is not the only thing that strands references — a **file move**
strands 25 of 33 `owner:` paths and 177 bare filename mentions `[measured]`.
`--moved` does nothing for that; §3.4 and §4 do. Worth saying in `CLAUDE.md` §2
alongside the three steps, because somebody mid-restructure will reach for the
familiar tool.

---

## 7. Cost

### Per ordinary commit: effectively zero, and one line of output

`[measured]` `check-staleness.py` currently takes **4.85 s** on a 757 KB, 31-file
corpus. `[calc]` That is 155 forbidden patterns × 31 files = 4805 whole-file
read-and-character-join operations, ≈1 ms each `[repo]`
`tools/check-staleness.py:64-92`.

My additions are **one** pass over the corpus for `datasheets/…` paths and citation
tokens, ~12 small YAML parses, and one `MANIFEST.csv` read (98 rows).
`[calc]` ≈31 file reads against 4805 = **+0.6%**, roughly +30 ms. Unmeasurable next
to what the hook already pays.

Output cost: **zero new lines.** The counters fold into the existing summary
(§3), the hook's `head -3` is untouched, and `.staleness/report.txt` grows only when
there is a defect.

Author cost per ordinary commit: **zero.** Nothing in §3.1–3.4 asks for an edit
unless you moved or deleted something, in which case the edit is the point.

### Per new circuit: one file, about fifteen lines

Written once, at creation, when the dependencies are in your head anyway. At
8–12 circuits, the whole declared graph is ~150 lines of YAML.

### Per gate: one command and a worklist

`--deps` is where the noisy check lives. It costs a `git log` per declared edge —
`[calc]` ~47 edges × ~20 ms = ~1 s — and it is run by a human at a gate, not by a
hook.

### Per figure change: one scan-read, replacing one remembered grep

Measured in §6: median ~13 lines, worst ~97. Not new work. Newly reliable work.

### The saving I am not counting, and one I will offer

`[inference]` The 4.85 s is 4805 reads of 31 files because the joined-text buffer is
rebuilt per pattern. Hoisting it into a `{path: (text, linemap)}` dict built once
would make it ~31 reads and roughly 30× faster. That is a five-line change to
`check_figures()` and it is out of my slice — but if the hook's latency ever becomes
the reason someone weakens a check, this is the thing to do first, and it changes no
behaviour at all.

---

## Summary of recommendations, in landing order

| # | Change | Depends on the restructure? | Size |
|---|---|---|---|
| 1 | Validate `figures.yaml owner:` resolves | no | ~6 lines |
| 2 | FAIL on any `datasheets/…` path in the corpus with no file — **catches D3-1 today** | no | ~8 lines |
| 3 | Wire up `check_refdes()` + `config/refdes-ignore.txt`, as WARN — **D3-2** | no | ~10 lines + 14-entry list |
| 4 | Fold counters into the existing one-line summary; do not touch `.claude/settings.json` | no | ~4 lines |
| 5 | `--moved <figure-id>` (prints candidates, writes nothing) | no | ~40 lines |
| 6 | `circuit.yaml`: `id`, `title`, `last_reviewed`, `depends_on`, `verified_against` | **yes** | 8–12 files |
| 7 | `owner:` → typed refs (`circuit:` / `adr:` / `file:`); 25 of 33 become move-proof | **yes** | 33 lines + mapping |
| 8 | `check_links()` inside `check-staleness.py`: §3.1–3.4 FAIL, §3.5–3.6 under `--deps` | **yes** | ~120 lines |
| 9 | `provides:` + unused-provides pruning | **yes**, phase 2 | small, defer one wave |

Items 1–5 are independent of the restructure and would pay for themselves before it
starts. Item 9 is the only one I would hold back, and I would hold it back until
`depends_on` has survived a wave, because it is the field most likely to become
something nobody maintains.

### What I am not claiming

The scheme catches **unresolvable names and moved snapshots**. It does not catch a
surviving argument, an undeclared edge, or an owner document that no longer states
its own figure. `CLAUDE.md` §5's example — ADR 0004's watchdog — stays a reader's
job under every version of this design, and the honest gain is that the reader
arrives with a generated worklist instead of a blank page.
