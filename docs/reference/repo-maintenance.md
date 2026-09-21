# Repo maintenance — what is generated, what is a record, what may be edited

**Written 2026-09-21.** Every trap in this file cost real time at least once.

The corpus rules are in `CLAUDE.md`. This page is the layer under them: **which
files a tool owns, which files are history, and where an edit will be silently
thrown away.**

---

## 1. The four kinds of file

| Kind | Files | Rule |
|---|---|---|
| **Design corpus** | `hardware/**`, `docs/decisions/**`, `docs/reference/**`, `config/**`, `firmware/**`, `README.md`, `ROADMAP.md` | Must be self-consistent. This is what `check-staleness.py` checks. |
| **Historical record** | `docs/review/**`, `docs/log/**`, `docs/research/**` | **Never "corrected".** A 2026-09-21 review saying "8HP" is right as a record of what was true when written. Excluded from the checker by design. |
| **Generated** | `datasheets/MANIFEST.csv` | **Edits are silently destroyed.** See §3. |
| **Fragments (append-only, per author)** | `datasheets/.manifest-R*.csv` | One per research wave. **Do not edit another wave's fragment** — a `BLOCKED` row is the honest record of a gap *when it was written*. See §3 for how to close someone else's gap without touching it. |

Not tracked, and gitignored: `.staleness/`, `.staleness-report.txt`, `*.tmp`.

---

## 2. `tools/check-staleness.py` — the mechanical half of the one failure mode

Run by a `PreToolUse` hook before every `git commit`, so forgetting it is
visible rather than silent. It greps the corpus for values `config/figures.yaml`
lists as `forbidden`, skipping lines whose wording refutes them.

### The trap: a forbidden list written from the document in front of you

**This is the mechanism behind the fourth and worst recorded instance of the
project's named failure mode**, and it is worth stating as a rule because it is
not obvious:

> When a figure moves, **grep the corpus for the OLD value first, and add one
> pattern per spelling you find.** Do not write the forbidden list from the
> document you happen to be editing.

`sensor-full-scale` moved and the list was written from its owner ADR. The
corpus spelled the same number **seven other ways** — an en dash without spaces,
a table cell with pipes, the superseded `0.2 + 0.766` with no ` V`. (That
spelling is quoted here as a refuted example, which is why the checker allows
this line and would not allow it in a design page.) Each missed by one or two
characters against a case-sensitive literal `find`. Eleven derived statements
stayed live while the checker reported **zero hits**, and two cold reviewers
found it independently hours apart.

### Other things it will not catch

- **Anything semantic.** It greps for values. It cannot see that a page still
  *depends* on a deleted part, or that an argument survives its own refutation.
  For that, run a review wave — at gates, not per commit.
- **A figure with an empty `forbidden` list.** A `disputed` entry protects
  nothing until it is settled and its old values are listed.

### Two structural holes, both found and fixed

1. **It matched line by line**, so any forbidden phrase that *wrapped* across a
   line break was invisible. It now joins lines into a single stream with a
   line map. Lines join with exactly **one** space and internal spacing is left
   alone, because several forbidden patterns are code-block spellings
   containing runs of spaces.
2. **Refutation detection is per-match context**, not per-file. A line that
   quotes an old value must carry refutation wording (`was`, `superseded`,
   `refuted`, `no longer`, …) *on that line or its neighbours*.

---

## 3. `datasheets/` — banked, not linked

`MANIFEST.csv` has one row per artefact with a SHA-256.
`tools/verify-datasheets.py` must pass before committing anything under
`datasheets/`.

### The trap: `MANIFEST.csv` is generated

**`tools/merge-manifests.py` rebuilds it from the `.manifest-R*.csv` fragments.
A direct edit to `MANIFEST.csv` survives until the next run of that tool and
then disappears without a word.** This happened in the session that wrote this
page; it was caught only by re-running the tool, not by noticing.

**To record something new about a banked document**, you have three options, in
order of preference:

1. **Fix the tooling**, if what you want is for a *check* to see something.
   That was the right answer when `verify-datasheets.py` could not tell that a
   manifest row naming a **refdes** (`"... (SW-POWER) - NKK Series M"`) is
   coverage for a BOM part whose number it cannot match. A vendor catalogue for
   a whole family, with the MPN chosen later out of it, is a case no
   part-number token can ever reach.
2. **Put it in `hardware/bom.csv`**, if it is a fact about the *part* rather
   than about the *document*.
3. **Add your own fragment** only if you actually fetched something. Two rows
   for the same file is tolerated (WS2815 is banked twice under two paths, same
   SHA) but it is not tidy.

### Closing someone else's `BLOCKED` row

Wave R8 established the convention, and it is in `datasheets/README.md`:

- **DECLARED** — your `OK` row quotes the blocked row's **exact `part` string**
  *and* contains the word `SUPERSEDES`. Opt-in, zero false positives.
- **LIKELY** — shared distinctive tokens, printed under `CHECK:`, never
  asserted as fact. Deliberately tuned to **refuse** `WS2812B-0807` →
  `WS2812B-2020` and the WS2815 strip → the WS2815 IC, because those are
  different dies.

### Traps when banking

- **A 200 and a `.pdf` filename prove nothing.** An RS-online URL recorded as
  the LT1641's mirror is a real PDF *of the LT4256*. A Diodes Inc URL found
  searching for a 1N4148W is the **MMST3906**. **Grep the extracted text for
  the part number, always.**
- **Several key documents have no text layer at all.** Gateron's drawing, both
  Laird bead drawings, the Neutrik outlines, the TE socket page and both toggle
  drawings are vector CAD — `pdftotext` returns a byte or two and the
  dimensions exist only in the picture. They were read by **rendering at
  150 dpi and looking**. Anything that pulls a dimension out of `datasheets/`
  programmatically will silently get nothing from these.
- **`pdftotext` is not installed in every session.** `python3 -c "import pypdf"`
  works and was used for every extraction in this session.

---

## 4. `hardware/bom.csv` — eleven columns, CRLF

```
ref,category,part,manufacturer,description,package,qty,status,source,adr,notes
```

- **The file is CRLF.** Python's `csv.writer` defaults to `\r\n`, but setting
  `lineterminator="\n"` rewrites every line in the file and buries a three-row
  change in a 130-row diff. **Always pass `lineterminator="\r\n"`.** Check with
  `git diff --stat` before committing: a BOM edit should touch about as many
  lines as rows you meant to change.
- **Validate column count and duplicate refdes after any edit** —
  `check-staleness.py` does both.
- The `notes` column is append-only in practice: corrections are added after a
  ` | ` with a date, and the superseded text is left in place. That is what
  makes the checker's refutation detection work, and it is why rows are long.
- **`TBD`/`open` must say what decides them.** Two rows are deliberately
  blocked on a datasheet and say so; that is correct, not a defect.

---

## 5. `config/figures.yaml` — the register

One entry per shared quantity. The owning document states it; **every other
document cites it by name and does not restate the number.**

Changing a tracked figure is three steps, never one:

1. Update `value`.
2. Move the old value into `forbidden` — **and see §2's trap first.**
3. Run the checker. It then tells you every file to fix. Fix them in the same
   commit.

Fields in use beyond the documented ones, all optional and all free text:
`derivation`, `provenance_note`, `companion`, `false_positive_note`,
`escape_note`, `consequence`, `adaptation`, `dc_error`, `robustness`,
`toggle_row`, `floor`, `candidates`, `decided_by`. **`false_positive_note` is
the one that earns its keep** — it tells the next person why a legitimate
occurrence of a forbidden string is allowed, so they do not "fix" it.

A `disputed` entry must carry `decided_by` naming **what decides it** — a
bench measurement, a datasheet, or a choice that is the owner's. An entry that
says "somebody should look at this" is not trackable.

> **A correct figure filed as `disputed` is the dangerous kind**, because it
> stops getting re-checked. This has happened once (the OPA2197's 1 nF
> capacitive-load limit, filed as refuted on the strength of a coincidence with
> the INA828's identical headline number).

---

## 6. Running the tools

```
python3 tools/check-staleness.py      # terse; detail lands in .staleness/report.txt
python3 tools/verify-datasheets.py    # SHA-256 + BOM coverage
python3 tools/merge-manifests.py      # REGENERATES datasheets/MANIFEST.csv
python3 tools/rewrite-paths.py        # restructure only; --apply/--verify/--invert
```

All three are expected to pass before a commit that touches the corpus. The
staleness hook surfaces the first one automatically.

### What each one refuses to do, and why it now refuses

All three used to fail **open** — they reported success on a tree that had been
broken underneath them. All three were fixed on 2026-09-21 after the failures
were reproduced, not argued:

| Tool | Used to | Now |
|---|---|---|
| `check-staleness.py` | `os.walk` a missing `CORPUS_DIRS` entry and print `PASS`. Moving `docs/decisions/` took the corpus from 33 files to 18 and still scored green | Asserts its own inputs exist, carries a file-count floor, and **prints the corpus file count on every run** — the count is what you check, not the verdict |
| `check-staleness.py` | Define `check_refdes()` and never call it — for the tool's whole life | Asserts its own wiring: any `def check_*` with no call site is a failure. It found `check_refdes` on the first run |
| `merge-manifests.py` | Write a header-only `MANIFEST.csv` from zero fragments, exit 0, destroying 98 rows of provenance | Refuses. The fragments are **dotfiles**, so `git mv datasheets/*` leaves them behind — move the directory whole |
| `verify-datasheets.py` | Skip BOM coverage silently when `bom.csv` was absent | Refuses to print a summary it cannot stand behind |

---

## 7. The 2026-09-21 restructure

Paths changed. **`path-map-2026-09-21.csv` in this directory maps every old
path to its new one** — every tracked file has a row, including the ones that
did not move, because the question a reader actually asks is "did this path
change?" and a map of only the movers cannot answer it.

**References inside `docs/review/**`, `docs/log/**` and `docs/research/**`
point at the old paths and are deliberately not corrected** (§1, `CLAUDE.md`
§6). There are over eight thousand of them, and history outnumbers the corpus
roughly 24:1 on path references — so any whole-repo `sed` is wrong by that
factor. A path is a value; rewriting one inside a dated record makes that
record say something its author did not. Resolve them through the map.

`tools/rewrite-paths.py --invert --baseline <rev>` is the proof that the move
changed no content: it applies the inverse rewrite to every moved file and
requires the result byte-identical to the original. A numeric diff is the weak
form — it cannot see a permutation, a non-numeric fact, or an edit inside a
path. Byte identity under inversion can.
