# Key chain — main board to two key boards

**Status:** Rewritten 2026-09-26 for the one-main-board design
([ADR 0017](../../../docs/decisions/0017-one-main-board.md)). The directory
keeps its old name so that paths into it do not break; there is no loom any
more. What this page described before — a carrier and four cluster boards on
IDC ribbons — is summarised in [`notes.md`](notes.md) and is whole in git.

The four 74HC165s are still one chain of 32 bits, **in the same order**, so the
bit map ([`key-marker-and-bits`](../../cluster/key-marker-and-bits/key-marker-and-bits.md))
and the firmware do not change. What changed is where the registers sit:

- **Two on the main board**, `right_thumb` and `left_thumb`, with their
  switches and networks (ADR 0017). Their part of the chain is traces.
- **Two on the key boards**, `right_hand` and `left_hand`, which hang from the
  lid under the top plate (`PCB-CLUSTER`). Each key board connects to the main
  board by **one 12-way flat flex ribbon** (`FFC-CHAIN`) with a ZIF connector
  (`J-CHAIN`) at each end — `chain-connectors` in all.

Evidence marking as on the other hardware pages: `[repo]` names a file,
`[calc]` shows the arithmetic, `[from memory]` means no datasheet was read for
it.

## Interfaces

Every net that crosses this circuit's boundary, and **which board each end is
on**. Quantities appear **only** as a citation into `config/figures.yaml` —
this table names nodes, it does not restate values.

The `Dir` and `Peer` columns are defined once in
[`hardware/README.md`](../../README.md#the-interfaces-table).

| Node | End | Dir | Peer | Figure | Note |
|---|---|---|---|---|---|
| `SCK` (pin 2) | main → all four registers | out | MCU IO38 → `cluster/key-register` | `chain-conductors` | One net: two registers by trace, two over the ribbons. `R-CHAIN-SER` at the driving end |
| `SH/LD` (pin 4) | main → all four registers | out | MCU IO7 → `cluster/key-register` | `chain-conductors` | One net, like `SCK`. A glitch here reloads every register mid-shift — the whole 32-bit word |
| `SER` (pin 6) | main → key board | out | → `cluster/key-register` | `chain-connectors` | **The key board's own serial input**, on both ribbons. On the `right_hand` ribbon it is `left_thumb`'s `QH`; on the `left_hand` ribbon it is the chain end, `IO33` and `R-SER-TERM` |
| `QH` (pin 8) | key board → main | in | `cluster/key-register` → | `chain-connectors` | **The key board's own serial output**, on both ribbons. `right_hand`'s goes to `right_thumb`'s `SER`; `left_hand`'s to `left_thumb`'s |
| `QH` of `right_thumb` | main board only | in → out | `cluster/key-register` → MCU IO40 | `marker-bits`, `free-bits` | Bit 0 onward. **Reaches no connector** — a trace from the register to the MCU's pins |
| `GND` ×5 (pins 1, 3, 5, 7, 9) | both | ref | `cluster/key-register`, `cluster/key-switch-network`, `cluster/key-marker-and-bits` | `chain-conductors` | One between every signal, and against pin 10 |
| `3V3` (pin 10) | main → key boards | out | MCU board's 3V3 → `F-CHAIN` → `cluster/key-register`, `cluster/key-switch-network`, `cluster/key-marker-and-bits`; shared with `carrier/breath-adc` | `key-pullup-qty` | **It is also the MCP3202's reference** — `carrier.md` §2 carries that argument |
| spare ×2 (pins 11, 12) | both | — | — | `chain-conductors` | ADR 0009's rule, free in a 12-way part |
| `J-CHAIN`, `FFC-CHAIN` | both | — | — | `chain-connectors` | This circuit's connectors and cables |
| `R-CHAIN-SER`, `R-SER-TERM`, `U-TVS-CHAIN`, `F-CHAIN` | main | — | — | — | This circuit's parts, all on the main board |
| the 32 bits | all four registers | — | `cluster/key-marker-and-bits` | `marker-bits`, `free-bits` | Allocated in `config/key-layout.yaml`. The chain order is unchanged |

Pin numbers in this table are the **main-board** connector's. The key board's
connector numbers the same conductors in reverse — see *The ribbon*, below.

---

## The chain

*Connectivity is **[`netlist.yaml`](netlist.yaml)**, not these drawings. It
holds the hop map — which register's `QH` feeds which register's `SER`, and
over which ribbon — as named nets. The register itself is one schematic built
four times ([`key-register`](../../cluster/key-register/netlist.yaml),
`replicated: 4`), so its side of each hop is per instance, and
`hardware/nets.yaml` marks those nets `per_board:`.*

The order is `config/key-layout.yaml`'s, unchanged: **bit 0 is the first bit
clocked out**, the `QH` of `right_thumb`, the device nearest the MCU, and
serial data flows toward the clock source (ADR 0001 fix 3) `[repo]`:

```
   MCU ◄── right_thumb ◄── right_hand ◄── left_thumb ◄── left_hand ◄── chain end
            (main)          (key board)     (main)         (key board)   IO33 / pull-up

   ┌─────────────────────────── MAIN BOARD ──────────────────────────────┐
   │                                                                     │
   │  IO40 ◄─ QH (RT) SER ◄─┐        ┌─► SER (LT) QH ─┐      IO33 ─┐     │
   │                        │        │                │   + pull-up│     │
   │             ┌─ pin 8 ──┘        └── pin 8 ─┐     │            │     │
   │             │  pin 6 ◄─────────────────────┼─────┘            │     │
   │             │  (right_hand J-CHAIN)        │  pin 6 ◄─────────┘     │
   │             │                              │  (left_hand J-CHAIN)   │
   └─────────────┼──────────────────────────────┼────────────────────────┘
          FFC-CHAIN, 6 out / 8 back       FFC-CHAIN, 6 out / 8 back
   ┌─────────────┴─────────────┐    ┌───────────┴───────────────┐
   │ KEY BOARD right_hand      │    │ KEY BOARD left_hand       │
   │  6 ──► SER (RH) QH ──► 8  │    │  6 ──► SER (LH) QH ──► 8  │
   └───────────────────────────┘    └───────────────────────────┘

   SCK, SH/LD, 3V3 and the grounds are one net each, on every register and
   on both ribbons. Each ribbon carries its key board's SER IN on pin 6 and
   its QH OUT on pin 8 — the same two pins the old IN connector used.
```

**The existing 12-way pinout already does this, and is kept.** Each ribbon is
a single hop out and a single hop back: the key board's serial input on pin 6
and its serial output on pin 8, with a ground either side of both. The old
design used pin 6 for a pass-through and pin 8 for the output; the pin
assignments are the same, only pin 6's job got simpler.

**No serial-input link is needed on any board.** The four-board design had a
solder link on every cluster board to choose where `SER` came from, because
the chain-end board was different ([`notes.md`](notes.md)). Now each key board
has one connector and its `SER` is **always** pin 6, whatever drives pin 6 on
the main board. Both key boards are identical in the chain;
the difference between the right-hand and left-hand hop is two traces on the
main board, which is one board with one layout anyway.

**The chain order no longer costs anything to follow.** Every key board's hop
is its own ribbon and back, so any order of the four devices uses the same two
ribbons and the same four connectors. The earlier proposal to swap `left_thumb`
and `left_hand` to save a body-thickness crossing has nothing left to save,
and `key-layout.yaml`'s order stands.

### The main-board end

```
  from the MCU                  J-CHAIN, main board, BOTH ribbons
  (MCU board pins)              (12-way 1.0 mm FFC ZIF)

   IO38  ──[R-CHAIN-SER 100R]──┬──► 2 SCK    both ribbons, and RT/LT CLK
   IO7   ──[R-CHAIN-SER 100R]──┼──► 4 SH/LD  both ribbons, and RT/LT SH/LD
   IO33  ──[R-CHAIN-SER 100R]──┼──► 6 SER    LEFT_HAND ribbon only
                               │     (right_hand ribbon: 6 = LT's QH)
                     ┌─────────┘
              [R-SER-TERM 10k] to 3V3 on the left_hand ribbon's pin 6

   IO40  ◄───────────────────────── RT's QH  (a trace; no connector)
                                     8 QH    right_hand ribbon: RT's SER
                                             left_hand ribbon:  LT's SER

   3V3   ───[F-CHAIN 100mA polyfuse]────► 10 3V3  both ribbons, and RT/LT
   GND   ─────────────────────────────►  1 3 5 7 9  both ribbons
                                         11 12  spare

   [U-TVS-CHAIN SP0504BAHTG] on SCK, SH/LD and the chain-end SER, to GND_CHAIN;
   its fourth channel is spare.
```

### The key-board end

```
   J-CHAIN, key board              74HC165 on this key board
   (conductor numbers; see
    the ribbon, below)
   conductor 2  SCK   ─────────────►  CLK
   conductor 4  SH/LD ─────────────►  SH/LD
   conductor 6  SER   ─────────────►  SER (pin 10)
   conductor 8  QH    ◄─────────────  QH  (pin 9)
   conductor 10 3V3   ─────────────►  VCC, pull-ups, marker straps
   conductors 1 3 5 7 9  GND
   conductors 11 12      spare, unconnected

   No link, no pull-up, no choice: both key boards are this drawing.
```

---

## The ribbon — contact side, connector type and pin numbering

The geometry is in `mechanical/DESIGN.md` and the model: the key board's
connector is on its **underside**, the main board's on its **top**, both
**side-entry, taking the ribbon from the same side** (toward the side wall),
and the ribbon joins them in one **180° C** `[repo]`. That fixes two things
about the parts, and neither needs a datasheet.

**1. Contact side: use the same connector at all four positions, and a
same-side-contact cable.** `[calc]`, from the geometry alone. Put the main
board's connector with its contacts facing **down** (toward its board —
"bottom contact"), so the ribbon enters with its conductors facing down. Going
round a 180° bend turns the ribbon over: the face that looked down now looks
**up** — toward the key board, which is above it. The key board's connector is
the same part mounted upside down, so its contacts face **up**, toward the key
board. The conductors meet the contacts at both ends, on **the same face of the
ribbon**. That is a same-side cable. (Start from top-contact instead and every
"down" and "up" swaps — same answer.) The other combination that works is an
opposite-side cable with **one** top-contact and **one** bottom-contact
connector per ribbon: two parts to stock and two to get wrong, for nothing.

**2. Pin numbering: the key board's connector reads the ribbon backwards.**
`[calc]`. The bend turns the ribbon over about an axis along the body, so each
conductor keeps its place along the body. The key board's connector is the main
board's part turned upside down with its entry still toward the side wall —
which is a half-turn about the axis *across* the body, and that reverses its
row of pins along the body. So:

```
   conductor k   =   main-board J-CHAIN pin k   =   key-board J-CHAIN pin 13 − k

   k:        1    2    3    4    5    6    7    8    9   10   11   12
   signal:  GND  SCK  GND SH/LD GND  SER  GND  QH   GND  3V3  sp   sp
   key pin: 12   11   10    9    8    7    6    5    4    3    2    1
```

**Lay the key boards' footprint out to the bottom row, never to the main
board's numbers.** Get it wrong and pin 10's 3V3 lands on the key board's
ground. This holds for any part whose pins are numbered along its row, which is
all of them, but **check it against the chosen part's pin-1 drawing** at M4 —
it is derived here, not read.

**Why this pinout survives a skewed insertion reasonably well, and where it
does not.** A ZIF slot the width of the ribbon (`routing.ffc_w` in
`config/body.yaml`) will not take it one full pitch off-centre, but a ribbon
pushed in at an angle can bridge neighbours. Every signal has a ground on
both sides, so a bridge takes a signal to ground rather than to another
signal — except pin 10, whose neighbours are a ground and a spare. **A 3V3–GND
bridge at pin 9/10 is the short this design can have**, and it is a service
event: the ribbons are re-seated every time the lid goes back on. That is what
`F-CHAIN` is now for (below).

---

## The chain-end serial input, and the self-test

`R-SER-TERM` moves to the **main board**, on the `left_hand` ribbon's pin 6,
on the connector side of `IO33`'s `R-CHAIN-SER`:

```
   IO33 ──[R-CHAIN-SER 100R]──┬──► left_hand ribbon pin 6 ──► LH register SER
                              │
                      [R-SER-TERM 10k]
                              │
                             3V3
```

**Decided: the main board, because that keeps the two key boards identical.**
On a key board it would have to be fitted on one and not the other — a board
variant, which is what the old solder link existed to avoid.

It still does what it did. Undriven, it holds the chain-end input high — the
tied-off case ADR 0001 specified. **Driven**, `IO33` wins through 100 Ω
against 10 kΩ `[calc]`: `3.3 V × 100 / 10 100 = 33 mV` from the rail. So an
end-to-end chain self-test — shift a known pattern in at `left_hand` and read
it back at `right_thumb` with no keys pressed — is **a firmware choice, not a
board choice**. It is worth more than it was: the pattern now crosses **both
ribbons in both directions**, so it tells "a ribbon is out of its latch" from
"one bit is stuck", which the static marker cannot. Fit the resistor; E4
decides whether firmware uses it.

---

## What the three protection parts are for now

All three were proposed against a 265 mm loom that ran beside the LED strip's
12 V feed. That loom is gone (ADR 0016 moved the strip onto the main board;
ADR 0017 put the thumbs there too), so each was re-derived against the chain
as it now is. **None is decided here**; each says what decides it.

**`R-CHAIN-SER` — still has a job, for a different reason.** `[calc]`, with two
inputs `[from memory]`: an MCU output edge of ~2 ns, and ~6 ns/m on FR-4 and
flat flex. A net behaves as a lump while its one-way delay is under about a
sixth of the edge:

```
   2 ns / 6 = 0.33 ns    →    0.33 ns / (6 ns/m) = 56 mm
```

`SCK` and `SH/LD` are single nets that run the main board — its length is
`mechanical/drc.echo` "main board (derived)", several times 56 mm — to two
registers and two ribbons (each a few centimetres: `drc.echo` "ribbon arc
length"). A fast edge sees that as a branched line, and a ring through the
74HC165's threshold on `SCK` is a double clock that shifts the whole word. The
100 Ω at the source slows the edge and damps the ring; it is not series
termination, which ADR 0001 rejected for a line that drops on several loads.
**Open, decided at E14**: scope `SCK` at the `left_hand` register on the real
main board and ribbons. It is three 0805s either way.

*(The registers' own `QH` edges are 74HC edges, several times slower
`[from memory]`, and each hop is a ribbon plus part of the main board — the
old "HC's slow edges keep it a lumped load" argument still covers them.)*

**`U-TVS-CHAIN` — the exposure moved from play to service.** The ribbons never
leave the body and sit under the grounded plate, so in play nothing reaches
them. The contacts are handled when the ZIF latches are flipped to lift the
lid, and a main-board `J-CHAIN` then exposes three MCU pins through their
100 Ω — `SCK`, `SH/LD` and the chain-end `SER` — which is where the array is
drawn and netted. The chain's `QH` into the MCU is `right_thumb`'s and reaches
no connector. **Open, decided by the owner**: protect service by procedure
(instrument off, a wrist strap) or by the part.

**`F-CHAIN` — the short it covers is now at re-assembly.** It still keeps a
short from browning out the MCU board's LDO, which is the instrument's only
3V3 and the MCP3202's reference. What changed is where the short comes from:
not a loom chafing inside a closed body, but a ribbon seated skewed at pin
9/10 (above). Its drop is harmless for the reason the BOM row gives — the
thresholds and the pull-ups share the rail. **Open, decided by**: fit it, or
protect at the source.

---

## What the main board still owes the chain

**The 3V3 rail, and it is a real load on the ADC's reference** `[calc]`:

```
3.3 V / (2.2 kΩ + 100 Ω) = 1.43 mA per CLOSED key
19 closed                = 27.3 mA, as a step, at play rate
```

Unchanged by this rework — the same pull-ups (`key-pullup-qty`) on the same
rail. It lands on the MCP3202's reference and is accepted as a gain term; the
argument is `carrier.md` §2's, and the numbers are
[`key-switch-network`](../../cluster/key-switch-network/key-switch-network.md)'s.

**A ground return per clocked signal** `[repo] 0001 fix 1`, on the main board
as on the ribbons: route `SCK` and `SH/LD` over unbroken ground, away from the
strip's data and 12 V feed and the breath signal (ADR 0017's routing note).

### The 32 bits, and which board each is on

From `config/key-layout.yaml` `[repo]`:

| Device | Bits | Board |
|---|---|---|
| `right_thumb` | 0–7 | **Main board** |
| `right_hand` | 8–15 | Key board, right-hand ribbon |
| `left_thumb` | 16–23 | **Main board** |
| `left_hand` | 24–31 | Key board, left-hand ribbon |

The allocation within each device — switches, the two reserved spare-switch
positions, the marker straps and the free bits — is
[`key-marker-and-bits`](../../cluster/key-marker-and-bits/key-marker-and-bits.md)'s,
and none of it moved.

---

## Still open

- **The `J-CHAIN` part**, decided at M4 with the part: a 12-way 1.0 mm
  side-entry ZIF that fits `boards.ffc_conn_h`, the same part at all four
  positions, top- or bottom-contact either way. With it, the key board's
  mirrored footprint numbering is confirmed against the part's own pin-1
  drawing.
- **The `FFC-CHAIN` length**, decided at M4: `drc.echo` "ribbon arc length"
  plus the two insertion depths off the chosen connector's drawing, rounded up
  to a stock length. Same-side contacts, per *The ribbon*.
- **`R-CHAIN-SER`** (E14), **`U-TVS-CHAIN`** (owner) and **`F-CHAIN`**
  (fit or protect at source) — above.
- **The main board's hop inputs float with the lid off.** With a ribbon out,
  `right_thumb`'s or `left_thumb`'s `SER` — the main-board end of that
  ribbon's pin 8 — has nothing on it. It costs nothing in play (the lid is on)
  and the markers show the missing board as a failed frame, not a wrong note.
  **Decided by** whether the main board is ever run with the lid off at
  bring-up for long enough to care; if so, a pull-up on each ribbon's pin 8 at
  the main board.
