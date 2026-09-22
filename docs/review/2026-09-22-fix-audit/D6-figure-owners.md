# D6 — the `owner:` field of every entry in `config/figures.yaml`

**Slice:** all 37 figures. Does the named owner *state* the value, does it
*derive* it, and did the nine repoints in `0e68f25` land everywhere.

**Method.** Cold — nothing under `docs/review/**` was read. (Two corpus-wide
greps returned one-line hits from `docs/review/**` incidentally; those lines
were not opened and nothing below rests on them.) For each figure the owner
was opened and the statement located by hand; the corpus was then swept for
every other file that states the same value. `check_owners` was re-run in
isolation to see exactly which token it tests for each figure. The ferrite
curve was extracted from the banked PDF's content-stream geometry with
PyMuPDF rather than read off a render.

**Headline.** Two of the nine repoints landed on a page that does not state
the figure at all (`key-pullup-qty`, `ref5050-grade`); a third figure
(`inamp-full-scale`, repointed in an earlier commit) has two documents
claiming to own it. The two pages that had text *added* state correct numbers
but neither added a derivation, and one of the additions was inserted inside a
block that declares itself moved verbatim. `hardware/bom.csv` is gone from the
`owner:` field everywhere — that part of the fix is complete and correct.

---

## Coverage — one row per figure

`States?` = the owner contains the value as a statement about this quantity.
`Derives?` = the owner shows the reasoning that *sets* it, rather than
asserting or drawing it. `Chk` = what `check_owners` actually tested
(`[test] python3 -c "import check-staleness; check_owners(spec)"`, tokens
reproduced from the same code).

| # | figure | owner | Chk | States? | Derives? | verdict |
|---|---|---|---|---|---|---|
| 1 | `inamp-full-scale` | `interfaces/breath-sense-link/breath-sense-link.md` | `9.94` | yes, :165 | yes, :160–166 | **D6-2 — contested: `breath-receive-stage.md:45` says "Owned here."** |
| 2 | `sensor-full-scale` | `docs/decisions/0003` | `4.86` | yes, :101 | yes (transfer function) | ok |
| 3 | `breath-sensor-slope` | `docs/decisions/0003` | `0.7665` | yes, :123 | yes, :123 | ok (owner never names the id) |
| 4 | `breath-zero-ref` | `module/breath-receive-stage/…md` | `0.573` | yes, :121 | yes, :121–124 | ok — says "this page owns" and it does |
| 5 | `key-scan-current` | `cluster/key-switch-network/…md` | `1.43` | yes, :108 | yes, :105–108 | ok (owner never names the id) |
| 6 | `key-release-time` | `cluster/key-switch-network/…md` | `119.9` | yes, :105 | yes (τ shown) | ok |
| 7 | `key-press-time` | `cluster/key-switch-network/…md` | `5.92` | yes, :106 | yes (τ shown) | ok |
| 8 | `marker-bits` | `config/key-layout.yaml` | **UNCHECKED** | yes, :147 | no — ADR 0001:323, :336–341 decides it | **D6-11** |
| 9 | `free-bits` | `config/key-layout.yaml` | **UNCHECKED** | yes, :149 | no — ADR 0001:341 | **D6-11** |
| 10 | `chain-conductors` | `docs/decisions/0001` | **UNCHECKED** | yes, :135 | yes, :253 | **D6-4 — :135's breakdown sums to 13** |
| 11 | `chain-connectors` | `interfaces/key-chain-loom/…md` | **UNCHECKED** | yes, :88 | yes, :248–252 | ok (ADR 0001:255 derives it again) |
| 12 | `key-pullup-qty` | `cluster/key-switch-network/…md` | **UNCHECKED** | **NO** | **NO** | **D6-1 — owner never states 24** |
| 13 | `spi-series-r` | `interfaces/spi-link/spi-link.md` | `R-SPI-SER` | yes, :58–63 | yes, :77 | ok |
| 14 | `umbilical-pinmap` | `docs/decisions/0004` | **UNCHECKED** | yes, :898–902 | yes, :893–930 | ok, verified by hand |
| 15 | `dac-rail` | `module/power-entry/power-entry.md` | `5.21` | drawing label only, :45 | no — ADR 0004:178, :196 | **D6-16 — weak** |
| 16 | `mod-reference` | `module/mod-channels/mod-channels.md` | `3.3333` | yes, :7–9, :114 | yes, :79–96 | ok |
| 17 | `pitch-compensation` | `module/pitch-stage/pitch-stage.md` | `2.2` | yes, :133 | yes, :178, :211 | ok (owner never names the id) |
| 18 | `panel-width` | `docs/decisions/0004` | `50.50` | yes, :687 | yes, :687 | ok |
| 19 | `panel-height-budget` | `docs/decisions/0004` | `115.5` | yes, :790 | yes, :774–790 | ok |
| 20 | `panel-toggle-hole` | `module/panel/panel.md` | `6.5` | yes, :61–66 **(text added)** | **no — assertion** | **D6-6** |
| 21 | `breath-working-point` | `docs/decisions/0003` | skipped (disputed) | yes, :140 (`0–5 kPa`) | n/a | **D6-14 — 2.8 kPa live in 3 other pages** |
| 22 | `pitch-cents-budget` | `module/pitch-stage/pitch-stage.md` | skipped (disputed) | no total, as the register says | n/a | owner right; **D6-15** on the citation |
| 23 | `loadswitch-timer` | `module/umbilical-load-switch/…md` | **UNCHECKED** | yes, :241 | yes, :235–251 | ok — repoint correct |
| 24 | `loadswitch-gate-cap` | `module/umbilical-load-switch/…md` | `197` | yes, :256–261 | yes, :256–268 | correct, but **D6-9** (id never named) |
| 25 | `loadswitch-fb-divider` | `module/umbilical-load-switch/…md` | `35.7` | yes, :176 | yes, :160–180 | correct, but **D6-9** |
| 26 | `cref-out-node` | `carrier/breath-excitation-reference/…md` | `100` | yes, :27, :100 | yes, :100 + datasheet | ok — **D6-13** on the token |
| 27 | `dig-gnd-topology` | `module/power-entry/power-entry.md` | skipped (disputed) | yes, :172–175 | n/a | **D6-10 — all three candidate locators stale** |
| 28 | `riso-ref-topology` | `carrier/breath-excitation-reference/…md` | `37.4` | yes, :43 | yes, :52–60 | ok — repoint correct |
| 29 | `loop-budget` | `docs/reference/latency-budget.md` | `250` | yes, :178 | yes, :178–199 | ok |
| 30 | `umbilical-current` | `docs/decisions/0005` | `359` | yes, :159 | yes, :96, :159 | ok (owner never names the id) |
| 31 | `diode-split-rationale` | `module/power-entry/power-entry.md` | `392` | yes, :114–117 | yes, :101–117 | ok (owner never names the id) |
| 32 | `ks33-contact-bounce` | `docs/reference/ks33-geometry.md` | **UNCHECKED** | yes, :206 | yes, :211–219 (vendor drawing) | ok, verified by hand |
| 33 | `plate-thickness` | `docs/reference/ks33-geometry.md` | `1.20` | yes, :108 | yes, :51–57 | ok — "this page owns it" and it does |
| 34 | `opa2197-output-impedance` | `carrier/breath-excitation-reference/…md` | `375` | yes, :40 | specified, not derived (register says so) | ok |
| 35 | `matrix-led-current` | `docs/decisions/0014` | skipped (blocked) | yes, :150, :395–397 | n/a | ok |
| 36 | `ferrite-bias-impedance` | `module/power-entry/power-entry.md` | `310` | yes, :152–166 **(text added)** | **no — assertion** | **D6-5** |
| 37 | `ref5050-grade` | `carrier/breath-excitation-reference/…md` | skipped (disputed) | **NO** | **NO** | **D6-3 — ADR 0003:484–491 owns it in fact** |

**Q6 — the four `hardware/bom.csv` owners.** None remain. All 37 `owner:`
paths exist on disk and none is a generated file (`hardware/bom.csv`,
`hardware/unplaced.csv`, `datasheets/MANIFEST.csv`) or a per-circuit
`bom.csv` fragment `[test]`. The four new homes are real pages —
`key-switch-network.md`, `panel.md`, `power-entry.md`,
`breath-excitation-reference.md` — but two of them (D6-1, D6-3) do not state
the figure they were given.

---

## Findings

### D6-1 — `key-pullup-qty`'s new owner never states 24 *(highest)*

`[repo] config/figures.yaml:299–307` names
`hardware/cluster/key-switch-network/key-switch-network.md` as owner of
`key-pullup-qty` = `"24"`, repointed from `hardware/bom.csv` in `0e68f25`.

**That page contains no `24` at all** `[test] grep -n "\b24\b"
hardware/cluster/key-switch-network/key-switch-network.md → no match`. What it
says is the *other* number: `## §2 The key network — 21 of these, spread
across four boards` `[repo] key-switch-network.md:28`. Its `## Interfaces`
row for `3V3` cites `key-pullup-qty` `[repo] :20` — it is a **citing** page,
which is exactly what rule 1 says an owner must not be.

The page that derives it is
`hardware/cluster/key-marker-and-bits/key-marker-and-bits.md`:

> That leaves **3 free bits**: `left_thumb` `B` and `A` (22, 23) and
> `left_hand` `A` (31). **Each gets an `R-KEY-PU` and nothing else** …
> `R-KEY-PU` is now **qty 24**. `[repo] key-marker-and-bits.md:97–107`

That is the register's own derivation string — "21 switch positions + 3 free
bits (22, 23, 31) which also need pulling" — word for word, on the page whose
subject *is* bits 22, 23 and 31. `key-marker-and-bits/circuit.yaml:46` already
declares `fig:key-pullup-qty`.

Nothing caught this because `"24"` is two characters, so `check_owners`
reports the figure `UNCHECKED` and moves on `[test]`. The repoint was made
from the one file in the repo where a statement vanishes silently, to a page
that never made the statement; the value's only other homes are
`key-switch-network/bom.csv:3` (qty column, generated into
`hardware/bom.csv:35`) and a drawing annotation at
`interfaces/key-chain-loom/key-chain-loom.md:76`.

**Recommend** `owner: hardware/cluster/key-marker-and-bits/key-marker-and-bits.md`.
Settled by reading either page; there is nothing uncertain here.

### D6-2 — `inamp-full-scale` has two owners, and the other one says so

The register says `hardware/interfaces/breath-sense-link/breath-sense-link.md`
`[repo] config/figures.yaml:25–33`. That page does derive it, in a table
ending `| **R_G = 42.2 kΩ → G = 2.1848, effective 2.1611** | **jack span
9.94 V** |` `[repo] breath-sense-link.md:160–166`.

But `hardware/module/breath-receive-stage/breath-receive-stage.md:45` reads:

> `| in-amp output | out | … | `inamp-full-scale` | **Owned here.** …`

and the same page states the value outright — "rests at 0 V and reaches
**−9.94 V** at full sensor range" `[repo] :133` — and carries the effective-gain
derivation inside its drawing `[repo] :86–94`.

**Sequence** `[repo] git log`: `68e9e1a` (19:46) wrote "Owned here."; `2a9c720`
(20:15) moved the owner away, its message explaining that "inamp-full-scale's
derivation moved to the interfaces directory". The page it moved away from was
never told. `check_owners` cannot see it: both files contain an unglued
`9.94`.

Which should own it is a real question, not just a wording fix: the in-amp's
own parts live with the circuit page — `U-DIFFRX` (INA828IDR) and
`R-GAIN-INAMP` (42.2k) are rows in
`hardware/module/breath-receive-stage/bom.csv:4–5`, and CLAUDE.md says a row
lives with the circuit *whose page derives its value*. Either the derivation
table belongs on `breath-receive-stage.md` with the parts, or the "Owned
here." claim and the `−9.94 V` at :133 become a citation. Both readings leave
the corpus stating one number in two places today.

### D6-3 — `ref5050-grade`'s new owner says nothing about the grade

Repointed in `0e68f25` from `hardware/bom.csv` to
`hardware/carrier/breath-excitation-reference/breath-excitation-reference.md`
`[repo] config/figures.yaml:716–724`. The whole of what that page says about
the part is one parts-table row: `| `U-REF-BREATH` | REF5050AIDR | 5.000 V for
the ratiometric sensor | `[repo]` |` `[repo] breath-excitation-reference.md:99`.
No grade, no ±0.1 %, no 8 ppm/°C, no mention that anything is disputed
`[test] grep -n -i "grade\|IDR\|ppm\|0\.05" …breath-excitation-reference.md`.

The document that states and derives the dispute is ADR 0003:

> SBOS410O Table 4-2 p.3: **`REF50xxI` = "High" = ±0.05 %, 3 ppm/°C**;
> **`REF50xxAI` = "Standard" = ±0.1 %, 8 ppm/°C** … it is tracked as
> `ref5050-grade` (**disputed**) in `config/figures.yaml`
> `[repo] docs/decisions/0003-breath-sensing-path.md:484–491`

ADR 0003 even names the figure id. `docs/reference/pcb-pipeline.md:106–108`
restates it a third time. Because the figure's status is `disputed`,
`check_owners` skips it entirely `[repo] check-staleness.py:807`, so this
repoint was verified by no mechanism at all.

**Recommend** `owner: docs/decisions/0003-breath-sensing-path.md`.

### D6-4 — the owner of `chain-conductors` states a breakdown that sums to 13

`docs/decisions/0001-mcu-and-board-partitioning.md:135`:

> `| Conductors down the body | **12 per hop** — 6 signals-and-supply, 5 grounds, 2 spare | 32–44 |`

6 + 5 + 2 = **13** `[calc]`. The register's derivation is "4 signals + 5
alternating grounds + 3V3 + 2 spare, on a 2x6 IDC"
`[repo] config/figures.yaml:269–276`, and the same ADR's own pin list —
`GND SCK GND SH/LD GND SER GND QH GND 3V3 spare spare` `[repo] :253` — is 12
conductors: 4 signals + 3V3 = **5** signals-and-supply, 5 grounds, 2 spare
`[calc]`. So `:135` should read "5 signals-and-supply". The tracked total is
right; the owner's decomposition of it is not, and it is the line a reader
checking the figure lands on first. Unreachable by any grep — it is the one
line in the corpus where the parts disagree with the whole.

### D6-5 — the ferrite table: numbers correct, derivation absent, old statement still live

**The datasheet numbers check out.** Extracting the impedance-vs-frequency
curve family from the content stream of
`datasheets/discrete-and-power/MI1206K601R-10-ferrite-bead.pdf` (single page,
vector, no text on the traces; legend colours mapped to the `0amp/250ma/500ma/
1000ma/1500ma` keys at x≈142, then each polyline sampled at the 100 MHz
abscissa) gives, at 100 MHz `[datasheet, geometry extraction]`:

| trace | register says | extracted (min–max across the stroked segments) |
|---|---|---|
| 0 A | ~614 Ω | 610–620 Ω |
| 250 mA | ~431 Ω | 426–439 Ω |
| 500 mA | ~157 Ω | 155–161 Ω |
| 1000 mA | ~72 Ω | 71–75 Ω |
| 1500 mA | ~51 Ω | 50–54 Ω |

All five match. The register's further claim that "DC bias shifts the
impedance peak **UP IN FREQUENCY**" is also confirmed: the 0 A trace peaks near
100 MHz and the 1000/1500 mA traces peak near 300–400 MHz
`[datasheet, same extraction]`.

**What the added text is.** `hardware/module/power-entry/power-entry.md:152–166`
states the two bands and cites the banked PDF. It is **assertion, not
derivation**: it gives no bias current for `FB1/FB3/FB4` ("the low-current
rails"), no curve readings and no interpolation, so a reader cannot check
`~580–614 Ω` from the page. The real derivation is in the `FB-IN` BOM row:
"FB4 (+5V, mA), FB3 (-12V, 10-20mA) and FB1 (+12V analog, ~45mA) all sit on
the flat part of the curve and get 580-614 ohm. FB2 carries the umbilical at
the 359 mA of figures.yaml `umbilical-current` and gets ~280-310 ohm"
`[repo] hardware/module/power-entry/bom.csv:8`, generated into
`hardware/bom.csv:61`.

So the repoint moved the `owner:` off `hardware/bom.csv` but **left the full
statement there** — the figure is now written out in three places
(register derivation, `power-entry.md`, the BOM row) plus a fourth,
`docs/reference/pcb-pipeline.md:219–221`, which restates "`FB2` … reads
~280–310 Ω, half its nameplate" without citing `ferrite-bias-impedance` at
all. Contrast the `D-REVPOL` row, which handles the same situation correctly:
"are the tracked figure diode-split-rationale, owned by
hardware/module/power-entry/power-entry.md, and are deliberately NOT restated
here" `[repo] hardware/module/power-entry/bom.csv:4`.

**Two soft spots in the numbers themselves**, neither wrong:

- `~580` is **not read off the drawing.** The lowest bias trace is 0 A and the
  next is 250 mA; 580 Ω is a linear interpolation to ~45 mA
  (614 − 45/250 × 183 = 581 `[calc]`). The curve's shape makes that
  conservative — it loses 183 Ω over the first 250 mA and 274 Ω over the
  second `[datasheet]` — so the true value is if anything closer to 614. Worth
  saying on the page, because "read off the drawing's curve family" currently
  covers a number that was not.
- The register's trailing clause "the module +12V total of 392 mA gives
  ~245-275" `[repo] config/figures.yaml:712` describes a current **no bead
  carries**: the +12 V splits at the IDC into `D1/FB1` (module analog, ~45 mA)
  and `D2/FB2` (umbilical, 359 mA) `[repo] power-entry.md:42–49`. 392 mA is
  the sum of the two branches, and `umbilical-current`'s own
  `false_positive_note` says so `[repo] config/figures.yaml:606`. It reads
  like a third band and is not one.

### D6-6 — the toggle-hole paragraph: right numbers, wrong shape, and it broke a verbatim claim

**The numbers are correct** `[datasheet]
datasheets/connectors/NKK-SERIES-M-TOGGLE.pdf p.6`. The `D4` bushing option is
"6mm/.350" (8.9mm) Threaded with D Flat", dimensioned `M6 P0.75`; the panel
cutout drawn under "For D1, D4, D3 or D8 Bushing with D Flat" is
**(6.5) Dia .256** with a flat at **(5.8) .228"** — 5.79 mm `[calc]`. The
register's further claims check out on the same page: the keyway cutout is
6.5 mm with a 5.6 mm flat, and the locking-ring cutout is 6.5 mm with a 2.2 mm
dia hole. `SW-POWER` is `NKK M2011SD4G01` `[repo]
hardware/module/umbilical-load-switch/bom.csv:2`, whose `D4` is that bushing.

**Three problems with the text.**

1. **It was inserted into a block the page declares moved verbatim.**
   `panel.md:41–45` says the section below "moved verbatim from
   `hardware/module/breath-output-stage/breath-output-stage.md`, 2026-09-21 …
   **Only the blockquote prefixes were stripped.**" The paragraph at :61–66 was
   added by `0e68f25` and is not in the moved text
   `[repo] git show 81fad55:hardware/module/panel/panel.md`. The provenance
   claim is now false, and it is the kind of claim `check-conservation.py`
   exists to protect.
2. **Its stated reason is a non-sequitur.** "The sourced bushing is 6 mm
   metric, so a 6.0 mm round hole is *not* the right cut" welds two
   independent facts together: 6.5 vs 6.0 is **thread clearance** for an
   M6×0.75 bushing, and round vs D-flat is **anti-rotation**. Neither follows
   from the other, and the paragraph's own opening ("needs a shaped hole, not a
   round one") is about the second while its reason is about the first. It also
   drops the register's manufacturing consequence — "THERE IS NO PLAIN ROUND
   OPTION IN THE METRIC RANGE, so this hole cannot be drilled - it is milled or
   filed" `[repo] config/figures.yaml:447` — which is the only part of this
   figure that changes what someone does.
3. **It is assertion written to satisfy the checker**, in the plain sense: no
   datasheet cited, no bushing dimension, no derivation — just the value and
   the token `6.5` that `check_owners` looks for `[test]`.

**A fourth, smaller thing.** The added sentence contains "superseded", which is
in the checker's `REFUTATION` vocabulary `[repo] check-staleness.py:93–97`, and
the exemption window is 300 characters `[repo] :73` — wider than the whole
paragraph. Any future `forbidden` pattern that lands in this paragraph is
pre-exempted by a word that was added for prose reasons. That is the same
shape as the `FB-IN`/`WIRE-LOOM` leaks `0e68f25` was written to close.

### D6-7 — `panel.md` says it does not restate the panel figures, and then restates them

> The tracked figures for that are `panel-width` and `panel-height-budget` …
> whose owner is `docs/decisions/0004-cv-interface-module.md` — **this page
> cites them and does not restate them.** `[repo] panel.md:4–7`

The same page then writes "**10HP is 50.50 mm**" `[repo] :54`, "**110 mm of
content against 115.5 mm of clear panel**" `[repo] :57–58` and "Three pots
across 50.50 mm" `[repo] :68`. Three restatements of two figures it does not
own, under a sentence saying there are none. Pre-dates the fix batch (the
block arrived at `81fad55`) but is live, and `0e68f25` edited this exact
section without noticing.

### D6-8 — old owners still state what moved away from them

- **`power-entry.md`** lost `loadswitch-timer`, `loadswitch-gate-cap` and
  `loadswitch-fb-divider` to `umbilical-load-switch.md`, and its drawing still
  carries `[C-TIMER 10µF]`, `[C-GATE 82nF]`, `[R-FB-HI 35.7k 1%]`,
  `[R-FB-LO 5.11k 1%]` `[repo] power-entry.md:63–69`. The page does say why —
  "The drawing below is unchanged and still shows all three, because it is one
  drawing" `[repo] :10–13` — so this is a judgement call, not an oversight.
  But note the spellings: `35.7k`, `5.11k`, `82nF`, `10µF`. The owner page
  spells the same values `35.7 kΩ`, `5.11 kΩ`, `82 nF`, `10 µF`. A `forbidden`
  pattern written from the owner page — which is where anyone changing the
  value will be — matches none of the four. That is CLAUDE.md §2's first trap,
  live, in a file the fix batch touched.
- **`carrier.md`** lost `cref-out-node` and `riso-ref-topology` to
  `breath-excitation-reference.md`, and its §2 drawing still states both: the
  two `C-REF-OUT` 10 µF caps on `VIN`/`VOUT` and `[37.4 Ω]` in the buffer
  output `[repo] hardware/carrier/carrier.md:93–101`. Unlike §1, which carries
  a "*moved verbatim to …*" note `[repo] :82–85`, §2 has no such note and
  cites neither figure id `[test] grep -n "riso-ref-topology\|cref-out-node"
  hardware/carrier/carrier.md → no match`.

### D6-9 — the repoints did not reach the graph, and 13 owners never name their figure

`hardware/module/umbilical-load-switch/circuit.yaml` declares
`fig:loadswitch-timer` and nothing else `[repo] :46–47`, although the circuit
now owns three figures. `loadswitch-gate-cap` and `loadswitch-fb-divider` are
declared by **no** `circuit.yaml` in the tree, and neither is
`ref5050-grade` — all three repointed by `0e68f25` `[test]`. The `fig:` edges
are seeded from co-mention `[repo] circuit.yaml header`, so this is evidence of
the underlying fact rather than a separate defect: **the owner page never
names the figure it owns.**

Thirteen of the 37 owner documents contain no occurrence of their figure's id
`[test]`: `breath-sensor-slope`, `key-scan-current`, `marker-bits`,
`free-bits`, `chain-conductors`, `umbilical-pinmap`, `pitch-compensation`,
`breath-working-point`, `loadswitch-gate-cap`, `loadswitch-fb-divider`,
`umbilical-current`, `diode-split-rationale`, `ks33-contact-bounce`,
`ref5050-grade`. Most of those pages state the value perfectly well; the cost
is that a reader editing the number has no signal on the page that it is
tracked, which is the precondition for every staleness defect in this repo's
history. The three repointed ones are the ones worth fixing first.

### D6-10 — `dig-gnd-topology`'s candidate locators are all three stale

`[repo] config/figures.yaml:528–539` cites:

| cited | actual |
|---|---|
| `hardware/module/power-entry/power-entry.md:495-498` | the file is **192 lines**; the text is at :172–175 |
| `docs/decisions/0004-cv-interface-module.md:627` | the claim ("`DIG_GND` likewise — its own path to the star") is at :646 |
| `hardware/module/digital-and-supervision/digital-and-supervision.md:53` | "analog star, single tie (ADR 0004)" is at :65 |

Three of three, and the first by ~300 lines — pre-split line numbers that the
2026-09-21 restructure invalidated. The owner field itself is right;
`power-entry.md:172–175` does state this page's side of the dispute.

### D6-11 — `marker-bits` / `free-bits` are owned by a data file that does not decide them

`config/key-layout.yaml:147` (`spare_bits_marker: 8`) and `:149`
(`spare_bits_free: 3`) state both values, and their comments point away from
themselves: "DECIDED 2026-09-21, ADR 0001 - was 6". ADR 0001 is where the
derivation is: "**Use 8 of the 14 spare chain bits as a fixed marker pattern.
DECIDED**" `[repo] docs/decisions/0001:323` and "the allocation went from a
superseded 6 marker to 8 marker, 5 free → 3 free" `[repo] :341`, restated again
at `:374`. Under the rule as written ("the page whose derivation sets the
value") the owner is ADR 0001. Arguable the other way — `key-layout.yaml` is
the machine-readable source firmware reads — so I file it as a judgement to
make explicitly rather than as an error. Whichever way it goes, the value is
currently written out in four places.

### D6-12 — the checker reports **eight** figures `UNCHECKED`, not seven

`[test]`: `marker-bits`, `free-bits`, `chain-conductors`, `chain-connectors`,
`key-pullup-qty`, `umbilical-pinmap`, `loadswitch-timer`,
`ks33-contact-bounce`. The eighth is `umbilical-pinmap`, whose value is prose
with no 3-digit number and no hyphenated identifier of 5+ characters, so both
token regexes come back empty `[repo] check-staleness.py:860–865`. All eight
were verified by hand for this slice; seven pass (rows 8–11, 14, 23, 32 above)
and one fails (**D6-1**).

### D6-13 — two more passes that are worth nothing

- `cref-out-node`'s only token is `100` `[test]` — the exact token
  `check_owners`'s own docstring names as the reason an earlier version was
  wrong `[repo] :826–830`. `100` appears in 38 corpus files. Verified by hand:
  the owner does state it, at `:27` and `:100`.
- `pitch-compensation` tokenises to `2.2` `[test]`, which appears in 14 files
  including `R-KEY-PU 2.2 kΩ`. Verified by hand: the owner states it correctly
  at `:133`, including the topology half of the value.

### D6-14 — `breath-working-point` is disputed and three pages state it as fact

The owner states the candidate it believes — "playing sits around 0–5 kPa"
`[repo] docs/decisions/0003:140`. Meanwhile `2.8 kPa` is stated flatly in
`hardware/module/breath-output-stage/breath-output-stage.md:41` and `:44`,
`hardware/carrier/breath-adc/breath-adc.md:40`, and
`hardware/module/breath-receive-stage/breath-receive-stage.md:200`. The
`breath-adc` line sources it to a page rather than to the register —
"`[2.8 kPa from breath-receive-stage.md]`" `[repo] breath-adc.md:41` — which is
a citation chain the register cannot see and which the register's own
`candidates` list flags as mis-attributed.

### D6-15 — `power-entry.md` cites a disputed figure as a settled total

> "`pitch-stage.md` puts the entire pitch error budget at 0.42 cents."
> `[repo] hardware/module/power-entry/power-entry.md:134`

`pitch-cents-budget` is `disputed` precisely because that is wrong: candidate
one is "0.42 cents (**this is a ROW of one table, not a total** - and it is
what power-entry.md scaled the ground-path finding against)"
`[repo] config/figures.yaml:461–468`. The register names this exact sentence as
the defect, and the sentence is still there — and it is load-bearing, because
the ground-path finding above it is scaled against it ("one to two orders of
magnitude below" `[repo] :136`). Verified against the owner: `pitch-stage.md`
has 0.42 cents as one row of the tempco table `[repo] :286` and states no
total.

### D6-16 — `dac-rail`'s owner draws it but does not derive it

`power-entry.md` states `DAC AVDD 5.21V` as a label inside the ASCII drawing
`[repo] :45` and the divider as `150R/475R 0.1%` `[repo] :46`. The arithmetic
— `1.25 × (1 + 475/150) = 5.208 V` — appears only in the register
`[repo] config/figures.yaml:349` and in ADR 0004:178, :196. Defensible (it is
the circuit whose divider sets the rail, and the page's `## Interfaces` row
cites the figure and its `floor`), but the page carries no sentence a reader
can check, and the token `5.21` passes only because `anchored_in` deliberately
allows a trailing unit letter `[repo] check-staleness.py:643–652`.

---

## What would settle the uncertain ones

- **D6-2** (`inamp-full-scale`) is the only finding where I am not certain
  which way the fix goes. It needs someone to decide whether the gain
  derivation belongs with the in-amp's BOM rows on `breath-receive-stage.md`
  or stays on `breath-sense-link.md`; either answer makes one of the two
  current statements a citation. Filed as a contradiction, not as a
  misassignment.
- **D6-11** (`marker-bits`, `free-bits`) is a judgement about whether a
  `config/*.yaml` data file can own a figure an ADR decided. Worth deciding
  once and writing down, because `key-layout.yaml` is the only non-prose owner
  in the register.
- Everything else above is checkable by opening the two files named in it.
