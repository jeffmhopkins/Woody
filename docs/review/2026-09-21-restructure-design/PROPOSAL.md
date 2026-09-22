# The reconciled target structure

**Written 2026-09-21**, after six cold agents reported and their load-bearing
claims were checked by hand (`VERIFIED.md`). This is the synthesis the
migration executes against. Where a detail lives in one of the six reports,
this page **cites it and does not restate it** — which is rule 1, and the
whole point.

> **Status: proposed. Nothing has moved.** The owner signs this off before
> Phase A begins.

---

## 1. What the wave changed about the plan

Three things, each of which would have damaged the restructure if it had run
on the original plan:

1. **`check-staleness.py` failed open on a moved directory** (D5, verified).
   The entire restructure would have run under a green check with 45% of the
   corpus unscanned. Fixed in `9310848` before anything moves.
2. **`check_refdes()` was dead code**, and a check I added during the wave was
   caught in the same unwired state. Found independently by D2, D3 and D4 — an
   incident three times is a class. The tool now asserts its own wiring.
3. **Two tracked figures were live-wrong in the corpus**, one of them inside
   its own owner document. Fixed in `c4fb614` by citation, not by patching
   prose.

None of these are restructure work. All three had to land first.

---

## 2. The target tree

Primary axis is the **circuit block**, with thin board pages above it. The
breath chain crosses two boards and the umbilical, and `pcb-pipeline.md`'s own
netlist precursor records two net-name collisions that are both between the two
ends of one crossing block — so a board-first split would divide exactly the
chain that must stay together.

```
hardware/
  <board>/                        carrier | cluster | module
    <board>.md                    board-level only: outline, mounting, loom,
                                  panel, and which circuits it carries
    <circuit>/
      <circuit>.md                the schematic: boundary nets, ASCII drawing,
                                  derivations, provenance markers
      <circuit>.bom.csv           fragment; GENERATES hardware/bom.csv
      circuit.yaml                id, title, depends_on, verified_against,
                                  last_reviewed
      notes.md                    past tense only: what this circuit WAS
      sim/                        deck + invocation + banked model ref
  interfaces/
    umbilical.md                  the three board-crossing links
  unplaced.csv                    BOM rows no circuit yet names (see §5)
  bom.csv                         GENERATED. Do not edit
```

**22 circuit directories**, plus two system-level ones that belong to no single
circuit — grounding/returns, and the jack-output-protection convention
currently stated six times across four files. The inventory, with exact source
line ranges, is `D1-circuit-inventory.md`.

**Unchanged, deliberately:** `docs/decisions/` keeps its files, its numbers and
its supersession chain (`D6`). ADR numbers are a live foreign key from all 138
BOM rows, 509 prose references and 8 figure owners, and carry no path syntax —
nothing would find a renumber. `datasheets/` moves as a whole directory or not
at all: its manifest paths are relative, so a whole-directory move rewrites
zero cells (`D4`).

**Naming:** `<circuit>.md`, not `README.md`. All bare backtick references in the
corpus are basenames with no path, so a *move* leaves them literally correct
while a *rename* invalidates every one and makes them ambiguous against the
~15 files already called `README.md` (`D2`).

---

## 3. Where a decision lives

The boundary, settled: **more than one circuit → ADR. Exactly one circuit →
the schematic page.** `notes.md` is past tense only — the circuit's superseded
shelf, the same convention `docs/decisions/README.md` already runs at project
scope.

The best result of the wave is that **this needs no new tooling**: `notes.md`
sits under `hardware/`, so the existing checker already scans it, and the
`REFUTATION` regex is literally a past-tense detector. A past-tense `notes.md`
passes automatically; a present-tense one fails the commit hook the moment it
restates a moved figure (`D2`).

---

## 4. Staleness, extended

Declared edges only. D3's central measurement is that an *inferred* dependency
edge has an unusable noise floor — which is precisely why `check_refdes` was
never switched on — so every new check runs over a `depends_on` block someone
wrote down, not over a graph a tool guessed.

Zero-false-positive checks fail in the hook; noisy ones warn and run at gates
only, matching `CLAUDE.md` §5's "at gates, not per commit". The design, the
field list, the rejected fields and the argument for each are in
`D3-staleness-paradigm.md`.

One change lands before the move: `figures.yaml`'s `owner:` becomes a typed
reference rather than a path. 25 of 33 then stop breaking on a move, and —
more importantly — `owner` becomes something a tool validates. Nothing reads
it today.

---

## 5. The BOM, and the 53 orphans

Fragments generate the master. Proven on real data, not asserted: 138 rows in,
138 out, byte-identical output, identical on a second run, and a one-value
fragment edit producing a two-line diff (`D4`).

**53 of 138 rows are named by no `hardware/**` page at all.** The module pages
key their value tables on local labels (`R1`, `R_G`, `C_diff`) that are not BOM
refdes; the two `Component table` pages key on refdes. **The two naming systems
never meet.** This is the largest single defect the wave found, and per-circuit
fragments force it open, because a row cannot be assigned to a circuit that
does not name it.

Decided: the 53 go to `hardware/unplaced.csv`, which the generator still folds
into the master. Reconciling local labels to refdes is explicit Phase B work,
visible and countable, rather than 53 guesses that afterwards look identical to
53 verifications.

---

## 6. The phase plan

**A0 — guards.** Already landed (`9310848`). Nothing moved.

**A1 — pure move.** `git mv` only. `git diff --cached --numstat` must be all
zeros. Git stores no rename and infers it at ≥50% similarity, so what preserves
`git log --follow` is *not touching content in the move commit*.

**A2 — pure rewrite.** Paths only, no renames. Exit gate is **inverse-rewrite
byte identity**: apply A2's inverse to each file and require it byte-identical
to the old one. That makes "Phase A changed no content" a decidable
proposition rather than a promise, and it subsumes the weaker numeric-token
check. Full criteria in `D5-migration-mechanics.md`.

**B — parallel agents**, one per circuit directory, each confined to its own
directory. Twelve shared files are frozen or integrator-owned; `figures.yaml`
and the BOM are serialised through per-agent patch files, because every split
changes an `owner:`. The freeze list is in `D5`.

**Cold review** follows, including one agent whose only job is content
conservation: every non-trivial line of the old corpus traceable to a line in
the new one, or on an explicit deliberate-deletion list.

---

## 7. What must not be fixed

**8,216 path references in `docs/review/`, `docs/log/` and `docs/research/`
go stale by design** and stay that way — 12,901 counting ADR-by-number, across
137 of 141 files. History outnumbers the corpus 24:1 on path references, so any
whole-repo `sed` is wrong by that factor. `CLAUDE.md` §6: a path is a value, and
rewriting it makes a review say what its author did not.

The old→new mapping is recorded **once**, in a new
`docs/reference/path-map-2026-09-21.csv`, pointed at from one line in
`repo-maintenance.md` and one in `CLAUDE.md`.

---

## 8. Known debt this creates, carried openly

- **One ASCII drawing (`carrier.md:164-211`) spans three circuit blocks.**
  Splitting it means redrawing it, which a content freeze does not allow. It
  goes to one directory whole, and the other two cite it.
- **`pcb-pipeline.md` says "`module.py` importing the six"** — a count coupled
  to the six files in `hardware/module/`. Phase B makes it wrong, it is prose
  rather than a tracked figure, and the checker cannot see it. This is the
  `mod-channels.md` watchdog case waiting to happen, and it is written down
  here so it does not have to be rediscovered.
- **Four more line ranges D1 declined to assign**, listed in its report rather
  than guessed at.
- **`CLAUDE.md` §83-85 ≡ `check-staleness.py` `CORPUS_DIRS` ≡
  `repo-maintenance.md` §1** are one fact in three files and must move in a
  single commit. The checker cannot check its own definition.
