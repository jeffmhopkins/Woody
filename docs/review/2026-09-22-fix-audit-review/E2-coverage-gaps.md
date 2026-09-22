# E2 — what the fix-audit wave did not look at

**Slice:** the complement of the twenty briefs. The parts of
`0e68f25~1..HEAD` no slice examined, the defect classes no slice was asked
about, and whether the twenty slices sliced by fact domain as `CLAUDE.md`
requires.

**Read:** `docs/review/2026-09-22-fix-audit-review/README.md`, all 20 `D*.md`
plus `README.md`, `STATUS.md` and `VERIFIED.md` of
`docs/review/2026-09-22-fix-audit/`, the batch's commit messages, and the
corpus. **No sibling in this round and no earlier wave was read**
`[test] ls docs/review/2026-09-22-fix-audit-review/` returns `README.md` only,
which is the whole of what I opened there.

---

## 0. The denominator moved while I was measuring it — read this first

`[repo] git reflog` — at the start of this session `HEAD` was `0576a95`
("Open round 2"). Partway through it became **`566159e` "Fix the instrument:
the verdict is reproducible again"**, authored `2026-09-22 03:07:25`, touching
`tools/check-staleness.py` (+104/−22 region), `tools/merge-bom.py` and
**`tools/rewrite-paths.py`** — a file that is in no slice's coverage because it
was not in the batch when the batch was defined.

This matters three ways and every measurement below is dated because of it.

1. **The round-2 rules say "Report, do not fix. The corpus is frozen."** The
   instrument was not frozen. `566159e` is fix-order items 1–3 of
   `STATUS.md`, executed while the audit of the report that produced that fix
   order was still running.
2. **`0e68f25~1..HEAD` no longer means what the briefs mean by it.** The
   wave's subject is `0e68f25~1..0576a95`. Everything in this report that
   says "the batch" means that range; everything about `566159e` is labelled.
3. **Two of round 2's three stated premises are now false at `HEAD`**, and a
   reader who takes the round-2 `README.md` at face value will mis-test their
   own findings. See §3.

`[calc]` The wave `README.md` says **"85 corpus files changed, +2,684 /
−1,228"**. Those two numbers have different denominators:
`git diff --stat 0e68f25~1..0576a95 -- . ':(exclude)docs/review'` → **85 files,
+2,657**; adding back the one review file the batch touched
(`docs/review/2026-09-21-pre-merge-review/STATUS.md`, +27) gives **86 files,
+2,684**. The file count excludes a file the line count includes. It is a
small thing and it is the project's signature defect, in the wave's own brief.

---

## 1. The coverage map

**Method.** For each of the 85 files in `0e68f25~1..0576a95` (corpus only), a
slice is counted as *naming* the file if the file's full repository path, or
its basename where that basename is distinctive, or `<parent>/<basename>`
where it is not (`bom.csv`, `circuit.yaml`, `README.md`, `MANIFEST.csv`),
appears in that slice's report `[test]` script over the 20 reports. **Naming
is a ceiling on examination, not a floor** — a slice that names
`config/figures.yaml` twelve times may still not have read the entry you care
about. Where naming and examination diverge I say so in §2.

| file | churn | slices naming it | n |
|---|---:|---|---:|
| `tools/check-staleness.py` | 546 | D1, D2, D3, D4, D5, D6, D7, D8, D11, D12, D13, D14, D15, D16, D17, D18, D20 | 17 |
| `config/figures.yaml` | 219 | D1, D2, D3, D5, D6, D7, D8, D9, D10, D11, D12, D13, D14, D15, D16, D19, D20 | 17 |
| `docs/reference/path-map-2026-09-21.csv` | 167 | D4, D11, D18, D19 | 4 |
| `docs/reference/pcb-pipeline.md` | 157 | D6, D9, D10, D11, D13, D14, D16, D19, D20 | 9 |
| `docs/reference/repo-maintenance.md` | 156 | D1, D3, D4, D7, D8, D9, D10, D11, D13, D14, D18, D19, D20 | 13 |
| `docs/reference/ks33-geometry.md` | 118 | D2, D6, D7, D8, D11, D14, D15, D19, D20 | 9 |
| `hardware/module/panel/circuit.yaml` | 79 | **none** | 0 |
| `hardware/carrier/power-entry-instrument/circuit.yaml` | 73 | **none** | 0 |
| `hardware/carrier/breath-adc/circuit.yaml` | 71 | **none** | 0 |
| `hardware/module/power-entry/circuit.yaml` | 71 | **none** | 0 |
| `hardware/cluster/key-marker-and-bits/circuit.yaml` | 70 | D6 | 1 |
| `hardware/cluster/key-register/circuit.yaml` | 70 | **none** | 0 |
| `hardware/cluster/key-switch-network/circuit.yaml` | 70 | **none** | 0 |
| `hardware/interfaces/breath-sense-link/circuit.yaml` | 70 | D11 | 1 |
| `hardware/module/breath-receive-stage/circuit.yaml` | 70 | **none** | 0 |
| `hardware/module/link-supervision/circuit.yaml` | 70 | D4 | 1 |
| `hardware/module/mod-channels/circuit.yaml` | 70 | **none** | 0 |
| `hardware/module/pitch-stage/circuit.yaml` | 70 | D10, D19 | 2 |
| `hardware/module/umbilical-load-switch/circuit.yaml` | 70 | D6 | 1 |
| `hardware/carrier/breath-excitation-reference/circuit.yaml` | 69 | **none** | 0 |
| `hardware/interfaces/spi-link/circuit.yaml` | 69 | **none** | 0 |
| `hardware/module/digital-and-supervision/circuit.yaml` | 69 | **none** | 0 |
| `hardware/module/panel-led/circuit.yaml` | 69 | **none** | 0 |
| `hardware/carrier/display-and-service-uart/circuit.yaml` | 68 | **none** | 0 |
| `hardware/carrier/led-strip-drive/circuit.yaml` | 68 | **none** | 0 |
| `hardware/interfaces/key-chain-loom/circuit.yaml` | 68 | **none** | 0 |
| `hardware/module/breath-output-stage/circuit.yaml` | 68 | **none** | 0 |
| `hardware/module/dac8568/circuit.yaml` | 68 | D9 | 1 |
| `hardware/module/breath-response-shaper/circuit.yaml` | 67 | **none** | 0 |
| `hardware/cluster/cluster-boards.md` | 58 | D1, D4, D10, D14, D19, D20 | 6 |
| `hardware/bom.csv` | 51 | D1, D2, D3, D4, D5, D6, D7, D8, D9, D10, D11, D13, D14, D15, D16, D19, D20 | 17 |
| `docs/reference/latency-budget.md` | 50 | D1, D3, D6, D7, D8, D14, D15, D19, D20 | 9 |
| `hardware/README.md` | 46 | D1, D9, D10, D16, D17, D19, D20 | 7 |
| `tools/check-conservation.py` | 45 | D4, D5, D6, D19 | 4 |
| `hardware/interfaces/breath-sense-link/breath-sense-link.md` | 44 | D1, D6, D8, D9, D10, D13, D15, D16, D17, D19, D20 | 11 |
| `hardware/module/panel/panel.md` | 41 | D4, D6, D9, D10, D12, D19, D20 | 7 |
| `CLAUDE.md` | 38 | D1, D2, D3, D4, D5, D6, D7, D8, D9, D10, D11, D12, D13, D14, D15, D16, D17, D18, D19, D20 | 20 |
| `hardware/module/breath-receive-stage/breath-receive-stage.md` | 35 | D1, D3, D4, D6, D7, D9, D10, D13, D16, D17, D18, D19, D20 | 13 |
| `hardware/module/power-entry/power-entry.md` | 31 | D1, D2, D3, D4, D6, D7, D9, D10, D16, D17, D18, D19, D20 | 13 |
| `README.md` | 25 | D1, D4, D5, D7, D8, D9, D10, D11, D12, D13, D14, D15, D16, D17, D18, D19, D20 | 17 |
| `tools/merge-bom.py` | 23 | D1, D2, D3, D4, D5, D9, D10, D12, D13, D16, D18, D19, D20 | 13 |
| `docs/decisions/0006-cv-channel-allocation.md` | 21 | D3, D4, D10, D11 | 4 |
| `docs/decisions/0014-lighting.md` | 21 | D9, D13 | 2 |
| `hardware/module/digital-and-supervision/digital-and-supervision.md` | 21 | D4, D6, D10, D12, D16, D19, D20 | 7 |
| `hardware/interfaces/spi-link/spi-link.md` | 20 | D1, D3, D5, D6, D12, D16, D17, D19, D20 | 9 |
| `hardware/module/breath-output-stage/breath-output-stage.md` | 20 | D2, D6, D7, D9, D10, D13, D16, D17, D19, D20 | 10 |
| `hardware/unplaced.csv` | 20 | D2, D4, D6, D7, D9, D10, D11, D13, D19, D20 | 10 |
| `hardware/carrier/power-entry-instrument/power-entry-instrument.md` | 17 | D13, D16, D19 | 3 |
| `hardware/cluster/key-register/key-register.md` | 17 | D8, D16, D19 | 3 |
| `config/key-layout.yaml` | 16 | D2, D6, D14, D20 | 4 |
| `docs/decisions/0002-key-switches-and-mounting.md` | 16 | D7, D8, D14, D15 | 4 |
| `hardware/carrier/breath-adc/breath-adc.md` | 15 | D2, D6, D8, D13, D15, D16, D17, D19 | 8 |
| `hardware/module/mod-channels/mod-channels.md` | 15 | D3, D6, D9, D12, D15 | 5 |
| `docs/decisions/0004-cv-interface-module.md` | 13 | D2, D3, D5, D6, D7, D9, D10, D12, D19, D20 | 10 |
| `hardware/carrier/breath-excitation-reference/breath-excitation-reference.md` | 13 | D6, D8, D16, D19 | 4 |
| `hardware/carrier/display-and-service-uart/display-and-service-uart.md` | 13 | D16, D19, D20 | 3 |
| `hardware/cluster/key-marker-and-bits/key-marker-and-bits.md` | 13 | D3, D4, D6, D14 | 4 |
| `hardware/cluster/key-switch-network/key-switch-network.md` | 13 | D1, D4, D6, D7, D8, D13, D14, D15, D20 | 9 |
| `hardware/interfaces/key-chain-loom/key-chain-loom.md` | 13 | D6, D7, D8, D16, D17, D20 | 6 |
| `hardware/module/pitch-stage/pitch-stage.md` | 13 | D4, D6, D9, D12, D15, D16, D17, D19, D20 | 9 |
| `hardware/carrier/led-strip-drive/led-strip-drive.md` | 11 | D9, D13, D16, D17 | 4 |
| `hardware/module/dac8568/dac8568.md` | 10 | D7, D10, D11, D12, D16, D17, D19 | 7 |
| `hardware/module/module.md` | 10 | D2, D3, D5, D6, D7, D9, D10, D12, D19, D20 | 10 |
| `hardware/module/breath-response-shaper/breath-response-shaper.md` | 9 | D7, D17, D20 | 3 |
| `hardware/module/link-supervision/link-supervision.md` | 9 | D4, D10, D17 | 3 |
| `hardware/module/panel-led/panel-led.md` | 8 | D17, D18, D19 | 3 |
| `docs/decisions/0005-power-architecture.md` | 7 | D10 | 1 |
| `hardware/module/power-entry/bom.csv` | 7 | D3, D6, D9, D10, D19 | 5 |
| `hardware/module/umbilical-load-switch/umbilical-load-switch.md` | 7 | D1, D2, D6, D9, D10, D16, D17, D18 | 8 |
| `hardware/interfaces/breath-sense-link/bom.csv` | 5 | D7, D8, D11, D13, D17 | 5 |
| `ROADMAP.md` | 4 | D4, D7, D8, D11, D12, D13, D14, D15, D16, D19, D20 | 11 |
| `datasheets/.manifest-R9.csv` | 4 | D4, D10, D11, D18, D19, D20 | 6 |
| `hardware/cluster/key-switch-network/bom.csv` | 4 | D2, D3, D6, D7, D10, D15 | 6 |
| `hardware/module/breath-receive-stage/bom.csv` | 4 | D3, D4, D6, D10, D17, D19, D20 | 7 |
| `datasheets/MANIFEST.csv` | 3 | D1, D4, D5, D6, D8, D10, D11, D12, D13, D14, D18 | 11 |
| `docs/decisions/0003-breath-sensing-path.md` | 3 | D3, D6, D7, D8, D10, D15 | 6 |
| `hardware/carrier/breath-adc/bom.csv` | 2 | D7 | 1 |
| `hardware/module/digital-and-supervision/bom.csv` | 2 | D4, D10 | 2 |
| `hardware/module/panel/bom.csv` | 2 | D4, D7, D9, D19 | 4 |
| `hardware/module/umbilical-load-switch/bom.csv` | 2 | D1, D2, D3, D5, D6, D7, D10 | 7 |
| `hardware/carrier/led-strip-drive/bom.csv` | 1 | D10, D20 | 2 |
| `hardware/module/bom.csv` | 1 | D9, D10, D19, D20 | 4 |
| `hardware/module/dac8568/bom.csv` | 1 | D4, D10, D11 | 3 |
| `hardware/module/panel-led/bom.csv` | 1 | D19 | 1 |
| `hardware/module/pitch-stage/bom.csv` | 1 | D4, D10 | 2 |

*85 files, 3,885 lines of churn. `[test]` `git diff --numstat 0e68f25~1..0576a95 -- . ':(exclude)docs/review'` for the churn, and a script over the 20 reports for the naming.*

### The shape of the gap

`[calc]` from the table above:

| band | files | churn | share of the 3,885-line batch |
|---|---:|---:|---:|
| named by **no** slice | 17 | 1,189 | **30.6 %** |
| named by 1–2 slices | 13 | 453 | 11.7 % |
| named by 3+ slices | 55 | 2,243 | 57.7 % |

**Every one of the seventeen unnamed files is a `hardware/**/circuit.yaml`.**
The other six `circuit.yaml` files are named once or twice each. As a class:
**23 files, 1,607 lines, 41.4 % of the batch's churn**, and the only slices
that opened them are D17 (the edge graph), D19 (the deleted schema rationale)
and D20 (two sentences' presence). There is no other systematic hole — every
non-`circuit.yaml` file in the batch is named by at least one slice, and the
thin end of the distribution (`panel-led/bom.csv`, `module/bom.csv`,
`carrier/breath-adc/bom.csv`) is thin because the edits there are one row each.

The gap is systematic exactly as predicted: the briefs were written from the
pre-merge wave's findings, the pre-merge wave's findings were about *values*,
and `circuit.yaml` carries no values. What it carries instead is a **68-line
prose header, byte-identical in all 23 files** `[test] md5sum of lines 1–30 →
one hash, 23 times`, making six counted factual claims. That header is the
single largest un-reviewed artefact in the batch, and §2.1 shows two of its
claims are wrong.

---

## 2. What is in the gaps

### E2-1 — the 23 `circuit.yaml` headers say "five rows"; the same commit's message says seven

`[repo]` All 23 headers, identically:

> `# the machine-seeded set both wrong and one-sided: five rows named`
> `# module/digital-and-supervision for nets that come from module/dac8568`

`[repo] git log -1 --format=%B 6645fb7` — the commit that wrote those headers:

> Five rows named the pre-split page as the peer for VREFOUT, the DAC channels
> and CLR. **The agent found the finding undercounted by two:**
> breath-receive-stage and breath-sense-link carried the same defect on CLR.

`[test]` Counting the rows at `0e68f25~1` that name `module/digital-and-supervision`
as the peer for a net `module/dac8568` owns:

```
breath-sense-link.md:52      CLR
breath-receive-stage.md:46   CLR
mod-channels.md:26           DAC ch7
mod-channels.md:27           DAC ch2-ch5
mod-channels.md:28           CLR
pitch-stage.md:19            VREFOUT
pitch-stage.md:20            DAC ch1
```

**Seven.** (`dac8568.md:16`'s `SCLK/DIN/SYNC` row also names
digital-and-supervision and is excluded, because that peer is correct — the
74AHCT125 is physically there, and the commit resolved it that way.)

So the corrected count was in the author's hand, in the message of the commit
that wrote the header, and the header kept the pre-correction number — then
that header was copied into **23 files**. This is the defect `CLAUDE.md` opens
with, at its maximum fan-out, and it is invisible to every check in the tree
because `circuit.yaml` prose holds no tracked figure.

### E2-2 — "(the review counted 27 of 49 ...)" is not reproducible from any committed state

`[repo]` Same header, next clause: *"26 of the 50 declared edges existed at
only one end (the review counted 27 of 49 before the day's other edits; the
count was re-measured here)."*

`[test]` `yaml.safe_load` over every `circuit.yaml` at each of the three
revisions in which `circuit.yaml` has ever existed before the rebuild:

```
07c7ae8   23 circuits  50 directed  38 undirected  26 one-sided
4ecc17e   23 circuits  50 directed  38 undirected  26 one-sided
0e68f25~1 23 circuits  50 directed  38 undirected  26 one-sided
```

There is no state of this repository in which the graph was 49 edges with 27
one-sided. The parenthetical is offered as a reconciliation of two
measurements and reconciles nothing; if it refers to a count taken over the
Interfaces tables rather than over `depends_on`, the header does not say so,
and a reader checking it gets 50/26 three times.

**What would settle it:** the pre-merge wave's own report of that count. I did
not read it and may not.

### E2-3 — the Interfaces rewrite deleted the tables' inline links, and `check_links` cannot see that

`[repo] hardware/carrier/power-entry-instrument/power-entry-instrument.md`, 17
lines, entirely the `## Interfaces` table. D16 read this table line by line for
net names and D17 for edges, and between them the rewrite is well covered on
the merits: `J-UMB pin 3 +12V` → `UMBILICAL +12V at J-UMB` with peer
`module/umbilical-load-switch`, `PWR_GND` re-typed `in` → `ref`, and the
`PWR_GND pour` row gaining the four carrier peers that make the graph
reciprocal. All of that is sound.

What neither brief covered: **the rewrite deleted the table's inline markdown
links.** `` [`led-strip-drive`](../led-strip-drive/led-strip-drive.md) ``
became the bare id `carrier/led-strip-drive`, four times on this page alone,
and the same substitution runs through the Interfaces tables generally
`[repo] breath-response-shaper.md` same commit. That is the notation
unification `6645fb7` intended, so it is not an error — but it is invisible to
every check, because `check_links` proves that links which *exist* resolve.
**A link that was removed is not a broken link.** This is the same fail-open
shape the batch spent itself closing on the value layer, sitting unexamined on
the navigation layer, and nothing in the wave (D4 and D5 own `check_links`)
names it.

### E2-4 — `docs/review/2026-09-21-pre-merge-review/STATUS.md`: the heading contradicts its own table, and the cold rule made it unreadable

`[repo] 04b5208` added 27 lines to that file — inside the batch under review.
The added block opens:

> ## Outcome: **all five items done**, 2026-09-21

and its own table, five rows down:

> | 5 | Adjudicate the umbilical topology | **NOT done, and deliberately.** ... |

A heading and the table two lines beneath it, in one 27-line addition,
disagreeing about the same fact. **No slice could report it**: the wave's cold
rule is *"No agent may read anything under `docs/review/**`"*, and this file is
under `docs/review/**` **and** in the diff. One file of the 86 was
structurally excluded from all twenty slices by the rule that makes them work.

Secondary, and offered as a tension rather than a defect: `CLAUDE.md` §6 says
`docs/review/` records *"are not the corpus and must never be 'corrected'"*,
while `CLAUDE.md`'s own "Where the details live" says a wave's `STATUS.md`
records what landed. The added block argues both sides in one sentence —
*"Kept as written, because a wave's STATUS is a record of what it found and
not of what happened next"* — immediately above a section about what happened
next. Somebody should decide which it is; I do not think this report is the
place.

### E2-5 — the seventeen `circuit.yaml` files, audited for what D17 and D19 did not cover

Stated plainly because it is most of the gap: **the `circuit.yaml` data is
sound.** `[test]` re-measured independently of D17: 23 circuits, 23 unique ids,
96 directed / 48 undirected `circuit:` edges, 0 one-sided, 0 self-loops, 0
isolated — identical to D17's numbers and to the header's claim. Nine circuits
declared no `circuit:` edge before the rebuild (all five `carrier/**`, all
three `cluster/**`, `module/panel`) `[test]`, exactly as the header says.
The header's "48 edges" and "every one declared from both ends" hold.

The defects in the class are E2-1 and E2-2, both in prose, both replicated 23
times, and both of a kind no brief in the wave was pointed at.

---

## 3. The defect classes nobody was briefed on

### E2-6 — the checker's verdict at `HEAD` is **FAIL, 8 live stale values**, and it is now deterministic

Round 2's `README.md` tells every slice two things to hold as established:
*"Ten identical runs with a real violation live gave 6 PASS / 4 FAIL"*, and
*"all 68 forbidden-pattern matches are currently exempted — the live list is
empty."* Both were true of `0576a95`. **Neither is true of `HEAD`**, because
`566159e` landed between the opening of this round and now.

`[test]` `python3 tools/check-staleness.py`, twelve consecutive runs at `HEAD`,
clean tree `[test] git status --porcelain` empty:

```
FAIL 0 shape + 0 owners + ... + 8 stale + 0 bom      x12, identical
```

`[test]` and across twelve **fixed** hash seeds, `PYTHONHASHSEED=0..11`:
identical output, twelve times. The nondeterminism is gone and the verdict is
**FAIL**.

The practical warning for my siblings: a slice that opened with "the checker
reports PASS" and re-ran to confirm will now get FAIL, and may read its own
tooling as broken. It is not. The instrument changed underneath the round.

### E2-7 — six of those eight live hits are false positives, and one of them fires on a sentence its own cell calls true

`[test] .staleness/report.txt` at `HEAD`, three figures:

| figure | file:line | pattern | my verdict |
|---|---|---|---|
| `chain-connectors` = 8 | `hardware/bom.csv:30`, `hardware/carrier/bom.csv:6` | `five connectors must match` | **real** |
| `loadswitch-timer` = 10 uF | `hardware/bom.csv:71`, `.../umbilical-load-switch/bom.csv:10` | `2.4x the ~62ms`; `the reviewers disagree and the datasheet decides` | **false positive ×4** |
| `panel-toggle-hole` | `hardware/bom.csv:63`, `.../umbilical-load-switch/bom.csv:2` | `6.00 and 6.35 need different holes` | **false positive ×2** |

**`chain-connectors` is real** and I confirm it independently of anyone:
`[repo] key-chain-loom.md:88` *"EIGHT connectors, not five"*, `:252` *"eight
connectors across five boards rather than five"*, register `value: 8` with
derivation `carrier 1, RT 2, RH 2, LT 2, LH 1`. The `WIRE-LOOM` cell says
*"five connectors must match: one on the carrier and one per cluster board"*
and carries **no refutation anywhere in the cell** `[test]` full 923-character
row read. D1 and D3 both filed this and both are right.

**`panel-toggle-hole` is not a defect and the pattern is a trap.**
`[repo] hardware/bom.csv:63` is a 5,538-character cell. The pattern fires at
~character 1,100. At ~character 2,900 the *same cell* says:

> SO TWO PARTS ARE BOTH LEGITIMATELY '6 mm' AND NEED DIFFERENT HOLES —
> **exactly the trap this row warned about.**

The later text does not retire the sentence the pattern matches; it
**endorses** it. `CLAUDE.md`: *"A pattern that fires on a correct sentence is
worse than no pattern, because its cheapest fix is to make the sentence
wrong."* D3 enumerated this exemption as `E27`/`E63` and judged it **ok**;
`566159e` overruled that judgement without citing it, and its commit message
reports all three figures as *"Three distinct defects"*.

**`loadswitch-timer` ×4 is the same shape, weaker.** The cell narrates the
dispute and then resolves it in a `| 2026-09-21` segment 900 characters later:
*"Both reviewers were half right exactly as this row already said"*, *"THE
150ms TARGET WAS NEVER THE SPEC"*. D3 marked these **marginal** and listed
them as LIVE, so D3 and I differ on two of the four and agree the question is
open. Note also that `the reviewers disagree and the datasheet decides` is a
**forbidden pattern containing no value at all** — `CLAUDE.md` §5 says the
checker greps for values; a narrative sentence in a `forbidden` list is a
category error whichever way this is resolved.

**This is the interaction class the brief asked for.** `df22096` added those
narrative patterns; that was correct *given* the bare-ISO-date refutation
marker then in force, which exempted the whole dated cell. `566159e` removed
the bare-date marker; that was correct, and demonstrated by injection. **Two
individually-correct edits, and together they produce six failing assertions
about correct text.** Neither edit's author could see it, because the fact
lives in the product of the two.

### E2-8 — the `PreToolUse` hook does not do what `CLAUDE.md` says it does

`[repo] .claude/settings.json`:

```json
"matcher": "Bash",
"command": "o=$(python3 \"$CLAUDE_PROJECT_DIR/tools/check-staleness.py\" ...)",
"if": "Bash(git commit *)",
```

`CLAUDE.md` §2: *"A `PreToolUse` hook runs the checker before every `git
commit`."* `[test]` During this session the hook fired on `ls`, `cat`,
`sed -n`, `git status`, `git diff`, `find`, and every `python3` invocation —
**every Bash tool call, none of them a commit.** The `if` key is not gating
anything.

Consequences, in order of cost:

1. Every Bash call in this repository pays a full corpus scan. It is the
   reason a twenty-iteration loop in this session exceeded a 120-second
   timeout.
2. The **only** statement in `CLAUDE.md` about when the check runs is wrong,
   and `CLAUDE.md` is the document every cold agent is required to read first.
3. The hook emits `additionalContext` and never `permissionDecision`, so a
   `FAIL` **does not block a commit** — it is advisory always, not only in
   D1's hang case. D1's *"the commit is not gated"* reads as a property of the
   hang; it is a property of the hook.

`[test]` Three slices name the hook. D5 exercises its shell pipeline by
retyping it, which proves the pipeline and cannot see the `if`; D4 notes what
the hook does *not* run (`check-conservation.py`); D1 attacks it with a
symlink-induced hang. None tests **when** it fires. This is the brief's
"examined by one slice as an afterthought" case, confirmed, and the afterthought
missed the first-order fact.

### E2-9 — `tools/**` is outside the corpus by construction, so every figure in a docstring is unchecked — and two are stale

`CLAUDE.md` defines the corpus as `hardware/**`, `docs/decisions/**`,
`docs/reference/**`, `config/**`, `firmware/**`, `README.md`, `ROADMAP.md`.
**`tools/**` is not in it**, twice over `[repo] check-staleness.py:30-32` — `CORPUS_DIRS = ["hardware", "docs/decisions", "docs/reference", "config", "firmware"]` does not name it, and `corpus_files()` collects only `.md/.csv/.yaml/.yml` in any case `[repo] :144`.
The docstrings are nonetheless load-bearing: `merge-bom.py`'s carries THE
ASSIGNMENT RULE that D9 and D10 both adjudicate rows against.

| claim | `[test]` measured at `HEAD` | verdict |
|---|---|---|
| `merge-bom.py` docstring: *"a silent re-sort of **138 rows**"* | `merge-bom.py --check` → `checked **139** rows from 26 fragments`; `csv` count → 139 data rows | **stale — moved by this very batch** |
| `merge-bom.py` docstring: *"the most-cited file in the repository — **37 backtick references**"* | `` `bom.csv` `` 50 + `` `hardware/bom.csv` `` 16 = **66** over the corpus (62 at `0e68f25~1`) | **not reproducible under any reading I could construct** |
| `check-conservation.py`: *"Usage: **conserve.py** \<rev\> ..."* | the file is `tools/check-conservation.py`; `conserve.py` exists nowhere `[test] grep -rn 'conserve\.py'` → this line only | **stale tool name in the usage line** |
| `merge-bom.py` docstring: *"THE ASSIGNMENT RULE, **from D4**"* | this wave also has a `D4` (`D4-other-tools.md`), about a different subject | **ambiguous reference**, cheap to disambiguate |

The 139-vs-138 is the exact defect `CLAUDE.md` opens with — *"a value changes,
and the documents derived from it do not follow"* — sitting in the tool that
generates the most-cited file in the repository, and structurally unreachable
by the check built to find it.

### E2-10 — `check-conservation.py`'s new multiplicity test penalises the deduplication rule 1 mandates

`[repo] tools/check-conservation.py`, added by the batch:

> A PASSAGE STATED TWICE CAN BE HALVED FOR FREE ... Compare MULTIPLICITY, not
> just presence.

and `sys.exit(1 if (real or tail_lost or head_lost or halved) else 0)`.

The fix is right for its motivating case — a reviewer deleted one of two copies
of a grounding warning and got `REAL GAPS: 0`. But `CLAUDE.md` rule 1 is
*"state it once and cite it"*, and the batch acted on it: `0576a95`'s own
`hardware/README.md` change *"the `## Interfaces` definition that sat inline in
all 23 circuit pages now lives there once and is cited"* is a 23→1 reduction in
multiplicity. **The tool that proves a split conserved content now exits 1 on
the correction the project's headline rule prescribes.** It reports the
thinning rather than failing silently, which is the right half of the
behaviour; the exit code is the wrong half. Nobody was briefed on the tension
because D19 audits conservation's *findings* and D4/D5 audit the other tools'
*fail-opens*, and this is neither.

### E2-11 — the commit messages as a corpus: 9,389 words, one slice sampling

`[calc] git log --format=%B 0e68f25~1..0576a95 | wc -w` → **9,389 words**
across 27 messages — larger than any single reference document in the tree, and
they are where the batch states what it did. Only D20 sampled them. I tested
five checkable claims:

| claim | source | `[test]` | verdict |
|---|---|---|---|
| *"50 directed edges with 26 one-sided, and nine circuits declaring no edge at all"* | `6645fb7` | yaml load at `0e68f25~1`: 50 / 26 / 9 | **confirmed** |
| *"now 96 directed, ZERO one-sided, ZERO isolated"* | `6645fb7` | yaml load at `HEAD`: 96 / 0 / 0 | **confirmed** |
| *"Dir settled at five values"* | `6645fb7` | header-indexed census over all 23 Interfaces tables: `in` 49, `—` 43, `out` 41, `ref` 27, `in/out` 4 — **exactly 5** | **confirmed** |
| *"Five rows named the pre-split page ... undercounted by two"* | `6645fb7` | 7 rows, enumerated in E2-1 | **confirmed in the message, contradicted by the header the same commit wrote** |
| *"The eight forbidden-list escapes"* | `df22096` subject | the body enumerates **seven** figures (`sensor-full-scale`, `inamp-full-scale`, `panel-height-budget`, `key-press-time`, `key-release-time`, `chain-conductors`, `panel-width`) | **unresolved** — it reaches eight only if `sensor-full-scale`'s two new spellings count as two escapes; the message does not say |

Four of five confirmed, which is a better hit rate than the corpus and is worth
saying. The commit-message corpus is not a problem area; it is an **unmeasured**
one, and the one defect it holds (E2-1) is the batch's worst single-fact
fan-out.

### E2-12 — `firmware/` carries no obligation from the batch, and one figure did not reach it

`firmware/` is **in** the corpus per `CLAUDE.md` and holds exactly one file
`[test] ls firmware/` → `README.md`. The batch touched it not at all.

Reading it against the batch:

- **Confirmed sound.** *"The latency budget already books six DAC words per
  pass while five are written"* `[repo] firmware/README.md` against
  `[repo] latency-budget.md:176` *"six DAC channels"* and
  `[repo] 0006:272` *"already assumes six DAC channels serviced every 250 µs
  pass"*. The batch rebuilt the latency budget (+50 lines) and this survived.
  The `3.3333 V` / `+11.45 V` mod-reference chain also still matches
  `[repo] 0006:105`.
- **Did not reach.** The batch newly tracked **`ks33-contact-bounce` = "5 ms
  max at 16 in/sec actuation"**, read off a banked Gateron drawing, and
  rewrote `ks33-geometry.md` and ADR 0002 around the discovery that *"the
  bounce figure is vendor-published and was recorded here as unpublished
  through four review waves"* `[repo] ks33-geometry.md:206,211`.
  `firmware/README.md` still says the release window is set *"from **measured**
  KS-33 bounce (milestone M1), not from the conventional 20 ms"* and **cites
  no figure**. That is not false — M1 is still the plan — but it is the one
  page in the corpus that tells a firmware author where the debounce number
  comes from, and the corpus acquired a published bound for it in this batch
  without that page learning of it. **Fifteen of D20's nineteen defects are
  "on a page that cites the page that was fixed"; this is the sixteenth, on the
  only page in a directory no brief mentioned.**

`ks33-contact-bounce` is also one of the eight figures the checker reports as
**UNCHECKABLE** — *"value '5 ms max at 16 in/sec actuation' has no token
distinctive enough to locate — owner `docs/reference/ks33-geometry.md` is
UNCHECKED"* `[test] .staleness/report.txt`. So the figure the batch was
proudest of recovering is one the instrument cannot verify and one its reader
does not cite.

### E2-13 — `datasheets/`: `.moves.csv` and `README.md` are covered; the manifest arithmetic in `STATUS.md` is not

`[test]` `.moves.csv` is named by D11 (10×), D18 (13×), D4, D19, D20;
`datasheets/README.md` by D11 (9×). Both are genuinely covered and I add
nothing.

The uncovered part is downstream. `[test]` at `HEAD`:

```
python3 tools/merge-manifests.py --check  ->  101 rows from 9 fragments |
        78 ok, 22 blocked, 1 other;  DE-DUPLICATED: 1 row(s)
python3 tools/verify-datasheets.py        ->  78 verified, 23 blocked, 0 problems
csv:  101 rows | 78 with a file | 76 DISTINCT files
```

`STATUS.md` reports this as *"**76 manifest rows against 76 files, both
ways**"*. It is 78 rows against 76 files; the bijection is on *files*, not on
rows. **D11 got this exactly right** — *"`verify-datasheets.py`'s '78 verified'
counts rows, not documents: 76 files, two counted twice. R9 raised that number
by one while banking nothing"* — and the wave's own summary flattened the
correction back out. Worth recording because `STATUS.md` is the document a
reader reaches for, and it restates a number its source report had already
qualified. The batch's `.manifest-R9.csv` is what created the second duplicate
(`DAC8568ICPW` → the same `analog/DAC8568CIPW.pdf` and the same SHA-256 as
`DAC8568CIPW`), deliberately, as a `SUPERSEDES the part string` record.

### E2-14 — things the wave called clean on one tool run, re-run

`[test]` at `HEAD`, three runs each unless noted:

| claim | re-run | verdict |
|---|---|---|
| BOM mechanics byte-exact | `merge-bom.py --check` ×3 → `139 rows from 26 fragments \| 0 problems`, rc 0 | **holds** (and note: 139, not the 138 its own docstring states) |
| datasheet bank intact | `verify-datasheets.py` → `0 problems` | **holds** |
| manifest generated cleanly | `merge-manifests.py --check` → clean, with the de-duplication and 10 superseded-BLOCKED notices it is designed to announce | **holds** |
| checker green | ×12 runs + ×12 fixed seeds → **FAIL, 8 stale** | **does not hold at `HEAD`** (E2-6) |

Three of four reproduce. The one that does not is the one the wave already said
not to trust.

---

## 4. Did the twenty slices slice by fact domain?

`CLAUDE.md`: *"Slice by fact domain, not by file. The defect is one fact across
five files. Slicing by file gets five agents reporting one defect from one
side."* The wave's own `README.md` repeats it verbatim.

**Mostly yes, and three exceptions, of which one cost something.**

**Genuinely fact-domain slices.** D3 (refutation exemptions), D6 (figure
owners), D7 (forbidden patterns), D8 (new figures), D16 (net names), D17 (the
dependency graph), D19 (conservation), D20 (completeness). D16 and D17 are the
clearest case of the method working: both read the same 23 Interfaces tables
from different questions and neither duplicates the other.

**Sliced by file.** D15 is *"the latency budget"* — one file, and its own
conclusion is about that file's reach: *"The fix was correct arithmetic in one
file, and the register was not extended to hold any of it in place."* D18 is
*"the path map"* — one CSV. Both produced good work; the risk is structural,
not realised here, and `STATUS.md` promoting D15's sentence to the wave's
one-line diagnosis is a slice-by-file report correctly diagnosing slicing by
file.

**The one that cost something: the `|`-dated BOM notes cell.**
`STATUS.md`'s own fix order, item 2, ends: *"decide whether a `|`-appended
dated segment in a BOM notes cell is a refutation convention, and if it is,
write it down."* That is a live open question at the end of a twenty-slice
wave, and it is open because it fell **between** slices, not through one:

- D3 owns refutation and saw the cells from the **checker's** side — it
  enumerated all 68 exemptions and graded them, calling `panel-toggle-hole`
  ok and `loadswitch-timer` marginal, with no brief to ask what the BOM's
  authors intended by the `|`.
- D9, D10 and D11 own the BOM and saw the same cells from the **document's**
  side — rows, refdes, buildability, provenance — with no brief to ask how a
  cell reads to a grep.

Neither slice was wrong. The fact — *what does `| <date>:` mean in a notes
cell* — has two sides and belonged to neither. Six days of false positives
(E2-7) are now live in the tree because the question was left open and
`566159e` answered half of it.

A second, smaller instance: **`hardware/**/circuit.yaml`**. Three slices
touched it and each from one artefact's side — D17 the edges, D19 the deleted
rationale, D20 the presence of two sentences. The defect that was actually
there (E2-1, E2-2) is in the *prose between* those, replicated 23 times, and it
is precisely "one fact across twenty-three files" with no slice pointed at the
fact.

---

## 5. Where the reports were right

`CLAUDE.md`: *"A slice that only lists errors gives no way to tell a careful
report from a lucky one."*

- **D17** is the deepest work in the wave. Its 96/48/0/0, its 23/23 set-equality
  of declared edges against Peer columns, and its warning that the three
  `interfaces/**` tables carry a sixth `End` column so a fixed column index is
  wrong — I reproduced all three independently, and I made the column-index
  mistake myself first and got a contaminated Dir census for it.
- **D1 and D3** are both right about `WIRE-LOOM`, independently, and the fixed
  checker now agrees with them.
- **D11** is right that `verify-datasheets.py`'s 78 counts rows, not documents,
  and right that R9 raised it without banking anything — a correction
  `STATUS.md` then lost.
- **D3's exemption table** is the most useful artefact in the wave for anyone
  fixing the refutation vocabulary: 68 rows with signed character distances,
  graded by hand. That two of its `ok` verdicts were overruled by `566159e`
  without argument is a defect in the fix, not in D3.
- **D13** caught the `R-ADCDIV` note rewrite (`"Sensor reaches 4.7V"` →
  `"reaches sensor-full-scale"`). I opened this expecting to file it as a
  number deleted from a build document and **withdrew it**: citing a figure id
  inside a BOM notes cell is an established convention here, 26 cells do it
  `[test]`, and D13 had already logged the change.

---

## 6. What would settle the open ones

- **E2-2** (`27 of 49`): the pre-merge wave's own report of that count.
  I may not read it.
- **E2-7** (`loadswitch-timer`): a decision on `| <date>:` as a refutation
  convention, which `STATUS.md` already asks for. I differ from D3 on
  `panel-toggle-hole` only.
- **E2-11** (`eight escapes`): whether the author counts
  `sensor-full-scale`'s two new spellings as two.
- **E2-8** (the hook `if`): the harness's own hook schema. My evidence is
  behavioural — the hook fired on every Bash call in this session — and that is
  sufficient to show `CLAUDE.md` §2 is wrong about *when*, whatever the reason.

## 7. Filed against nodes, per the rule

| # | node / artefact | claim |
|---|---|---|
| E2-1 | all 23 `circuit.yaml` headers | "five rows" is seven |
| E2-2 | all 23 `circuit.yaml` headers | "27 of 49" unreproducible |
| E2-3 | Interfaces tables, all 23 | inline links deleted; `check_links` cannot see it |
| E2-4 | `docs/review/2026-09-21-pre-merge-review/STATUS.md` | heading contradicts its table; excluded from every slice by the cold rule |
| E2-6 | `tools/check-staleness.py` @ `HEAD` | FAIL 8 stale, deterministic; round 2's premises are stale |
| E2-7 | `C-TIMER-LOADSW`, `SW-POWER` | 6 of 8 live hits are false positives; product of two correct edits |
| E2-8 | `.claude/settings.json` | `if` does not gate; `CLAUDE.md` §2 wrong; hook never blocks |
| E2-9 | `tools/merge-bom.py`, `tools/check-conservation.py` | docstring figures stale and unreachable by any check |
| E2-10 | `tools/check-conservation.py` | multiplicity test exits 1 on the deduplication rule 1 requires |
| E2-11 | commit-message corpus | 4 of 5 sampled claims confirmed; E2-1 is the exception |
| E2-12 | `firmware/README.md` | `ks33-contact-bounce` did not reach it |
| E2-13 | `datasheets/MANIFEST.csv` | 78 rows / 76 files; `STATUS.md` restates it as 76/76 |
