# A5 — Instrument power entry, and the cable between

**Wave:** 2026-09-21 pre-merge review · **Agent:** A5 · **Cold:** no prior
review directory was read.

**Slice:** +12 V from the module's load switch, down 2 m of Cat5, into
`carrier/power-entry-instrument` and everything it feeds. Spans
`hardware/carrier/power-entry-instrument/`, `hardware/interfaces/`,
`docs/decisions/0005-power-architecture.md`,
`docs/decisions/0014-lighting.md`, and the tracked figure `umbilical-current`.

**Provenance is marked on every claim.** `[repo] path:line`, `[calc]` with the
arithmetic, `[datasheet] document, page`, `[from memory]`. Findings are indexed
by circuit node or BOM reference. **Nothing was fixed** — this is a report.

Tool state at the time of review: `tools/check-staleness.py` → `PASS no live
stale values | corpus 121 files, 23 circuits | 5 unresolved (tracked)`;
`tools/merge-bom.py --check` → `checked 138 rows from 24 fragments | 0
problems` `[repo]`. Every finding below is therefore something neither tool can
see.

---

## Summary of findings

| # | Node / ref | Finding | Severity |
|---|---|---|---|
| **A5-1** | `UMBILICAL +12V`, `D2`, `FB2` | The corpus holds **two incompatible topologies** for the umbilical feed: branch *before* `D1`/`D2`, or *through* `D2`+`FB2`. A tracked figure depends on the second; two schematic pages assert the first | **High** |
| **A5-2** | `UMBILICAL +12V` | The far-end arrival voltage — the denominator of `umbilical-current` — is **not tracked**, and has three live values (11.4 V, ~11.5 V, ~10.96 V) built on three different drop chains | **High** |
| **A5-3** | `fig:umbilical-current` | The register's own `derivation` yields **358.1 mA** against a `value` of **359 mA**; the other three rows of the source table need **88.5 %**, not the 90 % the ADR mandates | Medium |
| **A5-4** | `CABLE-UMB` | The only drop calculation in the corpus assumes **24 AWG**; the BOM row specifies a *stranded* Cat5e patch lead with **no gauge**. 26 AWG is +59 % drop | **High** |
| **A5-5** | `U-BUCK` / ADR 0004 | ADR 0004 sizes the umbilical against "a buck that needs **more than 6 V** in". The part's minimum is **8 V** | Medium |
| **A5-6** | ADR 0004 series-R table | Header says "Drop at 359 mA"; both cells are computed at **290 mA** | Medium |
| **A5-7** | `L-BUCK-IN` / `C-BUCK-IN` | The stability derivation is sound but covers a **different LC** from the one the open item names, at the **wrong load case** | Medium |
| **A5-8** | open item "damping the input LC" | Assigned to **two** places under **one** stale path, and the milestone it is assigned to **cannot** close it | Medium |
| **A5-9** | `D-USBOR` | BOM package is **DO-41 THROUGH-HOLE** for a part the schematic names as **SS14 = SMA (DO-214AC)** | Medium |
| **A5-10** | 5 V node after `D-USBOR` | Worst-case stack puts it at **4.28–4.45 V**, below the `74AHCT125`'s specified **4.5 V** minimum VCC | **High** |
| **A5-11** | body / `MECH-GNDBOND` | The 3 K/W thermal chain is **three restatements deep with no measurement at the bottom**, and the clamp's 9 K is **additive** to a 10–20 K that eight documents treat as the total | **High** |
| **A5-12** | ADR 0014 thermal table | `~17.7 W` is computed at the **85 % efficiency ADR 0005 refuted**; the ×0.49 sibling was corrected and this one was not | Medium |
| **A5-13** | `C-STRIP-BULK` feed / WS2815 | ~120 mA of **strip quiescent** (≈1.44 W) is **invisible to the firmware clamp** — nearly half the 3 W budget | **High** |
| **A5-14** | 5 V rail | "Clamp fails" row omits **~300 mA of dev-board load** that the row above it counts | Medium |
| **A5-15** | 12 V direct column | Strips-blanked draw appears as **123 mA** and **119 mA** in the same table | Low |
| **A5-16** | 5 V rail | ADR 0014's "both dev boards take **330–400 mA**" **exceeds** ADR 0005's entire typical-play 5 V column (226 mA) | **High** |
| **A5-17** | `REF5050`/`U-BUF`, `key-scan-current` | The analog block's ~13 mA and the key pull-ups' 25.8 mA have **no visible line** in the load table | Medium |
| **A5-18** | `J-UMB` pins 1,2,4,5,7,8 | Nothing limits a **+12 V-to-signal short**; the only clamp is a **0.225 W** array, at one end only | **High** |
| **A5-19** | `J-UMB` pin 6 `PWR_GND` | A single open conductor silently reroutes **~360 mA into `DIG_GND`**. No analysis, no detection | Medium |
| **A5-20** | `fig:matrix-led-current` | The 3 W clamp permits **600 mA** through a path the same register puts at **283–435 mA** | **High** |
| **A5-21** | WS2815 strips | The **20 mA/LED** that sizes the whole thermal budget has **no provenance mark anywhere**, though the datasheet is banked | **High** |
| **A5-22** | `U-BUCK` ×2 | One efficiency point is applied across an **18 %–93 %** load range and across **two** regulators the table never splits | Medium |

---

## 1. The current budget — does `umbilical-current` reproduce?

### A5-3 — `fig:umbilical-current`: the register's derivation does not produce the register's value

`config/figures.yaml:458-465` `[repo]`:

```
value:      "359 mA"
derivation: "226 mA x 5 V / (0.9 x 11.4 V) + 248 mA = 358.1 mA"
```

`[calc]` `226 × 5 = 1130`; `0.9 × 11.4 = 10.26`; `1130 / 10.26 = 110.14`;
`+ 248 = 358.14` → **358 mA**. The entry states its own answer as 358.1 and then
carries 359. One milliamp, and irrelevant electrically — but this is the one
register in the project whose entire purpose is that a derivation and a value
cannot drift apart, and here they have, inside the entry itself.

**Where 359 actually comes from.** Reproducing all four rows of ADR 0005's load
table `[repo] docs/decisions/0005-power-architecture.md:156-161` at the two
conventions the same ADR mandates — "convert at the **arriving** voltage" and
"the buck is **~90 % efficient**" `[repo] 0005:169-172` — `[calc]`:

| Row | Stated umbilical | at 90 % / 11.4 V | at 88.5 % / 11.4 V |
|---|---|---|---|
| Quiescent | 212 mA | 210.7 (−1.3) | 212.2 (+0.2) |
| **Typical play** | **359 mA** | **358.1 (−0.9)** | **360.0 (+1.0)** |
| Typical + WiFi | 414 mA | 411.7 (−2.3) | 414.5 (+0.5) |
| Clamp-legal worst | 579 mA | 571.2 (**−7.8**) | 578.9 (−0.1) |

**Three of the four rows were computed at ~88.5 %, not at the 90 % the ADR
states as a convention to keep.** The register then recomputed the one row it
tracks at 90 %, got 358.1, and published 359. The table is self-consistent at
88.5 %; the register is consistent with nothing. Either the table is recomputed
at 90 % (212 / 358 / 412 / 571) or the convention paragraph is corrected — but
the current state is a tracked figure whose derivation disagrees with both its
own value and its own source table.

*(This is not the `refutation exemption` case the register warns about in
`diode-split-rationale`'s `escape_note`. Nothing here is refuted; the arithmetic
simply was never re-run.)*

### A5-16 — 5 V rail: two documents disagree by ~2× on what the dev boards draw

- ADR 0005's table puts the **entire 5 V rail** at **226 mA** at typical play,
  and that figure must already contain the matrix's idle draw, which ADR 0014
  estimates at **~40–64 mA** `[repo] 0014:426` and ROADMAP at ~50 mA
  `[repo] ROADMAP.md:189`. Dev boards + level shifter ≈ **170 mA**.
- ADR 0014 states the matrix "shares the 1 A R-78E5.0 with both dev boards,
  **which take roughly 330–400 mA between them**" `[repo] 0014:474-476`.
- ADR 0005's clamp-legal-worst row implies the same quantity is **328 mA**
  `[calc]`: 928 mA total less 600 mA of matrix at the 3 W clamp
  (`3 W / 5 V = 600 mA`).

So the same two boards are 170 mA in one row of a table and 328–400 mA in two
other documents. **Both figures feed regulator sizing**, from opposite sides:
`power-entry-instrument.md:88-94` `[repo]` derives buck A's 68–78 % loading from
the 928 mA, and the `U-BUCK` BOM row's whole "one per dev board" justification
rests on 928 mA too `[repo] hardware/carrier/power-entry-instrument/bom.csv:2`.
Nothing reconciles the 226.

### A5-14 — "Clamp fails, strips latched full white" omits the dev boards

`[repo] 0005:161` — 5 V column **1023 mA**. `[calc]` At the wrong-part matrix
figure that row was built on, 960 mA of matrix + 1023 leaves **63 mA** for two
ESP32-S3 boards, an AMOLED and a 74AHCT125 — against the 328 mA the row
immediately above allocates to exactly those loads. The failure row **omits
roughly 300 mA that the legal row counts**. The umbilical figure it produces
(~1522 mA) is therefore low by ~250 mA, and that figure is the one ADR 0005
uses to argue the latched-full-white state now *trips* the limiter
`[repo] 0005:288-296`. The conclusion survives — it gets further above the
0.78–1.10 A limit, not closer — but the row does not reproduce.

### A5-15 — the 12 V-direct column states strips-blanked twice, differently

Quiescent row: **123 mA**. Clamp-legal-worst row: **119 mA**
`[repo] 0005:157,160`. In both states the strips are unlit and the only 12 V
loads are strip quiescent plus the analog block, so the two should be identical.
4 mA, low severity, but it is a value stated twice in one table.

### A5-17 — loads with no visible line in the table

- **The analog block on raw +12 V.** `breath-excitation-reference.md:71`
  `[repo]` states "our load draws **10 mA**" through the REF5050/OPA2197 buffer
  into the sensor's `VS`. Add the REF5050's and the OPA2197's own quiescent and
  the +12 V analog branch is **≥ 10 mA and plausibly ~13 mA**. ADR 0005's
  quiescent 12 V column is 123 mA against "roughly **120 mA** of strip
  quiescent draw" `[repo] 0005:344`, which leaves **~3 mA** for the whole analog
  block. Either the strip quiescent is ~110 mA or ~10 mA of documented load is
  uncounted. It is 2.8 % of `umbilical-current`, so the figure survives; the
  point is that **no row of the table is attributable to a named consumer**, so
  a missing load cannot be found by reading it.
- **The key pull-ups.** `fig:key-scan-current` = **25.8 mA at 18 closed**
  `[repo] config/figures.yaml:126`, drawn from 3V3 and therefore from the 5 V
  rail through the real-time board's LDO at the same milliamps. ADR 0005's power
  tree describes the 3.3 V loads as "the shift register chain (**microamps**),
  the ADC (milliamps) and pull-ups" `[repo] 0005:245-247`. 25.8 mA is **11 % of
  the typical-play 5 V column** and is described in the tree as if it were
  negligible. It may well be inside the 226 mA; nothing says so.

### A5-22 — one efficiency point, two regulators, a 5× load range

The R-78E5.0-1.0 datasheet publishes **efficiency-vs-load curve families** with
traces at 8/12/24/28 V in `[datasheet] datasheets/discrete-and-power/R-78E5.0-1.0.pdf,
p. I-2, "Efficiency vs Load"`. The corpus reads **one point** off them and
applies it identically at 180 mA and at 928 mA — 18 % and 93 % of rating. For a
part of this class the low-load end sits materially below the peak
`[from memory]`, which biases the quiescent row's umbilical figure low.

Worse, **the conversion is structurally wrong once the rail is split.** There
are two bucks; efficiency is per-converter and load-dependent; the table has one
5 V column. `power-entry-instrument.md:96-99` `[repo]` already states this
("ADR 0005's load table has one 5 V column and the two-regulator decision needs
it split per buck. That split is not written anywhere and it is what sizes both
parts"). **I confirm that finding and add the arithmetic consequence:** buck B
at 150–250 mA is at 15–25 % of rating, where the datasheet's own curve is
lowest, and its losses are being charged to the corpus at buck A's rate.

*(The datasheet extraction also independently corroborates the `U-BUCK` BOM
row's emphatic 8 V claim: the R-78E3.3-1.0 chart carries a **7 Vin** trace and
the R-78E5.0-1.0 chart a **8 Vin** trace `[datasheet] R-78E5.0-1.0.pdf p.I-2`.
That row is right and is the best-sourced thing in this slice.)*

---

## 2. Voltage at the far end

### A5-1 — `UMBILICAL +12V` / `D2` / `FB2`: the corpus holds two incompatible topologies

This is the finding that most needs adjudication, because **the drop chain, a
tracked figure, and the load switch's `FB` divider all change depending on which
is true.**

**Topology A — the branch is taken *before* the entry diodes.** No series
Schottky, no bead in the umbilical path.

- `[repo] hardware/module/power-entry/power-entry.md:28` — "`+12V` ahead of
  `D1`/`D2` | out | `module/umbilical-load-switch` | The branch is taken
  **before** the diodes; `U-LOADSW`'s `VCC` and the top of `R-ILIM` hang off it"
- `[repo] hardware/module/umbilical-load-switch/umbilical-load-switch.md:15` —
  the same row from the other side, "Taken before the entry diodes, **which is
  the point of the split**"

**Topology B — the umbilical runs through `D2` and `FB2`.**

- `[repo] config/figures.yaml:533` (`fig:ferrite-bias-impedance`, `status:
  settled`) — "**`FB2` carries `umbilical-current` (359 mA)** and interpolates
  to ~280-310 ohm". The entire FB2 half of a settled tracked figure exists only
  under Topology B.
- `[repo] hardware/bom.csv:109` (`D-REVPOL`, qty **3**) — "THREE not two: the
  module's analog +12V **and the umbilical feed** must NOT share a diode"
- `[repo] hardware/module/power-entry/power-entry.md:111-113` — "Keep both
  diodes anyway, for the reasons that do hold: fault isolation **between the
  exported rail and the analog rail**". An exported rail that does not pass
  through `D2` cannot be isolated by it.
- `[repo] hardware/bom.csv:113` (`FB-IN`, qty 4) — "One per branch: +12V analog,
  **+12V umbilical**, -12V, +5V"
- `[repo] docs/reference/pcb-pipeline.md:144` — "`FB2` carries the umbilical at
  359 mA"

**And the drawing is a third thing.** `power-entry.md:46` `[repo]` renders the
branch as `└──[D2 1N5817]──[FB2]──[C2 47µF]──┬──────── PWR_GND (star)` — a
Schottky and a bead in series into the ground star, which is not a supply
branch at all.

So: **two pages** say A, **five places including a settled tracked figure and a
qty-3 BOM row** say B, and the drawing says neither. This is precisely the class
CLAUDE.md §5 says a grep cannot reach — every one of these statements is
individually true-looking, and the checker passes.

**What it costs, quantitatively** `[calc]`, at `umbilical-current`:

| Element | Drop at 359 mA | Source |
|---|---|---|
| 4 m of 24 AWG (round trip 0.337 Ω) | 121 mV | `[calc]`, matches `[repo] 0005:95` |
| `R-ILIM` 50 mΩ | 17.9 mV | `[repo] bom.csv R-ILIM` |
| FET at ~50 mΩ | 17.9 mV | assumption, `[repo] umbilical-load-switch.md:159-162` |
| `D2` 1N5817 `V_f` | **277 mV** | `[calc]` interpolated on the banked curve: 0.24 V @ 245 mA → 0.36 V @ 612 mA, `[repo] fig:diode-split-rationale` |
| `FB2` DCR 0.080 Ω max | **28.7 mV** | `[datasheet] MI1206K601R-10-ferrite-bead.pdf`, quoted `[repo] bom.csv:113` — "28.7 mV at 359 mA" |

- **Topology A**: arrives at **11.84 V** (rack at 12.00) / **11.24 V** (rack −5 %)
- **Topology B**: arrives at **11.54 V** (rack at 12.00) / **10.94 V** (rack −5 %)

**The consequence that actually bites is at the `FB` divider, not at the buck.**
`umbilical-load-switch.md:158-166` `[repo]` sizes `R-FB-HI`/`R-FB-LO` by an
explicit worst-case-output argument that assumes **Topology A**: "Eurorack +12 V
at −5 % is 11.4 V; `R-ILIM` at 50 mΩ drops exactly 20 mV at 0.4 A, and the FET
drops about the same … so the worst-case output is **~11.36 V**", against a
worst-case `PWRGD` release of **10.93 V** — "~0.4 V worst-case margin", and "at
200 mΩ the output is 11.30 V and the margin is still 0.37 V."

Re-run under Topology B `[calc]`, adding `D2` at 0.4 A (`V_f` ≈ 0.291 V) and
`FB2` at 0.080 Ω:

| FET `R_DS(on)` | Worst-case output | `PWRGD` worst-case release | Margin |
|---|---|---|---|
| 50 mΩ | **11.04 V** | 10.93 V | **0.11 V** (was 0.4 V) |
| 200 mΩ | **10.98 V** | 10.93 V | **0.05 V** (was 0.37 V) |

**The margin the divider was chosen to have is 0.4 V; under the topology five
other places assert, it is 0.05–0.11 V** — and the page explicitly says that
0.4 V is "what absorbs" an unknown FET, which is still TBD. If Topology B is the
real one, `PWRGD` can assert-then-release around the delivered rail on a −5 %
rack with a mediocre FET.

**Recommendation:** decide this before anything else in this slice. It is one
sentence of hardware and it moves a settled tracked figure, a BOM quantity, a
drop budget and a divider.

### A5-2 — the arrival voltage is load-bearing, restated three times, and not tracked

11.4 V is the denominator of `umbilical-current`'s derivation, so every figure
downstream of it moves when it moves. It is **not in `config/figures.yaml`**,
and the corpus carries three live values for it, each with a different chain:

| Value | Where | Chain |
|---|---|---|
| **~11.4 V** | `[repo] 0005:95` | 12.00 − (122 mV cable + **400 mV Schottky** + 60 mV) |
| **~11.5 V** | `[repo] 0004:281-283` | "A 1N5817 drops roughly 0.3–0.4 V at this current, leaving **~11.5 V** at the instrument after cable drop" |
| **~10.96 V** | `[repo] bom.csv:2` `U-BUCK` note | rack at **11.4 V** − 0.28 V Schottky − 36 mV of `R-ILIM`+FET − 121 mV cable |

Three problems, on top of A5-1:

1. **The Schottky drop is stated as 400 mV in one place and 280 mV in another**,
   for the same part at the same current. The **280 mV is right** — it follows
   the banked 1N5817 curve that `fig:diode-split-rationale` was rebuilt on
   `[calc]`, 277 mV. The **400 mV in ADR 0005 is an unsourced estimate of the
   same class the project already corrected once** ("`V_f` modulation at
   75–80 mV, 120 mV off the curve", CLAUDE.md §3). It sits in the table that
   sets the arrival voltage.
2. **`11.4 V` means two different things** and the collision is invisible.
   In ADR 0005 it is the *arrival* voltage at nominal rack; in the `U-BUCK`
   note and in `umbilical-load-switch.md:159` it is the *rack rail at −5 %*.
   The `U-BUCK` note then subtracts the whole drop chain from it a second time.
   That note is the **more conservative and more correct** of the two — but a
   reader who takes 11.4 V from either and uses it in the other's sense is
   double-counting or under-counting ~0.6 V, and nothing in the corpus flags
   that the same numeral is two quantities.
3. **Neither `60 mV` (ADR 0005) nor `36 mV` (BOM) is attributed.** 36 mV is
   reproducible as `R-ILIM` + a 50 mΩ FET at 360 mA `[calc]` = 35.8 mV. 60 mV
   is not reproducible from anything in the corpus.

**This quantity has every property of the project's named failure mode:** it is
derived, it is cited from three documents, it has three live values, and it is
the input to a figure that *is* tracked. It belongs in `config/figures.yaml`
with the drop chain as its `derivation`, so that the chain and the value cannot
diverge again.

**Does the conclusion survive?** Yes, in every reading `[calc]`: 11.24 V
(Topology A, rack −5 %) through 11.84 V (Topology A, nominal) gives
`umbilical-current` between **354 and 360 mA**, and the R-78E5.0's **8 V**
minimum has ≥ 2.9 V of headroom in the worst case. The buck is not at risk. The
divider (A5-1) and the 5 V node (A5-10) are.

### A5-4 — `CABLE-UMB`: the gauge that every drop calculation assumes is not specified

Three documents compute against **24 AWG**:

- `[repo] 0005:91` — "Over 2 m of 24 AWG, round trip ~0.34 Ω"
- `[repo] 0003:315` — "Drop across 2 m of 24 AWG"
- `[repo] breath-sense-link.md:100` — "0.168 Ω for 2 m of 24 AWG"

The BOM row that specifies the actual part says: **"Cat5e STP patch lead,
**STRANDED**, ~2m"** with no gauge at all `[repo] hardware/bom.csv:116`, and the
row's whole reasoning is about flex life, not conductor size. **Stranded Cat5e
patch leads are commonly 26 AWG, and slim ones 28 AWG** `[from memory]`.

`[calc]`, at 20 °C:

| Gauge | Round trip (4 m) | Drop at 359 mA | Drop at the 0.94 A limit |
|---|---|---|---|
| 24 AWG (0.0842 Ω/m) | 0.337 Ω | **121 mV** | 317 mV |
| **26 AWG (0.1339 Ω/m)** | **0.536 Ω** | **192 mV** | **503 mV** |
| 28 AWG (0.2128 Ω/m) | 0.851 Ω | 306 mV | 800 mV |

At 26 AWG the cable drop is **+71 mV** over what every document assumes, and
stranded conductors add a further ~2 % over solid of the same gauge
`[from memory]`. Combined with Topology B and a −5 % rack that is another
70 mV off an already 0.05 V `PWRGD` margin (A5-1).

It also reaches `breath-sense-link`'s `AGND` return-drop budget and ADR 0003's
signal-current table, which are outside my slice but share the same conductor.

**The fix is one word in one BOM row** — name the gauge — and it closes a
dependency that four derivations currently take on faith.

### A5-5 — ADR 0004 sizes the umbilical against a buck minimum that is wrong by 2 V

`[repo] docs/decisions/0004-cv-interface-module.md:281-283`:

> "A 1N5817 drops roughly 0.3–0.4 V at this current, leaving ~11.5 V at the
> instrument after cable drop, **against a buck that needs more than 6 V in**.
> Ample."

The part needs **8 V** `[datasheet] R-78E5.0-1.0.pdf` — the selection table
gives R-78E3.3-1.0 = 7–28 V and R-78E5.0-1.0 = **8–28 V**, corroborated in this
review by the efficiency charts (a **7 Vin** trace on the 3.3 V part's chart, an
**8 Vin** trace on the 5.0 V part's) `[datasheet] p. I-2`.

The `U-BUCK` BOM row records this in capitals and states the exact hazard:
"**Recorded because a future reader sizing the umbilical against '7V' would be
working to the wrong part**" `[repo] hardware/bom.csv:2`. **ADR 0004 is that
reader, and it is working to 6 V, which is not even the trap the row warns
about.** The conclusion ("Ample") survives — 2.9 V of real margin — but the
number a future reader would take from the ADR that *owns* the umbilical is
2 V optimistic.

### A5-6 — ADR 0004's series-resistor table: header updated, cells not

`[repo] docs/decisions/0004-cv-interface-module.md:271-278`:

> "…it **rules out the series-resistor variant**, which is harmless at 50 mA and
> is not at **290 mA**:
>
> | Series R | **Drop at 359 mA** |
> | 2.2 Ω | **0.64 V** |
> | 10 Ω | **2.90 V** |"

`[calc]` At 359 mA: `2.2 × 0.359 = 0.79 V` and `10 × 0.359 = 3.59 V`. The stated
cells are `0.64 / 2.2 = 291 mA` and `2.90 / 10 = 290 mA`. **Both cells are the
old 290 mA values under a header that was updated to 359 mA**, and the
surrounding prose still says 290 mA one line above.

`"Drop at 290 mA"` is in `umbilical-current`'s `forbidden` list
`[repo] config/figures.yaml:464` — and it caught the **header** and missed the
prose sentence and both cells, because the prose spells it "is not at 290 mA"
and the cells are bare numerals. **This is the seventh-spelling failure
CLAUDE.md §2 describes, live, in the document that owns the umbilical**, and it
is worth recording as a worked example: the pattern list was written from the
one spelling the editor was looking at.

### A5-9 / A5-10 — `D-USBOR`: wrong package, and a 5 V node that falls out of spec

**A5-9, package.** `[repo] hardware/carrier/power-entry-instrument/bom.csv:6` —
`D-USBOR,controller,1N5817 or SS14,…,DO-41 THROUGH-HOLE,2`. The schematic page's
component table names the part unambiguously as **`SS14`**
`[repo] power-entry-instrument.md:125`. The SS14 is
**"Case: SMA (DO-214AC)"** `[datasheet] datasheets/discrete-and-power/SS14.pdf
p.1, MECHANICAL DATA`. DO-41 is the 1N5817's package. The row names two parts
with different packages and lists only one.

This is **the same defect, in the same BOM fragment, two rows from the one that
was corrected for it on 2026-09-21** — `D-REVSHUNT` had "DO-214AC, which is the
SS14's package" and was moved to DO-214AB `[repo] same file, D-REVSHUNT note`.
The correction landed on the row being edited and not on its neighbour. That is
CLAUDE.md's opening paragraph, exactly.

**A5-10, the 5 V node.** The BOM row asserts "Both sources drop ~0.3V, leaving
**~4.7V** at the dev boards' 5V pins - fine for their onboard LDOs"
`[repo] same row`. Neither term is a guaranteed number:

- `[datasheet] R-78E5.0-1.0.pdf p. I-2, REGULATIONS`: **"Output Accuracy ±3.0 %
  typ. / ±5.0 % max."** → the buck output is specified only to **4.75–5.25 V**.
  This figure appears **nowhere in the corpus**.
- `[datasheet] SS14.pdf p.2, ELECTRICAL CHARACTERISTICS`: **"Maximum
  instantaneous forward voltage, 1.0 A, V_F = 0.50 V"** (pulse test, 300 µs,
  1 % duty, T_A = 25 °C). At buck A's clamp-legal 680–780 mA
  `[repo] power-entry-instrument.md:88-94` the max-spec `V_F` is ≈ **0.47 V**;
  0.30 V is a typical at a lower current and a warmer junction.

`[calc]` Worst-case stack: `5.00 × 0.95 − 0.47 = ` **4.28 V**. Even with the
typical 0.30 V diode: `4.75 − 0.30 = ` **4.45 V**.

**The `74AHCT125` sits on this node** — `[repo] power-entry-instrument.md:45-47`
draws `[R-78E5.0 A]──▷|──┬── dev board 5V / ├── 74AHCT125`, and the Interfaces
table confirms "Through `D-USBOR` onto the dev board's 5 V pin"
`[repo] power-entry-instrument.md:21`. The SN74AHCT125 is specified over
**VCC = 4.5–5.5 V** `[from memory]`, and its datasheet is banked
(`datasheets/logic/SN74AHCT125.pdf`) but could not be text-extracted in this
sandbox — **this specific number should be read off it before the finding is
actioned.**

**What breaks, and what does not:**

- The buffer's rail is **below its specified minimum VCC** at the guaranteed
  corner. The TTL input thresholds that are the *entire* reason ADR 0014 chose
  this part `[repo] 0014:104-110` are specified over that range.
- `led-strip-drive.md:98` `[repo]` states "the 74AHCT125 **at 5 V** delivers
  **~4.4 V minimum**" into the WS2815's `V_IH` of 3.15–3.85 V. That derivation
  is on the **wrong rail** — the buffer is not at 5 V, it is at ~4.7 V nominal
  and 4.28 V worst case. Two live values for one node.
- **The link still works.** The WS2815's `DI` is a high-impedance input, so the
  applicable `V_OH` spec is the µA column (≈ VCC − 0.1 V), giving ~4.2 V against
  a 3.85 V worst-case `V_IH` — **0.35 V of margin, not the ~0.55 V claimed**.
  The conclusion survives; the stated margin and the stated rail do not.

**A5-21 note (heat):** `[calc]` buck A's `D-USBOR` at 780 mA × ~0.45 V =
**0.35 W** dissipated inside the sealed body, in a part whose typical
`RθJA` is **88 °C/W** `[datasheet] SS14.pdf p.2, THERMAL CHARACTERISTICS` (on
the datasheet's 5.0 × 5.0 mm pads) — a ~31 K local rise. Neither watt nor rise
appears in any thermal accounting.

---

## 3. The input LC and the negative-resistance hazard

**The analysis is present, is arithmetically correct, is assigned to two places
under one stale path, and does not cover the hazard the open item names.**

### The derivation itself checks out

`[repo] power-entry-instrument.md:67-84`. Re-derived `[calc]`:

- `f0 = 1/(2π√(22 µH × 100 µF)) = 3.393 kHz` ✓ (page: 3.39 kHz)
- `Z0 = √(22 µH / 100 µF) = 0.469 Ω` ✓
- `Q ≈ Z0/ESR = 0.469/0.5 … 0.469/1.0 = 0.94 … 0.47` ✓ (page: 0.5–0.9)
- `R_neg = −V²/P = −11.4² / 1.26 = −103.1 Ω` ✓
- margin `103 / 0.47 = 219×` ✓ (page: ~220×, 47 dB)

The ESR-dependence warning and the "keep it electrolytic" instruction are right
and are matched by the BOM row `[repo] bom.csv C-BUCK-IN, "100uF 25V
electrolytic"`. **This is good work and should not be weakened.** Three defects
sit around it.

### A5-7a — it is evaluated at the wrong load case

A negative-resistance bound must be taken at **maximum** load, where `|R_neg|`
is smallest. The page uses **typical play** (1.26 W in). `[calc]` At
clamp-legal worst the 5 V branch draws `928 mA × 5 V / 0.885 = 5.24 W`, so
`R_neg = −11.4² / 5.24 = −24.8 Ω` and the margin is **53×, not 220×**. Still an
enormous margin, so **the conclusion holds** — but the page reports the
comfortable case as if it were the bound, and a reader who later reduces `L`,
raises `C`, or moves buck B will re-use the method.

### A5-7b — it covers a different LC from the one the open item names

The page says it "partly closes … the 'damping the input LC' open item".
The open item, in full `[repo] umbilical-load-switch.md:355-359`:

> "**Damping the input LC.** `L-BUCK-IN` (10–47 µH) in front of a constant-power
> switching load, **with 2 m of cable and ~2 mF at the far end**, is the
> textbook negative-resistance instability and no damping leg is specified."

The named hazard has **three** elements — `L-BUCK-IN`, the **cable inductance**,
and the **~2 mF of `C-STRIP-BULK`**. The instrument page analyses only
`L-BUCK-IN` against `C-BUCK-IN` (100 µF), which is the *innermost* loop. The
cable-inductance loop is untouched.

I ran it `[calc]`, with Cat5 loop inductance taken as `Z0/v = 100/(0.65 × 3×10⁸)`
≈ **0.51 µH/m** `[from memory]`, so ~1 µH over 2 m, against 2.2 mF:

- `f0 = 1/(2π√(1 µH × 2.2 mF)) = 3.39 kHz`
- `Z0 = √(1 µH / 2.2 mF) = 0.021 Ω`
- the cable's own DC resistance is **0.337 Ω at 24 AWG** (0.536 Ω at 26 AWG),
  i.e. **16–25× `Z0`** → `Q ≈ 0.06`, massively overdamped

**The outer loop looks harmless, and for a good reason the corpus never
states:** the umbilical is long enough that its resistance damps its own
inductance. That is a two-line result and it is the half of the open item
nobody has written down. **It should be written down and the item closed on it**
— not left as "partly closed" by an analysis of a different network.

*(Caveat, marked: my `0.51 µH/m` is from memory, not a datasheet, and
`CABLE-UMB` is `open` with no gauge — see A5-4. The margin is 16–25×, so the
conclusion is not sensitive to it, but the number should be sourced before it
goes in a page.)*

### A5-8 — the item is in two places under one stale path, and its assigned test cannot close it

- It **lives** at `[repo] hardware/module/umbilical-load-switch/umbilical-load-switch.md:355`.
- `[repo] hardware/module/power-entry/power-entry.md:163-165` correctly records
  that it moved there.
- `[repo] hardware/carrier/power-entry-instrument/power-entry-instrument.md:67-68`
  cites it as **"`power-entry.md`'s 'damping the input LC' open item"** — the
  pre-split location. A reader following that pointer lands on a page whose only
  remaining content on the subject is a note saying it went elsewhere.
- **And it is assigned to two ends.** The instrument page closes "the instrument
  end only"; the module page owns the item. `L-BUCK-IN` and `C-BUCK-IN` are both
  **instrument-side parts** `[repo] hardware/carrier/power-entry-instrument/bom.csv`
  — the open item is filed on the module page for a network that is entirely on
  the carrier. CLAUDE.md's hardware convention is that a row lives with the
  circuit whose page derives its value; the same should hold for the open item.

**A5-8b — `E11` cannot close it.** The item says "Put it on **E11** with the
real cable" `[repo] umbilical-load-switch.md:359`. ROADMAP:

> "**M8 exists because E11 tests a topology that does not survive to the
> finished instrument.** **At E11 the LED strips are not installed** — they
> arrive at M6" `[repo] ROADMAP.md:105-107`

The hazard is defined as "~2 mF at the far end", and `C-STRIP-BULK`
(470–1000 µF **×2**, i.e. **0.94–2.0 mF of the 2.2 mF**) arrives with the
strips at M6. **E11 would test the cable against ~0.2 mF** — under a tenth of
the capacitance the item is about. The corpus already knows E11 is not the final
topology and created M8 for precisely that reason; this item was left pointing
at E11 anyway. It belongs at **M8**, alongside the thermal soak.

### A5-7c — the LC the page analyses may not be the LC that gets built

`[repo] power-entry-instrument.md:123` flags it as contradictory and the page's
own *Still open* repeats it: **`L-BUCK-IN` qty 1 against `C-BUCK-IN` qty 2.**
The derivation is run at `L = 22 µH, C = 100 µF` — one inductor, **one**
capacitor — which is neither of the two topologies the BOM describes. `[calc]`
If it is one L feeding both bucks with 200 µF, `f0 = 2.40 kHz` and
`Z0 = 0.33 Ω`; the margin rises to ~310× and the conclusion is unchanged, but
**the stated derivation matches no buildable configuration.** I confirm the
existing flag rather than adding to it.

---

## 4. Heat

### The arithmetic reproduces

`[calc]` Dissipation = arriving power, since nothing leaves the body but light:

| State | Umbilical | × 11.4 V | ADR 0005 "Body heat" |
|---|---|---|---|
| Quiescent | 212 mA | 2.42 W | 2.4 W ✓ |
| **Typical play** | **359 mA** | **4.09 W** | **4.1 W** ✓ |
| Typical + WiFi | 414 mA | 4.72 W | 4.7 W ✓ |
| Clamp-legal worst | 579 mA | 6.60 W | 6.5 W ✓ |
| Clamp fails | 1522 mA | 17.35 W | ~17 W ✓ |

**At the tracked figure the instrument dissipates 4.09 W inside a sealed oak and
acrylic body.** That column is the one internally consistent thing in the load
table.

### A5-11 — the 3 K/W chain is three restatements deep with nothing at the bottom

```
  "10–20 K interior rise"   ← no derivation anywhere in the corpus
        │  restated in 8 documents, twice as "documented"
        ▼
  "roughly 5 W for 10–20 K, so call it ~3 K per watt"   [repo] 0014:146-148
        │
        ▼
  "~3 W lighting clamp … costs roughly 9 K"   [repo] 0014:176-179
        │
        ▼
  a hard, deliberately non-configurable firmware limit
```

The 10–20 K appears at `[repo] 0001:212`, `0003:202`, `0003:243`, `0006:277-278`,
`0007:210-211`, `0009:531`, `key-switch-network.md:118`,
`power-entry-instrument.md:97`. **Two of them call it documented** —
`0007:210` "inside a sealed body with a **documented** 10–20 K interior rise"
and `0005:312` "at the **documented** interior rise" — and nothing documents it.
ADR 0014 is the one document that is honest: "**That figure is a bounding
estimate, not a measurement**", validate at M8 `[repo] 0014:183-184`, and
ROADMAP carries the M8 row `[repo] ROADMAP.md:192`. **The honesty exists in one
place and the word "documented" exists in two others.**

### A5-11b — the clamp's 9 K is additive to a baseline the rest of the corpus treats as total

ADR 0014 derives 3 K/W from "**the existing electronics** dissipate roughly 5 W"
and then tables lighting as an **addition** ("Realistic use ~1.5 W | Interior
rise **it would add** ~4 K") `[repo] 0014:146-155`. So by the ADR's own
construction, a clamped instrument is `5 W + 3 W = 8 W` → **24 K**, and its
verdict "9 K … **inside what the design already tolerates**" `[repo] 0014:178`
compares the increment against the total.

Every downstream analysis uses 10–20 K as the whole story: ADR 0003's sealed
reference-chamber case (`5.2 kPa` at a 10–20 K rise, `[repo] 0003:199-202`),
ADR 0003's `0.5 mV/K` jack drift at a 20 K rise `[repo] 0003:638`, ADR 0007's
IMU siting `[repo] 0007:210`, ADR 0009's adhesive service limit
`[repo] 0009:531`. **If the clamped instrument runs at 19–29 K, those four
analyses are being run at roughly half the real rise.**

### A5-11c — and the 5 W baseline does not match ADR 0005

`[calc]` At clamp-legal worst, ADR 0005's 6.60 W decomposes as **3.0 W of
commanded light** (600 mA × 5 V, the clamp spent entirely on the matrix) plus
**3.6 W of everything else**. So ADR 0005's non-light baseline is **3.6 W**, not
the "roughly 5 W" ADR 0014 divides 10–20 K by. Taking 3.6 W instead gives
**2.8–5.6 K/W**, and the 3 W clamp then costs up to **17 K**, not 9 K.

**Two accepted ADRs disagree about the total dissipation at the clamp by ~1.5 W
(23 %), and the K/W figure that the clamp is sized from depends on which is
right.**

### A5-11d — "every watt leaves through the aluminium plate" is not supported, and points the wrong way

README: "**Every watt leaves through the aluminium plate**, part of which is
under the player's hands" `[repo] README.md:77-79`, echoed at
`[repo] 0014:145-147`. There is no calculation behind it anywhere.

`[calc]`, first order, with assumptions stated. Body 457 mm long, 57 mm wide
`[repo] 0009:591,671`; take the plate as ~400 × 57 mm = **0.023 m²**, one face
exposed:

- convection, `h ≈ 1.32·(ΔT/L)^¼` with `L = A/P = 0.025 m` at ΔT = 15 K →
  `h ≈ 6.5 W/m²K` → **2.2 W**
- radiation, `h_r ≈ 4εσT³` at 300 K → 4.9 W/m²K at ε = 0.8 (anodised) → **1.7 W**,
  but only **0.2 W** at ε ≈ 0.1 (bare mill aluminium)

**The plate alone is 2.4–3.9 W at a 15 K rise, i.e. 3.8–6.2 K/W — worse than the
3 K/W the clamp is sized on, not better.** The oak shell (~0.09 m² of outer
surface, `k ≈ 0.16 W/m·K` through ~8 mm, in series with a ~7 W/m²K surface film)
comes out around **5 W/m²K overall → ~6.7 W at 15 K**, i.e. **the wood is the
larger path, not the plate**.

**So the stated number and the stated mechanism contradict each other: 3 K/W is
defensible only if README's "every watt leaves through the aluminium plate" is
false.** Both cannot be kept. Two practical consequences: the plate's **surface
finish** (anodised vs bare) is a thermal decision nobody has recorded as one,
and covering the plate with hands removes convection from the covered area while
adding conduction into skin — which is not obviously a loss and is currently
assumed to be one.

*(All of §4's numbers here are `[calc]` from standard correlations `[from
memory]`, with assumed emissivity and an assumed plate area. They are an order-
of-magnitude check on an unsourced figure, not a replacement for M8.)*

### A5-12 — ADR 0014's `~17.7 W` is computed at the efficiency ADR 0005 refuted

`[repo] 0014:150-155`, "Matrix full white as well | **~17.7 W** | **~53 K**".

`[calc]` `12.1 W (strips, direct from 12 V) + 4.8 W (matrix at the LEDs) / η`:

- at **η = 0.85**: `12.1 + 5.65 = ` **17.75 W** ← matches the ADR exactly
- at **η = 0.90**: `12.1 + 5.33 = ` **17.43 W** → 52 K

ADR 0005 explicitly corrects this convention: "the buck is **~90 % efficient**
at a 12 V input, **not the 85 % this document used** — 85 % is the 28 V-input
figure" `[repo] 0005:171-172`. **ADR 0005 caught the sibling error in the same
ADR and missed this one.** It caught the `×0.49` factor and stated why it
survives — "(ADR 0014's ×0.49 umbilical conversion factor survives by
coincidence: two ~6 % errors in opposite directions)" `[repo] 0005:174-176`,
which I verify `[calc]`: `5/(0.85 × 12.00) = 0.4902` and
`5/(0.90 × 11.4) = 0.4873`. **The cancellation is a property of the current
conversion only.** A power figure has no second error to cancel against, so
17.7 W carries the full 85 % error and was not looked at.

Small numerically (0.3 W, 1 K). Recorded because it is a live instance of the
named failure mode *inside the correction that fixed its sibling*.

### A5-13 — the strips' quiescent draw is invisible to the clamp and is half its budget

ADR 0005 `[repo] 0005:344`: killing the buck "leaves roughly **120 mA of strip
quiescent draw** and the strips holding their last latched colours". ADR 0005's
quiescent 12 V-direct column (123 mA) is consistent with it.

`[calc]` **120 mA × 12 V = 1.44 W, drawn whenever the instrument is powered,
whatever the strips are showing.**

The clamp is "a single instrument-wide lighting budget of ~3 W … **enforced in
firmware before any write**" `[repo] 0014:170-172`. Firmware can only sum
*commanded* channel values. **Quiescent driver current is not a write and cannot
be in that sum.**

So at ADR 0014's own "realistic use" the lighting hardware actually dissipates
`1.5 W commanded + 1.44 W strip quiescent + ~0.25 W matrix idle` ≈ **3.2 W** —
**the clamp's entire budget, at a state the ADR calls "unremarkable against a
3 W budget"** `[repo] 0014:225-227`. At the clamp limit the real figure is
~4.7 W.

**The clamp is a 3 W limit on roughly 65 % of the lighting load.** ADR 0014's
current table (`[repo] 0014:130-133`) is LED current only — the 30/m and 60/m
rows reduce cleanly to 20.2 mA/LED at full white `[calc]`, with no quiescent
term anywhere. This does not make the clamp wrong; it makes its **thermal
headline (`~1.5 W`, `~4 K`) understate the real dissipation by about 1.7 W**,
which is more than half the budget it is being compared against, and it feeds
straight into A5-11c.

---

## 5. Fault current

README: "**Fault current**, which a larger supply makes *worse*, not better"
`[repo] README.md:82`. Conductor by conductor:

| `J-UMB` pin | Net | What limits fault current | Verdict |
|---|---|---|---|
| **3** | `+12V` | `LT1641-1` + `R-ILIM` 50 mΩ → **0.78 / 0.94 / 1.10 A**, latch-off `[repo] umbilical-load-switch.md:44-48` | **Protected**, and inside the connector's **1.5 A per contact** `[datasheet] NE8FDP, quoted at [repo] bom.csv J-UMBILICAL` |
| **6** | `PWR_GND` | same element (series return) | Protected against shorts; **see A5-19 for the open-circuit case** |
| 1 | `BREATH` | `D-TVS-BREATH` 12 V standoff at the instrument; 10 kΩ + `D-CLAMP-BREATH` BAV99 at the module. ADR 0003 designed the buffer onto +12 V so that a **sustained +12 V fault on `BREATH` is harmless** `[repo] bom.csv D-TVS-BREATH` | **Well protected** — the best-reasoned conductor in the cable |
| 2 | `AGND` | 10 kΩ series + `R-BIAS-INAMP` 1 MΩ at the in-amp | Protected (~1.2 mA at 12 V, `[calc]`) |
| **4, 5, 7** | `SCLK`, `MOSI`, `CS` | `R-SPI-SER` **100 Ω** at the *driving* end; `U-TVS-SPI` 5 V array at the instrument connector; **nothing at the module end** | **A5-18 — unprotected against a +12 V short** |
| 8 | `DIG_GND` | none needed for shorts | see A5-19 |

### A5-18 — a +12 V-to-signal short is bounded by nothing either end survives

`R-SPI-SER` at 100 Ω is sized and justified as a **transmission-line source
termination**, and its fault-current role is explicitly about the *driver*: "it
resolves in one transit and **draws 33 mA into a clamp**" `[repo]
spi-link.md:68`. It sits between the ESP32 pin and the connector, so it limits
what the **instrument's output** can push. It does **not** sit between the
umbilical conductor and anything.

A crushed cable or a half-inserted connector shorting pin 3 to pin 4/5/7 — the
exact faults ADR 0005 names as the load switch's reason for existing
`[repo] 0005:266-269` — puts the umbilical rail onto a logic net with:

- **At the instrument end:** `U-TVS-SPI`, whose package power is **0.225 W**,
  sourced `[repo] bom.csv U-TVS-SPI` from the banked Littelfuse extract
  (`datasheets/discrete-and-power/SP0504BAHT.pdf` p.2 Abs Max, corroborated
  p.7 "PD@70degC .225W"). `[calc]` A clamped conductor at ~10 V and even
  400 mA is **4 W into a 0.225 W part.**
- **At the module end:** nothing. `U-TVS-MODULE` is `status=open`
  `[repo] bom.csv:131` — "DELIBERATELY open, not forgotten … Fit at E12 if E11
  gives any reason to". So 12 V arrives at a `74AHCT125` input whose absolute
  maximum is VCC + 0.5 V `[from memory]`, and its input protection diode
  conducts **into the rack's bus +5 V rail** — which ADR 0004 deliberately gives
  **no series diode** ("The bus +5 V pin gets no diode: the only thing on it is
  a $0.30 buffer" `[repo] power-entry.md:141-143`).

**So an instrument-end cable fault has a conducting path into the rack's shared
+5 V rail, through a part chosen on the argument that killing it costs $0.30.**
The load switch cannot see this fault: 12 V through a clamp is well under its
0.78 A floor, so it neither limits nor latches until something fails short.

The corpus already contains the half of this that was found from the part side —
`U-TVS-SPI`'s row concludes "**the right fix is a series resistor or a
resettable element, not a bigger array**" `[repo] bom.csv U-TVS-SPI`. That
sentence is a conclusion in a BOM note with **no owning page, no open item and
no milestone**. It should be an open item on `spi-link.md`, and the +12 V-to-
signal case should be the thing that decides `U-TVS-MODULE` rather than "if E11
gives any reason to" — E11 will not give a reason, because E11 does not short
the cable.

**README's claim is upheld, and is sharper than it reads:** a larger supply
makes faults worse on the **six conductors the load switch does not watch**. On
pins 3 and 6 the limiter makes the rack's size irrelevant, which is exactly what
it was bought for.

### A5-19 — `J-UMB` pin 6 open-circuit: ~360 mA silently moves to `DIG_GND`

`CABLE-UMB` is specified as a flexing **consumable** — "keep spares and replace
at the first intermittency" `[repo] bom.csv:116` — so a single conductor failing
open is a designed-for event, not a hypothetical.

If **pin 6 `PWR_GND`** opens while the rest of the cable is intact, the
instrument's return has exactly one remaining path: **pin 8 `DIG_GND`**, which
is tied to the same pour at the instrument end. (`AGND` cannot take it — it is
an in-amp input behind 1 MΩ bias resistors, not a ground `[repo] 0003`,
`power-entry.md:153`.)

The whole of ADR 0004's grounding argument is that this must never happen:

> "If `PWR_GND` shares copper with the analog return for even a centimetre,
> **360 mA** develops an IR drop across that shared length … a review measured
> this as **5.7–7.2 cents of breath-correlated pitch bend**"
> `[repo] 0004:624-630`

A broken pin 6 puts the **entire** 360 mA into the digital return, at whatever
the cable conductor's resistance is (0.34–0.85 Ω, A5-4) **plus** every shared
millimetre at the module end. **Nothing detects it.** The instrument still runs,
the lights still work, and the pitch output acquires a large breath-correlated
error that looks like a design fault.

Not a request for a part — it is one sentence of analysis and, if `link-
supervision` can see it, one supervision case. It is filed here because
"whether any conductor is unprotected" is answered `no` for shorts and **`not
analysed` for opens**, and the open case is the one the cable is expected to
suffer.

---

## 6. The LED strips, and honesty about an unmeasured number

`fig:matrix-led-current` is `status: blocked`, `decided_by: "A BENCH
MEASUREMENT AT E1"` `[repo] config/figures.yaml:516-526`. **The register entry
is exemplary** — it names three candidates, names which is wrong and why, names
why no document can close it, and carries `supersedes_the_constraint`. Nothing
below criticises the entry.

### A5-20 — the 3 W clamp has never been checked against the constraint the register says is binding

The register states the real limit `[repo] config/figures.yaml:524`:

> "**THE 1 A R-78E5.0 IS NOT WHAT STOPS THE MATRIX FIRST.** All 64 LEDs draw
> through one B5819WS Schottky in SOD-323 … `P_D` 200 mW and `RθJA`
> 500 °C/W … which is **~435 mA at 25 °C and ~283 mA at a 60 °C interior**
> `[calc at V_F ~0.46 V]` … **ADR 0014's brightness cap is RIGHT and its
> JUSTIFICATION IS WRONG.**"

`[calc]` The clamp is **~3 W across strips and matrix**, and ADR 0014's own
worked example says "on the matrix it is … a full field at around 60 % of one
channel" — i.e. the clamp permits the entire 3 W to be spent on the matrix, at
`3 W / 5 V = ` **600 mA**.

**600 mA is 1.4× the B5819WS's 435 mA at 25 °C and 2.1× its 283 mA at the 60 °C
interior the same register names.** So the clamp as specified permits a state
that destroys the dev board's power path — which is the failure Waveshare's own
wiki warns about five times, quoted in the ADR `[repo] 0014:462-465`.

**"ADR 0014's brightness cap is RIGHT" is not established.** It is right against
the 960 mA it was written for. It has never been evaluated against the 283–435 mA
the register now says is the binding limit. **The conclusion was carried over
when the reason under it was replaced** — CLAUDE.md §5's `mod-channels.md`
shape, on a live figure.

*(Caveat, marked: whether matrix current actually passes the `B5819WS` when the
board is fed from the umbilical depends on whether the header's `5V` pin lands
on `VBUS` or on `VCC_5V`. The register and ADR 0014 both assert it does
`[repo] figures.yaml:524`, `0014:449-456`, from the banked Waveshare schematic.
If that is wrong the finding dissolves — and it is worth confirming at E1
alongside the current probe, because it is the difference between a 3 W clamp
being safe and being destructive.)*

### A5-21 — the strips' current figure is the least-sourced number in the whole thermal chain

`matrix-led-current` is blocked, loudly, and every document that touches it says
so. **The strips have no equivalent and are the larger load.**

Every strip figure in the corpus traces to ADR 0014's density table
`[repo] 0014:130-133`, which reduces to **20.2 mA per LED at full white**
`[calc]`, 1.01 A for 50 LEDs. From that one number come:

- `12.1 W` for both strips full white, and `~36 K` `[repo] 0014:150-154`
- `1.01 A` in ADR 0005's "clamp fails" row and the ~1522 mA umbilical that
  argues the limiter trips `[repo] 0005:161`
- `~1.5 W` "realistic use", the headline the 3 W clamp is presented against
- the `~120 mA` strip quiescent (A5-13)

**None of these carries a provenance mark.** There is no `[datasheet]`, no
`[calc]`, no `[web]`, no `[from memory]` on any of them — and CLAUDE.md is
explicit that "an unmarked claim is a defect in the report", which should hold
at least as strongly for the corpus.

**And the datasheet is banked.** `datasheets/led/WS2815.pdf`, Worldsemi V1.1,
SHA-256 in the manifest `[repo] datasheets/MANIFEST.csv`. It was read by hand
on 2026-09-21 to settle `V_IH` — a 700 dpi render of the application-circuit
figure, no less `[repo] led-strip-drive.md:96-125`. **The same document, in the
same week, was not read for the current figure that sizes the entire thermal
budget and the clamp.** (I attempted extraction in this sandbox; the PDF is
CID-encoded and no `pdftotext`/`pypdf` is available here, so I cannot supply the
number — which is exactly why it should be read by whoever has a working
renderer, as the `V_IH` reading was.)

Per CLAUDE.md §3, "**a number read off a banked document beats one from a
review**". The strips' 20 mA/LED is currently a number from nowhere at all, and
it outweighs the matrix in every state except full-field white.

**Recommendation:** either read it off `WS2815.pdf` and mark it, or track it in
`config/figures.yaml` beside `matrix-led-current` with its own `decided_by`.
The asymmetry — the smaller, better-documented load is blocked and tracked,
while the larger, undocumented one is stated as fact in five places — is the
condition under which the next divergence happens.

### What the corpus does get right here, and should keep

Recorded because the review should also say where the practice worked:

- **`led-strip-drive.md`'s `V_IH` resolution** `[repo] 0014:104-116`,
  `led-strip-drive.md:96-125` — a symbol reused for two nets, caught by reading
  the table's own conditions header, with the wrong reading (8.4 V) preserved
  and explained. This is the correct handling of an ambiguous datasheet.
- **`R-LED-PD`** — the pull-downs that hold the strips quiet through the
  bootloader window `[repo] led-strip-drive.md:78-90`. It correctly identifies
  that ADR 0014's blank-at-boot rule "cannot run in the window it matters", and
  that the buffer will square up float into 25 addressable LEDs on a 12 V rail.
  Two 0805s against an unretrofittable hole; this is the single best finding in
  the slice and it is already in the corpus.
- **`fig:ferrite-bias-impedance`** — the `≥1 A` rule refuted by the datasheet
  that was bought to satisfy it, with the counter-example part banked alongside
  to prove the point `[repo] config/figures.yaml:528-535`. (Its FB2 half is
  conditional on A5-1.)
- **The `U-BUCK` BOM note** — 8 V minimum, the derating curve worked against the
  real interior temperature, 330 kHz confirmed, "short circuit protection is
  CONTINUOUS WITH AUTOMATIC RECOVERY, not latching". The best-sourced row in
  this slice, and the one ADR 0004 contradicts (A5-5).

---

## What I would fix first

1. **A5-1** — decide whether the umbilical passes `D2`/`FB2`. It moves a settled
   tracked figure, a BOM quantity, the drop budget and the `FB` divider's
   margin, and five documents currently cannot all be right.
2. **A5-10** — read `SN74AHCT125.pdf`'s VCC range off the banked file and settle
   the 5 V node against the **±5 % max** buck accuracy and the **0.50 V max**
   SS14 `V_F` that are both in banked documents and in no corpus page.
3. **A5-2 / A5-4** — track the arrival voltage in `config/figures.yaml` with its
   drop chain, and put a gauge in the `CABLE-UMB` row.
4. **A5-13 / A5-20** — state plainly that the clamp does not see strip
   quiescent, and check the 3 W limit against the 283–435 mA the register calls
   binding before E1.
5. **A5-11** — stop calling 10–20 K "documented", and reconcile ADR 0014's 5 W
   baseline with ADR 0005's 3.6 W before M8 measures something neither predicts.

Everything else is recorded above with its arithmetic.
