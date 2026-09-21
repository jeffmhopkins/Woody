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

**1. Reconcile net names across all 23 circuit pages first** — twelve of them
on the module. (This said "the six pages" until 2026-09-21; Phase B split the
six module pages into twelve circuit directories plus the board-crossing
blocks, and each new page names nets of its own.) **Four collisions are known,
each a name that denotes two different physical nets:**

| Name | Means | And also means |
|---|---|---|
| `AGND` | the umbilical sense conductor | the module analog return |
| `BREATH` | the in-amp input | the output jack |
| `OE` | the module's `74AHCT125` output enable, tied to `GND` (`hardware/module/digital-and-supervision/digital-and-supervision.md`) | the carrier's LED-buffer output enable, tied low (`hardware/carrier/led-strip-drive/led-strip-drive.md`) |
| `CS` | the umbilical SPI chip select, `HDR-DEV` IO34 → `J-UMB` pin 7 → the DAC (`hardware/interfaces/spi-link/spi-link.md`) | the MCP3202's board-local chip select, IO39, which never leaves the carrier (`hardware/carrier/breath-adc/breath-adc.md`) |

**Three cold reviewers found the first two independently**; `OE` and `CS` came
out of the pre-merge wave. A transcription taking names off the drawings shorts
the breath in-amp input to the breath output jack — and every downstream check
passes, because the merge happened before anything could see it. `CS` is the
worse of the two new ones: **both of its nets are on the carrier**, so it does
not even need the umbilical to collide, and `carrier.md` already draws the host
as "SPI2 + 2×CS".

**2. One `rails.py`, and `Net.fetch` only.** `Net("+12V")` *constructs*. Two
modules naming the same rail give `+12V` and `+12V1`, electrically separate,
reported as two warnings among hundreds. Seven rails, and now one SKiDL module
per circuit page rather than six in total. Assert no net name ends in a digit.

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

`pcb/src/module/*.py`, **one SKiDL module per circuit directory — twelve of
them under `hardware/module/`, not the six pages this said before Phase B** —
and `module.py` importing all twelve. ERC, then emit `module.net`. Pass
`track_abs_path=False` or the generating script's absolute path lands in the
netlist and two clones differ.

> **A page-by-page netlist is not the whole board, and `hardware/unplaced.csv`
> is the measure of the gap.** A row lives with the circuit whose page derives
> it; a row nobody has drawn lives in `unplaced.csv`, so anything transcribed
> from the pages alone omits exactly those rows. **Re-measured against the
> current tree, 2026-09-21:**
>
> | | Rows | Units |
> |---|---|---|
> | `hardware/bom.csv`, the generated master | 138 | 388 |
> | In the 23 per-circuit fragments | 104 | 313 |
> | **In `hardware/unplaced.csv` — no page names them** | **34** | **75** |
>
> Of those 34, five are module-board netlist parts and would be missing from
> `module.net`: **`J-CV` ×6** (the CV jacks — the module's whole output
> connector set), `U-TVS-MODULE`, `D-CLAMP-BREATH` ×2, `R-BREATH-SUM` ×2 and
> `R-BREATH-OFF` ×2. **Thirteen units.** The rest of `unplaced.csv` is the
> instrument's mechanical and controller rows plus the board blank itself,
> which no netlist wants.
>
> `D-CLAMP-BREATH` is the shape of the problem: it **is drawn**, on
> `hardware/module/breath-receive-stage/breath-receive-stage.md`, and its row
> still sits in `unplaced.csv`. Drawn and placed are not the same test, and
> only the BOM fragment answers the second one.
>
> *This warning used to say ~50 rows / 105 units, and that the emitted module
> would have no DAC8568, no CV jacks, no etherCON and no AVDD rail. Sixteen
> rows have since been moved into the circuits that derive them, so the DAC
> (`hardware/module/dac8568/bom.csv`), the etherCON chassis connector and the
> `U-REG-DAC` AVDD regulator (`hardware/module/power-entry/bom.csv`) are all
> placed now. **The CV jacks are not**, and neither are the four rows beside
> them.*

### 2. Simulate — headless, runs today

Independent of everything else; `ngspice` needs no allowlist change. Ranked by
what the claim costs if wrong:

| Sim | Why |
|---|---|
| **Breath-link CMRR** with the INA828 | 1.7 dB of claimed margin, across two boards. A macromodel exists — same directory as the OPA2197. **See the note below: the premise that used to rank it first is retired** |
| **`R-ISO-REF` stability** | Already found the drawn circuit is the unstable one: 8.8° unfitted, **8.4° in-loop as drawn**, 75.2° out-of-loop. **And TI publishes the worked answer for this exact circuit** — SBOS737C §8.2.3, `R_ISO` 37.4 Ω with a dual-feedback network, 89° PM, against our 10 Ω. **Blocked on `cref-out-node` first** |
| **Pitch transient into a passive mult** | Measured 41.8 % overshoot at 82 nF, 65.4 % at 330 nF. **The AC sweep is structurally blind to this** on the same circuit at the same loads |
| **Power-on / reset transient** | Five power-on claims across three pages, no transient anywhere in the corpus |
| **Behavioural LT1641** | `power-entry.md` already writes the foldback law as equations, and this is the circuit proven not to start |

> **The CMRR row's stated reason was refuted and the ranking survives on a
> different one.** It read *"unretrofittable inside a bonded body"*. ADR 0009
> retired the bonded body — it comes apart on six fasteners — and `R1b`, the
> part the 60.2 dB term is entirely a statement about, is on the carrier inside
> that body. So it *is* retrofittable, and the argument that put this sim first
> is gone.
>
> It stays first on three weaker grounds, stated so the next reader can
> disagree with the real ones: it is the **thinnest claimed margin in the
> corpus** (1.7 dB, and a worst case over tolerance rather than a typical); its
> derivation is the only one that **crosses the umbilical**, so a bench
> iteration on it spans two boards and a 2 m cable rather than one bench; and
> the sim costs nothing, because the macromodel is already banked. If any of
> those stops being true, re-rank it.

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
                             # hierplace groups by SKiDL module, which is now
                             # one circuit directory, not one schematic page
```

**That grouping is finer than it used to be.** Twelve groups on the module
instead of six, and the two that a router wants adjacent — `dac8568` and
`digital-and-supervision` — are now separate groups because they are separate
directories. Expect to move whole groups by hand once, before routing.

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

**Some documents have no text layer, and which ones is not what this page used
to say.** `repo-maintenance.md` §3 carries the measured survey across all 60
banked PDFs and the two extraction routes that work in this container; read it
before writing anything that pulls a dimension out of `datasheets/`. The three
things that matter here:

- **Genuinely textless**, 0 characters: `datasheets/connectors/NE8FDP.pdf`,
  `datasheets/connectors/NE8MC.pdf`, `datasheets/connectors/PJ301M-12.pdf`.
  Both Laird bead drawings give up a title block and nothing else, so the bead
  bias curve really does only exist as a picture.
- **The TE socket catalogue and the NKK toggle sheet are fully extractable**,
  dimensions included. This page said otherwise and was wrong.
- **Prefer a companion file to a render.** For the etherCON panel cut-out, do
  **not** send anyone to `NE8FDP.pdf` — it extracts nothing.
  `datasheets/connectors/NE8FDP.dxf` is banked beside it with a complete
  `TEXT`/`MTEXT` layer carrying every dimension the corpus derives from that
  connector: the bore, the two ⌀3,2 clearance holes and their pitch, the flange
  and both depths behind the panel, all with tolerances, in a decimal-comma
  German drawing. Every number the corpus took off the render checks out
  against it. The DXF's *geometry* entities are to drawing scale and rotated
  per view, so read the text layer, not the coordinates.

  `hardware/module/power-entry/bom.csv`'s `J-UMBILICAL` row is where those
  dimensions live; this page cites them rather than restating them.

So a script that pulls a dimension out of `datasheets/` **can silently get
nothing** — from a shrinking, now-named list. Check the document, do not assume
the class.

Related: `WS2815` has **two manifest rows from two different researchers, both
now pointing at the same file**, `datasheets/led/WS2815.pdf`. (It used to be two
rows at two *paths* with the same SHA-256; the duplicate under `mechanical/` was
de-duplicated by the 2026-09-21 re-filing.) Harmless, but manifest-driven
tooling should expect a repeated path.

## Install

`kicad` plus its closure is **695 MiB**. `kicad-packages3d` is **5.44 GiB** and
is only needed for `export step` and `render` — split those from the fab
deliverable. Name the Python interpreter by **explicit minor version matching
the deb**: `python3` here is 3.11 and so is `/usr/bin/python3`, while `pcbnew`
wants 3.12. Do not set `PYTHONPATH=/usr/lib/python3/dist-packages` — it is
already on `sys.path`, so it converts a clean `ImportError` into an ELF error.
