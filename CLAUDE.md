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
2. Move the old value into that entry's `forbidden` list.
3. Run `python3 tools/check-staleness.py`. **It then tells you every file to
   fix.** Fix them in the same commit.

A `PreToolUse` hook runs the checker before every `git commit` and surfaces
the result, so forgetting step 3 is visible rather than silent.

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

### 4. What the checker cannot catch

Anything semantic. It greps for values. It cannot see that a page still
*depends* on a part that was deleted, or that an argument survives its own
refutation — `mod-channels.md` justified its whole topology on a watchdog that
no longer exists, and no grep would find that.

For that, run a review wave (see below). At gates, not per commit.

### 4. `docs/review/`, `docs/log/` and `docs/research/` are historical records

They are **not** the corpus and must never be "corrected". A 2026-09-21 review
saying "8HP" is right as a record of what was true when it was written. The
checker excludes them by design.

The design corpus — the thing that must be self-consistent — is:
`hardware/**`, `docs/decisions/**`, `docs/reference/**`, `config/**`,
`firmware/**`, `README.md`, `ROADMAP.md`.

## Review waves

Three have run: `docs/review/2026-09-20-cold-review/`,
`2026-09-21-hardware-and-standards-review/` (20 agents),
`2026-09-21-staleness-sweep/` (12 agents). Each directory's `README.md` states
its method; `VERIFIED.md` records what was checked by hand and where an agent
was wrong.

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

## Hardware conventions

- Every schematic page is Markdown with ASCII drawings and derivations inline.
- `hardware/bom.csv` is 11 columns. Validate column count and duplicate refdes
  after any edit — `tools/check-staleness.py` does both.
- Mark unresolved things `TBD`/`open` **with what decides them**. Two BOM rows
  are deliberately blocked on a datasheet and say so; that is correct, not a
  defect.
