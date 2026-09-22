# D17 — the `circuit.yaml` dependency graph, rebuilt 2026-09-22

**Slice:** the 23 `circuit.yaml` files, their `circuit:`/`adr:`/`fig:`/`refdes:`
edges, the header that now calls the `circuit:` edges *verified*, and the
`id` / `provides:` / `verified_against:` invariants.

**Method.** Every claim below is derived from the repository by script or by
reading the page named. The edge set was extracted with `yaml.safe_load` over
all 23 files; the peer set was extracted from each page's `## Interfaces`
table by parsing the header row and taking the `Peer` column (the three
`interfaces/**` tables carry a sixth `End` column, so a fixed column index is
wrong — an early pass of this audit made that mistake and reported three false
mismatches). Physical claims are read off the pages and the BOM fragments.
**No file under `docs/review/**` was read except this wave's `README.md`.**

---

## Verdict in one paragraph

The transcription is **exact**: all 96 directed / 48 undirected edges match the
`Peer` columns of the 23 Interfaces tables, in both directions, with **zero**
discrepancies either way `[test]`. The `id`/directory and duplicate-`id`
invariants hold for all 23 `[test]`. But "matches the tables" is not what the
header claims, and it is not what a reader will take "VERIFIED" to mean. Seven
of the 48 edges cannot be substantiated as dependencies — **five of them are
edges to `module/link-supervision`, a circuit whose own page opens with "NOT
FITTED. Nothing in this directory is on the board"** — and at least six real
couplings are absent, including the one that links `interfaces/breath-sense-link`
to the rails its own module-side parts return to. Reciprocity-by-construction
is the wrong model: the `Dir` column already carries the direction, the rebuild
discarded it, and the result cannot be topologically sorted at all. Nothing in
the toolchain enforces reciprocity, so 96/48/0/0 is a hand-measured property of
one commit, not an invariant `[test]`.

---

## 0. The numbers, re-measured

```
files with circuit.yaml           23
unique declared ids               23   (no duplicates)
id != directory                    0
circuit: edges, directed          96
circuit: edges, undirected        48
one-sided                          0
self-loops                         0
isolated circuits                  0
refdes: edges                    131
provides:          declared in     0 files
verified_against:  declared in     0 files
```
`[test]` script over all 23 files; the count matches the header's claim
exactly.

Degree distribution `[test]`: `module/power-entry` 11, `module/panel` 6,
`module/dac8568` 6, `carrier/power-entry-instrument` 6,
`interfaces/breath-sense-link` 5, `module/breath-output-stage` 5,
`module/link-supervision` 5, `module/umbilical-load-switch` 5, then 4s and 3s
down to `carrier/display-and-service-uart` 1 and `carrier/led-strip-drive` 1.

**The rule the header states is followed without exception.** For each of the
23 circuits, the set of distinct `board/circuit` ids appearing in that page's
`Peer` column equals the set of `circuit:` edges it declares — set difference
empty in both directions, 23/23 `[test]`. That is a real and unusual result
and it should be said plainly before the rest of this report takes it apart.

---

## 1. Edge-by-edge — is every edge true?

Columns 3 and 4 give the `Interfaces` rows at each end, as `node (Dir)`.
Verdict key: **OK** = a shared net or a real physical dependency at both ends;
**MECH** = real but mechanical/documentary only, no net; **WEAK** = true only
by an indirect reading; **FALSE** = cannot be substantiated.

| # | Edge | Rows at end A | Rows at end B | Verdict |
|---|---|---|---|---|
| 1 | `carrier/breath-adc` — `carrier/power-entry-instrument` | `AGND_INST` (ref) | `PWR_GND pour` (ref) | OK |
| 2 | `carrier/breath-adc` — `interfaces/breath-sense-link` | `buffered sensor output` (in) | `buffered sensor output` (out) | OK |
| 3 | `carrier/breath-adc` — `interfaces/key-chain-loom` | `VDD/VREF 3V3` (in) | `3V3 (J-CHAIN pin 10)` (out) | OK |
| 4 | `carrier/breath-adc` — `interfaces/spi-link` | `SPI2 SCLK, MOSI, DOUT` (in/out) | `MISO` (—); `SPI2 host` (—) | **WEAK** — see §1.3 |
| 5 | `carrier/breath-excitation-reference` — `carrier/power-entry-instrument` | `+12V` (in); `AGND_INST` (ref) | `+12V analog` (out); `PWR_GND pour` (ref) | OK |
| 6 | `carrier/breath-excitation-reference` — `interfaces/breath-sense-link` | `VS` (out) | `VS excitation` (in) | OK |
| 7 | `carrier/display-and-service-uart` — `carrier/power-entry-instrument` | `5 V (or +12V) on J-DISP` (in); `GND ×2` (ref) | `5 V, buck B` (out); `PWR_GND pour` (ref) | OK |
| 8 | `carrier/led-strip-drive` — `carrier/power-entry-instrument` | `5 V` (in); `+12V, GND at J-LED-L/-R` (—) | `+12V strip feed` (out); `5 V, buck A` (out); `PWR_GND pour` (ref) | OK |
| 9 | `carrier/power-entry-instrument` — `module/power-entry` | `PWR_GND at J-UMB` (ref) | `PWR_GND` (ref) | OK |
| 10 | `carrier/power-entry-instrument` — `module/umbilical-load-switch` | `UMBILICAL +12V at J-UMB` (in) | `UMBILICAL +12V` (out) | OK |
| 11 | `cluster/key-marker-and-bits` — `cluster/key-register` | `marker straps` (out); `free-bit pull-ups` (out) | `A…H` (in) | OK |
| 12 | `cluster/key-marker-and-bits` — `cluster/key-switch-network` | `switch positions` (in) | `unfitted positions` (—) | MECH (allocation) |
| 13 | `cluster/key-marker-and-bits` — `interfaces/key-chain-loom` | `the serial bit stream` (out); `3V3, GND` (ref) | `the 32 bits` (—) | OK |
| 14 | `cluster/key-register` — `cluster/key-switch-network` | `A…H` (in) | `key input node` (out) | OK |
| 15 | `cluster/key-register` — `interfaces/key-chain-loom` | `SCK`,`SH/LD`,`SER`,`3V3` (in); `QH` (out); `GND` (ref) | six mirrored rows + `CLK INH` (—) | OK — the best-evidenced edge in the graph |
| 16 | `cluster/key-switch-network` — `interfaces/key-chain-loom` | `3V3` (in); `GND` (ref) | `3V3 (J-CHAIN pin 10)` (out) | OK |
| 17 | `interfaces/breath-sense-link` — `module/breath-output-stage` | `in-amp output` (out) | `in-amp output` (in) | **FALSE** — see §1.1 |
| 18 | `interfaces/breath-sense-link` — `module/breath-receive-stage` | `BREATH_SENSE`,`AGND_SENSE`,`in-amp output` (out); `REF`,`±12 V` (in); `AGND_MOD` (ref); parts (—) | `BREATH_SENSE`,`AGND_SENSE` (in); `in-amp output` (out); parts ×2 (—) | OK |
| 19 | `interfaces/breath-sense-link` — `module/link-supervision` | `presence detect on the pair` (—) | `breath pair` (in) | **FALSE** — §1.2 |
| 20 | `interfaces/spi-link` — `module/dac8568` | `SPI2 host` (—); `SCLK_DAC, DIN, SYNC` (—) | `SCLK_DAC, DIN, SYNC` (in) | **WEAK** — §1.4 |
| 21 | `interfaces/spi-link` — `module/digital-and-supervision` | `SCLK`,`MOSI`,`CS_MOD` (out); 3 × (—) | `SCLK`,`MOSI`,`CS_MOD` (in); `DIG_GND` (ref); `SCLK_DAC…` (out) | OK |
| 22 | `interfaces/spi-link` — `module/power-entry` | `DAC AVDD` (in); `DIG_GND` (ref); `bus +5V` (—) | `DAC AVDD` (out); `DIG_GND` (ref) | OK |
| 23 | `module/breath-output-stage` — `module/breath-receive-stage` | `in-amp output` (in) | `in-amp output` (out) | OK |
| 24 | `module/breath-output-stage` — `module/breath-response-shaper` | `in-amp output` (in) | `V_shaped` (out) | OK |
| 25 | `module/breath-output-stage` — `module/panel` | `BREATH_OUT` (out); `POT-GAIN, POT-OFFSET` (—) | `POT-GAIN, POT-OFFSET` (—); `BREATH_OUT jack` (—) | MECH |
| 26 | `module/breath-output-stage` — `module/power-entry` | `DAC AVDD`, `±12V` (in); `AGND_MOD` (ref) | 3 × rail (out); `AGND_MOD` (ref) | OK |
| 27 | `module/breath-receive-stage` — `module/breath-response-shaper` | `in-amp output` (out) | `in-amp output` (in) | OK |
| 28 | `module/breath-receive-stage` — `module/power-entry` | `DAC AVDD`, `±12V` (in); `AGND_MOD` (ref) | 3 × rail (out); `AGND_MOD` (ref) | OK |
| 29 | `module/breath-response-shaper` — `module/panel` | `POT-RESP` (—) | `POT-RESP` (—) | MECH — no net at either end |
| 30 | `module/breath-response-shaper` — `module/power-entry` | `±12V` (in); `AGND_MOD` (ref) | 2 × rail (out); `AGND_MOD` (ref) | OK |
| 31 | `module/dac8568` — `module/digital-and-supervision` | `SCLK_DAC, DIN, SYNC` (in) | same (out) | OK |
| 32 | `module/dac8568` — `module/link-supervision` | `CLR` (in) | `CLR` (out) | **FALSE** — §1.2 |
| 33 | `module/dac8568` — `module/mod-channels` | `DAC ch2–ch5`, `ch7` (out) | same (in); `CLR` (—) | OK |
| 34 | `module/dac8568` — `module/pitch-stage` | `VREFOUT`, `DAC ch1` (out) | same (in) | OK |
| 35 | `module/dac8568` — `module/power-entry` | `DAC AVDD` (in); `AGND_MOD` (ref) | `DAC AVDD` (out); `AGND_MOD` (ref) | OK |
| 36 | `module/digital-and-supervision` — `module/link-supervision` | `OE_MOD ×4` (ref) | `OE_MOD ×4` (out) | **FALSE** — §1.2 |
| 37 | `module/digital-and-supervision` — `module/power-entry` | `bus +5V` (in); `DIG_GND` (ref) | `bus +5V` (out); `DIG_GND` (ref) | OK |
| 38 | `module/link-supervision` — `module/panel-led` | `panel LED` (out) | `comparator collector node` (—) | **FALSE** — §1.2 |
| 39 | `module/link-supervision` — `module/umbilical-load-switch` | `UMBILICAL +12V` (in) | `UMBILICAL +12V` (out) | **FALSE** — §1.2 |
| 40 | `module/mod-channels` — `module/panel` | `MOD 1–MOD 4` (out) | `MOD 1–MOD 4 jacks` (—) | MECH |
| 41 | `module/mod-channels` — `module/power-entry` | `±12V` (in); `AGND_MOD` (ref) | 2 × rail (out); `AGND_MOD` (ref) | OK |
| 42 | `module/panel` — `module/panel-led` | `LED-PANEL bezel` (—) | `panel cutout` (—) | MECH — no net at either end |
| 43 | `module/panel` — `module/pitch-stage` | `PITCH jack` (—) | `PITCH` (out) | MECH |
| 44 | `module/panel` — `module/umbilical-load-switch` | `SW-POWER toggle` (—) | `ON` (in) | MECH |
| 45 | `module/panel-led` — `module/power-entry` | `MODULE ANALOG +12V` (in); `LED return` (ref) | `MODULE ANALOG +12V` (out) | OK |
| 46 | `module/panel-led` — `module/umbilical-load-switch` | `TIMER / GATE of U-LOADSW` (—) | `TIMER / GATE` (—) | **FALSE** — §1.5 |
| 47 | `module/pitch-stage` — `module/power-entry` | `±12V` (in); `AGND_MOD` (ref) | 2 × rail (out); `AGND_MOD` (ref) | OK |
| 48 | `module/power-entry` — `module/umbilical-load-switch` | `+12V ahead of D1/D2` (out); `PWR_GND` (ref) | same (in); `PWR_GND` (ref) | OK |

**Tally: 34 OK, 7 MECH, 2 WEAK, 7 FALSE** (edges 17, 19, 32, 36, 38, 39, 46).
Seven of 48 is 15 % of the graph.

### 1.1 Edge 17 rests on a net with two declared drivers — the exact defect the rebuild commit was about

`hardware/README.md` states the invariant: *"Exactly one page sources a net…
Two pages both claiming to source one net is the defect this column exists to
make visible"* `[repo] hardware/README.md:37-41`. The rebuild commit
`6645fb7` lists three such shorts it resolved and then records under *Verified
before committing*: *"exactly one page sources the DAC's SPI nets"*
`[repo] git log -1 6645fb7`. The check was run on the DAC's nets, not on the
invariant.

Run over every row of all 23 tables, exactly one net still has two `out` rows
`[test]`:

```
in-amp output:  interfaces/breath-sense-link  (out)
                module/breath-receive-stage   (out)  "**Owned here.**"
```
`[repo] hardware/interfaces/breath-sense-link/breath-sense-link.md:59` and
`hardware/module/breath-receive-stage/breath-receive-stage.md:45`.

`in-amp output` is a module-board net between two module circuits. The
receive stage says "Owned here"; `breath-sense-link`'s row is the duplicate,
and it is the only thing creating edge 17. Remove the duplicate driver and
edge 17 has no basis at all.

There is a second, independent sign it is wrong: `breath-receive-stage`'s row
names **three** peers on that node — `module/breath-output-stage`,
`module/breath-response-shaper`, `interfaces/breath-sense-link` — while
`breath-response-shaper`'s mirror row names only `module/breath-receive-stage`
`[repo] breath-response-shaper.md:28`. So of the two consumers of one node,
one got an edge to `breath-sense-link` and one did not. Whichever answer is
right, the graph cannot be right as it stands. **Either edge 17 goes, or an
edge `interfaces/breath-sense-link` — `module/breath-response-shaper` is
missing.** I believe it is the former.

### 1.2 Five edges — a tenth of the graph — point at a circuit that is not on the board

`hardware/module/link-supervision/link-supervision.md:3` opens:

> **NOT FITTED. Nothing in this directory is on the board.** The frame
> watchdog (74HC123) and the presence comparator (LM311) were both deleted
> before layout, and neither ever had a `bom.csv` row.

Confirmed structurally: `hardware/module/link-supervision/` is the **only**
circuit directory in the tree with no `bom.csv` fragment `[test]`. Its
Interfaces table has five rows and **every one of the five begins
"**Not fitted.**"** `[repo] link-supervision.md:25-31`.

Those five rows are the whole of edges 19, 32, 36, 38, 39 — ten of the 96
directed edges. The far ends confirm it in their own words:

- `dac8568`: "`CLR` … **Nothing drives it** — the part that did is not fitted"
  `[repo] dac8568.md` Interfaces.
- `digital-and-supervision`: "`OE_MOD ×4` … **The circuit that used to gate
  them is not fitted.**"
- `panel-led`: "comparator collector node … **Not fitted.** The deleted
  presence comparator shared this node."
- `umbilical-load-switch`: "`UMBILICAL +12V` … `module/link-supervision`'s …"
- `breath-sense-link`: "presence detect on the pair … **Not fitted.**"

This is `CLAUDE.md` §5's named failure mode with the sign reversed: not an
argument surviving its refutation, but a *dependency* surviving the deletion
of the thing it depends on, asserted in a file whose header says the edges are
verified. Keeping the directory as a record of a live decision is right
(`CLAUDE.md` is explicit that a documented gap is useful). Declaring five
reciprocal `circuit:` edges to it is not the same act, and nothing in the
graph distinguishes "not fitted" from "wired".

**`module/link-supervision` has degree 5 — higher than `module/pitch-stage`,
`module/mod-channels` or `cluster/key-register`, all of which exist.**

### 1.3 Edge 4 — one end declares no connection twice, and one of those rows says the net was deleted

`interfaces/spi-link`'s two rows naming `carrier/breath-adc` are both `Dir: —`:

- `MISO` — "IO37 is the MCP3202's `DOUT` and **never leaves the board**. ADR
  0004 deleted `MISO` from the umbilical" `[repo] spi-link.md`
- `SPI2 host` — "One host, two devices, two clocks."

The edge is nevertheless **true**, but for a reason neither row states: `SCLK`
and `MOSI` are literally the same carrier copper feeding both the MCP3202 and
`J-UMB`, which `breath-adc`'s own `SPI2 SCLK, MOSI, DOUT (in/out)` row does
say. Marked WEAK rather than FALSE because the physics carries it and the
tables do not.

### 1.4 Edge 20 — a BOM-ownership edge dressed as a boundary crossing

Both of `interfaces/spi-link`'s rows naming `module/dac8568` are `Dir: —`, and
one is explicit: *"**Not sourced here.** … these three are a module-board net
and **do not cross the umbilical**"* `[repo] spi-link.md`. That wording is the
resolution of one of the three shorts commit `6645fb7` fixed, and it is
correct. What survives is that `spi-link`'s `bom.csv` owns the three DAC-side
`R-SPI-PULL` resistors, which sit on `dac8568`'s pins
`[repo] hardware/interfaces/spi-link/bom.csv:R-SPI-PULL`. So the edge is real
as *"this circuit owns parts on that circuit's nets"* and false as *"a net
crosses this boundary"*, which is what the table is defined to hold
(`hardware/README.md:26`). Not a defect to fix in the graph; a sign that one
edge type is being asked to carry two relations.

### 1.5 Edge 46 — both ends say the connection is proposed and not drawn

| end | row | Dir | note |
|---|---|---|---|
| `module/panel-led` | `TIMER / GATE of U-LOADSW` | — | "**Proposed, not drawn.** The rework below would take the indication from here instead" |
| `module/umbilical-load-switch` | `TIMER / GATE` | — | "**Proposed only, nothing is drawn on it.**" |

`[repo] panel-led.md`, `umbilical-load-switch.md`, Interfaces tables.

Neither end declares a connection, and both state in terms that none exists.
This is the clearest single false edge outside the link-supervision cluster,
and unlike those five it is not even a record of something deleted — it is a
record of something never built. Edges 29 and 42 are also `—`/`—` but those
are honest mechanical adjacencies (a pot body in a panel cutout, an LED bezel
in a panel cutout); 46 is neither electrical nor mechanical.

---

## 2. Is every real edge present? Six couplings the graph does not have

This is the direction nothing can check, so each claim names the evidence and
what would settle it.

### M1 — `interfaces/breath-sense-link` — `module/power-entry` **(high confidence)**

`breath-sense-link` owns module-side parts: its table lists
`R2, R3, C_diff, C_cm ×2, R4, R5` as *"The receive filter and the common-mode
bias return, **all module-side**"*, and its `bom.csv` owns `D-TVS-BREATH` and
`R-SER-BREATH` `[repo] hardware/interfaces/breath-sense-link/bom.csv`. Three
of its own rows name the rails those parts sit on:

| row | Dir | its own note |
|---|---|---|
| `AGND_MOD` | ref | "The module's own analog star, **sourced by `module/power-entry`**. Where `R4`, `R5`, both `C_cm` and the output RC return" |
| `±12 V` | in | "The module analog rails, **sourced by `module/power-entry`**: the INA828, both OPA2197 halves, and the BAV99 legs" |
| `REF` | in | "…**fed from the `DAC AVDD` rail**" |

`[repo] breath-sense-link.md:63-69`. All three put `module/breath-receive-stage`
in the `Peer` column, so no edge is created. Meanwhile `module/power-entry`'s
rail rows enumerate their consumers explicitly — six circuits on
`MODULE ANALOG +12V`, five on `−12V`, four on `DAC AVDD`, six on `AGND_MOD` —
and `interfaces/breath-sense-link` is in **none** of them
`[repo] power-entry.md:26-33`.

So a circuit with parts on `AGND_MOD` and `±12 V` is absent from the supply's
own consumer list, at both ends. The `Peer` column was filled with *the page
the row was split out of* rather than *the circuit at the other end of the
net*, which is the same defect commit `6645fb7` fixed for `VREFOUT`, the DAC
channels and `CLR` — undetected here because the page it names is a real
circuit id, so nothing failed to resolve.

**Settles it:** decide whether `R4`/`R5`/`C_cm` belong to `breath-sense-link`
or to `breath-receive-stage`. If they stay where the table puts them, the edge
is missing at both ends.

### M2 — `interfaces/spi-link` — `carrier/power-entry-instrument` **(high confidence)**

`spi-link`'s own part `U-TVS-SPI` is *"on all three signals, **to `PWR_GND`**,
at the connector"* `[repo] spi-link.md` Interfaces; its BOM row opens
*"SCLK, MOSI, CS (+ one spare channel) **to PWR_GND**"* and, from the banked
datasheet, *"**ALL FOUR CHANNELS SHARE ONE COMMON PIN (pin 2), so a single
array cannot straddle PWR_GND and DIG_GND**"*
`[repo] hardware/interfaces/spi-link/bom.csv:U-TVS-SPI`. That last sentence is
a live design constraint binding this circuit to whichever circuit defines
`PWR_GND` on the carrier — which is `carrier/power-entry-instrument`
("`PWR_GND` pour … **the whole board returns here**").

`spi-link`'s table has **no `PWR_GND` row at all** `[test]`, so the net its own
protection device returns to is not declared, and the edge does not exist.
The two circuits already share two figures and `HDR-DEV` `[test]`.

### M3 — `interfaces/breath-sense-link` — `carrier/power-entry-instrument` **(medium)**

Same shape: `D-TVS-BREATH ×2 | instrument | — | — | —` "This circuit's own
parts, **at the connector**, on both legs" `[repo] breath-sense-link.md:57`.
A TVS array at a connector has a return; the row declares `Peer: —`, so the
graph records none. Weaker than M2 only because the row does not name the net.
**Settles it:** name the return net in that row, as `spi-link` does.

### M4 — `interfaces/breath-sense-link` — `module/breath-response-shaper` **(medium)**

See §1.1. The two consumers of `in-amp output` are treated differently. These
two circuits also share three figures with no edge — the largest such pair in
the corpus `[test]`.

### M5 — the graph has no node for the circuits `carrier/carrier.md` holds **(high confidence, structural)**

`hardware/carrier/carrier.md` carries `## §2 Analog front end — sensor,
reference, buffer, ADC` and `## §4 SPI egress to the umbilical`
`[repo] carrier.md:89,210`. It has **no `circuit.yaml` and no `## Interfaces`
table** `[test]`. It is named in the `Peer` column of exactly two rows in the
corpus — the only two `Peer` cells anywhere that name a *file* rather than a
circuit id `[test]`:

- `breath-sense-link`: `BREATH_SENSE` / `AGND_SENSE` → ``` `carrier/carrier.md` §2 → `module/breath-receive-stage` ```
- `spi-link`: `DIG_GND` → ``` `carrier/carrier.md` ↔ `module/power-entry` ```

Under the header's own rule a non-circuit peer creates no edge — correct
mechanically, and it means **the breath signal chain has no source in the
graph.** Follow it backwards from the module's output jack and it stops at
`interfaces/breath-sense-link`, whose upstream is a page outside the graph.
The same hole swallows `HDR-DEV`, which actually drives every SPI and key-chain
signal and appears in seven circuits' `refdes:` lists but, being a header,
correctly creates no edge either.

So "zero isolated circuits" is true of the 23 nodes that exist and says nothing
about whether the 23 are the right 23. A graph whose purpose is to follow
signal chains cannot omit the node that sources two of them.

### M6 — `interfaces/key-chain-loom` draws its TVS array to a net that is on the other board **(flag, one of two defects)**

`key-chain-loom.md:80` draws `[U-TVS-CHAIN 4-ch array to DIG_GND]`. In this
graph `DIG_GND` is a module-side net: `module/power-entry` sources it to
`module/digital-and-supervision` and `interfaces/spi-link`, and it travels the
umbilical `[repo] power-entry.md:33`. The key loom runs carrier↔cluster and
never reaches the module. **Either the drawing's net name is wrong** (my
reading — a D16-class net-naming defect) **or an edge is missing.** Not both.

### Considered and rejected

`carrier/breath-adc` — `carrier/led-strip-drive` shares `C-STRIP-BULK` and
`HDR-DEV`, and `breath-adc.md:88` argues from the WS2815's ~2 kHz PWM rate
against a 4 kHz sampler on a shared LDO. That is a real coupling but it is a
supply-noise argument, not a shared net, and both circuits already reach
`carrier/power-entry-instrument` in one hop. Adding it would set a precedent
that puts an edge between every pair of circuits on a rail.
`carrier/breath-excitation-reference` — `module/breath-receive-stage` shares
three figures but is a two-hop path through `breath-sense-link`; correct as is.

---

## 3. Was enforcing reciprocity correct? No — and it destroyed information the tables already had

**The direction was never missing.** The `Dir` column is defined in
`hardware/README.md:25` as five values — `in`, `out`, `in/out`, `ref`, `—` —
and every one of the ~130 Interfaces rows carries one `[test]`. The rebuild
read the `Peer` column out of those rows and discarded the `Dir` beside it. The
header then records the loss as a standing limitation: *"Direction is still not
recorded: several pairs are mutual, which is honest for a net shared between
two circuits and **useless for ordering anything**."* It was available in the
same cell of the same table.

**What symmetry encodes that is false.** `depends_on` is not a symmetric
predicate, and forcing it produces claims no one would write by hand:

- `module/power-entry: depends_on circuit:module/panel-led` — the entry
  regulator depends on the indicator LED. Eleven of `power-entry`'s edges are
  rails; ten of the eleven reverse directions are like this.
- `module/dac8568: depends_on circuit:module/link-supervision` — the DAC
  depends on a circuit that is not fitted and, per its own row, does not drive
  `CLR`. Reciprocity manufactured that direction from a deleted part.
- `module/panel: depends_on circuit:module/pitch-stage` — a 2 mm aluminium
  plate depends on an analog stage. The true dependency is the other way: the
  jack needs the cutout, and the DXF is cut first.
- `carrier/power-entry-instrument: depends_on circuit:carrier/led-strip-drive`.

**The counter-argument, stated fairly.** A supply *does* depend on its loads
for sizing — `umbilical-current` and `matrix-led-current` are tracked figures
owned upstream and derived from downstream. That is a real relation. But it is
a *different* relation from "consumes", and collapsing the two into one
undirected `depends_on` is what makes `module/power-entry` degree 11 with no
way to tell which eleven are which.

**A reciprocal graph cannot be ordered at all.** Every one of the 48 edges is a
2-cycle, so the directed graph has 48 strongly-connected components of size ≥2
and no topological sort exists `[calc]`. Any future consumer wanting a build,
bring-up or power-up order gets nothing from this graph — not an imperfect
order, none.

**Recommendation.** Keep the symmetric *relation* if it is useful, but call it
what it is (`peers:`), and add the direction the tables already hold: one
`circuit:` edge per `Peer` cell, carrying that row's `Dir`. Then
`out`→`in` gives an orderable DAG, `ref` marks the ground/rail relations, and
`—` marks the mechanical and documentary ones — which would have separated
the 7 MECH and 7 FALSE edges above automatically.

---

## 4. The header's claim — "verified" by whom, against what?

**It overstates, and the commit that wrote it says so in its own message.**

The header asserts: *"`circuit:` edges are VERIFIED. They were rebuilt, in one
pass across all 23 circuits, from the `## Interfaces` tables…"*. The commit
that installed it records: *"**The graph followed the tables, which is the
point — it was seeded from them.**"* `[repo] git log -1 6645fb7`. Seeded from
the tables and verified against the tables are the same operation described
twice, and only one of the two descriptions is in the file a reader opens.

So what "verified" means here is precisely: **transcribed without error from
23 prose tables that eight agents wrote in parallel and that nothing checked
against each other** — the commit's own characterisation of those tables. That
transcription is genuinely exact (§0, 23/23) and worth something. It is not
verification of a dependency, and §§1–2 are what the difference costs: 7 false
edges and 6 absent ones, none of which a table-to-YAML comparison could ever
find, because the graph and the tables now agree perfectly *and are wrong
together*.

**A third statement contradicts the header outright.** `hardware/README.md:12`
still describes `circuit.yaml` as *"declared dependencies. **SEEDED, NOT
VERIFIED**"* — the directory-layout block every new reader meets first. Three
documents, two answers. The register rule in `CLAUDE.md` §1 exists for exactly
this: the claim is restated in three places instead of stated once and cited.
Note also that this one is invisible to `check-staleness.py`, which greps for
*values*.

**Nothing enforces any of it.** `check_circuits` checks that each edge
*resolves* — a `fig:` names a register entry, a `circuit:` names a declared
id, a `refdes:` names a BOM row `[repo] tools/check-staleness.py:459-521`.
That is all it checks, and the header says so accurately in its last paragraph.
There is **no reciprocity check, no isolation check, no table-vs-YAML check**
anywhere in `tools/` `[test]` — grep for `reciproc|one-sided|both ends|isolated`
over `tools/*.py` returns one unrelated hit in `rewrite-paths.py`. So 96/48/0/0
is a property measured by hand on 2026-09-21 and unprotected from
2026-09-22 onward. The next person who adds a `Peer` cell and forgets the far
end restores exactly the state this rebuild was run to fix, and the commit
hook will pass.

### 4.1 The three refdes edges a reviewer proved false — confirmed present, two still false, one now arguable

| edge | still declared? | still false? | evidence |
|---|---|---|---|
| `module/pitch-stage → refdes:R-BIAS-INAMP` | **yes** | **yes** | Sole mention: *"This project already fixed the identical problem on the breath in-amp with `R-BIAS-INAMP`. `R-BIAS-DAC` now does it here"* `[repo] pitch-stage.md:325`. An explicit contrast, as recorded. |
| `carrier/breath-adc → refdes:C-STRIP-BULK` | **yes** | **yes** | Sole mention: *"The repo's own `C-STRIP-BULK` note puts the WS2815 PWM rate at ~2 kHz"* `[repo] breath-adc.md:88`. A citation of another part's note. |
| `module/breath-receive-stage → refdes:U-OPA-PITCH` | **yes** | **disputed — I think this one is now true** | Sole mention is the package-count sentence `[repo] breath-receive-stage.md:172`, as recorded. **But `U-OPA-PITCH` is in `hardware/module/breath-receive-stage/bom.csv`** `[test]`, and the page's own argument is that the `REF` buffer *is* an OPA2197 half. The circuit uses the part and owns its row. |

The third one is worth flagging under `CLAUDE.md`'s *"a finding filed as
handled does not get re-checked"*: a finding that was right when written has
been overtaken by the BOM fragment split, and the header now repeats it as
settled fact. **The header should not carry a verdict it is not re-deriving.**

### 4.2 "Expect more of that shape" — there are at least eight more, and three are the same sentence pattern

Scored all 131 `refdes:` edges by (a) whether the refdes is in the circuit's
own `bom.csv` fragment and (b) how many times it appears on the circuit's own
page `[test]`. 39 edges are neither owned nor mentioned more than once. Reading
each of those mentions:

**Proven false — the page's only mention says the part is _not_ here** (the
exact `R-BIAS-INAMP` shape):

1. `module/power-entry → refdes:L-BUCK-IN` — *"(`L-BUCK-IN` and the umbilical's
   input LC **moved with the load switch** — they are in
   `umbilical-load-switch.md`.)"* `[repo] power-entry.md:183`
2. `carrier/led-strip-drive → refdes:C-STRIP-BULK` — *"**The 12 V strip power
   and `C-STRIP-BULK` are not here**"* `[repo] led-strip-drive.md:8`

**Proven false — a contrast, an analogy or a part-number reuse note:**

3. `module/breath-receive-stage → refdes:TRIM-OFFSET` — a comparison-table row
   *"Pitch | `TRIM-OFFSET`, set once | firmware's per-load affine"*
   `[repo] breath-receive-stage.md:162`. `TRIM-OFFSET` is `pitch-stage`'s.
4. `module/breath-output-stage → refdes:R-MODGAIN` — *"Fixed ×4. **Same E96
   part as `R-MODGAIN`**"* `[repo] breath-output-stage.md:149`. A part-number
   reuse note.
5. `carrier/led-strip-drive → refdes:R-SPI-PULL` — *"The module page has the
   same idea for the same reason: `R-SPI-PULL`, six of them"*
   `[repo] led-strip-drive.md:60`. An analogy to another board.
6. `interfaces/breath-sense-link → refdes:R-OUT-PROT` — *"argument, in full,
   for the module-side `R-OUT-PROT` — and it was never carried"*
   `[repo] breath-sense-link.md:182`.

**Proven false — prose about a deleted circuit's relationship to other
circuits' parts** (both on the not-fitted page, which owns no parts at all):

7. `module/link-supervision → refdes:R-CLR-PU` `[repo] link-supervision.md:27`
8. `module/link-supervision → refdes:R-SPI-PULL` `[repo] link-supervision.md:48`

**Also worth knowing, not false:** `module/power-entry` declares six `refdes:`
edges to parts owned by `module/umbilical-load-switch` (`R-FB-HI`, `R-FB-LO`,
`R-GATE-SER`, `R-GATE-COMP`, `R-ILIM`, `U-LOADSW`). Those are real — but only
because `power-entry.md` **redraws the entire load switch inline in its own
ASCII schematic** `[repo] power-entry.md:44-73`. That is a duplicated drawing
of another circuit, which is a live hazard for the transcribed netlist and is
outside my slice; I note it because it is what generated the edges.

**Also:** `L-BUCK-IN`'s BOM row lives in
`hardware/carrier/power-entry-instrument/bom.csv` `[test]`, while
`power-entry.md:183` says it "moved with the load switch … [it is] in
`umbilical-load-switch.md`", and `umbilical-load-switch.md:359` lists it under
`## Still open` as an undesigned damping leg. Three documents, three homes, one
part.

So the header's "Expect more of that shape" is right, and the count is at least
**eleven** false `refdes:` edges, not three.

---

## 5. `provides:` and `verified_against:` — still empty in all 23

`[test]`: neither key appears in any of the 23 files. The header does not
mention either, and neither was added.

Both checks over them therefore remain unfalsifiable:

- `check_verified_against` iterates `c.get("verified_against") or []` and
  returns `[]` for every circuit `[repo] tools/check-staleness.py:531-570`.
  Its purpose — catching a re-banked datasheet whose SHA moved under a figure
  read off the old revision — is real and is currently doing nothing.
- The `node:` branch of `check_circuits` resolves against `provided`, built by
  unioning every circuit's `provides:` `[repo] check-staleness.py:466-469`.
  With no `provides:` anywhere, `provided` is empty, so **any** `node:` edge
  would fail. There are zero `node:` edges, so it never fires either.

That second one is a latent trap rather than a mere no-op: the first person to
write a `node:` edge gets a failing commit hook with the message "no circuit
provides it", which is true and unhelpful, because the mechanism for providing
it has never been used. It would be worth one `provides:` entry somewhere just
to prove the path works — `module/power-entry` provides `AGND_MOD`,
`DAC AVDD`, `MODULE ANALOG ±12V`, `bus +5V` and `DIG_GND`, all five of which
its Interfaces table already declares `out`/`ref`. That is also the cleanest
way to fix M1: a rail consumer declares `node:AGND_MOD` and the false symmetry
in §3 disappears for eleven of the twelve rail edges.

---

## 6. `id` and path invariants — all 23 clean

`[test]`, over every `circuit.yaml` in `hardware/**`:

- 23 files, **23 distinct `id` values** — no duplicate, so nothing is silently
  evicted from the map the way `load_circuits` warns about
  `[repo] check-staleness.py:441-448`.
- **`id` equals the directory path in all 23 cases** (`hardware/` stripped),
  by the same rule `check_circuits` applies.
- No `depends_on` entry lacks a type prefix; no unknown prefix; every
  `circuit:` target is a declared id; `[test]` the full checker run reports
  `PASS` with zero circuit problems.

One observation the invariant does not cover: the directory-to-id map is also
the board grouping (`carrier/`, `cluster/`, `interfaces/`, `module/`), and
`hardware/README.md:18-21` states the counts as 5 / 3 / 3 / 12 = 23, which is
correct `[test]`. That is the one place the circuit count is restated and it
happens to be right.

---

## 7. What is the graph for? Decoration today; not fit for a netlist or a build order

**Today.** `check_circuits` is the only consumer in the repository `[test]` —
grep for `circuit.yaml` across `tools/` and `.claude/` returns only
`check-staleness.py`. What it does with the graph is check that each edge
*resolves*. That is worth having: it is the one check in the toolchain that
reports a **dependency** rather than a value, and it is the mechanism that
would catch a page still depending on a deleted part — `CLAUDE.md` §5's
semantic half. Note, though, that it did **not** catch the largest instance of
exactly that in the corpus: `module/link-supervision`'s five edges resolve
perfectly, because the circuit still has a `circuit.yaml` even though it has no
parts and no board presence. Resolution is a weaker guarantee than it sounds
against a directory that is kept deliberately.

**As a netlist source: no, and it should never become one.** The netlist is
transcribed from the Interfaces tables, and `hardware/README.md:29` says so.
The graph is a lossy projection of those tables — it keeps the peer and drops
the node name, the direction, the figure and the note. Anything driving a
netlist should read the tables. If the graph is ever used instead, the seven
FALSE edges become seven wires, five of them to a circuit that is not on the
board, and edge 17's duplicate driver becomes a short between the in-amp output
and the umbilical — the precise failure
`interfaces/breath-sense-link.md:9-14` warns about in its own preamble.

**As a build or bring-up order: no, structurally.** §3 — every edge is a
2-cycle, so there is no topological order to extract.

**What it could become, cheaply, in priority order:**

1. **Carry `Dir` into the edge.** The information is in the same table cell.
   This single change gives a DAG, separates rails from signals from mechanical
   adjacencies, and makes the 7 MECH and 7 FALSE edges visible by type.
2. **Make the table-to-YAML equality a check.** It is ~30 lines and it holds
   exactly today (§0), so it can be switched on at zero cost and will stay
   true. Without it, this rebuild decays on the next `Peer` edit.
3. **Mark not-fitted circuits.** One key (`fitted: false`) on
   `module/link-supervision`, and any consumer can drop its five edges — while
   the directory keeps doing the job `CLAUDE.md` wants it to do.
4. **Use `provides:`** for the rails (§5), which fixes M1 and eleven false
   reverse dependencies at once.

Until at least (1) and (2), the honest description is: **an exact, unenforced
transcription of 23 prose tables, with one real check running over it, labelled
"verified" in a way three other documents contradict.** It is not decoration —
the resolution check earns its place — but it is not a dependency graph in the
sense that its header implies, and the perfectly reciprocal shape the rebuild
produced is the strongest evidence of that, not against it.

---

## Findings index

| id | claim | confidence |
|---|---|---|
| D17-1 | Edges 19, 32, 36, 38, 39 declare dependencies on `module/link-supervision`, which is NOT FITTED, has no `bom.csv`, and whose five Interfaces rows all begin "Not fitted." 10 of 96 directed edges. | high |
| D17-2 | Edge 17 exists only because `in-amp output` has two declared `out` rows — the one net in the corpus still violating `hardware/README.md`'s one-source rule. Commit `6645fb7` verified that rule on the DAC's nets only. | high |
| D17-3 | Edge 46 (`panel-led` — `umbilical-load-switch`) has `Dir: —` at both ends and both notes say the connection is proposed and not drawn. | high |
| D17-4 | Missing: `interfaces/breath-sense-link` — `module/power-entry`. Its own rows name `power-entry` as the source of `AGND_MOD`, `±12 V` and `DAC AVDD`, but put `breath-receive-stage` in `Peer`; `power-entry`'s consumer lists omit it. | high |
| D17-5 | Missing: `interfaces/spi-link` — `carrier/power-entry-instrument`. `U-TVS-SPI` returns to `PWR_GND`; `spi-link` declares no `PWR_GND` row. | high |
| D17-6 | The graph has no node for `carrier/carrier.md` §2/§4, the source of `BREATH_SENSE`. Two `Peer` cells name a file rather than a circuit — the only two in the corpus. | high |
| D17-7 | The header says `circuit:` edges are VERIFIED; commit `6645fb7` says they were *seeded* from the tables; `hardware/README.md:12` still says SEEDED, NOT VERIFIED. Three documents, two answers. | high |
| D17-8 | Eight further `refdes:` edges are false by the same test as the three the header names; two are the identical "the part is not here" sentence shape. Total ≥11, not 3. | high |
| D17-9 | The `U-OPA-PITCH` finding the header repeats as proved-false is now arguable — the part is in `breath-receive-stage`'s own BOM fragment. A finding filed as settled stops being re-checked. | medium |
| D17-10 | Nothing enforces reciprocity, isolation or table-vs-YAML agreement. 96/48/0/0 is a one-off hand measurement. | high |
| D17-11 | Reciprocity-by-construction is the wrong model: `Dir` already had the direction, and the symmetric graph has 48 two-cycles and no topological order. | high |
| D17-12 | `provides:` and `verified_against:` are still empty in all 23 files; both checks over them remain unfalsifiable, and the `node:` branch will reject the first `node:` edge anyone writes. | high |
| D17-13 | All 23 `id`s match their directories; no duplicates. Clean. | high |
| D17-14 | `key-chain-loom.md:80` draws `U-TVS-CHAIN` to `DIG_GND`, a module-side net the carrier↔cluster loom does not reach. Either the net name is wrong or an edge is missing. | medium |
| D17-15 | `power-entry.md` redraws the whole of `umbilical-load-switch` inline, which is what generates six of its `refdes:` edges. A duplicated drawing feeding a transcribed netlist. | medium (outside slice) |
| D17-16 | `L-BUCK-IN` has three homes: a BOM row under `carrier/power-entry-instrument`, a sentence in `power-entry.md` saying it moved to `umbilical-load-switch`, and a `Still open` proposal on that page. | medium (outside slice) |
