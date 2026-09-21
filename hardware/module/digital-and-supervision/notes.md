# Digital path — decision history

**Past tense only.** Every live value is in
[`digital-and-supervision.md`](digital-and-supervision.md),
[`../dac8568/dac8568.md`](../dac8568/dac8568.md) or `hardware/bom.csv`. If a
number here is still true, it is in the wrong file.

This is the circuit's superseded shelf, on the convention
`docs/decisions/README.md` runs at project scope. Nothing is deleted from it: a
deleted superseded value stops warning the next person.

---

*Moved verbatim from `digital-and-supervision.md`, 2026-09-21, when that page
was split into three circuit directories. The two blockquotes that followed
item 4 did **not** come with it — they are live questions, and they stayed on
the page.*

## What this redraw changed

The previous drawing was wrong in four ways, all found independently by
more than one reviewer in `docs/review/2026-09-21-hardware-and-standards-review/`.

**1. It still drew the deleted watchdog and presence comparator.** The
74HC123 and LM311 were deleted — in ADR 0004, in `bom.csv`, and in this
page's own prose two sections below — and were still drawn here, still
allocated rails in the table below, and still counted in `bom.csv`'s
`C-DECOUPLE` quantity. **`C-DECOUPLE` drops from 21 to 19.** Neither part
ever had a BOM row, so a board built from the old drawing would have had
two footprints and no parts to fit.

**2. `CLR` was drawn as a pull-DOWN on an active-low pin.** `[R-CLR-PD 10k]`
to `AGND`, against `bom.csv`'s `R-CLR-PU`. With the watchdog deleted
nothing else drives that pin, so **as drawn `CLR` was asserted permanently:
six dead CV outputs, and no SPI write able to change them.** This was the
single cheapest way in the whole design to end up with a module that does
nothing at all.

**3. `OE` gating is gone.** It was driven from the presence comparator's
collector, pulled up through `R-OE-PU` to bus +5 V, and shared a node with
the panel LED through an 820 Ω resistor. With the comparator deleted, `OE`
is **tied low — permanently enabled** (`bom.csv` `U-LVL-MOD` already says
so). `R-OE-PU` and the 820 Ω had no BOM rows; `R-LED-PANEL` is 2.2 kΩ from
+12 V analog and is drawn on the power page, not here.

**4. The umbilical pin map is the corrected one.** `SCLK` and `MOSI` now
share pair (4,5); **`CS` is paired with `DIG_GND` on (7,8)**. Previously
`MOSI` and `CS` shared a pair with **no return conductor between them** —
two unrelated fast edges twisted tightly together, which is the most
efficient possible coupling rather than the cancellation twisting is for.
Two reviewers independently computed **365–907 mV of saturated intra-pair
crosstalk against `CS`'s 678 mV `V_IL` margin** and independently proposed
this exact swap. It improves the margin from about **1.9:1 to 6200:1** and
costs nothing but the pin assignment.

---

## One of the two bullets closed here, 2026-09-21

*Moved verbatim from `digital-and-supervision.md`'s "Two bullets closed here",
2026-09-21. The other of the two is the `LDAC` bullet, which went with the DAC
to [`../dac8568/notes.md`](../dac8568/notes.md).*

- **`SCLK` has no series resistor and `MOSI` does** — closed. It is
  `R-SPI-SER` ×3, 100 Ω, one on each of `SCLK`, `MOSI` and `CS` at the driving
  end (`carrier.md`, `bom.csv`, and ADR 0004 now agrees). That also closes the
  back-powering path found separately in the power review.
