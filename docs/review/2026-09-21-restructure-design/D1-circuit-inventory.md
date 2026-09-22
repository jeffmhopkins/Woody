# D1 — Circuit inventory for the Phase A split

Agent D1, cold. Sources read: the eight schematic pages under `hardware/`,
`docs/reference/pcb-pipeline.md`, `CLAUDE.md`. No `docs/review/**`,
`docs/log/**` or `docs/research/**` was opened.

Provenance on every claim: `[repo]` path:line, `[calc]` with arithmetic shown.
Line ranges are inclusive and exclude the `---` rule that follows a section.
All ranges verified against heading and fence line numbers extracted with
`grep -n` / `awk` on the files as they stand today `[repo]`.

---

## 1. Proposed circuit directories — flat table

**22 circuit directories**, plus 2 flagged below as system-level rather than
circuit blocks (`grounding-and-returns`, `jack-output-protection`).

| # | Directory | What it does | Board(s) | Source line ranges |
|---|---|---|---|---|
| 1 | `power-entry-instrument` | Umbilical +12 V in; reverse shunt, TVS, two R-78E5.0 bucks, OR diodes, strip bulk, plate bond | carrier | `hardware/controller/carrier.md:82-159` |
| 2 | `breath-excitation-reference` | REF5050 5.000 V + compensated OPA2197 buffer (`R-ISO-REF`/`R-FB-REF`/`R-FBX-REF`/`C-FB-REF`) driving the sensor's `VS` | carrier | `carrier.md:236-313`; `hardware/module/breath-receive-stage.md:339-361` |
| 3 | `breath-sense-link` | MPXV4006DP → OPA2197 buffer → `R1`/`R1b` → 2 m pair → `R2`/`R3`/`C_diff`/`C_cm`/`R4`/`R5` → INA828 + `REF` trimmer buffer | carrier **and** module | `carrier.md:164-235`, `carrier.md:340-346`; `breath-receive-stage.md:17-255` |
| 4 | `breath-adc` | 0.6× divider, `C-AA-ADC`, MCP3202 CH0, `C-ADC-BULK` — the instrument's own copy of breath | carrier | `carrier.md:349-406`; MCP3202 clock `carrier.md:639-661` |
| 5 | `key-chain-loom` | The 2×6 alternating-ground chain bus: pinout, source resistors, `U-TVS-CHAIN`, `F-CHAIN`, 3V3 conductor, `LK-SER`/`R-SER-TERM` | carrier **and** 4 cluster boards | `carrier.md:439-562`; `hardware/controller/cluster-boards.md:237-309`; `cluster-boards.md:57-86` |
| 6 | `key-register` | 74HC165 device: pin map, `CLK INH` low, `QH_bar` open, `C-DECOUPLE-165`, bit order | 4 cluster boards | `cluster-boards.md:89-125` |
| 7 | `key-switch-network` | `R-KEY-PU` / `R-KEY-SER` / `C-KEY` + KS-33, ×21 positions, and its threshold/debounce derivation | 4 cluster boards | `cluster-boards.md:128-234` |
| 8 | `key-marker-and-bits` | The 8 hard-wired marker straps, their levels, and the 32-bit allocation | 4 cluster boards | `cluster-boards.md:312-419`; `carrier.md:563-588` |
| 9 | `led-strip-drive` | 74AHCT125 gates, `R-LED-PD`, `R-LED-SER`, `J-LED-L/R`, WS2815 `V_IH`/`BI` | carrier (loads off-board) | `carrier.md:683-757` |
| 10 | `spi-link` | SPI egress: 3 × `R-SPI-SER` 100 Ω, `U-TVS-SPI`, pin map/pairing, 6 × `R-SPI-PULL`, 74AHCT125 receiver | carrier **and** module | `carrier.md:591-631`; `hardware/module/digital-and-supervision.md:15-132` |
| 11 | `display-and-service-uart` | `J-DISP` 9-way UART loom + `HDR-SERVICE` 2×3 | carrier (far end undrawn) | `carrier.md:760-806` |
| 12 | `module-power-entry` | `D1`–`D3`, `FB1`–`FB4`, `C1`–`C4`, LM317 → 5.21 V AVDD; the four rails | module | `hardware/module/power-entry.md:10-124` |
| 13 | `umbilical-load-switch` | LT1641-1, `R-ILIM`, FB divider, `C-TIMER`/`C-GATE`, FET, `ON` pin | module | `power-entry.md:125-451` |
| 14 | `panel-led` | `R-LED-PANEL` 2.2 kΩ from +12 V analog, and the job it has lost | module | `power-entry.md:461-490` |
| 15 | `dac8568` | DAC8568C, `CLR`/`R-CLR-PU`/`LK-CLR`, `LDAC` 0 Ω strap, grade lock | module | `digital-and-supervision.md:245-273`; DAC portion of the drawing `digital-and-supervision.md:15-58` |
| 16 | `link-supervision` | Not fitted: deleted 74HC123 watchdog, deleted LM311 presence, and the costed restoration | module | `digital-and-supervision.md:133-219`, `:220-244` |
| 17 | `breath-response-shaper` | `POT-RESP` antiparallel-diode shaper, ÷2 inverting + ×2 restore | module | `hardware/module/breath-output-stage.md:169-276`, `:301-317` |
| 18 | `breath-output-stage` | Buffered attenuator (GAIN 0.5–4×) → fixed ×4 summer with bipolar OFFSET → jack | module | `breath-output-stage.md:1-166` |
| 19 | `pitch-stage` | Two-resistor non-inverting `2·Vdac − 2.5`, LT5400 1:1, split loop tapped at the jack, trims | module | `hardware/module/pitch-stage.md:1-309`, `:310-369` |
| 20 | `mod-channels` | Four × `4·Vdac − 3·V_ref`, `k = 3`, shared 3.3333 V from DAC ch7 + buffer | module | `hardware/module/mod-channels.md:1-259` |
| 21 | `pitch-offset-reference` | `VREFOUT` → `TRIM-OFFSET` + range resistors → OPA2197 follower → `V_ref` 2.500 V | module | `pitch-stage.md:92-123`, `:235-248` |
| 22 | `mod-offset-reference` | DAC ch7 → `R-OPAMP-IN` → OPA2197 follower → 3.3333 V to four channels | module | `mod-channels.md:151-209` |

Flagged as **system-level, not a circuit block** — they need a home under the
new axis and none of the 22 above is the right one:

| Directory | Why it cannot sit inside one block | Source line ranges |
|---|---|---|
| `grounding-and-returns` | `AGND`/`PWR_GND`/`DIG_GND`/analog star spans carrier, module and the umbilical; `pcb-pipeline.md` names three ground questions that must be "decided in one sitting" `[repo] docs/reference/pcb-pipeline.md:88-104` | `carrier.md:314-339`; `power-entry.md:491-503`; `carrier.md:120-121` |
| `jack-output-protection` | `R-OUT-PROT` 1 kΩ 1206 + `D-JACK-CLAMP` BAV99 + a jack-side filter cap recurs on all six outputs, stated six times in three files | `pitch-stage.md:124-156` (rows); `mod-channels.md:95-100`; `breath-output-stage.md:124-141`; `breath-receive-stage.md:154-167` |

---

## 2. Blocks that cross a board boundary

### 2.1 `breath-sense-link` — carrier ↔ module. **ONE directory.**

Sensor, excitation buffer output resistor `R1`, its twin `R1b`, the twisted
pair, the module's `R2`/`R3`, the RC filter, the bias pair and the INA828.

**Argument for one:** the block has a single transfer function and a single
error budget that no half can state alone.

- The 482 Hz differential pole is derived from 1 kΩ *in both legs*, one of
  which is on the other board — `[repo] breath-receive-stage.md:162`
  ("**482 Hz** differential pole (not 531 — `R1b` makes both legs 11 kΩ)").
- The CMRR budget is computed on the module page from an instrument-side
  part: `[repo] breath-receive-stage.md:214-217`
  (`|1M/1.011M − 1M/1.010M| = 9.79e-4 → 60.2 dB`).
- The gain derivation multiplies an instrument-side number by a module-side
  one — `[repo] breath-receive-stage.md:168-180`.
- The recorded failure is exactly the split: `R1b` is at qty 2 in `bom.csv`
  and the carrier drawing showed one — `[repo] carrier.md:220-235`. Two
  reviewers found it "from opposite directions" `[repo] carrier.md:217-218`.

Splitting this into `breath-sense/` and `breath-receive/` reproduces the
failure the restructure exists to prevent. One directory; the umbilical is an
internal net of the block, not a boundary.

### 2.2 `spi-link` — carrier ↔ module. **ONE directory.**

**Argument for one:** the value of the source resistor is decided by a voltage
measured at the *far* board. `[repo] carrier.md:617-621` tabulates the first
step at the far end against `V_IH` 2.0 V for 220 Ω / 100 Ω / 68 Ω, and
`carrier.md:623-625` rejects 68 Ω on the driving pin's 40 mA source spec — one
argument, two boards. The pull polarity is likewise stated once per end and
must agree: `carrier.md:713-715` points at the module's six pulls;
`digital-and-supervision.md:118-132` states them. And the pin-map/pairing
argument (`CS` paired with `DIG_GND`) is a cable fact
`[repo] digital-and-supervision.md:92-107`.

The DAC is **not** in this directory. Its arguments (`CLR` polarity, `LDAC`
strap, the C-grade lock) are about the converter, not the wire, and
`mod-channels.md:151-195` depends on them from a third page.

### 2.3 `key-chain-loom` — carrier ↔ 4 cluster boards (5 boards, 8 connectors).
**ONE directory.**

**Argument for one:** the pinout must be byte-identical at all eight positions
and is currently written twice — `[repo] carrier.md:455-497` and
`cluster-boards.md:241-245`. The eight-connectors-not-five conclusion is
derived on both pages from the same `SER`/`QH` point-to-point fact
(`carrier.md:485-492`, `cluster-boards.md:283-288`). `LK-SER`/`R-SER-TERM` on
the cluster page answers a question raised on the carrier page
(`cluster-boards.md:286-309` answering `carrier.md:485-491`). Two directories
would mean two copies of one pinout table — the exact shape of the project's
recorded failure.

Note the chain-order question (`cluster-boards.md:57-86`) belongs here and not
to the board page: it changes the bit allocation in `key-marker-and-bits`
(`cluster-boards.md:84-86`).

### 2.4 Umbilical +12 V — module `umbilical-load-switch` ↔ carrier
`power-entry-instrument`. **TWO directories.**

**Argument for two:** the two ends solve independent problems. The module end
is a start-up/foldback/SOA problem (`power-entry.md:125-451`); the instrument
end is an input-LC damping and regulator-derating problem
(`carrier.md:123-159`). They share exactly one quantity, the current, which is
a tracked figure.

**But one analysis genuinely spans both and must be assigned explicitly:** the
negative-resistance instability. `power-entry.md:506-510` leaves "damping the
input LC" open naming "2 m of cable and ~2 mF at the far end", while
`carrier.md:125-127` closes it "for the instrument end only". Assign the whole
LC analysis to `power-entry-instrument` and leave a cite at the load switch.
Do not let it live in two places.

### 2.5 `led-strip-drive` — carrier ↔ two WS2815 strips. **ONE directory.**
The strips are loads on a loom, not boards with pages. `C-STRIP-BULK` is
specified from `carrier.md:754-757`; it is on the carrier and feeds off-board.
No crossing to resolve.

### 2.6 `display-and-service-uart` — carrier ↔ display board. **ONE directory,
with a declared gap.** The far end has **no schematic page in the corpus**
`[repo]` (`hardware/` contains eight pages; none is a display board). The
9-way conductor list `carrier.md:778-806` is the only statement of that
interface, and `carrier.md:946-953` leaves buck B's location open, which
changes the conductor list. Keep it one directory and record that half the
block is undrawn rather than implying symmetry.

### 2.7 `breath-excitation-reference` — does **not** cross, but is described
from the far side. All four compensation parts are instrument-side
`[repo] carrier.md:236-313`, yet the module page carries 23 lines about them
(`breath-receive-stage.md:339-361`) because they set the number it multiplies.
That text moves to this directory; the module block cites it.

---

## 3. Content in the eight pages that is NOT circuit content

| Content | Source range | Where it belongs |
|---|---|---|
| Status / provenance preamble, sandbox-blocked-datasheets note | `carrier.md:1-24` | Board page `boards/carrier/` header |
| "One dev board, not two" — socket count, display board 360 mm away | `carrier.md:25-36` | Board page (what the board carries) |
| Block diagram of §1–§7 | `carrier.md:39-79` | Board page (which circuits it carries) |
| Mechanical rules: both sensor ports one side, mask before `MECH-COAT`, tube routing, `SKT-BREATH` reachability | `carrier.md:426-436` | Board page, mechanical section. Cite from `breath-sense-link` |
| The two SPI hosts + clock allocation + loop budget + IO_MUX note | `carrier.md:632-680` | **Split is unsafe — see §4.** Provisionally a system page `buses/spi-allocation` |
| §7 dev-board mounting, matrix window, USB-C edge alignment | `carrier.md:809-840` | Board page: outline, mounting, panel/tail-face geometry |
| Component table (whole) | `carrier.md:843-886` | Rows distribute to their blocks; `HDR-DEV`, `PCB-CARRIER`, `MECH-GNDBOND`, `TP-*`/`LK-*` rows are board-level |
| Loom conductor count table | `carrier.md:889-932` | Board page, loom section (it aggregates per-block counts) |
| "Still open", board-level items: dev-board face, board outline, buck B location, etherCON variant, test points, coating | `carrier.md:935-946`, `:947-957`, `:983-995` selectively | Board page. Circuit-specific items (`F-CHAIN`, MPXV4006DP P1 identity, `L-BUCK-IN` qty) go to their blocks |
| Cluster preamble: four boards, one circuit, variant table framing | `cluster-boards.md:1-23` | Board page `boards/cluster/` |
| Physical placement diagram, U-bolt band, left-hand-is-upper | `cluster-boards.md:26-56` | Board page (placement/mechanical) |
| §5 Mechanical: plate-then-switch-then-board, KS-33 footprint table, standoff, plate thickness | `cluster-boards.md:422-481` | Board page, mechanical. Footprint table cites `docs/reference/ks33-geometry.md` |
| Per-board component/variant table | `cluster-boards.md:484-504` | Board page (it *is* the variant table); part rows cite the blocks |
| Cluster "Still open": spare-switch placement, plate thickness, springs, coating | `cluster-boards.md:507-544` selectively | Board page; `R-KEY-PU` 2k2-vs-10k goes to `key-switch-network` |
| Grounding: `PWR_GND` origin, `DIG_GND` not starred, `AGND` is not a ground | `power-entry.md:491-503` | `grounding-and-returns` (system) |
| **The 10HP panel decision: 50.50 mm, three pots one row, ≤14 mm knobs, `panel-height-budget`** | `breath-output-stage.md:277-300` | **Module panel/board page.** This is panel geometry living inside a breath response-control section — the single most misfiled range I found |
| "What this redraw changed" — a record of a fix wave | `digital-and-supervision.md:59-117` | Keep with `spi-link` / `dac8568` as a corrections section. Do **not** move to `docs/log/` — `CLAUDE.md` §6 makes that history, and the checker excludes it |
| Commissioning procedure (3 steps) | `breath-receive-stage.md:269-293` | `breath-sense-link`, but it names GAIN and OFFSET which are block 18. Procedure page citing both |
| Trim procedure (highest note / lowest note / repeat) | `pitch-stage.md:249-276` | `pitch-stage`, procedure section |
| "What this settles" finding-resolution table | `breath-receive-stage.md:256-268` | Wave record, not corpus. Flagged — see §4 |
| Prior-art survey: four published designs, ADDAC310/NuEVI comparison | `mod-channels.md:210-250`; `breath-output-stage.md:170-178` | Keep with the block as "recorded rather than adopted" |

---

## 4. Ranges I cannot confidently assign

Four. Each needs a human call before Phase A touches it.

**4.1 `carrier.md:164-211` — one ASCII drawing, three blocks.** The figure
contains the REF5050 + compensated buffer (block 2), the sensor + buffer +
`R1`/TVS (block 3) and the divider + MCP3202 (block 4) in a single connected
drawing. `sed -n '164,211p'` cannot split it; splitting means redrawing, which
is not a move. **Recommendation:** the drawing goes whole to `breath-sense-link`
and blocks 2 and 4 cite it, or §2 stays one directory. Do not let an agent
redraw it under a content freeze.

**4.2 `carrier.md:632-680` — the two-SPI-hosts section.** Row `SPI2` belongs to
`spi-link` + `breath-adc`; row `SPI3` belongs to `key-chain-loom`; the loop
budget block (`:666-672`) costs both hosts in one code block and is cited by
`docs/reference/latency-budget.md` `[repo] carrier.md:643`. Splitting a
two-row table and a five-line budget is an edit, not a move.

**4.3 `carrier.md:407-425` — key pull-ups loading the ADC reference.** 25.8 mA
of key-scan current landing on `VDD`/`VREF` of the MCP3202. It is one fact
owned by neither `key-switch-network` nor `breath-adc`, and it is already
stated **twice in the corpus** — `carrier.md:407-425` and again at
`carrier.md:505-525`, with `cluster-boards.md:225-234` as a third statement of
the same trade. Whichever block takes it, the other two become citations; I
cannot pick the owner without knowing which reader the restructure is for.

**4.4 `breath-receive-stage.md:256-268` and `digital-and-supervision.md:232-244`
/ `:245-273`.** These are finding-resolution tables ("Finding | Resolution",
"Three bullets retired here"). They are review bookkeeping sitting inside
corpus files. `CLAUDE.md` §6 says `docs/review/**` is history and must never be
corrected, so moving them there freezes them; leaving them makes a circuit
directory carry a wave's scorecard. I am not resolving this — it is a policy
call, not an inventory one.

**Not a gap but worth stating:** `digital-and-supervision.md:133-219`
(`link-supervision`) describes circuits that **do not exist**. It is a
directory for parts that are not on the board. I have proposed it as a
directory anyway because `mod-channels.md:239-249` and
`breath-receive-stage.md:307-316` both still reason from the deletion, and
`CLAUDE.md` §5 names exactly this class as what the checker cannot catch.

---

## 5. Against `docs/reference/pcb-pipeline.md`

The pipeline expects `pcb/src/module/*.py`, "one module per schematic page,
`module.py` importing the six" `[repo] docs/reference/pcb-pipeline.md:115-118`.

**Does the proposal map cleanly? Partly — and the mismatch is informative.**

| Pipeline expectation | Under the new axis | Verdict |
|---|---|---|
| One `.py` per schematic page | One `.py` per **circuit block** | Improvement. SKiDL modules are arbitrary; `hierplace` "groups by design hierarchy" `[repo] pcb-pipeline.md:152`, so finer modules give finer placement groups |
| "the six" | Module-side blocks are **12**: #12–#22 plus `grounding-and-returns` `[calc]` (13, 14, 15, 16, 17, 18, 19, 20, 21, 22 = 10 circuit blocks, + `jack-output-protection`, + the module half of `spi-link` and `breath-sense-link`) | The literal "six" goes stale the moment Phase A lands. It is prose, not a tracked figure, so `check-staleness.py` will not catch it `[repo] CLAUDE.md §5` |
| `pcb/src/module/` is board-scoped | Three blocks are **not** board-scoped: `breath-sense-link`, `spi-link`, and the +12 V pair | This is the real break — see below |

**What breaks.** A cross-board directory cannot be one SKiDL module, because
`pcb/src/module/` builds one board and the instrument end has no `pcb/src/`
tree at all today `[repo] pcb-pipeline.md:115`. So `breath-sense-link/` and
`spi-link/` each map to *two* netlist modules — one under `pcb/src/module/`,
one under a future `pcb/src/controller/`. The directory axis and the netlist
axis diverge at exactly the three crossing blocks and nowhere else.

**Recommendation:** keep `pcb/` board-scoped (it emits one board), and have
each SKiDL module name the circuit directory it implements in a docstring.
Do not try to make `pcb/src/` mirror the circuit tree.

**One thing the restructure makes measurably easier.** Pipeline precursor 1
`[repo] pcb-pipeline.md:58-63`: "`AGND` means the umbilical sense conductor
*and* the module analog return. `BREATH` means the in-amp input *and* the
output jack. **Three cold reviewers found this independently.**" Both
collisions are between the two ends of `breath-sense-link` and between it and
`breath-output-stage`. Putting both ends of the link in one directory puts both
meanings of each name on one page, where a reader sees the collision. That is
the strongest single argument in this report for one-directory-per-link.

**Two pipeline statements that a Phase A move will strand**, flagged for
Phase B rather than fixed here (content freeze):

- `pcb-pipeline.md:115-118` — "one module per schematic page… importing the
  six". The page count and the noun both change.
- `pcb-pipeline.md:152` — "grouped by schematic page". Same.
