# Key chain — what this circuit used to be

**Past tense only, and no live value.** Every live value is in
[`key-chain-loom.md`](key-chain-loom.md), in `hardware/bom.csv` or in
`config/figures.yaml`. If a number here is still true, it is in the wrong
file. Git holds every earlier version whole.

## 2026-09-21 — one loom, two descriptions

This directory did not exist before 2026-09-21. Until then the circuit was
described twice — once in `hardware/carrier/carrier.md` §3 and once in
`hardware/cluster/cluster-boards.md` §3 — and each half derived statements
from parts that were drawn only in the other. The consolidation moved text and
did nothing else.

## 2026-09-21 to 2026-09-26 — a carrier and four cluster boards on IDC

The chain ran from a carrier board through four cluster boards — right thumb,
right hand, left thumb, left hand — on 2×6 IDC boxed headers and 12-way
ribbons, about 265 mm of loom through the body beside the LED strip's 12 V
feed. `SER` and `QH` were point to point, so every cluster board but the last
had an IN and an OUT connector, and the count was eight across five boards
with four ribbon assemblies. Pin 6 was a pass-through that rode every hop to
the chain-end board.

Two parts existed only because of that topology:

- **`LK-SER`**, a 3-pad solder link on every cluster board, choosing whether
  the register's `SER` came from the next board's `QH` or from the pin-6
  pass-through, so that four boards could be one schematic. Retired
  2026-09-26: each key board now has one connector and its `SER` is always
  pin 6.
- **`R-SER-TERM`** sat on the chain-end cluster board. It moved to the main
  board with the same value and the same argument.

`R-CHAIN-SER`, `U-TVS-CHAIN` and `F-CHAIN` were justified by that loom — its
length, its run beside 12 V, and a short "inside something that bonds shut".
They were re-derived against the ribbons rather than carried over.

The hop map was prose only; the netlist placed the carrier's connector and
nothing else. The chain-order section of `cluster-boards.md` proposed swapping
`left_thumb` and `left_hand` to save a body-thickness crossing, which the
ribbons made moot. The drawing labelled the TVS array's return `DIG_GND`,
while the netlist had it on `GND_CHAIN`; the redrawn page uses `GND_CHAIN`.

## 2026-09-26 — one main board, two key boards on flat flex

ADR 0017 put the thumb clusters on the main board and gave each key board one
flat flex ribbon with a ZIF connector at each end. The chain order and the
12-way pinout were kept, so the bit map and firmware did not change.
