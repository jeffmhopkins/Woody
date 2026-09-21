# Key switch network — schematic

*`## §2` of [`../cluster-boards.md`](../cluster-boards.md), moved verbatim
2026-09-21 when that page was split into a board page and its circuits. One
network per switch position, repeated across the four boards; the section
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
| `3V3` | in | `interfaces/key-chain-loom` | `key-pullup-qty` | Chain bus pin 10 of `J-CHAIN`, `cluster-boards.md` §3. What `R-KEY-PU` pulls to. It is also the MCP3202's reference, which is what makes the static draw a live trade rather than a free one |
| key input node | out | `cluster/key-register` | `key-release-time`, `key-press-time` | Both passives sit **at the register input**, millimetres from the switch |
| `SW` | in | `SW-THUMB` | — | The KS-33 in its plate cutout, `cluster-boards.md` §5. Pressed = pulled LOW, through `R-KEY-SER` |
| `GND` | ref | `interfaces/key-chain-loom` | — | The chain bus, five alternating grounds. `C-KEY` and the closed switch both return here |
| unfitted positions | — | `cluster/key-marker-and-bits` | `free-bits` | The reserved spare-switch positions carry the full network; the free bits carry a pull-up only, and the marker straps carry nothing |

---

## §2 The key network — 21 of these, spread across four boards

```
   3V3 (from the loom, pin 10 of J-CHAIN)
    │
    └──[R-KEY-PU 2k2 1%]──┬────────────────────► 74HC165 parallel input
                          │                 │
                  [C-KEY 47 nF X7R]  [R-KEY-SER 100R 1%]
                          │                 │
                         GND               SW  KS-33
                                            │
                                           GND      pressed = pulled LOW

   CORRECTED 2026-09-21. The previous figure ran the switch leg off the
   3V3 rail, so a press was a 33 mA rail short and the register input
   never moved - contradicting the figure's own caption. Found in review.

   Both passives are AT the register input, millimetres from the switch.
   On this board that is automatic; under the tail topology it was a layout
   rule with a 265 mm loom in between.
```

### Derivations

`[calc]`, at 3.3 V into 74HC165 thresholds (**`V_IH` = 2.31 V, `V_IL` = 0.99 V**
— 0.70 / 0.30 × VCC `[datasheet MC74HC165A/D Rev. 13 p.4]`):

> **Corrected 2026-09-21, the same day it was changed the other way.** This
> page reasoned from TI's SCLS116E, which has no 3.3 V row, that the 0.70/0.30
> ratio "breaks at 2 V" and that the conservative 2 V ratio 0.75/0.25 was the
> defensible bound at 3.3 V. **A 3.0 V row is published, and it is 0.70/0.30.**
>
> | source | 2.0 V | **3.0 V** | 4.5 V | 6.0 V |
> |---|---|---|---|---|
> | TI SCLS116E `datasheets/logic/74HC165-ti-scls116e.pdf` | 1.5 / 0.5 | *(absent)* | 3.15 / 1.35 | 4.2 / 1.8 |
> | Nexperia Rev. 8 `74HC165-nexperia.pdf` | 1.5 / 0.5 | *(absent)* | 3.15 / 1.35 | 4.2 / 1.8 |
> | Toshiba TC74HC165 `74HC165-toshiba.pdf` | 1.5 / 0.5 | *(absent)* | 3.15 / 1.35 | 4.2 / 1.8 |
> | **onsemi MC74HC165A Rev. 13** `74HC165-onsemi.pdf` | 1.5 / 0.5 | **2.1 / 0.9** | 3.15 / 1.35 | 4.2 / 1.8 |
>
> All four agree digit for digit at every shared rail, so onsemi is not a
> different device — it simply prints the JEDEC HC row the other three omit.
> **3.3 V is bracketed on both sides by published 0.70/0.30 rows**, so no
> extrapolation through the 2 V point is needed at all. The 2 V entry is the
> single exception at the bottom of the family's range, not the start of a
> trend. Nexperia's own front page claims compliance with **JESD8C** (2.7–3.6 V),
> whose levels are 0.7/0.3 × VDD `[74HC165-nexperia.pdf p.1]` — a second strike.
>
> `[calc]` Interpolating in **absolute volts** between onsemi's bracketing rows,
> assuming no ratio at all:
> `V_IH`(3.3) = 2.1 + (0.3/1.5)(3.15−2.1) = **2.31 V**;
> `V_IL`(3.3) = 0.9 + (0.3/1.5)(1.35−0.9) = **0.99 V**. Both land exactly on
> 0.70/0.30, which is what makes the bracketing argument safe rather than lucky.
>
> So both crossing times go back to what they were before yesterday's move:
> **138.7 → 119.9 µs** and **6.89 → 5.92 µs**. Neither ever changed a
> conclusion — the release is absorbed by the asymmetric debounce either way,
> and the press clears the scan period by 42× instead of 36×. What was not
> defensible was stating 0.75/0.25 **as the datasheet threshold** when no
> datasheet in the corpus gave a threshold at 3.3 V at all.
>
> **If a TI SN74HC165 is the part actually fitted**, its own datasheet still
> guarantees nothing at 3.3 V, and the pessimistic bound is 2.475 / 0.825 V,
> giving 138.7 µs and 6.89 µs. Those are the numbers to design margin against
> if the margin ever gets tight. It is not tight: 42× and 36× are the same
> answer.
>
> *(The press row also said `τ = 100 Ω × 47 nF = 4.7 µs` beside a crossing
> time computed from the **parallel** combination, 4.496 µs. That correction is
> independent of the threshold question and **stands** — the pull-up is still
> connected, so the parallel value is the right one.)*
>
> The TI datasheet carries a warning worth repeating: operating in the
> threshold region risks **double-clocking from induced ground bounce**.
> Another reason not to shave this margin.

| | |
|---|---|
| Release, τ = 2.2 kΩ × 47 nF = 103.4 µs | crosses `V_IH` at **119.9 µs** |
| Press, τ = (2.2 kΩ ∥ 100 Ω) × 47 nF = 4.496 µs | crosses `V_IL` at **5.92 µs** — 42× inside the 250 µs scan |
| Pole | 1.54 kHz → **54 dB** at the WS2815's 800 kHz data rate |
| Static | **1.43 mA** per closed key; 18 closed = **25.8 mA** off the loom's 3V3 |

**Press is instant on the scan's timescale and release is filtered**, which is
the asymmetric-debounce shape ADR 0001 wants — instant attack, filtered release
`[repo] 0001`. The 125 µs release filter is half a scan period and costs
nothing musically; note-off is filtered in firmware anyway.

> **Why the network is fitted at all, stated honestly.** The argument that
> originally bought these parts — a 12 V LED edge through ~15 pF injecting a
> false level — was wrong, and ADR 0001 now records why: there is no 12 V edge,
> `Q/C` is the wrong model because coupling is a divider, and a divider cannot
> exceed its aggressor's swing `[repo] 0001`. **The pull-up is still
> mandatory**, because a floating CMOS input has no defined state at all — and
> this cavity is breathed into for hours at 10–20 K above ambient, with the
> switch contacts open. The 47 nF is a bounce filter and cheap insurance. It is
> not what makes the topology safe.

**`R-KEY-PU` is 2.2 kΩ and the reason it is no longer 10 kΩ has expired.**
`bom.csv` says so itself: the 2.2 kΩ was chosen when the node ran 265 mm down an
uncoated loom, *"that reason is gone now the register is back on the cluster
board"*, and it was kept as cheap insurance `[repo] bom.csv`. **Keeping it is
not free any more**, because 25.8 mA of play-rate load lands on the rail that is
also the MCP3202's voltage reference — worth 3.2 LSB, accepted on the carrier
page `[repo] carrier.md §2`. Going back to 10 kΩ would cut that to 5.9 mA and
0.7 LSB, at the price of a 100 µs τ in a humid cavity. **Recorded as a live
trade, not re-opened here.**

---

## Still open

*The two items from `cluster-boards.md`'s `Still open` list that belong to this
circuit, moved verbatim 2026-09-21. `§2` is this page.*

- **`R-KEY-PU` at 2.2 kΩ versus 10 kΩ** (§2). The reason for 2.2 kΩ expired when
  the register moved back to this board, and the cost — 25.8 mA on the ADC's
  reference rather than 5.9 mA — arrived at the same moment. Live trade,
  recorded on the carrier page as accepted.
- **Whether `LT` takes lighter springs** (`SW-THUMB`), which is an M1 decision by
  hand and changes nothing electrically `[repo] bom.csv, 0002`.
