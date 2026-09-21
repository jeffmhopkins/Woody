# Repo maintenance — what is generated, what is a record, what may be edited

**Written 2026-09-21.** Every trap in this file cost real time at least once.

The corpus rules are in `CLAUDE.md`. This page is the layer under them: **which
files a tool owns, which files are history, and where an edit will be silently
thrown away.**

---

## §1. The four kinds of file

| Kind | Files | Rule |
|---|---|---|
| **Design corpus** | `hardware/**`, `docs/decisions/**`, `docs/reference/**`, `config/**`, `firmware/**`, `README.md`, `ROADMAP.md` | Must be self-consistent. This is what `check-staleness.py` checks. |
| **Historical record** | `docs/review/**`, `docs/log/**`, `docs/research/**` | **Never "corrected".** A 2026-09-21 review saying "8HP" is right as a record of what was true when written. Excluded from the checker by design. |
| **Generated** | `datasheets/MANIFEST.csv`, **`hardware/bom.csv`** | **Edits are silently destroyed.** See §3 and §4. `bom.csv` joined this row on 2026-09-21 and this table did not say so for several hours. |
| **Fragments (append-only, per author)** | `datasheets/.manifest-R*.csv` | One per research wave. **Do not edit another wave's fragment** — a `BLOCKED` row is the honest record of a gap *when it was written*. See §3 for how to close someone else's gap without touching it. |
| **Fragments (per circuit)** | `hardware/**/bom.csv`, `hardware/unplaced.csv` | The source the BOM is generated from. Editable — this is where a part change goes. §4. |

Not tracked, and gitignored: `.staleness/`, `.staleness-report.txt`, `*.tmp`.

---

## §2. `tools/check-staleness.py` — the mechanical half of the one failure mode

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

## §3. `datasheets/` — banked, not linked

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
   for the same file is tolerated — WS2815 has one from each of two researchers,
   both now pointing at `led/WS2815.pdf` — but it is not tidy. (It used to be
   two rows at two *paths*; the duplicate under `mechanical/` was de-duplicated
   by the 2026-09-21 re-filing and has a `deleted` row in the path map.)

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
- **Text-layer coverage is per-document *and* per-element, so measure it, do
  not assume it.** One vendor sheet can carry fully extractable prose and fully
  outlined dimension callouts on the same page. Measured across all 60 banked
  PDFs, 2026-09-21:

  | Extracts | Documents |
  |---|---|
  | **Nothing at all — 0 characters** | `connectors/NE8FDP.pdf`, `connectors/NE8MC.pdf`, `connectors/PJ301M-12.pdf` |
  | **A title block and no more** | both Laird bead drawings (72 and 170 chars), `connectors/100SP1T2B3M2QEH.pdf` (157), `connectors/NE8MX.pdf` and `connectors/NE8MX6.pdf` (~400) |
  | **Everything, dimensions included** | `connectors/TE-IDC-SOCKET-CATALOG-82012.pdf` (239 kB) and `connectors/NKK-SERIES-M-TOGGLE.pdf` (49 kB). **This page listed both as textless and was wrong**: `8.89`, `8.9` and `6.5` are all in their text layers |
  | **Prose yes, drawing callouts no** | `mechanical/GATERON-KS-33-VENDOR-SPEC-DRAWING.pdf` — 11 kB of extractable spec text, and not one occurrence of `1.20` or `14.0`, the dimensions this project reads off sheets 3 and 6 |

  So **search the extracted text for the string you actually want**, not for
  "some text". The Gateron row is the one that has cost something:
  `ks33-geometry.md` recorded contact bounce as unpublished through four review
  waves, and *"Bounce Time: 5msec Max.(at 16 in/sec. actuation speed)"* was
  sitting in the extractable text of a document already in the bank.

- **The companion file is often the machine-readable one.**
  `connectors/NE8FDP.pdf` extracts zero characters. `connectors/NE8FDP.dxf`,
  banked beside it, has a full `TEXT`/`MTEXT` layer carrying every dimension
  the corpus derives from that connector. Its *geometry* entities are to
  drawing scale and rotated per view, so read the text layer, not the
  coordinates.

- **For a number that lives only in a curve, extract the content-stream
  geometry and calibrate against the gridlines.** Reading a render is the last
  resort, not the first: a reviewer's eyeball pass on the Laird bias curves was
  wrong by up to **60 %**, and the vector extraction corrected it.

- **`pdftotext` is not installed in every session, and a bare `import pypdf`
  raises a Rust panic in this container.** The system `cryptography` package's
  pyo3 binding fails to load — `ModuleNotFoundError: No module named
  '_cffi_backend'`, then `pyo3_runtime.PanicException` — and pypdf imports it
  eagerly although it needs it only for *encrypted* PDFs. Two routes, both
  verified against the bank on 2026-09-21:

  ```python
  # 1. pypdf, with the eager cryptography import stubbed out
  import sys, types
  for m in ('cryptography', 'cryptography.hazmat', 'cryptography.exceptions',
            'cryptography.hazmat.primitives', 'cryptography.hazmat.primitives.ciphers',
            'cryptography.hazmat.primitives.padding', 'cryptography.hazmat.backends'):
      sys.modules[m] = types.ModuleType(m)
  import pypdf
  ```

  ```python
  # 2. pymupdf - pip install pymupdf. Text AND rendering, and no stub needed
  import pymupdf
  doc  = pymupdf.open(path)
  text = "".join(p.get_text() for p in doc)
  pix  = doc[5].get_pixmap(dpi=150)        # for when you do have to look
  ```

  **The stub has one real limit and the bank contains a case.** Stubbing
  `cryptography` leaves pypdf unable to decrypt an AES-encrypted PDF, so
  `connectors/NKK-SERIES-M-TOGGLE.pdf` raises `DependencyError: cryptography>=3.1
  is required for AES algorithm` — on the document whose text layer carries the
  toggle dimensions. pymupdf opens the same file with an empty password and
  reads all 28 pages. **Prefer pymupdf**, and keep the stub for a session where
  pypdf is the only thing installed.

---

## §4. `hardware/bom.csv` — eleven columns, CRLF, **and generated**

```
ref,category,part,manufacturer,description,package,qty,status,source,adr,notes
```

> ### The trap: `bom.csv` is generated too, since 2026-09-21
>
> **`tools/merge-bom.py` rebuilds it from 24 per-circuit `bom.csv` fragments.
> A direct edit survives until the next run of that tool and then disappears
> without a word** — the same trap §3 documents for `MANIFEST.csv`, on the
> **most-cited file in this repository**.
>
> Unlike the manifest's, this one is caught: `merge-bom.py --check`
> regenerates into memory, byte-compares, and names the first differing line.
> `check-staleness.py` runs it, so the commit hook fails on a hand edit.
>
> **Edit the fragment, then re-run the tool.** A row lives with the circuit
> **whose page derives its value** — not where it is mentioned, not where it
> is mounted.
>
> **`hardware/unplaced.csv` holds the 50 rows of 138 that no schematic page
> names.** That is not a dumping ground, it is a count: a part nobody has
> drawn. Two of its clusters name circuits this corpus has no page for — six
> identical jack-protection networks drawn three times, and nineteen
> decoupling capacitors with no home.
>
> *This section described `bom.csv` as the file you edit for several hours
> after it stopped being one. Found by a cold reviewer. It is the project's
> named failure mode, in the document that exists to record exactly this
> trap.*

- **The file is CRLF.** Python's `csv.writer` defaults to `\r\n`, but setting
  `lineterminator="\n"` rewrites every line in the file and buries a three-row
  change in a 130-row diff. **Always pass `lineterminator="\r\n"`.** Check with
  `git diff --stat` before committing: a BOM edit should touch about as many
  lines as rows you meant to change.
- **Validate column count and duplicate refdes after any edit** —
  `merge-bom.py` does both, one level up: it now catches "two circuits both
  claim this refdes", with both file:line locations named, which the old
  same-file check could not see.
- The `notes` column is append-only in practice: corrections are added after a
  ` | ` with a date, and the superseded text is left in place. That is what
  makes the checker's refutation detection work, and it is why rows are long.
- **`TBD`/`open` must say what decides them.** Two rows are deliberately
  blocked on a datasheet and say so; that is correct, not a defect.

---

## §5. `config/figures.yaml` — the register

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

## §6. Running the tools

```
python3 tools/check-staleness.py      # terse; detail lands in .staleness/report.txt
python3 tools/verify-datasheets.py    # SHA-256 + BOM coverage
python3 tools/merge-manifests.py      # REGENERATES datasheets/MANIFEST.csv
python3 tools/merge-bom.py            # REGENERATES hardware/bom.csv
python3 tools/merge-bom.py --check    # ...or just prove it still matches
python3 tools/check-conservation.py <rev> <source> <dest>...   # split audit
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

## §7. The 2026-09-21 restructure

Paths changed. **`path-map-2026-09-21.csv` in this directory maps every old
path to its new one** — every tracked file has a row, including the ones that
did not move, because the question a reader actually asks is "did this path
change?" and a map of only the movers cannot answer it.

> **The as-of points, because they are not the same date and the map is
> applied at content granularity.**
>
> - **Old side** — the `old` column is exactly the tracked tree at `81c081d`,
>   the commit before A0 wrote the map. 287 paths, and it is a bijection onto
>   that tree: nothing in it is missing and nothing in it is invented.
> - **New side** — HEAD, reconciled against `git ls-files` on 2026-09-21 after
>   the pre-merge review wave closed. 410 rows: 405 tracked files, plus 4
>   `deleted` and 1 duplicate destination.
>
> **The "every tracked file has a row" sentence above was false for most of a
> day, and it is worth saying how.** The map was written at A0 and described
> Phase A1 only. Phase B then created files it had never heard of and the
> datasheet re-filing moved 22 more, which left **143 tracked files with no row
> and 22 rows whose `new` path existed on *neither* side**. A reader asking
> "did this path change?" about the TI 74HC165 sheet — filed under the retired
> `other-semi/` bucket — got `unmoved`, for a file that had moved directory
> *and* been renamed.
>
> **A map is not a document you keep true by being careful, it is one you
> assert.** The check is four lines and belongs in any future restructure's
> tooling; run it whenever files are added, because a new file is an orphan the
> moment it is committed:
>
> ```
> tracked = set(git ls-files)
> placed  = {r.new for r in rows if r.kind != "deleted"}
> assert not (tracked - placed)      # no tracked file without a row
> assert not (placed - tracked)      # no row pointing at nothing
> ```
>
> Both assertions hold as of this writing, and the second one is the half that
> caught the 22: they all pointed at `datasheets/` paths that no longer
> existed, and nothing had ever looked.
>
> **`datasheets/.moves.csv` is the authority for the datasheet rows**, not
> anyone's memory of the re-filing. It records all 22 moves with a reason each,
> and two of them **rename the file as well as the directory**: the two
> 74HC165 sheets that were `74HC165.pdf` and `74HC165-toshiba.pdf` are now
> `74HC165-ti-scls116e.pdf` and `74HC165-toshiba-1986-excerpt.pdf` under
> `logic/`. A map corrected from directory names alone gets those two wrong
> and still looks right. (Paths there are relative to `datasheets/`, the way
> `.moves.csv` and the `MANIFEST.csv` file column write them — and the way
> this paragraph has to write them, because `verify-datasheets.py` requires
> every `datasheets/…` path in the corpus to resolve on disk, which a
> deliberately retired one does not.)

**The `kind` column**, which is the part a reader acts on:

| `kind` | `old` | `new` | Means |
|---|---|---|---|
| `unmoved` | path | same path | Corpus file, path unchanged |
| `unmoved-history` | path | same path | `docs/review/**`, `docs/log/**`, `docs/research/**`. Path unchanged, and **never corrected** (§1) |
| `moved` | old path | new path | Rewritable: `rewrite-paths.py` reads exactly these rows |
| `deleted` | old path | *empty* | Gone. The `note` says where its content went, if anywhere |
| `created` | *empty* | path | Did not exist at the old-side as-of point. The `note` names the commit and, for a Phase B split, the page it was split out of |
| `created-history` | *empty* | path | Same, under `docs/review/**` — a record written after the map, never corrected |

**A `created` row's `old` is deliberately empty even when the file's text came
out of a known parent page.** `hardware/module/panel-led/panel-led.md` was
split out of `hardware/module/power-entry.md`, but power-entry has its own
`moved` row, and putting a second old→new pair on the same old path would make
`rewrite-paths.py` rewrite every reference to power-entry into a page about
the LED. The parent belongs in `note`, where a reader uses it and a tool does
not.

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
