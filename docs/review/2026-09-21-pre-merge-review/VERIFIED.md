# Verified by hand — pre-merge wave

A finding is a claim. This file records what was checked against the corpus
and where an agent was right or wrong. Checked as reports land; the wave is
still running.

## A3 — mod channels

| Claim | Check | Verdict |
|---|---|---|
| **M5** — "DAC channel 7" is never mapped to the DAC8568's address field, leaving it ambiguous by one channel (DAC-G `0110` vs DAC-H `0111`) on the node that sets the intercept of four jacks | `grep -rn "DAC-G\|DAC-H\|A3..A0\|0110\|0111"` across `hardware/`, `docs/decisions/`, `firmware/`, `config/` | **Confirmed. Zero hits.** The corpus names a channel by an ordinal that the datasheet does not use, with no `MISO` to catch a wrong write |

Not yet checked: M1 (the drawing's column positions), M2 (the buffer-load
model and the missing sink case), M3 (the `CLR` grade attribution), M4, M6,
M7, M8, S1–S3.

## A8 — grounding

| Claim | Check | Verdict |
|---|---|---|
| **Incidental** — `ROADMAP.md:53` carries a live `8HP`, and none of `panel-width`'s five forbidden patterns matches the spelling `at 8HP rather than` | Read the line; compared against the five patterns | **Confirmed.** The line reads "good practice **at 8HP** rather than the structural necessity it was at 6HP", describing a panel width that was superseded by 10HP. The five patterns are `panel is 40.34 mm`, `The panel is 8HP`, `inside 8HP`, `at 8HP this`, `Comfortable at 8HP` — **`at 8HP rather than` matches none**, and the checker reports PASS. **The fifth recorded escape of this exact class**, and it is in the file a builder follows at E12 |
| **F4-3** — all three line citations in `dig-gnd-topology`'s `candidates` are stale | Opened each cited line | **Confirmed, all three.** `0004:627` is mid-sentence about cents of error; the claim it cites is at **:637**. `digital-and-supervision.md:53` is a row of an ASCII drawing about `OE`; the claim is at **:60**. A line number is a path with different syntax, and nothing checks these |

Not yet checked: F1 (the jack sleeve and panel as an unassigned second
ground — needs a real part), F4-1/4-2 (ADR 0004 vs `power-entry.md`, and
`ROADMAP.md` as an undeclared fourth document), F5/F2, F6, F6-1/6-3, F9,
F-AGND-2, F3-1.

### Note on F4-3's significance

The `dig-gnd-topology` entry's own `note` field says *"power-entry.md states
that ADR 0004 was corrected on this point. IT WAS NOT — line 627 still says
the opposite."* That note is right about the substance and wrong about the
line, which is the failure mode one level up: **the record of the defect has
itself gone stale.**
