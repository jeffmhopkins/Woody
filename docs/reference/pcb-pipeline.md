# PCB pipeline — headless KiCad, schematic to fab

**Status:** Proposed 2026-09-21. **Not started.** This page is the procedure and
the objections to it; it is not a record of anything having been run.

The pipeline is meant to be re-runnable end to end, with every script in the
repo. That part is right and is why this page exists rather than a chat message.

---

## Before anything: this project is not one board and not one schematic

The source procedure said "turn the circuit in `schematic.md` into a PCB". There
is no `schematic.md`. There are **eight schematic pages** describing **six
physical boards**, and they are fabricated at two different milestones.

| Board | Pages | Milestone | Size |
|---|---|---|---|
| **Module CV interface** | `module/power-entry`, `digital-and-supervision`, `pitch-stage`, `mod-channels`, `breath-receive-stage`, `breath-output-stage` | **E12** | 2-layer, ~45 × 110 mm, 1.6 mm |
| **Module panel** | ADR 0004 | E12 | 10HP, **50.50 × 128.5 mm** |
| **Carrier** | `controller/carrier.md` | E13 | 2-layer, passive |
| **Cluster ×4** | `controller/cluster-boards.md` | E13 | one 74HC165 each |

**Run the pipeline once per board.** ROADMAP is explicit that the carrier *will*
spin at least once, so the module goes first — it is the one closest to
layout-ready.

---

## The gate: a board whose parts are not chosen cannot be laid out

Counted 2026-09-21 against `hardware/bom.csv`:

| | rows | `open` | `candidate` | `selected` | part or package still `TBD` |
|---|---|---|---|---|---|
| Module (E12) | 61 | 13 | 45 | 2 | **7** |
| Controller (E13) | 58 | 17 | 32 | 4 | 3 |

**Six of the module's seven `TBD` rows are footprint-determining**, and five of
those are blocked on one document:

| Row | Why it blocks layout |
|---|---|
| `C-TIMER-LOADSW` | 365 nF or 9.4 µF — an 0805 or an electrolytic. Different footprint entirely |
| `C-GATE-LOADSW` | ~83 nF, on a typical with no min/max |
| `R-FB-HI` / `R-FB-LO` | Values unset; the divider does not exist on any drawing yet |
| `J-UMBILICAL` | etherCON **variant** undecided (chassis vs PCB-mount changes the footprint and the board notch) |
| `R-PRECISION` | **LT5400 MS8E may have an exposed pad.** `bom.csv`'s package field says plain MSOP-8. Layout-blocking and flagged as such |

All five clear when `164112fc.pdf` and `5400fc.pdf` land.

**Do not start the module layout until those rows are `selected` and their
packages are real.** Everything else in this pipeline is cheap to redo; a
placement built around a wrong footprint is not.

---

## Objection 1 — a single GND pour destroys ADR 0004

> *"Add a GND pour (bottom layer, or both on 2-layer), fill all zones."*

**This board has three grounds that must not be merged.** ADR 0004's star rule:
one origin at the power inlet, `PWR_GND` and `DIG_GND` each on their own copper,
and **`AGND` is not a return at all** — it is a sense reference that carries no
current, which is the whole reason the analog breath channel survives two metres
of cable (ADR 0003).

A naive pour ties all three together. The board would pass DRC, fabricate, and
quietly throw away the most carefully argued decision in the project — and the
module's own ground is already the largest *live* error term in the pitch budget
at 5.7–7.2 cents.

**So:** pour `PWR_GND` and `DIG_GND` as separate zones with a single deliberate
tie at the inlet, and give `AGND` a routed star, never a zone. Add a check that
the three nets are still distinct after every fill.

## Objection 2 — the toolchain is not installable here today

Probed 2026-09-21 from this sandbox:

```
kicad-cli          ABSENT       java               PRESENT
python3 -c import pcbnew   ModuleNotFoundError

kicad.org                  000  blocked
ppa.launchpadcontent.net   000  blocked   ← where KiCad 8/9 .debs actually live
archive.ubuntu.com         200  reachable → kicad 7.0.11+dfsg-1build4 ONLY
github.com / objects.githubusercontent.com   reachable → Freerouting .jar is fine
```

**KiCad 7 has no `kicad-cli pcb drc`** — the DRC and ERC CLI arrived in KiCad 8.
Step 5 as written cannot run on what apt will install.

**Fix:** add `*.kicad.org` and `ppa.launchpadcontent.net` to the environment's
Custom network allowlist, alongside the vendor domains. Then KiCad 9 installs
normally. Verify `kicad-cli version` **and** `kicad-cli pcb drc --help` before
writing a line of anything else.

## Objection 3 — the highest-risk step has no check on it

Parsing hand-drawn ASCII schematics into a netlist is the single most
error-prone thing in this plan, and the procedure treats it as routine. DRC does
not check it: **DRC checks geometry, not intent.** A board wired wrong passes
DRC perfectly.

Two changes:

1. **Generate the `.kicad_sch` first, not "if you can do it reliably".** It is
   the priority, not the PCB. It buys ERC and `--schematic-parity`, and it puts
   the netlist in the form this project already knows how to review.
2. **Gate on a cold netlist review before any copper.** One agent that has not
   seen the extraction, diffing the netlist against the eight schematic pages
   node by node. This project files findings node-indexed precisely because that
   is the unit that matters — and its history is ninety defects of exactly this
   shape, including a DAC clear that would have pinned four jacks to +11.45 V
   and an `FB` pin connected to nothing.

## Objection 4 — autorouting is wrong for an enumerable set of nets

Not wrong for the board. Wrong for these, none of which Specctra can express:

- **`AGND`** — must stay a sense-only star. Freerouting will treat it as a net.
- **`BREATH` / `AGND` pair** from the etherCON to the INA828 — CMRR-critical,
  wants matched parallel routing. 60 dB of rejection was already spent on one
  unmatched resistor.
- **`PWR_GND` vs `DIG_GND`** — see Objection 1.
- **Pitch feedback** — `R2`/`TRIM-GAIN` tap at the **jack**, `C-FB-PITCH` from
  the op-amp **output** to the (−) input, `R-OUT-PROT` **inside** the DC loop.
  The netlist gets this right; the *loop area* is a layout judgement.
- **The load-switch power path** — 1 A, and the FET's thermal pad.

**So:** hand-route the critical list first, **lock those traces**, then let
Freerouting do the remainder, then verify the locked nets survived the import.

## Objection 5 — the footprint mapping must be durable

"List your choices" loses the mapping the moment the session ends, and the next
run re-derives it differently. That is this project's named failure mode.

**Add a `footprint` column to `hardware/bom.csv`** (12 columns; update
`CLAUDE.md` and `tools/check-staleness.py`'s column check in the same commit).
The mapping then lives where the part lives and the checker guards it.

**Prefer the footprints already banked in `datasheets/`** over guesses at
KiCad's standard libraries — several of these parts have no standard footprint:

| Part | Banked |
|---|---|
| Gateron KS-33 | two community footprints + a STEP solid |
| PJ398SM | `Jack_3.5mm_QingPu_WQP-PJ398SM_Vertical`, pads **named**, cross-checked against Thonk's drawing |
| Neutrik etherCON | `NE8FDV.kicad_mod` — **community, not vendor data**, flagged in the manifest |
| Eurorack panel | a real shipped 3HP panel, with the 3.2 × 6.2 mm slot geometry |

`MANIFEST.csv` records which are vendor-issued and which are community-authored.
That distinction has to survive into the layout.

## Objection 6 — "zero DRC errors" is necessary, not sufficient

Add explicit post-route assertions, because each of these passes DRC:

- net count matches the netlist; **no two nets merged**
- `AGND`, `PWR_GND`, `DIG_GND` still distinct; `AGND` tied exactly once
- every decoupling cap within ~2 mm of the pin it serves
- the locked critical nets unchanged from before the autoroute
- no copper under the etherCON bore or the panel cutouts

## Objection 7 — generated output must stay out of the staleness corpus

`hardware/**` is scanned by `tools/check-staleness.py`. Gerbers, `.ses` files and
netlists dumped there would be scanned as design documents.

**Put fab output in `fab/<board>/`** at the repo root, or add an `EXCLUDE` entry.
Decide before the first run, not after.

## Objection 8 — the panel is missing from the plan

The module ships a **10HP panel**, 50.50 × 128.5 mm, carrying the ⌀24.0 mm
etherCON bore, six jacks, three pots, a toggle and an LED. It is a separate
fabricated item with a mechanical relationship to the PCB, and its mounting
slots are **3.2 × 6.2 mm obround at y = 3.0 / 125.5, x = 7.5** — measured off a
real shipped panel, banked in `datasheets/mechanical/`.

It is the same pipeline with an Edge.Cuts job and no routing. Produce it in the
same run, and check it against the PCB in one assembly.

---

## Revised procedure

0. **Check the toolchain installs** (Objection 2). Stop and name the domain if not.
1. **Pick one board.** Module first.
2. **Confirm its BOM rows are `selected` with real packages.** Stop if not.
3. **Extract the netlist** from that board's schematic pages → `netlist.json`.
   Flag every ambiguity in one batch rather than asking serially.
4. **Generate `.kicad_sch`**, run ERC.
5. **GATE: cold netlist review**, node-indexed, against the schematic pages.
6. **Choose footprints**, write them into `bom.csv`'s new column.
7. **Place** — decoupling at the pins, groups per the schematic pages, high
   current and switching paths short.
8. **Hand-route and lock** the critical nets (Objection 4).
9. **Autoroute the rest** — Specctra out, Freerouting, Specctra in.
10. **Pour `PWR_GND` and `DIG_GND` separately; star `AGND`** (Objection 1).
11. **Verify**: DRC + ERC + parity + the assertions in Objection 6. Five
    iterations, then stop and explain.
12. **Export** Gerbers, drill, BOM, pick-and-place, per-layer SVG, 3D render →
    `fab/<board>/`, zipped.
13. **Report**: DRC summary, footprint choices, and what a human must check by
    hand — power paths, the breath pair, the star ground, thermal.

## What the fab rules should say

Not yet decided. `JLCPCB` 2-layer standard (0.15 mm trace/space, 0.3 mm drill) is
the obvious default and matches the "outsourced, no in-house capability"
constraint in ADR 0009. Default trace 0.25 mm, power nets 0.5 mm+. **Confirm
against the load switch's 1 A path before committing** — 0.5 mm of 1 oz copper
is about a 1 A trace at a 10 °C rise, which is no margin at all.
