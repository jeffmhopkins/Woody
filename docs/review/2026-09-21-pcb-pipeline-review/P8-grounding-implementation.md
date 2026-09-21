# P8 — the three-ground pour, as a KiCad implementation problem

**Slice:** `docs/reference/pcb-pipeline.md` §5 "Pour — three grounds, two zones,
one star", tested as an implementation rather than as an intention.
**Method:** cold. No `docs/review/**` read. Corpus read: `hardware/module/power-entry.md`,
`hardware/module/breath-receive-stage.md`, `hardware/module/breath-output-stage.md`,
`hardware/module/digital-and-supervision.md`, `hardware/module/mod-channels.md`,
`hardware/module/pitch-stage.md`, `docs/decisions/0004-cv-interface-module.md`,
`docs/decisions/0003-breath-sensing-path.md`, `config/figures.yaml`, `hardware/bom.csv`.
**Primary source:** KiCad at tag `9.0.0` from `gitlab.com/kicad/code/kicad`, read
as source. Every KiCad claim below carries a file and line. Vendor sites blocked;
no vendor claim is made.

---

## 0. Verdict in one paragraph

The plan's §5 is four sentences and **three of the four are wrong about what
KiCad does**, one of them in the direction that silently destroys the thing the
section exists to protect. Zone priorities do not stop two grounds flooding into
each other — they cannot, because different-net zones never merge under any
priority; what priority actually does is *delete* the losing zone in the overlap.
Net ties are the right mechanism and the plan does not mention them. "Thermal
reliefs on every through-hole pad" is already KiCad's default and, applied
literally, is wrong at the one pad that defines the whole scheme. And the pour
plan enumerates three grounds when the corpus has **four**, pours the two that
should be routed, and gives no copper at all to the one that every op-amp, the
DAC and all six jacks return to — a net which **has no name anywhere in this
repo**.

Underneath all of that: the corpus specifies **three mutually exclusive `DIG_GND`
topologies** in three documents, and §5 silently picks one. This slice cannot be
implemented as written because the thing to be implemented is not decided.

---

## 1. Element-by-element verdict

| Plan's words | Verdict | Why |
|---|---|---|
| "`PWR_GND` and `DIG_GND` as separate zones" | **Wrong nets.** The scheme is inverted | §7, F-7 |
| "with explicit zone priorities so they do not flood into each other" | **False premise.** Priority does not do this and cannot | §2, F-1 |
| "a single deliberate tie at the power inlet" | **Right, mechanism unstated.** It is a net tie or it is a DRC error | §3, F-4 |
| "`AGND` gets no zone at all — a routed star" | **Wrong twice**: AGND has no star in the corpus, and bare copper is worse than a guard | §7, F-8, F-9 |
| "plus a keepout so neither ground zone floods across it" | **Right object, wrong stage.** Must exist before the DSN export or Freerouting ignores it | §5, F-6 |
| "Thermal reliefs on every through-hole pad" | **Already the default**, and wrong at the star pad | §6, F-10, F-11 |
| `ZONE_FILLER(board).Fill(board.Zones())` | **Works**, but nothing checks the stored fill is current | §4, F-5 |
| (unstated) three grounds | **Four grounds.** The fourth is the one that needs the pour | §7, F-7 |
| (unstated) stitching vias | Needed, but not the binding problem | §8 |

---

## 2. Zone priorities do not do what the plan thinks

**F-1 `[source]` — different-net zones never merge, at any priority, so priority
is not what keeps them apart.**

`ZONE_FILLER::buildCopperItemClearances()` decides zone-vs-zone interaction in
one place, `pcbnew/zone_filler.cpp:1465-1485`:

```cpp
for( ZONE* otherZone : m_board->Zones() )
{
    if( evalRulesForItems( CLEARANCE_CONSTRAINT, aZone, otherZone, aLayer ) < 0 )
        continue;                                   // negative clearance permits shorting
    if( otherZone->GetIsRuleArea() ) { ... }
    else if( otherZone->HigherPriority( aZone ) )
    {
        if( !otherZone->SameNet( aZone ) )
            knockoutZoneClearance( otherZone );      // <-- the only different-net path
    }
}
```

Two zones on different nets are kept apart by the **clearance constraint**,
unconditionally, whatever their priorities are. Priority selects only *which one
loses*. And what "loses" means is not "yields the contested strip" — it is
`knockoutZoneClearance( otherZone )`, which subtracts the winner's **entire
outline plus clearance** from the loser's fill. So:

- If the `PWR_GND` and `DIG_GND` outlines are disjoint, priority is irrelevant.
- If they overlap, the lower-priority zone is **erased across the whole overlap**,
  not split with it.

**The copper split is set by where the zone *outlines* are drawn. Priority is a
tie-break, not a partition.** The plan describes priority as doing the
partitioning, which means the actual design work — deciding the two outline
polygons — is not in the plan at all.

**F-2 `[source]` — equal priorities resolve by UUID, which is not reproducible.**

`ZONE::HigherPriority()`, `pcbnew/zone.cpp:395-409`, ends:

```cpp
    if( m_priority != aOther->m_priority )
        return m_priority > aOther->m_priority;
    return m_Uuid > aOther->m_Uuid;
```

Two zones left at the default priority resolve by comparing freshly generated
UUIDs. For a pipeline whose stated purpose is to be "re-runnable forever", this
is a per-run coin-flip wherever the outlines touch. Explicit priorities *are*
worth setting — but for determinism, which is not the reason the plan gives.

**F-3 `[source]` — the default zone clearance is 0.5 mm, and it comes out of the
loser's side.**

`ZONE_CLEARANCE_MM 0.5` (`pcbnew/zones.h:37`). Where the two ground regions abut,
there is a ≥0.5 mm moat, entirely subtracted from the lower-priority zone. Any
trace crossing that moat has no return copper beneath it for at least 0.5 mm plus
whatever the moat widens to around pads.

**Precedent `[web]`, and it agrees.** `naguirre/mds-hardware/dac/dac.kicad_pcb`
(fetched `raw.githubusercontent.com/naguirre/mds-hardware/master/dac/dac.kicad_pcb`)
is a real 2-layer split-ground DAC board: `GND` zone at `(priority 1)` and `GNDA`
zone at the default priority, **outlines that abut along a shared polyline and do
not overlap** —

```
GND  outline: (43.5,48.25) (43.5,74) (56.75,74) (56.75,82) ... (57.5,114.75) (73.75,114.75) (73.75,48.25)
GNDA outline: (43.5,74)    (56.75,74) (56.75,82) ...           (57.5,114.75) (43.5,114.75)
```

The dividing line is drawn by hand, twice, once into each polygon. That is what
this job actually is. Priority 1 on `GND` exists only to make the border
deterministic.

---

## 3. Net ties: yes, this is the right mechanism, and here is exactly how

**F-4 — the plan's "single deliberate tie at the power inlet" has no legal
expression in KiCad without a net tie, a 0 Ω part, or a DRC exclusion.**

A track carries exactly one net. A track drawn from `PWR_GND` copper to
`DIG_GND` copper is `DRCE_SHORTING_ITEMS`, which defaults to
`RPT_SEVERITY_ERROR` — `BOARD_DESIGN_SETTINGS::BOARD_DESIGN_SETTINGS()`
initialises every code to error at `pcbnew/board_design_settings.cpp:164-165` and
shorting is not in the exception list at lines 167-203. So a "correct" board
built the naive way **fails** `kicad-cli pcb drc --severity-error
--exit-code-violations`.

### How KiCad's net tie works, verified in source

- **Declared on the footprint**, not the board: `FOOTPRINT::AddNetTiePadGroup()`
  / `GetNetTiePadGroups()` / `IsNetTie()`, `pcbnew/footprint.h:295-353`. A group
  is a comma-separated pad-number list; `MapPadNumbersToNetTieGroups()`
  (`pcbnew/footprint.cpp:3194`) parses it, backslash-escaped, into pad→group.
- **Serialised** as `(net_tie_pad_groups "1, 2")` —
  `pcbnew/pcb_io/kicad_sexpr/pcb_io_kicad_sexpr.cpp:1267-1271`, parsed at
  `..._parser.cpp:4635`.
- **DRC honours it in two places**: pad-to-pad, via
  `padToNetTieGroupMap` in `drc_test_provider_copper_clearance.cpp:760-767`; and
  track-to-item, via `DRC_ENGINE::IsNetTieExclusion()`,
  `drc_engine.cpp:1866-1878`, called at `drc_test_provider_copper_clearance.cpp:276`
  and `:872`. The cache is built once per run by
  `FOOTPRINT::BuildNetTieCache()` (`footprint.cpp:3127`), driven from
  `drc_cache_generator.cpp:165`.
- **DRC also validates the tie itself**: `FOOTPRINT::CheckNetTies()`
  (`footprint.cpp:~3020`) unions all of the footprint's copper on each of
  `{ F_Cu, In1_Cu, B_Cu }`, indexes pads to outlines, and errors if any single
  copper outline touches two pads that are *not* in the same group. So you cannot
  accidentally tie a third net through the footprint. `CheckNetTiePadGroups()`
  rejects unknown pad numbers and a pad listed in two groups. Both run from
  `drc_test_provider_footprint_checks.cpp:115-128`.
- **Connectivity is unchanged**: the nets stay distinct. Each net's ratsnest
  terminates on its own pad of the tie. That is exactly the property `verify.py`
  wants — "`AGND`, `PWR_GND`, `DIG_GND` still distinct" is *guaranteed by
  construction*, and "tied exactly once" becomes "there is exactly one net-tie
  footprint whose group contains pads of both nets".

**Version:** `net_tie_pad_groups` is present and complete in `9.0.0`, which the
plan already requires for `kicad-cli pcb drc` (KiCad 8+). `[source]` The stock
library ships `NetTie.pretty` with NetTie-2/3/4 in SMD and THT, pad sizes
0.3/0.5/1.0/2.0 mm `[web, GitHub code search over KiCad/kicad-footprints
mirrors]`. I could not reach `dev-docs.kicad.org` (egress-blocked) to pin the
exact introducing version; treat "7.0" as unverified and simply note that 9.0.0
has it.

### What a THT net tie actually looks like

`NetTie-2_THT_Pad1.0mm.kicad_mod`, fetched verbatim `[web,
raw.githubusercontent.com/diodeinc/pcb/main/lib/std/kicad-footprints/NetTie.pretty/NetTie-2_THT_Pad1.0mm.kicad_mod]`:

```
(attr exclude_from_pos_files exclude_from_bom allow_missing_courtyard)
(net_tie_pad_groups "1, 2")
(fp_poly (pts (xy 0 -0.65) (xy 2.6 -0.65) (xy 2.6 0.65) (xy 0 0.65)) (fill yes) (layer "F.Cu"))
(fp_poly (pts ... ) (fill yes) (layer "B.Cu"))
(pad "1" thru_hole circle (at 0 0)   (size 1.3 1.3) (drill 1) (layers "*.Cu"))
(pad "2" thru_hole circle (at 2.6 0) (size 1.3 1.3) (drill 1) (layers "*.Cu"))
```

Note `exclude_from_bom` — **this collides with the plan's own BOM parity gate.**
`tools/check-bom-parity.py` is specified to "fail on any part present in one and
not the other". A net tie has a refdes and pads, so it is in the SKiDL netlist
and in the generated BOM, and it must *not* be in `hardware/bom.csv` (it is not a
part). The parity script needs an explicit exemption for footprints carrying
`exclude_from_bom`, or the gate fails on a correct board. Stated now, because
this is precisely the class of defect this project keeps finding.

### Creating it programmatically

`pcbnew/python/swig/footprint.i:33` is `%include footprint.h`, so
`AddNetTiePadGroup`, `ClearNetTiePadGroups`, `GetNetTiePadGroups` and `IsNetTie`
are all reachable from `pcbnew` Python `[source]`. Either:

1. instantiate the stock `NetTie:NetTie-2_THT_Pad1.0mm` footprint like any other
   and assign the two pads to the two nets — the group is already in the library
   file, nothing to set; or
2. `fp.AddNetTiePadGroup("1, 2")` on a footprint you built.

The SKiDL side needs a two-pin part with that footprint so the netlist carries
the refdes and the two nets. This is a `Part` with two `passive` pins; the ERC
will not object.

### But: Freerouting does not understand net ties — and it does not need to

`[web]` freerouting/freerouting **issue #718, "Allow Net-Ties", is open**, on the
"Future" milestone, as of 2026-06-15: Freerouting reports clearance violations
between the different-net pads of a tie. A `fixtures/Issue718-Allow_Net-Ties/`
sample board exists in the repo; the local `v2.5.0` checkout contains no
net-tie handling of any kind (`grep -ril net.tie` → nothing).

Two things make this survivable, both read out of the KiCad exporter:

- The tie's copper bridge is an `fp_poly`, i.e. `SHAPE_T::POLY`, and the Specctra
  exporter's footprint-graphic switch
  (`pcbnew/specctra_import_export/specctra_export.cpp:702-860`) handles
  `SEGMENT`, `CIRCLE`, `RECTANGLE`, `ARC` and ends `default: continue;`. **The
  bridge is silently dropped from the `.dsn`.** Freerouting therefore never sees
  the short.
- The stock footprints do not overlap their pads: 0.5 mm edge-to-edge on
  `NetTie-2_SMD_Pad0.5mm`, 1.3 mm on `NetTie-2_THT_Pad1.0mm`. KiCad's default
  `DEFAULT_MINCLEARANCE` is 0.0 and clearance comes from the netclass
  (`include/board_design_settings.h:83`); at the plan's own 0.25 mm track class,
  a 0.5 mm pad gap clears.

**So: use a stock net-tie footprint whose pad gap exceeds the largest clearance
rule, and prove it on the two-resistor smoke board.** That is exactly the kind of
thing `pcb/smoke/` exists for, and the plan should name it alongside the locked-
track round trip it already names.

### Prefer a bridged solder jumper over a bare net tie

The `dac.kicad_pcb` precedent does not use `NetTie` at all — it uses
`Jumper:SolderJumper-2_P1.3mm_Bridged_RoundedPad1.0x1.5mm` with
`(net_tie_pad_groups "1, 2")` `[web]`. Same DRC mechanism, same one-point tie,
but the bridge can be **cut with a knife and re-bridged with solder**. On a board
whose whole grounding argument is a hypothesis about a 0.2-cents-per-square
effect, being able to open the star on the bench and measure the difference is
worth more than the footprint costs. Recommend that footprint over `NetTie-2_*`.

(That same board ties in **two** places — one net tie on F.Cu, one on B.Cu. Cited
as evidence for the *idiom*, not for the topology; two ties is not a star.)

---

## 4. Stopping a zone flooding across the AGND region

**The object is a rule area, and `pcbnew` can create it.** `[source]`
`ZONE::SetIsRuleArea(bool)` plus the five `SetDoNotAllow*` setters,
`pcbnew/zone.h:744-758`. `pcbnew/python/swig/zone.i` is `%include zone.h`, so all
of them are Python-reachable. The filler honours it at
`zone_filler.cpp:1475-1478`:

```cpp
if( otherZone->GetIsRuleArea() )
{
    if( otherZone->GetDoNotAllowCopperPour() && !aZone->IsTeardropArea() )
        knockoutZoneClearance( otherZone );
}
```

— note it knocks out **with clearance**, so the no-pour region is effectively the
polygon grown by the clearance rule.

Serialisation is `(zone ... (keepout (copper_pour not_allowed) ...))`; the legacy
name "keepout" and the current name "rule area" are the same object.

**F-5 `[source]` — nothing in the pipeline detects a stale fill, and `kicad-cli
pcb drc` does not refill.** `PCBNEW_JOBS_HANDLER`'s DRC job
(`pcbnew/pcbnew_jobs_handler.cpp:1932-2100`) builds a `DRC_ENGINE`, optionally
loads a netlist for parity, and runs the tests. There is no `ZONE_FILLER` call
anywhere in the file. `zone.h:916-919` says so explicitly in a comment:
"`m_needRefill = false` does not imply filled areas are up to date". There is no
DRC error code for an out-of-date fill. **So `pour.py` editing an outline without
re-filling, or `route.py` running after the pour, produces a board whose gerbers
and whose DRC report disagree, silently.** The plan says "re-fill after *any*
later change", which is the right instinct and exactly the kind of instruction
this project's CLAUDE.md says not to rely on. Make it mechanical: in `verify.py`,
re-fill a scratch copy of the board and assert every zone's
`GetFilledPolysList(layer)` is identical to the stored one.

**F-6 `[source]` — the rule area must exist before `ExportSpecctraDSN`, or
Freerouting routes straight through it.** Rule areas *are* exported, as Specctra
keepouts, at `specctra_export.cpp:1319-1345`, with the type chosen from the
flags:

```cpp
if( zone->GetDoNotAllowVias() && zone->GetDoNotAllowTracks() ) keepout_type = T_keepout;
else if( zone->GetDoNotAllowVias() )                           keepout_type = T_via_keepout;
else if( zone->GetDoNotAllowTracks() )                         keepout_type = T_wire_keepout;
else                                                           keepout_type = T_keepout;
```

A rule area with only `DoNotAllowCopperPour` set falls to the `else` and exports
as a full `T_keepout` — which is what you want, but only if the area exists at
export time. The plan creates everything zone-related in stage 5, **after** the
autoroute in stage 4. Move the AGND rule area (and, for the same reason, the two
ground zone outlines — they export as `COPPER_PLANE`s at
`specctra_export.cpp:1202-1240`) into stage 2, so Freerouting routes around them
instead of through them. Set `DoNotAllowTracks` and `DoNotAllowVias` as well as
`DoNotAllowCopperPour` on the AGND area; "no pour" alone does not stop a router
laying a `MOD 3` trace across the sense star.

---

## 5. Will DRC pass a correctly-built board? Yes — and that is the problem

**Short answer: with a net tie, DRC passes. Without one, it fails on
`shorting_items`. Neither outcome tells you the grounding is right, and the
failure modes that matter are all below the `--severity-error` line.**

**F-7 `[source]` — the pipeline's DRC gate cannot see an orphaned ground pour.**

`m_DRCSeverities[ DRCE_ISOLATED_COPPER ] = RPT_SEVERITY_WARNING`
(`board_design_settings.cpp:178`). The plan's gate is
`kicad-cli pcb drc --format json --severity-error --exit-code-violations`, which
excludes warnings. So:

- A `DIG_GND` pour whose only connection is the net tie, where the tie's thermal
  relief starves or the tie pad ends up on the wrong layer, is **isolated
  copper — a warning — and the gate passes.**
- Worse, the default island-removal mode is `ISLAND_REMOVAL_MODE::ALWAYS`
  (`zone_settings.cpp:75`, `zone.cpp:66`), and `zone_filler.cpp:737-746` deletes
  isolated outlines outright. A partly-orphaned pour loses the orphaned part
  from the gerbers with **no diagnostic at all**.
- The one case that does get reported is `allIslands` — if *every* polygon of a
  zone is an island, `zone_filler.cpp:703-717` declines to remove any of them, and
  each becomes a `DRCE_ISOLATED_COPPER` **warning**. Which the gate still skips.

**Fix, and it is cheap:** run the gate at `--severity-all` and treat the report as
a whitelist, or — better, and in this project's idiom — assert in `verify.py`
that `board.GetConnectivity()` puts every zone's fill in the same cluster as the
named anchor pad for its net. "Zero unrouted" does not cover this: a zone island
is not a ratsnest edge.

**F-8 `[source]` — `starved_thermal` is an ERROR by default and will fire on a
correct board.** `DRCE_STARVED_THERMAL` is not in the exception list at
`board_design_settings.cpp:167-203`, so it inherits `RPT_SEVERITY_ERROR`.
`DRC_TEST_PROVIDER_ZONE_CONNECTIONS` (`drc_test_provider_zone_connections.cpp:101-230`)
counts spoke intersections and reports if fewer than
`MIN_RESOLVED_SPOKES_CONSTRAINT`, default `DEFAULT_MINRESOLVEDSPOKES 2`
(`include/board_design_settings.h:99`). Any thermal-relieved pad that lands near
the edge of its region — which, on a 2-layer board with two abutting ground
regions and a 0.5 mm moat, is a *lot* of pads — resolves one spoke and hard-fails
the build. Expect to spend real iterations on this, and budget it: the plan's
"five full iterations, then stop and report" is likely to be consumed by exactly
this.

**Summary for question 3:**

| Situation | `--severity-error` result | Correct? |
|---|---|---|
| Two grounds joined by a track, no net tie | **FAIL** (`shorting_items`) | Board is right, gate is wrong |
| Two grounds joined by a net-tie footprint | PASS | Yes |
| Ground pour fully orphaned from its tie | PASS (warning only) | **Gate is blind** |
| Ground pour partly orphaned | PASS (island silently deleted) | **Gate is blind** |
| Correct board, pad near a region edge | **FAIL** (`starved_thermal`) | Gate is right, layout needs work |
| Zone outline edited, not re-filled | PASS against stale copper | **Gate is blind** |

---

## 6. Thermal reliefs: one zone setting, not a per-pad campaign

**F-9 `[source]` — "thermal reliefs on every through-hole pad" is a single enum
value, and it is not even necessary because thermal-on-everything is already the
default.**

`enum class ZONE_CONNECTION { INHERITED, NONE, THERMAL, FULL, THT_THERMAL }`,
`pcbnew/zones.h:46-53`, where `THT_THERMAL` is documented "Thermal relief only for
THT pads". Set it once per zone: `zone.SetPadConnection(...)`
(`pcbnew/zone.h:278`), serialising as `(connect_pads thru_hole_only)`
(writer `pcb_io_kicad_sexpr.cpp:2509-2528`, parser `..._parser.cpp:6707-6730`).
`DRC_ENGINE::EvalZoneConnection()` (`drc_engine.cpp:656-687`) then converts
`THT_THERMAL` to `THERMAL` for `PAD_ATTRIB::PTH` pads and to `FULL` for everything
else. And **KiCad's zone default is already `THERMAL` for all pads** — the writer
comment at `pcb_io_kicad_sexpr.cpp:2515` reads "Default option not saved or
loaded" for `THERMAL`. So the plan's bullet is a no-op as written, and if it
means "THT thermal, SMD solid", it is `thru_hole_only`, one call.

The plan's answer to "per pad, per zone, or per net class" is therefore: **per
zone**, with two escape hatches.

- **Per pad**: `PAD::SetLocalZoneConnection()` (`pcbnew/pad.h:482`), serialised
  `(zone_connect 2)`. The `dac.kicad_pcb` precedent uses exactly this to force
  `FULL` on its two net-tie pads `[web]`.
- **By rule**, and this is the answer the plan should have: the
  `.kicad_dru` it already carries supports `zone_connection`,
  `thermal_relief_gap`, `thermal_spoke_width` and `min_resolved_spokes`
  (`drc_rule_parser.cpp:298-299, 324-327`), with values `solid` /
  `thermal_reliefs` / `none` (`:405-407`). And critically, **`ZONE_FILLER` itself
  evaluates them** — `zone_filler.cpp:1070` calls
  `bds.m_DRCEngine->EvalZoneConnection( pad, aZone, aLayer )` — so a `.kicad_dru`
  rule changes the actual copper, not only the DRC verdict. Conditions on
  `A.Pad_Type == 'Through-hole'` and `B.Reference == 'C*'` are both documented in
  KiCad's own shipped examples (`pcbnew/dialogs/panel_setup_rules_help_9more_examples.h:49-50, 88`).
  Later matching rules override earlier ones — `drc_engine.cpp:1355` reports
  "Rule applied; overrides previous constraints" and calls `applyConstraint( c )`,
  iterating the ruleset forward from `m_constraintMap` in file order
  (`:1411-1416`, built by `push_back` at `:545`). **So write the broad rule
  first and the exceptions last.**

**F-10 `[calc]` — "every through-hole pad" is wrong at the star pad, and the
error is measurable in this design's own units.**

1 V/octave means 1200 cents per volt, so **1.2 cents/mV** — which reproduces
`power-entry.md`'s own 6.2 mV → 7.4 cents exactly (6.2 × 1.2 = 7.44), so the
transfer is right.

1 oz copper: R□ = ρ/t = 1.72×10⁻⁸ / 35×10⁻⁶ = **0.491 mΩ per square**.
Umbilical return current: `config/figures.yaml:umbilical-current`.

A default thermal relief is four 0.5 mm spokes across a 0.5 mm gap
(`ZONE_THERMAL_RELIEF_GAP_MM 0.5`, `ZONE_THERMAL_RELIEF_COPPER_WIDTH_MM 0.5`,
`pcbnew/zones.h:33-34`) — one square each, four in parallel, **0.25 square =
0.123 mΩ**. At 359 mA that is 44 µV, i.e. **0.053 cents**. Resolve only two
spokes (still legal: `DEFAULT_MINRESOLVEDSPOKES 2`) and it is **0.106 cents** —
a quarter of the tightest candidate in `config/figures.yaml:pitch-cents-budget`,
from one DRC-passing thermal relief on one pad.

**The star pad — `J-PWR-EURO`'s GND pin — must be `solid`.** So must the
`PWR_GND` pads of the load-switch path. Everything else THT can be
`thru_hole_only`. Express it as two `.kicad_dru` rules, broad first:

```
(rule "tht_thermal"
    (constraint zone_connection thermal_reliefs)
    (condition "A.Pad_Type == 'Through-hole'"))

(rule "star_and_power_solid"
    (constraint zone_connection solid)
    (condition "A.Type == 'Pad' && (A.Reference == 'J-PWR-EURO' || A.Reference == 'Q-LOADSW')"))
```

— and then assert the resolved connection per pad in `verify.py` rather than
trusting the rule, because `A.Reference` resolution on a *pad* (as opposed to a
footprint) is the one part of this I could not confirm from source; KiCad's own
example uses it on `B`, and `drc_engine.cpp:1424-1445` shows pads inheriting
zone-connection rules from their parent footprint when no pad-level rule matched,
which suggests it works but does not prove it. **Probe it.**

**On the plan's stated reason** — "this board is hand-soldered" — that is correct
and it is worth the cost everywhere except the star. A 1.0 mm-drill pad soldered
solid into a full pour on 1 oz copper is a nuisance, not an impossibility, with a
larger tip; one such pad is an acceptable price for the one node the whole
grounding scheme is named after.

---

## 7. What the scheme gets wrong electrically

### F-11 — there are four grounds, not three, and the fourth has no name

`docs/decisions/0004-cv-interface-module.md:606-611` lists **four** returns
arriving at this board, in a table: `PWR_GND`, `DIG_GND`, **"Module analog
return"**, and `AGND`. The pipeline plan enumerates three and pours two. The one
it never mentions is the module's own analog return — the net that carries:

- all six `OPA2197` negative supplies and the `INA828`'s reference `[repo,
  breath-receive-stage.md, breath-output-stage.md]`
- the DAC's `AVDD` return from the LM317 `[repo, power-entry.md]`
- the pitch stage's reference, the mod channels' `R1`/`R2` dividers
- **all six jack sleeves** — `C-FILT-MOD`, `C-OUT-BREATH`, `C-FILT-PITCH`,
  `C-AA-PITCH` all return to it `[repo, mod-channels.md:43, breath-output-stage.md:62,
  pitch-stage.md:202]`
- the two 1 MΩ in-amp bias resistors `R4`/`R5` `[repo,
  breath-receive-stage.md:44-47]`

**This net is the reference the Eurorack world actually measures the module's CV
against** — the jack sleeves *are* this net. And it has no name. The corpus calls
it, in four documents: "the analog return" (ADR 0004 ×3), "`AGND(module)`"
(`breath-receive-stage.md` ×4, `breath-output-stage.md` ×1), "module analog
ground" (ADR 0003:384), "analog star" (`breath-receive-stage.md:28`,
`digital-and-supervision.md:53`), and — in three separate drawings — **plain
`AGND`** (`breath-output-stage.md:55, :62`, `mod-channels.md:43`,
`pitch-stage.md:202`).

That last one is the live hazard. The plan's architectural choice is "transcribe
each schematic page into a SKiDL module". A transcriber reading
`mod-channels.md:43` writes `C_FILT_MOD[2] += Net('AGND')`, and the
umbilical's sense conductor — the thing ADR 0003 spends several pages
protecting — acquires an 82 nF capacitor to a jack sleeve, four times over. The
plan's `verify.py` check "**no two nets merged**; `AGND`, `PWR_GND`, `DIG_GND`
still distinct" will **pass**, because the merge happened in the transcription,
not in the pour. It is the same net from the moment the netlist is generated.

**This is the highest-severity finding in the slice.** It is not a pour problem
and no amount of zone work fixes it. **Name the fourth net before anyone writes a
SKiDL module** — `AGND_M`, or `ANA_GND`, anything that is not `AGND` — and fix
the four drawings that use the bare name. Then the parity check the plan already
has (board netlist ≡ SKiDL netlist) becomes meaningful.

### F-12 — the plan pours the two nets that should be routed and routes the one that should be poured

Work it from this design's own numbers.

`[calc]` **Cost of shared copper.** At 1.2 cents/mV and 0.491 mΩ/□:

```
per square of copper shared between the umbilical return and the analog reference
    0.359 A x 0.491 mΩ = 176 µV  ->  x 1.2 = 0.211 cents per square
```

Against `config/figures.yaml:pitch-cents-budget` — which is **DISPUTED**, and
whose candidates run 0.42 / 0.85 / ~1.2 / 1.35 cents — that is **2.0 squares** at
the tightest candidate, 6.4 at the loosest. Two squares of 0.25 mm trace is
**0.50 mm of length**. Two squares of a 2 mm-wide pour path is 4.0 mm.

Three consequences follow, and they invert the plan:

1. **`PWR_GND` should not be a zone.** It is a two-terminal net: etherCON return
   → star at `J-PWR-EURO` GND, plus the load switch's own ground pins (`LT1641`
   GND, `C-TIMER`, `R-FB-LO`, the FET source return). Its *own* IR drop is
   irrelevant — nothing on the board references it, and a 1.233 V threshold does
   not care about 2.7 mV. What matters is that it shares copper with nothing.
   A **pour is the worst possible shape for that requirement**, because a pour's
   entire purpose is to be the thing everything nearby connects to, and because
   the filler decides its boundary from whatever routing happens to land on that
   layer. Draw it as a wide trace. The plan's own stage 3 already says
   "**`PWR_GND` / `DIG_GND`** — separate copper, one tie at the inlet" and routes
   it by hand; stage 5 then pours it. The two stages contradict each other.

2. **The module analog return should be the pour**, and should be continuous
   under the whole analog section — the six op-amps, the in-amp, the DAC's AVDD
   decoupling, and all six jacks. That is the net the 0.211 cents/□ number
   applies to, and a continuous pour is the only shape that keeps its internal
   spreading resistance in the µΩ-per-path range.

3. **`DIG_GND` is undecided in the corpus** and §5 picks a side without saying
   so. Three documents, three topologies:

   | Document | What it says |
   |---|---|
   | `docs/decisions/0004-cv-interface-module.md:627` | "**`DIG_GND` likewise** — its own path to the star" |
   | `hardware/module/power-entry.md:495-498` | "**`DIG_GND` is *not* given its own path to the star**, which an earlier revision of ADR 0004 asked for … routing it to a distant star point is the classic split-plane mistake" |
   | `hardware/module/digital-and-supervision.md:53` | DIG_GND "`└── analog star, single tie (ADR 0004)`" — a *third* destination, the analog star, not the power inlet |

   `power-entry.md` asserts ADR 0004 was corrected. **ADR 0004 line 627 still
   says the opposite.** This is exactly the project's named failure mode, it is
   semantic so `tools/check-staleness.py` cannot see it (CLAUDE.md §4), and it is
   the single fact that decides whether §5 pours one ground region or two.
   **Not a pipeline defect — a corpus defect that blocks the pipeline.**

   My view, on the merits: `power-entry.md` is right. There is exactly one
   fast-edge net group on this board (SCLK/MOSI/CS, `74AHCT125` → `DAC8568`),
   it is physically tiny, and a 2 MHz SPI return routed to a distant star is a
   loop antenna sitting next to a 60 dB-CMRR instrumentation amplifier. Merge
   `DIG_GND` into the analog-return pour at the `74AHCT125`, keep the SPI in one
   corner by placement, and let the pour be the return. Then the board has **two**
   ground regions to build, not three: (analog return + DIG_GND) as one pour, and
   `PWR_GND` as a routed net, tied at the inlet star by one net tie.

### F-13 — `AGND` has no star in this design, and the plan invents one

`docs/decisions/0004-cv-interface-module.md:630-633`:

> **`AGND` is not in this list.** It terminates at the in-amp's IN+ and at the
> two 1 MΩ bias resistors, and that is all it does. Anything that makes it a
> return path breaks the reason a 2 m analog run works at all.

So `AGND` is a **two-terminal sense input**, DC-referenced to the module's analog
return only through `R4` = 1 MΩ. It does **not** meet `PWR_GND` and `DIG_GND` at
the inlet star, and `breath-receive-stage.md:232` confirms the intent: 1 MΩ
against a 359 mA return is 0.2 ppm, "the rule survives in substance".

The plan says "`AGND` … a routed star" and `verify.py` asserts "`AGND` tied
exactly once". If "tied once" means "one DC connection to the star at the inlet",
**that is a defect**: it shorts out `R4`, puts `AGND` in parallel with the return
path, and converts the sense conductor into a return — the one failure ADR 0003
exists to prevent. If it means "tied to nothing but the in-amp and the bias
resistors", the wording is wrong and will be implemented wrongly by whoever reads
it next. **Say which.** My reading of the corpus: `AGND` is tied to the analog
return at *one* point and that point is `R4`, a 1 MΩ resistor, not a piece of
copper. The check to write is "`AGND` has exactly three pads on it: `INA828` IN+
(via `R2`), `R4`, and the etherCON pin" — a netlist assertion, not a geometry
one, and therefore cheap and exact.

### F-14 — "no zone at all" is the wrong instinct for a high-impedance sense node

Bare laminate under a sense trace is not neutral; it is the absence of a
reference, which maximises capacitive pickup from whatever passes nearby. The
right structure for a node that **carries no current by construction** is a
**guard**: pour `AGND` as a small island under and around the BREATH/AGND pair
from the etherCON to the in-amp inputs, tied at exactly one point (the `R2`/`R4`
node). A zero-current net cannot become a return path no matter what shape it is;
the plan's ban on an AGND zone protects against a failure mode that a
single-point-tied island does not have.

The objection to check is asymmetry: a guard under `BREATH` alone adds stray
capacitance to one leg and unbalances the pair. `[calc]`, using
`breath-receive-stage.md`'s own method — which reproduces its "±5 % gives ~46 dB"
exactly at 1 kHz (ωRΔC = 2π·1000·10 kΩ·75 pF = 4.71×10⁻³ → 46.5 dB):

```
guard adds ~2.1 pF to one leg (0.25 mm trace, ~30 mm, over FR4, ~0.7 pF/cm)
    ωRΔC = 2π·1000 · 10 kΩ · 2.1 pF = 1.32e-4    ->  77.6 dB
RSS with the ±1 % C_cm term (15 pF -> 9.4e-4 -> 60.5 dB):
    sqrt(9.42e-4² + 1.32e-4²) = 9.51e-4          ->  60.4 dB
```

The guard costs **0.1 dB** of CMRR. It is affordable. Pour it.

*(Separate observation, outside this slice but it fell out of the arithmetic:
`±1 % C0G` on `C_cm` gives 60.5 dB on its own, which is the entire 60 dB budget
spent by one term with nothing left for the 0.1 % resistors' 94 dB or anything
else. `breath-receive-stage.md` says "±1 % is needed to clear 60" — it clears it
by 0.5 dB. Worth someone's attention; not mine.)*

---

## 8. Ground stitching vias

Needed, but they are not the interesting problem, and the plan's silence on them
is a smaller omission than it looks.

`[calc]` The fastest edge on the module is the `74AHCT125`'s output. Taking a
3–6 ns transition `[from memory — no AHCT datasheet is banked; `datasheets/`
should carry one before this is relied on]`, f_knee = 0.35/t_r = **58–117 MHz**.
In FR4 (v ≈ 1.4×10⁸ m/s), λ at 117 MHz is 1.2 m, so λ/20 = **60 mm**. A 45 ×
100 mm board is electrically small at every frequency it generates. **Stitching
pitch is not a constraint here.**

What *is* needed:

- A return via **within a few mm of every SPI signal via**. There are only three
  such signals and one hop (`74AHCT125` → `DAC8568`); place them by hand.
- If any ground region is poured on both F.Cu and B.Cu, stitch the two fills
  together — otherwise the top-side fragments are separate nets' worth of
  floating copper, and per F-7 they will be silently deleted as islands rather
  than reported.
- A via pair at each decoupling cap, since on 2 layers the decoupling loop
  includes two vias. The plan's "every decoupling cap within ~2 mm of the pin"
  check measures the wrong thing on a 2-layer board — the loop is
  pin→cap→via→pour→via→pin, and the via placement dominates the 2 mm.

None of this is a reason to change the plan's architecture. It is a reason to add
two assertions to `verify.py`.

---

## 9. 2-layer or 4-layer: a real opinion

**Go to 4 layers.** The design says 2; I think 2 is the wrong call, and the
argument is not "more layers are nicer", it is that **two of the corpus's own
stated requirements are mutually exclusive on two layers.**

`power-entry.md:496-498` requires the SPI return to be "the pour directly under
its trace". ADR 0004:624-628 requires `PWR_GND` to run "on its own copper,
touching no other return on the way", and the analog return to be "its own
region". On two layers there is exactly one continuous pour layer — the other is
the component and fanout layer, which on a board with ~63 through-holes
(6 jacks × 3 + 2 pots × 5 + toggle 3 + IDC 16 + 4 electrolytics × 2 + the DPAK +
the LM317 + the tie `[calc, from the schematic pages]`) is perforated on **both**
sides anyway. So the moment the two ground regions must be disjoint — which F-1
shows is the only way to get two regions — **any trace crossing the boundary has
no return copper under it for at least the 0.5 mm moat**, and its return current
detours to the star. That is precisely the "classic split-plane mistake"
`power-entry.md` names, and on two layers it is not avoidable by care; it is
forced by the topology.

The area argument is weaker and I will not lean on it: ~63 through-holes at a
1.6 mm pad plus 0.5 mm clearance remove ≈ 63 × 5.3 = **334 mm²**, about 7 % of a
45 × 100 mm layer, before any via `[calc, on an assumed outline — the real
outline is `pcb-pipeline.md` §Precursors item 4 and is not settled, and
`config/figures.yaml:panel-height-budget` is DISPUTED]`. Area is not the binding
constraint. **Continuity is.**

What 4 layers buys, concretely:

- **In1 = one solid, uncut analog-return plane** under the whole analog section
  and under the SPI. The 0.211 cents/□ number then applies to a plane whose
  spreading resistance between any two points in the analog section is in the
  tens of µΩ, not to a pour whose boundary was decided by the autorouter.
- `PWR_GND` becomes a routed net on In2 or B.Cu with no pour to accidentally
  touch, and the star becomes a genuinely local geometry rather than a
  board-scale one.
- The AGND guard gets a reference plane beneath it, which is what makes a guard
  work.
- `starved_thermal` (F-8) largely goes away, because pads are no longer near
  region edges.

What it costs, honestly:

- Hand-soldering THT into inner planes is harder, not easier — which is an
  argument *for* `thru_hole_only` thermals on the inner planes, i.e. the plan's
  §5 bullet, applied where it belongs.
- Prototype cost. I cannot quote it: vendor sites are blocked from this session.
  `[from memory, unverified]` 4-layer at this size is within a small multiple of
  2-layer at the usual prototype houses. **If that is load-bearing, someone must
  check it against a real quote before this recommendation is acted on.**

**If 2 layers is held anyway** — which is defensible on cost and on the fact that
essentially every Eurorack module cited in this repo's prior art is 2-layer — then
the scheme must change, not just the layer count:

1. **One pour, not two.** B.Cu poured solid with the analog return (with
   `DIG_GND` merged into it per F-12.3).
2. **`PWR_GND` as a routed trace**, ≥1.5 mm wide, etherCON → star, on F.Cu,
   crossing nothing.
3. **One net tie at `J-PWR-EURO`'s GND pad**, solid zone connection.
4. **AGND as a small guard island** on B.Cu, single-tied at the `R2`/`R4` node,
   inside a rule area that keeps the main pour out.
5. No boundary for any signal to cross, because there is only one region.

That is a simpler board than the plan describes and it satisfies more of the
corpus's stated requirements.

---

## 10. What the plan is missing

Ranked.

1. **The fourth ground net, and its name.** (F-11) Blocks the SKiDL
   transcription, not just the pour. Three drawings already call it `AGND`.
2. **A decision on `DIG_GND`.** (F-12.3) Three documents, three answers, one of
   them a live contradiction between ADR 0004 and `power-entry.md`. §5 cannot be
   implemented until this is one fact.
3. **Net ties.** (F-4) The named mechanism, with DRC support, for the exact
   problem §5 describes. Recommend the bridged-solder-jumper variant.
4. **A DRC gate that can see an orphaned pour.** (F-7) `--severity-error` is
   blind to isolated copper and blind to silently-deleted islands.
5. **A stale-fill assertion.** (F-5) `kicad-cli pcb drc` does not refill; nothing
   detects a fill that no longer matches its outline. This is the project's named
   failure mode wearing a copper hat.
6. **Zone outlines as first-class design artefacts.** (F-1) The partition is the
   outline geometry. There is no stage in the plan that produces it, reviews it,
   or diffs it.
7. **Rule areas created before the DSN export.** (F-6) Otherwise Freerouting
   routes through the AGND star.
8. **Freerouting's net-tie gap** (open issue #718) proved on the smoke board,
   alongside the locked-track round trip the plan already proves there.
9. **`check-bom-parity.py` must exempt `exclude_from_bom` footprints.** (§3) A
   net tie is in the netlist and not in `hardware/bom.csv`, correctly.
10. **`solid`, not thermal, at the star pad and the load-switch path.** (F-10)
    0.053–0.106 cents per default thermal relief at 359 mA.
11. **Stitching-via and decoupling-loop assertions.** (§8) The existing "cap
    within 2 mm" check measures the wrong loop on a 2-layer board.
12. **`config/figures.yaml:pitch-cents-budget` is DISPUTED**, and the entire
    grounding argument — including every number in this report — is scaled
    against it. The plan's own §Precursors item 3 says tracked figures the layout
    depends on must be out of `disputed` before the pipeline starts. This is one.

---

## 11. What I could not verify, and where I may be wrong

- **`A.Reference` as a condition on a `Pad`** (§6). KiCad's shipped example uses
  it on `B`, and `drc_engine.cpp:1424-1445` shows pad→footprint inheritance for
  zone-connection constraints, which is suggestive but not proof. Probe it.
- **`ZONE::SetLocalClearance( std::optional<int> )`** (`pcbnew/zone.h:165`). There
  is no `std::optional` typemap anywhere in `pcbnew/python/swig/*.i`. `[from
  memory]` SWIG without a typemap will not convert a Python `int` to
  `std::optional<int>`, so this setter is probably uncallable from `pcbnew`
  Python in 9.0.0. If so, set zone clearance via board design settings or by
  writing the S-expression with `kiutils` — which the plan already carries for
  exactly this class of gap. **Probe it; the plan's own "probe the API, don't
  assume it" rule covers this and it is the first place it will bite.**
- **SWIG spelling of the `ZONE_CONNECTION` enum** in Python
  (`ZONE_CONNECTION_THT_THERMAL` vs `ZONE_CONNECTION.THT_THERMAL`). Probe.
- **The KiCad version that introduced `net_tie_pad_groups`.**
  `dev-docs.kicad.org` is egress-blocked. Confirmed present and complete in
  `9.0.0` from source; the commonly-cited "7.0" is `[from memory]` and unverified.
- **74AHCT125 edge rate** (§8). No AHCT datasheet is banked in `datasheets/`. The
  58–117 MHz knee is `[from memory]` on a 3–6 ns transition. It does not change
  the conclusion (the board is electrically small either way) but it should be
  banked before anyone leans on it.
- **4-layer prototype cost** (§9). Vendor sites blocked. Unverified.
- **`FOOTPRINT::CheckNetTies()` hardcodes `{ F_Cu, In1_Cu, B_Cu }`**
  (`footprint.cpp:~3040`). On a 4-layer board a net tie's copper on In2 would not
  be validated. Noted, not chased — it does not affect a tie built from the stock
  footprints.
- **The `dac.kicad_pcb` precedent ties in two places**, one per layer. I cite it
  for the *idiom* (bridged solder jumper as net tie, abutting zone outlines,
  priority as tie-break) and explicitly not for its topology.
