# P9 — Alternatives and prior art: is this the right pipeline at all?

**Subject:** `docs/reference/pcb-pipeline.md` (Proposed 2026-09-21, not run).
**Slice:** what already exists, and whether the plan reinvents it badly.
**Method:** cold. No review directory read. Every claim below was checked by
cloning the public repo, querying pypi.org, or running the thing.
**Date of investigation:** 2026-09-21.

### Provenance key

- `[source]` — read in a cloned repo or on pypi.org, with path and date.
- `[test]` — I ran it in this sandbox and this is the output.
- `[from memory]` — unverified recollection. Treat as a lead, not a fact.

Repo last-commit dates are the tip of the default branch at the time of the
clone (2026-09-21) unless stated otherwise.

---

## 0. The short answer

**The generative half of the plan is right and has no mature competitor. The
verification-and-output half is a solved problem that the plan is about to
solve again, worse.**

Keep KiCad + SKiDL + `pcbnew` for netlist → board → route → pour. Delete
`export.py`, delete most of `verify.py`'s plumbing, and put stages 7 and 8
behind **KiBot**, which is a maintained declarative YAML front end for exactly
those two stages and which the plan does not mention.

Three specific things in the stack table are **wrong or unbuildable as
written**, proven by execution below: the Freerouting/Java pairing, the xvfb
claim, and `kiutils`. One is wrong in a way that would stop the first run dead.

---

## 1. Candidate tools

| Tool | What it does | Maintained? | Would replace | Verdict |
|---|---|---|---|---|
| **KiBot** 1.9.1 | Declarative YAML: DRC/ERC preflights, zone-fill check, gerbers, drill, STEP, SVG, render, netlist, BOM, position, board diff, fab zip, report | **Yes** — HEAD 2026-07-28, pypi 2026-07-28, KiCad 10 support `[source]` | **Stages 7 and 8 wholesale**, plus the zip, plus the generated BOM, plus the pre/post-route diff | **Adopt** |
| **KiAuto** 2.3.10 (= `kicad-automation-scripts`) | GUI automation for what `kicad-cli` can't do | Yes — 2026-07-14 `[source]` | Nothing directly; it is already a KiBot dependency | Comes along with KiBot |
| **KiDiff** / `kidiff` 2.6.0 | PCB/SCH image diff between git refs | Yes — pypi 2026-06-01 `[source]` | The "diff the locked nets" check, at layer granularity | Via KiBot's `diff` output |
| **Gasman2014/KiCad-Diff** | Same idea, standalone | Yes — 2026-09-20 `[source]` | Same | Redundant with KiDiff |
| **SKiDL** 2.3.0 | Circuit as Python, ERC, netlist, **schematic**, PCB via kinet2pcb, SPICE | **Yes** — HEAD 2026-08-10, 2.3.0 released 2026-07-28 with KiCad 10 backend `[source]` | — (it *is* the plan's choice) | **Keep** — and use more of it than the plan does |
| **kinet2pcb** 1.1.4 | KiCad netlist → `.kicad_pcb`, footprints loaded and nets assigned | Yes — 2025-11-03, pypi 2025-11-04 `[source]` | Most of `build_board.py` | **Adopt** (SKiDL calls it for you) |
| **kiutils** 1.4.8 | S-expression reader/writer for `.kicad_sch` / `.kicad_pcb` | **No** — last commit 2024-05-02, last pypi 2024-02-02, README says "KiCad 6.0 and up" `[source]` | — | **Drop** (see §3.3) |
| **kicad-python** 0.8.0 (official IPC bindings) | The supported successor to `pcbnew` SWIG | Yes — pypi 2026-08-30, gitlab.com/kicad/code/kicad-python `[source]` | Would replace `pcbnew` — **but requires a running KiCad** | Not usable headless. See §3.4 |
| **Freerouting 2.4.1** | Autorouter, DSN→SES, genuinely headless via `--gui.enabled=false` | Yes — HEAD 2026-09-19 `[source]` | — | Keep, but **not on Java 21** (§3.1) |
| **Freerouting 1.9.0** | Same, older | Frozen (build date 2023-10-30) `[test]` | — | Runs on Java 21, **needs xvfb** `[test]` |
| **@tscircuit/capacity-autorouter** | MIT autorouter, hypergraph/successive-approximation | Very — v0.0.918, 2026-09-20 `[source]` | Freerouting | **No.** Consumes `SimpleRouteJson`; the KiCad↔DSN bridges (`dsn-converter`, `dsn-to-circuit-json`, `circuit-json-to-dsn`) are 0–6 star repos with 293 open issues on the main one `[source]` |
| **atopile** 0.15.9 | A whole language for circuits-as-code, constraint solver, parametric part picking, KiCad layout sync | Alive on pypi (2026-09-12) — but see §4 | SKiDL + netlist + BOM | **No.** Decisively wrong fit; four independent reasons in §4 |
| **faebryk** 4.1.2 | Python circuit framework | **Absorbed into atopile** — it is `src/faebryk/` in the atopile tree; standalone pypi dead since 2024-10-28 `[source]` | — | Not a separate option |
| **edea** 0.8.4 | KiCad module composition (gitlab edea-dev/edea) | Thin — HEAD 2025-06-10, pypi 2025-06-09 `[source]` | Nothing the plan needs | No |
| **KiKit** 1.8.1 | Panelization, `kikit fab <house>` presets, board stencils | Yes — 2026-08-05 `[source]` | Part of stage 8 if panelizing | Not needed — a single 45×110 mm board, and the "panel" here is a *front* panel |
| **PcbDraw** | Pretty board renders / assembly guides | Yes — 2026-08-07 `[source]` | Documentation only | Optional, comes via KiBot |
| **Gingerbread.py** | SVG artwork → `.kicad_pcb`, Eurorack mounting-hole helpers | Yes — 2026-06-10 `[source]` | **The front panel** (E12), not the module board | **Look at this when the panel comes up** (§6) |
| **PCBFlow** | (the 2026 `NijoP/pcbflow`) LLM-driven EasyEDA/KiCad agent workflow, 7 stars, created 2026-07 `[source]` | New | — | No. Not the same category of thing |
| **PySpice** 1.5 | ngspice driver (the plan's new stage 2) | **No** — last pypi release 2021-05-15 `[source]` | — | Out of my slice, but flag it: five years stale |

---

## 2. What KiBot actually replaces, and what it does not

The brief asked whether KiBot replaces the last two stages wholesale. It
replaces more than that.

### It replaces

**Stage 8 (fab output), entirely.** `gerber`, `excellon`, `step`, `svg`,
`render_3d`, `compress` (the zip), `report`, `pcb_stats`, `netlist`,
`bom`, `position` are all output types
`[source: INTI-CMNB/KiBot@8a5106e (2026-07-28), kibot/out_*.py]`.

The important part is not that KiBot can run `kicad-cli`. It is the **fab
presets**: `JLCPCB`, `PCBWay`, `Elecrow`, `FusionPCB`, `P-Ban`, each with
stencil and with-THT variants, in
`kibot/resources/config_templates/` `[source]`. Read `PCBWay.kibot.yaml` and
count what the plan's two `kicad-cli` lines do not say:

```yaml
gerber_precision: 4.6
use_protel_extensions: true
disable_aperture_macros: true
subtract_mask_from_silk: false
inner_extension_pattern: '.gl%N'
exclude_edge_layer: true
exclude_pads_from_silkscreen: true
plot_sheet_reference: false
tent_vias: true
# excellon:
zeros_format: SUPPRESS_LEADING
left_digits: 2
right_digits: 4
metric_units: false
pth_and_npth_single_file: false
```

with a source comment pointing at a real OSH Park drill-format bug report
`[source: kibot/resources/config_templates/PCBWay.kibot.yaml, comment citing
docs.oshpark.com/design-tools/gerbv/fix-drill-format/]`. The plan's stage 8
says "the fab needs gerbers and drill. That is the whole order." That is true
and it is also exactly the sentence that precedes a rejected order, because
the *format* of the drill file is the thing fabs bounce. The plan cannot
currently state its own drill zero-suppression format; a KiBot preset is one
`import:` line.

**Stage 7's plumbing.** KiBot's `drc` preflight is a wrapper over the KiCad 8+
JSON DRC — the same thing the plan calls — but it also:

- **fixes the plan's own headless gotcha #2 for free**: its docstring reads
  "You need a valid *fp-lib-table* installed. If not KiBot will try to
  temporarily install the template."
  `[source: kibot/pre_drc.py:24-30]`. The plan spends a paragraph on copying
  `/usr/share/kicad/template/` by hand in `setup.sh`.
- parses the three JSON sections `violations`, `unconnected_items`,
  **`schematic_parity`** `[source: kibot/pre_drc.py:16]`, with severity
  counting and named filters for accepted exceptions. The plan's "five full
  iterations then stop" needs exactly this kind of filterable violation
  accounting to be usable.

**"Re-fill after *any* later change"** (stage 6). KiBot has a
`check_zone_fills` preflight — "Zones are filled before doing any operation
involving PCB layers. The original PCB remains unchanged"
`[source: kibot/pre_check_zone_fills.py]` — and a `CheckZoneFill` internal
template that diffs the on-disk board against the refilled one and **fails on
a threshold** `[source: kibot/resources/config_templates/CheckZoneFill.kibot.yaml]`.
That is the "did someone forget to refill" guard, written and maintained.

**"Diff the locked nets against their pre-route geometry"** (stage 5), *at
layer granularity*. `type: diff` with `old_type: git`, `diff_mode: stats`,
`threshold:` fails the build when copper moved more than N pixels between two
git refs `[source: kibot/out_diff.py:52-92]`, backed by `kidiff` 2.6.0.

### It does not replace

- **Anything before the board exists.** KiBot consumes a `.kicad_pcb`. Stages
  1–6 are untouched.
- **Placement.** Nothing replaces placement. See §7.
- **Routing.** No router, no DSN export.
- **Zone construction.** It fills zones; it does not *create* three-ground
  zones with priorities and a keepout. Stage 6 stays hand-rolled.
- **Net-level geometric assertions.** KiBot's diff is a rendered-layer image
  diff. "`AGND` tied exactly once", "locked nets geometrically unchanged",
  "decoupling cap within 2 mm of its pin", "no copper under the connector
  bore" are all *semantic* and belong in `verify.py`. That is the right
  hand-roll and the plan should keep it — it is the same argument
  `CLAUDE.md §4` makes about the staleness checker.

**Cost of adopting it:** `pip download kibot` succeeds from this sandbox —
`kibot-1.9.1-py3-none-any.whl`, 1.6 MB, no network-policy change `[test]`.
Runtime deps: `kiauto pyyaml xlsxwriter colorama requests qrcodegen markdown2
lark` `[source: kibot/__init__.py:9]`. Same install channel the plan already
verified for SKiDL.

---

## 3. Four things in the stack table that are wrong

### 3.1 `Freerouting 2.x … Java 21 already present` — **false, and it fails hard**

`[test]`, reproduced in full:

```
$ java -version
openjdk version "21.0.10" 2026-01-20

$ curl -L -o fr.jar https://github.com/freerouting/freerouting/releases/download/v2.4.1/freerouting-2.4.1.jar
   (200, 64,076,787 bytes)

$ java -jar fr.jar -help
Error: LinkageError occurred while loading main class app.freerouting.Freerouting
  java.lang.UnsupportedClassVersionError: app/freerouting/Freerouting has been
  compiled by a more recent version of the Java Runtime (class file version 69.0),
  this version of the Java Runtime only recognizes class file versions up to 65.0
```

Class file 69 is Java 25. The jar's own manifest says
`Created-By: 25.0.4.1 (Eclipse Adoptium 25.0.4.1+1-LTS)`, `Build-Date:
2026-09-03` `[test]`. It is not an accident:
`build.gradle:27-32` pins `sourceCompatibility = JavaVersion.VERSION_25`,
`targetCompatibility = VERSION_25`, `languageVersion = of(25)`, and every
release workflow uses `java-version: '25'`
`[source: freerouting/freerouting@97758b5 (2026-09-19)]`. The README's install
step says "Choose version `25`".

And **`adoptium.net` is blocked from here** — `api.adoptium.net` returns
`CONNECT tunnel failed, response 403` `[test]`. So the plan's Freerouting row
is not installable as written, and the obvious fix is behind the same wall as
the KiCad PPA.

Two remedies, both verified:

1. **Pin Freerouting 1.9.0.** Its jar is class file major 61 (Java 17), 5.0 MB,
   and it starts under the Java 21 that is already here `[test]`.
2. **Use the official container.** `ghcr.io/freerouting/freerouting:latest`
   manifest returns HTTP 200 with an anonymous ghcr token, and `docker` is on
   the PATH `[test]`. The image is `eclipse-temurin:25-jre-jammy`
   `[source: freerouting/Dockerfile]`.

### 3.2 `xvfb` for Freerouting — **right for 1.9.0, wrong for 2.x, and the plan has one foot in each**

The plan says "Two things still want OpenGL: `kicad-cli pcb render` and,
depending on version, Freerouting. Run both under `xvfb-run -a`." Then stage 5
hard-codes `xvfb-run -a java -jar freerouting.jar`.

`[test]` — Freerouting **1.9.0** under Java 21 with no `DISPLAY`:

```
2026-09-21 17:18:47 [main] INFO  Freerouting v1.9.0 (build-date: 2023-10-30)
2026-09-21 17:18:47 [main] ERROR No X11 DISPLAY variable was set...
java.awt.HeadlessException
  at sun.awt.HeadlessToolkit.getScreenSize(HeadlessToolkit.java:186)
  at app.freerouting.gui.MainApplication.main(MainApplication.java:269)
```

It calls `getScreenSize()` before it looks at its arguments. xvfb is
mandatory, always, even for `-help`.

Freerouting **2.x** is the opposite: `--gui.enabled=false` is the documented
headless switch `[source: docs/settings.md:120, docs/self-hosting.md:268
"Required for headless/server operation"]`, and the official Dockerfile
installs **no X11 or GL packages at all** — it is a bare `25-jre-jammy` with
one jar `[source: freerouting/Dockerfile]`.

So the two halves of the plan describe two different Freerouting versions and
neither combination exists. **Pick one and say which**, because the choice
changes `setup.sh` (xvfb or not), the Java requirement, and the CLI.

### 3.3 `kiutils 1.4.8` — **abandoned, and it predates the file formats it is asked to write**

- Last pypi release **2024-02-02**; 1.4.8 is still the latest `[source: pypi.org/pypi/kiutils/json]`.
- Last commit on master **2024-05-02** `[source: mvnmgrx/kiutils]`.
- README: "KiCad file parser … for KiCad **6.0 and up**" `[source: README.md:10]`.

KiCad 8 shipped in Feb 2024, KiCad 9 in 2025, KiCad 10 by mid-2026 (§3.5).
kiutils has seen none of them. The plan gives it a load-bearing job —
"Reads/writes `.kicad_sch` and `.kicad_pcb` S-expressions where `pcbnew`
won't" — and then names it again as the way to render a human-readable
schematic. Both uses should go:

- **Schematic rendering is SKiDL's job, not kiutils'.** SKiDL 2.2.2 (2026-04-03)
  "Schematic generation added for KiCad 6, 7, 8 and 9", and 2.3.0 is largely a
  schematic-generation release — hierarchical UUIDs, multi-unit references,
  net-label deconfliction, a tool-agnostic `SchematicBackend`
  `[source: devbisme/skidl HISTORY.md, 2.3.0 (2026-07-28)]`. The API is
  `Circuit.generate_schematic()` `[source: src/skidl/circuit.py:1274]`.
  kiutils cannot do this at all — it is a parser, not a renderer.
- **Therefore the plan does not have to lose `--schematic-parity`.** It says
  "You lose `--schematic-parity`, because there is no `.kicad_sch`." There can
  be one, generated from the same SKiDL source, for free. Then KiCad's own
  schematic-parity check runs, *and* the plan's stronger Python netlist
  equality assertion runs, and the two disagreeing is itself a finding. The
  plan's replacement is better than parity; it is not a reason to decline
  parity.

### 3.4 The SWIG `pcbnew` API is on a published removal path

From the official KiCad bindings package, verbatim:

> "The KiCad IPC API replaces the legacy SWIG-based Python bindings for
> KiCad's PCB editor. **The SWIG bindings still exist in KiCad 9 and 10, but
> are removed in KiCad 11.**"
>
> "Unlike the SWIG-based Python bindings, the IPC API requires communication
> with a running instance of KiCad. **It is not possible to use `kicad-python`
> to manipulate KiCad design files without KiCad running.**"

`[source: pypi.org/pypi/kicad-python 0.8.0, uploaded 2026-08-30; repository
gitlab.com/kicad/code/kicad-python]`

This is the single most consequential fact for the plan's architecture, and
the plan does not know it. Stages 3, 5 and 6 — `build_board.py`, the Specctra
round trip, `ZONE_FILLER` — are the most custom code in the pipeline and they
all sit on `pcbnew` SWIG. Its replacement is *less* headless, not more: it
needs a KiCad GUI session with the API server switched on in Preferences.

I am **not** recommending kicad-python. I am recommending the conclusion that
follows: **minimise the SWIG surface.** Every pcbnew call written by hand is
a call that has to be rewritten, and there is no headless successor to rewrite
it into. This is a direct argument for putting stages 7 and 8 behind KiBot
(KiBot absorbs that migration on the maintainer's schedule, not yours) and
for using `kinet2pcb` rather than hand-writing footprint loading (§5).

### 3.5 Smaller: "KiCad 9" is a pin, not the current version

KiBot 1.9.1 has a `Dockerfile_k10` on `ghcr.io/inti-cmnb/kicad10_auto_full`,
a `NEEDS_K9`/`version_k10` dependency matrix, and ~20 KiCad-10-specific
changelog entries `[source: kibot/Dockerfile_k10, kibot/out_netlist.py:33,
CHANGELOG.md]`. SKiDL 2.3.0 added a `KICAD10` tool identifier
`[source: HISTORY.md]`. Two independent projects, so KiCad 10 is out.

Pinning 9 is defensible — SKiDL's `kicad9` backend has a year more mileage
than `kicad10`. But the plan should say *"we pin 9 because …"*, not imply 9 is
the head. `config/figures.yaml` exists for exactly this class of statement.

### 3.6 Smaller: the PPA is currently blocked and the container is not

The plan calls the KiCad PPA "the one hard network requirement". Today:

- `ppa.launchpadcontent.net:443` → `connect_rejected` by the egress proxy `[test]`
- `ghcr.io/v2/inti-cmnb/kicad9_auto_full:latest` → **HTTP 200**, anonymous token `[test]`
- same for `kicad10_auto_full` and `kicad9_auto` `[test]`
- `docker` is at `/usr/bin/docker` `[test]`

So there is a second route that works right now and needs no allowlist change.
`kicad9_auto_full` is the base image KiBot's own `Dockerfile_k9` builds `FROM`
`[source: kibot/Dockerfile_k9]` — it carries KiCad 9, KiAuto, libraries and
the `fp-lib-table` templates already set up. I have not pulled the image (it
is large and this sandbox was at 100% disk twice during this review), so I
have **not** verified that it runs here — only that it is fetchable. Flagging
the route, not certifying it.

---

## 4. atopile: a hard look, and a clear no

The brief asked for one. atopile is the most serious circuits-as-code project
in existence and it is still the wrong tool here, for four independent
reasons, any one of which is disqualifying.

1. **`requires-python = ">=3.14,<3.15"`** `[source: pypi.org/pypi/atopile 0.15.9;
   also pyproject.toml:16 at v0.14]`. That collides head-on with the plan's own
   first headless gotcha: "`pcbnew` is built against the system interpreter …
   A venv will not see it." You cannot have a Python-3.14-only compiler and a
   system-`pcbnew` interpreter be the same interpreter. This is not a packaging
   inconvenience; it is two mutually exclusive constraints in one pipeline.
2. **It does not route, and its layout step is not headless.** The build
   targets are `bom`, `mfg-data`, `step`, `3d-image`, `manifest`, `datasheets`,
   `power-tree`, `variable-report`, `update-pcb`, `post-pcb-checks` — there is
   no route target `[source: atopile/atopile@619eda7, src/atopile/build_steps.py
   muster registrations]`. The README's own pipeline says "Layout — place and
   route in KiCad" and "Open layout when ready". atopile *syncs a netlist into*
   a `.kicad_pcb` you draw by hand. The plan's whole point is that nothing is
   drawn by hand.
3. **Its headline feature is the one this project must not use.** "Automatic
   parametric picking of discrete components", served by a remote components
   API (`config.project.services.components.url`, plus an LCSC picker)
   `[source: src/faebryk/libs/picker/api/api.py:52]`, with anonymous telemetry
   to `telemetry.atopileapi.com` on by default
   `[source: src/atopile/telemetry.py:72]`. Woody's parts are chosen,
   justified in `hardware/bom.csv`, and their datasheets are banked with
   SHA-256s. A cloud service that substitutes a part because it solves a
   tolerance constraint is the precise inverse of `CLAUDE.md §3`.
4. **The public source has fallen behind the shipped compiler.** pypi is at
   0.15.9 (2026-09-12) and healthy. GitHub `main` tip is **2026-03-11** and the
   tag list stops at `v0.14.x` `[source: git ls-remote + depth-1 clone of
   atopile/atopile, 2026-09-21]`. An MIT sdist for 0.15.9 does exist (95 MB,
   and the compiler core is now Zig — `.zigversion`, a `pyzig` build skill
   `[source: sdist listing]`). It is probably fine. It is also not the "every
   script in the repo, re-runnable forever" story the plan is buying.

Same verdict, shorter, for the rest: **faebryk** is now a subdirectory of
atopile, not a project. **tscircuit** is genuinely excellent and genuinely
growing (2,689 stars, commits today) but it is TypeScript/React with its own
board model, its own autorouter that speaks `SimpleRouteJson` not DSN, and a
JLCPCB-parts orientation; the KiCad bridge is four separate low-star repos.
**edea** and **PCBFlow** are not contenders.

---

## 5. What the plan should hand-roll less of

**`build_board.py` is mostly already written.** `Circuit.generate_pcb()` →
`kinet2pcb` loads each footprint with `pcbnew.FootprintLoad`, resolves the
library through `fp-lib-table`, and assigns every pad to its net — 495 lines,
MIT, maintained `[source: devbisme/kinet2pcb@HEAD (2025-11-03),
kinet2pcb/kinet2pcb.py:281-330; called from
skidl/src/skidl/tools/kicad9/gen_pcb.py:32-39]`. It does **not** place
anything. So `build_board.py` should shrink to what is genuinely this board's
problem: `Edge.Cuts` outline, placement, net classes, `.kicad_dru`.

**Freerouting's modern CLI is better than the plan's invocation**, if 2.x is
chosen:

- `-mp` is legacy. Canonical is `--router.autorouter.max_passes`; the flat keys
  "still apply and warn until they are removed"
  `[source: docs/settings.md, router.autorouter]`.
- `--router.result_json=<path>` writes a machine-readable routing manifest at
  the end of a headless `-de`/`-do` run `[source: docs/settings.md]`. That is
  a structured pass/fail for the plan's "zero unrouted" assertion instead of
  scraping a log.
- `-drc <file>` writes a DRC report **in KiCad's own JSON DRC schema**
  `[source: docs/command_line_arguments.md]` — parseable by the same code that
  reads `kicad-cli pcb drc`.
- `-inc GND,VCC` skips whole net classes. Worth pairing with locking for
  `AGND`/`BREATH`: belt and braces, and it does not depend on the `(wiring …)`
  protected round trip the plan is (rightly) planning to smoke-test.
- **`plane_as_obstacle` defaults to `false`** — "foreign traces may route
  through fills" `[source: docs/settings.md]`. With `PWR_GND` and `DIG_GND` as
  separate zones (stage 6), a default-configured router will happily run a
  signal across a ground pour. Set it.

---

## 6. What the plan is right to hand-roll

State this in the document, so the next reviewer does not re-litigate it.

1. **The SKiDL transcription.** No tool does what stage 1 does. The argument
   in "The architectural choice" is correct and survives this review intact.
2. **Placement.** Nobody automates it — not KiBot, not atopile, not tscircuit
   for anything analog. Five iterations then stop is as good as it gets.
3. **Stage 6's three-ground zone topology.** Zone priorities, an `AGND` keepout,
   thermal reliefs on THT pads because the board is hand-soldered. No
   declarative tool expresses this. `pcbnew` + a script is the answer.
4. **The semantic half of `verify.py`.** Net identity, `AGND` tied exactly
   once, decoupling-cap distance, locked-net geometry, no copper under the
   bore. This is the PCB equivalent of `CLAUDE.md §4` — the checker greps, the
   review thinks — and it is the highest-value code in the pipeline.
5. **The three-BOM split and `check-bom-parity.py`.** KiBot generates a BOM
   from the board; it has no opinion about why a part was chosen or that the
   sensor is bought in twos. Keep all three, keep the parity check.
6. **The two-resistor smoke board.** Excellent, and no tool supplies it. Given
   §3.1 and §3.2, add one more thing it must prove: *which Freerouting jar
   starts at all, under which JVM, with or without a display.* That is a
   five-second check that would have caught a stack-table error.

---

## 7. What real open-hardware projects actually do — and it is less than this

This is the most uncomfortable finding, so take it plainly.

**Winterbloom** (wntrblm) makes precision analog Eurorack — Helium is "a triple
1-to-3 precision buffered multiple and 3-to-1 precision adder", about as close
a cousin to this module as exists in public. Their hardware CI is **nothing**:

- `wntrblm/Helium` @ 2025-04-18: `.github/workflows/` contains **only**
  `docs.yml`. `hardware/board/` holds `board.kicad_pcb`, `board.kicad_sch`,
  `board.pdf` and a committed `gerbers.zip` `[source]`.
- `wntrblm/Neptune` @ 2025-01-30: only `docs.yml` `[source]`.
- `wntrblm/Castor_and_Pollux` @ 2025-09-22, 586 stars: `build.yml` is
  **firmware only** `[source]`.

The one thing they *do* generate programmatically is the **front panel**:
`hardware/faceplate/generate.py`, 71 lines, `gingerbread.convert` from an SVG
plus `gingerbread_helpers.add_eurorack_mounting_holes(pcb)`
`[source: Helium/hardware/faceplate/generate.py]`. That is production prior art
for generating a board from code — and it is the panel, not the circuit board.
**It is directly relevant to E12's panel** and the plan should look at
Gingerbread.py when it gets there.

`luftaquila/monolith` @ 2026-07-03 has a workflow literally named "Build PCB"
on `ppa:kicad/kicad-9.0-releases`. Read what it does: it exports SVGs and a
STEP for the README, then
`cp -r device/hardware/monolith/jlcpcb/production_files kicad/gerbers`
`[source: .github/workflows/pcb.yml]`. The gerbers were made in the GUI and
committed. The CI is a documentation renderer wearing a fab-output costume.

So: **the plan is attempting something more ambitious than the field does.**
That is not a reason to stop — repeatability is a legitimate goal and the
project's stated failure mode is exactly the kind a generated pipeline
prevents. It *is* a reason to (a) expect to be the first person to hit each
bug, and (b) refuse to also hand-roll the parts that *are* solved.

### The counter-example, which is the one to copy

**`BleepSound/ms20-vcf-double`** @ 2025-11-27 — an MS-20 filter, a
multi-board synth-DIY project (circuit board + jack board + front panel), one
person, **no CI server**, and a `.kibot/` directory of configs run from a
shell `[source]`. This is Woody's situation exactly, and it is KiBot. The
configs are split the way the plan's stages are:
`config_fab_circuit`, `config_fab_jack`, `config_fab_front`,
`config_bom_circuit`, `config_bom_jack`, `config_doc_global`.

And the counter-counter-example: **`VIPQualityPost/lemon-pepper-stepper`**
@ 2025-12-24 is the hand-rolled `kicad-cli` approach in the KiCad 9 era, and
it shows the bill — two bespoke `jlc_bom_formatter.py` / `jlc_cpl_formatter.py`
scripts, the same six `kicad-cli` invocations duplicated across
`design.yml` and `documentation.yml` with the layer lists already drifted
between them, and a layer string ending `Edge.Cuts,"--erd` where a space went
missing `[source: .github/workflows/documentation.yml]`. That is what stage 8
looks like after a year. It is also, precisely, this repo's named failure
mode — one fact, two files, drifted.

---

## 8. Recommendation

**Stack: KiCad 9 (pinned, stated as a pin) + SKiDL 2.3.0 + `kinet2pcb` +
Freerouting (version *decided*, see §3.1) + KiBot 1.9.1 + a small custom
`verify.py`. Drop `kiutils`.**

Stage by stage against the current document:

| Stage | Now | Should be |
|---|---|---|
| 1. Netlist | SKiDL | **Unchanged.** Also emit `generate_schematic()` → restores schematic parity (§3.3) |
| 2. Simulate | ngspice + PySpice 1.5 | Out of slice — but PySpice's last release is 2021-05-15 `[source]`. Somebody should check that |
| 3. Board bring-up | hand-written `build_board.py` | `Circuit.generate_pcb()` / `kinet2pcb` for footprints+nets; hand-roll only outline, placement, net classes, `.kicad_dru` |
| 4. Hand-route + lock | by hand | **Unchanged.** Add Freerouting `-inc` on the analog classes as a second guard |
| 5. Autoroute | `xvfb-run java -jar … -mp 100` | Pick a version. 1.9.0 + xvfb + Java 21, **or** 2.4.1 via `ghcr.io/freerouting/freerouting` + `--gui.enabled=false` + no xvfb. Use `--router.result_json` |
| 6. Pour | `pcbnew.ZONE_FILLER` | **Unchanged** — correctly hand-rolled. Add KiBot `check_zone_fills` as the "did you refill" guard. Set `plane_as_obstacle: true` on the router |
| 7. Verify | `kicad-cli pcb drc` + `verify.py` | KiBot `drc` + `erc` preflights (filters, severity counting, fp-lib-table handled) **+** `verify.py` reduced to the semantic assertions |
| 8. Fab output | five `kicad-cli` lines | **One KiBot YAML importing a fab preset.** Delete `export.py` |
| Zip | implied | KiBot `compress` |
| Generated BOM | "from the SKiDL netlist" | KiBot `bom` (and keep `check-bom-parity.py` against `hardware/bom.csv`) |

Rough shape of the trade: the plan's `verify.py` + `export.py` are on course
for several hundred lines of `kicad-cli` argument plumbing. KiBot turns that
into perhaps 60 lines of YAML plus the semantic assertions that were always
going to be custom. For a one-off build with no team, that is the right
direction — **fewer lines the owner has to remember the reasoning for in
eighteen months**, which is what this repo is actually optimising for.

**The honest counter-argument**, since the brief asked me not to recommend
heavyweight tooling for a one-off: KiBot is a 1.6 MB wheel with eight
dependencies and a large configuration surface, brought in to run maybe six
outputs. If the owner only ever wants gerbers and drill for one fab house, six
lines of `kicad-cli` really is enough. I still say adopt it, because the six
lines are not the risk — the *options on* the six lines are, the plan cannot
currently state them, and a rejected fab order on a board you can only afford
to spin once costs more than a dependency.

---

## 9. Real-world configs worth copying

1. **`BleepSound/ms20-vcf-double`** — `.kibot/config_fab_circuit.kibot.yaml`,
   `config_fab_jack`, `config_fab_front`, `config_doc_global`. Synth-DIY,
   multi-board, one person, no CI server. The closest match to this project.
   `[source: @HEAD 2025-11-27]`
2. **KiBot's own fab presets** — `kibot/resources/config_templates/`:
   `PCBWay.kibot.yaml`, `JLCPCB.kibot.yaml`, `Elecrow`, `FusionPCB`, `P-Ban`.
   Copy the one matching the fab, or `import:` it. `[source: INTI-CMNB/KiBot@8a5106e]`
3. **`kibot/resources/config_templates/CheckZoneFill.kibot.yaml`** — the
   "committed board needs a zone refill" guard, ~30 lines. `[source: same]`
4. **`RonMcKay/capacitive-soil-moisture-sensor`** — `.kibot/production.kibot.yaml`
   plus `.kibot/includes/`. A clean example of splitting one config into
   preflight / fab / docs with `import:`, and of injecting `git describe` into
   the board's text variables so the silkscreen version cannot drift from the
   tag. `[source: @HEAD 2023-11-26 — older, KiCad 6/7 era; copy the structure,
   not the options]`
5. **`wntrblm/Helium` → `hardware/faceplate/generate.py`** + **`wntrblm/Gingerbread.py`**
   — production prior art for generating a Eurorack front panel from SVG,
   including `add_eurorack_mounting_holes`. For E12's panel.
   `[source: Helium @2025-04-18; Gingerbread.py @2026-06-10]`
6. **`VIPQualityPost/lemon-pepper-stepper`** — read `.github/workflows/design.yml`
   and `documentation.yml` as a *warning*, not a template: it is the
   hand-rolled `kicad-cli` end state, already drifted between two files.
   `[source: @HEAD 2025-12-24]`

---

## 10. What I did not check

Stated so nobody files this as covered.

- I did not run KiCad, KiBot, SKiDL or `kinet2pcb`. KiCad is not installed here
  and the PPA is blocked `[test]`. Everything about KiBot's *behaviour* is read
  from its source and templates, not observed.
- I did not pull `ghcr.io/inti-cmnb/kicad9_auto_full`. I verified the manifest
  is fetchable (HTTP 200) and that `docker` exists; I did not verify the image
  runs in this sandbox.
- I could not read Freerouting's DSN parser to confirm it honours
  `(wiring … (type protect))`. My clone's git index was truncated by a
  disk-full condition and `src/` was not materialised. **The plan's instinct to
  prove the locked-track round trip on the two-resistor board is therefore
  unrefuted and should be treated as mandatory.**
- GitHub's REST API is gated in this session, so release *dates* came from tag
  lists, jar manifests and pypi rather than the releases endpoint.
- I did not audit atopile 0.15.9's actual source — only its 0.14 tree on
  GitHub plus 0.15.9's pypi metadata and sdist file listing. The four reasons
  in §4 all rest on metadata or on the 0.14 tree; if someone wants to overturn
  the verdict, that is where to dig.
