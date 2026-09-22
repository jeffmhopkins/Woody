# D2 — the two checks that did not exist before `0e68f25`

Slice: `check_bom_figures()` and `check_restated()`, both added in
`0e68f25` "Fix the tooling, and the defects the fixed tooling then found"
(`tools/check-staleness.py`, +492 / −54) `[repo] git show 0e68f25 --stat`.

Report only. Nothing in the corpus was changed. Every reproduction below was
run against `git archive HEAD | tar -x` in a scratchpad, never in the tree.

Baseline for all tests `[test]`:

```
$ python3 tools/check-staleness.py
PASS no live stale values | corpus 123 files, 23 circuits, 37 figures / 218 patterns
 | 5 unresolved (tracked) | 233 restated-not-cited (advisory)
```

---

## Headline

**`check_bom_figures()` reaches one figure out of thirty-seven.** It is
correct on that one. The documented failure it was written to close is
still open on the other 138 BOM rows, and reproduces green today. Worse,
every obvious way to extend its coverage — naming the part in the figure's
value — produces *false* failures on a corpus that is right, which is the
one outcome `CLAUDE.md` names as worse than no check at all.

**`check_restated()` is about 50 % signal at every threshold I measured**,
and its biggest blind spots are not in the threshold but in two places
nobody would look: a numeric-token suppression that silently hides 93 real
candidates, and a unit list that cannot see a resistor written the way this
repository's BOM writes one.

---

# Part 1 — `check_bom_figures()`

`tools/check-staleness.py:686` `[repo]`.

## 1.1 It works. On one figure.

`REFDES_IN_VALUE` (`:655`) only matches inside `fig["value"]` `[repo] :715`.
Measured over the register `[test]`:

| | count |
|---|---|
| figures in `config/figures.yaml` | 37 |
| `status: settled` (the only ones the check considers, `:708`) | 32 |
| settled figures with a numeric token of length ≥ 2 | 29 |
| figures whose **`value`** contains a refdes-shaped token | **1** |
| …that resolves to a `hardware/bom.csv` row | **1** (`spi-series-r`) |
| figures naming a real BOM refdes **anywhere in the entry** | **20** |

So of the 20 figures that are *about* a specific BOM part, the check reads
1. The other 19 name their part in `derivation`, `note`, `owner` or
`false_positive_note` — fields `check_bom_figures` never opens.

Regression test that the one covered case does work `[test]`:

```
$ # documented procedure: edit the fragment, re-run merge-bom.py, run the checker
$ sed R-SPI-SER part 100R 1% -> 220R 1% in hardware/interfaces/spi-link/bom.csv
$ python3 tools/merge-bom.py && python3 tools/check-staleness.py
FAIL ... + 1 register-vs-bom + ...
  [spi-series-r] says '100 ohm, R-SPI-SER, qty 3', but the BOM part field for
  R-SPI-SER is '220R 1%' and states no 100 - the register and the part it names
  disagree
```

That is exactly the reproduction the docstring claims, and it holds.

## 1.2 The same defect on a different part is still green

`loadswitch-gate-cap` is `82 nF` `[repo] config/figures.yaml`; its part is
`C-GATE-LOADSW`, `82nF C0G/NP0 or film, 50V` `[repo]
hardware/module/umbilical-load-switch/bom.csv:11`. The figure does not spell
the refdes in its `value`, so `[test]`:

```
$ sed C-GATE-LOADSW part 82nF... -> 100nF... ; python3 tools/merge-bom.py
$ python3 tools/check-staleness.py
PASS no live stale values | corpus 123 files, ... | 233 restated-not-cited (advisory)
```

Byte-identical to the healthy baseline. The register still says 82 nF, the
owner page still derives 49/98/197 ms from 82 nF, and the part is 100 nF.
This is the docstring's own scenario, one directory over.

## 1.3 The `part` field only — what that costs

`part = row[BOM_HDR.index("part")]` `[repo] :724`. The docstring's reason is
sound and I confirm it: searching the whole row is satisfied by prose *about*
the value.

But the register does not only carry part values.

- **`qty`.** `spi-series-r`'s value is literally `"100 ohm, R-SPI-SER,
  qty 3"`. Changing the BOM qty is invisible twice over — the `qty` column is
  never read, and `3` is dropped anyway by the `len(t) >= 2` filter at
  `:712`. `[test]`:

  ```
  $ set R-SPI-SER qty 3 -> 4 in the fragment; merge-bom.py; check-staleness.py
  PASS no live stale values | ... | 233 restated-not-cited (advisory)
  ```

  The figure that this check exists for, stating a qty in its own value
  string, and the qty can be changed under it silently.

- **`package`.** `panel-toggle-hole` is `6.5 mm diameter with a 5.8 mm
  D-flat`; `SW-POWER`'s package cell is `THROUGH-HOLE, M6x0.75 bushing
  mount, 6.5mm panel hole with a 5.8mm D-flat` `[repo] hardware/bom.csv`.
  Same two numbers, in the `package` column, unchecked.

- **`description`.** `chain-connectors` is `12`; `J-CHAIN` is
  `2x6 2.54mm IDC boxed header, keyed`, qty 8 — the pin count lives in
  `part`/`description`, and nothing relates the two.

- **`status`.** Two rows are deliberately `TBD`/blocked per `CLAUDE.md`.
  A figure marked `settled` against a row marked `TBD` is not detected.

These are all real, but they are second-order next to §1.1 — the check
misses 36 of 37 figures before the choice of column ever matters.

## 1.4 `primary = max(nums, key=len)` is not the value

`:713`. The longest numeric *token* is not the figure's value; it is a
coincidence of digit count. Constructed from a real register entry, no
invention needed:

`loadswitch-gate-cap` = `"82 nF, ramp 49-197 ms (98 ms typ)"`. Tokens of
length ≥ 2 are `82, 49, 197, 98`; `max(key=len)` returns **`197`** — the
ramp time at the slow corner `[calc] len("197")=3 > len("82")=2`.

Add the refdes the way a maintainer would to get this figure covered, and
leave the BOM **correct** at 82 nF `[test]`:

```
  [loadswitch-gate-cap] says '82 nF, C-GATE-LOADSW, ramp 49-197 ms (98 ms typ)',
  but the BOM part field for C-GATE-LOADSW is '82nF C0G/NP0 or film, 50V' and
  states no 197 - the register and the part it names disagree
```

Register right, BOM right, check fails. `CLAUDE.md`: *"A pattern that fires
on a correct sentence is worse than no pattern, because its cheapest fix is
to make the sentence wrong."* The cheapest fix here is to delete the ramp
numbers from the figure.

This is not one bad entry. I took the seven settled figures that name a BOM
refdes somewhere in their entry, moved the refdes into `value` — the only
change that would give the check anything to do — and left the BOM exactly
as it is at HEAD `[test]`, calling `check_bom_figures()` directly with a
synthetic spec so no other check's noise is mixed in:

| figure (refdes moved into `value`, BOM unchanged and correct) | result |
|---|---|
| `key-pullup-qty` `24` + `R-KEY-PU` | **false fail** — compares `24` against `2k2 1%` |
| `key-scan-current` + `R-KEY-PU` | **false fail** — compares `1.43` against `2k2 1%` |
| `loadswitch-fb-divider` + `R-FB-HI` **and** `R-FB-LO` | **false fail** — compares `35.7` against `5.11k 1% thin film` |
| `riso-ref-topology` + its four parts | **3 false fails** — compares `37.4` against `10k`, `100R`, `1nF` |
| `loadswitch-gate-cap` + `C-GATE-LOADSW` | **false fail** (§1.4) |
| `plate-thickness` + `PLATE-TOP`/`PLATE-THUMB` | clean |
| `loadswitch-timer` + `C-TIMER-LOADSW` | clean |

**Five of seven false-fail on a correct corpus.** Two structural causes:

1. **One `primary` is compared against *every* refdes in the value.** A
   figure that names two parts (`loadswitch-fb-divider`, `riso-ref-topology`)
   cannot pass — the check has no notion of which number belongs to which
   refdes. Four of the seven trials fail for this reason alone.
2. **A count is not a part value.** `key-pullup-qty` is `24` and
   `R-KEY-PU` is `2k2`; the numbers are unrelated by construction.

## 1.5 The spelling trap, reproduced inside the new check

`CLAUDE.md` §2 trap 1: *"Write the pattern in the spelling of the file it
must match."* `anchored_in` (`:643`) is a literal match with digit guards, so
`[test]`:

- register `37.4 ohm` vs BOM `37.4R 1%` → **clean** (same digits).
- register `2.2 kohm` vs BOM `2k2 1%` → **false fail**: *"states no 2.2"*.

`2k2`, `4k7`, `1R5` are ordinary E-series spellings and the BOM already uses
`2k2` `[repo] hardware/cluster/key-switch-network/bom.csv:3`. Any figure
tracking a resistance in prose spelling against a row in R-notation fails on
a corpus that is right.

## 1.6 Does it fire on anything it should not *today*?

No. 0 problems at HEAD `[test]`. Two things I checked that could have gone
wrong and do not:

- `REFDES_IN_VALUE` has no `NOT_REFDES` filter (unlike `check_refdes`
  `:355`), so `SOIC-8`, `MCP3202-CI`, `SHA-256` all match its shape. They are
  harmless because `bom_rows.get(ref)` returns `None` and the loop skips
  `:718`. It is silent-by-luck, not by design: the day a BOM refdes collides
  with a package name, the failure is a false positive.
- Refdes in `hardware/unplaced.csv` but not `bom.csv` would be skipped
  silently. Not reachable today — all 32 `unplaced.csv` refs are also rows in
  `bom.csv` `[test]`. Worth keeping true.

## 1.7 The fail-open: coverage is invisible

This is the finding I would act on first, and it is the seventh fail-open the
wave README asks for.

Everything else in this file carries a coverage number on the output line
*on purpose* — `npat`, the corpus file count, the circuit count — because,
in the file's own words, *"a run with no coverage used to print the same PASS
line as a healthy one"* `[repo] :1163`. `check_bom_figures` reports no
coverage at all. It reached 1 figure at HEAD; there is no way to know that
from any output.

So rewording one figure — no change of meaning, no change of value — takes
coverage from 1 to 0, permanently and silently `[test]`:

```
$ # value: "100 ohm, R-SPI-SER, qty 3"  ->  "100 ohm on SCLK, MOSI and CS, qty 3"
$ # and, separately, R-SPI-SER part 100R 1% -> 220R 1% via the fragment + merge-bom.py
$ python3 tools/check-staleness.py
PASS no live stale values | corpus 123 files, 23 circuits, 37 figures / 218 patterns
 | 5 unresolved (tracked) | 233 restated-not-cited (advisory)
$ grep -c "REGISTER vs BOM" .staleness/report.txt
0
```

Byte-identical to the healthy baseline, with the check's own named defect
(`R-SPI-SER` at 220 Ω, the value its derivation exists to reject) live in the
tree. Nothing else caught it either — the owner page still says `100 ohm`, so
`check_owners` is satisfied, and 220R is not a `forbidden` pattern for this
figure.

**What would settle it:** a coverage counter of the form
`register-vs-bom: N figures × M refdes compared` on the summary line, and an
advisory list of settled figures that name a refdes in any field but not in
`value` (19 today). Both are measurements, not judgements.

## 1.8 Is the hole large or small?

Large, and the report's arithmetic understates it. 1 of 37 figures is 2.7 %
of the register; 1 of 139 BOM rows is 0.7 % of the BOM. The check's docstring
describes closing "the hole this closes is the whole project". It closes
`R-SPI-SER`.

It is not useless — the covered case is the one that was actually
demonstrated, and a check that is right on 1 case is better than a check that
is wrong on 20. But extending it is blocked, not merely unfinished: §1.4 and
§1.5 mean the next person who tries to grow coverage gets five false failures
and the cheapest fix for each is to damage a correct sentence.

---

# Part 2 — `check_restated()`

`tools/check-staleness.py:740`, advisory, reports **233** `[test]`.

## 2.1 Sample: ~50 % real, and it does not improve

I classified 40 entries — a systematic sample of 36 taken at even intervals
across the sorted 233 (ranks 1, 8, 14, 21, 28, 34, 41, 47, 54, 61, 67, 74,
81, 87, 94, 100, 107, 114, 120, 127, 134, 140, 147, 153, 160, 167, 173, 180,
187, 193, 200, 206, 213, 220, 226, 233), plus `1.25 mm`, `20 K`, `99 ms` and
`6.02 dB`. Each was classified from its actual occurrences in the corpus, not
from the key `[test]` — a script printed the ±100 characters around the first
hit in each file.

| class | n | examples |
|---|---|---|
| **real** — one quantity, genuinely restated, could move | **21** | `14.0 mm` plate cutout (ROADMAP, `key-layout.yaml`, ADR 0002, `ks33-geometry.md`); `0.99 V` 74HC165 `V_IL`; `20 ns` Cat5 round trip; `360 mm` display board run; `928 mA` clamp-legal worst case; `120 mV` 1N5817 `V_f` modulation; `20 K` interior rise (5 ADRs); `47.5 ms` hot-plug case; `11.36 V` worst-case delivered output |
| **collision** — one number, two or more unrelated quantities | 9 | `47 nF` is both `C-KEY` and `C-AA-ADC`; `31 mm` is the etherCON flange *and* ADR 0008's length slack; `40 %` is LED brightness *and* op-amp overshoot; `0.01 %` is LT5400 grade A *and* LM317 line regulation `%/V`; `1.0 A` is the current limit *and* a datasheet test point |
| **datasheet quote** — the number belongs to a banked document | 6 | `110.5 dB` REF5050 PSRR worst case; `1.2 ms` MCP3202 §6.2 sample hold; `1.8 MHz` `fCLK` max; `8.8 V` LT1641 UVLO (quoted *as the refutation* of 9.8 V) |
| **package / footprint** | 1 | `1.25 mm` — the `0805 (2.0 x 1.25mm)` cell, 17 files, rank 2 of 233 |
| **unit mis-parse** | 1 | `244 V` is really `244 V/s` (§2.3) |
| **refuted / deleted** — must *not* be tracked | 1 | `99 ms`, the watchdog timeout that no longer exists, narrated as rejected in three files |
| **mathematical invariant** | 1 | `6.02 dB` = 20·log₁₀2 `[calc]`; cannot move |

**21 / 40 = 53 % real.**

Two checks on that number:

- **The top of the list is no better.** I separately classified the 40
  entries the report actually prints (`restated[:40]`, `:1089`, i.e. the
  most-restated). ~20 real, 2 package (`1.25 mm`, `1.27 mm`), ~16 collisions
  (`20 mm`, `14 mm`, `22 mm`, `15 mm`, `30 %`, `60 %`, `17 %`, `0.9 mm`,
  `7.0 mm`, `0.25 mm`, `40 mm`, `66 mm`, `0.1 %`…). Same ~50 %.
- **Two independent samples, same fraction.** The systematic sample spans
  ranks 1–233; the printed list spans ranks 1–40. Neither is better than a
  coin flip.

## 2.2 Three findings the advisory has already surfaced and nobody acted on

Flagging these for other slices; each is a claim, not a verdict.

- **`360 mA` in 6 files against a register that says `359 mA`.**
  `umbilical-current` is `359 mA`, derivation `226 mA × 5 V / (0.9 × 11.4 V)
  + 248 mA = 358.1 mA` `[repo] config/figures.yaml`. Six corpus files state
  `~360 mA` or `360 mA` for the same quantity `[repo]
  hardware/module/umbilical-load-switch/umbilical-load-switch.md:57,62,325;
  hardware/module/power-entry/power-entry.md:7,170;
  docs/decisions/0004-cv-interface-module.md:627,633`. Either that is an
  accepted rounding — in which case rule 1 says cite the figure, not a
  rounded copy — or the figure moved from 360 to 359 and six statements did
  not follow. **What would settle it:** git-blame on those six lines against
  the commit that set `359 mA`.
- **`0.265 V` in 6 files.** The sensor pedestal, stated in
  `sensor-full-scale`'s **`derivation`** — *"The PEDESTAL IS 0.265 V, not
  0.200 V"* — and restated numerically in ADR 0003, `breath-adc.md`,
  `breath-output-stage.md` and three BOM copies. It has a rejected
  predecessor with 11 `forbidden` patterns against it (`0.200 V at rest`, `|
  0.200 V |`, …). A value that was wrong once, is now restated six times, and
  is tracked only inside another figure's free text.
- **`120 mV`**, the 1N5817 `V_f` modulation, is one of the three figures
  `CLAUDE.md` §3 names as corrected off a banked datasheet ("an estimate at
  75–80 mV, 120 mV off the curve"). It is restated in three files and is not
  in the register `[repo] hardware/module/power-entry/power-entry.md` and two
  BOM copies.

## 2.3 The unit list — what it cannot see

`NUM_UNIT` `:733`. I ran a parallel regex over the same corpus with the units
it omits `[test]`:

| missing unit | values reaching ≥ 3 files | load-bearing example |
|---|---|---|
| `x` / `×` (ratios, multipliers) | 35 | `1.89x`, `2.7x`, `0.381x` margin ratios; `4 ×` gain |
| bare counts (`bits`, `keys`, `conductors`, `channels`) | 5 | `32 bits`, `8 bits` — and `marker-bits`, `free-bits`, `chain-conductors`, `chain-connectors` are **four tracked figures whose unit is not in the regex** |
| `cents` | 7 | `20 cents`, `0.42 cents`, `12.5 cents` — and `pitch-cents-budget` is a tracked **disputed** figure |
| `LSB` | 4 | `3.2 LSB`, `305 µV/LSB` |
| `in` / `in/sec` | 5 | `16 in/sec` is inside the tracked figure `ks33-contact-bounce` |
| `kPa` | 3 | `6 kPa` full scale (7 files), `5.2 kPa` thermal rise (5 files) — the entire breath input domain |
| `V/oct` | 1 | `1 V/oct` in 9 files — the defining constant of a CV instrument |
| `°`, `gf`, `/m`, `V/s` | 8 | spring force, LED density |
| **total additional ≥ 3-file entries** | **67** | |

And a whole spelling class, not a unit class: **resistance as the BOM writes
it.** `100R`, `10k`, `2k2`, `35.7k` match nothing in `NUM_UNIT`. Measured
`[test]`: **30 distinct R-notation tokens appear in ≥ 3 corpus files**, led by
`10k` in **29 files**, `1k` in 15, `100R` in 8, `220R` in 5, `35.7k` and
`5.11k` in 4 each. Resistors are the most-changed part class in this
repository — `R-SPI-SER` 100R↔220R is the check's own worked example — and in
their native spelling they are invisible to the advisory that exists to warn
that a value is about to become stale in five places at once.

This is `CLAUDE.md` §2 trap 1 (*"write the pattern in the spelling of the
file it must match"*) committed a second time, in the tool that enforces §2.

Two parse bugs in the same regex `[calc]`, both from the trailing guard
`(?![0-9A-Za-z])`, which permits `/`:

- `0.7665 V/kPa` is recorded as `0.7665 V`. So is `244 V/s` (rank 187) and
  `20 V/us`, and `3 ppm/°C` becomes `3 ppm`. A rate is filed as a level.
- `1 V/oct` is recorded as `1 V` — and `1` is in `known`, so it is then
  suppressed entirely (§2.4).

## 2.4 The suppression is the biggest hole, and it is invisible

`if n in known` `:777`, where `known` is built from **bare numeric tokens**
of every figure's `value` and `forbidden` (`:763`, `:765`) — not from
number+unit pairs.

Measured `[test]`:

```
>=3-file candidates before suppression : 379
suppressed because the NUMBER appears somewhere in the register : 146
reported : 233
```

Splitting those 146 by whether the register entry that suppressed them even
has the same unit:

```
unit matches a register entry (legitimate) : 53
unit does NOT match anything (spurious)    : 93
```

The 93 spurious suppressions, most-restated first `[test]`:

| value | files | suppressed by |
|---|---|---|
| `5 V` | **38** | `5` — from the umbilical pinmap `4,5 SCLK/MOSI` |
| `10 V` | 17 | `10` — from `50.50 mm (10HP)` |
| `10 kΩ` | 17 | `10` — same |
| `4 kHz` | 16 | `4` — from the pinmap `4,5 SCLK/MOSI` |
| `1 MHz` | 13 | `1` — from the pinmap `1,2 BREATH/AGND` |
| `100 Ω` | 12 | `100` — from `spi-series-r` `100 ohm` |
| `1 kΩ`, `2 kHz`, `10 mA`, `7 V`, `5 %`, `2 %` | 10–12 each | small integers in unrelated figure values |
| `250 µs` | 9 | `250` — from `loop-budget` `196-241 us of 250 us`, which spells the unit `us` while the corpus spells it `µs` |

`5 V` in **38 files** — the single most-restated quantity in the corpus — is
hidden from the advisory because the digit `5` occurs in a pin-map string.
`250 µs` is hidden by a same-figure, different-spelling match, which is the
`us`/`µs` half of trap 1 again.

The fix is one line — key `known` on `(n, u)` instead of `n` — but it takes
the advisory from 233 to roughly 326 `[calc] 233 + 93`, which bears directly
on §2.5.

## 2.5 Is 3 files the right threshold?

Volume `[test]`:

| threshold | entries |
|---|---|
| ≥ 3 | 233 |
| ≥ 4 | 128 |
| ≥ 5 | 73 |
| ≥ 6 | 39 |
| ≥ 8 | 17 |
| ≥ 10 | 10 |

**Raising it shortens the list without improving it.** The ≥ 6 band is
~50 % real by the same classification as the ≥ 3 sample (§2.1) — the top of
the list is where the package dimensions (`1.25 mm` 17 files, `1.27 mm` 9,
`1.6 mm` 8, `2.54 mm` 5) and the dimensional collisions (`20 mm`, `22 mm`,
`14 mm`, `15 mm`) concentrate, because a footprint really is written in
seventeen files. Precision does not vary with the threshold because the noise
is not thin-tailed; it is at the head.

I also tested the one structural correction that looked promising — collapsing
sources that are not independent. `hardware/bom.csv` is **generated** from the
per-circuit fragments, so any value in a fragment is automatically in two
files; and a circuit directory is a page plus its fragment plus `circuit.yaml`
plus `notes.md`, which is one source spelled up to four ways `[repo]
CLAUDE.md, "Hardware conventions"`. Collapsing both `[test]`:

```
raw >= 3 files                                      : 233
collapsing the generated master into its fragments  : 151
also collapsing each circuit directory to one source: 125
```

**46 % of the 233 reach three files only because one source is spelled in
several files by design.** But it does not help precision either: on my
40-entry sample, 20 survive the collapse and 9 of those are "real" — 45 %,
slightly *worse* than the 53 % before collapsing, because the copy-pasted
BOM-note class it removes contains real figures as well as datasheet quotes.

Nothing I measured moves this check off ~50 %.

## 2.6 Advisory or fatal?

**The case for fatal.** It is the only check here that looks at the
*condition* rather than the consequence, and the condition is the one
`CLAUDE.md` says the project's single failure mode grows from. The signal is
real: §2.2 lists three live rule-1 violations it has already surfaced,
including one (`360 mA` vs a tracked `359 mA`) that may be an outright
staleness defect sitting in six files. It found those the day it was switched
on, and in a month nobody will read entry 187 of an advisory.

**The case for advisory — which is the one I would keep.** Three measured
reasons, and they compound:

1. **~50 % precision, and no knob improves it.** Threshold does not (§2.5).
   Source-collapsing does not (§2.5). To make it fatal you would hand-write
   an exemption for roughly 117 entries before the first green build —
   package dimensions, datasheet quotes, coincidences, refuted values. For
   comparison, `check_refdes` is documented as unswitchable at 36 hits with
   ~14 false `[repo] :393`. This is six times the volume at worse precision.
2. **Every exemption is a new place for the project's own failure mode.**
   A hand-maintained allowlist of 117 numbers is a derived document. When one
   of those numbers moves, the allowlist does not follow — and it fails
   *open*, because a stale exemption suppresses a real finding silently.
   That is exactly the shape of the `forbidden`-list escapes in `CLAUDE.md`
   §2, on a list three times the size of the current `forbidden` corpus (218
   patterns).
3. **The fix queue is unbounded and the list is not.** 21 of my 40 are real,
   which scales to ~120 figures that "should be tracked" against a register
   of 37. Making it fatal makes the tree uncommittable until the register
   quadruples. The docstring's own reasoning applies (*"a check that cries
   wolf gets ignored or deleted"*) — and the deletion risk here is higher
   than for `check_refdes`, because this one blocks commits.

**What I would do instead, in order:**

1. Fix the two silent defects first — `(n, u)` suppression (§2.4) and the
   `V/s` / `V/kPa` / `ppm/°C` mis-parse (§2.3). Both make the *advisory
   itself* wrong, which is worse than noisy.
2. Add R-notation to the unit list (§2.3). `10k` in 29 files is the largest
   untracked restatement class in the corpus and it is not in the report at
   all.
3. Split the report into two bands, both advisory: values whose sources are
   independent after collapsing generation and co-location (125), and the
   rest. The first band is where a reader should spend time.
4. Print a count, not just the top 40. `233` is on the PASS line, which is
   right; 193 entries are never shown, which is worth saying out loud.
5. Revisit fatal only once the number is driven below ~30 and the residue is
   exempted by *class* (footprints, quoted datasheet values) rather than by
   hand-listing individual numbers.

---

# Summary of findings

| # | finding | severity |
|---|---|---|
| D2-1 | `check_bom_figures` reaches 1 of 37 figures / 1 of 139 BOM rows; the same defect on `C-GATE-LOADSW` reproduces green `[test]` | **high** |
| D2-2 | Coverage is unreported; rewording one figure takes it to 0 coverage with a byte-identical PASS line — the seventh fail-open `[test]` | **high** |
| D2-3 | `primary = max(nums, key=len)` picks the longest token, not the value; 5 of 7 coverage-extension trials false-fail on a correct corpus `[test]` | **high** — blocks the fix for D2-1 |
| D2-4 | One `primary` compared against every refdes: multi-part figures cannot pass | high |
| D2-5 | `2.2 kohm` vs BOM `2k2` false-fails — `CLAUDE.md` trap 1 inside the new check `[test]` | medium |
| D2-6 | `check_restated`'s `n in known` suppresses on bare digits: 93 spurious suppressions including `5 V` in 38 files `[test]` | **high** (silent) |
| D2-7 | `NUM_UNIT` cannot see R-notation; `10k` in 29 files invisible `[test]` | **high** |
| D2-8 | `NUM_UNIT` misses 67 further ≥3-file values (`cents`, `kPa`, `V/oct`, `LSB`, counts), including the units of 5 tracked figures `[test]` | medium |
| D2-9 | Trailing `/` accepted: `244 V/s`→`244 V`, `0.7665 V/kPa`→`0.7665 V`, `3 ppm/°C`→`3 ppm` `[calc]` | medium |
| D2-10 | 46 % of the 233 reach 3 files only via the generated master and co-located circuit files `[test]` | low (presentation) |
| D2-11 | `360 mA` in 6 files against tracked `359 mA`; `0.265 V` in 6 files tracked only inside another figure's `derivation`; `120 mV` untracked `[repo]` | **for other slices** |
| D2-12 | `qty` / `package` / `description` / `status` columns unread by `check_bom_figures` `[test]` | low, given D2-1 |

Not findings, checked and clean: `check_bom_figures` fires on nothing it
should not at HEAD; both checks are genuinely wired and `check_checks()`
would catch it if they were not (`:930` wraps by call, not by source text);
`unplaced.csv` refs are all present in `bom.csv`, so the `row is None` skip
is not currently a hole.
