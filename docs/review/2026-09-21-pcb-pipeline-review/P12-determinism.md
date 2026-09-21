# P12 — Failure modes, determinism, and whether "re-runnable" is true

**Slice:** the central promise of `docs/reference/pcb-pipeline.md` — that the
whole chain is re-runnable end to end, every script in the repo, "re-runnable
forever". The brief was to attack that promise. I did.

**Cold:** I did not read `docs/review/**` or any other agent's output. Sources
are KiCad's own source tree at `gitlab.com/kicad/code/kicad` (branches `7.0`,
`8.0`, `9.0`, `master`), the Freerouting source tree, the SKiDL source tree,
`gitlab.com/kicad/libraries/kicad-footprints`, and the subject document.

**What I could not do:** KiCad is not installed in this sandbox
(`which kicad-cli` empty, `import pcbnew` fails, `import skidl` fails), and no
Freerouting jar is built. **I ran no pipeline and produced no gerber.** Every
determinism verdict below is read off source, not measured. Where that matters
I say so, and §7 lists exactly what a first run must measure.

**Provenance:** `[source]` = read in the named file at the named line;
`[calc]` = arithmetic shown; `[from memory]` = not verified here.

---

## 0. The short version

The plan promises three things that cannot all be true at once:

1. the board is **generated** by `build_board.py` (stage 2),
2. the critical nets are **hand-routed** into that board (stage 3),
3. the pipeline is **re-runnable** (everywhere).

Re-running stage 2 destroys the product of stage 3. There is no script in the
plan that can recreate a hand-routed `AGND` star, and the plan does not say
where that geometry lives. **This is the biggest hole, and it is not a
determinism problem — it is a "the plan has no source of truth for layout"
problem.** §5 resolves it.

Separately, and independently: **two identical runs from a clean checkout will
not produce byte-identical gerbers, and cannot be made to without
post-processing.** Wall-clock timestamps are written unconditionally into every
gerber, every drill file, the job file and the DRC report. Three further layers
(random UUIDs, an absolute source path in the netlist, wall-clock cut-offs
inside the autorouter's inner loop) each break it again for different reasons.

The honest version of the promise is:

> **The board is the artifact of record and is committed. The scripts
> regenerate the *fab outputs* from that board, deterministically enough that a
> re-export is trustworthy. The scripts do not regenerate the board.**

---

## 1. Determinism verdict, stage by stage

| Stage | Second run byte-identical? | Root cause |
|---|---|---|
| 1. SKiDL netlist | **No** | wall-clock date, SKiDL version, **absolute path of the source script** written into the file (P12-04) |
| 2. `build_board.py` | **No** | every board object gets a fresh random UUID (P12-03) |
| 3. Hand-route | **N/A** | not a script at all (P12-11) |
| 4. Freerouting | **No** | wall-clock time limits inside the routing inner loop (P12-06). The RNG is *not* the problem |
| 5. Pour | Probably yes, **unverified** | parallel but per-zone independent (P12-13) |
| 6. `kicad-cli pcb drc` | Verdict stable; **report not** | report embeds date + KiCad version (P12-02) |
| 7. Gerbers / drill / job | **No** | date + full build-version string in every header (P12-01) |

Note the shape of this. Stages 1, 6 and 7 are non-deterministic only in
*metadata* — the payload is a pure function of the input. Stages 2 and 4 are
non-deterministic in *content*. That distinction is the whole design of the fix
(§3).

---

## 2. Findings

### P12-01 — Every gerber carries the wall clock and the exact build string, and `--no-x2` does not remove it

`common/plotters/GERBER_plotter.cpp` @ 9.0, in `StartPlot()`, unconditionally:

```c
wxDateTime date = wxDateTime::Now();
fprintf( m_outputFile, "G04 Created by KiCad (%s) date %s*\n",
         TO_UTF8( Title ), TO_UTF8( date.FormatISOCombined( ' ') ) );
```

where `Title = m_creator + " " + GetBuildVersion()`. `[source]` (identical on
`master`, lines 287–289 on `9.0`.)

This is outside the X2 block. `--no-x2` (`kicad/cli/command_pcb_export_gerber.cpp:70`,
`ARG_NO_X2`) `[source]` suppresses the `%TF…%` extended attributes — including
the X2 `CreationDate` produced by `GbrMakeCreationDateAttributeString()`
(`common/gbr_metadata.cpp:33-58`, `wxDateTime::GetTimeNow()`) `[source]` — but
the `G04 Created by KiCad … date …` comment is emitted regardless.

**Consequence:** two runs a second apart differ. Two runs on KiCad 9.0.1 and
9.0.5 differ *even with identical geometry*, because `GetBuildVersion()` is in
the string.

### P12-02 — Drill file, job file and DRC report do the same

- `pcbnew/exporters/gendrill_excellon_writer.cpp:565-568`:
  `"; DRILL file KiCad <GetBuildVersion()> date <GetISO8601CurrentDateTime()>"`,
  plus `GbrMakeCreationDateAttributeString(GBR_NC_STRING_FORMAT_NCDRILL)` at
  :604 and `GetBuildVersion()` again at :609. `[source]`
- `pcbnew/exporters/gerber_jobfile_writer.cpp:152,158`: `"Version": GetBuildVersion()`
  and `"CreationDate"`. `[source]`
- `pcbnew/drc/drc_report.cpp:68,134-135`: `"** Created on %s **"`,
  `reportHead.date = GetISO8601CurrentDateTime()`,
  `reportHead.kicad_version = GetMajorMinorPatchVersion()`. `[source]`

So the *verify* artifact is not byte-stable either. You cannot diff last run's
DRC json against this run's to prove nothing changed — you must parse it.

### P12-03 — Every object `build_board.py` creates gets a random UUID

`common/kiid.cpp` `[source]`:

```
static thread_local boost::mt19937                                       rng;
static thread_local boost::uuids::basic_random_generator<boost::mt19937> randomGenerator;
...
// We rely on the default non-arg constructor of basic_random_generator to provide a random seed.
KIID::KIID() { ... m_uuid = randomGenerator(); }
```

There *is* `KIID::SeedGenerator( unsigned int aSeed )` at :361 — but the comment
says it exists "for unit tests and other special cases", and I found no CLI
flag or environment variable that reaches it. `[source]` I did not find it
exposed in the SWIG surface either, though I could not enumerate the bindings
(the swig tree path I tried 404'd) — treat "not reachable from `pcbnew` Python"
as **unverified**. `[source]`/partial

**Consequence:** run `build_board.py` twice and you get two boards that are
geometrically identical and textually different on every single item. That
alone makes "diff the board to see what changed" useless if the board is
regenerated.

### P12-04 — The SKiDL netlist embeds the checkout's absolute path

`src/skidl/tools/kicad9/gen_netlist.py:307-317` `[source]`:

```python
scr_dict = scriptinfo()
src_file = os.path.join(scr_dict["dir"], scr_dict["source"])
if kwargs.get("track_abs_path", True):
    src_file = os.path.abspath(src_file)
...
date = time.strftime("%m/%d/%Y %I:%M %p")
tool = f"SKiDL ({__version__})"
```

Three defects in one function: the wall clock, the SKiDL version string, and —
the nasty one — **the absolute path of the generating script, on by default**.
Two clones of this repo at different paths produce different netlists from
identical source. CI and a laptop will never agree.

There is a documented fix: pass `track_abs_path=False` and the path is written
relative to the script. **The pipeline must pass it.**

Credit where due: SKiDL's *part* identifiers are already deterministic —
`gen_part_tstamp()` uses `uuid.uuid5(namespace_uuid, part.hiername)`, a hash,
not a random UUID (`gen_netlist.py:19-20,44-62`). `[source]` That is the one
piece of this chain that is stable by construction, and it is worth leaning on
(§3).

### P12-05 — SKiDL auto-assigned refdes are positional, and this repo's BOM is refdes-keyed

`src/skidl/utilities.py:444-505`, `get_unique_name()`: an unnamed part takes
`prefix + str(prefix_counts[…] + 1)` — the next free number in *instantiation
order*. `[source]`

`hardware/bom.csv` is keyed on `ref` (133 rows) `[source: repo]`, and the plan's
own `tools/check-bom-parity.py` diffs design BOM against generated BOM **by
refdes**. Insert one resistor in the middle of `pitch.py` and every auto-named
part after it in that module shifts by one. The parity check then reports a
hundred spurious mismatches, the placement script's coordinate table (if it is
keyed by refdes — it must be) points at the wrong parts, and the silkscreen no
longer matches the assembly notes.

**Fix, cheap and mandatory: every part in every SKiDL module gets an explicit
`ref=` matching `hardware/bom.csv`.** Never let SKiDL auto-number. Then add an
assertion to `verify.py`: the set of refdes in the netlist equals the set in
`hardware/bom.csv`, and no refdes was auto-generated.

### P12-06 — Freerouting: the RNG is seeded. The **wall clock** is the determinism killer

The obvious suspicion — an unseeded `new Random()` — is **wrong**, and I want
that on the record because it is the thing a reviewer would assert from memory.
`autoroute/maze/MazeSearchEngine.java:63,79-80` `[source]`:

```java
final Random randomGenerator = new Random();
...
randomGenerator.setSeed(ctrl.ripupCosts); // Keep v1.9 deterministic randomization across passes.
```

Seeded from a setting, not from entropy. The 2.x tree has clearly been worked
on for determinism: `ShapeSearchTree.java:708,728` sorts obstacles "to ensure
deterministic room partitioning"; `SortedRoomNeighbours`, `Sorted45Degree…`,
`SortedOrthogonal…` all sort "deterministically to ensure parity with v1.9";
`ExpandableObject`, `Point` and `TileShape` carry unique ids purely for
"deterministic tie-breaking". `PolygonShape` and `PlanarDelaunayTriangulation`
use a fixed seed of 99. `[source]`

**But the router cuts itself off on wall-clock time, inside the inner loop.**
`datastructures/TimeLimit.java` `[source]`:

```java
public TimeLimit(int milliSeconds) { this.timeLimit = milliSeconds;
                                     this.timeStamp = new Date().getTime(); }
public boolean limitExceeded() { return new Date().getTime() - this.timeStamp > this.timeLimit; }
```

and it is on the hot path, not some GUI convenience:

- `autoroute/pipeline/AutorouteConnectionRouter.java:22` —
  `TIME_LIMIT_TO_PREVENT_ENDLESS_LOOP = 1000`, passed as the pull-tight budget to
  `board.optChangedArea(…)` at :113 **after every routed connection**, and again
  at :235 on the neck-down retry. `[source]`
- Same constant and same use in `BatchAutorouter.java:43,536` and
  `BatchAutorouterThread.java:38,535,571`. `[source]`
- `autoroute/maze/AutorouteEngine.java:295-296` — `isStopRequested()` returns
  true when `timeLimit.limitExceeded()`, i.e. **the maze search abandons a
  connection because the clock ran out**. `[source]`
- `board/optimize/TraceTightener.java:73-77` — optimisation stops after
  `timeLimit` ms. `[source]`

A 1000 ms pull-tight budget means the geometry of every trace is a function of
how much pull-tight work the machine got through in one second. A faster CPU, a
noisier CI box, another agent's build hogging cores — **different copper**. This
is not a tie-break; it is a different board.

### P12-07 — Freerouting also stops the whole job on a wall-clock deadline

`autoroute/pipeline/BatchOptimizer.java:55,352,391,712,937,1044` —
`deadlineMs = sessionStartMs + timeoutSeconds * 1000`, checked in the optimizer
loops. `[source]` `BatchFanout.java:112,416` the same. `[source]`

The plan's own `timeout 1800` shell wrapper is a *second* wall-clock cut-off on
top of this. A board that routes in 25 minutes on one machine and 31 on another
does not merely take longer — it yields a **truncated, different** result, and
the shell timeout yields *no* result while leaving a partial `.ses`.

### P12-08 — Freerouting's own determinism test is much narrower than it sounds

`src/test/java/app/freerouting/fixtures/BatchOptimizerDeterminismTest.java`
`[source]`: `crossThreadOptimizationProducesIdenticalResults` sets
`maxPasses = 1`, `maxItems = 6`, `jobTimeout = "00:01:00"`, and compares a
1-thread against a 4-thread optimizer run **on the same pre-optimised board
clone**.

It proves: the optimizer's thread pool does not reorder results, on six items,
in one pass. It does **not** prove that two full `-mp 100` runs of the
autorouter agree, and given P12-06 it cannot. `Issue420ContributionBoardRoutingTest`
is explicit about why it caps things: "capped at 1 pass with a single thread to
keep the test deterministic". `[source]`

Take this as the upstream project telling you, in its own test names, what it
is and is not willing to guarantee.

### P12-09 — The DSN round trip quantises everything to 0.1 µm

`pcbnew/specctra_import_export/specctra_export.cpp:1254-1261` `[source]`:

```c
// Tell freerouter to use "tenths of micrometers", which is 100 nm resolution.
m_pcb->m_resolution->units = T_um;
m_pcb->m_resolution->value = 10;       // tenths of a um
```

KiCad's internal unit is 1 nm `[from memory]`. So placement handed to the router
is rounded to 100 nm, and routed geometry comes back on that grid
(`specctra_import.cpp`, `mapPt`/`scale`). `[source]` This is *deterministic*
rounding, so it is not a re-run hazard — but it does mean the board you verify
is not the board you placed, to 100 nm, and anything the plan does with
sub-100 nm precision is fiction.

### P12-10 — Good news: the locked-track round trip works, and the smoke test for it can be replaced by reading three files

The plan (line 107) says "One thing to prove specifically: that locked tracks
survive the round trip." It does survive, in every version I checked, and here
is the mechanism, end to end:

1. **KiCad exports a locked track as `fix`, not `protect`.**
   `specctra_export.cpp` @ 9.0:1585-1588 `[source]`:
   ```c
   if( track->IsLocked() )
       wire->m_wire_type = T_fix;    // tracks with fix property are not returned in .ses files
   else
       wire->m_wire_type = T_route;  // could be T_protect
   ```
   Identical on `7.0`:1645, `8.0`:1626; `master`:1679 changed the *else* branch
   to `T_protect` but kept `T_fix` for locked. Vias likewise
   (`master`:1729-1733). `[source]`
2. **Freerouting maps `fix` to `SYSTEM_FIXED`.**
   `io/specctra/parser/Wiring.java:257-267`, `calcFixed()` `[source]`:
   `shove_fixed`→`SHOVE_FIXED`, `fix`→`SYSTEM_FIXED`, anything else that is not
   `normal`→`USER_FIXED`. Identical in the bundled 1.9 tree
   (`src_v19/.../specctra/Wiring.java:257-267`). `[source]`
3. **Freerouting omits `SYSTEM_FIXED` items from the session file.**
   `io/specctra/SesWriter.java:339-340` `[source]`:
   ```java
   if (currentItem.getFixedState() == FixedState.SYSTEM_FIXED) { continue; }
   ```
4. **KiCad keeps its locked tracks on import.**
   `specctra_import.cpp` @ `master`:353-358 `[source]`:
   ```c
   // Remove unlocked tracks/vias (locked ones stay; they are exported as fixed and omitted
   if( !track->IsLocked() ) aCommit.Remove( track );
   ```
   @ `9.0`:381-390 the same partition into `locked` / not. `[source]`

So the strategy is sound **and the hand-routed copper is never re-quantised**,
because it never leaves KiCad. Keep the smoke board for the *other* nineteen
reasons the plan gives — but this particular question is answered, and the
answer should go in the document so nobody spends an afternoon on it.

Two cautions. (a) It is a **four-link chain across two projects**, and link 1
already drifted between 9.0 and master. Pin both tools (§4) and assert the
invariant in `verify.py` rather than trusting it. (b) A side effect nobody
plans for: an *unlocked* pre-existing track exports as `T_route`, which
`calcFixed` maps to `USER_FIXED` (it is not `normal`), and
`Item.java:862` `isUserFixed()` is true for it — so **Freerouting will not rip
up any track that was already on the board**, locked or not. If you ever
re-route an already-routed board expecting the router to improve it, it will
instead route around everything. `[source]`

### P12-11 — `build_board.py` and "hand-route" cannot both be in the same pipeline

Stage 2 *builds* the board: "Outline onto `Edge.Cuts` first… Load footprints,
assign every pad to its net, place." Stage 3 *hand-routes* five critical nets
into that board, in a GUI, by judgement the plan itself calls "a layout
judgement" (pitch feedback loop area). Then the plan says the whole thing is
re-runnable.

Run stage 2 again and the hand-routing is gone. Not corrupted — **gone**, along
with the placement, because a fresh `BOARD` has no tracks and fresh random
UUIDs (P12-03). The plan has no script that can put it back and no file where
it is stored. `pcb/<board>/*.kicad_pcb` is listed under the generated tree, and
the section heading above it is "Nothing generated under `hardware/`" — the
document is treating the board as an output, while stage 3 treats it as an
input that a human edits.

This is, structurally, the exact failure this repo is organised against: **two
places that must agree, and no mechanism that makes them.** Except here it is
worse than a stale number, because one of the two places does not exist.

### P12-12 — Placement is not captured by anything

Stage 2 says "place" in one word. Placement of a 10HP analog module is the
decision that determines whether the breath channel works: decoupling within
~2 mm of its pin (the plan's own verify assertion), the in-amp near the
connector, the load switch's thermal pad, panel components on their panel
positions. None of that is derivable from the netlist.

Either placement coordinates live in a file (`placement.csv`, refdes → x, y,
rotation, side, locked) that `build_board.py` reads, or placement lives in the
`.kicad_pcb` and `build_board.py` must never run again. The plan picks neither.

`placement.csv` is genuinely attractive for the panel-constrained parts — jacks
and pots have positions dictated by the panel DXF, and those belong in a file
next to the panel, not buried in a board. But it cannot capture the rest, and
it definitely cannot capture routing. See §5.

### P12-13 — The zone fill lives inside the `.kicad_pcb`, and it is most of the diff

`pcb_io/kicad_sexpr/pcb_io_kicad_sexpr.cpp:2647` writes `(filled_polygon …)`
into the board file. `[source]` Every refill rewrites every coordinate of both
ground pours. On a 10HP board with two zones that is easily the majority of the
file, and it changes on *any* edit that touches copper, because the plan
correctly says "re-fill after *any* later change".

For scale, a 2017-era 5.0 board in a real Eurorack repo is 22,785 lines with
447 `tstamp` lines `[source: scratch clone of performer-hardware,
sequencer.kicad_pcb]`; a 9.0 board carries a `uuid` on essentially every object
rather than 447 of them `[from memory]`.

So: the board file in git is a large binary-ish blob whose diffs are not
reviewable. That is not an argument against committing it (§3 argues for it) —
it is an argument for **committing it and reviewing something else**, and for
`.gitattributes` marking it so nobody wastes time on `git diff`.

### P12-14 — Board format version: one-way, and the numbers are concrete

Active `SEXPR_BOARD_FILE_VERSION` in `pcbnew/pcb_io/kicad_sexpr/pcb_io_kicad_sexpr.h`
`[source]`:

| Branch | Version |
|---|---|
| 8.0 | `20240108` |
| 9.0 | `20241229` |
| master (10.x dev) | `20260901` |

Two useful facts fall out.

**Good:** the constant is per stable series. 9.0.1 and 9.0.5 write the *same*
board format. Point-release drift will not churn the board file. (It will still
churn the gerber headers — P12-01.)

**Bad:** open a 9.0 board once in KiCad 10 and it is silently rewritten at
`20260901` and cannot go back. The 9.0 series alone accumulated eleven format
bumps between `20240703` and `20241229` — user layer types, embedded files,
component classes, complex padstacks, via stacks, teardrop representation
`[source]` — so the 9→10 delta is not cosmetic.

**Therefore:** the repo must state the KiCad major series the board belongs to,
and `verify.py` must assert the board's `(version …)` token equals the expected
value and fail loudly otherwise. That is a one-line check that catches the most
expensive accident available here.

### P12-15 — Footprint libraries change dimensions, and this is not hypothetical

`gitlab.com/kicad/libraries/kicad-footprints` is versioned separately and
tagged in step with KiCad (`9.0.9`, `10.0.1` … `10.0.6`). `[source]` Recent
commit titles from its log `[source]`:

- `a82aa581` 2026-01-24 — "Decrease pad size for SC-70 variants via IPC-sensity"
- `4764aff4` 2026-01-27 — "Fix Texas_RVC0020A to follow Texas recommended sizes"
- `db6eab55` 2026-06-11 — "Fix Texas PWP0028M / TSSOP-28"
- `82ab8dd8` 2026-09-13 — "Fix PCB Edge of DX07S016JA1R1500"
- `7bba3cb9`, `87dc08fc`, `b1c36ab9` — pads changed to roundrect on USB / SATA / DSUB

Pad size, pad shape and board-edge geometry all change under a stable footprint
*name*. `build_board.py` resolves footprints by name through
`fp-lib-table` — which the plan already notes must be hand-copied from
`/usr/share/kicad/template/` because no GUI has run. Whatever that table points
at on the day is what you get.

The plan's precursor list says "Every BOM row `selected`, with a real package
and a footprint. A placement built around a wrong footprint is the one
expensive thing to redo here." Correct — and then nothing pins the footprints.

This interacts with the repo's existing datasheet discipline in a way worth
naming: `datasheets/MANIFEST.csv` already records which footprints are
vendor-issued and which are community-authored, with SHA-256. **Extend exactly
that mechanism to the KiCad-library footprints actually used.** A footprint is
a document; bank it like one.

### P12-16 — Partial failure: the pipeline is not idempotent, and stages 3 and 4 must not be re-run

Walking the stages as written:

| Stage | Safe to re-run? | State left behind on failure |
|---|---|---|
| 1 netlist | Yes | `module.net` possibly truncated; regenerated wholesale |
| 2 build_board | **Destructive** | overwrites the board — see P12-11 |
| 3 hand-route | Not a script | — |
| 4 route | **No** | KiCad's SES import already removed unlocked tracks before it can fail; a truncated `.ses` from the `timeout` wrapper imports *partially* |
| 5 pour | Yes | zone fills are recomputed from scratch |
| 6 verify | Yes (read-only) | DRC markers; `DeleteMARKERs()` on SES import clears them |
| 7 export | Yes | stale files in `fab/` if the layer list changed — must clear the directory first |

Stage 4 is the dangerous one. `specctra_import.cpp` removes unlocked tracks and
*then* adds what the session contains. `[source]` If Freerouting was killed by
the shell `timeout` mid-write, the `.ses` is truncated, the import either throws
part-way or succeeds with a subset, and the board is now in a state that is
neither the pre-route board nor a routed board. The plan has no rollback.

**Minimum fix, and it is cheap:** every stage that mutates the board writes to a
new file and renames on success; the board is copied to `board.pre-route.kicad_pcb`
before import; Freerouting's exit status is checked *and* the `.ses` is validated
as complete (balanced parens, expected net count) before `ImportSpecctraSES` is
allowed to run. `[from memory]` for the paren-balance heuristic being sufficient —
a net-count assertion is the real check.

### P12-17 — The 5-iteration cap: the number is not the problem, the loop is

> "Five full iterations, then stop and report rather than thrashing placement."

The cap is the right instinct pointed at the wrong thing. It bounds the runtime
of a loop that should not exist.

An automated place → route → DRC → **adjust placement** → repeat loop optimises
for "DRC returns zero", and DRC is exactly the thing the plan already says is
"necessary, not sufficient". Every constraint that actually matters on this
board is invisible to DRC: whether `AGND` is still a sense-only star, whether
the `BREATH`/`AGND` pair is still matched and parallel, whether the pitch
feedback loop area grew, whether the two ground zones still meet at one tie.
A loop that moves parts until DRC is quiet will happily satisfy DRC by
destroying all four, and it will do so **five different ways on five different
machines** because of P12-06.

And the output is a board nobody has looked at, whose placement nobody chose,
which then goes to a fab. The plan's own framing — "an artifact nobody can
review" — was the reason it rejected parsing the ASCII schematics. The same
objection applies here with more force, because this artifact gets etched.

**A DRC failure is information for a human, not an input to a search.** See §6.

### P12-18 — Nothing in the stack is pinned, and one of the five things is `apt`

The tool table names KiCad 9, SKiDL 2.3.0, kiutils 1.4.8, Freerouting 2.x,
xvfb. Only two of those are versions. "KiCad 9" via apt/PPA is whatever the PPA
holds that week; "Freerouting 2.x" is a moving GitHub release. Blast radius,
worst first:

1. **KiCad major** — board format upgrade, one-way (P12-14).
2. **Footprint library** — silently different copper and drill (P12-15).
3. **Freerouting** — different routing; and the `fix`/`protect` mapping the
   locked-net strategy depends on lives here (P12-10).
4. **KiCad point release** — gerber header bytes only, *if* the format version
   is unchanged (P12-14).
5. **SKiDL / kiutils** — netlist formatting; caught by the netlist-equality
   assertion in `verify.py` if that assertion is written to compare structure
   rather than text.

§4 says what to do about each.

### P12-19 — The smoke board is the best idea in the plan, and it cannot prove determinism

`pcb/smoke/` is right and should be kept: it proves installs, API signatures and
export flags cheaply, on a board where the answer is obvious. But note what it
cannot do. A two-resistor board routes in milliseconds, so it never hits the
1000 ms pull-tight budget and never hits the job deadline. **It will look
perfectly deterministic and tell you nothing about the real board.** Do not let
a green smoke run be read as evidence for re-runnability.

If you want evidence, the test is in §7.

---

## 3. What the artifact of record should be

**The `.kicad_pcb` is the artifact of record. It is committed. It is not
generated.**

Everything else in the pipeline sorts itself once that is settled:

| Thing | Status | Lives |
|---|---|---|
| Schematic prose | source of truth, reviewed | `hardware/module/*.md` |
| SKiDL modules | source of truth, executable | `pcb/src/<board>/*.py` |
| `module.net` | **generated**, every run | `pcb/<board>/` — gitignored |
| **`<board>.kicad_pcb`** | **artifact of record, committed** | `pcb/<board>/` |
| `<board>.kicad_dru`, design settings | source of truth, committed | `pcb/<board>/` |
| `.dsn` / `.ses` | **intermediates**, committed only as evidence | `pcb/<board>/route/` |
| Gerbers, drill, step, svg | **generated**; committed once, at order time, under a tag | `fab/<board>/` |
| `order.csv` | source of truth (pack sizes, spares) | `fab/<board>/` |

Is putting a `.kicad_pcb` in git "right"? It is what every real hardware repo I
could look at does — six KiCad projects in my scratch survey, every one commits
the board, and most commit gerbers or a zip alongside it as a release drop
`[source: local clones of performer-hardware, es-hardware,
eurorack-modules-vk2gpu, sourcebox_74hc165-breakout, atopile_packages,
vpatkov_breath-controller]`. The diffs are unreadable (P12-13). That is
accepted, because the alternative — a board nobody can reproduce because the
only copy was on someone's laptop — is worse.

It is right *here* for a sharper reason. This project's stated failure mode is
two artifacts that must agree and no mechanism that makes them. Committing the
board gives you **one** artifact for layout, with the mechanism (`verify.py`)
checking it against the netlist rather than against another copy of itself.

**So: "re-runnable" honestly means "the fab outputs are a pure function of a
committed board".** Stages 5–7 re-run freely. Stages 1 and 6 re-run freely and
are read-only against the board. Stage 2 runs **once per board**, and stages
3–4 are how the board got made, recorded but not replayed.

Rename the stages to say so. `build_board.py` should be `bring_up_board.py`,
with a guard at the top: if the board file exists, refuse to run without
`--force-recreate`, and print what will be lost.

---

## 4. What must be pinned or vendored

In descending order of blast radius.

1. **KiCad major series → pin, and assert.** Record the exact version in
   `pcb/TOOLCHAIN` (e.g. `kicad 9.0.5`). `verify.py` asserts the board's
   `(version …)` token is `20241229` `[source: 9.0 header]` and fails on
   anything else — that catches "someone opened it in KiCad 10" before it
   reaches a fab. Do not pin the point release; do record it, because gerbers
   differ across it.
2. **Footprint libraries → vendor.** Copy the `.kicad_mod` files actually used
   into `pcb/footprints/<board>.pretty/`, point `fp-lib-table` there, and add a
   row per footprint to `datasheets/MANIFEST.csv` with its SHA-256 and whether
   it is vendor-issued or community-authored. This is the existing datasheet
   rule applied to a document type the plan forgot. It also removes the
   "library tables do not exist until a GUI has run" gotcha for the real board,
   since the table you copy in is yours.
3. **Freerouting → vendor the jar.** Commit the exact `freerouting-<ver>.jar`
   (or its SHA-256 plus the release URL if size is a concern) to
   `pcb/vendor/`. Its behaviour is the least stable thing in the chain and the
   `fix`/`protect` contract of P12-10 lives inside it.
4. **Python → a lockfile.** `pcb/requirements.txt` with `==` pins and hashes
   for SKiDL, kiutils and their transitive deps. Plus `PYTHONHASHSEED=0` and
   `SOURCE_DATE_EPOCH` exported in `setup.sh` — cheap, and rules out a class of
   ordering surprises I did not chase to ground.
5. **`track_abs_path=False`** in the SKiDL netlist call (P12-04). Not a pin, but
   it belongs in this list because without it the netlist depends on the
   checkout path.
6. **A post-export canonicalisation step.** `export.py` strips or normalises the
   `G04 Created by KiCad … date …` line, the X2 `TF.CreationDate`, the drill
   header date and the job-file `CreationDate`, writing a `fab/<board>/.sha256`
   over the canonicalised set. Now "did the fab output change?" is one `sha256sum -c`
   instead of a judgement call. **This is the only way to get a byte-comparable
   fab output, and it is ten lines of `sed`.** Keep the unmodified files as what
   you send; keep the canonical hashes as what you compare.

---

## 5. The hand-route vs re-run contradiction, resolved

**They are incompatible as written. Resolve it by deleting the re-run of
stage 2, not by trying to script the hand-routing.**

Concretely:

**Bring-up runs once, per board.** `bring_up_board.py` creates the board from
the netlist: outline, footprints, nets, net classes, design rules, and an
initial placement read from `placement.csv` for everything the panel fixes
(jacks, pots, the etherCON, LEDs). It writes `<board>.kicad_pcb`. **This file is
then committed and becomes the artifact of record.** The script never runs
against an existing board again.

**Placement and hand-routing happen in the board, in a GUI, by a human, and are
committed as board edits.** Critical nets are routed and **locked**. Locked is
not decoration — it is the load-bearing token (P12-10): it is what makes the
copper survive the autoroute, and it is the flag `verify.py` checks.

**Netlist changes are applied as updates, not rebuilds.** When a SKiDL module
changes, re-run stage 1, then apply the new netlist to the *existing* board with
pcbnew's netlist-update path, which matches existing footprints and preserves
placement, tracks and zones. This is exactly what the GUI's "Update PCB from
Schematic" does, and it is why SKiDL's stable uuid5 part identifiers (P12-04)
matter: they give the update a reliable key. `[from memory]` that `pcbnew`
exposes this headlessly in 9.0 — **verify before relying on it** (§7). If it
does not, the fallback is `kiutils` merging the netlist into the board's
`(net …)` and per-pad net assignments, which is more work but is the same
operation.

**Re-routing is a deliberate, logged act, not a pipeline stage.** `route.py`
takes a flag, copies the board aside first, and refuses to run if any net in
the critical list has unlocked copper on it.

**The `.ses` is committed as evidence, not as the source.** It records what the
router produced on a given day with a given jar; it is never the thing that is
re-imported to rebuild the board, because the board already has the result.
Given P12-06 you could not re-derive it anyway.

**"Re-run the pipeline" then means, precisely:** stage 1 (netlist, for the
parity and equality assertions), stage 5 (refill zones), stage 6 (verify), stage
7 (export fab). Four stages, all either read-only or idempotent, all fast, all
safe to run in CI on every commit. That is a real and useful promise. It is just
a smaller one than the document makes.

One thing this buys that the plan loses: **the board becomes reviewable by this
project's own method.** A cold reviewer can be handed `fab/<board>/*.svg` plus
`verify.py`'s assertions and asked whether the star ground survived — node-
indexed, against `AGND` and `PWR_GND`, not against a file and line.

---

## 6. What should happen on a DRC failure

Not an adjust loop. Concretely, `verify.py` exits non-zero and emits a report
that names, per violation: the DRC rule, the **net and refdes** involved (not a
file and line), and whether the violation touches any net on the critical list.
Then it stops. A human looks at it.

The distinction worth encoding, because it is where the automation *does* earn
its keep:

- **Violations on non-critical nets, from autorouting** — re-route with adjusted
  router costs or an added keepout. That is a legitimate retry, it is bounded by
  one human decision each time, and nothing silently moves.
- **Violations on critical nets** — never automatic. These are the hand-routed
  ones; if DRC is unhappy there, the hand-routing was wrong and the human who
  did it needs to know.
- **Violations that imply the placement is wrong** — the board is not routable
  as placed. Stop. Report which nets could not be completed and which pads are
  crowded. Moving parts is a design decision, and on this board it is the
  decision that determines whether the analog channel works.

And the assertions the plan lists beyond DRC (netlist equality, grounds
distinct, `AGND` tied exactly once, locked nets unchanged, decoupling within
~2 mm, zero unrouted, no copper under the bore) are the valuable half of
`verify.py`. Add three more that fall out of this review:

- the board's `(version …)` token equals the expected format version (P12-14)
- every refdes in the netlist is explicit, and the set matches `hardware/bom.csv`
  (P12-05)
- every net on the critical list is fully routed **and every segment on it is
  locked** (P12-10) — this is the assertion that makes the artifact-of-record
  model self-enforcing, because an unlocked critical net is exactly the state
  that would be silently destroyed by a re-route

Replace "five full iterations, then stop" with: **zero iterations. Report.**

---

## 7. What I could not verify, and the test that would settle it

No KiCad, no built Freerouting jar, no run. Everything above is source-reading.
The first real run should measure these, in this order, because each one is
cheap and each one invalidates something above if it comes out the other way:

1. **Two full Freerouting runs on the real board, same machine, byte-compare the
   `.ses`.** If they differ, P12-06 is confirmed and §5 is mandatory. If they
   match, run again under `nice -n 19` with a parallel `make -j8` running, and
   compare. My prediction is that the loaded run differs; the 1000 ms pull-tight
   budget makes that close to arithmetic.
2. **Two `build_board.py` runs, diff the `.kicad_pcb`.** Expect a difference on
   essentially every line (P12-03). Confirms the board cannot be regenerated and
   diffed.
3. **Export gerbers twice, one minute apart, diff.** Expect exactly the header
   lines to differ (P12-01/02). Confirms the canonicalisation step in §4.6 is
   both necessary and sufficient.
4. **Does `pcbnew` 9.0 expose a headless netlist-update against an existing
   board?** §5 depends on it. If not, the `kiutils` fallback needs designing
   before the first board, not after.
5. **Is `KIID::SeedGenerator` reachable from `pcbnew` Python?** If it is, a
   seeded bring-up would make even stage 2 reproducible, which is a nice-to-have
   rather than a need once §5 is adopted.
6. **Zone fill across thread counts.** `zone_filler.cpp:604-634` submits one
   lambda per zone to a thread pool and `:823` parallelises island removal
   `[source]`; each unit looks independent, so I expect determinism, but I did
   not trace the write-back ordering. Fill with `-j1` and `-j8`, diff the
   `(filled_polygon …)` blocks.

---

## 8. Summary of findings

| # | Finding | Severity |
|---|---|---|
| P12-11 | `build_board.py` regenerating the board destroys stage 3's hand-routing; no file holds it | **Blocking** |
| P12-12 | Placement is captured by nothing | **Blocking** |
| P12-06 | Freerouting cuts off pull-tight and maze search on wall-clock; output varies with machine speed and load | **Blocking** for "re-run and re-verify" |
| P12-15 | Footprint libraries change pad and edge dimensions under stable names; nothing pinned | **High** |
| P12-14 | Board format upgrades one-way across KiCad majors; nothing asserts the version | **High** |
| P12-05 | SKiDL auto-refdes are positional; this repo's BOM and parity check are refdes-keyed | **High** |
| P12-16 | Stage 4 has no rollback; a truncated `.ses` imports partially over a board whose tracks were already deleted | **High** |
| P12-17 | The automated DRC-adjust loop optimises for the one metric the plan says is insufficient | **High** |
| P12-04 | SKiDL netlist embeds the absolute checkout path, date and version | Medium (one kwarg) |
| P12-01/02 | Date and build version in every gerber, drill, job file and DRC report; `--no-x2` does not remove them | Medium (canonicalise) |
| P12-03 | Random UUIDs on every created board object | Medium (moot once the board is committed) |
| P12-18 | Nothing pinned or vendored | Medium |
| P12-13 | Zone fill inside the board file makes diffs unreviewable | Low (accept, mark in `.gitattributes`) |
| P12-09 | 0.1 µm DSN quantisation | Low (deterministic) |
| P12-10 | Locked-track round trip **works** — mechanism documented, smoke test for it unnecessary; four-link cross-project contract, already drifted once | Note |
| P12-08 | Freerouting's determinism test covers 1 pass / 6 items / cross-thread only | Note |
| P12-19 | The smoke board cannot exercise the time limits and will look falsely deterministic | Note |
