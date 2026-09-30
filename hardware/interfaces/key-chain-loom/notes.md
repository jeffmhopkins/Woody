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

## 2026-09-26 — `F-CHAIN` dropped, `U-TVS-CHAIN` fitted

Until ADR 0018 the chain's 3V3 fed all four registers through `F-CHAIN`, a
100 mA polyfuse in 0805 (Bourns MF-PSMF010X was the nearest banked part), on a
rail called `V3V3_CHAIN` that was a separate node from `DEV_3V3`. Its row
argued that the polyfuse's 1.0–7.5 Ω series resistance was harmless because
the 74HC165 thresholds and the pull-ups shared the rail, and left open whether
to fit it or to protect at the source. The owner chose the source: the
Matrix LDO's own current limit, with a ferrite bead per ribbon for isolation.
`V3V3_CHAIN` became the same node as `DEV_3V3` on the main board, and each key
board's rail got its own net past its bead.

`U-TVS-CHAIN` had been `open`, with "protect service by procedure (instrument
off, a wrist strap) or by the part" left to the owner. The owner chose the
part.

## 2026-09-27 — flat flex and ZIF replaced by through-hole 1.27 mm IDC

From 2026-09-26 the chain's connectors were a 12-way 1.0 mm SMT side-entry
ZIF (`J-CHAIN`, the Molex 200528-0120 as the first layout's stand-in) at each
end of a same-side-contact flat flex cable, `FFC-CHAIN`. The key board's
connector took the ribbon from the far side, level, and the ribbon ran round
one 180° C toward the far side wall into the main board's. That short arc let
the lid tilt only a little with the ribbons attached; to take the lid off,
the two ZIF latches were flipped first. The key board's pins were netted
13 − k, and the cable's length was to be "ribbon arc length" plus two
insertion depths. Flat flex had been chosen because a 2.54 mm IDC box header
and plug were judged too tall for the gap between the boards — a figure from
memory, about 2.54 mm parts only.

The owner changed it on 2026-09-27 (ADR 0017's amendment): through-hole, so
the board rather than SMT pads takes the cable's pull; right-angle 1.27 mm
shrouded IDC headers, stacked one over the other; the ribbon folded flat as a
hairpin along the body so that it never blocks the LED strip; and long enough
to plug in with the lid off, laid beside the body. `FFC-CHAIN` became
`CBL-CHAIN`, and the ZIF-era note that a ribbon "seated skewed" could bridge
3V3 to ground gave way to the keyed shroud.

**The key-board pin map was written wrong for part of the same day.** With
only Samtec's catalogue pages banked, the first IDC write-up derived the key
board's pins from the header alone `[calc]`: the same part upside down, a
straight-through cable, standard IDC numbering — so main-board pin k was said
(superseded the same day) to reach key-board pin 12 − k for odd k and 14 − k
for even k, with the key-board signals "side by side in its even row", the
chain-end `SER` on key-board pin 8 (superseded), and the closed hairpin's legs "one at each plug's height".
It was marked open until the full prints. The full prints were banked the
same day (`SAMTEC-SHF-1XX-01-X-D-XX-PRINT.pdf`, `SAMTEC-FFSD-XX-X-XX.XX-01-PRINT.pdf`)
and showed the derivation asked the wrong part: a keyed socket always mates
position k to header pin k, so the map is set by how the **cable** is built.
An FFSD socket's cable leaves on the side away from its notch, and a
straight cable would have left the key-board socket's ribbon rising into the
key board. Ordered `-RN2`, notch reversed on the key-board end, that socket
mates rotated 180°, its ribbon leaves downward like the main board's, and
conductor k meets key-board pin 13 − k — the same map the flat-flex design
had. The key boards' sheets were renetted to it (3V3 on pin 3, signals on
the odd pins); the same corrections moved the header's height, mouth and
pin-row depth in `config/body.yaml` off the print, and the hairpin became a
main-board leg on the board and a key-board leg just under its socket.
ADR 0017's amendment was corrected in place the same day.
