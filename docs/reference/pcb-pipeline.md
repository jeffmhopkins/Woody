# PCB pipeline — headless KiCad, schematic to fab

**Status:** Proposed 2026-09-21. **Not started, and not startable yet** — see
*Readiness* below. This page is the procedure; it is not a record of anything
having been run.

Assumes a sandbox whose network policy allows `*.kicad.org` and
`ppa.launchpadcontent.net` alongside the vendor domains, so KiCad 9 installs.
On Ubuntu noble's stock archive you get KiCad **7**, which has no
`kicad-cli pcb drc` — that arrived in KiCad 8, and step 11 depends on it.
Freerouting's `.jar` comes from GitHub and is fine either way.

---

## Four boards, not one

There is no `schematic.md`. Eight schematic pages describe **four fabricated
items**, at two milestones.

| Item | Source pages | Milestone | Geometry |
|---|---|---|---|
| **Module PCB** | `module/` × 6 | E12 | 2-layer, ~45 × 110 mm, 1.6 mm |
| **Module panel** | ADR 0004 | E12 | 10HP, **50.50 × 128.5 mm**, ⌀24.0 bore, slots 3.2 × 6.2 mm obround at y = 3.0 / 125.5, x = 7.5 |
| **Carrier** | `controller/carrier.md` | E13 | 2-layer, passive, hard against the key plate |
| **Cluster ×4** | `controller/cluster-boards.md` | E13 | one 74HC165 each, 14 mm switch cutouts set by the plate DXF |

Run the pipeline **once per item**, module first. ROADMAP is explicit that the
carrier will spin at least once, and E13 sits after E12 deliberately.

## Where things go

`tools/check-staleness.py` scans `hardware/`, `docs/decisions/`,
`docs/reference/`, `config/`, `firmware/`, `README.md`, `ROADMAP.md`. Nothing
else. So putting the pipeline at the repo root keeps generated files out of the
design corpus **with no checker change**:

```
pcb/
  scripts/            shared: extract.py, build_board.py, route.py, verify.py
  module/             module.kicad_pro .kicad_sch .kicad_pcb netlist.json
  module-panel/
  carrier/
  cluster/
fab/
  module/             gerbers, drill, bom.csv, cpl.csv, svg/, module-fab.zip
  module-panel/  carrier/  cluster/
```

One rule: **nothing generated goes under `hardware/`.** That directory is
reviewed prose and the checker treats it as such.

---

## Readiness — none of the four is layout-ready today

This is the part a better sandbox does not fix.

### Module PCB — closest

**Assume the datasheets land.** That clears three blockers outright and
converts a fourth from unknown to arithmetic:

| Blocker | Datasheets clear it? |
|---|---|
| `C-TIMER-LOADSW`, `C-GATE-LOADSW` | **Yes** — `164112fc.pdf` gives `I_TIMER` and `I_GATE`, so the values and therefore the packages follow |
| `R-PRECISION` package | **Yes** — `5400fc.pdf` says whether MS8E carries an exposed pad |
| `R-FB-HI` / `R-FB-LO` | **Values yes, drawing no.** The divider exists on no schematic page; it has to be drawn onto `power-entry.md` |
| `J-UMBILICAL` variant | **No — this is a decision.** The drawing gives both chassis and PCB-mount dimensions; it cannot tell you which to fit, and the choice changes the footprint *and* the board notch |
| **`TRIM-OFFSET` is not buildable as described** | **No — this is a redraw.** `V_ref` nominal *is* `VREFOUT` and a divider can only go below it, so the nominal sits at an end stop with no downward authority. The network has to put 2.500 V at mid-travel: divide `VREFOUT` and gain it back, or inject a bipolar correction |

And two layout decisions that no document makes:

- **The two-terminal trimmer's wiper strap.** `pitch-stage.md` says it plainly:
  *"That is a footprint decision, not a value."* Strap the wiper to one end so a
  dirty track degrades to a known resistance instead of an open circuit.
- **Entry bulk is 4 × 47 µF**, flagged as 2–5× the surveyed norm. Four large
  footprints are at stake, and shrinking them after placement is a re-place.

**So the remaining work is one schematic session, not a research problem:** pick
the connector variant, redraw `TRIM-OFFSET`, draw the `FB` divider, settle the
bulk count and the wiper strap. Then the module is layout-ready.

*(Resolved and ready: `R-BIAS-DAC` at the DAC pin, `R-LDAC` to `AVDD`,
`R-SPI-SER` ×3 at 100 Ω, `R-SPI-PULL` ×6, `D-REVPOL` ×3, `C-DECOUPLE` at 19.)*

### Module panel — disputed, but now derivable

`panel-height-budget` is **disputed** in `config/figures.yaml`, four candidates
from 97 to 124 mm, and ~110 mm usable is derived from nothing.

**The datasheets change this too.** It was filed as needing *a 1:1 paper check
with real parts* because nobody had dimensions. Four of the five control types
now have them — etherCON flange and depth, PJ398SM body and bushing, RV09 pot
body and lug span, and a 14 mm knob cap that `bom.csv` already calls the binding
constraint. The gap is the panel toggle, still `BLOCKED`, where the nearest
verified part is a usable proxy for row spacing and wrong by 0.35 mm on the hole.

So: **do the arithmetic against 128.5 mm, state a total, retire the dispute.**
Outline and ⌀24.0 bore are settled and can be cut now either way.

### Carrier — 11 open items, and one geometric

The KS-33 standoff finding says the board sits **hard against the plate
underside**, so every passive goes on the far face — but plate thickness is
still open, and that sets the exact offset. E13 is after E12 for good reason.

### Cluster ×4 — blocked upstream

Switch positions come out of the M2/M3 ergonomic iteration and the plate DXF.
The boards are fitted around an answer that does not exist yet.

---

## Procedure

### 0. Toolchain

`kicad-cli version`, `kicad-cli pcb drc --help`, `python3 -c "import pcbnew"`,
`java -version`. All four, before anything else. Stop and name the domain if a
download is refused.

### 1. Pick one item, and prove it is ready

Re-check its rows in `hardware/bom.csv`: every part `selected`, every `package`
real, no `TBD`. Re-read its pages' *Still open* sections and confirm none is
topological. **Stop here if not** — a placement built around a wrong footprint
is the one thing in this pipeline that is expensive to redo.

### 2. Extract the netlist

`pcb/scripts/extract.py` reads that item's schematic pages and writes
`netlist.json`: every component (ref, value, package) and every net.

Where the pages and `bom.csv` disagree, **the pages win on topology and the BOM
wins on parts** — that is the rule ADR 0006 already sets. Flag every ambiguity
in one batch rather than asking serially.

### 3. Generate the schematic, then run ERC

`.kicad_sch` **first**, not "if it works out". It buys ERC and
`--schematic-parity`, and it puts the netlist in the form this project already
knows how to review. The PCB is downstream of it.

### 4. GATE — cold netlist review

One agent that has not seen the extraction, diffing `netlist.json` against the
schematic pages **node by node**, filing findings node-indexed.

This gate exists because DRC checks geometry, not intent: a board wired wrong
passes DRC perfectly. Parsing hand-drawn ASCII into a netlist is the most
error-prone step here, and this project's history is ninety defects of exactly
that shape — a DAC clear that would have pinned four jacks to +11.45 V, an `FB`
pin connected to nothing.

### 5. Footprints, written down

Prefer what is already banked in `datasheets/` over KiCad's standard libraries —
several of these parts have no standard footprint:

| Part | Banked |
|---|---|
| Gateron KS-33 | two community footprints + a measured STEP solid |
| PJ398SM | pads **named**, cross-checked against Thonk's drawing |
| Neutrik etherCON | `NE8FDV.kicad_mod` — **community, not vendor data** |
| Eurorack panel | a real shipped 3HP panel with the slot geometry |

`MANIFEST.csv` records which are vendor-issued and which are community-authored.
**That distinction has to survive into the layout**, so put the choice where the
part lives: add a `footprint` column to `hardware/bom.csv` (12 columns — update
`CLAUDE.md` and the column check in `tools/check-staleness.py` in the same
commit). Otherwise the mapping is re-derived differently every run, which is
this project's named failure mode.

### 6. Place

Decoupling within ~2 mm of the pin it serves. Groups follow the schematic pages.
High-current and switching paths short. Then the item's own notes: etherCON
braced to the PCB and **rotated 90°**; USB-C and matrix window on the tail face;
the FET's thermal pad.

### 7. Hand-route and **lock** the critical nets

Specctra cannot express any of these, so they are routed before Freerouting sees
the board and locked after:

- **`AGND`** — a sense-only star. It carries no current and must never become a
  return. This is what makes the analog breath channel survive 2 m of cable.
- **`BREATH` / `AGND` pair**, etherCON to INA828 — CMRR-critical, matched and
  parallel. 60 dB of rejection was already spent on one unmatched resistor.
- **`PWR_GND` and `DIG_GND`** — separate copper, one tie at the inlet.
- **Pitch feedback** — `R2`/`TRIM-GAIN` tapped at the **jack**, `C-FB-PITCH`
  from the op-amp **output** to the (−) input, `R-OUT-PROT` **inside** the DC
  loop. The netlist gets this right; the loop *area* is a layout judgement.
- **The load-switch path** — 1.0 A. Note that 0.5 mm of 1 oz copper is about a
  1 A trace at a 10 °C rise, so **derive this width rather than defaulting it.**

### 8. Autoroute the remainder

`pcbnew.ExportSpecctraDSN` → `java -jar freerouting.jar -de board.dsn -do
board.ses -mp 100` (under `xvfb-run` if it wants a display) →
`pcbnew.ImportSpecctraSES`. Then **verify the locked nets survived the import**
before doing anything else.

### 9. Pour — three grounds, not one

> **A single GND pour ties `PWR_GND`, `DIG_GND` and `AGND` together and destroys
> ADR 0004.** It would pass DRC, fabricate, and silently throw away the most
> carefully argued decision in the project. The module's own ground is already
> the largest *live* term in the pitch error budget at 5.7–7.2 cents.

Pour `PWR_GND` and `DIG_GND` as **separate zones** with a single deliberate tie
at the power inlet. Give `AGND` a **routed star, never a zone.**

### 10. Verify — DRC is necessary, not sufficient

`kicad-cli pcb drc --format json --severity-error --schematic-parity`, plus ERC,
plus assertions that each pass DRC on their own:

- net count matches `netlist.json`; **no two nets merged**
- `AGND`, `PWR_GND`, `DIG_GND` still distinct; `AGND` tied exactly once
- every decoupling cap within ~2 mm of its pin
- the locked critical nets byte-identical to before the autoroute
- no copper under the etherCON bore or the panel cutouts

Five full iterations, then stop and explain. Export per-layer SVG and a 3D
render for review.

### 11. Fab output

Gerbers, drill, BOM, pick-and-place → `fab/<item>/`, zipped. Rules: JLCPCB
2-layer standard (0.15 mm trace/space, 0.3 mm drill), default trace 0.25 mm,
power nets derived per step 7.

### 12. Report

DRC summary and warnings. Footprint choices and which were community-authored.
And what a human must check by hand: the power path, the breath pair, the star
ground, the FET thermal.
