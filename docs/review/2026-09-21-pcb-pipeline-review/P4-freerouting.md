# P4 — Freerouting in practice

**Slice:** every claim about Freerouting in `docs/reference/pcb-pipeline.md`, and
whether autorouting is the right approach for this board at all.
**Reviewer:** cold. No prior review directory read.
**Date:** 2026-09-21.
**Subject state:** the doc was edited during this review (a simulate stage was
inserted as stage 2, pushing hand-route to 4 and autoroute to 5). Nothing in the
Freerouting claims changed. Stage numbers below are the *current* ones; where the
brief says "stages 3 and 4" it means what are now **stages 4 and 5**.

## Provenance key

- `[source]` — read in a cloned repo at a named tag/commit, path and line given.
- `[test]` — I ran it in this sandbox.
- `[calc]` — arithmetic over `[source]` data, method shown.
- `[web]` — fetched URL.
- `[from memory]` — unverified. Used once, marked.

Repos read:
`github.com/freerouting/freerouting` @ `97758b5` (master, 2026-09-19) and tags
`v1.4.4 … v2.4.1`; KiCad `specctra_import_export/*` via
`raw.githubusercontent.com/KiCad/kicad-source-mirror/master`;
`github.com/ohmtech-rdi/eurorack-blocks` @ depth-1 main.

---

## 1. Verdict table

### 1.1 The stack row

| Claim (line 21–22) | Verdict | Correct statement |
|---|---|---|
| "**Freerouting** 2.x" | **Under-specified, and the imprecision is load-bearing** | 2.x is not one thing. 2.0.0/2.0.1/2.1.0 are Java 21 builds; 2.2.0 through the current release 2.4.1 are Java 25 builds. Name the exact version. |
| "Java 21 already present" | **WRONG for every release since 2.2.0** | `build.gradle` sets `sourceCompatibility = targetCompatibility = JavaVersion.VERSION_21` and `languageVersion 21` at `v2.0.0` and `v2.1.0`, and `VERSION_25` / `of(25)` at `v2.2.0`, `v2.3.0`, `v2.4.0`, `v2.4.1` and master `[source: build.gradle:27-33]`. `docs/self-hosting.md:142` requires "Java JRE 25+" `[source]`. `Dockerfile:2,26` builds and runs on `eclipse-temurin:25-*` `[source]`. This sandbox has **OpenJDK 21.0.10 only** `[test: java -version; ls /usr/lib/jvm]`. Class-file major 69 will not load on a 21 JRE. |
| Fix | — | `apt-get install openjdk-25-jre-headless` — candidate `25.0.4.1+1-1~24.04.4` is in **noble's stock archive**, no allowlist change `[test: apt-cache policy openjdk-25-jre-headless]`. Or pin Freerouting `v2.1.0`, which is the last Java-21 build — but that forgoes ~2 years of router work. |
| "**xvfb** — Virtual display for the two things that still want GL" | **WRONG about Freerouting** | Freerouting has no OpenGL anywhere: zero matches for `opengl\|jogl\|GLCanvas\|lwjgl` across all `.java`/`.gradle`; it is Swing/Java2D (358 `javax.swing` imports in `src/main`) `[source: grep at master]`. `LIBGL_ALWAYS_SOFTWARE=1` does nothing for it. The `kicad-cli pcb render` half of that row is outside this slice. |
| Asset name `freerouting.jar` | Minor | The published artifact is `freerouting-<version>-executable.jar` (`archiveBaseName = 'freerouting-current'`, `archiveClassifier = 'executable'`) `[source: build.gradle:261-262]`; `docs/self-hosting.md` calls it `freerouting-executable.jar`. Not `freerouting.jar`. |

### 1.2 Flags in the stage-5 invocation

`timeout 1800 xvfb-run -a java -jar freerouting.jar -de board.dsn -do board.ses -mp 100`

| Token | Real? | Exact behaviour |
|---|---|---|
| `-de` | **Yes** | Design input. Accepts `.dsn`, and optionally a `.ses` and/or `.rules` joined with `+` (`-de b.dsn+b.rules`). **If no rules file is named it silently auto-loads an adjacent `<boardname>.rules`** `[source: docs/command_line_arguments.md; GlobalSettings.java:608-620]`. A stale `board.rules` left in the build directory will therefore be picked up without anyone asking for it — delete it in `route.py`. Parsed with `startsWith("-de")`, so `-de…` prefixes match loosely. |
| `-do` | **Yes** | Output format chosen by extension: `.ses`, `.dsn`, `.scr` `[source: docs/command_line_arguments.md]`. |
| `-mp` | **Yes, but** | Bounds **autorouter passes, not time or items**. Clamped to `[0, 9999]`; `0` means *no limit* and **0 is the default** `[source: GlobalSettings.java:744-758; DefaultSettings.java:147]`. Still accepted in the current release `v2.4.1` with no warning `[source: v2.4.1 GlobalSettings.java:670]`; on master it logs a deprecation and the canonical path is `--router.autorouter.max_passes` `[source: GlobalSettings.java:746-747; LegacyRouterSettingsBridge.java:31-43; GlobalSettingsTest.java:36-41]`. |
| `-mp 100` | **Not a bound in practice** | The batch loop stops on its own after `STAGNATION_PASS_LIMIT = 10` consecutive passes that fail to improve the score by `STAGNATION_SCORE_THRESHOLD = 0.5` `[source: BatchAutorouter.java:52,60; AutorouteBatchLoop.java:460-535]`. Across upstream's own 1157-fixture nightly run, completed autorouter passes are in the single digits to low twenties `[source: scripts/benchmark/results/benchmarks.md, "Passes" column]`. 100 never binds. It is decorative. |
| `xvfb-run -a` | **Unnecessary from 2.0.0 on** | See §1.3. |
| `timeout 1800` | **Actively harmful as the primary bound** | See §1.4. |
| missing | **`--gui.enabled=false` is absent and is the one flag that matters** | `gui.enabled` defaults to **true** `[source: GuiApplicationSettings.java:11; GlobalSettings.java:37-38]`. Without it you are relying on an exception fallback. |
| missing | `--api_server.enabled=false`, `--mcp_server.enabled=false` | Both default false `[source: ApiServerSettings.java:11; McpServerSettings.java:11]`, so this is belt-and-braces — but upstream's own plugin passes them explicitly `[source: integrations/KiCad/.../router_dsn.py:_build_command]`. |
| missing | `-da` | Telemetry is **on by default** (`isTelemetryAllowed = true` `[source: UserProfileSettings.java:19]`), plus a `VersionChecker` thread and an unconditional `Thread.sleep(1000)` at startup `[source: Freerouting.java:1546-1585]`. In a sandbox with restricted egress that is dead time and outbound noise. `-da` disables the analytics. |

### 1.3 "may need a display, run under xvfb-run" — changed across versions, and the doc is describing the old behaviour

| Version | Headless? |
|---|---|
| ≤ 1.9.0 | **No.** `MainApplication.main` calls `Toolkit.getDefaultToolkit().getScreenSize()` and `.getScreenResolution()` **unguarded** at startup `[source: v1.9.0 gui/MainApplication.java:265-275]`. No `DISPLAY` → `HeadlessException` → the process dies before it reads the DSN. `xvfb-run` was genuinely required. |
| ≥ 2.0.0 | **Yes.** The same block is wrapped in `try { … } catch (Exception) { … guiSettings.isEnabled = false; }` `[source: v2.0.0 Freerouting.java:178-188]`, and master logs *"If you are running in a headless environment, disable the GUI by setting gui.enabled to false"* before falling back `[source: Freerouting.java:1466-1485]`. |
| Explicit switch | **`--gui.enabled=false`**. Not `--gui off`. Separators `.`, `:` and `-` are all accepted, so `--gui-enabled=false` (the form in upstream's own `Dockerfile:50`) works too `[source: ReflectionUtil.java:23 `split("[.:\\-]")`; GlobalSettings.java:582-604]`. |
| What runs headless | `initializeCli()` is entered only when the GUI is off; it loads the DSN, waits for the job, writes the output and exits `[source: Freerouting.java:85-250, 1636-1690]`. `RoutingPipeline.createForHeadless(job)` is the headless routing path and has a dedicated test asserting a full autoroute pass completes with no GUI `[source: RoutingJobSchedulerActionThread.java:119; src/test/.../HeadlessRoutingTest.java]`. |

**Verdict:** drop `xvfb-run` for Freerouting and pass `--gui.enabled=false`. The
exception fallback works, but relying on it means the run passes through
`Toolkit`, analytics identify and the version check before it discovers it is
headless.

### 1.4 "Pass `-mp <passes>` *and* wrap it in a shell timeout" — the shell timeout is the wrong mechanism

The SES is written **after** the job reaches a terminal state, inside the same
process: `initializeCli` blocks in a `while (!isCliTerminalState(state))` loop
and only then calls `writeCliOutputIfAvailable` `[source: Freerouting.java:157-168, 258-275]`.
`timeout 1800` sends `SIGTERM`; the only shutdown hook registered is an
analytics flush `[source: Freerouting.java:1568-1571]`. **A shell-timeout kill
produces no `.ses` at all** — you lose the entire run rather than getting a
partial one.

The right mechanism already exists:

- `--router.job_timeout=HH:MM:SS`. A monitor thread calls `job.thread.requestStop()`,
  waits a `GRACE_PERIOD` of 30 s, sets `state = TIMED_OUT`
  `[source: RoutingJobSchedulerActionThread.java:26-88]`, and `writeCliOutputIfAvailable`
  **does** write on `TIMED_OUT` `[source: Freerouting.java:266-272]`. Capped at
  `MAX_TIMEOUT = 24 h`. Present in `v2.4.1` `[source: v2.4.1 RouterSettings.java "job_timeout"]`.
- **Format trap.** `parseTimespanString` only accepts colon forms — `HH:MM:SS`,
  `MM:SS`, `SS` `[source: TextManager.convertFromTimespanToDurationFormat]`.
  `"30m"` or `"1800s"` parse to `null`, which means **no timeout, silently**.
  Freerouting's own javadoc in the same repo documents `"5m"`/`"300s"`
  `[source: FanoutSettings.java:104-106; OptimizerSettings.java:100-102]` and is
  wrong. Use `--router.job_timeout=00:20:00`.
- Keep an outer `timeout` as a *backstop only*, set comfortably above
  `job_timeout + 30 s`, to catch a hung JVM rather than to bound the route.

### 1.5 Does it honour net-class rules from the DSN? — Yes, for width and clearance only

| Link in the chain | Evidence |
|---|---|
| KiCad writes them | `exportNETCLASS` emits `(width %.6g)` when `HasTrackWidth()` and `(clearance %.6g)` when `HasClearance()`, for the Default class plus every non-default class actually in use `[source: kicad specctra_export.cpp:1751-1820]`. A global default rule is written from the Default netclass, plus an `smd_smd` clearance at **defaultClearance / 4** `[source: ibid. 1277-1294]`. |
| Freerouting reads them | `Network.insert_net_class` maps `Rule.WidthRule → setTraceHalfWidth`, `Rule.ClearanceRule → clearance matrix`, both globally per class and per layer via `(layer_rule …)` `[source: io/specctra/parser/Network.java:440-530]`. |
| What is dropped | Any other rule type logs *"rule type not yet implemented"* and is discarded `[source: ibid. 491-494, 517-520]`. |

**Correction to the doc.** Stage 3 says: *"Both are read by `kicad-cli pcb drc`,
so what the router obeys and what DRC checks are the same file."* The first half
is true; the conclusion is **false**. The DSN carries netclass width, clearance,
via padstacks and max/min trace length — nothing else. `<project>.kicad_dru`
custom rules (copper-to-edge, hole-to-hole, per-area constraints, conditional
rules) are **not** exported to Specctra and Freerouting has never seen them.
Upstream says as much about its own newer JSON path: *"It does not yet import all
KiCad design rules (including copper-to-edge clearance)"*
`[source: integrations/KiCad/README.md]`. Expect DRC to find violations the
router had no way to avoid.

### 1.6 Does it honour protected / fixed wiring? — Yes, and the round trip is sound by construction

The doc treats this as an open risk to be proven on the smoke board. The source
settles it:

| Step | Evidence |
|---|---|
| KiCad export, **locked** track/via | `if( track->IsLocked() ) wire->m_wire_type = T_fix;` with the comment *"tracks with fix property are not returned in .ses files"* `[source: kicad specctra_export.cpp:1679-1682, 1730-1733]`. |
| KiCad export, **unlocked** existing track | `T_protect`. Zones are also exported as `T_protect` polygons `[source: ibid. 1351, 1682]`. |
| Freerouting parse | `calcFixed`: token `fix` → `SYSTEM_FIXED`; `shove_fixed` → `SHOVE_FIXED`; anything else that is not `normal` (i.e. `protect`) → `USER_FIXED` `[source: io/specctra/parser/Wiring.java:257-278; Keyword.java:34,96]`. |
| What fixed means | `isUserFixed()` and `isDeletionForbidden()` are true at `USER_FIXED` and above; `isShoveFixed()` true at `SHOVE_FIXED` and above `[source: board/model/items/Item.java:861-883]`. The trace normaliser and `PolylineTrace.split` both explicitly refuse to touch them `[source: PolylineTraceNormalization.java:105; PolylineTrace.java:723]`. |
| SES writeback | `SesWriter.writeNet` **skips every `SYSTEM_FIXED` item** `[source: io/specctra/SesWriter.java:339-341]`, so locked KiCad copper never appears in the session file. |
| KiCad import | *"Remove unlocked tracks/vias (locked ones stay; they are exported as fixed and omitted…)"* — `if( !track->IsLocked() ) aCommit.Remove( track );` `[source: kicad specctra_import.cpp:353-358]`. |

**Verdict: the lock round trip works by design, not by luck.** Keep the smoke test
— it costs nothing and it catches version skew — but the strategy is not at risk
and the doc should stop hedging on it.

**Two corollaries the doc misses:**

1. **Unlocked pre-existing copper is frozen too.** `protect → USER_FIXED` means
   Freerouting will not rip up or shove *any* track already on the board,
   locked or not. Re-running the autoroute on an already-autorouted board
   therefore compounds the previous result instead of improving it. `route.py`
   must delete all unlocked tracks and vias before exporting the DSN, every run.
   This is the only way the stage is idempotent.
2. **Fixed traces cannot be shoved.** The hand-routed AGND star, the matched
   BREATH/AGND pair, the split `PWR_GND`/`DIG_GND` copper and the 1 A
   load-switch path all become hard obstacles on a two-layer board. Locking
   them does not just protect them — it materially reduces what is left
   routable. This makes stage 5 *harder* than the benchmark numbers in §2, not
   easier.

### 1.7 What happens on a board it cannot fully route

| Question | Answer |
|---|---|
| Partial SES? | **Yes.** `SesWriter.writeNet` emits whatever items exist per net; nets with nothing routed simply get no scope `[source: SesWriter.java:334-360]`. You get a partial session file and KiCad imports it happily. |
| Does the exit code tell you? | **No.** `computeCliExitCode` returns 0 for `COMPLETED` **or** `TIMED_OUT` as long as bytes were written; 1 otherwise `[source: Freerouting.java:341-348]`. A stagnation stop with 40 unrouted connections is `COMPLETED` and exits **0**. **Never gate the pipeline on Freerouting's exit code.** |
| Does it report unrouted? | **Yes, two ways.** (a) A human-readable per-net report — *"Net 'GND' (1 unrouted connection): …"* with component and pin names for both endpoints — logged at the stagnation stop `[source: BatchAutorouter.java:482-521; AutorouteBatchLoop.java:504,534]`. (b) **Machine-readable**, via `--router.result_json=<path>`: a manifest with `board_statistics` (including `connections.incompleteCount` and `clearanceViolations.totalCount`), per-phase `before`/`after` snapshots, `passes_completed`, `final_state`, `exit_code`, `normalized_score` `[source: core/results/RoutingResultManifest.java; Freerouting.java:352-376]`. Present in `v2.4.1` `[source: v2.4.1 RouterSettings.java "result_json"]`. |

This is the single most useful thing in this slice that the doc does not know
about. If Freerouting stays, stage 7's "zero unrouted" assertion should read
`result.json` and not the process exit status.

### 1.8 Other real traps found in source

- **Non-Latin characters break the Specctra parser.** Upstream's own KiCad plugin
  strips `Ω`, `µ`, `Φ` from every line of the exported DSN and rewrites the
  `(pcb …)` header, with the comment *"KiCad net names and reference designators
  sometimes contain Greek letters … that the Specctra parser cannot handle"*
  `[source: integrations/KiCad/.../router_dsn.py:25-31, _sanitize]`. Any
  sanitising step must run on the DSN before Freerouting sees it.
- **`--router.via_costs` is documented and does not work.** `docs/command_line_arguments.md`
  gives `--router.via_costs=150` as an example. `viaCosts` lives on
  `RoutingCostSettings`, reachable at `router.scoring.via_costs`
  `[source: RoutingCostSettings.java:34-37; RouterSettings.java:105-106]`, and the
  legacy bridge only rewrites the six flat *autorouter* keys
  `[source: LegacyRouterSettingsBridge.java:31-43]`. `--router.via_costs=…` hits
  `NoSuchFieldException` and logs *"Unknown settings property"*, then routes on
  with the default `[source: GlobalSettings.setValue:509-529]`. Do not copy
  examples out of that document without checking them against `setValue`.
- **`-inc` does nothing headless in the current release.** In `v2.4.1` the only
  consumer of `routerSettings.ignoreNetClasses` is `GuiManager.java:456-463`
  — there is **no call site in the CLI or headless path**
  `[source: git grep ignoreNetClasses/isIgnoredByAutorouter @ v2.4.1]`. The flag
  parses, the field is set, and nothing reads it. Fixed on master, where
  `applyNetClassExclusions` is called from `HeadlessBoardManager:791` and
  `RoutingJobScheduler:187` `[source: RouterSettings.java:506-524 and those call
  sites]` — unreleased as of this review. So "just tell it to leave the analog
  classes alone" is **not available** in any shipped version when running headless.

---

## 2. Is autorouting the right approach here at all?

### 2.1 What Freerouting actually achieves on boards like this one

Upstream runs a nightly benchmark over 1157 real open-hardware fixtures and
commits the results `[source: scripts/benchmark/results/benchmarks.md, generated
2026-09-19]`. I filtered it to the comparable population — **2-layer boards,
25–90 cm², ≥50 components** — and counted `[calc: python over the committed
markdown; N=159 fixtures; "fully routed" = Unrouted column 0; "clean" = Unrouted
0 AND Violations 0]`:

| Version | Fully routed | Fully routed **and** 0 clearance violations | Median unrouted | Median violations | Median runtime |
|---|---|---|---|---|---|
| 1.9.0 | 57/159 (36%) | 38/159 (24%) | 1 | 2 | 82 s |
| **2.4.1 (current release)** | **57/159 (36%)** | **31/159 (19%)** | **1** | **3** | **230 s** |
| 2.5.0-RC7 (unreleased) | 70/159 (44%) | 49/159 (31%) | 1 | 0 | 89 s |

Upstream's own Tier B summary ("standard 2–4 layer boards") says the same thing
more bluntly: at 2.4.1, **3.4% of fixtures come out with zero DRC violations** and
28.7% fully routed `[source: benchmarks.md, Tier B table]`.

Named comparables from the same file, all 2-layer, all at 2.4.1 `[source]`:

- `zx-tsid` — 73.8 × 37.3 mm, 67 components, 30 nets: **42 unrouted** after 301 s.
  Every version from 1.9.0 to 2.5.0-RC7 leaves between 34 and 78.
- `Box0-hv-analog-breakoutboard` — 35 cm², 57 components: **134 unrouted**, score 89/1000.
- `BrushlessESC` — 30.2 cm², 79 components: 0 unrouted, **1368 clearance violations**.
- `Lys` — 41.9 cm², 78 components: 87 unrouted **and** 1252 violations.
- `kitspace_XassetteAsterisk` — 31.4 cm², 145 components: 87 unrouted after 906 s.

Woody's module PCB sits at the dense end of that population: the panel is
`panel-width` (10HP) and the usable height is `panel-height-budget` — which is
still **disputed** in `config/figures.yaml`, so the board area is not yet a
settled number — carrying roughly 120 BOM rows on two layers, with several nets
already hand-routed and locked as immovable obstacles (§1.6 corollary 2).

**So the honest expectation for stage 5 is: about a one-in-five chance of a board
that is both fully routed and clearance-clean, and a near-certainty of a
several-minute run that hands back work.** Stage 7's assertions "zero unrouted"
and DRC-clean will fail most of the time, and stage 7's own escape hatch is
*"five full iterations, then stop and report"* — which is the doc already
predicting this outcome without naming the cause.

### 2.2 What Freerouting cannot express, which is most of this board's design

The design thesis of this module, as stated in the doc's own stage 4 and stage 6,
is a set of *topological* constraints. Freerouting has representations for none
of them:

- **Star ground.** The router builds a minimum-spanning-tree / maze-search
  connection per net and will freely daisy-chain or bus ground pads. Upstream's
  own analysis of the feature request states the only current way to get a star
  is *"manually route every ground trace from the star center … lock those traces
  … let the autorouter route everything else around"*, and calls that workflow
  **"fragile"** `[source: docs/research/star-ground-routing.md]`. Status:
  *"Open — analysis complete, implementation not started."*
- **Matched / parallel pairs.** No differential-pair or length-matching routing
  exists in `src/main` at all. The only hits for "length matching" are a GUI
  colour-table entry and a ratsnest *display* of violations
  `[source: grep -ri "differential\|diff_pair\|matched.length" src/main]`.
  The `BREATH`/`AGND` pair cannot be stated.
- **Per-net via prohibition.** Via cost is a single global scalar
  (`router.scoring.via_costs`, plus `plane_via_costs`)
  `[source: RoutingCostSettings.java:34-41]`. There is no per-net-class "no vias
  on this net". `[web]` corroborates this as the commonly-cited limitation:
  *"Freerouting treats all vias equally and doesn't support prioritizing fewer
  vias for power/ground connections."*
- **Loop area, decoupling proximity, keepout-from-bore.** These are stage-6/7
  assertions in the doc. The router has no objective term for any of them, so
  every one is a post-hoc check that, when it fails, sends you back to
  re-placement — not to a router setting.

### 2.3 What comparable projects actually do

- **eurorack-blocks** (`ohmtech-rdi`) is the closest analogue: an open-hardware
  Eurorack framework that generates the schematic, the PCB, the panel, the BOM
  and the gerbers from a DSL, headlessly. Routing is the **one step it refuses to
  automate**: *"it is not possible to fully automate auto-routing … with Kicad 5
  and 6 for various technical reasons. We are working on it, but in the meantime,
  you can do manually what is not possible to automate."* The user sets
  `route manual` in the module definition, which *suppresses gerber generation*,
  routes by hand or with the **interactive Freerouting GUI**, and then re-runs
  `erbb build hardware --only-gerber`
  `[source: eurorack-blocks documentation/diy/routing.md]`. That is exactly the
  shape recommended below — and note it is only their *front panel* board
  (pads to headers), not an analog signal board.
- **Freerouting's own KiCad plugin defaults to the interactive GUI**:
  `DEFAULT_GUI_ENABLED = True`, with headless as the opt-out
  `[source: integrations/KiCad/.../config.py:157-163]`. The README's GUI
  walkthrough says a run *"may take from a few minutes to several hours"*
  `[source: README.md]`. Upstream's posture on its own tool is interactive-first.
- Hobbyist practice `[web]` is consistent: hand-route power, clocks and sensitive
  low-level analog; autoroute the remainder; one report of switching to the
  autorouter after 40 hand traces took a day. That is a *human-in-the-loop*
  pattern, not a build stage.

### 2.4 Recommendation

**Do not put Freerouting in the automated pipeline. Make routing the one
human, non-headless step, and keep everything on both sides of it scripted.**

This is not a hedge and it is not "hand-route everything in a script" either.
The reasoning, in order of weight:

1. **The autoroute is the one stage that is not re-runnable, which is the doc's
   entire stated goal.** A committed `.kicad_pcb` re-runs perfectly — it is a
   constant. An autoroute re-derives, and it re-derives *differently*: the same
   fixtures swing from 0 to 45 violations and 0 to 15 unrouted between adjacent
   versions of the same router `[source: benchmarks.md, `1Bitsy` fixture]`.
   Putting it in the pipeline makes the build output depend on which `.jar` was
   downloaded that day. That is this project's named failure mode — a value
   changes and the derived artifact does not follow — wearing a different hat.
2. **It does not remove the human step; it adds one.** Four times in five you get
   a board with unrouted airwires, clearance violations, or both, which a person
   must then finish in the GUI anyway — now on top of copper they did not lay and
   cannot review as a diff.
3. **The board's actual constraints are unstateable.** Star ground, matched pair,
   no-vias-on-analog, loop area: §2.2. Stage 4 already concedes this ("Specctra
   cannot express any of these"). Once the nets that matter are hand-routed and
   locked, what is left for the autorouter is bulk connectivity — and that is
   precisely what KiCad 9's interactive push-and-shove router does well, live,
   against the same netclass widths and clearances **and** the `.kicad_dru`
   rules Freerouting never receives (§1.5).
4. **The output is unreviewable.** This project reviews by cold, node-indexed
   reading of diffs. Autorouted copper produces neither a reviewable diff nor a
   rationale. Hand-routed copper, committed once, can at least be read against
   the schematic pages.
5. **Cost is smaller than it looks.** The critical nets are hand-routed under the
   current plan regardless. Placement is scripted. What remains is the bulk of a
   two-layer board with roughly 120 parts — a session's work, once, for a board
   the ROADMAP already expects to spin.

### 2.5 What replaces stages 4 and 5

Collapse the current **stage 4 (hand-route and lock)** and **stage 5
(autoroute)** into a single stage, and make the pipeline's guarantee a *parity*
guarantee rather than a *re-derivation* guarantee.

**Stage 4 — Route (one interactive step, output committed).**

1. `build_board.py` is unchanged and still fully scripted: outline, footprints,
   nets, placement, net classes, `.kicad_dru`. It writes
   `pcb/<board>/<board>-placed.kicad_pcb` and **that file is a build artifact,
   regenerated every run**.
2. A human routes it once in KiCad 9's PCB editor and commits
   `pcb/<board>/<board>-routed.kicad_pcb`. **This file is source, not output.**
   The interactive router enforces netclass widths and clearances live, and
   `.kicad_dru` applies — neither is true of the DSN path.
3. `verify.py` gains one new assertion, and it is the assertion that makes the
   manual step safe:

   > the routed board's **netlist, refdes set, footprint assignment and
   > placement** are identical to the freshly generated `-placed.kicad_pcb`.
   > Routing may add copper and change nothing else.

   Checkable with `pcbnew` or `kiutils`. When a SKiDL change moves a net or a BOM
   change swaps a footprint, this fails and names what must be re-routed — the
   same mechanical discipline as `tools/check-staleness.py`, applied to copper.
4. Stages 6 (pour), 7 (verify) and 8 (fab output) are unchanged and remain fully
   headless. The pipeline is still "one command from source to a fab zip"; the
   routed board is simply one of the sources.

**Consequences for the rest of the doc:**

- The `xvfb` row loses its Freerouting justification (it keeps the
  `kicad-cli pcb render` one).
- The Freerouting row and the Java claim come out of the stack table entirely.
- `pcb/smoke/` keeps its value — it still proves install, API signatures and
  export flags — and loses only the lock-round-trip objective, which §1.6 settles
  from source anyway.
- The "**One thing to prove specifically**" paragraph about locked tracks can be
  deleted or reduced to a citation of §1.6.
- Stage 7's "zero unrouted" assertion becomes trivially satisfiable, because a
  human does not hand over a board with airwires.

**If the autoroute is kept anyway**, use it as an *assist inside* the manual
stage — run it on a scratch copy, cherry-pick what looks right, hand-finish —
never as a build gate. The correct invocation for that, taken from upstream's own
plugin and corrected for the findings above:

```sh
# requires JRE 25 (apt: openjdk-25-jre-headless); NOT the Java 21 in this sandbox
java -jar freerouting-2.4.1-executable.jar \
  -de board.dsn -do board.ses \
  --gui.enabled=false \
  --api_server.enabled=false --mcp_server.enabled=false \
  -mp 20 \
  --router.job_timeout=00:20:00 \
  --router.result_json=route-result.json \
  --router.layers.preferred_direction_horizontal=true,false \
  --router.scoring.via_costs=200 \
  --router.strict_drc=true \
  --logging.file.location=build/logs \
  -da -host Woody/1
```

- No `xvfb-run`, no shell `timeout` as the bound (an outer `timeout 1500` as a
  backstop only). `-mp 20` is `--router.autorouter.max_passes=20` on master.
- `--router.strict_drc=true` rips up a connection whose new copper carries
  clearance violations instead of keeping it `[source: RouterSettings.java:60-68]`;
  present in `v2.4.1` `[source: v2.4.1 RouterSettings.java "strict_drc"]`. It
  trades unrouted count for violation count, which is the right trade here: an
  airwire is visible, a violation is a fab defect.
- **Gate on `route-result.json`**, asserting `connections.incompleteCount == 0`
  and `clearanceViolations.totalCount == 0` — **never on the exit code** (§1.7).
- Delete every unlocked track and via before exporting the DSN (§1.6 corollary 1).
- Strip `Ω µ Φ` from the DSN first (§1.8).
- Do **not** expect `-inc` to keep the router off the analog classes: it is a
  no-op headless in every released version (§1.8).

---

## 3. Findings summary

| # | Finding | Severity |
|---|---|---|
| P4-1 | "Java 21 already present" — every Freerouting release since 2.2.0 needs JRE 25; sandbox has 21 only. The stage cannot run as written. | **Blocking** |
| P4-2 | `timeout 1800 java …` destroys the output rather than bounding it. Use `--router.job_timeout=HH:MM:SS`; `"30m"` silently means no timeout. | **Blocking** |
| P4-3 | Exit code 0 does not mean routed. Gate on `--router.result_json`. | **Blocking** |
| P4-4 | `-mp 100` never binds (stagnation stop at 10 passes; observed passes ≤ ~21). Decorative. | Medium |
| P4-5 | `xvfb-run` unnecessary since 2.0.0; Freerouting has no OpenGL. Use `--gui.enabled=false` (GUI defaults **on**). | Medium |
| P4-6 | "What the router obeys and what DRC checks are the same file" is false: `.kicad_dru` is not exported to DSN. | Medium |
| P4-7 | Locked-track round trip works by construction (`fix` → SYSTEM_FIXED → omitted from SES → KiCad keeps locked). Doc's open risk is closed. | Informational |
| P4-8 | **Unlocked** pre-existing copper is also frozen (`protect` → USER_FIXED); the stage is not idempotent unless unlocked copper is deleted first. | High |
| P4-9 | `-inc` / `ignore_net_classes` is a no-op in the headless path of every released version. | Medium |
| P4-10 | `--router.via_costs` from upstream's own CLI doc is an unknown property; the real path is `--router.scoring.via_costs`. | Low |
| P4-11 | Ω/µ/Φ in the DSN break the Specctra parser; upstream strips them before routing. | Low |
| P4-12 | On 159 comparable 2-layer boards, the current release returns a fully-routed, clearance-clean board **19% of the time** (median 1 unrouted, 3 violations). Stage 7's assertions will fail most runs. | **Recommendation basis** |
| P4-13 | No star-ground, no matched-pair, no per-net via control — i.e. no representation for this board's stated design constraints. | **Recommendation basis** |

## 4. What I could not verify

- I could not download a release `.jar` (GitHub releases API and
  `releases/download/…` both return 404 through this session's proxy) `[test]`,
  so the Java requirement rests on `build.gradle`, `Dockerfile` and
  `docs/self-hosting.md` at each tag rather than on a class-file version read
  from the shipped artifact.
- `pcbnew` is not installed here `[test: ModuleNotFoundError]`, so I could not
  run an end-to-end DSN → SES round trip. The lock behaviour in §1.6 is read from
  both sides' source, not executed.
- `pcbnew.ExportSpecctraDSN` / `pcbnew.ImportSpecctraSES` do exist as Python
  bindings — upstream's plugin guards on
  `hasattr(pcbnew, "ExportSpecctraDSN") and hasattr(pcbnew, "ImportSpecctraSES")`
  `[source: integrations/KiCad/.../gui_helpers.py:91-95]` — but I could not reach
  the KiCad SWIG interface files to confirm the signatures. The doc's own advice
  to `help()` them first stands.
- The benchmark population in §2.1 is open-hardware boards of mixed character,
  not specifically precision-analog ones. Analog boards are not harder to *route*
  than digital ones of the same density; they are harder to route *acceptably*.
  The 19% figure is therefore an **upper** bound on what this board would get.
- `[from memory]` — nothing in this report rests on memory. Every claim above
  carries a `[source]`, `[test]`, `[calc]` or `[web]` tag.

**Sources fetched from the web:**
[eurorack-blocks routing docs](https://eurorack-blocks.readthedocs.io/en/latest/diy/routing.html)
(read via the repo, as the hosted page is egress-blocked) ·
[freerouting/freerouting](https://github.com/freerouting/freerouting) ·
[Why do people choose to NOT use the auto-router? — KiCad forum](https://forum.kicad.info/t/why-do-people-choose-to-not-use-the-auto-router/25849) ·
[PCB Autorouting — Big Mess o' Wires](https://www.bigmessowires.com/2019/03/27/pcb-autorouting/)
