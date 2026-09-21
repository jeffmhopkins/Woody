# PCB pipeline — schematic to a board you can route

**Status:** Proposed 2026-09-21, rewritten after a 13-agent review
(`docs/review/2026-09-21-pcb-pipeline-review/`). Not run.

**The handoff is routing.** Everything up to a placed, grouped, rules-configured
board is headless and re-runnable. You route it in KiCad. Everything after —
verification, gerbers, drill, the order package — is headless again.

That is not a compromise. Three cold reviewers reached it independently, and
one brought the number: against Freerouting's own benchmark, filtered to boards
like this one, it returns a fully routed board 36 % of the time and a
routed-*and*-clearance-clean one **19 %**. It also has no star ground, no
matched-pair support and no per-net via control — upstream's own documentation
says the only way to get a star ground is hand-route-and-lock, and calls that
fragile. There is no representation in the tool for this board's design thesis.

## What dropping the autorouter removes

Everything in this list was a real defect found by the review, and none of it
exists any more:

- Java 25 vs the installed 21; `--router.job_timeout` colon-format traps;
  `timeout` destroying the `.ses`; exit code 0 not meaning routed
- The Specctra round trip: arcs flattened to chords, `.kicad_dru` never
  exported, an `smd_smd` clearance deliberately 4× looser than DRC checks
- **Unlocked pre-existing tracks freezing**, so run *n* only fills gaps left by
  run *n−1* — the stage was never re-runnable
- A smoke test for locked tracks that passes either way and proves nothing
- Non-determinism from a 1000 ms wall-clock cutoff inside the routing hot path
- The router ploughing through the `AGND` star because rule areas were created
  after the autoroute

## The stack

| Tool | Job | Status |
|---|---|---|
| **SKiDL** 2.3.0 | Circuit as Python → netlist, ERC | Verified: works with **no KiCad installed**, parses KiCad 9 libraries, ad-hoc parts need no library |
| **kinet2pcb** 1.1.4 + **hierplace** 1.1.0 | Netlist → placed `.kicad_pcb`, **grouped by design hierarchy** | Verified downloadable. This is the "everything in there and placed" step |
| **ngspice** 42 | Analog verification | Stock Ubuntu archive, no allowlist change |
| **KiCad 9** | Interactive routing, and `pcbnew` for outline/classes/zones | Needs `*.kicad.org` **and** `api.launchpad.net` allowlisted |
| **KiBot** 1.9.1 | DRC/ERC preflights, fab output, the zip | Replaces hand-rolled `kicad-cli`, which the review found nobody's commands would even parse |

**Dropped:** Freerouting (above) and `kiutils` — abandoned since 2024, and named
for a job SKiDL's own `generate_schematic()` already does.

**Do not use PySpice.** 1.5 fails against ngspice 42: it treats every
non-`Warning:` stderr line as fatal and ngspice prints a solver banner to
stderr on every run. Use raw netlists plus `subprocess`. TI macromodels also
need `set ngbehavior=psa` in `.spiceinit` — inside `.control` is too late.

---

## Precursors that bite at the netlist, not the board

Only the ones that corrupt something no later stage can catch.

**1. Reconcile net names across the six pages first.** `AGND` means the
umbilical sense conductor *and* the module analog return. `BREATH` means the
in-amp input *and* the output jack. **Three cold reviewers found this
independently.** A transcription taking names off the drawings shorts the
breath in-amp input to the breath output jack — and every downstream check
passes, because the merge happened before anything could see it.

**2. One `rails.py`, and `Net.fetch` only.** `Net("+12V")` *constructs*. Two
modules naming the same rail give `+12V` and `+12V1`, electrically separate,
reported as two warnings among hundreds. Seven rails, six modules. Assert no
net name ends in a digit.

**3. Explicit `ref=` and `tag=` on every part.** Auto-refdes are positional, so
inserting one resistor renumbers everything after it — and KiCad matches by
reference, so a re-import silently misassigns downstream footprints.

**4. ERC does not fail the build.** SKiDL exits 0 with errors and writes the
netlist anyway. Check `erc_logger.error.count` explicitly.

**5. `U-TVS-SPI` is SOT-23-**5**, not -6.** The 4-channel SP0504BAHT has five
pins, so this is a **netlist** change, not just a footprint. `SP0505BAHTG` is
the genuine -6 with a fifth channel if the footprint matters more than the
channel count.

**6. `ref5050-grade` is disputed and may change the part.** `REF5050AIDR` is
the *Standard* grade — ±0.1 %, 8 ppm/°C — not the ±0.05 % / 3 ppm/°C the corpus
asserts in three places. `REF5050IDR` is the High grade: same package, same
pinout, one letter. So this blocks precursor 1 for that row, not just the
figures list.

## Three ground questions that must be decided in one sitting

Each is "which ground does this attach to", each is invisible to
`check-staleness.py` because it is semantic, and **all three are downstream of
2-layers-or-4**:

- **`dig-gnd-topology`** — three documents, three mutually exclusive answers,
  and `power-entry.md` states ADR 0004 was corrected when it was not.
- **The LT5400's exposed pad.** The part is MS8E with a **1.88 × 1.68 mm
  exposed pad** the BOM did not know it had. ADI says do not tie it to noisy
  ground and *"connecting the exposed pad to a quiet AC ground is
  recommended"* — and **pad-to-resistor coupling is 5.5 pF against only 1.4 pF
  resistor-to-resistor**, so the pad is the dominant stray on the 1 V/oct
  network. This plan gives `AGND` no zone and a keepout, so "a quiet AC ground"
  has to mean something specific here.
- **`cref-out-node`** — three drawings disagree about which side of the
  reference buffer `C-REF-OUT` sits on.

A pad told to find "a quiet AC ground" on a board that has not settled where
its grounds meet is a decision deferred twice, not once.

---

## Stages

### 1. Netlist — headless, re-runnable

`pcb/src/module/*.py`, one module per schematic page, `module.py` importing the
six. ERC, then emit `module.net`. Pass `track_abs_path=False` or the generating
script's absolute path lands in the netlist and two clones differ.

### 2. Simulate — headless, runs today

Independent of everything else; `ngspice` needs no allowlist change. Ranked by
what the claim costs if wrong:

| Sim | Why |
|---|---|
| **Breath-link CMRR** with the INA828 | 1.7 dB of claimed margin, unretrofittable inside a bonded body. A macromodel exists — same directory as the OPA2197 |
| **`R-ISO-REF` stability** | Already found the drawn circuit is the unstable one: 8.8° unfitted, **8.4° in-loop as drawn**, 75.2° out-of-loop. **And TI publishes the worked answer for this exact circuit** — SBOS737C §8.2.3, `R_ISO` 37.4 Ω with a dual-feedback network, 89° PM, against our 10 Ω. **Blocked on `cref-out-node` first** |
| **Pitch transient into a passive mult** | Measured 41.8 % overshoot at 82 nF, 65.4 % at 330 nF. **The AC sweep is structurally blind to this** on the same circuit at the same loads |
| **Power-on / reset transient** | Five power-on claims across three pages, no transient anywhere in the corpus |
| **Behavioural LT1641** | `power-entry.md` already writes the foldback law as equations, and this is the circuit proven not to start |

Not worth running: Monte Carlo on the pitch budget. The dispute is over *what
the terms are*, not their spread, and the two largest belong to a part with no
model.

**A simulated phase margin is a screen with a ±10° bar**, not a spec — TI's own
macromodel runs optimistic against TI's own tabulated figures. Results land in
`config/figures.yaml`; `.LIB` files get banked in `datasheets/` with SHA-256
like every other document.

**Two numbers to check any EMC or stability work against**, both corrected since
the corpus was written: the OPA2197's `Zo` is **375 Ω**, not the 75.8 Ω that was
back-solved — every pole derived from it moves ~5× the *wrong* way. And `FB-IN`
is **not 600 Ω where it matters**: `FB2` carries the umbilical at 359 mA and
reads ~280–310 Ω, half its nameplate, because a bead's current rating is
**thermal, not magnetic**.

### 3. Board bring-up — headless, **once per board**

```
circuit.generate_pcb(...)    # kinet2pcb: footprints placed, nets assigned,
                             # hierplace groups by module = by schematic page
```

Then `build_board.py` adds what `kinet2pcb` does not:

- **Board outline** on `Edge.Cuts`
- **Net classes** — `kinet2pcb` creates none, and they are what makes
  interactive push-and-shove pleasant. Derive the power width from IPC-2221:
  0.25 mm is 0.875 A and 0.50 mm is 1.447 A at a 10 °C rise, against a
  **0.940 A** limit — so the *default* class is the marginal one, not the power
  class
- **`.kicad_dru`** — interactive routing honours it, so the rules you route
  against and the rules DRC checks are the same file
- **Mechanically fixed parts** — connector, jacks, pots, toggle, LED, locked to
  panel geometry
- **Zone outlines, unfilled.** Zone priorities do *not* keep two grounds apart:
  different-net zones are separated by clearance at any priority, and what
  priority selects is which zone gets knocked out entirely. **The partition is
  the outline geometry.** Draw the outlines; leave filling to you
- **A net tie at the star.** Without one, a track joining two grounds is
  `DRCE_SHORTING_ITEMS` at ERROR and DRC fails a *correct* board

**Save the project file.** Net classes live in `.kicad_pro`, not the board —
`SaveBoard(aSkipSettings=True)` silently discards every trace width.

### 4. You route it

Open `pcb/module/module.kicad_pcb` in KiCad 9. Everything is in there, grouped
by schematic page, with the widths and rules already set.

**Hand-route these first**, because nothing else in the pipeline protects them:

- `VREFOUT`, `V_ref`, the three trimmer wipers, the mods' shared 3.3333 V —
  **1 mV on `V_ref` is 1.2 cents**, which equals or exceeds every candidate in
  the disputed pitch budget. These were the nets the old plan left to the router
- `BREATH` / `AGND` from the connector to the in-amp — one keepout window
  enclosing **both** legs, not one each, or the pour asymmetry costs the
  capacitive matching the ±1 % spec exists to control
- `PWR_GND` as a **trace, not a pour** — it is a two-terminal net whose own IR
  drop is irrelevant and which must share copper with nothing
- `SENSE` / `R-ILIM` as a Kelvin pair — 47 mV across 50 mΩ, so 1 mΩ of trace is
  a 2 % shift in the current limit
- The pitch feedback loop: tap at the jack, compensation cap from the op-amp
  *output*, protection resistor inside the DC loop

**Star pad solid, everything else thermal.** A default 4-spoke relief on the
star pad costs 0.053 cents at 359 mA — a quarter of the tightest pitch-budget
candidate, from one DRC-passing pad.

### 5. The update loop — and why it works here

Headless netlist import **does not exist**: the updater's only constructor
takes a `PCB_EDIT_FRAME*`, so it is structurally GUI-bound, and `kicad-cli pcb`
has no import verb. The SWIG bindings are also removed in KiCad 11.

**None of that blocks this workflow, because you are in the GUI.**
`File → Import → Netlist` updates the board in place and preserves your
routing. So: change a SKiDL module, re-run stage 1, import the netlist, route
the delta.

The `.kicad_pcb` is the **artifact of record** and is committed. Stage 3 runs
once per board. "Re-runnable" honestly means stages 1, 2 and 5 — all
read-only or idempotent.

### 6. Verify and ship — headless again

KiBot handles DRC preflights, `check_zone_fills`, fab output and the zip, with
vendor presets encoding the gerber precision and drill format this document
cannot currently state. It also already solves the `fp-lib-table` problem.

Assertions worth keeping beyond DRC, because each passes DRC on its own:

- board netlist **equals** the SKiDL netlist, ref by ref
- the four returns still distinct — `PWR_GND`, `DIG_GND`, the module analog
  return, and `AGND` which **is not a ground at all**
- `DRCE_ISOLATED_COPPER` defaults to **WARNING**, so an orphaned pour survives
  `--severity-error`; and default island removal *deletes* partly-orphaned fill
  with no diagnostic
- **check the output file list** — an invalid `--layers` token is reported and
  then ignored, exit 0, so a misspelt `F.Mask` gives a board with no soldermask
  and a green build
- verify the **zip**, not the board directory; every check in the old plan sat
  upstream of the thing actually being shipped

**The board is hand-assembled**, so no pick-and-place, no fab BOM format, no
rotation-correction table. Gerbers and drill. Add an interactive HTML BOM —
that is the artefact that helps *you*, and it runs headless.

## Two things that are not this pipeline

**The 10HP panel is 2 mm aluminium**, laser or waterjet from DXF, same vendor
and order as the key plate. Not a PCB. It belongs with the mechanical work.

**Open: 2 layers or 4.** On two layers, two corpus requirements are mutually
exclusive — `power-entry.md` wants the SPI return directly under its trace while
ADR 0004 wants `PWR_GND` on its own copper *and* the analog return as its own
region. Four layers dissolves it. This is a cost decision and it gates the
grounding scheme, so it is upstream of stage 3.

## One warning about reading `datasheets/` programmatically

**Several key documents have no text layer at all.** Gateron's switch drawing,
both Laird bead drawings, the Neutrik outlines and the TE socket page are vector
CAD — `pdftotext` returns a byte or two, and the dimensions exist only in the
picture. The plate thickness, the bead bias curve and the IDC stack height were
all obtained by rendering at 150 dpi and looking.

So any script that pulls a dimension out of `datasheets/` **will silently get
nothing** from exactly the documents that carry the mechanical constraints.
Render and read, or do not automate it.

Related: `WS2815` is banked twice under two paths with the same SHA-256, from
two different researchers. Harmless, but manifest-driven tooling should expect
it.

## Install

`kicad` plus its closure is **695 MiB**. `kicad-packages3d` is **5.44 GiB** and
is only needed for `export step` and `render` — split those from the fab
deliverable. Name the Python interpreter by **explicit minor version matching
the deb**: `python3` here is 3.11 and so is `/usr/bin/python3`, while `pcbnew`
wants 3.12. Do not set `PYTHONPATH=/usr/lib/python3/dist-packages` — it is
already on `sys.path`, so it converts a clean `ImportError` into an ELF error.
