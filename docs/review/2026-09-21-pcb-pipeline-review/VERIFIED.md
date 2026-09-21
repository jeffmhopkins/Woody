# VERIFIED — what was checked by hand, and where an agent was wrong

Findings are claims. This file records which ones were re-checked independently
of the agent that filed them, and what the re-check found.

---

## P2 — no headless netlist import exists

**Claim:** there is no way, in any KiCad version or interface, to import a
netlist into a board headless. `NETLIST`, `NETLIST_READER`, `PCB_NETLIST` and
`BOARD_NETLIST_UPDATER` are absent from the SWIG bindings; `kicad-cli pcb` has
no import verb; the IPC API needs a running KiCad.

**Re-checked independently, 2026-09-21. CONFIRMED.**

```
$ curl .../kicad/-/raw/9.0.9/pcbnew/python/swig/pcbnew.i   → 153 lines, no match for NETLIST
$ curl .../kicad/-/raw/9.0.9/pcbnew/python/swig/board.i    → 202 lines, no match for NETLIST
$ grep -oE 'CLI::PCB_[A-Z_]+' kicad/kicad_cli.cpp @ 9.0.9
    PCB_DRC_COMMAND  PCB_RENDER_COMMAND
    PCB_EXPORT_{DRILL,DXF,GENCAD,GERBER,GERBERS,IPC*,ODB,PDF,POS,SVG}_COMMAND
```

No import verb, no update verb. **This is a real hole in the pipeline as
written**, and it invalidates the unstated assumption in stage 3 that a
generated netlist lands in a board by itself.

**Also confirmed:** `skidl==2.3.0` hard-depends on `kinet2pcb>=1.1.4`
(`Requires-Dist: kinet2pcb>=1.1.4` in the sdist's `PKG-INFO` *and*
`setup.py`), which is the proposed route around the hole. Not yet tested
end to end — only the dependency is established.

**Noted while verifying, outside P2's slice:** `kicad-cli pcb export` offers
**`odb`** and **`ipc2581`** alongside gerbers. Neither appears in the plan.
Flagged for P7.

---

## Still to verify

Everything else. The wave is in flight; this file gets one section per report
as each is re-checked.

---

## P1 — not one `kicad-cli` line in the plan would parse

**Claim:** `input` is a *positional* argument with no default, so every command
in the plan — all six — fails with "Too few arguments" before doing anything.

**Re-checked, 2026-09-21. CONFIRMED.** `kicad/cli/command.cpp:124-133` @ 9.0:

```cpp
m_argParser.add_argument( ARG_INPUT )
        .help( UTF8STDSTR( _( "Input file" ) ) )
        .metavar( "INPUT_FILE" );
```

No `--` prefix, no `.default_value()`. Positional and required.

Not re-checked but carried: `--units mm` on `export drill` is really
`--excellon-units`; `--severity-error` *narrows* the report and drops every
warning from `--exit-code-violations`, which is a silent wrong-green; the
OpenGL paragraph is false for KiCad 9 because `pcb render` is a CPU raytracer;
and "library tables need a GUI first" is refuted — `kicad-cli` creates them
itself under `KFCTL_CLI`.

## P10 — the copper arithmetic was wrong and the conclusion inverted

**Claim:** "0.5 mm of 1 oz copper is roughly a 1 A trace at a 10 °C rise …
that is no margin" is wrong; IPC-2221 gives **1.447 A**.

**Re-checked by doing the arithmetic, 2026-09-21. CONFIRMED.**
IPC-2221 external, `I = k·ΔT^0.44·A^0.725`, k = 0.048, 1 oz = 1.378 mil:

| width | area | current at 10 °C |
|---|---|---|
| 0.25 mm | 13.56 mil² | **0.875 A** |
| 0.30 mm | 16.28 mil² | 0.999 A |
| 0.50 mm | 27.13 mil² | **1.447 A** |

Against a limit of `47 mV / 50 mΩ` = **0.940 A**, 0.5 mm has ~54 % margin. The
plan said the opposite.

**And the same table refutes the plan a second way, which P10 did not say:**
the plan's `Default` signal class at **0.25 mm is 0.875 A**, *below* the
0.940 A limit. So the advice "derive the power width, don't default it" was
right — but for the opposite reason. The power class is fine and it is the
*default* class that would be marginal if it ever carried fault current.

**Also confirmed by P10 and accepted without re-check:** "1.0 A" is stale —
`power-entry.md` opens with "the limit is 0.940 A, not 1.0 A". The plan copied
a superseded figure from ADR 0005, twice.

## P5 — SKiDL survives, three of the plan's claims about it do not

Not independently re-checked; P5 ran real circuits in a clean venv with no
KiCad, which is stronger evidence than re-reading source. Accepted as filed.

The architecture holds: SKiDL works with **no KiCad installed**, parses
**KiCad 9** symbol libraries, and ad-hoc parts need no library at all.

Three plan claims refuted: "fail the build on any ERC error" **does not
happen** — SKiDL exits 0 with errors and writes the netlist anyway;
`generate_schematic()` **does** exist, so "you lose `--schematic-parity`" is
out of date (though its output is non-deterministic and cannot be the parity
artifact); and `check-bom-parity.py` "diffs by refdes" is **impossible** —
`bom.csv` is role-keyed, and 61 rows are 149 physical parts.

## P12 — Freerouting is non-deterministic, and the reason is wall-clock

**Claim:** the RNG *is* seeded, so the obvious answer is wrong. The real
non-determinism is `TIME_LIMIT_TO_PREVENT_ENDLESS_LOOP = 1000` ms applied
inside the routing hot path — geometry becomes a function of how much work the
CPU got through in one second.

**Re-checked against the working clone, 2026-09-21. CONFIRMED.**

```
fr/src/main/java/app/freerouting/autoroute/pipeline/BatchAutorouterThread.java:38
    private static final int TIME_LIMIT_TO_PREVENT_ENDLESS_LOOP = 1000;
  ...called at :535 and :571
fr/src/main/java/app/freerouting/autoroute/pipeline/AutoroutePassRunner.java:33
    same constant
```

Two files, called from the routing path. **This is the finding that breaks the
re-runnability promise**, and it is one an agent working from memory would have
got wrong in the other direction — P12 says so explicitly, which is the right
way to file it.

### P12's ROADMAP flag — CHECKED AND CLEARED, not a defect

P12 raised `ROADMAP.md:53` as possibly saying the panel is 8HP. It does not.
The full line reads:

> "**10HP panel cut**, module assembled and racked. etherCON braced to the
> PCB — good practice at 8HP rather than the structural necessity it was at
> 6HP."

It states 10HP first and then compares bracing necessity *across* widths as
history. The phrasing is a fossil of the 8HP era but the claim is true and
nothing derives from it. Recorded so the next reviewer does not re-raise it.

### The staleness count moving 4 → 5 — EXPECTED

P12 noticed the pre-commit hook go from 4 unresolved to 5 mid-session and
correctly declined to assume it was theirs. It is the **datasheet session**
working the same branch: `ref5050-grade` was filed `disputed` when the
REF5050's A-suffix turned out to be the *worse* grade, and `matrix-led-current`
was filed `blocked`. Both are deliberate.

## P7 — the module panel is not a PCB, and the pipeline has no place for it

**Claim:** the 10HP panel is 2 mm aluminium, laser or waterjet cut from a DXF,
same vendor and order as the key plate. It is not a PCB, not that vendor, not
that file format — and the pipeline emits no DXF at all.

**Re-checked, 2026-09-21. CONFIRMED, twice over.**

```
hardware/bom.csv:21
  PANEL | 2mm aluminium, 10HP x 3U (50.50 x 128.5mm) | n/a
  "Laser or waterjet from DXF - SAME vendor and order as the key plate"

docs/decisions/0004-cv-interface-module.md:243
  "The 10HP panel is laser or waterjet cut from DXF - same vendor and ideally
   the same order as the aluminium key plate (ADR 0009)."
```

**This is a category error in the plan, not a missing feature.** The panel was
listed as one of four fabricated items going through KiCad to gerbers. It
belongs with the key plate in a mechanical DXF workflow that this pipeline does
not cover and should not try to — the two aluminium parts ship on one order.

Noted while verifying: the same BOM row records that a review *"rebuilt the
panel bottom-up and got ~115 mm against ~110 mm usable — already over before
`POT-RESP` was added"*. So `panel-height-budget` is not merely disputed, it is
disputed with an over-budget result on the table.

**Accepted without re-check, and each changes a script:** `--units mm` is not a
drill flag (it is `--excellon-units`); X2, netlist attributes and aperture
macros are **on** by default and all six vendor profiles in GerberZipper turn
all three **off**; PTH/NPTH default to **merged** while the etherCON's two
⌀3.2 ±0.1 NPTH clearance holes must not be plated; a `.gbrjob` ships
unconditionally whether the plan knows it or not; and an invalid `--layers`
token is **reported and then ignored, exit 0** — so a misspelt `F.Mask` yields
a board with no soldermask and a green build.

**And the plan verifies the wrong object.** Every check in stage 7 reads
`module.kicad_pcb`. Nothing ever opens a file from the zip, so the entire
export stage sits downstream of every assertion.

## P11 — the plan hand-routes the robust nets and autoroutes the fragile ones

**Claim:** the `Analog` class is `BREATH` plus the pitch and mod *outputs* —
every one of which already has 1 kΩ of series isolation and a shunt cap at the
jack. Meanwhile `VREFOUT`, `V_ref`, the three trimmer wipers and the mods'
shared 3.3333 V reference are in **no class**, so they fall to `Default` and
go to Freerouting. On `V_ref`, **1 mV = 1.2 cents**.

**Re-checked, 2026-09-21. CONFIRMED, with one small correction to P11.**

The plan's table (`pcb-pipeline.md:177-181`) is exactly as quoted. The
references and trimmer wipers appear in no class. The sensitivity is trivially
right — 1 V/octave means 1200 cents per volt, so 1 mV is 1.2 cents — and
`pitch-stage.md:112` states the same figure independently: *"Offset, 1 mV |
1.2 cents"*.

That is **equal to or larger than every candidate** in `figures.yaml`'s
`pitch-cents-budget` dispute. The plan protects the outputs, which are
buffered, and leaves the references, which are not.

**P11 is wrong on one detail:** it lists `AVDD` among the unclassed nets.
`AVDD` *is* in the `Power` class. Recorded so the correction does not get lost
— the finding stands without it.

## P10 and P11 converge independently on the `AGND` naming defect

Both agents, cold to each other, found that **`AGND` names two different
nets** — the umbilical sense conductor and the module analog return. P11 adds
the sharper consequence:

> the plan's own check, "`AGND`, `PWR_GND`, `DIG_GND` still distinct", cannot
> catch the merge that matters, **because both at-risk nets are called
> `AGND`**.

And worse, that `verify.py`'s "`AGND` tied exactly once" asserts a property
ADR 0004:630 says `AGND` does **not** have — so an implementer following the
plan literally would *create* the tie the rule exists to prevent.

Agreement between agents that cannot see each other is the evidence standard
this project uses. Two independent confirmations makes this the wave's
highest-confidence finding.

## P3, P4, P9 — three cold agents, one recommendation: do not autoroute

**Convergent findings.** Three reviewers who could not see each other reached
the same conclusion by three different routes.

**P4 has the number.** Against Freerouting's own committed nightly benchmark,
filtered to 2-layer boards 25–90 cm² with ≥50 components (N = 159): release
2.4.1 returns a fully routed board **36 %** of the time, and a
fully-routed-and-clearance-clean board **19 %**. Upstream's own Tier B summary
says 3.4 % DRC-clean. And it has no star ground, no matched-pair support and no
per-net via control — upstream's own research doc says the only way to get a
star ground is hand-route-and-lock, and calls that fragile.

**P3 and P4 independently found the same idempotency bug**, which I did not
anticipate: **unlocked pre-existing tracks are frozen too.** Freerouting's lexer
has no `route` keyword, so unlocked copper falls through to `USER_FIXED` — not
routable, not deletable. P3 proved it by running the router: a deliberate
4-segment detour survived 10 router and 2 optimizer passes untouched while the
optimizer demonstrably improved another net in the same run.

**So run *n* freezes run *n−1*'s output and only fills gaps. The stage is not
re-runnable at all** unless every unlocked track is deleted before each export.

**And the smoke test I proposed proves nothing.** P3: "route one trace, lock it,
autoroute, diff it" passes *either way*, because locked tracks are held aside as
C++ objects and re-added byte-identically regardless. It needs a second,
deliberately ugly *unlocked* trace asserted to have changed.

### The Java claim — CONFIRMED, and it is a one-line fix

**Re-checked, 2026-09-21.** Installed JDK is **21.0.10**. Freerouting 2.2.0
through the current 2.4.1 target **Java 25** (`build.gradle` `VERSION_25`; P9
found `freerouting-2.4.1.jar` is class-file major 69 and
`UnsupportedClassVersionError` on 21).

But `openjdk-25-jre-headless` **is in noble's stock archive** —
`Candidate: 25.0.4.1+1-1~24.04.4`, `noble-updates/universe`. No allowlist
change needed. The plan's "Java 21 already present" was wrong; the remedy is
`apt install`.

### `timeout 1800 java …` destroys the output

P4: the SES is written only when the job reaches a terminal state in-process.
`SIGTERM` leaves **no `.ses` at all**. The correct form is
`--router.job_timeout=00:20:00`, and only colon forms parse — `"30m"` silently
means *no timeout*, which Freerouting's own javadoc documents incorrectly.

### Exit code 0 does not mean routed

`computeCliExitCode` returns 0 for `COMPLETED` *or* `TIMED_OUT` whenever bytes
were written. A stagnation stop with 40 unrouted connections exits 0. The thing
to assert on is `--router.result_json`, which carries
`connections.incompleteCount` and `clearanceViolations.totalCount`.

### P9: `kiutils` is abandoned, and SKiDL already does what I wanted it for

Last pypi release 2024-02-02, last commit 2024-05-02, README says "KiCad 6.0
and up". I named it as the way to render a schematic — which it cannot do.
**`Circuit.generate_schematic()` exists in SKiDL** (KiCad 6–9), so
`--schematic-parity` was never lost. Drop `kiutils` entirely.

### P9: the SWIG bindings are removed in KiCad 11

From official `kicad-python` 0.8.0: *"The SWIG bindings still exist in KiCad 9
and 10, but are removed in KiCad 11"*, and the IPC successor *"requires
communication with a running instance of KiCad"*. Stages 3–6 are the plan's
most custom code and all sit on SWIG, whose replacement is **less** headless.
Second independent sighting — P2 found the same line.

**Conclusion: minimise SWIG surface.** Use `kinet2pcb` rather than hand-writing
footprint loading, and put verify/export behind **KiBot 1.9.1**, so the
migration is someone else's problem.

## P6 — the Python advice is wrong in this container, all three ways

**Claim:** `python3` is 3.11, not noble's 3.12, while `_pcbnew.kiface` needs
`libpython3.12.so.1.0`. So "use the system python3" picks the wrong one,
`venv --system-site-packages` makes a 3.11 venv, and
`PYTHONPATH=/usr/lib/python3/dist-packages` is *worse than useless* because
that directory is already on `sys.path` — so `pcbnew.py` is found and then dies
on an ELF/ABI error instead of a clean `ImportError`.

**Re-checked, 2026-09-21. CONFIRMED, and worse than filed:**

```
$ which python3   → /usr/local/bin/python3 → Python 3.11.15
$ /usr/bin/python3 -V → Python 3.11.15      ← the "system" one is 3.11 too
$ both interpreters: 'dist-packages' already in sys.path → True
```

P6 said naming `/usr/bin/python3` was the trap and `/usr/bin/python3.12` the
fix. In this container `/usr/bin/python3` is *also* 3.11 via `alternatives`, so
the interpreter must be named by **explicit minor version matching the deb** —
nothing else is safe.

**Three stated gotchas falsified.** "Library tables need a GUI first" — no,
`FP_LIB_TABLE::LoadGlobalTable()` creates them from the template itself, so the
`cp` is redundant. **The real hazard is the opposite**: if the template is
missing it writes an *empty* table and carries on silently, so `kicad` without
`kicad-library-footprints` gives unresolvable footprints and no error.
`KICAD9_FOOTPRINT_DIR` is a substitution *inside* the tables, not an
alternative to them. And `pcb render` needs no GL in KiCad 9 — it is a CPU
raytracer, so the xvfb advice there is cargo cult that hides the real cost,
which is CPU minutes.

**The network requirement is two hosts, not one.** `add-apt-repository` needs
`api.launchpad.net` as well as `ppa.launchpadcontent.net`, because
`softwareproperties/ppa.py` goes through launchpadlib. Both are blocked, so the
PPA must be added by hand-written `.sources` plus key. And **containers are
blocked only at the blob CDN** — the registries answer, but
`production.cloudfront.docker.com` and `pkg-containers.githubusercontent.com`
are 403, so `docker pull` fails.

**Disk: there is no per-session quota.** `/` is a shared 252 GiB ext4, and P6
watched free space move 7.9 → 3.4 → 19 → 23 GiB during its own review, with a
tool call failing ENOSPC at the low point — consistent with what I saw. So a
5.4 GiB install cannot be planned against a number; it needs a free-space check
immediately before unpacking.

**And the sizes split the stages:** `kicad` plus its 46-package closure is
**695 MiB installed**. `kicad-packages3d` is **5.44 GiB** and is *not* in that
closure — but `export step` resolves per-footprint 3D models unless
`--board-only`, and the plan's stated reason for STEP is mechanical fit. So the
fab deliverable costs 695 MiB and the mechanical check costs 6.3 GiB. Two
different installs.
