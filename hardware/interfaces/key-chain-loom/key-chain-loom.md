# Key chain loom — carrier to four cluster boards

**Status:** Consolidated 2026-09-21 from the two pages that described one
circuit from opposite ends of the loom — `hardware/carrier/carrier.md` §3 and
`hardware/cluster/cluster-boards.md` §3. Everything below the `## Interfaces`
table was **moved verbatim**: nothing was reworded, no value was edited and no
open question was closed.

One ribbon leaves the carrier and passes through four cluster boards in turn.
The conductor count, the alternating grounds, the series resistors and the
fusing are decided at the carrier end; the connector pinout, the bus-versus-
point-to-point split and the chain-end link are decided at the cluster end; and
neither half is a complete statement of what runs down the body.

The drawings came here whole. Each is wholly this circuit — a carrier header
to a chain connector, a chain connector to a register, and the chain-end link
between them — so none had to be divided and none was redrawn.

## Interfaces

Every net that crosses this circuit's boundary, and **which end of the loom
each one is on**. Quantities appear **only** as a citation into
`config/figures.yaml` — this table names nodes, it does not restate values.

| Node | End | Dir | Peer | Figure | Note |
|---|---|---|---|---|---|
| `SCK` (`J-CHAIN` pin 2) | carrier → clusters | out | `HDR-DEV` IO38 → `cluster/key-register` | `chain-conductors` | Series resistor at the driving end. Straight bus, IN to OUT, at every board |
| `SH/LD` (`J-CHAIN` pin 4) | carrier → clusters | out | `HDR-DEV` IO7 → `cluster/key-register` | `chain-conductors` | Straight bus. A glitch here reloads every register mid-shift, which is the whole 32-bit word |
| `SER` (`J-CHAIN` pin 6) | carrier → clusters | out | `HDR-DEV` IO33 → the far device, through `LK-SER` | `chain-conductors` | The one pass-through: it rides every hop to the chain-end board's serial input |
| `QH` (`J-CHAIN` pin 8) | clusters → carrier | in | `cluster/key-register` → `HDR-DEV` IO40 | `chain-conductors`, `marker-bits`, `free-bits` | **Point to point, and a different net on each side of every board.** That is what makes the chain eight connectors rather than five |
| `GND` ×5 (pins 1, 3, 5, 7, 9) | carrier ↔ clusters | ref | `HDR-DEV` → `cluster/key-register` | `chain-conductors` | One between every signal, and against pin 10 |
| `3V3` (`J-CHAIN` pin 10) | carrier → clusters | out | `HDR-DEV` LDO → `cluster/key-switch-network`, `cluster/key-register` | `key-pullup-qty` | The pull-ups, four `VCC` pins and four decouplers. **It is also the MCP3202's reference**, which is what makes the static draw a live trade — that argument is owned by neither end and stayed in `carrier.md` §2 |
| spare ×2 (pins 11, 12) | carrier ↔ clusters | — | — | `chain-conductors` | ADR 0009's rule, free in a 2×6 |
| `J-CHAIN` | both | — | `carrier/carrier.md` and `cluster/cluster-boards.md` component tables | `chain-connectors` | Same pinout at all eight positions, boxed and keyed at every one |
| `LK-SER`, `R-SER-TERM` | clusters | — | `cluster/cluster-boards.md` component table | — | Chain-end board only. Proposed |
| `CLK INH`, register `SER` termination | clusters | — | `cluster/key-register` | — | On the cluster boards, not on the carrier |
| the 32 bits | clusters | — | `cluster/key-marker-and-bits`, `config/key-layout.yaml` | `marker-bits`, `free-bits` | What the loom carries. **None of the allocation is a carrier decision** |

---

## From the carrier end — `carrier.md` §3

*Moved verbatim from `hardware/carrier/carrier.md` §3, 2026-09-21. "This board"
and "this page" throughout mean `carrier.md` as it stood before the move, and
`carrier.md` keeps its `## §3` heading because other pages cite it by number.*

**The registers are not on this board.** ADR 0001's *"One register per cluster"*
put one 74HC165 on each cluster board, with that cluster's 2.2 kΩ/100 Ω/47 nF
networks beside it, because the switches need a rigid PCB regardless (ADR 0002)
and putting the register on it makes every switch-to-chip connection a trace
`[repo] 0001, 0002`. **This page's first draft drew all four registers and all
21 networks here.** That was the superseded topology; what follows replaces it.

**Decided: a ground return per signal, laid out as an alternating-ground
ribbon.** ADR 0001 fix 1 calls this the highest-value item on its list, and it
is the only thing in the loom that can still be corrupted — a glitch on `SH/LD`
does not cost one wrong note, it reloads all four registers mid-shift and
corrupts the whole 32-bit word `[repo] 0001`. Four signals, five grounds, one
supply:

```
  HDR-DEV                                   J-CHAIN  (2×6 IDC, 12-way ribbon,
                                                      10 wired + 2 spare)
   GND  ────────────────────────────────────►  1  GND
   IO38  SPI3 SCK ──[R-CHAIN-SER 100R]─────►  2  SCK     ** R PROPOSED **
   GND  ────────────────────────────────────►  3  GND
   IO7   latch    ──[R-CHAIN-SER 100R]─────►  4  SH/LD   ** R PROPOSED **
   GND  ────────────────────────────────────►  5  GND
   IO33  SER out  ──[R-CHAIN-SER 100R]─────►  6  SER     (into the far device)
   GND  ────────────────────────────────────►  7  GND
   IO40  MISO     ◄─────────────────────────  8  QH      (out of the near one)
   GND  ────────────────────────────────────►  9  GND
   3V3  ───────[F-CHAIN, see below]─────────► 10  3V3     → 24 pull-ups,
                                              11  spare      4 × VCC, 4 × 100 nF
                                              12  spare

              [U-TVS-CHAIN 4-ch array to DIG_GND]   ** PROPOSED **

  Every signal has ground on both sides; 3V3 sits against pin 9's ground.
  The two spares are ADR 0009's rule and they are FREE: IDC comes in 2xN, so
  a 2x6 costs what a 2x5 costs and the ribbon is 2 mm wider. Under the tail
  topology a spare conductor bought a spare KEY; under this one it buys a
  REPAIR - expansion now lands on a spare register BIT, which needs no wire.

  EIGHT connectors, not five. The chain is four hops, and SER/QH cannot be a
  pass-through bus: each board's QH feeds the PREVIOUS board's SER, which is
  point-to-point and changes meaning every hop. So every cluster board except
  the last carries an IN and an OUT - carrier 1, RT 2, RH 2, LT 2, LH 1 - with
  four ribbon assemblies between them. Same 2x6 pinout at all eight.

  Pin 6 SER is the exception: it IS a pass-through, riding every hop to reach
  the far device's serial input. ADR 0001 has that input "terminated at the
  far device", which would make this conductor redundant. Driving it instead
  costs nothing and buys an end-to-end chain self-test - shift a known pattern
  in at LH and read it back at RT, with no keys pressed. That distinguishes
  "the loom is broken" from "one bit is stuck", which the static marker
  pattern cannot. NOT yet decided; it is a cluster-board question.

  Chained, not starred (ADR 0001 fix 2): ONE run leaves this connector and
  passes through right_thumb → right_hand → left_thumb → left_hand in turn.
  bit 0 is the first bit clocked out = QH of right_thumb, the device nearest
  the MCU (ADR 0001 fix 3, and config/key-layout.yaml).
```

**`CLK INH` is tied low and `SER` is terminated at the far device** — both on
the cluster boards, not here `[repo] 0001`.

### What this board still owes the chain

**1. The 3V3 rail, and it is a bigger load than it was** `[calc]`. The pull-ups
went 10 kΩ → 2.2 kΩ when the register moved back beside its switch `[repo]
bom.csv`:

```
3.3 V / (2.2 kΩ + 100 Ω) = 1.43 mA per CLOSED key
18 closed                = 25.8 mA, as a step, at play rate
plus 4 × 74HC165 quiescent, negligible
```

> **That current comes out of the dev board's 3V3 LDO, which is also the
> MCP3202's voltage reference** — the part has no `VREF` pin, `VDD` *is* the
> reference `[repo] R10 B4`. At a load regulation of ~0.3 % per 100 mA
> `[from memory]`, 25.8 mA moves the reference **0.077 %, about 3.2 LSB**, in
> step with how many keys are held.
>
> 3.2 LSB against a playable breath span of ~1594 counts is 0.2 % — almost
> certainly inaudible, and it is the *reference* moving, so it scales the
> reading rather than offsetting it. **Recorded rather than fixed, because the
> symptom of being wrong about it is "the breath reading moves when I press
> keys", which gets blamed on firmware for a week.** The first draft costed
> this at 5.9 mA and 0.7 LSB, against the old 10 kΩ. See *Still open*.

**2. A ground return per clocked signal** `[repo] 0001 fix 1` — the highest
value item on ADR 0001's list, and now the *only* thing in the loom that can be
corrupted. With the registers distributed, a disturbed key line no longer
exists as a loom signal; what runs the body is four clocked lines whose blast
radius is the whole 32-bit word, and a glitch on `SH/LD` reloads every register
mid-shift `[repo] 0001`. **Six conductors is the signal count, not the
conductor count.** Whether this connector is 6-way or 10-way is a decision this
page cannot take alone — see *Still open*.

**3. `F-CHAIN`, or not.** The 3V3 conductor leaves this board, runs 265 mm
through a bonded body next to 12 V LED power, and comes back as nothing. A
short on it browns out the dev board's LDO and takes the instrument down with
no diagnosis. A 100 mA polyfuse or a 0603 fuse is two millimetres of board.
**Proposed, not in the BOM.**

### Why the old charge-sharing derivation is gone

The first draft carried ADR 0001's `180 pC / 10 nF = 18 mV`, and a companion
figure of **+4.5 V on the loom node** from `180 pC / 40 pF`. Both are dead, for
two independent reasons, and neither should be reintroduced:

- **The model was wrong.** ADR 0001 now records it: there is no 12 V edge (the
  WS2815 rail is held by 470–1000 µF and its LED current is PWM'd at ~2 kHz),
  `Q/C` is the wrong model because coupling is a *divider*, and a passive
  divider cannot exceed the aggressor's own swing — so 4.5 V was 37 % above
  the ceiling of its own mechanism. Corrected, an unfiltered wire sees
  **1.36 V** `[repo] 0001`.
- **The node no longer exists.** The key network sits on the cluster board, a
  few millimetres from its switch. There is no loom conductor between the
  switch and the register input for anything to couple into.

**The key networks are still fitted** — see ADR 0001 for why (a floating CMOS
input has no defined state, in a cavity that is breathed into for hours) — but
they are a bounce filter and cheap insurance, not the thing that makes the
topology safe, and they are not this board's parts.

### The 32 bits, and where each decision now lives

From `config/key-layout.yaml` `[repo]`:

| Bits | Use | Whose board |
|---|---|---|
| 18 | Fitted switches | **Cluster boards** — network + trace to the switch |
| 3 | Reserved spare switches (octave up, octave down, hold/preset) | **Cluster boards** — network fitted, pad unloaded. Plate cutouts at M3 `[repo] 0010` |
| 8 | Marker pattern | **Cluster boards** — hard-wired at the register input. Unretrofittable. **Decided 2026-09-21: 8, not 6** |
| 3 | Genuinely free | **Cluster boards** — must be pulled `[repo] key-layout.yaml` |
| **32** | | **None of them on this carrier** |

**Which eight bits carry the marker, and their levels, was decided 2026-09-21**
(`key-marker-and-bits.md`, `key-layout.yaml`). The mapping inside each device is
still open, and
it is now a cluster-board decision** — as is the `H`…`A`-to-switch mapping
inside each device. Both still have to be settled before *those* boards are
made, and firmware has to be told about both. They are off this page's critical
path, not off the project's.

**The option worth costing has got cheaper.** Giving the 3 free bits the full
network too is now 15 passives spread across four boards that already carry
21 sets, with no extra loom conductors at all — under the tail topology it also
needed five more wires down the body. If "add a switch later" is worth
anything, this is the moment it costs least.

---

## From the cluster end — `cluster-boards.md` §3

*Moved verbatim from
[`cluster-boards.md`](../../cluster/cluster-boards.md) §3, 2026-09-21. "This
page" throughout means that page as it stood before the move, and it keeps its
`## §3` heading because four sibling pages cite it by number.*

`J-CHAIN` is a 2×6 IDC boxed header on a 12-way ribbon, alternating ground,
decided 2026-09-21 `[repo] 0001, bom.csv`:

```
   1 GND    2 SCK      3 GND    4 SH/LD    5 GND    6 SER
   7 GND    8 QH       9 GND   10 3V3     11 spare 12 spare
```

Boxed and keyed at all eight positions, because a reversed connector puts 3V3
onto the `QH` net.

```
   J-CHAIN-IN                                          J-CHAIN-OUT
   (toward the carrier)                        (away, to the next board)

    2 SCK   ─────────────┬──────────────────────────────► 2 SCK
    4 SH/LD ─────────────┼──┬───────────────────────────► 4 SH/LD
   10 3V3   ─────────────┼──┼──┬────────────────────────► 10 3V3
   GND ×5   ─────────────┼──┼──┼──┬─────────────────────► GND ×5
    6 SER   ─────────────┼──┼──┼──┼──┬──────────────────► 6 SER
                         │  │  │  │  │
                    ┌────▼──▼──▼──▼──┴─────┐
                    │  74HC165             │
                    │  CLK  SH/LD  VCC GND │
                    │                      │
    8 QH   ◄────────┤ QH (pin 9)           │
                    │                      │        ┌──── 8 QH
                    │  SER (pin 10) ◄──────┼──[LK-SER]
                    └──────────────────────┘        └──── from pin 6 above
                                                      ▲
                          LK-SER: a 3-pad solder link.
                          Position A (boards 1-3): SER comes from OUT pin 8,
                            i.e. the next board's QH. Normal chaining.
                          Position B (last board): SER comes from the IN pin 6
                            passthrough, which reaches all the way back to the
                            carrier.
```

**`SCK`, `SH/LD`, `3V3` and the five grounds are a straight bus** — IN to OUT,
1:1, so a plain straight-through ribbon works between any two boards.

**`QH` and `SER` are not a bus, and that is what forces two connectors.** Each
board's `QH` goes *toward* the carrier on `IN` pin 8; the *next* board's `QH`
arrives on `OUT` pin 8 and becomes this board's serial input. Pin 8 therefore
carries a different net on each side of the board, which is why the chain is
eight connectors across five boards rather than five `[repo] carrier.md §3`.

### `LK-SER` and `R-SER-TERM` close the self-test question for free

The carrier page raised whether the far device's serial input should be tied off
(ADR 0001) or driven from the carrier, which would let firmware shift a known
pattern through all 32 bits and distinguish *"the loom is broken"* from *"one
bit is stuck"* — something the static marker cannot do `[repo] carrier.md §3`.

**It does not have to be decided in copper.** Fit, on the last board only:

```
   IN pin 6 (SER passthrough) ──┬──[LK-SER position B]──► 74HC165 SER (pin 10)
                                │
                        [R-SER-TERM 10k]
                                │
                               3V3
```

`R-SER-TERM` holds the input high if nothing drives it, which is the tied-off
case ADR 0001 specified. If firmware *does* drive `IO33`, the carrier's output
wins through its 100 Ω series resistor against a 10 kΩ pull `[calc]` — a
divider of 100/10100, so the driven level is within 33 mV of the rail. **The
self-test becomes a firmware choice rather than a board choice**, at the cost of
one resistor, and this page recommends fitting it and deciding later.
