# P2 — the `pcbnew` Python API, and how a netlist gets into a board

Cold review of `docs/reference/pcb-pipeline.md`. Slice: every `pcbnew` call the
plan names or implies, and the unanswered question of netlist import.

**Reviewer's evidence base.** KiCad is not installed here and cannot be —
`apt-cache policy kicad` offers `7.0.11+dfsg-1build4` only, and there is no
`pcbnew` distribution on PyPI (`https://pypi.org/pypi/pcbnew/json` → 404)
[test]. So **nothing in Part A has runtime evidence.** Every API verdict below
is read off KiCad's own source at a release tag, which is stronger than memory
and weaker than a run. Where source cannot settle a question — SWIG's handling
of one non-const `shared_ptr&` — I say so rather than guessing.

Source read from a sparse shallow clone of `gitlab.com/kicad/code/kicad` at tag
`9.0.9`, cross-checked against `8.0.9` and `10.0.6` via the GitLab raw-file API
[test: `git clone --depth 1 --branch 9.0.9 --filter=blob:none --sparse`;
`git describe --tags` → `9.0.9`].

A note on version, since it bears on everything: the plan targets KiCad 9, but
**KiCad 10.0.6 is the current release** (10.0.0 tagged 2026-03-19, 10.0.6 on
2026-08-28) [test: GitLab tags API]. The plan does not say why 9. Every
signature in this report is identical across 8.0.9, 9.0.9 and 10.0.6, so the
choice is defensible — but see breaker #7 for its expiry date.

---

## 1. Verdict table

| # | Quoted claim | Verdict | Evidence |
|---|---|---|---|
| 1 | "The Specctra helpers have changed signature across versions. `help(pcbnew.ExportSpecctraDSN)` before writing against it." | **REFUTED** | The signatures are *unchanged* across 8.0.9, 9.0.9 and 10.0.6 — all four decls byte-identical [source: `pcbnew/python/scripting/pcbnew_scripting_helpers.h` @ 8.0.9 L141–182, @ 9.0.9, @ 10.0.6 L142–184]. The real trap is not drift, it is the **overload** (row 2). `help()` will show both and not say which one works headless. |
| 2 | "`pcbnew.ExportSpecctraDSN(...)`" (stage 5, argument elided) | **MISSING — and the elided argument is the whole problem** | Two overloads exist. `ExportSpecctraDSN(wxString&)` reads `if( s_PcbEditFrame ) … else return false;` — headless it **returns `False` and writes nothing, with no exception and no message**. Only `ExportSpecctraDSN(BOARD*, wxString&)` works standalone [source: `pcbnew/python/scripting/pcbnew_scripting_helpers.cpp` @ 9.0.9]. Same shape for `ImportSpecctraSES`. |
| 3 | "the DSN export writing it into the `(wiring …)` section as **protected**" | **REFUTED in mechanism, CONFIRMED in effect** | It is written as `fix`, not `protect`: `if( track->IsLocked() ) wire->m_wire_type = T_fix;` — the `else` branch carries the comment `// could be T_protect`, i.e. `protect` is explicitly *not* used [source: `pcbnew/specctra_import_export/specctra_export.cpp` @ 9.0.9 L1585–1588, vias L1639–1642]. |
| 4 | "The whole hand-route-then-autoroute strategy depends on … Freerouting leaving it alone." | **REFUTED as a dependency** | Survival does not depend on Freerouting at all. `fix` wires are *not returned in the .ses file* (KiCad's own comment). The **importer** is what saves them: it pulls locked tracks out before `RemoveAll({PCB_TRACE_T})`, deletes the rest, then re-adds the saved ones — `// Add locked tracks: because they are exported as Fix tracks, they are not in .ses file.` [source: `specctra_import.cpp` @ 9.0.9 L377–403]. Identical at 8.0.9 L343–370. The strategy is sound; the plan's stated reason for it is wrong. |
| 5 | "One thing to prove specifically: that locked tracks survive the round trip." | **CONFIRMED as worth proving, but the proof must be aimed elsewhere** | Correct instinct. But the smoke test as described would pass for the wrong reason and teach nothing. What actually needs proving is that Freerouting **honours `fix` wires as obstacles** — KiCad guarantees the geometry comes back, and guarantees nothing about whether the router routed *over* it. See breaker #4. |
| 6 | "define classes on the board, and `ExportSpecctraDSN` writes them into the `.dsn` as rules the router honours" | **CONFIRMED** (KiCad half) | `exportNETCLASS()` emits per-class `width` and `clearance` rules; `netclassesInUse` is built from `net->GetNetClass()` and the Default class is always emitted [source: `specctra_export.cpp` @ 9.0.9 L1039, L1488–1533, L1660–1733]. Note it exports **only classes actually in use on a net** — a class defined but unassigned is silently absent from the `.dsn`. |
| 7 | "Net classes are how trace widths happen." (implies setting them from Python) | **CONFIRMED, with one unverifiable step** | `NET_SETTINGS` is `%shared_ptr`-wrapped and the netclass map is `%template`d, so the path is reachable [source: `pcbnew/python/swig/board_design_settings.i` @ 9.0.9 L1–7]. `SetTrackWidth(int)` survives — only the `std::optional<int>` overloads are `%ignore`d [source: `common/swig/netclass.i` L27–38 vs `include/netclass.h` L119–137]. The one step source cannot settle is `SetNetclass(const wxString&, std::shared_ptr<NETCLASS>&)` — a **non-const** `shared_ptr&`, SWIG's weakest typemap. See §3. |
| 8 | "`pcbnew.ZONE_FILLER(board).Fill(board.Zones())`" | **CONFIRMED verbatim** | A compat ctor `ZONE_FILLER(BOARD*)` is `%extend`ed in specifically because the real `ZONE_FILLER(BOARD*, COMMIT*)` is `%ignore`d [source: `pcbnew/python/swig/zone.i` L19–37]. `Fill(const std::vector<ZONE*>&, bool aCheck=false, wxWindow* aParent=nullptr)` — the parent defaults to null, so it is headless-clean [source: `pcbnew/zone_filler.h` L58]. `Zones()` returns `const ZONES&` and `ZONES` is `DECL_VEC_FOR_SWIG(ZONES, ZONE*)`, i.e. a real `std::vector<ZONE*>` template [source: `pcbnew/pcb_item_containers.h` L38, `pcbnew/board.h` L348]. This is the one API line in the plan that is correct as written. |
| 9 | "explicit **zone priorities** so they do not flood into each other" | **CONFIRMED** | `ZONE::SetAssignedPriority(unsigned)` / `GetAssignedPriority()`, and `zone.h` is `%include`d whole with no `%ignore` on them [source: `pcbnew/zone.h` L120/L125, `pcbnew/python/swig/zone.i` L22]. Note the name: it is **not** `SetPriority`. |
| 10 | "Thermal reliefs on every through-hole pad." | **CONFIRMED** | `ZONE::SetPadConnection(ZONE_CONNECTION)`, plus `SetThermalReliefGap(int)` and `SetThermalReliefSpokeWidth(int)` [source: `pcbnew/zone.h` L219, L230, L292]. |
| 11 | "Outline onto `Edge.Cuts` first" | **CONFIRMED, unremarkable** | `PCB_SHAPE` is exposed via `pcb_shape.i`; layer ids via `layer_ids.i`. No trap found. |
| 12 | "Load footprints" | **CONFIRMED, with a signature trap** | `FootprintLoad` is not a C++ function — it is `%pythoncode` that does `GetPluginForPath(libname).FootprintLoad(libname, name, preserveUUID)` [source: `pcbnew/python/swig/footprint.i` L157–159]. Its first argument is a **library directory path**, not an `fp-lib-table` nickname. Getting this wrong is the most likely stage-3 failure. |
| 13 | "assign every pad to its net" | **CONFIRMED** | `NETINFO_ITEM(BOARD*, const wxString& aNetName="", int aNetCode=-1)`, `board.Add(net)`, `pad.SetNet(net)` [source: `pcbnew/netinfo.h` L59]. |
| 14 | *(implied)* pcbnew can save a `.kicad_pcb` KiCad 9 reads back cleanly | **CONFIRMED** | `SaveBoard` calls `BuildConnectivity()` and `SynchronizeNetsAndNetClasses(false)`, then `PCB_IO_MGR::Save(KICAD_SEXP, …)` — the same writer the GUI uses. With `aSkipSettings` false (the default) it also writes the `.kicad_pro` via `SaveProjectAs` [source: `pcbnew_scripting_helpers.cpp` @ 9.0.9]. **This is load-bearing**: netclasses live in the project file, not the board file, so a save with `aSkipSettings=True` silently discards every trace width in the plan's table. |
| 15 | *(implied by stage 1 → stage 3)* the SKiDL `.net` file lands in the board | **MISSING — the hole** | Stage 1 emits `module.net`. Stage 3 says "Load footprints, assign every pad to its net, place." Nothing in the plan ever reads `module.net`. There is no supported `pcbnew` path that could. See §2. |
| 16 | "Freerouting does not do zones" | **CONFIRMED** (indirect) | The DSN exporter has no zone/pour output path, and the SES importer's replacement loop touches only `PCB_TRACE_T` (traces, arcs, vias) and `DeleteMARKERs()` — zones are untouched either way [source: `specctra_import.cpp` @ 9.0.9 L379–397]. The plan's ordering (pour *after* import) is right. |

---

## 2. The big one: how a netlist gets into a board, headless

### The answer is: it does not. Not through KiCad, in any version, by any interface.

This is definitive, and it is four independent negatives:

**(a) Not in the SWIG bindings.** `NETLIST`, `NETLIST_READER`, `PCB_NETLIST`
and `BOARD_NETLIST_UPDATER` appear **zero times** across every SWIG interface
file [test: `grep -rn "NETLIST\|Netlist\|netlist" common/swig/ pcbnew/python/swig/ scripting/` @ 9.0.9 → no matches]. Not
`%ignore`d — simply never included. The C++ classes exist and are healthy
(`pcbnew/netlist_reader/` holds `netlist_reader.cpp`, `pcb_netlist.cpp`,
`board_netlist_updater.cpp`), they are just not wired to Python. Same result at
10.0.6 [test: same grep against `pcbnew.i` and `board.i` @ 10.0.6 → 0 matches].

**(b) Not merely unexposed — structurally GUI-bound.** This is the part that
makes it final. The updater's only constructor is:

```cpp
BOARD_NETLIST_UPDATER::BOARD_NETLIST_UPDATER( PCB_EDIT_FRAME* aFrame, BOARD* aBoard )
```

[source: `pcbnew/netlist_reader/board_netlist_updater.cpp` @ 9.0.9 L50]. It
**requires** a `PCB_EDIT_FRAME`. Its three call sites are
`dialog_import_netlist.cpp`, `dialog_update_pcb.cpp` and `cross-probing.cpp` —
all GUI [source: same tag]. So this is not an oversight someone could fix by
adding a line to a `.i` file; the class would have to be refactored first. Do
not wait for it.

**(c) Not in `kicad-cli`.** The full 9.0.9 command tree under `pcb` is `drc`,
`render`, and `export {brep, drill, dxf, gerber, gerbers, gencad, glb, ipc2581,
ipcd356, odb, pdf, pos, step, svg, vrml, xao, ply, stl}` [source:
`kicad/kicad_cli.cpp` @ 9.0.9 L162–250, `commandStack`]. There is no `import`,
no `update`, no netlist verb. `kicad-cli` can *export* a netlist from a
schematic (`sch export netlist`) — the direction the plan does not need.

**(d) Not in the new IPC API either.** KiCad 9 ships an IPC API
(`kicad-python` / `kipy`) intended to replace SWIG. `netlist` appears nowhere in
its protobuf definitions [test: grep of `board_commands.proto`,
`editor_commands.proto`, `project_commands.proto` @ 9.0.9 → no matches]. And it
is the wrong tool regardless: *"the IPC API requires communication with a
running instance of KiCad. It is not possible to use `kicad-python` to
manipulate KiCad design files without KiCad running."* [source:
`gitlab.com/kicad/code/kicad-python`, `README.md` @ `main`].

### So the netlist file *is* decorative — and that is fine, if done deliberately

The reviewer's brief asked whether people build the board by placing footprints
and assigning nets in Python, "which works but means the netlist file is
decorative." That is exactly right, and it is also **the SKiDL project's own
official answer**, not a workaround someone invented.

**SKiDL 2.3.0 — the exact version the plan pins — hard-depends on
`kinet2pcb>=1.1.4`** [test: `pypi.org/pypi/skidl/2.3.0/json` →
`requires_dist: ['kinet2pcb>=1.1.4', 'simp_sexp>=0.3.1', …]`]. `kinet2pcb` is by
the SKiDL author and is described as "Convert KiCad netlist into a PCBNEW
.kicad_pcb file" [test: `pypi.org/pypi/kinet2pcb/json` → version 1.1.4].

SKiDL exposes this as `generate_pcb()`, a sibling of the `generate_netlist()`
the plan already uses [source: `skidl-2.3.0/src/skidl/circuit.py` L808]. Its
KiCad 9 backend is four lines:

```python
import kinet2pcb
pcb_file = pcb_file or (get_script_name() + ".kicad_pcb")
kinet2pcb.kinet2pcb(circuit, pcb_file, fp_libs)
```

[source: `skidl-2.3.0/src/skidl/tools/kicad9/gen_pcb.py`]. Note it passes the
**`Circuit` object**, not a filename — SKiDL itself skips the `.net` file
entirely. `kinet2pcb` accepts either [source:
`kinet2pcb/kinet2pcb.py` @ `master`: `if isinstance(netlist_origin, type(''))`].

And `kinet2pcb` does precisely the manual thing, against a supported API:

```python
brd = pcbnew.BOARD()
fp = pcbnew.FootprintLoad(lib_uri, fp_name)
fp.SetParent(brd); fp.SetReference(part.ref); fp.SetValue(part.value)
fp.SetFPIDAsString(part.footprint); brd.Add(fp)
pcb_net = pcbnew.NETINFO_ITEM(brd, net.name); brd.Add(pcb_net)
pad = module.FindPadByNumber(pin.num, pad); cnct.Add(pad); pad.SetNet(pcb_net)
brd.BuildListOfNets(); cnct.RecalculateRatsnest(); pcbnew.Refresh()
hierplace.hier_place(brd)
pcbnew.SaveBoard(brd_filename, brd)
```

Three things I checked because they looked like they might break headless, and
do not:

- `pcbnew.BOARD()` is **not** the ignored C++ default ctor. `board.i` `%ignore`s
  `BOARD::BOARD()` and then overrides `__init__` in `%pythoncode` to call
  `CreateEmptyBoard()`, which attaches a default project [source:
  `pcbnew/python/swig/board.i` @ 9.0.9 L72, L139–147]. Present identically at
  8.0.9 and 10.0.6.
- `pcbnew.Refresh()` is guarded by `if( s_PcbEditFrame )` — a no-op headless,
  not a crash [source: `pcbnew_scripting_helpers.cpp` @ 9.0.9].
- `FindPadByNumber(num, pad)` is the newer two-argument iterator form;
  `kinet2pcb` falls back to the old `FindPadByName` on `AttributeError`.

All dependencies are pip-reachable from here: `kinet2pcb` 1.1.4 (needs
`simp_sexp`, `hierplace`), `hierplace` 1.1.0 [test: PyPI JSON for each].

### Recommendation

**Replace stage 1→3 with `generate_pcb()`, and keep `generate_netlist()` only as
a reviewable artifact.** Concretely:

1. `circuit.generate_netlist(tool=KICAD9)` → `module.net`. Keep it. It is what
   the BOM parity check and the stage-7 netlist assertion diff against, and it
   is the diffable record. Say in the doc that it is a **record, not an input**,
   so nobody later assumes it is being consumed.
2. `circuit.generate_pcb(tool=KICAD9, fp_libs=[...])` → `module.kicad_pcb` with
   every footprint placed and every pad netted. This *is* stage 3's "load
   footprints, assign every pad to its net, place" — already written, already
   maintained by the SKiDL author, already a dependency.
3. Then `build_board.py` does only what `kinet2pcb` does **not**: board outline
   on `Edge.Cuts`, net classes, design settings, zones. `kinet2pcb` creates no
   netclasses at all [test: `grep -n "netclass\|NETCLASS" kinet2pcb.py` → no
   matches], so the plan's whole trace-width table is `build_board.py`'s job and
   must run *after* the board is generated.

The alternative — writing the placement loop by hand — is maybe sixty lines and
gives more control over placement. It is defensible. But it is sixty lines that
`kinet2pcb` has already debugged against the fp-lib-table resolution the plan
lists as a known gotcha, and SKiDL pulls it in whether or not it is used.

**Either way, the plan must say which.** Right now it says neither, and the gap
sits exactly where a reader would assume KiCad does it for them.

---

## 3. Correct signatures

Headless-safe forms. `wxString&` accepts a Python `str`.

```python
# --- board creation -------------------------------------------------------
brd = pcbnew.NewBoard("module.kicad_pcb")   # PREFER THIS over pcbnew.BOARD()
```

`NewBoard(wxString&)` loads/creates a real project at that path **and sets
`bds.m_DRCEngine`**. `CreateEmptyBoard()` (which `pcbnew.BOARD()` calls) does
neither — it attaches the anonymous `""` project and leaves `m_DRCEngine` unset
[source: `pcbnew_scripting_helpers.cpp` @ 9.0.9, both functions]. Since the
pipeline runs DRC and depends on project-stored netclasses, use `NewBoard`.

```python
# --- Specctra round trip --------------------------------------------------
ok = pcbnew.ExportSpecctraDSN(brd, "board.dsn")   # BOARD* overload. CHECK ok.
ok = pcbnew.ImportSpecctraSES(brd, "board.ses")   # BOARD* overload. CHECK ok.
```

Both return `bool` and both are wrapped in `catch( ... ) { return false; }`, so
a malformed `.ses` gives you a bare `False` with the exception swallowed
[source: `pcbnew_scripting_helpers.cpp` @ 9.0.9]. Assert on the return value;
there will be no traceback to read.

```python
# --- net classes ----------------------------------------------------------
bds = brd.GetDesignSettings()
ns  = bds.m_NetSettings                       # shared_ptr<NET_SETTINGS>, %shared_ptr-wrapped

nc = pcbnew.NETCLASS("Power")                 # NETCLASS(const wxString&, bool aInitWithDefaults=True)
nc.SetTrackWidth(pcbnew.FromMM(0.5))          # int overload — NOT the optional<int> one
nc.SetClearance(pcbnew.FromMM(0.2))
nc.SetViaDiameter(pcbnew.FromMM(0.8))
nc.SetViaDrill(pcbnew.FromMM(0.4))

ns.SetNetclass("Power", nc)                   # <-- PROBE THIS (see below)
ns.SetNetclassPatternAssignment("+12V", "Power")
```

`SetName`, `SetTrackWidth(int)`, `SetClearance(int)`, `SetViaDiameter(int)`,
`SetViaDrill(int)` are all exposed; only the `std::optional<int>` overloads are
`%ignore`d [source: `common/swig/netclass.i` L27–38, `include/netclass.h`].

**The one thing to probe first.** `SetNetclass` takes
`std::shared_ptr<NETCLASS>&` — a *non-const* reference [source:
`include/project/net_settings.h` @ 9.0.9 L62]. SWIG's `std_shared_ptr.i`
handles by-value and `const&` reliably; non-const `&` is its known soft spot,
and source cannot tell you whether the generated typemap accepts a Python
`NETCLASS` here. If it rejects the call, the fallback is
`SetNetclasses(const std::map<wxString, std::shared_ptr<NETCLASS>>&)` — a
`const&` over a type that **is** explicitly `%template`d as `netclasses_map`
[source: `board_design_settings.i` L7], so it is the safer call of the two.
Build the whole map, set it once. Probe both in `pcb/smoke/`, first thing.

Also note `m_netClassPatternAssignments` is `%ignore`d as a member, so assign
through `SetNetclassPatternAssignment(pattern, netclass)`, not by touching the
map [source: `board_design_settings.i` L3–4].

```python
# --- zones ----------------------------------------------------------------
z = pcbnew.ZONE(brd)
z.SetNetCode(brd.GetNetcodeFromNetname("PWR_GND"))
z.SetAssignedPriority(2)                      # NOT SetPriority
z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
z.SetThermalReliefGap(pcbnew.FromMM(0.5))
z.SetThermalReliefSpokeWidth(pcbnew.FromMM(0.5))
brd.Add(z)

pcbnew.ZONE_FILLER(brd).Fill(brd.Zones())     # correct exactly as the plan writes it
```

```python
# --- footprints -----------------------------------------------------------
fp = pcbnew.FootprintLoad(lib_dir_path, "R_0805_2012Metric")  # DIRECTORY PATH, not nickname
fp.SetParent(brd); fp.SetReference("R1"); fp.SetValue("10k")
fp.SetFPIDAsString("Resistor_SMD:R_0805_2012Metric")
brd.Add(fp)

# --- nets -----------------------------------------------------------------
net = pcbnew.NETINFO_ITEM(brd, "BREATH")      # (BOARD*, name="", netcode=-1)
brd.Add(net)
pad.SetNet(net)

# --- locking --------------------------------------------------------------
track.SetLocked(True)                         # BOARD_ITEM::SetLocked(bool); IsLocked() is virtual

# --- save -----------------------------------------------------------------
pcbnew.SaveBoard("module.kicad_pcb", brd)     # leave aSkipSettings False, or lose netclasses
```

---

## 4. What would break a first run, ranked

**1. Stage 3 has no input.** No netlist reaches the board, and no KiCad
interface can make one. Everything downstream — DSN export, routing, DRC, the
stage-7 netlist equality assertion — operates on an empty board and several
steps will *succeed* on it. Highest rank because it is the only one that is a
gap in the plan rather than a bug in a line of it. Fix per §2.

**2. `ExportSpecctraDSN("board.dsn")` returns `False` and writes nothing.** The
plan elides the argument in the one place it shows the call, and the
single-argument form is the one a reader would write. No exception, no message,
no file — and the next line hands Freerouting a path that is not there. Use the
`BOARD*` overload and assert the return. Same for `ImportSpecctraSES`.

**3. Net classes silently absent from the `.dsn`.** Three ways to get this,
each quiet: (a) `SetNetclass`'s non-const `shared_ptr&` typemap refuses the call
(§3); (b) a class is defined but never pattern-assigned, so `netclassesInUse`
never sees it and `exportNETCLASS` never emits it [source: `specctra_export.cpp`
L1488–1501]; (c) the board is saved with `aSkipSettings=True`, so the classes
never reach the `.kicad_pro` and are gone on reload. In all three, Freerouting
routes power at the Default width and the board fabricates. The plan's stage-7
assertions check net *identity*, not trace *width* — nothing catches this. Add
a width assertion.

**4. Freerouting routing over the locked tracks.** KiCad's side is sound: `fix`
wires go into the `.dsn`, and the importer re-adds the originals regardless of
what comes back. But that guarantee is about *geometry preservation*, not
*obstacle avoidance*. If Freerouting ignores `fix`, the import restores your
hand-routed `AGND` star **and** keeps the autorouter's copper on top of it — two
sets of tracks in the same space, and the stage-7 check "locked nets
geometrically unchanged" passes, because they are. It is DRC that would have to
catch it. Prove Freerouting honours `fix` in the smoke board; that is the
question the plan's smoke test should be asking instead of the one it asks.

**5. `FootprintLoad` given a nickname.** Its first argument is a library
directory path. `FootprintLoad("Resistor_SMD", …)` fails. Compounded by the
plan's own correct gotcha that `fp-lib-table` does not exist until a GUI has
run — and if you use `kinet2pcb`, it resolves nicknames through exactly that
table, so the two interact.

**6. Missing footprints vanish silently.** `kinet2pcb` logs a warning and
`continue`s past any footprint it cannot find — the board is produced, minus
those parts. The plan's "board netlist equals the SKiDL netlist, ref by ref"
assertion is what catches this, which makes that assertion load-bearing rather
than belt-and-braces. Worth saying so in the doc.

**7. Nothing above is testable here, and the toolchain is one release from
expiry.** `apt` offers KiCad 7 only and there is no `pcbnew` on PyPI [test], so
the allowlist the plan names as "the one hard network requirement" gates the
entire review, not just the build. And when it clears: **the SWIG bindings are
removed in KiCad 11** — *"The SWIG bindings still exist in KiCad 9 and 10, but
are removed in KiCad 11"* [source: `gitlab.com/kicad/code/kicad-python`
`README.md` @ `main`]. Every `pcbnew.*` call in this plan has a known end date.
The successor IPC API needs a running KiCad in 9 and 10, and only becomes
headless-capable in 11 via `kicad-cli api-server` [source: same README]. Not a
first-run breaker. It is the reason to write stage 3 as a thin, replaceable
layer rather than spreading `pcbnew` calls through the pipeline.

---

## 5. Corrections the plan should absorb

- Stage 5 header line: `pcbnew.ExportSpecctraDSN(brd, path)` / `ImportSpecctraSES(brd, path)`, with the return value checked.
- Line 111: "as protected" → as `fix`; and the survival mechanism is the SES *importer* re-adding saved locked tracks, not Freerouting honouring them.
- Line 109–114: point the smoke test at *Freerouting honouring `fix` as an obstacle*. Locked-track survival is guaranteed by KiCad source and does not need proving.
- Line 91–92 ("probe, don't assume"): the signatures have not drifted across 8/9/10. Replace with the overload warning, which is the actual hazard.
- Stage 3: name how the netlist enters the board. It currently does not.
- Stage 1: mark `module.net` as a record, not a pipeline input.
- §"The stack": add `kinet2pcb` and `hierplace` (they arrive with SKiDL regardless), and state why KiCad 9 and not 10.

## Claims I could not settle

- `NET_SETTINGS::SetNetclass`'s non-const `shared_ptr&` under SWIG. Needs a run. `SetNetclasses` is the safer path and is `%template`d.
- Whether Freerouting 2.x honours DSN `fix` wires. Freerouting's behaviour, not KiCad's — out of this slice, and the single most important thing for the smoke board to answer.
- Whether `hierplace`'s placement is acceptable for this board, or whether placement must be authored. Unexamined.
