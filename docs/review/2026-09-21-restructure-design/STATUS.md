# Restructure — what landed, and what has not

**Written 2026-09-21.** A wave with six reports and two landed phases looks
finished from the outside and is not. This file is the difference.

## Phase A: landed

| Commit | What |
|---|---|
| `9310848` | **A0 part 1** — `check-staleness.py`'s fail-open, its dead check, and the crash-reads-as-silence hole |
| `8bb7366` | **A0 part 2** — `merge-manifests.py` and `verify-datasheets.py` guards, `tools/rewrite-paths.py`, the 287-row path map, `repo-maintenance.md` §7 |
| `9daec7f` | **A1** — 8 files moved, 8 renames at 100 %, zero bytes of content changed |
| `8ef7979` | **A2** — 26 path references rewritten across 10 files, nothing moved |
| `f3876be` | **A2b** — 3 relative links that broke invisibly, plus `check_links` so the class cannot recur |

### The eight exit criteria, all passing

1. **A1 is a pure rename set** — `git diff -M --numstat` prints nothing.
2. **Blob identity across A1** — all 8 moved files hash identically to their
   baseline blobs. Checked by hand, hash by hash, before A1 was committed.
   This is the real proof; check 1 depends on rename heuristics and this does
   not.
3. **No surviving old-side path token** — `rewrite-paths.py --verify`, 0.
4. **No corpus number changed** — the masked numeric bag is identical from A0
   to HEAD: 965 distinct tokens, 13,156 occurrences. **This is the weak
   check.** It cannot see a permutation, a non-numeric fact, or an edit inside
   a path string, which is the edit a restructure is most likely to make.
5. **Inverse-rewrite byte identity** — 34 files byte-identical under
   inversion, 0 mismatches, 2 named hand-edits excluded. **This is the strong
   check**, and it is what makes "Phase A changed no content" decidable.
6. All four tools pass. 7. `MANIFEST.csv` regenerates byte-identically.
8. `git log --follow` crosses the move in both directions.

### Three defects found while executing, all in my own tooling

- **`--invert` originally checked only the moved files**, so it would have
  skipped `config/figures.yaml`, `hardware/bom.csv` and five ADRs — the seven
  files where most of the rewriting actually happened, none of which moved. A
  check that proves the easy half is worse than none, because it reads as
  proof.
- **Three markdown links broke and every check passed.** They were bare
  filenames that resolved while the module pages were siblings. A bare
  filename is not a path token, so the rewriter had nothing to match. The fix
  is the general form: **check that what is written now RESOLVES**, not that
  known-old spellings are gone.
- **The baseline was captured before A0 rather than after it**, so the first
  numeric-bag comparison showed deltas that were A0's own content. Harmless
  once noticed, and worth writing down: the baseline for "did the move change
  anything" is the commit *the move starts from*, not the one the work started
  from.

## Phase B: the splits have landed

Seven agents, one per source page, each confined to its own subtree. **0 REAL
GAPS on content conservation for every one of the seven**, verified by me
before staging, plus the hand-built pilot.

| Source page | Became |
|---|---|
| `pitch-stage` (pilot, by hand) | + `notes` + `sim` |
| `breath-output-stage` | + `breath-response-shaper` + `panel` |
| `power-entry` | + `umbilical-load-switch` + `panel-led` |
| `digital-and-supervision` | + `dac8568` + `link-supervision` |
| `cluster-boards` | + `key-register` + `key-switch-network` + `key-marker-and-bits` |
| `carrier` | + `power-entry-instrument` + `breath-excitation-reference` + `breath-adc` + `led-strip-drive` + `display-and-service-uart` |
| `mod-channels`, `breath-receive-stage` | restructured in place |

### What the instruction not to split things bought

Every agent refused at least once to redraw an ASCII figure, and said so.
`carrier.md` §2's opening drawing contains three different circuits in one
connected picture; it stayed whole in the board page and both circuits cite
it. The DAC box excised from the digital drawing left bare columns on both
sides and they were left exactly as cut. Under a content freeze a redraw is
not a move, and seven agents held that line without exception.

### Three checks the splits forced into existence

Each was built because something broke that nothing could see:

- **`check_conservation`** — word shingles, not lines. Caught *me*
  paraphrasing historical text in the pilot instead of moving it verbatim.
- **`check_owners`** — nothing had ever read `figures.yaml`'s `owner:` field.
  Four agents that could not see each other reported the same consequence.
  Note the weaker check would have missed all four: after Phase A every
  owner path still *resolved*; what had broken is that the file no longer
  stated the value.
- **`check_sections`** — seven cross-file `§N` references pointing into files
  their target had left.

**The principle all three share, and the one worth keeping:** do not hunt for
spellings already known to be wrong; assert that what is written now
*resolves*. A forbidden list only knows about breakage someone predicted.

### Four live defects found by agents told not to fix anything

Reported, verified by hand, then fixed by me in separate commits:

1. `mod-channels.md` computed its follower's load current at the superseded
   2.5 V while its own drawing three sections above said otherwise — in the
   page that **owns** that figure.
2. The breath trimmer's null voltage existed as **three values in five
   places**, and `figures.yaml` was one of them; its own note said the figure
   "probably should be" tracked, which was correct and unacted-on. `0.579`
   turned out to be the exact bias-divider omission the register already
   documents one entry above.
3. Three figure owners pointing at files their derivations had left.
4. Seven dead section references.

**The grep-first rule earned itself again** on defect 2: the agent found
three of five occurrences because it was reading only its own page.

## The two cold reviews, and what they cost

Both reviewers were barred from `docs/review/**`, so neither could agree
with anything written here.

**Conservation: nothing was lost.** 97.2 % of the original word-mass present
verbatim; zero dropped passages, table rows, list items, headings or numeric
values, across all four of the gate's structural blind spots. It found two
things the gate cannot see — a duplicated derivation whose five numbers were
untracked, and a `sim/README.md` crediting a page that no longer derives the
figures. Both fixed.

**Tooling: twelve findings, and four were fail-open holes in checks I wrote
to close fail-open holes.** The worst: one non-UTF-8 byte in any BOM fragment
turned the generated-file guard off and flipped FAIL to PASS, because the
check harvested stdout only and the tool crashed to stderr. That is the
fourth instance of the class, inside the check written to close the third.

Tightening `check_owners` from "any token of the value appears" to "the most
distinctive one does" immediately found a real defect: `loop-budget`'s owner
stated neither 196 nor 241, only the shared denominator 250 — and what it
stated instead was a superseded 136 µs at "54 % duty, with room for the loop
to do work", against a true 78–96 %.

### The pattern across all six of my own defects this session

Every one landed where I was editing and not where the reader looks, which
is the mechanism `CLAUDE.md` names in its first paragraph. A commit message
that described two tools while carrying twenty-two file moves. A STATUS
section saying the split had not happened, one commit after it had.
`repo-maintenance.md`, `CLAUDE.md` and `README.md` still describing a
hand-edited BOM hours after it became generated. A guard on the file that
never had the accident while the file that did went unguarded.

**The rules are mechanical because trying harder does not work.** I spent
this session building checks against exactly this failure and committed six
instances of it anyway.

## Still to do

### Known debt, named rather than hidden

- **`circuit.yaml` edges are co-mention, not verified dependency.** Three
  verified false by a reviewer; expect more of that shape. The graph is also
  asymmetric — `carrier/**` and `cluster/**` declare zero `circuit:` edges
  because the agents that wrote their Interfaces tables named peers in prose
  rather than as ids. Every `circuit.yaml` now says so at the top. What *is*
  guaranteed is that every edge resolves.
- **`provides:` and `verified_against:` are empty**, so two checks over them
  can never fail. `check_checks` proves they are *called*; nothing proves
  they *check*.
- **`unplaced.csv` holds the principal IC of five circuits that have
  directories** — `U-DAC`, `U-DIFFRX`, `U-REG-DAC`, `D-REVPOL`, `U-LVL-MOD`.
  Assignment went by refdes string, so parts the drawings label by part
  number fell through. `hardware/module/dac8568/bom.csv` holds two resistors
  and not the DAC.
- **`check_sections` pools all 15 `notes.md` into one namespace** (keyed on
  basename), so a `notes.md §N` reference resolves against any of them.
  Latent, created by the restructure.
- **Two of four board directories have no board page** — `hardware/module/`
  and `hardware/interfaces/`. `panel.md` calls itself "a board-level page,
  not a circuit" while carrying a `circuit.yaml` two circuits depend on, and
  restates both figures it claims to cite.
- **Nothing checks rule 1.** The checker only searches *already-known-old*
  values; restating a figure's **current** value elsewhere is undetectable,
  and that is the state every future staleness defect grows from.
  `sensor-full-scale` — the figure `CLAUDE.md` names as the worst recorded
  case — is restated six times. This is the cheapest missing check in the
  repository.
- **The ADC-reference duplication is tracked but not deduplicated.**
- **`verify-datasheets.py` is wired to nothing**, so `CLAUDE.md`'s "must pass
  before committing" is a human rule with no mechanism.

### Still to build



- **Consolidate the three board-crossing blocks** — breath, SPI, key-chain.
  Each is currently split across a board page and a module page by necessity,
  and `breath-receive-stage`'s agent supplied the best argument for doing it:
  six of that page's numbers are derived from parts on the carrier, including
  a figure it owns.
- **BOM fragments and the generator**, with the 53 orphan rows to
  `hardware/unplaced.csv`. Held back from the agents deliberately: ownership
  across 138 rows and 22 circuits is a global decision, and parallel agents
  would have produced double-owned rows.
- **`circuit.yaml` and the dependency layer** (`D3`).
- **`datasheets/` re-filed by function** via `.moves.csv`.
- **Cold review**, including one agent whose only job is content conservation.

## A stale section that sat here, and what it cost to leave it

*This file carried a "Phase B: not started" section saying "the corpus is
moved but **not yet split**. Every page is still whole" — for one commit
after all seven splits had landed. I updated the part I was editing and left
the part a reader reaches next.*

*That is this project's named failure mode, in the file whose whole job is to
record what actually landed, committed by the person who had just written
three separate checks against it. `CLAUDE.md` says it plainly: "Fixes land
where the editing is happening; they do not land where the reader looks."
Recorded rather than quietly deleted, because it is the cheapest possible
demonstration that the mechanical rules are not optional for anyone.*

## Debt carried openly, not hidden

Listed in `PROPOSAL.md` §8 and repeated here because it is the part most
likely to be forgotten: the ASCII drawing at `carrier.md:164-211` spans three
circuit blocks and cannot be split by moving lines; `pcb-pipeline.md` says
"`module.py` importing the six" and Phase B makes that wrong with no check
able to see it; four more line ranges `D1` declined to assign rather than
guess at.
