# P5 — SKiDL, and whether circuit-as-code actually works

**Slice:** the central architectural choice in `docs/reference/pcb-pipeline.md` —
do not parse the ASCII schematics, transcribe them into SKiDL modules instead.

**Method:** cold. Prior review directories not read. SKiDL 2.3.0 cloned from
`github.com/devbisme/skidl` and installed from PyPI into a clean venv on a
machine with **no KiCad installed**; every claim below that is marked `[test]`
is backed by command output reproduced here. KiCad 9 behaviour read from
`gitlab.com/kicad/code/kicad` at ref `9.0`.

Provenance on every claim: `[source]` = read in a repo, `[test]` = I ran it,
`[calc]` = arithmetic shown, `[from memory]` = unverified.

**Bottom line:** the architectural choice survives. Every predicted breaking
point is false. But the *justification given for it* contains three claims that
are wrong, and there are four failure modes on a board like this one that the
plan does not mention and that will bite in exactly this project's named way —
silently, with a green build.

---

## 1. Verdict table

| # | Claim under test | Verdict | Evidence |
|---|---|---|---|
| 1 | SKiDL 2.3.0 is current and maintained | **TRUE** | Released 2026-07-28; last commit 2026-08-10. 466/486 unit tests pass here, all 20 failures from absent KiCad libs / `netlistsvg` binary, none code defects `[test]` |
| 2 | Breaks on KiCad 9 symbol format | **FALSE — falsified** | Parsed real `Amplifier_Operational.kicad_sym` v20241209 from `kicad-symbols` 9.0.0, multi-unit TL072, uA/uB/uC `[test]` |
| 3 | Needs KiCad installed | **FALSE** | Full ERC + netlist + `.kicad_sch` generated with no KiCad on the box `[test]`. Only `generate_pcb()` needs it |
| 4 | Needs symbol libraries at all | **FALSE** | Ad-hoc `Part(..., tool=SKIDL, pins=[...])` needs no library `[test]` |
| 5 | Netlist importable by KiCad 9 | **TRUE** | KiCad 9 reader ignores the version field outright `[source]` |
| 6 | Has a working `ERC()` | **TRUE but far weaker than the plan assumes** | See §4 |
| 7 | "Fail the build on any ERC error" works as written | **FALSE — defect** | Script exits **0** with 1 ERC error + 4 footprint errors, and writes the netlist anyway `[test]` |
| 8 | Output is deterministic across runs | **FALSE by default, TRUE if disciplined** | 32-line diff between two identical runs; 0-line diff once every part carries `tag=` `[test]` |
| 9 | Refdes are stable | **FALSE — defect** | Inserting one part renumbers every part after it `[test]` |
| 10 | "You lose `--schematic-parity`, because there is no `.kicad_sch`" | **FALSE — the plan is out of date** | `generate_schematic()` exists and emitted a valid 20 KB `.kicad_sch` `[test]`. It is however non-deterministic, so it cannot serve as the parity artifact |
| 11 | Handles op-amp sections, trimmers, gang pots, odd connectors | **TRUE** | Multi-unit emits one `U1` with all 8 pins `[test]`; the rest are ad-hoc pin lists |
| 12 | Footprint assignment is checked | **PARTLY — presence yes, validity no** | Missing footprint = error; `"NotAReal:Footprint_Xyzzy"` passes through verbatim `[test]` |
| 13 | `check-bom-parity.py` can diff design BOM against netlist "by refdes" | **FALSE — impossible as specified** | `hardware/bom.csv` has no refdes. See §6 |
| 14 | Net names are namespaced by hierarchy | **FALSE — defect** | Nets are one flat global namespace; hierarchy only affects sheetpath `[test]` |

---

## 2. Does SKiDL work without KiCad, and with KiCad 9 libraries?

**Yes to both. Definitively. This is the plan's one genuinely load-bearing
assumption and it holds.**

### No KiCad on the machine

```
$ which kicad-cli kicad; ls /usr/share/kicad
ls: cannot access '/usr/share/kicad': No such file or directory
$ ./v1/bin/pip list | grep -iE 'skidl|kiutils'
kinet2pcb       1.1.4
kiutils         1.4.8
skidl           2.3.0
```
`[test]`

A five-component in-amp front end, every part declared ad hoc with no library:

```
ERC INFO: 7 warnings found while running ERC.
ERC INFO: 0 errors found while running ERC.
=== NETLIST ===
(export
  (version "D")
  (design (source "t2.py") (tool "SKiDL (2.3.0)")
```
`[test]`

Startup prints six `KICAD*_SYMBOL_DIR environment variable is missing` warnings
and five `fp-lib-table file was not found`. **These are noise, not errors** —
everything downstream worked. They will be mistaken for the cause of the first
real failure; suppress them deliberately rather than learning to ignore them.

The only SKiDL entry point that needs KiCad is `generate_pcb()`, which goes
through `kinet2pcb`:

```
$ ./v1/bin/python -c "import kinet2pcb"
ModuleNotFoundError: No module named 'pcbnew'
```
`[test]`

The plan does not use `generate_pcb()` — stage 2 is a hand-written
`build_board.py` against `pcbnew` — so this costs nothing. Worth stating
explicitly in the doc, because `generate_pcb()` is the obvious thing to reach
for and it is the one door that is locked.

### KiCad 9 symbol libraries

The slice brief flagged this as the likely breaking point. It is not.

SKiDL 2.3.0 ships **eight** tool backends: `kicad5 … kicad10`, plus `skidl` and
`spice` `[source: src/skidl/tools/]`. `lib_suffix = [".kicad_sym"]` for the
KiCad 6+ backends `[source: tools/kicad9/lib.py]`.

Fetching the real library from `gitlab.com/kicad/libraries/kicad-symbols` at tag
`9.0.0` (`(version 20241209)`) and parsing it:

```
PART OK: TL072 | ref_prefix: U | datasheet: http://www.ti.com/lit/ds/symlink/tl071.pdf
NUM UNITS: 3 ['uA', 'uB', 'uC']
  UNIT uA [('1', ''), ('3', '+'), ('2', '-')]
  UNIT uB [('5', '+'), ('7', ''), ('6', '-')]
  UNIT uC [('4', 'V-'), ('8', 'V+')]
```
`[test]`

Correct: both amplifier sections plus the shared power unit. Used in anger, both
halves emit as a **single** `U1` carrying all eight pins `[test]` — the thing
that actually matters for a board with six dual op-amps.

**Revise the plan's stack table.** It pins KiCad 9, but SKiDL's default tool is
`kicad10`, not `kicad9` `[test: get_default_tool() → 'kicad10']`. This turns out
to be harmless for the netlist:

```
$ diff tools/kicad9/gen_netlist.py tools/kicad10/gen_netlist.py
$ echo $?
0
```
`[source]` — the two netlist generators are byte-identical. But relying on that
by accident is not the same as choosing it. **Call `set_default_tool(KICAD9)`
explicitly at the top of every module** so the backend is a stated fact rather
than a default that can move under you in 2.4.0.

### Is the netlist importable by KiCad 9?

Yes, and for a stronger reason than compatibility. KiCad 9's netlist reader:

```cpp
case T_version:  // The netlist starts here.
    // version id not yet used: read it but does not use it
    NextTok();
    NeedRIGHT();
    break;
```
`[source: pcbnew/netlist_reader/kicad_netlist_reader.cpp:100]`

The `(version "D")` string SKiDL writes is **read and discarded**. There is no
version negotiation to fail. The parser then reads `comp`, `sheetpath`,
`tstamps` and `nets` — all of which SKiDL emits `[source, test]`.

---

## 3. Determinism — the plan's "re-runnable forever" claim

**Not true out of the box.** Two runs of an unchanged script:

```
$ diff <(grep -v '(date ' run1.net) <(grep -v '(date ' run2.net)
57c57
<           (name "SKiDL Tag") "BzEPeWJ_B4")
>           (name "SKiDL Tag") "cRhe3ZWJF4")
67c67
<       (tstamps "b9f7a8fb-9683-5c57-b924-548ab87fbccc"))
>       (tstamps "17780d9b-7c26-5845-838b-da97301a5c19"))
[... 32 lines total]
```
`[test]`

Cause, from source:

```python
part_tstamp = str(uuid.uuid5(namespace_uuid, part.hiername))
```
`[source: tools/kicad9/gen_netlist.py:62]`

`uuid5` is deterministic — the *input* is not. `hiername` ends in `tag_ref_name`,
which is `tag or ref or name` `[source: part.py:1154,1180]`, and when no tag is
set SKiDL invents one:

```python
chars = string.ascii_letters + string.digits + "_"
self.tag = ''.join(random.choices(chars, k=length))
```
`[source: skidlbaseobj.py:267-269]`

It does warn — `Missing tag on AD8422 instantiated at t2.py:13` — but on a
149-part board that is 149 warnings nobody reads.

**The fix works and is cheap.** Give every part an explicit `tag=`:

```
$ diff <(grep -v '(date ' tag1.net) <(grep -v '(date ' tagged.net); echo $?
0
```
`[test]` — byte-identical apart from the `(date …)` stamp, which is wall-clock
and must be stripped before any diff.

### Why it matters less than it looks, and more than it looks

Less: KiCad 9 matches netlist components to board footprints **by reference, not
by timestamp**, by default — `m_lookupByTimestamp = false`
`[source: board_netlist_updater.cpp:60]`. Unstable tstamps therefore do **not**
cause footprints to be deleted and re-added, and routing is not lost.

More: the updater still rewrites the path and marks the board dirty —

```cpp
if( aPcbFootprint->GetPath() != new_path ) { … changed = true; aPcbFootprint->SetPath( new_path ); }
```
`[source: board_netlist_updater.cpp:451-469]`

— so every re-run produces a spurious `.kicad_pcb` diff on all 149 parts. That
destroys the review property the plan is buying the whole architecture for: *a
change to a page shows up as a code diff*. If the generated artifacts churn
unconditionally, nobody can see the one line that mattered.

### Refdes are worse than tstamps

```
BASELINE:                 RIN->R1  RFB->R2  RGAIN->R3  RLOAD->R4
AFTER INSERTING ONE PART: RIN->R1  RNEW->R2  RFB->R3   RGAIN->R4  RLOAD->R5
```
`[test]`

Adding one resistor renumbers every part after it. Combined with
reference-based matching above, a re-run after an insertion hands **every
downstream footprint the wrong netlist entry** — silently, because `R3` exists
in both and is simply now a different resistor. On a routed board this is a
quiet, total corruption.

`ref=` is honoured when set explicitly `[test: EXPLICIT REF: U7]`. So the rule
is: **every part carries both an explicit `ref=` and an explicit `tag=`.** Not
one or the other. `tag` pins the tstamp; `ref` pins the refdes.

### `generate_schematic()` is not a parity artifact

Two identical runs: **445 diff lines**, including component coordinates moving
(`(at 144.78 90.17 180)` → `(at 135.89 90.17 180)`) `[test]`. It also emits
`(version 20230409)` — a KiCad 7-era stamp — where KiCad 9's own constant is
`SEXPR_SCHEMATIC_FILE_VERSION 20250114` `[source: eeschema/sch_file_versions.h]`.
And it ignores `file_=`, writing to a filename derived from the script
(`./t9.kicad_sch`) `[test]`. Its placer warned `Routing failed on attempt 1/2,
expanding area by 1.5x` on a circuit with **one** op-amp `[test]`.

So: **correct the plan's claim that there is no `.kicad_sch`** — there can be
one, for human review, which is a real gain. But **do not** restore
`--schematic-parity` through it. The plan's replacement (assert board netlist ==
SKiDL netlist in Python) remains the right call, and is now better justified
than the doc justifies it.

---

## 4. What `ERC()` actually catches — much less than stage 1 assumes

Read the implementation, then test it. `dflt_net_erc` and `dflt_part_erc` call
`active_logger.warning` for **every** condition: unconnected pin, no-pin net,
single-pin net, no drivers, insufficient drive
`[source: erc.py:76,108,111,127,131]`. The only `error` path is a pin-type
conflict `[source: pin.py:798]`, and the conflict matrix marks just a handful of
pairs as `ERROR` — `OUTPUT/OUTPUT`, `PWROUT/OUTPUT`, `PWROUT/TRISTATE`; almost
everything else is `WARNING` or `OK`, with `OK` the default for unlisted pairs
`[source: pin.py:1023-1041]`.

Tested against four deliberate defects on a passive-heavy analog circuit:

| Defect planted | Caught? |
|---|---|
| Two op-amp outputs shorted together | **ERROR** — caught |
| Resistor value `"banana"` where the page says `10k0 0.1%` | no |
| Footprint `"NotAReal:Footprint_Xyzzy"` | no — written verbatim into the netlist |
| `AGND` and `PWR_GND` aliased to the same net object (ADR 0004 star rule) | no |

```
ERC ERROR: Pin conflict on net SHORTED_OUTS, OUTPUT pin 1/OUT of TL072/U1 <==> OUTPUT pin 1/OUT of TL072/U2
ERC INFO: 24 warnings found while running ERC.
ERC INFO: 1 errors found while running ERC.
```
`[test]`

One error, twenty-four warnings, three of the four defects through. And note
`(value "banana")` and `(footprint "NotAReal:Footprint_Xyzzy")` both appear in
the emitted netlist `[test]`.

The signal-to-noise problem is structural: 24 warnings for a 4-part circuit
scales to several hundred on 149 parts, and the warnings that matter look
exactly like the ones that don't.

**This board makes it worse.** Roughly 40 of the 61 module BOM rows are R, C, D,
FB, trimmers, pots and connectors. Declared ad hoc they will be `PASSIVE`, and
`PASSIVE`/`PASSIVE` is `OK` in the conflict matrix `[source]`. **ERC is close to
inert on the majority of this board.** It will catch a shorted op-amp output. It
will not catch a resistor on the wrong node — which, going by
`breath-receive-stage.md`, is the defect class this project actually produces.

### And stage 1 does not fail the build

```
$ ./v1/bin/python t4.py >/dev/null 2>&1; echo "EXIT: $?"
EXIT: 0
$ grep -c 'comp' defects.net
12
```
`[test]`

One ERC error and four `No footprint for …` errors, and the process exits **0**
having written a complete netlist. `python3 module.py && next_stage` proceeds
happily onto a broken netlist.

**Concrete fix for stage 1.** Not optional:

```python
import skidl, sys
ERC()
if skidl.erc_logger.error.count:
    sys.exit(1)
generate_netlist(file_="module.net")
if skidl.default_circuit.no_files or skidl.active_logger.error.count:
    sys.exit(1)
```
`skidl.erc_logger.error.count` and `.warning.count` are readable and correct
`[test: errors: 1 warnings: 24]`. Also **ratchet the warning count** — store the
expected number and fail if it rises. A warning count that only goes down is the
only way a warning-only checker stays useful.

---

## 5. The four things that will actually bite on this board

These are ordered by how quietly they fail.

### 5.1 Global rails split silently — the worst one

The plan's structure is six modules, one per schematic page, imported by
`module.py`. That structure walks straight into this:

```python
def module_a(): r[1] += Net("+12V"); r[2] += Net("AGND")
def module_b(): r[1] += Net("+12V"); r[2] += Net("AGND")
```
```
NETS: ['+12V', '+12V1', 'AGND', 'AGND1', '__NOCONNECT']
```
`[test]`

`Net("+12V")` **constructs a new net**. Two modules naming the same rail get two
electrically separate rails, silently, with `1` appended. `Net.fetch("+12V")`
does the right thing:

```
NETS: ['+12V', 'AGND', '__NOCONNECT']
```
`[test]`

This board has at least seven global rails — `+12V`, `-12V`, `+5V`, `AVDD`,
`AGND`, `PWR_GND`, `DIG_GND` — crossing six modules. A single `Net(` instead of
`Net.fetch(` on any one of them splits a rail. ERC reports it as `Only one pin
attached to net +12V1` and `No drivers for net +12V1` — **two warnings among
several hundred identical-looking ones**.

And it is the mirror image of the failure stage 5 is written to prevent. Stage 5
guards against three grounds being merged by a pour. Nothing guards against one
ground being split by a typo, and the split version passes DRC, fabricates, and
is unfixable in copper.

**Mitigation, all three:**
1. A single `rails.py` that constructs each global net **exactly once** and
   exports them as module-level objects. Modules `from rails import AGND` and
   never type `Net(` for a rail.
2. In `verify.py`, assert the exact set of global net names. Any name matching
   `^(\+12V|AGND|PWR_GND|DIG_GND|\+5V|AVDD|-12V)\d+$` is a hard failure.
3. Assert an expected minimum pin count per rail. A split rail has too few pins;
   the count is the tell.

### 5.2 Local net names collide across pages too

The same hazard, other direction. Hierarchy does **not** namespace nets:

```python
@subcircuit
def breath_rx(...): local = Net("FILT")
@subcircuit
def mods(...):      local = Net("FILT")
```
```
NETS: ['AGND', 'BREATH', 'FILT', 'FILT1', '__NOCONNECT']
```
`[test]`

Nets are one flat global namespace. Hierarchy shows up only in sheetpaths
(`/breath_rx1/`, `/mods1/`) `[test]`. So `FILT` in the breath page and `FILT` in
the mod page become `FILT` and `FILT1` — which is *correct behaviour* here, but
it means net names in the emitted netlist do not match the names in either page,
and the `1` suffix is indistinguishable from the rail-splitting bug in 5.1.

**Prefix every local net with its page:** `Net("BRX_FILT")`, `Net("MOD_FILT")`.
Then any bare numeric suffix anywhere in the netlist is unambiguously a bug, and
rule 5.1's regex check becomes a blanket `\d+$` scan.

### 5.3 Pin names are empty on library op-amps

```
ALL PINS: [('1', '', 'OUTPUT'), ('2', '-', 'INPUT'), ('3', '+', 'INPUT'), …]
```
`[test]`

The op-amp output pin has **no name** in the standard KiCad symbol. `u["OUT"]`
raises; you must write `u.uA[1]`. Inputs are `"+"` and `"-"` — legal but easy to
mistype, and `u.uA["+"]` versus `u.uA["-"]` is a one-character difference that
inverts a stage. Six dual op-amps, twelve sections, all addressed by bare number.

Given `breath-receive-stage.md` documents that two expert reviewers built two
different schematics from the same prose and six different in-amp gains were
derived, a transcription addressed by bare pin number is not where this project
should be relying on care. **Wrap each op-amp section in a named helper**
(`def inverting_stage(u_section, rin, rfb, vin, vout)`) so the polarity is
written once and reviewed once, not twelve times.

### 5.4 The design BOM has no refdes, so the parity check cannot work as written

The plan says `tools/check-bom-parity.py` "diffs the first two by refdes". It
cannot.

```
module rows: 61
total module instances (int qty): 149
qty>1 rows: U-OPA-PITCH 6 | J-CV 6 | C-DECOUPLE 19 | R-MODGAIN 8 | R-OPAMP-IN 7 …
```
`[test: python3 csv.DictReader over hardware/bom.csv]`

`hardware/bom.csv` is keyed by **role**, not designator — `R-GAIN-INAMP`,
`U-OPA-PITCH`, `TRIM-BREATH-ZERO` — and one row means many parts. 61 rows map to
**149 physical components**. The generated netlist will have 149 refdes. There is
no refdes column to diff against, and the plan's own "add a `footprint` column
(12 columns)" change does not add one.

*(The slice brief said "roughly 60 BOM rows"; that is right as rows and wrong as
parts. The SKiDL modules must instantiate 149.)*

The schematic pages make it worse: `breath-receive-stage.md` uses page-local
labels `R1`, `R1b`, `R2` … `R5` `[repo]`, which are not designators and which
will collide with the other five pages.

**This is a genuine blocker, and it has a clean fix that costs nothing.** SKiDL's
`tag=` is a free-form stable identifier that rides through into the netlist as a
field:

```
(field (name "SKiDL Tag") "R-PRECISION-1")
```
`[test]`

So set `tag="<bom-ref>-<n>"` on every instance — `tag="C-DECOUPLE-1"` …
`tag="C-DECOUPLE-19"`. Then:

- the tag pins the tstamp, giving determinism (§3);
- `check-bom-parity.py` diffs on the **tag prefix**, not refdes: strip `-\d+$`,
  group, and compare counts against the BOM's `qty` column. `C-DECOUPLE` must
  appear 19 times. That checks more than the plan's refdes diff would have —
  it catches a missing instance, not just a missing part type;
- refdes stay free to renumber without breaking parity, which defuses §3's
  cascade for the BOM check specifically (though not for board reimport).

This should go into the plan. It is the single change that makes the
`check-bom-parity.py` stage buildable at all.

---

## 6. The parts with no standard symbol

Proven to work, and this is where SKiDL beats a GUI outright. No library, no
`.kicad_sym`, no symbol editor:

```python
u1 = Part(name="AD8422", ref_prefix="U", dest=TEMPLATE, tool=SKIDL,
          pins=[Pin(num=1, name="-IN", func=Pin.types.INPUT),
                Pin(num=5, name="V-",  func=Pin.types.PWRIN), …])
```
`[test — netlist emitted, ERC ran, no KiCad, no library files]`

`tool=SKIDL` on the template is required; without it the part is looked up in a
library and fails. This covers the INA828, the MPXV4006DP, the umbilical RJ45
with its non-obvious pinout, the multi-gang pots (a 3-gang pot is just nine
pins), the trimmers and the load switch. **Make ad-hoc the default for this
board** and reach for the KiCad library only for genuinely standard parts — it
removes the `KICAD9_SYMBOL_DIR` dependency from the critical path entirely, and
with it a whole class of "works on my machine".

Set `func=` deliberately per pin. It is the only input ERC has. Typing power
pins `PWRIN`, op-amp outputs `OUTPUT` and inputs `INPUT` is what made the
output-short in §4 catchable; type everything `PASSIVE` and ERC does nothing at
all.

**Footprints are opaque strings.** SKiDL errors on a *missing* footprint but
does no validation whatsoever on a present one `[test]`. Given the plan's
intent to use footprints banked in `datasheets/MANIFEST.csv`, add a check that
every footprint string in the netlist resolves against the manifest — SKiDL will
never tell you.

---

## 7. Recommendation

**Keep SKiDL. Reject A and C. Keep B as a downstream nicety, not an
alternative.**

The argument is not that SKiDL is good — §4 shows its ERC is close to inert on
this board and §3 shows its defaults are non-deterministic. The argument is that
the alternatives lose something SKiDL has and gain nothing that matters here.

### Alternative A — hand-write the netlist S-expression from a Python dict

Genuinely tempting, and closer than it looks: the netlist is ~350 lines of
boilerplate plus a component loop, KiCad 9 discards the version field
`[source]`, and you would drop three dependencies.

**What you lose:**

1. **Connectivity is no longer derived.** In SKiDL you write `r[2] += agnd` and
   the net membership follows. In a dict you write the net membership *and* the
   pin list, and the two can disagree. That is a second source of truth for the
   same fact — the project's named failure mode, reintroduced at the centre of
   the pipeline.
2. **The output-to-output check goes.** It is nearly the only thing ERC catches
   (§4), and on a board with twelve op-amp sections it is the one worth having.
3. **Multi-unit bookkeeping becomes yours.** Six dual op-amps: you own the
   mapping from section to pin numbers and the shared power unit.
4. `netlist_to_skidl` round-tripping and `generate_svg`/`generate_dot` go.

**What you keep that SKiDL costs you:** trivially deterministic output, no random
tags, no `Net()` versus `Net.fetch()` trap, no refdes cascade.

Verdict: **reject, narrowly.** Point 1 decides it. But note that A's *advantages*
are precisely SKiDL's four gotchas — so adopting SKiDL means adopting the
mitigations in §5 as non-negotiable, not as polish.

### Alternative B — author `.kicad_sch` with `kiutils`, export via KiCad

`kiutils` 1.4.8 models the format fully — `Schematic` exposes `libSymbols`,
`schematicSymbols`, `junctions`, `labels`, `globalLabels`, `symbolInstances`
`[test]` — and it parsed SKiDL's generated schematic cleanly `[test]`.
`kicad-cli sch export netlist` exists in KiCad 9
`[source: kicad/cli/command_sch_export_netlist.cpp]`. So the chain closes.

**But it is not tractable as the primary path.** Authoring a `.kicad_sch`
means owning symbol geometry, pin coordinates, wire routing or label placement,
embedded `libSymbols`, and hierarchical UUID paths. SKiDL's own schematic
generator does exactly this job, is maintained by the author, and still failed
to route a **one**-op-amp circuit on its first attempt `[test]`. Reimplementing
that on top of `kiutils` for 149 parts is a larger project than the board.

And it buys `--schematic-parity`, which is a *proxy* for netlist equality. The
plan's replacement — assert board netlist equals SKiDL netlist, ref by ref —
checks the real thing. Trading a direct check for a proxy is backwards.

Verdict: **reject as the primary path.** Adopt the useful half: run
`generate_schematic()` as a build artifact for human review (§3), clearly marked
non-deterministic and excluded from diffs.

### Alternative C — draw it once in the GUI, automate downstream

Verdict: **reject, and it is the worst of the three.**

It defeats the stated goal in the first step, and more importantly it puts the
schematic — the thing under active revision — in a binary-ish format that this
project's review method cannot touch. Cold node-indexed review of a `.kicad_sch`
is not a thing. The one-time cost is also not one-time: `pitch-stage.md` and
`mod-channels.md` are still moving, and every topology change is another GUI
session that cannot be replayed or reviewed as a diff.

C would be right if the schematic were settled and the risk were transcription.
It is not settled, and §5 shows transcription risk is manageable with named
helpers and assertions.

### What to change in `docs/reference/pcb-pipeline.md`

1. **Correct:** "You lose `--schematic-parity`, because there is no
   `.kicad_sch`." SKiDL 2.3.0 can emit one. Keep the netlist-equality check as
   the parity mechanism and say *why* — it checks the thing directly — rather
   than presenting it as making the best of an absence.
2. **Correct:** "Fail the build on any ERC error." SKiDL exits 0 on ERC errors
   and writes the netlist anyway. Specify the `erc_logger.error.count` check and
   a warning-count ratchet (§4).
3. **Correct:** `check-bom-parity.py` "diffs the first two by refdes". The design
   BOM has no refdes and 61 rows mean 149 parts. Specify the `tag=`-prefix
   scheme in §5.4.
4. **Add:** a `rails.py` with the global nets constructed once, and the
   `Net.fetch` rule. This is the highest-consequence gotcha on the board (§5.1).
5. **Add:** every part carries explicit `ref=` **and** `tag=`. State that this
   is what makes the pipeline re-runnable; without it the claim is false (§3).
6. **Add:** `set_default_tool(KICAD9)` explicitly — SKiDL's default is `kicad10`.
7. **Add:** footprint strings are unvalidated; check them against
   `datasheets/MANIFEST.csv` in `verify.py`.
8. **Extend the smoke board.** The two-resistor proof is a good idea and should
   also prove: run the netlist generation twice and assert byte-identical output
   (ex-`date`), and assert that a deliberately split rail is caught by the
   `verify.py` net-name check. Both failures are cheap to see on two resistors
   and catastrophic to find on 149 parts.

---

## 8. Confidence and what I did not check

Marked honestly, per house rule.

- **High confidence:** everything in §2, §3, §4, §5.1, §5.2, §5.3, §6. All
  `[test]` on SKiDL 2.3.0 from PyPI, or `[source]` read in the cloned repo /
  KiCad 9.0.
- **Not tested — no KiCad in this sandbox:** that KiCad 9 actually *imports* a
  SKiDL netlist end to end. I verified the reader accepts the format by reading
  its parser `[source]`, not by running it. **This is the one claim in this
  report that the smoke board must confirm before the architecture is committed
  to.** If it fails, everything above is moot and Alternative A is next.
- **Not tested:** `ExportSpecctraDSN` round trip, locked-track survival,
  Freerouting — other slices, and all require KiCad.
- **Not checked:** whether the six schematic pages are individually transcribable
  without ambiguity. I read `breath-receive-stage.md` in full and sampled the
  BOM; the page-local `R1`/`R1b`/`R2` labelling (§5.4) is a real transcription
  hazard but I did not audit the other five pages for it.
- **Corrected mid-review:** I first computed 7750 module part instances and a
  malformed `qty` column, using `awk -F,` on a CSV with quoted commas. Re-run
  with `csv.DictReader`: 149 instances, no malformed rows. **`hardware/bom.csv`
  is fine** — the defect was in my tooling. Recorded because a finding filed
  against a clean file is the kind that does not get caught.
