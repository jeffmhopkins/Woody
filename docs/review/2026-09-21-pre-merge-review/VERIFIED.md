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

## A1 — breath chain

| Claim | Check | Verdict |
|---|---|---|
| `U-DIFFRX`'s BOM row carries a live `-9.6V`, a **forbidden** value of `inamp-full-scale`, escaping because the list spells it with a space | Read the row; compared to the four patterns | **Confirmed, and worse than reported.** The row says *"Output is 0V at rest to **-9.6V** at full"*. The forbidden patterns are `-9.6 V`, `−9.6 V`, `-10.05 V`, `−10.05 V` — all four carry a space before the `V`. **The corpus spells it without one.** The register's own note says −9.6 V "is derived from nothing and matches no configuration", and it is live on the in-amp's own row while `check-staleness.py` reports PASS |

**This is the sixth recorded escape of this class, and the second found
today.** The mechanism is identical every time and is written down in two
places in this repository: a forbidden pattern is a case-sensitive literal,
and the corpus spells its numbers more ways than the person writing the list
imagines. Today the spelling was one absent space.

## B5 — firmware contract

| Claim | Check | Verdict |
|---|---|---|
| `firmware/README.md` contradicts itself about where the display runs, inside the list it calls "not negotiable" | Read both bullets | **Confirmed.** Bullet 2: "Display renders on the other core, on its own SPI host." Bullet 5, three lines later: "WiFi and the display are on the other MCU." Both are in the same non-negotiable list |

Not yet checked: the twelve absent obligations, the SPI-host exhaustion
claim, the IMU I2C arithmetic, and the four further staleness escapes B5
reports.

## Cross-cutting, from four reports that could not see each other

Three agents independently report the same structural cause: **BOM rows were
assigned by matching reference-designator strings, so parts the drawings
label differently fell into `unplaced.csv`** — `U-DIFFRX`, `R-GAIN-INAMP`,
`C-FILT-BREATH` and others are *drawn* and filed as undrawn. A1 adds the
consequence that matters: **every staleness escape it found is in a file the
chain's own pages do not reach.** The misfiling did not create the stale
values, but it put them where no reader of the breath chain would look.

That assignment rule is mine, from this session.

## B4 — ADRs vs drawn reality

| Claim | Check | Verdict |
|---|---|---|
| **B4-01** — ADR 0004 withdraws the frame watchdog at `:484` and then reasons from it as live at `:523` | Read both lines; tested whether `:516-524` sit inside the withdrawal blockquote | **Confirmed, and the structure is the point.** `:484` opens `> **Withdrawn 2026-09-21.**`. Lines 516–524 are **plain prose, not quoted** — outside the withdrawal — and `:523` reads "the MCU dies, SPI stops, `CLR` fires, and breath keeps working." With no watchdog, `CLR` does not fire. **This is the exact class `CLAUDE.md` §5 names as the one no grep can find**, and it is the same watchdog, in a different document, still live |
| **B4-14** — `key-pullup-qty`'s forbidden pattern `"Twenty-one sets"` matches a **true** sentence, and is masked only by an accident of line wrapping | Read the pattern and `0001:217` | **Confirmed.** The line reads "…rather than 265 mm of loom. Twenty-one sets across the". The statement is correct — 21 networks and 24 pull-ups are different quantities — and the only reason the hook is silent is that `rather than` happens to share the line and counts as refutation wording. **Reflow that paragraph and the checker starts failing on a correct statement**, whose cheapest "fix" is to make it wrong |

## A2 — pitch chain

| Claim | Check | Verdict |
|---|---|---|
| **P2** — there is no decoupling capacitor on `VREFOUT` anywhere in the BOM, on the node where 1 mV is 1.2 cents | `grep -i vrefout hardware/bom.csv` | **Confirmed on the corpus side.** The only rows naming `VREFOUT` are the op-amp, the offset trimmer and a series resistor. No capacitor. **The datasheet half I could not verify myself** — `pypdf` fails in this container with a `_cffi_backend` error, so I could not re-read the cited pages. A2's datasheet citations for P1 and P2 stand as its claims, not as my verification |

Not yet checked: P1 (the 3-stated `VREFOUT` at power-on, which refutes three
separate statements about what the pitch jack does), P3 (the LT5400 outside
the clamp), P4, P6–P14.

### A note on the tooling, for whoever picks this up

`pypdf` is broken in this container. `docs/reference/repo-maintenance.md` §3
records `python3 -c "import pypdf"` as the working extraction route "used for
every extraction in this session" — **that is no longer true here**, and any
agent told to verify a datasheet claim will hit it. `pdftotext` was already
recorded as not installed in every session. Whoever re-verifies B3's slice
needs a working reader first.
