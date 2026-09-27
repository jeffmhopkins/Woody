# Key register — schematic

*The device itself: `## §1` of [`../cluster-boards.md`](../cluster-boards.md),
moved verbatim 2026-09-21 when that page was split into a board page and its
circuits. There are four: `right_thumb` and `left_thumb` on the main board,
`right_hand` and `left_hand` on the key boards (ADR 0017). The chain that
clocks them is [`key-chain-loom`](../../interfaces/key-chain-loom/key-chain-loom.md),
which holds the hop map; the section number is left as it was written.*

## Interfaces

Every net that crosses this circuit's boundary. Quantities appear **only** as a
citation into `config/figures.yaml` — this table names nodes, it does not
restate values.

The `Dir` and `Peer` columns are defined once in
[`hardware/README.md`](../../README.md#the-interfaces-table).

| Node | Dir | Peer | Figure | Note |
|---|---|---|---|---|
| `SCK` | in | `interfaces/key-chain-loom` | `chain-conductors` | One net to all four devices: a trace on the main board; on a key board, ribbon conductor 2 = key-board `J-CHAIN` pin 11 |
| `SH/LD` | in | `interfaces/key-chain-loom` | `chain-conductors` | The chain bus: a trace on the main board; on a key board, ribbon conductor 4 = key-board `J-CHAIN` pin 9. Level-sensitive: while it is LOW the parallel inputs load, asynchronously; the state captured is the inputs' when it returns HIGH |
| `SER` | in | `interfaces/key-chain-loom` | `chain-connectors` | Point to point: the next device's `QH`, or at the chain end `IO33` and its pull-up. On a key board it is always ribbon conductor 6 = key-board `J-CHAIN` pin 7. Which device feeds which is the hop map in the key-chain netlist |
| `QH` | out | `interfaces/key-chain-loom` | `chain-connectors` | Toward the MCU: on a key board, ribbon conductor 8 = key-board `J-CHAIN` pin 5; `right_thumb`'s is a trace to the MCU. Bit 0 is the `H` input of the `right_thumb` device |
| `A`…`H` | in | `cluster/key-switch-network`, `cluster/key-marker-and-bits` | `marker-bits`, `free-bits` | Eight parallel inputs per device: a switch network, a marker strap or a free bit |
| `3V3` | in | `interfaces/key-chain-loom` | — | The chain's 3V3 rail: a trace on the main board; on a key board, ribbon conductor 10 = key-board `J-CHAIN` pin 3. `C-DECOUPLE-165` is the local reservoir this input has no other source for |
| `GND` | ref | `interfaces/key-chain-loom` | `chain-conductors` | The main board's ground; on a key board, the ribbon's five alternating grounds. `C-DECOUPLE-165` returns here, at the package |

## §1 The device

*Connectivity is the KiCad sheet **[`key-register.kicad_sch`](key-register.kicad_sch)**
(render: `key-register.sch.png`), not this drawing (ADR 0019). `netlist.yaml`
is exported from the sheet and is what the checks read — never edit it. It is
one schematic for four boards — `replicated: 4`. The eight parallel
inputs are deliberately not netted there: which of `A`…`H` is a switch, a
marker strap or a free bit is different on every board, so no assignment
would be true of all four. The allocation table lives on
[`../key-marker-and-bits/key-marker-and-bits.md`](../key-marker-and-bits/key-marker-and-bits.md).*


```
                      SN74HCS165  SOIC-16  [ds SN74HCS165-ti-scls828a.pdf p.3]
                     ┌────────────∪────────────┐
       SH/LD  ──────►│ 1  SH/LD        VCC  16 │◄──── 3V3 ──┬── [C-DECOUPLE-165 100nF]
        SCK   ──────►│ 2  CLK       CLK INH 15 │──── GND     │   AT the package,
         E    ──────►│ 3  E (D4)       D  14   │◄──  key D   │   not near it
         F    ──────►│ 4  F (D5)       C  13   │◄──  key C  GND
         G    ──────►│ 5  G (D6)       B  12   │◄──  key B
         H    ──────►│ 6  H (D7)       A  11   │◄──  key A
    (no connect) ────│ 7  QH_bar      SER 10   │◄──── serial in
                GND ─│ 8  GND          QH  9   │─────► serial out
                     └─────────────────────────┘

  CLK INH (pin 15) is tied LOW, permanently.       [repo] 0001 fix 6
  QH_bar (pin 7) is an output and is left open — do NOT ground it.
  C-DECOUPLE-165 goes at the package, on this board, which is the whole
  point of the part: a 74x165's output edges brown out a local rail that
  has no reservoir.                                [repo] 0001 fix 5
```

**Bit order inside the device is `H` first, then `G F E D C B A`.** While
`SH/LD` is LOW the parallel inputs load, asynchronously and level-sensitively
(ADR 0001); what the chain then shifts out is the inputs' state at the moment
`SH/LD` returns HIGH. During the load `H` (D7) appears at `QH`, and each clock
after it shifts the next one toward the output `[datasheets/logic/SN74HCS165-ti-scls828a.pdf
p.13, Table 8-1 (SH/LD L: parallel load; SH/LD H, CLK ↑, CLK INH L: shift toward QH) and Table 8-2 (QH follows internal register H)]`. Combined with ADR 0001's *"bit 0 is the first bit clocked out"*
`[repo] 0001, key-layout.yaml`, that fixes **bit 0 = the `H` input of the
`right_thumb` device** and settles the `H`…`A` question the carrier page left
open — the ordering half of it, anyway. Which *switch* lands on which input is
§4.

**The part is the SN74HCS165: HC-family outputs, Schmitt-trigger inputs, not
74LVC and not a plain 74HC165**, and both halves are load-bearing. *Outputs:*
HC-family edges (output transition time 5 ns typical at 4.5 V
`[datasheets/logic/SN74HCS165-ti-scls828a.pdf p.8]`) keep each hop — a ribbon
and part of the main board — an ordinary lumped load instead of a transmission
line, which is what removed the hazards that briefly sent these registers to
the tail `[repo] 0001, bom.csv`. Same SOIC-16 footprint, so LVC with proper
source termination remains the way back if E4 disagrees. *Inputs:* the key
network's RC edges are far slower than a plain 74HC165's input transition
limit allows; the HCS165 has "no input signal transition rate requirements"
`[same, p.15]` (ADR 0001's amendment, 2026-09-27;
[`../key-switch-network/key-switch-network.md`](../key-switch-network/key-switch-network.md)).
A substitute must keep both: the `U-KEYS` row.
