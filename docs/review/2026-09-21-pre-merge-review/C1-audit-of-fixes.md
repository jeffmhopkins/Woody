# C1 — audit of this round's own fixes

**Agent:** C1, cold. **Tree:** `HEAD` = `c5e8f84` (`73c2b1b` + this wave's
reports). **Range audited:** `f94e91d..HEAD`, 41 commits.

**Method.** Read every commit message in the range for checkable claims, then
verified each claim **against the working tree at HEAD**, not against the
commit that made it. Tooling claims and reproductions were re-run in
`git archive HEAD` copies under the session scratchpad, never in the repo.
Nothing under `docs/review/**` was read, per the cold rule — see *Not
verified* at the end for what that excludes.

Provenance is marked on every claim: `[repo] path:line`, `[git] <sha>`,
`[calc]`, `[test]` for a reproduction I ran.

---

## Summary

Of ~30 checkable fix claims, **26 verify cleanly at HEAD**. Four do not, and
one of those is a check that reports green on the exact case its own docstring
names as the counter-example.

| # | Finding | Node / file | Consequence |
|---|---|---|---|
| **C1-1** | `check_owners` still passes `spi-series-r` on `100` — the case `2a9c720` claims to have fixed | `tools/check-staleness.py:515-523` | **High.** A green check believed to prove rule 1 |
| **C1-2** | `sim/README.md` credits `carrier.md` twelve lines below the note saying it must not | `hardware/module/breath-receive-stage/sim/README.md:49-50` | **High.** `f16b72b`'s fix, half-landed |
| **C1-3** | The path map and `repo-maintenance.md` §7 disagree with the tree: 22 rows say `unmoved` for files that moved, 113 tracked files have no row | `docs/reference/path-map-2026-09-21.csv`, `repo-maintenance.md:238-241` | **High.** The documented way to resolve a historical path |
| **C1-4** | `key-scan-current`'s register entry says "all three restate it"; it is five, in two files the entry never names | `config/figures.yaml:135-146` | **Medium.** Grep-first failed on the commit that invoked it |
| **C1-5** | `README.md` says `datasheets/` is 77 documents; it is 76, since five commits later the same branch deleted one | `README.md:116` | **Medium.** Named failure mode, inside the fix for it |
| **C1-6** | `pcb-pipeline.md` still says "the six pages"; `81c081d` §8 predicted this and nothing closed it | `docs/reference/pcb-pipeline.md:58` | **Medium.** Net-name reconciliation, the area three reviewers flagged |
| **C1-7** | `README.md` says `docs/review/` is seven waves; the disk has nine, `CLAUDE.md` says three | `README.md:117` | **Low.** Three counts of one quantity |
| **C1-8** | `check_refdes`'s advisory gained a 23-file noise entry, `CO-MENTION`, from `4ecc17e` | `.staleness/report.txt` | **Low.** Erodes the argument that made it advisory |
| **C1-9** | `b631987` says `108c633` carries "22 datasheet file renames"; it is 21 renames and one delete | `[git] 108c633` | **Low.** Accuracy of a commit that exists to record a mistake honestly |

---

## C1-1 — `check_owners` still passes the figure its docstring names (HIGH)

**The claim.** `[git] 2a9c720` — *"The filter was `len(token) >= 3` with
`any()`, so `spi-series-r` passed on `100` … It now requires the MOST
DISTINCTIVE token"* and *"The check now makes exactly one claim: the owner
states something only this figure would say."* The code repeats it in a
comment: *"THE LONGEST token, not any token. `any()` over everything >= 3
chars still passed `spi-series-r` on `100` — the very figure this docstring
names as the counter-example. A check whose own docstring names a case it
does not catch is worse than no check."* `[repo] tools/check-staleness.py:515-521`

**It does not catch it.** The token set is built from **digits only**:

```python
alltoks = re.findall(r"\d+\.?\d*", value)
toks = sorted((t for t in alltoks if len(t) >= 3), key=len, reverse=True)[:1]
```
`[repo] tools/check-staleness.py:522-523`

`spi-series-r`'s value is `100 ohm, R-SPI-SER, qty 3`. Its numeric tokens are
`['100', '3']`; after the `len >= 3` filter only `100` survives, so "the
longest" **is** `100`. The change from `any()` to longest-only is a no-op for
this figure. `R-SPI-SER` — the one string in the value that is distinctive —
is discarded by the regex before the sort ever runs. `[calc]`

**Reproduced.** In a throwaway `git archive HEAD` tree I repointed
`spi-series-r`'s owner to `docs/decisions/0009-enclosure-construction.md`, the
enclosure ADR, which derives no SPI series resistor and mentions SPI only in
passing about cable length:

```
PASS no live stale values | corpus 121 files, 23 circuits | 5 unresolved (tracked)
EXIT=0
```
`[test]` It passes on the single occurrence of `100` in that file, which is
*"10 kΩ, 100 Ω and 10 nF per switch position"* — a key-switch network.
`[repo] docs/decisions/0009-enclosure-construction.md:521`

**How wide the hole is.** For each settled figure I computed the single token
`check_owners` actually tests, and counted how many of the 121 corpus files
contain it — i.e. how many files would pass as that figure's owner: `[calc]`

| figure | token tested | corpus files containing it |
|---|---|---|
| `spi-series-r` | `100` | **47 of 121** |
| `loadswitch-gate-cap` | `197` | **38** |
| `pitch-compensation` | `2.2` | **27** |
| `cref-out-node` | `5050` | **17** |
| `dac-rail` | `5.21` | 16 |
| `plate-thickness` | `1.20` | 10 |
| `panel-toggle-hole` | `6.5` | 10 |
| `opa2197-output-impedance` | `375` | 10 |

Two further notes on the same function. `loadswitch-gate-cap`'s value is
`82 nF, ramp 49-197 ms (98 ms typ)` and the token tested is `197`, the ramp's
**upper bound**, not the `82 nF` the figure is about — so the check cannot
see the capacitor move. And `diode-split-rationale`'s value is prose; its
longest numeric token is `392`, from the parenthetical `r_d 69 mohm at 392 mA`.

**Why this ranks first.** `1d84861`, `2a9c720` and `4ecc17e` all rest on
`check_owners` being the thing that finally reads `owner:`. Three owners were
repointed on its evidence `[git] 2a9c720`, and `4ecc17e`'s STATUS entry treats
rule-1 enforcement as the *next* gap rather than a current one. A check that
green-lights 47 candidate owners for one figure is not evidence that the
repointing was right — it is the `--invert`-proves-the-easy-half mistake that
`8ef7979` names, shipped for the third time in the same session.

**What would close it.** Tokenise on non-numeric distinctive strings too —
refdes (`R-SPI-SER`), part numbers, unit-bearing spellings — and require the
match to be the *rarest* available token, not the longest digit run. The data
above is the acceptance test: no figure should be checkable on a token that
47 files contain.

---

## C1-2 — the sim deck's fix landed in the prose and not in the table (HIGH)

**The claim.** `[git] f16b72b` part B — *"`breath-receive-stage/sim/README.md`
attributed the 60.2 / 58.5 / 73 dB CMRR claims to `carrier.md`. Those moved to
`interfaces/breath-sense-link/` and `carrier.md` contains none of them."*

**Half landed.** The prose at the top is corrected and carries an honest note:

> *"Until 2026-09-21 this section credited `carrier.md` with all three
> figures; that page derives none of them any more"*
> `[repo] hardware/module/breath-receive-stage/sim/README.md:36-38`

Twelve lines below it, the table headed **"Three terms have to appear in the
same deck … each is currently argued on its own page"** still points two of
those three terms at `carrier.md`:

| Term | Where it is argued (as written at HEAD) |
|---|---|
| Source-impedance balance on the twisted pair | `` `carrier.md` ``, the `R1`/`R1b` pair |
| The bias pair against the series legs | … the floor `` `carrier.md` `` quotes |

`[repo] hardware/module/breath-receive-stage/sim/README.md:49-50`

`carrier.md` says in as many words that it no longer holds that argument:

> *"The `R1b` half of this section — the twin in the `AGND` leg, the link-CMRR
> argument for it, and the correction it files against the receive page's own
> case for the part — moved verbatim to `../interfaces/breath-sense-link/`"*
> `[repo] hardware/carrier/carrier.md:140-144`

Every live `R1b` derivation is now in `interfaces/breath-sense-link/`
(lines 70, 81-83, 135, 138, 183, 199, 237). `carrier.md` retains only the
drawing and the pointer. `[repo]`

**Consequence.** This is the sim deck's *contract* — the column that tells
whoever builds the deck where to read each term. It sends them to a page that
holds a drawing and a forwarding address. It is also invisible to every check
for the reasons `f16b72b` itself gives: the path resolves, the figures are
untracked, and the file was written during the restructure so it was never a
conservation source. The mechanism is the one `CLAUDE.md` opens with — the
author was editing the paragraph, and the reader of a deck contract reads the
table.

---

## C1-3 — the documented way to resolve a historical path no longer describes the tree (HIGH)

`CLAUDE.md` §6 ends: *"Paths in those records point at pre-2026-09-21
locations and are not to be corrected. Resolve them through
`docs/reference/repo-maintenance.md` §7."* §7 says:

> *"`path-map-2026-09-21.csv` in this directory maps every old path to its new
> one — **every tracked file has a row**, including the ones that did not
> move, because the question a reader actually asks is 'did this path change?'
> and a map of only the movers cannot answer it."*
> `[repo] docs/reference/repo-maintenance.md:238-241`

Measured against HEAD: `[calc]`

- The map has **287 rows**. **113 tracked files have no row** — every Phase B
  circuit directory (`hardware/carrier/breath-adc/*`, all 23 of them), the
  three new index pages, `datasheets/.moves.csv`, and all 22 re-filed
  datasheets. "Every tracked file has a row" is false by 113.
- **22 rows assert `kind=unmoved`** for datasheet paths that **do not exist**
  — `datasheets/other-semi/74HC165.pdf`, `datasheets/texas-instruments/OPA2197.pdf`
  and 20 more — with the note *"datasheets/ moves whole or not at all"*.
  They moved, internally, in `[git] 108c633` and were recorded in
  `datasheets/.moves.csv` by `[git] b631987`. Both the `new` column and the
  `kind` column are wrong for those rows.
  `[repo] docs/reference/path-map-2026-09-21.csv:79-99`
- One more: `datasheets/mechanical/WS2815-worldsemi-datasheet.pdf`, `unmoved`,
  deleted in `108c633` as the duplicate bank.

`[git] 1c1155f` says *"The path map is excluded by name, because its old-side
column is SUPPOSED to name paths that no longer resolve."* That is right about
the **old** column and does not cover this: the **new** column and the `kind`
verdict are the map's answer to "where is it now", and for 22 datasheets the
answer is a path that has not existed since `108c633`.

**Consequence.** `repo-maintenance.md` §7 says history outnumbers the corpus
24:1 on path references and that the map is how you resolve them. A reader
resolving `datasheets/texas-instruments/OPA2197.pdf` out of a September review
gets `unmoved` and a dead path, when `datasheets/.moves.csv` has the answer.
Either the map is regenerated and §7 stays true, or §7 stops claiming
completeness and names `.moves.csv` as the second hop. Both are cheap; neither
happened.

---

## C1-4 — `key-scan-current` undercounts its own duplication (MEDIUM)

**The claim.** `[git] f16b72b` part A and the register entry it wrote:

> *"1.43 mA, 25.8 mA, 0.077 %, 3.2 LSB and ~1594 counts each appear in two or
> three corpus files … DEDUPLICATING it is still owed: rule 1 says the owner
> states it and the other two cite it, and **today all three restate it**."*
> `[repo] config/figures.yaml:135-146`

The entry names three files: the owner
`hardware/cluster/key-switch-network/key-switch-network.md`, plus `carrier.md`
and `interfaces/key-chain-loom/key-chain-loom.md`.

**There are five statements, in four files.** `[repo]`

| File | Line | Text |
|---|---|---|
| `hardware/cluster/key-switch-network/key-switch-network.md` (owner) | 105 | `\| Static \| **1.43 mA** per closed key; 18 closed = **25.8 mA** \|` |
| `hardware/carrier/carrier.md` | 172-174 | full derivation, `1.43 mA` / `25.8 mA` / `0.077 %` / `3.2 LSB` |
| `hardware/interfaces/key-chain-loom/key-chain-loom.md` | 115-126 | full derivation, all five numbers |
| **`docs/decisions/0001-mcu-and-board-partitioning.md`** | **230** | `\| Static \| **1.43 mA** per closed key; 18 closed = **25.8 mA** \|` |
| `hardware/carrier/carrier.md` | 373 | `25.8 mA of play-rate load worth 3.2 LSB on a ~1594-count …` |

ADR 0001:230 is a **byte-identical copy** of the owner's table row and is
named nowhere in the entry, the `companion` field or the commit message.
`[calc]`

**Why it matters more than the count.** `f16b72b` is the commit that tracked
this figure *because* a cold reviewer found it live in two files with nothing
able to see a divergence. The register entry it wrote is now the authority on
where the duplicates are, and it is missing one of them — in an ADR, the
document class most likely to be read years from now. `CLAUDE.md` §2 step 2
exists for exactly this: the list was written from the pages in front of the
author. `6602b43` records the same lesson from the same afternoon
(*"the agent saw three of the five"*), one wave earlier.

**Related, unrecorded.** `inamp-full-scale` (`-9.94 V`, owner
`interfaces/breath-sense-link/breath-sense-link.md` after `2a9c720`
repointed it) is restated in **seven** non-owner corpus locations —
`breath-receive-stage.md:89,126`, `breath-output-stage.md:40`,
`breath-response-shaper.md:51,104`, `bom.csv:118`, plus the drawing `2a9c720`
names. That is worse than `sensor-full-scale`, which `4ecc17e` singles out as
*"restated six times right now"* — a count I confirmed exactly, at six.
`[calc]` `inamp-full-scale` appears in no debt list I can see from the corpus.

---

## C1-5 — `README.md` still says 77 datasheets; there are 76 (MEDIUM)

`[repo] README.md:116-118`:

> *"`datasheets/` is 77 banked documents and the largest directory in the
> repository; `docs/review/` is seven waves. Both were invisible in the one
> file a new reader opens first."*

Counted at each point in the branch: `[calc]`

| revision | files under `datasheets/` (excl. manifest, README, fragments) |
|---|---|
| `a973267` — the commit that wrote the sentence | **77** |
| `b631987^` (i.e. after `108c633`) | 76 |
| `HEAD` | **76** |

`[git] 108c633` deleted `datasheets/mechanical/WS2815-worldsemi-datasheet.pdf`
— the WS2815 was banked twice under two paths with one SHA-256, and
`[git] b631987` records the de-duplication deliberately: *"Both rows survive …
and now name one file."* The **row** count stayed 77; the **file** count went
to 76. `README.md` states it as a count of documents.

Directory census at HEAD: `analog 8, connectors 22, discrete-and-power 20,
led 6, logic 5, mechanical 15` = **76**. `[calc]`

This is the named failure mode with an unusually short fuse: the sentence was
written to fix an omission a cold reviewer found, and five commits later on
the same branch the number it states moved. Nothing can catch it — the
datasheet count is not a tracked figure, and `datasheets/` is not in
`CORPUS_DIRS`, so `datasheets/README.md` is unscanned as well.
`[repo] tools/check-staleness.py:30`

---

## C1-6 — `pcb-pipeline.md` still says "the six pages" (MEDIUM)

`[git] 81c081d` §8 recorded this as debt the restructure would create:
*"pcb-pipeline says 'the six' and will be wrong with no check able to see
it."* Nothing in the 40 commits since closed it.

At HEAD: `[repo] docs/reference/pcb-pipeline.md:58`

> **1. Reconcile net names across the six pages first.** `AGND` means the
> umbilical sense conductor *and* the module analog return. `BREATH` means the
> in-amp input *and* the output jack. **Three cold reviewers found this
> independently.**

There are now **23 circuit pages plus four board/index pages**, not six.
`[calc]` This is a live instruction under *"Precursors that bite at the
netlist, not the board — only the ones that corrupt something no later stage
can catch"*, and the failure it guards against is the one this wave keeps
naming: a transcription that misses the `AGND`/`BREATH` collision shorts the
in-amp input to the output jack with every downstream check passing
(`[git] 036b182`, `[git] fcd56e6`). Someone following the instruction
literally reconciles six pages out of twenty-seven.

Same section, line 67: *"Seven rails, six modules"* — SKiDL modules, probably
unaffected, but it reads as the same stale count on a second glance and is
worth a word either way.

---

## C1-7 — three documents, three counts of the review waves (LOW)

- `[repo] README.md:117` — *"`docs/review/` is seven waves"*.
- `[repo] CLAUDE.md:92-94` — *"Three have run"*, naming
  `2026-09-20-cold-review`, `2026-09-21-hardware-and-standards-review`,
  `2026-09-21-staleness-sweep`.
- On disk at HEAD: **nine** directories — the three above plus
  `datasheet-reconciliation`, `pcb-pipeline-review`, `preflight`,
  `restructure-design`, `schematic-review`, `pre-merge-review`, and one loose
  file `2026-09-20-analog-design-review.md`. `[calc]`

"Seven" was already off by one when `a973267` wrote it (eight directories at
that commit) and is off by two now: `[git] 6be65f7` and `[git] 73c2b1b` each
added one. `CLAUDE.md`'s "three" is the user's own and predates the branch;
I flag it only because it makes three different live answers to one question,
which is the shape the register exists to prevent.

---

## C1-8 — the refdes advisory gained a 23-file noise entry (LOW)

`[git] 9310848` wired `check_refdes` as an advisory on a measured argument:
*"raw it yields 36 hits of which about 14 are not reference designators at
all. Filtered, 18 — and they are real."*

At HEAD the advisory yields **19**, and the new one is `CO-MENTION`, listed
against **23 files** — every `circuit.yaml` in the repository:

```
CO-MENTION   hardware/carrier/breath-adc/circuit.yaml, …[23 files]…
```
`[test]` (`python3 tools/check-staleness.py --detail`)

`CO-MENTION` is not a refdes. It is a word in the `STATUS: SEEDED, NOT
VERIFIED` banner that `[git] 4ecc17e` added to all 23 `circuit.yaml` files
(*"`depends_on` was machine-seeded from CO-MENTION"*), and `check_refdes`
scans raw file text including comments. `[repo]` It is now the longest entry
in the advisory by a factor of five.

Low consequence on its own; worth reporting because the *only* argument for
this check being advisory rather than fatal is its signal-to-noise ratio, and
that ratio was degraded by the commit that documented the seeding. The fix is
one entry in the existing filter.

---

## C1-9 — `b631987`'s confession is accurate to within one word (LOW)

`[git] b631987` — *"Commit `108c633`, whose message says 'two tools', also
carries 22 datasheet file renames."*

`git show --name-status 108c633` gives **21 renames (all R100), one delete,
one modify, one add**. `[git] 108c633` The delete is
`datasheets/mechanical/WS2815-worldsemi-datasheet.pdf`. So the substance is
correct and honestly stated — `108c633`'s message does describe a commit that
does not exist — but "22 renames" is 21 renames and a deletion. Recording it
because `CLAUDE.md` is explicit that a finding filed as handled stops getting
re-checked, and this is a commit whose whole purpose is the accuracy of a
record.

---

## What I verified and found sound

Each of these was re-run or re-measured at HEAD, not taken from the commit.

**Tooling — reproduced in throwaway `git archive HEAD` trees**

| Claim | Commit | Result |
|---|---|---|
| Non-UTF-8 byte in a fragment + hand edit in `bom.csv` used to print PASS/exit 0; now fails | `eaf92f4` F1 | `[test]` `FAIL 1 shape … 11 generated`, **exit 1**. Both the stderr harvest and `check_readable` fire |
| Malformed `figures.yaml` renders `CHECKER CRASHED` in the hook, not a blank | `1787905` F6 | `[test]` hook string reproduced: `staleness: CHECKER CRASHED (exit 1) - no PASS or FAIL line` |
| `merge-manifests.py --check` byte-compares and names the first differing line; `check-staleness.py` runs it | `e30d3d8` | `[test]` appended a row to `MANIFEST.csv` → `PROBLEM: MANIFEST.csv does not match its fragments, first difference at line 100`, and `check-staleness` reports `1 generated`, exit 1 |
| `merge-manifests.py` checks **before** writing | `e30d3d8` | `[test]` corrupted `.manifest-R6.csv`'s header → `REFUSING TO WRITE`, exit 1, `MANIFEST.csv` still 99 lines |
| `check-conservation.py` exits non-zero and sees a tail loss | `1787905` F7 | `[test]` deleted the last 7 words of a page → `TAIL: the source's last 8 words are not in any destination`, **exit 1** |
| `MIN_CORPUS_FILES` raised 30 → 100 | `1787905` F10 | `[repo] tools/check-staleness.py:53` |
| `check_circuits` fails on a dangling refdes, fig and circuit id | `07c7ae8` | `[test]` all three named individually, exit 1 |
| `check_sections` and `check_links` bite | `9fc779a`, `f3876be` | `[test]` injected `§99` and a dead link → both reported, exit 1 |
| `verify-datasheets.py` resolves corpus-cited paths | `1c1155f` | `[test]` renamed a cited path → `CORPUS PATHS THAT DO NOT RESOLVE (3) of 127 cited`, exit 1 |
| Tool wiring assertion | `9310848` | `[repo] tools/check-staleness.py:576-592`, present and running |

**Data and structure — measured at HEAD**

- **23 circuit directories, 294 declared edges** — `refdes 126, fig 87,
  circuit 50, adr 31`, matching `[git] 07c7ae8` exactly. All 23 `circuit.yaml`
  open with the `SEEDED, NOT VERIFIED` banner `[git] 4ecc17e` promised; none
  is missing it. No board page has a `circuit.yaml`. `[calc]`
- **`bom.csv`**: 139 lines, **139 CRLF, 0 bare LF**, 138 rows × 11 columns,
  `unplaced.csv` 50 rows. The row **set** is byte-for-byte identical across
  `c483829` (0 lost, 0 added) and the `ref` set is unchanged from `c483829^`
  to HEAD. `[calc]` `merge-bom.py --check` and `merge-manifests.py --check`
  both clean.
- **Manifest fragments untouched** — all eight `.manifest-R*.csv` blobs are
  identical from `b631987^` to HEAD, as `[git] b631987` required. `[calc]`
- **Conservation re-run at HEAD**, not at the split commit: `carrier.md` from
  `fbf040c^` against all 16 current `carrier/` + `interfaces/` files gives
  **4 gaps, and all four are legitimate** — three are the datasheet path
  rewrites from `1c1155f`, one is the `cluster-boards.md §4` →
  `key-marker-and-bits.md` repoint from the split. No text was lost by any
  later commit. `[test]`
- **ADR index** — all 14 rows agree with their target's `**Status:**` line.
  `a973267` holds. `[calc]` (0008's row drops "(base, not Plus)"; harmless.)
- **`0.437 V` / `0.579 V`** (`6602b43`) — both now appear only inside
  refutation text; `0.573 V` is stated by its owner
  `breath-receive-stage.md:114` and nowhere else live. ADR 0006 and `bom.csv`,
  the two the grep-first rule caught, are both clean. `[calc]`
- **`0.00018` / `0.00027` / `0.00029`** (`c4fb614`) — all three only in
  refutation text; `0.00044` in the owner `power-entry.md:104` and the
  register. The `D-REVPOL` BOM note carries a correctly-formed append-only
  correction. `[calc]`
- **`sensor-full-scale`** — ADR 0003 now spells the coefficient `0.053` with
  the middle dot (`docs/decisions/0003-breath-sensing-path.md:123,436`), the
  one-character escape `c4fb614` describes. `[repo]`
- **`mod-reference`** (`d6146aa`) — `mod-channels.md:197-200` cites the figure
  and states `1.33 mA` with `[calc: 3.3333/2500]` and the refutation in place;
  the drawing at line 38 agrees at `~1.3 mA`. `[repo]`
- **`loop-budget`** (`eaf92f4` F4) — `latency-budget.md:148` states
  `196–241 µs of 250 µs`; the superseded `136 µs` / `54 % duty` survive only
  inside the blockquote that refutes them, and `291 µs with driver defaults`
  is stated. No other corpus page restates the comfortable version. `[calc]`
- **`pitch-stage` orphan table** (`14d2ccd`) — the follow-up it promised
  *did* land: the four headerless rows are now in
  `hardware/module/pitch-stage/notes.md:43-64` under *"The superseded accuracy
  table"*, and `pitch-stage.md:298` points at them. `[repo]`
- **`repo-maintenance.md` §4** (`d71488e`) — correctly describes `bom.csv` as
  generated, names `merge-bom.py`, and its "Validate … after any edit" bullet
  is re-scoped to what `merge-bom.py` does. `unplaced.csv` is now named in
  four Markdown files. `[repo]`
- **`README.md`** (`1787905` F2, `a973267`) — no "split by board", one licence
  section, `datasheets/` and `docs/review/` present in the layout tree.
  `[repo]`
- **The three new index pages** (`fcd56e6`) — `hardware/README.md`,
  `module/module.md`, `interfaces/README.md` exist; `module.md` lists all 12
  module circuits and restates no tracked value; `carrier.md` and
  `cluster-boards.md` likewise index all of theirs. `module.md`'s claim that
  `unplaced.csv` holds the DAC, the in-amp and the LM317 is true
  (`U-DAC`, `U-DIFFRX`, `U-REG-DAC`). `[calc]`
- **`§2` → "stage 2"** (`9fc779a`) — both sim decks now name the stage the way
  `pcb-pipeline.md` titles it. `[repo]`
- **Interfaces `End` column** (`036b182`) — present on all three crossing
  pages. `[repo]`
- **Hook wording** (`1787905` F6) — the hook writes the terse summary to
  `.staleness-report.txt` (83 bytes) and the detail lands in
  `.staleness/report.txt` (6.6 kB). The two halves now agree.
  `[repo] .claude/settings.json` `[calc]`
- **`check-staleness.py` clean at HEAD**: `PASS … corpus 121 files, 23
  circuits | 5 unresolved (tracked)`, exit 0. `[test]`

---

## Not verified — and why

**Anything whose evidence is inside `docs/review/**`.** The cold rule bars me
from reading it, so I did not open those files or `git show` their contents.
That leaves these claims **unaudited, not cleared**:

- `[git] 21e2ea3` — *"97.2% of the original word-mass present verbatim"*, the
  blob-SHA comparison across 87 datasheets, the sub-8-word structural diff,
  and *"497 words in 49 runs, 1.57%"* of duplication.
- `[git] 4ecc17e` / `2701647` / `aa2b89f` — `STATUS.md`'s *"eight named pieces
  of debt"*, the record of the six own-defects, and whether the stale Phase B
  section really was replaced with a note rather than deleted. I verified the
  one claim in `aa2b89f` that is checkable from outside: `4ecc17e`'s
  *"`sensor-full-scale` … is restated six times right now"* is **exactly
  right** at six. `[calc]`
- `[git] 81fad55` / `d88837b` / `453a3b3` / `68e9e1a` — per-agent *"0 REAL
  GAPS"* claims. I re-ran conservation at HEAD for the largest split
  (`carrier.md`, 8 709 words → 16 files) and it holds; I did not re-run the
  other six.
- `[git] 3473436` / `44697f9` — D1/D2/D3 findings and the `VERIFIED.md`
  entries recording which were checked by hand.

**`tools/rewrite-paths.py --invert`** (`8ef7979`, `8bb7366`) — the Phase A
inversion proof. I did not re-run it, because C1-3 shows the map it runs
against is a Phase-A snapshot; re-running it at HEAD would measure the map's
staleness, not the rewrite's correctness. It was a valid proof at `a9f647a`.
Whoever closes C1-3 should re-run it after, not before.

---

## Recommended order

1. **C1-1** — fix `check_owners`' tokeniser before anything else relies on it
   again. Three owner repointings this session rest on it, and the table in
   C1-1 is the acceptance test.
2. **C1-2**, **C1-4** — two half-landed fixes from `f16b72b`, both cheap, both
   in the "filed as handled" class `CLAUDE.md` calls worse than a wrong
   finding.
3. **C1-3** — decide whether the map is regenerated or §7 is re-scoped, then
   say which in `repo-maintenance.md`.
4. **C1-5**, **C1-6**, **C1-7** — three stale counts, one line each.
5. **C1-8**, **C1-9** — one filter entry and one word.
