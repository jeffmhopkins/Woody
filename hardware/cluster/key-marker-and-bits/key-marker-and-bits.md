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
| the serial bit stream | out | `interfaces/key-chain-loom` | `chain-connectors` | The allocation rides on the chain order, which `cluster-boards.md` fixes and may yet change |
| `3V3`, `GND` | ref | `interfaces/key-chain-loom` | — | The chain bus, `cluster-boards.md` §3. The straps land directly on the rails and share no component with the key networks they are read as vouching for |

## §4 The 32 bits

### Allocation, on the chain order as written today

`H` is the first bit out of each device, so within a cluster the lowest-numbered
key takes the earliest bit:

| Device | Bits | `H` | `G` | `F` | `E` | `D` | `C` | `B` | `A` |
|---|---|---|---|---|---|---|---|---|---|
| `right_thumb` | 0–7 | RT1 | RT2 | RT3 | sw+ | sw− | sw? | **M** | **M** |
| `right_hand` | 8–15 | RH1 | RH2 | RH3 | RH4 | RH5 | RH6 | **M** | **M** |
| `left_thumb` | 16–23 | LT1 | LT2 | LT3 | LT4 | **M** | **M** | free | free |
| `left_hand` | 24–31 | LH1 | LH2 | LH3 | LH4 | LH5 | **M** | **M** | free |

`sw+` `sw−` `sw?` are the three reserved spare-switch positions — octave up,
octave down, hold/preset `[repo] key-layout.yaml`. **Proposed on `right_thumb`**,
because RT is already the control cluster (its three fitted keys are `role:
control`, not fingering inputs `[repo] key-layout.yaml`) and it has the spare
capacity. They need **plate cutouts at M3 even if the switches are fitted
later** `[repo] key-layout.yaml, 0010`, and the cutouts go in `PLATE-THUMB`.

**Every position above gets the full `R-KEY-PU`/`R-KEY-SER`/`C-KEY` network**,
including the three unfitted spares — 21 sets, which is what `bom.csv` budgets
`[repo]`.

### The marker pattern: 8 bits, not 6 — DECIDED 2026-09-21

`key-layout.yaml` booked 6 marker bits and 5 genuinely free ones. **It now says
8 and 3** `[repo] key-layout.yaml, 0001`, and the table above shows the 8.
The argument, for the record:

A marker is a framing check: firmware reads it every scan, and a frame that
fails it holds the previous frame and increments a visible error counter
`[repo] 0001`. Its whole value is converting an invisible intermittent fault
into a number on the display.

**Six bits cannot do that per device in both directions, and eight can.** With
two marker bits in every device, one wired high and one wired low, a device that
is dead, unclocked, stuck high or stuck low fails its own marker — whichever way
it failed, and no matter what the other three are doing. At six, two devices get
a single marker bit each and are only checkable in one direction.

**The two extra bits cost almost nothing, because "free" bits are not free —
they are useless.** A free bit has no plate cutout and no switch. The body bonds
shut. You cannot add a switch to one without cutting the plate, and the plate is
generated at M3 and fitted before bonding `[repo] 0009, 0010`. The three
positions that *are* retrofittable are the reserved spare-switch bits, which
have cutouts and are untouched by this proposal. **So the trade is: two bits
that could never be used against per-device fault detection in both
directions.**

Proposed levels:

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
true corruption about 4×**. A mid-shift `SH/LD` reload passes at 11 of 31
reload points. And the straps go direct to the rails, so they share no
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

*The two items from `cluster-boards.md`'s `Still open` list that belong to this
circuit, moved verbatim 2026-09-21. `§4` is this page.*

- **Where the 3 reserved spare-switch positions go.** Proposed on `right_thumb`
  as the control cluster; placement is an M2 decision with hands on the mule
  `[repo] key-layout.yaml`, and it decides which board carries them **and which
  plate gets the cutouts.**
- **Whether the last 3 free bits should be marker bits too**, making it 11.
  The argument that took the marker from 6 to 8 — a free bit has no plate
  cutout and the body bonds shut, so it can never become a switch — applies to
  these three unchanged, and strapping them costs *nothing* where pulling them
  costs three resistors. Against: a pulled bit can still be jumpered at
  bring-up, and 8 was decided deliberately. Left at 8/3 rather than drifting.
