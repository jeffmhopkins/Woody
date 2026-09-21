# Verified by hand — restructure design wave

A report is a claim, not a fact. This file records what was checked against the
corpus by hand, and where an agent was wrong. Checks are listed as they were
made, newest last.

## D1 — circuit inventory

| Claim | Check | Verdict |
|---|---|---|
| `hardware/module/breath-output-stage.md:277-300` is panel geometry misfiled inside a breath response-control section | `sed -n '277,300p'` | **Confirmed.** The range is a block quote headed "The panel goes to 10HP — decided 2026-09-21" carrying 50.50 mm, the one-row-of-three-pots argument, the ≤14 mm knob limit and the tracked figure `panel-height-budget`. None of it is breath response control |
| `hardware/controller/carrier.md:164-211` is a single ASCII drawing spanning three proposed blocks, so `sed -n` cannot split it | `sed -n '164,175p;200,215p'` | **Confirmed.** One fenced block opens at :164 and carries the REF5050 and its buffer (block 2), the breath sense path and analog star (block 3), and the ADC's `VDD/VREF` and `C-ADC-BULK` (block 4). Splitting it means redrawing it, which is not a move |
| `docs/reference/pcb-pipeline.md:115-118` says "one module per schematic page, `module.py` importing the six", so Phase A strands the word "six" | `sed -n '113,118p'` | **Confirmed verbatim.** It is prose, not a tracked figure, so `check-staleness.py` cannot catch it going stale |

**Not yet checked:** the 22-directory inventory itself, the individual line
ranges beyond the three above, and the board-crossing verdicts. Those are
checked when Phase A executes against them, range by range — a range that does
not `sed` cleanly is caught at the moment it is used.

## D3 — staleness paradigm

| Claim | Check | Verdict |
|---|---|---|
| `hardware/bom.csv:97` cites a datasheet path that does not exist | Resolved all 35 distinct `datasheets/` paths cited anywhere in the corpus against disk | **Confirmed, and it is the only one.** The row cited `MF-PSMF010X.pdf`; the banked file is `MF-PSMF010X-polyfuse.pdf`. Fixed in `7deb71f` |
| `check_refdes()` at `tools/check-staleness.py:126-145` is dead code | `grep -n 'check_refdes\|check_bom\|check_figures'` — `main()` calls `check_figures` (:161) and `check_bom` (:162) and nothing else | **Confirmed.** A dependency check has been sitting in the tool, unwired, for its whole life |
| No tool reads `figures.yaml`'s `owner:` field | `grep -rn owner tools/*.py` returns nothing | **Confirmed.** All 33 `owner:` paths could be wrong today and nothing would say so |

**Found independently by D2** (H1), which could not see D3. Two cold agents
reaching the same two holes is the strongest signal this wave produced.

## D2 — directory standard

| Claim | Check | Verdict |
|---|---|---|
| `hardware/module/pitch-stage.md:301-304` is a superseded accuracy table left live | `sed -n '277,306p'` | **Confirmed, and worse than reported.** Four `\|`-rows with no header sit *after* the prose that replaced them, and they **contradict** the live table 12 lines above: `LT5400 ratio tracking ~0.1 cents` against the live `0.027`, `DAC internal reference ~0.5 cents` against the live `0.42`. Neither figure is in `figures.yaml`, so `check-staleness.py` is structurally blind to it |
| Provenance markers are near-absent on the module pages | Counted `[repo]`/`[calc]`/`[web]`/`[from memory]`/`[board-def]` per page | **Confirmed.** `carrier.md` 114 and `cluster-boards.md` 49, against **12 across all six module pages** — four of which have **zero**, including `pitch-stage.md`, the page that owns the tightest error budget in the project |

Note the second row cuts against a `CLAUDE.md` review rule — "an unmarked claim
is a defect in the report" is enforced on *reports* and has never been enforced
on the corpus itself.
