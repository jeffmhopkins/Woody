# G7 — the four fix shapes

**Slice:** G7, cold. **Wave:** 2026-09-22-goal-verification.
## Provenance of every measurement in this report — READ FIRST

**The working tree moved under this slice.** Another slice was injecting
defects into corpus files *and* into `tools/check-staleness.py` in the same
checkout, uncommitted, so `git log` shows none of it. I saw it directly:
`README.md` gained a line `See [the missing page](g10-does-not-exist.md).` at
line 148 mid-slice, and the `PreToolUse` hook reported `FAIL … 1 stale` on two
of my read-only Bash calls while my own direct runs of the checker returned
`PASS` on either side of them.

**So every count, tool run and quoted line in this report was re-taken from a
pinned clone after the coordinator's warning:**

```
git clone /home/user/Woody /tmp/claude-0/g7pin
cd /tmp/claude-0/g7pin && git checkout a4b80b1
git status --short          # empty — TREE CLEAN
```

All `[test]` and `[calc]` results below are from that clone, using **its own**
`tools/` at `a4b80b1`, with the tree verified clean immediately before each run.
Every line I quote was re-read from it and reproduces byte-for-byte; the check
is at the bottom of this section. **The first-pass numbers taken from the live
tree were identical in every case except one**, noted below.

| Measured at `a4b80b1`, clean tree | Value |
|---|---|
| `find hardware -name circuit.yaml \| wc -l` | **23** |
| `grep -c "^  - id:" config/figures.yaml` | **37** |
| `ls -d docs/review/*/ \| wc -l` | **11** |
| `git ls-files \| wc -l` | **440** |
| `python3 tools/merge-bom.py --check` | `checked 140 rows from 26 fragments \| 0 problems` |
| `python3 tools/check-staleness.py` | `PASS … corpus 123 files, 23 circuits, 37 figures / 217 patterns` |
| `hardware/bom.csv` | **140 rows, 391 units, 11 columns** |
| `hardware/unplaced.csv` | **32 rows, 67 units** |
| non-`unplaced` rows | **108 rows, 324 units** |
| fragment files | **25** (22 circuit-level + 3 board-level); 26 counting `unplaced.csv` |
| `R-KEY-PU` / `R-KEY-SER` / `C-KEY` / `C-DECOUPLE-165` | **24 / 21 / 21 / 4** |
| `J-CHAIN` / `U-OPA-PITCH` / `U-RESP` / `SW-THUMB` | **8 / 6 / 1 / 4** |
| path-map assertion, tracked with no row | **34** |

**The one number that differed** is the review-wave count: **11** at `a4b80b1`,
**12** in the live tree (this wave's own directory), and the path-map orphan
count moved with it, **34** pinned against **35** live. G7-21 and G7-25 are
written against the pinned figures. Neither finding turns on the difference —
the corpus says "nine" and "405".

**Line-quote verification.** All 26 lines quoted as `[repo] file:line` in the
findings below were re-read with `sed -n "<n>p"` from the pinned clone and match
what this report attributes to them — including every line in files the
injecting slice is known to have touched (`README.md`,
`hardware/module/pitch-stage/circuit.yaml` is cited nowhere here).

**Revision:** `a4b80b1` is the last commit touching anything under review;
`git diff --stat a4b80b1 HEAD` at the time of writing shows only this wave's own
`docs/review/2026-09-22-goal-verification/` files, which are outside the §6
corpus.

**`tools/` freeze:** the wave README does not pin `tools/`. I used the pinned
clone's copy, which is `tools/` **as of `a4b80b1`**, and modified nothing. If a
later slice's `[test]` baselines disagree with mine, the pinned-tools question is
where to look first.

**Cold:** I opened nothing under `docs/review/`. Two review paths appear below
only as strings I read *inside corpus files* (`figures.yaml` cites
`docs/review/2026-09-21-preflight/A4-carrier.md`; `pcb-pipeline.md` cites
`R10-keyscan-and-adc.md`) — I did not open either.

---

---

## Summary

24 findings. The ones that matter most, in order:

| | Shape | Node | One line |
|---|---|---|---|
| **G7-1** | 4 | body construction, ~20 files | ADR 0009 retired the bonded body; ~20 live arguments still rest on it |
| **G7-2** | 1 | `R-KEY-PU` / `key-pullup-qty` | 21 → 24 pull-ups; **"63 passives" in four files** never followed. It is 66 |
| **G7-3** | 4 | ADR 0003 latency table | A `< 1.5 ms` total sits 12 lines above the same page's corrected `~3.1 ms` |
| **G7-4** | 1 | `plate-thickness` | ADR 0009's mass table and stack list still build a 2 mm plate |
| **G7-5** | 4 | ADR 0004 §watchdog scope | "`CLR` fires" on MCU death — the watchdog that fired it is deleted |
| **G7-8** | 1 | `free-bits` | 5 → 3 free bits; "15 passives" is the 5-bit number, in the same sentence as "the 3 free bits" |
| **G7-13** | 2 | `diode-split-rationale` | The derivation chain is ~2000× off the value it states |

Shape counts: Shape 1 — 8; Shape 2 — 6; Shape 3 — 7; Shape 4 — 6 (some findings
carry two shapes; they are filed under the dominant one).

---

## Shape 4 — a conclusion its own corrected number refutes

### G7-1 — The bonded body is retired, and ~20 live arguments still stand on it

**Node:** whole-corpus premise. **Shape 4, and the largest instance I found.**

ADR 0009 reversed this explicitly:

> `[repo] docs/decisions/0009-enclosure-construction.md:493-494` — *"a body that
> is bonded shut is a body that is never opened again." **The body is not bonded
> shut any more**, so the items below are no longer impossible later*

and `:555` — *"**This supersedes the page's earlier assumption that the stack is
bonded shut.**"* `docs/reference/pcb-pipeline.md:193-194` records the same
reversal downstream: *"ADR 0009 retired the bonded body — it comes apart on six
fasteners."*

The fix landed in exactly those two places. Every one of the following is a
**live, present-tense** statement in the §6 corpus that the body cannot be
reopened `[repo]`:

| File:line | Stale text |
|---|---|
| `firmware/README.md:94` | **"The body is bonded.** Everything here exists because a failed flash cannot be…" |
| `config/key-layout.yaml:150` | "A free bit has no plate cutout and **the body bonds shut**, so it could never have become a switch anyway" |
| `hardware/cluster/key-marker-and-bits/key-marker-and-bits.md:133` | same argument, same wording |
| `docs/decisions/0001-mcu-and-board-partitioning.md:160` | "in a strap-worn instrument that **is bonded shut**" |
| `0001:191` | "inside **a body that cannot be reopened**" |
| `0001:244` | "they **cannot be retrofitted into a bonded body**" |
| `0001:337` | "**the body bonds shut**, so it can [never become a switch]" |
| `0003:248` | "most likely part to fail, in **a body that cannot be reopened**" |
| `0005:239` | "**bonded body that cannot be reopened** to change the decision" |
| `0007:199` | "In **a body that cannot be opened**, two pins is a cheap price" |
| `0013:294` | "Its own USB is inside **a bonded body**" |
| `0014:53`, `0014:83`, `0014:497` | three more |
| `ROADMAP.md:207` | "get **sealed inside a bonded body** at M6" |
| `hardware/interfaces/breath-sense-link/breath-sense-link.md:14, :91, :181` | three |
| `hardware/module/breath-receive-stage/breath-receive-stage.md:28` | "inside **a bonded body**, and unretrofittable" |
| `hardware/module/breath-receive-stage/sim/README.md:22` | "in **the bonded body**" |
| `hardware/cluster/cluster-boards.md:94` | "inside something that **bonds shut**" |
| `hardware/carrier/carrier.md:286, :339` | two |
| `hardware/interfaces/key-chain-loom/key-chain-loom.md:146` | "through **a bonded body**" |

**Most of the conclusions survive; the stated premise does not**, and that is
precisely the failure this repo already documented for the watchdog:
`firmware/README.md:70-73` warns that *"a reader who checks the old premise,
finds the watchdog gone, and relaxes the rule reintroduces +11.45 V on four
jacks."* The identical hazard applies here. `ROADMAP.md:97-103` shows the right
form — it keeps the ordering rule and restates the reason ("*recoverable* here
means a full strip-down") instead of keeping the retired premise.

**Two are not merely cosmetic and change the argument:**

- `config/key-layout.yaml:150` and `key-marker-and-bits.md:133` justify
  `free-bits` = 3 partly on *"the body bonds shut, so it could never have become
  a switch anyway."* With a serviceable body the load-bearing reason is the
  **plate cutout** (which `key-layout.yaml:145` already states), not the bonding.
- `ROADMAP.md:207` contradicts `ROADMAP.md:78` **in the same file**: M8's row
  says *"The body is no longer bonded shut — it closes on six fasteners onto an
  RTV gasket, ADR 0009"*, 129 lines above line 207's "sealed inside a bonded
  body at M6."

**Should be:** restate each as the consequence that actually survives —
"unretrofittable without a full strip-down", "hand-terminated once" — not as
"bonded".

### G7-2 — `R-KEY-PU` went 21 → 24 and four files still count 63 passives

**Node:** `R-KEY-PU` / figure `key-pullup-qty`. **Shape 4 and Shape 1.**

`key-pullup-qty` = **24** `[repo] config/figures.yaml:301`, derived as *"21
switch positions + 3 free bits (22, 23, 31) which also need pulling."* The BOM
agrees: `R-KEY-PU` qty 24, `R-KEY-SER` qty 21, `C-KEY` qty 21
`[repo] hardware/cluster/key-switch-network/bom.csv`.

`[calc]` network passives across the four cluster boards = **24 + 21 + 21 = 66**.
The old number, before the three free-bit pull-ups were added, was
`21 × 3 = 63`. **Four corpus files still carry 63:**

- `hardware/cluster/cluster-boards.md:211` — "18 fitted switches in 21 networked
  positions, **63 network passives**, 7 chain connectors"
- `docs/decisions/0001-mcu-and-board-partitioning.md:138` — "+41 %: 4 ICs and
  **63 passives**"
- `0001:162` — "the tail version added 4 ICs and **63 passives**"
- `hardware/bom.csv:23` (`R-LED-SER` notes, and its fragment
  `hardware/carrier/led-strip-drive/bom.csv`) — "TWO PARTS ON THE AGGRESSOR,
  against **63** on the victims"

`hardware/carrier/carrier.md:283` is wrong a second way: "4 ICs and **63
passives** moved to `PCB-CLUSTER`" — that row enumerates `R-KEY-PU`,
`R-KEY-SER`, `C-KEY` **and** `C-DECOUPLE-165` (qty 4), so the moved passive count
there is `[calc]` 24+21+21+4 = **70**.

**Nothing guards this.** `figures.yaml:299-306` records dropping the
`"Twenty-one sets"` pattern because it fired on a true sentence, leaving only
`"21 pull-ups"` — which none of these five lines spells. This is the register's
own documented trade (a pattern whose cheapest fix makes a correct sentence
wrong) landing exactly where it was predicted to.

**Should be:** 66 network passives (70 including `C-DECOUPLE-165` at
`carrier.md:283`), or cite `key-pullup-qty` and stop restating a sum.

### G7-3 — ADR 0003's latency table totals `< 1.5 ms`; its own next paragraph says 3.1 ms

**Node:** `docs/decisions/0003-breath-sensing-path.md:19-35`.

The table at `0003:19-27` `[repo]`:

| Stage | 0003 says | `latency-budget.md` says |
|---|---|---|
| SAR ADC conversion | ~50–200 µs | **~24 µs** `[repo] latency-budget.md:61` |
| SPI to DAC over the umbilical | ~50 µs | **~96 µs** `latency-budget.md:63` |
| Op-amp and reconstruction filter | ~160 µs | **~82 µs** `latency-budget.md:65` |
| Anti-alias filter | *absent* | 282 µs |
| Sampling period | *absent* | 0–250 µs |
| Tube propagation | *absent* | ~1.17 ms |
| **Total** | **< 1.5 ms** | **~2.9–3.1 ms + restrictor** |

Then eight lines below the table, the **same page** says
`[repo] 0003:35-36`: *"The digitised path comes to **~3.1 ms** against a 5 ms
target — about 1.6×, not the 10× this sentence used to claim."*

Two conclusions that only followed from the old table are still live above it:

- `0003:29-30` — *"**The transducer dominates.** The entire digital path costs
  less than the sensor's own settling time."* `[calc]` at the real figures the
  transducer is ~1 ms of ~2.9–3.1 ms — it is one term of three comparable ones.
- `0003:31-32` — *"Going fully analog would save roughly **400 µs** against a
  1 ms floor."* That is the old table's digital remainder.

This is the exact shape the brief names: the number was corrected in one
paragraph and the argument above it kept the retired one. **`loop-budget`'s
`forbidden` list already holds `"SAR ADC conversion ~50"`** and the checker
reports PASS — pinned clone at `a4b80b1`, tree clean, its own `tools/`
`[test] python3 tools/check-staleness.py` → `PASS no live stale values` —
because `0003:22` spells
it in a table cell with pipes and an en dash — `| SAR ADC conversion | ~50–200 µs |`
— the same table-cell-with-pipes escape `sensor-full-scale`'s `escape_note`
records as the fourth recorded instance.

**Should be:** delete the table and cite `loop-budget` and
`latency-budget.md`, or rebuild it with the six corrected terms.

### G7-4 — `plate-thickness` settled at 1.20 mm; ADR 0009 still builds a 2 mm plate

**Node:** `PLATE-TOP` / `PLATE-THUMB`, figure `plate-thickness`.

`plate-thickness` = **1.20 mm**, owner `ks33-geometry.md`, and *"BOTH candidates
the corpus was choosing between are OUTSIDE the vendor window"*
`[repo] config/figures.yaml:688-695`. The BOM followed: `PLATE-TOP` and
`PLATE-THUMB` are both `1.20mm aluminium`, `selected`
`[repo] hardware/bom.csv`, and `PLATE-THUMB`'s note says *"follows PLATE-TOP to
1.20mm."*

ADR 0009 followed in one line and not in two others `[repo]`:

- `0009:64` — `aluminium top plate       1.20 mm <- SETTLED …` ✔ fixed
- **`0009:68`** — `thumb switch plate        ~2 mm` ✘ stale. `plate-thickness`'s
  quantity field names `PLATE-THUMB` explicitly.
- **`0009:181`** — `| Aluminium top plate, 2 mm | 157 |` ✘ stale, in the mass
  table, 117 lines below the corrected stack list.

**Shape 4 on top of it:** `0009:183-186` concludes *"**Total ~825 (1.8 lb)** …
Squarely in EWI territory."* `[calc]` at aluminium 2.70 g/cm³, 157 g at 2.00 mm
implies 290.7 cm² of plate; the same plate at 1.20 mm is **94 g**, so the total
is **~762 g (1.68 lb)**. The conclusion survives; the number does not.

**And this is a textbook escape.** `plate-thickness.forbidden` contains
`"ADR 0009 specifies a ~2 mm aluminium top plate"` — written in **ADR 0002's**
spelling of a sentence *about* ADR 0009. ADR 0009's own two spellings are
`Aluminium top plate, 2 mm` and `thumb switch plate        ~2 mm`. Both escape by
punctuation, which is `sensor-full-scale`'s `escape_note` rule ("a forbidden list
written from the document in front of you cannot catch the document in front of
you") applied to a different figure and still costing.

**Should be:** `0009:68` → 1.20 mm; `0009:181` → "Aluminium top plate,
`plate-thickness`" at ~94 g, total ~762 g.

### G7-5 — ADR 0004 still has `CLR` firing on an MCU death

**Node:** `docs/decisions/0004-cv-interface-module.md:514-535`, section
"The watchdog's scope is the DAC channels".

`0004:493-501` records the withdrawal: *"**Withdrawn 2026-09-21.** The mechanism
below was built and then deleted."* The struck-through proposal follows. Then a
`####` section — **not struck through, not inside the blockquote** — reasons in
the present tense:

- `0004:517-518` — "`CLR` reaches pitch and the four mod channels … so **the
  watchdog has no authority** over the one jack…"
- **`0004:532`** — *"the MCU dies, SPI stops, **`CLR` fires**, and breath keeps
  working."*

There is nothing left to fire `CLR` on SPI loss. `hardware/module/mod-channels/mod-channels.md:160-163`
states the corrected list: *"**What asserts `CLR`, now that the watchdog is
gone.** Two things … the DAC's own **power-on reset** … and the **`LK-CLR`
solder pad**"*; `firmware/README.md:65-74` says the same. And
`ROADMAP.md:51` (E10) states the opposite outcome to `0004:532`: *"**pitch and
the four mod jacks hold their last value indefinitely** — that is the accepted
cost of deleting the frame watchdog."*

So the corpus holds two answers to "what happens at the jacks when the MCU
dies", and ADR 0004 — the ADR the other pages cite — has the retired one.
`0004:498-501` says *"The paragraphs below are kept because the problem they
describe is still real"*, which is true of the **problem** and false of the
**mechanism** at `:532`.

**Should be:** `0004:532` — the MCU dies, SPI stops, **nothing fires `CLR`**,
the DAC channels hold their last value, and breath keeps working. The
conclusion ("breath still working is designed behaviour") survives; the route to
it does not.

### G7-6 — ADR 0014 argues the 1 A regulator case on a figure it elsewhere retires

**Node:** figure `matrix-led-current` (status `blocked`), ADR 0014.

`figures.yaml:718` states it plainly: *"ADR 0014 uses it to argue the matrix
alone nearly exhausts the 1 A R-78E5.0 … **ADR 0014's brightness cap is RIGHT
and its JUSTIFICATION IS WRONG**."* ADR 0014 itself carries the refutation at
`0014:379-422` — *"⚠ THE PART IS NOT A WS2812C, AND 960 mA IS OPTIMISTIC BY AT
[LEAST 2.4×]"*, *"the binding constraint is not the one it names"*.

It also still carries the retired argument, twice, in **unmarked live prose**,
one of them 198 lines *before* the ⚠ block a reader would need `[repo]`:

- `0014:181-183` — "**The instrument's own regulator, which is a 1 A part.** …
  at full field it asks for **960 mA** on its own."
- `0014:448` — table row `| **Full field white** | **+960** | **+470** |`
- `0014:456-458` — "so a full-field matrix would ask for about **1.36 A** from a
  1 A part."

A reader meets the wrong argument first and the correction only if they reach
§`0014:379`. **Should be:** cite `matrix-led-current` (blocked) and state the
B5819WS/LDO constraint the register names as the one that actually binds.

---

## Shape 1 — a fix that did not reach the pages citing it

### G7-7 — The KS-33 bounce figure is published; ROADMAP says twice that it is not

**Node:** figure `ks33-contact-bounce` (`5 ms max at 16 in/sec actuation`).

Fixed in `docs/decisions/0002-key-switches-and-mounting.md:217-224`, in
`docs/reference/latency-budget.md:148`, and in `ks33-geometry.md:206-219`.
**Not fixed in ROADMAP.md** `[repo]`:

- `ROADMAP.md:71` (M1) — "**bounce and the actuation/reset hysteresis gap
  scoped** … — **neither is published**"
- `ROADMAP.md:84` — "M1 narrows to … **the two timing figures nobody publishes**"

ROADMAP contradicts itself: `ROADMAP.md:118-125` carries the correction in full
— *"**Partly refuted 2026-09-21** … Gateron *does* publish a bounce figure —
**5 ms max at 16 in/sec** … The **hysteresis gap is still not stated
numerically**"*. Lines 71 and 84 sit 34 and 47 lines above it.

`ks33-contact-bounce.forbidden` holds five patterns for this
(`"bounce is not published"`, `"no published bounce figure"`, …) — none of them
is `"neither is published"` or `"nobody publishes"`, which are ROADMAP's two
spellings. Same escape class as G7-4.

**Should be:** one timing figure, not two — the hysteresis gap. Cite
`ks33-contact-bounce` for the other.

### G7-8 — `free-bits` went 5 → 3; the passive count beside it is still the 5-bit number

**Node:** figure `free-bits` (= **3** `[repo] figures.yaml:264`).

`hardware/interfaces/key-chain-loom/key-chain-loom.md:192-194` `[repo]`:

> "Giving **the 3 free bits** the full network too is now **15 passives** spread
> across four boards that already carry 21 sets"

`[calc]` The full network is three passives per position — `R-KEY-PU` +
`R-KEY-SER` + `C-KEY` `[repo] hardware/cluster/key-switch-network/key-switch-network.md:28-40`.
3 bits × 3 = **9** (and only **6** are actually new, since `R-KEY-PU` qty 24
already covers the free bits `[repo] hardware/cluster/key-switch-network/bom.csv`).
**15 = 5 × 3** — the count when `free-bits` was 5, a value the register lists as
forbidden (`"five genuinely free"`, `"5 free bits"`).

**The corrected and uncorrected numbers are in the same sentence**, seven words
apart. That is Shape 1 and Shape 2 at once, and no grep can see it because both
tokens are legitimate in isolation.

**Should be:** 9 passives (6 new).

### G7-9 — `breath-adc.md` says a fix is "still unapplied" after it landed

**Node:** `C-AA-ADC`, `hardware/carrier/breath-adc/breath-adc.md:67-71`.

> "`latency-budget.md` and ADR 0003 book "SAR ADC conversion ~50–200 µs" and
> **no RC term at all** `[repo]`. … Found by `R10-keyscan-and-adc.md` §B-2 and
> **still unapplied**."

All three claims are now false of `latency-budget.md` `[repo]`:
`latency-budget.md:61` books **~24 µs** and says so explicitly ("This row said
50–200 µs"); `latency-budget.md:59` books the **anti-alias filter, 564 Hz,
282 µs** as its own row; and `latency-budget.md:63` books the RC term the
sentence says is absent.

They remain true of **ADR 0003** (see G7-3), so the sentence should narrow
rather than be deleted. As written, a reader checks the cited page, finds the
fix, and discards the *other* half of a live finding.

**Should be:** "ADR 0003 still books 50–200 µs and no RC term;
`latency-budget.md` was corrected 2026-09-21."

### G7-10 — `ks33-geometry.md` still points at a cluster-board fix that has landed

**Node:** `PCB-CLUSTER` layout rule, `docs/reference/ks33-geometry.md:137-142`.

> "**`hardware/cluster/cluster-boards.md` §"Three layout rules that are not
> obvious" still carries the reversed conclusion** … **That page has to follow
> this one**"

It does not. `cluster-boards.md:160-173` carries the corrected height rule
(*"chip passives and SOT-23 may sit on the plate-facing side; nothing with a body
over about 1.4 mm may"*) and a blockquote at `:169-173` recording the reversal
and dating it 2026-09-21 `[repo]`.

This is the mirror of the named failure and worth calling out as its own shape:
**a ledger of owed work that was not closed when the work was done.** The brief's
standing assumption is that fixes are partial; an un-closed pointer makes a
*complete* fix read as partial, which costs the next reviewer the same time.

**Should be:** mark it done, or delete the blockquote.

### G7-11 — ADR 0005's 3V3 argument predates `key-scan-current`

**Node:** figure `key-scan-current` (1.43 mA/key, 25.8 mA at 18 closed).

`docs/decisions/0005-power-architecture.md:206-208` `[repo]`:

> "**3.3 V does not need its own converter.** The loads on it are the shift
> register chain (**microamps**), the ADC (milliamps) and pull-ups, all
> comfortably inside the headroom of the real-time board's onboard regulator."

`key-scan-current` is **25.8 mA on 3V3 at play rate**, and the corpus's own
conclusion about it is the opposite of "comfortably inside the headroom":
`key-switch-network.md:129` — *"**not free any more**, because 25.8 mA of
play-rate load lands on the rail that is also the MCP3202's voltage reference —
worth 3.2 LSB"*. The register's `escape_note` records the figure only became
tracked on 2026-09-21; ADR 0005's sentence is from the 10 kΩ era, where
`0.33 mA per closed key` (a forbidden value) really was near-microamp territory.

Medium confidence on wording: "the shift register chain" could be read as the
ICs' own Icc. But the sentence also enumerates "pull-ups" and then asserts the
whole set is comfortable, which is the claim `key-scan-current` exists to refute.

**Should be:** cite `key-scan-current` and say the 3V3 conclusion survives
*because* the droop was budgeted at 3.2 LSB, not because the load is microamps.

### G7-12 — `R-KEY-PU`'s own row restates the pre-`R-KEY-SER` current

**Node:** `R-KEY-PU`, `hardware/bom.csv` + `hardware/cluster/key-switch-network/bom.csv`.

The row reads *"**1.5mA per PRESSED key** against a 360mA budget is nothing"*
`[repo]`. `key-scan-current` is **1.43 mA** `[repo] figures.yaml:193`, derived
as `3.3 / (2200 + 100)` — i.e. **with** `R-KEY-SER`. `[calc] 3.3/2200 = 1.50 mA`
is the pull-up alone, the value before the 100 Ω series resistor entered the
network. The `360mA budget` is likewise a restatement of `umbilical-current`
(359 mA).

Low severity — the conclusion ("is nothing") is unaffected — but it is a row of
the most-cited file restating two tracked figures instead of citing them, and
one of them at its superseded value.

### G7-13 is filed under Shape 2. Shape 1 continues:

### G7-14 — `pcb-pipeline.md`'s re-measured table is stale on every number

**Node:** `hardware/unplaced.csv`, `docs/reference/pcb-pipeline.md:150-168`.

The blockquote is headed *"**Re-measured against the current tree,
2026-09-21**"* and is live guidance, not history. Re-measured in the pinned
clone at `a4b80b1`, tree clean `[test] python3` over `hardware/bom.csv`,
`hardware/unplaced.csv` and `hardware/**/bom.csv`:

| `pcb-pipeline.md:153-155` says | Actual |
|---|---|
| master: **138** rows / **388** units | **140** / **391** |
| in the **23** per-circuit fragments: **104** / **313** | **22** circuit-level fragments (25 fragment files, 26 counting `unplaced.csv`); **108** / **324** |
| `unplaced.csv`: **34** rows / **75** units | **32** / **67** |

And the consequence drawn from it, `:158-166`, has moved under it. Searching
every fragment in the pinned clone `[test] python3`, of the five named
module-board parts only three are still in `unplaced.csv`
(`U-TVS-MODULE`, `R-BREATH-SUM` ×2, `R-BREATH-OFF` ×2). **`J-CV` is now placed**
in `hardware/module/bom.csv` and **`D-CLAMP-BREATH` is now placed** in
`hardware/module/breath-receive-stage/bom.csv`. So "five … **Thirteen units**"
is now three parts and `[calc]` **five units** — and `:164-168`, which uses
`D-CLAMP-BREATH` as *"the shape of the problem … its row is **still in
`unplaced.csv`**"*, names a row that is no longer there. The illustration that
survives is `J-CV` ×6, which also moved.

### Shape 1, minor: G7-15 — the `~1594` count and the `1598` that derives it

`key-scan-current.companion` `[repo] figures.yaml:198` and two pages
(`carrier.md:177`, `carrier.md:373`, `key-chain-loom.md:129`) put the playable
breath span at **~1594 counts**. The derivation that produces it,
`breath-adc.md:37-45`, gets **1598** `[calc]`: `(0.265 + 0.7665×2.8) × 0.6 /
3.3 × 4096 = 1795` minus `0.265 × 0.6 / 3.3 × 4096 = 197` = **1598**. Four
counts, three files, one derivation, and the register's own `escape_note` at
`figures.yaml:199-214` already says the deduplication "is still owed".

---

## Shape 2 — a fix whose own explanation restates the wrong value

### G7-13 — `diode-split-rationale`'s derivation chain is ~2000× off its own result

**Node:** `D1`/`D2`, figure `diode-split-rationale`;
`config/figures.yaml:626` and `hardware/module/power-entry/power-entry.md:105-107`.

Both state the chain identically `[repo]`:

> 120 mV → LM317 line reg 0.52 mV/V → **62 µV on AVDD** → OPA2197 PSRR
> **110.5 dB** worst case → **0.00044 cents**

`[calc]`, 1 V/oct ⇒ 1 cent = 1/1200 V = 833.3 µV. 110.5 dB = ×3.350×10⁵.
- Chain **as written**: 62.4 µV / 3.350×10⁵ = 1.86×10⁻¹⁰ V = **2.2×10⁻⁷ cents**.
- The stated **0.00044**: 0.120 V / 3.350×10⁵ = 3.58×10⁻⁷ V = **4.3×10⁻⁴ cents** ✔

So the published number is the **120 mV applied straight to the PSRR, with the
LM317 line-regulation step skipped.** The predecessor confirms it: the entry says
*"scales the result by 1.50×, from 0.00029 to 0.00044"*, and
`[calc]` 0.120 V / 10^(114/20) = 2.39×10⁻⁷ V = **0.00029 cents** exactly. Both
the old and the new value were computed the same wrong way.

This is Shape 2 exactly: the `provenance_note` is *about* correcting two inputs
(75–80 mV → 120 mV, 114 dB → 110.5 dB), reads authoritatively, and the
arithmetic between its own stated terms has never produced its own stated
result. **The conclusion is unharmed** — the true figure is 2000× *smaller*, so
"five orders of magnitude below every other term in the table" becomes eight —
which is why it has survived. **Should be:** drop the `62 µV on AVDD` step from
the chain, or restate the result as ~2×10⁻⁷ cents.

### G7-16 — `umbilical-current`'s derivation ends at 358.1 and the value is 359

**Node:** figure `umbilical-current`, `config/figures.yaml:614-617`.

`value: "359 mA"`; `derivation: "226 mA x 5 V / (0.9 x 11.4 V) + 248 mA =
358.1 mA"`. `[calc] 226×5 = 1130; 0.9×11.4 = 10.26; 1130/10.26 = 110.1;
+248 = 358.1.` The register's own arithmetic, spelled out in the field, does not
round to its own `value`.

**And the rest of the table does not use the stated convention.** ADR 0005
states it at `0005:161-163` — *"convert at the **arriving** voltage … and the
buck is **~90 % efficient**"* — but `[calc]` on the other three rows of
`0005:158-161` back-solves an arriving voltage of ~11.2–11.3 V, not 11.4:

| Row | 5 V | 12 V | stated umbilical | at 0.9 × 11.4 V |
|---|---|---|---|---|
| Quiescent | 180 | 123 | 212 | **210.7** |
| Typical play | 226 | 248 | 359 | **358.1** |
| + live config | 336 | 248 | 414 | **411.7** |
| Clamp-legal worst | 928 | 119 | 579 | **571.2** |

Low confidence that any of these is a defect rather than a deliberate
per-row arriving voltage; **but the derivation field is a defect either way**,
because it is the one place the convention is asserted and it disagrees with the
value it derives.

### G7-17 — `loadswitch-fb-divider`'s derivation expression gives 8, not 7

**Node:** `R-FB-HI`/`R-FB-LO`, `config/figures.yaml:513`.

> "the nominal target is 10.5 V, giving R-FB-HI/R-FB-LO = **1.313/10.5 inverted
> = 7.00**. 35.7k/5.11k is 6.986."

`[calc] 10.5/1.313 = 7.997`, not 7.00. The divider ratio is
`V_OUT/V_FBH − 1 = 6.997`, which is what 35.7k/5.11k = 6.986 matches. The
**answer is right and the expression written beside it is not** — it is off by
the "−1" and would mislead anyone re-deriving the divider from this field.
Everything downstream checks out `[calc]`: `1.313 × 7.986 = 10.49 V` PWRGD
release ✔, `0.5 × 7.986 = 3.99 V` ✔, `0.5/1.313 = 0.381` ✔.

### G7-18 — `opa2197-output-impedance`'s note is blocked on a question that is settled

**Node:** figure `opa2197-output-impedance`, `config/figures.yaml:706`.

> "**Not recomputed yet**, because it is **blocked on a prior question**: three
> files disagree about which side of the buffer `C-REF-OUT` sits on"

`cref-out-node` is `status: settled` `[repo] figures.yaml:521`, and its own note
says *"**IT BLOCKED riso-ref-topology, which is now also settled**"*
`[repo] figures.yaml:539`. `riso-ref-topology` is `settled` with the
recomputation done — *"Simulated phase margin 85.9 deg at 896 kHz"*
`[repo] figures.yaml:556`. So the stated blocker is gone and the recomputation
happened; this note is the register describing a state of the world two
decisions ago.

Its conclusion has also moved: *"The case for R-ISO-REF is **STRENGTHENED**"* —
`breath-excitation-reference.md:41-44` now says *"in-loop `R_ISO` buys nothing at
**any** value, 1.5° at 10 Ω and 1.5° at 37.4 Ω"*. The part survives only as one
of four in TI's dual-feedback network, which is a different argument.

### G7-19 — `latency-budget.md`'s own correction sentence gets the sum wrong

**Node:** `docs/reference/latency-budget.md:44-51`.

The analog breath table `:42-43` books **330 µs** (482 Hz) and **332 µs**
(480 Hz). The paragraph immediately below, `:47-50`, says:

> "a 500 Hz pole has 318 µs of group delay by definition, and this path has two
> of them. **The real figure is 632 µs** — three times what was written"

`[calc] 330 + 332 = 662 µs`, and `2 × 318 = 636 µs`. **632 matches neither** its
own table nor its own reasoning. A correction sentence, two lines under the
numbers it is correcting.

### G7-20 — the digital-copy total does not reproduce from its own rows

**Node:** `docs/reference/latency-budget.md:54-65`.

`[calc]` from the page's own rows: `2.17 (to sensor output) + 0.282 + (0…0.250)
+ 0.024 + 0.020 + 0.096 + 0.010 + 0.082` = **2.68–2.93 ms**. The stated total at
`:65` is **~2.9–3.1 ms + restrictor**, and `:76` states a third number for the
same budget, **2.80 ms**. Low-to-medium confidence — "~" may be doing work — but
three figures for one total in 22 lines is the shape that produced
`pitch-cents-budget`'s dispute.

The key-path table by contrast reproduces exactly `[calc] 0.25+0.032+0.25+0.02+
0.06+0.01 = 0.622`, `5/0.622 = 8.0×`, `0.50/0.622 = 80 %` — all three stated
figures check out.

---

## Shape 3 — a stated count that has moved under the sentence stating it

Every count below was measured, not read.

### G7-21 — `README.md:117`: "`docs/review/` holds nine waves"

`[test]` pinned clone at `a4b80b1`, tree clean, `ls -d docs/review/*/ | wc -l`
→ **11**. (The live tree read **12**, this wave's own directory; the corpus says
nine either way.)

The sentence containing it is the one that explains why counts do not belong
there: *"The counts that used to sit in this sentence — '77 banked documents',
'seven waves' — were true when written and wrong within the week, which is the
whole reason this repository cites rather than restates."* It then restates one.

`CLAUDE.md` names this as the third recorded instance and says of its own
equivalent sentence *"There is deliberately no number in this sentence."*
`README.md:117` is the fourth.

**Should be:** no number. `ls -d docs/review/*/` is the count.

### G7-22 — `hardware/README.md:112`: "It was 50 rows and is now 34. Sixteen of them were drawn all along"

`[test]` pinned clone at `a4b80b1`, tree clean, `csv.DictReader` over
`hardware/unplaced.csv` → **32 data rows**. So `[calc] 50 − 32 = 18`, not
sixteen. **Both numbers in the sentence are wrong.**

Both numbers in one sentence, and the sentence's own subject is a count. The
trim commits `c4109ec` / `192d03e` moved rows out after `0e68f25` wrote "34"
`[test] git log -S"is now 34" -- hardware/README.md`.

**Should be:** "It was 50 rows and is now 32. Eighteen of them were drawn all
along" — or a pointer, since this will move again.

### G7-23 — `repo-maintenance.md:204`: "the 50 rows of 138"

Live guidance inside §4's `> The trap` blockquote — **not** framed as history;
the italic line at `:212` only records that the section once described `bom.csv`
as hand-edited. Actual: **32 of 140**, from the pinned clone at `a4b80b1`, tree
clean `[test] python3 tools/merge-bom.py --check` → `checked 140 rows from 26
fragments | 0 problems`.

The two clusters it names are also gone: *"six identical jack-protection
networks drawn three times, and **nineteen decoupling capacitors with no home**"*
— `unplaced.csv` today holds no jack-protection rows and one capacitor row
(`CAP1-n`, qty 21) `[repo] hardware/unplaced.csv`.

### G7-24 — `repo-maintenance.md:191`: "24 per-circuit `bom.csv` fragments"

Pinned clone at `a4b80b1`, tree clean `[test] python3 tools/merge-bom.py
--check` → *"checked 140 rows from **26** fragments"*.
`[test] find hardware -name bom.csv | wc -l` → 26 files, of which one is the
generated master: **25 fragments** (22 circuit-level + 3 board-level), plus
`hardware/unplaced.csv`, which `merge-bom.py` also reads `[repo] tools/merge-bom.py:85,97`
— hence 26.

`CLAUDE.md` gets this right by saying "the per-circuit `bom.csv` fragments" with
no number. `repo-maintenance.md`, the file that exists to hold this detail, has
the number and it has moved.

**Also G7-14 above** states `pcb-pipeline.md` uses a third figure, **23**.
Three files, three counts, one set of fragments.

### G7-25 — `repo-maintenance.md:311` + `:322`: "every tracked file has a row", "405 tracked files"

I ran the file's own four-line assertion, quoted at `:334-338`, in the pinned
clone at `a4b80b1` with the tree verified clean `[test] python3`:

```
rows 410  deleted 4     tracked files 440
TRACKED WITH NO ROW: 34        ROWS POINTING AT NOTHING: 0
```

**440 tracked files against the stated 405**, and **34 orphans** against "every
tracked file has a row" — the `2026-09-22-fix-audit/` and
`2026-09-22-fix-audit-review/` directories. (In the live tree it reads 441 / 35,
the extra being this wave's own directory.)

The section's own italic warning says this sentence *"was false for most of a
day, and it is worth saying how"*, diagnoses it (Phase B created files the map
had never heard of), publishes the check, and says *"run it whenever files are
added, **because a new file is an orphan the moment it is committed**"*. Two
review waves were then committed and nobody ran it. **The paragraph predicted its
own next failure and the prediction came true inside a day** — the same shape
`CLAUDE.md` records for the review-wave count.

**Should be:** either the check runs in `check-staleness.py`, or `:311` says
"every tracked file **as of 2026-09-21** has a row" and the count goes.

### G7-26 — `U-RESP` is counted twice, and its two halves are allocated twice

**Node:** `U-RESP` / `U-OPA-PITCH`. **Shape 3, two ways.**

`U-OPA-PITCH` `[repo] hardware/bom.csv:80`: *"**Six packages, twelve halves, TEN
used**: pitch, mod 1-4, mod offset follower, VREFOUT follower, breath REF-zero
buffer, breath gain buffer, breath summer. **TWO SPARE** — and U-RESP claims
both of them if it is fitted."* `[calc]` the enumeration is 10 items ✔, 12 − 10
= 2 ✔, `R-OPAMP-IN` qty 7 for the seven DAC-driven inputs ✔. The count is sound.

But `U-RESP` is its **own BOM row**: `U-RESP,module,OPA2197IDR,…,SOIC-8,1,open`
`[repo] hardware/module/breath-response-shaper/bom.csv:5`. A qty-1 SOIC-8
OPA2197 is a **seventh package**, not two halves of the sixth. Fitting the
shaper as the BOM is written orders 7 packages while every page in the corpus
says the module has 6 with two spare halves.

**And the two halves are allocated twice, contradictorily:**

- `hardware/module/breath-response-shaper/breath-response-shaper.md:128` —
  *"**Both remaining OPA2197 halves** — one shapes at ÷2 inverting, one restores
  ×2 inverting"* (both to the shaper), echoed at `:30` — *"`U-RESP`'s two halves
  — the last two on the module"*.
- `U-RESP`'s own BOM row — *"the shaper needs **one** and **POT-OFFSET's wiper
  needs the other**"*.

Those are mutually exclusive. On the page's reading `POT-OFFSET` gets no buffer
and its unbuffered zero *"sits ~20 degrees past centre at +0.605V"* — a defect
the row raises and the page's allocation reintroduces.

### G7-27 — `ROADMAP.md:71`: "the four thumb keys … the eleven finger keys"

`[repo] config/key-layout.yaml:44-48`: `left_thumb: 4`, `right_thumb: 3`,
`total: 18`. **Seven thumb keys**, eleven finger keys (LH 5 + RH 6) ✔.
`[calc] 4 + 11 = 15` of 18 — RT1-3 are unaccounted for by a sentence about
"fingertip vs thumb-tip" action.

**Lower confidence than the rest of this section.** `SW-THUMB` is qty **4**
`[repo] hardware/cluster/key-switch-network/bom.csv` and is described as the LT
spring variant, so "four" may be deliberate and mean the left-thumb note keys
only. If so the sentence should say so; as written it partitions 18 keys into
4 + 11.

Note `PLATE-THUMB`'s BOM row states the real split correctly: *"Carries the 4
left-thumb and 3 right-thumb switches"* `[repo] hardware/bom.csv`.

---

## Counts I checked that are CORRECT

Recording these so the next slice does not re-spend the time. All `[test]`
measured or `[calc]`:

- `hardware/README.md:19-22` — carrier **5**, cluster **3**, module **12**,
  interfaces **3** circuits = 23 ✔ (`find hardware -name circuit.yaml | wc -l`
  → 23; `check-staleness.py` reports `23 circuits`).
- `chain-connectors` = **8**: carrier 1, RT 2, RH 2, LT 2, LH 1 ✔ — consistent
  at `0001:254`, `key-chain-loom.md:88/:252`, `carrier.md:293`,
  `cluster-boards.md:205-212`, and `J-CHAIN` qty 8 in the BOM.
- `chain-conductors` = **12**: `GND SCK GND SH/LD GND SER GND QH GND 3V3 spare
  spare` ✔ (4 signals + 5 grounds + 3V3 + 2 spare).
- `key-layout.yaml` bit accounting: 4 devices, 32 bits, 18 used, 14 spare; 8
  marker + 3 spare-switch + 3 free = 14 ✔.
- `key-pullup-qty` = 24 = 21 positions + 3 free ✔.
- `cluster-boards.md:210` — 4 ICs, 4 decoupling caps, 18 switches in 21
  positions, 7 chain connectors + 1 on the carrier ✔ (**except** "63 network
  passives", G7-2).
- ADR 0006 — "Six of eight channels used, two spare" ✔ (ch1 pitch + ch2-5 mod +
  ch7 reference = 6; ch6, ch8 spare). `R-OPAMP-IN` qty 7 ✔.
- ADR 0007 / `ROADMAP.md:195` — 17 GPIO broken out, 14 used, **3 spare** ✔.
- `decisions/README.md:39` — "three of its **fourteen** rows" ✔ (ADRs 0001-0014,
  14 index rows).
- `panel-height-budget` — `[calc]` 5 + 22 + 39 + 31 + 13 = **110** ✔;
  128.5 − 2×(3.0 + 3.5) = **115.5** ✔; 5.5 spare over 4 row boundaries = 1.4 ✔;
  116.9 / 112.5 on the other two hardware assumptions ✔; toggle strips
  (50.50 − 26)/2 = 12.25, (12.25 − 6.5)/2 = **2.88** ✔, D3.2 bezel 4.52 ✔,
  10.5 × sin 25° = **4.44** ✔. Every number in this entry reproduces.
- `loadswitch-timer` / `loadswitch-gate-cap` — 9.37 µF, 62×150 = 9.30 µF,
  587/160/95.6 ms at the 21/77/129 µA net, 95.6/47.5 = **2.01×**, 89.85/47.5 =
  **1.89×**; 82 nF → 61/122/244 V/s → 197/98/49 ms. All ✔ `[calc]`.
- `inamp-full-scale`, `sensor-full-scale`, `breath-sensor-slope`,
  `breath-zero-ref`, `key-press-time`, `key-release-time`, `dac-rail`,
  `panel-width`, `mod-reference` — every `derivation` field reproduces to the
  stated `value` `[calc]`.
- `breath-adc.md:37-45` — the whole divider chain reproduces (2.92 V / 3622 /
  197 / 1795 / 1598) ✔; only the 1594-vs-1598 spread of G7-15 is off.
- `mod-channels.md` — 3.3333/2500 = **1.33 mA** ✔ (the register's recorded
  1 mA→1.33 mA fix has landed); `4 × 0 − 3 × 0 = 0 V` ✔;
  `4 × 0 − 3 × 3.3333 = −10.00 V` ✔.
- `riso-ref-topology` — 37.4 = 375/10 ✔; TI 4.08 Hz ✔; 15.9 kHz ✔; 0.19 LSB ✔.
- `latency-budget.md` key path — total, 8× margin and the 80 % claim all ✔.
- ADR 0014 — 960 × 0.49 = 470 ✔ (the arithmetic is fine; the premise is G7-6).

---

## What I could NOT check

- **Anything requiring a datasheet PDF.** I did not open
  `datasheets/**`, so every `[datasheet …]` citation in the corpus — the
  MPXV4006DP transfer function, SBOS737C's 375 Ω and PSRR, the onsemi 3.0 V
  row, the Gateron drawing's 1.20 mm and 5 ms, 164112fc's currents — is taken as
  the corpus states it. G7-13's arithmetic is independent of whether 110.5 dB is
  the right number.
- **`docs/review/**`, `docs/log/**`, `docs/research/**`** — excluded by the cold
  rule and by §6. So I cannot say whether any finding here was already filed.
- **Whether the fixes G7-10 and G7-9 describe as owed were closed by a wave that
  did not update its pointer**, for the same reason.
- **Simulation and phase-margin claims** (`[sim, A4]`, 85.9° / 87.4° / 76°) —
  no deck was run. `hardware/module/breath-receive-stage/sim/` and
  `hardware/module/pitch-stage/sim/` exist; I did not execute anything in them.
- **`pitch-cents-budget` and `breath-working-point`** — both `status: disputed`
  with candidate lists. I did not attempt to adjudicate; a disputed figure is
  not a Shape-1 target because nothing has been corrected yet. `pitch-stage.md`
  does still carry two contradictory budget tables back to back, as the register
  says `[repo] figures.yaml:479-481`.
- **`dig-gnd-topology`** — the register already files it as the named failure
  mode (`0004:627` still says the opposite of `power-entry.md:495-498`). I
  confirmed nothing new and did not re-verify the line numbers.
- **`docs/reference/path-map-2026-09-21.csv`'s `old` side** — the 288 distinct
  old paths were not checked against `81c081d`; I checked only the `new` side,
  which is what G7-25 rests on.
- **Whether any finding here was already injected rather than original.** A
  slice was planting defects in this same checkout. Everything I report was
  re-read from a clean `a4b80b1` clone, so nothing here is an injected string —
  but I cannot rule out that a defect I found is one an injection slice *also*
  found and reported independently.
- **Whether the 24 "refuted in place" exemptions hide a wrong replacement.**
  `[test] python3 tools/check-staleness.py --detail` reports *"old values present
  but refuted in place (24)"* — this one run was taken from the live tree before
  the pinning warning and has **not** been re-taken from the clone, so treat the
  count as approximate. Rule 2b's own worked example
  (`TRIM-BREATH-ZERO`) is a refutation carrying a stale replacement, and the
  checker cannot see that class. I read several but not all 24; a slice that
  reads exactly those 24 windows would be well spent.

---

## One methodological note for the wave

Three of the escapes above (G7-3, G7-4, G7-7) are the **same mechanism**, and it
is the one `sensor-full-scale.escape_note` already names: the `forbidden` pattern
was written in the spelling of the document doing the correcting, and the
document that needed correcting spells it differently.

- G7-3: pattern `"SAR ADC conversion ~50"` vs ADR 0003's
  `| SAR ADC conversion | ~50–200 µs |` — table cell, pipes, en dash.
- G7-4: pattern `"ADR 0009 specifies a ~2 mm aluminium top plate"` (ADR 0002's
  sentence *about* ADR 0009) vs ADR 0009's own
  `| Aluminium top plate, 2 mm | 157 |` and `thumb switch plate        ~2 mm`.
- G7-7: five patterns about bounce being unpublished, none matching ROADMAP's
  `"neither is published"` or `"nobody publishes"`.

**A cheaper mechanical fix than more patterns exists for all three**: normalise
the searched stream before matching — collapse runs of whitespace, strip `|`,
`*`, backticks and `~`, and fold en/em dashes to `-`. That would have caught
every escape this register has recorded (the missing space, the pipes, the en
dash, the Title case aside) without adding a single pattern, and without the
false-positive risk the register keeps having to defend against. It is a change
to `tools/`, which this wave has not pinned, so it belongs after the freeze.
