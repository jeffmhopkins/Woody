# D1 — `tools/check-staleness.py`, adversarial

**Slice:** break the checker again. **Subject:** `0e68f25`, which rebuilt it
(+492 / −54).
**Method:** read `git show 0e68f25 -- tools/check-staleness.py`, then attack
`git archive HEAD | tar -x` into throwaway trees under the session scratchpad.
Every "this can be fooled" below was run. `[test]` claims quote the command
and its real output. Line numbers are `tools/check-staleness.py` at `HEAD`.

Nothing in the corpus was modified. `git status` shows this file only.

---

## The short answer: what a PASS proves now

Baseline, unmodified tree `[test]`:

```
$ python3 tools/check-staleness.py
PASS no live stale values | corpus 123 files, 23 circuits, 37 figures / 218 patterns | 5 unresolved (tracked) | 233 restated-not-cited (advisory)
```

| A PASS **does** prove | A PASS **still permits** |
|---|---|
| The 218 registered `forbidden` strings do not appear in the 123 corpus files **except** where a correction word, a shouted `NOT`, an ISO date or an ASCII `->` sits within 300 characters | A stale value with any dated note or any arrow within 300 chars of it — 47 % of today's 68 exemptions ride on a bare date (**F4**) |
| `hardware/bom.csv` and `datasheets/MANIFEST.csv` byte-match their fragments; `verify-datasheets.py` passes | — (sound; `--check` is genuinely implemented in both tools, verified) |
| Every `owner:` path exists | That the owner states the figure's **value** — for any figure whose value contains a hyphenated identifier, only the identifier is checked (**F1**); and 8 of 32 settled figures are reported `UNVERIFIABLE` and checked not at all |
| That *a* token of 24 settled figures appears in the owner | **Which** token, for 6 of them, is decided by the process hash seed — the same tree gives PASS or FAIL run to run (**F2**) |
| One figure–BOM relationship (`spi-series-r`) agrees | The other 12 figures that name a real BOM refdes, because they name it in `quantity:` not `value:` (**F3**) |
| 143 of 166 inline links resolve | The 23 that carry a `#fragment` — the regex cannot match them at all (**F5**) |
| 60 of 68 cross-file `§` references resolve | The 8 defeated by a hard wrap or a full stop, in a corpus hard-wrapped at 78 columns (**F6**) |
| Every declared `depends_on` edge resolves | Any circuit reachable only through a symlink — `load_circuits()` does not follow links even though `corpus_files()` now does (**F9**) |
| Every `check_*` function was **called** | That its result reached the verdict. Two tokens defeat the assertion (**F7**) |
| Nothing semantic, by design (docstring, ll. 9–11) | — (correctly disclaimed) |

And a PASS is not guaranteed to arrive at all: one symlink makes the tool run
forever inside a 60-second hook budget (**F8**).

---

## F1 — the seventh fail-open: `check_owners` stopped checking values

`[repo] tools/check-staleness.py:860-866`

```python
nums   = [t for t in re.findall(r"(?<![0-9A-Za-z.])(\d+\.?\d*)(?![0-9A-Za-z])", value) if len(t) >= 3]
idents = [t for t in re.findall(r"\b[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)+\b", value)          if len(t) >= 5]
toks = sorted(set(idents), key=len, reverse=True)[:2] or \
    sorted(set(nums), key=len, reverse=True)[:1]
```

The `or` is exclusive. If the value contains an identifier, **the numbers are
never looked at.** The docstring immediately above says the opposite —

> So: take EVERY distinctive token, numeric and symbolic

— and the same docstring block condemns exactly the behaviour the code now
has:

> picking 5050 out of it meant the check was asking whether the owner page
> mentions a part - which it does, and which proves nothing

For `spi-series-r`, value `100 ohm, R-SPI-SER, qty 3`, the check now verifies
that `hardware/interfaces/spi-link/spi-link.md` contains the string
`R-SPI-SER`. It does not ask about `100`.

### Reproduced `[test]`

The documented resistor-change procedure from `CLAUDE.md` §2 and
`repo-maintenance.md`: edit the fragment, update the register, re-run
`merge-bom.py`, run the checker. Owner page untouched.

```
$ sed -i 's/value: "100 ohm, R-SPI-SER, qty 3"/value: "150 ohm, R-SPI-SER, qty 3"/' config/figures.yaml
$ # hardware/interfaces/spi-link/bom.csv: R-SPI-SER part field 100R 1% -> 150R 1%
$ python3 tools/merge-bom.py            # rc=0
$ grep -c "100 Ω" hardware/interfaces/spi-link/spi-link.md
6
$ python3 tools/check-staleness.py
PASS no live stale values | corpus 123 files, 23 circuits, 37 figures / 218 patterns | 5 unresolved (tracked) | 233 restated-not-cited (advisory)
$ echo $?
0
```

The owner page still says, in bold, twice, with a three-row derivation table:
**"All three are `R-SPI-SER`, and the value is 100 Ω"** and **"The value is
100 Ω, not 220"** `[repo] hardware/interfaces/spi-link/spi-link.md:58,65`.
That is rule 1 broken on the figure `CLAUDE.md` uses as its worked example,
with exit 0.

### This is a regression, not a pre-existing gap `[test]`

Replaying both token-selection algorithms against the broken tree:

```
OLD toks: ['150'] -> any in owner? False      # 0e68f25~1, would have FAILED
NEW toks: ['R-SPI-SER'] -> all anchored? True # HEAD, PASSES
```

The pre-`0e68f25` code caught this. The rebuild traded the value for the part
name.

### The old hole is also still open where no identifier exists `[test]`

`cref-out-node`'s only token is `100` (its `REF5050` has no hyphen, so the
identifier regex misses it). Repointing its `owner:` at an unrelated ADR about
MCU partitioning:

```
    id: cref-out-node
    owner: docs/decisions/0001-mcu-and-board-partitioning.md
$ python3 tools/check-staleness.py
PASS no live stale values | corpus 123 files, ...
```

This is verbatim the failure the new docstring names as the reason the
*previous* version was wrong ("`100` also spells the Cat5 line impedance").

**Measured distinctiveness** `[calc]` — for each settled figure, the number of
the 123 corpus files that contain an anchored occurrence of every token the
check looks for, i.e. the number of files the owner could be repointed at
without the check noticing:

| figure | token(s) checked | files that satisfy it |
|---|---|---|
| `cref-out-node` | `100` | 48 |
| `loop-budget` | `250` / `241` / `196` (see F2) | 23 |
| `dac-rail` | `5.21` | 18 |
| `pitch-compensation` | `2.2` | 18 |
| `plate-thickness` | `1.20` | 13 |
| `spi-series-r` | `R-SPI-SER` | 10 |
| `panel-width` | `50.50` | 10 |
| `opa2197-output-impedance` | `375` | 10 |
| … 16 more, 2–8 files each | | |
| 8 settled figures | none — reported `UNVERIFIABLE` | n/a |

The eight unchecked are `marker-bits`, `free-bits`, `chain-conductors`,
`chain-connectors`, `key-pullup-qty`, `umbilical-pinmap`, `loadswitch-timer`,
`ks33-contact-bounce` `[test]` (the tool's own `--detail` output). Note
`loadswitch-timer` (`10 uF`) and `umbilical-pinmap` (the whole Cat5 pinout) —
both fall out because their tokens are under three characters or glued to a
unit letter. The `UNVERIFIABLE` list is honest and is the best thing in this
check; it is also 25 % of the settled register.

**Also correct, for the record:** `anchored_in()` (l. 643) genuinely closes the
`14.863` / `OPA2197` / `REF5050` substring hole. `inamp-full-scale` repointed at
the same unrelated ADR is caught `[test]`. The anchor is doing its job; the
token *selection* is what fails.

**Residual in the anchor itself** `[repo] :643-646`: the trailing lookahead is
`(?![0-9])` only, so `100` is satisfied by `100BASE-TX`, and the lookbehind
excludes `[0-9A-Za-z.]` but not `-`, so `375` is satisfied by a negative
`-375`. Not reproduced against the live corpus; latent.

---

## F2 — `check_owners` is nondeterministic: the same tree passes or fails

`[repo] :864` `sorted(set(...), key=len, reverse=True)[:1]`

`sorted` is stable, `key=len` alone does not break ties, and the input is a
`set` — so among equal-length tokens the winner is decided by set iteration
order, which varies with `PYTHONHASHSEED` from process to process.

`[test]` six seeds, same file:

```
seed 0: loop-budget=['196']  ferrite-bias-impedance=['580']  panel-toggle-hole=['5.8']  loadswitch-fb-divider=['5.11']  key-scan-current=['25.8']
seed 1: loop-budget=['241']  ferrite-bias-impedance=['310']  panel-toggle-hole=['5.8']  loadswitch-fb-divider=['5.11']  key-scan-current=['25.8']
seed 2: loop-budget=['196']  ferrite-bias-impedance=['310']  panel-toggle-hole=['6.5']  loadswitch-fb-divider=['35.7'] key-scan-current=['1.43']
seed 3: loop-budget=['241']  ferrite-bias-impedance=['280']  panel-toggle-hole=['6.5']  loadswitch-fb-divider=['35.7'] key-scan-current=['1.43']
seed 4: loop-budget=['250']  ferrite-bias-impedance=['614']  panel-toggle-hole=['6.5']  loadswitch-fb-divider=['35.7'] key-scan-current=['25.8']
seed 5: loop-budget=['241']  ferrite-bias-impedance=['310']  panel-toggle-hole=['6.5']  loadswitch-fb-divider=['5.11'] key-scan-current=['25.8']
```

6 of the 24 token-bearing settled figures flap. End to end, with a real rule-1
violation live — `5.11` removed from `loadswitch-fb-divider`'s owner page while
the register still states `35.7 kohm / 5.11 kohm` `[test]`:

```
$ sed -i 's/5\.11/5\.10/g' hardware/module/umbilical-load-switch/umbilical-load-switch.md
$ for i in $(seq 10); do python3 tools/check-staleness.py | cut -c1-12; done | sort | uniq -c
      4 FAIL 0 shape
      6 PASS no live
```

Confirmed source `[test]`:

```
FIGURE OWNERS (1)
  [loadswitch-fb-divider] owner .../umbilical-load-switch.md does not state its own value
  '35.7 kohm / 5.11 kohm, both 1%' - looked for '5.11' and found no unglued occurrence.
```

This is a new species for this repository: not a check that is always green,
but one that is green often enough. A clean run proves nothing about the next
run; the commit hook renders green 60 % of the time on a live defect; and a
maintainer who re-runs after a surprising FAIL will see it disappear.

---

## F3 — `check_bom_figures`, "the one that matters", examines 1 figure of 32

`[repo] :707-716`. The check iterates `REFDES_IN_VALUE.findall(value)` — refdes
spelled in the `value:` field. Exactly one figure in the register does that.

`[calc]` figures naming a **real BOM refdes** outside `value:` (in `quantity:`
or `derivation:`), which the check never reads:

```
key-scan-current       R-KEY-PU, R-KEY-SER     chain-connectors    J-CHAIN
key-pullup-qty         R-KEY-PU                pitch-compensation  C-FB-PITCH
panel-toggle-hole      SW-POWER                loadswitch-timer    C-TIMER-LOADSW
loadswitch-gate-cap    C-GATE-LOADSW           loadswitch-fb-divider R-FB-HI, R-FB-LO
cref-out-node          C-REF-OUT               riso-ref-topology   R-ISO-REF
plate-thickness        PLATE-TOP, PLATE-THUMB  ferrite-bias-impedance FB-IN
```

12 relationships out of 13 are outside the check's reach.

### Reproduced `[test]` — the same defect the check was written for, one row over

`loadswitch-timer` tracks `C-TIMER-LOADSW` at `10 uF`. The documented
procedure, fragment only:

```
$ # hardware/module/umbilical-load-switch/bom.csv: "10uF low-leakage..." -> "22uF low-leakage..."
$ python3 tools/merge-bom.py            # rc=0
$ grep "^C-TIMER-LOADSW" hardware/bom.csv
C-TIMER-LOADSW,module,"22uF low-leakage, 16V or better",...
$ grep -A2 "id: loadswitch-timer" config/figures.yaml
    quantity: C-TIMER-LOADSW
    value: "10 uF"
$ python3 tools/check-staleness.py
PASS no live stale values | corpus 123 files, ...   (exit 0)
```

The commit message says of `check_bom_figures`: *"Change a resistor the way
`CLAUDE.md` and `repo-maintenance.md` tell you to … and you get '0 problems'
and 'PASS'."* That sentence is still true for 12 of the 13 rows. The check
closed the one instance it was reproduced on.

**Also**: `if row is None: continue` `[repo] :715-717` — a figure naming a
refdes that has **no** BOM row is silently skipped, which is the deleted-part
case. And `primary = max(nums, key=len)` `[repo] :713` picks the longest
numeral, not the governing one; for a value like `82 nF, ramp 49-197 ms` that
would be `197`, and `max` over a list breaks ties on first-seen. Latent only
because the check's scope is one figure.

---

## F4 — the refutation vocabulary leaked again, on the same pattern

`[repo] :93-105`. The commit correctly dropped `was` / `old` / `rather than`,
then added:

```python
    r"|\d{4}-\d{2}-\d{2}|->|→",
```

A bare ISO date is not a statement that something was corrected. This corpus
dates almost every note it writes.

`[calc]` classifying all 68 exemptions the live corpus currently earns, by the
alternative that fired:

```
  32  a bare date \d{4}-\d{2}-\d{2}      (47 %)
  10  used to          8  superseded     7  until <year>
   2  obsolete         2  withdrawn      2  previously
   2  this row said    1  carried a superseded   1  refuted   1  deleted
```

Of those, **6 rest on the date or arrow alone** — no correction word, no
shouted `NOT`, anywhere in the window. Two of the six are the escape the
commit message names as its own justification:

```
[chain-connectors] hardware/carrier/bom.csv:6   'five connectors must match'
    exempted by '2026-09-21' 222 characters away
[chain-connectors] hardware/bom.csv:30          'five connectors must match'   (the generated copy)
```

`[repo] hardware/carrier/bom.csv:6`, `WIRE-LOOM`:

> … chained through each cluster board in turn **rather than starred, so five
> connectors must match**: one on the carrier and one per cluster board.

`chain-connectors` is settled at **8**. The commit message says:

> WIRE-LOOM states a live "five connectors" against a tracked 8, and is
> excused by "rather than starred" 24 characters away

`rather than` was removed from the vocabulary. The claim is still live, still
exempt — now on `DECIDED 2026-09-21:` 222 characters earlier in an unrelated
clause about J-CHAIN being a 2×6 IDC. The named defect was not fixed; its
exemption was re-sourced. The same text is in the repository twice, fragment
and generated master.

The other four date-only exemptions are `loadswitch-timer` patterns on
`hardware/bom.csv:71` and its fragment, exempted at +157 and +275 characters.

### `->` alone is sufficient, reproduced `[test]`

```
$ cat >> docs/reference/latency-budget.md <<'EOF'

## Panel note

The panel is 8HP and the layout below assumes it.

```
   BREATH -> ADC -> SPI -> DAC -> CV OUT
```
EOF
$ python3 tools/check-staleness.py
PASS no live stale values | corpus 123 files, ...   (exit 0)

$ # verbatim control: replace the four arrows with colons, change nothing else
$ python3 tools/check-staleness.py
FAIL ... + 1 stale + 0 bom | corpus 123 files, ...   (exit 1)
```

`The panel is 8HP` is a registered `forbidden` string for `panel-width`. A
signal-flow diagram three lines below it is the whole exemption. Every
schematic page in `hardware/**` is an ASCII drawing; `->` and `→` are the
notation those drawings are written in. This makes the exemption vocabulary
effectively "anything near a diagram."

### The window got *wider* for prose, not narrower

`[calc]` the old rule was `ctx = " ".join(lines[first-1:last])` — for an
unwrapped match, one hard-wrapped line, ~78 characters. The new rule is ±300
characters of the joined stream, ~600 characters, roughly eight lines. It
narrowed only for `bom.csv`, where a line is a row.

Measured honestly: only **4 of 68** exemptions exist solely because of the
widening, and all four read as genuine corrections one line away
(`spi-series-r` at `0004:78` on `refuted`; `pitch-compensation` at `0006:722`;
`diode-split-rationale` ×2 at `power-entry.md:102` on `used to`). **The
widening is not currently causing harm** — the commit's own thesis, that the
vocabulary rather than the distance was the leak, is correct. It just replaced
`was` (23 of 59) with a date (32 of 68).

**Suggested minimum**: require the dated marker to be *adjacent* — a date
followed within ~40 characters by `:` and one of the correction words, which is
the shape this corpus actually writes (`2026-09-21: 8HP -> 10HP`,
`DECIDED 2026-09-21:` would then correctly *not* qualify). And drop bare `->`
entirely; it is a drawing character here, not prose.

---

## F5 — `check_links` cannot see any link with a `#fragment`

`[repo] :903`

```python
pat = re.compile(r"\]\(([^)#\s]+)(?:\s+\"[^\"]*\")?\)")
```

The class excludes `#`, so on `](file.md#anchor)` the regex consumes `file.md`,
finds `#` where it needs `)` or a title, backtracks, and **fails entirely**.
The link is not checked — not the anchor, not the file. The body's
`tgt = m.group(1).split("#")[0]` `[repo] :912` shows the author believed the
opposite; that line is unreachable for inline links (it does work for the
reference-style branch, whose `(\S+)` does capture the fragment).

`[test]`

```
$ cat >> docs/reference/latency-budget.md <<'EOF'
See [the deleted page](no-such-file-at-all.md#section-4) and
[the old ADR](../decisions/0099-does-not-exist.md#rationale).
EOF
$ python3 tools/check-staleness.py
PASS no live stale values | ...   (exit 0)

$ # same two links, #anchor removed, nothing else changed
$ python3 tools/check-staleness.py
FAIL ... + 2 links + ...   (exit 1)
```

`[calc]` **23 of the 166 inline links in the corpus (14 %) are unchecked**, and
they are the ones most exposed: 12 of them are
`](../../README.md#the-interfaces-table)` from every circuit page in
`hardware/carrier/`, `hardware/cluster/`, `hardware/interfaces/` and
`hardware/module/`. The check was added, in its own docstring's words, because
the restructure broke sibling-relative links; these 23 all point across
directory boundaries at a heading in a table that this very wave (D16/D17) is
reviewing for renamed nets.

---

## F6 — `check_sections` is defeated by the corpus's own hard wrap

`[repo] :585`

```python
ref = re.compile(r"`?([a-z0-9][a-z0-9-]*\.md)`?\)?[^.\n]{0,24}?§\s?(\d+)")
```

Three separate ways to be invisible:

1. `[^.\n]` — the gap may not contain a **newline**. The corpus is hard-wrapped
   at ~78 columns. `check_figures` was rebuilt in this same commit to search a
   *line-joined* stream for exactly this reason (`:191-199`); `check_sections`
   was not.
2. `[^.\n]` — the gap may not contain a **full stop**, so `…foo.md). §3` never
   matches.
3. `[a-z0-9]` — the filename must start lowercase, so **`README.md §N` and
   `CLAUDE.md §N` are never matched at all.** (Which also means the
   10-way `README.md` basename collision that motivated the path-keying fix
   can never actually arise.)

`[test]` — one reference, three spellings, nothing else changed:

```
The derivation lives in `cluster-boards.md` §99, which does not exist.
  -> FAIL ... + 1 sections + ...

The derivation lives in `cluster-boards.md`
§99, which does not exist.                       (a hard wrap)
  -> PASS no live stale values | corpus 123 files, ...

The derivation lives in `cluster-boards.md`. §99 does not exist.
  -> PASS no live stale values | corpus 123 files, ...
```

`[test]` a broken `README.md` section reference:

```
See `hardware/README.md` §42, which is not there.
  -> PASS
```

`[calc]` against the live corpus, comparing the shipped regex with a
wrap-and-case-tolerant one, keyed on the position of each `§`:

```
captured by the shipped regex: 60 | captured by a tolerant one: 68 | MISSED: 8
```

The genuine cross-file misses include
`hardware/interfaces/breath-sense-link/breath-sense-link.md:73`
(`[`carrier.md`](../../carrier/carrier.md)\n§2`) and
`hardware/cluster/key-register/notes.md:19`
(`key-switch-network.md);\n`§1``) — both wrapped, both invisible.

---

## F7 — the wiring assertion records the call, not the consequence

`[repo] :930-971`. `instrument()` wraps each `check_*` so `RAN.add(nm)` fires on
invocation; `check_checks()` reports names not in `RAN`. This is a real
improvement — the old source-substring assertion was satisfied by
`# check_links(files)`, and an alias captured before `instrument()` runs is
correctly reported unwired. But the property that matters is *"the result
reached the verdict"*, and that is still unasserted.

`[test]` with a live broken link **and** a live registered stale value, two
edits totalling five tokens:

```python
    link_problems = check_links(files) and []         # added: " and []"
    live, refuted, spec = check_figures(files)
    live = []                                          # added line
```

```
$ python3 tools/check-staleness.py --detail | tail -3
old values present but refuted in place (69) - OK, this is how a correction reads

PASS no live stale values | corpus 123 files, 23 circuits, 37 figures / 218 patterns | 5 unresolved (tracked) | 233 restated-not-cited (advisory)
```

`UNWIRED CHECKS = 0`, exit 0, with a broken link and `The panel is 8HP` live.
The control on the unmodified tool is `FAIL … + 1 links + …`.

Note the coverage line — added in this commit specifically so a PASS would say
how much was checked — is **byte-identical to a healthy run**. It counts
inputs (files, circuits, figures, patterns), never findings, so it cannot
distinguish a run that checked everything from one that threw the answers away.
The same holds for a check whose body is emptied to `return []`: it runs, it
records, it reports nothing, and the assertion is satisfied.

*What would settle it:* assert consequence rather than invocation — e.g. have
each check return through a sink that `main()` must drain, and assert the sink
is empty at the end. Or a self-test fixture: a tiny synthetic tree with one
planted defect per check, asserted to produce exactly N failures.

---

## F8 — `followlinks=True` turns one symlink into an unbounded hang

`[repo] :119-120`. Added to fix a real hole (a circuit behind a symlinked
directory was invisible). `os.walk(followlinks=True)` has no cycle detection.

`[test]`

```
$ ln -s .. hardware/loop
$ timeout 60 python3 tools/check-staleness.py > out.txt 2>&1; echo $?
124
$ wc -c out.txt
0 out.txt
```

Sixty seconds, nothing printed. The hook
`[repo] .claude/settings.json` has `"timeout": 60`, so the check never
completes and the commit is not gated. Simulating the hook's own pipeline the
captured output is 0 bytes and `$s` is empty, so the best case is the hook's
`CHECKER CRASHED` fallback; without the explicit `timeout` the harness kills
the whole hook and nothing is emitted at all. `CLAUDE.md`'s rule via
`TOOL_INPUTS` is *"a crash must not read as silence"* — a **hang** is that
rule's unhandled sibling, and it is now reachable from a single `ln -s`.

### The budget is already most of the way gone

`[test]` clean runs: `11.36 s`, `11.55 s`, `11.17 s` of the hook's 60 s.
`[calc]` `check_figures` alone is `11.26 s` of that — essentially 100 % — at
**52 ms per pattern** across 123 files, because it re-reads and re-joins every
corpus file once per pattern (218 × 123 = 26 814 reads). `CLAUDE.md` §2 step 2
makes *adding a pattern per spelling found* a standing instruction, so this
number only goes up. The budget runs out at roughly **1 160 patterns** at
today's file count, sooner as the corpus grows — it went 33 → 123 files in one
restructure.

Separately, the tool's own subprocess timeouts sum to **240 s**
(`:282`, `:286` at 60 s each, `:675` at 120 s) against a 60 s hook budget: if
`merge-bom.py`, `merge-manifests.py` or `verify-datasheets.py` ever hangs, the
tool can never report it inside the window it runs in.

---

## F9 — the symlink fix was applied to one of the two `os.walk`s

`[repo] :119` has `followlinks=True`. `[repo] :437`, `load_circuits()`, does
not:

```python
for dirpath, _, names in os.walk(os.path.join(ROOT, "hardware")):
```

The docstring justifying the change says the motivation was *"a circuit
reachable only through a symlinked directory"* — and the circuit half is still
invisible.

`[test]` a `circuit.yaml` plus a page reachable only via `hardware/linked ->
../../elsewhere-circuits`:

```
PASS no live stale values | corpus 125 files, 23 circuits, ...
```

The two files joined the corpus (123 → 125) but the circuit count is
unchanged, so `check_circuits()` and `check_verified_against()` never see it —
its `depends_on` edges, its `verified_against` SHAs and its duplicate-id
collision are all unchecked. This is the pattern the file's own comment at
`:290-294` complains about: *"the fix below was applied to one branch and not
to this one … in the same commit."*

### And `EXCLUDE` cannot stop the reverse

`EXCLUDE` `[repo] :32` is tested against the **walked** path, not the resolved
one, so a symlink from inside a corpus directory into the historical record
pulls history into the corpus. `[test]`:

```
$ ln -s ../docs/review hardware/hist
$ python3 tools/check-staleness.py
FAIL 0 shape + 0 owners + 33 links + 209 sections + 0 deps + ... + 509 stale + 0 bom | corpus 287 files, ...
```

509 "stale values" that are correct as history. `CLAUDE.md` §6 makes
"correcting" those files an absolute prohibition; the tool would be pointing a
maintainer straight at them. (`EXCLUDE` is otherwise dead code today —
`CORPUS_DIRS` contains no ancestor of `docs/review`.)

---

## F10 — `check_links` fires fatally on links inside fenced code blocks

`CLAUDE.md`: *"A pattern that fires on a correct sentence is worse than no
pattern, because its cheapest fix is to make the sentence wrong."* `[test]`,
appending to the file that documents this very trap:

````
Do not write a bare-filename link. This is the shape that broke:

```markdown
See [the stage](breath-receive-stage.md) for the derivation.
```

[example-ref]: some/illustrative/path.md
````

```
BROKEN LINKS (2)
  docs/reference/repo-maintenance.md:381 links to 'breath-receive-stage.md', which does not resolve
  docs/reference/repo-maintenance.md:383 links to 'some/illustrative/path.md', which does not resolve
```

Both are correct prose. The check has no fence awareness, and the
reference-definition pattern `^\s{0,3}\[[^\]]+\]:\s*(\S+)` `[repo] :904` will
match any illustrative `[x]: y` line. `repo-maintenance.md` is exactly where
someone would write this. **No live instance today** — this is a trap set for
the next writer, not a current defect.

Under-matched on the same check: `[text][ref]` usages whose `[ref]:`
definition is missing are not checked at all; `](<foo.md>)` angle-bracket
targets are reported as literally `<foo.md>`; `](my file.md)` with a space is
missed.

---

## F11 — `check_sections` calls a correct, path-qualified reference "ambiguous"

`[repo] :607-620`. The regex captures only the basename, throwing away the
directory that was written; the resolver then tries a sibling, then a unique
basename, then reports ambiguity. A correct fully-qualified reference to one of
the 15 `notes.md` files is therefore fatal. `[test]`:

```
$ printf '\n## §7 What this circuit used to be\n\nText.\n' >> hardware/module/panel/notes.md
$ echo 'The history is in `hardware/module/panel/notes.md` §7.' >> docs/reference/latency-budget.md

BROKEN SECTION REFERENCES (1)
  docs/reference/latency-budget.md:240 points at notes.md §7, but 16 files in the corpus
  are called notes.md - the reference is ambiguous
```

The reference is not ambiguous; it is fully qualified, and the check discarded
the qualification before complaining it could not tell. The cheapest fixes are
to drop the path or renumber the heading — both make the corpus worse.
`CLAUDE.md`'s hardware conventions give *every* circuit a `notes.md`, so this
is reachable the moment anyone cites one across directories.

Also, `if target == os.path.basename(path): continue` `[repo] :603` means a
`notes.md` citing another `notes.md` §N, or a README citing a README, is never
checked — the self-reference test compares basenames, not paths.

---

## F12 — the tool tells you to read a report it did not write

`[repo] :1151` writes `.staleness/report.txt` at the end of `main()`. The
`TOOL_INPUTS` early return `[repo] :985-991` returns **before** that, as does
any traceback. The hook's `additionalContext` says: *"Detail is in
`.staleness/report.txt` … read it when fixing, do not re-run for detail."*

`[test]`

```
$ python3 tools/check-staleness.py            # clean run, writes the report
$ rm config/figures.yaml
$ python3 tools/check-staleness.py
  this tool reads 'config/figures.yaml', which does not exist. ...
FAIL 1 shape | corpus 122 files | checks did not run
$ head -1 .staleness/report.txt
corpus: 123 files | bom.csv: 139 rows x 11 cols | figures tracked: 37
```

The report on disk describes the previous run — 123 files where the failing run
saw 122 — and the reader was explicitly told to trust it and not re-run. A
stale derived artifact in the output path of the tool whose entire subject is
stale derived artifacts. `except Exception: pass` around the write
`[repo] :1150-1155` produces the same state silently if the write ever fails.

---

## F13 — `check_patterns` misses a second way a pattern can never fire

`[repo] :250-254` flags only `"\n" in bad`. The joiner `[repo] :201-209`
contributes **one space per line, including blank lines**, so text separated by
a paragraph break is joined with **two** spaces. `[calc]`:

```python
lines = ["The width is settled.", "", "The panel is 8HP throughout."]
-> 'The width is settled.  The panel is 8HP throughout.'
one-space pattern fires?  False
two-space pattern fires?  True
```

A `forbidden` pattern written across a paragraph break in the spelling the file
appears to have can never fire, and is reported nowhere — the same class as the
documented `"220 Ω with\n~200 pF"` trap, one step further out. `CLAUDE.md` §2's
instruction is *"write the pattern in the spelling of the file it must match"*,
which is precisely the instruction that produces this.

Also unflagged: an empty-string `forbidden` entry, which makes `text.find("")`
return a hit at every offset of every file.

---

## Attacked and found sound

Worth recording, because a fix audit should say what held.

- **`merge-bom.py --check` and `merge-manifests.py --check` are genuinely
  implemented** `[repo] tools/merge-bom.py:158, tools/merge-manifests.py:148` —
  both regenerate into memory and byte-compare. Neither silently ignores the
  flag and rewrites the file as a side effect of the checker.
- **Crash paths are loud.** `[test]` unparseable `config/figures.yaml`, a
  zero-byte `hardware/bom.csv`, and `figures: []` all exit 1; the hook's
  `[ -z "$s" ]` fallback renders `CHECKER CRASHED (exit 1)` for the first two,
  and the third prints a normal FAIL with `0 figures / 0 patterns` in the
  coverage line — which is the coverage line doing exactly its job.
  (Caveat: it is the *hook* providing this, not the tool. `TOOL_INPUTS` covers
  *missing* inputs only, not unparseable ones.)
- **`anchored_in()` works.** The `14.863` / `OPA2197` / `REF5050` substring
  hole is genuinely closed (F1 is about which token is chosen, not about the
  anchor).
- **`check_corpus_shape` + `MIN_CORPUS_FILES`** trip correctly; the early
  return on a missing `TOOL_INPUTS` file prints a grep-visible `FAIL` line.
- **`check_circuits`' prefix chain** has a working terminal `else` — the six
  typo'd prefixes are caught.
- **The `UNVERIFIABLE` (`owner_weak`) list** is the most honest construct in the
  file and should be kept and extended, not eliminated.
- `check_bom_generated` has ~12 lines of unreachable code after its
  `return []` `[repo] :302-322`. Harmless, but it duplicates the old broken
  filter and will mislead the next reader.

---

## Ranked, if only some of this is actioned

1. **F1** — `check_owners` stopped checking values. Regression, reproduced on
   the documented procedure, and the fix is one line (`+` instead of `or`,
   plus keeping the number even when an identifier is present).
2. **F2** — nondeterminism. One line (`key=(len, tok)`), and until it is fixed
   no run of this tool means anything precise.
3. **F4** — the date marker, with `chain-connectors` / WIRE-LOOM still live in
   two files as proof.
4. **F3** — read `quantity:` as well as `value:` for refdes; 12 of 13
   relationships are outside the check today.
5. **F8/F9** — `followlinks` cycle guard, and apply the fix to the second walk.
6. **F5/F6** — the two regexes; both under-match by 12–14 % of their subject.
7. **F7** — assert consequence, not invocation.

## Method note

Everything marked `[test]` was reproduced in a throwaway `git archive HEAD`
extraction under the session scratchpad, never in `/home/user/Woody`. Commands
and verbatim output are quoted above; controls (the same edit with the single
triggering character changed) are included wherever a PASS is claimed, because
a PASS from this tool is exactly the thing under suspicion. Claims marked
`[calc]` are counts computed by re-implementing the shipped code paths against
the live corpus and are reproducible from the excerpts shown.
