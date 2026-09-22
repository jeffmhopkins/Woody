# E1 — independent re-verification of the fix-audit wave's merge-critical claims

**Slice:** the twenty reports in `docs/review/2026-09-22-fix-audit/`, plus its
`STATUS.md` and `VERIFIED.md`. **Method:** every claim below was re-measured
from the primary source — the tool re-run, the arithmetic re-derived, the
banked PDF and STEP re-read, the file opened and counted. No sibling file in
`docs/review/2026-09-22-fix-audit-review/` and no earlier wave was read.

**Provenance:** `[test]` command and output, `[calc]` arithmetic shown,
`[repo] path:line`, `[datasheet]` document and page, `[step]` measured out of
the banked solid.

---

## E1-0 — READ THIS FIRST: the corpus was not frozen while this round ran

Round 2's `README.md` says *"Report, do not fix. The corpus is frozen."* It
was not.

`[test]` At my first command the tree was clean at `0576a95` and the checker
printed `PASS` five times out of five. `[test]` Ninety seconds later
`tools/check-staleness.py` had an uncommitted 49-line diff
(`stat`: modified `2026-09-22 03:03:27`, my session began `03:03`), and
minutes after that it was committed as **`566159e` "Fix the instrument: the
verdict is reproducible again"**. That commit lands fix-order items 1–3 from
the wave's own `STATUS.md`: the `check_owners` union + total sort order, and
the withdrawal of the date / `->` / `→` / `NOT` markers. `rewrite-paths.py`
was fixed in the same commit.

Three consequences, and all three matter more than any single row below:

1. **Every "the checker says PASS" statement in the fix-audit wave now
   describes a tool that no longer exists.** I therefore pinned all
   measurements to `0576a95` (`git archive` into a scratch tree, and a clone
   checked out at that rev for the git-dependent tools), and say so per row.
2. **The repaired checker does not pass.** `[test]` at `566159e`:
   `FAIL 0 shape + … + 8 stale + 0 bom`. The commit hook is failing on the
   corpus right now. The eight are listed in E1-5.
3. A round whose premise is "agreement between agents that cannot see each
   other is evidence" cannot also be a round in which the subject is being
   edited underneath the agents. Anyone reading this table should check
   `git log` before acting on a row marked `@0576a95`.

---

## The table

`@rev` marks the tree the measurement was taken on.

| # | Claim (source) | Verdict | What I measured |
|---|---|---|---|
| 1 | `check_owners` is nondeterministic end to end — D1 F2, `STATUS` §1 | **CONFIRMED** (ratio corrected) | E1-1 |
| 2 | "6 of the 24 token-bearing settled figures flap" — D1 F2 | **CONFIRMED WITH A CORRECTION** — it is **5** | E1-2 |
| 3 | 24 token-bearing, 8 `UNVERIFIABLE` of 32 settled — D1 | **CONFIRMED** exactly | E1-2 |
| 4 | All **68** forbidden-pattern matches exempted; live list empty — D3, D5, `STATUS` §2 | **CONFIRMED** exactly | E1-3 |
| 5 | The four withdrawn markers are sole support for 8 matches | **CONFIRMED** — and they are byte-for-byte the 8 the repaired tool now reports | E1-5 |
| 6 | `WIRE-LOOM` still live, exempted by a date **222 characters** away — `STATUS` §2 | **CONFIRMED** exactly | E1-4 |
| 7 | Exempt region **33.9 % → 48.4 %** of corpus characters — D5 | **CONFIRMED WITH A CORRECTION** — I get **33.6 % → 48.2 %** | E1-6 |
| 8 | "D3 and D5 measured that independently" — `STATUS` §2 | **REFUTED** — the *pair* has one source | E1-7 |
| 9 | `check_bom_figures` reaches **1 figure of 37** — D2, `STATUS` §3 | **CONFIRMED** exactly | E1-8 |
| 10 | "eighteen figures name a real BOM refdes elsewhere in their entry" — `STATUS` §3 | **CONFIRMED WITH A CORRECTION** — **17** | E1-8 |
| 11 | `C-GATE-LOADSW` 82 nF → 100 nF by the documented procedure gives `0 problems` / `PASS` — D2 §1.2 | **CONFIRMED**, byte-identical | E1-9 |
| 12 | `primary = max(nums, key=len)` false-fails on a correct BOM — D2 §1.4 | **CONFIRMED** — 5 of 6 figures I tried | E1-10 |
| 13 | `rewrite-paths.py --invert` = **112 MISMATCH**, 92 of them map-`created` — D4.21 | **CONFIRMED** exactly, both numbers | E1-11 |
| 14 | 0.625 × 5.21 = 3.2563 V; 3.3 V clears it; ADR 0004's stated conclusion is false at nominal — D12-1 | **CONFIRMED** | E1-12 |
| 15 | Plate gap is **2.50 − 1.20 = 1.30 mm**; the 3.2–3.6 mm premise is impossible at its upper end (−0.10 mm) — D14 | **CONFIRMED** from the vendor drawing | E1-13 |
| 16 | "−3.2 is not a coordinate in the file" — D14-1 | **CONFIRMED WITH A CORRECTION** — not a *z* coordinate; it is an *x* | E1-13 |
| 17 | 2.1 mA × 50 = **105 mA**, not the 123 mA claimed "exactly" — D13-9 | **CONFIRMED** | E1-14 |
| 18 | The clamp inverts: ~3 W is **0.83×** a realistic 3.6 W — D13-1 | **CONFIRMED** | E1-14 |
| 19 | "14 of 18 rows moved out of `unplaced.csv` are named by zero hardware pages" — `STATUS` | **CONFIRMED WITH A CORRECTION** — **15 of 18**; worse than claimed | E1-15 |
| 20 | Drawing corrupted at `breath-receive-stage.md:67` (rails 68/70 → 85/87) and **wrong part** at `:110` — D9-1/D9-2, D19 | **CONFIRMED** exactly | E1-16 |
| 21 | BOM byte-exact: 131,725 bytes, 139 rows, 140 CRLF, 11 cols, no duplicate refdes — `STATUS` | **CONFIRMED** exactly | E1-17 |
| 22 | 76 manifest rows ↔ 76 files both ways; 0 dangling citations; `LT1641` 51 / `LT4256` 0 — D11, `STATUS` | **CONFIRMED** (one wording correction) | E1-18 |
| 23 | Duplicate `false_positive_note` key silently discards a note — D12, D20 | **CONFIRMED**; convergence **partly** real | E1-19 |
| 24 | Three `forbidden` patterns carry their own exemption marker — `STATUS` fix-order 3 | **CONFIRMED** — exactly 3, named | E1-20 |
| 25 | D10's **reversal** of the sibling's `360 mA` staleness claim | **CONFIRMED** — D10 was right to reverse it | E1-21 |

**Nineteen of twenty-five confirmed outright; five confirmed with a numeric
correction; one refuted.** The fix-audit wave's mechanical work is, on this
evidence, unusually accurate. Every correction below is in the *conservative*
direction except two (E1-2, E1-6), and E1-19's correction makes the finding
worse, not better.

---

## E1-1 — the nondeterminism, reproduced end to end `@0576a95`

`[repo] tools/check-staleness.py:864` at `0576a95`:
`sorted(set(nums), key=len, reverse=True)[:1]`. `sorted` is stable and
`key=len` is not a total order, so among equal-length tokens the winner is
whichever the `set` iterates first — i.e. `PYTHONHASHSEED`.

`[test]` D1's exact experiment, in a pristine `0576a95` tree, thirty runs
instead of ten:

```
$ sed -i 's/5\.11/5\.10/g' hardware/module/umbilical-load-switch/umbilical-load-switch.md
$ for i in $(seq 30); do python3 tools/check-staleness.py | cut -c1-12; done | sort | uniq -c
      9 FAIL 0 shape
     21 PASS no live
```

**CONFIRMED.** Same tree, same command, same live rule-1 violation, two
different verdicts. D1's `6 PASS / 4 FAIL` and my `21 PASS / 9 FAIL` are two
samples of one distribution, not a disagreement.

`[test]` To pin the rate rather than sample it, I swept `PYTHONHASHSEED`
0–299 over the token-selection step alone: `loadswitch-fb-divider` selects
`'5.11'` (→ FAIL) **137 / 300 = 45.7 %** of the time, `'35.7'` (→ PASS)
163 / 300. My 30 live runs sat 1.7σ low of that; nothing in the mechanism is
better behaved than a coin.

**The operative sentence in D1 is right and is the reason this blocks a
merge:** a maintainer who re-runs after a surprising FAIL sees it disappear.

---

## E1-2 — how many figures actually flap: five, not six `@0576a95`

D1's prose says *"6 of the 24 token-bearing settled figures flap"*. **Its own
seed dump lists five**, and five is the right number.

`[test]` 120 `PYTHONHASHSEED` values, recording the selected token set per
figure: 5 figures produce more than one outcome. `[calc]` and definitively,
by enumerating *all permutations* of each figure's candidate pool rather than
sampling:

| figure | `value` | possible selections |
|---|---|---|
| `key-scan-current` | `1.43 mA per closed key, 25.8 mA at 18 closed` | `1.43` / `25.8` |
| `panel-toggle-hole` | `6.5 mm diameter with a 5.8 mm D-flat` | `5.8` / `6.5` |
| `loadswitch-fb-divider` | `35.7 kohm / 5.11 kohm, both 1%` | `35.7` / `5.11` |
| `loop-budget` | `196-241 us of 250 us` | `196` / `241` / `250` |
| `ferrite-bias-impedance` | `~580-614 ohm on FB1/FB3/FB4; ~280-310 ohm on FB2` | `280` / `310` / `580` / `614` |

**Exactly five, and no sixth exists** — no other settled figure has a tie at
the selection boundary. This is a **CORRECTION**, and note the direction: D1
overstated by one in a report whose evidence block was correct. The evidence
was right; the summary sentence counting it was not.

`[test]` The surrounding counts are exact: **32** settled figures, **24**
token-bearing, **8** reported `UNVERIFIABLE`. D1's denominator and its
`UNVERIFIABLE` list are confirmed.

---

## E1-3 — all 68 matches exempted, live list empty `@0576a95`

`[test]` Loading the tool as a module and calling `check_figures()` directly,
so no other check's noise is mixed in:

```
TOTAL MATCHES: 68   live: 0   exempted: 68
patterns in register: 218        figures: 37
```

**CONFIRMED exactly.** The stale-value half of the checker reported nothing
at all on this corpus. This is the second independent count of it and it
agrees to the unit.

---

## E1-4 — `WIRE-LOOM`, and the 222 characters `@0576a95`

`[repo] hardware/carrier/bom.csv:6`, refdes `WIRE-LOOM`. `[calc]` on the
joined stream the checker searches:

```
'five connectors must match'   at column 388
'2026-09-21'                   at column 166      distance = -222
```

**CONFIRMED exactly, to the character.** The row's text still contains
`rather than starred` — the clause it used to ride on — but that phrase was
dropped from the vocabulary, so the row now rides on the date that the *same
commit* introduced. The commit message names this row as one of the two
escapes it was closing. It closed the escape and opened a wider one 222
characters away.

---

## E1-5 — the four withdrawn markers are sole support for exactly eight

`[test] @0576a95` Re-running the exemption test with the base vocabulary and
the four added markers separated:

```
exempted by the base vocabulary ......... 60
exempted ONLY by date / -> / → / NOT ..... 8
live ..................................... 0
```

The eight:

| figure | pattern | file | marker |
|---|---|---|---|
| `chain-connectors` | `five connectors must match` | `hardware/bom.csv:30` | `2026-09-21` |
| `chain-connectors` | `five connectors must match` | `hardware/carrier/bom.csv:6` | `2026-09-21` |
| `panel-toggle-hole` | `6.00 and 6.35 need different holes` | `hardware/bom.csv:63` | `NOT` |
| `panel-toggle-hole` | `6.00 and 6.35 need different holes` | `…/umbilical-load-switch/bom.csv:2` | `NOT` |
| `loadswitch-timer` | `the reviewers disagree and the datasheet decides` | `hardware/bom.csv:71` | `2026-09-21` |
| `loadswitch-timer` | `the reviewers disagree and the datasheet decides` | `…/umbilical-load-switch/bom.csv:10` | `2026-09-21` |
| `loadswitch-timer` | `2.4x the ~62ms` | `hardware/bom.csv:71` | `2026-09-21` |
| `loadswitch-timer` | `2.4x the ~62ms` | `…/umbilical-load-switch/bom.csv:10` | `2026-09-21` |

**That prediction was made before I ran the repaired tool.** `[test]` at
`566159e`, `.staleness/report.txt` now reports `STALE VALUES STILL LIVE (8)`
and they are these eight rows, in this order. D3's `date REMOVED → live = 6`
and my 8 are the same measurement with and without the shouted `NOT`, and
both are right.

**This is the strongest single result in my slice**: an independent
prediction from a cold reading of the register matched the repaired
instrument's output exactly. The wave's diagnosis of defect 2 is correct.

---

## E1-6 — the exempt region, measured a third time `@0576a95`

`[test]` Over the same joined character stream, all 123 corpus files,
**1,196,197 characters** — a figure that reproduces D5's total exactly, which
tells me we scanned the same set:

| | measured here | D5 | D3 |
|---|---|---|---|
| OLD (old vocabulary, whole source line) | **33.6 %** | 33.9 % | — |
| NEW (new vocabulary + `NOT`, ±300) | **48.2 %** | 48.4 % | 47.9 % |

**CONFIRMED WITH A CORRECTION**, both ends about 0.3 pt low. Three
measurements of the new side now sit in 47.9–48.4 %; "roughly half the corpus
is ground where no pattern can fire" is solid.

### Is their method sound? Mostly — with two qualifications a fix should know

**Qualification 1: the headline conflates two changes, and attributes the
growth to the wrong one.** "33.9 % → 48.4 %" compares old-vocabulary /
*whole-line* against new-vocabulary / *±300-character window*. The window was
introduced in the same commit, so the pair is a fair before/after of the
commit — but it is read, in `STATUS` and now in the tool's own source comment,
as an indictment of the **vocabulary**. `[calc]` the 2×2 says otherwise:

| | whole source line | ±300 window |
|---|---|---|
| **old vocabulary** | 33.6 % *(as shipped before)* | 63.2 % |
| **new vocabulary** | **29.3 %** | 48.2 % *(as shipped after)* |

Read down the columns: **the vocabulary change narrowed the surface at either
geometry** (33.6 → 29.3, and 63.2 → 48.2). Read across the rows: **the window
is what widened it**, by 30 and 19 points respectively. In a corpus
hard-wrapped at ~78 columns, a ±300-character window is roughly eight source
lines, so moving from whole-line to windowed judgement is a large *widening*
for prose and a narrowing only inside the very long CSV rows it was written
for. The commit did two things in opposite directions and the net was
dominated by the one nobody measured.

This does not rescue the four markers — E1-5 shows they alone are worth eight
live defects — but "drop the date, the arrows and the shouted `NOT`" (fix
order 2) will **not** take the surface back to 33.9 %. It takes it to about
42.6 % (`[calc]` new vocabulary without `NOT`, ±300). If the goal is the old
surface, the window is the knob.

**Qualification 2: the denominator includes `config/figures.yaml`**, which
`check_figures` explicitly skips (`if rel == "config/figures.yaml": continue`)
and which is 67,928 characters of prose unusually dense in refutation words.
`[test]` excluding it: 33.6 % → 47.6 %. A ~0.6 pt effect, in the alarming
direction. Small, but it means the number is not quite "of the corpus the
checker scans".

**Everything else about the method is sound** and I would use it again: the
joined stream is the right substrate because it is what `check_figures`
actually searches, and dilating marker positions by the window is the right
model of the exemption.

---

## E1-7 — "D3 and D5 measured that independently" is **REFUTED**

`[test] grep -rn "33\.9\|48\.4" docs/review/2026-09-22-fix-audit/*.md` returns
**D5 only** (lines 123, 124, 127, 495), plus `STATUS.md:44` and
`VERIFIED.md:477` quoting it.

- D3 never states 33.9 %. D3 measured only the **new** side, and reports it as
  **47.9 %** `[repo] D3:548`.
- `VERIFIED.md:477` is accurate and careful — *"Accepted; consistent with D3's
  independent 47.9 %"*.
- `STATUS.md:44` compresses that into *"D3 and D5 measured that
  independently"*, where *that* is the **pair** including 33.9 %. **The pair
  has exactly one source.**
- The uncommitted-then-committed fix to `tools/check-staleness.py` escalates
  it again, to *"three cold slices measured that independently"*. `[test]` No
  third measurement of either number exists in the twenty reports.

So: **the 48 % figure is a real three-way convergence** (D3 47.9, D5 48.4,
E1 48.2, three methods, three agents). **The 33.9 % figure is single-sourced
and is now quoted in the tool's own source as triply-corroborated.** That is
the wave's named failure mode — a number travelling further than its
evidence — inside the fix for the wave's named failure mode.

### The other convergences, judged

The wave's briefs were **not** clean. `[test]` D7:35 *"The slice brief names
four entries that lost patterns"*; D9:211 *"A premise in the slice brief is
not borne out"*; D3:337 *"the brief's hypothetical"*; D19:321 *"brief flagged
…"*; and explicit sibling hand-offs in D10 (Part 2, "The two sibling
claims"), D11, D12, D13, D14, D15. Apparent convergence in this wave must be
checked case by case.

| convergence | real? |
|---|---|
| **68 matches / live list empty** (D1, D3, D5) | **Real but seeded.** D3 landed first (`a1983c0`); D1 and D5 landed later and could have been briefed with "68". But all three measured *different decompositions* of it — D3 sole-support-per-marker, D1 windows-containing-a-date (47 %), D5 date-with-no-other-marker (6). Three agents doing three different analyses of one number is independent work even if the number was handed to them. |
| **48 % exempt region** (D3, D5, E1) | **Real.** Different methods, different totals, agreeing to 0.5 pt. |
| **33.9 % old region** | **Not a convergence.** One source. See above. |
| **Duplicate YAML key** (D12, D20) | **Partly real.** See E1-19. |
| **BOM byte-exactness** (two slices' own concatenators) | **Real**, and I make it a third — E1-17. |
| **D14 on `ROADMAP.md:71`** | **Not independent, and D14 says so** — `[repo] D14:30` *"the sibling slice's claim … is confirmed"*. Filed honestly as a confirmation, not as agreement. |

---

## E1-8 — `check_bom_figures` reaches one figure of thirty-seven `@0576a95`

`[test]` Iterating the register exactly as `check_bom_figures` does, and
counting the figures for which the loop body executes at all:

```
figures total: 37
figures REACHED by check_bom_figures: 1
   spi-series-r   value='100 ohm, R-SPI-SER, qty 3'   ref=R-SPI-SER
```

**CONFIRMED exactly.** 1 of 37, 2.7 % of the register, for the check the
wave calls the flagship fix.

`[test]` Figures naming a **real BOM refdes** anywhere in their entry but
*outside* `value:` — i.e. in fields `check_bom_figures` never opens: I count
**17**, not the 18 `STATUS` states. `inamp-full-scale`, `sensor-full-scale`,
`key-scan-current`, `key-release-time`, `chain-connectors`, `key-pullup-qty`,
`dac-rail`, `pitch-compensation`, `panel-toggle-hole`, `loadswitch-timer`,
`loadswitch-gate-cap`, `loadswitch-fb-divider`, `cref-out-node`,
`riso-ref-topology`, `plate-thickness`, `opa2197-output-impedance`, `FB-IN`'s
`ferrite-bias-impedance`. **CONFIRMED WITH A CORRECTION** — off by one, and
the conclusion is untouched at either number.

---

## E1-9 — `C-GATE-LOADSW`, the documented procedure, green `@0576a95`

`[test]` In a pristine `0576a95` tree, following `CLAUDE.md` and
`repo-maintenance.md` exactly — edit the fragment, re-run the tool, run the
checker:

```
$ # hardware/module/umbilical-load-switch/bom.csv, C-GATE-LOADSW part field
$ #   '82nF C0G/NP0 or film, 50V'  ->  '100nF C0G/NP0 or film, 50V'
$ python3 tools/merge-bom.py
bom.csv: wrote 139 rows from 26 fragments | 0 problems
$ python3 tools/check-staleness.py
PASS no live stale values | corpus 123 files, 23 circuits, 37 figures / 218 patterns | 5 unresolved (tracked) | 233 restated-not-cited (advisory)
```

**CONFIRMED, byte-identical to the healthy baseline line.** Meanwhile
`[repo] config/figures.yaml` still says `value: "82 nF, ramp 49-197 ms
(98 ms typ)"` and the owner page still derives 49/98/197 ms from 82 nF. This
is the docstring's own scenario, one directory over, and it reproduces on the
first part anyone tries.

---

## E1-10 — and when you *do* wire a figure up, it fails on correct data

`[test]` Calling `check_bom_figures()` with a synthetic spec — the refdes
moved into `value`, which is the only change that gives the check anything to
do — and the BOM left exactly as it is at HEAD and **correct**:

| figure | result |
|---|---|
| `loadswitch-gate-cap` + `C-GATE-LOADSW` | **false fail** — compares `197` (the slow-corner ramp) against `82nF C0G/NP0 or film, 50V` |
| `key-pullup-qty` + `R-KEY-PU` | **false fail** — `24` against `2k2 1%` |
| `key-scan-current` + `R-KEY-PU` | **false fail** — `1.43` against `2k2 1%` |
| `loadswitch-fb-divider` + `R-FB-HI`/`R-FB-LO` | **false fail** — `35.7` against `5.11k 1% thin film` |
| `panel-toggle-hole` + `SW-POWER` | **false fail** — `6.5` against `NKK M2011SD4G01` |
| `pitch-compensation` + `C-FB-PITCH` | passes |

**CONFIRMED** — D2 §1.4 is right, and five of the six I tried fail on a
correct register against a correct BOM. `primary = max(nums, key=len)` picks
the longest *digit string*, which is a coincidence of notation, not the
figure's value. `CLAUDE.md`'s rule applies verbatim: the cheapest fix for a
check that fires on a correct sentence is to make the sentence wrong.

---

## E1-11 — `--invert` on a healthy tree `@0576a95`

`[test]` in a clone checked out at `0576a95`:

```
$ python3 tools/rewrite-paths.py --invert --baseline 8bb7366
  …
  tools/merge-bom.py: not present at baseline 8bb7366
invert: 55 file(s) byte-identical under inversion, 2 hand-edited/skipped, 112 MISMATCH
```

**CONFIRMED** — the line is byte-identical to D4.21's. `[test]` Of the 112,
**92** are `not present at baseline`, and classifying each against the path
map's own `kind` column gives `Counter({'created': 92})` — **92 of 92 are map-
`created` rows**, exactly as D4 says. `load_map()` filters out `unmoved` and
`unmoved-history` and nothing else, so `created` rows and files created since
the baseline are demanded of a revision that predates them.

The proof `rewrite-paths.py`'s own docstring calls *"THE PROOF … what makes
'Phase A changed no content' a decidable proposition rather than a promise"*
had stopped deciding anything, and any operator running it would have read
112 red lines and stopped believing the tool rather than the tree.

`[test]` D4's predicted repair is also confirmed: at `566159e` the same
command now prints `92 created after the baseline (outside the proof's
domain), 20 MISMATCH`, which is D4's predicted 112 → 20.

---

## E1-12 — ADR 0004's DAC threshold: the number is right and the sentence is wrong

`[datasheet]` `datasheets/analog/DAC8568CIPW.pdf` (SBAS430E), **p.4**,
electrical characteristics table, extracted text verbatim:

```
VINL    2.7V ≤AVDD ≤5.5V     0.3 × AVDD
VINH    2.7V ≤AVDD < 4.5V    0.7 × AVDD
        4.5V ≤AVDD ≤5.5V     0.625 × AVDD
```

**The row split is real and the ADR picked the right row** — `dac-rail` is
5.21 V, which is in the second band. The *previous* `0.7 × AVDD — 3.65 V` was
the wrong row. That half of the fix is correct.

`[calc]` `0.625 × 5.21 = 3.25625 V` → the ADR's stated **3.26 V** is correct
to two decimals. `[calc]` `3.3 − 3.25625 = 0.04375 V` = **43.75 mV**.

`[repo] docs/decisions/0004-cv-interface-module.md:218-219`, in the
correction's own annotation: *"The conclusion survives — **3.3 V CMOS still
cannot drive it** — but the number carrying the argument was 0.39 V wrong"*.

**CONFIRMED: at nominal that sentence is false.** A 3.3 V logic high exceeds
`V_INH` min by 44 mV. D12's body says 44 mV (right); D12's own summary table
at `:21` says 40 mV (a rounding of the same thing, and looser than its
evidence — the same shape as E1-2).

Two things I would add before anyone "fixes" the ADR by deleting the
parenthetical:

- **`V_INH` is a min over −40…+125 °C with no typical** `[datasheet]` p.4, so
  44 mV of nominal margin is not a margin you would design to. The
  *engineering* decision to keep the AHCT buffer is untouched, and the ADR's
  other stated margin improves: `[calc]` an AHCT output at 4.6 V now clears
  3.26 V by **1.34 V** where it cleared 3.65 V by 0.95 V.
- **The rail is not a point value.** `[repo] config/figures.yaml`,
  `dac-rail.floor`: *"E7 selects `R-REG-SET` on the bench across a 0.66 V
  worst-case spread"*. `[calc]` the parenthetical becomes true again at
  AVDD ≥ 5.28 V (`3.3 / 0.625`). So the honest replacement is a band, not a
  different flat assertion.

`[calc]` The register's own derivation checks out:
`1.25 × (1 + 475/150) = 5.2083 V` → `5.21 V`.

---

## E1-13 — the plate gap, from the two banked artefacts

`[datasheet]` `datasheets/mechanical/GATERON-KS-33-VENDOR-SPEC-DRAWING.pdf`
sheet 6, elevation view, rendered at 600 dpi and read directly. The dimension
chain is exactly as D14 tabulates it: **5.75±0.05**, **2.50±0.05**, **2.60**,
**1.20±0.05**, **14.00±0.05**, 13.75, ⌀1.00. The callouts are vector art with
no text layer, so this has to be rendered — `get_text()` returns none of them,
which is worth writing down for the next reader.

`[datasheet]` sheet 3 §8 *"Mounting Options"*, rendered at 400 dpi: 14.00
+0.05/−0.02 square cutout, ⌀5.25 centre, and an edge view carrying
**1.20 +0.01/−0.05** — the vendor's recommended **plate thickness**, which
independently corroborates the settled `plate-thickness` figure.

`[datasheet]` sheet 6, bottom-right, view titled **"PCB Layout"**: ⌀5.25
centre and **⌀3.00** holes at the 2.60/4.40 × 5.75/6.30 positions.
**D14's load-bearing premise is confirmed from the primary document** — the
vendor's own PCB pattern uses ⌀3.00 holes, which take the 2.00 mm blade root,
which only makes sense if the board seats against the housing bottom.

`[calc]` The arithmetic, re-derived:

```
plate-to-PCB gap, seated   = 2.50 − 1.20            = 1.30 mm
pin protrusion at d=3.20   = 5.10 − 3.20 − 1.6      = +0.30 mm
pin protrusion at d=3.50   = 5.10 − 3.50 − 1.6      =  0.00 mm
pin protrusion at d=3.60   = 5.10 − 3.60 − 1.6      = −0.10 mm   ← impossible
```

`[repo] hardware/bom.csv:59` confirms the 1.6 mm board (`PCB-CLUSTER`,
package `small, 1.6mm`). **CONFIRMED: the upper end of the published
3.2–3.6 mm window puts the pin tip 0.10 mm inside the board**, where "protrude
enough to solder" cannot be true.

`[repo] docs/decisions/0002-key-switches-and-mounting.md:181` does hold the
other answer, in the same batch: *"at 1.20 mm the plate consumes only 48 % of
the 2.50 mm through-section"*. `[calc]` 1.20/2.50 = 48.0 %; the unconsumed
52 % is 1.30 mm. **Two corpus documents, 1.30 mm against 2.0–2.4 mm, from the
same two vendor numbers** `[repo] docs/reference/ks33-geometry.md:108`,
`hardware/cluster/cluster-boards.md:153`.

`[step]` `datasheets/mechanical/GATERON-KS-33-3D.step`, parsed by collecting
every `CARTESIAN_POINT`'s z: the distinct z set is
`−5.7, −5.1, −3.0, −2.5, −2.469, −2.41, −2.207, −1.97, …` — **reproducing
D14's list exactly**, and `−3.2` is not in it. **CONFIRMED WITH A
CORRECTION**: `-3.2` *does* occur in the file, 19 times, but always as an **x**
coordinate (`CARTESIAN_POINT('',(-3.2,6.5,-2.5))`). `[test]` points with
z = −3.2: **0**. D14's finding stands; its sentence *"−3.2 is not a coordinate
in the file"* should read *"not a z coordinate"*, or the next reader who greps
will think D14 was wrong and stop reading.

---

## E1-14 — ADR 0014's lighting annotation

`[datasheet]` `datasheets/led/WS2815.pdf` **p.3**, Electrical Characteristics:
`Quiescent Current 2.1mA` and `RGB Channel Constant Current 15mA`. **Both
citations verified.**

**The "exactly".** `[repo] docs/decisions/0014-lighting.md:141-143`: *"the
same page's Quiescent Current **2.1 mA** reproduces ADR 0005's 123 mA figure
**exactly**"*. `[calc]` 2.1 mA × 50 LEDs = **105 mA**. `[repo]
docs/decisions/0005-power-architecture.md:158` states **123 mA**. `[calc]`
105/123 = 0.854, i.e. 14.6 % low; 123/50 = 2.46 mA/LED, and **no integer LED
count reproduces 123 from 2.1** (123/2.1 = 58.57). **CONFIRMED** — the
annotation's own corroborating sentence uses arithmetic that was never done.

**The clamp.** `[repo] 0014:132` gives the 60/m single-hue-40 % cell as
`0.13 A`; `[calc]` 0.13 × 12 = 1.56 W, which reproduces the `~1.5 W`
"realistic use" row at `:173` — so the identification is certain. At the
datasheet's 15 mA per channel, single hue full is `[calc]` 50 × 15 mA =
0.75 A, and 40 % of that is **0.30 A = 3.60 W**. Against the
`~3 W` clamp at `:193`: `[calc]` 3 / 3.6 = **0.83×**.

**CONFIRMED.** The clamp is *below* realistic use, not twice it, and it would
engage during ordinary single-hue breath tracking — the one behaviour the ADR
designed it not to have. D13's derived inversions check out too: `[calc]`
3/27 = 11 % of full white (not a quarter), 250 mA/0.75 A = 33 % (not ~75 %).

Worth stating plainly: **the annotation is right about the 2.23× and honest
about leaving the table as drawn**; what it got wrong is the one sentence it
offered as corroboration and the clamp it thought it was defending.

---

## E1-15 — `unplaced.csv`: fifteen of eighteen, not fourteen

`[test] git show 0e68f25 -- hardware/unplaced.csv` removes 16 rows;
`04b5208` removes 2 more. The eighteen are `U-DAC`, `R-PRECISION`,
`J-UMBILICAL`, `U-DIFFRX`, `U-LVL-MOD`, `D-REVPOL`, `U-REG-DAC`, `R-REG-SET`,
`C-REG-ADJ`, `FB-IN`, `R-GAIN-INAMP`, `R-SER-BREATH`, `C-FILT-BREATH`,
`C-BULK-RAIL`, `C-TIMER-LOADSW`, `C-GATE-LOADSW`, `J-CV`, `D-CLAMP-BREATH`.

`unplaced.csv` is defined as the rows **no schematic page names**, so the test
is: does the refdes string occur in any `.md` under `hardware/`?

`[test]` It does for **three**: `U-LVL-MOD` (`digital-and-supervision.md`,
`notes.md`), `R-SER-BREATH` (`breath-sense-link.md`,
`breath-receive-stage.md`, `carrier.md`), `D-CLAMP-BREATH`
(`breath-receive-stage.md` — and see E1-16 for what it says there). The other
**fifteen appear only in `bom.csv` files**, never on a page.

**CONFIRMED WITH A CORRECTION: 15 of 18, not 14 of 18** — the claim
understates its own case. Several of the fifteen *are* drawn, under a part
name rather than a refdes (`DAC8568C`, `LT5400`, `INA828`, `1N5817`,
`LM317LZ`), which is exactly D9's point and exactly the distinction
`pcb-pipeline.md` draws between *drawn*, *named* and *placed*. The batch
answered "drawn". `unplaced.csv` asks "named".

---

## E1-16 — the corrupted drawing and the wrong label

`[test] git show 04b5208 -- hardware/module/breath-receive-stage/breath-receive-stage.md`
— the whole edit is two lines:

```
-                              BAV99 to ±12 V, both legs  ◄──────────┼─┤
+                              [D-CLAMP-BREATH] BAV99 to ±12 V, both legs  ◄──────────┼─┤
-                                   [BAV99]── ±12 V
+                                   [D-CLAMP-BREATH BAV99]── ±12 V
```

**The corruption.** `[calc]` The inserted text `[D-CLAMP-BREATH] ` is 17
characters and nothing to its right was re-aligned. Column positions of the
vertical rails (0-based), measured off the file:

| line | length | rail columns |
|---|---|---|
| 66 | 71 | 68, 70 |
| **67** | **88** | **85, 87** |
| 68 | 71 | 68, 70 |

`[calc]` 88 − 17 = 71, and 85 − 17 = 68, 87 − 17 = 70 — **before the edit the
line was aligned with its neighbours to the column**. **CONFIRMED exactly:
68/70 → 85/87.** In the rendered drawing the ±12 V clamp's connection now
points 17 columns into empty space.

**The wrong label.** `[repo] :110` now reads `[D-CLAMP-BREATH BAV99]── ±12 V`
at the **BREATH output jack**. `[test]` The identical structure at every other
output jack on this module is labelled `D-JACK-CLAMP`:
`mod-channels.md:58`, `pitch-stage.md:48`, `breath-output-stage.md:84`, all
spelling `[D-JACK-CLAMP BAV99]── ±12 V`. `[repo] hardware/module/bom.csv:4`
— `D-JACK-CLAMP`, BAV99, *"Clamp diodes on the DRIVER side of R-OUT-PROT"*,
qty 6. And `D-CLAMP-BREATH`'s own row `[repo]
hardware/module/breath-receive-stage/bom.csv:7` is qty **2**, *"Clamp diodes
on the BREATH and AGND legs **at the in-amp inputs**"* — both of which are
already accounted for by line 67's *"both legs"*.

**CONFIRMED: `:110` names the wrong part**, and the BOM note the same commit
wrote (*"It was drawn on breath-receive-stage.md TWICE and the drawing never
wrote the refdes"*) records the wrong claim — the second instance was never
this part. D9-1/D9-2 and D19 are both right, and D19's conservation check
earning its keep by catching a drawing corruption is exactly what a
byte-level conservation proof is for.

---

## E1-17 — BOM mechanics, a third independent proof `@0576a95`

`[test]` Reading `hardware/bom.csv` as bytes and as CSV, without
`merge-bom.py`:

```
bytes: 131725 | CRLF: 140 | bare LF: 0
rows incl header: 140 | data rows: 139 | cols: 11
header: ['ref','category','part','manufacturer','description','package','qty','status','source','adr','notes']
duplicate refdes: []      units (qty): 390
```

**CONFIRMED to the byte.** `[calc]` 25 fragments carry 107 data rows;
107 + 32 in `unplaced.csv` = 139 — self-consistent with the master, and
confirming D10's fragment counts against `pcb-pipeline.md`'s stale
23-fragments/104-rows block.

---

## E1-18 — datasheets `@0576a95`

`[test] python3 tools/verify-datasheets.py` → `78 verified, 23 recorded as
blocked or not-fetched, 0 problems`. `CLAUDE.md` §3's precondition holds.

`[test]` Manifest ↔ disk, computed both directions: **76 distinct OK file
paths, 76 files on disk, zero missing either way.** **CONFIRMED.** One wording
correction: there are **78** `OK`/`OK-SUBSTITUTE` rows over those 76 files —
two parts deliberately share a file (the `DAC8568CIPW` / `DAC8568ICPW`
transposition, documented in the row itself). "76 rows against 76 files" is
"76 files against 76 files".

`[test]` Corpus citations of `datasheets/<dir>/<file>`: 306 occurrences, 22
of which do not resolve — and **all 22 are the `old` column of
`docs/reference/path-map-2026-09-21.csv`**, which is exactly what that column
is for. **Zero genuinely dangling citations: CONFIRMED.** (My raw count is not
D11's 141; that is a scope difference — D11 evidently counted a narrower file
set or distinct citations — and the substance is unaffected.)

`[test] [datasheet]` `datasheets/discrete-and-power/LT1641.pdf`, 12 pages:
`LT1641` **51** hits, `LT4256` **0**. **CONFIRMED exactly.** The
mislabelled-mirror trap is clear.

---

## E1-19 — the duplicate YAML key, and how independent the agreement is

`[test]` A duplicate-key scan of `config/figures.yaml` reports exactly one:
`panel-height-budget` declares `false_positive_note` at **:408** and **:423**.
`[test] yaml.safe_load` returns the **:423** string; the **:408** note — the
one recording that `panel.md:20` and `0004:736` legitimately *narrate* the
superseded numbers — is silently discarded and cannot protect anything.
**CONFIRMED, including "the only duplicate key in the file".**

**Is the D12/D20 agreement real?** `STATUS` presents it as the method earning
itself. **Partly.** D20 landed first (`143d4b4`); D12 landed at `7a1aa1f`.
D12 says `[repo] D12:476` *"one register defect I hit while checking the
sibling claim about `97 mm`"* — so D12 was **routed to this register entry by
a brief**, but was **not** told about the duplicate key; it found it while
looking at something else in the same entry. So: two agents found the same
defect by two routes, with the co-location arranged by the orchestrator. That
is meaningfully weaker than "two agents who could not see each other converged
from nothing", and meaningfully stronger than contamination. Worth one
sentence of hedging in `STATUS`, not a retraction.

---

## E1-20 — the three self-exempting patterns `@0576a95`

`[test]` Testing every one of the 218 registered `forbidden` strings against
`REFUTATION` / `REFUTATION_SHOUT`:

```
sensor-full-scale        '0.2 → 4.8 V'        (contains →)
loadswitch-fb-divider    'VALUES NOT SET'     (contains NOT)
diode-split-rationale    '75 mV → LM317'      (contains →)
```

**Exactly three: CONFIRMED.** Each carries its own exemption inside itself, so
it can never fire no matter what the corpus says, and reads in every report
identically to a pattern that matches nothing.

`[test]` The other dead-pattern class is now clean: **zero** patterns contain
a newline. The `spi-series-r` `"220 Ohm with\n~200 pF"` case named in
`check_patterns`'s docstring and in `CLAUDE.md` has been split.

---

## E1-21 — D10 was right to reverse the `360 mA` claim

`[repo] config/figures.yaml`: `umbilical-current` = **359 mA**. `[test]`
`360 mA` / `360mA` occurs in 6 corpus files. Reading each occurrence:

```
umbilical-load-switch.md:57   "draws ~360 mA while it is starting"
umbilical-load-switch.md:222  "at 940 mA less 360 mA load"
umbilical-load-switch.md:325  "irrelevant at 360 mA"
power-entry.md:7              "360 mA of someone else's load"
power-entry.md:170            "the ~360 mA umbilical return"
0004:627 / :633               "~360 mA of instrument current" / "360 mA develops an IR drop"
```

Every one is a rounding in a sentence that is **correct as written**. A
`forbidden` pattern on `360 mA` would fire on six true sentences, and its
cheapest fix would be to make them wrong. **D10's reversal is CONFIRMED and
was the right call** — it is the one case in this wave where an agent
overturned a sibling rather than confirming it, and it overturned it
correctly.

---

## What a merge decision should take from this round

1. **The wave's mechanical findings hold.** Nineteen of twenty-five
   re-verified outright, five off by one unit or one tenth of a point, one
   refuted — and the refuted one is a claim about *who measured*, not about
   the corpus. Nothing in the wave's four merge blockers weakened under
   re-measurement; two of them (E1-5, E1-11) got sharper.
2. **The instrument is being repaired mid-review, and the repaired instrument
   fails.** `566159e` landed during this round and the checker now reports 8
   live stale values — precisely the 8 my cold reading predicted. That is the
   tooling working. It is also a commit hook that currently blocks, and a
   round-2 premise ("the corpus is frozen") that no longer holds.
3. **Fix order 2 needs re-scoping.** Dropping the four markers takes the
   exempt surface to ~42.6 %, not back to 33.9 %. The `REFUTATION_WINDOW`, not
   the vocabulary, is what moved it (E1-6). Anyone who fixes the vocabulary
   and re-measures will find the number barely moved and may conclude the
   diagnosis was wrong. It was not; it was incomplete.
4. **`33.9 %` is now quoted in the tool's own source as measured by "three
   cold slices". It was measured by one.** Whatever else this round does, that
   sentence should be corrected before it is cited again — it is the project's
   named failure mode reproducing inside the fix for the project's named
   failure mode.
5. **Report-level roundings drifted twice in the same direction** (D1's "6 of
   24" for 5, D12's summary "40 mV" for 44) — in both cases the report's own
   evidence block was correct and the sentence summarising it was not. That is
   the same defect shape the whole corpus is being audited for, occurring in
   the audit.
