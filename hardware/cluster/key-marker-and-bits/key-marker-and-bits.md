# The 32 bits — marker straps and bit allocation — schematic

*`## §4` of [`../cluster-boards.md`](../cluster-boards.md), moved verbatim
2026-09-21 when that page was split into a board page and its circuits. The
straps are copper on the same boards the key networks are on; the section
number is left as it was written.*

## Interfaces

Every net that crosses this circuit's boundary. Quantities appear **only** as a
citation into `config/figures.yaml` — this table names nodes, it does not
restate values.

The `Dir` and `Peer` columns are defined once in
[`hardware/README.md`](../../README.md#the-interfaces-table).

| Node | Dir | Peer | Figure | Note |
|---|---|---|---|---|
| marker straps | out | `cluster/key-register` | `marker-bits` | Into the parallel inputs. Copper straight to a rail, two per device, one high and one low |
| free-bit pull-ups | out | `cluster/key-register` | `free-bits`, `key-pullup-qty` | Into the parallel inputs. An `R-KEY-PU` and nothing else — no switch, no series resistor, no capacitor |
| switch positions | in | `cluster/key-switch-network` | — | The networked positions, fitted and reserved, take the rest of the allocation |
| the serial bit stream | out | `interfaces/key-chain-loom` | — | The allocation rides on the chain order, `config/key-layout.yaml`'s. Since ADR 0017 no reordering saves any wiring, so it is not expected to change |
| `3V3`, `GND` | ref | `interfaces/key-chain-loom` | — | The chain's rails — main-board copper for `right_thumb` and `left_thumb`, the ribbon on a key board. The straps land directly on the rails and share no component with the key networks they are read as vouching for |

## §4 The 32 bits

### Allocation, on the chain order as written today

**The data is [`allocation.yaml`](allocation.yaml)**; the table below is its
written form. The wiring itself is on the KiCad board sheets (ADR 0019), and
`tools/kicad.py check` fails if a board's register is wired differently from
`allocation.yaml`, or if the file and this table disagree. Change all three
together. **This circuit is now just the free-bit pull-up**, one sheet placed
once per free bit ([`key-marker-and-bits.kicad_sch`](key-marker-and-bits.kicad_sch));
the marker straps are traces, drawn on each board's own sheet.

`H` is the first bit out of each device, so within a cluster the lowest-numbered
key takes the earliest bit:

| Device | Bits | `H` | `G` | `F` | `E` | `D` | `C` | `B` | `A` |
|---|---|---|---|---|---|---|---|---|---|
| `right_thumb` | 0–7 | RT1 | RT2 | RT3 | RT4 | sw+ | sw− | **M** | **M** |
| `right_hand` | 8–15 | RH1 | RH2 | RH3 | RH4 | RH5 | RH6 | **M** | **M** |
| `left_thumb` | 16–23 | LT1 | LT2 | LT3 | LT4 | **M** | **M** | free | free |
| `left_hand` | 24–31 | LH1 | LH2 | LH3 | LH4 | LH5 | **M** | **M** | free |

`sw+` `sw−` are the two reserved spare-switch positions — octave up and
octave down `[repo] key-layout.yaml`. **On `right_thumb`**, because RT is the
control cluster (its four fitted keys are `role: control`, not fingering
inputs `[repo] key-layout.yaml`). There was a third, hold/preset, until
2026-09-26: the right thumb went to four keys and RT4 took its bit. They have
their networks and **no cutouts** since the same day (owner, ADR 0010), so
fitting one means recutting `PLATE-BOTTOM` and the oak bottom.

**Every position above gets the full `R-KEY-PU`/`R-KEY-SER`/`C-KEY` network**,
including the two unfitted spares — 21 sets, which is what `bom.csv` budgets
`[repo]`.

### The marker pattern: 8 bits, not 6 — DECIDED 2026-09-21

`key-layout.yaml` booked 6 marker bits and 5 genuinely free ones. **It now says
8 and 3** `[repo] key-layout.yaml, 0001`, and the table above shows the 8.
The argument, for the record:

A marker is a framing check: firmware reads it every scan, and a frame that
fails it holds the previous frame and increments a visible error counter
`[repo] 0001`. Its whole value is converting an invisible intermittent fault
into a number someone can read — the error counter. There is no display
(ADR 0015); how the counter is surfaced, on the matrix or on configuration mode's page, is
firmware's (F7).

**Six bits cannot do that per device in both directions, and eight can.** With
two marker bits in every device, one wired high and one wired low, a device that
is dead, unclocked, stuck high or stuck low fails its own marker — whichever way
it failed, and no matter what the other three are doing. At six, two devices get
a single marker bit each and are only checkable in one direction.

**The two extra bits cost almost nothing, because "free" bits are not free —
they are useless.** A free bit has no plate cutout and no switch. The body bonds
shut. You cannot add a switch to one without cutting the plate, and the plate is
generated at M3 and fitted before bonding `[repo] 0009, 0010`. The
positions that *are* retrofittable are the reserved spare-switch bits
(`config/key-layout.yaml` `spare_bits_switches`), which
have their networks fitted and are untouched by this proposal. *(They had
cutouts too until 2026-09-26; the owner removed them, ADR 0010, so fitting
one now means recutting the bottom plate and oak bottom.)* **So the trade is: two bits
that could never be used against per-device fault detection in both
directions.**

Levels:

| Device | Input | Bit | Level | | Input | Bit | Level |
|---|---|---|---|---|---|---|---|
| `right_thumb` | `B` | 6 | **1** | | `A` | 7 | **0** |
| `right_hand` | `B` | 14 | **0** | | `A` | 15 | **1** |
| `left_thumb` | `D` | 20 | **0** | | `C` | 21 | **1** |
| `left_hand` | `C` | 29 | **0** | | `B` | 30 | **1** |

Read in bit order the marker is `1 0 · 0 1 · 0 1 · 0 1`.

*(Why `left_thumb`'s pair is that way round, and the one wrong chain
permutation that flipping it kills — [`notes.md`](notes.md).)*

**What the marker still cannot see**, stated plainly because firmware needs
it: a single-bit flip is caught **8 times in 32**, and the 24 bits that carry
the music are never among them — so **the visible error counter undercounts
true corruption about 4×**. **A mid-shift `SH/LD` reload is not reliably
caught**: a reload after *k* of 32 clocks makes each later bit a copy of the
bit *k* places earlier in the frame, so whether all eight marker positions
still read right depends on *k* and on which keys are held. `[calc over
allocation.yaml]` Only a reload at the last clock passes for every key state,
and many reload points pass for some key states. Firmware must not count on
the marker to catch it. And the straps go direct to the rails, so they share no
component with the 21 key networks they are read as vouching for.

That leaves **3 free bits**: `left_thumb` `B` and `A` (22, 23) and `left_hand`
`A` (31). **Each gets an `R-KEY-PU` and nothing else** — no switch, no series
resistor, no capacitor. A floating CMOS input is the exact fault `R-KEY-PU`
exists to fix `[repo] 0001, fix 6`.

> **The first draft of this page did not budget these three.** Its component
> table, `bom.csv` and `carrier.md` all carried a superseded count of 21
pull-ups for exactly the 21
> *switch* positions, leaving bits 22, 23 and 31 floating — unretrofittable,
> and precisely the fault the part exists to prevent. `R-KEY-PU` is now
> **qty 24**. Found in review.

> **Marker bits strap straight to the rails — no resistor, no capacitor.** A
> marker is not a switch: it never changes, so there is nothing to debounce and
> no pull-up to lose an argument with. Eight 47 nF caps on a rail that is
> already the ADC's reference, for eight nodes that are hard-wired, would be
> eight caps of pure cost. `[calc]` **16 parts saved** against wiring markers as
> if they were keys, and the network count stays exactly the 21 `bom.csv`
> budgets `[repo]`.

**This is hard-wired copper on boards that bond into the instrument. It has to
be right before the boards are ordered, and firmware has to be told the pattern.**

---

## Still open

- **Whether the reserved spare-switch positions** (`config/key-layout.yaml`
  `spare_bits_switches`) **are ever fitted.** Their bits are decided and wired
  — `sw+` `sw−` on `right_thumb` (`allocation.yaml`), networks fitted — and
  there are no cutouts for them (owner, 2026-09-26, ADR 0010). **Closed at M2**,
  with hands on the mule: where on the body a switch would go, and so whether
  fitting one is worth recutting `PLATE-BOTTOM` and the oak bottom. Nothing
  on a board waits on it.

**Decided: the last 3 free bits stay pulled up, not strapped** (8 marker bits,
3 free, as `config/key-layout.yaml` has them). `[calc over allocation.yaml]`
Strapping them would add no fault the marker cannot already see: every
device already carries one bit wired high and one wired low, which is what
makes a dead, unclocked, stuck-high or stuck-low device fail its own frame,
and the only devices holding free bits (`left_thumb`, `left_hand`) have both.
Three more straps would raise the single-bit-flip catch from 8 in 32 to 11 in
32 and nothing else. A pulled-up free bit reads high on every good frame
anyway, so firmware may check it as a high marker at no cost to the board,
while the pull-up keeps it usable as an input: since ADR 0025 the body opens
by cutting its silicone, so a free bit is no longer one that can never become
a switch. Both key boards are laid out with it (`R11`).
