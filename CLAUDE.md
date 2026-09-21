# Woody — working rules

A custom electronic woodwind instrument: a tethered digital controller joined
by a 2 m Cat5 umbilical to a 10HP Eurorack analog CV module.

## The one failure this project actually has

**A value changes, and the documents derived from it do not follow.** Three
review waves found it roughly ninety times. It is not carelessness that more
care fixes — it has happened inside commits whose own message was about it.
Fixes land where the editing is happening; they do not land where the *reader*
looks.

So the rules below are mechanical. Follow them instead of trying harder.

### 1. Shared figures live in `config/figures.yaml`. Cite, do not restate.

If a quantity is in that register, the owning document states it and every
other document **cites it by name**. Do not copy the number.

The model is USB MIDI opt-in — the only fact in this corpus with zero
staleness findings against it, because it is stated once and cited from three
other files.

### 2. Changing a tracked figure is three steps, not one

1. Update `value` in `config/figures.yaml`.
2. **Grep the corpus for the OLD value first**, and move one `forbidden`
   pattern into that entry **per spelling you find**.
3. Run `python3 tools/check-staleness.py`. **It then tells you every file to
   fix.** Fix them in the same commit.

Step 2 says "grep first" because writing the list from the document in front of
you is how the worst recorded instance of this happened. `sensor-full-scale`
moved, the list was written from its owner ADR, and the corpus spelled the same
number **seven other ways** — an en dash without spaces, a table cell with
pipes, a version with no ` V`. Each missed by a character or two against a
case-sensitive literal match. Eleven derived statements stayed live while the
checker reported **zero hits**.

A `PreToolUse` hook runs the checker before every `git commit` and surfaces
the result, so forgetting step 3 is visible rather than silent.

**Three traps in step 2, all paid for.**

- **Write the pattern in the spelling of the file it must match.** The BOM is
  CSV and spells `97mm`, `-9.6V` and `~5.7us`; a prose page spells `97 mm`,
  `−9.6 V` and `` `V_IL` at **5.7 ``. Patterns written from the prose miss the
  CSV every time, and the same stale text is then in the repository twice,
  because `hardware/bom.csv` is generated from the fragment.
- **A pattern containing a hard wrap can never fire.** The checker searches a
  line-joined stream, so `"220 Ω with\n~200 pF"` sat in the register matching
  nothing — and reading exactly like a pattern that matches nothing.
- **A refutation split across an ASCII drawing's gutter does not count.** The
  lines are joined with the `│` still in them, so "This line │ carried" is not
  "this line carried". Keep the correction and the value it corrects on one
  line.

And the counterpart to grepping first: **most hits will be legitimate.** Nine
of the eleven live `8HP`/`6HP` hits were the ADRs correctly narrating
6HP → 8HP → 10HP. Four of the six live `4.7 V` hits were a different node
entirely, one of them negative. A pattern that fires on a correct sentence is
worse than no pattern, because its cheapest fix is to make the sentence wrong.
Use `false_positive_note`.

### 3. Datasheets are banked, not linked

`datasheets/` holds the actual documents, one `MANIFEST.csv` row each with a
SHA-256. `python3 tools/verify-datasheets.py` must pass before committing
anything under it. A part that could not be fetched gets a row too, with
`status=BLOCKED` and the exact URLs — an honest gap is useful, a fabricated
file is not.

**A number read off a banked document beats one from a review.** Three
figures moved this way in one afternoon: the 74HC165's 3.3 V threshold (the
datasheet has no 3.3 V row, and the 0.7/0.3 ratio *breaks* at 2 V), the
1N5817's `V_f` modulation (an estimate at 75–80 mV, 120 mV off the curve),
and the WS2815's `V_IH` (8.4 V from reading `0.7 × VDD` against the wrong
`VDD`). Mark provenance on every figure so the weak ones are visible.

### 4. Datasheet edits go in a fragment — `MANIFEST.csv` is generated

`tools/merge-manifests.py` rebuilds `datasheets/MANIFEST.csv` from the
`.manifest-R*.csv` fragments. **A direct edit to `MANIFEST.csv` survives until
the next run of that tool and then disappears without a word.** Do not edit
another wave's fragment either — a `BLOCKED` row is the honest record of a gap
*when it was written*. `docs/reference/repo-maintenance.md` §3 gives the three
things to do instead.

### 5. What the checker cannot catch

Anything semantic. It greps for values. It cannot see that a page still
*depends* on a part that was deleted, or that an argument survives its own
refutation — `mod-channels.md` justified its whole topology on a watchdog that
no longer exists, and no grep would find that.

For that, run a review wave (see below). At gates, not per commit.

### 6. `docs/review/`, `docs/log/` and `docs/research/` are historical records

They are **not** the corpus and must never be "corrected". A 2026-09-21 review
saying "8HP" is right as a record of what was true when it was written. The
checker excludes them by design.

The design corpus — the thing that must be self-consistent — is:
`hardware/**`, `docs/decisions/**`, `docs/reference/**`, `config/**`,
`firmware/**`, `README.md`, `ROADMAP.md`.

**Paths in those records point at pre-2026-09-21 locations and are not to be
corrected.** Resolve them through `docs/reference/repo-maintenance.md` §7.

## Review waves

**Nine have run.** `docs/review/` is the index; this list is not kept in sync
by anything and said "three" for months while the directory held nine. The
ones with the most transferable method are
`2026-09-20-cold-review/`, `2026-09-21-hardware-and-standards-review/`
(20 agents), `2026-09-21-staleness-sweep/` (12 agents) and
`2026-09-21-pre-merge-review/` (22 agents, and the one that found the checks
themselves were passing on a corpus with live stale values in it).

Each directory's `README.md` states its method; `VERIFIED.md` records what was
checked by hand and where an agent was wrong; `STATUS.md`, where a wave has
one, records what actually landed.

What makes them work, and is worth keeping:

- **Cold.** Reviewers may not read prior review directories. Agreement between
  agents that cannot see each other is evidence; agreement with a document
  they just read is not.
- **Slice by fact domain, not by file.** The defect is one fact across five
  files. Slicing by file gets five agents reporting one defect from one side.
- **Provenance on every claim** — `[repo]`, `[calc]` with the arithmetic
  shown, `[web]` with the URL, `[from memory]`. An unmarked claim is a defect
  in the report.
- **Node-indexed findings**, filed against a circuit node or BOM reference
  rather than a file and line.
- **At least one agent auditing the previous round's fixes.** Every wave has
  found that the last round's fixes were partial.

## Checking an agent's work

Findings are claims. Several have been wrong, and one was wrongly marked
disputed by me — which is worse, because a wrong finding gets caught by the
next reviewer while a finding filed as handled does not. Verify before
repeating, and record the verification.

## Where the details live

- **`docs/reference/repo-maintenance.md`** — which files are generated, which
  are history, what each tool owns, and every trap that has cost time once.
  Read it before touching `datasheets/`, `bom.csv` or the tools.
- **`docs/review/<wave>/STATUS.md`**, where a wave has one — what that wave
  produced versus what actually landed in the corpus. A wave with thirteen
  reports and four landed slices looks finished from the outside and is not.

## Hardware conventions

- Every schematic page is Markdown with ASCII drawings and derivations inline.
  One circuit per directory: the page, its `bom.csv` fragment, its
  `circuit.yaml`, and `notes.md` for what the circuit *used to be*.
- **`hardware/bom.csv` IS GENERATED.** `tools/merge-bom.py` rebuilds it from
  the per-circuit `bom.csv` fragments, so **a direct edit survives until the
  next run of that tool and then disappears without a word** — the same trap
  as `MANIFEST.csv` in §4, on the most-cited file in this repository. Edit the
  fragment, then re-run the tool. A row lives with the circuit **whose page
  derives its value**. `merge-bom.py --check` proves the master still matches,
  and the commit hook runs it.
  It is 11 columns **and CRLF**; pass `lineterminator="\r\n"` to `csv.writer`,
  or a three-row change lands as a 130-row diff.
  `hardware/unplaced.csv` holds the rows no schematic page names — a count of
  parts nobody has drawn, not a dumping ground.
- Mark unresolved things `TBD`/`open` **with what decides them**. Two BOM rows
  are deliberately blocked on a datasheet and say so; that is correct, not a
  defect.
