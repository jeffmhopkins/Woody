# Interfaces — the circuits that cross a board boundary

Three circuits in this project do not sit on one board. Each was described in
two places until 2026-09-21, and each is now one directory.

| Directory | Runs between |
|---|---|
| [`breath-sense-link/`](breath-sense-link/breath-sense-link.md) | Sensor and excitation buffer on the carrier → 2 m twisted pair → in-amp on the module |
| [`spi-link/`](spi-link/spi-link.md) | Carrier SPI egress → umbilical → the module's 74AHCT125 |
| [`key-chain-loom/`](key-chain-loom/key-chain-loom.md) | Carrier → four cluster boards, eight connectors on one bus |

## Why these are not filed under a board

Because their numbers cannot be derived from one side.

`breath-sense-link` is the clearest case. Its differential pole is derived
from 1 kΩ in **both** legs, and one of those legs is on the other board. Its
CMRR term is *entirely* a statement about whether a resistor is fitted over
there. And it **owns a tracked figure**, `inamp-full-scale`, whose derivation
reaches across the umbilical. Split across two files, each half stated a
budget it could not check.

`docs/reference/pcb-pipeline.md`'s netlist precursor records the cost of
getting this wrong: `AGND` means two different things and `BREATH` means two
different things, and **both collisions are between the two ends of one of
these three blocks**. A transcription that takes net names off the drawings
shorts the breath in-amp input to the breath output jack — and every
downstream check passes, because the merge happens before anything can see it.

Each page's `## Interfaces` table therefore carries an **End** column naming
which side of the cable a node sits on, and the breath table states both
collisions explicitly.

## A disagreement is moved here, not resolved here

Consolidation was done under a content freeze: where the two halves disagreed,
**both statements were moved verbatim and placed adjacent**, with a closing
section saying no winner was picked.

`breath-sense-link.md` carries the live one. One end says `R1b` is worth
"fifty times" the rejection; the other says it buys about 13 dB. Both agree
the part must be fitted. The simulation deck in
`../module/breath-receive-stage/sim/` is what settles it, and it has not been
run.
