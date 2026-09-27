# Key switch network — schematic

*`## §2` of [`../cluster-boards.md`](../cluster-boards.md), moved verbatim
2026-09-21 when that page was split into a board page and its circuits. One
network per switch position, repeated across the four clusters — two on the
main board, one on each key board (ADR 0017); the section
number is left as it was written. The switch's plate cutout and the footprint
it solders into are `§5 Mechanical` on the board page.*

## Interfaces

Every net that crosses this circuit's boundary. Quantities appear **only** as a
citation into `config/figures.yaml` — this table names nodes, it does not
restate values.

The `Dir` and `Peer` columns are defined once in
[`hardware/README.md`](../../README.md#the-interfaces-table).

| Node | Dir | Peer | Figure | Note |
|---|---|---|---|---|
| `3V3` | in | `interfaces/key-chain-loom` | `key-pullup-qty` | The chain's 3V3 rail: a trace on the main board; on a key board, ribbon conductor 10 = key-board `J-CHAIN` pin 3. What `R-KEY-PU` pulls to. It is also the MCP3202's reference, which is what makes the static draw a live trade rather than a free one |
| key input node | out | `cluster/key-register` | `key-release-time`, `key-press-time` | One node: the register input, `R-KEY-PU`, `C-KEY` and `R-KEY-SER` all sit on it. Where the three passives are placed along it is the board's layout — on a key board, beside their own switch, with the node trace running to the register over the ground pour (`hardware/boards/key-board-lh/layout.yaml`) |
| `SW` | in | `SW1-n` (`SW-THUMB` is an option on LT) | — | The KS-33 in its plate cutout, `cluster-boards.md` §5. Pressed = pulled LOW, through `R-KEY-SER` |
| `GND` | ref | `interfaces/key-chain-loom` | — | The main board's ground; on a key board, the ribbon's five alternating grounds. `C-KEY` and the closed switch both return here |
| unfitted positions | — | `cluster/key-marker-and-bits` | `free-bits` | The reserved spare-switch positions carry the full network; the free bits carry a pull-up only, and the marker straps carry nothing |

---

## §2 The key network — 21 of these, spread across the four clusters

*Connectivity is the KiCad sheet
**[`key-switch-network.kicad_sch`](key-switch-network.kicad_sch)** (render:
`key-switch-network.sch.png`), not this drawing (ADR 0019). `netlist.yaml` is
exported from the sheet and is what the checks read — never edit it. It says
`replicated: 21` — one network, built twenty-one times. `R-KEY-PU`
is bought 24 times because the three free bits carry a pull-up and nothing
else; `tools/check-netlist.py` prints that shortfall by name every run.*


```
   3V3 (the chain rail: a main-board trace, or ribbon conductor 10 = key-board J-CHAIN pin 3)
    │
    └──[R-KEY-PU 2k2 1%]──┬────────────────────► 74HCS165 parallel input
                          │                 │
                  [C-KEY 47 nF X7R]  [R-KEY-SER 100R 1%]
                          │                 │
                         GND               SW  KS-33
                                            │
                                           GND      pressed = pulled LOW

   CORRECTED 2026-09-21. The previous figure ran the switch leg off the
   3V3 rail, so a press was a 33 mA rail short and the register input
   never moved - contradicting the figure's own caption. Found in review.

   The register input, R-KEY-PU, C-KEY and R-KEY-SER share ONE node.
   Where the passives sit along it is the board layout's choice: on a key
   board they sit beside their own switch (layout.yaml), and the node
   trace runs to the register over the ground pour.
```

### Derivations

`[calc]`, at 3.3 V into the **SN74HCS165**'s Schmitt-trigger thresholds, taken
at their guaranteed extremes: the input is certainly read high once it passes
**VT+ at its maximum, 2.475 V**, and certainly read low once it passes **VT− at
its minimum, 0.495 V** (0.75 / 0.15 × VCC). TI tabulates 2 V, 4.5 V and 6 V
and no 3.3 V row `[datasheets/logic/SN74HCS165-ti-scls828a.pdf p.6]`:

| VCC | VT+ max | VT− min | as × VCC |
|---|---|---|---|
| 2.0 V | 1.5 | 0.3 | 0.75 / 0.15 |
| 4.5 V | 3.15 | 0.9 | 0.70 / 0.20 |
| 6.0 V | 4.2 | 1.2 | 0.70 / 0.20 |

So the page takes the **largest VT+ ratio and the smallest VT− ratio in the
table**, not an interpolation. A ratio assumed to hold between published rows
has misled this page once already (`notes.md`). Linear interpolation between
the 2 V and 4.5 V rows gives 2.358 / 0.612 V instead; both are inside the
bound. Nexperia's 74HCS165 does publish a 3.0–3.6 V row
`[datasheets/logic/74HCS165-nexperia.pdf p.6]`, but it is a different die and
not the part bought, so it is a cross-check only: both of its thresholds are
inside the bound too.

**The slow edges are within this part's rating.** It has Schmitt-trigger
inputs and "no input signal transition rate requirements"
`[SN74HCS165-ti-scls828a.pdf p.15]`, which is why it is the part: the key
network's edges cross the thresholds at the RC's rate, hundreds of times
slower than a plain 74HC165 allows (`notes.md`, and ADR 0001's amendment).
The hysteresis between VT+ and VT− (at least 0.2 V at 2 V and 0.4 V at
4.5 V `[same, p.6]`) is what stops a slow edge with noise on it from reading as
several transitions.

| | |
|---|---|
| Release, τ = 2.2 kΩ × 47 nF = 103.4 µs | passes VT+ max at **138.7 µs** (`key-release-time`) |
| Press, τ = (2.2 kΩ ∥ 100 Ω) × 47 nF = 4.496 µs | passes VT− min at **9.87 µs** (`key-press-time`) — 25× inside the 250 µs scan |
| Pole | 1.54 kHz → **54 dB** at the WS2815's 800 kHz data rate |
| Static | **1.43 mA** per closed key; 19 closed = **27.3 mA** off the chain's 3V3 |

Both crossing times are derived in `config/figures.yaml` (`key-release-time`,
`key-press-time`); this page owns them, and every other page cites them by name.

**Press is instant on the scan's timescale and release is delayed by
`key-release-time`**, just over half a scan period, which costs nothing
musically: the release reaches firmware on the next scan either way. **This RC is a glitch filter, not the debounce.** It swallows a
contact opening shorter than `key-release-time`; the switch's own bounce,
`ks33-contact-bounce`, is many times longer, so bounce passes straight through
it in both directions — every re-closure during a release pulls the node low
again within `key-press-time`. Rejecting bounce is entirely firmware's release
window, sized against `ks33-contact-bounce` (the asymmetric debounce ADR 0001
wants — instant attack, filtered release; `firmware/README.md`,
`docs/reference/latency-budget.md`).

**What `R-KEY-SER` is for.** It sits between the node and the switch, not in
front of the register input, so it protects nothing on the register side. Its
two jobs are the pressed-node divider (the node sits a little above 0 V, which
both crossing figures start from) and **limiting `C-KEY`'s discharge into the
switch contact** on every press. `[calc]` Peak = 3.3 V / (100 Ω + ≤ 0.2 Ω
contact) ≈ 33 mA for a few µs (τ ≈ 4.7 µs, ½·47 nF·3.3² ≈ 0.26 µJ). The KS-33
is rated **10 mA 12 VDC, resistive load** `[datasheets/mechanical/GATERON-KS-33-VENDOR-SPEC-DRAWING.pdf,
item 3 "Ratings"]`, so the press transient is about 3× the rating, for
microseconds; without `R-KEY-SER` only the contact's own resistance would
bound it. The steady closed-key current (`key-scan-current`) is well inside
the rating. A larger `R-KEY-SER` (≈ 330 Ω brings the peak to the rating)
raises the pressed-node voltage and slows the press; that trade is open, not
taken here.

> **Why the network is fitted at all, stated honestly.** The argument that
> originally bought these parts — a 12 V LED edge through ~15 pF injecting a
> false level — was wrong, and ADR 0001 now records why: there is no 12 V edge,
> `Q/C` is the wrong model because coupling is a divider, and a divider cannot
> exceed its aggressor's swing `[repo] 0001`. **The pull-up is still
> mandatory**, because a floating CMOS input has no defined state at all — and
> this cavity is breathed into for hours at 10–20 K above ambient, with the
> switch contacts open. The 47 nF is a glitch filter and cheap insurance — not
> a debounce (above), and not what makes the topology safe.

**`R-KEY-PU` is 2.2 kΩ and the reason it is no longer 10 kΩ has expired.**
It was chosen when each key node ran a long uncoated loom to a register at the
tail; every register now sits beside its switches, on the main board or a key
board, and the 2.2 kΩ was kept as cheap insurance ([`notes.md`](notes.md)).
**Keeping it is not free any more**, because 27.3 mA of play-rate load lands on the rail that is
also the MCP3202's voltage reference — worth 3.4 LSB, accepted on the carrier
page `[repo] carrier.md §2`. Going back to 10 kΩ would cut that to 6.2 mA and
0.8 LSB — **but not with the fitted 47 nF.** `[calc]` 10 kΩ × 47 nF = 470 µs,
and the release would pass VT+ max at 470 × ln((3.3 − 0.033)/(3.3 − 2.475)) ≈
647 µs, more than two scan periods. So 10 kΩ also means shrinking `C-KEY`
(≈ 10 nF brings the release back near `key-release-time`), with less glitch
filtering in a humid cavity. **Recorded as a live trade, not re-opened here.**

---

## Still open

*The two items from `cluster-boards.md`'s `Still open` list that belong to this
circuit, moved verbatim 2026-09-21. `§2` is this page.*

- **`R-KEY-PU` at 2.2 kΩ versus 10 kΩ** (§2). The reason for 2.2 kΩ expired when
  the register moved back to this board, and the cost — 27.3 mA on the ADC's
  reference rather than 6.2 mA — arrived at the same moment. Live trade,
  recorded on the carrier page as accepted.
- **Whether `LT` takes lighter springs** (`SW-THUMB`), which is an M1 decision by
  hand and changes nothing electrically `[repo] bom.csv, 0002`.
