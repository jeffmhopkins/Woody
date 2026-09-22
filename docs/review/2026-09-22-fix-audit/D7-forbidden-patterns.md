# D7 — the `forbidden` patterns added and removed on 2026-09-22

**Slice:** every `forbidden` pattern added or removed in
`git diff 0e68f25~1..HEAD -- config/figures.yaml`, whether each one fires on
the text it was written for, whether it fires on anything true, whether it is
the right *shape*, and whether the register's coverage got better or worse.

**Report only. Nothing in the corpus was changed.** The three `git worktree`
checkouts and all sandbox trees used below were made under the scratchpad and
pruned afterwards.

## Provenance conventions

`[repo] path:line` — read in the tree at HEAD unless a commit is named.
`[git]` — reconstructed from history. `[calc]` — arithmetic shown.
`[test]` — a command and its output, reproducible from the recipe in §8.

---

## 0. Summary

| # | Finding | Severity |
|---|---|---|
| **D7-1** | **13 of the 31 patterns added in `df22096` match the stale text they were written for, and the checker exempts every one of those matches.** The commit's own headline case — `-9.6V` in the `U-DIFFRX` BOM row, the escape `escape_note` was written to close — is one of them. Applying the HEAD register to the pre-fix tree reports **19** live hits and **none** of them comes from those 13 patterns. | **high** |
| **D7-2** | **The exemption window leaks across record boundaries.** A refutation word in the *next, unrelated* `bom.csv` row excuses a live forbidden value in this one. Demonstrated at HEAD: identical row, 1 stale alone, 0 stale with a neighbour added. This is the mechanism behind most of D7-1. | **high** |
| **D7-3** | **Three patterns contain a refutation marker inside themselves and can therefore never fire anywhere.** `sensor-full-scale` `"0.2 → 4.8 V"`, `diode-split-rationale` `"75 mV → LM317"`, `loadswitch-fb-divider` `"VALUES NOT SET"`. Injected verbatim into a clean corpus file, the checker prints `PASS`, exit 0. | **high** |
| **D7-4** | **The `ks33-contact-bounce` fix is incomplete and no pattern catches the survivor.** `ROADMAP.md:71` still asserts bounce and the hysteresis gap are both unpublished — contradicting `ROADMAP.md:118-121`, fifty lines below it, in the same file. | **high** |
| **D7-5** | **9 of the 36 added patterns match nothing at any commit**; 8 of those never existed anywhere in the corpus's git history. `breath-sensor-slope`'s entire list (3 of 3) and 4 of `ks33-contact-bounce`'s 5. | medium |
| **D7-6** | `breath-sensor-slope`'s `"0.5059 V/kPa"` forbids the arithmetically **correct** slope at 3.3 V — and the same entry's `note` gives the reason someone will write that sentence. A trap primed, not sprung. | medium |
| **D7-7** | Four added patterns are bare numerals (`"~93us"`, `"~125us"`, `"~5.7us"`, `"= 97mm"`) that currently match only correction prose and survive on the exemption. Cheapest fix on a future false positive is to make a true sentence wrong. | medium |
| **D7-8** | The `"12x to 300x"` removal was mechanically defensible but left a **known-wrong ratio live in two files** with nothing tracking it. `[calc]` the real range is 37× to 925×. | medium |
| **D7-9** | CSV-spelling gaps in three entries, including in the two figures *newly tracked on 2026-09-22* — the same trap `CLAUDE.md` §2 bullet 1 describes, repeated in the commit that cites it. | medium |
| **D7-10** | 182 of 218 patterns match nothing at HEAD. Most are legitimately spent, but at least 5 are dead against text deleted in `cfcdc6e` and 3 more are dead on a `u`/`µ` spelling. `check_patterns()` reports `0 dead-patterns` for all of them. | low |
| **D7-11** | **Coverage: `dac-rail` is the next `sensor-full-scale`.** 36 restatements across 17 files in two canonical spellings, two of them inside ASCII drawings. The nine-spellings benchmark is already exceeded. | medium |
| **D7-12** | The slice brief names four entries that lost patterns. The committed diff shows **three**. `ks33-contact-bounce`'s two removals happened before the commit and exist only in its `false_positive_note` — they are not auditable from git. | note |

**Verdict on the slice question.** Coverage got *better* in shape and *worse
in confidence*. Three genuine defects were closed (the hard-wrap pattern, one
true-sentence trap, one self-referential pattern). But **the batch's own
headline claim — "the eight forbidden-list escapes, fixed by grepping first" —
is not established**: the grep found the spellings, the patterns were written
correctly against them, and the exemption rule then swallowed 13 of them. The
escapes are closed in the *text*; they are not closed in the *checker*.

---

## 1. What actually changed

`[git]` computed by parsing `config/figures.yaml` at each of the four commits
that touch it in the range and differencing the `forbidden` sets.

| commit | subject | added | removed |
|---|---|---|---|
| `0e68f25` | Fix the tooling… | 1 | 3 |
| `df22096` | The eight forbidden-list escapes, fixed by grepping first | 31 | 0 |
| `04b5208` | The six items the agents could not reach… | 5 | 0 |

**Removed (3, all in `0e68f25`):**

- `key-pullup-qty` — `"Twenty-one sets"`
- `loadswitch-timer` — `"12x to 300x"`
- `spi-series-r` — `"220 Ω with\n~200 pF"`, replaced by `"220 Ω with"`

**Added (36):** 5 to `inamp-full-scale`, 7 to `sensor-full-scale`, 3 to the new
`breath-sensor-slope`, 4 to `key-release-time`, 4 to `key-press-time`, 2 to
`chain-conductors`, 2 to `panel-width`, 4 to `panel-height-budget`, 5 to the
new `ks33-contact-bounce`.

Two entries are new: `breath-sensor-slope` and `ks33-contact-bounce`. No entry
was deleted. Register total: 35 → 37 figures, 190 → 218 patterns.

### D7-12 — the brief's fourth removal does not exist in git

`[git]` No pattern was removed from `ks33-contact-bounce`: the entry did not
exist before `04b5208`, and `04b5208` adds it with five patterns and removes
none. The two removals the brief expects are described in the entry's own
`false_positive_note` `[repo] config/figures.yaml:643-655` — a bare `"20 ms"`
and `"Gateron does not publish"` — and they were taken out **before** the
commit, so there is no committed state in which they existed.

That is not a defect in the fix; it is a gap in what an auditor can check.
The note is the only record, and I could not independently verify either
removal was necessary. What I *can* verify is that the note's reasoning is
sound on the text it names: `[repo] docs/decisions/0002-key-switches-and-mounting.md:217`
does read "The actuation/reset hysteresis gap, which Gateron does not
publish", and that sentence is true — the reset point really is undimensioned
`[repo] docs/reference/ks33-geometry.md:220-225`.

---

## 2. The removals — the dangerous half

### 2.1 `key-pullup-qty` / `"Twenty-one sets"` — **removal correct, coverage thinned**

The register's reason `[repo] config/figures.yaml:305-310` is that the pattern
fired on a true sentence. Verified:

`[repo] docs/decisions/0001-mcu-and-board-partitioning.md:216-218`

> **Per switch position: 2.2 kΩ to 3V3, 100 Ω in series, 47 nF to ground** …
> Twenty-one sets across the four boards, so the three reserved spare-switch
> bits are covered too.

`[repo] hardware/cluster/key-switch-network/key-switch-network.md:28` — "§2 The
key network — **21 of these**, spread across four boards"; and line 24 —
"The reserved spare-switch positions carry the full network; the free bits
carry a pull-up only".

`[calc]` 21 full networks (18 keys + 3 reserved spare-switch positions) + 3
free bits that need a pull-up only = **24 pull-ups**. So "twenty-one sets" and
"twenty-four pull-ups" are both correct and describe different things. The
pattern was a trap. **Removing it was right.**

**What now catches the text it was meant to catch?** `"21 pull-ups"` survives,
and it is the only pattern on this figure. I reintroduced the old wrong
statement in three spellings in a sandbox `[test]`:

| reintroduced text | caught? |
|---|---|
| `Twenty-one pull-ups, one per input.` | **no** |
| `R-KEY-PU is 21 pull-ups.` | yes (`"21 pull-ups"`) |
| a BOM qty column reading `…,0805 (2.0 x 1.25mm),21,candidate,…` | **no** |

(`[test]` three sandboxes from `git archive HEAD`, one injection each:
`PASS` / `FAIL … 1 stale` / `PASS` on the stale count. The third run also
reports 2 generated-file problems, which are the expected consequence of
appending to `unplaced.csv` and unrelated to the staleness result.)

The third is the live risk: the figure's value is a **BOM quantity**, and
`R-KEY-PU` `[repo] hardware/bom.csv:35` carries it in a bare numeric column
where no pattern of any shape in this register would see a regression. See
D7-9.

### 2.2 `loadswitch-timer` / `"12x to 300x"` — **removal defensible, a wrong number left live**

The register's reason `[repo] config/figures.yaml:478-483` is that the string
occurs nowhere except inside the sentence recording the correction. That is
half true. The string **is** still in the corpus, twice:

`[repo] hardware/bom.csv:71` and `[repo] hardware/module/umbilical-load-switch/bom.csv:10`
(one defect, two copies, one edit site — the fragment generates the master):

> BLOCKING. 10nF was wrong by **12x to 300x** and gave a 0.16-4ms fault timer…

And the same entry's own `note` says the ratio is wrong:

> The '12x to 300x' ratio is itself wrong — the page's own equation gives 37x
> to 925x, and bom.csv repeats the bad ratio so cross-checking finds false
> agreement.

`[calc]` from the entry's own `derivation`, `t = C · 1.233 V / I`:
at 10 nF, `I = 3 µA` → 4.11 ms; at `I = 77 µA` → 0.160 ms. Against the 150 ms
target that is **36.5× to 937×** — the note's "37x to 925x" to two figures, and
nothing like 12× to 300×.

So: removing the pattern lost nothing the checker was ever going to *report*
(the row is exempted by its own `2026-09-21` markers either way — see D7-2),
but the corpus still states a wrong ratio in two files, the register knows it,
and after the removal **nothing at all tracks it**. The `note` is now the sole
custodian of a defect that used to have a pattern.

**Recommendation for STATUS:** this is a one-line text fix in the fragment
(`12x to 300x` → `37x to 925x`), not a pattern question. Filed here because
the removal is what made it invisible.

### 2.3 `spi-series-r` / `"220 Ω with\n~200 pF"` → `"220 Ω with"` — **correct, and verified**

This is the `CLAUDE.md` §2 hard-wrap trap, and the fix is right.

`[test]` the old pattern: `"\n" in bad` is true, so `check_patterns()` reports
it and `text.find()` can never match the line-joined stream. The new pattern
fires on its target:

`[repo] docs/decisions/0004-cv-interface-module.md:78` — `> "220 Ω with ~200 pF of cable is a 3.6 MHz corner"`,
matched, exempt by `refuted` in the sentence above it. That is a correction
reading next to the thing it corrects: exactly right.

The accompanying `false_positive_note` is also correct and worth keeping as a
model: `~200 pF` alone would fire on `[repo] docs/decisions/0003-breath-sensing-path.md:405`
("With ~200 pF of…"), which is the breath pair's cable capacitance and a
different quantity.

**Coverage change: strictly positive.** One pattern that could never fire was
replaced by one that fires on the same text.

---

## 3. Test 1 — does each added pattern fire on the text it was written for?

**Method** `[test]`. I replicated `check_figures()`'s matcher exactly (stripped
lines joined with one space; `str.find`; `REFUTATION`/`REFUTATION_SHOUT` over a
±300-char window of the joined stream) and ran every added pattern against
`git worktree` checkouts of `6a635d9` (the batch's base), `0e68f25`, `df22096`,
`79f5c4a` and HEAD. `L` = live hit, `X` = matched but exempted.

| figure | pattern | base | at its motivating commit's parent | HEAD |
|---|---|---|---|---|
| `inamp-full-scale` | `-2.185*(V_BREATH` | 0L/2X | 0L/2X | — |
| | `-9.6V` | 0L/2X | 0L/2X | 0L/2X |
| | `to -9.6` | 0L/2X | 0L/2X | — |
| | `−2.185·(V_BREATH` | **1L** | **1L** | — |
| | `−9.6V` | — | — | — |
| `sensor-full-scale` | `(766mV/kPa, 0.2-4.7V)` | 0L/2X | 0L/2X | — |
| | `0.2 to 4.7 V` | — | — | — |
| | `0.2-4.7V` | 0L/2X | 0L/2X | — |
| | `0.2–4.7 V` | **1L** | **1L** | — |
| | `reaches 4.7 V` | **2L** | **2L** | — |
| | `reaches 4.7V` | **2L** | **2L** | — |
| | `top of range is 4.7V` | 0L/2X | 0L/2X | — |
| `breath-sensor-slope` | `0.6 V/kPa` | — | — | — |
| | `766.5 mV/kPa at 3.3` | — | — | — |
| | `0.5059 V/kPa` | — | — | — |
| `key-release-time` | `at ~125us` | 0L/2X | 0L/2X | — |
| | `release is ~93us` | **2L** | **2L** | — |
| | `~125us` | 0L/2X | 0L/2X | 0L/2X |
| | `~93us` | **2L** | **2L** | 0L/2X |
| `key-press-time` | `44x margin` | 0L/2X | 0L/2X | — |
| | `in ~5.7us` | 0L/2X | 0L/2X | — |
| | `press is ~1us` | **2L** | **2L** | — |
| | `~5.7us` | 0L/2X | 0L/2X | 0L/2X |
| `chain-conductors` | `Six conductors per` | **1L** | **1L** | — |
| | `Six conductors per hop` | **1L** | **1L** | — |
| `panel-width` | `good practice at 8HP` | **1L** | **1L** | — |
| | `practice at 8HP rather` | **1L** | **1L** | — |
| `panel-height-budget` | `107mm of ~110mm` | 0L/2X | 0L/2X | — |
| | `115mm against ~110mm` | 0L/2X | 0L/2X | — |
| | `13mm spare` | 0L/2X | **1L**/1X | — |
| | `= 97mm` | 0L/2X | **1L**/1X | — |
| `ks33-contact-bounce` | `bounce duration and the reset point` | 1L | **1L** | — |
| | `bounce is not published` | — | — | — |
| | `bounce, which Gateron does not` | — | — | — |
| | `does not publish contact bounce` | — | — | — |
| | `no published bounce figure` | — | — | — |

**Tally: 14 live, 13 exempt-only, 9 no-hit-ever.**

### D7-1 — the 13 exempt-only patterns, and why this is the finding

A pattern that matches only text the exemption rule excuses adds **no**
detection power. The cleanest demonstration is to put the HEAD register in
front of the pre-fix tree and run the HEAD checker `[test]`:

```
$ cp config/figures.yaml tools/check-staleness.py  <0e68f25 worktree copy>/
$ python3 tools/check-staleness.py --detail
...
STALE VALUES STILL LIVE (19)
  [chain-conductors]     ROADMAP.md:203 'Six conductors per', 'Six conductors per hop'
  [inamp-full-scale]     breath-receive-stage.md:88 '−2.185·(V_BREATH'
  [key-press-time]       bom.csv:35 + key-switch-network/bom.csv:4 'press is ~1us'
  [key-release-time]     bom.csv:35 + …/bom.csv:4 'release is ~93us', '~93us'
  [ks33-contact-bounce]  0002-key-switches-and-mounting.md:218 'bounce duration and the reset point'
  [panel-height-budget]  module/panel/bom.csv:2 '13mm spare', '= 97mm'
  [panel-width]          ROADMAP.md:53 'good practice at 8HP', 'practice at 8HP rather'
  [sensor-full-scale]    0005:74 '0.2–4.7 V'; 0003:565 + 0005:76 'reaches 4.7 V';
                         bom.csv:20 + breath-adc/bom.csv:4 'reaches 4.7V'
```

Nineteen live findings, from **14** patterns. The other 13 are silent, and
three of the silent ones are the ones the commit was named after:

**The `U-DIFFRX` row.** `escape_note` `[repo] config/figures.yaml:39-58` states
the case in capitals: *"THE MISS WAS ONE SPACE… All four patterns above spell
the value WITH a space; the row spells it without."* The fix adds `-9.6V`,
`to -9.6` and `-2.185*(V_BREATH` in the row's own spelling — correctly, by the
rule. And they still do not fire, because that BOM notes cell contains

`[repo] hardware/bom.csv:81 (at `0e68f25`, line 80)`

> …Output is 0V at rest to **-9.6V** at full (Vout = **-2.185\*(V_BREATH** −
> V_AGND) + V_REF…). This field read "-0.44V at rest to -10V at full"
> **until 2026-09-21** — that is the UN-NULLED output…

`until 2026` satisfies `REFUTATION`, 180 characters away, and it is a
correction about a **different** prior value (`-0.44V`/`-10V`). The
`escape_note` ends "and the checker reported PASS". With the new patterns in
place, against the same tree, **the checker still reports nothing for this
row**. The escape is closed in the text and open in the tool.

**The `C-KEY` row.** Same shape. `[repo] hardware/bom.csv:36 (at `0e68f25`)`
carried `in ~5.7us`, `44x margin` and `at ~125us` live, all three excused by
*"The '~1.4us / 176x' pair this row **used to carry**…"* — a correction about
yet another pair. Five of the added patterns land inside that one exemption.

**`D-BREATH-TVS`.** `top of range is 4.7V` is excused by `REFUTATION_SHOUT`
firing on the row's opening *"12V STANDOFF, **NOT** 5V"* — an unrelated
shouted NOT, 60 characters away `[repo] hardware/bom.csv:43 (at `0e68f25`)`.

**`U-BREATH`.** `0.2-4.7V` and `(766mV/kPa, 0.2-4.7V)` are excused by *"but IN
PRODUCTION to 2028 where the GP is **obsolete**"* — about a different part
variant `[repo] hardware/bom.csv:41 (at `0e68f25`)`.

This is the same failure the checker's own comments describe as `FB-IN` and
`WIRE-LOOM`, recurring at four new sites. The 2026-09-21 tightening of
`REFUTATION` removed `was`, `old`, `prior`; what is doing the work now is
`until \d{4}`, `\d{4}-\d{2}-\d{2}` and a case-sensitive `NOT`, all three of
which appear in almost every BOM notes cell in this repository **because the
corpus's own convention is to timestamp corrections inside the cell**. The
vocabulary was fixed; the fact that a BOM notes cell is 2,000 words of prose
with a date in it was not.

`[repo]` One more datum for whoever fixes this: the phrase the corpus actually
writes is *"This **field** carried / read"*, and `REFUTATION` matches
`this (row|line|page|ADR|file) (said|carried|read)` — **`field` is not in the
list**. Every `U-DIFFRX`-style exemption is therefore riding on the date, not
on the purpose-written correction idiom.

### D7-2 — the window crosses record boundaries

`[test]`, at HEAD, two runs differing by one appended row in
`hardware/unplaced.csv`:

```
row A alone:                "The panel is 8HP."                     → 1 stale   (FAIL)
row A + row B:  B = "An unrelated row. The old J-DISP part was deleted."  → 0 stale
```

`deleted` is in row **B** and excuses the forbidden value in row **A**. The
checker strips each line and joins with one space, so the ±300-char window
reaches straight through the row terminator into the neighbouring record.

This is not hypothetical: it is how `13mm spare` and `= 97mm` behaved at
`6a635d9`. In `hardware/bom.csv` those two strings sit at the very end of the
`PANEL` row and were exempted by *"POWER RATING IS **NOT** OPTIONAL"* — the
first words of the **next** row, `R-OUT-PROT`. In
`hardware/module/panel/bom.csv`, where `PANEL` is the last row and has no
neighbour, the identical text was **live**. The same defect, in the master and
in its own fragment, reported two different ways.

The tool's comment says the window is what makes "a correction reads NEXT TO
the thing it corrects" the rule rather than the hope. In a CSV, "next to" now
includes the adjacent part.

### D7-5 — nine added patterns match nothing, ever

`[git]` `git log -S<pattern> --all` over the corpus paths only
(`:!config/figures.yaml`, since the register contains the string by
construction) returns **no commit** for eight of the nine:

`0.5059 V/kPa`, `0.6 V/kPa`, `766.5 mV/kPa at 3.3`, `0.2 to 4.7 V`,
`does not publish contact bounce`, `bounce is not published`,
`no published bounce figure`, `bounce, which Gateron does not`.

The ninth, `−9.6V` (U+2212, no space), last existed before `24d6feb` and is
the legitimate unicode twin of `-9.6V`; I do not count it as a defect.

So **`breath-sensor-slope` is tracked with three patterns, none of which has
ever matched anything**, and `ks33-contact-bounce` with five, one of which
has. Neither list is harmful in itself. What is harmful is that
`check_patterns()` treats a non-empty list as coverage and the summary line
advertises "218 patterns", so an entry whose whole protection is decorative
is indistinguishable from one that is load-bearing.

For `ks33-contact-bounce` this matters concretely, because the real surviving
assertion is phrased in none of the five ways — see D7-4.

---

## 4. Test 2 — does any added pattern fire on something TRUE?

`[test]` Every one of the 218 patterns, scanned against HEAD: **36 patterns
produce at least one hit and every hit is exempt** (consistent with the
checker's `PASS`). I read all of them. The added ones resolve as:

- `-9.6V` → `[repo] hardware/bom.csv:81`, now a correction: *"This field
  carried the raw 2.185 and a -9.6V, which are two different wrong answers in
  one sentence"*. **Correct sentence, correctly exempted.**
- `~93us` → `[repo] hardware/bom.csv:36`, *"…~93us, both computed on the
  10k/10nF network that is **no longer** fitted"*. Correct.
- `~125us`, `~5.7us` → `[repo] hardware/bom.csv:37`, *"**SUPERSEDED**: this
  field carried ~5.7us, 44x and ~125us beside the CORRECTED thresholds"*.
  Correct.

No added pattern fires on a true sentence today. Two shape risks remain.

### D7-6 — `"0.5059 V/kPa"` forbids a correct number

`[calc]` The MPXV4006DP transfer function in this entry's own `derivation` is
`Vout = VS·[(0.1533·P) + 0.053]`, so the slope is `VS × 0.1533`.
At `VS = 5.00 V`: `0.7665 V/kPa` — the tracked value.
At `VS = 3.30 V`: `3.3 × 0.1533 = 0.50589 V/kPa` → **`0.5059 V/kPa` rounded to
four places is the arithmetically correct slope at 3V3.**

And the same entry's `note` says `[repo] config/figures.yaml:`

> It is ratiometric with VS, so it is only 0.7665 V/kPa while the sensor runs
> on 5.00 V — which is why ADR 0003 argues for the 5 V rail rather than 3V3.

The natural way to write that argument down is to state what the slope *would*
be at 3V3 — which is the string the register forbids. The pattern is not
firing because nobody has written the sentence yet. `CLAUDE.md` §2: *"A pattern
that fires on a correct sentence is worse than no pattern, because its
cheapest fix is to make the sentence wrong."* This is that pattern, one
sentence early. `"766.5 mV/kPa at 3.3"` is the same idea done **right** — the
wrong number *and* the wrong attribution, together.

### D7-7 — four bare-numeral patterns held up only by the exemption

`"~93us"`, `"~125us"`, `"~5.7us"` and `"= 97mm"` carry no words. Each matches
today only inside correction prose. Every one of them will also match the
*next* legitimate comparison anyone writes — and `[repo] config/figures.yaml:236`
already warns of exactly this for the same figure: *"A bare 125 us also
legitimately means the MEAN SAMPLING PERIOD (0-250 us at 4 kHz) and the 8 kHz
LOOP PERIOD. Match the phrase, not the numeral."* The bare `"~125us"` was then
added anyway, in the same file, eight lines above that note. The sibling
patterns `"at ~125us"`, `"in ~5.7us"`, `"release is ~93us"` do carry words and
are the right shape; the bare four are redundant with them and strictly
riskier.

**A pattern that got this right, for contrast.** `chain-conductors` added
`"Six conductors per"` and not `"Six conductors"` — and
`[repo] hardware/interfaces/key-chain-loom/key-chain-loom.md:141` says
**"Six conductors is the signal count, not the conductor count."** A bare
`"Six conductors"` would have fired on that true sentence. The added pattern
does not. Someone grepped.

---

## 5. Test 3 and 4 — shape, across all 218 patterns

### 5a. Hard-wrapped patterns — **clean**

`[test]` No pattern in the register contains `\n`. The one that did
(`spi-series-r`) was the removal in §2.3. `check_patterns()` covers this class
and reports `0`.

### 5b. D7-3 — patterns that refute themselves, and can never fire

A pattern whose own text matches `REFUTATION` or `REFUTATION_SHOUT` is always
exempt, because the ±300-char window is taken around the match and therefore
always contains the match. `check_patterns()` looks only for `"\n" in bad` and
cannot see this.

`[test]` All 218 patterns tested against the two regexes. Three self-refute:

| figure | pattern | marker inside it |
|---|---|---|
| `sensor-full-scale` | `0.2 → 4.8 V` | `→` |
| `diode-split-rationale` | `75 mV → LM317` | `→` |
| `loadswitch-fb-divider` | `VALUES NOT SET` | `NOT` (case-sensitive `REFUTATION_SHOUT`) |

`[test]` Three isolated sandboxes, each a clean `git archive HEAD`, each with
one line appended to `docs/reference/latency-budget.md`:

```
control: "The panel is 8HP and that is that."   → FAIL … 1 stale
test A:  "The divider is VALUES NOT SET today." → PASS no live stale values
test B:  "The sensor spans 0.2 → 4.8 V today."  → PASS no live stale values
```

The control proves the harness. A and B are forbidden values, stated flatly,
with nothing correcting them, and the checker is green. `"75 mV → LM317"`
behaves identically (it was in the first combined injection, which also
poisoned my own control — noted in §8 so nobody repeats it).

`0.2 → 4.8 V` and `75 mV → LM317` are *not* mistakes of intent: the arrow is
genuinely how the corpus spells those two statements. The bug is that the
corpus's arrow is also the checker's refutation marker. Any pattern that must
contain `→` or `->` is unenforceable as written.

### 5c. Refutation split by an ASCII-drawing gutter — no pattern affected, but the exposure is growing

`[test]` No pattern in the register spans a box-drawing character. The six
patterns containing `|` (`"| 0.200 V |"`, `"rest | 0.200 V"`, `"| MOSI / CS |"`,
`"+12 V | ~320 mA"`, `"chain read | < 10"`, `"| 4.800 V |"`) are Markdown table
cells, not drawings, and are correctly shaped.

The exposure is on the *other* side of the rule. `[repo]` `dac-rail`'s value is
restated **inside two ASCII drawings** — `hardware/module/dac8568/dac8568.md`
(`│           5.21V  │`) and `hardware/module/power-entry/power-entry.md`
(`│   AVDD 5.21V     `). When that value next moves, the correction beside it
will be on the far side of a `│`, and `CLAUDE.md` §2 bullet 3 says that
correction does not count. Same for `breath-response-shaper.md`'s
`(0…−9.94V) │`.

### 5d. D7-9 — CSV spelling versus prose spelling

The batch mostly got this right, and measurably: `[test]` 15 patterns use the
ASCII `u` prefix (`~93us`, `9.4 uF`), 8 use `µ`; 2 use `Ω`, 2 use the `R`
suffix, 0 use the word `ohm`; 6 use an ASCII hyphen-minus and 4 use U+2212; 6
contain an en dash. That mix is what `CLAUDE.md` §2 asks for.

Three entries are still single-spelling, and two of them are the figures
newly tracked **in this batch**:

| figure | patterns | the spelling that has no pattern |
|---|---|---|
| `key-pullup-qty` | `"21 pull-ups"` only | the BOM **qty column**, `…,21,candidate,…` `[repo] hardware/bom.csv:35` — a bare integer in a CSV field |
| `breath-sensor-slope` | 3, all prose `V/kPa` / `mV/kPa` | `766mV/kPa`, **no space**, which is how `hardware/bom.csv:41` and `hardware/interfaces/breath-sense-link/bom.csv:2` spell it — and is precisely the spelling that escaped for `sensor-full-scale` and had to be added as `"(766mV/kPa, 0.2-4.7V)"` in the same commit |
| `ks33-contact-bounce` | 5 prose assertions | `bounce time 5 msec max at 16 in/sec` `[repo] hardware/bom.csv:40` + `hardware/cluster/bom.csv:3`; and `5msec` `[repo] docs/reference/ks33-geometry.md:214`, `docs/reference/repo-maintenance.md:133` |

`breath-sensor-slope` is the sharpest: the commit message is *"fixed by
grepping first"*, the CSV-spelling trap is bullet 1 of the rule it cites, and
the new entry created in the same commit carries no CSV spelling of its own
value's unit.

---

## 6. D7-4 — the `ks33-contact-bounce` fix did not land everywhere

The entry's `note` names three documents that asserted Gateron does not
publish the figure: `ks33-geometry.md`, ADR 0002 and `latency-budget.md`. All
three are correctly fixed `[repo] docs/reference/ks33-geometry.md:211-227`,
`docs/decisions/0002-key-switches-and-mounting.md:217-226`,
`docs/reference/latency-budget.md:125-126,148`. So is `firmware/README.md:25-28`.

A fourth document was not, and the note does not name it.

`[repo] ROADMAP.md:71` (milestone M1):

> …**bounce and the actuation/reset hysteresis gap scoped** on fast press, slow
> press, fast release, slow release and a worn switch — **neither is
> published**…

`[repo] ROADMAP.md:118-121`, fifty lines below, in the same file:

> **Partly refuted 2026-09-21, now that the vendor drawing is banked**…
> Gateron *does* publish a bounce figure — **5 ms max at 16 in/sec**…
> The **hysteresis gap is still not stated numerically**…

The prose section was corrected; the milestone table row it summarises was
not. The file now contradicts itself, and the surviving half is the one a
reader of the roadmap sees first. This is the project's named failure mode —
"fixes land where the editing is happening; they do not land where the
*reader* looks" — inside the commit that tracked the figure.

**No pattern catches it, and none of the five could.** They match
`does not publish contact bounce`, `bounce is not published`,
`no published bounce figure`, `bounce, which Gateron does not` and
`bounce duration and the reset point`. The ROADMAP sentence separates the
subject from the predicate by 96 characters and says "neither is published".

A pattern that would catch it, in the entry's own style (specific to bounce,
not a number, not a claim about the vendor in general): `"bounce and the
actuation/reset hysteresis gap"`. `[test]` that string produces exactly two
hits in the corpus: `ROADMAP.md:71` **live**, and
`docs/decisions/0002-key-switches-and-mounting.md:223` exempted — the latter
being ADR 0002's own quoted record of the sentence it corrected, which is how
a correction is supposed to read. One live finding, one correct exemption, no
false positives.

**Severity.** `ROADMAP.md` is in the corpus definition, M1's scope is what a
bench session will be planned from, and the entry's own `note` argues the
figure matters because "fingerings are combinational, so a bouncing RELEASE
walks the fingering table through different notes". The surviving sentence
tells M1 to go and find out whether a number exists that the repository now
holds verbatim in a banked drawing.

---

## 7. The coverage question the tool cannot answer

> For each of the 37 figures, if its value moved tomorrow, would the current
> pattern list find the places that restate it?

**Structurally, no — for all 37.** `forbidden` holds *superseded* values. The
current value is by definition absent from it. Nothing in the register or the
tool maps a figure to the places that restate its value *now*; that is what
`CLAUDE.md` §2 step 2 ("grep the corpus for the OLD value first") does by
hand, and `check_restated()` deliberately only reports numbers that have **no**
register entry, so tracked figures are invisible to it.

So the answerable question is the one step 2 will face: **how many sites, in
how many spellings, will the grep have to find?** `[test]` Census over the
corpus at HEAD (excluding `config/figures.yaml`), counting occurrences of each
figure's own distinctive value tokens:

| figure | value | restatements | files | spellings |
|---|---|---|---|---|
| **`dac-rail`** | 5.21 V | **36** | **17** | `5.21 V` / `5.21V`, + 2 inside ASCII drawings |
| `cref-out-node` | 100 nF | 35 | 15 | `100 nF` / `100nF` |
| `panel-toggle-hole` | 6.5 mm, 5.8 mm D-flat | 30 | 7 | `6.5 mm` / `6.5mm` / `5.8 mm` / `5.8mm` |
| `loadswitch-gate-cap` | 82 nF, 98 ms typ | 30 | 11 | `82 nF` / `82nF` / `98 ms` / `98ms` |
| `plate-thickness` | 1.20 mm | 24 | 9 | `1.20 mm` / `1.20mm` |
| `panel-width` | 50.50 mm (10HP) | 21 | 10 | `50.50` / `50.5 ` / `10HP` |
| `mod-reference` | 3.3333 V | 20 | 7 | `3.3333 V` / `3.3333V` |
| `key-scan-current` | 1.43 mA / 25.8 mA | 17 | 6 | 4 (`1.43 mA` / `1.43mA` / `25.8 mA` / `25.8mA`) |
| `ferrite-bias-impedance` | ~580-614 / ~280-310 Ω | 17 | 8 | 4 bounds × 2 |
| `loadswitch-fb-divider` | 35.7 k / 5.11 k | 16 | 4 | 2 × 2 |
| `riso-ref-topology` | R_ISO 37.4 Ω | 16 | 5 | `37.4 Ω` / `37.4R` |
| `umbilical-current` | 359 mA | 10 | 5 | 1 (`359 mA`; no space-less form exists) |
| `inamp-full-scale` | −9.94 V | 9 | 6 | 6 micro-spellings incl. `−9.94 V`, `9.94V`, `(0…−9.94V) │` |
| `sensor-full-scale` | 4.86 V | 8 | 5 | 8 incl. `4.864 V`, `0.265–4.86 V`, `0.265 → 4.86 V` |
| `ks33-contact-bounce` | 5 ms max at 16 in/sec | 8 | 7 | `5 ms max` / `5 msec max` / `5msec` |
| `diode-split-rationale` | 69 mΩ at 392 mA | 8 | 3 | `392 mA` / `69 mΩ` / `69 mohm` |
| `breath-sensor-slope` | 0.7665 V/kPa | 7 | 4 | `0.7665 V/kPa` / `766 mV/kPa` / `0.766 ×` |
| `loop-budget` | 196-241 us of 250 us | 6 | 3 | 4 |
| `key-release-time` | 119.9 us | 3 | 2 | 1 (`119.9 µs`) |
| `key-press-time` | 5.92 us | 3 | 2 | 1 (`5.92 µs`) |
| `breath-zero-ref` | 0.573 V | 3 | 3 | 2 |

Twelve figures have no distinctive numeric token at all (`marker-bits` "8
bits", `free-bits` "3", `chain-conductors` "12", `chain-connectors` "8",
`key-pullup-qty` "24", `umbilical-pinmap`, `loadswitch-timer` "10 uF", the four
`DISPUTED` and the one `BLOCKED`). For those, grepping the old value is not
even possible mechanically — which is the same blind spot `check_owners()`
already reports as "UNCHECKED" for 8 of them.

### D7-11 — the reading

`sensor-full-scale` is the benchmark: `[repo] config/figures.yaml:75` — *"SO
THE COUNT IS NINE SPELLINGS OF ONE NUMBER"*. Against that:

- **`dac-rail` already exceeds it.** 36 restatements across 17 files, in both
  the prose and CSV spelling, twice inside a drawing gutter, and cited by id in
  17 files as well — so both conventions are in use for the same number. It has
  7 patterns, all against the superseded 5.25 V. If the LM317 rail moves,
  step 2 is a 17-file, ≥21-micro-spelling grep, and the corpus has never
  successfully completed one of those in a single pass.
- `cref-out-node`, `panel-toggle-hole`, `loadswitch-gate-cap` and
  `plate-thickness` are in the same class: 24–35 restatements, 7–15 files, both
  space and no-space spellings live.
- **`sensor-full-scale` itself is back to 8 spellings of its new value**,
  including `4.864 V` `[repo] hardware/module/breath-output-stage/breath-output-stage.md`
  — a fifth-figure rounding that a grep for `4.86 V` finds and a grep for
  `4.86` finds differently. It moved once, cost eleven derived statements, and
  the replacement number is restated the same way.
- The three figures with genuinely good coverage are `key-press-time`,
  `key-release-time` and `breath-zero-ref` — 3 restatements, one spelling, and
  12/12/6 patterns each. That is the shape rule 1 is aiming at, and the
  contrast with `dac-rail` is the register's real coverage story: **pattern
  count is inversely correlated with restatement count.** The figures with the
  most patterns are the ones already cleaned up; the figures with the most
  restatements have the fewest.

`ferrite-bias-impedance` deserves a specific line: one pattern, 78 characters
long, for a value restated 17 times across 8 files in four separate numeric
bounds. `[repo] hardware/bom.csv:61` shows that single pattern currently
matching the row whose premise it records, exempted by a date.

---

## 8. Reproducing this

```
git worktree add --detach <scratch>/pre  0e68f25~1     # 6a635d9, batch base
git worktree add --detach <scratch>/mid  0e68f25
git worktree add --detach <scratch>/mid3 79f5c4a
# matcher replica: stripped lines joined with " ", str.find, ±300-char window
# over the joined stream, REFUTATION + REFUTATION_SHOUT copied verbatim from
# tools/check-staleness.py

# D7-1, definitive form:
cp -r <scratch>/mid <scratch>/mixtree
cp config/figures.yaml tools/check-staleness.py <scratch>/mixtree/...
cd <scratch>/mixtree && python3 tools/check-staleness.py --detail

# D7-2 and D7-3: one sandbox per injection, from `git archive HEAD | tar -x`.
```

**A trap I fell into, recorded so the next auditor does not.** My first
injection test put all three self-refuting strings *and* the control in one
file. It printed `PASS`, which looked like the finding — but the control
should have failed. `0.2 → 4.8 V` and `75 mV → LM317` contain `→`, so they
exempted the control sentence 200 characters away. **Testing an exemption bug
requires one sandbox per injection.** The isolated runs in §5b are the ones to
trust.

## 9. What I could not settle

- **The two `ks33-contact-bounce` pattern removals** are not in git (§D7-12).
  Only the entry's `false_positive_note` records them. Settled by whoever has
  the session transcript, or accepted on the note's word.
- **Whether the exemption rule should be changed or the BOM notes convention
  should.** D7-1 and D7-2 are one defect with two possible fixes: narrow the
  window so it cannot cross a record boundary and cannot reach an unrelated
  clause, or stop putting 2,000-word dated narratives in a CSV cell. I have
  measured the failure, not chosen the fix. That call belongs with D1–D5.
- **Whether `"12x to 300x"` should be re-added or the text fixed.** I recommend
  the text (§2.2), but the row is `BLOCKING`-marked history and someone who
  knows the LT1641 provenance should confirm the sentence is a correction
  rather than a record.
