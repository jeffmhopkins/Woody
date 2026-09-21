# D4 — BOM generation and `datasheets/` de-duplication

Agent D4, 2026-09-21. Cold: I read no file under `docs/review/**`, `docs/log/**`
or `docs/research/**`. One repo-wide `grep` I ran for `hardware/datasheets`
printed two matching lines from review files in its output; I did not open those
files and nothing below rests on them.

Provenance on every claim: `[repo]` path:line, `[calc]` with the arithmetic,
`[proto]` for output of a prototype I ran in the session scratchpad (never in
the tree), `[from memory]`.

Everything marked `[proto]` was run against **copies** in
`/tmp/.../scratchpad/proto` and `/tmp/.../scratchpad/ds`. No corpus file, CSV or
tool was touched by me.

**The tree moved under me while I worked.** Other agents of this wave committed
`3473436`, `7deb71f` and `44697f9` between 18:50 and 18:55 UTC, and at 19:00 the
working tree carried uncommitted edits to `config/figures.yaml`,
`docs/decisions/0003/0004/0006`, `hardware/bom.csv` and
`tools/check-staleness.py` that are not mine. Where a measurement moved I give
both readings and the time. Everything structural (138 rows, 11 columns, 139
CRLF, 53 unnamed refdes, 56 citations, 31 moving datasheet paths) was
**re-verified at 19:00 UTC** and is unchanged.

---

## 0. The five measurements this design is built on

| | Value | Source |
|---|---|---|
| `hardware/bom.csv` | 138 rows × 11 cols, **139 CRLF, 0 bare LF**, no embedded newlines. 126 890 bytes at 18:50, 127 671 at 19:00 after a concurrent edit to one `notes` field | `[repo]`, `[calc]` byte count |
| Backticked citations of the file | **56** (`bom.csv` ×38, `hardware/bom.csv` ×4, inside `[repo] …` tags ×14) | `[calc]` grep over corpus + `tools/` |
| BOM refdes **named on no `hardware/**` page** | **53 of 138** | `[calc]`, strict word-boundary match |
| Corpus references to `datasheets/<dir>/<file>` | **75**, of which **31** point into the two directories I propose to dissolve | `[calc]` at 19:00; 76 at 18:50, before `7deb71f` fixed one — see §6 |
| Artefacts on disk under `datasheets/` | **77**; `MANIFEST.csv` 98 rows (77 OK-ish, 20 BLOCKED, 1 NOT-FETCHED) | `[repo]`, `[proto]` tool output |

Two of these are the whole story. **53 of 138 rows cannot be assigned to a
circuit by reading the circuits**, and **13 of the 31 moving datasheet paths
live inside `bom.csv` itself** — so parts 1 and 2 of this slice interlock.

---

# Part 1 — the BOM generator

## 1. Fragment format, CRLF, and the ordering rule

### Layout: the fragment sits beside the page it derives from

```
hardware/
  controller/
    carrier.md
    carrier.bom.csv              <- NEW
    cluster-boards.md
    cluster-boards.bom.csv       <- NEW
    _instrument-common.bom.csv   <- NEW  (no page; see §2)
  module/
    pitch-stage.md
    pitch-stage.bom.csv
    … one per page …
    _module-common.bom.csv
  _umbilical.bom.csv
  _enclosure.bom.csv
  _tooling.bom.csv
  bom.csv                        <- GENERATED, unchanged path, unchanged name
```

Not `hardware/bom/`. Putting `pitch-stage.bom.csv` next to `pitch-stage.md`
means a `git log --follow`, a directory listing and a PR diff all show the page
and its parts together. The project's one failure mode is "fixes land where the
editing is happening; they do not land where the reader looks" `[repo]
CLAUDE.md:11-12`. Same basename, same directory, is the cheapest possible
answer to that.

The generated master stays at `hardware/bom.csv`. **Do not move or rename it** —
56 backticked citations `[calc]` and two tools `[repo] tools/check-staleness.py:112,
tools/verify-datasheets.py:92` point at it.

### Columns

Fragments carry the master's **11 columns in the master's order**, plus two
page-owned columns the generator projects away (§5):

```
ref,category,part,manufacturer,description,package,qty,status,source,adr,notes,label,page_note
```

The master is written with exactly the first 11. That keeps `bom.csv` an
11-column file and every existing consumer working unchanged.

### CRLF and byte-identity

`csv.writer(out, lineterminator="\r\n")`, per `[repo]
docs/reference/repo-maintenance.md:132-136`. Fragments are CRLF too, so a row
moves between fragment and master without a line-ending change.

**The ordering rule is a hand-written list in the tool, not `glob()` and not
`sorted()`:**

```python
ORDER = ["carrier", "cluster-boards", "_instrument-common", "_umbilical",
         "breath-receive-stage", "breath-output-stage", "pitch-stage",
         "mod-channels", "digital-and-supervision", "power-entry",
         "_module-common", "_enclosure", "_tooling"]
```

Rows come out in `ORDER`, and within a fragment in **file order**. Three
properties follow:

1. **Deterministic** — no filesystem order, no locale-dependent sort.
2. **Adding a circuit is a visible one-line diff to `ORDER`**, not a silent
   re-sort of 138 rows. A fragment on disk but absent from `ORDER` is a
   `PROBLEM`, and so is the reverse — so you cannot add a fragment and have its
   rows quietly vanish.
3. **Appending a row appends a line.** Sorting by refdes instead would scatter
   every insert through the file.

`merge-manifests.py` sorts globally (`rows.sort(key=lambda r: (r[2] or "zzz", r[0]))`,
`[repo] tools/merge-manifests.py:41`). That is right for a manifest keyed on a
path and wrong here: the BOM's readable grouping *is* the circuit grouping.

### Proven, not asserted

I split the real `bom.csv` into 13 fragments by the §2 rule and merged it back
`[proto]`:

```
bom.csv: 138 rows x 11 cols from 13 fragments (rewritten)
rows only in original: 0   rows only in generated: 0
bytes orig 126890  generated 126890  delta 0
CRLF: 139   bare LF: 0
```

(Against the 18:50 snapshot. The row *set* and the line endings are what the
proof is about; the byte total tracks whatever the `notes` fields say that
minute.)

Two runs on an unchanged tree:

```
0851cf7960e2ab701f2985f0ed386c82  bom.csv
bom.csv: 138 rows x 11 cols from 13 fragments (unchanged)
0851cf7960e2ab701f2985f0ed386c82  bom.csv
```

The tool compares before writing and leaves the file alone when identical, so a
no-op run does not even touch the mtime.

One value changed in one fragment (`C-FILT-MOD` 82 nF → 100 nF) `[proto]`:

```
98c98
changed lines: 2
```

**One row changed, one line moved.** That is the `repo-maintenance.md` §4 trap
(`[repo]:132-136` — a three-row change landing as a 130-row diff) closed
mechanically rather than by remembering.

### The one unavoidable cost

`hardware/bom.csv` today is in **append order across circuits** — rows 2-25 are
the original set and rows 26-139 were appended by successive waves `[repo]
hardware/bom.csv`. Generation puts them in circuit order. **The row *set* is
identical and the byte count is identical (126 890 in, 126 890 out, `[proto]`),
but the first commit is a 138-line reorder.** Land that reorder as its own commit,
with nothing else in it, so `git log -p hardware/bom.csv` stays readable
afterwards.

---

## 2. Which rows belong to which fragment

### The rule

> A row lives in the fragment for the circuit **whose page derives its value**.
> Not where it is mentioned, not where it is mounted — where the number comes
> from.

"Where it is mounted" fails on `PLATE-TOP` (a mechanical part whose dimensions
`cluster-boards.md` derives). "Where it is mentioned" fails on `R-BIAS-INAMP`,
which is named **once in the whole corpus, on `pitch-stage.md:359`, as a
contrast** `[repo]` — the breath in-amp's bias resistor, mentioned only by the
pitch page.

I applied the rule to all 138 rows `[proto]`:

```
  carrier.bom.csv                     44 rows
  cluster-boards.bom.csv              12 rows
  breath-receive-stage.bom.csv        10 rows
  breath-output-stage.bom.csv         11 rows
  pitch-stage.bom.csv                  9 rows
  mod-channels.bom.csv                 2 rows
  digital-and-supervision.bom.csv      6 rows
  power-entry.bom.csv                 15 rows
  _module-common.bom.csv               7 rows
  _instrument-common.bom.csv           6 rows
  _umbilical.bom.csv                   4 rows
  _tooling.bom.csv                     1 rows
  _enclosure.bom.csv                  11 rows
  total 138
```

### The rows that do not fit, named

**(a) Genuinely fitted on more than one page — `_module-common.bom.csv` (7).**
These are module-wide conventions, not one circuit's parts:

| Ref | Qty | Pages it is fitted on |
|---|---|---|
| `C-DECOUPLE` | 19 | every module IC supply pin — 4 pages `[repo] bom.csv:43` |
| `R-OUT-PROT` | 6 | pitch ×1, mod ×4, breath-output ×1 `[repo] bom.csv:42` |
| `D-JACK-CLAMP` | 6 | the same six jacks `[repo] bom.csv:52` |
| `R-OPAMP-IN` | 7 | pitch + mod `[repo] bom.csv:51` |
| `J-CV`, `PANEL`, `PCB-MODULE` | | module-level, no page |

**This names three circuits the corpus has no page for**: jack output
protection (`R-OUT-PROT` + `D-JACK-CLAMP`, six identical networks drawn three
times), module decoupling, and the module panel. They are already shared; the
fragment split only makes it visible.

**(b) Spans both ends of the umbilical — `_umbilical.bom.csv` (4).**
`J-UMBILICAL` qty 2 is **one chassis connector at each end** `[repo]
bom.csv:19-20`; `CABLE-UMB` is `category=controller` `[repo] bom.csv:57` while
`J-UMBILICAL` is `category=module`. One row, two assemblies. This is a genuine
category defect the split surfaces (see the NOTE output below).

**(c) Board-level and mechanical, no circuit — `_instrument-common` (6),
`_enclosure` (11), `_tooling` (1).** `PCB-CARRIER`, `PCB-CLUSTER`, `WIRE-LOOM`,
`MECH-GNDBOND`, `MECH-COAT`, `MECH-WINDOW`; the eleven enclosure rows; `BENCH`,
which is `part=n/a, status=available` `[repo] bom.csv:25` and arguably should
not be in a bill of materials at all.

**(d) The pneumatic front end.** `TUBE`, `MECH-MOUTH`, `MECH-PTFE` are
`category=controller` `[repo] bom.csv:33,53,58` but mechanical in nature. They
belong with `U-BREATH`/`SKT-BREATH` in `carrier.bom.csv`, because that page owns
the sensor port. I put them in `_enclosure` on the first pass and **the
generator's own category cross-check caught me** (below).

### How the generator detects a row owned by two circuits

Exactly the `merge-manifests.py` mechanism, keyed on `ref` alone `[repo]
tools/merge-manifests.py:35-39`:

```python
if r[0] in seen:
    problems.append(f"{frag}:{i} refdes {r[0]} is already owned by "
                    f"{seen[r[0]]} - a row belongs to exactly one circuit")
    continue
seen[r[0]] = f"{frag}:{i}"
```

This is the same check as today's duplicate-refdes test, moved one level up. It
now catches a *stronger* error: not just "the same refdes twice in one file"
but "two circuits both claim it", with both file:line locations named.

### The category cross-check earns its place immediately

I also had the generator compare each row's `category` against the assembly its
fragment sits on. First run, 8 hits `[proto]`; four were **my assignment errors**
(`TUBE`, `MECH-MOUTH`, `MECH-PTFE`, `BENCH`), and after fixing those, three
remain:

```
  cluster-boards:5 PLATE-TOP category 'mechanical', fragment sits on 'controller'
  cluster-boards:8 PLATE-THUMB category 'mechanical', fragment sits on 'controller'
  _umbilical:4 CABLE-UMB category 'controller', fragment sits on 'module'
```

All three are legitimate — a mechanical plate whose geometry a board page
derives; a cable that is bought against the instrument and mates with the
module. **So emit this as `NOTE:` and exit 0, not `PROBLEM:` and exit 1.** Three
one-line explanations is a healthy standing output; a hard failure would be
turned off within a week.

---

## 3. Where the integrity checks live, and what generation adds

### Move them, do not copy them

| Check | Today | After |
|---|---|---|
| Column count | `check-staleness.py:117-118` `[repo]` | `merge-bom.py`, per fragment, before the master exists |
| Duplicate refdes | `check-staleness.py:119-121` `[repo]` | `merge-bom.py`, as cross-fragment ownership |

Both are *input* checks. Run on the generated file they are checking the
generator, not the author. `check_bom()` keeps its **reporting** role (the
`bom.csv: N rows × M cols` line the hook surfaces, `[repo]
check-staleness.py:164-165`) and drops the two tests.

### `check_refdes` is dead code, and this is the moment to fix it

`check_refdes` is defined in `tools/check-staleness.py` and **never called**.
`main()` calls `corpus_files`, `check_figures`, `check_bom` and nothing else,
and `bom_refs` — bound from `check_bom()`'s return — is never read `[repo]`.
Verified twice, before and after a concurrent agent edited the file:

```
$ grep -n "check_corpus_shape(\|check_refdes(\|check_bom(\|check_figures(" tools/check-staleness.py
79:def check_corpus_shape(files):
103:def check_figures(files):
153:def check_bom():
168:def check_refdes(files, bom_refs):
203:    live, refuted, spec = check_figures(files)
204:    bom_problems, bom_refs, ncols, nrows = check_bom()
```

> **A second dead check appeared while I was writing this, and someone should
> look before it lands.** At 19:00 UTC the working tree carried an uncommitted
> +55-line change to `tools/check-staleness.py` adding `check_corpus_shape()`
> — a genuinely good check, with a `MIN_CORPUS_FILES = 30` tripwire and a
> comment recording that `mv docs/decisions docs/adr` took the corpus from 33
> files to 18 and still printed `PASS` `[repo] working tree`. **It is not called
> from `main()` either** (see the grep above: it has a `def` line and no call
> site). That is not my change and it is in flight, so it may be wired up a
> minute after I write this — but a check that is added and not called is the
> project's named failure mode aimed at the tool that exists to prevent it, and
> it has now happened twice in the same file. **Whoever lands it: call it, and
> add a test that fails when a `def check_*` has no call site.** That test is
> four lines and it would have caught both.

I ran it by hand by importing the module and calling it `[proto]`. It reports
36 tokens drawn on hardware pages with no
BOM row. About half are false positives it has no defence against — package
names (`SOIC-16`, `SOT-23-5`, `SOT-23-6`, `SOIC-14`, `SOD-323`, `TO-92`), part
fragments (`R-78E5`, `CI-SN`, `KS-33`, `KS-33-3D`), a toolchain (`ESP-IDF`).
That is very likely why it is dead.

The other half are real, and they are exactly the class the new structure makes
checkable:

```
C-ADC-BULK   J-DISP   J-LED-L   J-LED-R   R-LED-PD   R-CS-SER   R-MOSI-SER
R-SCLK-SER   R-CLR-PD   R-PRESENCE   R-OE-PU   LK-CLR   C-GATE   C-TIMER
R-IN   R-FB   R-OFF   R-OFFNEG   R-LED   N-FET   R-OFFINJ*  R-TERM-CHAIN*
```
(`*` = explicitly deleted parts, correctly present as refutations.)

**Revive it as `merge-bom.py`'s job, scoped per fragment**, which kills the
false positives: a page's drawn labels are checked against **its own fragment**,
and the fragment's new `label` column (§5) declares the local symbol
(`R_G` → `R-GAIN-INAMP`, `C_diff` → `C-FILT-BREATH`, `C-TIMER` →
`C-TIMER-LOADSW`). Package strings never appear in a `label` column, so they
never trip it.

### The three new error classes generation introduces

**(i) A refdes in no fragment.** Impossible by construction if the tool refuses
to write a master when a fragment names a refdes twice — but the *reverse*
(a row deleted from its fragment by accident) is silent. Guard: the generator
writes a count and `check-staleness.py` asserts it. I would also assert a
**floor**: a run that drops more than 5 rows below the previous master needs
`--allow-shrink`. Cheap, and it is the failure that loses parts.

**(ii) A fragment row that survives after its circuit is deleted.** This is the
one the checker "cannot catch" class `[repo] CLAUDE.md:68-73` —
`mod-channels.md` justifying its topology on a deleted watchdog is the named
precedent. Under the new layout it becomes mechanical: **a `*.bom.csv` whose
sibling `*.md` does not exist is a `PROBLEM`**, and the `_`-prefixed fragments
are the explicit, enumerated exceptions. Deleting a page now forces a decision
about its parts in the same commit.

**(iii) A hand-edit to the generated master.** §4.

---

## 4. Stopping the hand-edit — recommend the re-generate-and-compare check

`hardware/bom.csv` is the most-cited file in the repository (56 backticked
citations, `[calc]`), and `repo-maintenance.md:78-81` records that a direct edit
to the generated `MANIFEST.csv` "survives until the next run of that tool and
then disappears without a word" — and that **it actually happened, and was
caught by re-running the tool rather than by noticing** `[repo]`.

### Recommendation: `tools/merge-bom.py --check`, wired into `check-staleness.py`

Regenerate into memory, byte-compare, name the first differing line `[proto]`:

```
FAIL hardware/bom.csv is GENERATED and does not match hardware/bom/*.bom.csv
     1 line(s) differ, first at line 98
     Your edit is in the generated file and the next run of
     tools/merge-bom.py will destroy it.
     Move it into the owning fragment, then re-run tools/merge-bom.py.
```

and after regenerating:

```
PASS hardware/bom.csv matches its fragments
```

**Cost: none to the file format, one function, ~15 lines.** And it catches the
*other* direction too — a fragment edited and never regenerated from — which no
banner or refusal can.

### The three alternatives, and what each costs

| Mechanism | Cost | Verdict |
|---|---|---|
| **Header banner in the CSV** | A `# GENERATED` line makes row 0 the banner, and `csv.DictReader` takes row 0 as the header. Two tools break today (`check-staleness.py:113`, `verify-datasheets.py:102` `[repo]`) and every future consumer — SKiDL, KiBot's interactive BOM `[repo] docs/reference/pcb-pipeline.md:236-237` — needs a skip rule. **Reject.** | No |
| **A `GENERATED` sentinel in the first data row's `notes`** | Survives DictReader, but it is a fake part and it will end up in a purchase list. **Reject.** | No |
| **Pre-commit refusal** | Real, and it is a *one-line* change: the hook at `[repo] .claude/settings.json` currently emits only `systemMessage` + `additionalContext` — **it surfaces, it does not block.** Adding `permissionDecision: "deny"` makes it block. Cost: it fires on `Bash(git commit *)` only, so any other commit path escapes it, and a deny is felt as an obstruction on a deliberate work-in-progress commit. | Yes, but as the *carrier* for the check above, not instead of it |

**Do all three of the useful ones, in this order:** (1) the compare check, always;
(2) surface it through the existing hook alongside the staleness line; (3) a
one-line `README` note at the head of the `hardware/` directory listing, **not**
inside the CSV. And add `bom.csv` to the `## 1. The four kinds of file` table in
`repo-maintenance.md:17` — that table currently lists `datasheets/MANIFEST.csv`
as the *only* generated file `[repo]`, and it must not stay that way for a day.

Do **not** gitignore `bom.csv`. It has to be readable on the web at the 56
places that cite it.

---

## 5. The component tables — recommendation: **generate them, and move their prose into the fragment**

### First, the premise needs correcting

The brief says eight pages carry `## Component table` sections. **Two do**
`[repo] hardware/controller/carrier.md:843, hardware/controller/cluster-boards.md:484`.
The six module pages carry `## Values` or `## Component values` instead `[repo]
breath-output-stage.md:124, breath-receive-stage.md:154, pitch-stage.md:124,
mod-channels.md:95` — and `digital-and-supervision.md` and `power-entry.md` have
no value table at all `[repo]`.

That difference is not cosmetic. **The two `Component table` sections are keyed
on BOM refdes. The four `Values` tables are keyed on local schematic labels that
are not BOM refdes**: `R1`, `R2`, `R_G`, `C_diff`, `C_cm`, `V_ref`, `R-IN`,
`R-FB`, `R-OFF`, `R-OFFNEG`, `Output RC` `[repo] breath-receive-stage.md:157-166,
breath-output-stage.md:127-135`.

So the two naming systems never meet, and the numbers confirm it:

- **53 of 138 BOM rows are named by no hardware page** `[calc]` — including
  `U-DAC`, `U-DIFFRX`, `R-PRECISION`, `J-CV`, `SW-POWER`, `U-LOADSW`,
  `R-GAIN-INAMP`, `C-FILT-BREATH`, `R-BREATH-SUM`, `R-BREATH-OFF`,
  `C-TIMER-LOADSW`, `C-GATE-LOADSW`, `D-CLAMP-BREATH`, `FB-IN`, `D-REVPOL`,
  `C-BULK-RAIL`, `U-TVS-MODULE`. The DAC, the in-amp and the load switch are all
  in that list.
- **36 tokens are drawn on pages with no BOM row** `[proto]`, ~20 of them real.
- `R-SER-BREATH` (qty 2, `[repo] bom.csv:61`) appears **nowhere**; the five
  corpus hits are all `R-SER-BREATH-INST`, a different part `[repo]
  carrier.md:189,207,221,345,865`.
- `U-OPA-PITCH` is named once, on `breath-receive-stage.md:146`, in a sentence
  about the op-amp budget — **not on `pitch-stage.md`** `[repo]`.

**This is the largest single defect in my slice**, and per-circuit fragments
force it into the open: you cannot assign a row to a circuit when no circuit
names it.

### What the tables hold that the BOM cannot

1. **A `Confidence` column** whose values are `[repo]`, `[calc]`, `[from memory]`,
   `proposed`, `settled`, `contradictory`, `[repo] note is wrong`, and **figure
   ids** — `cref-out-node`, `riso-ref-topology` `[repo] carrier.md:850-880`. Both
   ids are real entries in `config/figures.yaml:276,312` `[repo]`, so this column
   is already half-citing the register by name.
2. **Struck-through rows.** `~~U-KEYS, R-KEY-PU, …~~ — Not on this board`
   `[repo] carrier.md:851`. A negative statement about a part that used to be
   here. A BOM has no row shape for "deliberately absent".
3. **Per-board quantity splits.** `cluster-boards.md`'s table has `LH | LT | RH |
   RT` columns: `R-KEY-PU` is **6, 6, 6, 6 = 24**, against `bom.csv`'s single
   qty 24 `[repo] cluster-boards.md:493, bom.csv:91`. The split is a layout fact
   with a real argument attached (`RT` carries the three reserved spare-switch
   positions) and the BOM has one number.
4. **Proposed rows with no BOM entry at all** — `C-ADC-BULK`, `R-LED-PD`,
   `J-LED-L/-R`, `J-DISP`, `TP-*`, `LK-*` `[repo] carrier.md:856-882`.

### The recommendation

**Generate the table; give the prose a column in the fragment.**

Fragments carry 13 columns: the master's 11 plus

- **`label`** — the local schematic symbol (`R_G`, `C_diff`, `R-IN`,
  `C-TIMER`). Empty where the page uses the refdes. This is the join that does
  not exist today, and it is what makes the revived `check_refdes` (§3) precise.
- **`page_note`** — what today's `Job` column holds, carrying its provenance tag
  inline (`[repo]`, `[calc]`, `proposed`, or a `figures.yaml` id). The corpus
  already mandates that tag vocabulary `[repo] CLAUDE.md:102-104`, so this is
  not a new convention — it is the existing one, given a column.

`tools/merge-bom.py` then does two things: projects columns 1-11 into
`hardware/bom.csv`, and renders each page's table between markers:

```markdown
## Component table

<!-- BEGIN generated: carrier.bom.csv -->
| Ref | Value | Job |
|---|---|---|
| `U-ADC` | MCP3202-CI/SN | `VDD` **is** `VREF`; 3V3 from the dev board `[repo]` |
<!-- END generated -->
```

Four things then become checkable that are not today:

- A value can no longer differ between the page and the BOM. Today they are two
  hand-kept copies, which is the project's named failure mode `[repo]
  CLAUDE.md:8-12` applied to 122-odd rows.
- Every fragment row appears on its page and every page row has a fragment row.
- `label` gives the drawing-to-BOM join, so `R_G`, `C_diff` and `C-TIMER` stop
  reading as unbacked parts.
- A `page_note` naming a `figures.yaml` id can be validated against the register.

### Three things to keep hand-written, and say so

- **The struck-through "not on this board" rows.** They are negative space, not
  parts. Keep them in prose under the generated block.
- **The `LH/LT/RH/RT` split.** Either a 14th `qty_by` column with a
  `sum(qty_by) == qty` assertion, or leave that one table hand-written and let
  the checker assert the sum. I lean to `qty_by` — the 24-vs-21 discrepancy it
  encodes has an argument attached `[repo] cluster-boards.md:493` and deserves a
  machine check.
- **`proposed` rows with no BOM entry.** They must stay visible. Give them a
  fragment row with `status=proposed` instead — `check-staleness.py` already has
  a vocabulary for deliberately-unresolved rows `[repo] CLAUDE.md:133-135`.

**Do not delete the tables in favour of a citation.** The reader is looking at
an ASCII drawing and needs the value next to it; a link to a 138-row CSV is the
"fixes do not land where the reader looks" failure, deliberately introduced.

---

# Part 2 — `datasheets/` de-duplication

## 6. The axis, and the fragments-must-not-be-edited conflict

### The current axis is not one axis

`[repo]` file counts: `connectors/` 22, `discrete-and-power/` 18,
`mechanical/` 16, `other-semi/` 15, `texas-instruments/` 6 — **77 artefacts**.

Four of the five are function buckets. **`texas-instruments/` is a vendor
bucket**, and it exists only because one wave banked six TI documents together.
It puts `LM317LZ` (a regulator) and `SN74AHCT125` (a level shifter) away from
every other regulator and every other logic part. `other-semi/` is then, by
construction, "semiconductors from anyone else" — the ADC, the pressure sensor,
four 74HC165s, five WS281x parts, two XINGLIGHT surrogates, the LT5400 and an
LDO.

### Recommended axis: **what part of the design the document describes**, six buckets

```
datasheets/
  analog/               8   DAC8568CIPW, INA828IDR, OPA2197, REF5050,
                            MCP3202-CI-SN, MPXV4006DP, MPXV4006-AN1646, LT5400
  logic/                5   74HC165 ×4, SN74AHCT125
  led/                  6   WS2812B, WS2812B-2020, WS2812C, WS2815,
                            XL-0807RGBC ×2
  discrete-and-power/  20   unchanged + LM317LZ + ME6217C33M5G
  connectors/          22   unchanged
  mechanical/          15   unchanged − the duplicate WS2815
```

**22 of 77 paths move** — `texas-instruments/` (6), `other-semi/` (15), and the
duplicate `mechanical/WS2815-worldsemi-datasheet.pdf` (1). `connectors/`,
`discrete-and-power/` and `mechanical/` are already function-axis and are left
alone: renaming `discrete-and-power/` → `power/` for tidiness would move another
18 paths and buy nothing.

Verified by running it `[proto]`:

```
MOVED: 22 path(s) re-filed via .moves.csv (fragments untouched)
MANIFEST.csv: 97 rows from 8 fragments | 76 ok, 20 blocked, 1 other
Counter({'connectors': 22, 'discrete-and-power': 20, 'mechanical': 15,
         'analog': 8, 'led': 6, 'logic': 5})
```

### Resolving the append-only-fragment conflict

This is the hard part and it has a clean answer.

`repo-maintenance.md:18` says a fragment must not be edited because "a `BLOCKED`
row is the honest record of a gap *when it was written*" `[repo]`. That
protection is about **status, source URLs, error text and notes** — the
researcher's findings. It is not about where the repository files a byte for
byte identical PDF today.

**`merge-manifests.py` already rewrites the `file` column.** Lines 30-34
`[repo]`:

```python
# Fragments disagree on what `file` is relative to: some wrote
# "datasheets/connectors/x.pdf" (repo root), others "connectors/x.pdf".
r[2] = r[2].strip()
if r[2].startswith("datasheets/"):
    r[2] = r[2][len("datasheets/"):]
```

Path normalisation at merge time is therefore **already an established,
documented, sanctioned transformation that does not count as editing a
fragment.** A move table is the same transformation with a lookup instead of a
prefix strip.

So: add **`datasheets/.moves.csv`**, append-only itself, and apply it at exactly
that point.

```csv
old_path,new_path,when,why
texas-instruments/OPA2197.pdf,analog/OPA2197.pdf,2026-09-21,vendor bucket retired
other-semi/74HC165.pdf,logic/74HC165-ti-scls116e.pdf,2026-09-21,junk drawer split; name says whose
other-semi/74HC165-toshiba.pdf,logic/74HC165-toshiba-1986-excerpt.pdf,2026-09-21,junk drawer split
mechanical/WS2815-worldsemi-datasheet.pdf,led/WS2815.pdf,2026-09-21,DE-DUPLICATED: byte-identical (sha 72e22d2f...)
…22 rows…
```

```python
if r[2] in MOVES:
    moved_from[r[2]] = MOVES[r[2]]
    r[2] = MOVES[r[2]]
```

Properties:

- **No fragment changes.** All eight `.manifest-R*.csv` stay byte-identical.
- **The move is itself a record**, dated and reasoned — which is what the
  append-only rule is protecting.
- **A BLOCKED row is untouched**, because it has no `file` value to rewrite.
- **The tool announces it every run** (`MOVED: 22 path(s) …`), so nobody
  rediscovers the layout by accident.
- It composes with the existing prefix strip and needs no header change, so
  `merge-manifests.py`'s exact-header check keeps working on all eight
  fragments.

### The corpus half — and there is already one broken path

31 corpus references point into the two dissolving directories `[calc]`:

| File | Refs |
|---|---|
| `hardware/bom.csv` | **13** |
| `config/figures.yaml` | 6 |
| `hardware/controller/carrier.md` | 4 |
| `docs/decisions/0014-lighting.md` | 3 |
| `ROADMAP.md`, `docs/decisions/0003`, `0006`, `hardware/controller/cluster-boards.md`, `hardware/module/pitch-stage.md` | 1 each |

**13 of the 31 are inside `hardware/bom.csv`** — which Part 1 makes generated,
so those 13 rewrites land in the fragments and the master follows. That is the
interlock: do the BOM split first, then the datasheet move.

**Nothing checks these paths today, and one was dead when I started.**
Resolving all 76 corpus path references against disk at 18:50 gave exactly one
miss `[calc]`: `hardware/bom.csv` (`F-CHAIN` notes) cited
`datasheets/discrete-and-power/MF-PSMF010X.pdf`, while the file on disk and in
`MANIFEST.csv:35` is `MF-PSMF010X-polyfuse.pdf` `[repo]`.

**It was fixed at 18:54:47 by another agent of this wave** — commit `7deb71f`,
*"The corpus's only dangling datasheet path, found by a researcher"* `[repo]
git log`. Re-measured at 19:00: 75 references, zero misses. The short spelling
survives only in `docs/review/**` and `docs/review/2026-09-21-preflight/`, where
it is a historical record and must stay `[repo] CLAUDE.md:77-81`.

**That does not weaken the argument, it is the argument.** A dangling path in
the most-cited file in the repository was found by a person reading, twice in
one hour, by two different agents, because **no tool looks.** It is the
checker-cannot-see-it failure mode `[repo] CLAUDE.md:68-73` applied to file
paths, and a re-slice moving 22 files is exactly the operation that creates
twenty more of them.

**So add the rule regardless of whether the re-slice happens:**
`verify-datasheets.py` gains a pass that extracts every `datasheets/<dir>/<file>`
string from the corpus and asserts it exists, with a hint from `.moves.csv` when
the old path is a known move. That converts the re-slice from a 31-place manual
sweep into a mechanical one, and it would have caught `MF-PSMF010X.pdf` on its
first run instead of costing a reader's attention.

---

## 7. Real duplication: which are defects, which are deliberate

### Defect — the WS2815 double bank

Two `MANIFEST.csv` rows, two paths, **identical SHA-256 `72e22d2f740c…`**
`[proto]` `[repo] .manifest-R3.csv:5, .manifest-R6.csv:13`:

```
WS2815  ->  mechanical/WS2815-worldsemi-datasheet.pdf
WS2815  ->  other-semi/WS2815.pdf
```

Two researchers fetched the same Git-LFS object from the same FastLED URL. One
filed it under `mechanical/`, which is wrong on any axis — it is an LED IC
datasheet. `repo-maintenance.md:94-96` already calls this out: "Two rows for the
same file is tolerated (WS2815 is banked twice under two paths, same SHA) but it
is not tidy" `[repo]`.

**Fix via `.moves.csv`**: both rows resolve to `led/WS2815.pdf`, one file on
disk, both researchers' rows preserved. The merge tool needs one new rule —
when a move collapses two rows onto one path **and their `sha256` matches**,
that is a resolved duplicate, not a `PROBLEM` `[proto]`:

```
DE-DUPLICATED: 1 row(s) collapsed onto a path another row already holds, same sha256:
        - .manifest-R6.csv:13 WS2815 -> led/WS2815.pdf
```

Without that rule the existing `key in seen` branch `[repo]
merge-manifests.py:36-38` raises a `PROBLEM` and exits 1.

> ### A regression this fix introduces, found by running it
>
> Collapsing the duplicate takes the token `ws2815` from **3** part strings to
> **2**, and `merge-manifests.py`'s `LIKELY` heuristic fires on
> `any(_freq.get(t) == 2 for t in shared)` `[repo]:120`. The new `CHECK:` entry
> `[proto]` was:
>
> ```
> - WS2815 LED strip
>     possibly covered by: WS2815  ->  led/WS2815.pdf
> ```
>
> **That is precisely the match the tool was tuned to refuse** — "the WS2815
> strip → the WS2815 IC, because those are different dies" `[repo]
> merge-manifests.py:71-74, datasheets/README.md:39-41,
> repo-maintenance.md:105-107`. The strip's width, pitch and cut length are not
> in the IC datasheet `[repo] MANIFEST.csv` WS2815 notes.
>
> **Fix:** compute `_freq` over **every part string a fragment ever carried**,
> including collapsed rows, not over the de-duplicated output. Token frequency
> should describe the corpus of researcher statements, not the merge result.
> Verified: 6 `CHECK:` rows before, 5 after, `WS2815 LED strip` gone `[proto]`.
>
> Worth stating plainly: **de-duplicating this file without that one-line change
> would have broken the single heuristic this directory's README holds up as its
> proof of good judgement.**

### Deliberate — the four 74HC165 documents

All four are `status=OK` with distinct SHAs and distinct content `[repo]
MANIFEST.csv`:

| File | What only it has |
|---|---|
| `74HC165.pdf` (TI SCLS116E) | the original fetch; the part the corpus first cited |
| `74HC165-nexperia.pdf` | **answers the 3.3 V threshold question in the negative** — Table 6 tabulates V_IH/V_IL at 2.0 / 4.5 / 6.0 V only |
| `74HC165-onsemi.pdf` | **the only one with a 3.0 V column**, and it contradicted the repo |
| `74HC165-toshiba.pdf` | 1986 databook excerpt, pages 225-230 cut out of a 675-page 23.6 MB scan |

**Not duplication — this is the mechanism `CLAUDE.md:52-57` is built on.** "A
number read off a banked document beats one from a review", and the 74HC165's
3.3 V threshold is the first of the three examples it names `[repo]`. Four
vendors disagreeing is the evidence.

**What the tooling should do:** nothing about the count. What is missing is a
**datasheet of record**. `U-KEYS` is `part=74HC165` with `manufacturer` empty
`[repo] bom.csv:8`, so nothing states which of the four is authoritative for the
fitted part. Recommend the BOM row's `manufacturer` be filled (onsemi, since it
is the only one characterising at 3.0 V) and a `verify-datasheets.py` note when
a BOM part matches more than one `OK` row and its `manufacturer` is empty.

### Deliberate — the seven WS281x-family documents

Four distinct roles, all flattened into `status=OK` `[repo] MANIFEST.csv`:

| Role | Rows |
|---|---|
| **Fitted** | `WS2815` (→ `LED-SIDE`) |
| **Surrogate, must never be cited as the fitted part** | `XL-0807RGBC-WS2812B` ×2 — `datasheets/README.md:142-147` `[repo]` |
| **Bracketing** | `WS2812B` (5050) and `WS2812B-2020`, banked for the 2 kHz PWM figure absent from the 5050 sheet `[repo]` MANIFEST notes |
| **Refuted assumption** | `WS2812C` — what the corpus assumed the matrix was, before the Waveshare schematic showed `WS2812B-0807` `[repo] datasheets/README.md:120-124` |

**None is a defect.** But two things should change:

1. **`SURROGATE ONLY` is a convention with no enforcement, and it is already
   inconsistent.** `README.md:142-147` says **three** rows are surrogates — the
   two XINGLIGHT LEDs *and* the 1986 Toshiba excerpt. The string `SURROGATE ONLY`
   occurs on exactly **two** rows `[calc]` `grep -c SURROGATE MANIFEST.csv` = 2;
   the Toshiba row's notes begin "Toshiba TC74HC165P/F data pages, 6 pp,
   EXCERPTED from…" `[repo]`. Either the README overcounts or the row is
   unmarked. Make the marker machine-checked and the question answers itself.
2. **`verify-datasheets.py` will count a surrogate as BOM coverage.** Its
   `uncovered` test matches against the **whole manifest text** —
   `hay = _norm(" ".join(" ".join(r.values()) for r in rows))` `[repo]:97` —
   which includes surrogate rows. I tested it: **latent, not live.** Removing
   both surrogate rows from the haystack changes nothing `[proto]`:

   ```
   uncovered WITH surrogates   : 2  ['U-ESD-USB: USBLC6-2SC6', 'D-TVS-BREATH: PESD12VS1UB …']
   uncovered WITHOUT surrogates: 2  [same]
   BOM rows covered ONLY by a surrogate: []
   ```

   Recommend excluding `SURROGATE ONLY` rows from the coverage haystack anyway.
   It costs one filter and closes the hole before the 0807 matrix gets a BOM row.

---

## 8. `hardware/datasheets/` — delete it

It contains one file, `.gitkeep`, zero bytes `[repo]`. No corpus file references
it: `grep -rn "hardware/datasheets"` over `CLAUDE.md`, `README.md`, `ROADMAP.md`,
`config/`, `docs/decisions/`, `docs/reference/`, `firmware/`, `hardware/` and
`tools/` returns **nothing** `[calc]`. `git log` shows one commit touching it
`[repo]`.

It is worse than clutter: it is a **decoy at exactly the path someone looks for
first.** A reader in `hardware/` who wants the OPA2197 datasheet finds an empty
`datasheets/` directory sitting beside the pages, and the real bank is one level
up. `verify-datasheets.py` walks `ROOT/datasheets` only `[repo]:19,71`, so a PDF
dropped into `hardware/datasheets/` would be banked nowhere, hashed by nothing,
and invisible to every check.

**Delete it.** If a per-board landing area is ever wanted, it should be a
`README.md` pointing at `/datasheets/`, never an empty directory.

---

## 9. Order of work

1. **`tools/merge-bom.py` + 13 fragments**, in one commit with the 138-line
   reorder and nothing else. Add `hardware/bom.csv` to `repo-maintenance.md:17`'s
   generated-file table in the same commit.
2. **Move the two checks** out of `check_bom`; add the regenerate-and-compare
   check; wire it into the existing hook.
3. **Fix `_freq`** in `merge-manifests.py` (one-line, independent of everything
   else, and it makes the tool's own stated refusal robust).
4. **Add `.moves.csv` + the corpus path check** to `verify-datasheets.py`. The
   check catches the live `MF-PSMF010X.pdf` miss on its first run.
5. **Re-slice `datasheets/`** — 22 file moves, 31 corpus rewrites of which 13 are
   now fragment edits.
6. **Generate the component tables**, last, because it depends on the `label`
   column and on the 53 unnamed refdes being resolved.
7. **`git rm hardware/datasheets/.gitkeep`**, any time.

Step 6 is the expensive one and the valuable one: **53 of 138 BOM rows are named
by no drawing**, and no tool in this repo can see that today.

---

## 10. Claims in this report a reviewer should re-check by hand

Filed here rather than left implicit, per `CLAUDE.md:110-115`.

- **53 unnamed refdes** — from a word-boundary regex over `hardware/**/*.md`. A
  refdes named only inside an ASCII drawing with adjacent box characters could
  be missed. The count is a floor, not an exact figure; spot-check `U-DAC` and
  `U-DIFFRX`, which I did check by hand and which return zero hits `[repo]`.
- **"56 backticked citations"** counts backticked strings containing `bom.csv`,
  including the 14 inside `[repo] …` provenance tags. A stricter reading gives
  42. Either way it is the most-cited file.
- **The `.moves.csv` mechanism** is argued from `merge-manifests.py:30-34`
  already normalising the `file` column. If the owner reads the append-only rule
  as covering paths too, the whole of §6 needs a different answer — most likely
  symlinks, which I would not recommend.
- **My first fragment assignment was wrong for four rows** and the generator's
  own category cross-check found them, not me. The assignment in §2 is a
  proposal; the three remaining NOTEs are judgement calls, not facts.
- **`MF-PSMF010X.pdf` was a live defect at 18:50 and was fixed at 18:54:47 by
  commit `7deb71f`.** Do not file it as an open finding. File the *absence of a
  path check* as the finding.
- **`check_corpus_shape` having no call site** was read out of an uncommitted
  working tree at 19:00 UTC and is somebody else's work in progress. Check it
  against whatever landed before repeating it.
- **The ordering rule and the `.moves.csv` mechanism are both prototypes**, not
  the tools. They ran green in scratchpad against copies of the real data; they
  have not run in the tree.
