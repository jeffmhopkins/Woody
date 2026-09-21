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
