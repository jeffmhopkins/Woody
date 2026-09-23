# Key register — schematic

*The device itself: `## §1` of [`../cluster-boards.md`](../cluster-boards.md),
moved verbatim 2026-09-21 when that page was split into a board page and its
circuits. One of these sits on each of the four cluster boards. The chain bus
it clocks from is `§3` of the board page, and the section number is left as it
was written.*

## Interfaces

Every net that crosses this circuit's boundary. Quantities appear **only** as a
citation into `config/figures.yaml` — this table names nodes, it does not
restate values.

The `Dir` and `Peer` columns are defined once in
[`hardware/README.md`](../../README.md#the-interfaces-table).

| Node | Dir | Peer | Figure | Note |
|---|---|---|---|---|
| `SCK` | in | `interfaces/key-chain-loom` | `chain-conductors` | The chain bus, `cluster-boards.md` §3. Straight bus, IN to OUT, so any two boards take a plain straight-through ribbon |
| `SH/LD` | in | `interfaces/key-chain-loom` | `chain-conductors` | The chain bus. Falling edge loads the parallel inputs |
| `SER` | in | `interfaces/key-chain-loom` | `chain-connectors` | The next board's `QH`, or the carrier through `LK-SER`. Point to point, not a bus — which is what forces two connectors on most boards |
| `QH` | out | `interfaces/key-chain-loom` | `chain-connectors` | Toward the carrier, on `IN` pin 8. Bit 0 is the `H` input of the `right_thumb` device |
| `A`…`H` | in | `cluster/key-switch-network`, `cluster/key-marker-and-bits` | `marker-bits`, `free-bits` | Eight parallel inputs per device: a switch network, a marker strap or a free bit |
| `3V3` | in | `interfaces/key-chain-loom` | — | Chain bus pin 10, `cluster-boards.md` §3. `C-DECOUPLE-165` is the local reservoir this input has no other source for |
| `GND` | ref | `interfaces/key-chain-loom` | `chain-conductors` | The chain bus, five alternating grounds. `C-DECOUPLE-165` returns here, at the package |

## §1 The device

*Connectivity is **[`netlist.yaml`](netlist.yaml)**, not this drawing, and that
file is one schematic for four boards — `replicated: 4`. The eight parallel
inputs are deliberately not netted there: which of `A`…`H` is a switch, a
marker strap or a free bit is different on every board, so no assignment
would be true of all four. The allocation table lives on
[`../key-marker-and-bits/key-marker-and-bits.md`](../key-marker-and-bits/key-marker-and-bits.md).*


```
                        74HC165  SOIC-16          [from memory: pin map]
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

**Bit order inside the device is `H` first, then `G F E D C B A`.** On the
falling edge of `SH/LD` the parallel inputs load; `H` (D7) appears at `QH`
immediately, and each clock shifts the next one toward the output `[from
memory]`. Combined with ADR 0001's *"bit 0 is the first bit clocked out"*
`[repo] 0001, key-layout.yaml`, that fixes **bit 0 = the `H` input of the
`right_thumb` device** and settles the `H`…`A` question the carrier page left
open — the ordering half of it, anyway. Which *switch* lands on which input is
§4.

**The part is 74HC, not 74LVC**, and that is load-bearing rather than
incidental. HC's slow edges make 265 mm of loom an ordinary lumped load instead
of a transmission line, which is what removed the hazards that briefly sent
these registers to the tail `[repo] 0001, bom.csv`. Same SOIC-16 footprint, so
LVC with proper source termination remains the way back if E4 disagrees.
