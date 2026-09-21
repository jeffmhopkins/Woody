# P3 — The Specctra round trip, and the load-bearing locked-track claim

**Subject:** `docs/reference/pcb-pipeline.md` (Proposed 2026-09-21, nothing built).
**Method:** cold. Prior review directories not read. Conclusions come from the
KiCad and Freerouting sources and from running Freerouting on hand-built DSN
files.

**Sources used**

| Tag | What |
|---|---|
| `[source-kicad]` | `gitlab.com/kicad/code/kicad`, tag **9.0.0**, commit `286b061`. Paths relative to repo root. |
| `[source-fr]` | `github.com/freerouting/freerouting`, **master**, commit `97758b5`; the binary built from it self-reports `v2.4.2-SNAPSHOT`. |
| `[test]` | Freerouting built from that commit and run headless on DSN files written by hand for this review. Build required two local patches to compile on JDK 21 — see *Test harness caveat* at the end. |
| `[calc]` | Arithmetic, shown. |

---

## 1. Verdict on the locked-track strategy

> hand-route the critical nets first, LOCK them, export Specctra DSN, autoroute
> the rest with Freerouting, import SES, and the locked traces survive untouched.

### It works. Keep it. But it does not work for the reason the plan gives, and the plan's stated mechanism is wrong in a way that would have produced duplicate traces if it had been right.

The plan says the export writes locked tracks into `(wiring …)` "as protected"
and guesses the token `(type protect)`. **Both halves of that are wrong.** What
actually happens:

1. KiCad writes a locked track as **`(type fix)`**, not `protect`
   `[source-kicad pcbnew/specctra_import_export/specctra_export.cpp:1615]`:
   ```cpp
   if( track->IsLocked() )
       wire->m_wire_type = T_fix;    // tracks with fix property are not returned in .ses files
   else
       wire->m_wire_type = T_route;  // could be T_protect
   ```
   The same two lines exist for vias at `:1669`/`:1671`.

2. Freerouting maps `fix` → `SYSTEM_FIXED`, its strongest state
   `[source-fr src/main/java/app/freerouting/io/specctra/parser/Wiring.java:263]`.
   `SYSTEM_FIXED` items are not routable and not deletable
   (`Item.isUserFixed`, `Item.isDeletionForbidden` at `Item.java:861,866`;
   `Trace.isRoutable` at `Trace.java:206` returns `!isUserFixed() && netCount() > 0`).

3. Freerouting **omits every `SYSTEM_FIXED` item from the SES**
   `[source-fr src/main/java/app/freerouting/io/specctra/SesWriter.java:339]`:
   ```java
   for (Item currentItem : netItems) {
     if (currentItem.getFixedState() == FixedState.SYSTEM_FIXED) { continue; }
   ```

4. KiCad's importer does **not** recover locked tracks from the SES. It keeps
   the original objects in memory and re-adds them
   `[source-kicad pcbnew/specctra_import_export/specctra_import.cpp:377-405]`:
   ```cpp
   std::vector<PCB_TRACK*> locked;
   TRACKS tracks = aBoard->Tracks();
   aBoard->RemoveAll( { PCB_TRACE_T } );
   for( PCB_TRACK* track : tracks ) {
       if( track->IsLocked() ) locked.push_back( track );
       else { ...; delete track; }
   }
   ...
   // Add locked tracks: because they are exported as Fix tracks, they are not
   // in .ses file.
   for( PCB_TRACK* track : locked ) aBoard->Add( track );
   ```

So a locked track survives **byte-identically**, because it is the same C++
object that was never removed from the board — not because anything round-tripped
it. That is a stronger guarantee than the plan assumed, and the plan's verify
step ("locked nets geometrically unchanged") will pass exactly, with no
floating-point tolerance needed.

### Confirmed by running it `[test]`

Hand-built DSN with two nets already wired: `NET_LOCKED` marked `(type fix)`,
`NET_ROUTE_DETOUR` marked `(type route)`, plus `NET_TOROUTE` left unrouted and
positioned so its straight path on `F.Cu` is blocked by the `fix` wire.

```
java -cp … app.freerouting.Freerouting -de t2.dsn -do t2.ses -mp 20 --gui.enabled=false
```

SES `(network_out …)`:

```
(net "NET_ROUTE_DETOUR"
  (wire (path F.Cu 25000  850000 -2000000  850000 -3500000
                          4850000 -3500000 4850000 -2000000)
        (type protect)))
(net "NET_TOROUTE"
  (wire (path B.Cu 25000  1850000 -1200000  1850000 -200000)))
```

- `NET_LOCKED` is **absent** — as the KiCad comment claims.
- `NET_TOROUTE` was routed, and routed on **`B.Cu`**, i.e. it detoured to the
  other layer rather than cross the `fix` wire. **The locked track is honoured
  as an obstacle**, which is the part that actually matters and which the plan
  never states as a requirement.
- The newly routed wire carries no `(type …)`, so KiCad imports it unlocked.

### Why the plan's guess would have broken it

Re-running the identical board with the one wire changed from `(type fix)` to
`(type protect)` — the plan's guess `[test]`:

```
(net "NET_LOCKED"
  (wire (path F.Cu 25000  1150000 -2000000  1150000 -500000
                          5150000 -500000  5150000 -2000000)
        (type protect)))
```

`protect` **is echoed back into the SES**. KiCad would then re-add its preserved
locked original *and* build a second unlocked track from the SES wire at the same
coordinates — **two overlapping traces on the same net, one locked, one not**.
DRC would not flag it. The plan is saved only by KiCad not doing what the plan
says it does.

**Action:** correct the mechanism sentence in stage 4 / the smoke-test paragraph.
The token is `fix`, the guarantee is "KiCad never lets the locked track leave the
board", and the property to smoke-test is *that the autorouter treats it as an
obstacle*, not that it "survives".

---

## 2. Verdict table

| # | Claim under test | Verdict | Evidence |
|---|---|---|---|
| 1 | DSN export writes existing tracks into `(wiring …)` | **TRUE** | `specctra_export.cpp:1573-1630` emits one `WIRE`+`PATH` per run of same net/width/layer; vias at `:1637-1672` `[source-kicad]` |
| 2 | Locked tracks marked `(type protect)` | **FALSE** — it is `(type fix)` | `specctra_export.cpp:1615` `[source-kicad]` |
| 2b | Freerouting understands `protect` | Only by accident | `protect` is not a lexer keyword; it falls through `{Identifier} { return yytext(); }` (`SpecctraFileDescription.flex:208`) and lands in `calcFixed`'s `else if (nextToken != NORMAL)` branch → `USER_FIXED` (`Wiring.java:265-266`) `[source-fr]` |
| 3a | Unlocked tracks are exported too | **TRUE**, as `(type route)` | `specctra_export.cpp:1617` `[source-kicad]` |
| 3b | Freerouting rips up those unlocked tracks | **FALSE — it freezes them** | `route` is also not a keyword; same fall-through → `USER_FIXED` → `isRoutable()` false, `isDeletionForbidden()` true. Confirmed: a 4-segment detour on an otherwise trivial net survived 10 router passes and 2 optimizer passes untouched, while the optimizer demonstrably worked on another net in the same run `[test]` |
| 4 | Freerouting honours protected/fixed wiring | **TRUE**, and more strongly than needed | `Wiring.java:257-277`, `Item.java:861-872`, `Trace.java:206`, `Via.java:147` `[source-fr]` + `[test]` |
| 6 | `ImportSpecctraSES` replaces all tracks / preserves locked | **Replaces all, preserves locked** | `specctra_import.cpp:377-405`; `BOARD::RemoveAll` with `PCB_TRACE_T` clears the whole `m_tracks` list incl. arcs and vias (`board.cpp:1341-1349`, where `PCB_ARC_T`/`PCB_VIA_T` are explicitly rejected with "Use PCB_TRACE_T to remove all tracks, arcs, and vias") `[source-kicad]` |
| 7 | Net classes become DSN rules the router honours | **TRUE for width and clearance only** | See §4 |
| — | "Freerouting has no boundary without `Edge.Cuts`" | **TRUE** | `fillBOUNDARY` walks `GetBoardPolygonOutlines` (`specctra_export.cpp:1031-1075`) `[source-kicad]` |
| — | Freerouting needs `xvfb` / OpenGL | **FALSE** | Ran with no X display and no xvfb. `--gui.enabled=false` also silences the "Couldn't get screen resolution" warning `[test]` |
| — | "Java 21 already present" is enough | **TRUE to run; false to build** | Java 21 present and runs the jar. Building master needs **JDK 25** (`build.gradle` `languageVersion 25`; sources use unnamed `_` variables and `java.lang.IO`) `[source-fr]` `[test]` |

### Things I checked and found *not* to be defects

Recorded so the next reviewer does not re-spend the time.

- **`RemoveAll({PCB_TRACE_T})` followed by `delete` on vias and arcs is not a
  dangling-pointer bug.** `PCB_TRACE_T` clears all of `m_tracks`, which holds
  traces, arcs and vias together `[source-kicad board.cpp:1341-1344]`.
- **Footprint graphics from *every* layer — silkscreen, fab, courtyard — are
  exported as image `(outline …)`** (`specctra_export.cpp:703-706` collects all
  `PCB_SHAPE_T` with no layer filter). This does **not** block routing:
  `ComponentOutline.isObstacle()` returns `false` and `tileShapeCount()` returns
  `0` `[source-fr ComponentOutline.java:120]`.
- **The 10× coordinate difference between DSN input and SES output is not a
  bug.** KiCad declares `(resolution um 10)` but writes plain micrometres
  (`scale()` = nm/1000, `specctra_export.cpp`), Freerouting multiplies by the
  declared resolution on output, and KiCad's importer divides by it
  (`specctra_import.cpp`, `T_um: factor = 1e3` then `factor * distance /
  resValue`). `[calc]` 8.5 mm → exported `8500` → SES `85000` → imported
  `1e3 × 85000 / 10 = 8.5e6 nm` = 8.5 mm. Round trip exact.
- **Exception safety of the export.** `ExportBoardToSpecctraFile` reverts the
  temporary footprint flips on the exception path `[source-kicad
  specctra_export.cpp:110-131]`.

---

## 3. What the round trip destroys

Everything here must be done **after** `ImportSpecctraSES`, or protected by
locking, or accepted as lost.

### A. Destroyed on the board by the import

| Thing | What happens |
|---|---|
| **Every unlocked track, arc and via** | Deleted and rebuilt from the SES `[source-kicad specctra_import.cpp:377-390]` |
| **Arc curvature on any unlocked arc** | The exporter writes only `GetStart()`/`GetEnd()` into the `PATH` (`specctra_export.cpp:1585,1626,1630`); there is no `QARC` emission anywhere in the exporter. An unlocked arc leaves as a **straight chord** and cannot come back as an arc. Lock any arc you care about |
| **Unlocked tracks with no net** (`netcode == 0`) | Not exported (`specctra_export.cpp:1590`) and not preserved (not locked) → **silently deleted**. Lock them or lose them |
| **Footprint positions and orientations** | Overwritten from the SES `(placement …)` on every import (`specctra_import.cpp`, the `m_session->placement` block), even when the router moved nothing. Values are re-quantised to the SES integer grid |
| **Zone fills** | Zones themselves are untouched (`RemoveAll` never touches `m_zones`, and the importer calls no filler), but every fill is stale the moment new tracks land. Re-fill after import — the plan already says this |
| **Group membership of deleted tracks** | Removed from their parent group before deletion (`specctra_import.cpp:390-391`) |

### B. Never reaches the router (so it cannot be obeyed)

| Thing | Note |
|---|---|
| **`<project>.kicad_dru` custom rules** | **Zero references** to `kicad_dru` or custom DRC rules in the exporter. Not exported at all |
| **All non-copper layers** | Only `GetCopperLayerCount()` layers are emitted (`specctra_export.cpp:1124-1152`). Mask, paste, silkscreen, courtyard, Edge.Cuts (except as the boundary), user layers: absent |
| **Differential pairs, length matching, skew** | No diff-pair or length rule is emitted |
| **Per-net via size / drill** | Only a per-*class* via padstack via `(circuit (use_via …))` (`specctra_export.cpp:1766-1767`) |
| **Teardrops** | Teardrops are `ZONE`s in KiCad 9 (`zone.h:706`) and are **not** filtered out of the plane export (`specctra_export.cpp:1202-1211` skips only `GetIsRuleArea()`), so any pre-existing teardrop leaves as a `(plane …)`. Generate teardrops after import, never before |
| **Thermal-relief settings, zone priorities, pad connection modes** | Not expressible in the DSN. The plan's stage 6 already handles these post-import — correct |
| **Board-level clearance for SMD pairs is deliberately relaxed** | `specctra_export.cpp:1192-1198` writes `(clearance <default/4> (type smd_smd))`. The router is told a pad-to-pad clearance **four times looser** than DRC will check |

**Consequence for the doc.** Stage 3 currently says:

> Both are read by `kicad-cli pcb drc`, so what the router obeys and what DRC
> checks are the same file.

This is **false**, and it is the sentence most likely to cost a day. The router
obeys exactly five things: the boundary, keepouts (from rule areas), planes,
the global `(rule (width) (clearance) (clearance … smd_smd))`, and per-class
`(rule (width) (clearance))` plus `use_via`. Everything else DRC checks is
invisible to it — and the `smd_smd` term is deliberately mismatched. Expect DRC
violations after a clean autoroute and budget for them.

---

## 4. Do net classes really become router rules?

**Yes, for track width and clearance. Verified on both sides.**

Export `[source-kicad specctra_export.cpp:1698-1771]` — one `(class …)` per
netclass, listing its net names, with:

```cpp
clazz->m_rules = new RULE( clazz, T_rule );
std::snprintf( text, sizeof(text), "(width %.6g)", scale( aNetClass->GetTrackWidth() ) );
clazz->m_rules->m_rules.push_back( text );
std::snprintf( text, sizeof(text), "(clearance %.6g)", scale( aNetClass->GetClearance() ) );
clazz->m_rules->m_rules.push_back( text );
...
snprintf( text, sizeof(text), "(use_via \"%s\")", via->GetPadstackId().c_str() );
clazz->m_circuit.push_back( text );
```

Import `[source-fr Network.java:483-495]`:

```java
for (Rule currentRule : netClass.rules) {
  if (currentRule instanceof Rule.WidthRule rule1) {
    int traceHalfwidth = (int) Math.round(coordinateTransform.dsnToBoard(rule1.value / 2));
    boardNetClass.setTraceHalfWidth(traceHalfwidth);
  } else if (currentRule instanceof Rule.ClearanceRule rule) {
    addClearanceRule(board.rules.clearanceMatrix, boardNetClass, rule, -1, coordinateTransform);
    ...
```

Anything else in a rule scope hits
`FRLogger.warn("…rule type not yet implemented…")` and is dropped.

**Three caveats the plan should record:**

- KiCad renames the `Default` class to **`kicad_default`** in the DSN
  (`specctra_export.cpp:1756-1757`) to avoid colliding with Freerouting's own
  `default` class. Any script that greps the DSN for class names must expect this.
- The plan's `Analog` class is described as "0.25 mm, routed by hand". Because
  those nets will be hand-routed and locked, their class width is what
  Freerouting will use *if it ever routes them anyway* — e.g. a net you meant to
  hand-route but missed. Set the class width to the value you actually want, and
  rely on the verify step, not on the class, to catch a missed hand-route.
- Only width and clearance cross. Via **diameter** crosses only through the
  class's single `use_via` padstack.

---

## 5. Is there a cleaner alternative to the DSN round trip?

**No — but there is a much cleaner way to use it, and the plan should adopt two changes.**

There is no headless alternative worth having. `kicad-cli` has no autorouter;
KiCad's interactive router is not exposed to the Python API; the DSN/SES path is
the only scripted route-the-rest mechanism KiCad 9 ships. Keep it.

What to change:

### 5a. Delete all unlocked tracks before every export — the plan is not re-runnable without this

This is the most consequential finding after §1. Because `(type route)` is read
as `USER_FIXED`, **the previous run's autoroute output is frozen on the next
run.** Stage 5 run twice does not re-route; it routes only what is still
unconnected and accretes around whatever the last run left. The plan's stated
goal is that the pipeline "is re-runnable forever", and as written it is not:
run *n* and a clean run produce different boards.

Demonstrated: `NET_ROUTE_DETOUR` in the test is exactly "a previously autorouted,
unlocked track". It survived untouched `[test]`.

Fix, in `route.py`, immediately before `ExportSpecctraDSN`:

```python
for t in list(board.Tracks()):
    if not t.IsLocked():
        board.Remove(t)
```

This also removes the trap in the smoke test: as written
("Route one trace, lock it, autoroute, and diff it") the smoke test **passes
either way** and therefore proves nothing about unlocked tracks. Add a second
trace, left unlocked and deliberately ugly, and assert that it *was* changed.

### 5b. Use `-inc` / `ignore_net_classes` instead of relying on locking alone

Freerouting takes a list of net classes to leave entirely alone
`[source-fr GlobalSettings.java:893, AutorouterSettings.java:51]`:

```
--router.autorouter.ignore_net_classes Analog,AGND
```
(`-inc` is the deprecated spelling.) Putting the hand-routed nets in their own
class and naming that class here is declarative, survives a forgotten lock, and
is visible in the command line rather than in per-track state. Use it **with**
locking, not instead of it.

### 5c. Smaller, but they will each cost an hour

- **Use the two-argument overloads.** `pcbnew.ExportSpecctraDSN(filename)` and
  `ImportSpecctraSES(filename)` operate on the GUI frame and **return `False`
  immediately** when there is none `[source-kicad
  pcbnew/python/scripting/pcbnew_scripting_helpers.cpp:401-413,448-459]`. Only
  `ExportSpecctraDSN(board, filename)` / `ImportSpecctraSES(board, filename)`
  work headless (`:415,461`). Both wrap the call in `catch(...) { return false; }`,
  so **the failure reason is discarded** — check the boolean and treat `False`
  as fatal, because nothing will be printed. The plan's snippet shows neither the
  arguments nor a return check.
- **Drop `xvfb-run` from the Freerouting line.** Not needed; pass
  `--gui.enabled=false` instead `[test]`.
- **`-mp 0` means unlimited, and negative values clamp to 0**
  `[source-fr GlobalSettings.java:744-757]`. `-mp 100` is fine; keep the
  `timeout` wrapper regardless. `-mp` is deprecated in favour of
  `--router.autorouter.max_passes` and warns on every run.
- **Disable telemetry.** Freerouting calls `api.freerouting.app` on startup; in a
  sandbox that is 18 blocked CONNECTs and added latency. Pass
  `--usage_and_diagnostic_data.disable_analytics=true` — verified to silence it
  `[test]`.
- **A malformed DSN exits non-zero with no output file** `[test]`, so the shell
  can detect router failure without parsing the log. Worth asserting anyway that
  the `.ses` exists and is non-empty before importing.
- **A malformed board outline is only a warning.** `BuiltBoardOutlines` failing
  produces `wxLogWarning` and export continues with an **empty boundary**
  `[source-kicad specctra_export.cpp:118-119]`. Headless that message goes
  nowhere. Assert `GetBoardPolygonOutlines` succeeds, or grep the DSN for a
  non-degenerate `(boundary …)`, before invoking the router.

---

## Test harness caveat

Freerouting master does not build on the JDK 21 that is present. To get a binary
I set `build.gradle`'s Java version from 25 to 21, enabled preview features (the
sources use unnamed `_` variables), and added a four-line local shim for
`java.lang.IO`, which is a JDK 25 API used at four call sites in
`Freerouting.java`. **None of these touch the Specctra reader, the Specctra
writer, or the router**, and every behaviour reported as `[test]` is independently
derivable from the sources cited beside it. The binary self-reported
`v2.4.2-SNAPSHOT`.

The `[test]` results therefore describe Freerouting **master**, not a released
2.x jar. Anyone pinning a release should re-run the two-wire DSN above against
the exact jar the pipeline will use — it is a ten-second check and it is the one
that the whole analog strategy rests on.

## Open, with what decides it

- **Which Freerouting release the pipeline pins.** Decided by running the
  `fix`/`route` two-wire DSN against the candidate jar and confirming the `fix`
  wire is absent from the SES and the `route` wire comes back as `protect`.
- **Whether `PWR_GND`/`DIG_GND` should be poured before or after the export.**
  Not in this slice's scope, but the round trip forces the question: with no
  plane in the DSN the router will autoroute the ground nets as ordinary traces,
  which then sit under the pour added in stage 6. Decided by whether stage 6's
  zones can be created (unfilled) before stage 5 so they export as `(plane …)`,
  or by adding the ground nets to `ignore_net_classes`.
